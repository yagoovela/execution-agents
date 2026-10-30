# E5 — Stop Redis being allowed to evict correctness state

**Goal:** the keys that prevent duplicate customer emails and duplicate inbound-email runs cannot be
thrown away to make room, nothing in Redis can grow without a bound, and the instance is sized for
the pub/sub rate `B5` creates.

**Depends on:** nothing. **Should land before B5.** **Source:** `S8` Part 3, split out 2026-09-18
because it is an infrastructure change with no code in it, and holding `S8` for it would have
delayed the replica-safety fix for a defect that has never fired. **ClickUp:** 868m6ue54.

## What was measured

Read from the account read-only, on 2026-09-18 and again on 2026-10-02 (14-day windows, prod
column is the max across the three nodes):

| | 2026-09-18 | 2026-10-02 |
|---|---|---|
| prod cluster | `enhancedai-redis-prod`, 3 × `cache.t2.medium`, Valkey 8.0.1, cluster mode off | unchanged |
| staging / dev | — | `enhancedai-redis-staging` (3 × `cache.t2.small`), `enhancedai-redis-dev` (3 × `cache.t2.micro`) — separate clusters, up 24/7 |
| parameter group | `default.valkey8` | unchanged on all nine nodes, `in-sync` (no pending reboot); no custom group exists |
| **`maxmemory-policy`** | **`volatile-lru`** | unchanged, all three environments |
| `DatabaseMemoryUsagePercentage` | max **1.9%**, avg 1.3% | max 1.63%, avg 1.30% |
| `BytesUsedForCache` | max ~50 MB | max 42.3 MB |
| **`Evictions`** | **0** | 0, every node, every environment |
| `CurrItems` | max 383 | **max 6,843** — daily max jumped from ~290 to ~2,400 on 2026-09-20 and stayed at 2.4k–6.8k; memory did not move, so the new keys are small. **Not yet explained** |
| `EngineCPUUtilization` | max **1.8%** | max 5.58% (primary only; replicas ~2.4%), avg 0.3% |
| CloudWatch alarms on `AWS/ElastiCache` | — | **none** (the existing alarms are RDS/ECS/EC2 only) |
| `AutomaticFailover` / `MultiAZ` | **disabled** / **disabled** | unchanged |

The non-prod bastion cannot reach any Redis endpoint (port 6379 is not open to it), so the
key-level audit below runs from inside the API container via ECS Exec.

## What lives in Redis

Every application key family on the production refs (back `production`, worker `main`,
mcp-server `main`), read 2026-10-02. One Redis per environment, shared by back and worker
(`REDIS_HOST`/`REDIS_PORT`); mcp-server uses none; the worker only publishes.

| Family | Written at (back) | TTL | Under `volatile-lru` | On an OOM write under `noeviction` |
|---|---|---|---|---|
| `email-sent:<flow>:<node>:<run>` | `flux.service.ts:5476` | 24h | evictable → duplicate email | **fails closed** — no try/catch, the run errors, no email is sent |
| `email-content:<flow>:<node>:<sha256>` | `flux.service.ts:5506` | 90s | evictable → duplicate email | fails closed, same path |
| `pop3-processed:<Message-ID>` | `mail.service.ts:386` | 24h | evictable → inbound email runs twice | caught at `mail.service.ts:589`: sender gets an error reply, message is then deleted from the mailbox (`mail.service.ts:342`) |
| `integration_oauth_state:*` | `oauth-state.service.ts:21` | 600s | evictable → OAuth callback refused | fails closed (500) |
| `resend-verification-email:*` | `auth.service.ts:101` | 60s | evictable (low impact) | fails closed |
| `flux:chain-spend:*` | `chain-spend-ledger.ts:36` | 24h | evictable → spend ceiling resets | fails open (logged) |
| `flux:chain-root:*`, `flux:chain-ceiling:*` | `chain-root.registry.ts:24`, `chain-ceiling.registry.ts:43` | run max duration | evictable | fails open |
| `flux:tenant-runs:*`, `flux:tenant-key:*` | `tenant-concurrency.ledger.ts`, `tenant-key.resolver.ts:61` | set / 300s | evictable | fails open (admits the run) |
| `rl:*` rate-limit counters | `rate-limit.storage.ts:17`, `rate-limit-key.resolver.ts:104` | `ttlMs` / 300s | evictable → counter resets | fails open |
| Bull: `api-v2`, `schedule`, `extract-text-from-files`, `process-vector-*` | `apiV2Job.queue.ts:29`, `schedule-registrar.service.ts:68`, `app-api.module.ts:577` | **none, by design** | never evicted (not volatile) | **enqueue fails** — Bull writes through Lua scripts, which `noeviction` rejects |
| socket.io adapter, Nest `Transport.REDIS` | `redis-io.adapter.ts`, `main.ts:54` | pub/sub, holds no memory | — | — |

