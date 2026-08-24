# EPIC — Run the whole flow in the worker

**Status:** proposed 2026-08-21. Analysis this plan is built on:
`.specs/features/worker-node-migration-analysis/README.md` in the `enhancedai-com/Workflow`
repository (§1–§12, read against `worker@origin/main` and `back@origin/production`), plus the
published walkthroughs of the execution pipeline and the migration briefing. That analysis is
**not** copied here — see `README.md` in this folder.

**Do not restate the analysis here.** Where a task needs a fact — which gate routes a node type,
why `arrayNode` cannot be an activity, what the prefetch executor already does — it cites the
analysis section instead of re-deriving it. A second copy always drifts.

---

## 1. What this epic is for

Four goals, in the requester's words, with what each means in this codebase:

| # | Goal | Concretely |
|---|---|---|
| G1 | Run as many node types in the worker as possible | Go from **7 dispatched types + 9 integration providers** to full coverage of every node type that has server-side execution (§9.4, §11.1) |
| G2 | Run the flow itself through the worker, with the execution sequence owned there | Move the DAG scheduler and input resolution out of `FluxService.apiV2()`, replace the blocking per-node round trip with a workflow that dispatches ready nodes as a batch (§7, §9.2) |
| G3 | Reduce backend dependencies and clean up what was migrated | Delete the inline twins, stop cross-node writes, retire the legacy endpoint, collapse the four dispatch lists into one (§9.2.3, §9.4) |
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
- **One branch, one PR, per task.** `feat/<clickup-id>` (or `fix/`), same name in every repo the
  task touches. No side branches for sub-changes — they become loose ends.
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
   `worker.service.ts` + `workflows/configs.ts` proxy + `process-single-node.workflow.ts` case.
2. Registered in the **single dispatch registry** (Task A1) — not in one of the ad-hoc lists.
3. Reachable from **both** entry paths: a full flow run and a single-node run.
4. The inline twin in `flux.service.ts` is deleted, or guarded so it cannot double-fire.
5. Errors throw the right `NodeError` subclass (`UserConfigError` / `IntegrationError` /
   `ProviderError` / `TimeoutError` / `SystemError`).
6. A negative-control test per §3.3.1.
7. Documentation updated per Task D1 — the node's page and the contract table.

### 3.5 Backend has no CI test run
No workflow runs jest in `back`. A scoped local run is the only gate — prefer `it.skip` over an
early return so a skipped case is visible. Check `free -m` first and scope jest to the changed
files with `--maxWorkers=1`.

## 4. Task index

Each file below is a standalone spec, sized to be one ClickUp task and one PR.

### Track S — safety ceilings (blocks everything else)

Added after the scale-readiness review ([`ARCHITECTURE-REVIEW.md`](./ARCHITECTURE-REVIEW.md)).
These are not migrations. They are the ceilings that today's accidental throttles — one sequential
process, one queued run per replica, a blocking wait — are silently providing. **Removing the
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
| [`TASK-A1-DISPATCH-REGISTRY.md`](./TASK-A1-DISPATCH-REGISTRY.md) | Collapse the four uncoordinated "what can the worker run" lists into one derived source | — |
| [`TASK-A2-PROMOTE-SEVEN.md`](./TASK-A2-PROMOTE-SEVEN.md) | Ship the six finished modules and two providers still parked on a chore branch | A1 |
| [`TASK-A3-STRANDED-MODULES.md`](./TASK-A3-STRANDED-MODULES.md) | Route `sqlQuerier` and `audioReaderNode`, whose worker modules nothing reaches | A1 |
| [`TASK-A4-REPORT-BUILDER.md`](./TASK-A4-REPORT-BUILDER.md) | Migrate `reportBuilder` — the cheapest node, used to re-validate the template | A1 |
| [`TASK-A5-IMAGE-FAMILY.md`](./TASK-A5-IMAGE-FAMILY.md) | Migrate `imageGenerator` + `imageReaderNode` over one shared provider layer | A1 |
| [`TASK-A6-FRONT-DRIVEN-NODES.md`](./TASK-A6-FRONT-DRIVEN-NODES.md) | Give the nine front-driven types server-side execution for the first time | A1 |
| [`TASK-A7-OBJECT-CALLER.md`](./TASK-A7-OBJECT-CALLER.md) | Migrate `nodesBox` behind two new callbacks and an ordering guarantee | A1, B1 |
| [`TASK-A8-INPUT-EXTRACTION.md`](./TASK-A8-INPUT-EXTRACTION.md) | Move `varInputNode`'s link extraction, upload and OCR off the request path | A1 |
| [`TASK-A9-OUTBOUND-DELIVERY.md`](./TASK-A9-OUTBOUND-DELIVERY.md) | Emails and HTTP callbacks as retried activities instead of fire-and-forget | A1 |

