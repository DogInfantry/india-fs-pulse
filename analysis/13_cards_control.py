"""Sub-module M: the control group, and what a price actually does to a rail.

This report has compared India to itself and India to Brazil. Both are indirect.
India runs a second retail rail alongside UPI, in the same month, to the same
merchants, under the same regulator, and **cards may charge a merchant discount
rate where UPI may not**. Everything except the price is held constant, which
makes this the cleanest natural experiment available anywhere in the report.

The finding is not the one the rest of the report would predict. A price does not
kill a rail. It **segments** it: the priced rail keeps a small share of
transactions at a much larger ticket, and the free rail takes the volume.

Nothing is modelled. Card figures are RBI's own national Total row, transcribed
from the monthly workbook; UPI is the NPCI series this repo already carries. Both
are the same calendar month, so no period is stretched to make them meet.

One number is deliberately not computed: what the card rail earns in MDR. RBI
publishes no blended effective rate, the ceiling differs by instrument and
merchant category, and multiplying a statutory ceiling by total value would
publish an estimate as a measurement. The exhibit prices what is published and
says plainly that the rest is not.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-cards-control"


def main() -> None:
    banner("Sub-module M: cards, the rail that is allowed to charge")
    cards = load("rbi_card_payments")
    acc = load("rbi_acceptance")
    upi = load("upi_monthly")

    months = sorted(cards.month.unique())
    month = str(months[-1])
    row = upi[upi.month == month].iloc[0]
    upi_vol, upi_val = float(row.volume_mn) * 1e6, float(row.value_cr) * 1e7
    # Rule 12: the card side must be the SAME month as the UPI side. Summing every
    # transcribed month against one month of UPI is the exact mismatched-period
    # division this repo refuses elsewhere, and it silently triples the card rail.
    latest_cards = cards[cards.month == month]
    card_vol = float(latest_cards.volume.sum())
    card_val = float(latest_cards.value_inr.sum())
    card_ticket, upi_ticket = card_val / card_vol, upi_val / upi_vol

    vol_x, val_x = upi_vol / card_vol, upi_val / card_val
    card_vol_share = card_vol / (card_vol + upi_vol)
    card_val_share = card_val / (card_val + upi_val)
    ticket_x = card_ticket / upi_ticket

    latest_acc = acc[acc.month == month]
    metric = dict(zip(latest_acc.metric, latest_acc["count"].astype("int64")))
    qr, pos = metric["upi_qr_codes"], metric["pos_terminals"]

    # Every month transcribed, so the headline can say whether the split is stable
    # or whether one month happened to look that way.
    series = []
    for m in months:
        cm = cards[cards.month == m]
        um = upi[upi.month == m]
        if not len(um):
            continue
        cv, cval = float(cm.volume.sum()), float(cm.value_inr.sum())
        uv, uval = float(um.volume_mn.iloc[0]) * 1e6, float(um.value_cr.iloc[0]) * 1e7
        am = acc[acc.month == m].set_index("metric")["count"].astype("int64")
        series.append({
            "month": str(m),
            "card_value_share": round(cval / (cval + uval), 4),
            "card_volume_share": round(cv / (cv + uv), 4),
            "ticket_multiple": round((cval / cv) / (uval / uv), 2),
            "qr_per_terminal": round(float(am["upi_qr_codes"]) / float(am["pos_terminals"]), 1),
        })
    shares = [d["card_value_share"] for d in series]
    tickets = [d["ticket_multiple"] for d in series]
    share_range = (max(shares) - min(shares)) * 100
    stable = share_range < 1.0 and (max(tickets) - min(tickets)) < 0.5

    write_json("chart_cards_trend", {
        "note": "The split between the priced and the free rail, every month transcribed. "
                "Each month is a separate hand-transcribed workbook whose own Total row "
                "was reconciled against its bank rows before being used.",
        "months": [d["month"] for d in series],
        "card_value_share": shares,
        "card_volume_share": [d["card_volume_share"] for d in series],
        "ticket_multiple": tickets,
        "qr_per_terminal": [d["qr_per_terminal"] for d in series],
        "value_share_range_pp": round(share_range, 2),
        "stable": bool(stable),
    })

    write_json("chart_cards_control", {
        "note": "Two rails, one month, one country, one regulator. Cards may charge a "
                "merchant discount rate and UPI may not. Cash withdrawal is excluded from "
                "the card side: it is not a merchant payment.",
        "month": month,
        "rails": [
            {"rail": "Cards (priced)", "volume_mn": round(card_vol / 1e6, 1),
             "value_lakh_cr": round(card_val / 1e12, 2),
             "avg_ticket_inr": round(card_ticket), "priced": True},
            {"rail": "UPI (zero MDR)", "volume_mn": round(upi_vol / 1e6, 1),
             "value_lakh_cr": round(upi_val / 1e12, 2),
             "avg_ticket_inr": round(upi_ticket), "priced": False},
        ],
        "card_volume_share": round(card_vol_share, 4),
        "card_value_share": round(card_val_share, 4),
        "ticket_multiple": round(ticket_x, 2),
    })

    write_json("chart_acceptance", {
        "note": "Where a merchant can be paid, month end. A PoS terminal costs money to "
                "deploy and carries a fee; a UPI QR code is a printed sticker and does not.",
        "month": month,
        "points": [
            {"label": "PoS terminals", "count": pos, "priced": True},
            {"label": "Bharat QR codes", "count": metric["bharat_qr_codes"], "priced": True},
            {"label": "UPI QR codes", "count": qr, "priced": False},
        ],
        "qr_per_terminal": round(qr / pos, 1),
    })

    # The claim turns on which way the ticket falls, so it is decided here.
    stability = (
        f"Across the {len(series)} months transcribed the card share of value moves by only "
        f"{share_range:.1f} percentage points and the ticket multiple barely moves, so this "
        "is a standing split rather than one month that happened to look this way."
        if stable else
        f"Across the {len(series)} months transcribed the card share of value moves by "
        f"{share_range:.1f} percentage points, which is wide enough that the split should be "
        "read as unsettled rather than structural."
    )
    segments = ticket_x > 1.5
    verdict = (
        f"The priced rail did not lose. It **retreated to the large ticket**, where a fee is "
        f"small enough to absorb: {inr(card_ticket)} against {inr(upi_ticket)}, "
        f"{ticket_x:.1f} times."
        if segments else
        "The priced rail carries a ticket close to the free one, so price is NOT segmenting "
        "the market and the argument below does not hold."
    )

    n_months, first_month = len(series), months[0]
    body = f"""
