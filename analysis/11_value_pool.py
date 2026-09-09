"""Sub-module K: the prize, in rupees, which this report had never once stated.

Every headline in this report is a share, a margin or a basis point. Not one is a
sum of money. A reader can follow the whole argument and still not know whether the
thing being argued about is worth a hundred crore or a hundred thousand.

Nothing new is fetched. Every input was already committed: national merchant value
and the incentive actually paid from `upi_incentive`, the merchant shares from the
KPI layer, and what listed operators actually earn from `psp_financials`. The gap
was never data. It was that no module multiplied a rate by a base.

Two things are refused here.

The first is a take rate. Dividing any operator's revenue by national UPI volume
would cross perimeters that do not line up, which rule 12 forbids and which
sub-module J already refuses for the same reason.

The second is a point estimate for the fiscal ask. `pov-rail-cost` recommends
indexing the state's outlay to merchant volume and never sizes it. Sizing it needs
a full-year merchant base for a year whose published base covers ten months. So it
is published as a RANGE: the low end treats the ten-month figure as if it were the
year, which understates, and the high end scales it pro rata, which assumes twelve
flat months. The true number is between them and this module does not pretend to
know where.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-value-pool"
# Rates the exhibit prices the leg at. 30 is the ceiling NPCI permits on merchant
# UPI and has set to zero by statute; 15 is the incentive's own statutory rate.
RATES_BPS = [10, 15, 30, 50]
FULL_YEAR_MONTHS = 12


def main() -> None:
    banner("Sub-module K: the pool that does not exist")
    inc = load("upi_incentive")
    psp = load("psp_financials")
    hero = load_json("upi_monetisation")

    actual = inc[inc.effective_bps.notna()]
    last = actual.iloc[-1]
    rate_bps = float(last.effective_bps)
    base_lakh_cr = float(last.p2m_lakh_cr)
    paid_cr = float(last.payout_cr)

    # A pool is a rate times a base. Both sides are published; only the
    # multiplication was missing.
    pool = [{"rate_bps": b,
             "pool_cr": round(base_lakh_cr * 1e12 * b / 10_000 / 1e7)}
            for b in RATES_BPS]
    permitted = next(p for p in pool if p["rate_bps"] == 30)

    rail = psp[psp.model == "Transactions"].sort_values("fy_end").iloc[-1]
    rail_rev_cr = float(rail.revenue_cr)
    times_rail = permitted["pool_cr"] / rail_rev_cr

    write_json("chart_value_pool", {
        "note": "The merchant leg priced at each rate, against what the state actually "
                "pays to keep it at zero and what the largest listed operator earns in "
                "total. Every bar is a rate times a published base; nothing is modelled.",
        "fy": last.fy,
        "base_lakh_cr": base_lakh_cr,
        # One records list, so the exhibit downloads as one file. A reader comparing
        # a hypothetical pool with an actual figure wants them in the same table.
        "rows": [
            *[{"label": f"{p['rate_bps']}bps", "value_cr": p["pool_cr"],
               "kind": "hypothetical", "rate_bps": p["rate_bps"]} for p in pool],
            {"label": f"Paid by the state, FY{last.fy}", "value_cr": round(paid_cr),
             "kind": "actual", "rate_bps": None},
            {"label": f"{rail.company} total revenue, FY{rail.fy}",
             "value_cr": round(rail_rev_cr), "kind": "actual", "rate_bps": None},
        ],
        "permitted_bps": 30,
        "permitted_pool_cr": permitted["pool_cr"],
        "times_rail_revenue": round(times_rail, 2),
    })

    # --- The fiscal ask pov-rail-cost names and never prints
    budget = inc[inc.effective_bps.isna()]
    ask = None
    if len(budget):
        b = budget.iloc[0]
        months = int(b.months)
        base_low = float(b.p2m_lakh_cr)
        # Rule 12: a ten-month base is not a year. Neither reading is right, so both
        # are published and the answer is stated as lying between them.
        base_high = base_low * FULL_YEAR_MONTHS / months if months < FULL_YEAR_MONTHS else base_low
        to_cr = lambda base: round(base * 1e12 * rate_bps / 10_000 / 1e7)
        ask = {"fy": b.fy, "months": months,
               "appropriated_cr": round(float(b.payout_cr)),
               "hold_rate_bps": rate_bps,
               "low_cr": to_cr(base_low), "high_cr": to_cr(base_high)}
        ask["gap_low_cr"] = ask["low_cr"] - ask["appropriated_cr"]
        ask["gap_high_cr"] = ask["high_cr"] - ask["appropriated_cr"]
        # A records list as well as the scalars: the exhibit CSV generator handles
        # tables, and refuses a bare dict rather than inventing a shape for it.
        ask_rows = [
            {"reading": f"Published base as is ({months} months)", "cost_cr": ask["low_cr"],
             "gap_to_appropriation_cr": ask["gap_low_cr"]},
            {"reading": "Base scaled pro rata to twelve months", "cost_cr": ask["high_cr"],
             "gap_to_appropriation_cr": ask["gap_high_cr"]},
            {"reading": f"Actually appropriated FY{b.fy}", "cost_cr": ask["appropriated_cr"],
             "gap_to_appropriation_cr": 0},
        ]
        write_json("chart_fiscal_ask", {
            "readings": ask_rows,
            "note": f"What holding {rate_bps:.2f}bps would cost in FY{b.fy}, against what "
                    f"was appropriated. A range, not a point: the published merchant base "
                    f"for that year covers {months} months, so the low end treats it as a "
                    "year and the high end scales it pro rata.",
            **ask,
        })

    ask_block = ""
    if ask:
        ask_block = f"""

