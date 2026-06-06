"""
Engineering diagrams + result plots for PixelRoot.

Produces (in figures/):
  fig_gain_spectrum.{png,pdf}  -- gain-control granularity vs manufacturing technique
  fig_m1_dcg.{png,pdf}         -- 4T pixel with dual-conversion-gain (M1)
  fig_m2_coded.{png,pdf}       -- coded-exposure pixel with in-pixel memory (M2)
  fig_m3_stack.{png,pdf}       -- 3-layer stacked BSI + Cu-Cu hybrid bonding (M3)
  fig_datapath.{png,pdf}       -- PixelRoot provenance-write datapath
  fig_results.{png,pdf}        -- measured robustness / operating curve / ROC / PRNU

All schematics are drawn as vector figures (matplotlib) for label-accurate,
publication-quality engineering sketches.
"""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch, Circle, Polygon
from matplotlib.lines import Line2D
import numpy as np

FIG = os.path.join(os.path.dirname(__file__), "figures"); os.makedirs(FIG, exist_ok=True)
RES = os.path.join(os.path.dirname(__file__), "results")
INK = "#1b2838"; ACC = "#1f6feb"; GO = "#137333"; RD = "#b3261e"; AMB = "#b8860b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=200, bbox_inches="tight")
    fig.savefig(os.path.join(FIG, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)

def box(ax, x, y, w, h, text, fc="white", ec=INK, fs=9, lw=1.4, rad=0.02, tc=INK, weight="normal"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.005,rounding_size={rad}",
                       fc=fc, ec=ec, lw=lw)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, weight=weight)

def arrow(ax, x0, y0, x1, y1, c=INK, lw=1.6, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                 mutation_scale=12, color=c, lw=lw, linestyle=ls))

def wire(ax, pts, c=INK, lw=1.4):
    xs, ys = zip(*pts); ax.add_line(Line2D(xs, ys, color=c, lw=lw))

def nmos(ax, x, y, label, scale=1.0, gate_left=True, label_below=False):
    """Draw a simple NMOS: vertical channel (drain top, source bottom), gate on side."""
    s = scale
    wire(ax, [(x, y + 0.18 * s), (x, y - 0.18 * s)], lw=2.2)            # channel
    wire(ax, [(x, y + 0.18 * s), (x + 0.16 * s, y + 0.18 * s)])         # drain stub up-right
    wire(ax, [(x + 0.16 * s, y + 0.18 * s), (x + 0.16 * s, y + 0.30 * s)])
    wire(ax, [(x, y - 0.18 * s), (x + 0.16 * s, y - 0.18 * s)])         # source stub down-right
    wire(ax, [(x + 0.16 * s, y - 0.18 * s), (x + 0.16 * s, y - 0.30 * s)])
    gx = x - 0.12 * s
    wire(ax, [(gx, y + 0.13 * s), (gx, y - 0.13 * s)], lw=2.0)          # gate plate
    wire(ax, [(gx, y), (gx - 0.16 * s, y)])                            # gate lead
    if label_below:
        ax.text(x, y - 0.52 * s, label, fontsize=10, ha="center", va="top", color=INK)
    else:
        ax.text(x + 0.42 * s, y, label, fontsize=10, va="center", ha="left", color=INK)
    return dict(d=(x + 0.16 * s, y + 0.30 * s), s=(x + 0.16 * s, y - 0.30 * s), g=(gx - 0.16 * s, y))

