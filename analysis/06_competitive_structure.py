"""Sub-module F: market structure and the 30% share cap.

Governing thought: India's payments market is concentrated AND unmonetised at
the same time. Two apps intermediate roughly four in five transactions and earn
nothing on them, which is why the cap is contested, and why the arithmetic of
enforcing it by December 2026 does not work.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, pct, write_json, write_memo  # noqa: E402

CAP = 0.30           # NPCI's per-app volume share cap
RESIDUAL = "All other apps"


def main() -> None:
    banner("Sub-module F: market structure and the share cap")
    apps = load("upi_apps")
    hhi = load("upi_apps_hhi")
    national = load("kpi_upi_trend")

    latest_month = apps.month.max()
    latest = apps[apps.month == latest_month].sort_values("volume_share", ascending=False)
    nat_vol_mn = float(latest.nat_volume_mn.iloc[0])

    breaching = latest[(latest.volume_share > CAP) & (latest.app != RESIDUAL)]
    excess_pp = (breaching.volume_share - CAP).sum()
    excess_mn = excess_pp * nat_vol_mn

    leaders = latest[latest.app != RESIDUAL].head(2)
    top2_vol = leaders.volume_share.sum()
    top2_val = leaders.value_share.sum()

    # Is concentration falling fast enough to comply by the deadline?
    hhi_open, hhi_close = float(hhi.hhi.iloc[0]), float(hhi.hhi.iloc[-1])
    months_elapsed = len(hhi) and (
        (int(latest_month[:4]) - int(hhi.month.iloc[0][:4])) * 12
        + int(latest_month[5:]) - int(hhi.month.iloc[0][5:])
    )
    top_app = leaders.iloc[0]
    first = apps[(apps.month == apps.month.min()) & (apps.app == top_app.app)]
    share_then = float(first.volume_share.iloc[0]) if len(first) else float("nan")
    drift_pp_per_month = (top_app.volume_share - share_then) / months_elapsed
    months_to_cap = (
        (top_app.volume_share - CAP) / -drift_pp_per_month if drift_pp_per_month < 0 else float("inf")
    )

    tickets = latest[latest.app != RESIDUAL].sort_values("avg_ticket_inr")
    cheapest, dearest = tickets.iloc[0], tickets.iloc[-1]

    write_json("chart_market_structure", {
        "month": latest_month,
        "cap": CAP,
        "national_volume_mn": round(nat_vol_mn, 2),
        "cap_excess_share": round(float(excess_pp), 4),
        "cap_gap_txns_mn": round(float(excess_mn), 1),
        "top2_volume_share": round(float(top2_vol), 4),
        "note": "Column width is share of transactions; height is share of value. "
                "Shares are of the NPCI national total, so the residual is real.",
        "apps": [
            {"app": r.app, "volume_share": round(r.volume_share, 4),
             "value_share": round(r.value_share, 4),
             "avg_ticket_inr": round(r.avg_ticket_inr, 0),
             "breaches_cap": bool(r.volume_share > CAP and r.app != RESIDUAL)}
            for r in latest.itertuples()
        ],
    })

    trend_apps = [a for a in apps[apps.app != RESIDUAL].app.unique()][:6]
    write_json("chart_share_trend", {
        "cap": CAP,
        "months": sorted(apps.month.unique()),
        "note": f"Share of national UPI volume. The dashed line is the {CAP:.0%} cap.",
        "series": [
            {"app": a,
             "values": [
                 (lambda s: round(float(s.iloc[0]), 4) if len(s) else None)(
                     apps[(apps.month == m) & (apps.app == a)].volume_share)
                 for m in sorted(apps.month.unique())
             ]}
            for a in trend_apps
        ],
    })

    write_json("chart_hhi", {
        "note": "Herfindahl-Hirschman Index on true national volume shares, 0-10,000 scale.",
        "months": hhi.month.tolist(),
        "values": [round(float(v)) for v in hhi.hhi],
    })

    runway = (
        f"about {months_to_cap:.0f} months at the observed rate"
        if months_to_cap != float("inf") and months_to_cap < 600
        else "never, at the observed rate"
    )
    deadline_gap = "already past" if latest_month >= "2026-12" else "December 2026"

    body = f"""
## The answer

