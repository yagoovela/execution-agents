# S5 — Authorise the claim check, do not just guard it

**Goal:** a claim-check key can only be redeemed by the run it belongs to.

**Depends on:** nothing. **Severity:** high (review §3.1). Standalone — ship whenever.

## Why

`/worker/get-payload` validates a **prefix and nothing else**:

```
if (typeof body.key !== 'string' || !body.key.startsWith('node-exec/')) throw ...
const stream = await this.awsService.getFile(body.key);
```
(`worker.controller.ts:99`, still true on `origin/production` as of 2026-09-09)

There is no check that the key belongs to the caller's run, tenant, or anything else. Any holder of
the internal API key can read **any** node output of **any** customer, by key.

The route is behind `InternalApiGuard`, which is the right boundary and should stay. But it
is a **single shared secret**, and this epic puts that secret on every worker replica — the blast
radius grows with the fleet, and "we trust everything inside the perimeter" gets weaker with every
host added to the perimeter.

### What the obvious fix does not fix

The key is `node-exec/{execId}/{sanitised nodeId}-{input|output}.json` (`claim-check.ts:43-49`).
**`execId` and `nodeId` are inside the key.** So "the caller declares which run it is acting for and
the endpoint refuses when that disagrees with the key" adds **no authority at all**: a holder of the
shared secret reads both values out of the victim's key and declares them back. `/worker/store-payload`
is worse — it already receives `execId` and `nodeId` and *builds* the key from them
(`worker.controller.ts:86`), so there is no independent key to disagree with, and whatever the caller
declares simply *becomes* the key.

This task therefore does two separable things, and the split matters because only the second one is
authorisation:

1. **Bind the key to stored data** — validation. Kills forged, guessed, enumerated, truncated and
   path-traversing keys, and keys for runs that no longer exist.
2. **Bind the caller to a run** — authorisation. Needs something the caller cannot forge.

## Decisions taken before implementation

**D28 (new, recorded in `PLAN.md` §7): the worker does not get direct S3 access.** Review §2.4 argued
it should, which would delete both endpoints and supersede this task. Answered 2026-09-09: **no.** The
back stays the sole holder of the S3 credential, and the two endpoints stay — they are the only place
where "this key belongs to this run" can be enforced at all. Handing the worker the back's own S3
credential is the same decision by another name: it reduces the number of secrets, not the reach of
each one, and it deletes the enforcement point. §2.4's real argument is coupling and latency, not
security; it becomes its own task, and the measurement below shows the coupling costs almost nothing
today (6 offloads in 3417 node executions on dev).

**Never trust the declared values.** The endpoint derives `execId` and `nodeId` **from the key** and
validates the derived pair. The values the caller declares are recorded in the refusal log only, so a
refusal can be read as *"declared X, key said Y"* — which is what tells a bug from an attempt.

**`runToken`, without propagation.** The back mints a run-scoped token when it dispatches the
activity; the worker carries it in `ExecuteNodeActivityProps` and presents it on both endpoints. There
is deliberately **no chain propagation** in this task, because there is nothing to propagate: checked
on `worker@origin/main` 2026-09-09, the worker executes no sub-flow at all — no `parentRunId`, no
`startChild`, and no `fluxBox` / `libraryNode` / `flowCaller` / `arrayNode` module. Sub-flows still run
in the back's legacy engine. Carrying the token down the chain is a **Done-when line of `S1`** (which
owns the `parentRunId` chain under D13) and of `B6` (which owns the child workflow under D17). This
keeps S5 standalone.

## Scope

**In.** Derive `execId`/`nodeId` from the key; confirm a `node_executions` row exists for that pair
whose `__claimRef` envelope is exactly the requested key. Refuse otherwise.

**In.** `/worker/store-payload` gets the inverse bind: the run row for `(execId, nodeId)` must already
be open before a payload may be written into its key.

