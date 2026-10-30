# Delivery plan

How the tasks in this epic become shipped changes, in an order where **each wave is useful on
its own and revertible on its own**. **34, as of 2026-09-21** — `TASK-A1B` split out of `A1` and
`TASK-A10` was added the same day; see the retrospective near the end of this file. `TASK-A1C`
(2026-09-22) and `TASK-A5B` (2026-09-25) were split out later, each from the task it complements.

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

**Post-release validation, S4.** The wave's exit gate is met before the flag is flipped, so S4
carries a checklist that only runs after the release: flag off proves the release is revertible by
the flag; flag on with the shipped defaults treats **any** `flux.budget.*` hit as a false refusal
until classified; and the prod re-measure that `D15` still owes replaces numbers taken from
dev+staging. Two standing re-checks travel with it — X's negative control becomes runnable if the
scheduler ever re-dispatches a condition node, and the array ceiling is the one that fires first.
See `TASK-S4-LOOP-CEILING.md` § Post-release validation. Per-company and per-agent ceilings, with
`agent > company > env` and a screen, are carried forward to follow-up `868m10e1z`.

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
| `A1` | Every later task writes to this registry; nine uncoordinated lists (corrected 2026-09-21 — four when this row was written) is a tax each of them would otherwise pay |
| `A1b` | **Added 2026-09-21.** `basedOnType`'s two live copies already disagree in five places; deciding which side is the truth needs a measurement against real data, which is not behaviour-neutral — so it is split from A1 rather than risking A1's neutrality guarantee |
| `D2` | An agent following today's guidance produces wrong work **now** — this is not documentation polish |
| `A2` | **Corrected 2026-09-21, again 2026-09-23:** the six node types have shipped to production (verify, not promote). `clickup`'s worker-routed half moved to `A10`; `quickbooks` is out entirely, tracked as an external dependency (PLAN §9). A2 is a per-§3.4-point record in which every point is proved or handed to its owner |
| `A3` | Two worker modules nothing routes to — decide whether to finish or delete |

