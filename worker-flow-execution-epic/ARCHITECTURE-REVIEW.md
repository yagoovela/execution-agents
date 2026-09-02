# Architecture review — is this design safe to scale?

**Posture:** adversarial, including toward our own prior conclusions. The question is not "does the
plan make sense" but "what breaks, what costs money, and what can be abused when this runs with
many agents, many workers, and real parallelism".

**Scope note from the requester:** Temporal's own database is out of scope. The database that
matters here is the **application Postgres** — the one holding flows, nodes, executions and logs —
because that is the shared resource every worker replica will contend for.

**Method:** every finding below was read out of the code. Where a claim is inference rather than
observation, it says so. Read against `back@origin/production` (`7d523b29`),
`worker@origin/main` (`fe0db9f`).

**Verdict up front:** the *persistence* design is sound and scales — that was the right call and
it holds up (§6). The *control* design is not ready: there are three uncapped runaway paths, and
the plan as written would make two of them worse rather than better (§1). The database will hit a
connection ceiling before it hits a throughput ceiling (§2). Two security gaps get *more*
dangerous after migration, not less (§3).

---

## 1. Runaway, abuse, and unbounded cost — the critical group

### 1.1 Sub-flow recursion is unbounded — CRITICAL

`flowCallerNode` calls **`this.apiV2()`** — the whole orchestrator — for the selected flow
(`flux.service.ts:5611–5622`). `libraryNode` does the same.

There is **no depth limit and no cycle detection**. Greps for `visited`, `cycle`, `depth`,
`MAX_DEPTH` across the flux service return nothing; `parentFlowId` is threaded for billing
attribution only (`:5732, 5815`).

So flow A containing a Flow Caller pointing at flow B, and B pointing back at A, recurses until
the process dies. Each level is a **complete run**: its own scheduler state, its own
`node_executions` rows, its own run-log tree, its own token spend. No malice required — two people
composing reusable flows produce this by accident.

**The plan makes this worse.** Task B6 turns these into Temporal **child workflows**. Today the
recursion is bounded, crudely, by one Node process's stack and memory. As child workflows, it
becomes a fork bomb that the platform will faithfully sustain across the whole worker fleet, with
each level durably retried.

**Required before B6, and arguably before anything:** a depth counter in the run context with a
hard ceiling, plus a visited-flow set to reject cycles outright. Cheap, and it is the difference
between a bad flow failing fast and a bad flow taking the fleet down.

### 1.2 The loop limit can be switched off from the node's own data — HIGH

`evaluateLoopCondition` (`folw/helpers/helpers.ts:2075–2110`):

```
if (loopBehavior === 'continue') {
  finalResult = userConditionResult && loopLimitCheck;   // capped
} else {
  finalResult = userConditionResult;                     // NOT capped
}
```

With `loopBehavior !== 'continue'`, `loopLimitCheck` is computed, reported to the UI, and then
**not applied**. And even on the capped branch, `loopCount` is `node.data.loopCount` — user data.

So a condition that is always true, on a node whose behaviour is not `'continue'`, loops with no
ceiling. Combined with §1.3, that is unbounded spend.

Whether this is deliberate — "stop" may be intended to mean "do not use the counter" — the
observable effect is a user-controlled loop with no system-level maximum. A system-level ceiling
should exist regardless of node configuration.

### 1.3 There is no budget ceiling for a run — HIGH

`assertCompletionCredits` (`product.service.ts:265–284`) is a **boolean gate**: for `INTRO`
products it checks `trialTokens > 0`; otherwise, having a subscription is enough. Per-node,
`getUserProductFromFlow` checks *entitlement* to a model — not remaining budget.

Charges are recorded after the fact (`token_transactions`, aggregated by
`sumChargesByExecution`). Nothing decrements a per-run allowance, and nothing aborts a run that
has already spent more than it should.

For a paid account, §1.1 or §1.2 therefore converts directly into unbounded provider spend, and
the first signal is the invoice.

