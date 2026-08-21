"""PhonePe Pulse -> the P2P / merchant / utility split WITHIN each state.

Why this exists. The geographic module previously ranked states by an "intensity
index" of transaction share over value share. That index is algebraically
identical to national_avg_ticket / state_avg_ticket - the same number twice - so
it could never say anything about merchant behaviour that average ticket size did
not already say. Ranking by it was ranking by inverse ticket size.

This fetcher gets the real thing. Pulse publishes the category split per state at
  aggregated/transaction/country/india/state/{slug}/{year}/{q}.json
with the same {name, paymentInstruments[]} shape as the national endpoint, so a
state's merchant share of its own transactions is measured, not inferred - and it
is independent of ticket size.

It also buys a genuine cross-source check: the 36 state files are a different
endpoint from the country file, so their summed Retail count reconciling to the
national Retail count is an independent validation, not a tautology.

Shape verified 2026-08-21:
  aggregated/transaction/.../state/{slug} -> data.transactionData[]
                                            {name, paymentInstruments[]{type,count,amount}}
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    PROCESSED,
    banner,
    expect,
    expect_columns,
    expect_nonempty,
    get_json,
    record_source,
    write_processed,
)

BASE = "https://raw.githubusercontent.com/PhonePe/pulse/main/data/aggregated/transaction/country/india/state"
REPO = "https://github.com/PhonePe/pulse"
MERCHANT = "Retail"          # PhonePe's label for merchant payments
RECON_TOLERANCE = 0.001      # observed ratio is 1.000000 exactly; 0.1% is loose enough
                             # to survive upstream rounding, tight enough that dropping
                             # even a mid-sized state (Kerala is 0.76%) fails the build


def slug(state: str) -> str:
    """Pulse's path segment for a state.

    All 36 names verified 2026-08-21 to resolve under a plain space->hyphen
    substitution, including the ampersand cases ("jammu & kashmir",
    "dadra & nagar haveli & daman & diu"). '&' is not special in a path segment.
    """
    return state.replace(" ", "-")


def load_state_universe() -> tuple[list[str], str]:
    """States and the latest period, taken from the file fetch_pulse just wrote.

    Deliberately not re-derived: the two must agree, so they read one source.
    """
    path = PROCESSED / "pulse_txn_state.csv"
    expect(path.exists(), f"missing {path.name} - fetch_pulse.py must run first")
    df = pd.read_csv(path)
    expect_columns(df, ["period", "state", "count"], "pulse_txn_state")
    period = df.period.max()
    states = sorted(df[df.period == period].state.unique())
    expect(len(states) >= 30, f"expected >=30 states for {period}, got {len(states)}")
    return list(states), period


def fetch_state_mix(states: list[str], period: str) -> pd.DataFrame:
    year, quarter = period[:4], period[-1]
    rows = []
    for state in states:
        url = f"{BASE}/{slug(state)}/{year}/{quarter}.json"
        payload = get_json(url, allow_404=True)
        if not payload:
            print(f"   note: no file for {state} in {period} - left as a gap, not imputed")
            continue
        data = (payload.get("data") or {}).get("transactionData")
        expect(isinstance(data, list), f"state mix {state} {period}: transactionData is not a list")
        expect(bool(data), f"state mix {state} {period}: empty transactionData")
        for entry in data:
            instruments = entry.get("paymentInstruments") or []
            expect(bool(instruments), f"state mix {state} {period}: empty paymentInstruments")
            for inst in instruments:
                rows.append({
                    "period": period,
                    "state": state,
                    "category": entry["name"],
                    "count": int(inst["count"]),
                    "amount_inr": float(inst["amount"]),
                })
    df = pd.DataFrame(rows)
    expect_nonempty(df, "pulse state mix", minimum=90)   # 36 states x 3 categories
    df["avg_ticket_inr"] = df["amount_inr"] / df["count"].where(df["count"] > 0)
    return df.sort_values(["state", "category"]).reset_index(drop=True)


def reconcile(mix: pd.DataFrame, period: str) -> None:
    """Cross-check 36 state files against the separately-fetched country file.

    These are different endpoints. If they disagree, one of them is being read
    wrong, and a silently wrong chart is worse than a broken build.
    """
    path = PROCESSED / "pulse_txn_national.csv"
    expect(path.exists(), f"missing {path.name} - fetch_pulse.py must run first")
    national = pd.read_csv(path)
    national = national[national.period == period]
    expect_nonempty(national, f"pulse_txn_national has no rows for {period}")

    print(f"\n   reconciliation of 36 state files against the country file, {period}")
    for column, unit, scale in (("count", "txns", 1e9), ("amount_inr", "Rs lakh cr", 1e12)):
        state_total = float(mix[column].sum())
        nat_total = float(national[column].sum())
        ratio = state_total / nat_total
        print(f"     {column:<11} states {state_total / scale:8.2f} vs national "
              f"{nat_total / scale:8.2f} {unit:<11} ratio {ratio:.6f}")
        expect(
            abs(ratio - 1.0) <= RECON_TOLERANCE,
            f"state files and country file disagree on {column} for {period}: "
            f"ratio {ratio:.6f}, tolerance {RECON_TOLERANCE}",
        )

    merch = mix[mix.category == MERCHANT]
    expect_nonempty(merch, f"no '{MERCHANT}' rows in the state mix for {period}")
    share = merch["count"].sum() / mix["count"].sum()
    expect(0.3 < share < 0.9, f"implausible national merchant volume share {share:.1%}")
    print(f"     merchant leg = {share:.1%} of transactions across all states")


def main() -> None:
    banner("PhonePe Pulse: within-state category mix")
    states, period = load_state_universe()
    print(f"   {len(states)} states, latest period {period}")
    mix = fetch_state_mix(states, period)
    reconcile(mix, period)

    write_processed(mix, "pulse_txn_state_mix")
    record_source(
        "pulse_txn_state_mix",
        url=REPO,
        publisher="PhonePe Pulse",
        coverage=period,
        rows=len(mix),
        licence="CDLA-Permissive-2.0 (see PhonePe/pulse repository LICENSE)",
        note="P2P / merchant / utility split within each state, from the per-state "
             "aggregated endpoint. Reconciled against the country file. "
             "PhonePe's own transactions, not all of UPI.",
    )

    top = (mix[mix.category == MERCHANT]
           .assign(merchant_share=lambda d: d["count"] /
                   d.state.map(mix.groupby("state")["count"].sum()))
           .nlargest(3, "merchant_share"))
    for r in top.itertuples():
        print(f"   most merchant-heavy: {r.state.title():<22} {r.merchant_share:.1%} of its own txns")


if __name__ == "__main__":
    main()
