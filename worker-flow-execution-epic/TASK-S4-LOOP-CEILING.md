# S4 — Execution budget: per node, per run, per chain

**Goal:** make it impossible for a run to execute without bound, whatever shape the loop takes.

Three limits, because they catch different things and none of them subsumes the others:

| Limit | Catches | Misses |
|---|---|---|
| **X — iterations per node** | the runaway loop on one node | a loop that walks across many nodes |
| **Y — node executions per run** | every shape, including ones nobody predicted | nothing — but only within one run |
| **Chain total** | recursion that resets Y by starting a new run | — |

**Depends on:** nothing. Best done with S1 — same class of guard, same test harness.
**Severity:** high (review §1.2).

## Why

`evaluateLoopCondition` (`folw/helpers/helpers.ts`) applies the limit on one branch only:

```
if (loopBehavior === 'continue') finalResult = userConditionResult && loopLimitCheck;
else                             finalResult = userConditionResult;
```

On the second branch the limit is computed, reported to the UI through `loopStatus` and the
`condition-loop-status` socket event, and then **not applied**. And on the capped branch the limit
itself is `node.data.loopCount` — user data.

So an always-true condition on a node whose behaviour is not `'continue'` loops with no ceiling.
Whether `'stop'` was meant to bypass the counter is a product question; the engineering point is
that a system-level maximum should not be reachable from node configuration.

## Why the static check is not enough, and why Y is the one that matters

There are three defences and they belong in this order:

1. **Before the run — graph validation.** Refuse what can be proven wrong without spending anything:
   cycles inside the graph, and a flow already on the call chain (`TASK-S1`). Cheapest, and it gives
   the author a real error instead of a bill.
2. **During the run — X, per node.** Stops the common case: one node looping on a condition that
   never turns false.
3. **During the run — Y, per run, and the chain total.** The backstop.

**The third is not redundant, it is the only guarantee.** Whether a flow terminates is not decidable
by looking at it — the loop condition reads data that does not exist until the run happens. A static
check can prove *some* flows wrong; it can never prove the rest right. So no amount of pre-flight
validation removes the need for a budget that counts what actually executed and stops.

That is also the argument against anyone proposing to drop Y once the graph validation is good: the
validation and the budget answer different questions, and only the budget answers the one that
matters at 3 a.m.

## Scope

**In — X, per node.** A hard maximum applied on **both** branches, independent of `loopBehavior`
and of `loopCount`. The node's own limit still applies where it is lower — this is a ceiling, not a
replacement.

**Assumption to confirm — the system maximum is an env var, defaulted generously.** The point is to
stop the unbounded case, not to second-guess legitimate long loops. Set it well above the largest
real loop found in the measurement below.

**In.** When the system ceiling stops a loop, say so distinctly. `loopStatus.reason` already carries
a human-readable reason — `Loop limit exceeded (n/m)` — so the new case needs its own wording, or
a user will read "limit exceeded" and go looking for a limit they never set.

**In — X applies to `arrayNode` too**, which iterates a list rather than a condition. A
`processorArray` of a hundred thousand items is the same runaway with a different shape.

**In — Y, node executions per run.** A counter of executions, not of distinct nodes: a node that
runs forty times spends forty. When it is exhausted the run **terminates deterministically** with a
terminal state naming the budget — it does not simply stop being scheduled, and it does not die. A
run that ends ambiguously is worse than one that ends refused, because nobody can tell it from a
hang.

**In — the chain total.** Y is per run, and a sub-flow starts a new run (`TASK-S1`), so a per-run
budget is reset by nesting exactly as the spend ceiling was. The counter resolves the chain root and
accounts against it. **This is the same mechanism `TASK-S3` needs for cost** — one counter carrying
two limits, resolved at the same place, rather than two independent accountants that can disagree.

**In — the budget protects the workflow, not only the wallet.** Every node execution is activities
scheduled and completed in Temporal history. Y bounds history growth as a side effect, which is the
other half of what `TASK-B4`'s `continueAsNew` is for.

**Out.** Changing `loopBehavior`'s meaning. If `'stop'` bypassing the counter is intentional, this
task keeps that intent and adds a ceiling above it.

## Verification

- **Negative control (required).** A condition node with an always-true condition and
  `loopBehavior` set to anything but `'continue'`: watch it loop without bound on `main`, then
  confirm the ceiling stops it and the reason names the system limit rather than the node's.
- **Negative control for Y (required).** Build a flow that loops across *several* nodes rather
  than on one — the shape X cannot see — and confirm it runs unbounded on `main`, then confirm Y
  stops it with a terminal state naming the budget. Then nest that flow two levels deep and confirm
  the **chain** total stops it, rather than each level getting a fresh Y.
- **Measure before refusing** (PLAN §3.3.2): find the largest `loopCount` and the largest
  `processorArray` in the stored flows, and the largest number of node executions any real run has
  produced. Set X and Y above all of them with margin, and report the distribution rather than the
  maximum — a ceiling chosen from one outlier is a ceiling nobody trusts. Report the
  distribution, not just the maximum — a ceiling chosen from one outlier is a ceiling nobody
  trusts.
- Confirm the UI still shows the node's own limit when that is what stopped the loop; the two
  reasons must not be confused.

## Done when

No node configuration and no graph shape can produce an unbounded run: X bounds one node, Y bounds
the run, and the chain total bounds nesting. Every ceiling sits above the largest real value in the
stored data. A run that hits any of them ends in a terminal state that names which one, and the
three reasons are distinguishable from each other and from the node's own limit.

## Files

`back/src/app-api/folw/helpers/helpers.ts` (`evaluateLoopCondition`) ·
`back/src/app-api/flux/flux.service.ts` (`conditionNode()`; the inline `arrayNode` branch) ·
`back/src/app-api/flux/scheduler.ts` (the counter lives with the loop that dispatches) ·
the chain-root accounting shared with `TASK-S3` · new env vars + `env-vars-sync`
