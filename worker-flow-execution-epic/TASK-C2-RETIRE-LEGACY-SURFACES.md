# C2 — Retire the legacy surfaces, and settle the prefetch question

**Goal:** remove the entry points and the flags that only existed to bridge the migration, and
decide the prefetch executor's fate on evidence.

**Depends on:** C1, B4. **Answers:** decision **D2**.

## Scope — three separable pieces

**Not in scope, settled by `D18`: the batch-process endpoints stay.** None of the five is
deprecated — `POST /batch-process` (`flux.controller.ts`), `GET /batch-process/:id/status`, `GET /batch-process/all`, `POST /batch-process/:id/stop` and
`GET /batch-process/:ids/download`. The route stays as the entry point and its body moves
into `B7`'s durable workflow; the status, stop, listing and download endpoints are the batch's only
surface — the screen that would read them is not built in this epic (B7, 2026-09-02) — and they stay
regardless. Do not sweep them up with the legacy endpoint below — they look similar and are not.


### 1. `/process/single-node-legacy`

`back/src/temporal/temporal.controller.ts`, backed by
`single-node-legacy/single-node-legacy.service.ts`. Its `validateNode` refuses
migrated types, refuses mutating types, and accepts only `LEGACY_SINGLE_RUN_NODE_TYPES`.

Once every executable type runs in the worker, this endpoint accepts nothing — it becomes a
router with an empty destination set. Retire it and the allowlist that feeds it.

There is a defect to fix or carry until then: `thirdPartyIntegration` is worker-routed inside a
flow but is still in `LEGACY_SINGLE_RUN_NODE_TYPES`, so this endpoint runs it inline. The same
node takes different paths depending on how it was started (analysis §9.4). Either fix it in A1's
wake or record it here as knowingly carried until retirement.

### 2. The prefetch executor — execute the D2 answer

`back/src/app-api/flux/prefetch/` is in production behind `FLUX_EXEC_MEMORY_MODE`, defaulting to
`legacy`, with a 17-type whitelist that excludes every Temporal type and every control-flow type
(analysis §9.2.1). **The measurement is A1's and the answer is B3's** (ownership split 2026-09-02,
PLAN §7 D2): A1 reports, while it runs `canUsePrefetchForFlow` against every stored flow in Wave 2,
how many flows satisfy the whitelist, how many ran with the flag on, and what it saved; B3 answers
D2 with those numbers in Wave 4. This task **executes** whichever answer won:

- **Destination:** it is the model B3 generalised; the whitelist is derived from the A1 registry, not
  hand-maintained, and the executor stays.
- **Stopgap:** B3's worker-side resolution superseded it; retire the executor and its whitelist,
  removing a fourth list from the world.

Either answer is fine. Leaving it undecided is not: a dormant second execution path is a
maintenance tax nobody is paying attention to.

### 3. The migration flags

Every flag from PLAN §3.2 is temporary by construction. A flag that outlives its migration is a
branch of production behaviour nobody tests. Remove each once its node has soaked.

## Verification

- **Negative control (required).** Call `/process/single-node-legacy` with each node type before
  retirement and record the response; after retirement, confirm the removal is a clear 404/410 and
  that the front never calls it. A silently-dead endpoint the front still calls is worse than
  keeping it.
- **Measure before refusing** (PLAN §3.3.2), applied to the measurement itself: report flows whose
  eligibility you could not determine as *unverifiable*, not as ineligible. The prefetch decision
  must not rest on a count that quietly rounded unknowns to zero.
- Front check: `ProcessService.responseLegacy` (`front/src/service/processService.ts`) must have no
  callers before the endpoint goes.

## Done when

The legacy endpoint and its allowlist are gone; D2 is answered in writing with the numbers behind
it; no migration flag from this epic remains.

## Files

`back/src/temporal/temporal.controller.ts` (`/process/single-node-legacy`) · `back/src/temporal/single-node-legacy/**` ·
`back/src/app-api/flux/prefetch/**` (`memory-mode.ts` owns `FLUX_EXEC_MEMORY_MODE`) · `back/src/app-api/flux/flux.service.ts` (`PREFETCH_SUPPORTED_NODE_TYPES`, `canUsePrefetchForFlow`, the `isPrefetchMode()` switch) ·
`front/src/service/processService.ts`
