# B4c — Placeholder substitution on the workflow path

ClickUp: [1gahkf3byq6](https://app.clickup.com/t/1gahkf3byq6). **Drafted 2026-11-24** from the A14 edge-case investigation. **Urgent:**
batch rows in production are affected today.

**Depends on:** B3 and B4 (on `main`). **Blocks:** turning `engine_in_workflow` on in production
([868mnbm7h](https://app.clickup.com/t/9011479430/868mnbm7h)) and `temporal_schedules`, and B4b-D1
(seed pruning must keep every placeholder target).

## Problem statement

On the workflow path (`processFlow`), no `{{...}}` placeholder in a node's text is replaced. The
node receives the literal text, for example `{{topic.text}}`, and sends it to the model or the API.
The legacy loop builds a substitution schema from every node at run start
(`generateSchemaFromNodes`, `flux.service.ts:5081-5084`) and updates it after each node runs
(`updateSchemaWithNodeOutput`, `:2393`); with `worker_input_resolution` on, it stores that schema as
the snapshot `base` and each dispatch as a delta, so the worker rebuilds it exactly (B3). The B4
path writes `base = {}` (`run-seed.service.ts:~90`), each open writes an empty delta
(`openWorkerNodeExecution`, `flux.service.ts:2208`), and `processFlow` passes an empty journal
(`process-flow.workflow.ts:224-230`). No task owned it.

**Production impact today.** Since B7 (2026-11-03), every batch row runs on `processFlow` with no
flag (`flux.controller.ts:~744` starts `processBatch`, which runs `executeChild(processFlow)`), so
every batch row whose flow holds a placeholder sends the literal. API runs and Temporal schedules
are not affected yet, because `engine_in_workflow` and `temporal_schedules` are off in production.

Measured with the same function and input (ported files on `origin/main`):

| Reference | Legacy | Workflow |
|---|---|---|
| `{{label.text}}` to a node with no edge | resolved | literal |
| `{{x}}` to a node connected by an edge | resolved | literal (only the `*Data` array arrives, through the projection) |
| `{{varinput.text}}` (run input or batch row value) | resolved | literal |
| `{{textbox.text}}` (a source node) | resolved | literal |
| `{{writer.text}}` after `writer` ran | its output | literal |

## Goals

- [ ] Every placeholder that the legacy loop resolves resolves to the same value on the workflow
      path, on every entry point (batch rows, API runs, schedules, child runs).
- [ ] Batch rows in production resolve placeholders again.
- [ ] The substitution rule is imported from the back's service, never restated.

## Out of scope

| Item | Reason |
|---|---|
| A bare `{{label}}` resolving to `[object Object]` | A legacy quirk; parity keeps it. Fix separately if wanted. |
| Unknown keys staying literal | Legacy behaviour (`replacePlaceholders` leaves them). |
| Seed pruning | B4b-D1, after this task. |

## User stories

### P1: Batch rows resolve placeholders again ⭐ MVP

**User story:** As a customer who runs a flow in batch, I want each row's placeholders filled, so
that the model receives my data and not `{{...}}` text.

**Acceptance criteria:**

1. WHEN a batch row runs a flow whose node text holds `{{varinput.text}}` THEN the node SHALL
   receive that row's value.
2. WHEN a node references another node by label or id with no edge THEN it SHALL receive the same
   value as on the legacy loop.
3. WHEN a node references a node that already ran in this run THEN it SHALL receive that node's
   output, as on the legacy loop; WHEN the referenced node has not run yet THEN it SHALL receive its
   stored value.

**Independent test:** the same batch file run on `main` (literals) and after the change (resolved),
compared with the legacy loop's node inputs.

### P1: Every workflow entry point has parity ⭐ MVP

1. WHEN an API run, a scheduled run or a child run uses the workflow engine THEN its node inputs
   SHALL match the legacy loop's, placeholder for placeholder.
2. WHEN a node runs inside an `arrayNode` iteration THEN references to the iteration's nodes SHALL
   follow the legacy loop's per-iteration values (B3.1).
3. WHEN a run uses `continueAsNew` THEN the schema SHALL carry over.

## Edge cases

- WHEN a placeholder targets a node whose output is claim-checked to S3 THEN the value SHALL be
  resolved through the claim ref.
- WHEN two nodes share a label THEN the result SHALL match the legacy loop's choice.
- WHEN a `textBox` has an empty `text` THEN it SHALL be filled from its `textData`, as
  `generateSchemaFromNodes` does.
- WHEN B5 dispatches siblings in parallel THEN a node SHALL see only outputs of nodes that finished
  before it was dispatched, as the legacy order defines.

## Design direction (settled in Design)

1. The seed writes the snapshot `base` with the back's own `generateSchemaFromNodes` over the
   nodes after run inputs are applied, instead of `{}`.
2. Before resolving a node, the worker overlays the outputs of nodes that already finished in this
   run, through the ported `updateSchemaWithNodeOutput`, or `processFlow` passes a real journal so
   each finished node records its delta. Design picks one.
3. Size: the base holds the text fields of every referenceable node; it lives in
   `run_substitution_snapshots.base`, not in Temporal history.

## Requirement traceability

| ID | Story | Status |
|---|---|---|
| PH-01 | P1 batch: run inputs resolve | Pending |
| PH-02 | P1 batch: edgeless references resolve | Pending |
| PH-03 | P1 batch: outputs of finished nodes | Pending |
| PH-04 | P1 parity: API, schedule and child runs | Pending |
| PH-05 | P1 parity: array iterations | Pending |
| PH-06 | P1 parity: `continueAsNew` | Pending |

## Test list (must pass)

1. Negative control: on `main`, a batch row with `{{varinput.text}}`, `{{textbox.text}}`, an
   edgeless `{{label.text}}` and `{{writer.text}}` after `writer` sends all four literals; after the
   change, all four resolve to the legacy loop's values.
2. Parity corpus: stored dev flows that hold placeholders, run on both engines; node inputs match.
3. A batch file with three rows: each row's node inputs carry that row's values.
4. A reference inside an `arrayNode` body resolves per iteration as on the legacy loop.
5. A claim-checked referenced output resolves.
6. A scheduled run and an API run with the flag on locally: parity.
7. Dev: a batch file with placeholders on dev returns resolved inputs (`node_executions.input`).
8. Production: the impact queries in `etc/2026-11-24/` (`N-b4c-*.sql`) run before and after the
   deploy; literals in batch inputs drop to zero for new rows.

## Estimate

1.5 to 3 days: back seed base (2 files), worker overlay (2 to 3 files), specs with negative
controls, a batch and API parity test, and a dev check.
