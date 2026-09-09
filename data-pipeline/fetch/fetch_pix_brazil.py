"""Brazil's Pix: the only instant rail comparable to UPI, and the only one that publishes fraud.

This repository argues that India's rail separated volume from value and then priced
the busy half at zero. That claim is untestable against a single country. Pix is the
one real comparator: a national instant rail, free to the payer, run by the central
bank, at scale since November 2020, and published as keyless open data.

Two things make it directly comparable rather than merely interesting:

1. `NATUREZA` labels the leg at source. `P2B` is person to business, which is the
   same quantity as PhonePe's merchant leg, so the comparison needs no derivation
   and no assumption about who the counterparty was.
2. `EstatisticasFraudesPix` publishes disputed volume, accepted disputes per 100,000
   transactions, and the share of disputed value returned. India publishes nothing
   equivalent in machine-readable form. That asymmetry is itself a finding.

Nothing here converts a currency. Every comparison this feeds is a share of the same
country's own total, so no FX rate is needed and none is invented (the same reason
`gdp_current_usd` sits unused in the World Bank fetcher).

The Olinda endpoint has three traps, all verified 2026-09-09, all costly if assumed:

  * `Database` is the EARLIEST reference month, not the publication vintage. Every
    response runs cumulatively forward to the latest published month. Asking for
    '202608' returns one month; asking for '202011' returns all seventy.
  * Olinda ignores `$select`, `$count`, `$apply` and `$orderby`. Only `$top` and
    `$format` are honoured, so there is no server-side aggregation and the whole
    cross-tab has to come down and be aggregated here.
  * Some months return a truncated body that does not parse. '202101' and '202401'
    both returned an identical 15,613-byte fragment. The row-count guard below is
    what catches that, and it is a guard rather than a retry because the fault is
    reproducible rather than transient.

Because one pull is roughly 190 MB, the raw payload is cached under data/raw, keyed
on the calendar month. BCB publishes monthly and the CI refresh runs monthly, so the
key matches the real cadence without inventing a staleness heuristic.

Shapes verified 2026-09-09:
  EstatisticasTransacoesPix -> value[]{AnoMes, PAG_PFPJ, REC_PFPJ, PAG_REGIAO,
      REC_REGIAO, PAG_IDADE, REC_IDADE, FORMAINICIACAO, NATUREZA, FINALIDADE,
      VALOR, QUANTIDADE}
  EstatisticasFraudesPix    -> value[]{AnoMes, QtdePixcontestados,
      Qtdecontestacoesaceitas, Qtdecontestacoesrejeitadas,
      Qtdecontestacoesaceitasacada100mil, ValorPixcontestadosaceitos,
      ValorPixdevolvidosintegralmente, ValorPixdevolvidosparcialmente,
      PercentualdeDevolucao, ...}
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    RAW, banner, expect, expect_columns, expect_nonempty, get_json,
    record_source, write_processed,
)

BASE = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata"
TXN_URL = BASE + "/EstatisticasTransacoesPix(Database=@Database)?@Database='{month}'&$format=json"
FRAUD_URL = BASE + "/EstatisticasFraudesPix(Database=@Database)?@Database='{month}'&$format=json"
LANDING = "https://www.bcb.gov.br/estabilidadefinanceira/estatisticaspix"

PIX_LAUNCH = "202011"      # Pix went live 16 November 2020; the series starts there
FRAUD_START = "202201"     # the fraud table starts two years after the rail did

# A short body parses fine and yields a plausible-looking frame, which is the
# dangerous failure. Seventy months of this cross-tab run past 700,000 rows, so
# anything under half a million means the server truncated the response.
MIN_TXN_ROWS = 500_000
MIN_MONTHS = 60
MERCHANT_LEG = "P2B"       # person to business: the same leg as PhonePe's "Retail"
# Legs that must exist. If BCB renames one, every share below silently shifts.
REQUIRED_LEGS = {"P2P", "P2B", "B2B", "B2P"}
# Outside this band the merchant share is not a policy change, it is a units error.
P2B_SHARE_MIN, P2B_SHARE_MAX = 0.01, 0.90

# BCB's own field codes. The English labels are for the chart axis only; the code
# stays in the CSV so nothing depends on this translation. First-appearance months
# are from the data itself and corroborate each reading: AUTO and APDN both start
# 2025-06, INIC starts 2021-12.
INITIATION_LABEL = {
    "QRDN": "Dynamic QR",
    "QRES": "Static QR",
    "DICT": "Pix key",
    "MANU": "Manual entry",
    "INIC": "Payment initiator (open finance)",
    "AUTO": "Pix Automatico (recurring)",
    "APDN": "Contactless, dynamic",
    "APES": "Contactless, static",
    "Nao disponivel": "Not disclosed",
    # BCB leaves the field null on a small number of early rows. That is not the
    # same statement as its own "Nao disponivel" code, so it gets its own bucket
    # rather than being merged into it or, worse, dropped: a dropped grouping key
    # silently removes its transactions from the denominator.
    "Nao informado": "Not reported",
}
NULL_INITIATION = "Nao informado"

FRAUD_COLUMNS = {
    "QtdePixcontestados": "disputed_mn",
    "Qtdecontestacoesaceitas": "disputes_accepted_mn",
    "Qtdecontestacoesrejeitadas": "disputes_rejected_mn",
    "Qtdecontestacoesaceitasacada100mil": "accepted_per_100k_txns",
    "ValorPixcontestadosaceitos": "value_accepted_brl_bn",
    "ValorPixdevolvidosintegralmente": "value_returned_full_brl_bn",
    "ValorPixdevolvidosparcialmente": "value_returned_part_brl_bn",
    "PercentualdeDevolucao": "returned_pct",
}
FRAUD_COUNT_COLS = ["disputed_mn", "disputes_accepted_mn", "disputes_rejected_mn"]
FRAUD_VALUE_COLS = ["value_accepted_brl_bn", "value_returned_full_brl_bn",
                    "value_returned_part_brl_bn"]


def as_month(anomes) -> str:
    """202608 -> '2026-08'. The repo's month grammar, so both rails join on it."""
    s = str(int(anomes))
    expect(len(s) == 6, f"AnoMes is not YYYYMM: {anomes!r}")
    return f"{s[:4]}-{s[4:]}"


