"""Regenerate the README figures from the files in data/.

    pip install numpy matplotlib
    python figures/make_figures.py
"""
import csv
import glob
import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures")

MADE, MISS = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.labelcolor": MUTED, "axes.labelsize": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlecolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "legend.frameon": False, "legend.fontsize": 9,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "figure.dpi": 100, "savefig.dpi": 200,
})


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "free_throws.csv"), encoding="utf-8")))
    for r in rows:
        r["made"] = r["made"] == "1"
        for k in ("entry_lr_ft", "entry_sl_ft", "entry_angle_deg"):
            r[k] = float(r[k]) if r[k] else None
    return rows


def ygrid(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def suptitle(fig, title, sub):
    fig.text(0.012, 0.975, title, fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.012, 0.925, sub, fontsize=10, color=MUTED, va="top")


# ------------------------------------------------------------------ figure 1: what is in the dataset
def fig_coverage(rows):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.9), gridspec_kw=dict(width_ratios=[1, 1.25], wspace=0.3))
    fig.subplots_adjust(left=0.2, right=0.975, top=0.76, bottom=0.12)
    suptitle(fig, "What is in the dataset",
             "%s free throws from %d shooters. Every shot has the outcome; subsets carry each measurement."
             % (format(len(rows), ","), len({r["player"] for r in rows})))

    groups = [
        ("All free throws", rows),
        ("Left/right rim entry", [r for r in rows if r["entry_lr_ft"] is not None]),
        ("Short/long entry and angle", [r for r in rows if r["entry_sl_ft"] is not None]),
        ("3D pose tracking", [r for r in rows if r["has_pose"] == "1"]),
    ]
    y = np.arange(len(groups))[::-1]
    made = np.array([sum(r["made"] for r in g) for _, g in groups])
    miss = np.array([sum(not r["made"] for r in g) for _, g in groups])
    a.barh(y, made, height=0.56, color=MADE, label="Made")
    a.barh(y, miss, left=made, height=0.56, color=MISS, label="Missed", edgecolor="white", linewidth=1.5)
    for yi, m, x in zip(y, made, miss):
        a.text(m + x + 22, yi, format(m + x, ","), va="center", ha="left", color=INK, fontsize=10)
    a.set_yticks(y)
    a.set_yticklabels([g[0] for g in groups], color=INK, fontsize=10)
    a.set_xlim(0, 1700)
    a.set_xlabel("Free throws")
    a.set_title("Shots by measurement available", pad=26)
    a.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, handlelength=1, columnspacing=1.2, borderaxespad=0)
    a.grid(axis="x", color=GRID, linewidth=0.8)
    a.set_axisbelow(True)
    a.spines["left"].set_visible(False)
    a.tick_params(axis="y", length=0)

    per = Counter(r["player"] for r in rows)
    counts = np.array(sorted(per.values()))
    bins = np.arange(0.5, counts.max() + 2.5, 2)
    b.hist(counts, bins=bins, color=MADE, edgecolor="white", linewidth=1)
    med = float(np.median(counts))
    b.axvline(med, color=INK, linewidth=1, linestyle=(0, (4, 3)))
    b.text(med + 0.8, b.get_ylim()[1]*0.93, "median %g shots" % med, color=INK, fontsize=9.5, va="top")
    top = per.most_common(1)[0]
    b.annotate("%s, %d" % top, xy=(top[1], 1), xytext=(top[1], b.get_ylim()[1]*0.30), ha="right", color=INK, fontsize=9.5,
               arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8))
    b.set_xlabel("Free throws per shooter")
    b.set_ylabel("Shooters")
    b.set_title("Most shooters appear a handful of times", pad=26)
    ygrid(b)
    fig.savefig(os.path.join(OUT, "coverage.png"))
    plt.close(fig)


# ------------------------------------------------------------------ figure 2: rim entry
def hist_pair(ax, rows, key, bins, xlabel, title):
    made = np.array([r[key] for r in rows if r[key] is not None and r["made"]])
    miss = np.array([r[key] for r in rows if r[key] is not None and not r["made"]])
    ax.hist(made, bins=bins, density=True, color=MADE, alpha=0.30)
    ax.hist(made, bins=bins, density=True, histtype="step", color=MADE, linewidth=1.8, label="Made (n = %s)" % format(len(made), ","))
    ax.hist(miss, bins=bins, density=True, histtype="step", color=MISS, linewidth=1.8, label="Missed (n = %d)" % len(miss))
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density")
    ax.set_title(title, pad=8)
    ax.legend(loc="upper right", handlelength=1.3, borderaxespad=0)
    ygrid(ax)