**Recommendation:** a per-run token/cost ceiling enforced *at charge time*, in the same call that
already records the spend — the cheapest place to put it, and the only one that works when the
worker owns the loop. A per-org concurrent-run limit alongside it.

### 1.4 Nothing limits concurrent runs per user or per org — MEDIUM, becomes HIGH after B5

No throttle, no per-tenant concurrency cap anywhere in the flux or job paths. Today this is
partly masked: the Bull processor declares `@Process(...)` with no concurrency option
(`jobs/apiV2Job/apiV2Job.processor.ts:33`), so each backend replica runs **one queued run at a
time**. That accidental serialisation is doing real protective work.

**Corrected 2026-09-02.** The `@Process` claim above was already false when this review was
re-validated on 2026-08-24: PR #1902 landed
`@Process({ concurrency: parseConcurrency(process.env.AGENT_CONCURRENCY) })`, default 5, on
2026-08-21, and the re-validation did not re-read the processor. The finding stands and is slightly
worse — the throttle is explicit, five times looser, and still not per tenant. `TASK-S3` carries
the corrected premise.

Task B5 removes it deliberately. Fan-out without a per-tenant cap means one org's wide graph can
occupy the whole worker fleet and starve every other tenant. Our B5 spec says "pick a cap and
state the reasoning" — that is too weak. The cap must be **per tenant**, not only global,
otherwise it is a fairness bug rather than a capacity bug.

---

## 2. The application database is the first thing that breaks

### 2.1 The worker's connection pool is unbounded by configuration — CRITICAL for multi-worker

`worker/src/modules/database/database.service.ts:13` constructs `new Pool({host, port, user,
password, database})` — **no `max`**. node-postgres defaults to 10 connections per pool, per
process.

The worker runs `maxConcurrentActivityTaskExecutions: 10`
(`worker/src/modules/temporal/worker.service.ts:22`). So each replica can hold ten busy
connections. Connections then scale **linearly with worker replicas**, and Postgres
`max_connections` is a hard wall — the failure mode is not slowness, it is
`too many clients already` for the API as well, because they share the database.

No connection proxy (PgBouncer or equivalent) appears anywhere in the compose files or infra.

**This is the single biggest obstacle to "múltiplos workers", and it is one line of config plus a
capacity decision.** It must be settled before B5, and honestly before scaling the worker at all.

### 2.2 Write amplification per node, multiplied by fan-out

One successful node writes, at minimum:

| Write | Where |
|---|---|
| `node_executions.outputData` | `persist-node-success.ts:7–9` |
| `flows_nodes.data` JSONB merge | `persist-node-success.ts:59–63` |
| `node_executions` row insert (input) | `node-execution-store.ts:26–39` |
| `token_transactions` insert | `/worker/charge-tokens` |
| `execution_logs` | `generateExecutionLogsActivity` |
| `space_run_logs` upsert | debounced collector flush |

That is five to six writes per node, before Redis and before S3. Parallel dispatch multiplies it
by the width of the ready set, and loops multiply it again — with B1 adding a row per iteration
rather than reusing one.

None of this is wrong. It is simply the number that has to be sized deliberately rather than
discovered, and our epic never states it.

### 2.3 `flows_nodes.data` is a hot, fat, contended column

It is merged on every node completion, and it is what the builder UI reads. It carries
`previewResponses`, `contentData` and `text` — the known front-end performance offender.

Two aggravations found:
- The `previewResponses` trim uses `responses.length === 10` at six sites. Any array that gets
  past ten by another path never trims again. Already logged as `TASK-C3`.
- Under loops, the same node's row is merged once per iteration — serialised by row lock. Parallel
  siblings on *different* nodes are fine; the same node is not.

### 2.4 The claim check routes large payloads **through the API** — an anti-goal

Payloads over 256 KB are offloaded via `POST /worker/store-payload` and fetched back via
`/worker/get-payload` (`persist-node-success.ts:32–57`, `resolve-claim-ref.ts:38–51`) — because
the worker has no S3 client.

