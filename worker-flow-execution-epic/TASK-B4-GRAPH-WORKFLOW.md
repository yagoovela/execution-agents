# B4 — Move the DAG loop into a Temporal workflow, sequential first

**Goal:** the worker owns the execution sequence. **This task ships with no parallelism at all.**

**Depends on:** B2, B3. **Blocks:** B5, B6.

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
- The blocking wait to be removed: `await handle.result()` at `back/src/jobs/apiV2Job/apiV2Job.processor.ts` (writes `flow_execution_status` today — B4 and E1 decide who writes it after) · `back/src/app-api/flux/flux.service.ts`.
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

**In.** A writer for `flow_execution_status` (PR #1902, 2026-08-21 — read by `GET /flux/executions/:id`).
Today the api-v2 processor writes it from inside the loop; once the loop is a workflow, decide
whether the workflow reports status through a callback or E1's collector becomes the writer, and
state it in the PR. A table nobody writes is a status endpoint that lies.

**In.** A flag selecting engine-in-back vs engine-in-workflow, per flow, defaulting to back.

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

## Files

`worker/src/modules/temporal/workflows/process-agent.workflow.ts` · new flow workflow ·
`worker/src/modules/temporal/{activities,worker.service.ts,workflows/configs.ts}` ·
`back/src/jobs/apiV2Job/apiV2Job.processor.ts` (writes `flow_execution_status` today — B4 and E1 decide who writes it after) · `back/src/app-api/flux/flux.service.ts` (`await handle.result()` in `processNodeViaTemporal`; the `while (scheduledId !== null)` loop; the unprocessed-node warning) · the scheduler module from B2
