# Pipeline audit before rerun (started 17-09-2026)

Purpose: find every issue in the pipeline before a single, final rerun for the journal paper.
Each issue records where it sits, what goes wrong, what it affects, how severe it is and the fix
planned for the rerun. Decisions on which fixes go into the rerun are taken with the supervisors
once the audit is complete.

## Summary (audit completed 17-09-2026)

All notebooks (01-05, 11a-d, 12a/b including granularity, rt2a/b, 13a-d, 14, 15, 16) and the Reinhart-Rogoff code in the original workspace were reviewed, with quantitative checks where a finding could change a result. **58 issues: 4 High, 25 Medium, 29 Low** (after verification on 18-09-2026, see below; A42 moved from High to Medium). Checks that passed are listed below the summary.

**The four High issues**

| ID | Issue | What it means |
|---|---|---|
| A29 | The test years (2010-2012) contain no crisis onsets; all positives are years 3-5 of crises that began in 2008 | Main results measure recognition of an ongoing crisis, not early warning |
| A46 | Pre-crisis relabelling (rt2) uses future information in its training labels, and labels are constant per country; a "copy the country's training label" rule scores AUROC 1.000 | The only anticipation test is not valid |
| A33 | DeLong tests treat bank-years as independent although labels are set per country | 58% of comparisons significant under DeLong, 14% under a country-cluster bootstrap |
| A1 | Classification thresholds are chosen on the test year | Miss rate, false alarm rate and loss L(alpha) are best-case values; AUROC/AUPRC unaffected |

**Themes**

1. *Evaluation design* (A1, A29, A34, A35, A46): what the out-of-sample tests measure differs from the early-warning question posed.
2. *Inference and comparisons* (A33, A42, A49, A53, A56): significance and several comparisons ignore that labels vary by country, or compare different units or windows.
3. *Sample and variables* (A2, A7, A16, A17, A23, A24): non-banks, bank-years with no observed balance sheet, parent/subsidiary duplicates, credit-gap coverage (30% missing in 2004-2012), a mis-specified NFA growth rate, row-based lags.
4. *Attribution* (A3-A6, A36, A50-A52): pair selection, hyperparameter file, LR without dummies, SHAP on mixed scales, imprecise KernelSHAP.
5. *Reproducibility* (A9-A12, A40, A47, A57, A58): duplicated code, draft/final file mix, broken paths, R&R check outside the repository.

**Consequences for the thesis claims** (as far as the audit can judge without a rerun)

- *H1, integration does not improve performance*: numbers will change with the fixes; the direction may hold for crisis-state classification, but significance statements do not stand as reported (A33) and the early-warning interpretation needs the redesign in A29.
- *Signal dilution of duplicated macro rows*: weaker than Figure 4 suggests. Scored like-for-like and without LR (as in the thesis), country level stays ahead in the baseline set (0.683 against 0.649, 4 of 5 models); in the extended set there is no clear difference (A42).
- *Credit-cycle extension recovers macro/integrated performance*: affected by credit-gap coverage (A23), the NFA growth definition (A24) and unmatched windows (A53).
- *H3, no micro-macro interaction*: every check found small interactions (including the missing pairs, A3), but the regime-split evidence rests on 5-10 crisis countries per regime (A56).
- *RT1 and rt2 robustness*: RT1 changes the training labels to the same kind as the test labels, a confound the check cannot rule out (A34); rt2 is not a valid anticipation test (A46).

**Refit check of A2, A16, A17, A23, A24 (17-09-2026).** Models refitted with the published final hyperparameters (no re-tuning), baseline_t1, lag-1; the unchanged refit reproduces the published AUROC exactly (54/54 cells in 11a and in 11b). Mean AUROC over models, micro | macro | integrated:

| Variant | 11a baseline | 11b extended |
|---|---|---|
| Published | 0.749 / 0.652 / 0.640 | 0.691 / 0.721 / 0.725 |
| Without empty balance sheets (A16, 77 rows) | 0.762 / 0.667 / 0.645 | 0.698 / 0.717 / 0.716 |
| Without group duplicate (A17, 3 rows) | 0.747 / 0.658 / 0.647 | 0.694 / 0.722 / 0.728 |
| Without non-banks (A2, 18 rows) | 0.756 / 0.647 / 0.640 | 0.699 / 0.726 / 0.705 |
| All three sample fixes | 0.763 / 0.657 / 0.643 | 0.698 / 0.722 / 0.702 |
| Without `nfa_g` (A24) | n/a | 0.691 / 0.725 / 0.711 |
| Without `credit_gap` (A23) | n/a | 0.691 / 0.691 / 0.715 |
| Without both | n/a | 0.691 / 0.710 / 0.708 |

