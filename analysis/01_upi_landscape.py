"""Sub-module A: UPI landscape scan and the monetisation POV.

Governing thought: India's payments network monetises the wrong leg. The
merchant leg carries the transactions; the P2P leg carries the rupees; and the
merchant leg: the only one MDR could ever touch - is priced at zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-upi-monetization"


def main() -> None:
    banner("Sub-module A: UPI landscape and monetisation POV")
    hero = load_json("upi_monetisation")
    trend = load("kpi_upi_trend")

    cats = {c["category"]: c for c in hero["categories"]}
    merchant, p2p = cats["Retail"], cats["P2P"]

    complete = trend.dropna(subset=["volume_mn"])
    first, last = complete.iloc[0], complete.iloc[-1]
    # Five-year CAGR, not since-inception: UPI's 2016 base is near zero, so a
    # since-inception CAGR is arithmetically true and analytically meaningless.
    base = complete[complete.month <= f"{int(last.month[:4]) - 5}-{last.month[5:]}"].iloc[-1]
    years = 5.0
    cagr = (last.volume_mn / base.volume_mn) ** (1 / years) - 1
    ticket_then = complete[complete.month == "2019-01"].avg_ticket_inr
    ticket_now = last.avg_ticket_inr
    ticket_drop = (1 - ticket_now / ticket_then.iloc[0]) if len(ticket_then) else None

    latest_yoy = complete.dropna(subset=["volume_yoy"]).iloc[-1]
    mdr = hero["mdr_scenarios_cr"]

    write_json("chart_category_split", {
        "period": hero["period"],
        "note": "PhonePe's own transactions. Volume share vs value share by leg.",
        "series": [
            {"category": c["category"], "volume_share": c["volume_share"],
             "value_share": c["value_share"], "avg_ticket_inr": c["avg_ticket_inr"],
             "count_bn": c["count_bn"], "amount_lakh_cr": c["amount_lakh_cr"]}
            for c in hero["categories"]
        ],
    })
    write_json("chart_mdr_bridge", {
        "period": hero["period"],
        "merchant_gmv_lakh_cr": merchant["amount_lakh_cr"],
        "scenarios": [{"rate": k, "revenue_cr": v} for k, v in mdr.items()],
        "note": "Revenue that the merchant leg would generate at each MDR rate. Today it is zero.",
    })


    # --- Growth bridge: which leg actually produced the growth?
    # If the merchant leg dominates the delta, then growth is arriving in the
    # only leg that cannot be charged for, which is the whole argument.
    pulse = load("pulse_txn_national")
    per_period = pulse.groupby(["period", "category"])["count"].sum().unstack().dropna()
    open_p, close_p = per_period.index[0], per_period.index[-1]
    opening, closing = per_period.loc[open_p], per_period.loc[close_p]
    order = (closing - opening).sort_values(ascending=False)
    steps = [{"label": open_p, "value": round(float(opening.sum()) / 1e9, 2), "type": "start"}]
    for cat in order.index:
        steps.append({"label": cat, "value": round(float(order[cat]) / 1e9, 2), "type": "delta"})
    steps.append({"label": close_p, "value": round(float(closing.sum()) / 1e9, 2), "type": "end"})
    biggest = str(order.index[0])
    contribution = float(order.iloc[0]) / float(order.sum())
    write_json("chart_growth_bridge", {
        "unit": "billion transactions per quarter",
        "highlight": biggest,
        "steps": steps,
        "note": f"{biggest} contributed {contribution:.0%} of all volume growth between "
                f"{open_p} and {close_p}.",
    })

    body = f"""
## The answer

India's payments rails have separated volume from value, and then priced the
volume side at zero. In {hero['period']}, merchant payments were
**{pct(merchant['volume_share'])} of all transactions but only
{pct(merchant['value_share'])} of the rupees moved**. Person-to-person transfers
were the mirror image: {pct(p2p['volume_share'])} of transactions,
{pct(p2p['value_share'])} of value. The merchant leg is the only leg a merchant
discount rate could ever be charged on, and under the zero-MDR regime it earns
**nothing**.

The consequence, sized on one player's disclosed data: {hero['registered_merchants']:,}
registered merchants transacting {hero['txns_per_merchant']:,.0f} times a quarter each,
{inr(hero['gmv_per_merchant_inr'])} of GMV per merchant per quarter, at
**{inr(0)} of transaction revenue**.

