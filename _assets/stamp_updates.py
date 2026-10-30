#!/usr/bin/env python3
"""Stamp each task page with the latest CHANGELOG.md entry that changed it.

The stamp is one line at the end of the page's hero: "Updated 2026-10-29 · PR #42 ·
What changed", linking the PR and its entry on mudancas.html.  A page that no entry
lists gets no stamp.  Run it after a rebuild, because the generator does not write it.

    python3 _assets/stamp_updates.py           # write the stamps
    python3 _assets/stamp_updates.py --check   # report, write nothing; exit 1 on drift

changelog.py add runs it for you.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '_assets'))
from changelog import REPO_URL, parse, pt_date  # noqa: E402

STAMP_RE = re.compile(r'<div class="upd-stamp" data-en="[^"]*" data-pt="[^"]*">.*?</div>', re.S)
ANCHOR = '<div class="hero-links">'


def stamp_html(e: dict) -> str:
    pr = '<a href="%s/pull/%d">PR #%d</a>' % (REPO_URL, e['pr'], e['pr'])
    en = 'Updated %s · %s · <a href="../mudancas.html#pr-%d">what changed</a>' % (e['date'], pr, e['pr'])
    pt = 'Atualizada em %s · %s · <a href="../mudancas.html#pr-%d">o que mudou</a>' % (pt_date(e['date']), pr, e['pr'])
    return '<div class="upd-stamp" data-en="%s" data-pt="%s">%s</div>' % (
        html.escape(en, quote=True), html.escape(pt, quote=True), en)


def latest_by_page(entries: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for e in entries:
        for p in e['pages']:
            out.setdefault(p, e)
    return out


def apply(text: str, want: str) -> str | None:
    if STAMP_RE.search(text):
        return STAMP_RE.sub(lambda m: want, text, count=1)
    if not want:
        return text
    if ANCHOR not in text:
        return None
    return text.replace(ANCHOR, want + ANCHOR, 1)


def main(argv: list[str]) -> int:
    check = '--check' in argv
    latest = latest_by_page(parse())
    changed, bad = [], []
    for p in sorted((ROOT / 'timeline').glob('task-*.html')):
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding='utf-8')
        e = latest.get(rel)
        new = apply(text, stamp_html(e) if e else '')
        if new is None:
            bad.append(rel)
            continue
        if new != text:
            changed.append((rel, e['pr'] if e else None))
            if not check:
                p.write_text(new, encoding='utf-8')
    for rel, pr in changed:
        print('%s %s -> %s' % ('stale' if check else 'stamped', rel, 'PR #%d' % pr if pr else 'no stamp'))
    for rel in bad:
        print('SKIPPED %s: no hero-links line to put the stamp before' % rel)
    if check:
        print('%d task page(s) carry a stale or missing update stamp' % len(changed))
    else:
        print('%d task page(s) stamped' % len(changed))
    return 1 if bad or (check and changed) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
