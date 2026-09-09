# CLAUDE.md: India FS Pulse

Operating manual for this repo. Read before touching anything.

## Project

**India FS Pulse**: a code-driven Financial Services research portfolio:
reproducible Python pipeline → analysis → static Astro site → Vercel.

Independent research on a live, unresolved question: an industry point of view,
sector scans, survey analytics, a diligence simulation and interactive exhibits, all
computed from public data rather than asserted.

**Central question:** India built the world's largest real-time payments network.
Under zero-MDR it earns almost nothing directly. Who captures the value, and is there
an investable business model?

- Live: https://india-fs-pulse.vercel.app
- Repo: https://github.com/DogInfantry/india-fs-pulse
- **All links, evaluated tooling and data endpoints live in `docs/resources.md`.**

**Stack:** Python 3.14 + pandas (no polars) · Astro 5 static · hand-written scoped CSS
over one token file (no Tailwind, see decision 8) · ECharts lazily imported · hand-written
SVG components · Vercel · GitHub Actions monthly refresh.

## Commands

`make` is unavailable on Windows. Single entry point:

```bash
python run.py data      # 9 fetchers -> validate -> transform   (NO SECRETS REQUIRED, ~120s)
python run.py analyze   # 8 analysis modules + README exhibits + docs regeneration
python run.py site      # OG card + astro build
python run.py all
```

`docs/build_docs.py` is registered inside `analyze`, so `sources.md` and
`data-dictionary.md` cannot go stale behind a local run any more.

## Architecture: decisions and why

1. **PhonePe Pulse is the primary source, not NPCI's headline series.** Pulse is open,
   needs no auth, is current to 2026 Q2, and splits P2P from merchant, which *is* the
   monetisation question. The NPCI CKAN mirror everyone reaches for is frozen at 2023-08.
2. **Browser-only sources are transcribed, not scraped.** NPCI and PIB both return HTTP
   403 to every scripted request. Their tables live in `data-pipeline/data/manual/` with
   per-row `source_url` and `accessed`. This is honest sourcing, not a workaround to hide.
   PIB additionally publishes its figures as **chart images with printed data labels**,
   so those are read off the labels, never estimated from bar heights.
3. **Shares are computed against the national total**, never against the sum of the
   listed apps: NPCI caps its table at ten rows, so summing them would overstate every
   share. This yields a real "all other apps" residual and a genuine cross-source
   reconciliation (the ten cover 94 to 99% of national volume).
4. **The analysis layer never hardcodes a figure.** Memos are f-strings interpolating
   computed values, so prose cannot drift from data. Claims that depend on which way a
   number falls (pricing or funding, which cohort re-rated) are *conditionals in code*.
5. **No charting library for the bespoke exhibits.** Server-rendered SVG components carry
   the consulting vocabulary with zero client JS. ECharts is dynamically imported for the
   dashboard charts, keeping the entry script ~1.6 kB against a 1.0 MB lazy chunk.
6. **Colour is measured, not eyeballed.** `--signal` is for fills (3:1 suffices for
   non-text); `--signal-text` exists because small red text needs 4.5:1 on every surface
   token. Verified with Lighthouse.
7. **`script-src` is `'self'` with no `'unsafe-inline'`.** There is exactly one client
   entry point, `site/src/scripts/charts.ts`, which also boots the guided opening. Nothing
   inline executes. `style-src` still needs `'unsafe-inline'` for 74 computed style
   attributes, and `docs/stack-decisions.md` says so rather than implying otherwise.
8. **Tailwind was removed, not adopted.** It was installed and wired through the Vite
   plugin for four passes and never used: not one utility class, not one
   `@import "tailwindcss"`. Every component styles itself in a scoped `<style>` block
   against `site/src/styles/tokens.css`.

## File map

