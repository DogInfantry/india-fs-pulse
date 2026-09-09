"""The repository's own claims, checked. Run with `python run.py check`.

Every fetcher validates its input and every module computes rather than asserts, but
nothing until now checked the properties the project *publishes about itself*. These
are the ones a refresh can quietly break, each written because it has either bitten
this repo already or guards a rule that has.

Not a test framework and not a suite. Plain asserts, one file, exits non-zero with the
offending values named. The point is that `run.py check` fails loudly in CI before a
drifted artefact reaches the site.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSIGHTS = ROOT / "insights"
SITE_DATA = ROOT / "site" / "src" / "data"
PUBLIC_DATA = ROOT / "site" / "public" / "data"
PROCESSED = ROOT / "data-pipeline" / "data" / "processed"
INDEX = ROOT / "site" / "src" / "pages" / "index.astro"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"   {'ok  ' if ok else 'FAIL'} {name}" + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def rule_11() -> None:
    """No em dashes, no ' - ' joining clauses. The memos are REGENERATED, so a
    generator that reintroduces one ships it on every future run."""
    bad = []
    for path in sorted(INSIGHTS.glob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"[—–]", line) or re.search(r"\S - \S", line):
                bad.append(f"{path.name}:{n}")
    check("rule 11: no dashes as punctuation in any generated memo", not bad, ", ".join(bad[:5]))


def downloads_resolve() -> None:
    """Every download link on the page must point at a file that exists and has rows.
    A link to nothing is worse than no link, because the claim is reproducibility."""
    hrefs = re.findall(r'download="/data/([^"]+\.csv)"', INDEX.read_text(encoding="utf-8"))
    missing = [h for h in hrefs if not (PUBLIC_DATA / h).exists()]
    empty = [h for h in hrefs
             if (PUBLIC_DATA / h).exists()
             and len((PUBLIC_DATA / h).read_text(encoding="utf-8").strip().splitlines()) < 2]
    check(f"every one of {len(hrefs)} exhibit downloads resolves", not missing, ", ".join(missing))
    check("no exhibit download is header-only", not empty, ", ".join(empty))


def meta_matches_tree() -> None:
    """The footer publishes these counts. They are computed, but only on a DATA run,
    so a fetcher added without one leaves the site understating the pipeline."""
    meta = json.loads((SITE_DATA / "pipeline_meta.json").read_text(encoding="utf-8"))
    fetchers = len(list((ROOT / "data-pipeline" / "fetch").glob("fetch_*.py")))
    modules = len([p for p in (ROOT / "analysis").glob("*.py") if p.stem[0].isdigit()])
    datasets = len(list(PROCESSED.glob("*.csv")))
    check("footer fetcher count matches the tree", meta["fetchers"] == fetchers,
          f"meta {meta['fetchers']} vs {fetchers} on disk; run `python run.py data`")
    check("footer module count matches the tree", meta["analysis_modules"] == modules,
          f"meta {meta['analysis_modules']} vs {modules} on disk; run `python run.py data`")
    check("footer dataset count matches the tree", meta["datasets"] == datasets,
          f"meta {meta['datasets']} vs {datasets} on disk; run `python run.py data`")


def memos_are_reachable() -> None:
    """index.astro throws at build for a memo with no card. This catches the reverse:
    a card pointing at a memo the analysis layer no longer writes."""
    index = INDEX.read_text(encoding="utf-8")
    carded = set(re.findall(r"^\s*'([a-z0-9-]+)':\s*'[^']+',\s*$", index, re.M))
    written = {p.stem for p in INSIGHTS.glob("*.md")}
    orphan = sorted(carded - written)
    check("no memo card points at a memo that is no longer generated", not orphan,
          ", ".join(orphan))


def provenance_is_complete() -> None:
    """Rule 2: every figure traces to a source URL and an access date."""
    ledger = json.loads((PROCESSED / "_provenance.json").read_text(encoding="utf-8"))
    thin = [k for k, v in ledger.items()
            if not v.get("url") or not v.get("publisher") or not v.get("accessed")]
    check(f"all {len(ledger)} provenance entries carry url, publisher and date", not thin,
          ", ".join(thin))


def no_fabricated_zeros() -> None:
    """Rule 1: a gap stays a gap. A series JSON that carries nulls must still carry
    them after any change to the writer, so a zero cannot quietly replace an absence."""
    seen_null = []
    for path in SITE_DATA.glob("chart_*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(payload)
        if "null" in blob:
            seen_null.append(path.stem)
    # Not an equality check: this asserts the convention is alive somewhere, so a
    # refactor that null-fills everything to zero is visible rather than silent.
    check("null observations survive into the chart JSON", bool(seen_null),
          "no chart carries a null; a gap may have been zero-filled")


def margins_agree_across_memos() -> None:
    """One datum, one value. Two memos quoted Paytm's net margin as 7% and 6.8%,
    both computed but rendered at different precisions, which reads as two figures.
    Any "N% net margin" in a memo must match a margin actually in psp_financials."""
    import csv
    path = PROCESSED / "psp_financials.csv"
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        known = {round(float(r["net_margin_pct"]), 1)
                 for r in csv.DictReader(fh) if r.get("net_margin_pct")}
    bad = []
    for memo in sorted(INSIGHTS.glob("*.md")):
        for quoted in re.findall(r"(-?\d+(?:\.\d+)?)% net margin",
                                 memo.read_text(encoding="utf-8")):
            if round(float(quoted), 1) not in known:
                bad.append(f"{memo.name} says {quoted}%")
    check("every net margin quoted in a memo matches a computed one", not bad,
          "; ".join(bad) + f"  (computed: {sorted(known)})")


def main() -> None:
    print("\n-- Checking what this repository claims about itself")
    rule_11()
    downloads_resolve()
    meta_matches_tree()
    memos_are_reachable()
    margins_agree_across_memos()
    provenance_is_complete()
    no_fabricated_zeros()
    if failures:
        sys.exit(f"\n{len(failures)} invariant(s) failed:\n  " + "\n  ".join(failures))
    print("   all invariants hold")


if __name__ == "__main__":
    main()
