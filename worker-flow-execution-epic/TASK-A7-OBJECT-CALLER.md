# A7 — Migrate `nodesBox` (Object Caller)

**Goal:** migrate the one mutating node whose logic is actually extractable, behind two new
callbacks and an explicit ordering guarantee.

**Depends on:** A1, **B1** (execution identity). Do not start before B1 — this node's correctness
depends on knowing which execution a write belongs to.

## Why it is different from the other four mutating nodes

`conditionNode`, `arrayNode`, `fluxBox` and `libraryNode` are control flow; they decide what runs
next, and belong in the workflow (B6). `nodesBox` mutates **data**, not control (analysis §3.5).
Its own logic is about 130 lines. The work is entirely in what has to exist around it.

Today it reads `data.selectedId` against `objectCallerData` — the engine's in-memory array for the
run — reads the latest session state for
`{scopeType:'object', scopeId, sessionKey, ownerUserId}`, then reads and/or writes the object's
content and publishes the change back through `onMutateObjectCallerData` so later nodes see it.
Handler `objectCaller()` in `flux.service.ts`; three dispatch sites — the full-run type switch, the loop-body path and the single-node path — plus the pre-run session clear.

## Scope

**In.** Three things, in this order:

1. **An object-state callback** — read and write, exposing `objectsService`. Model it on the
   existing `/worker/store-payload` contract rather than inventing a shape.
2. **A session-state callback** mirroring `sessionStateService.readLatest` and `appendEntries`
   for the `object` scope.
3. **An answer on ordering.** Today the engine serialises every Object Caller in a run through one
   in-memory array. Two callers touching the same object must stay ordered once they are
   independent activities. Two acceptable answers: an advisory lock, following the pattern already
   used in `worker/src/modules/nodes/third-party-integration/oauth-token.repo.ts`
   (`pg_advisory_xact_lock`), or an idempotent activity. **Pick one and state why** — do not ship
   without addressing it and hope the ordering holds.

**Out.** Changing object semantics, session-state scoping, or the chat behaviour built on it.

## Verification

- **Negative control (required).** Remove the ordering guarantee and write a test that runs two
  Object Callers against the same object concurrently, asserting the final content. Watch it go
  red — an intermittent test is not acceptable here, so make the race deterministic by holding the
  lock explicitly in the test rather than relying on timing.
- Session-state parity: `readLatest` / `appendEntries` through the callback must produce the same
  rows the inline path produces, on real stored objects.
- The chat path (`fluxObject` / `nodesBox` with chat enabled) must be unaffected — it is written
  at run finalisation (`flux.service.ts`), outside this node.

## Done when

`nodesBox` satisfies PLAN §3.4; both callbacks exist and are documented in D1; the ordering
decision is recorded in this file with its rationale; the inline handler is deleted.

## Files

`back/src/app-api/flux/flux.service.ts` (`objectCaller()` + its three dispatch sites) ·
`back/src/temporal/worker.controller.ts` (new callbacks) · `back/src/app-api/objects/` ·
`back/src/app-api/session_state/` · new `worker/src/modules/nodes/object-caller/` · the A1 registry
