# E3b — Deliver each worker event once, however many back replicas run

**Goal:** every run event the worker publishes reaches the browser exactly once, with one, two or
three back replicas.

**Depends on:** nothing. **Blocks:** running the back on more than one replica, which production
already does (see **Why**). **Added 2026-11-04** from the replica audit of that day.
ClickUp: [868mrv6cg](https://app.clickup.com/t/868mrv6cg).

## Why

`E3` made Redis the one publish path and installed the Socket.io Redis adapter, so any replica can
reach any socket. It did not make delivery single. Read against back `origin/main` on 2026-11-04:

1. The back connects the Nest Redis microservice transport at boot (`main.ts`,
   `connectMicroservice` with `Transport.REDIS`). That transport is publish/subscribe, so **every
   replica** receives every `room_status_updated` and `room_stream_chunk` the worker publishes
   (`temporal.controller.ts`, `handleRoomUpdated` and `handleStreamChunk`).
2. Each replica then emits the event through `NotificationsGateway` (`sendToUser`,
   `sendStreamChunk`, `relayStreamChunkToSocket`) with `this.server.to(...)`. The Redis adapter
   broadcasts that emit to the sockets of every replica.
3. With N replicas, the browser receives each status and each stream chunk N times. The chatbot
   appends chunks as they arrive (front `ChatBot.tsx`), so streamed text appears N times.

`E3`'s verification asked for "no lost events" and never for "no duplicate events", and the `S8`
replica harness did not cover this path. That is how it shipped.

**Corrected premise (2026-11-04).** `E3`, `S4` and `S8` were written while production ran one back
task (`S4` measured `desiredCount` 1 in every environment). Production now autoscales the back on
CPU: target 55 %, minimum 1, maximum 3 (`api-autoscaling-prod`). It set the desired count to 2
every day from 2026-10-28 to 2026-11-03, around 11:00. So this defect is not latent: it can occur
every day.

## Scope

**In.** Each event is delivered once. Two acceptable designs; choose in the PR and record why:

1. **Emit locally.** Every replica still receives the event, but emits it with
   `this.server.local.to(...)`, so each replica delivers only to the sockets it holds. The pub/sub
   fan-out already reaches the replica that holds the socket. This is the smaller change.
2. **Consume once.** Worker events go to a queue or a Redis stream with one consumer group, and the
   consumer keeps the adapter broadcast.

**In.** The same rule for the chatbot relay (`relayStreamChunkToSocket`, emit by `socketId`).

**In.** Confirm, and record here, that the completion API stream (`router.controller.ts`,
`completion_stream_chunk`) is unaffected: only the replica that owns the request emits it.

**Out.** Any change to the event payloads the front reads. This is a delivery change only.

## Decision (2026-11-06)

**Design 1, emit locally.** `NotificationsGateway` emits with `this.server.local` in `sendToUser`,
`sendStreamChunk` and `sendChatStreamEvent` (the chatbot relay). Back PR
[#2094](https://github.com/enhancedai-com/Flux-Prompt/pull/2094), branch `fix/868mrv6cg`.

- **Why it is safe.** Every caller of these three methods is a Redis pub/sub handler
  (`temporal.controller.ts`, `handleRoomUpdated` and `handleStreamChunk`), and the back publishes its
  own run events through the same transport (`notification-publisher.service.ts`). So every replica
  receives every event, and the replica that holds the socket always delivers it.
- **Why not design 2.** One consumer group changes the worker and back transport and adds a queue,
  for no gain on this defect.
- **Keep the broadcast in `app-api/gateway/gateway.ts`.** `response` and `responseToUser` are called
  directly by request handlers on one replica, so they need the adapter broadcast to reach a socket
  on another replica. Do not switch them to `local`.
- **Completion API stream: unaffected.** `CompletionStreamRegistry.emit` calls
  `this.handlers.get(streamKey)?.(...)`. Only the replica that owns the HTTP request registered a
  handler, so the other replicas do nothing. The e2e spec pins this; sharing the handler map across
  replicas makes it fail.
- **Second symptom found.** On the old code, copies from different replicas interleave, so the
  browser could see a chunk before its node's `RUNNING`. With one emitting replica per socket, the
  order is the publish order.
- **Guard the assumption.** `TemporalModule` no longer exports `NotificationsGateway`, so only the
  Redis event handlers in the same module reach it. A request handler that emits through it would
  reach only the sockets of its own replica.
- **One room rule.** The room name comes from `flowRoomOf(userId, flowId)`, the helper the A11.2
  membership change (868mqc7w6, back PR #2092) adds with the same name and body, so the two PRs merge
  without a second copy. The e2e spec signs a JWT and provides `FlowAccessService`, so it passes
  before and after sockets must prove their user.

**Accepted trade-offs (from `/code-review`, 2026-11-06).**

1. **No redundancy while one replica's subscription is down.** Before, every replica re-broadcast,
   so a replica whose Redis subscriber dropped still got its sockets served by the others. Now the
   events published while that subscriber reconnects never reach that replica's sockets. ioredis
   resubscribes on reconnect, so the gap lasts as long as the reconnect.
2. **Duplicates during a rolling deploy.** While old tasks (broadcast) and new tasks (local) run
   side by side, a socket can still get one copy per old task plus one. It ends when the last old
   task drains.
3. **The spec waits 400 ms after the expected count.** A duplicate slower than that would pass. All
   negative controls failed inside that window on the local machine.

## Verification

- **Negative control (required).** Start two back processes against one Redis and connect one
  socket client to one of them. Publish one `room_stream_chunk`. On `main` today the client receives
  it twice. After the change it receives it once. Revert the change and watch the test fail.
- Repeat with the socket on the other replica, and with three replicas.
- Per node, `RUNNING` never arrives after `COMPLETED`.
- Count emitted versus received for a run with several streaming nodes: equal, with one, two and
  three replicas.

## Done when

With two and three back replicas, every status and every stream chunk reaches the browser once, and
the test that proves it fails with the change reverted.

## Result (2026-11-06, local)

1. `back/test/notifications-single-delivery.e2e-spec.ts` boots two and three replicas on one Redis
   with the real `RedisIoAdapter`, Redis transport, `TemporalController`, `NotificationsGateway` and
   `RouterController`, and publishes the way the worker does. It covers the socket on the first and
   the last replica, statuses, stream chunks, the chatbot relay, a three-node streaming run (order
   and count) and the completion stream. 16 tests pass.
2. Negative controls, each observed red and then restored:
   - Previous code: 14 of 16 fail, with 2 copies on two replicas and 3 on three.
   - Only the chatbot relay reverted: its 4 tests fail.
   - Only `sendToUser` reverted: the 6 status and run-order tests fail.
   - Only `sendStreamChunk` reverted: the 4 stream-chunk tests fail.
   - Completion handlers shared across replicas: the 2 completion tests fail.
3. Two real back processes (`node dist/main.js` on ports 3011 and 3012, one Redis): the client on
   either port receives 1 status, 2 chunks and 1 chatbot message, equal to what was published. With
   `.local` removed from the build, it receives 2, 4 and 2.
4. Run the spec against a Redis that no other back uses, because a running back joins the adapter
   and adds copies: `REDIS_PORT=6390 pnpm test:e2e test/notifications-single-delivery.e2e-spec.ts
   --forceExit`. `--forceExit` is needed because `RedisIoAdapter` never closes its Redis clients.
   The spec stops with a clear error when another process subscribes to the worker events on that
   Redis; an extra subscriber was added to prove it.
5. After `/simplify`, `/code-review` and `/security-review` (no security findings), the spec ran 16
   of 16 again in about 30 s, failed 14 of 16 with `.local` removed, and the same held on a copy of
   `develop` that already carries the A11.2 socket authentication.

## Result (2026-11-06, dev)

`develop` received only the three task commits by cherry-pick (`2fb443e1`), because `develop` is
409 commits ahead of `main`. The dev back ran one task (`api-task-definition-dev:2653`).

1. A socket signed in as a dev user, on flow runs started through the MCP:
   - Two Haiku nodes in a row: each status arrived once, in order, and 39 stream chunks arrived with
     no repeated chunk.
   - Seven runs of a two-node flow: each status arrived once per run.
2. Two-task check (the user scaled `api-service-dev` to two tasks, both on revision 2653 and healthy
   behind the load balancer): two sockets connected at once, and a two-node Haiku run sent each of
   them every status once, in order, and 27 stream chunks with no repeat. Both sockets got identical
   counts. On the old code every socket would have received two copies of each event, because both
   tasks receive every worker event.
3. **Finding outside this task.** In one of seven runs, the input node's `RUNNING` arrived after its
   `COMPLETED`. With one back task the delivery keeps the Redis order, so the swap happened when the
   back published them: `flux.service.ts` sends both through `NotificationPublisherService`
   (`sendStatusUpdate`), which does not wait for the publish. This is not a delivery defect and the
   change neither causes nor fixes it.

**Still open:** the production deploy.

## Files

`back/src/main.ts` (`connectMicroservice`, `RedisIoAdapter`) ·
`back/src/temporal/temporal.controller.ts` (`handleRoomUpdated`, `handleStreamChunk`) ·
`back/src/temporal/notifications.gateway.ts` (`sendToUser`, `sendStreamChunk`,
`relayStreamChunkToSocket`) · `back/src/adapters/redis-io.adapter.ts` ·
`worker/src/modules/notification/notification.service.ts` · front `ChatBot.tsx` (read only)
