# B1 Addendum A — dev validation, 2026-10-06

Environment: dev (`api-task-definition-dev:2548`, back `master` `29af085e`, front `main` `75ee7acc`).
Driven through the dev MCP (`fluxprompt-mcp-dev`, user alexandre.paravani) and read-only queries on
the dev database. Workspace under test: **lex corp.** (`a88a6f8f…`), billing owner
alexandre.paravani, plan Organization (20,000 included tokens), `user_product` `c99ba2f8…`.

Baseline before any test (08:30): `usedTokens` 2782.39, `apiCalls` 1292, `totalBill` 0,
`flows` 17, `chatbots` 0, `current_period_end` 2026-07-29 (past — see Renewal).

Test agents (lex corp., `gemini-2.5-flash-lite`, one `commandTextNode` each): personal
`845305f8…` (folder outside any space) and space `812c7dc2…` (space **s1** `1a9c579e…`).
Logs: the back's Winston logger ships to Datadog only, so cron evidence on dev comes from the
database, not CloudWatch.

## 868mdm99b — Addendum A: concurrent charges (PASS)

Six runs dispatched at once through the MCP (3 personal + 3 space, run ids `53f8dc33`,
`fc657ce4`, `f0134555`, `1174dc5e`, `abeb3592`, `99dc3fd3`); all `completed`, 0.0012 each.
T0 = 11:25:56 UTC, after = 11:27:46 UTC.

| Counter | Before | After | Delta | Ledger since T0 |
|---|---|---|---|---|
| `user_product.usedTokens` | 2782.3872177 | 2782.3944177 | +0.0072 | 0.0072 (18 rows) |
| `user_product.apiCalls` | 1292 | 1310 | +18 | 18 rows (6 execs × input/output/used) |
| `user_product.totalBill` | 0 | 0 | 0 | cost 0 (within the plan) |
| weekly `report` (user) | — | 3 rows, one per model | 0.0048 + 0.0024 + 0, `apiCalls` 6 each | per-api sums identical |

Every delta equals the ledger; one `report` row per key; no duplicates. (Locally the same burst
lost 22 of 54 `apiCalls` before the fix.)

## 868mdtvhg — space and flow usage reports (PASS)

Same six runs:

- `user_spaces` s1, alexandre: `nodeRuns` 75 → 78 (+3, only the 3 space runs), `usedTokens`
  +0.0036 (= 3 × 0.0012); the other member unchanged.
- `company_flow_report` / `user_flow_report`: one row per flow, `nodeRuns` 3 each,
  `tokenUsed` 0.0036 each.
- `company_user_report`: personal flow → one new row with `spacesId` null, `nodeRuns` 3; the
  space runs went to the existing s1 row of the user (`733f6fea`, key user+space+company+label,
  `nodeRuns` 62). That key is the production semantics (`origin/production` looks the space row
  up without `flowId`), not a regression.
- Company-level `report` row (`userId` null): one row, `usedTokens` 0.0072, `apiCalls` 6.
- The personal agent touched no space.

## 868mdtvj9 — space FluxToken limit (PASS)

s1 `limit` was null (unlimited); usage 708.69 + 146.34 = 855.03. Dev ad-hoc write, restored:

| Step | `spaces.limit` | Run | Result |
|---|---|---|---|
| 1 | 800 (below usage) | space agent `bf6efb17` | `error` in 75 ms: "This space has used its monthly limit of 800 FluxTokens. Ask a space admin to raise it to keep running agents." 0 tokens; `user_spaces` unchanged (708.6926 / 78) |
| 2 | 800 | personal agent `46b4abc9` | `completed` — a flow outside the space is never refused |
| 3 | 10000 (above usage) | space agent `a1c18510` | `completed`; s1 → 708.6938 / 79 (counter keeps counting) |
| 4 | restored to null | — | verified null |

Not covered on dev: the front dialog and the canvas Run (need a browser session).

## 868mdtvhb — A2 voice-clone charges (NOT OBSERVABLE ON DEV)

The cloned-voice cron has not charged on dev since 2025-10 (`charge-total-cloned-voices` rows
by month: last 2025-10); dev has 6 voices. No clone was created today. Covered by the
real-Postgres specs only; a dev check needs a voice clone in the UI (JWT) or the
`GET /cron-jobs/chargeUsersPerClonedVoice` trigger.

## 868mdtvhw — renewal (NOT OBSERVABLE ON DEV)

