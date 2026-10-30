# S7 — Authenticate and rate-limit the entry points

**Goal:** a run can only be created by someone entitled to create it, and no caller can create an
unlimited number of them.

**Three of the four ways to start a run are effectively unauthenticated** — the webhook route, the
email trigger for public flows, and the email trigger for private flows via a forgeable `From`.
None of the four is rate limited. Every other ceiling in this epic is downstream of admission.

**Depends on:** nothing. **Ship the first half immediately** — it is a live, unauthenticated spend
vector, not a scaling concern. **Severity:** critical (review §9.1, §9.2).

**Cards (PLAN §3.1):** two. Parts 1 and 3 are one card and ship together from Wave 0; part 2 is its
own card in Wave 1 — rate limiting is admission work with its own report-only cycle, and tying it to
the webhook fix would hold the fix hostage.

## Part 1 — the webhook entry point (ship first, on its own)

`POST /flux/api-v2-webhook` is `@Public()` (`flux.controller.ts`), so it opts out of the
global auth guard, and it resolves the flow like this:

```
where: [ { id: query.flowId }, { id: query.flowId, public: true } ]
```

The first branch of the OR has **no `public` condition**, which makes the second dead: any flow
matches, public or private. The rest of the handler contains no secret, no token and no ownership
check — only `if (!flow)`.

**Anyone who knows a flow id can execute that flow and charge its owner.** The only barrier is that
the id is a UUID, and flow ids travel through published interfaces, chatbot routes, shared links
and the MCP surface.

**Scope.** A per-flow webhook secret, verified before anything else runs; the `public` predicate
corrected so the two branches mean different things; and a decision, written down, about what
`public: true` is supposed to permit here. If public flows are meant to be webhook-triggerable by
anyone, say so explicitly and cap them under Part 2 — do not leave it as an artefact of a broken
`where`.

**Migration matters more than the fix.** Existing integrations call this URL today. Ship the secret
as optional with a deprecation window and a metric counting unauthenticated calls per flow, then
enforce. Turning it on cold breaks every customer webhook silently, and the failure looks like
"my automation stopped" rather than "my webhook is unauthenticated".

## Part 2 — rate limiting (all entry points)

There is no `ThrottlerModule`, no `@Throttle` and no `ThrottlerGuard` anywhere in `back/src`. Every
run-creating route accepts unlimited requests: `/flux/api-v2` (API key),
`/flux/api-v2-webhook` (public), `/flux/batch-process`, `/flux/execute-from-canvas`.

The Bull processor's concurrency (`AGENT_CONCURRENCY`, default five per replica) throttles
**execution**, not **admission** — the queue
still grows, and rows, logs and dedup keys are written on the way in.

**Scope.** Limits keyed by the thing that pays: API key, organisation, and flow for the webhook
route. Not by IP, which is meaningless for server-to-server callers.

**Assumption to confirm — reject with `429` and `Retry-After`, rather than queueing.** Admission is
the one place where rejecting is right: queueing an unbounded inbound flood just moves it.
Note the deliberate contrast with `S3`, where excess *tenant* runs are queued — there the caller is
already entitled to the work.

## Part 3 — the email trigger (ship with part 1)

Agents are also started by email. `mail.service.ts` resolves the flow from the **local part of the
recipient address** — the format the service itself advertises is `uuid@upload.fluxprompt.com` — then feeds `From`, `Subject`, the body and any attachments into the flow's
`varInputNode` and enqueues a run.

Its authorisation is the weakest of the four entry points:

- **Public flow → no sender check at all.** Anyone who emails the address runs the flow, charged to
  the owner, **and controls the prompt** — which, in a flow containing a push node or an
  integration, means driving side effects with the owner's credentials.
- **Private flow → the sender's `From` header** is matched against a user and compared to
  `flow.user`. Greps for `dkim`, `spf`, `dmarc` and `authentication-results` in `app-api/mail/`
  return nothing, so nothing verifies the message came from the address it claims. The check is a
  request for the attacker to type the owner's email address — which is not secret.

