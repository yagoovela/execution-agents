# E5b — Alert before Redis fills and when it evicts, in every environment

**Goal:** someone is told before a Redis that refuses writes fills up, as soon as any Redis
evicts a key, and when a Redis gets slow or runs out of CPU.

**Depends on:** nothing. **Added 2026-11-11** when `E5` closed: `E5` switched every environment to
`noeviction` and left the alarms open. ClickUp: [868mvfwr4](https://app.clickup.com/t/868mvfwr4).

## Why

Under `noeviction` a full Redis refuses writes instead of silently dropping the dedup keys. That is
only an improvement if someone is watching memory. On 2026-11-11 dev, staging and prod all run
`enhancedai-valkey8-noeviction` (`in-sync`, read-only), and the account has no ElastiCache alarm.

**Latency, added 2026-11-13.** The S4b production check
([TASK-S4B-SHARED-CHAIN-BUDGET.md](TASK-S4B-SHARED-CHAIN-BUDGET.md)) found `Redis command timed out`
in the prod back every day. Measured on 2026-11-13 (read-only, last 14 days, 5-minute points):

- Redis itself is fast. On the prod primary, read p99 never passed 1.0 ms and write p99 never
  passed 1.7 ms, and engine CPU never passed 3.9%, also at the 14:00 UTC peak.
- The timeouts happen in the back. `withRedisCommandTimeout` (`back/src/app-api/rate-limit/redis-command-timeout.ts`)
  rejects after a 250 ms `setTimeout`. When the back's event loop is blocked for 250 ms or more, the
  timer fires before the reply is read, even though Redis answered in under 2 ms.
- The timeouts come in one burst a day, weekends included, between 14:05 and 14:20 UTC: 1,700 in
  14 days, up to 92 in one 5-minute period. That points at work scheduled at 14:00 UTC in the back,
  not at customer traffic.

So a server-side latency alarm would not have caught this burst, and it is still worth having: like
the memory alarm, it stays quiet today and fires when Redis itself degrades. The burst needs its own
task in the back.

## Scope

**In.** The alarms decided in `E5` on 2026-10-02 ([TASK-E5-REDIS-POLICY-AND-SIZING.md](TASK-E5-REDIS-POLICY-AND-SIZING.md),
**Alarms**), per environment:

| Alarm | Metric | Rule |
|---|---|---|
| `Enhancedai-Redis-Memory-Usage-<ENV>` | `DatabaseMemoryUsagePercentage` (Maximum) | > 50% for 2 × 300s |
| `Enhancedai-Redis-Evictions-<ENV>` | `Evictions` (Sum) | > 0 in 300s, missing data not breaching |
| `Enhancedai-Redis-Volatile-Keys-Gap-<ENV>` | metric math `CurrItems − CurrVolatileItems` | above 500 (dev), 100 (staging); prod set from a fresh `ttl-audit` run |
| `Enhancedai-Redis-Latency-<ENV>` | metric math: `MAX` of `SuccessfulReadRequestLatency` and `SuccessfulWriteRequestLatency` (`p99`) over the three nodes | > 10,000 µs (10 ms) for 3 × 300s, missing data not breaching |
| `Enhancedai-Redis-Engine-CPU-<ENV>` | metric math: `MAX` of `EngineCPUUtilization` (Maximum) over the three nodes | > 80% for 3 × 300s |

The two rows added on 2026-11-13 take the `MAX` over the three nodes, so they keep working when
another node becomes primary; only the primary serves requests, so the replicas send no latency
data. In the last 14 days neither rule would have fired in any environment (prod p99 at most
1.7 ms, dev at most 3.4 ms once, staging served no request; engine CPU at most 3.9%).

**Golden signals.** What covers each signal, as measured on 2026-11-13:

| Signal | Covered by | Why |
|---|---|---|
| Latency | `Latency` alarm | Server-side p99. The back-side timeouts are in **Out** below. |
| Errors | Nothing in this task | The only Redis error seen is the back's `Redis command timed out`. A log alarm on it would fire every day at the current burst. |
| Saturation | `Memory-Usage`, `Engine-CPU`, `Evictions`, `Volatile-Keys-Gap` | Connections peaked at 72 on prod, far from any limit, so they get no alarm. |
| Traffic | No alarm | No threshold separates good from bad traffic. Read it on the ElastiCache console when an alarm fires. |

Each alarm and recovery notifies `Enhancedai-Redis-Alerts-<ENV>`, a new email topic per environment,
so Redis alerts do not reach the external subscribers of the existing topics.
`scripts/e5-controls/create-alarms.sh <env> <email>` prints the commands and changes nothing unless
`APPLY=1` is set. The user runs every AWS write.

**Out.** An alarm on the back's `Redis command timed out` log lines. Add it only after the daily
14:05–14:20 UTC burst is explained and fixed, so it does not fire every day. Re-measuring the pub/sub rate after `B5`. `AutomaticFailover` and `MultiAZ` stay a separate
decision, as in `E5`.

## Verification

1. Before applying, confirm the recipient email and the prod threshold of the keys-gap alarm.
2. In dev, breach each alarm on purpose (lower its threshold below the current value), confirm the
   email arrives, then restore the threshold and confirm the recovery email. Dev Redis is idle most
   of the time, so the latency alarm needs traffic first: run a flow during the test.
3. Read each alarm back with `aws cloudwatch describe-alarms` and confirm its dimension names the
   right replication group and its action names the right topic.

## Done when

The five alarms exist in dev, staging and prod, each has been seen to fire and recover in dev, and
the recipients and thresholds are recorded here.
