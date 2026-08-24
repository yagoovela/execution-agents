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

## Scope

**In.** A depth counter carried in the run context, and a visited-flow set. Both must survive the
move to child workflows, so put them in the run context that already crosses that boundary rather
than in a closure.

**In.** Two distinct refusals, because they are different mistakes and deserve different messages:
- **Cycle** — the flow being called is already on the call stack. Always refused; there is no
  legitimate case.
- **Depth** — the stack is deeper than the ceiling. Refused with a message naming the chain, so
  the author can see which composition got too deep.

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
