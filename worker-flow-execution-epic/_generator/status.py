# -*- coding: utf-8 -*-
"""Reads STATUS.md — the single source of each task's state.

Nothing else records progress. If you find a state written anywhere else, that copy
is a bug: delete it and read from here instead.
"""
import os, re

_EPIC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_EPIC, 'STATUS.md')

# state -> (EN label, PT label, css class)
LABELS = {
    'planned': ('Planned',     'Planejada',   'st-planned'),
    'blocked': ('Blocked',     'Bloqueada',   'st-blocked'),
    'doing':   ('In progress', 'Em andamento','st-doing'),
    'review':  ('In review',   'Em revisão',  'st-review'),
    'shipped': ('Shipped',     'Entregue',    'st-shipped'),
    'dropped': ('Dropped',     'Descartada',  'st-dropped'),
}

_ROW = re.compile(r'^\|\s*([A-Z]\d)\s*\|\s*([a-z-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$', re.M)

def load():
    if not os.path.exists(_PATH):
        return {}
    out = {}
    for code, state, ref, note in _ROW.findall(open(_PATH, encoding='utf-8').read()):
        if state not in LABELS:
            raise ValueError('STATUS.md: unknown state %r for %s' % (state, code))
        out[code] = {'state': state, 'ref': ref if ref not in ('—', '-', '') else None,
                     'note': note or None}
    return out

STATUS = load()

def of(code):
    return STATUS.get(code, {'state': 'planned', 'ref': None, 'note': None})

if __name__ == '__main__':
    from collections import Counter
    c = Counter(v['state'] for v in STATUS.values())
    print('%d tasks' % len(STATUS))
    for k in LABELS:
        if c[k]:
            print('  %-12s %d' % (k, c[k]))
    missing = [x for x in ('S7','S1','C2') if x not in STATUS]
    if missing:
        print('MISSING from STATUS.md:', missing)
