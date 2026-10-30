# TASK-D2 — Machine Contract — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the A1 dispatch registry as a machine-readable, test-enforced contract that an agent reads instead of a snapshot in prose, refresh `.claude/skills/node-worker-migration/SKILL.md` to cite it (with the four gates, the PLAN §3.4 definition of done, the blocking-wait cost, and the prefetch path), and add a short pointer in the workspace `CLAUDE.md`.

**Architecture:**
- A generator projects `NODE_DISPATCH_REGISTRY` into `back/src/shared/node-dispatch/node-dispatch-contract.json` — one entry per registered node type, sorted, no timestamps.
- A drift spec fails when the JSON diverges from the registry, using the same pattern as `node-types.contract.json`'s existing drift spec.
- The skill loses every "as of 2026-07" enumeration and cites the JSON file for the answers that used to be typed by memory. It gains the four dispatch gates, the seven-point definition of done, the blocking-wait note, and the prefetch path — all citations, no restatements.
- The workspace `CLAUDE.md` gains one short section that names the contract file, the seven layers plus the registry, and the three skills to run.

**Tech Stack:** NestJS + TypeScript + Jest (back), Markdown (skill + workspace CLAUDE.md).

**Reference spec:** [TASK-D2-MACHINE-CONTRACT.md](./TASK-D2-MACHINE-CONTRACT.md). Depends on A1 (already shipped: `back/src/shared/node-dispatch/`).

**User-specific plan conventions:**
- No `git commit` steps in the plan — the user manages git manually after implementation.
- No `pnpm build` / lint / type-check verification steps — the user runs those locally.
- Tests are run with `pnpm test -- --testPathPattern=<file>` on back (from `back/`).
- No code comments (workspace convention).
- All prose in English (workspace convention).

---

## File Structure

**Files created:**
- `back/scripts/generate-node-dispatch-contract.ts` — script that reads `NODE_DISPATCH_REGISTRY` and writes the JSON contract; exports a pure `generateNodeDispatchContract()` for the spec.
- `back/src/shared/node-dispatch/node-dispatch-contract.json` — the published, machine-readable contract (one entry per registered node type).
- `back/src/shared/node-dispatch/node-dispatch-contract.spec.ts` — drift spec that regenerates the JSON in memory and fails if it differs from the committed file.

**Files modified:**
- `back/package.json` — add `generate:node-dispatch-contract` script.
- `back/src/shared/node-dispatch/node-types-contract.spec.ts` — no logic change; extend its comment header to name the sibling published-artefact drift spec, so a reader of one finds the other.
- `Workflow/skills/node-worker-migration/SKILL.md` — full refresh: replace stale enum snapshot with pointer to the contract; add the four gates, the PLAN §3.4 definition of done, the blocking wait, the prefetch path; rewrite the Object Caller worked example (its verdict is being overturned by A7); mark the "activity is the only shape" claim as citation-shaped so B4 requires only a citation update.
- `Workflow/CLAUDE.md` — add one short section pointing to the contract, listing the seven layers plus the registry, and naming the skills to run.

**Files read but not modified:**
- `back/src/shared/node-dispatch/node-dispatch-registry.ts` (source of truth).
- `back/src/shared/node-dispatch/node-dispatch-registry.types.ts` (entry shape).
- `back/src/shared/node-dispatch/node-types.contract.json` (worker-enum snapshot, referenced by the new contract).
- `worker/src/modules/nodes/nodes.types.ts` (only through the existing enum contract).
- `back/src/app-mcp/node-types/node-type-metadata.ts` (contrast case, cited in the skill as "what the drift the registry avoids looks like").

---

## PART 1 — The generated machine-readable contract

### Task 1: Add the failing drift spec

**Files:**
- Create: `back/src/shared/node-dispatch/node-dispatch-contract.spec.ts`

- [ ] **Step 1: Create the drift spec that expects the generator + committed JSON to agree**

Create `back/src/shared/node-dispatch/node-dispatch-contract.spec.ts`:

```ts
import * as fs from 'fs';
import * as path from 'path';
import { generateNodeDispatchContract } from '../../../scripts/generate-node-dispatch-contract';

const contract = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, 'node-dispatch-contract.json'),
    'utf8',
  ),
);

const workerEnumSnapshot: { nodeTypes: string[] } = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'node-types.contract.json'), 'utf8'),
);

describe('node-dispatch contract drift', () => {
  it('matches the registry exactly (regenerate with pnpm generate:node-dispatch-contract)', () => {
    const fresh = generateNodeDispatchContract();
    expect(fresh).toEqual(contract);
  });
});

describe('node-dispatch contract shape', () => {
  it('names the registry file it is derived from', () => {
    expect(contract.source).toBe(
      'back/src/shared/node-dispatch/node-dispatch-registry.ts',
    );
  });

  it('cross-links the worker-enum snapshot spec so a reader finds both', () => {
    expect(contract.workerEnumContract).toBe(
      'back/src/shared/node-dispatch/node-types.contract.json',
    );
  });

  it('sorts node types so the diff is a diff, not a reshuffle', () => {
    const keys = Object.keys(contract.nodeTypes);
    expect([...keys].sort()).toEqual(keys);
  });
});

// This is the D2 assertion the task's spec-body names verbatim: "a spec that
// fails when the contract and the worker enum disagree". A1 already asserts
// registry-vs-worker-enum; this one asserts published-contract-vs-worker-enum
// directly, so a break in the chain is named at the layer an agent reads.
describe('published contract vs the worker node-type enum', () => {
  it('every published type marked workerModule is in the worker enum snapshot', () => {
    const claimed = Object.entries(
      contract.nodeTypes as Record<string, { workerModule?: boolean }>,
    )
      .filter(([, entry]) => entry.workerModule === true)
      .map(([type]) => type);
    const unbacked = claimed.filter(
      type => !workerEnumSnapshot.nodeTypes.includes(type),
    );
    expect(unbacked).toEqual([]);
  });

  it('every worker enum type appears in the published contract', () => {
    const unpublished = workerEnumSnapshot.nodeTypes.filter(
      type => !(type in contract.nodeTypes),
    );
    expect(unpublished).toEqual([]);
  });
});
```

