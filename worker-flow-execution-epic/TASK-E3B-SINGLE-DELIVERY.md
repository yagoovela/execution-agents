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

## Files

`back/src/main.ts` (`connectMicroservice`, `RedisIoAdapter`) ·
`back/src/temporal/temporal.controller.ts` (`handleRoomUpdated`, `handleStreamChunk`) ·
`back/src/temporal/notifications.gateway.ts` (`sendToUser`, `sendStreamChunk`,
`relayStreamChunkToSocket`) · `back/src/adapters/redis-io.adapter.ts` ·
`worker/src/modules/notification/notification.service.ts` · front `ChatBot.tsx` (read only)
