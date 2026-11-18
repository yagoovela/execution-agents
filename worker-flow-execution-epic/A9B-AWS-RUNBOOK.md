# A9b — validate on AWS dev before the merge to `main`

This runbook checks on the dev environment what the local stack checked (see **Implementation record**
in [TASK-A9B-STALLED-API-RUN-ONE-OUTCOME.md](TASK-A9B-STALLED-API-RUN-ONE-OUTCOME.md)): a back or
worker deploy in the middle of async API runs ends each run with one status, at most one callback and
a recorded cost equal to its charges.

It runs on dev only. Each AWS write is listed with the person who runs it.

## Before you start

Facts read on 2026-11-16 with a read-only profile:

| Item | Dev | Staging | Production |
|---|---|---|---|
| Back start command | Task definition overrides it: `sh -c "node dist/seed.js \|\| echo Seed skipped; node --max-old-space-size=6500 dist/main.js"` (added by hand on 2026-05-22, revision 2128) | Image `ENTRYPOINT`, runs `dev.sh` | `sh -c "sed … dev.sh && . ./dev.sh"`, runs `dev.sh` |
| Back `stopTimeout` / `initProcessEnabled` | unset (30 s) / unset | unset / unset | unset / unset |
| Back tasks | 1 | 1 | 1 |
| Target group deregistration delay | 300 s | — | — |
| `AUTH_JWT_SECRET` | set | **missing** | set |
| `NODE_MAX_OLD_SPACE_SIZE` | unset (`dev.sh` default 6500) | unset | 16384 |
| Worker start command | `node dist/main.js` (PID 1) | same | same |
| Worker `stopTimeout` | unset (30 s) | unset | unset |

With the dev override, `node` is a child of `sh`, which is PID 1 and does not forward SIGTERM, so ECS
kills the back 30 s after SIGTERM (checked on the branch image: exit 137). Part 1 of A9b cannot
work on dev until the override is removed.

Constraints:

- GitHub Actions minutes are limited. Use one merge to `develop` for the build; trigger every later
  deploy with `aws ecs update-service --force-new-deployment`, which uses no minutes.
- `engine_in_workflow` is one flag for all of dev. Turn it on only inside the test window and tell the
  team.
- The MCP dev service stops at 20:00 every day; run T5 before that.
- Freeze other dev deploys during the window: a deploy from another branch replaces the image under
  test.
- With two back tasks, a cron that takes no lock runs in both. Before step 2, list the back crons and
  confirm each takes a lock or is safe to run twice on dev.

## Step 0 — prepare dev (AWS writes, run by a person with write access)

The image on dev today runs the old `dev.sh` (`node` in the background, then `wait`). With
`initProcessEnabled` on that image, the init process sends SIGTERM to the shell, which exits at once
and kills the runs in flight. So the branch image goes to dev first, and the task definition changes
after it.

1. Merge `fix/868mvdm50` (back, then worker) into `develop` with the user's permission, and wait until
   each service has one deployment `COMPLETED` (the GitHub job turning green is not enough). The dev
   deploy keeps the live task definition and changes only its image.
2. Register a new revision of `api-task-definition-dev` from the live one, with:
   - `entryPoint` and `command` removed, so the image `ENTRYPOINT` runs `dev.sh`;
   - `stopTimeout: 120`;
   - `linuxParameters.initProcessEnabled: true` (it reaps the finished seed shell; since back
     `858685ce` the back exits with 0 without it too).

   Checked on 2026-11-16 against revision 2674: nothing else changes (image, 22 environment
   variables, 173 secrets, CPU, memory, roles, logging).
3. Point `api-service-dev` at it and set `desiredCount: 2`.
4. Set `worker-task-definition-dev-service` to `desiredCount: 2`.

After step 2 the dev back starts the app before the seed, and the seed runs in the background once
`/health` answers; before, the seed ran first and delayed `/health`.

## Tools

Everything below is a script; one Claude Code session can run the observers as monitors. Read-only
scripts use the read-only profile; write scripts use the profile the operator exports.