**In.** `runToken` on both endpoints, per the decision above. It is minted where the row is opened —
the worker only ever `UPDATE`s `node_executions`, never inserts, so the back is the sole writer of the
row's creation and the only place a token can come from. It cannot hang off `execution_logs`:
**1937 of dev's 3419 node executions have no `executionLogId` at all, and every one of the rows
carrying a claim envelope today is among them**, so anchoring the token there would refuse 100% of the
current large-payload traffic. It anchors on the `node_executions` row instead — the same row the bind
already reads, so both checks cost one query. Rows written before the column exists carry a null token
and are held to the bind alone; that allowance shrinks to nothing as retention ages them out, and it is
stated rather than hidden.

**In.** A single `parseClaimCheckKey` next to `claimCheckKey`, so the parse rule has one home. Five
back-side readers resolve `__claimRef` directly through `AwsService` without touching these endpoints —
`execution_logs.service.ts:374`, `flux.service.ts:509`, `node-executions.service.ts:51`,
`prefetch/load-outputs-by-refs.ts:45`, `prefetch/assemble-final-outputs.ts:55`. They are **not** in
scope (the back reading its own data for an authenticated user), but "a malformed key fails closed"
is only true of the system if the parser is a shared helper they can adopt later. Put it in
`claim-check.ts`, not in the controller.

**In.** The `nodeId` contract, below.

**Out.** Replacing `InternalApiGuard` or introducing per-worker credentials. **Out.** Chain
propagation of the token (S1 / B6, above). **Out.** Migrating the five direct readers.

## The nodeId contract

`claimCheckKey` sanitises the node id — `replace(/[^a-zA-Z0-9_.-]/g, '_')` (`claim-check.ts:47`) — and
that is lossy. Any rule comparing a node id against one recovered from a key therefore refuses a node
whose id contains anything outside that class. Measured, and then closed by contract rather than by
hope:

| # | Producer | Shape | Charset |
|---|---|---|---|
| 1 | canvas, main path — `front/src/util/myFunctionsCoreDisplay.tsx:76-79` | `${type}_${Date.now()}_${Math.random().toFixed(4)}` | safe |
| 2 | FormBuilder — `front/src/views/FormBuilder/FormBuilder.tsx:487` | same `getNodeId` | safe |
| 3 | copy/paste — `front/src/views/CoreNodeDisplay.tsx:1335`, `CoreNodeDisplaySpaces.tsx:1237` | `${id}-copy`, chainable | safe, but introduces `-` |
| 4 | file drop — `front/src/hooks/useExternalFileDrop.ts:110,162,243,318` | `${type}_${crypto.randomUUID()}` | safe |
| 5 | caller-supplied id — `myFunctionsCoreDisplay.tsx:104` (`type.id \|\| getNodeId(...)`) | external | unvalidated |
| 6 | **MCP `add_node`** — `back/src/app-mcp/dto/mcp-write.dto.ts` (`node: @IsObject() Record<string, unknown>`) + `mcp-write.service.ts:238-241` | **client-supplied, collision-checked only** | **arbitrary** |

There is no id contract anywhere in the workspace. The only id rule that exists is
`assertGlobalStarterIdConvention` (`mcp-write.service.ts:1715-1724`), which merely requires a substring
on `globalStarter`. No test asserts a charset. Producer #1 is safe **by accident**.

**Introduce `NODE_ID_PATTERN = /^[A-Za-z0-9_.-]{1,128}$/`** — deliberately the same class
`claimCheckKey` preserves, so that **sanitising a valid id is the identity function**. That is what
makes a false refusal impossible by construction rather than by measurement. Then:

- `getNodeId` becomes the only front producer, with a unit test asserting the pattern.
- Copy/paste goes through a `deriveCopyId(baseId)` that returns a valid id and stops the `-copy-copy`
  chain (numeric suffix instead).
- `@Matches(NODE_ID_PATTERN)` on the node id in `AddNodeDto`, with a message that says *why* — the
  claim-check key is derived from the id. This closes producer #6 for new writes only; nothing
  existing breaks.
