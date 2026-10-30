# Where FluxPrompt charges money, and what the charge knows about itself

Working notes assembled while building S3 (`868m0vk05`, spend ceiling + tenancy
cap). Kept here because the answers were expensive to find and are not written
down anywhere else; promote to `docs/` if they hold up.

Raw query output is committed alongside (`w1s4.r*.csv`) so every number below can
be rechecked without rerunning anything against prod.

Every file:line refers to `back/` on `origin/production` as of 2026-09-14.

---

## 1. The three places a charge row is written

Every charge ends as a row in `token_transaction`. Only three methods create
one, all in `src/app-api/product/product.service.ts`:

| method | decl. | carries `execId`/`nodeId` | called from |
|---|---|---|---|
| `updateUserProduct()` | ~1728 | **yes** | `updateTokens()` — the flow path |
| `createVoiceCloning()` | ~746 | no | `voice.service.ts:406`, `eleven_labs.service.ts:432` |
| `chargeUserProduct()` | ~1352 | no | only `cronJobs/chargeUsersPerClonedVoice` |

So: **flow work charges through `updateTokens`; the other two are outside a run
by construction** (voice cloning is a setup action, the cron is recurring
billing for an already-cloned voice). This matters because it is the reason the
large "charges with no execId" share in prod is *not* evidence of a hole.

## 2. `updateTokens` is the funnel

`product.service.ts:994`. Everything flow-related converges here — roughly 170
call sites across the provider services (`replicate`, `clip_drop`,
`buildWithApi`, `anthropic`, `runwayML`, `youtube_transcript`, …).

Two properties worth knowing:

- **It is already idempotent per (execId, nodeId).** `product.service.ts:1016`
  short-circuits with `{ tokens: 0, cost: 0 }` when a row already exists for the
  pair. A retry does not double-charge.
- **It returns `{ tokens, cost }`,** so the computed cost is available at the
  funnel without recomputing anything.

Because there is one funnel with the cost in hand, a spend ceiling belongs
*here*, not in the controller and not per provider.

## 3. How a charge learns which run it belongs to

`execId`/`nodeId` reach `updateTokens` in one of two ways:

1. **Passed explicitly** — what the worker does (see §4).
2. **From `chargeContext`**, an `AsyncLocalStorage` (`product/charge-context.ts`)
   read at `product.service.ts:1013`.

`chargeContext` is established in exactly **two** places, both inside the flux
run loops:

- `flux.service.ts:3507`
- `flux.service.ts:4143`

### The gap that matters for the future

- **`dispatchLegacyHandler` takes `execId` and throws it away.** Its signature
  reads `execId: _execId` (`flux.service.ts:1188`). The argument is accepted and
  deliberately unused.
- **The prefetch engine never enters `chargeContext`.**
  `runApiV2FlowLoopPrefetch` (`flux.service.ts:1501`) passes `execId` down to
  the dispatch, which discards it (above), and sets no context.

Today this is harmless **because prod runs the legacy engine** — the S4 env
audit confirmed dev/staging/prod declare none of the budget variables and all
run legacy. But when prefetch becomes the default (B4/B5), every charge it makes
loses its run identity, and any ceiling keyed on `execId` goes blind to it.
**This is a prerequisite for B5, not a nice-to-have.**

## 4. The worker's charge endpoints

`src/temporal/worker.controller.ts`. All four propagate `execId` **and**
`nodeId` — verified, not assumed:

| endpoint | line |
|---|---|
| `/charge-tokens` | 126 |
| `/charge-api-call` | ~314 |
| `/charge-scrape` | ~378 |
| `/charge-voice` | ~502 |

They only forward; they contain no billing logic of their own. A ceiling added
to `updateTokens` therefore covers the worker automatically.

## 5. The run chain

`chainRootKey = parentRunId || runLogProcessId` — `flux/cancel-run-key.ts`,
via `resolveCancelRunKey`. A sub-flow inherits its parent's key, so an entire
chain accumulates under one identifier. Computed at `flux.service.ts:2519`.

**Nothing persisted this link before S3.** `node_executions` has `execId`,
`flowId`, `nodeId`, `executionLogId` — no parent column; a repo-wide search of
`src/entities/` for `parentProcessId` / `parentRunId` / `parentExecId` returns
nothing (the only `parentId` is on `folder`, unrelated). The chain existed only
in the memory of the process running the flow, which is why a charge arriving
over HTTP could not ask which chain it belonged to.

S3 adds `ChainRootRegistry` (Redis, `flux:chain-root:<execId>`) to publish the
mapping, expiring with the run duration.

## 6. The counters, and why they do not share a backend

| counter | unit | storage | why |
|---|---|---|---|
| `ChainBudgetRegistry` (S4) | node executions | in-process `Map` | counted entirely inside one process's loop; Redis would add a round-trip **per node executed** — up to 50 000 in one run at S4's own ceiling |
| `ChainSpendLedger` (S3) | cost | Redis | the charge arrives over HTTP from the worker and can land on any replica |
| `TenantConcurrencyLedger` (S3) | concurrent runs per org | Redis (sorted set) | admission happens on whichever replica dequeues |

