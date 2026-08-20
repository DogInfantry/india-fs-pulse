"""Shared helpers for the analysis layer.

Analysis scripts read ONLY from data-pipeline/data/processed and site/src/data.
They never fetch, and they never hardcode a figure - every number in a memo is
interpolated from a computed value so the prose cannot drift from the data.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data-pipeline" / "data" / "processed"
SITE_DATA = ROOT / "site" / "src" / "data"
INSIGHTS = ROOT / "insights"

sys.path.insert(0, str(ROOT / "data-pipeline"))


def load(name: str) -> pd.DataFrame:
    path = PROCESSED / f"{name}.csv"
    if not path.exists():
        raise SystemExit(f"missing {path.name}. Run: python run.py data")
    return pd.read_csv(path)


def load_json(name: str) -> dict:
    path = SITE_DATA / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"missing {path.name}. Run: python run.py data")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload) -> None:
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / f"{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"   chart data -> site/src/data/{name}.json")


def write_memo(slug: str, title: str, body: str, *, sources: list[str]) -> None:
    """Write an answer-first memo. Front matter feeds the Astro content collection."""
    INSIGHTS.mkdir(parents=True, exist_ok=True)
    front = [
        "---",
        f'title: "{title}"',
        f"generated: {date.today().isoformat()}",
        "generator: analysis/" + Path(sys.argv[0]).name,
        "sources:",
        *[f"  - {s}" for s in sources],
        "---",
        "",
        "<!-- GENERATED FILE. Edit the analysis script, not this file. -->",
        "",
    ]
    (INSIGHTS / f"{slug}.md").write_text("\n".join(front) + body.strip() + "\n", encoding="utf-8")
    print(f"   memo -> insights/{slug}.md")


def inr(value: float) -> str:
    """Indian-format a rupee figure to the nearest sensible unit."""
    value = float(value)
    if abs(value) >= 1e12:
        return f"Rs {value / 1e12:,.2f} lakh crore"
    if abs(value) >= 1e7:
        return f"Rs {value / 1e7:,.0f} crore"
    return f"Rs {value:,.0f}"


def pct(value: float, dp: int = 1) -> str:
    return f"{value * 100:.{dp}f}%"


def banner(title: str) -> None:
    print(f"\n-- {title}")
