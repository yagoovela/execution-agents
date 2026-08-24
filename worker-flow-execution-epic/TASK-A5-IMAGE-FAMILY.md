# A5 — Migrate the image family: `imageGenerator` + `imageReaderNode`

**Goal:** migrate both image nodes over one shared provider layer in the worker.

**Depends on:** A1, and A4 having validated the template. **Blocked on:** D3 for the
`imageReaderNode` half (see A6 — it is one of the nine front-driven types).

## Why

`imageGenerator` is architecturally identical to `commandTextNode`, which has been in the worker
in production the longest (analysis §3.2). Every contract it needs already exists:
`/worker/charge-tokens`, `/worker/validate-model-access`, `/worker/generate-file`. Its cost is
**breadth** — six provider paths: `openAiService.createImageWithBilling`,
`geminiService.generateImage`, `replicateService.kandinsky`, and `imageService.{imageCore,sd,textToImage}`.

`imageReaderNode` overlaps heavily: OpenAI, Anthropic, Replicate, Ideogram, plus file and upload.
Migrating them separately means writing the provider layer twice and letting the two copies drift.
They are one task for that reason, not because they are similar in purpose.

## Scope

**In.** A `worker/src/modules/ai-provider/image/` layer both nodes consume, then the two node
modules on top of it.

**In.** Prompt resolution across `imageGenerator`'s seven prompt fields (`prompt`, `subject`,
`environment`, `tone`, `view`, `style`, `negativePrompt`) with placeholder interpolation against
the resolved run schema — the same pattern every migrated node with variable inputs already uses.

**Out.** New providers, new models, changes to the prompt fields, or the billing formula.

## Steps

1. Provider layer with one entry per path, ported from the back's services. Behaviour port only —
   no redesign of provider selection.
2. `imageGenerator` module; registry entry behind the flag; prove; flip; delete the twin (`:6972`,
   dispatch `:1145`).
3. `imageReaderNode` module on the same layer. This one **adds** execution rather than moving it
   (§4.3) — it needs an engine dispatch that does not exist today, and D3 must be answered first.
4. Timeouts set deliberately per provider in `workflows/configs.ts`; image generation is slow
   enough that the default `startToCloseTimeout` is a guess, not a decision.

## Verification

- **Negative control (required).** For each provider path, break the selection so it falls through
  to the wrong provider, and confirm a test catches it. Six paths means six ways to silently call
  the wrong API; a suite that only exercises the default path is not protection.
- Billing parity: for the same prompt and model, `token_transactions` rows written by the worker
  must match what the inline path wrote. Compare against real stored runs.
- Model-access refusal: a model the user is not entitled to must produce the same refusal through
  `/worker/validate-model-access` as it does inline. **Measure before refusing** (PLAN §3.3.2) —
  run the check against real entitlements and drive false refusals to zero.

## Done when

Both types satisfy PLAN §3.4, share one provider layer, billing matches, and both inline handlers
are deleted.

## Files

new `worker/src/modules/ai-provider/image/**` · new `worker/src/modules/nodes/{image-generator,image-reader}/` ·
`back/src/app-api/flux/flux.service.ts:1145, 6972` · `front/src/components/nodes/ImageReader.tsx` (Run path) ·
the A1 registry
