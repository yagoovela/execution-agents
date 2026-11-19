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

## Scope added: the schedule's inputs (2026-11-18)

`resolveScheduledRunActivity` loads the schedule's `variableInputs` but never applies them:
`persistRunSeedActivity` seeds the run from the flow's saved values. The `apiV2` job applied
them through `body.variableInputs`. Decided 2026-11-18: E4b fixes it too, because the flag cannot
go on without it. The back now seeds the run, the way it seeds a batch row.

## Implementation (2026-11-18)

Branches `feat/868muzf1f` (back `6e47a7be`..`24c3e7d3`, worker `996c502`..`c810fea`), not merged.

- Back `POST /worker/scheduled-run` seeds the run from the schedule's `variableInputs` through
  `prepareWorkflowSeed` (renamed from `prepareWorkflowSeedForBatchRow`, shared with batch rows).
  It refuses a deleted schedule.
- Back `POST /worker/scheduled-run-outputs` closes the run through `closeWorkerRun` with run type
  `cronjob` and email on (the `apiV2` default the schedule job used). Each delivery starts under
  the invocation id `scheduled-run`, so a retried finish delivers once. It finishes a run whose
  schedule was deleted while it ran.
- The `chat_logs` body is an explicit field list: `webhook`, `spaceId` (`null` outside a space),
  `inputText`, and the `variableInputs` stored in the run seed. The schedule row and its owner are
  never copied. The legacy schedule job gets the same list in a separate fix (1gahkf3bfgw, back
  #2120); after it merges, E4b imports its `scheduledRunBody`.
- Batch and scheduled finishes share `loadWorkerRunContext` and `startDeliveries`.
- Worker: behind `patched("e4b-scheduled-run-finish")`, `runScheduledFlow` calls
  `prepareScheduledRunActivity` in place of `persistRunSeedActivity`, runs `processFlow`, then
  `finishScheduledRunActivity` with the status and node failure `processFlow` returned. When
  `processFlow` itself fails, the run is finished as an error and the scheduled run still fails
  with the `processFlow` error, also when that finish fails. Both activities reuse the batch row
  retry policies; a 400 or 404 from the back is non-retryable.

Verification, each test seen failing first:

- Back, against the `apiV2` loop for a scheduled run: the same delivery plan with email and
  callback, one delivery on a retried finish, no delivery when a producer fails, the schedule
  inputs in the seed, the same `flows_logs`, `chat_logs`, chat memory and space run log, no owner
  field in the `chat_logs` body, `spaceId` `null` outside a space. Negative controls: email off,
  a random delivery id, inputs dropped, prepare reading deleted schedules, the body spreading the
  schedule, run type `api`, an undefined space id.
- Worker: workflow tests for success, a node failure, a failed child and a failed finish after a
  failed child; activity tests for the routes, a 5000-character provider reply, non-retryable 400
  and 404, retryable 500, and only the seed id or node error kept in the history.
- Replay: three histories (`origin/main` `8c80840` without the finish, with the finish, with a
  failed child) replay on the branch; without the guard, or with the old path forced, the replay
  fails with a `DeterminismViolationError`.

## Rollout order

`temporal_schedules` goes on in production only after both of these run there:

1. The registrar's cron fix (back #2118, merged to `main` 2026-11-18, not deployed): the front
   saves a 6-field cron with seconds first, which Temporal read as minute to year.
2. E4b, back first, then the worker.

Then turn the flag on and run `POST /schedule/admin/reconcile-temporal`. Production has no
schedule in Temporal while the flag is off, so the reconcile registers every schedule with the
fixed cron. On dev the flag has been on since 2026-11-04, and `reconcile()` keeps ids already in
Temporal, so a schedule registered before #2118 keeps its old cron: test E4b on dev with a new
schedule.

## Known limits

- A retried prepare writes a second seed and a second set of `varInputNode` node executions for
  the same run, as a retried batch row prepare does. B7b (868muzee4) makes `prepareWorkflowSeed`
  write once, which covers both.
- A schedule input that names a node no longer in the flow fails the prepare, as it failed the
  `apiV2` job. The run then has no log.
- `processFlow` runs with `ParentClosePolicy.ABANDON`. If the scheduled run itself is cancelled,
  the child keeps running and nothing finishes it in the back.
- A prepare that fails (schedule deleted between the resolve and the prepare, a stale input node)
  records no missed fire. The `apiV2` job left nothing for these cases either.
- A route-level 404 from the back is non-retryable, as for batch rows. The rollout order (back
  before worker) keeps the worker from calling a route that is not deployed.

## Reviews (2026-11-18)

- `/simplify`: applied 8. The patched resolve asks for `withGraph: false`, so the flow graph stays
  out of the workflow history (a large flow could pass the payload limit); `patched()` moved
  before the resolve and the two `with-*` replay histories were recorded again. The finish DTO
  picks the batch fields, the reply reuses the batch types, the run type is
  `FlowLogRunType.CRONJOB`, the test harnesses are shared, and the finish block is flatter.
  Skipped: the second schedule read in the finish (one primary-key read per run), a
  `finishWorkerRun` wrapper and shared replay or child-failure helpers (they touch `processBatch`
  and other specs), neutral renames.
- `/code-review` (high): fixed 2, each test seen failing first. A `processFlow` child cancelled on
  its own (workflow `run-<runId>`) is finished as `cancelled`; a stop cannot reach a `cronjob` run
  today, since only `canvas` and `api` runs are cancellable. The finish loads the flow
  `withDeleted`, so a flow deleted during the run (scheduled or batch row) still logs and
  delivers. Recorded as limits above: duplicate node executions on a retried prepare, no missed
  fire on a failed prepare, route-level 404. Declined: finishing inside `processFlow` (changes the
  shared workflow), the duplicate `scheduledRunBody` until #2120 merges, typing of the graph-free
  resolve output, batch-named contract.
- `/security-review`: no finding. The routes sit behind `InternalApiGuard`; the back takes the
  user and flow from the stored schedule, not the request; the `chat_logs` body and the schedule
  read carry no owner field; the new worker query is parameterized.

## Dev validation (2026-11-18)

On dev, `develop` carries only the E4b commits, cherry-picked onto it: back `be554332`, worker
`5a28680`. Both ECS rollouts completed before the test.

A new schedule on `a13-dev-qa-G` ran every 3 minutes with the variable input
`e4b schedule input`. The Data Output had email off and a callback to a missing path on the dev
API, so each delivery writes one `Delivery failed` row and nothing leaves dev. Three fires
(17:06, 17:09 and 17:12 UTC) each wrote:

- One `Successfully ran` row and exactly one `Delivery failed` row in `flows_logs`, both
  `cronjob`.
- One `space_run_logs` row (`cronjob`, `success`) while the flow sat in a space folder; none
  while its folder had no space, as in the `apiV2` path.
- One `chat_logs` row whose body holds the schedule's variable inputs, the space id and only the
  user id.

The output node received `e4b schedule input`, not the node's saved `alpha row`. After the
schedule was deleted, no run followed. The schedule is deleted and the flow is back in its folder.

The test also found that the Logs page listed the variable input row of each run as a separate
one-node run. The page groups node rows by `COALESCE(metadata->>'runId', execId)`, and
`seedVarInputNodeExecutions` wrote that row without `metadata`. A13 batch runs on dev show the same
split since 2026-11-10.

## Logs page split fix (2026-11-18)

Fixed in E4b at the user's request (back `f91b7881`). `prepareWorkflowSeed` takes the run type
(`cronjob` for a schedule, `batch` for a batch row), and the seed writes
`{ runKind: 'agent', runType, runId }`, the shape the other node writers use.
`workflow-seed-run-key.integration.spec.ts` lists a `cronjob` and a `batch` run through
`findFlowRunsFiltered` on real Postgres and expects one run with both nodes. With the seed
writing empty metadata, it lists two one-node runs, as seen on dev.

On dev (back `496373d4`), a new schedule on the same flow fired at 18:24 and 18:27 UTC. The Logs
listing showed one `scheduled` run per fire with three nodes (variable input, math, output), where
it showed two entries per fire before. Each fire still wrote one success row and exactly one
delivery. The schedule is deleted.

PRs to `main`: back #2122, worker #176.
