"""Sub-module C: PE diligence simulation on Indian merchant payments.

The diligence question, deliberately open-ended:
  "A sponsor is considering a growth investment in an Indian merchant-payments
   platform. Is there an investable business model, and what would we need to
   believe?"

Framing note: rather than invent a target and its financials, this benchmarks the
market unit economics computed from PhonePe Pulse against the only listed Indian
pure-play, One97 Communications (Paytm), using its filed statements. Nothing here
is a recommendation on a security.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, load_json, pct, write_json, write_memo  # noqa: E402


def main() -> None:
    banner("Sub-module C: PE diligence simulation")
    hero = load_json("upi_monetisation")
    fund = load("bank_fundamentals")

    merchants = hero["registered_merchants"]
    gmv_per = hero["gmv_per_merchant_inr"]
    txns_per = hero["txns_per_merchant"]
    mdr = hero["mdr_scenarios_cr"]
    merchant_cat = next(c for c in hero["categories"] if c["category"] == "Retail")

    comp = fund[fund.cohort == "Fintech"].dropna(subset=["total_revenue"]).sort_values("fy_end")
    have_comp = len(comp) > 0
    comp_block = ""
    if have_comp:
        latest = comp.iloc[-1]
        comp_rev = float(latest.total_revenue)
        comp_ni = float(latest.net_income) if latest.net_income == latest.net_income else 0.0
        comp_margin = comp_ni / comp_rev
        comp_fy = str(latest.fy_end)[:4]
        verdict = "a negative" if comp_margin < 0 else "a thin"
        comp_block = (
            "\n**3. The only listed pure-play has not solved it yet.** One97 Communications "
            f"(Paytm) reported {inr(comp_rev)} of revenue in FY{comp_fy} at a "
            f"{pct(comp_margin, 0)} net margin. A sponsor cannot underwrite this deal on a "
            "'payments scale economics' thesis when the largest listed comparable, with a "
            f"decade of scale, still earns {verdict} return on the payments business itself.\n"
        )

    # Revenue per merchant per year under each MDR scenario, annualising the quarter.
    scenarios = []
    for rate, revenue_cr in mdr.items():
        annual = float(revenue_cr) * 1e7 * 4
        scenarios.append({
            "rate": rate,
            "revenue_per_merchant_yr_inr": round(annual / merchants, 1),
            "revenue_cr_yr": round(annual / 1e7),
        })

    write_json("chart_unit_economics", {
        "period": hero["period"],
        "merchants": merchants,
        "gmv_per_merchant_quarter_inr": gmv_per,
        "txns_per_merchant_quarter": txns_per,
        "scenarios": scenarios,
        "note": "Merchant-side unit economics from PhonePe Pulse. Today's MDR is 0bps.",
    })

    rows = [
        f"| {s['rate']} | {inr(s['revenue_per_merchant_yr_inr'])} | {inr(s['revenue_cr_yr'] * 1e7)} |"
        for s in scenarios if s["rate"] != "0bps"
    ]
    scenario_table = "\n".join(rows)
    at_30 = next(s for s in scenarios if s["rate"] == "30bps")["revenue_per_merchant_yr_inr"]

    body = f"""
## The recommendation

**Conditional no on a payments-fee thesis; conditional yes on a merchant-financing
thesis.** The merchant payments market is enormous and still compounding, but at
0bps MDR the payment itself is not a revenue event. An investment here has to be
underwritten as **distribution economics**: the right to lend to, and sell software
to, a merchant base, not as **transaction economics**. If the sponsor's model
depends on MDR returning, the answer is no, because that is a policy bet, not a
business plan.

## What the numbers say

| Metric ({hero['period']}) | Value |
|---|---|
| Registered merchants | {merchants:,} |
| Transactions per merchant per quarter | {txns_per:,.0f} |
| GMV per merchant per quarter | {inr(gmv_per)} |
| Merchant GMV | {merchant_cat['amount_lakh_cr']:.2f} lakh crore |
| Average merchant ticket | {inr(merchant_cat['avg_ticket_inr'])} |
| **Payment revenue at today's 0bps MDR** | **{inr(0)}** |

