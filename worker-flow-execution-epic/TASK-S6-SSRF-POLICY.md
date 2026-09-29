# S6 — An egress policy for user-controlled URLs

**Goal:** decide what a node is allowed to fetch, **before** moving the code that fetches it into a
host with more privileges.

**Depends on:** nothing. **Must be decided as part of** A6 and A8, not after them.
**Severity:** high (review §3.2).

## Why the timing matters more than the finding

`/downloader?url=` takes a user URL (`downloader.controller.ts`), and the scraper, api-caller and
crawling paths take user URLs too. Searching those modules for private-range or metadata blocking —
`127.0.0.1`, `169.254`, `localhost`, `isPrivate` — returns **nothing**. A node pointing at the cloud
metadata endpoint or an internal hostname is the textbook case.

This is **pre-existing**; the epic did not create it. But the epic **moves these callers into the
worker**, and the worker sits in a different network position while holding the database password
and the integrations encryption key. Whether the move improves or worsens the exposure depends
entirely on the worker's subnet and instance role — and today the tasks that do the moving
(`A6`, `A8`) say nothing about it.

Fetchers that this epic relocates: `webCrawling`, `webAmazon`, `secApiNode`, `usCensusNode`,
`documentSummarizer`, `fileSave` (via `/downloader`), plus `apiCaller`, already in the worker.

## Scope

**In.** One egress policy, applied at the fetch layer both repos share, not per node:
- Resolve the hostname **and check the resolved address**, not the string. A string check is
  defeated by a DNS name that resolves to a private address.
- Block loopback, link-local (including `169.254.169.254`), private ranges and unique-local
  addresses by default.
- Re-check on redirect. A permitted URL that redirects to metadata is the standard bypass.

**In.** A decision on the worker's network position, written down: which subnet, which instance
role, what it can reach. If the worker can reach less than the API, moving these fetchers is a
security **improvement** and should be stated as one. If it can reach more, the move needs
compensating controls before it ships.

**In.** An allowlist escape hatch per organisation for legitimate internal endpoints, because some
customer will have one and a policy with no exception path gets disabled wholesale.

**Out.** Auditing every existing customer URL. That is the measurement below, not a remediation
project.

## Scope decision — left to the implementer (D25)

How wide the first cut is — the full resolved-address deny-list with redirect re-checks above, or a
narrower first step — is **the decision of whoever picks up this task**, made at the start and
recorded in this file before implementation. The requester's stated preference, for the record:
begin with limits on URL *consumption* (what a node may fetch, how much, how often) and add the
address blocklist as a second step. Whichever cut ships first, the three properties above remain the
target, and PLAN §3.3.2 applies to each step separately: measure against stored URLs, drive false
refusals to zero, then enforce.

**Added 2026-09-29 by A9 — a module to extend, not a decision taken for you.** A9 moves the delivery
path's outbound fetches (node callback, api-v2 consolidated callback, email attachment downloads)
into the worker and ships a guard for those call sites only: `worker/src/modules/egress/egress-policy.ts`
(`assertEgressAllowed`, `safeLookup`, `EGRESS_DENY_RANGES`), checking the resolved and pinned
address on every hop, behind `EGRESS_POLICY_MODE=off|report|enforce` defaulting to `report`, with an
optional `allow` hook and no allowlist. The full rule set and its relation to this task are in
`TASK-A9-OUTBOUND-DELIVERY.md` D-A9-5. It does not settle D25 for this task's call sites
(downloader, scraper, api_call, apiCaller), which A9 does not touch: whoever picks up S6 still
decides the first cut, and extends this module — adding the allowlist and apiCaller's undici
dispatcher — instead of writing a second one. S6 names neither the delivery callbacks nor the mail
attachment fetches; A9 adds that coverage. Out of both tasks' scope and flagged separately: back's
`/proxy?url=` route (`src/main.ts:135–180`, http-proxy-middleware to any origin).

## Verification

- **Negative control (required).** Point an `apiCaller` node at `169.254.169.254` and confirm it
  currently returns metadata. That is the finding; demonstrate it in a controlled environment
  before fixing it, and keep the test.
- Redirect bypass: a permitted host that 302s to a blocked address must be refused at the redirect.
- **Measure before refusing** (PLAN §3.3.2) — this rule refuses network traffic, which is the most
  disruptive kind of refusal. Sample the real URLs stored in node configurations, classify each as
  *would still work* or *would now be blocked*, and drive the second to zero before enabling.
  Anything unresolvable is *unverifiable*, not *blocked*.
- Enable in report-only mode first: log what would be blocked, for a full cycle, before enforcing.

## Done when

Egress is policy-controlled at the shared fetch layer, redirects are re-checked, the worker's
network position is documented, no legitimate stored URL is blocked, and the policy ran in
report-only mode before enforcement.

## Files

`back/src/app-api/downloader/downloader.controller.ts` (`@Query('url')`) · `back/src/app-api/scraper/` ·
`back/src/app-api/api_call/` · the worker's HTTP layer · infra network/subnet definitions
