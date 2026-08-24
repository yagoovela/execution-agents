# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

import sys
sys.path.insert(0, _GEN)
import tasklib, order
from TITLES_ALL import TITLES
import w5_b5, w5_a7, w5_b6, w5_b7, w6_c1, w6_c2


def build(code, mod, vnum, glance_note=None, decisions=None, sec1=None, sec3=None):
    blocks = []
    blocks.append({'k': 'label', 'n': '1', 't': sec1})
    if getattr(mod, 'TABLE', None):
        blocks.append({'k': 'table', **mod.TABLE})
    n = 2
    if decisions:
        blocks.append({'k': 'label', 'n': str(n),
                       't': ('The decisions this task needs', 'As decisões que esta task precisa')})
        blocks.append({'k': 'prose', 't': mod.PROSE})
        blocks.extend(decisions)
        n += 1
    blocks.append({'k': 'label', 'n': str(n), 't': sec3})
    for p in mod.PARTS:
        blocks.append({'k': 'part', **p})

    T = {
        'code': code,
        'vnum': vnum,
        'title': mod.TITLE,
        'goal': mod.GOAL,
        'glance': mod.GLANCE,
        'lede': mod.LEDE,
        'blocks': blocks,
        'verif': mod.VERIF,
        'done': mod.DONE,
        'files': mod.FILES,
    }
    T.update(order.nav(code, TITLES))
    return tasklib.write(T)


SPECS = [
 ('B5', w5_b5, '4', w5_b5.DECISIONS if hasattr(w5_b5, 'DECISIONS') else None,
  ('Why the gate is the correctness condition', 'Por que o gate é a condição de corretude'),
  ('What the task does, in four parts', 'O que a task faz, em quatro partes')),
 ('A7', w5_a7, '4', [w5_a7.DEC_ORDERING],
  ('The five mutating nodes, and where each one goes', 'Os cinco nodes mutantes, e para onde cada um vai'),
  ('What the task does, in three parts', 'O que a task faz, em três partes')),
 ('B6', w5_b6, '4', w5_b6.DECISIONS,
  ('Why these four are not activities', 'Por que estes quatro não são activities'),
  ('What the task does, in three parts', 'O que a task faz, em três partes')),
 ('B7', w5_b7, '4', [w5_b7.DEC_RESUME],
  ('Three consequences a workflow fixes for free', 'Três consequências que um workflow corrige de graça'),
  ('What the task does, in three parts', 'O que a task faz, em três partes')),
 ('C1', w6_c1, '3', None,
  ('What gets deleted, and who owns each deletion', 'O que é apagado, e de quem é cada deleção'),
  ('What the task does, in three parts', 'O que a task faz, em três partes')),
 ('C2', w6_c2, '4', w6_c2.DECISIONS,
  ('The three pieces, and what each removal buys', 'As três peças, e o que cada remoção traz'),
  ('What the task does, in three parts', 'O que a task faz, em três partes')),
]

W5_B5_DECISIONS = w5_b5.DECISIONS

if __name__ == '__main__':
    for code, mod, vnum, decs, sec1, sec3 in SPECS:
        print(build(code, mod, vnum, decisions=decs, sec1=sec1, sec3=sec3))
