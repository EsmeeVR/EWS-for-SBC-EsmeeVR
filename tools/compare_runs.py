"""
Compare two sets of model results, cell by cell and at the level of the paper's claims.

The rerun happens in stages. After each stage this answers two questions: did any number
move, and did any claim move. A claim is what the text states from these tables: which
configuration wins per model, the order of the three configurations on the mean over
models, and how many models have the integrated configuration beating both single-level
ones (the 0/6, 2/6, 1/6 counts).

Either side is a folder (a working tree with fresh results) or a git ref (branch, tag or
commit). Reading the "before" side from git means it is read from history, so a stray
write to outputs/ cannot change what you compare against. It also lets each stage be
compared with the previous one: commit the stage's results, then use that commit as --old.

    python tools/compare_runs.py --old audit-2026-09 --label stage0 --expect-identical
    python tools/compare_runs.py --old rerun-stage0 --label stage1
    python tools/compare_runs.py --old audit-2026-09 --new ../thesis-ews --label check

Writes outputs/compare/<label>/report.md (summary) and cells.csv (every cell, one row each).
"""
import argparse
import io
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = "outputs/results"
KEYS = ["model", "variant", "dataset", "test_year"]
# AUROC and AUPRC rank predictions and do not depend on the classification threshold, so
# they are the metrics claims rest on. Threshold metrics (F1, miss rate, loss) are
# expected to change once the threshold is chosen without test labels (audit A1).
RANKING = ["auroc", "auprc"]
CONFIGS = ["micro", "macro", "integrated"]
# The six models the claims are about. The results files also hold diagnostic fits, such
# as lr_no_dummies (LR without country dummies, 0.07-0.32 AUROC weaker); averaging those
# in shifts the means and can flip the configuration order. They stay in the cell-by-cell
# comparison, so a change to them is still reported.
MODELS = ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm", "mlp"]
# Seeded models in the same environment reproduce to the last digit, so "unchanged"
# means equal up to floating-point noise, not "close".
EXACT = 1e-9


def git(*args: str) -> bytes:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.decode().strip()}")
    return r.stdout


class Source:
    """One set of results, from a folder or a git ref, read the same way."""

    def __init__(self, spec: str):
        if Path(spec).is_dir():
            self.root, self.ref = Path(spec).resolve(), None
            self.label = f"{self.root} (folder)"
        else:
            check = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{spec}^{{commit}}"],
                capture_output=True)
            if check.returncode:
                raise SystemExit(f"'{spec}' is neither a folder nor a git branch, tag or commit")
            self.root, self.ref = None, spec
            sha = git("rev-parse", "--short", spec).decode().strip()
            self.label = f"{spec} @ {sha} (git)"

    def files(self) -> dict[str, list[str]]:
        """Results workbooks per specification folder, e.g. {'11a': [...xlsx paths]}."""
        if self.ref:
            paths = git("ls-tree", "-r", "--name-only", self.ref, "--", RESULTS).decode().splitlines()
        else:
            base = self.root / RESULTS
            paths = [p.relative_to(self.root).as_posix() for p in base.glob("*/*.xlsx")] if base.is_dir() else []
        out: dict[str, list[str]] = {}
        for p in paths:
            parts = p.split("/")
            # Only files directly in outputs/results/<spec>/. "~$" files are Excel lock files.
            if len(parts) == 4 and p.endswith(".xlsx") and not parts[3].startswith("~$"):
                out.setdefault(parts[2], []).append(p)
        return out

    def read(self, path: str) -> pd.DataFrame:
        raw = git("show", f"{self.ref}:{path}") if self.ref else (self.root / path).read_bytes()
        df = pd.read_excel(io.BytesIO(raw), sheet_name="all_results")
        dup = int(df.duplicated(KEYS).sum())
        if dup:
            raise SystemExit(f"{path}: {dup} duplicate rows on {KEYS}; cannot match cells")
        return df


def pick(files: list[str]) -> str | None:
    """The final file if there is one, else the highest-numbered draft (plain 'draft' = 1).

    Some specifications only have drafts (11c, audit A40), so falling back is needed, and
    the report shows which file was read on each side.
    """
    def rank(f: str) -> tuple[int, int]:
        stem = Path(f).stem
        if stem.endswith("_final"):
            return (2, 0)
        m = re.search(r"_draft(\d*)$", stem)
        return (1, int(m.group(1) or 1)) if m else (0, 0)
    return max(files, key=rank) if files else None


def fmt(x: float, signed: bool = False) -> str:
    return "" if pd.isna(x) else (f"{x:+.3f}" if signed else f"{x:.3f}")


