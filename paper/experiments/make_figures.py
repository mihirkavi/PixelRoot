"""
Data figures for PixelRoot, read from results/: the results plot (measured
robustness, operating curve, tamper-localization ROC, passive PRNU baseline) and
the adaptive local-edit example of E6.

The schematic figures (gain spectrum, M1-M3, datapath) are TikZ sources in
figures/src/ (build with figures/src/build.sh).

The figures are drawn at its printed size (IEEE two-column text width) with Times
text and math so that it matches the paper's typography; include them without
scaling.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
RES = os.path.join(HERE, "results")
ACC, GO, RD, GRAY = "#1F5FBF", "#1E7B3A", "#B3261E", "#8A8F98"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.3, "lines.markersize": 3.5,
    "legend.frameon": False, "pdf.fonttype": 42,
})


def read_csv(name):
    with open(os.path.join(RES, name)) as f:
        return list(csv.DictReader(f))


def jpeg_ber():
    qs, bers = [], []
    for line in open(os.path.join(RES, "e1_robustness.txt")):
        p = line.split()
        if len(p) >= 4 and p[0] == "JPEG" and p[1].startswith("Q") and p[1][1:].isdigit():
            qs.append(int(p[1][1:])); bers.append(float(p[2]))
    return qs, bers


def prnu():
    cond, gen, imp = [], [], []
    for line in open(os.path.join(RES, "e4_prnu.txt")):
        s = line.strip()
        for tag in ["clean", "JPEG Q95", "JPEG Q90", "JPEG Q70", "JPEG Q50"]:
            if s.startswith(tag + " "):
                p = s.split()
                cond.append(tag.replace("JPEG ", "")); gen.append(float(p[-3])); imp.append(float(p[-2]))
    return cond, gen, imp


def fig_results():
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 4.5))
    # (a) raw BER vs JPEG quality
    ax = axs[0, 0]
    qs, bers = jpeg_ber()
    ax.plot(qs, bers, "o-", color=ACC)
    ax.set_xlabel("JPEG quality $Q$"); ax.set_ylabel("raw coded-bit BER")
    ax.set_xticks([95, 80, 60, 40, 20, 10, 5]); ax.invert_xaxis(); ax.set_ylim(0, 0.25)
    ax.annotate("RS decodes the payload\ndown to $Q\\!=\\!10$", xy=(10, bers[qs.index(10)]),
                xytext=(52, 0.12), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6, color="0.3"))
    ax.set_title("(a) In-pixel channel vs. real JPEG (24 images)", loc="left")
    # (b) amplitude operating curve at JPEG Q40
    ax = axs[0, 1]
    rows = read_csv("e1_curve.csv")
    A = [float(r["A"]) for r in rows]
    ber = [float(r["raw_BER"]) for r in rows]
    dec = [int(r["decode"]) / int(r["n"]) for r in rows]
    l1, = ax.plot(A, ber, "s-", color=RD, label="raw BER")
    ax.set_xlabel("embedding amplitude $A$ (gray levels)"); ax.set_ylabel("raw BER", color=RD)
    ax.tick_params(axis="y", colors=RD); ax.set_ylim(0, 0.55)
    ax2 = ax.twinx()
    l2, = ax2.plot(A, dec, "^--", color=GO, label="payload decode rate")
    ax2.set_ylabel("payload decode rate", color=GO); ax2.tick_params(axis="y", colors=GO)
    ax2.set_ylim(0, 1.05); ax2.spines["top"].set_visible(False)
    ax.axvline(4, color=GRAY, lw=0.6, ls=":")
    ax.text(4.08, 0.06, "operating\npoint $A\\!=\\!4$", fontsize=7, color="0.3")
    ax.legend([l1, l2], [l1.get_label(), l2.get_label()], loc="center right")
    ax.set_title("(b) Amplitude operating curve at JPEG $Q\\!=\\!40$", loc="left")
    # (c) tamper-localization ROC
    ax = axs[1, 0]
    rows = read_csv("e3_roc.csv")
    ax.plot([float(r["fpr"]) for r in rows], [float(r["tpr"]) for r in rows], color=ACC, label="block level (AUC 0.97)")
    ax.plot([0, 1], [0, 1], ":", color=GRAY, lw=0.8, label="chance")
    ax.set_xlabel("false-positive rate"); ax.set_ylabel("true-positive rate")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02); ax.legend(loc="lower right")
    ax.set_title("(c) Tamper localization on real splices", loc="left")
    # (d) passive PRNU baseline
    ax = axs[1, 1]
    cond, gen, imp = prnu()
    x = np.arange(len(cond))
    ax.plot(x, gen, "o-", color=GO, label="genuine camera")
    ax.plot(x, imp, "s--", color=RD, label="other camera")
    ax.fill_between(x, imp, gen, color=GO, alpha=0.08, lw=0)
    ax.set_xticks(x); ax.set_xticklabels(["clean" if c == "clean" else f"$Q{c[1:]}$" for c in cond])
    ax.set_xlabel("JPEG compression"); ax.set_ylabel("PRNU correlation (NCC)")
    ax.legend(loc="upper right")
    ax.set_title("(d) Passive PRNU baseline: margin narrows", loc="left")
    for a in axs.flat:
        a.grid(alpha=0.25, lw=0.5)
        a.spines["top"].set_visible(False)
        if a is not axs[0, 1]:
            a.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.3, h_pad=1.0, w_pad=1.6)
    fig.savefig(os.path.join(FIG, "fig_results.pdf"))
    plt.close(fig)


def fig_adaptive():
    """Three 192x192 crops (marked original | adaptive edit after JPEG Q90 | donor)
    from results/e6_adaptive_example.png, upsampled for print, with the 96 px
    patch outlined (pad 48 px, see e6_device_identity.py)."""
    strip = Image.open(os.path.join(RES, "e6_adaptive_example.png")).convert("RGB")
    n = strip.width // 3
    fig, axs = plt.subplots(1, 3, figsize=(3.45, 1.42))
    labels = ["(a) marked original", "(b) adaptive edit", "(c) donor image"]
    for i, ax in enumerate(axs):
        crop = strip.crop((i * n, 0, (i + 1) * n, strip.height)).resize((4 * n, 4 * strip.height), Image.LANCZOS)
        ax.imshow(crop, extent=(0, n, n, 0), interpolation="none")
        ax.add_patch(Rectangle((48, 48), 96, 96, fill=False, ec="white", lw=0.8, ls=(0, (3, 2))))
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_linewidth(0.4)
        ax.set_xlabel(labels[i], fontsize=7, labelpad=2)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.14, wspace=0.05)
    fig.savefig(os.path.join(FIG, "fig_adaptive.pdf"), dpi=600, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)


if __name__ == "__main__":
    fig_results()
    fig_adaptive()
    print("wrote fig_results.pdf and fig_adaptive.pdf to", os.path.normpath(FIG))
