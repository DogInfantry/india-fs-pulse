"""Sub-module I: the only comparable rail, and what it says about the answer.

Every other module in this report measures India against itself. That is enough to
describe the monetisation gap and not enough to explain it: a structure observed once
could be an Indian artefact of zero MDR, of NPCI's governance, or of nothing at all.

Brazil's Pix is the one case that can settle it. Same design (a national instant rail,
free to the payer, run by the central bank), a different country, a different regulator,
and six years of history. If the merchant leg carries the transactions and not the money
there too, the shape is what zero-cost instant rails do, and the report's conclusion
stops being an interpretation of India.

Two comparisons are refused here on purpose. Nothing is converted between reais and
rupees: every figure is a share of its own country's total, so no exchange rate is
needed and none is invented. And raw monthly volumes are never set side by side without
a denominator, because Brazil runs a fraction of India's population and the unadjusted
comparison would flatter India while saying nothing about maturity.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-pix-comparator"
MERCHANT_LEG = "P2B"
INDIA_MERCHANT = "Retail"      # PhonePe's label for the merchant leg
# Layers Brazil added on top of the free transfer: recurring debits, open-finance
# initiation, and contactless. These are the candidates for "the rail grew a business".
ADD_ON_CODES = ["AUTO", "INIC", "APDN", "APES"]
# Below this share of merchant volume, a product is not yet a business line. Stated
# as a constant so the memo's verdict is a comparison rather than an adjective.
MATERIALITY = 0.01
UNDISCLOSED = {"Nao disponivel", "Nao informado"}


def banked_adults(wb: pd.DataFrame) -> tuple[float, int, float]:
    """Adults holding an account, on the 15+ base account ownership is measured against.

    Identical arithmetic to analysis/02 so the two countries are the same measure:
    total population, less ages 0 to 14, times the latest Findex ownership reading.
    """
    own = wb.dropna(subset=["account_ownership_pct"]).sort_values("year").iloc[-1]
    pop = wb.dropna(subset=["population", "population_0_14"])
    row = pop[pop.year <= own.year].sort_values("year").iloc[-1]
    adults = float(row.population) - float(row.population_0_14)
    return adults * float(own.account_ownership_pct) / 100, int(own.year), float(own.account_ownership_pct)


def main() -> None:
    banner("Sub-module I: Brazil's Pix, the comparator")
    pix = load("pix_txn_monthly")
    init = load("pix_p2b_initiation")
    fraud = load("pix_fraud_monthly")
    wb_br = load("worldbank_brazil")
    wb_in = load("worldbank_india")
    upi = load("upi_monthly")
    hero = load_json("upi_monetisation")

    latest_month = str(pix.month.max())
    first_month = str(pix.month.min())
    br = pix[(pix.month == latest_month) & (pix.leg == MERCHANT_LEG)].iloc[0]
    br_open = pix[(pix.month == first_month) & (pix.leg == MERCHANT_LEG)].iloc[0]
    br_p2p = pix[(pix.month == latest_month) & (pix.leg == "P2P")].iloc[0]
    br_b2b = pix[(pix.month == latest_month) & (pix.leg == "B2B")].iloc[0]

    in_merchant = next(c for c in hero["categories"] if c["category"] == INDIA_MERCHANT)
    in_p2p = next(c for c in hero["categories"] if c["category"] == "P2P")

    # --- Exhibit: the same shape in two countries
    write_json("chart_pix_shape", {
        "note": "Each bar is a leg's share of its OWN country's total, so no exchange "
                "rate is involved and the two rails are directly comparable.",
        "india_period": hero["period"],
        "brazil_month": latest_month,
        # The axis label is built here rather than in the page: the page should not be
        # retyping which country a bar belongs to.
        "rails": [
            {"label": "India merchant", "rail": "India, UPI", "period": hero["period"],
             "volume_share": in_merchant["volume_share"], "value_share": in_merchant["value_share"]},
            {"label": "India P2P", "rail": "India, UPI", "period": hero["period"],
             "volume_share": in_p2p["volume_share"], "value_share": in_p2p["value_share"]},
            {"label": "Brazil merchant", "rail": "Brazil, Pix", "period": latest_month,
             "volume_share": round(float(br.volume_share), 4),
             "value_share": round(float(br.value_share), 4)},
            {"label": "Brazil P2P", "rail": "Brazil, Pix", "period": latest_month,
             "volume_share": round(float(br_p2p.volume_share), 4),
             "value_share": round(float(br_p2p.value_share), 4)},
        ],
    })

    # --- Exhibit: the merchant leg migrated, on a rail six years old
    merch = pix[pix.leg == MERCHANT_LEG].sort_values("month")
    write_json("chart_pix_migration", {
        "note": f"Brazil's merchant leg as a share of all Pix. The dashed line is India's "
                f"merchant share of {pct(in_merchant['volume_share'], 0)} in {hero['period']}, "
                "measured on PhonePe's book rather than nationally.",
        "months": merch.month.tolist(),
        "volume_share": [round(float(v), 4) for v in merch.volume_share],
        "value_share": [round(float(v), 4) for v in merch.value_share],
        "india_merchant_volume_share": in_merchant["volume_share"],
        "india_period": hero["period"],
    })

    # --- Exhibit: what the rail grew on top of itself
    disclosed = init[~init.initiation.isin(UNDISCLOSED)]
    add_on = init[init.initiation.isin(ADD_ON_CODES)]
    add_on_now = float(add_on[add_on.month == latest_month].p2b_volume_share.sum())
    qr_now = float(init[(init.month == latest_month) & (init.initiation == "QRDN")]
                   .p2b_volume_share.iloc[0])
    months_disc = sorted(disclosed.month.unique())
    # A product that did not exist yet reads as null, never as zero: `?? 0` on a missing
    # observation invents a data point, and a zero would draw a flat line through years
    # in which the product had not launched.
    series = []
    for code in ADD_ON_CODES:
        rows = add_on[add_on.initiation == code].set_index("month").p2b_volume_share
        if not len(rows):
            continue
        label = add_on[add_on.initiation == code].initiation_label.iloc[0]
        series.append({
            "code": code, "label": label,
            "first_month": str(rows.index.min()),
            "values": [None if m not in rows.index else round(float(rows[m]), 6)
                       for m in months_disc],
        })
    write_json("chart_pix_products", {
        "note": "Share of Brazil's merchant-leg transactions initiated by each layer the "
                "central bank added on top of the free transfer. A layer reads null before "
                "it launched, never zero.",
        "months": months_disc,
        "series": series,
        "materiality": MATERIALITY,
        "dynamic_qr_share": round(qr_now, 4),
        "add_on_share": round(add_on_now, 6),
        "latest_month": latest_month,
    })

    # --- Exhibit: the asymmetry India cannot match
    write_json("chart_pix_fraud", {
        "note": "Brazil's central bank publishes Pix fraud monthly. India publishes no "
                "equivalent in machine-readable form, so there is no Indian line to draw.",
        "months": fraud.month.tolist(),
        "accepted_per_100k_txns": [round(float(v), 3) for v in fraud.accepted_per_100k_txns],
        "returned_pct": [round(float(v), 2) for v in fraud.returned_pct],
        "latest_month": str(fraud.month.max()),
        "transactions_latest_month": latest_month,
    })

    # --- Intensity, on the latest month both countries publish
    common = sorted(set(upi.month) & set(pix.month))
    common_month = common[-1]
    br_txns = float(pix[pix.month == common_month].volume_mn.sum()) * 1e6
    in_txns = float(upi[upi.month == common_month].volume_mn.iloc[0]) * 1e6
    br_banked, br_year, br_own = banked_adults(wb_br)
    in_banked, in_year, in_own = banked_adults(wb_in)
    br_per_adult = br_txns / br_banked
    in_per_adult = in_txns / in_banked
    intensity_x = br_per_adult / in_per_adult

    # --- Claims that depend on which way the numbers fall, decided in code
    shape_repeats = (br.volume_share > br.value_share) and (
        in_merchant["volume_share"] > in_merchant["value_share"])
    shape_line = (
        "The shape repeats."
        if shape_repeats else
        "The shape does NOT repeat, which would make India's split an Indian artefact "
        "rather than a property of zero-cost instant rails."
    )
    add_on_verdict = (
        f"still below the {pct(MATERIALITY, 0)} line, which is to say not yet a business"
        if add_on_now < MATERIALITY else
        f"through the {pct(MATERIALITY, 0)} line, so the layered products have become "
        "material and this conclusion needs revisiting"
    )
    year_ago = f"{int(latest_month[:4]) - 1}-{latest_month[5:]}"
    prior = add_on[add_on.month == year_ago].p2b_volume_share.sum()
    growth_note = ""
    if year_ago in set(add_on.month) and float(prior) > 0:
        growth_note = (
            f" It is also compounding fast: {add_on_now / float(prior):.0f} times its "
            f"{year_ago} share in twelve months. Small and accelerating is a different "
            "statement from small and static, and only the first of those is an option "
            "on something."
        )
    lead_country = "Brazil" if intensity_x > 1 else "India"
    stale_note = ""
    if str(fraud.month.max()) < latest_month:
        stale_note = (f" The fraud table stops at {fraud.month.max()} while the "
                      f"transaction table runs to {latest_month}, so the two are not "
                      "read against each other here.")

    body = f"""
