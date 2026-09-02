# S3 — A ceiling on what one run can spend, and on how much of the fleet one tenant can hold

**Goal:** bound cost and bound fairness, before parallelism removes the accidental throttle that
provides both today.

**Depends on:** nothing. **Blocks:** B5. **Severity:** high (review §1.3, §1.4).

## Why the current protection is accidental

**Spend.** `assertCompletionCredits` (`product.service.ts`) is a boolean gate: for `INTRO`
products it checks `trialTokens > 0`; otherwise, having a subscription is enough. Per node,
`getUserProductFromFlow` checks *entitlement to a model*, not remaining budget. Charges are recorded
after the fact into `token_transactions`. **Nothing decrements an allowance, and nothing aborts a
run that has already overspent.** For a paid account the first signal is the invoice.

**Tenancy.** There is no per-tenant concurrency cap anywhere. **Corrected 2026-09-02.** The first
draft said the Bull processor declared `@Process` with no concurrency option, so each backend
replica ran one queued run at a time, and that this accidental serialisation was doing protective
work. That stopped being true on 2026-08-21 — PR #1902 landed two hours after this spec's snapshot:
`apiV2Job.processor.ts` now declares `@Process({ concurrency: parseConcurrency(AGENT_CONCURRENCY) })`,
default **5** per replica. So the throttle is explicit, five times looser, and still not per
tenant: one organisation can hold all five slots on every replica. It caps *how many* runs execute,
not *whose*. The fairness bug this task fixes is unchanged; the protection it was said to be
replacing is smaller than described. Keep the two limits distinct in the code and in the prose —
the tenant cap admits, `AGENT_CONCURRENCY` executes — and start by emitting the per-tenant
concurrency metric, so that the number five stops being a guess. B5 removes the remaining
back-pressure deliberately.

## Scope

**In — spend.** A ceiling checked **at charge time**, in the same call that already records the
spend.

**The ceiling applies to the run chain, not to a single run** (`TASK-S1`). A sub-flow gets its own
run identity with a `parentRunId`, so a per-run ceiling would be defeated by nesting: five levels
buy five ceilings, and recursion becomes the way around the limit. The charge call must resolve the
chain root and account against it. This is cheap — the chain is already needed for depth, cycle and
cancellation — but it has to be stated, because a ceiling that recursion can multiply is not a
ceiling.

**One counter, two limits.** `TASK-S4` needs the same chain-root accounting for its node-execution
budget. Build it once and carry both units — cost and executions — rather than two accountants that
resolve the chain independently and can disagree about where the root is. That is the only place that keeps working once the worker owns the loop, and it needs no
new plumbing: `/worker/charge-tokens` already carries `execId`.

**Assumption to confirm — the run aborts rather than degrades.** Aborting is honest and cheap to
explain; degrading (dropping to a smaller model, truncating) hides the problem and produces output
the user did not ask for. Abort with a typed error carrying the ceiling and the spend, so the UI can
say what happened.

**Assumption to confirm — the default ceiling is derived from the plan, not a global constant.** A
single number is wrong for both ends of the customer range. Make it a column on the product with a
conservative default, overridable per org.

**In — tenancy.** A cap on concurrent runs per organisation, enforced where runs are admitted, with
excess runs queued rather than rejected. Rejection turns a capacity limit into an error the customer
sees; queueing turns it into latency, which is the correct trade for a background execution system.

**In.** Both limits emit a metric before they emit an error. A ceiling nobody can see being
approached will be discovered by being hit.

**In — the pre-flight credit check, per `D20`.** The ceiling is not a per-node property evaluated at dispatch. Check before the run starts, in the gate `S1` already runs between building the DAG and spending anything: does this flow need credit, and is there enough. Refusing there turns a bill into an error message. It does not replace the charge-time ceiling — a pre-flight check cannot know which branch will run — but it catches the case that matters most, which is starting work that was never going to finish.

**Out.** Changing pricing, plan structure, or how charges are computed.

## Verification

- **Negative control (required), spend.** Build a flow that loops until it exceeds the ceiling, run
  it with the check disabled, and record what it costs. Then enable and confirm it aborts at the
  ceiling with the spend and the limit in the error. The first half of that test is the
  justification for the second.
- **Measure before refusing** (PLAN §3.3.2), and here it is load-bearing: compute what the proposed
  ceiling would have done to **every real run in the stored history**. Any run that legitimately
  completed and would now be aborted is a false refusal, and the count must be zero before this
  ships. Report runs whose cost cannot be reconstructed as *unverifiable* rather than as passing.
- **Tenancy.** Two orgs, one submitting a wide graph: assert the second org's run still starts
  within a bounded wait. Then remove the cap and watch it starve — that is the fairness bug.

## Done when

A run cannot exceed its ceiling, no historical run would have been falsely aborted, one tenant
cannot occupy the fleet, and both limits are observable before they are hit.

## Files

`back/src/app-api/product/product.service.ts` (`assertCompletionCredits`) · `back/src/temporal/worker.controller.ts`
(`/worker/charge-tokens`) · `back/src/app-api/token_transaction/` ·
`back/src/jobs/apiV2Job/apiV2Job.processor.ts` (`@Process` concurrency, `AGENT_CONCURRENCY`) · product/plan schema + migration
