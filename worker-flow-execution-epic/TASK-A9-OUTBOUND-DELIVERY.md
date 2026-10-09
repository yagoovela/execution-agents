# A9 — Outbound delivery as activities

**Goal:** the emails and HTTP callbacks a run sends stop being fire-and-forget, and start being
retried.

**Depends on:** A1 (shipped, PR #1986). Can ship any time after it. **Source:** review §11.1.
**ClickUp:** [868m0vmux](https://app.clickup.com/t/9011479430/868m0vmux).

> **Corrected 2026-09-29 at task start.** Re-validated against `back@origin/production` `94cb2e26`
> (identical delivery block on `origin/master` `bdf0b555`, shifted +18 lines) and
> `worker@origin/main` `ceff351`. Seven premises of the 2026-09-02 text were wrong, and two of them
> would have made the task fail as written. Each is corrected in place below and listed here so a
> reader can tell a considered change from a typo:
>
> 1. **"Idempotency exists, so retry is safe" — false.** The dedup keys are claimed *before* the
>    send and never released on failure (no `DEL` anywhere). Ported unchanged into a retrying
>    activity, every retry of a failed send would be silently suppressed for 24 hours. The keys keep
>    their names, format and TTLs; their protocol changes (D-A9-6).
> 2. **Callbacks have no keys of their own** — neither the node callback nor the api-v2
>    consolidated one. Only email has keys. *Refined during implementation:* the node callback
>    sits after the email in the same node, and every early return of the email branch (no
>    recipients, either key suppressing, a Gmail/Microsoft throw) also skips that node's callback,
>    so on the 19 prod nodes with both (Q1) a suppressed email already withholds the callback. That
>    coupling is preserved (D-A9-3).
> 3. **Not everything is fire-and-forget.** Only the node callback is log-and-drop. A Gmail or
>    Microsoft send failure rethrows and fails the whole run (and a parent run, through sub-flows);
>    an SMTP failure is swallowed inside `MailService.sendMail` and never seen.
> 4. **The consolidated callback is worse than fire-and-forget:** when it fails it overwrites a
>    `completed` execution status with `error` and posts a second, contradictory `success:false`
>    callback to the same endpoint.
> 5. **"Email parity across the three paths" would preserve defects.** The three paths already
>    disagree (Gmail sends to the first recipient only). Parity here means *each path matches its own
>    before*, not that the three match each other (D-A9-4).
> 6. **PLAN §3.4 is the definition of done for a node type**; delivery is not a node type. The
>    applicable points are named in *Done when*.
> 7. **"The run log" is `flows_logs`**, the flow's log table the customer sees — not
>    `space_run_logs`, which is an internal staff view that many runs never write (D-A9-7).
>
> The review's line numbers (`flux.service.ts:4907–5200`) are stale; the block is now `:5329–5599`.

## What is there today (verified)

All references are `back@origin/production` `94cb2e26` unless marked. `FS` = `src/app-api/flux/flux.service.ts`.

**Where.** Inside `apiV2` (`FS:2498–5812`), after the scheduler loop has finished (`FS:5090`), after
the flow log (`FS:5199`) and after the space run log flush (`FS:5275`). One `Promise.all` over every
`outputObjectNode` (`FS:5357–5599`); its result is discarded. `apiV2`'s return value
(`FS:5704–5720`) does not depend on delivery.

**Nothing in the same run waits on it.** `outputObjectNode` has `sourceHandles: []`
(`back/src/app-mcp/node-types/node-handle-registry.ts:832`) and is a `DATA_SINK_TYPES` member
(`flux/scheduler.ts:23`). Prod stores 4 edges leaving an output node, in 3 flows (Q7: targets
`apiCaller`, `counterNode`, `stickyNote`); they cannot wait on delivery either, because the scheduler
loop has finished (`FS:5090`) before the delivery block starts (`FS:5329`).

**Who does wait on it**, because it is awaited before `apiV2` returns:

| Caller | What waits |
|---|---|
| `/beta-v2` (`flux.controller.ts:591`), `/run-public-flow` (`:1618`), agents (`agents.service.ts:72,152`), legacy cron (`legacy-schedule-registrar.service.ts:60,130`) | the HTTP response |
| chatbot socket (`:1293`), formapi (`:1385`) | the final socket message |
| `/api-v2` via the Bull processor | the 30 s synchronous wait (`AGENT_WAIT_TIMEOUT_MS`), `flow_execution_status` → `completed`, and the consolidated callback |
| flow-caller (`FS:6034`) and library (`FS:6435`) sub-flows | the **parent's next node**; a child email failure also fails the parent run (`FS:6143`, `FS:6574`) |
| canvas (`/execute-from-canvas`) | nothing — `apiV2` is not awaited and node statuses are emitted before delivery |

**Outbound calls:**

| Call | Where | Today on failure |
|---|---|---|
| attachment `axios.get(url, arraybuffer)` | `FS:5424` — runs for every output node with URLs, **even with email off** | logged, email goes out without it; no timeout, no size cap |
| Gmail `mailService.sendGmailEmail` | `FS:5522` → `mail.service.ts:686–860` (`To:` is `to[0]` only, `:746`) | rethrows → run fails |
| Microsoft `microsoftMailService.sendMail` | `FS:5536` → `microsoft-mail.service.ts` | rethrows → run fails; a token failure **deletes the user's integration** (`microsoft-auth.service.ts:175–179`) |
| SMTP `mailService.sendMail` | `FS:5551` → `mail.service.ts:73–155` (nodemailer, `EMAIL_*`, transport built per send) | swallowed inside `sendMail` — invisible |
| node callback `axios.post(url, {text}, {timeout:10000})` | `FS:5581`; URL = `callbackUrlInputData[0].text \|\| callbackUrl \|\| webhookUrl` | logged as `webhook_error`, dropped |
| consolidated callback `httpService.post(webhookUrl, payload, {timeout: CALLBACK_TIMEOUT_MS})` | `src/jobs/apiV2Job/apiV2Job.processor.ts:176–191`; Bull `attempts: 1` (`apiV2Job.queue.ts:34`) | `markError` overwrites `completed`, then a second `success:false` post (`:194–236`) |

Every one of them follows redirects (axios' follow-redirects default, 21 hops) and none validates the
destination address. `validateCallbackUrl` (`flux.controller.ts:97–120`) checks only that the api-v2
`callback_url` parses as `http(s)`.

**Dedup keys** (email only, `REDIS_CLIENT` ioredis on the Bull Redis):

- `email-sent:${flowId}:${nodeId}:${runLogProcessId}` — `SET '1' EX 86400 NX` (`FS:5475–5482`).
- `email-content:${flowId}:${nodeId}:${sha256(sortedRecipients|subject|text)}` — `SET '1' EX 90 NX`
  (`FS:5500–5512`).
- Both are claimed before the send and never deleted. `runLogProcessId = execId ??
  injectedRunLogCollector?.processId ?? parentProcessId ?? uuid()` (`FS:2557`); sub-flows inherit
  the parent's, so the same child output node run twice in one parent run shares a key.
- Under ElastiCache `volatile-lru` both keys are the first to be evicted (see `TASK-E5`).

**Where a failure could be shown.** `flows_logs` (the flow's log table the customer sees) and
`space_run_logs` (the internal staff view) are both written *before* delivery;
`flow_execution_status` has no delivery field; there is no delivery socket event. Today a lost
callback or SMTP failure exists only in Winston/Datadog (D-A9-7).

**Worker today.** No mail code; `googleapis`, `google-auth-library` and
`@microsoft/microsoft-graph-client` are already dependencies. A token broker exists
(`back/src/temporal/worker.controller.ts:111` `POST /worker/refresh-oauth-token`,
`worker/src/modules/integrations/token/token-provider.service.ts`). `ioredis` is a dependency but
only used as a Nest transport. No egress/SSRF check in any repo except mcp-server's
`assertSafeUrl` (`src/oauth/oauth-client.service.ts:103–139`), which is weaker than what S6 asks for.
One task queue (`enhanced-ai-queue`), 10 activity slots
(`worker/src/modules/temporal/temporal.constants.ts:1`). `configs.ts` gives every activity
`maximumAttempts: 1`, with two per-activity precedents (`largeMemoryActivity`,
`chargeVoiceActivity`). Back starts workflows already, including a non-node one
(`completionWorkflow`, `router/router.service.ts:439`), and fire-and-forget starts exist
(`FS:996`).

**The token broker covers both OAuth senders, verified.** For Google it refreshes
`users.googleRefreshToken` with `GOOGLE_LOGIN_CLIENT_ID`/`GOOGLE_LOGIN_CLIENT_SECRECT`
(`worker.controller.ts:88–93`, `:125–133`) — the same token and client as `sendGmailEmail`
(`mail.service.ts:695–723`) and as the code that minted the token (`auth.controller.ts:907–949`).
The `gmail.send` scope is requested by the front's connect flow (`ConnectToGoogleSheets.tsx:7–8`),
so a broker token can send exactly when today's path can. For Microsoft it calls the same
`microsoftAuthService.getValidAccessToken` as `MicrosoftMailService.sendMail`, whose default scopes
include `Mail.Send` (`microsoft.types.ts:14–15`). No refresh token or OAuth client secret moves to
the worker for these two paths. (Read from `fix/868m9zfba`, the head of PR #2000 that
`origin/production` `94cb2e26` merged; line numbers match.)

## Decisions

### D-A9-1 — delivery runs after the run, asynchronously, with server-side retries

**Question.** Should `apiV2` wait for delivery, including every retry, before it returns?

**How the retry works when it is asynchronous.** `apiV2` starts a small delivery workflow and
returns. The workflow runs one activity per output node and channel. When an attempt fails with a
retryable error, the Temporal server records it and schedules the next attempt after the backoff
interval; the wait holds no worker slot and no back process, and it survives a back or worker
restart because the state lives in Temporal, not in memory. It stops on the first success, on a
non-retryable error, or when the policy's attempts run out. Only then does the workflow record the
terminal outcome in the run log (D-A9-7). So yes: a failed asynchronous delivery is tried again, and
that is the part today's code cannot do at all — an in-process retry would die with the process.

**Why not synchronous.** Nothing inside the run waits on delivery (Q7, and the sink-only handles),
so "only move on after all retries" has no next node to protect. What would wait is the caller and
the parent of a sub-flow. A retry budget worth having (minutes, D-A9-2) does not fit any of them:
`/api-v2`'s synchronous wait is 30 s, the server timeout on `/run-public-flow` is 300 s
(`main.ts:228`), the Bull job timeout is 600 s, and a parent flow-caller node would sit blocked for
the whole budget. A synchronous retry short enough to fit those limits (a few seconds) would not
survive the thirty-second outage in the user case. The run's outcome is its nodes' outcome; the
output was produced whether or not the notification of it arrived.

**Rejected.** *Synchronous with full retries* — blocks callers past their timeouts. *Synchronous
first attempt, asynchronous retries* — keeps today's latency and today's coupling (an email failure
would still have to be reported somewhere after the caller already has its answer), for no gain.
*Bull queue in back* — gives retries without Temporal, but B4 would have to move it again and it
depends on the one Redis node whose eviction policy is already a finding (`TASK-E5`).

**Behaviour changes this decision accepts — named, not implied:**

- A Gmail/Microsoft send failure no longer fails the run, no longer fails a parent run, and no longer
  skips saving the chat log and session state (`FS:5651–5685`).
- Callers get their answer without waiting for delivery; `flow_execution_status` reaches
  `completed` before callbacks go out.
- An SMTP failure stops being invisible: it is retried and, if terminal, shown.
- If Temporal is unreachable when the run ends, delivery is not attempted and back writes the same
  `'Delivery failed'` row itself (D-A9-7) — there is no inline fallback, because an inline twin is
  exactly what PLAN §3.4 point 4 forbids.
- A callback URL that is not a URL stops being dropped silently: it is refused non-retryable on
  the first attempt and shown as a `'Delivery failed'` row. Prod stores 29 edge-fed callback values
  that are not URLs (Q2), so the flows behind them start showing a row per run — the failure was
  always there, and that is the intended visibility, named here so it is not read as a regression.
- Ordering between the node callback and the consolidated callback: see D-A9-3.

### D-A9-2 — per-channel retry policies

Chosen per channel, not inherited from `COMMON`. **Q3 (prod, 2026-09-29) keeps them:** of the api-v2
runs with a callback since 2026-08-24, 936 completed and 10 ended `error` (≤ 1 %, and the query
cannot separate a run error from the status overwrite), which gives no rate to tune against. Today's node-callback and SMTP failure rates exist only in
Winston logs, and there is no Datadog to count them (M8 dropped 2026-09-29), so the first week after
release tunes them from the `Delivery failed` rows and the per-attempt worker logs.

| | Callback (node and consolidated) | Email (SMTP, Gmail, Microsoft) |
|---|---|---|
| `startToCloseTimeout` | 15 s (the 10 s HTTP timeout stays) | 2 min (attachment fetch + send) |
| `initialInterval` / `backoffCoefficient` / `maximumInterval` | 5 s / 2 / 2 min | 30 s / 2 / 2 min |
| `maximumAttempts` | 8 — waits 5, 10, 20, 40, 80, 120, 120 s ≈ 6.6 min of outage covered | 3 — waits 30, 60 s |
| Retryable | network errors, timeouts, 5xx, 408, 425, 429 (honours `Retry-After` through `ApplicationFailure.nextRetryDelay`, capped at 2 min) | connection errors, SMTP 421/450/451/452, Gmail/Graph 429 and 5xx |
| Non-retryable | other 4xx, egress refusal (D-A9-5), malformed URL | SMTP 5xx permanent, auth failures (SMTP 535/EAUTH, Gmail `invalid_grant`, Microsoft token failure), no valid recipient |

Why they differ: a customer endpoint mid-deploy recovers in seconds to minutes and retrying costs it
nothing; a rate-limited SMTP relay gets worse when retried into, and a permanent SMTP rejection will
not change. `ApplicationFailure.nonRetryable` and `nextRetryDelay` are both in `@temporalio/common`
1.14.1, the version the worker pins. Errors go through `runNodeActivity`'s classification so the
retryable/non-retryable split has one source.

### D-A9-3 — the consolidated callback is covered, not left fire-and-forget

**Decided by the user 2026-09-29.** The api-v2 consolidated callback uses the same callback activity
and policy as the node callback. When it fails, `flow_execution_status` stays `completed` (the run
did complete), no contradictory `success:false` post is sent, and the terminal failure goes to the
run log. When the run itself fails, the existing error callback is sent — through the same activity,
so it is retried too. Payload unchanged.

**Ordering, resolved by Q5 = 0.** Today a caller that has both sees the node callback first
(`apiV2Job.processor.ts:137` then `:176`). Prod has 947 api-v2 runs with a callback in 180 days and
none of them also had a node callback or an email (Q5), so no caller observes the order. One path
serves both cases, and it is the simpler one: for api-v2 runs `apiV2` hands its plan to the
processor instead of starting it, and the processor starts a single `deliverRunOutputs` whose last
step is the consolidated callback, after the node callbacks settle (emails are not waited on).
Without Q5 = 0 this would still keep the observed order; with it, the wait never happens.

**Per node, the callback follows the email, and is withheld exactly when it is today:** when the
email is suppressed by either key, or when a Gmail/Microsoft send fails terminally (today that throw
skips the callback). An SMTP failure does not withhold it (today `sendMail` swallows the error and the
callback goes out). Q1: 19 prod nodes have both.

### D-A9-4 — existing defects are preserved and filed, not fixed here

**Decided by the user 2026-09-29.** This task moves and retries; it does not redesign. Each defect
below keeps its current behaviour, gets a parity test that pins it, and becomes its own ClickUp bug.
**Revised 2026-09-29:** defect 1 is fixed inside A9 as [Addendum A](#addendum-a--gmail-to-every-recipient-optional);
the others are subtasks of A9, specified in [Follow-ups found during A9](#follow-ups-found-during-a9).
Prod counts from Q1 (2026-09-29):

1. Gmail sends only to the first recipient (`mail.service.ts:746`) — the others are silently dropped.
   **Prod: 0 of 11 Gmail nodes store more than one recipient**, but edge-fed recipients are decided at
   run time and the field tells users several addresses work. **Fixed in A9 — Addendum A.**
2. The node callback ignores `enabledCallbackUrl` and `callbackUrlData`, both of which the MCP
   metadata says gate it (`node-type-metadata.ts:566–609`). **Prod: all 37 callbacks have the flag
   off**, so the flag gates nothing anyone relies on. The bug is the metadata and the UI, not the
   dispatch: gating on the flag would silence 37 of 37 callbacks. **Fixed in A9 (A9.2):** the UI has no
   toggle at all (`enabledCallbackUrl` was only a form default), so the flag and the wrong key left the
   metadata; the edge key is `callbackUrlInputData`, the one `resolveNodeCallbackUrl` reads.
3. The node callback fires in batch runs; `sendEmail=false` gates only email. **Decided (A9.3,
   2026-09-30): kept by design.** Product wants the callback available in batch runs and sub-flow runs
   even where nobody uses it yet, so bulk sends with a callback stay possible. The MCP metadata states
   the rule, and the parity test pins it (back `c4aff224`). Q11 is no longer needed for the decision.
4. Delivery is not gated on cancel, budget stop or node error; a cancelled run still sends. **Fixed in
   A9 (A9.4):** a cancelled or budget-stopped run delivers nothing. In a run where a node failed,
   output nodes that completed deliver as before. An output node that did not run holds the empty
   text the run start writes (`FS:2920`), so its callback and any email without attachments are
   withheld. Its email still goes out when it carries attachments, the one part that is not empty.
   Product chose that on 2026-09-30 after Q12 counted 16 such runs in 2 flows, so the rule refuses
   nothing that had content. A run that finishes is unchanged. Prod sizing is Q10 and Q12 (0 cancelled,
   0 ceiling- or budget-stopped delivering runs). Implemented by `withholdUndeliverable`: back
   `2af72cbe`, refined in `bee19525`.
5. Attachments are downloaded even when email is off (prod: 24 nodes). **Not preserved — the one
   deliberate deviation:** the fetch moves inside the email activity, so a node with email off no
   longer downloads anything. Today that download is discarded unused; keeping it would need an
   activity that only fetches and throws away, holding a worker slot and an outbound request per run
   for no output. Reversible in one delivery kind if the user wants the GET kept.
6. The same child output node run twice in one parent run: the second email is suppressed (shared
   `runLogProcessId`). **Fixed in A9 (A9.5):** a run started with a `parentProcessId` gets its own
   delivery scope — what it already got when space logging is off (`FS:2566`); top-level keys unchanged.
7. A Microsoft token failure deletes the user's integration. **Fixed in A9 (A9.6):** only a revoked
   grant (`InteractionRequiredAuthError`, `invalid_grant`, `no_account_found`) deletes it; any other
   failure keeps it and raises 503, which the token broker now passes on so the worker retries.

Not preserved, on purpose, because fixing them *is* this task: SMTP failures being swallowed, and
the consolidated callback's status overwrite and double post (D-A9-3).

### D-A9-5 — a minimal egress guard, shaped as S6's first cut

**Decided by the user 2026-09-29:** a minimal guard, with no conflict with S6 and no dependency on
it. A9 moves every user-controlled outbound fetch of the delivery path (node callback, consolidated
callback, attachment downloads) into the worker, which holds the DB password and
`INTEGRATIONS_ENCRYPTION_KEY`, so it cannot move them unchecked.

One module, `worker/src/modules/egress/egress-policy.ts`, used by every A9 call site and by nothing
else yet. It exports `assertEgressAllowed(url, { mode, allow? })`, a `safeLookup` for axios' `lookup`
option, and `EGRESS_DENY_RANGES`.

| Rule | Relation to S6 |
|---|---|
| `http`/`https` only; userinfo (`user:pass@`) refused | subset |
| Host taken from the WHATWG-normalised `new URL().hostname` (turns `2130706433`, `0x7f.1` into `127.0.0.1`) | S6: "not the string" |
| `dns.lookup(host, {all:true})`; refused if **any** address is in the deny set: `0/8`, `10/8`, `100.64/10`, `127/8`, `169.254/16`, `172.16/12`, `192.0.0/24`, `192.168/16`, `198.18/15`, `224/4`, `240/4`, `255.255.255.255`, `::`, `::1`, `fc00::/7`, `fe80::/10`, `ff00::/8`; `::ffff:a.b.c.d` and `64:ff9b::/96` unwrapped and re-checked. Implemented with `net.BlockList` (Node 22 in both Dockerfiles) — no new dependency | S6 names loopback, link-local, private and unique-local; the rest is a strict superset nobody legitimately needs |
| The checked address is the one connected to (`safeLookup` as axios' `lookup`), so a rebinding answer cannot slip in between check and connect | strengthens "resolved address" |
| Redirects keep being followed as today, and every hop goes through `safeLookup`. An IP literal never reaches a resolver, so a hop to one is checked synchronously in axios' `beforeRedirect` | S6: "re-check on redirect" |
| `proxy: false` on these clients, so an env proxy cannot bypass the lookup | neutral |
| Attachment fetch gets a 30 s timeout and a 25 MB cap (the Gmail/SMTP message ceiling — nothing that sends today is refused by it) | neutral; not a policy |
| A refusal is a non-retryable `UserConfigError` (failure type `user_config`) whose message starts `egress_refused host=… reason=…` — host + reason in the run log, no payload. A DNS failure is retryable, never a refusal | S6: "unresolvable is unverifiable, not blocked" |
| `EGRESS_POLICY_MODE=off\|report\|enforce`, default **`report`**: log `egress_would_refuse` and let the request through. `enforce` only after Q2 + Q6 show zero "refused although it works" and one week in `report` with none | S6 + PLAN §3.3.2: measure, then report-only, then enforce |
| No per-org allowlist in A9, but the optional `allow` hook is where S6 plugs it in without touching call sites | S6 owns the allowlist |

This is recorded in `TASK-S6-SSRF-POLICY.md` as the adopted first cut, so S6 extends this module
(allowlist, apiCaller's undici dispatcher, back's `/downloader`) instead of writing a second one.
**Dev and prod, 2026-09-29:** zero would-be refusals. Prod stores no literal private address
(Q2); its 18 distinct hosts all resolve to public addresses only, classified by the shipped
`isDeniedAddress` rather than a copy of it (Q6, `a9-q6-dns-resolution.prod.txt`). What stays
unverifiable from outside AWS is a split-horizon answer inside the worker's VPC — `api.fluxprompt.ai`
is one of the hosts — which is exactly what the report-mode week measures before `enforce`.

### D-A9-6 — the dedup protocol: same keys, claim–send–confirm

The key names, formats and TTLs stay exactly as they are. What changes is the order of operations,
because claim-before-send and never-release is what made retry unsafe:

The claim carries its owner, `${workflowId}:${activityId}`, which is the same on every attempt of
one activity and different for any other delivery (refined during implementation — a bare `pending`
could not tell "my own previous attempt died" from "someone else is sending").

1. **Claim** `email-sent:…` with `SET <key> pending:<owner> EX 300 NX` (300 s > the email
   `startToCloseTimeout`). If the key exists: `sent` or `1` (a value written by the old code) →
   suppressed, the activity succeeds without sending; `pending:<same owner>` → a previous attempt of
   this activity died mid-flight → reclaim and send; `pending:<other owner>` → another delivery of
   the same run and node is in flight → suppressed, as the old code would.
2. **Claim** `email-content:…` with `SET <key> <owner> EX 90 NX`; the same owner reclaims, anyone
   else is suppressed as today (and the sent key is set to `sent`, as today's `'1'` stayed).
3. **Send.**
4. **Confirm** on success: `SET email-sent:… sent EX 86400`. The content key keeps its 90 s.
5. **Release** on failure: delete each key only if it still holds this owner's value (one Lua
   compare-and-delete), then rethrow, so the next attempt can claim.

The residual window: a worker dying between a successful send and the confirm leaves
`pending:<owner>`, and the retry of the same activity reclaims it and sends again. That is at-least-once, not exactly-once, and
it is the honest guarantee — stated here rather than implied away.

Callbacks get no Redis key. Their idempotency is the header in D-A9-8, which the receiver can use;
a key could not tell "the receiver processed it but answered slowly" from "it never arrived".

### D-A9-7 — the failure surface is the flow's log table, the one the user sees

**"The run log" means `flows_logs`, not `space_run_logs`.** `space_run_logs` is the internal staff
view (`space_run_logs.controller.ts:31–32`, `ApiKeyGuard` + `InternalStaffGuard`, under
`/admin/space-logging`); it is written only when `spaces.loggingEnabled` and never for `manual` or
`chatbot` runs (`FS:2661–2665`); and its `summary.warnings` is rebuilt from the node tree by
`finalize` (`run-log-collector.ts:108–128`), so a warning appended afterwards would be erased.
`flows_logs` is what the customer reads: `GET /flow-logs?flowId=` (`flow_logs.controller.ts:22`,
`JwtAuthGuard`) rendered by the flow's log table (`front/src/components/nodes/FlowGlobalNode.tsx:1000–1090`,
status text plus an "Error info" button).

When an activity ends in terminal failure, the workflow calls a last activity that posts
`{ flowId, nodeId, channel, runType, attempts, lastErrorCode, lastErrorMessage }` to a new internal
endpoint `POST /worker/delivery-outcome` (`worker.controller.ts`, `InternalApiGuard`, the pattern of
`/worker/refresh-oauth-token`). Back writes one `flows_logs` row — `status: 'Delivery failed'`,
`error_message` (`<Channel> to <host> from node <id> was not delivered: <last error>` — no "after
retries", since a refused value is tried once and the row cannot tell) naming the channel, the destination host (never the full URL or recipients) and the
last error, `error_status_code` the last HTTP/SMTP code, `run_type` the run's, `spent_tokens` and
`cost` 0, `mcp_token_id` null — and logs it to Winston. The front's "Error info" button condition
(`FlowGlobalNode.tsx:1070`, today `status === 'Error while running'`) also accepts
`'Delivery failed'`: a one-condition front change, and the only front change in A9.

This is the same shape the user sees today when a Gmail/Microsoft send fails — a second row, then
`'Error while running'` (`FS:5776–5786`) — so D-A9-1 replaces that row rather than removing the
signal. One side effect is measured rather than assumed: `getMcpRunCallsForCompany`
(`company-admin-members.service.ts:~245`) counts `flows_logs` rows with `run_type = 'mcp'` without
filtering status, so an MCP run whose delivery fails terminally counts twice there — exactly as an
MCP run whose email fails does today. The per-user counts join `mcp_tokens` and are not affected
because the row's `mcp_token_id` is null. No new column, no migration.

### D-A9-8 — callback idempotency header

**Decided by the user 2026-09-29.** Every callback carries `X-FluxPrompt-Delivery-Id`, the same
value on every attempt of the same delivery: `${runLogProcessId}:${flowId}:${nodeId}:callback` for
the node callback, `${executionId}:consolidated` for the api-v2 one. The body is unchanged. Retrying
makes delivery at-least-once; the header is what lets a receiver make it effectively-once.

## Design

**Back.** `OutputDeliveryService` (`src/app-api/flux/output-delivery/`) replaces `FS:5357–5599`
(the `persistNodeDataToLiveRow` pass at `FS:5335–5348` stays). It builds the delivery plan exactly
as the block resolves it today — recipients, subject, text, template choice, attachment URLs,
provider, callback URL, `sendEmail` gate — and starts `deliverRunOutputs` without awaiting it.
Workflow id `output-delivery-${flowId}-${runLogProcessId}-${invocationId}` (`invocationId` a UUID
per `apiV2` call, so a child flow run twice in one parent run is two workflows, as it is two
deliveries today; the email keys keep suppressing the second email exactly as now). For api-v2 runs
the processor passes a sink: `apiV2` hands the plan to it instead of starting, and the processor
starts one workflow carrying the node deliveries and the consolidated callback (D-A9-3) — also on
its error path, so a plan collected before a later throw is not lost. `validateCallbackUrl` is
unchanged.

**Worker.** `modules/delivery/` (`delivery.module.ts`, `delivery.types.ts`, `delivery-plan.ts`,
`delivery-plan.store.ts`, `delivery-dedup.service.ts`, `delivery-errors.ts`, `email-attachments.ts`,
`email-delivery.service.ts`, `smtp-email.sender.ts`, `gmail-email.sender.ts`,
`microsoft-email.sender.ts`, `callback-delivery.service.ts`, `delivery-outcome.reporter.ts`,
`delivery.activities.ts`, specs), `modules/egress/egress-policy.ts`,
`workflows/deliver-run-outputs.workflow.ts` exported from `workflows/index.ts`, activities in their
own `DeliveryActivities` class (not `ActivitiesService`, which three specs build positionally) wrapped
in `runNodeActivity`, bound in `worker.service.ts`, and proxied in `configs.ts` with the D-A9-2
policies. `NodeError` gains two optional fields, `statusCode` and `retryAfterMs`, which
`runNodeActivity` turns into the failure detail and `nextRetryDelay` — additive, no node sets them.
SMTP needs `nodemailer` in the worker (the back's major, 6.x). Gmail and Microsoft send with tokens from the existing broker;
SMTP gets the `EMAIL_*` variables; Redis dedup uses a plain ioredis client on the existing
`REDIS_HOST`/`REDIS_PORT`, which must be the same Redis as back's (a deploy check, not assumed).

**Payload.** The plan carries URLs and ids, not fetched attachment bytes; attachments are fetched
inside the email activity. The body cannot always go inline: on dev the output text has p99 57 KB
but a max of 3 MB, with 6 nodes above 256 KB and 1 above 1 MB (Q8), and Temporal's self-hosted
default rejects a payload above 2 MB. Prod is larger still: max 9.2 MB, 8 above 256 KB, 3 above
1 MB (Q8). So a plan whose serialised size is at most 256 KB (the claim
check's threshold, `claim-check.ts:3–5`) goes inline; a larger one is written by back to S3 at
`delivery-plans/${workflowId}.json` with the existing `AwsService.uploadFile`, the workflow input
carries only the key, the worker reads it with its existing S3 client and credentials, and the last
activity deletes it. The node-execution claim check is not reused: `/worker/get-payload` needs a
matching `node_executions` row (`claim-check-authz.service.ts:136–157`), dev's output-node rows
carry no `output`/`outputData` (119 of 119 empty), and inbound-mail runs use a non-UUID process id
(`pop3-processed:…`, `mail.service.ts:379–382`) that the uuid `execId` column rejects.

**Capacity, resolved by Q4: shared queue.** Delivery activities share the 10 slots on
`enhanced-ai-queue`; an attempt holds one for at most 15 s (callback) or 2 min (email), and backoff
waits hold none. Prod peaks at 16 deliveries in one minute (303 delivering runs in 30 days): at a
few seconds per send that is under one slot on average. The worst case — an SMTP relay hanging every
send to the 2-minute timeout at that peak — would hold slots for minutes, and is what the first week's
per-attempt logs watch for; a dedicated task queue is the lever if it happens.

**Env.** Worker: `EMAIL_SERVICE`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`,
`EMAIL_FROM_ADDRESS`, `EGRESS_POLICY_MODE`. **Verified 2026-09-29 (read-only, `aws ecs
describe-task-definition`):** `worker-task-definition-{dev,staging,prod}` already reference the same
`EMAIL_*_<ENV>` and `REDIS_HOST_<ENV>`/`REDIS_PORT_<ENV>` SSM parameters as `api-task-definition-<env>`,
so no infra change is needed and the dedup keys live in the back's Redis. Run `env-vars-sync`.

**Keeping the worker's email env equal to the back's (A9.10, `868mdg20t`).** In the worker only the SMTP
path reads credentials from env (`smtp-email.sender.ts`: `EMAIL_*`, one platform-wide account; with
`EMAIL_HOST` and `EMAIL_SERVICE` both unset every SMTP email fails non-retryably as "The email could not
be sent."). Gmail and Microsoft read no env credential: the worker asks the back for the user's OAuth
token (`POST ${URL_MAIN_API}/worker/refresh-oauth-token`, `INTERNAL_API_KEY`), and the back reads the
integration from the database. The 2026-09-29 check above is a snapshot; `etc/sync-worker-env-from-back.sh`
makes it repeatable and applies the difference:

```bash
etc/sync-worker-env-from-back.sh <dev|staging|prod>             # read-only: plan + would-be task definition, exit 2 on drift
etc/sync-worker-env-from-back.sh dev --apply                    # register a new worker revision
etc/sync-worker-env-from-back.sh dev --deploy                   # ...and point the worker service at it now
CONFIRM_PROD=yes etc/sync-worker-env-from-back.sh prod --apply  # prod writes need the confirmation
```

- It compares `api-container-<env>` in `api-task-definition-<env>` with `worker-container-<env>` in
  `worker-task-definition-<env>` for `EMAIL_SERVICE EMAIL_HOST EMAIL_PORT EMAIL_USER EMAIL_PASSWORD
  EMAIL_FROM_ADDRESS REDIS_HOST REDIS_PORT` (`--vars` overrides the list), and reports each as
  `same`, `add`, `replace` or `absent-in-back`.
- SSM secrets are copied by reference (`valueFrom`); no secret value is read or printed, and plain
  values other than host/port/service/from are masked. Every other worker variable is kept as it is.
- `--apply` without `--deploy` is enough for the next deploy: the worker CI starts from
  `aws ecs describe-task-definition --task-definition worker-task-definition-<env>`, the latest revision.
  The script prints the previous revision and the undo/rollback command.
- When it adds an SSM reference and the worker's `executionRoleArn` differs from the back's, it warns
  that the worker role needs `ssm:GetParameters` (and `kms:Decrypt` for SecureString) on those
  parameters; without it the new tasks fail to start with `ResourceInitializationError`.
- Verified offline (2026-10-06) against task-definition fixtures: 15 checks (add, replace, plain→SSM,
  same, absent, role warning, no duplicate names, unrelated vars kept, read-only fields stripped, a
  second run reports in sync, prod refused without `CONFIRM_PROD`, wrong container fails). Removing the
  filter that drops the old entry turned 3 of them red (duplicate names, plain+SSM `EMAIL_USER`, second
  run not in sync).
- First run against AWS, prod, read-only (2026-10-06): all 8 variables `same` — the worker references
  the back's `EMAIL_*_PROD`, `REDIS_HOST_PROD` and `REDIS_PORT_PROD` SSM parameters; nothing to apply.

## Scope

**In.** D-A9-1 to D-A9-8; extracting the block while moving it; deleting the inline block once the
workflow path is live (no inline twin).

**Out.** Payload shapes, recipients, and when delivery triggers (D-A9-4 lists what stays wrong on
purpose). SES or any change of mail provider — see *Alternatives*. The per-org allowlist and every
non-delivery fetch (apiCaller, scraper, `/downloader`, `/proxy`) — S6. Moving the flow loop — B4;
when B4 lands, `deliverRunOutputs` becomes its last step and the back start is deleted.

## Alternatives considered

- **AWS EventBridge API Destinations** — has 24 h retry and a DLQ, but needs one API destination
  resource per endpoint URL; customer URLs are dynamic. Does not fit.
- **SQS + DLQ** — duplicates what Temporal already gives, and back/worker have no infrastructure as
  code to add it to.
- **Keep the mail stacks in back, have a worker activity call a back endpoint to send** — avoids
  porting, but every retry then depends on back being up and holding the send, which is the coupling
  this task removes.
- **SES instead of the SMTP relay** — the real gain on the email side (higher limits, bounce and
  complaint events), but it changes the sender, which is a redesign. Worth its own task; not A9.

## Measurements

Read-only, aggregates only, validated against the prod read-only validator and run on dev on
2026-09-29. Prod was run by a human: Q1–Q8 on 2026-09-29, Q9–Q12 on 2026-09-30. Each
result sits next to its query in this folder as `a9-qN-….prod.csv` (Q6's DNS pass as
`a9-q6-dns-resolution.prod.txt`). To re-run any of them, see "Re-validating A9" below.

| # | Query · result | Answers | Dev | Prod (Q1–Q8 2026-09-29, Q9–Q12 2026-09-30) | Decides |
|---|---|---|---|---|---|
| Q1 | `a9-q1-output-node-config.sql` · `.prod.csv` | channel split; how many nodes each D-A9-4 defect touches | 1040 output nodes; email on 126 (SMTP 116, Gmail 9 — 2 multi-recipient —, Microsoft 1); callbacks 6 (4 with the flag off) | 5301 output nodes in 4778 flows; email on 1406 (1202 with recipients): SMTP 1394, Gmail 11 (**0** multi-recipient), Microsoft 1; callback URL on **37, all 37 with `enabledCallbackUrl` off**; 23 callbacks fed by an edge; `callbackUrlData` 0; attachments on 339, **24 fetched with email off**; 19 nodes with email **and** callback | D-A9-4 counts; the D-A9-3 callback-withholding rule touches 19 nodes |
| Q2 | `a9-q2-egress-classification.sql` · `.prod.csv` | D-A9-5 would-be refusals | 0 | 0 literal private addresses; every URL needs DNS (api-v2 947 rows / 2 hosts, attachments 814 / 19, node callbacks 128 / 16); 36 values not a URL (fail today too); 4 templated, unverifiable | enforce readiness, with Q6 |
| Q3 | `a9-q3-apiv2-callback-outcomes.sql` · `.prod.csv` | lost consolidated callbacks and their error kinds (D-A9-2, D-A9-3) | no callbacks in dev | api-v2 runs with a callback, 2026-08-24 → 09-29: 936 `completed`, 10 `error` (kind `other`), 1 `in_progress`. At most ~1 % ended `error`; the query cannot tell a run error from the status overwrite | D-A9-2 values kept — no evidence to change them |
| Q4 | `a9-q4-delivery-run-volume.sql` · `.prod.csv` | delivering runs per entry point; peak per minute (capacity) | 0 runs in 30 d | 303 delivering runs in 30 d (api 192, formapi 102, webhook 6, cronjob 1, mcp 1 — email; api 1 — callback); peak **16 deliveries in one minute** | capacity: 16 × ~3 s ≈ 0.8 slot on average → **shared queue** |
| Q5 | `a9-q5-callback-overlap.sql` · `.prod.csv` | D-A9-3 ordering | 0 | 947 api-v2 runs with a callback URL in 180 d (13 flows, 2 callers); **0** also had a node callback or an email | ordering has no case in prod |
| Q6 | `a9-q6-distinct-hosts.sql` · `.prod.csv` + `a9-q6-dns-resolution.prod.txt` | D-A9-5 on public-looking names | 3 hosts, all public | 18 hosts, all resolve to public addresses only through the shipped `isDeniedAddress` — **0 would-be refusals**. Unverifiable from outside AWS: split-horizon answers inside the worker VPC (`api.fluxprompt.ai` is one of the hosts) | enforce needs the report-mode week |
| Q7 | `a9-q7-output-node-outgoing-edges.sql` · `.prod.csv` | nothing waits on delivery | 0 | **4** edges leave an output node, in 3 flows (targets `apiCaller`, `counterNode`, `stickyNote`). They do not wait on delivery: the scheduler loop finishes (`FS:5090`) before the delivery block starts (`FS:5329`), so those nodes already ran | D-A9-1 holds |
| Q8 | `a9-q8-output-body-size.sql` · `.prod.csv` | whether the body fits inline in the workflow input | p99 57 KB, max 3 MB; 6 over 256 KB, 1 over 1 MB | 3048 with text: p50 64 B, p99 57 KB, **max 9.2 MB** (node data 9.7 MB); 8 over 256 KB, 3 over 1 MB | by reference above 256 KB is required, not optional |
| Q9 | `a9-q9-customer-impact.sql` · `.prod.csv` | customer impact of the two visible differences and of edge-fed Gmail recipients: nodes, flows, owners, runs in 30 d | runs; dev: attachments with email off 2 nodes / 1 flow / 0 runs; Gmail edge-fed 1 / 1 / 0; non-URL callbacks 0 | attachments with email off 24 nodes / 22 flows / 4 owners / **0 runs**; non-URL callbacks 29 / 2 / 2 / **0 runs**; Gmail edge-fed recipients 8 / 8 / 6 / **0 runs**. None of the three ran in 30 d, so no customer sees either difference today | the test plans below; Addendum A |
| Q10 | `a9-q10-stopped-run-deliveries.sql` · `.prod.csv` | A9.4 refusal size: runs in 30 d of delivering flows that were cancelled, ceiling-stopped, or failed | 0 rows | cancelled **0**, spend-ceiling **0**; `Error while running` **1526 runs / 11 flows / 8 owners** (email flows, no callback). An upper bound, not a refusal count: the row is also written on the exception path, which never delivered, and in a node-failure run A9.4 withholds only output nodes that did not run, whose body is empty (text reset at run start). The query's note that budget stops write this row was wrong: they write `Stopped by …` and are counted by Q12 | A9.4 |
| Q11 | `a9-q11-callbacks-in-batch-and-sub-runs.sql` · `.prod.csv` | A9.3: callbacks fired per run type (batch, library-node, flow-caller-node) in 30 d | 0 rows | batch / library-node / flow-caller-node **0**; callbacks only on `api` (9 runs, 1 flow) and `cronjob` (5, 1). Confirms the A9.3 decision changes nothing for anyone today | A9.3 |
| Q12 | `a9-q12-budget-stops-and-failed-attachments.sql` · `.prod.csv` | the A9.4 cases Q10 could not see: budget-stopped runs of delivering flows (A9.4 withholds every output node, including one that ran), and failed runs of flows whose email node has attachments (a withheld empty-body email could still carry a file) | 0 rows (no delivering flow was ever budget-stopped in dev) | budget-stopped delivering runs **0**; failed runs of flows with email attachments **16 runs / 2 flows / 2 owners**, email only. An upper bound: the email is withheld only when the output node did not run, and whether it ran is not stored, so the count is unverifiable per run | A9.4 |
| M8 | ~~Datadog counts of `webhook_error` / `MailService.sendMail failed`~~ | real failure rates behind D-A9-2 | — | **dropped 2026-09-29** — no Datadog access; replaced by the first week of `Delivery failed` rows | — |

### Re-validating A9

Everything needed to check this task again lives in this folder. Nothing depends on a local `etc/`.

**Files.** Each query is `a9-qN-<topic>.sql`, and the prod result it produced is next to it as
`a9-qN-<topic>.prod.csv` (Q6 also has `a9-q6-dns-resolution.prod.txt`). Every `.sql` header says
what it counts and how to run it. All queries are read-only and return aggregates only, with no ids,
URLs or recipients.

**Running a query.**
- **Dev** (anyone): run
  `QUERY="$(cat <file>.sql)" ENV=dev node .workflow/skills/ec2-tunnel/templates/tunnel-and-query.mjs`
  from the workspace root.
- **Prod**: a human with prod access runs it, read-only (the command in each file's header). Save
  the output over the `.prod.csv`, commit it, and update the date and the Prod column in the table
  above. Git keeps the earlier result.

**What would change a decision if it came back different.**

| Query | Result recorded | If a re-run shows… | …then |
|---|---|---|---|
| Q9 | 0 runs in 30 d for all three cases | runs > 0 in a case | customers now see that difference; re-check it against T-A / T-B / Addendum A |
| Q10 | 0 cancelled, 0 spend-ceiling; 1526 failed (upper bound) | cancelled or ceiling runs > 0 | expected (A9.4 withholds them by design); confirm with the flow owner if it is a large number |
| Q11 | 0 callbacks in batch / sub-runs | runs > 0 | nothing to change: the callback is kept by design (A9.3, 2026-09-30) |
| Q12 | `budget_stopped` 0 | `budget_stopped` runs > 0 | product decides whether a budget-stopped run still delivers the output nodes that already ran (today A9.4 withholds all of them) |
| Q12 | `failed_with_attachments` 16 runs / 2 flows (upper bound) | nothing to change: those emails still go out (A9.4, 2026-09-30) | a withheld empty-body email in those runs could have carried a real file; decide whether that is acceptable |
| Q2 / Q6 | 0 refusals on the 18 prod hosts | a refusal in `report` logs (`egress_would_refuse`) | fix or allow the host before switching `EGRESS_POLICY_MODE` to `enforce` |

For every other query, its row's "Decides" column in the table above says what it settles.

**Tests to re-run.** Cap Jest at 4 GB heap and one worker.
- **worker**:
  `DELIVERY_TEST_REDIS_URL=redis://127.0.0.1:6390 DELIVERY_TEST_TEMPORAL=1 NODE_OPTIONS=--max-old-space-size=4096 npx jest --maxWorkers=1 src/modules/delivery src/modules/temporal/workflows/deliver-run-outputs src/modules/egress`
  - Without the two env vars, the real-Redis dedup and real-Temporal e2e suites are skipped.
  - Start Redis with `docker run -d --rm --name a9-redis -p 6390:6379 redis:7-alpine`.
- **back**:
  `NODE_OPTIONS=--max-old-space-size=4096 npx jest --maxWorkers=1 src/app-api/flux/output-delivery src/jobs/apiV2Job src/app-api/mail/mail.gmail-recipients.spec.ts src/app-api/microsoft/microsoft-auth.token-errors.spec.ts src/temporal/worker.controller.spec.ts src/app-mcp/node-types/node-types.service.spec.ts`
- **front**: `pnpm vitest run --project unit tests/unit/util/flowLogStatus.test.ts`

The "Verification" section lists the negative control behind each test. Break the named line and
the test must go red.

**Task tracking.** A9 and its subtasks A9.1–A9.6 each carry Description, User Case, Acceptance
Criteria and Test Case in ClickUp. A criterion is checked only when a test covers it (see the
"Follow-ups found during A9" table for commits and ClickUp links). QA confirms on dev.

## Addendum A — Gmail to every recipient (optional)

**Added 2026-09-29 at the user's request; optional** — it is two self-contained commits and reverts
without touching the rest of A9. ClickUp: [A9.1](https://app.clickup.com/t/868mbdm92).

- **Before.** `sendGmailEmail` put only `to[0]` in `To:` ([`mail.service.ts:746`](https://github.com/enhancedai-com/Flux-Prompt/blob/94cb2e264a0bd518529a7e2156c094e8dd0a5f76/src/app-api/mail/mail.service.ts#L746));
  the node field says "email(s) separated by ,", and SMTP and Microsoft send to all of them.
- **After.** Every valid, trimmed recipient goes in one `To:` header, as SMTP and Microsoft do. A value
  containing CR/LF is dropped (it could otherwise add a header such as `Bcc:` — a risk `to[0]` already
  had); an empty list is refused non-retryable before Google is called.
- **Where.** Both paths that send Gmail: the run's delivery, worker `gmail-email.sender.ts`
  ([`e6c7359`](https://github.com/enhancedai-com/Flux-Prompt-Worker/commit/e6c73591b6a3b0cacbf135878c937cdb3d7d4fb0)),
  and the node's Send button, back `POST /mail/send-gmail` → `mail.service.ts`
  ([`5eaa654`](https://github.com/enhancedai-com/Flux-Prompt/commit/5eaa6547efef008a65e551f5d83302bf99054022)).
- **Visible to the customer.** Recipients see each other in `To`, exactly as with SMTP/Microsoft today.
- **Tests.** Worker `email-senders.spec.ts` (every recipient; blank/CR-LF dropped; empty refused without
  calling Google) and back `mail.gmail-recipients.spec.ts` (the real `sendGmailEmail`, only Google
  mocked, both the plain and the multipart `To:`). Negative controls observed: back to `to[0]` → the
  every-recipient test fails; filter removed → the CR/LF test fails; guard removed → the refusal test
  fails, in both repos.

## Test plans for the two visible differences

Both prove the same claim: the customer loses nothing, and what changes is shown, not silent.

### T-A — attachments are no longer downloaded when no email goes out (defect 5 deviation)

**Before:** every output node with attachment URLs downloaded each URL on every run (`axios.get`, no
timeout, no size cap) and discarded it when email was off or the run had `sendEmail=false`
([`FS:5424`](https://github.com/enhancedai-com/Flux-Prompt/blob/94cb2e264a0bd518529a7e2156c094e8dd0a5f76/src/app-api/flux/flux.service.ts#L5424));
a failure went to the internal log only. **After:** no request at all.

| # | Evidence | Status |
|---|---|---|
| A1 | Code: on production the downloaded `files`/`result` are read only inside the email branch (`FS:5533`, `:5546`, `:5559`) — nothing else consumes them, so nothing the customer receives depended on the download | verified 2026-09-29 |
| A2 | Automated: `output-delivery-plan.spec.ts` "hands the worker no attachment URL when no email goes out" — email off with a callback, email off alone, and a batch run with email on: no attachment URL reaches the worker. Negative control: gate forced on → test fails | green, control observed |
| A3 | Structure: the worker fetches attachments only inside `deliverEmailActivity` (`email-attachments.ts`); with no email delivery there is no fetch path | verified |
| A4 | Prod size: Q9 `attachments_email_off` — nodes, flows, owners and runs in 30 d affected | 24 nodes / 22 flows / 4 owners, **0 runs in 30 d**: nobody is affected today |
| A5 | QA: output node with an attachment URL pointing at a request-logging endpoint (e.g. webhook.site), email off, callback on. Run 3×: the endpoint logs **0** GETs; the callback arrives 3× with the same body as before. Turn email on: 1 GET per run and the email carries the file | to run in QA |

### T-B — a callback value that is not a URL is tried once and shown

**Is there a retry limit for callbacks?** Yes, two: the callback policy `maximumAttempts: 8`
(`workflows/configs.ts`, D-A9-2), and — the one that applies here — a malformed URL is a
`UserConfigError` (`egress-policy.ts:169`), `nonRetryable = true`, so Temporal stops after attempt 1.
The check runs before the egress mode is read, so it holds even with `EGRESS_POLICY_MODE=off`.

**Before:** `axios.post("<text>")` threw `Invalid URL`; a `webhook_error` went to the internal log; the
customer saw nothing ([`FS:5576–5598`](https://github.com/enhancedai-com/Flux-Prompt/blob/94cb2e264a0bd518529a7e2156c094e8dd0a5f76/src/app-api/flux/flux.service.ts#L5576-L5598)).
**After:** the run still ends `completed`; one attempt, nothing sent, and one `Delivery failed` row:
`Callback to invalid-url from node <id> was not delivered: egress_malformed_url: …`.

| # | Evidence | Status |
|---|---|---|
| B1 | Automated, real Temporal: `deliver-run-outputs.e2e.spec.ts` "tries a callback value that is not a URL once, sends nothing and reports it" — attempts = 1, 0 HTTP hits, 1 report (`user_config`), guard off. Negative control: the refusal made retryable → Temporal keeps retrying and the test times out | green, control observed |
| B2 | Automated: `callback-delivery.service.spec.ts` "refuses a malformed URL without sending, in every mode" | green |
| B3 | Prod size: Q2 found 29 stored edge-fed values that are not URLs; Q9 `callback_not_a_url` gives flows, owners and an upper bound of runs in 30 d (the stored value is the last one an upstream node produced) | 29 nodes / 2 flows / 2 owners, **0 runs in 30 d**: nobody is affected today |
| B4 | QA: output node whose callback URL comes from a text node producing `hello`. Run: the run is `completed`, the flow log shows one `Delivery failed` row with "Error info", no retry rows follow. Replace the text with a real URL: the callback arrives and no row is written | to run in QA |

## Follow-ups found during A9

Defects found while moving delivery, each a subtask of A9. A9 pins today's behaviour for them (a parity
test each) so the move changes nothing for customers; fixing any of them changes what customers receive,
so each needs its own decision. They live here, not as epic tasks, because they are product bugs, not
worker-migration work; one that grows past this page gets its own `TASK-*.md` when it is picked up.

| Sub | Defect (D-A9-4) | What the customer sees | Fix | Status | ClickUp |
|---|---|---|---|---|---|
| A9.1 | 1 — Gmail first recipient only | only the first address gets the email | Addendum A — worker `e6c7359`, back [`5eaa6547`](https://github.com/enhancedai-com/Flux-Prompt/commit/5eaa6547efef008a65e551f5d83302bf99054022) | ready for QA | [868mbdm92](https://app.clickup.com/t/868mbdm92) |
| A9.2 | 2 — callback flag / MCP docs vs. reality | agents told a flag gates the callback; an edge linked to the documented key never arrives; the UI hid the connected URL | metadata drops `enabledCallbackUrl`/`callbackUrlData`, declares `callbackUrlInputData`; front shows it — back [`2b476942`](https://github.com/enhancedai-com/Flux-Prompt/commit/2b476942c14ff53c95d5098c7d25ae05012ac72a), front [`7d919e58`](https://github.com/enhancedai-com/Flux-Prompt-Frontend/commit/7d919e58) | ready for QA | [868mbdm9z](https://app.clickup.com/t/868mbdm9z) |
| A9.3 | 3 — callback in batch and sub-runs | one callback per batch row / per sub-run | kept by design and documented in the MCP metadata; parity test renamed | **fixed** — back `c4aff224` | [868mbdmah](https://app.clickup.com/t/868mbdmah) |
| A9.4 | 4 — cancel / budget / node error not checked | a cancelled run still emails; a failed run sends empty emails for nodes that never ran | `withholdUndeliverable` (an email with attachments from a node that did not run still goes out, 2026-09-30) — back [`bee19525`](https://github.com/enhancedai-com/Flux-Prompt/commit/bee19525), first cut [`2af72cbe`](https://github.com/enhancedai-com/Flux-Prompt/commit/2af72cbef8276b9f9cb5f324c6d39385033bbdaa) | ready for QA; Q10 before prod | [868mbdmb7](https://app.clickup.com/t/868mbdmb7) |
| A9.5 | 6 — sub-flow run twice shares the dedup key | second legitimate email dropped | `resolveDeliveryScopeId` — back [`1f506208`](https://github.com/enhancedai-com/Flux-Prompt/commit/1f5062084ca88235f073f4c8247b4529a3384bf7) | ready for QA | [868mbdmbn](https://app.clickup.com/t/868mbdmbn) |
| A9.6 | 7 — Microsoft token error deletes the integration | account disconnected after a transient error | `isMicrosoftGrantRevoked` + broker 503 — back [`f0f954d1`](https://github.com/enhancedai-com/Flux-Prompt/commit/f0f954d1eee0b1b1d2c3157a16bf5cbe3f666383) | ready for QA | [868mbdmc7](https://app.clickup.com/t/868mbdmc7) |

**Found while fixing A9.4, not fixed (out of scope, needs its own decision):** in a run that finishes
normally, an output node on a condition branch that was not taken still delivers — with the empty
text the run start wrote (`FS:2920`), so its recipients get an empty email and its callback an empty
`text`. Skipping untaken branches changes what completed runs send, so it is measured and decided
separately, not folded into A9.4.

Each ClickUp subtask carries the description, use case, acceptance criteria and test cases, with
permalinks to production `94cb2e26`. Defect 5 is not a follow-up: it is the deliberate deviation, T-A.

## Verification

- **Retry, negative control (required).** Callback to an endpoint that returns 500, 500, 200:
  delivered on attempt 3. Set `maximumAttempts: 1` and watch it fail.
- **Retry is not suppressed by dedup.** Email send fails on attempt 1 and succeeds on 2: exactly one
  email. Restore claim-before-send-without-release and watch attempt 2 be suppressed — the defect
  in correction 1, reproduced.
- **Double-send.** Run the email activity twice for the same run and node: the second is suppressed.
  Delete the key between runs: it sends twice. That proves the key is load-bearing.
- **Idempotency header** is identical across every attempt of one delivery, and differs between
  deliveries.
- **Egress.** `enforce`: `http://169.254.169.254/` refused non-retryable; an allowed host that 302s to
  `10.0.0.1` refused; a host resolving to both a public and a private address refused. `report`: the
  same requests go through and log `egress_would_refuse`. A DNS failure is retried, not refused.
  Break the range check and watch these go red.
- **Email parity, per path.** SMTP, Gmail and Microsoft each: same recipients (Gmail now every recipient, Addendum A),
  same subject, body, template choice and attachments as before the move.
- **Terminal failure** (retries exhausted) appears as a `'Delivery failed'` row in the flow's log
  table with its "Error info" button, host and last code but no URL path or recipients.
- **Large body.** A plan above 256 KB goes through S3 and arrives intact (a 3 MB body, the dev
  max); the object is gone after the workflow ends. Force it inline and watch Temporal reject it.
- **Consolidated callback** failing leaves `flow_execution_status` at `completed` and sends no
  `success:false` post.

## Done when

Email and callback delivery run as worker activities with the D-A9-2 per-channel policies, started
from `OutputDeliveryService` without the caller waiting; the inline block in `flux.service.ts` is
gone; the dedup keys keep their names, formats and TTLs under the D-A9-6 protocol, proven both ways;
each email path matches its own before; a terminal failure is visible in the run log; the
consolidated callback is covered per D-A9-3; every callback carries the D-A9-8 header; the egress
guard ships in `report` with Q2/Q6 recorded; and each D-A9-4 defect is pinned by a test and filed.

Of PLAN §3.4 (written for node types), the points that apply: the worker module and its wiring
(point 1, with `deliver-run-outputs.workflow.ts` in place of a `process-single-node` case), the
inline twin deleted (4), errors classified through `runNodeActivity` (5), negative controls (6) and
docs (7). Points 2 and 3 — the dispatch registry and the single-node entry path — do not apply:
delivery is not a node type and has no single-node run.

## Pull requests and published docs

| Repo | PR | Branch → base |
|---|---|---|
| back | [Flux-Prompt #2006](https://github.com/enhancedai-com/Flux-Prompt/pull/2006) | `feat/868m0vmux` → `production` |
| worker | [Flux-Prompt-Worker #111](https://github.com/enhancedai-com/Flux-Prompt-Worker/pull/111) | `feat/868m0vmux` → `main` |
| front | [Flux-Prompt-Frontend #2202](https://github.com/enhancedai-com/Flux-Prompt-Frontend/pull/2202) | `feat/868m0vmux` → `production` |
| spec (this file) | [Workflow #14](https://github.com/enhancedai-com/Workflow/pull/14) | `docs/868m0vmux-a9-spec` → `main` |
| docs | [docs #42](https://github.com/enhancedai-com/docs/pull/42) | `docs/868m0vmux-worker-delivery-env` → `main` |
| skill fix | [Workflow #15](https://github.com/enhancedai-com/Workflow/pull/15), `env-vars-sync`: `docs.json` is LF | `fix/868m0vmux-env-vars-sync-skill` → `workspace` |

Pages docs #42 adds or changes (Mintlify, `docs/`):

- `worker/activities/deliver-run-outputs.mdx`: new; the delivery behaviour this spec decides
- `main-api/specific-features/async-flow-execution.mdx`: how the api-v2 callback is delivered
- `main-api/specific-features/integrations/microsoft.mdx`: disconnect only on a revoked grant (A9.6)
- `main-api/specific-features/integrations/google.mdx`: Gmail to every recipient (Addendum A)
- `main-api/specific-features/execution-limits.mdx`: a ceiling stop sends no output-node delivery (A9.4)
- `worker/environment-variables.mdx` and `worker/pt-br/environment-variables.mdx`: `EMAIL_*`, `EGRESS_POLICY_MODE`

ClickUp: [A9](https://app.clickup.com/t/868m0vmux) and its subtasks A9.1–A9.6, listed in "Follow-ups found during A9".

## Files

`back/src/app-api/flux/flux.service.ts` (`:5329–5599`, the block) · `back/src/app-api/flux/output-delivery/` (new) ·
`back/src/jobs/apiV2Job/apiV2Job.processor.ts` · `back/src/temporal/worker.controller.ts` (`/worker/delivery-outcome`) ·
`back/src/app-api/flow_logs/` (the `'Delivery failed'` row) · `front/src/components/nodes/FlowGlobalNode.tsx` (one condition) ·
`back/src/app-api/mail/` and `back/src/app-api/microsoft/` (read for parity, kept for the front's direct send and inbound mail; `mail.service.ts` `sendGmailEmail` changed by Addendum A) ·
`worker/src/modules/delivery/` (new) · `worker/src/modules/egress/egress-policy.ts` (new) ·
`worker/src/modules/temporal/` (`activities.service.ts`, `worker.service.ts`, `workflows/configs.ts`, `workflows/deliver-run-outputs.workflow.ts`, `workflows/index.ts`, `temporal.module.ts`) ·
`worker/src/env.ts` · `.specs/.../TASK-S6-SSRF-POLICY.md`