So the design's escape valve for large data is a **synchronous hop into the very service the
migration is trying to take out of the path**. Under fan-out, every wide node's payload becomes an
API request. Giving the worker its own S3 credentials removes an entire class of coupling; the
counter-argument (credential surface) is real but weaker than it looks, since the worker already
holds the database password and the integrations encryption key.

### 2.5 Genuinely good: retention already exists

`purgeNodeExecutions` runs daily at 03:00 and does three things — slims by company/PHI override,
slims by age, deletes past `NODE_EXEC_DELETE_AFTER_DAYS` (default 30) and past `MAX_PER_NODE`
rows per node. Someone thought about growth before it hurt. **Revisit the thresholds when B1
starts writing a row per loop iteration**, because the per-node cap becomes load-bearing then.

---

## 3. Security

### 3.1 `/worker/get-payload` has no ownership check — HIGH

```
if (typeof body.key !== 'string' || !body.key.startsWith('node-exec/')) throw ...
const stream = await this.awsService.getFile(body.key);
```
(`worker.controller.ts:87–95`)

The only validation is a **prefix**. There is no check that the key belongs to the caller's run,
tenant, or anything else. Any holder of the internal API key can read **any** node output of
**any** customer, by key.

The controller is behind `InternalApiGuard` (`worker.controller.ts:45`), which is the right
boundary — but it is a single shared secret, and after this epic that secret sits on **every
worker replica**. Blast radius grows with the fleet. Bind the key to its `execId`/`nodeId` and
verify the caller's claim; the key already encodes them.

### 3.2 No SSRF protection on user-controlled URLs — HIGH, and migration changes the risk

`/downloader?url=` takes a user URL (`downloader.controller.ts:34`), and the scraper, api-caller
and crawling paths take user URLs too. Searching those modules for private-range or metadata-IP
blocking (`127.0.0.1`, `169.254`, `localhost`, `isPrivate`) returns **nothing**.

A node pointing at `169.254.169.254` or an internal hostname is the textbook case. This is a
pre-existing gap, not one the epic creates — **but the epic moves these callers into the worker,
which sits in a different network position**. Whether that is better or worse depends on the
worker's subnet and its instance role. Migrating an unvalidated URL fetcher into a host that holds
the database password and the integrations key is a decision that deserves a sentence in the
task, and currently gets none.

### 3.3 Genuinely good: scripting is out of process

The scripting node dispatches to AWS Lambda (`code-executor-js`, `code-executor-python` —
`scripting.service.ts:23–24, 213`) rather than evaluating in the worker. The largest arbitrary-code
surface in the product is already isolated at the strongest available boundary. Do not let a future
"optimisation" pull it back in-process to save a Lambda invocation.

### 3.4 Secret redaction has exactly one chokepoint

`redactSecrets` in the run-log collector is the only place credentials are scrubbed before
reaching `space_run_logs`. `TASK-E1` moves that collector. A refactor that drops the hook turns a
logging change into a credential disclosure. E1 already requires a test for it; that requirement
should be treated as non-negotiable rather than as one bullet among several.

---

## 4. Where our own prior conclusions do not hold up

This section exists because the requester asked for scepticism about the analysis itself.

### 4.1 We never mentioned Temporal workflow history limits — a real gap in B4

A Temporal workflow accumulates history events, and both event count and history size are bounded.
The worker uses **no `continueAsNew`** anywhere (grep returns nothing).

Task B4 proposes one workflow owning an entire flow run. For a large graph, a long loop, or an
`arrayNode` iterating a big list, the history grows with every activity scheduled and completed,
and every large input passed. That workflow will eventually be terminated by the platform, and it
will happen to the biggest, most valuable customer runs first.

**B4 must specify `continueAsNew` at an iteration or node-count boundary, and must pass state by
reference rather than by value** — which the id-based transport of §8 already makes possible. This
was missed because our analysis reasoned about Postgres and never about workflow history as a
storage medium.

### 4.2 Our B5 gate is necessary but not sufficient