India's payments market is **concentrated and unmonetised at the same time**, and
that combination is what makes the share cap unenforceable as written. In
{latest_month}, {leaders.iloc[0].app} held **{pct(leaders.iloc[0].volume_share)}** of national
UPI volume and {leaders.iloc[1].app} **{pct(leaders.iloc[1].volume_share)}**, together
**{pct(top2_vol)} of every transaction in the country and {pct(top2_val)} of the value**.
NPCI's cap is {pct(CAP, 0)} per app. Both leaders breach it, and neither earns a
rupee of MDR on the volume that puts them in breach.

To comply by {deadline_gap}, **{excess_mn / 1000:.1f} billion transactions a month**
would have to change app, {pct(excess_pp)} of the entire national market, relocated
inside a policy window. That is the whole argument in one number.

## Three supporting arguments

**1. The gap is not closing at anything like the required rate.**
{top_app.app}'s share has moved from {pct(share_then)} in {apps.month.min()} to
{pct(top_app.volume_share)} in {latest_month}: a drift of
{drift_pp_per_month * 100:+.2f} percentage points a month. Extrapolated, reaching
{pct(CAP, 0)} takes {runway}. Market concentration overall tells the same story: the
HHI has fallen from **{hhi_open:,.0f} to {hhi_close:,.0f}** over {months_elapsed} months,
which is real movement but still leaves the market highly concentrated by any
competition-authority standard.

**2. The challengers taking share are not substitutes for the leaders.** Average
ticket size separates them completely: {dearest.app} runs
{inr(dearest.avg_ticket_inr)} a transaction while {cheapest.app} runs
{inr(cheapest.avg_ticket_inr)}: a {dearest.avg_ticket_inr / cheapest.avg_ticket_inr:.0f}x
spread across apps on the same rails. These are different businesses serving
different customers, not rivals competing for the same payment. Share cannot simply
be redistributed from a leader to a challenger, because the challengers are not
built to absorb general-purpose everyday spend.

**3. Nobody is fighting for share that pays.** The leaders' value share
({pct(top2_val)}) runs *above* their volume share ({pct(top2_vol)}), so they carry the
larger transactions too, and under zero MDR that additional value converts to no
additional revenue. A cap is normally a remedy for market power being *exploited*.
Here the market power produces no direct rent, which is why the deadline has moved
before and why enforcement pressure is structurally weak.

## So what

- **Do not underwrite a plan that assumes the cap binds on schedule.** The
  arithmetic above ({excess_mn / 1000:.1f}bn transactions a month) is the reason. Treat
  the cap as a step-function risk with a low probability in any given quarter, not
  as a dated event.
- **If it does bind, the beneficiary is not the runner-up.** Redistribution would
  have to go to apps whose average ticket says they serve a different customer.
  Model the transition cost, not just the share transfer.
- **This reframes the monetisation question.** Concentration is not the reason the
  rails are unprofitable: price is. Splitting {pct(top2_vol)} of the market three ways
  changes who processes a free transaction, not whether it is free.

## Method and its limits

NPCI publishes the top ten apps by volume and no more, so the tenth-place cutoff
moves between months and a smaller app can drop out of view. Shares are computed
against the **NPCI national monthly total**, not against the sum of the ten, so
they are true market shares and the "{RESIDUAL}" residual is genuine rather than a
rounding artefact. The ten reconcile to between
{apps[apps.app != RESIDUAL].groupby('month').volume_share.sum().min():.1%} and
{apps[apps.app != RESIDUAL].groupby('month').volume_share.sum().max():.1%} of national
volume across the period: an independent cross-check between two separately
transcribed NPCI tables. The series starts {apps.month.min()} because NPCI renders
earlier months alphabetically rather than by size, capped at ten rows, which omits
the leaders entirely.
"""
    write_memo("pov-market-structure",
               "Concentrated and unmonetised at once, which is why the share cap cannot bind",
               body,
               sources=["NPCI UPI Ecosystem Statistics, per-application volume and value",
                        "NPCI monthly product statistics, national totals"])
    print(f"   {latest_month}: {leaders.iloc[0].app} {leaders.iloc[0].volume_share:.1%}, "
          f"{leaders.iloc[1].app} {leaders.iloc[1].volume_share:.1%}, top-2 {top2_vol:.1%}")
    print(f"   cap gap: {excess_mn / 1000:.1f}bn txns/month must move; HHI {hhi_open:,.0f} -> {hhi_close:,.0f}")


if __name__ == "__main__":
    main()
