# EPIC — Run the whole flow in the worker

**Status:** proposed 2026-08-21; readiness review 2026-09-02. Analysis this plan is built on:
[`../worker-node-migration-analysis/README.md`](../worker-node-migration-analysis/README.md)
(§1–§12), plus the published walkthroughs of the execution pipeline and the migration briefing.

**Code references name files and symbols, never lines.** Every fact in this spec set was
re-verified on 2026-09-02 against `back@origin/production` `23370f82`,
`worker@origin/main` `2fdeb97` and `front@origin/production` `ed012bc1`. The first draft cited
line numbers read at `back@3be1ea8e` (2026-08-21); ten days and ~40 production commits later,
about sixty of seventy-five had moved while the facts they pointed at had not. A symbol survives
that; a line does not. Where a symbol does not exist — an inline branch, a literal such as
`responses.length === 10` — the spec names the enclosing method or the literal to grep for.

**A1's facts were re-verified again on 2026-09-21**, against `back@origin/production` `3804a524`,
`worker@origin/main` `3e4c93a` and `front@origin/production` `fdeddbbc` — this re-check covered only
the dispatch-registry facts (A1, A2, A3, C1, C2, D2, D5), not the whole document. It found the
"four dispatch lists" and "48 registered types" this plan states below had already drifted: there
are **nine** dispatch lists, not four; there is no source with 48 node types (46 in
`front/src/util/nodeTypes.tsx`, 50 in `back/src/app-mcp/node-types/node-type-metadata.ts`); and A2's
six node types have shipped to production. A same-day second pass also measured `basedOnType`,
found the first correction had overstated it, and split it into its own task, **TASK-A1B**, in
Wave 2 after A1: one of its three cited copies is dead code, and the two live copies diverge in five
lines out of roughly thirty shared types, not sixty-six — see TASK-A1B for the measurement. TASK-A1,
TASK-A1B, TASK-A2 and TASK-A3 carry the corrected facts and the evidence; this file's own
restatements are corrected in place below, dated, with the old claim kept rather than deleted.

**Do not restate the analysis here.** Where a task needs a fact — which gate routes a node type,
why `arrayNode` cannot be an activity, what the prefetch executor already does — it cites the
analysis section instead of re-deriving it. A second copy always drifts.

---

## 1. What this epic is for

Four goals, in the requester's words, with what each means in this codebase:

| # | Goal | Concretely |
|---|---|---|
| G1 | Run as many node types in the worker as possible | Started from **7 dispatched types + 9 integration providers** (2026-08-21 baseline) toward full coverage of every node type that has server-side execution (§9.4, §11.1). **Corrected 2026-09-21:** A2's six types have since shipped — `isTemporalNode` carries 14 today (`back@origin/production` `3804a524`, see TASK-A1) — so the starting count is history, not the current state; full coverage is still the goal |
| G2 | Run the flow itself through the worker, with the execution sequence owned there | Move the DAG scheduler and input resolution out of `FluxService.apiV2()`, replace the blocking per-node round trip with a workflow that dispatches ready nodes as a batch (§7, §9.2) |
| G3 | Reduce backend dependencies and clean up what was migrated | Delete the inline twins, stop cross-node writes, retire the legacy endpoint, collapse the dispatch lists into one (§9.2.3, §9.4) — **nine lists as of 2026-09-21, not the four read on 2026-08-21 (TASK-A1)** |
| G4 | Clear documentation for developers **and for AI** | A single authoritative node contract, generated where possible, plus Mintlify pages and updated agent guidance (the existing `node-worker-migration` skill is already stale) |

**The order matters and is not the order above.** G1 is mostly a prerequisite for G2, G3 is only
safe after both, and G4 runs alongside from the start. §5 sets the sequence.

**Read the scale review before planning any wave.**
[`ARCHITECTURE-REVIEW.md`](./ARCHITECTURE-REVIEW.md) is adversarial about this plan and found four
critical items that change its order. [`DELIVERY-PLAN.md`](./DELIVERY-PLAN.md) maps the tasks into
shippable waves.

## 2. Why now, in one paragraph

The persistence model already supports parallel siblings — one `node_executions` row per
`(execId, nodeId)`, and `persistNodeSuccess` only ever merges into rows the activity owns (§7.3).
The scheduler is already a pure module with no injection and no DB (§7.1). The parallel dispatch
loop was already written and commented out (`process-agent.workflow.ts`). A prefetch executor that
resolves each node's input by reference is already in production behind a flag (§9.2.1). What is
missing is **coverage** and the **discipline to land the graph move and the parallelism switch as
two separately revertible changes**.

## 3. Conventions — apply to every task; task specs do not restate them

### 3.1 Branching and delivery
- **One ClickUp card per task; one branch per card.** `feat/<clickup-id>` (or `fix/`), same name in
  every repo the task touches. No side branches for sub-changes — they become loose ends.
- **One PR per card by default.** A card may ship in more than one PR when each PR is independently
  deployable and the later ones land *dark* — code not yet reachable, or behind the flag §3.2 already
  requires. Three tasks are cut that way on purpose, and only these: `S7` (two cards — parts 1 and 3
  in Wave 0, part 2 in Wave 1), `A6` (one card, one PR per stage) and `C1` (one card for its
  once-only half; the per-node deletions are a Done-when line of each A-track card).
- **Base:** each repo's production branch — `back`/`front` → `production`, `worker` → `main`.
  Check `git log origin/<base>..<branch>` before opening the PR.
- **Worker reaches `main` only through a PR.** `dev`/`staging` get the branch by merge.
- Never commit to an env branch. Feature branch is always the source.

### 3.2 Every routing change ships behind a flag
No task flips execution paths and lands in one deploy. A task adds the new path **disabled**,
proves it, and flips it in a **separate** deploy. The flag defaults to today's behaviour. This is
what makes each task independently revertible, which §6 depends on.

### 3.3 Gates, per task, no exceptions
1. **A new test counts only after you have seen it fail.** Break the code — revert the fix, gut
   the handler — watch it go red, restore, and state in the PR which failure you observed. Do not
   stub the collaborator the defect lives in.
2. **Measure before refusing.** Any rule that rejects input is checked against real stored data
   first, classifying every refusal as correctly-refused or refused-although-it-works, and driving
   the second count to zero. Where knowledge is incomplete, report unverifiable rather than refuse.
3. **Scoped formatting.** `npx biome check --write <files>` — never `pnpm lint:fix`, which ignores
   its path arguments and reformats the whole repo.