Two corrections to the 2026-09-18 version of this spec:

- **Outbound webhooks have no dedup at all** (`flux.service.ts:5577`, a bare `axios.post`). The
  policy change cannot protect them, and nothing here claims to. Whether they need one is not
  this task.
- The delivery dedup is not one key but two (`email-sent:` and `email-content:`), and the
  inbound-email claim (`pop3-processed:`, shipped by `S8` Part 4) is in the same population.

## Why it matters, stated honestly

Every correctness key above carries a TTL, which makes it **volatile**, which makes it exactly the
population `volatile-lru` evicts first under memory pressure. The failure mode is a duplicate
customer email or an inbound email run twice — a charge and a side effect, not a slow page.
`S8` control 5 showed it concretely: under `volatile-lru` 0 of 100 dedup keys survived a fill;
under `noeviction` all 100 survived and the filling write took the OOM.

And it has never happened. Zero evictions in fourteen days, twice, at under 2% of capacity. Per
§3.3.2 this is stated as measured: **the policy is wrong and the consequence is latent.** It is
debt with a bad blast radius, not an incident.

The second half — sizing for after `B5` — is answered by the same measurement, in the other
direction. Memory peaks at 1.6% and engine CPU at 5.6% of one core. **No resize is indicated.**
Recording that is the deliverable; re-measuring after `B5` is what would change it.

## What happens when memory runs out (decided: no application code)

`noeviction` turns "a key silently disappears" into "a write is refused". The question is whether
the refused write needs handling in code. It does not, for three reasons:

1. **When Redis is full, the queue is already down.** Every run enters through Bull, and Bull's
   enqueue is a Lua write that `noeviction` refuses. A dedup that failed open would not keep
   email flowing — the run carrying it could not have been enqueued in the first place, and the
   ones already in flight are the ones most likely to be retried.
2. **Failing open is the defect this task removes.** Sending the email when the dedup write
   fails reintroduces the duplicate, under exactly the condition — a stressed Redis and retries —
   where duplicates are most likely. Failing closed is the correct semantic for a dedup.
3. **The real protection is never reaching OOM.** At 1.6% of capacity, the alarms below fire
   long before any write is refused. Code that handles an OOM is code for a state the alarms
   exist to prevent.

What is accepted, and stated so nobody rediscovers it:

- During an OOM, the rate-limit, spend-ceiling and tenant-concurrency guards **fail open** — they
  stop protecting until memory is freed. Runs cannot be enqueued anyway, so the exposure is the
  in-flight set.
- An inbound email that arrives during an OOM gets an error reply and is deleted from the
  mailbox (`mail.service.ts:589` then `:342`). That is pre-existing behaviour for **any** error in
  `processEmail`, not something `noeviction` introduces; flagged, not fixed here.

## Nothing without a bound

`noeviction` means memory is reclaimed only by TTLs and by Bull's retention, so every key must be
in one of the two:

- **Application keys:** every family above sets a TTL at write time. One edge: in
  `rate-limit.storage.ts`, if `INCR` succeeds and `PEXPIRE` then fails, the key is left without a
  TTL; a `pttl < 0` repair path exists on the next hit.
- **Bull keys** carry no TTL by design and cannot be given one. They are bounded by retention:
  `api-v2` `removeOnComplete {age: 300}` / `removeOnFail {age: 86400, count: 20}`; repeatable
  schedules `removeOnComplete {age: 3600}`; the rest `removeOnComplete: true`. The `repeat`
  definitions are permanent by design (one per user schedule). No queue has unbounded retention.

That is what the code says. The stored data is audited with
`scripts/e5-controls/run-ttl-audit.sh <env>` (read-only: `SCAN`, `TYPE`, `PTTL`,
`MEMORY USAGE`, `INFO keyspace`, run inside the API container via ECS Exec). It groups keys by
family and prints, per family, how many have no TTL. Every no-TTL family must be a Bull key;
anything else is a finding.

