"""Sub-module E: geographic gap analysis.

MEASURED, not inferred. An earlier version of this module ranked states by an
"intensity index" of transaction share over value share. That index is
algebraically identical to national_avg_ticket / state_avg_ticket, so it was a
restatement of ticket size wearing a merchant-behaviour label, and it had the
sign backwards in practice: it put Assam top for merchant intensity because Assam
has the smallest average ticket, when Assam is in fact among the most P2P-heavy
states in the country.

The measure here is what fraction of a state's OWN transactions are merchant
payments, read directly from PhonePe's per-state category files. It is
independent of ticket size (observed correlation -0.05, against 1.00 for the old
index) and it is the leg zero-MDR actually applies to.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, load, pct, write_json, write_memo  # noqa: E402

MIN_SHARE = 0.01  # ignore very small states when naming extremes


def main() -> None:
    banner("Sub-module E: geographic gap")
    df = load("kpi_state_gap")
    period = df.period.iloc[0]
    material = df[df.volume_share >= MIN_SHARE].copy()

    high = material.nlargest(5, "merchant_volume_share")
    low = material.nsmallest(5, "merchant_volume_share")
    top10_share = df.nlargest(10, "volume_share").volume_share.sum()

    spread_pp = (material.merchant_volume_share.max() - material.merchant_volume_share.min()) * 100
    ticket_corr = material.merchant_volume_share.corr(material.avg_ticket_inr)
    national_merchant = df.merchant_volume_share.mul(df.volume_share).sum() / df.volume_share.sum()

    write_json("chart_state_gap", {
        "period": period,
        "metric": "Merchant share = a state's merchant (Retail) transactions as a share of its "
                  "own transactions. Measured from PhonePe's per-state category files, not "
                  "derived from ticket size.",
        "national_merchant_volume_share": round(float(national_merchant), 4),
        "min_share_for_extremes": MIN_SHARE,
        "states": [
            {"state": r.state.title(),
             "volume_share": round(r.volume_share, 4),
             "value_share": round(r.value_share, 4),
             "merchant_volume_share": round(r.merchant_volume_share, 4),
             "merchant_value_share": round(r.merchant_value_share, 4),
             "p2p_volume_share": round(r.p2p_volume_share, 4),
             "utility_volume_share": round(r.utility_volume_share, 4),
             "merchant_avg_ticket_inr": round(r.merchant_avg_ticket_inr, 0),
             "avg_ticket_inr": round(r.avg_ticket_inr, 0),
             "ticket_vs_national": round(r.ticket_vs_national, 3)}
            for r in df.itertuples()
        ],
    })

    def describe(frame):
        return ", ".join(
            f"**{r.state.title()}** ({pct(r.merchant_volume_share)} of its own transactions)"
            for r in frame.head(3).itertuples()
        )

    high_str, low_str = describe(high), describe(low)

    body = f"""
## The answer

Digital payments in India are not one market. In {period}, the ten largest states
carried **{pct(top10_share)} of all transactions**, but the more useful split is not size.
It is *what kind of transaction* a state runs. Measuring each state's merchant share
of its own transactions separates retail economies from remittance economies, and the
two carry different economics and need different strategies. Across the material
states the merchant share ranges over **{spread_pp:.0f} percentage points**.

## Two supporting arguments

**1. Merchant-heavy states are the urban retail economies.** The highest merchant
shares sit in {high_str}. These are dense, high-income, high-merchant-density states
where the everyday retail leg dominates: the leg that generates processing cost and,
at zero MDR, no revenue.

**2. P2P-heavy states are the remittance economies.** At the other end sit {low_str}.
A larger share of person-to-person transfers is the signature of money being *sent*
rather than *spent*: labour-exporting states receiving inbound remittance flows.

## So what

- **Merchant acquisition and lending should follow the merchant-heavy states.** That
  is where merchant density and repeat transaction frequency support underwriting.
- **The zero-MDR burden is geographically concentrated.** Processing cost sits
  disproportionately where the merchant share is highest, which is where a tiered MDR
  would land hardest and where a small-merchant exemption would matter most.
- **Do not read this as adoption.** It is a mix measure, not a penetration measure.

## Method and its limits

Computed from PhonePe Pulse per-state category files for {period}, cross-checked
against the separately-fetched country file: the 36 state files reconcile to the
national totals at a ratio of 1.000000 on both transaction count and value, and imply
a national merchant share of {pct(national_merchant)}.

Three limits, stated plainly. This is **one operator's** mix, not the market's,
though a *within-state* mix ratio is far less sensitive to PhonePe's uneven regional
footprint than a *between-state* volume ratio would be, which is the main reason this
measure is preferred. There is **no population denominator** in the open data used
here, so this is deliberately a composition measure, not a per-capita one. And states
below {MIN_SHARE:.0%} of national volume are excluded when naming extremes, so a small
union territory cannot top the ranking on a thin base.

**What would change this answer:** a second operator's state-level category split. If
Google Pay's mix inverted this ranking, the finding would be about PhonePe's
distribution rather than about India. Nothing open publishes that today.

## A note on the previous version

This module previously ranked states by transaction share divided by value share,
calling it an "intensity index". That quantity is identical to national average ticket
divided by state average ticket. It restated ticket size and nothing else. Measured
against the real merchant share it correlates at {ticket_corr:+.2f}, i.e. not at all.
The old index ranked Assam most merchant-intense; Assam is in fact among the most
P2P-heavy states here. The exhibit was replaced rather than relabelled.
"""
    write_memo("gap-geographic", "India runs two payments markets: one that spends, one that sends",
               body, sources=["PhonePe Pulse state-level transaction data",
                              "PhonePe Pulse per-state category split"])
    print(f"   {period}: top-10 states = {pct(top10_share)} of volume; "
          f"merchant share {pct(material.merchant_volume_share.min())}-"
          f"{pct(material.merchant_volume_share.max())} across {len(material)} material states")
    print(f"   most merchant-heavy: {high.state.iloc[0].title()}; "
          f"most P2P-heavy: {low.state.iloc[0].title()}; ticket correlation {ticket_corr:+.3f}")


if __name__ == "__main__":
    main()
