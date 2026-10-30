# A5 — Migrate `imageGenerator` over a shareable image provider layer

**Goal:** migrate `imageGenerator` into the worker, over a provider layer written so the next image
node can share it.

**Depends on:** A1.

**Corrected 2026-09-24 — A4 dependency dropped (user decision).** This task no longer depends on A4
having validated the reportBuilder canary template. A5's migration had already shipped before A4 did,
and neither of A5's two remaining leftovers (the provider-layer extraction and the per-provider
timeouts) reads anything from that template. The A1 dependency stands.

**Corrected 2026-09-02 — `imageReaderNode` is out (D24).** The first draft paired `imageGenerator`
with `imageReaderNode` so their overlapping provider paths would be written once. `imageReaderNode`
is **deprecated**: it leaves this task and A6. An OCR node is wanted in its place and will be
specified when it is built — not in this epic. If Temporal or the provider layer turns out to offer
a primitive for it, the developer of that node decides then. What survives from the pairing is the
*shape*: the provider layer is still built as a shared layer, because an image node that copies
provider calls into itself is the drift this epic keeps finding.

**An `imageGenerator` worker module is in progress on the dev line (2026-09-02).** Start from it,
not from a blank module; the steps below are what it has to satisfy before it ships, whoever
finishes it.

**Corrected 2026-09-21 — re-validated against `worker@origin/main` `3e4c93a` and
`back@origin/production` `3804a524`. The migration shipped in substance; two of this task's
distinctive deliverables did not, and one Done-when clause was deliberately not met, on an
established precedent. A5 does not come out of the epic — it stays open, narrowed to the two
leftovers below.**

**Shipped.** `worker/src/modules/nodes/image-generator/` is complete and dispatched: `node-activities.ts`
maps `NodeType.IMAGE_GENERATOR` to `imageGeneratorActivity`; `imageGenerator` is in `back`'s
`isTemporalNode` and in `MIGRATED_TEMPORAL_NODE_TYPES` (§ TASK-A1). Its `PORTED_FROM.md` documents a
careful port with per-provider provenance SHAs, deliberate deviations recorded and reasoned, and a
measured decision on the `sync_mode` string-equality bug — preserved byte-identically after
classifying it against real dev and staging data (18 of 763 dev rows and 11 of 744 staging rows use
the literal-string comparison) rather than silently "fixed" into a behaviour change.

**NOT done — leftover 1: the shared provider layer.** This task's Scope required a
`worker/src/modules/ai-provider/image/` layer the node consumes, with its Done-when saying the module
must carry no provider call of its own. `worker/src/modules/ai-provider/` contains only
`ai-provider.module.ts`, `ai-provider.service.ts` and `perplexity-stream.spec.ts` — **there is no
`image/` subdirectory.** The providers live node-locally, under
`worker/src/modules/nodes/image-generator/providers/` (`fal-provider.ts`, `gemini-provider.ts`,
`openai-provider.ts`, `ideogram/`, `stability/`, `fal-model-map.ts`, `resolve-image-model.ts`). This
is exactly the clause this task's Verification called "the part of this task the next image node
inherits; if it ends up bypassed, that part did not happen." It was bypassed. Recorded as such, not
softened.

**Corrected 2026-09-24 — leftover 1 resolved: Option A (extract and move), the user's decision. In
progress on worker branch `feat/868m0vkt4` (worktree `/home/alexandre/enhanced-wt/868m0vkt4/worker`),
committed and pushed as `413db60` — no PR yet, so say "in progress on `feat/868m0vkt4`," not
"shipped" or "a PR is open."** Everything provider-specific moved out of
`worker/src/modules/nodes/image-generator/providers/` (plus `ai-sdk-error-classifier` and
`http-error-classifier`) into `worker/src/modules/ai-provider/image/`, behind a new
`ImageProviderService` (`image-provider.service.ts`, registered and exported by `AiProviderModule`)
exposing `supports(aiSystem)` and `generate(request)`. `PROVIDER_BUILDERS`/`DIRECT_HTTP_BUILDERS` and
the `generateImage()` call plus its AI-SDK error classification now live there; types moved to
`ai-provider/image/image-provider.types.ts`. `image-generator.service.ts` keeps prompt building, the
unsupported-`aiSystem`/empty-prompt refusals, storage via `/worker/store-image`, billing via
`/worker/charge-tokens` (the charge closure is injected into the layer, so per-provider charge timing
is unchanged), the `previewResponses` shape and persistence — and carries no provider call of its own.
The Verification bullet "One layer, not a copy" now passes: grep shows the only fetches left in the
node module are the two back callbacks in `store-and-charge.ts`. `DirectHttpImageContext` dropped
`execId`, `nodeId`, `userId`, `flowId`, `spaceId` (no provider read them — only `ctx.charge` was used)
and gained `abortSignal` (see cancellation, below).

Option B — a node-agnostic typed `ImageGenerationRequest` — was deliberately deferred: it would
rewrite roughly 2,300 lines of provider specs (losing them as parity proof), has to carry the
preserved `sync_mode` string-equality quirk and each provider's own field names/defaults through an
adapter, and there is no second image node today to validate the request shape against (the OCR node
that would replace `imageReaderNode` is out of this epic, D24). Revisit once a second image node
exists. Known limitation of Option A: the layer's input still uses `imageGenerator`'s own field names
(e.g. `aspect_ratio_ideogram`).

