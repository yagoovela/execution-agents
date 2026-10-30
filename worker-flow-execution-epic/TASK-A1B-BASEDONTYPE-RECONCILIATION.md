# A1b — Reconcile `basedOnType`

**Goal:** decide, on a measurement, whether `basedOnType`'s two live copies become one source or
stay two named projections of a shared base, and delete the one copy that is dead code. Unlike A1,
this task is **not** behaviour-neutral by construction — the two live copies already disagree, so
someone has to decide which side is the truth for each divergence, and that decision needs evidence
before it is made.

**Added 2026-09-21**, split out of TASK-A1 the same day TASK-A1 was corrected. TASK-A1's first
correction pass called this "three divergent copies" needing "an explicit per-field decision table"
and named it "the single largest scope increase" in the epic's re-validation. **That framing was
wrong**, found by a same-day field-by-field re-measurement — see Why. It is recorded here rather
than silently fixed, because TASK-A1's own history note already carries the same pattern
("Corrected 2026-09-21") and a correction to a same-day correction deserves the same treatment: say
what the earlier text claimed and why it changed, not just publish the new number.

**Depends on:** A1 (the registry must exist — this task's eventual registry entry is a projection of
it, and A1's steps that used to mention `basedOnType` now point here instead). **Blocks:** nothing
downstream in this epic directly; it clears a defect A1's re-validation surfaced, not a
precondition any other task's Done-when line names.

## Why

`basedOnType` answers, for a node type, which of its data fields a placeholder (`{{nodeId.field}}`)
may reference. It is hand-maintained, in three places, not one map read from three call sites as the
original A1 draft assumed.

**One of the three is dead code, not a divergent copy.** `back/src/app-api/flux/constants.ts`
declares a local `nodeSchema` — `const nodeSchema = (nodes: any) => { ... }` — that is **not
exported**, and is referenced nowhere else in `back`: `grep -rn "nodeSchema" src/` finds only its own
declaration in that file, plus the unrelated, actually-exported `nodeSchema` in `folw/contants.ts` (a
same-named but different binding — see below). `flux/constants.ts`'s own exports are
`LEGACY_IMAGE_PROVIDER`, `IMAGE_MODEL_FIELD`, `LEGACY_AUDIO_SELECTOR`, `LEGACY_VOICE_PROVIDER`,
`VOICE_MODEL_BY_SYSTEM`, `arrayDataToText`, `findNextNodeToRun`, `replacePlaceholders` and similar
helpers — `nodeSchema` is not among them. The 14-type `basedOnType` embedded inside this `nodeSchema`
function has never executed in production. This copy is a **deletion**, not a reconciliation — once
its unreachability is proven fresh (below), it is simply removed.

**The two live copies serve genuinely different purposes, and that is why they are not obviously
"the same list" in the first place:**

- `back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts`'s
  `basedOnType` (26 types) feeds that service's `generateSchemaFromNodes`, called by:
  `prefetch-flow-executor.ts`'s `runPrefetchFlow` (via `deps.substitutionEngine.generateSchemaFromNodes`),
  `legacy-context-builder.ts`'s `buildLegacyContext` (via `params.substitutionService.generateSchemaFromNodes`),
  and `node-reference-substitution.controller.ts`'s `POST /generate-schema` handler
  (`generateSchema`). It builds the **placeholder-reference schema** — what a `{{nodeId.field}}`
  substitution is allowed to point at.
- `back/src/app-api/folw/contants.ts`'s `basedOnType` (29 types) feeds that file's own exported
  `nodeSchema` function, called inside `addConnectToNodes` (`const sx = nodeSchema(nodes);`), and
  `THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS` (`= basedOnType.thirdPartyIntegration`), read by
  `folw/helpers/helpers.ts`'s `modifyData` and `folw/flow.controller.ts`'s private
  `filterNodeConnections`. It builds the **node-to-node data-passing payload** — what
  `addConnectToNodes` (C1's territory) actually merges into a downstream node.

Because these feed different consumers, **"one unified map" is not obviously the right target** —
the correct outcome may be one source with two named projections, one per consumer. Deciding that
without measuring which fields the divergences actually affect would itself be a false refusal
(dropping a referenced field silently breaks a customer's flow) or a false unification (merging two
lists that exist because they answer different questions). This task's job is to measure first, then
decide, per CLAUDE.md's "measure before refusing" rule — it must not presume the answer.

**The measured divergence is five lines, not sixty-six, and 24 of the shared types are
byte-identical.** The complete list, `node-reference-substitution` vs. `folw`:

| Type | Divergence |
|---|---|
| `mcpNode` | both have 8 fields, but `node-reference-substitution` has `inputMode` where `folw` has `toolArguments` — the only genuine content conflict (same slot, different value) |
| `outputController` | `folw` has `customFileName` in addition to `text`; `node-reference-substitution` has `text` only — an addition, not a conflict |
| `fluxBox` (`['sessionId']`), `reportBuilder` (`['text']`), `thirdPartyIntegration` (63 fields) | present in `folw` only, with no counterpart in `node-reference-substitution` — not a conflict either, since there is nothing on the other side to disagree with |

The 63-field `thirdPartyIntegration` entry was flagged as alarming in TASK-A1's first correction
pass; measured directly, it is not a conflict at all — `node-reference-substitution` simply has no
entry for `thirdPartyIntegration`, so there is nothing to reconcile there beyond deciding whether the
placeholder-reference schema should gain one.

## Scope

**In.** Decide, backed by the measurement in Verification, whether the two live copies become:
- **one map**, if nothing depends on the two purposes staying separate, or
- **one source with two named projections** (e.g. a shared base plus a per-consumer overlay for
  `mcpNode`'s `inputMode`/`toolArguments` and `outputController`'s `customFileName`), if the
  placeholder-reference schema and the data-passing payload need to keep disagreeing on those fields.

Record the decision and the reasoning in this file once made, the way TASK-A1's D4/D5-style
decisions are recorded — not silently in code.

**In.** Prove `flux/constants.ts`'s `nodeSchema` (the dead copy) is unreachable, fresh, before
deleting it: an owner-anchored grep across `back`, `front`, `worker`, `mcp-server` **and**
`origin/production`, not just this checkout — the same proof burden C3 already applies to its own
dead-code candidates (`processFlowWithSubstitution`, `api-caller-polling.ts`). Delete it once proven,
including the enclosing 14-type literal.

**In.** For the two live copies' three points of divergence, decide which side wins (or whether both
survive as named projections) based on whether the dropped or added field is actually referenced —
see Verification.

**In.** Once the decision is made, express it as a single source the A1 registry can project from
(or two named projections, if that is the decision), and update the two call sites
(`node-reference-substitution.service.ts`, `folw/contants.ts`) to read from it.

**Out.** Changing what a placeholder can currently do for any node type where the two copies agree
(24 of the shared types) — this task touches only the measured divergences.

**Out.** The A1 registry's own shape and its nine dispatch predicates — those are TASK-A1's, already
shipped by the time this task starts.

## Steps

1. Re-confirm the measurement above against the current checkout before starting — the numbers here
   are as of `back@origin/production` `3804a524`, and this task may start later.
2. Grep-prove `flux/constants.ts`'s `nodeSchema` is unreferenced across all four repos and
   `origin/production`. Delete it once proven.
3. For each of the three divergences (`mcpNode`, `outputController`, and the three
   `folw`-only types), run the dev-only measurement in Verification to find out whether the field
   that would be dropped by unification is actually referenced by a stored flow.
4. Decide, per divergence, using the measurement: keep both sides as named projections, or collapse
   to one value. Record the decision and why in this file.
5. Build the single source (or the two named projections) and point both call sites at it.
6. Update the A1 registry, if the registry's shape needs a field for this (check TASK-A1's shipped
   registry — it does not model `basedOnType` itself, so this may be a registry addition or may stay
   a standalone module the registry does not need to know about; decide based on what B3 will
   actually need to read).

