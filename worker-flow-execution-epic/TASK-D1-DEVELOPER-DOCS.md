# D1 — Developer documentation

**Goal:** a developer who has never touched the worker can add a node type correctly, and a
developer debugging a run can find where it went wrong.

**Depends on:** nothing. **Runs alongside the whole epic** — each A-task updates it; this task
builds the frame and keeps it honest.

## Why it is a task and not a README line

The registration chain is seven layers and **all of them are load-bearing**: module, enum entry,
`temporal.module.ts`, `activities.service.ts`, `worker.service.ts` binding,
`workflows/configs.ts` proxy, and the `process-single-node.workflow.ts` case. Miss one and you get
a node that appears to run and does nothing, or a workflow that throws
`"Node type X not supported"` from the default branch. That failure is invisible in review and
obvious only at runtime.

## What already exists — this is not greenfield

`docs/worker/` is already populated and must be **audited and extended**, not recreated:

- `overview.mdx`, `development.mdx`, `environment-variables.mdx`
- `activities/` — `charge-tokens`, `generate-file`, `validate-model-access`, `notify-status`,
  `generate-execution-logs`, `get-info-database`, `node-execution-error`
- `node/` — `api-caller`, `audio-transcriber`, `counter`, `display-box`,
  `large-memory-dynamic-pod`, `math-function`, `mcp`, `scripting`, `sql-querier`, `text-generator`

Two gaps are visible from that listing alone. The `node/` pages document types the back does not
route — `sql-querier` and `audio-transcriber` are the stranded modules of A3, and `mcp` is not in
production — so **the docs already describe a system more migrated than the one that runs.** And
`pt-br/` contains only `environment-variables.mdx`, so the pt-br side is a stub.

The first job of this task is therefore an **audit**: for each existing page, does it describe
production, a branch, or an intention?

## Scope

Mintlify pages under `docs/worker/`, **en + pt-br**, per the docs repo convention. Use the
`mintlify-docs-writer` agent.

1. **Node execution lifecycle** — the path a run takes: entry endpoint, `node_executions`, the
   Temporal dispatch, `fetchNodeRow`, execute, `persistNodeSuccess`, Redis, socket. This is
   already drawn: reuse the published pipeline diagrams rather than describing them in prose.
2. **How to add a node type** — the seven layers, in order, with the failure each omission
   produces. Written as a checklist someone can follow while working, not as an essay.
3. **Callback reference** — `/worker/store-payload`, `/worker/get-payload`,
   `/worker/validate-model-access`, `/worker/charge-tokens`, `/worker/generate-file`, plus
   whatever A7 adds. Request, response, when to use, when not to.
4. **Error taxonomy** — `UserConfigError`, `IntegrationError`, `ProviderError`, `TimeoutError`,
   `SystemError`: which to throw when, and what each does to retries. Getting this wrong makes a
   user's typo retry for thirty minutes.
5. **Persistence contract** — own-row writes only, the JSONB merge, the claim check above 256 KB,
   and why this is what makes parallelism safe.
6. **Running and debugging locally** — the `docker-compose.devdb.yaml` stack, finding a run in
   Temporal, reading `node_executions`, the worker's log surface.

## Verification

- **Negative control (required), and it is a real one here.** Have someone who has not done it
  add a trivial node type following only the page. If they produce a node that silently does
  nothing, the page is wrong — that is the failure to look for, because it is the one the
  seven-layer chain actually produces. Record what they hit.
- Every file path and line reference in the docs is checked against the current code at the time
  of writing, and the commit SHA is stated on the lifecycle page. A stale line number in
  documentation is worse than none: it sends the reader to confidently wrong code.
- `env-vars-sync` if any page documents an env var.

## Done when

The audit is recorded (which existing page described production and which did not), the six
subjects above are covered in en **and** pt-br, someone unfamiliar has added a node type using
only them, and every reference resolves.

Each A-track task adds its node's page as part of PLAN §3.4 point 7 — this task does not backfill
them at the end.

## Files

`docs/worker/**` (+ `docs/pt-br/worker/**`) · `docs/docs.json` navigation ·
the published pipeline artifacts as diagram sources
