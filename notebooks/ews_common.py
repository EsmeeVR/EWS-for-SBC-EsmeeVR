"""
Shared modelling code for the expanding-window notebooks (11a-11d, 12a/12b macro-only and granularity).

Until the 2026 rerun this code was copy-pasted into eight notebooks (audit A9, README known issue 1),
which is how 12b came to differ from its sister notebook. Keeping one copy here means a fix is made
once and applies to every specification.

The notebooks import from this file; they run from notebooks/, so a plain `import ews_common` works.
"""
import numpy as np
import pandas as pd
import optuna
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, confusion_matrix,
    accuracy_score, f1_score, recall_score, precision_score,
    average_precision_score, brier_score_loss,
)
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
import lightgbm as lgb
from scipy import stats as scipy_stats

MODEL_NAMES = ['logistic_regression', 'random_forest', 'xgboost', 'mlp', 'decision_tree', 'lightgbm']

# A1: `best_threshold` is the cut-off APPLIED in the test year, chosen on the previous year's
# out-of-sample predictions (`threshold_from_year`). `test_optimal_threshold` is the F1-optimal
# cut-off on the test year itself, kept only to show how optimistic the old metrics were.
RESULT_COLUMNS = [
    'model', 'variant', 'dataset', 'test_year',
    'auroc', 'auprc', 'brier', 'best_threshold', 'threshold_from_year', 'test_optimal_threshold',
    'tp', 'fp', 'fn', 'tn',
    'f1', 'recall', 'precision',
    'miss_rate', 'false_alarm_rate', 'accuracy',
    'loss_07', 'loss_08', 'loss_09',
]

# A12: gradient boosting is multithreaded, and thread scheduling can change floating-point sums
# between runs. A fixed thread count (and LightGBM's deterministic mode) makes reruns reproducible.
N_JOBS = 4

# MLP architectures are tuned as strings (Optuna categoricals only accept primitives) and decoded here
MLP_ARCHS = {'32': (32,), '64': (64,), '128': (128,), '64_32': (64, 32), '128_64': (128, 64)}


def get_country_col(df):
    # Different datasets use different column names - check both
    for col in ['country_iso', 'country_iso3']:
        if col in df.columns:
            return col
    # raise is OUTSIDE the loop - only fires if neither column is found
    raise ValueError(f"No country column found - expected 'country_iso' or 'country_iso3', got: {df.columns.tolist()}")


def expanding_window_split(df, min_train_years):
    years = sorted(df['year'].unique())
    splits = []

    for i, test_year in enumerate(years):
        if i < min_train_years:
            continue
        train = df[df['year'] < test_year]
        test = df[df['year'] == test_year]
        splits.append((train, test))
    return splits


def f1_optimal_threshold(y_true, y_proba):
    """Cut-off that maximises F1 on (y_true, y_proba); NaN when only one class is present."""
    y_true = np.asarray(y_true, dtype=int)
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        return np.nan
    # np.where evaluates both branches eagerly, so the divide runs even where denom=0.
    # errstate suppresses the warning; np.where then correctly replaces those positions with 0.0.
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    denom     = precisions + recalls
    with np.errstate(invalid='ignore', divide='ignore'):
        f1_scores = np.where(denom > 0, 2 * precisions * recalls / denom, 0.0)
    return float(thresholds[np.argmax(f1_scores[:-1])])


