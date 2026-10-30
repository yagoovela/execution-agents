# A2 — Promote the finished modules and providers

**Goal:** produce a checkable record that the six node types already in production are wired end
to end, point by point against PLAN §3.4, with every point either proved here or handed to the task
that owns it by name. This is verification, not a build and not a promotion: nothing ships from
this task.

**Depends on:** A1 (shipped). **Blocks:** nothing, but it is the cheapest coverage-confirming work in the epic.

## Why

**Updated 2026-08-24.** `mcpNode` shipped: it is in the worker enum, has its `mcp` module, is in
`isTemporalNode`, is in the legacy allowlist, and `mcp` is a migrated integration provider. It is
done and out of this task.

**Corrected 2026-09-02 — only production counts.** Six types had complete worker modules that were
not in `worker@origin/main`, listed as of that date, with production not running them.

**Corrected 2026-09-21 — re-validated against `back@origin/production` `3804a524` and
`worker@origin/main` `3e4c93a`. All six have now shipped.** `voice-generator`, `web-crawling`,
`web-search`, `large-memory`, `pull-data`, `push-data` — plus `image-generator` — are all present in
production with modules and registration: the worker's `NodeType` enum has **20 entries**,
`worker/src/modules/temporal/workflows/node-activities.ts` dispatches **14** of them, and
`process-single-node.workflow.ts` handles `TEXT_GENERATOR`, `LARGE_MEMORY`, `WEB_SEARCH`, `VOICE` as
workflow cases. `flux.service.ts`'s `isTemporalNode` now lists 14 types
including all six of these (§ TASK-A1). **This task's node-type half is done; only its evidence
trail needed writing down, which this correction does.** The table below is kept for history — what
it said on 2026-09-02, and what is true now:

| Node type | Worker module | In `worker@origin/main`, 2026-09-02? | In production, 2026-09-21? |
|---|---|---|---|
| `voiceBoxNode` | `voice-generator` | no | **yes** |
| `webCrawling` | `web-crawling` | no | **yes** (but see TASK-A1: not in either legacy allowlist, wrong refusal message on the legacy endpoint) |
| `webSearch` | `web-search` | no | **yes** |
| `commandContentNode` | `large-memory` | no | **yes** |
| `pullData` | `pull-data` | no | **yes** |
| `pushData` | `push-data` | no | **yes** |

The first draft framed this as reconciling a chore branch that had "reached no environment"; that
framing was already dropped by the 2026-09-02 correction and does not need re-litigating.

**The integration-provider queue is the correction that still has open work — and it now needs
precision the earlier draft did not have.** `mcp` shipped on 2026-08-24. Two providers remained
listed as pending: `clickup` and `quickbooks`. Re-validated 2026-09-21, they are in two different
states, not the same one:

