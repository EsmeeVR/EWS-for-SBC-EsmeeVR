"""
Five-seed stability of the cross-specification bump chart (NB15 cell 59), lag 1, integrated configuration.

Same ranking logic as NB15 pooled_shares: per model the mean |SHAP| over the test observations is turned
into within-model shares, which are averaged within a model class (trees = DT, RF, XGB, LGBM; LR; MLP).
For every seed and class it reports, in the top 10 of the extended set, the rank of each of the four
added macroeconomic indicators, and which bank-level indicators are in the baseline top 10 but not in the
extended top 10. Reads the local SHAP parquets (per-observation values are gitignored; this script only
writes ranks). Output: outputs/tables/bump_seed_check.csv.
"""
from pathlib import Path
import pandas as pd

H = Path(r"C:\Users\esmvr")
SEEDS = {42: H / "thesis-ews-final", 7: H / "thesis-ews-final-s7", 13: H / "thesis-ews-final-s13",
         27: H / "thesis-ews-final-s27", 99: H / "thesis-ews-final-s99"}
CLASS = {"decision_tree": "Tree", "random_forest": "Tree", "xgboost": "Tree", "lightgbm": "Tree",
         "logistic_regression": "LR", "mlp": "MLP"}
ADDED = ["credit_gap", "credit_g", "nfa_gdp", "FS.AST.PRVT.GD.ZS"]
MACRO = {"NGDP_RPCH", "NGDPD", "PCPIPCH", "LUR", "BCA_NGDPD", "BIS_REER", "RXF11FX_REVS", "reer_g", "fx_g"} | set(ADDED)
N = 10


def pooled_shares(repo, spec):
    df = pd.read_parquet(repo / f"outputs/attribution/outputs_{spec}/shap_values_{spec}.parquet")
    df = df[(df["variant"] == "baseline_t1") & (df["feature_set"] == "integrated")]
    cols = [c for c in df.columns if c.startswith("shap_")]
    rows = []
    for m, sub in df.groupby("model_name"):
        imp = sub[cols].abs().mean()
        imp = imp[imp > 0]
        for c, s in (imp / imp.sum()).items():
            rows.append({"cls": CLASS[m], "feat": c[5:], "share": s})
    return pd.DataFrame(rows).groupby(["cls", "feat"])["share"].mean().reset_index()


out = []
for seed, repo in SEEDS.items():
    base, ext = pooled_shares(repo, "11a"), pooled_shares(repo, "11b")
    for cls in ["Tree", "LR", "MLP"]:
        rb = base[base.cls == cls].sort_values("share", ascending=False).feat.tolist()
        re_ = ext[ext.cls == cls].sort_values("share", ascending=False).feat.tolist()
        topb, tope = rb[:N], re_[:N]
        added_ranks = {a: (re_.index(a) + 1 if a in re_ else None) for a in ADDED}
        micro_out = [f for f in topb if f not in MACRO and f not in tope]
        micro_in_ext = [f for f in tope if f not in MACRO]
        out.append(dict(seed=seed, cls=cls, added_in_top10=sum(r is not None and r <= N for r in added_ranks.values()),
                        **{f"rank_{a}": added_ranks[a] for a in ADDED},
                        micro_in_base_top10=sum(f not in MACRO for f in topb), micro_in_ext_top10=len(micro_in_ext),
                        micro_dropped=", ".join(micro_out)))
res = pd.DataFrame(out)
res.to_csv(H / "thesis-ews-final/outputs/tables/bump_seed_check.csv", index=False)
pd.set_option("display.width", 250)
print(res.sort_values(["cls", "seed"]).to_string(index=False))
