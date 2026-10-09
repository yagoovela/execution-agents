# B3 — The consumer resolves its own input

**Goal:** stop the API from pre-chewing every node's input. Each node reads its upstream outputs
by reference and resolves its own placeholders.

**Depends on:** B1, B2. **Blocks:** B3b, B4. **Decision D2:** answered 2026-10-09 — the prefetch
executor is a stopgap; resolution moves to the worker on B2's ported substitution service.

## Why — and what already exists

**Corrected 2026-10-09**, against `back@origin/production` and `worker@origin/main`. The first
version of this section (2026-09-02) described the prefetch executor as the part of this task that
was already built. Four of its claims were wrong, and the corrections change the scope:

- **The prefetch executor does not resolve on the consumer side.** It resolves in the back and then
  dispatches through the back's in-process handlers (`dispatchLegacyHandler`, `flux.service.ts:1593`).
  It is a second loop inside the back, not a worker-side resolver, so "relocate it" was never a move.
  `schemaForNode` is a local variable in `runPrefetchFlow`, not a function, and `OutputPointer` is a map
  held in the back's process memory.
- **`openNodeExecution` is not the apiV2 path.** Its only production caller is the editor's
  single-node Run (`single-node-legacy.service.ts:107`). On apiV2 the input is written by
  `processNodeViaTemporal` → `createNodeExecution` (`flux.service.ts:738`, `:786`).
- **Resolving an input is two different steps, and B3 owns one of them.**
  - **Placeholder resolution (fetch).** Three operations, all of them "look up a value by reference
    and put it in place":
    `applySubstitutionToObject` walks the whole node `data`, including the strings inside the
    `*Data` arrays, and replaces `{{...}}` (`flux.service.ts:3599`); `resolveTextDataFromSchema`
    fills the `text` of every `{id}` entry in `REF_ARRAY_FIELDS` from the upstream with that id
    (`:775`); `syncPassthroughsFromNodes` / `propagateToPassthroughs` let passthrough nodes carry their
    upstream's value.
  - **Edge projection (field selection by handle).** When an upstream completes,
    `addConnectToNodes` → `givingDataToNode` / `getOutputByType` (`folw/helpers/helpers.ts:20`,
    about 1,070 lines) write an entry into the downstream's `*Data` arrays, choosing which field of the
    upstream each handle stands for (`result`, the console lines joined, `fileLink.src`,
    `extractText`, …). It was first read as a transform and left in the back; it is a pure selection
    over data already stored in `node_executions.outputData`, so it moves to the worker too — in its
    own task, **B3b**, because it is about 1,070 lines inside a `helpers.ts` that is not pure.
- **Nothing fails loudly today.** `replacePlaceholders` leaves an unknown key as the literal
  `{{x.y}}`; `clearRunOutputForSeed` blanks every output at run start (`:3035`), so a reference to an
  upstream that has not run in this run resolves to `''`; `loadOutputsByRefs` skips a ref with no
  pointer. The `''` is current, relied-on behaviour (a branch that did not run), not only a defect.

## Decision D2 — the prefetch executor is a stopgap

**Answered 2026-10-09.** Both halves of A1's measurement are now in hand:

| Question | Answer | Source |
|---|---|---|
| Stored flows that satisfy the whitelist | **78 of 15,984** production flows (0.5%) | A1, back PR #1986 |
| Runs with `FLUX_EXEC_MEMORY_MODE=prefetch` | **About 73 minutes, ever.** The SSM parameter `FLUX_EXEC_MEMORY_MODE_PROD` was `prefetch` from 2026-08-20 15:01 to 16:14 (-03:00) and has been `legacy` since. Dev and staging are `legacy` too. | `aws ssm get-parameter-history`, read-only, 2026-10-09 |
| What it saved | Nothing measurable: it has not carried traffic | follows from the row above |

A1 reported the second row as unverifiable because CloudWatch Logs Insights is not enabled. The
parameter history answers it without the logs. The variable is also missing from `.env.example` and
from the env-var docs, which is why nobody could see it.

The executor runs in the back, covers 0.5% of flows by construction (the registry marks the core
node types `prefetchSafe: false`), and has never been exercised in production. **Resolution moves to
the worker on B2's ported `NodeReferenceSubstitutionService`.** The prefetch path is retired by C2. Its
pure pieces, `scanPlaceholderRefs`, `loadOutputsByRefs` and `buildAliasIndex`, may be reused as
libraries where they help.

## Scope

**In — placeholder resolution moves to the worker, and the back stops doing it.** On the new path
the back writes the node's data with its placeholders **unresolved**, and the worker runs the three
fetch operations above, including on placeholders that arrive inside the `*Data` arrays. Every
placeholder that resolves today must resolve to the same value after the move. If one stops
resolving because the worker cannot fetch what it points at, that is a defect of this task, not an
accepted loss.

