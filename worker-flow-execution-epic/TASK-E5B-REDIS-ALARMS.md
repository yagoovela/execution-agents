# E5b — Alert before the prod Redis fills, gets slow or runs out of CPU

**Goal:** someone is told before the prod Redis fills up and refuses writes, when a new writer
stores keys without a TTL, and when Redis gets slow or runs out of CPU.

**Depends on:** nothing. **Added 2026-11-11** when `E5` closed: `E5` switched every environment to
`noeviction` and left the alarms open. ClickUp: [868mvfwr4](https://app.clickup.com/t/868mvfwr4).

## Why

Under `noeviction` a full Redis refuses writes instead of silently dropping the dedup keys. That is
only an improvement if someone is watching memory. On 2026-11-17 dev, staging and prod all run
`enhancedai-valkey8-noeviction` on all three nodes (`in-sync`, read-only), and no
`Enhancedai-Redis-*` alarm or Redis SNS topic exists.

**Latency, added 2026-11-13.** The S4b production check
([TASK-S4B-SHARED-CHAIN-BUDGET.md](TASK-S4B-SHARED-CHAIN-BUDGET.md)) found `Redis command timed out`
in the prod back every day. Measured on 2026-11-13 (read-only, last 14 days, 5-minute points):

- Redis itself is fast. On the prod primary, read p99 never passed 1 ms and write p99 never
  passed 2 ms, and engine CPU never passed 4%, also at the 14:00 UTC peak.
- The timeouts happen in the back. `withRedisCommandTimeout` (`back/src/app-api/rate-limit/redis-command-timeout.ts`)
  rejects after a 250 ms `setTimeout`. When the back's event loop is blocked for 250 ms or more, the
  timer fires before the reply is read, even though Redis answered in under 2 ms.
- The timeouts come in one burst a day, weekends included, between 14:05 and 14:20 UTC: 1,700 in
  14 days, up to 100 in one 5-minute period. That points at work scheduled at 14:00 UTC in the back,
  not at customer traffic.

So a server-side latency alarm would not have caught this burst, and it is still worth having: like
the memory alarm, it stays quiet today and fires when Redis itself degrades. The burst needs its own
task in the back.

**Prod only, without `Evictions`, decided 2026-11-17.** `E5` decided three alarms in every
environment, and 2026-11-13 raised that to five. On 2026-11-17 the scope became four alarms in prod:

- **No alarm in dev or staging.** Nobody acts on a dev or staging Redis alert, and both run far
  from every threshold (see **Baseline**).
- **No `Evictions` alarm.** Under `noeviction` Redis never evicts a key: a full Redis refuses
  writes, which `Memory-Usage` already reports first. `Evictions` can only rise above 0 if the
  parameter group changes, and `alarm-baseline.sh` prints the parameter group of every node.
  Creating the alarm with its actions disabled saves nothing: CloudWatch bills an alarm for as long
  as it exists, whether its actions are enabled or not.

## Scope

**In.** Four alarms on `enhancedai-redis-prod`:

| Alarm | Metric | Rule | Alarm metrics |
|---|---|---|---|
| `Enhancedai-Redis-Memory-Usage-PROD` | `DatabaseMemoryUsagePercentage` (Maximum) | > 50% for 2 × 300s | 1 |
| `Enhancedai-Redis-Volatile-Keys-Gap-PROD` | metric math `CurrItems − CurrVolatileItems` | above `NO_TTL_CEILING`, not set yet (see **Open decisions**) | 2 |
| `Enhancedai-Redis-Latency-PROD` | metric math: `MAX` of `SuccessfulReadRequestLatency` and `SuccessfulWriteRequestLatency` (`p99`) over the three nodes | > 10,000 µs (10 ms) for 3 × 300s, missing data not breaching | 6 |
| `Enhancedai-Redis-Engine-CPU-PROD` | metric math: `MAX` of `EngineCPUUtilization` (Maximum) over the three nodes | > 80% for 3 × 300s | 3 |

`Latency` and `Engine-CPU` take the `MAX` over the three nodes, so they keep working when another
node becomes primary; only the primary serves requests, so the replicas send no latency data.
`Memory-Usage` and `Volatile-Keys-Gap` read the primary, `enhancedai-redis-prod-001`, which is
safe while `AutomaticFailover` stays disabled.

Each alarm and recovery notifies `Enhancedai-Redis-Alerts-PROD`, a new email topic, so Redis alerts
do not reach the external subscribers of the existing topics.
The alarm names end in `-PROD`, like the other alarms of the account.

**Scripts.** All three live in `scripts/e5-controls/` and use the AWS profile of the caller's
shell. The user runs every AWS write.

- `apply-prod.sh <step>` is the one to run. It reads the recipient and `NO_TTL_CEILING` from
  **Decided** below, so the values live only in this spec, and runs four steps in order:
  - `check` (read-only) runs `check-alarms.sh 14`.
  - `apply` prints the account, runs `check`, prints the commands, asks for the word `apply`, then
    runs `create-alarms.sh` with `APPLY=1`.
  - `verify` (read-only) fails unless the email subscription is confirmed and each alarm matches
    what `create-alarms.sh` would create: threshold, periods, metrics, nodes, and the topic on both
    `ALARM` and `OK`.
  - `fire-test` runs `verify`, asks for the word `fire`, then, alarm by alarm, forces `ALARM` with
    `set-alarm-state` and waits up to 10 minutes for the next evaluation to return it to `OK`.
- `NO_TTL_CEILING=<n> create-alarms.sh prod <email>` creates the topic, the email subscription and
  the four alarms. It prints the commands and changes nothing unless `APPLY=1` is set. It refuses
  any environment other than `prod` and a missing or non-numeric `NO_TTL_CEILING`. It reads the
  primary and the three nodes from the replication group when it runs.
- `NO_TTL_CEILING=<n> check-alarms.sh [days]` is read-only. It takes the four alarms the first
  script would create, validates their `PutMetricAlarm` parameters offline against the API model
  (types, required fields, `ComparisonOperator`, `TreatMissingData`), checks the metric math rules
  (at most 10 metrics, exactly one series returned), then runs the same queries with
  `get-metric-data`. It fails when a query returns no data or when the alarm's own rule (for
  example 3 of 3 points above the threshold) would have fired in the window, and it prints the
  single-point and the sustained maximum.

