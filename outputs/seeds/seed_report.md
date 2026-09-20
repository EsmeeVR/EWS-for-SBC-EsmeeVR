# Results over 5 seeds: 7, 13, 27, 42, 99

Metric: AUROC, mean over test years, then over the six models. A claim is robust when it holds in every seed.

## 11a · baseline_t1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.740 | 0.732 | 0.748 |
| macro | 0.653 | 0.642 | 0.671 |
| integrated | 0.667 | 0.658 | 0.677 |

Order of the means over seeds: **micro > integrated > macro**
Best configuration: **micro in every seed**
Orders seen across seeds: micro > integrated > macro; micro > macro > integrated
Integrated beats both: 0 to 1 of 6 models · micro best: 4 to 6 of 6 models

## 11a · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.865 | 0.864 | 0.866 |
| macro | 0.881 | 0.878 | 0.883 |
| integrated | 0.884 | 0.880 | 0.888 |

Order of the means over seeds: **integrated > macro > micro**
Best configuration: **integrated in every seed**
Orders seen across seeds: integrated > macro > micro
Integrated beats both: 2 to 3 of 6 models · micro best: 1 to 1 of 6 models

## 11b · baseline_t1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.713 | 0.710 | 0.718 |
| macro | 0.742 | 0.732 | 0.749 |
| integrated | 0.750 | 0.741 | 0.761 |

Order of the means over seeds: **integrated > macro > micro**
Best configuration: **varies across seeds** (13: macro, 27: integrated, 42: integrated, 7: integrated, 99: integrated)
Orders seen across seeds: integrated > macro > micro; macro > integrated > micro
Integrated beats both: 1 to 4 of 6 models · micro best: 1 to 2 of 6 models

## 11b · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.884 | 0.882 | 0.885 |
| macro | 0.878 | 0.875 | 0.879 |
| integrated | 0.897 | 0.895 | 0.899 |

Order of the means over seeds: **integrated > micro > macro**
Best configuration: **integrated in every seed**
Orders seen across seeds: integrated > micro > macro
Integrated beats both: 2 to 3 of 6 models · micro best: 2 to 2 of 6 models

## 11c · baseline_t1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.746 | 0.741 | 0.750 |
| macro | 0.664 | 0.648 | 0.680 |
| integrated | 0.703 | 0.686 | 0.729 |

Order of the means over seeds: **micro > integrated > macro**
Best configuration: **micro in every seed**
Orders seen across seeds: micro > integrated > macro
Integrated beats both: 1 to 2 of 6 models · micro best: 4 to 5 of 6 models

## 11c · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.842 | 0.840 | 0.844 |
| macro | 0.851 | 0.841 | 0.855 |
| integrated | 0.864 | 0.857 | 0.870 |

Order of the means over seeds: **integrated > macro > micro**
Best configuration: **integrated in every seed**
Orders seen across seeds: integrated > macro > micro; integrated > micro > macro
Integrated beats both: 4 to 4 of 6 models · micro best: 2 to 2 of 6 models

## 11d · baseline_t1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.741 | 0.730 | 0.751 |
| macro | 0.772 | 0.720 | 0.803 |
| integrated | 0.767 | 0.755 | 0.787 |

Order of the means over seeds: **macro > integrated > micro**
Best configuration: **varies across seeds** (13: integrated, 27: macro, 42: macro, 7: macro, 99: integrated)
Orders seen across seeds: integrated > macro > micro; integrated > micro > macro; macro > integrated > micro
Integrated beats both: 1 to 3 of 6 models · micro best: 1 to 3 of 6 models

## 11d · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| micro | 0.845 | 0.844 | 0.847 |
| macro | 0.855 | 0.844 | 0.862 |
| integrated | 0.878 | 0.874 | 0.883 |

Order of the means over seeds: **integrated > macro > micro**
Best configuration: **integrated in every seed**
Orders seen across seeds: integrated > macro > micro; integrated > micro > macro
Integrated beats both: 3 to 3 of 6 models · micro best: 3 to 3 of 6 models

## 12a · macro_standalone

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.626 | 0.613 | 0.646 |

## 12a · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.596 | 0.592 | 0.602 |

## 12a_gran · macro_standalone

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.657 | 0.645 | 0.666 |

## 12a_gran · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.758 | 0.751 | 0.761 |

## 12b · macro_standalone

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.674 | 0.665 | 0.688 |

## 12b · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.630 | 0.619 | 0.635 |

## 12b_gran · macro_standalone

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.687 | 0.679 | 0.691 |

## 12b_gran · rt1

| Configuration | Mean over seeds | Lowest | Highest |
|---|---|---|---|
| macro | 0.828 | 0.822 | 0.834 |