| Path | Role |
|---|---|
| `run.py` | Task runner. Registers every fetch / analysis script, **add new scripts here** |
| `vercel.json` | Build config plus CSP, HSTS, Referrer-Policy, Permissions-Policy and cache rules. NOT `vercel.ts`: that needs `@vercel/config` at the repo root, and the only npm package here is `site/` |
| `data-pipeline/common.py` | Paths, `get_json`/`get_text`, `expect*` guards, `write_processed`, `record_source`, `read_seeded_csv` |
| `data-pipeline/fetch/fetch_pulse.py` | **Primary.** National + state transactions, user/merchant base |
| `data-pipeline/fetch/fetch_pulse_state_mix.py` | P2P / merchant / utility split **within** each state. Reconciles the 36 state files against the country file |
| `data-pipeline/fetch/fetch_upi_history.py` | NPCI monthly: CKAN mirror + manual seed, joined |
| `data-pipeline/fetch/fetch_upi_apps.py` | NPCI per-app shares, HHI, national reconciliation |
| `data-pipeline/fetch/fetch_upi_incentive.py` | **The cost side.** Government incentive payout joined to the NATIONAL P2M/P2P value split. Both seeds are PIB, browser-only. Cross-checks its merchant share against Pulse. Runs last: it reads `pulse_txn_national` |
| `data-pipeline/fetch/fetch_bank_stocks.py` | yfinance fundamentals (NIM proxy) + 5y prices; retries flaky tickers |
| `data-pipeline/fetch/fetch_worldbank.py` · `fetch_amfi.py` | Inclusion denominators, NPLs, private credit · fund scheme universe |
| `data-pipeline/fetch/fetch_fred_rates.py` | India call money rate, monthly. **Keyless** CSV endpoint, so rule 5 holds |
| `data-pipeline/data/manual/*.csv` | Hand-seeded NPCI and PIB rows. **Header comments are `#`-leading lines only** |
| `data-pipeline/transform/build_kpis.py` | Processed → KPI layer + `site/src/data/*.json`. Also computes the counts the site footer renders |
| `analysis/_lib.py` | `load`, `load_json`, `write_json`, `write_memo`, `inr`, `pct` |
| `analysis/01..08_*.py` | Eight modules → `insights/*.md` + chart JSON |
| `site/src/pages/index.astro` | The whole scrollable report: 17 exhibits, 11 sections. Section letters and exhibit numbers are hand-maintained, so renumber in document order after inserting one |
| `site/src/scripts/charts.ts` | The only client entry. Memoised `loadECharts`, IntersectionObserver mount, and it boots `scrolly.ts` |
| `site/src/scripts/scrolly.ts` | The guided opening. Lives here so nothing is inline, which is what keeps `script-src 'self'` honest |
| `site/src/components/charts/` | `Marimekko`, `Waterfall`, `Slopegraph`, `SmallMultiples`, `SlopeLines`, `HexCartogram`, `IndiaChoropleth` |
| `site/src/components/` | `Figure` (action-title frame), `EChart`, `Workbench`, `GapMatrix` (coverage and limits, Harvey balls), `ExecSummary`, `Contact` (the About section), `Monogram`, `BrandMark`, `Scrolly` |
| `site/scripts/make_og.py` | Social card, drawn from computed data (Pillow, declared in requirements.txt) |
| `site/scripts/build_india_map.py` | **Run once, output committed.** Boundary file for the choropleth; asserts 36 states and India's official extent |
| `docs/build_docs.py` | Generates `sources.md` + `data-dictionary.md` from the provenance ledger |
| `docs/build_readme_charts.py` | Nine README SVGs plus two generated README regions. 1,200 lines of hand-rolled SVG, no tests. **Every chart JSON shape change flows through here** |
| `docs/resources.md` | **All external links, tooling verdicts, data endpoints** |
| `docs/stack-decisions.md` | What was rejected and why, including the CSP's limits |
| `docs/REFRESH.md` | How to refresh the browser-only NPCI and PIB tables |

## Non-negotiable rules

1. **Never fabricate a number.** Not fetched or computed → write `TODO` and leave it
   visible. Months NPCI does not publish are left as gaps, never interpolated.
2. **Every figure traces to `docs/sources.md`** with source URL and access date.
   That file is *generated* from the fetchers' provenance ledger, so it cannot drift.
3. **Synthetic data is labelled synthetic**: in the filename, on the chart, and in the
   memo. The NPS survey is the only synthetic dataset here, and it is excluded from the
   footer's "public sources" count because the repo generated it.
