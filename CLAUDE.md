# CLAUDE.md — India FS Pulse

Operating manual for this repo. Read before touching anything.

## What this is

A code-driven Financial Services research portfolio: reproducible Python pipeline ->
analysis -> static Astro site. Built as a work sample calibrated to the **Associate,
Financial Services, Bain Capability Network FS Centre of Expertise** JD (Job ID 90399):
open-ended research, industry POV, sector scans, survey analytics, PE diligence support,
client-ready dashboards, and dealing with ambiguity.

**Central question:** India built the world's largest real-time payments network.
Under zero-MDR it earns almost nothing directly. Who captures the value, and is there
an investable business model?

## Commands

`make` is unavailable on Windows. Single entry point:

```bash
python run.py data      # fetch -> clean -> transform  (NO SECRETS REQUIRED)
python run.py analyze   # analysis scripts -> insights/*.md + site/src/data/*.json
python run.py site      # astro build
python run.py all
```

## Non-negotiable rules

1. **Never fabricate a number.** If a value was not fetched or computed, write `TODO`
   and leave it visible. No plausible-looking placeholders. Ever.
2. **Every figure traces to `docs/sources.md`** with source URL and access date.
3. **Synthetic data is labelled synthetic** — in the filename, on the chart, and in the
   memo. The NPS survey is the only synthetic dataset in this repo.
4. **Answer-first.** Chart titles state the conclusion, not the contents.
   "Merchant payments are 64% of transactions but 23% of rupees" — not "P2P vs P2M split".
5. **The pipeline stays secret-free.** Everything in `python run.py data` must work with
   zero environment variables. Key-gated sources skip gracefully with a printed notice.
6. **No firm trademarks.** No Bain/BCG/McKinsey logos, colours, or proprietary data.
   NPS as a *method* is public; NPS Prism data is not. The palette is original.
7. **Date-stamp every snapshot.** Market shares move monthly. Any single-period figure
   carries its period in the subtitle.
8. **Stale data is labelled stale.** The NPCI CKAN series ends 2023-08. Any chart using
   it says so on its face.

## Data provenance (verified 2026-08-20)

| Source | Coverage | Access | Note |
|---|---|---|---|
| PhonePe Pulse (GitHub raw) | 2018 - 2026 Q2 | open | **Primary.** P2P/Retail/Utility split, state, district |
| NPCI via India Data Portal CKAN | 2016-08 - **2023-08** | open | History only. **Stale.** Date column is `YYYY-DD-MM`, not ISO |
| NPCI official site | current | **403 / WAF** | Not scriptable. Hand-seeded into `data/manual/`, see `docs/REFRESH.md` |
| yfinance (NSE) | current | open | `.financials` carries real Net Interest Income / Interest Income |
| World Bank API | to 2024 | open | Account ownership, GDP |
| AMFI `NAVAll.txt` | daily | open | Semicolon-delimited |
| data.gov.in | varies | public sandbox key | No repo secret needed |

## Design tokens

Defined once in `site/src/styles/tokens.css`. Never hardcode a hex value in a component
or a chart config — read the CSS variable, or import from `site/src/lib/theme.ts` for
canvas-based charts that cannot read CSS.

Palette is firm-neutral editorial: ink/paper neutrals, one deep crimson signal colour,
one deep teal secondary, amber for the third series. Grey de-emphasises; crimson focuses
attention (Knaflic). High data-ink: no chart borders, no gridline clutter, direct labels
over legends where it fits.

## Conventions

- Conventional Commits: `feat:` `fix:` `data:` `docs:` `chore:`
- Python: stdlib + pandas. No new dependency for something a few lines can do.
- Fetchers: pull -> validate schema -> **fail loud on shape change** -> write processed.
- Processed data is committed (it is the site's input); raw pulls are gitignored.
- Charts: ECharts for dashboards, D3 for the bespoke consulting charts
  (Marimekko, waterfall, slopegraph), Perspective (WASM) for the pivot workbench.
- Astro islands: `client:visible` for anything heavy. Lighthouse perf target >= 95.
