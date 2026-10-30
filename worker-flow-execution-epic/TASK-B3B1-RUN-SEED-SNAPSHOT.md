# B3b.1 — Run seed snapshot for the worker's input

**Goal:** the worker builds a node's input from the flow as it was prepared at run start, never from
the live `flows_nodes` row, so that the back can stop sending its projected `node.data` with no
change in what a node receives.

**ClickUp:** `868mh8pqh`. **Parent:** [B3b](TASK-B3B-EDGE-PROJECTION.md) (`868mfkzgh`). **Branches:** the B3b branches
(`refactor/868mfkzgh` in back and worker, `docs/868mfkzgh-b3b-spec` here). Every commit of this
subtask carries the subtask id in its message; `git log --grep 868mh8pqh` lists them. The subtask starts
after back `05cd4073`, worker `e4d4841` and spec `6bf6412`.

## Why

B3b's worker projection reads a source that did not run from `flows_nodes` at dispatch time. Letting
the worker also seed the target from there, so the back can stop projecting, changes what a node
receives:

- **It breaks the anti-leak rule.** `createNodeExecution` states that a node's input must never come
  from the live `flows_nodes` row (the Therabee URL revert, and a PHI leak between concurrent runs).
  The worker merges every success output into that row except `LIVE_WRITE_EXCLUDED_FIELDS`, so an
  `apiCaller`'s resolved `url`, `headers` and `password`, `variables` and `urlData` of another run can
  be there at dispatch time.
- **Edits made during a run reach it.** 8 of 140 dev runs in 14 days had their flow saved while they
  ran. Today the back ignores those edits: it reads the flow once, at run start.
- **The run-start preparation lives only in memory.** `stripStaleErrorState`, the per-type resets,
  the Small Memory sessions, `clearRunOutputForSeed` and the run's input text are applied to the
  back's node list and never saved.

## Design

1. **Save the prepared flow once per run.** When the run opens the worker projection (B3's
   resolution and `worker_edge_projection` on, no back-only node), the back writes the prepared node
   list to `run_seed_nodes`, one row per node (`snapshotId`, `nodeId`, `type`, `data`), in the same
   statement that writes the run's first `run_substitution_snapshots` row. It is the list after
   `clearRunOutputForSeed` and `clearObjects`, with the run's input text applied to each
   `varInputNode`, and before any projection. The rows cascade from the snapshot, so B3's release
   at run end and the snapshot retention purge delete them too. One row per node keeps a dispatch's
   read to the nodes it needs: `flows_nodes.data` per flow version reaches 726 kB at p95, 2.05 MB at
   p99 and 53 MB at most in production (2026-10-14), and a single `jsonb` value is decompressed
   whole on every read.
2. **The dispatch names the seed and the starter.** `NodeInputProjection` gains `seedSnapshotId`
   and `starterSourceId`, the run's starter as the back finds it (`flowGlobalEdge`).
3. **The back sends the seed, not its projection.** On a dispatch that carries a projection, the
   target's input (and, in shadow mode, its raw input) is the target's seed. The resolution mode is
   computed from the original objects first, so `outputController`, `reportBuilder` and
   `counterNode` keep `refArrays`.
4. **The worker reads only the seed and this run's rows.** A source that did not run comes from the
   seed, never from `flows_nodes`. Edges that leave the starter are left out: the starter never
   completes, so the back never projects from it. Projecting it added `variables: []` to the first
   `scripting` or `mathFunction` node, which the first dev run in shadow mode caught.
5. **Completed nodes are the back's list.** `completedSourceIds` lists the completed nodes in the
   target's upstream neighbourhood: its sources, and through each source that did not run, that
   source's sources. The worker uses a `node_executions` row only for a node in that list, and fails
   loudly when a listed node has none. A parent run that calls the same sub-flow twice then cannot
   read the first call's rows for a node the second call has not run.

No start-of-run code moves or is ported: the back saves what it prepared, so the worker restates no
rule.

## What stays the same

| What | Today | After |
|---|---|---|
| Projected `*Data` | The back projects in memory | The worker projects; 101 of 101 verifiable dev targets match |
| Error and status fields, resets | Prepared at run start | Saved prepared, at run start |
| Edits and other runs' writes during the run | Ignored | Ignored |
| Input text of concurrent runs | Shared live row | Each run's own seed |
| Loops and sub-flows (`arrayNode`, `libraryNode`, `fluxBox`) | Back | Back (gated) |

## Verification

- **Negative controls.** Seed a source from `flows_nodes` instead of the snapshot and watch a test
  with a concurrent run's value go red. List a completed node without a row and watch the node fail.
  Drop the seed write and watch the dispatch fail loudly, not run with an empty input.
- **Equivalence.** The B3b harness re-runs over dev rows. A local run in shadow mode, which compares
  every field of the worker's input with what the back resolved, needs the full local stack and real
  provider calls; it is not run yet.
- **Size.** Measure the seed per run on dev (about 6.8 kB per flow on average) and ask for the
  production distribution before enabling the flag there.

## Commits

