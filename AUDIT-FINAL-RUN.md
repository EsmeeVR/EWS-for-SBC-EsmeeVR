# Audit of the final run (20-09-2026)

Checked: `thesis-ews`, branch `final-2026-09`, commit `009ac94`, plus the four extra seed
worktrees. This audit asks two questions: **was every issue from [AUDIT.md](AUDIT.md) actually
processed**, and **did the rerun introduce anything new**. Findings are verified against the
outputs and the notebook source, not against the audit text.

---

## 1. Was everything processed?

Every one of the 58 audit issues is accounted for in [RERUN.md](RERUN.md). Nothing was silently
dropped.

| Disposition | Count |
|---|---|
| Fixed in a commit | 36 |
| Deliberately unchanged (earlier decision or design question) | 14 |
| Not implemented, with a reason given | 9 |
| Listed as an open decision for the supervisors | 7 |
| **Unaccounted for** | **0** |

### Fixes verified in the outputs, not just in the document

| ID | Claim | How it was checked | Result |
|---|---|---|---|
| A1 | Threshold taken from the previous year, not the test year | `threshold_from_year` against `test_year` in 11a-d | 339 of 339 rows equal `test_year - 1`; **0** use the test year |
| A1 | No silent fallback to a test-optimal threshold | rows where no prior year exists | left **blank**, not filled in (see finding 2) |
| A33 | Significance from a country-cluster bootstrap, not DeLong | NB15 cell 22 aggregates `sig_boot`; the asterisk rule in cell 23 reads it | applied; the output column is confusingly still called `pct_sig` |
| A23 | `credit_gap_missing` excluded from every feature list | all 8 notebooks that read the extended data | dropped at load in all 8 |
| A24 | `nfa_gdp` replaces `nfa_g` | grep over the notebooks | 13 uses of `nfa_gdp`, 1 of `nfa_g` (in `rt2b`, see finding 1) |
| A2/A16/A17 | Sample fixes applied | `sample_composition.csv` old against new | panel 573 → 497 banks; lag-1 matrix 534 → 474 |
| A9 | Refits reproduce the published numbers | recorded in commit `8f74058` | 54/54 cells in 11a and 11b |

### Run integrity

- All five seed runs report `ALL DONE` with no failing step. The two interruptions on 19-09
  (kernel death at step 14, the slept laptop at 13d) were resumed and completed. The rt2 reruns of
  20-09 completed in every seed folder, and the result files now differ across seeds, as they
  should.
- Every result file is **complete**: no missing AUROC or AUPRC in any of the 10 specifications for
  the six reported models.
- The 16 "structural differences" flagged by `compare_runs.py` are the two new A1 columns
  (`threshold_from_year`, `test_optimal_threshold`) across 8 specifications. Benign.

---

## 2. What the rerun introduced or left behind

### Finding 1 — the pre-crisis results were from the old run (RESOLVED 20-09-2026)

**As found.** `rt2a` and `rt2b` were excluded from the pipeline on purpose (`tools/run_pipeline.py`;
RERUN.md, "Deliberately unchanged"), because the check is invalid as designed (A46). The result
files were **byte-identical** in all five seed folders and `compare_runs.py` reported **Δ +0.000 for
every cell**: they were the published files, carried over. `rt2b` still selected **`nfa_g`**, the
mis-specified growth rate A24 had replaced everywhere else, and both predated the sample fixes.

**What was done.** Rather than leave two runs in one document, the fixes were ported and both
notebooks rerun on the corrected data, in all five seed folders:

| Change | Why |
|---|---|
| `credit_gap_missing` dropped at load (rt2b) | `micro_cols` is built as "everything not listed as macro", so the flag would have been swept in as a *micro* feature |
| `nfa_g` → `nfa_gdp` (rt2b) | A24, consistent with every other specification |
| `crisis` excluded from `micro_cols` | it was being passed as a feature; constant 0 across all 3,188 rows used, so it was dead weight rather than leakage, but it does not belong in a feature list |
| threshold metrics left empty | A1: one test year with no evaluated predecessor means no honest cut-off exists. Same handling as the first RT1 window |
| falsification baseline added and reported | A46, see below |
| `rt2a`/`rt2b` added back to `run_pipeline.py` | they feed NB14/15, so they must run before them |

**The falsification baseline settles A46 empirically.** A rule that ignores every variable and
simply repeats the label its country carried in training scores:

| | AUROC | AUPRC |
|---|---|---|
| Country-label rule | **1.000** | **1.000** |
| Best model (LR, every configuration) | 1.000 | — |

1.000 in **all five seeds**, in both notebooks. No model beats it. The pre-crisis relabelling is
solvable from country identity alone, so these AUROCs measure that and not anticipation. The check
is now reported as a negative result, with the baseline in an `a46_falsification` sheet in each
workbook.

**Consequences for the thesis.** Re-running moved the pre-crisis numbers and added **8 claim
changes** (the comparison goes from 23 to 31). The one that matters: in the extended pre-crisis set
(`rt2b`), "integrated beats both" falls from **4 of 6 to 2 of 6**, and the ordering changes from
integrated > micro > macro to **micro > integrated > macro**. The thesis sentence that integration
outperforms the single-level configurations in most models in the pre-crisis specification no
longer holds.

