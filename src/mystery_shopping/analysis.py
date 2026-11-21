"""Channel performance, registry vs ancillary comparison, consistency, gaps, NPS demo, scorecards and charts."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from scipy import stats  # noqa: E402

from . import framework as F  # noqa: E402

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CH_COLOR = dict(zip(F.CHANNELS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
WAVE_COLOR = {"Wave 1": "#86b6ef", "Wave 2": "#1c5cab"}
DIV = LinearSegmentedColormap.from_list("div", ["#c23b3a", "#e88d8c", "#f0efec", "#86b6ef", "#1c5cab"])
GOOD, BAD = "#0ca30c", "#d03b3b"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 24,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "legend.frameon": False, "legend.fontsize": 9, "legend.labelcolor": INK2,
})
NOTE = "SYNTHETIC mystery-shopping data for demonstration. Not real results for any organisation."
DIM_COLS = [f"score_{d}" for d in F.DIMENSIONS]


def _finish(fig, path, note=NOTE):
    r = fig.canvas.get_renderer()
    y = (fig.get_tightbbox(r).y0 - 0.12) / fig.get_figheight()
    fig.text(0.01, y, note, fontsize=7.5, color=MUTED, ha="left", va="top", transform=fig.transFigure)
    fig.savefig(path, dpi=160, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def _sub(ax, t):
    ax.text(0, 1.015, t, transform=ax.transAxes, fontsize=9, color=INK2, va="bottom")


def nps_value(s: pd.Series) -> float:
    s = s.dropna().astype(int)
    return float(100 * ((s >= 9).mean() - (s <= 6).mean())) if len(s) else float("nan")


def mean_ci(x: pd.Series) -> tuple[float, float, float]:
    x = x.dropna()
    m = x.mean()
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan
    return m, m - h, m + h


def channel_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ch in [*F.CHANNELS, "All channels"]:
        g = df if ch == "All channels" else df[df["channel"] == ch]
        m, lo, hi = mean_ci(g["sqi"])
        rows.append({"channel": ch, "visits": len(g), "sqi": round(m, 1), "ci_low": round(lo, 1), "ci_high": round(hi, 1),
                     "visits_meeting_target_pct": round(100 * (g["sqi"] >= F.TARGET_SCORE).mean(), 1),
                     "response_standard_met_pct": round(100 * g["meets_response_standard"].mean(), 1),
                     "median_response_min": round(g["response_time_min"].median(), 1),
                     "first_contact_resolution_pct": round(100 * (g["RE1"] == 2).mean(), 1),
                     "sqi_sd": round(g["sqi"].std(), 1), "sqi_cv_pct": round(100 * g["sqi"].std() / g["sqi"].mean(), 1),
                     "critical_visits_pct": round(100 * (g["sqi"] < 60).mean(), 1), "nps_demo": round(nps_value(g["likelihood_to_recommend"]), 1)})
    return pd.DataFrame(rows)


def registry_vs_ancillary(df: pd.DataFrame) -> pd.DataFrame:
    a, b = df[df["channel"] == "Registry"], df[df["channel"] == "Ancillary services"]
    rows = []
    for d, col in [*zip(F.DIMENSIONS, DIM_COLS), ("Service Quality Index", "sqi")]:
        x, y = a[col].dropna(), b[col].dropna()
        t = stats.ttest_ind(x, y, equal_var=False)
        pooled = np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2)
        rows.append({"measure": d, "registry": round(x.mean(), 1), "ancillary": round(y.mean(), 1), "gap": round(x.mean() - y.mean(), 1),
                     "cohens_d": round((x.mean() - y.mean()) / pooled, 2), "p_value": round(float(t.pvalue), 4), "significant_5pct": bool(t.pvalue < 0.05)})
    return pd.DataFrame(rows)


def wave_change(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ch in F.CHANNELS:
        g = df[df["channel"] == ch]
        x, y = g[g["wave"] == "Wave 1"]["sqi"], g[g["wave"] == "Wave 2"]["sqi"]
        t = stats.ttest_ind(y, x, equal_var=False)
        rows.append({"channel": ch, "wave_1": round(x.mean(), 1), "wave_2": round(y.mean(), 1), "change": round(y.mean() - x.mean(), 1),
                     "p_value": round(float(t.pvalue), 4), "significant_5pct": bool(t.pvalue < 0.05)})
    return pd.DataFrame(rows)


def shopper_calibration(df: pd.DataFrame) -> pd.DataFrame:
    """Assessor consistency: each shopper's mean SQI residual after removing channel and wave effects."""
    resid = df["sqi"] - df.groupby(["channel", "wave"])["sqi"].transform("mean")
    t = df.assign(resid=resid).groupby("shopper_id").agg(visits=("visit_id", "count"), mean_residual=("resid", "mean"), sd=("resid", "std")).reset_index()
    t["se"] = t["sd"] / np.sqrt(t["visits"])
    t["z"] = t["mean_residual"] / t["se"]
    t["flag"] = np.where(t["z"] > 2.5, "Lenient: review calibration", np.where(t["z"] < -2.5, "Strict: review calibration", "Within range"))
    return t.round(2)


