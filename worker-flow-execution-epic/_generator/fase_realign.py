# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

"""Visual realignment of the eight complemento/fase-*.html pages onto the
task-page design system (BASE + EXTRA_CSS from tasklib.py).

Layout only: every data-en/data-pt pair, every href and every id is carried
across byte-identically; only wrappers and CSS change.
"""
import re, os

TMP = _GEN + '/'
DIR = _EPIC + '/complemento/'
FILES = ['fase-1.html', 'fase-2.html', 'fase-3.html', 'fase-3h.html', 'fase-4.html',
         'fase-5.html', 'fase-6.html', 'transversais.html']

BASE = open(TMP + 'base.css', encoding='utf-8').read()

# pull EXTRA_CSS out of tasklib.py without importing it (no side effects)
_src = open(TMP + 'tasklib.py', encoding='utf-8').read()
_i = _src.index('EXTRA_CSS = """') + len('EXTRA_CSS = """')
EXTRA_CSS = _src[_i:_src.index('"""', _i)]

FASE_CSS = """
/* ---------- phase page: same vocabulary as the task pages ---------- */
.hero .kicker .ico{display:inline-flex;align-items:center;justify-content:center;flex:none;
      width:38px;height:38px;border-radius:10px;font-size:19px;line-height:1;
      background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22)}
.hero h1{max-width:34ch}
.hero .goal{max-width:92ch}
.hero .goal code{word-break:break-word}
.hero-links{margin-top:16px}
.hero-links a{max-width:100%;overflow-wrap:anywhere}

/* topic cards read like .part */
.fn-card{margin:0 0 16px;border-radius:14px;border:1px solid #E2E8F0;background:#fff;
      overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.fn-card-header{background:linear-gradient(to right,#0F172A,#1E293B);padding:14px 20px;
      justify-content:flex-start;align-items:center;gap:12px;flex-wrap:wrap;cursor:default}
.fn-card-header:hover{background:linear-gradient(to right,#0F172A,#1E293B)}
.fn-card-header::before{content:none}
.fn-card-header .fn-title{font-size:15px;font-weight:600;letter-spacing:-.15px;gap:12px;
      align-items:center;min-width:0;flex:1 1 auto;overflow-wrap:anywhere}
.fn-card-header .fn-title .badge{width:26px;height:26px;flex:none;padding:0;letter-spacing:0;
      border-radius:7px;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);
      color:#fff;display:inline-flex;align-items:center;justify-content:center;
      font-size:12px;font-weight:700}
.fn-card-header .fn-loc{margin-left:auto;max-width:100%;font-size:10.5px;color:#94A3B8;
      background:rgba(0,0,0,.28);padding:4px 9px;border-radius:6px;overflow-wrap:anywhere}
.fn-card-body{padding:20px 22px}
.fn-purpose{font-size:14px;line-height:1.65;color:#0F172A;font-weight:500;background:none;
      border:0;border-left:3px solid #6366F1;border-radius:0;padding:0 0 0 13px;margin-bottom:16px}
.fn-body-cols{grid-template-columns:minmax(0,1.9fr) minmax(0,1fr);gap:18px}
@media(max-width:1000px){.fn-body-cols{grid-template-columns:1fr}}
.fn-main{gap:0;min-width:0}
.fn-asides{gap:11px;min-width:0}

.code-block{white-space:pre-wrap;word-break:normal;overflow-wrap:anywhere;overflow-x:auto;
      font-size:11.5px;line-height:1.62;padding:13px 16px;border-radius:9px;margin:0}

.ba{margin:16px 0 0}
.ba .now h5::before{content:'⚠';font-size:11px;line-height:1}
.ba .nxt h5::before{content:'✓';font-size:11px;line-height:1}
.ba code{overflow-wrap:anywhere}
.ba strong{font-weight:650}

/* asides realigned onto the callout tokens */
.aside{border:1px solid #E2E8F0;border-radius:10px;padding:13px 16px;font-size:12.5px;
      line-height:1.65;background:#F8FAFC;color:#334155}
.aside.info{background:#EFF6FF;border-color:#BFDBFE;color:#1E3A8A}
.aside.warn{background:#FFFBEB;border-color:#FDE68A;color:#78350F}
.aside.helper{background:#EEF2FF;border-color:#C7D2FE;color:#3730A3}
.aside-title{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
      margin-bottom:7px}
.aside.info .aside-title{color:#1D4ED8}
.aside.warn .aside-title{color:#B45309}
.aside.helper .aside-title{color:#4F46E5}
.aside code{background:rgba(255,255,255,.75);border:1px solid rgba(0,0,0,.07);padding:1px 5px;
      border-radius:4px;font-size:11px;overflow-wrap:anywhere;word-break:normal}
.aside strong{font-weight:650}

/* footer prev/next */
.page-footer-nav a.nx{margin-left:auto}

/* page-specific blocks kept, retuned to the new tokens */
.overview-mini{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:16px 18px;
      margin-bottom:20px;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.overview-mini-title{font-size:10.5px;letter-spacing:.8px;color:#94A3B8}
.overview-chain{flex-wrap:wrap;gap:8px}
.overview-chip{border-radius:9px;border:1px solid #E2E8F0}
.box{border-radius:10px;border:1px solid #E2E8F0;border-left-width:3px}
.cascade{background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:13px 15px;margin:12px 0}
.cascade-title{font-size:10.5px;letter-spacing:.7px;color:#B45309}
.cascade-step{border-radius:8px;border:1px solid #FDE68A;background:#fff;padding:7px 10px;margin-bottom:6px}
.cascade-num{border-radius:7px;width:22px;height:22px;background:#B45309}
.nested-flow{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:13px 15px;margin:12px 0}
.nested-flow-title{font-size:10.5px;letter-spacing:.7px;color:#047857}
.field-table{border-collapse:separate;border-spacing:0;background:#fff;border:1px solid #E2E8F0;
      border-radius:10px;overflow:hidden;font-size:12px;margin:12px 0}
.field-table th{background:#0F172A;color:#fff;font-size:10px;letter-spacing:.6px;
      padding:9px 12px;border-bottom:0}
.field-table td{padding:9px 12px;border-bottom:1px solid #F1F5F9;color:#334155}
.field-table tr:last-child td{border-bottom:0}
.note{border-radius:10px;border:1px solid #FDE68A;border-left-width:1px;background:#FFFBEB;
      padding:13px 16px;color:#78350F}
.note.info{border-color:#BFDBFE;background:#EFF6FF;color:#1E3A8A}
"""

