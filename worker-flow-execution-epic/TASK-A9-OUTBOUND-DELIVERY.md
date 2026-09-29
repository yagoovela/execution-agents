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
> 2. **Callbacks are not deduplicated at all** — neither the node callback nor the api-v2
>    consolidated one. Only email has keys. The user case below no longer assumes otherwise.
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
(`flux/scheduler.ts:23`). Stored data agrees: dev has 0 edges leaving an output node (Q7).

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
- Ordering between the node callback and the consolidated callback: see D-A9-3.

### D-A9-2 — per-channel retry policies

Chosen per channel, not inherited from `COMMON`. Values are the starting point; Q3 confirms or
changes them before code review. Today's node-callback and SMTP failure rates exist only in
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

**Ordering, resolved by Q5.** Today a caller that has both sees the node callback first
(`apiV2Job.processor.ts:137` then `:176`); nothing documents or tests that order. If Q5 shows no
api-v2 run with both, the consolidated callback is its own workflow started by the processor. If it
shows any, the consolidated callback runs as the last step of the same delivery workflow, after the
node deliveries settle, so the observed order is kept.

### D-A9-4 — existing defects are preserved and filed, not fixed here

**Decided by the user 2026-09-29.** This task moves and retries; it does not redesign. Each defect
below keeps its current behaviour, gets a parity test that pins it, and becomes its own ClickUp bug
(drafted in the PR, created only after the user confirms). Q1 counts how many nodes each touches.

1. Gmail sends only to the first recipient (`mail.service.ts:746`) — the others are silently dropped.
2. The node callback ignores `enabledCallbackUrl` (dev: 4 of 6 callbacks fire with it off) and
   `callbackUrlData`, both of which the MCP metadata says gate it (`node-type-metadata.ts:566–609`).
3. The node callback fires in batch runs; `sendEmail=false` gates only email.
4. Delivery is not gated on cancel, budget stop or node error; a cancelled run still sends.
5. Attachments are downloaded even when email is off.
6. The same child output node run twice in one parent run: the second email is suppressed (shared
   `runLogProcessId`).
7. A Microsoft token failure deletes the user's integration. A9 marks it non-retryable so a retry
   cannot trigger it a second time; the deletion itself is the separate bug.

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
| Redirects keep being followed as today, and every hop goes through `safeLookup` | S6: "re-check on redirect" |
| `proxy: false` on these clients, so an env proxy cannot bypass the lookup | neutral |
| Attachment fetch gets a 30 s timeout and a 25 MB cap (the Gmail/SMTP message ceiling — nothing that sends today is refused by it) | neutral; not a policy |
| A refusal is `ApplicationFailure.nonRetryable`, type `EgressRefused`, host + reason in the run log, no payload. A DNS failure is retryable, never a refusal | S6: "unresolvable is unverifiable, not blocked" |
| `EGRESS_POLICY_MODE=off\|report\|enforce`, default **`report`**: log `egress_would_refuse` and let the request through. `enforce` only after Q2 + Q6 show zero "refused although it works" and one week in `report` with none | S6 + PLAN §3.3.2: measure, then report-only, then enforce |
| No per-org allowlist in A9, but the optional `allow` hook is where S6 plugs it in without touching call sites | S6 owns the allowlist |

This is recorded in `TASK-S6-SSRF-POLICY.md` as the adopted first cut, so S6 extends this module
(allowlist, apiCaller's undici dispatcher, back's `/downloader`) instead of writing a second one.
**Dev, 2026-09-29:** every stored callback and attachment URL resolves to public addresses — zero
would-be refusals (Q2, Q6). One stored attachment is a `file://` URL, which fails today too.

### D-A9-6 — the dedup protocol: same keys, claim–send–confirm

The key names, formats and TTLs stay exactly as they are. What changes is the order of operations,
because claim-before-send and never-release is what made retry unsafe:

1. **Claim** `email-sent:…` with `SET <key> pending EX 300 NX` (300 s > the email
   `startToCloseTimeout`). If the key exists: `sent` or `1` (a value written by the old code) →
   suppressed, the activity succeeds without sending; `pending` → another attempt is in flight →
   retryable `DeliveryInFlight`.
2. **Claim** `email-content:…` with `SET <key> 1 EX 90 NX` as today; if it exists → suppressed.
3. **Send.**
4. **Confirm** on success: `SET email-sent:… sent EX 86400`. The content key keeps its 90 s.
5. **Release** on failure: `DEL` both keys, then rethrow, so the next attempt can claim.

The residual window: a worker dying between a successful send and the confirm leaves `pending`,
which expires after 300 s and lets the retry send again. That is at-least-once, not exactly-once, and
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
`error_message` naming the channel, the destination host (never the full URL or recipients) and the
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
deliveries today; the email keys keep suppressing the second email exactly as now). The processor
starts the consolidated callback per D-A9-3. `validateCallbackUrl` is unchanged.