- `parseClaimCheckKey` gets a round-trip test and closed cases: no prefix, no `/`, unknown field, an
  id ending in `-input`, `..` in the path, truncated.
- Comparison is **sanitised-vs-sanitised**, so legacy ids outside the pattern still resolve.

**Hazard to keep in mind:** in several places the "source id" is the composite `nodeId$handle`
(`fluxBox_1$out` — `worker/src/modules/nodes/shared/validation/resolve-edge-data.ts`). `$` is
sanitised too. If any path passes a composite where a node id is expected, the parse degrades
silently.

## Measurement (§3.3.2) — taken 2026-09-09 on dev and staging

Prod was deliberately **not** measured: the credentials for the prod bastion are not held by the
implementer, and the requester chose to proceed without them. Dev and staging are aligned with prod
in schema and code; prod differs in volume. Recorded so the omission is legible rather than silent.

| | dev | staging |
|---|---:|---:|
| `node_executions` | 3417 | 15 |
| rows with a null `execId` | 0 | 0 |
| `nodeId` outside `[A-Za-z0-9_.-]{1,128}` | **0** | **0** |
| `nodeId` longer than 128 | 0 | 0 |
| `__claimRef` envelopes | **6** | 0 |
| envelopes with a valid prefix | 6 | — |
| **bind passes** | **6 / 6** | — |
| **bind fails** | **0** | — |
| envelopes that depend on sanitisation | 0 | — |
| `flows_nodes` rows | 41206 | 39317 |
| `node_id` outside the pattern | **0** | **0** |

**80523 nodes, 3432 executions, zero charset violations, zero false refusals.** Classifying dev's
18991 distinct node ids also shows **three generations** of the front generator, all accidentally
safe: 11327 in today's format, 7647 in an older `${type}_${Math.random()}` format with the full float
(`varInputNode_0.11201825533878806`) plus `flow-global-starter_…`, hand-authored template ids
(`img-ideogram-v3turbo`) and perf-test ids; 14 from the file drop, 3 from copy/paste. Longest id
outside today's format: 41 characters.

Two honest limits. The measurement covers **stored** data, and producer #6 is about **future** ids —
it says the hole has not been exercised yet, which is exactly why closing it now is cheap. And 6
envelopes in 3417 executions says the large-payload path almost never runs, so its regression case has
to be **constructed**, not found.

## The flag

Reuses the existing mechanism rather than an env var: the `feature_flags` table
(`back/src/entities/feature_flag.entity.ts`), `PATCH /feature-flags/:key` behind
`JwtAuthGuard + InternalStaffGuard`, and the admin screen at
`front/src/views/AdminDashboard/FeatureFlagsPage.tsx`, already in the nav. **No new env var**, so
§3.3.5 is not triggered.

Key `claim_check_authz_enforce`, inserted by migration (`setEnabled` 404s on an unknown key — it does
not upsert). The flag is a boolean, so it carries two modes, not three:

- **off (default)** — compute the decision, **serve the payload anyway**, log *"would have refused,
  reason, key, declared"*. The measurement window.
- **on** — enforce.

`off` is a window with a deadline, not a resting state: the vulnerability is open while it is off.
Ship off, read the log, flip on in a separate deploy per §3.2.

**Fail-closed dominates the flag.** `isEnabled` swallows a read error and returns `false`
(`feature-flags.service.ts:21-26`), which would mean "log-only" when the database is unreachable. That
is harmless here, because the bind itself is a query: if the database is down the decision cannot be
computed, and an uncomputable decision **refuses**, flag or no flag. The flag only decides whether an
*already computed* refusal is acted on. Stated explicitly because it is subtle and invites a wrong
"optimisation" later.

**Caching.** `isEnabled` queries per call today. Add a few seconds of in-process cache, invalidated on
`setEnabled` so a toggle from the admin screen takes effect immediately rather than after the TTL.

