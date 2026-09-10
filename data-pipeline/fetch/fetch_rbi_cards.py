"""India's own control group: the card rail, which is allowed to charge.

Every comparison in this report so far is either India against itself or India
against Brazil. Both are useful and both are indirect. India runs a second
retail payment rail alongside UPI, in the same market, to the same merchants,
under the same regulator, and **cards are permitted a merchant discount rate
where UPI is not**. That is a natural experiment, and it is stronger than any
cross-country comparison because everything except the price is held constant.

Browser-only, per decision 2. `Scripts/ATMView.aspx` answers a script with HTTP
200, which is misleading: the monthly XLSX links it lists return an HTML
interstitial to a plain client and fail outright to a browser user agent. So the
workbook is downloaded by hand and its national `Total` row transcribed into
`data/manual/`, exactly as the NPCI and PIB tables are. See `docs/resources.md`.

The transcription carries its own cross-check. RBI publishes a `Total` row and 63
bank rows; the two reconciled at 0.00% on every column transcribed, which is why
the figure is trusted. Cash withdrawal is excluded throughout: it is a cash
logistics event, not a merchant payment, and including it would inflate the
priced rail with transactions no merchant ever accepted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    MANUAL, banner, expect, expect_columns, expect_nonempty,
    read_seeded_csv, record_source, write_processed,
)

SOURCE_URL = "https://www.rbi.org.in/Scripts/ATMView.aspx"
# Outside this band a card average ticket is a units error, not a market shift.
# The workbook states value in Rs'000 and the seed converts it; this catches a
# future transcription that forgets to.
TICKET_MIN_INR, TICKET_MAX_INR = 100.0, 60_000.0


def load_seed(name: str, cols: list[str]) -> pd.DataFrame:
    path = MANUAL / f"{name}.csv"
    expect(path.exists(),
           f"missing {path.name}. Download the month's workbook from {SOURCE_URL} and "
           "transcribe its Total row; see docs/resources.md")
    df = read_seeded_csv(path)
    expect_columns(df, cols, name)
    expect_nonempty(df, name, minimum=1)
    for col in ("source_url", "accessed"):
        expect(df[col].notna().all(), f"{name}: every row needs {col}")
    return df


def main() -> None:
    banner("RBI: the card rail, India's priced control group")

    pay = load_seed("rbi_card_payments",
                    ["month", "instrument", "channel", "volume", "value_inr",
                     "source_url", "accessed"])
    acc = load_seed("rbi_acceptance", ["month", "metric", "count", "source_url", "accessed"])

    pay["volume"] = pay.volume.astype("int64")
    pay["value_inr"] = pay.value_inr.astype(float)
    pay["avg_ticket_inr"] = (pay.value_inr / pay.volume).round(0)

    tickets = pay.avg_ticket_inr
    expect(bool(tickets.between(TICKET_MIN_INR, TICKET_MAX_INR).all()),
           f"card average ticket outside [{TICKET_MIN_INR:,.0f}, {TICKET_MAX_INR:,.0f}]: "
           f"{tickets.tolist()}. The workbook states value in Rs'000; check the conversion")
    expect(set(pay.instrument) == {"credit_card", "debit_card"},
           f"unexpected instruments {sorted(set(pay.instrument))}")

    # Cross-source check against the UPI series for the same month. These are two
    # rails, not two readings of one quantity, so no agreement is expected: what is
    # checked is that the priced rail is the SMALLER one, because a card leg larger
    # than UPI would mean a month or a unit has been transcribed wrong.
    upi_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "upi_monthly.csv"
    months = sorted(pay.month.unique())
    if upi_path.exists():
        upi = pd.read_csv(upi_path)
        for month in months:
            row = upi[upi.month == month]
            expect(len(row) == 1,
                   f"upi_monthly has no row for {month}, so that month cannot be compared")
            upi_val = float(row.value_cr.iloc[0]) * 1e7
            card_val = float(pay[pay.month == month].value_inr.sum())
            expect(card_val < upi_val,
                   f"card value Rs {card_val/1e12:.2f} lakh cr exceeds UPI's "
                   f"Rs {upi_val/1e12:.2f} lakh cr in {month}; check the month and the units")
            print(f"   cross-rail ok {month}: cards Rs {card_val/1e12:.2f} lakh cr "
                  f"against UPI Rs {upi_val/1e12:.2f} lakh cr")
        # Months must be contiguous, or a trend drawn on them lies about elapsed time.
        span = pd.period_range(months[0], months[-1], freq="M").astype(str).tolist()
        missing = sorted(set(span) - set(months))
        if missing:
            print(f"   note: no workbook transcribed for {', '.join(missing)}; "
                  "left as a gap, never interpolated")

    write_processed(pay, "rbi_card_payments")
    write_processed(acc, "rbi_acceptance")

    note = ("Browser-only: RBI's listing page answers a script but its XLSX links return an "
            "interstitial, so the monthly workbook is downloaded by hand and its national "
            "Total row transcribed. That Total reconciled against the sum of 63 bank rows at "
            "0.00% on every column. Cash withdrawal is excluded: it is not a merchant payment. "
            "Cards are the PRICED rail: a merchant discount rate is permitted on them and "
            "prohibited on UPI, which is what makes them a control group rather than a rival.")
    for name, df in (("rbi_card_payments", pay), ("rbi_acceptance", acc)):
        record_source(
            name,
            url=SOURCE_URL,
            publisher="Reserve Bank of India",
            coverage=f"{df.month.min()} to {df.month.max()}, national totals",
            rows=len(df),
            licence="Reserve Bank of India terms; data is provisional as published",
            note=note,
        )

    print(f"\n   {len(months)} month(s): {months[0]} to {months[-1]}")
    for month in months:
        m = pay[pay.month == month]
        vol, val = float(m.volume.sum()), float(m.value_inr.sum())
        a = acc[acc.month == month].set_index("metric")["count"]
        print(f"   {month}  cards {vol/1e6:>7.1f}mn  Rs {val/1e12:>5.2f} lakh cr  "
              f"avg Rs {val/vol:>6,.0f}  QR/PoS {a['upi_qr_codes']/a['pos_terminals']:>5.0f}x")


if __name__ == "__main__":
    main()