B5 gates parallelism on "every executable node in the flow is migrated", which correctly prevents
the mixed-mode lost update. It says nothing about **provider** concurrency. Fan-out will produce
bursts against OpenAI, Anthropic, Replicate and the integration APIs, and the first symptom is 429s
attributed to the customer as node failures.

B5 needs a per-provider, per-tenant concurrency budget — not just "pick a cap".

### 4.3 A single run-log tree is a sequential idea

`RunLogCollector` maintains one hierarchical tree in memory. Under parallel siblings, branches are
written concurrently. Our E1 offers two options — worker keeps the tree, or backend rebuilds from
events — as if they were equivalent. They are not: **keeping the tree in the workflow makes
workflow state grow with the run**, which collides directly with §4.1. Event-sourced reconstruction
is the only option compatible with both parallelism and history limits. E1 should say so instead
of leaving it open.

### 4.4 We treated "own-row writes" as sufficient proof of parallel safety

It is sufficient for *lost updates*, and that conclusion stands. It is not sufficient for
**ordering**. Two siblings writing their own rows cannot clobber each other, but a downstream node
reading both has no guarantee about which is visible when, and `nodesBox` has real ordering
requirements. A7 addresses that for one node; nothing addresses it as a general property. The
scheduler's dependency edges are the answer — but that is an argument, and our documents asserted
the conclusion without making it.

### 4.5 The blocking wait is partly load-bearing

We treated `await handle.result()` as pure waste. It also provides back-pressure: while the
backend blocks, it is not starting more work. Removing it without §1.4's per-tenant cap and §2.1's
connection ceiling replaces a slow system with an unstable one. The removal is still right; the
ordering is not optional.

---

## 5. Usability consequences nobody has specified

- **Concurrent RUNNING states.** The builder shows per-node status. With fan-out, several nodes
  are running at once — the UI must express that, and "which node is the run on" stops having a
  single answer, including in the cancel footprint the product shows today.
- **Cancellation becomes partial.** Cancelling a parallel run leaves some siblings completed, some
  aborted, some never started. The user-facing meaning of a cancelled run needs a decision.
- **Non-deterministic ordering of side effects.** Two independent push nodes today fire in graph
  order; in parallel they do not. Any customer who relied on the incidental ordering will
  experience it as a regression.
- **Error attribution.** Fail-fast today stops at the first error. With a batch in flight, several
  nodes can fail simultaneously — which one names the run?

None of these are blockers. All of them are decisions, and shipping B5 without making them means
making them by accident.

---

## 6. What is solid — and should not be redesigned

Being sceptical cuts both ways. These are good and the plan should protect them:

1. **Own-row writes.** `persistNodeSuccess` only ever merges into rows the activity owns. This is
   the property that makes parallelism possible at all, and it was already true before anyone
   planned for parallelism.
2. **One `node_executions` row per execution.** Run isolation by construction.
3. **The claim check.** Correct pattern, wrong transport (§2.4) — keep the pattern.
4. **Lambda-isolated scripting** (§3.3).
5. **`InternalApiGuard` on every `/worker/*` route.** The boundary exists; it needs
   authorisation inside it (§3.1), not replacement.
6. **The typed `NodeError` taxonomy.** Retry semantics derived from error type is exactly right,
   and it is what keeps a user's typo from retrying for thirty minutes.
7. **The advisory-lock precedent** in `oauth-token.repo.ts` — a working pattern for the ordering
   problem in A7, already in the codebase.
8. **The prefetch executor.** Reference-based input resolution, shipped, behind a flag.
9. **Retention with slimming** (§2.5).
10. **The pure scheduler.** Portable, testable, single source of ordering truth.

---

## 7. What this changes in the epic