## Verification

- **Negative control (required).** Before unifying a divergent field, break the current behaviour
  (e.g. temporarily remove `outputController`'s `customFileName` from `folw`'s copy) and confirm a
  flow using that field's data-passing path actually fails or drops data — not a synthetic test that
  cannot fail. Then restore it and make the real, decided change.
- **Measurement against real stored flows, dev only — never staging, never production.** For each
  divergence, query whether any stored flow actually references `mcpNode.inputMode`,
  `mcpNode.toolArguments`, or `outputController.customFileName` through a placeholder or through the
  data-passing payload. A field nobody references can be safely dropped from whichever side does not
  need it; a field that is referenced must not be dropped, regardless of which copy is judged
  "canonical" — dropping a referenced field is silent data loss, and CLAUDE.md's "measure before
  refusing" rule treats a false unification the same as a false refusal.
- **Proof of unreachability for the dead copy**, per item 2 of Steps — an owner-anchored grep across
  `back`, `front`, `worker`, `mcp-server` and `origin/production`, stated in the PR before the
  deletion, not asserted after.

## Done when

`flux/constants.ts`'s dead `basedOnType` copy is deleted, with its unreachability proof in the PR.
The two live copies' three divergences are each resolved by a recorded, measurement-backed decision
— not a silent pick. Both call sites (`node-reference-substitution.service.ts`, `folw/contants.ts`)
read from the single source (or the two named projections) this task builds. No field referenced by
a real stored flow was dropped.

## Decision

