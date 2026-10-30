# B2 — Decide code sharing, then extract the scheduler and the substitution service

**Goal:** get the two pure modules the worker needs out of `back` — under a decision that is made
once, deliberately, rather than by whoever writes B3 first.

**Depends on:** nothing to start. **Closes after:** A8 (`868m0vmpz`) reaches production — see
[The A8 resync](#the-a8-resync). **Blocks:** B3, B4. **Decision D1:** answered 2026-10-02 —
copy-port with a drift test.

## Why these two, and why it is a decision

**Corrected 2026-10-02**, against `back@origin/production` `bc727827`. The first version of this
section (2026-09-02) called both modules pure and listed their API from memory. Three of its claims
were wrong, and the corrections below are the reason the extraction is more than a copy:

- **`scheduler.ts` was not pure.** Line 1 imported `singleConditionCheck` from
  `folw/helpers/helpers.ts` (2,406 lines), which pulls in `flux/execution-budget` (reads
  `process.env`), `folw/helpers/loop-iteration-context` (`AsyncLocalStorage` from `async_hooks`)
  and a cycle with `folw/contants.ts`. A Temporal workflow bundle refuses `async_hooks` outright, so
  the scheduler as it stood could not have run where B4 needs it. The function moves verbatim to
  `flux/condition-check.ts` (60 lines, no imports); `scheduler.ts` and `flux/constants.ts`, its only
  two callers, import it from there.
- **The substitution service changed after this spec was written.** It is 304 lines, not 268.
  `processFlowWithSubstitution` was removed on 2026-09-11 (`de4a94cb`), `syncPassthroughsFromNodes`
  was added, and it was touched again on 2026-09-17, 2026-09-22 and 2026-10-01. It is `@Injectable()`
  with no constructor dependencies, and its only import is `shared/node-fields/node-referenceable-fields`
  (127 lines, no imports) — so that file travels with it.
- **More consumers than the spec named.** The scheduler is also imported by
  `integrations/zapier-webhook-trigger.service.ts`, `app-mcp/mcp-run-nodes.service.ts` and
  `app-mcp/node-types/node-types.service.ts`; the substitution service also by its controller and the
  two `temporal/single-node-legacy/` files. None of them change — the back keeps its files where they
  are and remains the source.
- **The prefetch executor lives in the back, not the worker** (`flux/prefetch/prefetch-flow-executor.ts`,
  behind `FLUX_EXEC_MEMORY_MODE=prefetch`, default `legacy`). It reuses the back's substitution service
  through an injected interface rather than re-implementing it. The worker had no copy of either module.

The exported API is therefore: `scheduler.ts` — `classifyEdge`, `isDependencyEdge`,
`isConditionHandle`, `resolveConditionHandle`, `buildSchedulerState`, `nextReady`, `markCompleted`,
`markDead`, `completeCondition` (alias `pruneDeadBranch`), `computeLoopBody`, `planOrder`, the
handle constants and the `Sched*` types. `NodeReferenceSubstitutionService` — `replacePlaceholders`,
`generateSchemaFromNodes`, `syncPassthroughsFromNodes`, `applySubstitutionToObject`,
`updateSchemaWithNodeOutput`, `resolveTextDataFromSchema`.

The project rule is explicit — *import the product's rule; never restate it* — and a second copy of
the scheduler is the most expensive possible place for silent drift: it would mean the back and the
worker disagree about **what runs next**.

## Decision D1 — copy-port, with a drift test that runs

**Answered 2026-10-02: B, copy-port** (the page had recommended A, a shared package). What decided
it was measured, not argued:

- **There is no package infrastructure to build on.** No registry, no `.npmrc`, no `publishConfig`, no
  workspace or git dependency in back, worker or mcp-server. Both Dockerfiles `COPY . .` with the repo
  as build context, so a shared package needs a registry plus credentials in both image builds before
  it can ship anything — infra with no other reason to exist yet.
- **The two repos do not compile the same way** — back `commonjs`/`es2021`/`strictNullChecks: false`,
  worker `nodenext`/`es2023`/`strictNullChecks: true` — so even a package would have to be built for
  both.
- **A's condition for B was met.** The page said B wins only if the drift test can be made to fail
  automatically and someone names where it runs. Both are true below.

A shared package (A), a third submodule (C) and a monorepo (D) remain on the page with their
reasons; they were not rejected as wrong, only as more expensive for two files.

### What exists now

| piece | where | what it guarantees |
|---|---|---|
| the manifest | `back/scripts/sync-ported-engine.ts` · `PORTED_ENGINE_FILES` | the four files that form the closed set: `flux/condition-check.ts`, `flux/scheduler.ts`, `node-reference-substitution/node-reference-substitution.service.ts`, `shared/node-fields/node-referenceable-fields.ts` |
| the sync | `pnpm sync:ported-engine` (back) | copies them **byte-for-byte** to `worker/src/ported/back/` at the same relative paths, so every import resolves unchanged; refuses while a manifest file is uncommitted, so the recorded SHA is real |
| the record | `worker/src/ported/back/PORTED_FROM.md` | the source commit and a sha256 per file — written by the sync, never by hand |
| the drift test | `back/src/shared/ported-engine/ported-engine-drift.spec.ts` | fails when a worker copy differs, is missing, or an unlisted file sits in the ported root; **always** fails when a manifest file imports anything outside the manifest except `@nestjs/common` (used only by the substitution service), which is what keeps the scheduler workflow-safe |
| the worker self-check | `worker/src/ported/ported-from.spec.ts` | fails when a copy no longer matches the sha256 the sync recorded (catches an edit made in the worker), and proves both modules load and run from the worker |
| Biome | `worker/biome.json` excludes `src/ported/back` | the worker formats with double quotes; without the exclusion the first `biome check --write` would rewrite every copy and break byte equality |

Two **type-only** edits went into the back sources so the copies compile under the worker's
`strictNullChecks` without diverging: `let value = undefined;` → `let value;` in
`generateSchemaFromNodes` (the same runtime `undefined`, but it no longer narrows to `never`), and
`text as string` at the `singleConditionCheck` call in `resolveConditionHandle` (the non-strict back
already passed it unchecked). With them the copies add **0** errors to the worker's `tsc` (its
pre-existing baseline on `main` `8962e10` is 52).