# ---------------------------------------------------------------- Fig 1
def fig_gain_spectrum():
    fig, ax = plt.subplots(figsize=(11, 4.6)); ax.axis("off")
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.6)
    ax.text(5.5, 4.3, "The provenance-write gain-control spectrum: granularity vs. manufacturing technique",
            ha="center", fontsize=12, weight="bold", color=INK)
    stages = [
        ("Per-FRAME\ngain", "Global analog/digital gain\n(every sensor today)", "Trivial\n(firmware)", GO),
        ("Per-COLUMN\ngain", "Column-parallel PGA / ADC\nreference trim", "Low\n(existing column ADC)", GO),
        ("Per-REGION\ngain  \u2605", "Tile programmable gain via\nrow/column gating (PixelRoot\nbaseline, evaluated here)", "Moderate\n(control logic + SRAM)", ACC),
        ("Per-PIXEL\ngain", "M1 dual/triple conv. gain;\nM2 coded-exposure SRAM;\nM3 3-layer stacked DPS", "Higher\n(area, pitch, yield)", AMB),
    ]
    x = 0.4; w = 2.45; gap = 0.18; y = 1.5; h = 2.1
    for i, (title, desc, cost, col) in enumerate(stages):
        box(ax, x, y, w, h, "", fc="#f6f9ff", ec=col, lw=2.0, rad=0.05)
        ax.text(x + w / 2, y + h - 0.32, title, ha="center", fontsize=10.5, weight="bold", color=col)
        ax.text(x + w / 2, y + h - 1.02, desc, ha="center", fontsize=8.0, color=INK)
        ax.text(x + w / 2, y + 0.32, "cost: " + cost, ha="center", fontsize=7.6, color="#555", style="italic")
        if i < 3:
            arrow(ax, x + w + 0.01, y + h / 2, x + w + gap - 0.01, y + h / 2, c=INK, lw=2.0)
        x += w + gap
    ax.annotate("increasing spatial resolution of the embedded mark  \u2192", (0.4, 1.15),
                fontsize=9, color="#444")
    ax.annotate("increasing manufacturing investment  \u2192", (0.4, 0.85), fontsize=9, color="#444")
    ax.text(5.5, 0.35, "PixelRoot's robust channel is realizable TODAY at per-region granularity; per-pixel is a manufacturable upgrade (M1\u2013M3), not a prerequisite.",
            ha="center", fontsize=8.2, color=GO)
    save(fig, "fig_gain_spectrum")

