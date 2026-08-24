# S4 — A loop ceiling the node cannot switch off

**Goal:** a maximum number of iterations that holds regardless of how the node is configured.

**Depends on:** nothing. Best done with S1 — same class of guard, same test harness.
**Severity:** high (review §1.2).

## Why

`evaluateLoopCondition` (`folw/helpers/helpers.ts:2075–2110`) applies the limit on one branch only:

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

## Scope

**In.** A hard maximum applied on **both** branches, independent of `loopBehavior` and of
`loopCount`. The node's own limit still applies where it is lower — this is a ceiling, not a
replacement.

**Assumption to confirm — the system maximum is an env var, defaulted generously.** The point is to
stop the unbounded case, not to second-guess legitimate long loops. Set it well above the largest
real loop found in the measurement below.

**In.** When the system ceiling stops a loop, say so distinctly. `loopStatus.reason` already carries
a human-readable reason — `Loop limit exceeded (n/m)` — so the new case needs its own wording, or
a user will read "limit exceeded" and go looking for a limit they never set.

**In.** The same ceiling must apply to `arrayNode`, which iterates a list rather than a condition.
A `processorArray` of a hundred thousand items is the same runaway with a different shape.

**Out.** Changing `loopBehavior`'s meaning. If `'stop'` bypassing the counter is intentional, this
task keeps that intent and adds a ceiling above it.

## Verification

- **Negative control (required).** A condition node with an always-true condition and
  `loopBehavior` set to anything but `'continue'`: watch it loop without bound on `main`, then
  confirm the ceiling stops it and the reason names the system limit rather than the node's.
- **Measure before refusing** (PLAN §3.3.2): find the largest `loopCount` and the largest
  `processorArray` in the stored flows, and set the ceiling above both with margin. Report the
  distribution, not just the maximum — a ceiling chosen from one outlier is a ceiling nobody
  trusts.
- Confirm the UI still shows the node's own limit when that is what stopped the loop; the two
  reasons must not be confused.

## Done when

No node configuration can produce an unbounded loop, the ceiling sits above every real loop in the
stored data, and the two stop reasons are distinguishable.

## Files

`back/src/app-api/folw/helpers/helpers.ts:2075–2110` ·
`back/src/app-api/flux/flux.service.ts:6742–6812` (condition), `:3738` (array) · new env var + `env-vars-sync`
