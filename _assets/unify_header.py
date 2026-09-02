"""Inject the shared 4-tab doc-nav header into every sub-page.

Goal: whether you're on a main doc, an auxiliary doc, a passo detail,
a timeline task, a complemento phase, or an epic doc, the top of the
page shows the same 4 tabs (Current architecture / v2 architecture /
Plan as tasks / Timeline) and the same language switcher.

Existing page-specific nav (breadcrumb, back-btn, step-badge) is kept
below the doc-nav. Duplicate lang-sw blocks are stripped so there's
only one language switcher per page.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build_doc_nav(prefix: str, active: str) -> str:
    """Return the shared doc-nav HTML with correct href prefix."""

    def tab(href: str, en: str, pt: str, key: str) -> str:
        active_cls = " is-active" if key == active else ""
        return (
            f'<a href="{prefix}{href}" class="doc-tab{active_cls}">'
            f'<span data-en="{en}" data-pt="{pt}">{en}</span></a>'
        )

    tabs = [
        tab("index.html", "Current architecture", "Arquitetura atual", "index"),
        tab("arquitetura-v2.html", "v2 architecture", "Arquitetura v2", "v2"),
        tab("arquitetura-v2-complemento.html", "Plan as tasks", "Plano em tarefas", "plan"),
        tab("timeline/index.html", "Timeline", "Timeline", "timeline"),
        tab("progresso-refatoracao.html", "Progress", "Progresso", "progress"),
    ]

    return (
        '<div class="doc-nav">\n'
        '  <nav class="doc-tabs" aria-label="Documentation sections">\n'
        + "\n".join(f"    {t}" for t in tabs)
        + "\n"
        '  </nav>\n'
        '  <div class="lang-sw" role="group" aria-label="Language">\n'
        '    <button type="button" data-lang="en" aria-pressed="true">EN-US</button>\n'
        '    <button type="button" data-lang="pt" aria-pressed="false">PT-BR</button>\n'
        '  </div>\n'
        '</div>\n'
    )


# --------------------------------------------------------------
# Header removal (existing doc-nav) and lang-sw stripping.
# --------------------------------------------------------------

# Match the entire existing <div class="doc-nav">...</div> block.
DOCNAV_RE = re.compile(
    r"<div\s+class=\"doc-nav\">.*?</div>\s*(?:\n\s*)?</div>",
    re.DOTALL | re.IGNORECASE,
)
# Simpler catch-all in case the closing tag structure differs.
DOCNAV_LOOSE_RE = re.compile(
    r"<div\s+class=\"doc-nav\">(?:(?!</div>\s*(?:<div|<h1|<h2|<nav|<body|<main)).)*?</div>\s*(?:</div>|</nav>)?",
    re.DOTALL | re.IGNORECASE,
)

# Match standalone <div class="lang-sw" ...>...</div> blocks (any single-line or minor multi-line variant).
LANGSW_RE = re.compile(
    r'<div\s+class="lang-sw"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)


def strip_existing_docnav(text: str) -> str:
    """Remove any existing <div class=\"doc-nav\">...</div>."""

    # Try a bounded regex first — find "doc-nav" opening and count </div>s.
    out = []
    i = 0
    key = '<div class="doc-nav"'
    while True:
        idx = text.lower().find(key, i)
        if idx == -1:
            out.append(text[i:])
            break
        out.append(text[i:idx])
        # Count nested divs from this position to find the matching close.
        depth = 1
        j = text.find(">", idx) + 1
        while j < len(text) and depth > 0:
            # Consume until next < token.
            nx = text.find("<", j)
            if nx == -1:
                break
            if text[nx:nx + 5].lower() == "</div":
                depth -= 1
                end = text.find(">", nx) + 1
                if depth == 0:
                    i = end
                    break
                j = end
            elif text[nx:nx + 4].lower() == "<div":
                depth += 1
                end = text.find(">", nx) + 1
                j = end
            else:
                # Not a div token, skip past this < character.
                j = nx + 1
        else:
            # Depth never returned to zero — bail with rest of text.
            out.append(text[idx:])
            break
    return "".join(out)