# ---------------------------------------------------------------- Fig 2 (M1)
def fig_m1_dcg():
    fig, ax = plt.subplots(figsize=(9.2, 6.0)); ax.axis("off")
    ax.set_xlim(0, 9.2); ax.set_ylim(0, 6.0)
    ax.text(4.6, 5.72, "M1 \u2014 Per-pixel conversion-gain selection (dual conversion gain, DCG)",
            ha="center", fontsize=13.5, weight="bold", color=INK)
    # photodiode
    pdx, pdy = 0.9, 2.85
    wire(ax, [(pdx, pdy), (pdx, pdy + 0.9)], lw=2.2)
    ax.add_patch(Polygon([(pdx - 0.22, pdy + 0.9), (pdx + 0.22, pdy + 0.9), (pdx, pdy + 0.55)], closed=True, fc=ACC, ec=INK))
    wire(ax, [(pdx - 0.25, pdy + 0.55), (pdx + 0.25, pdy + 0.55)], lw=2.2)
    ax.text(pdx, pdy - 0.18, "PD", ha="center", fontsize=11, weight="bold")
    wire(ax, [(pdx, pdy), (pdx, pdy - 0.35)]); wire(ax, [(pdx - 0.2, pdy - 0.35), (pdx + 0.2, pdy - 0.35)], lw=2.4)
    # transfer gate TX
    wire(ax, [(pdx, pdy + 0.9), (pdx, pdy + 1.25)])
    txm = nmos(ax, 1.9, pdy + 1.25, "TX", gate_left=True)
    wire(ax, [(pdx, pdy + 1.25), (1.9 + 0.16, pdy + 1.25 + 0.30)])
    # FD node rail (top)
    fdx = 3.0; fdy = pdy + 1.25
    wire(ax, [(txm["s"][0], txm["s"][1]), (txm["s"][0], fdy)])
    fd_end = 7.15
    wire(ax, [(txm["s"][0], fdy), (fd_end, fdy)])
    ax.add_patch(Circle((fdx, fdy), 0.05, fc=INK))
    ax.text(fdx - 0.12, fdy + 0.52, "FD node", ha="right", va="bottom", fontsize=10.5, color=RD, weight="bold")
    ax.text(fdx - 0.12, fdy + 0.30, "(floating diffusion)", ha="right", va="bottom", fontsize=8.8, color=RD)
    # C_fd (intrinsic) to ground
    def cap(ax, x, y, label, col=INK):
        wire(ax, [(x, y), (x, y - 0.18)]); wire(ax, [(x - 0.18, y - 0.18), (x + 0.18, y - 0.18)], lw=2.4)
        wire(ax, [(x - 0.18, y - 0.30), (x + 0.18, y - 0.30)], lw=2.4)
        wire(ax, [(x, y - 0.30), (x, y - 0.5)]); wire(ax, [(x - 0.14, y - 0.5), (x + 0.14, y - 0.5)], lw=2.0)
        ax.text(x + 0.32, y - 0.22, label, fontsize=10, va="center", color=col)
    cap(ax, fdx, fdy, "C_FD")
    ax.text(fdx + 0.05, fdy - 0.78, "(small \u2192 HIGH gain)", fontsize=9.5, ha="center", color="#555")
    # DCG transistor adding C_DCG — extra spacing before RST
    dgm = nmos(ax, 4.35, fdy, "", gate_left=True)
    ax.text(dgm["g"][0] + 0.05, fdy + 0.52, "DCG", ha="center", va="bottom", fontsize=10, color=INK, weight="bold")
    arrow(ax, dgm["g"][0] + 0.05, fdy + 0.65, dgm["g"][0], dgm["g"][1] + 0.02, c=ACC)
    ax.text(dgm["g"][0] + 0.05, fdy + 0.78, "GAIN SELECT", ha="center", va="bottom", fontsize=10, color=ACC, weight="bold")
    cap_x = dgm["s"][0] - 0.55
    wire(ax, [(dgm["s"][0], dgm["s"][1]), (cap_x, dgm["s"][1])])
    cap(ax, cap_x, dgm["s"][1] + 0.02, "C_DCG", col=AMB)
    ax.text(cap_x, dgm["s"][1] - 0.72, "(added \u2192 LOW gain)", fontsize=9.0, ha="center", color=AMB)
    # RST
    rstm = nmos(ax, 6.35, fdy, "RST", label_below=True)
    wire(ax, [(fd_end, fdy), (rstm["d"][0], rstm["d"][1])])
    wire(ax, [(rstm["d"][0], rstm["d"][1]), (rstm["d"][0], rstm["d"][1] + 0.25)])
    ax.text(rstm["d"][0], rstm["d"][1] + 0.40, "VDD", ha="center", fontsize=10)
    # SF + RS readout — separate row, tap FD rail at far right via outside route
    sfy = 1.75
    sfm = nmos(ax, 5.35, sfy, "SF", label_below=True)
    rsm = nmos(ax, 6.85, sfy, "RS", label_below=True)
    route_x = 8.55
    wire(ax, [(fd_end, fdy), (route_x, fdy), (route_x, sfy), (sfm["g"][0], sfy)])
    wire(ax, [(sfm["d"][0], sfm["d"][1]), (sfm["d"][0], sfm["d"][1] + 0.2)])
    ax.text(sfm["d"][0], sfm["d"][1] + 0.33, "VDD", ha="center", fontsize=10)
    out_y = sfy - 0.55
    wire(ax, [(sfm["s"][0], sfm["s"][1]), (sfm["s"][0], out_y), (rsm["d"][0], out_y), (rsm["d"][0], rsm["d"][1])])
    wire(ax, [(rsm["s"][0], rsm["s"][1]), (rsm["s"][0], 0.62)])
    ax.text(rsm["s"][0], 0.48, "column bus", ha="center", fontsize=10, color=INK)
    # callout — bottom-left, clear of routed wires
    box(ax, 0.25, 0.08, 4.55, 1.02,
        "Provenance use: a per-pixel GAIN-SELECT bit\n"
        "(from the keyed PRNG of the payload) toggles\n"
        "HIGH/LOW conversion gain, writing a faint\n"
        "intensity chip into each carrier pixel.",
        fc="#eef7ee", ec=GO, fs=8.8, tc=INK)
    save(fig, "fig_m1_dcg")

