---
title: "India's payments network monetises the wrong leg"
generated: 2026-08-20
generator: analysis/01_upi_landscape.py
sources:
  - PhonePe Pulse (github.com/PhonePe/pulse) - category split and merchant base
  - NPCI monthly product statistics - headline volume and value series
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

India's payments rails have separated volume from value, and then priced the
volume side at zero. In 2026Q2, merchant payments were
**63.9% of all transactions but only
23.0% of the rupees moved**. Person-to-person transfers
were the mirror image: 30.8% of transactions,
71.2% of value. The merchant leg is the only leg a merchant
discount rate could ever be charged on - and under the zero-MDR regime it earns
**nothing**.

The consequence, sized on one player's disclosed data: 50,705,249
registered merchants transacting 487 times a quarter each,
Rs 206,685 of GMV per merchant per quarter, at
**Rs 0 of transaction revenue**.

## Three supporting arguments

**1. The base is enormous and still compounding.** UPI has grown from
3,248 million transactions in 2021-07 to
23,658 million in 2026-07 - a **49% five-year CAGR**,
off a series that starts at 0.1 million in 2016-07. Even now, growth has not decayed to maturity: the most recent
year-on-year reading is 21.5% on volume and
19.1% on value (2026-07).

**2. Growth is arriving as small tickets, which is the expensive kind.**
The average UPI transaction has fallen to **Rs 1,263**, down 22.7% from January 2019. Every incremental transaction adds switch, fraud and support cost while adding
no fee income. Volume growth without price is a cost line, not a revenue line.

**3. The revenue foregone is quantifiable, and it is not small.** On the merchant
GMV of 10.48 lakh crore in 2026Q2 - again, one
player - a 10bps MDR would generate Rs 1,048 crore a quarter,
30bps Rs 3,144 crore, and 50bps Rs 5,240 crore.
The policy choice is therefore not "should payments be cheap" but "who funds a
Rs 3,144 crore-a-quarter subsidy, and for how long".

## So what: four monetisation pathways, ranked

| Pathway | Mechanism | Why it can work | Principal risk |
|---|---|---|---|
| **Credit on UPI** | Route pre-approved credit lines and RuPay credit cards over UPI, where interchange **is** permitted | Converts a zero-fee rail into a distribution channel for a fee-bearing product; the merchant relationship is already there | Credit risk sits with the lender, not the app; underwriting thin-file borrowers at this volume is unproven |
| **PPI / wallet interchange** | Wallet-loaded UPI transactions carry permitted interchange | Already regulator-sanctioned; no behaviour change asked of the payer | Small share of transactions; economics depend on load patterns |
| **Distribution and cross-sell** | Use the payment relationship to distribute insurance, mutual funds, lending | Highest-margin option; the app knows cash-flow behaviour no bank sees | Regulatory perimeter, and the trust cost of monetising a utility |
| **Cross-border and merchant SaaS** | Inbound remittance corridors, and paid tooling for merchants (settlement, reconciliation, capital) | Fees are acceptable where the payer is not the Indian consumer | Corridor-by-corridor build; slow to scale |

**The recommendation.** Treat UPI as customer acquisition, not as a product.
The defensible model is a **merchant-side flywheel**: use the
487 touchpoints a quarter to underwrite working capital
and sell software, where price is chargeable, rather than lobbying for an MDR that is
politically unavailable. Rank credit-on-UPI first because it is the only pathway that
scales with the existing transaction base rather than against it.

## What would change this answer

- **MDR returns for large merchants.** A tiered MDR - zero for small merchants,
  priced above a threshold - would make the merchant leg directly monetisable and
  reverse the ranking above.
- **The 30% market-share cap is enforced.** A binding cap redistributes volume
  rather than growing it, and changes who can afford the subsidy.
- **Credit losses on UPI-originated lending.** If loss rates on this channel run
  above unsecured norms, pathway one collapses and distribution moves to first.
