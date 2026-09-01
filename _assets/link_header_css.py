"""Ensure every HTML page links _assets/header.css.

Idempotent — skips files that already have the link. Inserts it right
after the i18n.css link when present, otherwise after <meta charset>,
otherwise after <title>, otherwise at the top of the file (for body
fragments without a proper <head>).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROOT_HTMLS = [
    "arquitetura-v2.html",
    "arquitetura-v2-complemento.html",
    "index.html",
    "algoritmo-dag.html",
    "validacao-dag.html",
    "endpoint-api-v2.html",
    "flow-version-atual.html",
]

SUB_GLOBS = [
    "timeline/*.html",
    "complemento/*.html",
    "passos/*.html",
    "worker-flow-execution-epic/*.html",
]

HEADER_LINK_RE = re.compile(r"<link[^>]+_assets/header\.css[^>]*>", re.IGNORECASE)
I18N_LINK_RE = re.compile(r"<link[^>]+_assets/i18n\.css[^>]*>", re.IGNORECASE)
META_CHARSET_RE = re.compile(r"<meta\s+charset[^>]*>", re.IGNORECASE)
TITLE_RE = re.compile(r"<title[^>]*>.*?</title>", re.IGNORECASE | re.DOTALL)


def link_tag(prefix: str) -> str:
    return f'<link rel="stylesheet" href="{prefix}_assets/header.css">'


def rewrite(path: Path, prefix: str) -> str:
    text = path.read_text(encoding="utf-8")

    if HEADER_LINK_RE.search(text):
        return "already-linked"

    tag = link_tag(prefix)

    # Preferred: right after the i18n.css link.
    m = I18N_LINK_RE.search(text)
    if m:
        end = m.end()
        text = text[:end] + "\n" + tag + text[end:]
        path.write_text(text, encoding="utf-8")
        return "after-i18n"

    # After <meta charset>.
    m = META_CHARSET_RE.search(text)
    if m:
        end = m.end()
        text = text[:end] + "\n" + tag + text[end:]
        path.write_text(text, encoding="utf-8")
        return "after-meta"

    # After <title>.
    m = TITLE_RE.search(text)
    if m:
        end = m.end()
        text = text[:end] + "\n" + tag + text[end:]
        path.write_text(text, encoding="utf-8")
        return "after-title"

    # Fragment file with no <head> — prepend.
    text = tag + "\n" + text
    path.write_text(text, encoding="utf-8")
    return "prepended"


def main() -> None:
    counts: dict[str, int] = {}

    for name in ROOT_HTMLS:
        p = ROOT / name
        if p.exists():
            status = rewrite(p, prefix="")
            counts[status] = counts.get(status, 0) + 1

    for pattern in SUB_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            status = rewrite(p, prefix="../")
            counts[status] = counts.get(status, 0) + 1

    print("--- totals ---")
    for k, v in sorted(counts.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
