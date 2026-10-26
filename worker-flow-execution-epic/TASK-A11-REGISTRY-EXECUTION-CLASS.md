# A11 — Give every node type an execution class

**Goal:** every node type the product can put on a canvas has one entry in the dispatch registry
that says where it executes, and every hand-kept type list is derived from that entry.

**Depends on:** A1. **Blocks:** turning the B4 flag on in production, B5's measurement.
**Added 2026-10-23** from [`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md).

## Why

The registry can say `worker` or `inline`, but it cannot say "does not execute". B4's gate
(`canUseWorkflowForFlow`, `back/src/app-api/flux/engine-selector.ts`) accepts a flow only when
every node is `worker` or one of five hard-coded passive types. So a Data Input, a sticky note or a
Small Memory node keeps the whole flow on the back's loop, and the loop can never be deleted.

The epic did map these types. PLAN §8 put the 11 inert types out of scope, but nothing turned "out
of scope" into a registry value, and four copies of the passive list grew instead:
`NON_EXECUTABLE_NODE_TYPES`, `WORKFLOW_SAFE_NON_WORKER_TYPES`, a literal list inside `apiV2`'s
logging, and the worker's `NON_EXECUTABLE_TYPES` with a "keep in sync" comment.

## Scope

**In.** An `execution` field on every registry entry: `worker`, `back` or `none`. Classify each
type from the code that reads or writes it at run time, not from its name.

| Class | Types (audit, 2026-10-23) |
|---|---|
| `none`, visual only | `stickyNote`, `nodesGroup`, `richTextBox`, `comment`, `label`, `group`, `textBox` |
| `none`, configuration read by the projection | `storedDataCaller`, `deepRefNode`, `nodesAdd`, `mediaBox`, `outputTable`, `tableProcessor`, `dynamicSettingsNode` |
| `none`, run entry | `varInputNode` (the back binds run inputs before the loop) |
| `worker`, registry wrong today | `thirdPartyIntegration`, `hubSpotCRM` |
| MCP-only, no front component | `webNews`, `webMedia`, `webLocations`, `varInputForm` (classify or remove from the MCP metadata) |

**In.** Derive from the field: the four passive lists, `BACK_ONLY_PROJECTION_NODE_TYPES` (back and
worker), and the B4 gate. `tableProcessor` and `dynamicSettingsNode` read fields that no writer
stores in `outputData`; the worker projection reads them from the run seed instead, and they leave
the back-only list.

**In — the rule that prevents the next gap.** A drift spec fails when a type exists in the front's
`nodeTypes.tsx` or in `node-type-metadata.ts` without a registry entry, and when any derived list
disagrees with the registry.

**In — the end state as a test.** An expected-failure test (`it.failing`) asserts that no type is
classed `back`. It fails today by design; C2 turns it into a plain test when the last back type
leaves.

**Out.** Moving any execution. Classification only.

## Verification

- **Negative control (required).** Add a type to the front list without a registry entry and watch
  the drift spec go red. Remove a derived list's import and restore a literal copy, and watch it go
  red again.
- **Measure before refusing** (PLAN §3.3.2). Classify every stored production flow as eligible or
  ineligible for B4's gate before and after this task. Every flow that stays ineligible names the
  type that keeps it there, and that type has a task.

## Done when

Every canvas and MCP type has an `execution` class; no hand-kept type list remains; the drift spec
is green and has been seen red; the before/after eligibility counts are recorded here; the
workspace `CLAUDE.md` checklist "Adding or changing a node type" names the `execution` field.

## Files

`back/src/shared/node-dispatch/node-dispatch-registry.ts` and `node-dispatch-contract.json` ·
`back/src/app-api/flux/engine-selector.ts` · `back/src/app-api/flux/prefetch/is-non-executable.ts` ·
`back/src/app-api/flux/flux.service.ts` (the logging copy) · `back/src/app-api/flux/node-input-projection.ts` ·
worker `process-flow.workflow.ts` and the ported projection list · `front/src/util/nodeTypes.tsx` (read) ·
`back/src/app-mcp/node-types/node-type-metadata.ts` (read)
