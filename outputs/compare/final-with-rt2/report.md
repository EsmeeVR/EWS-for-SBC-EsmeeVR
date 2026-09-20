# Results comparison: final-with-rt2

- Old: audit-2026-09 @ dd7a51c (git)
- New: C:\Users\esmvr\thesis-ews-final (folder)
- Claim checks on AUROC, means over matched test years; material change ≥ 0.01
- Claim checks use the six models; left out (still compared cell by cell): lr_no_dummies
- Generated 20-09-2026 14:28

## Verdict

- Cells compared: **594**, identical: **11**, changed: **583**
- Largest AUROC change in one cell: -0.5208 (12b macro_standalone decision_tree macro 2001)
- Cells where a threshold-based metric changed: 583
- Claim changes: **31**
  - 11a baseline_t1: order of configurations: micro > macro > integrated → micro > integrated > macro
  - 11a baseline_t1: integrated beats both: 0/6 → 1/6
  - 11a baseline_t1: best configuration for decision_tree: micro → integrated
  - 11a rt1: order of configurations: macro > integrated > micro → integrated > macro > micro
  - 11a rt1: integrated beats both: 2/6 → 3/6
  - 11a rt1: best configuration for xgboost: macro → integrated
  - 11b baseline_t1: integrated beats both: 2/6 → 3/6
  - 11b baseline_t1: best configuration for decision_tree: macro → integrated
  - 11b rt1: order of configurations: macro > integrated > micro → integrated > micro > macro
  - 11b rt1: integrated beats both: 1/6 → 3/6
  - 11b rt1: best configuration for lightgbm: macro → micro
  - 11b rt1: best configuration for logistic_regression: micro → integrated
  - 11b rt1: best configuration for random_forest: macro → integrated
  - 11c baseline_t1: order of configurations: micro > macro > integrated → micro > integrated > macro
  - 11c baseline_t1: integrated beats both: 0/6 → 1/6
  - 11c baseline_t1: best configuration for random_forest: micro → integrated
  - 11c rt1: integrated beats both: 3/6 → 4/6
  - 11c rt1: best configuration for lightgbm: macro → integrated
  - 11d baseline_t1: order of configurations: integrated > macro > micro → macro > integrated > micro
  - 11d baseline_t1: best configuration for lightgbm: macro → micro
  - 11d baseline_t1: best configuration for mlp: micro → macro
  - 11d rt1: best configuration for lightgbm: integrated → micro
  - 11d rt1: best configuration for random_forest: macro → integrated
  - rt2a rt2_2yr: best configuration for logistic_regression: integrated → micro
  - rt2a rt2_2yr: best configuration for random_forest: macro → integrated
  - rt2b rt2_2yr: order of configurations: integrated > micro > macro → micro > integrated > macro
  - rt2b rt2_2yr: integrated beats both: 4/6 → 2/6
  - rt2b rt2_2yr: best configuration for lightgbm: integrated → macro
  - rt2b rt2_2yr: best configuration for logistic_regression: integrated → micro
  - rt2b rt2_2yr: best configuration for random_forest: macro → integrated
  - rt2b rt2_2yr: best configuration for xgboost: integrated → macro
