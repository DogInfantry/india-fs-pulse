#!/usr/bin/env python
"""Draw the README's exhibits, and refresh its generated regions.

The README is the front door of a repository whose whole claim is that no figure
is typed in by hand. So the README does not type them in either: this script
reads the same computed JSON the site reads, emits nine SVG exhibits into
`docs/assets/`, and rewrites two marker-delimited regions inside `README.md`.

Stdlib only, on purpose. The pipeline already carries pandas; a README chart is
not a reason to add a plotting dependency. Output is deterministic (no clock, no
randomness, coordinates rounded), so `python run.py analyze` twice in a row
leaves the working tree clean.

Every exhibit is drawn on the project's own dark card, which is why one file
works on both GitHub themes: the card supplies its own background rather than
borrowing the page's. The frame follows site/src/components/Figure.astro, kicker
and action title included, so the README reads as the same piece of work.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "src" / "data"
GEOJSON = ROOT / "site" / "public" / "india_states.geojson"
OUT = ROOT / "docs" / "assets"
README = ROOT / "README.md"

# Palette lifted from site/src/styles/tokens.css. Never invent a hex here: the
# README should look like the site, not like a second design system.
BG = "#0C0F14"        # --ink
PANEL = "#131820"     # --surface
GRID = "#1E262F"      # --line-soft
BORDER = "#262F3B"    # --line
TEXT = "#E9EDF2"      # --text
TEXT2 = "#A6B0BE"     # --text-2
TEXT3 = "#7F8A97"     # --text-3
S1 = "#C02734"        # --s1 crimson: the subject
S2 = "#1F7A8C"        # --s2 teal: the comparator
S3 = "#C98A2E"        # --s3 amber: the third
S4 = "#5B6673"        # --s4 grey: context
SIGNAL_TEXT = "#DF5F6A"   # --signal-text: small red type needs 4.5:1
SOFT = "rgba(192,39,52,0.10)"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"

W = 960
PAD = 34
HEAD = 100    # y below which an exhibit may draw. Above it: kicker, title, deck.


def load(name: str):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(v) -> str:
    """Round for the wire. Keeps output byte-identical between runs."""
    r = round(float(v), 1)
    return f"{int(r)}" if r == int(r) else f"{r}"


def txt(x, y, s, size=12, fill=TEXT2, anchor="start", weight="400",
        family=SANS, opacity=None, spacing=None) -> str:
    extra = f' opacity="{opacity}"' if opacity is not None else ""
    extra += f' letter-spacing="{spacing}"' if spacing is not None else ""
    return (f'<text x="{n(x)}" y="{n(y)}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f'{esc(s)}</text>')


def rect(x, y, w, h, fill, rx=0, stroke=None, opacity=None, sw=1) -> str:
    extra = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
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


def dot(cx, cy, r, fill, stroke=None) -> str:
    extra = f' stroke="{stroke}" stroke-width="1.5"' if stroke else ""
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{r}" fill="{fill}"{extra}/>'


def panel(x, y, w, h) -> str:
    """The inset surface every plot sits on, matching Figure.astro's body."""
    return rect(x, y, w, h, PANEL, rx=8, stroke=GRID)


def wrap(s: str, budget: int) -> list:
    """Greedy word wrap. SVG text does not wrap on its own, and a source line
    that runs past the card is the one failure mode nothing else catches."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) > budget and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def card(height: int, kicker: str, title: str, deck: str, body: list,
         source: str, alt: str) -> str:
    """The shared frame: kicker, crimson rule, action title, deck, source line."""
    # 10.5px in this stack averages a shade over 5px a character.
    src = wrap(source, int((W - PAD * 2) / 5.1))
    rule_y = height - (46 if len(src) > 1 else 42)
    src_y = height - (30 if len(src) > 1 else 22)
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="{W}" height="{height}" role="img" aria-label="{esc(alt)}">',
        f"<title>{esc(alt)}</title>",
        rect(0, 0, W, height, BG, rx=14),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="13.5" '
        f'fill="none" stroke="{BORDER}"/>',
        txt(PAD + 13, 34, kicker.upper(), size=10, fill=SIGNAL_TEXT,
            weight="600", spacing="1.6"),
        rect(PAD, 46, 3, 21, S1),
        txt(PAD + 13, 63, title, size=20, fill=TEXT, weight="600", family=SERIF),
        txt(PAD + 13, 85, deck, size=13, fill=TEXT2),
        line(PAD, rule_y, W - PAD, rule_y, GRID),
    ] + [txt(PAD, src_y + i * 14, ln, size=10.5, fill=TEXT3)
         for i, ln in enumerate(src[:2])]
    return "\n".join(head + body + ["</svg>", ""])


def write_svg(name: str, svg: str) -> None:
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"   docs/assets/{name}.svg")


def inr(v) -> str:
    """Indian digit grouping. 1234567 becomes 12,34,567."""
    s = str(int(round(float(v))))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


# --------------------------------------------------------------- exhibit 1
def kpi_band():
    """The site's opening strip: four numbers, before any argument is made."""
    d = load("upi_monetisation")
    split = load("chart_category_split")
    cells = [
        ("Merchant share of transactions", f"{d['merchant_volume_share']:.1%}", TEXT),
        ("Merchant share of value", f"{d['merchant_value_share']:.1%}", TEXT),
        ("Average merchant ticket", f"Rs {inr(d['merchant_avg_ticket_inr'])}", TEXT),
        ("Payment revenue at zero-MDR", f"Rs {d['mdr_scenarios_cr']['0bps']:.0f}",
         SIGNAL_TEXT),
    ]
    H = 128
    cw = (W - PAD * 2 - 3) / 4
    b = [rect(PAD, 24, W - PAD * 2, 80, GRID, rx=10)]
    for i, (label, value, colour) in enumerate(cells):
        x = PAD + i * (cw + 1)
        b.append(rect(x, 24, cw, 80, PANEL, rx=10 if i in (0, 3) else 0))
        b.append(txt(x + 18, 48, label.upper(), size=9.5, fill=TEXT3,
                     weight="600", spacing="1.2"))
        b.append(txt(x + 18, 86, value, size=30, fill=colour, family=SERIF,
                     weight="600"))
    b.append(txt(PAD, H - 8, f"PhonePe Pulse, {split['period']}. PhonePe's own "
                             f"transactions, not all of UPI.", size=10, fill=TEXT3))
    alt = (f"Four headline figures for {split['period']}: merchant share of "
           f"transactions {d['merchant_volume_share']:.1%}, merchant share of value "
           f"{d['merchant_value_share']:.1%}, average merchant ticket "
           f"{inr(d['merchant_avg_ticket_inr'])} rupees, and payment revenue at "
           f"zero-MDR of zero rupees.")
    svg = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{esc(alt)}">',
        f"<title>{esc(alt)}</title>",
        rect(0, 0, W, H, BG, rx=14),
    ] + b + ["</svg>", ""])
    write_svg("kpi-band", svg)


