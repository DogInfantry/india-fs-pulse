"""Sub-module L: the whole report as one governing thought and three pillars.

A reader currently has to traverse twenty-five exhibits and eleven memos and
assemble the argument themselves. The exec summary lists six findings but does not
say what they add up to, and a list of findings is not an answer.

This module writes that answer once, to `answer.json`, and both the page and the
Word document read it. Writing it twice is how the page and the deliverable drift,
and it is the same reason the memos are f-strings rather than prose.

Nothing here is a new finding. Every figure is lifted from a chart JSON another
module already computed, so this module cannot say anything the evidence does not
already say. It runs last for that reason.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load_json, pct, write_json  # noqa: E402


def main() -> None:
    banner("Sub-module L: the answer, assembled from what the modules computed")
    hero = load_json("upi_monetisation")
    pool = load_json("chart_value_pool")
    biz = load_json("chart_business_models")
    pix = load_json("chart_pix_shape")
    rail = load_json("chart_rail_cost")

    merchant = next(c for c in hero["categories"] if c["category"] == "Retail")
    br = next(r for r in pix["rails"] if r["label"] == "Brazil merchant")
    state_paid = next(r for r in pool["rows"] if r["kind"] == "actual")["value_cr"]
    subsidy_share = state_paid / pool["permitted_pool_cr"]

    models = {c["model"]: c for c in biz["companies"]}
    txn = models["Transactions"]
    infra = models["Infrastructure"]
    best_dist = max((c for c in biz["companies"] if c["model"] == "Distribution"),
                    key=lambda c: c["net_margin_pct"])
    last_rate = [y for y in rail["years"] if y["effective_bps"] is not None][-1]

    governing = (
        f"India's instant rail moved the transactions and not the money, and the price it is "
        f"not permitted to charge is larger than the industry that runs it. The merchant leg "
        f"carries {pct(merchant['volume_share'], 0)} of transactions and "
        f"{pct(merchant['value_share'], 0)} of the value, earns nothing, and would be worth "
        f"{inr(pool['permitted_pool_cr'] * 1e7)} a year at the rate NPCI itself permits. That "
        f"is not a gap any operator can close, so the investable business is the relationship "
        f"the payment creates, not the payment."
    )

    pillars = [
        {
            "n": f"{pct(merchant['volume_share'], 0)} / {pct(merchant['value_share'], 0)}",
            "claim": "The busy leg is the cheap leg, and that is structural rather than Indian.",
            "support": (
                f"Brazil's Pix reaches the same shape, {pct(br['volume_share'], 0)} of "
                f"transactions and {pct(br['value_share'], 0)} of value, under a central bank "
                "that never had a discount rate to remove. Two regulators, one design, one "
                "outcome."),
            "href": "#module-pix",
        },
        {
            "n": inr(pool["permitted_pool_cr"] * 1e7),
            "claim": "What the statute forgoes is larger than what the industry earns.",
            "support": (
                f"Priced at the {pool['permitted_bps']}bps NPCI permits, the merchant leg would "
                f"be worth {pool['times_rail_revenue']:.1f} times {txn['company']}'s entire "
                f"revenue. The state replaces {pct(subsidy_share, 0)} of it with an "
                f"appropriation that has been thinning by arithmetic, from "
                f"{rail['years'][0]['effective_bps']:.2f}bps to "
                f"{last_rate['effective_bps']:.2f}bps."),
            "href": "#module-pool",
        },
        {
            "n": f"{txn['net_margin_pct']:.1f}% vs {infra['net_margin_pct']:.1f}%",
            "claim": "Distribution and infrastructure earn; the transaction does not.",
            "support": (
                f"Filed accounts, same year: {txn['company']} converts "
                f"{txn['net_margin_pct']:.1f}% of the largest revenue in the panel, "
                f"{best_dist['company']} {best_dist['net_margin_pct']:.1f}% selling "
                f"distribution, and {infra['company']}, the one piece of plumbing permitted to "
                f"charge a toll, {infra['net_margin_pct']:.1f}%."),
            "href": "#module-models",
        },
    ]

    write_json("answer", {
        "note": "Assembled from figures other modules computed. This module introduces no "
                "new measurement, which is why it runs last.",
        "governing": governing,
        "pillars": pillars,
    })
    print(f"   governing thought, {len(governing.split())} words, {len(pillars)} pillars")
    for p in pillars:
        print(f"     {p['n']:<22} {p['claim']}")


if __name__ == "__main__":
    main()
