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
