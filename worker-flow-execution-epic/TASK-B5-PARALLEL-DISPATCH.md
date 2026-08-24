# B5 — Turn on parallel dispatch

**Goal:** raise the batch size above one. This is the payoff of the whole epic, and it is one
configuration change plus one gate.

**Depends on:** B4 soaked in production, Track A complete for every executable type, and
**S2 + S3** — the connection ceiling and the spend/tenancy caps. Removing the accidental
back-pressure without them replaces a slow system with an unstable one (review §4.5).

## Why the gate is the whole task

The persistence model already supports parallel siblings (analysis §7.3): `node_executions` is one
row per execution, and `persistNodeSuccess` only merges into rows the activity owns. Two siblings
cannot lose each other's writes.

What is **not** safe is mixed mode. Nodes still running inline in the back do not write to their
own row — they end with `addConnectToNodes`, which merges the producer's output straight into the
**target** node's data (`back/src/app-api/folw/contants.ts:2032`, via `modifyData` at
`:2018–2024, 2056–2062`). That is a cross-node write, safe today only because the engine is
sequential and holds the whole node array in memory.

So: **all-backend is safe because it is serial; all-worker is safe because every write is own-row;
a flow that mixes the two and runs in parallel has a race that appears rarely and reproduces
badly** (§7.4b). The gate is not a precaution, it is the correctness condition.

## Scope

**In.** A per-flow eligibility check: run in parallel only when **every** executable node in the
flow is a migrated type, read from the A1 registry. `isMigratedTemporalNode`'s successor is
exactly this predicate.

**In.** Concurrency budgets, **per provider and per tenant** — not one global number
(review §4.2). Unbounded fan-out produces bursts against OpenAI, Anthropic, Replicate and the
integration APIs, and the first symptom is 429s surfaced to the customer as node failures. A global
cap does not prevent that, because one wide graph can spend the whole budget on one provider.

- Per provider: a concurrency budget derived from that provider's real rate limit, shared across
  the fleet rather than per replica.
- Per tenant: enforced by S3, which this task depends on. Without it, fan-out is a fairness bug.

**In — the parallel-execution UX, specified rather than discovered** (review §5). Four decisions
this task forces and must therefore make:
- **Concurrent status.** Several nodes are `RUNNING` at once; the builder shows per-node status
  today and "which node is the run on" stops having one answer — including in the cancel footprint
  the product already shows.
- **Partial cancellation.** Cancelling leaves some siblings completed, some aborted, some never
  started. Decide what a cancelled run means to the user.
- **Side-effect ordering.** Two independent push nodes fire in graph order today; in parallel they
  do not. A customer relying on that incidental ordering experiences it as a regression.
- **Error attribution.** Fail-fast stops at the first error today; with a batch in flight several
  can fail at once. Decide which one names the run.

**In.** Rollout by cohort, not by switch: internal flows, then a small customer cohort, then
general — with the eligibility gate meaning most flows simply stay sequential until their nodes
are covered.

**Out.** Anything that widens eligibility by relaxing the gate. If a flow is not eligible, the
answer is to migrate its remaining nodes, never to make the check lenient.

## Verification

- **Negative control (required).** Force an ineligible flow — one containing an inline node —
  through the parallel path and demonstrate the lost update: two writers on one `flows_nodes` row,
  one write disappearing. Then confirm the gate refuses that flow. **This is the test that
  justifies the gate**; without having seen the corruption, nobody will keep the gate strict.
- **Measure before refusing** (PLAN §3.3.2): the eligibility check is a refusing rule. Classify
  every production flow as eligible / ineligible and, for each ineligible one, name the node type
  that disqualified it. Refused-although-it-works must be zero.
- Determinism: the same flow run twice in parallel must produce the same final outputs. Run it
  enough times to mean something, and record the count.
- Measure the latency the epic bought back — R4 in PLAN §6 predicted a regression from the A track;
  this is where the claim is settled with numbers.

## Done when

Eligible flows run their ready set concurrently; ineligible flows run sequentially and are counted;
the corruption case is a passing test; latency is measured against the pre-epic baseline.

## Files

new eligibility predicate over the A1 registry · the flow workflow from B4 ·
`back/src/app-api/folw/contants.ts` (documented as the reason for the gate)
