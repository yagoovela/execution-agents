# A5b — Make image-generation capability detectable, self-configuring and listed

**Goal:** every model that can generate images — a native image model, or a chat model that
generates through a tool — is recognised as such from one stored capability, offered in the Image
Generator's picker, executed with the right call (including `toolChoice`) by the worker, and listed
with its capabilities and tools in the app and in MCP. A newly approved model that has the
capability works by default, without a code change, as the model catalog was designed to allow.

**Added 2026-09-25**, split out of A5 by user decision. It complements A5 rather than replacing any
of it: A5 delivered the shared image provider layer the worker calls; A5b makes sure the models that
layer is asked to run are the ones the catalog says can run, and that the catalog can say so for a
model nobody has hand-written yet.

**ClickUp:** [868m9zfba](https://app.clickup.com/t/868m9zfba) (subtask of the epic parent, `waiting_on`
868m0vkt4, linked to 868ky2g5f/868m3pkyu). **Unblocked, 2026-09-25:** A5's code is finished (worker PR
#104 and back's `feat/868m0vkt4`, both QA'd) though **not yet merged to `main`/`production`** — confirmed
directly with `git merge-base --is-ancestor` rather than assumed, since ClickUp's own description still
read "pending merge to prod" at the time. User decision: use A5's branches as the base rather than wait
for the prod merge. Implementation worktrees for back and worker (`feat/868m9zfba`) were reset onto
`origin/feat/868m0vkt4` (confirmed `worker/src/modules/ai-provider/image/` is present there); front
(`feat/868m9zfba`) has no A5 counterpart and stays on `origin/production`.

