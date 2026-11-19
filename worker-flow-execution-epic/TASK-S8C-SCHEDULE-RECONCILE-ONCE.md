# S8c — Run the schedule reconcile once per back task

**Goal:** a back task that boots runs the schedule reconcile once, in the main app, and the database
seed starts nothing but its own writes.

**Depends on:** nothing to build. Coordinates with A9b
([TASK-A9B-STALLED-API-RUN-ONE-OUTCOME.md](TASK-A9B-STALLED-API-RUN-ONE-OUTCOME.md)), which changes
`back/dev.sh`. **Added 2026-11-17** from the S8b production check
([TASK-S8B-SCHEDULE-ROLLOUT.md](TASK-S8B-SCHEDULE-ROLLOUT.md)). **Revised 2026-11-17:** the first
version blamed three modules that provide the registrars; that cause is false. ClickUp:
[868mw2u2t](https://app.clickup.com/t/868mw2u2t).

## Why

Datadog, from 2026-11-12 12:35 UTC: three back tasks booted (2026-11-12 12:38, 2026-11-12 14:18,
2026-11-13 14:29), and each logged `(Schedule Registrar) Reconciled 53 active schedule(s); 0
registered in this pass.` twice, 9 to 15 s apart. No `schedule_flag_read_failed` appeared.

### Cause

Read from back `origin/main` (`240b824f`) and confirmed by the CloudWatch timing below:

1. The three schedule registrars are providers of `AppApiModule` only
   (`back/src/app-api/app-api.module.ts:561-563`). `cronJobs.module.ts` and `internal.module.ts`
   keep their own `services` arrays and import `AppApiModule`, so Nest reuses one instance per
   context. The first version of this spec was wrong on this point.
2. `back/dev.sh` starts `dist/main.js`, waits for `/health`, then runs `node dist/seed.js` in the same
   container.
3. `back/src/seed.ts` calls `NestFactory.createApplicationContext(SeederModule)`, and
   `back/src/database/seeders/seeder.module.ts` imports the whole `AppModule`. Every `onModuleInit`
   runs a second time in that context, including `ScheduleRegistrarService.onModuleInit`
   (`schedule-registrar.service.ts:92`). The `reconcileSchedules` cron lock does not stop it, because
   the main app released the lock seconds earlier.

That gives two lines per task, which answers "why two lines, not three".

CloudWatch `/ecs/api-task-definition-prod` shows the gap: on the three boots above, "Seed worker:
main app healthy" to the seed start takes 8 to 12 s, which matches the 9 to 15 s between the two
`Reconciled` lines.

### What the seed context starts today

The seven seeder services inject only TypeORM repositories (`FeatureFlag`, `Flow`, `Folder`,
`ModelPrice`, `SystemAiModels`, `Product`, `UserProduct`, `Report`, `User`) and `Logger`. Because
`SeederModule` imports `AppModule`, the seed context also starts:

- Five boot hooks: `ScheduleRegistrarService`, `LegacyScheduleRegistrarService`, `TemporalService`,
  `ProxyService` and `RunMemoryTrackerService`.
- 17 `@Cron` methods.
- Seven Bull processors, including `api-v2` and `schedule`. They consume from the queues that every
  back task shares for as long as the seed process lives.

`@nestjs/bull` closes each queue on shutdown with `queue.close()` (`bull.providers.js:37`), which
waits for active jobs. A job that the seed context takes keeps the seed process alive until the job
ends. Whether the seed context has taken a production job is not measured.

### Measured cost

CloudWatch prod, 71 boots from 2026-10-18 to 2026-11-17, read-only:

| Step | Log lines | p50 | p90 | max |
|---|---|---|---|---|
| Main app boot | `Seed worker: waiting` → `main app healthy` | 10 s | 12 s | 14 s |
| Seed context boot (`AppModule` again) | `main app healthy` → `Starting database seeding` | 8.8 s | 12.6 s | 14.6 s |
| Seeding | `Starting database seeding` → `Seeding completed successfully` | 2.1 s | 5.6 s | 14.0 s |
| Context close and exit | `Seeding completed successfully` → `Seed worker: seed completed` | 3.6 s | 19.3 s | 21.7 s |
| Seed total | `main app healthy` → `Seed worker: seed completed` | 14 s | 37 s | 42 s |

The 2 s poll in `dev.sh` rounds the first row. One seed in 71 failed (non-fatal; cause not read). The
cause of the 17 to 22 s closes is not identified. The query, to repeat after the deploy:

```
fields @timestamp, @logStream, @message
| filter @message like /main app healthy|Starting database seeding|Seeding completed successfully|Seed worker: seed completed|Seed worker: seed failed/
| stats min(@timestamp) as t by @logStream, @message
| sort @logStream, t
| limit 3000
```

### Relation to A9b

On `fix/868mvdm50` (read 2026-11-17, A9b still in progress), `dev.sh` keeps the seed after `/health`,
now under `setsid`, and ends with `exec node ... dist/main.js`. Its comment gives the reason: "The
seed boots a full Nest context, so it waits for /health". S8c removes that reason:

- If A9b keeps the seed after `/health`, S8c removes the second reconcile and the queue consumers
  from a process that SIGTERM does not reach (`setsid` puts it in its own session).
- If A9b or a later task moves the seed before the app, every new task, including a scale-out,
  waits for the whole seed before it serves. Without S8c that wait is the seed total above (p50 14 s,
  p90 37 s), mostly an `AppModule` boot and close that the seeders do not use. The seed then becomes
  the first process to open the database, so it must apply pending migrations.

S8c works with either order. It does not change `dev.sh`; the order belongs to A9b.

## Scope

**In.**

1. `SeederModule` imports the TypeORM root connection and the seven seeder modules, and provides
   `Logger` and `Seeder`. It no longer imports `AppModule`.
2. The TypeORM root definition (`TypeOrmModule.forRootAsync` with `configOptions` and
   `dataSourceFactory: createMigratedDataSource`) moves out of `back/src/app.module.ts` into one
   exported definition that `AppModule` and `SeederModule` both import. It is not restated, so the
   seed keeps the migration runner and its advisory lock.
3. A unit test that walks the `SeederModule` import graph (`MODULE_METADATA` from `@nestjs/common`)
   and proves the requirements below.

**Out.**

| Item | Reason |
|---|---|
| The seed order in `dev.sh` | Owned by A9b |
| A guard in `ScheduleRegistrarService` that skips the seed context | Unneeded once the seed context has no registrar |
| The cause of the 17 to 22 s closes and the one failed seed | The fix removes the queues and connections a close waits for; measure again after the deploy before opening a task |
| Whether the seed context took production jobs | Does not change the fix, which removes the consumers |
| Seeded data and `seed.ts` | The rows and the entry point stay as they are |

## Requirements

| ID | Requirement |
|---|---|
| S8C-01 | WHEN the seed context boots THEN it SHALL contain no `ScheduleRegistrarService`, `LegacyScheduleRegistrarService` or `TemporalScheduleRegistrarService`. |
| S8C-02 | WHEN the seed context boots THEN no reachable provider SHALL carry Bull `@Processor` metadata or `@nestjs/schedule` cron metadata (`SCHEDULE_CRON_OPTIONS`), and `AppModule` and `AppApiModule` SHALL be unreachable from `SeederModule`. |
| S8C-03 | WHEN a back task boots with `repeatable_schedules` on THEN it SHALL log exactly one `(Schedule Registrar) Reconciled` line. |
| S8C-04 | WHEN the seed runs against a database with pending migrations THEN it SHALL apply them under the existing advisory lock before it seeds. |
| S8C-05 | WHEN the seed runs THEN it SHALL write the same rows as on `origin/main`, and a second run SHALL change nothing. |
| S8C-06 | WHEN the back deploys to production THEN the seed total SHALL be measured with the query above and recorded here against the baseline. |

Edge cases:

- WHEN the seed and the main app start migrations at the same time THEN the advisory lock in
  `run-migrations-exclusively.ts` SHALL let one run them and the other find none pending.
- WHEN the seed fails THEN `dev.sh` SHALL keep the app up, as today.

## Verification

1. Unit test for S8C-01 and S8C-02. Negative control: put `AppModule` back in `SeederModule.imports`,
   watch the test fail, then restore the import by edit.
2. Local, for S8C-04 and S8C-05: on an empty database, run `node dist/seed.js` before the app and
   confirm that the migrations apply and the seeded row counts match a run built from `origin/main`.
   Run it again and confirm nothing changes.
3. Local, for S8C-03: boot through `dev.sh` with `NODE_ENV=development` (the `WinstonLogger` prints to
   the console only then) and `repeatable_schedules` on, and count one `Reconciled` line. On
   `origin/main` the same boot prints two.
4. Dev, after the deploy: one `Reconciled` line per back boot in Datadog. Repeat the S8b schedule test
   (create every 2 minutes, update to every 3, delete) and get one run per tick.
5. Production, after the deploy: one `Reconciled` line per back task, including the daily second task
   around 14:17 UTC, and the seed total for S8C-06.

## Done when

S8C-01 to S8C-06 hold; schedule create, update, delete, pause and unpause work as before; S8b's
fail-closed mode resolution is unchanged; and the production seed total is recorded here.

## Files

`back/src/database/seeders/seeder.module.ts` · `back/src/app.module.ts` (TypeORM root moves out) · a
new shared TypeORM root definition under `back/src/database/` · a new spec next to `seeder.module.ts`.
Read, not changed: `back/src/seed.ts`, `back/dev.sh`, `back/src/database/run-migrations-exclusively.ts`.

**Estimate:** min 2 h, average 4 h, max 6 h.

## Implementation

Back branch `fix/868mw2u2t` (commits `142d2af3`, `69892da3`, `37e7a99a`), not merged to `develop` yet.

| Requirement | Where | Evidence |
|---|---|---|
| S8C-01 | `src/database/seeders/seeder.module.ts:12-25`; test `seeder.module.spec.ts:149` | The spec fails with the three registrars listed when `AppModule` is put back |
| S8C-02 | test `seeder.module.spec.ts:144`, `:155`, `:159`, `:163` | Same negative control: 7 Bull consumers, the boot hooks and `AppModule`/`AppApiModule` listed. A probe at `:139` proves the Bull and cron predicates still detect a consumer and an inherited cron |
| S8C-03 | `src/database/seeders/seeder.module.ts:14` (no `AppModule`) | Local boot through `dev.sh` with `NODE_ENV=development` and `repeatable_schedules` on: one `Reconciled` line; the same boot built from `origin/main` prints two, the second from the seed process |
| S8C-04 | `src/database/typeorm-root.module.ts:5-8`, shared by `src/app.module.ts:40` | On a copy of the local database with `SeedExecutionBudgetFlag1788460000000` un-applied, the seed re-applied it before seeding, on the branch and on `origin/main` alike |
| S8C-05 | the seeders are unchanged | With the seeded rows deleted from both copies, the branch and `origin/main` seeds wrote identical content (hash per table) and identical counts across 97 tables; a second branch run changed nothing |
| S8C-06 | back #2117 (merge `6f7f2de0`), released 2026-11-18 as `api-task-definition-prod:854` and `:855` (steady 12:28:31 UTC) | CloudWatch prod, read-only, 2026-11-18: seed total ("main app healthy" to "Seed worker: seed completed successfully") 3.05 s (12:22:46.447 to 12:22:49.500 UTC) and 2.85 s (12:26:21.755 to 12:26:24.607 UTC), against the 71-boot baseline p50 14 s, p90 37 s, max 42 s; no "seed failed" line. Each post-release task logs `AppApiModule dependencies initialized` once, against twice on every task before. The Datadog `Reconciled` count was not read (no Datadog access) |

**Dev check (2026-11-17).** The three commits were cherry-picked onto `develop` (`d1f70eca`), because `develop` lacks 17 commits that are on `main`. Dev ran `api-task-definition-dev:2682` (image `d1f70eca`, which also carries A9b's `dev.sh`) from 14:51 UTC. The registrar's Winston lines do not reach the dev CloudWatch group, so the count uses each context's `InstanceLoader` lines instead: the new task logs `AppApiModule dependencies initialized` once, where every earlier task that day logged it twice (app and seed). The seed took 1.1 s from "main app healthy" to "seed completed", against 5 to 8 s on the earlier dev boots. This also removes the `TypeORMError: Driver not Connected` from `[Scheduler]` in the seed process that the S8b dev check recorded. The S8b schedule test then ran on dev through the API, on "Jev 1 - Boolean question" (no delivery), schedule `ea8cea40-59f1-456b-904c-3a39815f29f3`:

| Step | Expected | Observed (`flows_logs`, `run_type = 'cronjob'`) |
|---|---|---|
| Create at 15:11:49, every 2 minutes | One run per tick | 15:12, 15:14, 15:16, 15:18: one run each, all successful |
| Update at 15:18:50 to every 3 minutes | The old interval stops | 15:21, 15:24, 15:27: one run each; none at 15:20, 15:22, 15:26 |
| Delete at 15:28:51 | No more runs | 0 runs through 15:34:03 (ticks 15:30 and 15:33 passed) |

The seed also compiles on its own: `seeder.module.spec.ts:181` builds `SeederModule` with a fake data source, so a seeder that injects a provider only `AppModule` supplied fails the test (observed with an unprovided token in `UserSeederService`).

Local seed time on the same database copy: 1.8 to 2.0 s on the branch, 20.4 to 23.3 s on `origin/main`. The branch seed also runs without Redis and without `AUTH_JWT_SECRET`.

An empty database cannot be used for S8C-04: on `origin/main` the migration chain fails at `AddImageGenerationToolPricing1788000000000` (`column sam.supportsImageGenerationTool does not exist`), with or without this change.

### Reviews

- `/simplify`: the spec walker was simplified. Nest's `DependenciesScanner` was tried in place of the hand-written walk and not kept: it is an internal API, and its negative-control run produced no result within 600 s.
- `/code-review` (medium): no correctness bug. Fixed: the compile test above, the predicate probe, inherited crons, module-class boot hooks and async imports. Not changed: `FlowSeederModule` and `FolderSeederModule` stay although `Seeder` does not use them (out of scope); the Biome import reorder in `app.module.ts` stays; `src/app-mcp/cli/create-dev-mcp-token.ts` still boots `AppModule` for a dev CLI, a separate case.
- `/security-review`: no findings. No TypeORM subscriber or provider-dependent transformer exists, so the seed context loses no control.
- `back/dev.sh:28` on `origin/main` still says the seed "boots a full Nest context". Left for A9b, which rewrites `dev.sh`.

### Production check (2026-11-18)

Deployed with A9b in the back deploy `6f7f2de0` (back #2117), `api-task-definition-prod:854` and then `:855`. Read-only, CloudWatch `/ecs/api-task-definition-prod`:

| Task | `AppApiModule dependencies initialized` | Seed ("main app healthy" to "seed completed") |
|---|---|---|
| `c81c08a8` (`:854`) | once, 12:22:44 UTC | 12:22:46 to 12:22:49 UTC, about 3 s |
| `d3821d91` (`:855`) | once, 12:26:20 UTC | 12:26:21 to 12:26:24 UTC, about 3 s |

Baseline on 71 prod boots: p50 14 s, p90 37 s, max 42 s. No `seed failed`. The `Reconciled` line goes to Datadog only and was not read here; one `AppApiModule` init per task means one reconcile per task.
