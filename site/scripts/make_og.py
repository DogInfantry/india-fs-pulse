"""Generate the social preview card from the computed data.

A portfolio link gets shared on LinkedIn, in email and over WhatsApp. Without an
og:image those all render as a blank rectangle. This draws the headline FINDING
- not a logo - so the preview carries the argument before anyone clicks.

Reads the same JSON the site reads, so the card cannot state a number the site
does not. Run via `python run.py site`.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "src" / "data"
OUT = ROOT / "site" / "public" / "og.png"

W, H = 1200, 630
INK, SURFACE, SIGNAL = "#0C0F14", "#131820", "#C02734"
TEXT, MUTED, DIM = "#E9EDF2", "#A6B0BE", "#6E7987"

SERIF = ["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/times.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
SANS = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
SANS_B = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def font(paths: list[str], size: int):
    for candidate in paths:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def wrap(draw, text: str, fnt, max_w: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def main() -> None:
    hero = json.loads((DATA / "upi_monetisation.json").read_text(encoding="utf-8"))
    merchant = next(c for c in hero["categories"] if c["category"] == "Retail")

    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 10, H], fill=SIGNAL)                       # spine
    d.rectangle([0, H - 118, W, H], fill=SURFACE)                 # stat band

    f_kick = font(SANS_B, 21)
    f_head = font(SERIF, 61)
    f_sub = font(SANS, 25)
    f_num = font(SERIF, 44)
    f_lab = font(SANS, 17)
    f_foot = font(SANS, 18)

    d.text((72, 68), "INDIA FS PULSE  ·  FINANCIAL SERVICES  ·  " + hero["period"],
           font=f_kick, fill=SIGNAL)

    head = "India built the world's largest payments network. It priced the busy half at zero."
    y = 122
    for line in wrap(d, head, f_head, W - 150):
        d.text((72, y), line, font=f_head, fill=TEXT)
        y += 74

    sub = (f"Merchant payments are {merchant['volume_share']:.1%} of transactions "
           f"but {merchant['value_share']:.1%} of the rupees — and earn no MDR.")
    y += 10
    for line in wrap(d, sub, f_sub, W - 160):
        d.text((72, y), line, font=f_sub, fill=MUTED)
        y += 34

    stats = [
        (f"{merchant['volume_share']:.1%}", "of transactions"),
        (f"{merchant['value_share']:.1%}", "of value"),
        (f"{hero['registered_merchants'] / 1e6:.1f}M", "merchants"),
        ("Rs 0", "payment revenue"),
    ]
    for i, (value, label) in enumerate(stats):
        x = 72 + i * 268
        d.text((x, H - 96), value, font=f_num, fill=SIGNAL if i == 3 else TEXT)
        d.text((x, H - 42), label.upper(), font=f_lab, fill=DIM)

    d.text((W - 72, 74), "india-fs-pulse.vercel.app", font=f_foot, fill=DIM, anchor="ra")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"   wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} kB, {W}x{H})")


if __name__ == "__main__":
    main()
