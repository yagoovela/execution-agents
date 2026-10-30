> **Source paths in this document are relative to `back/`.** It was written alongside the
> implementation and lived at `back/docs/` until it was moved here, where this kind of content
> belongs. Recover the original at any time with
> `git show 3af52fba:docs/<file> ` in the `back` repo.

# Rate limiting the run-creating entry points

S7 part 2 — ClickUp `868m0vkcj`. Spec: `.claude/tasks/worker-flow-execution-epic/TASK-S7-ENTRY-POINT-CONTROLS.md`.

## Why

`AGENT_CONCURRENCY` (default 5 per replica) throttles **execution**, not **admission**. A request
that reaches a run-creating route writes a `flows_logs` row and log lines on the way in, and
`/api-v2` additionally writes a `flow_execution_status` row before it queues
(`flux.controller.ts:213`, the only call site of `flowExecutionStatusService.create`). There is no `ThrottlerModule`, no
`@Throttle` and no `ThrottlerGuard` anywhere in `back/src`, so a misconfigured integration or a
caller with a valid API key can grow the queue and the storage bill without limit before a single
request is refused.

This card adds admission control. It does not change how runs execute.

## What is limited

Five entry points are in scope. All routes are in `src/app-api/flux/flux.controller.ts`.

| Entry point | Line | `runType` | Limit key | Provisional limit |
|---|---|---|---|---|
| `POST /flux/api-v2` | 184 | `api` | `company:<id>`, else `user:<id>` | 400/min, 4000/hour |
| `POST /flux/batch-process` | 643 | `batch` | `company:<id>`, else `user:<id>` | 400/min, 4000/hour |
| `POST /flux/execute-from-canvas` | 352 | `canvas` | `company:<id>`, else `user:<id>` | 400/min, 4000/hour |
| `POST /flux/api-v2-webhook` | 471 | `webhook` | `company:<id>`, else `flow:<id>` | 400/min, 4000/hour |
| Email trigger (POP3 cron) | `src/app-api/mail/mail.service.ts:541` | `email` | `flow:<id>` (always — bypasses the ladder) | 400/min, 4000/hour |