| Repo | Commit | What it does |
|---|---|---|
| back | `587dd282` | Adds the `seed` column and its migration, saves the seed with the run's first snapshot, sends the target's seed and the completed upstream neighbourhood. |
| worker | `be6cad3` | Syncs `NodeInputProjection.seedSnapshotId` from the back. |
| worker | `d9318b4` | Reads a source that did not run from the seed, uses only listed completed rows, and fails loudly on a missing row or seed. |
| back | `f0faf9ae` | Seeds the `worker_edge_projection` flag, off. The admin screen toggles only flags that already have a row. |
| back | `b44c8708` | Moves the seed to `run_seed_nodes`, one row per node, written with the snapshot in one statement and cascading from it; names the run's starter in the projection. |
| worker | `1741f79` | Syncs `NodeInputProjection.starterSourceId` from the back. |
| worker | `3ae454c` | Reads only the seed rows it needs and leaves out edges that leave the starter. |

`scripts/check-no-dev-in-prod-pr.sh` passes on both branches against `origin/main`.

## Results

- **Tests.** Back: 27 tests in `node-input-projection.spec.ts`, plus the `worker-input-resolution`,
  `node-execution-run-id` and `ported-engine` specs, pass (32 passed, 1 skipped without
  `WORKER_REPO_PATH`). Worker: 145 tests in `src/modules/nodes/shared` and `src/ported` pass against
  a local Postgres. Worker `tsc` reports no errors.
- **Negative controls, back (7).** Each one went red, including "saves the seed once", which first
  stayed green and was strengthened until it failed.
- **Negative controls, seed per node and starter (6).** Each one went red: the writer without the
  seed insert (3 tests), the seed rows without a cascade (2), the projection without
  `starterSourceId` (build error), the worker without the starter filter (1), the worker reading
  another snapshot's seed rows (5), and the seed check that ignores the table (1).
- **Negative controls, worker (4).** Each one went red:

  | Change | Tests that failed |
  |---|---|
  | Read the seed from `flows_nodes` | 4: both seed tests in `projectNodeInput` and both projection tests in `resolveNodeInput` |
  | Drop the missing-row check | 2: an upstream, and a completed node behind a source that did not run |
  | Drop the seed check | 1: "fails loudly when the run has no seed" |
  | Drop the completed filter | 1: "ignores a row of this run for a node the back does not list as completed" |

- **Equivalence on dev rows.** The B3b harness now serves the seed and throws on any `flows_nodes`
  read. On the projected `*Data` the result is unchanged: 101 of 101 verifiable targets match, 29 are
  gated, 10 are single-node runs and 1 diverges on a draft saved after the run. No target fails on a
  missing row.
- **What the harness cannot prove.** On every field, the remaining differences are the target's own
  run output (`nodeUsedTokens`, `logs`, `executionStatus`) and edits (`aiModel`, `aiSystem`) that later
  runs wrote to the exported rows. The harness emulates the seed from those rows, so they are not the
  run-start values. In the product the target's non-projected fields come from the same prepared
  object the back used before, which the `processNodeViaTemporal` tests pin.

## Rollout

The flag must stay off while the back and the worker deploy, and go on only after both run the new
code. During a rolling deploy the old back task keeps processing runs until it stops: on dev it
took about 8 minutes, and its rows had no `runId`. With the flag on, a dispatch from the old back
reaches the new worker without a projection, and a run that touches both versions can fail on a
missing row.

## Dev test (2026-10-14)

Dev ran back `67ff461f` and worker `c3d6a0ee` with `worker_input_resolution_shadow` and
`worker_edge_projection` on. The same three flows ran before and after the starter fix:

| Run | Flows | Nodes matched on every field |
|---|---|---|
| Projection off (baseline) | scripting ×3 → Text Generator; webSearch → `outputController`; scripting → Text Generator | 8 of 8 |
| Projection on, seed as one value | same | 7 of 8: the first `scripting` gained `variables: []` from the starter |
| Projection on, seed per node, starter skipped | same | 8 of 8 |

After the runs, `run_seed_nodes` and the runs' snapshots are empty, so the release at run end
removes the seed. The Text Generator in the third flow fails with a provider error from its own
model (`llama-3.1-8b-instant`) in every run, with or without the projection.

At 17:19 UTC the dev folder that held these flows was deleted with 39 flows. Two of them were
rebuilt from their stored rows in the folder "B3B dev checks", the first with its Text Generator on
`claude-4-5-haiku-latest`:

| Run | Mode | Flow | Result |
|---|---|---|---|
| `45a41dab` | shadow | scripting → Text Generator (Haiku) → Text Box → Data Output | Completed; both worker nodes matched; the Data Output received the generated text |
| `95913bf9` | apply | same | Completed; both nodes resolved by the worker; the Text Generator's input carries the script's console text in `instructionData` |
| `b77c0a93` | apply | webSearch → `outputController` | Completed; the `outputController`'s `textData` carries the search result (`refArrays` mode) |

## Out of scope

The order of execution, ready and dead nodes, and the loop: B4. Back-only sources: B6.
