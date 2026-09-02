# A2 — Promote the finished modules and providers

**Goal:** get the six node types and two integration providers that already have worker modules
into production. This is
release work, not engineering: verify what is in test against the definition of done, and promote it.

**Depends on:** A1. **Blocks:** nothing, but it is the cheapest coverage in the epic.

## Why

**Updated 2026-08-24.** `mcpNode` shipped: it is in the worker enum, has its `mcp` module, is in
`isTemporalNode`, is in the legacy allowlist, and `mcp` is a migrated integration provider. It is
done and out of this task. **Six** node types remain.

**Corrected 2026-09-02 — only production counts.** Six types have complete worker modules that are
**not in `worker@origin/main`**. Where they sit before that — dev, staging, a chore branch — is the
release pipeline's business, not this spec's: as of 2026-09-02 they are in test on the dev
environment, and an `imageGenerator` module is in progress there too (A5 builds on it). The one
fact this task cares about is that production does not run them:

| Node type | Worker module | In `worker@origin/main`? |
|---|---|---|
| `voiceBoxNode` | `voice-generator` | no |
| `webCrawling` | `web-crawling` | no |
| `webSearch` | `web-search` | no |
| `commandContentNode` | `large-memory` | no |
| `pullData` | `pull-data` | no |
| `pushData` | `push-data` | no |

The first draft framed this as reconciling a chore branch that had "reached no environment"; that
framing is dropped. If the dev line and production have diverged, resolving it is a step of the
promotion — union resolution, per `worker-thirdparty-integration-migration/DEV-RECONCILIATION.md` —
not the task's premise.

**There is a second queue, of the same shape** (analysis §10.3). Integration *providers* are
promoted through the same pipeline. `mcp` shipped on 2026-08-24; **two remain** — `clickup` and
`quickbooks` — in test, absent from both production refs. (`clickup` did reach
`back@origin/production` on 2026-08-27, but as an OAuth connection adapter under
`app-api/integrations/`, not as a worker-routed provider in `MIGRATED_INTEGRATION_PROVIDERS`; the
worker-routed half is what this task promotes.) This task covers them too; the promotion mechanics
are identical and splitting them would mean walking the same pipeline twice.

**Check staging before shipping.** As of 2026-08-21 `back@origin/staging` still carried the
pre-release six providers while production carried eight — staging is behind production for this
file. Confirm whether that is deliberate; if it is not, promoting through a stale staging will
either re-break production or silently pass.

## Scope

**In.** Verify each of the six node types and both providers against PLAN §3.4's seven-point
definition of done, and ship what passes.

**Out.** Any change to what those modules do. If a module fails the definition of done, that
failure becomes its own task — do not fix it inside the promotion.

## Steps

1. Take the dev line as it is in test. If it and production have diverged, merge with **union
   resolution — keep both sides, lose no code.** `-X ours` is banned here; it produces a clean
   merge that silently discards a side. `worker-thirdparty-integration-migration/DEV-RECONCILIATION.md`
   records the policy that was already paid for once; follow it.
2. Verify the merged `nodes.types.ts` has all six enum entries and each has its full
   registration chain (module, activity, binding, proxy, workflow case).
3. **Verify the back side exists.** A worker module without a registry entry is a stranded module
   (see A3). For each of the six, confirm the back actually routes it — and if not, add the
   registry entry here, behind the flag from PLAN §3.2.
4. Ship: `develop` → soak → `staging` → soak → PR to `main`.

## Verification

- **Negative control (required).** For one of the six, remove its case from
  `process-single-node.workflow.ts`, run its spec, and record the failure. The workflow's default
  branch throws "Node type X not supported" — confirm that is what you see, because that is the
  exact failure mode a missing registration produces in production.
- Per node, in the local Docker stack: run it in a flow, confirm the activity appears in Temporal,
  `node_executions` goes PENDING → COMPLETED, and the downstream node receives the output.
- Confirm no double execution: with the flag on, the inline handler must not fire. Log-assert it.

## Done when

All six node types are in `main`, the two pending providers are in production, and each satisfies
PLAN §3.4.

## Files

`worker/src/modules/nodes/{voice-generator,web-crawling,web-search,large-memory,pull-data,push-data}/` ·
`worker/src/modules/nodes/nodes.types.ts` · `worker/src/modules/temporal/**` · the A1 registry
