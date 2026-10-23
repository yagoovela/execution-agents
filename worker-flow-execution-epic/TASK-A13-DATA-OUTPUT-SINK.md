# A13 — The Data Output as the workflow's sink

**Goal:** a run under the B4 workflow produces the same Data Output value, API reply, chatbot answer
and delivery as a run on the back's loop.

**Depends on:** A9, B4, A11. **Blocks:** turning the B4 flag on in production.
**Added 2026-10-23** from [`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md).

## Why

A9 moved email and callback delivery into the worker and handed the rest to B4: "when B4 lands,
`deliverRunOutputs` becomes its last step". B4's spec never picked it up. Today the back builds the
Data Output's value from its producers in memory, and that value is what the API reply, the chatbot
answer and A9's delivery read. The worker enum has `OUTPUT` with no activity, so a workflow run has
no sink.

## Scope

**In.** Build the Data Output's value from its upstreams' `node_executions` rows, by reference, as
B3b does for every other consumer. Record which executions it read.

**In.** Make `deliverRunOutputs` the workflow's last step, and keep the back's loop calling the same
code.

**In.** Flip `outputObjectNode`'s registry entry once both paths use the same builder.

**Out.** Changing the reply shape, the delivery channels, or A9's retry policies.

## Verification

- **Negative control (required).** Run one stored API flow under the workflow before this task and
  record the empty or missing reply; after it, the reply matches the back's loop byte for byte.
- Parity over a corpus: the API reply and the chatbot answer match between the two engines.
- A delivery fires once per run under the workflow, including after a retried last step.

## Done when

Workflow runs return the same reply and deliver the same outputs as the back's loop; the registry
entry is flipped; no back-only code builds the Data Output value.

## Files

`back/src/app-api/flux/flux.service.ts` (the Data Output assembly, `deliverRunOutputs` caller) ·
worker `process-flow.workflow.ts` · worker `node-activities.ts` (`OUTPUT`) · the A1 registry
