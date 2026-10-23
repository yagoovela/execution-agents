# A7 — Migrate `nodesBox` (Object Caller)

**Goal:** migrate the one mutating node whose logic is actually extractable, behind two new
callbacks and an explicit ordering guarantee.

**Goal, widened 2026-10-23:** also make every `worker` type reachable from both back loops, so no
node is skipped or run inline while the B4 flag selects either engine. See "Scope, widened
2026-10-23" below; it overrides the scope it contradicts.

**Depends on:** A1, **B1** (execution identity, shipped 2026-10-14), B4 code (the flag). Do not
start before B1 — this node's correctness depends on knowing which execution a write belongs to.

## Why it is different from the other four mutating nodes

`conditionNode`, `arrayNode`, `fluxBox` and `libraryNode` are control flow; they decide what runs
next, and belong in the workflow (B6). `nodesBox` mutates **data**, not control (analysis §3.5).
Its own logic is about 130 lines. The work is entirely in what has to exist around it.

Today it reads `data.selectedId` against `objectCallerData` — the engine's in-memory array for the
run — reads the latest session state for
`{scopeType:'object', scopeId, sessionKey, ownerUserId}`, then reads and/or writes the object's
content and publishes the change back through `onMutateObjectCallerData` so later nodes see it.
Handler `objectCaller()` in `flux.service.ts`; three dispatch sites — the full-run type switch, the loop-body path and the single-node path — plus the pre-run session clear.

## Scope

**In.** Three things, in this order:

1. **An object-state callback** — read and write, exposing `objectsService`. Model it on the
   existing `/worker/store-payload` contract rather than inventing a shape.
2. **A session-state callback** mirroring `sessionStateService.readLatest` and `appendEntries`
   for the `object` scope.
3. **An answer on ordering.** Today the engine serialises every Object Caller in a run through one
   in-memory array. Two callers touching the same object must stay ordered once they are
   independent activities. Two acceptable answers: an advisory lock, following the pattern already
   used in `worker/src/modules/nodes/third-party-integration/oauth-token.repo.ts`
   (`pg_advisory_xact_lock`), or an idempotent activity. **Pick one and state why** — do not ship
   without addressing it and hope the ordering holds.

**Out.** Changing object semantics, session-state scoping, or the chat behaviour built on it.

## Scope, widened 2026-10-23

The review below found that the scope above rests on a write that does not exist, and that the
back's loops skip or inline several `worker` types. This section replaces items 1 and 3 above
where they disagree.

**In — the Object Caller itself.**

1. **Execution record.** The activity writes the `node_executions` row like every worker node:
   `input` holds `selectedId`, the session key and the element inputs; `outputData` holds the
   element values after the write.
2. **Consumers by reference.** A consumer records which writer execution it read, not a copy of the
   object text. Object text that a run produces is therefore stored once, in the writer's row, and
   follows a retention policy decided in this task.
3. **Read rule.** A consumer reads the writes that completed before it was scheduled, not the latest
   at read time, so a Temporal retry reads the same value.
