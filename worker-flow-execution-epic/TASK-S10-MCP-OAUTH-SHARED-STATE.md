# S10 — Keep the MCP OAuth state where every back replica can read it

**Goal:** a user can connect an MCP integration through OAuth whichever back replica serves the
callback.

**Depends on:** nothing. **Blocks:** running the back on more than one replica without random
OAuth failures. **Added 2026-11-04** from the replica audit of that day. ClickUp: [868mrv6cr](https://app.clickup.com/t/868mrv6cr).

## Why

The MCP OAuth flow keeps its state in the memory of the process that started it. Read against back
`main` `95533b9f` on 2026-11-04:

1. `mcp_oauth.service.ts` keeps the PKCE state in a module-level `Map` (`pkceStateStore`). The
   discovery and client-registration results are also in-process maps (`discoveryCache`,
   `registrationCache`).
2. The callback looks the state up in that map. When the callback lands on another replica, the
   lookup fails and the user sees "Invalid or expired state".
3. The production target group of the back (`enhancedai-tg-prod`) has stickiness **off**
   (`stickiness.enabled = false`, read on 2026-11-04). Nothing keeps the callback on the replica
   that started the flow.

With two replicas, about half of the OAuth connections can fail. Production runs two replicas every
day (`TASK-E3B-SINGLE-DELIVERY.md`, **Corrected premise**).

## Scope

**In.** The PKCE state goes to Redis, keyed by the OAuth `state` value, with the same expiry the
map applies today, and it is deleted when the callback consumes it. A second callback with the same
`state` is refused.

**In.** `discoveryCache` and `registrationCache` either move to Redis or are confirmed to be safe to
rebuild on any replica. Record which one in the PR. A cache miss that only costs one more request
is safe.

**Out.** Turning on load-balancer stickiness. It would hide this defect, it would also pin sockets
and runs to one replica, and a scale-in or a deploy would still break flows in progress.

## Verification

- **Negative control (required).** Start the flow on one back process and send the callback to a
  second one. On `main` today it fails with "Invalid or expired state". After the change it
  succeeds. Revert the change and watch the test fail.
- A replayed callback with the same `state` is refused.
- An expired state is refused with the same user-facing message as today.

## Done when

An MCP OAuth connection succeeds when the callback lands on a different replica from the one that
started it, and the state is single-use and expires as it does today.

## Files

`back/src/app-api/mcp_call/mcp_oauth.service.ts` (`pkceStateStore`, `discoveryCache`,
`registrationCache`) · the back's Redis client module

## Outcome

Back PR [#2104](https://github.com/enhancedai-com/Flux-Prompt/pull/2104), branch `fix/868mrv6cr`,
merged to dev on 2026-11-10 (`c30da186`). It passed QA on dev the same day and waits for the production deploy.

**Design.**

- `McpOAuthStateStore` (`src/app-api/mcp_call/mcp-oauth-state.store.ts`) writes the state to
  `mcp:oauth:state:<state>`, encrypted with `encryptCredentials`, with `SET PX
  MCP_OAUTH_STATE_TTL_MS` (10 minutes, as before).
- The callback reads it with `GETDEL`, so the state is single-use. Valkey is 8.0.1 in dev, staging
  and prod, which supports `GETDEL`.
- `discoveryCache` and `registrationCache` stay per process. The callback uses
  `resolvedConfig.clientId` from the state, so a cache miss on another replica costs one request
  and nothing else.
- When Redis fails, the store logs it and the callback redirects with "The connection could not be
  completed right now. Try connecting again." instead of a raw 500. A state that cannot be
  decrypted is logged as `mcp_oauth_state_unreadable`.

**Verification.**

- Seven specs, each negative-controlled. The cross-replica spec uses a real Redis when
  `REDIS_TEST_URL` is set and an in-memory shared double otherwise.
- A local run with three back processes: start on A and callback on B succeeded, a replayed
  callback was refused, and a replica on another Redis was refused.
- On dev, two in-app OAuth connections to `https://mcp-dev.fluxprompt.ai/mcp` succeeded on 2026-11-10, one from a password account and one from an Apple account. Each wrote its `mcp_integrations` and `user_integrations` rows in the same second, and the dev logs show no state error.

**Reviews.** `/simplify`, `/code-review` and `/security-review` ran on the branch; the security
review had no findings. Follow-ups that were noted and left out of scope:

- The MCP OAuth state is not bound to the browser session (pre-existing).
- `OAuthStateService.consume` in the integrations module reads and then deletes, which allows a
  replay race (pre-existing, other module).
- The shared `REDIS_CLIENT` has `maxRetriesPerRequest: null`.
- MCP access tokens are never refreshed; the user reconnects when the provider token expires.

**Deploy.** Read the prerequisite in the PR body before each environment's deploy.
