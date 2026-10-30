# E2 — Align cancellation with Temporal instead of porting the poller

**Goal:** cancelling a run works when the loop is in the worker — by using what Temporal already
provides, not by reimplementing the current design somewhere else.

**Depends on:** nothing since 2026-10-26 (was B4; the Temporal-native cancel is already in production).
**Blocks:** nothing since 2026-10-26 (E2-b moved the poller retirement to C1). **Source:** analysis §11.4.

**Rescoped on 2026-10-26 (E2-b, E2-c, E2-d).** The Temporal-native half is in production. The
per-node poller moves to C1, D23 moves to B6, and E2 keeps two items: the D22 gap and the latency
contract.

## Why aligning beats porting

The current mechanism cannot move as-is: `nodeCancelContext` is AsyncLocalStorage, so it is blind
the moment the handler runs in another process. The rest of it — a Postgres status column, a
WebSocket signal, a poll — is portable but is not what you would build on Temporal.

Temporal already has this. `WorkflowHandle.cancel()` on the backend side and
`Context.current().cancelled` on the worker side give cooperative cancellation with none of the
polling. So the migration gets cancellation **almost for free**, and the work is to converge on it.

## Scope

**Done (in production on 2026-10-26).** The back calls `handle.cancel()` when a cancel is
requested, and the worker honours cancellation. The cancel footprint — which node the run was on
when it was cancelled — is shown to the user, and `finishCancelledNode` marks state so a cancelled
run does not look stalled. Keep both working.

**In — what the ledger records, per `D22`.** We ask the provider to cancel. If it reports the tokens
spent up to that point, record the charge **normally**, exactly as a generation that completed — the
work was really done and really cost. If it reports nothing, record what is available and mark the
entry as cancelled or aborted by the user. **Never record zero for a cancelled generation that
consumed tokens**, because that is the case that makes the ledger disagree with the provider's
invoice, and it disagrees silently. The open gap: a cancel that arrives as a thrown error reaches
`resolve-cancel-settlement.ts` with `output: null` and charges nothing. The cancelled mark is the
`node_executions` row (`executionStatus: 'CANCELLED'`, `cancelledAt`), per E2-c.

