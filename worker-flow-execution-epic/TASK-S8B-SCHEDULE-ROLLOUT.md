# S8b — Finish the schedule rollout and lock the last cron

**Goal:** with any number of back replicas, every user schedule fires once and every cron runs once
per tick.

**Depends on:** nothing. **Blocks:** running the back on more than one replica, which production
already does (`TASK-E3B-SINGLE-DELIVERY.md`, **Corrected premise**). **Added 2026-11-04** from the
replica audit of that day. ClickUp: [868mrv6cm](https://app.clickup.com/t/868mrv6cm).

## Why

`S8` built the fix and shipped it behind a flag. Read against back `main` `95533b9f` on 2026-11-04,
three gaps remain:

1. **The flag may still be off.** User schedules use Bull repeatable jobs only when
   `repeatable_schedules` is on. The migration `SeedRepeatableSchedulesFlag` seeds it `false`. With
   the flag off, `LegacyScheduleRegistrar` registers every schedule in each replica's in-process
   `SchedulerRegistry` at boot, so N replicas fire the flow N times and charge the customer N times.
   A schedule created or deleted while the flag is off changes only the replica that took the
   request (`schedule.controller.ts`, which reads `isRepeatableModeEnabled()` on each create and
   update), so a deleted schedule keeps firing on the other replica until it restarts. Nothing in
   the spec records the flag being turned on in production.
2. **A failed flag read falls back to the duplicating path.** `FeatureFlagsService.read` treats a
   read error as "off". If the read fails at boot, that replica registers the legacy crons even when
   the flag is on everywhere else.
3. **One cron has no lock.** `S8` counted fourteen `@Cron` sites and put each one under
   `CronLockService.runExclusively`. `handleNegotiatedContractRenewal` (cron
   `negotiatedContractRenewal`, `user_product.controller.ts`) was not among them: it calls
   `renewNegotiatedContracts()` with no lock, and that method reads a subscription and then writes
   `usedTokens: 0`. With two replicas both run at midnight. The second normally finds nothing to
   renew, but the read and the write race.

`expireMaintenanceNotice` also has no lock, but running it twice clears the same notice twice. It is
idempotent, so it stays as it is.

## Scope

**In — the rollout.**

1. The user reads `repeatable_schedules` in production. If it is on, record the date here and skip
   to step 4.
2. Turn it on in dev, restart, and confirm that each schedule has one repeatable and fires once per
   tick with two back processes.
3. Turn it on in production, then restart every back task. The flag is read at boot, so a task that
   booted with it off keeps its legacy crons until it restarts.
4. Confirm in production: one `api-v2` run per schedule tick, and zero legacy registrations in the
   boot log.

**In — fail closed.** When the flag cannot be read at boot, `LegacyScheduleRegistrar` registers
nothing and logs the error. A missed fire is recoverable; a double charge is not.

**In — the last lock.** `handleNegotiatedContractRenewal` runs inside
`CronLockService.runExclusively`, the same way as `productIntervalCheck` above it.

**Out.** Deleting `LegacyScheduleRegistrar`. `S8` left it as the flag's cleanup, and `C2`'s flag
table retires `repeatable_schedules`. Temporal Schedules stay `E4`.

## Verification

- **Negative control (required).** Two back processes against one database and one Redis, with the
  flag off: a schedule fires twice per tick. With the flag on: once. Then make the flag read throw
  at boot and confirm that, after the change, no legacy cron is registered. On `main` today it is.
- With two processes, `negotiatedContractRenewal` runs its body once per tick. Remove the lock and
  watch the test fail.
- Measure before refusing (PLAN §3.3.2) does not apply: nothing is refused.

## Done when

`repeatable_schedules` is on in production and every back task restarted after it, a failed flag
read registers nothing, `negotiatedContractRenewal` runs under the cron lock, and the dates are
recorded here.

## Result

**Rollout (steps 1 to 4).** The user confirmed on 2026-11-05 that `repeatable_schedules` is on in
production, since about 2026-09-29, a week after `S8` shipped. Every back task has restarted since
then, at least with the 2026-11-03 and 2026-11-09 deploys, so steps 2 and 3 are already done. Step 4
was measured on 2026-11-11 13:06 UTC with `868mrv6cm` query 6, which lists every flow and minute in
`flows_logs` (`run_type = 'cronjob'`, last 30 days) with more runs than the schedules that existed
for that flow at that minute: **0 rows**. The window covers the two back tasks that production runs
every day since 2026-10-28. The query was checked on dev first: 0 rows in 30 days, 1 row for an
injected duplicate run, and the real 2× to 4× double fires of March 2026 on 365 days. A minute whose
schedule row was hard-deleted counts as unverifiable, not as a failure, and only ticks with two or
more runs are listed. The boot-log check is replaced by this query: the legacy registrar logs nothing
when it registers.

**Fail closed and the last lock.** Back `fix/868mrv6cm` (`a8861164`, `a8810ed1`, `7974a82f`), no PR
yet.

- `FeatureFlagsService.isEnabledOrThrow` throws the read error that `isEnabled` turns into `false`,
  and shares its cache. `read` stays fail-open: 31 callers depend on it, and for some of them
  `false` is not the safe value (`superchat-access.service.ts` returns `!isEnabled(...)`).
- `LegacyScheduleRegistrarService.onModuleInit` reads `temporal_schedules` and, through the new
  `ScheduleRegistrarService.isRepeatableModeEnabledOrThrow`, `repeatable_schedules`. When either
  read throws it registers nothing and logs `schedule_flag_read_failed`.
- `handleNegotiatedContractRenewal` runs inside `CronLockService.runExclusively` with its own key,
  `negotiatedContractRenewal`, so `productIntervalCheck` at the same midnight keeps its own lock.
- Tests: 17 suites, 154 tests green, scoped to the touched folders. Each new test was seen to fail
  with the fix removed: the boot falls back to `isEnabled` (2 tests red), the registrar method
  swallows (1 red), the lock is removed (2 red), the lock shares the `handleCron` key (1 red),
  `isEnabledOrThrow` swallows (1 red). The fake lock releases at the end of the transaction, like
  `pg_try_advisory_xact_lock`, so the spec claims only "while one replica renews, the other skips".
- Reviews on 2026-11-11: `/simplify` applied 7 cleanups (efficiency: none). `/code-review`: 10
  findings, 3 fixed (the fake lock, the lock double's options, `HttpStatus`); 3 declined with
  reasons (no retry when legacy is the real mode, which is the decision above and is not production's
  mode; the lock's idle transaction, the same `S8` pattern as every cron; a boot-order gap that this
  change did not add); 4 are out of scope and wait for the user's decision. `/security-review`: no
  finding.

**Widened on 2026-11-11 (the user's decision).** The reviews found the same fail-open read on three
more paths. Two are fixed in this task; the third goes to `E4`.

- `ScheduleRegistrarService.resolveScheduleMode()` is now the one place that decides `temporal`,
  `repeatable` or `legacy`. It reads both flags with `isEnabledOrThrow`; when a read fails it logs
  `schedule_flag_read_failed` and throws `ScheduleModeUnavailableError`. It replaces
  `isRepeatableModeEnabled` and `isRepeatableModeEnabledOrThrow`, which have no callers left.
- Schedule create and update (`schedule.controller.ts`) resolve the mode **before** they save, bill or
  unregister anything. Before, `createWithBilling` and `updateWithBilling` ran first and a failed
  read then registered an in-process cron next to the Bull repeatable. Now the user sees "Could not
  read the schedule settings, so nothing was changed. Try again." and nothing changes. This is the
  only new refusal, and it fires only when the flag read itself fails, so no stored data is refused.
- Both boot paths call it. The Bull reconcile runs only in `repeatable` mode, the legacy registrar
  only in `legacy` mode, and an unreadable mode runs neither; the next boot of any replica
  reconciles, because `reconcile()` registers every missing schedule.
- Left for `E4`: the Temporal guard in `schedule.consumer.ts` (`triggerScheduledFlow`) still reads
  `temporal_schedules` with the fail-open `isEnabled`. While the flag is off in production (no
  migration creates its row, so it reads as off), failing closed there would only turn a flag-read
  blip into a skipped run. `E4` makes it fail closed before the flag goes on.
- `pause`, `unpause` and `upcoming` decide through the same method, so a failed read tells the user
  to try again instead of claiming the schedule is not on Temporal. The controller no longer reads
  flags itself.
- Tests: 17 suites, 164 tests green. New negative controls, each seen red: create reads the mode
  after saving (1 red), update reads it after saving (1 red), `resolveScheduleMode` reads fail-open
  (4 red), the temporal branch registers on Bull (2 red), `shouldUseTemporal` swallows the error (1
  red).
- Second `/code-review` (on the widened commit): 9 findings, 2 fixed (the pause path, the missing
  temporal-branch test). Declined: the consumer (`E4`), no retry at boot (decided above), 400 rather
  than 503 (the controller's existing `catch` sets the status for every error), two boot reads (the
  second hits the flag cache), the generic log text. Offered as a follow-up, already on `main`
  before this task: in create and update, a register or unregister call that throws after
  `createWithBilling` or `updateWithBilling` leaves the row saved and billed but registered wrongly,
  and a retried create returns the existing row without registering it.
- Not done: a source-scan spec that fails on an unlocked `@Cron`. Offered, not asked for.

## Files

`back/src/app-api/schedule/legacy-schedule-registrar.service.ts` ·
`back/src/app-api/schedule/schedule-registrar.service.ts` ·
`back/src/app-api/schedule/schedule.controller.ts` ·
`back/src/app-api/feature-flags/feature-flags.service.ts` (`read`) ·
`back/src/app-api/user_product/user_product.controller.ts` (`handleNegotiatedContractRenewal`) ·
`back/src/cronJobs/cron-lock/cron-lock.service.ts` (`runExclusively`)