def run_model(model, X_train, y_train, X_test, y_test, metadata, sample_weight=None, return_proba=False,
              threshold=None, threshold_from_year=None):
    """Fit, predict and score one window.

    threshold : the alarm cut-off, chosen WITHOUT the test labels (A1: on the previous year's
        out-of-sample predictions). When None or NaN, the threshold-based metrics are NaN; the
        cut-off is never chosen on the test year. AUROC, AUPRC and Brier do not need a cut-off.
    """
    # sample_weight is only used by MLP -- LR/RF/XGBoost handle imbalance via class_weight/scale_pos_weight
    fit_kwargs = {'sample_weight': sample_weight} if sample_weight is not None else {}
    model.fit(X_train, y_train, **fit_kwargs)
    y_proba = model.predict_proba(X_test)[:, 1]

    auroc = roc_auc_score(y_test, y_proba)
    auprc = average_precision_score(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)

    result = {
        **metadata,
        'auroc':                  auroc,
        'auprc':                  auprc,
        'brier':                  brier,
        'best_threshold':         np.nan if threshold is None else threshold,
        'threshold_from_year':    threshold_from_year,
        # A1: the cut-off the old code used (F1-optimal on the test year), for comparison only
        'test_optimal_threshold': f1_optimal_threshold(y_test, y_proba),
    }

    if threshold is None or np.isnan(threshold):
        for k in ['tp', 'fp', 'fn', 'tn', 'f1', 'recall', 'precision', 'miss_rate',
                  'false_alarm_rate', 'accuracy', 'loss_07', 'loss_08', 'loss_09']:
            result[k] = np.nan
    else:
        y_pred = (y_proba >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        miss_rate        = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        result.update({
            'tp':               int(tp),
            'fp':               int(fp),
            'fn':               int(fn),
            'tn':               int(tn),
            'f1':               f1_score(y_test, y_pred, zero_division=0),
            'recall':           recall_score(y_test, y_pred, zero_division=0),
            'precision':        precision_score(y_test, y_pred, zero_division=0),
            'miss_rate':        miss_rate,
            'false_alarm_rate': false_alarm_rate,
            'accuracy':         accuracy_score(y_test, y_pred),
            'loss_07':          0.7 * miss_rate + 0.3 * false_alarm_rate,
            'loss_08':          0.8 * miss_rate + 0.2 * false_alarm_rate,
            'loss_09':          0.9 * miss_rate + 0.1 * false_alarm_rate,
        })

    # Only include raw probabilities when requested -- used by the main training loop
    # to populate proba_store for DeLong tests. Diagnostic loops (H3, no-dummies)
    # don't request them so their DataFrames stay clean.
    if return_proba:
        result['_y_proba'] = list(y_proba)
        result['_y_true']  = list(y_test)

    return result


def get_objective(model_name, X_tr_raw, y_tr, X_vl_raw, y_vl, n_neg_ratio):
    """
    Returns an Optuna objective function for the given model type.

    Imputation (and scaling for LR/MLP) are done inside each trial, fitted on inner_train only.
    This mirrors the full pipeline and prevents any leakage from inner_val into inner_train.
    Objective: maximise AUROC on the inner validation set.

    Parameters
    ----------
    X_tr_raw, X_vl_raw : pd.DataFrame - raw (pre-imputed) feature matrices
    y_tr, y_vl         : pd.Series   - crisis labels
    n_neg_ratio        : float        - n_neg / n_pos in the inner-training part (A39), for XGBoost/LightGBM/MLP
    """
    def objective(trial):
        # Fit imputer on inner_train only - same leakage rule as the outer loop.
        # A11: keep_empty_features keeps a column that is entirely missing in this fold (filled with 0),
        # so the matrix keeps one column per feature name; dropping it broke 12b.
        imputer = SimpleImputer(strategy='median', keep_empty_features=True)
        X_tr = imputer.fit_transform(X_tr_raw)
        X_vl = imputer.transform(X_vl_raw)

        if model_name == 'logistic_regression':
            C = trial.suggest_float('C', 1e-4, 10.0, log=True)
            # Scale inside trial - fit on inner_train only
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X_tr)
            X_vl = scaler.transform(X_vl)
            # L2 (Ridge): shrinks all coefficients toward zero but keeps all features.
            # Chosen over L1 because we want a consistent feature set across model classes
            # for cross-model SHAP comparison - L1 would zero out different features each window.
            # lbfgs is the recommended solver for L2; faster and more stable than saga for small-medium data.
            model = LogisticRegression(
                solver='lbfgs', C=C,
                max_iter=1000, class_weight='balanced', random_state=42
            )

        elif model_name == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=trial.suggest_int('n_estimators', 50, 500),
                max_depth=trial.suggest_int('max_depth', 3, 20),
                min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 20),
                max_features=trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.5]),
                class_weight='balanced', random_state=42,
            )

        elif model_name == 'xgboost':
            model = XGBClassifier(
                n_estimators=trial.suggest_int('n_estimators', 50, 500),
                max_depth=trial.suggest_int('max_depth', 2, 10),
                learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                subsample=trial.suggest_float('subsample', 0.5, 1.0),
                min_child_weight=trial.suggest_int('min_child_weight', 1, 10),
                scale_pos_weight=n_neg_ratio,
                eval_metric='logloss', random_state=42, n_jobs=N_JOBS  # A12
            )

        elif model_name == 'mlp':
            # MLP needs scaled inputs - gradient descent is sensitive to feature magnitude
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X_tr)
            X_vl = scaler.transform(X_vl)
            # suggest_categorical only accepts primitives - encode arch as string, decode to tuple
            arch = trial.suggest_categorical('hidden_layer_sizes', ['32', '64', '128', '64_32', '128_64'])
            # single-layer options (32/64/128): small to large capacity for limited panel data
            # two-layer funnels (64_32/128_64): standard progressive narrowing for tabular finance
            hidden_layer_sizes = MLP_ARCHS[arch]
            model = MLPClassifier(
                hidden_layer_sizes=hidden_layer_sizes,
                learning_rate_init=trial.suggest_float('learning_rate_init', 1e-4, 1e-2, log=True),
                alpha=trial.suggest_float('alpha', 1e-5, 1e-2, log=True),
                max_iter=5000,
                tol=1e-3,  # relaxed from default 1e-4 - suppresses warnings on flat loss landscapes without affecting AUROC
                random_state=42
            )

        elif model_name == 'decision_tree':
            model = DecisionTreeClassifier(
                max_depth=trial.suggest_int('max_depth', 2, 15),
                min_samples_leaf=trial.suggest_int('min_samples_leaf', 1, 30),
                class_weight='balanced', random_state=42
            )

        elif model_name == 'lightgbm':
            # Ensure consistent feature names for fit and predict
            # SimpleImputer may return a DataFrame in newer sklearn versions
            if not isinstance(X_tr, pd.DataFrame):
                X_tr = pd.DataFrame(X_tr, columns=X_tr_raw.columns)
                X_vl = pd.DataFrame(X_vl, columns=X_vl_raw.columns)
            model = lgb.LGBMClassifier(
                n_estimators=trial.suggest_int('n_estimators', 50, 500),
                max_depth=trial.suggest_int('max_depth', 2, 10),
                learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                num_leaves=trial.suggest_int('num_leaves', 15, 63),
                subsample=trial.suggest_float('subsample', 0.5, 1.0),
                subsample_freq=1,  # A37: LightGBM only bags rows when subsample_freq > 0; at 0 the tuned subsample had no effect
                min_child_samples=trial.suggest_int('min_child_samples', 5, 30),
                scale_pos_weight=n_neg_ratio,
                random_state=42, verbose=-1,
                n_jobs=N_JOBS, deterministic=True, force_row_wise=True  # A12: reproducible threading
            )

        # MLP has no class_weight parameter - pass sample_weight to handle class imbalance
        # All other models already handle imbalance via class_weight / scale_pos_weight
        if model_name == 'mlp':
            sw = np.where(y_tr == 1, n_neg_ratio, 1.0)
            model.fit(X_tr, y_tr, sample_weight=sw)
        else:
            model.fit(X_tr, y_tr)
        y_proba = model.predict_proba(X_vl)[:, 1]
        return roc_auc_score(y_vl, y_proba)

    return objective


