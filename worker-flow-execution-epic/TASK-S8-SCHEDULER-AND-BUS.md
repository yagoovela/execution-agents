# S8 — One fire per schedule, one run per cron

**Goal:** running a second backend replica stops multiplying scheduled work — crons, user
schedules and the email poll alike.

**Depends on:** nothing. **Blocks:** running more than one backend replica, and B5.
**Severity:** high (review §9.3, §9.4, §9.5).

> **Amended 2026-09-18, before implementation.** Four things in the first draft were wrong or
> stale, and they are corrected **in place** below rather than silently: the cron count, the size
> of the 3AM cluster, the advisory-lock precedent, and the lock function itself. Part 2's mechanism
> was decided (`D26` — Bull repeatable jobs, not Temporal Schedules yet) and Part 3 was split out
> into [`E5`](./TASK-E5-REDIS-POLICY-AND-SIZING.md). The durable-scheduler half of Part 2 became
> [`E4`](./TASK-E4-TEMPORAL-SCHEDULES.md), blocked on `B4`. Everything re-verified against
> `back@origin/production` on 2026-09-18.

## What is actually there

Two schedulers live in the backend, with nothing in common. The first draft blurred them, and the
blur is what made Part 2 look like it needed Temporal.

| | **Framework crons** | **User schedules** |
|---|---|---|
| what | internal maintenance: purges, the email poll, model sync | "run this flow every Monday at 08:00", created by the customer |
| where | `@Cron` from `@nestjs/schedule` | `schedulerRegistry.addCronJob` in `schedule.controller.ts` |
| who pays | nobody | **the customer pays every fire** |
| mechanism | advisory lock (`D12`) | Bull repeatable jobs (`D26`) |

## Part 1 — the framework crons

**Corrected 2026-09-18: there are fourteen active `@Cron` sites, not thirteen.**
`syncAiModelsFromGateway` (`EVERY_DAY_AT_4AM`) landed after the first draft. A fifteenth, in
`updateTechnologiesFromSheets.service.ts`, is commented out. There is no leader election — greps
for `leader`, `isLeader` and `CRON_ENABLED` return nothing. **Every cron fires on every replica.**

**Corrected: the 3AM cluster is six purges, not five** — `purgeCanceledSubscriptions`,
`purgeMcpIdempotencyKeys`, `purgeMcpTokens`, `purgeNodeExecutions`, `purgeSpaceRunLogs`,
`purgeZapierWebhookPayloads`. At two replicas that is twelve concurrent purges against the same
tables in the same minute.

**Not in the first draft, and it is the worst of the fourteen:** `chargeUsersPerClonedVoice`
(08:00 daily) calls `productService.chargeUserProduct`. It **debits customers**, and it is one of
the eight with no guard at all. Duplicated, it is a duplicated charge — not waste, a refund.

**A partial guard already exists, and the first draft missed it.** `DISABLE_CRONS` is checked at
the top of six of the fourteen (`purgeCanceledSubscriptions`, `purgeMcpIdempotencyKeys`,
`purgeMcpTokens`, `purgeNodeExecutions`, `purgeZapierWebhookPayloads`, `syncAiModelsFromGateway`)
and is declared in `.env.example` — twice, which is its own small bug. It is all-or-nothing: it
can turn every cron off, it cannot say "on one replica only". The new helper **absorbs** it rather
than sitting beside it as a second guard.

**Scope.** One mechanism for all fourteen, not fourteen guards. An **advisory lock per job name**
(`D12`), taken at the top of each run: it needs no new dependency and nothing has to know how many
replicas exist. A dedicated scheduler replica was considered and rejected in `D12` — it makes one
replica special, and a deploy that loses it loses every cron silently.

**Corrected, and this one changes the code.** The first draft cited `oauth-token.repo.ts` as the
existing precedent. **That file does not exist.** The three real sites are `flow-node.service.ts`
(twice) and `session-state.service.ts`, and all three use **`pg_advisory_xact_lock`**, which
**blocks** — it waits for the holder and then proceeds. Copying that precedent produces a losing
replica that waits for the winner's transaction and then runs the job anyway, which is the exact
defect this part exists to remove. The lock here must be **`pg_try_advisory_xact_lock`**, which
returns a boolean and lets the loser skip. It is used nowhere in the codebase today, so there is no
precedent to copy and the choice has to be made deliberately.

**In.** Stagger the 3AM cluster. Six purges in one minute is a self-inflicted load spike on the
database this epic is already worried about.

## Part 2 — user-scheduled flows

Scheduled runs are registered in NestJS's in-process registry at two sites in
`schedule.controller.ts` — `create()` and `getAllSchedules()` — so each replica holds its own copy
and fires it independently. **N replicas means N runs of the same schedule, each charged to the
customer.**