RE_HEADER = re.compile(
    r'[ \t]*<div class="page-header">(.*?)\s*(<span data-en=.*?</span>)</div>\n'
    r'[ \t]*<div class="page-sub">(.*?)</div>\n'
    r'[ \t]*<div class="topic-nav">(.*?)</div>\n',
    re.S)

RE_FOOTER = re.compile(r'[ \t]*<div class="page-nav">(.*?)</div>\n', re.S)


def build_hero(m):
    ico, title, sub, links = m.group(1), m.group(2), m.group(3), m.group(4)
    return (
        '  <div class="hero">\n'
        '    <div class="kicker"><span class="ico">%s</span></div>\n'
        '    <h1>%s</h1>\n'
        '    <div class="goal">%s</div>\n'
        '    <div class="hero-links">%s</div>\n'
        '  </div>\n' % (ico, title, sub, links))


def build_footer(m):
    inner = m.group(1)
    # drop the .back-btn skin; .page-footer-nav a supplies it
    inner = inner.replace(' class="back-btn"', '')
    anchors = re.findall(r'<a\b[^>]*>.*?</a>', inner, re.S)
    if len(anchors) == 1 and '→' in anchors[0]:
        inner = inner.replace(anchors[0], anchors[0].replace('<a ', '<a class="nx" ', 1))
    return '  <div class="page-footer-nav">%s</div>\n' % inner


def convert(path):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('</style>\n', 1)
    title = head.split('<style>', 1)[0]

    new_style = '<style>\n%s\n%s\n%s</style>\n' % (BASE, EXTRA_CSS, FASE_CSS)

    body, n1 = RE_HEADER.subn(build_hero, body, count=1)
    assert n1 == 1, 'header block not matched in %s' % path
    body, n2 = RE_FOOTER.subn(build_footer, body, count=1)
    assert n2 == 1, 'footer block not matched in %s' % path

    open(path, 'w', encoding='utf-8').write(title + new_style + body)
    return n1, n2


if __name__ == '__main__':
    for f in FILES:
        convert(DIR + f)
        print('realigned', f)
