# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Visual realignment of arquitetura-v2-complemento.html onto the task-page
design system (BASE + EXTRA_CSS from tasklib.py + a page overlay).

Layout only: every data-en/data-pt pair, every href and every id is carried
across byte-identically. The single content-touching change is making the
hard-coded Portuguese <strong> leftover in the closing note bilingual.
"""
import re

TMP = _GEN + '/'
PATH = _EPIC + '/arquitetura-v2-complemento.html'

BASE = open(TMP + 'base.css', encoding='utf-8').read()
_src = open(TMP + 'tasklib.py', encoding='utf-8').read()
_i = _src.index('EXTRA_CSS = """') + len('EXTRA_CSS = """')
EXTRA_CSS = _src[_i:_src.index('"""', _i)]

CO_CSS = """
/* ---------- companion hub: same vocabulary as the task pages ---------- */
.hero .kicker .ico{display:inline-flex;align-items:center;justify-content:center;flex:none;
      width:38px;height:38px;border-radius:10px;font-size:19px;line-height:1;
      background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22)}
.hero h1{max-width:34ch}
.hero .goal{max-width:92ch}
.hero .goal code{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);
      padding:1px 5px;border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:12.5px;color:#fff}
.hero-links{margin-top:16px}
.hero-links a{max-width:100%;overflow-wrap:anywhere}

.lede{margin:0 0 20px}

/* legend = a chip bar */
.legend{display:flex;flex-wrap:wrap;justify-content:flex-start;align-items:center;gap:8px 18px;
      background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:13px 18px;margin:0 0 20px;
      box-shadow:0 1px 3px rgba(15,23,42,.05)}
.legend-item{display:flex;align-items:center;gap:8px;font-size:12px;color:#475569}
.legend-swatch{width:18px;height:10px;border-radius:3px;flex:none}

/* the four states = the glance tiles */
.states{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:0 0 26px}
.state{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:14px 16px 15px;
      border-top:3px solid #94A3B8;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.state.now{border-top-color:#DC2626}.state.s1{border-top-color:#D97706}
.state.s4{border-top-color:#3B82F6}.state.tgt{border-top-color:#059669}
.state h4{margin:0 0 9px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
      color:#94A3B8}
.state ul{margin:0;padding-left:0;list-style:none;font-size:12px;color:#334155;line-height:1.55}
.state li{position:relative;padding-left:15px;margin-bottom:5px}
.state li:last-child{margin-bottom:0}
.state li::before{content:'';position:absolute;left:2px;top:7px;width:5px;height:5px;border-radius:50%;
      background:#CBD5E1}

/* each phase = a .part card */
.section{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;
      margin:0 0 16px;padding:0;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.section-header{background:linear-gradient(to right,#0F172A,#1E293B);color:#fff;padding:14px 20px;
      display:flex;align-items:center;gap:12px;flex-wrap:wrap;border:0;margin:0}
.section-number{width:26px;height:26px;border-radius:7px;background:rgba(255,255,255,.15);
      border:1px solid rgba(255,255,255,.25);color:#fff;flex:none;display:flex;align-items:center;
      justify-content:center;font-size:12px;font-weight:700}
.section-title{font-size:15px;font-weight:600;letter-spacing:-.15px;color:#fff;min-width:0;
      overflow-wrap:anywhere}
.section-header a.dive{margin-left:auto;font-size:10.5px;font-weight:700;text-transform:uppercase;
      letter-spacing:.6px;text-decoration:none;color:#CBD5E1;background:rgba(0,0,0,.28);
      border:1px solid rgba(255,255,255,.16);padding:4px 10px;border-radius:20px;white-space:nowrap}
.section-header a.dive:hover{background:rgba(255,255,255,.18);color:#fff}
.section-desc{margin:18px 22px 0;padding-left:13px;border-left:3px solid #6366F1;max-width:96ch;
      font-size:14px;line-height:1.65;font-weight:500;color:#0F172A;text-align:left}

/* the substeps = the body of the card */
.section .substep-group,.substep-group{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));
      gap:12px;align-items:start;margin:16px 0 0;padding:0 22px 20px;background:transparent;border:0;width:auto}
@media(max-width:980px){.substep-group{grid-template-columns:1fr}}
.substep{display:block;background:#F8FAFC;border:1px solid #E2E8F0;border-left:3px solid #94A3B8;
      border-radius:10px;padding:14px 17px 13px;box-shadow:none}
.substep.k-ok{border-left-color:#059669}
.substep.k-add{border-left-color:#3B82F6}
.substep.k-gap{border-left-color:#DC2626}
.substep .kind{display:inline-flex;align-items:center;gap:7px;margin-bottom:7px}
.substep .kind .ico{font-size:12px;line-height:1;width:18px;height:18px;border-radius:5px;flex:none;
      display:inline-flex;align-items:center;justify-content:center;font-weight:700}
.k-ok .kind .ico{background:#D1FAE5;color:#065F46}.k-ok .kind .lbl{color:#047857}
.k-add .kind .ico{background:#DBEAFE;color:#1E40AF}.k-add .kind .lbl{color:#1D4ED8}
.k-gap .kind .ico{background:#FEE2E2;color:#991B1B}.k-gap .kind .lbl{color:#B91C1C}
.substep .kind .lbl{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.7px}
.substep-content strong{display:block;font-size:14px;line-height:1.4;color:#0F172A;margin-bottom:5px;
      font-weight:650;letter-spacing:-.15px}
.substep .sd{color:#334155;font-size:13px;line-height:1.7;max-width:none;margin-top:3px;
      overflow-wrap:anywhere}
.substep .sd code{background:#fff;border:1px solid #E2E8F0;padding:1.5px 5px;border-radius:4px;
      font-family:'SF Mono',Menlo,monospace;font-size:11.5px;color:#0F172A;overflow-wrap:anywhere}
.substep .sd strong{display:inline;font-size:inherit;margin:0}
.substep .chips{margin-top:11px;padding-top:9px;border-top:1px dashed #E2E8F0}

.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
a.tk,a.wv{text-decoration:none;cursor:pointer}
.tk{font-family:'SF Mono',Menlo,monospace;font-size:10.5px;font-weight:700;letter-spacing:.3px;
      background:#0F172A;color:#fff;padding:3px 8px;border-radius:6px;white-space:nowrap}
a.tk:hover{background:#312E81}
.wv{font-size:9.5px;font-weight:700;padding:3px 9px;border-radius:20px;text-transform:uppercase;
      letter-spacing:.5px;white-space:nowrap}
a.wv:hover{filter:brightness(.94)}
.w0{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.w1{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A}
.w2{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}
.w3{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}
.w4{background:#DCFCE7;color:#14532D;border:1px solid #A7F3D0}
.w5{background:#DCFCE7;color:#14532D;border:1px solid #A7F3D0}
.w6{background:#F3E8FF;color:#6B21A8;border:1px solid #E9D5FF}

/* cross-cutting lane = a .part card with a violet head */
.cross-cutting{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;
      margin:0 0 16px;padding:0;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.cross-cutting .lane-title{background:linear-gradient(to right,#4C1D95,#6D28D9);color:#fff;
      padding:14px 20px;margin:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
      justify-content:flex-start;text-align:left;font-size:15px;font-weight:600;letter-spacing:-.15px}
.cross-cutting .lane-title a.dive{float:none;margin-left:auto;font-size:10.5px;font-weight:700;
      text-transform:uppercase;letter-spacing:.6px;text-decoration:none;color:#E9D5FF;
      background:rgba(0,0,0,.26);border:1px solid rgba(255,255,255,.18);padding:4px 10px;
      border-radius:20px;white-space:nowrap}
.cross-cutting .lane-title a.dive:hover{background:rgba(255,255,255,.18);color:#fff}
.cross-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px;padding:20px 22px}
.cross-item{background:#F8FAFC;border:1px solid #E2E8F0;border-left:3px solid #7C3AED;border-radius:10px;
      padding:14px 17px;font-size:13px;line-height:1.7;color:#334155}
.cross-item strong{display:block;font-size:14px;font-weight:650;color:#0F172A;margin-bottom:5px;
      letter-spacing:-.15px}
.cross-item .chips{margin-top:11px;padding-top:9px;border-top:1px dashed #E2E8F0}

/* the by-wave comparison = a .part card */
.comparison{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;
      margin:0 0 16px;padding:0;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.comparison-title{background:linear-gradient(to right,#0F172A,#1E293B);color:#fff;padding:14px 20px;
      margin:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:15px;font-weight:600;
      letter-spacing:-.15px}
.comparison-title a.dive{float:none!important;margin-left:auto;font-size:10.5px;font-weight:700;
      text-transform:uppercase;letter-spacing:.6px;text-decoration:none;color:#CBD5E1;
      background:rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.16);padding:4px 10px;
      border-radius:20px;white-space:nowrap}
.comparison-title a.dive:hover{background:rgba(255,255,255,.18);color:#fff}
.wave-lanes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:0;
      padding:20px 22px 4px}
.wave-lane{background:#F8FAFC;border:1px solid #E2E8F0;border-top:3px solid #94A3B8;border-radius:10px;
      padding:13px 15px;gap:0}
.wave-lane:nth-child(1){border-top-color:#DC2626}
.wave-lane:nth-child(2){border-top-color:#D97706}
.wave-lane:nth-child(3){border-top-color:#3B82F6}
.wave-lane:nth-child(4){border-top-color:#3B82F6}
.wave-lane:nth-child(5){border-top-color:#059669}
.wave-lane:nth-child(6){border-top-color:#059669}
.wave-lane:nth-child(7){border-top-color:#7C3AED}
.wave-lane-title{font-size:11.5px;font-weight:700;color:#0F172A;text-align:left;text-transform:none;
      letter-spacing:-.1px;line-height:1.45;margin-bottom:10px}
.wave-lane .chips{gap:5px}

.note{background:#FFFBEB;border:1px solid #FDE68A;border-left:4px solid #F59E0B;border-radius:10px;
      padding:14px 17px;margin:0 22px 20px!important;max-width:none;font-size:13px;line-height:1.7;
      color:#78350F}
.note.info{background:#EFF6FF;border-color:#BFDBFE;border-left-color:#3B82F6;color:#1E3A8A}
.note strong{color:#451A03;font-weight:650}

.code-block{white-space:pre-wrap;word-break:normal;overflow-wrap:anywhere;overflow-x:auto}
.page-footer-nav a.nx{margin-left:auto}
"""

