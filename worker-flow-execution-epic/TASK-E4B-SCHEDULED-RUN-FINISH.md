# E4b — Scheduled runs on Temporal Schedules finish through the back

**Goal:** with `temporal_schedules` on, a scheduled run delivers and logs exactly as it did through
the `apiV2` job.

**Depends on:** E4 and A13 (868mn64j4). **Blocks:** turning `temporal_schedules` on in production.
**Added 2026-11-10** from A13. ClickUp: [868muzf1f](https://app.clickup.com/t/868muzf1f).

## Why

`runScheduledFlow` (E4, worker `a1faf32`, 2026-11-03) starts the flow straight as a `processFlow`
child. The run never reaches the back's end of run, so the Data Output's email and callbacks are not
sent and the run logs are not written. Before E4 a scheduled run went through the `apiV2` job and did
all of that. Batch rows had the same gap; A13 closed it with `POST /worker/batch-row-outputs` and
`FluxService.settleRunOutputs`. `temporal_schedules` is off in production (read on 2026-11-10), so
nobody is affected today.

## Scope

**In.** After the `processFlow` child returns, `runScheduledFlow` calls a finish activity that asks
the back to settle the run through `settleRunOutputs`, with the schedule's email setting and run type,
the way A13's batch finish does. Delivery uses one workflow id per run, so a retried finish delivers
once. The run logs are written through the helpers A13 shared. The new step sits behind a `patched()`
marker, with replay histories for both shapes.

**Out.** Pause, backfill and last-run state (E4's remaining scope).

## Verification

- Negative control: a scheduled run of a flow with a Data Output sends nothing on the current code
  and delivers once after the change.
- Parity with a scheduled run through the `apiV2` job: same deliveries and same log records.
- Finish retried after the delivery started: one delivery.

## Done when

A scheduled run on Temporal Schedules delivers, replies and logs like one through the `apiV2` job,
once per run, and the flag can be turned on in production.

## Files

worker `run-scheduled-flow.workflow.ts`, the batch finish activity A13 added · back
`settleRunOutputs`, `finishBatchRowRun` (to generalise to a worker-started run) and the worker
controller
