> **Source paths in this document are relative to `back/`.** It was written alongside the
> implementation and lived at `back/docs/` until it was moved here, where this kind of content
> belongs. Recover the original at any time with
> `git show 3af52fba:docs/<file> ` in the `back` repo.

# Rate limits on the run-creating entry points

Reference for the S7-part-2 rate limiter (`src/app-api/rate-limit/`). For the design rationale,
the organisation-key derivation and its measurement history, see
[`S7-RATE-LIMITING-RUN-ENTRY-POINTS.md`](./rate-limiting-run-entry-points.md). This page documents
the shipped behaviour: what each route enforces, how failure is handled, and what a refused caller
actually receives.

**The limit values below are sized against 7 days of production traffic but not yet validated per
caller.** See "The enforce gate" below before anyone sets `RATE_LIMIT_MODE=enforce`.

## Per-entry-point reference

**The organisation ladder** (`rate-limit-key.resolver.ts`, `resolveOrganisation`, `:43-62`): resolve
a space id — **only** from `user.apiKeySpaceId`, which `apikey.strategy.ts:68` stamps onto the
principal from the validated api key, never from a request header — and look up its company; if
found, `company:<id>`. Else resolve a flow id and look up the company that *owns that
flow*; if found, `company:<id>`. A flow id reaching this point is consulted only to derive a
company — it is not yet a candidate key. If neither lookup found a company: when the request is
authenticated, use the company the caller owns if they own exactly one (`company:<id>`), otherwise
stop at `user:<id>` — an authenticated caller's ladder never reaches `flow:<id>`. Only when there is
**no** authenticated user at all (the `@Public()` webhook route) does the ladder fall through to
`flow:<id>`, and if that too is absent, `user:<unresolved>`.

**The pre-auth stage** (`rate-limit-key.resolver.ts`, `resolvePreAuth`) runs *before* the auth guard
on the four HTTP routes and keys by, in order: sha256 of the `api-key` header; sha256 of the
`Authorization: Bearer` token when there is no api-key header; the flow id from `query.flowId` or
`params.id`; `user:<unresolved>`. Hashing the bearer token means an authenticated caller's own
traffic never shares a bucket with an anonymous caller who merely knows the flow id — flow ids
travel through published interfaces and shared links, so a shared `flow:<id>` bucket would let a
stranger lock the owner out under `enforce`. The stage has its **own** limits,
`RATE_LIMIT_PRE_AUTH_PER_MINUTE` / `_PER_HOUR`, defaulting to ten times the general window
(**4000/min, 40000/hour**); per-route overrides do not apply to it. Its Redis keys are namespaced by
stage (`rl:pre-auth:<window>:<route>:<kind>:<value>` versus `rl:organisation:...`), so the two
stages can never share a counter even when both resolve to the same `flow:<id>`.