They share the **chain root key**, which is what the task actually guards
against ("two accountants that can disagree about where the root is"). They do
not share storage, because the two units have genuinely different locality.

`ChainBudgetRegistry.chargeCost` used to exist as a second, unused home for
spend; removed in S3 so there is one answer per unit.

### Degradation rule, applied everywhere

When Redis is unavailable every ledger **reports `degraded` and admits the
run**, never refuses. A false refusal is worse than the defect a ceiling fixes
(PLAN §3.3.2). Same stance as the existing `RateLimitStorage`.

When the chain root is unknown, a run is billed **as its own chain** — that
undercounts a chain and can never overcount one, so the error lands on the
admit side.

## 7. Run duration vs. agent job timeout — different things

A trap worth writing down, because it produced a real bug in S3's first pass.

- **`AGENT_JOB_TIMEOUT_MS`** (default 600 000) — Bull's job timeout on the
  `api-v2` queue (`jobs/apiV2Job/apiV2Job.queue.ts`). Was hard-coded.
- **`RUN_MAX_DURATION_MS`** (default 6 h) — how long a flow run may legitimately
  take. Real prod flows exceed an hour.
- **`AGENT_CONCURRENCY`** (default 5) — how many jobs one replica processes at
  once (`apiV2Job.processor.ts:46`). Per replica, **never per tenant**.
- `AGENT_WAIT_TIMEOUT_MS` (30 000) — how long the *client* waits. Unrelated to
  both.

Sizing anything run-shaped from the job timeout drops live runs from the count.

## 8. What the tenant key is

`folder.spaces.company.id`, falling back to `folder.companyUser.company.id` —
the rule `updateTokens` already applied when attributing a charge, extracted to
`product/company-of-flow.ts` so there is one copy. Prefixed (`company:` /
`user:`) so a company id can never collide with a user id.

---

## 9. Measured in prod — 2026-09-14, 180-day window

Queries live beside this file (`s3-q1-run-cost.sql` … `s3-q5-missing-exec-id.sql`);
each carries its own run instructions for bash and PowerShell, resolving the
repo root with `git rev-parse --show-toplevel` so they work from any directory
and on either OS;
raw results in `w1s4.r*.csv` beside it (the same run repeated three times; the small
deltas are the sliding window, not disagreement).

**Cost per run** — 119 245 runs carrying an `execId`:

| | |
|---|---|
| max | 8.156 |
| p50 / p95 / p99 / p99.9 | 0.027 / 0.323 / 1.330 / 3.415 |

False refusals by candidate ceiling: **1 → 1550 (1.30 %)**, 2 → 563 (0.47 %),
5 → 19 (0.016 %), **10 → 0**.

**Cost per chain** — 1151 chains, **216 of them nested (18.8 %)**, max 5.694,
p99 1.714. Same shape: 1 → 31, 2 → 11, 5 → 1, **10 → 0**.

→ **10 is the lowest ceiling with zero false refusals on both dimensions**,
a 1.23× margin over the most expensive run and 1.76× over the most expensive
chain.

**Attribution.** 1 021 523 charges total, **658 253 (64.4 %) with no `execId`**,
accounting for 58.1 % of cost (12 834 of 22 083). Per §1 and §3 these are the
non-flow paths, not lost flow work — a conclusion that comes from the code, not
from SQL, because `execId` and `nodeId` are written together and vanish
together.

**Tenant concurrency.** Busiest org peaked at **21 concurrent runs with a p95 of
20** across 173 runs — sustained, not a spike — against `AGENT_CONCURRENCY = 5`
per replica. Second busiest peaked at 12. The fairness problem is active, not
theoretical.

**Run duration — inconclusive, do not treat as a bound.** Max 17.29 min, zero
runs over an hour. But `space_run_logs` only exists where run logging is
enabled: 1152 runs measured against 119 245 charged runs, about 1 % coverage.
Flows over an hour are reported from the field and this sample cannot see them.
The 6 h default stands until a measurement with real coverage replaces it.

## 10. A caveat about `space_run_logs`

- `totalCost` on the root row **does not include nested runs.** A sub-flow
  finalizes its own document, nested under `logData->nodes[]->subRun`; the
  root's total was already computed from its own nodes
  (`run-log-collector.ts:381` and `:398`). Chain totals need
  `jsonb_path_query(logData, '$.**.totalCost')`, not the column.
- It only exists for spaces with logging enabled (~1 % of runs), so anything
  derived from it is a sample, not a census. Report such runs as
  **unverifiable**, never as passing.

## 11. The unit a ceiling must count: credits, not cost

`updateTokens` computes both numbers from the same charge:

```
cost = usedTokens * userProduct.product.fluxTokenPrice
```

`usedTokens` are **flux credits** — the unit the customer buys and sees.
`cost` is the money that falls out of the customer's plan price
(`fluxTokenPrice` in the seeded plans ranges 0.0011 to 0.003, and is 0 on the
free plan — `database/seeders/product/data.ts`).