### How the drift test actually runs

Neither repo runs tests in CI — back's and worker's workflows build and deploy only (PLAN §3.5). So
the drift test is a **local gate**, and this is where it is owed:

1. **Any PR that touches a manifest file in back** runs
   `jest src/shared/ported-engine` with the worker checked out as the sibling `../worker` (the
   workspace layout) or `WORKER_REPO_PATH` set. Red means: run `pnpm sync:ported-engine`, commit the
   worker change, and ship both — worker first, since nothing there is reachable until B3/B4 consume it.
2. **Any PR that touches `worker/src/ported/`** runs `jest src/ported` in the worker. It needs no back
   checkout.
3. Without a worker checkout the byte comparison **skips** rather than passes (`resolveWorkerRoot`'s
   typed error, the same mechanism `node-types-contract.spec.ts` uses and tests); the closure test and
   the detector's own tests still run.

`validate-changes` should call both when those paths change; until it does, the PR body states that
they were run.

### The A8 resync

A8 (`868m0vmpz`) adds `'imageReaderNode'` to `SIDE_EFFECT_TYPES` in `scheduler.ts`. It is on dev
(`master`, `6ebf202c`) but not on production. B2 extracts from **production**, by decision, so when
A8 reaches production the drift test goes red — on purpose. B2 does not close until that happens and
the worker copy is resynced in the same delivery; ClickUp carries it as B2 *waiting on* A8. Starting
B2 never waited on A8: the two changes touch different lines of the file.

## Scope

**In.** Answer D1, record the decision and its rationale in this file, then execute it.

**Out.** Changing either module's behaviour. Extraction is behaviour-neutral; `nextReady`'s batch
sibling belongs to B4.

