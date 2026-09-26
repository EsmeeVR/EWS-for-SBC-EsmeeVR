# Early Warning Systems for systemic banking crises: micro and macro indicators

Replication code and results for *The effect of integrating micro- and macro-level indicators on the
performance of Early Warning Systems for systemic banking crises* (MSc thesis, University of Twente,
2026), and for the journal article based on it.

**Research question.** How does integrating micro- and macro-level indicators affect the predictive
performance of Early Warning Systems for systemic banking crises?

The study builds a bank-year panel of EU banks across 25 countries, attaches country-level
macroeconomic indicators and the Laeven and Valencia (2026) crisis label, and compares three
indicator configurations, **micro-only**, **macro-only** and **integrated**, across six model
classes in an expanding-window design.

---

## Read this first: these are not the thesis numbers

In September 2026 the whole pipeline was audited and rerun. **The results in this repository come
from the corrected run and differ from those printed in the MSc thesis.** Of roughly 1,300 figures
the thesis reports, about 1,160 change, and the comparison tool flags 31 claim changes.

| | |
|---|---|
| Branch and commit of record | `final-2026-09`, plus the pre-crisis rerun of 20-09-2026 |
| Seed of record | 42. Four further seeds (7, 13, 27, 99) were run to measure sensitivity |
| Audit of the original pipeline | [AUDIT.md](AUDIT.md), 58 issues |
| What was fixed and what was not | [RERUN.md](RERUN.md) |
| Audit of the corrected run itself | [AUDIT-FINAL-RUN.md](AUDIT-FINAL-RUN.md) |
| Old against new, cell by cell | `outputs/compare/final-with-rt2/` |
| Results across the five seeds | `outputs/seeds/seed_report.md` |

**What holds and what does not.** In the baseline indicator set, micro-only is the best
configuration at both horizons. With the crisis onset excluded from training (RT1), the integrated
configuration ranks first in all four specifications. Both hold in every seed. In the **extended**
indicator sets the winning configuration varies by seed, so no claim is made there. Integration is
not systematically better than the single-level configurations under any specification tested.

---

## Seed sensitivity

The models draw on randomness in several places: the bootstrap sample and feature subsets in random
forest, row and column subsampling in XGBoost and LightGBM, the initial weights of the MLP, tie
breaking in the decision tree, and the order in which Optuna proposes hyperparameters. Fixing the
seed fixes those draws. The number itself carries no meaning: 42 and 13 are labels for two different
draws, not quantities.

With 16 crisis countries whose crises all begin in 2008, there are few effectively independent units,
so which draw you get moves the answer. The pipeline was therefore run five times, identical except
for the seed, and the spread is reported here rather than left unstated.

The figures below cover the twelve substantive specifications: `11a`-`11d` in both variants, and the
four country-level runs. The two pre-crisis runs are left out on purpose. They are almost
seed-invariant, because the task is degenerate (see below), so including them would lower every
number here and flatter the result. Including them, the headline 0.54% becomes 0.47%.

**At the level the results are reported** (mean over the six models, 36 configuration means):

| | Seed 42 against the five-seed mean | Spread across the five seeds |
|---|---|---|
| Average | **0.54%** | 2.49% |
| Largest | **1.95%** | 10.77% |

**At individual model × configuration cells** (168 of them):

| | Seed 42 against the five-seed mean | Spread across the five seeds |
|---|---|---|
| Average | 1.73% | 5.46% |
| Largest | 21.5% | 36.7% |

Seed 42 runs above the five-seed mean in 68 of 168 cells, by **+1.93%** on average, and below it in
72, by **-2.21%** on average. 71% of cells sit within 2% of the mean. Reporting seed 42 therefore
stays inside the 2% tolerance agreed with the supervisors at the level the claims are made.

Almost all of the variation sits in three model classes:

| Model | Mean spread (AUROC) | Largest single cell |
|---|---|---|
| Decision tree | 0.055 | 0.170 |
| MLP | 0.051 | 0.174 |
| LightGBM | 0.041 | 0.245 |
| Random forest | 0.039 | 0.123 |
| XGBoost | 0.033 | 0.130 |
| **Logistic regression** | **0.001** | 0.020 |

