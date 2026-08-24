# Status — the single source

**This table is the only place a task's state is written down.** The task pages and the timeline
read it at build time; nothing else records progress. Edit here, re-run the build, and every page
agrees. If you find status stated anywhere else, that copy is a bug — delete it and point at this
file. See `MAINTENANCE.md` for when to touch it.

`state` is one of:

| state | meaning |
|---|---|
| `planned` | Written down, not started. The default. |
| `blocked` | Cannot start — the `note` says what is in the way (a decision, another task, a measurement). |
| `doing` | Someone is working on it right now. |
| `review` | Code is up; the negative controls have been run and reported. |
| `shipped` | In production, with the definition of done satisfied. |
| `dropped` | Deliberately not doing it. The `note` says why, and that is a decision worth keeping. |

`ref` is the PR, branch or ClickUp id. Leave it `—` until there is one.

| task | state | ref | note |
|---|---|---|---|
| S7 | planned | — | |
| S1 | planned | — | |
| S4 | planned | — | Blocked on the D15 measurement before the ceilings can be numbers. |
| S5 | planned | — | Check whether the worker gets its own S3 credentials first — that would supersede it. |
| C3 | planned | — | |
| S2 | planned | — | |
| S3 | planned | — | |
| S8 | planned | — | |
| E3 | planned | — | |
| A1 | planned | — | |
| D2 | planned | — | |
| A2 | planned | — | |
| A3 | planned | — | |
| A4 | planned | — | |
| A5 | planned | — | |
| A6 | planned | — | Needs the D3 product sign-off before it becomes a behaviour change. |
| S6 | planned | — | |
| A8 | planned | — | |
| A9 | planned | — | |
| D1 | planned | — | |
| B1 | planned | — | |
| B2 | planned | — | Blocked on decision D1. |
| B3 | planned | — | Blocked on C2's measurement, which has to be pulled forward. |
| B4 | planned | — | |
| E1 | planned | — | |
| E2 | planned | — | |
| B5 | planned | — | Preconditions: S1, S2, S3, E3. |
| A7 | planned | — | |
| B6 | planned | — | Inherits D13 and D14 from S1 — do not re-open them. |
| B7 | planned | — | |
| C1 | planned | — | |
| C2 | planned | — | Owns the measurement that settles decision D2. |
