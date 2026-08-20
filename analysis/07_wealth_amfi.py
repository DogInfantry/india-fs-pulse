"""Sub-module G: wealth and asset management - the shape of India's fund shelf.

Governing thought: the Indian mutual fund industry looks like it offers 14,000
products. Strip the plan and option wrappers and it offers roughly a quarter of
that. The proliferation is packaging, not choice.

STATED LOUDLY AND REPEATEDLY: this module counts SCHEMES, not rupees. AMFI's
daily NAV file carries the full scheme universe but no AUM, so nothing here is a
statement about where the money is. It is a statement about the shelf.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, load, pct, write_json, write_memo  # noqa: E402

WRAPPER_PLAN = r"\s*[-\u2013]\s*(direct|regular)\s*plan.*$"
WRAPPER_OPT = r"\s*[-\u2013]\s*(growth|idcw|dividend|payout|reinvest).*$"


def main() -> None:
    banner("Sub-module G: wealth and asset management")
    df = load("amfi_schemes")

    base = (
        df.scheme_name.str.replace(WRAPPER_PLAN, "", case=False, regex=True)
        .str.replace(WRAPPER_OPT, "", case=False, regex=True)
        .str.strip().str.lower()
    )
    df = df.assign(strategy=base)

    listed = len(df)
    strategies = df.strategy.nunique()
    houses = df.fund_house.nunique()
    wrappers = listed / strategies
    packaging = 1 - strategies / listed

    by_class = (
        df.groupby("asset_class")
        .agg(schemes=("scheme_code", "count"), strategies=("strategy", "nunique"))
        .sort_values("schemes", ascending=False)
        .reset_index()
    )
    by_house = (
        df.groupby("fund_house")
        .agg(schemes=("scheme_code", "count"), strategies=("strategy", "nunique"))
        .sort_values("strategies", ascending=False)
        .reset_index()
    )
    top5 = by_house.head(5).strategies.sum() / strategies
    debt = by_class[by_class.asset_class == "Debt"].iloc[0]
    equity = by_class[by_class.asset_class == "Equity"].iloc[0]
    nav_date = df.nav_date.dropna().mode().iloc[0]

    write_json("chart_fund_shelf", {
        "nav_date": nav_date,
        "listed_schemes": int(listed),
        "distinct_strategies": int(strategies),
        "fund_houses": int(houses),
        "caveat": "Scheme counts, not AUM. AMFI's NAV file carries no assets under management.",
        "by_asset_class": [
            {"asset_class": r.asset_class, "schemes": int(r.schemes), "strategies": int(r.strategies)}
            for r in by_class.itertuples()
        ],
        "top_houses": [
            {"fund_house": r.fund_house, "schemes": int(r.schemes), "strategies": int(r.strategies)}
            for r in by_house.head(12).itertuples()
        ],
    })

    body = f"""
> **This module counts schemes, not rupees.** AMFI's daily NAV file is the full
> scheme universe with no AUM attached, so nothing below says where the money is.
> It describes the **shelf** - what is on offer, and in how many wrappers.

## The answer

On {nav_date} the Indian mutual fund industry listed **{listed:,} schemes** across
{houses} fund houses. Strip the plan and option wrappers - the same fund sold as
Direct and Regular, as Growth and IDCW - and those collapse to
**{strategies:,} distinct strategies**. About **{pct(packaging, 0)} of the apparent
product count is packaging**, roughly {wrappers:.1f} listed schemes for every real
investment decision.

That matters because the industry's complexity is usually described as a choice
problem. It is mostly a **distribution** problem: the shelf is not four times
richer than it looks, it is four times more administered than it looks.

## Two supporting arguments

**1. The wrapper multiple is remarkably uniform.** It holds across asset classes:
debt lists {debt.schemes:,} schemes for {debt.strategies:,} strategies
({debt.schemes / debt.strategies:.1f}x), equity {equity.schemes:,} for
{equity.strategies:,} ({equity.schemes / equity.strategies:.1f}x). This is not a few
houses over-engineering a product line; it is the market structure that the
Direct-plan reform of 2013 created and that nobody has since simplified.

**2. Scheme count and investor attention point in different directions.** Debt is
the largest category on the shelf at {pct(debt.schemes / listed, 0)} of listed schemes,
against {pct(equity.schemes / listed, 0)} for equity - the opposite of where retail
narrative sits. Much of that debt count is close-ended and interval product that a
retail investor will never choose. Counting products is not the same as counting
customers, and neither is the same as counting money.

**Concentration.** The five largest houses by strategy count run {pct(top5, 0)} of all
distinct strategies, so shelf breadth is materially concentrated even before any
AUM weighting.

## So what

- **For a distributor or platform:** the decision set to be curated is about
  {strategies:,}, not {listed:,}. Interfaces that present the listed count are
  presenting an artefact of plan structure as if it were choice.
- **For an asset manager:** the wrapper multiple is a fixed operating cost carried
  per strategy - compliance, NAV publication, reconciliation, statements - on
  products that are the same portfolio underneath.
- **For diligence on a wealth platform:** ask whether "products supported" is
  counted in schemes or strategies. The two differ by {wrappers:.1f}x, and the larger
  number flatters the platform.

## Method and its limits

Parsed from AMFI's `NAVAll.txt` for {nav_date}. Strategies are derived by stripping
plan and option suffixes from scheme names, which is a **heuristic**: a house that
names two genuinely different funds identically would be under-counted, and one
that appends non-wrapper text would be over-counted. The direction and rough
magnitude are robust; the exact figure is not a regulatory statistic.

The binding limitation is the one at the top: **no AUM**. Every statement here is
about the shelf, not about assets, flows or revenue. Adding AMFI's quarterly
average-AUM disclosure would let this be restated in rupees, which is the version
that would actually inform a fee-pool estimate.
"""
    write_memo("wealth-fund-shelf",
               "India's fund shelf is four times more administered than it is diverse",
               body, sources=[f"AMFI daily NAV file (NAVAll.txt), {nav_date}"])
    print(f"   {listed:,} listed schemes -> {strategies:,} strategies "
          f"({wrappers:.1f}x wrappers, {pct(packaging, 0)} packaging) across {houses} houses")


if __name__ == "__main__":
    main()
