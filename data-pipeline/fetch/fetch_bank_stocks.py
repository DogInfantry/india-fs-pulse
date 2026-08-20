"""Indian bank and fintech fundamentals via yfinance.

RBI's DBIE has no clean public API, so the NIM story is built from filed income
statements instead of a ready-made series. yfinance exposes `Net Interest Income`,
`Interest Income` and `Interest Expense` for NSE-listed banks, and Total Assets
from the balance sheet - enough for a defensible NIM PROXY:

    nim_proxy = net interest income / average total assets

That is a proxy, not the reported NIM: banks compute NIM on average EARNING
assets, a smaller denominator, so this reads a little low. It is used only for
cohort COMPARISON (public vs private), where the bias is common to both.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import banner, expect, record_source, write_processed  # noqa: E402

warnings.filterwarnings("ignore")
import yfinance as yf  # noqa: E402

COHORTS = {
    "HDFCBANK.NS": ("HDFC Bank", "Private"),
    "ICICIBANK.NS": ("ICICI Bank", "Private"),
    "AXISBANK.NS": ("Axis Bank", "Private"),
    "KOTAKBANK.NS": ("Kotak Mahindra Bank", "Private"),
    "INDUSINDBK.NS": ("IndusInd Bank", "Private"),
    "SBIN.NS": ("State Bank of India", "Public"),
    "BANKBARODA.NS": ("Bank of Baroda", "Public"),
    "PNB.NS": ("Punjab National Bank", "Public"),
    "CANBK.NS": ("Canara Bank", "Public"),
    "UNIONBANK.NS": ("Union Bank of India", "Public"),
    "PAYTM.NS": ("One97 (Paytm)", "Fintech"),
}

LINES = {
    "Net Interest Income": "net_interest_income",
    "Interest Income": "interest_income",
    "Interest Expense": "interest_expense",
    "Net Income": "net_income",
    "Total Revenue": "total_revenue",
}


def pick(frame: pd.DataFrame, label: str, col) -> float | None:
    if frame is None or frame.empty or label not in frame.index:
        return None
    value = frame.loc[label, col]
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    return None if pd.isna(value) else float(value)


def fundamentals() -> pd.DataFrame:
    rows = []
    for ticker, (name, cohort) in COHORTS.items():
        try:
            handle = yf.Ticker(ticker)
            income = handle.financials
            balance = handle.balance_sheet
            if income is None or income.empty:
                print(f"   {ticker:<15} no income statement, skipped")
                continue
            for col in income.columns:
                record = {
                    "ticker": ticker,
                    "bank": name,
                    "cohort": cohort,
                    "fy_end": pd.Timestamp(col).date().isoformat(),
                }
                for label, field in LINES.items():
                    record[field] = pick(income, label, col)
                record["total_assets"] = pick(balance, "Total Assets", col) if balance is not None else None
                rows.append(record)
            print(f"   {ticker:<15} {len(income.columns)} fiscal years")
        except Exception as exc:  # noqa: BLE001 - one bad ticker must not kill the pull
            print(f"   {ticker:<15} FAILED ({type(exc).__name__}), skipped")
    df = pd.DataFrame(rows)
    expect(
        df.ticker.nunique() >= len(COHORTS) * 0.6,
        f"only {df.ticker.nunique()}/{len(COHORTS)} tickers returned fundamentals",
    )
    return df


def add_nim(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "fy_end"]).copy()
    # Average of opening and closing total assets; falls back to closing in year one.
    df["avg_total_assets"] = (
        df.groupby("ticker")["total_assets"].transform(lambda s: s.rolling(2).mean()).fillna(df["total_assets"])
    )
    df["nim_proxy_pct"] = 100 * df["net_interest_income"] / df["avg_total_assets"]
    df["cost_of_funds_pct"] = 100 * df["interest_expense"] / df["avg_total_assets"]
    df["yield_on_assets_pct"] = 100 * df["interest_income"] / df["avg_total_assets"]

    # NIM is a banking metric. Paytm is a payments company whose net interest
    # income is incidental, so the ratio is meaningless there - blank it rather
    # than publish a number that invites a wrong comparison.
    is_bank = df["cohort"].isin(["Public", "Private"])
    df.loc[~is_bank, ["nim_proxy_pct", "cost_of_funds_pct", "yield_on_assets_pct"]] = pd.NA

    plausible = df.loc[is_bank, "nim_proxy_pct"].dropna()
    expect(
        bool(((plausible > 0.2) & (plausible < 12)).all()),
        f"bank NIM proxy outside 0.2-12%: {plausible.round(2).tolist()}",
    )
    return df


def prices() -> pd.DataFrame:
    raw = yf.download(list(COHORTS), period="5y", progress=False, auto_adjust=True)["Close"]
    expect(not raw.empty, "yfinance returned no price history")
    out = raw.reset_index().melt(id_vars="Date", var_name="ticker", value_name="close")
    out = out.dropna(subset=["close"])
    out["date"] = pd.to_datetime(out["Date"]).dt.date.astype(str)
    out["bank"] = out.ticker.map(lambda t: COHORTS[t][0])
    out["cohort"] = out.ticker.map(lambda t: COHORTS[t][1])
    print(f"   prices {out.date.min()} -> {out.date.max()}")
    return out[["date", "ticker", "bank", "cohort", "close"]]


def main() -> None:
    banner("yfinance: bank fundamentals")
    fund = add_nim(fundamentals())
    banner("yfinance: price history")
    px = prices()

    write_processed(fund, "bank_fundamentals")
    write_processed(px, "bank_prices")

    latest = fund.dropna(subset=["nim_proxy_pct"]).sort_values("fy_end").groupby("cohort").tail(3)
    print("\n   NIM proxy by cohort, latest reported years:")
    for cohort, value in latest.groupby("cohort")["nim_proxy_pct"].mean().items():
        print(f"     {cohort:<9} {value:5.2f}%")

    for name, df in [("bank_fundamentals", fund), ("bank_prices", px)]:
        record_source(
            name,
            url="https://finance.yahoo.com/",
            publisher="Yahoo Finance",
            coverage=f"{len(COHORTS)} NSE tickers",
            rows=len(df),
            licence="Yahoo Finance terms; personal/research use",
            note="Retrieved via the yfinance library. NIM here is a PROXY: net interest income / average total assets, not reported NIM.",
        )


if __name__ == "__main__":
    main()
