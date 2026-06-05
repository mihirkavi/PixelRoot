"""
E1 -- Imperceptibility + robustness of the in-pixel channel on REAL images
(Kodak), with REAL libjpeg/WebP codecs and a REAL Reed-Solomon outer code.
Validates claims C1, C2, C3.

Reports, per attack:
  - raw coded-bit BER (channel quality, pre-ECC)
  - payload decode success after RS error correction (the end-to-end result)

Outputs:
  results/e1_robustness.txt   human-readable summary
  results/e1_curve.csv        amplitude operating curve
"""
import glob, os, csv
import numpy as np
import pixelroot as pr

DATA = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "data/kodak/*.png")))
OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)

A = 4.0
KEY = "PIXELROOT-OEM-KEY-v2"

def n_blocks_of(rgb):
    H8, W8 = (rgb.shape[0] // 8) * 8, (rgb.shape[1] // 8) * 8
    return (H8 // 8) * (W8 // 8)

def run_robustness():
    attacks = pr.standard_attacks()
    agg = {name: {"ber": 0.0, "dec": 0, "n": 0} for name, _, _ in attacks}
    psnrs, ssims, clean_bers = [], [], []
    for idx, path in enumerate(DATA):
        rgb = pr.load_rgb(path)
        payload = np.random.RandomState(1000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
        coded, _ = pr.rs_encode_bits(payload)
        R = n_blocks_of(rgb) // len(coded)
        marked, plan = pr.embed_rgb(rgb, coded, KEY, R, A)
        H8, W8 = marked.shape[0], marked.shape[1]
        orig = rgb[:H8, :W8].astype(np.uint8)
        psnrs.append(pr.psnr(orig, marked)); ssims.append(pr.ssim(orig, marked))
        # clean decode sanity
        y0 = pr.rgb_to_y(marked.astype(np.float64))
        b0, _ = pr.extract_y(y0, plan, len(coded))
        clean_bers.append(pr.ber(coded, b0))
        for name, fn, needs_resync in attacks:
            att = fn(marked)[:H8, :W8]
            y = pr.rgb_to_y(att.astype(np.float64))
            if needs_resync:
                rb, _, _ = pr.extract_resync(y, plan, len(coded), max_off=28)
            else:
                rb, _ = pr.extract_y(y, plan, len(coded))
            agg[name]["ber"] += pr.ber(coded, rb)
            dec, ok = pr.rs_decode_bits(rb)
            agg[name]["dec"] += 1 if (ok and dec == payload.tobytes()) else 0
            agg[name]["n"] += 1
    return agg, psnrs, ssims, clean_bers

def run_amplitude_curve():
    rows = []
    for a in [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]:
        ps, be, dec, n = 0.0, 0.0, 0, 0
        for idx, path in enumerate(DATA):
            rgb = pr.load_rgb(path)
            payload = np.random.RandomState(2000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
            coded, _ = pr.rs_encode_bits(payload)
            R = n_blocks_of(rgb) // len(coded)
            marked, plan = pr.embed_rgb(rgb, coded, KEY, R, a)
            H8, W8 = marked.shape[0], marked.shape[1]
            ps += pr.psnr(rgb[:H8, :W8].astype(np.uint8), marked)
            att = pr.att_jpeg(marked, 40)[:H8, :W8]
            y = pr.rgb_to_y(att.astype(np.float64))
            rb, _ = pr.extract_y(y, plan, len(coded))
            be += pr.ber(coded, rb)
            d, ok = pr.rs_decode_bits(rb)
            dec += 1 if (ok and d == payload.tobytes()) else 0
            n += 1
        rows.append((a, ps / n, be / n, dec, n))
    return rows

def main():
    agg, psnrs, ssims, clean_bers = run_robustness()
    curve = run_amplitude_curve()
    L = []
    L.append("=== E1: imperceptibility + robustness on REAL images (Kodak), REAL codecs + RS ECC ===")
    L.append(f"Images: {len(DATA)}  payload=128b  RS(48,16) nsym={pr.RS_NSYM}  coded=384b  A={A}")
    L.append(f"Mean embed PSNR: {np.mean(psnrs):.2f} dB (min {np.min(psnrs):.2f})   "
             f"SSIM: {np.mean(ssims):.4f} (min {np.min(ssims):.4f})")
    L.append(f"Mean clean coded-bit BER (pre-ECC): {np.mean(clean_bers):.4f}  "
             f"(max {np.max(clean_bers):.4f})")
    L.append("")
    L.append(f"{'Attack':<22}{'raw BER':<12}{'payload decode'}")
    for name, _, _ in pr.standard_attacks():
        a = agg[name]
        L.append(f"{name:<22}{a['ber']/a['n']:<12.4f}{a['dec']}/{a['n']}")
    L.append("")
    L.append("Amplitude operating curve @ JPEG Q40 (all images): raw BER + post-ECC decode")
    L.append(f"{'A':<8}{'PSNR(dB)':<12}{'raw BER':<10}{'decode'}")
    for a, p, b, dec, n in curve:
        L.append(f"{a:<8.1f}{p:<12.2f}{b:<10.4f}{dec}/{n}")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e1_robustness.txt"), "w") as f:
        f.write(txt + "\n")
    with open(os.path.join(OUT, "e1_curve.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["A", "PSNR_dB", "raw_BER", "decode", "n"]); w.writerows(curve)

if __name__ == "__main__":
    main()