**Exit gate.** A1's behaviour-neutrality table covers every type in the reconciled worker-enum /
MCP-metadata source and proves nothing changed; its `dispatchConflict` invariant — three named
`it.failing()` cases plus one plain `it()` for every other type, pinned 2026-09-21 so the suite stays
green on arrival instead of permanently red (see TASK-A1) — passes as designed. A1b's measurement against dev-only
stored flows is reported, and its dead-copy deletion (`flux/constants.ts`) is proven unreachable
before it is removed. **A2's six node types are already in production** (verify against PLAN §3.4,
don't promote); its exit condition is the per-point record, with points 3, 4 and 7 handed to
C3, C1 and D1 by name (corrected 2026-09-23 — `clickup`'s worker adapter, once this gate's
remaining condition, is A10's and gates Wave 3). A3 leaves no module with `workerModule: true` and
`dispatch: 'inline'`.

**Rollback.** A1 is behaviour-neutral by construction, so reverting is safe at any point. A1b is a
data migration plus a reconciliation, not behaviour-neutral, and is rolled back by not deleting the
dead copy until the decision is re-confirmed. A2 is a promotion — revert by not promoting.

**Observable after.** One place answers "does the worker run this?", and it is true.

---

## Wave 3 — Cover the remaining nodes

| Task | Notes |
|---|---|
| `A4` | `reportBuilder` — the canary. Cheapest node, re-validates the template |
| `A5` | `imageGenerator`, over a provider layer built to be shared. `imageReaderNode` left the task — deprecated (D24) |
| `A5b` | **Added 2026-09-25.** Image-generation capability made detectable and self-configuring: the catalog sync derives it, the picker, the worker (`toolChoice` included) and MCP read it, and listings show every model's capabilities and tools. After A5 and 868ky2g5f |
| `A6` + `S6` | The front-driven types: eight after D24, six after D3 (two discontinued). **S6's egress decision ships with them, not after** — its width is the implementer's call (D25) |
| `A8` | `varInputNode`'s extraction and OCR off the request path |
| `A9` | Emails and callbacks as retried activities — today a customer's endpoint being down for thirty seconds loses the notification |
| `A10` | **Added 2026-09-21.** `clickup` — the only executable integration provider still routed inline — gets its worker adapter to production and an `integrationProviders` entry. **Corrected 2026-09-28:** the worker half was built on `develop` (`b027e55`) and never promoted — A10 promotes it, flag = deploy order |
| `D1` | Continuous; each node's page is part of its own done |

**Removed from Wave 3 on 2026-10-02.** C1 had a Wave 3 row for its per-node half, but that half is a Done-when line of each A-track card, not a deliverable of its own, so the row counted as an unstarted item in a wave whose nodes were already deleting their twins. Verified on `back@origin/production` `bc727827`: A4's `reportBuilderNode()` and dispatch case are gone, A5's `imageGenerator` dispatch case is gone (its dead method body stays, by precedent); A9's inline delivery block goes with its production deploy. C1 is tracked once, in Wave 6 ([868m0vm8g](https://app.clickup.com/t/9011479430/868m0vm8g)).

**Expect a latency regression in this wave and say so.** Every migrated node is a blocking round
trip until Wave 5 (review §4.5). Measure it per task and state the number in the PR. This is the
cost being paid up front for the parallelism that Wave 5 buys back — a team surprised by it in
production will ask to roll the migration back.

**Exit gate, restated 2026-09-21.** Every executable node type **and every executable integration
provider** is in the worker or explicitly out of scope. No mixed flows remain among the types Wave 5
will parallelise. S6 ran in report-only mode for a full cycle before enforcing.

<details><summary>2026-08-21 wording, before the restatement</summary>

> Every executable node type is in the worker or explicitly out of scope. No mixed flows remain
> among the types Wave 5 will parallelise. S6 ran in report-only mode for a full cycle before
> enforcing.

</details>

**Why the restatement.** Stated in terms of node *types* alone, the old wording was satisfiable
while `clickup` still ran inline, because the node type `thirdPartyIntegration` is migrated — the
gate never looked at what decides the actual path. `isWorkerRoutedIntegration`
(`back/src/shared/integration/integration-executable-node.ts`) resolves the node's **provider** and
tests it against `MIGRATED_INTEGRATION_PROVIDERS`; a `thirdPartyIntegration` node configured with
`provider: 'clickup'` fails that test and takes the inline path regardless of the node type's own
status. A type-only gate can read "passed" with a provider still inline — which is exactly what
happened, unnoticed, from `clickup`'s 2026-08-27 ship date until A1's 2026-09-21 re-validation found
it. `A10` is what the restated gate now requires closed.

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
| `B3` | The consumer resolves its own placeholders by reference; the prefetch executor is a stopgap (D2) |
| `B3b` | The worker builds each node's `*Data` from its upstreams' rows — the edge projection leaves the back (split out of B3, 2026-10-09) |
| `B4` + `E1` | The graph workflow — **shipped sequential** — with observability moving in the same wave |
| `E2` | Cancellation aligned with Temporal's native mechanism — **moved to Wave 5 on 2026-10-26** |
| `E5` | Redis stops being allowed to evict the dedup keys, and the post-B5 sizing answer is recorded — split out of S8 part 3 on 2026-09-18, and placed here because it has to precede B5 |

**The whole point of this wave is that nothing gets faster.** A flow runs in the same order, node
for node, with the same latency. What changes is *where* the loop lives. Shipping the relocation
and the parallelism together makes a rollback unable to tell you which one broke the run.

**Exit gate.** Order equivalence over a corpus of stored flows: same nodes, same order, node for
node. B4's history measurement done, with `continueAsNew` proven past its boundary. E1's redaction
test green. Cancellation is Temporal-native for a single-level run — the child-workflow case is
proven in Wave 5, when B6 creates the first child workflow.

**Rollback.** One flag selects engine-in-backend versus engine-in-workflow. **Corrected
2026-10-23:** the flag is global by design, not per flow; per-flow selection is the eligibility gate.
The backend loop stays in place through this whole wave and is only deleted in Wave 6.

**The flag stays off in production in this wave (2026-10-23).** It is off in dev too (corrected
2026-10-26: `engine_in_workflow` has been `false` since its row was created on 2026-10-23). Turning it on in
production moves to Wave 5, after A11 and A13, and only after the worker that registers
`processFlow` is deployed: the back starts that workflow as soon as the flag is on, and a worker
without it leaves every eligible run waiting.

**Observable after.** Nothing, to a user. That is the success criterion.

**The wave closes on 2026-10-26 (2026-10-23).** It closes with the production deploy of B4, with
its flag off, and E1. That is 17 working days from 2026-10-02, inside the 14–28 day estimate. The
timeline measures wave 5 from 2026-10-27. Two items of the exit gate do not hold the close and carry
into wave 5: B4's history measurement with `continueAsNew` proven past its boundary (B4-a, needed
before the flag goes on in production), and E2, which is paused.

