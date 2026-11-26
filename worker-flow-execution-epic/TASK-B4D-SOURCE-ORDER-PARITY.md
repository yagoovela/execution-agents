# B4d — Source order parity on the workflow path

ClickUp: [1gahkf3c5xc](https://app.clickup.com/t/1gahkf3c5xc). **Drafted 2026-11-26** from finding 1 of the A14-R4 dev
parity run.

**Depends on:** B3b and B4 (on `main`). Coordinates with B4c, which edits the same seed builders.
**Blocks:** turning `engine_in_workflow` on in production
([868mnbm7h](https://app.clickup.com/t/9011479430/868mnbm7h)), like B4c, and `temporal_schedules`.
**Relation to B5:** B5 does not need to wait for this task, and this task does not wait for B5. The
fix removes completion order from the rule, so parallel dispatch cannot change the result.

Code facts are read on back `origin/main` `90b7ef666` and worker `origin/main` `c34de93`. Lines are
given with the symbol, so you can find each place again after the lines move. No fact rests on
`develop`.

## Problem statement

A Data Output (`outputObjectNode`) with two or more sources joins their text in a different order on
the workflow engine (`processFlow`, B4) than on the legacy loop (`apiV2`). The joined text is the
API reply, and in a chat flow it is the assistant entry stored in chat history.

**Measured on dev on 2026-11-26 (A14-R4).** The same flow ran with `engine_in_workflow` off, then on:

| Probe | Flow | Legacy loop (`textData`) | Workflow (`textData`) |
|---|---|---|---|
| X1 | two `mathFunction` nodes into one Data Output, no memory | `first runs`, `second runs` | `second runs`, `first runs` |
| F2 | two AI Text Generators and a Small Memory into one Data Output (a copy of a stored dev flow) | `Ai Text Generator` A, B, memory | B, A, memory: the answer text and the stored assistant entry change |

Evidence: `node_executions.input.textData` of runs `064b3011` (X1 off), `2bfa4dcf` (X1 on),
`88fa5683` and `da75c047` (F2 off), `497642e1` and `c0e70e6c` (F2 on), in the A14-R4 evidence, kept outside this
repository. X1 has no memory, so the defect is not A14's. On `main`, F2's class stays on
the legacy loop (`fluxObject` is `execution: 'state'`, not accepted by the gate); A14 is what routes
it to the workflow.

### What each engine does

**Legacy loop.** The order is not completion order. It is the order in which each source first
appears as `source` in the flow's edge list.

1. At run start, `apiV2` empties the Data Output: `text: ''`, `textData: []`
   (`flux.service.ts:4897-4907`). No other `*Data` array is emptied: `clearRunOutputForSeed` blanks
   the `text` of each entry in `promptData`, `contentData` and `textData` and keeps the entries in
   place (`node-output-reset.ts:176-196`).
2. Each `addConnectToNodes` call runs `modifyData` once per distinct edge source, in the order the
   sources first appear in `edges` (`folw/contants.ts:1592-1604`).
3. Every source writes an entry, even one that has not run: the generic branch of `getOutputByType`
   writes `text: ''` (`folw/helpers/edge-projection.ts:733-743`).
4. Later writes update an entry in place by `id` and append only an `id` that is missing
   (`edge-projection.ts:1823-1878`).

So the first `addConnectToNodes` call of the run fixes every position. That call is the
variable-input apply (`flux.service.ts:5048`) or the publish after the first node, through
`processNodeViaTemporal` (`:2676`) or `publishInApiNodeOutput` (`:2693-2717`, called at `:6395` and
`:6683`). The loop's visit order (`planOrder`, `scheduler.ts:497-510`) decides only when that call
happens, not the order. A simulation on the `main` engine files confirms it: with edges
`A→Out, S→B, B→A, B→Out, C→Out, B→C`, the legacy rule gives `A, B, C` for completion orders
`B, A, C` and `B, C, A`. `planOrder` gives `B, A, C`, so the scheduler's order is not the legacy
order either.

`edges` comes from `getFlowWithNodesAndEdges` (`folw/flow.service.ts:63-97`), whose edge reads have
no `ORDER BY` (`flow-edge.service.ts:23-33`, `:154-162`). The legacy order therefore rests on the
physical row order of `flows_nodes_edges`. It is stable while no edge row is rewritten.

**Workflow.** The order is the order in which the worker reads the target's incoming edges.

1. The API seed is `newFlows` (`flux.service.ts:2287-2293`), taken after the reset. Unless a variable
   input ran the `addConnectToNodes` pass at `:5048`, the Data Output's `textData` is `[]`. The X1
   and F2 seeds hold `[]`.
2. `projectNodeInput` reads edges with `QUERY_FIND_EDGES`, which has no `ORDER BY`
   (`project-node-input.ts:8-12`). `projectIntoNode` calls `modifyData` once per source of the
   target's incoming edges, in that read order (`sourcesOf`, `:70-76`; loop, `:93-105`). Each call
   appends the source's entry.

In X1 the edge rows are `first→second` (control), `second→Out`, `first→Out`. The legacy rule sees
`first` before `second`; the worker reads `second→Out` before `first→Out`.

**Why S5 matched.** When a run passes `variableInputs`, the pass at `:5048` writes every Data Output
entry into `newFlows` in the legacy order before the seed is written. The worker then updates the
entries in place. The S5 seeds (`d20d9358`, `001f5995`) hold `varInputNode, mathFunction, fluxObject`,
the legacy order, while the worker's read order is `varInputNode, fluxObject, mathFunction`. Parity
there is an accident of the variable input.

### Which targets are affected

| Target and field | Affected | Why |
|---|---|---|
| `outputObjectNode.textData` (handle `input`) | Yes | The only array the legacy loop empties at run start, so its order is rebuilt every run. |
| Any other `*Data` array: `commandTextNode` `promptData`/`contentData`/`instructionData`/`personaData`, `outputController.textData`, `conditionNode.textData` (joined by the SWITCH rule, `scheduler.ts:84`), Data Output `emailsData`/`subjectData`/`urlsData`/`callbackUrlInputData` | Only when a connected source is missing from the stored array | Both engines keep the stored positions. A missing source is appended: in the legacy order on the legacy loop, in the read order on the worker. Not measured. |
| `fluxObject` entries (`inputAdd`) | No: A14 owns them | A14 orders memory entries by completion, stamped with the producer's finish time. |
| `nodesBox` joins | No | It joins in edge order directly (`edge-projection.ts:1661-1686`) and is not workflow-eligible (back-only projection, A7). |

### Which paths are affected

| Path | Affected | Detail |
|---|---|---|
| B4 full run (`runApiV2ViaWorkflow`): API, MCP, webhook | Yes, with `engine_in_workflow` on (off in production) | Diverges when no variable input prefills the seed. |
| Batch rows (B7) and Temporal schedules (E4b), both through `prepareWorkflowSeed` (`flux.service.ts:988-1040`) | Yes. Batch rows run on `processFlow` with no flag. `temporal_schedules` is off in production. | This seed applies neither the Data Output reset nor `clearRunOutputForSeed`, so it carries the canvas `textData`. That array holds the order of whichever engine ran last, because the finish step writes `textData` back to the live row (`:1597-1611`). The variable-input pass then appends only missing sources. |
| Legacy loop with `worker_edge_projection` on (B3b) | Data Output: no. Other targets: only a source missing from the stored array. | The legacy loop never dispatches a Data Output (`outputObjectNode.flowDispatch: 'inline'`, `node-dispatch-registry.ts:285-293`). The loop projects in the worker only with `worker_input_resolution` (or its shadow) on, `worker_edge_projection` on and no back-only projection node (`flux.service.ts:2509-2517`). **The production state of `worker_edge_projection` is not verified.** Dev has it on since 2026-10-14. |

## Goals

- [ ] Every multi-source target gets its `*Data` entries in the legacy loop's order on every workflow
      entry point: API runs with and without variable inputs, batch rows, schedules and child runs.
- [ ] The order does not depend on completion order, so B5's parallel dispatch and Temporal replay
      cannot change it.
- [ ] The rule comes from the back's own code (`addConnectToNodes`, the run-start reset), imported or
      ported through `sync:ported-engine`, never restated in the worker.

## Out of scope

| Item | Reason |
|---|---|
| A canonical order for both engines, for example `ORDER BY` on the edge reads | It changes the legacy loop's output for existing flows. That is a product decision: see B4d-D2. |
| Memory entry order (`fluxObject`) | A14 owns it, with a different rule (completion order). |
| The worker reading live edges instead of the run's edges, so an edit during a run changes the projection | A B3b design point, not an order rule. |
| Stale source text on the batch and schedule seed (a source on a dead branch keeps its canvas text) | Found while reading `prepareWorkflowSeed`, not measured. The shared reset below removes it as a side effect. If the user wants it tracked alone, it becomes its own task. |

## User stories

### P1: A Data Output joins its sources in the legacy order ⭐ MVP

**User story:** As a customer whose flow feeds several nodes into one Data Output, I want the same
reply whichever engine runs my flow, so that turning on the workflow engine does not change my
answers or my chat history.

**Acceptance criteria:**

1. **SO-01** WHEN a workflow API run without variable inputs reaches a Data Output with two or more
   sources THEN its `textData` SHALL list the sources in the order the legacy loop gives for the same
   flow.
2. **SO-02** WHEN the same run passes variable inputs THEN the order SHALL be the same as in SO-01.
3. **SO-03** WHEN a chat flow's Data Output becomes the assistant entry THEN the stored entry SHALL
   equal the legacy loop's entry, text for text.
4. **SO-04** WHEN sources complete in a different order between two runs of the same flow THEN
   `textData` SHALL keep the same order.

**Independent test:** X1 and the F2 class on dev, with `engine_in_workflow` off and on: identical
`textData`.

### P1: Batch rows and schedules start from the legacy run-start state ⭐ MVP

**User story:** As a customer who runs a flow in batch or on a schedule, I want each run's reply built
like an API run's, so that the order does not depend on which engine ran the flow last.

1. **SO-05** WHEN `prepareWorkflowSeed` builds a seed THEN it SHALL apply the same run-start reset as
   `apiV2`, through one shared back function.
2. **SO-06** WHEN the canvas `textData` holds another order or old texts THEN the batch row's
   Data Output SHALL still list the legacy order with this run's texts.

### P2: The worker projection follows the legacy rule

1. **SO-07** WHEN `projectIntoNode` adds an entry the seed does not hold (for example, a per-iteration
   entry inside an `arrayNode` body once B6 is on `main`) THEN it SHALL add the sources in the legacy
   order.
2. **SO-08** WHEN `flows_nodes_edges` returns the incoming edges in another physical order THEN the
   projected order SHALL not change.
3. **SO-09** WHEN a non-Data-Output target's stored array lacks a connected source THEN both engines
   SHALL place that source in the same position.

## Edge cases

- WHEN a source is on a dead branch THEN its entry SHALL keep its position with the text the legacy
  loop gives it (`''` for a cleared output type).
- WHEN one source feeds the Data Output on two handles (`input` and `emails`) THEN the `textData`
  position SHALL follow the legacy rule, which counts the source once.
- WHEN a self loop or the global starter edge (handle `a`) reaches the Data Output THEN the result
  SHALL match the legacy loop. The worker drops starter edges from `sourcesOf`; check what the legacy
  loop does with them before you decide.
- WHEN a flow has version control on THEN the order SHALL come from the deployed history's edges,
  which `resolveExecutionHistoryId` picks for both engines.
- WHEN a run continues as new or a child run (`fluxBox`, `libraryNode`) starts THEN the child seed
  SHALL follow the same rule.
- WHEN B5 dispatches sibling sources in parallel THEN SO-04 SHALL hold.

## Design direction (settled in Design)

1. **The seed holds the legacy order.** Before `runApiV2ViaWorkflow` and `prepareWorkflowSeed` write
   a seed, they run one `addConnectToNodes` pass over the seed nodes, with a no-op schema callback, as
   `applyVariableInputsToSeedNodes` already does (`flux.service.ts:935-986`). The pass works on a copy,
   so the legacy loop does not change. A simulation on the `main` engine files shows that a
   prefilled seed keeps `A, B, C` even when the worker reads the edges in reverse.
2. **One run-start reset.** Move the Data Output reset (`flux.service.ts:4897-4907`) into
   `node-output-reset.ts`, next to `clearRunOutputForSeed`, and call it from `apiV2` and
   `prepareWorkflowSeed`. B7b set the precedent of aligning `prepareWorkflowSeed` with `apiV2`.
3. **The worker walks sources in the legacy order.** Extract the source order of `addConnectToNodes`
   into an exported function in `folw/helpers/edge-projection.ts`, which `sync:ported-engine` already
   ports. `addConnectToNodes` and `projectIntoNode` both call it. The worker applies it to the run's
   edge list in the order the back loaded it (`run_seeds.payload.edges`), not to the unordered
   `QUERY_FIND_EDGES` result.
4. **Determinism.** The seed is data written before the workflow starts, and the projection runs in
   an activity, so no workflow code changes and no `patched()` gate is needed. Neither completion
   time nor `planOrder` enters the rule.

**Open decisions:**

| Id | Question | Recommendation |
|---|---|---|
| B4d-D1 | The legacy loop's B3b seed has no `run_seeds` row. Where does the worker get the edge order on that path? | Run the same prefill pass on the B3b seed nodes (`openRunInputResolution`), and let the worker keep its read order there. A Data Output is never dispatched on that path. |
| B4d-D2 | Keep the legacy order, which rests on physical row order, or define a canonical order for both engines? | Keep parity now. A canonical order changes the legacy loop and needs its own decision. |

## Requirement traceability

| ID | Story | Status |
|---|---|---|
| SO-01 | P1 Data Output: no variable inputs | Pending |
| SO-02 | P1 Data Output: with variable inputs | Pending |
| SO-03 | P1 Data Output: chat history entry | Pending |
| SO-04 | P1 Data Output: completion order independence | Pending |
| SO-05 | P1 batch and schedule: shared reset | Pending |
| SO-06 | P1 batch and schedule: canvas order ignored | Pending |
| SO-07 | P2 worker: entries the seed does not hold | Pending |
| SO-08 | P2 worker: physical row order ignored | Pending |
| SO-09 | P2 other targets: missing stored entry | Pending |

## Production reach

`b4d-q1-multi-source-targets.sql` (read-only, one statement, counts only) counts live flows with a
Data Output fed by two or more sources on `input`, and how many of those flows ran that Data Output
in the last 30 days. `order_differs` compares, per source, the first edge of the flow where the node
is a source (the legacy rule) with the first edge into this target from the node (the worker's read).
Both positions come from `ctid`, the physical row order that the unordered reads return today, so
the column is an approximation.

**Dev, 2026-11-26** (271 ms, 48.6k shared buffers, about 1k temp pages, sequential scans of
`flows_nodes_edges` and `flows`; a first version with correlated subqueries took 7.2 s):

| Measure | Dev |
|---|---|
| Flows with a multi-source Data Output | 51 (54 Data Output nodes, up to 10 sources on one) |
| ... where the legacy and workflow orders differ | 18 |
| ... of those, with no `varInputNode` (never prefilled) | 2 |
| Flows whose multi-source Data Output ran in the last 30 days | 7 |
| ... where the orders differ | 3: all A14-R4 copies (F2, S5, X1) |
| ... of those, with no `varInputNode` | 1 (X1) |

Production is not measured. The user runs the query in DBeaver before B4d ships and again before
`engine_in_workflow` goes on.

## Test list (must pass)

1. **Negative control first.** Worker spec on `projectNodeInput` with the X1 fixture, the edge query
   returning `second→Out` before `first→Out`: on `main` the result is `second, first`; after the
   change it is `first, second`. Record the red run.
2. Back spec on the API seed of a flow without variable inputs: the Data Output `textData` lists
   every source in the `addConnectToNodes` order. Negative control: remove the pass and watch `[]`.
3. The discriminating fixture (`A→Out, S→B, B→A, B→Out, C→Out, B→C`): the legacy loop with
   completion `B, A, C` and `B, C, A`, and the worker with the edge rows in both read orders, all give
   `A, B, C`.
4. Batch seed: a canvas `textData` of `B, A` with old texts gives a seed of `A, B` with this run's
   texts. Negative control: remove the shared reset from `prepareWorkflowSeed`.
5. A non-Data-Output target (`commandTextNode.contentData`) whose stored array lacks one connected
   source: both engines place it in the same position.
6. The `processFlow` replay histories replay unchanged.
7. Dev: X1, the F2 class and the discriminating fixture, each with `engine_in_workflow` off and on:
   identical `textData` and, for F2, an identical assistant entry.
8. Production: `b4d-q1-multi-source-targets.sql` before the deploy, to size the reach.

## Estimate

Uncalibrated, in hours:

| Part | Min | Avg | Max |
|---|---|---|---|
| Back: shared reset, seed prefill pass, extracted source order, port sync | 4 | 6 | 9 |
| Worker: projection order from the run's edge list | 2 | 4 | 6 |
| Specs with negative controls (back and worker) | 4 | 5 | 8 |
| Dev parity runs (X1, F2 class, discriminating fixture, a batch file) | 2 | 3 | 5 |
| **Total** | **12** | **18** | **28** |

The maximum covers B4d-D1 if the B3b seed needs the pass too, and a rebase onto B4c's seed changes.

## Not verified

- The production state of `worker_edge_projection`.
- Production reach: the query has run on dev only.
- `order_differs` uses the current physical row order. The order a past run saw may have been
  different.
- Whether the legacy loop gives the global starter edge into a Data Output an entry.
- Stale canvas text on the batch and schedule seed: read in the code, not reproduced.
- Batch and schedule runs were not exercised on dev. A14-R4 had no login JWT for `/upload/csv` or
  the schedule endpoints.
