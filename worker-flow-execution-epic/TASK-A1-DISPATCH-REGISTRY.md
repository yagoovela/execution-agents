# A1 — One dispatch registry

**Goal:** replace the uncoordinated lists that answer "can the worker run this node type?"
with one derived source. **Every other task in this epic writes to this registry**, so it goes
first.

**Depends on:** nothing. **Blocks:** TASK-A1B, all of Track A, plus D2.

## Why

**Corrected 2026-09-21 — re-validated against `back@origin/production` `3804a524`.** The original
count of "four lists" was read at `back@3be1ea8e` (2026-08-21) and was already wrong when A1's
readiness review re-verified the rest of the plan on 2026-09-02 without re-checking this file. There
are **nine** dispatch lists today, not four. The old claim is left below, kept for history rather
than deleted, because the size of the gap between what was planned and what exists is itself the
reason A1's scope grows in this correction.

**`basedOnType` moved out to its own task, TASK-A1B, on the same day.** A same-day re-measurement
found the first cut of this correction had overstated `basedOnType`'s problem — see TASK-A1B for
the corrected facts (one dead copy, two live copies that diverge in five lines, not "three divergent
copies" needing a large reconciliation). Because that work is not behaviour-neutral — it needs a
measurement-backed decision, not a projection — it does not belong inside A1, which must stay small
and behaviour-neutral to safely gate A2/A3/C1/D2. This file no longer scopes `basedOnType` at all;
see TASK-A1B.

<details>
<summary>What this section said until 2026-09-21 (kept for history)</summary>

> Four independent lists exist today, none referencing another: `isTemporalNode(type)` (7 types),
> `isWorkerRoutedIntegration(node)` (9 providers), `MIGRATED_TEMPORAL_NODE_TYPES` ("the same 7"),
> `PREFETCH_SUPPORTED_NODE_TYPES` (17 types), and `basedOnType` (one hand-maintained map).

</details>

Nine lists, each independently sourced from `back@origin/production` `3804a524`:

| List | Location | Contents | Actually governs |
|---|---|---|---|
| `isTemporalNode(type)` | `flux.service.ts` | 14 types: `commandTextNode`, `scripting`, `apiCaller`, `mathFunction`, `counterNode`, `outputController`, `commandContentNode`, `voiceBoxNode`, `webSearch`, `webCrawling`, `mcpNode`, `pullData`, `pushData`, `imageGenerator` | the flow loop **and** `executeSingleNode` |
| `MIGRATED_TEMPORAL_NODE_TYPES` | `legacy-allowlist.ts` | **10 types, a different set**: `commandTextNode`, `scripting`, `apiCaller`, `mcpNode`, `mathFunction`, `counterNode`, `outputController`, `pullData`, `pushData`, `imageGenerator` | only `/process/single-node-legacy` validation (refuses these as "migrated") |
| `LEGACY_SINGLE_RUN_NODE_TYPES` | `legacy-allowlist.ts` | 7 types: `voiceBoxNode`, `voiceNode`, `webSearch`, `audioReaderNode`, `commandContentNode`, `reportBuilder`, `thirdPartyIntegration` | which types `/process/single-node-legacy` accepts and runs inline |
| `MUTATING_NODE_TYPES` | `legacy-allowlist.ts` | 5 types: `fluxBox`, `libraryNode`, `arrayNode`, `nodesBox`, `conditionNode` | which types the legacy endpoint refuses outright |
| `PREFETCH_SUPPORTED_NODE_TYPES` | `flux.service.ts` | 17 types — unchanged from the original count | whether a flow may use the prefetch executor |
| `MIGRATED_INTEGRATION_PROVIDERS` | `integration-executable-node.ts` | 9 providers — unchanged: stripe, wordpress, slack, notion, zapier, hubspot, supabase, pinecone, mcp | `isWorkerRoutedIntegration`, the flow loop and `executeSingleNode` |
| `DEDICATED_INTEGRATION_PROVIDER_BY_NODE_TYPE` | `integration-executable-node.ts` | `{ hubSpotCRM: 'hubspot' }` | which provider a non-`thirdPartyIntegration` node type resolves to |
| `isIntegrationExecutableNodeType` | `integration-executable-node.ts` | 2 hard-coded types: `thirdPartyIntegration`, `mcpNode` | which node types even look up a provider |
| `dispatchLegacyHandler` switch | `legacy-node-dispatch.ts` | 9 `case` arms | which types the legacy endpoint can actually execute, once past the two allowlists above |

`basedOnType` is a related failure mode — adding a node type with a referenceable field means
editing it by hand in more than one place, with nothing checking that you did — but it is **not**
part of this task's scope. See TASK-A1B for what it is, why it is smaller than first measured, and
why it needs a decision this task must not make on its own.

**The dispatch split-brain also grew, not just the list count.** `isTemporalNode` minus
`MIGRATED_TEMPORAL_NODE_TYPES` is `commandContentNode`, `voiceBoxNode`, `webSearch`, `webCrawling` —
four types, not the one (`thirdPartyIntegration`) the epic was scoped against. Three of them
(`voiceBoxNode`, `webSearch`, `commandContentNode`) run on the **worker** inside a flow
(`isTemporalNode` true) but the legacy single-node endpoint accepts them via
`isLegacyRunnableNode` and runs them **inline** via `dispatchLegacyHandler` — the exact
`thirdPartyIntegration` defect, now replicated three more times. `webCrawling` is in **neither**
allowlist, so `/process/single-node-legacy` refuses it with the wrong message — see the bounded
sub-item below.

Also live: the worker's `sqlQuerier` / `audioReaderNode` modules are reachable by nothing (A3),
and `legacy-node-dispatch.ts` has two dead branches (`case 'pullData'` / `case 'pushData'`) that
`validateNode` rejects before they can ever run — see Out, below; C2 owns their removal.

## Scope

**In.** One registry module in `back`, keyed by node type, with the facts each caller needs:

```
{
  workerModule,
  dispatch,
  integrationProviders?,
  prefetchSafe,
  mutating,
  hasInlineTwin: boolean,
  dispatchConflict?: { legacyRunnable: boolean },
}
```

`hasInlineTwin` and `dispatchConflict` are new fields, added by this correction. `hasInlineTwin`
carries what A3's invariant already needed (`workerModule: true` with `dispatch: 'inline'`).
`dispatchConflict.legacyRunnable` names the second, larger defect this correction found: a type can
have `dispatch: 'worker'` (it is in `isTemporalNode`) and simultaneously be accepted by
`/process/single-node-legacy` (it is in `LEGACY_SINGLE_RUN_NODE_TYPES`) — two different code paths
for the same node type, chosen by which endpoint the caller happened to hit. Today that is true for
exactly three types: `voiceBoxNode`, `webSearch`, `commandContentNode`.

Re-express all nine predicates as reads of the registry. Keep the function names — call sites
should not need to change, which keeps the diff reviewable.

**Out — moved to TASK-A1B (2026-09-21).** `basedOnType` and its two live copies
(`node-reference-substitution.service.ts`, `folw/contants.ts`) plus the dead one
(`flux/constants.ts`). A1's registry does not model `basedOnType` and does not gain a projection of
it; A1b decides, on a measurement, whether the two live copies become one source with named
projections or one unified map, and does the reconciliation. This task's only remaining connection
to that one is temporal: A1b depends on A1, because A1b's eventual registry entry needs A1's
registry to project from.

**In.** A `node_types.contract.json` in `back`, generated from the worker's `NodeType` enum, plus a
spec that fails when the registry claims a `workerModule` the enum does not have. **Reuse the
existing precedent instead of inventing a new fixture format:**
`back/src/app-mcp/node-types/node-handle-registry.ts` +
`back/src/app-mcp/node-types/node-handle-registry.spec.ts` + the `pnpm generate:node-handle-registry`
script (`package.json`) are already exactly this shape — generated committed fixture, regeneration
script, drift spec. CLAUDE.md's rule is to import the product's rule, never restate it; this
contract is the same rule applied to node types instead of node handles, so it should look like that
precedent (same three-piece shape: generated JSON/TS fixture, a `pnpm generate:*` script, a spec that
fails on drift), not a new design.

**In — new invariant, added by this correction.** A spec asserting: **no type may be in both
`isTemporalNode` and `LEGACY_SINGLE_RUN_NODE_TYPES`.** As of `back@origin/production` `3804a524` this
assertion is **false** for exactly three types — `voiceBoxNode`, `webSearch`, `commandContentNode` —
and `back` has no CI running jest, so a locally scoped run is the only gate that exists; a spec that
is simply red on arrival would poison every local run someone does before this task's PR lands.

**Mechanism, pinned: `it.failing()`.** `back` is on jest `29.3.1` (`back/package.json`, the `jest` devDependency);
`test.failing`/`it.failing` landed in jest 29.0, so it is available without a version bump. Write
**two** things, not one spec:

1. Three named `it.failing()` cases, one per known-broken type —
   `it.failing('voiceBoxNode is worker-routed and still legacy-runnable', ...)`, and the same for
   `webSearch` and `commandContentNode` — each asserting the invariant for that one type. `it.failing`
   inverts reporting: the assertion inside genuinely fails today (the invariant **is** violated), so
   jest reports the case as **passing** — the suite stays green on arrival, not red. The moment C1
   deletes that type's inline twin and removes it from `LEGACY_SINGLE_RUN_NODE_TYPES`, the assertion
   inside starts succeeding, and `it.failing` reports that as a **failure** — the suite goes red at
   exactly the moment the fix lands, which is the signal to drop that case (or, once all three are
   gone, delete the `it.failing` cases and replace them with the plain assertion below).
2. One plain `it()` — not `.failing` — asserting the invariant holds for **every other** type in the
   reconciled worker-enum/MCP-metadata source (the same source the behaviour-neutrality table uses).
   This is what catches a **fourth** type falling into the same trap later: `it.failing` only ever
   watches the three types it names, so without this second assertion a new violation would pass
   silently, exactly the failure mode the invariant exists to prevent.

Do not weaken either assertion to make it pass early: naming a case is not the same as weakening it —
`it.failing` still records that the bug exists and where, and it still turns red the day it stops
being true. A spec quietly made to expect the current bug with no mechanism forcing it to be revisited
is a snapshot, not an invariant; a spec that screams the day the bug is fixed is the invariant this
task asks for.

**In — bounded sub-item, added by this correction.** `webCrawling` is in neither
`MIGRATED_TEMPORAL_NODE_TYPES` nor `LEGACY_SINGLE_RUN_NODE_TYPES`, so `single-node-legacy.service.ts`
(`validateNode`)'s `isLegacyRunnableNode` check falls through to the generic refusal — grep for
`is not supported for single-node legacy execution` — instead of the correct one — grep for
`is migrated to Temporal` — which is what every other worker-routed type gets when it
hits this endpoint. The fix is one line: add `webCrawling` to whichever check
`isMigratedTemporalNode` reads once the registry exists, so it takes the same branch as the other
thirteen `isTemporalNode` types. This is naturally C3's territory — a pre-existing defect in code
being touched, not new behaviour — and the default is to carry it there so A1 stays
behaviour-neutral. It is written here as a bounded, explicit sub-item, with its own Done-when line
below, because the message a caller sees is small enough that fixing it inside A1, in the same PR
that builds the registry, costs less than a second coordinated deploy through C3. Whoever picks up
this task decides which PR it lands in; either way it must land, and it is not to be left as an open
question in either task.

**In.** Reconcile the unaccounted types from the prefetch whitelist. `comment`, `label`, `group`
were the original three (decision **D5**, PLAN §7); the 2026-09-21 correction added a fourth,
`voiceNode`, which is in `LEGACY_SINGLE_RUN_NODE_TYPES` and in `legacy-node-dispatch.ts`
(`dispatchLegacyHandler`, the shared `case 'voiceBoxNode': case 'voiceNode':` arm) but is
registered in **no** node-type source — not `front/src/util/nodeTypes.tsx` (46 types) and not
`back/src/app-mcp/node-types/node-type-metadata.ts` (50 entries).

**This paragraph used to say "remove all four from wherever they are trusted". That instruction was
measured and is wrong for three of the four.** It is corrected here rather than quietly dropped, so
the next reader can see what changed and why — see **What D5 actually returned** below. `comment`,
`label` and `group` **keep their registry entry and stay prefetch-safe**. `voiceNode` is **no longer
part of this task** — its own measurement was never run, so removing it would repeat the mistake
this correction is recording. It moved to **TASK-A1C** (added 2026-09-22).

**Out.** Changing what any node type does. A1 must be behaviour-neutral: same types dispatched,
same refusals (except the one named `webCrawling` message, above), same prefetch eligibility. The
inconsistencies it exposes get fixed by the tasks that own them (A2, A3, C1) — this task only makes
them visible in one place.

**Out.** Deleting the two dead branches in `legacy-node-dispatch.ts`'s `dispatchLegacyHandler`
(`case 'pullData'` / `case 'pushData'` — both types are in `MIGRATED_TEMPORAL_NODE_TYPES`, so
`validateNode` rejects them before the switch is ever reached).
**Moved to C2** (2026-09-21 correction) — it is legacy-surface removal, not registry work; A1 only
needs to record their existence as evidence for why the legacy endpoint has an empty effective
destination set.

## Steps

1. Write the registry with today's values, entry per node type, sourced from the nine lists.
2. Give `comment`, `label` and `group` a registry entry marked `phantom`, and keep them
   prefetch-safe (D5, decided by the measurement in **What D5 actually returned**). Bind the
   registry's prefetch-safe set to the canonical `NON_EXECUTABLE_NODE_TYPES` with a spec, so the two
   cannot drift. `voiceNode` is TASK-A1C's, not this task's.
3. Rewrite `isTemporalNode`, `isWorkerRoutedIntegration`, `isMigratedTemporalNode`,
   `isLegacyRunnableNode`, `isMutatingNodeType`, `canUsePrefetchForFlow`, and
   `isIntegrationExecutableNodeType` as registry reads.
4. Fix `webCrawling`'s refusal message (bounded sub-item, above), in this PR or C3's — record which.
5. Add the generated contract fixture + drift spec, shaped like `node-handle-registry.ts` +
   `node-handle-registry.spec.ts` + `pnpm generate:node-handle-registry`.
6. Add the `hasInlineTwin` / `dispatchConflict` invariant: three named `it.failing()` cases
   (`voiceBoxNode`, `webSearch`, `commandContentNode`) plus one plain `it()` covering every other
   type. Confirm the suite is green on arrival — the three `it.failing` cases pass because the bug
   they name is still real — and say so in the PR.

`basedOnType` is not a step here — it is TASK-A1B, which starts once this task's registry exists.

## What D5 actually returned

**Added 2026-09-22, after the implementation.** The Scope above originally instructed A1 to remove
`comment`, `label` and `group` from `PREFETCH_SUPPORTED_NODE_TYPES`. That removal was implemented,
measured, and **reverted**. The instruction was written before anyone measured it; PLAN §3.3.2's
"measure before refusing" rule outranks it, and this section is the record so the reversal is not a
silent divergence between this file and the shipped code.

**Why the removal was wrong.** `canUsePrefetchForFlow` is a *refusing* rule: a flow is prefetch-
eligible only if **every** node in it is whitelisted, so deleting a type from the whitelist takes
prefetch away from any flow containing it. `back/src/app-api/flux/prefetch/is-non-executable.ts`
already declares `NON_EXECUTABLE_NODE_TYPES = {comment, label, group}`, and
`prefetch-flow-executor.ts:109` skips exactly those types at execution time. The three are on the
whitelist **deliberately**: they are canvas decorations, and whitelisting them means dropping a
comment onto a canvas cannot cost that flow its prefetch eligibility. Removing them would have
converted "decoration tolerated" into "decoration disqualifies the flow" — a false refusal, and a
direct violation of this task's own Out clause ("same prefetch eligibility").

**The measurement** (live canvases, `flow_version_history_id IS NULL`, last 4 months):

| Base | flows total | prefetch-eligible today | containing a phantom | would lose prefetch |
|---|---|---|---|---|
| production | 15984 | 78 | 0 | 0 |
| dev | 4476 | 1 | 1 | 0 |

A control run on the same query shape returns rows (`commandTextNode`: 9207 nodes across 4134
flows), so the zeros are a measured result and not an empty result set. The queries are
`etc/a1-q1-phantom-types-prod.sql` and `etc/a1-q3-prefetch-blast-radius-prod.sql`.

Note what the zeros do and do not say. `would lose prefetch = 0` means the removal would have been
harmless **on the flows stored on the day it was measured**. It does not make the removal correct:
the next flow someone decorates with a comment would have silently lost prefetch, and nothing in the
codebase would have said so. The rule is kept because it is the right rule, not because the blast
radius happened to be empty.

**What shipped instead.** All three keep a registry entry marked `phantom` (recording that they are
absent from `front/src/util/nodeTypes.tsx` and `node-type-metadata.ts`) and keep `prefetchSafe:
true`. A spec binds the registry's prefetch-safe set to the canonical `NON_EXECUTABLE_NODE_TYPES`,
so neither set can grow without the other.

**`voiceNode` is not covered by any of this.** The measurement above covers only the prefetch
whitelist. `voiceNode` sits in `LEGACY_SINGLE_RUN_NODE_TYPES` and in the legacy dispatch switch,
which is a different surface with a different blast radius, and no query was ever run against it.
Removing it on the strength of a measurement that did not look at it is exactly the error this
section records. It is TASK-A1C.

## Verification

- **Negative control (required).** Delete one type from the registry, run the suite, and record
  which test went red and with what message. Then flip a `dispatch` value and confirm the
  behaviour-neutrality spec catches it. State both observed failures in the PR.
- **Behaviour neutrality.** Replace the old fixed target ("48 registered types") with the **defined
  canonical source**: the worker's `NodeType` enum, reconciled against
  `back/src/app-mcp/node-types/node-type-metadata.ts` — the same reconciliation the contract fixture
  in Scope encodes. For every type in that reconciled set, assert the new predicates return exactly
  what the old lists returned. Table-driven, one case per type — this is the test that makes the
  refactor safe. **Do not hard-code a new count in this spec or the test's assertions;** the count is
  whatever the reconciled source contains on the day the test runs, and a hard-coded number is
  exactly the kind of restated fact that drifted the first time (§ Why, above — "48" matched no real
  source when re-checked).
- **`dispatchConflict` invariant.** Confirm the suite is green on arrival with the three
  `it.failing()` cases (`voiceBoxNode`, `webSearch`, `commandContentNode`) passing — i.e. each
  assertion inside genuinely fails, because the type really is in both lists — and the plain `it()`
  covering every other type also passing. State both in the PR description. As a negative control for
  the invariant itself: temporarily fix one type's conflict (remove it from
  `LEGACY_SINGLE_RUN_NODE_TYPES` in a scratch change) and confirm its `it.failing` case turns red,
  proving the mechanism actually watches the thing it claims to.
