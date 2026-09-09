"""Listed Indian financial-services businesses, grouped by what they actually sell.

This report concludes that the investable business in Indian payments is
distribution rather than transactions. Module 09 showed Brazil reaches the same
structure India did, which rules out an Indian artefact. Neither shows that
distribution earns more. India has listed companies on both sides of that line and
they file audited accounts, so the claim can stop being an inference.

Four companies, chosen because each is close to a pure play on one model:

  One97 (Paytm)   transactions     the rail itself, the thing priced at zero
  PB Fintech      distribution     insurance sold on someone else's balance sheet
  Angel One       distribution     broking, the same shape in a different product
  CDSL            infrastructure   a depository, the toll that IS allowed to charge

This is a PANEL OF NAMED COMPANIES, not cohort averages. Two of the groups would
otherwise be a cohort of one, and an average of one company is not an average. The
analysis layer therefore compares named businesses and says so.

These are not like-for-like companies. Different revenue recognition, different
perimeters, different regulators. What is comparable is the SHAPE of the margin
each model produces, which is the only claim built on this.

yfinance is already a dependency here, and it throws KeyError intermittently on
healthy tickers, so the three-attempt retry from fetch_bank_stocks.py is reused
rather than reinvented: an unretried miss silently drops a company and would move
the very comparison this exists to make.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import banner, expect, record_source, write_processed  # noqa: E402

warnings.filterwarnings("ignore")
import yfinance as yf  # noqa: E402

COMPANIES = {
    "PAYTM.NS": ("One97 (Paytm)", "Transactions", "Payments rail and merchant services"),
    "POLICYBZR.NS": ("PB Fintech", "Distribution", "Insurance and credit distribution"),
    "ANGELONE.NS": ("Angel One", "Distribution", "Retail broking and distribution"),
    "CDSL.NS": ("CDSL", "Infrastructure", "Securities depository"),
}

LINES = {
    "Total Revenue": "revenue",
    "Gross Profit": "gross_profit",
    "Operating Income": "operating_income",
    "Net Income": "net_income",
}

MIN_YEARS = 3
# A net margin outside this band is an accounting artefact or a units error, not a
# business model. Widened on the loss side because Paytm ran deep losses by design.
MARGIN_MIN_PCT, MARGIN_MAX_PCT = -80.0, 70.0


def pick(frame: pd.DataFrame, label: str, col) -> float | None:
    if frame is None or frame.empty or label not in frame.index:
        return None
    value = frame.loc[label, col]
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    return None if pd.isna(value) else float(value)


def financials() -> pd.DataFrame:
    rows = []
    for ticker, (name, model, what) in COMPANIES.items():
        income = None
        try:
            for attempt in range(3):
                try:
                    income = yf.Ticker(ticker).income_stmt
                    if income is not None and not income.empty:
                        break
                except Exception:  # noqa: BLE001. Transient; re-raised on the last try
                    if attempt == 2:
                        raise
                time.sleep(1.5 * (attempt + 1))
        except Exception as exc:  # noqa: BLE001. One bad ticker must not kill the pull
            print(f"   {ticker:<14} FAILED ({type(exc).__name__}), skipped")
            continue
        if income is None or income.empty:
            print(f"   {ticker:<14} no income statement, skipped")
            continue
        for col in income.columns:
            record = {
                "ticker": ticker,
                "company": name,
                "model": model,
                "sells": what,
                "fy_end": pd.Timestamp(col).date().isoformat(),
            }
            for label, field in LINES.items():
                record[field] = pick(income, label, col)
            rows.append(record)
        print(f"   {ticker:<14} {name:<16} {len(income.columns)} fiscal years")

    df = pd.DataFrame(rows)
    expect(len(df) > 0, "no company returned an income statement")
    got = df.ticker.nunique()
    expect(got >= len(COMPANIES) - 1,
           f"only {got}/{len(COMPANIES)} companies returned financials; the comparison "
           "names specific businesses, so a missing one changes what is being claimed")

    # Revenue is the denominator of every ratio downstream. A null one would make a
    # margin null rather than wrong, but a zero would make it infinite.
    df = df[df.revenue.notna() & (df.revenue > 0)].copy()
    for ticker, n in df.groupby("ticker").fy_end.nunique().items():
        expect(n >= MIN_YEARS,
               f"{ticker} returned {n} fiscal years, fewer than the {MIN_YEARS} a trend needs")
    return df.sort_values(["model", "company", "fy_end"]).reset_index(drop=True)


def add_margins(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["revenue_cr"] = (df.revenue / 1e7).round(0)
    df["net_margin_pct"] = (100 * df.net_income / df.revenue).round(2)
    df["gross_margin_pct"] = (100 * df.gross_profit / df.revenue).round(2)
    df["operating_margin_pct"] = (100 * df.operating_income / df.revenue).round(2)
    df["fy"] = df.fy_end.str.slice(0, 4)

    margins = df.net_margin_pct.dropna()
    expect(bool(margins.between(MARGIN_MIN_PCT, MARGIN_MAX_PCT).all()),
           f"net margin outside [{MARGIN_MIN_PCT}, {MARGIN_MAX_PCT}]%: "
           f"{margins.tolist()}")
    return df[["ticker", "company", "model", "sells", "fy_end", "fy", "revenue_cr",
               "gross_margin_pct", "operating_margin_pct", "net_margin_pct"]]


def main() -> None:
    banner("yfinance: listed FS business models")
    df = add_margins(financials())
    write_processed(df, "psp_financials")

    record_source(
        "psp_financials",
        url="https://finance.yahoo.com/",
        publisher="Yahoo Finance",
        coverage=f"{df.ticker.nunique()} NSE tickers, FY{df.fy.min()} to FY{df.fy.max()}",
        rows=len(df),
        licence="Yahoo Finance terms; personal/research use",
        note="Filed annual income statements retrieved via the yfinance library, for four "
             "listed businesses grouped by what each one sells. A PANEL OF NAMED COMPANIES, "
             "not cohort averages: two of the groups hold a single company, and an average "
             "of one is not an average. The companies are not like-for-like, so only the "
             "shape of the margin each model produces is compared, never a league table.",
    )

    latest = df.sort_values("fy_end").groupby("company").tail(1).sort_values("net_margin_pct")
    print(f"\n   latest reported year, by what the business sells:")
    for r in latest.itertuples():
        print(f"     {r.model:<14} {r.company:<16} FY{r.fy}  Rs {r.revenue_cr:>6,.0f}cr  "
              f"net {r.net_margin_pct:>6.1f}%")


if __name__ == "__main__":
    main()
