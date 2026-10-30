# B1 — One reference per execution, not per node

**Goal:** make the identifier that travels between nodes name **one execution of a node**, not
"a node within a run". Everything in Track B that passes data by reference depends on this.

**Depends on:** nothing. **Blocks:** B3, and therefore B4/B5; also A7.

## Why

**Corrected 2026-08-24.** An earlier version of this task claimed `(execId, nodeId)` names "a node
within a run" and that loops break it in general. That is only half true, and the real situation is
more interesting: **`execId` means two different things depending on which path ran the node.**

- **Temporal path** — `processNodeViaTemporal` does `const execId = uuid()` **per node dispatch**
  (`flux.service.ts`). Each execution, including each loop iteration, gets its own id. Here the
  pair is already unique.
- **Legacy path** — `recordLegacyNodeStart` is called with `execId: runLogProcessId`
  (`flux.service.ts`), which is **the same value for every node in the run**. Here the pair
  collides on every loop iteration, exactly as originally described.

So the defect is not "loops break the key". It is that **one column carries two incompatible
meanings**, and this epic is about to merge the two paths into one. Whichever meaning survives has
to be chosen deliberately, because the merge will otherwise pick one by accident.

The mechanical hazards below are real on the legacy path today, and become general the moment the
paths converge (analysis §8.4):

- `node_executions` has **no unique constraint** on `(execId, nodeId)`; only a plain index
  (`1776400000000-AlterNodeExecutionsForRunScopedIpc.ts`).
- `openNodeExecution` is a plain `INSERT`, no `ON CONFLICT`
  (`back/src/temporal/single-node-legacy/node-execution-store.ts`), so repeated executions
  insert additional rows.
- `persistNodeSuccess` updates `WHERE "execId" AND "nodeId"` — i.e. **every** such row
  (`worker/src/modules/nodes/shared/persist-node-success.ts`).
- `fetchNodeRow` takes `rows[0]` with **no `ORDER BY`** (`fetch-node-row.ts`); Postgres
  ordering is not guaranteed.

Contained today because the single-node path mints a fresh `execId` per click. It stops being
contained the moment a consumer reads an upstream's output by that pair, which is exactly what B3
introduces. Fixing it afterwards means changing the transport under running code.

## Scope

**In.** Choose and implement the identity. Two candidates:

- **`node_executions.id`** — the existing primary key — becomes the reference that travels.
  Cheapest; `(execId, nodeId)` stays a lookup, never a transport.
- **An iteration discriminator** added to the key, so `(execId, nodeId, iteration)` is unique.
  More invasive, but keeps the reference human-readable in logs and makes the loop position
  explicit — which B6 will want anyway.

**Pick one, write down why in this file.** The choice constrains B3 and B6.

**Recommendation: keep the Temporal meaning — one id per node execution — and make the legacy path
conform.** It is already the stricter of the two, it is what `node_executions` was documented to
be ("one row per node run"), and it is the only one of the two that survives loops and parallelism
without a discriminator.

**Sub-flows do not share the parent's execution identity.** A sub-flow is a different graph with
its own scheduler state; merging it into the parent's would mean one state holding two node sets
and two termination conditions. It gets its own run identity, **chained to the parent** — see
`TASK-S1`, which owns that chain.

**Corrected 2026-10-05.** Today a sub-flow *does* write under the parent's id: when space logging
is on, `runLogProcessId` resolves to the injected collector's `processId`, i.e. the parent's, and
every node of the child is recorded under it. Prod confirms this is not hypothetical — it is
**the main source** of repeated pairs (see *Measurements*). B1 removes the collision for sub-flows
as a side effect of the per-execution id, because every node execution now mints its own. What
stays with S1/D13 is the *run* identity: the child's rows still carry the parent's run in
`metadata.runId`, and whether a child should be a separate run in history is theirs to decide.

**In.** Whichever wins: a unique constraint or an explicit documented reason there is none,
`ORDER BY` on every read that can match more than one row, and a targeted `persistNodeSuccess`.

