# S4 — Execution budget: per node, per run, per chain

**Goal:** make it impossible for a run to execute without bound, whatever shape the loop takes.

Three limits, because they catch different things and none of them subsumes the others:

| Limit | Catches | Misses |
|---|---|---|
| **X — iterations per node** | the runaway loop on one node | a loop that walks across many nodes |
| **Y — node executions per run** | every shape, including ones nobody predicted | nothing — but only within one run |
| **Chain total** | recursion that resets Y by starting a new run | — |

**Depends on:** nothing. Best done with S1 — same class of guard, same test harness.
**Severity:** high (review §1.2).

## Why

`evaluateLoopCondition` (`folw/helpers/helpers.ts`) applies the limit on one branch only:

```
if (loopBehavior === 'continue') finalResult = userConditionResult && loopLimitCheck;
else                             finalResult = userConditionResult;
```

On the second branch the limit is computed, reported to the UI through `loopStatus` and the
`condition-loop-status` socket event, and then **not applied**. And on the capped branch the limit
itself is `node.data.loopCount` — user data.

So an always-true condition on a node whose behaviour is not `'continue'` loops with no ceiling.
Whether `'stop'` was meant to bypass the counter is a product question; the engineering point is
that a system-level maximum should not be reachable from node configuration.

## Why the static check is not enough, and why Y is the one that matters

There are three defences and they belong in this order:

1. **Before the run — graph validation.** Refuse what can be proven wrong without spending anything:
   cycles inside the graph, and a flow already on the call chain (`TASK-S1`). Cheapest, and it gives
   the author a real error instead of a bill.
2. **During the run — X, per node.** Stops the common case: one node looping on a condition that
   never turns false.
3. **During the run — Y, per run, and the chain total.** The backstop.

**The third is not redundant, it is the only guarantee.** Whether a flow terminates is not decidable
by looking at it — the loop condition reads data that does not exist until the run happens. A static
check can prove *some* flows wrong; it can never prove the rest right. So no amount of pre-flight
validation removes the need for a budget that counts what actually executed and stops.

That is also the argument against anyone proposing to drop Y once the graph validation is good: the
validation and the budget answer different questions, and only the budget answers the one that
matters at 3 a.m.

## Scope

**In — X, per node.** A hard maximum applied on **both** branches, independent of `loopBehavior`
and of `loopCount`. The node's own limit still applies where it is lower — this is a ceiling, not a
replacement.

**Assumption to confirm — the system maximum is an env var, defaulted generously.** The point is to
stop the unbounded case, not to second-guess legitimate long loops. Set it well above the largest
real loop found in the measurement below.

**In.** When the system ceiling stops a loop, say so distinctly. `loopStatus.reason` already carries
a human-readable reason — `Loop limit exceeded (n/m)` — so the new case needs its own wording, or
a user will read "limit exceeded" and go looking for a limit they never set.

**In — X applies to `arrayNode` too**, which iterates a list rather than a condition. A
`processorArray` of a hundred thousand items is the same runaway with a different shape.

**In — Y, node executions per run.** A counter of executions, not of distinct nodes: a node that
runs forty times spends forty. When it is exhausted the run **terminates deterministically** with a
terminal state naming the budget — it does not simply stop being scheduled, and it does not die. A
run that ends ambiguously is worse than one that ends refused, because nobody can tell it from a
hang.

**In — the chain total.** Y is per run, and a sub-flow starts a new run (`TASK-S1`), so a per-run
budget is reset by nesting exactly as the spend ceiling was. The counter resolves the chain root and
accounts against it. **This is the same mechanism `TASK-S3` needs for cost** — one counter carrying
two limits, resolved at the same place, rather than two independent accountants that can disagree.

**In — the budget protects the workflow, not only the wallet.** Every node execution is activities
scheduled and completed in Temporal history. Y bounds history growth as a side effect, which is the
other half of what `TASK-B4`'s `continueAsNew` is for.

**Out.** Changing `loopBehavior`'s meaning. If `'stop'` bypassing the counter is intentional, this
task keeps that intent and adds a ceiling above it.

## Verification

- **Negative control (required).** A condition node with an always-true condition and
  `loopBehavior` set to anything but `'continue'`: watch it loop without bound on `main`, then
  confirm the ceiling stops it and the reason names the system limit rather than the node's.
- **Negative control for Y (required).** Build a flow that loops across *several* nodes rather
  than on one — the shape X cannot see — and confirm it runs unbounded on `main`, then confirm Y
  stops it with a terminal state naming the budget. Then nest that flow two levels deep and confirm
  the **chain** total stops it, rather than each level getting a fresh Y.
- **Measure before refusing** (PLAN §3.3.2): find the largest `loopCount` and the largest
  `processorArray` in the stored flows, and the largest number of node executions any real run has
  produced. Set X and Y above all of them with margin, and report the distribution rather than the
  maximum — a ceiling chosen from one outlier is a ceiling nobody trusts. Report the
  distribution, not just the maximum — a ceiling chosen from one outlier is a ceiling nobody
  trusts.
- Confirm the UI still shows the node's own limit when that is what stopped the loop; the two
  reasons must not be confused.

## Done when

No node configuration and no graph shape can produce an unbounded run: X bounds one node, Y bounds
the run, and the chain total bounds nesting. Every ceiling sits above the largest real value in the
stored data. A run that hits any of them ends in a terminal state that names which one, and the
three reasons are distinguishable from each other and from the node's own limit.

## Files

`back/src/app-api/folw/helpers/helpers.ts` (`evaluateLoopCondition`) ·
`back/src/app-api/flux/flux.service.ts` (`conditionNode()`; the inline `arrayNode` branch) ·
`back/src/app-api/flux/scheduler.ts` (the counter lives with the loop that dispatches) ·
the chain-root accounting shared with `TASK-S3` · new env vars + `env-vars-sync`

## Settled while implementing (2026-09-03)

**The condition-node loop is not reachable in today's engine, so X could not be negative-controlled
at runtime.** The scenario this task asks to reproduce — always-true condition, `loopBehavior` other
than `'continue'`, a back edge — was built against `back@origin/production` and the run finished in
under a second instead of looping. `completeCondition` (`flux/scheduler.ts`) adds the condition to
`completed` and nothing removes it, and back edges are excluded from the dependency graph, so the
node is never re-dispatched; `currentLoopCounter` increments once per run, or once per iteration when
the condition sits inside an `arrayNode` body. X still ships — it is cheap and it holds if the node
ever becomes re-dispatchable — but it is recorded as **unverifiable at runtime**, not as a proven
fix. The runaway that *is* reachable is `arrayNode`, which iterated its stored list with no ceiling
at all; that one was reproduced and stopped (20 items capped to 5).

**The API response keeps its current shape.** When a ceiling stops a run, the terminal state is
written to `flows_logs.status` (`Stopped by run execution budget` / `Stopped by chain execution
budget`), and that is the run's recorded state. The synchronous `POST /flux/api-v2` reply still
returns `success` with the partial output, because the controller answers `{ message }` through
`MessageDto` and the response contract depends on more than this task. Surfacing the stop to the
caller is deliberately **out of scope** — a `stoppedBy` field was written, measured against the
controller, and reverted rather than left as a field nothing reads.

**The ceilings stay env-only here.** Per-company defaults, per-agent overrides and a screen to manage
them are follow-up card `868m10e1z`, with resolution order `agent > company > env`. That card also
carries the open question of whether an agent may raise a ceiling above the platform env value —
which is the question of whether the budget is still a guarantee.

## Post-release validation

The local validation (2026-09-03) proved the ceilings against a real running API, but with the
`execution_budget` flag on in one process and hand-lowered ceilings. Three things can only be
answered after the release, and this is the list to work through — in order, per environment
(dev → staging → prod), because the flag is per environment and the numbers are not.

1. **Flag off, nothing changes.** Before flipping anything, run a real agent in the released build
   with `execution_budget` off and confirm the run behaves exactly as the previous release. This is
   the only check that proves the release is revertible by the flag rather than by a deploy.
