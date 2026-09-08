# Refreshing the data

`python run.py data` refreshes everything that can be refreshed automatically. It
needs **no credentials** and takes about 90 seconds.

## Automatic (all of it, no secrets)

| Source | Cadence | Notes |
|---|---|---|
| PhonePe Pulse | quarterly | New quarter appears as `data/aggregated/.../{year}/{q}.json` in the upstream repo. The fetcher walks years and quarters and treats a 404 as "not published yet". |
| yfinance | daily / on results | Prices daily, fundamentals when a company files. |
| World Bank | irregular | Account-ownership indicators update every few years (Findex). |
| AMFI | daily | `NAVAll.txt` is regenerated every business day. |
| NPCI CKAN mirror | **never** | Frozen at 2023-08. History only. |

## Manual: the NPCI recent months

`npci.org.in` returns **HTTP 403** to every scripted request, including WebFetch.
A real browser session reaches it. To add newly published months:

1. Open <https://www.npci.org.in/product/upi/product-statistics> in a browser.
   Note: the older `/what-we-do/upi/product-statistics` path is dead.
2. Select the **Monthly Statistics** tab, then the financial year from the year picker.
3. Read off `Month`, `Volume (In Mn.)` and `Value (In Cr.)`.
4. Append rows to `data-pipeline/data/manual/npci_upi_monthly.csv`, keeping the
   `source_url` and `accessed` columns populated.
5. Re-run `python run.py data`.

### Two things to know before you edit that file

- **The table renders only the newest 10 months per financial year, with no
  pagination.** That is why 2024-04, 2024-05, 2025-04 and 2025-05 are missing. Leave
  them missing. Do not interpolate them (CLAUDE.md rule 1).
- **Exclude the current, incomplete month.** The newest row is month-to-date and will
  understate the month badly.

### Sanity check after any edit

The overlap month must still agree with the open mirror:

```bash
python -c "import pandas as pd; d=pd.read_csv('data-pipeline/data/processed/upi_monthly.csv'); print(d[d.month.between('2023-07','2023-10')].to_string(index=False))"
```

August 2023 should read 10,586.02 Mn / 15,76,536 Cr on both sides of the seam. If it
does not, the transcription is wrong or NPCI has restated the series.

## Manual: the per-application market shares

Same WAF problem, different table. To add newly published months:

1. Open <https://www.npci.org.in/product/ecosystem-statistics/upi> in a browser.
2. Select the **UPI Applications** tab.
3. Set the month and year with the two dropdowns above the table.
4. Read off `Application Name`, `Total Volume (In Mn.)` and `Total Value (Cr)`.
5. Append to `data-pipeline/data/manual/npci_upi_apps.csv`, transcribing the app
   name **verbatim**. Normalisation happens in `fetch_upi_apps.py`, so the raw
   record stays checkable.
6. Re-run `python run.py data`.

### Three traps in that table

- **Only ten rows render, with no pagination.** This is the top ten by volume, not
  the whole field. Shares are therefore computed against the NPCI *national* total,
  never against the sum of these rows.
- **Before roughly 2024 the ten rows are alphabetical, not ranked**, so PhonePe is
  not even present in December 2022. Those months are unusable; the series starts
  2023-12 for that reason.
- **The `#` in an app name is NPCI's third-party-provider marker, not a comment.**
  Parsing the seed file with pandas' `comment='#'` silently truncates every row.

## PIB: the incentive payout and the national P2M split

Two seeds, one release, and the only open national merchant/P2P value split this
project has found. `pib.gov.in` returns HTTP 403 to every scripted request, exactly
like `npci.org.in`, so both are transcribed from a browser session.

1. Open `https://www.pib.gov.in/PressReleasePage.aspx?PRID=2114335` in a real browser.
2. The two figures are published as **chart images, not text**. Open each image in its
   own tab to read the printed data labels. Read the labels, never the bar heights.
   - Year-wise government incentive payout, Rs crore, into
     `data-pipeline/data/manual/govt_upi_incentive.csv`
   - UPI transaction value split into P2M and P2P, Rs lakh crore, into
     `data-pipeline/data/manual/npci_upi_value_split.csv`
3. Record `months` honestly. A row labelled "Till Jan'25" covers ten months, not
   twelve, and the fetcher refuses to compute a rate against a part-year base.
4. Every row needs its own `source_url` and `accessed`. The fetcher fails without them.
5. Run `python data-pipeline/fetch/fetch_upi_incentive.py`. It reconciles P2M plus P2P
   against the published total to 0.15 lakh crore, and cross-checks the national
   merchant share of value against PhonePe Pulse's own. A wide divergence means one of
   the two is being read wrong.

**Trap.** The statutory rate is 0.15% and the blended rate is about 0.07%. They are
different quantities and the exhibit says so. Do not seed one as the other.

**When a newer release appears**, add rows rather than replacing them. The FY2024-25
row is a budgeted outlay; when its actual payout is published, change `status` to
`actual` and correct `payout_cr`, so the series keeps saying which is which.
