# B5 — Turn on parallel dispatch

**Goal:** a flow whose nodes all run on the worker runs its ready nodes at once, up to a per-run cap
(`maxInFlight`), so its wall-clock time approaches its slowest path instead of the sum of its nodes.

**Depends on**

- **Build:** [B6](TASK-B6-CONTROL-FLOW.md) (B5 is built on its `processFlow`; B6 ships first, still
  sequential), [S1](TASK-S1-SUBFLOW-CEILING.md) (sub-flow depth ceiling and cycle check),
  S2 (worker pool and DB connection ceiling), S3 (per-run spend ceiling and per-tenant run cap),
  E3 (cross-replica notifications).
- **Production ship gate:** B6 in production, and B4 running in production with
  `engine_in_workflow` on for a soak period. Development and the dev validation do not wait:
  `engine_in_workflow` has been on in dev since 2026-10-23.

ClickUp: [868m0vmkd](https://app.clickup.com/t/868m0vmkd). Decisions D17, D20, D23 and the risk R4
are in [PLAN.md](PLAN.md). Re-specified on 2026-11-19 and reviewed with EGM the same day (reports in
the session's `etc/2026-11-19/egm-b5-review/`); the 2026-10-23 version is in git history.

## Problem

`processFlow`, the Temporal workflow that runs a flow on the worker, runs one node at a time: it takes
one ready node, waits for it to finish, and only then takes the next. A flow with eight independent
image generations therefore takes the sum of the eight. The engine was built to run independent nodes
together, but nothing dispatches more than one.

## Goals and non-goals

**Goals**

1. Run the ready nodes of an eligible flow concurrently, up to `maxInFlight`.
2. Keep every run that is not eligible, or not on the rollout allowlist, exactly as it runs today.
3. Roll out by company, with a flag that turns it off for new runs.

**Non-goals**

- Running the iterations of one `arrayNode` concurrently.
- Changing the failure DTOs between the worker and the back.
- Adding the eligibility gate to the batch and Temporal-schedule starts (see
  [Current state](#current-state-code-read-2026-11-19), item 3).
- Parallel nodes inside batch rows in v1: batch rows already run 5 at once.
- The per-provider concurrency budget: it moves to **B5b** (decision B5-g).
- A per-tenant node budget (see [Open risks](#open-risks)).
- The agent view's "Step X of Y" counter (`useAgentRunSession.ts:165`).

## Current state (code read 2026-11-19)

Worker `origin/develop` @`2c7ea9d` (B6 included), worker `origin/main` for the pre-B6 lines, back
`origin/develop` @`8c72a38c`.

1. **The sequential bottleneck is the workflow loop.** On `main`, `processFlow`
   (`worker/src/modules/temporal/workflows/process-flow.workflow.ts`) takes one node with
   `nextReady(state)` (:155), waits for it with `await executeChild(processSingleNode, …)` (:231), and
   stops at the first failure with `break` (:317). `nextReady`
   (`worker/src/ported/back/app-api/flux/scheduler.ts:295-308`) marks only the node it returns as
   `scheduled`.
2. **Only all-worker flows reach the workflow from `apiV2`.** `apiV2` sends a flow to the workflow only
   when `ineligibleWorkflowNodeTypes` is empty (`back/src/app-api/flux/engine-selector.ts:5-16`,
   decided at `flux.service.ts:5172-5188`). An **inline node** — a type that
   `ineligibleWorkflowNodeTypes` returns, which runs inside the back — sends the flow to the legacy
   loop. On the workflow path every node writes only its own row (`persist-node-outcome.ts:27`), and
   `addConnectToNodes` (`back/src/app-api/folw/contants.ts:1568`), which writes into another node's
   data, runs only before the run starts. So parallel nodes cannot overwrite each other's rows.
3. **The batch and Temporal-schedule starts skip that gate** (`process-batch.workflow.ts:105`,
   `run-scheduled-flow.workflow.ts:66`). A flow with an inline node fails there with
   `Node type X not supported`. This predates B5 and is tracked separately.
4. **S3 counts runs, not nodes**, and only on the queue path (`TenantConcurrencyLedger`,
   `apiV2Job.processor.ts:189-200`).
5. **The platform runs 10 nodes at once.** The production worker service runs **1 replica with no
   autoscaling** (read-only, 2026-11-19), each replica runs at most 10 activities
   (`temporal.constants.ts:1`), and the DB pool is sized to it (S2). No activity has a
   schedule-to-start timeout, so extra nodes wait in the Temporal queue; they do not fail.
6. **No provider concurrency limit exists** in code, in the production task definitions or in feature
   flags (read-only, 2026-11-19). Provider 429s are mapped per call (`text-generator.service.ts:183`,
   `hubspot-http.ts:117`).
7. **Feature flags target `USER`, `COMPANY` or `SCHEDULE`** (`isEnabledFor`,
   `feature-flags.service.ts:154-180`) and carry a numeric `value` (`getValue`, :35). The worker reads
   no flag today but already queries Postgres (`databaseService.pool`).
8. **Only two activity types stop when cancelled.** `textGeneratorActivity` and `apiCallerActivity`
   use `WAIT_CANCELLATION_COMPLETED` (`configs.ts:12-30`). Every other activity uses Temporal's default
   `TRY_CANCEL`: the workflow records the node `CANCELLED` at once while the activity keeps running,
   and its result is discarded. `processSingleNode` returns `status: "CANCELLED"` instead of throwing
   (`process-single-node.workflow.ts:61-63, 395-410`). The `node_cancel_in_flight` flag is read only
   by the back, not by the worker. Today a node is cancelled only by a person or a cleanup job; a
   deploy drains for 100 s and then retries or fails the node (A9c).
9. **B6 rewrites the same loop.** On `develop`, `processFlow` runs `arrayNode` iterations inside
   `nonCancellable` (:290-450), resolves `conditionNode` with `completeCondition` (:535), and runs
   `fluxBox`/`libraryNode` as a `childFlow` child workflow (:578-674). Sub-flow depth is capped at 3
   (`SUBFLOW_DEPTH_CEILING`, `subflow-chain.ts:3`).
10. **Two places assume one in-flight node.** The run list picks one with `MAX(...)` over four columns
    (`inFlightNodeId`, `inFlightExecId`, `inFlightWorkflowId`, `inFlightNodeType`) and derives
    `stepInterruptible` from it (`execution_logs.service.ts`); `settleAbandonedRuns` checks one
    workflow. The socket payload already carries a status per node
    (`front/src/components/Socket/Socket.tsx:168-234`).

## Reference use case

The most sub-flow-heavy customer space in dev (measured read-only on 2026-11-19; the same customer
runs in production): 136 flows, 324 sub-flow nodes (101 `fluxBox`, 223 `libraryNode`), and the 10
most sub-flow-heavy flows of the whole platform.

- **Its production chain is deep and narrow.** The entry flow calls an orchestrator, which calls agent
  flows, which call small library flows: 3 child levels. The entry flow has 33 executing nodes in 26
  levels (widest level 4); the orchestrator and the library flows are strict chains (width 1). The
  agent flows have a first level of 1-2 text generations next to 3-4 library calls, then a loop closed
  by a `conditionNode`.
- **Expected speedup is small: about 1.2-1.5×** for one run, mostly from the agents' first level and
  the entry flow's first level. Many sub-flows does not mean a wide graph. A test wrapper that calls 12
  sub-flows in one level is the exception (up to 9×).
- **Where the time goes.** Dev runs (95 since May, inferred from `execution_logs`): p50 114 s, p90
  781 s, longest 35 min; 60-80% of the long runs' log rows come from two library flows (`scripting`
  and `apiCaller`). The runs of about 1 hour exist only in production; dev keeps no per-node timings
  for them.
- **Side effects in sub-flows.** The library flows that set values run 2 `apiCaller` each, so a
  `libraryNode` can write. Under fail-fast, a failing text generation in the agents' first level
  (the most common failure in these flows) cancels in-flight library calls whose writes may have
  started.
- **Depth.** The production chain sits at depth 3. Test wrappers reach depth 4-5. In production the
  back refuses by the root flow's `maxCascadeSize` (S1); on the workflow path B6 refuses above
  `SUBFLOW_DEPTH_CEILING` = 3. **B6 must reconcile the two before it ships**, or flows that run today
  are refused.

Production check: the owner of the rollout runs, in DBeaver, the per-flow query saved with the
review (`prod.sql`: sub-flow count and run wall-time p50/p90/max per flow) and the per-node timing of
the hour-long runs, to confirm the speedup before the rollout.

## Decisions

| Id | Question | State | Answer | Rejected, and why |
|---|---|---|---|---|
| B5-a | What turns parallelism on for a run? | Settled 2026-11-19 | The back decides once per run: the existing gate (`canUseWorkflowForFlow`) and the `parallel_dispatch` flag through `isEnabledFor` with a `COMPANY` allowlist. Rollout: internal companies, then a group of customers named in the rollout plan, then everyone (`isEnabled`). Turning the flag off restores sequential dispatch for **new** runs; runs already started keep their `maxInFlight`. | A `FLOW` target or a percentage rollout: neither exists in `FeatureFlagTargetType`. A decision in the worker: the worker reads no flags. |
| B5-b | What does a cancelled node do? | Settled 2026-11-19 | Today's settlement applies (D20, D23, `resolveCancelSettlement`): `textGenerator` and `apiCaller` stop, and text generation is charged for the tokens it used; every other activity keeps running under `TRY_CANCEL` and its result is discarded. | — |
| B5-c | Is graph order between two independent side-effect nodes a contract? | Open | Order comes from the flow's dependencies. Before the rollout widens past internal companies, count the production flows with two or more independent side-effect nodes in one ready level; then prefer an explicit edge. With parallel dispatch a failure no longer prevents an independent side effect that already started. A Data Output (`outputObjectNode`) that ran in a failed run still sends its email and callback (`deliver-run-outputs`), so a failed parallel run can deliver outputs that a sequential run stopped before. | A side-effect-only dispatch lane: a second per-type classification before the count exists. |
| B5-d | What happens when a parallel node fails? | Settled 2026-11-19 | **Fail-fast, behind its own flag.** The first genuine failure cancels every leaf sibling in flight, except when that failure is a `WorkerShutdown` (then the run drains). An in-flight `fluxBox` or `libraryNode` child is never cancelled: it runs to its end, because a library flow can hold half-done external writes (`apiCaller`). Each cancelled sibling records the reason ("stopped because node X failed"). The run is named by the genuine failure with the lowest dispatch index. With `parallel_fail_fast` off, the run drains instead. The contract stays singular: no DTO changes. | Drain only: reports a failure up to the slowest sibling later. A list of failures: a cross-repo DTO change. Cancel sub-flows too: stops a library flow between two external writes. |
| B5-e | How do B5 and B6 relate? | Settled 2026-11-19 (reverses D17's order) | B5 is built on B6's `processFlow` (`feat/868m0vmvr`). B6 ships first, sequential. | Build on `main`: rewrites the loop twice and dev differs from `develop`. Ship together: one bigger deploy, harder rollback. |
| B5-f | How do the control-flow nodes run? | Settled 2026-11-19 | `conditionNode`, `arrayNode`, `fluxBox` and `libraryNode` run concurrently with their siblings, under the rules in [Design](#design). A sub-flow inherits the **same** `maxInFlight` as its parent. | Barriers: give up the speedup of array- and sub-flow-heavy flows. Halving per level: at the default 2 a depth-2 agent flow runs sequentially, which removes the gain in the reference use case. A shared tree budget in Redis: a new lease for a bound the worker's 10 activity slots already give. |
| B5-g | Which concurrency limits ship? | Settled 2026-11-19 | B5 ships the per-run cap. The fleet-wide per-provider budget is **B5b**, which ships before the worker scales past 1 replica or the rollout reaches customers, whichever comes first. B5b keeps one flag per provider (`provider_cap_<key>`, `value` = cap), read by the worker with a 60 s cache, failing open. | Ship the budget in B5: no provider limit is known, so it would limit nothing on day one. An env var: every change needs a deploy. An adaptive limiter: more state, and one noisy tenant lowers the cap for everyone. |
| B5-h | What cap values ship? | Settled 2026-11-19 | `maxInFlight` = `clamp(floor(flag value ?? 2), 1, 4)`. Batch rows run sequentially in v1. Raising the ceiling needs a scaled worker (with the DB pool checked against S2 and S11) and B5b. | Default 4, ceiling 8: one run could hold 8 of the platform's 10 slots. |

**Genuine failure:** a node outcome `failed`. A cancellation is not a failure.
**Dispatch index:** a counter incremented each time a node enters the in-flight set.

## Requirements

| Id | Requirement |
|---|---|
| B5-R1 | Without `maxInFlight` > 1, or on a history recorded before the patch, a run produces the same node order and the same history events as today; histories recorded on B6 replay without a nondeterminism error. |
| B5-R2 | The number of nodes in flight in one workflow never exceeds that workflow's `maxInFlight`. |
| B5-R3 | An `arrayNode` holds its body nodes exclusively while it runs: no body node runs outside the loop, iterations stay sequential, and two arrays whose bodies overlap run one after the other. |
| B5-R4 | `conditionNode`, `fluxBox` and `libraryNode` run concurrently with their siblings; a dead branch is never dispatched; a sub-flow runs with the parent's `maxInFlight` and keeps its own S1 chain. |
| B5-R5 | With `parallel_fail_fast` on, the first genuine failure cancels every leaf sibling in flight unless the failure is a `WorkerShutdown`; in-flight `fluxBox`/`libraryNode` children run to their end; each cancelled sibling records the reason; the run is named per B5-d. With it off, or for a `WorkerShutdown`, the run stops dispatching, lets the siblings finish, then fails. |
| B5-R6 | Continue-as-new happens only with no node in flight. |
| B5-R7 | The back returns `maxInFlight` for the `apiV2` and Temporal-schedule starts only when the flow passes `canUseWorkflowForFlow` and the company is on `parallel_dispatch`; batch rows never get one in v1. |
| B5-R8 | `processFlow` reads each child's `status`: a `CANCELLED` result is a cancellation, never a completion. |
| B5-R9 | The run list returns every in-flight node, `stepInterruptible` is true only when every in-flight node can stop, and `settleAbandonedRuns` checks every in-flight workflow. |
| B5-R10 | The rollout does not widen past internal companies until B5-c is settled and B5b ships. |
| B5-R11 | B5 keeps no per-replica state: every limit and decision lives in workflow state, the run input or Redis, so it behaves the same with any number of worker and back replicas, and a worker scale-in during a parallel run drains instead of cancelling (`WorkerShutdown`, B5-R5). |
| B5-R12 | A flow in which a non-chat Small Memory (`fluxObject`) is fed across a back edge of a cycle runs sequentially, because a reader dispatched beside that producer would miss its entry (A14-D3, added 2026-11-23). Count such flows in production before shipping. |

## Design

### The loop (`processFlow`, on B6's version)

1. `parallel = patched('b5-parallel') && (input.maxInFlight ?? 1) > 1`. When it is false, the current
   loop runs unchanged.
2. Fill the in-flight set by calling `nextReady(state)` until it holds `maxInFlight` nodes or returns
   nothing. Wait for the first node to settle (`Promise.race`, as `process-batch.workflow.ts:268-290`
   does), apply its outcome, and fill again. No node is `scheduled` without being in flight.
3. Each node settles as one `Outcome`: `ok`, `failed` or `cancelled` (B5-R8). State changes (`seq`,
   counters, `markCompleted`, `completeCondition`) are applied in one synchronous step after each
   settle, which keeps the single-threaded workflow deterministic.
4. `maxInFlight?: number` is a new optional field of `ProcessFlowInput` and `ChildFlowInput`. It
   survives continue-as-new.

### Per-type rules

- **`arrayNode`.** Iterations write the current item onto the array's single row and body inputs read
  the latest output per node, so iterations cannot overlap. When the array is dispatched, its body ids
  are added to `state.scheduled`; the array is held back while any body id is in flight. When the loop
  ends, B6's code marks every body id completed or dead (develop :447-451). An outer array that holds
  an inner array runs it inside its own loop, so nested reservation cannot deadlock.
- **`conditionNode`.** A dead-branch target has the condition as a gating predecessor, so it cannot be
  in flight before the condition completes. Its `systemLimitExceeded` throw is a genuine failure.
- **`fluxObject` (Small Memory, A14).** It never runs; `processFlow` skips it like a `source` node. Its readers depend on its producers through ordinary edges, so they wait for them. The exception is a producer fed across a back edge of a cycle: B5-R12 keeps that flow sequential.
- **`fluxBox` / `libraryNode`.** Each call has its own `childRunId`, seed and workflow id. `childFlow`
  passes the same `maxInFlight`.

### Failure and continue-as-new

1. **Fail-fast** (flag on, failure is not `WorkerShutdown`): call `dispatchScope.cancel()` on the scope
   that holds every in-flight leaf node (`fluxBox`/`libraryNode` children run outside it and are awaited), pass the reason to `persistCancelledNodeActivity`, then wait for all
   of them to settle.
2. **Drain** (flag off, or a `WorkerShutdown`): stop filling, wait for every in-flight node, apply each
   outcome, then fail the run.
3. **Continue-as-new:** when the segment limit (`NODE_EXEC_LIMIT_PER_RUN_SEGMENT`, the node count per
   history segment) or `continueAsNewSuggested` trips, drain the same way, then serialize. A failure
   during the drain wins over the continuation.
4. `lastExecutedNodeId` is the failing node on failure and the last settled node otherwise.

### The back decision

`resolveParallelDispatch({ nodes, userId, companyId }): number | undefined` in `engine-selector.ts`
returns `clamp(floor(value ?? 2), 1, 4)` when `canUseWorkflowForFlow(nodes)` and
`isEnabledFor('parallel_dispatch', { userId, companyId })` are true, else `undefined`. The `apiV2` start
arguments (`flux.service.ts:2294-2312`) and `PrepareScheduledRunResponseDto` carry it; the batch
prepare result does not. Two seed migrations create `parallel_dispatch` (off, value 2) and
`parallel_fail_fast` (on). The worker needs `parallel_fail_fast` per run, so the back passes it as
`failFast?: boolean` next to `maxInFlight`. Deploy the worker first: it ignores absent fields.

### Scale-out readiness

The plan is to enable autoscaling for the worker, the back and the MCP server after B5; **the Temporal
server stays at 1 replica** (decided 2026-11-19). Today, in production (read-only, 2026-11-19): the
worker runs 1 replica with no autoscaling; the back (`api-service-prod`) autoscales from 1 to 3, sized
by S11; `mcp-prod` autoscales from 1 to 4; the Temporal server (`temporal-prod-service`) runs 1 replica
with 1 vCPU and 2 GB. Over the 14 days to 2026-11-19, hourly averages: Temporal CPU 3.9% on average with
peaks of 72.9%, memory at most 11.5%; worker CPU 4.1% on average with peaks of 100%, memory at most
71.6%.

| Concern | Why B5 is safe, or what must happen first |
|---|---|
| Where the cap lives | `maxInFlight` and `failFast` travel in the run input and live in workflow state; any worker replica that picks up the workflow task applies them. Nothing is counted per replica. |
| Back decision | `resolveParallelDispatch` is a pure function of the flow and the flag; any back replica returns the same value. |
| Events | More nodes in flight means more run events. E3 and E3b deliver each event once across back replicas. |
| Scale-in | A scale-in stops a worker: activities get 100 s, then `WorkerShutdown` and one retry (A9c). B5-R5 drains on `WorkerShutdown`, so a scale-in never cancels healthy siblings. Autoscaling makes this path frequent, which is why the exception is a requirement. |
| DB connections | Each worker replica opens a pool of 10 (S2). Before raising the worker maximum, check `max_connections` against back replicas (S11) plus worker replicas × 10. |
| Provider limits | More replicas raise the fleet's real concurrency, so B5b ships before the worker maximum goes above 1. |
| Temporal server | It stays at 1 replica: the container runs every Temporal service in one process (the `auto-setup` style image, configured by `DB`, `POSTGRES_SEEDS`, `DEFAULT_NAMESPACE`), so adding replicas would need the services split, membership between tasks and a history-shard count that is fixed when the cluster is created. Its CPU already peaks at 72.9% sequentially. A larger task (vertical sizing) is the capacity option. |
| Temporal database | **The real ceiling.** `enhancedai-temporal-db-prod` is a `db.t3.micro` (1 GB RAM, burstable CPU). Over the 14 days to 2026-11-19: CPU 7.4% on average, peak 63.8%; CPU credit balance fell to 40 of 288; free memory averaged about 100 MB and fell to about 44 MB; up to 57 connections. Every node is a child workflow plus activities, so parallel dispatch multiplies the history writes per second; if the credits run out, the database is throttled to its baseline and every run on the platform slows. **Resize it before the internal rollout** (the user's AWS change) and watch CPU, credits and free memory during the rollout; lower `parallel_dispatch`'s value or pause the rollout if they degrade. |
| Cap ceiling | The ceiling of 4 is a code constant sized for 1 replica. Raise it with the scale-out, in the same release that raises the worker maximum. |

### Run list

Replace the four `MAX(...)` columns with arrays (`inFlightNodeIds`, `inFlightExecIds`,
`inFlightWorkflowIds`), compute `stepInterruptible` with `bool_and`, and check every in-flight workflow
in `settleAbandonedRuns`. `FlowRunDto` gains the three array fields; the single fields keep the first
element until the front moves. This is additive and is not a failure DTO.

## Tasks

| Id | What | Repo | Depends on | Done when |
|---|---|---|---|---|
| B5-T1 | Branch `feat/868m0vmkd` from `origin/feat/868m0vmvr` in worker and back | worker, back | — | Done 2026-11-23: from B6's tip (worker `34255f2`, back `2b90438b`), then `origin/main` merged in, because B6 was 34 (worker) and 77 (back) commits behind and lacked A9b's `processFlow` patch and histories. Worker merge `8765566`; its one conflict (`process-flow.workflow.ts`) resolves identically to `origin/develop`. Back merge `b179abdc`, no conflicts. |
| B5-T2 | Record replay histories on B6 before any change | worker | T1 | Histories committed |
| B5-T3 | Loop rewrite: `patched('b5-parallel')`, `nextReady` until the cap, `Outcome` with `cancelled` | worker | T2 | B5-R1, B5-R2, B5-R8 |
| B5-T4 | Per-type rules: array hold, condition, sub-flow cap pass-through | worker | T3 | B5-R3, B5-R4 |
| B5-T5 | Fail-fast with reason and the `WorkerShutdown` exception; drain path; continue-as-new drain | worker | T3 | B5-R5, B5-R6 |
| B5-T6 | `resolveParallelDispatch`, both flags and seed migrations, `maxInFlight`/`failFast` in the `apiV2` and schedule starts | back | T1 | B5-R7 |
| B5-T7 | Run list over the in-flight set | back | T1 | B5-R9 |
| B5-T8 | Local tests with negative controls, then `/simplify`, `/code-review`, `/security-review` (the workspace review commands) | worker, back | T3-T7 | Every local check green after being seen to fail |
| B5-T9 | Dev validation (including two worker replicas) and latency report, including the reference use case | dev | T8 | Every dev check recorded here |

### Implementation record (2026-11-23)

T2 to T8 are done on `feat/868m0vmkd`: worker `ba1a6af` (15 commits after the base merge), back `353b0c5f`
(7 commits). Every new test was seen failing before it passed.

- **T2.** Five histories recorded on B6 plus main (`process-flow-b5-fanout`, `-condition`, `-array`,
  `-subflow`, `-failure`), with `scripts/b5-replay-histories/record-b5.cjs`. A sixth,
  `process-flow-b5-parallel-fanout`, is recorded with `maxInFlight: 2` and carries the patch marker. The
  replay spec replays all 8 `process-flow-*` histories and fails when a file on disk is missing from its
  list. Breaking determinism makes all 8 fail.
- **T3 to T5.** The loop body is split into one function per node type that returns an outcome, with the
  command order unchanged; the parallel path (`runParallel`) is added next to it. 30 parallel tests.
  Measured overlap in an 8-node fan-out: 3 at `maxInFlight` 3, 4 at 9 (ceiling), 1 at 1.9.
- **T6, T7.** `resolveParallelDispatchArgs`, one seed migration
  (`1795300000000-SeedParallelDispatchFlags`), and the run list. The run-list query measured at parity
  with the old one on a local 1-million-row copy (warm runs 656-1005 ms against 743-1072 ms); not
  measured on a production-sized copy.
- **B5-R12 (2026-11-24).** Back `cf96a38` on `feat/868m0vmkd`: 10 tests in `engine-selector.small-memory.spec.ts` (both edge orders, chat exempt, no-cycle and no-memory cases, the decision wiring). Negative controls seen failing: an into-only rule (the memory→reader order fails), the rule unwired from the decision, and chat memory treated as non-chat (3 tests fail). Until A14 opens B4's gate for `fluxObject`, a flow with a Small Memory never reaches this rule. Not on `develop` yet.
- **T8.** `/simplify` (16 fixes), `/code-review` (6 fixes, listed below), `/security-review` (no
  finding; the one candidate, stored XSS through the cancel reason on the staff run log page, was
  dropped: front `main` and `develop` sanitize that page since `2eab2787a`, and customer text already
  reached it before B5).

Where the code departs from this spec, and why:

| Spec text | What the code does | Why |
|---|---|---|
| B5-R8 for every new run | A `CANCELLED` child is a cancellation only on the parallel path. `patched('b5-parallel')` is called only when `maxInFlight` > 1, so a run with the flag off records no marker. | B5-R1: with the flag off nothing may change. On the sequential path a cancelled child still counts as completed, as today. |
| The two array rules in Per-type rules | Also `isHeldByArray`: a node in the body of an array that has not settled is never dispatched on its own. | B6 takes the body as a slice of `planOrder`, so a later body node or an inner array can be ready before the array. Without the extra rule B5-R3 fails. |
| `childFlow` passes the same cap | It also passes a continue-as-new hook, on every run. | B6 bug: a continue-as-new inside `childFlow` restarted it with a `processFlow` input and failed (`loadRunSeed(undefined)`). The command type stays `childFlow`, so replay is unaffected. |
| `WorkerShutdown` detection | A leaf walks the cause chain for `type: "WorkerShutdown"`; a sub-flow carries `workerShutdown` in `ChildFlowResult.nodeFailure`; `processFlow` returns it next to `nodeFailure`. | Comparing the user message would turn a drain into a cancel after a copy edit. `nodeFailure` keeps its shape, so the payloads sent to the back do not change. |
| The cancel reason on the cancelled node | Written only to the `node_executions` row and to the cancelled `node_finished` event's `error`. | Code review: the first version also merged it into `flows_nodes.data`, the flow's own definition. `RunEventErrorDto.userMessage` has no length limit; a 5000-character label is tested. |
| Fail-fast after a drain started | Only the first failure can cancel; once a `WorkerShutdown` or `failFast: false` started a drain, a later failure cannot. | Code review: a later ordinary failure cancelled the siblings the drain was meant to let finish. |
| Emits and opens in the cancellable scope | In parallel mode every open and every `node_started`/`node_finished` runs non-cancellable. | Code review: a sibling that finished after the cancel was recorded cancelled, and a condition or array cancelled mid-open left a row that looked in flight forever. |
| `resolveParallelDispatch(...): number \| undefined` | `resolveParallelDispatchArgs(flags, target): Promise<{ maxInFlight?, failFast? }>`; the two flags are read together. | The flag reads are asynchronous. |
| Allowlist target: the user's company | The company that owns the flow (`companyIdOfFlow`, folder space company, then the folder's company-user company), read from the seed query already made. | Code review: with the caller's selected company, a staff user on an internal company would turn on parallel dispatch for a customer's flow. A flow in a personal folder has no company and gets parallel dispatch only through a USER allowlist row. |
| Run list: three arrays, single fields keep the first element | `FlowRunDto.inFlightSteps: { nodeId, execId, workflowId }[]` from one `json_agg`; `stepInterruptible` is derived from it; `settleAbandonedRuns` describes the run workflow once when the run has one. | Three separate aggregates rely on an order Postgres does not promise. `FlowRunDto` never had single fields; the front reads only `isStepInterruptible`. |
| Two seed migrations | One migration seeds both flags. | Matches the Files table. |
| B5-R12: a producer fed across a back edge | `hasSmallMemoryOnBackEdge` (`engine-selector.ts`) matches a back edge into **or out of** a non-chat memory; `resolveParallelDispatchArgs` returns no `maxInFlight` for such a flow, in the `apiV2` and schedule starts. Back edges come from `buildSchedulerState`: a dependency edge between two reachable nodes that is missing from `forwardDeps`. Chat memory (`data.chat === true`, as `flux.service.ts` reads it) is exempt. | Which edge of a cycle becomes the back edge depends on the DFS order of the edges, so a producer→memory-only rule missed the same cycle when the edges came in another order (tested both ways). A false match only costs speed: the flow runs sequentially. |

Constraints found on the way:

- **Rollout stage "everyone" needs code.** `isEnabledFor` returns true only when an allowlist row matches,
  so turning `parallel_dispatch` on globally enables nobody. The global stage needs a second flag read
  with `isEnabled` (for example `parallel_dispatch_global`). `scheduleId` is not passed either, so a
  SCHEDULE allowlist row has no effect.
- **A future "stop step" button.** In a parallel run, any cancelled node stops dispatching and ends the
  run cancelled. Today no user action cancels one step without the run (the run stop cancels the parent
  workflow; the stalled-run cleanup only acts on stalled runs), so this is correct; a per-step stop
  would have to treat a step cancel as a settled node.
- **Pre-existing failures, not B5's.** Worker: 5 tests in `child-flow.workflow.spec.ts` and
  `process-flow.child.workflow.spec.ts` fail on B6's own tip (`34255f2`). Back:
  `workflow-seed-run-key.integration.spec.ts` (2 tests, the mock lacks `resolveExecutionHistoryId`)
  fails on the B5 base `b179abdc`.
- **Dev integration.** `develop` carries hundreds of commits of other tasks (worker 337, back 546), and
  `main` and `develop` diverge in the back, so B5 reaches `develop` by cherry-picking its own commits,
  not by merging the branch.

## Verification

### Local

Workflow tests run in `TestWorkflowEnvironment.createLocal()` with the stubs in
`worker/src/modules/temporal/workflows/__test-stubs__/`. T2 records the histories the same way, in the
`process-flow.replay.spec.ts` harness, for four fixture flows: a fan-out of 4 stubs, one with an
`arrayNode`, one with a `conditionNode`, one with a `fluxBox`. The segment limit becomes an optional
test-only input field, `segmentNodeLimit`.

1. **Determinism (R1).** The T2 histories replay on B5. Negative control: remove `patched('b5-parallel')`
   and watch a nondeterminism error.
2. **Cap (R2).** A fan-out of 8 slow stubs with `maxInFlight` 3 never has more than 3 in flight.
   Negative control: drop the cap check.
3. **Array hold (R3).** A body node that is also independently ready never runs outside the loop; two
   overlapping arrays run in series; two disjoint arrays run together. Negative control: skip the hold.
4. **Control flow (R4).** A dead branch is never dispatched; a sub-flow runs with the parent's cap; a
   `continueAsNew` inside `childFlow` resumes as `childFlow`.
5. **Fail-fast (R5).** A failing stub next to a slow text-generator stub: the slow one ends cancelled
   with the reason, and the run names the failing node. The same with a `WorkerShutdown` failure: the
   slow one completes. The same with `failFast` false: the slow one completes. A failing stub next to a running sub-flow: the sub-flow completes, then the run
   fails. Two simultaneous
   failures: the lower dispatch index names the run. Negative control: skip `dispatchScope.cancel()`.
6. **Child status (R8).** A child that returns `CANCELLED` is not marked completed. Negative control:
   treat every resolved child as completed.
7. **Continue-as-new drain (R6).** Trip `segmentNodeLimit` with slow stubs in flight: no node stays
   `scheduled`. Negative control: serialize without draining and watch the "unprocessed nodes" error
   from `detectUnprocessedNodes`.
8. **Back decision (R7).** Unit tests of `resolveParallelDispatch`: gate false, flag off, flag on, value
   null, 0.5, 9.
9. **Run list (R9).** One in-flight node gives today's result; three give three ids, and
   `stepInterruptible` is false when one of them cannot stop.

### Dev (`engine_in_workflow` on, B6 deployed)

Turn off Data Output delivery and swap recipient inputs on any copy of a customer flow before running
it.

1. **Gate refusal.** A flow with an inline node, or a company outside `parallel_dispatch`, has no
   overlapping `node_executions` intervals. Negative control: set the company's flag target and watch
   overlap appear.
2. **Parallel run.** The same fan-out flow with the company on the allowlist shows overlapping
   intervals, never more than `maxInFlight`.
3. **Schedule and batch.** A Temporal-schedule run of an eligible flow shows overlap; a batch run shows
   none.
4. **Determinism.** A flow with no AI node (math, scripting, condition) runs 10 times with
   `maxInFlight` 2: 10/10 runs have the same node statuses and final outputs.
5. **Events.** With 3 nodes in flight, the builder (`room_status_updated`) and the run list show all 3.
6. **Two worker replicas (B5-R11).** With the dev worker at 2 replicas (the user changes the desired
   count), a parallel run spreads its nodes across both and keeps its cap. Stop one replica during a
   parallel run with `failFast` on: its nodes retry on the other (A9c), no sibling is cancelled, and the
   run completes. Negative control: remove the `WorkerShutdown` exception and watch the siblings
   cancelled.
7. **Latency.** The same fan-out flow and the reference use case, 5 runs each with the flag off and on.
   Wall time per run is min(`createdAt`) to max(`updatedAt`) in `node_executions`, read as `::text`
   (UTC). This settles risk R4 in PLAN §6.

### Dev results (B5-T9, 2026-11-23)

The checks ran on worker `:270` (develop `a589de3`) and back `:2697` (develop `c784b2b9`), with the
dev worker at 2 replicas and `parallel_dispatch` on for one internal company at value 2. The last
attempt of check 6 ran on worker `:271` (develop `bb34e1f`, another task merged on top; the B5 code is
the same). The flows live in the `B5 dev checks` folder of the internal test workspace.

| Check | Verdict | Evidence |
|---|---|---|
| 1. Gate refusal | Pass | Outside the allowlist and with an inline node: concurrency 1, no overlapping intervals. Control (company added): concurrency 2. Company removed again: concurrency 1. |
| 2. Parallel run | Pass | 6 runs of a 4-wide fan-out at `maxInFlight` 2: concurrency 2 in every run, never above. |
| 3. Schedule and batch | Pass (2026-11-24) | Schedule: a Temporal schedule fired the fan-out twice (`runType` `cronjob`): concurrency 2 in both runs, 11.3 s and 12.2 s against 20.9 s sequential. The schedule was deleted and fired no more. Batch: 3 rows of a fan-out in the allowlisted company: concurrency 1 inside every row, 22 to 23 s each; the rows themselves ran at the same time. A batch needs a Variable Input node in the flow, or it fails before the first row. |
| 4. Determinism | Pass | 10 of 10 runs of a no-AI fan-out have the same statuses and outputs; every run overlapped. |
| 5. Events | Pass for the run list; not verified for the builder | At `maxInFlight` 3 the run list returned 3 `inFlightSteps` and `get_run_nodes` showed 3 nodes running. `room_status_updated` was not observed. |
| 6. Two worker replicas | Pass | See below. The negative control was skipped in dev by decision of the task owner; the local negative control stands. |
| 7. Latency | Pass | Fan-out: median 20.9 s off and 11.4 s on (1.84x). Reference shape: an internal flow built like the reference agent flows' first level (2 text generations next to 4 sub-flow calls, each sub-flow a chain of 2 scripts), median 71.5 s off and 37.7 s on (1.90x), concurrency 1 off and 2 on in all 10 runs, no failed node. The safe customer tree that passed review is a chain of width 1, so it was not used. The whole reference chain is mostly width 1, so its end-to-end gain stays about 1.2-1.5x. |

**Check 6 in detail.**

1. **Placement.** Temporal hands each workflow task and each activity task to any replica that polls
   the queue; nothing pins a run to a replica. Concurrent runs ran their `processFlow` on different
   replicas, and the cap of 2 held in every run.
2. **Workflow failover.** With the replica that ran `processFlow` stopped mid-run, the workflow
   continued on the other replica with no nondeterminism error. `patched('b5-parallel')` replays on a
   replica that did not start the run.
3. **`WorkerShutdown` retry.** Two AI text nodes of about 6 minutes each ran in parallel with
   `failFast` on, and the replica holding both activities was stopped about 20 s after they started.
   At the end of the 100 s grace both activities failed with `WorkerShutdown`, retried on a surviving
   replica, and succeeded. Neither node was cancelled, the join ran, and the run completed.

To repeat check 6, use a node that runs for longer than the 100 s grace without reaching outside the
platform. A `scripting` node cannot do it: the code executor stops a script after 30 s. An AI text
node with a long output works.

### Production (after B6 ships and B4 has soaked)

1. **Measure before refusing** (PLAN §3.3.2): classify every production flow as eligible or ineligible,
   name the node type that disqualifies it, and count the flows with a ready level wider than 1. A flow
   the gate refuses although every node type runs on the worker must not exist. The owner of the
   rollout runs the query in DBeaver.
2. **B5-c count** before widening past internal companies. The count (2026-11-24) reads the graph a run loads (`resolveExecutionHistoryId`) and reports, per flow: runs on the worker; an external writer (`pushData`, `sqlQuerier`, `fileSave`, `hubSpotCRM`, `thirdPartyIntegration`, `mcpNode`, `apiCaller`, `commandContentNode`) with another external read or write and no dependency path between them; a writer or Data Output beside an independent executable node; and a non-chat Small Memory on a cycle (B5-R12). It counts every wired node as reached, so it is an upper bound. On dev it never missed a flow that `buildSchedulerState` and `hasSmallMemoryOnBackEdge` flag (2,432 worker flows: 13 vs 10 independent pairs, 138 vs 82 failure cases, 8 vs 7 R12 flows), and a broken copy of it was caught. Server time on dev: 0.6 s.
3. **Docs.** Merge enhancedai-com/docs#66 (the parallel dispatch page) in the same release as the B5 back and worker PRs.

## Done when

Eligible flows of allowlisted companies run their ready nodes concurrently up to `maxInFlight`;
everything else runs as today; every local and dev check passed after being seen to fail; latency is
measured on the fan-out flow and the reference use case.

## Estimate

Min 43 h, average 67 h, max 100 h (2026-11-19, after the EGM review):

| Part | Min | Avg | Max |
|---|---|---|---|
| Loop rewrite, per-type rules, fail-fast and drain, patch | 16 | 24 | 36 |
| Worker tests, replay histories, negative controls | 12 | 18 | 26 |
| Back decision, flags, schedule plumbing, run list | 7 | 12 | 18 |
| Dev validation, latency report, reviews | 8 | 13 | 20 |

B5b is estimated separately (about 18 / 28 / 40 h).

**Calibrated to delivery with Claude (2026-11-19): 23 / 45 / 98 h.** Measured on the 12 Wave 5 tasks
delivered with Claude Code (A11, A13, S6b, S9, E3b, S8b, S10, S11, S4b, B7b, E4b, A9b): ClickUp
`date_active` to `date_done` in working days, divided by the estimate at 8 h a day, gives p25 0.42,
median 0.60, p75 0.98 (S6b 2.00 and S10 2.17 are the slow tail; E5b and S8c are left out because a
task under one day still counts one day). The code parts take those factors; dev validation does not,
because its runs are wall-clock (reference flows take up to 35 minutes in dev, dev runs only on office
hours) and each dev deploy is one Actions cycle:

| Part | Min (× 0.42) | Avg (× 0.60) | Max (× 0.98) |
|---|---|---|---|
| Code, tests, back (35 / 54 / 80 h) | 15 | 32 | 78 |
| Dev validation, latency report, reviews (× 1.0) | 8 | 13 | 20 |
| **Total** | **23** | **45** | **98** |

The maximum does not shrink: it is the B6 rebase and replay determinism, which Claude does not speed
up. The closest analogue, B4 (the first loop in a Temporal workflow), ran at 1.07. B5b on the same
factors: about 8 / 17 / 39 h.

## Open risks

- **Tenant fairness with 1 worker replica.** One run holds up to `maxInFlight` of the platform's 10
  slots (each sub-flow level asks for up to `maxInFlight` more; worst case `m^(depth+1)` = 16 slot
  requests at m = 2 and depth 3, which queue for the 10 slots and do not fail). Mitigation: default 2,
  batch sequential, internal allowlist. Trigger to revisit: queue wait (`schedule_to_start` latency) measured in
  the internal rollout. Scaling the worker out (see [Scale-out readiness](#scale-out-readiness)) is the
  long-term fix.
- **Fail-fast and side effects (accepted).** A cancelled `TRY_CANCEL` sibling — integrations, `pushData`,
  `sqlQuerier`, `mcp`, `largeMemory`, `fileSave` — finishes its write and is recorded cancelled; a
  re-run repeats the write. `imageGenerator` and `mcp` may charge after the cancel; voice,
  transcription and web search are paid to the provider but not charged. Mitigation: the cancel reason
  on the Logs page, and `parallel_fail_fast` to switch to drain.
- **Workflow CPU.** The input projection runs inside the workflow (`process-flow.workflow.ts:209`), so
  a wide ready set adds workflow-task CPU and history, and continue-as-new comes sooner. The B3b
  performance items are tracked in their own card.
- **Batch and schedule without the gate** (current state item 3) may already fail eligible-looking
  batches in production; tracked separately.

## Follow-up: B5b — per-provider budget

Before the worker scales past 1 replica or the rollout reaches customers. Scope: a pure
`resolveProviderKey(nodeType, nodeData)` with a decision per `NodeType` (inputs from
`getNodeInfoActivity`, extended to return `system_ai_models.aiCompany`); the `TenantConcurrencyLedger`
Lua script exported into `back/src/shared/concurrency/lease-admit.ts`, added to
`back/scripts/sync-ported-engine.ts` and ported to the worker; acquire and release activities called
from `processSingleNode` behind `patched('b5-provider-budget')`; lease renewal by a workflow timer, one
TTL per key; caps from `provider_cap_<key>` flags. Each cap comes from the provider account's real
limit.

## Files

| Repo | Path | Create / Modify | Change |
|---|---|---|---|
| worker | `src/modules/temporal/workflows/process-flow.workflow.ts` | M | Parallel loop, outcomes, fail-fast and drain |
| worker | the file that defines `ProcessFlowInput` (found in T1) | M | `maxInFlight`, `failFast`, `segmentNodeLimit` |
| worker | `src/modules/temporal/workflows/child-flow.types.ts`, `child-flow.workflow.ts` | M | Same `maxInFlight`, `failFast` |
| worker | `src/modules/temporal/workflows/run-scheduled-flow.workflow.ts` | M | Pass `maxInFlight` and `failFast` |
| worker | `src/modules/temporal/activities/activities.service.ts` | M | Cancel reason in `persistCancelledNodeActivity` |
| worker | `src/modules/temporal/workflows/replay-histories/`, `process-flow.replay.spec.ts`, `process-flow.parallel.spec.ts` | C/M | Histories and local checks |
| back | `src/app-api/flux/engine-selector.ts`, `engine-selector.spec.ts` | M | `resolveParallelDispatch` and tests |
| back | `src/app-api/flux/flux.service.ts` | M | `apiV2` start args, `prepareScheduledRun` |
| back | `src/shared/responses/scheduled-run.response.dto.ts` | M | `maxInFlight`, `failFast` |
| back | `src/database/migrations/<timestamp>-SeedParallelDispatchFlags.ts` | C | Both flags, following `1789600000000-SeedTenantConcurrencyFlag.ts` |
| back | `src/app-api/executions_logs/execution_logs.service.ts` and `FlowRunDto` | M | Run list over the in-flight set |
