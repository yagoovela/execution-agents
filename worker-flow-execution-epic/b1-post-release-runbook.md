# B1 — what to run after the production release (draft)

Draft 2026-10-06. B1 ships as one release: back PR #2031, worker PR #121, front PR #2218, plus this spec
(Workflow PR #23). It changes billing identity, concurrent charges, renewal, voice cloning, reports and
plan and space limits, so several checks only make sense once it is in production. Queries are
read-only: the R-series is in [`b1-post-release-queries.sql`](b1-post-release-queries.sql), and Q1c, Q2d,
Q2e, Q2f and Q7 are in [`b1-q2-prod-measurements.sql`](b1-q2-prod-measurements.sql). The user runs prod
queries; nobody here queries prod. Every query has run on dev.

## Before merging the prod PRs

| # | What | Why | Status |
|---|---|---|---|
| B-1 | `scripts/check-no-dev-in-prod-pr.sh` on the back, front and worker branches | No dev content in a prod PR | OK on 2026-10-06 (back 15 commits, front 2, docs 14); worker to run before merging #121 |
| B-2 | Re-run P1 (spaces the gate refuses) on the day | Nobody is blocked by the space limit on deploy | 0 on 2026-10-06 |
| B-3 | D1: check `customer-a@example.com` and `customer-b@example.com` in Stripe | 2 non-internal unlimited accounts: is their renewal skipped on purpose? | Open (product) |
| B-4 | Re-run P5 (Q7 drift) with every column | The 2026-10-06 export lost 3 columns | Open |
| B-5 | P10 (web-search unit, `b1-q1-web-search-unit.sql`) | Addendum B baseline | Open |
| B-6 | Merge order: worker #121 and back #2031 together, front #2218 right after | The worker and the back share the per-execution id; the front only needs the 402 bodies | — |
| B-7 | Write down the deploy time of back #2031 (UTC) | `:release` in every query below and in the partial unique index | Done: `2026-10-14 13:19:22+00`, already filled in both SQL files |

## Release day (T0)

| # | What | Expected |
|---|---|---|
| T0-1 | App: create an agent at the plan limit on a test account | Plan-limit dialog, not "Something went wrong" |
| T0-2 | MCP `create_agent` at the limit (test account) | "You have used all N agents your … plan includes." |
| T0-3 | `POST /integrations/agents` with an API key at the limit | 402 `flow_limit_reached` |
| T0-3b | `POST /flux/api-v2` with an API key on an agent whose space is over its limit (test space, limit restored after) | 402 `space_limit_reached` at once, no `flow_execution_status` row |
| T0-4 | R5 (accounts above their plan limit) | Baseline to compare on T+7 |
| T0-5 | Restore every test account | Row matches its snapshot |

## The morning after each nightly renewal (T+1, and on Oct 25, Oct 26 and Nov 1)

| # | What | Expected |
|---|---|---|
| D-1 | R1: overdue paid accounts | Only `unlimited_plan = true` rows; a paying account stuck overdue means the renewal stopped |
| D-2 | R2: accounts deactivated since `:release` | Each one has a failed Stripe charge |
| D-3 | R3: cloned-voice cron ledger rows | One `charge-total-cloned-voices` row per charged account per day (none since 2025-12 before) |
| D-4 | Oct 25 / Oct 26 / Nov 1: the 3 unlimited accounts in P2 | Skipped (no charge, no deactivation); every other account due that night renewed |

## Once, one week after the release (T+7)

| # | What | Expected | Gate |
|---|---|---|---|
| W-1 | Q1c: duplicate `(execId, nodeId)` among rows written after `:release` | 0 | Q1c counts every row since `:release`, so one run at 0 on T+7 covers all seven days and unlocks the partial unique index |

## One week after (T+7, follow-up 868mdkh7y)

| # | What | Expected |
|---|---|---|
| W7-1 | Q2f: charges whose id has no `node_executions` row, grouped by run | `max_charges_per_run_node > 1` in loops: each iteration is now charged (approved change) |
| W7-2 | Q2d / Q2e vs the 2026-10-06 baselines (P3, P4) | Run-level charge rows for inline node kinds trend to zero; credits per charge in the same range |
| W7-3 | Total charge volume per week vs the previous 4 weeks | In line with past weeks, apart from the loop increase |
| W7-4 | R4: duplicate report rows that grew after `:release` | 0 |
| W7-5 | R5 vs T0-4 | No growth |
| W7-6 | Space limit refusals: grep the back logs for `space_limit_reached` | Only spaces whose admin set a limit |

## After the first full billing cycle (about T+30)

| # | What | Expected |
|---|---|---|
| M-1 | R6: counter vs ledger drift for cycles that started after `:release` | `accounts_with_drift = 0` |
| M-2 | P5 / Q7 again | Drift only in cycles that started before the release, and shrinking |

## Code that waits for the gates

| # | What | When |
|---|---|---|
| G-1 | Partial unique index `UNIQUE("execId","nodeId") WHERE "createdAt" >= :release`, via `pnpm migration:generate` (back) | After W-1 reads 0 on T+7; if not, find and fix the writer first |
| G-2 | 868mebgw7 P2, P3, P5–P8 | Each refusing item ships only after its measurement (below) shows no false refusal |

## Measurements 868mebgw7 still needs (before each item ships)

| Item | Measurement | Source |
|---|---|---|
| P2 | Users without a plan who ran agents in the last 30 days, and their `trialTokens` | `node_executions` / `flow_logs` joined to users with no active `user_product` |
| P3 | INTRO charges where the caller is not the billing owner | `token_transaction.userId` vs the flow's billing owner |
| P5 | Space-key calls whose agent is outside the key's space | back logs (`apiKeySpaceId` is not stored) |
| P8 | 500 responses on `/worker/charge-tokens` | back / worker logs |

## Not run after the release

- Backfill of past drift, past duplicate report rows or overwritten claim-check payloads: decided not to.
- Recount of `user_product.flows` from live agents (47 counters below their live agents on dev): product decision, not part of B1.
