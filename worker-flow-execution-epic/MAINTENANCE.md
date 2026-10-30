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
cd .claude/tasks/worker-flow-execution-epic/_generator
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

### Node coverage — the rules that keep every type owned (added 2026-10-23)

The 2026-10-23 coverage audit found 21 of 49 node types without an owning task. The causes, and
the rule each one now carries:

1. **"Out of scope" is not a classification.** A type the epic does not migrate still gets an
   `execution` class in the registry (`worker`, `back` or `none`), or B4's gate refuses its flows.
   A11's drift spec fails on any front or MCP type without one.
2. **Classify from behaviour, not from the name.** A type is `none` only when no code reads or
   writes it at run time. `fluxObject` was called configuration-time and writes after every node.
3. **A hand-off edits the receiver.** When a task hands work to another ("when B4 lands, X becomes
   its last step"), the same PR adds that work to the receiver's Scope. A sentence only in the
   giver is a task nobody owns.
4. **"The inline twin is gone" is checked on both loops.** The full-run loop and the `arrayNode`
   loop body each dispatch by type; a Done-when about dispatch names both, and A7's reachability
   test asserts every `worker` type is dispatched by each.
5. **Coverage is re-measured at every wave exit**, from the registry against the front's
   `nodeTypes.tsx` and `node-type-metadata.ts`, not from the task list.

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

**`lang_scan.py` checks language, not agreement.** It catches English prose sitting inside `data-pt`
and Portuguese prose sitting inside `data-en` — it does not compare what the two sides *say*. Two
well-formed translations can restate a fact with different numbers and the scan reports zero hits,
because both sides are correctly written in their own language. That happened twice on 2026-09-21:
`delivery-waves.html`'s `A2` card read "six node types and two providers" in `data-en` and "sete
tipos de node e três providers" in `data-pt` — six-and-two against seven-and-three, both fluent,
neither flagged. A restated number, count or fact has to be checked in both languages by hand; this
gap is recorded rather than closed here — no new checker was built for it in this pass.

## 3b. Publishing to `execution-agents`, and the step that is easy to lose

The pages are mirrored into the `execution-agents` repo, which wraps every page in a **shared
header** — a four-tab doc-nav and one language switcher, added by that repo's own scripts. The
generator here knows nothing about it and emits the old `top-nav`, so **every regeneration strips
the shared header from whatever it rebuilds.**

That is what produced the conflict on PR #3 on 2026-09-01: eleven regenerated pages arrived without
the header while the other twenty-one had it.

After copying pages across, run that repo's two scripts, in this order:

```bash
python3 _assets/link_header_css.py     # idempotent — skips pages that already link it
python3 _assets/unify_header.py        # strips any existing doc-nav and re-inserts it
```

**`unify_header.py` is not byte-idempotent:** it appends two blank lines to every page on every run,
and it rewrites all 99 pages whether they needed it or not. So after running it, restore the pages
you did not actually change — otherwise the diff claims edits you never made, and the files grow a
little each time.

The durable fix is either to teach `tasklib.py` to emit that header, or to make `unify_header.py`
leave an unchanged page untouched. Until one of those happens, this step is manual and is the first
thing to check when a page loses its navigation.

## 3b-verify. Checking that the mirror still agrees with the spec

`reconcile_facts.py` cross-checks facts stated in *this* repo's own documents. It cannot see
`execution-agents` at all, so a page published there can drift from the spec that generated it —
silently, because both sides still read as internally consistent on their own.
`_generator/verify_publish_sync.py` is the check for that gap, keyed by `_generator/publish_manifest.json`
(one SHA-256 of the source content, one of the published page with the shared header normalised
out — see the script's docstring for why the header needs stripping before hashing).

**Run it** in the same two moments `reconcile_facts.py` already governs: after any epic task lands
(§2 "A task moves" / "A decision gets decided" / "Scope changes mid-flight"), and again in the
"Before publishing, every time" checklist in section 3, right alongside `reconcile_facts.py` and
`lang_scan.py`.

```bash
python3 _generator/verify_publish_sync.py                # check
python3 _generator/verify_publish_sync.py --refresh       # after a REAL rebuild + republish
python3 _generator/verify_publish_sync.py --check-normalization   # prove the header-stripping still holds
```

Read the verdicts the way `reconcile_facts.py`'s are read — never treat anything but `OK` as safe
to ignore:

| Verdict | Means | Do |
|---|---|---|
| `OK` | Source and published page both match the last verified publish. | Nothing. |
| `DRIFT` | The named source changed since the manifest was last written, so the published page is stale (or the published page itself changed without its source moving — a hand-edit or a half-finished publish). | Rebuild per section 1, republish per 3b, then run `--refresh` once you have actually verified the two sides agree. |
| `MISSING` | A `TASK-*.md` has no published page at all. | Publish one, or if the task is intentionally unpublished say so in `STATUS.md`'s note — do not silence the check. |
| `ORPHANED` | A published page has no manifest entry, so nothing is protecting it. | Give it a source: a generator (§1) if it substantially renders `STATUS.md`, or a fact-check registration in `reconcile_facts.py`'s `GROUPS` if it is genuinely hand-authored narrative — see the `status-tarefas.html` / `progresso-refatoracao.html` entries there for both shapes. Then run `--refresh`. |
| `BLIND` | The script cannot tell — a required source file is absent from this checkout, the task-file set doesn't match what the manifest expects, or `unify_header.py` could not be imported to normalise the published page. | Fix the underlying gap (usually: sync the checkout) before trusting anything else this run reported for that page. **Never read `BLIND` as `OK`.** |

`--refresh` re-seeds the manifest from *current* content, so only run it once you have actually
rebuilt (section 1) and republished (3b) — refreshing over an undetected drift just launders it.

## 3c. Code references: file and symbol, never a line number

Production moved ~40 commits in the ten days after the first draft, and about sixty of the
seventy-five `file:line` anchors drifted by −14 to +78 while every fact they pointed at held. A
reader following a stale line lands on confidently wrong code, which is worse than no reference.
So a reference is `flux.service.ts` plus the method (`objectCaller()`), the constant
(`PREFETCH_SUPPORTED_NODE_TYPES`) or the literal to grep for (`responses.length === 10`). State the
SHA the spec was read against in `PLAN.md`'s header, and refresh it when facts are re-verified.
This applies to the content modules in `_generator/` as well — they mirror the spec by hand.

## 4. The one rule behind all of the above

**A check you have not seen fail is not a check.** Both gates in `_generator/` were vacuous when
first written, and both were caught only by planting the exact defect and watching them stay green.
Before you trust a new one, break the thing it guards.
