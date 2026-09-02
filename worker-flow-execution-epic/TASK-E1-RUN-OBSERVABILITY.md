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

**In.** Under parallelism the before/after snapshot subtraction that computes a node's spend stops
working — two siblings both move the accumulator. Billing must dedup by primary key in
`token_transactions` instead. This must be settled before B5, not after.

**In.** Preserve `redactSecrets` explicitly, with a test.

**In, with B4.** Decide who writes `flow_execution_status` (PR #1902) once the loop leaves the back —
the workflow through a callback, or this task's collector. B4 carries the same line; answer it once.

**Out.** Redesigning the timeline UX or the `space_run_logs` schema. The JSONB there may need
partitioning eventually; that is a separate concern.

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
