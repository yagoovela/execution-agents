# S8 — One fire per schedule, one run per cron, and a bus that is sized

**Goal:** running a second backend replica stops multiplying scheduled work — crons, user
schedules and the email poll alike.

**Depends on:** nothing. **Blocks:** running more than one backend replica, and B5.
**Severity:** high (review §9.3, §9.4, §9.5).

## Part 1 — the fourteen crons

`@Cron` is registered fourteen times across `back/src`, and there is no leader election: greps for
`leader`, `isLeader`, `CRON_ENABLED` or an advisory-lock guard return nothing. **Every cron fires on
every replica.**

Some of it is waste — five separate purges all at `EVERY_DAY_AT_3AM`, each running per replica,
against the same tables in the same minute. Some of it is not: `mail.service.ts` polls POP3
`EVERY_10_SECONDS` per replica, and `markStuckSpaceRunLogs` runs every ten minutes per replica.

**Scope.** One mechanism for all fourteen, not fourteen guards. Two viable shapes:
- **An advisory lock per job name**, taken at the top of each run and released at the end.
  `pg_advisory_xact_lock` is already used in the codebase (`oauth-token.repo.ts:7`), needs no new
  dependency, and degrades correctly — a replica that cannot take the lock simply skips.
- **A dedicated scheduler role**, one replica with cron enabled by env. Simpler, but it makes that
  replica special, and a deploy that loses it loses every cron silently.

**Recommendation: the advisory lock**, because nothing has to know how many replicas exist.

**In.** Stagger the 3AM cluster while you are there. Five purges starting in the same minute is a
self-inflicted load spike on the database this epic is already worried about.

## Part 2 — user-scheduled flows

Scheduled runs do not use a durable scheduler. They are registered in NestJS's in-process registry
— `schedulerRegistry.addCronJob` at `schedule.controller.ts:179` and `:332` — so each replica holds
its own copy and fires it independently. **N replicas means N runs of the same schedule, each
charged to the customer.**

Two defects in the same code, both to fix here:

1. **The re-registration hides in a getter.** `getAllSchedules()` (`:242`) is a plain method with no
   route decorator that walks every active schedule and registers crons as a side effect. Whatever
   calls it registers crons on that replica.
2. **The queue is not doing the work.** The cron callback does
   `await this.scheduleQueue.add('schedule-job', { … job: await this.fluxService.apiV2({ … }) })`
   (`:157–159`, `:309–311`). The run is **awaited as an argument to the enqueue call**, so the flow
   already executed synchronously inside the cron callback and only its result reaches the queue.
   Fixing the duplication without fixing this just duplicates it more efficiently.

**Scope.** Schedules become durable and fire once. **Use Temporal Schedules** — greps for
`ScheduleClient`, `scheduleClient` and `createSchedule` across the worker and `back/src/temporal`
return nothing, so the platform's native scheduling is unused, and it gives by construction exactly
what this part is otherwise building by hand: one fire per schedule regardless of replica count,
durability across restarts and deploys, plus pause, backfill and last-run visibility the in-process
registry cannot offer (review §11.3). The advisory lock from Part 1 stays the right answer for the
fourteen framework crons, which are internal maintenance and have no reason to become workflows. Either way the callback **stops awaiting the run**, so the scheduler owns the trigger and the
workflow owns the execution.

**Keep the zombie-cron check** at `:283–297` — stop, delete, soft-delete when the flow is gone. It
is the one part of this code already doing the right thing.

## Part 3 — Redis

Redis backs the Bull queues, the worker→backend pub/sub, and the delivery dedup keys. The dedup is a
correct pattern already (`SET key '1' EX 86400 NX`, run-scoped, `flux.service.ts:5030–5044`).

Two things to confirm from infrastructure, not from this repo:
- **Eviction policy.** Under `allkeys-lru` or `allkeys-random`, dedup keys are evictable, and the
  failure mode is duplicate customer emails and duplicate outbound webhooks. Dedup keys are
  correctness state, not cache. Separate them from cache, or set a policy that cannot evict them.
- **Sizing for after B5.** Parallel dispatch raises the pub/sub rate substantially. Today's
  headroom is not evidence for post-parallelism, and losing Redis loses admission, visibility and
  duplicate suppression at once.

## Part 4 — the POP3 poll

The email poll is one of the fourteen crons, so it fires every ten seconds **per replica**
(`mail.service.ts:132`). There is no message-id dedup and no lock — greps for `messageId`, `dedup`,
`lock` and `NX` return nothing. Messages are fetched, processed and only then deleted
(`deleteEmailsSequentially`, `:314`), so the window between fetch and delete spans the whole batch,
including enqueueing the runs.

**Be fair about today's risk.** POP3 requires the server to lock the maildrop exclusively for the
session, so a well-behaved provider refuses the second replica and duplicates may not occur now.
That is exactly the problem: **correctness depends on a lock this code does not take and cannot
observe.** Move the mailbox to IMAP or an API, or use a provider that permits concurrent sessions,
and the failure becomes duplicate runs charged to the customer, with nothing to catch it. Meanwhile
every replica past the first fails to acquire that lock every ten seconds.

**Scope.** Part 1's advisory lock covers the polling. Independently of it, dedup by message id
before enqueueing — the same `SET … NX` pattern already used for delivery
(`flux.service.ts:5030–5044`) — so a message that is somehow fetched twice still produces one run.
Two independent guards, because the failure they prevent is a charge to a customer.

**In.** Reconsider the ten-second interval while you are there. It is a poll against a mailbox, and
at one replica it is 8,640 connections a day.

## Verification

- **Negative control (required), Part 2.** Run two backend replicas locally, create one schedule,
  and count the runs. Two is the bug — see it before fixing it. Then confirm exactly one.
- **Negative control, Part 1.** Two replicas, one purge cron: confirm it executes once, and that
  the replica which skipped logged that it skipped rather than failing silently.
- Confirm the schedule callback returns without waiting for the run, and that the run still happens
  — the failure mode of fixing this carelessly is a schedule that enqueues nothing.
- **Part 4.** Deliver one message and confirm exactly one run, with two replicas polling. Then
  bypass the maildrop lock deliberately — process the same message twice — and confirm the message-id
  dedup still yields one run. The second half is the test that matters, because it is the one that
  survives a change of mail provider.
- Redis: with the eviction policy set, fill the instance past `maxmemory` and confirm a dedup key
  survives. An assumption about eviction is worth exactly as much as the test that proves it.

## Done when

Each cron runs once per tick regardless of replica count, each schedule fires once and the queue
owns the execution, the 3AM cluster is staggered, and the dedup keys are proven to survive memory
pressure.

## Files

`back/src/cronJobs/**` (fourteen `@Cron` sites) · `back/src/app-api/mail/mail.service.ts` ·
`back/src/app-api/schedule/schedule.controller.ts:157–159, 179, 242, 283–297, 309–311, 332` ·
`back/src/app-api/flux/flux.service.ts:5030–5044` · Redis/infra configuration
