"""Per-country-year scoring for ALL three configurations (extends NB15 cell 44 / A42, which did macro only).

Read-only on the repos: loads the stored final predictions of 11a (baseline, lag 1) and 11b (extended, lag 1)
for the five seeds, averages bank-level predictions per country-year exactly as NB15 cell 44 does, and
computes AUROC on bank rows and on country-years for micro, macro and integrated. Mean over 2010-2012 per
model, then over models (all six, and without LR).
"""
import pickle
from pathlib import Path
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(r"C:\Users\esmvr")
MAIN = ROOT / "thesis-ews-final"
SEEDS = {42: MAIN, 7: ROOT / "thesis-ews-final-s7", 13: ROOT / "thesis-ews-final-s13",
         27: ROOT / "thesis-ews-final-s27", 99: ROOT / "thesis-ews-final-s99"}
SPECS = {
    "Baseline set": ("11a", "base", "12a_gran"),
    "Extended set": ("11b", "robust", "12b_gran"),
}
MODELS = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm", "mlp"]
CONFIGS = ["micro", "macro", "integrated"]
YEARS = [2010, 2011, 2012]


def panel_index(kind):
    """Country and year of every row of the lag-1 estimation panel, in panel order (no bank_id).

    The panel itself (data/engineered, bank-level ORBIS data) is licensed and gitignored. When it is
    present, the country/year index is written to outputs/tables/ so the check can be rerun without it;
    when it is absent, that committed index is read instead. Row order matches the stored predictions.
    """
    idx = MAIN / f"outputs/tables/panel_index_{kind}.parquet"
    panel = MAIN / f"data/engineered/parquet_saves/me_merged_{kind}.parquet"
    if panel.exists():
        df = pd.read_parquet(panel, columns=["country_iso", "year"])
        df.to_parquet(idx, index=False)
        return df
    return pd.read_parquet(idx)

rows = []
for seed, repo in SEEDS.items():
    for set_name, (nb, panel, gran) in SPECS.items():
        ps = pickle.load(open(repo / f"outputs/results/{nb}/proba_store_final.pkl", "rb"))
        cty_ps = pickle.load(open(repo / f"outputs/results/{gran}/proba_store_final.pkl", "rb"))
        df = panel_index(panel)
        for mdl in MODELS:
            for yr in YEARS:
                c = df.loc[df["year"] == yr, "country_iso"].to_numpy()
                for cfg in CONFIGS:
                    k = (mdl, cfg, yr, "baseline_t1")
                    if k not in ps:
                        continue
                    y, p = ps[k]
                    assert len(c) == len(y), (seed, set_name, k)
                    cy = (pd.DataFrame({"c": c, "y": y, "p": p}).groupby("c")
                          .agg(y=("y", "max"), p=("p", "mean")))
                    rows.append({"seed": seed, "set": set_name, "model": mdl, "year": yr, "config": cfg,
                                 "bank_rows": roc_auc_score(y, p),
                                 "per_country": roc_auc_score(cy["y"], cy["p"]), "n_cty": len(cy)})
                kc = (mdl, "macro", yr, "macro_standalone")
                if kc in cty_ps:
                    yc, pc = cty_ps[kc]
                    rows.append({"seed": seed, "set": set_name, "model": mdl, "year": yr,
                                 "config": "country model", "bank_rows": float("nan"),
                                 "per_country": roc_auc_score(yc, pc), "n_cty": len(yc)})

r = pd.DataFrame(rows)
per_model = r.groupby(["seed", "set", "config", "model"])[["bank_rows", "per_country"]].mean()


def summarise(pm):
    return pm.groupby(["seed", "set", "config"]).mean().round(3)


allm = summarise(per_model)
nolr = summarise(per_model.drop(index="logistic_regression", level="model"))
pd.set_option("display.width", 200)
for name, t in [("ALL SIX MODELS", allm), ("WITHOUT LR", nolr)]:
    print(f"\n===== {name} =====")
    for unit in ["bank_rows", "per_country"]:
        print(f"-- {unit}")
        print(t[unit].unstack("config")[["micro", "macro", "integrated"] +
                                        (["country model"] if unit == "per_country" else [])].to_string())

out = MAIN / "outputs/tables/granularity_all_configs.xlsx"
with pd.ExcelWriter(out) as w:
    allm.to_excel(w, sheet_name="all_six")
    nolr.to_excel(w, sheet_name="without_LR")
    per_model.round(3).to_excel(w, sheet_name="per_model")
    r.to_excel(w, sheet_name="per_year", index=False)
print("saved", out, "| country counts per year:", sorted(r["n_cty"].unique()))