**Corrected: `getAllSchedules()` has exactly one caller — the controller's own constructor**, as a
fire-and-forget promise. The first draft said "whatever calls it"; in fact the registration happens
once, at boot. It is still a plain method with no route decorator that registers crons as a side
effect, and it is still wrong, but the blast radius is boot, not arbitrary callers.

Four defects in this code, all in scope:

1. **The queue is not doing the work.** The callback does
   `scheduleQueue.add('schedule-job', { … job: await this.fluxService.apiV2({ … }) })`. The run is
   **awaited as an argument to the enqueue call**, so the flow already executed synchronously
   inside the callback and only its result reaches the queue. Fixing the duplication without
   fixing this just duplicates it more efficiently.
2. **`update()` never re-registers the cron.** Changing a schedule's interval does nothing until
   the process restarts. Not in the first draft.
3. **The registry is keyed by `schedule.name`**, which is user-supplied and not unique. Two
   schedules with the same name collide, and `create()` for a name already registered at boot
   throws. The durable id must be `schedule.id`. Not in the first draft.
4. **The two sites send different payloads.** `create()` sends `{...body, spaceId}` with `userId`;
   `getAllSchedules()` sends `{...schedule, webhook: true, spaceId}` with `socketId`. The same
   schedule behaves one way before the first restart and another way after. The entity shape is
   the survivor. Not in the first draft.

And a fifth thing, which is why "the queue owns the execution" needs a decision and not just a fix:
`ScheduleConsumer` **only emits a socket event**, and only when `data.userId` is set — which only
`create()` sets. Boot-registered schedules therefore notify nobody. The queue does not execute and
does not reliably notify.

**Scope — `D26`, settled 2026-09-18: Bull repeatable jobs.** Bull 4.16.5 is already a dependency
and `ApiV2Queue` / `ApiV2QueueProcessor` are already in production (`src/jobs/apiV2Job/`), with
`ApiV2QueueModel.params` already carrying exactly the fields the callback passes today. The
schedule state moves out of the per-replica `SchedulerRegistry` and into Redis, which Bull already
manages and which dedupes a repeatable by its repeat key regardless of how many replicas
registered it.

What that buys, beyond stopping the duplication: the "callback stops awaiting the run" clause
becomes **structural** rather than a discipline, because there is no callback left — the processor
is the execution. `getAllSchedules()` leaves the codebase, taking defects 2, 3 and 4 with it, and
`update()` and `delete()` become `removeRepeatable` + `add`.

**Corrected 2026-09-19, after implementation.** Two names in that sentence do not in fact leave,
and the original wording asked for something the chosen mechanism forbids.

The `schedule` **queue is the mechanism**, not a casualty of it: a Bull repeatable job lives in a
queue, so this queue now carries one repeatable per user schedule and `ScheduleConsumer` is what
processes them. What is retired is the **old shape** — the callback that awaited a run, and the
boot-time socket emit. The consumer that remains re-reads the schedule from the database,
unregisters itself when the schedule or its flow is gone, and enqueues the run without waiting for
it (measured: 14–68 ms per fire, one `api-v2` run per tick).

`SchedulerRegistry` survives in `legacy-schedule-registrar.service.ts` because §3.2 requires this
to ship behind a flag that is seeded **disabled** — with `repeatable_schedules` off, the old
in-process path is the one that runs, so deleting it would ship a flag with nothing behind one of
its two sides. It leaves the codebase when the flag is on in every environment; that removal is
the flag's cleanup, not this task's.

**Boot notification is deliberately dropped** (decided 2026-09-18): the socket emit was already
dead for every boot-registered schedule, so preserving it would mean building behaviour that never
worked rather than keeping behaviour that did.

**Why not Temporal Schedules, which the first draft recommended.** A Temporal Schedule can only
trigger a workflow, and the worker has none that runs a whole flow — that is `B4`, three waves
away. Shipping it here would have meant a bridge workflow plus an internal endpoint, both deleted
when `B4` lands. Temporal is the right destination and `E4` is where it goes; what it adds over
this — pause, backfill, last-run state, durability that does not depend on Redis — is `E4`'s
deliverable, and is honestly not delivered here.

**Keep the zombie check** — stop, delete, soft-delete when the flow is gone. It is the one part of
this code already doing the right thing. It becomes a reconciliation over the `schedule` table at
boot, which is also what recovers the repeatables if Redis is ever lost: **the table stays the
source of truth**, Redis only holds the timer.

## Part 3 — Redis

**Split out on 2026-09-18 into [`E5`](./TASK-E5-REDIS-POLICY-AND-SIZING.md).** It is an
infrastructure change with no application code in it, and the measurement says it is debt rather
than an incident: production runs `volatile-lru`, which *can* evict the TTL-bearing dedup keys, but
there have been **zero evictions in fourteen days** at 1.9% memory and 1.8% engine CPU. Holding a
replica-safety fix for a defect that has never fired is the wrong trade. `E5` carries the numbers.