| Route | Handler | `runType` | Limiter key | Env vars | Effective limit today |
|---|---|---|---|---|---|
| `POST /flux/api-v2` | `FluxController.api()` (`flux.controller.ts:190`, guarded at `:185-186`) | `api` | Organisation ladder (authenticated) — `company:<id>` when derivable, else `user:<id>`; see "The organisation ladder" above | `RATE_LIMIT_API_V2_PER_MINUTE` / `RATE_LIMIT_API_V2_PER_HOUR` | 400/min, 4000/hour (general fallback — no override is set in `.env.example`) |
| `POST /flux/api-v2-webhook` | `FluxController.apiWebhook()` (`flux.controller.ts:480`, guarded at `:476-477`) | `webhook` | Organisation ladder (unauthenticated — `@Public()`) — `company:<id>` when derivable, else `flow:<id>`, else `user:<unresolved>`; the only one of the four HTTP routes that can bottom out at `flow:<id>`, since it runs `OrganisationRateLimitGuard` without `ApiKeyGuard`/`JwtAuthGuard` | `RATE_LIMIT_API_V2_WEBHOOK_PER_MINUTE` / `_PER_HOUR` | 400/min, 4000/hour (general fallback) |
| `POST /flux/batch-process` | `FluxController.apiv3Batch()` (`flux.controller.ts:655`, guarded at `:650-651`) | `batch` | Organisation ladder (authenticated) — same as `api-v2` above | `RATE_LIMIT_BATCH_PROCESS_PER_MINUTE` / `_PER_HOUR` | 400/min, 4000/hour (general fallback) |
| `POST /flux/execute-from-canvas` | `FluxController.executeFromCanvas()` (`flux.controller.ts:358`, guarded at `:355-356`) | `canvas` | Organisation ladder (authenticated) — same as `api-v2` above | `RATE_LIMIT_EXECUTE_FROM_CANVAS_PER_MINUTE` / `_PER_HOUR` | 400/min, 4000/hour (general fallback) |
| Email trigger (POP3 cron) | `MailService.processEmail()` (`mail.service.ts:359`, called from `getPop3Email()`, itself driven by the `listPop3Emails` cron every 10s) | `email` | **Not** the organisation ladder — hardcoded to `flow:<id>` (`mail.rate-limit.ts` calls `service.check('email-trigger', { kind: 'flow', value: flowId })` directly; there is no `Request` object to resolve a company or user from) | `RATE_LIMIT_EMAIL_TRIGGER_PER_MINUTE` / `_PER_HOUR` | 400/min, 4000/hour (general fallback) |

A sixth limiter, separate from the five above and from the general/specific fallback rule
entirely:

| Limiter | Where it runs | Limiter key | Env var | Effective limit |
|---|---|---|---|---|
| Master API key | `ApiKeyStrategy.validateMaster()` (`apikey.strategy.ts:80`), via `MasterApiKeyService.consumeRateLimitAlwaysEnforced()` | `key-hash` — sha256 of the presented master key, so the limit is per key, not global | `MASTER_KEY_RATE_LIMIT_PER_MIN` | 600/min, 36000/hour (`masterKeyPerMinute x 60`, `rate-limit.config.ts`) |

**The master key is the one path that refuses in `report` mode.** `consumeRateLimitAlwaysEnforced()`
reads `decision.wouldRefuse`, the mode-independent signal, not `decision.refuse`. Before this module
the master-key limiter was an unconditional in-memory sliding window; reading `refuse` would have
made the key unlimited on merge, since `refuse` is only ever `true` under `RATE_LIMIT_MODE=enforce`.
`report` mode exists to size customer-facing traffic that is still being measured; the master key is
internal-only and was already enforcing, so it keeps enforcing. A **degraded** decision (Redis
unavailable) still admits — the limiter never locks ops out because its own counter is down.

**The master key is exempt from the organisation stage.**
`OrganisationRateLimitGuard.shouldSkipStage()` returns `true` for a master principal
(`organisation-rate-limit.guard.ts:26-28`), and `RateLimitGuardBase.canActivate()` consults that
hook before `resolveKey` and before `service.check` (`rate-limit.guard-base.ts:34-41`), so the
stage increments nothing for a master-key request and never charges one to a customer's
`company:<id>` bucket. Note what this does *not* mean: the master key's own limiter writes a counter
in the same Redis namespace, because `consumeRateLimitAlwaysEnforced()` calls `check()` without a
stage and `rate-limit.service.ts:84` defaults the stage to `organisation`. The key is therefore
counted at `rl:organisation:<window>:master-key:key-hash:<hash>`. Finding that key in Redis is the
per-key limiter working, not the exemption failing. Two reasons: the
act-as-space branch returns the *target company's owner* as the principal
(`apikey.strategy.ts:159-160`), so the stage used to spend the customer's 400/minute budget on the
master operator's traffic; and a refusal thrown by `RateLimitGuardBase` writes no
`master_key_access_log` row, so such a refusal was invisible in the master-key audit trail. The
600/min per-key limiter above already covers the key and already writes that row, so the exemption
leaves the master key with two limits rather than three: this 600/min per-key limiter, which logs,
and the pre-auth floor.

