#!/usr/bin/env python3
"""Write each task page's state chip and status note from STATUS.md, without a rebuild.

A task's state and note live in STATUS.md.  A generated page shows them in its hero
(the state chip in the kicker and the note line under the goal), rendered by
tasklib.render().  When only the STATUS.md row changes, this script rewrites those two
spots in place, the same way tasklib renders them, so a page whose generator module
has drifted (see CLAUDE.md) does not have to be rebuilt to show a new state.

    python3 _generator/sync_status.py            # every timeline/task-*.html
    python3 _generator/sync_status.py A11 E4     # only these pages
    python3 _generator/sync_status.py --check    # report, write nothing; exit 1 on drift

It never touches anything else on the page.  Board cards, the timeline cards and the
progress bars are separate; `impact.py CODE` lists them and reconcile_facts.py checks
them.
"""
import glob
import io
import os
import re
import sys

GEN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GEN)
import status as _status  # noqa: E402
from tasklib import B, D, esc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(GEN))
TIMELINE = os.path.join(ROOT, 'timeline')

CHIP = re.compile(r'(<div class="kicker">.*?)<span class="st st-[a-z]+" data-en="[^"]*" data-pt="[^"]*">[^<]*</span>', re.S)
NOTE = re.compile(r'<div class="stnote" data-en="[^"]*" data-pt="[^"]*">.*?</div>', re.S)
GOAL = re.compile(r'<div class="goal" data-en="[^"]*" data-pt="[^"]*">.*?</div>', re.S)


def note_html(st):
    if not (st['note'] or st['ref']):
        return ''
    bits_en, bits_pt = [], []
    if st['ref']:
        bits_en.append('<b>%s</b>' % esc(st['ref']))
        bits_pt.append('<b>%s</b>' % esc(st['ref']))
    if st['note']:
        bits_en.append(esc(st['note']))
        bits_pt.append(esc(st.get('note_pt') or st['note']))
    return D((' · '.join(bits_en), ' · '.join(bits_pt)), cls='stnote')


def sync(text, code):
    st = _status.of(code)
    en, pt, cls = _status.LABELS[st['state']]
    chip = B((en, pt), cls='st ' + cls)
    new, n = CHIP.subn(lambda m: m.group(1) + chip, text, count=1)
    if not n:
        return text, 'no state chip in the kicker'
    want = note_html(st)
    if NOTE.search(new):
        new = NOTE.sub(lambda m: want, new, count=1)
    elif want:
        new, n = GOAL.subn(lambda m: m.group(0) + want, new, count=1)
        if not n:
            return text, 'no goal line to put the status note under'
    return new, None


def main(argv):
    check = '--check' in argv
    codes = [a.upper() for a in argv if not a.startswith('--')]
    paths = ([os.path.join(TIMELINE, 'task-%s.html' % c) for c in codes] if codes
             else sorted(glob.glob(os.path.join(TIMELINE, 'task-*.html'))))
    changed, bad = [], 0
    for p in paths:
        code = os.path.basename(p)[5:-5]
        if not os.path.exists(p):
            print('MISSING  %s' % os.path.relpath(p, ROOT))
            bad += 1
            continue
        text = io.open(p, encoding='utf-8').read()
        new, err = sync(text, code)
        if err:
            print('SKIPPED  %s: %s' % (os.path.relpath(p, ROOT), err))
            bad += 1
            continue
        if new != text:
            changed.append(os.path.relpath(p, ROOT))
            if not check:
                io.open(p, 'w', encoding='utf-8').write(new)
    verb = 'would change' if check else 'changed'
    for c in changed:
        print('%s  %s' % (verb, c))
    print('%d page(s) %s, %d skipped' % (len(changed), verb, bad))
    return 1 if (check and changed) or bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
