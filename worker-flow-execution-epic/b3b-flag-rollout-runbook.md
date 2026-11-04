# 868mktvma rollout: deploy, then `worker_input_resolution`

Task: [868mktvma](https://app.clickup.com/t/868mktvma). PRs: back [#2054](https://github.com/enhancedai-com/Flux-Prompt/pull/2054), worker [#139](https://github.com/enhancedai-com/Flux-Prompt-Worker/pull/139), both merged into `main`.

The deploy ships three changes:

- **B3B fix (worker):** the worker keeps the starter's `Data` entry. This removes the prod nodes that mismatched on every run (77 on 2026-10-22, see `b3b-q6`), and it is what blocks `worker_input_resolution`.
- **Unique index (back):** `UQ_NODE_EXECUTIONS_EXEC_NODE` on `node_executions ("execId", "nodeId")` for rows created after the B1 release. The migration runs at boot and blocks writes to `node_executions` while it builds.
- **SEC and Census gate (back and worker):** both nodes ask the node credit gate. This applies only while `node_credit_gate` is on, and only in single-node runs. In a flow run, the back still marks these two nodes completed without running them, on `main` too. That is a separate finding.

Back `main` also holds #2057 and #2058 (868m7d6hv), so the back deploy from `main` ships them too.

## Why the flag waits

While `worker_input_resolution` is off, a shadow mismatch costs nothing: the node runs with the back's input. Once the flag is on, the same mismatch becomes a node that runs with the wrong input. The schedule changed on 2026-10-22: the deploy moved to Monday 2026-10-26, in one release with E1 before 11:00. Tuesday and Wednesday are full business days of shadow proof. On 2026-10-29 the plan changed again after one mismatch: see the sections from Wednesday on.

## How to run the queries

- Every query is read-only and one statement. Run it with Alt+X, or select the whole statement before Ctrl+Enter.
- Every file was run as-is on dev before its prod run (the first ones on 2026-10-21, the `q7b` to `q7e` and `q4-1t` files on 2026-10-28 and 2026-10-29).
- Save each output as `<query>.prod.csv`, or keep it local if it holds customer data.

## Monday 2026-10-26, before 11:00: deploy with E1

The deploy is one release with E1: each repo's prod workflow on `main`, worker first. The steps are in `wave4-prod-checks-runbook.md`, steps 2 and 3.

1. Before the deploy, run [`b1-q3-node-executions-size.sql`](b1-q3-node-executions-size.sql).
   - If `dup_pairs_since_release` is not `0`, stop: the migration would fail at boot.
   - If `total_size` is above a few GB, stop and ask: the index build would block writes too long. Prod on 2026-10-22: 1131 MB in total, 0 duplicate pairs. Dev: 26 MB, 340 ms.
2. Deploy, worker first. Write down the back deploy time (UTC).
3. 30 to 60 minutes after the back deploy, run [`b1-q4-unique-index-after-deploy.sql`](b1-q4-unique-index-after-deploy.sql).
   - Pass: `unique_index_present = 1`, `migration_rows = 1`, `dup_pairs_after_release = 0`, `duplicate_key_errors = 0`, and `worker_input_resolution=false` in `flags`.
   - Also search Datadog for `UQ_NODE_EXECUTIONS_EXEC_NODE`. Expect no hits.
4. Run [`b3b-q7-shadow-by-hour.sql`](b3b-q7-shadow-by-hour.sql). Its `params` line already has `fix_day` 2026-10-26.
   - Pass: from the first full hour after the deploy, `mismatched = 0` and `prev_bad_mismatched = 0`.
   - The hours before the deploy still show the old mismatches; that is expected.
   - If the deploy is not on 2026-10-26, change only the date in the `params` line.

Rollback: a duplicate key error that fails a customer run. Revert #2054 on its own.

## Wednesday 2026-10-28 and Thursday 2026-10-29: the decision (done)

The rule above (no hour with `mismatched` above `0`) did not hold, so the flag stayed off on Thursday and the one mismatch was traced.

[`b3b-q7-shadow-by-hour.sql`](b3b-q7-shadow-by-hour.sql), run on 2026-10-29:

- The shadow has been on since 2026-10-21 13:54 UTC (`feature_flags.updatedAt` of `worker_input_resolution_shadow`).
- From 2026-10-26 14:00 to 2026-10-29 13:00 UTC: 8,812 comparisons, 8,811 matched, 1 mismatch at 2026-10-27 12:00 UTC, 0 shadow errors.
- The nodes that mismatched before the fix ran 269 times since, and all matched (`prev_bad_mismatched` 0).
- In the 26 h before the fix, 85 of 841 comparisons mismatched.

The mismatch, traced with [`b3b-q7b-mismatch-detail.sql`](b3b-q7b-mismatch-detail.sql) and [`b3b-q7c-mismatch-cause.sql`](b3b-q7c-mismatch-cause.sql):

- A `commandTextNode` in a customer flow (`d00e44a0`) has an execution edge to itself (`outputFlow -> input`).
- The back sent `Data` = [the node's own stored output from an earlier run (353 characters), the starter entry].
- The divergent paths are `Data[0].id`, `Data[0].label`, `Data[0].text` and `Data[1]`, so the worker built `[starter entry]` only. The worker reads upstream outputs of the current run, and the node has no output in this run yet. This is inferred from the paths: in shadow mode the worker stores the outcome, not its value.
- No edge into the node changed within 10 minutes of the run, and no other run of the node started within 2 minutes, so neither an edit nor concurrency explains it.
- It is not the starter case that 868mktvma fixed: the starter entry is present on both sides.

How many nodes this affects, from [`b3b-q7d-self-loop-nodes.sql`](b3b-q7d-self-loop-nodes.sql):

- Prod has 32 nodes with an edge to themselves. 2 ran in the last 30 days.
- This node ran 4 times in 30 days, about once a week. It is the only one whose input changes.
- The other one, a `scripting` node with `console -> func...` (30 runs), matched 8 of 8 comparisons.

Decision: no rollout on Thursday. A 1 h trial on Friday, a decision on the self-loop behavior on Monday, and the rollout on Tuesday.

## What the shadow cannot see once the flag is on

The back reads the flags once when a run starts and opens the run with `shadow: !apply`. With `worker_input_resolution` on, the worker's input becomes the input the node runs with, and nothing compares it with the back's input. A trial with the flag on adds no mismatch data. It measures what only the flag shows: node errors, `Edge projection:` errors and snapshots left behind.

- A toggle takes effect in about 5 s (the flag cache TTL), for runs that start after it. A run already going keeps its mode until it ends.
- Every run deletes its snapshots in a `finally` block, in both modes. `b3b-q3` finds the runs that ended without that cleanup.
- Rollback: turn off only `worker_input_resolution`. The shadow compares again from the next run.

## Friday 2026-10-30: 1 h trial

1. [`b3b-q3-leftover-snapshots.sql`](b3b-q3-leftover-snapshots.sql) before the flag: no rows (no leftovers, no run in progress).
2. Flag on at about 13:17 UTC and off at about 14:16 UTC. The first row the worker resolved is from 13:17:14 UTC and the last from 14:28:15 UTC: a run that started with the flag on keeps that mode until it ends.
3. Log watch on `/ecs/worker-task-definition-prod` and `/ecs/api-task-definition-prod` from 13:17 UTC: 0 `Edge projection` lines and no resolution error while the flag was on. The 24 h before the trial had 0 of each too.
4. 30 min after the flag went off, all pass:
    - `b3b-q3`: 3 snapshots, all `active run (expected)`, no `leftover`.
    - [`b3b-q4-1t-trial-error-rate.sql`](b3b-q4-1t-trial-error-rate.sql): 1,213 node rows resolved by the worker, 33 errors (2.72%). The 24 h before had 4,721 shadow rows with 145 errors (3.07%). No node type is clearly above its baseline: `apiCaller` 8.33% against 10.60%, `scripting` 1.42% against 1.15% (9 of 636), `commandTextNode` 2.68% against 3.54%, every other type 0 errors.
    - [`b3b-q4-2-edge-projection-errors.sql`](b3b-q4-2-edge-projection-errors.sql): no `Edge projection:` error since the shadow went on.

**Open point: the switch back to shadow.** At 14:25:55 and 14:25:56 UTC, with the flag off, the worker logged two shadow errors on `commandTextNode` nodes: `was dispatched in shadow mode without its unresolved input`. The shadow could not compare those two nodes.

What the code shows (read at back and worker `main`, 2026-10-30):

- The flag change is not the cause. For one dispatch, the back decides shadow and stores `raw` from the same `RunInputResolution` object, opened once per `apiV2` call. A run opened before the switch keeps apply mode until it ends, which explains apply rows until 14:28:15.
- The error means `raw` was removed after the back wrote it and before the worker read it. Only `releaseRunInputResolution`, called in the `finally` block of `apiV2`, removes it during a run. So the `apiV2` that owned the run ended before the node's activity read its row.
- Customer impact: none. In shadow mode, the error is caught and the node runs with the back's input.
- With the flag on, the same race fails the node with the resolution user message, after 3 attempts.

What the data shows, from [`b3b-q4-3-switch-back-shadow-errors.sql`](b3b-q4-3-switch-back-shadow-errors.sql): no double dispatch. Each exec has one run and one `commandTextNode` row, created at 14:25:33 UTC, with no duplicate. Both rows are cancelled, and neither is an error. So a cancel ended the `apiV2` call, its `finally` block removed `raw`, and the activity read the row 22 s later (inferred from the timing; the cancel path is not read in code yet).

Autoscaling started a second back task at 14:23:33 UTC, ready at 14:25:15. With the cancel explaining the errors, the new task is likely a coincidence.

With the flag on, a cancelled node would fail resolution instead, inside a run that is already cancelled. [`b3b-q4-4-cancelled-node-input-resolution.sql`](b3b-q4-4-cancelled-node-input-resolution.sql) counts, per day since the shadow went on, the cancelled nodes, how many lost `raw` in shadow, and how many were marked as errors with the flag on. On dev, where the flag is on, 31 cancelled nodes were resolved by the worker with 0 errors.

`b3b-q4-1t` marks the trial rows by `metadata.inputResolution.resolvedAt`, which the worker writes only in apply mode. `b3b-q4-1` reads the flag `updatedAt`, so it only fits a single on switch with no off after it.

## Monday 2026-11-02: decide the self-loop behavior

Choose one before the node's next run, likely Tuesday 2026-11-03 12:00 UTC:

1. Accept the change. The node stops receiving its own output from an earlier run, which is state leaking between runs.
2. Keep the old behavior in the worker for self-loop edges, then run the shadow again before the flag.

## Tuesday 2026-11-03: flag on for good

Only if the Friday trial passed and Monday chose option 1.

1. Before 12:00 UTC: turn on `worker_input_resolution`. Write down the time (UTC).
2. Watch the logs for 1 h, as on Friday.
3. 30 to 60 min later: [`b3b-q3-leftover-snapshots.sql`](b3b-q3-leftover-snapshots.sql). Pass: no `leftover` rows.
4. After 12:00 UTC: [`b3b-q7e-self-loop-node-runs.sql`](b3b-q7e-self-loop-node-runs.sql). Pass: the run after step 1 has `resolved_by_worker` true, `is_error` false, `data_len` 1 and `data0_is_self` false.

## Wednesday 2026-11-04: 24 h check

1. [`b3b-q4-1-error-rate.sql`](b3b-q4-1-error-rate.sql). Pass: `after_resolved_by_worker` above `0`, and `after_error_pct` not clearly above `before_error_pct`.
2. [`b3b-q4-2-edge-projection-errors.sql`](b3b-q4-2-edge-projection-errors.sql). Pass: no growth on 2026-11-03 and 2026-11-04.

With both passing, 868mfkzgh (B3B) and 868mktvma can close, and the 14-day window for `worker_input_resolution` starts, counted from the Tuesday on time (earliest end 2026-11-17).