def build_final_model(model_name, best_params, n_neg_ratio, X_train_imp, X_test_imp, cols):
    """Outer-loop model for one window: returns (model, X_train_final, X_test_final).

    Hyperparameters come from best_params; anything missing (an untuned window, see the skip rule
    in run_expanding_window) falls back to the defaults below. LR and MLP are scaled on the
    training window only; LightGBM gets DataFrames so feature names match at fit and predict.
    Also used by the attribution notebooks (13a-d), so the explained model is the evaluated one.
    """
    if model_name == 'logistic_regression':
        scaler        = StandardScaler()
        X_train_final = scaler.fit_transform(X_train_imp)
        X_test_final  = scaler.transform(X_test_imp)
        model = LogisticRegression(
            solver='lbfgs',
            C=best_params.get('C', 1.0),
            max_iter=1000, class_weight='balanced', random_state=42
        )

    elif model_name == 'random_forest':
        X_train_final = X_train_imp
        X_test_final  = X_test_imp
        model = RandomForestClassifier(
            n_estimators=best_params.get('n_estimators', 100),
            max_depth=best_params.get('max_depth', None),
            min_samples_leaf=best_params.get('min_samples_leaf', 1),
            max_features=best_params.get('max_features', 'sqrt'),
            class_weight='balanced', random_state=42
        )

    elif model_name == 'xgboost':
        X_train_final = X_train_imp
        X_test_final  = X_test_imp
        model = XGBClassifier(
            n_estimators=best_params.get('n_estimators', 100),
            max_depth=best_params.get('max_depth', 6),
            learning_rate=best_params.get('learning_rate', 0.1),
            subsample=best_params.get('subsample', 1.0),
            min_child_weight=best_params.get('min_child_weight', 1),
            scale_pos_weight=n_neg_ratio,
            eval_metric='logloss', random_state=42, n_jobs=N_JOBS  # A12
        )

    elif model_name == 'mlp':
        scaler        = StandardScaler()
        X_train_final = scaler.fit_transform(X_train_imp)
        X_test_final  = scaler.transform(X_test_imp)
        arch = best_params.get('hidden_layer_sizes', '128')
        hidden_layer_sizes = MLP_ARCHS.get(arch, (64,))
        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            learning_rate_init=best_params.get('learning_rate_init', 1e-3),
            alpha=best_params.get('alpha', 1e-4),
            max_iter=5000,
            tol=1e-3,  # relaxed from default 1e-4 - suppresses warnings on flat loss landscapes without affecting AUROC
            random_state=42
        )

    elif model_name == 'decision_tree':
        X_train_final = X_train_imp
        X_test_final  = X_test_imp
        model = DecisionTreeClassifier(
            max_depth=best_params.get('max_depth', 5),
            min_samples_leaf=best_params.get('min_samples_leaf', 5),
            class_weight='balanced', random_state=42
        )

    elif model_name == 'lightgbm':
        # Wrap as DataFrame: ensures consistent feature names for fit and predict
        X_train_final = pd.DataFrame(X_train_imp, columns=cols)
        X_test_final  = pd.DataFrame(X_test_imp,  columns=cols)
        model = lgb.LGBMClassifier(
            n_estimators=best_params.get('n_estimators', 100),
            max_depth=best_params.get('max_depth', 6),
            learning_rate=best_params.get('learning_rate', 0.1),
            num_leaves=best_params.get('num_leaves', 31),
            subsample=best_params.get('subsample', 1.0),
            subsample_freq=1,  # A37: without it the subsample parameter is inert
            min_child_samples=best_params.get('min_child_samples', 20),
            scale_pos_weight=n_neg_ratio,
            random_state=42, verbose=-1,
            n_jobs=N_JOBS, deterministic=True, force_row_wise=True  # A12
        )

    else:
        raise ValueError(f"unknown model_name {model_name!r}")

    return model, X_train_final, X_test_final


