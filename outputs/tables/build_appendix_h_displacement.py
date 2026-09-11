"""Build Appendix H Tables 3 and 4 from the SHAP displacement export.

Source : results_tables/shap_displacement_11a_11b.xlsx  (written by NB15 cells 62-63)
Output : results_tables/appendix_h_displacement.xlsx     (+ one CSV per table)

Three things this does beyond re-formatting:

1. COLUMNS ARE RESOLVED BY PATTERN, not by exact name. The headers in the source have already been
   renamed once by hand (11a/11b -> baseline/extended), which broke an earlier exact-name version of
   this script. Matching on distinctive word combinations means the next rename does not break it
   either, and it fails loudly with the available columns listed if a match is genuinely missing.

2. It COMPUTES the "delta retained micro" column, which the export leaves empty. The extended
   micro-block share ALREADY INCLUDES the newly added micro variables, so the headline block change
   understates what happened to the variables present in both sets:

       delta retained = (micro block extended - new micro) - micro block baseline

   For LR that turns a -5.44 pp block change into a -8.09 pp fall in the retained variables.
   "Retained" = the 14 micro variables in both sets (baseline has 15, extended 17; l_loans was
   dropped and three were added). That definition belongs in the table note.

3. Publication labels for Table 3 come from `appendix_direction_11b.csv`, matched on the variable
   Code -- NOT invented here. Those labels are already vetted and already printed in the manuscript
   as Appendix H Tables 1-2, so reusing them guarantees the three tables name variables identically.
"""
import pandas as pd
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "shap_displacement_11a_11b.xlsx")
DIRECTION = os.path.join(BASE, "appendix_direction_11b.csv")
SHAP_11A = os.path.join(os.path.dirname(BASE), "model_featurecontribution",
                        "outputs_11a", "shap_values_11a.parquet")
OUT = os.path.join(BASE, "appendix_h_displacement.xlsx")

# The extension is not a pure addition: l_loans is DROPPED (baseline micro 15 -> extended 17;
# l_loans out, cr_impchg + r_loans_dep + l_obsi in). Nothing is dropped on the macro side.
# So a naive retained comparison mixes displacement with the mechanical loss of a removed variable.
DROPPED = "l_loans"
# Macro is an explicit list and micro is its complement -- mirroring NB11. Never use name prefixes
# (inc_nii, inc_op and cr_impchg match none of the micro prefixes and would be counted as macro).
MACRO_FEATURES = {"NGDP_RPCH", "NGDPD", "PCPIPCH", "LUR", "BCA_NGDPD",
                  "BIS_REER", "RXF11FX_REVS", "reer_g", "fx_g"}
MODEL_LABEL = {"logistic_regression": "LR", "decision_tree": "DT", "random_forest": "RF",
               "xgboost": "XGBoost", "lightgbm": "LightGBM", "mlp": "MLP"}


def dropped_variable_share():
    """Baseline attribution share of the dropped variable, per model, as a percentage.

    Uses NB15's convention: each model's mean |SHAP| is normalised to sum to 1 BEFORE anything is
    compared across models. Verified to reproduce the micro-block baseline shares in the source
    export exactly, which is what confirms the convention matches.
    """
    df = pd.read_parquet(SHAP_11A)
    df = df[(df["variant"] == "baseline_t1") & (df["feature_set"] == "integrated")]
    shap_cols = [c for c in df.columns if c.startswith("shap_")]
    out = {}
    for m, g in df.groupby("model_name"):
        mean_abs = g[shap_cols].abs().mean()
        shares = mean_abs / mean_abs.sum()
        out[MODEL_LABEL.get(m, m)] = 100 * shares["shap_" + DROPPED]
    return pd.Series(out)


