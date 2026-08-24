# B7 — Batch processing as a durable workflow

**Goal:** a CSV batch survives a deploy, and stops being a detached loop inside an API process.

**Depends on:** B4 (there must be a flow workflow for a batch to invoke) and **S3** (a batch is the
largest multiplier of a missing cost ceiling). **Source:** review §11.2.

## Why

`/flux/batch-process` calls `this.processBatch(...).catch(...)` (`flux.controller.ts:560`) —
unawaited. The request returns immediately and the work continues **detached inside the backend
process**.

`processBatch` (`:574–706`) is a sequential `for` loop over CSV rows. Per row it re-reads the batch,
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

**Out.** Changing the CSV format, the input mapping to `varInputNode`s, or the output shape.

## Verification

- **Negative control (required).** Start a batch, restart the backend mid-run, and confirm the
  batch stalls on `main` — that is today's behaviour and it should be seen once. Then confirm the
  workflow version resumes and completes.
- **Cost ceiling interaction.** Run a batch whose total would exceed the tenant's budget and confirm
  S3 stops it at the ceiling, with the partially-completed rows recorded rather than lost.
- Stop mid-batch and confirm in-flight rows cancel and the status is terminal.
- Compare outputs row for row against a pre-change run of the same CSV.
- Measure the bookkeeping reduction — queries per row, before and after. The claim in this task is
  four to five round trips; prove it or correct it.

## Files

`back/src/app-api/flux/flux.controller.ts:513–517, 560, 574–706, 710–800` ·
`back/src/entities/batch_processing_file*.ts` · new batch workflow in the worker
