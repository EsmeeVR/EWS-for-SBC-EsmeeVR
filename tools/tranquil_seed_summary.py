"""
Five-seed summary of the A35 tranquil-years false alarm rates (2013-2017, baseline labels).

Reads outputs/results/<spec>/tranquil_false_alarms.xlsx in each seed worktree and writes
outputs/seeds/tranquil_seed_summary.csv: per specification and configuration the pooled false alarm
rate (alarms / bank-years over the five tranquil years and the models), as mean, min and max over seeds.
The decision tree is left out because its macro configuration alarms on every bank-year in some seeds.

    python tools/tranquil_seed_summary.py --runs 42=. 7=../thesis-ews-final-s7 13=../thesis-ews-final-s13 \
        27=../thesis-ews-final-s27 99=../thesis-ews-final-s99
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SPECS = ["11a", "11b", "11c", "11d"]
EXCLUDE = {"decision_tree", "lr_no_dummies"}

ap = argparse.ArgumentParser()
ap.add_argument("--runs", nargs="+", required=True, help="seed=path pairs")
args = ap.parse_args()

rows = []
for pair in args.runs:
    seed, path = pair.split("=", 1)
    for spec in SPECS:
        d = pd.read_excel(ROOT / path / "outputs" / "results" / spec / "tranquil_false_alarms.xlsx", "by_year")
        d = d[(d["variant"] == "baseline_t1") & (~d["model"].isin(EXCLUDE))]
        for dataset, g in d.groupby("dataset"):
            rows.append(dict(seed=int(seed), spec=spec, dataset=dataset,
                             false_alarm_rate=g["n_alarms"].sum() / g["n_obs"].sum()))

per_seed = pd.DataFrame(rows)
summary = (per_seed.groupby(["spec", "dataset"])["false_alarm_rate"]
           .agg(["mean", "min", "max"]).round(3).reset_index())
out = ROOT / "outputs" / "seeds"
out.mkdir(parents=True, exist_ok=True)
per_seed.round(4).to_csv(out / "tranquil_per_seed.csv", index=False)
summary.to_csv(out / "tranquil_seed_summary.csv", index=False)
print(summary.to_string(index=False))