def fig_entry(rows):
    fig = plt.figure(figsize=(11, 8.2))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.15, 1], left=0.07, right=0.975, top=0.86, bottom=0.075, hspace=0.72, wspace=0.26)
    both = [r for r in rows if r["entry_lr_ft"] is not None and r["entry_sl_ft"] is not None]
    suptitle(fig, "Where the ball enters the rim",
             "Position of the ball as it comes down through rim height, and its descent angle. All values are estimates.")

    ax = fig.add_subplot(gs[:, 0])
    ax.add_patch(Circle((0, 0), 0.75, fill=False, edgecolor=INK, linewidth=2.2, zorder=3))
    for made, col, lab in ((True, MADE, "Made"), (False, MISS, "Missed")):
        g = [r for r in both if r["made"] == made]
        ax.scatter([r["entry_lr_ft"] for r in g], [r["entry_sl_ft"] for r in g], s=30, color=col, alpha=0.8,
                   edgecolor="white", linewidth=0.7, label="%s (n = %d)" % (lab, len(g)), zorder=4 if not made else 2)
    lim = 1.55
    ax.set_xlim(lim, -lim)                                   # positive = shooter's left, drawn on the left
    ax.set_ylim(lim, -lim)                                   # positive = short, drawn toward the shooter
    ax.set_aspect("equal")
    ax.axhline(0, color=GRID, linewidth=0.8, zorder=0)
    ax.axvline(0, color=GRID, linewidth=0.8, zorder=0)
    ax.set_xlabel("Left/right of rim centre (ft)   ← shooter's left · shooter's right →")
    ax.set_ylabel("Short/long of rim centre (ft)   ← short · long →")
    ax.set_title("Seen from above, shooter at the bottom. Circle = rim (n = %d)" % len(both), pad=8)
    ax.legend(loc="upper left", handletextpad=0.3, borderaxespad=0.2)

    hist_pair(fig.add_subplot(gs[0, 1]), rows, "entry_lr_ft", np.arange(-1.5, 1.5001, 0.1),
              "Left/right of rim centre (ft), positive = shooter's left", "Left/right entry")
    hist_pair(fig.add_subplot(gs[1, 1]), rows, "entry_sl_ft", np.arange(-1.5, 1.5001, 0.1),
              "Short/long of rim centre (ft), positive = short", "Short/long entry")
    hist_pair(fig.add_subplot(gs[2, 1]), rows, "entry_angle_deg", np.arange(34.5, 63.5, 1),
              "Descent angle at rim height (degrees from horizontal)", "Entry angle")
    fig.savefig(os.path.join(OUT, "rim_entry.png"))
    plt.close(fig)


# ------------------------------------------------------------------ figure 3: pose-derived measures
def angle(a, b, c):
    u, v = np.asarray(a) - b, np.asarray(c) - b
    return float(np.degrees(np.arccos(np.clip(u @ v/(np.linalg.norm(u)*np.linalg.norm(v)), -1, 1))))


def pose_metrics():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "pose", "*.json"))):
        o = json.load(open(f, encoding="utf-8"))
        T = {t["frame"]: t["data"] for t in o["tracking"]}
        d = T.get(0, {})
        if "L_WRIST" not in d or "R_WRIST" not in d:
            continue
        s = "R" if d["R_WRIST"][2] >= d["L_WRIST"][2] else "L"          # the arm whose wrist is higher at release
        m = dict(wrist=d[s + "_WRIST"][2], elbow=None, knee=None)
        if s + "_SHOULDER" in d and s + "_ELBOW" in d:
            m["elbow"] = angle(d[s + "_SHOULDER"], d[s + "_ELBOW"], d[s + "_WRIST"])
        knees = []
        for fr, x in T.items():
            if fr <= 0 and all(k in x for k in ("L_HIP", "L_KNEE", "L_ANKLE", "R_HIP", "R_KNEE", "R_ANKLE")):
                knees.append((angle(x["L_HIP"], x["L_KNEE"], x["L_ANKLE"]) + angle(x["R_HIP"], x["R_KNEE"], x["R_ANKLE"]))/2)
        if knees:
            m["knee"] = min(knees)
        out.append(m)
    return out


def fig_pose():
    M = pose_metrics()
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.3))
    fig.subplots_adjust(left=0.06, right=0.98, top=0.74, bottom=0.15, wspace=0.28)
    suptitle(fig, "Shooting form, measured from the 3D pose files",
             "One value per shot (n = %d). Examples of what the joint tracks support; computed in figures/make_figures.py." % len(M))
    panels = [
        ("wrist", np.arange(4.0, 9.01, 0.2), "Height of the higher wrist above the floor (ft)", "Wrist height at release", "%.1f ft"),
        ("elbow", np.arange(60, 181, 5), "Shoulder–elbow–wrist angle of that arm (degrees)", "Elbow angle at release", "%.0f°"),
        ("knee", np.arange(75, 176, 5), "Hip–knee–ankle angle (degrees), 180 = straight", "Deepest knee bend before release", "%.0f°"),
    ]
    for ax, (k, bins, xl, title, fmt) in zip(axes, panels):
        v = np.array([m[k] for m in M if m[k] is not None])
        v = v[(v >= bins[0]) & (v <= bins[-1])]
        ax.hist(v, bins=bins, color=MADE, edgecolor="white", linewidth=1)
        med = float(np.median(v))
        top = ax.get_ylim()[1]*1.12
        ax.set_ylim(0, top)
        ax.axvline(med, color=INK, linewidth=1, linestyle=(0, (4, 3)))
        left = med > (bins[0] + bins[-1])/2
        ax.text(med + (-1 if left else 1)*(bins[-1] - bins[0])*0.025, top*0.97, "median " + fmt % med, color=INK, fontsize=9.5,
                va="top", ha="right" if left else "left")
        ax.set_xlabel(xl)
        ax.set_title(title, pad=8)
        ygrid(ax)
    axes[0].set_ylabel("Shots")
    fig.savefig(os.path.join(OUT, "shooting_form.png"))
    plt.close(fig)


if __name__ == "__main__":
    rows = load()
    fig_coverage(rows)
    fig_entry(rows)
    fig_pose()
    print("wrote coverage.png, rim_entry.png, shooting_form.png")
