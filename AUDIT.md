# Pipeline audit before rerun (started 17-09-2026)

Purpose: find every issue in the pipeline before a single, final rerun for the journal paper.
Each issue records where it sits, what goes wrong, what it affects, how severe it is and the fix
planned for the rerun. Decisions on which fixes go into the rerun are taken with the supervisors
once the audit is complete.

**Severity**
- **High**: can change a headline claim, or introduces look-ahead into reported out-of-sample results.
- **Medium**: affects secondary results (robustness, attribution) or reproducibility of a reported number.
- **Low**: no plausible effect on conclusions; documentation, hygiene or disclosure.

**Status**: `open` (found, fix not decided) · `decided` (fix agreed) · `fixed` (in code) · `disclose` (kept, documented only)

---

## Audit progress

| Stage | Notebooks | Status |
|---|---|---|
| Data construction | 01, 02, 03, 04, 05 | 01 done (A2, A8, A16-A22); 02-05 not started (04 partly: A7) |
| Core modelling loop | 11a | partly (A1, A13) |
| Specification variants | 11b, 11c, 11d (diff against 11a) | not started |
| Macro-only and granularity | 12a, 12b (both variants) | not started (A11 known) |
| Pre-crisis relabelling | rt2a, rt2b | not started |
| Crisis-definition check | R&R notebooks (vault `Different Definition/Code_RR`) | not started |
| Attribution | 13a-13d | partly (A3-A6) |
| Aggregation and figures | 14, 15 | not started (A10 known) |
| Descriptives | 16 | not started |

---

## Issue register

