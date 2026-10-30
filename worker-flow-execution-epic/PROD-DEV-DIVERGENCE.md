# Keeping a task's scope out of dev's backlog

A task branch in this epic is cut from **production**. Dev is normally far
ahead of it — on 2026-09-21 `back`'s `master` was **278 commits** ahead of
`production`, none behind. That gap produces two failures, and they point in
opposite directions, which is why one rule does not cover both.

**Scope leak into the task.** A file read against production looks unfinished
or wrong, and the real reason is that dev already changed it. Fixing it inside
the task drags someone else's unshipped work into this demand, and the task's
PR to production then carries changes nobody asked this task for.

**Silent loss on the merge to dev.** The task rewrites a file whose dev copy
carries additions its base never had. The merge looks clean, the additions
disappear, and no test complains — the task's tests were written against
production, so they assert the production shape is correct.

The second one is the dangerous one: nothing fails.

## The check

```
.claude/tasks/worker-flow-execution-epic/scripts/prod-dev-divergence.sh <repo> [path ...]
```

Branch pairs are built in: `back` and `front` compare `production` against
`master`/`main`, `worker` compares `main` against `develop`. With no paths it
lists every file dev changed; with paths it prints the dev-only lines for the
files the task touches.

Run it **twice**: once before starting, to scope the task; once before merging
the task into dev, to see what the merge must preserve.

## Rule

- A difference that exists only because dev moved is **out of scope** for a
  task branched from production, unless the task names it.
- When merging a task into dev, every dev-only line in a file the task rewrote
  must be preserved deliberately. Do not let the merge resolve it.
- A frozen test oracle written against production will **assert the production
  shape**. On dev, that is not a bug in dev — it is the oracle telling the
  truth about a different base. Update the oracle at merge time with a note
  saying which base it now describes.

## Measured on 2026-09-21, for A1 (`back`, `production` 3804a524 → `master` 92c25e5a)

| Path | Dev-only | Verdict |
|---|---|---|
| `src/shared/integration/integration-executable-node.ts` | `MIGRATED_INTEGRATION_PROVIDERS` gains `clickup` and `quickbooks` | **Must survive the merge.** A1 moved this set onto the registry's `thirdPartyIntegration` entry, in a file dev does not have, so a clean merge drops both providers with nothing failing. |
| `src/app-api/flux/flux.service.ts` | substitution rework (`substitutedData`, `nodeSubstitutionSchema` threaded into the node call) plus formatting | Out of A1's scope; A1 only touches `isTemporalNode` and `canUsePrefetchForFlow` in this file. |
| `src/temporal/single-node-legacy/legacy-allowlist.ts` | `imageGenerator` reordered inside the array | Cosmetic. Same membership, so the registry derives the same set either way. |
| `src/app-api/flux/prefetch/is-non-executable.ts` | none | Identical — the canonical non-executable set is the same on both. |

**Consequence already recorded elsewhere:** `clickup` and `quickbooks` being
worker-routed on dev means TASK-A10's premise ("clickup is the only executable
provider still running inline") holds for **production only**. On dev that work
is done, and A10 is about getting it to production, not implementing it.
