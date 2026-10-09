# C1 — Retire the inline paths and the cross-node writes

**Goal:** delete what the migration replaced, so the back stops being a second implementation.

**Depends on:** per node, on that node's A-track task. **This is not a sweep at the end** — each
node's twin is deleted as part of proving that node, while the behaviour is fresh. This file is
the shared procedure those tasks follow, plus the two pieces that only make sense once.

**Card (PLAN §3.1):** one, in Wave 6, for the once-only half below. The per-node deletions are a
Done-when line of each A-track card, not cards of their own.

**Removed from Wave 3 on 2026-10-02.** C1 had a Wave 3 row for its per-node half, but that half is a Done-when line of each A-track card, not a deliverable of its own, so the row counted as an unstarted item in a wave whose nodes were already deleting their twins. Verified on `back@origin/production` `bc727827`: A4's `reportBuilderNode()` and dispatch case are gone, A5's `imageGenerator` dispatch case is gone (its dead method body stays, by precedent); A9's inline delivery block goes with its production deploy. C1 is tracked once, in Wave 6 ([868m0vm8g](https://app.clickup.com/t/9011479430/868m0vm8g)).

**Removida da Wave 3 em 02/10/2026.** A C1 tinha uma linha na Wave 3 para a metade por nó, mas essa metade é uma linha do Done-when de cada card da trilha A, não uma entrega própria, então a linha contava como item não iniciado numa wave cujos nós já apagavam seus gêmeos. Verificado em `back@origin/production` `bc727827`: o `reportBuilderNode()` e o case de dispatch da A4 sumiram, o case de dispatch do `imageGenerator` da A5 sumiu (o corpo morto do método fica, por precedente); o bloco de entrega inline da A9 sai com o deploy dela em produção. A C1 é acompanhada uma vez só, na Wave 6 ([868m0vm8g](https://app.clickup.com/t/9011479430/868m0vm8g)).

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
with `addConnectToNodes` (`back/src/app-api/folw/contants.ts`), which calls `modifyData` to merge the producer's output into the **target** node's data. That
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
`back/src/app-api/folw/contants.ts` (`addConnectToNodes`, `modifyData`) · the A1 registry