| ID | Stage | Location | Issue | Affects | Severity | Planned fix | Status |
|---|---|---|---|---|---|---|---|
| A1 | Evaluation | 11a-d, 12, rt2 `run_model` | F1-optimal classification threshold is chosen on the **test** year (`precision_recall_curve(y_test, ...)`). Miss rate, false alarm rate, F1, recall, precision and loss L(alpha) are ex-post optimal. AUROC, AUPRC, DeLong unaffected. | All threshold-based tables and loss results | High | Choose the threshold without test labels: on inner validation predictions, or on the previous test year's out-of-sample predictions | open |
| A2 | Sample | ORBIS extract, 01 | NACE 641 search admits 6411 (central banking): 34 of 52 Irish entities are non-banks with fully imputed balance sheets, plus two central banks elsewhere. About 2% of usable crisis observations. Test-side check: max AUROC change 0.008, ordering unchanged. | All bank-level results | Medium | Filter on 6419 and review remaining entities by name (decide on foreign banks with IE identifiers) | open |
| A3 | Attribution | 13a-d | Micro/macro split by name prefix counts `inc_nii`, `inc_op`, `cr_impchg` as macro; top-5 micro for H-statistic and PD pairs wrong in 11a and 11b. Check: missing pairs show no interaction. | H-statistic and PD pairs (11a, 11b); NB13 summaries | Medium | Use the explicit macro list from 14/15 | open |
| A4 | Attribution | 13b, 13d | Load draft `best_params_log.pkl` (pre HP-filter fix) instead of `_final`; differs for baseline 2011-2012. 11d micro shares move up to 7 pp. | SHAP, ALE, PD, H for 11b/11d baseline | Medium | Single source of hyperparameters; ideally store fitted models in 11 and reuse them in 13 | open |
| A5 | Attribution | 13a-d | Logistic regression is refitted **without** country dummies (intentional), so LR attribution explains a model 0.07-0.32 AUROC weaker than the evaluated LR. | LR SHAP/ALE/H | Medium (design) | Decide: keep and disclose, or explain the evaluated model and report the dummies as one grouped block | open |
| A6 | Attribution | 13a-d | MLP SHAP uses unseeded `KernelExplainer` (thesis text says DeepSHAP); MLP attributions vary up to 0.007 mean abs SHAP between runs. | MLP attribution; method description | Low | Seed the explainer; describe KernelSHAP correctly | open |
| A7 | Feature engineering | 04 `lag_features` | Lag is `groupby(bank_id).shift(k)`: previous **row**, not calendar year t-k. Banks with gaps get older values. Lag-1: 46/4,073 rows (14/1,997 usable); lag-2: 68/3,539 (22/1,616). No look-ahead. | All bank-level models, marginally | Low | Lag on calendar year (merge on year - k) | open |
| A8 | Imputation | 01 `panel_impute`, 02 | Within-bank interpolation and bank mean can use later observations of the same bank (under 0.4% of cells). | Strict real-time claim | Low | Forward-only fill or expanding bank mean; or disclose | open |
| A9 | Code structure | 11a-d, 12, rt2 | Objective, `run_model` and split copied across eight notebooks (README issue 1); already caused divergence (12b). | Risk of inconsistent fixes in the rerun | Low (risk: Medium) | Move shared code into one module before the rerun | open |
| A10 | Aggregation | 14, 15 | Read `_final` files except `11c` and `rt2a` (draft snapshots) (README issue 2). | Provenance of figures | Low | One result file per specification after rerun | open |
| A11 | Macro-only | 12b | Last saved in failed state: imputer drops an all-missing column in one fold, column-name mismatch (README issue 3). Published results from an earlier successful run. | Reproducibility of 12b | Medium | Keep column alignment when the imputer drops a column | open |
| A12 | Reproducibility | 11-13 | Nondeterminism not controlled or measured: multithreaded XGBoost/LightGBM, no deterministic mode, unseeded KernelSHAP. | Exact reproduction of numbers | Low | Fix threads/deterministic flags and seeds; optionally repeat with several seeds to report variation | open |
| A13 | Tuning | 11a-d | Tuning needs positives in both inner folds; otherwise library defaults (54 of 90 fits in 11a, 36 of 72 in 11d). | Absolute performance; comparability across windows | Medium (design) | Decide on inner validation design that contains positives (e.g. grouped or time-aware split with positive years) | open |
| A14 | Data | 02 | Current data vintages, not real-time vintages; revisions are in the inputs. | Real-time claim | Low | Disclose | disclose |
| A16 | Sample / imputation | 01 `panel_impute` | No bank-year or entity completeness rule. 77 of 1,997 usable lag-1 rows (3.9%) had all five core items (deposits, gross loans, equity, interbank liabilities, net interest income) missing before imputation and received bank-mean or year-median values. These rows hold 35 of 727 crisis observations (4.8%); 17 of the rows belong to non-6419 entities (A2). | All bank-level models; crisis class slightly over-represented among fabricated rows | Medium | Require a minimum set of observed core items per bank-year (and per entity); drop rows below it | open |
| A17 | Sample | ORBIS extract | Parent and subsidiary entities can both be present with consolidated accounts (C2), counting the same balance sheet twice. Clear cases by name and identical total assets: ABN AMRO Bank NV / ABN AMRO Group NV (5 overlapping years, ratio 1.000), Montepio Geral Associacao Mutualista / Caixa Economica Montepio Geral (3 years), Bank of Ireland Group / Bank of Ireland, AIB Group / Allied Irish Banks, Ibercaja and Unicaja banks / their foundations (1 year each). A size-and-name heuristic cannot establish the full extent. | Bank-level models; weight of affected countries | Medium | Deduplicate with ORBIS ownership data (global ultimate owner / consolidation links), keeping one entity per group | open |
| A18 | Variable selection | 01, collinearity step | Missingness thresholds and the Belsley collinearity screening are computed on the full 2004-2017 panel, test years included, so variable selection uses information from after the forecast origins. | Real-time claim (design choices) | Low | Base selection on data up to the first test year, or disclose | open |
| A19 | Sample | 01 integrity check | Merger-like jumps (total assets more than tripling) are detected but not treated: 18 cases in 16 banks, 7 in 2004-2012. | Growth-type and size variables of those banks | Low | Flag break years; optionally split the series at the break | open |
| A20 | Variable construction | 01 | Ratios are built from raw levels before imputation, then levels and ratios are imputed separately, so imputed ratios need not match imputed levels. | Internal consistency of imputed rows | Low | Impute levels first and rebuild ratios, or impute ratios only | open |
| A21 | Variable construction | 01 | Equity-ratio bound allows values between 1 and 1.5 (equity above assets), which are not economically possible. | A few observations | Low | Bound at 1 | open |
| A22 | Missing data | 01 | Baseline thresholds are computed on 2004-2017, extended thresholds on the full 1996-2017 panel, so the two sets are not selected on the same window. | Comparability of baseline and extended sets | Low | Compute both on the same window | open |
| A15 | Documentation | thesis text | Growth rates described as log differences in places; code uses simple relative change. MLP SHAP method named DeepSHAP. | Method description | Low | Correct in paper | open |
