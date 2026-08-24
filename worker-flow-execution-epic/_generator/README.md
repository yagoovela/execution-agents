# `_generator` — the source of the published pages

The HTML under `timeline/`, `complemento/` and the two hub pages is **generated**. This folder is
that generator, and it lives here rather than in a scratch directory for one reason: a deliverable
whose source is disposable can only be edited by hand-patching its own output, and every later
change then drifts away from the thing that produced it.

> Change the content module, re-run the build, re-run the checks. Do not hand-edit the HTML.

## Layout

| File | What it is |
|---|---|
| `tasklib.py` | The renderer: the stylesheet (`BASE` + `EXTRA_CSS` + `DECISION_CSS`), the content model, and `render()`/`write()`. **Every page's look lives here.** |
| `order.py` | Wave membership, the delivery order, the `complemento/` phase each task maps to, and `nav()` which resolves prev/next. |
| `TITLES_ALL.py` | The canonical short title of all 32 tasks, in EN and PT. Used for prev/next labels. |
| `c_s7.py`, `d_s7.py`, `w0_*.py` … `w6_*.py` | Content modules, one group per wave. These are the text. |
| `build_w0.py`, `w1_build.py` … `w5_build.py` | Assemble a wave's content into `TASK` dicts and write the HTML. |
| `fase_realign.py` | The one-shot transform that brought `complemento/fase-*.html` onto this design system. |
| `hub_*.py` | The same for `timeline/index.html` and `arquitetura-v2-complemento.html`. |
| `lang_scan.py` | Audits pages for language leakage (see below). |
| `reconcile_facts.py` | Cross-checks facts that several documents state independently (see below). |

## Rebuilding

```bash
cd .specs/features/worker-flow-execution-epic/_generator
for b in build_w0.py w1_build.py w2_build.py w3_build.py w4_build.py w5_build.py; do python3 "$b"; done
```

Paths resolve from the script's own location, so it works from any checkout.

## The two checks, and why they exist

### `lang_scan.py` — language leakage

```bash
python3 _generator/lang_scan.py ../timeline/task-*.html ../complemento/*.html
```

Every page is bilingual through `data-en`/`data-pt` attribute pairs that a small script swaps at
runtime. The obvious check — *count nodes that have `data-en` and no `data-pt`* — **cannot detect
the failure that actually happens**: a node whose text is hard-coded in one language, which then
shows that language in **both** modes. That check reported `0` on every page while 30 such leaks
were live: three code blocks and three chips carrying Portuguese inside the English variant, and
24 `.loc` chips carrying English prose that never switched.

`lang_scan.py` looks for language-specific vocabulary on the *wrong* side of a pair, and for chips
that are not bilingual at all. It is a heuristic, so triage its output: identifiers, file paths and
code listings are legitimately identical in both languages.

**It has its own history of being wrong.** An early version stripped `<...>` as if it were an HTML
tag and silently ate `<qualquer coisa>`, hiding a real leak. Read the rendered page too.

### `reconcile_facts.py` — facts restated in several documents

```bash
python3 _generator/reconcile_facts.py     # exit 1 when documents disagree
```

A number stated in more than one spec drifts the moment reality changes, and review does not catch
it because each document reads as internally consistent. After `mcpNode` shipped, `TASK-A2` said
"the seven node types" in five places while its own body said six types plus two providers, and
`TASK-A3` said "`isTemporalNode`'s six" against `TASK-A1`'s table of 7. Nothing compared them.

Add a group whenever a fact starts appearing in a second document. Run it after any release that
changes a count.

## Before trusting either check, break something

Both checks were **vacuous when first written**, and both were only caught by planting the defect
on purpose:

- `reconcile_facts.py` reported `OK` with the A3 drift restored, because its pattern did not
  account for the closing backtick in `` `isTemporalNode`'s ``. It also had a group whose pattern
  matched nothing at all and printed a reassuring `SKIP`; an unmatched group is now a **failure**,
  because a pattern that sees nothing can never fail.
- The i18n check described above had the structural blind spot that let 30 leaks through six
  parallel agents, each of which dutifully reported `0`.

So: plant the exact defect, watch the check go red, restore, and only then trust it. A green check
that structurally cannot see the defect is worse than no check, because it reads as protection.
