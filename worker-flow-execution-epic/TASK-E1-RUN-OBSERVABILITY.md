# E1 — Run observability when the worker owns the loop

**Goal:** keep the nested run timeline, the per-node billing attribution and the secret redaction
working once the loop is not in the backend's process.

**Depends on:** B2. **Must land with B4**, not after it. **Source:** analysis §11.3.

## Why this is a subsystem, not a detail

`RunLogCollector` is an in-memory **tree** living in the backend process for the length of a run:
`startNode` / `endNode` per node, `innerSteps` for sub-steps, `subRun` plus `startLoopBody` and
`startLibrarySubRun` for nested runs, debounced into `space_run_logs` and finalised with a
synchronous `flushNow`. The product surface built on it — the nested run timeline — depends on the
hierarchy, not just the events.

Two more things ride on it. `redactSecrets` is **the only** place credentials are scrubbed before
reaching a log; leaking into `space_run_logs` is a security event, so any refactor must keep that
hook. And `chargeContext`, the AsyncLocalStorage the backend uses to attribute token spend to the
current node, is single-process by construction.

None of this survives the loop moving, and none of it belongs to any node's task.

## Scope

**In. The model is decided, not open: the backend rebuilds the tree from events the worker emits.**
An earlier draft of this task offered "worker keeps the tree" as an equivalent option. It is not
(review §4.3): keeping the tree inside the workflow makes **workflow state grow with the run**,
which collides directly with the history limits B4 now has to respect. Event-sourced
reconstruction is the only shape compatible with both parallelism and bounded history — and it is
already how the Temporal path behaves, emitting status through Redis and writing `execution_logs`.

What remains to design is the event contract: enough to rebuild `innerSteps` and `subRun` ordering
without replaying the tree itself.

**In.** Converge charge accounting on the worker's pattern. The step documentation argues, and this
epic accepts, that explicit `execId`/`nodeId` over HTTP is the **better** design and the backend
should adopt it rather than the worker replicating AsyncLocalStorage. When `onUpdateTokens` and
`chargeContext` disappear, that is progress, not loss.

**In, if it is still open.** A run whose flow calls other agents reports `totalTokens = 0`, however
much the chain charged: the called agent runs in its own `apiV2` with its own accumulator, and
`flowCallerNode`/`libraryNode` drop what it returns. Measured on dev on 2026-09-18 (four runs, 0.218
to 0.803 credit charged, all logged as 0) and written up as 868m6r9py — a fix derived from S3, not
a prerequisite for it. Whoever retires `onUpdateTokens` here passes through exactly this code, so if
the follow-up has not shipped by then, it is cheaper to take it in this task than to fix the
accumulator twice.

**In.** Under parallelism the before/after snapshot subtraction that computes a node's spend stops
working — two siblings both move the accumulator. Billing must dedup by a key in
`token_transaction` instead, and a node's spend is read back by that key — the pattern the worker
path already uses (`sumChargesByExecution(execId, nodeId)` in `flux.service.ts`). This must be
settled before B5, not after.

**In. The dedup key, measured on dev on 2026-10-16.** The key is not `(execId, nodeId)`:

1. Today's dedup is a read-then-write. `ProductService.updateTokens` runs
   `findOne({ execId, nodeId })` and inserts when nothing is found, reading the ids from
   `chargeContext` when the caller does not pass them. No database constraint backs it, so two
   concurrent charges can both pass the read.
2. One AI charge writes three rows with the same `execId` and `nodeId`: `<model>-input-tokens`,
   `<model>-output-tokens`, and `<model>`. On dev, all 957 keyed pairs from the last 60 days have
   exactly three rows. A unique index on `(execId, nodeId)` refuses every AI charge.
3. `(execId, nodeId, api)` is unique on dev: 6,147 keyed triples since the first keyed row
   (2026-06-11), with no duplicates. Another 265 rows from the last 60 days have no `execId` and
   stay outside the key.

Before you ship a unique index on `(execId, nodeId, api)`:

1. Run [`e1-q1-charge-key.sql`](./e1-q1-charge-key.sql) on prod and classify every duplicate it
   returns, per the measure-before-refusing rule.
2. Check whether any node charges the same `api` twice in one execution. Today's `findOne`
   already swallows a second charge for the same `(execId, nodeId)`, so zero duplicates may hide an
   undercharge rather than prove the case cannot happen.
3. Generate the index with `pnpm migration:generate`, and make the insert conflict-safe so the
   database, not the read, resolves two concurrent charges.

**In.** Preserve `redactSecrets` explicitly, with a test.