- [ ] **Step 2: Run the new spec and observe it fail because the generator + JSON do not exist yet**

Run: `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.

Expected: the test cannot even load — the import of `generate-node-dispatch-contract` fails with "Cannot find module". Record that failure in your notes; it is the negative control for the whole PR.

---

### Task 2: Add the generator

**Files:**
- Create: `back/scripts/generate-node-dispatch-contract.ts`

- [ ] **Step 1: Read the sibling generator to follow the pattern**

Read `back/scripts/generate-node-types-contract.ts` end-to-end. Note: it exports a pure `generateNodeTypesContract()` used by both `main()` and the spec, uses `resolveSiblingRepoRoot` for the worker-enum case (not needed here — this contract's source is inside `back/`), and writes JSON with a trailing newline.

- [ ] **Step 2: Create the generator**

Create `back/scripts/generate-node-dispatch-contract.ts`:

```ts
import * as fs from 'fs';
import * as path from 'path';
import { NODE_DISPATCH_REGISTRY } from '../src/shared/node-dispatch/node-dispatch-registry';
import type { NodeDispatchEntry } from '../src/shared/node-dispatch/node-dispatch-registry.types';

const SOURCE_PATH = 'back/src/shared/node-dispatch/node-dispatch-registry.ts';
const WORKER_ENUM_CONTRACT_PATH =
  'back/src/shared/node-dispatch/node-types.contract.json';

export interface PublishedNodeDispatchEntry {
  flowDispatch: 'worker' | 'inline';
  legacyEndpoint:
    | 'accept'
    | 'refuse-migrated'
    | 'refuse-mutating'
    | 'refuse-unsupported';
  prefetchSafe: boolean;
  workerModule: boolean;
  integrationProviders?: string[];
  integrationExecutable?: boolean;
  dedicatedProvider?: string;
  handoffOwner?: string;
  strandedReason?: string;
  phantom?: string;
  note?: string;
}

export interface PublishedNodeDispatchContract {
  source: string;
  workerEnumContract: string;
  nodeTypes: Record<string, PublishedNodeDispatchEntry>;
}

function project(entry: NodeDispatchEntry): PublishedNodeDispatchEntry {
  const projected: PublishedNodeDispatchEntry = {
    flowDispatch: entry.flowDispatch,
    legacyEndpoint: entry.legacyEndpoint,
    prefetchSafe: entry.prefetchSafe,
    workerModule: entry.workerModule,
  };
  if (entry.integrationProviders) {
    projected.integrationProviders = [...entry.integrationProviders].sort();
  }
  if (entry.integrationExecutable !== undefined) {
    projected.integrationExecutable = entry.integrationExecutable;
  }
  if (entry.dedicatedProvider !== undefined) {
    projected.dedicatedProvider = entry.dedicatedProvider;
  }
  if (entry.handoffOwner !== undefined) {
    projected.handoffOwner = entry.handoffOwner;
  }
  if (entry.strandedReason !== undefined) {
    projected.strandedReason = entry.strandedReason;
  }
  if (entry.phantom !== undefined) {
    projected.phantom = entry.phantom;
  }
  if (entry.note !== undefined) {
    projected.note = entry.note;
  }
  return projected;
}

export function generateNodeDispatchContract(): PublishedNodeDispatchContract {
  const sortedTypes = Object.keys(NODE_DISPATCH_REGISTRY).sort();
  const nodeTypes: Record<string, PublishedNodeDispatchEntry> = {};
  for (const type of sortedTypes) {
    nodeTypes[type] = project(NODE_DISPATCH_REGISTRY[type]);
  }
  return {
    source: SOURCE_PATH,
    workerEnumContract: WORKER_ENUM_CONTRACT_PATH,
    nodeTypes,
  };
}

export const CONTRACT_OUTPUT_PATH = path.resolve(
  __dirname,
  '..',
  'src/shared/node-dispatch/node-dispatch-contract.json',
);

function main(): void {
  const contract = generateNodeDispatchContract();
  fs.writeFileSync(
    CONTRACT_OUTPUT_PATH,
    `${JSON.stringify(contract, null, 2)}\n`,
    'utf8',
  );
  const total = Object.keys(contract.nodeTypes).length;
  console.log(`Wrote ${total} node dispatch entries to ${CONTRACT_OUTPUT_PATH}`);
}

if (require.main === module) {
  main();
}
```

Notes for the implementer:
- `NodeDispatchEntry.integrationProviders` is a `ReadonlySet<string>` — serialize as a sorted array so the JSON diff is stable.
- Do not include `Date.now()` or any timestamp: the file is compared verbatim by the drift spec, so any non-deterministic field would poison it.
- Only include optional fields when present — omitting them (instead of writing `undefined` or `null`) keeps the JSON compact and matches the shape checks in Task 1's spec.

- [ ] **Step 2: Verify the spec still fails, but now because the JSON is missing**

Run: `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.

Expected: the tests load, but `fs.readFileSync(node-dispatch-contract.json)` throws `ENOENT`. Good — the next task creates the file.

---

### Task 3: Wire the generator into `package.json`

**Files:**
- Modify: `back/package.json`