## Four supporting arguments

**1. The base is enormous and still compounding.** UPI has grown from
{base.volume_mn:,.0f} million transactions in {base.month} to
{last.volume_mn:,.0f} million in {last.month}: a **{pct(cagr, 0)} five-year CAGR**,
off a series that starts at {first.volume_mn:,.1f} million in {first.month}. Even now, growth has not decayed to maturity: the most recent
year-on-year reading is {pct(latest_yoy.volume_yoy)} on volume and
{pct(latest_yoy.value_yoy)} on value ({latest_yoy.month}).

**2. Growth is arriving in the leg that cannot be charged for.** Between {open_p} and {close_p}, {biggest} contributed **{pct(contribution, 0)} of all volume growth**, {order.iloc[0] / 1e9:.1f} billion of the {order.sum() / 1e9:.1f} billion additional quarterly transactions. Growth is not merely large, it is concentrated in the merchant leg that zero-MDR prices at nothing.

**3. Growth is arriving as small tickets, which is the expensive kind.**
The average UPI transaction has fallen to **{inr(ticket_now)}**{
    f", down {pct(ticket_drop)} from January 2019" if ticket_drop else ""
}. Every incremental transaction adds switch, fraud and support cost while adding
no fee income. Volume growth without price is a cost line, not a revenue line.

**4. The revenue foregone is quantifiable, and it is not small.** On the merchant
GMV of {merchant['amount_lakh_cr']:.2f} lakh crore in {hero['period']}, again, one
player: a {"10bps"} MDR would generate {inr(float(mdr['10bps']) * 1e7)} a quarter,
30bps {inr(float(mdr['30bps']) * 1e7)}, and 50bps {inr(float(mdr['50bps']) * 1e7)}.
The policy choice is therefore not "should payments be cheap" but "who funds a
{inr(float(mdr['30bps']) * 1e7)}-a-quarter subsidy, and for how long".

## So what: four monetisation pathways, ranked

| Pathway | Mechanism | Why it can work | Principal risk |
|---|---|---|---|
| **Credit on UPI** | Route pre-approved credit lines and RuPay credit cards over UPI, where interchange **is** permitted | Converts a zero-fee rail into a distribution channel for a fee-bearing product; the merchant relationship is already there | Credit risk sits with the lender, not the app; underwriting thin-file borrowers at this volume is unproven |
| **PPI / wallet interchange** | Wallet-loaded UPI transactions carry permitted interchange | Already regulator-sanctioned; no behaviour change asked of the payer | Small share of transactions; economics depend on load patterns |
| **Distribution and cross-sell** | Use the payment relationship to distribute insurance, mutual funds, lending | Highest-margin option; the app knows cash-flow behaviour no bank sees | Regulatory perimeter, and the trust cost of monetising a utility |
| **Cross-border and merchant SaaS** | Inbound remittance corridors, and paid tooling for merchants (settlement, reconciliation, capital) | Fees are acceptable where the payer is not the Indian consumer | Corridor-by-corridor build; slow to scale |

**The recommendation.** Treat UPI as customer acquisition, not as a product.
The defensible model is a **merchant-side flywheel**: use the
{hero['txns_per_merchant']:,.0f} touchpoints a quarter to underwrite working capital
and sell software, where price is chargeable, rather than lobbying for an MDR that is
politically unavailable. Rank credit-on-UPI first because it is the only pathway that
scales with the existing transaction base rather than against it.

## What would change this answer

- **MDR returns for large merchants.** A tiered MDR: zero for small merchants,
  priced above a threshold, would make the merchant leg directly monetisable and
  reverse the ranking above.
- **The 30% market-share cap is enforced.** A binding cap redistributes volume
  rather than growing it, and changes who can afford the subsidy.
- **Credit losses on UPI-originated lending.** If loss rates on this channel run
  above unsecured norms, pathway one collapses and distribution moves to first.
"""

    write_memo(
        MEMO,
        "India's payments network monetises the wrong leg",
        body,
        sources=[
            "PhonePe Pulse (github.com/PhonePe/pulse): category split and merchant base",
            "NPCI monthly product statistics: headline volume and value series",
        ],
    )
    print(f"   merchant {pct(merchant['volume_share'])} volume / {pct(merchant['value_share'])} value; "
          f"CAGR {pct(cagr, 0)}; ticket {inr(ticket_now)}")


if __name__ == "__main__":
    main()
