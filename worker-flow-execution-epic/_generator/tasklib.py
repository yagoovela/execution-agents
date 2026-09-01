# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

import html, io, os, re
import status as _status

BASE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'base.css'), encoding='utf-8').read()

EXTRA_CSS = """
/* ---------- task page ---------- */
body{background:#F1F5F9;color:#0F172A;margin:0;padding:28px 24px 72px;line-height:1.45;
     font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.container{max-width:1500px;margin:0 auto}

.hero{background:linear-gradient(135deg,#0F172A 0%,#1E293B 60%,#312E81 100%);color:#fff;
      border-radius:16px;padding:26px 30px 24px;margin-bottom:18px;position:relative;overflow:hidden}
.hero::after{content:'';position:absolute;right:-60px;top:-60px;width:260px;height:260px;
      background:radial-gradient(circle,rgba(99,102,241,.35),transparent 70%);pointer-events:none}
.hero .kicker{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.hero .code{font-family:'SF Mono',Menlo,monospace;font-size:13px;font-weight:700;letter-spacing:1px;
      background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);color:#fff;
      padding:5px 12px;border-radius:7px}
.hero .st{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
      padding:5px 11px;border-radius:7px;border:1px solid;display:inline-flex;align-items:center;gap:6px}
.hero .st::before{content:'';width:7px;height:7px;border-radius:50%;background:currentColor}
.hero .st.st-planned{background:rgba(148,163,184,.18);border-color:rgba(203,213,225,.45);color:#CBD5E1}
.hero .st.st-blocked{background:rgba(220,38,38,.2);border-color:rgba(248,113,113,.5);color:#FCA5A5}
.hero .st.st-doing{background:rgba(59,130,246,.22);border-color:rgba(147,197,253,.5);color:#BFDBFE}
.hero .st.st-review{background:rgba(245,158,11,.22);border-color:rgba(252,211,77,.5);color:#FDE68A}
.hero .st.st-shipped{background:rgba(16,185,129,.24);border-color:rgba(110,231,183,.5);color:#A7F3D0}
.hero .st.st-dropped{background:rgba(100,116,139,.18);border-color:rgba(148,163,184,.4);color:#94A3B8;
      text-decoration:line-through}
.hero .stnote{margin-top:12px;font-size:12.5px;line-height:1.6;color:#CBD5E1;
      background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);
      border-left:3px solid #6366F1;border-radius:8px;padding:9px 13px;max-width:88ch}
.hero .stnote b{color:#fff}
.hero .wv{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
      padding:5px 11px;border-radius:7px;background:rgba(239,68,68,.22);border:1px solid rgba(248,113,113,.5);color:#FCA5A5}
.hero h1{margin:0 0 12px;font-size:29px;line-height:1.22;letter-spacing:-.6px;font-weight:700;max-width:30ch}
.hero .goal{font-size:15px;line-height:1.6;color:#CBD5E1;max-width:78ch;border-left:3px solid #6366F1;padding-left:14px}
.hero .goal b{color:#fff;font-weight:600}
.hero-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px;position:relative;z-index:2}
.hero-links a{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;
      text-decoration:none;color:#E2E8F0;background:rgba(255,255,255,.09);
      border:1px solid rgba(255,255,255,.16);padding:7px 13px;border-radius:8px}
.hero-links a:hover{background:rgba(255,255,255,.17);color:#fff}

.glance{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:20px}
.gl{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:14px 16px;
    border-top:3px solid #94A3B8;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.gl.crit{border-top-color:#DC2626}.gl.dep{border-top-color:#3B82F6}
.gl.wave{border-top-color:#8B5CF6}.gl.ship{border-top-color:#059669}
.gl .k{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#94A3B8;margin-bottom:7px}
.gl .v{font-size:16px;font-weight:700;color:#0F172A;line-height:1.25;margin-bottom:5px}
.gl .n{font-size:11.5px;color:#64748B;line-height:1.5}

.lede{background:#fff;border:1px solid #E2E8F0;border-left:4px solid #DC2626;border-radius:12px;
      padding:18px 22px;margin-bottom:22px;font-size:14.5px;line-height:1.7;color:#334155;
      box-shadow:0 1px 3px rgba(15,23,42,.05)}
.lede strong{color:#0F172A}
.lede p{margin:0 0 10px}.lede p:last-child{margin:0}

.sec-label{display:flex;align-items:center;gap:11px;margin:30px 0 14px}
.sec-label .n{width:25px;height:25px;border-radius:7px;background:#0F172A;color:#fff;flex:none;
      display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
.sec-label h2{margin:0;font-size:17px;font-weight:700;color:#0F172A;letter-spacing:-.25px}
.sec-label .rule{flex:1;height:1px;background:#E2E8F0}

.entry-table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;
      border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;font-size:12.5px;
      box-shadow:0 1px 3px rgba(15,23,42,.05);margin-bottom:8px}
.entry-table th{background:#0F172A;color:#fff;text-align:left;padding:11px 14px;font-size:10.5px;
      font-weight:700;text-transform:uppercase;letter-spacing:.6px}
.entry-table td{padding:12px 14px;border-bottom:1px solid #F1F5F9;vertical-align:top;color:#334155;line-height:1.55}
.entry-table tr:last-child td{border-bottom:0}
.entry-table tr:hover td{background:#F8FAFC}
.entry-table td.rt{font-family:'SF Mono',Menlo,monospace;font-size:11.5px;font-weight:600;color:#0F172A;white-space:nowrap}
.entry-table td.rt.lbl{font-family:inherit;font-size:12.5px;white-space:normal}
.pill{display:inline-block;padding:3px 9px;border-radius:20px;font-size:10.5px;font-weight:700;
      letter-spacing:.2px;white-space:nowrap}
.pill.no{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.pill.weak{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A}
.pill.ok{background:#D1FAE5;color:#065F46;border:1px solid #A7F3D0}

.part{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;margin-bottom:16px;
      box-shadow:0 1px 3px rgba(15,23,42,.06)}
.part-head{background:linear-gradient(to right,#0F172A,#1E293B);color:#fff;padding:14px 20px;
      display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.part-head .num{width:26px;height:26px;border-radius:7px;background:rgba(255,255,255,.15);
      border:1px solid rgba(255,255,255,.25);display:flex;align-items:center;justify-content:center;
      font-size:12px;font-weight:700;flex:none}
.part-head .t{font-size:15px;font-weight:600;letter-spacing:-.15px}
.part-head .loc{margin-left:auto;font-family:'SF Mono',Menlo,monospace;font-size:10.5px;
      color:#94A3B8;background:rgba(0,0,0,.28);padding:4px 9px;border-radius:6px}
.part-body{padding:20px 22px}
.purpose{font-size:14px;line-height:1.65;color:#0F172A;font-weight:500;
      border-left:3px solid #6366F1;padding-left:13px;margin-bottom:16px}
.part-body p{margin:0 0 12px;font-size:13.5px;line-height:1.72;color:#334155}
.part-body p:last-child{margin-bottom:0}
.part-body strong{color:#0F172A;font-weight:650}
.part-body code{background:#F1F5F9;border:1px solid #E2E8F0;padding:1.5px 5px;border-radius:4px;
      font-family:'SF Mono',Menlo,monospace;font-size:11.5px;color:#0F172A}
.part-body ul{margin:10px 0 14px;padding-left:0;list-style:none}
.part-body ul li{position:relative;padding-left:20px;margin-bottom:9px;font-size:13.5px;
      line-height:1.7;color:#334155}
.part-body ul li::before{content:'';position:absolute;left:5px;top:9px;width:6px;height:6px;
      border-radius:50%;background:#94A3B8}
.code-block{white-space:pre-wrap;word-break:break-word}

.ba{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0 4px}
@media(max-width:900px){.ba{grid-template-columns:1fr}}
.ba>div{border-radius:10px;padding:14px 16px;font-size:13px;line-height:1.65}
.ba .now{background:#FEF2F2;border:1px solid #FECACA;color:#7F1D1D}
.ba .nxt{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46}
.ba h5{margin:0 0 8px;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
      display:flex;align-items:center;gap:6px}
.ba .now h5{color:#B91C1C}.ba .nxt h5{color:#047857}
.ba code{background:rgba(255,255,255,.75);border:1px solid rgba(0,0,0,.07);padding:1px 5px;
      border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:11px}
.ba p{margin:0 0 9px;font-size:13px;line-height:1.65}
.ba p:last-child{margin:0}

.callout{border-radius:10px;padding:14px 17px;margin:15px 0 4px;font-size:13px;line-height:1.7}
.callout .ct{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;margin-bottom:7px}
.callout.decide{background:#EFF6FF;border:1px solid #BFDBFE;color:#1E3A8A}
.callout.decide .ct{color:#1D4ED8}
.callout.mig{background:#FFFBEB;border:1px solid #FDE68A;color:#78350F}
.callout.mig .ct{color:#B45309}
.callout p{margin:0 0 9px}.callout p:last-child{margin:0}
.callout code{background:rgba(255,255,255,.7);border:1px solid rgba(0,0,0,.07);padding:1px 5px;
      border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:11px}

.vcard{background:#fff;border:1px solid #FECACA;border-radius:14px;overflow:hidden;margin-bottom:16px;
      box-shadow:0 1px 3px rgba(15,23,42,.06)}
.vcard-head{background:linear-gradient(to right,#7F1D1D,#B91C1C);color:#fff;padding:13px 20px;
      font-size:15px;font-weight:600;display:flex;align-items:center;gap:10px}
.vcard-body{padding:18px 22px}
.vitem{display:grid;grid-template-columns:auto 1fr;gap:13px;padding:13px 0;border-bottom:1px solid #F1F5F9}
.vitem:first-child{padding-top:0}
.vitem:last-child{border-bottom:0;padding-bottom:0}
.vitem .vn{width:24px;height:24px;border-radius:7px;background:#FEE2E2;color:#B91C1C;flex:none;
      display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-top:1px}
.vitem.req .vn{background:#B91C1C;color:#fff}
.vitem .vt{font-size:13px;font-weight:700;color:#0F172A;margin-bottom:4px;display:flex;
      align-items:center;gap:8px;flex-wrap:wrap}
.vitem .vt .req-tag{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;
      background:#B91C1C;color:#fff;padding:2px 7px;border-radius:20px}
.vitem .vd{font-size:13px;line-height:1.68;color:#475569}
.vitem .vd code{background:#F1F5F9;border:1px solid #E2E8F0;padding:1px 5px;border-radius:4px;
      font-family:'SF Mono',Menlo,monospace;font-size:11px}
.vitem .vd strong{color:#0F172A}

.done{background:linear-gradient(135deg,#064E3B,#047857);color:#fff;border-radius:14px;
      padding:20px 24px;margin-bottom:16px}
.done .dt{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
      color:#6EE7B7;margin-bottom:10px;display:flex;align-items:center;gap:7px}
.done .dd{font-size:14.5px;line-height:1.72;color:#ECFDF5}
.done .dd strong{color:#fff;font-weight:650}
.done .dd code{background:rgba(255,255,255,.17);border:1px solid rgba(255,255,255,.28);padding:1.5px 6px;
      border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:12px;color:#fff}
.hero .goal code{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);padding:1px 5px;
      border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:12.5px;color:#fff}
.lede code{background:#F1F5F9;border:1px solid #E2E8F0;padding:1.5px 5px;border-radius:4px;
      font-family:'SF Mono',Menlo,monospace;font-size:12px;color:#0F172A}
.lede em{font-style:italic;color:#0F172A}

.filesbox{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;
      box-shadow:0 1px 3px rgba(15,23,42,.05)}
.filesbox-head{background:linear-gradient(to right,#334155,#475569);color:#fff;padding:12px 20px;
      font-size:14px;font-weight:600;display:flex;align-items:center;gap:9px}
.filesbox-body{padding:16px 20px;display:flex;flex-wrap:wrap;gap:8px}
.fchip{font-family:'SF Mono',Menlo,monospace;font-size:11.5px;background:#F8FAFC;color:#334155;
      border:1px solid #E2E8F0;border-left:3px solid #64748B;padding:7px 11px;border-radius:7px;line-height:1.4}
.fchip.new{border-left-color:#059669;background:#F0FDF4;color:#065F46}

.page-footer-nav{display:flex;justify-content:space-between;gap:12px;margin-top:26px;flex-wrap:wrap}
.page-footer-nav a{display:inline-flex;align-items:center;gap:7px;background:#fff;border:1px solid #E2E8F0;
      color:#334155;padding:11px 17px;border-radius:9px;text-decoration:none;font-size:12.5px;font-weight:600;
      box-shadow:0 1px 2px rgba(15,23,42,.05)}
.page-footer-nav a:hover{border-color:#94A3B8;color:#0F172A}
"""