def rt1_filter(train_full, country_col, target):
    """RT1: drop the onset year (t) and t+1 of every crisis from the training window, per country.

    Onset years are country-years where crisis first switches to 1 (crisis=1 but crisis=0 in the
    preceding year for that country). Only those rows (and their t+1) are dropped; the rest of the
    crisis duration stays, and non-crisis countries keep all their data.
    """
    df_sorted   = train_full.sort_values([country_col, 'year'])
    prev_crisis = df_sorted.groupby(country_col)[target].shift(1).fillna(0)
    onset_mask  = (df_sorted[target] == 1) & (prev_crisis == 0)
    onset_rows  = df_sorted[onset_mask][[country_col, 'year']]
    exclude_set = (
        set(zip(onset_rows[country_col], onset_rows['year'])) |
        set(zip(onset_rows[country_col], onset_rows['year'] + 1))
    )
    return train_full[~train_full.apply(
        lambda r: (r[country_col], r['year']) in exclude_set, axis=1
    )]


def calibration_split(df, min_train_years):
    """The window just before the first test window, used only to calibrate the first alarm cut-off (A1).

    For test year t the cut-off is chosen on the out-of-sample predictions for t-1. The first test
    window has no evaluated predecessor, so one extra window is fitted for t-1. It trains on one year
    fewer than min_train_years (agreed with Esmee, 18-09-2026); its own scores are never reported.
    """
    return expanding_window_split(df, min_train_years - 1)[0]


def prepare_window(train_full, use_rt1, country_col, target):
    """RT1 filter, class ratios and the inner split for one window, or None when it cannot be fitted.

    Returns a dict with the (possibly filtered) training data, the full-window class ratio used in the
    outer refit, the inner-training class ratio used in tuning (A39), and the inner split.
    """
    if use_rt1:
        train = rt1_filter(train_full, country_col, target)
        if train[target].sum() == 0:
            return None
    else:
        train = train_full

    y_train     = train[target]
    n_pos       = (y_train == 1).sum()
    n_neg       = (y_train == 0).sum()
    n_neg_ratio = n_neg / n_pos if n_pos > 0 else 1.0

    # Inner split: last 2 years of the (possibly filtered) training window
    train_years     = sorted(train['year'].unique())
    inner_val_years = set(train_years[-2:])
    inner_train     = train[~train['year'].isin(inner_val_years)]
    inner_val       = train[train['year'].isin(inner_val_years)]
    y_inner_train   = inner_train[target]
    y_inner_val     = inner_val[target]

    # A39: tuning fits on inner_train only, so its class weights must come from inner_train too.
    # Taking them from the full window gave the tuned models a ratio they were never trained with.
    n_pos_inner = (y_inner_train == 1).sum()
    inner_ratio = (y_inner_train == 0).sum() / n_pos_inner if n_pos_inner > 0 else 1.0

    return dict(train=train, y_train=y_train, n_neg_ratio=n_neg_ratio, inner_ratio=inner_ratio,
                inner_train=inner_train, inner_val=inner_val,
                y_inner_train=y_inner_train, y_inner_val=y_inner_val,
                inner_val_years=inner_val_years,
                can_tune=y_inner_val.sum() > 0 and y_inner_train.sum() > 0)