**Closed on 2026-10-26.** Production runs back `5e92e879` and worker `abf3b09d` (ECS task
definitions `api-task-definition-prod:828` and `worker-task-definition-prod:80`), so B4 and E1 are
shipped. E2 moved to Wave 5: the production code has the Temporal-native half (the back calls
`handle.cancel()`, the worker honours cancellation), but the per-node poller and
`nodeCancelContext` are still live behind `node_cancel_in_flight`, and a cancel that arrives as a
thrown error charges no tokens (D22). Users can cancel runs today through the existing path.

---

## Wave 5 — Turn on parallelism

| Task | Notes |
|---|---|
| `E2` | **Moved from Wave 4 on 2026-10-26; rescoped the same day.** Record the tokens of a cancel that arrives as a thrown error (D22), and measure the cancel latency. The per-node poller moved to C1 and D23 to B6. No dependency; blocks nothing |
| `A11` | **Added 2026-10-23.** An execution class for every node type; every hand-kept type list derived; a drift spec. First, because the B4 gate and B5's measurement read it |
| `A13` | **Added 2026-10-23.** The Data Output as the workflow's sink — a workflow run has no reply without it |
| — | **Turn the B4 flag on in production**, after A11, A13 and the worker deploy that registers `processFlow` |
| `A7` | `nodesBox` with an execution record, a session lock and object ordering in the scheduler; **widened 2026-10-23** to make every `worker` type reachable from both back loops |
| `A14` | **Added 2026-10-23, rescoped the same day.** Small Memory and chat flows on the workflow engine without moving a node: memory content derived from stored executions, persistence kept in the back |
| `A6b` | **Added 2026-10-23.** Migrate or retire `webTrends` |
| `S6b` | **Added 2026-10-26.** Close the SSRF gaps the S6-a check found: authenticate and allowlist `/proxy`, one egress guard that pins the checked address, one deny-list, `POST /api_call` guarded |
| `B5` | Batch dispatch, gated per flow on full migrated coverage — after every A-track task above |
| `B6` | Control flow and sub-flows as workflow constructs and child workflows; ships after B5 (D17), and proves that cancelling a parent stops its children — E2's clause, moved here because no child workflow exists before B6. It also owns D23 — propagating a cancel to `fluxBox`, `libraryNode` and `arrayNode` — since 2026-10-26 |
| `B7` | CSV batches as durable workflows — the largest multiplier of every ceiling. The batch screen is out (2026-09-02) |
| `E4` | User schedules move onto Temporal Schedules — **blocked until B4 ships**, because a Temporal Schedule can only trigger a workflow and no whole-flow workflow exists before B4. S8 shipped the duplication fix on Bull repeatables (D26); this adds pause, backfill, last-run state and durability independent of Redis |

