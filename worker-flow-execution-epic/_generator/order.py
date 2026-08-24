# -*- coding: utf-8 -*-
ORDER = ['S7','S1','S4','S5','C3', 'S2','S3','S8','E3', 'A1','D2','A2','A3',
         'A4','A5','A6','S6','A8','A9','D1', 'B1','B2','B3','B4','E1','E2',
         'B5','A7','B6','B7', 'C1','C2']
WAVE = {}
for w,codes in [(0,['S7','S1','S4','S5','C3']),(1,['S2','S3','S8','E3']),
                (2,['A1','D2','A2','A3']),(3,['A4','A5','A6','S6','A8','A9','D1']),
                (4,['B1','B2','B3','B4','E1','E2']),(5,['B5','A7','B6','B7']),(6,['C1','C2'])]:
    for c in codes: WAVE[c]=w
PHASE={'S1':'fase-3h','S2':'fase-3','S3':'fase-3','S4':'fase-3h','S5':'transversais',
 'S6':'transversais','S7':'fase-1','S8':'fase-1','A1':'transversais','A2':'transversais',
 'A3':'transversais','A4':'fase-3','A5':'fase-3','A6':'fase-3','A7':'fase-3h','A8':'fase-1',
 'A9':'fase-4','B1':'fase-2','B2':'fase-2','B3':'fase-2','B4':'fase-3','B5':'fase-3',
 'B6':'fase-3h','B7':'fase-1','C1':'transversais','C2':'transversais','C3':'fase-6',
 'D1':'fase-6','D2':'fase-6','E1':'fase-4','E2':'fase-5','E3':'fase-3'}
def nav(code, titles):
    i = ORDER.index(code)
    prev = ORDER[i-1] if i>0 else None
    nxt  = ORDER[i+1] if i<len(ORDER)-1 else None
    out = {}
    if prev:
        t = titles[prev]
        out['prev'] = ('task-%s.html'%prev, ('← %s — %s'%(prev,t[0]), '← %s — %s'%(prev,t[1])))
    if nxt:
        t = titles[nxt]
        out['next'] = ('task-%s.html'%nxt, ('Next: %s — %s →'%(nxt,t[0]), 'Próxima: %s — %s →'%(nxt,t[1])))
    out['phase'] = (PHASE[code]+'.html', ('Where this lands in the flow →','Onde isto entra no fluxo →'))
    out['wave'] = WAVE[code]
    return out
