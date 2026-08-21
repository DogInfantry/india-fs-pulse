---
title: "India's fund shelf is four times more administered than it is diverse"
generated: 2026-08-21
generator: analysis/07_wealth_amfi.py
sources:
  - AMFI daily NAV file (NAVAll.txt), 20-Aug-2026
---

<!-- GENERATED FILE. Edit the analysis script, not this file. -->
> **This module counts schemes, not rupees.** AMFI's daily NAV file is the full
> scheme universe with no AUM attached, so nothing below says where the money is.
> It describes the **shelf** - what is on offer, and in how many wrappers.

## The answer

On 20-Aug-2026 the Indian mutual fund industry listed **14,288 schemes** across
52 fund houses. Strip the plan and option wrappers - the same fund sold as
Direct and Regular, as Growth and IDCW - and those collapse to
**3,353 distinct strategies**. About **77% of the apparent
product count is packaging**, roughly 4.3 listed schemes for every real
investment decision.

That matters because the industry's complexity is usually described as a choice
problem. It is mostly a **distribution** problem: the shelf is not four times
richer than it looks, it is four times more administered than it looks.

## Two supporting arguments

**1. The wrapper multiple is remarkably uniform.** It holds across asset classes:
debt lists 8,016 schemes for 1,525 strategies
(5.3x), equity 3,110 for
809 (3.8x). This is not a few
houses over-engineering a product line; it is the market structure that the
Direct-plan reform of 2013 created and that nobody has since simplified.

**2. Scheme count and investor attention point in different directions.** Debt is
the largest category on the shelf at 56% of listed schemes,
against 22% for equity - the opposite of where retail
narrative sits. Much of that debt count is close-ended and interval product that a
retail investor will never choose. Counting products is not the same as counting
customers, and neither is the same as counting money.

**Concentration.** The five largest houses by strategy count run 51% of all
distinct strategies, so shelf breadth is materially concentrated even before any
AUM weighting.

## So what

- **For a distributor or platform:** the decision set to be curated is about
  3,353, not 14,288. Interfaces that present the listed count are
  presenting an artefact of plan structure as if it were choice.
- **For an asset manager:** the wrapper multiple is a fixed operating cost carried
  per strategy - compliance, NAV publication, reconciliation, statements - on
  products that are the same portfolio underneath.
- **For diligence on a wealth platform:** ask whether "products supported" is
  counted in schemes or strategies. The two differ by 4.3x, and the larger
  number flatters the platform.

## Method and its limits

Parsed from AMFI's `NAVAll.txt` for 20-Aug-2026. Strategies are derived by stripping
plan and option suffixes from scheme names, which is a **heuristic**: a house that
names two genuinely different funds identically would be under-counted, and one
that appends non-wrapper text would be over-counted. The direction and rough
magnitude are robust; the exact figure is not a regulatory statistic.

The binding limitation is the one at the top: **no AUM**. Every statement here is
about the shelf, not about assets, flows or revenue. Adding AMFI's quarterly
average-AUM disclosure would let this be restated in rupees, which is the version
that would actually inform a fee-pool estimate.