| # | Action | Where |
|---|---|---|
| 1 | Depth ceiling + cycle detection for sub-flows, **before** B6 turns them into child workflows | new task, blocks B6 |
| 2 | System-level loop ceiling independent of `loopBehavior` and of node data | new task |
| 3 | Per-run cost ceiling enforced at charge time; per-tenant concurrent-run cap | new task, blocks B5 |
| 4 | Set the worker pool `max`; size connections against `max_connections`; decide on a connection proxy | blocks B5, and blocks scaling the worker today |
| 5 | Bind claim-check keys to their run; authorise inside `InternalApiGuard` | security, standalone |
| 6 | SSRF allow/deny policy for user-controlled URLs, decided **as part of** moving those callers | A6, A8 |
| 7 | `continueAsNew` and by-reference workflow state | B4 |
| 8 | Per-provider, per-tenant concurrency budget | B5 |
| 9 | E1 commits to event-sourced run logs rather than leaving the choice open | E1 |
| 10 | Specify the parallel-execution UX: concurrent status, partial cancel, error attribution | B5 |

## 8. The one-line summary

The data model was designed by someone thinking about concurrency, and it holds. The control
plane was designed by someone thinking about a single sequential process, and every uncapped
path in it — recursion, loops, spend, tenancy, connections — becomes a fleet-wide problem the
moment the loop is parallel. **Fix the ceilings before removing the throttle.**

---

## 9. Entry points, schedulers and Redis — added after review

**This section exists because the first review missed it.** It covered Redis only as the
notification transport and crons only as the retention job, and it never looked at how a run is
*admitted*. Asked directly about crons, Redis, webhooks and API calls, the honest answer was
"partially" — and the gap contained the most severe finding in this document.

### 9.1 The webhook entry point is unauthenticated and runs any flow — CRITICAL

`POST /flux/api-v2-webhook` is decorated `@Public()` (`flux.controller.ts:340–341`), so it opts out
of the global auth guard. It resolves the flow from a query parameter:

```
const flow = await Flow.findOne({ where: [ { id: query.flowId },
                                           { id: query.flowId, public: true } ] });
```
(`flux.controller.ts:352–362`)

The `where` is an **OR array whose first branch has no `public` condition**, so the second branch is
dead: **any** flow matches, public or private. Scanning the rest of the handler for a secret, a
token, an ownership check or any other throw finds only `if (!flow)`.

So: **anyone who knows a flow id can execute that flow and charge its owner.** The only barrier is
that the id is a UUID — security by obscurity, and flow ids travel through published interfaces,
chatbot routes, shared links and the MCP surface.

Now combine it with the rest of this review: no rate limiting (§9.2), no per-run cost ceiling
(§1.3), no per-tenant concurrency cap (§1.4), and unbounded sub-flow recursion (§1.1). A single
leaked flow id is an unbounded, unauthenticated spend and load vector against one customer.

**This outranks everything else in this document.** It is not a scaling concern — it is live.

### 9.2 There is no rate limiting anywhere — HIGH

No `ThrottlerModule`, no `@Throttle`, no `ThrottlerGuard` anywhere in `back/src`. Every run-creating
entry point — `/flux/api-v2` (API key), `/flux/api-v2-webhook` (public), `/flux/batch-process`,
`/flux/execute-from-canvas` — accepts unlimited requests, and each request creates a run.

The Bull processor's accidental serialisation (§1.4) throttles *execution*, not *admission*. The
queue still grows without bound, and the rows, logs and dedup keys are written on the way in.

### 9.3 Thirteen crons, no leader election — HIGH

`@Cron` is registered thirteen times across `back/src` (a fourteenth site is commented out in
`updateTechnologiesFromSheets.service.ts`; corrected 2026-09-02 — the first draft counted it), and greps for `leader`, `isLeader`,
`CRON_ENABLED` or an advisory-lock guard return nothing. **With more than one backend replica,
every cron fires on every replica.**

Some of that is merely wasteful: five separate purges all scheduled at `EVERY_DAY_AT_3AM`, each
running once per replica, all hitting the same tables at the same minute. Some is not:
`mail.service.ts` polls POP3 `EVERY_10_SECONDS`, per replica, and
`markStuckSpaceRunLogs` runs every ten minutes, per replica.