2. **Flag on, the ceilings never fire on real traffic.** Flip the flag with the shipped defaults
   (150 / 12000 / 50000 / 200000) and watch for `flux.budget.*` log lines for one full cycle.
   **Any occurrence is a false refusal until proven otherwise** — the defaults sit far above the
   largest value measured in dev+staging, so a hit means either a real runaway (which is the point)
   or a flow bigger than anything the measurement saw. Classify each one; PLAN §3.3.2 applies after
   release exactly as it does before it.
3. **The prod re-measure that `D15` still owes.** *Runbook: `.claude/tasks/worker-flow-execution-epic/s4-prod-ceilings.sql`* — one
   read-only `WITH ... SELECT`, accepted by the `ec2-tunnel-prod` validator, run with
   `QUERY="$(cat .claude/tasks/worker-flow-execution-epic/s4-prod-ceilings.sql)" node .claude/skills/ec2-tunnel-prod/templates/read-query.mjs`.
   It returns one row per ceiling: the distribution, the ceiling suggested by an explicit margin
   (50x / 10x / 100x over the observed maximum, floored at the shipped defaults), and
   `would_refuse_today` — the count of stored flows that ceiling would refuse, which **must be 0**.
   A row with `sample_size` 0 means prod holds no data for that metric: keep the floor and report
   the number as unverified rather than as measured. The query was validated against dev, where it
   reproduces the numbers below exactly; needs `SSH_HOST_PROD` / `DB_HOST_PROD` /
   `PGPASSWORD_PROD` in `.env`, which were not configured when the task shipped. The ceilings were set from dev+staging, whose
   distributions are identical (`loopCount` p50 3 / max 20, `processorArray` p50 7 / p95 81 /
   max 963, node executions per run max 42) and therefore share an origin. Re-run the three queries
   against prod — `flows_nodes.data->>'loopCount'`, `jsonb_array_length(data->'processorArray')`,
   and executions per run — and raise a ceiling if prod holds anything above it. This needs
   `SSH_HOST_PROD` / `DB_HOST_PROD` / `PGPASSWORD_PROD` in `.env`, which were not
   configured when the task shipped.

**Two standing re-checks, not one-offs:**

*   **X becomes verifiable if the scheduler changes.** X is unverifiable at runtime today because
    the condition node is never re-dispatched. Any change to `completeCondition`, to how back edges
    enter the dependency graph, or to condition handling in the prefetch path makes the loop
    reachable again — and the negative control this task could not run becomes runnable. Re-run it
    then, rather than assuming X is dead code.
*   **The array ceiling is the one that fires first.** `processorArray` is the only shape that
    iterates without a system bound today, and its stored maximum (963) is within one order of
    magnitude of the shipped ceiling (12000). Watch it before the other three.

**Carried forward, not validated here:** per-company defaults and per-agent overrides with the
`agent > company > env` resolution, plus the screen that shows the effective value and its source —
follow-up `868m10e1z`. Until that ships, the only lever in production is the env var plus a
redeploy, which moves the ceiling for every tenant at once.

## Cleanup review, 2026-09-03 — what it found, and what is still open in code

Four review passes (reuse, simplification, efficiency, altitude) ran against the shipped diff.
Reuse found nothing: there is no shared numeric-env helper in the repo (every site hand-rolls its
own), and `ChainBudgetRegistry` duplicates none of `RunCancellationService` (a boolean TTL cache),
`McpRunQuotaService` (a daily DB counter) or `RunLogCollector` (aggregates only at `finalize()`, so
it cannot bound a chain while it is still running). The rest is open, in severity order.

**1. The prefetch engine bypasses the run and chain ceilings entirely.** `chargeNodeExecution` is a
closure inside `apiV2`, called only from the classic dispatch loop and the `arrayNode` body loop.
When `isPrefetchMode()` and `canUsePrefetchForFlow()` both hold, `runApiV2FlowLoopPrefetch` runs a
second, independent dispatch pipeline that never touches the budget — and its
`PREFETCH_SUPPORTED_NODE_TYPES` includes `libraryNode` and `nodesBox`, the two types that build the
recursive chains the chain ceiling exists to bound. **Latent today:** `FLUX_EXEC_MEMORY_MODE` is
absent from `.env.example` and from the env docs, so `getFluxMemoryMode()` returns `legacy`
everywhere unless a task definition sets it explicitly — which is exactly why the post-release
checklist has to confirm the value per environment before trusting the ceiling. The deeper seam is
the `dispatchHandler` that both the prefetch loop and the single-node runner already funnel
through; charging there covers both engines instead of one.

**2. The per-node ceiling reports the wrong terminal status.** `executionBudgetRunStatus` is a
two-way ternary over a four-value enum: `node_iterations` falls through to
`'Stopped by run execution budget'`. So a run stopped by the iteration ceiling is labelled as a
run-budget stop — which contradicts the acceptance criterion that the three reasons be
distinguishable. `CEILING_LABEL`, two lines above, already has the right label for every ceiling;
the status should derive from it rather than from a second table that drifts.

**3. The array ceiling is the odd one out.** It truncates the slice, logs, emits a socket event —
and the run still finishes `Successfully ran`. The other two ceilings set a terminal state. Either
the array ceiling should fail the run like its siblings, or truncation must reach the run status,
because a console line and an ephemeral socket event leave nothing durable for anyone asking why an
array stopped short. It also re-logs identically on every re-dispatch of the same node, with no
per-node guard, where the other ceilings self-bound via `stoppedByBudget`.

**4. Two flag reads serialised.** `NODE_CANCEL_IN_FLIGHT_FLAG` and `EXECUTION_BUDGET_FLAG` are
awaited one after the other, each an uncached `findOne`. They have no data dependency, and this runs
once per run *plus* once per sub-flow call — `Promise.all` removes a round trip per nesting level.

**5. Smaller, agreed but unfixed:** `systemLimitCheck` is the negation of `systemLimitExceeded` and
both are threaded through payloads; `chargeCost` / `totals().cost` / `openChains()` have no consumer
until `TASK-S3` and nothing in the file says so; `resolveExecutionBudget()` re-parses four env vars
per run and could be resolved once at bootstrap; the counter increments even when the flag is off.
The ref-counting in `open`/`release` was challenged and **confirmed necessary** — nested `apiV2`
calls collapse onto the same `chainRootKey`, so a child's `release()` would delete the entry
mid-run and silently stop the parent accumulating.

**Decided 2026-09-03.** Items **1 and 2 were applied**; item 3 is still open (options below); items
4 and 5 are cleanups that can travel with the next change to this file.

*   **1 — fixed at the scheduling seam.** `runApiV2FlowLoopPrefetch` now receives the same
    `chargeNodeExecution` closure and charges inside the scheduler it hands to `runPrefetchFlow`:
    `nextReady` charges the node it is about to release and returns `null` on a breach, so the
    prefetch loop ends the way it already ends when there is no ready node, and the method returns
    `stoppedByBudget` to the caller. Charging at *scheduling* rather than at dispatch is what makes
    the two engines share one accounting point — neither engine can execute a node it was never
    handed. **Not covered by a unit test:** the wrapper lives inside a private method behind
    `runPrefetchFlow`; it is verified by types and by reading, and needs one manual run with
    `FLUX_EXEC_MEMORY_MODE=prefetch` on a supported flow before the flag is enabled anywhere.
*   **3 — fixed as option B: the truncation reaches the run status.** The array ceiling still
    truncates (option A, failing the run, would take away a partial result that works today, from
    the very tenants closest to the ceiling; option C, a pre-flight refusal, cannot exist outside the
    node because `processorArray` is recomputed at run time). What was wrong was not the truncation
    but its *invisibility*: the run read `Successfully ran`. Now every capped node is recorded as an
    `ArrayTruncation` (`nodeId`, `requested`, `processed`); the run ends in a terminal state of its
    own, `Completed with truncated array`, and the flow log carries `processed N of M items across K
    node(s)`. Precedence is deliberate and tested: a node error, a cancellation and a budget stop all
    outrank the truncation, because they say something worse about the run; the truncation only
    replaces `Successfully ran`.
