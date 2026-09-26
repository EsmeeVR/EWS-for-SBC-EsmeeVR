"""
Figures for Section 5 of the IJF paper (drafts, 25-09-2026).

Figure A  Mean AUROC per configuration across specifications, test years 2011-2012 (the years every
          specification shares). Dot = reported seed (42), line = range over the five seeds.
          Same numbers as the robustness table, so the two can be compared side by side.
Figure B  Share of SHAP attribution taken by the bank-level block, per model, in the integrated
          configuration (baseline and extended set, lag 1). Bar = seed 42, whisker = five-seed range.
          Shares are within-model (each model's |SHAP| sums to 100%) before averaging, as in NB15.

Reads only committed outputs of the five runs: outputs/results/11x/results_11x_final.xlsx and
outputs/tables/shap_displacement_11a_11b.xlsx in each worktree. Writes PDF + PNG to outputs/figures/paper/.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

H = Path(r"C:\Users\esmvr")
SEEDS = {42: H / "thesis-ews-final", 7: H / "thesis-ews-final-s7", 13: H / "thesis-ews-final-s13",
         27: H / "thesis-ews-final-s27", 99: H / "thesis-ews-final-s99"}
OUT = H / "thesis-ews-final" / "outputs" / "figures" / "paper"
OUT.mkdir(parents=True, exist_ok=True)

# Validated configuration palette (dataviz validator: all checks pass on white, 25-09-2026)
COL = {"micro": "#0094B3", "macro": "#5B3FC0", "integrated": "#C05E00"}
MARK = {"micro": "o", "macro": "s", "integrated": "D"}   # shape as a second cue next to colour
INK, MUTED, GRID = "#231F20", "#59595B", "#E3E4E6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": INK})

# ---------------------------------------------------------------- Figure A
SPECS = [("11a", "baseline_t1", "Baseline, lag 1"), ("11b", "baseline_t1", "Extended, lag 1"),
         ("11c", "baseline_t1", "Baseline, lag 2"), ("11d", "baseline_t1", "Extended, lag 2"),
         ("11a", "rt1", "Onset excluded, baseline, lag 1"), ("11b", "rt1", "Onset excluded, extended, lag 1"),
         ("11c", "rt1", "Onset excluded, baseline, lag 2"), ("11d", "rt1", "Onset excluded, extended, lag 2")]
rows = []
for seed, repo in SEEDS.items():
    for spec in ["11a", "11b", "11c", "11d"]:
        d = pd.read_excel(repo / f"outputs/results/{spec}/results_{spec}_final.xlsx", sheet_name="all_results")
        # lr_no_dummies is a comparison run stored in the same sheet, not one of the six models
        d = d[d.test_year.isin([2011, 2012]) & (d.model != "lr_no_dummies")]
        m = d.groupby(["variant", "dataset", "model"]).auroc.mean().groupby(["variant", "dataset"]).mean()
        for (variant, cfg), v in m.items():
            rows.append(dict(seed=seed, spec=spec, variant=variant, config=cfg, auroc=v))
A = pd.DataFrame(rows)
A.to_csv(OUT / "figA_auroc_across_specs_data.csv", index=False)

fig, ax = plt.subplots(figsize=(6.5, 4.6))
offs = {"micro": -0.22, "macro": 0.0, "integrated": 0.22}
ylabels = []
for i, (spec, variant, label) in enumerate(SPECS):
    y = len(SPECS) - 1 - i + (-0.6 if i >= 4 else 0)   # small gap between the two blocks
    ylabels.append((y, label))
    for cfg in ["micro", "macro", "integrated"]:
        g = A[(A.spec == spec) & (A.variant == variant) & (A.config == cfg)]
        lo, hi, v42 = g.auroc.min(), g.auroc.max(), g[g.seed == 42].auroc.iloc[0]
        yy = y + offs[cfg]
        ax.plot([lo, hi], [yy, yy], color=COL[cfg], lw=2, solid_capstyle="round", zorder=2)
        ax.plot(v42, yy, MARK[cfg], color=COL[cfg], ms=6.5, mec="white", mew=1.2, zorder=3)
ax.set_yticks([y for y, _ in ylabels]); ax.set_yticklabels([l for _, l in ylabels])
ax.axhline(3.2 - 0.6 + 0.1, color=GRID, lw=1)
ax.set_xlabel("Mean AUROC over the six models (test years 2011-2012)")
ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
handles = [Line2D([0], [0], marker=MARK[c], color=COL[c], lw=2, ms=6.5, mec="white", label=c.capitalize())
           for c in ["micro", "macro", "integrated"]]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=3, frameon=False)
fig.text(0.01, 0.005, "Dot: reported seed (42). Line: range over the five seeds.", color=MUTED, fontsize=7.5)
fig.tight_layout()
for ext in ["pdf", "png"]:
    fig.savefig(OUT / f"figA_auroc_across_specs.{ext}", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- Figure B
MODELS = [("LR", "LR"), ("DT", "DT"), ("RF", "RF"), ("XGBoost", "XGB"), ("LightGBM", "LGBM"), ("MLP", "MLP"), ("MEAN", "Mean")]
sh = []
for seed, repo in SEEDS.items():
    pm = pd.read_excel(repo / "outputs/tables/shap_displacement_11a_11b.xlsx", sheet_name="Per model").set_index("Model")
    for key, lab in MODELS:
        sh.append(dict(seed=seed, model=lab, baseline=pm.loc[key, "Micro block 11a (%)"],
                       extended=pm.loc[key, "Micro block 11b (%)"]))
B = pd.DataFrame(sh)
B.to_csv(OUT / "figB_shap_micro_share_data.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.2), sharey=True)
for ax, col, title in zip(axes, ["baseline", "extended"], ["Baseline set", "Extended set"]):
    for j, (_, lab) in enumerate(MODELS):
        y = len(MODELS) - 1 - j
        g = B[B.model == lab][col]
        v42 = B[(B.model == lab) & (B.seed == 42)][col].iloc[0]
        ax.barh(y, v42, height=0.62, color=COL["micro"], edgecolor="white", lw=0)
        ax.barh(y, 100 - v42, left=v42, height=0.62, color=COL["macro"], edgecolor="white", lw=0, alpha=0.9)
        ax.plot([g.min(), g.max()], [y, y], color=INK, lw=1.4, zorder=3)
        ax.text(102, y, f"{v42:.0f}%", va="center", fontsize=8, color=INK)
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.set_xlim(0, 112); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Share of attribution (%)")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.axhline(0.5, color=GRID, lw=1)
axes[0].set_yticks(range(len(MODELS))); axes[0].set_yticklabels([lab for _, lab in MODELS][::-1])
handles = [plt.Rectangle((0, 0), 1, 1, color=COL["micro"], label="Bank-level (micro) block"),
           plt.Rectangle((0, 0), 1, 1, color=COL["macro"], label="Country-level (macro) block"),
           Line2D([0], [0], color=INK, lw=1.4, label="Micro share, range over five seeds")]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.01))
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext in ["pdf", "png"]:
    fig.savefig(OUT / f"figB_shap_micro_share.{ext}", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- Figure C
# Displacement: bank-level share of attribution in the integrated configuration, baseline set (grey dot)
# against extended set (teal dot), per model, lag 1, seed 42. Values written next to each row, so the figure
# reads without the axis. Seed ranges are left out here (they are in figure B); the text states that the
# share falls in five of six models in every seed.
fig, ax = plt.subplots(figsize=(6.5, 3.1))
for j_, (_, lab) in enumerate(MODELS):
    y = len(MODELS) - 1 - j_
    g = B[(B.model == lab) & (B.seed == 42)]
    b42, e42 = g.baseline.iloc[0], g.extended.iloc[0]
    ax.plot([b42, e42], [y, y], color=GRID, lw=3, solid_capstyle="round", zorder=1)
    ax.plot(b42, y, "o", ms=8, color="#939598", mec="white", mew=1, zorder=3)
    ax.plot(e42, y, "o", ms=8, color=COL["micro"], mec="white", mew=1, zorder=3)
    ax.text(31, y, f"{b42:.1f}% → {e42:.1f}%", va="center", fontsize=8, color=INK)
ax.set_yticks(range(len(MODELS))); ax.set_yticklabels([lab for _, lab in MODELS][::-1])
ax.axhline(0.5, color=GRID, lw=1)
ax.set_xlim(-0.5, 38); ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
ax.set_xlabel("Share of the attribution that goes to the bank-level indicators (%)")
ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
handles = [Line2D([0], [0], marker="o", ls="", ms=8, color="#939598", label="Baseline indicator set"),
           Line2D([0], [0], marker="o", ls="", ms=8, color=COL["micro"], label="Extended indicator set")]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ["pdf", "png"]:
    fig.savefig(OUT / f"figC_displacement.{ext}", dpi=200)
plt.close(fig)

# sanity check against the robustness table (seed 42, baseline lag 1: 0.853 / 0.733 / 0.783)
chk = A[(A.seed == 42) & (A.spec == "11a") & (A.variant == "baseline_t1")].set_index("config").auroc.round(3)
print("seed 42 baseline lag 1:", chk.to_dict())
print("saved to", OUT)