**Order inside the wave (2026-10-23).** A11 → A13 → B4 flag on in production → A7 → A14 → B5 →
B6 and B7. A6b runs any time after A11, before B5 measures eligibility. S6b has no dependency and runs
first, starting with `/proxy` (added 2026-10-26). E2 depends on nothing and blocks nothing (rescoped 2026-10-26). A7 can be built in parallel
with A11 and A13, because it works with the flag off and on.

**Open before this wave starts (2026-10-23).**

1. Team alignment on this restructure, then merge the spec PR and run `SYNC-PLAN-2026-10-23.md`.
2. B4 worker (`feat/wave-4-b4`) reaches worker `main`; it is on `develop` only. A7's worker PR
   waits for it (A7-D4).
3. `sqlQuerier`: back `feat/sql-node` (`196df420`) gets a PR to `main`; it has none and is 63
   commits behind. **Assumption (2026-10-23):** it ships in the Monday 2026-10-26 production deploy,
   together with E1 and B4 (`wave4-prod-checks-runbook.md`). Wave 5 planning treats it as done
   from that date.
4. Production counts for A7 (`a7-q1` to `a7-q3`).
5. ~~A7-D9 (protection on the internal callback) confirmed.~~ Settled 2026-10-23 (`TASK-A7`).
6. ClickUp: ~~cards for A11, A13, A14 and A6b~~ created 2026-10-26 with estimates (A11 24 h, A13 32 h,
   A14 32 h, A6b 24 h), plus S6b. A7's description rewritten and re-estimated at 96 h on the
   same day.

**Preconditions, all from earlier waves:** S1 (recursion ceiling — B6 turns sub-flows into child
workflows), S2 (connections), S3 (spend and tenancy), E3 (notifications across replicas), plus
B5's own per-provider budget.

**A staged rollout, not a single switch.** Internal flows first, then a small group of customers,
then everyone — with the eligibility gate meaning most flows simply stay sequential until their nodes are
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
| `C2` | The legacy endpoint, the prefetch decision, every flag this epic created, and **the back's DAG loop itself** (named 2026-10-23) |

**This wave only removes (2026-10-23).** Every migration happens in Wave 5. Wave 6 deletes what the
evidence shows is no longer reached. **Entry gate and per-flag conditions:** C2 section 3 lists
every flag the epic created, the production check that allows its removal, and the code that goes
with it. A flag without a recorded check stays.

**Exit gate.** `addConnectToNodes` has no callers on the run path. No migration flag from this epic
remains. The back's run loop is deleted. The end-state test — "no executable node type runs in the
back" — passes as a plain test after living as an expected failure since A11. `flux.service.ts` is
materially smaller and the reduction is stated.

**Observable after.** One implementation of each node, one dispatch registry, one engine.

---

## Critical path, and what runs beside it

**Critical path** — the longest chain, and the one to staff first:

```
S2 → A1 → A2 → A3 → A4 → A5 · A6 · A8 → B1 → B2 → B3 → B3b → B4+E1 → B5 → B6
```

**Runs in parallel with it, no contention:** S7 parts 1 and 3, S4, S5, C3 (Wave 0); S1 and S3 (Wave 1,
but both must land before their gates — S1 before B6, S3 before B5 and B7); S8, S7 part 2 and E3
(before B5); A1b, A9 and A10 (any time after A1); D1 and D2 (continuous); C1's per-node half (a Done-when line of each
node's task — not a Wave 3 item since 2026-10-02).

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
| 13 | Leader election for the fourteen crons | `S8` | 1 |
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
- `D2`'s measurement is `A1`'s (Wave 2); `B3` answers, `C2` executes. **Fourteen live crons as of
  2026-09-18** — thirteen when this was written; `syncAiModelsFromGateway` landed since, and the
  fifteenth site stays commented out. Every code reference names a file and a symbol, never a line.
- The decisions-by-wave table below is recomputed from PLAN §7's Blocks column and gated by
  `_generator/reconcile_facts.py`; D18, D20, D22 and D23 moved rows. No task changed wave.

The spec, its content modules and the published pages were regenerated together in that pass.

