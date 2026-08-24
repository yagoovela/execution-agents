# E3 — Make run notifications distributed, and unify the two paths

**Goal:** one delivery mechanism for run events, working across backend replicas.

**Depends on:** nothing technically; **must land before B5**, because parallel execution multiplies
the event rate. **Source:** analysis §11.3.

## Why

Two problems, both structural.

**The socket path is process-local.** `chatbotSocketByRun` is a plain `Map` in the backend process
(`flux.service.ts:2288, 5293–5307`, cleaned up at `:5392–5395`). A run whose socket was registered
on replica A cannot be notified from replica B. That is a blocker for horizontal scale, and it is
already latent — it does not need the worker migration to bite.

**There are two mechanisms.** The worker publishes to Redis (`room_status_updated`,
`room_stream_chunk`, `completion_stream_chunk`) which the backend relays via `@EventPattern` to
Socket.io; the inline path writes to the socket directly. Two paths to maintain, two places to fix
a bug, and they will drift — the same failure this epic is trying to end for dispatch lists.

## Scope

**In.** One path: everything publishes to Redis, the socket layer only consumes. The worker's
existing mechanism is the survivor — it already works across processes, which is the property
being bought.

**In.** A Redis adapter for Socket.io, or an equivalent, so any replica can deliver to any
connected client. Without it, unifying on Redis moves the problem rather than solving it.

**In.** Type the status strings. `'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'` are
free strings on both sides of a process boundary today — the worst place for a typo, because it
fails silently as a status the UI does not recognise.

**Out.** Changing the event payloads the front consumes. This is a transport change; a payload
change would make a regression impossible to attribute.

## Verification

- **Negative control (required).** Register a run's socket on one replica and emit from another;
  assert the client receives it. Run that test **before** the change and watch it fail — that
  failure is the bug, and demonstrating it is what justifies the work.
- Event ordering per node under parallel dispatch: a node's `RUNNING` must never arrive after its
  `COMPLETED`. Worth asserting explicitly, because parallelism is what makes it possible.
- No lost events with several nodes streaming at once — count emitted versus received.
- The inline path's direct socket writes are gone, not merely unused.

## Done when

One publish path, delivery works across replicas, statuses are typed, and ordering holds under
parallel dispatch.

## Files

`back/src/app-api/gateway/gateway.ts:69, 76` · `back/src/temporal/temporal.controller.ts:88–97` ·
`back/src/app-api/flux/flux.service.ts:2288, 5293–5307, 5392–5395` ·
`worker/src/modules/notification/notification.service.ts`
