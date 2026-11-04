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

## Files

`back/src/app-api/schedule/legacy-schedule-registrar.service.ts` ·
`back/src/app-api/schedule/schedule-registrar.service.ts` ·
`back/src/app-api/schedule/schedule.controller.ts` ·
`back/src/app-api/feature-flags/feature-flags.service.ts` (`read`) ·
`back/src/app-api/user_product/user_product.controller.ts` (`handleNegotiatedContractRenewal`) ·
`back/src/cronJobs/cron-lock/cron-lock.service.ts` (`runExclusively`)