The midnight renewal did not touch any `user_product` on dev: 25 rows are due (12 with a past
`current_period_end`, oldest 2026-01-12, including lex corp. at 2026-07-29; 13 without one) and
none was updated at 00:00 UTC. Either the cron is disabled on dev outside the task definition,
or the loop stops at the first Stripe error — the second is 868mdym0c's "one user's failure
stops the others". Telling them apart needs Datadog. Covered by the real-Postgres specs only.

## 868mdtvj4 — plan limits (PASS in the app; MCP bypass confirmed)

First run: lex corp. is on Organization (`products.flows` null, chatbots `unlimited`), so no
refusal path runs there. Two agents created through the MCP left the counter at 17.

Second run, 2026-10-06, against `api-dev.fluxprompt.ai` with the account owner's token. user_product
`c99ba2f8` was moved to Starter (5 agents / 3 chatbots) with the counters at 4 / 2, so each limit had
one free slot, then restored.

| Step | Action | HTTP | Counter flows / chatbots |
|---|---|---|---|
| 0 | start | — | 4 / 2 |
| 1 | create agent | 200 | 5 / 2 |
| 2 | create agent at the limit | 400, refused | 5 / 2 |
| 3 | duplicate at the limit | 400, refused | 5 / 2 |
| 4 | delete the agent from step 1 | 200 | 4 / 2 |
| 5 | duplicate with a free slot | 200 | 5 / 2 |
| 6 | duplicate at the limit | 400, refused | 5 / 2 |
| 7 | create chatbot | 200 | 5 / 3 |
| 8 | create chatbot at the limit | 400, refused | 5 / 3 |
| 9 | MCP `create_agent` at the limit | applied | 5 / 3 (not counted) |
| 10 | MCP `remove_agent` | applied | 5 / 3 (not released) |
| 11 | delete the copy and the chatbot | 200, 200 | 4 / 3, then 4 / 2 |

Restore: Starter → Organization, counters 17 / 0; the row matches the pre-test snapshot. All four test
flows are soft-deleted.

Steps 9–10 are the "before" of the decision taken on 2026-10-06 (MCP agents count toward the plan
limit).

After: implemented in back `refactor/868m0vmun` `38cfef04` (dev `master` `6a534bb8`, deploy run
37484774763 green). Same account, Starter, counters 4 / 2, through the dev MCP (`create_agent`,
`remove_agent`):

| Step | Action | Result | Counter flows / chatbots |
|---|---|---|---|
| 1 | create agent | applied | 5 / 2 |
| 2 | create agent at the limit | refused: "You have used all 5 agents your Starter plan includes." | 5 / 2 |
| 3 | dry-run at the limit | same refusal | 5 / 2 |
| 4 | remove the agent from step 1 | applied | 4 / 2 |
| 5 | create chat agent | applied, recorded in `chatsId` | 4 / 3 |
| 6 | create chat agent at the limit | refused: "You have used all 3 chatbots your Starter plan includes." | 4 / 3 |
| 7 | remove the chat agent | applied, removed from `chatsId` | 4 / 2 |

Restored to Organization 17 / 0; the row matches the snapshot. Unlike the app endpoints, the MCP
returns the plan-limit message itself.

Pre-existing, not caused by B1: every refusal answers `400 "Something went wrong"`. `createFlow` and
`duplicateFlow` throw `planLimitReached` inside a `try` whose `catch` replaces it with the generic
error (same on `origin/production`), so the plan-limit message never reaches the client.

Fixed on 2026-10-06 (decision: the refusal must show a clear plan-limit message). Back `3140bf26`:
both catches rethrow a 402, and only a 402; every other error keeps the old answer. Front `6faaab8b`:
the create modal, duplicate, Fluxbot quick-create and the dashboard modal open the plan-limit dialog.
`flow-plan-limits.integration.spec.ts` asserts the refusal body (402, `flow_limit_reached` /
`chatbot_limit_reached`, the plan sentence) for concurrent creates and a duplicate at the limit;
the three cases are red with the rethrow removed.

Dev check, 2026-10-06 (dev `master` `7fd66d4f`, `main` `d1e6554b`, deploys green), same account moved
to Starter at 4 / 2 and restored (the row matches the snapshot, `chatsId` empty, no test flow left):

