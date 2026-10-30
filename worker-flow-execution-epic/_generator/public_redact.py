# -*- coding: utf-8 -*-
"""Find values that must not be published, without storing the values here.

This repository is public and the Workflow spec it mirrors is private. A few things in the
spec stay out of the public copy: people's names, customer names, email addresses, AWS
profile names, and the text of a security gap that is not fixed yet. `publish_sync.py`
removes them while it mirrors the spec. This module is the check that they stay out.

Writing the values here would publish them. So `redactions.json` holds only a SHA-256 of
each value, computed over normalized words, and this module compares those hashes with
every word sequence of every published file:

- a value of one to three words is stored as the hash of those words;
- a removed passage is stored as the hash of each run of six words, minus the runs that
  the published files legitimately contain.

Generic patterns (an email address outside the allowed domains, an AWS ARN, an account id,
an access key id, a named AWS profile) need no hash and are listed in `PATTERNS`.

A hash of a short value can be reversed by guessing candidates. The hashes keep the values
out of a casual read and out of a search engine; they are not a secret.
"""
import hashlib
import html
import json
import os
import re

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(GEN))
HASHES = os.path.join(GEN, 'redactions.json')
SIZES = (1, 2, 3, 6)
DIGEST = 20

ALLOWED_EMAIL_DOMAINS = ('example.com', 'example.org', 'example.net', 'upload.fluxprompt.com', 'anthropic.com')
ALLOWED_EMAIL_TLDS = ('example', 'invalid', 'test', 'localhost')
ALLOWED_PROFILES = ('default',)

PATTERNS = [
    ('email address', re.compile(r'[A-Za-z0-9._%+-]+@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})\b')),
    ('AWS ARN', re.compile(r'\barn:aws[a-z-]*:[a-z0-9-]*:')),
    ('AWS account id', re.compile(r'(?<![\w.:/-])\d{12}(?![\w.:/-])')),
    ('AWS access key id', re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b')),
    ('AWS profile name', re.compile(r'(?i)(?:--profile[= ]+|AWS_PROFILE=|aws profile\s*[`\'"])([A-Za-z0-9][\w.-]*)')),
]

_TAG = re.compile(r'<[A-Za-z/!][^<>]{0,2000}>')
_ATTR = re.compile(r'=\s*"([^"]*)"|=\s*\'([^\']*)\'')
_TOKEN = re.compile(r'[a-z0-9@._+-]+')
_EDGE = '@._+-'


def _tag_text(m):
    tag = m.group(0)
    vals = [a or b for a, b in _ATTR.findall(tag)]
    return ' ' + ' '.join(vals) + ' ' + '\n' * tag.count('\n')


def normalize(text):
    """Return the text as the hashes see it: unescaped, tags reduced to their attribute values."""
    for _ in range(2):
        text = html.unescape(text)
    text = _TAG.sub(_tag_text, text)
    return text.replace('`', ' ').replace('*', ' ').lower()


def tokens(text):
    """Return (token, line) pairs of normalized text."""
    out = []
    for n, line in enumerate(text.split('\n'), 1):
        for t in _TOKEN.findall(line):
            t = t.strip(_EDGE)
            if t:
                out.append((t, n))
    return out


def digest(words):
    return hashlib.sha256(' '.join(words).encode('utf-8')).hexdigest()[:DIGEST]


def grams(toks, n):
    """Yield (hash, line) for every run of n tokens. A one-token run also yields the parts of
    the token split on '@' and '.', so a domain or a mailbox name matches on its own."""
    words = [t for t, _ in toks]
    for i in range(len(words) - n + 1):
        yield digest(words[i:i + n]), toks[i][1]
        if n == 1 and re.search(r'[@.]', words[i]):
            for part in re.split(r'[@.]+', words[i]):
                part = part.strip(_EDGE)
                if part:
                    yield digest([part]), toks[i][1]


def value_hashes(value):
    """Hash a value of one to three words, as `grams` would see it in a page."""
    words = [t for t, _ in tokens(normalize(value))]
    if not 1 <= len(words) <= 3:
        raise ValueError('a value must be one to three words after normalization, got %d' % len(words))
    return len(words), digest(words)


def passage_hashes(text):
    return {h for h, _ in grams(tokens(normalize(text)), 6)}


def load():
    with open(HASHES, encoding='utf-8') as f:
        data = json.load(f)
    return {int(n): set(v) for n, v in data['hashes'].items()}


def published_files(root=ROOT):
    """Every file the repository publishes as text."""
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ('.git', '__pycache__', 'node_modules')]
        for f in files:
            p = os.path.join(d, f)
            if p == HASHES or not f.endswith(('.md', '.html', '.py', '.js', '.css', '.json', '.txt', '.sh', '.sql', '.csv')):
                continue
            yield p


def _pattern_hits(raw):
    text = raw
    for _ in range(2):
        text = html.unescape(text)
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            if kind == 'email address':
                dom = m.group(1).lower()
                if dom in ALLOWED_EMAIL_DOMAINS or dom.rsplit('.', 1)[-1] in ALLOWED_EMAIL_TLDS:
                    continue
            if kind == 'AWS profile name' and m.group(1).lower() in ALLOWED_PROFILES:
                continue
            yield kind, text.count('\n', 0, m.start()) + 1


def scan(hashes=None, root=ROOT, files=None):
    """Return a sorted list of (path, line, kind). The value itself is never returned."""
    hashes = load() if hashes is None else hashes
    hits = set()
    for p in files or published_files(root):
        try:
            raw = open(p, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        rel = os.path.relpath(p, root)
        toks = tokens(normalize(raw))
        for n in SIZES:
            want = hashes.get(n)
            if not want:
                continue
            for h, line in grams(toks, n):
                if h in want:
                    hits.add((rel, line, 'redacted value' if n < 6 else 'redacted passage'))
        for kind, line in _pattern_hits(raw):
            hits.add((rel, line, kind))
    return sorted(hits)
