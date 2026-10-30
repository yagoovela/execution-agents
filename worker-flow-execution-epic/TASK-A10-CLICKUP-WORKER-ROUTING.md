# A10 — Route the ClickUp provider through the worker

**Goal:** a `thirdPartyIntegration` node configured with `provider: 'clickup'` executes through the
worker in production, like every other migrated provider, instead of through the inline `back` path
it has used since it shipped.

**Depends on:** A1. **Relates to:** A2. **ClickUp card:**
[868m7kbf0](https://app.clickup.com/t/868m7kbf0), child of Wave 3's card
[868m0vk0p](https://app.clickup.com/t/868m0vk0p).

## Correction, 2026-09-28 — the worker half was built; it never reached production

The first version of this spec (2026-09-21) said ClickUp's worker half "was never built", and scoped
A10 as new work. **That is true of production only.** Re-validated at task start against
`back@origin/production` `94cb2e26`, `worker@origin/main` `ceff351`, `front@origin/production`
`493b05e9`, and against the dev lines `back@origin/master` `9abaca4c`, `worker@origin/develop` `4b39d74`:

- **The port exists.** Guilherme Ferreira ported the adapter on 2026-07-31 — worker commit
  `b027e55` ("port the ClickUp adapter to the Temporal worker"): `clickup.adapter.ts`,
  `clickup-http.ts`, a 550-line `clickup.adapter.spec.ts`, the `third-party-integration.module.ts`
  factory line, and a `PORTED_FROM.md` "P7 — ClickUp" entry. It is on `develop`, never on `main`.
  `PROD-DEV-DIVERGENCE.md` already recorded the dev-side half of this on 2026-09-21.
- **The port matches production.** Its cited back source, `ec87a9b2`, is byte-identical to
  `back@origin/production`'s `clickup.adapter.ts` (empty diff). Both send `Bearer ${accessToken}`.
  The worker's `user-integration.repo.ts` on `main` already decrypts `enc:v1:` tokens before the
  adapter sees them, so the P7 adapter needs nothing else from `main`.
- **It applies cleanly.** `b027e55` merges onto `worker@origin/main` with no conflict (`git
  merge-tree`, checked without touching the branch).
- **The dev version is a superset that production cannot use yet.** `develop` also carries
  `e9b85ca` ("authenticate ClickUp per connection", task `868kkgkqa`/`868kkgm1g`): `metadata.authKind`
  with `personal_token` and `user_oauth_app`. Back production's adapter has no `authKind`; that half
  exists only on `back@origin/master`. Porting `e9b85ca` would ship the worker half of another task
  ahead of its back half, so it is **out of scope** (`PROD-DEV-DIVERGENCE.md` rule).
- **The back entry on dev is entangled.** On `back@origin/master`, `'clickup'` entered
  `integrationProviders` in commit `4884ffb0` ("add the QuickBooks Online provider"), together with
  `'quickbooks'`. It cannot be cherry-picked; the production change is written by hand.

So A10 **promotes finished dev work to production**. It is closer to A2's shape than first stated,
but it stays its own task because it needs a routing change, a flag flip and a parity measurement.
A2 needed none of those.

The original finding still holds for production: the front registers 11 providers
(`front/src/components/ThirdPartyIntegration/registry.ts`); nine have worker adapters on `main`;
`microsoft` is connection-only (`supportsPull: false`, `supportsPush: false`) and is not a gap;
`clickup` (`supportsPull: true`, `supportsPush: true`) is the only executable provider still inline
in production. This is still the case `PLAN.md` §3.6 exists to prevent: the port was done, but
nothing tied it to the product feature's release to production.

## Decisions (approved 2026-09-28)

1. **Port base: P7, `b027e55` only.** Not `e9b85ca`, not the `develop` tip. P7 is what matches
   `back@origin/production`.
2. **The flag is the deploy order.** Production has no routing flag: the provider gate is the static
   `integrationProviders` set in `back/src/shared/node-dispatch/node-dispatch-registry.ts`, read by
   `isWorkerRoutedIntegration`. Pinecone (`4dce40f6`) and Supabase shipped by adding to that set.
   A10 satisfies `PLAN.md` §3.2 the same way, with two PRs in two separate deploys:
   - **Deploy 1 — worker PR to `main`.** The adapter is registered in the factory but unreachable:
     the back never dispatches a `clickup` node to the worker. Behaviour in production is unchanged.
   - **Deploy 2 — back PR to `production`** adding `'clickup'` to `integrationProviders`. This is
     the flip. Rollback is reverting this PR; the worker adapter can stay.

   No new env var is introduced.

## Scope

**In — worker (`feat/868m7kbf0` from `origin/main`).** Cherry-pick `b027e55`: `clickup.adapter.ts`,
`clickup-http.ts`, `clickup.adapter.spec.ts`, the factory line in `third-party-integration.module.ts`,
and the P7 `PORTED_FROM.md` entry. Amend the P7 entry's `getToken` note: tokens reach the adapter
already decrypted by `user-integration.repo.ts`; they are not plaintext at rest. The port covers every
action the front's `ClickUpConfig.ts` exposes: 5 pull object types (`tasks`, `task`, `spaces`,
`lists`, `comments`) and 3 push actions (`create_task`, `update_task`, `create_comment`).

**In — back (`feat/868m7kbf0` from `origin/production`).** `'clickup'` added to
`NODE_DISPATCH_REGISTRY.thirdPartyIntegration.integrationProviders`; regenerate
`node-dispatch-contract.json` (`pnpm generate:node-dispatch-contract`); update
`node-dispatch-registry.spec.ts`. Its test "still refuses an unknown provider" uses `clickup` as the
unknown provider, so it must switch to a provider that really is refused (`microsoft`). The registry
has no `hasInlineTwin` field. The first version of this spec named one; the real fields are
`inlineTwin`/`inlineTwinMethod` in the generated contract. The inline twin is the
`IntegrationsService` path, which stays.

**In — MCP can see ClickUp's picker values (added 2026-09-28, requested at task start).** Without
them an MCP client cannot author a working ClickUp node: `team`/`space`/`folder`/`list`/`status`/
`assignees` are account ids, and nothing on the MCP surface exposed them.
- back: `GET /mcp/v1/internal/integrations/:id/options/:field` (read scope) →
  `McpIntegrationsService.listOptions`. It checks reachability, takes the provider from the
  connection, strips caller-supplied `integrationId`/`connectedByUserId` from the context (the
  product's `resolveIntegration` does not refuse an unreachable id), and delegates to the same
  `IntegrationsService.getOptions` the canvas pickers use. Generic, so every provider's pickers work.
- back: `node-type-metadata.ts` documents clickup (provider, 5 pull types, 3 actions, fields).
- mcp-server (`feat/868m7kbf0` from `origin/main`): new tool `list_integration_options` (31 tools).
- docs (`docs/868m7kbf0` from `origin/main`): tool page, changelog, pt-br.
- MCP writes of a ClickUp node are released by the same back flip: `add_node`/`update_node` default
  their allowlist to `MIGRATED_INTEGRATION_PROVIDERS`.

**In — two pre-existing red tests on `back@origin/production`, fixed on request (small, test-only).**
`node-dispatch-invariants.spec.ts` had been red since `7067d2d0` left `audioReaderNode`'s unreachable
legacy arm in place; it is declared in `KNOWN_UNREACHABLE_ARMS` like `pullData`/`pushData` (C2
deletes all three). `execution_logs.retention.spec.ts` never compiled under ts-jest (0 of 9 tests
ran); its query mock is now typed.

**In — ClickUp `taskId` / `commentText` edges applied (approved 2026-09-28).** The front marks both
with `hasConnectionPoint`, but neither was in `NODE_REFERENCEABLE_FIELDS.thirdPartyIntegration` (back) /
`THIRD_PARTY_INTEGRATION_DATA_PAYLOAD_KEYS` (worker), so an edge into them was dropped on **both** paths
(pre-existing in production). Both keys are now in both lists; the MCP schema documents `taskIdData` /
`commentTextData`. Tests: worker `payload-builder.spec.ts` and back `third-party-companions.spec.ts`
(negative control: removing the keys turned 2 worker and 1 back test red), plus both drift oracles.
ClickUp's other connection-point fields (`name`, `description`) were already in the lists.

**Out.** Front: no change. `ClickUpConfig.ts` already exposes all 8 actions.

**Out.** `e9b85ca` / `authKind` (customer-owned credentials) — belongs to `868kkgkqa`, whose back
half is not in production.

**Out.** `quickbooks` — not in production in any repo (`PLAN.md` §9).

**Out.** Redesigning the integration — same pull types, push actions and payload shapes.

**Out.** Deleting the inline `clickup.adapter.ts` / `IntegrationsService` path — C1's, in a later
deploy after the flip (`TASK-C1-RETIRE-INLINE-PATHS.md`).

## Steps

1. Worker: cherry-pick `b027e55` onto `feat/868m7kbf0`, amend the `PORTED_FROM.md` note, run the
   ClickUp and `third-party-integration` specs scoped (4 GB heap, 1 worker).
2. Back: add `'clickup'` to `integrationProviders`, regenerate the contract, fix the registry spec.
3. Run the negative control on each new/changed test (see Verification).
4. Worker → `develop` → soak → `staging` → soak → PR to `main` (deploy 1).
5. Back → `master` → soak → `staging` → soak → PR to `production` (deploy 2), only after deploy 1 is
   live and the parity check passed.

**Merging into the dev lines — do not let the merge pick the version.** `develop` already carries
`clickup.adapter.ts`, `clickup-http.ts` and the spec in their `e9b85ca` (`authKind`) form. `master`
already lists `'clickup'` and `'quickbooks'`. When this task's branches merge into `develop`/`master`,
keep the dev-line versions of every ClickUp file and of the `integrationProviders` set. Taking this
task's P7 files would silently remove `authKind` support from dev. Run
`scripts/prod-dev-divergence.sh` before each merge.

## Verification

- **Negative control (required).** On a stack with deploy 2 applied, break the worker adapter (make
  one pull handler throw) and confirm the run **fails loudly**: the flow reports the failure and does
  not fall back to the inline path. Record the observed failure in the PR.
- **Field-by-field output parity, worker vs. inline.** Equality diff, not a shape check, for every
  one of the 8 actions. **Data available on dev (measured 2026-09-28):** 2 `clickup` rows in
  `user_integrations` (`authKind`: none, `platform_oauth`) and 2 stored ClickUp nodes: one pull
  `tasks` (flow `a39eaf92-…`) and one push `create_task` (flow `b8d3bf63-…`). The other 6 actions have
  no stored configuration, so their parity fixtures are built on dev against a test ClickUp space.
  Production was not queried (dev-only rule).
- **Measure before refusing (required).** After deploy 2, confirm the set of `thirdPartyIntegration`
  nodes that take the worker path is exactly the previous nine providers plus `clickup`. Classify every
  node whose routing changed, and drive to zero any non-ClickUp node whose path moved.
- **No double execution.** With deploy 2 applied, assert with a log or counter that exactly one
  execution occurs per dispatch for a ClickUp node and that `IntegrationsService` does not also
  execute it (R1, `PLAN.md` §6).

## Done when

The worker has the P7 ClickUp adapter on `main` (deploy 1). The back has `'clickup'` in
`integrationProviders` on `production` (deploy 2, a separate deploy). All 8 front actions have
field-by-field parity measured against the inline path. The negative control and the
no-double-execution assertion both passed. The inline ClickUp path still exists; deleting it is C1's.

## Files

**Worker:** `src/modules/nodes/third-party-integration/adapters/clickup.adapter.ts`,
`clickup-http.ts`, `clickup.adapter.spec.ts` (all from `b027e55`) ·
`src/modules/nodes/third-party-integration/third-party-integration.module.ts` (factory line) ·
`src/modules/nodes/third-party-integration/PORTED_FROM.md` (P7 entry).

**Back:** `src/shared/node-dispatch/node-dispatch-registry.ts` (`integrationProviders`) ·
`src/shared/node-dispatch/node-dispatch-contract.json` (regenerated) ·
`src/shared/node-dispatch/node-dispatch-registry.spec.ts` · read-only:
`src/app-api/integrations/adapters/clickup.adapter.ts`.

**MCP (back):** `src/app-mcp/mcp-integrations.service.ts` (+spec) · `mcp-internal.controller.ts` ·
`integration-options.source.ts` · `app-mcp.module.ts` · `node-types/node-type-metadata.ts` (+
`node-types.service.spec.ts`).

**mcp-server:** `src/tools/handlers/list-integration-options.handler.ts` (+spec) ·
`src/tools/tool-registry.service.ts` (+spec) · `src/tools/tools.module.ts` ·
`src/upstream/back-http-client.service.ts` · `test/pipeline.e2e-spec.ts`.

**Front:** none.
