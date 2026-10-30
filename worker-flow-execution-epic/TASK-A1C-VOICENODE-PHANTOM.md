# A1C — Decide `voiceNode`

**Goal:** decide, on a measurement, whether `voiceNode` is removed from the legacy single-node
surface or kept with a stated reason — and record which, so a live list stops trusting a type nobody
can name without anyone having checked.

**Added 2026-09-22**, split out of TASK-A1 on the day A1 shipped. A1's Scope instructed the removal
of four phantom types. Three of them (`comment`, `label`, `group`) were measured and the removal was
reverted — see **What D5 actually returned** in TASK-A1. `voiceNode` was never measured at all, so
it could neither be removed nor be declared safe, and shipping it either way on the strength of a
measurement that did not look at it would have repeated the error A1 had just recorded.

**Depends on:** A1 (the registry exists; `voiceNode` already has an entry marked `phantom`).
**Blocks:** nothing. It clears a known-unresolved item, not a precondition.

## Why

`voiceNode` is registered in **no** node-type source — not `front/src/util/nodeTypes.tsx` (46
types), not `back/src/app-mcp/node-types/node-type-metadata.ts` (50 entries). Nothing in the product
can create one today. Yet it is trusted in two live places:

- `LEGACY_SINGLE_RUN_NODE_TYPES` (now derived: `legacyEndpoint: 'accept'` in the registry), so
  `/process/single-node-legacy` **accepts** it and runs it inline.
- `legacy-node-dispatch.ts`'s `dispatchLegacyHandler`, in the shared
  `case 'voiceBoxNode': case 'voiceNode':` arm.

Unlike the prefetch whitelist, this is not a permissive list whose extra entries are harmless.
It is the accept list of a live endpoint. That cuts both ways, which is the whole reason this
needs measuring rather than deciding:

- If no stored node has this type and no caller sends it, the arm is dead surface and removing it
  shrinks the legacy endpoint — which is what C2 wants.
- If some old flow **does** carry a `voiceNode`, removing it turns a request that works today into
  a refusal. That is a false refusal on a live endpoint, strictly worse than the untidiness.

## Scope

**In.** Run the measurement below and record the numbers in this file.

**In.** Decide from it: remove `voiceNode` from the registry's accept verdict and from the dispatch
switch arm, **or** keep it with a `note` stating why and what evidence supports that. Record the
decision and the reasoning here, not only in code.

**In.** If the decision is removal, share the `case 'voiceBoxNode': case 'voiceNode':` arm carefully
— `voiceBoxNode` is a real, live type and must keep its handler.