Under `RATE_LIMIT_MODE=enforce` this is a deliberate loosening: a master key's ceiling on the two
routes that can carry a master principal rises from the general 400/minute to its own 600/minute. The **pre-auth** stage still applies: it runs
before authentication, is keyed by the sha256 of the presented credential, and is unchanged.

None of the five routes ships a per-route override today — every `RATE_LIMIT_<ROUTE>_PER_*` var in
`.env.example` is blank, so all five currently enforce (in `enforce` mode) or report against (in
`report` mode) the general limit: **400/min, 4000/hour**. Setting a route-specific value later is a
config change, not a code change — `rate-limit.config.ts` reads it at startup.

## How a limit is chosen

`limitsForRoute()` (`rate-limit.config.ts`) picks, per window, the pre-auth window when the caller is
the pre-auth stage, otherwise the route's own env override if one is set, otherwise the general
value. There is never "no limit" — the general value is always the
floor.

The relationship between the general value and any per-route override is a startup invariant, not
a convention:

```
specific  <=  general  <=  10 x specific
```

`loadRateLimitConfig()` calls `assertInvariant()` for every one of the five routes at boot. A
general value tighter than a route's override, or looser than ten times it, throws and the process
does not start — a mistyped env var is a boot failure, not a silent hole or a silent lockout.

The pre-auth floor has its own startup invariant,
`assertPreAuthIsNotTighterThanGeneral()`: `pre-auth >= general`, per window. A pre-auth floor
tighter than the product limit would make the unauthenticated stage the binding constraint on a
legitimate caller, which is the one outcome this limiter must not produce, so it is a boot failure
too.

**`master-key` is the deliberate exception.** Its entry (`perRoute['master-key']`) is written
directly after that loop, outside `assertInvariant()`. `MASTER_KEY_RATE_LIMIT_PER_MIN` defaults to
600/min, which is above the 400/min general default — running it through the invariant as written
would refuse to boot on the shipped defaults. Master keys are internal-use only and looser on
purpose (see `S7-RATE-LIMITING-RUN-ENTRY-POINTS.md`, "Reconciling the master-key limiter"), so it is
registered as its own bucket instead.

## The two windows: minute and hour, and what "both" costs you

Every check walks `minute` then `hour` (`RateLimitService.check()`, `rate-limit.service.ts`). A
minute-only limit lets sustained abuse that stays just under the per-minute cap run forever. An
hour-only limit either admits a whole hour's budget in one burst or hands a caller who trips it a
`Retry-After` approaching an hour. Stacking both windows closes both holes.

`check()` increments **every** window first and decides afterwards
(`incrementEveryWindow()`, `rate-limit.service.ts`), so the hour counter keeps advancing for a
caller already over the minute limit. An earlier revision returned on the first breached window,
which under-counted the hour window for exactly the callers most worth measuring and so biased the
eventual limits downward — straight into false refusals later. The reported `window` is still the
first breached one in `minute`, `hour` order, so `Retry-After` stays the shorter of the two.

The cost of incrementing unconditionally is that a refused attempt also spends hour budget. That is
accepted: while `RATE_LIMIT_MODE=report` nothing is refused at all, and the whole purpose of the
report cycle is an accurate hour-window peak.

## The report/enforce switch

`RATE_LIMIT_MODE` defaults to `report`: `RateLimitService.check()` still walks both windows and
still returns `wouldRefuse: true` on a breach, but `refuse` is only `true` when
`config.mode === 'enforce'`. In `report` mode, `refuse` is always `false` — every request is
admitted, decided and logged, refused never.

**This is an environment variable, not a feature flag.** That was a deliberate choice — a
`FeatureFlagsService.isEnabled` check is a Postgres read per call, which is exactly the per-request
cost this limiter exists to avoid paying under flood. Despite this file's name, do not describe
`RATE_LIMIT_MODE` as a flag anywhere; it is read once from `process.env` at module init
(`rate-limit.module.ts`), not evaluated per request against a `feature_flags` row.

