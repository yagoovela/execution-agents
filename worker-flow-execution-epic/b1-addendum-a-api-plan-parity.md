# B1 Addendum A — API-key and REST API callers: charging and plan limits

Task: https://app.clickup.com/t/868mebgw7 (parent 868mdm99b). Back branch `refactor/868m0vmun`.
Status 2026-10-06: P1 (`bf23e69b`) and P4 (`5ce3019d`) done and validated on dev, P2, P3, P5–P8 planned.

## Decisions (2026-10-06)

- Every API caller is charged and respects the limits of **their own plan or their org's plan**.
- A user **without a plan is not refused**. They are limited by `users.trialTokens` when they have it,
  and by their plan's values when the plan has values.
- Paid plans keep overage billing (existing decision). No paid plan has a hard FluxToken stop:
  `token_limit_reached` is declared in `plan-limit.ts` but nothing throws it.

## Who the caller is

Every path resolves to a `User`; nothing is anonymous.

| Auth | Principal | Org known? |
|---|---|---|
| JWT | the user (`JwtStrategy` + `CurrentUserInterceptor`) | `selectedCompanyId` |
| Personal key (`users.apiKey`) | the user (`apikey.strategy.ts`) | `selectedCompanyId` (last UI choice, not tied to the key) |
| Space key (`spaces.apiKey`) | the space's `company.user`, tagged `apiKeySpaceId` | the space's company, but only the space id is attached |
| Master key | the master owner, or with `x-flux-act-as-space` the target space's `company.user` | written to the audit log only |

Space and master keys can only be charged to the company owner, never to the person who generated the key.

## How runs are charged today

- **Who pays.** Runs bill the **flow's** company billing owner (`selectFlowAdmin`, `getUserProductFromFlow`,
  `resolveBillingOwner`), never the caller's selected org. Reports are keyed by the flow's company.
- **Trial.**
  - The pre-check `assertOwnerTrialAllowance` only runs when the billing owner has an INTRO `user_product`.
  - The decrement `consumeTrialTokens(userId)` hits the **caller**.
- **No plan.**
  - `getUserProduct` throws "No active subscription found".
  - Inline nodes fail.
  - Worker nodes: `/worker/charge-tokens` answers 500, and `process-single-node.workflow.ts` ignores the
    result, so **the node runs for free**.

## Gaps and plan

| # | Gap | Fix | Refuses? | Measure first |
|---|---|---|---|---|
| P1 ✅ | REST `POST /integrations/agents` never claimed a plan slot; REST chatbots never entered `chatsId`; an empty company id matched an arbitrary company | `createCountedFlow` with the shared `claimCreationSlot`; release on failure; `chatsId`; `if (!companyId) return null` | yes, at the plan limit only, same as app/MCP | done: on dev 9 limited-plan users have a membership but no valid selected org; they are now counted on their own plan |
| P2 | No-plan users never checked against `trialTokens`; their runs fail (inline) or run free (worker) | Charge no-plan users against `users.trialTokens` (atomic decrement, floor 0, ledger row); pre-run refusal `insufficient_quota` at 0; no `trialTokens` = current behaviour kept and reported | yes, at 0 trial tokens | no-plan users who ran agents in the last 30 days, and their `trialTokens` (dev, then prod by the user) |
| P3 | Trial checked on the billing owner, decremented on the caller | Decrement the account whose INTRO plan was checked (the billing owner) | no | rows where caller ≠ billing owner on INTRO charges |
| P4 ✅ | `/flux/api-v2` checks only inside the queued job; a 402 reaches sync callers as 500 | `ProductService.assertCanStartRun` (access, space limit, read-only plan and trial; nested runs skip the owner part) used by `apiV2` and, through `assertCanStartRunById`, by the controller before the status row and `enqueueApiV2Job` — back `5ce3019d` | no new refusal, only when and the status code (402/403 at once; a callback caller no longer gets 202 + error callback) | none needed; `api-v2-refusal.integration.spec.ts` red without the pre-queue call; dev: 402 at once, sync and callback, no status row |
| P5 | A space key runs any agent the owner can reach; the space limit checked is the agent's space | With `apiKeySpaceId`, require the flow to be in that space | yes | space-key calls whose flow is outside the key's space (logs / `flow_logs`) |
| P6 | `/open-ai/get-completion` has no pre-run check and bills the owner of any `flowId`, with no access check | `checkIfUserCanRunFlow` + `assertOwnerCanRunFlow` + `assertSpaceWithinLimit` before the call | yes (cross-tenant) | callers whose `flowId` they cannot access |
| P7 | `/flux/batch-process` starts any batch by id, with no ownership check | Load the batch scoped to the caller | yes (security) | may become its own task |
| P8 | The worker treats a failed charge (500) and a refused model access as success | Fail the node with the charge error, or retry; decide with P2 | yes | count of 500s on `/worker/charge-tokens` |

