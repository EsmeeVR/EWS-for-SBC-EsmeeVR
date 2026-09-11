"""Rebuild the descriptive-statistics tables SPLIT BY LEVEL instead of by specification.

Why this exists
---------------
NB16 exports one table per *specification* (baseline / extended), which means the
same variable is printed twice and the reader has to compare two tables to see
which variables the extension adds. The manuscript reports macro and micro
separately (3.2.4.1 / 3.2.4.2), so the useful split is by LEVEL, with a column
saying which specification(s) each variable belongs to.

Reads NB16's own export rather than recomputing, so these tables cannot drift
away from Appendix C. Same pattern as build_appendix_h_displacement.py.

⚠️ Which panel supplies the numbers
-----------------------------------
The two panels were imputed separately, so a variable present in BOTH sets has
slightly different statistics in each (e.g. r_cti mean 66.227 baseline vs 66.619
extended). This script reports the BASELINE panel for anything in the baseline
set, because the baseline specification is the primary one, and falls back to the
extended panel only for variables the baseline set does not contain. The
manuscript note must say so, and Appendix C keeps both full versions.
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "descriptive_statistics.xlsx"

# Columns kept for the body tables. p25/p75 are dropped: min, median, max and
# skew already convey shape, and the quartiles cost two columns on a page-width
# table. The long 'indicator' name is dropped because Appendix B (B1/B2) already
# defines every coded name, so repeating it here is duplication, not reference.
KEEP = ["count", "mean", "std", "min", "median", "max", "skew"]
RENAME = {
    "count": "N", "mean": "Mean", "std": "SD", "min": "Min",
    "median": "Median", "max": "Max", "skew": "Skew",
}


def load(sheet: str) -> pd.DataFrame:
    """Load one NB16 sheet, indexed by coded variable name."""
    df = pd.read_excel(SRC, sheet_name=sheet)
    # NB16 writes the coded name into the unnamed index column
    df = df.rename(columns={"Unnamed: 0": "coded"}).set_index("coded")
    return df


def main() -> None:
    base, ext = load("baseline"), load("extended")

    base_vars, ext_vars = set(base.index), set(ext.index)

    def membership(v: str) -> str:
        """Which specification(s) contain this variable.

        This is the column that replaces having two separate tables: the reader
        sees the extension as a property of each row instead of as a second table.
        """
        if v in base_vars and v in ext_vars:
            return "Both"
        return "Baseline only" if v in base_vars else "Extended only"

    rows = []
    for v in sorted(base_vars | ext_vars):
        # Baseline is the primary specification, so it supplies the numbers
        # wherever it can; the extended panel only fills in its own additions.
        src = base if v in base_vars else ext
        r = src.loc[v, KEEP + ["level"]].copy()
        r["Set"] = membership(v)
        r.name = v
        rows.append(r)

    tbl = pd.DataFrame(rows).rename(columns=RENAME)
    tbl.index.name = "Variable"

    out = {}
    for level in ("Macro", "Micro"):
        sub = tbl[tbl["level"] == level].drop(columns="level")
        # Set first so membership reads before the statistics
        sub = sub[["Set"] + list(RENAME.values())]
        # Sort so shared variables lead and the extension additions group at the
        # end, which is the order the prose walks through them in.
        order = {"Both": 0, "Baseline only": 1, "Extended only": 2}
        sub = sub.sort_values("Set", key=lambda s: s.map(order), kind="stable")
        out[level] = sub.round(3)

    dst = BASE / "descriptive_statistics_by_level.xlsx"
    with pd.ExcelWriter(dst) as w:
        for level, sub in out.items():
            sub.to_excel(w, sheet_name=level.lower())
            sub.to_csv(BASE / f"descriptive_statistics_{level.lower()}.csv")

    for level, sub in out.items():
        print(f"\n===== {level} ({len(sub)} variables) =====")
        print(sub.to_string())
    print(f"\nWritten: {dst.name} (+ two csv)")


if __name__ == "__main__":
    main()
