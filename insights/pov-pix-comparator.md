---
title: "The only comparable rail repeats India's shape and has not monetised the transaction either"
generated: 2026-09-10
generator: analysis/09_pix_comparator.py
sources:
  - "Banco Central do Brasil, Pix statistics (Olinda open data): https://www.bcb.gov.br/estabilidadefinanceira/estatisticaspix"
  - "World Bank Global Findex and population, for the banked-adult denominator"
  - "PhonePe Pulse and NPCI monthly product statistics, for the India side"
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

The one rail comparable to UPI does the same thing, and after six years it still does
not earn from the transaction. In 2026-08, Brazil's merchant leg was
**46.6% of all Pix transactions and 11.8%
of the value**. India's merchant leg in 2026Q2 was
**63.9% of transactions and 23.0%
of value**. The shape repeats. Two central banks, two regulators, one design, and in both cases
the busy leg is the cheap leg.

That matters because it converts this report's central claim from an interpretation into
an observation. The split is not a consequence of India's zero-MDR statute, because Brazil
never had an MDR to remove and arrived at the same place.

## Three supporting arguments

**1. Brazil's merchant leg migrated exactly as India's did, from a standing start.**
P2B was 5.2% of Pix in 2020-11, the rail's first
month, and 46.6% in 2026-08. Nothing redirected it: the
merchant leg is simply where instant payments go once the habit exists. India's own growth
bridge says the same thing from the other end, that the merchant leg produced most of the
volume growth. Two independent series, one behaviour.

**2. The layers built on top of the free rail are real and still immaterial.** Brazil did
what the "just add products" answer prescribes: recurring debits, open-finance payment
initiation, and contactless. Together they account for **0.26% of merchant
transactions**, still below the 1% line, which is to say not yet a business. It is also compounding fast: 14 times its 2025-08 share in twelve months. Small and accelerating is a different statement from small and static, and only the first of those is an option on something. Meanwhile the merchant leg consolidated
into dynamic QR, now 84.1% of it, which is a distribution channel rather than a
revenue line: it carries an amount and a payload into a merchant's own system, and it is
free.

**3. Brazil is further along the same curve, so this is not a maturity gap India will
grow out of.** On 2026-07, the latest month both countries publish, Brazil ran
**49 instant payments per banked adult** against India's
**24**, so Brazil leads by 2.0 times. Both use the
same denominator: total population less ages 0 to 14, times account ownership
(86% for Brazil and 89% for India, Findex 2024 and 2024).
The more mature rail is the one with the smaller merchant value share. Volume does not
convert into transaction revenue by getting bigger.

## So what

- **For an operator:** stop treating zero-MDR India as a special case awaiting a policy
  fix. The comparator says the transaction does not become monetisable at scale, at
  maturity, or under a different regulator. Plan for a rail that stays free.
- **For an investor:** this is the outside view the diligence memo was missing. The
  business that exists here is the relationship the payment creates, not the payment. The
  add-on layers are worth watching precisely because they are 0.26% today,
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
other share. The fraud table stops at 2026-04 while the transaction table runs to 2026-08, so the two are not read against each other here.
