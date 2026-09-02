# -*- coding: utf-8 -*-
"""Cross-check facts that the epic's documents state in more than one place.

A number restated in several specs drifts the moment reality changes, and no review
catches it because each document reads as internally consistent.  This script is the
mechanical comparison that review cannot do.  Run it after any release that changes a
count, and before publishing the doc set.

    python3 _generator/reconcile_facts.py

Exit code 1 when any group disagrees, so it can gate a publish.
"""
import io, os, re, sys, glob, collections

EPIC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each group: a fact that several documents state independently.
# `pattern` captures the value; every capture in the group must agree.
GROUPS = [
    ('isTemporalNode dispatch count', [
        (r'`isTemporalNode\(type\)`[^|]*\|[^|]*\|\s*(\d+)\s*types', 'TASK-A1-DISPATCH-REGISTRY.md'),
        (r"isTemporalNode`?(?:'s|’s)\s+(\w+)", 'TASK-A3-STRANDED-MODULES.md'),
        (r'isTemporalNode\s*→\s*(\d+)\s*types', 'complemento/transversais.html'),
    ]),
    ('prefetch whitelist size', [
        (r'(\d+)[- ]type whitelist', '*.md'),
        (r'whitelist[^.]{0,40}?(\d+)\s*types', '*.md'),
    ]),
    ('node type census', [
        (r'all (\d+) registered types', '*.md'),
        (r'across all (\d+) components', '../worker-node-migration-analysis/README.md'),
        (r'census — (\d+) node types', '../worker-node-migration-analysis/README.md'),
        (r'census of (\d+)', '../worker-node-migration-analysis/README.md'),
    ]),
    ('live cron count', [
        (r'`@Cron` is registered (\w+) times', '*.md'),
        (r'(\w+) crons with no leader election', 'PLAN.md'),
        (r'Leader election for the (\w+) crons', 'DELIVERY-PLAN.md'),
        (r'Part 1 — the (\w+) crons', 'TASK-S8-SCHEDULER-AND-BUS.md'),
    ]),]

WORDNUM = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,
           'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,
           'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18}

def norm(v):
    v = v.strip().lower()
    return WORDNUM.get(v, v)

def read(rel):
    p = os.path.join(EPIC, rel)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None

def expand(spec):
    if '*' in spec:
        return [os.path.relpath(p, EPIC) for p in sorted(glob.glob(os.path.join(EPIC, spec)))]
    return [spec]

failures = 0
for name, rules in GROUPS:
    found = collections.defaultdict(list)
    for pattern, spec in rules:
        for rel in expand(spec):
            body = read(rel)
            if body is None:
                continue
            for m in re.finditer(pattern, body, re.I):
                v = norm(m.group(1))
                if isinstance(v, str) and not v.isdigit():
                    continue
                found[int(v)].append(rel)
    if not found:
        failures += 1
        print('BLIND %-32s no statement matched — the pattern sees nothing, so it can never fail' % name)
        continue
    if len(found) == 1:
        v, where = next(iter(found.items()))
        print('OK    %-32s %s  (%d place%s)' % (name, v, len(where), '' if len(where) == 1 else 's'))
    else:
        failures += 1
        print('DRIFT %-32s documents disagree:' % name)
        for v, where in sorted(found.items()):
            for w in sorted(set(where)):
                print('        %-4s <- %s' % (v, w))


# --- decision coverage -------------------------------------------------------
# PLAN.md §7 is the single source for what a decision says; DELIVERY-PLAN.md's wave
# map is the single source for which wave it gates.  Splitting them that way only
# works if every decision appears in both, so this is the check that keeps the split
# honest: a decision added to one and forgotten in the other is a failure here.
plan = read('PLAN.md') or ''
sec7 = plan.split('## 7.')[-1].split('## 8.')[0]
in_plan = set(re.findall(r'^\|\s*(D\d+)\s*\|', sec7, re.M))
wavemap = (read('DELIVERY-PLAN.md') or '').split('Decisions that gate a wave')[-1]
in_waves = collections.Counter(re.findall(r'\bD\d+\b', '\n'.join(re.findall(r'^\|\s*Wave \d\s*\|.*$', wavemap, re.M))))
missing_wave = sorted(in_plan - set(in_waves), key=lambda d: int(d[1:]))
missing_plan = sorted(set(in_waves) - in_plan, key=lambda d: int(d[1:]))
dupes = sorted([d for d, n in in_waves.items() if n > 1], key=lambda d: int(d[1:]))
if not in_plan:
    failures += 1
    print('BLIND %-32s PLAN.md section 7 matched no decision row' % 'decision coverage')
elif missing_wave or missing_plan or dupes:
    failures += 1
    print('DRIFT %-32s decision tables disagree:' % 'decision coverage')
    for d in missing_wave:
        print('        %-4s <- in PLAN.md section 7, absent from the wave map' % d)
    for d in missing_plan:
        print('        %-4s <- in the wave map, absent from PLAN.md section 7' % d)
    for d in dupes:
        print('        %-4s <- listed under %d waves' % (d, in_waves[d]))