**Re-validated against production on 2026-09-21** (`back@origin/production` `3804a524`,
`worker@origin/main` `3e4c93a`, `front@origin/production` `fdeddbbc`) — triggered by a re-check of
A1, then extended the same day to A5 and to `quickbooks`'s disposition, so this pass covers Wave 2's
tasks (A1, A1b, A2, A3), the tasks that cite their facts (C1, C2, D2), Wave 3's A5, and a new
external-dependency record (PLAN §9) — not the whole document. What changed, and where:

- **A1's scope grew, not just its facts, though less than the first correction pass claimed.** Nine
  dispatch lists, not four — the ninth, `dispatchLegacyHandler`'s switch, was missed by the first
  draft entirely. A1 also gained a `dispatchConflict` invariant (no type both `isTemporalNode` and
  `LEGACY_SINGLE_RUN_NODE_TYPES`), a bounded fix for `webCrawling`'s wrong refusal message, and the
  contract fixture is now specified to reuse `node-handle-registry.ts`'s shape rather than invent
  one. **`basedOnType` moved out entirely, into the new `A1b`, the same day.** The first correction
  pass called it "three divergent copies" needing "a per-field reconciliation" and "the largest
  scope increase" — a same-day field-by-field re-measurement found that overstated it: one of the
  three (`flux/constants.ts`) is unreferenced dead code, and the two live copies diverge in five
  lines out of roughly thirty shared types, not the sixty-six first reported. Correcting a
  correction, on the same day, is recorded here rather than silently overwritten. No task removed;
  one added (`A1b`). A1's own Done-when line grew from the dispatch-list work alone.
- **A1b is new.** It owns the measured `basedOnType` reconciliation — a decision (one map or two
  named projections) backed by a dev-only measurement of whether `mcpNode.inputMode` and
  `outputController.customFileName` are actually referenced, plus proof the dead copy is
  unreachable before deletion. It is not behaviour-neutral, which is why it is not inside A1.
- **A2's node-type half is done.** The six node types this task was written to promote are in
  production. A2's remaining scope is narrower and re-framed: `clickup`'s product feature shipped
  (868j988uj) but only on the inline OAuth path, so its worker adapter and
  `MIGRATED_INTEGRATION_PROVIDERS` entry are what is left; `quickbooks` has no code anywhere and
  moved out of A2 entirely, into a new PLAN §9 "External dependencies" section that tracks work this
  epic relies on but does not own — the same shape as `clickup`'s own product feature.
- **A3 is unchanged in substance** — `sqlQuerier` and `audioReaderNode` are still unrouted — only its
  citation of `isTemporalNode`'s count moved (fourteen, not seven).
