# S1 — Depth ceiling and cycle detection for sub-flows

**Goal:** make a self-referencing flow fail fast instead of recursing until something dies.

**Depends on:** nothing. **Blocks:** B6. **Severity:** critical (review §1.1).

## Why now rather than with B6

`flowCallerNode` calls `this.apiV2()` — the whole orchestrator — for the selected flow
(`flux.service.ts:5611–5622`); `libraryNode` does the same. There is no depth limit and no cycle
detection: `parentFlowId` is threaded for billing attribution only (`:5732, 5815`).

Flow A pointing at B and B pointing back at A recurses until the process dies, and each level is a
complete run — its own scheduler state, its own `node_executions` rows, its own run-log tree, its
own token spend. Two people composing reusable flows produce this by accident.

Today the blast radius is one backend process. **B6 turns sub-flows into Temporal child workflows**,
and a durable platform will faithfully sustain the recursion across the whole fleet, retrying each
level. The guard has to exist before that, not after.

## The identity decision — settled

A sub-flow **does not run under the parent's execution identity**, and it **does not** get a
disconnected one either. It gets its own run identity with an explicit **`parentRunId`**, forming a
chain back to the origin.

Three things fall out of the chain, and they are the reason for choosing it over the alternatives:

- **Depth and cycle** are read from the chain — it *is* the visited set.
- **Cancellation** propagates along it, which Temporal child workflows give natively.
- **Budget aggregates over it.** This is the one that is easy to miss: with a per-run ceiling and a
  sub-flow creating a new run, five levels of nesting buy five ceilings. Recursion becomes the way
  to defeat the limit. `TASK-S3` is amended to make the ceiling apply to the chain.

Absorbing the sub-flow into the parent's run was considered and rejected: it is a different graph,
so one `SchedulerState` would hold two node sets and two termination conditions, and the nested
run-log timeline the product already shows would be lost.

## Why the cycle is prohibited outright, not merely capped

The depth ceiling and the cycle rule are different rules with different justifications, and the
second is stronger.

**A flow already on the chain is awaiting a return.** When A calls B, A is suspended waiting for B's
result. For B to call A is not "deep recursion" — it is asking a flow that is already mid-execution,
with a caller expecting a value, to start again from the top. There is no semantics that makes that
coherent, and no legitimate use for it. So it is refused outright rather than allowed up to some
depth.

**The rule applies to the whole chain, not only the direct parent.** A → B → A is the obvious case,
but A → B → C → A has exactly the same problem: A is still waiting. The visited set covers both, and
the refusal message should name the chain so the author sees which link closed the loop.

The depth ceiling is a separate, weaker guard for the legitimate case: composition that is
genuinely nested but not circular.

## Pre-flight validation, before anything is spent

The chain guard is a run-time refusal, and it fires after the run has started. Where the answer is
knowable earlier, it should be given earlier: **validate the call graph before execution**, in the
same gate the v2 already runs between building the DAG and starting to spend (its phase 2).

What is provable statically:

- a cycle **inside** the flow's own graph — the v2 already checks this;
- a cycle in the **flow-call graph** reachable from this flow: A → B → C → A, walking
  `fluxBox`/`libraryNode` targets transitively. This is new, and it is the combinatorial case:
  B must not be reachable from C, and C must not reach A or B, all the way down;
- a chain that would exceed the depth ceiling before it runs a single node.

Refusing here turns a bill into an error message, and gives the author the chain to fix.

**What it cannot prove** is termination in general — the loop conditions read data that does not
exist until the run happens. That is why the static check does not replace the runtime budget in
`TASK-S4`; the two answer different questions.

## Scope

**In.** A `parentRunId` chain and a visited-flow set derived from it, plus a depth counter. All
three must survive the move to child workflows, so put them in the run context that already crosses
that boundary rather than in a closure.

**In.** Two distinct refusals, because they are different mistakes and deserve different messages:
- **Cycle** — the flow being called is already on the call stack. Always refused; there is no
  legitimate case.
- **Depth** — the stack is deeper than the ceiling. Refused with a message naming the chain, so
  the author can see which composition got too deep.

**Cycle: refused always, no configuration.** It is not a tunable, because there is no depth at
which calling back into a waiting ancestor becomes correct.

**Assumption to confirm — depth ceiling of 3.** Chosen because it covers composition of reusable
building blocks without allowing accidental deep nesting; make it an env var so it can be raised
without a deploy. **If real flows already nest deeper than three, this number is wrong** — measure
before shipping (see below).

**Out.** Changing what a sub-flow does when it runs legitimately. This task only refuses.

## Verification

- **Negative control (required).** Build two flows referencing each other, run one, and watch the
  recursion happen on `main` — the process degrades and the run never returns. Then add the guard
  and confirm it refuses on the second entry with the cycle message. Seeing the failure first is
  what makes the ceiling defensible.
- **Measure before refusing** (PLAN §3.3.2), and this one is not optional. Walk the stored flows:
  for every flow containing a `fluxBox` or `libraryNode`, compute the real maximum nesting depth
  and detect existing cycles. Classify each as *would still work* or *would now be refused*, and
  drive the second count to zero — either by raising the ceiling or by contacting the owners of
  the flows that would break. A ceiling that refuses working customer flows is worse than the
  recursion it prevents.
- Report any **existing cycles** found separately. Those flows are already broken; the guard makes
  the breakage legible instead of fatal.

## Done when

Cycles are refused with a clear message, depth is capped by an env-configurable ceiling, the stored
flows were measured and no working flow is refused, and the guard lives in state that survives the
move to child workflows.

## Files

`back/src/app-api/flux/flux.service.ts:5400, 5611–5622, 5717, 5732, 5815` · the run context threaded
through `apiV2` · new env var + `env-vars-sync`
