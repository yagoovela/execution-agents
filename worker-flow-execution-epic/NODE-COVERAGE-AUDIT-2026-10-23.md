# Node coverage audit — 2026-10-23

> **Snapshot.** This is dated evidence read at `back@a38fef57` and `worker@748d8dc9`. Its line
> numbers go stale; the task specs cite files and symbols (MAINTENANCE §3c). One correction after
> review: `thirdPartyIntegration` is dispatched by the full-run loop through
> `isWorkerRoutedIntegration`; its gap is the `arrayNode` loop body only.

**Question.** Does every node type the product can hold have a task in this epic that moves its
execution into the worker and deletes the back's copy, so that no node type still executes inline
when the epic ends?

**Answer.** No. 28 of 49 canvas types are covered. 21 are not: 13 need only a registry
classification, and 8 still execute in the back, or never execute, with no task that fixes it
(`sqlQuerier`, `animationNode`, `secApiNode`, `usCensusNode`, `webAmazon`, `outputObjectNode`,
`fluxObject`, `webTrends`). Four MCP-only types come on top. The largest gap is not a missing activity. The registry has no way to say
"this type does not execute". As a result, B4's gate (`canUseWorkflowForFlow`) refuses any flow
that holds a Data Input, a Data Output, a sticky note, a Small Memory or an integration node. Those
flows stay on the back's loop, and C2 can never delete that loop.

## Evidence base

Read-only. `git -C` into the product repos was refused in this session, so the code was read from
checkouts whose `HEAD` was matched to `origin/main` through the ref files:

| Repo | `origin/main` | Checkout read | Caveat |
|---|---|---|---|
| back | `a38fef57` | `.claude/worktrees/868mmj7fj-back` (branch `fix/868mmj7fj` = `a38fef57`) | Uncommitted edits, if any, could not be ruled out. The registry and `engine-selector.ts` match `b4-predeploy-back` and `wave5-back` apart from the flag constant. |
| worker | `748d8dc9` | `.claude/worktrees/868m8fnqe-worker` (detached at `748d8dc9`) | B4's `process-flow.workflow.ts` is **not** on worker `main`. It exists only on `wave5-worker`. |
| front | `8c52b2d5` | `.claude/worktrees/868m8fnqe-front` | No checkout sits at `origin/main`. `nodeTypes.tsx` is byte-identical (md5) in 32 checkouts, including `~/enhanced/front`, so it may lag `origin/main`. |

Prefixes: `back:`, `worker:`, `front:` are the checkouts above. Epic files are relative to this
folder.

## 1. Every node type

The sources are `front:src/util/nodeTypes.tsx:64-112` (46 types),
`back:src/shared/node-dispatch/node-dispatch-registry.ts:6-259` (35 types, three of them phantom),
and `back:src/app-mcp/node-types/node-type-metadata.ts` (four extra MCP-only types). The union is 49
canvas types plus four MCP-only types.

Registry columns: `flowDispatch` (W = `worker`, I = `inline`, — = not registered),
`legacyEndpoint` (mig = `refuse-migrated`, uns = `refuse-unsupported`, mut = `refuse-mutating`,
acc = `accept`), `prefetchSafe`, `workerModule`. "Module" is the directory under
`worker:src/modules/nodes/`. "BO" marks membership of `BACK_ONLY_PROJECTION_NODE_TYPES`
(`back:src/app-api/flux/node-input-projection.ts:6-14`).

### 1.1 Worker-dispatched types (23)

