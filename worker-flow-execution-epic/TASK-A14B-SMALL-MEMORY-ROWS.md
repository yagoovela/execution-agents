# A14b — Store Small Memory entries as rows

ClickUp: [1gahkf3byq8](https://app.clickup.com/t/1gahkf3byq8). **Drafted 2026-11-24** from the A14 edge-case investigation
(`TASK-A14-SMALL-MEMORY-AND-CHAT-STATE.md`, "Edge-case investigation (2026-11-24)", A14-D12 and
A14-D15). Status: specified, approved by the user on 2026-11-24. This is an architecture change, not a
refactor step: it changes how a node stores data, in back, front, worker and MCP.

**Depends on:** A14 (on `main`). **Related:** B4b removes the Temporal ceiling for every flow; A14b
removes the ceilings that remain for memory itself.

## Problem statement

A non-chat Small Memory (`fluxObject`) keeps all its entries in its node's `data` jsonb, and stores
each entry twice (`entries` and `userSessionsChat.default`). Every producer write reads, merges,
sanitizes and saves the whole blob, the editor re-uploads both copies on every open, and every reader
loads the whole blob to pick the last few entries. The memory is therefore bounded by `jsonb` (about
255 MB per value), by a V8 string (about 512 MB) and by one process's RAM at several steps, and its
write cost grows with its size. Chat memory already stores rows in `session_state_entries` (scope
`flowId:nodeId`, ordered by `seq`) with a blob fallback; non-chat memory never does.

## Goals

- [ ] A non-chat memory's entries live as rows; a write appends only the new entries.
- [ ] A reader that needs the last or first X entries reads X rows, not the whole memory.
- [ ] The editor shows a memory of 100,000 entries without loading them all.
- [ ] The run seed and Temporal history carry no memory entries.
- [ ] Dedup, order, timestamps, sessions, clear-on-run and version behaviour match today's.

## Out of scope

| Item | Reason |
|---|---|
| Changing the chat memory model | It is already row-first; only shared parts move. |
| Editing or deleting a single entry in the editor | Not possible today; a product decision. |
| `commandTextNode` memories (`userSessionsChat[].memories`) | A different memory, already under scope type `memory`. |
| Object Caller (`nodesBox`) object state | A7. |

## User stories

### P1: Writes and reads scale with what they touch ⭐ MVP

**User story:** As a customer with a memory that grows every run, I want each run to cost the same
whatever the memory's size, so that my flow does not slow down or fail as it grows.

**Acceptance criteria:**

1. WHEN a producer adds an entry THEN the system SHALL insert one row and SHALL NOT rewrite the
   existing entries.
2. WHEN the same content is produced again THEN the system SHALL NOT add a row (dedup by content,
   per session when sessions are on).
3. WHEN a reader selects "Load Last X" or "Load First X" THEN the system SHALL read at most X rows.
4. WHEN a reader selects "Load All Entries" THEN the system SHALL read the rows in order up to the
   byte cap of A14b-D2, and SHALL tell the reader when entries were left out.
5. WHEN a run event is redelivered THEN the system SHALL NOT add a row twice (keyed by `execId`).

**Independent test:** a memory of 100,000 entries; one run with 10 producers; count rows read and
written and peak RSS, against the blob baseline.

### P1: Existing memories keep working during the switch ⭐ MVP

**User story:** As a customer, I want my existing memories to stay complete after the change.

**Acceptance criteria:**

1. WHEN the backfill runs THEN every non-chat memory blob SHALL become rows with the same entries,
   order and timestamps.
2. WHEN rows and a blob both exist during the transition THEN readers SHALL read rows first.
3. WHEN a memory was copied into chat rows by the June backfills although it is not a chat memory
   THEN the system SHALL NOT serve those rows as its entries (check on dev first).

### P1: The editor and MCP read pages ⭐ MVP

1. WHEN the editor opens a memory THEN it SHALL load one page of entries and SHALL NOT re-upload
   entries it did not change.
2. WHEN the user clears a memory THEN the system SHALL delete its rows.
3. WHEN MCP `get_agent` or `export_agent` returns a memory node THEN it SHALL NOT embed every entry.

### P2: Versions keep today's behaviour

1. WHEN a version is published or rolled back THEN the deployed memory SHALL be what it is today
   (copied from the source version).
2. WHEN a flow is duplicated THEN its memory rows SHALL be copied; WHEN a template or a chatbot share
   is created THEN they SHALL NOT be.

## Edge cases

- WHEN an entry is empty or only `\n` THEN it SHALL be skipped, as today.
- WHEN "Load First/Last X Words" reads an empty memory THEN it SHALL return an empty value, not
  throw (today it throws on `connectedText[0].content`).
- WHEN "Load Last X" feeds an `outputObjectNode` THEN it SHALL keep today's behaviour (all entries)
  unless A14b-D2 changes it.
- WHEN `clearOnExecution` is on THEN the run start SHALL delete the rows before the first append.

## Decisions to settle (discuss)

| ID | Question | Recommendation | Alternative |
|---|---|---|---|
| A14b-D1 | Where the rows live | `session_state_entries` with a new scope type `smallMemory`, plus `flowVersionHistoryId`, `contentHash` (unique, for dedup) and `entryAt` | A new table; or keep the blob with a cap or rotation (changes semantics: old entries drop) |
| A14b-D2 | "Load All Entries" on a huge memory | **Open (2026-11-24).** Recommended: keep the newest entries up to a byte cap and tell the reader how many were left out. The cap bounds worker RAM; memory content never enters Temporal history (`resolveNodeInputActivity` returns nothing, the resolved input goes to `node_executions` and S3). The user asked to size the cap from evidence: production memory sizes (`a14-q4`, `a14-q11`) and the worker's RAM history in CloudWatch, and to consider a per-worker ceiling, a cap that follows free memory, or a pre-check that the read fits. Settle in Design without over-engineering | No cap (the reader then hits the model's context limit and the worker holds the whole memory) |
| A14b-D3 | Owner of non-chat rows | No owner (shared by every user, as the blob is today) | Per-user rows |
| A14b-D4 | Publish and rollback | **Settled (2026-11-24):** copy rows, as the blob is copied today | Point the version at the source rows (cheaper, changes isolation) |
| A14b-D5 | Rollout | Backfill as a Bull job, read rows first with blob fallback, stop writing the blob in a later release | One-shot switch |