## The answer

The one rail comparable to UPI does the same thing, and after six years it still does
not earn from the transaction. In {latest_month}, Brazil's merchant leg was
**{pct(float(br.volume_share))} of all Pix transactions and {pct(float(br.value_share))}
of the value**. India's merchant leg in {hero['period']} was
**{pct(in_merchant['volume_share'])} of transactions and {pct(in_merchant['value_share'])}
of value**. {shape_line} Two central banks, two regulators, one design, and in both cases
the busy leg is the cheap leg.

That matters because it converts this report's central claim from an interpretation into
an observation. The split is not a consequence of India's zero-MDR statute, because Brazil
never had an MDR to remove and arrived at the same place.

## Three supporting arguments

**1. Brazil's merchant leg migrated exactly as India's did, from a standing start.**
P2B was {pct(float(br_open.volume_share))} of Pix in {first_month}, the rail's first
month, and {pct(float(br.volume_share))} in {latest_month}. Nothing redirected it: the
merchant leg is simply where instant payments go once the habit exists. India's own growth
bridge says the same thing from the other end, that the merchant leg produced most of the
volume growth. Two independent series, one behaviour.

**2. The layers built on top of the free rail are real and still immaterial.** Brazil did
what the "just add products" answer prescribes: recurring debits, open-finance payment
initiation, and contactless. Together they account for **{pct(add_on_now, 2)} of merchant
transactions**, {add_on_verdict}.{growth_note} Meanwhile the merchant leg consolidated
into dynamic QR, now {pct(qr_now)} of it, which is a distribution channel rather than a
revenue line: it carries an amount and a payload into a merchant's own system, and it is
free.

