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
python run.py data      # 11 fetchers -> validate -> transform  (NO SECRETS REQUIRED)
python run.py analyze   # 10 analysis modules + exhibit CSVs + README exhibits + docs
python run.py site      # OG card + astro build
python run.py check     # assert the properties this repo publishes about itself
python run.py report    # the memos as one .docx under deliverables/ (gitignored)
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
| `data-pipeline/fetch/fetch_psp_financials.py` | **The thesis test.** Filed accounts for four listed FS businesses grouped by what each sells. A panel of named companies, never cohort averages |
| `data-pipeline/fetch/fetch_pix_brazil.py` | **The comparator.** Brazil's Pix from the central bank's Olinda API, keyless. Caches its ~190 MB pull under `data/raw`, keyed on the calendar month |
| `data-pipeline/fetch/fetch_worldbank.py` · `fetch_amfi.py` | Inclusion denominators, NPLs, private credit · fund scheme universe |
| `data-pipeline/fetch/fetch_fred_rates.py` | India call money rate, monthly. **Keyless** CSV endpoint, so rule 5 holds |
| `data-pipeline/data/manual/*.csv` | Hand-seeded NPCI and PIB rows. **Header comments are `#`-leading lines only** |
| `data-pipeline/transform/build_kpis.py` | Processed → KPI layer + `site/src/data/*.json`. Also computes the counts the site footer renders |
| `analysis/_lib.py` | `load`, `load_json`, `write_json`, `write_memo`, `inr`, `pct` |
| `analysis/01..12_*.py` | Twelve modules → `insights/*.md` + chart JSON |
| `site/src/pages/index.astro` | The whole scrollable report: 25 exhibits, 14 sections. Every exhibit carries a CSV download. Section letters and exhibit numbers are hand-maintained, so renumber in document order after inserting one |
| `site/src/scripts/charts.ts` | The only client entry. Memoised `loadECharts`, IntersectionObserver mount, and it boots `scrolly.ts` |
| `site/src/scripts/scrolly.ts` | The guided opening. Lives here so nothing is inline, which is what keeps `script-src 'self'` honest |
| `site/src/components/charts/` | `Marimekko`, `Waterfall`, `Slopegraph`, `SmallMultiples`, `SlopeLines`, `HexCartogram`, `IndiaChoropleth`, `ValuePool` (money, hypothetical against actual), `RangeBar` (an estimate as a band) |
| `site/src/components/` | `Answer` (governing thought and three pillars, above the fold, fed by `answer.json` so the page and the .docx cannot differ), `Figure` (action-title frame), `EChart`, `Workbench`, `GapMatrix` (coverage and limits, Harvey balls), `ExecSummary`, `Contact` (the About section), `Monogram`, `BrandMark`, `Scrolly` |
| `site/scripts/make_og.py` | Social card, drawn from computed data (Pillow, declared in requirements.txt) |
| `site/scripts/build_india_map.py` | **Run once, output committed.** Boundary file for the choropleth; asserts 36 states and India's official extent |
| `analysis/12_answer.py` | **Runs last.** Assembles the governing thought and three pillars into `answer.json` from figures other modules already computed. Introduces no new measurement, so it cannot outrun the evidence |
| `docs/check_invariants.py` | **The one runnable check.** Rule 11 across every generated memo, every download link resolving, footer counts against the tree, no orphan memo card, provenance completeness, and that nulls survive rather than being zero-filled. Plain asserts, no framework. Runs in CI before anything is committed |
| `docs/build_exhibit_csv.py` | Per-exhibit CSVs into `site/public/data/`, from the chart JSON each exhibit reads. Handles three JSON shapes and **exits non-zero on an unrecognised one**, so an exhibit cannot ship a download link to nothing |
| `docs/build_report.py` | The memos assembled into `deliverables/india-fs-pulse.docx`. Run with `python run.py report`; output is gitignored |
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

- `python run.py data`, zero secrets, **11 fetchers, 23 processed datasets**. Currently
  **blocked at `fetch_pulse.py`** by an upstream removal; see next steps item 1. The other
  nine fetchers and the transform run clean. The first Pix pull adds about 65s and roughly
  190 MB, then caches under `data/raw` for the calendar month
- `python run.py analyze`, **12 modules**, artefacts byte-identical across consecutive runs
- `python run.py site`, **13 pages** (index, methodology, 11 memos)
- `python run.py report`, the memos as one `.docx` under `deliverables/` (gitignored),
  opening on the answer from `answer.json`
- `python run.py check`, **11 invariants**, all green. Runs in CI before anything commits
- 25 exhibits, every one carrying a CSV download; 9 hand-written SVG chart components
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
| Brazil Pix merchant leg: share of transactions vs share of value | **46.6% / 11.8%**, the same shape as India's 63.9% / 23.0% |
| Brazil's merchant leg since the rail launched | **5.2% (2020-11) → 46.6% (2026-08)** |
| Everything Brazil layered on top of the free rail, six years in | **0.26% of merchant transactions**; dynamic QR is 84.1% and earns nothing |
| Priced at the 30bps NPCI itself permits, the merchant leg would be worth | **Rs 15,450cr a year, 1.9x One97 (Paytm)'s entire revenue**; the state replaces it with Rs 3,631cr |
| Cost of holding the subsidy rate steady, against what was appropriated | **Rs 2,681cr to Rs 3,517cr more**, a range because the published base covers ten months |
| Instant payments per banked adult per month, Brazil vs India | **49 vs 24**, same denominator, latest month both publish |