def load_transactions() -> pd.DataFrame:
    """Fetch the full cross-tab, or reuse this calendar month's cached pull.

    The cache is keyed on the calendar month rather than on a freshness probe: BCB
    publishes monthly, so a mid-month republication is not picked up until the next
    month. That is a deliberate trade against re-downloading 190 MB on every run.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"pix_transacoes_{date.today():%Y%m}.json"

    if cache.exists():
        print(f"   reusing this month's cached pull: {cache.name}")
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        print(f"   no cache for {date.today():%Y-%m}; pulling the full series (about 190 MB)")
        payload = get_json(TXN_URL.format(month=PIX_LAUNCH), timeout=300)
        cache.write_text(json.dumps(payload), encoding="utf-8")
        print(f"   cached to data/raw/{cache.name}")
        for old in sorted(RAW.glob("pix_transacoes_*.json")):
            if old != cache:
                old.unlink()
                print(f"   removed superseded pull {old.name}")

    rows = (payload or {}).get("value")
    expect(isinstance(rows, list), "pix transactions: 'value' is not a list")
    expect(
        len(rows) >= MIN_TXN_ROWS,
        f"pix transactions: {len(rows):,} rows, expected at least {MIN_TXN_ROWS:,}. "
        "Olinda serves a truncated body for some months; delete the cached file in "
        "data/raw and retry rather than trusting this.",
    )

    df = pd.DataFrame(rows)
    expect_columns(df, ["AnoMes", "NATUREZA", "FORMAINICIACAO", "VALOR", "QUANTIDADE"],
                   "pix transactions")
    df["month"] = df.AnoMes.map(as_month)
    df["VALOR"] = df.VALOR.astype(float)
    df["QUANTIDADE"] = df.QUANTIDADE.astype(float)

    # pandas drops null grouping keys, which would quietly shrink a numerator while
    # leaving its denominator whole. A null leg is unrecoverable, so it fails loud.
    expect(bool(df.NATUREZA.notna().all()),
           f"{int(df.NATUREZA.isna().sum())} rows have no NATUREZA, so no leg share "
           "computed from them can be trusted")
    blank = df.FORMAINICIACAO.isna()
    if bool(blank.any()):
        print(f"   note: {int(blank.sum()):,} rows carry no initiation method "
              f"({df.loc[blank, 'QUANTIDADE'].sum():,.0f} transactions); bucketed as "
              f"{NULL_INITIATION!r} rather than dropped")
        df["FORMAINICIACAO"] = df.FORMAINICIACAO.fillna(NULL_INITIATION)
    return df


def check_months(months: list[str], source: str) -> None:
    """Pix publishes every month. A hole means an upstream change, so say so and
    leave it as a hole: rule 1 forbids interpolating a month nobody published."""
    expect(len(months) >= MIN_MONTHS,
           f"{source}: {len(months)} months, expected at least {MIN_MONTHS}")
    span = pd.period_range(months[0], months[-1], freq="M").astype(str).tolist()
    missing = sorted(set(span) - set(months))
    if missing:
        print(f"   note: {source} has no rows for {', '.join(missing)}; "
              "left as gaps, never interpolated")


def build_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Month by leg, with each leg's share of that month's own national total."""
    g = (df.groupby(["month", "NATUREZA"])[["QUANTIDADE", "VALOR"]].sum()
           .reset_index().rename(columns={"NATUREZA": "leg"}))
    total = df.groupby("month")[["QUANTIDADE", "VALOR"]].sum()
    volume_share = g.QUANTIDADE / g.month.map(total.QUANTIDADE)
    value_share = g.VALOR / g.month.map(total.VALOR)

    legs = set(g.leg)
    expect(REQUIRED_LEGS.issubset(legs),
           f"pix legs missing {sorted(REQUIRED_LEGS - legs)}; got {sorted(legs)}")
    # Check the unrounded shares. Rounding ten legs to six places and then summing
    # accumulates a few parts in a million, which is arithmetic rather than a data
    # fault, so the guard would be measuring this function instead of the source.
    sums = volume_share.groupby(g.month).sum()
    expect(bool(((sums - 1.0).abs() < 1e-9).all()),
           f"per-month leg shares do not sum to 1; worst {float((sums - 1).abs().max()):.2e}")

    g["volume_share"] = volume_share.round(6)
    g["value_share"] = value_share.round(6)
    g["volume_mn"] = (g.QUANTIDADE / 1e6).round(3)
    g["value_brl_bn"] = (g.VALOR / 1e9).round(3)

    out = g[["month", "leg", "volume_mn", "value_brl_bn", "volume_share", "value_share"]]
    return out.sort_values(["month", "leg"]).reset_index(drop=True)


