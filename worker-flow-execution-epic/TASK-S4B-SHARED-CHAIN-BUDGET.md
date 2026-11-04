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

## Files

`back/src/app-api/flux/chain-budget.ts` (`ChainBudgetRegistry`) · `back/src/app-api/flux/flux.service.ts`
(`open`, `chargeExecutions`, `release` call sites) · `back/src/app-api/rate-limit/rate-limit.storage.ts`
(the fail-open pattern)
