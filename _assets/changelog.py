#!/usr/bin/env python3
"""Keep CHANGELOG.md and the "What changed" page (mudancas.html) in step with git.

Each publish PR gets one entry in CHANGELOG.md, newest first.  The entry is built from
git: the files that changed since the base, the task codes they belong to (a task page,
a spec file, or a STATUS.md row whose state, ref or note changed) and the commit
subjects.  `add` writes the entry, then renders mudancas.html and stamps the task pages
(see stamp_updates.py).

    # a publish PR, after the pages are regenerated (the working tree counts)
    python3 _assets/changelog.py add --pr 43 --base origin/main \\
        --title "Show A11 shipped" --title-pt "Mostra a A11 entregue"

    # a PR that changes a task's spec or generator but on purpose not its page
    python3 _assets/changelog.py add ... --no-page-change "A7: wording in the spec only"

    # an entry for a PR that is already in history
    python3 _assets/changelog.py add --pr 40 --range 108ae52..3798074 --title ... --title-pt ...

    python3 _assets/changelog.py render     # rewrite mudancas.html from CHANGELOG.md
    python3 _assets/changelog.py check      # exit 1 when mudancas.html is out of date

Re-running `add` for the same PR number replaces its entry, so it is safe to run again
after a review fix.
"""
from __future__ import annotations

import argparse
import datetime
import html
import io
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / 'CHANGELOG.md'
PAGE = ROOT / 'mudancas.html'
REPO_URL = 'https://github.com/yagoovela/execution-agents'
EPIC = 'worker-flow-execution-epic'
sys.path.insert(0, str(ROOT / EPIC / '_generator'))
sys.path.insert(0, str(ROOT / '_assets'))

INTRO = """# Changelog

Every publish to this repository, newest first. `_assets/changelog.py add` writes each
entry from git; do not edit the generated lines by hand. The page `mudancas.html`
renders this file, and each task page shows the latest entry that changed it.

The log starts with PR #40. Earlier history is in `git log`.
"""

HEAD_RE = re.compile(r'^## (\d{4}-\d{2}-\d{2}) · \[#(\d+)\]\([^)]*\) · (.+)$')
FIELD_RE = re.compile(r'^- ([A-Za-z ()]+): (.*)$')


def git(*args: str) -> str:
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def parse(text: str | None = None) -> list[dict]:
    if text is None:
        text = LOG.read_text(encoding='utf-8') if LOG.exists() else INTRO
    entries, cur = [], None
    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            cur = {'date': m.group(1), 'pr': int(m.group(2)), 'title': m.group(3),
                   'title_pt': m.group(3), 'tasks': [], 'pages': [], 'commits': [], 'no_page_change': []}
            entries.append(cur)
            continue
        if cur is None:
            continue
        m = FIELD_RE.match(line)
        if m:
            key, val = m.group(1).lower(), m.group(2).strip()
            if key == 'title (pt)':
                cur['title_pt'] = val
            elif key in ('tasks', 'pages'):
                cur[key] = [v.strip().strip('`') for v in val.split(',') if v.strip()]
            elif key == 'no page change':
                cur['no_page_change'].append(val)
        elif line.startswith('  - ') and cur is not None:
            cur['commits'].append(line[4:].strip())
    return entries


def fmt(e: dict) -> str:
    out = ['## %s · [#%d](%s/pull/%d) · %s' % (e['date'], e['pr'], REPO_URL, e['pr'], e['title'])]
    out.append('- Title (PT): %s' % e['title_pt'])
    out.append('- Tasks: %s' % (', '.join(e['tasks']) or 'none'))
    out.append('- Pages: %s' % (', '.join('`%s`' % p for p in e['pages']) or 'none'))
    for n in e['no_page_change']:
        out.append('- No page change: %s' % n)
    if e['commits']:
        out.append('- Commits:')
        out.extend('  - %s' % c for c in e['commits'])
    return '\n'.join(out)


def write(entries: list[dict]) -> None:
    body = INTRO + '\n' + '\n\n'.join(fmt(e) for e in entries) + '\n'
    LOG.write_text(body, encoding='utf-8')


