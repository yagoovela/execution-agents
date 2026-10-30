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

**In — cancellation propagates down the chain, per `D23` (moved from E2 on 2026-10-26, E2-d).**
A `fluxBox`, `libraryNode` or `arrayNode` is not allowed to finish the way a generation is: its
execution is an open-ended amount of further work. Cancelling one cancels its children. For
`arrayNode`, the element already generating finishes; the remaining elements never start.
**`nodesBox` is not in this list:** it dispatches to `objectCaller`, which executes no nodes and
only reads and writes an object's session state, so cancelling it prevents no spend and leaves the
object half-written.

**In — the run chain.** The child carries a `parentRunId` back to its caller, and the visited-flow
set and depth counter travel with it (`TASK-S1`). Three things depend on that chain existing at this
boundary and not only inside one process: the cycle refusal, the depth ceiling, and the spend
ceiling that `TASK-S3` applies to the chain root. **A child workflow started without the chain is a
child workflow with no ceilings at all** — and unlike today, a durable platform will sustain the
result across the fleet.

**In.** The loop-body computation already exists as `computeLoopBody` in the scheduler — use it
rather than re-deriving the body from indices, which is what the inline `arrayNode` does.

**In — each iteration receives its own item (added 2026-10-14).** Today a node wired straight to
the `arrayNode` `output` handle receives the **whole list** in every iteration. The rebuilt loop
delivers item *i* to iteration *i* on any wiring. This fixes a defect; it does not change what a
loop means, so the **Out** below still holds. See
[The item-per-iteration defect](#the-item-per-iteration-defect).

**Out.** Changing what a condition means or how a loop terminates. The `evaluateLoopCondition`
behaviour, including the maximum-iteration guard, ports as-is.

## Decisions (2026-10-23)

| Id | Question | State | Answer |
|---|---|---|---|
| B6-a | Is an array iteration a loop inside the workflow, or a child workflow per item? | **Settled, pending one measurement** | A loop inside the flow workflow (option A). It reuses `computeLoopBody` and the `continueAsNew` boundary that B4 defines (B4-a), so there is one mechanism. B4's history measurement confirms it: if one iteration's events times the largest real `arrayNode` list does not fit under the B4 boundary with margin, reopen this decision with that number. |

## The item-per-iteration defect

Found on 2026-10-14 while validating B1 in production. It predates B1: the overwrite below has run
on every worker dispatch since `2e6e1f44` (2026-07-01).

**What happens.** In each iteration the back writes the current item into the body node's
`contentData` / `promptData` (`getOutputByType`, `arrayNode` branch: `processorArray[completed]`).
Just before dispatch, `processNodeViaTemporal` → `fillRefArrayFields` → `resolveTextDataFromSchema`
rewrites those entries from the substitution schema. The schema entry for an `arrayNode` holds only
`content` (`NODE_REFERENCEABLE_FIELDS.arrayNode = ['content']`), which is the whole list, and no
iteration updates it. So the item is replaced by the list.

**Why a Text Box works around it.** A Text Box is a passthrough type: `syncPassthroughsFromNodes`
refreshes its schema entry from its own `textData` (the current item) before each dispatch. Users
put one between the loop and the AI node; with it, the loop behaves.

**Evidence.**

| Where | Flow | Result |
|---|---|---|
| Dev DB, `node_executions` | `a9933cf5-59f7-4a13-a9c6-a167f3711da0`, loop wired straight into the AI node | 3 AI executions; each input has `contentData[0].text = "red\ngreen\nblue"`; each output is all three colors |
| Prod, same wiring | `48da9b41-…` (W4B1 T1b), runs `efc5e51d`, `0aa7c346` | The AI node returns all three colors on every call |
| Prod, Text Box in between | `bb63e394-…` (W4B1 T1c), run `43f8976a` | Data Output `#0..#2` = `9`, `18`, `27`: one item per iteration |

**Suggested fix.** Treat the current item as the `arrayNode`'s output for that iteration, resolved
like any other upstream output. In today's back that is one call per iteration, before the body
runs: `updateSchemaWithNodeOutput(schema, arrayNodeId, label, item)`. In B6's workflow loop, pass the
item as the `arrayNode`'s per-iteration output to the body's input resolution (B3). A `{{<arrayNodeId>.text}}`
placeholder then resolves to the item too.

**How to validate.** Build this flow (no Text Box), set `arrayNode.executing` to the AI node's id,
and run it once:

```text
globalStarter    --a-----------> arrayNode.input
varInputNode     --output------> arrayNode.content          "red\ngreen\nblue", Custom Separator "\n"
arrayNode        --outputFlow--> commandTextNode.input
arrayNode        --output------> commandTextNode.contentIn  the item, no Text Box
commandTextNode  --output------> outputObjectNode.input
```

```sql
SELECT ne."execId", ne.input::jsonb -> 'contentData' -> 0 ->> 'text' AS item, left(ne.output, 40) AS output
FROM node_executions ne
WHERE ne."flowId" = '<flowId>' AND ne."nodeId" = '<commandTextNodeId>'
ORDER BY ne."createdAt";
```

1. Expect 3 rows with `item` = `red`, `green`, `blue`, and one color per output.
2. Negative control: revert the fix and run again. Expect `item` = `red\ngreen\nblue` on every row,
   as observed on 2026-10-14.

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
- **Item per iteration.** Run the flow in
  [The item-per-iteration defect](#the-item-per-iteration-defect) without a Text Box: each
  iteration's input holds one item. Revert the fix and watch it receive the whole list.

- **`arrayNode` cancel (D23, moved from E2 on 2026-10-26).** Cancel during the second element of a
  five-element array: the second element finishes, and elements three to five never start. Negative
  control: let the loop ignore the cancel and watch element three start.

## Done when

All four types run in the worker; a replay test passes; nested runs keep their logs, cancellation
and billing — **cancelling a parent stops its child workflows, proven here because no child workflow
exists before this task** (moved from E2); each loop iteration receives its own item on any
wiring, without a Text Box; no executable node type remains inline.

## Carried over from B3b (validate first)

`BACK_ONLY_PROJECTION_NODE_TYPES` (`back/src/app-api/flux/node-input-projection.ts`) keeps a flow
with an `arrayNode`, `fluxObject`, `nodesBox`, `libraryNode`, `fluxBox`, `tableProcessor` or
`dynamicSettingsNode` on the back's projection. It is a hand-kept list, apart from the dispatch
registry. When this task moves those types, remove each one from the list, or derive the list from a
registry field, and update `node-dispatch-contract.json`. Check whether `fluxObject`,
`tableProcessor` and `dynamicSettingsNode`, which are not in this task's four types, still need it.

**Answered 2026-10-23.** A11 derives the list from the registry and removes `tableProcessor` and
`dynamicSettingsNode`; A7 removes `nodesBox`; A14 removes `fluxObject`. This task removes only its
own four types.

## Files

`back/src/app-api/flux/flux.service.ts` (`conditionNode()`, `flowCallerNode()`, `libraryNode()`, the inline `arrayNode` branch) ·
`back/src/app-api/flux/scheduler.ts` (`completeCondition`, `computeLoopBody`) ·
worker flow workflow + new child workflow · the A1 registry
