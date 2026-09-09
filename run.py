#!/usr/bin/env python
"""India FS Pulse task runner.

`make` is not available on the primary dev box (Windows), so this stdlib script
is the single entry point for both local runs and CI.

    python run.py data       # fetch -> clean -> transform
    python run.py analyze    # analysis scripts -> markdown + chart JSON
    python run.py site       # astro build
    python run.py check      # assert the invariants this repo publishes
    python run.py report     # the memos as one .docx deliverable
    python run.py all
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Explicit and ordered. Transform depends on every fetcher having landed.
FETCH = [
    "data-pipeline/fetch/fetch_pulse.py",
    "data-pipeline/fetch/fetch_pulse_state_mix.py",   # depends on fetch_pulse's output
    "data-pipeline/fetch/fetch_upi_history.py",
    "data-pipeline/fetch/fetch_upi_apps.py",
    "data-pipeline/fetch/fetch_bank_stocks.py",
    "data-pipeline/fetch/fetch_worldbank.py",
    "data-pipeline/fetch/fetch_fred_rates.py",
    "data-pipeline/fetch/fetch_amfi.py",
    "data-pipeline/fetch/fetch_pix_brazil.py",   # keyless BCB open data; caches its raw pull under data/raw
    "data-pipeline/fetch/fetch_psp_financials.py",
    "data-pipeline/fetch/fetch_rbi_cards.py",   # browser-transcribed seed, the priced control group
    "data-pipeline/fetch/fetch_upi_incentive.py",   # reads pulse_txn_national for the cross-check
]
TRANSFORM = ["data-pipeline/transform/build_kpis.py"]
ANALYZE = [
    "analysis/01_upi_landscape.py",
    "analysis/02_banking_health.py",
    "analysis/03_pe_diligence.py",
    "analysis/04_survey_nps.py",
    "analysis/05_geo_gap.py",
    "analysis/06_competitive_structure.py",
    "analysis/07_wealth_amfi.py",
    "analysis/08_rail_cost.py",
    "analysis/09_pix_comparator.py",
    "analysis/10_business_models.py",
    "analysis/11_value_pool.py",
    "analysis/13_cards_control.py",
    "analysis/12_answer.py",
    "docs/build_exhibit_csv.py",     # per-exhibit CSVs the site offers for download
    "docs/build_readme_charts.py",   # README exhibits + its generated regions
    "docs/build_docs.py",            # sources.md + data-dictionary.md from the ledger
]


def run_py(rel: str) -> None:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"missing script: {rel}")
    print(f"\n\033[1m>> {rel}\033[0m", flush=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {rel} (exit {r.returncode})")
    print(f"   ok  {time.time() - t0:.1f}s")


def run_cmd(args: list[str], cwd: Path) -> None:
    print(f"\n\033[1m>> {' '.join(args)}  (in {cwd.name}/)\033[0m", flush=True)
    # shell=True on Windows so npm/npx resolve through .cmd shims.
    r = subprocess.run(args, cwd=cwd, shell=(sys.platform == "win32"))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(args)} (exit {r.returncode})")


def task_data() -> None:
    for s in FETCH + TRANSFORM:
        run_py(s)


def task_analyze() -> None:
    for s in ANALYZE:
        run_py(s)


def task_check() -> None:
    run_py("docs/check_invariants.py")   # the properties this repo publishes about itself


def task_report() -> None:
    run_py("docs/build_report.py")   # the memos, assembled into one Word document


def task_site() -> None:
    run_py("site/scripts/make_og.py")   # social card, drawn from the computed data
    site = ROOT / "site"
    if not (site / "node_modules").exists():
        run_cmd(["npm", "install"], site)
    run_cmd(["npm", "run", "build"], site)


TASKS = {"data": task_data, "analyze": task_analyze, "site": task_site,
         "check": task_check, "report": task_report}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("task", choices=[*TASKS, "all"])
    task = p.parse_args().task
    todo = list(TASKS) if task == "all" else [task]
    t0 = time.time()
    for name in todo:
        TASKS[name]()
    print(f"\n\033[32mdone: {', '.join(todo)}  ({time.time() - t0:.1f}s)\033[0m")


if __name__ == "__main__":
    main()
