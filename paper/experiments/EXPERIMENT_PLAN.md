# PixelRoot — Experimental Validation Plan and Claims Matrix

This document (a) enumerates every falsifiable claim in `pixelroot.tex`, (b) scrutinizes
it, (c) specifies a rigorous experiment grounded in current best practice, and (d)
points to the script and results file that produce the measured numbers.

Methodology is aligned with the current state of the art:
- **WAVES** (An et al., ICML 2024) — the standard image-watermark robustness benchmark:
  26+ attacks (JPEG, Gaussian noise/blur, rotation, resized-crop, erase, brightness,
  contrast, and combos), reported as *Performance-vs-Quality* with PSNR/SSIM and a
  detection rate at a fixed false-positive budget.
- **Image-forgery-localization** protocol (CASIA, Columbia, IMD2020 literature):
  pixel-level **F1, AUC, IoU**, and the permutation metric **p-F1**.
- **PRNU** camera-ID protocol (Lukáš 2006; Chen 2008): residual-based fingerprint with
  normalized cross-correlation / PCE.

All earlier numbers in the paper came from a **synthetic** image model and a
**luminance-only** DCT JPEG approximation. The upgrades below re-derive every empirical
claim on **real public images** (Kodak) with a **real JPEG/WebP codec** (libjpeg via
Pillow), plus realistic tamper masks.

---

## Datasets (public, downloaded)

| ID | Dataset | Content | Use | Source |
|----|---------|---------|-----|--------|
| D1 | Kodak True Color (24) | 768×512 natural photos | imperceptibility, robustness, security, localization host | r0k.us/graphics/kodak |
| D2 | (optional) Columbia/CASIA masks | tamper shapes | realistic localization masks | forensics datasets |
| D3 | (optional) Dresden/VISION | multi-camera | PRNU cross-camera ID | gated; see E4 |

Kodak is the canonical reference set for image-compression and watermarking evaluation;
it gives reproducible, license-clean natural-image content.

---

## Claims matrix

| # | Claim (as stated in paper) | Scrutiny / risk | Experiment | Script | Metrics |
|---|----------------------------|-----------------|------------|--------|---------|
| C1 | Embedding is imperceptible (~40 dB PSNR, 0.97 SSIM) | Synthetic only; real photos have edges/texture that interact with the carrier | Embed in Y of real RGB photos; measure PSNR/SSIM vs original | `e1_robustness.py` | PSNR, SSIM, LPIPS-free |
| C2 | 0% payload BER through JPEG to Q=10, noise σ≤20, resize 0.5/0.75×, crop 1–6% w/ resync | JPEG model was luminance-only (no 4:2:0 chroma, no real libjpeg rounding); synthetic content under-stresses detector | Real libjpeg JPEG Q95→Q5, WebP, AWGN, blur, resize, rotate, brightness/contrast, combos (WAVES suite) on real images | `e1_robustness.py` | BER, decode-success, BER vs quality |
| C3 | Amplitude operating curve shows a graceful cliff | Need to confirm cliff location on real content | Sweep A∈{0.5..6} at fixed strong attack; PSNR vs BER | `e1_robustness.py` | PSNR, BER, success |
| C4 | Security: wrong-key BER≈0.5, forgery BER≈0.5, 0 false-accepts | Must hold on real images, with many trials, near the RS accept threshold | Wrong-key reads, unmarked-image reads, transplant/copy attack | `e2_security.py` | mean BER, false-accept count, RS-accept rate |
| C6 | Carrier unpredictability (Prop. 2): guess prob ≈ [C(N_B,m)2^m]^-1 | Combinatorial bound is exact; empirical counterpart is C4 | Analytic + empirical wrong-key | `e2_security.py` | guess-prob, empirical BER |
| C7 | Soft false-accept bound (Prop. 3): ≤ Σ … ≪ 2^-100 | Closed-form; verify code & numerics, compare to empirical | Evaluate Eq. (fa) numerically; compare with E2 empirics | `e5_crypto.py` | bound value vs empirical |
| C9 | Per-pixel localization: TPR 0.986 / FPR 0.022 | Synthetic; coarse single-shape splice; no AUC/F1/IoU | Embed per-pixel layer in real photos; realistic splices; sweep thresholds | `e3_localization.py` | Pixel-F1, p-F1, AUC, IoU, TPR/FPR |
| C10 | Crypto micro-bench: SHA-256 over 6 MP ≈ 3 ms; seed/sig in µs | JS-only; verify cross-impl on real frame | Time SHA-256 on real 6 MP frame; seed/selection | `e5_crypto.py` | ms/op |
| C11 | Notarization O(1) amortized via Merkle batching | Need real Merkle build + path-length + gas estimate | Build Merkle over N∈{1,10²,10⁴}; per-image cost; gas model | `e5_crypto.py` | bytes, path len, gas est |
| C12 | PRNU sensor fingerprint is a real baseline PixelRoot improves on | We claim PixelRoot is *active* vs PRNU *passive*; should show PRNU detection curve for context | PRNU residual fingerprint + NCC/PCE detection (best-effort w/ available data) | `e4_prnu.py` | NCC/PCE, ROC |
| C-MFG | Per-pixel gain is manufacturable (M1/M2/M3) | Engineering claim; needs schematic-level grounding | Engineering diagrams + sourced process narrative | `figures/`, `MANUFACTURING.md` | n/a (qualitative) |