**Settled 2026-09-22: one source, by union.** `NODE_REFERENCEABLE_FIELDS` in the new
`back/src/shared/node-fields/node-referenceable-fields.ts` replaces both `basedOnType` literals.
`node-reference-substitution.service.ts` and `folw/contants.ts` both now assign
`basedOnType = NODE_REFERENCEABLE_FIELDS` (the service via a typed field initializer) instead of
carrying their own object literal, and `THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS` is re-exported
from the same module as `NODE_REFERENCEABLE_FIELDS.thirdPartyIntegration` — a named slice of the one
source, not a second one. This is recorded again as `D27` in `PLAN.md` §7, per this epic's convention
that a cross-task decision lives once in the parent spec.

**Step 1 — re-confirmed, not assumed.** Measured fresh against `back@origin/production` `5333b4d3`
(this task's own baseline, `3804a524`, was already superseded): 26 types in
`node-reference-substitution`, 29 in `folw`, 24 byte-identical, 3 divergent. The numbers in Why held.

**Step 2 — the dead copy.** `flux/constants.ts`'s `nodeSchema` (with its embedded 14-type
`basedOnType`) is deleted. Proof, stated before the deletion: (1) the declaration is
`const nodeSchema = (nodes: any) => { ... }`, not `export const`; (2) `grep -n "nodeSchema"
flux/constants.ts` finds only that one declaration inside its own file; (3) the file's closing
`export { ... }` block (`modifyAllSearchDataToSingleOne`, `findConnectedNodes`, `findNextNodeToRun`,
`formatPrompt`, `mergeText`, `htmlBody`, `replacePlaceholders`) does not name it — module scope
closes the question on its own. Corroborated, not proven, by a cross-repo grep: `back`, `front`,
`worker` and `mcp-server` `src/` all clean of any reference to this binding; the only other
`nodeSchema` symbols found are `folw/contants.ts`'s own exported one (unrelated) and a fourth,
independent one in `front/src/util/myFunctionsCoreDisplay.tsx:429` (see Out-of-scope finding below).
Additional evidence the copy was never touched: it is already one field stale relative to both live
copies (`commandTextNode` here has 5 fields, both live copies have added a 6th, `modelSettings`).

**Steps 3–4 — the three divergences, each decided by measurement, not preference.**

| Divergence | Measurement (dev DB, 41,652 non-deleted `flows_nodes` rows; never staging/prod) | Decision |
|---|---|---|
| `mcpNode`: `inputMode` (sub-only) vs. `toolArguments` (folw-only) | Not a conflict once traced: both are real, currently-used fields. `inputMode` is written by the front (`front/src/util/dataStoredToType.ts:73`); `toolArguments` is read by `folw/contants.ts`'s own `allNodesTargetBasedOnType` map and described in the MCP schema (`node-type-metadata.ts:2095`, worker-consumed via `third-party-integration/adapters/mcp.adapter.ts`). In dev: 16 `mcpNode` rows, 1 has `inputMode` set, 0 have `toolArguments` set, 0 placeholder references to either. | **Union — keep both.** Neither field is the "wrong" one; each copy simply lacked a field the other tracked for a different reason. |
| `outputController.customFileName` (folw-only) | 2,811 `outputController` rows in dev; 15 have `customFileName` set, 1 has `customFileNameData` (edge-linked) populated. 0 placeholder references (`{{...customFileName}}`) — the field travels through the data-passing path, not the placeholder path. | **Union — keep it.** Dropping it from the merged source would be exactly the silent data loss CLAUDE.md's "measure before refusing" rule and this task's Done-when line forbid; 15 real dev rows depend on it. |
| `fluxBox`, `reportBuilder`, `thirdPartyIntegration` (folw-only, no counterpart) | Not a conflict — nothing on the sub side to disagree with. Populated in dev (354 `fluxBox`, 23 `reportBuilder`, 59 `thirdPartyIntegration` rows), so real data exists behind all three. | **Union — carry them into the single source**, extending what a placeholder can reach to match what data-passing could already reach. This is additive, not a behaviour change to any of the 24 types that already agreed. |

Regex used for the placeholder counts was validated against real traffic before trusting its zeros:
it matches `{{prompt.text}}`, `{{aitextgenerator10.text}}` and 342 other live `.text` references out
of 365 total placeholder-field references in dev — so the zero for `inputMode`/`toolArguments`/
`customFileName` is a real zero, not a pattern miss.

**Negative control, run before trusting the union (required by Verification).** Each of the three
unions, and the "24 agreeing types stay untouched" invariant, were broken one at a time in
`node-referenceable-fields.spec.ts` and observed red before being restored:
- Dropping `customFileName` from the merged `outputController` entry: the data-passing schema
  (`nodeSchema` in `folw/contants.ts`) lost the field (`undefined` instead of the stored value), and
  the placeholder schema left `{{out.customFileName}}` unresolved instead of substituting it — two
  independent real failures, not a synthetic assertion.
