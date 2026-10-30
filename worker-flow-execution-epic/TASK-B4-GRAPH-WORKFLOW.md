# B4 — Move the DAG loop into a Temporal workflow, sequential first

**Goal:** the worker owns the execution sequence. **This task ships with no parallelism at all.**

**Depends on:** B2, B3, B3b. **Blocks:** B5, B6.

## Why sequential first is not caution, it is a requirement

Two changes are hiding in "move the graph": relocating the loop, and letting it dispatch more than
one node. Shipped together, a rollback cannot tell you which one broke the run. Shipped apart,
each is a one-line flag.

Sequential is also nearly free to express: `allReady()` returning a single id **is** today's
behaviour. B4 builds the batch-capable machinery and configures it to a batch size of one.

## What exists

- The graph is already correct and already portable — `scheduler.ts`, extracted in B2.
- The parallel loop was already written and commented out:
  `worker/src/modules/temporal/workflows/process-agent.workflow.ts`, carrying in-degree per node,
  a `readyToRun` filter and `Promise.all` over the batch, under the line *"It will not be used for
  the time being; the logic has already been removed."* Read it before writing a new one.
- The blocking wait to be removed: `await handle.result()` at `back/src/jobs/apiV2Job/apiV2Job.processor.ts` (writes `flow_execution_status` today; E1 writes it after — see E1's contract with B4) · `back/src/app-api/flux/flux.service.ts`.
  Today every migrated node is a synchronous round trip (analysis §9.2.2) — this is the task that
  pays that back.

## Scope

**In.** A workflow that owns `SchedulerState`, calls `allReady()`, dispatches, and applies
`markCompleted` / `markDead` / `completeCondition` as results arrive. `markCompleted` and
`markDead` are set-based and already tolerate out-of-order completion, which is what a batch
produces — no change needed there.

**In.** `allReady(state): string[]` alongside `nextReady`, draining every eligible id and marking
each `scheduled`. Keep `nextReady` while the backend loop exists — it is that loop's primitive, and
C2 retires it with the loop. The MCP write service (`mcp-write.service.ts`) uses the scheduler too,
but only `buildSchedulerState` and `classifyEdge`, so it is unaffected either way. Before writing
`allReady()`, check whether the Temporal SDK offers a primitive for ready-set dispatch (B2 carries
the same note); decide during development — D16 is unchanged whichever way it goes.

**In.** The back's role shrinks to: start the flow workflow, serve the callbacks it already owns
(billing, model access, S3, file generation), and read the result. It stops being the loop.

**In.** The run events that E1 consumes. Settled in
[E1's contract with B4](./TASK-E1-RUN-OBSERVABILITY.md#contract-with-b4): the workflow emits
ordered events through an activity, and E1's back side writes `space_run_logs`,
`flow_execution_status` (PR #1902, read by `GET /flux/executions/:id`) and the run totals. B4 does
not write any of them. Validate the branch with that task's checklist before the PR.

**In.** A flag selecting engine-in-back vs engine-in-workflow, defaulting to back. **Corrected
2026-10-23:** the flag is global by design (`isEnabled`, not per flow); which flows it routes is
decided by the eligibility gate. In production it stays off until A11 and A13 ship and the worker
that registers `processFlow` is deployed (DELIVERY-PLAN Wave 4 and Wave 5).

**In — workflow history is a storage medium, and it is bounded.** A Temporal workflow accumulates
history events, and both the event count and the total size are capped. The worker uses
**no `continueAsNew`** anywhere today. One workflow owning an entire flow run therefore grows with
every activity scheduled and completed and every value passed — and it will be terminated by the
platform on exactly the largest, most valuable customer runs (review §4.1).

Two requirements follow, and neither is optional:
- **`continueAsNew` at a boundary** — iteration count or node count. Pick one, state the number,
  and prove it by running a graph past it.
- **State by reference, never by value.** The id-based transport from B1 already makes this
  possible: the workflow carries ids, and the payloads stay in Postgres and S3. Passing a resolved
  input through workflow state would put node output into the history.

**B4-a — the boundary, with the infrastructure limits (open, proposal 2026-10-23).**

Our Temporal is self-hosted: `temporalio/auto-setup:1.22.0` on ECS (1 task, 1 vCPU, 2 GB) over its
own RDS Postgres 14 on `db.t3.micro`. Dev and staging share one server and the `default` namespace.
No dynamic config is set, so every 1.22 default applies:

| Limit | Value | What happens |
|---|---|---|
| `limit.historyCount.suggestContinueAsNew` | 4,096 events | `continueAsNewSuggested` turns true |
| `limit.historyCount.warn` / `.error` | 10,240 / 51,200 events | A warning; at the error limit the run is terminated |
| `limit.historySize.suggestContinueAsNew` | 4 MB | `continueAsNewSuggested` turns true |
| `limit.historySize.warn` / `.error` | 10 MB / 50 MB | A warning; at the error limit the run is terminated |
| `limit.blobSize.warn` / `.error` | 512 KB / 2 MB per payload | At 2 MB, the activity result or input is refused and the run cannot go on |
| Pending activities, child workflows, signals | 2,000 each | Not a constraint at batch size one |

What the branch does today (worker `feat/wave-4-b4` `fd9f5387`):

1. `process-flow.workflow.ts` sets `NODE_EXEC_LIMIT_PER_RUN_SEGMENT = 500` and also continues when
   `workflowInfo().continueAsNewSuggested` is true.
2. Each node costs about 21–27 history events in the parent: two activities, one child workflow,
   one more activity and the workflow tasks between them. This is an estimate; no `processFlow`
   history has been recorded yet.
3. At 27 events a node, the server's suggestion fires at about 150 nodes, so the coded 500 is never
   reached. At 500 the history would hold about 13,500 events, past the warn line.
4. The boundary test (`process-flow.continue-as-new.spec.ts`) is a stub with `expect(true)`.
5. `carryNodeExecCount: 0` on continue resets the count, so `nodeExecCount` reports only the last
   segment.

Production size: the largest run in the S4 re-measure (1,218 runs, 2026-09-23) had 116 node
executions; p99 was 89. At 27 events a node that is about 3,130 events, inside one segment.

**Proposal.** Set the boundary at **150 node executions**: 1.3 times the largest production run, the
same margin S4 uses. Keep `continueAsNewSuggested` as the size backstop. Fix the count carry, and
replace the stub with a run past 150.

**The larger risk is payload size, not event count.** `loadRunSeedActivity` returns the full
`node.data` of every node, and `openNodeExecutionActivity` takes a node's full `nodeData` as input.
Both are written to history. A seed over 2 MB, or one node whose data is over 2 MB, stops the run at
`limit.blobSize.error`, whatever the boundary. Production output bodies reach 9.2 MB (A9 Q8). Pass
the seed and the node data by reference (`seedSnapshotId`), as the requirement above already says.
Before the flag goes on in production, measure the largest seed (the sum of `flows_nodes.data` per
flow) and the largest single `node.data`.

Not verified: the real events per node, the server's gRPC message size limit, and the namespace
retention.

**Out.** Batch size above one. **Out.** Control flow and sub-flows — B6. **Out.** Deleting the
back's loop — C1/C2, after this has soaked.

## Verification

- **Negative control (required).** Break `markCompleted` so a completed node is not recorded, and
  confirm the workflow detects the stall rather than hanging until the Temporal timeout. A graph
  engine whose failure mode is "hangs for 30 minutes" is not shippable; prove it fails fast.
- **Order equivalence.** For a corpus of stored flows, assert the workflow executes nodes in the
  same order the back's loop does, node for node. With batch size one this must be exact — any
  divergence is a defect in the port, and this is the last moment it is cheap to see.
- **Unprocessed-node detection** must survive the move. The back warns today when a node ends
  outside `completed` or `dead` (`flux.service.ts`); the workflow needs the equivalent,
  because a silently skipped node is the characteristic failure of a scheduler port.
- Cancellation must still work end to end, including the in-flight flag
  (`flux/node-cancel-watch.ts`).
- **History growth, measured.** Run the widest and the longest real flow available and record the
  event count and history size at completion, against the platform's limits. Then run one past the
  `continueAsNew` boundary and confirm it continues rather than being terminated. A graph engine
  whose ceiling is unknown has no ceiling.

## Done when

A flow runs start to finish under the workflow, in identical order, behind a flag defaulting off;
the back's loop is untouched and still selectable.

## Carried over from B3b (validate first)

B3b left these in the worker's input projection (`worker/src/modules/nodes/shared/project-node-input.ts`).
Before you fix one, check that it still applies to the graph workflow; if it does not, record why
and close it here.

1. **A source with no seed row is dropped without an error.** `RunData.nodes` keeps only the sources
   it finds in the run's outputs or in `run_seed_nodes`. A node added to the flow after the run
   started has neither, so its edge projects nothing. Decide whether the graph workflow can see such
   a node, and if it can, fail the target the way a completed source with no output does.
2. **A cycle of nodes that have not run yet.** `RunData.fromSeed` skips an upstream node that is
   already being loaded from the seed, so inside such a cycle a node is projected without that
   source. `conditionNode` loops are not gated, so they reach the worker today. Compare against the
   back on a `conditionNode` loop. Today the back's scheduler drops back edges, so a cycle meets the
   projection only on its first pass, where dev run `842aeff8` matched (B3b, "Left out, and where
   it goes"). Re-check it once the graph workflow runs a loop more than once.
3. **The starter edges are dropped by id.** The worker drops edges whose source is
   `starterSourceId`. The product's rule for which edges carry data is `isDependencyEdge`
   (`flux/scheduler.ts`), which also leaves out `GLOBAL_HANDLE` sources and edges without a
   `targetHandle`. Use the product's rule if the graph workflow reads edges the same way.
4. **Small cleanups, when you touch the code.** `RunInputResolution.seedSnapshotId` can read
   `snapshotIds[0]`; `backOnlyProjectionNodes(...).length === 0` can be a `some` check.

## Files

`worker/src/modules/temporal/workflows/process-agent.workflow.ts` · new flow workflow ·
`worker/src/modules/temporal/{activities,worker.service.ts,workflows/configs.ts}` ·
`back/src/jobs/apiV2Job/apiV2Job.processor.ts` (writes `flow_execution_status` today; E1 writes it after — see E1's contract with B4) · `back/src/app-api/flux/flux.service.ts` (`await handle.result()` in `processNodeViaTemporal`; the `while (scheduledId !== null)` loop; the unprocessed-node warning) · the scheduler module from B2
