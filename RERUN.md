# Rerun with the audit fixes (branch `rerun-2026-09`)

This branch applies the fixes from [AUDIT.md](AUDIT.md) that have one clearly correct answer, runs
the whole pipeline once, and compares the result with the published run (`audit-2026-09`). The
principle agreed with Esmée: **the rerun fixes errors; it does not reopen decisions made with the
supervisors.** Design questions (what the paper measures) are left for the supervisors.

## How to run

From the repository root, with the Python that has the pinned `requirements.txt`:

```bash
python tools/run_pipeline.py                 # 01 -> 16 in order; about 2-3 hours
python tools/run_pipeline.py --tranquil      # separate A35 job, after the main run; about 1 hour
python tools/compare_runs.py --old audit-2026-09 --label all-fixes
```

`run_pipeline.py` first checks that the notebook kernel has the pinned pandas and scikit-learn,
stops at the first failing notebook (`--from <step>` resumes) and keeps an executed copy of every
notebook plus `run.log` in `outputs/run_logs/`. The comparison report lands in
`outputs/compare/all-fixes/`. Expected structural differences there: the 11c result file is a draft
on the old side and a final on the new side, and `all_results` gains the columns
`threshold_from_year` and `test_optimal_threshold` (A1).

**Runtime** (measured 18-09-2026 on this machine, 16 logical cores): one fully tuned window of six
models takes about 0.8 minutes (integrated set, 50 trials each), and most windows are untuned under
the skip rule (A13). One MLP KernelSHAP window at the new settings (A51) takes about 36 seconds.
Estimate: modelling under an hour, attribution 1 to 1.5 hours, aggregation a few minutes.

## What was fixed, per commit

| Commit | Audit IDs |
|---|---|
| `22e066b` prep | compare tool; verified AUDIT.md; README disclosure; WDI GDP (current LCU) sheet for A24 |
| `8f74058` shared module | A9 (verified: refits reproduce the published AUROC and AUPRC exactly, 11a/11b 54/54 baseline and 36/36 rt1, 12a and 12a_gran all cells) |
| `c6eb9cd` data | A2, A16, A17 (84 of 579 entities removed), A7/A45, A25, A24 (`nfa_gdp` replaces `nfa_g`), A23 (`credit_gap_missing`), A31, A32; A18 checked, not applied |
| `ab7ff9e` modelling | A1 (cut-off from the previous year's out-of-sample predictions, calibration window one training year shorter, never reported), A39, A37, A12, A11, A38, A40; A35 as a separate job |
| `1c53466` attribution, aggregation, inference | A4, A3, A6/A51, A50, A52, A33 (country-cluster bootstrap + Holm), A56, A57, A10, A39 (Brier not reported), A55, A54, A53, A44, A42, A58 |
| `ae12a4d` runner | `tools/run_pipeline.py`; three fixes found by a smoke run of 14-16 (NB14 output folder, repository-root paths in NB14/15, R&R cells skip when the vault folder is absent) |

## Deliberately unchanged

| ID | Why |
|---|---|
| A8, A19, A21, A22 | Decided or agreed earlier with the supervisors (see AUDIT.md, earlier-decision column) |
| A26 | FX-reserve breaks: a definition choice, disclosed |
| A13, A29, A30, A34, A36, A46 | Design questions for the supervisors; the rerun keeps the published design |
| A5 | LR attribution without country dummies: decided and disclosed |
| A43 | BIS_REER dropped at country level by a deliberate VIF > 10 decision |
| Figure 2 (lag effect) | Unmatched test windows by decision (05-08-2026); A53 applies to the other comparisons |
| rt2a / rt2b | Not rerun: invalid as designed (A46); NB14/15 read the published rt2 files |

## Not implemented

- **A20** (rebuild ratios from imputed levels): would require imputing levels that the agreed rule
  leaves unimputed, so it changes a decision.
- **A47 / A48 / A49** (Reinhart-Rogoff check): the R&R arms live in the vault, outside this
  repository. NB15 skips that figure and Appendix I when `Different Definition/Code_RR` is not next
  to the repository.
- **A14, A15, A27, A28, A41**: text or disclosure in the paper.

## Decisions needed

1. **Variable selection on the corrected sample** (A2/A16/A17). With the non-banks and empty entities
   removed, the agreed missingness thresholds would admit `cr_impchg` and `r_loans_dep` in the
   baseline set and four more variables in the extended set. The rerun keeps the published variable
   sets (`RESELECT_VARIABLES = False` in NB01), because re-selecting changes the specification.
2. **A18**: selecting variables on data up to 2009 only would change 2 (baseline) and 3 (extended)
   variable categories. Not applied.
3. **Multiple-testing correction** (A33). Tables mark significance by the unadjusted country-cluster
   bootstrap and carry a Holm column. On the published 11a predictions: DeLong 58% significant,
   bootstrap 14%, bootstrap with Holm 0%.
4. **A56**: the regime split's minimum-size rule counts bank-years. It now also reports crisis countries
   per regime (5 to 10) and a country-bootstrap interval, but the rule itself is unchanged.
5. **A46**: redesign or drop the pre-crisis check.

## Pre-registered reading (PROPOSED, for Esmée to confirm before the results are seen)

a. The supervisors' 2% rule: a change in mean AUROC over the six models of at most about 0.015 is
   immaterial.
b. The audit's refit prediction for the sample fixes: in the baseline set micro-only stays best in 6
   of 6 models; in the extended set integrated falls to about 0.70, just below macro-only.
c. Split the run into stages (by the commits above) only if the comparison shows a claim change, or
   a mean shift above 0.02, that (b) does not predict.

**Caveat, for transparency.** A quick check on the fixed data (18-09-2026) already refitted 11a and
11b with the *published* hyperparameters, so some extended-set information exists before this rule is
confirmed. Baseline: micro 0.750, macro 0.666, integrated 0.641; micro best in 6/6; integrated beats
both 0/6, as predicted. Extended: micro 0.698, macro 0.709, integrated 0.721; integrated beats both
3/6. That is 0.019 above the prediction in (b) and above macro-only, most likely from the changes (b)
did not include (`nfa_gdp`, `credit_gap_missing`, calendar lags, 2004 growth rates). The tuned run
will differ from these refits.
