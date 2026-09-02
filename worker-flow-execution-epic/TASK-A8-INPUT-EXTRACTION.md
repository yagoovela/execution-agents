# A8 — Move input extraction and OCR off the request path

**Goal:** the link extraction, file upload and OCR that `varInputNode` performs at the start of
every run stop blocking the backend.

**Depends on:** A1. **Source:** analysis §11.1 — this task exists because the census was wrong.

## Why this was missed, and why it matters

The census classified `varInputNode` as inert: its front component only calls the backend at
configuration time. That is true of the component and false of the run.

During a run, **before the loop**, the engine iterates every `varInputNode`
(`back/src/app-api/flux/flux.service.ts`) and does real external I/O:
`extractionService.extractTextFromLink` per link and `awsService.uploadFile` per file, with an OCR mode chosen per input (`typeOCR`).

It is invisible to every dispatch gate because it is resolved *before* `nextReady` ever runs — so
it is not in `isTemporalNode`, not in the prefetch whitelist, and not in the census. It is
nonetheless synchronous, external, and on the critical path of every run that has one.

## Scope

**In.** An extraction activity in the worker, so the backend is free while OCR runs. The step
documentation's own observation: OCR *"é síncrono e cega o backend"*, and a dedicated activity is
a large win for agents with several files.

**In.** Three improvements the same source flags, each cheap while the code is open:
- **Extraction cache** keyed by URL or file hash. Sub-flows re-extract the same file today — pure
  rework.
- **Batch the writes.** `persistInputNodeData` runs one `UPDATE` per input, sequentially.
- **Telemetry.** Nothing is logged today about OCR duration, file size or provider, which makes
  Phase-1 latency undiagnosable. Add it before changing the shape, so the change can be measured.

**Out.** Renaming `extractText` — the field holds URLs when `isExtraction` is false, which is
confusing, but renaming a persisted field is its own migration.

**Out.** An OCR *node*. `imageReaderNode` is deprecated (D24) and an OCR node is wanted in its place,
but it is not built in this epic and not here: this task moves the OCR that `varInputNode` already
does off the request path; it does not add a node type.

## Egress policy — decided here, not later

Several of these nodes fetch user-controlled URLs, and this task moves them into the worker, which
holds the database password and the integrations key. Whether that improves or worsens the exposure
depends on the worker's network position, and there is no SSRF protection today (review §3.2).

`TASK-S6` owns the policy. This task does not ship a relocated fetcher until S6's decision exists
and applies to it — the point of S6 is that the decision is made **with** the move, because the
move is what changes the risk.

## Verification

- **Negative control (required).** Break the extraction call and confirm a test fails on the
  resolved input being empty, rather than the run continuing with a blank variable. Today a failed
  extraction can leave a placeholder resolving to nothing, which reads downstream as a bad prompt
  rather than a failed upload — that is the failure this test must pin.
- Parity on real inputs: same link and same file, backend vs worker, byte-identical extracted text.
- Latency measured before and after, per input type. This task's whole justification is that the
  backend stops blocking; state the number.
- Cache correctness: the same file in two nodes extracts once; a changed file does not serve a
  stale extraction.

## Done when

Extraction and OCR run as an activity, parity is proven, the backend no longer blocks on them, and
the before/after latency is recorded.

## Files

`back/src/app-api/flux/flux.service.ts` (the pre-loop `varInputNode` resolution: `extractTextFromLink`, `uploadFile`, `typeOCR`) · `back/src/app-api/extraction/` ·
`back/src/app-api/google_ocr/` · `back/src/app-api/aws/` · new worker module · the A1 registry