This is not caused by the worker migration. It is caused by horizontal scaling, which the
migration exists to enable — so it becomes this epic's problem the moment a second replica exists.

### 9.4 User-scheduled flows fire once per replica — HIGH

Scheduled runs do **not** go through a durable scheduler. `schedule.controller.ts` registers them
with NestJS's in-process registry — `this.schedulerRegistry.addCronJob(...)` at `:179` on creation
and at `:332` in a bulk re-registration path — so each backend replica holds its own copy of every
active schedule and fires it independently. **N replicas means N runs of the same scheduled flow,
each charged.**

Two aggravations found in the same code:

- The re-registration lives in `getAllSchedules()`, a **plain method with no route decorator**
  (`:242`), which walks every active schedule and registers a cron as a side effect. A function
  named "get" that mutates scheduler state will be called by someone who does not expect that.
- The cron callback does `await this.scheduleQueue.add('schedule-job', { … job: await
  this.fluxService.apiV2({ … }) })` (`:157–159`, and again at `:309–311`). The **run is awaited as
  an argument to the enqueue call** — so the flow has already executed synchronously inside the cron
  callback, and what reaches the queue is its result. The queue is not doing the work it appears to
  be doing.

The self-healing zombie-cron check at `:283–297` — stop, delete and soft-delete the schedule when
its flow is gone — is a genuinely good touch in code that otherwise has this problem.

### 9.5 Redis carries three unrelated responsibilities — MEDIUM, verify

Redis backs the Bull queues, the worker→backend pub/sub, and the delivery dedup keys. The dedup
itself is a correct pattern — `SET key '1' EX 86400 NX` with a run-scoped key
(`flux.service.ts:5030–5044`), plus a shorter content-hash key — and it is what stops a retried run
from emailing a customer twice.

Two things to verify, because neither can be read from this repository:

- **Eviction policy.** If the instance runs `allkeys-lru` or `allkeys-random`, the dedup keys are
  evictable under memory pressure, and the failure mode is duplicate emails and duplicate outbound
  webhooks. Dedup keys are correctness state, not cache, and must not share an eviction policy with
  cache.
- **Availability.** With the queue, the notification bus and the dedup all on one instance, losing
  Redis loses run admission, run visibility and duplicate suppression together. Parallel dispatch
  increases the pub/sub rate substantially, so the sizing that holds today is not evidence for
  after B5.

### 9.6 What this adds to the plan

| # | Action | Task | Blocks |
|---|---|---|---|
| 11 | Authenticate the webhook entry point and fix the `public` predicate | `S7` | nothing — ship immediately |
| 12 | Rate limiting on every run-creating entry point | `S7` | B5 |
| 13 | Leader election or an advisory-lock guard for the thirteen crons | `S8` | running more than one backend replica |
| 14 | Move user schedules to a durable scheduler, one fire per schedule | `S8` | running more than one backend replica |
| 15 | Confirm the Redis eviction policy protects dedup keys; size the bus for post-B5 traffic | `S8` | B5 |

---

## 10. Email as a trigger — the fourth entry point

Added after §9, when the requester pointed out that agents are also triggered by email. §9 treated
the POP3 poll as a wasteful cron; it is also a **run-creating entry point**, and it has the weakest
authentication of the four.

### 10.1 How it works

`mail.service.ts` polls POP3 every ten seconds (`:132`), parses each message, and resolves the flow
from the **local part of the recipient address** — the format the service itself tells users about
is `uuid@upload.fluxprompt.com` (`:434`). It then loads the flow, feeds
`From: … / Subject: … / Message: …` plus any uploaded attachments into the flow's `varInputNode`,
and enqueues an `apiV2` job with `runType: 'email'` (`:503–556`).

The authorisation model is two-branched (`:453–487`):

- **`flow.public === true` → no sender check at all.** Anyone who emails the address runs the flow,
  charged to the owner.
- **Otherwise** → the sender's address must match a user, and that user must be `flow.user`.

### 10.2 The ownership check rests on a forgeable header — CRITICAL

