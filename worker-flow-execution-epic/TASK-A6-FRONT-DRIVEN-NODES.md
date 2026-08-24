# A6 — Give the nine front-driven types server-side execution

**Goal:** the nine node types that today run only from the browser get an activity and, for the
first time, engine dispatch.

**Depends on:** A1. **Blocked on:** decision **D3**. **Ship in three stages** — they are one task
because they share the same three-part scope, not because they are one deploy.

## Why this is not an ordinary migration

These nodes are **front-driven**: the component calls a backend endpoint directly, bypassing the
flow engine (analysis §4.1). They produce output only when a user clicks Run in the builder. In an
API, cron, chatbot, form or MCP run, the engine never dispatches them, so the flow uses whatever
the last manual run left behind — or nothing.

So the scope is not "move code from the back" — nothing executes in the back today. It is three
things, and the second does not exist for any other task in this epic:

1. Implement the activity (the normal registration chain).
2. **Make the engine dispatch the type for the first time**, including declaring its dependency
   edges to the scheduler so it runs in the right order.
3. Decide what the front's Run button does afterwards: route it through
   `ProcessService.response` (`POST /process/single-node`) like every migrated node, and delete
   the direct provider call. **Keeping both paths is exactly how the four lists diverged.**

**This changes behaviour for existing customers.** A scheduled flow containing one of these nodes
starts producing fresh output where it produced stale output before. That is almost certainly the
fix — but it is a product decision (D3), not a refactor, and it must be answered before stage 1.

## Stages

**Stage 1 — the three that are almost free.** No provider work at all; the clients are already in
the worker.

| Type | Why it is free |
|---|---|
| `webTrends` | the SerpApi client is already in the worker, inside `web-search` |
| `webAmazon` | the Scraper client is already in the worker, inside `web-crawling` |
| `fileSave` | `GoogleDriveService.uploadFile` and `TokenProviderService` already exist in the worker |

`fileSave` is the most valuable of the three and the worst offender: it is listed in
`SIDE_EFFECT_TYPES` (`flux/scheduler.ts:29–36`), so the scheduler protects it from being pruned —
yet nothing executes it server-side. Its `uploadToDrive()` runs in the browser against a
`localStorage` OAuth token, so it **cannot** run headless even in principle. The server-side token
already exists (`user.googleRefreshToken`) and the engine already refreshes it — but only when the
flow has `pullData`/`pushData` with `provider = google` (`flux.service.ts:2621–2641`). Extend that
condition; do not build a second refresh path.

**Stage 2 — port a small client.** `secApiNode` (`app-api/sec`), `usCensusNode`
(`app-api/census_data`), `documentSummarizer` (`app-api/summarize`). No credentials beyond an env
key, except `documentSummarizer`, which is LLM-backed and therefore uses the existing billing and
model-access callbacks.

**Stage 3 — asset providers.** `commandMusicNode` (Replicate) and `animationNode` (Luma + Runway).
Both produce assets, so both use `/worker/generate-file`; both are long-running, so both need
their `startToCloseTimeout` and `heartbeatTimeout` chosen deliberately rather than inherited.

(`imageReaderNode` is the ninth and is migrated in A5, over the shared image provider layer.)

## Egress policy — decided here, not later

Several of these nodes fetch user-controlled URLs, and this task moves them into the worker, which
holds the database password and the integrations key. Whether that improves or worsens the exposure
depends on the worker's network position, and there is no SSRF protection today (review §3.2).

`TASK-S6` owns the policy. This task does not ship a relocated fetcher until S6's decision exists
and applies to it — the point of S6 is that the decision is made **with** the move, because the
move is what changes the risk.

## Verification

- **Negative control (required), per stage.** Remove the engine dispatch for one type and confirm
  a test fails proving the node did **not** run in a headless flow. That is precisely today's
  production behaviour, so this is the one test in the epic that reproduces the defect being
  fixed — write it first, watch it pass against `main`, then make it fail.
- **Headless parity.** For each type: run the same flow via the builder Run button and via an API
  trigger, and assert both produce output. Today only the first does.
- **`fileSave` specifically:** prove a scheduled run uploads to Drive with the server-side token,
  with no browser involved.
- **No double execution** once the front's Run button is rerouted: the direct provider call must
  be gone, not merely unused.

## Done when

All nine satisfy PLAN §3.4; a headless run produces output for each; no front component calls a
provider service directly for execution.

## Files

`front/src/components/nodes/{WebTrends,WebAmazon,SecApiNode,UsCensusNode,AiTextSummarizer,AiMusicGenerator,AiVideoGenerator}.tsx` ·
`front/src/components/FileSave/FileSave.tsx` · `back/src/app-api/{sec,census_data,summarize,scraper,serpApi,repiclate,luma_labs,runwayML}/` ·
`back/src/app-api/flux/flux.service.ts:2621–2641` · `back/src/app-api/flux/scheduler.ts` · new worker modules · the A1 registry
