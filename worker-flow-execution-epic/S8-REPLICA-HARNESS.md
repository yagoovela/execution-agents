# S8 — running the two-replica negative controls locally

The defects S8 fixes only appear with **more than one backend replica**, and the default local
stack cannot produce one: `docker/devdb/docker-compose.devdb.yaml` pins `back` to `3001:3001`, which collides
under `--scale`, and sets `DISABLE_CRONS: 'true'`, which turns off the very crons under test. The
POP3 poll additionally returns early when `ENVIRONMENT === 'localhost'`, and there is no mail
server in the stack at all.

`docker-compose.replicas.yaml` is the override that removes all four obstacles. It widens the port
mapping to a range, turns the crons on, points the mailbox at a GreenMail container, and nothing
else — it is a test harness, not a second environment.

```bash
cd ~/enhanced
docker compose -f docker/devdb/docker-compose.devdb.yaml -f docker-compose.replicas.yaml up -d --scale back=2
```

Both replicas share one Postgres and one Redis, which is what makes the controls meaningful.

**Build from the right code.** `docker/back.Dockerfile` takes the superproject as its context and
copies `back/` out of it, so the image is built from whatever branch the **primary** `back`
checkout is on — not from a worktree. Before running any control below, confirm:

```bash
git -C back branch --show-current   # must be feat/868m0vkve, or you are testing other code
```

If it is on something else, either check the branch out there or point the build at the right
tree. A green control against the wrong branch is worse than no control.

## Control 1 — Part 1, the framework crons

Watch both replicas at once and confirm exactly one of them does the work per tick:

```bash
docker compose -f docker/devdb/docker-compose.devdb.yaml -f docker-compose.replicas.yaml logs -f back \
  | grep -E 'Purge|Cron Lock'
```

**Pass:** one replica logs the purge; the other logs `(Cron Lock) Skipped <job>: another replica
holds the lock for this tick.` The skip has to be **visible** — a silent skip and a crashed cron
look identical from outside, which is why the log line is part of the acceptance criteria.

**See it fail first.** In `back/src/cronJobs/cron-lock/cron-lock.service.ts` swap
`pg_try_advisory_xact_lock` for `pg_advisory_xact_lock`, rebuild, and re-run: the second replica
now *waits* for the first and then runs the job anyway, so the purge logs twice and nothing logs a
skip. That is the specific way this fix gets written wrong, and it is why the control exists.

## Control 2 — Part 2, user schedules