For private flows, the entire check is
`userService.findOne({ email: parsedEmail.from.value[0].address })` compared against the flow
owner. That is the **`From` header**, which any sender can set to any value.

Searching `app-api/mail/` for `dkim`, `spf`, `dmarc` or `authentication-results` returns
**nothing**. There is no verification that the message actually came from the address it claims.

So the private-flow branch is not an authorisation check — it is a request for the attacker to type
the owner's email address. And the address is not secret: it is the flow owner's login email.

This is the same class as §9.1 and arguably worse, because §9.1 at least required a UUID. Here the
attacker needs the flow id **and** an email address that is, by design, easy to find.

### 10.3 Public flows are an open prompt-injection surface — HIGH

For a public flow there is no sender check, and the email's `From`, `Subject` and body are injected
directly into the flow's input. Whoever sends the email therefore **controls the prompt**.

If that flow contains a push node, a third-party integration or a Flow Caller, the sender is
driving side effects with the owner's credentials — sending Slack messages, writing to Notion,
charging through Stripe — with an unauthenticated email as the only input. This is not a
hypothetical chain: the integration nodes are exactly the ones this epic is migrating.

### 10.4 The poll runs on every replica, with nothing deduplicating messages — HIGH

The POP3 cron is one of the thirteen with no leader election (§9.3), so it fires every ten seconds
**per backend replica**. There is no message-id dedup and no lock anywhere in the service — greps
for `messageId`, `dedup`, `lock` or `NX` return nothing. Messages are fetched, processed, and only
then deleted (`deleteEmailsSequentially`, `:314`), so the window between fetch and delete spans the
whole batch, including enqueueing the runs.

**Being fair about the current risk:** POP3 requires the server to lock the maildrop exclusively
during a session, so a well-behaved provider will refuse the second replica's session and duplicates
may not occur today. That is the honest read — but it means **correctness depends on a lock the code
does not take and cannot see**. If the provider allows concurrent sessions, or the mailbox moves to
IMAP or an API, the failure mode is duplicate runs and duplicate charges with nothing to catch them.
Meanwhile, every replica beyond the first is failing to acquire that lock every ten seconds.

### 10.5 What this adds to the plan

| # | Action | Task | Blocks |
|---|---|---|---|
| 16 | Verify the sender before trusting `From` — DKIM/SPF/DMARC, or a per-flow secret in the address | `S7` part 3 | nothing — ship with part 1 |
| 17 | Decide what a public flow's email trigger may do, and cap it | `S7` part 3 | nothing |
| 18 | Message-id dedup that does not rely on the POP3 maildrop lock | `S8` part 4 | running >1 backend replica |

### 10.6 The pattern across all four entry points

Worth stating plainly, because it is the same mistake four times:

| Entry point | Authentication | Rate limit |
|---|---|---|
| `/flux/api-v2` | API key | none |
| `/flux/api-v2-webhook` | **none** — and the `public` predicate is dead | none |
| Email | **a forgeable header**, or nothing for public flows | none |
| Scheduled | owner, at creation time | n/a — but fires once per replica |

**Three of the four ways to start a run are effectively unauthenticated, and none of the four is
rate limited.** Every ceiling this review proposes — cost, tenancy, recursion, loops — is downstream
of admission. Fixing admission last would mean building all of them and still leaving the front door
open.

---

## 11. What else belongs in the worker

Asked directly whether anything else in the front or the back should move. Four things in the
back, and — usefully — **nothing left in the front**.

### 11.1 Outbound delivery: emails and HTTP callbacks — should be activities

The ~300-line block at the end of every run (`flux.service.ts:4907–5200`) sends emails through
three different paths (`mailService.sendMail`, `sendGmailEmail`,
`microsoftMailService.sendMail`) and fires HTTP callbacks with `axios.post`, each wrapped in a
`catch` — **fire and forget, with no retry**.