4. **`validate-changes` skill** before the PR.
5. **`env-vars-sync` skill** if the task touches any env var, in either repo.
6. **`mcp-node-schema-sync` skill** if the task touches `node-type-metadata.ts`, a front node
   component, or a worker node module. Handle changes additionally require
   `pnpm generate:node-handle-registry` and a green `node-handle-registry.spec.ts`.

### 3.4 Definition of done for "node type X runs in the worker"
A node is **not** done when its activity exists. All seven must hold:
1. Worker module + `nodes.types.ts` enum entry + `temporal.module.ts` + `activities.service.ts` +
   `worker.service.ts` + `workflows/configs.ts` proxy + an entry in `UNIFORM_NODE_ACTIVITIES`
   (`workflows/node-activities.ts`), or an explicit `process-single-node.workflow.ts` case when the type
   has its own workflow logic (corrected 2026-10-15: six types have a case; the rest go through the map; clarified 2026-09-23, TASK-A2: both forms throw
   `Node type X not supported` when the entry is missing).
2. Registered in the **single dispatch registry** (Task A1) — not in one of the ad-hoc lists.
3. Reachable from **both** entry paths: a full flow run and a single-node run. The full-run loop
   (`apiV2`) has no generic dispatch, so the type needs its own `processNodeViaTemporal` branch in the
   main loop and in the `arrayNode` inner loop. On 2026-10-15 five worker types lacked it (see A6 and A8
   in `STATUS.md`).
4. The inline twin in `flux.service.ts` is deleted, or guarded so it cannot double-fire.
   **Decided 2026-09-23 — wording kept, not broadened.** The inline twins A1 found for
   `voiceBoxNode`, `webSearch` and `commandContentNode` live on `/process/single-node-legacy`, not
   in `flux.service.ts`. This point is deliberately not widened to "any inline path": TASK-C1 already
   owns those twins and their removal, and restating that scope here would give it a second home.
   A node that has such a twin records this point as C1's (see TASK-A2's per-point record).
5. Errors throw the right `NodeError` subclass (`UserConfigError` / `IntegrationError` /
   `ProviderError` / `TimeoutError` / `SystemError`).
6. A negative-control test per §3.3.1.
7. Documentation updated per Task D1 — the node's page and the contract table.

### 3.5 Backend has no CI test run
No workflow runs jest in `back`. A scoped local run is the only gate — prefer `it.skip` over an
early return so a skipped case is visible. Check `free -m` first and scope jest to the changed
files with `--maxWorkers=1`.

### 3.6 A new integration provider ships worker-routed from the start

**Added 2026-09-21.** A worker adapter and a `MIGRATED_INTEGRATION_PROVIDERS` entry are part of a
new integration provider's own definition of done — not a later migration task this epic picks up
after the fact.