def build_initiation(df: pd.DataFrame) -> pd.DataFrame:
    """How the merchant leg is initiated, as a share of that month's P2B volume.

    Every code is kept, "Nao disponivel" included, because BCB only began breaking
    the method out in 2021-06 and hiding that would turn an undisclosed month into
    an apparent zero. The chart window is the analysis layer's decision, not this
    layer's.
    """
    p2b = df[df.NATUREZA == MERCHANT_LEG]
    expect_nonempty(p2b, f"pix {MERCHANT_LEG} rows", minimum=1000)
    g = (p2b.groupby(["month", "FORMAINICIACAO"])["QUANTIDADE"].sum()
           .reset_index().rename(columns={"FORMAINICIACAO": "initiation"}))
    total = p2b.groupby("month")["QUANTIDADE"].sum()
    p2b_share = g.QUANTIDADE / g.month.map(total)
    sums = p2b_share.groupby(g.month).sum()
    expect(bool(((sums - 1.0).abs() < 1e-9).all()),
           f"per-month initiation shares do not sum to 1; worst {float((sums - 1).abs().max()):.2e}")
    g["p2b_volume_share"] = p2b_share.round(6)
    g["volume_mn"] = (g.QUANTIDADE / 1e6).round(4)

    unknown = sorted(set(g.initiation) - set(INITIATION_LABEL))
    expect(not unknown, f"unmapped Pix initiation codes {unknown}: BCB added a method, "
                        "so INITIATION_LABEL needs extending before the chart can label it")
    g["initiation_label"] = g.initiation.map(INITIATION_LABEL)

    out = g[["month", "initiation", "initiation_label", "volume_mn", "p2b_volume_share"]]
    return out.sort_values(["month", "initiation"]).reset_index(drop=True)


def load_fraud() -> pd.DataFrame:
    payload = get_json(FRAUD_URL.format(month=FRAUD_START), timeout=120)
    rows = (payload or {}).get("value")
    expect(isinstance(rows, list) and bool(rows), "pix fraud: 'value' is empty or not a list")
    raw = pd.DataFrame(rows)
    expect_columns(raw, list(FRAUD_COLUMNS), "pix fraud")

    df = raw[["AnoMes", *FRAUD_COLUMNS]].rename(columns=FRAUD_COLUMNS)
    df.insert(0, "month", raw.AnoMes.map(as_month))
    df = df.drop(columns=["AnoMes"]).sort_values("month").reset_index(drop=True)
    for col in FRAUD_COUNT_COLS:
        df[col] = (df[col].astype(float) / 1e6).round(4)
    for col in FRAUD_VALUE_COLS:
        df[col] = (df[col].astype(float) / 1e9).round(4)
    df["accepted_per_100k_txns"] = df.accepted_per_100k_txns.astype(float).round(3)
    df["returned_pct"] = df.returned_pct.astype(float).round(2)

    expect_nonempty(df, "pix fraud", minimum=24)
    expect(bool(df.returned_pct.between(0, 100).all()),
           f"returned share outside 0 to 100 per cent: {df.returned_pct.tolist()}")
    expect(bool(df.accepted_per_100k_txns.between(0, 10_000).all()),
           f"implausible accepted-dispute rate: {df.accepted_per_100k_txns.tolist()}")
    return df


