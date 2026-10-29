# C2 — Retire the legacy surfaces, and settle the prefetch question

**Goal:** remove the entry points and the flags that only existed to bridge the migration, and
decide the prefetch executor's fate on evidence.

**Depends on:** C1, B4. **Answers:** decision **D2**.

## Scope — four separable pieces

**Not in scope, settled by `D18`: the batch-process endpoints stay.** None of the five is
deprecated — `POST /batch-process` (`flux.controller.ts`), `GET /batch-process/:id/status`, `GET /batch-process/all`, `POST /batch-process/:id/stop` and
`GET /batch-process/:ids/download`. The route stays as the entry point and its body moves
into `B7`'s durable workflow; the status, stop, listing and download endpoints are the batch's only
surface — the screen that would read them is not built in this epic (B7, 2026-09-02) — and they stay
regardless. Do not sweep them up with the legacy endpoint below — they look similar and are not.


### 1. `/process/single-node-legacy`

`back/src/temporal/temporal.controller.ts`, backed by
`single-node-legacy/single-node-legacy.service.ts`. Its `validateNode` refuses
migrated types, refuses mutating types, and accepts only `LEGACY_SINGLE_RUN_NODE_TYPES`.

Once every executable type runs in the worker, this endpoint accepts nothing — it becomes a
router with an empty destination set. Retire it and the allowlist that feeds it.

**Corrected 2026-09-21 — this defect is now four types, not one.** The original draft named
`thirdPartyIntegration` as worker-routed inside a flow while still accepted (and run inline) by this
endpoint. A1's re-validation against `back@origin/production` `3804a524` found `isTemporalNode` minus
`MIGRATED_TEMPORAL_NODE_TYPES` is actually four types — `commandContentNode`, `voiceBoxNode`,
`webSearch`, `webCrawling` — and three of the four (`voiceBoxNode`, `webSearch`,
`commandContentNode`) are in exactly this shape: worker-routed inside a flow, but still in
`LEGACY_SINGLE_RUN_NODE_TYPES`, so this endpoint runs them inline. `webCrawling` is the different
case, below. A1 adds a `dispatchConflict` invariant for this exact defect — three named
`it.failing()` cases (jest 29.0+; `back` is on 29.3.1), green on arrival, each turning red the
moment its type is fixed; C1 clears each as it does that node's inline-twin deletion, so by the time
this task retires the endpoint, the allowlist should already be down to `reportBuilder` and whatever
A3's decision keeps routed there. If any of the three are still in `LEGACY_SINGLE_RUN_NODE_TYPES`
when this task starts, that is the fix to carry — same defect, same remedy, three known instances
instead of one.

**`webCrawling`'s defect is a different shape and already has its own fix.** It is in **neither**
`MIGRATED_TEMPORAL_NODE_TYPES` nor `LEGACY_SINGLE_RUN_NODE_TYPES`, so `single-node-legacy.service.ts`
(`validateNode`) refuses it with the generic message — grep for
`is not supported for single-node legacy execution` — instead of the correct migrated-type message —
grep for `is migrated to Temporal`.
A1 carries this as a bounded sub-item (add `webCrawling` to the migrated-type check) with its own
Done-when line; by default it lands in A1's PR, not here. If A1's PR ships without it for any reason,
it is this task's to pick up before the endpoint retires — but check A1's PR first, since the default
plan is that it never reaches C2 as open work.

**The two dead branches, moved here from A1 (2026-09-21).** `legacy-node-dispatch.ts`'s
`dispatchLegacyHandler` has `case 'pullData'` and `case 'pushData'`, but both types are in
`MIGRATED_TEMPORAL_NODE_TYPES`, so `validateNode` rejects them before `dispatchLegacyHandler` is ever
reached — the branches are unreachable today and stay that way until this task deletes the whole
switch. A1 only records their existence as evidence that the legacy endpoint's effective destination
set is already smaller than its allowlist suggests; deleting them is this task's, alongside the rest
of `legacy-node-dispatch.ts`, because it is legacy-surface removal, not registry work.

### 2. The prefetch executor — execute the D2 answer

`back/src/app-api/flux/prefetch/` is in production behind `FLUX_EXEC_MEMORY_MODE`, defaulting to
`legacy`, with a 17-type whitelist that excludes every Temporal type and every control-flow type
(analysis §9.2.1). **The measurement is A1's and the answer is B3's** (ownership split 2026-09-02,
PLAN §7 D2): A1 reports, while it runs `canUsePrefetchForFlow` against every stored flow in Wave 2,
how many flows satisfy the whitelist, how many ran with the flag on, and what it saved; B3 answers
D2 with those numbers in Wave 4. This task **executes** whichever answer won:

