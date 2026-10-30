#!/usr/bin/env python3
"""Rebuild the named task pages from the generator and publish only those.

    python3 _generator/rebuild.py A11 A14      # rebuild timeline/task-A11.html and task-A14.html

Every wave build runs (the build scripts write whole waves), into a temporary folder.
Only the named pages are copied to timeline/.  Each copied page then gets the shared
header (_assets/link_header_css.py and unify_header.py, run on that page only) and its
"Updated" stamp back (_assets/stamp_updates.py), so no other page is touched.

Some published pages carry content that their content module lacks, so a rebuild
would delete it.  Those codes are listed in DRIFTED and refused; port the missing
content into the module first, then remove the code from DRIFTED.  For a change to a
task's state, note or ref only, use sync_status.py: it needs no rebuild.
"""
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = Path(GEN).parent.parent
sys.path.insert(0, GEN)
sys.path.insert(0, str(ROOT / '_assets'))
BUILDS = ('build_w0.py', 'w1_build.py', 'w2_build.py', 'w3_build.py', 'w4_build.py', 'w5_build.py')

# Measured 2026-10-30 by rebuilding every page and diffing it with the published one.
# S1 and S7 carry hand edits to their wording (S1 rewritten in plain language, S7's PT text
# corrected and its card count updated) that the content modules do not have.
DRIFTED = {'S1', 'S7'}


def main(argv):
    force = '--force' in argv
    codes = [a.upper() for a in argv if not a.startswith('--')]
    if not codes:
        print(__doc__)
        return 2
    refused = sorted(set(codes) & DRIFTED)
    if refused and not force:
        print('Refused: %s. The published page has content its content module lacks, so a rebuild '
              'would delete it. Port that content into the module, remove the code from DRIFTED in '
              'rebuild.py, then rebuild. A state, note or ref change needs only sync_status.py.' % ', '.join(refused))
        return 1
    import tasklib
    tmp = tempfile.mkdtemp(prefix='epic-build-')
    tasklib.OUT = tmp + os.sep
    cwd = os.getcwd()
    os.chdir(GEN)
    devnull = open(os.devnull, 'w')
    try:
        for b in BUILDS:
            stdout, sys.stdout = sys.stdout, devnull
            try:
                runpy.run_path(os.path.join(GEN, b), run_name='__main__')
            finally:
                sys.stdout = stdout
    finally:
        os.chdir(cwd)
    import link_header_css
    import unify_header
    missing = []
    for c in codes:
        src = os.path.join(tmp, 'task-%s.html' % c)
        if not os.path.exists(src):
            missing.append(c)
            continue
        dst = ROOT / 'timeline' / ('task-%s.html' % c)
        shutil.copyfile(src, dst)
        link_header_css.rewrite(dst, prefix='../')
        unify_header.process(dst, prefix='../', active='timeline')
        print('rebuilt  %s' % dst.relative_to(ROOT))
    shutil.rmtree(tmp)
    import stamp_updates
    stamp_updates.main([])
    for c in missing:
        print('MISSING  task-%s.html: no build script writes it (a hand-written page; patch it by hand)' % c)
    sys.stdout.flush()
    subprocess.run(['git', 'diff', '--stat', '--'] + ['timeline/task-%s.html' % c for c in codes if c not in missing], cwd=ROOT)
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