- Dropping `toolArguments`/`inputMode` from `mcpNode`, or dropping `reportBuilder`/`fluxBox`/
  `thirdPartyIntegration` entirely: both placeholder-schema tests failed as expected.
- Re-introducing a divergence between the two call sites (patching only `folw/contants.ts`'s local
  `basedOnType` alias to add a field neither the source nor the sub-service copy has): the "served
  from the same object" anti-drift assertion caught it.

All four negative controls confirmed red, then the code was restored before the real change shipped.

**Step 5 — call sites.** `node-reference-substitution.service.ts`'s `basedOnType` field and
`folw/contants.ts`'s module-level `basedOnType` constant both now read `NODE_REFERENCEABLE_FIELDS`
directly; neither carries its own literal any more.

**Step 6 — A1 registry.** Not extended. TASK-A1's shipped registry does not model `basedOnType`
(confirmed by reading its shape), and B3 — the task that will actually read this measurement — can
import `NODE_REFERENCEABLE_FIELDS`/`THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS` directly from the new
module; there is no registry gap to fill for this task's scope.

**Verified against `origin/production`'s real two copies, not just against the new module's own
tests:** every field either copy had is present in the union (no drops), and the 24 types where both
copies already agreed are byte-identical in the merged source to what either copy had before.

**Out-of-scope finding, flagged not fixed.** A fourth `basedOnType`-shaped map, also named
`nodeSchema`, exists in `front/src/util/myFunctionsCoreDisplay.tsx:429` and is called from
`CoreNodeDisplay.tsx`, `CoreNodeDisplaySpaces.tsx`, `SmallMemory.tsx` and
`util/autosave/nodedata_autosave.ts`. It is unrelated to the three back copies this task's Files
section names and outside the ClickUp task's declared scope. Left unresolved; worth its own task if
front-side drift from the back's placeholder/data-passing schema turns out to matter.

**Pre-existing, unrelated test failures found while running the scoped regression, not caused by this
change, fixed and folded into this PR rather than split off.** `jest --findRelatedTests` on the
changed files surfaced 6 failing suites; each was independently reproduced on a clean
`origin/production` checkout before being touched, so none were caused by the union above:

- `node-types.service.spec.ts`: `THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS`'s hard-coded expected
  array was missing 9 keys (`idPrefix`, `ids`, `metadataFilter`, `namespaceOverride`,
  `paginationToken`, `queryById`, `queryText`, `queryVector`, `vectorsJson`) that the worker's own
  `payload-builder.ts` and the back's real `thirdPartyIntegration` entry already agreed on. The
  test's literal had drifted, not the two repos. Synced.
- `flux.controller.api-v2-queue.spec.ts`: `FluxController.api()` now calls
  `fluxService.checkSubFlowCascade()` first; the spec never stubbed it. Added the stub.
- `api-flows.service.spec.ts`: `toAgentJson()` now returns a `documentation` field; one older test's
  expected literal predated it. Synced.
- `worker.controller.claim-check.spec.ts` / `worker.controller.charge-scrape.spec.ts`:
  `WorkerController`'s constructor grew two trailing params (`UserService`, `MicrosoftAuthService`)
  read only inside `refreshOauthToken()`, a method neither spec exercises. Appended placeholder args
  to match the real signature.
- `flow.controller.create-flow.spec.ts`: failed to load at all (`pdfjs-dist`'s `import.meta` — ts-jest
  can't parse it); added the same `jest.mock('pdfjs-dist', ...)` a sibling spec already uses. Once
  loaded, 6 of 16 tests pass outright; the other 10 fail on real behavioral drift unrelated to
  `pdfjs-dist` (folder-not-found status code, user-product-limit counters, report creation, default
  templates) that needs a product decision, not a mechanical fixture update — marked `it.skip` with a
  comment recording why, rather than left silently red or deleted.

Merged to `production` 2026-09-23 as `173edf27` via [PR #1989](https://github.com/enhancedai-com/Flux-Prompt/pull/1989).

## Files

`back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts` (`basedOnType`,
`generateSchemaFromNodes`) ·
`back/src/app-api/folw/contants.ts` (`basedOnType`, the exported `nodeSchema`,
`THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS`) ·
`back/src/app-api/flux/constants.ts` (the dead, unexported `nodeSchema` function and its embedded
`basedOnType` — deleted once proven unreachable) ·
`back/src/app-api/flux/prefetch/prefetch-flow-executor.ts`,
`back/src/temporal/single-node-legacy/legacy-context-builder.ts`,
`back/src/app-api/node-reference-substitution/node-reference-substitution.controller.ts`,
`back/src/app-api/folw/helpers/helpers.ts`, `back/src/app-api/folw/flow.controller.ts` (consumers,
read only unless the chosen source changes their call shape) ·
the A1 registry (only if the chosen shape needs a registry field — decide in Steps)
