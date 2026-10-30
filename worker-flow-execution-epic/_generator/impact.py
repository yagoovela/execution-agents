# -*- coding: utf-8 -*-
"""Which files render which fact of a task.  Derived by scanning, never hand-kept.

When a task changes, every page that restates one of its facts has to change with it.
Nothing links those pages to each other, so a fact fixed in one place stays stale in
the others.  This script answers "task X changed — which files must change?" by
reading the sources (the spec mirror, STATUS.md, the generator) and scanning every
published page.  A new page is picked up the moment it mentions the task.

    python3 _generator/impact.py A11          # files and facts for one task
    python3 _generator/impact.py --all        # the whole map
    python3 _generator/impact.py A11 --json   # machine-readable

Facts:
    title     the task's title (spec H1, page H1, nav labels, cards)
    state     planned / doing / shipped ... (STATUS.md; chips, badges, wave counts)
    note      the STATUS.md note shown under the page title
    links     the STATUS.md ref: ClickUp id, PR, branch
    wave      which wave ships it (order.py; wave sections, wave chips)
    order     delivery order: the prev/next links of neighbouring task pages
    deps      the "Depends on" line (spec; the page's glance card)
    estimate  the wave estimate shown next to the wave the task belongs to
    content   the spec body (spec mirror, content module, task page)
    owner     who owns the task (owners.py, synced from ClickUp; the board's owner line)
    mention   any other page or document that names the task in its text

Kinds:
    source     edit this (spec mirror, STATUS.md, generator inputs)
    generated  rebuild this (written by the _generator build scripts)
    hand       patch this by hand (no generator writes it)

A state, note or ref change on a task page can be written without a rebuild:
_generator/sync_status.py CODE.  CHANGELOG.md, mudancas.html and the "Updated" stamp
on task pages are left out of this map: _assets/changelog.py add writes them.
"""
import collections
import glob
import html
import io
import json
import os
import re
import runpy
import sys

GEN = os.path.dirname(os.path.abspath(__file__))
EPIC = os.path.dirname(GEN)
ROOT = os.path.dirname(EPIC)
sys.path.insert(0, GEN)

FACTS = ('title', 'state', 'note', 'links', 'wave', 'order', 'deps', 'estimate', 'content', 'owner', 'mention')
BUILDS = ('build_w0.py', 'w1_build.py', 'w2_build.py', 'w3_build.py', 'w4_build.py', 'w5_build.py')
TOOLS = ('impact.py', 'reconcile_facts.py', 'lang_scan.py', 'sync_status.py', 'rebuild.py', 'sync_owners.py', 'owners.py')
SUBSPEC = re.compile(r'-(PLAN|DESIGN|QA-HANDOFF|CURRENT-PROCESS)\.md$')


def canon(code):
    return code.replace('.', '').upper()


def rel(p):
    return os.path.relpath(p, ROOT)


def read(p):
    return io.open(p, encoding='utf-8').read() if os.path.exists(p) else ''


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html.unescape(s))).strip()


# --------------------------------------------------------------------------- sources
def status_rows():
    out = {}
    for line in read(os.path.join(EPIC, 'STATUS.md')).splitlines():
        m = re.match(r'^\|\s*([A-Z]\d+[a-z]?(?:\.\d+)?)\s*\|\s*([a-z-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$', line)
        if m:
            out[canon(m.group(1))] = {'code': m.group(1), 'state': m.group(2), 'ref': m.group(3), 'note': m.group(4)}
    return out


def spec_files():
    """code -> [spec md paths]; the first is the task spec, the rest are its sub-specs."""
    out = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(EPIC, 'TASK-*.md'))):
        parts = os.path.basename(p).split('-')
        code = canon(parts[1])
        if len(parts) > 2 and parts[2][:1].isdigit():
            code = canon(parts[1] + parts[2])
        out[code].append(p)
    for code in out:
        out[code].sort(key=lambda p: (bool(SUBSPEC.search(p)), p))
    return dict(out)


def spec_title_text(text):
    first = text.splitlines()[0] if text else ''
    return re.sub(r'^#\s*[A-Za-z0-9.]+\s*[—-]\s*', '', first).strip()


def spec_title(path):
    return spec_title_text(read(path))


def gen_tables():
    import importlib
    order = importlib.import_module('order')
    titles = importlib.import_module('TITLES_ALL')
    return order, titles


_TRACE = None


