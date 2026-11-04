# S9 — Refuse a third-party credential the executing user cannot reach

**Goal:** a run, or a configuration call, uses a saved third-party connection only when the user it
runs for can reach that connection under the product's own rule, and only for the provider the node
names.

**Depends on:** A11 ([868mn64he](https://app.clickup.com/t/868mn64he)). After A11, no path runs
`thirdPartyIntegration` or `hubSpotCRM` inline, so the worker is the only run path that resolves a
credential. **Blocks:** nothing. **Added 2026-10-29** from the finding that P7
([868kmjhjx](https://app.clickup.com/t/868kmjhjx)) recorded and left open. ClickUp:
[868mpn1h3](https://app.clickup.com/t/868mpn1h3).

## Why

P7 found that authorization is not checked when a saved credential is used
(`.claude/tasks/worker-thirdparty-integration-migration/p7-mcp/spec.md`, "Finding: authorization
is not checked when the credential is used"). P7 closed only the MCP write side: `add_node` and
`update_node` refuse an `integrationId` the token's user cannot reach. It wrote: "Fixing the runtime
resolution is a separate task with its own production measurement." That task was never created
(ClickUp search, 2026-10-29). This is that task.

Checked on 2026-10-29 against worker `main` `892ae3d` and back `main` `e8781bda`:

| # | Where | What happens today |
|---|---|---|
| 1 | Worker `resolveMigratedIntegration` (`worker/src/modules/nodes/third-party-integration/user-integration.repo.ts:189-215`) | Reads the row with `QUERY_FIND_BY_ID` (`:7-12`, `WHERE id = $1 AND "deletedAt" IS NULL`): no owner, no sharing, no provider. When the row exists, `reportUnreachableIntegration` (`:174-187`) only logs "Run used an integration the executing user cannot reach", and the run uses the credential. |
| 2 | Same function, an `integrationId` that is not a UUID | `user_integrations.id` is a `uuid` column, so Postgres raises `invalid input syntax for type uuid`. The run fails with a raw database error instead of a `UserConfigError`. Node data is free text: `update_node` writes it. |
| 3 | Worker `ThirdPartyIntegrationService.process` (`third-party-integration.service.ts:36-57`) | Resolves the credential, then refreshes an expired OAuth token and writes it back (`executeWithOAuth`, `:77` onward), then calls the provider. A run with another user's `integrationId` refreshes and stores that user's token. |
| 4 | Worker `connectedByUserId` | Copied into the payload (`payload-builder.ts:197-199`) and never read for resolution. `PORTED_FROM.md:14` records that the cross-user fallback was not ported. |
| 5 | Back `resolveIntegration` (`back/src/app-api/integrations/integrations.service.ts:647-710`) | A bare `findById` for `integrationId`, then `reportUnreachableIntegration` (`:614-645`) logs and the credential is used. The `connectedByUserId` fallback (`:668-691`) uses another user's credential for the provider after a `fallbackUserId !== userId` test, and also only logs. |
| 6 | Back callers of `resolveIntegration` | `pull` (`:486`), `push` (`:512`), `getOptions` (`:536`) and `getDatabaseSchema` (`:563`), reached from `POST /integrations/:provider/pull`, `/push`, `/test-push` and `GET /integrations/:provider/schema/database` (`integrations.controller.ts:389-476`, `:494-497`). A11 leaves these configuration routes in place (A11, **Integration types**, **Out**). `push` and `test-push` write to the provider. |
| 7 | Worker MCP target (`mcp/mcp-target.ts:94-110`) | Already refuses an unreachable MCP connection, but with two different messages: "no longer exists" and "You do not have access". The difference tells the caller whether the id exists. An `integrationId` that is not a UUID reaches Postgres and fails with a raw database error, as in row 2. |
| 8 | Back `refreshToken` (`integrations.service.ts:445-477`), reached from `POST /integrations/:provider/refresh-token` | With an `integrationId`, a bare `findById` with no owner, sharing or provider check, then `adapter.refreshAccessToken` and `persistRefreshedToken`. A caller refreshes and stores another user's token. Added to S9 on 2026-10-30. |
| 9 | Back `getIntegrationById` (`integrations.service.ts:197-224`), the only check behind `getMcpConnectionCredentials`, reached from `POST /mcp-call` and `POST /mcp-call/list-tools` | A third reachability rule: the caller's own row, or any row whose owner is an `active` member of the request's company, shared or not. It ignores `isSharedWithOrg` and returns the credentials. Added to S9 on 2026-10-30. |

The line numbers above are those of the commits named before the table. A11, merged on 2026-10-30,
moved `third-party-integration.service.ts` (`process` now at `:43`, `executeWithOAuth` at `:90`) and
`payload-builder.ts` (`connectedByUserId` at `:203-204`).

Stated fairly: the ids are UUIDv4, so this is not mass exfiltration. The concrete risk is **access
persistence**. An id someone legitimately saw, as a company member or while the connection was
shared with the organization, keeps working after they leave the company or after the owner stops
sharing it. Whoever can write node data chooses the credential.

**Why now.** A11 removes the back's inline integration path. After A11, every `thirdPartyIntegration`
and `hubSpotCRM` run resolves its credential in the worker, so the run-time fix lives in one place.
The back's configuration routes (row 6) stay, and they are part of this task.

## The rule — reuse it, never re-derive it

"Reachable" already exists in both repos. Call it; do not write a third copy.

- **Worker:** `isIntegrationReachableByUser(db, integrationId, userId)`
  (`user-integration.repo.ts:162-172`, `QUERY_IS_REACHABLE_BY_USER` at `:14-36`). The row is the
  user's own, or it has `isSharedWithOrg = true` and its owner and the user are both `active` members
  of one company. `reachability.spec.ts` pins the query shape.
- **Back:** `isReachableByUser` (`integrations.service.ts:586-598`), which calls
  `UserIntegrationService.findAvailableConnections(userId, companyId, provider)`
  (`back/src/app-api/user_integration/user_integration.service.ts:36-69`) and filters by the row's
  provider.

The two rules differ in two ways. Record both here and do not change either rule in this task:

1. The back's rule, with a `companyId`, checks that the connection owner is `active` in that company
   but does not check the caller's own membership status. The worker checks both.
2. The back's rule filters by provider; the worker's does not. This task adds the provider check in
   the worker's resolver, not in the reachability query, so `reachability.spec.ts` keeps its meaning.

A third rule existed in the back: `getIntegrationById` (row 9). It is not a variant to keep. This task
deletes it and routes its caller through `isReachableByUser`.

## Scope

**In — the worker resolver.**

1. In `resolveMigratedIntegration`, when `integrationId` is set:
   1. If it is not a UUID, refuse.
   2. Read the row with its `provider`. If no row exists, keep today's behaviour: fall back to the
      executing user's own connection for the provider, then to the legacy migration. Disconnecting
      deletes the row (`user_integration.service.ts:93-95`, `repository.delete`), so this keeps a
      flow working after its owner disconnects and reconnects. The fallback never reaches another
      user's row.
   3. If the row's `provider` differs from the node's provider, refuse.
   4. If `isIntegrationReachableByUser` returns `false`, refuse. Never fall back to the user's own
      connection after a refusal: a run that silently writes to a different account is worse than a
      failed run.
2. The refusal is a `UserConfigError` with `field: "integrationId"` and one `userMessage` for every
   refused case, including "no row and no own connection" when an `integrationId` was given. For
   example: "This node's {provider} connection is not available to you. Pick one of your
   connections in the node, or ask the connection's owner to share it with your organization." The
   message never says whether the id exists. `devMessage` names the reason (`not-uuid`,
   `provider-mismatch`, `unreachable`, `no-fallback`) and at most the first 36 characters of the id.
3. The check runs before the first side effect of `process`: before `migrateLegacyCredential`
   inserts a row, before `executeWithOAuth` refreshes and stores a token, and before the adapter
   calls the provider. If the reachability query throws, the run fails with a retryable error and
   nothing else happens. A retry runs the check again; nothing caches an earlier answer.
4. `connectedByUserId` stays ignored at run time. Add a test that pins it: a node with another user's
   `connectedByUserId` and no `integrationId` resolves only the executing user's own connection, or
   fails with "Not connected".
5. Delete the log-only `reportUnreachableIntegration`. Log each refusal once, with the reason, the
   provider, the user and the integration id, so production refusals can be counted.
6. `mcp-target.ts:94-110` uses the same `userMessage` for its "no row" and "not reachable" cases. It
   refuses an `integrationId` that is not a UUID before any query, and a failure of the row read or
   of the reachability query is a retryable error, as in the resolver. MCP keeps no fallback to the
   user's own connection (`mcp/PORTED_FROM.md`).

**In — the back configuration routes.**

1. In `resolveIntegration`, an `integrationId` that resolves to a row the user cannot reach
   (`isReachableByUser`, which also checks the provider) is refused with the same `userMessage`, as
   a NestJS exception with an `HttpStatus` enum value. A missing row keeps today's fallback to the
   user's own connection, as in the worker.
2. The `connectedByUserId` fallback is used only when `isReachableByUser` accepts the fallback row.
   Otherwise the call continues as if no fallback were named, and ends in today's "Not connected"
   error.
3. Delete the log-only `reportUnreachableIntegration` in the back, as in the worker.
4. `refreshToken` with an `integrationId` (row 8) refuses a malformed id, a missing row, a row of
   another provider and a row `isReachableByUser` rejects, with the same message, before any
   refresh. A reachable shared row still refreshes. Without an `integrationId` it behaves as today.
   The refresh-token route passes `user.selectedCompanyId`, as `pull` and `push` do.
5. `getMcpConnectionCredentials` (row 9) uses the same named-connection check as
   `resolveIntegration`, with the provider fixed to `mcp`. A missing row, an unreachable row and a row
   of another provider get the same message. Delete `getIntegrationById` and
   `UserIntegrationService.isUserInCompany`, which has no other caller.

**Out.**

- The difference between the two reachability rules (see **The rule**). A change to either one
  needs its own measurement. The MCP routes take the company from `body.organizationId`, and the
  back's rule does not check the caller's membership in it: tracked in
  [868mq9rjr](https://app.clickup.com/t/868mq9rjr).
- `processFlow` sends the Temporal failure text as `userMessage` in `node_finished` and the run's
  final event, so `space_run_logs.errorMessage` and the run outcome do not show the refusal;
  `execution_logs.userMessage` does. It affects every node type: tracked in
  [868mq9rk6](https://app.clickup.com/t/868mq9rk6).
- In `refreshToken`, a failure after `refreshAccessToken` succeeds makes a retry refresh again. It
  predates S9, and the new check runs before every side effect. Left as is by decision.
- The MCP write-time check. P7 shipped it, and it is in production.
- A data repair of nodes that would be refused. If the measurement finds any, the repair is a
  decision for the user before this task ships (see **Measurement gate**).
- Front changes. The connection picker already lists only reachable connections
  (`IntegrationsService.listConnections`, `integrations.service.ts:119`).

## Measurement gate — this refusal must not ship unmeasured

Unlike P7's write-time check, this refusal affects every saved flow and the editor's preview panels
(PLAN §3.3.2, "Measure before refusing"). Classify every stored node that carries an
`integrationId` or a `connectedByUserId` before the refusal ships.

[`s9-q1-integration-reachability.sql`](./s9-q1-integration-reachability.sql) is one read-only
statement. It classifies three scopes:

| Scope | Node data | Checked against |
|---|---|---|
| `live` | the live canvas node | the flow owner |
| `history` | each version history copy of the node | the flow owner |
| `executed_30d` | the live canvas node | every user who ran it in the last 30 days (`node_executions."userId"`) |

Each row gets one verdict: `own`, `org_shared`, `unreachable`, `provider_mismatch`, `dangling`,
`not_uuid`, `connected_by_self`, `connected_by_reachable` or `connected_by_unreachable`. The
would-be-refused verdicts are `unreachable`, `provider_mismatch` and `connected_by_unreachable`.
`not_uuid` already fails today; `dangling` keeps its fallback.

Steps:

1. Run the file on dev with the `ec2-tunnel` skill and record the counts here. P7 measured 14
   (flow owner, `integrationId`) pairs on dev, 0 unreachable; the back's comment at
   `integrations.service.ts:600-608` records 6 pairs on staging, 0 unreachable. This query also
   covers history, executing users, provider and `connectedByUserId`, so expect different totals.
2. Hand the file to the user for production. The user runs it in DBeaver and saves the result as
   `s9-q1-integration-reachability.prod.csv` next to the spec. You never query production.
3. Count the two log-only report lines in production since the deploy that carries them, read-only:
   the back's "resolved an integration the executing user cannot reach" and the worker's "Run used
   an integration the executing user cannot reach". Confirm the deployed commit first; both lines
   are on `main` as of back `e8781bda` and worker `892ae3d`. Each line is a run that S9 would have
   refused.
4. Ship only when every would-be-refused count is zero in dev and in production and the log count is
   zero. Record all counts here.

If production shows any would-be-refused node or log line, do **not** ship the refusal. Report the
count to the user and treat it as a data-repair question first, because those flows run today.

`s9-q1` covers `thirdPartyIntegration` and `hubSpotCRM` only. MCP is its own node type, `mcpNode`,
so rows 7 and 9 are measured by
[`s9-q2-mcp-reachability.sql`](./s9-q2-mcp-reachability.sql). It uses the same scopes and adds the
verdict `loose_only`: a row the deleted `getIntegrationById` rule accepts and the product rule
refuses. The would-be-refused verdicts are `unreachable`, `loose_only` and `provider_mismatch`.

### Results, 2026-10-30

**Dev**, `s9-q1`:

| Scope | Verdict | Refused | Nodes | Flows |
|---|---|---|---|---|
| `executed_30d` | `own` | no | 2 | 2 |
| `live` | `own` | no | 18 | 11 |
| `live` | `org_shared` | no | 3 | 3 |
| `live` | `connected_by_self` | no | 3 | 2 |
| `live` | `provider_mismatch` | **yes** | 1 | 1 |

The `provider_mismatch` node is correctly refused. It is a `wordpress` node whose `integrationId`
names its owner's own `zapier` row, left over from a provider switch. It has never run, was last
edited on 2026-03-23, and its owner has no WordPress connection, so it fails today as well. No
history copy carries `integrationId` or `connectedByUserId`. Every other node of these types that
names a credential is in a deleted flow (32 `thirdPartyIntegration`, 1 `hubSpotCRM`).

**Dev**, `s9-q2`: 6 live `mcpNode` rows, all `own`. One more `mcpNode` is in a deleted flow.

**Production** (run by the user):

- `s9-q1` ([`s9-q1-integration-reachability.prod.csv`](./s9-q1-integration-reachability.prod.csv)):
  2 live nodes, both `own`. Zero would-be-refused.
- `s9-q2` ([`s9-q2-mcp-reachability.prod.csv`](./s9-q2-mcp-reachability.prod.csv)): no rows. No
  `mcpNode` in production names a saved connection.
- Log-only lines, CloudWatch Logs Insights from 2026-08-11 (the day both lines were added) to
  2026-10-30: the worker's "Run used an integration the executing user cannot reach" in
  `/ecs/worker-task-definition-prod` (1,057,600 lines in that window): 0. The back's "resolved an
  integration the executing user cannot reach" and "could not classify integration reachability"
  in `/ecs/api-task-definition-prod`: 0. Control: `[Integrations]` in the same back group returns 2
  lines (2026-08-24), so the query finds lines that exist.

The gate is met: zero would-be-refused in production, and zero log lines.

## Verification

- **Negative control (required).** Each test is seen red before it counts:
  - Restore the log-only path and watch the unreachable-id test go red.
  - Remove the provider comparison and watch the provider-mismatch test go red.
  - The not-UUID test is red on `main` today (raw database error); it goes green with the fix.
  - Wire a `connectedByUserId` fallback into the worker resolver and watch its pinning test go red.
  - Back: remove the check in `resolveIntegration` and watch the `push` route test with an
    unreachable id go red; that test also asserts that the adapter was never called.
  - Back: return `refreshToken` to a bare `findById` and watch the refresh refusal tests go red;
    restore the same-company rule and watch the MCP "same company, not shared" test go red.
  - Worker: remove the not-UUID check in `mcp-target.ts` and watch its test go red.
- **Failure after a side effect** (`CLAUDE.md`, "Coding Rules"). The new check adds an `await`
  before the side effects, not after them. Make the reachability query throw and assert that
  `migrateLegacyCredential`, the token refresh and the adapter were never called, and that a second
  attempt runs the check again. Assert the same when the row read throws.
- **Text that crosses to another service** (`CLAUDE.md`, "Coding Rules"). The refusal travels from
  the worker to the back as the node's error. Test it with a 5000-character `integrationId`: the run
  gets the same refusal, `devMessage` stays bounded, and the back stores the error. Assert
  `userMessage` where the back receives it, never `devMessage`. Use a real-looking `userMessage` in
  fixtures. The review opens the receiving DTO in the back (`@MaxLength`, required fields) and
  names it in the PR.
- **Rule reuse.** The worker test asserts that the resolver calls `isIntegrationReachableByUser`
  with the executing user from the activity props, never the flow owner from node data.
- Run every test locally, scoped (`--maxWorkers=1`, 4 GB heap). Never probe production.

## Done when

The worker refuses an unreachable, wrong-provider or malformed `integrationId` with one
`UserConfigError` before any side effect; `connectedByUserId` cannot select another user's
credential in the worker or the back; the back's configuration routes apply the same rule; no
log-only reachability report remains; the refusal message never reveals whether an id exists; every
negative control has been seen red; refresh-token and the MCP credential route apply the product
rule; and the dev and production counts from `s9-q1` and `s9-q2` and the production log count are
recorded here, with zero would-be-refused.

## Files

worker `src/modules/nodes/third-party-integration/user-integration.repo.ts`,
`third-party-integration.service.ts`, `reachability.spec.ts`, `mcp/mcp-target.ts`,
`mcp/mcp-target.spec.ts`, `PORTED_FROM.md`, `mcp/PORTED_FROM.md` · back
`src/app-api/integrations/integrations.service.ts`, `integrations.controller.ts`,
`integrations.reachability.spec.ts`, `src/app-api/user_integration/user_integration.service.ts` ·
this folder's `s9-q1-integration-reachability.sql`, `s9-q2-mcp-reachability.sql` and their
`.prod.csv` results