*   **2 — fixed.** `executionBudgetRunStatus` now switches on a `CEILING_RUN_STATUS` record with a
    distinct string per ceiling (`node iteration` / `array item` / `run execution` / `chain
    execution` budget). Negative control: restoring the old ternary turns the new test red
    (4 distinct statuses expected, 2 received).

## The env deploy script

`node etc/execution-budget-env.mjs --env <dev|staging|prod>` validates the five variables this task depends
on against the **real ECS task definition** for that environment (the names come from the three
`cicd_*.yml` workflows: `api-task-definition-<env>` / `api-container-<env>` / `enhancedai-<env>` /
`api-service-<env>`). It reports, per variable, the *effective* value the app would compute — via
`resolveExecutionBudget`, the same function the run uses, so the script cannot drift from the
contract — and one of four verdicts:

| verdict | meaning |
|---|---|
| `OK` | declared and equal to the shipped default |
| `DEFAULT` | not declared; the shipped default applies |
| `OVERRIDE` | declared and deliberately different — reported, not an error |
| `INVALID` | **fails the run**: the value is not a positive integer |

`INVALID` is the whole reason the script exists. `readCeiling` uses `Number.parseInt`, which does not
fail — it *truncates*. `FLUX_MAX_ARRAY_ITEMS=12_000` becomes **12**, `1e3` becomes **1**, and
`prefech` for `FLUX_EXEC_MEMORY_MODE` reads as `legacy`. Every one of those deploys "successfully"
and quietly moves the ceiling by three orders of magnitude; nothing in the app logs it. The tests
pin exactly those three cases (found *by* the tests — the first version of the validator assumed a
bad value fell back to the default, and it does not).

Applying is opt-in and staged: `--set KEY=VALUE` (repeatable, only the five managed keys) prints a
plan and stops; `--yes` registers a new task-definition revision, leaving running tasks on the old
one; `--update-service` is what actually rolls it out; prod additionally demands
`--i-know-this-is-prod`. It refuses to apply values that would be `INVALID`, and refuses a no-op.
Every unrelated variable in the container definition is carried over untouched (`mergeEnvForDeploy`,
tested for that). The `execution_budget` feature flag is a database row and is deliberately **out of
scope** for the script — see the table below.

### What the three environments actually hold, 2026-09-03

The script, run with real AWS credentials:

| env | task definition | the five variables | engine | verdict |
|---|---|---|---|---|
| dev | `api-task-definition-dev:2403` | none declared | `legacy` | PASS |
| staging | `api-task-definition-staging:758` | none declared | `legacy` | PASS |
| prod | `api-task-definition-prod:794` | none declared | `legacy` | PASS |

Three things follow, and they change the release.

**Nothing needs to be applied.** No environment declares any `FLUX_MAX_*`, so the effective ceilings
are exactly the shipped defaults — the values this task set. There is no env deploy to do, and
`--set` should stay unused: pinning a default into a task definition is how the code default and the
running value drift apart later, and a pinned value survives every future change to
`DEFAULT_EXECUTION_BUDGET` silently. Declare a variable only to *deviate* from the default in one
environment, and then the script's `OVERRIDE` verdict is there to keep it visible.

**No truncated value exists anywhere.** The `INVALID` case the script was built for did not fire in
any of the three; the ceilings are what the code says they are.

**Every environment runs the legacy engine.** `FLUX_EXEC_MEMORY_MODE` is undeclared in dev, staging
and prod, so `runApiV2FlowLoopPrefetch` — the path whose budget charge has no unit test — **is not
running anywhere today**. That drops the risk of finding 1 to zero for this release: the manual
`FLUX_EXEC_MEMORY_MODE=prefetch` check becomes a precondition for whoever flips that mode, not a
blocker for enabling `execution_budget`. Re-run this script before flipping it. It lives in `etc/`, outside the API: it is an ops tool, not application code, and it carries its own `--self-test` (the assertions that used to be a jest spec) plus a drift guard that refuses to run when its copy of the shipped defaults disagrees with `back/src/app-api/flux/execution-budget.ts` — `--contract <path>` points it at that file when the checkout sits on an older branch, and an unreadable contract downgrades to a warning rather than a refusal. `etc/` is gitignored, so the script is local to a machine, not shared — whoever needs it copies it, and this section is the record of what it does.

The only thing left to deploy for this task is therefore the **database flag**, not an env var.

## Release checklist for this task — the flags

Both flags must be checked per environment, because each one can silently void a ceiling:

| flag | where | why it matters |
|---|---|---|
| `execution_budget` (feature_flags row) | dev → staging → prod, in that order | seeded **disabled** by `1788460000000-SeedExecutionBudgetFlag`. Until it is on, all four ceilings are inert; it is read uncached per run, so flipping it needs no redeploy |
| `FLUX_EXEC_MEMORY_MODE` | task definition per environment | selects which engine runs. Both engines now charge, but the prefetch path is the one with no test — confirm the value you are actually running before trusting the run/chain ceilings |
| `FLUX_MAX_*` (4 vars) | task definition per environment | absent = the shipped defaults (150 / 12000 / 50000 / 200000). Confirm they are either unset or set deliberately; a stale value from another environment is the likeliest source of a false refusal |


## The prod measurement, 2026-09-03 — and the correction it forced

Run against production (`s4-prod-ceilings.sql`), sample sizes an order of magnitude above dev:

| ceiling | sample | p50 | p95 | p99 | max in prod | shipped default | margin over max |
|---|---|---|---|---|---|---|---|
| `FLUX_MAX_ARRAY_ITEMS` | 749 | 8 | 116 | 684 | **8555** | 10000 | **1.17x** |
| `FLUX_MAX_NODE_ITERATIONS` | 834 | 3 | 3 | 15 | 40 | 1000 | 25x |
| `FLUX_MAX_RUN_NODE_EXECUTIONS` | 32430 | 1 | 9 | 22 | 438 | 50000 | 114x |

`would_refuse_today` was 0 on all three, so nothing shipped would refuse a stored flow. **But the
array ceiling is 17% away from real traffic** — the 10000 default was chosen from dev, whose largest
array is 963, and prod holds one of 8555. An array one sixth larger than today's biggest would be
silently truncated. That is the ceiling to change.

**The per-run number is a lower bound, not a measurement.** `s4-prod-ceilings.sql` counted
`jsonb_array_length(logData->'nodes')`, which is the top-level list only, and
`RunLogCollector.startLoopBody()` files loop-body executions under the parent node's `innerSteps`
(`space_run_logs/run-log-collector.ts`) — so an `arrayNode` over 8555 items contributes **one**
entry to `nodes` and 8555 x body to `innerSteps`. The query undercounted exactly the shape Y bounds.
`s4-prod-run-executions.sql` walks `innerSteps` recursively and returns the real distribution; run
it before trusting any Y derived from 438. (A `$.**.nodeId` jsonpath was tried first and rejected:
it double-counts, returning 12 for a document holding 6 executions.)

**Decision, 2026-09-03 — the ceilings applied.** The instruction was to keep every ceiling *close*
to the observed maxima, a margin between 1.1x and 1.5x, and to proceed without waiting for the
corrected Y query. Applied:

| env var | from | to | margin | why |
|---|---|---|---|---|
| `FLUX_MAX_NODE_ITERATIONS` | 1000 | **150** | 1.5x of 100 | the margin is taken over the *product's* bound, not the stored max. `DecisionPaths.tsx` sets `inputProps={{ min: 1, max: 100 }}`, so 100 is a value a user can legitimately type today; 1.5x of the stored max (40) would be 60 and would refuse the UI's own maximum |
| `FLUX_MAX_ARRAY_ITEMS` | 10000 | **12000** | 1.4x of 8555 | 8555 is the largest stored `processorArray`. Caveat below: the stored length is not the runtime bound |
| `FLUX_MAX_RUN_NODE_EXECUTIONS` | 50000 | **50000** | — | left wide deliberately. 438 is an undercount (`nodes` only, loop bodies live in `innerSteps`), and one legitimate run at the array ceiling costs 12000 executions per body node, so a Y near the observed max would refuse the very runs the array ceiling permits |
| `FLUX_MAX_CHAIN_NODE_EXECUTIONS` | 200000 | **200000** | — | the shipped 4x ratio over Y |

