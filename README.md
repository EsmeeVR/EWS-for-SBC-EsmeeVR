# Early Warning Systems for systemic banking crises: micro and macro indicators

Replication code for the MSc thesis *The effect of integrating micro- and macro-level indicators on
the performance of Early Warning Systems for systemic banking crises* (University of Twente, 2026).

**Research question.** How does integrating micro- and macro-level indicators affect the predictive
performance of Early Warning Systems for systemic banking crises?

The study builds a bank-year panel of 636 EU banks across 25 countries, attaches country-level
macroeconomic indicators and the Laeven and Valencia (2026) crisis label, and compares three
indicator configurations, **micro-only**, **macro-only** and **integrated**, across six model
classes in an expanding-window design.

---

## Running it

```bash
pip install -r requirements.txt
jupyter lab notebooks/
```

Notebooks read and write via paths relative to their own folder, so run them from `notebooks/`.
They are numbered in dependency order and each one states its inputs and outputs at the top.

Use Python 3.12 or later: one cell uses the f-string syntax introduced in 3.12 (PEP 701).
`requirements.txt` pins the versions the results were produced with. `02_macro_construction`
uses `transform` instead of `groupby.apply` in two places to avoid a `KeyError` in pandas 2.2 and
later.

The macro side runs end to end from what is committed here. The micro side needs the ORBIS extract,
which is licensed and not distributed; see [DATA.md](DATA.md).

---

## Pipeline

### Data construction

| Notebook | Does | Needs |
|---|---|---|
| `01_micro_construction` | ORBIS extract to clean bank panel: reshape, derive ten indicators, apply domain bounds, split into baseline and robustness sets | ORBIS |
| `02_macro_construction` | Five macro sources to four country-year panels, including the real-time credit gap | public |
| `03_panel_construction` | Build the crisis label, then merge micro, macro and label | ORBIS |
| `04_feature_engineering` | Lag every feature by one year, and again by two for the longer-lag robustness test | ORBIS |
| `05_macro_individual_merge` | Build the country-level panels the macro-only notebooks use, which do not come from the merge cascade above | public |

### Modelling

Six model classes throughout: logistic regression, decision tree, random forest, XGBoost, LightGBM
and a multilayer perceptron. They are chosen as a **set** spanning the range of approaches, not as
individually optimal techniques, because the object of comparison is the indicator configuration.

| Notebook | Specification | Test years |
|---|---|---|
| `11a_modelling_baseline_lag1` | Baseline indicators, t-1 | 2010-2012 |
| `11b_modelling_robust_lag1` | Extended indicators, t-1 | 2010-2012 |
| `11c_modelling_baseline_lag2` | Baseline indicators, t-2 | 2010-2012 |
| `11d_modelling_robust_lag2` | Extended indicators, t-2 | 2010-2012 |
| `12a_macro_only_baseline` | Macro-only, country level | 2008-2012 |
| `12b_macro_only_robust` | Macro-only, extended window | 2008-2012 |
| `12a_granularity_baseline` | Macro at country level against bank level, baseline | 2008-2012 |
| `12b_granularity_robust` | Macro at country level against bank level, extended | 2008-2012 |
| `rt2a_precrisis_baseline` | Pre-crisis relabelling, baseline | 2007, fixed split |
| `rt2b_precrisis_robust` | Pre-crisis relabelling, extended | 2007, fixed split |

`rt2` **relabels the target**, it does not restrict the test set. `crisis_rt2 = 1` in the two years
before each country's first onset, `NaN` in actual crisis years so they leave both train and test,
`0` otherwise. It asks whether a crisis is coming, not whether one is happening. Its positive rate
is high, so AUPRC has a no-skill floor around 0.84 and AUROC is the metric that carries the claim.

### Interpretation and results

| Notebook | Does |
|---|---|
| `13a`-`13d_attribution_*` | SHAP, ALE and Friedman's H for each of the four main specifications |
| `14_visualisations` | Figures across specifications |
| `15_results` | Result tables, DeLong tests, appendix tables |
| `16_descriptive_statistics` | Sample descriptives and correlations |

Generated artefacts are committed under `outputs/`: `figures/`, `tables/`, `results/` (raw metric
stores per specification) and `attribution/`.

---

## Repository layout

```
notebooks/     the pipeline, in dependency order
data/          inputs; the micro tree is gitignored, see DATA.md
outputs/       figures, tables, result stores, attribution
archive/       superseded work, kept for provenance, not part of the pipeline
```

---

## Notes for anyone reading the code

**Notebook outputs are stripped.** Committed notebooks carry code only. Every figure and table they
produce is committed as a file under `outputs/`, so nothing is lost and diffs stay readable.

**Tuning is conditional.** A fresh Optuna study of 50 trials runs per `(variant, dataset, test_year,
model)`, but only when the inner validation split contains at least one positive and one negative
case. Where it does not, the model is fitted on library defaults. This affects 54 of 90 fits in
`11a` and 36 of 72 in `11d`. It applies to every model and configuration within a window alike, so
the comparisons the thesis draws are unaffected, but it is disclosed because the absolute numbers
depend on it.

**A rerun will not reproduce the published numbers exactly.** Seeds are fixed throughout
(`TPESampler(seed=42)` for Optuna, `random_state=42` for every model), but that does not make the
pipeline deterministic across machines or library versions:

