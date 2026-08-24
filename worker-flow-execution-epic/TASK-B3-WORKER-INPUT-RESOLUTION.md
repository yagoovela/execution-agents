# B3 — The consumer resolves its own input

**Goal:** stop the API from pre-chewing every node's input. Each node reads its upstream outputs
by reference and resolves what it needs.

**Depends on:** B1, B2. **Blocks:** B4. **Blocked on:** decision **D2**.

## Why — and what already exists

Today the API resolves a node's input and pre-saves it before dispatch: `openNodeExecution`
INSERTs `node_executions.input`, and the worker only reads it (`fetch-node-row.ts:6–10` selects
`input` when `execId` is present, never the live row). While the API owns that step, the worker
cannot own the graph — every node needs a round trip through the back to become runnable.

**This is partly built already.** The prefetch executor is in production behind
`FLUX_EXEC_MEMORY_MODE=prefetch` (analysis §9.2.1): `scanPlaceholderRefs` discovers only the refs
a node actually uses, `loadOutputsByRefs` fetches only those rows from `node_executions`, a small
per-node `schemaForNode` is built instead of mutating the global one, outputs travel as
`OutputPointer`, and `assembleFinalOutputsFromDb` assembles at the end.

So this task is **not** a design task. It is: measure what exists, decide whether it is the
destination, and move it to the worker side of the boundary.

## Scope

**In.** Answer D2 with the measurement from C2 in hand: how many production flows satisfy the
17-type whitelist, and what the prefetch path actually saved. A flag defaulting to `legacy` whose
whitelist excludes every LLM node and every control-flow node may be shipped but dormant.

**In.** Then either widen and relocate the prefetch executor, or implement resolution in the
worker using the substitution service from B2 — with the prefetch path retired by C2.

**In.** Either way: `node_executions.input` changes meaning. It stops being a **precondition for
running** and becomes a **record of what the node ran with**. Keep writing it; the run history and
debugging depend on it.

**Out.** Removing the back's copy. It stays until this is proven — PLAN §3.2, and this step must
be reversible above all others.

## Verification

- **Negative control (required).** Point a node at an upstream that has not completed and confirm
  it fails loudly rather than resolving to an empty string. Silent empty resolution is the failure
  mode that will otherwise reach production and look like a prompt bug for weeks.
- **Output equivalence over real flows.** For a corpus of stored runs, resolve each node's input
  both ways and diff. Placeholder resolution has three key shapes per node in the schema
  (`nodeId`, normalised ref-key, lowercased label alias) — cover all three, including the alias
  collision case where two nodes share a label.
- **Measure before refusing** (PLAN §3.3.2): whatever gate decides "this flow can resolve
  worker-side" is a refusing rule. Classify every refusal against real stored flows and drive
  refused-although-it-works to zero.

## Done when

A node can be made runnable without the API resolving its input; equivalence is proven; the back's
path is still present and revertible by flag.

## Files

`back/src/app-api/flux/prefetch/**` · `back/src/temporal/single-node-legacy/node-execution-store.ts` ·
`worker/src/modules/nodes/shared/fetch-node-row.ts` · the substitution module from B2
