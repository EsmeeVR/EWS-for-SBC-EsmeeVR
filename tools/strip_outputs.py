"""
Clear stored outputs and execution counts from notebooks before committing.

Committed notebooks carry code only; the figures and tables they produce are committed
as files under outputs/ instead. That keeps diffs readable and the repository small.

    python tools/strip_outputs.py              # strip every notebook
    python tools/strip_outputs.py --check      # report, change nothing (use in CI)
    python tools/strip_outputs.py notebooks/01_micro_construction.ipynb
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strip(path: Path, check_only: bool) -> tuple[bool, int]:
    """Return (was_dirty, cells_cleared)."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    cleared = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs") or cell.get("execution_count") is not None:
            cleared += 1
            cell["outputs"] = []
            cell["execution_count"] = None
        # nbconvert leaves per-cell execution metadata behind
        cell.get("metadata", {}).pop("execution", None)

    if cleared and not check_only:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    return bool(cleared), cleared


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="notebooks to strip (default: all)")
    ap.add_argument("--check", action="store_true", help="report only, exit 1 if any is dirty")
    args = ap.parse_args()

    targets = [Path(p) for p in args.paths] or sorted(ROOT.rglob("*.ipynb"))
    targets = [p for p in targets if ".ipynb_checkpoints" not in p.parts]

    dirty = 0
    for p in targets:
        was_dirty, n = strip(p, args.check)
        if was_dirty:
            dirty += 1
            verb = "would clear" if args.check else "cleared"
            print(f"  {verb} {n:>3} cells  {p.relative_to(ROOT)}")

    if args.check and dirty:
        print(f"\n{dirty} notebook(s) still carry outputs. Run: python tools/strip_outputs.py")
        return 1
    print(f"\n{len(targets)} notebooks checked, {dirty} modified" if not args.check
          else f"\n{len(targets)} notebooks checked, all clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