def esc(t):
    return html.escape(t, quote=True)

def bi(en, pt, tag='span', cls=None, extra=''):
    """bilingual node"""
    c = ' class="%s"' % cls if cls else ''
    return '<%s%s%s data-en="%s" data-pt="%s">%s</%s>' % (
        tag, c, extra, esc(en), esc(pt), en, tag)


DECISION_CSS = """
/* ---------- decisions ---------- */
.dec{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;margin-bottom:14px;
     box-shadow:0 1px 3px rgba(15,23,42,.06)}
.dec>summary{list-style:none;cursor:pointer;padding:15px 20px;display:flex;align-items:flex-start;
     gap:13px;background:linear-gradient(to right,#1E1B4B,#312E81);color:#fff}
.dec>summary::-webkit-details-marker{display:none}
.dec>summary:hover{background:linear-gradient(to right,#312E81,#3730A3)}
.dec>summary:focus-visible{outline:2px solid #A5B4FC;outline-offset:-2px}
.dec .chev{flex:none;width:22px;height:22px;border-radius:6px;background:rgba(255,255,255,.15);
     border:1px solid rgba(255,255,255,.25);display:flex;align-items:center;justify-content:center;
     font-size:11px;transition:transform .18s ease;margin-top:1px}
.dec[open] .chev{transform:rotate(90deg)}
.dec .dq{flex:1;min-width:0}
.dec .dq .lbl{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
     color:#A5B4FC;margin-bottom:5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.dec .dq .q{font-size:15px;font-weight:600;line-height:1.45;letter-spacing:-.15px}
.dec .dq .q code{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.26);
     padding:1px 6px;border-radius:5px;font-family:'SF Mono',Menlo,monospace;font-size:13px;
     font-weight:600;color:#E0E7FF}
.dstat{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;
     padding:2.5px 8px;border-radius:20px;white-space:nowrap}
.dstat.open{background:#F59E0B;color:#451A03}
.dstat.rec{background:#38BDF8;color:#082F49}
.dstat.set{background:#34D399;color:#022C22}
.dec .dq .lbl .planid{font-family:'SF Mono',Menlo,monospace;font-size:9.5px;font-weight:700;
     letter-spacing:.3px;color:#C7D2FE;background:rgba(255,255,255,.1);
     border:1px solid rgba(255,255,255,.2);padding:2px 7px;border-radius:20px}
.dec-body{padding:18px 20px 20px;background:#FAFAFF}
.dec-intro{font-size:13px;line-height:1.7;color:#334155;margin-bottom:16px}
.dec-intro strong{color:#0F172A}
.dec-intro code{background:#EEF2FF;border:1px solid #C7D2FE;padding:1.5px 5px;border-radius:4px;
     font-family:'SF Mono',Menlo,monospace;font-size:11.5px;color:#3730A3}
.opts{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}
.opt{background:#fff;border:1px solid #E2E8F0;border-radius:11px;padding:0;overflow:hidden;
     display:flex;flex-direction:column;position:relative}
.opt.pick{border-color:#6366F1;box-shadow:0 0 0 2px rgba(99,102,241,.16)}
.opt.no{opacity:.82}
.opt-h{padding:12px 15px;display:flex;align-items:flex-start;gap:10px;background:#F8FAFC;
     border-bottom:1px solid #E2E8F0}
.opt.pick .opt-h{background:#EEF2FF;border-bottom-color:#C7D2FE}
.opt.no .opt-h{background:#FEF2F2;border-bottom-color:#FECACA}
.opt-h .ltr{width:23px;height:23px;border-radius:6px;background:#334155;color:#fff;flex:none;
     display:flex;align-items:center;justify-content:center;font-size:11.5px;font-weight:700;margin-top:1px}
.opt.pick .opt-h .ltr{background:#4F46E5}
.opt.no .opt-h .ltr{background:#B91C1C}
.opt-h .on{font-size:13.5px;font-weight:700;color:#0F172A;line-height:1.35}
.opt-h .tag{margin-left:auto;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
     padding:3px 8px;border-radius:20px;white-space:nowrap;margin-top:2px}
.opt.pick .opt-h .tag{background:#4F46E5;color:#fff}
.opt.no .opt-h .tag{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA}
.opt-b{padding:13px 15px 14px;flex:1;display:flex;flex-direction:column;gap:11px}
.opt-how{font-size:12.5px;line-height:1.6;color:#475569}
.opt-how code{background:#F1F5F9;border:1px solid #E2E8F0;padding:1px 4px;border-radius:3px;
     font-family:'SF Mono',Menlo,monospace;font-size:11px;color:#0F172A;word-break:break-all}
.opt-l{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px}
.opt-l li{position:relative;padding-left:20px;font-size:12.5px;line-height:1.55;color:#334155}
.opt-l li::before{position:absolute;left:0;top:0;font-size:12px;font-weight:700}
.opt-l li.p::before{content:'✓';color:#059669}
.opt-l li.c::before{content:'✕';color:#DC2626}
.opt-cost{margin-top:auto;display:flex;gap:7px;flex-wrap:wrap;padding-top:4px}
.cst{font-size:10px;font-weight:600;padding:4px 8px;border-radius:6px;background:#F1F5F9;
     color:#475569;border:1px solid #E2E8F0;line-height:1.3}
.cst b{font-weight:700;color:#0F172A}
.cst.hi{background:#FEF3C7;border-color:#FDE68A;color:#78350F}
.cst.hi b{color:#78350F}
.cst.lo{background:#ECFDF5;border-color:#A7F3D0;color:#065F46}
.cst.lo b{color:#065F46}
.dec-rec{margin-top:15px;background:#EEF2FF;border:1px solid #C7D2FE;border-left:4px solid #4F46E5;
     border-radius:10px;padding:14px 17px;font-size:13px;line-height:1.7;color:#312E81}
.dec-rec .rt{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
     color:#4F46E5;margin-bottom:7px}
.dec-rec strong{color:#1E1B4B}
.dec-rec code{background:rgba(255,255,255,.75);border:1px solid #C7D2FE;padding:1.5px 5px;
     border-radius:4px;font-family:'SF Mono',Menlo,monospace;font-size:11.5px}
.dec-rec p{margin:0 0 9px}.dec-rec p:last-child{margin:0}
.dec-who{margin-top:11px;display:flex;align-items:center;gap:9px;flex-wrap:wrap;
     font-size:11.5px;color:#64748B}
.dec-who .wk{font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:.5px;font-size:9.5px}
.dec-who .wv2{background:#fff;border:1px solid #E2E8F0;padding:4px 10px;border-radius:20px;font-weight:600;color:#334155}
"""