Reading: in the baseline set, micro-only is the best configuration for all six models under every variant, and integrated stays below macro-only on average. In the extended set, the sample fixes move integrated from marginally above to below macro-only on average, and the per-model winner changes in up to one model (sample fixes) or three models (without `nfa_g`), with single cells moving by up to 0.14 AUROC. Model-level statements for the extended set are therefore fragile; the statement that integration is not systematically better holds in every variant. Removing the credit gap lowers macro-only by 0.030 on average, so it carries signal despite its coverage gap; most of the gain from extending the indicator set remains without the gap and NFA growth.

**Implication for the rerun**: the High issues are design choices, not only code bugs. The target definition and evaluation scheme (A29, A46), the inference method (A33) and threshold selection (A1) need to be decided first; sample and code fixes (A2, A7, A16, A17, A23, A24, A3-A6, A9) follow.

---

**Severity**
- **High**: can change a headline claim, or introduces look-ahead into reported out-of-sample results.
- **Medium**: affects secondary results (robustness, attribution) or reproducibility of a reported number.
- **Low**: no plausible effect on conclusions; documentation, hygiene or disclosure.

**Status**: `open` (found, fix not decided) · `decided` (fix agreed) · `fixed` (in code) · `disclose` (kept, documented only)

---

## Verification (18-09-2026)

Every issue was checked again against the code and data (not against the audit text), and against the
decisions recorded in the project notes, so that earlier decisions are not presented as new findings.

**Corrections to the first version**
- **A42** Granularity: the like-for-like comparison included logistic regression, whose bank-level version
  carries country dummies that the country-level model cannot have. Excluding it, as the thesis does,
  country level stays ahead in the baseline set (0.683 against 0.649, 4 of 5 models); in the extended set
  there is no clear difference (0.699 against 0.712). Severity High to Medium.
- **A5, A36** The LR dummy effect is 0.13-0.48 in mean AUROC across the four specifications (the notebooks'
  own `lr_dummy_comparison` sheets), not 0.07-0.32, which was the per-year range of `11b` only. Without
  dummies, micro-only is still LR's best configuration in the main specification (`11a`).
- **A15** Bank growth rates are log differences in both code and thesis. Only the DeepSHAP/KernelSHAP
  mismatch stands.
- **A34** That RT1 aligns training and test labels is verified (81 against 556 training positives for
  test 2011). That this alignment causes the gains is not tested; it is a confound, not an explanation.
- **A17** Total assets are identical for Bank of Ireland and AIB; 0.96-1.00 for ABN AMRO; 1.07-1.11 for
  Montepio (the association consolidates the bank).
- **A48** Ireland has rows in the R&R source but no label in any year.
- **A12** Not controlled, but same-machine refits reproduce the published AUROC exactly (54/54 cells).
- Precision: **A19** counts jumps across reporting gaps (16 in 14 banks for consecutive years); **A24**
  gives the long-panel count (38 of 178 in the panel the models use); **A43** the drop is a deliberate
  VIF > 10 decision; **A6** background rows are seeded by default, the coalition sampling is not.

**Confirmed exactly**: A1, A2, A7, A13, A16, A23, A25, A26, A29, A30, A33, A35, A37, A38, A39, A40, A46,
A50, A51, A52, A54, A55, A57, plus the code facts behind A18, A20, A21, A31, A32.

**Not re-verified**: A27, A45, A47, A56 (crisis countries per regime), A58. Also open: CLAUDE.md records
LightGBM +0.159 for the Figure 4 gap, the stored predictions give +0.125, so the figure may come from
an earlier file.

**Earlier decisions**: the new column in the register records where an issue was already decided,
known or disclosed. Where an earlier decision was to keep and disclose, the status is now `disclose`
(A4, A8, A19, A22).

---

## Audit progress

| Stage | Notebooks | Status |
|---|---|---|
| Data construction | 01, 02, 03, 04, 05 | done |
| Core modelling loop | 11a | done |
| Specification variants | 11b, 11c, 11d (diff against 11a) | done |
| Macro-only and granularity | 12a, 12b (both variants) | done |
| Pre-crisis relabelling | rt2a, rt2b | done |
| Crisis-definition check | R&R notebooks (vault `Different Definition/Code_RR`) | done |
| Attribution | 13a-13d | done |
| Aggregation and figures | 14, 15 | done |
| Descriptives | 16 | done |

---

## Checks passed

Things that were specifically checked and found to be correct.

