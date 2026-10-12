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

_ROW = re.compile(r'^\|\s*([A-Z]\d+[a-z]?)\s*\|\s*([a-z-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$', re.M)

def load():
    if not os.path.exists(_PATH):
        return {}
    out = {}
    for code, state, ref, note in _ROW.findall(open(_PATH, encoding='utf-8').read()):
        if state not in LABELS:
            raise ValueError('STATUS.md: unknown state %r for %s' % (state, code))
        if note and ' // ' not in note:
            raise ValueError(
                'STATUS.md: the note for %s has no Portuguese side. Write it as '
                '"English // Portugues" — the pages are bilingual and the note is rendered '
                'into them verbatim, so an untranslated note shows English in both languages.'
                % code)
        note_en, _, note_pt = note.partition(' // ')
        out[code] = {'state': state, 'ref': ref if ref not in ('—', '-', '') else None,
                     'note': note_en or None, 'note_pt': (note_pt or note_en) or None}
    return out

STATUS = load()
_LOWER = {k.lower(): v for k, v in STATUS.items()}

def of(code):
    # STATUS.md's row regex only accepts a lowercase letter suffix (e.g. `A1b`),
    # matching the convention every prose reference to that task uses. The
    # published-page code, derived from the TASK-*.md filename, follows the
    # filename's own all-caps convention instead (`TASK-A1B-...md` -> `A1B`).
    # Same task, two casings by convention — fall back to a case-insensitive
    # match rather than silently dropping the recorded state and note.
    if code in STATUS:
        return STATUS[code]
    return _LOWER.get(code.lower(), {'state': 'planned', 'ref': None, 'note': None, 'note_pt': None})

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