Logistic regression solves the same convex problem every time, so no random draw enters it. Its
spread of 0.001 is the control: everything else is the draws.

**What survives a seed change**

| Claim | In all five seeds |
|---|---|
| Micro-only best in the baseline set, both horizons | yes |
| Integrated ranks first under RT1, all four specifications | yes |
| Which configuration wins in the extended sets | **no** |
| The "integrated beats both" counts per model | **no** |

Per-model and extended-set orderings are not claimable from a single seed. `outputs/seeds/seed_report.md`
gives the full picture.

---

## Running it

```bash
pip install -r requirements.txt
python tools/run_pipeline.py            # every step in dependency order
python tools/run_pipeline.py --dry-run  # list the steps, run nothing
python tools/run_pipeline.py --from 13a # resume at a step
python tools/run_pipeline.py --tranquil # the separate tranquil-years job, after the main run
```

`run_pipeline.py` checks that the notebook kernel has the pinned pandas and scikit-learn, stops at
the first failing notebook, and writes an executed copy of every notebook plus `run.log` to
`outputs/run_logs/`. Notebooks read and write via paths relative to their own folder, so run them
from `notebooks/` if you run them by hand.

Use Python 3.12 or later. `requirements.txt` pins the versions the results were produced with
(pandas 3.0.2, scikit-learn 1.8.0). The macro side runs end to end from what is committed here. The
micro side needs the ORBIS extract, which is licensed and not distributed; see [DATA.md](DATA.md).

**A rerun will not reproduce these numbers exactly.** Seeds are fixed, but XGBoost and LightGBM run
multithreaded without a deterministic mode, so floating-point results shift with core count,
hardware and numerical libraries. Optuna's TPE sampler proposes each trial from the scores of the
ones before it, so a small numerical difference is amplified through tuning rather than averaged
away. Expect differences of the order shown in the seed table above.

---

## Pipeline

### Data construction

| Notebook | Does | Needs |
|---|---|---|
| `01_micro_construction` | ORBIS extract to clean bank panel: reshape, derive indicators, apply domain bounds, split into baseline and extended sets | ORBIS |
| `02_macro_construction` | Five macro sources to four country-year panels, including the real-time credit gap | public |
| `03_panel_construction` | Build the crisis label, then merge micro, macro and label | ORBIS |
| `04_feature_engineering` | Lag every feature by one year, and again by two for the longer-lag test | ORBIS |
| `05_macro_individual_merge` | Build the country-level panels the macro-only notebooks use, which do not come from the merge cascade above | public |

### Modelling

Six model classes throughout: logistic regression, decision tree, random forest, XGBoost, LightGBM
and a multilayer perceptron. They are chosen as a **set** spanning the range of approaches, not as
individually optimal techniques, because the object of comparison is the indicator configuration.

| Notebook | Specification | Test years |
|---|---|---|
| `11a_modelling_baseline_lag1` | Baseline indicators, t-1 | 2010-2012 |
| `11b_modelling_robust_lag1` | Extended indicators, t-1 | 2010-2012 |
| `11c_modelling_baseline_lag2` | Baseline indicators, t-2 | 2011-2012 |
| `11d_modelling_robust_lag2` | Extended indicators, t-2 | 2011-2012 |
| `12a_macro_only_baseline` | Macro-only, country level | 2008-2012 |
| `12b_macro_only_robust` | Macro-only, extended window | 2001-2012 |
| `12a_granularity_baseline` | Macro at country against bank level, baseline | 2010-2012 |
| `12b_granularity_robust` | Macro at country against bank level, extended | 2010-2012 |
| `rt2a_precrisis_baseline` | Pre-crisis relabelling, baseline | 2007 only |
| `rt2b_precrisis_robust` | Pre-crisis relabelling, extended | 2007 only |

Each of `11a`-`11d` runs two variants: `baseline_t1` on the full training window, and `rt1`, which
excludes each country's onset year and the year after it from **training**. Because every crisis
begins in 2008, RT1 has no crisis observations left to train on until 2010 re-enters the window,
which is why it evaluates only 2011 and 2012.

