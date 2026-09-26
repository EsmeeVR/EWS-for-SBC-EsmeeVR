"""Region benchmark on the test years 2010-2012, at country-year level (read-only on the repos).

Region rule as in tools/precrisis_evaluate.py: score 1 for the EU-14 WEST set, 0 otherwise.
Compared with the equal-weight per-country average of bank-level predictions for micro/macro/integrated
(11a baseline, 11b extended, lag 1, five seeds). Also reports AUROC within West and within CEE.
"""
import pickle
from pathlib import Path
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(r"C:\Users\esmvr")
MAIN = ROOT / "thesis-ews-final"
SEEDS = {42: MAIN, 7: ROOT / "thesis-ews-final-s7", 13: ROOT / "thesis-ews-final-s13",
         27: ROOT / "thesis-ews-final-s27", 99: ROOT / "thesis-ews-final-s99"}
SPECS = {"Baseline set": ("11a", "base"), "Extended set": ("11b", "robust")}
WEST = {"AUT", "BEL", "DNK", "FIN", "FRA", "DEU", "GRC", "IRL", "ITA", "LUX", "NLD", "PRT", "ESP", "SWE"}
MODELS = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm", "mlp"]
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


def auc(y, s):
    return roc_auc_score(y, s) if pd.Series(y).nunique() == 2 else float("nan")


# labels per country-year and the region rule
df = panel_index("base")
ps = pickle.load(open(MAIN / "outputs/results/11a/proba_store_final.pkl", "rb"))
print("Crisis countries per test year (West / CEE):")
region_rows = []
for yr in YEARS:
    c = df.loc[df.year == yr, "country_iso"].to_numpy()
    y, _ = ps[("logistic_regression", "micro", yr, "baseline_t1")]
    lab = pd.DataFrame({"c": c, "y": y}).groupby("c").y.max()
    west = lab.index.isin(WEST)
    print(f"  {yr}: {lab.sum()} of {len(lab)} in crisis | West {lab[west].sum()}/{west.sum()}, "
          f"CEE {lab[~west].sum()}/{(~west).sum()}")
    region_rows.append(auc(lab.values, west.astype(int)))
print(f"Region rule AUROC per year {[round(a, 3) for a in region_rows]}, mean {sum(region_rows) / 3:.3f}\n")

rows = []
for seed, repo in SEEDS.items():
    for set_name, (nb, panel) in SPECS.items():
        d = panel_index(panel)
        store = pickle.load(open(repo / f"outputs/results/{nb}/proba_store_final.pkl", "rb"))
        for mdl in MODELS:
            for cfg in ["micro", "macro", "integrated"]:
                for yr in YEARS:
                    y, p = store[(mdl, cfg, yr, "baseline_t1")]
                    c = d.loc[d.year == yr, "country_iso"].to_numpy()
                    assert len(c) == len(y)
                    cy = pd.DataFrame({"c": c, "y": y, "p": p}).groupby("c").agg(y=("y", "max"), p=("p", "mean"))
                    w = cy.index.isin(WEST)
                    rows.append(dict(seed=seed, set=set_name, model=mdl, config=cfg, year=yr,
                                     all=auc(cy.y, cy.p), west=auc(cy.y[w], cy.p[w]), cee=auc(cy.y[~w], cy.p[~w])))
r = pd.DataFrame(rows)
pm = r.groupby(["seed", "set", "config", "model"])[["all", "west", "cee"]].mean()
for label, t in [("ALL SIX MODELS", pm), ("WITHOUT LR", pm.drop(index="logistic_regression", level="model"))]:
    s = t.groupby(["set", "config", "seed"]).mean()
    rng = s.groupby(["set", "config"]).agg(["min", "max"]).round(3)
    print(f"===== {label}: range over five seeds (mean over models and 2010-2012) =====")
    print(rng.to_string(), "\n")
out = MAIN / "outputs/tables/region_benchmark_testyears.xlsx"
with pd.ExcelWriter(out) as w:
    pm.round(3).to_excel(w, sheet_name="per_model")
    r.to_excel(w, sheet_name="per_year", index=False)
print("saved", out)
