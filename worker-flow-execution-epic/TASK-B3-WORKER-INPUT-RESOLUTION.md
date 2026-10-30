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

**Reach.** The node types the dispatch contract routes to the worker (17 when this was written; 23 in `node-dispatch-contract.json` on `back@origin/main` `0f66a5fb`, 2026-10-15), plus `thirdPartyIntegration`
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

## As built (2026-10-10)

Branch `refactor/868m0vmy4` in back and worker, on top of B1's `refactor/868m0vmun` until B1
reaches production. Two flags, both seeded off: `worker_input_resolution` (the worker resolves and
the back stops substituting) and `worker_input_resolution_shadow` (the back resolves as today, the
worker resolves too and only records whether it agrees). When both are on, apply wins.

**What changed against the scope above.**

- **A dispatch journal, not a completed-upstream map.** Label aliases are last-write-wins, so the
  order that matters is the order the back changed its schema, which is dispatch order. Each dispatch
  records in its own `node_executions.metadata.inputResolution.delta` what changed in the schema
  since the previous dispatch. The workflow receives `{ snapshotId, mode, journal, shadow }`, where
  `journal` lists the `{ nodeId, execId }` of the dispatches since the snapshot, ids only. The worker
  rebuilds the schema as base + journal deltas + its own delta.
- **The snapshot is a table.** `run_substitution_snapshots` holds the run-start base. Every 50
  dispatches the back writes a checkpoint snapshot and restarts the journal, so a long loop does not
  grow the journal without bound.
- **Two modes.** `full` when the back built a substituted copy of the node (`*Data` filled and text
  substituted); `refArrays` when it only fills the `*Data` arrays. The worker resolves the same way.
- **Cleanup.** At the end of the run the back removes `delta` and `raw` from the run's rows and
  deletes its snapshots. Both retention passes remove them too, and the cron deletes snapshots older
  than the run ceiling + 1 h.
- **Failure.** A missing row, delta or snapshot fails the node with "This step could not load the
  results of the steps before it. Run the agent again." The activity retries 3 times first. Shadow
  mode never fails a node: a mismatch or an error is recorded as `{ matched: false, divergentPaths,
  error? }` and logged as `worker_input_resolution.shadow_mismatch`.
- **Claim-check.** A resolved input above the threshold is stored as `{nodeId}-resolved.json` through
  `/worker/store-payload` (`field: 'resolved'`).

**`''` stays `''`, and nothing is refused.** A placeholder pointing at a node that did not run
resolves from that node's own field in the run-start base: `''` when the field is empty, the literal
placeholder when the field does not exist. The worker reads the same base, so both stay as they are.
B3 adds no rule that refuses a flow (every run with the flag on resolves worker-side), so PLAN
§3.3.2's measurement has no refusal to classify. Shadow mode is the equivalence check over real runs.

**Verified on a local stack** (back and worker from the branch, Temporal, a clone of the local
database, a local echo server for `apiCaller`), all three modes, with every request body read from
the echo server:

| Run | Off | Shadow | Apply |
|---|---|---|---|
| Placeholders: two upstreams, a shared label (`dup` → the last), an unknown label, a node off the path, an LLM node with `promptData` | 6/6 | 6/6 matched | 6/6 |
| 55-node chain, each body naming the previous node and the first (crosses the 50-dispatch checkpoint) | 55/55 | 55/55 matched | 55/55 |
| 60-item loop (62 dispatches) | 62 | 62 matched | 62 resolved |
| 300 KB upstream output into a body | ok | matched | ok, `user-resolved.json` stored |
| 3 concurrent runs of the same flow + a loop | — | — | each run got only its own values |

Snapshots per run matched the checkpoint (2 for the 55- and 62-dispatch runs, 1 otherwise), and
none were left after any run. Negative controls on the same stack: a trigger that corrupted one
node's unresolved input made shadow mode record `matched: false` on `jsonRequestBody` for that node
only, while the run succeeded; deleting the snapshot mid-run in apply mode stopped the run at that
node with the message above. That second control found the activity was not wrapped in
`runNodeActivity`, so the user saw the generic "Internal error" (fixed, worker `fb28328`).

