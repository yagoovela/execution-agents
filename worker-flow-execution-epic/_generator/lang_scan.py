# -*- coding: utf-8 -*-
import re, html, glob, sys

PT_ONLY = re.compile(r'(?<![\w-])(tipos?|integraç\w+|qualquer|coisa|nenhum\w*|resultado\w*|não|são|está[o]?|então|cada|também|apenas|ainda|mesmo|porque|quando|antes|depois|hoje|fluxo|nós|node[s]? por|por provider|dele[s]?|dela[s]?|seu|sua|isso|aqui|agora|sempre|nunca|todos?|toda[s]?|maior|menor|linha[s]?|arquivo[s]?|banco|fila|escrita[s]?|leitura[s]?|chave[s]?|erro[s]?|falha[s]?|prova|medi\w+|recus\w+|teto|cadeia|orçamento|gasto|caminho|entrada[s]?|saída[s]?)(?![\w-])', re.I)
EN_ONLY = re.compile(r'(?<![\w-])(the|and|with|from|that|this|which|every|when|before|after|only|still|would|should|does|doesn|isn|aren|there|their|these|those|because|while|through|without|between|already|nothing|anything|something|whatever|however)(?![\w-])', re.I)

def strip(t): return re.sub(r'<[^>]+>', ' ', t)

def scan(path):
    s = open(path, encoding='utf-8').read()
    hits = []
    for m in re.finditer(r'data-en="(.*?)"\s+data-pt="(.*?)"', s, re.S):
        en = strip(html.unescape(html.unescape(m.group(1))))
        pt = strip(html.unescape(html.unescape(m.group(2))))
        pen = PT_ONLY.findall(en)
        if pen: hits.append(('PT-in-EN', sorted(set(w.lower() for w in pen)), ' '.join(en.split())[:110]))
        pep = EN_ONLY.findall(pt)
        if pep: hits.append(('EN-in-PT', sorted(set(w.lower() for w in pep)), ' '.join(pt.split())[:110]))
    # non-bilingual prose chips
    for cls in ('fn-loc','loc'):
        for m in re.finditer(r'class="%s"[^>]*>(.*?)</(?:div|span)>' % cls, s, re.S):
            t = ' '.join(strip(m.group(1)).split())
            if 'data-en' in m.group(0): continue
            if PT_ONLY.search(t) or (len(t.split()) > 2 and EN_ONLY.search(t)):
                hits.append(('CHIP-not-bilingual', [], t[:110]))
    return hits

files = sys.argv[1:]
total = 0
for f in files:
    h = scan(f)
    if h:
        print('==', f)
        for k, w, t in h:
            print('   %-20s %-28s | %s' % (k, ','.join(w)[:28], t))
        total += len(h)
print('\nTOTAL HITS:', total)