A ceiling must count **credits**, for three independent reasons.

**`cost` is forced to zero on two whole populations.** In `updateTokens`
(`product.service.ts:1802`) and again in `chargeUserProduct` (`:1408`):

- `if (trial) { ... cost = 0 }` — every charge on an `INTRO` product
- `else if (totalSpentTokens <= userProduct.extraTokens) { cost = 0 }` — every
  charge still inside a prepaid credit balance

A cost-based ceiling therefore reads **zero** for trial accounts and for
prepaid accounts, and can never fire for either. Those are precisely the two
populations a runaway ceiling exists to protect: the trial account spends our
money with no revenue attached, and the prepaid account has already paid, so
nothing downstream objects either. The credits are counted correctly in both
cases — only the money is zeroed.

**The same ceiling means different things per plan.** 100,000 credits is
100,000 credits to every customer. Ten dollars is 3,333 credits on the most
expensive plan and 9,090 on the cheapest — the cheaper the plan, the more work
the customer is allowed to do before the same ceiling stops them, which is
backwards.

**Credits are the unit a customer can configure.** A per-flow ceiling the
customer sets in the agent's settings has to be expressed in the unit shown in
their own usage screen. That is credits.

So `maxChainSpend` holds credits. The column type (`double precision`) does not
change; only the unit it is read in.

### Converting the prod measurement

The Q1/Q2 measurement (§9) was taken in **cost**, because `space_run_logs`
stores `totalCost`. Dividing by the plan price converts it:

| measured (cost) | at 0.003/credit | at 0.0011/credit |
|---|---|---|
| worst single run, 8.156 | 2,719 credits | 7,415 credits |
| worst measured chain, 5.694 | 1,898 credits | 5,177 credits |
| p999 run, 3.415 | 1,138 credits | 3,105 credits |

The worst run ever observed in 180 days of production is therefore somewhere
between 2.7k and 7.4k credits, depending on which plan ran it.

### Why the default is 100,000 and not 3,000

Two ceilings with two different jobs, and conflating them is what makes any
single number look wrong:

- **The system ceiling** (`DEFAULT_MAX_CHAIN_SPEND`, 100,000 credits) is a
  catastrophe stop. It exists so a runaway loop costs three figures instead of
  being unbounded. It must never refuse real work, so it sits ~13x above the
  worst run ever measured. It is not a budget.
- **The customer's ceiling** (per plan via `maxChainSpend`, and later per flow
  in the agent settings) is the tight one, set by whoever knows what that flow
  is worth. 1,000 or 3,000 credits is a sensible number *there*, chosen
  deliberately by a customer for one flow — not imposed by us on everyone.

A tight global default would refuse real production work today (at 5 cost —
about 1.7k to 4.5k credits — Q1 already shows 19 real runs refused). A loose
global default refuses nothing and still bounds the disaster. The tight number
belongs to the customer, not to the constant.

## 12. Cancellation vs. charging — what happens to a charge after the stop signal

The rule being validated: **a node that is already running and already
spending is not killed by the ceiling.** The ceiling stops the run from
starting more work; it never tries to claw back work in flight.

### The charge path does not consult cancellation

`POST /worker/charge-tokens` (`temporal/worker.controller.ts:220`) resolves the
user product and calls `updateTokens`. There is no cancellation check anywhere
on that path. A charge that arrives after the run was cancelled is recorded
normally — `token_transactions`, `user_product.usedTokens`, `totalBill`, the
reports. This is the behaviour we want, and it already holds: **no change
needed to make a late charge land.**

### Where cancellation does reach into a charge

Cancellation is a **transport** abort, not a billing decision. The signal is
carried on the axios request (`node-cancel-interceptor.ts` attaches the
`AbortSignal` from `node-cancel-watch.ts` to every outbound request), and only
for node types listed in `node-abort-capability.ts`
(`imageGenerator`, `voiceBoxNode`, `commandContentNode`, `audioReaderNode`,
`webSearch`, `reportBuilder`); everything else resolves to `'none'` and runs to
completion.

When a transport abort fires mid-request, axios rejects, the node throws, and
**no charge is written for that node** — while the provider has usually already
billed us for the tokens it produced. That is an under-charge, and it is the
correct trade: we absorb the cost of work the customer asked us to stop rather
than bill them for output they never received. It is recorded here so nobody
later reads the gap as a bug.

### The consequence for the ceiling

Because late charges keep landing, the chain ledger keeps growing **after** the
ceiling has already fired. Two properties follow, and both are requirements on
the implementation:

1. **The stop signal must be idempotent.** Every subsequent charge on that
   chain also reads above the ceiling. Signalling once per chain — not once per
   charge — is what keeps that from turning into a cancel storm. The natural
   place is a Redis `SET NX` on the chain root, the same key space the ledger
   already uses.
