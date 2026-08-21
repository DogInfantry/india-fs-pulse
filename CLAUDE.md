# CLAUDE.md — India FS Pulse

Operating manual for this repo. Read before touching anything.

## Project

**India FS Pulse** — a code-driven Financial Services research portfolio:
reproducible Python pipeline → analysis → static Astro site → Vercel.

Built as a work sample for **Associate, Financial Services, Bain Capability Network
FS Centre of Expertise** (Job ID 90399): open-ended research, industry POV, sector
scans, survey analytics, PE diligence support, client-ready dashboards, dealing with
ambiguity.

**Central question:** India built the world's largest real-time payments network.
Under zero-MDR it earns almost nothing directly. Who captures the value, and is there
an investable business model?

- Live: https://india-fs-pulse.vercel.app
- Repo: https://github.com/DogInfantry/india-fs-pulse
- **All links, evaluated tooling and data endpoints live in `docs/resources.md`.**

**Stack:** Python 3.14 + pandas (no polars) · Astro 5 static · Tailwind v4 (Vite
plugin) · ECharts lazily imported · hand-written SVG components · Vercel · GitHub
Actions monthly refresh.

## Commands

`make` is unavailable on Windows. Single entry point:

```bash
python run.py data      # fetch -> validate -> transform   (NO SECRETS REQUIRED, ~115s)
python run.py analyze   # 7 analysis modules -> insights/*.md + site/src/data/*.json
python run.py site      # OG card + astro build
python run.py all
python docs/build_docs.py   # regenerate docs/sources.md and docs/data-dictionary.md
```

## Architecture — decisions and why

1. **PhonePe Pulse is the primary source, not NPCI's headline series.** Pulse is open,
   needs no auth, is current to 2026 Q2, and is the only feed that splits P2P from
   merchant — which *is* the monetisation question. The NPCI CKAN mirror everyone
   reaches for is frozen at 2023-08.
2. **NPCI's own site is browser-only.** It returns HTTP 403 to every scripted request,
   so its two tables are transcribed into `data-pipeline/data/manual/` with per-row
   provenance. This is honest sourcing, not a workaround to hide.
3. **Shares are computed against the national total**, never against the sum of the
   listed apps — NPCI caps its table at ten rows, so summing them would overstate every
   share. This also yields a real "all other apps" residual and a genuine cross-source
   reconciliation (the ten cover 94–99% of national volume).
4. **The analysis layer never hardcodes a figure.** Memos are f-strings interpolating
   computed values, so prose cannot drift from data. Claims that depend on which way a
   number falls (e.g. "pricing or funding?") are written as *conditionals in code*.
5. **No charting library for the bespoke exhibits.** Five server-rendered SVG components
   carry the consulting vocabulary with zero client JS. ECharts is dynamically imported
   for the dashboard charts, keeping the entry script ~2.6 kB.
6. **Colour is measured, not eyeballed.** `--signal` is for fills (3:1 suffices for
   non-text); `--signal-text` exists because small red text needs 4.5:1 on every surface
   token. Verified with Lighthouse.

## File map

| Path | Role |
|---|---|
| `run.py` | Task runner. Registers every fetch / analysis script — **add new scripts here** |
| `data-pipeline/common.py` | Paths, `get_json`/`get_text`, `expect*` guards, `write_processed`, `record_source`, `read_seeded_csv` |
| `data-pipeline/fetch/fetch_pulse.py` | **Primary.** National + state transactions, user/merchant base |
| `data-pipeline/fetch/fetch_upi_history.py` | NPCI monthly: CKAN mirror + manual seed, joined |
| `data-pipeline/fetch/fetch_upi_apps.py` | NPCI per-app shares, HHI, national reconciliation |
| `data-pipeline/fetch/fetch_bank_stocks.py` | yfinance fundamentals (NIM proxy) + 5y prices; retries flaky tickers |
| `data-pipeline/fetch/fetch_worldbank.py` · `fetch_amfi.py` | Inclusion denominators · fund scheme universe |
| `data-pipeline/data/manual/*.csv` | Hand-seeded NPCI rows. **Header comments are `#`-leading lines only** |
| `data-pipeline/transform/build_kpis.py` | Processed → KPI layer + `site/src/data/*.json` |
| `analysis/_lib.py` | `load`, `write_json`, `write_memo`, `inr`, `pct` |
| `analysis/01..07_*.py` | Seven modules → `insights/*.md` + chart JSON |
| `site/src/pages/index.astro` | The whole scrollable report: 16 exhibits, 10 sections |
| `site/src/components/charts/` | `Marimekko`, `Waterfall`, `Slopegraph`, `SmallMultiples`, `SlopeLines` |
| `site/src/components/` | `Figure` (action-title frame), `EChart`, `Workbench`, `GapMatrix`, `ExecSummary`, `Contact` |
| `site/scripts/make_og.py` | Social card, drawn from computed data (Pillow) |
| `docs/build_docs.py` | Generates `sources.md` + `data-dictionary.md` from the provenance ledger |
| `docs/resources.md` | **All external links, tooling verdicts, data endpoints** |
| `docs/stack-decisions.md` | What was rejected and why |
| `docs/REFRESH.md` | How to refresh the browser-only NPCI tables |

