# CLAUDE.md

This file tells Claude Code, and you, how to change the pages in this repository.

## What this repository is

This repository publishes the worker flow execution epic as static HTML pages: the
architecture, the plan, the timeline with one page per task, the progress page, the task
status board and the "What changed" page (`mudancas.html`).

**This repository is public.** The epic's source of truth is private: the `Workflow`
repository (`enhancedai-com/Workflow`), folder `.claude/tasks/worker-flow-execution-epic/`.
Every change is made there first and then mirrored here. Never edit a fact here that the
Workflow spec does not already say.

Before you publish a new spec file or a new task, check that it is safe to make public.
Leave it out, and ask the user, when it describes a security gap that is not fixed yet,
or carries customer data, credentials or internal hostnames. The private literal list in
Workflow (`_generator/public_redactions.json` in the epic folder) records every file,
passage and value left out, with the reason. Never write one of those values here, not
even in a redaction list: `_generator/redactions.json` holds hashes only.

## Where each fact lives

A fact about a task is written once in a source and restated on several pages.

| Fact | Source here | Restated on |
|---|---|---|
| Spec text, title, "Depends on" | `worker-flow-execution-epic/TASK-<code>-*.md` (mirror of Workflow) and the content module `_generator/w<wave>_<code>.py` | the task page |
| State, ClickUp link, status note | `worker-flow-execution-epic/STATUS.md` (mirror of Workflow) | the task page, the board, the timeline cards, the progress bars |
| Short title for navigation | `_generator/TITLES_ALL.py` | prev/next links, board cards |
| Wave and delivery order | `_generator/order.py` | prev/next links, wave sections |
| Task owners | `_generator/owners.py` (from ClickUp assignees, read only) | the owner line on each board card |

`_generator/impact.py` finds every restatement by scanning the pages, so you do not keep
this map by hand.

## Publish a change

Run every command from the repository root. Set `WORKFLOW` to your Workflow checkout and
`CODE` to the task code, for example `A11`.

1. Make the change in the Workflow spec and merge it there. Note the Workflow PR number.
2. Create a branch from `main`:

   ```bash
   git fetch origin
   git switch -c docs/<clickup-id>-<topic> origin/main
   ```

3. Mirror the spec files with the private values removed. Do not copy them with `cp`: the
   Workflow text names people, customers, email addresses and AWS profiles, and describes
   security gaps that are not fixed yet. `publish_sync.py` applies the private literal list
   that lives in Workflow, and writes nothing if a rule no longer matches its file:

   ```bash
   EPIC="$WORKFLOW/.claude/tasks/worker-flow-execution-epic"
   python3 worker-flow-execution-epic/_generator/publish_sync.py --from "$EPIC" --literals "$EPIC/_generator/public_redactions.json"
   ```

   If the change adds a person, a customer, an email address, an AWS profile or account,
   or an unfixed security gap, add a rule and a value to `public_redactions.json` in
   Workflow first. After step 6, run the same command with `--hashes` to refresh
   `_generator/redactions.json`, which stores only hashes of those values.

4. List every file that restates the changed facts:

   ```bash
   python3 worker-flow-execution-epic/_generator/impact.py $CODE
   ```

   The output has three groups: `edit (source)`, `rebuild (generated)` and
   `patch by hand`. Each line names the facts the file shows. A file that only mentions
   the task (`mention`) changes only when its sentence about the task is no longer true.

5. Update the sources in the `edit (source)` group that the change affects: the content
   module for spec text, `TITLES_ALL.py` for a new title, `order.py` for a new wave or
   order.
6. Regenerate the pages in the `rebuild (generated)` group:
   - If only the state, note or ClickUp link changed, rewrite the hero line:

     ```bash
     python3 worker-flow-execution-epic/_generator/sync_status.py $CODE
     ```

   - If the spec text or title changed, rebuild the page:

     ```bash
     python3 worker-flow-execution-epic/_generator/rebuild.py $CODE
     ```

     If `rebuild.py` refuses the code, its published page has content the content module
     lacks. Port that content into the module first, or patch the page by hand.
7. If an owner changed in ClickUp, update `_generator/owners.py` and run
   `python3 worker-flow-execution-epic/_generator/sync_owners.py`. Then patch each file in the
   `patch by hand` group: board cards and counts in
   `status-tarefas.html`, cards in `timeline/index.html`, bars in
   `progresso-refatoracao.html`, and any sentence that is no longer true.
8. Run the checks. All must pass, and `lang_scan.py` must not report more hits than
   `main` (46 on 2026-10-29). The `public redactions` group of `reconcile_facts.py` fails
   when a removed value, a removed passage, an email address outside the allowed domains,
   an AWS ARN, account id, access key or named profile appears in any published file:

   ```bash
   python3 worker-flow-execution-epic/_generator/publish_sync.py --from "$EPIC" --literals "$EPIC/_generator/public_redactions.json" --check
   python3 worker-flow-execution-epic/_generator/reconcile_facts.py
   python3 worker-flow-execution-epic/_generator/lang_scan.py timeline/task-*.html complemento/*.html
   ```

9. Commit with a signed commit, push, and open a draft PR. Use the PR body format in
   [Pull requests](#pull-requests).

   ```bash
   git commit -S -m "docs(<clickup-id>): <what changed>"
   git push -u origin HEAD
   gh pr create --draft --base main --title "[DOCS] <What changed>" --body-file <body.md>
   ```

10. Add the changelog entry with the PR number from the previous step. This writes
    `CHANGELOG.md`, renders `mudancas.html` and stamps each changed task page with
    "Updated <date> · PR #N":

    ```bash
    python3 _assets/changelog.py add --pr <N> --base origin/main \
      --title "<What changed>" --title-pt "<O que mudou>"
    ```

    If the spec or content module of a task changed and its page must stay as it is,
    say so in the entry with `--no-page-change "<CODE>: <reason>"`.

11. Run the diff check. It fails when a task's source changed and a file that
    `impact.py` maps to that change did not:

    ```bash
    python3 worker-flow-execution-epic/_generator/reconcile_facts.py --since origin/main
    ```

12. Commit, push, and mark the PR ready with `gh pr ready <N>`.

## Pull requests

- Title: `[DOCS] <Imperative summary>`.
- Body: a `Description` of what changed and why, a `Checks` section with the output of
  step 8 and step 11, and a `References` section that links the Workflow PR, the code PRs
  and the ClickUp tasks.
- Do not merge your own PR.

## Rules

- Do not edit generated HTML by hand, except a page that `rebuild.py` refuses.
- Do not run `_assets/unify_header.py` on the whole site. Each run adds blank lines to
  every page; `rebuild.py` and `changelog.py` run it on the pages they write.
- Do not write `CHANGELOG.md` or `mudancas.html` by hand; run `_assets/changelog.py`.
- Before you trust a check you changed, plant the defect it should catch and watch it
  fail. `_generator/README.md` explains why.
