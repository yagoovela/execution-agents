# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

import sys
sys.path.insert(0, _GEN)
import tasklib, order
from TITLES_ALL import TITLES
import w4_b1b2, w4_b3b4, w4_e1e2

DEC_LABEL = ('The decisions this task needs', 'As decisões que esta task precisa')

TASKS = [
 ('B1', w4_b1b2.B1, [w4_b1b2.B1_DEC]),
 ('B2', w4_b1b2.B2, [w4_b1b2.B2_DEC]),
 ('B3', w4_b3b4.B3, [w4_b3b4.B3_DEC]),
 ('B4', w4_b3b4.B4, [w4_b3b4.B4_DEC]),
 ('E1', w4_e1e2.E1, []),
 ('E2', w4_e1e2.E2, [w4_e1e2.E2_DEC]),
]

def build(code, t, decs):
    blocks = [{'k': 'label', 'n': '1', 't': t['L1']}]
    for tb in t.get('TABLES', []):
        blocks.append({'k': 'table', **tb})
    if t.get('PROSE1'):
        blocks.append({'k': 'prose', 't': t['PROSE1']})
    n = 2
    if decs:
        blocks.append({'k': 'label', 'n': '2', 't': DEC_LABEL})
        if t.get('DECINTRO'):
            blocks.append({'k': 'prose', 't': t['DECINTRO']})
        blocks.extend(decs)
        n = 3
    blocks.append({'k': 'label', 'n': str(n), 't': t['LPARTS']})
    for p in t['PARTS']:
        blocks.append({'k': 'part', **p})
    TASK = {
        'code': code,
        'vnum': str(n + 1),
        'title': t['TITLE'],
        'goal': t['GOAL'],
        'glance': t['GLANCE'],
        'lede': t['LEDE'],
        'blocks': blocks,
        'verif': t['VERIF'],
        'done': t['DONE'],
        'files': t['FILES'],
    }
    TASK.update(order.nav(code, TITLES))
    return tasklib.write(TASK)

if __name__ == '__main__':
    for code, t, decs in TASKS:
        print(build(code, t, decs))