- **Destination:** it is the model B3 generalised; the whitelist is derived from the A1 registry, not
  hand-maintained, and the executor stays.
- **Stopgap:** B3's worker-side resolution superseded it; retire the executor and its whitelist,
  removing a fourth list from the world.

Either answer is fine. Leaving it undecided is not: a dormant second execution path is a
maintenance tax nobody is paying attention to.

### 3. The migration flags

Every flag from PLAN §3.2 is temporary by construction. A flag that outlives its migration is a
branch of production behaviour nobody tests. Remove each once its node has soaked.

**Inventory and removal conditions (added 2026-10-23).** "Soaked" was never defined, so this table
defines it per flag. A flag goes only when every condition in its row holds in production, and the
PR that removes it also deletes the off path it guarded and updates the env-var docs
(`env-vars-sync`). The 14-day window is a proposal; confirm it before Wave 6 starts.

| Flag | Created by | Remove when, in production | Deletes with it |
|---|---|---|---|
| `engine_in_workflow` | B4 | On for 14 days with no rollback; zero runs routed to `legacy_loop` in that window (the route log in `apiV2`); A7's shadow comparison shows zero differences | The back's run loop, and A7's shadow comparison |
| `worker_input_resolution`, `worker_input_resolution_shadow` | B3 | On for 14 days; zero shadow mismatches (`b3b-q7-shadow-by-hour.sql`) | The back's placeholder substitution on the run path |
| `worker_edge_projection` | B3b | On for 14 days; zero projection errors (`b3b-q4-2-edge-projection-errors.sql`) | The back's edge projection on the run path, and `BACK_ONLY_PROJECTION_NODE_TYPES` |
| `run_log_events_shadow`, `run_log_from_events` | E1 | `run_log_from_events` on for 14 days; the E1 check (`b1-q2i`) clean in that window | The old run-log writer |
| `FLUX_EXEC_MEMORY_MODE` (env) | Prefetch, before the epic | `legacy` since 2026-08-20; D2's answer recorded here | The prefetch executor (section 2) |
| `repeatable_schedules` | S8 | E4's Temporal Schedules on for 14 days; zero Bull repeatable registrations | The Bull repeatable consumer |
| `MIGRATED_INTEGRATION_PROVIDERS` (code list) | A2, A10 | Every provider routed to the worker; A11 derives routing from the registry | The list |
| B5's parallel dispatch flag | B5 | General rollout complete; B5 decides whether it becomes a batch-size setting or stays as a kill switch | — |

**Not migration flags — kept unless decided otherwise.** These guard permanent features, so this
task does not remove them by default: `execution_budget` (S4), `spend_ceiling` and
`tenant_concurrency_cap` (S3), `node_credit_gate` and `node_credit_gate_no_plan` (billing), and the
S7 rate-limit modes. Open decision: keep each boolean as a kill switch, or remove it and keep only
the limit values. `node_cancel_in_flight` predates the epic and is out of scope.

**Wave 6 entry gate.** Every Wave 5 task is shipped; the B4 flag has been on in production for the
whole window above; and each row of the table carries the date and result of its check. A row
without a recorded check is not removable, whatever the calendar says.

### 4. The deprecated node types (added 2026-10-28)

`webNews`, `webMedia`, `webLocations` and `varInputForm` are deprecated. A11 removes them from the
MCP metadata, the per-type tables, the seeder and the back's `NodeType` enum, and keeps them in one
deprecated list in the dispatch registry (see
[`TASK-A11-REGISTRY-EXECUTION-CLASS.md`](./TASK-A11-REGISTRY-EXECUTION-CLASS.md), **What the
2026-10-29 implementation and review changed**, item 6). Because saved nodes of these types still
exist (dev: 47), A11 also makes sure a saved one never blocks a flow: the front shows a placeholder
the user can delete, the back accepts an existing node on every update, copy, version and import
path while refusing a new one, and the MCP marks it as deprecated. Three things stay until the saved
nodes are gone:

- the deprecated list in the dispatch registry, with the four `visual` phantom entries;
- the validator rule that accepts an existing node of a deprecated type, and the MCP marker;
- the front placeholder node for the four types.

This task removes them, in this order:

1. **Count.** Count the saved nodes of each type and the edges that touch them, on the live canvas
   (`flow_version_history_id IS NULL`) and in version history, on production. `a11-q2` counts the
   live canvas only; add a query that covers both and record the result here. Rows that only
   record past runs (`node_executions`, `run_seed_nodes`) are not counted: the retention purge owns
   them, and nothing edits them.
