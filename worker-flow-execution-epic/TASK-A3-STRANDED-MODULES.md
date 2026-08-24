# A3 — Reach the stranded worker modules

**Goal:** resolve `sqlQuerier` and `audioReaderNode`, which have worker modules **in production**
that no dispatch gate routes to.

**Depends on:** A1 (the invariant spec that detects this). **Blocked on:** decision **D4**.

## Why

Both node types are in the worker's `NodeType` enum on `origin/main` and have complete modules.
Neither is in `isTemporalNode`'s seven, and neither resolves to a migrated integration provider — so
nothing in the back ever starts a workflow for them (analysis §9.4). `audioReaderNode` still has
its inline handler in `flux.service.ts` (~7911), and that is what actually runs. This is the
concrete case the A1 invariant spec flags: `workerModule: true` with `dispatch: 'inline'`.

This task is where the analysis stopped and a decision is required: **was the migration paused
deliberately, or was the routing simply forgotten?** (PLAN §7, D4.) The two answers produce
opposite work.

## Scope

**If the migration is to be finished** (expected): add both to the A1 registry behind the flag,
flip in a separate deploy, delete the inline twins, and give each a negative-control test.

**If the modules are to be abandoned:** delete them from the worker, remove the enum entries, and
record why in the module's place — a deleted module with no explanation invites someone to rewrite
it in six months.

**Out.** Rewriting either module. They exist and were presumably tested when written; this task
routes or removes, it does not redesign.

## Steps

1. Answer D4. Check the git history of both worker modules and of `isTemporalNode` — if the module
   landed and the routing PR never followed, that is the answer.
2. Registry entries behind the flag; deploy disabled.
3. Prove each against the real inline behaviour: same input, compare worker output to inline
   output field by field. `audioReaderNode` in particular has an inline version to diff against,
   which is a luxury the other migrations do not have — use it.
4. Flip the flag in a separate deploy.
5. Delete the inline twins (this is C1's pattern, applied here as part of the node's own task).

## Verification

- **Negative control (required).** With the flag on, break the worker module's `process()` and
  confirm the run fails — rather than silently falling back to the inline handler. A fallback that
  masks the worker being broken is worse than the stranding this task fixes.
- Field-by-field output diff, worker vs inline, on at least three real stored node
  configurations per type.
- After the twin is deleted: confirm the flag-off path fails loudly rather than doing nothing.

## Done when

Neither type has `workerModule: true` with `dispatch: 'inline'`; the A1 invariant spec passes with
no `strandedReason` entries; the inline twins are gone.

## Files

`worker/src/modules/nodes/{sql-querier,audio-transcriber}/` · `back/src/app-api/flux/flux.service.ts`
(inline `audioReaderNode` ~7911, `sqlQuerier` ~4479) · the A1 registry
