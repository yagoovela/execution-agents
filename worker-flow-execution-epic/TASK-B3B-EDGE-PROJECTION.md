# B3b — Edge projection in the worker

**Goal:** the worker builds a node's `*Data` arrays from its upstreams' `node_executions` rows, so
that no node needs a round trip through the back to become runnable.

**Depends on:** B2, B3. **Blocks:** B4. **Split out of B3 on 2026-10-09** — see
[Why this is its own task](#why-this-is-its-own-task).

## What it is

When a node completes, the back walks the edges leaving it and, for each one, decides **which field
of the source node the edge's handle stands for**, then writes a `{ id, label, text }` entry into the
target's `*Data` array (`addConnectToNodes` → `modifyData` → `givingDataToNode` / `getOutputByType`,
`back/src/app-api/folw/helpers/helpers.ts:20`, about 1,070 lines). Examples from `origin/production`:

| Source and handle | What becomes `text` |
|---|---|
| `scripting` · `output` | `data.result` |
| `scripting` · `console` | `data.console`, lines joined with `\n` |
| `commandTextNode` / `outputController` / `reportBuilder` · `fileLink` | `data.fileLink.src`, or `'No Link generated'` |
| `commandTextNode` · `logs` | `data.logs`, or `'No Logs generated'` |
| `varInputNode` · `outputExtractText` | `data.extractText` |

Around it: `buildHandleEntryIdForWrite` gives the entry an edge identity, suffixed `#N` inside a loop
iteration (read from `loopIterationContext`, an `AsyncLocalStorage`); `reconcileEntries` drops the
entries of edges that are no longer connected. It is called from fourteen places in
`flux/flux.service.ts` (`addConnectToNodes` at `:831`, `:865`, `:3304`–`:3388`, `:4172`, `:5329`,
`:5806`–`:5871`; `modifyData` at `:1480`, `:3868`, `:4508`, `:5657`).

It is **field selection by handle**, not a content transformation. The only formatting in it is the
console join and the default strings, and those are product behaviour that must stay byte-identical.

## Why this is its own task

B3 was first scoped with this left in the back, on the reading that it was a transform. It is not:
it is a pure function of the edge, the source's output and the loop iteration, and it lives in the
back only because the loop and its in-memory node list (`nds`) live there.

- **The worker already has its inputs.** Both writers store the node's data in
  `node_executions.outputData`: the back's legacy path (`recordLegacyNodeSuccess`,
  `flux.service.ts:2010`) and the worker (`persist-node-outcome.ts:9`). `result`, `console`,
  `fileLink`, `logs` and `extractText` are on the upstream's row.
- **B4 needs it gone from the back.** Once the loop is a workflow, the back no longer holds `nds`.
  Leaving the projection there turns it into a back callback per node, which is the round trip B4
  exists to remove.
- **It is too big to ride inside B3.** About 1,070 lines with branches per source type, inside a
  2,337-line `helpers.ts` that is not pure (it imports `flux/execution-budget` and
  `loop-iteration-context`). B2 already had to extract `singleConditionCheck` from the same file for
  the same reason.

## Scope

**In.** Extract the projection (`getOutputByType`, `givingDataToNode`, `modifyData`,
`addConnectToNodes`, `buildHandleEntryIdForWrite`, `reconcileEntries` and what they need) from
`helpers.ts` into a pure module, behaviour-neutral, the way B2 extracted `singleConditionCheck`. The
back keeps importing it from there.

**In.** Port it to the worker through B2's mechanism: `pnpm sync:ported-engine` copies it
byte-for-byte into `worker/src/ported/back/`, and both drift tests cover it. Import the rule; never
restate it.

**In.** The loop iteration becomes an explicit argument (index and body node ids), not an
`AsyncLocalStorage` read, so the worker can call it.

**In.** On B3's flag, the worker builds the target's `*Data` from the upstreams' rows, found through
the run's completed `{ nodeId: execId }` map B3 introduces, and B3's placeholder resolution then runs
over the result. The back stops writing the projected `*Data` into the input on that path.

**Out — branches whose source data lives only in the back's memory.** `nodesBox`
(`objectCallerData`), `arrayNode`, `fluxObject`, `outputObjectNode`, `libraryNode` / `fluxBox` and
`globalStarter`. They are control-flow or inline-only types, B6's territory. A flow with an edge from
one of them stays on the back's path; that gate is a refusing rule (below).

**Out.** The front's own copy of the projection in `front/src/util/autosave/` (the editor computes
the same entries client-side). It is a third copy and a drift risk worth its own look, not part of
this task.

## Verification

- **Negative control (required).** Change one branch in the ported copy (for example the `console`
  join separator) and confirm the drift test goes red. Then remove the upstream's `outputData` row on
  the new path and confirm the node fails loudly instead of receiving an empty entry.
- **Equivalence over real flows.** For a corpus of stored runs, build every node's `*Data` both ways
  (back in memory vs. worker from rows) and diff: every source/handle pair present in the corpus, the
  default strings, loop iterations (`#N` ids) and an edge disconnected between runs.
- **Measure before refusing** (PLAN §3.3.2). The gate that keeps flows with a back-only source on the
  back's path refuses flows. Classify every refusal against stored flows and drive
  refused-although-it-works to zero.

## Done when

On B3's flag, the worker builds every `*Data` entry from references for flows without back-only
sources; equivalence is proven over stored runs; the projection exists once, extracted and ported
with a drift test; and the back's path is still present and selectable.

## Files

`back/src/app-api/folw/helpers/helpers.ts` · `back/src/app-api/folw/contants.ts` (`addConnectToNodes`) ·
`back/src/app-api/folw/helpers/loop-iteration-context.ts` · `back/src/app-api/flux/flux.service.ts`
(the fourteen call sites) · `back/scripts/sync-ported-engine.ts` and its manifest ·
`worker/src/ported/back/` · worker-side projection (new)