# ---------------------------------------------------------------- Fig 3 (M2)
def fig_m2_coded():
    fig = plt.figure(figsize=(12.2, 5.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.42)
    ax = fig.add_subplot(gs[0, 0]); axt = fig.add_subplot(gs[0, 1])
    for a in (ax, axt): a.axis("off")
    ax.set_xlim(0, 5.6); ax.set_ylim(0, 5.6)
    ax.text(2.8, 5.35, "M2 \u2014 Coded-exposure pixel\n(per-pixel integration gating)",
            ha="center", fontsize=12, weight="bold", color=INK)
    # PD
    wire(ax, [(1.0, 2.85), (1.0, 3.65)], lw=2.2)
    ax.add_patch(Polygon([(0.78, 3.65), (1.22, 3.65), (1.0, 3.3)], closed=True, fc=ACC, ec=INK))
    wire(ax, [(0.75, 3.3), (1.25, 3.3)], lw=2.2)
    ax.text(1.0, 2.65, "PD", ha="center", fontsize=11, weight="bold")
    # gating switch
    sw = nmos(ax, 2.3, 3.45, "GATE")
    wire(ax, [(1.0, 3.65), (sw["d"][0], sw["d"][1])])
    box(ax, 1.55, 1.55, 1.7, 0.8, "1-bit in-pixel\nSRAM cell", fc="#eef3ff", ec=ACC, fs=10)
    arrow(ax, 2.4, 2.35, sw["g"][0] + 0.05, sw["g"][1] - 0.05, c=ACC)
    ax.text(3.35, 1.95, "stores per-pixel\nexposure bit b_i", fontsize=9.5, color=ACC)
    # storage node / readout
    wire(ax, [(sw["s"][0], sw["s"][1]), (sw["s"][0], 3.45), (4.05, 3.45)])
    ax.add_patch(Circle((4.05, 3.45), 0.05, fc=INK))
    ax.text(4.05, 4.02, "storage / FD", fontsize=10, ha="center", color=RD)
    box(ax, 4.45, 3.05, 1.05, 0.8, "SF + RS\nreadout", fc="white", ec=INK, fs=10)
    wire(ax, [(4.10, 3.45), (4.45, 3.45)])
    box(ax, 0.25, 0.08, 5.15, 0.96,
        "GATE conducts only while b_i = 1, so each pixel\n"
        "integrates for a keyed sub-window \u2192 a per-pixel\n"
        "effective-gain chip, independent of its neighbours.",
        fc="#eef7ee", ec=GO, fs=8.8, tc=INK)
    # timing diagram — labels stay inside the right panel
    axt.set_xlim(0, 10); axt.set_ylim(0, 5.6)
    axt.text(5, 5.35, "Per-pixel coded exposure (timing)", ha="center", fontsize=11.5, weight="bold", color=INK)
    def pulse(y, pattern, label, code, col):
        axt.text(0.05, y + 0.55, label, fontsize=9.2, ha="left", color=col, weight="bold")
        if code:
            axt.text(0.05, y + 0.18, code, fontsize=8.0, ha="left", color=col, family="monospace")
        x = 3.4; step = 0.62
        pts = [(x, y)]
        for b in pattern:
            lvl = y + 0.5 * b
            pts.append((x, lvl)); x += step; pts.append((x, lvl))
        axt.add_line(Line2D(*zip(*pts), color=col, lw=1.8))
    axt.text(3.4, 4.15, "exposure window", fontsize=9.5, color="#666")
    pulse(3.55, [1,1,1,1,1,1,1,1,1,1], "global shutter", "", "#999")
    pulse(2.35, [1,0,1,1,0,1,0,1,1,0], "pixel A", "b = 1011010110", ACC)
    pulse(1.15, [0,1,1,0,1,1,1,0,0,1], "pixel B", "b = 0110111001", GO)
    axt.text(5, 0.35, "Each pixel's keyed on/off code sets its integration time \u2192 per-pixel gain.",
             ha="center", fontsize=9.5, color=INK)
    save(fig, "fig_m2_coded")

# ---------------------------------------------------------------- Fig 4 (M3)
def fig_m3_stack():
    fig, ax = plt.subplots(figsize=(10.4, 5.6)); ax.axis("off")
    ax.set_xlim(0, 10.4); ax.set_ylim(0, 5.6)
    ax.text(4.6, 5.35, "M3 \u2014 3-layer stacked BSI sensor with Cu\u2013Cu hybrid bonding",
            ha="center", fontsize=13.5, weight="bold", color=INK)
    x0, w = 1.2, 6.0
    layers = [
        (3.95, 1.05, "#cfe3ff", "Layer 1 \u2014 BSI photodiode array (back-illuminated)",
         "microlens + color filter + pinned photodiode + transfer gate"),
        (2.55, 1.05, "#d8f0d8", "Layer 2 \u2014 pixel-parallel ADC + comparator",
         "single-ended comparator, per-pixel 10-bit SRAM (coded exposure / DPS)"),
        (1.15, 1.05, "#ffe9c7", "Layer 3 \u2014 logic: frame memory + ISP + keyed PRNG",
         "FPN correction, provenance-write controller, hashing pre-processor"),
    ]
    for yy, hh, col, t1, t2 in layers:
        box(ax, x0, yy, w, hh, "", fc=col, ec=INK, lw=1.6, rad=0.03)
        ax.text(x0 + 0.15, yy + hh - 0.25, t1, fontsize=11, weight="bold", color=INK, ha="left")
        ax.text(x0 + 0.15, yy + 0.30, t2, fontsize=9.3, color="#333", ha="left")
    # microlenses on top
    for i in range(10):
        cx = x0 + 0.5 + i * 0.55
        ax.add_patch(Circle((cx, 5.05 + 0.0), 0.16, fc="#bcd4ff", ec=INK, lw=0.8))
    ax.text(x0 + w + 0.1, 5.05, "microlenses", fontsize=9.5, va="center")
    arrow(ax, x0 - 0.55, 5.45, x0 - 0.05, 5.05, c=AMB, lw=2.0)
    ax.text(x0 - 0.9, 5.5, "incident\nlight", fontsize=9.3, color=AMB, ha="center")
    # hybrid bond interfaces (Cu pads)
    def bonds(y):
        for i in range(11):
            cx = x0 + 0.45 + i * 0.55
            ax.add_patch(Rectangle((cx - 0.05, y - 0.06), 0.10, 0.12, fc="#b87333", ec=INK, lw=0.6))
    bonds(3.95); bonds(2.55)
    ax.annotate("Cu\u2013Cu hybrid bond\n(\u2248 0.4 \u00b5m pitch,\n~10^6 bonds / mm\u00b2)",
                xy=(x0 + w + 0.05, 3.95), xytext=(x0 + w + 0.15, 3.55),
                fontsize=9.3, color="#b87333",
                arrowprops=dict(arrowstyle="->", color="#b87333"))
    ax.annotate("per-pixel vertical via\n(face-to-back)", xy=(x0 + w + 0.05, 2.55),
                xytext=(x0 + w + 0.15, 2.15), fontsize=9.3, color="#b87333",
                arrowprops=dict(arrowstyle="->", color="#b87333"))
    box(ax, x0, 0.08, w, 0.86,
        "Per-pixel ADC + SRAM + logic sit UNDER each pixel \u2192 independent\n"
        "per-pixel gain, exposure coding, and on-die provenance write\n"
        "with no fill-factor penalty (light hits Layer 1 only).",
        fc="#eef7ee", ec=GO, fs=8.8)
    save(fig, "fig_m3_stack")

# ---------------------------------------------------------------- Fig 5 datapath
def fig_datapath():
    fig, ax = plt.subplots(figsize=(11.5, 4.2)); ax.axis("off")
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 4.2)
    ax.text(5.75, 4.0, "PixelRoot provenance-write datapath (capture-time)", ha="center",
            fontsize=12, weight="bold", color=INK)
    y = 2.4; h = 0.95
    blocks = [
        (0.2, 1.7, "Pixel array\n(PD + gain\nselect)", "#cfe3ff"),
        (2.1, 1.5, "Keyed PRNG\nseed = H(k \u2225 m)\nselect carriers", "#eef3ff"),
        (3.8, 1.5, "Gain/exposure\nmodulation\n(\u00b1 chip)", "#d8f0d8"),
        (5.5, 1.4, "ADC + ISP\n(readout)", "white"),
        (7.1, 1.5, "SHA-256\ncommit\nH(I \u2225 m)", "#ffe9c7"),
        (8.8, 1.5, "Merkle batch\n+ smart\ncontract", "#ffd9d4"),
        (10.5, 0.9, "Public\nledger", "#e8e8e8"),
    ]
    xs = []
    for x, w, t, c in blocks:
        box(ax, x, y, w, h, t, fc=c, ec=INK, fs=8.0); xs.append((x, w))
    for i in range(len(blocks) - 1):
        x, w = xs[i]; nx, _ = xs[i + 1]
        arrow(ax, x + w + 0.02, y + h / 2, nx - 0.02, y + h / 2)
    # payload input
    box(ax, 2.1, 0.7, 1.5, 0.7, "payload m\n(ID, time, GPS)", fc="white", ec=ACC, fs=7.6, tc=ACC)
    arrow(ax, 2.85, 1.4, 2.85, y - 0.02, c=ACC)
    # OEM key
    box(ax, 0.5, 0.7, 1.3, 0.7, "OEM key k\n(OTP/secure)", fc="white", ec=RD, fs=7.6, tc=RD)
    arrow(ax, 1.8, 1.05, 2.1, 1.05 + 0.0, c=RD)
    arrow(ax, 1.15, 1.4, 1.15, y - 0.02, c=RD, ls=(0, (3, 2)))
    ax.text(5.75, 0.25, "Soft binding (in-pixel, survives transcoding)  +  Hard binding (on-chain hash) \u2014 two independent barriers.",
            ha="center", fontsize=8.2, color=GO)
    save(fig, "fig_datapath")

