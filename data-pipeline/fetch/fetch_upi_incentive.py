"""What the zero-MDR rail actually costs, and who pays it.

The rest of this pipeline prices the merchant leg at zero, which is true of the
discount rate and false of the system. Merchants pay nothing because the state
pays instead: acquiring banks receive an incentive of 0.15% on low-value merchant
transactions, and that money is appropriated, disbursed and published.

Two hand-seeded tables, both from the same PIB release, both browser-only:

1. data/manual/govt_upi_incentive.csv    year-wise incentive actually paid
2. data/manual/npci_upi_value_split.csv  national UPI value, P2M against P2P

The second is worth as much as the first. PhonePe Pulse gives a merchant split
for one operator's book; this is the split for the whole country, which is the
base the subsidy has to be measured against, and it lets the two be reconciled.

The number this produces is a BLENDED rate: incentive paid divided by ALL
merchant value. It is deliberately not the statutory rate. The statutory 0.15%
applies only to transactions at or under Rs 2,000 to small merchants, and no
open source publishes the share of merchant value that qualifies. Blending over
the whole leg needs no assumption about that share, and it is the number a
policymaker is actually spending: what the state pays per rupee of merchant
volume it is subsidising. Both sides are measured. Neither is estimated.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    MANUAL, PROCESSED, banner, expect, expect_columns, expect_nonempty,
    read_seeded_csv, record_source, today, write_processed,
)

SOURCE_URL = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2114335"
STATUTORY_RATE_PCT = 0.15
# A blended rate outside this band means a transcription slip or a units error,
# not a policy change. Fail rather than publish it.
BPS_MIN, BPS_MAX = 1.0, 40.0


def load_seed(name: str, cols: list[str]) -> pd.DataFrame:
    path = MANUAL / f"{name}.csv"
    expect(path.exists(), f"missing {path.name}: see docs/REFRESH.md for how to transcribe it")
    df = read_seeded_csv(path)
    expect_columns(df, cols, name)
    expect_nonempty(df, name, minimum=3)
    # Rule 2: a hand-seeded row without provenance is worse than no row.
    for col in ("source_url", "accessed"):
        expect(df[col].notna().all(), f"{name}: every row needs {col}")
    return df


def main() -> None:
    banner("Government incentive on low-value merchant UPI")

    pay = load_seed("govt_upi_incentive",
                    ["fy", "payout_cr", "status", "rate_pct", "ceiling_inr", "scope"])
    val = load_seed("npci_upi_value_split",
                    ["fy", "months", "total_lakh_cr", "p2m_lakh_cr", "p2p_lakh_cr"])

    expect(bool((pay.rate_pct == STATUTORY_RATE_PCT).all()),
           f"incentive rate is no longer a flat {STATUTORY_RATE_PCT}%; the exhibit assumes one rate")
    expect(bool(pay.payout_cr.between(100, 20_000).all()),
           f"payout outside Rs 100 to 20,000 crore: {pay.payout_cr.tolist()}")

    # The published labels are rounded to 0.1 lakh crore, so the legs sum to the
    # total only to that precision. Anything wider is a transcription error.
    residual = (val.p2m_lakh_cr + val.p2p_lakh_cr - val.total_lakh_cr).abs()
    expect(bool((residual <= 0.15).all()),
           f"P2M + P2P does not reconcile to the published total: {residual.tolist()}")

    df = pay.merge(val, on="fy", how="left", suffixes=("", "_val"))
    expect(df.p2m_lakh_cr.notna().all(), "a payout year has no matching national value row")

    # Divide only where the outlay and the value base cover the same window. The
    # FY2024-25 row is a full-year outlay against ten months of value, and a
    # ratio across mismatched periods is not a rate.
    full_year = df.months == 12
    df["effective_bps"] = pd.NA
    df.loc[full_year, "effective_bps"] = (
        df.loc[full_year, "payout_cr"] * 1e7 / (df.loc[full_year, "p2m_lakh_cr"] * 1e12) * 10_000
    ).round(2)
    df["rate_basis"] = df.months.map(lambda m: "full year" if m == 12 else "not computed: part-year base")

    computed = df.effective_bps.dropna().astype(float)
    expect(len(computed) >= 3, "fewer than three comparable years; the trend claim needs three")
    expect(bool(computed.between(BPS_MIN, BPS_MAX).all()),
           f"blended rate outside [{BPS_MIN}, {BPS_MAX}]bps: {computed.tolist()}")

    # Cross-source check against PhonePe Pulse. The two measure different things,
    # one operator against the country, so they are not expected to match; a wild
    # divergence would mean one of them is being read wrong.
    pulse_path = PROCESSED / "pulse_txn_national.csv"
    if pulse_path.exists():
        pulse = pd.read_csv(pulse_path)
        latest = pulse[pulse.period == pulse.period.max()]
        pulse_share = float(
            latest[latest.category == "Retail"].amount_inr.sum() / latest.amount_inr.sum())
        national_share = float(val.p2m_lakh_cr.iloc[-1] / val.total_lakh_cr.iloc[-1])
        expect(abs(pulse_share - national_share) < 0.15,
               f"PhonePe merchant value share {pulse_share:.1%} against national "
               f"{national_share:.1%}: one of the two is being read wrong")
        print(f"   cross-source ok: PhonePe {pulse_share:.1%} of value is merchant, "
              f"national {national_share:.1%}")

    write_processed(df, "upi_incentive")
    record_source(
        "upi_incentive",
        url=SOURCE_URL,
        publisher="Press Information Bureau, Ministry of Finance",
        coverage=f"FY{df.fy.iloc[0]} to FY{df.fy.iloc[-1]}, incentive payout and national UPI value split",
        rows=len(df),
        licence="Government of India, PIB terms",
        note="Hand-transcribed in a browser: PIB serves HTTP 403 to scripted requests, and the "
             "figures are published as chart images with printed data labels. The blended rate is "
             "incentive paid over ALL merchant value, not the statutory 0.15%, which applies only "
             "to transactions at or under Rs 2,000 to small merchants. STALE: the release stops at "
             f"FY2024-25 and was accessed {today()}.",
    )

    for r in df.itertuples():
        rate = f"{float(r.effective_bps):5.2f}bps" if pd.notna(r.effective_bps) else "     n/a"
        print(f"   FY{r.fy}  Rs {r.payout_cr:>5,}cr {r.status:<9} on Rs {r.p2m_lakh_cr:>5.1f} "
              f"lakh cr of merchant value  ->  {rate}  ({r.rate_basis})")


if __name__ == "__main__":
    main()