4. **Answer-first.** Chart titles state the conclusion, not the contents.
5. **The pipeline stays secret-free.** `python run.py data` must work with zero
   environment variables. Key-gated sources skip gracefully.
6. **No consulting firm's trademarks.** No firm's logos, colours or proprietary data.
   NPS as a *method* is public; NPS Prism data is not. The palette is original.
7. **Date-stamp every snapshot.** Any single-period figure carries its period.
8. **Never `pd.read_csv(comment="#")` on the seeded files.** Use `common.read_seeded_csv()`.
9. **Stale data is labelled stale**, and the chart shows the seam rather than hiding it.
10. **Fail loud on shape change.** Fetchers validate schema *and* plausible ranges.
11. **No dashes as punctuation.** No em dashes, and no ` - ` joining clauses. Use a comma,
    colon, semicolon or full stop. Hyphenated compounds are fine and expected: `zero-MDR`,
    `answer-first`, `Herfindahl-Hirschman`. This applies to memo generators too, since the
    memos are regenerated from them.
12. **Never divide across mismatched periods.** A full-year outlay over a ten-month base
    is not a rate. `fetch_upi_incentive.py` refuses, by design.

## Current state: all green

- `python run.py data`, ~120s, zero secrets, **9 fetchers, 18 processed datasets**
- `python run.py analyze`, **8 modules**, artefacts byte-identical across consecutive runs
- `python run.py site`, **10 pages** (index, methodology, 8 memos)
- Live headers verified on the production URL with `curl -I`: CSP, HSTS, nosniff,
  Referrer-Policy, Permissions-Policy, and `max-age=31536000, immutable` on `/_astro/*`
- ECharts 5.6.0 confirmed loading in a real browser **under the CSP**, zero console errors
- All commits authored `DogInfantry <ankleshrawat5@gmail.com>` except two genuine
  `github-actions[bot]` refresh commits. Working tree clean, `main` level with `origin`
- Deployed, publicly reachable, auto-deploys on push
- CI refresh workflow now also runs the Astro build before committing, and stages
  `docs/`, `README.md` and `og.png`, which it previously regenerated and discarded

### Headline findings (all computed, none typed in)

| Finding | Figure |
|---|---|
| Merchant payments: share of transactions vs share of value | **63.9% / 23.0%** |
| What zero MDR actually costs, blended over ALL national merchant value | **7.05bps in FY2023-24, paid by the state**, down from 8.68bps in FY2021-22 |
| FY2024-25 incentive outlay against the FY2023-24 payout | **Rs 1,500cr vs Rs 3,631cr**, a 58.7% cut while the base still grew |
| Implied floor on merchant value inside the Rs 2,000 eligibility band | **at least 47%** |
| Non-performing loans, peak to latest | **9.98% (2017) → 2.06% (2025)**: the public-bank re-rating is balance-sheet repair, not margin |
| Credit to the private sector, UPI launch to latest | **38.2% → 44.0% of GDP**: ten years of the rail moved penetration 5.8 points |
| Merchant share of own transactions: most vs least (material states) | **Delhi 68.5% vs West Bengal 56.4%** |
| Merchant contribution to all volume growth since 2018Q1 | **64%** |
| PhonePe / Google Pay share of national UPI volume | **45.9% / 32.3%**: both above the 30% cap |
| Transactions that must change app for the cap to bind | **4.3 bn a month** |
| Private vs public bank NIM gap | **114 bps** |
| Five-year price return, public vs private banks | **+284% vs +17%** |
| UPI transactions per banked adult per month | **14.9**, up from 4.0 in 2021 |
| Fund schemes vs distinct strategies | **14,288 → 3,353** (4.3× wrappers) |

## Active task

**Pass 5 is complete, pushed and verified live. Nothing is half-finished.** Three commits:
`460b159`, `57ad435`, `c0915a1`.

1. **The job-description framing is gone**, which was the point of the pass. It had shaped
   the site's whole spine: sections existed to tick sector boxes on a brief. The Gap
   Analyser, which was 13 transcribed JD bullets under a column header reading "What the
   job description asks for", is now an FS **coverage and limits map** that marks three
   areas not covered and says why for each.