2. **The final total is allowed to exceed the ceiling.** A chain stopped at
   100,000 credits will settle somewhat above it, by whatever was in flight.
   The ceiling bounds the *order of magnitude*, not the exact number, and the
   error message must report the measured spend rather than the ceiling.

### The flow, end to end

```
node runs ─► provider bills us ─► worker POSTs /worker/charge-tokens
                                        │
                                        ▼
                             updateTokens  (the funnel, §2)
                                        │
                      ┌─────────────────┴──────────────────┐
                      ▼                                     ▼
          token_transactions +                  ChainRootRegistry.resolve(execId)
          user_product totals                              │
          (always, cancelled or not)                       ▼
                                             ChainSpendLedger.charge(root, credits)
                                                           │
                                                           ▼
                                             over ceiling?  ──no──► done
                                                           │yes
                                                           ▼
                                             SET NX  flux:chain-stopped:<root>
                                                   │              │
                                              already set     first time
                                                   │              │
                                                   ▼              ▼
                                                 done        emit metric,
                                                             signal cancel on
                                                             the existing
                                                             cancelRunKey path
```

Nothing in that diagram kills a request in flight. The cancel signal is the one
S4 already ships, and the loop honours it at the next node boundary — which is
exactly "stop starting new work", not "abort what is running".

## 13. `triggerOnly` — the cost that escapes its parent

`flowCallerNode` (`flux.service.ts:5931`) and `libraryNode` (`:6320`) both
branch on `executionMode === 'triggerOnly'` and call
`apiV2Queue.enqueueApiV2Job({ params: { body, user, flowId, sessionId, ... } })`
without awaiting it. Until this task the enqueued params carried **no
`parentProcessId` and no chain root**, and the only trace of the relationship
was a human-readable string:

```
runType: `flow-caller-node (trigger-only) - flowId: ${flowIdSelected}`
```

which names the *called* flow, not the caller and not the parent run. The
child was therefore the root of its own chain: its own ceiling, its own budget,
and no way for either to see the caller. A flow triggering N children bought N
ceilings.

**Resolved 2026-09-14 — the child now inherits the caller's chain.** Both
branches pass `parentCancelRunKey`, which each method already receives and
which is exactly the chain root. One field carries both halves on purpose:
the child's spend counts against the caller's ceiling, and that ceiling — or a
person pressing stop — reaches the child too.

The alternative was considered and rejected: a separate billing-lineage field
would have attributed the cost to the caller while leaving the child running
when the ceiling fired. A flow triggering children in a loop is the exact
catastrophe the ceiling exists for, so attributing the spend without being
able to stop it is the wrong half to get right.

**What this changes for a user.** Cancelling a parent run now also stops the
`triggerOnly` children it started and had not awaited. Before this they
survived their caller. That follows from the decision rather than being a
side effect of it — the runs are still independent in every other sense, with
their own run logs, their own status and their own duration.

**Why the asynchrony needs no special handling.** `triggerOnly` exists so the
parent does not wait, so the parent's run log is finalised, with its
`totalCost` computed, before the child has spent anything. Nothing writes back
into that closed document:

- *Live ceiling.* The ledger is keyed by chain root with a 24h TTL and no
  `release`, so it accepts a charge from any replica at any later time. A child
  that starts after the parent finished accumulates onto the right chain.
- *History.* `chainRootId` on `token_transaction` (§11) makes the chain total
  `sum(used_tokens) where chainRootId = X` — a query, current by construction.
  The late child needs no update at all.

**Still true, and worth watching.** The parent's own `totalCost` on its run log
still excludes the children, because that number is computed when the parent
finishes. The chain query is the number to trust; the run log's own total
answers a narrower question.

**Measured, and worse than the paragraph above implies (2026-09-18).** The
exclusion is not confined to `triggerOnly`. A parent that *awaits* its called
agents also reports zero: the called run executes in its own `apiV2` invocation
with its own accumulator, and `flowCallerNode`/`libraryNode` return only
`{ nodes }`, dropping the `totalTokensUsed`/`totalCost` that invocation computed.
Four dev runs of `ebd7390a-e682-4c45-ba56-d35ee7484953` charged 0.743, 0.218,
0.303 and 0.803 credit and every one logged `totalTokens = 0`, while runs of the
called flow started directly logged theirs correctly. So for a calling flow the
run log's total is not merely narrower than the chain query — it is empty.
Tracked as 868m6r9py; the ceiling itself is unaffected, since it reads
`token_transaction` and the Redis chain ledger and never this number.

## 14. Two meanings of `execId`, and the charge the guard drops

`updateTokens` refuses to charge twice for the same node run
(`product.service.ts:1056`, introduced by `dddab3d1`):

```ts
const alreadyCharged = await TokenTransaction.findOne({
  where: { execId, nodeId },
});
if (alreadyCharged) return { tokens: 0, cost: 0 };
```

That is correct idempotency only while `execId` identifies **one execution of
one node**. The column carries two different things:

| written by | `execId` is | on a loop's 2nd..Nth iteration |
|---|---|---|
| worker dispatch (`flux.service.ts:716`, `:914`) | a fresh `uuid()` per node run, the id written to `node_executions` | a new pair, charges normally |
| inline charge (`flux.service.ts:3512`) | `runLogProcessId` — the **run** id, constant for the whole run | the same pair, the guard returns `{ tokens: 0, cost: 0 }` |

So a node charged inline that repeats inside one run is billed once, however
many times it runs. Nothing logs the skip: the guard returns a successful
zero, indistinguishable from a free node.

This is a code-level finding, not a measurement. **How large it is in money is
unknown and must not be guessed** — it depends on how many charges land in the
run-scoped regime and how often those nodes repeat. `s3-q6-undercharge.sql`
splits production charges into the two regimes by asking whether the charge's
`execId` appears in `node_executions` (per node run) or in `space_run_logs`
(per run), and reports anything matching neither as `unknown` rather than
counting it as safe.

Two consequences for this task, whatever the number turns out to be:

- **The ceiling undercounts by the same amount.** The chain ledger is fed from
  the same funnel, so a charge the guard drops never reaches Redis either. The
  ceiling is therefore conservative — it can only ever stop later than it
  should, never earlier, which is the safe direction for a false-refusal
  budget of zero.
- **The fix is not to remove the guard.** The guard exists because a retry
  must not double-bill. What is wrong is the key, not the idea: the inline
  path should carry a per-node-run id the way the worker path already does.
  That is a change to charge identity, which is B1's subject, not S3's.

### Other places credits are burned without money being charged

Confirmed in code, all of them deliberate except the last:

- **Trial accounts** — `cost = 0` for every charge on an `INTRO` product
  (`product.service.ts:1829`). Credits are decremented from `trialTokens`.
- **Prepaid balance** — `cost = 0` while `totalSpentTokens <=
  userProduct.extraTokens` (`:1830`, and `:1415` in `chargeUserProduct`).
  Credits are counted, money is not, because it was paid in advance.
- **Cancelled node with a transport abort** — the provider has billed us and
  no charge row is written at all (§12). Neither credits nor money are
  recorded. This one is a real loss, accepted deliberately rather than bill a
  customer for output they stopped and never received.

## 15. Where a run is refused before it starts, and why S3 adds nothing there

S1 (`868m0vfyz`, branch `refactor/868m0vfyz`) builds the pre-flight gate this
task's acceptance criteria referred to. It is a **static** analysis of the
call graph, not a credit check: `analyzeSubFlowCascade` walks the flows
reachable from the root through `fluxBox` and `libraryNode` targets and refuses
two shapes — a cascade deeper than the root flow's `maxCascadeSize`
(`cascade_size`) and a cycle in the call graph (`cascade_cycle`). It refuses in
two places: `flux.controller.ts` returns HTTP 422 before enqueueing, and
`flux.service.apiV2` returns early with an `ExecutionBudgetStop`-shaped object.

> Read that branch against `git merge-base origin/production HEAD`, not against
> `origin/production` — it is 62 commits behind, so a plain diff shows dozens of
> unrelated deletions that are really just prod moving on.

### The interaction with the chain lineage, and why it is benign

S1 gates on `const isRootRun = !parentCancelRunKey;`. §13 makes `triggerOnly`
children carry `parentCancelRunKey`, so after that change such a child is no
longer a root run and **skips the cascade analysis**.

That loses no coverage. The analyzer never reads `executionMode`, so a
`triggerOnly` target is already a node in the graph the root analysed — the
child was re-analysing a subgraph that had just been cleared. It also removes a
subtle wrong answer: re-analysing from the child used the *child's*
`maxCascadeSize` as the limit, when the thing being bounded is one cascade,
which is the root's. The two changes compose correctly, but `isRootRun` now
means something narrower than when it was written, which is worth knowing
before either branch merges.

### A pre-flight for the spend ceiling was considered and dropped

The idea: a run whose chain already claimed a stop (`flux:chain-stopped:<root>`)
should refuse before executing anything, rather than start and die. It would
have been safe by construction — it reuses a decision already recorded for that
chain, so it cannot produce a false refusal.

It was dropped because **the cost is already protected**. The run loop tests
cancellation at the top of the scheduler loop, before executing a node
(`flux.service.ts:3480`), and with the ceiling flag on `cancelWatchEnabled` is
always true (§12). Since a `triggerOnly` child now polls its caller's chain key,
and the ceiling has already written a cancel request against exactly that key, a
child that starts after the stop halts before its first node and spends nothing.

What a pre-flight would still buy is smaller and not about money:

- no run log or execution row for a run that cannot do anything;
- no tenant concurrency slot consumed — `apiV2Job.processor.ts` calls
  `tenantConcurrencyLedger.enter` *before* `apiV2`, so a doomed child holds a
  slot for as long as its setup takes;
- an immediate 422 on the HTTP path instead of an accepted run that dies.

Worth doing eventually as hygiene; not worth doing as protection.

