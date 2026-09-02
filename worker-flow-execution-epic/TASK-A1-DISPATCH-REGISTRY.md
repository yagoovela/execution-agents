# A1 — One dispatch registry

**Goal:** replace the four uncoordinated lists that answer "can the worker run this node type?"
with one derived source. **Every other task in this epic writes to this registry**, so it goes
first.

**Depends on:** nothing. **Blocks:** all of Track A, plus D2.

## Why

Four independent lists exist today, none referencing another (analysis §9.2.3):

| List | Where | Contents | Actually governs |
|---|---|---|---|
| `isTemporalNode(type)` | `back/src/app-api/flux/flux.service.ts` | 7 types | the flow loop **and** `executeSingleNode` |
| `isWorkerRoutedIntegration(node)` | `back/src/shared/integration/integration-executable-node.ts` | provider ∈ {stripe, wordpress, slack, notion, zapier, hubspot, supabase, pinecone, mcp} | the same two paths |
| `MIGRATED_TEMPORAL_NODE_TYPES` | `back/src/temporal/single-node-legacy/legacy-allowlist.ts` | the same 7 | only `/process/single-node-legacy` validation |
| `PREFETCH_SUPPORTED_NODE_TYPES` | `flux.service.ts` | 17 types | whether a flow may use the prefetch executor |
| `basedOnType` | `node-reference-substitution.service.ts` | per node type, which fields a placeholder may reference | whether a node's field can be referenced at all |

`basedOnType` is not a dispatch list, but it is the same failure mode and it is load-bearing for
B3: adding a node type with a referenceable field means editing it by hand, with nothing checking
that you did (analysis §11.2).

Two consequences are already live: `thirdPartyIntegration` takes the worker path inside a flow and
the inline path from the legacy endpoint, and the worker's `sqlQuerier` / `audioReaderNode`
modules are reachable by nothing (§9.4).

## Scope

**In.** One registry module in `back`, keyed by node type, with the facts each caller needs:

```
{ workerModule, dispatch, integrationProviders?, prefetchSafe, mutating, hasInlineTwin }
```

Re-express all four predicates as reads of the registry. Keep the function names — call sites
should not need to change, which keeps the diff reviewable.

**In.** `basedOnType` becomes a projection of the registry rather than a parallel hand-maintained
map. Its contents must not change in this task — same fields referenceable, same behaviour.

**In.** A `node_types.contract.json` in `back`, generated from the worker's `NodeType` enum, plus
a spec that fails when the registry claims a `workerModule` the enum does not have. The repos are
separate submodules with no shared build graph, so the check is a committed fixture with a
regeneration script — not an import.

**Out.** Changing what any node type does. A1 must be behaviour-neutral: same types dispatched,
same refusals, same prefetch eligibility. The inconsistencies it exposes get fixed by the tasks
that own them (A2, A3, C1) — this task only makes them visible in one place.

## Steps

1. Write the registry with today's values, entry per node type, sourced from the four lists.
2. Reconcile the three unaccounted types from the prefetch whitelist — `comment`, `label`,
   `group` (decision **D5** in PLAN §7). They must either get a registry entry or be removed from
   the whitelist; a live whitelist trusting types nobody can name is not a base to build on.
3. Rewrite `isTemporalNode`, `isWorkerRoutedIntegration`, `isMigratedTemporalNode`,
   `isLegacyRunnableNode`, `isMutatingNodeType`, `canUsePrefetchForFlow` as registry reads.
4. Add the generated contract fixture + drift spec.
5. Add a spec asserting the epic's invariant: **no type may have `workerModule: true` and
   `dispatch: 'inline'`** without an explicit `strandedReason`. That is what A3 will clear.

## Verification

- **Negative control (required).** Delete one type from the registry, run the suite, and record
  which test went red and with what message. Then flip a `dispatch` value and confirm the
  behaviour-neutrality spec catches it. State both observed failures in the PR.
- **Behaviour neutrality.** For all 48 registered types plus the 3 unaccounted ones, assert the
  new predicates return exactly what the old lists returned. Table-driven, one case per type —
  this is the test that makes the refactor safe.
- **Measure before refusing** (PLAN §3.3.2): `canUsePrefetchForFlow` is a refusing rule. Run the
  new implementation against real stored flows and confirm the set of flows it accepts is
  identical to today's. Report any difference as a defect in this task, not as an improvement.
- **D2's measurement, reported here.** While `canUsePrefetchForFlow` runs against every stored flow
  for the check above, record how many flows satisfy the whitelist, how many of them ran with
  `FLUX_EXEC_MEMORY_MODE=prefetch`, and what it saved. Report the numbers in the PR — B3 answers D2
  with them (Wave 4) and C2 executes the answer (Wave 6). Unknown is unverifiable, not zero.

## Done when

Registry is the only place a node type's dispatch is declared; the six predicates read from it;
the drift spec is green; the behaviour-neutrality table covers every type; no production
behaviour changed.

## Files

`back/src/app-api/flux/flux.service.ts` (`isTemporalNode`, `PREFETCH_SUPPORTED_NODE_TYPES`, `canUsePrefetchForFlow`) ·
`back/src/shared/integration/integration-executable-node.ts` (`MIGRATED_INTEGRATION_PROVIDERS`, `isWorkerRoutedIntegration`) ·
`back/src/temporal/single-node-legacy/legacy-allowlist.ts` · new registry module + fixture + specs ·
`worker/src/modules/nodes/nodes.types.ts` (read only, source of the fixture)
