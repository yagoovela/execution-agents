# -*- coding: utf-8 -*-
"""Cross-check facts that the epic's documents state in more than one place.

A number restated in several specs drifts the moment reality changes, and no review
catches it because each document reads as internally consistent.  This script is the
mechanical comparison that review cannot do.  Run it after any release that changes a
count, and before publishing the doc set.

    python3 _generator/reconcile_facts.py

Exit code 1 when any group disagrees, so it can gate a publish.
"""
import os, re, sys, glob, collections

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

print()
if failures:
    print('%d fact group(s) disagree. Fix the documents, or the pattern if it is over-matching.' % failures)
    sys.exit(1)
print('All cross-stated facts agree.')