## Admin screen — driving the list from the API

The page's list is hardcoded (`FeatureFlagsPage.tsx:26-33`). Driving it from `GET /feature-flags`
requires care, because the API is not currently shaped for it:

- **There is no `label`.** The entity has `key`, `enabled`, `description`; the page supplies `label`
  itself. Deriving a label from the key would rename the existing switch from "Node cancellation" to
  something generated — a visible regression on a live admin screen. Add a `label` column and backfill
  it.
- **`maintenance_banner` is deliberately absent from the list.** The key exists
  (`front/src/service/FeatureFlagsService.ts:3`) and drives `isMaintenanceBannerEnabled` in the store,
  but it is not rendered. An API-driven list would expose it as a toggle for the first time — an
  unintended behaviour change. Add an `adminVisible` boolean and backfill `maintenance_banner` as
  **false**, preserving today's screen exactly.
- **`description` is nullable** and is rendered unconditionally. Render `label ?? key` and
  `description ?? ''` so a row can never come out blank.
- **`GET /feature-flags` is behind plain `JwtAuthGuard`**, so any signed-in user can already enumerate
  keys. Moving labels and descriptions into the table widens what that enumeration returns. Accepted,
  and noted; narrowing the `GET` would break the store's maintenance-banner read and is not in scope.

## Verification

The three layers, all required — no gap left for the error paths.

**1. Contract tests.** `back` and `worker` have no shared build graph, and the claim-check contract is
already duplicated by hand: `ClaimRef` is declared twice (`back/.../claim-check.ts:13-17` and
`worker/.../resolve-claim-ref.ts:6-10`) and `CLAIM_CHECK_THRESHOLD_BYTES` is read twice
(`claim-check.ts:9-11`, `persist-node-outcome.ts:3-4`). This task widens the contract, so a mocked
unit test on each side would pass while the two sides disagree. One fixture of canonical
request/response shapes and key cases, committed identically in both repos with a comment naming the
other copy, and a test in each repo asserting its own code produces and accepts exactly that. D1
(shared package) stays open; this is the cheap version that fails loudly meanwhile.

**2. Integration, back, against a real Postgres.** The bind *is* a query, so mocking the repository
would stub the collaborator the defect lives in — forbidden by §3.3.1. Use the existing
`docker/devdb/docker-compose.devdb.yaml`. This is where the negative control lives: two real runs, request the
other one's key.

**3. Unit, per side.** `worker.controller.spec.ts` **does** exist — an earlier draft of this spec said
it did not, which was wrong. It covers `storeImage` and the billing routes and has never touched the
claim-check ones, so the new coverage is a sibling file rather than an edit: get-payload happy path ·
another run's key refused · a key with no `node_executions` row refused · malformed, truncated,
prefix-less and `..`-bearing keys refused · the refusal logged with context; store-payload happy path ·
a pair with no open row refused. Plus `claim-check.spec.ts` for the parse round trip, the closed cases,
and sanitise-is-identity, and `claim-check-authz.service.spec.ts` for the decision branches. Worker:
extend `resolve-claim-ref.spec.ts` (new request body, and a 403 becoming `SystemError`) and
`persist-node-outcome.spec.ts` (offload still works). Front: a `getNodeId` pattern test.

**4. Cross-service E2E — run, not deferred.** A constructed >256 KB payload through the real stack.
It was brought back for a decision before closing, the decision was to run it, and it is recorded
under *As shipped* below.

Each new test gets §3.3.1's negative control: break it, watch it go red, restore, and state which
failure was observed.

## As shipped (2026-09-09)

Three branches, all `fix/868m0vfhf`.

**back** — `8851c161` the run token · `6f48c745` the flag and the admin columns · `41683b5e` the node
id at the MCP entry point · `d3b8c046` the Postgres integration suite. (`a2c6bf75` the parser and
`19209aa8` the bind landed earlier.)
**worker** — `a4c56f3` the token on both routes. (`d0cbe30` execId/nodeId earlier.)
**front** — `8b62032c` one id producer and the API-driven flag list.