def pick(columns, *alternatives, must_not=()):
    """Return the single column matching any one of the `alternatives`.

    Each alternative is a list of fragments that must ALL appear (case-insensitive substring match);
    `must_not` fragments must appear in none. Alternatives are tried in order, which lets one call
    accept several naming schemes -- the source headers have already flipped once between NB15's
    own names ("Micro block 11a (%)") and hand-edited ones ("Micro block: baseline (%)"), and a
    re-run of NB15 restores the originals. Raises with the full column list if nothing matches
    uniquely, so a rename surfaces loudly rather than silently selecting the wrong column.
    """
    for must_have in alternatives:
        hits = [c for c in columns
                if all(f.lower() in str(c).lower() for f in must_have)
                and not any(f.lower() in str(c).lower() for f in must_not)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise KeyError("ambiguous match for %s: %s" % (must_have, hits))
    raise KeyError("no unique column for any of %s (excluding %s). Available: %s"
                   % (list(alternatives), must_not, list(columns)))


# ---------------------------------------------------------------- Table 3: added features
added = pd.read_excel(SRC, sheet_name="Added features")
c_code = pick(added.columns, ["code"])
c_level = pick(added.columns, ["level"])
c_share = pick(added.columns, ["share"])
c_rank = pick(added.columns, ["rank"])
c_feat = pick(added.columns, ["feature"])

labels = (pd.read_csv(DIRECTION, encoding="utf-8-sig")
            .set_index("Code")["Variable"].to_dict())
missing = [c for c in added[c_code] if c not in labels]
if missing:
    print("!! no vetted label in appendix_direction_11b.csv for: %s "
          "(falling back to the export's own name)" % missing)
added["Variable"] = [labels.get(c, n) for c, n in zip(added[c_code], added[c_feat])]

table3 = (added[["Variable", c_level, c_share, c_rank]]
          .rename(columns={c_level: "Level",
                           c_share: "Share of total attribution (%)",
                           c_rank: "Rank (of 30)"})
          # Macro block first, then Micro; each ordered by rank, so the contrast reads top-to-bottom
          # (ranks 4-8 then 18-25). "Macro" sorts before "Micro" alphabetically, hence ascending.
          .sort_values(["Level", "Rank (of 30)"], ascending=[True, True])
          .reset_index(drop=True))
table3["Share of total attribution (%)"] = table3["Share of total attribution (%)"].round(2)

# ---------------------------------------------------------------- Table 4: per model
per = pd.read_excel(SRC, sheet_name="Per model")
c_model = pick(per.columns, ["model"])
c_nmacro = pick(per.columns, ["macro"])
c_nmicro = pick(per.columns, ["micro"], must_not=["block", "retained"])
c_base = pick(per.columns, ["block", "baseline"], ["block", "11a"])
c_ext = pick(per.columns, ["block", "extended"], ["block", "11b"])
c_dblock = pick(per.columns, ["block", "pp"])

# Compute the retained-micro change per model. The MEAN row is then the mean OF THE PER-MODEL VALUES,
# not a recomputation from already-averaged shares -- averaging an average of ratios is the shape of
# the pooling error found on 29-07, so it is avoided here deliberately.
body = per[per[c_model].astype(str).str.upper() != "MEAN"].copy()

# Baseline share of the dropped variable, aligned to this table's model labels.
drop_share = dropped_variable_share()
body["Dropped variable: baseline (%)"] = body[c_model].map(drop_share)
if body["Dropped variable: baseline (%)"].isna().any():
    raise ValueError("could not match model labels to the SHAP file: %s vs %s"
                     % (list(body[c_model]), list(drop_share.index)))

# Like-for-like: remove the dropped variable from the BASELINE side and the new variables from the
# EXTENDED side, so both cover the same 14 micro variables. Without this the column would charge the
# extension for losing a variable that was simply taken out of the set.
body["Δ retained micro (pp)"] = (
    (body[c_ext] - body[c_nmicro]) - (body[c_base] - body["Dropped variable: baseline (%)"])
)

mean_row = per[per[c_model].astype(str).str.upper() == "MEAN"].copy()
if len(mean_row):
    # Mean OF THE PER-MODEL VALUES, not a recomputation from already-averaged shares -- averaging an
    # average of ratios is the shape of the pooling error found on 29-07.
    mean_row["Dropped variable: baseline (%)"] = body["Dropped variable: baseline (%)"].mean()
    mean_row["Δ retained micro (pp)"] = body["Δ retained micro (pp)"].mean()

table4 = pd.concat([body, mean_row], ignore_index=True).rename(columns={
    c_model: "Model",
    c_nmacro: "New macro (% of total)",
    c_nmicro: "New micro (% of total)",
    c_base: "Micro block: baseline (%)",
    c_ext: "Micro block: extended (%)",
    c_dblock: "Δ micro block (pp)",
})
table4 = table4[["Model", "New macro (% of total)", "New micro (% of total)",
                 "Micro block: baseline (%)", "Micro block: extended (%)",
                 "Δ micro block (pp)", "Dropped variable: baseline (%)",
                 "Δ retained micro (pp)"]]
for c in table4.columns[1:]:
    table4[c] = table4[c].astype(float).round(2)

# ---------------------------------------------------------------- export
with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    table3.to_excel(w, sheet_name="Table 3 added features", index=False)
    table4.to_excel(w, sheet_name="Table 4 per model", index=False)
table3.to_csv(os.path.join(BASE, "appendix_h_table3_added_features.csv"), index=False)
table4.to_csv(os.path.join(BASE, "appendix_h_table4_per_model.csv"), index=False)

print("=" * 100)
print("TABLE 3. Attribution Share of the Variables Added by the Extended Indicator Set (lag-1).")
print("=" * 100)
print(table3.to_string(index=False))
print("\n" + "=" * 100)
print("TABLE 4. Micro-Block Attribution Before and After Extension, by Model (lag-1).")
print("=" * 100)
print(table4.to_string(index=False))
print("\nwrote %s (+ 2 CSVs)" % os.path.basename(OUT))
