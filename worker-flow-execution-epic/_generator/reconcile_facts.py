# -*- coding: utf-8 -*-
"""Cross-check facts that the epic's documents state in more than one place.

A number restated in several specs drifts the moment reality changes, and no review
catches it because each document reads as internally consistent.  This script is the
mechanical comparison that review cannot do.  Run it after any release that changes a
count, and before publishing the doc set.

    python3 _generator/reconcile_facts.py
    python3 _generator/reconcile_facts.py --since origin/main   # also check what changed since a ref

Exit code 1 when any group disagrees, so it can gate a publish.

The task groups at the end compare every published page with its source, per task:
the task registry (page, spec, title entry, delivery order), titles, states and
status notes.  `--since REF` adds the diff check: for every task whose source changed
since REF, each file `impact.py` maps to that change must have changed too.
"""
import io, os, re, sys, glob, collections

EPIC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each group: a fact that several documents state independently.
# `pattern` captures the value; every capture in the group must agree.
GROUPS = [
    ('isTemporalNode dispatch count', [
        (r'`isTemporalNode\(type\)`[^|]*\|[^|]*\|\s*(\d+)\s*types', 'TASK-A1-DISPATCH-REGISTRY.md'),
        (r"isTemporalNode`?(?:'s|’s)\s+(\w+)", 'TASK-A3-STRANDED-MODULES.md'),
        (r'isTemporalNode\s*→\s*(\d+)\s*types', 'complemento/transversais.html'),
    ]),
    ('prefetch whitelist size', [
        (r'(\d+)[- ]type whitelist', '*.md'),
        (r'whitelist[^.]{0,40}?(\d+)\s*types', '*.md'),
    ]),
    ('node type census', [
        (r'all (\d+) registered types', '*.md'),
        (r'across all (\d+) components', '../worker-node-migration-analysis/README.md'),
        (r'census — (\d+) node types', '../worker-node-migration-analysis/README.md'),
        (r'census of (\d+)', '../worker-node-migration-analysis/README.md'),
    ]),
    ('live cron count', [
        (r'`@Cron` is registered (\w+) times', '*.md'),
        (r'(\w+) crons with no leader election', 'PLAN.md'),
        (r'Leader election for the (\w+) crons', 'DELIVERY-PLAN.md'),
        (r'Part 1 — the (\w+) crons', 'TASK-S8-SCHEDULER-AND-BUS.md'),
    ]),]

WORDNUM = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,
           'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,
           'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18}

def norm(v):
    v = v.strip().lower()
    return WORDNUM.get(v, v)

def read(rel):
    p = os.path.join(EPIC, rel)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else None

def expand(spec):
    if '*' in spec:
        return [os.path.relpath(p, EPIC) for p in sorted(glob.glob(os.path.join(EPIC, spec)))]
    return [spec]

failures = 0
for name, rules in GROUPS:
    found = collections.defaultdict(list)
    for pattern, spec in rules:
        for rel in expand(spec):
            body = read(rel)
            if body is None:
                continue
            for m in re.finditer(pattern, body, re.I):
                v = norm(m.group(1))
                if isinstance(v, str) and not v.isdigit():
                    continue
                found[int(v)].append(rel)
    if not found:
        failures += 1
        print('BLIND %-32s no statement matched — the pattern sees nothing, so it can never fail' % name)
        continue
    if len(found) == 1:
        v, where = next(iter(found.items()))
        print('OK    %-32s %s  (%d place%s)' % (name, v, len(where), '' if len(where) == 1 else 's'))
    else:
        failures += 1
        print('DRIFT %-32s documents disagree:' % name)
        for v, where in sorted(found.items()):
            for w in sorted(set(where)):
                print('        %-4s <- %s' % (v, w))


# --- decision coverage -------------------------------------------------------
# PLAN.md §7 is the single source for what a decision says; DELIVERY-PLAN.md's wave
# map is the single source for which wave it gates.  Splitting them that way only
# works if every decision appears in both, so this is the check that keeps the split
# honest: a decision added to one and forgotten in the other is a failure here.
plan = read('PLAN.md') or ''
sec7 = plan.split('## 7.')[-1].split('## 8.')[0]
in_plan = set(re.findall(r'^\|\s*(D\d+)\s*\|', sec7, re.M))
wavemap = (read('DELIVERY-PLAN.md') or '').split('Decisions that gate a wave')[-1]
in_waves = collections.Counter(re.findall(r'\bD\d+\b', '\n'.join(re.findall(r'^\|\s*Wave \d\s*\|.*$', wavemap, re.M))))
missing_wave = sorted(in_plan - set(in_waves), key=lambda d: int(d[1:]))
missing_plan = sorted(set(in_waves) - in_plan, key=lambda d: int(d[1:]))
dupes = sorted([d for d, n in in_waves.items() if n > 1], key=lambda d: int(d[1:]))
if not in_plan:
    failures += 1
    print('BLIND %-32s PLAN.md section 7 matched no decision row' % 'decision coverage')