What differs from the plan above, and why:

- **The token is verified, not just carried.** `acceptsToken` accepts a row whose stored token is
  null — that is the in-flight allowance, stated here rather than hidden — and otherwise requires an
  exact match, compared with `timingSafeEqual`. A pair that resolves to several rows is authorised by
  any one of their tokens, because a retry writes a second row for the same `(execId, nodeId)`.
- **The refusal log never carries a token.** It records how many rows matched and how many of those
  carried a token. A log that quoted the token would be the leak the token exists to prevent.
- **The node id is validated in `mcp-write.service.ts`, not the DTO.** `AddNodeDto.node` is an
  untyped `Record`, so class-validator has nothing to hang `@Matches` on; the check sits next to the
  `assertGlobalStarterIdConvention` it resembles, before anything is persisted.
- **The front's producer moved to its own module.** `front/src/util/nodeId.ts` holds `getNodeId`,
  `deriveCopyId` and the pattern; `myFunctionsCoreDisplay.tsx` re-exports so no caller changed.
  `CreateShorthandFlowModal` had its own inline generator with a different alphabet and now calls the
  shared one. The contract fixture is copied into `front/src/util/` — three byte-identical copies,
  one test in each repo.
- **`plannedFields` is gone from the contract.** Both routes now list `runToken` in `requiredFields`.
- **The flag cache is per replica.** Five seconds, written through on a toggle, so the replica that
  served the toggle is correct immediately and the others within the window.

Negative controls observed (§3.3.1), all restored green afterwards:

| what was broken | what went red |
|---|---|
| `acceptsToken` forced to true | 4 back unit tests |
| the null-token allowance inverted to a refusal | 8 back unit tests |
| the token written into the refusal context | 1 back unit test |
| `AsyncLocalStorage` replaced by a module variable | 3 worker tests, including the concurrency case |
| the offload no longer presenting the token | 2 worker tests |
| `assertNodeIdRedeemable` removed | 2 back MCP tests |
| sanitisation removed from `getNodeId` | 1 front test |
| the legacy repair removed from `deriveCopyId` | 1 front test |
| `adminVisible` ignored by the admin page | 1 front test |
| the label's key fallback removed | 1 front test |
| **`authorizeRead` short-circuited — the endpoint as it was** | **5 of 10 integration tests, including run A reading run B's stored payload** |

The last row is the demonstration the task exists for: it is what the endpoint did before this
change, run against a real Postgres rather than argued about.

### The >256 KB end-to-end run — done 2026-09-09, no longer deferred

Deferred by agreement, then run rather than assumed. The local stack (`docker/devdb/docker-compose.devdb.yaml`
for app_db, redis and Temporal) with the **back and the worker both running this branch**, against a
real S3 bucket. A `counterNode` was inflated to 300 KB of node data and executed through
`POST /flux/execute-single-node`.

The whole chain worked on the first run: the back offloaded the input to S3 and stored the envelope,
minted a token, and passed it as the workflow's ninth argument
(`06d39929-…`, byte-for-byte the `runToken` on the row); the worker bound it to the activity's async
context, presented it on `/worker/get-payload`, and the node **completed**. Zero refusals logged.

Then the question §3.3.2 actually asks — *does enforcement refuse real traffic?* — with
`claim_check_authz_enforce` **on**, the same 300 KB run completed again, again with zero refusals.
The flag flipped through the admin API and took effect on the next request, so the write-through
cache behaves as designed.

With enforcement on, at the HTTP boundary and with a **valid internal API key** — the actual threat
model:

| request | result |
|---|---|
| run A redeems its own key | `200` |
| run B presents run A's key with B's own token | `403` |
| run B declares A's execId and nodeId, presents A's key and B's token | `403` |
| run A's key with no token at all | `403` |
| a key nobody ever stored | `403` |
| `node-exec/../../etc/passwd` | `403` |
| run A writes under its own pair | `200` |
| run B writes into run A's pair | `403` |
| a write into a run that was never opened | `403` |
| a write whose node id the key could not carry | `403` |

