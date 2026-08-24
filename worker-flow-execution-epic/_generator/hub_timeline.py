# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Visual realignment of timeline/index.html onto the task-page design system
(BASE + EXTRA_CSS from tasklib.py + a page overlay).

Layout only: every data-en/data-pt pair, every href and every id is carried
across byte-identically. The single content-touching change is making the
hard-coded `N tasks` wave chip bilingual.
"""
import re

TMP = _GEN + '/'
PATH = _EPIC + '/timeline/index.html'

BASE = open(TMP + 'base.css', encoding='utf-8').read()
_src = open(TMP + 'tasklib.py', encoding='utf-8').read()
_i = _src.index('EXTRA_CSS = """') + len('EXTRA_CSS = """')
EXTRA_CSS = _src[_i:_src.index('"""', _i)]

TL_CSS = """
/* ---------- delivery timeline: same vocabulary as the task pages ---------- */
.hero .kicker .ico{display:inline-flex;align-items:center;justify-content:center;flex:none;
      width:38px;height:38px;border-radius:10px;font-size:19px;line-height:1;
      background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22)}
.hero h1{max-width:34ch}
.hero .goal{max-width:92ch}
.hero-links{margin-top:16px}
.hero-links a{max-width:100%;overflow-wrap:anywhere}

/* the opening rule reads as a callout */
.aside{border:1px solid #E2E8F0;border-radius:12px;padding:16px 20px;font-size:13.5px;
      line-height:1.72;background:#F8FAFC;color:#334155;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.aside.warn{background:#FFFBEB;border-color:#FDE68A;border-left:4px solid #F59E0B;color:#78350F}
.aside.info{background:#EFF6FF;border-color:#BFDBFE;color:#1E3A8A}
.aside-title{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.aside.warn .aside-title{color:#B45309}
.aside strong{font-weight:650;color:#451A03}
.aside code{background:rgba(255,255,255,.75);border:1px solid rgba(0,0,0,.07);padding:1px 5px;
      border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:11.5px;overflow-wrap:anywhere}

/* one wave = one numbered section */
.tl-wave{position:relative;margin:0 0 30px;padding-top:26px}
.tl-wave::before{content:none}
.tl-wave>.sec-label{margin:0 0 12px}
.sec-label h2{min-width:0;overflow-wrap:anywhere}
.tl-wave.t-hazard .sec-label .n{background:#B91C1C}
.tl-wave.t-data .sec-label .n{background:#B45309}
.tl-wave.t-control .sec-label .n{background:#047857}
.tl-wave.t-muted .sec-label .n{background:#6B21A8}
.wv{font-size:9.5px;font-weight:700;padding:4px 9px;border-radius:20px;text-transform:uppercase;
      letter-spacing:.5px;white-space:nowrap;flex:none}
.w0{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.w1{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A}
.w2{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}
.w3{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}
.w4{background:#DCFCE7;color:#14532D;border:1px solid #A7F3D0}
.w5{background:#DCFCE7;color:#14532D;border:1px solid #A7F3D0}
.w6{background:#F3E8FF;color:#6B21A8;border:1px solid #E9D5FF}

/* why this wave = the purpose line of the task pages */
.tl-why{font-size:14px;line-height:1.65;color:#0F172A;font-weight:500;max-width:96ch;
      border-left:3px solid #6366F1;padding-left:13px;margin:0 0 14px}
.tl-wave.t-hazard .tl-why{border-left-color:#DC2626}
.tl-wave.t-data .tl-why{border-left-color:#D97706}
.tl-wave.t-control .tl-why{border-left-color:#059669}
.tl-wave.t-muted .tl-why{border-left-color:#7C3AED}

/* every task card reads like a .part block */
.tl-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin:0}
a.tl-card{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;
      text-decoration:none;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;
      background-color:#fff;background-image:linear-gradient(to right,#0F172A,#1E293B);
      background-repeat:no-repeat;background-size:100% 44px;
      box-shadow:0 1px 3px rgba(15,23,42,.06);transition:box-shadow .15s,border-color .15s,transform .15s}
a.tl-card:hover{border-color:#94A3B8;box-shadow:0 4px 14px rgba(15,23,42,.13);transform:translateY(-1px)}
a.tl-card .c{grid-column:1;grid-row:1;margin:9px 0 9px 14px;min-width:26px;height:26px;padding:0 7px;
      border-radius:7px;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);
      color:#fff;display:inline-flex;align-items:center;justify-content:center;
      font-family:'SF Mono',Menlo,monospace;font-size:12px;font-weight:700;letter-spacing:.3px}
a.tl-card .chev{grid-column:2;grid-row:1;justify-self:end;margin-right:15px;
      color:#94A3B8;font-size:17px;line-height:1}
a.tl-card:hover .chev{color:#E2E8F0}
a.tl-card .t{grid-column:1/-1;grid-row:2;margin:14px 16px 0;padding-left:11px;
      border-left:3px solid #6366F1;font-size:13.5px;font-weight:600;line-height:1.45;
      color:#0F172A;overflow-wrap:anywhere}
a.tl-card .g{grid-column:1/-1;grid-row:3;margin:9px 16px 15px;font-size:12.5px;line-height:1.62;
      color:#64748B;overflow-wrap:anywhere}

/* exit gate */
.gate{display:grid;grid-template-columns:auto minmax(0,1fr);gap:9px 14px;background:#F8FAFC;
      border:1px solid #E2E8F0;border-left:3px solid #94A3B8;border-radius:10px;padding:13px 17px;
      margin-top:14px;font-size:12.5px;color:#334155;line-height:1.68}
.gate b{font-size:9.5px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;color:#64748B;
      white-space:nowrap;padding-top:3px}
.tl-wave.t-hazard .gate{border-left-color:#DC2626}
.tl-wave.t-data .gate{border-left-color:#D97706}
.tl-wave.t-control .gate{border-left-color:#059669}
.tl-wave.t-muted .gate{border-left-color:#7C3AED}
@media(max-width:640px){.gate{grid-template-columns:1fr;gap:4px 0}.gate b{padding-top:6px}}

.code-block{white-space:pre-wrap;word-break:normal;overflow-wrap:anywhere;overflow-x:auto}
.page-footer-nav a.nx{margin-left:auto}
"""