- **`clickup` — the product feature shipped; the worker-routed half did not, and that split is the
  whole story.** `clickup` **is** in `back@origin/production` and `front@origin/production` today,
  via back PR #1922 and front PR #2134, under ClickUp task
  [868j988uj](https://app.clickup.com/t/868j988uj), landed 2026-08-27:
  `back/src/app-api/integrations/adapters/clickup.adapter.ts`, registered in `IntegrationsService`'s
  constructor (`this.adapters.set('clickup', clickUpAdapter)`,
  `back/src/app-api/integrations/integrations.service.ts`); `IntegrationProvider.CLICKUP` in
  `back/src/entities/user_integration.entity.ts`; front
  `front/src/components/ThirdPartyIntegration/registry.ts` registers `clickupConfig`. **But it
  shipped entirely on the inline OAuth-connection path, not the worker-routed one this task
  promotes.** There is no `clickup` adapter under
  `worker/src/modules/nodes/third-party-integration/adapters/` (that directory has adapters for
  exactly the 9 `MIGRATED_INTEGRATION_PROVIDERS`, and `clickup` is not one of them), and `clickup` is
  not in `integration-executable-node.ts`'s `MIGRATED_INTEGRATION_PROVIDERS`.
  The 2026-08-27 note in the first draft of this correction — "the product feature is delivered; the
  worker-routed half this epic owns is not" — was correct and still holds; stating it explicitly
  here is so nobody re-litigates it as if the ClickUp task closed this task's item. **Corrected
  2026-09-21, same day: `clickup`'s worker adapter is not this task's — it is
  [`TASK-A10`](./TASK-A10-CLICKUP-WORKER-ROUTING.md).** The first version of this correction put the
  adapter in A2's own scope, below. That was written before this epic had a standing rule for new
  integrations (`PLAN.md` §3.6, added the same day, also written because of this exact gap); with
  the rule in place, ClickUp's leftover work reads as new coverage this epic must add — A2's shape,
  "verify what's finished," does not fit it, because nothing about the worker half is finished. A2's
  provider-queue scope is therefore **empty** as of this correction: `mcp` is done, `clickup` moved
  to A10, `quickbooks` stays in PLAN §9. A2's remaining work is entirely the node-type verification
  pass above.
- **`quickbooks` — has zero presence in production, in any repo.** The only two greps that hit the
  string are noise, not code: prose in `worker/src/modules/nodes/third-party-integration/PORTED_FROM.md:142`,
  and unrelated LLM sample text in `back/src/app-auth/auth/dto/example.ts`. There is no adapter, no
  entity value, no front registry entry, nothing in `MIGRATED_INTEGRATION_PROVIDERS`. **This is not
  a promotion — there is nothing finished to promote.** If `quickbooks` support is still wanted, it
  is new work (an adapter, an OAuth connection, a front config, a provider registration), not a
  release step, and it does not belong in this task's scope of "verify what exists against the
  definition of done." **A2's provider queue is empty**, per the 2026-09-21 correction above:
  `clickup`'s worker adapter moved to `TASK-A10`; `quickbooks` is dropped from this task until
  someone builds it (PLAN §9), at which point §3.6's rule is what should keep it from becoming a
  line item here again.

**Check staging before shipping.** As of 2026-08-21 `back@origin/staging` still carried the
pre-release six providers while production carried eight — staging was behind production for this
file. Not re-measured in this correction; confirm again before promoting the `clickup` adapter,
since the same staging-lag risk applies to any new worker-side change.

## Corrected 2026-09-23 — what A2 can close, and what belongs to other tasks

Re-validated against `back@origin/production` `a90d1ae6` (A1, A1b and A1c all merged) and
`worker@origin/main` `d9d7170`. The worker's only changes since `3e4c93a` are in `notification/`, so
every fact of the 2026-09-21 correction above still holds: 20 `NodeType` entries, the six modules
imported in `temporal.module.ts`, each of the six in `node-dispatch-registry.ts` with
`flowDispatch: 'worker'` and `workerModule: true`, `clickup` absent from
`MIGRATED_INTEGRATION_PROVIDERS` (A10), `quickbooks` absent from every repo (PLAN §9).

**Two clauses of that correction's Done-when could not be met inside this task, and are rewritten
here rather than quietly ticked.**

1. **"An A1 registry entry with no `hasInlineTwin`" is false for three of the six — by design.** A1
   shipped `hasInlineTwin` as a derived fact (`hasDispatchConflict()`), not a stored one. For
   `voiceBoxNode`, `webSearch` and `commandContentNode` it is true: `flowDispatch: 'worker'` plus
   `legacyEndpoint: 'accept'`, so a flow runs them on the worker while
   `/process/single-node-legacy` runs them inline. A1 pins exactly these three with `it.failing`
   in `node-dispatch-invariants.spec.ts`, and that spec names **C1** as the task that removes them.
   A2's Out clause forbids changing what a module does, so A2 cannot make the clause true. It
   records it.
2. **"Against PLAN §3.4's seven-point definition of done" is more than a verification pass can
   close.** Points 3, 4 and 7 have owners outside this task. Asking A2 to close them would either
   keep A2 open until C1, C3 and D1 land, or tempt a fix inside a verification task.

**What A2's done means instead — every §3.4 point is either proved here or handed off by name. No
cell of the record is left blank.**

| §3.4 point | What A2 does | Owner of any gap |
|---|---|---|
| 1. Registration chain | Prove per type, file and symbol: module, enum entry, `temporal.module.ts`, `activities.service.ts`, `worker.service.ts` binding, `workflows/configs.ts` proxy, and the workflow dispatch — a `switch` case (`LARGE_MEMORY`, `WEB_SEARCH`, `VOICE`) **or** an entry in `node-activities.ts`'s uniform table resolved by `resolveNodeActivity` in the `default` branch (`PULL_DATA`, `PUSH_DATA`, `WEB_CRAWLING`) | — |
| 2. Dispatch registry | Prove the entry exists with `flowDispatch: 'worker'` and `workerModule: true` | — |
| 3. Both entry paths | Prove a full flow run and a single-node run (`executeSingleNode`, which reads `isTemporalNode`) both reach the worker | The legacy endpoint: `webCrawling`'s wrong refusal message → **C3** (`handoffOwner: 'C3'`); the three inline accepts → **C1** |
| 4. No inline twin | Record the three `it.failing` pins as the current, known state | **C1** |
| 5. `NodeError` subclasses | Read each module's error paths and record which subclass it throws | A module that fails becomes **its own task** (Out clause), not a fix here |
| 6. Negative control | Run the required control below | — |
| 7. Documentation | Record whether the node's page and contract-table row exist | **D1** |

**Two decisions, 2026-09-23.**

- **PLAN §3.4 point 4 keeps its wording.** It names only the `flux.service.ts` twin. The three twins
  here live on `/process/single-node-legacy`, and they stay C1's rather than being folded into §3.4.
  This record marks point 4 as C1's for them.
- **The title is kept, although it no longer describes the task.** "Promote the finished modules
  and providers" is what A2 was written to do. Since the 2026-09-21 and 2026-09-23 corrections it
  promotes nothing: it verifies six shipped node types against §3.4. It is not renamed, because the
  title is referenced by the timeline pages, `_generator/TITLES_ALL.py` and the ClickUp task, and
  renaming all of them for a task that ships nothing is not worth the churn. Read the Goal, not
  the title.

## Scope

**In.** The record above, for `voiceBoxNode`, `webCrawling`, `webSearch`, `commandContentNode`,
`pullData`, `pushData`, plus a confirmation that `mcp` is done. Read-only against every repo; the
only writes are to this spec, `STATUS.md` and the ClickUp task.

**Out — handed off, recorded, not done here.** The three inline twins (C1). `webCrawling`'s
refusal message on the legacy endpoint (C3). Node documentation (D1). `clickup`'s worker adapter
(A10). `quickbooks` (PLAN §9, until it is built).

**Out.** Any change to what a module does. If a module fails a §3.4 point that A2 owns, that failure
becomes its own task — do not fix it inside the verification.

**Out.** Staging. A2 ships nothing, so the staging-lag question (decision A2-a) no longer governs
anything here; it applies forward, to A10.

## Steps

1. Fill the record, per type, for points 1, 2 and 5 — file and symbol, not line numbers.
2. Run the negative controls (Verification, below).
3. Run each of the six in the local Docker stack, for point 3.
4. Fill points 4 and 7 with their current state and owner.
5. Update `STATUS.md` and the ClickUp task; move the ClickUp Progress field as each step lands.

## Verification

- **Negative control (required) — one per dispatch mechanism, because the two paths differ.** Remove
  `LARGE_MEMORY`'s `switch` case from `process-single-node.workflow.ts`, and separately remove
  `PULL_DATA` from `node-activities.ts`'s table. Run `process-single-node.workflow.spec.ts` and
  `node-activities.spec.ts` for each, and record the failure. In both cases the `default` branch
  throws `Node type X not supported`, which is the failure a missing registration produces in
  production. If a spec stays green with the entry removed, that spec is vacuous: record it as a
  finding, and do not count it as coverage.
- **Per node, in the local Docker stack:** run it in a flow and as a single node, and confirm the
  activity appears in Temporal, `node_executions` goes PENDING → COMPLETED, and the downstream node
  receives the output. A node whose provider credential is not available locally is reported
  **unverifiable**, not passed.

## Done when

The record has a cell for every §3.4 point × each of the six types, each holding either evidence
(file and symbol, a test run, a run id) or the named owner task. Both negative controls were
observed failing. `mcp` is confirmed done. `clickup` is routed to A10 and `quickbooks` to PLAN §9,
both recorded above. `STATUS.md` and the ClickUp task agree with this file.

## Record — against `back@origin/production` `a90d1ae6`, `worker@origin/main` `d9d7170`

Filled 2026-09-23. Every cell holds evidence, an owner, or an explicit **unverifiable** with its reason.

| Type | 1 Registration chain | 2 Registry | 3 Both entry paths | 4 Inline twin | 5 `NodeError` | 6 Negative control | 7 Docs |
|---|---|---|---|---|---|---|---|
| `voiceBoxNode` | ✅ `VoiceGeneratorModule` · `voiceGeneratorActivity` (service, binding, proxy) · `switch` `case NodeType.VOICE` | ✅ `flowDispatch: 'worker'`, `workerModule: true` | ✅ routed: flow + single-node both ran as `processSingleNode` (`node-process-x-1-406248cc…`, `…-1b978075…`). Success **unverifiable locally** — ElevenLabs answered `Unauthorized`, correctly classified. *Corrected 2026-09-24:* the fixture hard-coded `voiceId` `21m00Tcm4TlvDq8ikWAM`, the same id that failed on dev, where a voice picked from the node's list succeeded with the same key — so the id, not the credentials, is the likely cause here too (not re-run locally) | Flow: guarded by `isTemporalNode`. Legacy endpoint accepts it → **C1** (`it.failing` pin) | ✅ `UserConfigError`, `IntegrationError`, `ProviderError`, `TimeoutError` | ✅ covered by the uniform/switch spec | ❌ no `worker/node/` page → **D1** |
| `webCrawling` | ✅ `WebCrawlingModule` · `webCrawlingActivity` · `node-activities.ts` table entry | ✅ same; `legacyEndpoint: 'refuse-unsupported'`, `handoffOwner: 'C3'` | ✅ flow (`x-1` + consumer `cons-1` received the page text) and single-node, both COMPLETED · legacy refusal message → **C3** | Flow: guarded. Legacy: refused, no twin | ⚠ `charge-scrape.client.ts` throws a plain `Error` on an HTTP failure of `/worker/charge-scrape`; `runNodeActivity` turns it into a non-retryable `SystemError`. Observation, not a failure | ✅ | ❌ → **D1** |
| `webSearch` | ✅ `WebSearchModule` · `webSearchActivity` · `switch` `case NodeType.WEB_SEARCH` | ✅ same | ✅ flow (`x-1` + consumer `cons-1` received the SerpAPI results) and single-node, both COMPLETED; Temporal status `Completed` | Legacy endpoint accepts it → **C1** | ⚠ only `IntegrationError`: a missing `SERP_API_KEY` is reported as retryable, and an empty query is not validated before SerpAPI. Reachability not proven — observation | ✅ | ❌ → **D1** |
| `commandContentNode` | ✅ `LargeMemoryModule` · `largeMemoryActivity` · `switch` `case NodeType.LARGE_MEMORY` | ✅ same | ✅ routed on both paths. Success **unverifiable locally** — the cloned DB has no `namespace` rows, so no pod exists to query | Legacy endpoint accepts it → **C1** | ❌ `UserConfigError` for a missing pod, but `modules/vector/vector.service.ts` throws a plain `Error("Namespace not found")` when the configured pod no longer exists or is not accessible — observed in the run: the user sees "Internal error while running this node." → recorded, like `pushData`'s | ✅ **observed failing** (control 1) | ❌ only the feature page `large-memory-dynamic-pod.mdx`; no `worker/node/` page → **D1** |
| `pullData` | ✅ `PullDataModule` · `pullDataActivity` · table entry | ✅ same; `legacyEndpoint: 'refuse-migrated'` | ✅ routed on both paths; failed with a classified error (`Google integration missing for user`). Success **unverifiable** — no Google OAuth token locally | Legacy: refused; the unreachable `case` arm is **C2**'s to delete | ✅ `UserConfigError` | ✅ **observed failing** (control 2, after the spec fix below) | ❌ → **D1** |
| `pushData` | ✅ `PushDataModule` · `pushDataActivity` · table entry | ✅ same; `legacyEndpoint: 'refuse-migrated'` | ✅ routed on both paths; same classified error as `pullData`. Success **unverifiable** — no Google OAuth token locally | Same as `pullData` → **C2** | ❌ `push-data.service.ts` throws a plain `Error("Google Slides input is not valid JSON")` for invalid **user** input; the user sees the generic "Internal error while running this node." instead of a `UserConfigError` → **its own task** (Out clause) | ✅ | ❌ → **D1** |

**`mcp` — confirmed done.** `mcpNode` has a registry entry with `flowDispatch: 'worker'`,
`legacyEndpoint: 'refuse-migrated'`, `workerModule: true`, `integrationExecutable: true`; `mcp` is one
of the registry's migrated integration providers; the worker has `modules/nodes/mcp/` and
`third-party-integration/adapters/mcp.adapter.ts`, and `node-activities.ts` maps `NodeType.MCP` to
`mcpActivity`.

All six activities go through `runNodeActivity` (`nodes/shared/run-node-activity.ts`), so nothing escapes unclassified: a non-`NodeError` becomes a `SystemError`. Point 5 is therefore about **misclassification**, not leaks.

**Negative controls, observed.**

- **Control 1** — `LARGE_MEMORY`'s `switch` case removed: `processSingleNode with LARGE_MEMORY › runs validateLargeMemoryAccess -> largeMemory -> chargeLargeMemoryUsage in order` failed with `Node type commandContentNode not supported` (1 failed / 20 passed).
- **Control 2** — `PULL_DATA` removed from `node-activities.ts`: **the suite stayed green, 21/21.** `node-activities.spec.ts` pinned a hand-maintained list of nine types that stopped before `pullData`, `pushData`, `webCrawling`, `mcpNode` and `imageGenerator`. So the uniform-table path had no test that could fail for three of A2's six types.
- **The fix** — `worker` `feat/868m0vkgj` `9f27301`, test-only. The spec now derives the expected set from the `NodeType` enum, minus the workflow's own `switch` cases (read from `process-single-node.workflow.ts`) and minus the two never-dispatched types. Re-run after the fix: control 2 fails `resolves pullData to an activity`, and removing `LARGE_MEMORY`'s case fails `resolves commandContentNode to an activity`. Green otherwise, 32 tests across both specs.

**Point 3 — how it was run.** Dev could not stand in for production: `worker@origin/develop` differs
from `main` on exactly the exercised paths. So the run used an isolated stack built from this task's
worktrees — `back@origin/production` `a90d1ae6`, `worker@origin/main` `d9d7170` — as compose project
`a2-verify` (`etc/868m0vkgj-stack/`, its own ports and volumes). Its database was a **clone** of the
local devdb volume with production's migrations applied; the original volume was not touched. One flow
per type (start → X → `outputController`) was seeded into the clone and driven through
`POST /flux/execute-from-canvas` and `POST /flux/execute-single-node`. **20 distinct
`processSingleNode` workflows** on `enhanced-ai-queue` confirm the worker path. The fixture configs
needed three corrections (`system: 'scrapingBee'`, not `scrapingbee`; `nameSpace` as `{id, name}`;
a `voiceId`), and each was first surfaced by the worker as a correctly classified `UserConfigError`.

**Point 3 on dev — before and after the merge into `develop`.** Dev carries the provider
configuration the local stack lacks, so the same six shapes were rebuilt there, in workspace
"lex corp." (folder `a2-verify-868m0vkgj`, agents `a2-<type>`, pod `a2-verify-pod` holding
`rfc2606.txt`), and each ran through `run_agent` and `POST /flux/execute-single-node`. **Before:**
`worker@develop` `8503264`. **After:** `feat/868m0vkgj` merged straight into `develop` as `1bd3632`
(no PR, per the env-branch policy), deployed by "Deploy Worker to ECS Dev" with
`wait-for-service-stability`, finished 15:19 UTC. The 12 results (6 types × 2 paths) are identical
before and after, as expected for a test-only change. Rows read from dev's `node_executions`, kept in
`etc/868m0vkgj-stack/dev-before.txt` and `dev-after.txt`.

| Type | Flow · single-node, before = after | Evidence / reason |
|---|---|---|
| `webSearch` | ✅ · ✅ | SerpAPI results for "fluxprompt" reach `cons-1` |
| `webCrawling` | ✅ · ✅ | example.com text reaches `cons-1` |
| `commandContentNode` | ✅ · ✅ | The pod answers with the RFC 2606 names — closes the local "unverifiable". `cons-1` shows `''` because the output is an object `{result}`; pre-existing, not dispatch |
| `voiceBoxNode` | ❌ · ❌ → ✅ after the fix | `ElevenLabs generateSpeech failed: Unauthorized`, routed and classified. *Corrected 2026-09-24:* the key was never the problem. The fixture's `voiceId` (`21m00Tcm4TlvDq8ikWAM`) was hard-coded, not taken from the voice list the node offers; with a voice picked in the node (`pNInz6obpgDQGcFmaJgB`) the same agent produced an audio file on dev with the same key (`execId` `28dedb26`, 2026-09-24 14:59 UTC) |
| `pullData` | ❌ · ❌ → ✅ once Google was connected | `Google integration missing for user`, classified, while the test user had no Google OAuth on dev. *2026-09-24, manual QA:* after the user signed in to Google (through the "app not verified" warning), it read back the document `pushData` had created — output `A2 verification` (`execId` `e981b062`) |
| `pushData` | ❌ · ❌ → ✅ once Google was connected | Same error as `pullData` before sign-in. *2026-09-24, manual QA:* created the Google Doc `a2-verify-868m0vkgj` (`execId` `397dee70`), which `pullData` then read |

**Manual QA on dev, 2026-09-24.** The six agents were re-run by hand from the canvas, flow Run and
the node's own Run: all six passed. Two needed setup first — Google sign-in for `pullData`/`pushData`
(the dev Google OAuth app shows an "app not verified" warning; the sign-in still completes) and a voice
picked from the list for `voiceBoxNode` (`execId` `28dedb26`, `efbf71b5`). With that, every point-3
cell A2 left **unverifiable** is closed on dev.

**Fixture rule for `voiceBoxNode` — so this does not recur.** Take the voice from the list the node
itself offers in the canvas, never from a remembered provider id: a well-known ElevenLabs id that the
environment's account cannot use fails as `Unauthorized`, which reads as a bad key. The node shows a
default voice (`pqHfZKP75CvOlQylNhV4`, `front/src/components/AiAudioGenerator/constants.ts`) but never
saves it, so a node built through MCP, or never touched in the canvas, has no `voiceId`; the worker then
refuses it with `UserConfigError` "Voice ID is required for ElevenLabs.". After building one through
MCP, open it and pick a voice before the run. `voiceBoxNode`'s MCP schema marks only `aiSystem` as
required and says nothing about where a valid `voiceId` comes from — recorded here, not fixed (not A2's
scope).

**Observation, outside A2's scope.** At the end of the `webSearch` run the back logged `closed node
executions left in flight at run end … closed: 2`, but both of the run's node rows finished with
output and without `cancelledAt`. The sweep matches on the run's `execId`, while node rows carry
their own — so what it closed is unexplained. Not investigated further; it is run bookkeeping, not
dispatch.

## Files

`worker/src/modules/nodes/{voice-generator,web-crawling,web-search,large-memory,pull-data,push-data}/`
(verification only — already shipped) ·
`worker/src/modules/nodes/nodes.types.ts` · `worker/src/modules/temporal/**` ·
`back/src/shared/node-dispatch/` (the A1 registry and its invariant spec). Written: this file · `STATUS.md`.

## Decision recorded (2026-10-23)

**A2-a — closed without a choice.** A2 was rescoped to verification and promoted nothing. The
`clickup` adapter shipped through A10 (back PR #2004, worker PR #109). Back `staging` `8af0171f` now
has the same ten worker-routed integration providers as `main` `a38fef57`, so staging is no longer
behind production for `node-dispatch-registry.ts`.