**No downtime.** Applying creates an SNS topic, a subscription and four CloudWatch alarms that read
metrics ElastiCache already publishes. Redis is not touched: no restart, no parameter change.
`fire-test` changes only the alarm state, and sends 4 `ALARM` and 4 `OK` emails to the recipient,
so tell the team before running it.

**Validated on 2026-11-17 and 2026-11-18, nothing applied.**

- `check-alarms.sh 14` with `NO_TTL_CEILING=600` passed for all four alarms: valid parameters,
  4,032 points each, no window where a rule would have fired, 12 alarm metrics billed.
- `check-alarms.sh` failed with exit 1 on each deliberate break: a ceiling of 300 (the alarm
  would have fired in 5 windows during the 2026-11-18 deploy) or 100, a wrong metric name
  (`EngineCPUUtilisation`), an invalid `ComparisonOperator` and an `EvaluationPeriods` of the
  wrong type. A ceiling of 400 passed although 3 single points were above it, because none lasted
  3 points in a row.
- `create-alarms.sh` refused `dev`, a missing ceiling and the ceiling `4o0`.
- `apply-prod.sh`, run through an `aws` stand-in that refuses every write and returns simulated
  alarms for `verify`: `check` passed; `verify` failed before `apply` because the topic does not
  exist; `apply` stopped before any write without a terminal to confirm; `verify` passed on alarms
  equal to the spec, also with their dimensions in another order, and failed on a pending
  subscription, a ceiling of 500, a missing `OK` action and a node of another replication group.
  The stand-in recorded 0 writes. The simulated alarms follow the shape `describe-alarms` returns
  for an existing metric math alarm of the account.

**Golden signals.** What covers each signal, as measured on 2026-11-13:

| Signal | Covered by | Why |
|---|---|---|
| Latency | `Latency` alarm | Server-side p99. The back-side timeouts are in **Out** below. |
| Errors | Nothing in this task | The only Redis error seen is the back's `Redis command timed out`. A log alarm on it would fire every day at the current burst. |
| Saturation | `Memory-Usage`, `Engine-CPU`, `Volatile-Keys-Gap` | Connections stayed under 100 on prod, far from any limit, so they get no alarm. |
| Traffic | No alarm | No threshold separates good from bad traffic. Read it on the ElastiCache console when an alarm fires. |

**Out.**

- Alarms in dev and staging, and the `Evictions` alarm, for the reasons in **Why**.
- An alarm on the back's `Redis command timed out` log lines. Add it only after the daily
  14:05–14:20 UTC burst is explained and fixed, so it does not fire every day.
- Re-measuring the pub/sub rate after `B5`.
- `AutomaticFailover` and `MultiAZ`, which stay a separate decision, as in `E5`.

## Cost

CloudWatch charges USD 0.10 per alarm metric per month for a standard-resolution alarm in
us-east-1 (AWS price list, read on 2026-11-17). A metric math alarm counts each metric in its
expression. The first 10 alarm metrics of the account are free, but the account already uses 63
in us-east-1, so every new metric is paid.

| Scope | Alarm metrics | Per month | Per year |
|---|---|---|---|
| **This task: four alarms, prod only** | **12** | **USD 1.20** | **USD 14.40** |
| Five alarms, prod only | 13 | USD 1.30 | USD 15.60 |
| Five alarms in dev, staging and prod (scope before 2026-11-17) | 39 | USD 3.90 | USD 46.80 |
| Four alarms, prod, `Latency` and `Engine-CPU` on the primary only | 6 | USD 0.60 | USD 7.20 |

