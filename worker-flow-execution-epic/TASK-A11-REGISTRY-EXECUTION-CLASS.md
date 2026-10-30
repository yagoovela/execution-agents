# A11 — Give every node type an execution class

**Goal:** every node type the product can put on a canvas has one entry in the dispatch registry
that says where it executes, and every hand-kept dispatch list is derived from that entry.

**Depends on:** A1. **Blocks:** turning the B4 flag on in production, B5's measurement.
**Added 2026-10-23** from [`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md).
**Revised 2026-10-28** after validating the spec against back `e8781bda`, worker `892ae3d` and
front `2e533dc62` (all `origin/main`). The revision corrects five claims, adds the classes the first
table left out, and adds two pieces of work the validation found: the workflow projection fix that
makes `source` and `visual` safe, and the removal of the integration inline fallback. See **What the 2026-10-28
validation changed**.

## Why

The registry can say `worker` or `inline`, but it cannot say "does not execute". B4's gate
(`canUseWorkflowForFlow`, `back/src/app-api/flux/engine-selector.ts:5-28`) accepts a flow only when
every node has `flowDispatch: 'worker'` or is one of five hard-coded passive types. An unregistered
type fails the gate. So a Data Input, a sticky note or a Small Memory node keeps the whole flow on
the back's loop, and the loop can never be deleted.

Eighteen front or MCP types have no registry entry: `deepRefNode`, `dynamicSettingsNode`,
`fluxObject`, `mediaBox`, `nodesAdd`, `nodesGroup`, `outputTable`, `richTextBox`, `stickyNote`,
`storedDataCaller`, `tableProcessor`, `textBox`, `varInputForm`, `varInputNode`, `webLocations`,
`webMedia`, `webNews` and `webTrends`. The front's `nodeTypes` has 46 keys; the MCP's
`NODE_TYPE_METADATA` has 50 (the 46 plus the four MCP-only types).

The "does not execute" rule lives in four hand-kept copies, and they do not agree:

| Copy | Where | Types |
|---|---|---|
| `NON_EXECUTABLE_NODE_TYPES` | `back/src/app-api/flux/prefetch/is-non-executable.ts:1-5` | 3: `comment`, `label`, `group` |
| `WORKFLOW_SAFE_NON_WORKER_TYPES` | `back/src/app-api/flux/engine-selector.ts:5-11` | 5: the three plus `globalStarter`, `textBox` |
| `WHITELISTED` (`ineligibleTypes` log) | `back/src/app-api/flux/flux.service.ts:3778-3784` | the same 5 |
| `NON_EXECUTABLE_TYPES` | `worker/src/modules/temporal/workflows/process-flow.workflow.ts:39-45` | the same 5, with a "Keep in sync" comment at `:37` |

The prefetch copy has three types on purpose: prefetch handles `globalStarter` and `textBox` on its
own path. A spec already binds the registry to it (`node-dispatch-registry.spec.ts`). Nothing binds
the three five-type copies.

## Classes

An `execution` field on every registry entry, with one of six values. Classify each type from the
code that reads or writes it at run time, not from its name.

| Value | Meaning | Gate |
|---|---|---|
| `worker` | The worker executes it in a flow run and in the single-node Run. | accepts |
| `source` | Nothing executes it, but it has a value. The projection resolves it: from the run seed when nothing feeds it (a fixed value), or from its upstream producer's output in the same run when it is a pass-through. | accepts |
| `visual` | Nothing executes it and it has no value in a run. Its edges carry nothing. | accepts |
| `sink` | It receives the run's output and builds the reply that the API, the chatbot and delivery read. | refuses until A13 |
| `state` | It keeps state across runs: it reads before the run and writes after nodes and after the run. | refuses until A14 |
| `back` | A step that the back still executes, with a task that moves it to `worker`. | refuses |

`sink` and `state` are roles, not a location. They stay true after A13 and A14 move the work into
the workflow: a sink still builds the reply and a memory still outlives the run. Classing them `back`
would mix "not migrated yet" with "a different role", and `back` would grow into a catch-all. Each
of those tasks changes the gate to accept its class, and nothing else.

**The rule that keeps `back`, `sink` and `state` small.** Every entry with one of these three values
names the task that resolves it in `handoffOwner`. The drift spec fails on an entry without one, so
a new exception cannot land without an owner. `handoffOwner`'s union type grows to name A6b, A7,
A13, A14 and B6.

### The model behind `source` and `visual`

In a run, every value comes from one of two places, and no node writes into another:

1. The run seed (`run_seed_nodes`): the canvas snapshot plus the bound run inputs, written before the
   workflow starts and never changed during the run.
2. The `node_executions` rows of that `runId`: each producer's output.

This keeps the worker and the back stateless. Temporal replays read the same input, a retried
activity reads the same seed, two concurrent runs of one flow do not overwrite each other's display
nodes, and no back instance holds run state in memory. `fluxObject` and `outputObjectNode` are the
two types the model does not cover as a value: one is `state`, the other `sink`.

**In.** The six values, and the skip below: the workflow still schedules a `source` or `visual` node
and skips it, and the projection walks past it.

**The class does not change reading or execution.** It is registry metadata; node data stays as it
is. A display node keeps its references: each `textData` item is
`{ id: "<producer id>$<handle>", text }`, where `id` is the reference and `text` is a cached copy.
The projection, in back and in the worker, resolves through the edge, not through that cached text.

**Out — later steps of the same model, and what each one costs.**

1. **The scheduler stops scheduling `source` and `visual` nodes** and links a consumer straight to
   the producer behind a pass-through. It saves a workflow step and its Temporal events per node,
   and the skip goes away.
   - It changes a shared rule: `classifyEdge` and `buildSchedulerState`
     (`back/src/app-api/flux/scheduler.ts`, ported to the worker). Both engines change together, or
     B4's order-equivalence check breaks.
   - The contracted edge keeps the class of the edges it replaces. Dev has control edges through a
     `textBox` (`webAmazon → textBox`: 40), and a `conditionNode` that prunes a branch must also
     prune the consumer behind a pass-through on that branch.
   - The Logs page stops listing these nodes under B4 (the skip already does). That is fewer rows
     and fewer copies of PHI.
2. **A display node shows its producer's value instead of a copy.** Today the front's autosave copies
   the producer's `data.text` into the target's `textData` (`front/src/util/autosave/utilis.ts:495-545`)
   and `TextBoxNode.tsx:38` shows that copy; the back's loop does the same in memory
   (`addConnectToNodes`). The worker's live write already skips `textData`
   (`LIVE_WRITE_EXCLUDED_FIELDS`, `worker/src/modules/nodes/shared/persist-node-outcome.ts`).
   - It removes a cross-node write (C1's goal), the clobber between concurrent runs of one flow, and
     an autosave PATCH per producer run.
   - Read the producer's own canvas row, which the worker's live write keeps current, not
     `node_executions`. Production slims `outputData` after 7 days and deletes the row after 30, so
     a display that reads run rows goes blank after a week.
   - Execution does not change: a single-node Run walks from the display node to the producer in
     the seed. This is traced from code, not tested.
   - Not checked: who else reads `textData[].text` directly (the MCP, published interfaces,
     exports). Each such reader would see a stale value.
   - C1 removes the copy from the run path, so it needs this read in place first. See **Open items**.

`execution` sits **next to** `flowDispatch`; it does not replace it. The gate,
`strandedWorkerModules()` and `hasDispatchConflict()` read `flowDispatch` today, and rewriting them is
not classification. C2 removes `flowDispatch` when it deletes the back's loop, because `inline` stops
meaning anything then (see C2's Done-when).

| Class | Types | Dev evidence (live canvas, 2026-10-28) |
|---|---|---|
| `visual` | `stickyNote`, `nodesGroup`, `comment`, `label`, `group` | `stickyNote` 2221 nodes, 6 control edges out; `nodesGroup` 28, no edges; the phantoms have 0 nodes |
| `visual`, deprecated (`phantom`) | `webNews`, `webMedia`, `webLocations`, `varInputForm` | deprecated; `webNews` 25 nodes with 27 edges out; no code executes any of the four, so the next node gets nothing today. See **Deprecated types** |
| `source`, value | `textBox`, `richTextBox`, `storedDataCaller`, `deepRefNode`, `nodesAdd`, `mediaBox`, `outputTable`, `tableProcessor`, `dynamicSettingsNode` | `textBox` 5646 nodes, 6264 data edges out (5549 into `commandTextNode`); `richTextBox` 1216, 856 |
| `source`, run entry | `varInputNode`, `globalStarter` | `varInputNode` 1155 nodes, 1327 data edges out; its run input is bound into the seed before the workflow starts (`flux.service.ts:3628-3640`); `globalStarter` edges classify as `global` and it is never scheduled |
| `worker` | every entry that has `flowDispatch: 'worker'` today, plus `thirdPartyIntegration` and `hubSpotCRM` | see **Integration types** |
| `sink` | `outputObjectNode` (A13) | the API reply, the chatbot answer and A9's delivery read it (audit §2.4) |
| `state` | `fluxObject` (A14) | `persistSmallMemoryEntries` writes after every node (`flux.service.ts:1257`); chat sessions load before the run (audit §2.5) |
| `back` | `webTrends` (A6b), `nodesBox` (A7), `arrayNode`, `conditionNode`, `fluxBox`, `libraryNode` (B6) | each has a task that moves it to `worker` |

`textBox` and `richTextBox` are value sources, not decoration: `edge-projection.ts:417-429` reads
`textData`. They play two roles. With no inbound data edge, the value is fixed configuration. More
often they are pass-through displays: on dev, `commandTextNode` feeds `richTextBox` through 539
edges and `textBox` through 272, and `textBox` feeds `textBox` through 169. The back's loop copies
the producer's output into the target's `textData` (`addConnectToNodes`,
`back/src/app-api/folw/contants.ts:723`), a cross-node write that C1 removes from the run path. The
projection needs no copy: `completedUpstream` walks past a node that is not in `completed` until it
reaches a producer.

`webTrends` executes nowhere in a run; the browser calls `POST /trends`
(`buildWithApi.controller.ts:151`). It stays `back` until A6b decides it.

The counts come from [`a11-q2-none-sources.sql`](./a11-q2-none-sources.sql) (outbound edges) and
[`a11-q4-source-inbound.sql`](./a11-q4-source-inbound.sql) (inbound edges), run on dev. Run both on
production before trusting the classes; the before/after measurement below needs them anyway.

## Deprecated types

`webNews`, `webMedia`, `webLocations` and `varInputForm` are deprecated (decided 2026-10-28). No
front component renders them (`front/src/util/nodeTypes.tsx:83-85` has the three web types commented
out, and `varInputForm` is in neither `nodeTypes` nor `formNodeTypes`), and no code executes them.
The MCP already refuses to build them: `UNBUILDABLE_NODE_TYPES`
(`back/src/app-mcp/node-types/node-types.service.ts:76-82`) holds exactly these four,
`list_node_types` hides them, and `assertNodeTypeBuildable` (`mcp-write.service.ts:2052-2059`)
rejects them in a write. The nodes on dev predate that guard.

Saved nodes of these types still exist (dev: 25 `webNews`, 11 `webLocations`, 6 `varInputForm`, 5
`webMedia`). They decide how far the removal can go.

**Where the four still appear** (`main` of all five repos, 2026-10-28, a case-insensitive search that
also matches `-`, `_` and space variants): 17 files, 10 in back, 7 in front and 2 in the worker; none
in `mcp-server` or `docs`. None of them renders or executes the four.

| Group | Files | In A11 |
|---|---|---|
| Definitions | back `src/enums/node_types.enum.ts:7,20-22`; back `node-type-metadata.ts:479,1591,1615,1647` | metadata removed; enum stays (see **Out**) |
| Dead entries in per-type tables | back `folw/helpers/node-target-fields.ts:101-109` (`allNodesTargetBasedOnType`) and its worker port; back `shared/node-fields/node-referenceable-fields.ts:23-27` (`NODE_REFERENCEABLE_FIELDS`) and its worker port; back `folw/agentflow-doc.node-extractor.ts:24-33` (`WEB_DATA_TYPES`); back `app-mcp/node-layout.util.ts:86`; front `util/dataStoredToType.ts:2,119-127`; front `util/myFunctionsCoreDisplay.tsx:388-392` (`basedOnType`); front `util/checkHandlesConnectable.ts:14-16` (`WEB_NODES`); front `components/UI/Node/nodeConstants.tsx:1100-1110`; front `util/nodeTypes.tsx:83-85` (comments) | removed |
| Guards | back `UNBUILDABLE_NODE_TYPES` (derived from the enum), pinned by `node-handle-registry.spec.ts:60-66` and used by `mcp-write.service.spec.ts:2208`; front `views/CoreNodeDisplay.tsx:404` and `views/CoreNodeDisplaySpaces.tsx:447` | MCP guards stay; front filter fixed |
| Data and fixtures | back seeder, "Sales funnel" flow (`database/seeders/flow/data.ts:3272`, one `webNews` node and four edges, run only by `pnpm seed`); back `test/fixtures/superchat-learning-eval/cases.json` (conversation text only) | seeder node removed; fixture text stays |

**In.**

1. Remove the four entries from `NODE_TYPE_METADATA` (`back/src/app-mcp/node-types/node-type-metadata.ts`).
   Run the `mcp-node-schema-sync` skill (PLAN §3.3 point 6).
2. Register the four as `execution: 'visual'` with `phantom: true`, the same treatment A1 gave
   `comment`, `label` and `group`: the registry names them, no canvas offers them. A flow that still
   holds one stays eligible for the gate, and the node keeps delivering nothing, as today. Leaving
   them unregistered would make the gate refuse those flows, a false refusal.
3. Remove the dead entries listed above from every per-type table, in back and front, and delete the
   commented-out lines in `nodeTypes.tsx`. Change the back files and run `pnpm sync:ported-engine`
   for the two worker copies, so the ported-engine drift spec stays green.
4. Remove the `webNews` node and its four edges from the seeder's "Sales funnel" flow, so a new local
   database no longer gets one. Keep the flow's other nodes and edges as they are.
5. Fix the filter in `CoreNodeDisplay.tsx:404` and `CoreNodeDisplaySpaces.tsx:447`, and keep it
   while saved nodes exist. Today it filters `'webLocation'`, singular, so a saved `webLocations`
   node is not hidden, and it does not filter `varInputForm`. Make both views read one front
   constant that names the four deprecated types.

**Out — keep them in the back's `NodeType` enum.** `createNode.dto.ts` and `updateNode.dto.ts`
validate `type` with `@IsNodeType()`, which ends in `@IsEnum(NodeType)` (`nodeTypeAlias.decorator.ts`).
Removing a member makes the API reject any create or update of a node already saved with that type,
such as the front's autosave on an old canvas or a copy of such a flow. `UNBUILDABLE_NODE_TYPES` is
derived from the enum, so the MCP guard keeps working while the members stay.

**Out — the MCP guards stay** with the enum: `UNBUILDABLE_NODE_TYPES`, its pin in
`node-handle-registry.spec.ts:60-66` and the refusal case in `mcp-write.service.spec.ts:2208`.

**Later — owned by C2 (Wave 6).** Removing the enum members needs the saved nodes gone first. Wave 6
only removes what the evidence shows is no longer reached, and C2 already removes legacy surfaces
behind a production check. C2's section 4 holds the steps: count the saved nodes live and in version
history, delete them and their edges through an internal endpoint with a dry run, then remove the
enum members, the MCP guards, the registry entries and the front filter. It is not part of A11.

## A `source` that feeds a node fails today

A `source` type is safe in the gate only if its value reaches the next node. Today it does not under
B4, and that is already true for `textBox`, which the gate accepts.

1. The workflow skips a passive node and marks it completed without a `node_executions` row
   (`process-flow.workflow.ts:126-134`).
2. It passes `completed: state.completed` to `buildNodeInputProjection` (`:174-188`).
   `completedUpstream` (`worker/src/ported/back/app-api/flux/node-input-projection.ts:75-93`) puts
   the skipped node in `completedSourceIds`.
3. `project-node-input.ts:233-236` throws `missingSourceError` for a completed source with no row,
   before the seed path is reached. The seed path (`fromSeed`, `:123-185`) would have delivered the
   right value.
4. A spec pins the throw: `project-node-input.integration.spec.ts:410-415`, with a `textBox` source.

So under B4, `textBox → commandTextNode` fails, and so would every `source` type once the gate
accepts it. A `visual` node with an edge out (`stickyNote` has 6 control edges on dev) fails the same
way. The back's loop does not hit this: it writes a row for
every non-Temporal node (`recordLegacyNodeStart`, `recordLegacyNodeSuccess` at
`flux.service.ts:2459`). Dev has `engine_in_workflow` off, so nobody hits it yet. This is traced
from code, not reproduced in a run.

**In.** Keep skipped `source` and `visual` nodes out of the `completed` set given to the
projection, so the projection walks past them: to the producer's row for a pass-through, or to
`fromSeed` for a fixed value. The skip set is the registry's `source` and `visual` classes, not
`NON_EXECUTABLE_TYPES`. The workflow still schedules and skips them, so a consumer behind a
pass-through keeps waiting for the producer.

**`tableProcessor` and `dynamicSettingsNode`.** The back's loop refuses worker projection when one
of them is connected (`backOnlyProjectionNodes`, `flux.service.ts:1050-1051`). B4 has no such check
(`flux.service.ts:3771`); today that is harmless only because the gate refuses both types. They
leave `BACK_ONLY_PROJECTION_NODE_TYPES` only when a worker projection test shows the seed delivers
their value (`edge-projection.ts:130` for `tableProcessor`, `:159` for `dynamicSettingsNode`). If it
does not, they stay in the list and the gate refuses any flow where `backOnlyProjectionNodes` is
non-empty.

## Integration types

`thirdPartyIntegration` and `hubSpotCRM` are classed `worker`, and **no path runs them inline**.

Today every real provider already goes to the worker. The front offers ten providers; nine of them
are in the registry's `integrationProviders` (`node-dispatch-registry.ts:155-166`). `hubSpotCRM`
always resolves to `hubspot`.

The tenth, `microsoft` (Microsoft 365), has nothing to migrate. In this node it is only the account
connection card (`supportsPull: false`, `supportsPush: false`,
`front/src/components/ThirdPartyIntegration/providers/microsoft/MicrosoftConfig.ts:12-13`). The
Microsoft work already runs in the worker: `pushData` and `pullData` for Excel, Word, PowerPoint and
OneDrive (`worker/src/modules/nodes/push-data/push-data.service.ts:76-87`), and delivery for Outlook
(`worker/src/modules/delivery/microsoft-email.sender.ts`). `google` is the same case: it is a
`pushData`/`pullData` provider, not a provider of this node. A node saved with either gets the
user-facing error from step 2 below.
The node's Run button calls `execute-single-node` (`ThirdPartyIntegrationNode.tsx:184`); the hook
that called the inline routes (`_legacyOnSubmit`, `:165`) is unused.

What still runs inline, or claims to:

| Path | When | What it does |
|---|---|---|
| Main loop, `flux.service.ts:4064` | provider not in the routed set (empty, unknown, or a different case) | `getAdapter` finds nothing, the node gets `errorMessage: Unknown provider`, and the next node receives empty text |
| `executeSingleNode`, `flux.service.ts:1767` | same | same |
| Legacy endpoint, `legacy-node-dispatch.ts:99` | any provider (`legacyEndpoint: 'accept'`) | inline, no provider check |
| `arrayNode` loop body, `flux.service.ts:4592-5015` | always | no branch for either type; the loop writes a success row with unchanged data (`:5056-5068`). A silent false success, not an inline run |

The routed set matches case exactly, but `getAdapter` lowercases (`integrations.service.ts:75`), so a
provider stored as `Slack` skips the worker and works inline.

Dev, from [`a11-q3-integration-providers.sql`](./a11-q3-integration-providers.sql): 37 nodes, 30
routed. The 7 that fall inline are 6 with an empty provider and 1 with `google`, which has no
adapter. All lowercase. None is in a flow with an `arrayNode`.

**In.**

1. Set `flowDispatch: 'worker'` and `execution: 'worker'` for both types, and regenerate
   `node-dispatch-contract.json`. This makes `isTemporalNode` true for both, so read the contract
   diff: `thirdPartyIntegration` gains `hasDispatchConflict`, and `hubSpotCRM` moves into the
   wrong-message set until step 3.
2. Replace the inline fallback at `flux.service.ts:4064` and `:1767` with a user-facing error that
   names the missing provider. Measure first: every node that falls inline today already fails, so
   each refusal must classify as correctly refused.
3. Set `legacyEndpoint: 'refuse-migrated'` for both and delete the `thirdPartyIntegration` case in
   `dispatchLegacyHandler` (C1's pattern).
4. Normalise the provider case in `resolveIntegrationProvider`, or show on production that no
   mixed-case provider is stored.

**Out — owned by A7.** The `arrayNode` loop body. A7 replaces the per-type branches in both back
loops with dispatch read from the registry, and its list of types the loop body misses names both
integration types (`TASK-A7-OBJECT-CALLER.md:72-83`). Once A11 sets them to `worker`, A7's loop body
dispatches them. Until A7 ships, a loop body with either type is a false success.
**Out.** The configuration-time routes `POST /integrations/:provider/pull|push|test-push`
(`integrations.controller.ts:389-452`), which the node's preview panels call. They are not a run path.

## Derived lists

**In.** Derive from the `execution` field: the three five-type passive copies, the worker's
`NON_EXECUTABLE_TYPES`, `BACK_ONLY_PROJECTION_NODE_TYPES` (back and the worker's ported copy) and
the B4 gate (every node `worker`, `source` or `visual`). `NON_EXECUTABLE_NODE_TYPES` keeps its three
types as a named subset (`visual` and `phantom`), still bound by its spec.

The worker imports nothing from back. It gets the class map the way it gets the projection code: a
dependency-free back file added to `PORTED_ENGINE_FILES` (`scripts/sync-ported-engine.ts`) and
checked by the ported-engine drift spec.

**Out.** Type lists that answer other questions: `DATA_SINK_TYPES` and `SIDE_EFFECT_TYPES`
(`scheduler.ts:23`, `:29`), the output set at `flux.service.ts:2085`, `node-output-reset.ts`,
`node-abort-capability.ts`, `agent-node-catalog.ts`, `agent-blueprint.normalizer.ts`,
`flow-doc.deterministic.ts` and the worker's `TEXT_PASSTHROUGH_TYPES`. They are not dispatch
verdicts.

## Drift and end-state specs

**In — the rule that prevents the next gap.** A drift spec fails when a type exists in the front's
`nodeTypes.tsx`, in `node-type-metadata.ts` or in the back's `NodeType` enum without a registry entry,
and when a derived list disagrees with the registry. The enum covers the deprecated types after they
leave the metadata. Back CI checks out one repo, so the spec reads the committed
`NODE_HANDLE_REGISTRY` (46 keys, generated from the front) and `NODE_TYPE_METADATA`, and does the
live front read only when `FRONT_REPO_PATH` or `../front` exists, like `node-handle-registry.spec.ts`.

**In — the end state as tests.** Three expected-failure tests (`it.failing`), each with the task
that turns it into a plain test:

| Assertion | Fails today because | Turned plain by |
|---|---|---|
| No type is classed `back` | the B6, A7 and A6b types exist | C2, when the last one leaves |
| The gate accepts a flow that holds a `sink` | the gate refuses `sink` | A13 |
| The gate accepts a flow that holds a `state` node | the gate refuses `state` | A14 |

`sink` and `state` stay classes after their tasks; only the gate's answer changes.

**In.** The drift spec also fails when a `back`, `sink` or `state` entry has no `handoffOwner`.

**In.** The 18 new entries need `workerModule: false` for `node-types-contract.spec.ts`, and the
`phantom` flag keeps its meaning: a type the registry names but no canvas offers.

## Verification

- **Negative control (required).** Add a type to the front list without a registry entry and watch
  the drift spec go red. Remove a derived list's import and restore a literal copy, and watch it go
  red again. Revert the projection fix and watch the `textBox → commandTextNode` workflow case go
  red. Restore the inline fallback and watch the integration refusal test go red. Remove one
  `handoffOwner` from a `back`, `sink` or `state` entry and watch the drift spec go red.
- **Projection fix.** Flip `project-node-input.integration.spec.ts:410-415` to expect seed delivery,
  and add `process-flow.workflow` cases for both `source` roles: a fixed `textBox`, a `varInputNode`
  and a `tableProcessor` feeding a worker node, and a pass-through `commandTextNode → textBox →
  commandTextNode` where the second node receives the first one's output.
- **Deprecated types.** With a flow that holds a saved `webNews` node: `get_agent` and
  `check_agent_integrity` still answer; `add_node` with `webNews` is still refused; a `PATCH` of that
  saved node through the API is still accepted; and B4's gate accepts the flow. `CoreNodeDisplay`
  and `CoreNodeDisplaySpaces` hide a saved node of each of the four, `webLocations` and
  `varInputForm` included. A repeat of the 2026-10-28 search finds the four only in the enum, the
  registry, the MCP guards and their specs, the front's deprecated-types constant and the fixture
  text.
- **Measure before refusing** (PLAN §3.3.2). Classify every stored production flow as eligible or
  ineligible for B4's gate before and after this task. Every flow that stays ineligible names the
  type that keeps it there, and that type has a task. Run `a11-q2`, `a11-q3` and `a11-q4` on
  production for the per-type counts, the integration refusals and the pass-through edges. The user
  runs production queries.

## Done when

Every canvas and MCP type has an `execution` class (`worker`, `source`, `visual`, `sink`, `state` or
`back`), and every `back`, `sink` and `state` entry names its owner; no hand-kept dispatch list
remains; a `source` delivers its value under B4, fixed or pass-through; no path runs
`thirdPartyIntegration` or `hubSpotCRM` inline; the four deprecated types are out of the MCP
metadata, the per-type tables and the seeder, registered as `visual` phantoms, and hidden by both
front views; the drift spec is green and has been seen red; the
before/after eligibility counts are recorded here; the workspace `CLAUDE.md` checklist "Adding or
changing a node type" names the `execution` field.

## Open items

1. **Saved nodes of the deprecated types.** Owned by C2 (Wave 6, section 4), after a production count on
   the live canvas and in version history; see **Deprecated types**, **Later**. Only then can the
   enum members go.
2. **Display nodes under B4 are not verified.** Under B4 nothing copies a producer's output into a
   display `textBox` or `richTextBox`, so the canvas may stop showing it once the flag is on. Check
   this on the local stack before the flag goes on in production. The front's autosave copy may
   still cover it, because the worker's live write updates the producer's row. The fix is step 2 in
   **Out — later steps**; it needs an owner, and C1 is the natural one because it removes the copy.

## What the 2026-10-28 validation changed

1. "Four copies of the passive list": the prefetch copy has 3 types on purpose; the other three have
   5.
2. "`tableProcessor` and `dynamicSettingsNode` read fields no writer stores in `outputData`": wrong.
   The back's loop stores the node's `data` as `outputData` (`recordLegacyNodeSuccess`). The worker
   never calls `backOnlyProjectionNodes`; only the back's loop does.
3. The class table left out `fluxObject`, `outputObjectNode`, `webTrends`, `globalStarter` and the
   control-flow types.
4. "No hand-kept type list remains" was too broad; it now names the dispatch lists and lists the
   ones out of scope.
5. `textBox` and `richTextBox` are value sources, not visual only, and most often pass-through
   displays of a producer's output.
6. Added: the projection fix (`textBox` already fails under B4), the integration inline removal, and
   the decision that `execution` sits next to `flowDispatch` until C2.
7. Decided: `none` splits into `source` (has a value, fixed or pass-through) and `visual` (no
   value), under the stateless model in **Classes**. Behaviour in A11 stays the skip.
8. Decided: `outputObjectNode` and `fluxObject` get their own classes, `sink` and `state`, instead
   of `back`, and every `back`, `sink` or `state` entry must name its owner. `back` now means only a
   step still waiting to move to the worker.
9. Decided: `webNews`, `webMedia`, `webLocations` and `varInputForm` are deprecated. A11 removes
   them from the MCP metadata and registers them as `visual` phantoms; they stay in the `NodeType`
   enum while saved nodes exist.
10. Decided: a search of `main` found the four in 17 files. A11 also removes their dead entries from
    the per-type tables in back, front and the worker's ports, removes the seeder's `webNews` node,
    and fixes the front filter that misses `webLocations` and `varInputForm`.

## What the 2026-10-29 implementation and review changed

These decisions came up while A11 was built and reviewed. Where one contradicts a section above,
this list wins until that section is rewritten.

1. **`tableProcessor` and `dynamicSettingsNode` leave the back-only projection list.** The worker
   projection test serves both from the run seed and matches the back's `modifyData`. A dev read on
   2026-10-29 (`a11-q5-backonly-shape.sql`) confirmed the shapes the tests use: every
   `dynamicSettingsNode` edge goes into a `commandTextNode`'s `modelSettings` handle (5 edges), and 2
   of the 3 `tableProcessor` edges come from a table with a selected column. The gate keeps only the
   class check. A drift test fails if a type still flagged `backOnlyProjection` is ever accepted by
   class.
2. **Every `visual` type is prefetch-safe.** `stickyNote`, `nodesGroup` and the four deprecated types
   join `comment`, `label` and `group`, so a decoration no longer costs a flow its prefetch
   eligibility. `NON_EXECUTABLE_NODE_TYPES` is now the `visual` class. The prefetch executor already
   skips these types without dispatching or writing anything (`prefetch-flow-executor.ts:109-113`).
   The production oracle declares the six additions in `MEASURED_PREFETCH_ADDITIONS`.
3. **Editor chain runs go to the worker.** In a chain run, `useTemporalFlowExecution` called
   `/process/single-node-legacy` for the types in the front's `LEGACY_SINGLE_RUN_NODE_TYPES`. The
   back already refuses `webSearch`, `mcpNode`, `reportBuilder` and `audioReaderNode` there, and
   since A11 also `thirdPartyIntegration`, so a chain run on those types got a 422. Rule: a type that
   has a worker module runs in the worker; a type that still needs the back stays there. All seven
   types moved to `MIGRATED_NODE_TYPES`, including `voiceBoxNode` and `commandContentNode`. The
   worker dispatches each one, the full run already sends each one to the worker, and the worker
   does what the back's inline twin did. The legacy list was then empty, and A11 deleted it with its
   helpers (`isLegacyRunnableNode`, `isRunnableNode`). No feature flag
   decides the outcome: only the node credit gate flags are read on this path, and they decide
   whether a refusal blocks or only logs, as on the legacy path. A back drift test reads the front
   `MIGRATED_NODE_TYPES` and fails when it lists a type without a worker module. Item 11 replaced the
   route: a chain step now goes through `/flux/execute-single-node`, not `/process/single-node`.
4. **`audioReaderNode` was already on the worker on every path.** A3 migrated it (shipped
   2026-10-02). The registry, the main loop, the `arrayNode` inner loop and `executeSingleNode` all
   send it to the worker, and its MCP schema matches the worker and the front. Nothing changed.
5. **Large Memory and the voice node dispatch a chain run once.** `LargeMemory.tsx`
   (`commandContentNode`) called the run hook and also ran its own `flowTrigger` effect, so a chain
   run dispatched twice and could charge twice. `AiAudioGenerator.tsx` (`voiceBoxNode`) imported the
   hook but never called it, and its own `flowTrigger` effect had already been removed, so a voice
   node in a chain run never ran. Both now use the hook as the only chain-run path, and a component
   test asserts exactly one dispatch per chain run; the manual Run button is unchanged. The chain
   run ignores Large Memory's `canceled`/`paused` guard, like every other node that uses the hook.
   Item 11 gives every chain step a 1-second delay again.
6. **Deprecated types are removed from the enum, and a saved one never blocks a flow.** The four
   leave the `NodeType` enum and become one deprecated list in the registry. A saved node of these
   types must not stop anyone from opening, reading, editing, saving, copying or restoring a flow,
   through the front, the back or the MCP:
   - The front shows a placeholder that says the node type no longer exists and lets the user delete
     it, instead of hiding it.
   - The back refuses to add a node of a deprecated type (`AddNodeDto` on `PATCH /flow/add-node`)
     and keeps accepting existing ones on every update, copy, version and import path:
     `IsNodeType()` accepts `NodeType` plus the deprecated list. `POST /flow` (create with nodes) and
     the external `api-flows` create keep accepting them too, because they import or copy existing
     flows (decided 2026-10-29).
   - The MCP marks the node as deprecated in `get_agent` and `get_run_nodes`, lists it in
     `check_agent_integrity` without failing `ok`, refuses `add_node`, `update_node` and
     `connect_nodes` on it, and keeps every other edit working, `remove_node` included.
   - Runs keep skipping it.
   - Nothing that describes the product to a person names the four any more: the MCP catalog, the
     SuperChat node guide and the docs. The registry, the front constant that draws the
     placeholder, the tests and the back `CLAUDE.md` record keep the names while saved nodes exist.

   C2 section 4 keeps the deletion of the saved nodes and of the placeholder.

   **Bug found on `main` and fixed here.** `toNodeEntity`
   (`back/src/app-api/folw/flow-node.service.ts`) resolves every node type through the MCP catalog,
   which already hid the four types. So a full save of a flow that holds one fails with "Unknown node
   type: webNews": every MCP write to that flow, and any full node save. The front hid the problem by
   filtering the node out on load, and its full-graph saves then deleted the node without telling
   the user. A11 makes `toNodeEntity` keep a deprecated type as stored, and
   `deprecated-node-persistence.spec.ts` covers the full save, the data-only save and the version
   paths with a `webNews` node.
7. **Provider normalisation lives where the provider is read.** The worker trims and lowercases the
   provider in the payload builder, so the adapter lookup and `payload.provider` see the same value.
   A spec binds the worker's adapter keys to the registry's integration providers.
8. **The apiV2 loop keeps its literal integration branch.** A registry-driven condition worked at
   run time, but `flux.service.worker-dispatch.spec.ts` finds each worker type's branch by its
   `node.type === '<type>'` literal (layer 7 of the node-type checklist). C2 deletes this loop.
9. **Deploy order.** Deploy the worker before the back, and the front with the back. A back without
    the A11 worker would send `source` and `visual` types that the old worker does not skip. The
    front's chain-run lists must match the back's legacy endpoint.
11. **Editor chain runs reach the next node.** "Run from start" and "Run from here" (node menu,
    `front/src/components/UI/Node/Node.tsx`) write `data.flowTrigger` on a node; the node runs, and
    its completion writes the trigger on the next node. The 2026-10-29 local E2E found that this
    chain stopped after the first node for every runnable type except `outputController`, on `main`
    too:
    - Why the hook types failed: they dispatched to `POST /process/single-node`, which passes no
      `execId` (`back/src/temporal/temporal.controller.ts`). The worker defaults it to `""`, and
      `generateExecutionLogsActivity` casts `''::uuid` and throws, on the success path too. The
      front never got `executionExecId`, so the hand-off never fired. On dev, `execution_logs`
      holds no row without `execId` in 14 days, which matches every such call failing.
    - Why the other types failed: `AiTextGenerator`, `WebSearch` and `ProcessCounter` ran a step
      through their own `flowTrigger` effect and `executeSingleNode`, which works, but never called
      `checkExecuteTrigger` afterwards. `McpClient` had no chain run at all.
    - Why "Run from here" also skipped a node: it set the trigger's `completed` to the node's index
      plus one, while "Run from start" uses the index and the hand-off adds one. Without a condition
      node in the flow, the node after the clicked one never ran.

    Decision (option 1 of two; the server-side "run from node" in `apiV2` and B4 was rejected as
    1-2 days of change to both schedulers): `useTemporalFlowExecution` is the only chain driver of
    the 18 components that call it.
    - Twelve other components still run their own chain step from a `flowTrigger` effect, without
      the token check: `OutputControllerNode`, `DecisionPaths`, `FlowCaller`, `TableProcessor`,
      `UsCensusNode`, `AiVideoGenerator`, `WebTrends`, `WebCrawling`, `WebAmazon`, `SecApiNode`,
      `ObjectCaller` and `TableOutput`. This is how `main` works; A11 does not change it. Why: those
      types are not in the D3 scope, and moving them needs the same per-component proof as the six
      covered here. A follow-up task decides it.
    - It dispatches through `executeSingleNode` (`/flux/execute-single-node`), the route the Run
      button uses. Why: it checks that the user may run the flow, creates the `node_executions` row,
      returns an `execId`, and honours the open version; `/process/single-node` did none of that.
      The route has no front caller now; a later task removes it.
    - A component with its own Run handler passes it as `runNode`, so a chain step behaves exactly
      like its Run button (flushing local field edits, session, notifications). Why: the
      run-flush rule; a chain step must not run on a stale prompt. For these components the hook
      handles only chain completions, so their Run button behaves as before.
    - Large Memory and the voice node pass `flushLocalEdits` instead of `runNode`: the hook saves
      a field edited during the wait, then dispatches. Why: the hook already handled every
      completion of these two nodes on `main`, so `runNode` would have changed their Run button;
      without the flush, a field edited in the last second before the step ran on its old value.
    - It waits 1 second before a step (plus the counter's wait). Why: the components that ran
      chains through their own effect used that delay, and it lets the previous step's propagated
      values save first; the hook also flushes pending saves before dispatching.
    - Every new trigger gets a `dispatchToken` that only the tab that created it can claim, once
      (`front/src/util/flowTriggerTokens.ts`, applied at the single exit of
      `flowTriggerDataHandle`). Why: a dispatching chain would otherwise run a trigger it did not
      create. Dev holds 12 saved nodes with an old `flowTrigger` (newest from June 2026), and a
      trigger saved by one tab reaches every other open tab. Neither one runs now.
    - The hook checks the token when the trigger arrives and claims it when the step fires. A step
      still waiting is cancelled when its trigger is cleared or replaced. Why: a node that remounts
      during the wait (`_remountKey`) claimed the token on the first mount and lost it with that
      mount, so the chain stopped there; and the end of a run clears every trigger, which must
      also stop a step that has not fired yet.
    - The issued-token set forgets the token of a trigger that is replaced or cleared, so it does
      not grow for the life of the tab.
    - The hook ignores a new trigger while a step of the same node runs, and does not hand off a
      completion that was already on the node when the step started. Why: a node that remounts in
      the middle of a chain would otherwise hand off its old result and also run, and a second
      hand-off would start a second run.
    - It keeps ignoring the dead `canceled`/`paused` flags. Why: nothing sets them any more, and
      the hook already ignored them by design (`useTemporalFlowExecution.deadRunFlags.test.tsx`).
    - A removed node type is not a chain step. `findConnectedNodes` walks through it but leaves it
      out of the step list, so the chain runs the node after it. Why: the placeholder keeps the
      node and its edges on the canvas and has no run, so the chain stopped there, while a server
      run skips it (item 15). On `main` the front dropped the node on load, so this never showed.

    Local E2E on 2026-10-29, in the editor with a 4-node chain and a dev flow copy that holds
    `webNews`, all passed:
    - "Run from start" and "Run from here" sent exactly one `POST /flux/execute-single-node` per
      step, in order, wrote one `node_executions` row per step, and passed each output to the next
      node. Nothing called `/process/single-node`, and the worker logged no `uuid` error.
    - The chain walked past the `webNews` placeholder without a request to it.
    - A trigger written into the database, with or without a token, did not run after a reload, and
      a second open tab sent no run request.
    - A failing step stopped the chain and showed the error; the next "Run from start" ran again.
    - The Run button, a single-node run and Run Agent each sent one request and started nothing
      downstream.

    Known and left as is: when a run ends, `FlowGlobalNode` (`FlowGlobalNode.tsx:603-620`) writes
    four status fields on every node, the placeholder included. The node keeps its type and still
    shows the placeholder; C2 deletes these nodes.

    Tests: the hook, the token module, `flowTriggerDataHandle` and one dispatch per chain step for
    six components. Ten deliberate mutations each fail at least one test: the "Run from here" index,
    no token issued, the claim check off, the running-step lock off, an old failure or an old
    completion accepted, the lock kept after a failed dispatch, the hook handling a component's own
    Run completion, a trigger passed on an ordinary Run completion, and the dead flags blocking a
    step.
12. **The versions list no longer fails without paging parameters.** `GET /flow/:flowId/versions`
    declared `page: number = 1`. The global `ValidationPipe` (`transform: true`) turns a missing
    value into `NaN`, so the default never applied and TypeORM failed with "skip value is not a
    number" (500). `DefaultValuePipe` plus `ParseIntPipe` now give page 1 and page size 10, and a
    value that is not a number falls back to the default. Found by the local E2E; the front always
    sends both values, so users did not see it.
13. **The editor and the API show the same message for a removed node type.** The placeholder said
    "no longer exists"; the API and the MCP said "was removed and can no longer be added or edited".
    The front now uses the back wording, and the back drift spec fails if the two diverge.
14. **The back `CLAUDE.md` section "Removed node types" stays** and describes every path that
    carries a saved node: full save, duplicate, versions, `POST /flow`, the run skip on both engines,
    the editor placeholder and the MCP marks.
15. **Full runs pass with the flag on and off.** Local run on 2026-10-29 of a dev flow copy that
    holds a `webNews` node: with `engine_in_workflow` off the run took the legacy loop; with it on,
    a flow without an output node took the B4 workflow, and a flow with `outputObjectNode` stayed on
    the loop because of that node, not because of `webNews`. Every node ran or was skipped without
    an error. The legacy loop writes an empty `node_executions` row for `webNews`, as it does for
    every node it passes without running; the B4 workflow writes none.
16. **The handle registry generator no longer depends on import order.** A11's new front imports
    made `node-handle-registry.spec.ts` fail: the generator followed every relative import from a
    node component and cut each closure at 80 files or depth 8, and the voice node's clone dialog
    imports the settings modal, which renders the integrations catalog. The closure now stops at
    `src/views`, `Modals`, `settings` and `Integrations` (a handle rendered there never attaches to
    a node), the limits are 400 files and depth 20, and a closure that reaches them throws instead
    of being cut. The largest closure is 199 files. The base front and the A11 front generate the
    same registry, and every entry the regeneration adds is already accepted by a catch-all on its
    type, so `connect_nodes` accepts the same handles as before.
17. **Deploy order: worker, then front, then back.** The back moves `thirdPartyIntegration` to
    `refuse-migrated` on the legacy single-node endpoint, and the front on `main` sends chain steps
    of that type there. The new front only calls `/flux/execute-single-node`, which the back on
    `main` already serves, so it can ship first. A tab that still runs the old bundle after the
    back deploy gets a refusal on that chain step until it reloads.

## Files

`back/src/shared/node-dispatch/node-dispatch-registry.ts`, `node-dispatch-registry.types.ts` and
`node-dispatch-contract.json` · `back/src/app-api/flux/engine-selector.ts` ·
`back/src/app-api/flux/prefetch/is-non-executable.ts` · `back/src/app-api/flux/flux.service.ts` (the
logging copy, the inline fallbacks) · `back/src/app-api/flux/node-input-projection.ts` ·
`back/src/shared/integration/integration-executable-node.ts` ·
`back/src/temporal/single-node-legacy/legacy-node-dispatch.ts` · `back/scripts/sync-ported-engine.ts` ·
worker `process-flow.workflow.ts`, `project-node-input.ts` and the ported files ·
`back/src/app-mcp/node-types/node-type-metadata.ts` (four entries removed) ·
`back/src/enums/node_types.enum.ts` (read; members stay) · the deprecated types' dead entries:
back `folw/helpers/node-target-fields.ts`, `shared/node-fields/node-referenceable-fields.ts`,
`folw/agentflow-doc.node-extractor.ts`, `app-mcp/node-layout.util.ts`,
`database/seeders/flow/data.ts`; front `util/nodeTypes.tsx`, `util/dataStoredToType.ts`,
`util/myFunctionsCoreDisplay.tsx`, `util/checkHandlesConnectable.ts`,
`components/UI/Node/nodeConstants.tsx`, `views/CoreNodeDisplay.tsx`, `views/CoreNodeDisplaySpaces.tsx`