**Depends on:** A5 (PR #104 — the shared `ai-provider/image/` layer), and 868ky2g5f reaching
production (the multimodal chat-with-tool path; today on dev only — see *Where each piece is today*).
**Blocks:** the planned "image-studio" consolidation (not yet scoped or dated, 2026-09-25 — a single
component meant to centralize image-generation across every native and multimodal model). Image-studio
should consume the capability signal (`supportsImageOutput` / `supportsImageGenerationTool`) and the
`tools` projection this task builds, rather than re-deriving model eligibility itself — the exact
per-layer duplication this task exists to end (see *Why*). Nothing in the current epic (C1, B5) is
blocked by or blocks this task — see *Impact on image-studio* below for what a future image-studio
build should and should not reimplement.

## Why

A5's dev verification (2026-09-24) found that `gpt-5-nano` on the multimodal path answered the
prompt with written prompt suggestions and no image in 2 of 3 runs. The fix, `a29d073` on
`feat/868m0vkt4-dev`, forces the tool:

```ts
// worker/src/modules/ai-provider/image/openai-multimodal-provider.ts:66
toolChoice: { type: "tool", toolName: "image_generation" },
```

It is correct today only because its sole caller already checked the capability. The function
itself does not know whether the model supports the tool — nothing threads that fact to it. That is
the small symptom. Tracing it back found the larger one: the product has **no single, trustworthy
answer to "can this model generate images, and how?"**, and each layer that needs the answer
restates its own:

| Layer | What it uses instead of a shared capability | Consequence for a newly approved model |
|---|---|---|
| Catalog sync (back) | `gateway-model-mapper.ts` never computes an image capability; `SYNCED_CAPABILITY_FIELDS` (`ai-model-sync.service.ts:47`) omits `supportsImageGenerationTool` | Approved without the flag; a human must remember to toggle it |
| Catalog (back) | `modelType = 'Image'` — overloaded: it also marks models that only *read* images | Cannot be used as "generates images" (see *Measured*) |
| Picker (front) | `openAiModelsImage` / `geminiModelsImage` literal arrays (`ImageGenerator/constants.ts:84-115`) for native models; `supportsImageGenerationTool` only for the multimodal branch, and only for `openai` | A new native image model never appears |
| Worker, native OpenAI | Hardcoded `gpt-image-1` for the call and the billing; `nodeData.aiModel` is only persisted | A new OpenAI image model is never called even when selected |
| Worker, multimodal | Reads `supportsImageGenerationTool` to route, then forces `toolChoice` unconditionally | Correct only while the one caller keeps checking |
| MCP | `ModelItem` (`mcp-server/src/upstream/back-http-client.service.ts:247`) carries `supportsVision`/`supportsReasoning` only | An agent cannot tell which models generate images or which tools any model has |

The design intent this task honours: the catalog sync (`AiModelSyncService`, nightly,
`sync-ai-models-from-gateway.service.ts:17`) proposes new models, a human approves, and an approved
model is usable. That works for text capabilities — `supportsWebSearch`, `supportsStructuredOutput`,
`isVisionModel` and the rest are derived from the gateway and kept current. Image generation was
left out of that loop, so for images the loop ends at "approved" instead of "usable".

## Measured

**Gateway catalog, 2026-09-25**, `https://ai-gateway.vercel.sh/v1/models` (public, the same source
the sync reads), 390 models, script `scripts/a5b-image-capability/measure-gateway-image-capability.py`:

- **Native image models are advertised.** 34 models have `type: "image"`, every one tagged
  `image-generation` (e.g. `openai/gpt-image-1`, `gpt-image-1.5`, `gpt-image-2`, `meta/muse-image-1.0`,
  `bfl/flux-2-pro`, `recraft/recraft-v4`). The mapper already maps `type: image` to `modelType: 'Image'`.
- **Chat models that output images are advertised.** 7 `type: "language"` models carry
  `modalities.output: ["text","image"]` and the `image-generation` tag — the five Gemini image
  models (`gemini-2.5-flash-image`, `gemini-3-pro-image`, `gemini-3.1-flash-image`,
  `gemini-3.1-flash-image-preview`, `gemini-3.1-flash-lite-image`) and two `quiverai` models. The
  mapper reads `modalities.input` only, so this signal is dropped today.
- **OpenAI's image tool is not advertised at all.** Of 62 OpenAI language models, the gateway marks
  **none** with image output or the `image-generation` tag — including all 12 that OpenAI's documentation
  lists for the Responses API `image_generation` tool (`gpt-5.5, gpt-5.4-mini, gpt-5.4-nano, gpt-5.2,
  gpt-5, gpt-5-nano, o3, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini`, per
  `1788200000000-AddMissingOpenAiImageToolModels.ts`, checked 2026-09-01). This matches the
  catalog-freshness spec's finding (`.claude/tasks/ai-model-catalog-freshness-check/spec.md`).
- **No heuristic reproduces the OpenAI list.** "`tool-use` + `vision`" flags 56 models; excluding the
  21 `-fast` variants the sync already skips (`GATEWAY_ID_EXCLUSION_PATTERNS`), 35 against 12
  documented — 23 flagged without documentation (`gpt-5-pro`, `gpt-5.x-codex`, `o3-pro`, `gpt-5.6-*`,
  `gpt-6-*`, ...). It misses none, so it is a candidate generator, not a rule.

**Dev catalog, 2026-09-25** (`system_ai_models`, read-only):

- **Correction, 2026-09-25 (this task's own earlier draft overstated this):** `modelType = 'Image'`
  contamination is smaller than first measured and already half-fixed. Migration
  `1787946296892-AddImageGenerationToolAndDeprecationForecast.ts` (dev/master, **not yet in
  production**) already reclassified 6 of 8 non-generating rows to `'Text'` — `claude-3-opus-20240229`,
  `pixtral-12b`, and 4 `gpt-4-*-preview`/`gpt-4-turbo-preview` snapshots — citing the same
  `text-node-multimodal-image-generation` design pass this task's own research kept independently
  re-deriving. Only 2 remain `'Image'` and unresolved by design: `ideogram-describe-image`, `blip2` —
  left out **on purpose**, "pending further verification," the same "unverifiable, don't guess"
  discipline this task's own decisions follow. Gemini's `gemini-2.5-flash-image` and
  `gemini-3.1-flash-image-preview` are correctly `'Image'` already, with no contamination.
- `supportsImageGenerationTool = true` on exactly the 7 rows the migration backfilled
  (`gpt-4.1, gpt-4o, gpt-4o-mini, gpt-5, gpt-5.2, gpt-5.5, gpt-5-nano`); the 5 documented in
  `1788200000000` are dev-only rows added later.

**Dev stored nodes, 2026-09-25** (`flows_nodes`, live canvases, `type = 'imageGenerator'`):

- `openai`: `gpt-image-1` 390 nodes / 242 flows; `dall-e-3` 42 / 37; `dall-e-2` 1. All run as
  `gpt-image-1` today.
- `openai` with a text model the catalog does **not** flag: `o3-pro` 2, `gpt-5.5-pro` 2, `gpt-5.2-pro`
  1, `gpt-5.6-sol` 1 — they fall through to the native path and silently produce a `gpt-image-1` image.
- `openai` with a flagged text model: `gpt-5-nano` 3, `gpt-4.1` 1.
- `gemini`: `gemini-2.5-flash-image` 12, `gemini-3.1-flash-image` 2, `gemini-3-pro-image` 2 — the last
  two have **no** catalog row and still work, because the Gemini provider passes `aiModel` straight
  through.
- `anthropic` / `claude-3-opus-20240229` 2 — a non-image model stored on an image node.

These counts are the false-refusal baseline for every rule below: **any change that refuses or
hides one of these nodes must say so and why, on this data, before it ships** (PLAN §3.3.2).

## Corroboration from ClickUp — where the 12-model OpenAI list actually came from

Two closed ClickUp tasks answer, directly, the question this task's own research could only infer:
**868ky2g5f** ("Enable image output for multimodal models" — the feature this capability serves) and
**868m3pkyu** ("Add `supportsImageGenerationTool` as an admin-manageable field" — the toggle this task's
*Where each piece is today* table already cites). Their comment threads are the origin of the flag,
not just its consumer.

- **The capability is a human audit against OpenAI's own docs, not a derivation.** 868ky2g5f's
  2026-08-31 comment: *"Audited all 33 OpenAI rows in `system_ai_models` against OpenAI's docs for
  Responses API `image_generation` tool eligibility (developers.openai.com/api/docs/guides/tools-image-generation,
  checked 2026-09-01). The 7 models already flagged ... are all correct — no false positives."* The
  same audit then added the 5 rows in `1788200000000-AddMissingOpenAiImageToolModels.ts` and
  **deliberately left two candidates unflagged** — `gpt-5.4-2026-03-05`, `gpt-5-mini` — because *"the
  docs don't clearly confirm they're the same models the eligibility list refers to."* That is
  D-A5B-1's "unknown stays unknown" principle, already practiced once, by hand, before this task
  existed. It directly confirms this task's finding that no gateway signal exists for the tool: the
  audit's author had the same catalog and the same gateway available and still had to read OpenAI's
  prose page.
- **This precedent is the strongest evidence for D-A5B-1 Option B.** The "one named rule module with
  its source and date" the recommendation proposes is not a new invention — it is this exact audit,
  formalized into code instead of a one-off ClickUp comment that the next model release will not
  reread. Rollout was staged the same way B proposes staging it: Gemini's `gemini-2.5-flash-image`
  first (a teammate, 2026-09-03: *"This is only just for gemini-2.5-flash-image right now? ...
  Other providers like Open AI do not work"*), OpenAI's 12 added afterward once audited.
- **A third silent-drop point, found and fixed once already — the pattern must not repeat for the new
  field.** 868m3pkyu's follow-up comment (2026-09-10): `back/src/app-api/model_price/dto/responseModelPrice.dto.ts`'s
  `ResponseSystemAiModelDto` never declared `supportsImageGenerationTool` with `@Expose()`. Since
  `BaseController.success()` serializes with `plainToInstance(..., { excludeExtraneousValues: true })`,
  the field was silently stripped from every read even though the entity, the patch DTO and the
  `/technologies` DTO all handled it — the PATCH persisted the value, but no read path, including the
  admin UI, ever showed it back. Fixed in back PR #1954 (`@Expose()` added, confirmed on both `origin/master` and `origin/production`
  2026-09-25) with a negative-controlled spec. **`supportsImageOutput` (D-A5B-3) needs the same
  `@Expose()` in the same DTO, or it repeats this exact bug for the new field.**
- **A fourth must-touch file this task had not named: the PATCH allowlist.** The admin-wiring skill
  written after 868m3pkyu (`system-ai-model-capability-sync`, on branch/worktree
  `system-ai-model-capability-sync`, not yet merged into the main skills tree) documents
  `back/src/shared/system-ai-model-upsert-fields.ts`'s `SYSTEM_AI_MODEL_PATCH_KEYS` array (confirmed on
  `origin/master` and `origin/production`, 2026-09-25): a field absent from that array is silently
  dropped by `PATCH /model_price/:id/system-ai-model` with no error. `supportsImageGenerationTool` is
  already in it; `supportsImageOutput` will need adding, alongside `ModelPriceSystemAiModelCapabilityBody`
  and the two payload-builder functions in the same file.
- **As of 2026-09-10, the admin toggle had never actually been used.** 868m3pkyu's DTO-bug comment:
  *"all 22 rows currently flagged true share one identical timestamp from the original backfill
  migrations — no isolated row shows a real admin-UI save landed."* The toggle exists and is wired
  correctly since PR #2161/#1954, but every `true` value in the catalog, before and after, has come
  from a migration seeded by a manual audit — corroborating that D-A5B-1's "approval screen shows a
  pre-filled value" is how this capability is actually set in practice, not a hypothetical.
- **The admin-wiring skill's own stated boundary is exactly this task's job.** Its "What this does not
  cover" section: *"Whether the flag should gate behavior for providers beyond the one it currently
  does (e.g. `supportsImageGenerationTool` only takes effect for `aiSystem === 'openai'` today ...) —
  a behavior question, not an admin-wiring one."* That is Scope items 9-11 verbatim. The skill should
  still be run for Scope items 6 and 8 (admin surfaces, DTO/allowlist exposure of the new
  `supportsImageOutput` field) once it exists — see Steps.

## Where each piece is today

| Piece | prod | dev |
|---|---|---|
| `system_ai_models.supportsImageGenerationTool` column | yes (`1789200000000`) | yes |
| 12-model OpenAI backfill (`1788200000000`) and Gemini flag rows (`1788300000000`) | no | yes |
| `modelType` cleanup — 6 vision-only rows reclassified `Image → Text` (`1787946296892`) | no | yes |
| `ResponseSystemAiModelDto.supportsImageGenerationTool` `@Expose()` fix (PR #1954) | yes | yes |
| `SYSTEM_AI_MODEL_PATCH_KEYS` includes `supportsImageGenerationTool` | yes | yes |
| Admin toggle (`AiModelsManagementPage.tsx`, 868m3pkyu) | yes | yes |
| Newer admin panel (`features/admin-panel/pages/ai-models/`) | does not exist | exists, without the flag |
| Front multimodal branch in `SettingsModal.tsx` | no | yes (`main`) |
| Worker multimodal path + `isMultimodalTextModel()` | no (`origin/main` has none) | yes (`feat/868m0vkt4-dev`, via `develop`) |
| Worker `toolChoice` forced | no | yes (`a29d073`) |
| MCP capability fields | no | no |

## Why the worker multimodal path never reached prod, and why A5b absorbs it

This is a real, previously-unknown gap, root-caused with `gh pr view`/`git merge-base --is-ancestor`
rather than assumed from branch names or ClickUp's own status label — 868ky2g5f reads **"deployed on
live"** in ClickUp, which is stale/incorrect measured against the worker repo's actual `main`: `git
branch -r --contains 6106fc4` and `grep -i multimodal` against `origin/main` both come back empty.

**The cause — a 12-second PR-merge race.** 868ky2g5f's worker-side work landed as five commits on
`feat/868ky2g5f` (`6106fc4` .. `a29d073`, 2026-09-01 to 2026-09-24), merged into an intermediate branch
`feat/868hgvq5u` by PR #87 (`mergedAt: 2026-09-09T13:20:11Z`, merge commit `98c2aa1`). Twelve seconds
*earlier* — `2026-09-09T13:19:59Z` — PR #93 had already merged `feat/868hgvq5u`'s then-current state
into `main` (merge commit `ae6522d0`). `main`'s cut landed one merge-window too early to include
868ky2g5f's fold-in: `git merge-base --is-ancestor origin/feat/868hgvq5u origin/main` returns NO, and no
follow-up PR was ever opened to reconcile the gap — `feat/868hgvq5u` (and the multimodal work riding on
it) has sat unmerged to `main` since. A5's own branch (`feat/868m0vkt4`) branched from a lineage that
also missed this fold-in, which is why the multimodal file is absent there too, independent of A5's
later provider-layer refactor (`413db60`) — confirmed via `git show --stat 413db60 | grep -i
multimodal` (no output): A5's refactor moved the native providers, never touched a file it didn't have.

**What this is not.** A sibling feature — the ideogram/stability→fal migration — shares a duplicate
commit message ("migrate ideogram generate/remix to fal", `09ddad3` on the 868ky2g5f/868hgvq5u lineage
vs. `8ebc333` on `feat/868m0vjwk`) but is a red herring: `8ebc333` **is** an ancestor of `origin/main`
(confirmed), meaning that work reached prod through a different, unaffected sibling branch. Only
868ky2g5f's multimodal-image commits were caught by the race.

**Why A5b absorbs the fix instead of a separate worker-repo PR.** The five commits are surgical
(`generateOpenAiMultimodalImage`, the `isMultimodalTextModel` gate, connected-input-image support,
provider-usage-based billing, and the `toolChoice` force fix) and are exactly what A5b's own scope items
9-11 need working before they can be exercised — waiting for an independent PR against `main` would
block this task on a fix that has no other owner and no open PR today. Per the explicit constraint that
A5b's implementation must build on **A5's own branch** and nothing from `develop` (A5's branch, not
`develop`/`feat/868m0vkt4-dev`, is the base — see *Where each piece is today*), the five commits were
cherry-picked in their original chronological order (`6106fc4` → `24706cb` → `be8f1bd` → `59fdcd5` →
`a29d073`) directly onto the A5b worker worktree's `feat/868m0vkt4` base, explicitly excluding
`7d5b256` (the provider-layer-extraction refactor, already covered by A5's own `413db60`) and the
ideogram/stability-fal commits (already on `main` via the `8ebc333` sibling lineage above). Each
conflict this produced was a mechanical consequence of cherry-picking pre-refactor code onto A5's
already-refactored `ImageProviderService` layer — e.g. `PROVIDER_BUILDERS`/`buildOpenAiSpec` calls
resolved to `this.imageProviders.generate(...)`, and a signal-aware `fetchSourceImageBuffer` A5 had
already added independently was kept over the incoming signal-less version — never a case of picking
old behavior over new. This does not create a second PR debt: it's the same fix, applied once, riding
on the branch that will eventually reach prod anyway; whoever reconciles `feat/868hgvq5u` into `main`
later will find the work already shipped via A5b's PR and can close that gap as a no-op.

## Decisions

### D-A5B-1 — Where the "generates images" capability comes from

- **A. Gateway signal only.** Native (`type: image`) and chat-output (`modalities.output` has `image`,
  or the `image-generation` tag) are derived by the sync. OpenAI's tool support stays a manual toggle.
- **B. A + one named rule for provider tools.** Same as A, plus a single back module that states
  which provider tools exist and how a model qualifies (for OpenAI's `image_generation`: the
  documented list, kept in one file with its source and date). The sync uses it to **pre-fill** the
  flag on the add-model proposal; the approving admin sees it and can change it.
- **C. Probe.** On approval, call the provider once with the tool forced and a tiny prompt; set the
  flag from the result. Real, but costs a paid call per model and needs a key per provider.

**Recommendation: B, with C's cost objection now measured and mostly retracted for OpenAI.** A alone
leaves every new OpenAI model at "approved but not usable", which is the reported problem. B keeps the
human approval the catalog was designed around, moves the knowledge to the approval screen instead
of someone's memory, and states the OpenAI list exactly once. **This is not a new pattern**:
868ky2g5f's 2026-08-31 comment is this exact audit, done once by hand against OpenAI's docs, including
leaving two ambiguous models unflagged rather than guess — B formalizes what already happened instead
of proposing something untried (see *Corroboration from ClickUp* above).

**Tested, 2026-09-25 — C's "spends money on a guess" objection does not hold for OpenAI specifically.**
Live calls to `POST https://api.openai.com/v1/responses` with `tools: [{"type": "image_generation"}]`
and `tool_choice: {"type": "image_generation"}` (a tiny prompt, "draw a small red circle"):

| Model | HTTP | Result | `usage` |
|---|---|---|---|
| `gpt-3.5-turbo` (known ineligible) | 400 | `invalid_request_error`: *"Tool 'image_generation' is not supported with gpt-3.5-turbo."* | `None` — **no tokens billed** |
| `gpt-4.1-nano` (known eligible) | 200 | `completed`, `output: [image_generation_call, message]` | 4038/32/4070 |
| `gpt-5-mini` (868ky2g5f left unflagged — docs unclear) | 200 | `completed`, `output: [reasoning, image_generation_call, message]` | 2762/481/3243 |
| `gpt-5.4-2026-03-05` (868ky2g5f left unflagged — docs unclear) | 200 | `completed`, `output: [image_generation_call, message]` | 2316/35/2351 |

OpenAI validates tool-model compatibility **before** generating: an ineligible pairing is rejected with
`HTTP 400` and `usage: None`, at zero token cost — the same shape as any other bad-request rejection,
not a billed attempt. This means a probe is not "the only fully automatic option but spends money on a
guess" (the original framing above) — for a model that turns out ineligible, it costs nothing; for a
model that turns out eligible, it costs one real generation (~2-4k tokens, a few cents), same as the
feature actually being tested. It also **resolved both models 868ky2g5f's manual audit left
ambiguous** — `gpt-5-mini` and `gpt-5.4-2026-03-05` are both confirmed eligible, something reading
OpenAI's prose page could not settle.

This does not replace B; it removes B's manual-audit step for OpenAI. **Revised recommendation:** when
the sync proposes a new OpenAI language-type `ADD_MODEL`, run this probe once (not nightly, not against
the existing catalog — only against models with no probe result yet) and use its outcome to pre-fill
`supportsImageGenerationTool` on the proposal, replacing "read OpenAI's docs by hand" with an
automatic, self-verifying check; keep the named rule module (B) as the audit trail / source-of-record
and as the mechanism for providers without this validate-before-generate behavior. The 23 heuristic hits
neither confirmed nor rejected by a probe are still **not** pre-filled true — the "unknown stays
unknown" principle is unchanged, it is just resolved automatically now instead of by hand where OpenAI's
API allows it.

**Limits of the probe, asked and answered 2026-09-25 (do not build on any of these without re-verifying):**

- **Not monotonic by release date — do not assume every model newer than a known-eligible one inherits
  the capability.** The documented 12-model list itself already contradicts a straight release-date
  line: it includes `gpt-4o`/`gpt-4o-mini` but not `gpt-4-turbo` or `gpt-3.5-turbo`. The sync's own
  `GATEWAY_ID_EXCLUSION_PATTERNS` already excludes `-fast` variants precisely because a newer ID can
  behave differently from its base model. A pure-reasoning release (`o1`, `o1-mini`, `o3-mini`) or a
  specialized future model (safety-tuned, audio/realtime-first) could ship without the tool despite
  being newer. **This is exactly why probing every new model once, rather than assuming inheritance, is
  the recommendation** — the free-rejection property removes the cost argument for assuming instead of
  checking.
- **No capability listing exists to shortcut the probe.** Checked both candidate sources: OpenAI's own
  `GET /v1/models` returns only `id`, `created`, `owned_by` — no tool/capability field. The AI SDK
  (Vercel) adds no OpenAI-specific capability metadata either; it relays the call to the provider,
  which is the same gap this task's own gateway measurement already found (*Measured*, above — the
  gateway carries no signal for this tool). The probe call **is** the check; there is no cheaper
  parameter to read instead of making it.
- **Scoped to OpenAI only — not validated, and not assumed, for any other provider.** The specific
  behavior this task leans on — an incompatible tool+model pairing rejected with `HTTP 400` and
  `usage: None` *before* generating — is a detail of OpenAI's Responses API, observed only there.
  Whether Anthropic, Gemini (if it ever exposes a discrete image tool rather than native image output),
  or a future provider rejects the same way, at the same zero cost, is unverified and must not be
  assumed. Gemini's image capability is already handled differently and outside this problem entirely
  (D-A5B-3 — native `modelType = 'Image'` rows, not a tool over a text model). Providers outside the
  gateway (`fal`, `stabilityai`, `ideogram`, `bfl`, `recraft`, ...) are already Out of Scope for other
  reasons (see *Scope*); this note keeps their probe status explicitly unverified rather than silently
  inheriting OpenAI's finding.

**No re-incidence for a pending or rejected proposal.** `AiModelSyncProposal` rows for `ADD_MODEL` are
re-proposed nightly until an admin decides them (per the existing proposal flow), so pre-filling from a
fresh probe every night would re-run — and, for an eligible model, re-bill — the same generation on
every undecided proposal. The probe result (eligible / ineligible / unknown, with the date) is persisted
**on the proposal row itself** the first time it is probed; a subsequent night's sync checks that cached
result before probing again, and only probes a `(model, provider)` pair that has never been probed. This
is what makes "mark it as tested so it never repeats" literally true, including for a proposal nobody
has approved or rejected yet — not just for a model that has already been added to the catalog.

### D-A5B-2 — How the sync treats an existing row

The gateway can never see OpenAI's tool, so a naive sync would flip a human-set `true` back to `false`
every night. **Recommendation:** the sync may raise the image capability to `true` from a gateway
signal; it **never lowers** it. A lowering is only proposed (a capability-change proposal), never
applied.

### D-A5B-3 — Separate "outputs images" from "has an image tool"

**Not because `modelType = 'Image'` is contaminated** — that is mostly fixed already (see the
*Measured* correction above) — **but because `modelType` is a billing category, and reclassifying a
model into it has a cost a capability flag doesn't.** `modelType` gates
`hasUsablePricing`/`perImageFluxConversion` in `gateway-model-mapper.ts:237` and the inline routing at
`gemini.service.ts:636`; a chat model billed per token cannot also become `modelType = 'Image'`
(billed per image) without breaking its own text billing the rest of the time it is used as a chat
model. That is the real, structural reason `supportsImageGenerationTool` had to be a boolean on a
`'Text'` row rather than a reclassification, and why a merged "generates images" signal cannot simply
be `modelType`.

The product has already solved "a chat model that also produces images" two different, ad hoc ways —
Gemini's image models became their **own separate `'Image'`-type catalog rows** (per
`1788300000000`'s own comment); OpenAI's became a **boolean on the existing `'Text'` row**
(`supportsImageGenerationTool`). Nothing currently lets the sync recognise either shape from the
gateway's own signal (`type: language` + `image` in `modalities.output`) and decide which of the two
the product wants — a human did it by hand for Gemini, and by manual audit for OpenAI (see
*Corroboration from ClickUp*). **Recommendation:** a new boolean `supportsImageOutput`, read by the
picker and the worker directly (`supportsImageOutput || supportsImageGenerationTool`), so a future
provider whose model behaves like Gemini's — a chat model that emits images inline, not through a
discrete tool call — is recognised the same way regardless of whether the catalog also gives it its
own `'Image'` row. `modelType = 'Image'` stays what it already is — a billing category, cleaned up but
not repurposed. The backfill migration is decided row by row against the dev and production catalogs and the
stored-node counts above, never by `modelType`.

### D-A5B-4 — The shape of "all tools of a model"

**Recommendation:** one back function derives `tools: string[]` from the stored capability columns —
`image_generation`, `image_output`, `web_search`, `structured_output`, `vision_input`, `reasoning` — and
every listing uses it: `TechnologiesDto`, `CompanyTechnologiesDto`, and the MCP internal models
endpoint. The raw booleans stay exposed as well. No second list anywhere; the worker keeps reading
the booleans from `system_ai_models`.

### D-A5B-5 — MCP writes an image model that cannot generate images

MCP's `add_node`/`update_node` already validates `aiModel` against the workspace's enabled models
(`mcp-write.service.ts:1948-1959`). Refusing a non-image model on an `imageGenerator` would refuse
the 6 unflagged OpenAI text-model nodes and the 2 `claude-3-opus` nodes measured above, which run
today. **Recommendation:** no refusal; return a warning naming the capability the model lacks, and
make `list_ai_models` able to filter by capability so agents pick correctly up front.

## Scope

**In — back.**
1. `gateway-model-mapper.ts`: derive `supportsImageOutput` from `type: image`, `modalities.output`
   and the `image-generation` tag; add it and the pre-filled `supportsImageGenerationTool` (D-A5B-1 B)
   to `MappedGatewayModel` and to the `ADD_MODEL` proposal payload, so approval creates the row with
   both.
2. The provider-tool rule module (D-A5B-1 B): a named source-of-record for the OpenAI list plus, for
   OpenAI specifically, a one-time probe call against `/v1/responses` for any new OpenAI language
   model the sync has not yet probed, used to pre-fill `supportsImageGenerationTool` on the
   `ADD_MODEL` proposal (D-A5B-1, "Tested 2026-09-25"). The probe result is persisted on the proposal
   row itself, keyed by model, so a pending or rejected proposal is never re-probed (and, for an
   eligible model, never re-billed) on a later night's sync (D-A5B-1, "No re-incidence"). Providers
   without OpenAI's validate-before-generate behavior fall back to the rule module alone.
3. `ai-model-sync.service.ts`: raise-only sync of both image fields (D-A5B-2).
4. Migration: `supportsImageOutput` column plus the reviewed backfill (D-A5B-3), generated with
   `pnpm migration:generate`, data rows NOT-EXISTS/idempotent.
5. The `tools` projection (D-A5B-4) in `TechnologiesDto`, `CompanyTechnologiesDto`,
   `mcp-resources.service.ts` `listModels`.
6. The proposal payload carries both image fields, and the approval decision can override them, so the
   admin confirms them instead of remembering them. `supportsImageOutput` added everywhere
   `supportsImageGenerationTool` already appears in `system-ai-model-upsert-fields.ts`
   (`ModelPriceSystemAiModelCapabilityBody`, both payload-builder functions, and
   `SYSTEM_AI_MODEL_PATCH_KEYS` — a field missing from that array is silently dropped by PATCH, per
   868m3pkyu's admin-wiring skill) and `@Expose()`d on `ResponseSystemAiModelDto`
   (`responseModelPrice.dto.ts`) — 868m3pkyu shipped exactly this omission once for
   `supportsImageGenerationTool` (PR #1954) and it must not repeat for the new field.

**In — front.**
7. Image Generator picker: native and multimodal models from `technologies` by capability, per
   provider; `openAiModelsImage` / `geminiModelsImage` removed. A node whose stored `aiModel` is no
   longer offered still shows its value (no silent reset).
8. Both admin surfaces expose `supportsImageOutput` and `supportsImageGenerationTool`, following the
   same touch points `AiModelsManagementPage.tsx` already uses for `isVisionModel`/`supportsTemperature`
   (create/edit form defaults, both edit-state hooks, `handleSave`/`handleCreate` payloads, the detail
   view, the `Switch` control) and the matching fields on `AdminAiModelsService.ts`'s request/response
   types.

**In — worker.**
9. `ImageProviderMultimodalRequest` carries the capability; `generateOpenAiMultimodalImage` sets
   `toolChoice` from it and refuses with a `UserConfigError` before `streamText` when it is false.
10. Native OpenAI: use the node's `aiModel` for the call and the billing when it is an active catalog
    model with `supportsImageOutput`; otherwise keep `gpt-image-1` — so the 43 `dall-e-*` nodes keep
    today's behaviour and a newly approved OpenAI image model is actually called.
11. Routing reads both capabilities from one query instead of `isMultimodalTextModel()` alone.

**In — MCP.**
12. `ModelItem` and `list_ai_models`: the capability booleans and `tools`, plus an optional
    capability filter; tool description updated; unit specs per the mcp-server CLAUDE.md checklist.
13. `imageGenerator` metadata description points agents at the capability filter; D-A5B-5's warning.

**Out.**
- Providers the gateway does not cover (`fal`, `stabilityai`, `ideogram`, `bfl`, `recraft`, ...): their
  catalogs, fal endpoint maps (`fal-model-map.ts`) and new builders. A new provider still needs code.
- The text generator's `supportsWebSearch` gap (`build-web-search-tools.ts`) — its own task.
- Charge hardening (missing `model_price` rows) and the model-access check before generation — their
  own tasks; A5b relies on them for a newly approved model to bill, and says so in its Verification.
- Timeouts (A5 leftover 2).

## Steps

1. **Measure first, both environments.** Re-run the gateway script; run the catalog and stored-node
   queries on dev; hand the same read-only queries to the user for production. Classify every row the
   backfill touches and every stored node the picker or worker change affects as "unchanged",
   "gains capability" or "loses something", and drive "loses something" to zero or name it.
2. **Back: capability and sync** (Scope 1-4, 6), behind the existing approval flow. Includes promoting
   `1787946296892`'s `modelType` cleanup to production (it is dev/master-only today) and deciding
   `ideogram-describe-image`/`blip2` — resolve if verifiable, otherwise leave them, named, as that
   migration already does.
3. **Back: `tools` projection** (Scope 5).
4. **Worker** (Scope 9-11), on top of A5 and 868ky2g5f.
5. **Front** (Scope 7-8); run the `system-ai-model-capability-sync` skill against `supportsImageOutput`
   once it is merged into the main skills tree — it is the checklist 868m3pkyu's own gap produced, and
   it explicitly does not cover Scope 9-11's provider-gating question, so it complements rather than
   replaces this task's own steps.
6. **MCP** (Scope 12-13); run the `mcp-node-schema-sync` and `mcp-validation` skills.
7. **End to end on dev:** approve a real gateway model that is not yet in the dev catalog through the
   proposal flow, and confirm with no code change that it appears in the picker, runs, bills and is
   listed by MCP with its tools.

## Verification

- **Negative controls, each seen red before green:**
  - mapper: drop the `modalities.output` read → the Gemini image fixture loses `supportsImageOutput`;
  - sync: allow lowering → a human-set `true` fixture is flipped;
  - worker: remove the capability guard → the "not supported" test calls `streamText`; hardcode
    `toolChoice` again → the flag-false test fails;
  - worker native OpenAI: always use `gpt-image-1` → the approved-new-model test fails; always use
    `aiModel` → the `dall-e-3` test fails;
  - front: reintroduce a literal model array → the "model from technologies appears" test fails;
  - MCP: drop `tools` from the projection → the handler spec fails.
  - OpenAI probe: assert the ineligible fixture (`gpt-3.5-turbo`) returns `usage: None` on rejection
    (live-verified 2026-09-25, `scripts/a5b-image-capability/probe-openai-image-tool.py`) — a live
    contract test, not mocked, since this is the fact the whole probe design leans on.
- **Fixtures from reality:** the mapper tests use entries copied from the captured gateway response,
  not invented shapes.
- **Measure before refusing** (PLAN §3.3.2): the worker guard, the picker filter and D-A5B-5 are each
  checked against the stored-node counts; nothing that runs today stops running unless named here.
- **Billing:** a newly approved model with no `model_price` row is refused before generation once the
  charge-hardening task lands; until then this is recorded as a known dependency, not tested around.
- **End to end:** Step 7, on dev.

## Deployed to dev (2026-09-25)

All three repos merged to their dev branches and validated — back `master` (`76f5bf0d`), worker
`develop` (`e48caf3`), front `main` (`1420c6ef`).

- **Back → `master`:** clean merge apart from one duplicate-column collision
  (`system_ai_models.entity.ts` — an unrelated master commit had independently added
  `supportsImageGenerationTool`; resolved by keeping the single column). Scoped Jest (`ai-model-sync`,
  `gateway-model-mapper`, `openai-image-tool-eligibility`, `system-ai-model-tools`,
  `system-ai-model-upsert-fields`, `responseModelPrice`, `mcp-write.service`, `responseCompanyTech`):
  259/259 passed. `tsc --noEmit`: two pre-existing errors on unrelated master commits
  (`execution_logs.retention.spec.ts`, `feature-flags.service.spec.ts`), confirmed via
  `git log -- <file>` before the merge, zero errors in any A5b-touched file.
- **Worker → `develop`:** a genuine feature-duplication merge, not a mechanical one. `develop` already
  carried an independent implementation of the OpenAI multimodal-image path (via the
  `feat/868m0vkt4-dev` → `develop` route investigated earlier in this task) with `AbortSignal`
  cancellation threaded through `generateOpenAiMultimodalImage`/`buildGeminiSpec`/
  `fetchSourceImageBuffer`, which this task's cherry-picked chain (from `868ky2g5f`) lacked; this
  task's chain in turn added the token-usage billing (`ImageTokenUsage`, `inputTokens`/`outputTokens`)
  that `develop`'s route lacked. Reconciled by keeping both: the merged
  `generateOpenAiMultimodalImage` takes `abortSignal` **and** iterates the full stream to read
  `result.usage`; `ImageProviderService` keeps `generateMultimodalText()` (develop's delegation point)
  **and** `tokenUsage` on the ai-sdk result variant. 14 files touched by the conflict. `tsc --noEmit`
  clean on every touched file (two pre-existing unrelated errors on `report-builder`/`activities`
  specs, confirmed via `git log` as `develop`-origin). Scoped Jest (`image-generator`,
  `ai-provider/image`): 220/222 passed (2 pre-existing skips).
- **Front → `main`:** an analogous small collision in `OpenAiImg.tsx`/`SettingsModal.tsx` — `main`
  independently added the `multimodalModels` dropdown (from the same `868ky2g5f` feature) while this
  task added capability-filtered `models`/`withStoredModelFallback`. Merged both: `OpenAiImg` now takes
  both `models` and `multimodalModels` props, selects from either. `pnpm-lock.yaml` conflict resolved
  by regenerating (`git checkout --theirs` + `pnpm install`) rather than hand-merging. Production build
  (`vite build`) succeeded; `OpenAiImg.test.tsx` (merged, both test suites kept): 6/6 passed.
- **End to end on dev (MCP, live):** `list_ai_models` returns the real, live capability flags —
  `gpt-5-nano`/`gpt-5.5` → `supportsImageGenerationTool: true`; `gemini-2.5-flash-image` →
  `supportsImageOutput: true` with `"image_output"` in `tools`; every non-image-capable model (Claude,
  Gemini text, Stability, Ideogram, Fal, audio models) → both `false`. `get_node_type("imageGenerator")`
  resolves unchanged post-merge. This is Step 7's verification, run directly against dev rather than
  through a fresh proposal-flow approval (no new gateway model was available to approve at merge time);
  the capability signal it validates is the same one Step 7 describes.

## Done when

A model the gateway advertises as image-capable, approved through the existing proposal flow, is
offered in the Image Generator picker, executed by the worker with the right call, and listed by the
app and by MCP with its capabilities and `tools` — with no code change. OpenAI tool-capable models
reach the same state once the approving admin confirms the pre-filled flag. `toolChoice` is derived
from the stored capability, never assumed. Every stored node measured above either behaves as before
or is named in this file with the reason.

## Impact on image-studio

Image-studio is not yet scoped or dated (2026-09-25). This is what it inherits from A5b and should not
redo, and what it still owns:

- **Inherits, should not redo:** the capability signal (`supportsImageOutput`,
  `supportsImageGenerationTool`) and the derived `tools` list (D-A5B-4) — read from `system_ai_models`
  via `TechnologiesDto`/`CompanyTechnologiesDto`/MCP, already correct for every model in the catalog. If
  image-studio re-derives "can this model generate images" on its own, it repeats the exact per-layer
  duplication A5b was created to close.
- **Inherits, should not redo:** the OpenAI eligibility source — the named rule module plus the
  once-per-model probe (D-A5B-1) — and the raise-only sync rule (D-A5B-2), so a human-approved capability
  is never silently reverted.
- **Still image-studio's own job:** the actual call to each provider (worker `ai-provider/image/`
  layer, native and multimodal), and any new UI for a unified picker/settings surface. A5b wires the
  *existing* picker and the *existing* worker paths to the capability signal — a picker/worker
  consolidation is a bigger, separate change and free to replace that wiring later, as long as it keeps
  reading the same capability fields instead of inventing a second source.
- **Sequencing:** none of A5b's five back-layer scope items (mapper, sync, migration, `tools`
  projection, MCP fields) are touched by image-studio's absence — they ship now regardless. The
  front/worker items (Scope 7, 9-11) are the parts most likely to be touched again once image-studio is
  scoped; shipping them now still fixes a real production defect (an approved image-capable model, or a
  multimodal model without the tool, silently doing the wrong thing) rather than waiting on an unscoped
  future task.

## Files

`back/src/shared/ai-model-gateway/gateway-model-mapper.ts`, `gateway-model.types.ts` ·
`back/src/app-api/system_ai_models/ai-model-sync.service.ts`, `ai-model-proposal.service.ts` ·
`back/src/entities/system_ai_models.entity.ts` + a generated migration ·
`back/src/shared/system-ai-model-upsert-fields.ts` (the PATCH allowlist — 868m3pkyu's admin-wiring skill) ·
`back/src/app-api/model_price/dto/responseModelPrice.dto.ts` (`ResponseSystemAiModelDto`'s `@Expose()` — 868m3pkyu's PR #1954 gap, must not repeat) ·
`back/src/technologies/responseTechnologies.dto.ts` · `back/src/app-api/company/dto/responseCompanyTech.dto.ts` ·
`back/src/app-mcp/mcp-resources.service.ts` · `back/src/app-mcp/mcp-write.service.ts` ·
`back/src/app-mcp/node-types/node-type-metadata.ts` ·
`front/src/components/ImageGenerator/constants.ts`, `SettingsModal/SettingsModal.tsx`, `OpenAiImg.tsx` ·
`front/src/views/AdminDashboard/AiModelsManagementPage.tsx` · `front/src/features/admin-panel/pages/ai-models/` ·
`worker/src/modules/ai-provider/image/openai-multimodal-provider.ts`, `openai-provider.ts`,
`image-provider.types.ts`, `image-provider.service.ts` ·
`worker/src/modules/nodes/image-generator/image-generator.service.ts` ·
`mcp-server/src/upstream/back-http-client.service.ts`, `src/tools/handlers/list-ai-models.handler.ts` ·
`scripts/a5b-image-capability/measure-gateway-image-capability.py`,
`scripts/a5b-image-capability/probe-openai-image-tool.py`
