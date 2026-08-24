# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Find visible text nodes not covered by any data-en ancestor."""
from html.parser import HTMLParser
import sys

VOID = {'br','hr','img','input','meta','link','source','col'}

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # list of (tag, has_data_en, classattr)
        self.hits = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ('script','style'):
            self.skip += 1
        if tag in VOID:
            return
        self.stack.append((tag, 'data-en' in d, d.get('class',''), d.get('href','')))
    def handle_endtag(self, tag):
        if tag in ('script','style'):
            self.skip = max(0, self.skip-1)
            return
        if tag in VOID:
            return
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
    def handle_data(self, data):
        if self.skip: return
        t = data.strip()
        if not t: return
        if not any(ch.isalpha() for ch in t): return
        if any(f[1] for f in self.stack): return
        path = ' > '.join('%s.%s' % (f[0], f[2]) if f[2] else f[0] for f in self.stack[-3:])
        self.hits.append((path, t[:90]))

for name, path in [('timeline',_EPIC + '/timeline/index.html'),
                   ('complemento',_EPIC + '/arquitetura-v2-complemento.html')]:
    s = open(path, encoding='utf-8').read()
    p = P(); p.feed(s.split('</style>\n',1)[1])
    print('=== %s : %d uncovered text nodes ===' % (name, len(p.hits)))
    seen = set()
    for a, b in p.hits:
        k = (a, b)
        if k in seen: continue
        seen.add(k)
        print('   [%s]  %r' % (a, b))
