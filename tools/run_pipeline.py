"""
Run the whole pipeline unattended, in dependency order, and log every step.

Each notebook is executed with nbclient in notebooks/ (the folder its relative paths assume). The
committed notebooks are not modified: the executed copy, with its outputs, is written to
outputs/run_logs/<start time>/, next to run.log (start, end, duration and status per notebook).
The run stops at the first failure; --from resumes there.

    python tools/run_pipeline.py                      # everything, 01 to 16
    python tools/run_pipeline.py --from 13a           # resume at a step
    python tools/run_pipeline.py --only 14 15 16      # selected steps
    python tools/run_pipeline.py --dry-run            # list the steps, run nothing
    python tools/run_pipeline.py --tranquil           # the separate A35 job (after the main run)

Run it with the Python that has the pinned requirements. Before anything runs, a probe cell checks
that the notebook kernel sees the pinned pandas and scikit-learn versions, because a kernel from
another installation would produce a whole night of unusable results.
"""
import argparse
import asyncio
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"

# Dependency order. rt2a/rt2b run before 14/15, which read their results. The pre-crisis
# relabelling is still invalid as an anticipation test (audit A46); it is rerun so that every
# number in the paper comes from one sample and one code version, and each notebook now reports
# the A46 falsification baseline next to its own scores so the result is read as a negative one.
STEPS = [
    ("01", "01_micro_construction"),
    ("02", "02_macro_construction"),
    ("03", "03_panel_construction"),
    ("04", "04_feature_engineering"),
    ("05", "05_macro_individual_merge"),
    ("11a", "11a_modelling_baseline_lag1"),
    ("11b", "11b_modelling_robust_lag1"),
    ("11c", "11c_modelling_baseline_lag2"),
    ("11d", "11d_modelling_robust_lag2"),
    ("12a", "12a_macro_only_baseline"),
    ("12a_gran", "12a_granularity_baseline"),
    ("12b", "12b_macro_only_robust"),
    ("12b_gran", "12b_granularity_robust"),
    ("rt2a", "rt2a_precrisis_baseline"),
    ("rt2b", "rt2b_precrisis_robust"),
    ("13a", "13a_attribution_11a"),
    ("13b", "13b_attribution_11b"),
    ("13c", "13c_attribution_11c"),
    ("13d", "13d_attribution_11d"),
    ("14", "14_visualisations"),
    ("15", "15_results"),
    ("16", "16_descriptive_statistics"),
    # Crisis-definition check (Reinhart & Rogoff against L&V on the same rows). Nothing downstream reads
    # it. The panel step is a script, rebuilt every time so the check can never run on a stale sample.
    ("rr_panels", "tools/build_rr_panels.py"),
    ("rr11a_RR", "rr_11a_RR"),
    ("rr11a_LViso", "rr_11a_LViso"),
    ("rr11b_RR", "rr_11b_RR"),
    ("rr11b_LViso", "rr_11b_LViso"),
]
PINNED = {"pandas": "3.0.2", "sklearn": "1.8.0"}


def log(logfile: Path, line: str) -> None:
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"[{stamp}] {line}", flush=True)
    with logfile.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def check_kernel() -> None:
    import nbformat
    from nbclient import NotebookClient
    probe = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(
        "import sys, pandas, sklearn; print(sys.executable, pandas.__version__, sklearn.__version__)")])
    NotebookClient(probe, timeout=120, kernel_name="python3").execute()
    exe, pd_v, sk_v = probe.cells[0].outputs[0]["text"].split()
    if (pd_v, sk_v) != (PINNED["pandas"], PINNED["sklearn"]):
        raise SystemExit(f"kernel {exe} has pandas {pd_v}, scikit-learn {sk_v}; "
                         f"expected {PINNED['pandas']} and {PINNED['sklearn']} (requirements.txt)")
    print(f"kernel ok: {exe} (pandas {pd_v}, scikit-learn {sk_v})")


def run_notebook(name: str, out_dir: Path, timeout: int) -> None:
    import nbformat
    from nbclient import NotebookClient
    nb = nbformat.read(NOTEBOOKS / f"{name}.ipynb", as_version=4)
    client = NotebookClient(nb, timeout=timeout, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOKS)}})
    try:
        client.execute()
    finally:
        # keep the executed copy even when a cell fails, so the traceback can be read
        nbformat.write(nb, out_dir / f"{name}.ipynb")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", help="step key to resume from, e.g. 13a")
    ap.add_argument("--only", nargs="+", help="run only these step keys")
    ap.add_argument("--timeout", type=int, default=6 * 3600, help="seconds per notebook cell (default 6 h)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tranquil", action="store_true", help="run the separate A35 tranquil-years job instead")
    args = ap.parse_args()

    if sys.platform == "win32":
        # zmq on Windows needs the selector event loop; avoids a warning per notebook
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    keys = [k for k, _ in STEPS]
    steps = STEPS
    if args.only:
        unknown = set(args.only) - set(keys)
        if unknown:
            raise SystemExit(f"unknown step(s): {sorted(unknown)}; known: {keys}")
        steps = [s for s in STEPS if s[0] in args.only]
    elif args.start:
        if args.start not in keys:
            raise SystemExit(f"unknown step {args.start!r}; known: {keys}")
        steps = STEPS[keys.index(args.start):]

    if args.dry_run:
        for k, name in (steps if not args.tranquil else [("tranquil", "tools/tranquil_years.py")]):
            print(f"{k:>9}  {name}")
        return 0

    out_dir = ROOT / "outputs" / "run_logs" / datetime.now().strftime("%Y%m%d_%H%M")
    out_dir.mkdir(parents=True, exist_ok=True)
    logfile = out_dir / "run.log"
    check_kernel()

    if args.tranquil:
        t0 = time.time()
        log(logfile, "START tranquil years (A35)")
        rc = subprocess.run([sys.executable, str(ROOT / "tools" / "tranquil_years.py")], cwd=ROOT).returncode
        log(logfile, f"{'DONE' if rc == 0 else 'FAILED'} tranquil years in {(time.time() - t0) / 60:.1f} min")
        return rc

    t_all = time.time()
    for key, name in steps:
        t0 = time.time()
        log(logfile, f"START {key} {name}")
        try:
            if name.endswith(".py"):
                subprocess.run([sys.executable, str(ROOT / name)], cwd=ROOT, check=True)
            else:
                run_notebook(name, out_dir, args.timeout)
        except Exception as exc:  # noqa: BLE001 - log whatever stopped the notebook, then stop the run
            first = str(exc).strip().splitlines()[-1] if str(exc).strip() else type(exc).__name__
            log(logfile, f"FAILED {key} after {(time.time() - t0) / 60:.1f} min: {first}")
            log(logfile, f"executed copy with the traceback: {out_dir / (name + '.ipynb')}")
            log(logfile, f"resume with: python tools/run_pipeline.py --from {key}")
            return 1
        log(logfile, f"DONE  {key} in {(time.time() - t0) / 60:.1f} min")
    log(logfile, f"ALL DONE in {(time.time() - t_all) / 3600:.2f} h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