And the vulnerability itself, shown rather than described: with the flag **off**, run B presenting
run A's key received `200` and **300000 bytes of run A's payload**, while the log recorded
`would have refused` naming both sides. That is the endpoint's behaviour before this task, and the
same request is `403` with the flag on.

Grepping the whole API log for either run token returns **zero** occurrences.

The stack was torn down afterwards, the inflated node restored, and the flag put back to off.

Running the integration suite needs the local Postgres (`pnpm infra:up`); the suite says so when it
cannot reach one, rather than skipping and reading as protection.

## On dev

Merged into the three dev branches on 2026-09-09: back `master` (`792e703f`), worker `develop`
(`050490c`), front `main` (`0f50cb40`). Each merge was made in its own worktree against a freshly
fetched origin, type-checked, and run against the suites that cover the merged files — the back at
360 tests across 10 suites including the Postgres integration suite, the worker at 18 suites / 125
tests for the workflow and shared modules (its 8 remaining red suites are dev's own, a constructor
that gained five parameters without its specs following), the front at 12 component tests and 10
unit tests over the touched areas.

Three conflicts were worth recording, because in each one the dev line had moved:

- **The admin flag list.** Dev has already built the API-driven screen this task proposed, as a new
  page under `features/admin-panel` with React Query hooks, a `humanizeKey` fallback and
  `maintenance_banner` filtered by key. It is on dev only — not staging, not production — so the old
  `views/AdminDashboard` page still needs the change for the environments S5 targets. Dev's
  structure won: the merged old page uses dev's query hooks and derives its rows from the query,
  with `adminVisible` doing the filtering. Both pages and both test files now coexist.
- **`FeatureFlagsService`.** Dev's banner fields (`message`, `startsAt`, `endsAt`,
  `showEndsAtInMessage`) and its `update()` replacing `setEnabled()` were kept; `label` and
  `adminVisible` were added alongside, and the flag cache's write-through moved into `update()`.
- **The workflow.** Dev added a `LARGE_MEMORY` case while this branch was adding the run token. The
  case was kept intact and `largeMemoryActivity` now receives the token too — it resolves claim refs
  like the others. An audit after the merge re-checked all 21 activity call sites: every activity
  that can touch a claim ref carries the token, and none of the ones that cannot do.

The merge also exposed a real defect in this branch's own work: `myFunctionsCoreDisplay` re-exported
`getNodeId` from the new module without importing it, so its own call site had no binding. The front
has no `typecheck` script on the dev branch and its pinned TypeScript is 4.9.5 against a TS5
`tsconfig`, which is why it went unseen — it was found by running a TS 5 compiler by hand and is
fixed in the merge.

The state stays `review`, not `shipped`: this table calls a task shipped when it is in **production**,
and production is still a PR away.

The behaviour is documented for the team in `docs`, on branch `docs/868m0vfhf`:
`main-api/specific-features/claim-check-authorization.mdx` — the run token and why declaring the
execId and nodeId would have added nothing, the five refusal reasons, and what the flag does in each
position (off: served, logged as `would have refused`; on: `403`), including the one case that
refuses regardless.

## Known gap — nodes that execute inside the API

Validated on dev on 2026-09-09 with enforcement **on**, against a real run of the agent
`7a5cc1d5-19ab-4b25-a4ed-1e523c174d7a`. The run had two nodes and they took different paths:

| node | execId | executed | runToken | claim refs |
|---|---|---|---|---|
| `textBox` | `4eaa84c9-…` (the runId) | inside the API | **null** | input + output, 288000 chars |
| `commandTextNode` | `65169c64-…` | worker / Temporal | `2ff7df55-…` | input + output |

