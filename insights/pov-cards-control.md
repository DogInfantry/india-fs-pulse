---
title: "A price does not kill a rail, it segments it: cards kept the large ticket and lost the volume"
generated: 2026-09-10
generator: analysis/13_cards_control.py
sources:
  - "Reserve Bank of India, Bank-wise ATM/PoS/Card Statistics, national Total row: https://www.rbi.org.in/Scripts/ATMView.aspx"
  - "NPCI monthly product statistics, for the UPI side of the same month"
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
## The answer

India runs the experiment this report has been reaching for. In 2026-07, cards and UPI
moved money between the same merchants and the same customers under the same regulator,
and **only one of them was allowed to charge for it**.

The free rail took the volume: UPI ran **33 times** the card transactions and
**12 times** the value. Cards were left with 2.9% of the
transactions between the two rails.

But cards kept **7.6% of the value**, which is
2.6 times their share of transactions. The priced rail did not lose. It **retreated to the large ticket**, where a fee is small enough to absorb: Rs 3,482 against Rs 1,263, 2.8 times.

A merchant discount rate does not decide whether a rail survives. It decides **which
transactions it gets**. Across the 3 months transcribed the card share of value moves by only 0.2 percentage points and the ticket multiple barely moves, so this is a standing split rather than one month that happened to look this way.

## Three supporting arguments

**1. Acceptance is the clearest thing a price has ever moved.** There are
**803 million UPI QR codes** in the country against
10.0 million card terminals: 80 to one. A terminal is hardware
that costs money to deploy and carries a fee on every swipe. A QR code is a printed
sticker that carries nothing. Where a merchant can be paid has been decided, and it was
decided by price rather than by technology.

**2. The two rails are not competing for the same transaction.** At
Rs 3,482 against Rs 1,263, they serve different purchases. That is
why zero MDR did not simply destroy the card business: a fee of a percent or two is
invisible on a Rs 3,482 purchase and impossible on a Rs 1,263 one.
The report's earlier finding, that the merchant leg is volume-heavy and value-light,
now has a mechanism attached to it rather than only a description.

**3. It bounds what re-pricing UPI could ever achieve.** Sub-module C prices the
merchant leg at rates nobody charges. This is the same country actually charging one,
and the priced rail holds 7.6% of the value between them. Anyone
underwriting a return of MDR is underwriting a migration of value from the free rail to
the priced one, and cards show what that side looks like at its current size.

## So what

- **For an operator:** stop modelling cards as a legacy rail in decline. They are the
  high-ticket segment, and they are the only segment where a fee is collectable today.
  If a payments business needs fee income now, that is where it is.
- **For an investor:** the acceptance ratio, 80 to one, is the moat and it
  belongs to the free rail. Underwriting a card-acceptance build in India means
  competing against a sticker.
- **For a policymaker:** the natural experiment is already running domestically. Whether
  a tiered MDR would move volume or only move tickets is answerable from this data over
  time, and it does not need a pilot.

## Method and its limits

Card figures are RBI's own national **Total** row, transcribed by hand from the monthly
workbook because RBI's document links return an interstitial to a script. That Total was
reconciled against the sum of its 63 bank rows at 0.00% on every column transcribed, which
is the check that makes a hand-transcribed figure usable. Cash withdrawal is excluded
throughout: it is a cash logistics event, not a merchant payment. UPI is the NPCI series
this repo already carries, for the same calendar month, so no period is stretched.

What this does not say. **It does not price the card rail.** RBI publishes no blended
effective MDR; the ceiling differs by instrument, merchant category and ticket, so
multiplying a statutory rate by total value would publish an estimate as a measurement,
and this module refuses that exactly as sub-module B refuses a rate across mismatched
periods. It rests on **3 months**, 2026-05 to 2026-07, each a separate workbook
downloaded and transcribed by hand. That is enough to show the split is standing rather
than incidental, and not enough to call a direction: three points do not make a trend, and
every further month is another manual transcription. And card value here excludes transactions on cards routed over UPI, which
RuPay credit-on-UPI makes a growing and separately unpublished category, so the boundary
between the two rails is blurring in a direction this data cannot yet see.
