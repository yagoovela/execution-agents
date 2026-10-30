# B1 Addendum A — plans and token usage modes (868mebgw7, P2/P8 input)

Analysis 2026-10-07, back `refactor/868m0vmun` @ `5ce3019d`, worker @ `65f19a7`, dev database.
Question: does "a user without a plan is not refused; they are limited by `trialTokens`, or by their
plan's values" fit the plans that exist on the platform?

Short answer: no. "No plan" is not one state, two plan types are missing from the code, and the
worker ignores the charge result. The rule needs the decisions at the end before P2/P8 ship.

## Plans on dev

| Plan | `type` | Allowance (`tokens`) | `fluxTokenPrice` | Agents / chatbots | Active subs |
|---|---|---|---|---|---|
| Intro | `intro` | 0 (trial in `users.trialTokens`) | 0.003 (not charged) | 5 / 3 | 129 |
| Starter | `starter` | 1500 | 0.003 | 5 / 3 | 27 |
| Advanced | `advanced` | 3000 | 0.002 | 25 / 15 | 3 |
| Professional | `professional` | 10000 | 0.0015 | unlimited | 7 |
| Organization | `organization` | 20000 | 0.00125 | unlimited | 25 |
| Enterprise | `enterprise` | `unlimited` | 0.0011 | unlimited | 12 |
| Vault | `vault` | 0, `can_run_flows=false` | 0 | 0 | 0 |
| Voice Plan | `monthly` | none | **0** | none | 4 |
| Premium FluxPrompt Plan | `one_time` | none | **0** | none | 12 |

`monthly` and `one_time` are not in `ProductType` (`products.entity.ts:74-82`).

## Account states found

| State | Users on dev | How usage is charged today | What refuses |
|---|---|---|---|
| Intro | 129 | Rate 0, `trialTokens` decremented, floor 0 | Pre-run 402 at 0 (root runs only) |
| Guest | — | Intro with 60 tokens, 5000 once an email is bound | `guest_preview_exhausted` |
| Starter…Organization | 62 | `extraTokens` free, then `fluxTokenPrice`, Stripe in $50 chunks | Nothing; a failed $50 charge sets `active=false` mid-period |
| Enterprise (`unlimited`) | 12 | Every token billed in $50 chunks; never renewed | Nothing |
| Plan with no `subscriptionId` | 26 Starter, 9 Org, 10 Ent, … | Never renewed: `extraTokens` stays, all usage is overage | `payBill` with no Stripe customer fails |
| Only `monthly` / `one_time` | 10 | **Rate 0, no allowance: free and unlimited** | Nothing |
| Several active plans | 6 | `getUserProduct` picks an arbitrary row (no `ORDER BY`) | Trial gate refuses if any active row is an exhausted Intro |
| Internal `@enhanced.ai` | — | Shared internal Enterprise row `83dcc3b3…`, no Stripe | Trial gate still reads the user's own rows |
| No plan, never had one | 121 (`trialTokens` null 121) | Inline nodes fail; worker text node runs **uncharged** | `/v1/chat/completions` 402; apiV2 gate lets them through |
| No plan, lost one (cancelled, failed renewal, failed $50 charge) | 77 (29 with `trialTokens > 0`) | Same as above | Same; Intro cannot be re-provisioned (`intro-plan.service.ts:34`) |

Usage in the last 90 days (ledger): Intro 33 accounts, Organization 4, Professional 1, Enterprise 1,
internal account 2475 rows. No `monthly`/`one_time`-only account and no account without a plan was
charged. Worker text and image nodes in the last 30 days: 0 successful runs without a charge.

## Gaps against the rule

1. **No plan is refused, not trial-limited.** Inline back nodes, completions and non-text worker nodes
   fail on "No active subscription found"; `trialTokens` is never decremented for them.
2. **Worker text generator ignores model access and the charge** (`process-single-node.workflow.ts`:
   `validateModelAccessActivity` and `chargeTokensActivity` return `success:false` and are not read).
   No plan, a plan without the model, and Vault all run uncharged. (P8)
3. **`monthly` / `one_time` plans run free** (rate 0, no allowance).
4. **Several active plans**: which one pays is arbitrary.
5. **A paid plan stops mid-period** after one failed $50 charge and the account falls into "no plan",
   with no way back to Intro.
