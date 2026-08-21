# CLAUDE.md: India FS Pulse

Operating manual for this repo. Read before touching anything.

## Project

**India FS Pulse**: a code-driven Financial Services research portfolio:
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

## Architecture: decisions and why

1. **PhonePe Pulse is the primary source, not NPCI's headline series.** Pulse is open,
   needs no auth, is current to 2026 Q2, and is the only feed that splits P2P from
   merchant, which *is* the monetisation question. The NPCI CKAN mirror everyone
   reaches for is frozen at 2023-08.
2. **NPCI's own site is browser-only.** It returns HTTP 403 to every scripted request,
   so its two tables are transcribed into `data-pipeline/data/manual/` with per-row
   provenance. This is honest sourcing, not a workaround to hide.
3. **Shares are computed against the national total**, never against the sum of the
   listed apps: NPCI caps its table at ten rows, so summing them would overstate every
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
| `run.py` | Task runner. Registers every fetch / analysis script, **add new scripts here** |
| `data-pipeline/common.py` | Paths, `get_json`/`get_text`, `expect*` guards, `write_processed`, `record_source`, `read_seeded_csv` |
| `data-pipeline/fetch/fetch_pulse.py` | **Primary.** National + state transactions, user/merchant base |
| `data-pipeline/fetch/fetch_pulse_state_mix.py` | P2P / merchant / utility split **within** each state. Reconciles the 36 state files against the country file |
| `data-pipeline/fetch/fetch_upi_history.py` | NPCI monthly: CKAN mirror + manual seed, joined |
| `data-pipeline/fetch/fetch_upi_apps.py` | NPCI per-app shares, HHI, national reconciliation |
| `data-pipeline/fetch/fetch_bank_stocks.py` | yfinance fundamentals (NIM proxy) + 5y prices; retries flaky tickers |
| `data-pipeline/fetch/fetch_worldbank.py` · `fetch_amfi.py` | Inclusion denominators, NPLs, private credit · fund scheme universe |
| `data-pipeline/fetch/fetch_fred_rates.py` | India call money rate, monthly to 2026-06. **Keyless** CSV endpoint, so rule 5 holds |
| `data-pipeline/data/manual/*.csv` | Hand-seeded NPCI rows. **Header comments are `#`-leading lines only** |
| `data-pipeline/transform/build_kpis.py` | Processed → KPI layer + `site/src/data/*.json` |
| `analysis/_lib.py` | `load`, `write_json`, `write_memo`, `inr`, `pct` |
| `analysis/01..07_*.py` | Seven modules → `insights/*.md` + chart JSON |
| `site/src/pages/index.astro` | The whole scrollable report: 16 exhibits, 10 sections |
| `site/src/components/charts/` | `Marimekko`, `Waterfall`, `Slopegraph`, `SmallMultiples`, `SlopeLines`, `HexCartogram`, `IndiaChoropleth` |
| `site/src/components/` | `Figure` (action-title frame), `EChart`, `Workbench` (cartogram + table + detail, linked), `GapMatrix` (Harvey balls), `ExecSummary`, `Contact`, `Monogram`, `BrandMark`, `Scrolly` |
| `site/scripts/make_og.py` | Social card, drawn from computed data (Pillow) |
| `site/scripts/build_india_map.py` | **Run once, output committed.** Boundary file for the choropleth; asserts 36 states and India's official extent |
| `docs/build_docs.py` | Generates `sources.md` + `data-dictionary.md` from the provenance ledger |
| `docs/resources.md` | **All external links, tooling verdicts, data endpoints** |
| `docs/stack-decisions.md` | What was rejected and why |
| `docs/REFRESH.md` | How to refresh the browser-only NPCI tables |

## Non-negotiable rules

1. **Never fabricate a number.** Not fetched or computed → write `TODO` and leave it
   visible. Four months NPCI does not publish are left as gaps, never interpolated.
2. **Every figure traces to `docs/sources.md`** with source URL and access date.
   That file is *generated* from the fetchers' provenance ledger, so it cannot drift.
3. **Synthetic data is labelled synthetic**: in the filename, on the chart, and in the
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
11. **No dashes as punctuation.** No em dashes, and no ` - ` joining clauses. Use a comma,
    colon, semicolon or full stop. Hyphenated compounds are fine and expected: `zero-MDR`,
    `answer-first`, `Herfindahl-Hirschman`. This applies to memo generators too, since the
    memos are regenerated from them.