4. **Implicit edges.** `buildSchedulerState` derives ordering edges from object access (writer to
   writer, writer to reader, in today's tie-break order). Both engines use it: the back's loop is
   the same DAG scheduler run one node at a time, so the order does not change on the back's loop
   and stays defined when B5 dispatches a batch.
5. **Session writes in the back.** One callback, idempotent per `execId` + `nodeId`, calls
   `sessionStateService` for the `object` scope. One advisory lock per
   `objectId:sessionKey:ownerUserId` covers read, merge and append in one transaction, with
   `SET LOCAL lock_timeout`. `clearObjects` takes the same lock.
6. **Read side switched by the B4 flag.** With the flag off, the back's loop keeps feeding
   downstream nodes from `objectCallerData`, now updated from the activity's result. With the flag
   on, the worker projection reads by reference. A shadow comparison on the back's loop logs any
   difference before the flag is turned on, as B3b did.

**In — every worker type reachable from both loops** (moved here from the coverage audit's A12).
Replace the per-type `if` branches in the full-run loop and in the `arrayNode` loop body with one
branch derived from the registry (`dispatchesToWorker`). This closes three gaps:

- `animationNode`, `secApiNode`, `usCensusNode` and `webAmazon` are never executed by a full run in
  production (STATUS A6, open since 2026-10-15).
- `sqlQuerier` still runs inline through `sqlQuerierNode()` in both loops on `main`, contrary to
  A3's Done-when. **Not redone here:** back branch `feat/sql-node` (commit `196df420`, 2026-10-22)
  already routes both loops through `processNodeViaTemporal` and deletes `sqlQuerierNode()`. It has
  no PR yet and is 63 commits behind `main`. Assumption (2026-10-23): it ships in the Monday
  2026-10-26 deploy with E1 and B4, before A7's code, so A7's generic branch replaces that per-type
  branch.
- The loop body also misses `thirdPartyIntegration`, `hubSpotCRM`, `outputController`,
  `reportBuilder`, `counterNode` and `fileSave`.

**Out.** Unifying the object owner rule (A7-D7), the two session flags (A7-D5), the chat scope
(A14), and the Data Output sink (A13).

## Verification

- **Negative control (required).** Remove the ordering guarantee and write a test that runs two
  Object Callers against the same object concurrently, asserting the final content. Watch it go
  red — an intermittent test is not acceptable here, so make the race deterministic by holding the
  lock explicitly in the test rather than relying on timing.
- Session-state parity: `readLatest` / `appendEntries` through the callback must produce the same
  rows the inline path produces, on real stored objects.
- The chat path (`fluxObject` / `nodesBox` with chat enabled) must be unaffected — it is written
  at run finalisation (`flux.service.ts`), outside this node.

## Done when

`nodesBox` satisfies PLAN §3.4; both callbacks exist and are documented in D1; the ordering
decision is recorded in this file with its rationale; the inline handler is deleted.

Widened 2026-10-23: every `nodesBox` execution has a `node_executions` row on both engines; a test
asserts that every `worker` type in the registry is dispatched by the full-run loop and by the loop
body, and it has been seen red; `sqlQuerierNode()` is deleted (by `feat/sql-node` or by A7,
whichever lands first).

## Files

`back/src/app-api/flux/flux.service.ts` (`objectCaller()` + its three dispatch sites) ·
`back/src/temporal/worker.controller.ts` (new callbacks) · `back/src/app-api/objects/` ·
`back/src/app-api/session_state/` · new `worker/src/modules/nodes/object-caller/` · the A1 registry ·
`back/src/app-api/flux/scheduler.ts` (implicit edges, ported to the worker through B2's sync) ·
`back/src/app-api/flux/edge-projection` and the worker port (`getOutputByType`) ·
`back/src/app-api/flux/node-input-projection.ts` and the worker copy

**Branches.** Cut the back and worker branches from `origin/main`. The worker branch merges
`origin/feat/wave-4-b4` locally so the B4 flag can be validated with A7; the PR body says so, and
A7's worker PR to `main` waits for B4's (A7-D4).

## Review against production and B4 (2026-10-23, open)

This section records the review that opened the task. The sections above are unchanged until the
open decisions close. Evidence: [`TASK-A7-OBJECT-CALLER-CURRENT-PROCESS.md`](./TASK-A7-OBJECT-CALLER-CURRENT-PROCESS.md)
(how the node works today), [`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md)
(epic-wide node coverage), and the queries `a7-q1` to `a7-q3` in this folder (copy in `etc/wave5-a7/`).

### State of the dependencies

- B1, B3 and B3b are in production since 2026-10-14.
- B4 back merged into back `main` on 2026-10-23 (#2060) and is not deployed. B4 worker (PR #138) is
  on worker `develop` only.
- The `engine_in_workflow` flag is global by design (product owner, 2026-10-23). TASK-B4 says "per
  flow"; that text is wrong.

### What the scope above gets wrong

1. **No object write exists.** `objectCaller` never writes `flow_objects`; only the UI does. A write
   lives in the run's in-memory `objectCallerData`. Session objects also append a full snapshot to
   `session_state_entries`, without `execId` or `flowId`.
2. **No execution record.** `node_executions` holds no `nodesBox` row on dev, for any period, while
   other inline types appear. The object value a run used cannot be recovered afterwards.
3. **Four entry paths, not three:** full run, loop body, single node, and the prefetch loop. The
   pre-run `clearObjects` and the chat override of `selectedSession` also touch object state.
4. **B4 gap.** Flipping `nodesBox` to `flowDispatch: 'worker'` makes its flows eligible for
   `processFlow` on the same commit, where the worker projection passes `undefined` as
   `objectCallerData`, so downstream nodes get empty text.
5. **Two session flags.** The node flag (`data.sessionEnabled`) gates the pre-run seed; the object
   flag gates the read and the write. Dev: 35 callers set the node flag, 11 set both (reset on every
   run), and 24 set only the node flag (session rows written and never read).
6. **The race is cross-run, not only cross-branch.** Within one run, calls are serial today and
   under B4. Across runs of one flow, `readLatest` then append has no lock, so the later stale
   snapshot wins.

### Product requirements (2026-10-23)

- Every node writes a database record of its execution, for determinism and audit.
- A consumer reads the value it needs from the database, or from the owner of the current value when
  the value must be live at read time.
- The integrity of a node's inputs and outputs holds at the time the node uses them.
- No executable node type remains outside the worker at the end of the epic.

### Changes to make, and how

| # | Change | How |
|---|---|---|
| 1 | Record every `nodesBox` execution | The worker activity writes the `node_executions` row like every other worker node: `input` holds `selectedId`, session key and element inputs; `outputData` holds the element values after the write; `execId` is set. |
| 2 | Make run-scoped object state durable | The source of truth is the run's `nodesBox` rows. The value of an object for a consumer is the latest completed `nodesBox` write to that object in the run, else the stored template in `flow_objects`. |
| 3 | Feed the worker projection | `getOutputByType` resolves a `nodesBox` source from item 2 instead of `objectCallerData`. Remove `nodesBox` from `BACK_ONLY_PROJECTION_NODE_TYPES` (back and worker). The consumer records the value it read in its own `input`. |
| 4 | Order session writes (A7-D3) | One advisory lock per `objectId:sessionKey:ownerUserId`, held for read, merge and append in one transaction inside `sessionStateService`, taken by both object-scope writers: the callback and `clearObjects`. Bound the wait with `SET LOCAL lock_timeout`, because a waiting transaction holds a back pool connection. |
| 5 | Stamp session rows | Pass `execId` and `flowId` on every object-scope append. |
| 6 | Owner resolved once (A7-D7) | The back resolves the object owner once per run and puts it in the run seed, keeping each path's current rule until A7-D7 closes. |
| 7 | Cover all four paths | Delete the inline handler from the full run, loop body, single node and prefetch paths. Set `prefetchSafe` from what the activity really needs. |
| 8 | Characterise before deleting | No test covers `objectCaller` or `clearObjects` today. Add parity tests on the back first, then run them against the worker path. |
| 9 | Negative controls | Downstream node under `processFlow` gets non-empty text (red before item 3). Two concurrent session writes keep both updates (red without item 4, lock held explicitly in the test). |
| 10 | Callback shape | If any callback remains, model it on `/node-credit-gate` or `/run-events` (DTO class, `@HttpCode`), not on `/store-payload`. |

### Decisions

| Id | Question | Status |
|---|---|---|
| A7-D1 | Projection and execution record in A7, or deferred to B6 | **Settled 2026-10-23: A7.** Solving it outranks the estimate. A7 is built and works without B4: legacy loop, loop body, single node and prefetch. |
| A7-D2 | Session reads and writes from the worker directly, or through a back callback | **Settled 2026-10-23: back callback.** One implementation in `sessionStateService`. The callback is idempotent per `execId` + `nodeId`, so a Temporal retry after a lost response does not append twice. |
| A7-D3 | Advisory lock or idempotent activity | **Settled 2026-10-23: advisory lock**, in `sessionStateService`, taken by both object-scope writers: `objectCaller()` (through the callback) and `clearObjects()`, both in `flux.service.ts`. The chat scope (`scopeType: 'chat'`, appended in `apiV2`'s finalisation) is not involved; A14 needs no lock, because it derives Small Memory content from stored executions instead of writing it. An idempotent activity alone does not prevent a lost update between two runs. |
| A7-D4 | A7's worker PR waits for B4 worker on `main` | Agreed 2026-10-23. Coordinate the order with the B4 owner. |
| A7-D5 | Unify the two session flags, or keep today's behaviour for parity | **Settled 2026-10-23: keep today's behaviour for parity.** Unifying is a product change, not part of A7. |
| A7-D6 | Under B5, two `nodesBox` nodes on one object in one run: serialise, or accept arrival order | Direction 2026-10-23: the DAG orders them. The graph has no edge between two callers of one object, so the scheduler must derive implicit edges from object access (writer to writer, writer to reader) in today's tie-break order, inside `buildSchedulerState`. A consumer reads the writes completed before it was scheduled, not the latest at read time, so a retry reads the same value. |
| A7-D7 | Unify the object owner rule (full run uses the runner's selected company, single node uses space then user) | **Settled 2026-10-23: keep each path's rule**, resolved once by the back and carried in the run seed. Unifying is a product change, not part of A7. |
| A7-D8 | Read side while the B4 flag exists | **Settled 2026-10-23: the B4 flag switches it.** Flag off: the back's loop reads `objectCallerData`, fed by the activity's result. Flag on: the worker reads by reference. A shadow comparison runs on the back's loop before the flag is turned on. |
| A7-D9 | Protection on the internal callback | Proposed 2026-10-23, pending: no requests-per-minute limit; bound the lock wait, cap concurrent callbacks per back instance with a retryable `503`, and alert on lock wait and refusals. |

### Still needed before implementation

1. Production counts: run `a7-q1` to `a7-q3` in DBeaver.
2. Confirm A7-D9.
3. Rewrite the ClickUp description. Its spec link points at `.specs/features/...`, which does not
   exist on `main`.
4. Re-estimate. The current 40 hours assume two callbacks only; the widened scope adds the
   execution record, the implicit edges, the read switch with its shadow, and the registry-driven
   dispatch in both loops.