def build_trace():
    """code -> {'build': script, 'modules': [content module files]}, by running the builds
    with tasklib.write replaced, so nothing is written and nothing is guessed from names."""
    global _TRACE
    if _TRACE is not None:
        return _TRACE
    import tasklib
    seen = {}
    real_write = tasklib.write
    current = {'script': None}

    def fake_write(T):
        seen[canon(T['code'])] = (current['script'], T)
        return T['code']

    tasklib.write = fake_write
    old_out, old_argv = sys.stdout, sys.argv
    try:
        for b in BUILDS:
            current['script'] = b
            sys.stdout = io.StringIO()
            sys.argv = [b]
            runpy.run_path(os.path.join(GEN, b), run_name='__main__')
    finally:
        tasklib.write = real_write
        sys.stdout, sys.argv = old_out, old_argv
    gen_files = {os.path.abspath(p) for p in glob.glob(os.path.join(GEN, '*.py'))}
    out = {}
    for code, (script, T) in seen.items():
        probes = [T.get('lede'), T.get('goal'), T.get('done'), T.get('title')]
        mods = set()
        for mod in list(sys.modules.values()):
            f = os.path.abspath(getattr(mod, '__file__', '') or '')
            if f not in gen_files or f.endswith(('tasklib.py', 'order.py', 'TITLES_ALL.py', 'status.py', 'impact.py')):
                continue
            for v in vars(mod).values():
                vals = list(v.values()) if isinstance(v, dict) else [v]
                if any(any(x is pr for pr in probes if pr is not None) for x in vals):
                    mods.add(f)
                    break
        out[code] = {'build': os.path.join(GEN, script), 'modules': sorted(mods)}
    _TRACE = out
    return out


# --------------------------------------------------------------------------- scan
def pages():
    out = []
    for pat in ('*.html', 'timeline/*.html', 'complemento/*.html', 'passos/*.html', 'worker-flow-execution-epic/*.html'):
        out.extend(p for p in sorted(glob.glob(os.path.join(ROOT, pat))) if os.path.basename(p) != 'mudancas.html')
    return out


def wave_section(text, wave):
    """Slice of a hand page that belongs to one wave, found by its header, or ''."""
    heads = []
    for m in re.finditer(r'id="w(\d)"|=+ WAVE (\d) =+|<span class="num">Wave (\d)</span>', text):
        w = int(next(g for g in m.groups() if g))
        if not heads or heads[-1][1] != w:
            heads.append((m.start(), w))
    for i, (pos, w) in enumerate(heads):
        if w == wave:
            end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
            return text[pos:end]
    return ''


def visible_text(text):
    """data-en strings plus text nodes, tags removed: what a reader sees in EN."""
    parts = [html.unescape(m) for m in re.findall(r'data-en="(.*?)"', text, re.S)]
    body = re.sub(r'<(script|style)\b.*?</\1>', ' ', text, flags=re.S)
    parts.append(body)
    return strip_tags(' '.join(parts))


def code_re(code, status_code=None):
    alts = {code}
    if status_code:
        alts.add(status_code)
    if code.endswith('B') and len(code) > 2:
        alts.add(code[:-1] + 'b')
    return re.compile(r'(?<![\w-])(?:%s)(?![\w-])' % '|'.join(re.escape(a) for a in sorted(alts, key=len, reverse=True)))