2. **Three correctness bugs fixed**, all of which had been shipping wrong output:
   calendar-blind year-on-year, two exec-summary anchors landing a section late, and app
   trend charts plotting the December-2023 top six.
3. **Vercel hardened** and verified live end to end.
4. **Module 08 added**: the cost side of the rail, which the report had priced at zero.

**Nothing is in flight outside git.** The working tree is clean and pushed. The survey
pack referenced in the pass-4 handoff lived in a temporary scratchpad and is presumed
gone; if it matters, it has to be rebuilt.

## Next steps, in order

1. **Module 09: Brazil's Pix, the only comparable rail.** Endpoint verified live during
   pass 5, keyless JSON, current to 2026-08:
   `https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/EstatisticasTransacoesPix(Database=@Database)?@Database='YYYYMM'&$format=json`
   `PAG_PFPJ` and `REC_PFPJ` give payer and receiver type, so person-to-business is
   directly comparable to the merchant leg, and it is central-bank data for a whole
   country rather than one operator's book. `EstatisticasFraudesPix` publishes fraud
   statistics, which India does not publish in machine-readable form at all: that
   asymmetry is itself a finding. **Note:** `Database` is the publication vintage, not the
   reference month, so query the latest vintage and aggregate by `AnoMes`. This closes the
   coverage map's "comparison with other instant rails" row.
2. **Per-exhibit CSV downloads.** A `download` prop on `Figure.astro` pointing at a static
   `/data/<name>.csv`. The reproducibility claim is the project's strongest differentiator
   and it currently stops at the repository.
3. **Excel + PowerPoint deliverables.** `openpyxl` + `python-pptx`, roughly two hours.
4. **Extend the per-app series**, currently 12 irregular months (2023-12 to 2026-07).
   More months sharpen the HHI trend. Browser-transcribed; see `docs/REFRESH.md`.
5. **A second operator's state-level mix.** The biggest weakness in the geographic module:
   the merchant-share ranking is PhonePe's. Nothing open publishes an alternative today.
   Say so rather than pretending otherwise.
6. **AMFI quarterly AAUM**, which would restate the wealth module in rupees rather than
   scheme counts, the version that informs a fee pool.
7. **Insurance**, the last major FS sector with no coverage here. IRDAI is PDF-only.
8. **De-synthesise sub-module D.** Needs real fieldwork. When data lands, four
   `SYNTHETIC` labels come off together: the module docstring, the `synthetic` flag in
   `chart_nps_episodes.json`, the on-page banner in `index.astro`, and the coverage map
   note. Miss one and the site contradicts itself.
9. **Optional: `site/tsconfig.json`.** There is none, so the TypeScript in `.astro`
   frontmatter is stripped and never checked. Adding `astro/tsconfigs/strict` will surface
   a pile of pre-existing `as number` casts and untyped params. Its own session.

## Gotchas: things that actually bit us

### Numbers and method

- **`pct_change(12)` is positional, not calendar.** `upi_monthly` has five holes, so 34 of
  116 rows were compared against the wrong month: 2026-05 was reported year-on-year
  against 2025-03. Map each month to its calendar predecessor instead. Do **not** fix this
  by reindexing to a complete `PeriodIndex` and keeping the inserted rows: the CSV is a
  committed contract and phantom months break the chart that reads it.
- **A ratio of two shares can be a tautology.** `intensity_index = volume_share /
  value_share` is algebraically `national_ticket / state_ticket`, verified to 4.4e-16
  across all 36 states, so the exhibit plotted one variable against itself and inverted
  the ranking. **Before trusting a derived index, correlate it against its own inputs.**
- **A statutory rate and an effective rate are different numbers.** The UPI incentive pays
  0.15% on eligible transactions; blended over all merchant value the state pays ~0.07%.
  Publishing either as the other would be wrong. The implied eligible share is published
  as a **floor** because 20% of each claim is performance-conditional.