| Stage | Check | Result |
|---|---|---|
| 02 | One-sided HP filter uses no future data | Correct: recursive filter keeps only the end point; no country-year in 2004-2012 has an interpolated credit value in its filter history |
| 02 | Credit gap in the combined panels uses the long 1995-2017 history | Correct |
| 02 | Log transforms applied after growth rates are computed | Correct |
| 03 | Laeven-Valencia start and end years parsed for all 25 countries (no episode lost to "ongoing" or footnote formats) | Correct: all 30 EU episodes parsed, 85 crisis country-years 1995-2017 |
| 03 | Macro and crisis merges preserve micro row counts; no unmatched country-years | Correct |
| 04 | Lags are built within bank and the t-2 panel is built from unlagged data | Correct (but see A7 on calendar gaps) |
| 05 | Country-level lags for the macro-only panels | Correct: country panels are complete, so a row shift equals a calendar-year lag |
| 13b/13d | Output files reflect the net foreign assets level drop | Correct: `FM.AST.NFRG.CN` absent from all attribution outputs |
| 11a-d | Stored predictions reproduce stored metrics | Correct: recomputed AUROC/AUPRC match exactly |
| 11a-d | Expanding-window split uses only earlier years for training | Correct |
| 11a-d | Imputer and scaler fitted on training data only, in both the outer loop and every Optuna trial | Correct |
| 11a-d | Inner validation years lie inside the training window | Correct |
| 11a-d | DeLong implementation (placement values, ties, variance of the difference) | Correct as an implementation of DeLong et al. (1988); the independence assumption is the problem (A33) |
| 11a-d | RT1 onset identification on bank-year rows | Correct: excludes the intended country-years |
| 11b-d | Differ from 11a only in data file, variable lists, drops and one removed diagnostic | Correct: code otherwise identical |
| 12 | Macro-only notebooks share the 11a training loop (split, tuning, imputation, class weights) | Correct: code identical apart from data and feature list |
| 12 gran | Granularity notebooks restrict to 2005-2017 so test years match the bank-level models | Correct |
| 12b gran | Assertion that the credit gap is one-sided before modelling | Present and correct |

---

## Issue register

