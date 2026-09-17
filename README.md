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
defaults (see the note above). Its size has not been measured: the published results come from a
single run per specification. MLP attributions in `13a`-`13d` are also stochastic: the
KernelExplainer samples feature coalitions without a fixed seed, so recomputing SHAP for the same
MLP moved mean |SHAP| per feature by up to 0.007.

**The trial budget is not symmetric across models.** All six get 50 trials while tuning between one
and six hyperparameters (LR 1, DT 2, MLP 3, RF 4, XGB 5, LGBM 6). This bounds what the attribution
results can claim.

**Regularisation differs by model class.** Genuine L2 penalties apply to logistic regression (`C`)
and the MLP (`alpha`) only. The tree models use complexity constraints instead.

**Logistic regression is explained without its country dummies.** In `11a`-`11d` logistic
regression includes country dummies (`get_dummies(country_iso, drop_first=True)`), and this is the
LR in every performance table. The attribution notebooks `13a`-`13d` refit logistic regression on
the micro and macro indicators only, with the same tuned `C`, and compute SHAP, ALE and the
H-statistics on that model. This is deliberate: with more than twenty dummy columns, attribution
would largely go to country identity, which is not an indicator and would obscure the micro/macro
comparison the attribution exists for. The consequence has to be read with it. The explained LR is
not the evaluated LR and performs clearly worse: in the baseline integrated configuration, the
published `lr_no_dummies` runs score 0.07-0.32 AUROC below LR with dummies per test year, and the
refitted attribution models checked in `11b` and `11d` score 0.09-0.26 below. LR attribution results
describe how the indicators enter a model without country fixed effects. The other five model
classes are refitted exactly as evaluated, apart from the hyperparameter file issue in Known
issues 7.

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

   **Check on the missing pairs (17-09-2026).** The pairs that were left out (`inc_nii` and `inc_op`
   against the five macro features in `11a`, `inc_nii` against them in `11b`) were computed with the
   notebooks' own fitting and partial dependence code, for every model, test year and variant. One
   stored pair was recomputed alongside as a control and matched exactly (H² difference 0). The
   missing pairs show no more interaction than the stored ones:

   | | Missing pairs: mean H² | max H² | Stored pairs: mean H² | max H² |
   |---|---|---|---|---|
   | `11a` baseline_t1 | 0.0007 | 0.027 | 0.0027 | 0.217 |
   | `11a` rt1 | 0.0023 | 0.078 | 0.0082 | 0.144 |
   | `11b` baseline_t1 | 0.0019 | 0.086 | 0.0064 | 0.508 |
   | `11b` rt1 | 0.0032 | 0.038 | 0.0062 | 0.123 |

   No missing-pair cell reaches H² ≥ 0.10. The largest values come from the MLP. The finding of
   near-zero micro-macro interaction does not depend on the pair selection. For `11b` this check
   uses the same hyperparameter file as the stored results, so it inherits issue 7.

