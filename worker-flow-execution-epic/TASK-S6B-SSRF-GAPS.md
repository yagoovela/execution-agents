# S6b — Close the SSRF gaps the S6 check found

**Goal:** no FluxPrompt endpoint or node reaches an internal address through a URL a user
supplies, whatever that URL's name resolves to.

**Depends on:** nothing. It can ship at any point in Wave 5, and the `/proxy` part should ship
first. **Added 2026-10-26** from the code check of decision S6-a (`TASK-S6-SSRF-POLICY.md`).
ClickUp: [868mn5gb5](https://app.clickup.com/t/868mn5gb5).

## Why

S6 shipped an egress policy, and A9 shipped a second, stricter one. The check of 2026-10-23,
repeated on 2026-10-26 against back `main` `10e64b20` and worker `main` `abf3b09d`, found four
places where a user-supplied URL still leaves the platform unchecked or checked in a way that does
not hold:

| # | Where | What happens today |
|---|---|---|
| 1 | Back `/proxy` (`src/main.ts`, `createProxyMiddleware`) | An Express middleware registered before any Nest guard forwards the request to the origin named in the `url` query parameter. No authentication, no host allowlist, no address check. The front loads images through it (`ExpandImageModal.tsx`, `MaskImageEditModal.tsx`). |
| 2 | Worker `safe-fetch` (`safe-dispatcher.ts`) | Resolves the host, lets it through as soon as **one** resolved address is allowed, then calls the default connector **by hostname**. The name is resolved again, so the address that was checked is not necessarily the one used. |
| 3 | Two deny-lists | `safe-fetch` (`egress-policy.service.ts`) has 10 ranges. The A9 `egress` module (`egress-policy.ts`) has 17, checks every address, pins it through a `lookup` hook and re-checks each redirect hop. |
| 4 | Back `POST /api_call` (`api_call.service.ts`) | Sends an authenticated user's request with plain axios and no egress check. `DownloaderService.downloadFile` (`downloader.service.ts`) also fetches with plain axios, and no caller was found. |

Row 1 is the most exposed: it needs no account.

## Scope

**In — `/proxy`.**

1. Require authentication, the same as the Nest routes the front already calls.
2. Forward only to an allowlist of our own asset hosts (CloudFront, the S3 buckets the image nodes
   write to). Read the list from configuration, not from the request.
3. Keep the two front modals working. If an image from an outside host is needed, decide it in the
   PR and state it.

**In — one guard.** `safe-fetch` uses the A9 `egress` module: every resolved address is checked,
the checked address is pinned, and each redirect hop is checked again. Keep `safe-fetch`'s
current choice to refuse redirects unless the PR states a reason to follow them. One deny-list
remains: the 17 ranges of `egress`.

**In — the back.** `POST /api_call` goes through the same check. Delete `downloadFile` if it still
has no caller; guard it if one is found.

**In — the sweep.** List every outbound fetch of a user-supplied URL in back and worker, and record
the result here. The plain `fetch(url)` calls in `audio-transcriber.service.ts`,
`google-docai-base.ts` and `push-data.service.ts` are the first to check: confirm whether their URL
can come from a user.

**Out.** A per-organisation allowlist (S6-a's option A). It stays a later decision.

## Verification

- **Negative control (required).** A test host that resolves to one public and one denied address
  passes `safe-fetch` on `main` today. After the change it is refused. Then remove the pinning and
  watch the test fail.
- `/proxy` without a token answers 401. With a token and a host outside the allowlist it answers
  403. With an asset host it returns the image.
- `POST /api_call` to a denied address is refused with a user-facing message.
- Run every test locally. Never probe a production endpoint to prove a gap.
- Measure before refusing (PLAN §3.3.2): before the allowlist ships, count which hosts `/proxy`
  serves today from the access logs, so a real image host is not refused.

## Done when

`/proxy` is authenticated and allowlisted, every outbound fetch of a user-supplied URL goes through
one guard that pins the checked address, one deny-list remains, and the sweep is recorded here.

## Files

`back/src/main.ts` (`/proxy`) · `back/src/app-api/api_call/api_call.service.ts` ·
`back/src/app-api/downloader/downloader.service.ts` ·
`worker/src/modules/safe-fetch/safe-dispatcher.ts` ·
`worker/src/modules/safe-fetch/egress-policy.service.ts` ·
`worker/src/modules/egress/egress-policy.ts` ·
`front/src/components/ExpandImageModal/ExpandImageModal.tsx` ·
`front/src/components/MaskImageEditModal/MaskImageEditModal.tsx`

## Sweep (recorded 2026-10-29)

Every outbound fetch of a user-supplied URL in `back` and `worker`:

**Back (3):**
- `back/src/main.ts` `/proxy` (was: Express middleware, no auth, no allowlist, silent `api-dev.fluxprompt.ai` fallback) → rewritten as `src/app-api/proxy/` NestJS module with `JwtAuthGuard` + `PROXY_ALLOWED_HOSTS` allowlist + `egressHttpConfig` (pin + redirect guard, defence in depth).
- `back/src/app-api/api_call/api_call.service.ts` `executeApiCall` (was: plain axios) → guarded by `assertEgressAllowed` + `egressHttpConfig`, `maxRedirects: 0`, controller catches `isEgressRefusal(err)` and surfaces "This URL points to an address that is not allowed." via WS.
- `back/src/app-api/downloader/downloader.service.ts` `downloadFile` → **deleted** (grep confirmed no callers; `DownloaderController` only uses `AwsService.getFile`).

**Worker (5):**
- `worker/src/modules/nodes/audio-transcriber/audio-transcriber.service.ts:156` `downloadAudio` → `SafeFetchService.getBuffer`.
- `worker/src/modules/nodes/audio-transcriber/google-speech.ts:50` → `SafeFetchService.getBuffer`.
- `worker/src/modules/nodes/image-reader/providers/google-docai-base.ts:45` `downloadDocument` → `SafeFetchService.getBuffer`; both `GoogleDocAiFormProvider` and `GoogleDocAiOcrProvider` now inject `SafeFetchService` and thread it through `processWithDocAi`.
- `worker/src/modules/nodes/push-data/push-data.service.ts:438` `uploadMicrosoftRawFiles` → `SafeFetchService.getBuffer`.
- `worker/src/modules/nodes/text-generator/multimodal-file-processor.ts` `detectMimeFromHead` / `downloadFile` → `SafeFetchService.head` / `SafeFetchService.getBuffer`. `fetchWithTimeout`, `USER_AGENT`, `HEAD_TIMEOUT_MS`, `DOWNLOAD_TIMEOUT_MS` removed; timeout now owned by SafeFetchService.

**Deny-list consolidation:**
- `worker/src/modules/safe-fetch/egress-policy.service.ts` (10 ranges) → **deleted** along with its spec.
- `worker/src/modules/egress/egress-policy.ts` (17 ranges) → sole source. Byte-identical port at `back/src/common/egress/egress-policy.ts` (error types swapped: `UserConfigError`/`IntegrationError` → `BadRequestException`/`InternalServerErrorException`). Drift tested in both repos via `test/egress-policy-drift.spec.ts` with the same canonical constant block.

**Safe-fetch rewrite (worker):**
- `safe-dispatcher.ts` and `safe-axios.ts` now use `createSafeLookup` + `createRedirectGuard` from the A9 egress module. The TOCTOU gap (one address allowed → re-resolve by hostname at connect time) is closed by routing the connection through the pinning lookup; `SafeFetchService` public surface is preserved (`get`, `getBuffer`, `post`, `createAxios`, `getDispatcher`) and gains `head()`.

**Negative control (safe-fetch.service.spec.ts):**
- A test host that resolves to one public + one 127.0.0.1 is now refused. Removing the `createSafeLookup` hook makes the test fail.

No other outbound fetch of a user-supplied URL remained unguarded as of this change.