Claims **C5 (hard-binding soundness)** and the threat-catalogue reductions are
cryptographic arguments (collision resistance + ledger immutability); they are validated
by Prop. 1 and the C10/C11 implementation, not a statistical experiment.

---

## Attack suite (WAVES-aligned, real codecs)

Degradation: JPEG (Q ∈ {95,90,80,70,60,50,40,30,20,10,5}, real libjpeg, 4:2:0), WebP
(q80/60), Gaussian noise (σ ∈ {2,5,10,20}), Gaussian blur (σ ∈ {0.5,1.0}).
Geometric: resize (0.5×, 0.75×, 1.5× round-trip), center-crop+pad (1–8%), rotation (±1°, ±2°),
with block-grid resynchronization.
Photometric: brightness (×0.9, ×1.1), contrast (×0.9, ×1.1), gamma (0.9, 1.1).
Combo: JPEG70+resize0.75, JPEG50+noise5, resize0.75+JPEG40.

---

## Reproduction

```
cd paper/experiments
python3 e1_robustness.py   # C1, C2, C3  -> results/e1_*.txt, results/e1_curve.csv
python3 e2_security.py     # C4, C6      -> results/e2_*.txt
python3 e3_localization.py # C9          -> results/e3_*.txt, results/e3_roc.csv
python3 e4_prnu.py         # C12         -> results/e4_*.txt
python3 e5_crypto.py       # C7,C10,C11  -> results/e5_*.txt
python3 make_figures.py    # engineering diagrams + result plots -> figures/
```

(Full console output is consolidated in `results/ALL_RESULTS.txt`.)

---

## Measured results (headline)

All on **24 real Kodak images** with **real libjpeg/WebP** and a **real RS(48,16)** code.

| Claim | Result | Verdict vs. paper |
|-------|--------|-------------------|
| C1 imperceptibility | PSNR 38.2 dB, SSIM 0.942 @ A=4 (≈41 dB @ A=3) | **corrected** (was 40.2 dB synthetic) |
| C2 robustness | payload recovered 23/24 through JPEG Q10, WebP, noise σ≤20, blur, resize, photometric, crop 1–3%; raw BER ≈1.6% | **corrected & strengthened** (real data; was "0% / 24-of-24 synthetic") |
| C2 limits | rotation ±1–2° and resized-crop → BER ≈0.5 (need explicit geo-sync); JPEG Q5 fails | **new, honest limitation** |
| C3 operating curve | genuine cliff: 0/24 @ A=0.5 → 23/24 @ A=4 (JPEG Q40) | confirmed |
| C4 security | wrong-key BER 0.4996, 0/1200 FA; forgery 0/24; copy-attack 0/17 pass as new identity | confirmed on real data |
| C7 RS false-accept bound | ≤ 1.8×10⁻⁶⁵ (matches 0 empirical) | confirmed |
| C9 localization | ROC-AUC 0.974, pixel-F1 0.74, IoU 0.59, TPR/FPR 0.914/0.037; AUC 0.954 @ JPEG Q90 | **corrected** (was TPR 0.986/FPR 0.022 single synthetic splice) |
| C10 SHA-256 | 2.64 ms / 5.9 MB frame | confirmed (~3 ms claim) |
| C11 notarization | Merkle 10⁴ leaves → 14-deep, 448 B proofs, 5.8 ms; ≈45k gas/tx → 4.5 gas/img @ batch 10⁴ | confirmed (O(1) amortized) |
| C12 PRNU baseline | accurate clean; genuine–impostor margin shrinks +0.019→+0.004 and PCE −18% under JPEG | confirmed (motivates active mark) |
| C-MFG | engineering schematics + sourced 0.4 µm hybrid-bond / 3-layer DPS narrative | see `MANUFACTURING.md`, `figures/` |

**Key correction:** the earlier synthetic "0% BER / 24-of-24 / 40.2 dB / TPR 0.986"
claims were optimistic. On real photographs with real codecs the honest picture is:
~38 dB PSNR, a ~1.6% raw channel BER that the RS code cleans to **23/24** exact
payload recoveries across the realistic attack range, AUC-0.97 localization, and a
clearly-stated geometric limitation. This is a stronger, defensible result because it
is measured on public data others can reproduce.
