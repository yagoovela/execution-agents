# B1 — test results draft (not published)

Draft started 2026-10-06. Plain text, ready to paste into ClickUp once the dev checks are filled in.
Nothing below has been posted.

---

## 868mdtvj4 — Agent and chatbot plan limits: clear plan-limit message

Before
- When the plan limit was reached, creating or duplicating an agent in the app showed "Something went wrong". The real plan-limit message was replaced by a generic error.

After
- The app opens the plan-limit dialog with a clear message, for example "You have used all 5 agents your Starter plan includes. Upgrade to keep building." This applies to create, duplicate and chatbot creation. Every other error keeps its previous message.

Evidence
- Local, automated test on a real database: 5 simultaneous creates on a plan of 3 create 3, and the other 2 receive the plan-limit refusal with the plan sentence. A duplicate at the limit gets the same refusal. With the fix removed, the three checks fail (the refusal never reaches the caller).
- Validated on dev (2026-10-06), on a test account moved to Starter (5 agents / 3 chatbots) and restored afterwards:
  - create an agent with one free slot: created (counter 4 → 5);
  - create an agent at the limit: refused with "You have used all 5 agents your Starter plan includes. Upgrade to keep building." (before: "Something went wrong");
  - duplicate at the limit: same message;
  - create a chatbot at the limit: refused with "You have used all 3 chatbots your Starter plan includes. Upgrade to add more.";
  - the counter never moved on a refusal; the account matches its snapshot after the restore.

Not checked
- The space-limit dialog in the browser: dropped, because there is no screen to set a space limit for now.

---

## 868mebgw7 — API callers are charged and respect their plan (part 1: agent creation)

Before
- Agents and chatbots created through the public API (`POST /integrations/agents`, with an API key or a login) did not count toward the plan, so an integration could create more agents than the plan allows.

After
- Agents created through the API count toward the same plan as the app and the MCP, with the same refusal at the limit. Agents in an organization on an unlimited plan count on the organization owner with no limit. A user without a plan is not refused. A failed creation does not use a slot, and an API chatbot is recorded as a chatbot so deleting it frees the right slot.
- Also fixed: an agent in a personal folder could be counted against a random organization the user belongs to (and escape the plan limit). It now counts against the user's own plan. On dev, 9 users on a limited plan were in this situation.

Evidence
- Local, automated test on a real database, 6 cases, each seen failing with its part of the fix removed: 5 simultaneous creates on a plan of 3 create exactly 3; a failed creation releases the slot; a chatbot is counted and recorded; a user without a plan is created; an unlimited-organization member counts on the owner; a personal-folder agent counts on the user's own plan.
- Validated on dev (2026-10-06) with the API key of the same test account (Starter, restored afterwards):
  - one free agent slot: created through the API (counter 4 → 5);
  - at the limit: refused with "You have used all 5 agents your Starter plan includes." (counter unchanged);
  - a chatbot at the limit: refused with the chatbot message;
  - a chatbot with one free slot: created, counted as a chatbot (2 → 3) and recorded as a chat;
  - deleting both API-created items in the app freed their slots (5 → 4, 3 → 2).

---

## 868mebgw7 — API callers are charged and respect their plan (part 2: clear refusal on /flux/api-v2)

Before
- When a run through `/flux/api-v2` was refused (space limit reached, plan or trial exhausted, no access to the agent), the refusal happened only after the run was queued. A caller waiting for the answer got a 500 error, and a caller using a callback URL got "202 accepted" and then an error callback. A failed execution was recorded each time.

After
- The checks run before the run is queued. The caller gets the refusal at once with the right status (402 for a limit, with the same structured body as the app; 403 for no access), with or without a callback URL, and no execution is recorded. Nothing new is refused: only when and how the existing refusal is returned changed.

Evidence
- Local, automated test on a real database: a space at its limit answers 402 and nothing is queued or recorded; a user without access answers 403 and nothing is queued; a space under its limit queues the run. With the new check removed, the two refusal cases fail.
- Validated on dev (2026-10-06) with an API key on an agent in a test space whose limit was set below its usage (800 vs 855) and restored afterwards:
  - before the new version was live: 500 with an execution id, and a failed execution recorded;
  - with the new version: 402 "This space has used its monthly limit of 800 FluxTokens…" at once, both without and with a callback URL, and no execution recorded.

Still open (planned in the task)
- Runs started through the API: trial tokens for users without a plan, the right account for the trial decrement, space API keys limited to their space, `/open-ai/get-completion` and `/flux/batch-process` access checks, and failed worker charges.