**Why the array ceiling still cannot be tightened to 1.1x.** `processorArray` is recomputed at run
time from upstream data, not read from the stored node: `helpers.ts` builds
`content: newObject['contentData']?.text` and passes it through `processorArrayFc(formData)`. The
749-row distribution therefore describes what users *saved*, not what the engine *iterates* — a
node whose stored array is 8 can split a fetched document into thousands of items. 12000 is 1.4x the
largest stored value and, for the runtime case, the first real bound the platform has ever had; the
post-release watch on `flux.budget.array_capped` is what closes the gap between the two.

**Y stays provisional.** `s4-prod-run-executions.sql` (walks `innerSteps` recursively) was not run;
the number above is a compound bound, not a measurement. When that query runs, Y should be re-derived
from it and the 4x chain ratio re-applied.

## The Y re-measure, 2026-09-23 — provisional closed

`s4-prod-run-executions.sql` ran against production, walking `innerSteps` recursively as designed:

| metric | sample (runs) | p50 | p95 | p99 | max observed | shipped `FLUX_MAX_RUN_NODE_EXECUTIONS` | margin over max | would refuse today |
|---|---|---|---|---|---|---|---|---|
| node executions per run, loop bodies included | 1218 | 7 | 59 | 89 | **116** | 50000 | 431x | **0** |

This supersedes the 438 compound bound above, which was `jsonb_array_length(logData->'nodes')` — the
top-level list only, undercounting the shape this query is built to see. The two numbers are not
directly comparable per run (each is a max over a different run in the sample), but the recursive
count is the one Y is supposed to bound, and it is what this table reports.

**Y needs no change.** The shipped default (50000) already sits 431x above the real observed maximum,
`would_refuse_today` is 0, and the chain ceiling (200000 = Y × 4) inherits the same margin. Per
`PLAN.md` §3.3.2 — report the distribution, not just the maximum — the p50/p95/p99 above show the
431x margin is not a single-outlier artifact: even p99 (89) sits three orders of magnitude under the
ceiling. No ceiling change follows from this measurement.

## Exercising the ceilings through MCP — the prompt (rewritten 2026-09-04)

The ceilings need a customer-shaped flow to run against, not a unit fixture: the point is that a
real client, building through the MCP surface, hits a platform limit and gets a legible terminal
status. Two constraints shape the prompt. It must spend **machine resources only** — no generative
or AI node anywhere, so a ceiling test costs no tokens and no credits. And it must be buildable by
`create_agent`/`add_node`/`connect_nodes` alone, because that is the surface under test.