6. **`/execute-single-node`** checks access only: no trial, Vault or space gate.
7. **`/v1/chat/completions`** charges the caller's own plan, never the org's.
8. **Voice-clone cron** aborts for every remaining account when one owner is Intro or has no plan.
9. Space usage is not counted when the running user has no `user_spaces` row (chatbot, public runs).

## Decisions needed

- D-P2a: a user who never had a plan (121 on dev: ~79 email sign-ups, mostly 2023–2024, before Intro
  was provisioned automatically; ~40 invites, 27 of them org members who run on the owner's plan; 13
  sign-ups from 2026): provision Intro on first run (5000 trial tokens), or refuse with a "choose a
  plan" message?
- D-P2b: a user who lost a paid plan (77): refuse with "your plan is inactive, update your payment",
  or let them run on leftover `trialTokens`?
- D-P8: worker text node when the charge or model access fails: fail the node (same as inline), or
  keep running and report?
- D-3: `monthly` / `one_time` plans: are they add-ons (voice, one-time purchase) that should never pay
  for runs? If so, the charge must pick the account's run plan, not them.
- D-4: several active plans: which one pays (highest tier, most recent, the one with a subscription)?
- D-5: failed $50 overage charge: deactivate at once (today) or keep running until renewal?

Items 6–9 are outside 868mebgw7 unless chosen.

## Decisions (2026-10-07)

| # | Decision | Next step |
|---|---|---|
| D-P2a / D-P2b | Measure in prod first: it may be a dev-only shape | User runs PM1 and PM2 in [`b1-plan-modes-prod-queries.sql`](b1-plan-modes-prod-queries.sql) |
| D-P8 | Report only: a refused charge or model access is logged, the node keeps running | Worker `refactor/868m0vmun`: `charge-tokens refused` / `validate-model-access refused` (`console.error`), `activities.charge-refusal.spec.ts` red without it. PM7 is the baseline |
| D-3 | Open | PM5 shows whether `monthly` / `one_time`-only accounts run agents |
| D-4 | Needs more evidence | User runs PM4 (which plan row each charge used) |
| D-5 | Keep deactivating on a failed $50 charge | No email or notice exists today: `payBill` and the renewal only log, and there is no Stripe `payment_failed` webhook. Adding a notice is a separate scope question |

PM4 reads `transaction_payload` with `#>> '{}'`: the column is JSON holding a string, so
`->> 'userProductId'` alone returns null for every row (0 of 4169 on dev, 4169 of 4169 unwrapped).

## Production results (export of 2026-10-07 14:19)

PM1–PM11 ran in prod; PM5 and PM5b came back empty. Emails stay out of this file (they are in the
private decisions page).

| Item | Prod |
|---|---|
| O1 / D-P2a, never had a plan | 1,031 users (833 in no org, 198 org members); none ran an agent in 90 days |
| O2 / D-P2b, lost a plan | 107 users (74 org members, 17 with trial left); 8 accounts ran 928 runs in 90 days, the last on the day of the export; ledger cost $0 |
| O3 / D-3, Voice / Premium only | 0 accounts: dev-only shape |
| O4 / D-4, several active plans | 5 people, no subscription; one (Intro + Organization) had 84 charges in 90 days, 54 on the free Intro row |
| O5 / D-5, deactivations | 44 paid plans deactivated Apr–Sep 2026 whose owner has no plan now (~7 a month), all with a subscription |
| O6, no subscription | Starter 74 of 85 (50 with no Stripe customer), Organization 10/18, Enterprise 8/12, Professional 9/33, Advanced 1/16 |
| C2, $50 charge | 9 external open bills, highest $24.50: none at $50 |
| O7, unlimited external | 8 Enterprise accounts: 3 with a subscription, 5 with neither subscription nor period end |
| O11 / C8 / P8 | 406 of 8,993 AI text runs in 30 days succeeded without a charge (4.5%); image 0 of 318 |

PM2b and PM7b (received 2026-10-07 15:46):

| Item | Result |
|---|---|
| O2 / D-P2b, PM2b | The 8 accounts are external and all lost a paid plan (Professional, Advanced, Organization; last change from 2026-01 to 2026-08). 947 runs in 90 days, 5 of the 8 ran on the day of the query, the largest 528 runs. Trial tokens: none, one account at 0.02 |
| O11 / C8 / P8, PM7b | 410 uncharged AI text runs at the time of the query: 291 from 8 accounts with no active plan, 119 from 4 accounts on Intro only, 0 from a paid plan, all external |