This is the textbook activity. It is pure external I/O, it is the part of a run most likely to fail
for reasons that resolve themselves, and **its idempotency is already solved**: the Redis dedup keys
(`SET … EX 86400 NX`, run-scoped, plus a content hash) exist precisely so a repeated attempt does
not double-send. Retry with backoff is the one thing missing, and it is what Temporal gives for
free.

Today, a customer's webhook endpoint being down for thirty seconds means the notification is simply
lost, with a log line. New task: `TASK-A9-OUTBOUND-DELIVERY.md`.

### 11.2 Batch processing is detached background work in the API process — should be a workflow

`/flux/batch-process` calls `this.processBatch(...).catch(...)` (`flux.controller.ts:560`) —
**fire-and-forget, unawaited**, so the HTTP request returns immediately and the work continues
detached inside the backend process.

`processBatch` (`:574–706`) is a sequential `for` loop over CSV rows. Each iteration re-reads the
batch row, re-reads the row record, runs a **complete flow** with `await this.fluxService.apiV2(…)`,
writes the output, re-reads the batch and saves the pointer — four to five database round trips per
row on bookkeeping alone, before the run itself.

Three consequences:

- **No durability.** A deploy, a restart or a scale-down mid-batch kills the loop silently. The
  batch stalls at `lastProcessedLine` with a non-terminal status and nothing resumes it.
- **No parallelism, and no way to add it safely** while it is a loop in a request handler.
- **It is the largest amplifier of every missing ceiling.** A thousand-row CSV is a thousand full
  runs, admitted through one API-key call, against no rate limit (§9.2), no per-run cost ceiling
  (§1.3) and no per-tenant cap (§1.4).

A batch is a durable workflow with a child per row and a concurrency cap — which is what this epic
is building anyway. New task: `TASK-B7-BATCH-WORKFLOW.md`.

### 11.3 User schedules should use Temporal Schedules, not an advisory lock

`S8` part 2 proposed fixing the per-replica schedule duplication with the same advisory lock used
for the crons. That works, but it is the second-best answer, and this review should say so.

Greps for `ScheduleClient`, `scheduleClient` and `createSchedule` across the worker and
`back/src/temporal` return **nothing** — Temporal's native scheduling is not used at all. It gives,
by construction, exactly what `S8` part 2 is trying to build by hand: one fire per schedule
regardless of replica count, durability across restarts and deploys, plus pause, backfill and
last-run visibility that the in-process registry cannot offer.

The advisory lock stays the right answer for the **thirteen framework crons**, which are internal
maintenance and have no reason to become workflows. **S8 is amended**: locks for the crons,
Temporal Schedules for user-facing schedules.

### 11.4 Google token refresh, once its consumers have moved

The engine refreshes the Google access token centrally at run start, but only when the flow
contains `pullData`/`pushData` with `provider = google` (`flux.service.ts:2621–2641`). The worker
already has `TokenProviderService` and the Google service clients.

While the token's consumers were in the back, central refresh was the efficient choice — one refresh
per run rather than one per node. Once they are all in the worker, the refresh is a round trip in
the wrong direction, and `fileSave` (task `A6`) needs the token worker-side regardless. Fold it into
`A6` rather than making it a task: it is a few lines, and it only makes sense at the moment
`fileSave` lands.

### 11.5 Dead code found while looking

`back/src/app-api/flux/api-caller-polling.ts` has **no importers** — greps across `back` and
`worker` find only the file itself. The polling it implements already lives in the worker as
`execute-polling`, consumed by `api-caller.service.ts:17, 407`. Confirm across all repos and
`origin/production` before deleting, then add it to `TASK-C3`.

### 11.6 The front is clean — and that is worth stating

Searching the published interface, the chatbot pages and the node components for work performed
**during** a run — `setInterval`, `refetchInterval`, polling loops, node-by-node dispatch — finds
nothing. The front's only run-time roles are starting a run and receiving socket events.

The nine front-driven node types (§4.1; eight after D24) were the exception, and they already have tasks. So the
answer to "is there anything in the front that should be in the worker" is **no, beyond what is
already planned** — which is a good sign about where the boundary sits.
