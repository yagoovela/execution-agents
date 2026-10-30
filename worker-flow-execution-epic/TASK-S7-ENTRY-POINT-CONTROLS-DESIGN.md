# TASK-S7 — Entry-Point Controls — Design

Companion to [TASK-S7-ENTRY-POINT-CONTROLS.md](./TASK-S7-ENTRY-POINT-CONTROLS.md).
Scope: Parts 1 and 3 only (Wave 0 card). Part 2 (rate limiting) is a separate Wave 1 card and is out of scope here.

## Goal restated

A run can only be created by someone entitled to create it. Close the two live unauthenticated
spend vectors this card owns: the anonymous webhook route, and the email trigger that trusts
a forgeable `From` header (or, for public flows, trusts nothing at all).

## Decisions locked in this design

| Ref | Decision | Rationale |
|---|---|---|
| Part 1 | **Retire `POST /flux/api-v2-webhook`** with `410 Gone` in a single release. Frontend is updated in the same release to guide callers to `POST /flux/api-v2` with `callback_url` and status polling at `GET /flux/executions/:id`. | The replacement path already exists, is already authenticated by API key, and already supports the async pattern webhook callers actually want. Designing a per-flow secret + rotation UI + deprecation metric for a route we don't need is more work than the migration itself. Trade-off: violates the parent spec's "no legitimate caller is refused" AC in the strict sense — the frontend guidance is what carries the migration burden. |
| Part 3 | **Address-token** — the trigger email address becomes `<flowId>+<token>@upload.fluxprompt.com`. Possession of the address is the credential. Applies to public and private flows equally; the old `From`-header check is removed. | Enforceable in this codebase today; independent of the mail provider's headers; rotates per flow. DKIM/SPF/DMARC can be added later without undoing this (as the parent spec notes). |
| Part 3 legacy | **Old address `<flowId>@upload.fluxprompt.com` is rejected on cutover** with a bounce reply telling the sender where to find the new address. | Same aggressive-cutover choice as Part 1, applied consistently. |
| Part 3 public | **Public flows keep email trigger** with address-token gating (option 1). "Public" means readable, not "anyone may spend the owner's tokens." | The token is the credential regardless of whether the flow is public. |

Deferred (out of this card): rate limiting (Part 2, Wave 1); DKIM/SPF/DMARC verification as a
second-factor on top of address-token; audit log entry for token rotations.

## Design — Part 1: retire `/api-v2-webhook`

### Backend

**`back/src/app-api/flux/flux.controller.ts`** — replace the `apiWebhook` handler body
(currently lines 471–572) with a `410 Gone` response:

```ts
@Post('/api-v2-webhook')
async apiWebhook(@Res() res: Response, @Req() req: Request, @Query() query: any) {
  this.loggerService.log({
    message: 'Retired route hit: /flux/api-v2-webhook',
    metadata: {
      other: {
        flowId: query?.flowId,
        ip: req.ip,
        userAgent: req.get('user-agent'),
      },
    },
  });
  return res.status(HttpStatus.GONE).json({
    status: 'error',
    data: {
      message:
        'This endpoint has been retired. Use POST /flux/api-v2 with callback_url and poll GET /flux/executions/:id for status.',
    },
  });
}
```