# --- top nav: single white back button, lang switch on the right ---
RE_TOPNAV = re.compile(
    r'([ \t]*<div class="top-nav">\n)'
    r'([ \t]*)(<a href="arquitetura-v2\.html" class="back-btn">.*?</a>)'
    r'(<a href="timeline/index\.html" class="back-btn">.*?</a>)\n'
    r'([ \t]*)(<div class="lang-sw".*?</div>)</div>\n', re.S)

# --- h1 + subtitle -> hero ---
RE_HEAD = re.compile(
    r'[ \t]*<h1 (data-en=".*?" data-pt=".*?")>(.*?)</h1>\n'
    r'\n?'
    r'[ \t]*<div class="subtitle" (data-en=".*?" data-pt=".*?")>(.*?)</div>\n', re.S)

# --- the untranslated leftover in the closing note ---
LEAK_OLD = ('<strong>Toda onda que remove um limitador vem depois da\n'
            '      onda que adiciona o teto correspondente.</strong>')
LEAK_NEW = ('<span data-en="&lt;strong&gt;Every wave that removes a throttle comes after the wave '
            'that adds the matching ceiling.&lt;/strong&gt;" '
            'data-pt="&lt;strong&gt;Toda onda que remove um limitador vem depois da onda que '
            'adiciona o teto correspondente.&lt;/strong&gt;">'
            '<strong>Every wave that removes a throttle comes after the wave that adds the '
            'matching ceiling.</strong></span>')


