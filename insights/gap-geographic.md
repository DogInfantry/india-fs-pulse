---
title: "India runs two payments markets: one that spends, one that sends"
generated: 2026-08-21
generator: analysis/05_geo_gap.py
sources:
  - PhonePe Pulse state-level transaction data
  - PhonePe Pulse per-state category split
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

Digital payments in India are not one market. In 2026Q2, the ten largest states
carried **79.6% of all transactions**, but the more useful split is not size -
it is *what kind of transaction* a state runs. Measuring each state's merchant share
of its own transactions separates retail economies from remittance economies, and the
two carry different economics and need different strategies. Across the material
states the merchant share ranges over **12 percentage points**.

## Two supporting arguments

**1. Merchant-heavy states are the urban retail economies.** The highest merchant
shares sit in **Delhi** (68.5% of its own transactions), **Haryana** (67.9% of its own transactions), **Karnataka** (67.5% of its own transactions). These are dense, high-income, high-merchant-density states
where the everyday retail leg dominates - the leg that generates processing cost and,
at zero MDR, no revenue.

**2. P2P-heavy states are the remittance economies.** At the other end sit **West Bengal** (56.4% of its own transactions), **Bihar** (56.6% of its own transactions), **Assam** (57.3% of its own transactions).
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

Computed from PhonePe Pulse per-state category files for 2026Q2, cross-checked
against the separately-fetched country file: the 36 state files reconcile to the
national totals at a ratio of 1.000000 on both transaction count and value, and imply
a national merchant share of 63.9%.

Three limits, stated plainly. This is **one operator's** mix, not the market's -
though a *within-state* mix ratio is far less sensitive to PhonePe's uneven regional
footprint than a *between-state* volume ratio would be, which is the main reason this
measure is preferred. There is **no population denominator** in the open data used
here, so this is deliberately a composition measure, not a per-capita one. And states
below 1% of national volume are excluded when naming extremes, so a small
union territory cannot top the ranking on a thin base.

**What would change this answer:** a second operator's state-level category split. If
Google Pay's mix inverted this ranking, the finding would be about PhonePe's
distribution rather than about India. Nothing open publishes that today.

## A note on the previous version

This module previously ranked states by transaction share divided by value share,
calling it an "intensity index". That quantity is identical to national average ticket
divided by state average ticket - it restated ticket size and nothing else. Measured
against the real merchant share it correlates at -0.05, i.e. not at all.
The old index ranked Assam most merchant-intense; Assam is in fact among the most
P2P-heavy states here. The exhibit was replaced rather than relabelled.