- **C1's per-node procedure now has three more instances of the pattern it already handled**
  (`voiceBoxNode`, `webSearch`, `commandContentNode`), reached through the legacy-endpoint door
  rather than a second `flux.service.ts` copy. **C2 gains two dead branches** moved from A1
  (`legacy-node-dispatch.ts`'s unreachable `pullData`/`pushData` cases) and a corrected count of the
  worker-routed-but-legacy-accepted defect (four types, not one; `webCrawling` is a distinct
  wrong-message defect with its own fix).
- **D2's enum-size citation moved twice in six weeks** (ten → thirteen → 20), which the task file now
  states as the argument for the generated contract rather than a number to keep re-chasing.
- **D5 is settled by measurement**, not just named: `comment`, `label`, `group` and (newly found)
  `voiceNode` are removed from every list that trusts them; there is no fourth registration to find.
- **A5 shipped in substance, and stays open on two named clauses.** `imageGenerator` is dispatched
  and billing-verified in production, but the shared `ai-provider/image/` layer was never built
  (providers are node-local) and `imageGeneratorActivity`'s timeout is a self-declared, dated
  placeholder, not measured data. A5's provider-topology description was also wrong — six provider
  *systems* (`openai`/`gemini`/`fal`/`stabilityai`/`ideogram`/`opensources`), not six service-method
  *paths* — corrected in the task file. Its state moves from `planned` to `doing`, not `shipped`: a
  task shipped at less than 100% is information, not a status to hide (MAINTENANCE §2).
- **QuickBooks gets a destination, not a task.** It does not replace A5's slot or become a new epic
  task. A new PLAN §9 "External dependencies" records it the same way `clickup`'s own product
  feature already proved out: the epic owns a provider's worker-routed half once the provider
  exists, never the product work of building the integration itself.
- **A sixth pass, same day: `A10` is new, Wave 3's exit gate had a hole, and there is now a standing
  rule.** `clickup` is the only executable integration provider still routed inline — its worker
  adapter was never shipped (it was built on `develop`, found 2026-09-28 — see `TASK-A10`), only ever noticed via A1's re-validation of `isWorkerRoutedIntegration`
  — so it becomes `TASK-A10`, not a line item inside `A2` (A2's shape is "verify what's finished";
  nothing about `clickup`'s worker half is finished). Wave 3's exit gate is restated to cover
  executable integration providers, not just node types — the old, type-only wording was
  satisfiable with a provider still inline, which is exactly what went unnoticed for nearly a month.
  `PLAN.md` §3.6 records the standing rule this gap produced: a new integration provider ships
  worker-routed from the start, as part of its own definition of done, not as a later migration —
  cross-referenced from `A2`'s Out clause and from `PLAN.md` §9's QuickBooks entry, the named next
  case it exists to stop.
- No task added to Track A/B/C/E/S beyond `A1b` and `A10`; no wave changed but Wave 3's exit gate was
  restated (above). `back/src/app-mcp/node-types/node-type-metadata.ts`
  (50 entries) and `front/src/util/nodeTypes.tsx` (46 types) are recorded here as the two real
  node-type sources — there is no source with 48, which the earlier acceptance criterion assumed.

This pass did not regenerate the content modules or the published `timeline/` pages — it corrected
source documents only. Three hand-authored pages that are not generator output (`epic-handbook.html`,
`delivery-waves.html`, `complemento/fase-3.html`, plus `complemento/transversais.html` in the same-day
A1 pass) were fixed directly — **correcting this section's own earlier claim**, which named
`fase-2.html`: the "seven types plus nine providers" restatement that needed fixing was in
`fase-3.html`; `fase-2.html` carries no such claim. The `timeline/task-*.html` pages generated from
`_generator/w2_a1.py`, `w2_a2.py`, `w3_a5.py` and siblings were deliberately left stale rather than
hand-patched — see `MAINTENANCE.md` §1 on why a direct edit there is reverted by the next build —
and there is no generated page yet for `A1b` or `A10`.

## Decisions that gate a wave

A decision is listed under the **earliest wave that contains a task it blocks** — PLAN §7's Blocks
column mapped through the wave tables above; `_generator/reconcile_facts.py` recomputes it, so this
table cannot drift from PLAN §7 silently. Most decisions are settled and live inside their task.
None still needs an answer from outside engineering: D15 (a measurement) was answered on
2026-09-03, and D3 (product) on 2026-09-02. D2 is
spread across three tasks — A1 measures in Wave 2, B3 answers in Wave 4, C2 executes in Wave 6 —
and is listed under Wave 4 because that is where the answer is needed.

**What each decision asks, what it settled and why is in [`PLAN.md`](./PLAN.md) §7 — that table is
the single source.** This one only says which wave each decision gates, because the same answer
written in two places diverges the first time somebody edits one of them. That already happened in
this spec once.

| Wave | Decisions that gate it |
|---|---|
| Wave 0 | D6, D10, D13, D14, D15, D20, D23, D28 |
| Wave 1 | D7, D8, D9, D11, D12, D18, D19, D22, D26 |
| Wave 2 | D4, D5, D27 |
| Wave 3 | D3, D24, D25 |
| Wave 4 | D1, D2, D16 |
| Wave 5 | D17, D21 |
| Wave 6 | — |