**Scope.**
- Verify the sender: DKIM/SPF/DMARC at the boundary, **or** move the secret into the address
  (`<flowId>+<token>@…`) so possession of the address is the credential. Either is defensible;
  trusting `From` is not.
- Decide, and write down, what a **public** flow's email trigger is allowed to do. "Public" should
  probably mean readable, not "anyone may spend the owner's tokens and drive their integrations".
  If public email triggers stay, cap them explicitly under part 2 and treat their input as
  untrusted for any node with side effects.
- Keep the existing bounce-back replies — telling a sender "flow not found" or "unauthorized" is
  good behaviour, and it is already there.

**Assumption to confirm — the address-token option is preferred over DKIM.** It is enforceable in
this codebase today, does not depend on the mail provider's headers, and rotates per flow. DKIM
verification is the more standard answer and can be added later without undoing it.

## Verification

- **Negative control (required), Part 3.** Send a message to a private flow's address with the
  owner's email forged in `From`, and confirm the flow runs and is charged. Then confirm it is
  refused. Do the same for a public flow with body content that would drive an integration — that
  demonstration is what settles the "what may a public trigger do" decision.
- **Negative control (required), Part 1.** From an unauthenticated client, trigger a **private**
  flow by id and confirm it runs and charges the owner. That demonstration is the justification for
  the whole task. Then confirm it is refused, and that a correctly-signed call still works.
- **Negative control, Part 2.** Exceed the limit and confirm a `429`; then confirm the queue depth
  and the row count stop growing — the point is admission, so measuring the refusal is not enough.
- **Measure before refusing** (PLAN §3.3.2). Both halves refuse traffic, and this is customer
  traffic. Count real calls per flow and per key over a full cycle, set the limits above the
  observed peak with margin, and run in **report-only** mode before enforcing. Any legitimate
  caller refused is a production incident, not a test failure.
- Confirm the deprecation metric actually names the flows still calling unauthenticated, so someone
  can contact their owners.

## Done when

The webhook route authenticates, the `public` predicate means what it says, every run-creating
route is limited by the paying entity, both ran in report-only mode against real traffic first,
and no legitimate caller is refused.

## Files

`back/src/app-api/flux/flux.controller.ts` (`apiWebhook()`, `api()`, `executeFromCanvas()`, the `/batch-process` handler) ·
`back/src/app-api/mail/mail.service.ts` (the POP3 poll cron, the sender check, `deleteEmailsSequentially`) ·
`back/src/app-auth/guards/` · new throttler configuration · `env-vars-sync`

---

## Part 2, follow-up — the remaining run-creating routes (`868m48692`)

Part 2 named four routes and shipped five (the POP3 email trigger came with it). Tracing where
`run_type` values are produced, to size those limits against production, turned up five more routes
that create runs and carried no admission control at all. They were outside the card's declared
scope, so they land here instead of widening a card whose code review had already finished.

| Route | Auth before this card | Guard stack now |
|---|---|---|
| `POST /flux/beta-v2` | `@Public()` + `JwtAuthGuard` | pre-auth → `JwtAuthGuard` → organisation |
| `POST /flux/execute-single-node` | `JwtAuthGuard` | pre-auth → `JwtAuthGuard` → organisation |
| `POST /flux/chatbot-api-socket` | `@Public()` + `JwtAuthGuard` | pre-auth → `JwtAuthGuard` → organisation |
| `POST /flux/formapi-v1` | `@Public()` + `JwtAuthGuard` | pre-auth → `JwtAuthGuard` → organisation |
| `POST /flux/run-public-flow/:id` | none | pre-auth → organisation |

`run-public-flow` has no authentication stage to sit between the two, so its stack is the same
two-guard shape the webhook route used. Every route carries a `@RateLimitRoute` name, and the names
are in `RATE_LIMITED_ROUTES`, which the decorator's type enforces — dropping one is a compile error,
not a silent gap.

