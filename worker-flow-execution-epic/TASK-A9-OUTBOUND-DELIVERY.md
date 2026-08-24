# A9 — Outbound delivery as activities

**Goal:** the emails and HTTP callbacks a run sends stop being fire-and-forget, and start being
retried.

**Depends on:** A1. Can ship any time after it. **Source:** review §11.1.

## Why

The block at the end of every run (`flux.service.ts:4907–5200`, ~300 lines) sends emails through
three paths — `mailService.sendMail`, `mailService.sendGmailEmail`,
`microsoftMailService.sendMail` — and fires HTTP callbacks with `axios.post`, each wrapped in a
`catch`. **Nothing is retried.** A customer's webhook endpoint being down for thirty seconds means
the notification is lost, with a log line as the only trace.

This is the cleanest activity candidate left in the codebase: pure external I/O, no engine state,
and the hard part is already done. **Idempotency exists**: the Redis dedup keys
(`flux.service.ts:5030–5044`) are a run-scoped `SET … EX 86400 NX` plus a shorter content hash,
built exactly so a repeated attempt does not double-send. Retry with backoff is the missing half,
and it is what Temporal provides.

## Scope

**In.** One delivery activity per channel — email and callback — with retry policies chosen per
channel rather than inherited. A callback to a customer endpoint should retry generously; an email
should not retry into a rate-limited SMTP relay.

**In.** The dedup keys move with the code, unchanged. They are the reason retry is safe, so they are
not an implementation detail to re-derive worker-side — port them as they are.

**In.** Extract the block while moving it. The review's source material calls it a candidate for an
`OutputDeliveryService`; 300 lines of inline delivery is the reason nobody has added retry in the
first place.

**In.** A failure surface. Today a lost callback is invisible to the customer. With retries there is
a terminal state, and it should be visible — in the run log at minimum.

**Out.** Changing payload shapes, recipients, or when delivery is triggered. This moves and retries;
it does not redesign.

## Verification

- **Negative control (required).** Point a callback at an endpoint that returns 500 twice then 200,
  and confirm the delivery succeeds after retry. Then break the retry policy and confirm the test
  fails — a retry that is configured but not exercised is not a retry.
- **Double-send.** Force the activity to run twice for the same run and node, and confirm the dedup
  key suppresses the second. Then delete the key and confirm it double-sends. That second half is
  what proves the key is load-bearing rather than decorative — and it is a customer-visible failure,
  so it deserves the proof.
- Email parity across all three paths: same recipients, same attachments, same body, before and
  after.
- Confirm a terminal delivery failure appears in the run log rather than only in Winston.

## Files

`back/src/app-api/flux/flux.service.ts:4907–5200, 5030–5075, 5164–5195` ·
`back/src/app-api/mail/` · `back/src/app-api/microsoft/` · new worker delivery module · the A1 registry