| Type | Registry | Module | Task | State |
|---|---|---|---|---|
| `commandTextNode` | W mig N Y | text-generator | pre-epic (analysis README §1.1, line 22) | Covered |
| `scripting`, `mathFunction`, `outputController` | W mig N Y | scripting, math-function, display-box | pre-epic | Covered; dead method bodies tracked by C1 (`TASK-C1:40-49`) |
| `apiCaller`, `counterNode` | W mig N Y | api-caller, counter | pre-epic | Covered (see §2.3 for the loop body) |
| `mcpNode` | W mig Y Y | mcp | pre-epic (analysis §12.1) | Covered |
| `voiceBoxNode`, `commandContentNode` | W acc Y Y | voice-generator, large-memory | A2 (`TASK-A2:29-36`) | Legacy-endpoint twin → C1 (`TASK-C1:23-38`) |
| `webSearch`, `pullData`, `pushData` | W mig Y Y | web-search, pull-data, push-data | A2 | Covered; dead legacy arms → C2 (`TASK-C2:52-58`) |
| `webCrawling` | W uns Y Y | web-crawling | A2 | Covered; refusal message only (`TASK-C2:42-50`) |
| `audioReaderNode` | W mig Y Y | audio-transcriber | A3 (`PLAN.md:171`) | Covered |
| `sqlQuerier` | W mig Y Y | sql-querier | A3 (`PLAN.md:171`) | **Partial** — §2.2 |
| `reportBuilder` | W mig Y Y | report-builder | A4 (`PLAN.md:172`) | Covered (see §2.3) |
| `imageGenerator` | W mig Y Y | image-generator | A5 (`PLAN.md:173`) | Covered |
| `imageReaderNode` | W mig N Y | image-reader | A8 / D24 (`STATUS.md:48`) | Covered; full-run branch is live (`back:src/app-api/flux/flux.service.ts:4223-4224`) |
| `fileSave` | W mig N Y | file-save | A6 stage 1 (`TASK-A6:50`) | Covered (see §2.3) |
| `webAmazon`, `secApiNode`, `usCensusNode`, `animationNode` | W mig N Y | web-amazon, sec-api, us-census, ai-video-generator | A6 (`TASK-A6:49,60,64`) | **Partial** — §2.3 |

### 1.2 Inline control flow and mutation (5)

| Type | Registry | BO | Task | State |
|---|---|---|---|---|
| `conditionNode` | I mut N N | — | B6 (`TASK-B6:3-4`) | Covered |
| `arrayNode`, `fluxBox` | I mut N N | yes | B6 | Covered |
| `libraryNode` | I mut Y N | yes | B6 | Covered |
| `nodesBox` | I mut Y N | yes | A7 (`PLAN.md:175`, `TASK-A7:51-52`) | Covered for the node. Chat path excluded (`TASK-A7:46-47`) — §2.5 |

### 1.3 Types the worker runs but the registry calls inline (2)

| Type | Registry | Module | Task | State |
|---|---|---|---|---|
| `thirdPartyIntegration` | I acc Y Y | third-party-integration | A2, A10 (`PLAN.md:178`) | **Partial** — all ten providers with a back adapter (`back:src/app-api/integrations/adapters/`) are worker-routed (`registry:155-166`), but `flowDispatch` stays `inline` — §2.1 |
| `hubSpotCRM` | I uns N Y | third-party-integration | pre-epic (dedicated provider `hubspot`, `registry:177-185`) | **Partial** — same as above |

### 1.4 Run entry, run sink and storage (4)

| Type | Registry | BO | Back work at run time | Task | State |
|---|---|---|---|---|---|
| `globalStarter` | I uns N Y (enum only, no module) | — | none; whitelisted (`back:src/app-api/flux/engine-selector.ts:5-11`) | — | Covered by the whitelist; stranded registry entry is cosmetic |
| `varInputNode` | — | — | binds run inputs before the loop (`flux.service.ts:3582`); A8 removed extraction | A8 (`TASK-A8:3-4`) | **Gap** — passive but unregistered, so B4 refuses the flow |
| `outputObjectNode` | I uns N Y (enum only, no module) | — | sink: receives producers' output, feeds the API/chatbot reply and A9's delivery | A9 covers delivery only (`TASK-A9:699-703`) | **Gap** — §2.4 |
| `fluxObject` | — | yes | writes entries after every producer (`flux.service.ts:1242-1282`, called at `:5010` and `:5291`); loads chat sessions before the loop (`:3343-3390`); persists the assistant answer after the run (`:5843`) | **NO TASK** — `PLAN.md:317-319` calls it configuration-time | **Gap** — §2.5 |

