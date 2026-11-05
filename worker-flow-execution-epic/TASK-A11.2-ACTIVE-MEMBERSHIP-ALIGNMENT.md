# A11.2 — One membership rule for folders, spaces, chatbots and forms

**Goal:** every check that grants access through a company or a space answers the same question the
agent rule answers since A11.1: is the user the owner, or an ACTIVE member of the company that owns
the space? A pending, inactive or removed member gets the same refusal everywhere, and an active
member keeps every access they have today.

**Depends on:** A11.1 ([868mq7c8q](https://app.clickup.com/t/868mq7c8q)), back #2078, merged and
deployed to production on 2026-11-03 (back `fe318119`). **Blocks:** nothing. **Added 2026-10-30**
from the A11.1 code review. ClickUp: [868mqc7w6](https://app.clickup.com/t/868mqc7w6).

## Why

A11.1 made `FlowAccessService.applyAccessPredicates`, the agent rule, require an ACTIVE company
membership. The other membership checks were left as they were, so the same user gets different
answers from different routes.

Checked on 2026-11-03 against back `main` `2cfe43d4`:

| # | Where | What happens today |
|---|---|---|
| 1 | `FlowAccessService.resolveFolderForUser` (`folw/flow-access.service.ts:56`) | Accepts the folder's owner in any folder, and any company member of the space's company with no status check. Its callers create agents: `api-flows.service.ts:215`, `flow.controller.ts:1438`, `app-mcp/mcp-folder.service.ts:404`. A pending member resolves a company folder, and then gets "Agent not found" for every agent inside it. |
| 2 | `canAccessSpaceOwnedResource` (`company/space-resource-access.ts:12`) | Grants access through a `user_spaces` row with no status check. It decides internal chatbots and internal forms (see "Chatbot and form routes"). |
| 3 | `FlowAccessService.assertUserCanWriteToSpace` | Grants write access to a space through a `user_spaces` row with no status check. |
| 4 | `user_spaces` rows | Survive a change of membership. `PATCH /company/user` (set inactive) and `POST /company/remove-user/:id` touch only `company_user` (`company.controller.ts:1641-1663`, `:1458`), and the entity has no cascade (`user_spaces.entity.ts:40-55`). Only `POST /company-spaces/remove-user` deletes a row. So a removed or inactive member keeps chatbot, form and space-write access through a leftover row. |
| 5 | `GET /forms/:id` (`forms.controller.ts:370`), the form builder read | Allows the owner or a `user_spaces` row only. An ACTIVE company member without a row gets "Form not found", and an inactive member with a leftover row gets in. |
| 6 | `resolveRunLogAccess` on top of `findAccessibleAgent` (`flow-access.service.ts:270`, `:306`) | Loads the whole agent row, its folder and its space (`leftJoinAndSelect`) to read the agent's id and name, on every run-log request, including the editor's poll. Performance only. |
| 7 | Runs list "started by" (`executions_logs/execution_logs.service.ts:693`, `:1212`) | The list filters by row (`ne."userId"`) and shows `MAX(userId)` as the starter. A run's steps and Cancel use the oldest row (`assertCanReadRun`). A user with a row in someone else's run sees it in the list and gets 404 on its steps. |

The A11.2 card also listed `SuperchatLiveFactsService.failedNodesOf` as unchecked. It is not: both
callers resolve the agent with `resolveAccessibleAgent` first (`read-run.tool.ts:73`,
`superchat-location.service.ts:38`), and the steps stay bound to that agent. It is out of this task.

## The rule — reuse it, never re-derive it

The product rule after A11.1 is `applyAccessPredicates`:

1. The owner of a personal folder (no space, no workspace folder).
2. An ACTIVE member of the company that owns the space, for everything in that space.
3. The ACTIVE owner of a workspace folder.

Space membership (`user_spaces`) is added only for ACTIVE members of the company
(`company_spaces.controller.ts:678-700`). So, for reading, an ACTIVE member already passes rule 2, and
a `user_spaces` row adds access only when the membership is no longer ACTIVE, which is the case this
task closes.

This task moves the membership question into one helper that every check calls, for example
`hasActiveCompanyMembership(userId, companyId)`, and keeps `applyAccessPredicates` as the SQL form of the
same rule. It does not add a fourth rule.

## Decisions

**D1, decided 2026-11-03: a person keeps access to the forms and chatbots of the space they are in,
only while they are an ACTIVE member of the company.** An ACTIVE company member also has access. A
public form or chatbot is a different case, covered in "Chatbot and form routes".

**D2, decided 2026-11-03: a `user_spaces` row counts only while the user is an ACTIVE member of the
space's company.** It closes item 4 without deleting data: reactivating the member restores the
access. Deleting `user_spaces` rows when a member is set inactive or removed was rejected, because it
changes data and reactivation cannot undo it.

**D3, decided 2026-11-03: write access to a space (`assertUserCanWriteToSpace`) also requires an
ACTIVE membership.** Today a removed member with a leftover row can create an agent in the space, and
under A11.1 cannot open it afterwards.

**D4, decided 2026-11-03: the unprotected routes in "Unprotected routes" come into this
task.** `PATCH /flow/clear-chat` gets an access check. The other routes are fixed only after their
callers and business rules are mapped, so that no legitimate access closes.

## Chatbot and form routes

How each route decides access today (back `main` `2cfe43d4`). `@Public()` means optional auth: with no
token, or an invalid one, the caller is anonymous (`app-auth/guards/jwt-auth.guard.ts:13-22`). The
front pages `/chatbot/:chatId` and `/published/interface/:formId` sit outside `PrivateRoutes`
(`front/src/navigator/Navigator.tsx`), so they do not require login.

| Route | Auth | Decides access with |
|---|---|---|
| `GET /flow/chatbot/:id` (`flow.controller.ts:197`) | JWT required | `resolveChatbotAccess`: owner, then `canAccessSpaceOwnedResource`. Ignores `public` and the publish type. |
| `GET /flow/chatbot/public/:id/:sessionId` (`flow.controller.ts:333`) | Optional | `resolveChatbotDelivery`: owner; not `public` is refused; `chatbotPublishType = 'internal'` needs login and `canAccessSpaceOwnedResource`; anything else is open. |
| `POST /flux/chatbot-api-socket` (`flux.controller.ts:954`) | Optional | `resolveChatbotDelivery`, as above. Runs the flow as its owner. |
| `GET /forms/published/:id` (`forms.controller.ts:281`) | Optional | Not `published` is refused, even for the owner. `publishType = 'internal'` (the default) needs login and `canOpenInternalForm`, which calls `canAccessSpaceOwnedResource`. Anything else is open. |

A public chatbot (`public = true`, publish type not `internal`) and a published form whose publish type
is not `internal` are open to anyone, including anonymous callers. This task does not change them:
`canAccessSpaceOwnedResource` is reached only for the internal publish type and for the logged-in
chatbot read.

After this task, for an internal chatbot or an internal published form:

| Caller | Today | After |
|---|---|---|
| Anonymous or stranger | Refused | Refused |
| Owner | Allowed | Allowed |
| ACTIVE company member | Allowed | Allowed |
| `user_spaces` member, ACTIVE in the company | Allowed | Allowed |
| `user_spaces` row, membership inactive, pending or removed | Allowed | **Refused** |
| Inactive or pending member without a row | Refused | Refused |

## Scope

**In — back, with one front change for R5.** Phases 5 to 9 widened this list; see "Phases" and D14 to D21.

1. `resolveFolderForUser`: the owner branch applies only to a personal folder, and the company branch
   requires an ACTIVE membership, matching `applyAccessPredicates`. It reads the same folder query as
   `canAccessFolder`, so a workspace folder is not restricted to the user's selected company.
2. `canAccessSpaceOwnedResource`: the `user_spaces` branch also requires an ACTIVE membership in the
   space's company (D2).
3. `assertUserCanWriteToSpace`: the same (D3).
4. `GET /forms/:id`: decides with `canAccessSpaceOwnedResource` instead of its own owner or
   `user_spaces` check, so an ACTIVE company member reads the form like they read its agents.
5. `resolveRunLogAccess`: selects only `flow.id` and `flow.name` with the same predicate.
6. Runs list: under OWN scope, filter by the run's starter (the oldest row, the same expression
   `assertCanReadRun` uses), and show that starter.

**Out.**

- Public chatbots and public forms. Their behaviour is a product decision this task does not make.
- Deleting `user_spaces` rows when a membership changes (D2 alternative).
- Fixing a route in "Unprotected routes" before its callers and business rules are mapped
  (D4).

## Measurement gate — this refusal must not ship unmeasured

Write each query as one read-only statement, run it on dev, and give it to the owner to run in
production before the PR to `main`.

1. **Leftover space access.** Users with a `user_spaces` row whose membership in the space's company is
   not ACTIVE or missing. Count the users, the spaces, the internal chatbots and internal published
   forms in those spaces, and how many of those users ran a chatbot (`runType = 'chatbot'`) or a form
   (`runType = 'formapi'`) of those spaces in the last 30 days.
2. **Folder resolution.** Users who resolve a company folder today only through a non-ACTIVE
   membership, or as the owner of a space folder without an ACTIVE membership, and how many of them
   created an agent in the last 30 days.
3. **A11.1 results.** The A11.1 inactive-member count was not recorded before A11.1 shipped. Record
   it with these two.

Pass: no user who used the access in the last 30 days loses it, or each one is listed and accepted.

**Result (2026-11-05): pass.** The gate grew to nine queries as the phases widened the scope. Each one
is versioned here with its production result: `a11-2-q1`, `q6`, `q7`, `q8`, `q9` and `q11` ran on
2026-11-04, and `q12`, `q13` and `q14` on 2026-11-05 (`a11-2-q*.sql` and `a11-2-q*.prod.csv`). Every
refused group shows 0 runs and 0 uses in the last 30 days. Q6 counts 7 refused agents edited in the
last 30 days by anyone; no table records who edited an agent, and none of the refused users ran them.
Q12 finds 0 MCP calls that would be refused, Q13 finds 0 creations that would hit a plan limit, and Q14
finds 0 runs in the folders that stop counting as personal.

## Verification

- Real-Postgres integration tests, one per row of the "After" table, for an internal chatbot, an
  internal published form, the form builder read, folder resolution and space write.
- Public chatbot and public form tests: anonymous, stranger and inactive member are still allowed.
- Run-log tests from A11.1 stay green; a new test covers the runs list under OWN with a run that has
  rows from two users.
- Negative controls, each seen red: remove the ACTIVE check from each helper caller, and revert the
  runs list filter.

## Done when

- The six items in "In", the route fixes R1, R2, R3 and R5, and phases 5 to 9 are merged, each with
  tests and negative controls. The front ships before the back (R5).
- R2 and the plan company check from the folder (D20, D21) ship in report-only mode. Their enforcement
  belongs to [868mrfjt5](https://app.clickup.com/t/868mrfjt5), after one week of production logs.
- The measurement passes in production.
- R4 and R6 are tracked in A11.3 ([868mrfga7](https://app.clickup.com/t/868mrfga7)).

## Unprotected routes (D4)

Mapped on 2026-11-03 against back `main` `2cfe43d4` and front `main` `30dc3025`. Every fix keeps the
callers the product uses today; a fix that refuses something ships first as a report-only log line
(caller id or `anon`, `req.ip`, route, ids, the would-refuse reason), and enforces after one week of
production logs. No route records the caller's IP today, and the rate limiter never keys by IP
(`rate-limit/rate-limit-key.resolver.ts:30-62`); `trust proxy` is 1 (`main.ts:51`), so `req.ip` is the
client's IP.

### R1. `PATCH /flow/clear-chat/:id/:sessionId` — fix now

**How it works.** `@Public()` with no access check (`flow.controller.ts:2354`). It empties the session in
the legacy `userSessionsChat` of every chat node, deletes the session key from `flyOutContents`,
clears the session's `session_state_entries`, and saves **every node of the flow** with
`saveFlowNodes`, which also invalidates the snapshot and re-syncs autotriggers.

**Callers.** The public chatbot page (`PublicChatBot.tsx:400`, anonymous or logged in), the editor
chatbot preview (`ChatBot.tsx:503`) and the dashboard chat widget (`ChatWidget.tsx:522`). None reads
the response.

**Impact.**
- Anyone with a flow id and a session key erases that session on any flow, of any tenant, published
  or not. Flow ids are in every chatbot share link. Session keys leak through the public chatbot read,
  which returns every visitor's `flyOutContents` key, and API sessions use guessable keys (`default`,
  `1234`).
- Every call, legitimate ones included, rewrites all nodes outside the save lock. An editor autosave in
  that window is lost. On a versioned flow it saves history copies as live nodes, or fails on
  `UQ_flows_nodes_live`; on dev, 41 flows would fail.

**Fix.**
1. Allow when the caller passes `resolveChatbotAccess` (the editor and dashboard read) or
   `resolveChatbotDelivery` (the public page read). Refuse with the same 404 otherwise.
2. Clear only the session: `sessionStateService.clear`, a jsonb removal of the one `flyOutContents`
   key, and a data-only update of live chat nodes. Do not call `saveFlowNodes`.
3. The public chatbot read returns only `flyOutContents[sessionId]`.

Nothing legitimate breaks: the three callers already pass the matching read.

### R2. `POST /flux/formapi-v1` — fix with a log-only week first

**How it works.** `@Public()` with optional login (`flux.controller.ts:1315`). It checks only that the
form exists; the published and internal checks were commented out on 2024-12-02 (PR #284), one month
after the form builder preview moved onto this route. It runs `query.flowId` as the form's owner and
sends every Output node's text to the caller's socket.

**Callers.** The published form pages (v2 and legacy, anonymous or logged in), the Board interface
widget, and the builder preview, which runs **draft** forms. Each sends a flow id from the form's
`activeFlows`, except legacy forms whose submit button stores its own flow list (`submitType`
`all-flows` or `specific`).

**Business rule.** KB `account-types-and-roles-prd.md:136`: internal means logged in with access to
the space. `route-role-matrix.md:59`: a published form opens for anyone with the link. PRD `:344`: "a
widget is never proof of access: the run gate must resolve the underlying resource and check access
to it".

**Impact.**
- A visitor runs a draft, unpublished or internal form anonymously. Unpublishing a form does not stop
  its runs.
- A caller runs **any flow the form's owner can run**, not only the form's flows, as the owner, on the
  flow company's credits, and reads the outputs. Form flow ids are public: the published form read
  returns them.
- A missing `formId` likely resolves to an arbitrary form under TypeORM (`findOne({ id: undefined })`).
  Confirm with a test.
- `versionId` picks any stored version; no product caller sends it.

**Fix (the rule `GET /forms/published/:id` already applies, plus the builder).**
1. `formId` is a UUID and the form exists.
2. `flowId` is in the form's flows: `activeFlows`, or `[activeFlowId]` when empty. For a legacy form,
   also the flows of its published submit-button node, if the measurement finds live ones.
3. Published and external: anyone.
4. Published and internal: logged in and `canOpenInternalForm`.
5. Draft, or internal refused by step 4: logged in and allowed to open the form in the builder.
6. Keep `isBoardRunBlocked`. Refuse `versionId`.

**Measurement.** No table stores the `formId` of a run, so the log-only week is the measurement. Also
count legacy forms whose submit-button flows are not in `activeFlows` (dev: 1, its flow deleted).

### R3. `POST /flux/run-public-flow/:id` — fix now

**Why it exists.** Added on 2024-09-02 as a credential-less run API, documented in
`docs/main-api/specific-features/external-api-endpoints.mdx:98`, whose warning at `:105` says the only
protection is the flow's `public` flag. No front, MCP or worker code calls it; the chatbot embed uses
`chatbot-api-socket`. Dev: 13 runs ever, all from the rate-limit QA on 2026-09-17.

**How it works.** No auth guard at all. It checks only `flow.public`, which is the chatbot "Published"
switch, and ignores `chatbotPublishType`. It runs as the flow's creator and returns every Output text.
An error is swallowed by an empty `catch` (`flux.controller.ts:1628` before this task), so a failure hangs until the 300 s timeout.

**Impact.** Anyone with a published chatbot's flow id runs it anonymously, including an **internal**
chatbot, which is meant to need login and space access. It spends the owner's credits and can pick any
stored version.

**Fix.**
1. Decide with `resolveChatbotDelivery(flowId, caller)`, with optional login, so an internal chatbot
   needs a logged-in member and an external published chatbot keeps working.
2. Return the error instead of the empty `catch`.

**Measurement.** Production `public-api` runs in the last 90 days on internal chatbots (expected 0), and
the number of internal published chatbots.

### R4. `POST /flux/beta-v2` — log-only first, enforce after the decision on system flows

**Why it exists.** It was the authenticated test route until 2024-10-01 (PR #252), when it became
`@Public()` and started to run as the flow's owner. It is the editor's Flow Caller and Library node
"Run" (`FlowCaller.tsx:275`, `LibraryNode.tsx:310`), and the front also posts to the **production** API
for three platform system flows (agent summary, data-input purpose, auto model) from every
environment (`FluxApiProduction`).

**How it works.** Optional login. It refuses only `public === false` for a non-owner, so a flow whose
`public` is `null` runs for anyone. `public` is the chatbot "Published" switch; every agent, library
flow and system flow is `null` (dev: 3,143 of 3,196 live flows). It runs as the company's billing owner
and returns the outputs, the tokens and the cost.

**Impact.** Without a token, anyone with a flow id runs almost any flow, charged to the owner's
company, and reads the outputs. Flow ids leak through chatbot links, published forms and the MCP.

**Fix.** Allow, in order:
1. The flow's owner.
2. A logged-in caller who can run the flow: access to its space or folder, or the library installed
   (`checkIfUserCanRunFlow` with the real caller).
3. `public === true`, with `resolveChatbotDelivery` for an internal chatbot.
4. The platform's system flows, listed explicitly, or set to `public = true` in production.
5. Refuse anything else, including an anonymous caller on a `null` flow.

"Treat `null` as not public" alone breaks the Flow Caller on a colleague's flow, every Library node and
the system-flow calls.

**Measurement.** The caller is not stored, so ship the log line first and count, for one week,
anonymous and non-owner calls on `null` flows, split by library, colleague, system flow and other.

### R5. Socket `new-user` — needs a front change first

**How it works.** `gateway.ts:60` trusts the `id` in the message: it joins `room_user_<id>` and writes
`users.socketId = <socket>`. It ignores the user the handshake verified, and the editor socket sends
no token at all (`front Socket.tsx:138`), so no socket of the editor is ever verified. The write uses
`save`, so an unknown id inserts a blank user (dev: 7 such rows).

**Impact.** With another user's id (visible to co-members and ex-members, not public), a socket
receives that user's events: run outputs, vector and scraper results, generated audio, budget and
flow-log notifications. It also redirects the deliveries that fall back to `users.socketId` (API calls,
MCP calls, cron runs), so the victim sees a hang until their next reconnect. `subscribe_to_flow` in the
notifications gateway has the same pattern for live run text.

**Fix.**
1. Front: the editor socket sends its token, as the public chatbot socket already does.
2. Back: `new-user` and `subscribe_to_flow` use the verified user and ignore a different `id`; a flow
   room checks flow access.
3. Back: `update` instead of `save`, so no user row is created.

The front ships before the back, or every editor socket stops receiving its results.

### R6. `POST /groq/chatbot/text-to-speech/:id` — a bug, not an access hole

**How it works.** Login required. The voice comes from the URL and the model from the body. Since
2025-12-12 (PR #1235) the back requires a `flowId` to bill the flow's company, and the front never
sends it, so **voice fails for everyone**, owners included. With a `flowId`, any logged-in user could
bill another company's flow, because no access check ties the caller to it.

**Impact for visitors.** An anonymous visitor gets 401. With autoplay on, the failure aborts the
socket handler, so the chatbot's reply is not shown and the typing indicator stays on.

**Fix.** The front sends `flowId`; the back checks `resolveChatbotDelivery` for that flow, uses the
flow's own voice and a server-side model, caps the text, and adds a rate limit. **D6, decided
2026-11-03: anonymous visitors of a public chatbot get voice, billed to the chatbot's owner**, so the
route becomes `@Public()` behind `resolveChatbotDelivery`. In every case, the front wraps the voice
call so a failure never hides the reply.

## Phases

**D7, decided 2026-11-03: R4 and R6 are not fixed in this task.** They move to A11.3
([868mrfga7](https://app.clickup.com/t/868mrfga7)), and their analysis stays above.

1. **Membership rule (back):** "In" items 1-6, after the production measurement.
2. **Close now (back):** R1 and R3.
3. **Form runs (back):** R2 ships report-only with the never-legitimate refusals (a `formId` that is not
   a UUID or matches no form); the access rule enforces in a second PR after one week of production
   logs.
4. **Socket (front, then back):** R5. The front sends the token on the editor socket and reaches
   production first; the back then trusts only the verified user.
5. **Form writes (back):** every form write route uses the builder rule (`canOpenFormInBuilder`) or
   `assertUserCanWriteToSpace`, so a leftover `user_spaces` row stops granting writes (D8).
6. **Docs, last:** `docs/main-api/specific-features/external-api-endpoints.mdx` (en and pt-br)
   describes the access rule of `run-public-flow` (D11).
7. **Remaining checks (back), before the docs:** every other "owner or `user_spaces` row" check in
   the flow, flux, file and folder routes; `POST /flow/clear-session/:id`; form flow ids that the
   caller cannot access (`POST /forms`, `PATCH /forms/:id`, `POST /forms/auto-populate`); folder
   reorder and move routes that write items without checking them; and the unchecked form reads
   (`GET /forms?flowId`, `POST /forms/inputs-outputs`, `GET /forms/debug/:id`) (D13).
8. **Follow-ups found in review (back), before the docs:** the MCP call checks the caller's ACTIVE
   membership in the company it names ([868mq9rjr](https://app.clickup.com/t/868mq9rjr), D19); the plan
   and slot checks of create paths use the folder's company (D20); a folder in a soft-deleted space no
   longer counts as a personal folder.
9. **Risk mitigations of phase 8 (back):** the plan check by the folder's company runs report-only when
   only the selected company would allow the creation (D21); `deleteFlow` releases the slot to the
   company the creation counted against; `POST /integrations/:provider/connect` checks the caller's
   membership in the company it names, like phase 8 does for the MCP call.

Decisions taken after phase 4, on 2026-11-03:

**D8: the form write routes come into this task.** They accepted a `user_spaces` row with no status
check, the same defect as D2.

**D9: post one short ClickUp comment per phase on this task**, without asking each time.

**D10: clearing a chat does not change deployed-version history rows.** A legacy chat that is cleared
can come back from a history row (6 flows on dev). Accepted.

**D11: the docs page for `run-public-flow` is updated in this task, as the last step.**

**D12: the socket flow room follows the agent access rule, with no creator exception.** On dev, 15
creator pairs (agents with no folder, or in another user's personal folder) lose live canvas status
but still receive results; none of those agents changed in 30 days. Accepted, and measured in
production with `etc/2026-11-03/10-BEFORE-MERGE-a11-2-q4-socket-flow-room-access.sql` before the merge.

**D13: the remaining checks come into this task as phase 7, instead of a separate A11.4.** The
`/simplify` review found about 25 more "owner or `user_spaces` row" checks; phase 5 found the form
flow-id and folder-write gaps. Each group is measured on dev and in production before it refuses.

Decisions taken on the phase 7 inventory, on 2026-11-04 (dev counts in
`etc/2026-11-03/12` to `16-BEFORE-MERGE-a11-2-q6` to `q10`):

**D14: an agent's creator who is neither the folder owner nor an ACTIVE member loses access.** On dev,
18 pairs and 14 users, none used in 30 days. Same reasoning as D12. Confirmed again on 2026-11-04 with
no creator exception: the agent rule decides by the folder, and it already does for runs, run logs and
the MCP since A11.1. The agents with no folder do not appear in the sidebar, and most are copies left
by the old `POST /flow/duplicate` without a folder, which step 7a fixed.

**D15: an ACTIVE company member without a `user_spaces` row gains the access the agent rule gives.** On
dev, 152 agent pairs and 250 folder pairs. `PATCH /flux/json/:id` and `POST /file` have no `@Roles`, so
they also require the builder, admin or owner role for JWT callers. The `/code-review` (finding 2)
moved the API-key path of `GET` and `PATCH /flux/json/:id` onto the agent rule for the key's principal
too (a user key is that user, a space key is the company owner): on dev it refuses 14 of 5,941 user-key
pairs and 42 space-key pairs, all D2 or D14 cases. A space key that reaches agents outside its own space
is unchanged and left to a product decision (on dev 23,660 of 24,272 key and agent pairs lie outside the
key's space). `CompanyRoleGuard` reads the role in the selected company, so `POST /file` also refuses a
caller who is not an ACTIVE member of their selected company. The production count
`etc/2026-11-03/17-BEFORE-MERGE-a11-2-q11-post-file-role.sql` decides whether the role requirement
stays on `POST /file` (dev: no refused upload in 90 days).

**D16: every unchecked route found in phase 7 comes in:** `POST /flow/nodes-automation/:id`,
`GET /flow/:flowId/node/:nodeId`, `POST /flow/duplicate`, `GET /flux/json/:id`, `POST /folder/add-flow`,
the space admin routes (including `POST /:id/refresh-api-key`), the entity-doc and SuperChat doc
checks, and the space-based agent lists. `GET /forms/debug/:id` is deleted.

**D17: `PATCH /forms/:id` checks only the flow ids it adds.** The editor sends the whole form on every
save, so checking stored ids would break a colleague's save.

**D18: the API key hard-coded in `GET /flux/json/:id` is not changed in this task.**

Phase 7 runs in four steps with separate files: 7a agent routes (`flow.controller.ts`,
`flux.controller.ts`, `file.controller.ts`), 7b folder routes (`folder.controller.ts`,
`folder.service.ts`, `folder-list.service.ts`, `mcp-folder.service.ts`), 7c form flow ids
(`forms.controller.ts`), 7d space admin and docs (`company_spaces.controller.ts`,
`entity-doc.access.service.ts`, `superchat-doc-search.service.ts`).

Reviews of phases 1-7, on 2026-11-04:

- `/simplify`: 13 cleanups applied (each resource loaded once per request, one rule per decision,
  clear-chat in one transaction, facets queried once). A later step made every yes/no check an id-only
  query and every batch check one query.
- `/code-review`: 10 findings. 8 confirmed and fixed with a failing test first: legacy submit-node flow
  ids bypassing D17, the API-key rule on `/flux/json/:id`, API-key detection by header, soft-deleted
  `company_user` rows still granting access (also through the workspace-folder join), `clear-session`
  overwriting a concurrent autosave, per-item move checks, the folder-scope read loading every agent,
  and the duplicated `canWriteToSpace`. Finding 10 was half a false positive: session entries are keyed
  by every node id, history versions included. Finding 4 became D20.
- `/security-review`: no HIGH or MEDIUM finding on the branch's own commits.

**D19, decided 2026-11-04: [868mq9rjr](https://app.clickup.com/t/868mq9rjr) comes into this task as
phase 8.** It is the same defect (a caller's membership in the company they name is not checked) and
reuses `hasActiveCompanyMembership`.

**D20, 2026-11-04: create paths count plan and slot limits against the folder's company, not the
selected company.** `createFlow` checked the selected company while `CompanyFlowReport` used the
folder's company; on dev, 25 ACTIVE users have 84 workspace folders outside their selected company.
Confirmed by the user on 2026-11-04. It refuses no one except by that company's own plan limit.

**D21, decided 2026-11-04: the plan check by the folder's company starts report-only.** When the folder's
company would refuse a creation that the selected company allows, the creation goes through as before
and the back writes one `Plan company (report-only): would refuse` line. The refusal turns on in the
enforcement task [868mrfjt5](https://app.clickup.com/t/868mrfjt5) after one week of production logs,
together with the form-run rule. `assertCanCreateItems` (the Vault read-only check, about 25 routes)
still reads the selected company and is left to a separate task.

## Files

- Shared rule: `back/src/app-api/folw/flow-access.service.ts`, `back/src/app-api/company/space-resource-access.ts`,
  `back/src/app-api/forms/internal-form-access.ts`, `back/src/app-api/folw/chatbot-access.ts`,
  `back/src/app-api/forms/form-run-access.ts`, `back/src/app-api/mcp_call/mcp-organization-access.ts`
- Routes: `back/src/app-api/folw/flow.controller.ts` (R1, chatbot reads, plan company),
  `back/src/app-api/flux/flux.controller.ts` (R2, R3), `back/src/app-api/gateway/gateway.ts` and
  `back/src/temporal/notifications.gateway.ts` (R5), `back/src/app-api/forms/forms.controller.ts`,
  `back/src/app-api/folder/folder.controller.ts`, `back/src/app-api/folder/folder.service.ts`,
  `back/src/app-api/file/file.controller.ts`, `back/src/app-api/company_spaces/company_spaces.controller.ts`,
  `back/src/app-api/entity_docs/entity-doc.access.service.ts`, `back/src/app-api/mcp_call/mcp_call.controller.ts`,
  `back/src/app-api/integrations/integrations.controller.ts`, `back/src/app-api/executions_logs/execution_logs.service.ts`
- Front: `src/components/Socket/Socket.tsx` (R5)
- Tests: one real-Postgres integration spec per group, for example `space-resource-access`,
  `agent-routes-access`, `folder-routes-access`, `form-write-access`, `formapi-run-access`,
  `chatbot-public-routes`, `socket-user-binding`, `mcp-call-caller-membership` and `flow-plan-company`
- Production counts: `a11-2-q*.sql` and `a11-2-q*.prod.csv` beside this spec
