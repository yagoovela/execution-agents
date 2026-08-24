# B2 — Decide code sharing, then extract the scheduler and the substitution service

**Goal:** get the two pure modules the worker needs out of `back` — under a decision that is made
once, deliberately, rather than by whoever writes B3 first.

**Depends on:** nothing. **Blocks:** B3, B4. **Blocked on:** decision **D1**.

## Why these two, and why it is a decision

Both modules are **pure** — no NestJS injection, no database, no I/O:

- `back/src/app-api/flux/scheduler.ts` — `buildSchedulerState` (`:152`), `classifyEdge` (`:46`),
  `isDependencyEdge` (`:59`), `nextReady` (`:295`), `markCompleted` (`:352`), `markDead` (`:359`),
  `completeCondition` (`:366`), `computeLoopBody` (`:393`), `planOrder` (`:412`). Already the
  single source of ordering truth, consumed by `flux.service.ts:1463, 3136, 3227` and by
  `app-mcp/mcp-write.service.ts:1327`.
- `back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts` — 268
  lines, no injected dependencies: `replacePlaceholders`, `generateSchemaFromNodes`,
  `applySubstitutionToObject`, `updateSchemaWithNodeOutput`, `resolveTextDataFromSchema`,
  `processFlowWithSubstitution`.

Purity is what makes sharing cheap here and what makes copying tempting. The project rule is
explicit — *import the product's rule; never restate it* — and a second copy of the scheduler is
the most expensive possible place for silent drift: it would mean the back and the worker disagree
about **what runs next**.

Against that: `back` and `worker` are separate git repos wired as submodules, with no shared build
graph and no root workspace. The `thirdPartyIntegration` migration weighed the same question and
chose copy-port, for reasons recorded in `worker-thirdparty-integration-migration/PLAN.md` — but
that was for adapter code that dragged heavy dependencies. These two drag nothing.

## Scope

**In.** Answer D1, record the decision and its rationale in this file, then execute it.

**If shared package:** the package, its release process, and the submodule-bump ordering
(submodule pushed before the superproject, always).

**If copy-port:** a `PORTED_FROM.md` per module carrying the source SHA, plus a **drift test** —
not a comment asking people to be careful. The test must fail when the two copies diverge. Given
the back has no CI test run (PLAN §3.5), state plainly how the drift test will actually be run.

**Out.** Changing either module's behaviour. Extraction is behaviour-neutral; `nextReady`'s batch
sibling belongs to B4.

## Verification

- **Negative control (required).** Change one branch of `classifyEdge` in the extracted copy and
  confirm the drift test (or the package's own suite) goes red. If copy-port was chosen and this
  test cannot be made to fail automatically, copy-port is not viable — say so and revisit D1.
- Behaviour equivalence: run both implementations over every stored flow's node/edge set and
  assert identical `SchedulerState` and identical `planOrder`. This is a pure function over data
  that already exists, so full coverage is achievable — take it.

## Done when

D1 is answered in writing; both modules are consumable from the worker; equivalence is proven over
real flows; drift is detected by a test, not by convention.

## Files

`back/src/app-api/flux/scheduler.ts` · `back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts` ·
`worker/src/**` (new consumption point) · `worker-thirdparty-integration-migration/PLAN.md` (prior art)