def B(pair, tag='span', cls=None, extra=''):
    if not isinstance(pair, tuple):
        pair = (pair, pair)
    en, pt = pair
    c = ' class="%s"' % cls if cls else ''
    return '<%s%s%s data-en="%s" data-pt="%s">%s</%s>' % (tag, c, extra, esc(en), esc(pt), en, tag)

def D(pair, cls=None, tag='div', extra=''):
    return B(pair, tag, cls, extra)

WAVE_PT = {0:'onda 0',1:'onda 1',2:'onda 2',3:'onda 3',4:'onda 4',5:'onda 5',6:'onda 6'}

def render(T):
    o = io.StringIO(); w = o.write
    code = T['code']
    plain = re.sub(r'<[^>]+>', '', T['title'][0])
    w('<title>%s — %s</title>\n' % (code, plain))
    w('<style>\n%s\n%s\n%s\n</style>\n' % (BASE, EXTRA_CSS, DECISION_CSS))
    w('<div class="container">\n')

    w('<div class="top-nav">')
    w('<a href="index.html" class="back-btn"><span>←</span> <span data-en="Timeline" data-pt="Timeline">Timeline</span></a>')
    w('<div class="lang-sw" role="group" aria-label="Language">'
      '<button type="button" data-lang="en" aria-pressed="true">EN-US</button>'
      '<button type="button" data-lang="pt" aria-pressed="false">PT-BR</button></div>')
    w('</div>\n')

    wv = T['wave']
    w('<div class="hero">')
    st = _status.of(code)
    slab_en, slab_pt, scls = _status.LABELS[st['state']]
    w('<div class="kicker"><span class="code">%s</span>%s%s</div>'
      % (code, B(('wave %d' % wv, WAVE_PT[wv]), cls='wv'),
         B((slab_en, slab_pt), cls='st ' + scls)))
    w(B(T['title'], tag='h1'))
    w(D(T['goal'], cls='goal'))
    if st['note'] or st['ref']:
        bits_en, bits_pt = [], []
        if st['ref']:
            bits_en.append('<b>%s</b>' % esc(st['ref'])); bits_pt.append('<b>%s</b>' % esc(st['ref']))
        if st['note']:
            bits_en.append(esc(st['note']))
            bits_pt.append(esc(st.get('note_pt') or st['note']))
        w(D((' · '.join(bits_en), ' · '.join(bits_pt)), cls='stnote'))
    w('<div class="hero-links">')
    if T.get('phase'):
        w('<a href="../complemento/%s">%s</a>' % (T['phase'][0], B(T['phase'][1])))
    w('<a href="index.html#w%d">%s</a>' % (wv, B(('Other tasks in wave %d →' % wv,
                                                  'Outras tasks da %s →' % WAVE_PT[wv]))))
    if T.get('next'):
        w('<a href="%s">%s</a>' % (T['next'][0], B(T['next'][1])))
    w('</div></div>\n')

    w('<div class="glance">')
    for cls, k, v, n in T['glance']:
        w('<div class="gl %s">%s%s%s</div>' % (cls, B(k,'div','k'), B(v,'div','v'), B(n,'div','n')))
    w('</div>\n')

    w(D(T['lede'], cls='lede') + '\n')

    for blk in T['blocks']:
        k = blk['k']
        if k == 'label':
            w('<div class="sec-label"><span class="n">%s</span>%s<span class="rule"></span></div>\n'
              % (blk['n'], B(blk['t'], tag='h2')))
        elif k == 'table':
            w('<table class="entry-table"><thead><tr>')
            for h in blk['head']:
                w('<th>%s</th>' % B(h))
            w('</tr></thead><tbody>\n')
            for row in blk['rows']:
                w('<tr>')
                for cell in row:
                    if isinstance(cell, dict):
                        if cell.get('pill'):
                            w('<td><span class="pill %s">%s</span></td>' % (cell['pill'], B(cell['t'])))
                        elif cell.get('mono'):
                            w('<td class="rt">%s</td>' % esc(cell['t']) if isinstance(cell['t'], str) else '<td class="rt">%s</td>' % B(cell['t']))
                        else:
                            w('<td class="rt lbl">%s</td>' % B(cell['t']))
                    else:
                        w('<td>%s</td>' % B(cell))
                w('</tr>\n')
            w('</tbody></table>\n')
        elif k == 'part':
            w('<div class="part"><div class="part-head">')
            w('<span class="num">%s</span>' % blk['n'])
            w('<span class="t">%s</span>' % B(blk['title']))
            if blk.get('loc'):
                lv = blk['loc']
                if isinstance(lv, tuple):
                    w(B(lv, 'span', 'loc'))
                else:
                    w('<span class="loc">%s</span>' % esc(lv))
            w('</div><div class="part-body">')
            if blk.get('purpose'):
                w(D(blk['purpose'], cls='purpose'))
            if blk.get('body'):
                w(D(blk['body']))
            if blk.get('code'):
                c = blk['code']
                w('<div class="code-block" data-en="%s" data-pt="%s">%s</div>'
                  % (esc(c[0]), esc(c[1]), esc(c[0])))
            if blk.get('list'):
                w('<ul>')
                for li in blk['list']:
                    w(B(li, tag='li'))
                w('</ul>')
            if blk.get('body2'):
                w(D(blk['body2']))
            if blk.get('ba'):
                now, nxt = blk['ba']
                w('<div class="ba">')
                w('<div class="now"><h5>⚠ %s</h5>%s</div>'
                  % (B(('How it is today','Como está hoje')), D(now, tag='p')))
                w('<div class="nxt"><h5>✓ %s</h5>%s</div>'
                  % (B(('How it will be','Como fica')), D(nxt, tag='p')))
                w('</div>')
            for kind, ct, cb in blk.get('callouts', []):
                w('<div class="callout %s">%s%s</div>' % (kind, B(ct, cls='ct'), D(cb)))
            w('</div></div>\n')
        elif k == 'decision':
            w('<details class="dec"%s><summary>' % (' open' if blk.get('open') else ''))
            w('<span class="chev">▸</span><span class="dq">')
            st = blk.get('status','open')
            stl = {'open':('Open — needs a call','Em aberto — precisa de decisão'),
                   'rec':('Recommended — confirm','Recomendada — confirmar'),
                   'set':('Settled','Decidida')}[st]
            did = blk.get('id')
            plan = blk.get('plan')
            lbl = B(('Decision %s' % did if did else 'Decision',
                     'Decisão %s' % did if did else 'Decisão'))
            if plan:
                lbl += '<span class="planid">%s</span>' % B(('PLAN %s' % plan, 'PLAN %s' % plan))
            w('<span class="lbl">%s<span class="dstat %s">%s</span></span>' % (lbl, st, B(stl)))
            w('%s</span></summary>' % B(blk['q'], cls='q'))
            w('<div class="dec-body">')
            if blk.get('intro'):
                w(D(blk['intro'], cls='dec-intro'))
            w('<div class="opts">')
            for op in blk['opts']:
                cls = 'opt' + (' pick' if op.get('pick') else '') + (' no' if op.get('no') else '')
                w('<div class="%s"><div class="opt-h"><span class="ltr">%s</span>' % (cls, op['ltr']))
                w('<span class="on">%s</span>' % B(op['name']))
                if op.get('tag'):
                    w('<span class="tag">%s</span>' % B(op['tag']))
                w('</div><div class="opt-b">')
                w(D(op['how'], cls='opt-how'))
                if op.get('pros') or op.get('cons'):
                    w('<ul class="opt-l">')
                    for p in op.get('pros', []):
                        w(B(p, tag='li', cls='p'))
                    for c in op.get('cons', []):
                        w(B(c, tag='li', cls='c'))
                    w('</ul>')
                if op.get('cost'):
                    w('<div class="opt-cost">')
                    for cc, ct in op['cost']:
                        w('<span class="cst %s">%s</span>' % (cc, B(ct)))
                    w('</div>')
                w('</div></div>')
            w('</div>')
            if blk.get('rec'):
                w('<div class="dec-rec">%s%s</div>'
                  % (B(('Our recommendation','Nossa recomendação'), cls='rt'), D(blk['rec'])))
            if blk.get('who'):
                w('<div class="dec-who"><span class="wk">%s</span>' % B(('Who decides','Quem decide')))
                for x in blk['who']:
                    w('<span class="wv2">%s</span>' % B(x))
                w('</div>')
            w('</div></details>\n')
        elif k == 'prose':
            w('<div class="lede" style="border-left-color:#6366F1">%s</div>\n' % D(blk['t']))

    w('<div class="sec-label"><span class="n">%s</span>%s<span class="rule"></span></div>\n'
      % (T.get('vnum','·'), B(('How it is proved','Como se prova'), tag='h2')))
    w('<div class="vcard"><div class="vcard-head">🔬 %s</div><div class="vcard-body">'
      % B(('Verification','Verificação')))
    for i, (req, vt, vd) in enumerate(T['verif'], 1):
        w('<div class="vitem%s"><div class="vn">%d</div><div>' % (' req' if req else '', i))
        w('<div class="vt">%s%s</div>' % (B(vt),
          ('<span class="req-tag">%s</span>' % B(('required','obrigatório'))) if req else ''))
        w(D(vd, cls='vd'))
        w('</div></div>\n')
    w('</div></div>\n')

    w('<div class="done">%s%s</div>\n'
      % (B(('✓  Done when','✓  Pronto quando'), cls='dt'), D(T['done'], cls='dd')))

    w('<div class="filesbox"><div class="filesbox-head">📂 %s</div><div class="filesbox-body">'
      % B(('Files this task touches','Arquivos que esta task toca')))
    for f, isnew in T['files']:
        w('<span class="fchip%s">%s</span>' % (' new' if isnew else '', esc(f)))
    w('</div></div>\n')

    w('<div class="page-footer-nav">')
    if T.get('prev'):
        w('<a href="%s">%s</a>' % (T['prev'][0], B(T['prev'][1])))
    else:
        w('<a href="index.html">%s</a>' % B(('← Back to the timeline','← Voltar para a timeline')))
    if T.get('next'):
        w('<a href="%s">%s</a>' % (T['next'][0], B(T['next'][1])))
    w('</div>\n</div>\n')

    w("""<script>
(function(){
  var n=document.querySelectorAll('[data-en]'),b=document.querySelectorAll('.lang-sw button');
  function apply(l){
    n.forEach(function(el){var v=el.getAttribute('data-'+l); if(v===null)return; el.innerHTML=v;});
    b.forEach(function(x){x.setAttribute('aria-pressed',String(x.getAttribute('data-lang')===l))});
    document.documentElement.lang = l==='pt' ? 'pt-BR' : 'en';
    try{localStorage.setItem('flux-lang',l)}catch(e){}
  }
  b.forEach(function(x){x.addEventListener('click',function(){apply(x.getAttribute('data-lang'))})});
  var saved=null; try{saved=localStorage.getItem('flux-lang')}catch(e){}
  apply(saved==='pt'?'pt':'en');
})();
</script>
""")
    return o.getvalue()

OUT = _EPIC + '/timeline/'

def write(T):
    p = OUT + 'task-%s.html' % T['code']
    open(p,'w',encoding='utf-8').write(render(T))
    return p