**Why this is a rule and not a preference.** `clickup` shipped as a product feature in August 2026
(ClickUp task [868j988uj](https://app.clickup.com/t/868j988uj), back PR #1922, front PR #2134,
2026-08-27) while this epic was already running, and nothing connected the pipeline that built the
integration to the pipeline that routes it through the worker. The product half — OAuth connection,
front config, back execution adapter — shipped complete; the worker half was ported on `develop`
(2026-07-31) but never promoted with it (corrected 2026-09-28, see `TASK-A10`), and this
epic only found the gap on 2026-09-21, via A1's re-validation of `isWorkerRoutedIntegration`
(`back/src/shared/integration/integration-executable-node.ts`), a month later. That gap is now
`TASK-A10`. Without this rule, the next integration repeats it, and the epic keeps acquiring
migration work it should never have needed — QuickBooks (§9) is the named next case this rule is
meant to stop from arriving inline.

Cross-referenced from `TASK-A2`'s Out clause and from §9's QuickBooks entry, so both places that
name an integration's provider work point back here instead of restating it.

## 4. Task index

Each file below is a standalone spec, sized to be one ClickUp card. Most ship in one PR; §3.1 says
when a card may ship in more than one.

### Track S — safety ceilings (blocks everything else)

Added after the scale-readiness review ([`ARCHITECTURE-REVIEW.md`](./ARCHITECTURE-REVIEW.md)).
These are not migrations. They are the ceilings that today's accidental throttles — one sequential
process, five queued runs per replica (`AGENT_CONCURRENCY`; it was one until 2026-08-21), a blocking
wait — are silently providing. **Removing the
throttle before adding the ceilings replaces a slow system with an unstable one.**

| Task | Goal | Blocks |
|---|---|---|
| [`TASK-S1-SUBFLOW-CEILING.md`](./TASK-S1-SUBFLOW-CEILING.md) | Depth ceiling and cycle detection for sub-flows | B6 |
| [`TASK-S2-CONNECTION-CEILING.md`](./TASK-S2-CONNECTION-CEILING.md) | Size the worker's database connections against `max_connections` | B5, and adding worker replicas today |
| [`TASK-S3-SPEND-AND-TENANCY-CAPS.md`](./TASK-S3-SPEND-AND-TENANCY-CAPS.md) | Per-run cost ceiling at charge time; per-tenant concurrency cap | B5 |
| [`TASK-S4-LOOP-CEILING.md`](./TASK-S4-LOOP-CEILING.md) | A loop maximum the node cannot switch off | — |
| [`TASK-S5-CLAIM-CHECK-AUTHZ.md`](./TASK-S5-CLAIM-CHECK-AUTHZ.md) | Bind claim-check keys to their run | — |
| [`TASK-S6-SSRF-POLICY.md`](./TASK-S6-SSRF-POLICY.md) | Egress policy for user-controlled URLs, decided with the move | A6, A8 |
| [`TASK-S7-ENTRY-POINT-CONTROLS.md`](./TASK-S7-ENTRY-POINT-CONTROLS.md) | Authenticate the webhook route; rate-limit every run-creating entry point | B5 — but part 1 ships immediately |
| [`TASK-S8-SCHEDULER-AND-BUS.md`](./TASK-S8-SCHEDULER-AND-BUS.md) | One fire per schedule and per cron regardless of replica count; size Redis | running >1 backend replica, B5 |

### Track A — coverage (G1)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-A1-DISPATCH-REGISTRY.md`](./TASK-A1-DISPATCH-REGISTRY.md) | Collapse the uncoordinated "what can the worker run" lists into one derived source (nine, as of the 2026-09-21 re-validation — see the task file) | — |
| [`TASK-A1B-BASEDONTYPE-RECONCILIATION.md`](./TASK-A1B-BASEDONTYPE-RECONCILIATION.md) | Decide, on a measurement, whether `basedOnType`'s two live copies become one source or stay two named projections, and delete the third, dead copy | A1 |
| [`TASK-A2-PROMOTE-FINISHED-MODULES.md`](./TASK-A2-PROMOTE-FINISHED-MODULES.md) | Verify, point by point against §3.4, that the six node types already in production are wired end to end — each point proved or handed to its owner (corrected 2026-09-23; nothing ships from it) | A1 |
| [`TASK-A3-STRANDED-MODULES.md`](./TASK-A3-STRANDED-MODULES.md) | Route `sqlQuerier` and `audioReaderNode`, whose worker modules nothing reaches | A1 |
| [`TASK-A4-REPORT-BUILDER.md`](./TASK-A4-REPORT-BUILDER.md) | Migrate `reportBuilder` — the cheapest node, used to re-validate the template | A1 |
| [`TASK-A5-IMAGE-FAMILY.md`](./TASK-A5-IMAGE-FAMILY.md) | Migrate `imageGenerator` over a provider layer built to be shared (`imageReaderNode` is deprecated — D24) | A1, A4 |
| [`TASK-A5B-IMAGE-CAPABILITY-DETECTION.md`](./TASK-A5B-IMAGE-CAPABILITY-DETECTION.md) | Make image-generation capability detectable, self-configuring and listed — native and tool-based image models, `toolChoice` derived from the stored capability, capabilities and tools in app and MCP listings (added 2026-09-25, split from A5) | A5, 868ky2g5f |
| [`TASK-A6-FRONT-DRIVEN-NODES.md`](./TASK-A6-FRONT-DRIVEN-NODES.md) | Give the front-driven types server-side execution for the first time (nine in the census; `imageReaderNode` deprecated — D24; two discontinued — D3; six get execution) | A1 |
| [`TASK-A7-OBJECT-CALLER.md`](./TASK-A7-OBJECT-CALLER.md) | Migrate `nodesBox` with an execution record, a session lock and object ordering in the scheduler; **widened 2026-10-23** to make every `worker` type reachable from both back loops | A1, B1, B4 (code) |
| [`TASK-A8-INPUT-EXTRACTION.md`](./TASK-A8-INPUT-EXTRACTION.md) | Move `varInputNode`'s link extraction, upload and OCR off the request path | A1 |
| [`TASK-A9-OUTBOUND-DELIVERY.md`](./TASK-A9-OUTBOUND-DELIVERY.md) | Emails and HTTP callbacks as retried activities instead of fire-and-forget | A1 |
| [`TASK-A10-CLICKUP-WORKER-ROUTING.md`](./TASK-A10-CLICKUP-WORKER-ROUTING.md) | **Added 2026-09-21.** Promote `clickup`'s worker adapter (built on `develop`, never shipped) to production and add it to `integrationProviders` — the only executable integration provider still inline in production (§3.6, §9; corrected 2026-09-28) | A1 |
| [`TASK-A11-REGISTRY-EXECUTION-CLASS.md`](./TASK-A11-REGISTRY-EXECUTION-CLASS.md) | **Added 2026-10-23.** Give every canvas and MCP node type an execution class (`worker`, `back`, `none`), derive every hand-kept type list from it, and fail a drift spec on any unclassified type | A1 |
| [`TASK-A13-DATA-OUTPUT-SINK.md`](./TASK-A13-DATA-OUTPUT-SINK.md) | **Added 2026-10-23.** Build the Data Output value from upstream rows and make delivery the workflow's last step | A9, A11, B4 |
| [`TASK-A14-SMALL-MEMORY-AND-CHAT-STATE.md`](./TASK-A14-SMALL-MEMORY-AND-CHAT-STATE.md) | **Added 2026-10-23, rescoped the same day.** Run Small Memory and chat flows on the workflow engine without moving a node: history in the run seed, memory content derived from stored executions, persistence kept in the back | B3b.1, B4, A7 (read rule) |
| [`TASK-A6B-WEB-TRENDS.md`](./TASK-A6B-WEB-TRENDS.md) | **Added 2026-10-23.** Migrate or retire `webTrends`, which A6 shipped without | A1, A11 |

### Track B — the flow itself (G2)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-B1-EXECUTION-IDENTITY.md`](./TASK-B1-EXECUTION-IDENTITY.md) | Make the reference between nodes identify one **execution**, not one node in a run | — |
| [`TASK-B2-CODE-SHARING.md`](./TASK-B2-CODE-SHARING.md) | Decide shared package vs copy-port, then extract the scheduler and the substitution service | — |
| [`TASK-B3-WORKER-INPUT-RESOLUTION.md`](./TASK-B3-WORKER-INPUT-RESOLUTION.md) | Let the consumer resolve its own placeholders by reference; D2 answered — the prefetch executor is a stopgap | B1, B2 |
| [`TASK-B3B-EDGE-PROJECTION.md`](./TASK-B3B-EDGE-PROJECTION.md) | Build each node's `*Data` from its upstreams' rows in the worker, instead of the back's in-memory edge projection (split out of B3, 2026-10-09) | B2, B3 |
| [`TASK-B4-GRAPH-WORKFLOW.md`](./TASK-B4-GRAPH-WORKFLOW.md) | Move the DAG loop into a Temporal workflow — **sequential first**, no parallelism yet | B2, B3, B3b |
| [`TASK-B5-PARALLEL-DISPATCH.md`](./TASK-B5-PARALLEL-DISPATCH.md) | Turn on batch dispatch, gated per flow on full coverage | A-track complete (including A7, A11, A13, A14, A6b), B4, S2, S3, E3 |
| [`TASK-B6-CONTROL-FLOW.md`](./TASK-B6-CONTROL-FLOW.md) | `conditionNode`, `arrayNode` as workflow control flow; `fluxBox`, `libraryNode` as child workflows | B4, S1; ships after B5 (D17) |
| [`TASK-B7-BATCH-WORKFLOW.md`](./TASK-B7-BATCH-WORKFLOW.md) | CSV batches as durable workflows instead of a detached loop in the API process | B4, S3 |

### Track C — hygiene (G3)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-C1-RETIRE-INLINE-PATHS.md`](./TASK-C1-RETIRE-INLINE-PATHS.md) | Delete inline twins and stop the cross-node writes that make mixed mode unsafe | A-track per node |
| [`TASK-C2-RETIRE-LEGACY-SURFACES.md`](./TASK-C2-RETIRE-LEGACY-SURFACES.md) | Retire `/process/single-node-legacy`, and decide the prefetch executor's fate | C1, B4 |
| [`TASK-C3-PRE-PORT-DEFECTS.md`](./TASK-C3-PRE-PORT-DEFECTS.md) | Fix the known defects in the code about to be duplicated | — |

### Track E — cross-cutting subsystems (G2, G3)

These are not nodes, and the node-by-node census could not surface them. Each one **breaks when
the loop leaves the backend process**, and none belongs to any node's task.

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-E1-RUN-OBSERVABILITY.md`](./TASK-E1-RUN-OBSERVABILITY.md) | Keep the nested timeline, per-node billing and secret redaction working without a shared process | B2; lands **with** B4 |
| [`TASK-E2-CANCELLATION.md`](./TASK-E2-CANCELLATION.md) | Align cancellation with Temporal's native mechanism instead of porting the poller | — (was B4 until 2026-10-26) |
| [`TASK-E3-DISTRIBUTED-NOTIFICATIONS.md`](./TASK-E3-DISTRIBUTED-NOTIFICATIONS.md) | One publish path for run events, working across replicas | before B5 |
| [`TASK-E4-TEMPORAL-SCHEDULES.md`](./TASK-E4-TEMPORAL-SCHEDULES.md) | Move user schedules onto Temporal Schedules, for pause, backfill and durability independent of Redis | **B4** — blocked until it ships |
| [`TASK-E5-REDIS-POLICY-AND-SIZING.md`](./TASK-E5-REDIS-POLICY-AND-SIZING.md) | Stop Redis being allowed to evict the dedup keys, and record the post-B5 sizing answer | before B5 |

### Track D — documentation (G4)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-D1-DEVELOPER-DOCS.md`](./TASK-D1-DEVELOPER-DOCS.md) | Mintlify pages: the node lifecycle, how to add a node, the callback and error reference | runs alongside |
| [`TASK-D2-MACHINE-CONTRACT.md`](./TASK-D2-MACHINE-CONTRACT.md) | One generated, test-enforced contract an agent can read; refresh the stale skill and CLAUDE.md | A1 |

