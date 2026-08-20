---
title: "India runs two different payments markets, not one"
generated: 2026-08-20
generator: analysis/05_geo_gap.py
sources:
  - PhonePe Pulse state-level transaction data
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

Digital payments in India are not one market. In 2026Q2, the ten largest states
carried **79.6% of all transactions**, and the states differ less in *how
much* they transact than in *what kind* of transaction they run. Ranking states by an
intensity index - share of transactions divided by share of value - separates
merchant-heavy states from remittance-heavy ones, and the two need different
strategies and carry different economics.

## Two supporting arguments

**1. Merchant-heavy states transact often and small.** The highest-intensity material
states are **Assam** (1.24, average ticket Rs 946), **Delhi** (1.17, average ticket Rs 1,004), **Chhattisgarh** (1.12, average ticket Rs 1,050). High frequency, low ticket: this is everyday retail spend, the leg that generates cost and no MDR revenue.

**2. Remittance-heavy states move fewer, larger transactions.** At the other end sit
**Andhra Pradesh** (0.83, average ticket Rs 1,424), **Telangana** (0.89, average ticket Rs 1,322), **Tamil Nadu** (0.94, average ticket Rs 1,255). Larger tickets point
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

Computed from PhonePe Pulse state-level transaction counts and values for 2026Q2.
Two limits, stated plainly: this is **one operator's** mix, not the market's; and with
**no population denominator** in the open data used here, this is deliberately a
*composition* measure, not a per-capita one. States below 1% of national
volume are excluded when naming extremes, so a small union territory cannot top the
ranking on a thin base.