def tune_params(model_name, w, cols, n_trials):
    """Optuna study on the inner split of window w; {} (library defaults) when it cannot be tuned (A13)."""
    if not w['can_tune']:
        return {}
    objective = get_objective(
        model_name,
        w['inner_train'][cols], w['y_inner_train'],
        w['inner_val'][cols],   w['y_inner_val'],
        w['inner_ratio'],
    )
    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params


def outer_model(model_name, best_params, w, test, cols):
    """Unfitted outer model and imputed matrices for window w: (model, X_train, X_test, sample_weight)."""
    imputer     = SimpleImputer(strategy='median', keep_empty_features=True)  # A11
    X_train_imp = imputer.fit_transform(w['train'][cols])
    X_test_imp  = imputer.transform(test[cols])
    model, X_train_final, X_test_final = build_final_model(
        model_name, best_params, w['n_neg_ratio'], X_train_imp, X_test_imp, cols)
    sw = np.where(w['y_train'] == 1, w['n_neg_ratio'], 1.0) if model_name == 'mlp' else None
    return model, X_train_final, X_test_final, sw


def fit_window_model(model_name, params, w, test, cols):
    """Fit the evaluated model of one window, for attribution (13a-d, audit A4).

    Same imputer, scaler and model settings as the training loop (outer_model), so the explained
    model is the evaluated one. Returns a dict with the fitted model, the matrices it was fitted and
    evaluated on, the imputed training matrix in raw units (for ALE) and the scaler (LR/MLP, else None).
    """
    model, X_train, X_test, sw = outer_model(model_name, params, w, test, cols)
    fit_kwargs = {'sample_weight': sw} if sw is not None else {}
    model.fit(X_train, w['y_train'], **fit_kwargs)
    imputer     = SimpleImputer(strategy='median', keep_empty_features=True)
    X_train_imp = imputer.fit_transform(w['train'][cols])
    # build_final_model scales LR/MLP inputs with a StandardScaler fitted on this same matrix;
    # refitting one here gives the identical transform, which ALE needs to work in raw units
    scaler = StandardScaler().fit(X_train_imp) if model_name in ('logistic_regression', 'mlp') else None
    return dict(model=model, X_train=X_train, X_test=X_test, X_train_imp=X_train_imp, scaler=scaler)