## Active task

**Pass 8 (2026-09-09/10) did three things. Nothing is half-finished.** Five commits:
`310eba9`, `ba9d115`, `363f993`, `0056cef`, and `27ac500` from the tail of pass 7.

1. **Four joints in the argument were reconciled**, found by a director-level review of
   the *argument* rather than the data. The worst: `execAnswer` said the rails "priced the
   busy half at zero" while section B's callout said "the merchant leg is **not** unpriced,
   it is priced at 7.0bps", and **no exec finding anchored to the cost module at all**.
   Both were true of DIFFERENT PARTIES (the app earns zero; the acquiring bank receives the
   incentive) and the page never said which. Also fixed: a cross-check that was announced
   and never printed, a causal mechanism ("the mechanism is deposit mix") asserted while
   `casa` is computed nowhere, and one datum rendering at two precisions.
2. **Module 11 states the prize in rupees**, which the report had never once done. At the
   30bps NPCI itself permits, the merchant leg would be worth **Rs 15,450cr a year, 1.9x
   One97 (Paytm)'s entire revenue**. Two new SVG primitives: `ValuePool` (hypothetical
   money hollow and dashed, actual money solid) and `RangeBar` (a point inside a band).
3. **Module 12 gives the report an answer before the evidence**: one governing thought and
   three pillars, written once to `answer.json` and read by BOTH the page and the `.docx`,
   which now opens on the answer rather than a contents list.

**A correction worth carrying.** A review agent reported that a hand-typed `7%` falsified
the "no figure typed by hand" claim. It did not: `analysis/03` computes it and rendered at
0dp while module 10 rendered at 1dp. Verify an agent's finding before acting on it; this
one was wrong and was repeated once before checking.

**Pass 6 added module 09, Brazil's Pix, the comparator.** The report asserted that the
investable business is distribution rather than transactions and had nothing outside India
to test it against. It does now, and the coverage map's "comparison with other instant
rails" row has moved from not covered to partial.

What it found: Brazil's merchant leg is **46.6% of Pix transactions and 11.8% of the
value**, against India's 63.9% and 23.0%. The same shape, under a regulator that never had
a discount rate to remove, which turns the report's central claim from an interpretation of
India into an observation about zero-cost instant rails. Brazil is also further along the
curve, at **2.0x India's transactions per banked adult**, so this is not a maturity gap
India grows out of. What Brazil built on top of the free rail (recurring debits,
open-finance initiation, contactless) is **0.26% of merchant transactions**: real,
compounding fast, and still an option rather than a business.

**One correction carried into the code.** The pass-5 note that Olinda's `Database`
parameter is the publication vintage was wrong, and following it would have returned one
month instead of seventy. See the gotchas below.

**Pass 7 added module 10, the thesis against filed accounts, plus two deliverables.**
Four listed companies test the report's own recommendation and agree with it: the
transaction business earns **6.8%** net margin, distribution **9.9%** and **21.2%**, and
the depository that IS allowed to charge a toll **39.8%**. Also shipped: a CSV download on
every exhibit, marks for State Bank and Union Bank, and `python run.py report`.

**Pass 5 remains as described.** Three commits: `460b159`, `57ad435`, `c0915a1`.

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

1. **URGENT, and it blocks `python run.py data`: PhonePe Pulse has removed `amount`
   from the national category-split endpoint.** `aggregated/transaction/country/india/*`
   now returns `paymentInstruments[]{count, type}` with **no `amount`**, and it is gone
   across the whole history, 2018Q1 to 2026Q2, not only recent quarters. Verified
   2026-09-09. `fetch_pulse.py` dies on `KeyError: 'amount'`, so the pipeline stops at
   fetcher one and the CI monthly refresh will fail.
   - The **state** endpoint `map/transaction/hover/...` still carries `amount`, so
     state-level value survives and `pulse_txn_state` is unaffected.
   - What breaks if it is patched carelessly: every value share on the page, including
     the headline merchant **23.0% of value**, average ticket, GMV per merchant and the
     MDR scenarios. The committed CSVs still hold the last good pull (2026-08-21), so
     the site is correct as of then and only a refresh is blocked.
   - This needs a decision, not a quick fix. The house convention already exists in
     `upi_monthly`: keep the last known good values, mark them with a `provenance`
     column and show the seam (rules 9 and 1). The alternative is to drop the value side
     of the category split and restate the module on volume only. Do not silently
     `.get("amount", 0)`: that would fabricate zero value for every category.
