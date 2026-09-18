# Delivery plan

How the 32 tasks in this epic become shipped changes, in an order where **each wave is useful on
its own and revertible on its own**.

Two documents govern what is in here and neither is repeated:
[`PLAN.md`](./PLAN.md) holds the conventions and the definition of done;
[`ARCHITECTURE-REVIEW.md`](./ARCHITECTURE-REVIEW.md) holds the reasoning behind the order.

## The rule that sets the order

Today the system is protected by three accidents: one sequential engine loop, a small per-replica
run concurrency (`AGENT_CONCURRENCY`, default five — it was one run per replica until 2026-08-21),
and a blocking wait on every Temporal node. None of them was designed as a per-tenant safeguard,
and all three disappear in this epic.

**Every wave that removes a throttle must come after the wave that adds the matching ceiling.**
That single rule produces the sequence below. It is also the answer to "can we start with the fun
part" — no, because the fun part is the throttle removal.

---

## Wave 0 — Close what is already open

**Ships without touching the migration at all.** Everything here is a live gap today; none of it
depends on the worker.

| Task | What it closes |
|---|---|
| `S4` | A loop the node's own data can make unbounded |
| `S5` | A claim-check endpoint that authorises nothing beyond a key prefix |
| `C3` | Defects in the code that later waves are about to duplicate |
| `S1` | Sub-flow recursion with no depth limit and no cycle detection |
| `S7` parts 1 and 3 | An unauthenticated webhook route that runs **any** flow and charges its owner; an email trigger that trusts `From` |

**`S7` part 1 is the single most urgent item in this epic.** It is not a scaling concern and not a
migration concern — a flow id is currently enough to execute someone's private flow at their
expense. It ships on its own, ahead of everything, with a deprecation window for existing callers.

**Why S1 is here rather than next to B6:** the recursion is exploitable now, and the measurement it
requires — the real nesting depth of stored flows — takes calendar time to run and to resolve with
flow owners. Starting it late makes it the thing that blocks B6.

**Exit gate.** Each has a negative control that failed first. S1 and S4 have their measurement
against stored data with zero false refusals. Nothing in this wave changes execution behaviour for
a working flow.

**Rollback.** Per task, independently. Nothing here is coupled.

**Observable after.** A recursive flow fails with a clear message instead of degrading a process.
A runaway loop stops. A leaked internal key can no longer read every tenant's output.

---

## Wave 1 — Make the fleet able to grow

**Nothing in this wave migrates a node.** It removes the reasons the fleet cannot scale.

| Task | What it unlocks |
|---|---|
| `S2` | Adding worker replicas at all — today connections scale linearly into a shared ceiling |
| `S3` | Parallel dispatch later, by bounding spend and bounding one tenant's share. **Stays here although its tenancy premise changed** (see the task, corrected 2026-09-02): the exposure today is fairness, bounded by five runs per replica, and nothing in Wave 0 depends on it. Its first deliverable is the per-tenant concurrency metric |
| `E3` | Notifications that survive more than one backend replica |
| `S7` part 2 | Rate limiting on every run-creating entry point — admission, not just execution |
| `S8` | One fire per cron and per schedule regardless of replica count; Redis sized and its dedup keys protected |

**Exit gate.** The capacity arithmetic from S2 is written down with real numbers and states how
many worker replicas the current database supports. Two backend replicas run one schedule once and
one cron tick once, each proven by a test that counted two before the fix. Rate limits ran in
report-only mode against real traffic with no legitimate caller refused. S3's ceiling was replayed against the stored
run history with zero runs falsely aborted. E3 delivers an event across replicas in a test that
failed before the change.

**Rollback.** S2 is configuration. S3 is a flag defaulting to unlimited. E3 is the riskiest —
transport change — so it ships behind a flag with the old path intact for one cycle.

**Observable after.** A number: how many workers this database supports. That number is the input
to every capacity decision after this point.

---

## Wave 2 — Make coverage measurable

| Task | Why here |
|---|---|
| `A1` | Every later task writes to this registry; four uncoordinated lists is a tax each of them would otherwise pay |
| `D2` | An agent following today's guidance produces wrong work **now** — this is not documentation polish |
| `A2` | Six node types and two providers are finished and not in production. Cheapest coverage in the epic |
| `A3` | Two worker modules nothing routes to — decide whether to finish or delete |

**Exit gate.** A1's behaviour-neutrality table covers every registered type and proves nothing
changed. A2's six satisfy the seven-point definition of done. A3 leaves no module with
`workerModule: true` and `dispatch: 'inline'`.

**Rollback.** A1 is behaviour-neutral by construction, so reverting is safe at any point. A2 is a
promotion — revert by not promoting.

**Observable after.** One place answers "does the worker run this?", and it is true.

---

## Wave 3 — Cover the remaining nodes