**3. Brazil is further along the same curve, so this is not a maturity gap India will
grow out of.** On {common_month}, the latest month both countries publish, Brazil ran
**{br_per_adult:,.0f} instant payments per banked adult** against India's
**{in_per_adult:,.0f}**, so {lead_country} leads by {intensity_x:.1f} times. Both use the
same denominator: total population less ages 0 to 14, times account ownership
({br_own:.0f}% for Brazil and {in_own:.0f}% for India, Findex {br_year} and {in_year}).
The more mature rail is the one with the smaller merchant value share. Volume does not
convert into transaction revenue by getting bigger.

## So what

- **For an operator:** stop treating zero-MDR India as a special case awaiting a policy
  fix. The comparator says the transaction does not become monetisable at scale, at
  maturity, or under a different regulator. Plan for a rail that stays free.
- **For an investor:** this is the outside view the diligence memo was missing. The
  business that exists here is the relationship the payment creates, not the payment. The
  add-on layers are worth watching precisely because they are {pct(add_on_now, 2)} today,
  which makes them an option rather than a base case.
- **For a policymaker:** Brazil publishes monthly Pix fraud statistics and India publishes
  none in machine-readable form. That gap is not analytical, it is a disclosure choice, and
  it is the single cheapest thing on this page to fix.

## Method and its limits

Brazil's central bank publishes the transaction cross-tab as keyless open data, labelled
by payer and receiver type, so the merchant leg is read from the publisher's own `P2B`
label rather than derived. No currency is converted anywhere in this module: every figure
is a share of its own country's total, which is why no exchange rate appears and none is
assumed. The intensity comparison is the one place a denominator is used, and both sides
use the same one.

What this cannot support: it is **one comparator, not a survey of instant rails**. India's
merchant split is PhonePe's book while Brazil's is national, so the two are the same
measure on different populations, and the levels should be read as approximate even though
the direction is not in doubt. Brazil's series carries a small number of early rows with no
initiation method recorded, kept as a separate bucket rather than dropped, because dropping
a grouping key removes its transactions from the denominator and quietly inflates every
other share.{stale_note}
"""

    write_memo(
        MEMO,
        "The only comparable rail repeats India's shape and has not monetised the transaction either",
        body,
        sources=[
            "Banco Central do Brasil, Pix statistics (Olinda open data): "
            "https://www.bcb.gov.br/estabilidadefinanceira/estatisticaspix",
            "World Bank Global Findex and population, for the banked-adult denominator",
            "PhonePe Pulse and NPCI monthly product statistics, for the India side",
        ],
    )
    print(f"   {latest_month}: Brazil merchant {br.volume_share:.1%} of volume / "
          f"{br.value_share:.1%} of value, against India {in_merchant['volume_share']:.1%} / "
          f"{in_merchant['value_share']:.1%}")
    print(f"   merchant leg migrated {br_open.volume_share:.1%} ({first_month}) to "
          f"{br.volume_share:.1%} ({latest_month}); B2B holds {br_b2b.value_share:.1%} of value")
    print(f"   layered products {add_on_now:.2%} of merchant volume, dynamic QR {qr_now:.1%}")
    print(f"   intensity on {common_month}: Brazil {br_per_adult:,.0f} vs India "
          f"{in_per_adult:,.0f} per banked adult per month ({intensity_x:.1f}x)")


if __name__ == "__main__":
    main()