| Script | Does | Access |
|---|---|---|
| `taskdef.sh apply\|status\|--dry-run` | Renders the step 0 revision from the live one, shows the diff, registers it and updates the service; reuses `scripts/deploy-direct/lib/ecs.sh` (`render_taskdef`, `register_revision`, `update_service`, `ecs_wait`) | write (operator) |
| `deploy.sh back\|worker` | `--force-new-deployment` on one service and prints the old and new task ids | write (operator) |
| `swap-watch.sh` | For each task stopped during the window: revision, `startedAt`, `stoppingAt`, `stoppedAt`, `stoppedReason`, container exit code (0 = clean, 137 = killed), and the shutdown lines in its log stream (`Paused N queue instances`, `apiV2 shutdown: …`) | read-only |
| `receiver` | A local HTTP server behind an ngrok URL: logs each callback by run, and serves `/delay?s=N` for the long flows | local |
| `drive.sh T<n>` | Starts the runs of one test against the dev API with a test user's API key and records their ids | dev API |
| `observe.sh` | Per run: status and error text (`flow_execution_status`, `mcp_run_status`), `end_delivery` left behind, flow log count, recorded cost against the credit ledger, callbacks received; prints one PASS/FAIL line per run | read-only (dev DB, CloudWatch) |
| `report.sh` | Joins the swap and run tables into one report | local |

Building them takes about 3 to 5 h. Running T1–T8 takes about half a day.

## Test flows on dev

Create them under a test user; none holds customer data.

- **Short:** `globalStarter` → `mathFunction` → Data Output (about 3 s).
- **Long 60 s / long 150 s:** `globalStarter` → `apiCaller` (GET `<receiver>/delay?s=60` or `s=150`) →
  Data Output. The `apiCaller` activity allows 5 min.
- **Batch:** a three-row CSV for the long 60 s flow; row 2 makes the call fail.

## Tests

Every test passes only when each of its runs has exactly one terminal status, at most one callback,
no `end_delivery` left after 10 min, and, 35 min after its end, a recorded cost equal to its ledger
charges.

| # | Setup | Action | Also passes when |
|---|---|---|---|
| T1 | Flag off; one long 60 s run on back task X | Deploy the back | X logs the pause and one waiting run, the run completes, X exits with code 0 |
| T2 | Flag off; one long 150 s run on X | Deploy the back | X closes its queue with one run still running and exits with code 0; the other task writes `error` with the "server restarted" message and sends one callback |
| T3 | Flag on; one long 60 s run on X | Deploy the back | X exits with code 0 within seconds; the run ends `completed` with one callback (through `owned` and then the stall path, or the orphaned finish) |
| T4 | Flag on; ten long 60 s runs over two workers | Deploy the worker | Measures A9c: count runs that end `error` because an activity was cut at 30 s; each run still has one status and one callback |
| T5 | MCP run of the long 60 s flow | Deploy the back | One `mcp_run_status` end, no callback |
| T6 | The batch | Deploy the worker during row 2 | Row 2 ends `error`, its run is finished, the batch reaches a terminal status |
| T7 | Reaper flag on; on the dev DB, one test run moved back to `pending` 25 h ago and one to `in_progress` past the ceiling plus 30 min | Wait one cron tick (every 10 min) | Each row is closed once, with `RUN_NOT_STARTED_MESSAGE` and `RUN_CEILING_MESSAGE`; no second close on the next tick |
| T8 | — | Read the heap sizes of `flow_execution_status` and `mcp_run_status` in production from `pg_stat_user_tables` (catalog only, no scan); the migration's duration in the dev deploy log is a lower bound | TypeORM runs all pending migrations in one transaction, so the three tables keep an `ACCESS EXCLUSIVE` lock until the last index is built. Worst case on gp2 without burst: (sum of the two heaps) / 37 MB/s. Under 30 s: deploy at any time; 30 s to 2 min: a low-traffic window; over 2 min: build the indexes `CONCURRENTLY` in a migration of its own first. Local reference: 1 M rows, 651 MB heap, 0.4 s per index with a warm cache |

Also check, for every deploy, that no task stopped with exit code 137.

## After the tests

1. Turn `engine_in_workflow` and `unfinished_run_reaper` back off on dev.
2. Set both dev services back to one task.
3. Keep the step 0 task definition; it is what dev should have run since 2026-06-16.
4. Record the results in **Implementation record** of the spec.
