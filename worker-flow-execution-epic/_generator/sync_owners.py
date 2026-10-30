#!/usr/bin/env python3
"""Write the owner line of every task board card from owners.py.

    python3 _generator/sync_owners.py           # write status-tarefas.html
    python3 _generator/sync_owners.py --check   # report, write nothing; exit 1 on drift
"""
import html
import io
import os
import re
import sys

GEN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GEN)
import owners  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(GEN))
BOARD = os.path.join(ROOT, 'status-tarefas.html')
CARD = re.compile(r'(<div class="task-id">([A-Z]\d+[A-Za-z]?\d*)(?:<span class="task-part"><span data-en="([^"]*)"[^<]*</span></span>)?</div>'
                  r'(?:(?!<div class="task-id">).)*?<div class="task-owner">)([^<]*)(</div>)', re.S)


def key(code, part):
    k = code.upper() + (' ' + html.unescape(part) if part else '')
    return k


def cards(text):
    return [(key(m.group(2), m.group(3)), m.group(4)) for m in CARD.finditer(text)]


def main(argv):
    check = '--check' in argv
    text = io.open(BOARD, encoding='utf-8').read()
    changed, missing = [], []

    def rep(m):
        k = key(m.group(2), m.group(3))
        if k not in owners.OWNERS:
            missing.append(k)
            return m.group(0)
        want = owners.label(k)
        if m.group(4) != want:
            changed.append((k, m.group(4), want))
        return m.group(1) + want + m.group(5)

    new = CARD.sub(rep, text)
    for k, old, want in changed:
        print('%s %-14s %s -> %s' % ('stale' if check else 'owner', k, old, want))
    for k in missing:
        print('MISSING %s: no entry in owners.py' % k)
    if not check and new != text:
        io.open(BOARD, 'w', encoding='utf-8').write(new)
    print('%d owner line(s) %s, %d card(s) without an owners.py entry'
          % (len(changed), 'stale' if check else 'written', len(missing)))
    return 1 if missing or (check and changed) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