6. **The bank sample includes some non-banks, concentrated in Ireland.** The ORBIS search on NACE
   641 also admits code 6411 (central banking), which ORBIS assigns to a number of Irish companies
   that are not banks. Their deposit, loan and equity lines are missing and filled by the year
   median during imputation. They make up under 1% of the usable bank-years but about 2% of the
   crisis observations (1.8% for lag-1, 1.5% for lag-2). Counts, entities and the fix for a new
   extract are in [DATA.md](DATA.md#sample-composition-non-banks-in-the-extract). Not corrected,
   because it means re-running every bank-level model.

   **Test-side sensitivity check (17-09-2026).** Without retraining, all entities not coded 6419
   were dropped from the stored test predictions (the `proba_store` files `15_results` reads) and
   AUROC and AUPRC were recomputed. That removes 1-3 test observations per test year, all of them
   crisis observations. Recomputing on the full test sets reproduced the stored metrics exactly,
   which confirms the rows were matched correctly.
   - Across `11a`-`11d`, six models and three configurations (`baseline_t1`, mean over test years),
     the largest change in any cell is 0.008 AUROC and 0.011 AUPRC. Averaged over models, changes
     are within ±0.004 AUROC and ±0.005 AUPRC, except micro-only in `11b` (+0.007 AUROC).
   - The ordering of micro-only, macro-only and integrated is unchanged in 24 of 24 model ×
     specification cells on AUROC and 23 of 24 on AUPRC. The exception is the decision tree in `11a`,
     where macro-only (0.380 to 0.369) and micro-only (0.376 to 0.374) swap on AUPRC.
   - The narrowest AUROC gap in the main results, integrated against macro-only in `11b` (0.7248
     against 0.7213, mean over models), stays the same size after exclusion (0.7254 against 0.7219).
     Changes under the `rt1` variant are of the same size.

   This covers evaluation only. The non-banks remain in every training window, and their effect on
   the fitted models is unknown without re-running.

7. **`13b` and `13d` refit models with pre-correction hyperparameters for two test years.** The
   attribution notebooks load `best_params_log.pkl`. For `11b` and `11d` that file is the 02-06-2026
   draft, tuned before the credit-gap HP filter was corrected. The published results use
   `best_params_log_final.pkl`. The two files are identical for `11a`, and `11c` has only one file.
   For `11b` and `11d` they differ in `baseline_t1`, macro-only and integrated, test years 2011 and
   2012, for all six models (23 and 24 entries). `rt1` is unaffected. The data are the corrected data
   in both cases. Only the hyperparameters differ, but the attribution models for those windows are
   not the evaluated models. SHAP, ALE, partial dependence and H-statistics are all affected for
   these windows, and so are the figures built on them in `14_visualisations` and `15_results`.

   **Sensitivity check (16/17-09-2026).** The affected windows were refitted with both parameter files.
   With the draft file the stored SHAP values are reproduced exactly (MLP to within its sampling
   noise). With the final file the five non-LR models reproduce the published AUROC exactly (LR
   differs by design, see the notes above). Share of total mean |SHAP| going to micro indicators,
   integrated configuration, `baseline_t1` pooled over test years:

   | Model | `11b` published | `11b` final params | `11d` published | `11d` final params |
   |---|---|---|---|---|
   | Decision tree | 1.2% | 1.9% | 0.3% | 1.4% |
   | LightGBM | 3.7% | 6.0% | 9.4% | 3.9% |
   | Random forest | 6.1% | 3.7% | 10.7% | 6.3% |
   | XGBoost | 10.9% | 10.3% | 11.7% | 18.7% |
   | MLP | 19.4% | 19.2% | 21.4% | 18.9% |
   | Logistic regression | 15.2% | 14.8% | 15.7% | 16.8% |

   In `11b` the effect is small: rank correlations of pooled feature importance between the two
   runs are 0.92-1.00 and the top five features are nearly unchanged. In `11d` it is larger: micro
   shares move by up to 7 percentage points, the decision tree's rank correlation is 0.64, and the
   top feature changes for random forest (real GDP growth to FX reserves growth) and XGBoost (credit
   growth to real GDP growth). Macro indicators take at least 78% of attribution in every model under
   both parameter files, so the dominance of macro indicators in attribution does not depend on
   the parameter file. Exact `11d` shares and rankings in the published figures should be read with
   this in mind. After discussion with the supervisor, the published attribution outputs are kept as
   they are and the issue is disclosed here. Outputs recomputed with the final file exist in the
   original workspace (`outputs_11b_finalpkl`, `outputs_11d_finalpkl`) and agree with this check; they
   are not part of this repository.

---

## Citing

Laeven, L., & Valencia, F. (2026). *Systemic Banking Crises Database: 1970-2025.* IMF Working Paper
WP/26/94.

See [DATA.md](DATA.md) for the full data availability statement.
