# B6 — Control flow and sub-flows in the workflow

**Goal:** `conditionNode` and `arrayNode` become workflow control flow; `fluxBox` and `libraryNode`
become child workflows. The last four node types leave the back.

**Depends on:** B4. Can run alongside B5.

## Why these four are not activities

They do not compute values — they decide what runs next, or they run whole flows. An activity's
return value cannot reshape the caller's iteration (analysis §3.3–§3.7):

| Type | What it actually does | Where it belongs |
|---|---|---|
| `conditionNode` (`flux.service.ts:6742`) | evaluates `conditions[]`, mutates `currentLoopCounter` in place, and **rewrites the engine's work queue** via `newIds = findConnectedNodes(...)` | workflow control flow, calling `completeCondition(state, id, handle)` |
| `arrayNode` (inline `:3738`) | slices a sub-range of the ordered node list between `firstId` and `loopingToId` and re-executes it per array item | a workflow loop; possibly a child workflow per iteration |
| `fluxBox` (`:5400`) | executes another whole flow inside the node, inheriting the parent's run-log collector, cancel key and trigger counters | child workflow |
| `libraryNode` (`:5717`) | structurally the same as `fluxBox`; the engine already treats them together (`:2660`, `:3287`) | child workflow — **migrate as one unit with `fluxBox`**, or the contract gets written twice |

Once B4 exists, these stop being blocked and become the natural content of the workflow. That is
the inversion this epic is built on.

## Scope

**In.** Condition and loop semantics expressed as deterministic workflow control flow. Temporal
workflows must be deterministic on replay — loop counters and condition results must come from
activity results or workflow state, never from ambient time or randomness.

**In.** Child workflows for `fluxBox` / `libraryNode`, carrying what the parameter list carries
today: cancellation propagation (native to Temporal child workflows), nested run logs so child
node logs still appear under the parent, and billing attributed to the parent's `billingFlowId`.

**In.** The loop-body computation already exists as `computeLoopBody` in the scheduler — use it
rather than re-deriving the body from indices, which is what the inline `arrayNode` does.

**Out.** Changing what a condition means or how a loop terminates. The `evaluateLoopCondition`
behaviour, including the maximum-iteration guard, ports as-is.

## Verification

- **Negative control (required).** Make a loop's termination condition never fire and confirm the
  guard stops it — then confirm the workflow surfaces it as a real failure, not as a workflow that
  runs until its timeout. Do the same for a condition branch that marks the wrong handle: assert
  the dead branch is marked dead and its downstream nodes do not run.
- **Replay determinism.** Take a completed workflow history and replay it. Any non-determinism
  shows up here and nowhere else; this test is not optional for a control-flow workflow.
- **Nested runs.** A `fluxBox` inside a flow must produce nested run logs, propagate cancellation
  from the parent, and attribute tokens to the parent — verify all three, since each is carried by
  a different parameter today and each can be lost independently.
- Loop billing must match the pre-migration totals per iteration, using the identity from B1.

## Done when

All four types run in the worker; a replay test passes; nested runs keep their logs, cancellation
and billing; no executable node type remains inline.

## Files

`back/src/app-api/flux/flux.service.ts:3540, 3738, 4013, 5400, 5717, 6742` ·
`back/src/app-api/flux/scheduler.ts` (`completeCondition`, `computeLoopBody`) ·
worker flow workflow + new child workflow · the A1 registry