### 1.5 Projection-only, front-driven and passive types (15)

| Type | Registry | BO | Task | State |
|---|---|---|---|---|
| `tableProcessor` | — | yes | `PLAN.md:324` (transform out of scope); B6 only checks (`TASK-B6:133-134`) | **Gap** — projection source (`back:src/app-api/folw/helpers/edge-projection.ts:130`) |
| `dynamicSettingsNode` | — | yes | B6 only checks (`TASK-B6:133-134`) | **Gap** — projection source (`edge-projection.ts:159`) |
| `webTrends` | — (no module) | — | A6 stage 1 (`TASK-A6:48`) | **Gap** — A6 shipped without it and recorded no decision; `front:src/components/nodes/WebTrends.tsx:6` still calls `SerpService` |
| `textBox` | — | — | `PLAN.md:317` (inert) | Whitelisted by B4, but unregistered |
| `richTextBox`, `stickyNote`, `nodesGroup`, `outputTable`, `storedDataCaller`, `deepRefNode`, `nodesAdd`, `mediaBox` | — | — | `PLAN.md:317-319` (inert) | **Gap** — classification only: nothing executes, but B4 refuses the flow |
| `comment`, `label`, `group` | I uns Y N, phantom | — | A1 / D5 (`STATUS.md:37`) | Covered; in `NON_EXECUTABLE_NODE_TYPES` |

**MCP-only types.** `webNews`, `webMedia`, `webLocations` and `varInputForm` have entries in
`node-type-metadata.ts` (lines 1647, 1591, 1615, 479), no front component and no registry entry. A
flow an agent builds with one is refused by B4 and skipped by the back's loop. No task owns them.

## 2. Types that run in the back outside the scope a task claims

### 2.1 The gate has no notion of "does not execute"

`canUseWorkflowForFlow` accepts a type only when it is in a five-type whitelist or has
`flowDispatch: 'worker'` (`back:src/app-api/flux/engine-selector.ts:5-28`). An unregistered type
returns `false`. So 14 front types, the four MCP-only types, the two integration types and
`outputObjectNode` each disqualify a whole flow. Every API flow has a Data Input or a Data Output,
so on today's `origin/main` the flag can route almost no real flow.

The "does not execute" rule now lives in four hand-kept copies:
`NON_EXECUTABLE_NODE_TYPES` (3 types, `back:src/app-api/flux/prefetch/is-non-executable.ts:1-5`),
`WORKFLOW_SAFE_NON_WORKER_TYPES` (5, `engine-selector.ts:5-11`), a literal copy inside `apiV2`'s
logging (`flux.service.ts:3774-3780`), and the worker's `NON_EXECUTABLE_TYPES` with a "keep in sync"
comment (`wave5-worker:src/modules/temporal/workflows/process-flow.workflow.ts:33-45`). This is the
drift A1 existed to end.

### 2.2 `sqlQuerier` still runs inline on a full run

The registry says `worker`, and a single-node Run reaches the worker. The back's full-run loop
still calls the inline `sqlQuerierNode()` in the main loop (`flux.service.ts:5241`) and in the
`arrayNode` body (`:4923`). The handler is at `:9447`. A3's Done-when — "the inline twins are gone"
(`TASK-A3:58-61`) — is false for this type.

### 2.3 Types the back's loop never reaches

`STATUS.md:46` records that the main loop has no branch for `animationNode`, `secApiNode`,
`usCensusNode` or `webAmazon`, and no task owns the fix. This audit confirms it on `a38fef57`: none
of the four appears in `flux.service.ts`. The `arrayNode` loop body is worse. Its branch list
(`:4580-4967`) also lacks `thirdPartyIntegration`, `hubSpotCRM`, `outputController`, `reportBuilder`,
`counterNode` and `fileSave`, so a loop body silently skips them. PLAN §3.4 point 3 requires both
loops (`PLAN.md:105-108`). This also breaks B4's order-equivalence check (`TASK-B4:73-75`): the
workflow dispatches these types, and the back's loop skips them.

