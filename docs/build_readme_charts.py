#!/usr/bin/env python
"""Draw the README's exhibits, and refresh its generated regions.

The README is the front door of a repository whose whole claim is that no figure
is typed in by hand. So the README does not type them in either: this script
reads the same computed JSON the site reads, emits four SVG exhibits into
`docs/assets/`, and rewrites two marker-delimited regions inside `README.md`.

Stdlib only, on purpose. The pipeline already carries pandas; a README chart is
not a reason to add a plotting dependency. Output is deterministic (no clock, no
randomness, coordinates rounded), so `python run.py analyze` twice in a row
leaves the working tree clean.

Every exhibit is drawn on the project's own dark card, which is why one file
works on both GitHub themes: the card supplies its own background rather than
borrowing the page's.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "src" / "data"
OUT = ROOT / "docs" / "assets"
README = ROOT / "README.md"

# Palette lifted from site/src/styles/tokens.css. Never invent a hex here: the
# README should look like the site, not like a second design system.
BG = "#0C0F14"        # --ink
GRID = "#1E262F"      # --line-soft
BORDER = "#262F3B"    # --line
TEXT = "#E9EDF2"      # --text
TEXT2 = "#A6B0BE"     # --text-2
TEXT3 = "#7F8A97"     # --text-3
S1 = "#C02734"        # --s1 crimson: the subject
S2 = "#1F7A8C"        # --s2 teal: the comparator
S4 = "#5B6673"        # --s4 grey: context
SIGNAL_TEXT = "#DF5F6A"   # --signal-text: small red type needs 4.5:1
SOFT = "rgba(192,39,52,0.10)"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"

W = 960
PAD = 34


def load(name: str):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(v) -> str:
    """Round for the wire. Keeps output byte-identical between runs."""
    r = round(float(v), 1)
    return f"{int(r)}" if r == int(r) else f"{r}"


def txt(x, y, s, size=12, fill=TEXT2, anchor="start", weight="400",
        family=SANS, opacity=None) -> str:
    extra = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{n(x)}" y="{n(y)}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f'{esc(s)}</text>')


def rect(x, y, w, h, fill, rx=0, stroke=None, opacity=None) -> str:
    extra = f' stroke="{stroke}"' if stroke else ""
    extra += f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{rx}" '
            f'fill="{fill}"{extra}/>')


def line(x1, y1, x2, y2, stroke, width=1, dash=None, opacity=None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    extra += f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
            f'stroke="{stroke}" stroke-width="{width}"{extra}/>')


def polyline(pts, stroke, width=2.4, dash=None) -> str:
    d = " ".join(f"{n(x)},{n(y)}" for x, y in pts)
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{d}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linejoin="round" '
            f'stroke-linecap="round"{extra}/>')


def dot(cx, cy, r, fill) -> str:
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{r}" fill="{fill}"/>'


def card(height: int, title: str, deck: str, body: list, source: str, alt: str) -> str:
    """The shared frame: crimson rule, action title, deck, plot, source line."""
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="{W}" height="{height}" role="img" aria-label="{esc(alt)}">',
        f"<title>{esc(alt)}</title>",
        rect(0, 0, W, height, BG, rx=14),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="13.5" '
        f'fill="none" stroke="{BORDER}"/>',
        rect(PAD, 30, 3, 21, S1),
        txt(PAD + 13, 47, title, size=20, fill=TEXT, weight="600", family=SERIF),
        txt(PAD + 13, 70, deck, size=13, fill=TEXT2),
        line(PAD, height - 42, W - PAD, height - 42, GRID),
        txt(PAD, height - 22, source, size=10.5, fill=TEXT3),
    ]
    return "\n".join(head + body + ["</svg>", ""])


def write_svg(name: str, svg: str) -> None:
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"   docs/assets/{name}.svg")


# --------------------------------------------------------------- exhibit A
def monetisation_gap():
    """Paired bars: share of transactions against share of value, by leg."""
    d = load("chart_category_split")
    rows = [
        ("Merchant (Retail)", "Retail"),
        ("Person to person", "P2P"),
        ("Utility and bills", "Utility"),
    ]
    by = {s["category"]: s for s in d["series"]}

    H = 418
    x0, x1 = PAD + 172, W - PAD - 96
    top, row_h = 134, 72
    # The merchant row carries a callout beneath it, so every row below it drops
    # by that much. Without the offset the callout lands on the next label.
    drop = 18
    axis_y = top + 2 * row_h + drop + 52

    def sx(v):
        return x0 + (x1 - x0) * (v / 0.80)

    b = []
    # Legend spelled out in words, so the chart survives being read on its own.
    b.append(rect(PAD + 13, 92, 10, 10, S1, rx=2))
    b.append(txt(PAD + 31, 101, "Share of transactions", size=12))
    b.append(rect(PAD + 186, 92, 10, 10, S4, rx=2))
    b.append(txt(PAD + 204, 101, "Share of rupees moved", size=12))

    for g in (0.2, 0.4, 0.6, 0.8):
        b.append(line(sx(g), top - 14, sx(g), axis_y - 14, GRID))
        b.append(txt(sx(g), axis_y, f"{int(g * 100)}%", size=10.5,
                     fill=TEXT3, anchor="middle"))

    for i, (label, key) in enumerate(rows):
        s = by[key]
        y = top + i * row_h + (drop if i else 0)
        lead = key == "Retail"
        b.append(txt(PAD + 13, y + 8, label, size=13,
                     fill=TEXT if lead else TEXT2,
                     weight="600" if lead else "400"))
        b.append(txt(PAD + 13, y + 26,
                     f"avg ticket Rs {int(s['avg_ticket_inr']):,}", size=11, fill=TEXT3))

        vol, val = s["volume_share"], s["value_share"]
        b.append(rect(x0, y - 6, sx(vol) - x0, 17, S1, rx=2,
                      opacity=None if lead else 0.55))
        b.append(rect(x0, y + 15, sx(val) - x0, 17, S4, rx=2,
                      opacity=None if lead else 0.75))
        b.append(txt(sx(vol) + 9, y + 7, f"{vol * 100:.1f}%", size=12.5,
                     fill=TEXT if lead else TEXT2,
                     weight="600" if lead else "400"))
        b.append(txt(sx(val) + 9, y + 28, f"{val * 100:.1f}%", size=12.5, fill=TEXT2))

    # The gap is the whole argument, so it gets drawn rather than described.
    r = by["Retail"]
    gap_pp = (r["volume_share"] - r["value_share"]) * 100
    gx1, gx2, gy = sx(r["value_share"]), sx(r["volume_share"]), top + 46
    b.append(line(gx1, top + 32, gx1, gy, S1, opacity=0.55))
    b.append(line(gx2, top + 11, gx2, gy, S1, opacity=0.55))
    b.append(line(gx1, gy, gx2, gy, S1, width=1.4))
    b.append(txt((gx1 + gx2) / 2, gy + 17,
                 f"{gap_pp:.1f} points of volume that carries no price",
                 size=11.5, fill=SIGNAL_TEXT, anchor="middle", weight="600"))

    write_svg("monetisation-gap", card(
        H,
        "The busy half of India's UPI is the half that carries no revenue",
        f"PhonePe transactions by leg, {d['period']}. Merchant payments are the only "
        f"leg a merchant discount rate could ever price.",
        b,
        f"Source: PhonePe Pulse, {d['period']}. PhonePe's own transactions, not all of "
        f"UPI. Computed by analysis/01_upi_landscape.py.",
        f"Bar chart. Merchant payments are {r['volume_share'] * 100:.1f} percent of "
        f"PhonePe transactions but only {r['value_share'] * 100:.1f} percent of value, "
        f"a gap of {gap_pp:.1f} percentage points. Person to person transfers are the "
        f"mirror image at {by['P2P']['volume_share'] * 100:.1f} percent of transactions "
        f"and {by['P2P']['value_share'] * 100:.1f} percent of value.",
    ))


# --------------------------------------------------------------- exhibit B
def market_structure():
    """Share of national UPI volume against the 30% cap, plotted on real time."""
    d = load("chart_share_trend")
    ms = load("chart_market_structure")
    cap, months = d["cap"], d["months"]
    y0m, m0m = int(months[0][:4]), int(months[0][5:])

    def idx(m):
        return (int(m[:4]) - y0m) * 12 + int(m[5:]) - m0m

    # Plotted on elapsed months, not on position in the list. The series thins
    # from six-monthly to monthly, and spacing it evenly would fake the slope.
    xs = [idx(m) for m in months]
    span = xs[-1] or 1

    H = 432
    x0, x1 = PAD + 48, W - PAD - 122
    ytop, ybase = 128, H - 78
    ymax = 0.52

    def sx(i):
        return x0 + (x1 - x0) * (i / span)

    def sy(v):
        return ybase - (ybase - ytop) * (v / ymax)

    order = {s["app"]: s for s in d["series"]}
    show = (("PhonePe", S1), ("Google Pay", S2), ("Paytm", S4))

    b = []
    # Everything above the dashed line is territory neither leader may occupy.
    b.append(rect(x0, ytop, x1 - x0, sy(cap) - ytop, SOFT))
    for g in (0.1, 0.2, 0.3, 0.4, 0.5):
        b.append(line(x0, sy(g), x1, sy(g), GRID))
        b.append(txt(x0 - 10, sy(g) + 4, f"{int(g * 100)}%", size=10.5,
                     fill=TEXT3, anchor="end"))
    b.append(line(x0, sy(cap), x1, sy(cap), S1, width=1.4, dash="6 4", opacity=0.9))
    b.append(txt(x0 + 8, sy(cap) - 9,
                 f"NPCI cap: {cap:.0%} of national volume per app, due December 2026",
                 size=11.5, fill=SIGNAL_TEXT, weight="600"))

    for m in ("2023-12", "2024-12", "2025-12", months[-1]):
        b.append(txt(sx(idx(m)), ybase + 22, m, size=10.5, fill=TEXT3, anchor="middle"))
    b.append(line(x0, ybase, x1, ybase, BORDER))

    for app, colour in show:
        s = order[app]
        pts = [(sx(x), sy(v)) for x, v in zip(xs, s["values"])]
        b.append(polyline(pts, colour))
        b.append(dot(pts[-1][0], pts[-1][1], 3.4, colour))
        b.append(txt(x1 + 14, pts[-1][1] - 2, app, size=12.5, fill=TEXT, weight="600"))
        b.append(txt(x1 + 14, pts[-1][1] + 15, f"{s['values'][-1] * 100:.1f}%",
                     size=12, fill=colour))

    gap_bn = ms["cap_gap_txns_mn"] / 1000
    b.append(txt(PAD + 13, 95,
                 f"{gap_bn:.1f} billion transactions a month would have to change app "
                 f"for the cap to bind", size=12))

    lead = order["PhonePe"]["values"][-1]
    second = order["Google Pay"]["values"][-1]
    write_svg("market-structure", card(
        H,
        "Both leaders sit above a cap that neither is on course to meet",
        f"Share of national UPI volume, {months[0]} to {months[-1]}, plotted on elapsed "
        f"months so the thinning series does not flatter the trend.",
        b,
        "Source: NPCI UPI ecosystem statistics, transcribed (see docs/REFRESH.md). "
        "Shares are of the national total, so the residual is real. Computed by "
        "analysis/06_competitive_structure.py.",
        f"Line chart. In {months[-1]} PhonePe holds {lead * 100:.1f} percent and Google "
        f"Pay {second * 100:.1f} percent of national UPI volume, both above the 30 "
        f"percent NPCI cap. About {gap_bn:.1f} billion transactions a month would have "
        f"to move between apps for the cap to bind.",
    ))


# --------------------------------------------------------------- exhibit C
def growth_bridge():
    """Waterfall: which leg actually built the volume."""
    d = load("chart_growth_bridge")
    steps = d["steps"]
    start = next(s for s in steps if s["type"] == "start")
    end = next(s for s in steps if s["type"] == "end")
    deltas = [s for s in steps if s["type"] == "delta"]

    H = 412
    x0, x1 = PAD + 54, W - PAD - 24
    ytop, ybase = 132, H - 78
    ymax = end["value"] * 1.18
    slot = (x1 - x0) / len(steps)
    bw = min(88, slot * 0.52)

    def sy(v):
        return ybase - (ybase - ytop) * (v / ymax)

    def cx(i):
        return x0 + slot * (i + 0.5)

    b = []
    for g in (0, 10, 20, 30, 40):
        if g > ymax:
            continue
        b.append(line(x0 - 12, sy(g), x1, sy(g), GRID))
        b.append(txt(x0 - 20, sy(g) + 4, f"{g}", size=10.5, fill=TEXT3, anchor="end"))
    b.append(txt(PAD + 13, 95, d["unit"], size=10.5, fill=TEXT3))

    running = start["value"]
    for i, s in enumerate(steps):
        x = cx(i) - bw / 2
        if s["type"] == "delta":
            top, bot = sy(running + s["value"]), sy(running)
            colour = S1 if s["label"] == d["highlight"] else S4
            lbl = f"+{s['value']:.2f}"
            running += s["value"]
        else:
            top, bot, colour = sy(s["value"]), ybase, S4
            lbl = f"{s['value']:.2f}" if s["type"] == "start" else f"{s['value']:.1f}"
        faded = s["type"] == "delta" and colour == S4
        b.append(rect(x, top, bw, max(bot - top, 1.5), colour, rx=2,
                      opacity=0.72 if faded else None))
        b.append(txt(cx(i), top - 10, lbl, size=12.5,
                     fill=TEXT if colour == S1 else TEXT2,
                     anchor="middle", weight="600" if colour == S1 else "400"))
        name = f"+ {s['label']}" if s["type"] == "delta" else s["label"]
        b.append(txt(cx(i), ybase + 22, name, size=11.5,
                     fill=TEXT if colour == S1 else TEXT3, anchor="middle",
                     weight="600" if colour == S1 else "400"))
        if i + 1 < len(steps):
            b.append(line(cx(i) + bw / 2, top, cx(i + 1) - bw / 2, top,
                          BORDER, dash="3 3"))

    b.append(line(x0 - 12, ybase, x1, ybase, BORDER))
    share = deltas[0]["value"] / (end["value"] - start["value"])
    b.append(txt(PAD + 13, 113,
                 f"The merchant leg alone is {share:.0%} of everything UPI added "
                 f"since {start['label']}", size=12))

    write_svg("growth-bridge", card(
        H,
        "Growth came from the leg nobody is paid for",
        f"Quarterly transaction volume bridged from {start['label']} to "
        f"{end['label']}, in {d['unit']}.",
        b,
        f"Source: PhonePe Pulse, {start['label']} to {end['label']}. Computed by "
        f"analysis/01_upi_landscape.py.",
        f"Waterfall chart. Quarterly UPI volume on PhonePe grew from "
        f"{start['value']:.2f} to {end['value']:.1f} billion transactions between "
        f"{start['label']} and {end['label']}. The merchant leg contributed "
        f"{deltas[0]['value']:.1f} billion of that, or {share:.0%} of all growth.",
    ))


# --------------------------------------------------------------- exhibit D
def bank_nim_gap():
    """Slopegraph: the private against public margin gap, over a full rate cycle."""
    d = load("chart_nim_slope")
    periods = d["periods"]
    series = {s["cohort"]: s["values"] for s in d["series"]}
    gaps = d["gap_bps"]

    H = 404
    x0, x1 = PAD + 96, W - PAD - 128
    ytop, ybase = 138, H - 76
    lo = min(min(v) for v in series.values()) - 0.45
    hi = max(max(v) for v in series.values()) + 0.35
    slot = (x1 - x0) / (len(periods) - 1)

    def sx(i):
        return x0 + slot * i

    def sy(v):
        return ybase - (ybase - ytop) * ((v - lo) / (hi - lo))

    b = []
    for g in (2.5, 3.0, 3.5, 4.0):
        b.append(line(x0 - 16, sy(g), x1 + 6, sy(g), GRID))
        b.append(txt(x0 - 24, sy(g) + 4, f"{g:.1f}%", size=10.5, fill=TEXT3, anchor="end"))
    for i, p in enumerate(periods):
        b.append(txt(sx(i), ybase + 24, p, size=11.5, fill=TEXT3, anchor="middle"))
    b.append(line(x0 - 16, ybase, x1 + 6, ybase, BORDER))

    # The gap is the finding, so shade it rather than leaving it to be measured.
    poly = ([(sx(i), sy(v)) for i, v in enumerate(series["Private"])]
            + [(sx(i), sy(v)) for i, v in reversed(list(enumerate(series["Public"])))])
    pts = " ".join(f"{n(x)},{n(y)}" for x, y in poly)
    b.append(f'<polygon points="{pts}" fill="{S1}" opacity="0.09"/>')

    for cohort, colour in (("Private", S1), ("Public", S2)):
        vals = series[cohort]
        pts_c = [(sx(i), sy(v)) for i, v in enumerate(vals)]
        b.append(polyline(pts_c, colour))
        for x, y in pts_c:
            b.append(dot(x, y, 3.2, colour))
        b.append(txt(x1 + 18, pts_c[-1][1] - 2, f"{cohort} banks", size=12.5,
                     fill=TEXT, weight="600"))
        b.append(txt(x1 + 18, pts_c[-1][1] + 15, f"{vals[-1]:.2f}%", size=12, fill=colour))

    # Anchored inward at both ends so neither label crowds the axis it sits beside.
    for i, anchor, nudge in ((0, "start", 10), (len(periods) - 1, "end", -10)):
        mid = (sy(series["Private"][i]) + sy(series["Public"][i])) / 2
        b.append(txt(sx(i) + nudge, mid + 4, f"{gaps[i]} bps", size=12,
                     fill=SIGNAL_TEXT, anchor=anchor, weight="600"))

    b.append(txt(PAD + 13, 95, d["metric"], size=10.5, fill=TEXT3))
    b.append(txt(PAD + 13, 113,
                 f"The gap opened at {gaps[0]} bps and closed at {gaps[-1]} bps: "
                 f"{abs(gaps[-1] - gaps[0])} bps of movement across the cycle", size=12))

    write_svg("bank-nim-gap", card(
        H,
        "A full rate cycle moved the margin gap by two basis points",
        f"Net interest margin proxy, {periods[0]} to {periods[-1]}, cohort means of "
        f"five private and five public sector banks.",
        b,
        f"Source: Yahoo Finance fundamentals for 11 NSE tickers. {d['caveat']} "
        f"Computed by analysis/02_banking_health.py.",
        f"Slope chart. The private bank margin proxy runs from "
        f"{series['Private'][0]:.2f} to {series['Private'][-1]:.2f} percent between "
        f"{periods[0]} and {periods[-1]}, and the public bank proxy from "
        f"{series['Public'][0]:.2f} to {series['Public'][-1]:.2f} percent. The gap "
        f"between them is {gaps[0]} basis points at the start and {gaps[-1]} at the "
        f"end, so it survived the whole cycle.",
    ))


# ------------------------------------------------------ generated README text
def key_figures() -> str:
    """The headline table. Every cell is read, none is typed."""
    split = load("chart_category_split")
    hero = load("upi_monetisation")
    ms = load("chart_market_structure")
    trend = load("chart_share_trend")
    nim = load("chart_nim_slope")
    spread = load("chart_bank_spread")
    gap = load("chart_state_gap")
    bridge = load("chart_growth_bridge")
    shelf = load("chart_fund_shelf")
    incl = load("chart_inclusion")

    retail = next(s for s in split["series"] if s["category"] == "Retail")
    p2p = next(s for s in split["series"] if s["category"] == "P2P")
    apps = {s["app"]: s["values"][-1] for s in trend["series"]}
    priv = next(s for s in spread["series"] if s["cohort"] == "Private")
    pub = next(s for s in spread["series"] if s["cohort"] == "Public")

    material = [s for s in gap["states"]
                if s["volume_share"] >= gap["min_share_for_extremes"]]
    material.sort(key=lambda s: s["merchant_volume_share"])
    low, high = material[0], material[-1]

    start = next(s for s in bridge["steps"] if s["type"] == "start")
    end = next(s for s in bridge["steps"] if s["type"] == "end")
    merch = next(s for s in bridge["steps"]
                 if s["type"] == "delta" and s["label"] == bridge["highlight"])
    merch_share = merch["value"] / (end["value"] - start["value"])

    dated = [r for r in incl["series"]
             if r["txns_per_banked_adult_per_month"] is not None]
    latest, prior = dated[-1], dated[-2]

    rows = [
        ("Merchant payments: share of transactions against share of value",
         f"**{retail['volume_share']:.1%} / {retail['value_share']:.1%}**",
         f"PhonePe Pulse, {split['period']}"),
        ("Person to person, the mirror image",
         f"{p2p['volume_share']:.1%} / {p2p['value_share']:.1%}",
         f"PhonePe Pulse, {split['period']}"),
        ("Payment revenue earned on the merchant leg under zero-MDR",
         f"**Rs {hero['mdr_scenarios_cr']['0bps']:.0f}**",
         f"PhonePe Pulse, {split['period']}"),
        ("What 30bps would have been worth on that same leg",
         f"Rs {hero['mdr_scenarios_cr']['30bps']:,.0f} crore per quarter",
         f"PhonePe Pulse, {split['period']}"),
        (f"Merchant contribution to all volume growth since {start['label']}",
         f"**{merch_share:.0%}**",
         f"PhonePe Pulse, {start['label']} to {end['label']}"),
        ("PhonePe and Google Pay share of national UPI volume",
         f"**{apps['PhonePe']:.1%} / {apps['Google Pay']:.1%}**, both above the "
         f"{ms['cap']:.0%} cap",
         f"NPCI, {ms['month']}"),
        ("Transactions that must change app for the cap to bind",
         f"**{ms['cap_gap_txns_mn'] / 1000:.1f} bn a month**",
         f"NPCI, {ms['month']}"),
        ("Private against public bank margin gap",
         f"**{nim['gap_bps'][-1]} bps** "
         f"({(priv['yield_on_assets'] - pub['yield_on_assets']) * 100:.0f} pricing, "
         f"{(pub['cost_of_funds'] - priv['cost_of_funds']) * 100:.0f} funding)",
         f"Yahoo Finance, FY{spread['fy']}"),
        ("Merchant share of own transactions: most against least, material states",
         f"**{high['state']} {high['merchant_volume_share']:.1%} against "
         f"{low['state']} {low['merchant_volume_share']:.1%}**",
         f"PhonePe Pulse, {gap['period']}"),
        ("UPI transactions per banked adult per month",
         f"**{latest['txns_per_banked_adult_per_month']:.1f}**, up from "
         f"{prior['txns_per_banked_adult_per_month']:.1f} in {prior['year']}",
         f"World Bank Findex and NPCI, {latest['year']}"),
        ("Fund schemes against distinct strategies",
         f"**{shelf['listed_schemes']:,} to {shelf['distinct_strategies']:,}** "
         f"({shelf['listed_schemes'] / shelf['distinct_strategies']:.1f}x wrappers)",
         f"AMFI, {shelf['nav_date']}"),
    ]
    out = ["| Finding | Figure | Source and period |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(out)


def facts_block() -> str:
    """A machine-readable summary, for anything that reads before it quotes."""
    meta = load("pipeline_meta")
    split = load("chart_category_split")
    hero = load("upi_monetisation")
    ms = load("chart_market_structure")
    nim = load("chart_nim_slope")
    shelf = load("chart_fund_shelf")

    retail = next(s for s in split["series"] if s["category"] == "Retail")
    p2p = next(s for s in split["series"] if s["category"] == "P2P")
    lead, second = ms["apps"][0], ms["apps"][1]

    def fact(metric, value, unit, period, source):
        return [f"  - metric: {metric}",
                f"    value: {value}",
                f"    unit: {unit}",
                f"    period: {period}",
                f"    source: {source}"]

    lines = [
        "```yaml",
        "name: India FS Pulse",
        "url: https://india-fs-pulse.vercel.app",
        "repository: https://github.com/DogInfantry/india-fs-pulse",
        "license: Apache-2.0",
        "author: Anklesh Rawat",
        "question: >-",
        "  India built the world's largest real time payments network and charges",
        "  nothing for the merchant leg. Who captures the value, and is there an",
        "  investable business model?",
        "method: reproducible Python pipeline, then analysis, then a static site",
        f"publishers: {meta['publishers']}",
        f"fetchers: {meta['fetchers']}",
        f"analysis_modules: {meta['analysis_modules']}",
        f"processed_datasets: {meta['datasets']}",
        "credentials_required: none",
        "findings:",
    ]
    lines += fact("merchant share of UPI transactions", retail["volume_share"],
                  "share of transactions", split["period"], "PhonePe Pulse")
    lines += fact("merchant share of UPI value", retail["value_share"],
                  "share of rupees", split["period"], "PhonePe Pulse")
    lines += fact("person to person share of UPI value", p2p["value_share"],
                  "share of rupees", split["period"], "PhonePe Pulse")
    lines += fact("payment revenue on the merchant leg under zero-MDR",
                  hero["mdr_scenarios_cr"]["0bps"], "INR crore per quarter",
                  split["period"], "PhonePe Pulse")
    lines += fact("registered merchants", hero["registered_merchants"], "count",
                  split["period"], "PhonePe Pulse")
    lines += fact(f"{lead['app']} share of national UPI volume", lead["volume_share"],
                  "share of national volume", ms["month"], "NPCI")
    lines += fact(f"{second['app']} share of national UPI volume",
                  second["volume_share"], "share of national volume",
                  ms["month"], "NPCI")
    lines += fact("NPCI per app volume share cap", ms["cap"],
                  "share of national volume", "due December 2026", "NPCI")
    lines += fact("transactions that must change app for the cap to bind",
                  ms["cap_gap_txns_mn"], "millions per month", ms["month"], "NPCI")
    lines += fact("private against public bank net interest margin gap",
                  nim["gap_bps"][-1], "basis points", nim["periods"][-1],
                  "Yahoo Finance fundamentals")
    lines += fact("mutual fund schemes against distinct strategies",
                  f"{shelf['listed_schemes']} to {shelf['distinct_strategies']}",
                  "count", shelf["nav_date"], "AMFI")
    lines += [
        "caveats:",
        "  - PhonePe Pulse covers PhonePe's own transactions, not all of UPI.",
        "  - The NIM figure is a proxy: net interest income over average total assets.",
        "  - The NPS panel is synthetic and labelled synthetic everywhere it appears.",
        "  - Four months NPCI does not publish are left as gaps, never interpolated.",
        "```",
    ]
    return "\n".join(lines)


def patch_readme() -> None:
    """Rewrite the marker-delimited regions, leaving the prose untouched."""
    text = README.read_text(encoding="utf-8")
    for marker, payload in (("KEYFIGURES", key_figures()), ("FACTS", facts_block())):
        pattern = re.compile(
            rf"(<!-- BEGIN:{marker} -->\n).*?(\n<!-- END:{marker} -->)", re.DOTALL)
        if not pattern.search(text):
            raise SystemExit(f"README.md is missing the {marker} markers")
        text = pattern.sub(lambda m: m.group(1) + payload + m.group(2), text, count=1)
    README.write_text(text, encoding="utf-8", newline="\n")
    print("   README.md generated regions")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("README exhibits")
    monetisation_gap()
    market_structure()
    growth_bridge()
    bank_nim_gap()
    patch_readme()


if __name__ == "__main__":
    main()
