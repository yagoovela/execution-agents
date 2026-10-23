# A6b — Decide `webTrends`

**Goal:** `webTrends` either executes in the worker or is retired, and the decision is written down.

**Depends on:** A1, A11. **Added 2026-10-23** from
[`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md).

## Why

A6 listed `webTrends` among the front-driven types (stage 1) and shipped without it. No decision
was recorded. The front still calls `SerpService` directly, so the node never runs in a flow.

## Scope

**In.** Measure how many stored flows use it and when one last ran. Then either migrate it as A6
migrated its siblings, or retire it from the canvas and the MCP metadata.

**Out.** Any other front-driven type.

## Done when

The decision and its numbers are recorded here, and the type is `worker` or removed.

## Files

`front/src/components/nodes/WebTrends.tsx` · the A1 registry · `back/src/app-mcp/node-types/node-type-metadata.ts`