| ID | Stage | Location | Issue | Affects | Severity | Planned fix | Status | Earlier decision or disclosure |
|---|---|---|---|---|---|---|---|---|
| A1 | Evaluation | 11a-d, 12, rt2 `run_model` | F1-optimal classification threshold is chosen on the **test** year (`precision_recall_curve(y_test, ...)`). Miss rate, false alarm rate, F1, recall, precision and loss L(alpha) are ex-post optimal. AUROC, AUPRC, DeLong unaffected. | All threshold-based tables and loss results | High | Choose the threshold without test labels: on inner validation predictions, or on the previous test year's out-of-sample predictions | open | Archive note said the loss table uses fixed thresholds; it does not, loss uses the test-year threshold |
| A2 | Sample | ORBIS extract, 01 | NACE 641 search admits 6411 (central banking): 34 of 52 Irish entities are non-banks with fully imputed balance sheets, plus two central banks elsewhere. About 2% of usable crisis observations. Test-side check: max AUROC change 0.008, ordering unchanged. | All bank-level results | Medium | Filter on 6419 and review remaining entities by name (decide on foreign banks with IE identifiers) | open | README known issue 6 (17-09-2026) |
| A3 | Attribution | 13a-d | Micro/macro split by name prefix counts `inc_nii`, `inc_op`, `cr_impchg` as macro; top-5 micro for H-statistic and PD pairs wrong in 11a and 11b. Check: missing pairs show no interaction. | H-statistic and PD pairs (11a, 11b); NB13 summaries | Medium | Use the explicit macro list from 14/15 | open | README known issue 5 (17-09-2026) |
| A4 | Attribution | 13b, 13d | Load draft `best_params_log.pkl` (pre HP-filter fix) instead of `_final`; differs for baseline 2011-2012. 11d micro shares move up to 7 pp. | SHAP, ALE, PD, H for 11b/11d baseline | Medium | Single source of hyperparameters; ideally store fitted models in 11 and reuse them in 13 | disclose | README known issue 7: kept and disclosed after discussion with the supervisor |
| A5 | Attribution | 13a-d | Logistic regression is refitted **without** country dummies (intentional), so LR attribution explains a model 0.13-0.48 AUROC weaker (mean per configuration) than the evaluated LR. | LR SHAP/ALE/H | Medium (design) | Decide: keep and disclose, or explain the evaluated model and report the dummies as one grouped block | open | README design note (17-09-2026) |
| A6 | Attribution | 13a-d | MLP SHAP uses unseeded `KernelExplainer` (thesis text says DeepSHAP; background rows are fixed by `shap.sample`'s default seed, the coalition sampling is not); MLP attributions vary up to 0.007 mean abs SHAP between runs. | MLP attribution; method description | Low | Seed the explainer; describe KernelSHAP correctly | open | |
| A7 | Feature engineering | 04 `lag_features` | Lag is `groupby(bank_id).shift(k)`: previous **row**, not calendar year t-k. Banks with gaps get older values. Lag-1: 46/4,073 rows (14/1,997 usable); lag-2: 68/3,539 (22/1,616). No look-ahead. | All bank-level models, marginally | Low | Lag on calendar year (merge on year - k) | open | |
| A8 | Imputation | 01 `panel_impute`, 02 | Within-bank interpolation and bank mean can use later observations of the same bank (under 0.4% of cells). | Strict real-time claim | Low | Forward-only fill or expanding bank mean; or disclose | disclose | Checked 23-06-2026 on the second supervisor's question (under 0.4% of cells); decided no rerun needed |
| A9 | Code structure | 11a-d, 12, rt2 | Objective, `run_model` and split copied across eight notebooks (README issue 1); already caused divergence (12b). | Risk of inconsistent fixes in the rerun | Low (risk: Medium) | Move shared code into one module before the rerun | open | README known issue 1 |
| A10 | Aggregation | 14, 15 | Read `_final` files except `11c` and `rt2a` (draft snapshots) (README issue 2). | Provenance of figures | Low | One result file per specification after rerun | open | README known issue 2: deliberate (11c and rt2a drafts equivalent to finals) |
| A11 | Macro-only | 12b | Last saved in failed state: imputer drops an all-missing column in one fold, column-name mismatch (README issue 3). Published results from an earlier successful run. | Reproducibility of 12b | Medium | Keep column alignment when the imputer drops a column | open | README known issue 3 |
| A12 | Reproducibility | 11-13 | Nondeterminism not controlled or measured: multithreaded XGBoost/LightGBM, no deterministic mode, unseeded KernelSHAP. In practice same-machine refits reproduce the published AUROC exactly (54/54 cells in `11a` and `11b`). | Exact reproduction of numbers | Low | Fix threads/deterministic flags and seeds; optionally repeat with several seeds to report variation | open | README note on rerun variation (17-09-2026) |
| A13 | Tuning | 11a-d | Tuning needs positives in both inner folds; otherwise library defaults (54 of 90 fits in 11a, 36 of 72 in 11d). | Absolute performance; comparability across windows | Medium (design) | Decide on inner validation design that contains positives (e.g. grouped or time-aware split with positive years) | open | Known and disclosed (thesis 3.4.1); '2010 is weak because untuned' tested and falsified |
| A14 | Data | 02 | Current data vintages, not real-time vintages; revisions are in the inputs. | Real-time claim | Low | Disclose | disclose | |
| A16 | Sample / imputation | 01 `panel_impute` | No bank-year or entity completeness rule. 77 of 1,997 usable lag-1 rows (3.9%) had all five core items (deposits, gross loans, equity, interbank liabilities, net interest income) missing before imputation and received bank-mean or year-median values. These rows hold 35 of 727 crisis observations (4.8%); 17 of the rows belong to non-6419 entities (A2). | All bank-level models; crisis class slightly over-represented among fabricated rows | Medium | Require a minimum set of observed core items per bank-year (and per entity); drop rows below it | open | README 'Found after the thesis' (18-09-2026) |
| A17 | Sample | ORBIS extract | Parent and subsidiary entities can both be present with consolidated accounts (C2), counting the same balance sheet twice. Clear cases by name and total assets: ABN AMRO Bank NV / ABN AMRO Group NV (5 overlapping years, total-asset ratio 0.96-1.00), Montepio Geral Associacao Mutualista / Caixa Economica Montepio Geral (3 years, ratio 1.07-1.11; the association consolidates the bank), Bank of Ireland Group / Bank of Ireland, AIB Group / Allied Irish Banks, Ibercaja and Unicaja banks / their foundations (1 year each). A size-and-name heuristic cannot establish the full extent. | Bank-level models; weight of affected countries | Medium | Deduplicate with ORBIS ownership data (global ultimate owner / consolidation links), keeping one entity per group | open | README 'Found after the thesis' (18-09-2026) |
| A18 | Variable selection | 01, collinearity step | Missingness thresholds and the Belsley collinearity screening are computed on the full 2004-2017 panel, test years included, so variable selection uses information from after the forecast origins. | Real-time claim (design choices) | Low | Base selection on data up to the first test year, or disclose | open | Thresholds set on the 2004-2017 panel with the supervisors (March 2026); the look-ahead angle is new |
| A19 | Sample | 01 integrity check | Merger-like jumps (total assets more than tripling) are detected but not treated: 18 cases in 16 banks, 7 in 2004-2012 (counting jumps across reporting gaps; 16 cases in 14 banks for consecutive years). | Growth-type and size variables of those banks | Low | Flag break years; optionally split the series at the break | disclose | Supervisor decision 19-03-2026: leave as is, mention as a limitation |
| A20 | Variable construction | 01 | Ratios are built from raw levels before imputation, then levels and ratios are imputed separately, so imputed ratios need not match imputed levels. | Internal consistency of imputed rows | Low | Impute levels first and rebuild ratios, or impute ratios only | open | |
| A21 | Variable construction | 01 | Equity-ratio bound allows values between 1 and 1.5 (equity above assets), which are not economically possible. | A few observations | Low | Bound at 1 | open | Cleaning rule (equity ratio < 0 or > 1.5) reviewed with the supervisors, March 2026 |
| A22 | Missing data | 01 | Baseline thresholds are computed on 2004-2017, extended thresholds on the full 1996-2017 panel, so the two sets are not selected on the same window. | Comparability of baseline and extended sets | Low | Compute both on the same window | disclose | By design: baseline 2004-2017 at 9%, extended 1995-2017 at 12%, agreed with the supervisors |
| A23 | Macro variables | 02 `add_credit_gap_hp` | The credit-to-GDP gap is missing in 68 of 225 country-years in 2004-2012 (30%): Croatia, Latvia and Lithuania for every year up to 2012, Estonia and Slovenia to 2008, Slovakia to 2010, all other countries in 2004-2005 (six-year warm-up on WDI data). Missing values are filled with the training-window median, so for these countries the extended set's key credit-cycle variable carries no information. Latvia is a crisis country. | Extended specifications (11b, 11d, 12b, rt2b); credit-cycle interpretation | Medium | Use a longer credit series (e.g. BIS total credit to the private non-financial sector) or a missingness indicator; at minimum report coverage | open | Follows from the agreed no-extrapolation rule (24-03-2026); higher credit-gap missingness accepted for the extended set |
| A24 | Macro variables | 02 `compute_derived` | Net foreign assets growth is a percentage change of a level that is negative for 11 countries. In 2004-2012, 41 of 197 observations in the long panel (38 of 178 in the panel the models use, where 2004 is missing, A25) have a negative base and 14 change sign, so the growth rate has a meaningless sign and size (e.g. Spain 2010: NFA falls from -64 to -122 bn, recorded as +90% growth). `nfa_g` ranks among the top features for some tree models. | Extended specifications; attribution | Medium | Use the change in NFA as a share of GDP | open | Keeping nfa_g and dropping the level was a deliberate collinearity decision; the negative-base problem is new |
| A25 | Macro variables | 02 | Derived growth rates for the 2004-2017 combined panels are computed on the 2004 slice, so all 2004 growth values are missing although 2003 levels exist (the credit gap is correctly taken from the long panel). After lagging these become missing 2005 features, filled with the training median. | Early training windows | Low | Compute all derived variables on the long panel, then slice | open | |
| A26 | Macro variables | 02 | Structural breaks in FX reserves are not treated, e.g. euro adoption (Slovenia 2007: -87%) and large jumps (Luxembourg 2008: +175%). | `fx_g` | Low | Flag euro-adoption years or scale reserves by GDP or imports | open | |
| A27 | Documentation | 02 vs thesis | The macro baseline set is selected as the variables with zero missingness in the window, not by the 5/9% thresholds described in the thesis. In the extended 2004-2017 panel the interpolation step for credit and NFA fills nothing (all gaps are at the edges). | Method description | Low | Describe what the code does | open | |
| A28 | Timing | 02, 03 | Annual year t-1 data are assumed to be available when predicting year t, without accounting for publication lags (annual accounts and WDI data for t-1 appear during year t, while crisis onset can fall early in t). | Real-time claim | Low | Disclose; optionally a two-year lag as the conservative case (already a robustness specification) | disclose | |
| A29 | Crisis label / evaluation design | 03 (duration labelling), 11a-d test years | **The out-of-sample test sets contain no crisis onsets.** All 16 onsets in the 2004-2017 sample fall in 2008. With duration labelling, every positive in the test years 2010, 2011 and 2012 (81, 81 and 90 bank-years) is year three to five of an episode that began in 2008. The positives in those years are exactly the ten countries whose episode Laeven and Valencia truncate at five years (end 2012, footnote 5/); the negatives include the six countries whose episode ended in 2009 plus countries without a crisis. The main results therefore measure how well models separate banks in countries with a long-lasting, ongoing crisis from the rest, not whether they anticipate a crisis. The only specification that evaluates anticipation is the pre-crisis relabelling (rt2), with a single test year (2007). Training data up to 2009 contain 232 onset bank-years out of 475 positives. | Interpretation of all main and robustness results; early-warning and forecasting claims | High | Decide the target: onset or pre-crisis window labelling (crisis years removed, as in rt2) as the main design, possibly with a leave-one-country-out or pooled evaluation to get more than one test year with events; at minimum reframe the main results as crisis-state classification | open | Noted in the thesis (¶399, Future Research) |
| A30 | Crisis label | 03 | End years of 10 of the 16 GFC episodes are the database's five-year truncation (footnote 5/), not an observed resolution. Labels for 2011-2012 in these countries depend on this convention. | Test-year labels (A29) | Medium | Discuss; sensitivity with truncation at a shorter horizon or end-of-intervention dates | open | Five-year truncation known and applied as the database convention |
| A31 | Documentation | 03 markdown | Stale notes describe an older labelling ("3164 crisis=1 (68%)"); current panel is 17.8% positive after lagging. | Readability | Low | Update notebook text | open | |
| A32 | Code hygiene | 05 | The unlagged `micro_ind_*` panels are written but not used downstream (micro-only models take columns from the integrated panel). Comments refer to "22 LV onset events", which matches no current labelling. | Readability | Low | Remove dead outputs and stale comments | open | |
| A33 | Inference | 11a-d `delong_test` | DeLong tests treat bank-years as independent, but within a test year the label is set per country (10 crisis countries out of 25) and macro features are identical within a country. For 11a baseline, integrated against micro-only and macro-only (36 model-year comparisons), 58% are significant at 5% under DeLong and 14% under a country-cluster bootstrap (2,000 draws of countries). No correction for multiple comparisons. | All significance statements (DeLong asterisks, "significantly outperforms") | High | Country-cluster bootstrap or permutation inference; report confidence intervals; adjust for multiple testing | open | |
| A34 | Robustness design | 11a-d RT1 variant | Excluding onset year and onset+1 removes all 2008 and 2009 positives, so RT1 training positives are only 2010 (and 2011) continuation years: 81 positives for test 2011 against 556 in baseline. Because the test positives are also continuation years (A29), RT1 aligns the training labels with the test labels. The large RT1 gains (+0.15 to +0.24 AUROC for macro and integrated) can therefore not be attributed to the removal of post-crisis bias: the alignment is a confound the check cannot rule out. Whether it causes the gains is not tested. | Interpretation of the RT1 robustness finding | Medium | Redesign together with A29; describe RT1 as a change in training label composition | open | Volatility and headroom explanations retracted 29-07-2026; decision: asymmetry stays unexplained, no new mechanism without a test |
| A35 | Evaluation design | 11a-d, 12 | Test years without crisis observations are skipped, so 2013-2017 (2,076 bank-years) are never evaluated. False alarms in tranquil years, the main operational cost of an early warning system, are not measured. | Operational relevance; false-alarm claims | Medium | Report false-alarm rates in tranquil years using thresholds fixed without test labels (A1) | open | Skipping 2013-2017 is necessary for AUROC (recorded as correct); the false-alarm angle is new |
| A36 | Model specification | 11a-d `feature_sets_lr` | Logistic regression includes country dummies in all three configurations, so "micro-only" and "macro-only" LR both contain country fixed effects. With persistent crisis labels (A29), dummies encode crisis membership: LR without dummies scores 0.13-0.48 lower in mean AUROC (0.05-0.49 per test year). Without dummies, micro-only remains LR's best configuration in `11a`; in `11b`, `11c` and `11d` the best configuration changes (integrated, macro, macro). LR is the best-performing model in the thesis. | H1 for LR; model ranking | Medium | Decide LR specification; report with and without dummies side by side | open | Known: LR dummy caveat in the thesis and the lr_dummy_comparison sheets |
| A37 | Tuning | 11a-d, 13 LightGBM | `subsample` is tuned but `subsample_freq` is left at 0, so LightGBM bagging is off and the parameter has no effect. One of LightGBM's six tuned dimensions is inert. | LightGBM tuning; stated tuning budget | Low | Set `subsample_freq=1` or drop the parameter | open | |
| A38 | H3 diagnostics | 11a | Threshold interaction terms (`integrated_h3_thr`) use medians of the whole panel, test years included. Coefficient inspection on the last window uses untuned C = 1.0. | H3 threshold-interaction diagnostic | Low | Per-window medians; tuned C | open | |
| A39 | Metrics | 11a-d `run_model` | Brier score is computed on class-weighted models whose probabilities are not calibrated, so it is not interpretable as a probability score. The imbalance ratio passed to inner tuning comes from the full training window, not the inner-training part. | Brier score; tuning detail | Low | Drop Brier or calibrate; use the inner ratio | open | |
| A40 | Provenance | 11a-d, README | Notebooks write the results parquet to `notebooks/results_11x/` while committed outputs live in `outputs/results/`; for 11c only draft files exist although the notebook writes `_final`. README lists test years 2010-2012 for 11c/11d, actual 2011-2012. | Reproducibility of file paths; documentation | Low | One output location; correct README | open | |
| A41 | Research design | whole project | Specification choices (variable drops, HP-filter correction, interaction forms, labelling) were revised after seeing results on the same three test years; there is no untouched hold-out period. | Out-of-sample credibility | Low | Disclose; for the rerun, fix the design before looking at test results | disclose | |
| A42 | Granularity comparison | 12a_gran, 12b_gran vs 11a/11b macro configuration | The "signal dilution" comparison scores country-level models on 25 countries per test year but bank-level models on several hundred bank rows, where countries weigh by their number of banks. Scored like-for-like (bank-level predictions averaged per country-year, same 25 units) and without LR, whose bank-level version carries country dummies (as in the thesis), country-level models stay ahead in the baseline set (0.683 against 0.649, 4 of 5 models) and there is no clear difference in the extended set (0.699 against 0.712). With LR included the first version of this audit reported 0.675 against 0.680 and 0.695 against 0.732. Per-model differences are noisy (SD about 0.12 on 25 units). The dilution interpretation is weaker than Figure 4 suggests and does not carry over to the extended set, but its baseline direction survives a like-for-like comparison. | Granularity finding and its policy implication | Medium | Evaluate both granularities on the same unit (country-year), with cluster-aware uncertainty; reframe the finding | open | The thesis already excluded LR from the granularity reading as a dummy artefact; the first audit version did not |
| A43 | Granularity comparison | 12b, 12b_gran | The country-level extended macro set removes `BIS_REER`, which the bank-level extended macro configuration (11b) keeps, so the extended comparison also differs in features. The drop is a deliberate VIF > 10 decision in both `12b` notebooks, not applied to `11b`. | Extended granularity comparison | Medium | Use identical feature lists | open | Deliberate VIF > 10 drop at country level |
| A44 | Macro-only design | 12a, 12b | Standalone macro-only models are tested on 2008-2012 (25 countries per year, including the 2008 onsets), the bank-level models on 2010-2012; AUROC on 25 units is reported without uncertainty. Comparisons between the two notebooks mix evaluation windows (the granularity notebooks correct this by restricting to 2005-2017). | Macro-only results and cross-notebook comparisons | Medium | Same test years for all comparisons; report intervals | open | Known; comparisons moved to the matched isolation runs (07-07-2026) |
| A45 | Data construction | 04 via 11 macro configuration | Macro features are not exactly identical across banks in the same country-year (predictions of macro-only models vary within a country by up to 0.33 in 2010) because of row-based lags (A7) and imputation. | "Duplicated macro rows" description; A42 | Low | Fixed by A7 | open | |
| A46 | Pre-crisis relabelling | rt2a, rt2b | Three problems make rt2 uninformative about anticipation. (1) **Look-ahead in training labels**: the 2006 training rows are positive because a crisis starts in 2008, which was not known at the 2007 forecast origin. (2) **Labels constant per country** in training (2006) and test (2007): every bank in the 16 countries with a 2008 onset is positive, every bank in the other 9 (BGR, CZE, EST, FIN, HRV, LTU, POL, ROU, SVK) negative, identically in both years. A rule that assigns each test bank its country's training label reaches AUROC 1.000; LR with country dummies also reaches 1.000, the other models 0.96-0.98 (decision tree 0.61). (3) Training covers 2005-2006 only (code comment says 2004-2006), no tuning, 84% positives in the test year. rt2 therefore measures recognition of the countries that later had a crisis. As the only specification aimed at anticipation (A29), this leaves the paper without a valid early-warning test. | rt2 results; any anticipation claim | High | Redesign: labels must use only information available at the forecast origin (e.g. pre-crisis windows for episodes that have already started, or pooled/leave-country-out evaluation over several crisis waves including the 1990s episodes in the macro panels) | open | |
| A47 | Crisis-definition check | vault `Different Definition/Code_RR` | The Reinhart-Rogoff comparison is not part of the replication repository and reads data from the old workspace (`../../Code/data_*`). Its modelling code is identical to 11a, so it inherits A1, A29, A33 and A36. | Reproducibility of a reported robustness result | Medium | Add to the repository with relative paths | open | |
| A48 | Crisis-definition check | `RR_source.xlsx` | The source is a pre-filtered file labelled Reinhart and Rogoff (2011) but it carries labels up to 2014 (the 2011 dataset ends earlier) and Ireland has rows but no label in any year, although R&R date Irish crises. Provenance of the 2011-2014 labels and the Irish gap is undocumented. | Validity of the R&R labels | Medium | Document the exact source and version (e.g. the updated Global Crises Data); check Ireland | open | |
| A49 | Crisis-definition check | `RR_vs_LV_comparison.md` | "Core findings survive" rests on counts of the best configuration per model (e.g. micro best in 4 of 6 models under both definitions) on 13 countries, without uncertainty; under R&R 71% of the matched sample is positive and test positives are again ongoing crisis years. | Strength of the robustness claim | Medium | Cluster-aware intervals; same redesign as A29 | open | Design constraints set 04-08-2026 (shared windows 2010-2012, AUROC only, L&V-isolated comparison) |
| A50 | Attribution | 13a-d | SHAP values are on different scales per model: log-odds for XGBoost, LightGBM (TreeExplainer raw output) and logistic regression (LinearExplainer), probability for random forest, decision tree and the MLP (KernelExplainer on `predict_proba`). Pooling across models (top-5 pair selection, ALE feature selection, aggregated figures) therefore weights models by scale: in 11a baseline, LightGBM, XGBoost and LR supply 91% of the pooled attribution mass. The thesis states all SHAP values share one unit (contribution to predicted probability). | Pooled SHAP rankings, H/PD pair and ALE feature selection, method description | Medium | Explain all models on one output scale, or pool within-model shares only | open | Known for shares: NB14/15 normalise within model (29-07-2026); the pooling in NB13 selections is new |
| A51 | Attribution | 13a-d MLP | KernelSHAP uses 50 background rows and `nsamples=50` coalition samples for 24-30 features, far below what KernelSHAP needs for stable estimates (default is 2M + 2048). MLP attributions are therefore imprecise, beyond the run-to-run noise in A6. | MLP attribution | Medium | Increase `nsamples` (or use DeepExplainer / permutation explainer) and seed it | open | |
| A52 | Attribution | 13a-d | Selection of H-statistic pairs and ALE features pools both variants (baseline and RT1) and all models; partial dependence and H use 300 training rows on a 10-point grid; the "temporal importance" heatmap plots the absolute value of the mean signed SHAP. | Robustness of interaction and ALE summaries | Low | Select per variant; larger grid; mean of absolute values | open | |
| A53 | Comparison design | 15 (Table E1, loss-delta figures), thesis text | Several cross-specification comparisons average each specification over its own test years (lag-1 specs 2010-2012, lag-2 and RT1 2011-2012). NB15 itself documents mean AUROC across models of 0.477 in 2010 against 0.764 and 0.799 in 2011 and 2012, a window bias of about 0.11 (up to 0.21) that exceeds the lag effects measured (0.03-0.07). A matched table (E2) exists, but E1-based statements and the loss-delta figures remain unmatched. That average models score at chance in 2010 also underlines A29. | Robustness comparisons; lag and extension effects | Medium | Report comparisons on matched windows only | open | Figure 2 deliberately unmatched with a note (decision 05-08-2026); matched version in Appendix E2; E1 known to be unmatched |
| A54 | Presentation | 15 asterisk rule | Significance markers require p < 0.05 in at least half of the windows: 2 of 3 for lag-1 specs but 1 of 2 for lag-2 and RT1 specs, so the rule is looser for the latter. Inherits A33. | Significance markers | Low | One rule; cluster-aware tests (A33) | open | Decided rule was a majority of windows; the code implements at least half |
| A55 | Presentation | 15 | Pooled ROC and PR curves concatenate predictions from differently trained yearly models, so the AUROC shown in figure legends differs from the mean-over-years AUROC in the tables. Macro-only figure titles state 2001-2017 while the panels start in 1999 (baseline) and 1995 (extended). `MODEL_LABELS` is redefined in later cells, so outputs depend on execution order. | Figures and labels | Low | Compute legend values as in tables; fix titles; remove hidden state | open | MODEL_LABELS redefinition known |
| A56 | H3 regime split | 14 section 12 | The regime split computes AUROC within macro regimes on bank-years, but labels are set per country: each regime holds only 5-10 distinct crisis countries (11a: 9 and 10; 11b: 6 and 9; 11d: 5 and 9), and the minimum-size rule counts bank-years (10 positives), not countries. The credit-gap regime drops Croatia, Lithuania, Latvia and Slovakia (missing gap, A23), including a crisis country. | H3 regime evidence | Medium | Country-level inference; report the number of crisis countries per regime | open | Low power disclosed in Limitations (n = 3) and ¶305; the country count per regime is new |
| A57 | Reproducibility | 14 | Three input paths do not exist in the repository (`11c/results_n50_trials_draft4.parquet`, `rt2a_draft.xlsx`, `rt2b_final.xlsx`), and rt2a and 11c are read from draft snapshots, so NB14 does not run from the committed state. | Figures produced by NB14 | Medium | Fix paths to the committed files | open | |
| A58 | Reproducibility | 16 | NB16 uses paths relative to the repository root while the README says to run notebooks from `notebooks/`; GFDD benchmark medians are hard-coded without the source files in the repository; the macro missingness column labelled "pre-imputation" reads a file written after treatment; `outputs/tables/crisis_volatility_ratios.csv` supports a mechanism that was later retracted. | Descriptive statistics provenance | Low | Consistent paths; add benchmark sources; relabel; mark or remove the retracted output | open | Volatility mechanism retracted 29-07-2026; the leftover output is the point |
| A15 | Documentation | thesis text | MLP SHAP method named DeepSHAP (thesis ¶207); code uses KernelSHAP. (Bank growth rates are log differences in code and thesis alike; the first version wrongly listed them.) | Method description | Low | Correct in paper | open | DeepSHAP was the original plan; text not updated when the code used KernelSHAP |