| Task | Notes |
|---|---|
| `A4` | `reportBuilder` — the canary. Cheapest node, re-validates the template |
| `A5` | `imageGenerator`, over a provider layer built to be shared. `imageReaderNode` left the task — deprecated (D24) |
| `A6` + `S6` | The front-driven types: eight after D24, six after D3 (two discontinued). **S6's egress decision ships with them, not after** — its width is the implementer's call (D25) |
| `A8` | `varInputNode`'s extraction and OCR off the request path |
| `A9` | Emails and callbacks as retried activities — today a customer's endpoint being down for thirty seconds loses the notification |
| `C1` | Per node, as each lands — not a sweep at the end |
| `D1` | Continuous; each node's page is part of its own done |

**Expect a latency regression in this wave and say so.** Every migrated node is a blocking round
trip until Wave 5 (review §4.5). Measure it per task and state the number in the PR. This is the
cost being paid up front for the parallelism that Wave 5 buys back — a team surprised by it in
production will ask to roll the migration back.

**Exit gate.** Every executable node type is in the worker or explicitly out of scope. No mixed
flows remain among the types Wave 5 will parallelise. S6 ran in report-only mode for a full cycle
before enforcing.

**Rollback.** Per node, per flag. This is why the flags exist.

**Observable after.** Flows that silently produced stale output in headless runs — the eight
front-driven types — start producing fresh output. That is a **behaviour change for customers**,
D3 was answered on 2026-09-02 (`PLAN.md` §7), so this wave is no longer gated on it.

---

## Wave 4 — Move the engine, still sequential

| Task | Notes |
|---|---|
| `B1` | Execution identity — before anything makes it the transport |
| `B2` | The code-sharing decision, then the scheduler and substitution extraction |
| `B3` | The consumer resolves its own input, building on the prefetch executor |
| `B4` + `E1` | The graph workflow — **shipped sequential** — with observability moving in the same wave |
| `E2` | Cancellation aligned with Temporal's native mechanism |

**The whole point of this wave is that nothing gets faster.** A flow runs in the same order, node
for node, with the same latency. What changes is *where* the loop lives. Shipping the relocation
and the parallelism together makes a rollback unable to tell you which one broke the run.

**Exit gate.** Order equivalence over a corpus of stored flows: same nodes, same order, node for
node. B4's history measurement done, with `continueAsNew` proven past its boundary. E1's redaction
test green. Cancellation is Temporal-native for a single-level run — the child-workflow case is
proven in Wave 5, when B6 creates the first child workflow.

**Rollback.** One flag selects engine-in-backend versus engine-in-workflow, per flow. The backend
loop stays in place through this whole wave and is only deleted in Wave 6.

**Observable after.** Nothing, to a user. That is the success criterion.

---

## Wave 5 — Turn on parallelism

| Task | Notes |
|---|---|
| `B5` | Batch dispatch, gated per flow on full migrated coverage |
| `A7` | `nodesBox`, with its ordering contract — needs B1 and the parallel model settled |
| `B6` | Control flow and sub-flows as workflow constructs and child workflows; ships after B5 (D17), and proves that cancelling a parent stops its children — E2's clause, moved here because no child workflow exists before B6 |
| `B7` | CSV batches as durable workflows — the largest multiplier of every ceiling. The batch screen is out (2026-09-02) |

**Preconditions, all from earlier waves:** S1 (recursion ceiling — B6 turns sub-flows into child
workflows), S2 (connections), S3 (spend and tenancy), E3 (notifications across replicas), plus
B5's own per-provider budget.

**Rollout is by cohort, not by switch.** Internal flows, then a small customer cohort, then
general — with the eligibility gate meaning most flows simply stay sequential until their nodes are
covered.

**Exit gate.** The corruption test passes: an ineligible flow forced through the parallel path
demonstrably loses a write, and the gate refuses it. Determinism holds across repeated runs.
Latency is measured against the pre-epic baseline — this is where Wave 3's regression is paid back,
and the claim is settled with numbers or not at all.

**Rollback.** Per-flow eligibility, then a global off switch. Both leave Wave 4's sequential
workflow running.

**Observable after.** Wide flows finish in the time of their slowest path rather than the sum of
their nodes.

---

## Wave 6 — Remove the old road

| Task | Notes |
|---|---|
| `C1` | Finish it: the cross-node writes go once their last inline caller does |
| `C2` | The legacy endpoint, the prefetch decision, and every flag this epic created |

**Exit gate.** `addConnectToNodes` has no callers on the run path. No migration flag from this epic
remains. `flux.service.ts` is materially smaller and the reduction is stated.

**Observable after.** One implementation of each node, one dispatch registry, one engine.

---

## Critical path, and what runs beside it

**Critical path** — the longest chain, and the one to staff first:

```
S2 → A1 → A2 → A3 → A4 → A5 · A6 · A8 → B1 → B2 → B3 → B4+E1 → B5 → B6
```