| Step | Call | HTTP | Counter flows / chatbots |
|---|---|---|---|
| 1 | app create agent | 200 | 5 / 2 |
| 2 | app create agent at the limit | 402 "You have used all 5 agents your Starter plan includes. Upgrade to keep building." | 5 / 2 |
| 3 | app duplicate at the limit | 402, same message | 5 / 2 |
| 4 | app create chatbot | 200 | 5 / 3 |
| 5 | app create chatbot at the limit | 402 "You have used all 3 chatbots your Starter plan includes. Upgrade to add more." | 5 / 3 |
| 6 | app delete the agent | 200 | 4 / 3 |
| 7 | REST `POST /integrations/agents` (API key) | 201 | 5 / 3 |
| 8 | REST at the agent limit | 402, agent message | 5 / 3 |
| 9 | REST chat at the chatbot limit | 402, chatbot message | 5 / 3 |
| 10 | app delete the chatbot | 200 | 5 / 2 |
| 11 | REST chat | 201, recorded in `chatsId` | 5 / 3 |
| 12–13 | app delete both REST items | 200, 200 | 4 / 3, then 4 / 2 |

The first create and chatbot calls at the limit answered `400 "Something went wrong"` while ECS was
still draining the previous task (duplicate already answered 402); repeated a minute later, every
call answered 402. The sequential create at the limit had no test (the concurrent ones are refused by
the atomic claim, not by the pre-check): added to `flow-plan-limits.integration.spec.ts`.

The browser check of the space-limit dialog (868mdtvj9) is dropped: there is no screen to set a
space limit for now.

## 868mebgw7 — API-key and REST API callers (P1 AND P4 VALIDATED ON DEV, P2, P3, P5–P8 PLANNED)

Plan: `b1-addendum-a-api-plan-parity.md`. P1 is back `bf23e69b`: `POST /integrations/agents` claims
a plan slot through `createCountedFlow`, and `unlimitedCompanyProduct` returns null for an empty
company id. `api-flows-plan-limits.integration.spec.ts` covers 6 cases on real Postgres, each red
with its part removed. Dev check: steps 7–13 of the 868mdtvj4 table above.

P4 is back `5ce3019d` (dev `9609806b`): `/flux/api-v2` runs `assertCanStartRunById` before the status
row and the enqueue. Dev check on 2026-10-06, space `s1` (`1a9c579e`, usage 855.03, limit null),
agent `812c7dc2` ("B1-AddA-validation · space s1"), owner's personal API key:

| # | Step | Result |
|---|---|---|
| 1 | Set `spaces.limit` = 800 | 1 row |
| 2 | 3 sync calls at 22:15 UTC, right after the deploy reported success | 500 + `executionId` + error (old task still serving); 3 `error` rows in `flow_execution_status` |
| 3 | Sync call at 22:16 UTC | **402** `{type:'plan_limit', code:'space_limit_reached', limit:800, used:855.03}` at once |
| 4 | Call with `callback_url` | **402** at once (before: 202 + error callback) |
| 5 | `flow_execution_status` for the agent | only the 3 rows of step 2; none for steps 3–4 |
| 6 | Restore `spaces.limit` = null | 1 row, read back null |

Not checked on dev: a run that passes the check (covered by the local spec's "queues the run" case;
a dev run would spend tokens). `flow_execution_status.created_at` reads 3 h ahead of `now()` on dev,
so filter by id, not by time.

## 868mdym0c — Enterprise NaN (FIXED AFTER THIS RUN, NOT OBSERVABLE ON DEV)

Implemented after the validation above. First version (`7cd69cb3`, dev `8eca3350`) kept the current
`extraTokens`; the owner then clarified that `unlimited` Enterprise accounts are internal no-limit
accounts (dev and product teams) that must not change. Dev has two of them with a Stripe
subscription and no period end (`user@example.com`: 47,120 tokens used, `totalBill` 51.83, `extraTokens`
0; `another-user@example.com`). Keeping `extraTokens` would have let the renewal reach them for the
first time: charge the accrued 51.83 on Stripe, or deactivate them if the subscription is not active.
Before, the renewal only reached them to crash — very likely why dev's renewal leaves 25 accounts
due (see 868mdtvhw): the missing-period sync threw on them and aborted the whole selection.

Final rule (`dc9b4830`, dev `6bff8fce`): a plan without a numeric allowance is left out of the
renewal and the missing-period sync. Real-Postgres tests: the `unlimited` account stays untouched
(no lookup, no payment, counters and `extraTokens` unchanged) while the next account renews; the
isolation tests use a numeric Enterprise. Controls: without the filter, or with the filter only on
the final list (the early return leaks), the three `unlimited` tests turn red. Dev: an Enterprise
with negotiated terms still renews with its credits (ad-hoc check, terms ignored → not renewed).