## The enforce gate

The limit values shipped in `.env.example` are sized against aggregate production traffic
(≤23 calls/min and ~273 calls/hour across all tenants on the busiest limited run types), but no
per-key peak has ever been measured. Do not set `RATE_LIMIT_MODE=enforce` until a full report-only
cycle has run and its per-key peaks have confirmed these numbers. The acceptance bar for that cycle (see `S7-RATE-LIMITING-RUN-ENTRY-POINTS.md`,
"No legitimate caller is refused"): classify every `wouldRefuse: true` decision from the cycle as
either **correctly refused** or **refused although it works**, and drive the second count to zero
before flipping the switch. Where a case cannot be classified from the log, report it as
unverifiable rather than counting it as correctly refused.

## Behaviour under failure: fails open

`RateLimitStorage.increment()` (`rate-limit.storage.ts`) wraps every Redis command
(`INCR`, `PEXPIRE`, `PTTL`) in `withRedisCommandTimeout()` (`redis-command-timeout.ts`), which races
the command against a **250ms** (`REDIS_COMMAND_TIMEOUT_MS`) timer.
`RateLimitKeyResolver`'s flow-to-company cache (`GET`/`SET`) uses the same helper, for the same
reason: `redis.module.ts` configures `maxRetriesPerRequest: null` with a retry strategy that never
surrenders and an offline queue, so during an outage an ioredis command **hangs rather than
rejecting** — a bare `try`/`catch` around it never runs. If Redis is unreachable, or a command does not answer
inside that window, the `catch` block logs `'Rate limit counter unavailable, admitting request'`
via `console.error` and returns `{ totalHits: 0, timeToExpireMs: 0, degraded: true }`.

`RateLimitService.check()` treats `degraded: true` as an immediate admit — it returns
`admit(0, limit, true)` in both `report` and `enforce` mode. Both windows are still incremented
first (`rate-limit.service.ts:62` reads `degraded` from the outcomes it has already collected);
what a degraded check skips is the refusal decision, not the counting. The
request is admitted even while enforcing, and the decision carries `degraded: true` so it can be
told apart from a normal admission in the logs. A degraded check also logs one
`'Rate limit check degraded, admitting request'` line via `console.error` — one line per check, not
per command — so a Redis outage is visible instead of silently adding latency. A limiter that refuses because its own counter is
unavailable is worse than no limiter — a Redis blip should never turn into an outage for the routes
it protects.

## What a refused caller receives

**The four HTTP routes** (`api-v2`, `api-v2-webhook`, `batch-process`, `execute-from-canvas`), via
`RateLimitGuardBase.canActivate()` (`rate-limit.guard-base.ts`): a `429` (`HttpStatus.TOO_MANY_REQUESTS`)
with a `Retry-After` header set to `decision.retryAfterSeconds`, thrown as

```ts
new HttpException(
  { error: 'error', data: { message: 'Rate limit exceeded' } },
  HttpStatus.TOO_MANY_REQUESTS,
)
```

The retry delay travels in the `Retry-After` header only. It is deliberately absent from the body:
`CustomExceptionFilter` reshapes the payload and drops any key it does not know, so a
`retryAfterSeconds` field in the body never reached the client.

`CustomExceptionFilter` (`src/common/custom_exception_firlter.service.ts`) then reshapes this.
It reads `exceptionResponse['message']` for the top-level `message` field — this exception body has
no `message` key (only `error` and `data`), so that lookup is `undefined`. It
reads `exceptionResponse.data.message` for the `error` field, which **is** present here
(`'Rate limit exceeded'`). Document what actually reaches the caller, not what would be ideal: the
JSON body is

```json
{
  "message": "ERROR <uuid>: undefined",
  "statusCode": 429,
  "error": "Rate limit exceeded"
}
```