Placeholders inside an array loop's body are not substituted today in any mode, flags off included.
B3 keeps that as it is.

## Files

`back/src/app-api/flux/flux.service.ts` (`processNodeViaTemporal`, the substitution at `:3599`, the
`REF_ARRAY_FIELDS` loop at `:775`) · `back/src/app-api/flux/ref-array-fields.ts` ·
`worker/src/modules/nodes/shared/fetch-node-row.ts` · `worker/src/ported/back/` (B2's copies) ·
`back/src/shared/ported-engine/` (the sync manifest, if `ref-array-fields.ts` joins it) ·
worker-side resolution (new) · the run snapshot (new)

## QA on dev (2026-10-13)

`worker_input_resolution` (apply) was turned on in dev from 15:36:46Z to 15:38:50Z and turned off again; shadow stayed on. No other flow ran in that window. Agent "B3 QA — apply mode (868m0vmy4)": `varInputNode` "Data Input" → starter → `mathFunction` "Alpha" → `scripting` "Sleeper" (20 s) → `apiCaller` "Gamma" with `{{datainput.text}}`, `{{alpha.result}}` and `{{unused.text}}` (a `commandTextNode` that never runs).

| Check | Result |
|---|---|
| Equivalence | Shadow baseline (`d84c5024`, back substitutes) and apply runs give the same Gamma input shape; every apply row carries `inputResolution.resolvedAt`, so the worker resolved it |
| Empty stays empty | `{{unused.text}}` resolves to `''` on both paths |
| Concurrency | Two simultaneous apply runs (`5893d123`, `601baaa7`) received only their own input, `concurrent-one` and `concurrent-two` |
| Negative control | With Alpha's `node_executions` row deleted while Sleeper ran (`b7cd96ec`), Gamma failed with "This step could not load the results of the steps before it. Run the agent again." and never called the API |
| Loops under apply | B3.1's loop agents resolved `acme-widgets` on every iteration, including an LLM body node |

**Left for a human:** look at the canvas error a user sees when the negative control fires.

**Found, not changed:** `{{alpha.result}}` resolves to `''` on both paths even after the `mathFunction` ran, so a worker-run `mathFunction` result does not reach the substitution schema. Behaviour is equal on both paths, so B3 is unaffected; it is a separate defect.

**Trap:** deleting the upstream row while that upstream is still running fails the upstream itself with a generic internal error (`635ddd9c`). Delete only after the next node has started.

### Canvas notification on failure

**Found in human QA:** the error panel showed the user message, but the run notification said `Node <id> execution failed`.

- **Cause:** on every node failure, `generateExecutionLogsActivity` in `worker/src/modules/temporal/activities/activities.service.ts` merged `executionStatus: "FAILED"` into the live `flows_nodes.data`. The back never persists that field (`NON_PERSISTED_NODE_DATA_FIELDS` in `flow-node.service.ts`), and `executionError` is never stored. When the canvas loads the node again, `sanitizeLoadedNodes` keeps `FAILED`, and `ApiCaller.tsx` (as well as `MathFunction`, `Scripting` and `SqlQuerier`) falls back to the generic text. Dev had 49 live rows in that state.
- **Fix:** worker commit `30e5a46` on `refactor/868m0vmy4` (PR #128) drops the field from that write. `errorMessage` is still written. No back or worker code reads a persisted `executionStatus`.
- **Test:** `activities.service.spec.ts` asserts that the live-row delta has no `executionStatus` and keeps `errorMessage`. **Negative control:** with the line restored, it fails with `Received value: "FAILED"`. The spec did not load before this change (a missing constructor stub and the ESM-only `ai` package); the commit adds the stub and an `ai` mock.
- **Dev:** cherry-picked to `develop` as `369423b` (dev also needed its own stub order). After the rollout, run `fdd329f9` of the B3.2 agent failed with HTTP 500, and the live row kept `executionStatus` empty with the user message in `errorMessage`.
- **Left out:** rows written before the fix keep `FAILED` and still show the generic text when their flow opens. Cleaning them needs a back migration, which is a separate decision. A budget stop also emits `FAILED` without a message (`run-stop-statuses.ts`).