**Out.** Changing loop semantics. B6 owns those; B1 only makes them addressable.

## Decision, 2026-10-05 — one `execId` per node execution, on both paths

**Chosen: the Temporal meaning.** `execId` names one execution of one node. The legacy flow loop
in `FluxService.apiV2` now mints `nodeExecId = uuid()` per node, adopts it into the chain root of
the run (`chainRootRegistry.adopt(nodeExecId, runLogProcessId)`, the same call the Temporal path
already makes), and uses it for every write about that node: `chargeContext`,
`recordLegacyNodeStart/Success/Cancelled`, `recordInApiNodeError`, `markNodeStoppedByCeiling`.
The run id stays where run grouping already reads it: `metadata.runId`
(`COALESCE(metadata->>'runId', execId::text)` in `execution_logs.service.ts`, `runId ?? execId`
in the front).

**Rejected:** promoting `node_executions.id` to the transport (the pair would stay ambiguous as a
lookup, and the worker, claim-check keys and billing all key on the pair) and an iteration column
(adds a migration and a third field to every reader for what a fresh id already gives). B6 can
still add an iteration number as *metadata* if it wants loop position in logs.

**Why the legacy id was a run id.** It was never designed — `runLogProcessId` is the value that
already existed when node-level rows were added. Nothing reads a legacy row by the pair except
the end-of-run close, which now takes the list of ids the run opened
(`closeInFlightNodeExecutionsForRun(execIds[])`).

### Where one node actually executes more than once under one id

Audited 2026-10-05 against `back@origin/production`. The main loop is a DAG walk and never
revisits a node, so the original "loops" premise is narrower than written:

| Case | Before | After B1 |
|---|---|---|
| Main loop, each node | one row under the run id | one row under its own id |
| `arrayNode` body, inline nodes | **no row, no status**, but billed under `(runId, nodeId)` — iterations 2..N skipped by the `updateTokens` guard | each iteration bills under its own id |
| `arrayNode` body, worker nodes | own id per dispatch (Temporal) | unchanged |
| Sub-flow (`fluxBox`, library node, flow caller) with space logging on | child nodes written under the parent's id | own id per node |
| Same sub-flow called twice by one parent | duplicate pairs | none |
| Prefetch | one id per run, rows targeted by primary key | unchanged |
| Single-node run, API single node | fresh id per click | unchanged |

### Billing — behaviour change, approved

`ProductService.updateTokens` skips a charge when a `token_transaction` row already exists for
`(execId, nodeId)`. With a run-level id this silently dropped every repeat after the first: inline
nodes in an `arrayNode` body and sub-flow nodes executed twice. **With a per-execution id each
execution is billed** — approved by the epic owner on 2026-10-05: a loop body that does nothing
billable (a counter, a text edit) still costs nothing; any node that charges is charged on every
iteration. The guard keeps doing its real job — deduplicating a retried charge of the *same*
execution.

`sumChargesByExecution(execId, nodeId)` is a report, not a bill. Before, for a repeated pair it
returned the sum of every execution; now it returns the charges of the execution being closed,
which is what the run log and the cancelled-node `nodeUsedTokens` meant to show.

The loss cannot be sized from data: a suppressed charge leaves no row. Q2c sizes the population
that was exposed; follow-up `868mdkh7y` re-runs it one week after release and compares per node
kind. Expected shape: run-level charge rows for the inline kinds trend to zero.

### Claim-check

The S3 key is `node-exec/<execId>/<nodeId>-<field>.json`. Two executions under one pair
overwrote each other's payload; prod shows 20 envelopes inside duplicate pairs (Q4). With a
per-execution id the keys are distinct. No backfill — the overwritten payloads of past runs are
not recoverable and the rows are pruned by retention.

### The unique index — gated, follow-up

A `UNIQUE("execId","nodeId")` would refuse inserts the moment any path still writes a repeat, and
a false refusal fails a customer run. So it does not ship with B1:

1. Release B1. Run **Q1c** (duplicates among rows created after the release) daily.
2. After seven consecutive days at 0, ship a **partial** unique index
   `WHERE "createdAt" >= <release>` — historical duplicates stay readable, 506 pairs in 30 days
   of prod would otherwise block the migration.
3. If Q1c is not 0, the remaining writer is found and fixed first; the index waits.

Until then, every read and write that can match more than one row targets the newest execution
explicitly (`ORDER BY "createdAt" DESC, id DESC LIMIT 1`, helper `latestNodeExecutionId` in back
and worker) instead of relying on Postgres order.

### Found while auditing — not fixed here

- **Email-triggered runs write no legacy rows.** The queued run's `processId` is
  `params.parentProcessId ?? jobId`, and the POP3 job id is `pop3-processed:<id>` — not a uuid —
  so every legacy `INSERT` into `node_executions` fails and is swallowed. B1's per-node id makes
  those rows valid again (the node id is a uuid); `metadata.runId` still carries the job id. Run
  grouping for these runs belongs to S1/D13.
- **Addendum A (lost update in `updateUserProduct`) — measured, it loses updates.** See the
  measurement at the end of Addendum A. The fix is its own task.

## Measurements, prod, 30 days to 2026-10-05

Queries: [`b1-q2-prod-measurements.sql`](b1-q2-prod-measurements.sql), validated on dev in a
read-only transaction. Prod output: [`b1-q2-prod-measurements.prod.csv`](b1-q2-prod-measurements.prod.csv)
(the queries in file order; Q2 returns no rows).

| Query | Result |
|---|---|
| Q0 window | 1060 MB, 63.4k rows, retention 30 days |
| Q1 duplicate pairs | 506 — library node 457, flow caller 42, api 7 |
| Q1b cause | 221 same flow re-entered, 285 two flows sharing a nodeId |
| Q2 repeats with a charge | 0 |
| Q2b charges under a run-level id | ~1,215 rows — audioReaderNode 519, no row 417, commandContentNode 201, imageGenerator 51, webCrawling 21, fluxBox 3, webSearch 3 |
| Q3 ids spanning flows | 332 ids, 823 flows |
| Q4 claim envelopes in duplicates | 8 input + 12 output, of 713 |
| Q5 overlapping charges (Addendum A exposure) | 2,212 pairs among 37,989 charges, 13 users |

Every duplicate is a sub-flow — none come from a loop in the main graph. Q1c and Q2c are the
post-release gates above.

**Q2c baseline** ([`b1-q2c-baseline.prod.csv`](b1-q2c-baseline.prod.csv)) — charges under a
run-level id with no `node_executions` row. One node kind only, every one an `audioReaderNode`
called inline from an `arrayNode` body (the main loop writes a row, so it is excluded):

| node kind | cutoff side | charge rows | charges | credits |
|---|---|---|---|---|
| audioReaderNode | before 2026-09-25 14:32 UTC | 159 | 53 | 320.5 |
| audioReaderNode | after | 267 | 89 | 3,053.3 |

The cutoff separates time, not behaviour. It was meant as the audioReaderNode move to the worker,
but that move (`7067d2d0`, on production 2026-09-23) only routes the **main loop**; the
`arrayNode` body runs `this.audioReaderNode` inline on both sides. Normalised by window (about 20
days before, 10 after, bounded by `node_executions` retention): 2.6 → 8.8 charges a day and 6.0 →
34.3 credits a charge. Q2e breaks that down by day, user and model. This is the slice the
per-iteration id changes. **After release Q2c reads 0 by construction** — an iteration's id has
no `node_executions` row, so it never enters Q2c's run-level set, and a lost charge would read 0
too. The post-release check is **Q2f**: charges whose id has no row at all, grouped into runs by
`chainRootId`; `max_charges_per_run_node > 1` is the iteration billing showing up.

