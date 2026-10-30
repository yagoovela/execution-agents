# Wave 4 prod checks: E1 deploy, B3B cause, node credit gate

This runbook covers the prod checks outside the 868mktvma rollout. The rollout itself (Monday 2026-10-26 to Friday 2026-10-30) is in [b3b-flag-rollout-runbook.md](b3b-flag-rollout-runbook.md). ClickUp epic: [868mkvtcm](https://app.clickup.com/t/868mkvtcm).

Every query is read-only and one result set. Run it in DBeaver as a script (Alt+X), and save the CSV under the name the file gives.

## Rules for the week

The schedule changed on 2026-10-22: the E1 and 868mktvma deploys moved from Thursday to Monday, and `node_credit_gate` moved from Monday to Friday. On 2026-10-23 the two Monday deploys became one: E1 and 868mktvma ship together from `main` before 11:00.

- Thursday 2026-10-22: pre-checks only.
- Friday 2026-10-23: `node_credit_gate` on.
- Monday 2026-10-26: the gate check at 09:00, then one deploy from `main` before 11:00. The checks after the deploy stay separate: `b1-q2i` checks E1, and `b1-q4` and `b3b-q7` check 868mktvma, so a failed check still points at one change.
- Thursday 2026-10-29: `worker_input_resolution`, if Wednesday's check is a go.
- `e1-q1-charge-key.sql` and `b1-q3-node-executions-size.sql` run right before the deploy. Either one stops the deploy.

## Thursday 2026-10-22: pre-checks (done)

1. [e1-q5-loop-sizes-from-node-rows.sql](e1-q5-loop-sizes-from-node-rows.sql): PASS. 121 loops in 9 flows; p50 1, p95 3, max 4 items; `control_b1_arr_items = 3`.
2. [b3b-q6-starter-data-shape.sql](b3b-q6-starter-data-shape.sql) ([868mfkzgh](https://app.clickup.com/t/868mfkzgh)): PASS. All 77 mismatched nodes have `data0_is_starter = true`, `starter_edges = 1` and `inbound_edges >= 2`, the cause the worker fix in 868mktvma covers.
3. [e1-q1-charge-key.sql](e1-q1-charge-key.sql): 0 duplicate triples in 528,042. Baseline; it runs again right before the Monday deploy.
4. [b1-q3-node-executions-size.sql](b1-q3-node-executions-size.sql): 0 duplicate pairs. Baseline; it runs again right before the Monday deploy.
5. `scripts/check-no-dev-in-prod-pr.sh` on worker and back: clean. E1 (worker #137, back #2052) and 868mktvma (worker #139, back #2054) are merged into `main` and not deployed.

## Friday 2026-10-23: turn on `node_credit_gate` (done)

Task: [868mkvu2c](https://app.clickup.com/t/868mkvu2c), validates [868mf2v73](https://app.clickup.com/t/868mf2v73). The 2026-10-21 run of [b1-t7-checks.sql](b1-t7-checks.sql) is the "before" picture (G1 to G3).

1. `node_credit_gate` went on at 12:40 UTC. `node_credit_gate_no_plan` stays off; it waits on the product decision in 868mebgw7.
2. One hour later, the CloudWatch check replaced the Datadog export: [gate-refusals-cloudwatch.sh](gate-refusals-cloudwatch.sh) reads the worker log and the API log. It covers every gated node: all 9 gated node types run on the worker in a flow, and the only other caller, the legacy single-node run, logs to the API log.
3. Result: 1 refusal from 12:40 to 14:15 UTC, `model_not_in_plan` on a `gemini-3-flash-preview` node. [gate-q1-model-not-in-plan.sql](gate-q1-model-not-in-plan.sql) showed the billing owner on the Intro plan, with `gemini = false`. [gate-q2-refused-node-history.sql](gate-q2-refused-node-history.sql) showed the node never charged before. Correctly refused, not rolled back.

How the gate decides `model_not_in_plan`: it filters the billing owner's active plan by the provider flag of the node model (`anthropic`, `gemini`, `perplexity`, `stability_ai`, `ideogram`, `replicate_ai` on `products`). The charge endpoint uses the same filter. Intro and Starter do not include Gemini (868mebgw7 Test Case 8). Whether they should is a product decision ([868mh19pw](https://app.clickup.com/t/868mh19pw) item 4).

Rollback: a refusal that the plan does not explain (the provider flag is `true` on an active plan), a refusal for an account that still has credit or plan room, or a customer report. Turn off only `node_credit_gate`. It takes effect in about 5 seconds.

## Monday 2026-10-26, 09:00: gate check, before the deploy

### 1. `node_credit_gate` check since Friday ([868mkvu45](https://app.clickup.com/t/868mkvu45))

1. Run [b1-t8-checks.sql](b1-t8-checks.sql).
   - Pass: G1 shows `node_credit_gate` on and `node_credit_gate_no_plan` off. G2 lists refusals per code. G3 `gate_rows` match G2, and the other `user_config` rows stay within 69 to 198 per day (weekend days can be lower).
2. Run [gate-refusals-cloudwatch.sh](gate-refusals-cloudwatch.sh) (read-only).
   - Pass: the control line is above 0, and every refusal listed is explained with [gate-q1-model-not-in-plan.sql](gate-q1-model-not-in-plan.sql) (set the flow and node ids in its `WHERE` lines): the provider flag is `false` on every active plan.
3. Optional: Datadog `service:EnhancedAILogging "node_credit_gate refused"` (production `env`) since Friday 12:40 UTC.

With both passing, 868mf2v73 can close. If a refusal is not explained, turn off only `node_credit_gate` before you start the deploy.

Result on 2026-10-26 (done, PASS; 868mkvu45 and 868mf2v73 closed):

- [b1-t8-checks.prod.csv](b1-t8-checks.prod.csv): G1 `node_credit_gate` on (`updatedAt` 2026-10-23 13:46 UTC) and `node_credit_gate_no_plan` off. G2 one refusal, `model_not_in_plan`, 2026-10-23 14:13 UTC. G3 `gate_rows` 1 on 2026-10-23 and 0 on the other days; other `user_config` rows 98, 92 and 89 from Friday to Sunday.
- [gate-refusals-cloudwatch.prod.txt](gate-refusals-cloudwatch.prod.txt): the same single refusal, 0 legacy single-node failures, control 408. The refusal is the Friday one, already explained (Intro plan, `gemini = false`).

## Monday 2026-10-26, before 11:00: one deploy, E1 and 868mktvma ([868mkvu58](https://app.clickup.com/t/868mkvu58))

The deploy runs each repo's prod workflow on `main`. Prod back is at `f60767be` (2026-10-21) and prod worker at `348ca1f` (2026-10-15), so it ships:

- E1: worker [#137](https://github.com/enhancedai-com/Flux-Prompt-Worker/pull/137) and back [#2052](https://github.com/enhancedai-com/Flux-Prompt/pull/2052) (tasks [868m0vn4x](https://app.clickup.com/t/868m0vn4x), [868mk5yj4](https://app.clickup.com/t/868mk5yj4)). Back #2052 also carries 868mkv67z and 868mkp63f.
- 868mktvma: worker [#139](https://github.com/enhancedai-com/Flux-Prompt-Worker/pull/139) and back [#2054](https://github.com/enhancedai-com/Flux-Prompt/pull/2054).
- Back #2057/#2058 (868m7d6hv), worker #135 (868m6uck1, Cloudflare models), worker #133 and a dependency update.
- Back [#2060](https://github.com/enhancedai-com/Flux-Prompt/pull/2060) (B4, [868m0vn26](https://app.clickup.com/t/868m0vn26)), merged on 2026-10-23 after this plan was written. Back `main` moved from `2f5dfb97` to `a38fef57`; worker `main` stays at `748d8dc`. B4 is inert: it routes a run through the `processFlow` workflow only while the `engine_in_workflow` flag is on, and its migration seeds the flag as `false`. It adds 3 cheap migrations: a nullable `flow_execution_status.run_workflow_id` column, the `run_seeds` table, and the flag row.
- **Planned, pending a PR (2026-10-23).** The `sqlQuerier` fix on back `feat/sql-node`
  (`196df420`) is assumed to ship in this deploy. It has no PR and is 63 commits behind `main`. If
  it is not merged before the deploy, it waits for the next one. When it ships, add a post-deploy
  check that a full run with a `sqlQuerier` node reaches the worker.

### 2. Before the deploy

1. Run [e1-q1-charge-key.sql](e1-q1-charge-key.sql).
   - Pass: `duplicate_triples = 0`.
2. Run [b1-q3-node-executions-size.sql](b1-q3-node-executions-size.sql).
   - Pass: `dup_pairs_since_release = 0`, and `total_size` is not above a few GB (1131 MB on 2026-10-22). The unique index migration builds at boot and blocks writes to `node_executions` while it builds.
3. Run [e1-q7-token-transaction-size.sql](e1-q7-token-transaction-size.sql).
   - Pass: `heap_size` is not above 3 GB. The E1 boot migration builds `UQ_token_transaction_exec_node_api` without `CONCURRENTLY`, so `token_transaction` stays write-locked while it builds, about 8 to 9 seconds per GB measured on dev.
4. Information only: run [e1-q6-loop-audio-source.sql](e1-q6-loop-audio-source.sql). `reads_array_file_before_e1` counts live audio nodes, fed by an `arrayNode`, whose transcript source changes with E1.

If check 1, 2 or 3 fails, do not deploy.

Result on 2026-10-26 (done, PASS):

- [e1-q1-charge-key.prod.csv](e1-q1-charge-key.prod.csv): 586,803 triples, `duplicate_triples = 0`.
- [b1-q3-node-executions-size.prod.csv](b1-q3-node-executions-size.prod.csv): `dup_pairs_since_release = 0`, `total_size` 1162 MB.
- [e1-q7-token-transaction-size.prod.csv](e1-q7-token-transaction-size.prod.csv): `heap_size` 1023 MB, `total_size` 1201 MB, 586,809 keyed rows. Expected write lock: about 9 seconds.
- [e1-q6-loop-audio-source.prod.csv](e1-q6-loop-audio-source.prod.csv): 5 loop audio nodes in 4 flows; 1 node in 1 flow reads the `arrayNode` file before E1.

### 3. Deploy from `main`, worker first

1. Run the worker prod workflow (`workflow_dispatch`) on `main`. Prod back runs `audioReaderNode` inline today, so the new worker stays unused for audio until the back ships.
2. A few minutes later, run the back prod workflow on `main`. Back first would send audio to the old worker, which has no ffmpeg and no `/worker/charge-transcription`.
3. Write down both times (UTC). Leave both run-log flags off: `run_log_events_shadow` and `run_log_from_events`.

### 4. After the deploy: E1

1. Run the prod agent "B1 loop billing check (868mdkh7y)" (`01d5f0bc-ef20-476a-94c7-80e80b713e55`, workspace Enhanced Ai, folder `tasks`). Write down the run's start time (UTC).
2. Run [b1-q2i-controlled-run.sql](b1-q2i-controlled-run.sql) with the `createdAt` lower bound changed to that start time.
   - Pass: `b1-cmd` shows `charges = 3` and `roots = 1`.
   - `b1-aud` has no row. This is expected after E1: before E1, the loop transcribed the file of the `arrayNode`, and since E1 the audio node reads its own file, which `b1-aud` does not have. Do not open a bug for it.
3. The docs PR [docs#56](https://github.com/enhancedai-com/docs/pull/56) is already merged (2026-10-22). Once E1 is live, check that the docs site matches it.

### 5. After the deploy: 868mktvma ([868mkvnqw](https://app.clickup.com/t/868mkvnqw))

Run the checks in [b3b-flag-rollout-runbook.md](b3b-flag-rollout-runbook.md), Monday section, steps 3 and 4.

### 6. After the deploy: B4 stays inert

1. Run [b4-q1-engine-flag-after-deploy.sql](b4-q1-engine-flag-after-deploy.sql) after the back deploy.
   - Pass: `engine_in_workflow_enabled = false`, `b4_migrations = 3`, `run_workflow_id_column = 1`, `run_seeds_table = 1`.
2. Keep `engine_in_workflow` off. Worker B4 (`processFlow`) is not on worker `main`, so turning the flag on would start a workflow the prod worker does not have.

Do not turn on any flag on Monday.

### Later: the run-log flags (not this week)

The rebuild debounce and the S3 reads before the lock ship in back #2052. To move run logs to events:

1. Turn on `run_log_events_shadow`. Wait a few days.
2. Turn on `run_log_from_events` only when the API logs show no `Run log shadow: ... differences` lines.

Rollback: turn the flag off.