Not done, and out of scope on purpose (a follow-up, not a leftover of this task): `ideogram/http.ts`
and `stability/http.ts` still duplicate the fal queue client and `fetchSourceImageBuffer`;
`postStabilityForm`/`postStabilityJson` and `classifyHttpError` have no production caller.

**New 2026-09-24 — cancellation wired into `imageGeneratorActivity`, as part of leftover 1's work.**
An earlier hypothesis suspected the activity only heartbeats once before the provider call, so it
would die with a heartbeat `TIMED_OUT` after 30 s under a slow provider. Correcting that here, for the
record: it is false. `imageGeneratorActivity` is wrapped in `withKeepAliveHeartbeat`
(`worker/src/modules/temporal/activities/activities.service.ts`, `KEEP_ALIVE_HEARTBEAT_MS = 15000`, half the 30 s
`heartbeatTimeout`), matching Temporal's own guidance of heartbeating on a timer at half the
`heartbeatTimeout` (`heartbeatTimeout` detects a dead worker; `startToCloseTimeout` bounds a stalled
call). What was actually missing: nothing listened to the cancellation signal. `generateImage()` got
no `abortSignal`; the fal queue submit/poll/result fetches got none. The activity runs inside
`cancelScope.run` (`process-single-node.workflow.ts`), and back sends the `cancelNode` signal
(`execution_logs.service.ts`) / MCP's `cancel_run` cancels the workflow — cancellation is reachable.
By code reading, not observed in data: with the default `TRY_CANCEL`, the workflow settles the node as
cancelled while the activity keeps running and can later call `persistNodeSuccess`, whose UPDATE is
keyed only on `(execId, nodeId)` — it could overwrite the cancelled state with `COMPLETED` and bill a
run the user had already cancelled.

The fix: the node passes `Context.current().cancellationSignal` down into the layer; the layer passes
it into `generateImage()` and into every fal submit/status/result fetch, `fetchSourceImageBuffer` and
`postIdeogramJson`, and the poll wait uses a new `abortableSleep`. A cancellation abort is rethrown
unclassified (not wrapped into `ProviderError`) so `runNodeActivity` reports a cancellation, not a
failure. Verified against the prod runtime versions (Node 22.13.0, `ai` 7.0.83,
`@ai-sdk/provider-utils` 5.0.32, `@temporalio/activity` 1.14.1): Temporal aborts with a
`CancelledFailure` reason, `fetch` rejects with that reason, and the AI SDK's retry wrapper rethrows
abort errors unwrapped rather than retrying them.

Behavioural consequence to flag, not fixed here: `stabilityai` methods charge **before** the provider
call (preserved parity with the inline path). A cancel that lands after that pre-charge now ends the
same way a provider failure after the pre-charge does today — the user is charged and gets no image.
AI-SDK providers and `ideogram` charge after success, so a cancel there charges nothing. Left
unchanged on purpose: `generateImage()`'s `maxRetries` stays at the SDK default (2 retries inside one
activity; Temporal's own retry policy is `maximumAttempts: 1`). Whether providers bill failed attempts
is unknown.

