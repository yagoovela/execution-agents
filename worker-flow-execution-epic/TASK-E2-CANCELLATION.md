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

**Out.** Changing what cancellation means to the user, or cancelling already-committed side
effects. A cancelled push that already reached Stripe stays sent.

## Verification

- **Negative control (required).** Cancel a run mid-node and assert the next node never starts.
  Then break the propagation and watch it start anyway — that is the regression this task exists to
  prevent, and it is invisible without the test.
- Cancel during a **child workflow** (`fluxBox` / `libraryNode`): the child must stop too.
  Cancellation propagation is native for child workflows, so this test is cheap and proves the
  design choice.
- Measure click-to-effective-cancel before and after.
- Confirm the per-node timers are gone: run a sixty-node agent and count active timers and the
  database query rate against the pre-change baseline.

## Done when

Cancellation is Temporal-native end to end including child workflows, the poller and the ALS
context are removed, the footprint UX is unchanged, and the latency is measured.

## Files

`back/src/app-api/flux/node-cancel-watch.ts` · `back/src/app-api/flux/flux.service.ts:3192–3194, 4516–4530` ·
`back/src/temporal/temporal.service.ts` · the worker flow workflow and its activities
