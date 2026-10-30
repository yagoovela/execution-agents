# TASK-S7 (Parts 1 + 3) — QA Handoff

## What was delivered

Two admission-side security changes:

1. **Route `POST /flux/api-v2-webhook` retired** — returns **410 Gone** with a message pointing callers to `/api-v2 + callback_url + /executions/:id`. Before this change, anyone with a `flowId` could trigger a private flow and charge its owner.
2. **Email trigger now requires an address-token** — the address changed from `<flowId>@upload.fluxprompt.com` to `<flowId>+<token>@upload.fluxprompt.com`. Possession of the address is the credential. The forgeable `From:` header check has been removed. A "Rotate" button is now available in the flow settings.

Also: the `webhook` field was removed from the `GET /integrations/agents` response; the frontend no longer shows the webhook toggle; the Mintlify docs page (list-agents) was updated.

## Test plan

### 1 — Retired webhook

**1.1 Negative control (what was broken)**

- On production/staging **today** (before the deploy): `curl -X POST '<host>/flux/api-v2-webhook?flowId=<any-private-flow>' -d '{}'` → confirm it returns 200 and the flow runs and charges the owner. This is the baseline for the bug.

**1.2 After deploy — cutoff**

- Same `curl` → expected: **HTTP 410 Gone**, body:
  ```json
  {"status":"error","data":{"message":"This endpoint has been retired. Use POST /flux/api-v2 with callback_url and poll GET /flux/executions/:id for status."}}
  ```
- No job enters the queue (verify with `SELECT COUNT(*) FROM node_executions WHERE "createdAt" > now() - interval '1 minute'` — this call must not appear).
- Backend log records `Retired route hit: /flux/api-v2-webhook` with `flowId`, `ip`, and `userAgent`.

**1.3 Replacement path works**

- `curl -X POST '<host>/flux/api-v2?flowId=<same-private-flow>&callback_url=https://webhook.site/<your-endpoint>' -H 'api-key: FLUX_API.xxx' -d '{"variableInputs":[...]}'`
- Returns 202 with `executionId` and `statusUrl`.
- The callback arrives at webhook.site when the run finishes.
- Polling alternative: `GET /flux/executions/<executionId>` → returns `pending` → `in_progress` → `completed` with `output`, `tokensUsed`, `totalCost`, `durationMs`.

### 2 — Email trigger with address-token

**2.1 Negative control (what was broken)**

- On prod/staging **today** (before the deploy): send an email to `<flowId>@upload.fluxprompt.com` for a **private** flow with the owner's email typed into `From:`. Confirm the flow runs and is charged. This is the baseline.
- Also: send an email to a **public** flow's address with body content that would drive an integration (push node, third-party). Confirm the integration fires with the owner's credentials.

**2.2 After deploy — cutoff**

| Scenario | Expected |
|---|---|
| Email to `<flowId>@upload.fluxprompt.com` (old format) | Flow **does not** run. Sender receives a bounce reply "Invalid trigger address!" with text "This address is no longer accepted. Get your new trigger address from the flow settings page." |
| Email to `<flowId>+<wrong-token>@upload.fluxprompt.com` | Flow **does not** run. Bounce reply "Invalid trigger address!" with text "The token in this address does not match." |
| Email to `<flowId>+<correct-token>@upload.fluxprompt.com` (private flow, `From` is the owner) | Flow runs, owner is charged. |
| Email to `<flowId>+<correct-token>@…` (private flow, `From` **forged** as the owner) | Flow runs (the address is the credential; `From` is no longer verified). Confirms the policy change is intentional. |
| Email to `<flowId>+<correct-token>@…` (private flow, `From` is a third party, **not forged**) | Flow runs the same way (same logic). |
| Email to `<flowId>+<correct-token>@…` (**public** flow) | Flow runs, owner is charged. |

**2.3 Token rotation — UI**

Frontend, on the `/agent/<flowId>/settings` page (v2) and also in the FlowGlobalNode settings modal (v1):

