# C3 — Fix the defects before they get ported

**Goal:** clear the known bugs in the code being moved, so the migration does not copy them into a
second place where they must be fixed twice.

**Depends on:** nothing. **Do it early** — every one of these gets more expensive after the code it
lives in has been duplicated. **Source:** analysis §11.5.

## Scope

**Verified in this repository:**

1. **`previewResponses` trim uses strict equality.** `responses.length === 10` at six sites
   (`flux.service.ts:3276, 3868, 7978, 8031, 8083, 8210`). One element is appended per run, so the
   cap normally holds — but any array that reaches eleven by another path never trims again and
   grows without bound inside `flows_nodes.data`, which is the known front-end performance
   offender. Change to `>=`, and decide whether to backfill oversized arrays.
2. **`endNode` called twice on the same handle.** `flux.service.ts:4537` and `:4553`, both on
   `genericRunLogNode`. Harmless today, but it will confuse anyone porting the collector, and E1
   is about to.

**Reported by the step documentation, confirm before acting:**

3. **`processFlowWithSubstitution`** (`node-reference-substitution.service.ts:241–267`) may be dead
   code. B2 is about to extract this module — extracting dead code and then maintaining it in two
   repos is the specific waste to avoid. Prove it is unreachable across all four repos and
   `origin/production` before deleting; code absence in one repo is not proof of no traffic.
4. **`GOOGLE_LOGIN_CLIENT_SECRECT`** — a typo in an env var name. Renaming requires changing dev,
   CI and production together; run the `env-vars-sync` skill and treat it as a coordinated change,
   not a find-and-replace.
5. **`api-caller-polling.ts` has no importers.** `back/src/app-api/flux/api-caller-polling.ts` is
   referenced by nothing across `back` and `worker`; the polling it implements already lives in the
   worker as `execute-polling`, consumed by `api-caller.service.ts:17, 407` (review §11.5). Same
   proof burden as item 3 — all repos plus `origin/production` — before deleting.
6. **The friendly error timestamp** records "now" rather than when the error occurred
   (`flux.service.ts:4881–4884`).

**Out.** Anything that changes execution semantics. This task is for defects whose fix is
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

## Done when

Each defect has a test that failed before the fix, the trim's data impact is measured rather than
assumed, and the dead-code claim is proven across every repo before anything is deleted.

## Files

`back/src/app-api/flux/flux.service.ts:3276, 3868, 4537, 4553, 4881–4884, 7978, 8031, 8083, 8210` ·
`back/src/app-api/node-reference-substitution/node-reference-substitution.service.ts:241–267` ·
`back/.env.example` and every environment that carries the Google client secret