The last row is not chosen: it saves USD 7.20 a year, and the two alarms would stop seeing traffic,
without warning, the day another node becomes primary.

SNS adds no cost: an email topic is free, and the first 1,000 emails a month are free. The
`set-alarm-state` test below creates nothing that is billed.

## Baseline

Read-only, 14 days to 2026-11-17, 5-minute points, from `scripts/e5-controls/alarm-baseline.sh`.
No point breaches any rule in any environment. Maxima are rounded up: to the next whole number for
% and ms, to the next 10 below 100, and to the next 100 from 100 up.

| Metric | prod | staging | dev |
|---|---|---|---|
| Memory usage (rule > 50%) | max 7% | max 2% | max 5% |
| Evictions | 0 | 0 | 0 |
| Keys without a TTL (`CurrItems − CurrVolatileItems`) | p50 148, p99 246, max 400 (to 2026-11-18: one point at 600, 3 points in a row at 400) | 14 | max 60 |
| Read/write p99 over the nodes (rule > 10 ms) | max 3 ms | max 1 ms | max 4 ms |
| Engine CPU over the nodes (rule > 80%) | max 4% | max 1% | max 1% |
| Connections (no alarm) | max 100 | max 80 | max 200 |

## Decided

`apply-prod.sh` reads the two lines below; keep each on one line in this format.

- Recipient of `Enhancedai-Redis-Alerts-PROD`: `team-alerts@example.com`, the team list, decided 2026-11-18.
- `NO_TTL_CEILING`: `600`, decided 2026-11-18.

**Why 600.** `CurrItems − CurrVolatileItems` counts every key without a TTL, the Bull queue keys
included, so it rises while jobs wait. In the 14 days to 2026-11-18 it stayed near 150 and rose
only during prod deploys: one point reached 525 on 2026-11-18, during the A9b and S8c deploy, and the highest value held for 3 points in a row (what the alarm sees) was 391. A ceiling
of 600 is 4 times the usual level and 53% above that sustained peak, so a slower deploy does not
raise a false alarm, while a writer that keeps adding keys without a TTL still crosses it.
`run-ttl-audit.sh prod` lists the key families when the alarm fires.

The task moved to ready for deploy on 2026-11-18; the user applies when they choose.

## Production rollout (2026-11-18)

The user ran `apply-prod.sh apply` on 2026-11-18. Read back with `aws cloudwatch describe-alarms`
and `describe-alarm-history` the same day (read-only):

| Alarm | Created (UTC) | State | Threshold | Periods | Topic on `ALARM` and `OK` |
|---|---|---|---|---|---|
| `Enhancedai-Redis-Memory-Usage-PROD` | 17:21:28 | `OK` | 50 | 2 | `Enhancedai-Redis-Alerts-PROD` |
| `Enhancedai-Redis-Volatile-Keys-Gap-PROD` | 17:21:29 | `OK` | 600 | 3 | `Enhancedai-Redis-Alerts-PROD` |
| `Enhancedai-Redis-Latency-PROD` | 17:21:31 | `OK` | 10,000 µs | 3 | `Enhancedai-Redis-Alerts-PROD` |
| `Enhancedai-Redis-Engine-CPU-PROD` | 17:21:33 | `OK` | 80 | 3 | `Enhancedai-Redis-Alerts-PROD` |

Each alarm moved from `INSUFFICIENT_DATA` to `OK` within two minutes and published that change to
the topic successfully.

Still open, so the **Done when** is not met yet:

1. The email subscription of `Enhancedai-Redis-Alerts-PROD` reads `PendingConfirmation`. Until the
   recipient clicks **Confirm subscription**, SNS delivers no alert, and `apply-prod.sh verify`
   fails by design.
2. `apply-prod.sh fire-test` has not run: no alarm history shows an `ALARM` state.

After both, record the `verify` output and the fire-test emails here.

## Verification

From `scripts/e5-controls/`, in the user's terminal, with a profile that can write CloudWatch and
SNS:

1. `bash apply-prod.sh check` prints four `OK` lines and exits 0.
2. `bash apply-prod.sh apply`, then type `apply`.
3. Click **Confirm subscription** in the AWS Notification email sent to the recipient.
4. `bash apply-prod.sh verify` prints only `OK` lines and exits 0.
5. Tell the team, then run `bash apply-prod.sh fire-test` and type `fire`. Each alarm goes to
   `ALARM` and back to `OK`, and the recipient receives 4 `ALARM` and 4 `OK` emails.

## Done when

The four alarms exist in prod, `verify` passes, and each alarm has been seen to fire and recover
with `fire-test`.