The worker path is proven end to end under enforcement: the token is the workflow's ninth argument
and matches the row byte-for-byte, it reaches `getNodeInfo`, `textGenerator` and
`generateExecutionLogs` and none of the four activities that cannot touch a claim ref, and the
workflow completed. The same node with the flag off behaved identically (`4d43af64-…`, token
`8dfd034a-…`). So a legitimate large payload passes with enforcement on — the question §3.3.2 asks.

The gap is the other row. A node that executes inside the API — `textBox` here, and any type
`isTemporalNode` does not list — is written by
`flux.service.ts:1922`, which calls `serializeWithClaimCheck` and so **creates a claim ref, but
inserts no `runToken`**. The error-path insert at `flux.service.ts:1851` has the same omission. Three
of the four writers mint a token; this fourth one was missed.

With a null stored token `acceptsToken` accepts anything — the fallback that keeps an in-flight run
from being refused mid-deploy. For these rows it is not transitory, so enforcement degrades to the
bind alone: a holder of the internal API key can still redeem that key, which is the hole this task
set out to close. It is closed for worker nodes and open for in-API nodes.

**Addendum, 2026-09-09 — this is being closed in this task, not deferred.** It was briefly left as a
follow-up and then pulled back in, because the Done-when of this very task says a key can only be
redeemed for its own run, and a key produced by an in-API node does not satisfy it. It is not new
scope; it is scope this task left incomplete after finding three of the four writers.

What changes: `recordLegacyNodeStart` (`flux.service.ts:1889`, the insert at `:1922`, one call site)
and `recordInApiNodeError` (`:1760`, the insert at `:1851`, three call sites) mint a `runToken` like
the other three writers. No caller changes — nobody presents these tokens. The two updates that
later write an output claim ref (`:1984`, `:2064`) keep whatever token the row already carries.

Why no false refusal is possible, checked before writing it: both worker sites that resolve a claim
ref (`activities.service.ts:357`, `fetch-node-row.ts:53`) resolve their own `(execId, nodeId)` row
and never another node's, and an in-API node reads S3 directly rather than through
`/worker/get-payload`. The dev run of 2026-09-09 shows this in real data: the text generator
consumed the 288000 characters the `textBox` produced, but its input was written under **its own**
key (`node-exec/65169c64-…/commandTextNode_…-input.json`), never the `textBox`'s. So no legitimate
HTTP redemption of an in-API key exists, and requiring a token on them refuses nothing real.

Proof obligation: the Postgres integration suite gains a case built on a row created the way the
in-API path creates one — refused without a token, refused with another run's token, served with its
own — and the mint is reverted once to watch it go red (§3.3.1).

**A second thing worth knowing before trusting the token.** It travels in the workflow history in
plain text, and `temporal-ui-dev.fluxprompt.ai` answered a request for a full history with no
credential at all — no cookie, no header. If that host is reachable from outside the network, the
token is not a secret in dev: read it from the history, and with the internal API key the claim
check is satisfiable. Worth confirming what the UI exposes in staging and production before the flag
is read as protection there.

## Follow-up — how far does a compromised worker actually reach?

Out of scope here, and recorded so it is not mistaken for something this task covers.

The run token stops a holder of the internal API key who has nothing else. It does not stop the
worker itself, and the worker holds more than the key:

- **The database.** `TYPEORM_USERNAME` and `TYPEORM_PASSWORD` are in its environment and it runs raw
  SQL (`databaseService.pool.query`). It can read `node_executions` for any run — the payloads small
  enough to sit inline, and the `runToken` column itself. Reading run B's token and then presenting
  it is a legitimate-looking redemption.
