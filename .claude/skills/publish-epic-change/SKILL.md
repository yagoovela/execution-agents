---
name: publish-epic-change
description: Publish a change to the worker flow execution epic pages - a task's state, title, spec text, wave or order - from the Workflow spec to a PR here, with every page that restates the change updated, the checks passing and a changelog entry. Use when a task ships or changes state, a spec is revised, or someone asks to "publish", "republish", "sync the status" or "update the epic pages".
---

# Publish an epic change

The steps and commands are in the repository's `CLAUDE.md`, section "Publish a change".
Follow them in order. This skill adds only what an agent tends to get wrong.

## Before you start

- Read the Workflow spec, not this repository, for every fact you write. This repository
  is a public mirror.
- Run `python3 worker-flow-execution-epic/_generator/impact.py <CODE>` for every task you
  change, and keep the output. It is the checklist for steps 5 to 7.

## While you work

- A state, note or ClickUp link change needs only `sync_status.py`. Do not rebuild a page
  for it.
- When `rebuild.py` refuses a code, do not pass `--force`. The refusal means the rebuild
  would delete published content.
- A `mention` line in the impact output is a candidate, not an order. Change it only when
  its sentence about the task is no longer true.

## Before you hand back

- `reconcile_facts.py` and `reconcile_facts.py --since origin/main` both end with
  "All cross-stated facts agree."
- `lang_scan.py` reports no more hits than `main`.
- The PR links the Workflow PR, the code PRs and the ClickUp tasks, and the changelog
  entry carries the PR number.