**3. The state's own stated target has a price, and nobody has printed it.**
Sub-module B recommends indexing the outlay to merchant volume so the effective rate
stops falling by arithmetic. Holding {rate_bps:.2f}bps in FY{ask['fy']} costs between
**{inr(ask['low_cr'] * 1e7)} and {inr(ask['high_cr'] * 1e7)}**, against
{inr(ask['appropriated_cr'] * 1e7)} appropriated: a fiscal ask of roughly
{inr(ask['gap_low_cr'] * 1e7)} to {inr(ask['gap_high_cr'] * 1e7)}. It is a range rather
than a figure because the published merchant base for that year covers {ask['months']}
months, and a ten-month base annualised is an assumption, not a measurement."""

    body = f"""
## The answer

This report has never once said how much money is at stake. It says the merchant leg
carries {pct(hero["merchant_volume_share"])} of transactions and earns nothing, that the
state pays {rate_bps:.2f} basis points to hold it there, and that distribution earns
wider margins than transactions. All true, and none of it is a number a budget can hold.

Here it is. Priced at the **{permitted['rate_bps']} basis points NPCI itself permits on
merchant UPI**, the leg would generate **{inr(permitted['pool_cr'] * 1e7)} a year** on
FY{last.fy}'s national merchant value of Rs {base_lakh_cr:.1f} lakh crore. That is
**{times_rail:.1f} times the entire revenue** of {rail.company}, India's largest listed
payments company, across all of its business lines. The state replaces it with
{inr(paid_cr * 1e7)}, which is {pct(paid_cr / permitted['pool_cr'])} of it.

The foregone pool is not a rounding error against the industry. It is larger than the
industry.

## Three supporting arguments

**1. The gap between the permitted rate and the charged rate is the whole market.**
NPCI permits {permitted['rate_bps']}bps and statute sets it to zero, so the distance
between them is not a pricing decision any operator can make. At {RATES_BPS[0]}bps the
leg would still produce {inr(pool[0]['pool_cr'] * 1e7)}, comfortably more than
{rail.company} earns today. No operator is failing to capture this. It is not available
to capture.

**2. What the state pays is not a substitute for the price, and was never sized as one.**
{inr(paid_cr * 1e7)} against a {permitted['rate_bps']}bps pool of
{inr(permitted['pool_cr'] * 1e7)} means the subsidy stands in for about
{pct(paid_cr / permitted['pool_cr'], 0)} of the foregone rate. Sub-module B shows that
share falling every year without a decision. An operator modelling the incentive as
revenue is modelling {pct(paid_cr / permitted['pool_cr'], 0)} of a price that does not
exist, on an appropriation that is shrinking.{ask_block}

## So what

- **For an operator:** the number that matters is not the pool, it is that the pool is
  unavailable. Size the distribution opportunity against
  {inr(rail_rev_cr * 1e7)}, what the largest listed operator actually earns, not against
  {inr(permitted['pool_cr'] * 1e7)}, which is what the transaction would earn in a country
  that priced it.
- **For an investor:** any model whose upside depends on MDR returning is underwriting a
  {inr(permitted['pool_cr'] * 1e7)} policy reversal. State that as the size of the bet.
- **For a policymaker:** the choice has a price and now it has a figure. Zero MDR moves
  roughly {inr(permitted['pool_cr'] * 1e7)} a year from acquirers to merchants and
  consumers, and the state buys back a fraction of it.

## Method and its limits

Every figure above is a published rate multiplied by a published base. National merchant
value and the incentive paid are the PIB tables sub-module B already uses; the operator
revenue is the filed account sub-module J already uses. Nothing is modelled and no new
source is introduced.

What this is not. It is **not a revenue forecast**: it prices a leg at rates that are not
charged, to show the size of what the statute forgoes, and an MDR actually introduced
would change behaviour, shift volume and not simply multiply out. It is **not a take
rate**: no operator's revenue is divided by national volume anywhere here, because those
perimeters do not line up. And the fiscal ask is a **range rather than a figure**,
because the merchant base published for that year covers ten months and annualising it
would be an assumption presented as a measurement.
"""

    write_memo(
        MEMO,
        "The leg that earns nothing would be worth more than the industry that runs it",
        body,
        sources=[
            "PIB, Ministry of Finance: national UPI value split and incentive paid",
            "Filed annual accounts via Yahoo Finance, for what a listed operator earns",
            "PhonePe Pulse, for the merchant share of transactions",
        ],
    )
    print(f"   FY{last.fy}: merchant base Rs {base_lakh_cr:.1f} lakh cr")
    for p in pool:
        print(f"     {p['rate_bps']:>2}bps -> Rs {p['pool_cr']:>7,}cr")
    print(f"   permitted-rate pool is {times_rail:.1f}x {rail.company}'s "
          f"Rs {rail_rev_cr:,.0f}cr total revenue")
    if ask:
        print(f"   fiscal ask to hold {rate_bps:.2f}bps in FY{ask['fy']}: "
              f"Rs {ask['gap_low_cr']:,}cr to Rs {ask['gap_high_cr']:,}cr")


if __name__ == "__main__":
    main()
