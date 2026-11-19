# B7b — Batch rows keep chat memory, a retried prepare writes once, and workflow runs keep their log steps

**Goal:** a batch row run through `processFlow` computes and records the same thing as the same row
run through the API loop, a retried step writes once, and every run whose nodes ran in the worker
keeps its steps on the Logs page.

**Depends on:** A13 (868mn64j4), which added the batch-row finish step and the shared end of run.
**Blocks:** nothing. **Added 2026-11-10** from the A13 batch work. **Specified 2026-11-18** against
back `origin/main` `4e759cf7` and worker `origin/main`; items 2 and 3 corrected, see
[What changed in this revision](#what-changed-in-this-revision). ClickUp:
[868muzee4](https://app.clickup.com/t/868muzee4). Branches: back `fix/868muzee4`, worker
`fix/868muzee4`.

## Why

A13 restored the batch rows' Data Output value, callback and run logs. On the way it found three
gaps it did not cause, on the paths B7 and B4 opened. Each one was read again on 2026-11-18:

1. **Chat memory.** `prepareWorkflowSeedForBatchRow` (`flux.service.ts:974`) builds the seed from
   the stored graph and the row's inputs only. `apiV2` (`flux.service.ts:4572-4741`) first clears
   the `fluxObject` nodes marked clear-on-execution, then loads each chat node's stored history from
   `session_state` into `data.entries`, sets `selectedChat`, and keeps `chat: true` on the first chat
   node only. A batch row skips all of it, so a chat-memory node answers without its history.
   `closeWorkerRun` already writes the turn back through `recordChatLog`, so the history grows but a
   batch row never reads it. With two chat nodes, every one of them keeps `chat: true` and receives
   the turn.
2. **Retried `prepare`.** `prepareBatchRowRunActivity` retries up to three times with a one-minute
   timeout (worker `workflows/configs.ts`). `BatchRunPreparationService.prepare` draws a new
   `runId = uuid()` on every call, so a retry does not duplicate rows inside one run, as the first
   version of this spec said. When the first call did its work but its answer was lost, the retry
   leaves an orphan run: a `run_seeds` row and one Variable Input `node_executions` row per node,
   keyed by a `runId` that never runs.
3. **Log steps.** A run whose nodes ran in the worker has a run-log collector with no node entries:
   the collector gets nodes only through `startNode` in the inline loop. `RunEventsService.ingest`
   rebuilds the run log from the worker's events and writes it on every batch, whatever the flag
   says. At the end of the run, `persistFinishedRun` writes the collector document in `off` and
   `shadow` mode, and `flushNow` replaces the whole row, so the Logs page shows `nodes: []`. This
   hits two callers, not only the first one:
   - `apiV2` routed to the workflow (`runApiV2ViaWorkflow`), which needs `engine_in_workflow` on.
   - `closeWorkerRun`, the end shared by batch rows, scheduled runs and API runs finished in the
     worker. `openSpaceRunLog` creates the worker event source only when the mode is not `off`.

   Dev has `run_log_from_events` on (read 2026-11-18), so dev does not show the gap. The production
   value was not read; batch rows run in the worker in production, so they lose their steps there
   if the flag is off.

## Requirements

| ID | Requirement | Acceptance |
|---|---|---|
| B7B-R1 | A batch row prepares its session nodes through the same code `apiV2` uses, in a chat session of its own. | A chat `fluxObject` in a batch row gets `selectedChat` set to the row's `runId`, reads the history of that session (empty when the row starts), never reads the canvas `default` session or another row's turns, and records its turn in its own session. Only the first chat node keeps `chat: true`, and clear-on-execution clears the node and its session before the row runs. `apiV2` calls the same method and its behaviour does not change. |
| B7B-R2 | A retried `prepare` for one batch row writes one run. | Every attempt of one `prepareBatchRowRunActivity` call uses the same `runId`, chosen by the workflow. Two calls with that `runId` leave one Variable Input row per node. A call without a `runId` (a workflow started before the worker deploy) still works. |
| B7B-R3 | A run whose nodes ran in the worker writes its final run log from events in every mode. | In `off`, `shadow` and `events` mode, the final run log of a workflow-routed `apiV2` run and of a `closeWorkerRun` run keeps its node entries. The collector document is written only when the rebuild from events returns nothing or throws. Inline `apiV2` runs keep today's behaviour in every mode. |

## Design

### B7B-R1: one session preparation

1. Move the `apiV2` block that runs from `fluxObjectsToClear` to the end of the `sessionIdForChat`
   branch, including the `nodesBox` session selection, into one `FluxService` method,
   `prepareRunSessionNodes({ flowId, nodes, sessionId, ownerUserId, flowVersionHistoryId })`. It
   returns the prepared nodes. Move the code as it is; do not rewrite it.
2. `apiV2` calls it with the values it passes today: `sessionId`, `user?.id` and its
   `flowVersionHistoryId`.
3. `prepareWorkflowSeedForBatchRow` calls it before `applyVariableInputsToSeedNodes`, the same order
   as `apiV2`. Pass `sessionId: undefined` and `chatSessionFallback: runId`: where `apiV2` falls
   back to `default` when a chat node exists, a batch row falls back to its own `runId`, so each row
   starts with empty chat memory and rows that run together never share it (decision 2026-11-18,
   see [Reviews](#reviews)). `finishBatchRowRun` records the turn under the seed's `selectedChat`,
   the row's session. The worker child keeps `sessionId: 'default'`: the AI Text memory and the
   Counter read that key, and moving them is out of scope. Pass the flow owner as `ownerUserId`, the user the
   row runs and records the chat turn as. Pass `flowService.resolveExecutionHistoryId(getFlow)`, the
   value `finishBatchRowRun` resolves for the same row.

### B7B-R2: the workflow owns the row's run id

1. Worker: `processRow` in `process-batch.workflow.ts` draws `runId` with `uuid4()` from
   `@temporalio/workflow` and passes it in the `prepareBatchRowRunActivity` input. `uuid4()` is
   seeded by the workflow, so it replays to the same value and emits no command. Temporal does not
   compare activity input on replay, so the recorded histories in
   `workflows/replay-histories/process-batch/` must still replay.
2. Back: `PrepareBatchRowRunInput` gains an optional `runId`. `prepare` uses it and falls back to
   `uuid()` when it is missing.
3. Back: `seedVarInputNodeExecutions` gives each row `id = execId = uuidv5(`${runId}:${nodeId}`,
   namespace)` and inserts with `ON CONFLICT (id) DO NOTHING`. The primary key makes the second
   insert a no-op, atomically, without a read. A second `run_seeds` row for the same `runId` is
   harmless: `RunSeedService` reads the latest one, and the workflow uses the `seedSnapshotId` the
   successful attempt returned.
4. Deploy order: back first, then worker. The back endpoint takes a plain interface, not a validated
   DTO, so an older back ignores the new field and an older worker sends none.

### B7B-R3: events are the source for worker runs

1. `openSpaceRunLog` gives a run opened with `events: 'worker'` the `events` mode instead of the
   flag's mode. Its collector flush then schedules a rebuild from events from the start, its event
   source is the worker's, and `persistFinishedRun` folds the events at the end, writing the collector
   document only when the rebuild returns `null` or throws. `closeWorkerRun` needs no change.
2. `apiV2` opens its collector before it knows the route. When it routes the run to the workflow and a
   run log is open, it switches its run-log mode to `events` and its event source to the collector's
   recorder or, without one, `runEventsService.workerRunEvents(runLogProcessId)`. The success and the
   error path read the same two variables.
3. `persistFinishedRun` cancels the collector's queued write before it folds the events. The write
   that `apiV2` queued at open holds a reference to the root document, which `finalize` fills in, and
   would otherwise land after the final write with `nodes: []`.
4. The first version threaded a `nodesFromEvents` flag through `persistFinishedRun`; the `/simplify`
   review replaced it with the mode, which removes the flag and a helper.

## Out of scope

- **Scheduled runs on Temporal Schedules.** `resolveScheduledRunActivity` (worker) builds the seed
  from the database graph and skips the same session preparation. That path belongs to E4b
  ([TASK-E4B-SCHEDULED-RUN-FINISH.md](TASK-E4B-SCHEDULED-RUN-FINISH.md)) or its own follow-up.
- The live Logs-page entry while a run is in progress: the collector's flush during the run can
  still write a document without nodes before the final write.
- The budget and spend stops, which `processFlow` does not have yet.

## Tasks

| ID | Task | Repo | Requirement | Done when |
|---|---|---|---|---|
| T1 | Extract `prepareRunSessionNodes` from `apiV2`; no behaviour change. | back | R1 | Existing `apiV2` chat and clear-on-execution specs pass unchanged. |
| T2 | Call it from `prepareWorkflowSeedForBatchRow`. | back | R1 | A spec persists a batch-row seed whose chat node carries the stored history; seen failing with the call removed. |
| T3 | Optional `runId` in `prepare`; deterministic Variable Input ids with `ON CONFLICT`. | back | R2 | A spec calls `prepare` twice with one `runId` and finds one row per node; seen failing with `uuid()` restored. |
| T4 | `processRow` passes a workflow `uuid4()` as `runId`. | worker | R2 | A workflow spec sees the same `runId` on a retried attempt; the process-batch replay histories pass. |
| T5 | A worker run's log opens in `events` mode; `persistFinishedRun` cancels the queued collector write. | back | R3 | A batch-row finish in `off` and `shadow` mode folds the events and writes no collector log; seen failing without the mode. |
| T6 | A workflow-routed `apiV2` switches its run log to `events` mode. | back | R3 | The routed run folds its events in `off` and `shadow` mode and leaves no queued write behind; seen failing without the switch and without the cancel. |
| T7 | Reviews: `/simplify`, `/code-review`, `/security-review`. | both | all | Findings fixed or answered in this file. |
| T8 | Dev QA after the dev merge, with the user's go-ahead. | both | all | A batch on a chat-memory flow answers with history; the Logs page shows the rows' steps. |

T1 and T2 run first, T3 and T4 next, T5 and T6 after. Every new test is run against the code without
its fix first, and the failure seen is recorded below.

## Verification

- Negative control per requirement, seen failing on the current code: a chat-memory node in a batch
  row has no history in its seed; `prepare` called twice with one `runId` leaves two Variable Input
  rows; a worker-run finish in `off` mode overwrites the run log with `nodes: []`.
- Parity: the same row through the API loop and through the batch gives the same seed for the chat
  node (`entries`, `selectedChat`, `chat`).
- Jest runs scoped to the changed specs, capped at 4 GB and one worker. The integration specs use the
  local Postgres from `docker/devdb/`.

## Done when

A chat-memory node answers the same in a batch row as through the API, a retried prepare writes
one run, and every run whose nodes ran in the worker shows its steps whatever the run-log flag says.

## Files

- `back/src/app-api/flux/flux.service.ts`: `apiV2` session block, `prepareWorkflowSeedForBatchRow`,
  `seedVarInputNodeExecutions`, `openSpaceRunLog`, `writeSpaceRunLog`, `closeWorkerRun`.
- `back/src/app-api/flux/batch-run-preparation.service.ts`: `prepare`.
- `back/src/app-api/space_run_logs/run-events.service.ts`: `persistFinishedRun`.
- `worker/src/modules/temporal/workflows/process-batch.workflow.ts`: `processRow`.

## What changed in this revision

- Item 2 said a retried `prepare` duplicates rows for one run. Each call draws its own `runId`, so
  the effect is an orphan run, and the fix needs the workflow to own the id. That adds a worker
  change.
- Item 3 named only `apiV2`. The same overwrite happens in `closeWorkerRun`, which batch rows use in
  production.

## Implementation evidence

Every new test was run against the code without its fix first. Jest ran scoped, capped at 4 GB and
one worker; the integration specs ran on the local Postgres.

| Requirement | Spec | Failure seen without the fix |
|---|---|---|
| R1 | `api-v2-data-output-workflow.spec.ts`, "a batch row's chat memory" (2 tests) | The seed had no history (`Expected -20 / Received +0`) and nothing was cleared. |
| R1, own session | `api-v2-data-output-workflow.spec.ts`, "starts the row in a chat session of its own" | With the `default` fallback, it and the three parity tests failed: the seed had `selectedChat: "default"` and the canvas session. |
| R2 | `batch-row-prepare-retry.integration.spec.ts` | With `uuid()` in the insert, the `NodeExecution` table held two rows per node. |
| R2 | `batch-run-preparation.service.spec.ts` | With `uuid()` in `prepare`, the retried attempt prepared another run. |
| R2 | worker `process-batch.workflow.spec.ts`, "a prepare retried after the back did its work" | Sending no `runId`, the retried attempt reached the back with `undefined`. |
| R3 | `api-v2-data-output-workflow.spec.ts`, batch row in `off` and `shadow` | Without the worker `events` mode, the collector log was written and nothing folded. |
| R3 | `api-v2-data-output-workflow.spec.ts`, "the run log of an API run" | Without the switch, the routed run wrote the collector log; without the cancel, a queued write landed after the finish. |

Tests changed on purpose:

- `api-v2-data-output-workflow.spec.ts` pinned the defect: "writes the collector log and folds
  nothing when the run log flag is off, as an API run does". It now asserts the fold for a batch row
  in `off` and `shadow` mode. Four tests that check the collector log's content now run with events
  that cannot be folded, where the collector log is still the fallback.
- `run-events.integration.spec.ts` and `api-v2-finish-orphaned.spec.ts`: their doubles gained the
  fields the real services always have (`pendingFlushes`, `spaceRunLogsService`, `rebuild`).

Pre-existing failures, also on clean `origin/main`: `batch-process-access.integration.spec.ts` (one
test, `res.req` undefined in `base.controller.ts`) and three `worker.controller.*.spec.ts` suites that
do not compile (14 arguments expected, 13 given). Worker: `activities.web-search.spec.ts` does not
compile on `origin/main` either.

## Reviews

- `/simplify` (2026-11-18): applied the R3 rework above, the parallel history and object lookups
  in the batch prepare, the entity-built table in the integration spec, and two test clean-ups.
  Skipped: a second rebuild at the end of the run, which `events` mode already pays today; parallel
  reads inside the moved session block, a verbatim move; a multi-row Variable Input insert, a few
  rows per flow; `NodeLike` for the moved block, which reads untyped node data; and the window in
  which `apiV2`'s collector can write a document without nodes while a routed run is in progress,
  cosmetic because the final write is correct.

- `/code-review` medium (2026-11-18), 10 findings:
  - Fixed: an unfinished rebuild (no `run_finished`) now falls back to the collector log instead of
    leaving the run `in_progress`; a routed `apiV2` run flips its collector flush to the rebuild when
    it routes (`openSpaceRunLog().routeToWorkflow`), which removed the end-of-run cancel and leaves
    `persistFinishedRun` as on `main`; `prepare` refuses a `runId` that is not a UUID;
    `openSpaceRunLog` dropped its unread `recorder` field.
  - No change: a retried prepare leaves a second `run_seeds` row for the same `runId`, harmless
    because readers take the latest row or the `seedSnapshotId` the workflow carries;
    `Record<string, any>` on `RunSessionNode`, which the moved block needs; sequential reads in the
    moved block.
  - Known, not changed by B7b: the rebuild from events maps every non-error `run_finished` to
    `success`. R3 now applies events-mode semantics to worker runs in every mode, so this applies
    where the flag is off too.
  - **Decided 2026-11-18: each row gets its own chat session.** Batch rows run five at a time and all used session key
    `default`. With R1, a row reads whatever history the rows that finished before it wrote, in no
    fixed order, and a clear-on-execution row clears it while others run and rewrites the live node
    row once per row. The legacy batch ran rows one at a time, so rows shared memory in order. The
    choices were: share memory as today (non-deterministic order), give each row its own session
    (each row starts empty), or run a chat-memory flow's rows one at a time (legacy parity, worker
    change). The product owner chose the session per row; see the R1 design. The parity tests now
    run the API loop with the row's session, and the `chat_logs` record of a batch row keeps
    `input.sessionId: ''`, as the legacy batch wrote it.
- `/security-review` (2026-11-18): no finding at confidence 8 or above. Memory stays inside one
  owner and one flow (`ownerUserId` is the batch flow owner, scope `flowId:nodeId`); the insert is
  parameterised; the internal endpoint keeps `InternalApiGuard`; `ON CONFLICT DO NOTHING` never
  overwrites. Rows of one batch sharing a session is product behaviour, not a breach.

## Progress

- 2026-11-18: specified. Back `fix/868muzee4` and worker `fix/868muzee4` cut from `origin/main`.
- 2026-11-18: implemented and reviewed. Back: 7 commits (last `a3b762e6`); worker: 2 commits (last
  `0d8bd67`). Not pushed. Waiting on the batch-row memory decision before the PRs.
- 2026-11-18: decision 1, a chat session per batch row. Back commit `18cf648a`; related suites
  88 of 88.
- 2026-11-18: PRs opened as drafts: back #2121, worker #175, this spec #118. ClickUp moved to
  `in dev`.
- 2026-11-18: on dev. `develop` had drifted from `main` (back 521 commits, worker 340), so the task
  commits were cherry-picked instead of merging the branch. Back `develop` `bb201279` (revision
  2690), then worker `develop` `aab1977` (revision 267). Conflicts resolved with E4b (868muzf1f),
  which renamed `prepareWorkflowSeedForBatchRow` to `prepareWorkflowSeed`, shares it with scheduled
  runs and added `runType` and `metadata` to the Variable Input insert. In the dev landing the
  session fallback is a `prepareWorkflowSeed` input that only the batch preparation passes, so a
  scheduled run keeps `default`; a new spec pins it and was seen failing with the fallback inside
  `prepareWorkflowSeed`. **When E4b reaches `main` after B7b, resolve the same way.** Related suites
  on the dev tree: back 155 of 155 (with E4b's `workflow-seed-run-key` spec), worker 17 of 17.
- 2026-11-18: dev QA passed on real runs (9 batch rows in 3 batches, 3 workflow-routed API runs).
  R1: each row's seed has `selectedChat` = its `runId` with empty `entries`, and each row wrote its
  turn to its own session; the canvas `default` session did not change. R2: 9 of 9 Variable Input
  ids match `uuidV5(runId:nodeId)`, one row and one seed per run; a real retry was not forced. R3:
  `space_run_logs` keeps its nodes with status `success` in `events`, `off` and `shadow` mode for
  batch rows and API runs; the run-log flags were restored and verified. ClickUp moved to
  `ready for deploy`.
- Found during the dev QA, not caused by B7b: a chat flow wired the product's way (`fluxObject`
  output into the AI node, AI output into `inputAdd`) fails in a batch with "Node type fluxObject
  has no worker module", because the edges put the `fluxObject` in the workflow schedule and the
  worker has no module for it (registry `execution: 'state'`, `handoffOwner: 'A14'`). The row still
  records its turn in its own session. Owned by A14. Worker-run logs also omit the Variable Input
  step, which emits no event.