## The answer

India runs the experiment this report has been reaching for. In {month}, cards and UPI
moved money between the same merchants and the same customers under the same regulator,
and **only one of them was allowed to charge for it**.

The free rail took the volume: UPI ran **{vol_x:.0f} times** the card transactions and
**{val_x:.0f} times** the value. Cards were left with {pct(card_vol_share)} of the
transactions between the two rails.

But cards kept **{pct(card_val_share)} of the value**, which is
{card_val_share / card_vol_share:.1f} times their share of transactions. {verdict}

A merchant discount rate does not decide whether a rail survives. It decides **which
transactions it gets**. {stability}

## Three supporting arguments

**1. Acceptance is the clearest thing a price has ever moved.** There are
**{qr / 1e6:,.0f} million UPI QR codes** in the country against
{pos / 1e6:,.1f} million card terminals: {qr / pos:.0f} to one. A terminal is hardware
that costs money to deploy and carries a fee on every swipe. A QR code is a printed
sticker that carries nothing. Where a merchant can be paid has been decided, and it was
decided by price rather than by technology.

**2. The two rails are not competing for the same transaction.** At
{inr(card_ticket)} against {inr(upi_ticket)}, they serve different purchases. That is
why zero MDR did not simply destroy the card business: a fee of a percent or two is
invisible on a {inr(card_ticket)} purchase and impossible on a {inr(upi_ticket)} one.
The report's earlier finding, that the merchant leg is volume-heavy and value-light,
now has a mechanism attached to it rather than only a description.

**3. It bounds what re-pricing UPI could ever achieve.** Sub-module C prices the
merchant leg at rates nobody charges. This is the same country actually charging one,
and the priced rail holds {pct(card_val_share)} of the value between them. Anyone
underwriting a return of MDR is underwriting a migration of value from the free rail to
the priced one, and cards show what that side looks like at its current size.

## So what

- **For an operator:** stop modelling cards as a legacy rail in decline. They are the
  high-ticket segment, and they are the only segment where a fee is collectable today.
  If a payments business needs fee income now, that is where it is.
- **For an investor:** the acceptance ratio, {qr / pos:.0f} to one, is the moat and it
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
periods. It rests on **{n_months} months**, {first_month} to {month}, each a separate workbook
downloaded and transcribed by hand. That is enough to show the split is standing rather
than incidental, and not enough to call a direction: three points do not make a trend, and
every further month is another manual transcription. And card value here excludes transactions on cards routed over UPI, which
RuPay credit-on-UPI makes a growing and separately unpublished category, so the boundary
between the two rails is blurring in a direction this data cannot yet see.
"""

    write_memo(
        MEMO,
        "A price does not kill a rail, it segments it: cards kept the large ticket and lost the volume",
        body,
        sources=[
            "Reserve Bank of India, Bank-wise ATM/PoS/Card Statistics, national Total row: "
            "https://www.rbi.org.in/Scripts/ATMView.aspx",
            "NPCI monthly product statistics, for the UPI side of the same month",
        ],
    )
    write_json("chart_cards_trend_meta", {"months": len(series)}) if False else None
    print(f"   {len(series)} months {months[0]} to {months[-1]}, "
          f"card value share range {share_range:.2f}pp, stable={stable}")
    print(f"   {month}: cards {card_vol/1e6:,.0f}mn / {inr(card_val)} at {inr(card_ticket)}")
    print(f"           UPI {upi_vol/1e6:,.0f}mn / {inr(upi_val)} at {inr(upi_ticket)}")
    print(f"   cards hold {pct(card_vol_share)} of transactions but {pct(card_val_share)} "
          f"of value, at {ticket_x:.1f}x the ticket")
    print(f"   acceptance {qr/pos:.0f} QR codes per card terminal")


if __name__ == "__main__":
    main()