**Runs in parallel with it, no contention:** S7 parts 1 and 3, S4, S5, C3 (Wave 0); S1 and S3 (Wave 1,
but both must land before their gates — S1 before B6, S3 before B5 and B7); S8, S7 part 2 and E3
(before B5); A9 (any time after A1); D1 and D2 (continuous); C1 (attached to each node's task).

**The two hard sequencing rules,** stated once so no wave plan can accidentally violate them:
1. Wave 5 comes after S2 **and** S3. Removing back-pressure without the ceilings is worse than
   keeping the back-pressure.
2. B4 ships sequential. Wave 4 and Wave 5 are two deploys, always.

---

## Where the review's actions landed

Every action from `ARCHITECTURE-REVIEW.md` §7 has a home. Nothing was dropped.

| # | Review action | Task | Wave |
|---|---|---|---|
| 1 | Sub-flow depth ceiling and cycle detection | `S1` | 0 |
| 2 | System-level loop ceiling | `S4` | 0 |
| 3 | Per-run cost ceiling; per-tenant concurrency cap | `S3` | 1 |
| 4 | Worker pool `max`; connection sizing; proxy decision | `S2` | 1 |
| 5 | Bind claim-check keys to their run | `S5` | 0 |
| 6 | SSRF policy decided with the move | `S6` (+ `A6`, `A8`) | 3 |
| 7 | `continueAsNew` and by-reference workflow state | `B4`, amended | 4 |
| 8 | Per-provider, per-tenant concurrency budget | `B5`, amended | 5 |
| 9 | Commit to event-sourced run logs | `E1`, amended | 4 |
| 10 | Specify the parallel-execution UX | `B5`, amended | 5 |
| 11 | Authenticate the webhook route; fix the `public` predicate | `S7` part 1 | 0 |
| 12 | Rate-limit every run-creating entry point | `S7` part 2 | 1 |
| 13 | Leader election for the thirteen crons | `S8` | 1 |
| 14 | Durable, single-fire user schedules | `S8` | 1 |
| 15 | Redis eviction policy and post-parallelism sizing | `S8` | 1 |
| 16 | Verify the email sender instead of trusting `From` | `S7` part 3 | 0 |
| 17 | Decide and cap what a public flow's email trigger may do | `S7` part 3 | 0 |
| 18 | Message-id dedup independent of the POP3 maildrop lock | `S8` part 4 | 1 |
| 19 | Outbound delivery as retried activities | `A9` | 3 |
| 20 | CSV batches as durable workflows | `B7` | 5 |
| 21 | Temporal Schedules for user schedules, locks for framework crons | `S8` part 2 | 1 |

**Re-validated against production on 2026-08-24.** `mcpNode` shipped completely, so the promotion
queue drops from seven node types to six and from three providers to two. Every safety finding is
unchanged. No task added, removed or re-sequenced — see analysis §12.

**Re-validated against production on 2026-09-02** (`back@23370f82`, `worker@2fdeb97`,
`front@ed012bc1`). The task count is **32**, not the 28 the first line of this file said until
today: `S7` and `S8` were added from review §9–§10, `A9` and `B7` from review §11 — the table above
already showed all four; the intro was never updated. What changed in this pass, and where:

- `S3`'s premise: the processor has run **five** queued runs per replica since 2026-08-21
  (PR #1902), not one. The task stays in Wave 1 and starts with the per-tenant metric.
- `A2` is written in production-only terms. `A5` is `imageGenerator` alone and `A6` covers eight
  types: `imageReaderNode` is deprecated (D24). `S6`'s width is the implementer's call (D25).
  `B7`'s batch screen is out.
- `E2` proves single-level cancellation; the child-workflow proof is now `B6`'s Done-when clause.
- `D2`'s measurement is `A1`'s (Wave 2); `B3` answers, `C2` executes. Thirteen live crons, not
  fourteen. Every code reference names a file and a symbol, never a line.
- The decisions-by-wave table below is recomputed from PLAN §7's Blocks column and gated by
  `_generator/reconcile_facts.py`; D18, D20, D22 and D23 moved rows. No task changed wave.

The spec, its content modules and the published pages were regenerated together in this pass.

## Decisions that gate a wave

A decision is listed under the **earliest wave that contains a task it blocks** — PLAN §7's Blocks
column mapped through the wave tables above; `_generator/reconcile_facts.py` recomputes it, so this
table cannot drift from PLAN §7 silently. Most decisions are settled and live inside their task. The
one that still needs an answer from outside engineering is D15 (a measurement); D3 (product) was
answered on 2026-09-02. D2 is
spread across three tasks — A1 measures in Wave 2, B3 answers in Wave 4, C2 executes in Wave 6 —
and is listed under Wave 4 because that is where the answer is needed.

**What each decision asks, what it settled and why is in [`PLAN.md`](./PLAN.md) §7 — that table is
the single source.** This one only says which wave each decision gates, because the same answer
written in two places diverges the first time somebody edits one of them. That already happened in
this spec once.

| Wave | Decisions that gate it |
|---|---|
| Wave 0 | D6, D10, D13, D14, D15, D20, D23 |
| Wave 1 | D7, D8, D9, D11, D12, D18, D19, D22 |
| Wave 2 | D4, D5 |
| Wave 3 | D3, D24, D25 |
| Wave 4 | D1, D2, D16 |
| Wave 5 | D17, D21 |
| Wave 6 | — |