# --------------------------------------------------------------- exhibit 2
def monetisation_gap():
    """Paired bars: share of transactions against share of value, by leg."""
    d = load("chart_category_split")
    rows = [
        ("Merchant (Retail)", "Retail"),
        ("Person to person", "P2P"),
        ("Utility and bills", "Utility"),
    ]
    by = {s["category"]: s for s in d["series"]}

    H = 436
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 190, px + pw - 96
    top, row_h, drop = py + 48, 72, 18
    axis_y = top + 2 * row_h + drop + 50

    def sx(v):
        return x0 + (x1 - x0) * (v / 0.80)

    b = [panel(px, py, pw, ph)]
    b.append(rect(px + 20, py + 18, 10, 10, S1, rx=2))
    b.append(txt(px + 38, py + 27, "Share of transactions", size=12))
    b.append(rect(px + 195, py + 18, 10, 10, S4, rx=2))
    b.append(txt(px + 213, py + 27, "Share of rupees moved", size=12))

    for g in (0.2, 0.4, 0.6, 0.8):
        b.append(line(sx(g), top - 14, sx(g), axis_y - 14, GRID))
        b.append(txt(sx(g), axis_y, f"{int(g * 100)}%", size=10.5,
                     fill=TEXT3, anchor="middle"))

    for i, (label, key) in enumerate(rows):
        s = by[key]
        y = top + i * row_h + (drop if i else 0)
        lead = key == "Retail"
        b.append(txt(px + 20, y + 8, label, size=13,
                     fill=TEXT if lead else TEXT2,
                     weight="600" if lead else "400"))
        b.append(txt(px + 20, y + 26, f"avg ticket Rs {inr(s['avg_ticket_inr'])}",
                     size=11, fill=TEXT3))
        vol, val = s["volume_share"], s["value_share"]
        b.append(rect(x0, y - 6, sx(vol) - x0, 17, S1, rx=2,
                      opacity=None if lead else 0.55))
        b.append(rect(x0, y + 15, sx(val) - x0, 17, S4, rx=2,
                      opacity=None if lead else 0.75))
        b.append(txt(sx(vol) + 9, y + 7, f"{vol * 100:.1f}%", size=12.5,
                     fill=TEXT if lead else TEXT2,
                     weight="600" if lead else "400"))
        b.append(txt(sx(val) + 9, y + 28, f"{val * 100:.1f}%", size=12.5, fill=TEXT2))

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
        H, "Exhibit 1 · Volume against value",
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