def run_expanding_window(splits, feature_sets, feature_sets_lr, variants, target, country_col,
                         n_trials=50, model_names=MODEL_NAMES, fixed_params=None, calibration=None):
    """The expanding-window training loop shared by 11a-d and 12a/b.

    For every variant, feature set, test window and model: optional RT1 filter, inner split
    (last two training years), Optuna tuning when both inner parts contain a crisis (otherwise
    library defaults: the skip rule, audit A13), outer refit on the full training window, and
    evaluation on the test year.

    A1: the alarm cut-off for test year t is the F1-optimal cut-off on the out-of-sample predictions
    for year t-1 by the same model, variant and feature set (the previous window). The test labels are
    never used to choose it. When there is no such predecessor (RT1 2011, whose 2010 window is skipped)
    the threshold-based metrics are NaN.

    calibration : a (train, test) split for the year before the first test window (calibration_split),
        fitted only to calibrate the first cut-off. Not reported.
    fixed_params : dict keyed (variant, dataset, test_year, model) -> params, optional.
        When given, tuning is skipped and these parameters are used. This reproduces a published
        run without re-tuning (the refit checks) and is how attribution reuses the evaluated models.

    Returns (results, best_params_log, proba_store, fi_store).
    """
    all_results     = []
    best_params_log = {}  # keyed by (variant, dataset, test_year, model)
    proba_store     = {}  # (model, dataset, test_year, variant) -> (y_true_list, y_proba_list)
    fi_store        = {}  # (model, dataset, test_year, variant) -> {feature: importance} (None for MLP)
    windows = ([(calibration, True)] if calibration is not None else []) + [(s, False) for s in splits]

    for variant_name, use_rt1 in variants:
        for dataset_name, feat_cols in feature_sets.items():
            lr_cols = feature_sets_lr[dataset_name]
            print(f"\n=== Variant: {variant_name} | Dataset: {dataset_name} ===")
            previous = {}  # model -> (year, y_true, y_proba) of the latest out-of-sample predictions

            for (train_full, test), is_calibration in windows:
                test_year = test['year'].values[0]
                y_test    = test[target]
                tag = " (calibration only)" if is_calibration else ""

                if y_test.sum() == 0:
                    print(f"  test={test_year}{tag} | SKIPPED - no crisis obs in test year")
                    continue

                w = prepare_window(train_full, use_rt1, country_col, target)
                if w is None:
                    print(f"  test={test_year}{tag} | RT1 SKIPPED - no crisis obs after onset filter")
                    continue
                print(f"  test={test_year}{tag} | val={sorted(w['inner_val_years'])} | crisis_in_val={w['can_tune']}")

                for model_name in model_names:
                    cols = lr_cols if model_name == 'logistic_regression' else feat_cols
                    key = (variant_name, dataset_name, test_year, model_name)

                    # --- Inner loop: Optuna tunes hyperparameters on inner_train/inner_val ---
                    if fixed_params is not None:
                        best_params = fixed_params.get(key, {})
                    else:
                        best_params = tune_params(model_name, w, cols, n_trials)

                    # --- A1: cut-off from the previous year's out-of-sample predictions ---
                    prev = previous.get(model_name)
                    if prev is not None and prev[0] == test_year - 1:
                        threshold, threshold_year = f1_optimal_threshold(prev[1], prev[2]), prev[0]
                    else:
                        threshold, threshold_year = np.nan, None

                    # --- Outer loop: refit on full (filtered) training window ---
                    model, X_train_final, X_test_final, sw = outer_model(model_name, best_params, w, test, cols)
                    result = run_model(
                        model, X_train_final, w['y_train'], X_test_final, y_test,
                        metadata={
                            'model':     model_name,
                            'variant':   variant_name,
                            'dataset':   dataset_name,
                            'test_year': test_year,
                        },
                        sample_weight=sw,
                        return_proba=True,
                        threshold=threshold,
                        threshold_from_year=threshold_year,
                    )
                    y_true_list, y_proba_list = result.pop('_y_true'), result.pop('_y_proba')
                    previous[model_name] = (test_year, y_true_list, y_proba_list)
                    if is_calibration:
                        continue  # calibration window: used for the next cut-off only, never reported

                    best_params_log[key] = best_params
                    # Store raw probabilities for significance tests and figures
                    proba_store[(model_name, dataset_name, test_year, variant_name)] = (y_true_list, y_proba_list)
                    # Tree models expose feature_importances_, LR exposes coef_
                    # MLP has no native importance (None here; use SHAP in NB13 if needed)
                    if hasattr(model, 'feature_importances_'):
                        fi_store[(model_name, dataset_name, test_year, variant_name)] = dict(zip(cols, model.feature_importances_))
                    elif hasattr(model, 'coef_'):
                        fi_store[(model_name, dataset_name, test_year, variant_name)] = dict(zip(cols, model.coef_[0]))
                    else:
                        fi_store[(model_name, dataset_name, test_year, variant_name)] = None
                    all_results.append(result)

    results = pd.DataFrame(all_results, columns=RESULT_COLUMNS) if all_results else pd.DataFrame(columns=RESULT_COLUMNS)
    if not all_results:
        print("\nWARNING: no results collected - every test year had zero crisis observations.")
    else:
        print(f"\nCompleted: {len(results)} model-window evaluations")
    return results, best_params_log, proba_store, fi_store