### Track B — the flow itself (G2)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-B1-EXECUTION-IDENTITY.md`](./TASK-B1-EXECUTION-IDENTITY.md) | Make the reference between nodes identify one **execution**, not one node in a run | — |
| [`TASK-B2-CODE-SHARING.md`](./TASK-B2-CODE-SHARING.md) | Decide shared package vs copy-port, then extract the scheduler and the substitution service | — |
| [`TASK-B3-WORKER-INPUT-RESOLUTION.md`](./TASK-B3-WORKER-INPUT-RESOLUTION.md) | Let the consumer resolve its own input, building on the prefetch executor | B1, B2 |
| [`TASK-B4-GRAPH-WORKFLOW.md`](./TASK-B4-GRAPH-WORKFLOW.md) | Move the DAG loop into a Temporal workflow — **sequential first**, no parallelism yet | B2, B3 |
| [`TASK-B5-PARALLEL-DISPATCH.md`](./TASK-B5-PARALLEL-DISPATCH.md) | Turn on batch dispatch, gated per flow on full coverage | A-track complete, B4 |
| [`TASK-B6-CONTROL-FLOW.md`](./TASK-B6-CONTROL-FLOW.md) | `conditionNode`, `arrayNode` as workflow control flow; `fluxBox`, `libraryNode` as child workflows | B4 |
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
| [`TASK-E2-CANCELLATION.md`](./TASK-E2-CANCELLATION.md) | Align cancellation with Temporal's native mechanism instead of porting the poller | B4 |
| [`TASK-E3-DISTRIBUTED-NOTIFICATIONS.md`](./TASK-E3-DISTRIBUTED-NOTIFICATIONS.md) | One publish path for run events, working across replicas | before B5 |

### Track D — documentation (G4)

| Task | Goal | Depends on |
|---|---|---|
| [`TASK-D1-DEVELOPER-DOCS.md`](./TASK-D1-DEVELOPER-DOCS.md) | Mintlify pages: the node lifecycle, how to add a node, the callback and error reference | runs alongside |
| [`TASK-D2-MACHINE-CONTRACT.md`](./TASK-D2-MACHINE-CONTRACT.md) | One generated, test-enforced contract an agent can read; refresh the stale skill and CLAUDE.md | A1 |

## 5. Sequence

```
S4 · S5 · C3 (standalone, any time)
S2 (before ANY worker scaling)      S6 (with A6/A8)     E3 (before B5)
S1 ──────────────────────────────────────────────── blocks B6
S3 ──────────────────────────────────────────────── blocks B5

A1 ──┬── A2 ── A3 ── A4 ── A5 ── A6 ── A8 ───────┐
     │                                            │
     └── D2 ── D1 (continuous)                    │
                                                  │
B1 ── B2 ── B3 ── B4 ──┬── E1 (with B4) ──┬── A7 ─┼── B5 ── B6
                       │                  │       │
                       └── E2             └── C1 ─┴── C2
```

Read as four rules:
1. **A1 first, always.** Every later task adds a node type to a registry; if the registry is still
   four lists, every task pays that tax and one of them will get it wrong.
2. **The A track and the B track run in parallel** up to B5. They only converge when parallelism
   is switched on, because that is the first moment coverage actually matters.
3. **B4 ships sequential.** Moving the graph and enabling parallelism must be two deploys, or a
   rollback cannot tell which change broke the run.
4. **Track S is not a phase, it is a precondition set.** S2 blocks adding worker replicas at all,
   S3 and S2 block parallel dispatch, S1 blocks child workflows, and S6 is decided inside A6/A8
   rather than after them. Only S4 and S5 are free-floating.
5. **C3 and E3 come first and stand alone.** C3 fixes defects in code that B2 is about to
   duplicate — after duplication each fix costs twice. E3's replica bug is already live and does
   not need the migration to bite; it only gets worse when parallelism multiplies the event rate.
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
| R5 | **Ordering loss for `nodesBox`.** The engine serialises object access through one in-memory array today; parallel activities do not. | high | A7 ships an advisory-lock or an idempotent activity, and is gated behind B1. |
| R6 | **Drift between the repos.** Two pure modules copied instead of shared (§7.6). | medium | B2 decides explicitly and records the decision; if copy-port wins, a `PORTED_FROM.md` with the source SHA and a drift test, as the integration migration did. |
| R7 | **The stale skill teaches the wrong thing.** `skills/node-worker-migration/SKILL.md` still describes a 10-type enum and knows nothing of the gates or prefetch. | medium | D2, early — an agent following it today produces wrong work. |
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
| D1 | Shared package between `back` and `worker`, or copy-port with a drift test? | B2, and therefore B3/B4 | The repos are separate submodules with no shared build graph; the integration migration chose copy-port for good reasons. The two modules here are *pure*, which is the case where sharing is cheapest. |
| D2 | Is the prefetch executor the destination for worker-side input resolution, or a stopgap to retire? | B3, C2 | Needs the measurement in C2 first: how many production flows satisfy its whitelist, and what did it save. A flag defaulting to `legacy` whose whitelist excludes every LLM node may be shipped but dormant. |
| D3 | The nine front-driven types do not run in headless flows today. Intended, or a silent defect for customers with one in a scheduled flow? | A6 | Independent of the worker. Answer it on its own before A6 turns it into a behaviour change. |
| D4 | Are `sqlQuerier` and `audioReaderNode` unreachable on purpose — a migration paused mid-way — or by oversight? | A3 | Changes whether A3 is "finish it" or "delete it". |
| D5 | What are `comment`, `label`, `group`? They are trusted by the prefetch whitelist but are not registered front node types. | A1 | The registry cannot be authoritative while three types in a live whitelist are unaccounted for. |

## 8. What this epic explicitly does not do

- It does not migrate the 13 node types with nothing to migrate (§4.4), and does not invent
  run-time behaviour for the four configuration-time types.
- It does not decide whether `tableProcessor`'s transform should exist server-side — that is a
  product question with no engineering answer (§4.3).
- It does not change the front's builder UX beyond the Run button's dispatch path.
- It does not touch billing, model access, or file storage contracts. Those callbacks already
  exist and are the boundary this epic keeps.