# --------------------------------------------------------------- exhibit 3
def growth_bridge():
    """Waterfall: which leg actually built the volume."""
    d = load("chart_growth_bridge")
    steps = d["steps"]
    start = next(s for s in steps if s["type"] == "start")
    end = next(s for s in steps if s["type"] == "end")
    deltas = [s for s in steps if s["type"] == "delta"]

    H = 434
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 66, px + pw - 16
    ytop, ybase = py + 44, py + ph - 44
    ymax = end["value"] * 1.16
    slot = (x1 - x0) / len(steps)
    bw = min(88, slot * 0.52)

    def sy(v):
        return ybase - (ybase - ytop) * (v / ymax)

    def cx(i):
        return x0 + slot * (i + 0.5)

    b = [panel(px, py, pw, ph)]
    for g in (0, 10, 20, 30, 40):
        if g > ymax:
            continue
        b.append(line(x0 - 12, sy(g), x1, sy(g), GRID))
        b.append(txt(x0 - 20, sy(g) + 4, f"{g}", size=10.5, fill=TEXT3, anchor="end"))
    b.append(txt(x0 - 20, ytop - 22, d["unit"], size=10.5, fill=TEXT3))

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
    b.append(txt(px + 20, py + 26,
                 f"The merchant leg alone is {share:.0%} of everything UPI added "
                 f"since {start['label']}", size=12))

    write_svg("growth-bridge", card(
        H, "Exhibit 2 · Growth bridge",
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


# --------------------------------------------------------------- exhibit 4
def market_mekko():
    """Variable-width bars. Width is transaction share, height is average ticket,
    so area is rupees. The cap is drawn on the width axis because the cap is a
    rule about width. Mirrors site/src/components/charts/Marimekko.astro."""
    d = load("chart_market_structure")
    apps = d["apps"]
    cap = d["cap"]

    H = 476
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 78, px + pw - 18
    ytop, ybase = py + 76, py + ph - 52
    step = 1000
    ymax = math.ceil(max(a["avg_ticket_inr"] for a in apps) / step) * step

    def sx(share):
        return x0 + (x1 - x0) * share

    def sy(t):
        return ybase - (ybase - ytop) * (t / ymax)

    b = [panel(px, py, pw, ph)]
    for i in range(int(ymax // step) + 1):
        t = step * i
        b.append(line(x0, sy(t), x1, sy(t), GRID))
        b.append(txt(x0 - 10, sy(t) + 4, f"Rs {inr(t)}", size=10,
                     fill=TEXT3, anchor="end"))
    b.append(txt(x0 - 58, ytop - 30, "Average ticket", size=10, fill=TEXT3))

    cursor = 0.0
    for a in apps:
        w = (x1 - x0) * a["volume_share"]
        x, y = sx(cursor), sy(a["avg_ticket_inr"])
        residual = a["app"] == "All other apps"
        colour = S1 if a["breaches_cap"] else (S4 if residual else S2)
        b.append(rect(x + 1, y, max(w - 2, 1), ybase - y, colour, rx=2,
                      opacity=None if a["breaches_cap"] else (0.5 if residual else 0.75)))
        if a["volume_share"] > 0.055:
            mid = x + w / 2
            b.append(txt(mid, y - 23, a["app"], size=12, fill=TEXT,
                         anchor="middle", weight="600"))
            b.append(txt(mid, y - 9, f"{a['volume_share']:.1%} of transactions",
                         size=10.5, fill=TEXT2, anchor="middle"))
            b.append(txt(mid, ybase - 10, f"Rs {inr(a['avg_ticket_inr'])}", size=11,
                         fill=TEXT if a["breaches_cap"] else TEXT2, anchor="middle"))
        cursor += a["volume_share"]

    b.append(line(x0, ybase, x1, ybase, BORDER))
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        b.append(txt(sx(t), ybase + 22, f"{t:.0%}", size=10, fill=TEXT3, anchor="middle"))
    b.append(txt(x1, ybase + 38, "cumulative share of national transactions",
                 size=10, fill=TEXT3, anchor="end"))

    capx = sx(cap)
    b.append(line(capx, ytop - 34, capx, ybase + 8, S1, width=1.4, dash="6 4",
                  opacity=0.9))
    b.append(txt(capx + 8, ytop - 38, f"the {cap:.0%} cap falls here, on the width axis",
                 size=11.5, fill=SIGNAL_TEXT, weight="600"))

    # The tallest column is a sliver, and that is the point of drawing area at all.
    tallest = max(apps, key=lambda a: a["avg_ticket_inr"])
    tx = sx(sum(a["volume_share"] for a in apps[:apps.index(tallest)])
            + tallest["volume_share"] / 2)
    ty = sy(tallest["avg_ticket_inr"])
    b.append(line(tx, ty - 6, tx - 46, ty - 26, TEXT3, opacity=0.7))
    b.append(txt(tx - 52, ty - 28, tallest["app"], size=11, fill=TEXT,
                 anchor="end", weight="600"))
    b.append(txt(tx - 52, ty - 15,
                 f"Rs {inr(tallest['avg_ticket_inr'])} ticket, "
                 f"{tallest['volume_share']:.1%} of transactions",
                 size=10, fill=TEXT2, anchor="end"))
    b.append(txt(tx - 52, ty - 3,
                 f"but {tallest['value_share']:.1%} of value", size=10,
                 fill=TEXT2, anchor="end"))

    lead, second = apps[0], apps[1]
    top2 = d["top2_volume_share"]
    b.append(txt(px + 20, py + 26,
                 f"Area is rupees. {lead['app']} and {second['app']} are the only two "
                 f"columns wide enough to breach the cap, and neither is unusual on "
                 f"ticket", size=12))

    write_svg("market-mekko", card(
        H, "Exhibit 3 · Who holds what",
        f"Two apps hold {top2:.0%} of transactions, and the tallest column holds "
        f"{tallest['volume_share']:.1%}",
        f"Column width is share of national transactions; height is average ticket, so "
        f"area is rupees moved. {d['month']}.",
        b,
        f"Source: NPCI UPI ecosystem statistics, {d['month']}, transcribed (see "
        f"docs/REFRESH.md). Shares are of the national total, so the residual is real. "
        f"Computed by analysis/06_competitive_structure.py.",
        f"Variable width bar chart for {d['month']}. {lead['app']} occupies "
        f"{lead['volume_share']:.1%} of national transactions at an average ticket of "
        f"{inr(lead['avg_ticket_inr'])} rupees, and {second['app']} "
        f"{second['volume_share']:.1%} at {inr(second['avg_ticket_inr'])} rupees. Both "
        f"breach the 30 percent cap, which is drawn on the width axis. The tallest "
        f"column, {tallest['app']}, has an average ticket of "
        f"{inr(tallest['avg_ticket_inr'])} rupees but only "
        f"{tallest['volume_share']:.1%} of transactions against "
        f"{tallest['value_share']:.1%} of value.",
    ))


# --------------------------------------------------------------- exhibit 5
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

    H = 448
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 62, px + pw - 126
    ytop, ybase = py + 44, py + ph - 42
    ymax = 0.52

    def sx(i):
        return x0 + (x1 - x0) * (i / span)

    def sy(v):
        return ybase - (ybase - ytop) * (v / ymax)

    order = {s["app"]: s for s in d["series"]}
    show = (("PhonePe", S1), ("Google Pay", S2), ("Paytm", S4))

    b = [panel(px, py, pw, ph)]
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
    b.append(txt(px + 20, py + 26,
                 f"{gap_bn:.1f} billion transactions a month would have to change app "
                 f"for the cap to bind", size=12))

    lead = order["PhonePe"]["values"][-1]
    second = order["Google Pay"]["values"][-1]
    write_svg("market-structure", card(
        H, "Exhibit 4 · Share shift",
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


# --------------------------------------------------------------- exhibit 6
# Bins are steps in percentage points away from the national figure, not a
# continuous ramp: a reader has to be able to decode the legend, and a ramp on a
# choropleth this small is decoration rather than information.
MAP_BINS = [
    (-12.0, "#0A3038", "12 points or more below"),
    (-6.0, "#155A69", "6 to 12 points below"),
    (-2.0, "#3AA0B4", "2 to 6 points below"),
    (2.0, "#4A5462", "within 2 points of India"),
    (4.5, "#7E1F2A", "2 to 4.5 points above"),
    (999.0, "#D93A47", "4.5 points or more above"),
]

# The seven territories flagged too small to see cluster on the west coast and
# around Delhi, so naming them in place collides no matter how the labels are
# nudged. They get numbered discs and a key instead, which also stops the map
# from being unreadable if an eighth is ever added.
SHORT_NAMES = {
    "Dadra & Nagar Haveli & Daman & Diu": "Dadra & Nagar Haveli, Daman & Diu",
    "Andaman & Nicobar Islands": "Andaman & Nicobar",
}


def bin_colour(pp):
    for edge, colour, _ in MAP_BINS:
        if pp <= edge:
            return colour
    return MAP_BINS[-1][1]


def india_map():
    """A real choropleth of all 36 states and union territories.

    The boundary file is built once by site/scripts/build_india_map.py, which
    asserts 36 features and India's official northern and eastern extent, and
    which already flags the territories too small to see and computes a
    representative point for each. Nothing here re-derives geography.
    """
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    d = load("chart_state_gap")
    share = {s["state"]: s["merchant_volume_share"] for s in d["states"]}
    nat = d["national_merchant_volume_share"]
    assert {f["properties"]["name"] for f in geo["features"]} == set(share), \
        "boundary file and state data disagree"

    lons, lats = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            lons.append(c[0])
            lats.append(c[1])
            return
        for part in c:
            walk(part)

    for f in geo["features"]:
        walk(f["geometry"]["coordinates"])
    lo_x, hi_x, lo_y, hi_y = min(lons), max(lons), min(lats), max(lats)
    kx = math.cos(math.radians((lo_y + hi_y) / 2))   # do not stretch India

    H = 620
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    map_x, map_y = px + 16, py + 14
    map_h = ph - 28
    scale = map_h / (hi_y - lo_y)
    map_w = (hi_x - lo_x) * kx * scale

    def proj(lon, lat):
        return (map_x + (lon - lo_x) * kx * scale,
                map_y + (hi_y - lat) * scale)

    def path_for(geom):
        polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        out = []
        for poly in polys:
            for ring in poly:
                pts = [proj(c[0], c[1]) for c in ring]
                out.append("M" + " L".join(f"{n(x)} {n(y)}" for x, y in pts) + " Z")
        return " ".join(out)

    b = [panel(px, py, pw, ph)]
    smalls = []
    for f in sorted(geo["features"], key=lambda f: f["properties"]["name"]):
        p = f["properties"]
        pp = (share[p["name"]] - nat) * 100
        b.append(f'<path d="{path_for(f["geometry"])}" fill="{bin_colour(pp)}" '
                 f'stroke="{BG}" stroke-width="0.6" stroke-linejoin="round"/>')
        if p["small"]:
            smalls.append((p, pp))

    # A 10px dot cannot carry a diverging ramp: mid-range values land on the
    # neutral stop and every marker comes back looking the same. So the markers
    # encode one bit, which side of the national figure the territory falls on.
    smalls.sort(key=lambda sp: proj(*sp[0]["point"])[1])   # numbered north to south
    for i, (p, pp) in enumerate(smalls, 1):
        cx, cy = proj(*p["point"])
        colour = S1 if pp > 0 else S2
        b.append(dot(cx, cy, 7, colour, stroke=BG))
        b.append(txt(cx, cy + 3.4, str(i), size=9, fill=TEXT, anchor="middle",
                     weight="700"))

    kx0, ky0 = map_x + 194, map_y + 312
    b.append(txt(kx0, ky0, "TOO SMALL TO SEE UNAIDED", size=9, fill=TEXT3,
                 weight="600", spacing="1.1"))
    for i, (p, pp) in enumerate(smalls, 1):
        y = ky0 + 4 + i * 14
        b.append(dot(kx0 + 6, y - 3.5, 6, S1 if pp > 0 else S2))
        b.append(txt(kx0 + 6, y - 0.5, str(i), size=8, fill=TEXT, anchor="middle",
                     weight="700"))
        b.append(txt(kx0 + 18, y, SHORT_NAMES.get(p["name"], p["name"]), size=8.5,
                     fill=TEXT2))
        b.append(txt(map_x + map_w - 5, y, f"{share[p['name']]:.0%}", size=8.5,
                     fill=TEXT3, anchor="end"))

    # Right column: legend labelled by meaning, then the ranked extremes.
    rx = map_x + map_w + 46
    b.append(txt(rx, py + 34, "MERCHANT SHARE OF A STATE'S OWN TRANSACTIONS",
                 size=9, fill=TEXT3, weight="600", spacing="1.1"))
    b.append(txt(rx, py + 52, f"India is at {nat:.1%}. Colour is distance from that.",
                 size=11, fill=TEXT2))
    ly = py + 72
    for i, (_, colour, label) in enumerate(MAP_BINS):
        b.append(rect(rx, ly + i * 20, 22, 12, colour, rx=2))
        b.append(txt(rx + 30, ly + i * 20 + 10, label, size=10.5, fill=TEXT2))
    foot = ly + len(MAP_BINS) * 20
    b.append(txt(rx, foot + 16, "Crimson runs more on merchants than India does.",
                 size=10, fill=TEXT3))
    b.append(txt(rx, foot + 30, "Teal runs more on person to person transfers.",
                 size=10, fill=TEXT3))

    material = sorted(
        (s for s in d["states"] if s["volume_share"] >= d["min_share_for_extremes"]),
        key=lambda s: s["merchant_volume_share"], reverse=True)
    ty = foot + 62
    b.append(txt(rx, ty, "MOST AND LEAST MERCHANT-DRIVEN", size=9, fill=TEXT3,
                 weight="600", spacing="1.1"))
    b.append(txt(rx, ty + 15,
                 f"Of the {len(material)} states above "
                 f"{d['min_share_for_extremes']:.0%} of national volume",
                 size=10, fill=TEXT3))
    listing = [(s, False) for s in material[:4]] + [(None, True)] \
        + [(s, False) for s in material[-3:]]
    for i, (s, spacer) in enumerate(listing):
        y = ty + 36 + i * 19
        if spacer:
            b.append(txt(rx + 4, y, "...", size=11, fill=TEXT3))
            continue
        top = s is material[0]
        bottom = s is material[-1]
        colour = S1 if top else (S2 if bottom else TEXT2)
        b.append(txt(rx + 4, y, s["state"], size=11,
                     fill=TEXT if (top or bottom) else TEXT2,
                     weight="600" if (top or bottom) else "400"))
        b.append(txt(rx + 246, y, f"{s['merchant_volume_share']:.1%}", size=11,
                     fill=colour, anchor="end",
                     weight="600" if (top or bottom) else "400"))

    hi, lo = material[0], material[-1]
    write_svg("india-merchant-map", card(
        H, "Exhibit 5 · Geography",
        f"{hi['state']} runs on merchants, {lo['state']} runs on transfers",
        f"Each state's merchant transactions as a share of its own, {d['period']}. All "
        f"36 states and union territories, with the seven too small to see given "
        f"numbered markers and a key.",
        b,
        f"Source: PhonePe Pulse per-state category files, {d['period']}. Measured, not "
        f"derived from ticket size. Boundaries built by site/scripts/build_india_map.py. "
        f"Computed by analysis/05_geo_gap.py.",
        f"Choropleth map of India for {d['period']}, showing each state's merchant "
        f"transactions as a share of its own transactions against the national "
        f"{nat:.1%}. {hi['state']} is highest at {hi['merchant_volume_share']:.1%} and "
        f"{lo['state']} lowest at {lo['merchant_volume_share']:.1%} among the "
        f"{len(material)} states above one percent of national volume. All 36 states "
        f"and union territories are shown, with seven small territories given numbered "
        f"markers and a key.",
    ))


# --------------------------------------------------------------- exhibit 7
def bank_margin_verdict():
    """Two panels: the margin gap that would not move, and what the market paid
    for it anyway. Neither half means much without the other."""
    d = load("chart_nim_slope")
    mv = load("chart_market_view")
    spread = load("chart_bank_spread")
    periods = d["periods"]
    series = {s["cohort"]: s["values"] for s in d["series"]}
    gaps = d["gap_bps"]
    medians = {s["cohort"]: s["median_price_return"] for s in mv["series"]}
    sp = {s["cohort"]: s for s in spread["series"]}

    H = 524
    py, ph = HEAD + 4, H - HEAD - 60
    lw = 446
    lx, rxp = PAD, PAD + lw + 22
    rw = W - PAD - rxp

    b = [panel(lx, py, lw, ph), panel(rxp, py, rw, ph)]

    # ---- left: the margin gap over a full rate cycle
    ax0, ax1 = lx + 70, lx + lw - 92
    ytop, ybase = py + 84, py + ph - 116
    lo = min(min(v) for v in series.values()) - 0.4
    hi = max(max(v) for v in series.values()) + 0.3
    slot = (ax1 - ax0) / (len(periods) - 1)

    def sx(i):
        return ax0 + slot * i

    def sy(v):
        return ybase - (ybase - ytop) * ((v - lo) / (hi - lo))

    b.append(txt(lx + 20, py + 28, "The gap that would not move", size=12.5,
                 fill=TEXT, weight="600"))
    b.append(txt(lx + 20, py + 46, d["metric"], size=10, fill=TEXT3))
    for g in (2.5, 3.0, 3.5, 4.0):
        b.append(line(ax0 - 14, sy(g), ax1 + 4, sy(g), GRID))
        b.append(txt(ax0 - 22, sy(g) + 4, f"{g:.1f}%", size=10, fill=TEXT3, anchor="end"))
    for i, p in enumerate(periods):
        b.append(txt(sx(i), ybase + 22, p, size=10.5, fill=TEXT3, anchor="middle"))
    b.append(line(ax0 - 14, ybase, ax1 + 4, ybase, BORDER))

    poly = ([(sx(i), sy(v)) for i, v in enumerate(series["Private"])]
            + [(sx(i), sy(v)) for i, v in reversed(list(enumerate(series["Public"])))])
    b.append('<polygon points="' + " ".join(f"{n(x)},{n(y)}" for x, y in poly)
             + f'" fill="{S1}" opacity="0.09"/>')
    for cohort, colour in (("Private", S1), ("Public", S2)):
        pts = [(sx(i), sy(v)) for i, v in enumerate(series[cohort])]
        b.append(polyline(pts, colour))
        for x, y in pts:
            b.append(dot(x, y, 3.2, colour))
        b.append(txt(ax1 + 12, pts[-1][1] - 2, cohort, size=11.5, fill=TEXT,
                     weight="600"))
        b.append(txt(ax1 + 12, pts[-1][1] + 13, f"{series[cohort][-1]:.2f}%",
                     size=10.5, fill=colour))
    for i, anchor, nudge in ((0, "start", 8), (len(periods) - 1, "end", -8)):
        mid = (sy(series["Private"][i]) + sy(series["Public"][i])) / 2
        b.append(txt(sx(i) + nudge, mid + 4, f"{gaps[i]} bps", size=11.5,
                     fill=SIGNAL_TEXT, anchor=anchor, weight="600"))

    # Where the gap comes from. Half of it is priced, half of it is funded, and
    # a slopegraph alone cannot say which.
    pricing = (sp["Private"]["yield_on_assets"] - sp["Public"]["yield_on_assets"]) * 100
    funding = (sp["Public"]["cost_of_funds"] - sp["Private"]["cost_of_funds"]) * 100
    dy0 = ybase + 46
    b.append(line(lx + 20, dy0 - 16, lx + lw - 20, dy0 - 16, GRID))
    b.append(txt(lx + 20, dy0, f"WHERE THE FY{spread['fy']} GAP COMES FROM", size=9,
                 fill=TEXT3, weight="600", spacing="1.1"))
    for i, (label, priv_v, pub_v, delta) in enumerate((
        ("Yield on assets", sp["Private"]["yield_on_assets"],
         sp["Public"]["yield_on_assets"], pricing),
        ("Cost of funds", sp["Private"]["cost_of_funds"],
         sp["Public"]["cost_of_funds"], funding),
    )):
        y = dy0 + 20 + i * 19
        b.append(txt(lx + 20, y, label, size=11, fill=TEXT2))
        b.append(txt(lx + 190, y, f"private {priv_v:.2f}%", size=11, fill=S1,
                     anchor="end"))
        b.append(txt(lx + 290, y, f"public {pub_v:.2f}%", size=11, fill=S2,
                     anchor="end"))
        b.append(txt(lx + lw - 20, y, f"{delta:+.0f} bps", size=11,
                     fill=TEXT, anchor="end", weight="600"))

    # ---- right: what the market paid for it
    tickers = sorted(mv["tickers"], key=lambda t: t["price_return"])
    bx0, bx1 = rxp + 142, rxp + rw - 62
    rmax = math.ceil(max(t["price_return"] for t in tickers))

    def bx(v):
        return bx0 + (bx1 - bx0) * (v / rmax)

    b.append(txt(rxp + 20, py + 28, "What the market paid for it", size=12.5,
                 fill=TEXT, weight="600"))
    b.append(txt(rxp + 20, py + 46,
                 f"Five year price return, {mv['window'][0]} to {mv['window'][1]}",
                 size=10, fill=TEXT3))
    row0, rh = py + 76, 22
    for g in range(0, int(rmax) + 1, 2):
        b.append(line(bx(g), row0 - 12, bx(g), row0 + len(tickers) * rh - 10, GRID))
        b.append(txt(bx(g), row0 + len(tickers) * rh + 8, f"{g * 100:.0f}%",
                     size=10, fill=TEXT3, anchor="middle"))
    cohort_colour = {"Private": S1, "Public": S2, "Fintech": S3}
    for i, t in enumerate(tickers):
        y = row0 + i * rh
        c = cohort_colour.get(t["cohort"], S4)
        b.append(txt(rxp + 16, y + 4, t["bank"], size=10.5, fill=TEXT2))
        b.append(line(bx(0), y, bx(t["price_return"]), y, c, width=1.6, opacity=0.55))
        b.append(dot(bx(t["price_return"]), y, 4, c))
        b.append(txt(bx(t["price_return"]) + 9, y + 4,
                     f"{t['price_return'] * 100:.0f}%", size=10, fill=c))
    b.append(line(bx(0), row0 - 12, bx(0), row0 + len(tickers) * rh - 10, BORDER))
    b.append(txt(rxp + 16, row0 + len(tickers) * rh + 32,
                 f"Cohort medians: public {medians['Public'] * 100:.0f}%, private "
                 f"{medians['Private'] * 100:.0f}%.", size=10.5, fill=TEXT2))
    b.append(txt(rxp + 16, row0 + len(tickers) * rh + 48,
                 "The two cohorts do not overlap at any point.", size=10.5,
                 fill=TEXT2))

    write_svg("bank-margin-verdict", card(
        H, "Exhibit 6 · Cohort margins and the market's verdict",
        "The thinner-margin cohort re-rated many times harder",
        f"Left: the margin gap across a full rate cycle. Right: what each of the "
        f"{len(tickers)} banks returned over five years.",
        b,
        f"Source: Yahoo Finance fundamentals and prices for {len(tickers)} NSE tickers. "
        f"{d['caveat']} Price only, excluding dividends. Computed by "
        f"analysis/02_banking_health.py.",
        f"Two panels. On the left, the private bank margin proxy runs from "
        f"{series['Private'][0]:.2f} to {series['Private'][-1]:.2f} percent between "
        f"{periods[0]} and {periods[-1]} and the public bank proxy from "
        f"{series['Public'][0]:.2f} to {series['Public'][-1]:.2f} percent, a gap of "
        f"{gaps[0]} basis points at the start and {gaps[-1]} at the end. On the right, "
        f"five year price returns for all {len(tickers)} banks, where the public bank "
        f"median of {medians['Public'] * 100:.0f} percent far exceeds the private bank "
        f"median of {medians['Private'] * 100:.0f} percent and the two cohorts do not "
        f"overlap.",
    ))


# --------------------------------------------------------------- exhibit 8
def nps_episodes():
    """Grouped bars: the same brand can hold the best and the worst episode."""
    d = load("chart_nps_episodes")
    eps = d["episodes"]
    series = d["series"]

    H = 458
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 96, px + pw - 24
    ytop, ybase = py + 78, py + ph - 50
    lo, hi = -60.0, 60.0

    def sy(v):
        return ybase - (ybase - ytop) * ((v - lo) / (hi - lo))

    zero = sy(0)
    group = (x1 - x0) / len(eps)
    bw = min(46, group / (len(series) + 1.4))
    cohort_colour = {"Neobank / payments app": S1, "Private bank": S2, "Public bank": S4}

    b = [panel(px, py, pw, ph)]
    for g in (-60, -40, -20, 0, 20, 40, 60):
        b.append(line(x0 - 12, sy(g), x1, sy(g), BORDER if g == 0 else GRID))
        b.append(txt(x0 - 20, sy(g) + 4, f"{g:+d}" if g else "0", size=10,
                     fill=TEXT3, anchor="end"))

    best, worst = (None, -999.0), (None, 999.0)
    for gi, ep in enumerate(eps):
        gx = x0 + group * gi
        b.append(txt(gx + group / 2, ybase + 26, ep, size=11.5, fill=TEXT2,
                     anchor="middle"))
        for si, s in enumerate(series):
            v = s["values"][gi]
            x = gx + (group - bw * len(series)) / 2 + si * bw
            c = cohort_colour.get(s["cohort"], S4)
            b.append(rect(x + 1, min(sy(v), zero), bw - 2, abs(sy(v) - zero), c, rx=2,
                          opacity=None if c == S1 else 0.8))
            b.append(txt(x + bw / 2, sy(v) + (-6 if v >= 0 else 14),
                         f"{v:+.0f}", size=9.5, fill=TEXT2, anchor="middle"))
            if v > best[1]:
                best = (s["cohort"], v)
            if v < worst[1]:
                worst = (s["cohort"], v)

    for i, s in enumerate(series):
        c = cohort_colour.get(s["cohort"], S4)
        b.append(rect(px + 20 + i * 246, py + 18, 10, 10, c, rx=2))
        b.append(txt(px + 37 + i * 246, py + 27,
                     f"{s['cohort']} (overall {s['overall']:+.1f})", size=11, fill=TEXT2))

    b.append(txt(px + 20, py + 54,
                 f"Net Promoter Score by episode. The {best[0].split(' /')[0]} cohort "
                 f"owns both the best ({best[1]:+.0f}) and the worst "
                 f"({worst[1]:+.0f}); its overall score, {series[0]['overall']:+.1f}, "
                 f"shows neither.", size=12))

    bw_badge = 128
    b.append(rect(W - PAD - bw_badge - 16, py + 14, bw_badge, 22, "none", rx=11,
                  stroke=S1, sw=1.2))
    b.append(txt(W - PAD - bw_badge / 2 - 16, py + 29, "SYNTHETIC DATA", size=10,
                 fill=SIGNAL_TEXT, anchor="middle", weight="600", spacing="1.2"))

    write_svg("nps-episodes", card(
        H, "Exhibit 7 · Episode-level NPS",
        "One brand holds both the best and the worst episode in the market",
        f"{d['respondents']:,} simulated respondents, {len(eps)} service episodes, "
        f"three provider cohorts. The method is real; the panel is not.",
        b,
        f"{d['label']}. Seed {d['seed']}, so it reproduces exactly. NPS as a method is "
        f"public; no proprietary benchmark data is used. "
        f"Computed by analysis/04_survey_nps.py.",
        f"Grouped bar chart of synthetic Net Promoter Scores across {len(eps)} service "
        f"episodes for three provider cohorts. The {best[0]} cohort scores "
        f"{best[1]:+.0f} on its best episode and {worst[1]:+.0f} on its worst, while "
        f"its overall score is {series[0]['overall']:+.1f}. The data is synthetic and "
        f"illustrates the method, not the market.",
    ))


# --------------------------------------------------------------- exhibit 9
def fund_shelf():
    """Paired bars: how much of the shelf is packaging rather than strategy."""
    d = load("chart_fund_shelf")
    rows = [r for r in d["by_asset_class"] if r["schemes"] >= 100]

    H = 440
    px, pw = PAD, W - PAD * 2
    py, ph = HEAD + 4, H - HEAD - 60
    x0, x1 = px + 152, px + pw - 196
    top = py + 74
    row_h = (ph - 104) / len(rows)
    xmax = max(r["schemes"] for r in rows)

    def sx(v):
        return x0 + (x1 - x0) * (v / xmax)

    b = [panel(px, py, pw, ph)]
    b.append(rect(px + 20, py + 18, 10, 10, S4, rx=2))
    b.append(txt(px + 38, py + 27, "Listed schemes", size=12))
    b.append(rect(px + 168, py + 18, 10, 10, S1, rx=2))
    b.append(txt(px + 186, py + 27, "Distinct strategies", size=12))
    b.append(txt(px + 20, py + 50,
                 f"{d['listed_schemes']:,} schemes resolve to "
                 f"{d['distinct_strategies']:,} strategies, about "
                 f"{d['listed_schemes'] / d['distinct_strategies']:.1f} wrappers each",
                 size=12, fill=TEXT))

    for g in (0, 2000, 4000, 6000, 8000):
        if g > xmax:
            continue
        b.append(line(sx(g), top - 8, sx(g), top + row_h * len(rows) - 8, GRID))
        b.append(txt(sx(g), top + row_h * len(rows) + 10, f"{g:,}", size=10,
                     fill=TEXT3, anchor="middle"))

    for i, r in enumerate(rows):
        y = top + i * row_h
        ratio = r["schemes"] / r["strategies"]
        b.append(txt(px + 20, y + 14, r["asset_class"], size=12, fill=TEXT2))
        b.append(rect(x0, y, sx(r["schemes"]) - x0, 11, S4, rx=2, opacity=0.8))
        b.append(rect(x0, y + 13, sx(r["strategies"]) - x0, 11, S1, rx=2))
        b.append(txt(sx(r["schemes"]) + 8, y + 9, f"{r['schemes']:,}", size=10.5,
                     fill=TEXT2))
        b.append(txt(x1 + 86, y + 16, f"{ratio:.1f}x", size=12,
                     fill=SIGNAL_TEXT if ratio >= 4 else TEXT2,
                     weight="600" if ratio >= 4 else "400"))
    b.append(txt(x1 + 86, top - 14, "WRAPPERS", size=9, fill=TEXT3, weight="600",
                 spacing="1.1"))

    debt = next(r for r in rows if r["asset_class"] == "Debt")
    write_svg("fund-shelf", card(
        H, "Exhibit 8 · The fund shelf",
        "India's fund shelf is far more administered than it is diverse",
        f"Listed schemes against distinct strategies by asset class, {d['nav_date']}, "
        f"across {d['fund_houses']} fund houses.",
        b,
        f"Source: AMFI daily NAV file, {d['nav_date']}. {d['caveat']} Computed by "
        f"analysis/07_wealth_amfi.py.",
        f"Paired bar chart. India's {d['listed_schemes']:,} listed mutual fund schemes "
        f"resolve to {d['distinct_strategies']:,} distinct strategies, about "
        f"{d['listed_schemes'] / d['distinct_strategies']:.1f} wrappers per strategy. "
        f"Debt is the heaviest at {debt['schemes']:,} schemes over "
        f"{debt['strategies']:,} strategies.",
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
    mv = load("chart_market_view")

    retail = next(s for s in split["series"] if s["category"] == "Retail")
    p2p = next(s for s in split["series"] if s["category"] == "P2P")
    apps = {s["app"]: s["values"][-1] for s in trend["series"]}
    priv = next(s for s in spread["series"] if s["cohort"] == "Private")
    pub = next(s for s in spread["series"] if s["cohort"] == "Public")
    med = {s["cohort"]: s["median_price_return"] for s in mv["series"]}

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
        ("Five year price return, public against private banks",
         f"**{med['Public']:+.0%} / {med['Private']:+.0%}** median",
         f"Yahoo Finance, {mv['window'][0]} to {mv['window'][1]}"),
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
    mv = load("chart_market_view")
    gap = load("chart_state_gap")

    retail = next(s for s in split["series"] if s["category"] == "Retail")
    p2p = next(s for s in split["series"] if s["category"] == "P2P")
    lead, second = ms["apps"][0], ms["apps"][1]
    med = {s["cohort"]: s["median_price_return"] for s in mv["series"]}
    material = sorted((s for s in gap["states"]
                       if s["volume_share"] >= gap["min_share_for_extremes"]),
                      key=lambda s: s["merchant_volume_share"])

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
    lines += fact("median five year price return, public banks", med["Public"],
                  "price return", f"{mv['window'][0]} to {mv['window'][1]}",
                  "Yahoo Finance prices")
    lines += fact("median five year price return, private banks", med["Private"],
                  "price return", f"{mv['window'][0]} to {mv['window'][1]}",
                  "Yahoo Finance prices")
    lines += fact("highest merchant share of own transactions, material states",
                  f"{material[-1]['state']} {material[-1]['merchant_volume_share']}",
                  "share of own transactions", gap["period"], "PhonePe Pulse")
    lines += fact("lowest merchant share of own transactions, material states",
                  f"{material[0]['state']} {material[0]['merchant_volume_share']}",
                  "share of own transactions", gap["period"], "PhonePe Pulse")
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
    kpi_band()
    monetisation_gap()
    growth_bridge()
    market_mekko()
    market_structure()
    india_map()
    bank_margin_verdict()
    nps_episodes()
    fund_shelf()
    patch_readme()


if __name__ == "__main__":
    main()