def run_tranquil_years(splits, feature_sets, feature_sets_lr, variants, target, country_col, proba_store,
                       n_trials=50, model_names=MODEL_NAMES):
    """A35 (separate analysis, outside the main results): false alarms in years without any crisis.

    Test years without crisis observations are skipped by the main loop because AUROC needs both
    classes. An early warning system is still judged on those years: every alarm there is false.
    Each tranquil year gets a model fitted exactly as in the main loop (tuning, skip rule, RT1 filter),
    and alarms are counted with a cut-off fixed in advance: the F1-optimal cut-off on the most recent
    evaluated year's out-of-sample predictions in proba_store (2012 for 2013). After the first tranquil
    year there is no newer year with crises to recalibrate on, so that cut-off is carried forward.

    Returns a DataFrame with one row per model x variant x dataset x tranquil year.
    """
    rows = []
    for variant_name, use_rt1 in variants:
        for dataset_name, feat_cols in feature_sets.items():
            lr_cols = feature_sets_lr[dataset_name]
            for (train_full, test) in splits:
                test_year = test['year'].values[0]
                if test[target].sum() > 0:
                    continue  # evaluated in the main loop
                w = prepare_window(train_full, use_rt1, country_col, target)
                if w is None:
                    continue
                for model_name in model_names:
                    cols = lr_cols if model_name == 'logistic_regression' else feat_cols
                    evaluated = sorted(y for (m, d, y, v) in proba_store
                                       if m == model_name and d == dataset_name and v == variant_name and y < test_year)
                    if not evaluated:
                        continue
                    last_year = evaluated[-1]
                    y_true_prev, y_proba_prev = proba_store[(model_name, dataset_name, last_year, variant_name)]
                    threshold = f1_optimal_threshold(y_true_prev, y_proba_prev)
                    if np.isnan(threshold):
                        continue
                    best_params = tune_params(model_name, w, cols, n_trials)
                    model, X_train_final, X_test_final, sw = outer_model(model_name, best_params, w, test, cols)
                    fit_kwargs = {'sample_weight': sw} if sw is not None else {}
                    model.fit(X_train_final, w['y_train'], **fit_kwargs)
                    y_proba = model.predict_proba(X_test_final)[:, 1]
                    alarms = int((y_proba >= threshold).sum())
                    rows.append({
                        'model': model_name, 'variant': variant_name, 'dataset': dataset_name,
                        'test_year': test_year, 'threshold': threshold, 'threshold_from_year': last_year,
                        'n_obs': len(y_proba), 'n_alarms': alarms, 'false_alarm_rate': alarms / len(y_proba),
                        'mean_proba': float(np.mean(y_proba)), 'tuned': bool(best_params),
                    })
                print(f"  tranquil {variant_name}/{dataset_name}/{test_year}: done")
    return pd.DataFrame(rows)


def _auroc_ranks(y_true, y_score):
    """AUROC from ranks (Mann-Whitney), fast enough to call thousands of times per comparison."""
    ranks = scipy_stats.rankdata(y_score)
    n_pos = y_true.sum()
    n_neg = len(y_true) - n_pos
    return (ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def cluster_bootstrap_auroc_diff(y_true, score_a, score_b, clusters, n_boot=2000, seed=42):
    """A33: country-cluster bootstrap for AUROC(a) - AUROC(b) on the same observations.

    DeLong treats every bank-year as an independent observation, but the crisis label and every macro
    indicator are set per country, so banks in one country are not independent. Here countries are drawn
    with replacement and all of a drawn country's observations enter the resample, which keeps that
    dependence intact. Draws without both classes are skipped.

    Returns dict(diff, ci_lo, ci_hi, p, n_valid): the observed difference, the 95% percentile interval,
    the two-sided p-value (twice the smaller share of draws on either side of zero) and the number of
    usable draws. NaN when fewer than 2 countries or fewer than 100 usable draws.
    """
    y_true  = np.asarray(y_true, dtype=int)
    score_a = np.asarray(score_a, dtype=float)
    score_b = np.asarray(score_b, dtype=float)
    clusters = np.asarray(clusters)
    out = dict(diff=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan, n_valid=0)
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        return out
    out['diff'] = _auroc_ranks(y_true, score_a) - _auroc_ranks(y_true, score_b)

    groups = [np.flatnonzero(clusters == c) for c in pd.unique(clusters)]
    if len(groups) < 2:
        return out
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])
        yb = y_true[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        diffs.append(_auroc_ranks(yb, score_a[idx]) - _auroc_ranks(yb, score_b[idx]))
    diffs = np.asarray(diffs)
    out['n_valid'] = len(diffs)
    if len(diffs) < 100:
        return out
    out['ci_lo'], out['ci_hi'] = np.percentile(diffs, [2.5, 97.5])
    out['p'] = min(1.0, 2 * min((diffs <= 0).mean(), (diffs >= 0).mean()))
    return out


def holm_adjust(pvals):
    """Holm step-down adjustment of a set of p-values (NaN stays NaN)."""
    p = np.asarray(pvals, dtype=float)
    adj = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    order = np.argsort(p[ok])
    m = ok.sum()
    running = 0.0
    vals = np.empty(m)
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[ok][i])
        vals[i] = min(1.0, running)
    adj[ok] = vals
    return adj


