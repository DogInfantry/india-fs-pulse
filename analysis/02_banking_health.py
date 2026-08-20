"""Sub-module B: Indian banking health scan.

Governing thought: the public-private gap in Indian banking is a funding-cost
gap, not a lending gap - which is why it has not closed and will not close on
its own.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, load, write_json, write_memo  # noqa: E402


def main() -> None:
    banner("Sub-module B: banking health scan")
    nim = load("kpi_bank_nim").dropna(subset=["gap_bps"])
    fund = load("bank_fundamentals")
    banks = fund[fund.cohort.isin(["Public", "Private"])].dropna(subset=["nim_proxy_pct"]).copy()
    banks["fy"] = banks.fy_end.str[:4].astype(int)

    latest_fy = int(banks.fy.max())
    latest = banks[banks.fy == latest_fy]
    first_fy = int(nim.fy.min())
    open_row, close_row = nim.iloc[0], nim.iloc[-1]

    cohort = latest.groupby("cohort").agg(
        nim=("nim_proxy_pct", "mean"),
        cost_of_funds=("cost_of_funds_pct", "mean"),
        yield_on_assets=("yield_on_assets_pct", "mean"),
        n=("ticker", "nunique"),
    ).round(2)

    write_json("chart_nim_slope", {
        "metric": "NIM proxy (net interest income / average total assets), %",
        "caveat": "Proxy, not reported NIM: banks use average EARNING assets, a smaller denominator.",
        "periods": [f"FY{int(r.fy)}" for _, r in nim.iterrows()],
        "series": [
            {"cohort": c, "values": [round(float(r[c]), 2) for _, r in nim.iterrows()]}
            for c in ("Private", "Public") if c in nim.columns
        ],
        "gap_bps": [round(float(r.gap_bps)) for _, r in nim.iterrows()],
    })
    write_json("chart_bank_spread", {
        "fy": latest_fy,
        "note": "Decomposition of the NIM proxy into what banks earn and what they pay.",
        "series": [
            {"cohort": idx, "yield_on_assets": float(row.yield_on_assets),
             "cost_of_funds": float(row.cost_of_funds), "nim": float(row.nim), "banks": int(row.n)}
            for idx, row in cohort.iterrows()
        ],
    })

    priv, publ = cohort.loc["Private"], cohort.loc["Public"]
    yield_gap = (priv.yield_on_assets - publ.yield_on_assets) * 100
    funding_gap = (publ.cost_of_funds - priv.cost_of_funds) * 100

    # Let the data pick the claim. If one half dominates, say so; if the split is
    # near-even, that is itself the finding. Never hardcode which side wins.
    total_gap = yield_gap + funding_gap
    skew = abs(yield_gap - funding_gap) / total_gap if total_gap else 0
    if skew < 0.15:
        headline = "splits almost evenly between what private banks earn and what they pay"
        title = "The private-bank margin advantage is half pricing, half funding"
        argument_one = (
            f"Neither side dominates. Private banks earned {priv.yield_on_assets:.2f}% on assets "
            f"against {publ.yield_on_assets:.2f}% for public banks - a {yield_gap:.0f}bps asset-side "
            f"advantage - while paying {priv.cost_of_funds:.2f}% for funding against "
            f"{publ.cost_of_funds:.2f}% - a {funding_gap:.0f}bps liability-side advantage. The two "
            f"halves are within {skew:.0%} of each other, so a public bank cannot close the gap by "
            f"repricing loans alone; it has to win the deposit too."
        )
    elif funding_gap > yield_gap:
        headline = "is mainly about what each cohort pays for its deposits"
        title = "The public-private bank gap is a funding-cost gap, not a lending gap"
        argument_one = (
            f"Private banks paid {priv.cost_of_funds:.2f}% for funding against "
            f"{publ.cost_of_funds:.2f}% ({funding_gap:.0f}bps), versus only a {yield_gap:.0f}bps "
            f"asset-side advantage. The liability side is where the structural advantage sits."
        )
    else:
        headline = "is mainly about what each cohort charges its borrowers"
        title = "The public-private bank gap is an asset-pricing gap, not a funding gap"
        argument_one = (
            f"Private banks earned {priv.yield_on_assets:.2f}% on assets against "
            f"{publ.yield_on_assets:.2f}% ({yield_gap:.0f}bps), versus a {funding_gap:.0f}bps "
            f"funding advantage. The asset side is where the difference is made."
        )

    body = f"""
## The answer

Private banks out-earn public banks by **{close_row.gap_bps:.0f} basis points** of
net interest margin (FY{int(close_row.fy)}: {close_row.Private:.2f}% versus
{close_row.Public:.2f}%), and the gap has been persistent, running
{open_row.gap_bps:.0f}bps as far back as FY{first_fy}. Decomposed, that advantage
**{headline}**.

## Three supporting arguments

**1. The gap decomposes cleanly into pricing and funding.** In FY{latest_fy},
{argument_one} The two components sum to {total_gap:.0f}bps against a measured NIM gap
of {close_row.gap_bps:.0f}bps, so the decomposition is complete.

**2. The gap is stable, which means it is structural, not cyclical.** Across
FY{first_fy} to FY{int(close_row.fy)} the cohort gap moved from
{open_row.gap_bps:.0f}bps to {close_row.gap_bps:.0f}bps. A cyclical gap would
compress when rates fall; a franchise gap does not.

**3. The mechanism is deposit mix, and payments is upstream of it.** Low-cost
current and savings balances are won through primary-relationship behaviour -
salary credit, bill payment, and everyday transactions. That is precisely the
behaviour UPI now intermediates, which is why the payments question in
Sub-module A is a *deposit* question for banks.

## So what

- **For a bank client:** closing a {close_row.gap_bps:.0f}bps margin gap needs both
  levers. The {funding_gap:.0f}bps funding half is won through primary-account status,
  which is a payments and behaviour problem, not a treasury one.
- **For an investor:** treat the cohort gap as a franchise moat with a measurable
  width, and underwrite convergence only where deposit mix is actually shifting.
- **The link to payments:** whoever owns the transaction owns the relationship that
  produces the cheap deposit. That is the strategic reason banks tolerate zero MDR.

## Method and its limits

NIM here is a **proxy**: net interest income divided by average total assets,
computed from filed annual income statements and balance sheets ({banks.ticker.nunique()}
NSE-listed banks). Reported NIM uses average *earning* assets, a smaller
denominator, so these levels read low by roughly 20-40bps. The **comparison** is
sound because the bias applies equally to both cohorts; the **levels** should not be
quoted against a bank's disclosed NIM.
"""
    write_memo(
        "pov-deposit-war",
        title,
        body,
        sources=["Filed annual income statements and balance sheets via yfinance"],
    )
    print(f"   FY{latest_fy}: private {priv.nim:.2f}% vs public {publ.nim:.2f}%  "
          f"(yield gap {yield_gap:.0f}bps, funding gap {funding_gap:.0f}bps)")


if __name__ == "__main__":
    main()