else:
    print('OK    %-32s %d decisions, each in one wave' % ('decision coverage', len(in_plan)))


# --- decision wave placement ---------------------------------------------------
# DELIVERY-PLAN.md lists each decision under one wave.  The rule is that a decision
# sits under the earliest wave containing a task it blocks — PLAN.md section 7's
# Blocks column, mapped through order.WAVE.  The table was hand-written once and
# four rows had drifted from the rule by 2026-09-02; this recomputes it every run.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from order import WAVE as _WAVE
except Exception:
    _WAVE = None
_PART_WAVE = {('S7', '1'): 0, ('S7', '3'): 0, ('S7', '2'): 1,
              ('S8', '1'): 1, ('S8', '2'): 1, ('S8', '3'): 1, ('S8', '4'): 1}

def earliest_wave(blocks):
    waves = []
    for code, part in re.findall(r'\b([A-ES]\d)\b(?:\s+part\s+(\d))?', blocks):
        if part and (code, part) in _PART_WAVE:
            waves.append(_PART_WAVE[(code, part)])
        elif _WAVE and code in _WAVE:
            waves.append(_WAVE[code])
    return min(waves) if waves else None

plan7 = (read('PLAN.md') or '').split('## 7.')[-1].split('## 8.')[0]
expected = {}
for d, blocks in re.findall(r'^\|\s*(D\d+)\s*\|[^|]*\|([^|]*)\|', plan7, re.M):
    w = earliest_wave(blocks)
    if w is not None:
        expected[d] = w
listed = {}
for w, ds in re.findall(r'^\|\s*Wave (\d)\s*\|([^|]*)\|', wavemap, re.M):
    for d in re.findall(r'\bD\d+\b', ds):
        listed[d] = int(w)
wrong = sorted([(d, expected[d], listed[d]) for d in expected
                if d in listed and expected[d] != listed[d]], key=lambda t: int(t[0][1:]))
if _WAVE is None or not expected or not listed:
    failures += 1
    print('BLIND %-32s could not compute waves from PLAN.md section 7 and order.py' % 'decision wave placement')
elif wrong:
    failures += 1
    print('DRIFT %-32s the wave map disagrees with PLAN.md section 7 Blocks:' % 'decision wave placement')
    for d, e, l in wrong:
        print('        %-4s <- listed under Wave %d, earliest blocked task is in Wave %d' % (d, l, e))
else:
    print('OK    %-32s %d decisions sit under the earliest wave they block' % ('decision wave placement', len(expected)))

# --- task page freshness ------------------------------------------------------
# TASK-<code>.md is the spec; timeline/task-<code>.html is written by hand from it,
# through a content module, so nothing makes them agree.  Editing the spec and
# forgetting the module is silent, and it happened during the 2026-08-31 review.
# The tightest signal with almost no false positives: a decision the spec cites must
# be visible on the page.  The page may cite more; it may never cite less.
# The published copy puts timeline/ beside the spec folder rather than inside it,
# so resolve both layouts.  A gate that fails on a valid layout is a false refusal,
# and a false refusal is worse than the drift it was meant to catch.
TIMELINE = next((d for d in (os.path.join(EPIC, 'timeline'),
                             os.path.join(os.path.dirname(EPIC), 'timeline'))
                 if os.path.isdir(d)), None)
stale = []
for md in sorted(glob.glob(os.path.join(EPIC, 'TASK-*.md'))):
    code = os.path.basename(md).split('-')[1]
    page = os.path.join(TIMELINE, 'task-%s.html' % code) if TIMELINE else None
    if not page or not os.path.exists(page):
        stale.append((code, 'no published page'))
        continue
    in_md = set(re.findall(r'\bD(\d+)\b', io.open(md, encoding='utf-8').read()))
    in_pg = set(re.findall(r'\bD(\d+)\b', io.open(page, encoding='utf-8').read()))
    missing = sorted(in_md - in_pg, key=int)
    if missing:
        stale.append((code, 'spec cites ' + ', '.join('D' + m for m in missing) + ' — page does not'))
if not glob.glob(os.path.join(EPIC, 'TASK-*.md')):
    failures += 1
    print('BLIND %-32s no TASK-*.md matched' % 'task page freshness')
elif TIMELINE is None:
    failures += 1
    print('BLIND %-32s no timeline/ directory beside or inside the spec folder'
          % 'task page freshness')
elif stale:
    failures += 1
    print('DRIFT %-32s the page is behind its spec:' % 'task page freshness')
    for code, why in stale:
        print('        %-4s <- %s' % (code, why))
else:
    print('OK    %-32s %d pages cite every decision their spec does'
          % ('task page freshness', len(glob.glob(os.path.join(EPIC, 'TASK-*.md')))))

print()
if failures:
    print('%d fact group(s) disagree. Fix the documents, or the pattern if it is over-matching.' % failures)
    sys.exit(1)
print('All cross-stated facts agree.')