elif missing_wave or missing_plan or dupes:
    failures += 1
    print('DRIFT %-32s decision tables disagree:' % 'decision coverage')
    for d in missing_wave:
        print('        %-4s <- in PLAN.md section 7, absent from the wave map' % d)
    for d in missing_plan:
        print('        %-4s <- in the wave map, absent from PLAN.md section 7' % d)
    for d in dupes:
        print('        %-4s <- listed under %d waves' % (d, in_waves[d]))
else:
    print('OK    %-32s %d decisions, each in one wave' % ('decision coverage', len(in_plan)))


# --- decision wave placement ---------------------------------------------------
# DELIVERY-PLAN.md lists each decision under one wave.  The rule is that a decision
# sits under the earliest wave containing a task it blocks — PLAN.md section 7's
# Blocks column, mapped through order.WAVE.  The table was hand-written once and
# four rows had drifted from the rule by 2026-09-02; this recomputes it every run.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from order import WAVE as _WAVE
except Exception:
    _WAVE = None
_PART_WAVE = {('S7', '1'): 0, ('S7', '3'): 0, ('S7', '2'): 1,
              ('S8', '1'): 1, ('S8', '2'): 1, ('S8', '3'): 1, ('S8', '4'): 1}

def earliest_wave(blocks):
    waves = []
    for code, part in re.findall(r'\b([A-ES]\d)\b(?:\s+part\s+(\d))?', blocks):
        if part and (code, part) in _PART_WAVE:
            waves.append(_PART_WAVE[(code, part)])
        elif _WAVE and code in _WAVE:
            waves.append(_WAVE[code])
    return min(waves) if waves else None

plan7 = (read('PLAN.md') or '').split('## 7.')[-1].split('## 8.')[0]
expected = {}
for d, blocks in re.findall(r'^\|\s*(D\d+)\s*\|[^|]*\|([^|]*)\|', plan7, re.M):
    w = earliest_wave(blocks)
    if w is not None:
        expected[d] = w
listed = {}
for w, ds in re.findall(r'^\|\s*Wave (\d)\s*\|([^|]*)\|', wavemap, re.M):
    for d in re.findall(r'\bD\d+\b', ds):
        listed[d] = int(w)
wrong = sorted([(d, expected[d], listed[d]) for d in expected
                if d in listed and expected[d] != listed[d]], key=lambda t: int(t[0][1:]))
if _WAVE is None or not expected or not listed:
    failures += 1
    print('BLIND %-32s could not compute waves from PLAN.md section 7 and order.py' % 'decision wave placement')
elif wrong:
    failures += 1
    print('DRIFT %-32s the wave map disagrees with PLAN.md section 7 Blocks:' % 'decision wave placement')
    for d, e, l in wrong:
        print('        %-4s <- listed under Wave %d, earliest blocked task is in Wave %d' % (d, l, e))
else:
    print('OK    %-32s %d decisions sit under the earliest wave they block' % ('decision wave placement', len(expected)))

# --- task page freshness ------------------------------------------------------
# TASK-<code>.md is the spec; timeline/task-<code>.html is written by hand from it,
# through a content module, so nothing makes them agree.  Editing the spec and
# forgetting the module is silent, and it happened during the 2026-08-31 review.
# The tightest signal with almost no false positives: a decision the spec cites must
# be visible on the page.  The page may cite more; it may never cite less.
# The published copy puts timeline/ beside the spec folder rather than inside it,
# so resolve both layouts.  A gate that fails on a valid layout is a false refusal,
# and a false refusal is worse than the drift it was meant to catch.
TIMELINE = next((d for d in (os.path.join(EPIC, 'timeline'),
                             os.path.join(os.path.dirname(EPIC), 'timeline'))
                 if os.path.isdir(d)), None)