### Decision — a public flow gets its own bucket, not its owner's

Required by the card. At the organisation stage the key resolver derived the company from the flow
whenever a `flowId` was present, with no regard for whether anyone was authenticated. On a
`@Public()` route that means a stranger who knows one public flow id fills the **owner's**
organisation bucket for that route, and every other flow of that organisation is refused with it —
the same shape that had to be fixed on the webhook route, one stage further in.

`resolveOrganisation` now returns `flow:<id>` when there is no authenticated principal and no API
key space. An anonymous caller gets a bucket per flow; the owner's organisation bucket is untouched.
The five routes shipped before this card all authenticate before the organisation stage runs, so
none of them changes behaviour.

The remaining exposure is deliberate and stated: a stranger flooding one public flow can still fill
**that flow's** bucket, refusing other anonymous callers of that same flow. Per-flow is the right
granularity for traffic nobody authenticates; the alternative is refusing nothing.

### Deliberately excluded

- **Cron-triggered runs.** The application dispatches them, not an external caller — the same
  category as the in-process `library-node` / `flow-caller-node` runs left out of sizing. A limit
  here refuses our own scheduler, which is not the threat.
- **MCP.** A separate service with its own deploy and infra. Limiting it means carrying
  `RateLimitModule` and its Redis dependency into `mcp-server/`; that is its own card.

### Sizing, and why nothing is refused on the way in

No per-route override is set: all five fall back to the general window, 400/min · 4000/h per
organisation. Against the seven days of production already measured for part 2 — no limited route
above 23 calls in any single minute, largest hourly peak 273/h — that is an order of magnitude of
headroom. `RATE_LIMIT_MODE` still defaults to `report`, so this deploy decides and logs and refuses
nothing; the numbers above are what the first report-only cycle is meant to replace with per-key
measurements.

### Found on the way

- `rate-limit.wiring.spec.ts` still asserted a guard stack on `apiWebhook`. That route was retired
  to a `410` stub after part 2 merged, so two of its assertions had been failing on `production`
  since then — `back` runs no tests in CI, so nothing reported it. The stub creates no runs; it
  moves to the deliberately-unlimited list.
- `RATE_LIMITED_ROUTES` still carries `api-v2-webhook` and `.env.example` still carries its two
  override vars, both now unreachable. Left in place rather than removed inside this card.
- The `run_type` data-quality caveat from the card is **not** addressed here: `FlowLogRunType` has
  no `CANVAS` value and `flux.service.ts` defaults to `run_type = 'webhook'`, so the observed
  `webhook` figure is a catch-all. It does not block this card — sizing is per rate-limit key, not
  per `run_type` — but per-route run counts cannot be trusted until it is fixed.
- The refusal a caller actually receives said `undefined`. Testing in dev with `enforce` temporarily
  on showed the `429` body reading `ERROR <uuid>: undefined`. The guards threw
  `{ error: 'error', data: { message: ... } }`, but `CustomExceptionFilter` builds its user-facing
  `message` from the response's top-level `message`, which was absent. Fixed at the two throw sites
  — `rate-limit.guard-base.ts` and `apikey.strategy.ts` — so they emit `{ message, error }`, the
  shape the filter reads. The filter itself is deliberately untouched: it is global, and 14 other
  call sites render correctly today through a different path that changing it would break. The
  deeper fix is carried by `868m69vr9`, which measured the blind spot at 29 sites with the broken
  shape but only 6 that actually destroy the reason, all behind `POST /converter/xlsx-to-csv`.

### Cleanup after review

A quality pass over the merged diff (reuse / simplification / efficiency / altitude) found no
efficiency waste — the anonymous branch is a saving, since it skips the `findCompanyOfFlow` lookup —
and confirmed two depth choices as correct: per-handler `@RateLimitRoute` is the established general
mechanism for a selective concern, and fixing the `429` body at the throw sites rather than in the
global filter is the defensible call given the 14 call sites above. Four duplications were removed:

