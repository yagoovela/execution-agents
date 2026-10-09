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

### D25 decision (2026-10-06)

**Cut C — four controls ship together.** The implementer, in agreement with the requester, opted
for a single wider cut instead of the two-step rollout the preference suggested, because the
controls share one call site (the fetch layer) and splitting them into two passes would duplicate
the refactor of the same six node modules.

**The four controls (originally five — see note below on dropped rate-limit):**
1. **Response size cap** enforced on the stream (aborts the connection on overflow).
2. **Request timeout** via `AbortSignal.timeout`.
3. **Deny-list on the resolved address** — resolves the hostname, checks every resolved IP against
   `127.0.0.0/8`, `169.254.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `::1/128`,
   `fc00::/7`, `fe80::/10`, and pins the connection to the IP that was checked (resolve-pin-connect,
   the task's own option D-as-mechanism).
4. **No redirects** — the HTTP clients are configured with `maxRedirects: 0`. A `3xx` response is
   returned to the node as-is (with the `Location` header) and the node author issues the next GET
   manually if intended. This is a stricter stance than the "re-check on redirect" the spec framed,
   deliberately, because the follow-up GET at the node level makes the second hop visible to the
   user rather than hidden inside the HTTP client.

**Rate-limit per `{organization, nodeType}` was removed from scope (2026-10-07).** The requester
decided a per-org rate limit is a product-level concern that belongs elsewhere (billing/quota, not
the egress policy), and that forcing a worker-level cap would surprise customers whose legitimate
use is bursty. The deny-list, size cap, timeout and no-redirect still cover the SSRF threat; the
rate-limit was the only one of the five that did not address an SSRF vector directly.

**Per-organisation allowlist was also removed from scope (2026-10-07).** The spec framed it as the
escape hatch required to keep the deny-list from being disabled wholesale the first time a
legitimate internal endpoint is refused. The requester accepted that risk for v1: no customer is
known to need an internal endpoint today, and if one appears later we revisit then — either by
reintroducing the allowlist, by punching a specific hole in the hardcoded deny-list, or by placing
that customer's worker in a dedicated subnet. The hardcoded deny-list (RFC-based private, loopback,
link-local, metadata ranges) is the only exception path that ships. If this causes real customer
pain before S6-b is resolved, the allowlist is the first thing to bring back.

**Per-organisation allowlist** stored in a new `organization_egress_allowlist` table — the required
escape hatch for legitimate internal endpoints.

**Report-only cycle (PLAN §3.3.2) was removed from scope (2026-10-07).** The requester opted to
ship directly in enforce — no `EGRESS_MODE` env var, no `egress.would_block` log event, no soft
rollout. The only mode is enforce. The negative-control test and the measurement script still
exist for pre-deploy validation; the production report-only cycle is dropped as a conscious
trade-off: we accept the risk of a legitimate customer URL being refused on first enforce in
exchange for a simpler surface. If this causes real pain, re-introducing a toggle is a small code
change (one env var + one branch).

**Scope by node (from code analysis of the current branch):**

| Node type   | URL comes from | SSRF checks  | Operational caps |
|-------------|----------------|--------------|------------------|
| `apiCaller` | user           | yes          | yes              |
| `fileSave`  | user           | yes          | yes              |
| `webCrawling` | system (ScrapingBee/OxyLabs/BuiltWith) | no | yes |
| `webAmazon` | system (OxyLabs) | no         | yes              |
| `secApiNode` | system (api.sec-api.io) | no   | yes              |
| `usCensusNode` | system (api.census.gov) | no | yes              |

Only `apiCaller` and `fileSave` connect the worker to a user-controlled URL, so the deny-list,
DNS-pin and no-redirect controls apply only to those two. The other four already connect to a known
host; they pass through `safeFetch` with `skipAddressChecks: true` so the rate-limit, size cap and
timeout still apply.

**Front-end exposure:** a discreet `<EgressPolicyTooltip>` on the Run button of the six affected
node UIs, read-only, consuming `GET /egress-policy`. No per-node override. Policy errors render
with specific `userMessage`s on the node error card (`"Request blocked: destination IP is in a
blocked range (link-local)"` etc.), not generic failures.

**Out of scope here** (deferred to follow-up tasks): admin UI to manage the allowlist (allowlist
CRUD lives behind the API for v1); a dashboard of "what would be blocked in the last 24h"; a
per-node override UI for limits.

## Verification

- **Negative control (required).** Point an `apiCaller` node at `169.254.169.254` and confirm it
  currently returns metadata. That is the finding; demonstrate it in a controlled environment
  before fixing it, and keep the test.
- Redirect bypass: a permitted host that 302s to a blocked address must be refused at the redirect.
- **Measure before refusing** (PLAN §3.3.2) — this rule refuses network traffic, which is the most
  disruptive kind of refusal. Sample the real URLs stored in node configurations, classify each as
  *would still work* or *would now be blocked*, and drive the second to zero before enabling.
  Anything unresolvable is *unverifiable*, not *blocked*.
- Report-only cycle removed from scope (see "D25 decision"). The negative-control test and the
  pre-deploy measurement script replace the production report-only window.

## Done when

Egress is policy-controlled at the shared fetch layer, redirects are refused, the worker's
network position is documented, and the measurement script shows no legitimate stored URL would be
blocked by the hardcoded deny-list before deploy.

## Rollout (ship directly in enforce)

The code changes land with the policy **always enforced**. There is no `EGRESS_MODE` env var and no
report-only mode. The sequence is:

1. **Run the measurement script in prod before merging.** `pnpm script:egress-measure` reads
   `flow_node` rows, extracts the user URLs from `apiCaller` and `fileSave` configurations, and
   classifies each as `wouldWork`, `wouldBlock`, or `unresolvable`. Review the `wouldBlock` list
   with the team before deploy; if any entry looks like a legitimate customer URL, re-think the
   deny-list before shipping.
2. **Deploy to dev.** Negative control test (`safe-fetch.service.spec.ts`) must pass in CI.
3. **Deploy to staging.** Monitor `node_executions.errorCategory = 'egress_policy'` for 48h.
4. **Deploy to prod.** Monitor the same metric for the first week.
5. **If a legitimate customer URL is refused**, we have three options to resolve: punch a hole in
   the hardcoded deny-list (if the IP range truly is public but miscategorised), reintroduce the
   per-organisation allowlist, or isolate that customer's worker in a dedicated subnet. Document
   whichever path is taken, with the ticket number.

## Files

`back/src/app-api/downloader/downloader.controller.ts` (`@Query('url')`) · `back/src/app-api/scraper/` ·
`back/src/app-api/api_call/` · the worker's HTTP layer · infra network/subnet definitions ·
`worker/src/modules/safe-fetch/` (the new module shipped by this task) ·
`back/src/app-api/egress_policy/` (the `GET /egress-policy` endpoint consumed by the front tooltip)
· `front/src/components/EgressPolicyTooltip/` and the `EGRESS_POLICY_NODE_TYPES` registration in
`front/src/components/UI/Node/Node.tsx`.

## Files

`back/src/app-api/downloader/downloader.controller.ts` (`@Query('url')`) · `back/src/app-api/scraper/` ·
`back/src/app-api/api_call/` · the worker's HTTP layer · infra network/subnet definitions
