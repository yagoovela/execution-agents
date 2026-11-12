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

   **Observed once, locally (2026-11-06, during `E3b`).** Two back processes (`node dist/main.js`,
   back `origin/main` `90b263ea` plus the E3b change, installed TypeORM 0.3.31) booted together
   against the local database with one pending migration, `BatchStopAfterFailures1793131184072`.
   One process ran it and started. The other failed it with `column "stopAfterFailures" of relation
   "batch_processing_file" already exists`, then `TypeOrmModule` logged `Unable to connect to the
   database. Retrying (1)...`, found nothing pending on the retry, and started about 4 s later. So
   with one transactional migration, the loser fails and retries inside the same process; it does
   not hang. Not tested: a migration with `transaction = false`, a migration that is not safe to
   repeat, the retry budget running out, and ECS starting the new tasks together. This is evidence
   for the migrations scope below, not its negative control.

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

## Result (2026-11-10)

Branch `fix/868mrv6cx` (back), commits `0c7fe533` and `dd318af4`, on back `origin/main` `da769bbb`.

### Connection budget

Read on 2026-11-10 with read-only AWS access:

| Client | Pool per task | Tasks at the ceiling | During a rolling deploy | Source |
|---|---|---|---|---|
| Back | 30 (`TYPEORM_POOL_MAX` unset in `api-task-definition-prod:847`) | 3 (`api-service-prod`, min 1, max 3) | 6 (`maximumPercent` 200) | 90 / 180 |
| Worker | 12 (10 activities + 2) | 1 (no autoscaling) | 2 | 12 / 24 |
| MCP server | 0: it has no Postgres client and calls the back | 1 to 4 | — | 0 |
| Temporal server | 0: it uses its own instance, `enhancedai-temporal-db-prod` | — | — | 0 |
| People and tools (bastion, DBeaver) | not measured; allowance | — | — | 20 |
| **Total** | | | | **122 / 224** |

`enhancedai-db-prod` is a `db.t3.xlarge` (16 GiB) on `default.postgres14`, so `max_connections` is
`LEAST({DBInstanceClassMemory/9531392}, 5000)`: at most 1,802, and somewhat less after the memory RDS
reserves (read 1,716 on 2026-11-11). `superuser_reserved_connections` is 3. The worst case, 224 during a deploy at the ceiling,
is about 13 % of that. CloudWatch `DatabaseConnections`, daily maximum from 2026-10-27 to 2026-11-09:
peak 94 (2026-10-29 and 2026-11-01, days with two back tasks), daily average 3 to 8.

**Decision:** the budget fits. `TYPEORM_POOL_MAX` and the ceiling stay as they are. 

### Migrations at boot

**On `main` today the defect is silent.** TypeORM's `migrationsRun` has no lock between processes.
Each process reads the `migrations` table before any of them commits, so a migration with nothing
to collide on (an `INSERT` into a table with no unique key) is applied, and recorded, once per
process. Measured locally with a data-only migration and an existing `migrations` table:

| Processes booting together | Boots | Migration applied | `migrations` rows |
|---|---|---|---|
| 2 | 2 succeed | 2 times | 2 |
| 3 | 3 succeed | 3 times | 3 |

The 2026-11-06 observation (the loser fails and retries) holds only for a migration that changes the
schema, where the catalog collides. 0 of 345 migrations use `transaction = false`, and many are
data-only (`Seed*Flag`, `Add*Price`, `Deprecate*`).

**Fix: an advisory lock, not a separate deploy step.** `createMigratedDataSource`
(`back/src/database/run-migrations-exclusively.ts`) is the back's `dataSourceFactory`. It initializes
the data source and asks TypeORM whether a migration is pending. If none is, the task starts without
the lock, which is every boot that is not a deploy with a new migration. Otherwise it takes the
session lock `pg_advisory_lock(8720184, 1)` on its own connection, runs `runMigrations` with the
configured `migrationsTransactionMode`, and unlocks. A second task waits on the lock, then finds
nothing pending. When a migration fails, the unlock is skipped and the data source is destroyed,
which closes the session and frees the lock; Nest's retry starts from a clean pool. The
`cron-lock` namespace is 8720183, so the keys do not collide. `migrationsRun: true` in
`configOptions` still decides whether migrations run. A separate
deploy step was not chosen: the deploy runs through two paths (GitHub Actions and
`scripts/deploy-direct`), and both would need the new step.

**Verification.**

- `run-migrations-exclusively.integration.spec.ts`, against a real local Postgres, 5 tests: three
  processes and one pending data-only migration give one row, and the lock is free afterwards while
  the data sources stay open; a migration that fails after its `INSERT` leaves no row and a free
  lock; a boot with nothing pending starts while another session holds the lock; `migrationsTransactionMode: 'each'`
  runs a `transaction = false` migration (`CREATE INDEX CONCURRENTLY`); `migrationsRun: false` runs
  nothing.
- Negative controls in the spec, each restored by the inverse edit: no lock gives
  `Expected: 1, Received: 3`; no unlock makes the other boots wait on a lock that is never released;
  no pending check makes a boot wait with nothing to run; a forced `'all'` mode fails the
  `CREATE INDEX CONCURRENTLY` test.
- Two real back processes (`node dist/main.js`, ports 3011 and 3012) against the local database with
  one pending data-only migration: with the lock, both start, 1 row and 1 `migrations` row, and no
  advisory lock is left held; with the lock removed from `dist`, both start, 2 rows and 2
  `migrations` rows.
- `tsc --noEmit -p tsconfig.build.json` passes.
- Reviews: `/code-review` found 8 points. Fixed: the forced `'all'` transaction mode, a rollback or
  `destroy` error hiding the migration error, the lock taken at every boot, and a test that could not
  see a leaked lock. Declined: a `lock_timeout` (the ECS health check already bounds the wait, and a
  timeout would turn a long migration into a restart loop); the CLI `MyDataSource` running
  `migration:run` without the lock (prod migrates only at boot); the spec needing a local Postgres
  (the convention of every `*.integration.spec.ts`). `/security-review`: no finding.
- Dev: no migration name recorded twice (380 rows, 380 names). Production: 0 rows (see below).

### Production (2026-11-11)

Back #2106 merged at 12:29 UTC (`68d7ed73`) and went live at 12:36 UTC on
`api-task-definition-prod:849`. The same deploy carried #2102's `ActivateGptImage15` migration,
which ran once under the new lock: its 4 catalog prices exist once. Read at 13:06 UTC:

- `migrations` names recorded more than once: 0 rows. No boot migration ever ran twice in
  production, so nothing needs to be cleaned up.
- `SHOW max_connections`: 1,716. The worst case, 224, is 13 % of it.
- Back log since 12:30 UTC: 0 `QueryFailedError` and 0 `ERROR`.

### Ceiling

On 2026-11-10 the database and the boot hold the current ceiling of **3** back tasks. Autoscaling to
3 is fully confirmed once `S8b` and `S10` ship, and `S4b` if `execution_budget` is on in production.
`E3b` shipped on 2026-11-09.

## Files

`back/src/config/config.service.ts` (`TYPEORM_POOL_MAX`, `migrationsRun`) · `back/src/main.ts` ·
`worker/src/modules/database/database.service.ts` · the back's production task definition and
autoscaling policy (read only)
