# B3b — Edge projection in the worker

**Goal:** the worker builds a node's `*Data` arrays from data stored in the database, so that no
node needs a round trip through the back to become runnable.

**Depends on:** B2, B3. **Blocks:** B4. **Split out of B3 on 2026-10-09** — see
[Why this is its own task](#why-this-is-its-own-task). **Revised against the code on 2026-10-13** —
see [Corrections on 2026-10-13](#corrections-on-2026-10-13).

## What it is

When a node completes, the back walks the edges leaving it and, for each one, decides **which field
of the source node the edge's handle stands for**, then writes a `{ id, label, text }` entry into the
target's `*Data` array (`addConnectToNodes` in `back/src/app-api/folw/contants.ts`, which calls
`modifyData`, `givingDataToNode` and `getOutputByType` in `back/src/app-api/folw/helpers/helpers.ts`).
The projection spans `helpers.ts` lines 20 to 1959, about 1,940 lines; `modifyData` alone is about
760. Examples from `origin/main`:

| Source and handle | What becomes `text` |
|---|---|
| `scripting` · `output` | `data.result` |
| `scripting` · `console` | `data.console`, lines joined with `\n` |
| `commandTextNode` / `outputController` / `reportBuilder` · `fileLink` | `data.fileLink.src`, or `'No Link generated'` |
| `commandTextNode` · `logs` | `data.logs`, or `'No Logs generated'` — broken since 2026-06-09, see [The `logs` handle](#the-logs-handle) |
| `varInputNode` · `outputExtractText` | `data.extractText` |

Around it: `buildHandleEntryIdForWrite` gives the entry an edge identity, suffixed `#N` inside a loop
iteration (read from `loopIterationContext`, an `AsyncLocalStorage`); `reconcileEntries` drops the
entries of edges that are no longer connected.

Callers on both `origin/main` and the B3 branch: 54 calls to `addConnectToNodes` and 5 to `modifyData`
in `flux/flux.service.ts`, plus `givingDataToNode`, `getOutputByType` and `modifyData` inside
`folw/contants.ts`, and `modifyData` in `flux/helpers/resolve-inbound-variables.ts`. Line numbers
shift with every change to `flux.service.ts`, so this spec names functions, not lines.

It is **field selection by handle**, not a content transformation. The only formatting in it is the
console join, the `logs` serialization and the default strings, and those are product behaviour that
must stay byte-identical between the back and the worker.

## Why this is its own task

B3 was first scoped with this left in the back, on the reading that it was a transform. It is not:
it is a pure function of the edge, the source's data and the loop iteration, and it lives in the
back only because the loop and its in-memory node list (`nds`) live there.

- **The data is already in the database.** See [Where the projection's data lives](#where-the-projections-data-lives).
- **B4 needs it gone from the back.** Once the loop is a workflow, the back no longer holds `nds`.
  Leaving the projection there turns it into a back callback per node, which is the round trip B4
  exists to remove.
- **It is too big to ride inside B3.** About 1,940 lines with branches per source type, inside a
  2,337-line `helpers.ts` that is not pure (see [Extraction](#extraction)).

## Where the projection's data lives

The projection uses only data that is saved in the database. A field that is never saved is never
used, on either path.

| What | Where |
|---|---|
| The edges of the run | `flows_nodes_edges` for the run's version: `flow_id`, `target`, and `flow_version_history_id IS NOT DISTINCT FROM` the run's version (`NULL` is the live draft). |
| A source that ran in this run | Its latest `node_executions` row for `(runId, flowId, nodeId)`, field `outputData`. A `__claimRef` payload is resolved before projecting. |
| A source that did not run in this run | Its `flows_nodes.data` for the run's version, passed through `clearRunOutputForSeed`. |

Why this matches the back exactly:

- **Worker sources.** After every worker dispatch the back re-reads `node_executions.outputData` for
  that execution and replaces the node's in-memory data with it. The activity's return value is not
  used. What the back projects is therefore what the row holds.
- **Inline sources.** `recordLegacyNodeSuccess` writes the node's full in-memory data to `outputData`.
- **Sources that did not run.** At run start the back builds `nds` from `flows_nodes` and runs
  `clearRunOutputForSeed` (`flux/node-output-reset.ts`) on every node. It empties the output fields
  and keeps static data, such as a `textBox`'s text. The worker applies the same function, ported
  through B2's sync, to a source that has no row in this run. This is data, not order: deciding which
  node runs, is dead or is ready stays with the back's loop until B4.
- **Fields that are never saved.** For example, the worker never writes `commandTextNode.fileLink`,
  so the back already projects `'No Link generated'` for it, and so does the worker.

**Back-only sources** keep a flow on the back's path (the gate below). Their data is used without
being saved, or it comes from outside the node tables:

- `arrayNode`: the per-iteration index (`completed`), and inline nodes inside its loop body, which
  get no `node_executions` row.
- `conditionNode` loop counter (`currentLoopCounter`), kept in memory.
- `fluxObject` and `nodesBox`: session data read at run start from the session store, and
  `objectCallerData` from the `objects` table.
- `libraryNode` / `fluxBox`: sub-flows.
- `tableProcessor` and `dynamicSettingsNode`: they read fields that no writer stores in `outputData`.
- Target-side accumulation (Small Memory entries with timestamps).

These are control flow and sub-flows, B6's territory. `outputObjectNode` and `globalStarter` are not
source branches of the projection; the earlier list was wrong.

## Run identity

`node_executions` has no run column today: the run id lives only in `metadata->>'runId'` (since
2026-07-24), with no index. `execId` is per execution, not per run, and `sessionId` repeats across
runs. B3 avoided the need: its journal lists only worker dispatches since the last checkpoint, so it
cannot find inline sources or sources dispatched before the checkpoint.

This task adds a `runId` column to `node_executions`:

1. Before choosing the type, check that every stored `metadata->>'runId'` is a UUID. If one is not,
   use `text`.
2. Add a non-unique index on `("runId", "nodeId", "createdAt")`. Every read also filters by `flowId`,
   because a parent run and the sub-flows it calls share one `runId`.
3. Write the column wherever a row is created, in the back and in the worker.
4. Do not backfill it. Only rows written by the new code are read by `runId`: the worker reads the
   current run's rows, and the claim-check same-run read requires a `runId`. A backfill would
   rewrite `node_executions` inside the boot migration for no reader. Older rows leave with the
   30-day retention.
5. Readers keep the existing grouping rule, `COALESCE(metadata->>'runId', "execId")`, for rows that
   have no run id.
6. Generate the migration with `pnpm migration:generate`, and order it after any migration B1 adds.

`flows_nodes_edges` needs no change. `flow_id` and `target` already have indexes, and the
version filter applies to the few rows they return. Add a composite index only if a measurement on
real data shows it is needed: the table is rewritten on every autosave.

What this must not undo (from the history of both tables):

- One row per execution; parallel runs never overwrite each other (2026-06-10).
- Every node read and write is scoped by `(flow_id, node_id, flow_version_history_id)`.
- Retention bounds the table: payloads are slimmed after 7 days, rows deleted after 30.
- Cancellation stays in `flow_run_states`.
- `runToken` stays `select: false` and is never logged.

## How the worker receives a node's input

The dispatch carries a `projection` (`NodeInputProjection` in `flux/substitution-schema-delta.ts`) next
to B3's resolution: `runId`, `flowId`, `flowVersionHistoryId`, `completedSourceIds` and, inside a loop
iteration, `{ index, bodyNodeIds }`. The worker then projects into the target only:

1. It reads the version's edges and the run's latest row per node (`runId`, `flowId`), and resolves
   each `__claimRef`.
2. It gives every source of the target its data, as `addConnectToNodes` does after each completion:
   a source with a row uses `outputData`; any other source, including `globalStarter`, uses its
   saved `flows_nodes.data` through `clearRunOutputForSeed`, projected from its own sources first.
3. It runs the ported `modifyData` once per source, in edge order, and keeps only the target.
4. B3's placeholder resolution runs over the result. In shadow mode the worker projects the raw input
   before it compares.

**Completed sources (decision 6).** `completedSourceIds` lists only the target's own sources that are
in the scheduler's `completed` set when the node is dispatched. If one of them has no row, the node
fails with a `SystemError` instead of receiving an empty entry. Listing every completed node in the
run would make each dispatch, and so the Temporal history, grow with the run. On the main loop every
completed node writes a row; the paths that mark a node completed without one are the `arrayNode`
body (gated), a budget stop and a cancellation, and the last two end the run.

**Claim-check reads.** A node may read the claim-check payload of another node in the same run and
flow: `ClaimCheckAuthzService.authorizeRead` accepts a run token whose row shares the owner row's
`runId` and `flowId`. A sub-flow (same `runId`, other `flowId`), another run and a row without a
`runId` are refused. Writes are unchanged.

**Flag.** The projection runs only when B3's resolution is on (apply or shadow) **and**
`worker_edge_projection` is on, so turning B3 on in production does not turn this on with it.

**Gate.** A run keeps the projection on the back when any connected node of the flow is an
`arrayNode`, `fluxObject`, `nodesBox`, `libraryNode`, `fluxBox`, `tableProcessor` or
`dynamicSettingsNode` (`BACK_ONLY_PROJECTION_NODE_TYPES` in `flux/node-input-projection.ts`). The
gate is per flow, not per target: inside an `arrayNode` loop, inline body nodes have no row and are
not yet completed, so a per-target gate would hand the worker their saved, cleared data instead of
their output. `conditionNode` is not gated: its loop counter is read by `evaluateLoopCondition`,
never by the projection. A dispatch for a node of another flow in the same run (a sub-flow) carries
no projection.

## The `logs` handle

Until 2026-06-09 `commandTextNode.data.logs` was text. That day a worker refactor removed the
`JSON.stringify` that a 2026-04 change had added, so the worker now saves `logs` as an object
(`{ sources, reasoning, toolCalls, toolResults, finishReason }`). The projection still treats it as
text: an object is truthy, so it becomes the entry's `text` as is, and the next node receives
`"[object Object]"`. The Logs panel was fixed on 2026-08-03 with `formatNodeLogs`; the edge was not.

This task fixes it. The `logs` entry carries the same text the Logs panel shows:

- A string stays as is.
- An object becomes `JSON.stringify(logs, null, 2)`.
- A missing value becomes `'No Logs generated'`.

The fix lands in the back's projection (and so in the worker's ported copy) and in the front's own
copy (`front/src/util/autosave/utilis.ts`, which can call `formatNodeLogs`). It is a separate commit,
before the extraction, so the extraction stays behaviour-neutral against it. No backfill: the
projection rewrites the target's entries on the next run.

## Extraction

`helpers.ts` is not pure. It imports `folw/contants.ts` (which imports `helpers.ts` back),
`flowTextSegmentation`, `flux/execution-budget` and `loop-iteration-context`. B2's sync accepts a
file only when every relative import is also ported, and allows only `@nestjs/common` as a package.
The extraction therefore cuts those imports, so that the new module depends only on other ported
files.

The pure module is `folw/helpers/edge-projection.ts`, with the iteration as `LoopIteration`
(`folw/helpers/loop-iteration.ts`). `helpers.ts` keeps wrappers for `getOutputByType`,
`buildHandleEntryIdForWrite`, `givingDataToNode` and `modifyData` that read `loopIterationContext`
and pass it on, so the back's call sites do not change. `allNodesTargetBasedOnType` moved to
`folw/helpers/node-target-fields.ts` and the processor-array helpers to
`folw/helpers/processor-array.ts`; `contants.ts` re-exports them.

## Scope

**In.** Extract the projection (`getOutputByType`, `givingDataToNode`, `modifyData`,
`addConnectToNodes`, `buildHandleEntryIdForWrite`, `reconcileEntries` and what they need) into a
pure module, behaviour-neutral. The back imports it at every call site.

**In.** The loop iteration becomes an explicit argument (index and body node ids), not an
`AsyncLocalStorage` read, so the worker can call it.

**In.** Port the module and `clearRunOutputForSeed` to the worker through `pnpm sync:ported-engine`,
covered by both drift tests (`back/src/shared/ported-engine/ported-engine-drift.spec.ts` and
`worker/src/ported/ported-from.spec.ts`). Import the rule; never restate it.

**In.** The `runId` column and its index, without a backfill.

**In.** On B3's flag, the worker builds the target's `*Data` from the database as described above,
and B3's placeholder resolution then runs over the result. The back stops projecting into a
worker-dispatched target on that path.

**In.** The gate that keeps a flow with a back-only source on the back's path.

**In.** The `logs` fix, in the back and in the front's copy.

**Out.** Execution order, ready and dead nodes, and the loop itself: B4.

**Out.** Back-only sources: B6.

**Out.** The front's copy of the projection, except for the `logs` fix. It is a third copy and a
drift risk worth its own look.

## Verification

- **Negative control (required).** Change one branch in the ported copy (for example the `console`
  join separator) and confirm a drift test goes red. Then remove an upstream's `node_executions` row
  on the new path and confirm the node fails loudly instead of receiving an empty entry.
- **`logs`.** A test where the source's `logs` is an object fails before the fix with
  `"[object Object]"` and passes after it.
- **A source that did not run.** A test where an upstream on a branch not taken has stale output in
  `flows_nodes` confirms the target receives the cleared value, as the back delivers it.
- **Equivalence.** Build every node's `*Data` both ways (back in memory vs. worker from the database)
  and diff: every source/handle pair, the default strings, loop iterations (`#N` ids) and an edge
  disconnected between runs. Retention slims `input` and `outputData` after 7 days, so the stored
  corpus covers only the last week of runs; use dev runs plus fixtures for the pairs it lacks.
- **Measure before refusing** (PLAN §3.3.2). Classify every flow the gate keeps on the back's path
  and drive refused-although-it-works to zero.

### Subtask B3b.1

The worker must not read the live `flows_nodes` row to build an input. Seeding the target and the
sources that did not run from the flow the back prepared at run start is
[B3b.1](TASK-B3B1-RUN-SEED-SNAPSHOT.md) (`868mh8pqh`), on the same branches.

### Measured on 2026-10-14

The harness is `etc/b3b-equivalence/harness.ts` in the workspace. It runs the worker's own
`projectNodeInput` over exported dev rows. Each target sees only the rows created before it, and its
`*Data` is diffed against the input the back sent.

| Verdict | Targets | Why |
|---|---|---|
| Match | 101 | — |
| Gated | 29 | `arrayNode` or `fluxBox` in the flow |
| Unverifiable | 10 | Single-node runs: the input comes from the canvas, not a flow run |
| Diverges | 1 | A `pushData` reconfigured after its run; its live draft was saved later |

- With the projection removed, 17 more targets diverge, so the harness can see a difference.
- No completed source lacked a row, so the loud failure refused nothing.
- The gate keeps 8 of 61 dev flow versions on the back's path, all because their data lives only
  in the back's memory.
- The dev corpus has no skipped source with stale saved output, no loop iteration (gated) and no
  edge disconnected between runs. The worker fixture tests cover the first; the characterization
  snapshots cover each source/handle pair, because the worker runs the same ported function.

## Done when

On B3's flag, the worker builds every `*Data` entry from the database for flows without back-only
sources; equivalence is proven; the projection exists once, extracted and ported with a drift test;
`logs` reaches the next node as text; and the back's path is still present and selectable.

## Corrections on 2026-10-13

- The projection is about 1,940 lines, not 1,070, and it has 59 call sites in `flux.service.ts` plus
  callers in `contants.ts` and `resolve-inbound-variables.ts`, not fourteen.
- B3 does not introduce a `{ nodeId: execId }` map of completed upstreams. Its journal lists worker
  dispatches since the last checkpoint only. This task adds the `runId` column instead.
- On B3's path the back still projects `*Data` before dispatch; the worker only fills in their text.
- The back-only list was wrong: `outputObjectNode` and `globalStarter` are not projection sources;
  `tableProcessor`, `dynamicSettingsNode` and the `arrayNode` loop body were missing.
- A source that did not run in the run needs `clearRunOutputForSeed`, not its stored output.
- `commandTextNode.logs` has been an object since 2026-06-09; this task fixes the projection.
- (2026-10-14) The `conditionNode` loop counter is not a projection source; the gate leaves
  `conditionNode` out. 28 dev runs in 14 days had a `conditionNode` source.
- (2026-10-14) The back projects from every source after each completion, not only from sources that
  ran, so a source that did not run is projected from its cleared saved data.
- (2026-10-14) The `runId` migration no longer backfills old rows (back `400dd9fd`). No reader needs
  them, and the backfill would rewrite `node_executions` at boot in prod.

## Files

`back/src/app-api/folw/helpers/helpers.ts` · `back/src/app-api/folw/contants.ts` ·
`back/src/app-api/folw/helpers/loop-iteration-context.ts` · `back/src/app-api/flux/flux.service.ts` ·
`back/src/app-api/flux/node-output-reset.ts` · `back/src/entities/node_execution.entity.ts` and a
generated migration · `back/scripts/sync-ported-engine.ts` · `worker/src/ported/back/` ·
`worker/src/modules/nodes/shared/resolve-node-input.ts` and the worker-side projection (new) ·
`front/src/util/autosave/utilis.ts`
