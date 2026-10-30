# B3.2 — A failed apiCaller keeps its typed request body

**Goal:** when an `apiCaller` or `mcpNode` run fails in the worker, the body the user typed stays in the
node.

**Card:** [868mgqxbc](https://app.clickup.com/t/9011479430/868mgqxbc), a subtask of B3. **Branch:**
`refactor/868m0vmy4` (worker), commit `b974cba`. It ships with B3's worker PR (#128).

## What is wrong

`buildFailedNodeOutputReset` in `worker/src/modules/nodes/shared/failed-node-output-reset.ts` (added by
868kbdtn5, commit `15ad819`) puts `apiCaller` and `mcpNode` in `RESPONSE_RESET_TYPES` and always sets
`jsonRequestBody = ""`. The activity merges that delta into the live `flows_nodes` row.

`jsonRequestBody` is user configuration: the node editor writes it
(`front/src/components/nodes/ApiCaller.tsx`), and the worker's success path never writes it
(`LIVE_WRITE_EXCLUDED_FIELDS` in `persist-node-outcome.ts`). One failed run therefore erases the user's
body.

The commit meant to mirror the back. The back's `clearStaleNodeOutput`
(`back/src/app-api/flux/node-output-reset.ts`) clears the body only when it is edge-fed:

```ts
const isEdgeFedBody = (data) =>
  Array.isArray(data.jsonRequestBodyData) && data.jsonRequestBodyData.length > 0;
```

Only then is the body a computed value from an upstream node.

## The fix

The worker applies the same condition. If `jsonRequestBodyData` is a non-empty array, the reset clears
`jsonRequestBody`; otherwise it leaves the field alone. `response: null` and the `text` reset do not
change.

## Tests

- `failed-node-output-reset.spec.ts` gains three cases: a typed `apiCaller` body (`jsonRequestBodyData:
  []`) is kept, a typed `mcpNode` body (no `jsonRequestBodyData`) is kept, and an edge-fed `mcpNode` body
  is cleared. The existing edge-fed `apiCaller` case still clears.
- **Negative control:** with the fix reverted, the two typed-body cases fail with `Expected path: not
  "jsonRequestBody"`, `Received value: ""`.

## Found and left out

- For `apiCaller`/`mcpNode`, the back's reset also clears `errorMessage`, `errorStatusCode` and
  `canceled`. The worker writes `errorMessage` separately on failure, so this is probably intended, but it
  is not verified.
- The worker's failure reset skips `voiceBoxNode`, `imageGenerator`, `commandContentNode` and
  `audioReaderNode`, which the back clears.
- `pnpm install --frozen-lockfile` fails on worker `origin/main`, because `pnpm-lock.yaml` lacks
  `@google-cloud/documentai`.

## Dev verification (2026-10-13)

- **Already on dev:** worker `develop` already applies the same rule, but `main` does not, so production still has the defect. This task fixes it in production through B3's worker PR; the dev cherry-pick was skipped.
- **Agent:** "B3.2 dev check — failed apiCaller keeps typed body (868mgqxbc)": starter → `apiCaller` POST to `https://httpbin.org/status/500` with the typed body `{"keep":"this typed body"}`.
- **Result (runs `ae04ec5e` and `ab7efedb`, the second after the worker rollout to `17e7afb`):** the run fails with HTTP 500, and the live row keeps `jsonRequestBody` = `{"keep":"this typed body"}`, with `response: null` and `text: ""`.