- Means over models that moved by 0.01 or more: **25**
  - 11a baseline_t1 integrated: 0.640 → 0.664 (+0.024)
  - 11a rt1 integrated: 0.895 → 0.884 (-0.011)
  - 11a rt1 macro: 0.900 → 0.883 (-0.016)
  - 11a rt1 micro: 0.885 → 0.865 (-0.020)
  - 11b baseline_t1 integrated: 0.725 → 0.751 (+0.026)
  - 11b baseline_t1 macro: 0.721 → 0.741 (+0.020)
  - 11b baseline_t1 micro: 0.691 → 0.714 (+0.023)
  - 11b rt1 macro: 0.913 → 0.875 (-0.038)
  - 11c baseline_t1 integrated: 0.657 → 0.689 (+0.032)
  - 11c baseline_t1 macro: 0.693 → 0.663 (-0.030)
  - 11c baseline_t1 micro: 0.802 → 0.747 (-0.055)
  - 11c rt1 macro: 0.869 → 0.855 (-0.014)
  - 11d baseline_t1 integrated: 0.801 → 0.755 (-0.047)
  - 11d baseline_t1 macro: 0.797 → 0.762 (-0.035)
  - 11d baseline_t1 micro: 0.756 → 0.738 (-0.018)
  - 11d rt1 integrated: 0.892 → 0.876 (-0.015)
  - 11d rt1 macro: 0.875 → 0.857 (-0.018)
  - 12b macro_standalone macro: 0.692 → 0.669 (-0.023)
  - 12b rt1 macro: 0.659 → 0.619 (-0.040)
  - 12b_gran rt1 macro: 0.810 → 0.827 (+0.018)
  - rt2a rt2_2yr integrated: 0.916 → 0.957 (+0.041)
  - rt2a rt2_2yr macro: 0.907 → 0.948 (+0.040)
  - rt2a rt2_2yr micro: 0.900 → 0.942 (+0.042)
  - rt2b rt2_2yr macro: 0.894 → 0.916 (+0.022)
  - rt2b rt2_2yr micro: 0.920 → 0.944 (+0.024)
- Structural differences: **20** (see below)

## Files read

| Spec | Old | New |
|---|---|---|
| 11a | results_11a_final.xlsx | results_11a_final.xlsx |
| 11b | results_11b_final.xlsx | results_11b_final.xlsx |
| 11c | results_11c_draft4.xlsx | results_11c_final.xlsx ⚠ draft vs final |
| 11d | results_11d_final.xlsx | results_11d_final.xlsx |
| 12a | results_12a_final.xlsx | results_12a_final.xlsx |
| 12a_gran | results_12a_isolate_gran_final.xlsx | results_12a_isolate_gran_final.xlsx |
| 12b | results_12b_final.xlsx | results_12b_final.xlsx |
| 12b_gran | results_12b_isolate_gran_final.xlsx | results_12b_isolate_gran_final.xlsx |
| rt2a | results_rt2a_final.xlsx | results_rt2a_final.xlsx |
| rt2b | results_rt2b_final.xlsx | results_rt2b_final.xlsx |

## Structural differences

- **11a**: column `threshold_from_year` added
- **11a**: column `test_optimal_threshold` added
- **11b**: column `threshold_from_year` added
- **11b**: column `test_optimal_threshold` added
- **11c**: column `threshold_from_year` added
- **11c**: column `test_optimal_threshold` added
- **11d**: column `threshold_from_year` added
- **11d**: column `test_optimal_threshold` added
- **12a**: column `threshold_from_year` added
- **12a**: column `test_optimal_threshold` added
- **12a_gran**: column `threshold_from_year` added
- **12a_gran**: column `test_optimal_threshold` added
- **12b**: column `threshold_from_year` added
- **12b**: column `test_optimal_threshold` added
- **12b_gran**: column `threshold_from_year` added
- **12b_gran**: column `test_optimal_threshold` added
- **rt2a**: column `threshold_from_year` added
- **rt2a**: column `test_optimal_threshold` added
- **rt2b**: column `threshold_from_year` added
- **rt2b**: column `test_optimal_threshold` added

## Per specification

### 11a · baseline_t1

