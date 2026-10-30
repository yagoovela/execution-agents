# B3.1 — Placeholders resolve inside arrayNode loops

**Goal:** a node inside an `arrayNode` loop body receives its `{{placeholders}}` substituted, exactly as
it does outside the loop.

**Card:** [868mgqx9q](https://app.clickup.com/t/9011479430/868mgqx9q), a subtask of B3. **Branch:**
`refactor/868m0vmy4` (back), commit `387cb6f6`. It ships with B3's back PR (#2036).

## What is wrong

The main path substitutes each node before dispatch: `applySubstitutionToObject(node, schema)` after
`syncPassthroughsFromNodes`, in `back/src/app-api/flux/flux.service.ts`. The loop body does not. It
takes the raw node from `newNodes` and passes it as both `node` and `processedNode` to
`processNodeViaTemporal`, so the worker receives the literal `{{Topic.text}}`. Only `nodesBox`
substitutes inside the loop.

The substitution schema is already kept current per iteration (`addConnectToNodes` with
`onMutateSchema` at the iteration start, `updateSchemaWithNodeOutput` after each body node, and
`onMutateSchema` inside `processNodeViaTemporal`). The values exist; the loop never applies them. The
call shape dates from at least `99297619` (2026-06-12).

## The fix

1. Extract the main path's two steps into one private helper, `substituteNodeReferences(node, schema,
   nodes)`. The main path calls it instead of its inline copy.
2. In the loop, compute `substitutedNode` per body node and per iteration from the current schema.
3. Pass `node: raw, processedNode: substitutedNode` to all 11 `processNodeViaTemporal` calls in the
   loop: `webCrawling`, `apiCaller`, `mcpNode`, `commandTextNode`, `voiceBoxNode`, `imageGenerator`,
   `commandContentNode`, `mathFunction`, `pullData`/`pushData`, `webSearch` and `scripting`.

Inline handlers keep the raw node: `conditionNode` (only its `textData` is resolved, which the loop
already does), `audioReaderNode`, `sqlQuerier`, `libraryNode` and `fluxBox`. The main path also gives
them the raw node, so the loop now matches it. If those types should substitute too, change both paths
together, in a separate task.

### Interplay with B3

When `processedNode !== node`, B3's `inputResolutionModeOf` picks mode `full` instead of `refArrays`. The
worker's shadow comparison and apply path need no change.

## What changes for users

Only flows with a resolvable placeholder in a loop body node change.

- **Placeholder to a node before the loop:** resolves to that node's value, which is fixed for the whole
  loop. This is the common case.
- **Placeholder to an earlier body node:** resolves to the current iteration's output.
- **Placeholder to a later body node:** resolves to the previous iteration's output. On iteration 1 it
  resolves to the run seed, which is `''` for the reset types and the previous run's value for the
  others (see "Seed" below).
- **`{{<arrayNode>.content}}`:** resolves to the whole content, not the current item. The current item
  keeps arriving through the edge (`*Data`), as it does today.
- **Cost:** LLM nodes in the body get the substituted text instead of `{{x}}`, on every iteration.
- **Data:** `node_executions.input` grows accordingly. Above 256 KB it goes to S3 through the existing
  claim-check.
- **Unknown keys:** a `{{x}}` that matches no node id, ref-key or label stays literal, as it does outside
  the loop.

## Measured impact

- **Dev:** 128 loops, 86 with a body, 1 with a resolvable placeholder (an `apiCaller`, no runs in 90
  days).
- **Prod (2026-10-13, [`b3-1-q1-loop-placeholders.sql`](b3-1-q1-loop-placeholders.sql) →
  [`.prod.csv`](b3-1-q1-loop-placeholders.prod.csv)):** 707 loop flows, 62 with a placeholder in some
  other node (upper bound), and **0 of those 62 ran in the last 30 days** per `node_executions`.
- **Why the 0 is trusted:** on dev the same join finds the 2 loop flows that did run in 30 days, so it is
  not blind. `node_executions` is trimmed by retention (dev keeps rows from 2026-09-14), so
  [`b3-1-q2-loop-placeholders-runs.sql`](b3-1-q2-loop-placeholders-runs.sql) re-checks from `flows_logs`,
  which keeps one row per run since 2026-01-30 on dev, over 30 and 90 days. On dev it gives 13 placeholder
  loop flows, 0 run in 90 days, while 11 loop flows overall ran in that window.
- **Prod, confirmed from `flows_logs` (2026-10-13, [`.prod.csv`](b3-1-q2-loop-placeholders-runs.prod.csv)):**
  of the 62 flows, 0 ran in the last 30 days and 3 ran in the last 90 days. Prod's `flows_logs` holds
  runs since 2026-02-04, so both windows are fully covered.
- **Reading:** no customer ran a loop flow whose placeholders this fix would change in the last 30
  days. Three flows did run within 90 days; if they run again, their loop nodes receive the substituted
  value instead of the literal `{{x}}`. The 62 is an upper bound (a placeholder in any node of the flow,
  not only in the loop body), so the real number can be lower.

## Tests

- `back/src/app-api/flux/loop-body-substitution.spec.ts` calls the real `apiV2` with the real
  `NodeReferenceSubstitutionService`. Only collaborators that leave the process are stubbed, and
  `processNodeViaTemporal` records what it receives.
- **Flow:** starter → textBox "Topic" (`acme-widgets`) → `arrayNode` with 2 items → `apiCaller` in the
  body with `{{topic.text}}` in `url` and `jsonRequestBody` → `apiCaller` after the loop.
- **Assertions:** both loop dispatches and the after-loop dispatch carry the substituted values, and the
  raw `node` keeps the placeholder.
- **Negative control (observed on `refactor/868m0vmy4`):** with the `flux.service.ts` change reverted, the
  loop assertion fails with `Received: "https://api.example.com/{{topic.text}}/items"`.
- **Regression run:** all 53 suites under `src/app-api/flux/` (551 tests). The same 2 tests fail on the B3
  commit before this fix (`node-output-reset.spec.ts` library failure paths and
  `flux.service.error-timestamp.spec.ts`), so they are not caused by it.

## Found and left out

- The loop has no `fileSave` branch and no third-party integration branch; the main path has both.

## Seed

A placeholder with no edge to its target reads whatever the schema holds when the consumer runs, because
the scheduler (`flux/scheduler.ts`) orders by edges only. `clearRunOutputForSeed` resets the outputs of
`commandTextNode`, `voiceBoxNode`, `imageGenerator`, `commandContentNode`, `audioReaderNode`, `apiCaller`,
`mcpNode`, `scripting`, `mathFunction`, `counterNode` and `outputController`. The `text` of the `web*`
family, `webCrawling`, `reportBuilder`, `imageReaderNode`, `varOutputNode` and `thirdPartyIntegration`
keeps the previous run's value. This exists on production today and is not part of this task. It waits on
a product decision.

## Dev verification (2026-10-13)

Cherry-picked to back `master` (`afca0b00`, plus a dev-only stub for `entityDocService` in the spec) and deployed.

- **Agent:** "B3.1 dev check — loop placeholders (868mgqx9q)" in the "lex corp." workspace: starter → `arrayNode` (2 items) → `apiCaller` with `{{topic.text}}` in `url` and `jsonRequestBody`, and a textBox "Topic" = `acme-widgets`.
- **Before (run `157cc92b`, served by the old task during the rollout):** the body node received `https://httpbin.org/anything/{{topic.text}}/outside` on both iterations.
- **After (run `e04bebda`, new task only):** both iterations received `https://httpbin.org/anything/acme-widgets/outside` and `{"topic":"acme-widgets"}`; httpbin echoed the substituted body; B3's shadow recorded `matched: true`.
- **Trap:** a run started while ECS still drains the old task is served by old code. Read the service's deployments (`rolloutState`) before trusting a dev run.
- **Observed, not changed:** a node connected from the starter in parallel with the `arrayNode` ran as a loop body node, because the loop body follows plan order. That is existing loop behaviour.

## QA on dev (2026-10-13)

- Agent "B3.1 QA — LLM inside loop (868mgqx9q)": starter → `arrayNode` (2 items) → `commandTextNode` with `Reply with only this word and nothing else: {{topic.text}}`.
- Shadow run `91e5c0c8` and apply run `d3a747a6`: both iterations received the substituted prompt and answered `acme-widgets`.
