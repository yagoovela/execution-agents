# A9b — A stalled async API run reaches one outcome and delivers once

**Goal:** when Bull marks a running async `apiV2` job as stalled, the run ends with exactly one
outcome: one execution status, one MCP run status and one delivery (callback, email).

**Depends on:** A9 (delivery as a workflow) and the 2026-11-04 fix that stopped Bull from
redelivering a stalled job (back PR #2086). **Blocks:** nothing. It matters most once the back runs
on more than one task, because another replica can then detect the stall while the job is still
running.
**Added 2026-11-11** from A13. ClickUp: [868mvdm50](https://app.clickup.com/t/868mvdm50).

## Why

Since back PR #2086 the async queue never redelivers a stalled job (`attempts: 1`,
`APIV2_QUEUE_SETTINGS = { maxStalledCount: 0 }`). Instead, `onFailed` calls `failStalledRun`
(`src/jobs/apiV2Job/apiV2Job.processor.ts`), which marks the run failed and delivers the error
callback. Bull marks a job stalled when its lock is not renewed in time (default 30 s), which also
happens when the process is alive but its event loop is blocked. The 2026-11-04 incident that led to
PR #2086 was such a freeze.

If the frozen job then resumes, the same run reaches its normal end:

1. `markCompleted` overwrites the `markError` that `failStalledRun` wrote, so polling flips from
   `error` to `completed`.
2. `deliverOutputs` starts a second delivery. The first one sent the failure with the stalled
   message; the second one sends the real outputs. Each uses a random delivery workflow id, so
   `REJECT_DUPLICATE` does not stop either.

The customer receives a failure callback followed by a success callback for the same run, and the
MCP run status and the execution status end on whichever write came last.

A13 found this while checking "one delivery per run" (2026-11-11). A fixed delivery id alone is the
wrong fix: it keeps whichever delivery starts first, usually the failure, and withholds the real
outputs. Production since 2026-11-04 (prod CloudWatch, read 2026-11-11): 14 stalled runs, 13 in one burst
on 2026-11-04 and 1 on 2026-11-10. Whether the live job finished afterwards is not yet measured.

## Scope

**In.**

- One terminal transition per run. The processor's normal end and `failStalledRun` both claim the
  run's end through a single compare-and-set on the run's status (for example
  `in_progress → completed` or `in_progress → error` in `flow_execution_status`, or a claim row keyed
  by the job id). Only the winner writes the final statuses and starts the delivery.
- Decide, with the product owner, which outcome wins when the live run finishes after the stall was
  reported. The options are: the first claim wins and the live run's result is discarded (and
  logged), or the stall report is held for a short grace period before it claims the end.
- Every await after a side effect gets a test where it throws, per the workspace rule.

**Out.** Bull lock settings (`lockDuration`, `stalledInterval`); the event-loop freezes themselves.
The sync API path, which has no queue.

## Verification

- Negative control: on the current code, a test that runs `failStalledRun` and then lets the live
  job finish shows two deliveries and the status flipping from `error` to `completed`. After the
  change it shows one delivery and one status.
- The reverse order (live end first, then the stall report) also gives one outcome.
- Measure first, per the workspace rule: count stalled runs in production since 2026-11-04 and, for
  each, whether the live run later finished. Classify every refused second outcome as correctly
  refused or refused although it works.

## Done when

A stalled async run produces one status and one delivery, whichever of the two ends comes first.

## Files

back `src/jobs/apiV2Job/apiV2Job.processor.ts` (`process`, `failStalledRun`, `reportRunFailure`,
`deliverOutputs`), `flow_execution_status` service, `McpRunStatusService`,
`output-delivery.service.ts`
