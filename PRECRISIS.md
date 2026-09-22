# Pre-crisis check (redesign): decision rule

Written 22-09-2026, **before any code for this check exists or has run**. The rules below fix what
counts as a result. They are not changed after the results are seen; any deviation is recorded
here with its date and reason.

## Why a redesign

The original pre-crisis check (`rt2a`/`rt2b`, audit A46) relabelled the two years before each onset.
All 16 crises in the sample start in 2008, so the positive years are 2006-2007 for every crisis
country, the label is constant within a country, and only 2007 can be a test year. A rule that
repeats each country's training label scores AUROC 1.000 (the `a46_falsification` sheets). Laeven &
Valencia (2026) record no later onsets for these 25 countries, so a second wave is not available.

## Question

Are the patterns that the models associate with a crisis already present **before** the 2008
onsets, in countries the model has never seen? This is a backcast: training uses years after 2008,
so it is **not** a real-time forecast and is never framed as one.

## Setup (fixed)

- **Label:** the crisis-state label of the main design (Laeven & Valencia 2026), unchanged.
- **Groups:** crisis countries = the 16 with a 2008 onset (AUT BEL DEU DNK ESP FRA GRC HUN IRL ITA
  LUX LVA NLD PRT SVN SWE); non-crisis = the other 9 (BGR CZE EST FIN HRV LTU POL ROU SVK).
- **Estimation:** leave-one-country-out. For each of the 25 countries, models are trained on the
  other 24 over 2006-2012 and score the held-out country in every year 2006-2012. The scored country
  never enters training, so country identity cannot leak.
- **Tuning:** Optuna, 50 trials, as in the main design, but validated on held-out *countries*
  instead of the last two years (the exact inner split is fixed in code before the first run and
  recorded here). The tuning design is a choice that can affect claims (as seen in the thesis), so
  it is disclosed.
- **Configurations and models:** micro, macro and integrated; the six models; baseline indicator
  set; **lag 1**.
- **Unit of evaluation:** the country-year. Bank-level predictions are averaged within each
  country-year, as in the granularity comparison, so countries are not weighted by their number of
  banks. (At bank level the region rule below reaches 0.94-0.95, because the crisis countries hold
  most banks; the country-year is the fair unit.)
- **Configuration score:** AUROC averaged over the six models, the level used in the main results.
- **Seeds:** seed 42 is reported; the claim check uses all five seeds (42, 7, 13, 27, 99).
- **No changes** to indicators, specifications or tuning after results are seen.

## Baselines (computed in advance)

- **Country-label rule:** 0.5 by construction (the held-out country is never in training).
- **Region rule:** "Western European (EU-14) = crisis". 13 of 16 crisis countries are Western; of
  the 9 non-crisis countries only Finland is. Country-level AUROC = (13/16 + 8/9) / 2 = **0.851**
  (verified on the panel: 0.8507).
- **No skill:** 0.5.

## Rules

1. **Signal before onset.** A configuration shows a signal if its country-level AUROC in **2007**
   is **above 0.851** (point estimate) in **all five seeds**. 2006 is reported alongside but does not
   decide. The country-cluster bootstrap interval is computed and reported as well, and the rule is
   also evaluated on the lower bound, so the stricter reading is available; the **point estimate
   decides**.
2. **Within Central and Eastern Europe (supporting, not decisive).** Country-level AUROC among the
   11 CEE countries only (crisis: HUN LVA SVN; non-crisis: BGR CZE EST HRV LTU POL ROU SVK; 24 pairs)
   is computed and reported in all five seeds. It supports rule 1 but is not required for it: with
   3 against 8 countries one misranked pair moves the AUROC by 0.04.
3. **Configurations are reported, not ranked.** All three configurations are shown, but the check
   is about whether a pre-crisis signal exists, not about integration. No claim that one
   configuration beats another is made from this check.
4. **Lag 2** is run only if rule 1 holds at lag 1 for at least one configuration.
5. **Always reported, whatever the outcome:** the figure of the average predicted probability per
   year (2006-2012) for crisis against non-crisis countries per configuration, the AUROCs of rules
   1 and 2 with their intervals, and all baselines.
6. **Null result.** If no configuration meets rule 1, that is reported as it is: "no signal beyond
   region" (or "no signal"), without softening.
7. **Framing.** "The signal is present before onset", never real-time prediction.

## Deviations

**22-09-2026, before the first run (implementation details fixed in `tools/precrisis_loco.py`):**
- **LR without country dummies.** A held-out country has no dummy of its own, so LR uses the
  indicators only. The LR in the main tables carries dummies; the two are not the same model.
- **Inner validation split for tuning:** within the 24 training countries, **4 crisis and 2
  non-crisis countries** form the inner validation set, drawn per outer fold with the seed
  (`numpy.random.default_rng([seed, fold])`). The objective is bank-level AUROC on that set, as in the
  main design. Every inner split contains crisis observations, so every fit is tuned (no defaults).
- **Training years:** label years 2006-2012 of the lag-1 panel (`me_merged_base.parquet`), 1,901
  bank-years; 15 micro and 9 macro indicators, the 11a baseline set after the Belsley drops.
- Seeds enter through each seed worktree's own `ews_common.py` (model `random_state`) and the Optuna
  sampler seed, exactly as in the main run.