### Finding 2 — under RT1 the threshold metrics now rest on a single year (new)

The A1 fix calibrates the cut-off on the previous year's out-of-sample predictions. Under RT1 the
onset year and the year after it are removed from training, so no calibration year is available for
2011 and the threshold metrics are correctly left blank rather than fitted on the test year.

| Specification | Test years | Years with miss rate / false alarm rate / loss |
|---|---|---|
| 11a, 11b, 11c, 11d — baseline | 2010-2012 (lag-1), 2011-2012 (lag-2) | all of them |
| 11a, 11b, 11c, 11d — RT1 | 2011, 2012 | **2012 only** |

This is the fix behaving correctly, but it changes what the loss section rests on. The thesis
compares RT1 loss against the baseline specifications in **paragraph 206, Figure 6 and Appendix G**
as though both sides had the same number of windows. On the new run the RT1 side is n = 1.
AUROC and AUPRC are unaffected.

### Finding 3 — most fits still use library defaults (unchanged, A13)

Tuning needs positives in both inner folds; where it cannot, the model is fitted on library
defaults. Counted from `best_params_log_final.pkl`:

| Spec | Fits | Tuned | Library defaults |
|---|---|---|---|
| 11a | 90 | 36 | **54 (60%)** |
| 11b | 90 | 36 | **54 (60%)** |
| 11c | 72 | 36 | 36 (50%) |
| 11d | 72 | 36 | 36 (50%) |

The untuned fits are spread evenly across the test years (18 per year), so this is systematic
rather than confined to one window. A13 is disclosed in thesis 3.4.1 and was deliberately left as a
design question, so this is not a regression. It is flagged here because Methodology describes a
50-trial Optuna search, and for the majority of fits no search took place.

### Finding 4 — AUDIT.md statuses are stale (documentation)

All 58 rows still read `open` or `disclose` in the Status column, although 36 were fixed. The real
record is the commit table in RERUN.md. Anyone reading AUDIT.md alone would conclude that nothing
was fixed. Worth correcting before the repository is published.

### Finding 5 — descriptive statistics were not regenerated against the new sample

The sample changed but the thesis's descriptive tables were written from the old one.

| | Old | New |
|---|---|---|
| Banks, contemporaneous panel | 573 | **497** |
| Bank-years, contemporaneous panel | 4646 | **4405** |
| Banks, lag-1 modelling matrix | 534 | **474** |
| Bank-years, lag-1 modelling matrix | 4073 | **3873** |
| Bank-years per macro state, lag-1 | 13.3 | **12.8** |

Thesis **Tables 3, 4, C1, C2, C3 and C4** and every sample count in Section 3 need rebuilding from
`outputs/tables/`. The "636 banks" in the abstract and in 3.1 describes the raw extract before
cleaning, so that figure still stands, but the cleaned counts quoted alongside it do not.

---

## 3. Seed sensitivity

Reporting a single seed is defensible at the level the thesis reports, and the numbers say so.

| Level | Seed 42 against the five-seed mean | Spread across the five seeds |
|---|---|---|
| Mean over the six models (what the thesis reports) | 0.54% on average, at most 1.95% | 2.49% on average, at most 10.77% |
| Individual model × configuration cell | 1.73% on average, at most 21.5% | 5.46% on average, at most 36.7% |

Seed 42 is higher than the five-seed mean in 68 of 168 cells (+1.93% on average) and lower in 72
(-2.21% on average). At the reported level it stays **inside the supervisors' own 2% rule**, so
seed 42 can be reported as the run of record.

What does **not** survive a seed change is the finer claims:

| Claim | Holds in all five seeds? |
|---|---|
| Micro best in the baseline set, both lags | **yes** |
| Integrated best under RT1, all four specifications | **yes** |
| Ordering in the baseline lag-1 set | no: seed 27 gives micro > macro > integrated |
| Ordering in the extended lag-1 set | no: seed 13 gives macro > integrated > micro |
| Ordering in the extended lag-2 set | no: three different orderings across the five seeds |
| "Integrated beats both" counts | no: e.g. 1-4 of 6 in the extended lag-1 set |

Logistic regression is effectively seed-independent (mean spread 0.001). The variation is
concentrated in DT (0.055), MLP (0.051) and LightGBM (0.041), whose worst single cell moves 0.245
AUROC.

---

## 4. Summary

Nothing in the audit list was missed, and the fixes that were claimed are present in the outputs.

**Resolved on 20-09-2026**

- **rt2a/rt2b** rerun on the corrected data in all five seed folders, with the A46 falsification
  baseline reported alongside. Every number in the repository now comes from one sample and one
  code version. The pre-crisis check is reported as a negative result.
- **RT1 loss metrics**: RT1 is dropped from the loss comparison and reported on AUROC and AUPRC
  only, since the threshold metrics there rest on a single window.

**Still open**

1. **Descriptive statistics**: rebuild Tables 3, 4 and C1-C4 from the new sample (573 → 497 banks).
2. **AUDIT.md statuses**: all 58 still read `open`; correct them before the repository is published.
3. **Design questions for the supervisors**, unchanged by the rerun: A29 (the test years contain no
   crisis onsets), A13 (60% of fits use library defaults), A33 (whether to report Holm alongside the
   country-cluster bootstrap).

Items 2 and 3 are documentation and disclosure rather than defects.
