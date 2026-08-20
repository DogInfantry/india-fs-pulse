"""Sub-module E: geographic gap analysis.

No population denominator is invented. The gap is measured within the payments
data itself: a state's share of TRANSACTIONS against its share of VALUE. A state
transacting far more often than its rupee share implies is merchant-heavy - and
merchant-heavy is exactly where zero-MDR bites.
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

    high = material.nlargest(5, "intensity_index")
    low = material.nsmallest(5, "intensity_index")
    top10_share = df.nlargest(10, "volume_share").volume_share.sum()

    write_json("chart_state_gap", {
        "period": period,
        "metric": "Intensity index = share of transactions / share of value. Above 1.0 = "
                  "transacts more often than its rupee share implies (merchant-heavy).",
        "states": [
            {"state": r.state.title(), "volume_share": round(r.volume_share, 4),
             "value_share": round(r.value_share, 4),
             "intensity_index": round(r.intensity_index, 3),
             "avg_ticket_inr": round(r.avg_ticket_inr, 0)}
            for r in df.itertuples()
        ],
    })

    def describe(frame):
        return ", ".join(
            f"**{r.state.title()}** ({r.intensity_index:.2f}, average ticket Rs {r.avg_ticket_inr:,.0f})"
            for r in frame.head(3).itertuples()
        )

    high_str, low_str = describe(high), describe(low)

    body = f"""
## The answer

Digital payments in India are not one market. In {period}, the ten largest states
carried **{pct(top10_share)} of all transactions**, and the states differ less in *how
much* they transact than in *what kind* of transaction they run. Ranking states by an
intensity index - share of transactions divided by share of value - separates
merchant-heavy states from remittance-heavy ones, and the two need different
strategies and carry different economics.

## Two supporting arguments

**1. Merchant-heavy states transact often and small.** The highest-intensity material
states are {high_str}. High frequency, low ticket: this is everyday retail spend, the leg that generates cost and no MDR revenue.

**2. Remittance-heavy states move fewer, larger transactions.** At the other end sit
{low_str}. Larger tickets point
to P2P transfers and remittance corridors rather than merchant checkout.

## So what

- **Merchant acquisition and lending should follow the high-intensity states.** That
  is where merchant density and transaction frequency support underwriting.
- **The zero-MDR burden is geographically concentrated.** The cost of processing sits
  disproportionately in the high-intensity states, which is where a tiered MDR would
  land hardest and where a small-merchant exemption would matter most.
- **Do not read this as adoption.** Intensity is a mix measure, not a penetration
  measure.

## Method and its limits

Computed from PhonePe Pulse state-level transaction counts and values for {period}.
Two limits, stated plainly: this is **one operator's** mix, not the market's; and with
**no population denominator** in the open data used here, this is deliberately a
*composition* measure, not a per-capita one. States below {MIN_SHARE:.0%} of national
volume are excluded when naming extremes, so a small union territory cannot top the
ranking on a thin base.
"""
    write_memo("gap-geographic", "India runs two different payments markets, not one",
               body, sources=["PhonePe Pulse state-level transaction data"])
    print(f"   {period}: top-10 states = {pct(top10_share)} of volume; "
          f"most merchant-intense material state = {high.state.iloc[0].title()}")


if __name__ == "__main__":
    main()