Delete `@Public()` from the handler — it's no longer necessary because the handler does no
work. Remove the unused imports if no other handler in the file references them (`Flow`,
`ProductService` reference, etc. remain used elsewhere — only trim what's truly unused).

**`back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts`** — delete tests that
exercised the old `apiWebhook` behavior; add one test asserting the route returns 410.

### Frontend

**Flow settings — the section that today displays the webhook URL** — replace with a
"Trigger this flow via API" block that shows two copy-to-clipboard code snippets:

```
POST https://<api-host>/flux/api-v2?flowId=<flow-id>&callback_url=<your-url>
Header: api-key: FLUX_API.xxxxxxxx
Body:   { "variableInputs": [ ... ] }
```

```
GET https://<api-host>/flux/executions/<executionId>
Header: api-key: FLUX_API.xxxxxxxx
```

Copy for both must state that `callback_url` is optional; if omitted, the API returns
`executionId` and the caller polls the status endpoint until `status: completed` or `error`.

Delete any wizard step that assumed the old webhook URL exists.

### Docs

**`docs/`** (Mintlify) — remove the `/api-v2-webhook` page. Extend the `/api-v2` page with
the callback pattern (`callback_url` param, status polling, response shapes for
`in_progress` / `completed` / `error`).

## Design — Part 3: address-token for the email trigger

### Schema

New migration in `back/src/database/migrations/`:

1. `ALTER TABLE flows ADD COLUMN email_trigger_token varchar(64) NULL`
2. Backfill: for each row where `email_trigger_token IS NULL`, set it to a freshly generated
   token (see helper below). This runs in the same migration, in batches if needed for large
   tables.
3. `ALTER TABLE flows ALTER COLUMN email_trigger_token SET NOT NULL`.
4. Optional (defense-in-depth): `CREATE INDEX flows_email_trigger_token_idx ON flows (email_trigger_token)` — the lookup key is `(id, token)` so uniqueness is implicit, but the index speeds parsing failures.

The migration follows the project's naming convention: `<timestamp>-AddFlowEmailTriggerToken.ts`.

### Entity

**`back/src/entities/flow.entity.ts`** — add:

```ts
@Column({ type: 'varchar', length: 64 })
@Expose()
emailTriggerToken: string;
```

Not exposed on public-facing DTOs that go to non-owners; the owner needs it to construct the
address in the UI.

### Token helper

**`back/src/utils/generate-email-trigger-token.ts`** (new):

```ts
import { randomBytes } from 'crypto';

export function generateEmailTriggerToken(): string {
  return randomBytes(32).toString('base64url');
}
```

32 bytes → 43 base64url chars → 256 bits of entropy. Well above the "not guessable" bar.

### Flow service

**`back/src/app-api/folw/flow.service.ts`** — in the flow-creation path, populate
`emailTriggerToken` with `generateEmailTriggerToken()`. If flows are created in more than one
place, thread it through a shared helper so every creation path gets the token.

New endpoint (route lives on whichever controller currently owns per-flow settings — likely
`FlowController`, not `FluxController`):

```
POST /flow/:id/rotate-email-trigger-token
Guard: JwtAuthGuard + ownership check (must be flow owner or space admin)
Body:  (empty)
Response: { emailTriggerAddress: "<flowId>+<newToken>@upload.fluxprompt.com" }
```

The response returns the full new address so the frontend can display it immediately.

### MailService

**`back/src/app-api/mail/mail.service.ts`** — replace the address-parsing block
(lines 355–405) and delete the `From` check block (lines 454–500).

New parsing logic:

```ts
const ADDRESS_PATTERN =
  /^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\+([A-Za-z0-9_-]{20,})@/i;

const match = ADDRESS_PATTERN.exec(recipientEmail);
if (!match) {
  await this.sendMail(
    [parsedEmail.from.value[0].address],
    'Invalid trigger address!',
    'This address is no longer accepted. Get your new trigger address from the flow settings page.',
  );
  return;
}
const [, flowId, providedToken] = match;
```

Flow lookup + token check:

```ts
const flow = await this.flowService.getFlowWithNodesAndEdges(flowId, ['user']);
if (!flow) {
  await this.sendMail([parsedEmail.from.value[0].address], 'Flow not found!');
  return;
}
if (!timingSafeEqualStrings(flow.emailTriggerToken, providedToken)) {
  await this.sendMail(
    [parsedEmail.from.value[0].address],
    'Invalid trigger address!',
    'The token in this address does not match. Get your new trigger address from the flow settings page.',
  );
  return;
}
```

`timingSafeEqualStrings` is a small wrapper around `crypto.timingSafeEqual` that returns
`false` on length mismatch instead of throwing. Lives next to the token helper.

The old `From` check block is deleted entirely — the address IS the credential now, and
`flow.public` no longer changes the auth path.

Everything downstream of the check (uploading attachments, building `variableInputs`,
enqueuing the run) stays the same.

The `Received` and `Delivered-To` fallback header parsing stays — it's still useful when the
`To:` field is dropped by an intermediate mail hop.

### Frontend

**Flow settings — email trigger section** — replace whatever is shown today with:

```
Email trigger address
  [ <flowId>+<token>@upload.fluxprompt.com ]  [Copy]

  This address is a credential. Anyone with it can trigger this flow at
  your expense. Keep it in your Zapier/Make/forwarding config only.

  [Rotate address]
```

Rotate button opens a confirm modal:

> Rotating this address will immediately invalidate the current one. Any integration
> (Zapier, Make, Gmail forwarding rule) still using the old address will stop working.
> Continue?

On confirm → `POST /flow/:id/rotate-email-trigger-token` → update the displayed address.

### Docs

**`docs/`** (Mintlify) — update the email trigger doc to show the new address format,
explain that the address is a credential, and document the rotate action.

## Verification

Two negative controls, both required.

**Part 1**
- On main today: `curl -X POST '<host>/flux/api-v2-webhook?flowId=<private-flow-id>' -d '{}'`
  returns 200 and enqueues a run charged to the flow owner.
- After this change: same call returns `410 Gone` with the migration message. A correctly
  authenticated `POST /flux/api-v2?flowId=<same-flow>` continues to work end-to-end
  (returns `executionId`, status endpoint reports `completed` when done).

**Part 3**
- On main today: send an email to `<flowId>@upload.fluxprompt.com` with the owner's email
  address typed into `From:` — the flow runs and the owner is charged.
- After this change:
  - Email to `<flowId>@upload.fluxprompt.com` (old format) → bounce reply, no run.
  - Email to `<flowId>+<wrong-token>@upload.fluxprompt.com` → bounce reply, no run.
  - Email to `<flowId>+<correct-token>@upload.fluxprompt.com` → run enqueues, owner is
    charged. Repeat with the owner's email forged in `From:` and confirm behavior is
    identical (the `From` check is gone; the token is what matters).
  - Same three cases for a public flow — behavior identical to a private flow.

## Rollout order

Single release, back and front together:

1. Migration runs (adds column + backfills tokens + sets NOT NULL).
2. Backend starts serving new `MailService` behavior and returns 410 from `/api-v2-webhook`.
3. Frontend shows the new email address in flow settings and the "Trigger via API" block
   instead of the webhook URL.
4. Docs go out at the same time.

If back and front must deploy separately, ship frontend first (users see the guidance and
new address) then backend (starts enforcing).

Do not merge the migration ahead of the code that reads the new column, and do not ship the
code that reads the new column ahead of the backfill.

## Files touched

- `back/src/app-api/flux/flux.controller.ts` — retire `apiWebhook`
- `back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts` — update tests
- `back/src/app-api/mail/mail.service.ts` — replace address parsing, remove `From` check
- `back/src/app-api/folw/flow.service.ts` — generate token on create; add rotation method
- `back/src/app-api/folw/flow.controller.ts` (or wherever per-flow settings live) — add rotate endpoint
- `back/src/entities/flow.entity.ts` — new column
- `back/src/utils/generate-email-trigger-token.ts` (new) — helper
- `back/src/database/migrations/<timestamp>-AddFlowEmailTriggerToken.ts` (new)
- `front/` — flow settings UI (webhook section replaced with API guidance; email section replaced with token address + rotate)
- `docs/` — Mintlify pages for `/api-v2` (expanded) and email trigger (rewritten); `/api-v2-webhook` deleted

## Explicitly not in this card

- Rate limiting on any run-creating route (Part 2, separate Wave 1 card).
- DKIM/SPF/DMARC verification (future reinforcement).
- Audit log entry for token rotations.
- Rate limit or CAPTCHA on the rotation endpoint (not exposed publicly, guarded by JWT).
- Any UI to view historical usage of the old webhook route (we're cutting, not measuring).
