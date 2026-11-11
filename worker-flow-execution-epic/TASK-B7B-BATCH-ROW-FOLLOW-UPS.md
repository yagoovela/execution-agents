# B7b — Batch rows keep chat memory, a retried prepare writes once, and workflow runs keep their log steps

**Goal:** a batch row run through `processFlow` computes and records the same thing as the same row
run through the API loop, and a retried step writes once.

**Depends on:** A13 (868mn64j4), which added the batch-row finish step and the shared end of run.
**Blocks:** nothing. **Added 2026-11-10** from the A13 batch work. ClickUp:
[868muzee4](https://app.clickup.com/t/868muzee4).

## Why

A13 restored the batch rows' Data Output value, callback and run logs. On the way it found three
gaps it did not cause, on the paths B7 and B4 opened:

1. **Chat memory.** `prepareWorkflowSeedForBatchRow` skips the `fluxObject` preparation `apiV2`
   does before a run: clear-on-execution and loading the stored chat history. A chat-memory node in a
   batch row runs without its history, so its answer can differ from the same row run through the
   API. This changes results, not only logs.
2. **Retried `prepare`.** `seedVarInputNodeExecutions` inserts new `node_executions` rows on every
   call, so a retried prepare leaves duplicate Variable Input rows for one run.
3. **Log steps on API workflow runs.** With `RUN_LOG_FROM_EVENTS` off or in shadow mode, the end of
   `apiV2` overwrites the space run log built from events with a collector doc that has no node
   entries, so the Logs page shows the run without its steps.

## Scope

**In.** Batch-row preparation calls the same `fluxObject` preparation `apiV2` calls; it does not
restate it. A retried prepare is idempotent for the Variable Input rows. An API workflow run keeps
its node entries in every run-log mode.

**Out.** The live Logs-page entry for a running batch row (A13 writes the logs when the row
finishes); the budget and spend stops, which `processFlow` does not have yet.

## Verification

- Negative control per item, seen failing on the current code: a chat-memory node in a batch row
  answers without history; `prepare` called twice leaves two Variable Input rows; an API workflow
  run in `off` mode shows `nodes: []` on the Logs page.
- Parity: the same row through the API loop and through the batch gives the same answer and the same
  memory entries.

## Done when

A chat-memory node answers the same in a batch row as through the API, a retried prepare writes
once, and an API workflow run shows its steps whatever the run-log flag says.

## Files

`back/src/app-api/flux/batch-run-preparation.service.ts` (`prepareWorkflowSeedForBatchRow`,
`seedVarInputNodeExecutions`) · `back/src/app-api/flux/flux.service.ts` (the `fluxObject`
preparation in `apiV2`, the end-of-run log write) · `back/src/app-api/space_run_logs/run-events.service.ts`