### Decision, 2026-09-16: the pre-flight spend check is not built

The acceptance criterion "the pre-flight credit check runs in S1's existing
DAG-build gate" is met by S1's gate as it stands, and S3 adds no second check
there. The reason is that pre-flight cannot know which branch will run, so it
cannot bound spend; the charge-time ceiling of §11 is what bounds it, and that
ceiling is already in place. A pre-flight refusal would only save the work
between admission and the first charge — hygiene, not protection — and it buys
that at the cost of a new refusal path that could reject a run that would have
completed. Ruled out deliberately, not forgotten.

### One thing to check on the S1 branch

The gate emits two ceilings that did not exist before, `cascade_size` and
`cascade_cycle`. Over HTTP that is a 422 and the front never has to recognise
them. If either is ever emitted over the socket instead, it falls into the trap
§12's front fix covers: `parseBudgetLimitEvent` validates the ceiling against an
allow-list and **drops an unknown one silently**, with no error anywhere. No
front branch for `868m0vfyz` exists yet, so this is unverified rather than
broken.

## 16. The tenant concurrency cap, and how to test that it is fair

### What bounds a tenant today, and what does not

`apiV2Job.processor.ts` declares `@Process({ concurrency:
parseConcurrency(AGENT_CONCURRENCY) })`, default 5 **per replica**. That caps
how many runs execute, not *whose*: one organisation can hold all five slots on
every replica and every other tenant waits behind it with nothing forcing a
rotation.

**Bull's group limiter does not fix this**, which is worth stating because it
looks like it should. Bull 4.16.5 supports `limiter.groupKey`, but the limiter
is `{ max, duration, groupKey }` — a *rate*: at most `max` jobs per `duration`
per group, with the excess moved to the delayed queue. That gives queueing
rather than rejection and per-tenant grouping, but it bounds **admissions per
minute, not simultaneity**. A tenant whose runs last an hour stays inside any
rate limit while holding every slot. Rate is the wrong quantity.

### What the cap actually is

`TenantConcurrencyLedger` already measures true simultaneity: a Redis sorted
set per tenant, scored by start time, with stale members evicted on every read
(`ZREMRANGEBYSCORE` then `ZADD` then `ZCARD`), so a count cannot leak when a
replica dies mid-run — unlike an INCR/DECR pair. `enter` returns the count
*including* the run asking, so a cap of 25 defers the 26th.

The processor defers rather than refuses: it releases the slot it just took,
then calls `job.moveToDelayed`. Three details carry the weight:

- **The slot is released first.** A deferred job that kept its slot would be
  waiting for capacity it is itself holding.
- **`moveToDelayed`, not re-adding the job.** Re-adding mints a new job id, and
  `flux.controller.ts:252` awaits `job.finished()` — the caller would wait
  forever on a job that never completes. `moveToDelayed` keeps the same job, so
  the caller still gets its result, later. The method exists on a Bull job at
  runtime (`bull/lib/job.js:349`) but is absent from the package's typings, so
  it has to be named in an intersection type.
- **Jitter on the delay.** Every deferred job of one tenant is released by the
  same cap, so a fixed delay marches them back together and they are all
  deferred again. The delay is `base + random * base`.

A degraded count never defers, per §12's rule: the ledger reports `degraded`
when Redis did not answer, and a run delayed because a count could not be read
is a run delayed for no reason.

### Why the default cap is 25

Measured, not chosen. Over 180 days the busiest organisation held **21** runs at
once and the next held 12 (`w1s4.r*.csv`, Q3). A cap of 25 would have delayed
nobody. That is deliberate: the mechanism ships with its metric already flowing
and the number is tightened against evidence, exactly as the execution budget
did. A cap guessed low turns a large customer's throughput into a queue on the
day the flag is enabled.

### How to test the fairness, end to end

The unit tests cover the decision (`tenant-concurrency-cap.spec.ts`) and the
wiring (`apiV2Job.processor.spec.ts`). Neither proves *fairness*, which is a
property of two tenants competing. That needs the local stack:

1. **Reproduce the bug first.** Flag off. Pick a cap below what one org can
   produce — `TENANT_MAX_CONCURRENT_RUNS=2` — and submit ~20 runs from org A,
   each slow enough to overlap (a flow with a long model node, or a loop).
   Submit one run from org B a few seconds later. Record how long B waits. With
   no cap, B waits behind A's whole batch. **That wait is the bug**; a test that
   never saw it cannot claim to have fixed it.
2. **Enable and repeat.** Turn `tenant_concurrency_cap` on, same load. B should
   start within roughly one deferral window rather than behind A's batch.
3. **Assert nothing was refused.** Every run of A must still complete. Count
   `flux.tenancy.deferred` in the logs — deferrals are expected and are the
   mechanism working; **errors are not**. Any failed run of A is a bug in the
   cap, not a cap doing its job.
4. **Check the count self-heals.** Kill a replica mid-run and confirm the
   tenant's `concurrent` falls back on its own within
   `RUN_MAX_DURATION_MS` rather than staying permanently inflated. This is what
   the sorted set buys over a counter, and it is the failure that would
   otherwise deadlock a tenant until someone flushed Redis by hand.