**Rows are not charges.** `updateUserProduct` writes one `token_transaction` row per part of a
charge (input, output, used; plus web search), so one charge is three rows — dev shows exactly
3× rows per pair for every node kind. 267 rows over 89 runs is **one** audioReader charge per run.
Q2d counts charges per pair in this slice; a pair stuck at 3 rows in a run whose `arrayNode` had
more than one item is a suppressed iteration. Q2b's row counts above are rows, not charges.

## Verification

- **Negative control (required) — done.** Integration specs against a real Postgres open one
  node twice under one `execId` and assert every read and write targets the second execution,
  including when the second row was inserted first. Observed red on production code, green after
  the fix: `back/src/app-api/flux/node-execution-identity.integration.spec.ts` (5 writers) and
  `worker/src/modules/nodes/shared/node-execution-identity.integration.spec.ts` (7 readers and
  writers).
- **End to end, local stack — done 2026-10-05.** Baseline `back@origin/production` `6dd9afae` vs
  the branch, same worker, same data. A charge is counted as a distinct `execId` in
  `token_transaction` (one charge = three rows).

  | Scenario | Baseline | Branch |
  |---|---|---|
  | `arrayNode` × 3 — `audioReaderNode` (inline) | 1 charge, under the run id | 3 charges, 3 ids |
  | `arrayNode` × 3 — `commandTextNode` (worker) | 3 | 3 |
  | `arrayNode` × 3 — `mathFunction` (no cost) | 0 | 0 |
  | Parent calls one child twice — duplicate pairs | 1 | 0 |
  | Parent calls one child twice — parent's `fluxBox` rows | **both cancelled** by the child's end-of-run close | untouched |
  | Same, child input 300 KB — claim-check keys | 2 (second PUT overwrote the first) | 4 distinct |
  | Status packets carrying `runId` | 12 of 14 (`arrayNode` had none) | 14 of 14 |

  Every run stays one run in history (`COALESCE(metadata->>'runId', execId::text)`), with no row
  left in flight and no error in the back log. The cancelled-parent row is a defect of its own on
  production: the child's close sweep matched the parent's rows because they shared the id.
  Not covered: cancel and budget-stop paths, concurrent runs, the worker latest-row change (covered
  by its integration spec).
- **Backfill check.** No migration; historical rows keep their run-level id and stay readable —
  run history groups by `metadata.runId` falling back to `execId`, which is the run id for them.
- **Billing.** Changes on purpose (see *Billing*). Q2c before and one week after release.

## Done when

No read that can match multiple rows relies on Postgres ordering; every node execution on both
paths writes under its own id; Q1c reads 0 for seven days, and then the partial unique index ships.

## Addendum, 2026-09-16 — how many times one charge reads `user_product`

Found while building S3 (`868m0vk05`) and assigned here because B1 already owns
`updateTokens` and its identity rules. **The first version of this note was
wrong and the correction is the point**, so it is written out rather than
quietly fixed.

`ProductService.updateTokens` calls `updateUserProduct` up to four times per
charge (flux input, flux output, web search, used tokens), and each opens by
re-reading `currentUser` and `userProduct`. That looks like four redundant
reads of one row, and the obvious "fix" is to read once at the top and pass the
instance down.

**That fix would silently under-bill.** Each call is a read-modify-write:

```ts
await this.userProductService.update(userProduct.id, {
  apiCalls: userProduct.apiCalls + apiCalls,
  usedTokens: usedTokens + userProduct.usedTokens,
  totalBill: userProduct.totalBill + cost,
});
```

The next call's `findOne` is what picks up the value the previous one wrote. So
the four reads are an accumulation chain, not four copies of the same answer —
hoisting a single instance across them would make each call add to the balance
the charge *started* with, and three of the four increments would be lost.