- **Measure before refusing** (PLAN §3.3.2): `canUsePrefetchForFlow` is a refusing rule. Run the new
  implementation against real stored flows and confirm the set of flows it accepts is identical to
  today's. Report any difference as a defect in this task, not as an improvement.
- **D2's measurement, reported here.** While `canUsePrefetchForFlow` runs against every stored flow
  for the check above, record how many flows satisfy the whitelist, how many of them ran with
  `FLUX_EXEC_MEMORY_MODE=prefetch`, and what it saved. Report the numbers in the PR — B3 answers D2
  with them (Wave 4) and C2 executes the answer (Wave 6). Unknown is unverifiable, not zero.

## Done when

The registry is the source every dispatch *predicate* reads. One list is pinned rather than derived:
`legacy-node-dispatch.ts`'s `dispatchLegacyHandler` keeps its literal `case` arms, because they
select a **handler**, not a dispatch verdict — a spec asserts the arms are exactly
`registeredNodeTypes().filter(legacyEndpointAccepts)` plus the known-unreachable ones, so the two
cannot drift apart silently. Eight of the nine lists derive; the ninth is drift-checked. Say that
plainly rather than claiming the registry is the only place a node type is named.

The drift spec is green; the `dispatchConflict` invariant exists as three named `it.failing()` cases
plus one plain `it()` for every other type, the suite is green on arrival, and the PR states that;
`comment`, `label` and `group` carry a `phantom`-marked registry entry and remain prefetch-safe, with
a spec binding that set to `NON_EXECUTABLE_NODE_TYPES` (D5, per **What D5 actually returned**), and
`voiceNode` is handed to TASK-A1C; `webCrawling`'s refusal message is fixed (in this task or
explicitly handed to C3, not left unresolved); the behaviour-neutrality table covers every type in
the reconciled worker-enum/MCP-metadata source; no other production behaviour changed. `basedOnType`
is explicitly out — TASK-A1B's done-when, not this task's.