- The `429` body literal was written out in both `rate-limit.guard-base.ts` and
  `apikey.strategy.ts`, two modules this card already had to edit in lockstep. It becomes
  `rateLimitExceededException()` in `rate-limit.exception.ts`, so when `868m69vr9` changes the
  filter's contract there is one place to edit.
- `FakeStorage`, `configFor` and the `ExecutionContext` mock existed in three spec files before this
  card and the two new specs added a fourth and fifth copy. They move to `rate-limit.test-support.ts`,
  kept free of `jest` globals on purpose: `tsconfig.build.json` excludes only `*spec.ts`, so a helper
  referencing `jest.fn()` would fail `nest build`. The three pre-existing specs keep their own copies
  — migrating them is a wider change than this card reviewed.
- `resolveOrganisation` stated its flow-or-unresolved fallback twice. It now guards the
  `findCompanyOfFlow` lookup with `isAnonymous` and states the fallback once.
- A wiring assertion that pre-auth comes first was already implied by the exact guard-stack equality
  in the `it.each` above it, and the refusal-body spec had an unreachable third `canActivate` call.
  Both removed.

Verified with the rate-limit and app-auth suites (122 tests green), a clean
`tsc -p tsconfig.build.json --noEmit`, and a negative control on the refusal-body test: reverting
the factory to the old shape turns it red, restoring it turns it green.

---

## Part 2 — the report cycle and the gate to enforce

The card requires the limiter to run report-only "for a full cycle" against real traffic before
`RATE_LIMIT_MODE=enforce`, without defining the cycle. This section defines it and records how to
read it. Until now the procedure lived only in a ClickUp comment on `868m0vkcj`.

### What a cycle is

**Seven days**, because the traffic is weekly: batch and cron callers behave differently on
weekdays and weekends, and a two- or three-day window can miss the weekly peak.

**The clock starts when the env vars reach the running task, not at merge.** Until
`apply-rate-limit-envs.sh prod --profile=default --apply` had run, prod had no `RATE_LIMIT_*` at all.
Read the start from the first task-definition revision that carries `RATE_LIMIT_MODE`.

**Each set of routes has its own clock.** Since `RATE_LIMIT_MODE` is one global switch, enforce can
only be turned on once the **youngest** set has completed its seven days.

