# B1 — One reference per execution, not per node

**Goal:** make the identifier that travels between nodes name **one execution of a node**, not
"a node within a run". Everything in Track B that passes data by reference depends on this.

**Depends on:** nothing. **Blocks:** B3, and therefore B4/B5; also A7.

## Why

`(execId, nodeId)` is already the transport for a node's input and output. Inside a loop —
`arrayNode`, `conditionNode` — the same `nodeId` executes many times under one `execId`, and today
(analysis §8.4):

- `node_executions` has **no unique constraint** on `(execId, nodeId)`; only a plain index
  (`1776400000000-AlterNodeExecutionsForRunScopedIpc.ts:28`).
- `openNodeExecution` is a plain `INSERT`, no `ON CONFLICT`
  (`back/src/temporal/single-node-legacy/node-execution-store.ts:26–39`), so repeated executions
  insert additional rows.
- `persistNodeSuccess` updates `WHERE "execId" AND "nodeId"` — i.e. **every** such row
  (`worker/src/modules/nodes/shared/persist-node-success.ts:7–9`).
- `fetchNodeRow` takes `rows[0]` with **no `ORDER BY`** (`fetch-node-row.ts:31–47`); Postgres
  ordering is not guaranteed.

Contained today because the single-node path mints a fresh `execId` per click. It stops being
contained the moment a consumer reads an upstream's output by that pair, which is exactly what B3
introduces. Fixing it afterwards means changing the transport under running code.

## Scope

**In.** Choose and implement the identity. Two candidates:

- **`node_executions.id`** — the existing primary key — becomes the reference that travels.
  Cheapest; `(execId, nodeId)` stays a lookup, never a transport.
- **An iteration discriminator** added to the key, so `(execId, nodeId, iteration)` is unique.
  More invasive, but keeps the reference human-readable in logs and makes the loop position
  explicit — which B6 will want anyway.

**Pick one, write down why in this file.** The choice constrains B3 and B6.

**In.** Whichever wins: a unique constraint or an explicit documented reason there is none,
`ORDER BY` on every read that can match more than one row, and a targeted `persistNodeSuccess`.

**Out.** Changing loop semantics. B6 owns those; B1 only makes them addressable.

## Verification

- **Negative control (required).** Write a test that runs one node twice under the same `execId`
  and asserts the second read returns the second execution. Run it against `main` first and watch
  it fail — or pass by luck, which is the more likely and more alarming outcome. If it passes on
  `main`, force the row order (insert them out of order) until it fails, then fix and re-run.
- Backfill check: existing `node_executions` rows must remain readable. A migration that orphans
  historical rows breaks run history and the MCP run-status surface.
- `sumChargesByExecution(execId, nodeId)` (`flux.service.ts:710, 1998`) aggregates by the same
  pair. Confirm billing totals are unchanged for loops — this is the one place where "every
  matching row" was arguably the intended behaviour.

## Done when

No read that can match multiple rows relies on Postgres ordering; the transport identifies one
execution; loop billing is provably unchanged.

## Files

`back/src/entities/node_execution.entity.ts` · `back/src/temporal/single-node-legacy/node-execution-store.ts` ·
`back/src/database/migrations/` (new) · `worker/src/modules/nodes/shared/{fetch-node-row,persist-node-success}.ts` ·
`back/src/app-api/token_transaction/token_transaction.service.ts`