2. **Cards against UPI, India's own control group.** The strongest unbuilt exhibit:
   India charges an MDR on cards and zero on UPI, same market, same merchants, same
   regulator. RBI publishes monthly bank-wise POS and card statistics and the direct
   file URLs are known, but **the documents are browser-only**, verified 2026-09-09:
   the listing page answers a script while the XLSX links return an interstitial or
   fail. It is a manual transcription job like the NPCI seeds, so it needs a human at a
   browser. Full evidence and the URL shape are in `docs/resources.md`; do not re-probe
   the endpoint.
3. ~~Per-exhibit CSV downloads.~~ **Done.** `Figure.astro` takes a `download` prop and all
   23 exhibits carry one. `docs/build_exhibit_csv.py` generates the files from the same
   chart JSON the exhibit reads, so a CSV cannot disagree with the chart above it.
4. **Excel and PowerPoint deliverables.** The Word half is done: `python run.py report` builds `deliverables/india-fs-pulse.docx` from the generated memos. `openpyxl` and `python-pptx` would extend the same pattern.
5. **Extend the per-app series**, currently 12 irregular months (2023-12 to 2026-07).
   More months sharpen the HHI trend. Browser-transcribed; see `docs/REFRESH.md`.
6. **A second operator's state-level mix.** The biggest weakness in the geographic module:
   the merchant-share ranking is PhonePe's. Nothing open publishes an alternative today.
   Say so rather than pretending otherwise.
7. **AMFI quarterly AAUM**, which would restate the wealth module in rupees rather than
   scheme counts, the version that informs a fee pool. **AMFI publishes it as a JPEG**,
   verified 2026-09-09, and the documented AUM paths now 404. So it is a manual seed like
   the PIB tables, read off printed labels, not a fetcher. See `docs/resources.md`.
8. **Insurance**, the last major FS sector with no coverage here. IRDAI is PDF-only.
9. **De-synthesise sub-module D.** Needs real fieldwork. When data lands, four
   `SYNTHETIC` labels come off together: the module docstring, the `synthetic` flag in
   `chart_nps_episodes.json`, the on-page banner in `index.astro`, and the coverage map
   note. Miss one and the site contradicts itself.
10. **Optional: `site/tsconfig.json`.** There is none, so the TypeScript in `.astro`
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
  the repo's front door drifting from its own data. **It happened twice:** adding
  `docs/build_exhibit_csv.py` made `analyze` also rewrite `site/public/data/*.csv`, which
  the workflow did not stage, so a refresh would have served downloads that disagreed
  with the charts above them. `run.py check` now runs in CI specifically to catch this
  class of drift. **Add a generator, add its output to the `git add` line.**

### Sources

- **PhonePe Pulse dropped `amount` from the national category-split endpoint**, across the
  whole history, verified 2026-09-09. The state endpoint still has it. This is the repo's
  primary source and it blocks `python run.py data`. See next steps item 1 before touching
  `fetch_pulse.py`.
- **Olinda's `Database` parameter is the EARLIEST reference month, not the publication
  vintage**, and every response runs cumulatively forward to the latest published month.
  Asking for `'202608'` returns one month, `'202011'` returns all seventy and about 190 MB.
  An earlier note in this file said the opposite, and following it would have shipped a
  one-month series presented as a trend.
- **Olinda ignores `$select`, `$count`, `$apply` and `$orderby`.** Only `$top` and
  `$format` are honoured, so there is no server-side aggregation and no cheap way to ask
  how many rows exist. `$top` without `$orderby` returns arbitrary rows, so it cannot be
  used to find the latest month either.
- **Some Olinda months return a truncated body that does not parse.** `'202101'` and
  `'202401'` both returned an identical 15,613-byte fragment. Reproducible, not transient,
  which is why `fetch_pix_brazil.py` guards on a row-count floor rather than retrying.
- **`groupby` silently drops rows whose key is null**, which shrinks a numerator while
  leaving its denominator whole. Pix leaves `FORMAINICIACAO` null on 1,952 early rows and
  the share-sum guard is what caught it. Bucket nulls explicitly; never let them vanish.
- **Guard the unrounded value, not the rounded one.** Rounding ten shares to six places and
  then asserting they sum to 1 measures the rounding, not the data, and fails at about
  2e-6.

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

- **An agent's finding is a hypothesis, not a fact.** A review agent reported a hand-typed
  `7%` that would have falsified the repo's central integrity claim. It was computed, at a
  different precision. Verify before acting, and before repeating it to the user.
- **A renumber loop that guards on `count == 1` skips silently.** Inserting a section whose
  exhibits duplicate existing numbers made the guard skip both, leaving two 6s, two 7s and
  no 8 or 9. Renumber the OLD items before inserting the new ones, or target by position.
- **`/impeccable` is a Claude Code slash command, not a shell command.** Presenting it in a
  ```bash fence gives it a Run button in the desktop app, which sends it to PowerShell where
  it fails. Persist design-hook ignores through the plugin's own
  `skills/impeccable/scripts/hook-admin.mjs` instead of hand-writing the config.
- **The design hook's `border-accent-on-rounded` misfires here.** It does not read WHICH
  corners are rounded. `ExecSummary` and `Answer` both zero the radius on the accent edge,
  which is the remedy the rule asks for. Scoped off for `Answer.astro` in
  `.impeccable/config.json` with the reason attached.

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