The reason does reach the caller, in `error` — but `message` renders literally as the string
`"undefined"` interpolated into the error-id line. This is an existing property of
`CustomExceptionFilter` (any `HttpException` whose body has `data.message` but no top-level
`message` hits the same path), not something specific to rate limiting, but a caller parsing this
response needs to read `error`, not `message`.

**The email trigger** cannot answer with an HTTP status — there is no request to respond to.
`applyEmailTriggerRateLimit()` (`mail.rate-limit.ts`) instead replies to the original sender by
email, but **only on the first refusal in each window**, detected as
`decision.count === decision.limit + 1`. Every subsequent refusal in the same window is logged but
sends no mail. This matters because the inbound `From:` address is unauthenticated and
attacker-controlled: replying to every refused message would turn the rate limiter into a
backscatter reflector, generating outbound mail to a forged address in direct proportion to the
attacker's send rate — adding outbound mail traffic exactly while the system is trying to shed
load. Suppressing the bounce after the first refusal removes that amplification while still telling
a legitimate sender once that they hit the limit. The refusal is logged (`'Rate limit decision'`,
same shape as the guards) on every occurrence regardless of whether the mail is sent.

**The master API key** gets a `429` from `ApiKeyStrategy.rateLimitedKey()` (`apikey.strategy.ts`) —
same body shape as the four HTTP routes (`{ error: 'error', data: { message: 'Rate limit exceeded' } }`),
so it goes through the same `CustomExceptionFilter` reshaping above. **It carries no `Retry-After`
header** — `rateLimitedKey()` builds a bare `HttpException`, unlike `RateLimitGuardBase` which sets
the header before throwing. The rejection also writes a `master_key_access_log` row with
`outcome: 'rejected_rate'` and `statusCode: 429`. Every other master-key rejection outcome
(`rejected_ip`, `rejected_invalid`, `rejected_not_owner`, `rejected_bad_target`) is unchanged: those
stay `401` (`UnauthorizedException`) with `statusCode: null` in the audit row.

## Measurement

Every guard and the email-trigger path log one uniform line per decision, built by
`buildRateLimitLog()` (`rate-limit.decision-log.ts`) and written at `rate-limit.guard-base.ts:40`
and `mail.rate-limit.ts:26`:

```
console.log('Rate limit decision', {
  stage, route, keyKind, key, count, limit, window,
  wouldRefuse, refused, trigger, observationThreshold,
})
```

A line is written in exactly two cases, and `trigger` says which:

| `trigger` | Written when | `wouldRefuse` / `refused` | `observationThreshold` |
|---|---|---|---|
| `breach` | the count exceeded the **real** limit for a window | `true` / `true` only under `enforce` | `null` |
| `observation` | the **minute** count reached the observation threshold but no limit was breached | `false` / `false`, always | the threshold that fired |

Never both, and never more than one line per decision — `buildRateLimitLog()` returns a single
payload or `null`, and a breach takes precedence over an observation.

### The observation threshold, and why it exists

Without it, `report` mode logs nothing. Production peaks at ~23 calls/min against a 400/min limit,
so `wouldRefuse: true` never happens in a normal week and the report cycle — the gate for ever
enabling enforcement — would produce zero data.

There is exactly one env var, and it is per minute:

| Env var | Default | Meaning |
|---|---|---|
| `RATE_LIMIT_OBSERVATION_PER_MINUTE` | 5 | log when a **per-key** minute count reaches 5 |

Read by `loadRateLimitConfig()` into `config.observationPerMinute` (`rate-limit.config.ts:131`),
validated as a positive integer like every other limit.

The default is 5 because the threshold is evaluated **per resolved key**, while the ~23 calls/min
figure is the aggregate across every tenant; a single organisation does roughly 1 to 3 calls per
minute, so a per-key threshold of 50 would never be crossed. Total production traffic is about 805
runs/hour (~13/min across all keys), so at that volume the extra log volume is trivial. That is a
statement about normal traffic, not a bound: `rate-limit.service.ts:63` compares `>=` with no
per-window dedup, so once a key crosses the threshold in a minute, every request after it in that
same window logs its own line too, not just the crossing one. Volume is bounded by inbound traffic,
not by the threshold — a single key flooding the pre-auth stage can emit up to its stage's own limit
in lines per minute (4000/min at the pre-auth floor), not merely the lines above the threshold.