def impact(code, _cache={}):
    code = canon(code)
    if 'ctx' not in _cache:
        order, titles = gen_tables()
        _cache['ctx'] = (status_rows(), spec_files(), order, titles, build_trace(),
                         {p: read(p) for p in pages()},
                         {},
                         {p: read(p) for p in sorted(glob.glob(os.path.join(EPIC, '*.md')))})
    st, specs, order, titles, trace, page_text, vis, md_text = _cache['ctx']

    def seen(p, t):
        if p not in vis:
            vis[p] = visible_text(t)
        return vis[p]
    row = st.get(code)
    wave = order.WAVE.get(code)
    out = collections.defaultdict(lambda: {'kind': None, 'facts': set(), 'how': set()})

    def add(path, kind, facts, how):
        e = out[rel(path)]
        e['kind'] = e['kind'] or kind
        e['facts'].update(facts)
        e['how'].add(how)

    # sources
    for i, p in enumerate(specs.get(code, [])):
        add(p, 'source', {'title', 'content', 'deps'} if i == 0 else {'content'}, 'spec' if i == 0 else 'sub-spec')
    if row:
        add(os.path.join(EPIC, 'STATUS.md'), 'source', {'state', 'note', 'links'}, 'STATUS.md row %s' % row['code'])
    if code in titles.TITLES:
        add(os.path.join(GEN, 'TITLES_ALL.py'), 'source', {'title'}, 'nav title')
    import owners as _owners
    owner_keys = [k for k in _owners.OWNERS if k.split(' ')[0] == code]
    if owner_keys:
        add(os.path.join(GEN, 'owners.py'), 'source', {'owner'}, 'owner (ClickUp)')
    if code in order.ORDER or wave is not None:
        add(os.path.join(GEN, 'order.py'), 'source', {'wave', 'order'}, 'ORDER/WAVE')
    tr = trace.get(code)
    if tr:
        add(tr['build'], 'source', {'content'}, 'build script')
        for m in tr['modules']:
            add(m, 'source', {'title', 'content', 'deps'}, 'content module')

    title_texts = set()
    if code in titles.TITLES:
        title_texts.add(strip_tags(titles.TITLES[code][0]))
    own = os.path.join(ROOT, 'timeline', 'task-%s.html' % code)
    m = re.search(r'<h1 data-en="(.*?)"', page_text.get(own, ''), re.S)
    if m:
        title_texts.add(strip_tags(m.group(1)))
    title_texts.discard('')
    clickup = re.findall(r'868[a-z0-9]{6}', row['ref']) if row else []
    cre = code_re(code, row['code'] if row else None)

    for p, t in page_text.items():
        if not t:
            continue
        pm = re.search(r'timeline/task-([A-Z0-9]+)\.html$', p.replace(os.sep, '/'))
        kind = 'generated' if (pm and pm.group(1) in trace) else 'hand'
        facts, hows = set(), []
        if p == own:
            facts |= {'title', 'state', 'note', 'links', 'wave', 'deps', 'content'}
            hows.append('task page')
        link = re.compile(r'href="(?:\.\./|timeline/)?task-%s\.html[#"]' % re.escape(code))
        if link.search(t):
            if '/timeline/task-' in p.replace(os.sep, '/') and p != own:
                if re.search(r'class="page-footer-nav">.*?task-%s\.html' % re.escape(code), t, re.S):
                    facts.add('order')
                    hows.append('prev/next link')
            for lm in link.finditer(t):
                near = t[lm.start():lm.start() + 700]
                if re.search(r'class="st st-', near[:400]):
                    facts.add('state')
                    hows.append('state chip on a card')
                card = re.match(r'href="[^"]*"[^>]*>(?:(?!</a>).)*?<span class="t"', near, re.S)
                if card or any(tt and tt in strip_tags(near) for tt in title_texts):
                    facts.add('title')
                if re.search(r'class="wv w\d', near[:300]):
                    facts.add('wave')
                    hows.append('wave chip')
        if re.search(r'<div class="task-id">%s(?:<|\s)' % re.escape(row['code'] if row else code), t) or \
                re.search(r'<div class="task-id">%s(?:<|\s)' % re.escape(code), t):
            facts |= {'title', 'state', 'wave'}
            if 'class="task-owner"' in t and owner_keys:
                facts.add('owner')
            hows.append('board card' + (' and overall counts' if 'summary-counts' in t else ''))
        if wave is not None:
            sec = wave_section(t, wave)
            if sec and (cre.search(visible_text(sec)) or link.search(sec)):
                facts.add('wave')
                if re.search(r'tl-estimate|title="Engineering estimate|est\.', sec):
                    facts.add('estimate')
                    hows.append('wave %d estimate' % wave)
            if re.search(r'class="ew-row"><span data-en="Wave %d\b' % wave, t):
                facts.add('state')
                hows.append('wave %d progress bar' % wave)
        if any(cu in t for cu in clickup):
            facts.add('links')
            hows.append('ClickUp id')
        if p != own and cre.search(seen(p, t)):
            facts.add('mention')
            hows.append('names %s in the text' % code)
        if facts:
            add(p, kind, facts, ', '.join(hows) or 'mentions')

    for p in sorted(glob.glob(os.path.join(GEN, '*.py'))):
        if rel(p) in out or p.endswith(TOOLS):
            continue
        if cre.search(read(p)):
            add(p, 'source', {'mention'}, 'names %s' % code)
    for p, t in md_text.items():
        if rel(p) in out:
            continue
        if cre.search(t):
            add(p, 'source', {'mention'}, 'names %s' % code)
    return {k: {'kind': v['kind'], 'facts': sorted(v['facts']), 'how': sorted(v['how'] - {''})} for k, v in sorted(out.items())}


def all_codes():
    order, titles = gen_tables()
    codes = set(status_rows()) | set(spec_files()) | set(order.ORDER) | set(titles.TITLES)
    codes |= {canon(os.path.basename(p)[5:-5]) for p in glob.glob(os.path.join(ROOT, 'timeline', 'task-*.html'))}
    return sorted(codes)


def show(code, data):
    order, titles = gen_tables()
    t = titles.TITLES.get(code, ('',))[0]
    print('%s — %s' % (code, strip_tags(t) or '(no title in TITLES_ALL)'))
    for kind in ('source', 'generated', 'hand'):
        rows = [(f, d) for f, d in data.items() if d['kind'] == kind]
        if not rows:
            continue
        print('  %s' % {'source': 'edit (source)', 'generated': 'rebuild (generated)', 'hand': 'patch by hand'}[kind])
        for f, d in rows:
            print('    %-58s %s' % (f, ', '.join(d['facts'])))
    print()


def main(argv):
    as_json = '--json' in argv
    args = [a for a in argv if not a.startswith('--')]
    codes = all_codes() if '--all' in argv else [canon(a) for a in args]
    if not codes:
        print(__doc__)
        return 2
    result = {c: impact(c) for c in codes}
    if as_json:
        print(json.dumps(result, indent=1, ensure_ascii=False))
    else:
        for c in codes:
            show(c, result[c])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
