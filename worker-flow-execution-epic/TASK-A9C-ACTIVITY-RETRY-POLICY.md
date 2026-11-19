# A9c — A worker that stops mid-activity does not fail the run

**ClickUp:** [1gahkf3b3pp](https://app.clickup.com/t/9011479430/1gahkf3b3pp)
**Parent:** Wave 5 [868m0vm9n](https://app.clickup.com/t/9011479430/868m0vm9n)
**Depends on:** A9b [868mvdm50](https://app.clickup.com/t/9011479430/868mvdm50), which found this gap and whose AWS test harness this task reuses
**Status:** in implementation; spec reviewed (EGM stages 5 to 8) and retry values fixed by the prod duration query, both on 2026-11-17
**Sizing:** Large: worker code, three task definitions, dev QA on AWS

## Terms

- **Back:** the NestJS API service (`api-task-definition-<env>`). **Worker:** the Temporal worker service (`worker-task-definition-<env>`).
- **B4:** the workflow engine that runs a whole agent as one Temporal workflow (`processFlow`), behind the `engine_in_workflow` flag. Prod runs with the flag off: the back's loop calls the worker once per node (`processSingleNode`).
- **T4:** A9b's AWS dev test 4: ten 60 s runs over two workers while one worker is deployed (`A9B-AWS-RUNBOOK.md`).
- **Cut:** a worker stop ends an activity attempt before it returns, and the attempt's result is lost.
- **`check` step:** the read-only step of the A9c release script, which prints each worker task definition's `stopTimeout` and the service's rollout state.

## Goals

1. A worker deploy (SIGTERM) does not fail a run whose activities are in the `safe`, `provider-cost` or `keyed` classes. Measured by T4 repeated with 150 s activities: 10 of 10 runs `completed`.
2. A deploy never sends a second request to a customer system: activities in the `not-safe` class keep one attempt.
3. The customer is charged once per node execution, whatever the number of attempts.

## Non-goals

| Item | Reason |
|---|---|
| Making `not-safe` activities idempotent (customer URLs, third-party writes) | The receiving system controls deduplication; the 100 s drain covers these activities when they are shorter than the grace |
| Retrying ordinary provider errors (429, 5xx) | Changes behavior outside a worker stop; a separate decision |
| An `effectStarted` marker that lets a `not-safe` activity retry when the cut came before its side effect | Needs a per-activity marker and a check on every write path; revisit if the prod measurement shows `not-safe` activities over 100 s |
| The AI Video Generator: skipped by the back's loop in a full run (prod, 2026-11-17), Luma legacy API shut down (HTTP 410 on dev), never charged | A product bug, not a retry problem: [1gahkf3bcau](https://app.clickup.com/t/9011479430/1gahkf3bcau) |
| Retrying `apiCaller` for read methods only | Decision 3 keeps one attempt for every `not-safe` activity |
| Back deploys | A9b |

## Why

A worker deploy fails node activities that are still running, and the customer gets `error` for a run that would have finished.

- T4 on AWS dev (2026-11-17): one worker held `apiCaller` activities in `DRAINING`, ECS killed it with exit 137 at 30 s, and one run of ten ended `error` with a heartbeat timeout.
- A9b on the local stack (2026-11-16): two workers, ten B4 runs, one worker stopped with SIGKILL. Two of ten runs ended `error`.

## What production shows (2026-11-17)

`etc/2026-11-18/2-prod-a9c-node-durations.sql`, run by the user on 2026-11-17 at 14:04 local time, over the last 30 days of `node_executions`. Duration is `updatedAt - createdAt`. It includes the time a node waits for a free worker slot before its activity starts, so the counts over 100 s are upper bounds: `mathFunction` shows a 173 s maximum under a 10 s start-to-close timeout. Sanity check passed: `commandTextNode` p50 is 8.5 s, not near 0.

| Node type (activity) | Class | Runs | p50 s | p95 s | Max s | Over 100 s | Over 120 s |
|---|---|---|---|---|---|---|---|
| `commandTextNode` (`textGenerator`) | `provider-cost` | 10,703 | 8.5 | 190.9 | 2,698.0 | 1,827 | 1,393 |
| `outputController` (`displayBox`) | `safe` | 1,129 | 1.1 | 16.3 | 301.0 | 10 | 9 |
| `audioReaderNode` (`audioTranscriber`) | `provider-cost` | 220 | 10.5 | 69.7 | 408.8 | 7 | 6 |
| `scripting` | `not-safe` | 20,497 | 0.6 | 3.8 | 1,427.7 | 6 | 5 |
| `webCrawling` | `provider-cost` | 133 | 3.0 | 39.0 | 653.6 | 3 | 2 |
| `mathFunction` | `safe` | 371 | 0.5 | 6.9 | 173.0 | 1 | 1 |
| `pullData` | `safe` | 36 | 0.7 | 2.5 | 1,031.3 | 1 | 1 |
| `apiCaller` | `not-safe` | 3,823 | 0.8 | 5.8 | 62.3 | 0 | 0 |
| `imageGenerator` | `provider-cost` | 297 | 11.8 | 32.3 | 72.8 | 0 | 0 |
| `imageReaderNode` (`imageReader`) | `provider-cost` | 256 | 10.2 | 19.6 | 24.8 | 0 | 0 |
| `voiceBoxNode` (`voiceGenerator`) | `provider-cost` | 51 | 3.1 | 7.0 | 22.7 | 0 | 0 |
| `webSearch` | `provider-cost` | 9 | 0.6 | 12.9 | 13.3 | 0 | 0 |
| `outputObjectNode` (`dataOutput`) | `safe` | 9,348 | 0.0 | 0.0 | 1.1 | 0 | 0 |
| `pushData`, `sqlQuerier`, `thirdPartyIntegration`, `counterNode` | `not-safe` | 67 | ≤ 5.9 | ≤ 8.2 | ≤ 8.5 | 0 | 0 |

`libraryNode` (380 over 100 s) and `fluxBox` (63) are not worker activities: a library node runs a sub-flow whose own nodes are the activities above.

What it decides:

1. **The retry is the part that matters for text generation.** 17 % of `textGenerator` runs (1,827 of 10,703) last over 100 s, so a deploy catches some of them past the grace; the drain alone does not save them.
2. **The drain alone covers almost every `not-safe` activity.** `apiCaller` never passed 62.3 s in 30 days, and `pushData`, `sqlQuerier`, `thirdPartyIntegration` and `counterNode` stay under 9 s. Only `scripting` had 6 runs of 20,497 over 100 s, which includes queue wait. The `effectStarted` marker stays a non-goal.
3. **One retry is enough.** A deploy cuts an attempt once, and the long runs are a minority. `maximumAttempts` stays 2.
4. **`displayBox` needs the heartbeat; `dataOutput` and `webSearch` do not.** `outputController` reached 301 s (10 runs over 100 s). `outputObjectNode` never passed 1.1 s and `webSearch` 13.3 s, so neither can be cut on a deploy, and a heartbeat would only add Temporal history.

## What the code does today

All references are to worker `origin/main` (`834cb32`) unless noted.

1. **No node activity retries.** `workflows/configs.ts` has 36 `proxyActivities` calls. Every node activity runs with `retry: { maximumAttempts: 1 }` (`COMMON`), except `largeMemoryActivity` (2 attempts). The charge, delivery, run, batch and schedule activities already retry 3 to 10 times.
2. **The worker gets 30 s to stop.** `temporal/worker.service.ts` sets `shutdownGraceTime` 30 s and `shutdownForceTime` 40 s. `main.ts` has no signal handler; the Temporal SDK 1.14.1 runtime shuts the worker down on SIGTERM. The Dockerfile runs `node dist/main.js` as PID 1.
3. **ECS kills the worker at 30 s.** No worker task definition sets `stopTimeout` (read 2026-11-17: `worker-task-definition-dev` revision 263, `-staging` revision 83, `-prod` revision 101), so ECS sends SIGKILL 30 s after SIGTERM, when the grace ends. Prod runs one worker task on revision 101. The worker runs on Fargate, where `stopTimeout` is at most 120 s. The dev service deploys rolling, with `minimumHealthyPercent` 100, `maximumPercent` 200 and the circuit breaker on.
4. **A deploy's cancel never becomes a retry.** At the end of the grace the SDK cancels every activity in flight. Two helpers turn that cancel into a cancel the workflow did not ask for:
   - `runCancellableNode` (`nodes/shared/run-cancellable-node.ts`, used by `textGeneratorActivity` and `apiCallerActivity`) turns any abort into a successful `CancelledNodeOutput`. The workflow settles the node as cancelled and charges the partial tokens (`settleCancelledNode` in `process-single-node.workflow.ts`).
   - `runNodeActivity` (`nodes/shared/run-node-activity.ts`, used by every node activity) re-throws an abort as is when `cancellationSignal.aborted` is set (`isRequestedCancellation`), whatever the reason. The SDK then reports the attempt as cancelled.
5. **The SDK can tell a deploy from a user cancel.** `Context.current().cancellationDetails` has `workerShutdown` and `cancelRequested` (`@temporalio/common` 1.14.1, `ActivityCancellationDetails`). During a cancel, the SDK reports an attempt that throws a `CancelledFailure` or an `AbortError` as cancelled, which never retries, and reports an attempt that throws any other error as failed, which follows the retry policy (`@temporalio/worker/lib/activity.js`, `Activity.run`).
6. **Charging.** The workflow runs `nodeCreditGateActivity`, then the node activity, then its charge activity after the final attempt returns (`process-single-node.workflow.ts`). That charge bills only what the final attempt reports. Four node activities charge inside themselves instead: `imageGenerator` (`store-and-charge.ts`), `mcp` (`mcp-billing.ts`), `webCrawling` and `webAmazon` (`charge-scrape.client.ts`). Every charge sends `execId` and `nodeId`, and back inserts with `orIgnore` on the unique index `UQ_token_transaction_exec_node_api (execId, nodeId, api)` (back migration `1792167689256-TokenTransactionUniqueExecNodeApi`). `api` comes from the node's model, and none of the four activities falls back to another model, so a second charge for the same node is ignored: when a first attempt charged before it was cut, the first charge stands.
7. **Ordinary errors are retryable.** `runNodeActivity` rethrows each error as an `ApplicationFailure` whose type is its category: `user_config`, `integration`, `provider`, `timeout`, `system`, `schema_validation`, `node_not_found` or `egress_policy` (`NodeErrorCategory` in `nodes/shared/node-error.ts`). `integration` and `timeout` are retryable, and `provider` is retryable when the error's `retryable` flag is set. With more than one attempt, an `apiCaller` 5xx would re-send the customer's request.
8. **`largeMemoryActivity`'s non-retryable list never matches.** It lists `UserConfigError` and `InvalidInputError`, but the failure type is the category string (`user_config`), and no `InvalidInputError` class exists. Today only the `nonRetryable` flag that `runNodeActivity` sets stops those retries.

## Decisions (2026-11-17, with the user)

1. A `safe` or `provider-cost` activity that a worker stop cuts runs again on another worker. The customer is charged once per node execution. The provider can bill twice for that node, and the platform absorbs the lost first call, the same absorb-the-cost stance as `CHARGING-MAP.md` §12.
2. The worker task definition sets `stopTimeout` 120 s (the Fargate maximum), and the worker sets `shutdownGraceTime` 100 s and `shutdownForceTime` 110 s.
3. `not-safe` activities keep one attempt. A deploy sends nothing twice to a customer system. A `not-safe` activity still running when the 100 s grace ends now fails its node with the user message "This step stopped because the platform restarted while it ran. Run the agent again." Before A9c, `runCancellableNode` settled it as cancelled and the run ended `completed` with the output cut short (seen locally, Verification 1).
4. `largeMemoryActivity` keeps two attempts. Amended 2026-11-17 with the user, after the consumer was traced: the "add text" step uploads a PDF and publishes to RabbitMQ queue `vector_db_queuee`, and nothing consumes that queue. Its consumer, the Python service `summarize-llm` (source not on GitHub), has desired 0 in prod since 2026-07-16 and last logged on 2025-08-11 (an `AMQPConnectionError` crash); dev and staging have no such service, and Amazon MQ reports `ConsumerCount` 0 for 150 days in prod and 7 days in dev and staging. So a second publish creates no entry today, and a deterministic upload key would change nothing: it leaves A9c. The real retry hazard is the delete step, which runs first: a second attempt looked up a file the first attempt had already deleted and failed the node. On a retry attempt a missing file now counts as already deleted; on the first attempt it fails as before. The dead consumer is a separate production bug.
5. The video node's problems are out of A9c (see Non-goals).
6. Drain and retry both ship in A9c, not in two phases (review C6).
7. A retry fires only on the new `WorkerShutdown` failure and on a heartbeat timeout. Every node error category is non-retryable, and a start-to-close timeout does not trigger a retry (review C1).
8. The retry policy covers the long `safe` proxies. The values are fixed by the prod duration query (review C4; "What production shows"). Amended during implementation and review: the 1-minute group (with `sqlQuerier` in it) and `mathFunction` (10 s) keep one attempt, because no retry trigger can reach them: they end inside the 100 s grace, and they have no heartbeat (see "Retry policy per proxy group").
9. `completionActivity` keeps one attempt: it streams to the client, and Temporal sets a retry policy per proxy, not per call (review C8).
10. One guard on `cancellationDetails` decides a cancel; a user cancel (`cancelRequested`) wins over a worker shutdown (review C5).

## Activity classes

Each proxy in `configs.ts` belongs to one class.

| Class | Activities | Why |
|---|---|---|
| `safe` | `mathFunction`, `pullData`, `dataOutput` (idempotent `persistRunNodeOutcome`; delivery runs in its own workflow), `displayBox`, `generateFile`, `reportBuilder` (an orphan file at worst), `getNodeInfo`, `getInfoInDatabase`, `nodeCreditGate`, `validateModelAccess`, `validateApiAccess`, `validateLargeMemoryAccess`, `notifyStatus` (a duplicate socket event), `persistCancelledNode`, `nodeExecutionError` (no-op), `generateExecutionLogs` (an extra info row at worst) | Nothing the customer sees twice |
| `provider-cost` | `textGenerator`, `imageReader`, `audioTranscriber`, `voiceGenerator`, `webSearch`, `secApiNode`, `usCensusNode`, `imageGenerator`, `webCrawling`, `webAmazon`, `aiVideoGenerator` | The provider bills again; the customer is charged once (item 6). `imageGenerator` and `aiVideoGenerator` can leave an orphan stored file |
| `keyed` | `chargeTokens`, `chargeApiCall`, `chargeLargeMemoryUsage`, `chargeVoice`, `chargeTranscription`, `largeMemory` (after decision 4) | `UQ_token_transaction_exec_node_api`; `largeMemory`: its delete tolerates a missing file on a retry attempt, and its add publishes to a queue nothing consumes (decision 4) |
| `not-safe` | `apiCaller` (any method to any customer URL), `thirdPartyIntegration` (Slack, Notion, HubSpot, Stripe, Zapier, WordPress, ClickUp writes), `mcp` (any `tools/call`), `pushData` (Sheets rows, Drive and OneDrive files), `fileSave` (Drive upload), `counter` (atomic increment), `sqlQuerier` (customer SQL, can write), `scripting` (customer code can call out), `completion` (streams to the client) | A second attempt repeats an effect the customer sees |

## Design

### The `WorkerShutdown` failure

One helper, `failIfWorkerShutdown(err)` in `nodes/shared/`, reads `Context.current().cancellationDetails` when an attempt sees an abort:

1. When `cancelRequested` is set, the cancel came from the workflow (a user cancel). The helper returns, and today's behavior stays: `runCancellableNode` returns `CancelledNodeOutput`, and `runNodeActivity` re-throws the abort.
2. Otherwise, when `workerShutdown` is set, the helper throws `ApplicationFailure.retryable("Worker shutting down", "WorkerShutdown")`. The SDK reports the attempt as failed, and the retry policy decides.

Both helpers call it before their own abort handling: `runCancellableNode` in the catch that sets `interrupted`, and `runNodeActivity` before `isRequestedCancellation`, for any error, so a provider SDK that wraps the abort in its own error also fails as `WorkerShutdown`. `runNodeActivity` passes a `WorkerShutdown` failure through without wrapping it in a node error. Done 2026-11-17: `nodes/shared/worker-shutdown.ts`, worker `e8c4f7d`, with three negative controls.

An activity that ignores the abort signal keeps running until the force time (110 s), then the worker exits without reporting it. Temporal detects that loss through the heartbeat timeout.

### Retry policy per proxy group

| Proxy group | Class | `maximumAttempts` | Retry triggers |
|---|---|---|---|
| Long node proxies (`textGenerator`, `imageReader`, `audioTranscriber`, `voiceGenerator`, `webSearch`, `secApiNode`, `usCensusNode`, `imageGenerator`, `webCrawling`, `webAmazon`, `aiVideoGenerator`, `pullData`, `dataOutput`, `displayBox`) | `provider-cost`, `safe` | 2 | `WorkerShutdown`, heartbeat timeout |
| `largeMemory` | `keyed` | 2 | `WorkerShutdown`, heartbeat timeout |
| `mathFunction` (10 s) and the 1-minute group (charges, lookups, notifications, `reportBuilder`, `sqlQuerier`) | `safe`, `keyed`, `not-safe` | 1 | none: no trigger can reach them |
| `apiCaller`, `thirdPartyIntegration`, `mcp`, `pushData`, `fileSave`, `counter`, `scripting`, `completion` | `not-safe` | 1 | none |

Every retried proxy sets:

- `initialInterval` 1 s and `backoffCoefficient` 2. One retry only: a deploy cuts an attempt once, and a crash loop stops after the second attempt instead of using up the run.
- `nonRetryableErrorTypes`: every `NodeErrorCategory`, imported from a constant array in `node-error.ts` so a new category cannot be missed, plus `TemporalTimeout:StartToClose`. The Temporal server names a timeout failure `TemporalTimeout:<TimeoutType>` (Go server, `common/retrypolicy`), and no SDK guide documents listing one. Proven on 2026-11-17 by `retry-trigger.temporal.spec.ts` (worker `59d104b`) on the Temporal test server: with the entry, a start-to-close timeout runs once; a heartbeat timeout and a `WorkerShutdown` failure run twice; a retryable `provider` error runs once. Negative control: without the entry, the start-to-close case ran twice.
- The 1-minute group keeps one attempt. Its 60 s ceiling ends inside the 100 s grace, so a deploy never fails it with `WorkerShutdown`, and it has no heartbeat. A retry policy there would never fire on a worker loss. Most of its errors do not pass through `runNodeActivity`, so the SDK names them after the JavaScript error (`Error`, `AxiosError`), and a second attempt would only re-run an ordinary charge or lookup error. No wrapper is needed.

A heartbeat timeout is a valid trigger even for a provider that hangs: the keep-alive heartbeat (`withKeepAliveHeartbeat`, every 15 s) beats while the worker process lives, whatever the provider does, so the timeout fires only when the worker is gone.

### Heartbeats

| Activity | `startToCloseTimeout` | `heartbeatTimeout` today | Change |
|---|---|---|---|
| `displayBox` | 12 min | none | keep-alive, 30 s (prod max 301 s) |
| `dataOutput` | 2 min | none | none: prod max 1.1 s |
| `webSearch` | 2 min | none | none: prod max 13.3 s |
| `textGenerator` | 30 min | 2 min | none |
| `audioTranscriber` | 15 min | 3 min | none |
| `voiceGenerator`, `largeMemory` | 10 min, 5 min | 1 min | none |
| `imageReader`, `imageGenerator`, `aiVideoGenerator`, `pullData`, `webCrawling`, `webAmazon`, `secApiNode`, `usCensusNode` | 2 to 10 min | 30 s | none |

The 1-minute group and `mathFunction` (10 s) get no heartbeat: they end within the 100 s grace on a deploy. After a crash (SIGKILL) they are not retried, because a start-to-close timeout is not a trigger (Risks). Done 2026-11-17: `displayBox` beats through `withKeepAliveHeartbeat` with a 30 s timeout, worker `80d743e`; `heartbeat-coverage.spec.ts` failed with the wrapper removed.

### Charging

A retried attempt charges as today: the workflow's charge activity runs once, after the final attempt, and bills what that attempt reports. For the four activities that charge inside themselves, the unique index keeps the first charge and ignores the second.

### Replay safety

A changed retry policy does not change the activity type the workflow schedules, so workflows in flight replay unchanged and need no `patched()`. Verification 8 proves it by replaying the `processFlow` and `processSingleNode` histories on disk against the new code.

## Alternatives considered

| Option | Why not |
|---|---|
| Drain only: 120 s `stopTimeout`, no retry | Fixes T4 and the local test, but every activity over 100 s still fails on a deploy; textGenerator runs up to 30 min |
| Retry only, keep the 30 s grace | Every deploy cuts every activity over 30 s and pays the provider twice; the drain avoids most of those retries |
| Retry long proxies only | The user chose to cover short proxies too (decision 8) |
| Re-dispatch the node from the workflow (`processSingleNode` catches the failure and schedules the activity again) | The same effect as a retry policy, written by hand in workflow code, with its own replay risk |
| A separate task queue for long activities, on workers that rarely deploy | A second worker service to build, deploy and monitor; activities still get cut when that service deploys |
| ECS on EC2, where `stopTimeout` has no 120 s cap | A new launch type and capacity to manage, for activities that the retry already covers |
| Blue/green deploys, or waiting for the queue to empty before SIGTERM | The old worker keeps polling until it stops, so the queue never empties under load; blue/green on ECS needs CodeDeploy and still ends with a stop |

## Risks and mitigations

| Risk | Mitigation or acceptance |
|---|---|
| The provider bills twice for a cut `provider-cost` activity | Accepted (decision 1). Bounded by one retry per cut; only runs in flight past the 100 s grace at deploy time pay twice, and 17 % of `textGenerator` runs last over 100 s |
| A deploy takes up to 120 s longer, per old worker task | Accepted. Rolling deploys start the new task first (`minimumHealthyPercent` 100), so capacity does not drop; the old tasks drain in parallel |
| After a crash, a retry waits for the heartbeat timeout (30 s to 3 min) | Accepted. A deploy uses the faster `WorkerShutdown` path |
| A crash during a short activity without a heartbeat is not retried | Accepted. Deploys are covered by the drain; adding a sub-10 s heartbeat to every short activity costs more Temporal history than the crashes it saves |
| Orphan files from `imageGenerator` and `aiVideoGenerator` second attempts | Accepted. They hold no customer data beyond the generated media |
| A task definition changes between this read (2026-11-17) and the release | The `check` step reads them again before any write |
| The deploy that ships A9c is not protected | Accepted. The tasks it replaces run the old revision and still stop at 30 s |
| A crash loop | One retry only; the second failure ends the node as today |
| The worker process stays up after the Temporal worker reaches `STOPPED` (Redis and Temporal connections stay open, seen locally on both builds; `main.ts` is unchanged) | Out of A9c's diff. With `stopTimeout` 120 s, ECS still sends SIGKILL at 120 s, after the drain, so no activity is lost; the exit code stays 137. Reported to the user as a separate candidate fix, the same pattern A9b fixed in the back |
| `TemporalTimeout:StartToClose` stops working after a Temporal server upgrade | `retry-trigger.temporal.spec.ts` runs against the test server of the pinned SDK; re-run it when the SDK or server version changes |

## Requirements

| ID | Requirement |
|---|---|
| A9C-01 | WHEN a worker receives SIGTERM THEN it SHALL let in-flight activities run for up to 100 s (`shutdownGraceTime`), SHALL force its stop at 110 s (`shutdownForceTime`), and ECS SHALL NOT send SIGKILL before 120 s (`stopTimeout`) |
| A9C-02 | WHEN the grace ends with an activity still running and no user cancel requested THEN the attempt SHALL fail with a retryable `WorkerShutdown` failure, and no node SHALL be settled as cancelled |
| A9C-03 | WHEN a user cancel and a worker shutdown both reach an attempt THEN the user cancel SHALL win: the node ends cancelled with its partial charge, as today |
| A9C-04 | WHEN an attempt of a retried proxy fails with `WorkerShutdown` or a heartbeat timeout THEN Temporal SHALL run one more attempt, and the node SHALL be charged once |
| A9C-05 | WHEN an attempt fails with a node error of any category or a start-to-close timeout THEN Temporal SHALL NOT retry it, and the 1-minute group SHALL keep one attempt |
| A9C-06 | WHEN an activity is in the `not-safe` class THEN its proxy SHALL have one attempt |
| A9C-07 | WHEN `displayBox` runs THEN it SHALL heartbeat, with a 30 s heartbeat timeout |
| A9C-08 | WHEN a retry attempt of `largeMemoryActivity` finds no file to delete THEN the node SHALL go on, WHEN the first attempt finds no such file THEN the node SHALL fail as today, and its non-retryable list SHALL name the category strings |

## Verification

Local steps run on the two-worker stack from A9b; AWS steps reuse A9b's harness (`wait-rollout.sh`, `deploy-test.sh`).

1. Negative control, before the change: two workers, ten B4 runs with a 150 s text generation, SIGTERM one worker mid-batch. Record the runs that end `error` or settle as cancelled. (A9C-01, A9C-02, A9C-04) Done 2026-11-17 locally on origin/main `834cb32` (audit `etc/2026-11-17/a9c-local-qa/`, a 146–172 s `commandTextNode` on `ministral-8b`): the cut runs did not end `error`. Each cut generation stopped at the 30 s grace, the node was marked cancelled after 1,722–3,233 of 16,500 tokens, and the run still ended `completed` with callback `success: true`: 6 of 6 cut runs were truncated and reported as successes.
2. The same test after the change: every run `completed`, one callback each, one `token_transaction` row per node. (A9C-01, A9C-02, A9C-04) Done 2026-11-17 locally on worker `0a92209`: 10 of 10 `completed`, one callback each, one `token_transaction` row per api per node. The 5 runs on the stopped worker failed attempt 1 with `WorkerShutdown` after a 100.1 s drain and finished the full output on the other worker.
3. SIGKILL one worker during a 150 s text generation: the attempt runs again after the 2-minute heartbeat timeout, and the run ends `completed`. (A9C-04) Done 2026-11-17 locally: 3 of 3 `completed`; attempt 2 started about 119 s after the kill with last failure `TIMEOUT_TYPE_HEARTBEAT`.
4. A user cancel during a text generation, with a SIGTERM in the same grace: the node ends cancelled with its partial charge. (A9C-03) Done 2026-11-17 locally: the run ended cancelled with a partial charge of 1,128 output tokens and no second attempt; the worker stopped 11 s after SIGTERM.
5. An `imageGenerator` first attempt that charges, then is cut: one `token_transaction` row for the node. (A9C-04)
6. A retryable `ProviderError` and an `apiCaller` 5xx each fail the node on the first attempt. (A9C-05, A9C-06) Policy done 2026-11-17: `configs.retry-policy.spec.ts`, worker `80d743e`, checks 16 retried proxies and 9 single-attempt ones; swapping the `textGenerator` and `apiCaller` policies failed 2 tests. The retryable `provider` case is in `retry-trigger.temporal.spec.ts`.
7. A Temporal test environment case where an attempt exceeds its start-to-close timeout: no second attempt. (A9C-05) Done 2026-11-17: `retry-trigger.temporal.spec.ts`, worker `59d104b`.
8. Replay every `processFlow` and `processSingleNode` history on disk against the new code with no nondeterminism error. (Replay safety) Done 2026-11-17 on worker `17040e1`: the three single-node histories (two with `textGenerator`, whose retry policy changed) and the two batch histories replay; no `process-flow-*.json` history is on disk yet.
9. A `largeMemory` delete whose file is gone: attempt 2 goes on, attempt 1 fails, another delete error fails on attempt 2. (A9C-08) Done 2026-11-17: `large-memory.service.spec.ts`, worker `0a92209`; dropping the retry guard failed the attempt-2 test, and tolerating every attempt failed the attempt-1 test.
10. `displayBox` heartbeats: a test reads the heartbeat during a long attempt. (A9C-07) Static check done 2026-11-17: `heartbeat-coverage.spec.ts` fails when a proxy declares `heartbeatTimeout` and the activity does not beat.
11. AWS dev: repeat T4 with 150 s activities and a worker deploy; 10 of 10 runs `completed`. (A9C-01, A9C-02, A9C-04) Done 2026-11-18 on worker `develop` `ae95c4b` (revision 265, `stopTimeout` 120; audit `etc/2026-11-18/a9c-t4-audit/`). T4: 10 of 10 `completed`, one charge per api per node, old task exit code 0. Dev runs one api-v2 run at a time today, so the old worker held no activity at SIGTERM and drained in 6 ms: T4 proves a clean deploy, not the cut. T4b (one more forced deploy, approved by the user): one run with a 290 s generation started on the old task; the drain lasted 100.0 s, the attempt failed as `WorkerShutdown` (`nonRetryable: false`), the container exited with code 0 at 112.4 s, attempt 2 on the new task wrote the full output (73,267 characters, the token cap), the run ended `completed` with one `token_transaction` row per api. The cut attempt's provider spend is not billed (decision 1).

## Rollout

1. Run the A9c release script's `check` step in each environment. It prints `stopTimeout` and the rollout state of `worker-task-definition-<env>`.
2. Register a `worker-task-definition-<env>` revision from the live one with `stopTimeout` 120 on `worker-container-<env>` and nothing else changed, and point the service at it (one rolling deploy, same image). Both deploy paths then carry it: the worker's deploy workflows (`cicd_dev.yml`, `cicd_staging.yml`, `cicd_prod.yml`) start from the family's latest revision, and `scripts/deploy-direct` starts from the running one (`lib/ecs.sh` `render_taskdef`), so registering without the rollout would let a direct deploy drop the 120 s. The script refuses during a rollout and when the family's latest revision is not the live one. Old code with a 30 s grace still exits at 30 s.
3. Deploy the worker with the A9c code. A deploy takes up to 120 s longer than today. The tasks it replaces run the old revision and stop at 30 s, so the first protected deploy is the next one.
4. Order: dev, staging, prod. The back does not change.

The user runs the staging and prod steps in their own terminal. Rollback: redeploy the previous worker image. The 120 s `stopTimeout` can stay, because the old code exits at 30 s.

## Done when

1. Every requirement A9C-01 to A9C-08 has a test that was seen failing with the change reverted.
2. Verification steps 1 to 11 pass, with the negative control recorded.
3. `stopTimeout` is 120 on the worker task definitions in dev, staging and prod.
4. The classification table above records each `not-safe` activity's reason.
5. Reviews (`/simplify`, `/code-review`, `/security-review`) are recorded in this spec.

## Estimate

10 / 14 / 24 h of Claude-assisted work (optimistic / likely / pessimistic). The card holds the maximum, 24 h.

The method converts a bottom-up estimate with the ratio between the card estimate and the time measured in Claude Code sessions on comparable Wave 5 tasks. "Measured" is active session time: gaps under 10 minutes between events, Claude's and the user's together (`~/claude-usage-analysis/semanal.js 12 --ate=2026-11-17`, summed per task over 12 weeks).

| Task | Card estimate | Measured | Ratio |
|---|---|---|---|
| A9b (868mvdm50), spec to dev QA | 80 h (likely 74.5 h) | 21.0 h, 6 active days, US$ 237 | 0.26–0.28 |
| A13 (868mn64j4) | 32 h | 15.0 h | 0.47 |
| A11 (868mn64he) | 24 h | 24.7 h | 1.03 |

Bottom-up, after the review widened the scope: 34 / 50 / 75 h.

| Part | Hours |
|---|---|
| `WorkerShutdown` helper in both node helpers, retry policy per proxy group | 10 / 14 / 20 |
| Heartbeats for `displayBox`, `dataOutput`, `webSearch` | 1 / 2 / 3 |
| `largeMemory` retry-tolerant delete and non-retryable list (the deterministic key left A9c, decision 4) | 2 / 3 / 5 |
| Tests with negative controls (Verification 3 to 10), including the start-to-close and replay cases | 10 / 15 / 22 |
| Prod duration query and fixing the values | 1 / 1 / 2 |
| Task definition script, local two-worker tests (150 s, SIGKILL), AWS dev QA | 7 / 10 / 15 |
| Reviews and fixes | 3 / 5 / 8 |

- Likely: 50 h × 0.28 (A9b, the closest task: same worker area and harness) = 14 h.
- Optimistic: 34 h × 0.28 ≈ 10 h.
- Pessimistic: 50 h × 0.47 (the median ratio) ≈ 24 h. A11's ratio (1.03) is the outlier risk; its scope grew during the task.
- Cost: A9b ran at about US$ 11 per measured hour, so about US$ 155 likely (US$ 110 to 265).

The measured time leaves out meetings, PR review by other people and waiting for deploys.

## Files

Worker:
- `src/modules/temporal/workflows/configs.ts`, `src/modules/temporal/workflows/retry-policies.ts`: retry policy per proxy group, non-retryable lists
- `src/modules/nodes/shared/node-error.ts`: `NODE_ERROR_CATEGORIES`, the one list the error type and the retry policy read
- `src/modules/temporal/worker.service.ts`, `src/modules/temporal/temporal.constants.ts`: grace 100 s, force 110 s (worker `17040e1`; `temporal.constants.spec.ts` keeps grace < force < `stopTimeout` ≤ 120 s and failed with force at 130 s)
- `src/modules/nodes/shared/run-cancellable-node.ts`, `src/modules/nodes/shared/run-node-activity.ts`: call the `WorkerShutdown` helper
- `src/modules/nodes/shared/` (new helper file): `failIfWorkerShutdown`
- `src/modules/temporal/activities/activities.service.ts`: keep-alive heartbeat for `displayBox`
- `src/modules/nodes/large-memory/large-memory.service.ts`, `src/modules/vector/vector.service.ts`, `src/modules/vector/namespace-file-not-found.error.ts`, `src/modules/nodes/shared/activity-attempt.ts`: the delete tolerates a missing file on a retry attempt (worker `0a92209`)
- Unchanged: `src/modules/temporal/workflows/process-single-node.workflow.ts` (the charge order stays) and `src/modules/nodes/shared/is-abort-error.ts`

Infra: `worker-task-definition-{dev,staging,prod}` (`stopTimeout` 120), through `etc/2026-11-17/6-a9c-worker-stop-timeout.sh <env> check|apply|wait`, a dry run unless `--apply`, with a typed env name. Dry run on dev, 2026-11-17: revision 263, `stopTimeout` unset → 120, nothing else differs; the diff guard refused an image change and a second container's `stopTimeout` in a negative control.

Query: `etc/2026-11-18/2-prod-a9c-node-durations.sql` (read-only, dev-tested on 2026-11-17).

## Review record

EGM review, stages 5 to 8, on 2026-11-17: 3 Blockers, 8 Majors, 6 Nits (C1 to C17); the user decided C1, C4, C5, C6, C8 and C12, recorded above as decisions 6 to 10 and 4. The reports are in the A9c session's job folder (`a9c-egm/`).

Implementation reviews on the worker branch, 2026-11-17:

1. `/simplify` (4 reviewers): 8 fixes in worker `2bb8e73`. The Temporal retry-trigger spec now runs the real `RETRY_ON_WORKER_LOSS` (moved to `workflows/retry-policies.ts`) instead of a copy that had lost `egress_policy`, and bundles its stub once. One `tryGetActivityContext()` replaces four private `Context.current()` copies. `sqlQuerier` is back in the 1-minute group, whose timeout is the constant `SINGLE_ATTEMPT_GROUP_TIMEOUT_MS` the drain spec reads. Negative controls: removing the start-to-close entry from the real policy failed 17 tests; a 120 s group timeout failed the drain spec. Skipped: grouping identical proxy blocks (the file's style is one block per activity), a single throw site for the shutdown failure (no gain), reverting Biome formatting in two specs (the files would fail Biome).
2. `/code-review` (high), 10 findings. Fixed in worker `3ff9627`: the `WorkerShutdown` failure carries a node error detail with a clear user message (the final failure showed the generic internal error); `mathFunction` keeps one attempt (dead retry); a spec fails when a proxy leaves its attempts unnamed and would fall back to unlimited retries. Accepted, with the reason:
   - A retried `textGenerator` opens a second chat stream: the chat shows the cut partial message, then the full answer. Before A9c it showed only the cut message as if complete.
   - A retry has no schedule-to-start limit: when dev and staging stop at 24:00, a cut attempt runs again at 07:00. Prod keeps a worker during a rolling deploy, and the workflow itself also waits for a worker.
   - An error that lands in the 10 s between the grace and the force stop becomes `WorkerShutdown` even when it is not caused by the abort, which includes the delivery activities. The window is narrow, both delivery activities already retry ordinary errors, and the design accepts it so that a provider error wrapping the abort still retries.
   - A Large Memory attempt 1 cut before its delete makes attempt 2 tolerate a delete target that never existed. Rare; A9C-08 now says "a retry attempt finds no file to delete".
   - The in-activity charges (`imageGenerator`, `webCrawling`, `webAmazon`) rely on back's claim insert with `orIgnore` on `UQ_token_transaction_exec_node_api`, which back's `user-product-concurrent-charges.integration.spec.ts` covers on a real database (a retry returns `charged: false`); attempt 2 sends the same `execId`, `nodeId` and model. This covers Verification 5.
   - Rejected: `largeMemory` losing retries on transient errors (no error on its path was retryable before A9c either), `unknown` in `isWorkerShutdownFailure` (same signature as `isAbortError` and `extractNodeError`).
3. `/security-review`: no findings. A retry re-runs the pod and namespace access checks; the new failure detail and heartbeat carry only fixed strings and ids; only the SDK's own shutdown signal triggers the path.
