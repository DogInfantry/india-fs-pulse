# Stack decisions

What was chosen, what was rejected, and why. Rejections are recorded because
choosing a tool is only half of a sourcing decision.

## Chosen

| Layer | Choice | Why |
|---|---|---|
| Site | Astro 5, static output | Zero JavaScript by default; the whole site is 7 static pages. |
| Styling | Hand-written scoped CSS over one token file | Tailwind v4 was installed and wired through the Vite plugin, then never used: not one utility class, not one `@import "tailwindcss"`. Every component styles itself in a scoped `<style>` block against `tokens.css`. Two dependencies that emitted nothing, removed in pass 5. |
| Charts | ECharts, lazily imported | One dynamic import keeps a 1 MB library out of the critical path; the entry script is 1.6 kB. |
| Cohort chart | Hand-written SVG, server-rendered | Four points per series does not need a charting library, a canvas, or any JavaScript. |
| Workbench | ~40 lines of DOM code | Sorting and filtering 36 rows is a table, not a BI platform. |
| Pipeline | Python 3.14 + pandas | Already present; the largest dataset is 14,283 rows. |
| Host | Vercel, static | No backend needed. |
| Deployment config | `vercel.json`, not `vercel.ts` | `vercel.ts` is the current recommendation and gives typed, build-time config, but it needs `@vercel/config` installed at the repository root. The only npm package here lives in `site/`, so adopting it would mean a root `package.json` that exists purely to hold a type import. Revisit if the config ever needs real logic. |
| Analytics | None | Vercel Web Analytics and Speed Insights both inject a third-party script. The whole design is zero external requests, and the Lighthouse and privacy claims depend on that staying true. Traffic numbers are not worth the first third-party origin on the page. |

## The Content-Security-Policy, and what it does not cover

`script-src` is `'self'` with no `'unsafe-inline'`. That is only possible because the
one inline module script on the page, the guided opening, was lifted into
`site/src/scripts/scrolly.ts` and is now booted from the same entry that mounts the
charts. Astro inlines a component script whose bundled chunk has no imports, so moving
the file alone was not enough: it had to be called from a module that already has
imports. The eleven `<script type="application/json">` data islands are not classic or
module scripts, so `script-src` never applies to them.

`style-src` still carries `'unsafe-inline'`, and that is a real limitation rather than
an oversight. The built page has 74 inline `style` attributes: propbar widths, and
geometry computed inside the server-rendered SVG components. CSP hashes do not cover
style attributes at all, and `'unsafe-hashes'` would need one hash per distinct computed
value, which is unmaintainable by construction. Astro 6, released March 2026, generates
CSP hashes as part of the build and would close the script side automatically; it does
nothing for style attributes. The honest summary is that this policy blocks every
external origin outright, which is the whole attack surface on a site that loads nothing
third-party, and does not pretend to defend against injected inline styles.

## Rejected, and why

**Perspective, Superset, Panel, Redash, Vizro, glue.** All were evaluated as the
"client-ready dashboard" layer. Superset, Redash, Panel and Vizro need a live
Python or Node backend, which a static, free-hosted site cannot have. Perspective
runs client-side, but ships multiple megabytes of WASM: a real choice for a
million-row streaming grid, and the wrong one for 36 rows of state data against a
Lighthouse target of 95. The workbench was built in code instead.

**D3.** Specified early, then dropped once the exhibits were designed. The only
bespoke chart is a four-point cohort comparison, which is cleaner as
server-rendered SVG with no client JavaScript at all. Removing D3 took out a
dependency and a bundle.

**Motion and Scrollama.** Installed in the first pass for a scrollytelling hero,
then removed without being used.

> **Reversed in part, pass 4.** The page did want a guided opening after all: sixteen
> exhibits in a grid gave a cold reader no path in. `Scrolly.astro` now tells the whole
> thesis in four sticky steps. The dependencies stayed out. `position: sticky` is CSS,
> step activation is the same `IntersectionObserver` the chart loader already runs, and
> the bar is sized by custom properties the script writes. Zero bytes of library. The
> original objection was to scroll-hijacking the whole document, and that still stands:
> this is an opening that hands off to the exhibits, not a treatment applied to all
> sixteen.

The rest of the original note still applies: The page turned out to be exhibit-driven: fifteen
figures, each making one point, and scroll-driven sequencing fights that structure
rather than serving it. Carrying two dependencies for an effect the content does not
want is how bundles rot.

**WebGPU.** No dataset here is within three orders of magnitude of needing it.

**geohacker/india for the state map.** The obvious GeoJSON source, and unusable: it is a
pre-2014 GADM extract with no Telangana, no Ladakh, "Orissa" and "Uttaranchal". Telangana
is 10% of the volume in this project. A map that omits it is wrong, not merely dated.
`udit-001/india-maps-data` was used instead: 760 districts dissolved to exactly the 36
states the data carries, and its boundary reaches 37.08N / 80.33E, which is India's
official depiction including Aksai Chin. Both facts are asserted in
`site/scripts/build_india_map.py`, so a source that fails either breaks the build rather
than shipping a wrong map quietly.

**Full brand logos.** Only 7 of the 19 companies named here have a freely redistributable
mark, and the twelve missing include State Bank of India and every other public-sector
bank. Marks are used for the payment apps, where the three that matter cover 86% of
national volume; the banks stay on monograms, because marks on three of five private banks
and none of five public ones would imply something about the cohorts that is not true.

**RBI DBIE.** An Angular application with no documented public REST API. NIM is
derived from filed income statements instead, more defensible than scraping a
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
   open, and splits P2P from merchant, which the headline series does not.
2. **`make` became `run.py`.** `make` is not installed on Windows; a stdlib task
   runner works on both the dev box and CI.
3. **The workbench is hand-built rather than Perspective.** See above.
