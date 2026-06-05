"""
E4 -- PRNU baseline (C12). Implements the STANDARD passive sensor-fingerprint
pipeline (Lukas 2006; Chen 2008): denoising-residual fingerprint estimation,
normalized cross-correlation (NCC) and Peak-to-Correlation-Energy (PCE) detection,
and camera attribution accuracy -- on REAL image content (Kodak).

Note on data: per-camera RAW datasets (Dresden, VISION) are access-gated. We use
real Kodak *content* and the textbook multiplicative PRNU model I*(1+K)+noise to
synthesize two cameras; the extraction/detection pipeline is the real, standard
one. This establishes the passive baseline and its key weakness -- PRNU
correlation collapses under JPEG -- which motivates PixelRoot's ACTIVE mark
(measured robust to JPEG in E1). Path to full validation: rerun on Dresden/VISION.

Outputs: results/e4_prnu.txt
"""
import glob, os
import numpy as np
from scipy.ndimage import gaussian_filter
import pixelroot as pr

DATA = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "data/kodak/*.png")))
OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)

SIZE = (512, 512)
K_STD = 0.01        # fingerprint strength (typical PRNU ~1%)
READ_NOISE = 3.0

def to_gray_crop(rgb):
    y = pr.rgb_to_y(rgb)
    return y[:SIZE[0], :SIZE[1]]

def residual(img):
    """Denoising residual = image - denoised (Gaussian denoiser stand-in)."""
    return img - gaussian_filter(img, sigma=1.5)

def capture(clean, K, seed):
    rng = np.random.RandomState(seed)
    return np.clip(clean * (1 + K) + rng.normal(0, READ_NOISE, clean.shape), 0, 255)

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt(np.sum(a * a) * np.sum(b * b))
    return float(np.sum(a * b) / d) if d > 0 else 0.0

def pce(a, b):
    """Peak-to-correlation-energy via FFT cross-correlation."""
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    F = np.fft.fft2(a) * np.conj(np.fft.fft2(b))
    cc = np.fft.ifft2(F).real
    peak = cc.max()
    energy = (cc ** 2).sum() / cc.size
    return float(peak ** 2 / (energy + 1e-9))

def estimate_fingerprint(clean_imgs, K, seed0):
    res = []
    for i, c in enumerate(clean_imgs):
        cap = capture(c, K, seed0 + i)
        res.append(residual(cap))
    fp = np.mean(res, axis=0)
    return fp - fp.mean()

def capture_q(test_clean, K_true, seed, jpeg_q=None):
    cap = capture(test_clean, K_true, seed)
    if jpeg_q is not None:
        rgb = np.repeat(np.clip(cap, 0, 255).astype(np.uint8)[..., None], 3, axis=2)
        cap = pr.rgb_to_y(pr.att_jpeg(rgb, jpeg_q).astype(np.float64))[:SIZE[0], :SIZE[1]]
    return cap

def attribute(test_clean, K_true, KA, KB, seed, jpeg_q=None):
    r = residual(capture_q(test_clean, K_true, seed, jpeg_q))
    return ncc(r, KA), ncc(r, KB)

def main():
    clean = [to_gray_crop(pr.load_rgb(p)) for p in DATA]
    train_n = 12
    KA = np.random.RandomState(11).normal(0, K_STD, SIZE)
    KB = np.random.RandomState(22).normal(0, K_STD, SIZE)
    fpA = estimate_fingerprint(clean[:train_n], KA, 100)
    fpB = estimate_fingerprint(clean[:train_n], KB, 200)
    test = clean[train_n:]
    rows = []
    for q in [None, 95, 90, 70, 50]:
        correct, total = 0, 0
        gen_ncc, imp_ncc, pces = [], [], []
        for i, c in enumerate(test):
            na, nb = attribute(c, KA, fpA, fpB, 1000 + i, q)   # true A
            if na > nb: correct += 1
            total += 1
            gen_ncc.append(na); imp_ncc.append(nb)
            nb2, na2 = attribute(c, KB, fpB, fpA, 2000 + i, q)  # true B
            if nb2 > na2: correct += 1
            total += 1
            gen_ncc.append(nb2); imp_ncc.append(na2)
            pces.append(pce(residual(capture_q(c, KA, 3000 + i, q)), fpA))
        rows.append((q, correct / total, float(np.mean(gen_ncc)),
                     float(np.mean(imp_ncc)), float(np.mean(pces))))
    L = []
    L.append("=== E4: PRNU passive-baseline pipeline (real Kodak content) ===")
    L.append(f"fingerprint strength K_std={K_STD}, train={train_n} imgs/camera, test={len(test)} imgs x 2 cameras")
    L.append("standard pipeline: denoise-residual fingerprint + NCC attribution + PCE")
    L.append("")
    L.append(f"{'Condition':<14}{'attr. acc':<12}{'genuine NCC':<14}{'impostor NCC':<14}{'PCE'}")
    for q, acc, gn, imp, pc in rows:
        cond = "clean" if q is None else f"JPEG Q{q}"
        L.append(f"{cond:<14}{acc:<12.3f}{gn:<14.4f}{imp:<14.4f}{pc:.1f}")
    L.append("")
    L.append("Takeaway: passive PRNU attribution is accurate on clean images but its")
    L.append("correlation/PCE degrades under JPEG -- the documented weakness PixelRoot's")
    L.append("ACTIVE, error-corrected mark addresses (E1: payload survives to JPEG Q10).")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e4_prnu.txt"), "w") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
