"""Convert the .page-header + .page-sub pair to the shared .hero block
across all passos/*.html.

Before:
    <div class="page-header">
      <span class="icon">🚚</span>
      <h1>Title</h1>
    </div>
    <div class="page-sub">
      Description
    </div>

After:
    <div class="hero">
      <div class="kicker"><span class="ico">🚚</span></div>
      <h1>Title</h1>
      <div class="goal">Description</div>
    </div>

Idempotent — files already converted (no .page-header) are skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASSOS_DIR = ROOT / "passos"


PATTERN = re.compile(
    r"""
    <div\s+class="page-header">\s*
      <span\s+class="icon">(?P<icon>.+?)</span>\s*
      <h1>(?P<h1>.+?)</h1>\s*
    </div>\s*
    <div\s+class="page-sub">\s*
      (?P<goal>.+?)\s*
    </div>
    """,
    re.DOTALL | re.VERBOSE,
)


def to_hero(match: re.Match[str]) -> str:
    icon = match.group("icon").strip()
    h1 = match.group("h1").strip()
    goal = match.group("goal").strip()
    return (
        '<div class="hero">\n'
        f'    <div class="kicker"><span class="ico">{icon}</span></div>\n'
        f"    <h1>{h1}</h1>\n"
        f'    <div class="goal">{goal}</div>\n'
        "  </div>"
    )


def convert(path: Path) -> str:
    text = path.read_text(encoding="utf-8")

    if 'class="page-header"' not in text:
        return "already-converted"

    new_text, n = PATTERN.subn(to_hero, text)
    if n == 0:
        return "no-match"

    path.write_text(new_text, encoding="utf-8")
    return f"converted ({n})"


def main() -> None:
    counts: dict[str, int] = {}
    for p in sorted(PASSOS_DIR.glob("*.html")):
        status = convert(p)
        counts[status] = counts.get(status, 0) + 1
        print(f"[{status:>18}] {p.name}")

    print("\n--- totals ---")
    for k, v in sorted(counts.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