- [ ] **Step 1: Find the existing `generate:node-types-contract` entry**

Run: `grep -n generate: back/package.json`. Note its exact form — the plan below uses the same runner flags for consistency.

- [ ] **Step 2: Add the new script directly after `generate:node-types-contract`**

Add this line to the `scripts` block:

```json
"generate:node-dispatch-contract": "node --max-old-space-size=4096 ./node_modules/ts-node/dist/bin.js -r tsconfig-paths/register scripts/generate-node-dispatch-contract.ts",
```

- [ ] **Step 3: Run the script and confirm it writes the JSON**

Run: `pnpm generate:node-dispatch-contract` from `back/`.

Expected: prints `Wrote 28 node dispatch entries to <abs path>/node-dispatch-contract.json` (28 is today's count — if the registry has grown by the time this ships, use the current count; the spec, not this number, is what will keep it honest).

---

### Task 4: Verify the drift spec now passes

**Files:**
- Read only.

- [ ] **Step 1: Re-run the drift spec**

Run: `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.

Expected: all four tests pass (`matches the registry exactly`, `names the registry file`, `cross-links the worker-enum snapshot`, `sorts node types`).

- [ ] **Step 2: Negative control — flip one registry field and observe the drift spec fail**

Edit `back/src/shared/node-dispatch/node-dispatch-registry.ts`: change `commandTextNode.prefetchSafe` from `false` to `true`.

Run: `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.

Expected: `matches the registry exactly` fails with a diff on `commandTextNode.prefetchSafe`. Record this failure in the PR body.

Revert the registry edit.

- [ ] **Step 3: Negative control — hand-edit the committed JSON and observe the drift spec fail**

Edit `back/src/shared/node-dispatch/node-dispatch-contract.json`: change `commandTextNode.prefetchSafe` to `true`.

Run: `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.

Expected: same failure as Step 2, but pointing at the committed file. Record this failure too.

Regenerate with `pnpm generate:node-dispatch-contract` to restore the file.

---

### Task 5: Cross-link the sibling drift spec

**Files:**
- Modify: `back/src/shared/node-dispatch/node-types-contract.spec.ts`

- [ ] **Step 1: Read the current header of `node-types-contract.spec.ts` and identify a natural place for a one-line pointer**

The file's `describe('node-types contract drift', ...)` block is the analogue of the new spec. Add one line above that block, so a reader of the enum-snapshot spec discovers the fuller dispatch contract.

- [ ] **Step 2: Add the pointer as a single-line comment above the `describe` block**

Insert directly before `describe('node-types contract drift', () => {`:

```ts
// The fuller published contract lives in node-dispatch-contract.json, kept in
// sync by node-dispatch-contract.spec.ts. This spec covers the worker-enum
// snapshot only.
```

(This is the ONE comment this task adds in code. The workspace convention forbids comments, but a cross-link between two drift specs is a why, not a what — a future reader must find both files or the pair is silently unenforced.)

- [ ] **Step 3: Re-run both drift specs and confirm both are green**

Run:
- `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.
- `pnpm test -- --testPathPattern=node-types-contract.spec` from `back/`.

Expected: both green.

---

## PART 2 — Refresh the migration skill

### Task 6: Capture the SHAs the skill will cite

**Files:**
- Read only.

- [ ] **Step 1: Record the SHAs for the four repos at the moment of writing**

From `back/`: `git rev-parse HEAD`
From `worker/` (or the sibling checkout `WORKER_REPO_PATH` points at): `git rev-parse HEAD`
From `front/`: `git rev-parse HEAD`
From `Workflow/`: `git rev-parse HEAD`

Write them down. They go into the skill's front-matter block in Task 7 and into the PR body per D1's discipline: "every claim in the refreshed skill is checked against the code at the time of writing, with the SHA recorded."

- [ ] **Step 2: Confirm the four gate call sites**

Grep to confirm each gate is a registry read today:

- `dispatchesToWorker` used from `flux.service.ts` `isTemporalNode` — `grep -n "dispatchesToWorker" back/src/app-api/flux/flux.service.ts`
- `isWorkerRoutedIntegration` — `grep -n "isWorkerRoutedIntegration" back/src/shared/integration/integration-executable-node.ts back/src/app-api/flux/flux.service.ts`
- `isMigratedTemporalNode` / `isLegacyRunnableNode` — `grep -n "isMigratedTemporalNode\|isLegacyRunnableNode" back/src/temporal/single-node-legacy/`
- `isPrefetchSafeNodeType` and `canUsePrefetchForFlow` — `grep -n "isPrefetchSafeNodeType\|canUsePrefetchForFlow" back/src/app-api/flux/`

Record file:symbol for each. The skill's four-gates section names them, so if any moved between the SHA and now, the skill would be born stale.

---

### Task 7: Rewrite the skill

**Files:**
- Modify: `Workflow/skills/node-worker-migration/SKILL.md`

- [ ] **Step 1: Read the current skill end-to-end**

Open `Workflow/skills/node-worker-migration/SKILL.md`. The rewrite touches every section — do not diff it line-by-line; treat it as a full replacement of the body while keeping the front-matter shape.

- [ ] **Step 2: Replace the file body with the refreshed content**

Overwrite the file with:

````markdown
---
name: node-worker-migration
description: How to profile a FluxPrompt node type across front/back/worker, assess whether its execution should be migrated INTO the Temporal worker, drive the go/no-go decision with the user, and — if go — kick off the migration spec + docs. Load this whenever the user wants to "migrate node X to the worker", "move a node's execution to the worker", asks whether a node belongs in the worker, or references the worker-migration-object_caller line of work. Read-only analysis; it never migrates code itself — it produces a profile, a fitness verdict, and (on go) a spec skeleton.
license: CC-BY-4.0
---

# Node → worker migration

FluxPrompt executes node types in **two different places**. The published, machine-readable answer to "which node types does the worker have modules for, and how does the flow loop dispatch each one?" lives in **`back/src/shared/node-dispatch/node-dispatch-contract.json`** (source: `back/src/shared/node-dispatch/node-dispatch-registry.ts`; kept in sync by `node-dispatch-contract.spec.ts` — the file is generated from the registry with `pnpm generate:node-dispatch-contract`, so an out-of-date claim in this skill is a spec failure, not a maintenance chore).

**Read the contract before making any claim about which node types the worker covers.** This skill never states "the worker has N types" or lists them — the contract is the answer, and its shape is stable enough that "look at `nodeTypes` in the contract" is what the skill says instead. When B4 or a later task changes the worker's execution shape, the citation stays; only the referenced content moves.

Migrating a node "to the worker" means moving its execution from the inline path in `back/src/app-api/flux/flux.service.ts` to a worker module the flow loop dispatches to. **This is not always the right move** — some nodes are so coupled to backend engine state that extracting them costs more than it saves. The point of this skill is to make that call *with evidence*, not optimistically.

## The one hard rule

**Never start writing migration code or a spec until the user has explicitly chosen GO on the fitness verdict.** The user framed this line of work as "maybe it doesn't make sense depending on what the node does." Respect that: profile → verdict → *ask* → only then spec. Producing the profile and verdict is always in scope; acting on them is not until the user says go.

## Phase 1 — Profile the node (read-only, across all repos)

Produce a factual profile. For the node type in question:

1. **Resolve the type string.** The FE/DB node-type key is often NOT the component name. Resolve through `front/src/util/nodeTypes.tsx` (`<typeKey>: <Component>`). Example: Object Caller is `nodesBox` → `ObjectCaller.tsx`. If you're unsure of the mapping, load the `mcp-node-schema-sync` skill's known-surprises list or read `nodeTypes.tsx` directly.
2. **Front data shape.** Read the component under `front/src/components/nodes/`. List every `data.*` field it reads/writes, noting scalars vs nested objects vs array-of-objects, and dynamic/computed keys (e.g. Object Caller's `data[<textId>+'checked']` / `data[<textId>+'-in']`).
3. **Where it executes today.** Look up the type in `back/src/shared/node-dispatch/node-dispatch-contract.json`:
   - `flowDispatch: "worker"` — the flow loop already dispatches it to Temporal (`flux.service.ts` `isTemporalNode` reads `dispatchesToWorker`, which reads the registry). Migration is *maintenance*, not a route change.
   - `flowDispatch: "inline"` + `workerModule: true` — a **stranded** worker module. Something built the activity but the flow loop still runs the inline path; `strandedReason` in the registry names the reason and (if applicable) the epic task that owns finishing it.
   - `flowDispatch: "inline"` + `workerModule: false` — the honest "not migrated yet" case. This is where a new migration lives.
   - Also grep `back/src/app-api/flux/flux.service.ts` for the type string, and for a handler method named after the node (e.g. `objectCaller(...)`). Record the entry method + **every backend service/parameter it depends on** (e.g. `objectCallerData`, `sessionStateService`, `objectsService`, `onMutateSchema`, `onMutateObjectCallerData`, `spaceId`, `u`).
4. **Confirm what's already on the worker.** Look up the type in `back/src/shared/node-dispatch/node-types.contract.json` — that file is generated from `worker/src/modules/nodes/nodes.types.ts` and answers "does the worker's `NodeType` enum carry this string?" without needing the worker repo checked out.
5. **MCP surface.** Check `back/src/app-mcp/node-types/node-type-metadata.ts` for an entry (many nodes have none). That file is a hand-maintained JSON catalog — the exact drift pattern the dispatch registry exists **not** to reproduce — so an entry there proves nothing about worker coverage; use the contract for that.
6. **I/O and side effects.** Classify what the node actually does: pure compute? external I/O (HTTP/DB)? reads/writes user objects? mutates flow schema mid-run? streams chunks? maintains session state across runs?

## Phase 2 — The four dispatch gates

Every migrated node type is routed by **four separate predicates**, each with a different consumer. All four are registry reads today (Task A1 of the worker-flow-execution epic); the registry is what a migration writes to, and the four gates are what read from it. **A migration that adds a worker module but writes to only one of these gates ships a node the worker can technically run but no path actually reaches** — that is the failure mode that produced the `thirdPartyIntegration`, `sqlQuerier`, and `audioReaderNode` inconsistencies A1 was cutting.

Look up each gate for the node type in the contract:

| Gate | Registry field | Consumer | What it decides |
|---|---|---|---|
| Flow-loop dispatch | `flowDispatch: "worker"` | `FluxService.apiV2()` and `executeSingleNode()` in `back/src/app-api/flux/flux.service.ts` (via `isTemporalNode` → `dispatchesToWorker`) | Whether the flow loop hands the node to Temporal or runs it inline. |
| Integration gate | `integrationExecutable: true` and/or `integrationProviders: [...]` and/or `dedicatedProvider: "..."` | `isWorkerRoutedIntegration` in `back/src/shared/integration/integration-executable-node.ts` | Whether a `thirdPartyIntegration` (or a dedicated-provider node like `hubSpotCRM`) is routed to the worker per-provider. Nodes routed here look "not routable" to the flow-loop gate. |
| Legacy endpoint verdict | `legacyEndpoint: "accept" \| "refuse-migrated" \| "refuse-mutating" \| "refuse-unsupported"` | `/process/single-node-legacy` allowlist in `back/src/temporal/single-node-legacy/legacy-allowlist.ts` (`isMigratedTemporalNode`, `isLegacyRunnableNode`, `isMutatingNodeType`) | Whether the standalone single-node endpoint accepts the type, refuses as migrated (Temporal has it), refuses as mutating (schema mutation), or refuses as unsupported. |
| Prefetch eligibility | `prefetchSafe: true` | `isPrefetchSafeNodeType` and `canUsePrefetchForFlow` in `back/src/app-api/flux/flux.service.ts` and `back/src/app-api/flux/prefetch/` | Whether a flow containing this node type may run through the prefetch executor. **A new type not marked `prefetchSafe` silently disqualifies every flow that carries it** — this is a refusal, so treat it as one (§3.3.2 of PLAN.md: measure before refusing). |

A new node type **must** appear in the registry with each of these fields set on purpose. If two fields conflict (e.g. `flowDispatch: "worker"` with `legacyEndpoint: "accept"`), `hasDispatchConflict` in the registry names the pair and `node-dispatch-invariants.spec.ts` fails.

## Phase 3 — Fitness assessment (the "does this make sense?" gate)

Score the node against what the worker execution model can cleanly support. Today's template is: a node **fetches its own config from the DB by id** (`ExecuteNodeActivityProps = {execId, nodeId, sessionId, userId, flowId, flowVersionHistoryId, socketId?}`), runs `fetch → validate → execute → persistNodeSuccess → return DTO`, talks back via **DB writes**, **Redis pub/sub** (status/stream), and **HTTP callbacks** to the main API (`/worker/store-payload`, `/worker/charge-tokens`, `/worker/validate-model-access`, `/worker/generate-file`). It does NOT receive engine in-memory state.

**This template is stable as of today, and is scheduled to change under epic task B4 (graph workflow).** When B4 lands, the flow's DAG loop moves inside a Temporal workflow and per-node input resolution moves next to the node (B3). The migration template will change with it. Do not commit to "the activity template is the only shape" — cite `back/src/shared/node-dispatch/node-dispatch-contract.json` for what the current template is, and let the section that describes it be a citation update, not a rewrite, when B4 ships.

**Good fit (favor GO):**
- Self-contained execution: input derivable from the node row + a small set of ids.
- Long-running / CPU- or IO-bound / rate-limited work that benefits from Temporal retries, timeouts, heartbeats (API calls, transcription, SQL, heavy compute).
- Side effects expressible as DB writes + existing callbacks.
- Little or no dependence on mutable engine-scoped state passed by reference.

**Poor fit (favor NO-GO / defer):**
- Heavy dependence on engine parameters threaded by reference (`onMutateSchema`, `onMutate<X>Data`, in-memory merged node arrays) — these have no equivalent in the activity model without new endpoints/DB contracts.
- Mid-run mutation of *other* nodes' data or the flow schema.
- Tight coupling to backend-only services with no worker equivalent, where replicating them (or adding callbacks) dwarfs the node's own logic.
- Cross-node/cross-run shared state (e.g. session state scoped to objects) that the back currently coordinates transactionally.

Deliver the verdict as: **GO / GO-WITH-CAVEATS / NO-GO**, each with the concrete blockers and, for GO-WITH-CAVEATS, the new contracts (endpoints/DB columns/callbacks) the migration would have to introduce first.

## Phase 3b — The blocking-wait cost

Every migrated node today is a **synchronous, blocking round trip** inside `FluxService.apiV2()`: the flow loop starts a workflow, waits for it, resumes the loop with the result, then dispatches the next node. See PLAN.md §R4 for the epic's honest statement of the cost. Migrating a node **increases per-node latency** — extraction overhead + Temporal round trip — and does not reduce total flow time until B4 (graph workflow) and B5 (parallel dispatch) both ship.

State this cost in the fitness verdict. A GO that promises "faster" is wrong today; a GO that promises "Temporal retries/timeouts/heartbeats" is honest. If the node is on the hot path for a customer whose flows have to complete in a fixed budget, the answer might be **defer**, not migrate: wait until B5 makes parallel dispatch available, then reassess.

## Phase 3c — The prefetch path

`canUsePrefetchForFlow` is a refusing rule (PLAN.md §3.3.2: **measure before refusing**). A new node type not marked `prefetchSafe: true` disqualifies every flow that carries it from the prefetch executor. Ask the two questions in this order:

1. **Does the new node type belong on the prefetch whitelist?** A node is prefetch-safe when its input can be resolved from prior node outputs alone (no engine-scoped state, no mid-run mutation of another node). Most worker-side compute qualifies. Answer yes/no with evidence, not by default.
2. **If yes**, set `prefetchSafe: true` in the registry entry. If no, set `prefetchSafe: false` and state the reason in the entry's `note`. Do not omit the field.

If the node is `flowDispatch: "inline"` and phantom/non-executable (like `comment`, `label`, `group`), `prefetchSafe: true` is deliberate: a decoration should not cost a flow its prefetch eligibility. `NON_EXECUTABLE_NODE_TYPES` in `back/src/app-api/flux/prefetch/is-non-executable.ts` is the canonical set, and `node-dispatch-registry.spec.ts` binds the two so they cannot drift.

## Phase 4 — Ask the user (decision gate)

Present the profile + verdict compactly and ask the user to choose: proceed with migration, defer, or drop. Do not assume. If the verdict is NO-GO, say so plainly and let the user override — they may still want it for consistency reasons.

## Phase 5 — On GO: kick off spec + docs (only after explicit go-ahead)

### The seven layers plus the registry — the definition of done (PLAN.md §3.4)

A node is **not** done when its activity exists. All eight must hold:

1. **Worker module** at `worker/src/modules/nodes/<node>/`: `.module.ts` (provider + **export** service), `.service.ts` (`@Injectable`, inject `DatabaseService`, single `process(props)` = fetch→validate→execute→`persistNodeSuccess`→DTO), `.type.ts` (response DTO), `.service.spec.ts`.
2. **`nodes.types.ts` enum entry** (value = FE/DB type string).
3. **`temporal.module.ts`** import + inject service into `ActivitiesService` constructor.
4. **`activities.service.ts`**: `<node>Activity(props)` wrapped in `runNodeActivity("<node>", ...)`.
5. **`worker.service.ts`** activity binding + **`workflows/configs.ts`** `proxyActivities` proxy (with `startToCloseTimeout`/`heartbeatTimeout`).
6. **`process-single-node.workflow.ts`**: `case NodeType.X:` calling the proxied activity.
7. **Backend inline twin removed or guarded** in `back/src/app-api/flux/flux.service.ts`, plus any new `/worker/*` callback the fitness verdict flagged.
8. **Registered in the single dispatch registry** at `back/src/shared/node-dispatch/node-dispatch-registry.ts` with all four fields (`flowDispatch`, `legacyEndpoint`, `prefetchSafe`, `workerModule`) set on purpose. Missing this step is exactly the drift the registry exists to prevent — the four gates read the registry, not the enum.

Reachable from **both** entry paths (a full flow run and a single-node run) and errors thrown as the right `NodeError` subclass (`UserConfigError` / `IntegrationError` / `ProviderError` / `TimeoutError` / `SystemError`) are properties of steps 6 and 7, not separate boxes.

### The rest of the migration

1. **Spec.** Invoke the `tlc-spec-driven` skill to specify the migration feature under `.claude/tasks/worker-<node>-migration/`. The task breakdown must cover the eight items above (skipping one produces a node the worker "runs" doing nothing, or one gate refuses while the other accepts).
2. **Docs.** Author a Mintlify page under `docs/worker/` describing the node's functionality now that the worker owns it (what it does, its inputs/outputs, retry/timeout behavior, any new callbacks). Use the `mintlify-docs-writer` agent. Add en + pt-br per the docs repo convention.
3. **Env vars.** If the migration adds any env var (worker or back), run the `env-vars-sync` skill.
4. **Node schema.** If the node gains/needs an MCP entry, run `mcp-node-schema-sync` before touching `node-type-metadata.ts`.
5. **`validate-changes` skill** before the PR (PLAN.md §3.3.4).
6. **Regenerate the contract** if the worker enum grew: `pnpm generate:node-dispatch-contract` and `pnpm generate:node-types-contract` from `back/`, so both drift specs pass.

## The Object Caller worked example — verdict pending A7

`nodesBox` (Object Caller) executes at `flux.service.ts` inside `objectCaller(...)`; depends on `objectCallerData` (threaded engine-wide), `sessionStateService` (scope `'object'`), `objectsService`, and two `onMutate*` callbacks; mutates object data mid-run. **On today's template alone this profile reads NO-GO** — a migration would need to expose objects + session-state + object-data mutation to the worker.

**Epic task A7 changes the answer** — it migrates `nodesBox` behind two new callbacks and an ordering guarantee, gated on B1's execution identity. Do not cite this example as precedent for a NO-GO on similar profiles: A7 is the answer for `nodesBox`, and its callbacks are the pattern for future engine-coupled types. Look at the registry entry's `strandedReason` and `handoffOwner` when the type has one — they name the task and the reason, and are the fastest way to find out whether the honest answer is "not yet" rather than "not ever."

## Reporting format

- **Profile:** type string, component, current execution site (file:line), dependencies, I/O class, MCP presence — all with file:line evidence. Every claim in this skill was checked against the code at the SHAs listed above.
- **Verdict:** GO / GO-WITH-CAVEATS / NO-GO + blockers + required new contracts. Include the blocking-wait cost and the prefetch answer explicitly — they are the two things this skill used to say nothing about.
- **Decision prompt:** the explicit question to the user.
- Never fabricate a "clean fit" — an honest NO-GO is the valuable output here.

## SHAs at the time of writing

Insert here at authoring time:

```
back:    <sha>
worker:  <sha>
front:   <sha>
Workflow: <sha>
```

The four SHAs anchor every claim in this skill. If a later task moves any of the file paths named in Phase 2, this skill's SHAs are the pointer that lets a reader tell "moved since" from "always was."
````

- [ ] **Step 3: Grep the finished skill for stale enumeration patterns**

Run these greps against `Workflow/skills/node-worker-migration/SKILL.md`:

- `grep -nE 'as of [0-9]{4}-[0-9]{2}' .claude/skills/node-worker-migration/SKILL.md`
- `grep -nE '\b(ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)( |,|\.| types)' .claude/skills/node-worker-migration/SKILL.md`
- `grep -nE '\b(commandTextNode|outputObjectNode|globalStarter|scripting|audioReaderNode|mathFunction|apiCaller|counterNode|sqlQuerier|outputController|commandContentNode|voiceBoxNode|webSearch|voiceNode|webCrawling|thirdPartyIntegration|hubSpotCRM|mcpNode|imageGenerator|pullData|pushData)\b' .claude/skills/node-worker-migration/SKILL.md`

Expected:
- The first two return no matches. Any hit is a fact with an expiry date and no expiry mechanism — the exact drift this task exists to end.
- The third grep will hit `nodesBox` (the Object Caller section), `NodeType.X` (placeholder in the definition of done), and possibly `thirdPartyIntegration`, `sqlQuerier`, `audioReaderNode` in the "failure mode that produced X, Y, Z inconsistencies" prose. Those are named for a reason (they are the historical defects), and are not enumeration — accept them. **Any other type name that survives is a stale enumeration.**

If a stale enumeration survived, remove it and repeat the grep before moving to Step 4.

- [ ] **Step 4: Substitute the four real SHAs recorded in Task 6 for the `<sha>` placeholders at the bottom of the skill**

The block at the bottom of the file reads:

```
back:    <sha>
worker:  <sha>
front:   <sha>
Workflow: <sha>
```

Replace each `<sha>` with the seven-character (or longer) short SHA recorded in Task 6. If any of the four SHAs is missing at this point, go back to Task 6 — the skill claims are anchored to those four commits and shipping without them defeats the whole "checked against the code at the time of writing" gate.

---

## PART 3 — The workspace CLAUDE.md pointer

### Task 8: Add the section

**Files:**
- Modify: `Workflow/CLAUDE.md`

- [ ] **Step 1: Read the current file end-to-end to pick the right insertion point**

Read `Workflow/CLAUDE.md`. The existing structure is: Workspace Structure → Git Branch Strategy → Project Overview → Common Commands → Coding Rules → Architecture Overview → Local Development Quick Start → Claude Code Agents (which mentions skills). The new section is skill-adjacent; insert it as a new `##` block **between "Architecture Overview" and "Local Development Quick Start"**, so it sits with the other cross-repo architecture facts a new-comer needs.

- [ ] **Step 2: Insert the new section**

Insert this block between the "Architecture Overview" section and the "Local Development Quick Start" section:

```markdown
## Adding or changing a node type

Node execution is split between `back` (inline) and `worker` (Temporal activities). **Adding or changing a node type touches seven files plus one registry entry** — miss any and the type is either silently non-executable or dispatched by only one of the four gates.

**The published contract:** `back/src/shared/node-dispatch/node-dispatch-contract.json` is a machine-readable, test-enforced projection of the dispatch registry (`back/src/shared/node-dispatch/node-dispatch-registry.ts`). It answers "for each node type: does the flow loop dispatch it to the worker? Does the legacy endpoint accept it? Is it prefetch-safe? Does the worker have a module for it?" Read the contract before making any claim about coverage. Regenerate with `pnpm generate:node-dispatch-contract` from `back/`; two Jest specs fail if it drifts (`node-dispatch-contract.spec.ts`, `node-types-contract.spec.ts`).

**The seven layers plus the registry** (see PLAN.md §3.4 in `.claude/tasks/worker-flow-execution-epic/`):

1. Worker module at `worker/src/modules/nodes/<node>/` (`.module.ts`, `.service.ts`, `.type.ts`, `.service.spec.ts`).
2. `nodes.types.ts` enum entry.
3. `temporal.module.ts` import + `ActivitiesService` constructor injection.
4. `activities.service.ts` `<node>Activity` wrapped in `runNodeActivity`.
5. `worker.service.ts` activity binding + `workflows/configs.ts` `proxyActivities` proxy.
6. `process-single-node.workflow.ts` `case NodeType.X:`.
7. Backend inline twin in `back/src/app-api/flux/flux.service.ts` deleted or guarded.
8. `back/src/shared/node-dispatch/node-dispatch-registry.ts` entry with all four fields (`flowDispatch`, `legacyEndpoint`, `prefetchSafe`, `workerModule`) set on purpose.

**Skills to run** before the PR:

- `mcp-node-schema-sync` — if the change touches `back/src/app-mcp/node-types/node-type-metadata.ts`, a `front/src/components/nodes/` component, or a `worker/src/modules/nodes/` module.
- `env-vars-sync` — if the change adds any env var.
- `validate-changes` — always.

The full runbook lives in `.claude/skills/node-worker-migration/SKILL.md` (`SKILL.md` covers profiling, the four dispatch gates, the fitness verdict, the blocking-wait cost, and the prefetch path). Load it whenever "migrate node X" is on the table — the CLAUDE.md paragraph is for the agent that never loads the skill, not a replacement for it.
```

- [ ] **Step 3: Skim the surrounding sections for a repeated fact**

Re-read the two sections above and below the new one. If either restates something the new section says (e.g. "the workspace has two repos" appears twice), the new section is fine because it names the four repos in the contract quote; do not touch the neighbours. If a neighbour has an outdated pointer to the migration skill without mentioning the contract, note it in the PR body — do not edit it here (out of D2's scope).

---

## Negative controls to run before opening the PR

These four negative controls prove the drift specs actually fail on the manufactured breakages they exist to catch. Because the implementer of this task cannot run shell commands, the controls are documented here for the user to run locally before opening the PR — the exact edit, the exact command, and the exact expected failure message for each. Paste the observed messages into the PR body.

### Control 1: registry edit fails the new drift spec

Purpose: prove `node-dispatch-contract.spec.ts` catches a registry that has moved past the committed JSON.

- **Edit:** `back/src/shared/node-dispatch/node-dispatch-registry.ts` — change `commandTextNode.prefetchSafe` from `false` to `true`.
- **Command:** `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.
- **Expected failure:** the `matches the registry exactly (regenerate with pnpm generate:node-dispatch-contract)` test fails with a Jest diff on `nodeTypes.commandTextNode.prefetchSafe` (`false` in the file, `true` in the fresh contract).
- **Revert:** restore the registry edit, re-run the spec — should be green.

### Control 2: committed-JSON edit fails the new drift spec

Purpose: prove the drift spec catches a hand-edit to the committed file (the mirror of Control 1).

- **Edit:** `back/src/shared/node-dispatch/node-dispatch-contract.json` — change `commandTextNode.prefetchSafe` from `false` to `true`.
- **Command:** `pnpm test -- --testPathPattern=node-dispatch-contract.spec` from `back/`.
- **Expected failure:** the same `matches the registry exactly` test fails with the diff pointing at the committed JSON.
- **Revert:** run `pnpm generate:node-dispatch-contract` from `back/` to regenerate the file, re-run the spec — should be green.

### Control 3: registry-without-entry fails the sibling drift spec

Purpose: prove `node-types-contract.spec.ts` still catches the "agent adds a worker module and forgets the registry" mistake (this control is unchanged by D2 — it existed under A1, and D2 must not have broken it).

- **Edit:** `back/src/shared/node-dispatch/node-dispatch-registry.ts` — delete the `thirdPartyIntegration` entry (the `thirdPartyIntegration: { … }` block that includes the `integrationProviders` set). Do NOT touch `node-types.contract.json`.
- **Command:** `pnpm test -- --testPathPattern=node-types-contract.spec` from `back/`.
- **Expected failure:** `registers every node type the worker can run` fails, naming `thirdPartyIntegration` as the unregistered type in the array-equality assertion.
- **Revert:** restore the entry, re-run the spec — should be green.

### Control 4: worker enum bump without registry entry fails the sibling drift spec

Purpose: prove the sibling spec catches the "agent adds a type to the worker enum but not the registry" mistake, end-to-end through the enum-contract generator.

- **Edit:** in the sibling `worker/` checkout (or the path `WORKER_REPO_PATH` points at), add `FAKE_NODE = "fakeNode"` to the `NodeType` enum in `worker/src/modules/nodes/nodes.types.ts`.
- **Commands (in order):**
  1. `pnpm generate:node-types-contract` from `back/` — regenerates `node-types.contract.json` from the mutated worker enum.
  2. `pnpm test -- --testPathPattern=node-types-contract.spec` from `back/`.
- **Expected failure:** `registers every node type the worker can run` fails, naming `fakeNode` as the unregistered type.
- **Revert:** remove the enum entry in `worker/`, then run `pnpm generate:node-types-contract` again — should restore the committed JSON; re-run the spec — should be green.

### Green baseline (run first)

Before running the four controls, confirm the baseline is green so a failure below is caused by the manufactured edit and not by pre-existing drift:

- `pnpm generate:node-dispatch-contract` — should exit with `Wrote <N> node dispatch entries to …/node-dispatch-contract.json` and leave **no diff** on `node-dispatch-contract.json` (this is the primary "the hand-written JSON matches the generator" gate).
- `pnpm test -- --testPathPattern=node-dispatch-contract.spec` — all four tests pass.
- `pnpm test -- --testPathPattern=node-types-contract.spec` — all four tests pass (the drift check may skip if `WORKER_REPO_PATH` is unset and there is no sibling `../worker`, which is fine — Control 4 is what exercises that path).

### PR body: the six lines to paste

Under a `## Negative controls observed` section in the PR body, paste one line per control:

- `Control 1 (registry → drift spec): <observed Jest failure message, one line>`
- `Control 2 (JSON hand-edit → drift spec): <observed Jest failure message, one line>`
- `Control 3 (registry entry deleted → sibling spec): <observed Jest failure message, one line>`
- `Control 4 (worker enum bumped → sibling spec): <observed Jest failure message, one line>`
- `Baseline: generate:node-dispatch-contract left no diff on node-dispatch-contract.json (Y/N).`
- `Baseline: both drift specs green with all edits reverted (Y/N).`

Recording the observed messages is what turns "I ran the controls" into evidence a reviewer can trust.

### Skill negative control (documentation only)

The plan originally included a Task 10 that dispatched a fresh agent against the refreshed skill and measured how many of the eight definition-of-done items it missed. That control is deferred: it requires launching a sibling agent and comparing free-form output to the eight-item list, which is out of scope for a "no commands" implementation of D2. The skill's Phase 5 subsection was written with that agent-facing test in mind — the numbered list is explicit and self-contained — and the shipping D2 PR body will note this deferral under `Skill gaps observed: deferred to a follow-up`, so the check does not fall silently off the plan.

---

## Self-review checklist (do this before opening the PR)

- [ ] Both drift specs are green: `node-dispatch-contract.spec.ts` and `node-types-contract.spec.ts`.
- [ ] The negative controls in Task 4 (steps 2 + 3), Task 9, and Task 10 all went red on the manufactured breakages, and the observed messages are in the PR body.
- [ ] The skill contains no `as of YYYY-MM` claim (Task 7 Step 3 grep clean).
- [ ] The skill contains no bare enumeration of node types outside the historical-defect list and the `nodesBox` worked example (Task 7 Step 3 grep clean).
- [ ] The skill's SHA block at the bottom has real short SHAs, not `<sha>` placeholders.
- [ ] The workspace `CLAUDE.md` names the contract file and the seven layers plus the registry.
- [ ] The workspace `CLAUDE.md` names all three skills to run (`mcp-node-schema-sync`, `env-vars-sync`, `validate-changes`).
- [ ] The workspace `CLAUDE.md` points to `.claude/skills/node-worker-migration/SKILL.md` for the full runbook, so the two entry paths (skill + workspace file) both reach the contract.
- [ ] Task 10's `## Skill gaps observed` section is in the PR body.
- [ ] `pnpm generate:node-dispatch-contract` and `pnpm generate:node-types-contract` both run clean from a fresh `back/` checkout, so a reviewer can regenerate the two JSON files locally.

## Done when

The contract is generated and test-enforced; the skill contains no stale enumeration; the workspace `CLAUDE.md` points at both the contract and the skill; a fresh agent following the skill produces a complete eight-item registration for a new node type.
