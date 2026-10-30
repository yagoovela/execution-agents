# A10 — Route the ClickUp provider through the worker

**Goal:** give `clickup` a worker adapter, so a `thirdPartyIntegration` node configured with
`provider: 'clickup'` executes through the worker like every other migrated provider, instead of
through the inline `back` path it has used since it shipped.

**Depends on:** A1. **Relates to:** A2 — A2 promotes providers whose worker half is *finished but
not yet in production*; this is not that shape. ClickUp's worker half was never built, so this is
new work, not a promotion, and it gets its own task rather than reopening A2's already-corrected
scope. **ClickUp card:** [868m7kbf0](https://app.clickup.com/t/868m7kbf0), child of Wave 3's card
[868m0vk0p](https://app.clickup.com/t/868m0vk0p).

## Why

**Added 2026-09-21**, the same day A2 was re-validated and found that `clickup`'s product feature
had shipped (ClickUp task [868j988uj](https://app.clickup.com/t/868j988uj), back PR #1922, front PR
#2134, 2026-08-27) entirely on the inline OAuth-connection path — while this epic was already
running. Re-measured against `back@origin/production` `3804a524`, `worker@origin/main` `3e4c93a`,
`front@origin/production` `fdeddbbc`:

- The front registers **11** providers
  (`front/src/components/ThirdPartyIntegration/registry.ts`, the `registerProvider(...)` calls):
  `wordpress`, `slack`, `zapier` (three configs — pull, push, poll — one provider),
  `notion`, `stripe`, `mcp`, `hubspot`, `microsoft`, `pinecone`, `supabase`, `clickup`.
- **Nine** have worker adapters under
  `worker/src/modules/nodes/third-party-integration/adapters/`: `stripe`, `wordpress`, `slack`,
  `notion`, `zapier`, `hubspot`, `supabase`, `pinecone`, `mcp`.
- **`microsoft` is correctly excluded and is not a gap.** Its config
  (`front/src/components/ThirdPartyIntegration/providers/microsoft/MicrosoftConfig.ts`) declares
  `supportsPull: false` and `supportsPush: false` — a connection-only provider (Microsoft 365 OAuth)
  that executes no pull or push action. It has no back execution adapter either, and needs none.
  Stating this explicitly matters because "11 front providers vs. 9 worker adapters" invites the
  conclusion that there are two gaps, when there is one.
- **`clickup` is the only executable provider still inline.** Its config
  (`front/src/components/ThirdPartyIntegration/providers/clickup/ClickUpConfig.ts`) declares
  `supportsPull: true` and `supportsPush: true`. Its back execution adapter,
  `back/src/app-api/integrations/adapters/clickup.adapter.ts`, is registered in
  `IntegrationsService`'s constructor (`this.adapters.set('clickup', clickUpAdapter)`,
  `back/src/app-api/integrations/integrations.service.ts`) and `IntegrationProvider.CLICKUP` exists
  in `back/src/entities/user_integration.entity.ts`. **Nothing exists in the worker** — no adapter
  file, no module registration — and `clickup` is absent from `MIGRATED_INTEGRATION_PROVIDERS`
  (`back/src/shared/integration/integration-executable-node.ts`).

**This is the case the new standing rule (`PLAN.md` §3.6) exists to prevent.** ClickUp's product
feature and its worker routing were built by different pipelines on different timelines, and nothing
connected them — the epic acquired migration work it should never have needed, discovered only
because A1's re-validation happened to look at `isWorkerRoutedIntegration`. Without the rule, the
next integration (QuickBooks — `PLAN.md` §9 — is the named next case) repeats it.

## Scope

**In.** A `clickup` adapter under `worker/src/modules/nodes/third-party-integration/adapters/`,
following the shape of the nine adapters that already exist there (adapter + `.spec.ts` + any
`clickup-http.ts` transport helper the port needs, per the pattern `hubspot`/`notion`/`slack` set).
Coverage for every pull object type and every push action the front's `ClickUpConfig.ts` exposes —
not a subset chosen for convenience.

**In.** `clickup` added to `MIGRATED_INTEGRATION_PROVIDERS`, behind the flag from `PLAN.md` §3.2,
and an A1-registry entry with `hasInlineTwin: true` until C1's deletion step runs.

**In.** A `PORTED_FROM.md` entry for the new adapter, in the same file and the same shape as the
existing entries (source SHAs, what was ported vs. dropped, the error-classification mapping) — see
`worker/src/modules/nodes/third-party-integration/PORTED_FROM.md` for the convention every prior
provider followed.

**Out.** Redesigning what the ClickUp integration does — same pull object types, same push actions,
same payload shapes as the inline adapter. This ports and routes; it does not change behaviour.

**Out.** Deleting the inline `clickup.adapter.ts` twin. That happens in a **separate deploy after
the flag flip**, per C1's pattern (`TASK-C1-RETIRE-INLINE-PATHS.md`) — not in the same PR as this
task, and not before the worker path has run in production behind the flag.

## Steps

1. Build the `clickup` adapter (and any HTTP helper it needs) under
   `worker/src/modules/nodes/third-party-integration/adapters/`, porting
   `back/src/app-api/integrations/adapters/clickup.adapter.ts`'s runtime pull/push subset — not its
   editor-time OAuth operations, same split every prior adapter made.
2. Register it in the worker's provider registry (`third-party-integration.module.ts`'s factory,
   per the pattern P2 onward set).
3. Add `clickup` to `MIGRATED_INTEGRATION_PROVIDERS`, behind the flag.
4. Confirm the A1 registry picks it up with `hasInlineTwin: true`.
5. Add the `PORTED_FROM.md` entry.
6. Ship: `develop` → soak → `staging` → soak → PR to `main`, flag off. Flip the flag in a separate
   deploy once the negative control and the parity check below both pass.

## Verification

- **Negative control (required).** With the flag on, break the worker adapter (revert one pull
  handler to throw) and confirm the run fails **loudly** — the flow reports the failure, it does not
  silently fall back to the inline path. A fallback that masks a broken adapter is worse than the
  inline path it replaces, because it hides the exact defect this task exists to catch.
- **Field-by-field output parity, worker vs. inline, on at least three real stored ClickUp
  configurations**, covering both a pull and a push action each. Diff the outputs field by field —
  not a shape check, an equality check.
- **Measure before refusing (required).** After the flag flips, confirm the set of
  `thirdPartyIntegration` nodes now taking the worker path is exactly the old
  `MIGRATED_INTEGRATION_PROVIDERS` set plus ClickUp's — classify every node whose routing changed,
  and drive to zero any node whose provider is *not* ClickUp but whose path moved anyway. That is the
  failure mode of a registry-entry mistake, not a ClickUp defect, and it would otherwise ship silent.
- **No-double-execution log assertion.** With the flag on, assert with a log or a counter that
  exactly one execution occurred per dispatch for a ClickUp node — this is R1 (`PLAN.md` §6), the
  same guard every other provider promotion required.

## Done when

`clickup` has a worker adapter, a `PORTED_FROM.md` entry, and a `MIGRATED_INTEGRATION_PROVIDERS`
entry, shipped behind a flag and flipped in a separate deploy; every pull object type and push
action the front exposes has worker-side coverage with measured field-by-field parity against the
inline path; the negative control and the no-double-execution assertion both passed; the inline
`clickup.adapter.ts` still exists (its deletion is C1's, after this task's flag flip, not this
task's own Done-when).

## Files

`worker/src/modules/nodes/third-party-integration/adapters/` (new `clickup.adapter.ts`,
`clickup.adapter.spec.ts`, and any `clickup-http.ts`) ·
`worker/src/modules/nodes/third-party-integration/third-party-integration.module.ts` (provider
registry factory) · `worker/src/modules/nodes/third-party-integration/PORTED_FROM.md` (new entry) ·
`back/src/app-api/integrations/adapters/clickup.adapter.ts` (port source, read-only for this task) ·
`back/src/shared/integration/integration-executable-node.ts`
(`MIGRATED_INTEGRATION_PROVIDERS`) · the A1 registry