5. **Watch for thrash.** With the cap saturated, confirm a deferred job is not
   re-deferred indefinitely — the jitter should let jobs through in turn. A job
   deferred more than a handful of times means the delay is too short relative
   to run length, not that the cap is wrong.

Run 1 and 2 against `docker/devdb/docker-compose.devdb.yaml`, never against dev or staging:
the load is the point of the test and it would be indistinguishable from an
incident.

## 17. The prefetch path charged without saying which run it was charging

`dispatchLegacyHandler` in `back/src/app-api/flux/flux.service.ts` took an
`execId` and threw it away — the parameter was literally destructured as
`execId: _execId`. Nothing else on that path establishes `chargeContext`, so
every charge a legacy node made through `ProductService.updateTokens` arrived
with `execId = null`.

That is not a cosmetic gap. With a null `execId`:

- `chainRootRegistry.resolve` is never called, so the charge belongs to no
  chain and the spend ceiling of §11 cannot see it;
- `chainRootId` is left null on `token_transaction`, so the row cannot be
  grouped back onto its run afterwards;
- `shouldAccountChainSpend` refuses the charge, so the ledger total a run is
  measured against silently excludes everything the prefetch path spent.

In other words the ceiling was blind on exactly the path built to run nodes
ahead of time. Two callers share the method — the prefetch scheduler and
`runLegacyAndPersist` (execute-single-node) — and both were blind.

The fix establishes the context around the handler, in
`back/src/app-api/flux/legacy-dispatch-charge-context.ts`:

```ts
export function withRunChargeContext<T>(
  execId: string | null | undefined,
  run: () => Promise<T>,
): Promise<T> {
  if (!execId) return run();
  return chargeContext.run({ execId }, run);
}
```

Three decisions are load-bearing.

**`run`, never `enterWith`.** The prefetch scheduler dispatches sibling nodes
concurrently. `enterWith` mutates the caller's own context and leaves it
mutated, so the node that happened to start last would rewrite the execId the
caller and its other children then read. `run` scopes the store to one call and
hands the caller its context back untouched. This distinction is the one a
concurrency test does **not** catch: when a sibling resumes from an `await` it
restores the context snapshot taken when the continuation was scheduled, so
`enterWith` looks correct between siblings. The leak is only visible to the
*caller*, after the dispatch resolves, which is what
`legacy-dispatch-charge-context.spec.ts` asserts.

**No `nodeId`.** The idempotency guard at `product.service.ts:1056` fires only
when `execId` **and** `nodeId` are both set, and it drops the charge when a row
already exists for that pair. On this path the guard's meaning would be "one
charge per node per run" (see §14 on the two meanings of `execId`), and the
legacy dispatch covers thirteen node types, including `libraryNode` and
`nodesBox`, which stand in front of whole sub-graphs. Setting `nodeId` would
arm that guard for all of them. I looked and could **not** demonstrate a legacy
dispatch type that charges twice in one execution — `objectCaller` does not
charge at all, `libraryNode` enqueues a child job with its own `execId`, and
the provider branches inside `imageGeneratorNode` are alternatives rather than
a loop. So this is a conservative choice, not a proven bug avoided: S3 needs
`execId` alone, and arming a guard whose semantics are unverified across
thirteen node types is a billing change that belongs to B1, not here.

**Falsy `execId` leaves the caller's context alone.** Overwriting a context the
caller already established with `{ execId: undefined }` would blind a path that
was previously accounted — the opposite of the fix.

### What this is worth

The charges themselves were never lost; they always reached
`token_transaction`. What was lost was their *attribution*: which run, and
therefore which chain, had spent the money. The visible effect is that a flow
executed through the prefetch scheduler could run past the spend ceiling
without the ceiling ever counting it, because as far as the ledger was
concerned nothing had been spent.

### What running the procedure actually found — 2026-09-16

Run against a real Redis with `back/test/manual/s3-fairness-harness.ts`
(40 long runs from a hog tenant, 5 short runs from a quiet one, 8 slots,
cap 3). Step 1 of the procedure did its job: with the cap off the quiet tenant
waited **15.1 s** to start, which is the starvation this task exists to fix.
With the cap on it started in **0.2 s**.

But the harness also failed a check, and the failure was real.

**Admission was not atomic.** `enter` added the run to the sorted set and then
read the count, so every member of a simultaneous burst saw the whole burst.
`back/test/manual/s3-enter-race-probe.ts` measured it directly — cap 3, five
runs arriving together, 30 trials:

```
before:  bursts that admitted exactly the cap: 0/30
         bursts that admitted nobody:         30/30
```

Not one run of thirty bursts was admitted, where three should have been. A
tenant **inside** its allowance had its entire burst deferred. That is the
false-refusal failure mode the plan requires to be zero, wearing a delay
instead of an error, and no unit test could have caught it: the stub answered
one call at a time, so the window never opened.

