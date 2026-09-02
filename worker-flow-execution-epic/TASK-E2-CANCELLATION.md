# E2 — Align cancellation with Temporal instead of porting the poller

**Goal:** cancelling a run works when the loop is in the worker — by using what Temporal already
provides, not by reimplementing the current design somewhere else.

**Depends on:** B4. **Source:** analysis §11.4.

## Why aligning beats porting

The current mechanism cannot move as-is: `nodeCancelContext` is AsyncLocalStorage, so it is blind
the moment the handler runs in another process. The rest of it — a Postgres status column, a
WebSocket signal, a poll — is portable but is not what you would build on Temporal.

Temporal already has this. `WorkflowHandle.cancel()` on the backend side and
`Context.current().cancelled` on the worker side give cooperative cancellation with none of the
polling. So the migration gets cancellation **almost for free**, and the work is to converge on it.

There is also a cost to carrying the current design forward: it runs **one `setInterval` per
node**, so a sixty-node agent holds sixty timers hitting the database. Behind a flag that is
tolerable; on by default and unoptimised it becomes a performance offender in its own right.

## Scope

**In.** Backend calls `handle.cancel()` when a cancel is requested; the worker respects
`Context.current().cancelled`; the per-node poller is retired along with `nodeCancelContext`.

**In.** Keep what the product needs: the cancel footprint — which node the run was on when it was
cancelled — is shown to the user, and `finishCancelledNode` must still mark state correctly so a
cancelled run does not look stalled.

**In.** Decide the latency contract. Today a 1500 ms cache over a 2000 ms poll can leave up to
3.5 s between the click and the effective cancel. Native cancellation should improve that —
measure it and state the number rather than assuming.

**In.** Validate the feature flag's current state before relying on it. `NODE_CANCEL_IN_FLIGHT_FLAG`
was added after the original design and is not proven at production scale.

**In — what the ledger records, per `D22`.** We ask the provider to cancel. If it reports the tokens
spent up to that point, record the charge **normally**, exactly as a generation that completed — the
work was really done and really cost. If it reports nothing, record what is available and mark the
entry as cancelled or aborted by the user. **Never record zero for a cancelled generation that
consumed tokens**, because that is the case that makes the ledger disagree with the provider's
invoice, and it disagrees silently.

**In — cancellation propagates down the chain, per `D23`.** A `fluxBox`, `libraryNode` or
`arrayNode` is not allowed to finish the way a generation is: its execution is an open-ended amount
of further work. Cancelling one cancels its children, which is native for Temporal child workflows
and is what the `parentRunId` chain from `S1` exists to carry. For `arrayNode`, the element already
generating finishes; the remaining elements never start. **`nodesBox` is not in this list:** it dispatches to `objectCaller`, which executes no nodes and only reads and writes an object's
session state, so cancelling it prevents no spend and leaves the object half-written.

**Out.** Changing what cancellation means to the user, or cancelling already-committed side
effects. A cancelled push that already reached Stripe stays sent.

## Verification

- **Negative control (required).** Cancel a run mid-node and assert the next node never starts.
  Then break the propagation and watch it start anyway — that is the regression this task exists to
  prevent, and it is invisible without the test.
- Cancel during a **child workflow** (`fluxBox` / `libraryNode`): the child must stop too.
  Propagation is native for child workflows, so the test is cheap — but **no child workflow exists
  until B6 (Wave 5)**, so this proof is B6's Done-when clause, not this task's. E2 proves
  cancellation for a single-level run.
- Measure click-to-effective-cancel before and after.
- Confirm the per-node timers are gone: run a sixty-node agent and count active timers and the
  database query rate against the pre-change baseline.

## Done when

Cancellation is Temporal-native end to end for a single-level run (the child-workflow proof lands
with B6, which creates the first child workflow), the poller and the ALS context are removed, the footprint UX is unchanged, and the latency is measured.

## Files

`back/src/app-api/flux/node-cancel-watch.ts` · `back/src/app-api/flux/flux.service.ts` (`NODE_CANCEL_IN_FLIGHT_FLAG`, `nodeCancelContext.enterWith`, `finishCancelledNode`) ·
`back/src/temporal/temporal.service.ts` · the worker flow workflow and its activities