- **₹1 lakh crore = 1e12**, not 1e13.
- **`0` is falsy, so `.filter(x => x.value)` silently drops a real zero.** Use `!= null`.
- **`?? 0` on a missing observation invents data.** The slopegraph did this for apps with
  no first-month value. A slopegraph compares two endpoints on shared axes, so exclude
  series that do not span the window rather than fabricating an endpoint.

### Charts and time

- **An irregular series on a category axis lies about slope.** The per-app months thin
  from six-monthly to monthly, so even spacing drew two years at the width of seven
  months. Use a time axis in ECharts and elapsed-month positioning in SVG.
  `docs/build_readme_charts.py` already had the correct arithmetic; reuse it.
- **Selecting "the top N" from a frame sorted by (month, share) gives the FIRST month's
  top N**, not the current one. That kept a dead app rendering as an empty panel and
  omitted the two fastest-growing challengers.
- **A series that starts late or ends early breaks naive chart code.** `find()` with an
  `as number` cast yields `undefined`, then `cy="NaN"`. Guard the empty case, break the
  line at gaps instead of bridging, and put the end dot on the last real observation.

### Build and platform

- **Astro inlines a component script whose bundled chunk has no imports.** Moving the code
  into its own file is not enough to get it out of the HTML; it has to be *called from* a
  module that already has imports. This is the whole reason `script-src 'self'` is
  achievable without hashes or an Astro 6 upgrade.
- **CSP hashes do not cover style *attributes*.** The page carries 74 computed
  `style="..."` attributes, so `style-src` needs `'unsafe-inline'`. `'unsafe-hashes'`
  would need one hash per distinct computed value. Say so rather than implying strictness.
- **A hidden browser tab does not run layout**, and IntersectionObserver never fires, so
  lazy ECharts appear broken in a non-composited pane. Verify against the deployed site.
  Screenshots can also time out when the window is minimised; use `get_page_text`, `find`
  or `javascript_tool` instead.
- **`npx astro check` is very slow** here (minutes). Use `npx astro build` to validate.
- **The CI workflow regenerates more than it used to stage.** `run.py analyze` rewrites
  `docs/assets/*.svg` and two regions inside `README.md`. Staging only `sources.md` left
  the repo's front door drifting from its own data.

### Sources

- **`#` is data, not a comment.** NPCI marks third-party providers with a trailing `#`
  ("Phone Pe #"). `pd.read_csv(comment='#')` silently truncated every row to `NaN`.
- **PIB and NPCI both serve HTTP 403 to scripts**, and PIB publishes key figures as
  **chart images**. Read the printed data labels, never the bar heights.
- **CKAN's date column is `YYYY-DD-MM`**, not ISO. `2023-01-08` is 1 August 2023.
- **NPCI's URL moved** to `/product/upi/...`; `/what-we-do/upi/...` 404s.
- **yfinance throws `KeyError` intermittently** on healthy tickers, silently dropping a
  bank from a cohort mean. Retried three times, plus a per-cohort minimum of 3 banks.
- **Paytm is not a bank**. Its NIM is meaningless, so it is blanked rather than averaged in.
- **Fund houses have brackets too.** `IL&FS Mutual Fund (IDF)` was parsed as a category
  header, misattributing 2,535 AMFI rows.
- **A colon inside an unquoted YAML scalar silently breaks the content collection.**
  `write_memo` runs every source through `json.dumps`, so quoting is automatic. Any new
  memo title containing a colon depends on that.

### Working in this repo

- **Never run two pipeline invocations at once**. They race on the same output files.
- **A failed `git pull --rebase` can silently revert the working tree.** Locked
  `.claude/data/*.sqlite-wal` files blocked a checkout, the rebase aborted mid-flight, and
  uncommitted work was lost. Commit before pulling; prefer `--no-rebase`.
- **Escaped quotes and Windows paths break bash heredocs.** For long files use the Write
  tool; for path literals inside a Python heredoc, use a regex rather than typing `C:\...`.
- **The site footer's counts are computed in `build_kpis.py`, which runs in
  `run.py data`, not `analyze`.** Adding a fetcher or module and only running `analyze`
  leaves the footer understating the pipeline.