The fix moves prune-count-decide-add into a single Lua script, which Redis runs
to completion before serving anything else. Same probe after:

```
after:   bursts that admitted exactly the cap: 30/30
         bursts that admitted nobody:          0/30
```

Two consequences worth keeping. The ledger now owns the decision, so
`shouldDeferForTenant` is gone — a run never takes a slot it is about to wait
for, which makes the earlier "release the slot before deferring" step
unnecessary rather than merely correct. And the victim tenant's wait stopped
depending on `TENANT_DEFER_DELAY_MS`: it was previously waiting a whole delay
period because none of its own runs were admitted either.

**One thing reported rather than fixed.** How often a queued job is re-checked
scales with the defer delay against run length and backlog depth — measured at
86 re-checks on one job with a 300 ms delay and 14 with 2000 ms, for a 40-job
backlog of 3 s runs. Every job still completed and none was refused, so this is
a tuning parameter, not a defect; the harness reports the number instead of
asserting a bound invented by the test. If `flux.tenancy.deferred` shows heavy
churn once the flag is on, the answer is a longer delay or a backoff carried on
the job, and that is a change worth making against evidence rather than ahead
of it.

## 18. What the spend ceiling survives under real concurrency

`back/test/manual/s3-spend-ceiling-probe.ts`, against a real Redis. The tenant
cap's defect (§16) was a concurrency defect that no stub could show, so the
same question was put to the ceiling:

| property | result |
|---|---|
| 200 simultaneous charges sum exactly | 7500 of 7500, no lost update |
| 50 simultaneous breaches claim the stop | exactly **1** claim |
| the claim carries ceiling and spend | `{"ceiling":1000,"spend":1100}` |
| a charge landing after the stop still settles | 5000 → 5500 |
| both keys expire | 86 400 s each |
| a degraded read never stops a run | no breach |

The second row is the one that matters and it was proved by breaking it:
dropping `'NX'` from `claimStop` turns 1 claim into **40**, which is 40 cancel
requests for one run. `INCRBYFLOAT` and `SET NX` are atomic server-side, which
is why this ledger held where the tenant ledger's read-then-write did not.

### What is still not tested

Test Case 1 of the task — a real looping flow, cost measured with the check
off, then the abort observed with spend and limit in the error — has **not**
been run. It needs the full local stack with provider credentials and spends
real money on real model calls. Everything between the charge arriving and the
run being asked to stop is covered above and by the unit tests; what is not
covered is a provider call actually producing the charge that starts it. That
gap should be closed in QA against dev, not by asserting it here.

## 19. Validated against production after S1 shipped — 2026-09-16

Production moved 24 commits past this branch's base, and **S1 (`868m0vfyz`)
is now part of it** — the commit this map reviewed as a branch tip,
`1f597809`, is in `origin/production`. The check was a real merge into a
throwaway worktree, not a reading of the diff: no conflicts, merged build
`exit 0` with zero error lines, and **160 tests green across 13 suites**, this
task's suites running beside S1's cascade specs and the execution-budget ones.

Three files were touched by both sides (`.env.example`,
`app-api.module.ts`, `flux.service.ts`) and git resolved all three.

### The two §15 predictions, now checkable against shipped code

**`isRootRun` is live and the interaction is still benign.** `flux.service.ts`
gates on `const isRootRun = !parentCancelRunKey;` before
`checkSubFlowCascade`, so the `triggerOnly` children that §13 gave a
`parentCancelRunKey` now skip the cascade analysis. That loses no coverage:
`sub-flow-cascade-analyzer.ts` walks `subFlowTargets` and has no notion of
`executionMode` anywhere in it, so a `triggerOnly` target is already a node in
the graph the root analysed. Re-verified against the shipped file, not the
branch this map first read.

**The front's ceiling allow-list is short, but the gap is latent.**
`front` on `production` lists four ceilings — `node_iterations`,
`array_items`, `run_executions`, `chain_executions`. `cascade_size` and
`cascade_cycle` are absent, so `parseBudgetLimitEvent` would drop them
silently. They never arrive that way: the cascade gate sits inside `apiV2` and
returns **before** the run loop, while the only two `emitBudgetLimit` call
sites are inside it. A cascade breach reaches the user as an HTTP 422 carrying
`buildCascadeBreachPayload`, which the socket path never sees. So this is a
latent gap to close when a front counterpart lands, not a live defect.

`chain_spend` is the opposite case and does need its front entry, which this
branch adds: the spend ceiling stops a run from inside the loop and is
announced through `emitBudgetLimit`.

### One thing to know about production's migrations

`production` carries two migrations sharing the timestamp `1789000000000`
(`AddFlowEmailTriggerToken` and `AddMaxCascadeSizeToFlow`). This task's
migrations are all later and unaffected, but the collision is worth knowing —
production already shipped a fix of exactly this shape ("move the proposal
migration off a colliding timestamp"), so ordering between those two is
decided by glob order rather than by the timestamp.