| env | date | keys / with TTL | no-TTL families outside Bull | notes |
|---|---|---|---|---|
| dev | 2026-10-02 | 68 / 18 | `bikes:1` (ReJSON), `test`, `age` — hand-written test keys, 160 bytes | orphan queues with no consumer: `bull:apiV2Queue:*` (6 jobs, old queue name) and `bull:superchat-learning:id` — static, do not grow. Largest family: `process-vector-chunks-queue` failed jobs, 20 × ~290 KB, held by `removeOnFail.count: 20` |
| dev (route) | 2026-10-02 | 59 / 9 | same three test keys | first run of `GET /internal/redis-monitor/ttl-audit` in dev: 200 in 0.4s, a second call 429, no JWT 401. **`evictedKeys: 312`** — `INFO stats` counts since the node's last restart, so dev has evicted real keys outside CloudWatch's 14-day window: the defect is not only theoretical on a small node |
| staging (route) | 2026-10-02 | 14 / 6 | none | after the noeviction switch, on deploy f7d983d7: `maxmemoryPolicy: noeviction`, `evictedKeys: 0`; the 8 no-TTL keys are all Bull; the only non-Bull family is the route's own cooldown key, which has a TTL |
| prod | 2026-10-05 | 588 / 444 | none — all 144 no-TTL keys are Bull | run by Alexandre via `run-ttl-audit.sh prod`, before the switch. Largest TTL'd families are the S8 chain keys (`flux:chain-root` 241, `flux:chain-spend` 124, `flux:chain-ceiling` 58 — 423 keys), added to production on 2026-09-14/16: the likely source of the 2026-09-20 `CurrItems` jump (max 383 on 09-18, 588 now). Memory is Bull job payloads: `process-vector-chunks-queue` 5 failed jobs = 26 MB, legacy `apiV2Queue` (no consumer) 20 jobs = 7.4 MB. Policy not read: the script used `CONFIG GET` (blocked); fixed in 41aa704 to read `INFO memory` |

**The QA path: `GET /internal/redis-monitor/ttl-audit`** (master JWT, back PR #2025, documented in
`docs/main-api/specific-features/redis-ttl-audit.mdx`). It returns the policy the server is
running (read from `INFO memory`, since ElastiCache blocks `CONFIG GET`), `evicted_keys`, the
keyspace totals and the same family breakdown as the script, never a value. The field to read
is `familiesWithoutTtlOutsideBull`: it must be empty. One audit per 60s across all users
(429 otherwise), 200k key ceiling, paced batches, one audit log line per call. The scripts below
stay for the moment before the route is deployed.

**Without ECS Exec or the Session Manager plugin.** ElastiCache publishes `CurrVolatileItems`
(keys with a TTL) next to `CurrItems`, so `CurrItems − CurrVolatileItems` is the no-TTL count,
per hour, with only CloudWatch read access: `scripts/e5-controls/cw-ttl-check.sh <env> [days]`.
It answers *how many* and *is it growing*, not *which family* — use the audit above for that.
On dev it agrees with the audit (50 no-TTL keys; the metric held 46–58 over 14 days, every
`CurrItems` peak being TTL-bearing keys). The same count is in `GET /redis-monitor/info`
(`db0: keys=…,expires=…`, master JWT); `GET /redis-monitor/key` returns a key's TTL but also
its value, so it is not suitable for sweeping prod.

Because that difference is a metric, it can carry an alarm: a metric-math alarm on
`CurrItems − CurrVolatileItems` above a per-environment ceiling catches a new no-TTL writer
before memory does. Proposed alongside the two alarms in scope; thresholds and recipients are
decided with them.

## Rollout log

| env | date | parameter group | `ParameterApplyStatus` | policy read back from the server | notes |
|---|---|---|---|---|---|
| dev | 2026-10-02 | `enhancedai-valkey8-noeviction` (created this day, `maxmemory-policy = noeviction`, `ChangeType: immediate`) | `in-sync` on all three nodes, no reboot | `noeviction` (`GET /internal/redis-monitor/ttl-audit`) | `evictedKeys` stayed at 312 after the switch |
| staging | 2026-10-02 | `enhancedai-valkey8-noeviction` | `in-sync` on all three nodes, no reboot | `noeviction`, read by the route after deploy f7d983d7 | before the switch: 8 keys without TTL, flat for 14 days (`cw-ttl-check.sh`), 0 evictions |
| prod | 2026-10-05 | `default.valkey8` (not switched yet) | — | `volatile-lru`, `evicted_keys: 0` (`run-ttl-audit.sh prod` after 41aa704) | baseline before the switch; key audit clean (all 144 no-TTL keys are Bull) |

## Alarms (decided 2026-10-02, not applied yet)

Audit of the account first: 50 CloudWatch alarms, 22 of them console-made with the name pattern
`Enhancedai-<Topic>-<Resource>-<ENV>`, one email-only SNS topic per alarm family shared across
environments, subscribers external (an outside domain), no `OKActions`. The six Terraform MCP alarms
have no actions at all. No Slack path exists (no webhook, no Lambda, AWS Chatbot not reachable);
application error logs reach Google Chat through `api-logs-to-google-space-{dev,stg,prod}`, but no
alarm does. No ElastiCache alarm exists.

