# E4 — Move user schedules onto Temporal Schedules

**Goal:** the durable scheduler that `S8` could not reach owns user-scheduled flow runs, with
pause, backfill and last-run visibility.

**Depends on:** **B4** — hard. **Blocked until B4 ships.** **Source:** `S8` Part 2, split out
2026-09-18 when the decision below was taken.

## Why this is a separate task, and why it is blocked

`S8` Part 2 recommended Temporal Schedules for user-scheduled flows. The recommendation was right
about the destination and wrong about the timing, and the reason is worth stating plainly rather
than rediscovering later.

**A Temporal Schedule can only trigger a workflow.** The worker exposes three today —
`processSingleNode`, `processAgent` and `completionWorkflow`. **None of them executes a whole
flow**; that workflow is what `B4` builds. So a Temporal Schedule shipped during `S8` would have
needed two pieces of scaffolding invented purely to give it something to call:

1. a `runScheduledFlow` workflow in the worker whose only job is to call back into the backend, and
2. an internal HTTP endpoint for that activity to call — which, after `S7` part 2, also has to be
   reasoned about against the rate-limit guards.

Both are thrown away the moment `B4` lands a real flow workflow. Building a bridge in order to
demolish it is not a reason to delay the safety fix that `S8` actually is, so `S8` shipped the
duplication fix on a mechanism that needs no bridge (see below) and the durable scheduler became
this task.

## What S8 shipped instead, and what it leaves for here

`S8` moved user schedules onto **Bull repeatable jobs** (decision `D26`). The schedule state left
the per-replica in-process `SchedulerRegistry` and moved into Redis, which Bull already manages;
`ApiV2Queue` — already in production — became the execution owner. Measured, three simulated
replicas registering the same schedule produced **one** repeatable and **one** execution per tick,
against **three per tick** for the shape it replaced.

That closes duplication and it closes durability across restarts and deploys. It does **not**
give:

- **pause / resume** of a schedule as a first-class operation;
- **backfill** — replaying the fires a schedule missed while it was down;
- **last-run visibility** as scheduler state rather than as a queue artefact;
- **durability independent of Redis.** Bull's repeatables live in Redis. The `schedule` table stays
  the source of truth and `S8` reconciles from it on boot, so a lost Redis is recoverable, but the
  recovery is code this repo owns rather than a platform guarantee.

Those four are what this task buys.

## Scope

**In.** `ScheduleController`'s create / update / delete drive `ScheduleClient` instead of
`ApiV2Queue`'s repeatable, with the schedule's **`id`** as the Temporal schedule id — not its
`name`, which is user-supplied and not unique (`S8` already made that change; do not regress it).

**In.** The schedule action targets `B4`'s flow workflow directly. If it still needs an
intermediate, `B4` is not done and this task is not ready.

**In.** A migration path that does not double-fire: every schedule is either a Bull repeatable or a
Temporal Schedule, never both, and the cutover is per-schedule and reversible. Under §3.2 this
ships behind the same feature flag `S8` introduced, defaulting to the Bull path.

**In.** The zombie check `S8` preserved — stop, delete, soft-delete when the flow is gone — has to
survive the move, as a schedule policy rather than as a callback body.

**In — E4-a, missed fires (open; cases expanded 2026-10-23).** When a schedule could not fire on
time, does it replay the fires it missed, or skip to now? The answer depends on the case, so the
policy is set per case, not as one global default. Temporal's `catchupWindow` defaults to one year,
so leaving it unset replays almost everything: set it on purpose.

| # | Case | What the customer expects | Proposed answer |
|---|---|---|---|
| 1 | The user paused the schedule | Nothing runs while it is paused | Skip every missed fire. Log each one as "missed: paused". |
| 2 | Short outage or deploy (shorter than one interval) | The run happens, a little late | Run the latest missed fire once, then return to the normal cadence. |
| 3 | Long outage (hours or days) | Depends on the frequency (rows 4 and 5) | Never replay more than one fire. Log the rest as "missed: outage". |
| 4 | High-frequency schedule (hourly or more often, polling) | Only the latest data matters | Skip to now. A late run of an old tick has no value. |
| 5 | Low-frequency schedule (daily, weekly report) | The missed report still arrives | Run the latest missed fire once. Replaying every missed day is option C below, per schedule, only when a customer asks. |
| 6 | The flow has side effects (email, CRM push, webhook, payment) | No duplicates | Never more than one catch-up run. A replay burst sends the same email many times. |
| 7 | The previous run is still running when the next fire comes | No pile-up | Overlap policy `SKIP`; log the fire as "missed: still running". |
| 8 | The flow was deleted or disabled while the schedule was down | Nothing runs | The zombie check refuses it, as it does today. |
| 9 | Credits or plan ran out at fire time | Nothing runs, and the user is told why | Refused by the credit gate; log "missed: no credit". Do not retry later. |
| 10 | Cutover from Bull to Temporal for that schedule | Exactly one run | One mechanism per schedule (the negative control in Verification). |
| 11 | Daylight-saving change in the schedule's time zone | One run per local day | Assert in a test that the fire neither doubles nor disappears. |

Today's baseline, to verify in the PR: a Bull repeatable keeps only its next occurrence in Redis,
so after an outage the one pending fire runs late and the others are not replayed. That is close to
rows 2 and 3. Still to decide with product: the threshold between row 4 and row 5, and whether the
missed-fire log is shown to the user or only kept for support.

**Out.** The fourteen framework crons. They stay on `S8`'s advisory lock; they are internal
maintenance and have no reason to become workflows. This was settled in `D12` and is not reopened.

## Verification

- **Negative control (required).** With the flag on for one schedule and two backend replicas,
  confirm exactly one run per fire — and confirm it was Temporal that fired it, not a surviving
  repeatable. A green count proves nothing if both mechanisms are live and one of them is idle.
- Flip the flag back and confirm the Bull repeatable resumes, with no fire lost and none doubled
  across the transition. The cutover is the risky part, not the steady state.
- Pause a schedule, wait past a fire, resume, and confirm the backfill behaviour that was chosen —
  whichever it is, assert it, because the default is not obviously the one a customer wants.
- Kill the Redis instance and confirm schedules still fire. That is the property this task adds
  over `S8`, so it is the one that has to be demonstrated rather than assumed.

## Done when

User schedules are Temporal Schedules, fire exactly once regardless of replica count, survive the
loss of Redis, and expose pause, resume and last-run state. The Bull repeatable path is deleted,
not merely disabled.

## Files

`back/src/app-api/schedule/schedule.controller.ts` · `back/src/app-api/schedule/schedule.service.ts` ·
`back/src/temporal/temporal.service.ts` (a `ScheduleClient` beside the existing `WorkflowClient`) ·
the flow workflow `B4` introduces · `back/src/jobs/apiV2Job/` (the repeatable registration `S8` adds)