## Requirement traceability

| ID | Story | Status |
|---|---|---|
| MEMR-01 | P1 scale: append one row per entry | Pending |
| MEMR-02 | P1 scale: dedup by content hash | Pending |
| MEMR-03 | P1 scale: LAST/FIRST X read X rows | Pending |
| MEMR-04 | P1 scale: Load All with a byte cap | Pending |
| MEMR-05 | P1 scale: idempotent on redelivery | Pending |
| MEMR-06 | P1 switch: backfill, rows first | Pending |
| MEMR-07 | P1 switch: June backfill rows not served | Pending |
| MEMR-08 | P1 editor and MCP: pages, clear, no echo | Pending |
| MEMR-09 | P2 versions and duplicates | Pending |

## Measurement before designing

Production queries, run by the user: `a14-q4` (memory size distribution), `a14-q8` (memory on
history rows and copies per node), `a14-q9` (non-chat memories that also have chat rows), `a14-q10`
(configuration distribution), `a14-q11` (longest single entry).

## Estimate

70 to 110 h. Back about 14 to 18 files (entity and migration, session-state service, edge-projection
reader and writer, run start and clear, A14 writer and reader, flow controller, version and duplicate
copies, backfill job, MCP metadata), worker 3 to 4, front 6 to 8 (Small Memory component, append
logic, paged table, chatbot mapper), mcp-server 0 to 1.

## Test list (must pass)

1. Negative control: on `main`, a run against a memory of 100,000 entries reads and rewrites the whole
   blob; after the change it inserts one row per new entry and reads at most X rows for "Load Last
   X", measured by query count and peak RSS.
2. A repeated content adds no row; a redelivered run event adds no row.
3. "Load All Entries" over the cap returns the newest entries within the cap and says how many were
   left out.
4. The backfill turns every dev memory blob into rows with the same count, order, timestamps and a
   matching hash per memory.
5. A non-chat memory that the June backfills copied into chat rows reads its own entries, not those
   rows.
6. The editor opens a memory of 100,000 entries with one page loaded and no re-upload; Clear deletes
   the rows.
7. Publish, rollback and duplicate copy the rows; a template and a chatbot share do not.
8. MCP `get_agent` and `export_agent` return a memory node without every entry.
9. A14's parity corpus gives the same reader input and stored entries on both engines.

## Success criteria

- [ ] A run against a memory of 100,000 entries reads and writes O(new entries) rows, measured.
- [ ] The parity corpus of A14 gives the same reader input and the same stored entries.
- [ ] No memory loses an entry in the backfill, checked by count and hash per memory on dev.
