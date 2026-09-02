# D2 — One machine-readable contract, and guidance an agent can trust

**Goal:** an agent — Claude Code or otherwise — that is asked to add or change a node type gets
current facts, not a snapshot from 2026-07.

**Depends on:** A1. **Do this early**, not at the end: an agent following today's guidance
produces wrong work now (PLAN §6, R7).

## Why this is urgent rather than tidy

`skills/node-worker-migration/SKILL.md` is the guidance an agent loads when asked to migrate a
node. It currently states the worker enum covers ten types "as of 2026-07" — it has thirteen today,
in `worker@origin/main` — says nothing about
`isTemporalNode`, nothing about the integration gate, nothing about the prefetch executor, and
nothing about the blocking wait. It also tells the agent the worker "does NOT receive engine
in-memory state" — true — while presenting the activity template as the only shape, which will be
wrong the moment B4 lands.

The skill even carries a worked example whose verdict this epic overturns. An agent that follows
it will confidently produce a migration that ignores three of the four dispatch lists.

## Scope

1. **The generated contract.** A1 produces the registry; this task makes it the published source:
   node type → dispatch, worker module, integration providers, prefetch eligibility, mutating,
   inline twin. Generated, not hand-maintained — node **fields** in
   `back/src/app-mcp/node-types/node-type-metadata.ts` are hand-maintained JSON with nothing
   type-checking them, and that is precisely the drift this epic should not reproduce.
2. **Refresh `skills/node-worker-migration/SKILL.md`.** Replace the enum snapshot with a pointer
   to the generated contract; add the four gates, the definition of done from PLAN §3.4, the
   blocking wait, and the prefetch path. Where the skill states a fact that can go stale, make it
   cite the generated file instead.
3. **CLAUDE.md.** A short section in the workspace file: where the contract lives, that adding a
   node type means the seven layers plus the registry, and which skills to run
   (`mcp-node-schema-sync`, `env-vars-sync`, `validate-changes`).
4. **Keep it true.** A spec that fails when the contract and the worker enum disagree — the same
   drift check A1 builds, extended to cover the published artefact. Documentation that can go
   stale silently will.

## Verification

- **Negative control (required).** Add a node type to the worker enum without registering it, and
  confirm the drift spec fails and names the missing registration. Then ask an agent to add a node
  type using only the refreshed skill, and check whether it produces all seven layers plus the
  registry entry. Record what it missed — that gap is the next revision of the skill.
- Every claim in the refreshed skill is checked against the code at the time of writing, with the
  SHA recorded. This is the same discipline D1 requires, and for the same reason.

## Done when

The contract is generated and test-enforced; the skill contains no stale enumeration; CLAUDE.md
points at both; an agent following the skill produces a complete registration.

## Files

`skills/node-worker-migration/SKILL.md` · `CLAUDE.md` · the A1 registry + generator + drift spec ·
`back/src/app-mcp/node-types/node-type-metadata.ts` (contrast case, not modified here)