RE_FOOTER = re.compile(r'[ \t]*<div class="page-nav">\s*(<a .*?</a>)\s*(<a .*?</a>)\s*</div>\n', re.S)
RE_HEADER = re.compile(
    r'[ \t]*<div class="page-header">(.*?)\s*(<span class="" data-en=.*?</span>)</div>\n'
    r'[ \t]*<div class="page-sub">(.*?)</div>\n', re.S)
RE_WAVE = re.compile(
    r'[ \t]*<div class="tl-dot">(\d)</div>\n'
    r'[ \t]*<div class="tl-head">(.*?)\n'
    r'[ \t]*<span class="wv (w\d)">(\d+ tasks)</span></div>\n', re.S)


def convert(path):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('</style>\n', 1)
    title = head.split('<style>', 1)[0]

    # 1. footer: keep the back link, promote the forward link into the hero
    m = RE_FOOTER.search(body)
    assert m, 'footer not matched'
    back_a, fwd_a = m.group(1), m.group(2)
    fwd_hero = fwd_a.replace(' class="back-btn"', '')
    back_foot = back_a.replace(' class="back-btn"', '')
    body = body[:m.start()] + '  <div class="page-footer-nav">%s</div>\n' % back_foot + body[m.end():]

    # 2. header + sub -> hero
    def hero(mm):
        ico, h1, sub = mm.group(1).strip(), mm.group(2), mm.group(3)
        return ('  <div class="hero">\n'
                '    <div class="kicker"><span class="ico">%s</span></div>\n'
                '    <h1>%s</h1>\n'
                '    <div class="goal">%s</div>\n'
                '    <div class="hero-links">%s</div>\n'
                '  </div>\n' % (ico, h1, sub, fwd_hero))
    body, n = RE_HEADER.subn(hero, body, count=1)
    assert n == 1, 'header not matched'

    # 3. each wave head -> numbered .sec-label (id stays on .tl-wave)
    def sec(mm):
        num, ttl, wcls, chip = mm.group(1), mm.group(2).strip(), mm.group(3), mm.group(4)
        return ('    <div class="sec-label"><span class="n">%s</span><h2>%s</h2>'
                '<span class="wv %s" data-en="%s" data-pt="%s">%s</span>'
                '<span class="rule"></span></div>\n' % (num, ttl, wcls, chip, chip, chip))
    body, n = RE_WAVE.subn(sec, body)
    assert n == 7, 'waves matched: %d' % n

    style = '<style>\n%s\n%s\n%s</style>\n' % (BASE, EXTRA_CSS, TL_CSS)
    open(path, 'w', encoding='utf-8').write(title + style + body)
    print('timeline realigned: 7 waves, footer + hero rebuilt')


def restyle(path):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('</style>\n', 1)
    title = head.split('<style>', 1)[0]
    style = '<style>\n%s\n%s\n%s</style>\n' % (BASE, EXTRA_CSS, TL_CSS)
    open(path, 'w', encoding='utf-8').write(title + style + body)
    print('stylesheet refreshed')


if __name__ == '__main__':
    import sys
    (restyle if '--css' in sys.argv else convert)(PATH)
