"""
Combine the results of the same pipeline run with several random seeds.

A single seed gives one of many equally valid outcomes: Optuna's search path, the bootstrap samples
of the forests and the MLP's starting weights all depend on it. On a sample with ten crisis
countries per test year that matters, so results are reported as the average over seeds, with the
range across seeds, and a claim counts as robust only when it holds in every seed.

    python tools/aggregate_seeds.py --runs 42=../thesis-ews-final 7=../thesis-ews-final-s7 ...

Writes outputs/seeds/seed_summary.xlsx (per cell and per configuration) and seed_report.md.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SIX = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm", "mlp"]
KEYS = ["spec", "variant", "model", "dataset", "test_year"]
SPECS = ["11a", "11b", "11c", "11d", "12a", "12a_gran", "12b", "12b_gran"]
CONFIGS = ["micro", "macro", "integrated"]


def result_file(root: Path, spec: str) -> Path | None:
    """The final results workbook of one specification (falls back to the newest draft)."""
    d = root / "outputs" / "results" / spec
    if not d.is_dir():
        return None
    finals = sorted(d.glob("results_*_final.xlsx"))
    drafts = sorted(d.glob("results_*_draft*.xlsx"))
    return (finals or drafts or [None])[-1]


def load(runs: dict[str, Path]) -> pd.DataFrame:
    frames = []
    for seed, root in runs.items():
        for spec in SPECS:
            f = result_file(root, spec)
            if f is None:
                continue
            a = pd.read_excel(f, sheet_name="all_results")
            a.insert(0, "spec", spec)
            a.insert(0, "seed", seed)
            frames.append(a)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="seed=folder pairs, e.g. 42=../thesis-ews-final")
    ap.add_argument("--metric", default="auroc")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    runs = {s.split("=", 1)[0]: Path(s.split("=", 1)[1]).resolve() for s in args.runs}
    m = args.metric

    d = load(runs)
    d = d[d.model.isin(SIX)]
    seeds = sorted(d.seed.unique(), key=lambda s: int(s) if s.isdigit() else s)

    # per cell: mean over seeds and the range
    cells = (d.groupby(KEYS)[[m, "auprc"]].agg(["mean", "min", "max", "count"]))
    cells.columns = [f"{a}_{b}" for a, b in cells.columns]
    cells = cells.reset_index()

    # per seed: mean over test years per model, then claims per spec x variant
    per_model = d.groupby(["seed", "spec", "variant", "model", "dataset"])[m].mean().unstack("dataset")
    lines = [f"# Results over {len(seeds)} seeds: {', '.join(seeds)}", "",
             f"Metric: {m.upper()}, mean over test years, then over the six models. A claim is robust when it holds in every seed.", ""]
    summ_rows = []
    for (spec, variant), g in per_model.groupby(level=["spec", "variant"]):
        cfgs = [c for c in CONFIGS if c in g.columns and g[c].notna().any()]
        means = g[cfgs].groupby(level="seed").mean()                   # seed x config
        row = {"spec": spec, "variant": variant}
        for c in cfgs:
            row[f"{c}_mean"], row[f"{c}_min"], row[f"{c}_max"] = means[c].mean(), means[c].min(), means[c].max()
        lines.append(f"## {spec} · {variant}\n")
        lines.append("| Configuration | Mean over seeds | Lowest | Highest |\n|---|---|---|---|")
        for c in cfgs:
            lines.append(f"| {c} | {means[c].mean():.3f} | {means[c].min():.3f} | {means[c].max():.3f} |")
        if len(cfgs) == 3:
            orders = means.apply(lambda r: " > ".join(r.sort_values(ascending=False).index), axis=1)
            top = means.idxmax(axis=1)
            beats = g.groupby(level="seed").apply(lambda x: int((x["integrated"] > x[["micro", "macro"]].max(axis=1)).sum()))
            best_micro = g.groupby(level="seed").apply(lambda x: int((x[cfgs].idxmax(axis=1) == "micro").sum()))
            order_pooled = " > ".join(pd.Series({c: means[c].mean() for c in cfgs}).sort_values(ascending=False).index)
            row.update({"order_of_means": order_pooled, "top_config_in_all_seeds": top.iloc[0] if top.nunique() == 1 else "varies",
                        "orders_seen": "; ".join(sorted(set(orders))), "integrated_beats_both_range": f"{beats.min()}-{beats.max()} of 6",
                        "micro_best_models_range": f"{best_micro.min()}-{best_micro.max()} of 6"})
            lines.append(f"\nOrder of the means over seeds: **{order_pooled}**")
            lines.append(f"Best configuration: **{top.iloc[0]} in every seed**" if top.nunique() == 1
                         else f"Best configuration: **varies across seeds** ({', '.join(f'{s}: {t}' for s, t in top.items())})")
            lines.append(f"Orders seen across seeds: {'; '.join(sorted(set(orders)))}")
            lines.append(f"Integrated beats both: {beats.min()} to {beats.max()} of 6 models · micro best: {best_micro.min()} to {best_micro.max()} of 6 models")
        lines.append("")
        summ_rows.append(row)

    out = ROOT / "outputs" / "seeds"
    out.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out / "seed_summary.xlsx") as w:
        pd.DataFrame(summ_rows).to_excel(w, sheet_name="configurations", index=False)
        cells.to_excel(w, sheet_name="cells", index=False)
    (out / "seed_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:4]))
    print(f"Written: {out / 'seed_summary.xlsx'} and seed_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