### Interpretation and results

| Notebook | Does |
|---|---|
| `13a`-`13d_attribution_*` | SHAP, ALE and Friedman's H for each of the four main specifications |
| `14_visualisations` | Figures across specifications |
| `15_results` | Result tables, significance tests, appendix tables |
| `16_descriptive_statistics` | Sample descriptives and correlations |

---

## The pre-crisis check is a negative result

`rt2a` and `rt2b` relabel the target: `crisis_rt2 = 1` in the two years before each country's first
onset, `NaN` in actual crisis years so they leave both train and test, `0` otherwise. The intention
was to ask whether a crisis is coming rather than whether one is happening.

**It does not work, and the notebooks now show why.** Each reports a falsification baseline: a rule
that ignores every variable and simply repeats the label its country carried in training.

| | AUROC | AUPRC |
|---|---|---|
| Country-label rule | **1.000** | **1.000** |
| Best model | 1.000 | — |

1.000 in both notebooks and in all five seeds. No model beats it. Because every onset is 2008, the
pre-crisis window is 2006-2007 for every crisis country, the labels are constant within a country,
and only 2007 can be a test year. The task is solvable from country identity alone. Logistic
regression, which carries country dummies, reaches 1.000 in every configuration, which makes the
mechanism explicit.

These results are reported as a negative result, not as evidence that crises can be anticipated.
The baseline is in the `a46_falsification` sheet of each workbook.

---

## Scoring per country-year (added 26-09-2026)

The crisis label is set per country, but the main comparison scores bank-years, so countries weigh by
their number of banks. `tools/granularity_all_configs.py` averages the stored bank-level predictions per
country-year (equal weights) and scores all three configurations, and the country-level macro model, on
the same 25 countries, for all five seeds. `tools/region_benchmark_testyears.py` adds a region-only rule
for 2010-2012 and AUROC within Western and within Central and Eastern Europe.

| Mean AUROC, 2010-2012, range over five seeds | Micro | Macro | Integrated | Country model |
|---|---|---|---|---|
| Baseline, bank-years | 0.73-0.75 | 0.64-0.67 | 0.66-0.68 | |
| Baseline, country-years | 0.87-0.88 | 0.69-0.71 | 0.70-0.73 | 0.65-0.67 |
| Extended, bank-years | 0.71-0.72 | 0.73-0.75 | 0.74-0.76 | |
| Extended, country-years | 0.85-0.86 | 0.74-0.76 | 0.76-0.78 | 0.68-0.69 |

Micro > integrated > macro per country-year in both sets and all seeds, also without LR; the region rule
reaches 0.617. Read it as recognition of countries in an ongoing crisis (A29), not as early warning.
Both scripts only read committed outputs plus `outputs/tables/panel_index_{base,robust}.parquet`, the
country and year of every panel row (no bank identifier), so they run without the licensed ORBIS data.
Figures for the paper: `tools/paper_figures.py` -> `outputs/figures/paper/`.

---

## Disclosures

**Threshold metrics are calibrated out of sample, and are sometimes absent.** The alarm cut-off for
test year *t* is chosen on the predictions for *t-1*; one extra window is fitted to calibrate the
first test year. Where no evaluated predecessor exists, the threshold-dependent metrics are left
empty rather than fitted on the test year. This affects **RT1 in 2011** in all four specifications,
so RT1 miss rate, false alarm rate and loss rest on 2012 alone, and RT1 is reported on AUROC and
AUPRC only. The pre-crisis runs have no threshold metrics at all, for the same reason. The column
`test_optimal_threshold` records the best-case cut-off for transparency; it is not a usable rule.

**The test years contain no crisis onsets.** All 16 crises begin in 2008, so every crisis
observation in 2010-2012 is year three to five of an ongoing crisis. The out-of-sample results
measure recognition of an ongoing crisis, not early warning. This is a property of the crisis
dating and the sample period, and it bounds what any specification here can claim.