## 5. Sequence

```
S7 parts 1 + 3 (first of all)  ·  S4 · S5 · C3 (standalone, any time)
S2 (before ANY worker scaling)    S6 (decided inside A6/A8; width per D25)
S8 · S7 part 2 · E3 (before B5, and before a second backend replica)
S1 ──────────────────────────────────────────────── blocks B6
S3 ──────────────────────────────────────────────── blocks B5, B7

A1 ──┬── A2 ── A3 ── A4 ── A5 ──┬── A6 ──┬──────────────┐
     │                          └── A8 ──┘              │
     ├── A1b (any time after A1)                        │
     ├── A5b (after A5 and 868ky2g5f)                   │
     ├── A9 (any time after A1)                         │
     ├── A10 (any time after A1)                        │
     └── D2 ── D1 (continuous)                          │
                                                        │
B1 ── B2 ── B3 ── B3b ── B4 ───── E1 (with B4) ──┬── A7 ─┬── B5 ──┬── B6 (after B5, D17)
                                                 │       │        └── B7 (also needs S3)
                                                 └── C1 ─┴── C2

Wave 5 additions (2026-10-23):
A1 ── A11 ──┬── A13 (also A9, B4) ──┐
            ├── A6b                  ├── B4 flag on in production ── B5
            └── A7 ── A14 ───────────┘

E2 (moved 2026-10-26; no dependency, blocks nothing — the poller moved to C1, D23 to B6)
```

**Added 2026-10-23.** The B4 flag is global by design, and turning it on in production waits for
A11 and A13: without A11 the gate refuses almost every real flow, and without A13 a workflow run has
no reply. A7 and A14 complete coverage before B5 measures eligibility.

Read as seven rules:
1. **A1 first, always.** Every later task adds a node type to a registry; if the registry is still
   nine uncoordinated lists (§4 above, corrected 2026-09-21 — it read four when this rule was
   written), every task pays that tax and one of them will get it wrong.
2. **The A track and the B track run in parallel** up to B5. They only converge when parallelism
   is switched on, because that is the first moment coverage actually matters.
3. **B4 ships sequential.** Moving the graph and enabling parallelism must be two deploys, or a
   rollback cannot tell which change broke the run.
4. **Track S is not a phase, it is a precondition set.** S2 blocks adding worker replicas at all,
   S3 and S2 block parallel dispatch, S1 blocks child workflows, and S6 is decided inside A6/A8
   rather than after them. Only S4 and S5 are free-floating.
5. **C3, E3, S7 and S8 come early and stand alone.** C3 fixes defects in code that B2 is about to
   duplicate — after duplication each fix costs twice. E3's replica bug is already live and does
   not need the migration to bite; it only gets worse when parallelism multiplies the event rate.
   S7's parts 1 and 3 are the most urgent item in the epic and ship first of all; S8 is what makes
   a second backend replica safe, and both S8 and S7 part 2 land before B5.
6. **E1 ships with B4, not after.** The moment the loop leaves the process, the run timeline, the
   billing attribution and the secret redaction all lose their host. A B4 that ships without E1
   ships a run nobody can debug.
7. **C1 follows each node, not the whole track.** Delete a node's inline twin as part of proving
   that node, while the behaviour is fresh — not in a cleanup sweep months later.