def changed_tasks(base: str, head: str | None, files: list[str]) -> list[str]:
    import impact
    codes = set()
    for f in files:
        b = os.path.basename(f)
        m = re.match(r'task-([A-Z0-9]+)\.html$', b) if f.startswith('timeline/') else None
        if m:
            codes.add(m.group(1))
        m = re.match(r'TASK-([A-Z]\d+[A-Za-z]?\d*)-', b) if f.startswith(EPIC + '/') else None
        if m:
            codes.add(impact.canon(m.group(1)))

    def rows(rev: str | None) -> dict:
        try:
            text = git('show', '%s:%s/STATUS.md' % (rev, EPIC)) if rev else (ROOT / EPIC / 'STATUS.md').read_text(encoding='utf-8')
        except subprocess.CalledProcessError:
            return {}
        out = {}
        for line in text.splitlines():
            m = re.match(r'^\|\s*([A-Z]\d+[a-z]?(?:\.\d+)?)\s*\|\s*([a-z-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$', line)
            if m:
                out[impact.canon(m.group(1))] = (m.group(1), m.group(2), m.group(3), m.group(4))
        return out

    old, new = rows(base), rows(head)
    for code in set(old) | set(new):
        if old.get(code) != new.get(code):
            codes.add(code)
    order = getattr(__import__('order'), 'ORDER', [])
    return sorted(codes, key=lambda c: (order.index(c) if c in order else 999, c))


def stamp_only(f: str, base: str, head: str | None) -> bool:
    """True when a task page differs from base only in its "Updated" stamp."""
    if not f.startswith('timeline/task-'):
        return False
    from stamp_updates import STAMP_RE
    try:
        old = git('show', '%s:%s' % (base, f))
        new = git('show', '%s:%s' % (head, f)) if head else (ROOT / f).read_text(encoding='utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return STAMP_RE.sub('', old) == STAMP_RE.sub('', new)


def cmd_add(a: argparse.Namespace) -> int:
    if a.range:
        base, head = a.range.split('..')
        files = git('diff', '--name-only', base, head).split()
        commits = git('log', '--no-merges', '--reverse', '--format=%h %s', '%s..%s' % (base, head)).splitlines()
        date = git('log', '-1', '--format=%cs', head).strip()
    else:
        base, head = a.base, None
        files = sorted(set(git('diff', '--name-only', base).split())
                       | set(git('ls-files', '--others', '--exclude-standard').split()))
        commits = git('log', '--no-merges', '--reverse', '--format=%h %s', '%s..HEAD' % base).splitlines()
        date = a.date or datetime.date.today().isoformat()
    skip = {'CHANGELOG.md', PAGE.name}
    files = [f for f in files if f not in skip and not stamp_only(f, base, head)]
    pages = sorted(f for f in files if f.endswith('.html'))
    entry = {'date': date, 'pr': a.pr, 'title': a.title, 'title_pt': a.title_pt,
             'tasks': changed_tasks(base, head, files), 'pages': pages,
             'commits': commits, 'no_page_change': a.no_page_change or []}
    entries = [e for e in parse() if e['pr'] != a.pr]
    entries.append(entry)
    entries.sort(key=lambda e: (e['date'], e['pr']), reverse=True)
    write(entries)
    print('CHANGELOG.md: #%d, %d task(s), %d page(s), %d commit(s)' % (a.pr, len(entry['tasks']), len(pages), len(commits)))
    render()
    import stamp_updates
    stamp_updates.main([])
    return 0


def B(en: str, pt: str, tag: str = 'span', cls: str = '', extra: str = '') -> str:
    c = ' class="%s"' % cls if cls else ''
    return '<%s%s%s data-en="%s" data-pt="%s">%s</%s>' % (
        tag, c, extra, html.escape(en, quote=True), html.escape(pt, quote=True), en, tag)


def pt_date(d: str) -> str:
    y, m, dd = d.split('-')
    return '%s/%s/%s' % (dd, m, y)


CSS = """
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #F1F5F9; color: #0F172A; margin: 0; padding: 32px 24px 80px; line-height: 1.5; }
  .container { max-width: 1100px; margin: 0 auto; }
  .hero { background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: #fff;
          border-radius: 16px; padding: 32px 36px; margin-bottom: 28px; }
  .hero h1 { margin: 0 0 8px; font-size: 30px; letter-spacing: -0.5px; }
  .hero p { margin: 0; color: #CBD5E1; max-width: 760px; line-height: 1.7; font-size: 15px; }
  .entry { background: #fff; border: 1px solid #E2E8F0; border-radius: 12px;
           padding: 20px 24px; margin-bottom: 16px; }
  .entry h2 { margin: 0 0 4px; font-size: 18px; line-height: 1.4; }
  .entry .meta { font-size: 12.5px; color: #64748B; margin-bottom: 12px; }
  .entry .meta a { color: #334155; font-weight: 600; }
  .entry dl { margin: 0; display: grid; grid-template-columns: 110px 1fr; gap: 6px 14px; font-size: 13.5px; }
  .entry dt { color: #64748B; font-weight: 600; }
  .entry dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
  .entry .code { display: inline-block; background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 6px;
                 padding: 1px 7px; margin: 0 4px 4px 0; font-weight: 700; font-size: 12px; color: #0F172A;
                 text-decoration: none; }
  .entry ul { margin: 0; padding-left: 18px; }
  .entry code { font-size: 12px; }
  @media (max-width: 640px) { .entry dl { grid-template-columns: 1fr; } }
"""


def render_html(entries: list[dict]) -> str:
    out = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="UTF-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<title>Flux — What changed</title>',
           '<link rel="stylesheet" href="_assets/i18n.css">',
           '<link rel="stylesheet" href="_assets/header.css">',
           '<style>%s</style>' % CSS, '</head>', '<body>', '<div class="container">',
           '<div class="hero">',
           B('What changed', 'O que mudou', tag='h1'),
           B('Every publish to these pages, newest first, with the tasks and pages it changed. '
             'Generated from <code>CHANGELOG.md</code> by <code>_assets/changelog.py</code>.',
             'Cada publicação nestas páginas, da mais nova para a mais antiga, com as tasks e as páginas que '
             'ela mudou. Gerada a partir do <code>CHANGELOG.md</code> pelo <code>_assets/changelog.py</code>.', tag='p'),
           '</div>']
    for e in entries:
        url = '%s/pull/%d' % (REPO_URL, e['pr'])
        out.append('<section class="entry" id="pr-%d">' % e['pr'])
        out.append(B(html.escape(e['title']), html.escape(e['title_pt']), tag='h2'))
        out.append('<div class="meta"><span data-en="%s" data-pt="%s">%s</span> · <a href="%s">PR #%d</a></div>'
                   % (e['date'], pt_date(e['date']), e['date'], url, e['pr']))
        out.append('<dl>')
        tasks = ''.join('<a class="code" href="timeline/task-%s.html">%s</a>' % (c, c)
                        if (ROOT / 'timeline' / ('task-%s.html' % c)).exists() else '<span class="code">%s</span>' % c
                        for c in e['tasks']) or '—'
        out.append(B('Tasks', 'Tasks', tag='dt') + '<dd>%s</dd>' % tasks)
        pages = ', '.join('<a href="%s"><code>%s</code></a>' % (p, p) for p in e['pages']) or '—'
        out.append(B('Pages', 'Páginas', tag='dt') + '<dd>%s</dd>' % pages)
        if e['no_page_change']:
            items = ''.join('<li>%s</li>' % html.escape(n) for n in e['no_page_change'])
            out.append(B('No page change', 'Sem mudança de página', tag='dt') + '<dd><ul>%s</ul></dd>' % items)
        if e['commits']:
            items = ''.join('<li><code>%s</code> %s</li>' % (html.escape(c.split(' ', 1)[0]),
                                                            html.escape(c.split(' ', 1)[1] if ' ' in c else ''))
                            for c in e['commits'])
            out.append(B('Commits', 'Commits', tag='dt') + '<dd><ul>%s</ul></dd>' % items)
        out.append('</dl>')
        out.append('</section>')
    out += ['</div>', '<script src="_assets/i18n.js"></script>', '</body>', '</html>', '']
    return '\n'.join(out)


