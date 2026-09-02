# A5 — Migrate `imageGenerator` over a shareable image provider layer

**Goal:** migrate `imageGenerator` into the worker, over a provider layer written so the next image
node can share it.

**Depends on:** A1, and A4 having validated the template.

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

## Why

`imageGenerator` is architecturally identical to `commandTextNode`, which has been in the worker
in production the longest (analysis §3.2). Every contract it needs already exists:
`/worker/charge-tokens`, `/worker/validate-model-access`, `/worker/generate-file`. Its cost is
**breadth** — six provider paths: `openAiService.createImageWithBilling`,
`geminiService.generateImage`, `replicateService.kandinsky`, and `imageService.{imageCore,sd,textToImage}`.

## Scope

**In.** A `worker/src/modules/ai-provider/image/` layer the node consumes, then the node module on
top of it. One entry per provider path; nothing node-specific inside the layer.

**In.** Prompt resolution across `imageGenerator`'s seven prompt fields (`prompt`, `subject`,
`environment`, `tone`, `view`, `style`, `negativePrompt`) with placeholder interpolation against
the resolved run schema — the same pattern every migrated node with variable inputs already uses.

**Out.** New providers, new models, changes to the prompt fields, or the billing formula.

**Out.** `imageReaderNode` (D24), and the OCR node that will replace it.

## Steps

1. Provider layer with one entry per path, ported from the back's services. Behaviour port only —
   no redesign of provider selection.
2. `imageGenerator` module; registry entry behind the flag; prove; flip; delete the twin
   (`imageGeneratorNode()` and its dispatch case).
3. Timeouts set deliberately per provider in `workflows/configs.ts`; image generation is slow
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
- **One layer, not a copy.** Confirm the module carries no provider call of its own — every path
  goes through `ai-provider/image/`. The layer is the part of this task the next image node
  inherits; if it ends up bypassed, that part did not happen.

## Done when

`imageGenerator` satisfies PLAN §3.4, its module consumes the shared provider layer and carries no
provider call of its own, billing matches the inline path on real runs, timeouts were chosen per
provider, and `imageGeneratorNode()` and its dispatch case are deleted.

## Files

new `worker/src/modules/ai-provider/image/**` · `worker/src/modules/nodes/image-generator/` (in progress on the dev line) ·
`worker/src/modules/temporal/workflows/configs.ts` · `back/src/app-api/flux/flux.service.ts` (`imageGeneratorNode()` + its dispatch case) ·
the A1 registry