**Tuning is conditional.** A fresh Optuna study of 50 trials runs per `(variant, dataset, test_year,
model)`, but only when the inner validation split contains at least one positive and one negative
case. Where it does not, the model is fitted on library defaults. That is **54 of 90 fits in `11a`
and `11b`, and 36 of 72 in `11c` and `11d`**, spread evenly across test years. It applies to every
model and configuration within a window alike, so the comparisons are unaffected, but the absolute
numbers depend on it.

**Significance uses a country-cluster bootstrap.** Labels are set per country, so treating
bank-years as independent overstates significance: on the published predictions DeLong called 58% of
comparisons significant against 14% for the bootstrap. Tables mark significance by the unadjusted
bootstrap. Under Holm correction nothing remains significant; whether to report Holm alongside is
an open decision.

**The trial budget is not symmetric across models.** All six get 50 trials while tuning between one
and six hyperparameters (LR 1, DT 2, MLP 3, RF 4, XGB 5, LGBM 6). This bounds what the attribution
results can claim.

**Regularisation differs by model class.** Genuine L2 penalties apply to logistic regression (`C`)
and the MLP (`alpha`) only. The tree models use complexity constraints instead.

**Logistic regression is explained without its country dummies.** In `11a`-`11d` logistic regression
includes country dummies, and that is the LR in every performance table. The attribution notebooks
refit LR on the indicators only, with the same tuned `C`, and compute SHAP, ALE and the H-statistics
on that model. With more than twenty dummy columns, attribution would largely go to country
identity, which is not an indicator. The consequence must be read with it: the explained LR is not
the evaluated LR and performs clearly worse, by 0.13-0.48 mean AUROC across the four specifications.

**Outliers are bounded, not winsorised.** Equity ratio outside [0, 1.5], leverage outside [0, 100]
and loans-to-deposits above 5 are set to `NaN`. Macro variables get no treatment beyond `inf` to
`NaN`. Extreme tails elsewhere are real.

**Interpolation fills internal gaps only.** `limit_area="inside"` throughout, so no value is
extrapolated before a series starts or after it ends.

**Variable selection was not redone on the corrected sample.** With the non-banks and empty entities
removed, the agreed missingness thresholds would admit two further variables in the baseline set and
four in the extended set. The published variable sets are kept (`RESELECT_VARIABLES = False` in
`01`), because re-selecting changes the specification rather than correcting an error.

**Known issues that remain in the attribution notebooks** (the micro/macro prefix split in
`13a`-`13d`, and the hyperparameter file used for two `11b`/`11d` windows) are recorded with their
measured effects in [AUDIT.md](AUDIT.md), issues A3 to A6 and A50 to A52. Every affected line carries
a `KNOWN ISSUE` comment.

---

## Repository layout

```
notebooks/     the pipeline, in dependency order, plus ews_common.py
tools/         run_pipeline.py, compare_runs.py, aggregate_seeds.py, tranquil_years.py
data/          inputs; the micro tree is gitignored, see DATA.md
outputs/       figures, tables, result stores, attribution, seeds, compare, run_logs
archive/       superseded work, kept for provenance, not part of the pipeline
```

Notebook outputs are stripped before commit: committed notebooks carry code only, and everything
they produce is committed as a file under `outputs/`, so nothing is lost and diffs stay readable.

`notebooks/ews_common.py` holds the expanding-window split, the RT1 filter, the Optuna objective,
`run_model` and the significance tests, shared by `11a`-`11d` and `12a`/`12b`, so a fix is made once
for every specification.

---

## Data availability

The ORBIS/Bankscope extract is licensed from Bureau van Dijk per institution and may not be
redistributed. Nothing derived from it at bank level is committed: the rule is that if a file has a
`bank_id` column, it stays out. The macro sources are public and the pipeline reproduces them from
what is here. [DATA.md](DATA.md) gives the search strategy, the extract version and the sample
composition, so the extract can be rebuilt under an institutional licence.

---

## Citing

Laeven, L., & Valencia, F. (2026). *Systemic Banking Crises Database: 1970-2025.* IMF Working Paper
WP/26/94.

See [DATA.md](DATA.md) for the full data availability statement.