Out of scope, noted:
- Space usage is added to `user_spaces` only when the caller has a row there, so space-key usage can be
  undercounted (data-dependent, not verified).
- Library/sub-flow worker charges bill `node.flow_id` without `billingFlowId`.
- The app single-node path skips the trial and space checks (JWT, not API). For paid nodes this is
  closed by A3 below: the node credit gate runs on every path that executes a paid node.

## Order

P1 (done) → P4 (status code only, no new refusal) → P3 → P2 + P8 together (same account, same ledger) →
P6 → P5 → P7. Every refusing item ships only after its measurement shows zero false refusals.

## Tests

One real-Postgres spec per item, each seen red with its part removed, then a dev check through an API key
on a test account restored afterwards. P1: `api-flows-plan-limits.integration.spec.ts`, 6 cases:
- concurrent creates on a plan of 3 create 3 and refuse 2;
- a failed provision releases the slot;
- a chatbot is counted and added to `chatsId`;
- a no-plan user is created without a refusal;
- an unlimited-org member is counted on the owner;
- a personal folder counts on the creator, not on an unlimited org the creator belongs to.

The negative controls (claim, release, `chatsId`, empty-id guard removed) each turned the matching case red.

## A3 — Stop a paid node when the paying account can no longer be charged

Task: https://app.clickup.com/t/868meyyw8 (subtask of B1). Back `d2d44b9f`, `a8131b1a`; worker `4dad3dd`,
`03cc813`; all on `refactor/868m0vmun`. Amends PLAN.md D19 and D20 (2026-10-08).

**Decisions (2026-10-08).**
- The trial balance keeps its floor of 0. The node that crosses 0 finishes and its full usage goes to
  the ledger; the balance does not go negative.
- A paid node runs only while the paying account can still be charged. Free nodes after it still run;
  the next paid node is refused before any provider call and the run stops there (A B C D E with A and E
  paid and A emptying the balance: A finishes, B C D run, E is refused).
- A plan without the model's provider is refused (`model_not_in_plan`).
- No active plan is refused only once product decides (O1/O2/P2), behind its own flag.
- Both flags ship off: each would-be refusal is logged, nothing is refused.

**The rule.** `ProductService.checkNodeCreditGate` reuses the run checks, nothing restated:
`assertSpaceWithinLimit`, `assertOwnerCanRunFlow` (Vault, Intro trial, guest) and `getUserProductFromFlow`
(plan, and the provider when a model is given). It classifies the refusal (`space_limit_reached`,
`read_only_plan`, `insufficient_quota`, `guest_preview_exhausted`, `model_not_in_plan`, `no_active_plan`)
and enforces it only when `node_credit_gate` is on, or `node_credit_gate_no_plan` for `no_active_plan`;
otherwise it logs `node_credit_gate would refuse <code>` and allows. System agents and system libraries
are exempt, as in the pre-run check. Migration `1790700000000-SeedNodeCreditGateFlags` seeds both flags
off (hand-written, like `SeedSpendCeilingFlag`: a data seed has no entity diff to generate).

