"""Sub-module D: NPS-style episode analytics on a SYNTHETIC survey.

*** THE SURVEY DATA IN THIS MODULE IS SYNTHETIC. IT IS NOT A REAL SURVEY. ***

Why synthetic: real episode-level loyalty benchmarks for Indian retail banking
are proprietary. Rather than cite numbers this project cannot source, it
GENERATES a documented, seeded, reproducible dataset and applies the public NPS
method to it. The method is the artefact; the numbers are illustrative.

NPS = %promoters (9-10) - %detractors (0-6), scored per customer episode.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import PROCESSED, banner, write_json, write_memo  # noqa: E402

SEED = 20260820          # fixed: `python run.py analyze` must be reproducible
N = 2000
COHORTS = {"Neobank / payments app": 0.34, "Private bank": 0.42, "Public bank": 0.24}
AGE_BANDS = {"18-29": 0.34, "30-44": 0.38, "45-59": 0.19, "60+": 0.09}
EPISODES = ["Open an account", "Make a payment", "Get support", "Apply for credit"]

# Latent mean rating per (cohort, episode) on a 0-10 scale. These encode the
# hypothesis the module tests: digital-first players win effortless, automated
# episodes and lose episodes that need a human.
LATENT = {
    "Neobank / payments app": {"Open an account": 8.7, "Make a payment": 9.0,
                               "Get support": 6.1, "Apply for credit": 7.6},
    "Private bank":           {"Open an account": 7.6, "Make a payment": 8.1,
                               "Get support": 7.4, "Apply for credit": 7.5},
    "Public bank":            {"Open an account": 6.4, "Make a payment": 7.2,
                               "Get support": 6.6, "Apply for credit": 6.3},
}


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    cohort = rng.choice(list(COHORTS), N, p=list(COHORTS.values()))
    age = rng.choice(list(AGE_BANDS), N, p=list(AGE_BANDS.values()))
    # Older respondents rate digital-first providers a little lower.
    age_shift = {"18-29": 0.3, "30-44": 0.1, "45-59": -0.2, "60+": -0.5}
    rows = []
    for i in range(N):
        for episode in EPISODES:
            mu = LATENT[cohort[i]][episode]
            if cohort[i] == "Neobank / payments app":
                mu += age_shift[age[i]]
            score = int(np.clip(round(rng.normal(mu, 1.9)), 0, 10))
            rows.append({"respondent_id": f"R{i:04d}", "cohort": cohort[i],
                         "age_band": age[i], "episode": episode, "score": score})
    return pd.DataFrame(rows)


def nps(scores: pd.Series) -> float:
    promoters = (scores >= 9).mean()
    detractors = (scores <= 6).mean()
    return round(100 * (promoters - detractors), 1)


def main() -> None:
    banner("Sub-module D: NPS episode analytics (SYNTHETIC data)")
    df = generate()
    df.to_csv(PROCESSED / "survey_SYNTHETIC_nps.csv", index=False)
    print(f"   generated {len(df):,} SYNTHETIC ratings ({N:,} respondents x {len(EPISODES)} episodes)")

    by_episode = df.groupby(["cohort", "episode"])["score"].apply(nps).unstack()
    overall = df.groupby("cohort")["score"].apply(nps)

    write_json("chart_nps_episodes", {
        "synthetic": True,
        "label": "SYNTHETIC DATA - illustrates the method, not the market",
        "seed": SEED, "respondents": N,
        "episodes": EPISODES,
        "series": [{"cohort": c, "overall": float(overall[c]),
                    "values": [float(by_episode.loc[c, e]) for e in EPISODES]}
                   for c in by_episode.index],
    })

    neo = "Neobank / payments app"
    best = by_episode.loc[neo].idxmax()
    worst = by_episode.loc[neo].idxmin()
    spread = by_episode.loc[neo, best] - by_episode.loc[neo, worst]
    rival_worst = by_episode["Get support"].idxmax()

    body = f"""
> **This module runs on synthetic data.** {N:,} respondents were generated from a
> documented, seeded model (`analysis/04_survey_nps.py`, seed `{SEED}`) because
> episode-level loyalty benchmarks for Indian banking are proprietary. The
> **method** is the deliverable. The numbers illustrate it and must not be quoted
> as market fact.

## The answer

Measured at the level of the customer **episode** rather than the brand,
digital-first providers do not have a loyalty advantage - they have an
*episode-shaped* one. On this synthetic panel the neobank cohort scores
**{by_episode.loc[neo, best]:+.0f} NPS on "{best}"** and
**{by_episode.loc[neo, worst]:+.0f} on "{worst}"** - a {spread:.0f}-point spread inside
a single brand. A blended brand-level NPS ({overall[neo]:+.0f}) hides that entirely.

## Three supporting arguments

**1. The brand-level number is an average of opposites.** Neobank overall NPS is
{overall[neo]:+.0f}, against {overall['Private bank']:+.0f} for private banks and
{overall['Public bank']:+.0f} for public banks. Ranking on that single figure would
misdirect investment, because the underlying episodes disagree with each other.

**2. Automated episodes and human episodes separate cleanly.** Digital-first wins
the episodes a machine completes end to end ("{best}"). It loses the episode that
requires a person ("{worst}"), where **{rival_worst}** leads. Loyalty here is not
about brand affinity; it is about whether the episode had to escalate.

**3. The gap is where the churn risk lives.** An episode scoring
{by_episode.loc[neo, worst]:+.0f} is a detractor-generating machine, and it sits inside
the same relationship that Sub-module A identified as the monetisation route.
Cross-sell attempted on the back of a failed support episode converts poorly.

## So what

- **Measure and manage at episode level, not brand level.** Episode NPS is
  actionable; brand NPS is a scoreboard.
- **Fix the escalation path before monetising the relationship.** The credit and
  distribution pathways in Sub-module A depend on trust that the "{worst}" episode
  is currently spending.
- **For diligence:** ask a target for episode-level NPS. If they only have a blended
  figure, they do not know which part of their franchise is working.

## Method

Ratings drawn from a per-(cohort, episode) normal latent model, clipped to 0-10,
with a small age adjustment applied to the digital-first cohort. NPS computed the
standard way: %promoters (9-10) minus %detractors (0-6). Re-running the script
reproduces these figures exactly.
"""
    write_memo("survey-nps-episodes",
               "Episode-level NPS shows a spread inside one brand that brand-level NPS hides",
               body, sources=[f"SYNTHETIC dataset generated by analysis/04_survey_nps.py (seed {SEED})"])
    print(f"   neobank: best '{best}' {by_episode.loc[neo, best]:+.0f}, "
          f"worst '{worst}' {by_episode.loc[neo, worst]:+.0f}, spread {spread:.0f}pts")


if __name__ == "__main__":
    main()