What is genuinely redundant is only the **fifth** read, the one S3 added:
`resolveChainSpendCeilingFor` re-reads `userProduct` purely for
`maxChainSpend`, immediately after the fourth call read the same row. And it is
the least urgent of the five, because it sits behind the `spend_ceiling` flag —
`enforceChainSpendCeiling` returns before resolving the ceiling when the flag
is off.

**The real change, if it is worth making:** accumulate the four increments in
memory and issue one write, then read the ceiling from the instance already in
hand. That turns five reads and four writes into one of each.

**It also closes a race B1 should care about.** Read-modify-write across four
separate round trips means two charges landing concurrently on the same
`user_product` can lose an update — the same lost-update shape S3 measured on
the tenant ledger, where 30 of 30 bursts got it wrong. Nobody has measured
whether it happens here; that measurement belongs with this task, and the
answer decides whether the rewrite is an optimisation or a fix.

**Why not in S3.** Every charge on the platform goes through this function, and
the change is now known to be subtler than it looks. It needs its own negative
control — one that bills a multi-part charge and fails if any increment is
lost.

**Files:** `back/src/app-api/product/product.service.ts` (`updateTokens`,
`updateUserProduct`, `resolveChainSpendCeilingFor`).

### Measured 2026-10-05 — it loses updates in every concurrent burst

Harness: the real `ProductService.updateUserProduct` with the real `UserProductService`,
`UserService`, `ReportService` and `TokenTransactionService` repositories on a local Postgres;
only the logger, the socket gateway and `isInternalUserProduct` (to keep `payBill` out) are stubbed.
One `user_product`, charges of 10 tokens, 30 bursts per width
([`b1-addendum-a-lost-update.measure.spec.ts`](b1-addendum-a-lost-update.measure.spec.ts)).
Control: five sequential charges add up exactly on every counter.

| Concurrent charges | Bursts losing `user_product` increments | Increments lost (max possible) | Bursts losing `report` tokens | Bursts with duplicate `report` rows | `token_transaction` correct |
|---|---|---|---|---|---|
| 2 | 30 / 30 | 30 (30) | 0 | 24 | 30 / 30 |
| 3 | 30 / 30 | 59 (60) | 5 | 25 | 30 / 30 |
| 5 | 30 / 30 | 119 (120) | 29 | 14 | 30 / 30 |

Concurrent charges on one `user_product` keep, in practice, only the last writer: `usedTokens`,
`apiCalls` and `totalBill` lose every other increment. The ledger (`token_transaction`) is always
right, so the loss is recoverable from it. The weekly `report` row races the same way and also
splits into duplicates (`findOne` then `create`).

**What it costs.** `totalBill` is the accumulator `payBill` compares to 50 before charging $50 on
Stripe, so a lost increment delays real billing; `usedTokens` is what plan allowance and
`extraTokens` read, so a lost increment lets a user spend past their quota. Local Postgres has no
network latency; prod's round trips widen the window, so this is a lower bound. Exposure in prod
(Q5): 2,212 overlapping charge pairs among 37,989 charges in 30 days, 13 users. Not measured:
`user.trialTokens` (same shape) and two concurrent `payBill` calls both crossing 50.

### Fixed 2026-10-05 — subtask 868mdm99b (back `e7366789`, `44700a35`)

Each part of a charge now updates `user_product` with one atomic `UPDATE … RETURNING`
(`UserProductService.addCharge`, the caller passes the per-token rate so negotiated terms on dev
keep their price); `users.trialTokens` is decremented under a row lock with the zero floor
(`UserService.consumeTrialTokens`); the weekly `report` row is incremented in place under a
per-row advisory lock and inserted only when absent (`ReportService.accumulateUsage`, no
migration); `payBill` deducts the 50 only when `deductFromBill` finds `totalBill >= 50`.
Negative control `user-product-concurrent-charges.integration.spec.ts`: red before (lost
increments, `trialTokens` 15 instead of 0, 0 payments for 90 charged), green after; breaking only
the report path turns it red again. Local E2E, three concurrent runs of one flow: baseline lost
22 of 54 `apiCalls` and 23% of `usedTokens`; with the fix every delta equals the ledger.