**In — the worker fetches only.** It loads what it needs through a reference: a `node_executions`
row, or a claim-check payload in S3 through `get-payload` (the boundary S5 authorises). It does not
transform, extract or OCR what it fetched — extraction is A8's, and an OCR node is out of the epic
(D24). Confirmed with the requester on 2026-09-02, and refined on 2026-10-09: fetch-then-substitute is
fetch. Selecting the field a handle stands for is also fetch, and moves in B3b.

**In — a minimal per-run snapshot.** Today's substitution schema is built at run start from every
node in the flow (`generateSchemaFromNodes`, `:3423`), so a placeholder can point at a node that does
not execute in this run (a static text node, a node off the path) and resolve from its content. The
worker cannot read that from the live `flows_nodes` row: concurrent runs write it. The back records
the run-start base once per run and hands the worker a reference to it. The worker builds the schema
from that base plus the outputs of the upstreams that completed in this run, applied **in completion
order**, because label aliases are last-write-wins and the order decides which node a shared label
names. The snapshot holds only what substitution reads. It does not carry chat history or starter
files; those reach the node through the input the back still writes.

**In — a run-scoped way to find upstreams.** `node_executions` has no indexed run key (`runId` lives
in `metadata` only, and B1 adds none). The dispatch carries the run's completed `{ nodeId: execId }`
map, ids only. That is the same shape B4's workflow will hold in its state, so B4 inherits it
instead of replacing it.

**In.** `node_executions.input` changes meaning. It stops being a **precondition for running** and
becomes a **record of what the node ran with**. The worker writes the resolved input back to it. Run
history (`execution_logs.service.ts`) and the front (`NodeIoView.tsx`, `NodeExecutionsModal.tsx`) read
it.

**In — behind a flag, default off.** The back's resolution stays present and is the default. One
flag selects worker-side resolution.

**Out — edge projection, to B3b.** In B3 the back keeps building the `*Data` entries
(`getOutputByType`) and writes them into the input with their placeholders unresolved; B3b moves that
step to the worker on the same flag. B4 depends on both.

**Out.** Removing the back's resolution path — PLAN §3.2; this step must be reversible above all
others. Control-flow and inline-only node types (B6). Retiring the prefetch executor (C2).

**Reach.** The 17 node types the dispatch contract routes to the worker, plus `thirdPartyIntegration`
and `hubSpotCRM` when routed per provider. Every one of them reads its input through `fetchNodeRow`.

## Verification

- **Negative control (required).** On the new path, delete or withhold the `node_executions` row of
  an upstream that **did** complete in this run, and confirm the node fails loudly instead of
  resolving to `''` or to the literal placeholder. This is the failure the move can introduce, and it
  must never look like a prompt bug.
- **Today's empty results stay empty.** A reference to an upstream that did not run in this run
  resolves to `''` today and must still resolve to `''`. Before turning anything into an error,
  measure against stored flows how many rely on it (PLAN §3.3.2). A false failure is worse than the
  defect it fixes.
- **Output equivalence over real flows.** For a corpus of stored runs, resolve each node's input both
  ways and diff the full `data`, `*Data` arrays included. Cover all three key shapes (`nodeId`,
  normalised ref-key, lowercased label alias), passthrough nodes, a placeholder inside a `*Data`
  entry, and the alias collision where two nodes share a label. The service and the prefetch
  `alias-index` resolve that collision differently; the worker must match the service, which is what
  production runs.
- **Concurrency.** Two runs of the same flow with different starter inputs: each node resolves its own
  run's values. That is the clobber the snapshot exists to prevent.
- **Measure before refusing** (PLAN §3.3.2). Whatever gate decides "this flow can resolve worker-side"
  is a refusing rule. Classify every refusal against real stored flows and drive
  refused-although-it-works to zero.

## Done when

Behind a flag defaulting off, the worker resolves every placeholder of a node's input from references
(the run snapshot, its upstreams' `node_executions` rows, claim-check payloads), with no
substitution in the back. Equivalence is proven over stored runs. The back's path is still present
and selectable. The `*Data` entries are still built by the back until B3b lands.

## Files

`back/src/app-api/flux/flux.service.ts` (`processNodeViaTemporal`, the substitution at `:3599`, the
`REF_ARRAY_FIELDS` loop at `:775`) · `back/src/app-api/flux/ref-array-fields.ts` ·
`worker/src/modules/nodes/shared/fetch-node-row.ts` · `worker/src/ported/back/` (B2's copies) ·
`back/src/shared/ported-engine/` (the sync manifest, if `ref-array-fields.ts` joins it) ·
worker-side resolution (new) · the run snapshot (new)
