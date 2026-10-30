# 868mktvma rollout: deploy, then `worker_input_resolution`

Task: [868mktvma](https://app.clickup.com/t/868mktvma). PRs: back [#2054](https://github.com/enhancedai-com/Flux-Prompt/pull/2054), worker [#139](https://github.com/enhancedai-com/Flux-Prompt-Worker/pull/139), both merged into `main`.

The deploy ships three changes:

- **B3B fix (worker):** the worker keeps the starter's `Data` entry. This removes the prod nodes that mismatched on every run (77 on 2026-10-22, see `b3b-q6`), and it is what blocks `worker_input_resolution`.
- **Unique index (back):** `UQ_NODE_EXECUTIONS_EXEC_NODE` on `node_executions ("execId", "nodeId")` for rows created after the B1 release. The migration runs at boot and blocks writes to `node_executions` while it builds.
- **SEC and Census gate (back and worker):** both nodes ask the node credit gate. This applies only while `node_credit_gate` is on, and only in single-node runs. In a flow run, the back still marks these two nodes completed without running them, on `main` too. That is a separate finding.

Back `main` also holds #2057 and #2058 (868m7d6hv), so the back deploy from `main` ships them too.

## Why the flag waits

While `worker_input_resolution` is off, a shadow mismatch costs nothing: the node runs with the back's input. Once the flag is on, the same mismatch becomes a node that runs with the wrong input. The schedule changed on 2026-10-22: the deploy moved to Monday 2026-10-26, in one release with E1 before 11:00. Tuesday and Wednesday are full business days of shadow proof. The flag goes on Thursday morning so someone watches the first hour.

## How to run the queries

- Every query is read-only and one statement. Run it with Alt+X, or select the whole statement before Ctrl+Enter.
- Every file was run as-is on dev on 2026-10-21.
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

## Wednesday 2026-10-28, end of day: decide the flag

Run [`b3b-q7-shadow-by-hour.sql`](b3b-q7-shadow-by-hour.sql) again.

Turn the flag on Thursday only when every hour after the deploy has:

1. `mismatched = 0` and `shadow_errors = 0`.
2. `prev_bad_mismatched = 0`.
3. And Tuesday's and Wednesday's hours show `prev_bad_matched` above `0`.

If any hour has `mismatched` above `0`, keep the flag off and open a look at that node.

## Thursday 2026-10-29, morning: turn the flag on

1. Turn on `worker_input_resolution`. Write down the time. Do not change `node_credit_gate` on the same day. It has been on since 2026-10-23 and was checked on Monday (`wave4-prod-checks-runbook.md`).
2. Watch the worker logs for `Edge projection:` errors for 30 to 60 minutes.
3. Run [`b3b-q3-leftover-snapshots.sql`](b3b-q3-leftover-snapshots.sql). Pass: no `leftover` rows, or only a few that are gone on a second run.

Rollback: an `Edge projection:` or input resolution error in the first hour, or a customer report of a node with empty or wrong input. Turn off only this flag; the shadow keeps comparing.

## Friday 2026-10-30: 24 h check

1. Run [`b3b-q4-1-error-rate.sql`](b3b-q4-1-error-rate.sql). Pass: `after_resolved_by_worker` above `0`, and `after_error_pct` not clearly above `before_error_pct`.
2. Run [`b3b-q4-2-edge-projection-errors.sql`](b3b-q4-2-edge-projection-errors.sql). Pass: no growth on 2026-10-29 and 2026-10-30.

With both passing, 868mfkzgh (B3B) and 868mktvma can close.