**Out.** `voiceBoxNode` itself, and its dispatch conflict (that is A3's).

**Out.** The other three phantom types. They are settled — TASK-A1, **What D5 actually returned**.

## Steps

1. Run the measurement (below) against production, read-only.
2. Decide, and write the decision plus its numbers into this file.
3. Apply it: either drop the accept verdict and the switch arm, or add the `note`.
4. The registry's drift spec already pins the switch arms against
   `registeredNodeTypes().filter(legacyEndpointAccepts)`, so a removal that touches only one of the
   two places fails the suite. Confirm that is what happens before trusting the change.

## Verification

- **Measurement, production, read-only, the deciding number.** Two questions, because a type can be
  stored without ever being called and called without being stored:
  - does any stored node carry `type = 'voiceNode'`? (`flows_nodes`, live canvases and version
    history both — a legacy request can name a node from an old version)
  - did any `node_executions` row with `type = 'voiceNode'` run, and how recently?
  Model the query on `etc/a1-q1-phantom-types-prod.sql`, which already carries the join and window
  conventions. **Include a control row** for a type known to be present (e.g. `commandTextNode`), so
  an empty result set cannot be mistaken for a measured zero — A1's D5 measurement did this and it
  is what made its zeros trustworthy.
- **Negative control (required).** Before removing the switch arm, confirm the drift spec actually
  catches a half-removal: drop the arm while leaving `legacyEndpoint: 'accept'` in the registry, and
  record which test goes red with what message. Then make the real change.
- **Measure before refusing** (PLAN §3.3.2). If the measurement cannot distinguish "never used" from
  "not observable", report it as unverifiable and keep the type with a `note`. Unknown is not zero,
  and a false refusal on a live endpoint is worse than a stale arm.

## Done when

The measurement is run and its numbers are in this file. `voiceNode` is either gone from both the
registry's accept verdict and the dispatch switch, or present with a `note` saying why and on what
evidence. No request that succeeds today against `/process/single-node-legacy` refuses afterwards.

## What the measurement returned

Run 2026-09-22 against **production** (read-only, by the task owner) and against **dev**, all time,
with two control rows — `commandTextNode` (known present, migrated) and `voiceBoxNode` (the live
sibling that shared the switch arm). The controls are what make each zero a measured zero rather
than an empty result set. Query: `etc/a1c-voicenode-measure.sql`.

| Question | Production | Dev |
|---|---|---|
| `flows_nodes`, live canvases, `voiceNode` | **0** | **0** |
| — control `commandTextNode` | 41,868 nodes / 15,531 flows | 9,217 / 4,144 |
| — control `voiceBoxNode` | 338 nodes / 244 flows | 369 / 273 |
| `flows_nodes`, version history, `voiceNode` | **0** | **0** |
| — control `commandTextNode` | 10,670 nodes / 2,031 versions | 386 / 170 |
| table size, so a zero is a measured zero | 244,453 rows, 53 distinct types, oldest 2026-02-24 | 41,674 rows, 54 types, oldest 2026-02-14 |
| `flows.nodes` pre-migration JSON, `voiceNode` | **0** over 14,818 flows | **0** over 4,193 flows |
| — controls in the same column | `voiceBoxNode` 273 · `commandTextNode` 14,270 | 266 · 3,970 |
| `node_executions`, `voiceNode` | **0** | **0** |
| — controls | `commandTextNode` 8,783 · `voiceBoxNode` 20 | 287 · 17 |
| what `node_executions` can see at all | 62,298 rows, window opens 2026-08-23 | 2,424 rows, opens 2026-08-26 |

**The `node_executions` window is short, and it does not matter.** That table only goes back a month,
so on its own its zero would be "not observable", not "never ran" — exactly the case the task said to
report as unverifiable. It is not the deciding number. `SingleNodeLegacyService.validateNode()` reads
`node.type` from the **stored** node (`flows_nodes`, via `getFlowWithNodesAndEdges`), so a caller
cannot name a type nobody has saved. `flows_nodes` covers everything since the 2026-02-24 migration
and the deprecated `flows.nodes` JSON column covers the canvases from before it, both measured, both
zero, both with live controls. There is no window a stored `voiceNode` could be hiding in.

Three facts outside the database point the same way:

- `voiceNode` has never appeared in `front/src/util/nodeTypes.tsx` or `front/src/components/nodes/`
  in the **entire history** of those paths (`git log -S`, all branches, empty). It is not a type the
  product retired; it is a type the product never had.
- It does not exist in the worker.
- In the flow-execution path, only `voiceBoxNode` is ever tested (`flux.service.ts` lines 1305, 2975,
  2982, 3678, 4300). `this.voiceNode(...)` is `voiceBoxNode`'s handler *method*, not a type check —
  which also means the entry's `flowDispatch: 'inline'` described a dispatch that did not exist.
  The string `'voiceNode'` as a node type lived only in the legacy allowlist and the switch arm,
  both introduced by the same commit, `f15a83a0`.

## Decision — removed

`voiceNode` is gone from both places: the registry entry is deleted (so `legacyEndpoint: 'accept'`
and therefore `LEGACY_SINGLE_RUN_NODE_TYPES` no longer carry it), and the shared
`case 'voiceBoxNode': case 'voiceNode':` arm is split so `voiceBoxNode` keeps its handler untouched.

This is the opposite verdict from `comment`/`label`/`group`, and the asymmetry is the reason, not an
inconsistency. Those three sit in the **prefetch whitelist**, which is permissive — an extra entry
costs nothing, and removing one would have cost a flow its prefetch eligibility, a false refusal.
This is a **live endpoint's accept list**, where an entry nobody can reach is dead surface and C2
wants it gone. No request that succeeds today refuses afterwards, because no request naming a
`voiceNode` can be constructed today: there is no stored node of that type in production, and no
source in the product can create one.

## Negative controls — run and observed red

1. **The half-removal the task asked for.** Dropped `case 'voiceNode':` from
   `legacy-node-dispatch.ts` while leaving `legacyEndpoint: 'accept'` in the registry. Baseline was
   10/10 green; the drift spec then failed:
   `legacy dispatch switch vs the registry › handles exactly the accepted types plus the known-unreachable arms`,
   `expect(received).toEqual(expected)`, `- Expected - 1` / `"voiceNode"`, at
   `node-dispatch-invariants.spec.ts:112`. Restored, green again. The suite does catch a
   one-sided removal.
2. **The new assertions.** Re-added the registry entry after the real change and ran the whole
   `src/shared/node-dispatch/` suite: **5 tests went red**, one per assertion that claims something
   about this removal — the switch-vs-registry drift check, `really removed the types it declares
   removed`, `voiceNode › isLegacyRunnableNode matches production, except where a measurement removed
   it`, `names the three phantom types D5 kept`, and `leaves voiceNode out of the canonical
   non-executable set, and out of the registry`. Removed again: 246 passed, 1 skipped, 0 failed.

## What this left behind, deliberately

The production snapshots in `node-dispatch-registry.spec.ts` (`PROD_LEGACY_SINGLE_RUN_NODE_TYPES`
and friends) still list `voiceNode`, verbatim. They are a record of what production did at
`3804a524`; editing them would erase the very departure being declared. The departure is declared
instead in a named `MEASURED_REMOVALS` list carrying the numbers above, the same idiom
`KNOWN_UNREACHABLE_ARMS` already uses in the invariants spec — and a companion test asserts each
declared removal is genuinely absent from the registry, so the exception cannot quietly cover an
accidental deletion.

## Files

`back/src/shared/node-dispatch/node-dispatch-registry.ts` (the `voiceNode` entry) ·
`back/src/temporal/single-node-legacy/legacy-node-dispatch.ts` (the shared switch arm) ·
`back/src/shared/node-dispatch/node-dispatch-invariants.spec.ts` (the switch drift spec) ·
TASK-A1's **What D5 actually returned** (the precedent this task follows)
