"""Sub-module J: distribution against transactions, settled with filed accounts.

Every module before this one argues from volumes. Sub-module A shows the merchant
leg earns nothing, H prices what the state pays to keep it that way, and I shows
Brazil arrives at the same structure without ever having had a discount rate to
remove. None of them shows what the alternative earns.

India has listed companies on both sides of the line this report draws. One sells
transactions. Two sell distribution. One sells the piece of infrastructure that is
permitted to charge a toll. They all file audited annual accounts, so the report's
recommendation can be tested against them instead of asserted over them.

The comparison is deliberately narrow. These are not like-for-like companies and
no league table is built here. What travels between them is the SHAPE of the margin
each model produces, and that is the only claim made.

One ratio is refused on purpose. Dividing Paytm's revenue by national UPI volume
would produce a take rate, and it would be meaningless: Paytm's revenue spans
payments, financial services and commerce, and national UPI volume is not its
denominator. Rule 12 forbids exactly that division.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-business-models"
TRANSACTIONS = "Transactions"


def main() -> None:
    banner("Sub-module J: what each business model actually earns")
    df = load("psp_financials")
    hero = load_json("upi_monetisation")
    # fy is written as a four-character string and read back as int64, which numpy
    # will not serialise to JSON. Normalise once, here, rather than at each use.
    df["fy"] = df.fy.astype(str)

    latest = df.sort_values("fy_end").groupby("company").tail(1).sort_values("net_margin_pct")
    rail = latest[latest.model == TRANSACTIONS].iloc[0]
    others = latest[latest.model != TRANSACTIONS]
    dist = others[others.model == "Distribution"].sort_values("net_margin_pct")
    infra = others[others.model == "Infrastructure"].iloc[0]

    paytm = df[df.company == rail.company].sort_values("fy_end")
    peak = paytm.loc[paytm.revenue_cr.idxmax()]
    below_peak = 1 - float(rail.revenue_cr) / float(peak.revenue_cr)

    # --- Exhibit: the latest reported year, by what each business sells
    write_json("chart_business_models", {
        "note": "Filed annual accounts for four listed businesses, grouped by what each "
                "one sells. Named companies rather than cohort averages, because two of "
                "the groups hold a single company.",
        "companies": [
            {"company": r.company, "model": r.model, "sells": r.sells, "fy": r.fy,
             "revenue_cr": float(r.revenue_cr),
             "net_margin_pct": float(r.net_margin_pct),
             "operating_margin_pct": None if r.operating_margin_pct != r.operating_margin_pct
             else float(r.operating_margin_pct)}
            for r in latest.itertuples()
        ],
    })

    # --- Exhibit: how each margin got where it is
    years = sorted(df.fy.unique())
    write_json("chart_margin_trajectory", {
        "note": "Net margin on filed annual accounts. A company reads null in a year it "
                "had not listed or did not report, never zero.",
        "years": years,
        "series": [
            {"company": c, "model": g.model.iloc[0],
             "values": [
                 (lambda s: None if not len(s) else float(s.iloc[0]))(g[g.fy == y].net_margin_pct)
                 for y in years
             ]}
            for c, g in df.groupby("company")
        ],
    })

    # --- Claims that turn on which way the numbers fall, decided here rather than typed
    dist_beats = bool(dist.net_margin_pct.min() > rail.net_margin_pct)
    verdict = (
        "Every distribution business in the panel earns a wider margin than the "
        "transaction business."
        if dist_beats else
        "At least one distribution business earns a NARROWER margin than the transaction "
        "business, which weakens the recommendation this report has been making."
    )
    profitable = float(rail.net_margin_pct) > 0
    rail_state = (
        f"turned its first profit, at {rail.net_margin_pct:.1f}% net margin"
        if profitable else
        f"is still loss-making, at {rail.net_margin_pct:.1f}% net margin"
    )
    shrunk = (
        f" It did so on revenue **{pct(below_peak)} below its own FY{peak.fy} peak**, which "
        "is the shape of a business that got better by getting smaller."
        if below_peak > 0.01 else ""
    )
    gap = float(dist.net_margin_pct.max()) - float(rail.net_margin_pct)

    body = f"""