### 2.4 `outputObjectNode` is delivery plus a sink

A9 moved email and callback delivery to the worker. It states that the registry and the
single-node path "do not apply: delivery is not a node type" (`TASK-A9:699-703`). It hands the
rest to B4: "when B4 lands, `deliverRunOutputs` becomes its last step" (`TASK-A9:449`). B4's spec
never mentions it (`TASK-B4:27-66`). Nobody owns materialising the Data Output's value from its
upstream rows in a workflow run, which is what the API reply, the chatbot answer and delivery all
read. The worker enum has `OUTPUT` with no activity (`worker:src/modules/temporal/workflows/node-activities.ts:30-47`).

### 2.5 `fluxObject` (Small Memory) is not configuration-time

`PLAN.md:317-319` excludes `fluxObject` as a configuration-time type. The code contradicts that.
After every node, `persistSmallMemoryEntries` writes the memory node's `entries` and
`userSessionsChat` to its live row (`flux.service.ts:1242-1282`). The run also reads chat sessions
before the loop (`:3343-3390`) and appends the assistant answer after it (`:5843`). A7 explicitly
leaves the chat path out (`TASK-A7:46-47`), and E1 does not cover it. In a worker run, nothing
performs these writes.

## 3. Gaps and proposed homes

| Type(s) | Why not covered | Proposed home | Wave now | Should have been |
|---|---|---|---|---|
| `varInputNode`, `textBox`, `richTextBox`, `stickyNote`, `nodesGroup`, `outputTable`, `storedDataCaller`, `deepRefNode`, `nodesAdd`, `mediaBox`, MCP-only four | No task; `PLAN.md:317-319` excludes them from migration, correctly, but nothing classifies them, so B4/B5 refuse their flows | **New A11** | 4, before B4's flag flip | 2, with A1 |
| `thirdPartyIntegration`, `hubSpotCRM` | Execution moved (A2, A10); registry still says `inline` | **A11** | 4 | 3, with A10 |
| `globalStarter`, `outputObjectNode` registry entries | Stranded entries with no execution meaning | **A11** (classification), A13 (behaviour) | 4 | 2 |
| `tableProcessor`, `dynamicSettingsNode` | B6 only checks the BO list (`TASK-B6:133-134`); `PLAN.md:324` scopes out the transform, not the projection | **A11**: classify as passive; prove the worker's ported projection reads them from the seed snapshot; drop them from BO | 4 | 4, with B3b |
| `sqlQuerier` (full run), `animationNode`, `secApiNode`, `usCensusNode`, `webAmazon`, loop-body misses | A3 and A6 marked shipped without §3.4 point 3 | **New A12** | 4, before B4's order-equivalence run | 3, inside A3/A6 |
| `outputObjectNode` | A9 covers delivery only; B4 does not pick up the hand-off | **New A13** | 4, with B4 + E1 | 4, in B4's scope |
| `fluxObject`, chat path of `nodesBox` | Excluded by `PLAN.md:317-319` on a wrong census; A7 excludes the chat path | **New A14** | 5, after A7 | 3 (census) |
| `webTrends` | A6 stage 1 lists it; A6 shipped without it or a decision | **New A6b** | 4 or 5, before B5's measurement | 3, in A6 |

### Proposed tasks

1. **A11 — Register every canvas node type.** Depends on A1 and D2. Add an execution class to every
   registry entry, for example `executes: 'worker' | 'back' | 'none'`. Register the 14 missing front
   types and decide the four MCP-only ones. Flip `thirdPartyIntegration` and `hubSpotCRM` to
   `worker`; the provider gate already refuses an unknown provider. Derive
   `NON_EXECUTABLE_NODE_TYPES`, `WORKFLOW_SAFE_NON_WORKER_TYPES`, the `apiV2` logging copy, the
   worker's `NON_EXECUTABLE_TYPES` (through the contract) and `BACK_ONLY_PROJECTION_NODE_TYPES`
   from it. Measure with B5's procedure (`TASK-B5:65-67`): classify every stored flow as eligible or
   refused, and name the type that refused it. It must land before the B4 flag flips, or the flag
   routes only toy flows.