**Where it is asked.**

| Path | Paid node types | How |
|---|---|---|
| Flow run and `/process/single-node` (worker) | AI text, large memory, web search, voice, image, web crawling, MCP | `processSingleNode` calls `nodeCreditGateActivity` → `POST /worker/node-credit-gate` before the node's work, behind `patched('node-credit-gate')`. A refusal is a non-retryable `UserConfigError` carrying the plan sentence |
| Run node through `/process/single-node-legacy` (back inline) | large memory, web search, voice (the paid types that endpoint accepts) | `SingleNodeLegacyService` asks the same rule before dispatching; a refusal goes through the existing failure path (node error row, FAILED status with the sentence) |
| Prefetch mode (`FLUX_EXEC_MEMORY_MODE=prefetch`) | all | **not covered.** Off by default and set nowhere in the repos; needs the same call if it is ever turned on |

Only AI text passes its model, so only AI text is filtered by provider. Image charges send
`billingFlowId`, which drops the provider filter, so the gate does not add an image refusal the charge
itself would not make. Both paths fail open: when the back cannot answer, the node runs and the failure
is logged, so a gate defect never blocks a run.

**Production numbers before enabling (2026-10-08, `868mebgw7-billing-cards-prod-queries.sql`).**
- BC4, 30 days: no AI text or image run would be refused as `model_not_in_plan`. 285 runs from accounts
  with no active plan (228 Anthropic, 56 OpenAI, 1 Perplexity) would be refused as `no_active_plan` once
  its flag is on. 119 uncharged Intro runs have a plan that includes the provider; their cause is not
  yet known (exhausted trial or library runs are the candidates).
- BC6: Intro (731 active) and Starter (85) do not include Gemini, and BC5 shows the template agent of new
  Intro accounts has a `gemini-3-pro-preview` node. No Intro or Starter Gemini run succeeded in 30 days,
  but with `node_credit_gate` on that node is refused. Product decides before the flag is turned on.
- BC1 and BC3: no account is above its agent or chatbot limit; 1 of 108 spaces has a monthly limit and
  it is below it.

**Tests (each seen red with its part removed).**
- Back, `node-credit-gate.integration.spec.ts` (real Postgres, 9 cases): covered plan and Intro with
  trial allowed; Intro at 0, `model_not_in_plan`, Vault, space over its limit and no plan refused with
  their codes; the trial and no-plan refusals only logged while their flag is off. Red: 5 cases with the
  enforcement removed, 3 with `no_active_plan` mapped to the general flag.
- Back, `single-node-legacy.credit-gate.spec.ts` (4): refused large memory never dispatched, error row
  and FAILED status carry the sentence; allowed web search runs; voice runs when the gate throws; a free
  node never asks. Red: 2 without the call, 1 without fail-open, 1 without the type filter.
- Worker, `process-single-node.workflow.spec.ts` (4): refused AI text and image never generate, FAILED
  carries the sentence; allowed AI text passes its model; a free node never asks. Red: 3 without the call.
- Worker, `activities.charge-refusal.spec.ts` (3): refusal is non-retryable with the sentence and 402;
  allowed resolves; a 500 from the back lets the node run. Red: 1 when the refusal is ignored.
- Worker, `process-single-node.replay.spec.ts`: histories recorded on a local Temporal server from the
  workflow at `4dad3dd^` (AI text, free node) and from the gated workflow replay cleanly. Red without the
  patch guard: `TMPRL1100 Nondeterminism error: ... 'validateModelAccessActivity' does not match ...
  'nodeCreditGateActivity'`. Regenerate with `etc/_868meyyw8/capture-replay-histories.ts`.

**Before turning the flags on in production.** Count the `node_credit_gate would refuse` log lines by
code for at least a week, and settle the Gemini question for Intro and Starter.
