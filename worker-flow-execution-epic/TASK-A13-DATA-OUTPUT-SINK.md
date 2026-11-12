# A13 — The Data Output as the workflow's sink

**Goal:** a run under the B4 workflow produces the same Data Output value, API reply, chatbot answer
and delivery as a run on the back's loop.

**Depends on:** A9, B4, A11. **Blocks:** turning the B4 flag on in production.
**Added 2026-10-23** from [`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md).

## Why

A9 moved email and callback delivery into the worker and handed the rest to B4: "when B4 lands,
`deliverRunOutputs` becomes its last step". B4's spec never picked it up. Today the back builds the
Data Output's value from its producers in memory, and that value is what the API reply, the chatbot
answer and A9's delivery read. The worker enum has `OUTPUT` with no activity, so a workflow run has
no sink.

## Scope

**In.** Build the Data Output's value from its upstreams' `node_executions` rows, by reference, as
B3b does for every other consumer. Record which executions it read.

**In.** Make `deliverRunOutputs` the workflow's last step, and keep the back's loop calling the same
code.

**In.** Flip `outputObjectNode`'s registry entry once both paths use the same builder.

**Out.** Changing the reply shape, the delivery channels, or A9's retry policies.

## Verification

- **Negative control (required).** Run one stored API flow under the workflow before this task and
  record the empty or missing reply; after it, the reply matches the back's loop byte for byte.
- Parity over a corpus: the API reply and the chatbot answer match between the two engines.
- A delivery fires once per run under the workflow, including after a retried last step.

## Done when

Workflow runs return the same reply and deliver the same outputs as the back's loop; the registry
entry is flipped; no back-only code builds the Data Output value.

**Added 2026-10-28.** A11 classes `outputObjectNode` as `execution: 'sink'`. This task makes B4's
gate accept `sink` and turns A11's `it.failing` "the gate accepts a flow that holds a `sink`" into a
plain test. The class stays `sink`.

## Files

`back/src/app-api/flux/flux.service.ts` (the Data Output assembly, `deliverRunOutputs` caller) ·
worker `process-flow.workflow.ts` · worker `node-activities.ts` (`OUTPUT`) · the A1 registry

## Code check and design (2026-11-09)

Read against back `origin/main` `cb2eec21` and worker `origin/main` `534d85a`. Branch
`refactor/868mn64j4` in back and worker.

### What the code does today

1. **The gate keeps the Data Output off the workflow on the API route.** `isWorkflowAcceptedNodeType`
   (back `engine-selector.ts`) accepts `worker`, `source` and `visual`; `outputObjectNode` is the only
   `sink`, so an API run with a Data Output goes to the back's loop. A11's
   `it.failing('accepts a flow that holds a sink (A13)')` sits in `engine-selector.spec.ts`.
2. **The back already builds the reply after a workflow run.** It awaits `processFlow`, merges each
   node's latest `node_executions.outputData` into `node.data` (`hydrateRunFromNodeExecutions`), then
   runs the same end-of-run code as the loop: reply, chatbot answer, form socket, delivery. That code
   reads the Data Output's `data.textData` (one `{id, label, text}` per incoming edge). What is missing
   is a Data Output row: the worker has no activity for `outputObjectNode`, so the child workflow
   throws "Node type outputObjectNode not supported".
3. **Batch and Temporal schedules reach `processFlow` with no gate.** `POST /batch-process` starts
   `processBatch`, which runs each row as a `processFlow` child (since worker `c022c88`, 2026-10-28);
   `runScheduledFlow` does the same behind `temporal_schedules`. A Data Output in those flows does not
   fail: `processSingleNode` throws a plain `Error`, Temporal retries the child workflow task forever,
   and the row, `processFlow` and the batch hang (seen in both red runs of the A13 specs). Prod worker
   logs since 2026-10-26 hold no "outputObjectNode not supported" and no `processBatch` line, so
   whether a production batch hit this is not verified.
4. **B3b's projection already handles the Data Output.** Worker `projectNodeInput` reads upstream
   `node_executions.outputData`, resolves large stored outputs, and runs the shared edge projection,
   which accumulates every input of an `outputObjectNode`. No new builder is needed.
5. **Delivery is a separate workflow the back starts after the run.** The plan carries rendered
   values; the consolidated callback is the final `apiV2` result and fires after `markCompleted`.
   `processFlow` has neither the callback URL nor the reply.

### Decisions

- **A13-D1. The worker writes the Data Output's row.** A new `outputObjectNode` activity runs through
  the B3b projection and writes the same row the back's loop writes (`outputData` holds `textData`),
  so the back's end-of-run code needs no engine branch. The upstream execution ids it read go to
  `metadata.sourceExecIds` (existing `jsonb` column, no migration).
- **A13-D2. Delivery stays a workflow the back starts after the run.** "`deliverRunOutputs` as the
  workflow's last step" is dropped: the plan needs the reply and the callback URL, which only the
  back has, and both engines already reach the same delivery code. Delivery for batch and
  scheduled runs, which never reach that code, is out of scope and recorded as a follow-up.
- **A13-D3. The class stays `sink`; the gate accepts it.** The registry entry loses `handoffOwner`
  and a `sink` entry no longer needs one; the A11 `it.failing` becomes a plain test; the contract
  JSON is regenerated. `strandedReason` stays, reworded: the type is still a stranded worker module
  for the back's loop (`flowDispatch: 'inline'`, because the loop builds the value in memory with the
  same edge projection and records the row itself), and the invariants spec requires a reason for
  every stranded entry. `prefetchSafe` stays `false`: prefetch is a separate engine chosen after the
  B4 route, and nothing shows it builds the Data Output the way the loop does.
- **A13-D5. The Data Output writes only its run row.** Other worker nodes merge their output into
  the live `flows_nodes` row; the back's loop resets only `text` and `textData` there and its
  end-of-run code saves `{text, textData}`. A projected `emailsData` left on the live row would reach
  the next run, so the Data Output activity writes `node_executions` only.
- **A13-D6. `metadata.sourceExecIds` is recorded for every node the B3b resolver reads, not only the
  Data Output.** It is the same single update `resolveNodeInput` already makes, so it adds no query.
- **A13-D4. The text renderers stay in the back.** The row stores the `textData` array, not joined
  text, so the three joins (`'\n'`, `' '`, `','`) keep one owner.

### Parity gaps found, in scope

1. `hydrateRunFromNodeExecutions` does not resolve large stored outputs, so a producer or Data
   Output over the inline limit would hydrate as a reference.
2. On an async API run, `run_finished` carries a `resultRef`, and `finishExecution`
   (`run-events.service.ts`) closes `flow_execution_status` with the workflow's stub result before
   the back writes the reply; `markCompleted` then changes nothing and polling returns the stub.
3. The final end-of-run projection runs only when the flow has a global-starter edge; confirm the
   hydrated `textData` is not overwritten or dropped.

### Out of scope, recorded

- One entry per loop iteration (needs B6 to let `arrayNode` through).
- Delivery for batch and scheduled runs (A13-D2).

## Implementation (2026-11-09)

Back `e05d15ef` and worker `422ec18` on `refactor/868mn64j4`; the worker's ported engine is synced
from back `e05d15ef`.

- **Gap 1** fixed: `hydrateRunFromNodeExecutions` resolves large stored outputs with
  `executionsLogsService.resolveMaybeClaimRef`, the resolver MCP and run logs already use.
  `rebuildMyUpdatedNodesFromDb` has the same gap but runs only in prefetch mode; left as is.
- **Gap 2** fixed: `runApiV2ViaWorkflow` writes `runWorkflowId` before it starts `processFlow`, and
  `finishExecution` closes only `flow_execution_status` rows without it. Only the async API creates
  those rows, and the back's job closes them itself (`markCompleted` or `markError`), so the real
  `{message, outputs}` wins. Trade-off: if the back task dies while it awaits, the row waits for
  Bull's stalled-job retry or `markError` instead of being closed with the stub.
- **Gap 3** needed no fix: with the starter edge the final re-projection does not overwrite the
  hydrated value, and without it the reply comes from the Data Output row (tested).
- Tests, each seen failing first: back `api-v2-data-output-workflow.spec.ts` (reply and delivery plan
  equal the loop's, including the three joins; large outputs; no starter edge; a failed Data Output
  withholds delivery) and two `run-events.integration.spec.ts` cases; worker
  `data-output.service.spec.ts` (shape, `sourceExecIds`, large upstream, re-run, saved row
  untouched), `process-flow.workflow.spec.ts` and `process-batch.workflow.spec.ts` with the real
  workflow code, `node-activities.spec.ts`.

## Reviews (2026-11-09)

**`/simplify`** (reuse, simplification, efficiency, altitude). Applied: one projection entry point
per layer instead of the `...WithSources` twins, one run-row persist instead of
`persistRunNodeSuccess`, `EdgeDataItem` for the Data Output arrays, one accepted-class list in the
gate, shared test stubs and the product's claim envelope in the specs. Skipped, recorded:

- **Who closes `flow_execution_status`.** `runWorkflowId IS NULL` works and is tested end to end, but
  it is not an explicit owner signal. A cleaner contract is a `callerFinishesRun` input to
  `processFlow` that omits `resultRef`, which reuses the existing "no `resultRef` leaves the row to
  the api-v2 job" rule. It changes the worker/back contract; follow-up.
- **The live-write deny list.** `LIVE_WRITE_EXCLUDED_FIELDS` restates the projection by hand, so
  other worker types (file-save, push-data, pull-data and more) can also leave projected
  `<field>Data` on `flows_nodes`. Deriving the list from the projection's target-field map would fix
  every type but changes their behavior; follow-up. A13 keeps a per-type opt-out for the Data Output.
- **Resolving large outputs only for the Data Output.** Rejected: the final re-projection reads the
  producers too, and the large-output test failed exactly there.
- **Large outputs in the prefetch readers** (`rebuildMyUpdatedNodesFromDb`, `buildPrefetchUpdatedNodes`).
  Same gap, other engine; follow-up.
- **Copying `input` into `outputData` in SQL** to avoid moving the payload through the worker, and
  one shared DDL fixture for the five worker integration specs. Optimizations outside the diff.
- **Other types still hang batch and scheduled runs.** `processSingleNode` throws a plain `Error` for
  any type without a module, so `arrayNode`, `conditionNode`, `fluxBox`, `fluxObject`,
  `libraryNode`, `nodesBox` and `webTrends` still hang a batch row forever. A non-retryable failure
  there, or the gate at `processBatch` and `runScheduledFlow` entry, would end the hang. Outside A13.

**`/code-review`** (high). Fixed, each with a test seen failing first:

- **A Data Output that never ran delivered on a failed run.** On the workflow route a node with no
  `node_executions` row was marked completed when the run ended in `error`, so a failed upstream
  still sent the Data Output's email (an empty "This is an output by undefined") and callback. The
  route now marks only executed nodes, as the loop does (back `4b279f07`).
- **The gate accepted every `sink`.** It now accepts a `sink` only with `workerModule: true`, reuses
  `isWorkflowSkippedNodeType`, and a `sink` without a worker module needs a `handoffOwner` again.

Checked and not changed:

- **A back task dies mid-run.** The `api-v2` queue never retries (`maxStalledCount: 0`,
  `attempts: 1`). After about 30 s another replica's stalled-job check fails the job and
  `failStalledRun` marks the execution `error` and sends the failure callback. The `processFlow`
  workflow keeps running and its result and delivery are dropped. Same as before A13.
- Resolving every large output at run end costs one S3 read per offloaded node, bounded by the node
  count; a failed read now fails the run loudly instead of replying with a reference.
- `metadata.sourceExecIds` has no reader yet; it is the acceptance criterion (A13-D6).

**A13-D7. Batch rows get the Data Output value and the callback (decided 2026-11-09).** Before B7
each row called `apiV2` with `sendEmail: false` and `runType: 'batch'`, stored `message[]` in the row
and fired the Data Output callback (A9.3); since B7 the row runs through `processFlow` and stores
only the workflow status. A13 restores the pre-B7 row: after each row the worker asks the back to run
the shared end-of-run code on the hydrated run, writes the reply into the row and starts one
delivery (callback only, no email).

### Batch rows and `nodeError` (2026-11-09)

Back `b6b6b59b`, `8abbd67f`; worker `8c63fc3`, `923e932`.

- The end of `apiV2` is `FluxService.settleRunOutputs`, shared by every `apiV2` route and
  `POST /worker/batch-row-outputs` (`InternalApiGuard`). After a row's `processFlow` child returns,
  the worker calls it with the row id; the back hydrates the run, settles it with `sendEmail: false`
  and run type `batch`, writes the row as before B7 and returns only `nodeError`, so the row text
  never travels through Temporal. The step is behind `patched('batch-row-finish')`.
- `OutputDeliveryService.start` rejects a reused workflow id and treats it as already started;
  batch rows use one id per run, so a retried finish sends the callback once.
- **`nodeError` parity.** The workflow route returned `null` for a failed node because the worker
  records the failure in `execution_logs`, not `outputData`. Hydration now joins the failed row's
  log (`deletedAt IS NULL`) and marks the node with the loop's `markNodeFailed`. A failure with no
  log (timeout, retries exhausted) uses the node's own user message, which `processFlow` now unwraps
  from the child failure; only for an `error` run with no logged failure. Cancelled, budget-stopped
  and truncated runs keep `nodeError: null`, as the loop does.
- The first failing row's reason becomes the batch `errorMessage`, also when the batch runs to the
  end. The finish activity has 10 attempts; 400 and 404 are non-retryable.
- Fixed on the way: B7's `writeRowOutput` passed a JS array as a jsonb parameter, which Postgres
  rejects, so a row with a message array could never be written.
- Not changed: with five rows in flight, the live Data Output row shows the row that finished last
  (since B7). `flows_logs`, `space_run_logs` and `chat_logs` are not written for batch rows (since
  B7); follow-up.

**`/code-review`, second pass on the batch commits.** Eight findings fixed as above (payload size,
`nodeError` without a log, owner objects for object callers, batch `errorMessage`, retry policy,
soft-deleted logs, one row outcome, precise types); one skipped (live row, above).

**`/security-review`.** No HIGH or MEDIUM finding. Checked: the new endpoint's guard and DTO
validation, parameterized queries, the egress guard on batch callbacks, that only `userMessage`
reaches users, `sourceExecIds` scope and the new logs. Below the threshold: `resolveMaybeClaimRef`
reads any S3 key without the `node-exec/` prefix or `authorizeRead` check that `/worker/get-payload`
applies; it predates A13 and needs a planted `__claimRef` plus a guessed UUID key. Optional hardening.

### Batch run logs (2026-11-10)

Back `6335ab55` and its review fixes. Decided by the user: batch rows write the run logs they wrote
before B7.

- Each row leaves the `flows_logs`, `space_run_logs` and `chat_logs` records the pre-B7 per-row
  `apiV2` call left. `apiV2` and `finishBatchRowRun` share the helpers factored out of `apiV2`
  (`openSpaceRunLog`, `describeRunLogOutcome`, `createRunFlowLog`, `writeSpaceRunLog`,
  `recordChatLog`); the batch space run log folds the run events `processFlow` already emits and
  follows `RUN_LOG_FROM_EVENTS` and shadow mode like an API run.
- A retried finish writes each record once: `flows_logs` and `chat_logs` keyed by the run id, chat
  memory appended in the same transaction as the `chat_logs` insert, `openRun` inserts the root doc
  only when missing, token totals read from the ledger. The row inputs `prepare` used are kept in
  `run_seeds.payload` and read at finish.
- Logs are written when the row finishes, so a running batch row is not on the Logs page yet.
- `/code-review` on the commit: ten findings, all fixed (debounced empty flush overwriting the
  events log, an errored row logged as success, the run-log flag ignored, chat memory lost after a
  failed append, a retry resetting a finished log, inputs recomputed from the current flow, wasted
  reads, an API chat-log rule change, loose types). Budget and spend stops need no change:
  `processFlow` has none today.

Found, not fixed (outside A13): a chat-memory `fluxObject` runs without its history in a batch row
because `prepare` skips the `fluxObject` preparation `apiV2` does; with `RUN_LOG_FROM_EVENTS` off an
API workflow run's Logs entry has no node steps; `seedVarInputNodeExecutions` inserts new rows on a
retried `prepare`. Scheduled runs started by E4's `runScheduledFlow` reach `processFlow` without the
back's end of run, as batch rows did; open question for the user. Both became Wave 5 tasks on 2026-11-10: B7b
(868muzee4) and E4b (868muzf1f).

## Dev tests (2026-11-10 and 2026-11-11)

Back `develop` `08786409` and worker `develop` `80a6cbb`, with real runs on dev. The test flows are in
the folder "a13-dev-qa" of a dev account. The flag `engine_in_workflow` was on only for each check,
and was restored and verified each time.

- Sync API: the replies are byte-identical between the loop and the workflow, with the timestamp
  masked. Flow A: loop `bdbf614a` vs workflow `9570d31c` (HTTP 200). Failing formula: loop
  `e42b1a39` vs workflow `ef184140` (HTTP 400).
- Async API under the workflow: polling returns the real `{message, outputs}`, and the execution
  status ends `completed`.
- Parity over more flows: the chatbot answer (loop `ad348e90` vs workflow `5ed3296e`), a 300 KB
  output stored as claim refs (`d0b1f401` vs `60a5bc44`), and a Data Output with no starter edge
  (`4b1cdd64` vs `6d27782d`).
- One delivery per run: 8 runs gave 8 delivery workflows, with one callback each and no email. A
  Temporal reset of a finished batch re-ran `finishBatchRowRunActivity` for both rows and started
  no new delivery and no duplicate log row.
- Batch of 2 rows: each row stores its own output, delivers once, sends no email and has its
  `flows_logs` record. `space_run_logs` was not verifiable, because the folder is not in a space.
- Failing node: the same error on both engines. A failed batch names the first failing row's reason.
- Not re-run on dev: the "before" half of the negative control, which needs a rollback. It was seen
  locally on 2026-11-09.

## The run log input keeps an explicit field list (2026-11-11)

The chatbot and sync API run log now stores an explicit field list with the owner's id. Back `b653484a`, `05a8db4f`, `7b321c1d`; the tests were seen failing first, and the reviews found no HIGH or MEDIUM issue.

## One delivery per API run: dropped (2026-11-11)

A fixed delivery id per top-level API run was implemented (back `0e6cff99`) and then dropped, because
no path reaches it. The async queue never retries a job (`attempts: 1`, `maxStalledCount: 0`), and the
async path delivers through its own sink. The real double delivery is a stalled job that resumes:
`failStalledRun` delivers the failure, then the live run delivers the real outputs. A fixed id would
keep the failure and withhold the real outputs, so that case is now A9b (868mvdm50).

## Merge readiness (2026-11-11)

Back #2105 and worker #168 are out of draft. Merged with the current `main` in a scratch tree, the
back has no conflict and passes 12 suites and 524 tests, and `tsc` is clean; the worker shares no
file with the new `main` commits. Deploy the back first.