## Current state: all green

- `python run.py data`, ~120s, zero secrets, 8 fetchers, 17 processed datasets
- `python run.py analyze`, 7 modules, **26 artefacts byte-identical across runs**
- `python run.py site`, 9 pages
- `python site/scripts/build_india_map.py`, run once, output committed to `site/public/`
- Lighthouse on the **production URL**: **Accessibility 100 · Best Practices 100 ·
  SEO 100 · Agentic 100**, 62 audits passed / 0 failed
- 34 commits, all authored `DogInfantry <ankleshrawat5@gmail.com>` except two genuine
  `github-actions[bot]` refresh commits. Working tree clean, `main` level with `origin`
- Deployed, publicly reachable, auto-deploys on push
- CI refresh workflow verified green on Linux / Python 3.12, with a real data commit

### Headline findings (all computed, none typed in)

| Finding | Figure |
|---|---|
| Merchant payments: share of transactions vs share of value | **63.9% / 23.0%** |
| Merchant share of own transactions: most vs least (material states) | **Delhi 68.5% vs West Bengal 56.4%** |
| Rate travel over FY2023-FY2026 vs movement in the NIM gap | **250bps vs 2bps**: the gap survived a full cycle |
| Merchant contribution to all volume growth since 2018Q1 | **64%** |
| PhonePe / Google Pay share of national UPI volume | **45.9% / 32.3%**: both above the 30% cap |
| Transactions that must change app for the cap to bind | **4.3 bn a month** |
| Time for the leader to reach 30% at observed drift | **~470 months** |
| Private vs public bank NIM gap | **114 bps** (59 pricing + 56 funding) |
| Five-year price return, public vs private banks | **+284% vs +17%** |
| UPI transactions per banked adult per month | **14.9**, up from 4.0 in 2021 |
| Fund schemes vs distinct strategies | **14,288 → 3,353** (4.3× wrappers) |

## Active task

**Pass 4 is complete and deployed. Nothing is half-finished.** It did four things:

1. **A real India choropleth**, with the equal-area tile cartogram kept behind a toggle.
   Boundary source verified twice: current administrative geography, and India's own
   depiction. Both are build-time assertions, see the gotchas.
2. **Union territories made visible.** All 8 were always in the data; several render at
   under half a percent of the largest state and could not be found. Small territories
   now get labelled markers.
3. **A guided opening** (`Scrolly.astro`): the whole thesis in four sticky steps, with no
   Scrollama and no Motion. It reverses part of a documented decision, and the reasoning
   is recorded in `docs/stack-decisions.md`.
4. **Brand marks and a dash purge.** Real marks wherever one is freely licensed, and
   every em dash and clause-joining hyphen removed from prose. See rule 11.

**Not in the repo, and it must not be lost:** a survey pack was produced this session so
the synthetic NPS panel can be replaced with real fieldwork. It lives in the session
scratchpad, which is temporary. **Move it somewhere permanent before that directory is
cleaned.** See the memory snapshot for the exact path and contents.

## Next steps, in order

1. **Field the survey and de-synthesise sub-module D.** The pack exists (instrument,
   Apps Script form builder, response loader). Target 200 responses, minimum 120. The
   design makes the *paired episode contrast* the headline because it needs ~29
   respondents, against ~700 for the same claim framed as a cohort NPS difference.
   When the data lands, four `SYNTHETIC` labels must come off together: the module
   docstring, the `synthetic` flag in `chart_nps_episodes.json`, the on-page banner in
   `index.astro`, and the Gap Analyser note. Miss one and the site contradicts itself.
2. **Excel + PowerPoint deliverables.** The JD names both as hard requirements and the
   Gap Analyser still carries its only "Not covered" row for them. The pipeline emits
   tidy CSV, so `openpyxl` + `python-pptx` is roughly two hours.
3. **An asset-quality exhibit.** `npl_pct_gross_loans` is fetched (4.81% to 2.06%) and
   used in no chart. It is most of why the public-bank cohort re-rated +284%.
4. **Extend the per-app series**, currently 12 months (2023-12 to 2026-07). More months
   sharpen the HHI trend. Browser-transcribed; see `docs/REFRESH.md`.