**In, with B4.** Write `flow_execution_status` (PR #1902) once the loop leaves the back. Settled in
[Contract with B4](#contract-with-b4): this task's back side writes it.

**Out.** Redesigning the timeline UX or the `space_run_logs` schema. The JSONB there may need
partitioning eventually; that is a separate concern.

## Contract with B4

This section is the single source for how B4's workflow and E1's back side meet. B4 links here
instead of restating it.

### Who owns what

| Concern | Owner | B4 does |
|---|---|---|
| Run-log tree, `space_run_logs`, `RunLogCollector`, `redactSecrets` | E1 (back) | Emits events only |
| `flow_execution_status` | E1 (back) | Emits `run_finished` only |
| Run and node token totals, `token_transaction` dedup, retiring `onUpdateTokens` and `chargeContext` | E1 (back) | Passes `execId` and `nodeId` explicitly on every charge call |
| Event contract type | E1 (back), ported to the worker | Imports the ported type |
| Emitting events, in order, from the workflow | B4 (worker) | Everything in [What B4 does](#what-b4-does) |

**`flow_execution_status` is settled: E1's back side writes it** when it handles `run_finished`,
in the same place that finalises `space_run_logs`. The status, the run log and the run total then
come from one handler and one ledger sum, so they cannot disagree. The rejected alternative was a
separate status callback from the workflow: it adds a second writer for the end of a run, and it
still depends on the same final activity running.

### The event

The worker sends events to `POST /worker/run-events` on the back, through an activity, in
batches. Do not use Redis pub/sub: a lost event leaves a broken tree or a run stuck in
`in_progress`.

| Field | Type | Meaning |
|---|---|---|
| `runId` | `string` | The run's id (`runLogProcessId` today) |
| `seq` | `number` | Monotonic per `runId`, starting at 1, with no gaps. The back orders by it and treats a repeated `seq` as a retry. |
| `kind` | enum, below | What happened |
| `execId` | `string` | The node execution id from B1. Absent on run-level kinds. |
| `nodeId` | `string` | Absent on run-level kinds |
| `nodeType` | `string` | Absent on run-level kinds |
| `parentExecId` | `string \| null` | The container node execution this event nests under. `null` at the run's top level. |
| `iteration` | `number \| null` | Loop iteration, when the event is inside a loop body |
| `status` | `'success' \| 'error' \| 'cancelled'` | On `node_finished` and `run_finished` only |
| `error` | `{ userMessage: string; devMessage?: string } \| null` | On failure only |
| `at` | ISO 8601 string | When it happened in the workflow |

| `kind` | Collector call it rebuilds | Emitted from |
|---|---|---|
| `run_started` | collector creation | B4 |
| `node_started` | `startNode` | B4 |
| `node_finished` | `endNode` | B4 |
| `run_finished` | `finalize`, plus the `flow_execution_status` write | B4 |
| `loop_body_started` | `startLoopBody` | B6 |
| `library_subrun_started` | `startLibrarySubRun` | B6 |
| `flow_caller_subrun_started` | `startFlowCallerSubRun` | B6 |

Events carry ids only. They never carry a node's input, output, settings, raw response or token
count. The back reads those from the node's `node_executions` row and its charges from
`token_transaction`, by `execId`, and applies `redactSecrets` before anything reaches
`space_run_logs`. This keeps workflow history bounded (B4) and keeps redaction in one place.

### What B4 does

1. Imports the event type through `sync:ported-engine`, the same path B2 uses, covered by the
   drift test. Do not hand-write a copy.
2. Emits `run_started` before the first node and `node_started`/`node_finished` around every
   dispatched node, with `seq` incremented in workflow code. Workflow code is deterministic, so
   `seq` survives replay.
3. Emits `run_finished` from a `finally` block, so it is sent on success, on error and on
   cancellation. Use a non-cancellable scope for that activity so a cancelled workflow still
   reports the end of the run.
4. Passes `execId` and `nodeId` explicitly on every charge call to the back. Nothing in the
   worker reads a run-scoped context.
5. Writes nothing to `space_run_logs`, `flow_execution_status` or `token_transaction`, and
   computes no token totals.

### Ordering between E1 and B4

1. E1 publishes the event type and `POST /worker/run-events` first, behind the same per-flow flag
   B4 uses. The back's own loop emits through the same contract, which lets E1 prove timeline
   equivalence before B4 exists.
2. B4 imports the type and emits events.
3. They ship together, as the plan requires.

## Validating B4 against this contract

If you validate B4's branch with an AI assistant, give it this section and the branch, and ask it
to report each check as `PASS`, `FAIL` or `COULD NOT VERIFY`, with `file:line` evidence. Ask it to
read the code and run the tests; a grep with no hits is not proof on its own.

1. The worker has no write to `space_run_logs`, `flow_execution_status` or `token_transaction`,
   and no token arithmetic.
2. Every event the workflow emits has `runId` and `seq`, and every node-level event also has
   `execId`, `nodeId` and `nodeType`.
3. No event payload carries input, output, settings, a raw response or a token count.
4. `seq` is assigned in workflow code, starts at 1 and increases by one per event.
5. `run_finished` is emitted from a `finally` block inside a non-cancellable scope, and a test
   covers the cancelled case.
6. Every charge call from the worker passes `execId` and `nodeId` explicitly.
7. The event type is imported from the ported module, and the drift test passes.
8. **Negative control.** Change one `kind` value in the ported type and confirm the drift test
   fails. Then remove the `run_finished` call and confirm a test fails. Restore both and say which
   failures you observed.

## Verification

- **Negative control (required).** Remove the nesting so loop iterations are emitted as siblings
  of the loop rather than children, and confirm a test fails on the tree shape. This is not
  hypothetical: the same source records it as the classic bug in this code — using
  `runLogCollector` where `loopRunLogCollector` was meant. Reproduce it deliberately, then guard it.
- **Redaction.** Feed a credential through a node and assert it does not appear in
  `space_run_logs`. Break `redactSecrets` and watch the test go red.
- **Billing parity under concurrency.** Run a flow with two parallel siblings that both charge, and
  assert the total matches the sequential run exactly. Subtraction-based accounting fails here;
  that failure is the point of the test.
- Timeline equivalence: a nested `fluxBox` run renders the same tree before and after.

## Done when

The timeline is identical for nested runs, secrets are still redacted, billing matches under
concurrency, and no run-scoped state depends on AsyncLocalStorage.

## Files

`back/src/app-api/space_run_logs/` (`run-log-collector.ts` — `RunLogCollector` and `redactSecrets`) · `back/src/jobs/apiV2Job/apiV2Job.processor.ts` (writes `flow_execution_status` today) ·
`back/src/app-api/flux/flux.service.ts` (`runLogCollector` start/end/finalize/`flushNow`, `chargeContext`) ·
`back/src/app-api/token_transaction/` · `back/src/temporal/worker.controller.ts` · the worker flow workflow
