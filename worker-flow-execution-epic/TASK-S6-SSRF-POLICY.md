# S6 — An egress policy for user-controlled URLs

**Goal:** decide what a node is allowed to fetch, **before** moving the code that fetches it into a
host with more privileges.

**Depends on:** nothing. **Must be decided as part of** A6 and A8, not after them.
**Severity:** high (review §3.2).

## Why the timing matters more than the finding

`/downloader?url=` takes a user URL (`downloader.controller.ts:34`), and the scraper, api-caller and
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

`back/src/app-api/downloader/downloader.controller.ts:34` · `back/src/app-api/scraper/` ·
`back/src/app-api/api_call/` · the worker's HTTP layer · infra network/subnet definitions
