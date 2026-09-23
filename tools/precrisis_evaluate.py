"""
Evaluate the leave-one-country-out pre-crisis predictions against the rules in PRECRISIS.md.

Rule 1 (signal before onset): country-level AUROC in 2007 above the region rule (0.851) in all five
seeds, point estimate; the country-cluster bootstrap interval is reported alongside.
Rule 2 (supporting): the same AUROC within the 11 CEE countries only.
Configurations are reported, not ranked.

    python tools/precrisis_evaluate.py --lag 1

Writes outputs/precrisis/evaluation_lag<lag>.xlsx and prints a summary.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOTS = {42: ".", 7: "../thesis-ews-final-s7", 13: "../thesis-ews-final-s13",
         27: "../thesis-ews-final-s27", 99: "../thesis-ews-final-s99"}
WEST = {"AUT", "BEL", "DNK", "FIN", "FRA", "DEU", "GRC", "IRL", "ITA", "LUX", "NLD", "PRT", "ESP", "SWE"}
MODELS = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm", "mlp"]
REGION_RULE = 0.851
N_BOOT = 2000


def country_year(lag):
    """Country-year scores: mean predicted probability per (seed, dataset, model, country, year)."""
    frames = []
    for seed, root in ROOTS.items():
        files = sorted((Path(root) / "outputs" / "precrisis" / f"lag{lag}").glob("fold_*.parquet"))
        d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        d["seed"] = seed
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    return (d.groupby(["seed", "dataset", "model", "held_out", "year"])
            .agg(proba=("proba", "mean"), crisis_country=("crisis_country", "max"),
                 n_banks=("proba", "size")).reset_index())


def config_auroc(g, countries=None):
    """Mean over the six models of the country-level AUROC in one year."""
    if countries is not None:
        g = g[g.held_out.isin(countries)]
    vals = []
    for m in MODELS:
        h = g[g.model == m]
        if h.crisis_country.nunique() < 2:
            return np.nan
        vals.append(roc_auc_score(h.crisis_country, h.proba))
    return float(np.mean(vals))


def bootstrap(g, countries=None, seed=42):
    """Country-cluster bootstrap of the configuration AUROC: countries drawn with replacement.

    One country contributes one score per model in a given year, so the whole draw is an index into
    a (model x country) score matrix; no dataframe is rebuilt per draw.
    """
    if countries is not None:
        g = g[g.held_out.isin(countries)]
    piv = g.pivot_table(index="model", columns="held_out", values="proba")
    lab = g.groupby("held_out").crisis_country.max().reindex(piv.columns).to_numpy()
    scores = piv.to_numpy()
    rng = np.random.default_rng(seed)
    n = len(lab)
    out = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        y = lab[idx]
        if y.min() == y.max():
            continue
        out.append(float(np.mean([roc_auc_score(y, scores[m, idx]) for m in range(scores.shape[0])])))
    return (np.percentile(out, 2.5), np.percentile(out, 97.5)) if out else (np.nan, np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lag", type=int, default=1)
    args = ap.parse_args()
    cy = country_year(args.lag)
    cee = sorted(set(cy.held_out.unique()) - WEST)

    rows = []
    for (seed, ds, year), g in cy.groupby(["seed", "dataset", "year"]):
        lo, hi = bootstrap(g, seed=seed) if year in (2006, 2007) else (np.nan, np.nan)
        rows.append(dict(seed=seed, dataset=ds, year=year,
                         auroc=config_auroc(g), ci_lo=lo, ci_hi=hi,
                         auroc_cee=config_auroc(g, cee),
                         mean_proba_crisis=g[g.crisis_country == 1].proba.mean(),
                         mean_proba_calm=g[g.crisis_country == 0].proba.mean()))
    res = pd.DataFrame(rows).sort_values(["dataset", "year", "seed"])

    per_model = (cy.groupby(["seed", "dataset", "model", "year"])
                 .apply(lambda g: roc_auc_score(g.crisis_country, g.proba) if g.crisis_country.nunique() > 1 else np.nan,
                        include_groups=False).rename("auroc").reset_index())

    pre = res[res.year.isin([2006, 2007])]
    verdict = []
    for (ds, year), g in pre.groupby(["dataset", "year"]):
        verdict.append(dict(dataset=ds, year=year, seeds=len(g),
                            auroc_min=g.auroc.min(), auroc_mean=g.auroc.mean(), auroc_max=g.auroc.max(),
                            auroc_seed42=g[g.seed == 42].auroc.iloc[0],
                            above_region_all_seeds=bool((g.auroc > REGION_RULE).all()),
                            ci_lo_above_region_all_seeds=bool((g.ci_lo > REGION_RULE).all()),
                            cee_above_half_all_seeds=bool((g.auroc_cee > 0.5).all()),
                            cee_min=g.auroc_cee.min(), cee_seed42=g[g.seed == 42].auroc_cee.iloc[0]))
    verdict = pd.DataFrame(verdict)

    out = Path(f"outputs/precrisis/evaluation_lag{args.lag}.xlsx")
    with pd.ExcelWriter(out) as w:
        verdict.to_excel(w, sheet_name="rules", index=False)
        res.to_excel(w, sheet_name="per_seed_year", index=False)
        per_model.to_excel(w, sheet_name="per_model", index=False)
        cy.to_excel(w, sheet_name="country_year_scores", index=False)
    pd.set_option("display.width", 250)
    print(f"Region rule = {REGION_RULE}; CEE countries ({len(cee)}): {', '.join(cee)}\n")
    print("RULES (pre-crisis years)\n", verdict.round(3).to_string(index=False))
    print("\nSEED 42, all years\n", res[res.seed == 42].round(3).to_string(index=False))
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
