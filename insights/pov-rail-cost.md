---
title: "Zero MDR is not zero cost: the state pays about seven basis points, and it is falling"
generated: 2026-09-10
generator: analysis/08_rail_cost.py
sources:
  - "PIB, Ministry of Finance, Advancing Cashless India, 24 March 2025: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2114335"
  - "PhonePe Pulse, for the merchant-share cross-check"
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

Zero MDR is not zero cost. It is **7.0 basis points, paid by the
taxpayer**, and it is falling. In FY2023-24 the government paid acquiring banks
Rs 3,631 crore in incentive against
Rs 51.5 lakh crore of national merchant volume. Set beside the
30 basis points NPCI permits on merchant UPI and that statute
has held at zero since January 2020, the state is funding roughly 23.5% of
the discount rate the market is not allowed to charge.

**The appropriation is now falling in absolute terms, not only per rupee.** FY2024-25 was approved at **Rs 1,500 crore**, 58.7% below the Rs 3,631 crore actually paid in FY2023-24, against a merchant base that was still growing. No rate is computed for that year here: the outlay covers twelve months and the published value base covers 10, and a ratio across mismatched periods is not a rate.

## Three supporting arguments

**1. The subsidy per rupee has fallen in every year measured.** The blended rate went
from **8.68bps in FY2021-22 to 7.05bps in
FY2023-24**, a 18.8% decline. Nobody legislated that. The payout grew
2.6 times while the merchant base it covers grew 3.2 times,
and the distance between those two multiples is the whole mechanism: the appropriation
is set in rupees and the base compounds in percent.

**2. The statutory rate and the effective rate are different numbers, and only one of
them is money.** The scheme pays 15.00bps, but only on merchant
transactions at or under Rs 2,000 to small merchants. Blended across all merchant
value the state pays 7.05bps, which implies that **at least
47.0% of national merchant value sits inside that band**. That is a floor
rather than an estimate: 20% of every claim is withheld unless the acquiring bank holds
technical declines below 0.75% and uptime above 99.5%, so any entitlement left unclaimed
pushes the true eligible share up rather than down.

**3. It reframes the question from "why is the rail free" to "for how long".** The
merchant leg carries 63.9% of transactions and
23.0% of value at an average ticket of
Rs 425. Those economics are not zero-revenue. They are
revenue of last resort, appropriated one year at a time, at an effective rate nobody has
committed to holding. A business model resting on it is underwriting a budget line, not
a price.

## So what

- **For a payments operator:** the incentive is the floor under acquirer economics and it
  is thinning without an announcement. Model the rail at zero and treat the subsidy as
  upside, never as base case.
- **For a policymaker:** a fixed rupee appropriation against a compounding base is a rate
  cut delivered by arithmetic rather than by decision. If holding the effective rate is
  the intent, the outlay has to be indexed to merchant volume.
- **For an investor:** this is the strongest support yet for the conclusion in the
  diligence memo. The payment will not be repriced, and the subsidy is not a growth
  business. Whatever is investable here sits in the products the relationship carries,
  not in the transaction.

## Method and its limits

Both tables come from one PIB release, transcribed in a browser because PIB serves HTTP
403 to scripted requests and publishes these figures as chart images with printed data
labels rather than as text. The blended rate divides incentive actually paid by all
national merchant value, so both sides are measured and neither is modelled. The national
merchant share it implies, 25.8% of UPI value, is cross-checked against
PhonePe Pulse's own merchant share of value, 23.0%: a gap of
2.7 percentage points. Announcing a cross-check
without printing its result would be worth nothing, so it is printed. The two are not the
same quantity and are not expected to match: PIB measures the whole country, Pulse
measures one operator's book. The rate above is computed on the **national** figure,
because the incentive is paid against national merchant value and not against PhonePe's.

What is not known: how merchant value splits above and below the Rs 2,000 ceiling,
what share of it belongs to small merchants as the scheme defines them, and how much
entitlement went unclaimed on the performance conditions. Those three unknowns are
precisely why the eligible share above is published as a floor and not as a figure. The
series ends at FY2024-25 and is not extended by interpolation.
