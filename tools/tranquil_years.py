"""
False alarms in tranquil years (audit A35): a separate analysis, outside the main results.

The main loop skips test years without crisis observations (2013-2017), because AUROC needs both
classes. An early warning system is still judged on those years: every alarm there is a false one.
This script fits a model for each tranquil year exactly as the main loop does and counts alarms with a
cut-off fixed in advance (see ews_common.run_tranquil_years). It writes

    outputs/results/<spec>/tranquil_false_alarms.xlsx

and never touches all_results or any other main result. Run it after the main notebooks, because the
cut-off comes from their stored predictions (proba_store_final.pkl):

    python tools/tranquil_years.py            # 11a, 11b, 11c, 11d
    python tools/tranquil_years.py 11a        # one specification

To reuse each notebook's own data preparation without duplicating it, the script executes that
notebook's code cells up to (not including) the training loop. Those cells only read data; the
script refuses to run any cell that writes a file.
"""
import contextlib
import io
import json
import os
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
SPECS = {
    "11a": "11a_modelling_baseline_lag1",
    "11b": "11b_modelling_robust_lag1",
    "11c": "11c_modelling_baseline_lag2",
    "11d": "11d_modelling_robust_lag2",
}
WRITES = ("to_excel", "to_parquet", "to_csv", "pickle.dump", "savefig", "write_text")


def notebook_setup(spec):
    """Namespace after the notebook's cells that come before the training loop."""
    cells = json.loads((NOTEBOOKS / f"{SPECS[spec]}.ipynb").read_text(encoding="utf-8"))["cells"]
    loop = [i for i, c in enumerate(cells) if "run_expanding_window(" in "".join(c["source"])]
    assert len(loop) == 1, f"{spec}: expected one training-loop cell, found {len(loop)}"
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        for i, c in enumerate(cells[: loop[0]]):
            if c["cell_type"] != "code":
                continue
            code = "".join(c["source"])
            if any(w in code for w in WRITES):
                raise RuntimeError(f"{spec} cell {i} writes a file; refusing to run it from here")
            exec(compile(code, f"{spec}[{i}]", "exec"), ns)
        variants_line = [l for l in "".join(cells[loop[0]]["source"]).split("\n") if l.startswith("VARIANTS =")]
        exec(variants_line[0], ns)
    return ns


def main() -> int:
    specs = sys.argv[1:] or list(SPECS)
    os.chdir(NOTEBOOKS)  # the notebooks read ../data/..., relative to notebooks/
    sys.path.insert(0, str(NOTEBOOKS))
    import pandas as pd
    import ews_common as ec

    for spec in specs:
        out_dir = ROOT / "outputs" / "results" / spec
        proba_file = out_dir / "proba_store_final.pkl"
        if not proba_file.exists():
            print(f"{spec}: {proba_file} not found - run the main notebook first")
            return 1
        proba_store = pickle.loads(proba_file.read_bytes())
        ns = notebook_setup(spec)
        print(f"=== {spec}")
        res = ec.run_tranquil_years(ns["splits"], ns["feature_sets"], ns["feature_sets_lr"], ns["VARIANTS"],
                                    target=ns["target"], country_col=ns["country_col"],
                                    proba_store=proba_store, n_trials=ns.get("N_TRIALS", 50))
        summary = (res.groupby(["variant", "dataset", "model"])[["false_alarm_rate", "n_alarms", "n_obs"]]
                   .agg({"false_alarm_rate": "mean", "n_alarms": "sum", "n_obs": "sum"}).round(3))
        with pd.ExcelWriter(out_dir / "tranquil_false_alarms.xlsx", engine="openpyxl") as writer:
            res.to_excel(writer, sheet_name="by_year", index=False)
            summary.to_excel(writer, sheet_name="summary")
        print(f"[SAVED] {out_dir / 'tranquil_false_alarms.xlsx'} ({len(res)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