**Tests & negative controls (2026-09-24).** New tests: `generateImage` receives the activity's
cancellation signal; a cancellation abort is rethrown unclassified with no node update written; fal
polling (the `stabilityai` and `ideogram` copies) stops and rejects with the abort reason, and every
fetch carries the signal. Each was seen failing first — drop the signal on `generateImage`, drop the
abort rethrow, make the poll wait non-abortable, drop the signal from a status fetch (once per copy) —
then restored, per this repo's negative-control rule. Validation on the branch: `tsc` clean, Biome
clean on the 31 changed files, related Jest 214 passed / 2 skipped. Pre-existing failures reproduced
identically on a clean `origin/main` checkout (not caused by this change): `heartbeat-coverage.spec.ts`
(`pullDataActivity`/`pushDataActivity`), and `activities.service.spec.ts`,
`activities.web-search.spec.ts`, `perplexity-stream.spec.ts` fail to load (ESM "Cannot use import
statement outside a module"). The 2 skipped tests are the pre-existing `FAL_KEY`-dependent
ideogram/stability service tests.

**NOT done — leftover 2: per-provider timeouts.** Step 3 required timeouts chosen deliberately per
provider in `workflows/configs.ts`. There is a single `imageGeneratorActivity` proxy, one
`startToCloseTimeout` ("5 minutes") and one `heartbeatTimeout` ("30 seconds") for every provider, and
the comment directly above it in `configs.ts` says so in writing: it is **not** a measured p95, M2's
capture method could not record per-node duration (its `baseline/*.json` fixtures all show
`durationMs: null`), and — its own words — "Replace with a measured value before W5." That is a
written, dated commitment with a deadline inside this epic. It is carried here as an explicit open
Done-when clause, not left as prose buried in a source comment nobody outside the file will read.

**Corrected 2026-09-24 — leftover 2 still open; method decided: measure production first.** SDK facts
checked: `generateImage` exposes no timeout option, only `abortSignal`; fal documents no client-side
timeout (the ~2-minute poll budget, 120×1 s, is this codebase's own local decision, not a provider
default). Decision: measure real production durations before picking numbers, rather than guessing
again. A read-only measurement kit was written to
`.claude/tasks/worker-flow-execution-epic/scripts/a5-image-timeouts/`:
`measure-image-generator-durations.mts` lists `processSingleNode` workflows via Temporal visibility
and pairs `imageGeneratorActivity` events into a CSV; `image-generator-duration-summary.sql` joins to
`node_executions` on `(execId, nodeId)` for per-`aiSystem`/model p50/p95/p99/max and timeout counts,
plus an approximate `createdAt`/`updatedAt` cross-check; `README.md` documents how to run both. The
user runs this against prod — no agent accesses prod. Unverified until it is run: prod Temporal's
visibility query support and its connection/TLS mode. Next step once the data is back: set
`startToCloseTimeout` per provider above the slowest observed real call, and decide whether the fal
poll budget needs to grow alongside it.

**Corrected 2026-09-25 — leftover 2 narrowed (user decision): no per-provider timeouts.** Re-reading
what the code already guarantees, a timeout per provider buys almost nothing:

- `imageGeneratorActivity` runs with `maximumAttempts: 1` (`COMMON` in `configs.ts`), so a wrong
  timeout never multiplies calls or charges; the worst case is one error, or one worker slot held for
  at most five minutes.
- `withKeepAliveHeartbeat` beats every 15 s, so the 30 s `heartbeatTimeout` never cuts a live call.
- `stabilityai` and `ideogram` stop polling fal after their own 120 × 1 s budget, so for them the
  five-minute ceiling is never the limit that applies.
- What is left is the AI SDK path (`openai`, `gemini`, `fal`, `meta`), which took seconds to about a
  minute on dev, well under one five-minute ceiling.

The Temporal kit (`measure-image-generator-durations.mts` + `image-generator-duration-summary.sql`)
answered a finer question than the one that matters. It is kept for the record, not required. What
leftover 2 now is:

1. **Validate the single ceiling with one query**, `scripts/a5-image-timeouts/image-generator-duration-check.sql`
   (read-only, production, run by the user): p50/p95/p99/max of `updatedAt - createdAt` per
   `aiSystem` for successful `imageGenerator` executions in the last 30 days, plus error and timeout
   counts. The duration is approximate and errs long (it includes dispatch and any later write to the
   row), which is the safe side for this question. If p99 and max sit well under five minutes and
   timeouts are rare, the ceiling stays and `configs.ts`'s comment records the measured numbers instead
   of "placeholder". A provider that comes close to five minutes gets its own value; only that one.
2. **Cancel fal jobs on our side**: a best-effort `PUT cancel_url` (without the aborted signal, errors
   swallowed) on abort and on the poll timeout, plus `X-Fal-Request-Timeout` at submit, identically in
   both fal clients (`ai-provider/image/stability/http.ts`, `ideogram/http.ts`). This is the part with
   real value: today a cancelled or timed-out node leaves the job running at fal, where it can start
   and bill for an image nobody receives (see *Dev verification, 2026-09-24*, finding 2).

**Corrected 2026-09-25 (later) — leftover 2 implemented on the branch, pending merge.** The user ran
`image-generator-duration-check.sql` against prod (30 days, successful `imageGenerator` executions):

| `aiSystem` | Runs | p50 | p95 | p99 | Max | Errors |
|---|---|---|---|---|---|---|
| `openai` | 230 | 14 s | 33 s | 63 s | 91 s | 42 |
| `stabilityai` | 60 | 119 s | 126 s | — | 127 s | 38 |
| `fal` | 17 | — | — | — | 19 s | 0 |

`gemini`, `ideogram` and `meta` had no prod runs in the window. The AI SDK path sits far under the
five-minute ceiling, which stays. `stabilityai` was the exception: the user confirmed its 38 errors
are poll timeouts, so its limit was never the ceiling but its own 120 × 1 s fal poll budget
(120 attempts took ~127 s, fetch latency included). What shipped, on worker `feat/868m0vkt4`
(PR #104):

1. **`966f446`** — Stability's fal poll runs against a 270 s wall-clock deadline instead of 120
   attempts (user decision: align with the five-minute ceiling). A deadline, not 280 attempts, so it
   still fails with a classified `TimeoutError` before Temporal's `startToCloseTimeout` kills the
   activity. `configs.ts`'s placeholder comment now records the measured numbers above. Negative
   control: with the budget back at 120 s, the new test goes red.
2. **`7e10e5e`** — both fal clients send a best-effort `PUT cancel_url` (5 s cap, errors swallowed,
   not on the aborted signal) on abort and on poll timeout, and set `X-Fal-Request-Timeout` to the
   poll budget at submit, so a request still queued when the worker gives up is never started. The
   method (`PUT`) and header were confirmed against `fal-js`'s `queue.ts` source, since fal's docs
   list the cancel as `POST` in one place. `ideogram` moves to the same deadline shape but keeps its
   120 s budget (no prod runs, not asked). Negative controls: dropping the header, the timeout cancel
   or the abort cancel each turns two tests red (one per client).

Both were cherry-picked onto `feat/868m0vkt4-dev` (`91c96de`, `b74d35a`) and merged to `develop`
(`4e48a20`, `68a0932`); the dev deploy succeeded. Remaining flag, unchanged by design:
`stabilityai` pre-charges, so a run that still exceeds 270 s bills with no image.

**Dev QA, 2026-09-25, after the deploy of `68a0932`.**
- Run `db4000d6` of flow `0f4250af` ("A5 dev M-tests via MCP"). `fal` (2 s, 5 credits), `gemini`
  (7 s, 39), `openai` `gpt-image-1` (17 s, 40) and `ideogram` remix (12 s, 60, through the changed fal
  client) each returned an image. The `stabilityai` sketch node pre-charged 50 and then failed with
  `TimeoutError` ("The image provider took too long to respond.") at 14:20:15.653Z, 271 s after it
  started at 14:15:44. So the 270 s deadline fired on dev, before the five-minute activity ceiling.
  The run stopped at that node, as a failed node does; the two nodes after it did not run.
- Real-fal abort check, using the branch's `runFalQueueRequest` against `fal-ai/stable-diffusion-v35-large`
  and aborting after 1.5 s. The submit carried `X-Fal-Request-Timeout: 270`. The `PUT cancel_url`
  answered 202 `CANCELLATION_REQUESTED`, and the request ended `client_cancelled` with
  `inference_time: 0.0`, so nothing was billed.
- Not visible without worker logs (no AWS access from here): whether the timed-out sketch's cancel
  PUT was sent in the ECS run. The unit tests and the real-fal check above cover that path.
- Stability sketch, second run (`918ea8b5`): all seven nodes returned an image, the two multimodal
  ones (`gpt-4.1` with an image, `gpt-5-nano`) included. The sketch took 126 s (14:42:55 → 14:45:01):
  it would have failed under the old 120 s budget, and it passes under the 270 s deadline.
- Nothing hangs on our side in the sketch path. The branch's `runFalSketch`, run locally with the
  dev node's exact input and every fetch timed: fal held the request `IN_QUEUE` for ~115 s, the loop
  kept polling, then result fetch, image download and return took ~2 s. A direct probe of the same
  endpoint had finished in 15 s a few minutes earlier, so the wait is fal's queue, and it varies.
- The sketch output drifts from the source image. That is not a code defect. `influenceStrength` is a
  0–100 percent in the front (`ImageGenerator.tsx`, "Influence Strength: N%"), the back
  (`flux.service.ts` `/ 100`) and the worker alike. The dev test node was written through MCP with
  `0.5`, which reads as 0.5 %, so fal got `strength` ≈ 0.70, the most creative end of the band. Rerun
  locally with `100`: the body carried `strength: 0.6` and the output kept the source's angle,
  background and hull shape. Two findings came out of this:
  - **Fixed in A5 scope (user decision, 2026-09-25): the MCP schema did not state the scale.**
    `back/src/app-mcp/node-types/node-type-metadata.ts` typed `influenceStrength` as a bare `number`
    ("Defaults to 0."), so an agent could write a 0–1 fraction that the node silently reads as under
    1 %. On dev, 5 of the 33 `imageGenerator` nodes that carry a numeric `influenceStrength` hold a
    fraction between 0 and 1; 23 hold 1–100 and 5 hold 0. The description now says it is a 0–100
    percentage, divided by 100 before use, and that higher keeps more of the source image (true for
    all three sub-methods: sketch maps onto fal `strength` 0.7→0.6, style onto 0.85→0.8). Text only,
    no `minimum`/`maximum`, so nothing new is refused. Commit `e08bbe1e` on back branch `feat/868m0vkt4` (from
    `origin/production`); `node-type-contract.spec.ts` + `node-types.service.spec.ts` 113 passed,
    Biome clean, `tsc` shows the same 13 pre-existing errors as the base (`redis-io.adapter.ts`,
    `execution_logs.retention.spec.ts`). No new test: the change is documentation text, and a test
    asserting a string would protect nothing.
  - **Noted, not changed:** even at 0.6, SD3-medium img2img drops fine detail (the pizza toppings).
    The 0.6–0.7 band was validated on 2026-09-03; retuning it is a product call.

**Deliberately deferred, not a leftover.** This task's Done-when also said `imageGeneratorNode()` and
its dispatch case would be deleted. The dispatch case is gone — `imageGenerator` routes to the worker
via `isTemporalNode`/`MIGRATED_TEMPORAL_NODE_TYPES`. The method itself survives in
`back/src/app-api/flux/flux.service.ts` as a single, uncalled definition. `PORTED_FROM.md` records
this as intentional: "`imageGeneratorNode` itself is untouched dead code in the back … left in place,
matching the precedent of `scriptingNode`/`mathFunctionNode`/`outputControllerNode`." This is C1's
own established pattern applied deliberately — those three types' inline methods were left as dead
code the same way, once their dispatch was gone — not a clause this task missed. C1's task file now
lists `imageGeneratorNode` alongside them so the pattern is visible in one place rather than
rediscovered per node.

## Why

`imageGenerator` is architecturally identical to `commandTextNode`, which has been in the worker
in production the longest (analysis §3.2). Every contract it needs already exists:
`/worker/charge-tokens`, `/worker/validate-model-access`, `/worker/generate-file`.

**Corrected 2026-09-21 — the provider topology below was wrong; the real shape is six provider
systems, not six service methods.** The first draft described the cost as breadth across six
*paths* — `openAiService.createImageWithBilling`, `geminiService.generateImage`,
`replicateService.kandinsky`, and `imageService.{imageCore,sd,textToImage}` — describing back
services that predate this migration. Production instead ships six provider **systems** — `openai`,
`gemini`, `fal`, `stabilityai`, `ideogram`, `opensources` — split into `PROVIDER_BUILDERS` (the
AI-SDK path: `openai`/`gemini`/`fal`, pure `build<X>Spec()` functions feeding a shared
`ImageGenerateSpec`) and `DIRECT_HTTP_BUILDERS` (`stabilityai`/`ideogram`, each self-charging via a
`ctx.charge` closure, since charge-before-vs-after timing differs per provider and can't be
normalized). `opensources` (Kandinsky, via Replicate) is not built at all — it was ported, then
deprecated and deleted in the same worker task once confirmed broken in both dev and prod (HTTP 401
from Replicate, no viable replacement); the worker now refuses it outright with a typed
`UserConfigError` rather than reproducing the crash the back has. A migration to `fal` happened along
the way for several providers — `image-generator/IDEOGRAM_FAL_MIGRATION.md`,
`SKETCH_FAL_MIGRATION.md`, `STABILITY_FAL_MIGRATION.md` and `STYLE_FAL_MIGRATION.md` document it —
which the six-service-method framing had no way to anticipate.

<details>
<summary>What this section said until 2026-09-21 (kept for history)</summary>

> Its cost is **breadth** — six provider paths: `openAiService.createImageWithBilling`,
> `geminiService.generateImage`, `replicateService.kandinsky`, and
> `imageService.{imageCore,sd,textToImage}`.

</details>

## Scope

**In.** A shared image-provider layer the node consumes, with nothing node-specific inside it.
**Corrected 2026-09-24 — done, via extraction (Option A), on `feat/868m0vkt4` (pushed as `413db60`,
no PR yet):** `worker/src/modules/ai-provider/image/` now exists behind `ImageProviderService`; the
node module carries no provider call of its own, per the original Done-when clause. See the
2026-09-24 correction on leftover 1 above for detail, including the deliberately-deferred Option B
and the two out-of-scope duplications left as a follow-up (`ideogram/http.ts`/`stability/http.ts`).

**In.** Prompt resolution across `imageGenerator`'s seven prompt fields (`prompt`, `subject`,
`environment`, `tone`, `view`, `style`, `negativePrompt`) with placeholder interpolation against
the resolved run schema — the same pattern every migrated node with variable inputs already uses.
Shipped; no further work here.

**Out.** New providers, new models, changes to the prompt fields, or the billing formula.

**Out.** `imageReaderNode` (D24), and the OCR node that will replace it.

**Out.** Deleting `imageGeneratorNode()`'s body in `back`. Its dispatch case is already gone, which is
what determines behaviour; deleting the now-dead method follows the repo's own established precedent
(above) and is not required by this task.

## Steps

1. ~~Provider layer with one entry per path, ported from the back's services.~~ **Shipped, and as of
   2026-09-24 extracted into a shared `ai-provider/image/` layer** — done on worker branch
   `feat/868m0vkt4`, pushed as `413db60`, not yet opened as a PR. See leftover
   1's 2026-09-24 correction above.
2. ~~`imageGenerator` module; registry entry behind the flag; prove; flip.~~ **Shipped and in
   production.** Deleting `imageGeneratorNode()`'s body is deliberately not part of this step — see
   Scope.
3. ~~Leftover 2, narrowed 2026-09-25.~~ **Implemented on `feat/868m0vkt4` (`966f446`, `7e10e5e`),
   pending merge to `origin/main`.** The single five-minute ceiling is validated against production
   and recorded in `configs.ts`; Stability's fal poll budget is 270 s; fal jobs are cancelled on abort
   and on poll timeout. See leftover 2's later 2026-09-25 correction above.

## Verification

- **Negative control (required).** For each provider path, break the selection so it falls through
  to the wrong provider, and confirm a test catches it. Six systems means six ways to silently call
  the wrong API; a suite that only exercises the default path is not protection. (Shipped —
  `fal-provider.spec.ts` and its siblings cover this per-provider; re-confirm coverage extends to
  `stabilityai`/`ideogram`'s direct-HTTP path too before calling this clause done.)
- Billing parity: for the same prompt and model, `token_transactions` rows written by the worker
  must match what the inline path wrote. Compare against real stored runs.
- Model-access refusal: a model the user is not entitled to must produce the same refusal through
  `/worker/validate-model-access` as it does inline. **Measure before refusing** (PLAN §3.3.2) —
  run the check against real entitlements and drive false refusals to zero. **Corrected 2026-09-25 —
  measured on prod, no code change:** the user ran the 30-day entitlement query (`imageGenerator`
  runs × the user's active product flag for the provider). **No row has `entitled = false`**, so
  prod has no run that the inline path would have refused and the worker let through. The only
  other rows are 31 `openai` runs by 1 user with no active product (plan unresolved, not a refusal
  gap); all 31 errored. Whether they failed before or after the OpenAI call is not in that data.
  The user attributes the `openai` errors to configuration, as seen in QA: a missing model
  definition, or the tests that switched `supportsImageGenerationTool` on and off. Not measured.
  Adding a pre-generation check would refuse 0 real runs today, so none is added.
- **One layer, not a copy.** Confirm the module carries no provider call of its own. **Corrected
  2026-09-24 — passes, on `feat/868m0vkt4` (pushed as `413db60`, unmerged).** Every provider call
  moved to `worker/src/modules/ai-provider/image/image-provider.service.ts`; grep confirms the only
  fetches left in the node module are the two back callbacks in `store-and-charge.ts`
  (`/worker/store-image`, `/worker/charge-tokens`). Verified on the branch only — recheck once merged
  to `origin/main`. It remains leftover 1's own acceptance check.
- **Cancellation reaches the provider call (new, 2026-09-24).** Negative control: drop the
  `abortSignal` wiring at each of four points (`generateImage`, the abort rethrow, the poll wait, a
  status fetch) one at a time and confirm the corresponding test goes red; restore and confirm green.
  Done — see the 2026-09-24 tests-and-negative-controls note above.
- **Timeout measurement — open.** Before closing leftover 2, capture real per-provider duration data
  (M2's capture method could not; whatever replaces it must be able to) and set each provider's
  `startToCloseTimeout`/`heartbeatTimeout` above the slowest observed real call, not at a round
  number — the same "measure before refusing" discipline C3 applies to worker OAuth timeouts.
  **Corrected 2026-09-24 — a read-only measurement kit now exists**
  (`.claude/tasks/worker-flow-execution-epic/scripts/a5-image-timeouts/`) to capture this from
  Temporal visibility plus `node_executions`; still open pending the user running it against prod.
  **Corrected 2026-09-25 — narrowed:** one read-only query (`image-generator-duration-check.sql`)
  validates the single ceiling; the Temporal kit is no longer required. Plus a test, seen red first,
  that an aborted and a timed-out fal poll each send the `cancel_url` PUT. **Corrected 2026-09-25
  (later) — done on the branch:** the query ran (numbers in leftover 2's later correction), and the
  cancel tests were each seen red with the cancel removed.

### Dev verification, 2026-09-24

**Before:** `worker@develop` `1bd3632`. **After:** the extraction and cancellation wiring,
cherry-picked onto `origin/develop` as `feat/868m0vkt4-dev` (`7d5b256`) because `develop` already
carries 868ky2g5f's multimodal path, and fast-forwarded into `develop`. Deployed by `cicd_dev.yml`
run `36038189907`, finished 18:08 UTC. The automated checks ran through `run_agent`/`cancel_run` on
the agent "A5 dev smoke — image provider layer (868m0vkt4)" (`45c241c2-f667-4852-a982-651e648b758b`,
folder "Baseline 868hgvq5u"). Results were read from dev's `node_executions`, `generated_images` and
`token_transaction`. That agent runs its nodes one at a time in edge order and stops at the first
failure, so nodes were disconnected as each result was settled.

| Check | Result | Evidence / reason |
|---|---|---|
| A1 — worker boots with `ImageProviderService` | ✅ | The AI-SDK, direct-HTTP and multimodal paths all ran on the new image; no DI error |
| A2 — fal `flux-2-flash` | ✅ | Stored, charged once (0.0055, `used_tokens` 5), `execId` `d450fdfa` |
| A2 — ideogram `v3-turbo` | ✅ | 0.033 / 30, `execId` `b2914707` |
| A2 — ideogram remix (input image) | ✅ | 0.066 / 60, `execId` `9acaa506` |
| A2 — openai `gpt-image-1`, gemini `2.5-flash-image` (text and input image), multimodal `gpt-5-nano` | ❌ → ✅ after the `model_price` restore | Image generated and stored, then `charge-tokens` 500. Dev-data defect, not code: see "`model_price` soft-delete" below. After the restore, `gpt-image-1` + `gemini-2.5-flash-image` charged 40 + 39 (run `00217d0d`) |
| A2 — gemini with the coffee `.jpg` as input | ❌, provider refusal | `NoImageGeneratedError` in 1.5 s. Reproduced with a bare AI SDK call outside our code. The same edit with a PNG source generated in 9.6 s. Fixture rule: use a PNG source for the gemini input-image case |
| A2 — stability SD3.5 Large (`stability-ai-sd3.5-large` / `stability-ai-sd3`) | ❌, provider outage | Pre-charged once (0.0715), then `TimeoutError` after the 120 × 1 s budget. Reproduced locally with the worker's own `runFalQueueRequest`: fal kept `fal-ai/stable-diffusion-v35-large` at `IN_QUEUE` `queue_position: 0` for over 2 minutes, from 18:27 UTC on. Our polling behaved correctly |
| A2 — fal `flux-schnell` via `aiModel` | fixture error | `"Not Found"`: `flux-schnell` is neither `schnell` nor a key of `FAL_FLUX_MODEL_URL_MAP`, so fal gets an undefined endpoint. Unchanged by this task |
| A3 — cancel mid-generation, AI-SDK path (multimodal `streamText`) | ✅ | Cancelled 14 s into a ~20–24 s call. Rechecked 45 s later: no `generated_images` row, no charge, row untouched after `cancelledAt` (`execId` `31f3a9a4`). Before this task the activity ran on and stored the image |
| A4 — cancel stability after its pre-charge (sketch) | ✅ | One charge (0.055), no image; the row stayed cancelled past the moment the poll budget would have expired (`execId` `06c64bef`) |
| A5 — billing parity | ✅ | `cost` and `used_tokens` equal to earlier dev rows for the same keys: flux-2-flash 0.0055/5, ideogram-v3 0.066/60, v3-turbo 0.033/30, sd3.5-large 0.0715/65, sketch 0.055/50 |

**Manual QA on dev, 2026-09-24 (canvas).**
- **M1 — node Run and flow Run: ✅.** fal `flux-2-flash` and ideogram `v3-turbo` each stored one
  image and one charge per run (`execId` `e26ea211`, `346fbe50`, `6aa8c429`, `2a73f0c9`). openai
  `gpt-image-1` generated, then failed at charge (`bac0784c`, before the restore). `cost` is 0 on this
  test user's account for every charge, including all 176 before the deploy, so it is an account
  property, not a regression.
- **M2 — canvas stop button: ✅.** `gpt-5-nano` was cancelled 16 s in (`execId` `2023413c`): no image,
  no charge, no frozen screen, no refresh needed, and the flow stopped.
  - Two later re-runs without cancelling failed with "The model did not generate an image for this
    prompt" (`5d741194`, `c8224cc7`). That is 868ky2g5f's multimodal path; see the next paragraph.
  - `gpt-4.1` generated, then hit the same charge 500 (`c2038c53`).
  - The stability node used `stability-ai-sd3`, which runs on the stalled SD3.5 fal queue and timed
    out after its pre-charge (`5b163d42`).
- **M3 (connected input image) and M4 (multimodal with and without an input image): ✅, run
  through MCP.**
  - Agent "A5 dev M-tests via MCP (868m0vkt4)" (`0f4250af-f53d-4dc2-8af4-7908e47b0b05`), run
    `a35b3fb7`, 20:04–20:06 UTC, on dev worker `696caa3` (which contains `a29d073`), after the
    `model_price` restore.
  - A Data Input node feeds the prompt "create a pizza spaceship like a Star movie" to the first node
    and to `gpt-5-nano`, the same shape as the canvas flow that failed in M2.
  - The first node's image reaches the five edit nodes through a real edge into `inputPreview`, not
    a static URL, and the nodes run in one execution chain.
  - All 8 nodes succeeded: each stored an image and was charged once with the right key. The images
    were opened to check content, not only their URLs.

  | Node | Result | `execId` · charge (`used_tokens`) |
  |---|---|---|
  | M1 — fal `flux-2-flash`, prompt from the Data Input edge | ✅ pizza spaceship, so the Data Input value won over the node's fallback "a red bicycle" | `54f455ac` · flux-2-flash 5 |
  | M3 — gemini `2.5-flash-image`, connected image | ✅ the same ship, repainted blue: the edge-fed image was used | `73f82f43` · 39 |
  | M3 — openai `gpt-image-1`, connected image | ✅ | `a48792de` · 40 |
  | M3 — ideogram remix, connected image | ✅ | `86ee52c2` · ideogram-v3 60 |
  | M3 — stability sketch, connected image | ✅ | `e5f76d15` · 50 |
  | M4 — multimodal `gpt-4.1` + connected image | ✅ | `6e5b8087` · 70 |
  | M4 — multimodal `gpt-5-nano`, prompt from Data Input, no image | ✅ pizza spaceship, the prompt that failed twice in M2 | `e355eb64` · 70 |

  Run total 334 tokens, cost 0.3674. The canvas-only parts of M1/M2, namely the node's own Run button
  and the stop button, were covered by the user's canvas QA above.

**Fix shipped on the dev branch — force the `image_generation` tool (`a29d073`).**
- The multimodal path (`ai-provider/image/openai-multimodal-provider.ts`) called `streamText` with the
  tool but no `toolChoice`, so the chat model decided whether to generate.
- `buildPrompt` sends `"Prompt: create a pizza spaceship like a Star movie\n "`. Run locally with that
  exact text, `gpt-5-nano` answered with written prompt suggestions and no image in 2 of 3 runs, and
  generated every time with `toolChoice: { type: "tool", toolName: "image_generation" }`.
- The fix adds that `toolChoice` and a spec. Negative control: without the line the new test fails;
  restored, 9/9 pass.
- Committed on `feat/868m0vkt4-dev` and fast-forwarded into `develop`. Not on `feat/868m0vkt4` (PR
  #104), because the multimodal path is not on `main`: when 868ky2g5f goes to production it must
  carry this change.
- Verified on dev by M4 above (`e355eb64`).
- The deploy of `a29d073` itself (run `36051050941`) ended in failure:
  - `amazon-ecs-deploy-task-definition` reported "Deployment … not found after stabilization".
  - It was superseded, not broken. Another developer's push fast-forwarded `develop` to `696caa3`
    two minutes later, and that commit's deploy (run `36051255120`) replaced it and succeeded.
  - `696caa3` contains `a29d073`, including the `toolChoice` line.

**`model_price` soft-delete on dev — restored 2026-09-24 (dev only).**
- **What happened:** a single statement at 2026-09-11 19:58:42.434144 soft-deleted 130
  `model_price` rows and 51 `system_ai_models` rows. No code in any repo, current or historical, sets
  `deletedAt` on either table (every removal mechanism flips `isDeprecated`/`isActive`), so it points
  to an ad-hoc SQL run against dev.
- **Why charging failed:** `calculateTokens` (`back/src/app-api/product/product.service.ts:169-180`)
  throws a plain `Error` when the exact-key row is missing, which surfaces as an opaque 500 after the
  image is already stored.
- **Restored:** 13 rows that break charging for active models, after checking that none had a live
  duplicate:
  - `gpt-image-1` 40, `gemini-2.5-flash-image` 39, `gemini-3.1-flash-image-preview` 67;
  - the seven multimodal per-image rows at 70 (`gpt-4.1`, `gpt-4o`, `gpt-4o-mini`, `gpt-5`, `gpt-5.2`,
    `gpt-5.5`, `gpt-5-nano`, seeded by `AddImageGenerationToolPricing1788000000000`);
  - `claude-4-5-haiku-latest-output-tokens`, `claude-4-5-opus-latest-input-tokens` and
    `-output-tokens`.
- **Deliberately not restored:** `claude-4-sonnet-latest` and `claude-4-opus-latest`, which are
  deprecated but still referenced by 75 and 8 flow nodes.
- **Still to check:** staging and prod were not queried. The user runs the read-only check there: a
  `GROUP BY "deletedAt"` over `model_price`, plus the models above.

**Found during verification — pre-existing, out of this task's scope.**
1. **MCP `cancel_run` stops only the node in flight.**
   - `back/src/app-mcp/mcp-run.service.ts:246` cancels the tracked `currentWorkflowId` (one per-node
     `processSingleNode` workflow) and never calls `runCancellationService.requestCancel()`.
   - `CANCELLABLE_RUN_TYPES = ['canvas']` (`run-cancellation.service.ts:15`) means `flux.service.ts:3540`
     never checks cancellation for MCP runs.
   - The workflow settles a cancel gracefully (`settleCancelledNode`), so the loop dispatches the next
     node. Observed: run `37424a6d` went on to execute and charge three sibling nodes after its cancel.
   - The same pattern appears on dev on 2026-09-16..18 (`fluxBox`, `libraryNode`), before this task.
     The canvas stop (`execution_logs.service.ts:838`) does stop the run, which M2 confirms.
   - Fix belongs to `back` as its own task.
2. **fal queue requests are never cancelled on our side.**
   - `cancel_url` is never read (`ai-provider/image/{stability,ideogram}/http.ts`), on `main` and on
     the dev branch alike.
   - fal does not bill queue time, so the stalled request cost nothing (it ended `client_cancelled`,
     `inference_time: 0.0`). The risk is a request that starts after we stop polling and then bills
     for an image we discard.
   - Fix, for leftover 2: a best-effort `PUT cancel_url` without the aborted signal, on abort and on
     timeout, plus `X-Fal-Request-Timeout` (`start_timeout`) at submit. Apply it identically to both
     copies of the fal client. **Done 2026-09-25 as `7e10e5e`** on `feat/868m0vkt4`.
3. **`back` hardening, own task.**
   - Throw an `HttpException` with the missing key from `calculateTokens`.
   - Make `resolvePriceBaseKey`'s `linkedPrice` fallback deterministic
     (`model_price.service.ts:33-40`). Without the exact row, `gpt-image-1` either throws or charges
     the 0.005 text price instead of 40.
   - Check the price exists before calling the provider, not after the image is stored.
   - Add an idempotent data migration that re-seeds the rows above, following the
     `AddGptImage1FlatPrice` precedent.

## Done when

`imageGenerator` satisfies PLAN §3.4 (met) and: (1) its module consumes a **shared** provider layer
and carries no provider call of its own — **done on `feat/868m0vkt4` (pushed as `413db60`, no PR
yet), pending merge to `origin/main`** (was open as leftover 1; see the 2026-09-24 correction above);
(2) the single timeout is validated against production data and the numbers replace the
placeholder wording in `configs.ts`, and fal jobs are cancelled on abort and on poll timeout —
**done on `feat/868m0vkt4` (`966f446`, `7e10e5e`), pending merge to `origin/main`** (was leftover
2, narrowed 2026-09-25 from per-provider timeouts; measured with
`scripts/a5-image-timeouts/image-generator-duration-check.sql`); billing matches the inline
path on real runs (met); `imageGeneratorNode()`'s dispatch case is deleted (met) — its method body is
deliberately not deleted, per the established repo precedent (see Scope), and that is not an open
clause.

## Files

`worker/src/modules/ai-provider/image/` (`image-provider.service.ts`, `image-provider.types.ts` —
leftover 1, extracted here 2026-09-24 on `feat/868m0vkt4`, pushed as `413db60`) ·
`worker/src/modules/nodes/image-generator/providers/` (emptied by the extraction; kept as history in
`PORTED_FROM.md`'s provenance trail) ·
`worker/src/modules/nodes/image-generator/` (`image-generator.service.ts`, `store-and-charge.ts`,
`PORTED_FROM.md`) ·
`worker/src/modules/temporal/activities/activities.service.ts` (`withKeepAliveHeartbeat`,
`KEEP_ALIVE_HEARTBEAT_MS` — unchanged; the cancellation signal is read in `image-generator.service.ts` and
threaded by `ai-provider/image/image-provider.service.ts`) ·
`worker/src/modules/temporal/workflows/process-single-node.workflow.ts` (`cancelScope.run`) ·
`worker/src/modules/temporal/workflows/configs.ts` (`imageGeneratorActivity` — leftover 2) ·
`back/src/app-api/executions_logs/execution_logs.service.ts` (`cancelNode` signal) ·
`back/src/app-api/flux/flux.service.ts` (`imageGeneratorNode()` — dead, deliberately not deleted) ·
`.claude/tasks/worker-flow-execution-epic/scripts/a5-image-timeouts/`
(`image-generator-duration-check.sql` — leftover 2's one query, run on prod 2026-09-25;
`measure-image-generator-durations.mts`, `image-generator-duration-summary.sql`, `README.md` — the
original Temporal kit, kept, no longer required) ·
`worker/src/modules/ai-provider/image/stability/http.ts`, `ideogram/http.ts` (fal `cancel_url` —
leftover 2) · `back/src/app-mcp/node-types/node-type-metadata.ts` (`influenceStrength` scale, back
branch `feat/868m0vkt4`) · the A1 registry