def strip_standalone_langsw(text: str) -> str:
    return LANGSW_RE.sub("", text)


# --------------------------------------------------------------
# Insertion point
# --------------------------------------------------------------

INSERT_ANCHORS = [
    # Prefer to place the doc-nav right after <div class="container">
    (re.compile(r'<div\s+class="container"[^>]*>', re.IGNORECASE), "after"),
    # Otherwise, immediately after <body> (open tag)
    (re.compile(r"<body[^>]*>", re.IGNORECASE), "after"),
]


def insert_doc_nav(text: str, doc_nav_html: str) -> str:
    for anchor_re, mode in INSERT_ANCHORS:
        m = anchor_re.search(text)
        if m:
            end = m.end()
            # Skip trailing whitespace so the doc-nav lands on its own line.
            while end < len(text) and text[end] in " \t":
                end += 1
            # Ensure a preceding newline.
            prefix = "\n" if end > 0 and text[end - 1] != "\n" else ""
            return text[:end] + prefix + doc_nav_html + text[end:]
    # Fragment file — insert at top after any <link>/<title> block.
    m = re.search(r"</link>|<title[^>]*>.*?</title>|<link[^>]*>", text, re.IGNORECASE | re.DOTALL)
    if m:
        pos = m.end()
        # Also skip subsequent <link> tags.
        rest = text[pos:]
        add_re = re.compile(r"^\s*<link[^>]*>", re.IGNORECASE)
        while True:
            mm = add_re.match(rest)
            if not mm:
                break
            pos += mm.end()
            rest = text[pos:]
        return text[:pos] + "\n" + doc_nav_html + text[pos:]
    # Absolute fallback.
    return doc_nav_html + text


# --------------------------------------------------------------
# Per-file processing
# --------------------------------------------------------------

def process(path: Path, prefix: str, active: str) -> str:
    text = path.read_text(encoding="utf-8")

    # Remove existing doc-nav (we'll reinsert a canonical one).
    text = strip_existing_docnav(text)

    # Remove standalone lang-sw blocks (the new one is inside doc-nav).
    text = strip_standalone_langsw(text)

    # Insert canonical doc-nav.
    doc_nav = build_doc_nav(prefix=prefix, active=active)
    text = insert_doc_nav(text, doc_nav)

    path.write_text(text, encoding="utf-8")
    return "rewrote"


# --------------------------------------------------------------
# File groups
# --------------------------------------------------------------

def main() -> None:
    groups = [
        # (glob, prefix, active) — 'active' matches build_doc_nav keys.
        (["arquitetura-v2.html"], "", "v2"),
        (["arquitetura-v2-complemento.html"], "", "plan"),
        (["index.html"], "", "index"),
        (["progresso-refatoracao.html"], "", "progress"),
        (["algoritmo-dag.html", "validacao-dag.html", "endpoint-api-v2.html", "flow-version-atual.html"], "", "v2"),
        (list(ROOT.glob("passos/*.html")), "../", "index"),
        (list(ROOT.glob("complemento/*.html")), "../", "plan"),
        (list(ROOT.glob("timeline/*.html")), "../", "timeline"),
        (list(ROOT.glob("worker-flow-execution-epic/*.html")), "../", "plan"),
    ]

    # timeline/index.html should keep timeline as active but use ../
    # (already handled above by treating timeline/index.html like other timeline files)

    total = 0
    for spec, prefix, active in groups:
        for entry in spec:
            if isinstance(entry, str):
                p = ROOT / entry
            else:
                p = entry
            if not p.exists():
                continue
            status = process(p, prefix=prefix, active=active)
            total += 1
            print(f"[{status}] {p.relative_to(ROOT)}  (prefix='{prefix}', active='{active}')")
    print(f"\n--- total: {total} files ---")


if __name__ == "__main__":
    main()
