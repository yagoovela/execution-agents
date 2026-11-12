# S4b — One chain budget across back replicas

**Goal:** when the execution budget is enforced, a chain of runs stops at its ceiling however many
back replicas share the work.

**Depends on:** nothing. **Conditional:** it matters only while `execution_budget` is on in
production. If the flag is off, record that here and set the task to `dropped` until the flag is
turned on. **Added 2026-11-04** from the replica audit of that day. ClickUp: [868mrv6cz](https://app.clickup.com/t/868mrv6cz).

## Why

`S4` decided to leave the chain budget in memory because production ran one back task
(`TASK-S4-LOOP-CEILING.md`, "Whether the chain budget needs to move to Redis": `desiredCount` was 1
in every environment, so the split was latent). That premise is no longer true: production
autoscales the back to two tasks every day (`TASK-E3B-SINGLE-DELIVERY.md`, **Corrected premise**).

Read against back `main` `95533b9f` on 2026-11-04:

1. `ChainBudgetRegistry` (`chain-budget.ts`) counts executions per chain root in a private `Map`
   held by the module singleton `chainBudgetRegistry`.
2. `open`, `chargeExecutions` and `release` always run (`flux.service.ts`). Only the breach check
   reads `execution_budget` (`EXECUTION_BUDGET_FLAG`).
3. A `triggerOnly` child is enqueued to Bull, and any replica can take it. Each replica then counts
   its share of the chain, so the ceiling can be passed up to N times with N replicas.

`S4` also recorded two defects that are about identity, not storage: the queue hop drops
`parentCancelRunKey`, and the webhook mints a new `processId` per call. Moving the counter to Redis
does not fix them; it is the prerequisite for fixing them.

## Scope

**In.**

1. The user reads `execution_budget` in production. If it is off, stop here (see **Conditional**).
2. The chain counter moves to Redis: an atomic increment per chain root, with an expiry longer than
   the longest chain, and a release that cannot go below zero.
3. A Redis error does not block runs. The check fails open and logs, as the rate limiter does
   (`rate-limit.storage.ts`).

**Out.** The two identity defects above. They stay in `S4`'s record until a task owns them.

## Verification

- **Negative control (required).** Two back processes and a chain whose children land on both. With
  a ceiling of N, on `main` today the chain runs more than N executions. After the change it stops
  at N. Revert the change and watch the test fail.
- Measure before refusing (PLAN §3.3.2): before the change ships, count the production chains that
  would have been stopped, and confirm none of them is a legitimate run.

## Done when

With the flag on, a chain stops at its ceiling with two and three back replicas, and a Redis error
does not block runs. Or, with the flag off, the reading is recorded here and the task is `dropped`.

## Result (2026-11-11)

**Flag reading.** `execution_budget` is on in production (read 2026-11-10). The task goes ahead.

**Status.** In review: back [#2107](https://github.com/enhancedai-com/Flux-Prompt/pull/2107) (`feat/868mrv6cz`). Back only, with no env var, SSM or task definition change.

**Design.**

1. Each replica writes its own absolute total for the chain to a Redis hash: `HSET flux:chain-executions:<root> <replicaId> <total>`, a 24 h TTL, then `HVALS`. The chain total is the sum of the fields. An absolute write is idempotent, so a write that timed out after Redis applied it cannot count twice, and a failed write is sent again on the next charge or release. Scope item 2 asked for "a release that cannot go below zero"; there is no release in Redis, because executions that happened stay counted, as in `ChainSpendLedger`.
2. `chargeExecutions` stays synchronous, because `budgetedNextReady` (the prefetch scheduler) calls it synchronously. It answers from this replica's count plus the other replicas' share from the last reply, so a replica sees the others at most one Redis round trip late. Each chain has one write in flight; charges made meanwhile go in the next write.
3. A run that opens a chain on a replica while the first open is still reading Redis waits for that read. An entry leaves memory only after its last run released it and its count is written.
4. Redis unreachable: the replica counts its own share, logs once per chain, and never blocks a run.
5. A `triggerOnly` child that starts after its caller finished now continues the chain count. Before, it restarted from 0 even on one replica.

**Measure before refusing.** `etc/2026-11-11/4-868mrv6cz-prod-chain-charges.sql` (credit charges per `chainRootId`, last 30 days, run 2026-11-11): the largest chain had 99 charges and lived 0.8 h. The ceiling is 200,000 node executions (production sets no `FLUX_MAX_*`). No real chain is near it.

**Verification.**

- Negative control (required): with each replica counting only its own share and a ceiling of 40, the chain ran 140 executions in sequence and 280/420 at once on 2/3 replicas. With the shared count it stops at 40 in sequence, and within one run of nodes per extra replica at once. Two registries (three for the 3-replica case), each with its own ioredis connection, against a real Redis (`chain-budget.redis.spec.ts`, needs `REDIS_TEST_URL`). Not run as separate OS processes.
- The wait on a concurrent open, the retry after a failed write, forgetting the entry and a double-counted timeout each have a unit test that was seen red by breaking its mechanism.

**Dev test (2026-11-11).** The three commits were cherry-picked onto `develop` (`3f06cff6`), with `FLUX_MAX_CHAIN_NODE_EXECUTIONS=12` on one dev back task (`etc/2026-11-11/9-868mrv6cz-dev-chain-ceiling.sh`). The flows are in the "lex corp." workspace, folder "S4b QA 868mrv6cz": A has 7 executions and then a `fluxBox` that calls B `triggerOnly`; B has 8.

- B alone: `Successfully ran`.
- A then B: A `Successfully ran`. B started 4 s after A finished and stopped with `Stopped by system limit — chained flow steps (reached 13, limit 12)`, with A's run as the chain root. With the old code, B restarted from 0 and finished. There was no `Chain execution count unavailable` log.
- Not shown on dev: the cross-replica case, because dev runs one back task. The local real-Redis test covers it.
- Dev was restored to 200,000 (`:2668`). A `develop` deploy that ran during the test (`0463cf7b`, revision `:2667`) inherited the 12, and the restore put the S4b image back. Finish a dev env change before anyone else deploys, or build the restore from the newest revision.

**Reviews.** `/simplify`, `/code-review` and `/security-review` ran on 2026-11-10/11. `/security-review` found nothing: the chain root is set only by the server. Findings kept as they are, with the reason:

- Redis is touched even when `execution_budget` is off. The flag is on in production and writes are coalesced.
- A Bull retry of a stalled run with the same `processId` inherits the earlier attempt's count. Those executions happened, and the ceiling is 200,000.
- `chargeExecutions` was not made async in every caller. That would change the prefetch executor and add one Redis round trip per node.

**Not in scope, found on the way.** Six `apiV2` fixture suites fail on `origin/main` with `Cannot read properties of undefined (reading 'track')`, because the fixture lacks `runMemoryTracker`.

## Files

`back/src/app-api/flux/chain-budget.ts` (`ChainBudgetRegistry`) · `back/src/app-api/flux/flux.service.ts`
(`open`, `chargeExecutions`, `release` call sites) · `back/src/app-api/rate-limit/rate-limit.storage.ts`
(the fail-open pattern)
