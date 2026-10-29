# A14 — Small Memory and chat under the workflow engine, without moving a node

**Goal:** flows with Small Memory (`fluxObject`) and chat history run on the B4 workflow engine with
the same results as on the back's loop. No node moves to the worker.

**Depends on:** B3b.1 (the run seed snapshot), B4, A7 (the read rule: a consumer reads the writes
that completed before it was scheduled). **Added 2026-10-23** from
[`NODE-COVERAGE-AUDIT-2026-10-23.md`](./NODE-COVERAGE-AUDIT-2026-10-23.md); **rescoped 2026-10-23**
(the first draft moved chat writes into the workflow behind A7's callback and lock).

## Why

Small Memory does not execute. It is a container that the edge projection writes into when it is
the target of an edge, and reads from when it is the source (`edge-projection.ts`, the `fluxObject`
branches). On the back's loop that state lives in the loop's memory: a node that reads Small Memory
sees what earlier nodes in the same run added. The back also loads the chat history before the loop
and persists the memory and the assistant's answer around it.

The workflow engine has no process that holds a run's memory; each node runs on its own. Today the
gap is hidden: `fluxObject` has no registry entry, so B4's gate refuses every flow that has one and
those flows stay on the back's loop. If nothing changes, the loop can never be deleted (Wave 6).

PLAN §8 called `fluxObject` configuration-time. That was wrong; this task corrects the
consequence.

## Scope

Three parts. Only the second needs new logic, and none of them needs a worker module.

1. **Chat history at run start.** The back already loads it before the loop. It writes it into the
   run seed snapshot, so both engines start from the same value.
2. **Small Memory content during the run, derived instead of held.** The content of a Small Memory
   node at a given moment is the history at run start plus the outputs of the nodes that feed it
   and that completed before the reader was scheduled. Those outputs are already stored, one row
   per execution. The worker projection rebuilds the content from the seed and those rows, in
   completion order, with the ported projection code. No new write, no callback, no lock.
3. **Persistence stays in the back.** The back persists the memory to the canvas node and appends
   the assistant's answer, as today. On the workflow engine it does so from the B4 per-node events
   it already receives, so the editor still sees the memory grow during the run, and at run end for
   the answer.

**In.** `fluxObject` gets its registry class (`none`, through A11) and leaves
`BACK_ONLY_PROJECTION_NODE_TYPES`.

**Out.** Moving any node to the worker. Changing chat semantics, session keys or what the chatbot
shows. Two overlapping chat turns on one session can still overwrite each other, as today; fixing
that is a separate decision.

## Verification

- **Negative control (required).** Force a Small Memory flow through the workflow engine before
  this task and record the consumer's missing content; after it, the content matches the back's
  loop.
- Parity over a corpus of stored chat flows: the chatbot answer and the persisted memory match
  between the two engines.
- A retried reader activity reads the same memory content as its first attempt.

## Done when

Flows with Small Memory are eligible for the workflow engine and produce the same answer and the
same persisted memory as the back's loop; `fluxObject` is out of the back-only list.

**Added 2026-10-28.** A11 classes `fluxObject` as `execution: 'state'`. This task makes B4's gate
accept `state` and turns A11's `it.failing` "the gate accepts a flow that holds a `state` node" into
a plain test. The class stays `state`.

## Files

`back/src/app-api/flux/flux.service.ts` (`persistSmallMemoryEntries`, the chat load before the
loop, the answer append at finalisation, the per-node event handler) · the run seed snapshot (B3b.1) ·
worker projection (`project-node-input.ts`) and the ported `edge-projection` · the A1 registry
