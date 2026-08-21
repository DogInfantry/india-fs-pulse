"""FRED -> India's policy-rate spine, with no API key.

Why this matters. The banking module measures a private-vs-public NIM gap and a
five-year price divergence, but had nothing to say about the rate environment
those margins were earned in. A margin gap without the rate cycle behind it is
half an argument: margins widen and compress with the cost of money.

Why no key. FRED's JSON API requires one, and CLAUDE.md rule 5 says the whole
pipeline must run with zero environment variables. FRED also serves the same
series as CSV from its charting endpoint with no authentication at all, so that
is what is used here. A key would buy nothing this project needs.

What it actually is. IRSTCI01INM156N is India's immediate / call money interbank
rate, relayed to FRED via the OECD from RBI's own publication. RBI's DBIE portal
is an Angular application with no public REST API, so this is the open, scriptable
route to RBI-sourced rate data.

Shape verified 2026-08-21:
  observation_date,IRSTCI01INM156N
  1968-01-01,4.5000
  ...          (missing observations are ".", never interpolated)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    banner,
    expect,
    expect_columns,
    expect_nonempty,
    get_text,
    record_source,
    write_processed,
)

CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
PAGE = "https://fred.stlouisfed.org/series/{series}"
SERIES = {"IRSTCI01INM156N": "call_money_rate_pct"}

# India's call money rate has sat roughly between 3% and 15% for its whole
# recorded history. Anything outside that is a parsing failure, not a rate move.
RATE_MIN, RATE_MAX = 1.0, 25.0


def fetch(series: str, label: str) -> pd.DataFrame:
    raw = get_text(CSV.format(series=series))
    expect(raw.lstrip().lower().startswith("observation_date"),
           f"FRED {series}: unexpected header, got {raw[:60]!r}")
    df = pd.read_csv(io.StringIO(raw))
    expect_columns(df, ["observation_date", series], f"FRED {series}")
    df = df.rename(columns={"observation_date": "month", series: label})

    # FRED writes "." for a month it does not publish. Drop it; never interpolate.
    df[label] = pd.to_numeric(df[label], errors="coerce")
    gaps = int(df[label].isna().sum())
    df = df.dropna(subset=[label]).copy()
    expect_nonempty(df, f"FRED {series}", minimum=120)

    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")
    lo, hi = df[label].min(), df[label].max()
    expect(RATE_MIN <= lo and hi <= RATE_MAX,
           f"FRED {series}: rates outside [{RATE_MIN}, {RATE_MAX}] - got {lo} to {hi}")
    print(f"   {label:<22} {len(df):>4} obs  {df.month.iloc[0]} -> {df.month.iloc[-1]}  "
          f"latest {df[label].iloc[-1]:.2f}%  ({gaps} unpublished months left as gaps)")
    return df


def main() -> None:
    banner("FRED: India policy rates (no API key)")
    merged: pd.DataFrame | None = None
    for series, label in SERIES.items():
        df = fetch(series, label)
        merged = df if merged is None else merged.merge(df, on="month", how="outer")
    assert merged is not None
    merged = merged.sort_values("month").reset_index(drop=True)

    write_processed(merged, "india_rates")
    record_source(
        "india_rates",
        url=PAGE.format(series=next(iter(SERIES))),
        publisher="FRED (Federal Reserve Bank of St. Louis), series sourced from OECD / RBI",
        coverage=f"{merged.month.iloc[0]} to {merged.month.iloc[-1]}",
        rows=len(merged),
        licence="FRED terms of use; underlying series (c) OECD. Free to redistribute with attribution.",
        note="India immediate/call money interbank rate, monthly. Fetched from FRED's keyless "
             "CSV endpoint so the pipeline needs no credentials. Months FRED does not publish "
             "are dropped, never interpolated.",
    )


if __name__ == "__main__":
    main()
