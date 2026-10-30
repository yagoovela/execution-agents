# -*- coding: utf-8 -*-
"""Mirror the Workflow spec files into this public repository, with the private values removed.

    python3 worker-flow-execution-epic/_generator/publish_sync.py --from "$EPIC" --literals "$EPIC/_generator/public_redactions.json"
    python3 worker-flow-execution-epic/_generator/publish_sync.py --from "$EPIC" --literals "$EPIC/_generator/public_redactions.json" --check
    python3 worker-flow-execution-epic/_generator/publish_sync.py --from "$EPIC" --literals "$EPIC/_generator/public_redactions.json" --hashes

`$EPIC` is `.claude/tasks/worker-flow-execution-epic` in your Workflow checkout. The literal
list is private and stays in Workflow: it names the values this repository must not show.

The default run copies every top-level `.md` and `.html` file of the Workflow folder into
`worker-flow-execution-epic/`, applies the literal list on the way, and writes nothing if
any rule no longer matches its file. A rule that stops matching means the Workflow text
changed, so the value it removed may now be in the copy: fix the rule first.

`--check` writes nothing. It fails when a mirror file differs from its redacted source,
when a source file has no mirror, when a mirror file has no source, or when a rule no
longer matches.

`--hashes` rewrites `_generator/redactions.json` from the literal list. Run it after the
pages are rebuilt: it drops the six-word runs of a removed passage that a published file
legitimately contains, and it refuses when a removed value is still published.
`reconcile_facts.py` then fails whenever a hashed value or passage shows up again.
"""
import argparse
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import public_redact as pr

MIRROR = os.path.join(pr.ROOT, 'worker-flow-execution-epic')

MIRROR_ONLY = {
    'README.md': 'describes this mirror; Workflow has no counterpart',
    'S6-WORKER-NETWORK-POSITION.md': 'written in this repository',
}
SOURCE_ONLY = {
    'arquitetura-v2-complemento.html': 'a copy of a root page; the published root page is maintained here',
}


def load_literals(path):
    with open(path, encoding='utf-8') as f:
        lit = json.load(f)
    for key in ('drop_files', 'rules', 'values'):
        if key not in lit:
            raise SystemExit('%s: missing "%s"' % (path, key))
    return lit


def sources(src):
    return sorted(f for f in os.listdir(src)
                  if f.endswith(('.md', '.html')) and os.path.isfile(os.path.join(src, f)))


def redact(name, text, lit):
    """Apply every rule for `name`. Return (text, problems, removed passages)."""
    problems, passages = [], []
    for i, r in enumerate(lit['rules']):
        if not fnmatch.fnmatch(name, r['file']):
            continue
        if r.get('kind') == 'drop-line':
            lines = text.split('\n')
            hit = [l for l in lines if l.startswith(r['match'])]
            if len(hit) != r.get('count', 1):
                problems.append('rule %d (%s) matched %d line(s) of %s, expected %d' % (i, r['class'], len(hit), name, r.get('count', 1)))
                continue
            passages += hit
            text = '\n'.join(l for l in lines if not l.startswith(r['match']))
        else:
            n = text.count(r['old'])
            if n != r.get('count', 1):
                problems.append('rule %d (%s) matched %d time(s) in %s, expected %d' % (i, r['class'], n, name, r.get('count', 1)))
                continue
            if r.get('passage'):
                passages.append(r['old'])
            text = text.replace(r['old'], r['new'])
    return text, problems, passages


def plan(src, lit):
    """Return ({name: redacted text}, problems, removed passages)."""
    out, problems, passages = {}, [], []
    for name in sources(src):
        if name in SOURCE_ONLY:
            continue
        text = open(os.path.join(src, name), encoding='utf-8').read()
        if name in lit['drop_files']:
            passages.append(text)
            continue
        out[name], probs, pas = redact(name, text, lit)
        problems += probs
        passages += pas
    for f in lit['drop_files']:
        if f not in sources(src):
            problems.append('drop_files names %s, which the Workflow folder does not have' % f)
    return out, problems, passages


def mirror_files():
    return sorted(f for f in os.listdir(MIRROR) if f.endswith(('.md', '.html')) and f not in MIRROR_ONLY)


def compare(out):
    diffs = []
    for name, text in sorted(out.items()):
        p = os.path.join(MIRROR, name)
        if not os.path.exists(p):
            diffs.append('missing  %s' % name)
        elif open(p, encoding='utf-8').read() != text:
            diffs.append('differs  %s' % name)
    for name in mirror_files():
        if name not in out:
            diffs.append('no source %s (dropped by the literal list, or deleted in Workflow)' % name)
    return diffs


def build_hashes(lit, passages):
    """Return (hash file dict, problems, report lines)."""
    tree = {n: set() for n in pr.SIZES}
    for p in pr.published_files():
        try:
            toks = pr.tokens(pr.normalize(open(p, encoding='utf-8').read()))
        except (UnicodeDecodeError, OSError):
            continue
        for n in pr.SIZES:
            tree[n].update(h for h, _ in pr.grams(toks, n))
    hashes = {n: set() for n in pr.SIZES}
    problems, report = [], []
    kinds = {}
    for v in lit['values']:
        n, h = pr.value_hashes(v['value'])
        if h in tree[n]:
            problems.append('a %s value is still published; remove it before hashing' % v['kind'])
        hashes[n].add(h)
        kinds[v['kind']] = kinds.get(v['kind'], 0) + 1
    for k in sorted(kinds):
        report.append('%-16s %d value(s)' % (k, kinds[k]))
    for i, text in enumerate(passages):
        allh = pr.passage_hashes(text)
        keep = allh - tree[6]
        if allh and len(keep) < len(allh) / 2:
            problems.append('passage %d: %d of %d six-word runs are published; it looks leaked, not shared' % (i, len(allh) - len(keep), len(allh)))
        hashes[6] |= keep
        report.append('passage %-8d %d run(s) hashed, %d shared with published text' % (i, len(keep), len(allh) - len(keep)))
    data = {
        'about': 'SHA-256 hashes of values this public repository must not show. See _generator/public_redact.py.',
        'digest_hex_chars': pr.DIGEST,
        'hashes': {str(n): sorted(hashes[n]) for n in pr.SIZES if hashes[n]},
    }
    return data, problems, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='src', required=True, help='the Workflow epic folder')
    ap.add_argument('--literals', required=True, help='the private literal list')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--hashes', action='store_true')
    a = ap.parse_args()
    lit = load_literals(a.literals)
    out, problems, passages = plan(a.src, lit)
    if a.hashes:
        data, probs, report = build_hashes(lit, passages)
        print('\n'.join(report))
        if problems or probs:
            print('\n'.join(problems + probs))
            sys.exit(1)
        with open(pr.HASHES, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1)
            f.write('\n')
        print('wrote %s: %d hashes' % (os.path.relpath(pr.HASHES, pr.ROOT), sum(len(v) for v in data['hashes'].values())))
        return
    if problems:
        print('\n'.join(problems))
        print('Nothing written. Fix the literal list for the changed Workflow text first.')
        sys.exit(1)
    diffs = compare(out)
    if a.check:
        if diffs:
            print('\n'.join(diffs))
            sys.exit(1)
        print('OK: %d mirror files match their redacted Workflow source' % len(out))
        return
    for name, text in sorted(out.items()):
        with open(os.path.join(MIRROR, name), 'w', encoding='utf-8') as f:
            f.write(text)
    for d in diffs:
        print(d)
    print('mirrored %d files, %d changed' % (len(out), sum(1 for d in diffs if not d.startswith('no source'))))


if __name__ == '__main__':
    main()