**In.** Decide the latency contract. Today a 1500 ms cache (`isCancelRequested`) over a 2000 ms poll
can leave up to 3.5 s between the click and the effective cancel on the inline loop. Measure
click-to-effective-cancel on the inline loop and on the `processFlow` workflow, and state the
number rather than assuming.
Measured on 2026-10-26; see [Latency contract](#latency-contract).

**Moved to C1 (E2-b).** Retiring the per-node poller (`node-cancel-watch.ts`), `nodeCancelContext`
and the `node_cancel_in_flight` flag. The poller lives only in the back inline loop, which runs
almost every production run while `engine_in_workflow` is off and twelve node types are `inline`.
It is also the only thing that aborts an outbound request in the middle of an inline node.

**Moved to B6 (E2-d).** Cancellation propagation down the chain, per `D23`. `fluxBox`,
`libraryNode` and `arrayNode` are `inline` until B6 makes them workflow constructs, so nothing in
E2 can deliver or prove it.

**Out.** Changing what cancellation means to the user, or cancelling already-committed side
effects. A cancelled push that already reached Stripe stays sent.

## Decisions (2026-10-23)

| Id | Question | State | Answer |
|---|---|---|---|
| E2-a | Port the cancellation mechanism into the worker, or converge on Temporal's? | **Settled** | Converge on Temporal-native cancellation (option A): the back calls `handle.cancel()`, the worker checks `Context.current().cancelled`, and the per-node poller and `nodeCancelContext` are retired. The cancel footprint and `finishCancelledNode` are still wired by hand. |
| E2-b | Does E2 retire the per-node poller, or does C1? | **Settled 2026-10-26** | C1. The poller lives only in the back inline loop, so C1 deletes it together with that loop, after the B4 flag is on in production and B6 moves the container types. E2 no longer blocks C1. |
| E2-c | Where is a cancelled charge marked (D22)? | **Settled 2026-10-26** | On `node_executions` (`CANCELLED`, `cancelledAt`). `token_transaction` gets no new column and no migration. |
| E2-d | Does E2 own D23 propagation to `fluxBox`, `libraryNode` and `arrayNode`? | **Settled 2026-10-26** | No. B6 owns D23 and its proof, because the three types stay `inline` until B6. |

## State in production (2026-10-26)

Checked on the production code (back `5e92e879`, worker `abf3b09d`). **Moved to Wave 5.**

| Criterion | In production | Evidence |
|---|---|---|
| The back calls `handle.cancel()` | Yes | `execution_logs.service.ts` (`requestRunCancellation`), `temporal.service.ts` (`cancelWorkflow`) |
| The worker honours cancellation | Yes | `process-flow.workflow.ts` (`isCancellation`, `nonCancellable` finalize), `process-single-node.workflow.ts` (`CancellationScope`, `cancelNode`), activity heartbeats |
| Poller and `nodeCancelContext` retired | **No — moved to C1 (E2-b)** | `node-cancel-watch.ts` (`setInterval` every 2000 ms, `AsyncLocalStorage`), still wired in `flux.service.ts` behind `node_cancel_in_flight` |
| Cancel footprint and `finishCancelledNode` | Yes | `flux.service.ts`, `cancelled-run-footprint.ts`; worker `settleCancelledNode` |
| D22: a cancelled generation records its tokens | **Partly** | `resolve-cancel-settlement.ts` charges partial tokens for `textGenerator` when the activity returns a cancelled output; a cancel that arrives as a thrown error passes `output: null` and charges nothing; no entry is marked as cancelled |

Users can cancel `canvas` and `api` runs today: `POST /runs/:runId/cancel` writes the cancel row,
cancels the B4 workflow when one exists, and signals every in-flight node workflow. What remains in E2
is the **Partly** row and the latency measurement.

## Latency contract

Measured on dev on 2026-10-26 for an in-flight `commandTextNode`, from the cancel request to
`node_executions.cancelledAt`. Data and scripts: `etc/868m0vn6y/latency/` in the workspace.

| Engine | Cancel entry point | n | Median | p90 | Max |
|---|---|---|---|---|---|
| Inline loop | MCP `cancel_run` | 16 | 1.88 s | 2.18 s | 2.26 s |
| `processFlow` workflow | `POST /executions_logs/runs/:runId/cancel` | 8 | 1.94 s | 2.02 s | 2.08 s |

**The contract.** A worker node stops within about 2.3 s of the cancel request on both engines.
The bound comes from the worker's Temporal heartbeat throttle (`maxHeartbeatThrottleInterval: "2
seconds"` in `worker.service.ts`): the activity sees the cancel in the response to its next
heartbeat. Cancels land in two groups, about 0.2–0.4 s when a heartbeat was due and about
1.8–2.3 s when one had just been sent. The provider stream runs until the node stops, so a slower
cancel leaves a longer partial output, and D22 charges it.

**The 3.5 s figure applies only to inline nodes.** The 1500 ms cache over a 2000 ms poll
(`node-cancel-watch.ts`) only aborts calls the back makes itself. A worker node dispatched by the
inline loop runs in `executeNodeViaTemporal`, which never reads that abort signal. The poller and
its bound leave with C1 (E2-b).

**How it was measured.** On the inline loop, the requested time is the local send time corrected by
the measured clock offset to the dev DB (±150 ms). On `processFlow`, `engine_in_workflow` was
turned on in dev for 136 s and restored to `false`; the requested time is
`flow_run_states.requestedAt`, so both ends come from the DB clock.

## Verification

- **Negative control (required).** Cancel a generation so that the cancel arrives as a thrown
  error, and assert the partial tokens the provider reported are charged and the
  `node_executions` row is `CANCELLED`. Then restore `output: null` in the settlement and watch the
  charge drop to zero — that is the silent ledger gap this task exists to close.
- Cancel a run mid-node on the `processFlow` workflow and assert the next node never starts.
- Measure click-to-effective-cancel on the inline loop and on the `processFlow` workflow, and record
  both numbers here. Done on 2026-10-26; see [Latency contract](#latency-contract).

## Validation results

### Local end to end (2026-10-27)

The PR heads ran on an isolated local stack with a copy of the dev database. All ten checks
passed: partial charge on cancels at 1 s, 3 s and 12 s; `CANCELLED` rows with `cancelledAt`; the
cancel footprint; `processFlow` stopping before the next node; and the MCP `cancelled` status on
the inline engine, `processFlow`, a queued run, a cancel before the workflow starts, and the MCP
Tasks primitive.

The run found two defects that dev could not show. Both are fixed in worker #148, and each fix has
a test that was seen failing first:

1. **A cancel charged 0 credits with the AI SDK version that `main` resolves.**
   `@ai-sdk/anthropic` 4.0.78 wraps the Temporal `CancelledFailure` in an `AI_APICallError` while
   the stream still waits on the network, so the worker read the cancel as a provider failure.
   `develop` resolves 4.0.44, so the dev check passed. Fix: `isAbortError` follows `error.cause`,
   and the stream's catch path reports the partial usage before it rethrows.
2. **A cancel before the first node opened ended the run as `error`.** No result was stored, so
   `run_finished` carried `resultRef: ""`, which back refuses with a 400. Fix: `run_finished` sends
   `resultRef` only when a result was stored. The general cause, retrying a refused event, is
   [868mnzkgg](https://app.clickup.com/t/868mnzkgg).

Known limit: a cancel at 0 s charges nothing, because the provider request has not started.

### Dev (2026-10-28)

After back `api-task-definition-dev:2628` and worker `worker-task-definition-dev:237`, an MCP
cancel of run `66c90d19` ended `cancelled` with "Run cancelled", charged 3.458 credits for the
partial generation, and no later node ran.

### Production (2026-10-28)

After back `api-task-definition-prod:830`, worker `worker-task-definition-prod:83` and MCP
`mcp-prod:15`, a temporary agent with two Claude Haiku 5.5 nodes (a long essay, then "Say OK") ran
in a folder created for the test. The agent and the folder were deleted afterwards.

| Run | Cancel | Node 1 | Node 2 | Status | Credits |
|---|---|---|---|---|---|
| `4d4414b6` | None (baseline) | 39.7 s, 18,818 bytes | Ran | `completed` | 3.524 |
| `88ee1612` | At about 19.5 s | Stopped with 5,727 bytes | Never started | `cancelled` | 0.719 |
| `3009e8a7` | At 10.3 s | Stopped with 0 bytes | Never started | `cancelled` | 0.0033 |

Run `88ee1612` meets every acceptance criterion: the node stops mid-generation, keeps the partial
text, charges in proportion to it, and the next node never starts.

**Open point, not verified.** Run `3009e8a7` stopped before any text arrived. Its 0.0033 credits
matches the prompt's input tokens alone. If Claude Haiku 5.5 was still reasoning, the reasoning
tokens were not charged: with hidden reasoning, there is no text to estimate from. The charge is
not zero, so the acceptance criterion holds as written, but the charge may be lower than the
tokens spent. To confirm, cancel a reasoning model locally before its first text token and compare
the charge with the provider's usage.

## Done when

A cancelled generation that consumed tokens is never charged zero, whether the cancel arrives as a
cancelled output or as a thrown error; the footprint UX is unchanged; and the latency contract is
measured and stated.

## Files

`back/src/app-api/executions_logs/execution_logs.service.ts` (`requestRunCancellation`) ·
`back/src/temporal/temporal.service.ts` (`cancelWorkflow`) ·
`back/src/app-api/executions_logs/run-cancellation.service.ts` (`isCancelRequested`) ·
`back/src/app-api/flux/flux.service.ts` (`finishCancelledNode`, `recordLegacyNodeCancelled`) ·
`back/src/app-api/flux/cancelled-run-footprint.ts` ·
`worker/src/modules/temporal/workflows/resolve-cancel-settlement.ts` (`resolveCancelSettlement`) ·
`worker/src/modules/nodes/shared/run-cancellable-node.ts` ·
the worker `process-flow.workflow.ts` and `process-single-node.workflow.ts` (`settleCancelledNode`) ·
`worker/src/modules/nodes/shared/is-abort-error.ts` (`isAbortError`) ·
`worker/src/modules/nodes/text-generator/text-generator.service.ts` (`consumeFullStream`)
