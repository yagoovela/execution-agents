# Market comparison — what the category has that we do not

**Caveat, stated first.** The FluxPrompt side of every claim below was read out of this repository
and cites `file:line`. The competitor side comes from general knowledge of the category and is
**not verified against current product documentation** — this space moves fast, so treat competitor
specifics as "common in this category" rather than as audited fact, and re-check before quoting any
of it externally.

**Framing.** The most useful finding is not a feature list. It is that several of the biggest gaps
are **blocked by the same architectural limitation this epic is already removing** — and become
cheap the moment the worker owns the loop. That changes what the epic is worth: it is not only a
scaling project, it is the precondition for the product's next three capabilities.

---

## 1. Where we are genuinely ahead

Worth stating before the gaps, because two of these are real differentiators and should not be
traded away while fixing the rest.

**The trigger surface is unusually broad.** API key, public webhook, email to a per-flow address,
schedule, chatbot, form, public API, MCP, and CSV batch. Most tools in the category have three or
four. (The security state of three of them is a separate matter — review §9, §10.)

**MCP is a first-class surface, not an integration.** 28 tools covering read, CRUD, versioning and
execution, so an AI client can *build and run* flows, not merely call one. Most competitors expose
an API for triggering; exposing the builder itself to an agent is a different posture, and it is
the thing hardest for others to copy quickly.

**Durable execution on Temporal.** Most of the category built bespoke queue-and-retry machinery.
Temporal gives retries, timeouts, cancellation and history for free — the epic exists to actually
collect on that.

**Model breadth.** Anthropic, OpenAI, Gemini, Groq, Mistral, plus Replicate, Ideogram, Luma,
Runway and ElevenLabs for image, video and audio. Broader than the typical text-only AI node.

**Long-term memory as a node.** A vector-backed memory node in the graph, rather than an
integration a user has to assemble.

---

## 2. Gaps that this epic unblocks — the interesting group

### 2.1 Resume a failed run from the node that failed — **highest user-visible gap**

Standard in the category. We do not have it: greps for `retryFrom`, `resumeFrom`, `rerunFrom` and
`replayRun` return nothing.

**The data model already supports it.** `node_executions` records the resolved `input` and the
`outputData` per node per run. What is missing is an engine that can start mid-graph — and the
backend's loop cannot, because it rebuilds state from the top.

Once `B4` puts the graph in a workflow, "resume from node X" is a scheduler state seeded from the
completed set. **Impossible today, near-free after B4.**

### 2.2 Human-in-the-loop and approval steps

Common in the category, and a frequent enterprise requirement: pause, ask a person, continue.
Greps for `approval`, `humanIn`, `waitFor`, `pauseRun` and `resumeRun` in `app-api` return nothing.

It is impossible today for a structural reason: the backend loop holds the run in memory, and it
cannot wait a day for a human. A **Temporal workflow can** — a signal, with no resources held while
it waits. This is one of the strongest reasons to want `B4` that has nothing to do with scale.

### 2.3 App-native triggers — "when a new row appears", not "when someone calls us"

Every trigger we have is **push-in**: something else must call us. The category's default is the
opposite — trigger on a new Sheets row, a new Slack message, a new Stripe event.

We already have the hard half: the integration adapters and their credentials. What is missing is a
trigger runtime — a durable cursor per connection, polled on a schedule. That is exactly what
`S8`'s Temporal Schedules give, so the incremental cost after `S8` is a cursor table and one
activity per provider.

### 2.4 Per-flow concurrency and rate controls, visible to the user

The category exposes concurrency limits per workflow. We expose none, and internally have none —
which is `S3`. Once the ceiling exists as a mechanism, surfacing it as a per-flow setting is a UI
change, not an engineering one.

---

## 3. Gaps that are cheap and independent of the epic

### 3.1 Evals and regression testing — **the cheapest large win**

The LLM-tooling half of the category has converged on datasets plus scorers plus regression runs.
We have **no** eval surface: greps for `eval`, `dataset`, `regression`, `goldenSet` and `assertion`
find nothing relevant.

But we have 80% of the machinery already: **batch processing** takes a CSV of inputs, runs the flow
per row and stores per-row outputs (`flux.controller.ts:574–706`). Add an expected-output column and
a scorer node, and that is an eval harness. Add "run it on every version" and it is regression
testing.

