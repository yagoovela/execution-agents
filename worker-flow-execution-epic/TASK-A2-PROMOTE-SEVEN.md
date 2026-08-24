# A2 — Promote the finished modules and providers

**Goal:** get the seven node types that already have worker modules into production. This is
release work, not engineering — but it is blocked on a branch reconciliation nobody has done.

**Depends on:** A1. **Blocks:** nothing, but it is the cheapest coverage in the epic.

## Why

**Updated 2026-08-24.** `mcpNode` shipped: it is in the worker enum, has its `mcp` module, is in
`isTemporalNode`, is in the legacy allowlist, and `mcp` is a migrated integration provider. It is
done and out of this task. **Six** node types remain.

Six types have complete worker modules that are not in production, and they are all on **one branch
that was never merged anywhere** — not `develop`, not `staging` (analysis §12):

| Node type | Worker module | Line |
|---|---|---|
| `voiceBoxNode` | `voice-generator` | the merge branch |
| `webCrawling` | `web-crawling` | the merge branch |
| `webSearch` | `web-search` | the merge branch |
| `commandContentNode` | `large-memory` | the merge branch |
| `pullData` | `pull-data` | the merge branch |
| `pushData` | `push-data` | the merge branch |

`origin/chore/merge-868k8twjb-develop-20260805` carries all six. **The gap widened rather than
closed:** the `mcpNode` line went all the way to production while these six are still parked on a
chore branch that has reached no environment. Whatever is blocking that merge has now been blocking
it while a parallel line shipped past it — worth finding out what, before this task starts.

**There is a second queue, of the same shape** (analysis §10.3). Integration *providers* are
promoted through the same pipeline. `mcp` shipped on 2026-08-24; **two remain** — `clickup` and
`quickbooks`, present on `worker@origin/develop` and in `MIGRATED_INTEGRATION_PROVIDERS` on
`back@origin/master`, absent from both production refs. This task covers them too; the promotion
mechanics are identical and splitting them would mean reconciling the same branches twice.

**Check staging before shipping.** As of 2026-08-21 `back@origin/staging` still carried the
pre-release six providers while production carried eight — staging is behind production for this
file. Confirm whether that is deliberate; if it is not, promoting through a stale staging will
either re-break production or silently pass.

## Scope

**In.** Reconcile the two lines, verify each of the seven against PLAN §3.4's seven-point
definition of done, and ship.

**Out.** Any change to what those modules do. If a module fails the definition of done, that
failure becomes its own task — do not fix it inside the promotion.

## Steps

1. Create the reconciliation branch and merge both lines. Expect conflicts: the dev branches moved
   a long way while the migration was in flight. **Union resolution — keep both sides, lose no
   code.** `-X ours` is banned here; it produces a clean merge that silently discards a side.
   The `worker-thirdparty-integration-migration/DEV-RECONCILIATION.md` records the policy that
   was already paid for once; follow it.
2. Verify the merged `nodes.types.ts` has all seven enum entries and each has its full
   registration chain (module, activity, binding, proxy, workflow case).
3. **Verify the back side exists.** A worker module without a registry entry is a stranded module
   (see A3). For each of the seven, confirm the back actually routes it — and if not, add the
   registry entry here, behind the flag from PLAN §3.2.
4. Ship: `develop` → soak → `staging` → soak → PR to `main`.

## Verification

- **Negative control (required).** For one of the seven, remove its case from
  `process-single-node.workflow.ts`, run its spec, and record the failure. The workflow's default
  branch throws "Node type X not supported" — confirm that is what you see, because that is the
  exact failure mode a missing registration produces in production.
- Per node, in the local Docker stack: run it in a flow, confirm the activity appears in Temporal,
  `node_executions` goes PENDING → COMPLETED, and the downstream node receives the output.
- Confirm no double execution: with the flag on, the inline handler must not fire. Log-assert it.

## Done when

All six node types are in `main`, the two pending providers are in production, each satisfies
PLAN §3.4, and the two branch lines no longer exist as divergent heads.

## Files

`worker/src/modules/nodes/{voice-generator,web-crawling,web-search,large-memory,pull-data,push-data}/` ·
`worker/src/modules/nodes/nodes.types.ts` · `worker/src/modules/temporal/**` · the A1 registry
