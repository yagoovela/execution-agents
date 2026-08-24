# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Snapshot ids / hrefs / bilingual pairs for the two hub pages."""
import re, json, sys, html

EPIC = _EPIC + '/'
FILES = {
    'timeline': EPIC + 'timeline/index.html',
    'complemento': EPIC + 'arquitetura-v2-complemento.html',
}

def snap(path):
    s = open(path, encoding='utf-8').read()
    body = s.split('</style>\n', 1)[1]
    ids = sorted(re.findall(r'\sid="([^"]*)"', body))
    hrefs = sorted(re.findall(r'\shref="([^"]*)"', body))
    pairs = sorted(re.findall(r'data-en="([^"]*)"\s+data-pt="([^"]*)"', body))
    lone_en = re.findall(r'data-en="([^"]*)"(?!\s+data-pt=)', body)
    return {'ids': ids, 'hrefs': hrefs, 'pairs': pairs, 'n_pairs': len(pairs),
            'lone_en': lone_en}

if __name__ == '__main__':
    out = {k: snap(v) for k, v in FILES.items()}
    tag = sys.argv[1] if len(sys.argv) > 1 else 'before'
    json.dump(out, open(_GEN + '/hub_snap_%s.json' % tag, 'w'), ensure_ascii=False, indent=1)
    for k, v in out.items():
        print(k, 'ids=%d hrefs=%d pairs=%d lone_en=%d' % (len(v['ids']), len(v['hrefs']), v['n_pairs'], len(v['lone_en'])))