### 868mebgw7 — P5–P8 and C2-B on dev (2026-10-07)

Back dev `ba06f80a` (all of P3, P5, P6, P7, C2-B and the P7 deleted-agent fix), worker dev `786a6c2` (P8).
Test account: the owner's Organization plan `c99ba2f8…`, restored after each step (read back equal).

| Item | Step | Result |
|---|---|---|
| P6 | Owner's key, another user's personal agent | **403** before any work; no ledger rows |
| P6 | Owner's key, agent in test space `s1` with `limit` set to 800 (restored to null) | **402** `space_limit_reached` |
| P5 | A space key (another org) on an agent outside any space, 17:25:59 UTC | 403 (stranger). Datadog `service:EnhancedAILogging env:dev` at 17:25:00.556Z: `space_key_outside_space: key of space 9b6fb0e3… ran flow 80ed4ac7… in space none` (dev's clock runs about a minute behind; the same offset shows in `node_executions`) |
| P7 | Stranger space key on a batch whose agent was soft-deleted | Before `ba06f80a`: 200 on status and download (and a start would have nulled the batch's `flowId`). After: **403** on start, status, stop and download; owner still 200 on status and download; batches unchanged |
| P8 | Text-only agent `845305f8`, plan active (control) | Node "OK", 3 ledger rows |
| P8 | Same agent, plan set inactive for the call (18:32:04 UTC, exec `02f71f01…`) | Node "OK", **0 ledger rows**: the run is not refused and the text node runs uncharged (O11 case 1). Old worker at the time (see the P8 rerun below) |
| P8 | Rerun after worker dev `c0a72cc` (build fix `2c7074c`, task definition `:194`) started, plan inactive for the call (19:07 UTC, exec `2da0e6b9…`) | 200, node "OK", **0 ledger rows**, plan restored (read back equal). Worker CloudWatch `/ecs/worker-task-definition-dev`, task `4b3a6f1b…`, 19:06:08 UTC: `validate-model-access refused` and `charge-tokens refused` with `execId 2da0e6b9…`, `nodeId commandTextNode_b1val_p`, both `statusCode: 500` (back answers 500 "No active subscription found" for an account with no active plan, the P2 case). Until that deploy dev ran worker `26112f6`: the `5fe389f` and `786a6c2` deploys failed to start with `Cannot find module '/app/dist/main.js'` because `scripts/egress-measure.ts` (868m0vm7q) was in the build |
| P8 | Plan message, back dev `3fba2cc0` and worker dev `639230f`, plan inactive for the call (2026-10-08 12:15 UTC, exec `2c2d6010…`) | 200, node "OK", 0 ledger rows, plan restored (read back equal). Worker CloudWatch, task `73f636ac…`: `validate-model-access refused` and `charge-tokens refused` now carry `statusCode: 402`, `code: no_active_plan` and `No active plan covers this agent. Choose a plan to keep running agents.` (was 500 with no reason). `model_not_in_plan` is covered by `plan-access-refusal.integration.spec.ts`, not run on dev |
| C2-B | `usedTokens` above the allowance, `totalBill` 50.5, payment method `pm_card_chargeDeclined` (Stripe test mode) | `totalBill` 50.5 kept, plan **deactivated** (card-declined path) |
| C2-B | Same, real test card | `totalBill` 50.5 → **0.5**, plan active ($50 test charge) |

| P3 | Test account `+nonadmin` given an Intro plan (trial 100) and made billing owner of the owner's org; the owner (trial 50) runs the org's text agent with its own key, model set to `gpt-4o-mini` (18:41:15 UTC, exec `3e135bae…`) | `+nonadmin` 100 → **99.9967**, caller **50 unchanged**; the 3 ledger rows are on the new Intro row at $0. Everything restored (plan row deleted, trials null, billing owner, node model) |

The P7 dev check found the hole fixed in back `5ffdeca1`: the two dev batches belong to agents deleted on
2026-10-01, which the access check could not see.

The first P3 attempt kept the node on `gemini-2.5-flash-lite`: the Intro product has `gemini: false`, so
model access and the charge were refused and the node ran uncharged with neither trial touched. That is
O11 case 2 (a model outside the plan runs free), seen on dev.
