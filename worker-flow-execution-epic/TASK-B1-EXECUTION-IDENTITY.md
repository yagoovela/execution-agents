# B1 — One reference per execution, not per node

**Goal:** make the identifier that travels between nodes name **one execution of a node**, not
"a node within a run". Everything in Track B that passes data by reference depends on this.

**Depends on:** nothing. **Blocks:** B3, and therefore B4/B5; also A7.

## Why

**Corrected 2026-08-24.** An earlier version of this task claimed `(execId, nodeId)` names "a node
within a run" and that loops break it in general. That is only half true, and the real situation is
more interesting: **`execId` means two different things depending on which path ran the node.**

- **Temporal path** — `processNodeViaTemporal` does `const execId = uuid()` **per node dispatch**
  (`flux.service.ts:681`). Each execution, including each loop iteration, gets its own id. Here the
  pair is already unique.
- **Legacy path** — `recordLegacyNodeStart` is called with `execId: runLogProcessId`
  (`flux.service.ts:3304`), which is **the same value for every node in the run**. Here the pair
  collides on every loop iteration, exactly as originally described.

So the defect is not "loops break the key". It is that **one column carries two incompatible
meanings**, and this epic is about to merge the two paths into one. Whichever meaning survives has
to be chosen deliberately, because the merge will otherwise pick one by accident.

The mechanical hazards below are real on the legacy path today, and become general the moment the
paths converge (analysis §8.4):

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

**Recommendation: keep the Temporal meaning — one id per node execution — and make the legacy path
conform.** It is already the stricter of the two, it is what `node_executions` was documented to
be ("one row per node run"), and it is the only one of the two that survives loops and parallelism
without a discriminator.

**Sub-flows do not share the parent's execution identity.** A sub-flow is a different graph with
its own scheduler state; merging it into the parent's would mean one state holding two node sets
and two termination conditions. It gets its own run identity, **chained to the parent** — see
`TASK-S1`, which owns that chain.

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
