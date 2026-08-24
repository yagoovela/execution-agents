# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Wave 3 build — renders task-A4/A5/A6/S6/A8/A9/D1.html via the shared tasklib."""
import sys
sys.path.insert(0, _GEN)

import tasklib, order
from TITLES_ALL import TITLES

import w3_a4, w3_a5, w3_a6, w3_s6, w3_a8, w3_a9, w3_d1

MODULES = [w3_a4, w3_a5, w3_a6, w3_s6, w3_a8, w3_a9, w3_d1]

if __name__ == '__main__':
    for m in MODULES:
        T = dict(m.TASK)
        T.update(order.nav(T['code'], TITLES))
        print(tasklib.write(T))
