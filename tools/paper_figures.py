"""
Figures for Section 5 of the IJF paper (drafts, 25-09-2026).

Figure A  Mean AUROC per configuration across specifications, test years 2011-2012 (the years every
          specification shares). Dot = reported seed (42), bar = five-seed mean, line = range over the five seeds.
          Same numbers as the robustness table, so the two can be compared side by side.
Figure B  Share of SHAP attribution taken by the bank-level block, per model, in the integrated
          configuration (baseline and extended set, lag 1). Bar = seed 42, whisker = five-seed range.
          Shares are within-model (each model's |SHAP| sums to 100%) before averaging, as in NB15.
Figure C  Where the attribution goes when the indicator set is extended: per model a baseline and an
          extended 100% bar, the extended one split into bank-level, macroeconomic already in the baseline,
          and the four added macroeconomic indicators (seed 42). Replaces the earlier dumbbell version.

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
# Times New Roman to match the manuscript (elsarticle 'times' option; IJF artwork guide lists Times New
# Roman). pdf.fonttype 42 embeds the font as TrueType, as the guide asks for embedded fonts.
plt.rcParams.update({"font.family": "Times New Roman", "mathtext.fontset": "stix", "pdf.fonttype": 42,
                     "font.size": 9, "axes.edgecolor": MUTED,
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
        mean5 = g.auroc.mean()
        yy = y + offs[cfg]
        ax.plot([lo, hi], [yy, yy], color=COL[cfg], lw=2, solid_capstyle="round", zorder=2)
        ax.plot(v42, yy, MARK[cfg], color=COL[cfg], ms=6.5, mec="white", mew=1.2, zorder=3)
        ax.plot(mean5, yy, "|", color=INK, ms=9, mew=1.4, zorder=4)   # five-seed mean
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
fig.text(0.01, 0.005, "Dot: reported seed (42). Black bar: mean over the five seeds. Line: range over the five seeds.",
         color=MUTED, fontsize=7.5)
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
                       extended=pm.loc[key, "Micro block 11b (%)"], added_macro=pm.loc[key, "Added macro (%)"]))
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
           plt.Rectangle((0, 0), 1, 1, color=COL["macro"], label="Macroeconomic (macro) block"),
           Line2D([0], [0], color=INK, lw=1.4, label="Micro share, range over five seeds")]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.01))
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext in ["pdf", "png"]:
    fig.savefig(OUT / f"figB_shap_micro_share.{ext}", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- Figure C
# Where the attribution goes when the indicator set is extended (integrated configuration, lag 1, seed 42).
# Per model two 100% bars: baseline set (bank-level | macroeconomic) and extended set (bank-level | macroeconomic
# already in the baseline | the four added macroeconomic indicators). The added block is a lighter, hatched purple:
# it is macroeconomic too, and the hatch keeps it distinguishable without colour. The extended bank-level block
# includes the three added bank-level indicators (about 1% together).
NEW = "#B3A6E6"
fig, ax = plt.subplots(figsize=(6.5, 4.4))
h, gap = 0.34, 0.04
yt, yl = [], []
for j_, (_, lab) in enumerate(MODELS):
    y = (len(MODELS) - 1 - j_) * 1.0
    g = B[(B.model == lab) & (B.seed == 42)].iloc[0]
    mb, me, am = g.baseline, g.extended, g.added_macro
    yb, ye = y + h / 2 + gap / 2, y - h / 2 - gap / 2
    ax.barh(yb, mb, height=h, color=COL["micro"], lw=0)
    ax.barh(yb, 100 - mb, left=mb, height=h, color=COL["macro"], lw=0)
    ax.barh(ye, me, height=h, color=COL["micro"], lw=0)
    ax.barh(ye, 100 - me - am, left=me, height=h, color=COL["macro"], lw=0)
    ax.barh(ye, am, left=100 - am, height=h, color=NEW, hatch="////", edgecolor="white", lw=0)
    ax.text(101.5, yb, f"{mb:.0f}%", va="center", fontsize=7.5, color=INK)
    ax.text(101.5, ye, f"{me:.0f}%", va="center", fontsize=7.5, color=INK)
    ax.text(100 - am / 2, ye, f"{am:.0f}%", va="center", ha="center", fontsize=7, color=INK,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
    ax.text(-1.5, yb, "Baseline", va="center", ha="right", fontsize=7, color=MUTED)
    ax.text(-1.5, ye, "Extended", va="center", ha="right", fontsize=7, color=MUTED)
    yt.append(y); yl.append(lab)
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=9)
ax.tick_params(axis="y", length=0, pad=42)
ax.axhline(0.5, color=GRID, lw=1)
ax.set_xlim(0, 108); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("Share of the attribution in the integrated configuration (%)")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
handles = [plt.Rectangle((0, 0), 1, 1, color=COL["micro"], label="Bank-level indicators"),
           plt.Rectangle((0, 0), 1, 1, color=COL["macro"], label="Macroeconomic indicators (baseline set)"),
           plt.Rectangle((0, 0), 1, 1, facecolor=NEW, hatch="////", edgecolor="white", label="Macroeconomic indicators added in the extended set")]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.42, 1.0), ncol=2, frameon=False, fontsize=7.5)
fig.tight_layout()
for ext in ["pdf", "png"]:
    fig.savefig(OUT / f"figC_displacement.{ext}", dpi=200)
plt.close(fig)

# sanity check against the robustness table (seed 42, baseline lag 1: 0.853 / 0.733 / 0.783)
chk = A[(A.seed == 42) & (A.spec == "11a") & (A.variant == "baseline_t1")].set_index("config").auroc.round(3)
print("seed 42 baseline lag 1:", chk.to_dict())
print("saved to", OUT)