5. **A second operator's state-level mix.** The single biggest weakness in the geographic
   module: the merchant-share ranking is PhonePe's. If Google Pay's mix inverted it, the
   finding would be about distribution rather than about India. Nothing open publishes it
   today. Say so rather than pretending otherwise.
6. **AMFI quarterly AAUM**, which would restate the wealth module in rupees rather than
   scheme counts, the version that informs a fee pool.
7. **Insurance**, the last JD-named sector with no coverage. IRDAI is PDF-only.
8. **Dead `vendor` script** in `site/package.json` points at `scripts/vendor-assets.mjs`,
   which does not exist. Still there. One-line deletion.

## Gotchas: things that actually bit us

- **A ratio of two shares can be a tautology.** `intensity_index = volume_share /
  value_share` looked like a merchant-behaviour measure. It is algebraically identical to
  `national_avg_ticket / state_avg_ticket` - verified to 4.4e-16 across all 36 states -
  so the exhibit plotted one variable on the y-axis and the *same* variable as colour.
  Worse, it inverted: it ranked Assam most merchant-intense because Assam has the
  smallest ticket, when Assam is among the most P2P-heavy states in the country. **Before
  trusting a derived index, correlate it against its own inputs.** The replacement is
  measured merchant share, which correlates -0.05 with ticket size.
- **`aria-hidden` does not satisfy WCAG 2.5.3.** The cartogram tiles show "DL" and "68%"
  with both spans `aria-hidden`, and Lighthouse still failed `label-content-name-mismatch`:
  a voice-control user says what they *see*, so the accessible name must contain the
  visible text. The name now starts with the code and the value, and the metric switch
  rewrites it whenever the displayed value changes.
- **`0` is falsy, so `.filter(x => x.value)` silently drops a real zero.** Cost a year of
  the inclusion series before anyone noticed. Use `!= null`.
- **A colon inside an unquoted YAML scalar silently breaks the content collection.**
  Rewriting a source label to `"PhonePe Pulse: category split"` turned the frontmatter list
  item into a mapping and failed the Astro build. `write_memo` now runs every source through
  `json.dumps`, so quoting and escaping are automatic.
- **A hidden browser tab does not run layout.** Not just IntersectionObserver: in a
  non-composited pane, even `element.style.width = '23%'` leaves `getComputedStyle().width`
  at its stale value, so any visual assertion measured there is meaningless. Verify layout
  against the deployed site with a real rendering browser instead of the preview pane.
- **"All states of India" means 36, and present is not the same as visible.** All 8
  union territories were in the boundary file from the first build, and the map still
  read as though they had been left out: Lakshadweep renders at 0.00% of Rajasthan's
  area, Chandigarh 0.02%, Delhi 0.41%. `build_india_map.py` flags anything under 2% of
  the largest state and the map draws a labelled marker for it. Check findability, not
  just row counts.
- **A 10px dot cannot carry a continuous colour ramp.** Sampled off the canvas, the
  small-territory markers all came back within one dark red of each other because a
  diverging scale puts mid-range values near the neutral stop. They now encode only
  which side of the national figure they fall on, which two hues can carry.
- **ECharts `visualMap` claims every series unless told otherwise.** It silently
  repainted the marker series and discarded its per-item colours. Bind it with
  `seriesIndex`.
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
- **Paytm is not a bank**. Its NIM is meaningless, so it is blanked rather than averaged
  in. The range guard caught this on the first run.
- **Never run two pipeline invocations at once**. They race on the same output files.
- **A failed `git pull --rebase` can silently revert the working tree.** It happened
  here: locked `.claude/data/*.sqlite-wal` files blocked the checkout, the rebase
  aborted mid-flight, and uncommitted work was lost. Commit before pulling; prefer
  `--no-rebase` while those files remain tracked.
- **Escaped quotes collapse inside Python heredocs.** Prefer `chr(10).join(...)` over
  `"\n".join(...)` when generating code that way.
- **`npx astro check` is very slow** here (minutes). Use `npx astro build` to validate.
- **IntersectionObserver never fires in a hidden tab**, so lazy ECharts appear "broken"
  when the browser pane is not composited. That is the environment, not the code.