def add_cluster_bootstrap(delong_df, proba_store, clusters_by_year, n_boot=2000, seed=42):
    """A33: add country-cluster bootstrap columns to the DeLong table built in 11a-d.

    clusters_by_year : {test_year: array of country codes}, in the row order of the test set, which is
        the order of the lists in proba_store (the test set is df[year == test_year], no row drops).
    Adds diff_auroc, ci_lo, ci_hi, p_boot, p_boot_holm (Holm within each comparison and variant, across
    models and test years) and sig_boot (p_boot < 0.05). DeLong's z, p and sig_05 are kept alongside.
    """
    rows = []
    for _, r in delong_df.iterrows():
        comp, variant, model, year = r['comparison'], r['variant'], r['model'], r['test_year']
        if comp.startswith('integrated_vs_'):
            key_a = (model, 'integrated', year, variant)
            key_b = (model, comp[len('integrated_vs_'):], year, variant)
        else:  # baseline_vs_rt1_<dataset>: same test set, baseline scores against rt1 scores
            ds = comp[len('baseline_vs_rt1_'):]
            key_a, key_b = (model, ds, year, 'baseline_t1'), (model, ds, year, 'rt1')
        y_true, s_a = proba_store[key_a]
        _,      s_b = proba_store[key_b]
        rows.append(cluster_bootstrap_auroc_diff(y_true, s_a, s_b, clusters_by_year[year], n_boot, seed))
    boot = pd.DataFrame(rows, index=delong_df.index).rename(columns={'diff': 'diff_auroc', 'p': 'p_boot'})
    out = pd.concat([delong_df, boot.drop(columns='n_valid')], axis=1)
    out['p_boot_holm'] = np.nan
    for _, idx in out.groupby(['comparison', 'variant']).groups.items():
        out.loc[idx, 'p_boot_holm'] = holm_adjust(out.loc[idx, 'p_boot'])
    out['sig_boot'] = out['p_boot'] < 0.05
    return out


def delong_test(y_true, y_score_a, y_score_b):
    """
    DeLong et al. (1988) non-parametric test for comparing two AUROCs.
    Returns (z, p): positive z means AUROC_a > AUROC_b; p is two-sided.
    Returns (nan, nan) when fewer than 2 positives or 2 negatives exist
    (covariance cannot be estimated with a single observation).

    Method: placement values (structural components) measure how well each
    positive score outranks each negative score. Their covariance across the
    two score vectors gives the variance of the AUROC difference - no parametric
    assumptions about score distributions needed.
    """
    y_true    = np.asarray(y_true,    dtype=int)
    y_score_a = np.asarray(y_score_a, dtype=float)
    y_score_b = np.asarray(y_score_b, dtype=float)

    pos = y_true == 1
    neg = y_true == 0
    m   = pos.sum()  # number of positives
    n   = neg.sum()  # number of negatives

    if m < 2 or n < 2:
        return np.nan, np.nan

    def placements(scores):
        s_pos = scores[pos]
        s_neg = scores[neg]
        # V10[i]: fraction of negatives outranked by positive i (ties split 50/50)
        V10 = np.array([(p > s_neg).mean() + 0.5 * (p == s_neg).mean() for p in s_pos])
        # V01[j]: fraction of positives that outrank negative j (ties split 50/50)
        V01 = np.array([(s_pos > nj).mean() + 0.5 * (s_pos == nj).mean() for nj in s_neg])
        return V10, V01

    V10_a, V01_a = placements(y_score_a)
    V10_b, V01_b = placements(y_score_b)

    auc_a = V10_a.mean()
    auc_b = V10_b.mean()

    # 2x2 covariance matrices of the placement value pairs
    S10 = np.cov(np.vstack([V10_a, V10_b]), ddof=1)
    S01 = np.cov(np.vstack([V01_a, V01_b]), ddof=1)
    S   = S10 / m + S01 / n  # covariance matrix of (AUC_a, AUC_b)

    # Var(AUC_a - AUC_b) = S[0,0] + S[1,1] - 2*S[0,1]
    var_diff = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    if var_diff <= 0:
        return np.nan, np.nan

    z = (auc_a - auc_b) / np.sqrt(var_diff)
    p = 2 * scipy_stats.norm.sf(abs(z))
    return float(z), float(p)
