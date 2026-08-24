# -*- coding: utf-8 -*-
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasklib, order
from TITLES_ALL import TITLES
import w2_a1, w2_d2, w2_a2, w2_a3

for mod in (w2_a1, w2_d2, w2_a2, w2_a3):
    T = dict(mod.TASK)
    T.update(order.nav(T['code'], TITLES))
    print(tasklib.write(T))