## Files

`back/src/app-api/flux/flux.service.ts` (`isTemporalNode`, `PREFETCH_SUPPORTED_NODE_TYPES`,
`canUsePrefetchForFlow`) ·
`back/src/shared/integration/integration-executable-node.ts` (`MIGRATED_INTEGRATION_PROVIDERS`,
`DEDICATED_INTEGRATION_PROVIDER_BY_NODE_TYPE`, `isIntegrationExecutableNodeType`,
`isWorkerRoutedIntegration`) ·
`back/src/temporal/single-node-legacy/legacy-allowlist.ts`
(`MIGRATED_TEMPORAL_NODE_TYPES`, `LEGACY_SINGLE_RUN_NODE_TYPES`, `MUTATING_NODE_TYPES`) ·
`back/src/temporal/single-node-legacy/legacy-node-dispatch.ts` (`dispatchLegacyHandler` switch) ·
`back/src/temporal/single-node-legacy/single-node-legacy.service.ts` (`validateNode`, the
`webCrawling` refusal message) ·
`back/src/app-mcp/node-types/node-handle-registry.ts` + `.spec.ts` (shape precedent for the new
contract fixture, not modified here) ·
new registry module + fixture + specs ·
`worker/src/modules/nodes/nodes.types.ts` (read only, source of the fixture)