# ---------------------------------------------------------------- Fig 6 results
def read_csv(name):
    p = os.path.join(RES, name)
    if not os.path.exists(p): return None
    with open(p) as f:
        return list(csv.reader(f))

def fig_results():
    fig, axs = plt.subplots(2, 2, figsize=(11.0, 8.8))
    title_fs = 9.5
    # (a) BER vs JPEG quality (parsed from e1 results text)
    qs = [95,90,80,70,60,50,40,30,20,10,5]
    bers = []
    txt = open(os.path.join(RES, "e1_robustness.txt")).read().splitlines()
    for q in qs:
        for line in txt:
            if line.startswith(f"JPEG Q{q} ") or line.startswith(f"JPEG Q{q}\t") or line.strip().startswith(f"JPEG Q{q} "):
                parts = line.split()
                bers.append(float(parts[2])); break
    ax = axs[0, 0]
    ax.plot(qs, bers, "o-", color=ACC, lw=2)
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_xlabel("JPEG quality Q"); ax.set_ylabel("raw coded-bit BER")
    ax.set_title("(a) In-pixel channel BER vs real-JPEG quality\n(Kodak, pre-ECC; RS recovers payload \u2265 Q10)", fontsize=title_fs, pad=10)
    ax.invert_xaxis(); ax.grid(alpha=0.3)
    # (b) amplitude operating curve
    ax = axs[0, 1]
    rows = read_csv("e1_curve.csv")
    if rows:
        A = [float(r[0]) for r in rows[1:]]
        psnr = [float(r[1]) if r[1] != "inf" else np.nan for r in rows[1:]]
        ber = [float(r[2]) for r in rows[1:]]
        dec = [int(r[3]) for r in rows[1:]]; n = int(rows[1][4])
        ax.plot(A, ber, "s-", color=RD, lw=2, label="raw BER @ Q40")
        ax2 = ax.twinx()
        ax2.plot(A, [d / n for d in dec], "^--", color=GO, lw=2, label="post-ECC decode")
        ax.set_xlabel("embedding amplitude A (gray levels)")
        ax.set_ylabel("raw BER", color=RD); ax2.set_ylabel("payload decode rate", color=GO)
        ax.set_title("(b) Amplitude operating curve @ JPEG Q40\n(genuine robustness cliff on real images)", fontsize=title_fs, pad=10)
        ax.grid(alpha=0.3)
    # (c) localization ROC
    ax = axs[1, 0]
    rows = read_csv("e3_roc.csv")
    if rows:
        fpr = [float(r[0]) for r in rows[1:]]; tpr = [float(r[1]) for r in rows[1:]]
        ax.plot(fpr, tpr, color=ACC, lw=2)
        ax.plot([0, 1], [0, 1], "--", color="#999", lw=1)
        ax.set_xlabel("false positive rate"); ax.set_ylabel("true positive rate")
        ax.set_title("(c) Tamper-localization ROC (real splices)\nblock-level, AUC \u2248 0.97", fontsize=title_fs, pad=10)
        ax.grid(alpha=0.3)
    # (d) PRNU NCC margin vs JPEG
    ax = axs[1, 1]
    cond, gen, imp = [], [], []
    pr_txt = open(os.path.join(RES, "e4_prnu.txt")).read().splitlines()
    for line in pr_txt:
        for tag in ["clean", "JPEG Q95", "JPEG Q90", "JPEG Q70", "JPEG Q50"]:
            if line.strip().startswith(tag):
                p = line.split()
                cond.append(tag); gen.append(float(p[-3])); imp.append(float(p[-2]))
    if cond:
        xx = range(len(cond))
        ax.plot(xx, gen, "o-", color=GO, lw=2, label="genuine NCC")
        ax.plot(xx, imp, "s--", color=RD, lw=2, label="impostor NCC")
        ax.set_xticks(list(xx)); ax.set_xticklabels(cond, rotation=20, fontsize=7)
        ax.set_ylabel("PRNU NCC")
        ax.set_title("(d) Passive PRNU baseline: genuine\u2013impostor\nmargin shrinks under JPEG (motivates active mark)", fontsize=title_fs, pad=10)
        ax.legend(fontsize=7); ax.grid(alpha=0.3)
    fig.subplots_adjust(left=0.10, right=0.94, top=0.93, bottom=0.12, hspace=0.55, wspace=0.40)
    save(fig, "fig_results")

if __name__ == "__main__":
    fig_gain_spectrum(); fig_m1_dcg(); fig_m2_coded(); fig_m3_stack(); fig_datapath(); fig_results()
    print("figures written to", FIG)
    print(sorted(os.listdir(FIG)))