Annualised revenue per merchant, if an MDR existed:

| MDR | Revenue per merchant per year | Total |
|---|---|---|
{scenario_table}

## Three supporting arguments

**1. Market attractiveness is not the constraint; price is.** {merchants:,} merchants
each running {txns_per:,.0f} transactions a quarter is a distribution asset most lenders
would pay a great deal to rent. The constraint is that the transaction carries no price.

**2. The unit economics only work at the merchant level, and only with a second
product.** At 30bps: a rate that does not exist: a merchant is worth
{inr(at_30)} a year. Any working-capital product priced off the same relationship
dwarfs that. The payment is the acquisition channel; the loan is the P&L.
{comp_block}
## Red flags

- **Policy dependency.** Any model that assumes MDR returns is underwriting a
  political decision. Size the downside at 0bps forever.
- **Concentration.** The top players intermediate the large majority of volume; a
  binding 30% share cap redistributes rather than grows the pool, and could force
  uneconomic customer acquisition.
- **Credit is a different business.** The pivot to lending swaps a capital-light fee
  model for a balance-sheet, provisioning and collections business. Underwrite the
  team for the business they are becoming, not the one they built.
- **Take-rate opacity.** Reported "payments revenue" at Indian platforms blends
  MDR-bearing instruments, PPI interchange and incentives. Insist on a take-rate
  bridge by instrument before signing.

## Upside register

- **Credit on UPI at scale**, where interchange is permitted, converts the base into
  a fee-bearing channel without a policy change.
- **A tiered MDR** exempting small merchants would monetise large-merchant GMV with
  political cover. Low probability, high impact: a genuine option, not a base case.
- **Merchant software and settlement**, priced as SaaS, is chargeable today and is
  not exposed to the MDR debate at all.

## Ambiguity register

The JD asks for the ability to deal with ambiguity and to develop approaches to
tackle diligence questions. Stated explicitly, here is what this analysis does
**not** know, and how a real diligence would resolve it:

| Unknown | Why it is unresolved here | How to resolve it |
|---|---|---|
| True market-wide merchant count | Pulse discloses one operator's registered merchants; merchants multi-home across apps | Acquirer-level data room; NPCI acquirer reporting under NDA |
| Actual blended take rate | Not disclosed at instrument level in any open source | Management take-rate bridge; sample settlement files |
| CAC and payback by merchant segment | Not observable externally at all | Cohort files from the target; channel-level spend |
| Credit loss on UPI-originated lending | Vintages too short and not public | Static-pool loss curves by vintage from the lending partner |
| Whether the 30% share cap binds | The enforcement date has moved before | Regulatory counsel; model the cap as a step function |

**How this changes the recommendation.** The conditional *no* is robust to all five:
none of them makes a 0bps payment fee-bearing. The conditional *yes* is fragile to
the credit-loss question specifically: if UPI-originated loss rates run materially
above unsecured norms, the merchant-financing thesis fails and there is no third leg
to fall back on. That single unknown is where diligence spend should concentrate.

## Scope note

This is a **simulation** built entirely on public data, to demonstrate diligence
structure. It is not investment advice and not a recommendation on any security.
One97 Communications appears only as the listed comparable, using its filed figures.
"""
    write_memo("diligence-merchant-payments",
               "Underwrite distribution economics, not transaction economics",
               body,
               sources=["PhonePe Pulse: merchant base and merchant GMV",
                        "One97 Communications filed statements via yfinance"])
    print(f"   {merchants:,} merchants, {inr(gmv_per)}/quarter each, "
          f"{'listed comp included' if have_comp else 'no listed comp available'}")


if __name__ == "__main__":
    main()
