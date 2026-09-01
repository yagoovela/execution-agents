# C2 — Retire the legacy surfaces, and settle the prefetch question

**Goal:** remove the entry points and the flags that only existed to bridge the migration, and
decide the prefetch executor's fate on evidence.

**Depends on:** C1, B4. **Answers:** decision **D2**.

## Scope — three separable pieces

**Not in scope, settled by `D18`: the batch-process endpoints stay.** None of the five is
deprecated — `POST /batch-process` (`flux.controller.ts:643`), `GET /batch-process/:id/status`
(`:839`), `GET /batch-process/all` (`:872`), `POST /batch-process/:id/stop` (`:888`) and
`GET /batch-process/:ids/download` (`:923`). The route stays as the entry point and its body moves
into `B7`'s durable workflow; the status, stop, listing and download endpoints are the surface a
batch screen reads, so they gain a consumer rather than losing one. Do not sweep them up with the
legacy endpoint below — they look similar and are not.


### 1. `/process/single-node-legacy`

`back/src/temporal/temporal.controller.ts:71`, backed by
`single-node-legacy/single-node-legacy.service.ts`. Its `validateNode` (`:132–150`) refuses
migrated types, refuses mutating types, and accepts only `LEGACY_SINGLE_RUN_NODE_TYPES`.

Once every executable type runs in the worker, this endpoint accepts nothing — it becomes a
router with an empty destination set. Retire it and the allowlist that feeds it.

There is a defect to fix or carry until then: `thirdPartyIntegration` is worker-routed inside a
flow but is still in `LEGACY_SINGLE_RUN_NODE_TYPES`, so this endpoint runs it inline. The same
node takes different paths depending on how it was started (analysis §9.4). Either fix it in A1's
wake or record it here as knowingly carried until retirement.

### 2. The prefetch executor — measure, then decide (D2)

`back/src/app-api/flux/prefetch/` is in production behind `FLUX_EXEC_MEMORY_MODE`, defaulting to
`legacy`, with a 17-type whitelist that excludes every Temporal type and every control-flow type
(analysis §9.2.1). **Before deciding anything, measure:**

- How many production flows satisfy `canUsePrefetchForFlow`? A whitelist excluding every LLM node
  may make the answer near zero.
- Of those, how many ran with the flag on? What did it save — memory, latency, row size?

Then one of:
- **Destination:** it is the model B3 generalises; widen the whitelist as the A track lands and
  keep it.
- **Stopgap:** B3's worker-side resolution supersedes it; retire the executor and its whitelist,
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

`back/src/temporal/temporal.controller.ts:71` · `back/src/temporal/single-node-legacy/**` ·
`back/src/app-api/flux/prefetch/**` · `back/src/app-api/flux/flux.service.ts:1402–1431, 3198–3226` ·
`front/src/service/processService.ts`