Mean AUROC over models (test years 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.749 | 0.748 | -0.001 |
| macro | 0.652 | 0.642 | -0.010 |
| integrated | 0.640 | 0.664 | +0.024 |

Order of configurations: micro > macro > integrated  →  **micro > integrated > macro**
Integrated beats both: 0/6  →  **1/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | integrated ⚠ | +0.038 | -0.019 | +0.134 |
| lightgbm | micro | micro | +0.010 | +0.040 | -0.005 |
| logistic_regression | micro | micro | -0.033 | -0.002 | +0.001 |
| mlp | micro | micro | -0.042 | +0.032 | -0.025 |
| random_forest | micro | micro | +0.022 | -0.043 | -0.001 |
| xgboost | micro | micro | +0.001 | -0.067 | +0.036 |

### 11a · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.885 | 0.865 | -0.020 |
| macro | 0.900 | 0.883 | -0.016 |
| integrated | 0.895 | 0.884 | -0.011 |

Order of configurations: macro > integrated > micro  →  **integrated > macro > micro**
Integrated beats both: 2/6  →  **3/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | -0.034 | -0.065 | -0.007 |
| lightgbm | macro | macro | -0.014 | -0.029 | -0.038 |
| logistic_regression | macro | macro | -0.004 | +0.000 | -0.003 |
| mlp | integrated | integrated | -0.040 | -0.013 | -0.019 |
| random_forest | integrated | integrated | -0.007 | +0.003 | -0.012 |
| xgboost | macro | integrated ⚠ | -0.022 | +0.006 | +0.014 |

### 11b · baseline_t1

Mean AUROC over models (test years 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.691 | 0.714 | +0.023 |
| macro | 0.721 | 0.741 | +0.020 |
| integrated | 0.725 | 0.751 | +0.026 |

Order of configurations: integrated > macro > micro  (unchanged)
Integrated beats both: 2/6  →  **3/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | macro | integrated ⚠ | -0.008 | +0.048 | +0.077 |
| lightgbm | integrated | integrated | +0.018 | -0.016 | -0.059 |
| logistic_regression | micro | micro | -0.007 | +0.014 | +0.030 |
| mlp | micro | micro | +0.070 | +0.044 | +0.041 |
| random_forest | integrated | integrated | +0.031 | +0.041 | +0.046 |
| xgboost | macro | macro | +0.031 | -0.013 | +0.022 |

### 11b · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.879 | 0.885 | +0.006 |
| macro | 0.913 | 0.875 | -0.038 |
| integrated | 0.901 | 0.899 | -0.002 |

Order of configurations: macro > integrated > micro  →  **integrated > micro > macro**
Integrated beats both: 1/6  →  **3/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | +0.033 | -0.074 | -0.009 |
| lightgbm | macro | micro ⚠ | +0.007 | -0.118 | -0.027 |
| logistic_regression | micro | integrated ⚠ | -0.001 | +0.006 | +0.005 |
| mlp | integrated | integrated | -0.013 | -0.017 | -0.001 |
| random_forest | macro | integrated ⚠ | +0.001 | -0.008 | +0.014 |
| xgboost | macro | macro | +0.007 | -0.019 | +0.005 |

### 11c · baseline_t1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.802 | 0.747 | -0.055 |
| macro | 0.693 | 0.663 | -0.030 |
| integrated | 0.657 | 0.689 | +0.032 |

Order of configurations: micro > macro > integrated  →  **micro > integrated > macro**
Integrated beats both: 0/6  →  **1/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | -0.068 | -0.100 | +0.083 |
| lightgbm | micro | micro | -0.086 | -0.130 | +0.156 |
| logistic_regression | micro | micro | -0.015 | -0.048 | +0.001 |
| mlp | micro | micro | -0.060 | +0.014 | +0.010 |
| random_forest | micro | integrated ⚠ | -0.028 | +0.147 | +0.070 |
| xgboost | micro | micro | -0.073 | -0.060 | -0.126 |

### 11c · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.846 | 0.844 | -0.001 |
| macro | 0.869 | 0.855 | -0.014 |
| integrated | 0.875 | 0.870 | -0.005 |

Order of configurations: integrated > macro > micro  (unchanged)
Integrated beats both: 3/6  →  **4/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | -0.028 | -0.094 | -0.067 |
| lightgbm | macro | integrated ⚠ | +0.004 | -0.012 | +0.026 |
| logistic_regression | micro | micro | -0.000 | +0.005 | +0.004 |
| mlp | integrated | integrated | +0.011 | +0.006 | -0.004 |
| random_forest | integrated | integrated | +0.010 | +0.005 | +0.010 |
| xgboost | integrated | integrated | -0.004 | +0.006 | -0.003 |

### 11d · baseline_t1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.756 | 0.738 | -0.018 |
| macro | 0.797 | 0.762 | -0.035 |
| integrated | 0.801 | 0.755 | -0.047 |

Order of configurations: integrated > macro > micro  →  **macro > integrated > micro**
Integrated beats both: 1/6  (unchanged)

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | integrated | integrated | -0.024 | -0.097 | -0.071 |
| lightgbm | macro | micro ⚠ | -0.051 | -0.185 | -0.247 |
| logistic_regression | micro | micro | -0.011 | +0.011 | +0.010 |
| mlp | micro | macro ⚠ | +0.005 | +0.091 | +0.046 |
| random_forest | macro | macro | -0.011 | -0.005 | +0.003 |
| xgboost | macro | macro | -0.017 | -0.024 | -0.020 |

### 11d · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.842 | 0.844 | +0.002 |
| macro | 0.875 | 0.857 | -0.018 |
| integrated | 0.892 | 0.876 | -0.015 |

Order of configurations: integrated > macro > micro  (unchanged)
Integrated beats both: 3/6  (unchanged)

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | -0.032 | -0.100 | -0.114 |
| lightgbm | integrated | micro ⚠ | +0.020 | -0.063 | -0.015 |
| logistic_regression | micro | micro | +0.000 | +0.007 | +0.004 |
| mlp | integrated | integrated | -0.005 | +0.053 | +0.020 |
| random_forest | macro | integrated ⚠ | +0.009 | -0.008 | +0.006 |
| xgboost | integrated | integrated | +0.018 | +0.003 | +0.007 |

### 12a · macro_standalone

Mean AUROC over models (test years 2008, 2009, 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.619 | 0.623 | +0.003 |

### 12a · rt1

Mean AUROC over models (test years 2008, 2009, 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.598 | 0.597 | -0.001 |

### 12a_gran · macro_standalone

Mean AUROC over models (test years 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.675 | 0.666 | -0.009 |

### 12a_gran · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.761 | 0.761 | +0.000 |

### 12b · macro_standalone

Mean AUROC over models (test years 2001, 2002, 2008, 2009, 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.692 | 0.669 | -0.023 |

### 12b · rt1

Mean AUROC over models (test years 2001, 2002, 2008, 2009, 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.659 | 0.619 | -0.040 |

### 12b_gran · macro_standalone

Mean AUROC over models (test years 2010, 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.695 | 0.690 | -0.004 |

### 12b_gran · rt1

Mean AUROC over models (test years 2011, 2012):

| Configuration | Old | New | Δ |
|---|---|---|---|
| macro | 0.810 | 0.827 | +0.018 |

### rt2a · rt2_2yr

Mean AUROC over models (test years 2007):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.900 | 0.942 | +0.042 |
| macro | 0.907 | 0.948 | +0.040 |
| integrated | 0.916 | 0.957 | +0.041 |

Order of configurations: integrated > macro > micro  (unchanged)
Integrated beats both: 4/6  (unchanged)

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | +0.120 | +0.274 | +0.257 |
| lightgbm | integrated | integrated | +0.040 | -0.007 | -0.027 |
| logistic_regression | integrated | micro ⚠ | +0.002 | +0.004 | +0.000 |
| mlp | integrated | integrated | +0.027 | +0.021 | +0.013 |
| random_forest | macro | integrated ⚠ | +0.017 | -0.050 | +0.010 |
| xgboost | integrated | integrated | +0.047 | -0.001 | -0.007 |

### rt2b · rt2_2yr

Mean AUROC over models (test years 2007):

| Configuration | Old | New | Δ |
|---|---|---|---|
| micro | 0.920 | 0.944 | +0.024 |
| macro | 0.894 | 0.916 | +0.022 |
| integrated | 0.926 | 0.917 | -0.009 |

Order of configurations: integrated > micro > macro  →  **micro > integrated > macro**
Integrated beats both: 4/6  →  **2/6**

| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |
|---|---|---|---|---|---|
| decision_tree | micro | micro | +0.094 | +0.006 | -0.065 |
| lightgbm | integrated | macro ⚠ | +0.006 | +0.068 | -0.016 |
| logistic_regression | integrated | micro ⚠ | +0.004 | +0.010 | +0.002 |
| mlp | integrated | integrated | +0.018 | +0.056 | +0.012 |
| random_forest | macro | integrated ⚠ | +0.013 | -0.039 | -0.006 |
| xgboost | integrated | macro ⚠ | +0.010 | +0.029 | +0.019 |
