# B7 — Batch processing as a durable workflow

**Goal:** a CSV batch survives a deploy, and stops being a detached loop inside an API process.

**Depends on:** B4 (there must be a flow workflow for a batch to invoke) and **S3** (a batch is the
largest multiplier of a missing cost ceiling). **Source:** review §11.2.

## Why

`/flux/batch-process` calls `this.processBatch(...).catch(...)` (`flux.controller.ts`) —
unawaited. The request returns immediately and the work continues **detached inside the backend
process**.

`processBatch` is a sequential `for` loop over CSV rows. Per row it re-reads the batch,
re-reads the row record, runs a **complete flow** via `await this.fluxService.apiV2(…)`, writes the
output, re-reads the batch and saves the pointer — four to five database round trips on bookkeeping
before the run itself.

Three consequences, each of which a workflow fixes for free:

- **No durability.** A deploy, restart or scale-down mid-batch kills the loop silently; the batch
  stalls at `lastProcessedLine` with a non-terminal status and nothing resumes it.
- **No parallelism**, and no safe way to add it while it is a loop in a request handler.
- **It multiplies every missing ceiling.** A thousand-row CSV is a thousand full runs from one
  API-key call, against no rate limit, no per-run cost ceiling and no per-tenant cap.

## Scope

**In.** A batch workflow: one child workflow per row, a concurrency cap, and the row pointer as
workflow state rather than a re-read column. `continueAsNew` at a row boundary — a large CSV is
exactly the case that exhausts workflow history (review §4.1).

**In.** Keep `lastProcessedLine` and the batch status columns updated. They are the customer-facing
progress surface and the existing status/download endpoints read them; the workflow becomes their
writer.

**In.** Resumption. Today a stalled batch needs someone to notice. With a workflow the stall becomes
either an automatic continuation or a visible failed workflow — decide which, and make sure the
existing `/batch-process/:id/status` reflects it honestly.

**In.** The per-row bookkeeping collapses. Re-reading the batch row on every iteration exists
because the loop cannot trust its own memory across a restart; a workflow can.

**In.** Honour the stop endpoint (`/batch-process/:id/stop`) through workflow cancellation, which
also cancels in-flight rows — better than today, where stopping sets a flag the loop checks.

**Out — a batch screen** (`front`). The screen does not exist today and is **not built in this
migration/refactor** (decided 2026-09-02). When it is built it reads what already exists — rows done,
rows failed, the current row, per-row output, the stop endpoint. The route stays regardless (`D18`):
the five endpoints are the batch's only surface, and this task makes what runs behind them durable.

**In — an optional stop-on-failure policy, set by the customer per batch.** Either an absolute
count or a share of rows processed — *stop after 1000 failures*, or *stop at 60% failed*. Unset
means run the whole CSV. Two things have to be decided with it and stated in the PR: what counts as
a failure (a failed row, or a failed node inside an otherwise successful row), and what happens to
rows already in flight when the threshold trips — cancelled with the batch, or allowed to finish.
The share form cannot be evaluated on the first rows without a minimum sample, or a batch whose
first two rows fail stops at 100%.

**Interaction with `D21`.** Every row is a child workflow of a parent that has already started. If a priority list is ever introduced, `D21` would put all of a large batch's rows ahead of newly admitted runs, and one thousand-row CSV could hold the front of the queue. No such ordering exists today — work starts as capacity frees up — so this is a risk to re-read when `D21`'s condition is met, not a constraint on this task now.

**Interaction with `S1`.** A row is a sub-flow, so it starts at depth 1 and any flow it calls goes
deeper. A batch of a flow that itself composes two levels reaches the `S1` ceiling — confirm the
ceiling is measured against batch rows, not only against hand-built flows.

**Out.** Changing the CSV format, the input mapping to `varInputNode`s, or the output shape.

## Verification

- **Negative control (required).** Start a batch, restart the backend mid-run, and confirm the
  batch stalls on `main` — that is today's behaviour and it should be seen once. Then confirm the
  workflow version resumes and completes.
- **Cost ceiling interaction.** Run a batch whose total would exceed the tenant's budget and confirm
  S3 stops it at the ceiling, with the partially-completed rows recorded rather than lost.
- **Negative control, stop-on-failure.** Build a CSV whose rows fail deterministically past a
  known point, run it with the policy unset, and confirm the batch processes every row and fails
  every one. Then set the threshold and confirm it stops at the row it should, with the reason
  recorded and the completed rows kept. A threshold that has never been seen not to trigger is not
  a threshold.
- Stop mid-batch and confirm in-flight rows cancel and the status is terminal.
- Compare outputs row for row against a pre-change run of the same CSV.
- Measure the bookkeeping reduction — queries per row, before and after. The claim in this task is
  four to five round trips; prove it or correct it.

## Done when

A batch survives a backend restart and resumes; the workflow is the sole writer of
`lastProcessedLine` and the status columns, and they reach a terminal state; stop cancels the rows
in flight and the status says so; the stop-on-failure policy trips at the row it should — and
demonstrably does not trip when unset or before its minimum sample; a batch that would exceed the
tenant's ceiling is stopped by S3 with the completed rows kept; outputs match a pre-change run row
for row; and the bookkeeping reduction is measured, not asserted. The batch screen is not part of
this task's done.

## Files

`back/src/app-api/flux/flux.controller.ts` (the `/batch-process` handler, `processBatch()`, and the four status/listing/stop/download handlers) ·
`back/src/entities/batch_processing_file*.ts` · new batch workflow in the worker
