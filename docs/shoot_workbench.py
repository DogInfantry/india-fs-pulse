#!/usr/bin/env python
"""Photograph the live workbench for the README.

Run once, commit the output. Same convention as site/scripts/build_india_map.py,
and deliberately NOT in `run.py`: this needs a browser and the deployed site,
neither of which belongs in a pipeline whose whole promise is that it runs with
no credentials and no surprises.

    python docs/shoot_workbench.py

Why a screenshot at all. Every other exhibit in the README is generated from
committed data, and should be. But the workbench is the one artefact whose point
is that it responds: pick a state and the table and the detail panel follow.
A generated SVG cannot show that, and pretending otherwise would undersell the
thing the job description actually asks for.

Why it does not just point a headless browser at the page and scroll. Two
things defeat that, and both were tried:

  * `html { scroll-behavior: smooth }` never completes under a virtual time
    budget, so `#workbench` in the URL leaves the shot at the top of the page.
  * With smooth scrolling disabled the jump lands in the scrolly section's
    sticky spacer, which lays out differently in headless and photographs as an
    empty rectangle.

So this lifts the workbench's own server-rendered markup out of the delivered
HTML and renders that alone, against the site's own stylesheet. The cartogram is
41 buttons and a table rather than a lazy canvas, so it paints with no
JavaScript at all. The result is also a tighter image than a viewport grab.

The detail panel photographs in its default state, prompting for a selection.
That is honest: it is what a reader sees before they touch anything.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SITE = "https://india-fs-pulse.vercel.app"
ANCHOR = 'id="workbench"'
OUT = Path(__file__).resolve().parent / "assets" / "workbench.png"
SHOT = (1500, 1600)      # generous; the image is cropped back to its content
BUDGET_MS = 20000
MARGIN = 20

# Chrome is not on PATH on a stock Windows box, so look where it actually lives.
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome() -> str:
    for name in ("google-chrome", "chromium", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    sys.exit("no Chrome found. Install it, or capture docs/assets/workbench.png by hand.")


def extract_section(html: str) -> str:
    """Pull out the workbench <section>, balancing nested ones."""
    at = html.find(ANCHOR)
    if at < 0:
        sys.exit(f"{ANCHOR} not found in the delivered HTML. Did the page change?")
    start = html.rfind("<section", 0, at)
    depth, i = 0, start
    for m in re.finditer(r"<section\b|</section>", html[start:]):
        depth += 1 if m.group(0).startswith("<section") else -1
        if depth == 0:
            return html[start:start + m.end()]
    sys.exit("the workbench section never closes. Did the page change?")


def build_page(html: str, section: str) -> str:
    body = re.search(r"<body[^>]*>", html)
    body_tag = body.group(0) if body else "<body>"
    head = html[:html.find("</head>")]
    links = re.findall(r'<link[^>]*rel="stylesheet"[^>]*>', head)
    if not links:
        sys.exit("no stylesheet link in the page head. Did the build change?")
    # The design tokens are inlined in a head <style>, not in the linked sheet.
    # Without them every var() falls back and the whole thing renders in serif.
    inline = re.findall(r"<style[^>]*>.*?</style>", head, re.S)
    if not any("--font-sans" in s for s in inline):
        sys.exit("the design tokens are no longer inlined in the head. "
                 "Check where site/src/styles/tokens.css ends up in the build.")
    links += inline
    # The workbench's own behaviour ships as its own module, so pulling that one
    # in is enough to make the thing live without the rest of the page's script.
    scripts = [s for s in re.findall(r'<script[^>]*type="module"[^>]*src="[^"]*"[^>]*>'
                                     r'\s*</script>', html) if "Workbench" in s]
    if not scripts:
        sys.exit("the Workbench module script is missing. Did the build change?")
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<base href='{SITE}/'>" + "".join(links) +
        # Lifting the section out of the page loses the body-level theme, so the
        # two surface tokens are restated here. Values from site/src/styles/tokens.css.
        "<style>body{margin:0;padding:26px;background:#0C0F14;color:#E9EDF2}"
        "#shot{max-width:1180px;margin:0 auto}</style>"
        f"</head>{body_tag}<div id='shot'>{section}</div>" + "".join(scripts) +
        "</body></html>"
    )


def crop_to_content(png: Path) -> int:
    """Trim to what actually rendered, and report how many colours it carries.
    A blank frame is the one failure mode that would otherwise ship silently."""
    from PIL import Image, ImageChops
    with Image.open(png) as im:
        im = im.convert("RGB")
        bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
        box = ImageChops.difference(im, bg).getbbox()
        if box is None:
            return 0
        left, top, right, bottom = box
        im = im.crop((max(left - MARGIN, 0), max(top - MARGIN, 0),
                      min(right + MARGIN, im.size[0]),
                      min(bottom + MARGIN, im.size[1])))
        colours = im.getcolors(maxcolors=200_000)
        im.save(png)
        print(f"   cropped to {im.size[0]}x{im.size[1]}, "
              f"{len(colours) if colours else '200,000+'} distinct colours")
        return len(colours) if colours else 200_000


def main() -> None:
    chrome = find_chrome()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f">> {SITE}")
    with urllib.request.urlopen(SITE, timeout=60) as r:
        html = r.read().decode("utf-8")
    section = extract_section(html)
    print(f"   workbench markup: {len(section):,} bytes, "
          f"{section.count('<button')} tiles, {section.count('<table')} table")

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "workbench.html"
        page.write_text(build_page(html, section), encoding="utf-8")
        shot = Path(tmp) / "shot.png"
        subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={SHOT[0]},{SHOT[1]}",
             f"--virtual-time-budget={BUDGET_MS}",
             f"--screenshot={shot}", page.as_uri()],
            check=True, capture_output=True,
        )
        if not shot.exists():
            sys.exit("Chrome produced no file")
        if crop_to_content(shot) < 400:
            sys.exit("the frame came back blank. Capture docs/assets/workbench.png "
                     "by hand instead of committing an empty panel.")
        shutil.copyfile(shot, OUT)

    root = Path(__file__).resolve().parents[1]
    print(f"   wrote {OUT.relative_to(root)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