## Non-negotiable rules

1. **Never fabricate a number.** Not fetched or computed → write `TODO` and leave it
   visible. Four months NPCI does not publish are left as gaps, never interpolated.
2. **Every figure traces to `docs/sources.md`** with source URL and access date.
   That file is *generated* from the fetchers' provenance ledger, so it cannot drift.
3. **Synthetic data is labelled synthetic** — in the filename, on the chart, and in the
   memo. The NPS survey is the only synthetic dataset here.
4. **Answer-first.** Chart titles state the conclusion, not the contents.
5. **The pipeline stays secret-free.** `python run.py data` must work with zero
   environment variables. Key-gated sources skip gracefully.
6. **No firm trademarks.** No Bain/BCG/McKinsey logos, colours or proprietary data.
   NPS as a *method* is public; NPS Prism data is not. The palette is original.
7. **Date-stamp every snapshot.** Any single-period figure carries its period.
8. **Never `pd.read_csv(comment="#")` on the seeded files.** Use `common.read_seeded_csv()`.
9. **Stale data is labelled stale**, and the chart shows the seam rather than hiding it.
10. **Fail loud on shape change.** Fetchers validate schema *and* plausible ranges.

## Current state — all green

- `python run.py data` — 115s, zero secrets, 15 processed datasets
- `python run.py analyze` — 7 modules, **21 artefacts byte-identical across runs**
- `python run.py site` — 9 pages
- Lighthouse: **Accessibility 100 · Best Practices 100 · SEO 100 · Agentic 100**,
  63 audits passed / 0 failed. **LCP 676 ms, CLS 0.00**
- Deployed, publicly reachable, auto-deploys on push
- CI refresh workflow verified green on Linux / Python 3.12, with a real data commit

### Headline findings (all computed, none typed in)

| Finding | Figure |
|---|---|
| Merchant payments: share of transactions vs share of value | **63.9% / 23.0%** |
| Merchant growth contribution to all volume growth since 2018Q1 | **64%** |
| PhonePe / Google Pay share of national UPI volume | **45.9% / 32.3%** — both above the 30% cap |
| Transactions that must change app for the cap to bind | **4.3 bn a month** |
| Time for the leader to reach 30% at observed drift | **~470 months** |
| Private vs public bank NIM gap | **114 bps** (59 pricing + 56 funding) |
| Five-year price return, public vs private banks | **+284% vs +17%** |
| UPI transactions per banked adult per month | **14.9**, up from 4.0 in 2021 |
| Fund schemes vs distinct strategies | **14,288 → 3,353** (4.3× wrappers) |

## Active task

**Pass 2 is complete, committed and deployed.** Nothing is half-finished.

The one open item is external: **the LinkedIn URL.** `site/src/components/Contact.astro`
has `const LINKEDIN: string | null = null` and renders that row only when it is set —
deliberately, so no placeholder link ships. Set the constant and rebuild.

## Next steps, in order

1. **LinkedIn URL** into `Contact.astro` (one line, blocked on the user).
2. **Excel + PowerPoint deliverables** — the JD names both as hard requirements, and
   the gap matrix currently carries an honest "Not covered" row for them. The user chose
   web-only; the pipeline emits tidy CSV, so `openpyxl` + `python-pptx` is roughly an
   hour if they change their mind.
3. **Extend the per-app series** — currently 12 months (2023-12 → 2026-07). More months
   sharpen the HHI trend. Browser-transcribed; see `docs/REFRESH.md`.
4. **AMFI quarterly AAUM** — would restate the wealth module in rupees rather than
   scheme counts, which is the version that informs a fee pool.
5. **Insurance** — the last JD-named sector with no coverage. IRDAI is PDF-only.

## Gotchas — things that actually bit us

- **`#` is data, not a comment.** NPCI marks third-party providers with a trailing `#`
  ("Phone Pe #"). `pd.read_csv(comment='#')` silently truncated every row to `NaN`.
- **Fund houses have brackets too.** `IL&FS Mutual Fund (IDF)` was parsed as a category
  header, misattributing 2,535 AMFI rows. Category headers must match
  `^(Open Ended|Close Ended|Interval Fund) Schemes?\(`.
- **₹1 lakh crore = 1e12**, not 1e13. Caught before it reached a chart.
- **CKAN's date column is `YYYY-DD-MM`**, not ISO. `2023-01-08` is 1 August 2023.
- **NPCI's URL moved** to `/product/upi/...`; `/what-we-do/upi/...` 404s.
- **yfinance throws `KeyError` intermittently** on healthy tickers, silently dropping a
  bank from a cohort mean. Retried three times, plus a per-cohort minimum of 3 banks.
- **Paytm is not a bank** — its NIM is meaningless, so it is blanked rather than averaged
  in. The range guard caught this on the first run.
- **Never run two pipeline invocations at once** — they race on the same output files.
- **Astro heredocs:** escaped quotes inside Python heredocs collapse. Prefer
  `chr(10).join(...)` over `"\n".join(...)` when generating code via a heredoc.
- **`npx astro check` is very slow** here (minutes). Use `npx astro build` to validate.
- **IntersectionObserver never fires in a hidden tab**, so lazy ECharts appear "broken"
  when the browser pane is not composited. That is the environment, not the code.