def criterion_pass_rates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cid, dim, q, chans in F.CRITERIA:
        for ch in chans:
            v = df.loc[df["channel"] == ch, cid].dropna()
            rows.append({"criterion": cid, "dimension": dim, "question": q, "channel": ch, "n": len(v),
                         "full_pass_pct": round(100 * (v == 2).mean(), 1), "fail_pct": round(100 * (v == 0).mean(), 1)})
    return pd.DataFrame(rows)


def run() -> dict:
    for d in (F.FIGURES, F.TABLES, F.SCORECARDS):
        d.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(F.DATA_CLEAN, encoding="utf-8-sig", parse_dates=["visit_date"])
    log = pd.read_csv(F.CLEANING_LOG)
    ch = channel_table(df)
    dims = df.groupby("channel")[DIM_COLS].mean().reindex(F.CHANNELS).round(1)
    dims.columns = F.DIMENSIONS
    rva = registry_vs_ancillary(df)
    waves = wave_change(df)
    shop = shopper_calibration(df)
    crit = criterion_pass_rates(df)
    gaps = crit.sort_values("full_pass_pct").head(10)
    tod = df.groupby(["channel", "time_of_day"])["sqi"].mean().unstack().round(1).reindex(F.CHANNELS)
    tod_test = stats.ttest_ind(df[df["time_of_day"] == "Morning"]["sqi"], df[df["time_of_day"] == "Afternoon"]["sqi"], equal_var=False)
    gap_matrix = (dims - F.TARGET_SCORE).round(1)
    nps_ch = df.groupby("channel")["nps_segment"].value_counts(normalize=True).mul(100).round(1).unstack().reindex(F.CHANNELS)[["Detractor", "Passive", "Promoter"]]

    tables = {"01_channel_performance": ch, "02_dimension_scores_by_channel": dims.reset_index(), "03_gap_to_target": gap_matrix.reset_index(),
              "04_registry_vs_ancillary": rva, "05_wave_comparison": waves, "06_shopper_calibration": shop, "07_criterion_pass_rates": crit,
              "08_top_10_gaps": gaps, "09_time_of_day": tod.reset_index(), "10_nps_demo_by_channel": nps_ch.reset_index(), "11_cleaning_log": log}
    for k, t in tables.items():
        t.to_csv(F.TABLES / f"{k}.csv", index=False, encoding="utf-8-sig")

    figs = {k: F.FIGURES / f"{i:02d}_{k}.png" for i, k in enumerate(
        ["sqi_by_channel", "dimension_heatmap", "registry_vs_ancillary", "response_standard", "wave_comparison", "consistency", "shopper_calibration", "top_gaps", "nps_demo"], 1)}

    # 1 SQI by channel with CI and target line
    t = ch[ch["channel"] != "All channels"].sort_values("sqi")
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    y = np.arange(len(t))
    ax.axvline(F.TARGET_SCORE, color=MUTED, linestyle=(0, (4, 3)), linewidth=1)
    ax.text(F.TARGET_SCORE + 0.5, len(t) - 0.4, f"Target {F.TARGET_SCORE}", color=INK2, fontsize=8.5)
    ax.hlines(y, t["ci_low"], t["ci_high"], color=[CH_COLOR[c] for c in t["channel"]], linewidth=2.4, alpha=0.6)
    ax.scatter(t["sqi"], y, s=80, color=[CH_COLOR[c] for c in t["channel"]], edgecolor=SURFACE, linewidth=2, zorder=3)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r["ci_high"] + 1, yi, f"{r['sqi']:.0f}  ({r['visits']} visits)", va="center", fontsize=9, color=INK2)
    ax.set_yticks(y, t["channel"])
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(40, 100)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_xlabel("Service Quality Index, 0-100 (dot = mean, line = 95% CI)")
    ax.set_title("Service Quality Index by channel")
    _finish(fig, figs["sqi_by_channel"])

    # 2 Heatmap: gap to target (diverging around target)
    fig, ax = plt.subplots(figsize=(9.2, 4.0))
    im = ax.imshow(gap_matrix.values, cmap=DIV, norm=TwoSlopeNorm(vcenter=0, vmin=-35, vmax=20), aspect="auto")
    for i in range(gap_matrix.shape[0]):
        for j in range(gap_matrix.shape[1]):
            sc, gp = dims.iat[i, j], gap_matrix.iat[i, j]
            dark = gp < -20
            ax.text(j, i, f"{sc:.0f}", ha="center", va="center", fontsize=11, fontweight="bold", color="#ffffff" if dark else INK)
    ax.set_xticks(range(len(F.DIMENSIONS)), [d.replace(" ", "\n", 1) for d in F.DIMENSIONS], fontsize=8.5)
    ax.set_yticks(range(len(F.CHANNELS)), F.CHANNELS)
    ax.tick_params(length=0, colors=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(F.DIMENSIONS)), minor=True)
    ax.set_yticks(np.arange(-.5, len(F.CHANNELS)), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=3)
    ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Points vs target (80)", color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, length=0)
    ax.set_title("Dimension scores by channel")
    _sub(ax, "Cell = mean score (0-100); colour = distance from the target of 80 (red below, blue above)")
    _finish(fig, figs["dimension_heatmap"])

    # 3 Registry vs Ancillary
    r = rva.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    yy = np.arange(len(r))
    ax.hlines(yy, r["ancillary"], r["registry"], color=AXIS, linewidth=3)
    ax.scatter(r["registry"], yy, s=80, color=CH_COLOR["Registry"], label="Registry", zorder=3, edgecolor=SURFACE, linewidth=2)
    ax.scatter(r["ancillary"], yy, s=80, color=CH_COLOR["Ancillary services"], label="Ancillary services", zorder=3, edgecolor=SURFACE, linewidth=2)
    for yi, (_, row) in zip(yy, r.iterrows()):
        ax.text(max(row["registry"], row["ancillary"]) + 1.5, yi, f"{row['gap']:+.0f}{'*' if row['significant_5pct'] else ''}", va="center", fontsize=9, color=INK2)
    ax.set_yticks(yy, r["measure"])
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(40, 100)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.12), ncol=2)
    ax.set_title("Registry vs ancillary services")
    _sub(ax, "Gap = registry minus ancillary; * = significant at 5% (Welch t-test)")
    _finish(fig, figs["registry_vs_ancillary"])

    # 4 Response standard compliance
    t = ch[ch["channel"] != "All channels"].set_index("channel").reindex(F.CHANNELS)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    x = np.arange(len(t))
    bars = ax.bar(x, t["response_standard_met_pct"], color=[CH_COLOR[c] for c in t.index], width=0.6, edgecolor=SURFACE, linewidth=2)
    for xi, (c, row) in zip(x, t.iterrows()):
        std = F.RESPONSE_STANDARD_MIN[c]
        label = f"≤{std // 60:.0f} h" if std >= 60 else f"≤{std} min"
        ax.text(xi, row["response_standard_met_pct"] + 2, f"{row['response_standard_met_pct']:.0f}%", ha="center", fontsize=9.5, color=INK)
        ax.text(xi, -12, f"standard {label}\nmedian {row['median_response_min']:g} min", ha="center", fontsize=7.5, color=INK2)
    ax.set_xticks(x, t.index)
    ax.tick_params(axis="x", pad=26)
    ax.set_ylim(0, 105)
    ax.set_ylabel("% of contacts within standard")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_title("Response-time standard met, by channel")
    _sub(ax, "Service standards are illustrative assumptions (see framework.py)")
    _finish(fig, figs["response_standard"])

    # 5 Wave comparison
    w = waves.set_index("channel").reindex(F.CHANNELS)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    x = np.arange(len(w))
    for off, wv, col in [(-0.19, "Wave 1", "wave_1"), (0.19, "Wave 2", "wave_2")]:
        ax.bar(x + off, w[col], width=0.36, color=WAVE_COLOR[wv], label=wv, edgecolor=SURFACE, linewidth=2)
    for xi, (_, row) in zip(x, w.iterrows()):
        ax.text(xi, max(row["wave_1"], row["wave_2"]) + 2, f"{row['change']:+.1f}{'*' if row['significant_5pct'] else ''}", ha="center", fontsize=9, color=INK)
    ax.axhline(F.TARGET_SCORE, color=MUTED, linestyle=(0, (4, 3)), linewidth=1)
    ax.set_xticks(x, w.index)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Mean SQI")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.1), ncol=2)
    ax.set_title("Change between evaluation waves")
    _sub(ax, "Label = change in points; * = significant at 5%")
    _finish(fig, figs["wave_comparison"])

    # 6 Consistency: distribution of visit SQI per channel (strip + box)
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    data = [df[df["channel"] == c]["sqi"].dropna() for c in F.CHANNELS]
    bp = ax.boxplot(data, vert=False, widths=0.5, patch_artist=True, showfliers=False, medianprops={"color": INK, "linewidth": 1.5})
    for patch, c in zip(bp["boxes"], F.CHANNELS):
        patch.set_facecolor(CH_COLOR[c])
        patch.set_alpha(0.35)
        patch.set_edgecolor(CH_COLOR[c])
    rng = np.random.default_rng(0)
    for i, (c, d) in enumerate(zip(F.CHANNELS, data), 1):
        ax.scatter(d, i + rng.uniform(-0.18, 0.18, len(d)), s=9, color=CH_COLOR[c], alpha=0.55, linewidth=0)
    ax.axvline(60, color=BAD, linestyle=(0, (2, 2)), linewidth=1)
    ax.text(60.5, 5.45, "Critical (<60)", color=BAD, fontsize=8)
    ax.set_yticks(range(1, len(F.CHANNELS) + 1), F.CHANNELS)
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.set_xlabel("Visit-level Service Quality Index")
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_title("Service consistency: spread of visit scores")
    _finish(fig, figs["consistency"])

    # 7 Shopper calibration
    s = shop.sort_values("mean_residual")
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    colors = [GOOD if f == "Within range" else BAD for f in s["flag"]]
    ax.axvline(0, color=AXIS)
    ax.hlines(range(len(s)), s["mean_residual"] - 1.96 * s["se"], s["mean_residual"] + 1.96 * s["se"], color=MUTED, linewidth=1.5)
    ax.scatter(s["mean_residual"], range(len(s)), color=colors, s=60, zorder=3, edgecolor=SURFACE, linewidth=1.5)
    for yi, (_, row) in enumerate(s.iterrows()):
        if row["flag"] != "Within range":
            ax.text(row["mean_residual"] + 1.96 * row["se"] + 0.8, yi, row["flag"], va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(s)), s["shopper_id"])
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.set_xlabel("Mean SQI difference vs other assessors on the same channel and wave")
    ax.set_title("Assessor calibration check")
    _sub(ax, "Flagged when |z| > 2.5: a quality-control step before results are reported")
    _finish(fig, figs["shopper_calibration"])

    # 8 Top gaps (criteria with lowest full-pass rate)
    g = gaps.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    yy = np.arange(len(g))
    ax.barh(yy, g["full_pass_pct"], color=[CH_COLOR[c] for c in g["channel"]], height=0.6, edgecolor=SURFACE, linewidth=2)
    for yi, (_, row) in zip(yy, g.iterrows()):
        ax.text(row["full_pass_pct"] + 1, yi, f"{row['full_pass_pct']:.0f}%", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(yy, [f"{r.channel} · {r.criterion}: {r.question[:58]}{'…' if len(r.question) > 58 else ''}" for r in g.itertuples()], fontsize=8)
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of visits fully meeting the criterion")
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_title("Ten largest service gaps (criterion level)")
    _finish(fig, figs["top_gaps"])

    # 9 NPS demo
    fig, ax = plt.subplots(figsize=(8.6, 3.5))
    yy = np.arange(len(nps_ch))[::-1]
    left = np.zeros(len(nps_ch))
    seg_col = {"Detractor": "#e34948", "Passive": "#c3c2b7", "Promoter": "#2a78d6"}
    for seg in ["Detractor", "Passive", "Promoter"]:
        v = nps_ch[seg].fillna(0).to_numpy()
        ax.barh(yy, v, left=left, color=seg_col[seg], height=0.6, edgecolor=SURFACE, linewidth=2, label=seg)
        for yi, l, vi in zip(yy, left, v):
            if vi >= 8:
                ax.text(l + vi / 2, yi, f"{vi:.0f}%", ha="center", va="center", fontsize=8.5, color="#ffffff" if seg != "Passive" else INK)
        left += v
    for yi, c in zip(yy, nps_ch.index):
        ax.text(101.5, yi, f"NPS {ch.set_index('channel').loc[c, 'nps_demo']:+.0f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(yy, nps_ch.index)
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 113)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, -0.13))
    ax.set_title("Likelihood to recommend (mystery-shopper NPS demonstration)")
    _sub(ax, "Shoppers' own 0-10 rating after each visit: a proxy, not a customer NPS")
    _finish(fig, figs["nps_demo"])

    # Channel scorecards (one PNG each)
    for c in F.CHANNELS:
        row = ch.set_index("channel").loc[c]
        fig = plt.figure(figsize=(8.6, 4.4))
        fig.text(0.03, 0.93, f"{c} scorecard", fontsize=15, fontweight="bold", color=INK)
        fig.text(0.03, 0.87, f"{int(row['visits'])} synthetic visits across two waves · target {F.TARGET_SCORE}", fontsize=9, color=INK2)
        kpis = [("Service Quality Index", f"{row['sqi']:.0f}", row["sqi"] >= F.TARGET_SCORE),
                ("Response standard met", f"{row['response_standard_met_pct']:.0f}%", row["response_standard_met_pct"] >= 80),
                ("First-contact resolution", f"{row['first_contact_resolution_pct']:.0f}%", row["first_contact_resolution_pct"] >= 70),
                ("NPS (demo)", f"{row['nps_demo']:+.0f}", row["nps_demo"] >= 0)]
        for i, (lab, val, ok) in enumerate(kpis):
            x0 = 0.03 + i * 0.24
            fig.patches.append(plt.Rectangle((x0, 0.58), 0.22, 0.24, transform=fig.transFigure, facecolor="#ffffff", edgecolor=GRID))
            fig.text(x0 + 0.015, 0.765, lab, fontsize=8.5, color=INK2)
            fig.text(x0 + 0.015, 0.64, val, fontsize=20, fontweight="bold", color=INK)
            fig.text(x0 + 0.2, 0.64, "✓" if ok else "!", fontsize=13, color=GOOD if ok else BAD, ha="right", fontweight="bold")
        ax = fig.add_axes([0.25, 0.13, 0.68, 0.38])
        v = dims.loc[c]
        ax.barh(range(len(v))[::-1], v.values, color=[GOOD if s >= F.TARGET_SCORE else BAD for s in v.values], height=0.6, alpha=0.85)
        ax.axvline(F.TARGET_SCORE, color=MUTED, linestyle=(0, (4, 3)), linewidth=1)
        for yi, s in zip(range(len(v))[::-1], v.values):
            ax.text(s + 1, yi, f"{s:.0f}", va="center", fontsize=8.5, color=INK2)
        ax.set_yticks(range(len(v))[::-1], v.index, fontsize=8.5)
        ax.tick_params(axis="y", colors=INK, length=0)
        ax.set_xlim(0, 105)
        ax.spines["left"].set_visible(False)
        fig.text(0.03, 0.01, NOTE + "  ✓ meets / ! below threshold", fontsize=7, color=MUTED)
        fig.savefig(F.SCORECARDS / f"scorecard_{c.lower().replace(' ', '_')}.png", dpi=160, facecolor=SURFACE)
        plt.close(fig)

    return {"df": df, "log": log, "ch": ch, "dims": dims, "gap_matrix": gap_matrix, "rva": rva, "waves": waves, "shop": shop, "crit": crit,
            "gaps": gaps, "tod": tod, "tod_p": float(tod_test.pvalue), "nps_ch": nps_ch, "figs": figs, "tables": tables}
