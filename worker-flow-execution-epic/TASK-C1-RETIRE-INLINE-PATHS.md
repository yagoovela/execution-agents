# C1 — Retire the inline paths and the cross-node writes

**Goal:** delete what the migration replaced, so the back stops being a second implementation.

**Depends on:** per node, on that node's A-track task. **This is not a sweep at the end** — each
node's twin is deleted as part of proving that node, while the behaviour is fresh. This file is
the shared procedure those tasks follow, plus the two pieces that only make sense once.

## Why deletion is part of the migration, not cleanup

Two implementations of one node do not coexist neutrally. They diverge, and the divergence is
silent — someone fixes a bug in the inline handler that the worker module still has. Worse, while
both exist, a flag misconfiguration means **double execution**: a duplicated Stripe charge, a
duplicated Slack message (PLAN §6, R1).

## Scope

**Per node (owned by the A-track task, procedure defined here):**

1. The inline handler in `flux.service.ts` and its dispatch branch are deleted, not commented out
   and not left behind a dead flag.
2. Anything that only that handler used goes with it. `flux.service.ts` is ~9,500 lines; a
   migration that only adds is a migration that made the file worse.
3. The A1 registry entry loses `hasInlineTwin`.

**Once, and this is the load-bearing half — the cross-node writes.** Every inline handler ends
with `addConnectToNodes` (`back/src/app-api/folw/contants.ts:2032`), which calls `modifyData`
(`:2018–2024`, `:2056–2062`) to merge the producer's output into the **target** node's data. That
is the mechanism that makes mixed-mode parallelism unsafe (analysis §7.4b) and the reason B5 needs
its gate.

Once a node runs in the worker, its output reaches downstream nodes through `persistNodeSuccess`
writing its **own** row. The cross-node write is then not merely redundant — it is a second writer
on a row someone else owns.

**Out.** Removing `addConnectToNodes` while any executable node type still runs inline. It is
correct for those. This task removes it path by path, as each path's last inline node leaves.

## Steps

1. Per node, as its A-task completes: delete handler, dispatch, dead helpers.
2. Track which call sites of `modifyData` / `addConnectToNodes` still have a live inline caller.
   When a call site's last caller is gone, delete the call site.
3. When the last executable inline node is migrated, `addConnectToNodes` should have no callers on
   the run path. If it still does, something was missed — that is the check, not a formality.

## Verification

- **Negative control (required).** Before deleting a handler, re-point the flag at the inline path
  and confirm the node still works. Then delete, and confirm the flag-off path now fails **loudly**
  rather than silently doing nothing. A deleted path that fails silently is indistinguishable in
  production from a node that produced empty output.
- **Double-execution guard.** For each migrated node, assert with a log or a counter that exactly
  one execution occurred per dispatch. Assert it, do not eyeball it — this is R1.
- After each `modifyData` call-site removal, run the flows that reach it and diff downstream node
  inputs against a pre-change run.

## Done when

No executable node type has two implementations; `addConnectToNodes` has no callers on the run
path; `flux.service.ts` is materially smaller and the reduction is stated in the PR.

## Files

`back/src/app-api/flux/flux.service.ts` (all inline handlers) ·
`back/src/app-api/folw/contants.ts:2018–2062, 2032` · the A1 registry