2. **Delete.** Delete the nodes and every edge that touches them, live and in version history,
   through an internal endpoint (`JwtAuthGuard` + `MasterUserGuard`), not a hand-run script. The
   endpoint has a dry run that reports the counts per type, and the real run must match them.
   Version history matters: restoring an old version would bring a node back, and the placeholder
   is what keeps that flow usable until then.
3. **Remove.** Once a re-run of the count returns zero in both places: the deprecated list and its
   four registry entries, the validator rule and the MCP marker, and the front placeholder. A11's
   drift spec then has nothing to cover for them.

**Remove when, in production:** the count returns zero, live and in version history, after step 2.
A count that has not been recorded keeps everything in place, like a flag row in section 3.

## Decisions (2026-10-23)

| Id | Question | State | Answer |
|---|---|---|---|
| C2-b | A type that runs in the worker inside a flow is still accepted, and run inline, by `/process/single-node-legacy`. Fix it now, or carry it? | **Settled: fix it** (option A) | Set `legacyEndpoint` to refuse-as-migrated in the dispatch registry for every type that the endpoint still accepts and that has a worker module. On back `origin/main` `a38fef57` that is `commandContentNode`, `thirdPartyIntegration` and `voiceBoxNode` (`webSearch` is already fixed). In the same change, give `webCrawling` the migrated-type message instead of the generic one. Regenerate `node-dispatch-contract.json`. Each refusal needs the same care as any refusing rule: count the calls each type received on that endpoint first (PLAN §3.3.2). This fix does not wait for C1. **Updated 2026-10-29:** A11 refuses `thirdPartyIntegration` and `hubSpotCRM` on this endpoint. It still accepts `commandContentNode` and `voiceBoxNode` (`summary.dispatchConflicts` in `node-dispatch-contract.json`), and those two stay for this task. |

## Verification

- **Negative control (required).** Call `/process/single-node-legacy` with each node type before
  retirement and record the response; after retirement, confirm the removal is a clear 404/410 and
  that the front never calls it. A silently-dead endpoint the front still calls is worse than
  keeping it.
- **Measure before refusing** (PLAN §3.3.2), applied to the measurement itself: report flows whose
  eligibility you could not determine as *unverifiable*, not as ineligible. The prefetch decision
  must not rest on a count that quietly rounded unknowns to zero.
- Front check: `ProcessService.responseLegacy` (`front/src/service/processService.ts`) must have no
  callers before the endpoint goes.
- **Deprecated types (section 4).** The endpoint's dry-run counts match the count query. After the
  deletion, the count is zero live and in version history, and restoring a version that held one
  of the four succeeds. Negative control on dev: after the enum members go, create a node of one of
  the four through the API and watch it be refused.

## Done when

The legacy endpoint and its allowlist are gone; D2 is answered in writing with the numbers behind
it; no migration flag from this epic remains.

**Added 2026-10-23.** The back's run loop is deleted by name: the `while (scheduledId !== null)`
loop in `apiV2`, its `arrayNode` loop body, and the per-type branches. A11's expected-failure test
("no executable node type runs in the back") becomes a plain test and passes.

**Added 2026-10-28.** The registry's `flowDispatch` field is removed. With the back's loop gone,
`inline` means nothing, and `flowDispatch` repeats A11's `execution` field. Its readers
(`canUseWorkflowForFlow`, `isTemporalNode`, `strandedWorkerModules()`, `hasDispatchConflict()`)
read `execution` instead, and `node-dispatch-contract.json` drops the column.

**Added 2026-10-28.** No saved node of `webNews`, `webMedia`, `webLocations` or `varInputForm`
remains, live or in version history, and the four are gone from the `NodeType` enum, the MCP
guards, the dispatch registry and the front (section 4).

## Files

`back/src/temporal/temporal.controller.ts` (`/process/single-node-legacy`) · `back/src/temporal/single-node-legacy/**` ·
`back/src/app-api/flux/prefetch/**` (`memory-mode.ts` owns `FLUX_EXEC_MEMORY_MODE`) · `back/src/app-api/flux/flux.service.ts` (`PREFETCH_SUPPORTED_NODE_TYPES`, `canUsePrefetchForFlow`, the `isPrefetchMode()` switch) ·
`front/src/service/processService.ts` · section 4: `back/src/enums/node_types.enum.ts`,
`back/src/app-mcp/node-types/node-types.service.ts`, `back/src/app-mcp/mcp-write.service.ts` and
their specs, `back/src/shared/node-dispatch/node-dispatch-registry.ts`, a new internal endpoint for
the deletion, `front/src/views/CoreNodeDisplay.tsx`, `front/src/views/CoreNodeDisplaySpaces.tsx`
and the front constant of deprecated types
