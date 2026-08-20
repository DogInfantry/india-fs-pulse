"""Shared plumbing for the India FS Pulse fetchers.

Three jobs: consistent paths, loud schema validation, and automatic provenance
capture so `docs/sources.md` is generated rather than hand-maintained
(CLAUDE.md rule 2: every figure traces to a source URL and an access date).
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data-pipeline" / "data" / "raw"
PROCESSED = ROOT / "data-pipeline" / "data" / "processed"
MANUAL = ROOT / "data-pipeline" / "data" / "manual"
SITE_DATA = ROOT / "site" / "src" / "data"
PROVENANCE = PROCESSED / "_provenance.json"

UA = "india-fs-pulse/1.0 (portfolio research project; +https://github.com/)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


class SchemaError(RuntimeError):
    """Upstream changed shape. Fail loud rather than emit a silently wrong number."""


def today() -> str:
    return date.today().isoformat()


def get_json(url: str, *, timeout: int = 45, retries: int = 3, allow_404: bool = False):
    """GET JSON with linear backoff. Returns None on an allowed 404."""
    last = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 404 and allow_404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - retry anything transient
            last = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url}\n  {last}")


def get_text(url: str, *, timeout: int = 60, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url}\n  {last}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SchemaError(message)


def expect_columns(df: pd.DataFrame, cols: list[str], source: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    expect(not missing, f"{source}: expected columns {missing} missing. Got {list(df.columns)}")


def expect_nonempty(df: pd.DataFrame, source: str, minimum: int = 1) -> None:
    expect(len(df) >= minimum, f"{source}: got {len(df)} rows, expected >= {minimum}")


def write_processed(df: pd.DataFrame, name: str) -> Path:
    """Write CSV always; parquet when the wheel supports this interpreter."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    csv_path = PROCESSED / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(PROCESSED / f"{name}.parquet", index=False)
    except Exception as exc:  # noqa: BLE001 - parquet is a convenience, CSV is the contract
        print(f"   note: parquet skipped for {name} ({type(exc).__name__}); CSV is authoritative")
    print(f"   wrote {csv_path.relative_to(ROOT)}  ({len(df):,} rows x {len(df.columns)} cols)")
    return csv_path


def record_source(
    dataset: str, *, url: str, publisher: str, coverage: str, rows: int, licence: str, note: str = ""
) -> None:
    """Append to the provenance ledger that generates docs/sources.md."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ledger: dict = {}
    if PROVENANCE.exists():
        ledger = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    ledger[dataset] = {
        "url": url,
        "publisher": publisher,
        "coverage": coverage,
        "rows": rows,
        "licence": licence,
        "note": note,
        "accessed": today(),
        "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    PROVENANCE.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")


def banner(title: str) -> None:
    print(f"\n-- {title}")