| Routes | Shipped in | First revision in prod | Cycle ends |
|---|---|---|---|
| api-v2, batch-process, execute-from-canvas, email-trigger (+ the retired api-v2-webhook) | `868m0vkcj` (#1957) | `api-task-definition-prod:798`, 2026-09-14 10:04 -03 | 2026-09-21 10:04 -03 |
| beta-v2, execute-single-node, chatbot-api-socket, formapi-v1, run-public-flow | `868m48692` (#1975) | `api-task-definition-prod:804`, 2026-09-21 11:26 -03 | **2026-09-28 11:26 -03** |

### How to read it

```
AWS_PROFILE=<read-only profile> python3 scripts/rate-limit-cycle-report.py <start ISO> [end ISO]
```

Use the script, not a hand-written CloudWatch query. The reason is how the log is written:

- The decision log is `console.log('Rate limit decision', payload)` (`rate-limit.guard-base.ts`,
  `mail.rate-limit.ts`). `util.inspect` prints it over **13 lines**, and the prod `awslogs` driver
  has no `awslogs-multiline-pattern`, so **every line is its own event**. A filter on
  `trigger: 'breach'` returns a line that carries neither the route nor the key.
- All 13 lines share one millisecond timestamp and several decisions land in the same millisecond,
  so Logs Insights interleaves them (a first attempt rebuilt only 1844 of 2262 blocks). The script
  reads each stream with `filter-log-events`, which keeps the ingestion order, and prints
  `headers` against `rebuilt`. If those differ, do not trust the figures below them.
- The field is **`count`**, not `totalHits`. `totalHits` is internal to `rate-limit.storage.ts` and
  is never logged; a query on it returns nothing.
- Only the minute window is logged below the limit (the observation trigger), so hourly load is a
  bracket: the floor sums the logged minutes, the ceiling adds `threshold − 1` for every silent
  minute of that hour.

The script was negative-controlled against the dev log group during the dev tests
(`RATE_LIMIT_LOG_GROUP=/ecs/api-task-definition-dev`, 2026-09-11 19:00Z → 2026-09-12 03:00Z): it
reports 16 breaches, 4 `refused: true` (the enforce test) and the `unresolved` bucket. It can see
what it reports as absent in prod.

### What to read

- **`trigger: 'breach'`** decides. Each one would have been a `429` under enforce, and each must be
  classified as legitimate or abusive. One legitimate caller means: do not enforce. Raise that
  route's override instead and run another cycle.
- **`trigger: 'observation'`**: per-key traffic above `RATE_LIMIT_OBSERVATION_PER_MINUTE`
  (default 5/min). This is the material for per-key sizing.
- **The `keyKind` mix**, especially `user:unresolved` (one shared bucket for every caller whose
  organisation cannot be resolved) and `flow:<id>` (anonymous callers of a public flow).
- **Which limited routes never appear.** Absence means below 5/min per key, not no traffic.
- **`Rate limit check degraded`**: Redis errored or exceeded 250 ms and the request was admitted
  with no limit applied. Under enforce these windows are unprotected.
- Out of this script's reach: master-key refusals, which are always enforced, are recorded as
  `REJECTED_RATE` in `master_key_access_log`, which is a database read.

### Gate to `RATE_LIMIT_MODE=enforce`

All of these, together:

1. The youngest route set has completed seven days.
2. Zero `breach` lines from callers identified as legitimate.
3. The `user:unresolved` share has been reviewed and judged acceptable.
4. The per-route limits have been checked against the measured per-key peaks, minute and hour.

Then `scripts/apply-rate-limit-envs.sh prod --mode=enforce --apply`. If a cycle comes back nearly
empty it has not failed: it shows the limits sit far above real traffic, but it gives no per-key
sizing. The escape hatch is `RATE_LIMIT_OBSERVATION_PER_MINUTE=1` and a second cycle; no deploy
needed.

### First cycle — result (read 2026-09-23)

| | Expected | Measured |
|---|---|---|
| Cycle length | 7 days after the env vars land | Original routes: 7 full days (rev 798 → 2026-09-21). Follow-up routes: 2 of 7 days (rev 804, ends 2026-09-28) |
| Blocks rebuilt | all | 1885 / 1885 (original window) · 276 / 276 (follow-up so far) |
| `breach` | none, since the limits were sized far above the observed peak | **0**, both windows |
| `refused: true` | none in report mode | **0** |
| `user:unresolved` | unknown; flagged as the main risk before enforcing | **0** |
| Per-key minute peak | a few keys above 5/min; aggregate peak was 23/min across all tenants | **61/min** from one organisation (`18210670-…`, api-v2, 2026-09-16 13:00Z), which is **15 % of 400/min**. Next peaks: 35, 28, 17, 16 |
| Per-key hour peak | not measured before | floor 231 · ceiling 447 per hour, **≤ 11 % of 4000/h** |
| Routes seen | the first data ever for batch-process, execute-from-canvas, email-trigger | Only **api-v2** and **beta-v2** crossed 5/min. The other seven never did |
| Redis degraded | none expected | **3** in the original window (2026-09-18), **6** on 2026-09-22, and 14 overall from 2026-09-14 to 2026-09-23 |

**What it proves.** In seven days, no organisation or key used more than 16 % of any limit, and nothing
would have been refused. The limits are adequate for api-v2 and beta-v2 by a factor of six or more.

**What it corrects.** The sizing premise "at most 23 calls/minute, aggregated across all tenants"
understated per-key load: a single organisation reached 61/min on its own. The limits hold anyway,
but aggregate data (`etc/data.hourly.csv`) is not a sizing source: only per-key decision logs are.

**What it does not prove.**

- The sizing of the seven routes that never crossed 5/min. Their limits are untested upper bounds.
- The follow-up routes, which have not completed their own cycle.
- Master-key refusals, which need a database read.
- Whether the 14 degraded events cluster in a way that matters under enforce.

**Decision (as written on 2026-09-23).** Do not flip before 2026-09-28 11:26 -03. Then re-run the
script from `2026-09-21T11:26:00-03:00`, and enforce if the gate still holds. Enforce was in fact
turned on the same day; see below.

### Enforce — second read (2026-09-28)

**Enforce went live on 2026-09-23 10:16 -03**, with `api-task-definition-prod:807`, five days before
the gate above. That revision was registered by the account's `root` identity, not the pipeline, and
it changes exactly one key: `RATE_LIMIT_MODE` `report` → `enforce`. That was checked field by field
against 806. The later pipeline revisions, 808 to 810, change only the image and keep `enforce`.

The follow-up routes' window, 2026-09-21 11:26 → 2026-09-28, is therefore two days of report
followed by five of enforce. It was read twice: from the cycle start, and from the moment enforce
went live.

| | Expected | Measured |
|---|---|---|
| Real refusals (`refused: true`) under enforce | none | **0** in five days (2026-09-23 10:16 → 2026-09-28 14:00Z) |
| `breach` | none | **0**, both windows |
| Blocks rebuilt | all | 2103 / 2103 (from the cycle start) · 1827 / 1827 (from enforce) |
| `user:unresolved` | 0 | **0** |
| Per-key minute peak | well under 400/min | **52/min** (`beab4496-…`, api-v2), which is **13 %**, below the first cycle's 61/min |
| Per-key hour peak | well under 4000/h | floor 152/h, under 4 % |
| Follow-up routes seen | first data ever | **beta-v2** (9/min) and **execute-single-node** (5/min). chatbot-api-socket, formapi-v1 and run-public-flow never crossed 5/min |
| Redis degraded (no limit applied) | none | **10** under enforce (2 on 2026-09-25, 8 on 2026-09-26), against 14 in the nine days before. The rate went up |

**What it proves.** Enforce is live, nothing has been refused in five days, and every limit sits more
than seven times above the busiest key. Gate conditions 2 to 4 hold on the full window. Condition 1
was skipped by five days, but the result shows no harm from that.

**What it does not prove.**

- The limits for batch-process, execute-from-canvas, email-trigger, chatbot-api-socket, formapi-v1
  and run-public-flow. None of them has crossed 5/min, so their limits are still untested upper bounds.
- Master-key refusals, which live in `master_key_access_log` and need a database read.
- Why degraded events rose. Under enforce, each one is a window with no admission control. Look at
  Redis latency on 2026-09-26.

**Found on the way — `diff` is not installed on the operator machine.**
`apply-rate-limit-envs.sh` proves that "nothing but the rate-limit variables moved" with `diff`, and
on a machine without it that check passes without comparing anything. The ClickUp procedure warned
about this, and the machine used for this read has no `diff`. Revision 807 turned out clean, but that
was not guaranteed. A second hole sat in the same check: both sides came from process substitution,
so a failed `jq` compared two empty streams and also passed.

Fixed in the script. It now compares with `git diff --no-index` (git is on every machine that has
this repo, and the script refuses to start without it), writes both sides to files so a `jq` failure
stops it, and reads the exit code explicitly: 0 is identical, 1 aborts, anything else aborts as
"could not compare". Negative control, on the machine without `diff`: the old code let two
different files through, and the new code aborts on different files, on a missing file and on a
`jq` failure.