**Decisions (2026-10-05).**
- *The fifth read stays.* `resolveChainSpendCeilingFor` reads configuration only
  (`maxChainSpend`, no writer in `back/src`), the spend it compares comes from the Redis
  `ChainSpendLedger` (`INCRBYFLOAT`, atomic), the fix does not touch that path, and the read is a
  primary-key lookup run in parallel behind the flag. Removing it is an optimisation with no
  correctness gain; dropped from the acceptance criteria.
- *No reconciliation of past drift* (pending confirmation with product). Counters reset at
  renewal, past cycles were billed on the undercounted `totalBill` and cannot be recovered by
  editing counters, reconciling `totalBill` would charge customers immediately and reconciling
  `trialTokens` would block trial users. The ledger is not a complete mirror of the counters:
  Q7 on dev finds accounts both under and over it. Q7 sizes it in prod.

**Same shape elsewhere — audited, split into their own tasks.**

| Function | Concurrency | What a lost update costs | Task |
|---|---|---|---|
| `chargeUserProduct`, `createVoiceCloning` (+ `voice_cloning` string-concat bug) | cron / click | money, rare | 868mdtvhb |
| `updateSpaceTokens` (5 report tables, find-then-create; duplicates already on dev) | every charge | dashboards only | 868mdtvhg |
| `renewUserProducts` (snapshot, Stripe, absolute reset) | midnight window | money, rare | 868mdtvhw |
| flow / chatbot limit counters (`flow.controller.ts`) | click / MCP burst | plan limit exceeded | 868mdtvj4 |
| space token limit thrown and swallowed | — | product gap, not a race | 868mdtvj9 |
| `deleteVoiceCloning`, `updateFlowTriggers`, `createCompanySpace`, `checkUserCompanyFlows` | click | nothing reads the counter as a limit | left |
| `updateNamespaces` | none | dead code | left |

## Addendum, 2026-09-16 — the web-search charge is in the wrong unit

**Recorded here as a finding, not as work in this task** (confirmed with the
epic owner on 2026-09-16). B1's deliverable stays behaviour-neutral for
billing; acting on this one is not.

Found while measuring why the S3 spend ceiling (`868m0vk05`) never fired, and
assigned here because B1 already owns `updateTokens`. It is **not** what broke
the ceiling — that was chain-root fragmentation, fixed in S3 — but it sits in
the same sum and would quietly corrupt it for any run that searches the web.

`updateTokens` builds the credit total from four parts. Three of them convert
provider units into credits through `calculateTokens(model, units)` =
`units * model_price.fluxConversion`. The web-search part does neither half of
that:

```ts
const { cost: fluxWebSearchCost } = await this.updateUserProduct(
  { ..., usedTokens: webSearchCalls, model: modelWebSearch, ... }, flow, userId);

tokens.fluxWebSearchTokens = fluxWebSearchCost;
```

Two defects stacked:

1. **The raw call count goes in.** `webSearchCalls` never passes through
   `calculateTokens`, so `user_product.usedTokens` and
   `token_transaction.used_tokens` are incremented in *calls*, not credits.
2. **A cost comes out.** `fluxWebSearchTokens` is the only one of the four
   accumulator fields holding money. `totalTokens` therefore mixes units, and
   `accountChainSpend` compares that mixture against a credit ceiling.

A third, smaller symptom: `updateSpaceTokens` sums only input, output and used,
so web-search consumption never reaches the per-space report at all.

**Surface.** Small and closed: two model keys, `anthropic-web-search` and
`open-ai-web-search`, hardcoded at three call sites
(`anthropic.controller.ts`, `anthropic.service.ts`, `openAI.service.ts`).
Nothing in `worker`.