## 6. Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Double execution.** A node routed to the worker whose inline twin still fires — a duplicated Stripe charge, a duplicated Slack message. | critical | §3.2 flag + atomic inline guard; C1 deletes the twin as part of the same task. Push-type activities retry once unless idempotent. |
| R2 | **Lost update in mixed mode.** A back-resident node writing into a target's row while a worker sibling merges the same row (§7.4b). | critical | B5 is gated per flow on full migrated coverage. Never enable parallelism for a flow containing an unmigrated executable type. |
| R3 | **Loop identity.** `(execId, nodeId)` names a node in a run, not one execution; a loop produces multiple rows and `fetchNodeRow` takes `rows[0]` with no `ORDER BY` (§8.4). | high | B1 lands before B3 makes that pair the transport. |
| R4 | **Latency regression.** Every migrated node today is a blocking round trip (§9.2.2), so the A track alone makes flows slower. | high | Accept and measure. State it in each A-task PR. B4/B5 is what pays it back — do not let the A track ship without the B track funded. |
| R5 | **Ordering loss for `nodesBox`.** The engine serialises object access through one in-memory array today; parallel activities do not. | high | A7 ships an advisory lock (settled 2026-10-23) and object-access edges in the scheduler, and is gated behind B1. Note: the lost update already exists across runs of one flow today, not only across parallel branches. |
| R6 | **Drift between the repos.** Two pure modules copied instead of shared (§7.6). | medium | B2 decides explicitly and records the decision; if copy-port wins, a `PORTED_FROM.md` with the source SHA and a drift test, as the integration migration did. |
| R7 | **The stale skill teaches the wrong thing.** `.claude/skills/node-worker-migration/SKILL.md` still describes a 10-type enum and knows nothing of the gates or prefetch. | medium | D2, early — an agent following it today produces wrong work. |
| R16 | **Unauthenticated run creation.** `/flux/api-v2-webhook` is `@Public()` and its `where` matches any flow, public or private, so a flow id is enough to execute it and charge its owner. No rate limiting exists anywhere. | critical, **live** | S7 part 1, immediately; S7 part 2 before B5. |
| R17 | **Scheduled work multiplies with replicas.** Fourteen crons with no leader election, and user schedules held in an in-process registry, so each replica fires its own copy. | high | S8, before a second backend replica. |
| R12 | **Unbounded sub-flow recursion.** Flow Caller re-enters the whole orchestrator with no depth limit and no cycle detection; B6 would turn that into durable child workflows across the fleet. | critical | S1, before B6. |
| R13 | **Connection exhaustion.** The worker pool sets no `max`, so connections scale linearly with replicas against a `max_connections` shared with the API. | critical | S2, before any worker scaling. |
| R14 | **Unbounded spend.** No per-run budget ceiling; credit checking is a boolean gate and charges are recorded after the fact. | high | S3, at charge time. |
| R15 | **Workflow history exhaustion.** One workflow per run, no `continueAsNew`, state passed by value — terminated by the platform on the largest runs. | high | B4, amended. |
| R9 | **Observability silently degrades.** The run timeline, per-node billing attribution and `redactSecrets` all live in the backend process and have no owner in a worker-orchestrated run (§11.3). | high | E1, shipped with B4. Redaction gets its own test — leaking a credential into `space_run_logs` is a security event, not a bug. |
| R10 | **Billing breaks under parallelism.** A node's spend is computed by subtracting an accumulator before and after; two siblings both move it. | high | E1 converges on dedup by primary key in `token_transactions` before B5. |
| R11 | **Notifications do not cross replicas.** `chatbotSocketByRun` is a process-local `Map`, so a run registered on one replica cannot be notified from another. Already latent. | medium | E3, before B5. |
| R8 | **Front-driven nodes change behaviour.** Giving them engine dispatch means flows that silently produced stale output start producing fresh output. | medium | A6 treats this as a product change, not a refactor: decision D3 below must be answered first. |

## 7. Open decisions — needed before the tasks they block