**Worker.** `modules/delivery/` (`delivery.module.ts`, `email-delivery.service.ts`,
`callback-delivery.service.ts`, `delivery-dedup.service.ts`, specs), `modules/egress/egress-policy.ts`,
`workflows/deliver-run-outputs.workflow.ts` exported from `workflows/index.ts`, activities in
`activities.service.ts` wrapped in `runNodeActivity`, bound in `worker.service.ts`, and proxied in
`configs.ts` with the D-A9-2 policies. Gmail and Microsoft send with tokens from the existing broker;
SMTP gets the `EMAIL_*` variables; Redis dedup uses a plain ioredis client on the existing
`REDIS_HOST`/`REDIS_PORT`, which must be the same Redis as back's (a deploy check, not assumed).

**Payload.** The plan carries URLs and ids, not fetched attachment bytes; attachments are fetched
inside the email activity. The body cannot always go inline: on dev the output text has p99 57 KB
but a max of 3 MB, with 6 nodes above 256 KB and 1 above 1 MB (Q8), and Temporal's self-hosted
default rejects a payload above 2 MB. So a plan whose serialised size is at most 256 KB (the claim
check's threshold, `claim-check.ts:3–5`) goes inline; a larger one is written by back to S3 at
`delivery-plans/${workflowId}.json` with the existing `AwsService.uploadFile`, the workflow input
carries only the key, the worker reads it with its existing S3 client and credentials, and the last
activity deletes it. The node-execution claim check is not reused: `/worker/get-payload` needs a
matching `node_executions` row (`claim-check-authz.service.ts:136–157`), dev's output-node rows
carry no `output`/`outputData` (119 of 119 empty), and inbound-mail runs use a non-UUID process id
(`pop3-processed:…`, `mail.service.ts:379–382`) that the uuid `execId` column rejects.

**Capacity, resolved by Q4.** Delivery activities share the 10 slots on `enhanced-ai-queue`; an
attempt holds one for at most 15 s (callback) or 2 min (email), and backoff waits hold none. If Q4's
p99 deliveries per minute keep the average slot use under one, they share the queue; if not, they
get their own task queue on the same worker process.

**Env.** Worker: `EMAIL_SERVICE`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`,
`EMAIL_FROM_ADDRESS`, `EGRESS_POLICY_MODE`. The worker task definitions reference the existing
`EMAIL_*_PROD` SSM parameters. Run `env-vars-sync`.

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
2026-09-29. Prod is run by a human; results are recorded here before code review.

| # | File | Answers | Dev | Prod |
|---|---|---|---|---|
| Q1 | `a9-q1-output-node-config.sql` | channel split; how many nodes each D-A9-4 defect touches | 1040 output nodes; email on 126 (SMTP 116, Gmail 9 — 2 multi-recipient —, Microsoft 1); callbacks 6 (4 with the flag off) | pending |
| Q2 | `a9-q2-egress-classification.sql` | D-A9-5 would-be refusals | 0 | pending |
| Q3 | `a9-q3-apiv2-callback-outcomes.sql` | lost consolidated callbacks and their error kinds (D-A9-2, D-A9-3) | no callbacks in dev | pending |
| Q4 | `a9-q4-delivery-run-volume.sql` | delivering runs per entry point; peak per minute (capacity) | 0 runs in 30 d | pending |
| Q5 | `a9-q5-callback-overlap.sql` | D-A9-3 ordering | 0 | pending |
| Q6 | `a9-q6-distinct-hosts.sql` + DNS | D-A9-5 on public-looking names | 3 hosts, all public | pending |
| Q7 | `a9-q7-output-node-outgoing-edges.sql` | nothing waits on delivery | 0 | pending |
| Q8 | `a9-q8-output-body-size.sql` | whether the body fits inline in the workflow input | p99 57 KB, max 3 MB; 6 over 256 KB, 1 over 1 MB — by reference above 256 KB | pending |
| M8 | ~~Datadog counts of `webhook_error` / `MailService.sendMail failed`~~ | real failure rates behind D-A9-2 | — | **dropped 2026-09-29** — no Datadog access; replaced by the first week of `Delivery failed` rows |

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
- **Email parity, per path.** SMTP, Gmail and Microsoft each: same recipients (Gmail still first-only),
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

## Files

`back/src/app-api/flux/flux.service.ts` (`:5329–5599`, the block) · `back/src/app-api/flux/output-delivery/` (new) ·
`back/src/jobs/apiV2Job/apiV2Job.processor.ts` · `back/src/temporal/worker.controller.ts` (`/worker/delivery-outcome`) ·
`back/src/app-api/flow_logs/` (the `'Delivery failed'` row) · `front/src/components/nodes/FlowGlobalNode.tsx` (one condition) ·
`back/src/app-api/mail/` and `back/src/app-api/microsoft/` (read for parity, kept for the front's direct send and inbound mail) ·
`worker/src/modules/delivery/` (new) · `worker/src/modules/egress/egress-policy.ts` (new) ·
`worker/src/modules/temporal/` (`activities.service.ts`, `worker.service.ts`, `workflows/configs.ts`, `workflows/deliver-run-outputs.workflow.ts`, `workflows/index.ts`, `temporal.module.ts`) ·
`worker/src/env.ts` · `.specs/.../TASK-S6-SSRF-POLICY.md`