**Checked before B4 writes `allReady()`:** `@temporalio/workflow` 1.14.1 exports no ready-set or DAG
primitive — its workflow-side surface is `condition`, `proxyActivities`/`scheduleActivity`,
`executeChild`/`startChild`, `continueAsNew`, signals/updates and `sleep`. Draining the ready set is
`Promise.all`/`Promise.race` over activity promises fed by the scheduler. D16 is unchanged: the DAG
decides what is ready, and B4 drains it. (The SDK's published samples were not re-checked offline.)

## Verification

- **Negative control (required) — done 2026-10-02.** `classifyEdge`'s condition branch changed to
  return `'data'` in the worker copy: the drift test went red naming `src/app-api/flux/scheduler.ts`,
  `reason: different`; restored, green. Second control: re-adding the `folw/helpers/helpers` import to
  `scheduler.ts` turned the closure test red naming that specifier. The worker self-check went red on
  its own when two copies were updated by hand without re-running the sync.
- **Behaviour equivalence — done 2026-10-02, over the dev database.** All 4,875 stored graphs (every
  non-deleted `(flow_id, flow_version_history_id)` node/edge set, live copies included) were run
  through back's **original production** `scheduler.ts` (`bc727827`, still importing `helpers.ts`) and
  through the worker copy compiled by the worker's own `tsconfig`. `SchedulerState` (every field, in
  insertion order), `planOrder` and `resolveConditionHandle` for all 362 condition nodes: **4,875 of
  4,875 identical**; 4,450 graphs had a non-empty order; none threw. The harness can fail: with the
  `classifyEdge` mutation above, 174 graphs differed. Harness and how to re-run it:
  `scripts/b2-scheduler-equivalence/README.md`. Production was not measured — dev only, by rule.
- **Workflow-bundle check.** A probe workflow importing the worker copy of `planOrder` bundles with
  `bundleWorkflowCode`; the same probe importing `async_hooks` is refused
  (`disallowed modules: 'async_hooks'`), which is what the old `helpers.ts` import would have caused.
  This holds for the scheduler and `condition-check.ts` only. The substitution service imports
  `Injectable` from `@nestjs/common`, and a probe importing it fails to bundle (`Can't resolve
  'class-validator'`). Use it from activities, which run in the Nest context its spec already
  exercises. Do not use it from workflow code.
- **Re-validated 2026-10-05, before ready for QA**, back `feat/868m0vmw3` @ `439501fb` against worker
  `feat/868m0vmw3` @ `aa4e697`:
  - **Back Jest.** The 7 specs covering the touched files pass (64/64), including the drift spec
    (7/7), whose worker test ran rather than skipped.
  - **Worker Jest.** `ported-from.spec.ts` passes (5/5).
  - **Worker `tsc`.** 52 errors in total, the same as the `main` baseline, and 0 in `src/ported`.
  - **Negative control repeated.** The `classifyEdge` mutation turned the back drift test red
    (`scheduler.ts`, `different`) and the worker hash test red. Restoring the line turned both
    green again.
  - **Equivalence re-run against production.** The baseline was back `production` @ `6dd9afae`,
    over the dev database. 4,878 of 4,878 graphs were identical: 4,453 had an order, 362 were
    condition nodes, and none threw. Under the mutation, 174 differed.
- **QA on dev, 2026-10-05.** Back `master` @ `b7a179d2` and worker `develop` @ `ba423fd`, both
  deployed and both containing B2. The agent `18de9c0d-1a17-4b02-a4d1-5bec03b5fb98` ("B2 QA - condition
  SWITCH routing", workspace "Product Dev - Testing") was built through the dev MCP. It holds a
  `conditionNode` in SWITCH mode (`> 100`, `> 10`) with each handle wired to its own `mathFunction`.
  Text `42` ran only `conditionHandle-T1`, `500` ran only `T0`, and `5` ran only `F1`. That is the
  scheduler's `resolveConditionHandle` going through the relocated `singleConditionCheck` on the
  deployed back. The branch nodes executed on the deployed worker. No run had an error, and none
  spent a token.

## Done when

D1 is answered in writing; both modules are consumable from the worker; equivalence is proven over
real flows; drift is detected by a test, not by convention; and the worker copy matches production
after A8 ships.

## Files

`back/src/app-api/flux/condition-check.ts` (new) · `back/src/app-api/flux/scheduler.ts` ·
`back/src/app-api/flux/constants.ts` · `back/src/app-api/folw/helpers/helpers.ts` ·
`back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts` ·
`back/scripts/sync-ported-engine.ts` (new) · `back/src/shared/ported-engine/ported-engine-drift.spec.ts` (new) ·
`worker/src/ported/back/**` (generated) · `worker/src/ported/ported-from.spec.ts` (new) · `worker/biome.json` ·
`worker-thirdparty-integration-migration/PLAN.md` (prior art)
