# S11 — Size the database and the boot for the back's replica ceiling

**Goal:** the back's autoscaling ceiling is a number the database and the boot can hold, and the
number is recorded.

**Depends on:** nothing. **Blocks:** confirming the back's autoscaling ceiling. **Added 2026-11-04**
from the replica audit of that day. ClickUp: [868mrv6cx](https://app.clickup.com/t/868mrv6cx).

## Why

Production autoscales the back from one to three tasks on CPU (`api-autoscaling-prod`, target
55 %), and it reaches two every day (`TASK-E3B-SINGLE-DELIVERY.md`, **Corrected premise**). Two
things nobody has checked against that ceiling, read against back `main` `95533b9f` and worker
`main` on 2026-11-04:

1. **Database connections.** Each back task opens up to `TYPEORM_POOL_MAX` connections (default
   30, `config.service.ts`) per data source. Each worker task opens up to 12 (`S2`,
   `database.service.ts`). At the ceiling that is about 30 × 3 for the back plus 12 per worker task,
   plus the MCP server, the Temporal server and any other client. Nobody has compared that sum with
   the production `max_connections`.
2. **Migrations at boot.** `migrationsRun` is `true`, and TypeORM 0.3.28 runs all pending
   migrations in one transaction, with no lock between processes. When a deploy starts two or three
   new tasks together, each one tries to run the same pending migrations. The first commits; the
   others either fail on a duplicate object and restart, or wait on a table lock. Nobody has
   checked which one.

## Scope

**In — connections.**

1. The user reads `SHOW max_connections` and the peak of `pg_stat_activity` in production.
2. Write the budget here: back pool × back ceiling + worker pool × worker count + every other
   client, against `max_connections` minus the reserved superuser connections.
3. If the budget does not fit, lower `TYPEORM_POOL_MAX` or the ceiling, and record which and why.

**In — migrations.** Prove what happens when two back processes boot together with one pending
migration. If one fails or the boot hangs, make the migration run once: take a Postgres advisory
lock around `runMigrations`, or run migrations as a separate step of the deploy before the tasks
start. Record the choice.

**In — the decision.** Record the ceiling the back may autoscale to (today: 3), with the date and the
tasks it waited for (`E3b`, `S8b`, `S10`, and `S4b` when its condition holds).

**Out.** Changing the autoscaling policy itself without the user's decision.

## Verification

- **Negative control (required).** Two back processes boot together against a dev database with one
  pending migration. Record what happens on `main` today. After the change, the migration runs once
  and both processes start. Remove the lock and watch the test fail.
- The connection budget is written here with the production numbers and the date they were read.

## Done when

The connection budget fits `max_connections` at the recorded ceiling, two back tasks booting
together run a pending migration once, and the ceiling and the date are recorded here.

## Files

`back/src/config/config.service.ts` (`TYPEORM_POOL_MAX`, `migrationsRun`) · `back/src/main.ts` ·
`worker/src/modules/database/database.service.ts` · the back's production task definition and
autoscaling policy (read only)