None of the five routes has a per-route override configured — every `RATE_LIMIT_<ROUTE>_PER_*` var
in `.env.example` is blank, so all five currently fall back to the general limit,
**400/min, 4000/hour**. These values are provisional pending production sizing (see "Provisional
values, and the gate to enforce" below). The limit key and the limit in the table above are the
**organisation** stage; the pre-auth stage in front of it has its own key and its own, looser limit
(`RATE_LIMIT_PRE_AUTH_PER_MINUTE` / `_PER_HOUR`, 4000/min and 40000/hour by default) — see
"Reconciling the master-key limiter" below. For the shipped per-route behaviour (handlers, guards, env
vars) see [`S7-RATE-LIMIT-ENV-AND-MODES.md`](./feature-flags-and-rate-limits.md), the source of
truth for what is actually enforced today.

The email trigger is not HTTP, so it cannot carry a 429. It refuses through the bounce-back reply
that already exists in `mail.service.ts`, which the spec explicitly says to keep.

### Out of scope, and why it is written down

The same controller exposes five more doors that create runs through the same primitive. They are
**not** limited by this card and need one of their own:

| Entry point | Line | Guard today | Why it is deferred |
|---|---|---|---|
| `POST /flux/run-public-flow/:id` | 1615 | none | Reachable with no credential. Needs a limit, but keyed per end user, not per flow. |
| `POST /flux/beta-v2` | 581 | `@Public` + Jwt | Same. |
| `POST /flux/formapi-v1` | 1353 | `@Public` + Jwt | Same. |
| `POST /flux/execute-single-node` | 412 | Jwt | Canvas UX: a user clicks Run on several nodes in a row. A per-flow or per-org key refuses legitimate bursts. |
| `POST /flux/chatbot-api-socket` | 1008 | `@Public` + Jwt | One call per end-user message, all sharing one `flowId`. A busy public chatbot exceeds a per-flow limit with nobody abusing it. |

`execute-single-node` and `chatbot-api-socket` are the two that would refuse real users if limited
with the keys this card uses. That is the reason they are deferred rather than included: they need a
per-end-user key, which is its own design.

## The key is the paying entity, never the IP

An IP is meaningless for server-to-server callers, so it is not used. The key is resolved in this
order, and every limited entry point always resolves to exactly one key:

| Order | Key | When |
|---|---|---|
| 1 | `company:<id>` | Whenever the organisation is derivable — see below. |
| 2 | `user:<id>` | An **authenticated** caller whose organisation is not derivable. The ladder stops here. |
| 3 | `flow:<id>` | An **unauthenticated** caller — the `@Public()` webhook route. The email trigger also keys by flow, but bypasses this ladder entirely. |
| 4 | `user:<unresolved>` | Nothing above resolved. |

Order 2 before order 3 is deliberate and matches `rate-limit-key.resolver.ts:42-60`: once a
request carries an authenticated user, the ladder terminates at that user and never falls
through to the flow. See "How the organisation is derived" below for the full table.

### How the organisation is derived — measured, not assumed

Four paths reach a company. Their coverage was measured against 7 days of **dev** `flows_logs`
(2,276 runs), because picking one on structural grounds alone produced the wrong answer:

| Path | Derivation | Coverage (webhook) | Ambiguity |
|---|---|---|---|
| A | `folder.spacesId` → `spaces.companyId` | **0.7%** | none |
| **B** | **`folder.companyUserId` → `company_user.companyId`** | **99.3%** | none — one row, one company |
| C | flow owner's `company_user` memberships | 100% | **up to 3 companies** |
| D | flow owner's owned `companies.userId` | 99.9% | none in dev (max 1 owned) |

Path A is the one this document originally chose, and it resolves almost nothing: `folders.spacesId`
is NULL for 1,372 of 1,382 webhook runs and for all 877 `library-node` runs. The flow has a folder
and the folder exists — the folder simply is not attached to a space. Choosing A would have keyed
99% of traffic by `user:<id>` while the document claimed it was keyed by organisation.

**Path B is the primary derivation.** It also reads better than A: the folder belongs to a
company-user, so the company owning the folder that owns the flow is the payer. The ladder:

| Order | Key | Source |
|---|---|---|
| 1 | `company:<id>` | The space the **validated principal** carries — `apiKeySpaceId`, stamped by `apikey.strategy.ts:68` from the api key itself. Most specific; use it when present. No request header is read here: see "Why the resolver does not read `x-flux-act-as-space`" below. |
| 2 | `company:<id>` | Path B — `folder.companyUserId` → `company_user.companyId`. The normal case. |
| 3 | `company:<id>` | Path D — the company the flow owner owns. Last resort; only when exactly one. |
| 4 | `user:<id>` | An authenticated caller who owns no company. **The ladder stops here** — `flow:<id>` is never reached for `/flux/api-v2`, `/flux/batch-process` or `/flux/execute-from-canvas`. |
| 5 | `flow:<id>` | Only when there is no authenticated user: the `@Public()` webhook route. The email trigger also keys by flow, but it bypasses this ladder entirely and calls `check` with the flow key directly (`mail.rate-limit.ts`), having no `Request` to resolve from. |
| 6 | `user:<unresolved>` | Floor, when nothing above resolves. |

As implemented in `rate-limit-key.resolver.ts:43-62`. Note that orders 4 and 5 are the reverse of
what an earlier draft of this document assumed: a flow id is consulted at order 2 to *derive* a
company, but `flow:<id>` as the final key belongs to unauthenticated callers only.

Path C is rejected: a user with three memberships has no single answer, and picking one silently
would cap a company the caller was not acting for.

**These figures are dev.** Dev flows are not attached to spaces the way customer flows may be, so
the coverage query is part of what runs against production before the ladder is trusted. If path B
does not hold in prod, the ladder changes again — that is why the numbers are recorded here with
their source rather than asserted.

### The cost, and how it is paid

Deriving the organisation is a three-join read, and the guard runs **before** the handler that would
have loaded the flow anyway. A Postgres read per admitted request is the cost this card exists to
stop paying under flood, so the `flow:<id> → company:<id>` mapping is cached in Redis with a TTL. A
stale mapping caps the wrong bucket for one TTL, which is far cheaper than a join per request.

### Why the resolver does not read `x-flux-act-as-space`

An earlier revision of the resolver read the header directly, because the master-key-with-target-
space branch of the strategy resolves `space.company.user` and returns **without** stamping
`apiKeySpaceId` (`apikey.strategy.ts:159-160`) — the space is known during validation and discarded
after. That header read was a cross-tenant denial of service: `resolveSpaceId` applied it to *any*
principal, not only a master, so any authenticated caller could send
`x-flux-act-as-space: <a victim's space id>` and have every one of its requests counted against
`company:<victim>`. Under `enforce` that refuses a paying customer because of someone else's
traffic — the outcome this card calls worse than the defect it fixes. The strategy validates the
header (`:109-131` verifies the master key first, then `:138-150` looks the space up and rejects a
bad target with `REJECTED_BAD_TARGET`); the resolver restated a version of that rule with the validation removed, which
is exactly the drift the "import the product's rule, never restate it" constraint exists to stop.

The header rung is deleted. No legitimate caller loses attribution, because all three paths are
already covered without it:

| Caller | How the organisation is still derived |
|---|---|
| Space-scoped api key | `apikey.strategy.ts:68` stamps a validated `apiKeySpaceId` from the key; order 1 uses it. |
| Master key acting as a space | It no longer needs one. `apikey.strategy.ts:159` stamps `isMaster = true` on `space.company.user` before returning it, and `OrganisationRateLimitGuard.shouldSkipStage()` skips the whole stage for a master principal (see "Why the master key skips the organisation stage"). |
| Everyone else | No space; the ladder falls through to the flow and user rungs as designed. |

The caveat that used to sit here — that a target owner holding more than one company falls through
`findCompanyOwnedBy`'s `rows.length === 1` guard to `user:<target owner id>` — no longer applies to
the master path, because the master path no longer reaches the ladder at all. It still applies to
every non-master authenticated caller that gets as far as order 3.

### Why the master key skips the organisation stage

`OrganisationRateLimitGuard.shouldSkipStage()` returns `true` when `isMasterPrincipal(req.user)`
(`src/app-api/rate-limit/organisation-rate-limit.guard.ts:26-28`), and
`RateLimitGuardBase.canActivate()` consults that hook immediately after the unannotated-route early
return — **before** `resolveKey` and before `service.check`
(`src/app-api/rate-limit/rate-limit.guard-base.ts:34-41`, with the default no-skip hook at
`:30-32`). So a master-key request touches neither Postgres, nor the Redis `flow → company` cache,
nor any organisation counter belonging to a customer.

One namespace caveat, so nobody reads Redis and concludes the exemption broke: the master key's own
limiter shares the `organisation` stage prefix. `MasterApiKeyService.consumeRateLimitAlwaysEnforced()`
calls `check()` with no stage argument and `rate-limit.service.ts:84` defaults it to `organisation`,
so the per-key counter lives at `rl:organisation:<window>:master-key:key-hash:<hash>`. What the
exemption removes is the *ladder* lookup and any `company:<id>`/`user:<id>` counter, not this one.

Two reasons, both of which the stage got wrong for a master key:

1. **Attribution.** Both master return points stamp `isMaster = true` — `apikey.strategy.ts:134`
   (the key's own owner) and `:159` (acting as a target space). The second returns the *target
   company's owner* as the principal, so the ladder resolved `company:<target>` and spent the
   customer's 400/minute budget on the master operator's traffic.
2. **Audit.** A refusal thrown by `RateLimitGuardBase` writes no `master_key_access_log` row, so a
   master-key request refused by the organisation stage was invisible in the audit trail that exists
   precisely to record master-key access.

The master key is not unlimited as a result: it keeps two limits, one of which logs. `MasterApiKeyService.consumeRateLimitAlwaysEnforced()` caps it at 600/minute **per key**,
Redis-backed and enforced regardless of `RATE_LIMIT_MODE`, and its refusal writes
`MasterKeyAccessOutcome.REJECTED_RATE` with `HttpStatus.TOO_MANY_REQUESTS`
(`src/app-auth/strategies/apikey.strategy.ts:99-107`).

State the consequence plainly, because it is a loosening and not a neutral refactor: under
`RATE_LIMIT_MODE=enforce`, a master key's ceiling rises from the general 400/minute to its own
600/minute. It applies to the two routes that can carry a master principal — `api-v2`
(`flux.controller.ts:186`) and `batch-process` (`:651`), the only two whose guard chain includes
`ApiKeyGuard`. The other two organisation-stage routes cannot produce a master principal at all:
`:356` authenticates with `JwtAuthGuard` and `:477` carries no authentication guard.

The **pre-auth** stage is deliberately unchanged for master keys. It runs before authentication, so
`req.user` does not exist when `PreAuthRateLimitGuard` executes and there is no organisation bucket
to protect; it is keyed by the sha256 of the presented credential either way.

The strategy-side observation stands and is still worth knowing: all four `done(null, ...)` return
points were audited (`:57`, `:69`, `:136`, `:160`) and `:160` is the only one that loses context.
`jwt.strategy.ts:27` returns `{ ...user, userId }` and drops nothing.

### The residual leak

The same payer can hold a user-level API key and a space-level API key. Where the flow reaches a
space both now collapse to the same `company:<id>`. Where it does not, they remain two keys and the
payer gets two buckets. Closing that completely would mean picking one of the N companies a user
owns (`user.company` is a `@OneToMany`, `user.entity.ts:212`), which is the ambiguity the
space-based reading exists to avoid. It is recorded rather than hidden.

## Where the limit sits, and why not at the choke point

Every door reaches one of two primitives: `apiV2Queue.enqueueApiV2Job()` (`/api-v2`,
`/api-v2-webhook`, the email trigger) or `fluxService.apiV2()` (the rest).

Putting the limit on `apiV2()` looks tempting — it is one place, and it would also cap
`/batch-process`, which fans out internally (one HTTP request loops rows calling `apiV2()` per row,
`flux.controller.ts:778`). It is the wrong place, for two reasons:

1. `apiV2()` is also called by sub-flows (`flowCallerNode`), by schedule-triggered runs
   (`src/app-api/schedule/schedule.controller.ts:159,311`) and by the queue consumer
   (`src/jobs/apiV2Job/apiV2Job.processor.ts:71`). A limit there refuses **internal** work that
   never crossed the boundary — the false refusal that PLAN §3.3.2 calls a production incident.
2. PLAN D18 keeps `/flux/batch-process` permanently but moves its body into `B7`'s durable
   workflow. A limit inside that body moves with it or is lost; a limit on the route survives.

So the limit sits on the **route**. The consequence is stated rather than hidden: one
`/batch-process` request can still admit a large fan-out. Capping runs per batch is a separate
ceiling and belongs to `S3`, where excess tenant runs are queued rather than refused (PLAN D9).

## Refusal

`429` with `Retry-After` derived from the window TTL. Refusing is right at admission: queueing an
unbounded inbound flood only relocates it. This is a deliberate contrast with `S3`/D9, where excess
tenant runs are queued because that caller is already entitled to the work. The two must not be
collapsed into one shared "ceiling" abstraction.

## Counters live in Redis

`@nestjs/throttler` with Redis storage (`@nest-lab/throttler-storage-redis`, 1.2.0 — neither is in
`package.json` today), on the Redis that Bull already uses. The API runs more than
one replica, so in-process counters would make the effective limit `configured × replicas` and a
distributed flood would pass. With Redis the configured limit is the real limit.

Cost is one INCR/EXPIRE per request. If Redis is unreachable the limiter **fails open** (admits) —
at admission, availability of the product outranks the limit, and a Redis outage already degrades
the queue this card protects.

## Mode switch: report before enforce

One env var, read at startup:

| `RATE_LIMIT_MODE` | Behaviour |
|---|---|
| `report` (**default**) | Decide, log the decision, **always admit**. Refuses nothing. |
| `enforce` | Refuse over-limit requests with 429 + `Retry-After`. |

`report` is the default so that deploying this card changes no behaviour, per PLAN §3.2 ("the flag
defaults to today's behaviour"). Flipping to `enforce` is a separate, deliberate deploy.

The switch is an env var rather than a `feature_flags` row on purpose: `FeatureFlagsService.isEnabled`
issues a `findOne` per call, and a Postgres read on every admitted request is exactly the per-request
cost this card exists to stop paying under flood.

## Two windows, general and specific

### Why both a minute and an hour

An hour-only limit does not delay *detecting* a flood, but it does two other harmful things: a
fixed hourly bucket admits its whole budget in one second and then refuses for the remaining 59
minutes, and the `Retry-After` it hands a caller who tripped it can approach an hour. A minute-only
limit has the opposite hole: sustained abuse that parks just under the cap is admitted forever —
399/min is 23,940 runs in an hour, every one of them accepted.

So both, stacked. `@nestjs/throttler` supports multiple named throttlers for exactly this:

| Window | Bounds | Role |
|---|---|---|
| `short` | per minute | Burst. This is the one that stops a flood inside a minute. |
| `long` | per hour | Sustained spend. Stops the just-under-the-minute-cap pattern. |

### General and specific

Every limited entry point resolves a limit the same way: **use the route's own value if it is
configured, otherwise use the general one.** There is never no limit.

The general value is a permissive backstop; a per-route value tightens one route. The relationship
between them is an invariant, not a convention:

```
specific  <=  general  <=  10 x specific
```

The general may not be tighter than any route's own limit, and it may not be more than ten times
looser. This is validated at startup and fails fast, so a mistyped env var is a boot error rather
than a silent hole or a silent lockout.

### The sized values, and the gate to enforce

The general windows are now sized against 7 days of production traffic rather than inferred from a
single global maximum:

| Default | Value | Where |
|---|---|---|
| `RATE_LIMIT_GENERAL_PER_MINUTE` | 400 | `DEFAULT_GENERAL_PER_MINUTE`, `rate-limit.config.ts` |
| `RATE_LIMIT_GENERAL_PER_HOUR` | 4000 | `DEFAULT_GENERAL_PER_HOUR`, `rate-limit.config.ts` |
| `RATE_LIMIT_PRE_AUTH_PER_MINUTE` | 4000 | general x `PRE_AUTH_GENERAL_MULTIPLE` |
| `RATE_LIMIT_PRE_AUTH_PER_HOUR` | 40000 | general x `PRE_AUTH_GENERAL_MULTIPLE` |

What the production data established: the busiest run types that actually reach a limited route
peak at ~273 calls/hour aggregated across **all** tenants, and no limited route exceeded **23 calls
in any single minute**. Limits are per organisation, so a single tenant sits well below those
aggregates. The two largest run types overall (`library-node`, `flow-caller-node`, ~440/hour
combined) are created in-process and never traverse a guard, so they are deliberately not sized in.

Why 4000 per hour: it restores the design rule that the hour limit is ~10x the minute limit
(400 x 10), which the previous 7000 broke at 17.5x, and it still leaves ~15x headroom over the worst
observed hour. The pre-auth floor follows automatically, since it is the general window times ten
(40000/hour), keeping it a floor that never binds a legitimate caller.

Two honest limits on the derivation remain:

- `flows_logs` records runs **created**. A request refused earlier (401 at the guard) never appears,
  so this undercounts what arrives at the door.
- There is still no **per-key** measurement. That is what the observation threshold below exists to
  produce.

**The gate: `RATE_LIMIT_MODE=enforce` must not be set until a full report-only cycle has produced
per-key peaks and confirmed that nothing legitimate would have been refused.** The values above are
sized, not validated per caller.

## The measurement cycle

**One week** of `report` mode against real production traffic.

### The observation threshold is what makes the cycle produce data

Logging only breaches would have produced **nothing at all**: with a 400/min limit and a real peak
near 23/min, no decision in a normal week reaches `wouldRefuse: true`, so a week of `report` mode
would have written zero lines and the cycle would have measured nothing.

So the decision carries a second, independent trigger. `RateLimitService.check()` computes the
refusal in `decideRefusal()` and only then attaches `observation` to the returned decision
(`rate-limit.service.ts:100`), where `findObservation()` reports the **minute** window when its
count has reached the observation threshold. The threshold is **a logging trigger only** — it is
never read by `decideRefusal()`, never reaches `refuse`, `wouldRefuse`, `retryAfterSeconds` or the
429, and `rate-limit.observation.spec.ts` holds every field of the decision constant across a matrix
of thresholds in both `report` and `enforce` mode, and the guard's actual admission (200 versus 429)
constant across that same matrix in **enforce** mode — `report` mode refuses nothing by
construction, so pinning guard-level admission there would hold regardless of what the threshold
did.

There is exactly **one** env var, and it is per minute:

| Env var | Default | Meaning |
|---|---|---|
| `RATE_LIMIT_OBSERVATION_PER_MINUTE` | 5 | Log any decision whose **per-key** minute count reaches 5. |

It is read by `loadRateLimitConfig()` into `config.observationPerMinute`
(`rate-limit.config.ts:131`) and validated as a positive integer like every other limit, so a typo
is a boot failure rather than a silent hole.

The default is 5, not a fraction of the aggregate peak, because the threshold is evaluated **per
resolved key** while the 23/min figure is the aggregate across every tenant. A single organisation
does a small fraction of that — on the order of 1 to 3 calls per minute — so a per-key threshold of
50 would essentially never be crossed and a full week in `report` mode would log nothing. Volume
makes 5 safe at normal traffic: production runs at roughly 805 runs/hour across every run type,
about 13 per minute across all keys combined, so the resulting log volume is trivial at that scale.
That is a statement about normal traffic, not a bound on the mechanism: `rate-limit.service.ts:63`
compares `>=` with no per-window dedup, so once a key crosses 5 in a minute, every subsequent
request in that same window logs its own line too — not just the crossing one. A single key being
flooded can therefore emit up to its stage's own limit in lines per minute (4000/min at the pre-auth
floor), bounded by inbound volume rather than by the threshold. Dedup is deliberately not added:
logging every crossing is what makes the per-minute *peak* visible, whereas logging only the first
crossing would record the threshold value instead of the peak.

That single env var does not give an exact per-key hourly total. What the
minute-level lines *do* let you recover: the per-key, per-minute count for every minute that reached
the threshold; every actual limit breach, since a breach logs regardless of the threshold; and the
distribution of resolved key kinds, including how much traffic lands in the shared `user:unresolved`
bucket. What they do **not** recover: the exact hourly total for a key. `findObservation()` only
fires when a **minute** count reaches the threshold, so a key that never crosses 5 calls in any
single minute of the hour writes nothing at all — the typical tenant at 1-3 calls/min above
reconstructs as **zero** from the log, not its real ~60-180 calls/hour.

That is accepted, not a gap to close. The cycle's job is to confirm no legitimate caller would be
refused and to size the limits against observed peaks, not to reproduce exact hourly totals: a key
that never crosses 5 in a minute is, by that fact, nowhere near the 400/minute limit its stage
enforces, and the hour limit (4000) was derived as 10x the minute limit and already carries ~15x
headroom over the largest observed hourly peak (see above). If exact per-key hourly totals are ever
needed, lower `RATE_LIMIT_OBSERVATION_PER_MINUTE` to 1, which logs essentially every decision (~805
lines/hour at current production volume) — this stays a single knob deliberately; do not add a
second, per-hour env var. The real per-hour *enforcement* limit (`RATE_LIMIT_GENERAL_PER_HOUR`,
4000) is a different thing and is untouched.

One line is written per decision, never per Redis command or per window: the two guards and the
email trigger all build it through `buildRateLimitLog()` (`rate-limit.decision-log.ts`), which
returns a single payload or `null`, and log it at `rate-limit.guard-base.ts:40` and
`mail.rate-limit.ts:26`. A breach always wins over an observation, so a refused decision is still
logged exactly once, as a breach.

### The log line

Still a bare `console.log`, **not** routed through `WinstonLogger`, and still under the same message
string so existing queries keep matching:

```
console.log('Rate limit decision', {
  stage, route, keyKind, key, count, limit, window,
  wouldRefuse, refused, trigger, observationThreshold,
})
```

Two fields are new. `trigger` is `'breach'` when the count exceeded the real limit and
`'observation'` when it only crossed the observation threshold; `observationThreshold` carries the
threshold that fired and is `null` on a breach line. An observation line always carries
`wouldRefuse: false` and `refused: false` — nothing was refused. For an observation line, `count`,
`window` and `limit` describe the window that crossed the threshold, so `limit` is the real limit
for that window, not the threshold.

### Reading it back as per-key peaks

Aggregation: this line bypasses the `WinstonLogger` -> Datadog HTTP transport entirely
(`src/logging/winston.logger.ts`), which is what tags a log `service:EnhancedAILogging` and nests
its fields under `usage`. A `service:EnhancedAILogging` / `@usage.*` query will **not** match it — it
is a flat object written straight to stdout, with no `service` attribute and no `usage` wrapper.
Whatever picks up stdout in the deployed environment (a container log driver or agent) is the
pipeline that carries this line to an aggregator; match on the literal message
`"Rate limit decision"` and the flat field names above, for example (Datadog):

```
"Rate limit decision" env:production trigger:observation window:minute
```

Grouped by `key` (and `keyKind`, `route`, `stage`), the maximum `count` per group is the per-key
peak for that window — precisely the number the SQL exports over `flows_logs` could not provide,
because that table has no notion of the resolved limiter key. `trigger:breach` over the same period
is the set of decisions that would have been refused.

**If the cycle produces no observation lines at all, the threshold is too high, not the traffic too
low.** Tuning it is a config change and costs one line per crossing decision, so the first days of
the cycle should be used to settle it before drawing any conclusion about peaks: if 5 still yields
too little data, lower it to 2 or 1; if it floods, raise it.

**Follow-up, not made on this branch:** routing these logs through `WinstonLogger` with `usage.*`
metadata — so they match the rest of the app's observability — is a deliberate, separate change.
`WinstonLogger` is `@Injectable()` but not `@Global()` (provided only in `app-api.module.ts:317`),
so it needs module wiring plus changes to both rate-limit guards, the shared guard base, the mail
helper, and their specs.

**Follow-up, and it is the one that must not be forgotten:** the observation threshold is
**provisional**. It was chosen from aggregate, not per-key, production numbers. Revalidate and
retune it after the first real report cycle, using the per-key peaks the cycle itself produces: if
that cycle still yields too little data, lower it to 2 or 1; if it floods, raise it.

The hourly peak query over `flows_logs` that produced the aggregates above:

```sql
SELECT run_type, max(calls) AS peak_per_hour, round(avg(calls), 1) AS avg_per_active_hour
FROM (
  SELECT run_type, date_trunc('hour', "createdAt") AS hour, count(*) AS calls
  FROM flows_logs
  WHERE "createdAt" > now() - interval '7 days'
  GROUP BY 1, 2
) t
GROUP BY run_type
ORDER BY peak_per_hour DESC;
```

## No legitimate caller is refused

Every `wouldRefuse:true` from the cycle is classified as **correctly refused** or **refused although
it works**, and the second count must be zero before enforcing. A caller refused in report-only is a
finding to act on, not a test failure. Where the log cannot settle whether a caller was legitimate,
the case is reported as unverifiable rather than counted as correctly refused.

## Verification

The negative control the card requires, run against the real limiter:

1. Exceed the limit on a limited route in `enforce` mode and confirm `429` with `Retry-After`.
2. Confirm the **queue depth and the row count stop growing** on refusal. The row to count differs
   per route: `flow_execution_status` for `/api-v2` (its only writer), `flows_logs` for the rest.
   Bull queue depth applies to `/api-v2`, `/api-v2-webhook` and the email trigger, which enqueue;
   `/batch-process` and `/execute-from-canvas` call `apiV2()` in-request and do not. Measuring the
   response code alone does not demonstrate admission control; that is the whole point of the card.
3. Confirm a caller under the limit still succeeds, and that `report` mode refuses nothing.

Each test is seen failing before it is trusted.

## Why a sequence node cannot trip this limiter

A `sequenceNode` in dev fires 3,000 to 12,000 items. It does not reach this limiter, and the reason
is worth writing down because it is also the reason the limit sits on the route.

**The iteration is intra-run.** The loop lives in the scheduler inside `apiV2()`
(`flux.service.ts:3968-4050`): it reads `processorArray`, slices it between `startingPoint` and
`endingPoint`, and advances the same `markCompleted` / `nextReady` state machine every other node
uses. Twelve thousand items are one HTTP request and therefore **one admission event**. A per-route
limiter at admission never sees the items, whatever their number.

**The ceiling that does govern it already exists, and is not this card.** `maxArrayItems`
(`execution-budget.ts:20`, default **12000**, overridable through `readCeiling`) caps the slice. It
**truncates** rather than refuses — it processes the first N, pushes an `arrayTruncations` entry,
logs `flux.budget.array_capped`, emits `ceiling: 'array_items'` and marks the run
`ARRAY_TRUNCATED_RUN_STATUS`. Truncating is the right verb there: the caller is already entitled to
the run, exactly the D9 contrast this document draws against admission. The observed 3k-12k sits
right at that designed ceiling.

Note for whoever owns the execution budget: the whole mechanism is gated by the `execution_budget`
feature flag, seeded **`false`** (`1788460000000-SeedExecutionBudgetFlag.ts`). Sequence fan-out is
therefore uncapped in production today. That is a finding for that card, not this one.

**And this is the case that would have broken the other placement.** When the looped segment
contains a `flowCallerNode`, that node calls `this.apiV2()` per item (`flux.service.ts:5959`,
invoked from `:4527` and `:4636` inside the loop). A sequence of 12,000 items over a segment
containing a flow-caller therefore produces up to **12,000 internal `apiV2()` calls inside one
already-admitted request**. Had the limiter been placed on the `apiV2()` choke point, one entirely
legitimate run would have been refused twelve thousand times — the largest false refusal available
in this codebase. The route placement is immune to it by construction.

Anyone later tempted to "simplify" this by moving the limit to `apiV2()` should read this section
first.

## Reconciling the master-key limiter

A rate limiter already exists in the product, for master keys only:
`masterApiKeyService.consumeRateLimit()`, called from `apikey.strategy.ts:96` and implemented in
`master-api-key.service.ts:131-141`, `consumeRateLimitAlwaysEnforced()` (it was `:130-147` before this branch). A 60-second sliding window, default 60, env
`MASTER_KEY_RATE_LIMIT_PER_MIN`.

It is absorbed into this module — one mechanism, in Redis, keyed per key rather than globally. Four
consequences of that, none of them blocking, all of them things that change:

1. **The error contract changes, and the audit keeps up.** Today an over-limit master call is
   refused as `UnauthorizedException` (**401**) and writes a `master_key_access_log` row with
   outcome `REJECTED_RATE`. Under this module it becomes **429**. Nothing in the audit schema is
   tied to 401 — `statusCode` is a free `number | null`
   (`master_key_access_log.entity.ts:36`) and `REJECTED_RATE` already exists in the outcome enum —
   so the row is written exactly as before with `statusCode: 429`. The audit records any 4xx; the
   only requirement is that the new limiter writes the row, which it does.
2. **Per-key is looser than today, deliberately.** The current counter is a single array shared by
   *all* master keys, so 60/min is the total across every key. The replacement is **600/min, per
   key** — master keys are internal-use only, so the looser value is a decision, not an accident.
3. **Redis is stricter than today.** The current counter is in-process, so the real limit is
   `60 x replicas`. Moving it to Redis tightens the effective limit — the one direction that can
   refuse traffic that works today, so master-key traffic has to be part of the report-only cycle
   rather than assumed safe.
4. **Ordering matters, and it is the important one — so the limiter has two stages.** The existing
   check runs *inside* the passport strategy, before authentication resolves, so it also throttles
   calls bearing an *invalid* key. A `ThrottlerGuard` running after the auth guard would not: an
   unauthenticated flood would still pay for the key lookup and the rejection log on every request.
   The property is kept by splitting the limiter:

   | Stage | Runs | Keyed by | Purpose |
   |---|---|---|---|
   | 1 | **before** the auth guard | `sha256` of the presented `api-key` header, else `sha256` of the `Authorization: Bearer` token, else `flow:<id>` from the request | Stops a flood of *invalid* keys from paying for a DB lookup and an audit write per request. Its own limit, `RATE_LIMIT_PRE_AUTH_PER_MINUTE` / `_PER_HOUR`, ten times the general window by default (4000/min, 40000/hour); it is a floor, not the product limit. |
   | 2 | after the auth guard | the organisation ladder above | The acceptance criterion's limit: keyed by the paying entity. **Skipped entirely for a master principal** — see "Why the master key skips the organisation stage" above; a master key's only cap is `consumeRateLimitAlwaysEnforced()`'s 600/min per key. |

   Stage 1 never keys by IP: an invalid key still presents *a* key, which is a better identifier
   than an IP for a server-to-server caller, and a public route always carries a flow id.

   Stage 1's limit is deliberately far looser than stage 2's, and is enforced as such at boot
   (`pre-auth >= general`, `assertPreAuthIsNotTighterThanGeneral()`). Equal limits would make the
   unauthenticated floor the binding constraint, contradicting "a floor, not the product limit".
   For the same reason stage 1 hashes a bearer token when one is present: on the JWT route
   (`execute-from-canvas`) there is no `api-key` header, so without it the owner's own requests
   would land in the very `flow:<id>` bucket that anyone knowing the flow id — they travel through
   published interfaces, shared links and the MCP surface — could exhaust, locking the owner out
   once `enforce` is on. The two stages' counters are also namespaced by stage in Redis
   (`rl:<stage>:<window>:<route>:<kind>:<value>`), so a request that resolves to `flow:<id>` at both
   stages does not increment one shared counter against two different limits.

## Dependencies and sequencing

- **Gates `B5`** and gates running a second backend replica (PLAN §5, §6 R16, §4).
- **`S8` sizes the same Redis** these counters write to, and is sequenced alongside this card. The
  throttler's write volume has to be part of that arithmetic.
- **Wave 0 dependency (Parts 1 and 3).** The email-trigger cap here is the "cap them explicitly
  under part 2" that Parts 1 and 3 commit to. Part 3 decides *what* a public email trigger may do
  and authenticates the sender; this card caps its rate. The cap does not need that decision to
  exist, but the entry point is not safe until both land.
- **PLAN D10 is open** — what `public: true` should permit on the webhook route, owned by Part 1.
  The `flow:<id>` limit for public webhook flows may need revisiting once it is settled.

## Env vars

`RATE_LIMIT_MODE`, the general limit for each window, the pre-auth floor, the observation
threshold (`RATE_LIMIT_OBSERVATION_PER_MINUTE`), and the
optional per-route overrides.
`MASTER_KEY_RATE_LIMIT_PER_MIN` is absorbed and its removal is part of the same change.
`env-vars-sync` covers `.env.example`, the env-vars audit README pair and the Mintlify pages when
these land.

## Implementation deviations from this spec

Both of the following were discovered while reading the shipped code, not decided in review. This
document originally described the implementation the two points below contradict; it now records
what actually shipped instead.

1. **`@nest-lab/throttler-storage-redis` is not used, and `@nestjs/throttler` was never added.**
   "Counters live in Redis" above describes an intended `@nestjs/throttler` + Redis-storage design;
   neither package is in `package.json`. The app already provides a configured `ioredis` client
   through the `@Global()` `RedisModule` (`src/infrastructure/redis.module.ts`, exporting
   `REDIS_CLIENT`). The counter store is a small class, `RateLimitStorage`
   (`src/app-api/rate-limit/rate-limit.storage.ts`), built directly over `REDIS_CLIENT` with its own
   `INCR`/`PEXPIRE`/`PTTL` calls and its own per-command timeout. No second Redis connection is
   opened, and no throttler library sits in the dependency tree.
2. **There is no `APP_GUARD` anywhere in this codebase.** The two-stage design ("Reconciling the
   master-key limiter" above) is not implemented by registering a global `NestJS` guard provider.
   Each limited route applies `PreAuthRateLimitGuard` and `OrganisationRateLimitGuard` directly via
   `@UseGuards(...)`, and NestJS runs guards passed to `@UseGuards` in the order listed — that
   declaration order is what implements "stage 1 before auth, stage 2 after auth," not a global
   `APP_GUARD` registration. Nothing is registered globally, so no route that lacks
   `@RateLimitRoute(...)` is affected by either guard: `RateLimitGuardBase.canActivate()` reads the
   route metadata first and returns `true` immediately when it is absent.