stale = []
for md in sorted(glob.glob(os.path.join(EPIC, 'TASK-*.md'))):
    code = os.path.basename(md).split('-')[1]
    try:
        from TITLES_ALL import NO_PAGE as _NO_PAGE
    except Exception:
        _NO_PAGE = {}
    code = _NO_PAGE.get(code.upper(), code)
    page = os.path.join(TIMELINE, 'task-%s.html' % code) if TIMELINE else None
    if not page or not os.path.exists(page):
        stale.append((code, 'no published page'))
        continue
    in_md = set(re.findall(r'\bD(\d+)\b', io.open(md, encoding='utf-8').read()))
    in_pg = set(re.findall(r'\bD(\d+)\b', io.open(page, encoding='utf-8').read()))
    missing = sorted(in_md - in_pg, key=int)
    if missing:
        stale.append((code, 'spec cites ' + ', '.join('D' + m for m in missing) + ' — page does not'))
if not glob.glob(os.path.join(EPIC, 'TASK-*.md')):
    failures += 1
    print('BLIND %-32s no TASK-*.md matched' % 'task page freshness')
elif TIMELINE is None:
    failures += 1
    print('BLIND %-32s no timeline/ directory beside or inside the spec folder'
          % 'task page freshness')
elif stale:
    failures += 1
    print('DRIFT %-32s the page is behind its spec:' % 'task page freshness')
    for code, why in stale:
        print('        %-4s <- %s' % (code, why))
else:
    print('OK    %-32s %d pages cite every decision their spec does'
          % ('task page freshness', len(glob.glob(os.path.join(EPIC, 'TASK-*.md')))))


# --- task registry, titles, states, notes ------------------------------------
# Every fact about a task is written once in a source (the spec mirror, STATUS.md,
# TITLES_ALL.py, order.py) and restated on several pages.  These groups compare
# every restatement with its source.  impact.py lists where each fact is restated.
import html as _html
try:
    import impact as _impact
    import status as _st
    import TITLES_ALL as _T
    import order as _order
except Exception as _e:
    _impact = None
    failures += 1
    print('BLIND %-32s could not import the generator tables: %s' % ('task registry', _e))

