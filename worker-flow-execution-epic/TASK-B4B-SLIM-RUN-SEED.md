# B4b — Keep node data out of Temporal history (slim run seed)

ClickUp: [1gahkf3byq7](https://app.clickup.com/t/1gahkf3byq7). **Drafted 2026-11-24** from the A14 edge-case investigation
(`TASK-A14-SMALL-MEMORY-AND-CHAT-STATE.md`, "Edge-case investigation (2026-11-24)" and A14-D12).
Status: specified, approved by the user on 2026-11-24.

**Depends on:** B4 (on `main`). Ships after B6 and B5 reach `main`, because both rewrite the same
`processFlow` call sites and add history-heavy array and child-flow payloads.
**Blocks:** turning `engine_in_workflow` on in production
([868mnbm7h](https://app.clickup.com/t/9011479430/868mnbm7h)), removing A14's seed-size guard
(A14-B19), and Wave 6 (C1, C2), which deletes the legacy loop that guard falls back to.

## Problem statement

A workflow run writes every node's full `data` into Temporal history twice: once as the result of
`loadRunSeedActivity` (the whole `run_seeds.payload`, again on every `continueAsNew` segment) and once
per node as the `nodeData` input of `openNodeExecutionActivity`. Temporal refuses any payload above
2 MB (`limit.blobSize.error`), so a flow whose node data adds up past about 2 MB cannot run on the
workflow engine, while the legacy loop runs it. Measured on 2026-11-24: a 2.84 MB Small Memory fails
with `Complete result exceeds size limit` (HTTP 500). B4's own spec asked to pass the seed by
reference and to measure the largest seed before the flag goes on; neither has happened.

The data is also stored twice per run in Postgres (`run_seeds.payload` and `run_seed_nodes`), and
`run_seeds` is never purged. `run_seed_nodes` is purged daily at 03:00 once it is older than
`RUN_MAX_DURATION_MS` plus one hour (7 h), while `processFlow` starts without an execution timeout
and the unfinished-run reaper is off in production, so a run alive past 7 h loses its seed rows.

## Goals

- [ ] No node's `data` enters Temporal history on the `processFlow` path; the history carries only
      the scheduling skeleton (ids, types, edges, starter, and the few control fields B5 and B6
      read).
- [ ] A flow whose node data totals 10 MB runs on the workflow engine with the same result as on the
      legacy loop.
- [ ] A14's 1.5 MB seed-size guard is removed.
- [ ] Seed rows cannot be purged while their run is still open, and `run_seeds` has a retention.

## Out of scope

| Item | Reason |
|---|---|
| Pruning the seed to the reachable set | Deferred by B4b-D1. |
| A single array item or node output above 2 MB | A separate limit (array items enter history as `writeArrayIterationItemActivity` input). Recorded as a known limit. |
| Placeholder substitution on the workflow path | B4c. |
| Small Memory storage | A14b. |

## User stories

### P1: A flow with large node data runs on the workflow engine ⭐ MVP

**User story:** As a customer whose flow holds large text or memory, I want my run to finish on the
workflow engine, so that the engine switch does not break my flow.

**Acceptance criteria:**

1. WHEN `processFlow` loads its seed THEN the activity result SHALL hold no node `data` beyond the
   control fields the workflow reads.
2. WHEN a node execution opens THEN its `data` SHALL be read from `run_seed_nodes` by
   (`snapshotId`, `nodeId`) and SHALL NOT be an activity input or result.
3. WHEN a flow's node data totals 10 MB THEN the run SHALL finish and match the legacy loop's
   answer, persisted outputs and deliveries.
4. WHEN a history recorded before this change replays THEN it SHALL replay without a
   non-determinism error.

**Independent test:** run a 10 MB-seed flow on both engines locally; it fails on the workflow before
the change and passes after (negative control).

### P1: Seed rows live as long as their run ⭐ MVP

**User story:** As an operator, I want a long run to keep its seed rows until it closes, so that no
run fails because a cron deleted its inputs.

**Acceptance criteria:**

1. WHEN the daily purge runs THEN it SHALL NOT delete the seed rows of a run that is not closed.
2. WHEN a run closed more than the retention period ago THEN its `run_seeds` row SHALL be deleted.
3. WHEN a batch-row or schedule finish activity is still retrying THEN its `run_seeds` row SHALL
   stay.

**Independent test:** a run kept open past the purge window still reads its seed; a closed run's
seed is purged after the retention period.

### P2: Remove A14's seed-size guard

1. WHEN B4b is in production THEN the engine selector SHALL NOT route a run by seed size.

## Edge cases

- WHEN a run uses `continueAsNew` THEN each segment SHALL load only the skeleton.
- WHEN an `arrayNode` body or a `fluxBox`/`libraryNode` child flow runs (B6) THEN their configuration
  SHALL come from activities that return ids and counts, not the child graph's full data.
- WHEN `run_seed_nodes` has no row for a node THEN the open SHALL fail with the existing
  `missingSeedError` message, not a generic error.

## Decisions

| ID | Question | Settled | Rejected |
|---|---|---|---|
| B4b-D1 | Prune the seed to the reachable set plus the nodes that `{{...}}` placeholders and `*Data` arrays reference, using a list of targets stored per seed? | **Deferred (2026-11-24).** Once node data leaves history, pruning saves only Postgres rows. Revisit after the production run of `a14-q5` shows how many bytes sit outside the reachable set, and after B4c (placeholder substitution on the workflow path) ships, because a pruning pass must keep every placeholder target | Prune in B4b with a seed-time scan |
| B4b-D2 | How long seed rows live | **Settled (2026-11-24):** the daily purge deletes only rows of closed runs; `run_seeds` stays 7 days after the run closes, and longer while a batch-row or schedule finish activity still retries | An execution timeout on `processFlow` equal to the run ceiling, keeping the time-based purge |
| B4b-D3 | Who reads node data at open | Open: the worker activity reads `run_seed_nodes` and posts it to back, so the HTTP body never enters history. Settled in Design | Back reads the row itself in `openWorkerNodeExecution` (deploy back first) |

## Requirement traceability

| ID | Story | Status |
|---|---|---|
| B4B-01 | P1 large data: skeleton-only seed result | Pending |
| B4B-02 | P1 large data: node data read at open, not passed | Pending |
| B4B-03 | P1 large data: 10 MB parity and replay | Pending |
| B4B-04 | P1 seed lifetime: no purge of open runs | Pending |
| B4B-05 | P1 seed lifetime: `run_seeds` retention | Pending |
| B4B-06 | P2 guard removal | Pending |

## Measurement before shipping

Production queries, run by the user: `a14-q5` (per-flow seed size), `a14-q6` (largest node data by
type), `a14-q7`/`q13` (`run_seeds` and `run_seed_nodes` sizes), `a14-q12` (longest workflow runs
against the 7 h purge).

## Estimate

About 1.5 to 2.5 days on `main`, plus about 1 day to fit B5 and B6. Worker: about 6 files (seed
projection, open activity, types, `processFlow` input, B6 child and array activities, specs and a
replay history). Back: none, or 3 files if B4b-D3 picks the back read. Purge: 2 files.

## Test list (must pass)

1. Negative control: a flow whose node data totals 10 MB fails on `main` with `Complete result
   exceeds size limit`; after the change it finishes, and its answer, outputs and deliveries match
   the legacy loop's.
2. No `processFlow` history recorded in the tests holds a payload above 512 KB.
3. A history recorded before the change replays without a non-determinism error.
4. A run that crosses `continueAsNew` loads only the skeleton in each segment.
5. A batch row, a scheduled run and a child flow (B6) with large node data finish.
6. The purge leaves the seed rows of an open run older than 7 h, and deletes them after the run
   closes plus the retention period; a retrying batch-row finish still finds its seed.
7. A missing `run_seed_nodes` row fails the open with the existing `missingSeedError` message.
8. With A14's guard removed, a 3 MB memory flow runs on the workflow engine.

## Success criteria

- [ ] A 10 MB-seed flow passes on the workflow engine locally and on dev.
- [ ] No `processFlow` history on dev holds a payload above 512 KB (Temporal's warn line).
- [ ] 868mnbm7h lists B4b as done before its date is set.