- XGBoost and LightGBM run multithreaded on all available cores by default, and neither is put in a
  deterministic mode (`deterministic` is not set for LightGBM). Floating-point results can shift
  with the number of cores, the hardware and the numerical libraries underneath. The MLP depends
  on the same numerical libraries.
- Optuna's TPE sampler proposes each trial from the scores of the trials before it. A small
  numerical difference in one validation score can steer the search to different hyperparameters,
  so small differences are amplified through tuning rather than averaged out.
- The evaluation sets are small (two or three test years per specification, with few positive
  cases in some inner validation windows), so a few changed rankings move AUROC and AUPRC visibly.
- Library upgrades can change defaults and the TPE sampler itself.

Variation should be largest for the tuned tree ensembles and the MLP, and smallest for logistic
regression (one hyperparameter, deterministic solver) and for fits that fall back to library
defaults (see the next note). Its size has not been measured: the published results come from a
single run per specification.

**The trial budget is not symmetric across models.** All six get 50 trials while tuning between one
and six hyperparameters (LR 1, DT 2, MLP 3, RF 4, XGB 5, LGBM 6). This bounds what the attribution
results can claim.

**Regularisation differs by model class.** Genuine L2 penalties apply to logistic regression (`C`)
and the MLP (`alpha`) only. The tree models use complexity constraints instead.

**Outliers are bounded, not winsorised.** A small number of ratios are set to `NaN` by hard domain
bounds: equity ratio outside [0, 1.5], leverage outside [0, 100], loans-to-deposits above 5. Macro
variables get no value treatment beyond `inf` to `NaN`. Extreme tails elsewhere are therefore real.

**Interpolation fills internal gaps only.** `limit_area="inside"` throughout, so no value is ever
extrapolated before a series starts or after it ends.

---

## Known issues

These are recorded rather than silently fixed, because fixing them would mean re-running models and
changing published numbers.

1. **The modelling notebooks duplicate shared code.** The Optuna objective, `run_model` and the
   expanding-window split are copy-pasted across eight notebooks rather than imported from a common
   module. This is the intended next refactor. It is also how `12b` came to differ from
   `12b_granularity` (see 3).

2. **`14_visualisations` and `15_results` deliberately read different snapshots for two
   specifications.** Both point at `_final` result files except for `11c` and `rt2a`, which stay on
   `_draft` snapshots. Those two were unaffected by the HP filter correction that prompted the
   repointing of the others, so their drafts and finals are equivalent. The paths are left as they
   were when the published figures were generated.

3. **`12b_macro_only_robust` was last saved in a failed state in the original workspace.** Its
   training loop raised `ValueError: Shape of passed values is (75, 11), indices imply (75, 12)`
   inside the Optuna objective, where `pd.DataFrame(X_tr, columns=X_tr_raw.columns)` received eleven
   columns for twelve names, consistent with the imputer dropping an all-missing column in one fold.
   The committed results in `outputs/results/12b/` come from the earlier successful run that
   produced them, not from the failed one. The notebook has not been re-run.

4. **`16_descriptive_statistics` is large and its cells must be edited as JSON.** Stored outputs
   previously pushed it past what some tools will open. Outputs are stripped here, which resolves it.

5. **`13a`-`13d` split features into micro and macro by name prefix.** Several cells treat a feature
   as micro when its name starts with `g_`, `l_`, `r_`, `c_`, `x_` or `p_`. `inc_nii`, `inc_op` and
   `cr_impchg` match none of these, so they are counted as macro. The modelling notebooks are not
   affected (`11a`-`11d` list the macro columns explicitly and take micro as the rest), so no
   performance result depends on this, and the SHAP value files are written before the split.
   `14_visualisations` and `15_results` use an explicit macro list and were corrected. Two things
   in `13a`-`13d` are affected:
   - **The Friedman H-statistic and partial dependence pairs.** The pairs are the top five micro
     features crossed with the top five macro features, plus three theory-driven pairs, and the
     top five micro come from the prefix split. In `11a`, `inc_nii` and `inc_op` belong in the top
     five but are left out, with `p_nim` and `x_ib_liab` in their place. In `11b`, `inc_nii` is left
     out for `l_assets`. For `11c` and `11d` the selection is the same under either split. The
     H-statistics in `outputs/attribution/` are correct for the pairs computed, but for `11a` and
     `11b` those are not the intended top-five pairs, and interactions between net interest income
     or operating income and the macro indicators were not tested. `14_visualisations` reads these
     files for the H-statistic figure, so the figure carries the same pair sets.
   - **The micro/macro summaries and figures `13a`-`13d` produce themselves.**

   Every affected line carries a `KNOWN ISSUE` comment. It is left as run because correcting the
   pairs means re-running the H-statistic and partial dependence cells.

6. **The bank sample includes some non-banks, concentrated in Ireland.** The ORBIS search on NACE
   641 also admits code 6411 (central banking), which ORBIS assigns to a number of Irish companies
   that are not banks. Their deposit, loan and equity lines are missing and filled by the year
   median during imputation. They make up under 1% of the usable bank-years but about 2% of the
   crisis observations (1.8% for lag-1, 1.5% for lag-2). Counts, entities and the fix for a new
   extract are in [DATA.md](DATA.md#sample-composition-non-banks-in-the-extract). Not corrected,
   because it means re-running every bank-level model.

---

## Citing

Laeven, L., & Valencia, F. (2026). *Systemic Banking Crises Database: 1970-2025.* IMF Working Paper
WP/26/94.

See [DATA.md](DATA.md) for the full data availability statement.