With the `repeatable_schedules` flag **off** (the default, and today's behaviour), create one
schedule and count the runs over a few fires:

```sql
SELECT COUNT(*) FROM space_run_logs
WHERE "flowId" = '<flow>' AND "createdAt" > now() - interval '5 minutes';
```

**Two per fire is the bug.** See it before fixing it. Then enable the flag:

```sql
UPDATE feature_flags SET enabled = true WHERE key = 'repeatable_schedules';
```

restart both replicas, and confirm **one run per fire**.

**Count runs that completed, not jobs enqueued.** After S3 a scheduled run passes the spend
ceiling and the tenant concurrency cap, so a queue-depth count can show one while two runs
happened, or two while one did.

Confirm the repeatable is single and shared, not per-replica:

```bash
docker compose -f docker/devdb/docker-compose.devdb.yaml -f docker-compose.replicas.yaml exec redis \
  redis-cli --scan --pattern 'bull:schedule:repeat:*'
```

One key per schedule, regardless of replica count.

## Control 3 — the schedule triggers without waiting for the run

Confirm the fire returns immediately and the run still happens: the `schedule` queue job should
complete in milliseconds while the `api-v2` job it created is still running. The failure mode of
fixing this carelessly is a schedule that enqueues nothing at all, so assert both halves — the
trigger completes **and** a run appears.

## Control 4 — Part 4, the POP3 poll

GreenMail's web UI is on `http://localhost:8080`; SMTP for injecting a message is on `3025`.

```python
import smtplib
from email.message import EmailMessage
m = EmailMessage()
m['From'] = 'sender@example.com'
m['To'] = '<flow-uuid>+<emailTriggerToken>@upload.fluxprompt.com'
m['Subject'] = 'harness'
m['Message-ID'] = '<harness-1@example.com>'
m.set_content('body')
smtplib.SMTP('localhost', 3025).send_message(m)
```

**First half:** one message, two replicas polling, exactly one run.

**Second half, and this is the one that matters.** POP3's exclusive maildrop lock may be what
produces that result, not our code — so bypass it deliberately and process the same message twice:

```bash
docker compose -f docker/devdb/docker-compose.devdb.yaml -f docker-compose.replicas.yaml exec redis \
  redis-cli DEL 'pop3-processed:<harness-1@example.com>'
```

Deleting the dedup key and re-delivering the message simulates a provider that permits concurrent
sessions. With the key present, the second delivery must produce **no** run. This half is the test
that survives a change of mail provider; the first half only tests the provider.

## Control 5 — Redis eviction (follow-up E5, runnable here)

```bash
docker run -d --rm --name s8-redis-evict -p 6399:6379 redis:7-alpine \
  redis-server --maxmemory 16mb --maxmemory-policy volatile-lru
```

Write a dedup key in the real shape (`SET k '1' EX 86400 NX`), fill past `maxmemory`, and watch it
disappear. Then repeat with `--maxmemory-policy noeviction` and confirm it survives and the filling
write fails instead. Production runs `volatile-lru` today; `E5` carries the numbers.

## Tearing down

```bash
docker compose -f docker/devdb/docker-compose.devdb.yaml -f docker-compose.replicas.yaml down
```

**If Redis will not bind.** `pnpm infra:up` leaves a `back-cache-1` container on 6379, and the
stack then fails with `Bind for 127.0.0.1:6379 failed: port is already allocated`. Do not stop the
other container — add a third override file mapping the harness Redis somewhere else
(`redis: ports: !override ['6380:6379']`) and point the probes at that port.

## Recorded run — 2026-09-18

Two `back` replicas against one Postgres and one Redis, image built from `feat/868m0vkve` (the
primary checkout was on another branch, so the context was assembled from the worktree — see
"Build from the right code"). Every control was run twice: once against the real code, and once
against a deliberately broken copy, so the failing result is observed rather than assumed. The
probe scripts live in `scripts/s8-controls/` and are run with
`npx ts-node -T -r tsconfig-paths/register <probe>` from the `back` worktree.

| Control | Real code | Broken copy (negative control) |
|---|---|---|
| 1 — cron lock | 1 executed, 1 `skipped-locked` | guard forced open: 2 executed, interleaved |
| 2 — schedule dedup | 1 repeatable entry, `id` = schedule id, 11 fires / 21 s alternating replicas | per-replica `jobId`: 2 entries, 20 fires |
| 2b — register/unregister | 1 entry → 0 entries | — |
| 3 — trigger without waiting | schedule job completes in 14–68 ms, one `cronjob` run per tick | consumer awaiting the run: 3023 ms, probe reports FAIL |
| 4 — inbound email dedup | 2 identical `Message-ID`s → 1 run; back-2 logs `Skipping duplicate inbound email` | 2 distinct `Message-ID`s → 2 runs, so the count is not stuck at one |
| 5 — Redis eviction | `noeviction`: keys survive, the filling write gets `OOM command not allowed` | `volatile-lru`: **0 of 100** dedup keys survived, 219 761 evictions |

Control 3 also ran end to end against the real stack: fires at 17:51:40, 17:52:00 and 17:52:20 —
exactly one per 20 s tick — each creating one `api-v2` job with `runType: 'cronjob'`. The reconcile
on boot ran on `back-1` only; `back-2` logged `Skipped reconcileSchedules`.

### The POP3 poll is the one cron the lock does not cover

`listPop3Emails` registers event handlers on the POP3 client and returns; the awaited part of the
job is a few milliseconds, so the transaction commits — and the advisory lock releases — while the
POP3 conversation is still in flight. Over 22 ticks of a 10-second poll, **4 ticks ran on both
replicas concurrently**. This is not a defect in `CronLockService`: Control 1 shows the lock is
exclusive whenever the job actually awaits its own work. It is a property of this job's shape.

What protects inbound email is therefore the Redis claim (`SET <key> '1' EX 86400 NX`) measured in
Control 4, not the cron lock, and the `api-v2` enqueue carries the same key as its `jobId` for a
second layer. Making the lock cover the poll would mean promisifying the whole POP3 conversation
and holding a Postgres transaction open across it for every tick — a worse trade than the claim
already in place. Recorded here so the next reader does not mistake the doubled poll for a
regression.

### Two measurement traps worth knowing

The first Control 2 run read a **halved** fire rate. The probe had attached to the real `schedule`
queue, which the two running replicas also consume, so half the fires were counted by them. Run
the schedule probes against an isolated queue name.

That halved rate was first misread as Bull mishandling a top-level `jobId` on a repeatable job,
and the `jobId` was moved into the `repeat` descriptor. It does not belong there: Bull's types
reject it (`TS2353`), the container crash-looped on the build, and a configuration matrix showed
every placement firing correctly at the requested interval. Top-level `jobId` — the committed
shape — is correct.

## Dev validation — 2026-09-21

`repeatable_schedules` was turned on in dev (`feature_flags`) and the API redeployed, because the
registrar reconciles in `onModuleInit` — **flipping the flag on a running process registers
nothing until the next boot.**

A temporary schedule (`0 */2 * * * *`, on a small owned flow) was inserted, the API restarted so
the boot reconcile picked it up, and the runs were counted in `flows_logs`:

```
14:14:07  14:16:05  14:18:02  14:20:03  14:22:05
```

Five consecutive ticks, one run each, two minutes apart, no duplicates. Four were stopped by S3's
run-spend ceiling and the fifth completed — irrelevant to what is being measured, but it does show
the schedule reaching the real execution path rather than a stub.

The row was then soft-deleted at 14:23:45 with **no restart**. Six further ticks passed (14:24
through 14:34) and produced **no runs**: the first fire after the deletion found no schedule and
removed its own repeatable, which is the self-healing path the consumer is written for. The probe
row was hard-deleted afterwards; dev is back to its one original schedule with the flag left on.

**What could not be checked from here.** The bastion cannot reach dev ElastiCache — a
`/dev/tcp` probe to `enhancedai-redis-dev…:6379` from the bastion reports unreachable, so its
security group does not admit it. Inspecting the `bull:schedule:repeat` keys in dev would need a
security-group change, which is why the evidence above is behavioural (runs in `flows_logs`)
rather than a key listing. The key listing was measured locally instead, in Control 2.

### The flag was not safe to flip, and that was fixed first

Flipping `repeatable_schedules` on a running process used to leave `delete()` taking the new path
only: it removed a repeatable that had never been registered and never stopped the in-process
`CronJob` created at boot. That job captures its payload in a closure and calls
`fluxService.apiV2` directly without re-reading the database, so a deleted schedule kept executing
and charging until the process restarted. `update()` had the mirror of it — two registrations
firing on two different intervals.

Only **registration** branches on the flag now; **teardown always runs on both paths**, and
`update()` re-registers on whichever path the flag selects, which also closes the "update never
re-registers" defect for the legacy path. `legacyRegistrar.stop` became idempotent, since
`SchedulerRegistry.getCronJob` throws on an unknown name. `schedule.controller.spec.ts` covers it
and was seen red first: with teardown back behind the flag, 4 of its 5 tests fail.
