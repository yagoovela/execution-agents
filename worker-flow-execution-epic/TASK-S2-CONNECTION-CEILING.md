# S2 — Size the database connections before adding workers

**Goal:** know, and enforce, how many Postgres connections the worker fleet can hold.

**Depends on:** nothing. **Blocks:** B5, and blocks adding worker replicas today.
**Severity:** critical (review §2.1).

## Why this is the first thing that breaks

`worker/src/modules/database/database.service.ts:13` constructs
`new Pool({host, port, user, password, database})` — **no `max`**. node-postgres defaults to ten
connections per pool, per process. The worker runs
`maxConcurrentActivityTaskExecutions: 10` (`worker.service.ts:22`), so a replica can hold ten busy
connections, and total connections scale linearly with replicas.

`max_connections` is a hard wall, and the wall is **shared with the API** — the failure mode is not
a slow worker, it is `too many clients already` for customer-facing requests. No connection proxy
appears in the compose files or the infra.

Every other task in this epic assumes more workers. This one decides whether more workers are
possible.

## Scope

**In.** An explicit `max` on the worker pool, plus `idleTimeoutMillis` and
`connectionTimeoutMillis`, so a saturated pool fails fast with a clear error instead of hanging an
activity until its `startToCloseTimeout`.

**Assumption to confirm — `max` equal to `maxConcurrentActivityTaskExecutions` plus two.** The two
are the headroom for the health check and for anything that opens a connection outside an activity.
Setting `max` higher than the activity concurrency cannot help: the worker cannot use connections
it has no activities to run.

**In.** The capacity arithmetic, written down: `max_connections` versus
`(api_replicas × api_pool) + (worker_replicas × worker_pool) + migrations + operators`. State the
current numbers and the number of worker replicas the current database supports. That sentence is
the deliverable — the config change is trivial once it exists.

**In.** A decision on a connection proxy. **Recommendation: PgBouncer in transaction mode**, because
it decouples replica count from connection count and is the only thing that makes "many workers"
open-ended. Note the constraint honestly: transaction mode forbids session-level state, and
`pg_advisory_xact_lock` — already used in `oauth-token.repo.ts:7` and planned for A7 — is
transaction-scoped, so it survives. Session-level advisory locks would not.

**Out.** Tuning Postgres itself. This task sizes the client side and states what the server side
must support.

## Verification

- **Negative control (required).** Saturate the pool deliberately — set `max` to 1 and run two
  concurrent activities — and confirm the second fails with a connection timeout naming the pool,
  rather than hanging until the Temporal timeout. The difference between those two failure modes is
  the difference between a diagnosable incident and a mysterious one.
- Measure actual concurrent connections per replica under a realistic flow, rather than assuming
  the configured maximum is reached.
- With the proxy, if adopted: confirm `pg_advisory_xact_lock` still behaves under transaction
  pooling, using the existing OAuth refresh path as the test.

## Done when

The pool has explicit limits, the capacity arithmetic is written down with real numbers, the
supported replica count is stated, and the proxy decision is recorded either way.

## Files

`worker/src/modules/database/database.service.ts:13` ·
`worker/src/modules/temporal/worker.service.ts:20–22` · infra/compose · `env-vars-sync`
