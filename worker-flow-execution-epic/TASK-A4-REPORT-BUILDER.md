# A4 — Migrate `reportBuilder`

**Goal:** move the cheapest node in the catalogue into the worker, and use it to re-validate the
activity template end to end after the seven-module promotion.

**Depends on:** A1. Best done immediately after A2, while the template is fresh.

## Why

`reportBuilder` is pure compute plus one upload (analysis §3.1): it sorts `data.variables` by
`(y, x)`, escapes HTML, composes the document, and calls `uploadService.uploadText`. No billing,
no model access, no mutable engine state. Handler at `flux.service.ts:9177`, dispatched at `:1343`.

It is the only remaining node where a migration exercises the whole pipeline — registration,
dispatch, persistence, notification — **without** a provider surface or a new contract obscuring a
failure. That makes it the right canary, not merely the easiest win.

## Scope

**In.** The worker module, the registry entry, the flag, the flip, the twin deletion.

**In.** Decide the upload path: `uploadService.uploadText` has no worker equivalent, but
`/worker/generate-file` already exists and is the established contract. Prefer the callback over a
second S3 client in the worker — the worker deliberately has no S3 client, which is why the
claim-check goes through the API.

**Out.** Changing the report format. Byte-identical output is the acceptance criterion.

## Steps

1. Worker module following `sql-querier`'s shape: a thin `process(props)` that fetches the row,
   validates, composes, calls the file callback, `persistNodeSuccess`, returns the DTO.
2. Registry entry behind the flag.
3. Prove byte-identical output against the inline handler on real stored `reportBuilder` nodes.
4. Flip; delete the twin at `flux.service.ts:9177` and the dispatch at `:1343`.

## Verification

- **Negative control (required).** Remove the `y`-then-`x` sort from the worker implementation and
  confirm a test fails on variable ordering. Layout order is the node's whole behaviour; a test
  suite that passes without it is testing nothing.
- **Byte-identical output.** Run both implementations over every distinct `reportBuilder`
  configuration in the dev database and diff the produced text. Any difference is a defect in this
  task, not an improvement.
- Empty `variables` returns early in the inline version — confirm the worker matches, rather than
  producing an empty document.

## Done when

`reportBuilder` satisfies PLAN §3.4, output is proven identical, and the inline handler is deleted.

## Files

new `worker/src/modules/nodes/report-builder/` · `worker/src/modules/nodes/nodes.types.ts` ·
`worker/src/modules/temporal/**` · `back/src/app-api/flux/flux.service.ts:1343, 9177` · the A1 registry
