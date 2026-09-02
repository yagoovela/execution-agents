# B6 — Control flow and sub-flows in the workflow

**Goal:** `conditionNode` and `arrayNode` become workflow control flow; `fluxBox` and `libraryNode`
become child workflows. The last four node types leave the back.

**Depends on:** B4, S1. Development can overlap B5's, but it ships after B5 (D17).

## Why these four are not activities

They do not compute values — they decide what runs next, or they run whole flows. An activity's
return value cannot reshape the caller's iteration (analysis §3.3–§3.7):

| Type | What it actually does | Where it belongs |
|---|---|---|
| `conditionNode` (`flux.service.ts`) | evaluates `conditions[]`, mutates `currentLoopCounter` in place, and **rewrites the engine's work queue** via `newIds = findConnectedNodes(...)` | workflow control flow, calling `completeCondition(state, id, handle)` |
| `arrayNode` (inline branch, no handler method) | slices a sub-range of the ordered node list between `firstId` and `loopingToId` and re-executes it per array item | a workflow loop; possibly a child workflow per iteration |
| `fluxBox` (`flowCallerNode()`) | executes another whole flow inside the node, inheriting the parent's run-log collector, cancel key and trigger counters | child workflow |
| `libraryNode` (`libraryNode()`) | structurally the same as `fluxBox`; the engine already treats them together | child workflow — **migrate as one unit with `fluxBox`**, or the contract gets written twice |

Once B4 exists, these stop being blocked and become the natural content of the workflow. That is
the inversion this epic is built on.

## Scope

**In.** Condition and loop semantics expressed as deterministic workflow control flow. Temporal
workflows must be deterministic on replay — loop counters and condition results must come from
activity results or workflow state, never from ambient time or randomness.

**In.** Child workflows for `fluxBox` / `libraryNode`, carrying what the parameter list carries
today: cancellation propagation (native to Temporal child workflows), nested run logs so child
node logs still appear under the parent, and billing attributed to the parent's `billingFlowId`.

**In — the run chain.** The child carries a `parentRunId` back to its caller, and the visited-flow
set and depth counter travel with it (`TASK-S1`). Three things depend on that chain existing at this
boundary and not only inside one process: the cycle refusal, the depth ceiling, and the spend
ceiling that `TASK-S3` applies to the chain root. **A child workflow started without the chain is a
child workflow with no ceilings at all** — and unlike today, a durable platform will sustain the
result across the fleet.

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
and billing — **cancelling a parent stops its child workflows, proven here because no child workflow
exists before this task** (moved from E2); no executable node type remains inline.

## Files

`back/src/app-api/flux/flux.service.ts` (`conditionNode()`, `flowCallerNode()`, `libraryNode()`, the inline `arrayNode` branch) ·
`back/src/app-api/flux/scheduler.ts` (`completeCondition`, `computeLoopBody`) ·
worker flow workflow + new child workflow · the A1 registry
