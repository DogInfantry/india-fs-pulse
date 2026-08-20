"""PhonePe Pulse -> national + state transaction data and the user/merchant base.

PRIMARY SOURCE for this project. PhonePe publishes its own transaction data openly
on GitHub, currently through 2026 Q2. It is the only open, current, no-auth source
that splits Indian digital payments into P2P vs merchant vs utility - which is the
whole monetisation question, because MDR applies (or would) only to the merchant leg.

Caveat carried into every chart built on this: these are PhonePe's OWN transactions,
not all of UPI. PhonePe is the largest UPI app, so the mix is indicative of the
market, but the levels are one player's.

Shapes verified 2026-08-20:
  aggregated/transaction -> data.transactionData[]{name, paymentInstruments[]{type,count,amount}}
  aggregated/user        -> data.aggregated.registeredCount
  aggregated/merchant    -> data.aggregated.registeredCount
  map/transaction/hover  -> data.hoverDataList[]{name, metric[]{type,count,amount}}
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    banner,
    expect,
    expect_columns,
    expect_nonempty,
    get_json,
    record_source,
    write_processed,
)

BASE = "https://raw.githubusercontent.com/PhonePe/pulse/main/data"
REPO = "https://github.com/PhonePe/pulse"
START_YEAR = 2018
END_YEAR = date.today().year


def periods():
    for year in range(START_YEAR, END_YEAR + 1):
        for q in (1, 2, 3, 4):
            yield year, q


def fetch_national_transactions() -> pd.DataFrame:
    rows = []
    for year, q in periods():
        url = f"{BASE}/aggregated/transaction/country/india/{year}/{q}.json"
        payload = get_json(url, allow_404=True)
        if not payload:
            continue
        data = (payload.get("data") or {}).get("transactionData")
        expect(isinstance(data, list), f"pulse txn {year}Q{q}: transactionData is not a list")
        for entry in data:
            instruments = entry.get("paymentInstruments") or []
            expect(bool(instruments), f"pulse txn {year}Q{q}: empty paymentInstruments")
            for inst in instruments:
                rows.append({
                    "year": year,
                    "quarter": q,
                    "period": f"{year}Q{q}",
                    "category": entry["name"],
                    "instrument": inst.get("type", "TOTAL"),
                    "count": int(inst["count"]),
                    "amount_inr": float(inst["amount"]),
                })
    df = pd.DataFrame(rows)
    expect_nonempty(df, "pulse national transactions", minimum=100)
    expect_columns(df, ["period", "category", "count", "amount_inr"], "pulse national")
    df["avg_ticket_inr"] = df["amount_inr"] / df["count"].where(df["count"] > 0)
    df["amount_lakh_cr"] = df["amount_inr"] / 1e12  # 1 lakh crore = 1e5 * 1e7 = 1e12
    df["count_bn"] = df["count"] / 1e9
    return df.sort_values(["year", "quarter", "category"]).reset_index(drop=True)


def fetch_state_transactions() -> pd.DataFrame:
    rows = []
    for year, q in periods():
        url = f"{BASE}/map/transaction/hover/country/india/{year}/{q}.json"
        payload = get_json(url, allow_404=True)
        if not payload:
            continue
        hover = (payload.get("data") or {}).get("hoverDataList")
        expect(isinstance(hover, list), f"pulse state {year}Q{q}: hoverDataList is not a list")
        for entry in hover:
            for metric in entry.get("metric") or []:
                rows.append({
                    "year": year,
                    "quarter": q,
                    "period": f"{year}Q{q}",
                    "state": entry["name"],
                    "count": int(metric["count"]),
                    "amount_inr": float(metric["amount"]),
                })
    df = pd.DataFrame(rows)
    expect_nonempty(df, "pulse state transactions", minimum=500)
    df["avg_ticket_inr"] = df["amount_inr"] / df["count"].where(df["count"] > 0)
    return df.sort_values(["year", "quarter", "state"]).reset_index(drop=True)


def _registered(kind: str, year: int, q: int):
    url = f"{BASE}/aggregated/{kind}/country/india/{year}/{q}.json"
    payload = get_json(url, allow_404=True)
    if not payload:
        return None
    agg = (payload.get("data") or {}).get("aggregated") or {}
    value = agg.get("registeredCount")
    return int(value) if value is not None else None


def fetch_base() -> pd.DataFrame:
    rows = []
    for year, q in periods():
        users = _registered("user", year, q)
        merchants = _registered("merchant", year, q)
        if users is None and merchants is None:
            continue
        rows.append({
            "year": year,
            "quarter": q,
            "period": f"{year}Q{q}",
            "registered_users": users,
            "registered_merchants": merchants,
        })
    df = pd.DataFrame(rows)
    expect_nonempty(df, "pulse base", minimum=20)
    return df


def sanity_check(national: pd.DataFrame, base: pd.DataFrame) -> None:
    """Fail loud if the numbers stop making sense. A silently wrong chart is worse
    than a broken build."""
    latest = national[national.period == national.period.max()]
    total_count = latest["count"].sum()
    total_amount = latest["amount_inr"].sum()
    expect(total_count > 0 and total_amount > 0, "latest quarter has no volume")

    shares = latest.groupby("category")["count"].sum() / total_count
    expect(abs(shares.sum() - 1.0) < 1e-9, f"category shares sum to {shares.sum()}, not 1")

    tickets = latest["amount_inr"] / latest["count"]
    expect(
        bool(((tickets > 10) & (tickets < 200000)).all()),
        f"implausible average tickets: {tickets.round(0).tolist()}",
    )
    merchants = base["registered_merchants"].dropna()
    expect(bool(merchants.is_monotonic_increasing), "registered merchants went backwards")

    print(f"\n   sanity ok - latest period {latest.period.iloc[0]}")
    agg = latest.groupby("category")[["count", "amount_inr"]].sum()
    for cat, row in agg.iterrows():
        vol_share = row["count"] / total_count
        val_share = row["amount_inr"] / total_amount
        print(
            f"     {cat:<9} {row['count'] / 1e9:6.2f}bn txns"
            f"   Rs {row['amount_inr'] / 1e12:6.2f} lakh cr"
            f"   avg Rs {row['amount_inr'] / row['count']:,.0f}"
            f"   [{vol_share:.1%} of volume / {val_share:.1%} of value]"
        )


def main() -> None:
    banner("PhonePe Pulse: national transactions")
    national = fetch_national_transactions()
    banner("PhonePe Pulse: state transactions")
    state = fetch_state_transactions()
    banner("PhonePe Pulse: user and merchant base")
    base = fetch_base()

    sanity_check(national, base)

    write_processed(national, "pulse_txn_national")
    write_processed(state, "pulse_txn_state")
    write_processed(base, "pulse_base_national")

    coverage = f"{national.period.min()} - {national.period.max()}"
    entries = [
        ("pulse_txn_national", national, "P2P / Retail (merchant) / Utility split"),
        ("pulse_txn_state", state, "State-level transaction count and value"),
        ("pulse_base_national", base, "Registered users and registered merchants"),
    ]
    for name, df, note in entries:
        record_source(
            name,
            url=REPO,
            publisher="PhonePe Pulse",
            coverage=coverage,
            rows=len(df),
            licence="CDLA-Permissive-2.0 (see PhonePe/pulse repository LICENSE)",
            note=note + ". PhonePe's own transactions, not all of UPI.",
        )


if __name__ == "__main__":
    main()
