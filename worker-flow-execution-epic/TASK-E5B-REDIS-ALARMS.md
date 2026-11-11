# E5b — Alert before Redis fills and when it evicts, in every environment

**Goal:** someone is told before a Redis that refuses writes fills up, and as soon as any Redis
evicts a key.

**Depends on:** nothing. **Added 2026-11-11** when `E5` closed: `E5` switched every environment to
`noeviction` and left the alarms open. ClickUp: [868mvfwr4](https://app.clickup.com/t/868mvfwr4).

## Why

Under `noeviction` a full Redis refuses writes instead of silently dropping the dedup keys. That is
only an improvement if someone is watching memory. On 2026-11-11 dev, staging and prod all run
`enhancedai-valkey8-noeviction` (`in-sync`, read-only), and the account has no ElastiCache alarm.

## Scope

**In.** The alarms decided in `E5` on 2026-10-02 ([TASK-E5-REDIS-POLICY-AND-SIZING.md](TASK-E5-REDIS-POLICY-AND-SIZING.md),
**Alarms**), per environment:

| Alarm | Metric | Rule |
|---|---|---|
| `Enhancedai-Redis-Memory-Usage-<ENV>` | `DatabaseMemoryUsagePercentage` (Maximum) | > 50% for 2 × 300s |
| `Enhancedai-Redis-Evictions-<ENV>` | `Evictions` (Sum) | > 0 in 300s, missing data not breaching |
| `Enhancedai-Redis-Volatile-Keys-Gap-<ENV>` | metric math `CurrItems − CurrVolatileItems` | above 500 (dev), 100 (staging); prod set from a fresh `ttl-audit` run |

Each alarm and recovery notifies `Enhancedai-Redis-Alerts-<ENV>`, a new email topic per environment,
so Redis alerts do not reach the external subscribers of the existing topics.
`scripts/e5-controls/create-alarms.sh <env> <email>` prints the commands and changes nothing unless
`APPLY=1` is set. The user runs every AWS write.

**Out.** Re-measuring the pub/sub rate after `B5`. `AutomaticFailover` and `MultiAZ` stay a separate
decision, as in `E5`.

## Verification

1. Before applying, confirm the recipient email and the prod threshold of the keys-gap alarm.
2. In dev, breach each alarm on purpose (lower its threshold below the current value), confirm the
   email arrives, then restore the threshold and confirm the recovery email.
3. Read each alarm back with `aws cloudwatch describe-alarms` and confirm its dimension names the
   right replication group and its action names the right topic.

## Done when

The three alarms exist in dev, staging and prod, each has been seen to fire and recover in dev, and
the recipients and thresholds are recorded here.
