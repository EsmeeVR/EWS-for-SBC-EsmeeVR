"""
Pre-crisis check, redesigned (PRECRISIS.md): leave-one-country-out backcast.

For each of the 25 countries, the six models are trained on the other 24 countries over 2006-2012
with the crisis-state label of the main design, and score the held-out country in every year
2006-2012. The scored country never enters training, so country identity cannot leak (audit A46).
This script only produces predictions; the decision rules are evaluated in a separate step.

Same indicators, drops, preprocessing (median imputation, scaling for LR/MLP), search spaces and
class weighting as 11a, taken from the seed's own ews_common.py so the seed is applied exactly as in
the main run. Differences, recorded in PRECRISIS.md before the run:
  - LR has no country dummies (a held-out country has no dummy of its own).
  - Tuning validates on held-out countries: within the 24 training countries, 4 crisis and
    2 non-crisis countries form the inner validation set, drawn per outer fold with the seed.

    python tools/precrisis_loco.py --root ../thesis-ews-final-s7 --seed 7 [--lag 1] [--trials 50]

Writes <root>/outputs/precrisis/lag<lag>/fold_<ISO>.parquet (one file per held-out country, so an
interrupted run resumes where it stopped) and best_params_<ISO>.json.
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

YEARS = range(2006, 2013)
ID_COLS = ["bank_id", "country_iso", "year"]
TARGET = "crisis"
MACRO_COLS = ["NGDP_RPCH", "NGDPD", "PCPIPCH", "LUR", "BCA_NGDPD", "BIS_REER", "RXF11FX_REVS", "reer_g", "fx_g"]
# 11a, cell 16: drops from the Belsley diagnostics (baseline set)
MICRO_DROPS = ["x_assets", "x_equity", "x_liab", "x_liab_equity", "x_loans_net", "exp_total"]
PANELS = {1: "me_merged_base.parquet", 2: "me_merged_base_lag2.parquet"}
N_INNER_CRISIS, N_INNER_CALM = 4, 2


def log(msg):
    print(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="repo worktree of the seed (its ews_common.py is used)")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--lag", type=int, default=1, choices=[1, 2])
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--only", nargs="*", help="held-out countries to run (default: all)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    sys.path.insert(0, str(root / "notebooks"))
    import optuna
    import ews_common as ec
    from sklearn.impute import SimpleImputer
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    df = pd.read_parquet(root / "data" / "engineered" / "parquet_saves" / PANELS[args.lag])
    df = df[df.year.isin(YEARS)].reset_index(drop=True)
    micro = [c for c in df.columns if c not in ID_COLS + [TARGET] + MACRO_COLS and c not in MICRO_DROPS]
    macro = list(MACRO_COLS)
    feature_sets = {"micro": micro, "macro": macro, "integrated": micro + macro}

    ever = df.groupby("country_iso")[TARGET].max()
    crisis_c = sorted(ever[ever == 1].index)
    calm_c = sorted(ever[ever == 0].index)
    out_dir = root / "outputs" / "precrisis" / f"lag{args.lag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"seed {args.seed}, lag {args.lag}, {len(df)} bank-years {min(YEARS)}-{max(YEARS)}, "
        f"{len(crisis_c)} crisis / {len(calm_c)} non-crisis countries, {len(micro)} micro, {len(macro)} macro")

    countries = args.only or sorted(ever.index)
    for k, held in enumerate(countries, 1):
        f_out = out_dir / f"fold_{held}.parquet"
        if f_out.exists():
            log(f"{held}: done already, skipped")
            continue
        t0 = time.time()
        train = df[df.country_iso != held]
        test = df[df.country_iso == held]

        # inner validation countries: stratified draw from the 24 training countries, fixed by seed and fold
        rng = np.random.default_rng([args.seed, k])
        tr_crisis = [c for c in crisis_c if c != held]
        tr_calm = [c for c in calm_c if c != held]
        val_c = set(rng.choice(tr_crisis, N_INNER_CRISIS, replace=False)) | \
            set(rng.choice(tr_calm, N_INNER_CALM, replace=False))
        inner_tr = train[~train.country_iso.isin(val_c)]
        inner_vl = train[train.country_iso.isin(val_c)]

        y_train = train[TARGET]
        n_neg_ratio = (y_train == 0).sum() / (y_train == 1).sum()
        inner_ratio = (inner_tr[TARGET] == 0).sum() / (inner_tr[TARGET] == 1).sum()

        rows, params_log = [], {}
        for fs, cols in feature_sets.items():
            for m in ec.MODEL_NAMES:
                obj = ec.get_objective(m, inner_tr[cols], inner_tr[TARGET], inner_vl[cols], inner_vl[TARGET], inner_ratio)
                study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=args.seed))
                study.optimize(obj, n_trials=args.trials, show_progress_bar=False)
                best = study.best_params
                params_log[f"{fs}|{m}"] = {"params": best, "inner_auroc": study.best_value}

                imputer = SimpleImputer(strategy="median", keep_empty_features=True)
                X_tr = imputer.fit_transform(train[cols])
                X_te = imputer.transform(test[cols])
                model, X_tr_f, X_te_f = ec.build_final_model(m, best, n_neg_ratio, X_tr, X_te, cols)
                if m == "mlp":
                    model.fit(X_tr_f, y_train, sample_weight=np.where(y_train == 1, n_neg_ratio, 1.0))
                else:
                    model.fit(X_tr_f, y_train)
                proba = model.predict_proba(X_te_f)[:, 1]
                rows.append(pd.DataFrame({
                    "seed": args.seed, "lag": args.lag, "held_out": held, "dataset": fs, "model": m,
                    "bank_id": test.bank_id.values, "year": test.year.values,
                    "crisis": test[TARGET].values, "crisis_country": int(ever[held]), "proba": proba,
                }))
        pd.concat(rows, ignore_index=True).to_parquet(f_out)
        (out_dir / f"best_params_{held}.json").write_text(json.dumps(
            {"inner_validation_countries": sorted(val_c), "models": params_log}, indent=1, default=str))
        log(f"{held} ({k}/{len(countries)}): {len(test)} bank-years scored in {(time.time() - t0) / 60:.1f} min")
    log("finished")


if __name__ == "__main__":
    main()