**Why this is not a bug fix.** `model_price.fluxConversion` is **10** for both
keys — in the repo seed (`src/database/seeders/modelPrice/data.ts`), in dev and
in staging. The value is configured and never read, so web search has been
billed at a tenth of the configured rate. Applying the conversion multiplies
what customers pay for web search by ten. That is a pricing decision, not a
correctness fix, and it is the reason this was not folded into S3 — nor into
C3, whose scope explicitly excludes anything that changes what a run produces.

The ambiguity cannot be settled from data: because the rate has never been
applied, nothing proves whether 10 is the intended price or a line that was
written and never took effect. Whoever owns pricing decides. If the answer is
"adjust the seed to the rate we actually charge", the code change becomes
billing-neutral and belongs in C3 instead, at wave 0.

**Measure before deciding.** Dev and staging are one restored dataset — identical
row counts and timestamps to the millisecond — and carry no web-search traffic
in the last 90 days, so neither can size the exposure. Run
`b1-q1-web-search-unit.sql` against production first; it reports prod's own
rate, the volume, the accounts reached, and separates the trial and prepaid
charges that no price decision would change.

**History.** Rows already written are in the wrong unit and a code fix does not
rewrite them, so any credit total spanning the fix mixes both units. Decide
whether that stays documented or gets a backfill.

**Files:** `back/src/app-api/product/product.service.ts` (`updateTokens`,
`updateUserProduct`, `calculateTokens`, `updateSpaceTokens`) ·
`back/src/database/seeders/modelPrice/data.ts` ·
`back/src/app-api/anthropic/{anthropic.controller,anthropic.service}.ts` ·
`back/src/app-api/openAI/openAI.service.ts`

## Addendum A subtasks — 2026-10-05