| # | Decision | Blocks | Notes |
|---|---|---|---|
| D1 | Shared package between `back` and `worker`, or copy-port with a drift test? | B2, and therefore B3/B4 | **Answered 2026-10-02: copy-port with a drift test.** The repos are separate submodules with no shared build graph, and there is no registry or package plumbing to build on — both Dockerfiles build from their own repo — so a package needs new infra before it ships anything. Back is the source: `pnpm sync:ported-engine` copies a closed manifest byte-for-byte into `worker/src/ported/back/`, and `ported-engine-drift.spec.ts` fails on any divergence or on an import that leaves the manifest; it was seen red on a `classifyEdge` mutation. It runs locally, since neither repo runs tests in CI (§3.5). The shared package was the earlier recommendation and stays on B2's page with its reasons. Details: `TASK-B2-CODE-SHARING.md`. |
| D2 | Is the prefetch executor the destination for worker-side input resolution, or a stopgap to retire? | B3, C2 | **Answered 2026-10-09: a stopgap.** 78 of 15,984 production flows are eligible (A1), and `FLUX_EXEC_MEMORY_MODE_PROD` was `prefetch` for about 73 minutes on 2026-08-20 and `legacy` ever since (SSM parameter history), so it has carried no traffic to measure. It also resolves in the back and dispatches inline, so it was never a consumer-side resolver. B3 moves placeholder resolution to the worker on B2's ported substitution service; C2 retires the executor. See `TASK-B3-WORKER-INPUT-RESOLUTION.md`. |
| D3 | The front-driven types (eight, after D24) do not run in headless flows today. Intended, or a silent defect for customers with one in a scheduled flow? | A6 | Independent of the worker. Answer it on its own before A6 turns it into a behaviour change. **Answered by the requester, 2026-09-02.** `documentSummarizer` and `commandMusicNode` are discontinued and leave A6; `webAmazon` and `secApiNode` are broken today, so giving them execution includes making them work, or dropping them — A6 decides per type and records it; `fileSave` is under review and stays in scope until that review says otherwise. The six that remain run headless: that is the product answer, and A6 is no longer blocked on this row. |
| D4 | Are `sqlQuerier` and `audioReaderNode` unreachable on purpose — a migration paused mid-way — or by oversight? | A3 | Changes whether A3 is "finish it" or "delete it". |
| D15 | What are X, Y and the chain total? | S4 | **Answered 2026-09-03 by measurement, shipped 2026-09-10** (back #1947, front #2155): X = 150 iterations per node (1.5x the UI's own maximum of 100), 12000 array items (1.4x the largest stored 8555), Y = 50000 node executions per run and a chain total of 200000, all behind the `execution_budget` flag. The production re-measure of Y on 2026-09-23 changed no ceiling. See `TASK-S4` ("Decision, 2026-09-03"). |
| D13 | Does a sub-flow share the parent's execution identity, get a disconnected one, or a chained one? | S1, B6, S3 | **Settled: chained.** Own run identity with a `parentRunId`. Depth, cycle, cancellation and the spend ceiling all read the chain — see `TASK-S1`. |
| D14 | Is calling a flow already on the chain refused outright, or merely depth-limited? | S1 | **Settled: refused outright.** A flow on the chain is awaiting a return; restarting it from the top has no coherent semantics. Applies to the whole chain, not only the direct parent. |
| D5 | What are `comment`, `label`, `group`, and (added 2026-09-21) `voiceNode`? They are trusted by a live whitelist — the first three by the prefetch whitelist, `voiceNode` by `LEGACY_SINGLE_RUN_NODE_TYPES` and `legacy-node-dispatch.ts` — but none is a registered node type in `front/src/util/nodeTypes.tsx` (46 types) or `back/src/app-mcp/node-types/node-type-metadata.ts` (50 entries). | A1 | **Settled for three of the four, 2026-09-22, and not the way this row first said.** The 2026-09-21 verdict read "remove all four" and claimed measurement it did not have. The measurement was then actually run: removing `comment`/`label`/`group` from the prefetch whitelist would be a **false refusal** — `prefetch-flow-executor.ts` already skips them via `NON_EXECUTABLE_NODE_TYPES`, so whitelisting them is what stops a canvas decoration from costing a flow its prefetch eligibility. They keep a `phantom`-marked registry entry and stay prefetch-safe; see **What D5 actually returned** in TASK-A1. `voiceNode` is a different surface (a live endpoint's accept list), was never measured, and is now **A1c**. The original question named three; re-validation against `back@origin/production` `3804a524` found `voiceNode` is the same defect — trusted by a dispatch list, registered nowhere. The registry cannot be authoritative while a live list trusts types nobody can name; "no evidence of reachability" was assumed, not measured, and measuring it inverted the answer for three of the four. |
| D6 | What is the sub-flow depth ceiling? | S1, B6 | **Superseded by what shipped (in production since 2026-09-16):** the ceiling is the root flow's `maxCascadeSize`, a per-flow value, not a fixed 3 in an env var. The pre-flight gate refuses a deeper cascade, and any cycle, with HTTP 422 before enqueueing. The first proposal was 3, env-configurable. |
| D7 | Behaviour when a run hits its cost ceiling | S3 | **The in-flight node finishes; the run then stops only if what remains would spend.** A typed error, never silent degradation. Amended by D20. |
| D8 | What is the worker pool `max`? | S2 | **Activity concurrency plus two** — the headroom is the health check and anything that opens a connection outside an activity. Setting it higher cannot help: the worker cannot use connections it has no activities to run. PgBouncer in transaction mode is recommended, and `pg_advisory_xact_lock` survives it where a session-level lock would not. |
| D9 | Per-tenant concurrency when the cap is reached | S3 | **Queue the excess, do not reject.** The caller is already entitled to the work, so a capacity limit should become latency rather than an error. Deliberately unlike D11. |
| D10 | What should `public: true` permit on the webhook route? | S7 part 1 | **Answered by S7 parts 1 and 3, now in production: `public: true` permits nothing on a trigger.** The webhook route is retired with `410 Gone` for every flow, so no predicate is left to state, and the email trigger needs the per-flow address token whether the flow is public or not. "Public" means readable, not "anyone may spend the owner's tokens"; `flow.public` no longer changes the auth path (`TASK-S7-ENTRY-POINT-CONTROLS-DESIGN`). |
| D11 | Behaviour when a rate limit is hit | S7 part 2 | **Reject with `429` and `Retry-After`.** Deliberately unlike D9: admission is the one place where rejecting is right, because queueing an unbounded inbound flood only moves it. |
| D12 | Cron single-fire mechanism | S8 | **Advisory lock per job name**, so nothing needs to know the replica count. A dedicated scheduler replica was considered and rejected: it makes one replica special, a deploy that loses it loses every cron silently, and a rolling deploy runs two of them anyway. |
| D16 | Does the workflow order nodes by the DAG's ready set, or by a recorded sequence? | B4, B3 | **Settled: the DAG decides.** The workflow dispatches whatever has no unmet dependency; ordering is a property of the graph, not a stored list. This is what `buildSchedulerState` already computes — import the rule, do not restate it. **Edge order is not removed:** it may stay as presentation, so a user can see what ran and in what sequence, but it never dictates execution order. Do not delete it as dead code. |
| D17 | Is a sub-flow executed as a Temporal child workflow, and does that change Wave 5's order? | B6 | **Settled: the child workflow is the mechanism, and Wave 5's order is unchanged.** `B5` still ships before `B6`; this confirms `B6`'s design rather than resequencing it. The chain (`parentRunId`, depth, visited set) must still live in the run context rather than a closure, or it does not survive the move — that is a property of `B6`, not of the order. |
| D21 | If the execution queue ever has to choose what runs next, what wins? | B5, B6, B7 | **Settled, and conditional — and as of 2026-08-31 the condition does not hold.** Nothing orders work today: `nextReady()` is `state.ready.shift()`, plain FIFO (`flux.service`'s `scheduler.ts`), everything runs on one unprioritised task queue (the worker's `worker.service.ts`, the back's `temporal.controller.ts`), and `priority` appears nowhere in `back/src/jobs`, `back/src/temporal` or `worker/src`. Work simply starts as capacity frees up. **If a priority list is ever introduced**, prefer the items that are already children of a running workflow: finishing the children is what finishes the flow, so work that *completes* something beats work that *starts* something, and deeper first follows the same logic. **Do not build the mechanism to satisfy this decision** — check first whether the deployed Temporal server exposes queue priority at all, which cannot be read from this repo. Starvation is then a real but unquantified risk, since it depends on replica count, concurrent runs and executions per run; it needs a floor only once the priority exists. |
| D18 | Is `/flux/batch-process` retired with the other legacy surfaces, or kept? | C2, B7, S7 part 2 | **Settled: the route is kept and its body moves into `B7`'s durable workflow.** The endpoint stays as the entry point; what runs behind it stops being a detached loop. `C2` retires none of the five batch endpoints — create, status, listing, stop and download — and the rate limit covers the creating one permanently rather than for a deprecation window. A batch screen was going to be added here; **it is not built in this epic** (2026-09-02). The endpoints stay anyway — they are the batch's only surface — and honouring stop through cancellation is `B7`'s, screen or no screen. |
| D19 | What pays for a node whose provider consumes tokens, and what happens when that runs out mid-generation? | S3, E2, B5 | **Settled: `fluxCred` — the platform's own token credit, which already exists — is what the node spends.** When it is exhausted **during** a generation the node is allowed to finish, and the run then aborts if any work remains, because there is no credit left to continue with. This is `D20`'s rule applied to credit exhaustion rather than to a configured ceiling, and it carries the same consequence: the platform accepts going negative by at most one node — or, under `B5`'s parallel dispatch, by as many nodes as are in flight. Size that headroom rather than assuming it is one. **Amended 2026-10-08 (868meyyw8):** the balance does not go negative. The trial balance keeps its floor of 0; the node that crosses 0 finishes and its full usage is written to the ledger, and the next paid node is refused (B1 Addendum A, A3). |
| D22 | How is provider usage recorded when a generation is cancelled or aborted? | E2, S3 | **Settled, and it depends on what the provider returns.** We ask the provider to cancel. If it reports the tokens spent up to that point, record the charge **normally** — exactly as a generation that completed, because the work was really done and really cost. If it reports nothing, record what is available and mark the entry as cancelled or aborted by the user, so the gap is legible rather than silent. **Do not record zero for a cancelled generation that consumed tokens:** that is the case that makes the ledger disagree with the provider's invoice. |
| D23 | Does a node that runs a sub-flow also get to finish when a ceiling stops the run? | S1, S3, S4, B6, B5 | **Settled: no — it is cancelled.** `D20` lets an in-flight node finish because a generation is short, already paid for, and yields a result. A `fluxBox`, `libraryNode` or `arrayNode` is not that: its execution is an open-ended amount of further work, which is exactly the spending being refused. So a container node is cancelled and the cancellation propagates down the chain — native for Temporal child workflows, and what `S1`'s `parentRunId` chain exists to carry. **For `arrayNode`:** the element already generating finishes under `D20`; the remaining elements never start. **`nodesBox` is not a container and is not cancelled** — checked against `back@origin/production` on 2026-09-01: it dispatches to `objectCaller` (`flux.service.ts`), whose 137-line body contains no `apiV2`, no `startWorkflow` and no node execution of any kind — it reads and writes an object's session state. The file's only two `apiV2` calls are `flowCallerNode` and `addConnectToNodes`. Cancelling it prevents no spend and leaves a half-written object, so under `D20` it finishes. Its real hazard is concurrent writes once `B5` parallelises, which is `A7`'s ordering contract, not cancellation. |
| D20 | When a ceiling is reached, what stops? | S3, S4, S1, B5 | **Settled: a ceiling stops future spending, not work in progress — and it stops only the part of the run that would spend.** The in-flight node finishes and produces its result; what is being refused is the *continuation of the flow*, not a generation that has already been paid for. If the remaining work consumes credit, the run stops there with a terminal state naming which ceiling; if it does not consume credit, it runs to the end. **Do not build a mechanism to interrupt a running node** — if one is not already in the code, this decision does not ask for it. **Exception, D23:** a node whose execution *is* a sub-flow is cancelled rather than allowed to finish. Amends D7, which said abort. **The same rule applies to every ceiling in this epic**, not only the spend one. **Where this is checked: before the run, not per node during it.** `S1` already runs a pre-flight gate between building the DAG and starting to spend, and `S4` already validates the graph there; extend that gate to credit rather than tagging node types at dispatch time. Be honest about its limit — a pre-flight check answers *can this flow spend*, not *will it*, because the branch taken depends on data that does not exist until the run happens. That is the same argument `S4` makes for keeping a runtime budget, and it applies here unchanged. **Amended 2026-10-08 (868meyyw8):** for credit, the pre-flight check is kept and a second check runs **before each paid node**: it reads the current balance, so it also catches a balance emptied mid-run or by another run of the same account. Free nodes are never checked; the in-flight node still finishes. Spec: B1 Addendum A, A3. **Consequence for `B5`:** N nodes are in flight, so the overshoot is up to N — size the headroom rather than assuming one. |
| D26 | What mechanism makes a user schedule fire exactly once? | S8, E4 | **Settled 2026-09-18: Bull repeatable jobs now, Temporal Schedules after `B4`.** Temporal is the right destination and was the wrong thing to build during `S8`: a Temporal Schedule can only trigger a workflow, and the worker has none that runs a whole flow — that is `B4`. Shipping it in `S8` would have meant inventing a bridge workflow plus an internal endpoint purely to be deleted when `B4` lands. Bull 4.16.5 is already a dependency and `ApiV2Queue` is already in production, so the schedule state moves out of the per-replica in-process `SchedulerRegistry` and into Redis, which Bull already manages, and the queue becomes the execution owner **structurally** — there is no callback left to forget to stop awaiting. **Measured, not read from documentation:** three simulated replicas registering the same repeatable produced one repeatable key and one execution per tick, against three per tick for the shape it replaces. What it does not buy — pause, backfill, last-run state, and durability that does not depend on Redis — is `E4`, blocked on `B4`. The rejected option, an advisory lock around the in-process cron, is left on the record: it stops the duplication but leaves the schedule in memory, so a fire with no replica up is still lost in silence. |
| D27 | Do the two live `basedOnType` copies (`node-reference-substitution.service.ts`, `folw/contants.ts`) become one source, stay two named projections, or something else — once the three genuine divergences are resolved? | A1b, B3 | **Settled 2026-09-22: one source (`NODE_REFERENCEABLE_FIELDS` in `shared/node-fields/node-referenceable-fields.ts`), by union.** Re-measured fresh against `origin/production` `5333b4d3` (newer than the task's `3804a524` baseline): 26 vs 29 types, 24 byte-identical, 3 divergent — the task's numbers still held. `mcpNode`'s `inputMode`/`toolArguments` are not a conflict to pick a winner on: both are real, live fields (`inputMode` from `front/src/util/dataStoredToType.ts:73`, `toolArguments` from `folw/contants.ts`'s own `allNodesTargetBasedOnType` and from `node-type-metadata.ts:2095`) that each copy happened to have alone — union keeps both. `outputController.customFileName` is populated on 15 real dev nodes (1 with `customFileNameData` linked); dropping it is exactly the silent data loss the task calls out, so it stays. `fluxBox`/`reportBuilder`/`thirdPartyIntegration` were folw-only with no counterpart to disagree with, so union is a no-op decision for them, not a pick. **Why union and not two projections:** the two copies already agree on 24/26 types — they are the same map, drifted, not two answers to different questions. `THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS` is kept as a named slice (`NODE_REFERENCEABLE_FIELDS.thirdPartyIntegration`) because it answers a genuinely different question (which fields may be filled from an upstream edge's `<field>Data`, not which a placeholder may read) and is pinned by two tests (`third-party-companions.spec.ts`'s negative-key check, `node-types.service.spec.ts`'s worker-parity check) — it is a projection of the base, not a second source. **Measured in dev (never staging/prod), 41,652 nodes, regex validated against real placeholders (`{{prompt.text}}` etc. matched) before trusting the zero:** placeholder references to `inputMode`, `toolArguments`, `customFileName` are all zero — the live placeholder traffic is 342/365 references to `.text` alone. Nothing currently depends on the divergence resolving one way over the other through the placeholder path; the union is validated by the data-passing path instead, where `customFileName` is live. The dead `nodeSchema` copy in `flux/constants.ts:392` was deleted: proven unreachable by three independent checks (unexported `const`, no other reference inside its own file, absent from that file's closing `export { ... }` block), corroborated by a `back`/`front`/`worker`/`mcp-server` grep sweep — and it was already one field stale (`commandTextNode` missing `modelSettings`), further evidence it was never touched. A fourth `basedOnType`-shaped map was found in `front/src/util/myFunctionsCoreDisplay.tsx:429` (also named `nodeSchema`, unrelated to the back copies) — out of this task's declared scope, left unresolved, flagged for a separate task. See `A1b`'s PR for the negative-control test run (each of the 3 unions + the anti-drift assertion broken and observed red, then restored) and the fresh cross-repo unreachability grep. |
| D24 | Does `imageReaderNode` stay in the migration? | A5, A6 | **Settled 2026-09-02: no — it is deprecated.** It leaves A5 (which becomes `imageGenerator` alone, over a provider layer still built to be shared) and A6 (eight types instead of nine). An OCR node is wanted in its place and is **not built in this epic**; it is specified when it is built, and whether Temporal or the provider layer offers a primitive for it is decided then, by its developer. **Superseded in practice by A8 (recorded 2026-10-15):** A8 moved OCR out of the Data Input into `imageReaderNode`, which now has a worker module (`worker/src/modules/nodes/image-reader`, in production since 2026-09-29) and a `flowDispatch: 'worker'` registry entry. It is no longer deprecated. Its full-run branch in `apiV2` ships with `868mhdzky` (see A8 in `STATUS.md`). |
| D25 | How wide is S6's egress policy on day one — the full resolved-address deny-list with redirect re-checks, or a narrower first cut? | S6, A6, A8 | **Delegated, 2026-09-02: the developer who picks up S6 decides, and records the choice in the task file before implementing.** The requester's preference, for the record: start with limits on URL *consumption* — what a node may fetch, how much, how often — and add the address blocklist as a second step. Whichever cut ships first, the three properties in S6's scope stay the target, and §3.3.2 applies to each step: measure against stored URLs before refusing. |
| D28 | Does the worker get direct S3 access, so large payloads stop travelling through the API? | S5 | **Settled 2026-09-09: no.** Review §2.4 argued it should, which would delete `/worker/store-payload` and `/worker/get-payload` and supersede `S5`. The back stays the sole holder of the S3 credential and both endpoints stay, because they are the only place where "this key belongs to this run" can be enforced at all. **Handing the worker the back's own credential is the same decision by another name** — it reduces the number of secrets, not the reach of each one, and it removes the enforcement point. §2.4's real argument is coupling and latency rather than security, and it is cheap today: 6 offloads in 3417 node executions on dev (measured 2026-09-09). Revisit it when `B5`'s fan-out makes the hop expensive, as its own task — by then `S5` will have paid for the authorisation. |

## 8. What this epic explicitly does not do

- It does not migrate the 11 inert node types (analysis §4.4, as revised by its §11.1), and does not
  invent run-time behaviour for the configuration-time types among them (`storedDataCaller`,
  `deepRefNode`, `nodesAdd`, `mediaBox`). **Corrected 2026-10-23:** `fluxObject` was listed here as
  configuration-time, but it writes during every run; A14 owns it. Not migrating an inert type
  still requires an execution class (`none`) in the registry — A11 — or B4's gate refuses its flows.
- It does not build a new OCR node. **Update 2026-10-15:** A8 made `imageReaderNode` that node (see D24). The original line read: the OCR node that replaces the deprecated `imageReaderNode` (D24). That node is
  specified when it is built.
- It does not build a batch-process screen. `B7` makes the batch durable behind the existing
  endpoints; the screen that reads them is a later product task.
- It does not decide whether `tableProcessor`'s transform should exist server-side — that is a
  product question with no engineering answer (§4.3).
- It does not change the front's builder UX beyond the Run button's dispatch path.
- It does not touch model access or file storage contracts. Those callbacks already exist and are
  the boundary this epic keeps. **Billing is not off limits, and the earlier wording here was too
  strong.** What the epic will not do is change what a model costs, or anything else priced
  directly. What it will do — D19, D20, D22, D23 — is add ceilings, cancellation and abort paths
  that stop a run, and those change what gets spent and what gets written to the ledger.

## 9. External dependencies — things the epic relies on but does not own

Added 2026-09-21, when `quickbooks`'s absence from A2 raised the question of where it belongs. This
section is for exactly that shape of item: work this epic's tasks are stated in terms of, but whose
existence is a product decision made outside this epic, on its own timeline.

| Dependency | What this epic needs from it | Status | Owner |
|---|---|---|---|
| A QuickBooks integration | If and when a `quickbooks` third-party integration is built as a product feature, its worker-routed half becomes an A10-shaped task: an adapter under `worker/src/modules/nodes/third-party-integration/adapters/` plus a `MIGRATED_INTEGRATION_PROVIDERS` entry (`back/src/shared/integration/integration-executable-node.ts`) — **but only if §3.6's rule is not followed for it.** If QuickBooks is built as a new integration under §3.6, the worker adapter ships as part of its own definition of done and this row never turns into a task at all. | **Not built.** No adapter, no OAuth connection, no front config, no provider entry, in any repo, as of `back@origin/production` `3804a524` / `front@origin/production` `fdeddbbc` / `worker@origin/main` `3e4c93a`. | Product — building the integration is the same shape of work as `clickup`'s (ClickUp task 868j988uj), which this epic did not own either. |

**Why this is not a task in the epic.** The epic's interest in a third-party integration begins once
the integration exists and needs worker routing — building the integration itself is product work,
the same as `clickup` was. `clickup` proves the pattern, and also the failure mode: its product
feature shipped under a ClickUp task outside this epic (868j988uj), but its worker-routed half was
never shipped alongside it (it sat on `develop`), so this epic had to acquire it after the fact as `TASK-A10`. **§3.6 is the
rule written to stop QuickBooks from repeating that** — see it for the reasoning. Until a QuickBooks
integration is built, this epic carries no QuickBooks work, and it does not take A5's or any other
task's slot; A5 stays scoped to `imageGenerator` (see TASK-A5).
