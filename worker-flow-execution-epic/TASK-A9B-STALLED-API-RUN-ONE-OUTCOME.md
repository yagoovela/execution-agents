# A9b — An async API run survives a back deploy, or ends with one outcome

**Goal:** a back deploy no longer kills async `apiV2` runs that are in flight. When a run does lose
its process, it ends with exactly one outcome: one status, one delivery, and a recorded cost that
matches what was charged. On the B4 path the run continues in the worker, and any live back finishes
it when its handler is gone. No run stays unfinished, or keeps processing, past the run ceiling
plus 30 min.

**Depends on:** A9 (delivery as a workflow), A13 (the worker-side batch finish,
`POST /worker/batch-row-outputs`, which part 4's reduced end follows), B4 (the `processFlow` path) and back PR #2086
(no redelivery of a stalled job). **Blocks:** turning `engine_in_workflow` (the B4 flag) on in
production: on that path today a deploy charges the whole run and still reports `error` (see
**Why**, point 5). **Added 2026-11-11** from A13; **re-scoped 2026-11-12** after the production
measurement below; **reviewed 2026-11-13** (EGM implementation readiness, rounds 1 to 4, decisions D3, D6, D9 and
D11–D18).
ClickUp: [868mvdm50](https://app.clickup.com/t/868mvdm50).

## Why

Read on 2026-11-12 against back `main` `ba55e32` and worker `main` `834cb32`, and against
production CloudWatch and ECS (read-only).

### What production shows

Fifteen async runs were reported stalled since 2026-11-04 (`apiV2 run abandoned after its process
died`): 13 on 2026-11-04, 1 on 2026-11-10 and 1 on 2026-11-12. All three dates are back production
deploys. In each case:

1. The run had started on the old ECS task, which kept taking Bull jobs while it drained. The
   target group's deregistration delay is 300 s, and nothing tells the process that it is draining.
2. The old task's log stops with no shutdown line. ECS then stops it: the container has no
   `stopTimeout` (default 30 s), back registers no shutdown hook, and PID 1 is `/bin/sh -c ". ./dev.sh"`,
   which starts `node` in the background and does not forward SIGTERM. `node` is killed with the run
   in flight. The SIGTERM path is inferred from the code and the image; it was not tested.
3. The new task, the only one live at that moment, found the stall within 30–90 s and ran
   `failStalledRun`.

No run shows a live end after its stall (no `[SpaceRunLog persisted]` line, no later loop line).
The "frozen process resumes and finishes" case this task was written for occurred **0 times in 15**.
It stays reachable: a lost Bull lock (an event loop blocked for 30 s, or a Redis blip) fails the job
while the handler keeps running, and the stall check runs on any replica.

In 4 of the 15 runs, a node that the worker was still running finished and was charged after the
stall, for about 7,000 credits in total, while the run ended as `error` with no outputs.

### What the code does

1. **The execution status already has a compare-and-set.** `markCompleted` and `markError` go
   through `finishFlowExecution` (`flow-execution-status.service.ts`), which updates only while the
   status is `pending` or `in_progress`. A live end after a stall cannot turn `error` into
   `completed`. But both return `void`, so the caller never learns that it lost.
2. **The MCP run status has no guard.** `McpRunStatusService.markFinished` and `markCancelled`
   update by id only, so the last writer wins.
3. **Delivery is not gated.** The delivery workflow id carries a random invocation id, so
   `REJECT_DUPLICATE` never matches. A stalled API run delivers a consolidated callback with
   `success: false`; a live end would deliver the real one. Both carry the same
   `X-FluxPrompt-Delivery-Id` (`<executionId>:consolidated`), so a receiver that deduplicates on the
   header keeps the error and drops the real result.
4. **Cost.** `failStalledRun` writes `NO_SPEND`, so the status and the MCP row show 0 while the
   ledger holds the charges of every node that ran, including those charged after the stall. Charges
   happen per node in the worker; no end-of-run charge exists to skip.
5. **The B4 path has no finisher after a stall.** The Bull handler starts `run-<execId>` and awaits
   its result. When the back task dies, `processFlow` keeps running in the worker and charges every
   remaining node, but nothing writes the end: `finishExecution` skips a row whose `runWorkflowId` is
   set, and `processFlow` emits `run_finished` without delivering. The stall report then marks the run
   `error`.
6. **Which runs are affected.** Only async API runs have a `flow_execution_status` row and a callback
   URL; MCP runs have a `mcp_run_status` row keyed by the run's process id. A stalled schedule,
   inbound email, Zapier or child run delivers nothing (its stall plan is empty), so it already has
   one outcome. The run's process id (`parentProcessId ?? job.data.jobId`) is the same in the live end
   and in `failStalledRun`, and is fixed before the run starts.
7. `failStalledRun` also releases the tenant's concurrency slot while the run may still be alive.
8. **Nothing stops a run at its ceiling, and nothing closes a forgotten one.** `RUN_MAX_DURATION_MS`
   (6 h by default, not set in production) only sets the TTL of the chain keys
   (`chain-ceiling.registry.ts`, `chain-root.registry.ts`) and when the tenant ledger drops a slot;
   the chain ceiling stops runs on credits, not on time. The B4 run workflow starts with no timeout.
   No sweep closes a `flow_execution_status` or `mcp_run_status` row left unfinished. The `api-v2` Bull
   job times out at 600 s (`AGENT_JOB_TIMEOUT_MS`, not set in production): Bull then marks a longer run
   failed and frees its worker slot while the handler keeps running.

## Decisions (2026-11-12 and 2026-11-13, with the user)

| # | Question | Decided | Why |
|---|---|---|---|
| A9b-D1 | Scope | Re-scoped: deploy-killed runs first, plus the one-outcome guard | The measured cause is the deploy (15 of 15); the double outcome was seen 0 times but is cheap to close |
| A9b-D2 | How a deploy stops killing runs | Graceful shutdown now; the B4 path, finished through any back, is the durable fix | Runs last up to 6 h, so no stop window can drain them; only a run that lives outside the back process survives |
| A9b-D3 | Which outcome wins when both arrive | The first claim wins. A loser writes no status and delivers nothing of its own: it only starts the winner's stored plan (revised in round 2) | No second callback; the customer never gets an error and then a success under one delivery id; a winner that dies before its delivery starts is still delivered |
| A9b-D4 | Cost of a legacy run killed by a deploy | Interrupt the run's steps still in flight, and record the real cost; no refund | No refund mechanism exists (a charge writes seven ledgers); an interrupt stops new charges, a node in progress still charges partial tokens (E2 D22) |
| A9b-D5 | Resume a killed legacy run from where it stopped | No | The legacy loop keeps its scheduler state and node outputs in memory and has no resume entry. Handing a partial run to `processFlow` (`carryState`) is feasible but costs 3–5 days for a path Wave 6 deletes, reruns the nodes in flight (new `execId`, charged again), restarts arrays, and works only for flows B4 accepts |
| A9b-D6 | Who writes the end of a B4 run | The live handler, as today. At its end the run workflow calls a finish activity; back writes a reduced end only when no live handler holds the Bull job (revised in round 2) | The full end uses state that exists only in the handler (chat log, schema change, the result for sync waiters); a run whose handler died is still finished by any live back, with no back waiting for it |
| A9b-D7 | How SIGTERM reaches `node` | `exec node` at the end of `dev.sh`, the database seed script started with `setsid`, and `initProcessEnabled` in the task definition | `node` gets the signal with no shell in between and the init process reaps orphans; unlike a command in the task definition, it keeps the database seed script and the variable check, stays in the image for every environment, and the local test (`docker run --init`) runs what production runs |
| A9b-D8 | Deregistration delay | 180 s, down from 300 s | Measured 2026-11-12 over 15 days: the daily p99.99 of `TargetResponseTime` was 96–155 s and the daily maximum 98–175 s, except two days at the 300 s server timeout; 60 s would cut long requests every day |
| A9b-D9 | Runs left unfinished or running too long | A cron closes any run past `max(run ceiling + 30 min, flag value)` and stops its processing, behind the `unfinished_run_reaper` flag; it also starts a stored plan that no one started; it skips a run while Temporal cannot be reached; the `api-v2` Bull timeout becomes the ceiling plus 1 h | No run may stay `in_progress` forever; closing a run during a Temporal outage could fail a live B4 run; cancelling at Bull's 600 s would kill every legitimate run longer than 10 min |
| A9b-D10 | A retried run end | Keep A9's guarantees (email dedup keys, `X-FluxPrompt-Delivery-Id`) and give the run's end delivery the run id as its invocation id | Under 1 h of work; a receiver that ignores the header still gets one callback |
| A9b-D11 | Child-run charges in a legacy stall | Library and flow-caller child runs keep their own run id and add it to a Redis set of their parent (`flux:run-children:<parentRunId>`); the recompute reads the set (revised in round 2; it was "children inherit the parent's id") | Sharing the parent's id made the child open a root run log, take the parent's recompute job id and clear the parent's cancel cache |
| A9b-D12 | The claim's delivery | The claim stores the run's delivery plan (`end_delivery`); it is cleared once its delivery has started | Any later writer, and the cron, can start a delivery that the winner never started |
| A9b-D13 | Inline child runs on the B4 path | Library and flow-caller children run on the legacy loop until B6 | An eligible child with the parent's id would start `run-<parentRunId>` while the parent's workflow runs; no effect in production while `engine_in_workflow` is off |
| A9b-D14 | When to recompute a legacy stall's cost | Two passes, 5 min and 35 min, scheduled before the claim, with the exec ids read when each pass runs | A node activity that ignores the interrupt runs up to 30 min (`textGeneratorActivity`); scheduling first survives a throw after the claim |
| A9b-D15 | Who writes a cancel request | No one at a stall; the cron writes the chain cancel for a live legacy run past its limit (round 3) | A cancel on the root run id also stops the run's `triggerOnly` children; at a stall the handler is dead (15 of 15); past the limit the whole chain stops, as the chain spend ceiling already does |
| A9b-D16 | A plain `Error` in `processFlow` code | Every `processFlow` run fails with a non-retryable `ApplicationFailure`, batch rows included (round 3) | Today Temporal retries the workflow task forever, so the `finally` never runs; workflows stuck that way fail once the new worker ships |
| A9b-D17 | Unfinished rows older than 7 days when the cron runs | Closed with status, error and cost only: no callback, no email; at most 100 rows per select per tick, oldest first (round 4) | A callback months after the request confuses the customer; a capped tick cannot flood Temporal or a receiver |
| A9b-D18 | The error text the cron writes | `RUN_CEILING_MESSAGE`, `RUN_NOT_STARTED_MESSAGE`, `RUN_OWNER_MISSING_MESSAGE`, in the tone of `STALLED_RUN_MESSAGE`; a B4 run past its limit gets the ceiling text, not "Run cancelled" (round 4) | The text reaches the status endpoint, the MCP status and the callback; a legacy and a B4 run past the same limit read the same |

## Scope

**In.** Build the parts in this order: part 1, which depends on nothing and addresses the measured
cause (15 of 15 stalled runs died in a deploy); then part 2; then parts 3 and 4, which use its claim
(part 3's `closed` branch uses part 4's reduced end, so it lands with part 4); then part 5, which uses
parts 2 to 4. Deploy order, the AWS changes and the flag: see **Rollout** at the end of Scope.

**Terms.**

- *Run id*: `params.parentProcessId ?? job.data.jobId` in `ApiV2QueueProcessor`. It is the
  `flow_execution_status.id` of an async API run, the `mcp_run_status.id` of an MCP run, the suffix of
  the run workflow id `run-<runId>` and, after part 4, the Bull job id of async API runs and MCP runs.
- *Async run*: an async API run or an MCP run. Only these have a *claim row* (`flow_execution_status`
  or `mcp_run_status`).
- *B4 run*: a run that executes as the run workflow `run-<runId>` (`processFlow`), on the *B4 path*.
  *Legacy run*: a run that executes in back's in-process loop (the *legacy loop*). *B4 handler*: the
  `api-v2` job handler of a B4 run, which waits on `handle.result()`.
- *B4 job*: an `api-v2` Bull job whose run started `run-<runId>`.
- *Run ceiling*: `resolveRunMaxDurationMs()`, 6 h unless `RUN_MAX_DURATION_MS` is set (not set in
  production on 2026-11-12).
- *Writer*: any code path that writes a run's end: the live handler (the *live end*), `failStalledRun`,
  the reduced end (part 4) or the cron (part 5).
- *Claim*: defined in part 2. *Stored plan*: the run's full delivery plan kept in `end_delivery` until
  its delivery has started.
- *Fixed delivery workflow id*: the delivery workflow id built with the run id as invocation id (part
  2). It is not the `X-FluxPrompt-Delivery-Id` header.
- *Chain cancel*: a cancel request on the root run id (`RunCancellationService.requestCancel`); it stops
  the run and every child run that watches the root's cancel key, `triggerOnly` children included.
- *Run seed*: what `RunSeedService.persist` stores for a B4 run (a `run_seeds` row). *Database seed script*:
  `node dist/seed.js`, which `dev.sh` runs in the background once `/health` answers. *Seed migration*:
  the migration that adds the `unfinished_run_reaper` flag.
- *Tenant slot*: the run's entry in the tenant concurrency ledger. *Bull worker slot*: one of the
  `api-v2` processor's concurrent jobs.

1. **Graceful shutdown (back and the task definition).**
   - The container's PID 1 delivers SIGTERM straight to `node` (A9b-D7). `dev.sh` runs under `dash`
     (`/bin/sh -c`, `Dockerfile`). It starts the database seed script with
     `( setsid sh -c '<wait for /health while kill -0 "$1" succeeds, then node dist/seed.js>' seed "$$" & )`:
     the outer subshell exits at once, so the seed shell is reparented to the init process, which reaps
     it; `"$$"` passes the shell's process id, which `node` keeps after `exec`, so the existing abort
     when the main process exits still works. `dev.sh` ends with
     `exec node --max-old-space-size=… dist/main.js`. The task definition sets
     `containerDefinitions[].linuxParameters.initProcessEnabled: true`: its init process becomes PID 1,
     forwards SIGTERM to `node`, its direct child, and reaps orphaned child processes. The `Dockerfile`
     does not change. The memory flag stays in `dev.sh`.
   - `src/main.ts` calls `exitAfterClose(app, ['SIGTERM', 'SIGINT'])` (`src/common/exit-after-close.ts`).
     On the first signal it calls `app.close()`, so Nest runs every `onModuleDestroy`, then every
     `beforeApplicationShutdown`, then every `onApplicationShutdown`; then it exits with 0, or with 1
     when the close fails. A repeated signal while the app closes is ignored. It replaces
     `enableShutdownHooks`, which sends the signal to its own process again after the close: when
     `node` is PID 1, the kernel ignores that signal, and the process stays up until `stopTimeout`.
   - Two hooks that run today in `onModuleDestroy` would break runs still in flight, so one is removed
     and one moves to a later phase:
     - `TemporalService` stops closing its connection on shutdown; the process exit closes the socket.
       A close at any point before exit rejects every B4 handler's `handle.result()`, and that handler
       then claims `error`.
     - `SpaceRunLogsService` clears its pending flush timers in `onApplicationShutdown`, so debounced
       run-log writes keep firing during the wait. A run's final write goes through `flushNow` either
       way.
   - A new `BullShutdownService` (`src/jobs/bull-shutdown.service.ts`) pauses, in `onModuleDestroy`,
     every instance of each consumed queue name. `@nestjs/bull` binds each `@Process` to the first
     instance that `moduleRef.get(getQueueToken(name), { strict: false })` returns
     (`bull.explorer.js`), and `schedule`, `process-vector-chunks-queue` and
     `process-vector-dimensions-queue` are registered twice (their own modules and
     `internal.module.ts`), so a consumer cannot know which instance it reads. The service gets all of
     them with `moduleRef.get(getQueueToken(name), { strict: false, each: true })` (`@nestjs/core`
     10.4) and calls `pause(true, true)` on each, in its own try/catch: the pause applies only to this
     process and does not wait for running jobs, so the process takes no new job. The names: `api-v2`,
     `schedule`, `process-vector-chunks-queue`, `process-vector-dimensions-queue`,
     `entity-doc-refresh`, `run-spend-recompute`, `superchat-learning`. The consumers do not change.
   - The `api-v2` processor keeps a map of its active jobs. `apiV2` gets a new `onWorkflowStarted`
     callback, like `outputDeliverySink`, which `runApiV2ViaWorkflow` calls after `client.start`; it
     records the job as a B4 job in the map. In `beforeApplicationShutdown`, the processor waits for its
     jobs that are not B4 jobs, for at most 100 s; a job that becomes a B4 job during the wait drops out
     of the wait. It then calls `close(true)` on its queue, injected as a property with
     `@InjectQueue(APIV2_QUEUE_NAME)` (`api-v2` is registered once, in `apiV2Job.module.ts`). Bull
     4.11.4 returns the first call's promise on a second `close()` (`if (this.closing) return
     this.closing;`), so the `close()` that `@nestjs/bull` calls in `onApplicationShutdown` does not
     wait again. `whenCurrentJobsFinished` is not used: it waits for every active job, and a B4 job ends
     only with its workflow. At shutdown, the processor neither resolves nor rejects a B4 job: the
     process exits, Bull fails the job as stalled, and part 4 finishes the run. The other queues keep
     `@nestjs/bull`'s `close()`.
   - The `api-v2` job `timeout` becomes the run ceiling plus 1 h (7 h today) instead of
     `AGENT_JOB_TIMEOUT_MS` (600 s by default): Bull no longer marks a live run of more than 10 min
     failed and frees its Bull worker slot. After part 5, the timeout acts only on a run that the cron
     did not close (flag off, or Temporal unreachable). `resolveAgentJobTimeoutMs` and
     `DEFAULT_AGENT_JOB_TIMEOUT_MS` lose their last caller and are removed with their three tests; the
     two `resolveTenantRunStaleAfterMs` tests that use them are rewritten.
   - Set `stopTimeout` to 120 s on the back container, the Fargate maximum (the service runs on
     Fargate; today the field is empty, so ECS waits 30 s). The `api-v2` wait stops at 100 s, which
     leaves 20 s for the other shutdown steps; if a consumer's `close()` still waits at 120 s, SIGKILL
     ends the process. A legacy run that does not end within 100 s of SIGTERM goes through part 3, until
     Wave 6 removes the legacy path.
   - Lower the target group's deregistration delay from 300 s to 180 s (A9b-D8). ECS sends SIGTERM only
     after the drain, and until then the old task keeps taking Bull jobs, so a shorter delay shortens
     that window. A request still running 180 s after the drain starts is cut.
2. **One terminal outcome.**
   - A run with no claim row (schedule, Zapier, inbound email, `triggerOnly` child) keeps today's stall
     behavior: at a stall, back logs it, delivers nothing and releases its tenant slot.
   - **The claim** is one guarded update of the claim row: it sets the terminal status, the cost, the
     output (`flow_execution_status` only; `mcp_run_status` has no output column) and the stored plan,
     only while the status is `pending` or `in_progress`, and returns whether it changed the row. The
     first writer to claim wins. An empty plan (no Data Output plan and no callback, for example an MCP
     error end) is stored as `NULL`.
   - `FlowExecutionStatusService.markCompleted` and `markError` take the plan and return the boolean
     that `finishFlowExecution` already returns. `McpRunStatusService.markFinished` and `markCancelled`
     get the same guard and an optional plan (`McpRunService.cancelQueuedJob` passes none), and return
     whether they changed the row. Callers that ignore the result keep working.
   - `markInProgress` and `markRunning` update only a `pending` row and return whether they did
     (`markRunning` updates any row today). When they return `false`, `execute` returns `undefined`
     inside its `try`, so its `finally` releases the tenant slot and no failure is reported: the row was
     closed while the job waited (part 5).
   - Every writer works in this order: build the plan, claim, start the stored plan's delivery, then
     clear `end_delivery`. `OutputDeliveryService.start` never throws: it returns the workflow id for a
     new or a duplicate start, and `null` for an empty plan or a failed start (after recording it as
     undispatched). `end_delivery` is cleared only when `start` returns a workflow id, so a failed start
     keeps the plan for a later writer or the cron. In `ApiV2QueueProcessor` the status writes already
     come before the delivery.
   - **A loser starts the stored plan (A9b-D3).** A writer that loses the claim reads `end_delivery`
     and, if it is set, starts its delivery and clears it as above. It never delivers its own outcome.
   - The run's end delivery passes the run id as the invocation id (`OutputDeliveryService.start(plan,
     runId)`). The delivery workflow id is `output-delivery-<flowId>-<plan.context.runLogProcessId>-<runId>`;
     its middle part is set when the plan is built (a scope id from `resolveDeliveryScopeId` for a
     queued run) and the stored plan keeps it, so every start of the same stored plan uses the same
     workflow id and a second start is a duplicate. Every start of a stored plan after the winner's own
     start (by a loser, the reduced end, `failStalledRun` or the cron) passes a new
     `{ recordFailure: false }` option, so a failed start records no second undispatched outcome. Other
     callers of `start` keep their invocation id (random, or `batch-row` for A13). A duplicate start of
     a plan over A9's payload size limit uploads A9's large-payload object again before Temporal detects
     the duplicate; the extra object stays unused (accepted).
   - One generated migration adds `end_delivery` (nullable `jsonb`) to both tables, `end_context`
     (nullable `jsonb`, part 4) to `run_seeds`, and four partial indexes, declared on the entities with
     `@Index(name, propertyNames, { where })` so that later generated migrations keep them
     (`propertyNames` lists entity property names; `where` uses database column names):
     - `IDX_FLOW_EXECUTION_STATUS_OPEN` (`startedAt`, `createdAt`)
       `WHERE status IN ('pending', 'in_progress')`;
     - `IDX_FLOW_EXECUTION_STATUS_END_DELIVERY` (`finishedAt`) `WHERE end_delivery IS NOT NULL`;
     - `IDX_MCP_RUN_STATUS_OPEN` (`updatedAt`, `createdAt`) `WHERE status IN ('pending', 'in_progress')`;
     - `IDX_MCP_RUN_STATUS_END_DELIVERY` (`updatedAt`) `WHERE end_delivery IS NOT NULL`.
     The migration creates them without `CONCURRENTLY`, which blocks writes to each table while it is
     scanned (accepted: on dev on 2026-11-13 the tables held 105 and 568 rows; production sizes were not
     queried).
   - A new `RunEndDeliveryService` (`src/app-api/flux/run-end/`) takes from the processor the
     consolidated-callback payload, the plan building, `runErrorMessage` and the error body of
     `reportRunFailure`. It also implements the claim with the stored plan and the start of a stored
     plan. The processor, part 4's reduced end and part 5 use it. The run-end messages live in
     `run-end-messages.ts` next to it: `STALLED_RUN_MESSAGE` (moved from the processor),
     `RUN_CEILING_MESSAGE` ("The run stopped because it ran longer than the maximum run time. Run it
     again to retry."), `RUN_NOT_STARTED_MESSAGE` ("The run was cancelled because it did not start
     within 24 hours. Run it again to retry.") and `RUN_OWNER_MISSING_MESSAGE` ("The run could not be
     finished because its agent or its owner no longer exists.").
3. **A legacy run that lost its process.**
   - For an async run, `failStalledRun` asks Temporal about `run-<runId>` through a new public
     `ExecutionsLogsService.describeRunWorkflow(runId)`. It returns
     `{ state: 'running' | 'closed' | 'missing' | 'unknown', closeStatus?, result? }`: `unknown` when
     Temporal cannot be reached or does not answer within `RUN_LIVENESS_TIMEOUT_MS` (1.5 s); for a
     `COMPLETED` workflow, `result` is read with `handle.result()`. The private `isRunWorkflowAlive`
     returns only true or false and returns true on a timeout, so it is not reused.
     - `running`: a B4 run. Return; part 4 finishes it.
     - `closed`: a B4 run whose handler died after the workflow ended. Run part 4's reduced end now,
       with the close mapping of part 4.
     - `unknown`: log and return. The run stays `in_progress` until part 5 closes it, and keeps its
       tenant slot until the ledger drops it at the run ceiling.
     - `missing`: a legacy run, handled by the steps below.
   - For a legacy run, `failStalledRun` runs these steps in order. It writes no cancel request
     (A9b-D15).
     1. Schedule the cost recompute in two passes (A9b-D14), before the claim, so a throw after the
        claim cannot lose it: `RunSpendRecomputeQueue.schedule` with job id `run-spend-stall:<runId>`
        after 5 min, and with job id `run-spend-stall-final:<runId>` after 35 min (the 30-min
        `startToCloseTimeout` of `textGeneratorActivity` plus 5 min). The ids differ from the
        handler's own `run-spend:<runId>`. A new optional `delayMs` (used instead of the fixed
        `RUN_SPEND_RECOMPUTE_DELAY_MS` when set), `jobId` and `resolveFromRunId` on the job set them;
        a `resolveFromRunId` job passes `execIds: []`. With `resolveFromRunId`, the consumer reads the exec ids when the job runs:
        the run id, the child run ids (below), and every `node_executions.execId` whose `runId` is one
        of them. A later pass therefore includes steps opened after the stall, and a pass scheduled by
        a writer that then loses the claim writes the full sum. Both passes write the claim row's cost
        (`flowExecutionStatusId` or `mcpRunStatusId`). The claim row shows 0 until the first pass
        writes the cost. A job with the same id that is pending, or failed and still kept (7 days),
        makes the new one a no-op. If the run id is not a UUID, the `node_executions` query is skipped
        and logged (`node_executions.runId` is a `uuid` column); async runs use the claim row's id, a
        UUID.
     2. Claim the end with `error` and `STALLED_RUN_MESSAGE` (part 2). If the claim won, start the
        stored plan's delivery; if it lost, start the winner's stored plan.
     3. Interrupt the node workflows still in flight, for the run id and every child run id, through a
        new public `ExecutionsLogsService.interruptStalledRun(runIds)`. It calls the existing private
        `interruptStepsInFlight` for each id with a new option that filters with `runKeyMatchExpr`, the
        form that `IDX_NODE_EXECUTIONS_RUN_NODE` and `IDX_NODE_EXECUTIONS_EXEC_NODE` serve; today's
        `runKeyExpr` filter reads `metadata->>'runId'`, which no index covers. It does not call
        `cancelRun`, which writes a cancel request and cancels `run-<runId>`. For a run that already
        ended, the interrupt finds nothing.
     4. Release the tenant slot, as today. A legacy run whose handler is still alive after a lost lock
        loses its tenant slot early (accepted: the ledger drops it at the run ceiling).
   - **Child runs (A9b-D11).** `apiV2`, `flowCallerNode` and `libraryNode` get a new `parentRunId`
     parameter (line numbers as of back `ba55e32`). `apiV2`'s four calls into the two handlers
     (`flux.service.ts` 5767, 5798, 5923, 5976) pass `runLogProcessId`. `dispatchLegacyHandler` (2726)
     passes its `execId` when `runExecIds` is set: that is the prefetch path
     (`runApiV2FlowLoopPrefetch`), where `execId` is the parent's run id. Otherwise it serves
     worker-dispatched handlers, has no run id and passes none. Both handlers forward `parentRunId` into
     their own `apiV2` calls (6866–6880, 7225–7240). In the child's `apiV2`, right after
     `runLogProcessId` is computed and next to `chainRootRegistry.register`, before any node can charge,
     the child registers when `parentRunId` is set and differs from its own run id: it adds its run id
     to the Redis set `flux:run-children:<parentRunId>`. A new `RunChildrenRegistry`, modeled on
     `ChainRootRegistry` (`@Inject('REDIS_CLIENT')`, `withRedisCommandTimeout`), does the `SADD` and
     refreshes the set's TTL to the run ceiling plus 1 h on every add, so the 35-min pass still finds
     it. The recompute and the interrupt read the set for the run, then for each child, with a visited
     set (no depth constant exists: `maxCascadeSize` is a per-flow setting). Children started with
     `triggerOnly` are not added: their cost was never part of the parent's. If Redis fails when a child
     adds its run id, that child's charges and steps are missing from a stall; the failure is logged
     with both run ids.
4. **A B4 run: the worker triggers the finish (A9b-D6).**
   - **Which runs.** `ApiV2QueueProcessor` passes a new `finishInWorker: true` to `apiV2` only for a job
     with a claim row (`executionId` or `mcpTracking`). `apiV2` passes it on to `runApiV2ViaWorkflow`
     only for a root run (no `parentCancelRunKey`), and the workflow input then has
     `finishApiRun: true`. Sync callers, schedules, Zapier, inbound email and child runs never get it.
   - **Inline children stay on the legacy loop (A9b-D13).** The B4 decision in `apiV2` adds "and
     `parentRunExecIds` is not set". This closes an existing defect: an eligible library or flow-caller
     child that has the parent's run id starts `run-<parentRunId>` and writes `runWorkflowId` on the
     parent's row. Children started with `triggerOnly` have their own run id and keep the B4 path. B6
     moves children to child workflows.
   - **The MCP Bull job id.** `McpRunService` enqueues with `jobId: processId`; today it passes no
     `jobId`. The Bull job id then equals the run id for MCP runs too, as it already does for API runs
     (`jobId: executionId`).
   - **The live end keeps writing the end.** `apiV2` and the processor keep writing the end and
     returning the result, so sync waiters, the chat log and the schema change work as today. For a
     `finishInWorker` run, the live end writes the flow log with `id: runId` on the success and the
     error paths (`createLog` upserts by id) and the chat log with `claimId: runId` (`recordChatLog`
     inserts it once and skips it after), so a reduced end that also runs adds no second row.
   - **The end context** of a `finishInWorker` run is stored in the new `run_seeds.end_context` column,
     not in `payload`: `GET /worker/run-seed/:id` returns `payload`, and `loadRunSeedActivity` returns
     it into the Temporal history, so the end context stays out of that history. It holds `flowId`,
     `userId`, `sessionId`, `callbackSessionId` (the raw `params.sessionId ?? null` that the callback
     sends), `runType`, `sendEmail`, `mcpTokenId`, `flowVersionHistoryId` and the API `variableInputs`
     (`MultipleDataDto[]`). `PersistRunSeedInput` gains an optional `endContext`; `load()` keeps
     returning `payload` only. A new back-only `RunSeedService.loadEndContext` takes a
     `seedSnapshotId` or a run id and returns the end context and the row's `createdAt`; by run id it
     reads the newest row for that `run_id` (indexed, not unique). The callback URL stays in
     `flow_execution_status.callback_url`.
   - **A run seed with no end context.** On the `closed` path (parts 3 and 5) the reduced end can reach
     a B4 run started by an older back. It then takes the flow from `flow_id` (`agent_id` for MCP), the
     user from `user_id` (unknown for MCP) and the callback from `callback_url`, and uses
     `callbackSessionId` `null`, `sendEmail` `false`, an empty input body and the flow's deployed
     version (`resolveExecutionHistoryId(flow)`, as A13's fallback does). When the user or the flow
     cannot be loaded, step 2 below applies.
   - **Worker (A9b-D16).**
     - `loadRunSeedActivity` and the scheduler build (`buildSchedulerState`,
       `deserializeSchedulerState`) move inside the `try`, so their errors reach the `catch` and the
       `finally`. In the `finally`, `storeRunResultActivity` and `emitRunEventActivity` each run in a
       try/catch that logs, so the finish still runs when they fail.
     - When the input has `finishApiRun`, `processFlow` calls a new `finishApiRunActivity` in its
       existing `!isContinuing` `finally`, after `emitRunEventActivity`, in a non-cancellable scope,
       behind `patched('a9b-finish-api-run')`. It posts `runId`, `seedSnapshotId`,
       `flowVersionHistoryId` (from `ProcessFlowInput`), `finalStatus` and `nodeFailure` to
       `POST /worker/api-run-finish`. `startToCloseTimeout` 1 min; retry `initialInterval` 1 s,
       `backoffCoefficient` 2, `maximumInterval` 60 s, `maximumAttempts` 60 (about 1 h); HTTP 400 and
       404 are non-retryable, as A13's `finishBatchRowRunActivity` does. A failure of the activity is
       caught and logged in the workflow, which still returns `{ status: finalStatus, … }`: a live
       handler never reports a successful run as `error` because back was unreachable. Part 5 closes a
       run whose finish never reached back.
     - In the outer `catch` of every `processFlow` run, an error is rethrown as it is when `isContinuing`
       is set, when it is a cancellation, or when it is a `TemporalFailure`; any other error is rethrown
       as `ApplicationFailure.nonRetryable` with its message. A plain `Error` in workflow code (for
       example `Node … not found in seed`) then fails the workflow and the `finally` runs, instead of
       retrying the workflow task forever. This also applies to `processBatch` rows (a plain `Error`
       becomes a failed row) and to scheduled runs. Workflows stuck in task retries when the new worker
       ships fail at their next workflow task attempt.
   - **The finish endpoint** (`FluxService.finishApiRunFromWorkflow`) finds the claim row by run id in
     `flow_execution_status`, then in `mcp_run_status`; with neither, it answers HTTP 404. It returns
     `{ outcome: 'finished' | 'owned' }` and handles three cases:
     - `finished`: the claim row is terminal. If `end_delivery` is still set, back starts it (part 2).
     - `owned`: a new `ApiV2Queue.isHeldByLiveHandler(runId)` finds the run's Bull job active
       (`job.isActive()`) with its lock key (`job.lockKey()`) present in Redis, so a live handler will
       write the end. The activity ends; it does not retry, because the handler's `handle.result()`
       waits for this activity.
     - Orphaned: no live handler. Back writes the reduced end and answers `finished`.
     On this path the reduced end loads the end context by the posted `seedSnapshotId`; every run that
     gets `finishApiRun` was started by a back that writes it. On the `closed` path it loads it by run
     id, and the fallback above covers an older run seed.
   - **The reduced end** (`FluxService.finishOrphanedApiRun`, modeled on `finishBatchRowRun`):
     1. Read the claim row. If it is terminal, answer `finished` as above and write nothing else.
     2. Load the end context, the user and the flow (MCP rows: `agent_id` as the flow). If the user or the
        flow no longer exists, claim `error` with `RUN_OWNER_MISSING_MESSAGE` and no logs, start the
        stored plan's delivery and stop, instead of answering 404 on every retry.
     3. Cost from `runChargeTotals`; flow log (`id: runId`); space run log (keyed by the run id); if the
        cost read failed, schedule a recompute with targets `flowLogId`, `spaceRunLogId` and the claim
        row; `settleRunOutputs` with the run's `sendEmail` and `flowVersionHistoryId` (the posted value;
        on the `closed` path, the end context's), collecting its Data Output plan; chat log
        (`claimId: runId`).
     4. Build the result `{ message, nodeError, cancelled, totalTokensUsed, totalCost, outputs }` from
        `settleRunOutputs`, as `apiV2` returns it, with `cancelled` set when the status is `cancelled`.
        The claim status: `cancelled` when `finalStatus` is `cancelled`. Else, when `finalStatus` is
        `error` and no node failed, `error` with `readRunEnds(runId).error?.userMessage ??
        RUN_FAILED_MESSAGE`, as `finishBatchRowRun` does; the result's `nodeError` carries that
        message. Else the processor's rule (`runErrorMessage`): `error` with `nodeError` when it is
        set, else `completed`. So the callback says `success: false` exactly when the claim is
        `error`. `finalStatus` also sets the `failed` and `stopped` inputs of `settleRunOutputs`. `durationMs` is from `readRunEnds(runId).startedAt`, or
        the run seed's `createdAt`. A cancelled API row uses `CANCELLED_RUN_OUTCOME`.
     5. Claim with the result as `output` and the stored plan (the Data Output plan plus the
        consolidated callback built from `callback_url`, `callbackSessionId` and the result); start the
        stored plan's delivery; release the tenant slot (a no-op when the ledger already dropped it, as
        when the cron runs this end).
     A retried activity finds the claim row terminal at step 1 and only starts a stored plan that is
     still set.
   - **The close mapping** (parts 3 and 5, `closed`): `COMPLETED` uses the result's `status` as
     `finalStatus` and its `nodeFailure` (through `withWorkflowNodeFailure`, as the posted path does);
     `FAILED`, `TERMINATED` and `TIMED_OUT` give `error` with no node failure; `CANCELLED` gives
     `cancelled`. Step 4's rule then claims `error` for every failed kind.
   - **A handler that dies after `owned`.** `failStalledRun` sees `closed` and runs the reduced end
     (part 3). If a handler dies after its claim and before its delivery starts, `failStalledRun` sees
     `closed`, finds the claim row terminal, and starts the stored plan.
   - `finishExecution` (`run-events.service.ts`) writes only an unfinished row with no `runWorkflowId`
     whose run events hold a `run_finished` with a `resultRef`, which only `processFlow` emits. A B4 run
     sets `runWorkflowId` before `client.start`, so `finishExecution` does not race the claims of A9b.
   - A run workflow that someone terminates never calls the finish activity; part 5 closes its run.
   - If back died between `setRunWorkflowId` and `client.start`, no workflow exists: part 3 treats the
     run as legacy and fails it; no node ran, so no charge is lost.
5. **No run stays unfinished (A9b-D9).**
   - A cron job, `UnfinishedRunReaperService` in `src/cronJobs/unfinishedRunReaper/`, runs every 10 min
     (`@Cron`) while the `unfinished_run_reaper` flag is on. `CronLockService.runExclusively` holds a
     database transaction for its whole callback, so the job only selects the ids inside it, on one
     replica per tick. It handles each row after the transaction ends. Two overlapping ticks are safe:
     the claim prevents a second status, and the fixed delivery workflow id prevents a second delivery.
     It reaches Temporal only through `ExecutionsLogsService` (`describeRunWorkflow`,
     `interruptStalledRun` and a new public `cancelRunWorkflow(runId)` that throws when the cancel
     fails, unlike the private `cancelRunWorkflowIfPresent`, which swallows errors), so
     `CronJobsModule` needs no `TemporalModule`.
   - **Pending cancels.** A run id whose cancel failed is added to the Redis set
     `flux:reaper:cancel-pending` (TTL 7 days, refreshed on every add). Each tick first retries every
     member and removes it when `cancelRunWorkflow` succeeds or `describeRunWorkflow` returns `closed`
     or `missing`.
   - The limit is `max(run ceiling + 30 min, flag value in minutes)`, read with
     `FeatureFlagsService.getValue`, as `superchat_daily_cap` does.
   - Each select takes at most 100 rows per tick, oldest first, through the partial indexes of part 2:
     - `in_progress` rows older than the limit: by `flow_execution_status.started_at`, and by
       `mcp_run_status.updated_at`, which `markRunning` sets (a later update only makes the age lower);
     - `pending` rows older than 24 h, by `created_at` (`WHERE status = 'pending' AND created_at < $1
       ORDER BY created_at LIMIT 100`, which reads the `*_OPEN` index);
     - terminal rows that still have `end_delivery` and are older than 10 min (`finished_at`;
       `updated_at` for MCP): it starts the stored plan and clears it as in part 2.
   - **Old rows (A9b-D17).** An unfinished row whose age, on its select's column, is over 7 days goes
     through the same branches as a younger row, with two differences: its stored plan is `NULL` (no
     callback, no email, no Data Output delivery), and on `closed` the reduced end is replaced by a
     claim with the close mapping's status and step 4's message rule, with no logs and no output. Its
     messages, recompute passes, cancels and interrupts are the same. It is logged with its run id. This
     covers the rows already unfinished when the flag is first turned on (see **Rollout**).
   - For an unfinished row, it calls `describeRunWorkflow(runId)`:
     - `running` (a B4 run past the limit): schedule both recompute passes, claim `error` with
       `RUN_CEILING_MESSAGE`, start the stored plan, then cancel `run-<runId>`; a failed cancel goes to
       the pending cancels. The finish in `finally` then gets `finished` (part 4).
     - `closed`: part 4's reduced end, with the close mapping.
     - `missing`, and `ApiV2Queue.isHeldByLiveHandler(runId)` is true: a live legacy run. Write the chain
       cancel (A9b-D15): `requestCancel` with the row's flow (`agent_id` for MCP), the user from
       `user_id` or, for an MCP row, from the Bull job's `params.user.id`, and
       `stopReason: { reason: 'run_ceiling', limitMs }`. Like the chain spend ceiling, it stops the whole
       chain. Then schedule both recompute passes, claim `error` with `RUN_CEILING_MESSAGE`, start the
       stored plan, interrupt the steps of the run and its children, and write `cancelledAt`
       (`RunCancellationService.markCancelled` with `stoppedAtNodeId: null` and
       `notExecutedNodeIds: []`), so the run log does not stay "Cancelling". `markCancelled` writes only
       while `cancelledAt` is null, so the handler's later, more detailed record is dropped (accepted).
       The handler stops at its next cancel check and loses the claim.
     - `missing` and no live job: a dead legacy run, or a B4 run whose workflow Temporal no longer
       keeps (on an API row, `run_workflow_id` is set; both get the same end). Schedule both recompute
       passes, claim `error` with `RUN_CEILING_MESSAGE`, start the stored plan, interrupt the steps of
       the run and its children.
     - `unknown`: skip the row this tick and log it. Closing it could fail a live B4 run during a
       Temporal outage.
   - A `pending` row past 24 h: claim `error` with `RUN_NOT_STARTED_MESSAGE` first, then remove the
     queued Bull job (a failed removal is logged). If the job starts anyway, `markInProgress` or
     `markRunning` returns `false` and the processor skips it (part 2).
   - The error delivery comes from `RunEndDeliveryService`: `callback_url` for an API run (an MCP run has
     no callback) and the consolidated error body that `reportRunFailure` sends today. Its delivery
     context uses `runType` `'api'` for an API row and `'mcp'` for an MCP row, and `userEmail` from the
     user of `user_id` for an API row, or `''` for an MCP row or when the user cannot be loaded (an MCP
     error plan is empty and stored as `NULL`).
   - The cron releases no tenant slot: the ledger drops a tenant slot at the run ceiling, before the
     cron's limit.

**Recovery paths.** Four paths recover an end that did not complete: Temporal retries
`finishApiRunActivity`; `failStalledRun` acts on a B4 run whose handler died; part 5 closes a run that
`failStalledRun` left unfinished (nothing retries `failStalledRun` itself: `attempts: 1`,
`maxStalledCount: 0`); and part 5 starts a stored plan that no one started. A9's guarantees stay as
they are: email is suppressed by its dedup keys (D-A9-6) and every callback carries
`X-FluxPrompt-Delivery-Id` (D-A9-8). In addition, the run's end delivery has the fixed delivery
workflow id (part 2, A9b-D10), and the recompute passes are scheduled before the claim.

**Rollout.**

- Deploy the worker before back, in each environment. If back ships first, an older worker ignores
  `finishApiRun`, and a run whose handler dies stays `in_progress` until part 5 closes it. A newer
  worker with an older back receives no `finishApiRun` and behaves as today.
- MCP jobs queued before the back deploy keep a random Bull job id, so for them
  `isHeldByLiveHandler(runId)` is false: part 4 treats a live handler as orphaned, and part 5 treats
  a live legacy MCP run as dead. This applies only to runs in flight across the deploy.
- AWS: set `initProcessEnabled` only after the back image with the new `dev.sh` is in production. With
  the old image, the init process is expected to send SIGTERM to the `/bin/sh -c` shell, which exits at
  once and kills the run in flight (inferred from the image; the negative control in **Verification**
  checks it). Between the back deploy and this change, `node` is PID 1: `exitAfterClose` still exits with 0
  after the close, and only the init process that reaps the finished database seed shell is missing
  (one zombie process per container, harmless). `stopTimeout` and the
  deregistration delay do not depend on the image. A person with AWS write access applies the three
  changes.
- The seed migration creates the `unfinished_run_reaper` flag off. Before turning it on in an
  environment, run `etc/<YYYY-MM-DD>/<NN>-a9b-unfinished-runs-by-age.sql` in the Workflow repository
  (one read-only statement that runs in DBeaver; run it on dev first): it counts the unfinished rows by
  age (under 7 days, over 7 days) in both tables. Then turn the flag on; rows over 7 days are closed
  with no callback and no email.

**Out.**

- A refund for charges already made (A9b-D4). A run killed before this ships keeps its charges.
- Resuming a legacy run mid-way (A9b-D5).
- Letting the B4 handler return right after it starts the workflow, which would free Bull worker
  slots: it changes how back limits concurrent runs.
- Bull's own lock settings (`lockDuration`, `stalledInterval`).
- Raising the run ceiling (`RUN_MAX_DURATION_MS`, for example to 12 h): a separate change in the task
  definition, which also changes the TTL of the chain keys. Part 5's limit follows it.
- Inline child runs on the B4 path (A9b-D13): B6.
- A cancel request for a handler that lost its lock but still runs (A9b-D15): it loses the claim at its
  end and only starts the winner's stored plan.
- **Known undercount.** A legacy run that dies loses up to 99 inline loop-body executions that
  `InlineNodeExecutionBatch` had not yet written (size 100). It applies to a run that records events
  and has a loop whose body runs inline in back. The stall recompute cannot find their charges.
- **Inbound-email run ids.** An inbound-email run's run id (`pop3-processed:…`) is not a UUID. A
  production query on 2026-11-13 found 0 `email` runs in `flows_logs` in the last 60 days, so whether
  such runs reach part 3's non-UUID guard cannot be checked in production. If email runs appear, the
  engineer who sees them files a separate bug.

## Verification

Every `await` after a side effect (an end claimed, a delivery started, a step interrupted, a workflow
cancelled, a cancel written) gets a test where it throws, and the next attempt neither delivers again
nor writes a second status: the claim stops a second status, and the fixed delivery workflow id stops a
second delivery.

- **Graceful shutdown, negative control.** Locally, run two containers of the production image with
  `docker run --init` (the local equivalent of `initProcessEnabled`) against the same Postgres and
  Redis. Start container A, queue a run of about 60 s, wait until A takes it, then start container B.
  Run `docker stop -t 120 A` and queue a second run. On the current image, the init process forwards
  SIGTERM to the `/bin/sh -c` shell, which exits at once and kills the run in flight. After the change,
  A logs that its queues paused, takes no new job, finishes the first run and exits before 120 s; B
  takes the second run. Two more cases: a B4 run in flight on A, which A leaves to part 4 with no status
  written; and a legacy run that does not end within 100 s of SIGTERM, which goes through part 3.
- **Shutdown hooks.** `BullShutdownService`: in a test module where one queue name is registered twice,
  both instances are paused, and a rejected pause does not reject the hook. Tests on the `api-v2`
  processor: the wait covers only jobs that are not B4 jobs, stops at 100 s, and ends with `close(true)`
  on its queue; a job that becomes a B4 job during the wait does not delay it. Tests assert that
  `TemporalService` no longer closes its connection in `onModuleDestroy` and that `SpaceRunLogsService`
  clears its timers in `onApplicationShutdown`. A test asserts that the `api-v2` job timeout is the run
  ceiling plus 1 h.
- **One outcome, both orders, both run kinds.** Four processor tests, driven through `onFailed` with
  `BULL_STALLED_JOB_ERROR` because `failStalledRun` is private: an API run (`executionId`, callback
  URL) and an MCP run (`mcpTracking`), each with the stall first and with the live end first. On the
  current code each test starts two delivery workflows; the API run's execution status keeps the first
  value (the compare-and-set), and the MCP run's status changes from the first outcome to the second
  (`markFinished` has no guard). After the change each test shows one status write and at most one
  delivery workflow: the MCP run with the stall first starts none, because its end has no callback and
  no node outputs. Revert the change and confirm that all four fail. More tests: the winner dies after its
  claim and before its delivery start, and the loser starts the stored plan once; a failed start
  (`start` returns `null`) keeps `end_delivery`; an empty plan is stored as `NULL`; a job whose row is no
  longer `pending` returns without running and releases its tenant slot.
- **Test helper.** `buildProcessor` (`apiV2Job.processor.spec.ts`) makes `markInProgress`,
  `markRunning`, `markCompleted`, `markError`, `markFinished` and `markCancelled` return `true` by
  default, and adds defaults for the `api-v2` queue (`close`), `RunSpendRecomputeQueue.schedule`,
  `describeRunWorkflow`, `interruptStalledRun`, `RunChildrenRegistry` and `RunEndDeliveryService`. The
  queue is a property injection, so `new ApiV2QueueProcessor()` still builds. Without these defaults,
  every existing test would skip its run (part 2).
- **Legacy stall.** Tests assert, for API and MCP runs: `running` returns without writing; `closed` runs
  the reduced end; `unknown` only logs; `missing` schedules both recompute passes before the claim,
  claims with `STALLED_RUN_MESSAGE`, starts the stored plan, interrupts the run and its children, and
  writes no cancel request; a lost claim starts the winner's stored plan; a throw after the claim leaves
  both passes scheduled; a run with no claim row keeps today's behavior. An integration test against
  local Postgres and Redis (`pnpm infra:up`) checks that, after the final pass, the recorded cost equals
  the ledger's charges for the run, including a library child run in a space with run logging off and a
  step charged after the stall.
- **B4 finish.** Back tests for `finishApiRunFromWorkflow`: `finished` (with and without a stored
  plan), `owned`, the orphaned case with `success`, `error` and `cancelled`, and no claim row (404); a
  `success` run whose result has a `nodeError` is claimed `error`, and its callback says
  `success: false`; an orphaned `error` finish with no `nodeFailure`, and a `TERMINATED` close, are
  claimed `error` with the run-events message or `RUN_FAILED_MESSAGE`; `GET /worker/run-seed/:id` never
  returns the end context; a run seed with no end context uses the claim-row fallback; the reduced end writes node data under the posted `flowVersionHistoryId`; a retried
  orphaned finish writes no second flow log, space run log or chat log; a deleted flow or user ends with
  `RUN_OWNER_MISSING_MESSAGE`. Worker tests: the activity runs in `finally` for an input with
  `finishApiRun` and not for others, runs after a cancel, after a plain `Error` in workflow code, after a
  failed `loadRunSeedActivity` and after a failed `emitRunEventActivity`, does not run when
  `isContinuing`, and its failure leaves the workflow result unchanged; a continue-as-new still
  continues; a plain `Error` in a `processBatch` row's `processFlow` fails the row instead of hanging.
  `process-flow.replay.spec.ts` loads two new histories, `process-flow-a9b-before-finish.json` and
  `process-flow-a9b-with-finish.json`, and fails if either is missing (today it skips when it finds no
  `process-flow-*.json` file, and the three existing histories, `before-gate.free-node.json`,
  `before-gate.text-node.json` and `with-gate.text-node.json`, do not match that name). Each is recorded
  for the same two-node flow, from the current worker build and from the new one, with
  [`scripts/a9b-replay-histories/`](scripts/a9b-replay-histories/README.md). The batch-row fix (see
  **Implementation record**) adds two `processBatch` histories with a failed row child. Manual check: two back processes
  and a worker locally, with the worker's `URL_MAIN_API` on the process that survives; start a run on
  the B4 path, kill the process
  that started it with SIGKILL, and confirm that the other process writes `completed`, delivers once
  and records the cost. On the current code the run ends `error` with every node charged.
- **Nested runs.** Tests assert that a library child (`parentRunExecIds` set) takes the legacy loop
  with `engine_in_workflow` on, that a `triggerOnly` child keeps the B4 path, that a child with its own
  run id adds it to its parent's set before its first charge and refreshes the TTL, that a library
  child on the prefetch path registers under its parent, and that `dispatchLegacyHandler` outside the
  prefetch path registers nothing.
- **Reaper.** Tests for the cron: nothing while the flag is off; with the flag on, each case of part 5
  (`running` with `RUN_CEILING_MESSAGE` before the cancel, `closed`, live legacy with the chain cancel
  and `cancelledAt`, dead legacy, `unknown`, `pending` past 24 h with `RUN_NOT_STARTED_MESSAGE`, a stored
  plan not started, a row over 7 days closed with no delivery in each branch, a failed cancel kept in
  the pending cancels and retried the next tick); at most 100 rows per select, oldest
  first; the limit is never below the run ceiling plus 30 min; it selects inside the lock and works
  after the transaction.
- **Query cost.** Run `EXPLAIN ANALYZE` on a local copy:
  - the cron's six selects (three per table), with at least 10,000 rows per table: each plan uses its `*_OPEN` or
    `*_END_DELIVERY` index and no sequential scan;
  - the recompute's `node_executions` read by `runId` and the interrupt's `runKeyMatchExpr` filter,
    with at least 1 million `node_executions` rows: each plan uses `IDX_NODE_EXECUTIONS_RUN_NODE` or
    `IDX_NODE_EXECUTIONS_EXEC_NODE` and no sequential scan.
- **Rollout query.** The count query runs on dev with no error before it is used in production.

## Done when

- A back deploy does not kill an async run on the B4 path: its handler, or any back when its handler is
  gone, writes one status and at most one delivery (an MCP run has no callback) and records a cost
  equal to its charges.
- A legacy async run that loses its process ends with one status and at most one delivery and, after
  the final recompute pass, a recorded cost equal to its charges, its library and flow-caller child
  runs included, except the inline loop executions in **Out**.
- A back task stopped by a deploy takes no new Bull job after SIGTERM, and a legacy run whose remaining
  work takes less than 100 s after SIGTERM completes and writes its live end.
- A plain `Error` in `processFlow` code fails the workflow instead of retrying its task forever.
- While the `unfinished_run_reaper` flag is on and Temporal answers, the cron closes every async run
  `in_progress` past its limit or `pending` past 24 h within one tick of that age (more if over 100 rows
  wait), and starts every stored plan that no one started.

## Estimate

Revised after round 2 (+12 h), round 3 (+6 h), round 4 (+5 h) and round 5 (+2.5 h) on 2026-11-13.

| Part | Min | Average | Max |
|---|---|---|---|
| 1. Graceful shutdown | 8 h | 13 h | 21 h |
| 2. One terminal outcome and the stored plan | 6 h | 10 h | 16 h |
| 3. Legacy stall: interrupt, recorded cost, child runs | 8.5 h | 13 h | 20 h |
| 4. B4: the worker triggers the finish | 14 h | 23.5 h | 40.5 h |
| 5. No run stays unfinished | 10 h | 15 h | 23.5 h |
| **Total** | **46.5 h** | **74.5 h** | **121 h** |

## Implementation record (2026-11-16)

Branches: back `fix/868mvdm50` and worker `fix/868mvdm50`, both cut from `origin/main` (back
`240b824f` merged in as `d7b66205`; worker `834cb32`).

| Part | Back | Worker |
|---|---|---|
| 1. Graceful shutdown | `223022a1` | — |
| 2. One terminal outcome and the stored plan | `758b0cb8`, migration `af6e16a1` | — |
| 3. Legacy stall | `2f3e4457` | — |
| 4. B4 finish | `9e095fe4` | `1307e76` |
| 5. Reaper | `b68f5135` | — |
| Reviews (`/simplify`, `/code-review`) | `7649ecfb`, `f22e6725`, `8cdeb0c2` | `471610e`, `b9c4e61` |
| Batch-row fix | — | `2af9876` |
| Replay histories | — | `9e12516`, `22aed78` |
| `env-vars-sync` | `5a180338` | — |
| Internal error text, worker exit | `0bb15208` | `401c494` |

### Decisions taken during implementation

- **A stored plan that no one starts for 7 days is given up and recorded once.** The reaper starts
  every stored plan it finds; a plan still stored after 7 days is cleared with its failure recorded,
  as D17 does for a row with no delivery. This is an assumption: dev holds no such row.
- **`duration_ms` is clamped to 2,147,483,647**, the largest value its `integer` column holds, and it
  ends at `run_finished`.
- **A run whose flow or owner is gone keeps its cost.** It ends with `RUN_OWNER_MISSING_MESSAGE`; an
  MCP run with an older seed reads its user through `selectFlowAdmin`.
- **A plain `Error` in `processFlow` reports `userMessage: 'Run failed'`**, with the raw text in
  `devMessage` only, and fails the workflow with an `ApplicationFailure` that keeps the cause.
- **The finish POST treats a 404 as final only when the body says `Run not found`.** A route-level 404
  from an older back during a deploy is retried. Both finish POSTs abort with the activity.
- **`describeRunWorkflow` returns a union** (`running`, `closed` with its close status, `missing`,
  `unknown`), and `cancelRunWorkflow` returns quietly on `WorkflowNotFound`.
- **Batch-row fix (approved by the user).** When a `processBatch` row's `processFlow` child fails for a
  reason other than a cancel, the row now finishes its run through `finishBatchRowRunActivity` with
  status `error`, behind `patched('a9b-batch-row-child-failure-finish')`. Before, that run stayed
  unfinished. A failed finish only logs: the row stays failed and the batch goes on.

### Evidence

- Back: about 2,692 tests pass. The only failures, 1 in `node-output-reset.spec.ts` and 4 in
  `flux.controller.batch-process.spec.ts`, also fail on `main`.
- Worker: the A9b specs pass, and the three replay specs replay every history on disk. Each new test
  was seen failing against a broken fix.
- `EXPLAIN ANALYZE` on a local copy (1.2 million `node_executions` rows, rolled back): the six reaper
  selects and the recompute and interrupt reads use their indexes, with no sequential scan.
- The count query `etc/2026-11-16/a9b-unfinished-runs-by-age.sql` ran on local and on dev with no
  error; dev holds no unfinished row.
- `dev.sh`, in the back image with a `curl` stand-in: `node` is PID 1, the seed runs after `/health`,
  SIGTERM reaches `node`, and the container exits 0. The finished seed shell stays a zombie, one per
  container, because `node` does not reap it.
- Security review (back and worker): no high or medium finding. New Redis keys hold only run ids that
  back creates; every new error text sent to a customer is a fixed message or the node's
  `userMessage`.

### Manual checks on a local stack

Two back processes (ports 3001 and 3002) and the worker, built from the branches, with the local
Postgres and Redis and the Temporal dev server; the flow is `globalStarter` → `mathFunction` → Data
Output. A run stays in flight while the worker is stopped. The container part (the shell, `dev.sh`,
`node` as PID 1) was checked separately (**Evidence**), so these checks signal the `node` process.

| Case | What happened |
|---|---|
| SIGTERM, no job | Both queues pause (10 instances), the wait finds 0 runs, and the process exits in 1 s. |
| SIGTERM, legacy run ends within 100 s | The process logs one run waiting and takes no new job; the run completes after the worker starts and the process exits at 26 s. One `completed` status, one callback. |
| SIGTERM, legacy run still going at 100 s | The process closes its queue with 1 run still going and exits at 102 s. The other process takes the stalled job and writes `error` with `STALLED_RUN_MESSAGE`; one callback with `success: false`. |
| Run queued after SIGTERM | The other process takes it: `completed`, one callback. |
| SIGKILL, B4 run (`engine_in_workflow` on) | The worker's finish gets `owned`, because the dead process's Bull lock has not expired. When it expires, the other process takes the stalled job, finds the workflow `closed` and runs the reduced end: `completed`, one callback, one flow log. |
| SIGTERM, B4 run | The process does not wait for the B4 run and exits in 1 s. The finish gets `owned` while its lock lasts; the other process then closes the run through the stall path: `completed`, one callback 29 s after SIGTERM. |
| Two workers, SIGTERM one during 10 B4 runs | The stopped worker drains and exits; two runs that started on it finish on the other. 10 `completed`, one callback each. |
| Two workers, SIGKILL one during 10 B4 runs | 8 `completed` and 2 `error`, one callback each. Each `error` run had a node activity running on the killed worker: the activity times out after 60 s and is not retried, because node activities use `maximumAttempts: 1` (as on `main`). |

Every run ended with one status and one callback. The Docker two-container variant, with
`--init` and the production image, was not run.

### Production image check (2026-11-16)

Both images were built from the branches with their `Dockerfile` (the install `timeout 150` raised
locally only, for a slow network) and run against the local Postgres, Redis and Temporal dev server.
Each case waits for `/health`, then runs `docker stop`.

| Case | PID 1 | Result |
|---|---|---|
| Back, prod task definition command (`sh -c "sed … && . ./dev.sh"`), no init, before `858685ce` | `node` | The shutdown logs pause the queues and close the queue, then the process stays up: exit 137 after 121 s. Nest's re-raised SIGTERM is ignored by PID 1. |
| Same, with `--init`, before `858685ce` | `docker-init` | Exit 143 after 1 s. |
| Back, prod command, no init, after `858685ce` | `node` | Exit 0 after 1 s. |
| Back, prod command, `--init`, after `858685ce` | `docker-init` | Exit 0 after 1 s. |
| Back, image entrypoint (staging, and dev after step 0) | `node` | Exit 0 after 1 s. |
| Back, dev task definition override (`sh -c "node dist/seed.js …; node … dist/main.js"`) | `sh` | The app never gets SIGTERM: exit 137 at the stop timeout. |
| Worker, image `CMD` (`node dist/main.js`) | `node` | `Worker state changed: STOPPED`, exit 0 after 1 s. |

The prod `sed` no longer matches the new `dev.sh`; the heap comes from `NODE_MAX_OLD_SPACE_SIZE`,
which the prod task definition sets to 16384. `exitAfterClose` has three tests, each seen failing
against a broken helper.

### Dev QA on AWS (2026-11-17)

Back `d7d47018` (the 12 A9b commits cherry-picked onto `develop`) and worker `77a9f67` ran on dev
with step 0 applied (`api-task-definition-dev:2681`: no command override, `stopTimeout` 120,
`initProcessEnabled`), 2 api tasks and 2 workers. Every run used the flow "A9b QA - delayed call"
(LLM node, then `apiCaller` against a local receiver behind a Cloudflare quick tunnel). A run passes
when it has one terminal status, one callback, no `end_delivery` left, and `tokens_used` equal to
the sum of `token_transaction.used_tokens` for its `chainRootId`. Every command, write and API run
is logged in `etc/2026-11-17/a9b-qa-audit/` (local, not versioned).

| # | Result | What happened |
|---|---|---|
| T1 | Pass | Flag off, 4 runs of 60 s. The old task logged `waiting: 1` at SIGTERM, then `waiting: 0` 26 s later, closed the queue and exited 0. All 4 runs `completed`. |
| T2 | Pass | Flag off, runs of 230 s. The old task closed the queue after 100 s with `drained: false, stillRunning: 1` and exited 0. Another task wrote `error` with the restart message and sent one callback. `tokens_used` read 0, then equalled the ledger after the 5 min recompute and still did after the 35 min one. |
| T3 | Pass | Flag on, 4 B4 runs of 60 s. The old tasks logged `waiting: 0` and exited 0 about 12 s after SIGTERM. All 4 runs `completed`. |
| T4 | Measured | Flag on, 10 runs of 60 s, worker deploy. One worker held `apiCaller` activities in `DRAINING` and was killed at the 30 s stop timeout (exit 137); one run ended `error` with a heartbeat timeout. One more run ended `error` because the tunnel lost its request. 8 `completed`. Every run kept one status and one callback. A9c number: 1 of 10. |
| T5 | Pass | Flag on, 4 MCP runs of 150 s. The task that held run `04740135` got SIGTERM 19 s after the start and exited 0; another task finished the run. Each run has one `mcp_run_status` end, `tokens` equal to the ledger, no `end_delivery` and no callback. |
| T6 | Pass | 3-row batch, worker deploy while row 2 ran. Both old workers exited 0. Row 2's run ended `Error while running` (HTTP 524), rows 1 and 3 succeeded, the batch ended `error` with 3 of 3 rows processed. Each row's cost equals its ledger. |
| T7 | Pass | Reaper on, one row set to `pending` 25 h ago and one to `in_progress` 7 h ago. The 14:30 tick closed them with `RUN_NOT_STARTED_MESSAGE` and `RUN_CEILING_MESSAGE` and sent one callback each; the 14:40 tick closed nothing. The `in_progress` row's cost was recomputed to the ledger. |
| T8 | Pass | Production on 2026-11-17: `flow_execution_status` heap 105 MB (85,509 rows, 463 MB with indexes), `mcp_run_status` 264 kB, `run_seeds` empty. Worst case (105 MB + 264 kB) / 37 MB/s = about 3 s, and 12.5 s even for the full 463 MB: under 30 s, so the deploy can run at any time. Dev: the whole boot, migrations included, took 1.7 s. |

Every api task replaced on `:2681` exited 0. The two tasks replaced on `:2679` and `:2680`, which still
ran the `sh -c` override, exited 137, as the production image check above predicts. A CI deploy
during the scale-down registered `:2682` from the live revision and kept the step 0 settings.

Production holds 49 runs `in_progress` for over 7 days (43 in `flow_execution_status`, 6 in
`mcp_run_status`, none younger; read on 2026-11-17). The first reaper tick after the flag is turned
on closes them with no callback, because a run over 7 days old is closed without delivery.

What the harness needed:

- The `apiCaller` fetch gives up after 30 s by default (`DEFAULT_FETCH_TIMEOUT_MS`). The test node
  sets `requestTimeoutMs` 240000. The MCP `update_node` tool reports that field as unknown.
- A Cloudflare quick tunnel returns HTTP 524 when the first response byte takes over 100 s. Long
  calls used a receiver route that sends the headers at once and one space every 10 s.
- On dev, an api task gets SIGTERM 323 to 354 s after `stoppingAt` (ALB deregistration). ECS marks
  a deployment `COMPLETED` while old tasks still drain; `list-tasks --service-name` with
  `--desired-status STOPPED` returns none of them, `--family` does.
- With 2 api tasks, the target tracking policy scales in to 1 after about 15 min of low CPU. The
  test raised the scalable target's minimum to 2, and set it back to 1 afterwards.

### Production release (2026-11-18)

Released in the order of **Rollout**, each step run by the user with `1-prod-a9b-release.sh` and checked read-only:

| Step | Result |
|---|---|
| Worker #172 (`8c808404`) | `worker-task-definition-prod:102`, rollout `COMPLETED`. The replaced worker task stopped with exit 137 (worker `stopTimeout` default 30 s, A9c). |
| `stopTimeout` and deregistration delay | `api-task-definition-prod:853` registered with `stopTimeout` 120 s; the back workflow built `:854` from it. Deregistration delay 300 s to 180 s. |
| Back #2114 (`9a96bf3a`, image `6f7f2de0`, which also carries S8c #2117) | `:854`; `node` runs as PID 1 under the prod command `sh -c "sed … && . ./dev.sh"`. The old `:852` task stopped with exit 137 (image before A9b). `NODE_MAX_OLD_SPACE_SIZE` is 16384 in the task definition, so the heap is unchanged although the prod `sed` no longer matches `dev.sh`. |
| `initProcessEnabled` | `:855`, rollout `COMPLETED`, `node` as PID 7. The replaced `:854` task logged `Paused 10 queue instances`, `apiV2 shutdown: waiting for runs in this process { waiting: 0 }` and `closing the queue { drained: true, stillRunning: 0 }`, then stopped with exit code 0. |
| Migrations | Both new tasks logged `Nest application successfully started` and no error; migrations run at boot, so `AddRunEndDelivery1794597678794` and `SeedUnfinishedRunReaperFlag1794700000000` applied. |

`unfinished_run_reaper` stays off. Delivered in under 30 h against the 46.5/74.5/121 h estimate; the card holds 30 h.

### Found during the work, outside A9b

- **Fixed in back `0bb15208`:** `apiV2Job.processor.ts` sent the raw exception text (`error.message`)
  as the callback and status error when a run threw, as `main` does. `customerRunErrorMessage` now
  sends `Run failed` for JS programming errors, TypeORM errors, Node system errors and thrown
  non-`Error` values, and keeps the message of a plain `Error` or a NestJS exception (the product's
  own messages, such as a space's monthly limit).
- **Fixed in worker `401c494`:** the worker process did not exit after SIGTERM once it had run a flow;
  on `origin/main` too, it was still alive 120 s later. Two Redis connections held it: the Nest
  application context was never closed and the delivery Redis client had no close hook. It now
  exits in 1 s.
- A worker killed with SIGKILL fails the node whose activity was running on it, 60 s later, because
  node activities use `maximumAttempts: 1`. Not changed: whether each activity can run twice
  safely (some charge credits or call a provider) needs its own check.
- Two finishes of the same run at once can hit a duplicate key on the flow log; the claim keeps one
  status and one delivery.
- The dev worker task definition keeps the default 30 s stop timeout, so a worker that holds a long
  activity at SIGTERM is killed with exit 137 (T4 on 2026-11-17). This is A9c's scope.
- When the remote server answers with an HTML error page, the `apiCaller` error message, and so the
  run's `error_message`, carries that raw HTML (T6 row 2: Cloudflare's 524 page).
- `POST /worker/api-run-finish` does not check that `seedSnapshotId` belongs to `runId`. The route is
  behind `InternalApiGuard`.

## Files

**Back (`Flux-Prompt`).** Files are modified unless marked *create*.

- `dev.sh` (`exec node`, the database seed script under `setsid`) and `src/main.ts`
  (`exitAfterClose`); *create* `src/common/exit-after-close.ts` and `exit-after-close.spec.ts`.
- `src/temporal/temporal.service.ts` and `temporal.service.spec.ts` (no connection close on shutdown);
  `src/app-api/space_run_logs/space_run_logs.service.ts` (timers cleared in `onApplicationShutdown`)
  and *create* `space_run_logs.service.spec.ts`.
- *Create* `src/jobs/bull-shutdown.service.ts` and `bull-shutdown.service.spec.ts`, provided in
  `src/app.module.ts` (modified).
- `src/jobs/apiV2Job/apiV2Job.processor.ts` (`execute`, `reportRunFailure`, `failStalledRun`,
  `onFailed`, the active-job map, the queue property and the shutdown hooks) and
  `apiV2Job.processor.spec.ts`; `apiV2Job.queue.ts` (the job timeout, `isHeldByLiveHandler`) and
  *create* `apiV2Job.queue.spec.ts`.
- `src/app-api/flux/run-timeout.ts` and `run-timeout.spec.ts` (remove `resolveAgentJobTimeoutMs` and
  `DEFAULT_AGENT_JOB_TIMEOUT_MS` and their three tests; rewrite the two `resolveTenantRunStaleAfterMs`
  tests).
- `src/app-api/flux/flow-execution-status.service.ts` (`markInProgress`, `markCompleted`, `markError`)
  and `flow-execution-status.service.spec.ts`; `src/entities/flow_execution_status.entity.ts`
  (`endDelivery`, two indexes).
- `src/app-mcp/mcp-run-status.service.ts` (`markRunning`, `markFinished`, `markCancelled`) and
  `mcp-run-status.service.spec.ts`; `src/entities/mcp_run_status.entity.ts` (`endDelivery`, two
  indexes); `src/app-mcp/mcp-run.service.ts` (`jobId: processId`) and `mcp-run.service.spec.ts`.
- *Create* the generated migration in `src/database/migrations/` (`end_delivery`, `end_context` and the
  four partial indexes).
- `src/app-api/flux/output-delivery/output-delivery.service.ts` (`recordFailure` option) and
  `output-delivery.service.spec.ts`; `output-delivery-plan.ts` and `output-delivery-plan.spec.ts`
  (`toStoredPlan`, which removes NUL characters with `sanitizeJsonb`).
- *Create* `src/app-api/flux/run-end/run-end-delivery.service.ts`, `run-end-delivery.service.spec.ts`
  and `run-end-messages.ts`; `api-run-close-mapping.ts` and `api-run-close-mapping.spec.ts`
  (`mapRunWorkflowClose`); `run-failure-message.ts` and `run-failure-message.spec.ts`
  (`customerRunErrorMessage`); `stalled-run-cleanup.service.ts` (`StalledRunCleanupService`: the two
  recompute passes and the interrupt, shared by the stall path and the reaper).
- `src/app-api/flux/tenant-concurrency.ledger.ts` (the `releaseTenantSlot` helper);
  `src/app-api/space_run_logs/run-events.service.ts` (`finishedAt` in `readRunEnds`).
- Specs updated for the new columns or call shapes: `legacy-dispatch-charge.spec.ts`,
  `run-ledger-totals.spec.ts`, `src/app-api/space_run_logs/run-events.integration.spec.ts`, and
  *create* `run-spend-recompute.consumer.spec.ts`.
- `.env.example` (remove `AGENT_JOB_TIMEOUT_MS`).
- *Create* `src/app-api/flux/run-children.registry.ts` and `run-children.registry.spec.ts`.
- `src/app-api/app-api.module.ts` (provide and export `RunEndDeliveryService` and
  `RunChildrenRegistry`).
- `src/app-api/executions_logs/execution_logs.service.ts` (`describeRunWorkflow`,
  `interruptStalledRun`, `cancelRunWorkflow`, the `runKeyMatchExpr` option) and
  `execution_logs.service.spec.ts`.
- `src/app-api/token_transaction/run-spend-recompute.ts`, `run-spend-recompute.queue.ts` and
  `run-spend-recompute.consumer.ts` (`delayMs`, `jobId`, `resolveFromRunId`); *create*
  `run-spend-recompute.queue.spec.ts`; `run-spend-recompute.integration.spec.ts` (modified: the
  stall case).
- `src/app-api/flux/flux.service.ts` (`finishInWorker`; `onWorkflowStarted`; the nested-run condition
  in the B4 decision; the flow log `id: runId` and chat log `claimId: runId` of a `finishInWorker`
  run; `runApiV2ViaWorkflow` sets `finishApiRun` and stores the end context; `parentRunId` in `apiV2`,
  `flowCallerNode`, `libraryNode`, their four call sites and `dispatchLegacyHandler`, and the children
  registration in `apiV2`; new
  `finishApiRunFromWorkflow` and `finishOrphanedApiRun`). *Create* `api-v2-finish-orphaned.spec.ts` and
  `api-v2-nested-route.spec.ts` in `src/app-api/flux/`.
- `src/app-api/flux/run-seed.service.ts` (`endContext` in `PersistRunSeedInput`, `loadEndContext`) and
  `run-seed.service.spec.ts`; `src/entities/run_seed.entity.ts` (the `endContext` column).
- `src/temporal/worker.controller.ts` (`POST /worker/api-run-finish`) and `worker.controller.spec.ts`;
  *create* `src/shared/requests/api-run-finish.request.dto.ts` and
  `src/shared/responses/api-run-finish.response.dto.ts`.
- *Create* `src/cronJobs/unfinishedRunReaper/unfinished-run-reaper.service.ts`,
  `unfinished-run-reaper.service.spec.ts` and `unfinished-run-reaper.ts` (the
  `UNFINISHED_RUN_REAPER_FLAG` key and the default limit, as `superchat-daily-cap.ts` does);
  `src/cronJobs/cronJobs.module.ts` (register the service; add `FlowExecutionStatus` and
  `McpRunStatus` to `TypeOrmModule.forFeature`). *Create* the seed migration
  `src/database/migrations/<timestamp>-SeedUnfinishedRunReaperFlag.ts`, written by hand like
  `1790700000002-SeedSuperchatDailyCapFlag.ts`.

**Worker (`Flux-Prompt-Worker`).** Files are modified unless marked *create*.

- `src/modules/temporal/workflows/process-flow.workflow.ts` (the seed load inside the `try`, the guarded
  `finally` activities, the finish step behind `patched('a9b-finish-api-run')`, the
  `ApplicationFailure` rethrow), `process-flow.workflow.spec.ts` (the finish and rethrow tests) and
  `process-flow.continue-as-new.spec.ts` (a continue-as-new still continues).
- `src/modules/temporal/activities/activities.service.ts` and `activities.types.ts`
  (`finishApiRunActivity`); *create* `src/modules/temporal/activities/finish-api-run.activity.spec.ts`.
- `src/modules/temporal/worker.service.ts` (register `finishApiRunActivity`) and
  `src/modules/temporal/workflows/configs.ts` (its `proxyActivities` options).
- `src/modules/temporal/workflows/process-flow.replay.spec.ts`, with the two new histories in
  `src/modules/temporal/workflows/replay-histories/` (which holds three histories today); `process-batch.workflow.spec.ts` (a row whose
  `processFlow` throws a plain `Error`); `process-single-node.replay.spec.ts` (skips the
  `process-flow-*` histories).
- `src/modules/batch/batch.types.ts` (the shared `RunFinalStatus` and `RunNodeFailure` types) and
  `src/modules/temporal/activities/activities.finish-batch-row.spec.ts` (the shared finish POST).
- `src/modules/temporal/workflows/process-batch.workflow.ts` (the row's run finish when its child
  fails, behind `patched('a9b-batch-row-child-failure-finish')`), `process-batch.replay.spec.ts` and
  two histories in `replay-histories/process-batch/`; *create* `__test-stubs__/hanging-child-stub.ts`
  and `__test-stubs__/throwing-serialize-scheduler.ts`.
- `src/main.ts` (close the application once the worker stops) and
  `src/modules/delivery/delivery-dedup.service.ts` (disconnect the delivery Redis client); *create*
  `src/modules/delivery/delivery-dedup.shutdown.spec.ts`.

**Workflow repository.** *Create* `etc/<YYYY-MM-DD>/<NN>-a9b-unfinished-runs-by-age.sql` before the
flag is turned on, and `scripts/a9b-replay-histories/` (the history recorder).

**AWS** (applied by a person with write access): task definition `api-task-definition-prod`
(`stopTimeout`, `containerDefinitions[].linuxParameters.initProcessEnabled`) and target group
`enhancedai-tg-prod` (deregistration delay 180 s).