def claims(both: pd.DataFrame, metric: str) -> tuple[list[str], list[str]]:
    """Report lines and claim changes for one specification and variant.

    `both` holds only cells present on both sides, so means are over matched test years:
    a stage that adds or drops a year does not show up as a change in performance.
    """
    lines, changes = [], []
    years = ", ".join(str(y) for y in sorted(both.test_year.unique()))
    per_model = both.groupby(["model", "dataset"])[[f"{metric}_old", f"{metric}_new"]].mean()
    overall = per_model.groupby("dataset").mean()

    lines.append(f"Mean {metric.upper()} over models (test years {years}):\n")
    lines.append("| Configuration | Old | New | Δ |\n|---|---|---|---|")
    for ds in [c for c in CONFIGS if c in overall.index] + [c for c in overall.index if c not in CONFIGS]:
        o, n = overall.loc[ds]
        lines.append(f"| {ds} | {fmt(o)} | {fmt(n)} | {fmt(n - o, True)} |")

    if not set(CONFIGS) <= set(overall.index):
        return lines, changes  # macro-only specifications: no configuration comparison

    order ={s: " > ".join(overall[f"{metric}_{s}"].sort_values(ascending=False).index) for s in ("old", "new")}
    lines.append(f"\nOrder of configurations: {order['old']}"
                 + ("  (unchanged)" if order["old"] == order["new"] else f"  →  **{order['new']}**"))
    if order["old"] != order["new"]:
        changes.append(f"order of configurations: {order['old']} → {order['new']}")

    wide = {s: per_model[f"{metric}_{s}"].unstack("dataset")[CONFIGS] for s in ("old", "new")}
    winner = {s: wide[s].idxmax(axis=1) for s in ("old", "new")}
    beats = {s: (wide[s]["integrated"] > wide[s][["micro", "macro"]].max(axis=1)) for s in ("old", "new")}
    n_models = len(wide["old"])
    b_old, b_new = int(beats["old"].sum()), int(beats["new"].sum())
    lines.append(f"Integrated beats both: {b_old}/{n_models}"
                 + ("  (unchanged)" if b_old == b_new else f"  →  **{b_new}/{n_models}**"))
    if b_old != b_new:
        changes.append(f"integrated beats both: {b_old}/{n_models} → {b_new}/{n_models}")

    lines.append("\n| Model | Best (old) | Best (new) | micro Δ | macro Δ | integrated Δ |\n|---|---|---|---|---|---|")
    for m in wide["old"].index:
        w_o, w_n = winner["old"][m], winner["new"][m]
        d = wide["new"].loc[m] - wide["old"].loc[m]
        flag = "" if w_o == w_n else " ⚠"
        lines.append(f"| {m} | {w_o} | {w_n}{flag} | " + " | ".join(fmt(d[c], True) for c in CONFIGS) + " |")
        if w_o != w_n:
            changes.append(f"best configuration for {m}: {w_o} → {w_n}")
    return lines, changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="folder or git ref with the 'before' results")
    ap.add_argument("--new", default=".", help="folder or git ref with the 'after' results (default: this tree)")
    ap.add_argument("--label", required=True, help="name of this comparison, e.g. stage1; used as output folder")
    ap.add_argument("--metric", default="auroc", choices=RANKING, help="metric for the claim checks")
    ap.add_argument("--material", type=float, default=0.01,
                    help="flag a change in a mean over models at least this large (default 0.01)")
    ap.add_argument("--expect-identical", action="store_true",
                    help="exit 1 unless every cell and every file matches (use for the stage-0 check)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    old, new = Source(args.old), Source(args.new)
    f_old, f_new = old.files(), new.files()
    specs = sorted(set(f_old) | set(f_new))

    files_tbl, structure, sections, cells = [], [], [], []
    claim_changes, material = [], []
    excluded: set[str] = set()

    for spec in specs:
        p_old, p_new = pick(f_old.get(spec, [])), pick(f_new.get(spec, []))
        n_old = Path(p_old).name if p_old else "none"
        n_new = Path(p_new).name if p_new else "none"
        # A draft on one side and a final on the other means the two may not be the same
        # run of the notebook (audit A10); the numbers are still compared, but flagged.
        mixed = p_old and p_new and ("_final" in n_old) != ("_final" in n_new)
        files_tbl.append(f"| {spec} | {n_old} | {n_new}{' ⚠ draft vs final' if mixed else ''} |")
        if not (p_old and p_new):
            structure.append(f"- **{spec}**: results only on the {'old' if p_old else 'new'} side")
            continue

        a, b = old.read(p_old), new.read(p_new)
        metrics = [c for c in a.columns if c in b.columns and c not in KEYS
                   and pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c])]
        for gone in [c for c in a.columns if c not in b.columns]:
            structure.append(f"- **{spec}**: column `{gone}` dropped")
        for added in [c for c in b.columns if c not in a.columns]:
            structure.append(f"- **{spec}**: column `{added}` added")

        m = a[KEYS + metrics].merge(b[KEYS + metrics], on=KEYS, how="outer",
                                    suffixes=("_old", "_new"), indicator=True)
        for side, tag in (("left_only", "old"), ("right_only", "new")):
            only = m[m._merge == side]
            if len(only):
                groups = only.groupby(["variant", "test_year"]).size()
                desc = ", ".join(f"{v} {y} ({n})" for (v, y), n in groups.items())
                structure.append(f"- **{spec}**: {len(only)} cells only in {tag}: {desc}")

        both = m[m._merge == "both"].copy()
        changed_other = pd.Series("", index=both.index)
        for c in metrics:
            o, n = both[f"{c}_old"], both[f"{c}_new"]
            # NaN on both sides counts as equal; NaN on one side counts as a change.
            diff = ((o - n).abs() > EXACT) | (o.isna() != n.isna())
            if c not in RANKING:
                changed_other[diff] += c + " "
        both["changed_other"] = changed_other.str.strip()
        for c in RANKING:
            both[f"{c}_delta"] = both[f"{c}_new"] - both[f"{c}_old"]
        both["changed"] = both[[f"{c}_delta" for c in RANKING]].abs().gt(EXACT).any(axis=1) | both.changed_other.ne("")
        both.insert(0, "spec", spec)
        cells.append(both[["spec", *KEYS] + [f"{c}_{s}" for c in RANKING for s in ("old", "new", "delta")]
                          + ["changed", "changed_other"]])

        excluded |= set(both.model) - set(MODELS)
        for variant, g in both[both.model.isin(MODELS)].groupby("variant"):
            lines, changes = claims(g, args.metric)
            sections.append(f"### {spec} · {variant}\n\n" + "\n".join(lines) + "\n")
            claim_changes += [f"{spec} {variant}: {c}" for c in changes]
            means = g.groupby("dataset")[[f"{args.metric}_old", f"{args.metric}_new"]].mean()
            for ds, (o, n) in means.iterrows():
                if abs(n - o) >= args.material:
                    material.append(f"{spec} {variant} {ds}: {o:.3f} → {n:.3f} ({n - o:+.3f})")

    allc = pd.concat(cells, ignore_index=True) if cells else pd.DataFrame()
    n_cells = len(allc)
    n_changed = int(allc.changed.sum()) if n_cells else 0
    n_other = int(allc.changed_other.ne("").sum()) if n_cells else 0

    verdict = [f"- Cells compared: **{n_cells}**, identical: **{n_cells - n_changed}**, changed: **{n_changed}**"]
    if n_changed:
        d = allc[f"{args.metric}_delta"].abs()
        top = allc.loc[d.idxmax()]
        verdict.append(f"- Largest {args.metric.upper()} change in one cell: {top[f'{args.metric}_delta']:+.4f} "
                       f"({top.spec} {top.variant} {top.model} {top.dataset} {top.test_year})")
        verdict.append(f"- Cells where a threshold-based metric changed: {n_other}")
    verdict.append(f"- Claim changes: **{len(claim_changes)}**" + "".join(f"\n  - {c}" for c in claim_changes))
    verdict.append(f"- Means over models that moved by {args.material} or more: **{len(material)}**"
                   + "".join(f"\n  - {c}" for c in material))
    verdict.append(f"- Structural differences: **{len(structure)}** (see below)")

    report = "\n".join([
        f"# Results comparison: {args.label}",
        "",
        f"- Old: {old.label}",
        f"- New: {new.label}",
        f"- Claim checks on {args.metric.upper()}, means over matched test years; "
        f"material change ≥ {args.material}",
        f"- Claim checks use the six models; left out (still compared cell by cell): "
        f"{', '.join(sorted(excluded)) or 'none'}",
        f"- Generated {datetime.now():%d-%m-%Y %H:%M}",
        "",
        "## Verdict", "", *verdict, "",
        "## Files read", "", "| Spec | Old | New |", "|---|---|---|", *files_tbl, "",
        "## Structural differences", "", *(structure or ["None."]), "",
        "## Per specification", "", *sections,
    ])

    out = ROOT / "outputs" / "compare" / args.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(report, encoding="utf-8")
    allc.to_csv(out / "cells.csv", index=False)

    print(f"# {args.label}: {old.label}  →  {new.label}\n")
    print("\n".join(verdict))
    print(f"\nWritten: {out / 'report.md'}\n         {out / 'cells.csv'}")

    if args.expect_identical and (n_changed or structure or any("⚠" in r for r in files_tbl)):
        print("\nNOT IDENTICAL (--expect-identical)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
