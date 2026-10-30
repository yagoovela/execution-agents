# C3 — Fix the defects before they get ported

**Goal:** clear the known bugs in the code being moved, so the migration does not copy them into a
second place where they must be fixed twice.

**Depends on:** nothing. **Do it early** — every one of these gets more expensive after the code it
lives in has been duplicated. **Source:** analysis §11.5.

## Scope

**Verified in this repository:**

1. **`previewResponses` trim uses strict equality.** `responses.length === 10` at six sites
   (`flux.service.ts`). One element is appended per run, so the
   cap normally holds — but any array that reaches eleven by another path never trims again and
   grows without bound inside `flows_nodes.data`, which is the known front-end performance
   offender. Change to `>=`, and decide whether to backfill oversized arrays.
2. **`endNode` called twice on the same handle.** two consecutive calls in `flux.service.ts`, both on
   `genericRunLogNode`. Harmless today, but it will confuse anyone porting the collector, and E1
   is about to.

**Reported by the step documentation, confirm before acting:**

3. **`processFlowWithSubstitution`** (`node-reference-substitution.service.ts`) may be dead
   code. B2 is about to extract this module — extracting dead code and then maintaining it in two
   repos is the specific waste to avoid. Prove it is unreachable across all four repos and
   `origin/production` before deleting; code absence in one repo is not proof of no traffic.
4. **`GOOGLE_LOGIN_CLIENT_SECRECT`** — a typo in an env var name. Renaming requires changing dev,
   CI and production together; run the `env-vars-sync` skill and treat it as a coordinated change,
   not a find-and-replace.
5. **`api-caller-polling.ts` has no importers.** `back/src/app-api/flux/api-caller-polling.ts` is
   referenced by nothing across `back` and `worker`; the polling it implements already lives in the
   worker as `execute-polling`, consumed by `api-caller.service.ts` (review §11.5). Same
   proof burden as item 3 — all repos plus `origin/production` — before deleting.
6. **The friendly error timestamp** records "now" rather than when the error occurred
   (`flux.service.ts`).
7. **The OAuth refresh holds a pooled connection across an external HTTP call.**
   `refreshOAuthTokenUnderLock` (`worker/.../third-party-integration/oauth-token.repo.ts:76`) checks
   out a client, opens a transaction, takes `pg_advisory_xact_lock`, and only then calls
   `doRefresh` — the provider's own token endpoint. The connection, the transaction and the lock
   are all held for the whole round trip. Every adapter bounds that call (Notion 15s, Slack 15s,
   HubSpot 30s per request with a 30s retry budget), so this is **bounded, not unbounded** — but it
   is three to four orders of magnitude longer than any other query the worker runs, and nothing in
   the worker sets `statement_timeout` or `idle_in_transaction_session_timeout`, so the database
   will not cut it short either. Twelve concurrent stale-token refreshes on one replica saturate
   its whole pool for that window, and because the advisory lock is keyed by integration, a slow
   provider also stalls every other replica refreshing the same integration. Found while validating
   S2; it is a defect of the code being ported, not of S2's pool sizing.

**Out.** Restructuring item 7's lock so the HTTP call happens outside the transaction. That is the
right long-term shape, but it changes when a concurrent refresh is allowed to proceed — which is
execution semantics, and belongs to the task that owns third-party integration. What belongs here is
the behaviour-preserving half: set `statement_timeout` and `idle_in_transaction_session_timeout` on
the worker's pool so a stuck connection is reclaimed rather than pinned.

Anything else that changes execution semantics. This task is for defects whose fix is
behaviour-preserving in the normal case; a fix that changes what a run produces belongs to the task
that owns that behaviour.

## Verification

- **Negative control (required), per fix.** Each of these needs a test that fails on the current
  code. For the trim: seed a node with eleven stored responses, run it, and assert the array does
  not grow — that test fails today. For the duplicate `endNode`: assert one end event per node.
  A fix without a test that failed first is indistinguishable from a fix that changed nothing.
- **Measure before acting on the trim backfill.** Query the real data for
  `previewResponses` arrays longer than ten before deciding whether a backfill is needed, and
  report the count. If none exist, say so — an unnecessary data migration is its own risk.
- For the dead-code deletion: owner-anchored greps across `back`, `front`, `worker`, `mcp-server`
  **and** `origin/production`, not just the local checkout.
- **For item 7, measure before setting the timeouts.** An `idle_in_transaction_session_timeout`
  shorter than a real OAuth round trip would abort refreshes that work today — the false-refusal
  failure. Measure the real distribution of `doRefresh` durations per adapter against stored
  integrations before picking a value, and set it above the slowest observed round trip, not at a
  round number.

## Done when

Each defect has a test that failed before the fix, the trim's data impact is measured rather than
assumed, and the dead-code claim is proven across every repo before anything is deleted.

## Files

`back/src/app-api/flux/flux.service.ts` (`responses.length === 10` at six sites; the two consecutive `endNode` calls on `genericRunLogNode`; the friendly-error timestamp) ·
`back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts` (`processFlowWithSubstitution`) ·
`back/.env.example` and every environment that carries the Google client secret ·
`worker/src/modules/nodes/third-party-integration/oauth-token.repo.ts` (`refreshOAuthTokenUnderLock` holds the connection across `doRefresh`) ·
`worker/src/modules/database/database.service.ts` (no `statement_timeout` / `idle_in_transaction_session_timeout`)

## Decision recorded (2026-10-23)

**C3-a — resolved as B.** PR #1966 shipped only the forward fix: `previewResponses` drops one item
per append once it holds ten (`>= 10`, back `flux.service.ts:3919` and `:4560`; worker
`preview-responses.ts`). No backfill migration exists, and the count of stored arrays longer than
ten was never recorded, so an existing oversized array stops growing but keeps its length.