if _impact is not None:
    ROOT = _impact.ROOT
    _rows = _impact.status_rows()
    _specs = _impact.spec_files()
    _NO_PAGE = getattr(_T, 'NO_PAGE', {})
    _NO_SPEC = getattr(_T, 'NO_SPEC', {})
    _SHORT = getattr(_T, 'SHORT_TITLES', {})
    _pages = {os.path.basename(p)[5:-5]: p for p in glob.glob(os.path.join(ROOT, 'timeline', 'task-*.html'))}

    def _txt(p):
        return io.open(p, encoding='utf-8').read() if os.path.exists(p) else ''

    def _norm_title(t):
        t = _impact.strip_tags(t).replace('`', '')
        return re.sub(r'[\s.]+$', '', t).lower()

    def _group(name, problems, ok_msg):
        global failures
        problems = list(dict.fromkeys(problems))
        if problems:
            failures += 1
            print('DRIFT %-32s %d problem%s:' % (name, len(problems), '' if len(problems) == 1 else 's'))
            for p in problems:
                print('        ' + p)
        else:
            print('OK    %-32s %s' % (name, ok_msg))

    # registry: page, spec, title entry, delivery order
    probs = []
    for code, row in sorted(_rows.items()):
        if code in _NO_PAGE:
            parent = _pages.get(_NO_PAGE[code])
            if not parent:
                probs.append('%-5s <- NO_PAGE points at task-%s.html, which does not exist' % (code, _NO_PAGE[code]))
            elif '.' not in row['code'] and not re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(row['code']), _txt(parent), re.I):
                probs.append('%-5s <- NO_PAGE says task-%s.html covers it, but that page never names %s' % (code, _NO_PAGE[code], row['code']))
            continue
        if code not in _pages:
            probs.append('%-5s <- has a STATUS.md row but no timeline/task-%s.html' % (code, code))
        if code not in _T.TITLES:
            probs.append('%-5s <- missing from TITLES_ALL.py' % code)
        if code not in _order.ORDER:
            probs.append('%-5s <- missing from order.py ORDER (prev/next links skip it)' % code)
        if code not in _specs and code not in _NO_SPEC:
            probs.append('%-5s <- no TASK-%s-*.md in the spec mirror; copy it, or list it in TITLES_ALL.NO_SPEC' % (code, code))
    for code in sorted(_pages):
        if code not in _rows:
            probs.append('%-5s <- timeline/task-%s.html has no STATUS.md row' % (code, code))
    for code in sorted(_specs):
        if code not in _rows:
            probs.append('%-5s <- %s has no STATUS.md row' % (code, os.path.basename(_specs[code][0])))
    _group('task registry', probs, '%d tasks: page, spec, title entry and order all present' % len(_rows))

    # titles: page H1 = spec title (or its listed short title); nav labels = TITLES_ALL
    probs = []
    for code, p in sorted(_pages.items()):
        t = _txt(p)
        m = re.search(r'<h1 data-en="(.*?)" data-pt="(.*?)"', t, re.S)
        if not m:
            probs.append('%-5s <- task-%s.html has no bilingual <h1>' % (code, code))
            continue
        h1_en, h1_pt = _impact.strip_tags(m.group(1)), _impact.strip_tags(m.group(2))
        if code in _specs:
            spec_t = _impact.spec_title(_specs[code][0])
            if _norm_title(h1_en) != _norm_title(spec_t):
                if code not in _SHORT:
                    probs.append('%-5s <- page title %r differs from the spec title %r; fix the page, or list it in TITLES_ALL.SHORT_TITLES' % (code, h1_en, spec_t))
                elif _norm_title(_SHORT[code]) != _norm_title(spec_t):
                    probs.append('%-5s <- the spec title changed to %r; SHORT_TITLES still says %r — review the short title' % (code, spec_t, _SHORT[code]))
            elif code in _SHORT:
                probs.append('%-5s <- page title now equals the spec title; drop its SHORT_TITLES entry' % code)
        nav = _T.TITLES.get(code)
        if nav:
            ne, np_ = _impact.strip_tags(nav[0]), _impact.strip_tags(nav[1])
            if not _norm_title(h1_en).startswith(_norm_title(ne)) or not _norm_title(h1_pt).startswith(_norm_title(np_)):
                probs.append('%-5s <- TITLES_ALL %r / %r is not the page title %r / %r or its start' % (code, ne, np_, h1_en, h1_pt))
            for q, qt in _pages.items():
                for lm in re.finditer(r'href="task-%s\.html"><span data-en="(?:← |Next: )%s — (.*?)(?: →)?" data-pt="(?:← |Próxima: )%s — (.*?)(?: →)?"'
                                      % (re.escape(code), re.escape(code), re.escape(code)), _txt(qt)):
                    le, lp = _impact.strip_tags(lm.group(1)), _impact.strip_tags(lm.group(2))
                    if (le, lp) != (ne, np_):
                        probs.append('%-5s <- task-%s.html links to it as %r / %r; TITLES_ALL says %r / %r — rebuild or patch that page' % (code, q, le, lp, ne, np_))
    _group('task titles', probs, '%d pages: titles match the spec, nav labels match TITLES_ALL' % len(_pages))

    # states: task page chip, timeline card, board card, board counts, progress bars
    _BUCKET = {'shipped': 'done', 'doing': 'doing', 'review': 'doing', 'planned': 'planned', 'blocked': 'planned', 'dropped': 'planned'}
    probs = []
    for code, p in sorted(_pages.items()):
        row = _rows.get(code)
        if not row:
            continue
        want = _st.LABELS[row['state']]
        m = re.search(r'<div class="kicker">.*?<span class="st (st-[a-z]+)" data-en="([^"]+)"', _txt(p), re.S)
        if not m:
            probs.append('%-5s <- task-%s.html shows no state chip' % (code, code))
        elif (m.group(1), m.group(2)) != (want[2], want[0]):
            probs.append('%-5s <- task-%s.html shows %s; STATUS.md says %s' % (code, code, m.group(2), row['state']))
    for hub in glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, '*', 'index.html')):
        t = _txt(hub)
        for code, cls, lbl in re.findall(r'<a class="tl-card" href="task-([A-Z0-9]+)\.html"><span class="c">[^<]*</span><span class="st (st-[a-z]+)" data-en="([^"]+)"', t):
            row = _rows.get(code)
            if row and (cls, lbl) != (_st.LABELS[row['state']][2], _st.LABELS[row['state']][0]):
                probs.append('%-5s <- %s card shows %s; STATUS.md says %s' % (code, os.path.relpath(hub, ROOT), lbl, row['state']))
        cards = re.findall(r'<div class="task (\w+)">\s*<div class="task-status-icon">[^<]*</div>\s*<div class="task-body">\s*<div class="task-id">([A-Z]\d+[A-Za-z]?\d*)'
                           r'(?:<span class="task-part">.*?</span></span>)?</div>.*?<span class="task-badge (\w+)">', t, re.S)
        if not cards:
            continue
        for wrap, code, badge in cards:
            row = _rows.get(_impact.canon(code))
            if wrap != badge:
                probs.append('%-5s <- %s card is styled %s but its badge says %s' % (code, os.path.relpath(hub, ROOT), wrap, badge))
            if row and _BUCKET[row['state']] != badge:
                probs.append('%-5s <- %s card says %s; STATUS.md says %s' % (code, os.path.relpath(hub, ROOT), badge, row['state']))
        cnt = collections.Counter(b for _, _, b in cards)
        sm = re.search(r'summary-counts">\s*<strong>(\d+)</strong>.*?<strong>(\d+)</strong>.*?<strong>(\d+)</strong>.*?<strong>(\d+)</strong>', t, re.S)
        if sm:
            got = tuple(int(x) for x in sm.groups())
            want_c = (cnt['done'], cnt['doing'], cnt['planned'], len(cards))
            if got != want_c:
                probs.append('total <- %s overall counts say %s done/doing/planned/total; its cards add up to %s' % (os.path.relpath(hub, ROOT), got, want_c))
        board_waves = {}
        for wm in re.finditer(r'<!-- =+ WAVE (\d) =+ -->(.*?)(?=<!-- =+ WAVE|\Z)', t, re.S):
            wcards = re.findall(r'<div class="task (\w+)">\s*<div class="task-status-icon">[^<]*</div>\s*<div class="task-body">\s*<div class="task-id">([A-Z]\d+[A-Za-z]?\d*)(<span class="task-part">)?.*?<span class="task-badge (\w+)">', wm.group(2), re.S)
            wc = collections.Counter(b for _, _, _, b in wcards)
            home = {c for _, c, _, _ in wcards if _order.WAVE.get(_impact.canon(c), int(wm.group(1))) == int(wm.group(1))}
            board_waves[int(wm.group(1))] = collections.Counter(
                'done' if _rows.get(_impact.canon(c), {}).get('state') == 'shipped' else 'open' for c in home)
            chips = {k: int(v) for k, v in re.findall(r'<span class="chip (done|doing|planned)">(\d+) ', wm.group(2))}
            if chips and chips != {k: v for k, v in wc.items() if v}:
                probs.append('wave%s <- %s wave chips say %s; its cards add up to %s' % (wm.group(1), os.path.relpath(hub, ROOT), chips, dict(wc)))
        if board_waves:
            _impact_board = board_waves
    _boardw = globals().get('_impact_board', {})
    prog = os.path.join(ROOT, 'progresso-refatoracao.html')
    for w, d, n in re.findall(r'<div class="ew-row"><span data-en="Wave (\d) [^"]*"[^>]*>.*?<span class="ew-num">(\d+)/(\d+)</span>', _txt(prog), re.S):
        wc = _boardw.get(int(w))
        if wc is not None and (int(d), int(n)) != (wc['done'], sum(wc.values())):
            probs.append('wave%s <- progresso-refatoracao.html says %s/%s; the board has %d of %d tasks shipped (a task counts in its order.py wave only)' % (w, d, n, wc['done'], sum(wc.values())))
    _group('task states', probs, 'every page, card, count and bar agrees with STATUS.md')

    # status notes: the line under each task title renders the STATUS.md ref and note
    probs = []
    for code, p in sorted(_pages.items()):
        row = _rows.get(code)
        if not row:
            continue
        info = _st.of(code)
        bits_en, bits_pt = [], []
        if info['ref']:
            bits_en.append('<b>%s</b>' % _html.escape(info['ref'], quote=True))
            bits_pt.append('<b>%s</b>' % _html.escape(info['ref'], quote=True))
        if info['note']:
            bits_en.append(_html.escape(info['note'], quote=True))
            bits_pt.append(_html.escape(info['note_pt'] or info['note'], quote=True))
        m = re.search(r'<div class="stnote" data-en="(.*?)" data-pt="(.*?)">', _txt(p), re.S)
        if not bits_en:
            if m:
                probs.append('%-5s <- task-%s.html shows a status note; STATUS.md has none' % (code, code))
            continue
        if not m:
            probs.append('%-5s <- task-%s.html shows no status note; STATUS.md has one' % (code, code))
        elif (_html.unescape(m.group(1)), _html.unescape(m.group(2))) != (' · '.join(bits_en), ' · '.join(bits_pt)):
            probs.append('%-5s <- task-%s.html status note differs from STATUS.md — rebuild or patch it' % (code, code))
    _group('task status notes', probs, 'every page shows its STATUS.md note and ref')

    # changelog: mudancas.html renders CHANGELOG.md; each task page carries its latest entry
    import subprocess
    probs = []
    for script, args in (('changelog.py', ['check']), ('stamp_updates.py', ['--check'])):
        r = subprocess.run([sys.executable, os.path.join(ROOT, '_assets', script)] + args, cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            probs.extend('_assets/%s: %s' % (script, l) for l in r.stdout.splitlines() if l.strip())
    _group('changelog and update stamps', probs, 'mudancas.html and every task page stamp match CHANGELOG.md')

    # diff mode
    if '--since' in sys.argv:
        import subprocess
        ref = sys.argv[sys.argv.index('--since') + 1]

        def _git(*a):
            return subprocess.run(['git'] + list(a), cwd=ROOT, capture_output=True, text=True).stdout

        changed = set(_git('diff', '--name-only', ref).split()) | set(_git('ls-files', '--others', '--exclude-standard').split())
        epic_rel = os.path.relpath(EPIC, ROOT)
        need = collections.defaultdict(set)
        for f in changed:
            b = os.path.basename(f)
            if f.startswith(epic_rel + '/TASK-'):
                need[_impact.canon(b.split('-')[1])].add('content')
                old_spec = _git('show', '%s:%s' % (ref, f))
                new_spec = _txt(os.path.join(ROOT, f))
                if old_spec and _impact.spec_title_text(old_spec) != _impact.spec_title_text(new_spec) and not re.search(r'-(PLAN|DESIGN|QA-HANDOFF|CURRENT-PROCESS)\.md$', f):
                    need[_impact.canon(b.split('-')[1])].add('title')
        old_rows = {}
        for line in _git('show', '%s:%s/STATUS.md' % (ref, epic_rel)).splitlines():
            m = re.match(r'^\|\s*([A-Z]\d+[a-z]?(?:\.\d+)?)\s*\|\s*([a-z-]+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$', line)
            if m:
                old_rows[_impact.canon(m.group(1))] = (m.group(2), m.group(3), m.group(4))
        for code, row in _rows.items():
            old = old_rows.get(code)
            if old is None or old[0] != row['state']:
                need[code].add('state')
            if old is None or old[1:] != (row['ref'], row['note']):
                need[code].add('note')
        trace = _impact.build_trace()
        for code, tr in trace.items():
            for mod in tr['modules']:
                if os.path.relpath(mod, ROOT) in changed:
                    need[code].add('content')
        cl = _git('diff', ref, '--', 'CHANGELOG.md')
        probs = []
        for code in sorted(need):
            if code in _NO_PAGE:
                code_page = _NO_PAGE[code]
            else:
                code_page = code
            waived = re.search(r'^\+.*no page change:.*\b%s\b' % re.escape(code), cl, re.M | re.I)
            if 'content' in need[code]:
                page = 'timeline/task-%s.html' % code_page
                if page not in changed and not waived:
                    probs.append('%-5s <- its spec or content module changed since %s, but %s did not. Rebuild it, or add '
                                 '"no page change: %s" to the CHANGELOG.md entry' % (code, ref, page, code))
            if 'note' in need[code] and code_page == code and 'timeline/task-%s.html' % code not in changed:
                probs.append('%-5s <- its STATUS.md note or ref changed since %s, but timeline/task-%s.html did not: run _generator/sync_status.py %s' % (code, ref, code, code))
            for fact, why in (('state', 'its STATUS.md state'), ('title', 'its spec title')):
                if fact not in need[code] or (fact == 'title' and waived):
                    continue
                for f, d in _impact.impact(code_page).items():
                    if d['kind'] != 'source' and fact in d['facts'] and f not in changed:
                        probs.append('%-5s <- %s changed since %s, but %s (which shows the %s) did not' % (code, why, ref, f, fact))
        if need and not any(f == 'CHANGELOG.md' for f in changed):
            probs.append('CHANGELOG.md <- %d task(s) changed since %s and no changelog entry was added: run _assets/changelog.py add' % (len(need), ref))
        _group('changed since %s' % ref, probs, '%d changed task(s); every mapped file changed with them' % len(need))

print()
if failures:
    print('%d fact group(s) disagree. Fix the documents, or the pattern if it is over-matching.' % failures)
    sys.exit(1)
print('All cross-stated facts agree.')
