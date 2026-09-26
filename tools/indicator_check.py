"""
Which bank-level indicators matter, and in which direction? Five-seed check for the policy section (26-09-2026).

Micro configuration (bank-level indicators only), baseline set, lag 1 (11a) and lag 2 (11c), variant
baseline_t1. Per seed and model:
  - importance: within-model share of mean |SHAP| (sums to 100% per model), averaged over the six models
  - direction: Spearman rho between the indicator's value and its SHAP value, and a quintile check that the
    profile does not reverse. Same rules as NB15 cell 61: a direction is 'reportable' when |median rho| > 0.30,
    at least 5 of 6 models agree in sign, and at least 80% of evaluable models are monotone.
Across seeds it reports the rank range, the share range, and in how many seeds the direction is reportable
with the same sign. Reads the local SHAP parquets and the lagged panels (both gitignored, bank-level); it
writes only aggregates: outputs/tables/indicator_check_micro.csv.
"""
from pathlib import Path
import numpy as np
import pandas as pd

H = Path(r"C:\Users\esmvr")
SEEDS = {42: H / "thesis-ews-final", 7: H / "thesis-ews-final-s7", 13: H / "thesis-ews-final-s13",
         27: H / "thesis-ews-final-s27", 99: H / "thesis-ews-final-s99"}
PANEL = {"11a": "me_merged_base", "11c": "me_merged_base_lag2"}
LABEL = {"r_cti": "Cost-to-income ratio", "x_loans_gross": "Gross loans", "x_ib_liab": "Interbank liabilities",
         "inc_nii": "Net interest income", "p_nim": "Net interest margin", "inc_op": "Operating income",
         "p_roa": "Return on assets", "p_roe": "Return on equity", "x_dep": "Customer deposits",
         "c_eqratio": "Equity ratio", "l_assets": "Log total assets", "l_loans": "Log gross loans",
         "r_loans_assets": "Loans-to-assets", "r_dep_liab": "Deposits-to-liabilities", "c_leverage": "Leverage"}


def spearman(x, y):
    xr, yr = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    return np.nan if xr.std() == 0 or yr.std() == 0 else float(np.corrcoef(xr, yr)[0, 1])


def monotone(v, s, n_bins=5, tol=0.10):
    d = pd.DataFrame({"v": v, "s": s}).dropna()
    if len(d) < 50 or d.s.nunique() < 2:
        return np.nan
    try:
        prof = d.groupby(pd.qcut(d.v, n_bins, duplicates="drop"), observed=True).s.mean().to_numpy()
    except ValueError:
        return np.nan
    if len(prof) < 3 or prof.max() == prof.min():
        return np.nan
    steps = np.diff(prof)
    big = steps[np.abs(steps) > tol * (prof.max() - prof.min())]
    return float(len(set(np.sign(big))) <= 1)


rows = []
for spec in ["11a", "11c"]:
    panel = pd.read_parquet(H / f"thesis-ews-final/data/engineered/parquet_saves/{PANEL[spec]}.parquet")
    for seed, repo in SEEDS.items():
        sv = pd.read_parquet(repo / f"outputs/attribution/outputs_{spec}/shap_values_{spec}.parquet")
        sv = sv[(sv.variant == "baseline_t1") & (sv.feature_set == "micro")]
        cols = [c for c in sv.columns if c.startswith("shap_") and sv[c].notna().any()]
        feats = [c[5:] for c in cols]
        m = sv.merge(panel[["bank_id", "year"] + feats], on=["bank_id", "year"], how="left", suffixes=("", "_v"))
        for f in feats:
            per_model = []
            for mod, g in m.groupby("model_name"):
                imp = g[cols].abs().mean()
                share = 100 * imp[f"shap_{f}"] / imp.sum()
                ok = g[f].notna() & g[f"shap_{f}"].notna()
                rho = spearman(g.loc[ok, f], g.loc[ok, f"shap_{f}"]) if ok.sum() >= 30 and g.loc[ok, f].nunique() >= 3 else np.nan
                per_model.append((share, rho, monotone(g[f], g[f"shap_{f}"])))
            share = np.mean([p[0] for p in per_model])
            rhos = np.array([p[1] for p in per_model], dtype=float)
            monos = np.array([p[2] for p in per_model], dtype=float)
            med = np.nanmedian(rhos)
            agree = max((rhos > 0).sum(), (rhos < 0).sum())
            n_eval = np.sum(~np.isnan(monos))
            shaped = n_eval > 0 and np.nansum(monos) / n_eval >= 0.80
            reportable = abs(med) > 0.30 and agree >= 5 and shaped
            rows.append(dict(spec=spec, seed=seed, feature=f, share=share, median_rho=med, agree=agree,
                             reportable=reportable, sign=int(np.sign(med)) if reportable else 0))

r = pd.DataFrame(rows)
r["rank"] = r.groupby(["spec", "seed"]).share.rank(ascending=False, method="min").astype(int)
summ = (r.groupby(["spec", "feature"])
          .agg(rank_min=("rank", "min"), rank_max=("rank", "max"), share_min=("share", "min"),
               share_max=("share", "max"), rho_median=("median_rho", "median"),
               seeds_up=("sign", lambda s: int((s > 0).sum())), seeds_down=("sign", lambda s: int((s < 0).sum())))
          .reset_index())
summ["indicator"] = summ.feature.map(LABEL)
summ["direction_all_seeds"] = np.where(summ.seeds_up == 5, "higher -> higher risk",
                               np.where(summ.seeds_down == 5, "higher -> lower risk", "not stable"))
summ = summ.sort_values(["spec", "rank_min"])
summ.to_csv(H / "thesis-ews-final/outputs/tables/indicator_check_micro.csv", index=False)
pd.set_option("display.width", 250)
print(summ[["spec", "indicator", "rank_min", "rank_max", "share_min", "share_max", "rho_median",
            "seeds_up", "seeds_down", "direction_all_seeds"]].round(2).to_string(index=False))