## The answer

The report has argued that the investable business here is distribution rather than
transactions. Four listed companies file accounts that test it, and they agree.

In FY{rail.fy} the transaction business, {rail.company}, {rail_state}.{shrunk} In the same
year {dist.iloc[-1].company} earned **{dist.iloc[-1].net_margin_pct:.1f}%** and
{dist.iloc[0].company} **{dist.iloc[0].net_margin_pct:.1f}%** selling distribution, and
{infra.company}, which operates the piece of market infrastructure that **is** permitted
to charge a toll, earned **{infra.net_margin_pct:.1f}%**. {verdict}

The ordering is the finding: the further a business sits from the transaction and the
closer to the relationship or the toll, the wider the margin.

## Three supporting arguments

**1. The rail is the thinnest margin in the panel, at its best year yet.**
{rail.company} carries the largest revenue of the four at
Rs {rail.revenue_cr:,.0f} crore and converts the least of it, {rail.net_margin_pct:.1f}%,
against {dist.net_margin_pct.max():.1f}% at the best distribution business: a gap of
{gap:.1f} percentage points. Scale is not the constraint. Price is, which is what
sub-module A said from the volume side and what sub-module H priced at
{pct(hero["merchant_volume_share"])} of transactions earning nothing.

**2. Infrastructure that may charge a toll earns like infrastructure that may charge a
toll.** {infra.company} runs on the smallest revenue in the panel,
Rs {infra.revenue_cr:,.0f} crore, and returns {infra.net_margin_pct:.1f}%. It is the
control case for the whole report: identical in kind to a payment rail, a piece of
plumbing everyone must cross, and the difference in outcome is that its crossing has a
price. UPI's does not.

**3. Distribution scales without the rail's cost base.** Both distribution businesses
in the panel earn more per rupee of revenue than the transaction business while running
a fraction of its revenue. That is the merchant-side flywheel sub-module A recommended,
visible in filed accounts rather than argued from first principles.

## So what

- **For an operator:** the pathway ranking in the diligence memo survives contact with
  audited accounts. Build toward the products the payment relationship carries, and treat
  the transaction as the acquisition cost it is.
- **For an investor:** the transaction business is the one that took the longest to earn
  anything and earns least now. Underwrite the distribution attached to it, not the
  volume running through it.
- **For a policymaker:** a rail whose only listed operator reached breakeven this
  recently is not a sector that can absorb a further pricing cut. Sub-module H already
  shows the state's own subsidy thinning by arithmetic.

## Method and its limits

Four filed annual income statements, retrieved through the same library the banking
module already uses. Margins are computed from revenue and reported net income; nothing
is estimated and no figure is typed in.

What this cannot support. These are **not like-for-like companies**: different revenue
recognition, different perimeters, different regulators, and one of them is a regulated
monopoly. Only the shape of the margin each model produces is compared, never a ranking
of management. It is a **panel of named companies, not cohort averages**, because two of
the three groups hold a single company and an average of one is not an average. Four
companies also cannot stand in for a sector, and a bad year at any of them would move the
comparison, which is why the verdict above is computed rather than asserted. Finally,
this module says nothing about consumer credit, which remains the largest gap on the
coverage map: distribution here means insurance and broking, the two that happen to be
listed as near-pure plays.
"""

    write_memo(
        MEMO,
        "The listed accounts agree with the recommendation: distribution earns, transactions do not",
        body,
        sources=[
            "Filed annual income statements via Yahoo Finance (yfinance): One97 (Paytm), "
            "PB Fintech, Angel One and CDSL",
            "PhonePe Pulse, for the merchant-leg share this is set against",
        ],
    )
    for r in latest.itertuples():
        print(f"   {r.model:<14} {r.company:<16} FY{r.fy}  Rs {r.revenue_cr:>6,.0f}cr  "
              f"net {r.net_margin_pct:>6.1f}%")
    print(f"   distribution beats transactions: {dist_beats}; widest gap {gap:.1f}pp")


if __name__ == "__main__":
    main()