This matters beyond feature parity: without it, nobody can safely change a prompt in a flow that
matters, which is the single biggest reason AI automations stall after the demo.

### 3.2 Inbound idempotency keys

We dedup **outbound** delivery well — run-scoped `SET … EX … NX` plus a content hash
(`flux.service.ts:5030–5044`). Inbound has nothing: a webhook provider that retries its delivery,
which Stripe and Slack both do routinely, creates a **second run** and a second charge.

The pattern is already in the codebase. It just points the wrong way. Small, and it pairs naturally
with `S7`.

### 3.3 Cost observability that a customer can act on

We record `token_transactions` per node and totals per run, so the data exists. What does not exist
is a surface: cost per flow over time, cost per run trend, a forecast, an alert before a budget is
hit. `S3` introduces the ceiling; the reporting is the half that makes the ceiling humane rather
than a surprise.

### 3.4 Trace export to the customer's own stack

Teams running AI in production increasingly want traces in the observability tool they already pay
for. We have a hierarchical run log with tokens, cost and timings per node — genuinely good raw
material — and no export. An OpenTelemetry exporter over `RunLogCollector` reuses everything
`E1` is already touching.

### 3.5 Environments and diffs for a flow

`flow_version_history` exists and the MCP surface has versioning, so this is half-built. Missing:
a dev/staging/prod notion per flow, a readable diff between versions, and one-click rollback. The
storage is there; this is product surface over existing data.

---

## 4. The positioning question — we orchestrate, we do not (yet) agent

This is the largest strategic gap, and it is not a missing feature so much as a missing category.

**We call flows "agents"** — the MCP tools are `create_agent`, `run_agent`, `list_agents`. But the
execution model is a **deterministic graph**: a human draws the edges, and every path is decided in
advance. The MCP node resolves a **fixed** `toolName` from node data
(`mcp_flux_node.service.ts:43`); the model does not choose the tool.

Meanwhile the category's centre of gravity moved to autonomous agents — give a model a goal and a
toolbox, and let it decide the sequence, loop until done, and ask for help when stuck.

**Both models are legitimate**, and deterministic graphs are *better* for compliance, cost
predictability and debuggability — the reasons enterprises reject autonomous agents. The risk is
not that the graph model is wrong; it is being sold as "agents" while a buyer comparing against
Lindy or Gumloop expects something else, and finds out during the trial.

**And we are unusually well placed to add it.** An agent node needs three things: a tool catalogue,
multi-provider models, and a durable runtime that can loop safely with a ceiling. We have the first
two, and the third is precisely what this epic builds — including the loop ceiling (`S4`), the cost
ceiling (`S3`) and the recursion guard (`S1`), which are the three things that make an autonomous
loop safe to sell rather than terrifying.

**The MCP tool catalogue is the unfair advantage here.** Competitors adding an agent node must
build a tool registry; ours already exists, is already exposed, and is already how external AI
clients drive the product.

---

## 5. Ranked by value over cost

| # | Opportunity | Cost | Depends on | Why this rank |
|---|---|---|---|---|
| 1 | Evals and regression testing over the batch runner | low | — | The machinery exists; unblocks customers changing prompts safely |
| 2 | Resume from the failed node | low **after B4** | B4 | Highest user-visible parity gap; data model already supports it |
| 3 | Human-in-the-loop approval | low **after B4** | B4 | Structurally impossible today; a signal after |
| 4 | Inbound idempotency | very low | pairs with S7 | Stops duplicate runs from routine provider retries |
| 5 | Autonomous agent node | medium | S1, S3, S4 | Category positioning, and our MCP catalogue makes it cheaper for us |
| 6 | App-native triggers | medium | S8 | Changes us from "callable" to "watching"; adapters already exist |
| 7 | Cost dashboards and budget alerts | low–medium | S3 | Makes the new ceiling humane instead of a surprise |
| 8 | Trace export (OpenTelemetry) | low | E1 | Reuses the run-log work already planned |
| 9 | Environments, diff and rollback | medium | — | Half-built already; product surface over existing storage |
| 10 | Per-flow concurrency settings | very low | S3, B5 | A UI over a mechanism the epic builds anyway |

**The pattern worth taking away:** six of the ten are gated on work this epic already contains.
The epic is currently justified as scaling and safety. It is also the unlock for most of the
product roadmap, and that is a stronger argument for funding it than latency.