- **S3, possibly the same bucket.** `/worker/get-payload` reads from `AWS_S3_BUCKET_NAME` using
  `AWS_S3_ACCESS_KEY_ID` (`app-api/aws/aws.service.ts`). The worker's env schema requires those same
  four variables — not optional — and already uses them in `storage/s3-upload.service.ts` and
  `vector/aws.service.ts`. If dev and production point both services at the same bucket, the worker
  reaches every claim-check object directly through the SDK, with no endpoint and no token in the
  way. **This contradicts the premise of D28** ("the worker gets no direct S3 access, so the two
  endpoints stay"), which was taken as settled when this task started. The variable names match; the
  deployed values were not read, because the implementer holds no AWS credentials — that is the first
  thing the follow-up must check, by comparing the two task definitions.
- **Every provider key.** OpenAI, Anthropic, Gemini, Groq, xAI, Perplexity, ElevenLabs, SerpAPI,
  ScrapingBee, Oxylabs, BuiltWith, Pinecone, Voyage, plus `INTEGRATIONS_ENCRYPTION_KEY` — the key
  that decrypts customers' stored third-party credentials — and the Slack, Notion, HubSpot and
  QuickBooks client secrets.

So the honest scope of what this task buys is narrow and worth stating plainly: it removes the
property "one shared secret is enough to read any customer's large payload" for anyone who holds
only that secret. Against the worker itself it buys little, and `INTEGRATIONS_ENCRYPTION_KEY` sitting
in the same environment means the blast radius of a compromised worker is larger than the payloads
this task is about.

**First concrete step, requested 2026-09-09: compare the keys across local, dev and production.**
For each environment, read `AWS_S3_BUCKET_NAME`, `AWS_S3_ACCESS_KEY_ID`, `AWS_S3_REGION`,
`INTERNAL_API_KEY` and the `TYPEORM_*` values as they are actually deployed — on the API task
definition and on the worker task definition — and write down, per environment, whether the two
services share a bucket, share a credential, and whether the worker's database user is the same one
the API uses. Local counts too: `docker/devdb/docker-compose.devdb.yaml` hands the worker
`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` and points both services at the same Postgres, which is
fine locally but is exactly the shape that must not be assumed for the other two. The answer decides
whether the claim-check endpoints are a real boundary or a formality, and it is cheap: two task
definitions per environment. It could not be done from this task because the implementer holds no
AWS credentials.

What the follow-up should produce, before anyone decides whether per-worker identity is the answer:
an enumeration of what the worker's credentials actually permit — which buckets, which database
grants (is it read-write on every table?), which of those secrets are shared with other services,
and which are per-environment. Only then is it possible to say whether the fix is an identity per
replica, or moving the worker's data access behind endpoints, or narrowing the grants. Per-worker
identity alone would not close the database or the bucket.

## Done when

A key can only be redeemed for a run that stored it, writes are equally bound, the caller presents a
run token, refusals are logged, malformed keys fail closed, node ids have a contract with a test
behind it, and the existing large-payload path still works.

## Files

`back/src/temporal/worker.controller.ts` (`/worker/get-payload`, `/worker/store-payload`) ·
`back/src/app-api/flux/claim-check.ts` (`claimCheckKey`, new `parseClaimCheckKey`, `NODE_ID_PATTERN`) ·
`back/src/app-api/flux/flux.service.ts:565,1561` and
`back/src/temporal/single-node-legacy/node-execution-store.ts:45,82` (the other key writers) ·
`back/src/app-api/feature-flags/*` + `back/src/entities/feature_flag.entity.ts` (flag, cache, `label`,
`adminVisible`) · `back/src/app-mcp/mcp-write.service.ts` (`assertNodeIdRedeemable`) ·
`worker/src/modules/temporal/activities/activities.types.ts` (`runToken`) ·
`worker/src/modules/nodes/shared/resolve-claim-ref.ts` ·
`worker/src/modules/nodes/shared/persist-node-outcome.ts` (**not** `persist-node-success.ts`, which
holds no claim-check code) · `front/src/util/nodeId.ts` (`getNodeId`, `deriveCopyId`, `NODE_ID_PATTERN`) · `front/src/views/AdminDashboard/FeatureFlagsPage.tsx` +
`front/src/service/FeatureFlagsService.ts` (API-driven list)