Decided: follow the existing pattern, with a new per-environment topic so Redis alerts do not reach
the external subscribers of the existing ones.

| Alarm | Metric | Rule |
|---|---|---|
| `Enhancedai-Redis-Memory-Usage-<ENV>` | `DatabaseMemoryUsagePercentage` (Maximum) | > 50% for 2 × 300s |
| `Enhancedai-Redis-Evictions-<ENV>` | `Evictions` (Sum) | > 0 in 300s, missing data not breaching — under `noeviction` it fires only if the policy is reverted |
| `Enhancedai-Redis-Volatile-Keys-Gap-<ENV>` | metric math `CurrItems − CurrVolatileItems` | above 500 (dev), 100 (staging), prod set after the route has run there; 3 × 300s |

All three alarm **and** recover to `Enhancedai-Redis-Alerts-<ENV>` (email). Created by
`scripts/e5-controls/create-alarms.sh <env> <email>`, which prints the commands and changes nothing
unless `APPLY=1` is set. **Held until Alexandre says to apply.**

## Scope

**In.** A custom parameter group with **`maxmemory-policy = noeviction`**, applied to prod,
staging and dev. `default.valkey8` is AWS-managed and cannot be edited, so a new group is not a
preference, it is the only way to change the value.

**In.** CloudWatch alarms per environment on `DatabaseMemoryUsagePercentage` and on
`Evictions > 0`. Under `noeviction` the evictions alarm can only fire if the policy is reverted,
so it guards the change itself; the memory alarm is the one that prevents the OOM. **Recipients
(SNS topic) and thresholds are open — no ElastiCache alarm or topic exists today.**

**In.** The key-level TTL audit above, per environment, before the switch.

**In.** Re-measure the pub/sub rate after `B5` is on, and record the number against the baseline
above. A headroom claim ages.

**Open.** Explain the 2026-09-20 `CurrItems` jump before calling the headroom settled — the TTL
audit's family breakdown is the first place to look.

**Out, and flagged rather than fixed.** `AutomaticFailover` and `MultiAZ` are disabled on all
three groups. Losing the primary loses the queues, the dedup keys and the pub/sub relay at once,
with no automatic promotion. That needs its own decision about downtime and cost. Outbound-webhook
dedup and the delete-after-error in `processEmail` are likewise out.

## Verification

- **Negative control (required), and it runs locally.** A Redis container with
  `--maxmemory 16mb --maxmemory-policy volatile-lru`: write a dedup key in the real shape
  (`SET k '1' EX 86400 NX`), fill past `maxmemory`, and **watch the key disappear**. Then
  `noeviction`, repeat, and confirm the key survives and the filling write is what fails instead.
  Committed as `scripts/e5-controls/eviction-control.sh` (`S8` control 5 recorded the same
  result but never committed its probe). Run 2026-10-02 on `valkey/valkey:8.0`, 16 MB,
  100 dedup keys, filled with no-TTL 10 KB writes through Lua as Bull writes:

  | policy | dedup keys surviving | `evicted_keys` | filling write |
  |---|---|---|---|
  | `volatile-lru` | **0 / 100** | 100 | **OOM anyway** |
  | `noeviction` | 100 / 100 | 0 | OOM |

  The `volatile-lru` row is the argument in one line: once the volatile keys are gone the
  instance refuses Bull's writes regardless, so today's policy loses the dedup **and** still
  stops the queue. It also confirms the premise of the OOM decision above — a Lua write is
  refused under OOM.
- TTL audit on every environment shows no non-Bull family without a TTL.
- Confirm the parameter group is actually in effect on each environment — the node's
  `ParameterApplyStatus` is `in-sync` and `GET /internal/redis-monitor/ttl-audit` reports
  `maxmemoryPolicy: "noeviction"`, not the console's intention. A pending-reboot parameter change is a classic way to believe a policy is
  applied when it is not.
- Confirm the alarms fire, by breaching them on purpose in dev.

## Done when

No environment can evict a dedup key, no key outside Bull lives without a TTL, both alarms exist
and have been seen to fire, and the post-`B5` pub/sub measurement is recorded next to the
pre-`B5` baseline.

## Files

No application code on the protected path (the dedup itself is unchanged). One read-only
internal route for validation: `back/src/internal/services/redis_ttl_audit.service.ts` +
`GET /internal/redis-monitor/ttl-audit` (PR #2025). ElastiCache parameter group and CloudWatch alarms, per environment ·
`scripts/e5-controls/` (TTL audit) · read, not changed: `back/src/app-api/flux/flux.service.ts`
(the `email-sent:`/`email-content:` dedup), `back/src/app-api/mail/mail.service.ts`
(`pop3-processed:`).