All on back `refactor/868m0vmun` (PR #2031), each proven red on a real Postgres before the fix
and merged to dev once. Specs: `user-product-concurrent-charges.integration.spec.ts`,
`flow-plan-limits.integration.spec.ts`; shared setup `real-postgres.test-support.ts`.

| Subtask | Commit | What was wrong | Fix |
|---|---|---|---|
| A2 `868mdtvhb` | `878c41d6` | Voice clone and cloned-voice cron were read-modify-write; `voice_cloning` stored `plan + 1` as a string (`251`, `unlimited1`); the cron's `report` insert omitted `usedTokens` (`NOT NULL`, no default) since `aec3f800`, so it charged `user_product`, failed, wrote no ledger row and charged again the next day | `addCharge` (clone keeps full price: `waiveWithinExtraTokens: false`), `accumulateUsage`, atomic `adjustVoiceCloning` |
| Reports `868mdtvhg` | `9d973c88` | Five find-then-create counters in `updateSpaceTokens`; TypeORM ignores `null` in `where`, so no-space charges hit a random space and no-company charges hit a user's own `report` row | `ReportService.accumulateRow` (advisory lock, `IS NOT DISTINCT FROM`, oldest row), no `spaceId` → no space |
| Renewal `868mdtvhw` | `3813e589` | Absolute reset after the Stripe wait wiped charges landing in between; `getUserProductsToRenew` saved a stale entity | `settleRenewal` subtracts the billed amount and the snapshot |
| Plan limits `868mdtvj4` | `5ec18b41` | Check-then-act: 5 flows on a plan of 3 | `claimPlanSlot` before provisioning, released on failure; NULL counts as 0 (0 false refusals on dev) |
| Space limit `868mdtvj9` | back `d420f73c`, front `refactor/868m0vmun` | Checked inside the counter update, thrown and swallowed: runs continued and the space counter froze at the limit | Decision 2026-10-06: the space limit blocks. `assertSpaceWithinLimit` before the run (`apiV2`, every entry point and nested runs, plus the canvas pre-check) → 402 `space_limit_reached`; counters keep counting and still reset on the 1st (`tokenLimitCron`). No limit = never refused; paid plans keep overage. Per-member `user_spaces.limit` dropped (nothing writes it; all null on dev). Front: dialog without "See plans", canvas Run reports plan limits. Dev: 8 spaces with a limit, all at 0 used, 0 refused on deploy |
| Enterprise renewal `868mdym0c` | `7cd69cb3`, `dc9b4830` (dev `8eca3350`, `6bff8fce`) | `extraTokens = Number('unlimited')` on a plan without a numeric allowance; the integer column rejects `NaN`, so the renewal loop stopped for every later account, and after a paid overage the catch set `active = false`. Same on the missing-period sync, where the throw aborted the whole selection | Decision 2026-10-06 (owner): an `unlimited` Enterprise without a numeric allowance is an internal no-limit account (dev and product teams) and must not change. Such a plan is left out of the renewal and of the missing-period sync — untouched exactly as before, never billed or deactivated by the renewal — and no longer stops the other accounts. Each other account renews in its own try/catch; a failure after a successful payment is logged, only a failed payment deactivates. On dev the rule asks `includedCreditsFor` with the negotiated terms, so a contract with terms still renews with its credits (checked ad hoc on dev: with terms → renewed, 20000; without → untouched) |

**Added 2026-10-06 (same branch):**

| Item | Commit | What changed |
|---|---|---|
| MCP plan limit (decision: MCP agents count toward the plan) | back `38cfef04` | `create_agent` / `remove_agent` claim and release the slot through the shared `ProductService.claimCreationSlot` / `releaseCreationSlot` (rule in `plan-limit.ts`); dry-run answers like the apply path; MCP chatbots enter `chatsId`. `mcp-agent-plan-limits.integration.spec.ts`, 9 cases, 7 negative controls |
| Plan-limit message (decision: the refusal must be clear) | back `3140bf26`, front `6faaab8b` | `createFlow` / `duplicateFlow` rethrow the 402 instead of "Something went wrong"; the front opens the plan-limit dialog on create, duplicate, Fluxbot quick-create and the dashboard modal |
| API-key and REST callers `868mebgw7` | back `bf23e69b` (P1), `5ce3019d` (P4) | `POST /integrations/agents` counts toward the plan (`createCountedFlow`); `unlimitedCompanyProduct` no longer matches an arbitrary company for an empty id. `/flux/api-v2` checks access, space limit and owner plan before it queues, so a refusal answers 402/403 at once instead of 500 or 202 + error callback. P2, P3, P5–P8 (trial tokens for no-plan users, trial decrement account, space-key scope, `get-completion` / `batch-process` access, worker charge failures) planned in [`b1-addendum-a-api-plan-parity.md`](b1-addendum-a-api-plan-parity.md) |

Dev validation: [`b1-addendum-a-dev-validation.md`](b1-addendum-a-dev-validation.md). Prod checks before the release (2026-10-06): no space would be blocked; no corrupted `voice_cloning` counter; the cloned-voice cron has written no ledger row since 2025-12 (only one internal account shows the re-charge); 3 unlimited accounts have a subscription, 2 not internal (D1, open). After the release: [`b1-post-release-runbook.md`](b1-post-release-runbook.md).

## Files

`back/src/app-api/flux/flux.service.ts` (`apiV2` main loop and `arrayNode` body, `emitNodeStatus`,
`finishCancelledNode`, `closeRunInFlightNodes`, the legacy record writers) ·
`back/src/app-api/flux/latest-node-execution.ts` (new) ·
`back/src/temporal/single-node-legacy/node-execution-store.ts` ·
`back/src/app-api/executions_logs/execution_logs.service.ts` (`closeInFlightNodeExecutionsForRun`) ·
`worker/src/modules/nodes/shared/{fetch-node-row,persist-node-success,persist-node-outcome,latest-node-execution}.ts` ·
`worker/src/modules/temporal/activities/activities.service.ts` (`generateExecutionLogsActivity`) ·
follow-up: `back/src/database/migrations/` (partial unique index, after the Q1c gate).
`ProductService.updateTokens` and `TokenTransactionService.sumChargesByExecution` are unchanged —
their behaviour changes through the id they receive.