def convert(path):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('</style>\n', 1)
    title = head.split('<style>', 1)[0]

    m = RE_TOPNAV.search(body)
    assert m, 'top-nav not matched'
    back_a, tl_a, lang_sw = m.group(3), m.group(4), m.group(6)
    tl_hero = tl_a.replace(' class="back-btn"', '')
    body = (body[:m.start()]
            + '  <div class="top-nav">\n    %s\n    %s\n  </div>\n' % (back_a, lang_sw)
            + body[m.end():])

    def hero(mm):
        h1_attrs, h1_in, sub_attrs, sub_in = mm.groups()
        return ('  <div class="hero">\n'
                '    <div class="kicker"><span class="ico">\U0001F9ED</span></div>\n'
                '    <h1 %s>%s</h1>\n'
                '    <div class="goal" %s>%s</div>\n'
                '    <div class="hero-links">%s</div>\n'
                '  </div>\n' % (h1_attrs, h1_in, sub_attrs, sub_in, tl_hero))
    body, n = RE_HEAD.subn(hero, body, count=1)
    assert n == 1, 'h1/subtitle not matched'

    assert body.count(LEAK_OLD) == 1, 'leak fragment not found'
    body = body.replace(LEAK_OLD, LEAK_NEW)

    style = '<style>\n%s\n%s\n%s</style>\n' % (BASE, EXTRA_CSS, CO_CSS)
    open(path, 'w', encoding='utf-8').write(title + style + body)
    print('complemento realigned: top-nav, hero, note leak fixed')


def restyle(path):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('</style>\n', 1)
    title = head.split('<style>', 1)[0]
    style = '<style>\n%s\n%s\n%s</style>\n' % (BASE, EXTRA_CSS, CO_CSS)
    open(path, 'w', encoding='utf-8').write(title + style + body)
    print('stylesheet refreshed')


if __name__ == '__main__':
    import sys
    (restyle if '--css' in sys.argv else convert)(PATH)
