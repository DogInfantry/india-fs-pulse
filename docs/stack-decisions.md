# Stack decisions

What was chosen, what was rejected, and why. Rejections are recorded because
choosing a tool is only half of a sourcing decision.

## Chosen

| Layer | Choice | Why |
|---|---|---|
| Site | Astro 5, static output | Zero JavaScript by default; the whole site is 7 static pages. |
| Styling | Tailwind v4 via the Vite plugin | The `@astrojs/tailwind` integration is deprecated for v4. |
| Charts | ECharts, lazily imported | One dynamic import keeps a 1 MB library out of the critical path; the entry script is 2.6 kB. |
| Cohort chart | Hand-written SVG, server-rendered | Four points per series does not need a charting library, a canvas, or any JavaScript. |
| Workbench | ~40 lines of DOM code | Sorting and filtering 36 rows is a table, not a BI platform. |
| Pipeline | Python 3.14 + pandas | Already present; the largest dataset is 14,283 rows. |
| Host | Vercel, static | No backend needed. |

## Rejected, and why

**Perspective, Superset, Panel, Redash, Vizro, glue.** All were evaluated as the
"client-ready dashboard" layer. Superset, Redash, Panel and Vizro need a live
Python or Node backend, which a static, free-hosted site cannot have. Perspective
runs client-side, but ships multiple megabytes of WASM — a real choice for a
million-row streaming grid, and the wrong one for 36 rows of state data against a
Lighthouse target of 95. The workbench was built in code instead.

**D3.** Specified early, then dropped once the exhibits were designed. The only
bespoke chart is a four-point cohort comparison, which is cleaner as
server-rendered SVG with no client JavaScript at all. Removing D3 took out a
dependency and a bundle.

**Motion and Scrollama.** Installed in the first pass for a scrollytelling hero,
then removed without being used. The page turned out to be exhibit-driven - fifteen
figures, each making one point - and scroll-driven sequencing fights that structure
rather than serving it. Carrying two dependencies for an effect the content does not
want is how bundles rot.

**WebGPU.** No dataset here is within three orders of magnitude of needing it.

**RBI DBIE.** An Angular application with no documented public REST API. NIM is
derived from filed income statements instead — more defensible than scraping a
portal, and it produces a number this project computed rather than quoted.

**data.gov.in.** The public sandbox key authenticates and `/lists` returns 285,833
resources, but filtered queries time out, and many finance resources have no active
API behind them. It would have added nothing the spine does not already cover.

**Quarto.** Planned for the analysis notebooks, then dropped: it is not installed on
the dev box, and Astro content collections already render the generated Markdown.
One fewer toolchain.

**Google Fonts.** The type stack is system-resident, so the site renders offline and
makes zero third-party requests.

## Deviations from the original plan, and why

1. **PhonePe Pulse replaced the NPCI CKAN CSV as the primary source.** The CSV was
   described as verified; it is live but ends 2023-08. Pulse is current to 2026Q2,
   open, and splits P2P from merchant — which the headline series does not.
2. **`make` became `run.py`.** `make` is not installed on Windows; a stdlib task
   runner works on both the dev box and CI.
3. **The workbench is hand-built rather than Perspective.** See above.