2. **A12 — Reach every worker type from both loops.** Depends on A1. Replace the per-type branches
   in the main loop and the `arrayNode` body with one branch derived from `dispatchesToWorker` and
   `isWorkerRoutedIntegration`. Delete `sqlQuerierNode()`. A negative control per loop: remove the
   branch and watch a headless run skip the node. It must land before B4's order-equivalence
   corpus, because the corpus otherwise diverges on these types. It is still needed after B4,
   because the back's loop stays the default until C2.
3. **A13 — The Data Output as the workflow's sink.** Depends on B3b, A9 and B4. Build the Data
   Output's value from its upstream rows in the workflow. Make `deliverRunOutputs` the workflow's
   last step (`TASK-A9:449`). Return the run result from it, and flip the registry entry.
4. **A14 — Small Memory and chat state in the worker.** Depends on B1, B4 and A7's session-state
   callback (`TASK-A7:27-28`), extended to the `chat` scope. Move `persistSmallMemoryEntries`, the
   chat pre-load and the post-run chat append. Prove parity on stored chat sessions. Remove
   `fluxObject` from the BO list.
5. **A6b — `webTrends`: give it execution or retire it.** Depends on A1 and S6 (shipped). Same
   three-part scope as A6 (`TASK-A6:25-35`). Record the decision in the registry either way.

## 4. Exit criteria

The global rule is written, in three places:

- B6's Done-when ends with "no executable node type remains inline" (`TASK-B6:122-125`).
- C1's Done-when: "No executable node type has two implementations; `addConnectToNodes` has no
  callers on the run path" (`TASK-C1:94-95`).
- C2: "Once every executable type runs in the worker, this endpoint accepts nothing"
  (`TASK-C2:24-25`). B5 gates on "every executable node in the flow is a migrated type, read from
  the A1 registry" (`TASK-B5:27-29`). Wave 6 promises "one implementation of each node, one
  dispatch registry, one engine" (`DELIVERY-PLAN.md:236`).

**Nothing enforces it.** None of these defines "executable", and the registry has no field for it.
`summary.inlineOnly` in `node-dispatch-contract.json` mixes control flow, phantoms, the sink and the
integration types. The contract specs compare the registry with the worker enum only
(`back:src/shared/node-dispatch/node-types-contract.spec.ts:43-59`) and with
`NON_EXECUTABLE_NODE_TYPES` (`node-dispatch-registry.spec.ts:360-373`). No spec reads
`front/src/util/nodeTypes.tsx` or `node-type-metadata.ts`. A type missing from the registry
therefore slips through every check: today that is 14 front types and four MCP-only types. D2's
negative control only covers a type added to the worker enum (`TASK-D2:47-48`).

Two smaller holes in the exit criteria:

- No Done-when deletes the back's DAG loop. B4 defers it to "C1/C2" (`TASK-B4:65-66`), and
  `DELIVERY-PLAN.md:190` says Wave 6 deletes it. C1 and C2 only imply it through "no migration flag
  … remains" (`TASK-C2:96-97`).
- The inline handler for an executable type can be live while the registry says `worker`
  (`sqlQuerier`), and the contract's `inlineTwin` flag cannot tell a live path from a dead body.

**Proposal.** A11 adds two specs:

1. A drift spec that reads the front's `nodeTypes` keys and the MCP metadata keys, and fails when
   either names a type the registry does not register.
2. The end-state invariant as an `it.failing`, following A1's pattern (`TASK-C1:29-36`): "every
   registered type has `executes` in `{worker, none}`". C2 turns it into a plain `it` when the
   back's loop is deleted. Add that deletion to C2's Done-when by name.