That single env var does not give an exact per-key hourly total. What the
minute-level lines *do* let you recover: the per-key, per-minute count for every minute that reached
the threshold; every actual limit breach, since a breach logs regardless of the threshold; and the
distribution of resolved key kinds, including how much traffic lands in the shared `user:unresolved`
bucket. What they do **not** recover: the exact hourly total for a key. `findObservation()`
(`rate-limit.service.ts:57-72`) only fires when a **minute** count reaches the threshold (5 by
default), so a key that never crosses 5 calls in any single minute of the hour writes nothing at
all — a tenant steady at the typical 1-3 calls/min reconstructs as **zero**, not its real ~60-180.

That is accepted, not a gap to close. The cycle's job is to confirm no legitimate caller would be
refused and to size the limits against observed peaks, not to reproduce exact hourly totals: a key
that never crosses 5 in a minute is, by that fact, nowhere near the 400/minute limit its stage
enforces, and the hour limit (4000) was derived as 10x the minute limit and already carries ~15x
headroom over the largest observed hourly peak. If exact per-key hourly totals are ever needed,
lower `RATE_LIMIT_OBSERVATION_PER_MINUTE` to 1, which logs essentially every decision (~805
lines/hour at current production volume) — this is a single knob deliberately; do not add a second,
per-hour env var. This is unrelated to `RATE_LIMIT_GENERAL_PER_HOUR` (4000), the real per-hour
enforcement limit, which is unchanged.

**It cannot refuse anything.** `RateLimitService.check()` computes the refusal in `decideRefusal()`,
which is not given the threshold at all, and only then attaches `observation` to the returned
decision (`rate-limit.service.ts:100`). No code path lets the threshold reach `refuse`,
`wouldRefuse`, `retryAfterSeconds` or the 429. `rate-limit.observation.spec.ts` pins this: for a
matrix of counts it asserts that every field of the decision is identical across a matrix of
thresholds in **both** `report` and `enforce` mode, and that the guard's actual admission (200
versus 429) is identical across that same matrix in **enforce** mode — `report` mode refuses
nothing by construction, so a guard-level admission assertion there would be true regardless of
what the threshold did.

Tuning it is a config change: raise it to quieten the signal, lower it to 2 or 1 if a cycle
produces too few lines.

**This threshold is provisional** and should be revalidated and retuned after the first real report
cycle, against the per-key peaks that cycle produces.

### Finding the line

This is a plain `console.log`, not routed through `WinstonLogger`. That distinction matters for
finding it: `WinstonLogger.log()` ships to Datadog through its own dedicated HTTP transport
(`src/logging/winston.logger.ts`), tagged `service=EnhancedAILogging` and nesting call metadata
under a `usage` key. The rate-limit line bypasses that transport entirely and does not nest its
fields under `usage` — it is a flat object written straight to stdout. A `service:EnhancedAILogging`
/ `@usage.*` filter will not match it; search for the literal message `"Rate limit decision"` and
its flat fields instead.

Grouping the observation lines by `key`, `keyKind`, `route` and `window` and taking `max(count)`
gives the **per-key peak** — the number the SQL exports could not provide, since `flows_logs` has no
notion of the resolved limiter key.

**Production sizing of the aggregate windows is still not read from the Redis counters.** The
counters are ephemeral (windowed `INCR`/`PEXPIRE` keys) and only hold the current window's count —
they answer "is this caller over the limit right now," not "what was the peak last week." The
aggregate sizing comes from SQL over `flows_logs`, grouped by `run_type` and time bucket; the
per-key sizing comes from the observation log above. See `S7-RATE-LIMITING-RUN-ENTRY-POINTS.md`,
"The measurement cycle".
