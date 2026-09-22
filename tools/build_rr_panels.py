"""
Build the panels for the crisis-definition check (Reinhart & Rogoff 2011 against Laeven & Valencia).

Both arms use the corrected, lagged estimation panels of the main run, restricted to the country-years
the R&R file covers (13 countries, up to 2014; Ireland is blank in the R&R source and drops out). The
feature matrix is identical in both arms and only the label differs, so any difference in results comes
from the crisis definition:

    me_merged_{base,robust}_RR     R&R label
    me_merged_{base,robust}_LViso  the same rows with the L&V label of the main run

data/crisis/clean/crisis_panel_RR.csv was built from data/crisis/raw/RR_source.xlsx by
08_Crisis_dataset_RR.ipynb (July 2026, thesis). The earlier R&R results merged the label onto the
pre-correction micro panel; this script replaces that step so the check uses the corrected sample.

    python tools/build_rr_panels.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ENG = ROOT / "data" / "engineered" / "parquet_saves"

rr = pd.read_csv(ROOT / "data" / "crisis" / "clean" / "crisis_panel_RR.csv")
assert rr["crisis"].notna().all(), "R&R label has missing values"
rr = rr.rename(columns={"country_iso3": "country_iso", "crisis": "crisis_rr"})

for spec in ["base", "robust"]:
    me = pd.read_parquet(ENG / f"me_merged_{spec}.parquet")
    both = me.merge(rr, on=["country_iso", "year"], how="inner", validate="many_to_one")
    lviso = both.drop(columns="crisis_rr")
    rr_arm = both.assign(crisis=both["crisis_rr"].astype(int)).drop(columns="crisis_rr")
    assert lviso.drop(columns="crisis").equals(rr_arm.drop(columns="crisis")), "feature matrices differ"
    rr_arm.to_parquet(ENG / f"me_merged_{spec}_RR.parquet")
    lviso.to_parquet(ENG / f"me_merged_{spec}_LViso.parquet")
    print(f"{spec}: {len(both)} bank-years, {both['bank_id'].nunique()} banks, "
          f"{both['country_iso'].nunique()} countries, {both['year'].min()}-{both['year'].max()} | "
          f"crisis share R&R {rr_arm['crisis'].mean():.1%}, L&V {lviso['crisis'].mean():.1%}")
    print("  crisis bank-years by year (R&R / L&V):")
    by = pd.DataFrame({"RR": rr_arm.groupby("year")["crisis"].sum(), "LV": lviso.groupby("year")["crisis"].sum()})
    print("  " + by.T.to_string().replace("\n", "\n  "))
