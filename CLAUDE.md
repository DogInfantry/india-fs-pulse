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