The first version of this prompt built the flow around the arrayNode's *reference* to a node ahead
as the soft loop limit. That reference is real — it is `data.executing` — but it is an optional
override, not how the body is normally designated, so the prompt was asking for a shape the product
does not build. The wiring below is read off `de6c4be5-0ab9-46cf-aa81-acd5225de195` ("sequence
node") in dev, a flow built by the UI, and cross-checked against the derived handle registry and
the executor.

### The verified wiring

```
globalStarter      --a----------> arrayNode.input             control: starts the sequence
varInputNode       --output-----> arrayNode.content           data:    the list, e.g. "a,b,c,d"
arrayNode          --outputFlow-> outputController.input      control: puts the body in plan order  
arrayNode          --output-----> outputController.contentIn  data:    the current item
outputController   --contentOut-> outputObjectNode.input      data:    the accumulated result
```

Both edges out of the arrayNode are needed, and they do different jobs. The executor does not read
the graph to find the body — it derives it from **plan order** (`flux.service.ts:3878-3897`):
`firstId` is the node immediately after the arrayNode in `allNodesIds`, and `loopingToId` is
`data.executing` when set, otherwise that same next node; the body is the plan-order slice
`[firstId .. loopingToId]`. So the `outputFlow` control edge is what places the body node after the
arrayNode in plan order and makes it execute at all, while the `output` data edge delivers the
current item to it. `executing` is the optional override that **extends** the body past a single
node — it names a node further ahead as the last one in the loop, which is the soft limit. The
canonical flow omits `executing`, so its body is exactly the one next node.

The body must be a node that executes: `richTextBox` has `canContinueExecutionChain: false` and no
control target handle, so `connect_nodes` refuses `outputFlow -> richTextBox.input` correctly.
`outputController` (Display Box) is what the product uses, and it carries `input` +
`contentIn`/`contentOut`. A flow with only the data edge builds fine, runs, reports `completed` —
and iterates nothing.

Result shape, from that flow's run: `outputObjectNode.textData` holds one entry per iteration
(`<bodyId>#0 .. #N`) plus a bare `<bodyId>` entry equal to the **last** iteration. That is the
signal to assert on — per-iteration entries, not a single blob.

### Two rules that silently void the test

- **Node ids must contain their type name.** `helpers.ts:196` and the sibling branches through
  `:674` resolve a data edge by testing `source.includes('<type>')` against the source node **id**,
  not its `type`. The UI generates type-prefixed ids, so this works there by construction. Via MCP
  the client picks the id: with `an1`/`tx1` every downstream value resolves to `''` while the run
  still completes and every node still executes. Use `arrayNode_<suffix>`,
  `outputController_<suffix>`, and so on. Proven by a negative control — the same flow, ids the only
  difference, agents `e8600e7f` (empty) and `349fca53` (correct) in dev.
- **An edge into `content` re-derives `processorArray`.** `processorArrayFc(formData)` rebuilds the
  array from the incoming text and wraps each item as `preInput + ' ' + item + ' ' + postInput`, so
  a `processorArray` set explicitly by the client is overwritten. Either feed `content` by edge and
  let it derive, or set `processorArray` and leave `content` unconnected — not both. The canonical
  flow stores the array already wrapped (`["[inicio] a [fim]", ...]`), which is the derived form.
- **`endingPoint` is ignored when `auto: true`.** The executor computes the range as
  `startingPoint - 1` to `auto ? processorArray.length - 1 : endingPoint - 1`
  (`flux.service.ts:3887-3890`), so with `auto: true` the whole array is processed whatever
  `endingPoint` says. `startingPoint` is 1-based and, when absent, `startingPoint - 1` is `NaN` —
  which `slice` happens to treat as 0. The canonical flow relies on that accident; set
  `startingPoint: 1` explicitly instead.

### Which flow exercises which ceiling

`maxNodeIterations` (X, 150) is charged on the **loop node** path only — `loopEvaluation` in
`flux.service.ts:6924-6999`, i.e. a node with `loopCount`/`loopBehavior`. The arrayNode body does
**not** charge against it: each body iteration calls `chargeNodeExecution` (`:3293`), which tests
only the run and chain totals. The array has its own ceiling, applied as truncation of the
requested slice (`:3917-3923`). So one flow cannot exercise all four, and the prompt asks for three.

| Flow | Shape | Ceiling under test | Expected terminal status |
|------|-------|--------------------|--------------------------|
| A | arrayNode, ~20 items, in-range | none — control | `Successfully ran` |
| B | arrayNode, `processorArray` above `FLUX_MAX_ARRAY_ITEMS` | `array_items` | `Completed with truncated array` + `processed N of M items across K node(s)` |
| C | loop node with `loopCount` above `FLUX_MAX_NODE_ITERATIONS` | `node_iterations` | `Stopped by node iteration budget` |

Lower the env ceiling for the environment under test rather than building a 12000-item flow — the
env script (`etc/execution-budget-env.mjs`) validates and applies the override, and B stays cheap.

### The prompt

> Build me three flows in the FluxPrompt workspace, in the folder I name, using only the MCP tools.
> Use no AI, model, image, audio or web-search node anywhere — these tests must cost no tokens and
> no credits, only machine time. Give every node an id that starts with its own type name followed
> by an underscore and a short suffix (for example `arrayNode_a`, `outputController_a`) — the
> backend resolves data edges by matching the type name inside the node id, and any other id makes
> the values arrive empty while the run still reports success.
>
> **Flow A — control.** A `globalStarter`; a `varInputNode` whose text is 20 comma-separated items;
> an `arrayNode` with `options: "Custom Separator"`, `customOperator: ","`, `startingPoint: 1`,
> `endingPoint: 20`, `preInput: "[start]"`, `postInput: "[end]"`, `auto: true`; an `outputController`
> as the loop body; an `outputObjectNode`. Wire it as: starter `a` into `arrayNode.input`;
> `varInputNode.output` into `arrayNode.content`; `arrayNode.outputFlow` into
> `outputController.input`; `arrayNode.output` into `outputController.contentIn`;
> `outputController.contentOut` into `outputObjectNode.input`. Do not set `processorArray` yourself —
> the edge into `content` derives it. Run it, then read the agent back and report
> `outputObjectNode.textData`: I expect 20 per-iteration entries `outputController_a#0` through
> `#19`, each wrapped with `[start]`/`[end]`, plus a bare entry equal to the last one.
>
> **Flow B — array ceiling.** Same shape, but the `varInputNode` text must hold more items than the
> environment's `FLUX_MAX_ARRAY_ITEMS` allows. Keep `auto: true` and leave `endingPoint` at the item
> count — with `auto` on, the executor derives the range from the array length and ignores
> `endingPoint`, so the whole list is requested and the ceiling is what truncates it. Run it and
> report the run's terminal status and the truncation message, plus how many per-iteration entries
> actually landed in the output.
>
> **Flow C — node iteration ceiling.** A `globalStarter` into a loop node whose `loopCount` is above
> the environment's `FLUX_MAX_NODE_ITERATIONS`, with a cheap body and an `outputObjectNode`. Run it
> and report the terminal status and the iteration count reached.
>
> For each flow, report the agent id, the run id, the terminal status, and the number of iterations
> observed. Do not conclude a flow iterated from a `completed` status alone — read the
> per-iteration entries in the output node and count them.

### What to record from a run

The terminal status and, for B, the truncation message are the deliverable — they are what a
customer sees, and the S4 contract is that each ceiling is non-confusable. Record them per
environment alongside the ceiling values in effect, since the ceilings are env-overridable and a
status without its ceiling value is not reproducible.

## Addendum, 2026-09-08 — the dev exercise: what is proven, what is not

Everything below was measured against **dev** (`enhancedai-dev` / `api-service-dev`), by overriding the
ceiling env vars on the ECS task definition, running a flow, and reading back the terminal status from
`flows_logs` plus the `flux.budget.*` line from CloudWatch log group `/ecs/api-task-definition-dev`.
The ceilings are env-overridable, so every result below is recorded with the values in effect.

### The task definitions used

| revision | `NODE_ITERATIONS` | `ARRAY_ITEMS` | `RUN_NODE_EXECUTIONS` | `CHAIN_NODE_EXECUTIONS` |
|---|---|---|---|---|
| 2413 (baseline) | — | — | — | — |
| 2414 | — | — | — | 200 |
| 2415 | — | — | 20 | 600 |
| 2416 | 3 | 5 | 200 | 600 |
| 2417 | — | 100 | — | 200 |

A dash means the var is absent and `readCeiling` falls back to the compiled default
(`execution-budget.ts`): 150 / 12000 / 50000 / 200000.

### Three of the four ceilings are proven end to end

**`chain_executions`.** With 200 (TD 2414), four consecutive runs of the `libraryNode` cycle
A→B→C→A were each capped at exactly 200 node executions, and every run in the chain ended
`Stopped by chain execution budget` — 61, 56, 41 and 41 rows respectively, one per run in the chain,
not retries. The log line is

```
flux.budget.chain_executions
  reason: "System chain execution budget reached (201/200) — platform limit, not this node's own limit"
```

with `chainRootKey` equal to the parent run's id. Re-measured at 600 (TD 2416) the same shape appears,
counting up 601…615 as the nested runs unwind. The overshoot past the ceiling is the number of nested
runs still unwinding, not extra work: the charge happens *before* execution
(`flux.service.ts:3368-3369`, `stoppedByBudget = chargeNodeExecution(); if (stoppedByBudget) break;`),
so real work is capped exactly and only the counter runs ahead.

**`run_executions`.** With 20 (TD 2415), a purpose-built flow — a `globalStarter` into a 30-item
`arrayNode` whose body is a single `outputController` — stopped on the 21st execution:

```
flux.budget.run_executions
  execId: 5b1e06de-…, chainRootKey: 5b1e06de-…      (same value → a single-run chain)
  reason: "System run execution budget reached (21/20) — platform limit, not this node's own limit"
```

`flows_logs.status` = `Stopped by run execution budget`. The run counter breached before the chain
counter (600 at the time), which is the order `execution-budget.ts:85-88` specifies.

**`array_items`.** With 5 (TD 2416), the *same flow with the same 30 items* — the only change being the
env var — ended `Completed with truncated array` instead of exhausting the run budget. That is the
cleanest available control: one variable changed, a different ceiling took effect.

Re-measured at 100 (TD 2417) against a 250-item list, `flows_logs` carries both halves of the contract:

```
status:        Completed with truncated array
error_message: System array ceiling reached: processed 100 of 250 items across 1 node(s)
               — platform limit, not this node's own limit
```

Note where that message lives: `arrayTruncationMessage` (`execution-budget.ts:134-140`) is written to
`flows_logs.error_message` (`flux.service.ts:4982-4995`), **not** to CloudWatch. Unlike the three
`flux.budget.*` ceilings there is no log line for a truncation, so the database is the only place to
read it.

In the same 36-second window a third run of the same flow reported `processed 5 of 250` — the TD 2416
value. Chasing that down produced the sharpest evidence of the day, and it is recorded under the Redis
question below: the 2416 task was still consuming the queue six minutes after ECS had declared the
deployment complete.

### `node_iterations` could not be exercised, and the reason is not the ceiling

Two probes were built and both iterated **exactly once**, so the ceiling was never approached. The
scheduler explains it: `nextReady` / `markCompleted` (`scheduler.ts:295-357`) drive a `completed: Set`
with no re-arm, and `findBackEdges` removes the loop-back edge from `forwardDeps` before the run
starts. A `conditionNode` in the top-level graph therefore executes at most once per run. Both loop
topologies were tried — the back edge landing on the `conditionNode` itself, and the back edge landing
on the first body node upstream of it (the shape used by the real `Loop` flow `542f3372`) — with the
same result.

The stored data agrees. Across all of dev, the most recent `conditionNode` whose persisted
`currentLoopCounter` exceeds 1 was last written **2026-05-30**; every other one is frozen at a
2026-02-14 bulk timestamp. `currentLoopCounter` is reset to 0 at the start of every run
(`flux.service.ts:2838`), so a stored value above 1 is proof that *that run* iterated — and nothing has
in over three months.

The one place a `conditionNode` is still re-evaluated in series is inside an `arrayNode` loop body,
the second call site at `flux.service.ts:4156-4188`. **Do not read this as "the ceiling is broken."**
It is a ceiling guarding a path that the current scheduler has made nearly unreachable; whether the
top-level loop *should* still iterate is a separate defect to triage against the `conditionNode`
itself, and is out of scope here.

### Which ceiling binds depends on the topology, and this is worth stating plainly

The two execution ceilings are not redundant and are not interchangeable:

- **`run_executions` binds when the work is concentrated inside one run** — a loop or an `arrayNode`
  body, where every iteration shares one `execId`.
- **`chain_executions` binds when the work fans out into nested runs** — a `libraryNode` cycle, where
  each nested call opens its own `execId` and therefore its own, freshly-reset run counter.

Measured on the `Ceiling loop agent` chain: **every nested run performs exactly 4 node executions**,
against a run ceiling of 20. The per-run counter can never bind there no matter how long the chain
runs; only the chain counter accumulates. Expecting `Stopped by run execution budget` on that flow is
the natural mistake, and the data is the answer to it.

### The stop is recorded in exactly one place, and reported as success everywhere else

A budget stop sets no `nodeError`. `apiV2Job.processor.ts:80-87` decides the run's outcome purely from
`result.nodeError`, so everything downstream of that decision reports success:

| surface | what it records after a budget stop | correct? |
|---|---|---|
| `flows_logs.status` | `Stopped by … budget` | yes |
| `space_run_logs.status` | `success` | no — measured on a truncated run |
| `mcp_run_status` | `completed`, `error_message: null` | no — measured in dev |
| `flow_execution_status` | `markCompleted` with the partial output | no |
| webhook callback | the success payload | no |
| per-node status in the UI | keeps spinning | no |

The UI spinner has its own cause: `flux.service.ts:4929` handles `stoppedByCancel` only —
`resolveCancelledRunFootprint` + `markCancelled` + `emitCancelledRunStatuses` — and `stoppedByBudget`
is used just twice, to suppress the error log (`:4955`) and to pick the terminal status (`:4986`).

Reusing "cancelled" for this is the wrong fix: `markCancelled` writes `errorMessage: 'Run cancelled'`,
which asserts a user action that did not happen. The shape that fits is to propagate the stop as its
own terminal outcome — `apiV2` returning `budgetStop: { ceiling, reason }` alongside `nodeError`, the
processor treating it as terminal-not-success with the ceiling reason as the message, and `:4929`
becoming `stoppedByCancel || stoppedByBudget`, reusing the footprint and `emitCancelledRunStatuses`
but **not** `markCancelled`.

### Whether the chain budget needs to move to Redis

It does, but not for the reason originally assumed, and not urgently.

`ChainBudgetRegistry` (`chain-budget.ts`) is an in-memory module singleton `Map`, ref-counted per chain
root. The worry was that it splits across API processes. Measured: **`desiredCount` is 1 in dev,
staging and prod alike**, so that split is latent, not active — and the ceilings demonstrably work
today, which is what the three proofs above establish.

What does bite:

1. **Deploys already create the multi-process condition, and the window is minutes long.** Measured,
   not inferred. Task `dbe77b4f` (TD 2416, `FLUX_MAX_ARRAY_ITEMS=5`) reports:

   ```
   stoppingAt: 2026-09-08T14:10:34-03:00
   stoppedAt:  2026-09-08T14:17:04-03:00     ← 6.5 minutes later
   ```

   ECS had already deregistered it from the target group, marked the deployment complete, and reduced
   `describe-services` to a single deployment at 14:11:36 — yet the container kept **consuming Bull
   jobs** until 14:17:04. Three runs of the same flow in a 36-second window prove it: 14:15:31 and
   14:16:07 were served by the new task and truncated at 100, while 14:15:37 was served by the old one
   and truncated at 5. `resolveExecutionBudget()` reads `process.env` per run, so two different answers
   in six seconds can only mean two processes.

   Two consequences. First, any chain in flight across a deploy loses its in-memory counter or gains a
   second one — the ceiling silently becomes 2x for that window. Second, **`deployments == 1` is not a
   valid readiness signal for an env-var rollout**; the rollout watchers used during this exercise
   waited on exactly that and were fooled twice, which is why two probe runs had to be discarded and
   re-run. Wait for the old task's `stoppedAt`, not for the deployment count.
2. **The queue hop already loses chain identity.** `flux.service.ts:6098-6112` — the `triggerOnly`
   branch enqueues without `parentCancelRunKey`.
3. **The webhook mints a fresh `processId` per call** (`flux.controller.ts:471-560`), so a
   webhook-driven self-loop escapes the chain ceiling entirely. That is an *identity* defect, not a
   storage one; Redis is a prerequisite for the fix, not the fix.
4. **The worker migration is the real driver.** `counterNode` already executes on the Temporal worker
   (`flux.service.ts:4663-4680`), and the stated direction is that all node execution moves there. An
   in-memory counter in the API cannot see work the worker schedules on its own.

On the renewing TTL: the metric that matters is the maximum **gap between consecutive executions**
within a run, not the run's total duration, because each execution renews the key. Over 6,502 dev runs
the largest such gap is **7.6 min** (p99.99 = 2.53 min), so a 4h TTL carries roughly 31x margin.
Staging could not be used to corroborate this — it has zero runs.

**Priority: medium, not urgent.** The ceilings hold in the current single-task topology; Redis is what
makes them hold across restarts, the queue hop, scale-out, and the move to the worker.

### MCP gotchas found while building the probes

These cost real time and belong with the two rules already recorded above.

- **A `text` condition compares against `sentimentValue`, not `value`** (`helpers.ts`,
  `evaluateCondition`). A condition authored with `{type: 'text', operator: 'contains', value: 'x'}`
  compares against the empty string and is silently always-true. Use `charCount` unless you set
  `sentimentValue`.
- **`textBox` cannot be a loop body.** Its only source handle is `textOutput` (a data handle) and
  `canContinueExecutionChain` is false, so it cannot carry the execution chain back. `outputController`
  and `counterNode` can.
- **`create_agent` seeds a `globalStarter` plus a `commandTextNode`.** Remove the seeded
  `commandTextNode` before wiring, or the probe calls a model.
- **`get_run_status` reports a budget-stopped run as `completed` with `error: null`** — the same
  false-success described above, reaching MCP clients. Read `flows_logs.status` to learn the truth.
- **`connect_nodes` warns that only `outputHandle-1` is reachable on a `conditionNode` authored through
  MCP**, because it routes on the stored `statement` field. The warning is about the *stored* value;
  at run time the executor writes `statement` before routing, and `outputHandle-0` was in fact taken.

### Why a truncation is invisible in the UI until the page is reloaded

Three separate reasons, all confirmed, and only the third is about the front end.

**The truncated items do run.** `flux.service.ts:3913-3922` takes
`requestedProcessorArray.slice(0, maxArrayItems)` and iterates that normally; the run then continues to
a normal end. A truncation is not a stop — the first N items execute and the remainder are dropped.

Counted directly, with 250 items and `FLUX_MAX_ARRAY_ITEMS=100`:

| depth | node type | executions |
|---|---|---|
| 0 | `varInputNode` | 1 |
| 0 | `arrayNode` | 2 |
| 0 | `outputObjectNode` | 1 |
| **1 (loop body)** | **`outputController`** | **100** |

Exactly the ceiling, no more and no less.

**How to count iterations at all — turn on run-log capture.** `node_executions` records only top-level
nodes; loop-body executions live in `space_run_logs.logData -> nodes[] -> innerSteps[]`, and that table
is only written when the gate at `flux.service.ts:2443-2459` passes:

```
willCapture = spaces.loggingEnabled && folder.spacesId is set && runType ∉ {manual, chatbot}
```

The trap is the middle term. A personal folder has `folders.spacesId = null`, so the gate fails with
`spaceOwnerId: undefined` no matter what `loggingEnabled` says — flipping the flag alone does nothing.
The fix that needs no database write is to move the flow into a folder that already belongs to a
logging-enabled space (`move_agent`). In dev, `Dev to Prod Testing Space`
(`d0ea50e2-63f2-4e3b-98d5-25beb750fc39`), two spaces copied from customers already have `loggingEnabled = true`.
Note also that `space_run_logs.id` **is** the run's `processId`, so a run log is looked up by run id
directly.

**There is a log line, but under a name that does not contain "truncate".** It is
`console.error('flux.budget.array_capped', …)` at `flux.service.ts:3934-3939`, carrying
`System array ceiling reached (250/100) — …`. Searching CloudWatch for "truncated" finds nothing; search
`array_capped`.

**The live socket event is emitted onto a channel nobody listens to.**
`flux.service.ts:3940-3947` emits the truncation as `condition-loop-status` — the event name the
`conditionNode` loop uses — with a payload missing that event's `finalResult` / `userCondition` /
`behavior` fields. Grepping the whole front for `condition-loop-status` returns **no handler at all**;
the front registers roughly thirty socket events and this is not one of them. The event is dropped.

It is also guarded by `if (u?.id)`, so a run triggered by MCP or by a webhook has no user socket to
emit to in the first place.

Finally, the terminal status and the `processed N of M` message are computed only at the end of the run
(`flux.service.ts:4982-4995`) and written to `flows_logs`; neither is ever pushed over the socket. The
UI therefore has no path to them except re-reading from the database, which is exactly why they appear
only after a refresh. Fixing the dropped socket event alone would not fix this — the terminal status
needs to be emitted too.

### The user-facing copy — decided 2026-09-08

The first wording spoke to the engineer who wrote the ceiling, not to the customer who hit it.
`Stopped by run execution budget` / `System run execution budget reached (21/20) — platform limit, not
this node's own limit` uses three words a lay user does not have — *budget*, *execution*, *ceiling* —
and the `(21/20)` reads as an error code.

Two fields, with distinct jobs. **status** is the short badge in the run list and is what
`flows_logs.status` stores. **message** is the plain-language explanation, stored in
`flows_logs.error_message`, and — following the decision to reuse `error` as the terminal state — it is
also the `errorMessage` on `mcp_run_status` and `flow_execution_status`.

| ceiling | status | message |
|---|---|---|
| `run_executions` | `Stopped by system limit — run steps` | Your flow stopped at a system limit: a single run can perform 20 steps. Every node execution counts as a step, including each repeat inside a loop. |
| `chain_executions` | `Stopped by system limit — chained flow steps` | Your flow stopped at a system limit: a flow and everything it calls can perform 200 steps in total. Flows that call each other in a loop reach this quickly. |
| `node_iterations` | `Stopped by system limit — node repeats` | Your flow stopped at a system limit: a single node can repeat 150 times. Lower the loop count or add a condition that ends the loop. |
| `array_items` | `Finished — list shortened by system limit` | Your Sequence node received 250 items, but a system limit allows 100 items per node. The first 100 were processed and 150 were skipped, so the flow finished with partial results. |

The numbers shown are the configured ceilings; the examples use the dev values in effect during the
exercise.

Four things this wording settles deliberately:

- **"system limit", never "budget" or "ceiling".** The phrase appears in both the status and the
  message so the reader learns in the badge alone that this is a platform rule, not something they
  misconfigured. That was the whole point of the old trailing clause "not this node's own limit", which
  can now be dropped.
- **The count reached is not shown to the user.** Only the limit is. The sentence around it already
  says the run stopped because it hit that limit, so `21` adds nothing a customer can act on. It stays
  in the engineering log line, which keeps the `21/20` form, so support loses nothing.
- **`array_items` stays "Finished", not "Stopped".** Measured: with 250 items and a ceiling of 100 the
  loop body executed exactly 100 times and the run completed. Labelling that "stopped" would be a lie
  in the other direction. Its two numbers *are* the information — how much came in and how much was
  processed — so both stay.
- **The shared prefix `Stopped by system limit — …` is load-bearing.** The three stops sort together in
  a status-ordered list and share one grep.

**Consistency requirement.** The same status phrase must appear everywhere the stop is recorded — the
`flux.budget.*` log line, `flows_logs.status`, `space_run_logs.status`, and the socket event payload —
so that one string finds every trace of a given run. The log line additionally carries the terse
`reached/limit` counters; it does not get a different phrasing.

### What was implemented, 2026-09-08

Back — `feat/868m0vfby`, commit `dc603a42`:

- `execution-budget.ts` is the single source for both strings. `executionBudgetRunStatus(ceiling)`
  gives the status phrase, `executionBudgetMessage(ceiling, limit)` the customer sentence, and
  `executionBudgetLogReason(ceiling, reached, limit)` is literally
  `"<status phrase> (reached N, limit M)"` — that concatenation is what makes the consistency
  requirement above mechanical instead of a convention someone has to remember.
  `describeExecutionBudgetStop(ceiling, budget)` bundles ceiling, limit, status and message so no
  caller re-derives any of them.
- `CEILING_LABEL` and `executionBudgetReason` are gone. `helpers.ts` (`evaluateLoopCondition`) now
  builds its `node_iterations` reason with `executionBudgetLogReason`, so `loopStatus.reason` on the
  node opens with the same words as the run status.
- **The false success is fixed at one point.** A budget stop with no node error now sets `nodeError`
  to the ceiling message. `nodeError` is the value the whole downstream already reads, so
  `mcp_run_status` records `error`, `flow_execution_status` takes `markError` instead of
  `markCompleted`, the webhook payload flips to `success: false`, and the `space_run_logs` document
  becomes `error`. No change was needed in `apiV2Job.processor.ts`.
- The end-of-run footprint block runs for `stoppedByBudget` as well as `stoppedByCancel`, so the
  unexecuted nodes stop spinning. `markCancelled` stays gated to a real cancellation — a budget stop
  is not a cancellation and must not be recorded as one.
- New socket event `run-budget-limit` (`BUDGET_LIMIT_EVENT`), emitted for a stop and for an array
  truncation, carrying `{ processId, flowId, ceiling, limit, status, message, nodeId, nodeLabel }`.
  It replaces the `condition-loop-status` emit in the array-cap path, which had no listener.

Front — `feat/868m0vfby` off `production`, commit `a4979089`:

- `Socket.tsx` listens for `run-budget-limit` and toasts `payload.message` verbatim, so the words on
  screen are the words in the run log. A stop toasts as an error, an array truncation as a warning.
  Both carry a **View log** action pointing at that run.
- `storeBudgetLimit.ts` keeps the last 20 runs that hit a limit. `FlowGlobalNode` reads it and stays
  quiet for those runs, so a budget stop is no longer announced as "Agent run cancelled".
- The keying works because a canvas run's `execId` *is* `runLogProcessId` *is* the event's
  `processId` (`flux.controller.ts` mints the uuid, `flux.service.ts:2387` adopts it).

Verification: back `tsc --noEmit` clean, 46 tests green across `execution-budget`,
`node-cancel-outcome` and `loop-system-ceiling`; front type-checks clean under TS 5.9.3 (the
`production` branch still pins 4.9.5, which cannot read the tsconfig at all) and 6 new unit tests
pass. Every new assertion was negative-controlled: breaking the log-reason prefix, the array status
reuse and the "no reached count" rule turned 4 tests red; breaking the truncation wording turned 2
more red; on the front, flattening the error/warning split, dropping the log link and removing the
store cap turned 4 red. All were restored and re-run green.

Not done here: the message is English-only, like the rest of the run surface.

### The regression the dev exercise caught, 2026-09-08

Making `nodeError` carry the ceiling message fixed the false success and broke the nested case in the
same stroke. Back — `feat/868m0vfby`, commit `4090bf2d`.

**What happened.** A run stopped by the chain ceiling returns that message as its `nodeError`. The
`flowCallerNode` and `libraryNode` handlers treated any non-empty `nodeError` as a failed nested run
(`isFlowCallerRunFailed`) and stamped it on themselves with `errorStatusCode: 500`. The parent then
found a node carrying an `errorMessage` and wrapped it again:

```
Execution failed at node "ceiling node | B" — Execution failed at node "ceiling node | C" — …
  × 39 …  Your flow stopped at a system limit: …  … Check the execution logs for details (…).  × 39
```

Two defects in one, both user-visible in the run log's **Error info**:

- the message compounded once per nesting level — 39 prefixes and 39 suffixes around the real sentence
- the caller run recorded `Error while running - 500` instead of the ceiling status, because the
  parent only ever saw "a node failed", never "the chain hit its ceiling"

**The fix.** A budget stop is not a node failure. `isFlowCallerRunFailed` returns `false` when the
nested result carries a `budgetStop`, and both handlers hand the ceiling upward through
`budgetCeiling` — the channel `conditionNode` already used — so the parent sets its own
`stoppedByBudget` and derives the same clean status and message from
`describeExecutionBudgetStop`. Every level of the chain now records one identical, unwrapped
sentence. `apiV2` returns `budgetStop` alongside `nodeError` to make this possible.

**Why the tests did not catch it.** The change altered what crosses the nesting boundary, and the
tests covered only the two sides — the strings in `execution-budget.ts` and the precedence in
`node-cancel-outcome.ts`. Nothing exercised the crossing. Before the change nothing crossed, because
a budget stop returned `nodeError = null`; that is exactly why the gap was invisible. The lesson is
narrower than "write more tests": **when a change alters what a boundary carries, the boundary is the
unit to test.**

The regression test lives in `flow-caller-result.spec.ts`. The first version of its status assertion
was **vacuous** — it hard-coded `budgetTerminalStatus`, so it passed with and without the fix. Only
the negative control exposed that. It now derives both inputs the way the dispatch does (the parent
learns the ceiling *only when* the caller reports no failure), and reverting the fix turns it red
with the literal `"Error while running"` the user saw.

**Still true after the fix:** the client needed no change. It renders `payload.message` from the
`run-budget-limit` event, which always carried the clean sentence; only `nodeError` — the value
feeding the run log and the API — was being wrapped.

### Three front defects the first real run exposed, 2026-09-08

The back was right and the UI still lied. All three were invisible to the unit tests because each
lived at a boundary the tests did not cross.

**1. The socket envelope.** `Gateway.responseToUser` emits `{ data: payload }`
(`app-api/gateway/gateway.ts`). The `run-budget-limit` handler read `payload.processId` straight off
the event, so its guard dropped **every** budget limit in silence. No toast — and with nothing
recorded in the store, the canvas suppression never ran either, so a stopped run was announced with
two green successes: *"ceiling node | A run finished"* and *"Agent run finished"*. Fixed with
`parseBudgetLimitEvent`, which unwraps the envelope, still accepts a bare payload, and rejects
anything unusable. Same lesson as the nesting regression: the payload was tested, the **wire format**
was not.

**2. The log list never refetched.** `useFlowLogs` is a plain React Query with key
`['flow-logs', flowId, page, limit]` and nothing invalidated it when a run ended, so the card line
and the logs modal both showed the previous run until a reload. Not budget-specific — a plain
successful run went just as stale. The canvas now invalidates that key once per run when the run is
over. Note it is *intermittent*: without an explicit invalidation the list depends on an accidental
refetch (window focus, remount), which is why an automated run saw it update and a human watching
the tab did not.

**3. The progress bar never stopped.** `isRunSettled` (`util/runProgress.ts`) restated the rule
`TERMINAL_RUN_STATUSES` already owns and left `CANCELLED` out, requiring every step to be
`COMPLETED`. A run the server stopped never reaches that, so the bar kept saying *"is running"* —
observed at **~7h elapsed**. This was **pre-existing and equally true of a plain cancellation**; the
ceiling work merely started producing that state often.

The last one had a test enshrining it — *"waits for the server when a step was cancelled"*, expecting
`false`. That expectation was deliberate: do not declare the run over while something might still
arrive. But it could not tell *cancelled and still waiting* from *cancelled and finished*. The rule
now settles when nothing is active **and every step is terminal**, which keeps the protected case
intact (a step with no status at all still waits) while releasing the finished one. Changing a
deliberate expectation needs its reason recorded next to it, so the test carries the observation
that justified it.

Settling then exposed a fourth mouth: with the run finally finished, `useRunResultNotification`
would have called a stopped run *"finished"*. It now stays quiet when the run hit a ceiling — the
budget toast already said which limit and why. **Every surface that can speak about a run's outcome
has to know about the ceiling, or it will contradict the run log.** Four of them did.

### Three more the second real run exposed, 2026-09-08

The first round of fixes was validated against the run log, not against a live run, and every one of
the three defects that survived was a boundary the tests still did not cross.

**4. The stop was invisible in the node log.** A node's error is read from `execution_logs` through
`node_executions.executionLogId`, not from the node row. `markNodeStoppedByCeiling` wrote only the
row, so the ceiling was recorded on the run and absent exactly where a user looks for a failed node.
It now writes the `execution_logs` row too, behind the same `NOT EXISTS` guard the canonical error
writer uses, so a retry cannot stack a second row for the same node of the same run.

**5. "Only the root run announces" was decided from a feature flag.** `isNestedRunLog` and
`parentProcessId` both come from the `RunLogCollector`, and the collector is only created when
`space.loggingEnabled` is on. On a space with logging off — which is where this was tested — every
nested run arrived with both null and every one of them announced: 28 distinct `execId`s, 28 toasts.
The rule now also reads `parentCancelRunKey`, the product's own chain marker, passed at all four
dispatch sites regardless of any logging flag. **A nesting decision must not be derived from state
that an unrelated feature owns.**

**6. The packet that ends a run was thrown away.** Only a run whose nodes go through the worker ever
announces itself: the legacy in-API path emits `execId` and never `runId`
(`emitNodeStatus`, `flux.service.ts`). So on a flow built from library and flow-caller nodes the
canvas never adopts a run id, and `Socket.tsx` dropped the one packet that carries one — the end of
the run — for naming an unknown run (`if (!hasRunning) return`). The stopped node kept no status,
the steps never reached a terminal state, and the progress bar stayed green until a reload. The rule
is now the pure `resolveRunStatusPacket`: a packet with nothing running is the *end* of a run, so it
applies its statuses but never clears the canvas, and it is trusted only while no other run has
claimed the flow.

Defect 3 above and defect 6 are the same run reported twice: fixing `isRunSettled` could not settle
anything while the statuses that would settle it were being discarded one layer earlier. **A fix to
a reducer is worth nothing until you have proven its input arrives.**

#### Defect 6 was fixed wrong the first time, 2026-09-09

The first attempt let an ending packet **adopt** the run id when the canvas had none, and kept
ignoring endings that named a different run. On a flow that calls itself that is still broken, and
the DB said so: three flows (`527edd49`, `477f8eb1`, `032ee8b4`) produced ~10 runs of one flow, each
with `inflight = 0` and `err = 1` -- the back was entirely correct, every ending *was* emitted. The
runs unwind innermost first, so the innermost ending arrived first, claimed the flow, and every
later ending including **the root's** was dropped. Before the fix all endings were dropped; after
it, all but one. An ending now always applies and never claims the flow.

A second rule was wrong for the same reason. `counterNode` is in `isTemporalNode`, so it runs on the
worker and its packets carry `runId` while the legacy nodes beside it carry only `execId` -- the
same flow learns a run id from some packets and not others. Each nested run's first worker packet
therefore looked like a fresh run and **cleared every status on the canvas**, including everything
the parent had already completed. `isRunSettled` treats a step with no status as one still waiting,
so the run could not settle even after its ending arrived. The reset now runs only when nothing is
in flight; `FlowGlobalNode` already clears every `executionStatus` where a run really begins.

**A recursive flow breaks any front rule phrased as "the active run".** There is no single active
run: N runs of one flowId share one canvas, one room and one set of node ids. Statuses have to be
last-writer-wins, and only the *reset* may be gated -- on whether anything is in flight, never on
run identity.

#### Defect 7: the run was announced before it was recorded, 2026-09-09

The green line on the global node (`FlowGlobalNode`, `#4CAF50`) is `logsData.data[0]` -- the newest
flow log row's timestamp and status. The canvas settling is what invalidates that list, and the run's
own row was inserted at `flux.service.ts` ~5182 while the websocket statuses went out ~5090. The
refetch therefore raced the insert and won, and the line kept showing the **previous** run after a
run had visibly failed. The toast was never the problem -- it arrived correctly the whole time,
which is exactly why this looked like a front bug for two rounds.

The end-of-run statuses and the ceiling toast now go out **after** `createLog` resolves. The
footprint is remembered instead of announced on the spot, and the ordering is a named rule
(`announceRunEndAfterRecord`) with its own test, because the block it governs lives in a method Jest
cannot import.

**An event that tells a client to go read something must not be emitted before the something
exists.** Three of the seven defects in this task are the same shape: the surface was right and the
timing or the wire format was not.