## Part 4 — the POP3 poll

The email poll is one of the fourteen crons, so it fires every ten seconds **per replica**
(`mail.service.ts`). There is no message-id dedup and no lock. Messages are fetched, processed and
only then deleted (`deleteEmailsSequentially`), so the window between fetch and delete spans the
whole batch, including enqueueing the runs.

**Be fair about today's risk.** POP3 requires the server to lock the maildrop exclusively for the
session, so a well-behaved provider refuses the second replica and duplicates may not occur now.
That is exactly the problem: **correctness depends on a lock this code does not take and cannot
observe.** Move to IMAP or an API, or to a provider that permits concurrent sessions, and the
failure becomes duplicate runs charged to the customer, with nothing to catch it.

**Scope.** Part 1's advisory lock covers the polling. Independently of it, dedup by message id
before enqueueing.

**Corrected 2026-09-19, after implementation.** This paragraph originally ruled out `SET … NX` and
asked for the deterministic Bull `jobId` alone. The `jobId` alone does not hold: the enqueue sets
`removeOnComplete`, so once the job is cleaned up Bull frees the id and a redelivery of the same
message enqueues a second run. The claim is therefore a Redis `SET <key> '1' EX 86400 NX` keyed on
`Message-ID` (sha256 of the raw message when the header is absent), **and** the same key rides
along as the `api-v2` `jobId` — the two independent guards the paragraph below asks for, one
durable for 24 hours and one for as long as the job exists. Two guards, because the failure they
prevent is a charge to a customer.

Measured with two replicas polling one GreenMail mailbox: two deliveries of one `Message-ID`
produce one run and the second replica logs `Skipping duplicate inbound email`; two distinct
`Message-ID`s produce two, so the count is not stuck at one.

**The lock does not cover this poll, and that is recorded rather than papered over.**
`listPop3Emails` registers POP3 event handlers and returns, so the transaction commits — and the
advisory lock releases — while the conversation is still in flight; 4 of 22 ticks ran on both
replicas at once. `CronLockService` is exclusive whenever the job awaits its own work (Part 1's
control proves it), so the fix would be promisifying the whole POP3 conversation and holding a
Postgres transaction open across it every tick. What protects inbound email is the claim above.

**In.** Reconsider the ten-second interval. At one replica it is 8,640 mailbox connections a day.

## Verification

Every negative control below needs two backend replicas locally, and the local stack cannot do
that today: `docker-compose.devdb.yaml` pins `back` to `3001:3001` and sets `DISABLE_CRONS: 'true'`.
**Building that harness is part of this task**, as a compose override — `--scale back=2`, crons on,
plus a GreenMail container for Part 4, because the poll also returns early when
`ENVIRONMENT === 'localhost'` and there is no POP3 server in the stack.

- **Negative control (required), Part 2.** Two replicas, one schedule: count the runs. Two is the
  bug — see it before fixing it. Then confirm exactly one. **Count runs that completed, not jobs
  enqueued:** after `S3`, a scheduled run passes the spend ceiling and the tenant concurrency cap,
  so an enqueued-job count measures the wrong thing.
- **Negative control, Part 1.** Two replicas, one purge cron: confirm it executes once, and that
  the replica which skipped **logged** that it skipped rather than failing silently. Then plant the
  blocking variant (`pg_advisory_xact_lock`) and confirm the control goes red — that is the
  specific way this fix gets written wrong.
- Confirm the schedule callback returns without waiting for the run, and that the run still
  happens — the failure mode of fixing this carelessly is a schedule that enqueues nothing.
- **Part 4.** Deliver one message and confirm exactly one run, with two replicas polling. Then
  bypass the maildrop lock deliberately — process the same message twice — and confirm the
  message-id dedup still yields one run. The second half is the test that matters, because it is
  the one that survives a change of mail provider.
- `update()` changes a live schedule's interval without a restart, and `delete()` leaves no
  orphaned repeatable behind.

## Done when

Each cron runs once per tick regardless of replica count, each schedule fires once with the queue
owning the execution, the 3AM cluster is staggered, the POP3 poll is deduped by message id, and
the two-replica harness exists in the repo so the next person can re-run every control above.

## Files

`back/src/cronJobs/**` (fourteen `@Cron` sites) · `back/src/app-api/mail/mail.service.ts` ·
`back/src/app-api/schedule/schedule.controller.ts` (`create()`, `update()`, `delete()`,
`getAllSchedules()`) · `back/src/app-api/schedule/schedule.consumer.ts` (rewritten: it processes the repeatable) ·
`back/src/jobs/apiV2Job/` (the repeatable registration) · `back/src/app-api/feature-flags/`
(the §3.2 flag — the module is already in production; do not add an env var for it) ·
`docker-compose.devdb.yaml` + the two-replica override