def main() -> None:
    banner("Banco Central do Brasil: Pix transactions")
    df = load_transactions()
    monthly = build_monthly(df)
    check_months(sorted(monthly.month.unique()), "pix transactions")

    latest = monthly[monthly.month == monthly.month.max()]
    merchant = latest[latest.leg == MERCHANT_LEG].iloc[0]
    expect(P2B_SHARE_MIN <= merchant.volume_share <= P2B_SHARE_MAX,
           f"{MERCHANT_LEG} volume share {merchant.volume_share:.3f} outside "
           f"[{P2B_SHARE_MIN}, {P2B_SHARE_MAX}]: check the units, not the policy")

    banner("Banco Central do Brasil: how the merchant leg is initiated")
    initiation = build_initiation(df)

    banner("Banco Central do Brasil: Pix fraud statistics")
    fraud = load_fraud()

    write_processed(monthly, "pix_txn_monthly")
    write_processed(initiation, "pix_p2b_initiation")
    write_processed(fraud, "pix_fraud_monthly")

    coverage = f"{monthly.month.min()} to {monthly.month.max()}"
    shared = ("`Database` in the Olinda URL is the EARLIEST reference month, not the "
              "publication vintage: each response runs cumulatively forward to the latest "
              "published month. Olinda ignores $select, $count, $apply and $orderby, so the "
              "full cross-tab is downloaded and aggregated locally. No currency is converted "
              "anywhere: every comparison is a share of Brazil's own total.")
    record_source(
        "pix_txn_monthly",
        url=LANDING,
        publisher="Banco Central do Brasil",
        coverage=coverage,
        rows=len(monthly),
        licence="Banco Central do Brasil open data terms",
        note=f"Monthly Pix volume and value by leg, where P2B is person to business and is "
             f"the leg comparable to India's merchant payments. {shared}",
    )
    record_source(
        "pix_p2b_initiation",
        url=LANDING,
        publisher="Banco Central do Brasil",
        coverage=f"{initiation.month.min()} to {initiation.month.max()}",
        rows=len(initiation),
        licence="Banco Central do Brasil open data terms",
        note="How the P2B leg is initiated, as a share of that month's P2B volume. BCB began "
             "breaking the method out in 2021-06; earlier months carry the code 'Nao "
             "disponivel', which is kept rather than dropped so an undisclosed month cannot "
             f"read as a zero. {shared}",
    )
    record_source(
        "pix_fraud_monthly",
        url=LANDING,
        publisher="Banco Central do Brasil",
        coverage=f"{fraud.month.min()} to {fraud.month.max()}",
        rows=len(fraud),
        licence="Banco Central do Brasil open data terms",
        note=f"STALE relative to the transaction series: fraud stops at {fraud.month.max()} "
             f"while transactions run to {monthly.month.max()}. Disputed volume, accepted "
             "disputes per 100,000 transactions, and the share of disputed value returned "
             "through the special return mechanism. No Indian equivalent is published in "
             f"machine-readable form. {shared}",
    )

    disclosed = initiation[initiation.initiation != "Nao disponivel"]
    top = (disclosed[disclosed.month == disclosed.month.max()]
           .nlargest(1, "p2b_volume_share").iloc[0])
    print(f"\n   {monthly.month.max()}: {MERCHANT_LEG} is {merchant.volume_share:.1%} of "
          f"transactions and {merchant.value_share:.1%} of value")
    print(f"   {len(monthly.month.unique())} months, {monthly.month.min()} to {monthly.month.max()}")
    print(f"   merchant leg initiated mostly by {top.initiation_label} "
          f"({top.p2b_volume_share:.1%} of P2B volume)")
    print(f"   fraud series {fraud.month.min()} to {fraud.month.max()}: latest "
          f"{fraud.accepted_per_100k_txns.iloc[-1]:.2f} accepted disputes per 100k, "
          f"{fraud.returned_pct.iloc[-1]:.1f}% of disputed value returned")


if __name__ == "__main__":
    main()