def rendered() -> str:
    import link_header_css
    import unify_header
    text = render_html(parse())
    text = unify_header.insert_doc_nav(text, unify_header.build_doc_nav(prefix='', active='changes'))
    assert link_header_css.HEADER_LINK_RE.search(text)
    return text


def render() -> None:
    PAGE.write_text(rendered(), encoding='utf-8')
    print('%s: %d entries' % (PAGE.name, len(parse())))


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('--pr', type=int, required=True)
    a.add_argument('--title', required=True)
    a.add_argument('--title-pt', required=True)
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument('--base', help='compare the working tree with this ref')
    g.add_argument('--range', help='BASE..HEAD of a PR already in history')
    a.add_argument('--date', help='entry date for --base (default: today)')
    a.add_argument('--no-page-change', action='append', metavar='"CODE: reason"')
    sub.add_parser('render')
    sub.add_parser('check')
    args = p.parse_args(argv)
    if args.cmd == 'add':
        return cmd_add(args)
    if args.cmd == 'render':
        render()
        return 0
    current = PAGE.read_text(encoding='utf-8') if PAGE.exists() else ''
    if re.sub(r'\s+', ' ', current) != re.sub(r'\s+', ' ', rendered()):
        print('mudancas.html is out of date with CHANGELOG.md: run python3 _assets/changelog.py render')
        return 1
    print('mudancas.html matches CHANGELOG.md (%d entries)' % len(parse()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
