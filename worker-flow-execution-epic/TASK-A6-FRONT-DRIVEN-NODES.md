# A6 — Give the front-driven types server-side execution

**Goal:** the front-driven node types that today run only from the browser get an activity and, for
the first time, engine dispatch. Eight after D24 (the census counted nine); **six after D3**, which
discontinues `documentSummarizer` and `commandMusicNode`.

**Depends on:** A1. **D3 answered on 2026-09-02** (PLAN §7) — the wave's product sign-off exists.
**One card, one PR per stage** (PLAN §3.1) —
they are one task because they share the same three-part scope, not because they are one deploy;
each stage is independently deployable behind the flag.

**D3, as answered on 2026-09-02.** `documentSummarizer` and `commandMusicNode` are discontinued and
leave this task. `webAmazon` and `secApiNode` are broken today: giving them execution includes making
them work, or dropping them — decide per type in its stage and record the decision here. `fileSave`
is under review and stays in scope until that review says otherwise. The stages below are re-cut
accordingly: six types.

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
starts producing fresh output where it produced stale output before. That is the fix — and it is a
product decision (D3), answered on 2026-09-02, not a refactor.

## Stages

**Stage 1 — the three that are almost free.** No provider work at all; the clients are already in
the worker.

| Type | Why it is free |
|---|---|
| `webTrends` | the SerpApi client is already in the worker, inside `web-search` |
| `webAmazon` | the Scraper client is already in the worker, inside `web-crawling` — **broken today** (D3): fix it as part of giving it execution, or drop it, and record which |
| `fileSave` | `GoogleDriveService.uploadFile` and `TokenProviderService` already exist in the worker |

`fileSave` is the most valuable of the three and the worst offender: it is listed in
`SIDE_EFFECT_TYPES` (`flux/scheduler.ts`), so the scheduler protects it from being pruned —
yet nothing executes it server-side. Its `uploadToDrive()` runs in the browser against a
`localStorage` OAuth token, so it **cannot** run headless even in principle. The server-side token
already exists (`user.googleRefreshToken`) and the engine already refreshes it — but only when the
flow has `pullData`/`pushData` with `provider = google` (`flux.service.ts`). Extend that
condition; do not build a second refresh path.

**Stage 2 — port a small client.** `secApiNode` (`app-api/sec`; **broken today**, D3 — fix or drop,
and record which) and `usCensusNode` (`app-api/census_data`). No credentials beyond an env key.
`documentSummarizer` (`app-api/summarize`) was here; it is **discontinued (D3)** and leaves the task.

**Stage 3 — asset provider.** `animationNode` (Luma + Runway). It produces an asset, so it uses
`/worker/generate-file`; it is long-running, so its `startToCloseTimeout` and `heartbeatTimeout` are
chosen deliberately rather than inherited. `commandMusicNode` (Replicate) was here; it is
**discontinued (D3)** and leaves the task.

(`imageReaderNode` was the ninth of the census. It is **deprecated (D24)** and leaves the migration;
an OCR node is wanted later and will be specified when it is built, not here.)

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

All six that remain after D3 satisfy PLAN §3.4; a headless run produces output for each; no front
component calls a provider service directly for execution; `documentSummarizer` and
`commandMusicNode` are recorded as discontinued in the A1 registry, not left as front-driven; and
the fix-or-drop call for `webAmazon` and `secApiNode` is written in this file.

## Files

`front/src/components/nodes/{WebTrends,WebAmazon,SecApiNode,UsCensusNode,AiVideoGenerator}.tsx` ·
`front/src/components/FileSave/FileSave.tsx` · `back/src/app-api/{sec,census_data,scraper,serpApi,luma_labs,runwayML}/` ·
`back/src/app-api/flux/flux.service.ts` (the Google refresh-token condition on `pullData`/`pushData`) · `back/src/app-api/flux/scheduler.ts` (`SIDE_EFFECT_TYPES`) · new worker modules · the A1 registry
