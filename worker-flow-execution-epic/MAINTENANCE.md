# Keeping this spec current

An epic spec rots in a specific way: the code ships, reality moves, and the documents keep saying
what was true when they were written. Nobody notices, because each document still reads as
internally consistent. That already happened here once — `mcpNode` shipped and three separate specs
went on stating a count that had changed, in five places, until a cross-check found them.

This file is the routine that stops it. It is short on purpose.

## 1. What derives from what

Update the source, re-run the build. Never hand-edit anything downstream.

| The source | What derives from it |
|---|---|
| `TASK-*.md` | the wording on `timeline/task-*.html`, via the content modules in `_generator/` |
| `STATUS.md` | the state chip and note on every task page |
| `PLAN.md` §7 + `DELIVERY-PLAN.md` | the `PLAN D<n>` ribbon and status on every decision block |
| `_generator/order.py` | wave membership, delivery order, prev/next links, the `#w<n>` anchors |
| `_generator/TITLES_ALL.py` | every prev/next label, in both languages |
| `_generator/tasklib.py` | the look of all 46 pages |

The HTML is **output**. If you edit it directly, the next build silently reverts you.

```bash
cd .specs/features/worker-flow-execution-epic/_generator
for b in build_w0.py w1_build.py w2_build.py w3_build.py w4_build.py w5_build.py; do python3 "$b"; done
```

## 2. The routine, by what just happened

### A task moves

Edit its row in `STATUS.md` — `state`, `ref`, and a `note` when the state needs explaining. Rebuild.
That is the whole change. **Do not write progress into the task spec**; a second copy of a state is
a second thing to forget.

When a task reaches `shipped`, do one extra thing: re-read its **Done when** section and confirm each
clause is actually true. If a clause was quietly dropped, say so in the `note` — a task that shipped
at 80% is useful information, and pretending otherwise is how the next task inherits a surprise.

### A decision gets decided

Three places, and all three matter:

1. `PLAN.md` §7 and the `DELIVERY-PLAN.md` `D<n>` table — record the answer **and the reason**.
2. The decision block in the content module — flip `status` from `'open'` to `'set'`, and rewrite
   `rec` to state what was chosen rather than what we would choose.
3. Leave the rejected options in place. A decision without its alternatives gets re-litigated by
   the next person, and the second argument is always longer than the first.

### A release changes a fact

This is the dangerous one, because nothing breaks.

```bash
python3 _generator/reconcile_facts.py     # exits 1 when documents disagree
```

Run it after any release that changes a count, an enum, or a dispatch list. When it reports drift,
fix the **documents**, not the checker — unless the pattern is genuinely over-matching, which it
will tell you to consider.

When a fact starts appearing in a second document, add a group to `GROUPS`. Then **plant the drift
on purpose and watch the check go red.** A pattern that matches nothing prints a reassuring result
and guards nothing; that is why an unmatched group is a failure, not a skip.

### Scope changes mid-flight

- **A task grows or splits** — write the new task file, add it to `_generator/order.py` (wave and
  position), to `TITLES_ALL.py` (both languages), to `STATUS.md`, and to `DELIVERY-PLAN.md`'s wave.
  Its neighbours' prev/next fix themselves on rebuild.
- **A task is dropped** — set `state: dropped` with a `note` saying why. Do not delete the page.
  The reasoning is the valuable part, and a dead link is worse than a page that says "we decided
  not to".
- **A wave reorders** — change `order.py` only. Everything else follows.
- **A premise turns out wrong** — correct it in the spec **in place, and say so**, the way
  `TASK-B1` carries its "Corrected 2026-08-24" note. A silent edit destroys the reader's ability to
  tell a considered change from a typo.

## 3. Before publishing, every time

```bash
python3 _generator/reconcile_facts.py                                   # facts agree
python3 _generator/lang_scan.py ../timeline/task-*.html ../complemento/*.html   # no language leak
# then render: no horizontal overflow, no node missing a translation, no broken link
```

The rendering check is not optional and cannot be replaced by reading the source. Every layout and
translation defect found in this project was invisible in the markup and obvious in the browser.

**Triage the language scan** — identifiers, file paths and code listings are legitimately identical
in both languages. What you are looking for is prose.

## 4. The one rule behind all of the above

**A check you have not seen fail is not a check.** Both gates in `_generator/` were vacuous when
first written, and both were caught only by planting the exact defect and watching them stay green.
Before you trust a new one, break the thing it guards.