1. Turn on "Turn ON Email triggering".
2. Confirm the "Agent Email" field shows `<flowId>+<token>@upload.fluxprompt.com` (not just the flowId).
3. Click the Copy icon → success notification, copied text uses the format above.
4. Click the Rotate icon → confirmation modal opens with text about invalidating the current address.
5. Confirm rotation → displayed address changes (new token), success notification.
6. Send an email to the **previous** address (the one shown before the rotation) → bounce reply.
7. Send an email to the **new** address → flow runs.

**2.4 Rotation — permissions**

- User A (flow owner) calls `POST /flow/<flowId>/rotate-email-trigger-token` with their JWT → 200 with a new `emailTriggerAddress`.
- User B (not the owner, no space access) calls the same route → **403** with "You do not own this flow".
- Call for a nonexistent flow → **404**.
- No JWT → **401** (guard).

### 3 — Frontend, Triggers sections

On both versions (`/agent/<id>/settings` **and** the FlowGlobalNode modal):

- The "Turn ON Webhook" toggle is **no longer** shown.
- The "Turn ON Email triggering" toggle still works; when enabled, the address includes the token and shows Copy and Rotate buttons.
- The "Turn ON API calling" toggle shows:
  - `Agent API URL` (`/flux/api-v2?flowId=…`)
  - Api Key (with show/hide)
  - **Callback URL** label now reads "async delivery — replaces the retired webhook" and explains that it replaces the old webhook.
  - **Status URL** — new block: `GET <host>/flux/executions/{executionId}`, with an explanation of the polling pattern.
- Copy-to-clipboard works in every block.

### 4 — API `/integrations/agents` (cleanup)

- `GET /integrations/agents` with a valid API key → the `endpoints` object returns **only** `api` (and `chatbotSocket` when the flow is a chatbot). The `webhook` field is **no longer** in the response.
- Legacy third-party callers that parsed this response and used `endpoints.webhook` will now get `undefined` — this is the expected behavior.

### 5 — Regression

Things that **should not** have changed but sit on the same paths:

- **Create flow** (`POST /flow`) → works; the new flow already has `emailTriggerToken` generated in the DB.
- **Duplicate flow** → the new flow has a `emailTriggerToken` distinct from the original (it must not be copied — the `??` in the service generates a fresh one).
- **Share flow** → the shared flow has its own `emailTriggerToken` (same logic).
- **`POST /flux/api-v2`** — behavior unchanged (sync/async with callback still works).
- **Chatbot socket** — behavior unchanged.
- **Email trigger with attachments** (PDF, CSV, TXT, TSX) — should keep working: the automated attachment tests pass under the new address format.

## Automated tests that ran GREEN

| Suite | Tests |
|---|---|
| `flux.controller.api-v2-queue.spec.ts` | 6/6 |
| `generate-email-trigger-token.spec.ts` | 6/6 |
| `flow.service.rotate-email-trigger.spec.ts` | 4/4 |
| `mail.service.spec.ts` | 14/14 (includes 5 new address-token tests + 9 pre-existing tests adjusted) |
| `agent-endpoints.util.spec.ts` + `api-flows.*.spec.ts` | 80/81 (1 failing test is pre-existing drift in `toAgentJson` — unrelated to this task) |

## Out of scope (intentional)

- **Rate limiting** — Part 2 of S7, separate Wave 1 card (not in this scope).

## Repo references

- Design spec: `Workflow/.claude/tasks/worker-flow-execution-epic/TASK-S7-ENTRY-POINT-CONTROLS-DESIGN.md`
- Implementation plan (checklist with 15 tasks): `Workflow/.claude/tasks/worker-flow-execution-epic/TASK-S7-ENTRY-POINT-CONTROLS-PLAN.md`
- Canonical S7 spec (context): `Workflow/.claude/tasks/worker-flow-execution-epic/TASK-S7-ENTRY-POINT-CONTROLS.md`
