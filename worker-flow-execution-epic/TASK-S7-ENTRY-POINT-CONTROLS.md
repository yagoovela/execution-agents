# S7 — Authenticate and rate-limit the entry points

**Goal:** a run can only be created by someone entitled to create it, and no caller can create an
unlimited number of them.

**Three of the four ways to start a run are effectively unauthenticated** — the webhook route, the
email trigger for public flows, and the email trigger for private flows via a forgeable `From`.
None of the four is rate limited. Every other ceiling in this epic is downstream of admission.

**Depends on:** nothing. **Ship the first half immediately** — it is a live, unauthenticated spend
vector, not a scaling concern. **Severity:** critical (review §9.1, §9.2).

## Part 1 — the webhook entry point (ship first, on its own)

`POST /flux/api-v2-webhook` is `@Public()` (`flux.controller.ts:340–341`), so it opts out of the
global auth guard, and it resolves the flow like this:

```
where: [ { id: query.flowId }, { id: query.flowId, public: true } ]
```

The first branch of the OR has **no `public` condition**, which makes the second dead: any flow
matches, public or private. The rest of the handler contains no secret, no token and no ownership
check — only `if (!flow)`.

**Anyone who knows a flow id can execute that flow and charge its owner.** The only barrier is that
the id is a UUID, and flow ids travel through published interfaces, chatbot routes, shared links
and the MCP surface.

**Scope.** A per-flow webhook secret, verified before anything else runs; the `public` predicate
corrected so the two branches mean different things; and a decision, written down, about what
`public: true` is supposed to permit here. If public flows are meant to be webhook-triggerable by
anyone, say so explicitly and cap them under Part 2 — do not leave it as an artefact of a broken
`where`.

**Migration matters more than the fix.** Existing integrations call this URL today. Ship the secret
as optional with a deprecation window and a metric counting unauthenticated calls per flow, then
enforce. Turning it on cold breaks every customer webhook silently, and the failure looks like
"my automation stopped" rather than "my webhook is unauthenticated".

## Part 2 — rate limiting (all entry points)

There is no `ThrottlerModule`, no `@Throttle` and no `ThrottlerGuard` anywhere in `back/src`. Every
run-creating route accepts unlimited requests: `/flux/api-v2` (API key),
`/flux/api-v2-webhook` (public), `/flux/batch-process`, `/flux/execute-from-canvas`.

The Bull processor's single concurrency throttles **execution**, not **admission** — the queue
still grows, and rows, logs and dedup keys are written on the way in.

**Scope.** Limits keyed by the thing that pays: API key, organisation, and flow for the webhook
route. Not by IP, which is meaningless for server-to-server callers.

**Assumption to confirm — reject with `429` and `Retry-After`, rather than queueing.** Admission is
the one place where rejecting is right: queueing an unbounded inbound flood just moves it.
Note the deliberate contrast with `S3`, where excess *tenant* runs are queued — there the caller is
already entitled to the work.

## Part 3 — the email trigger (ship with part 1)

Agents are also started by email. `mail.service.ts` resolves the flow from the **local part of the
recipient address** — the format the service itself advertises is `uuid@upload.fluxprompt.com`
(`:434`) — then feeds `From`, `Subject`, the body and any attachments into the flow's
`varInputNode` and enqueues a run (`:503–556`).

Its authorisation is the weakest of the four entry points (`:453–487`):

- **Public flow → no sender check at all.** Anyone who emails the address runs the flow, charged to
  the owner, **and controls the prompt** — which, in a flow containing a push node or an
  integration, means driving side effects with the owner's credentials.
- **Private flow → the sender's `From` header** is matched against a user and compared to
  `flow.user`. Greps for `dkim`, `spf`, `dmarc` and `authentication-results` in `app-api/mail/`
  return nothing, so nothing verifies the message came from the address it claims. The check is a
  request for the attacker to type the owner's email address — which is not secret.

**Scope.**
- Verify the sender: DKIM/SPF/DMARC at the boundary, **or** move the secret into the address
  (`<flowId>+<token>@…`) so possession of the address is the credential. Either is defensible;
  trusting `From` is not.
- Decide, and write down, what a **public** flow's email trigger is allowed to do. "Public" should
  probably mean readable, not "anyone may spend the owner's tokens and drive their integrations".
  If public email triggers stay, cap them explicitly under part 2 and treat their input as
  untrusted for any node with side effects.
- Keep the existing bounce-back replies — telling a sender "flow not found" or "unauthorized" is
  good behaviour, and it is already there.

**Assumption to confirm — the address-token option is preferred over DKIM.** It is enforceable in
this codebase today, does not depend on the mail provider's headers, and rotates per flow. DKIM
verification is the more standard answer and can be added later without undoing it.

## Verification

- **Negative control (required), Part 3.** Send a message to a private flow's address with the
  owner's email forged in `From`, and confirm the flow runs and is charged. Then confirm it is
  refused. Do the same for a public flow with body content that would drive an integration — that
  demonstration is what settles the "what may a public trigger do" decision.
- **Negative control (required), Part 1.** From an unauthenticated client, trigger a **private**
  flow by id and confirm it runs and charges the owner. That demonstration is the justification for
  the whole task. Then confirm it is refused, and that a correctly-signed call still works.
- **Negative control, Part 2.** Exceed the limit and confirm a `429`; then confirm the queue depth
  and the row count stop growing — the point is admission, so measuring the refusal is not enough.
- **Measure before refusing** (PLAN §3.3.2). Both halves refuse traffic, and this is customer
  traffic. Count real calls per flow and per key over a full cycle, set the limits above the
  observed peak with margin, and run in **report-only** mode before enforcing. Any legitimate
  caller refused is a production incident, not a test failure.
- Confirm the deprecation metric actually names the flows still calling unauthenticated, so someone
  can contact their owners.

## Done when

The webhook route authenticates, the `public` predicate means what it says, every run-creating
route is limited by the paying entity, both ran in report-only mode against real traffic first,
and no legitimate caller is refused.

## Files

`back/src/app-api/flux/flux.controller.ts:158–160, 221–222, 340–362, 513–514` ·
`back/src/app-api/mail/mail.service.ts:132, 314, 434, 453–487, 503–556` ·
`back/src/app-auth/guards/` · new throttler configuration · `env-vars-sync`
