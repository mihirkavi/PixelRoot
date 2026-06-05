"""
E2 -- Security / false-accept on REAL images. Validates C4, C6 (Prop. 2).

Three tests:
  (A) Wrong-key read: a marked image read with many WRONG OEM keys -> coded-bit
      BER ~0.5 and RS must NOT decode to the true payload (carrier unpredictability).
  (B) Forgery / unmarked: an UNMARKED real image (deepfake stand-in) read with the
      CORRECT key against an attacker's CLAIMED payload -> must not falsely accept.
  (C) Copy / transplant attack: lift the marked residual from image A and paste it
      onto a different image B; B must decode to A's payload (the original identity),
      not B's claimed one -> the forgery is exposed as a copy, not authenticated.

Outputs: results/e2_security.txt
"""
import glob, os
import numpy as np
import pixelroot as pr

DATA = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "data/kodak/*.png")))
OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)
A = 4.0
KEY = "PIXELROOT-OEM-KEY-v2"
WRONG_KEYS = [f"attacker-guess-{i}" for i in range(50)]

def n_blocks_of(rgb):
    H8, W8 = (rgb.shape[0] // 8) * 8, (rgb.shape[1] // 8) * 8
    return (H8 // 8) * (W8 // 8)

def main():
    # ---- (A) wrong-key ----
    wk_ber, wk_trials, wk_false = 0.0, 0, 0
    # ---- (B) forgery on unmarked ----
    fa_ber, fa_trials, fa_false = 0.0, 0, 0
    # ---- (C) copy attack ----
    copy_trials, copy_to_A, copy_to_B = 0, 0, 0

    for idx, path in enumerate(DATA):
        rgb = pr.load_rgb(path)
        payload = np.random.RandomState(1000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
        coded, _ = pr.rs_encode_bits(payload)
        R = n_blocks_of(rgb) // len(coded)
        marked, plan = pr.embed_rgb(rgb, coded, KEY, R, A)
        H8, W8 = marked.shape[0], marked.shape[1]
        ymark = pr.rgb_to_y(marked.astype(np.float64))

        # (A) read marked image with wrong keys
        for wk in WRONG_KEYS:
            wplan = (pr.keyed_plan(wk, len(coded), R, plan[2] * plan[3])[0],
                     pr.keyed_plan(wk, len(coded), R, plan[2] * plan[3])[1], plan[2], plan[3])
            rb, _ = pr.extract_y(ymark, wplan, len(coded))
            # decode with the SAME wrong plan layout; false accept if it yields the true payload
            dec, ok = pr.rs_decode_bits(rb)
            wk_ber += pr.ber(coded, rb); wk_trials += 1
            if ok and dec == payload.tobytes():
                wk_false += 1

        # (B) forgery: UNMARKED image read with correct key, attacker claims a payload
        unmarked = rgb[:H8, :W8].astype(np.uint8)
        yunm = pr.rgb_to_y(unmarked.astype(np.float64))
        rb, _ = pr.extract_y(yunm, plan, len(coded))
        claimed = np.random.RandomState(9000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
        claimed_coded, _ = pr.rs_encode_bits(claimed)
        fa_ber += pr.ber(claimed_coded, rb); fa_trials += 1
        dec, ok = pr.rs_decode_bits(rb)
        if ok and dec == claimed.tobytes():
            fa_false += 1

        # (C) copy attack: residual of A pasted onto B
        if idx + 1 < len(DATA):
            rgbB = pr.load_rgb(DATA[idx + 1])
            HB, WB = (rgbB.shape[0] // 8) * 8, (rgbB.shape[1] // 8) * 8
            h, w = min(H8, HB), min(W8, WB)
            residual = (marked[:h, :w].astype(np.float64) - rgb[:h, :w])
            forged = np.clip(np.round(rgbB[:h, :w] + residual), 0, 255).astype(np.uint8)
            # B's plan uses same key/R but B has different block count; recompute plan on h,w
            nbk = (h // 8) * (w // 8)
            planB = (pr.keyed_plan(KEY, len(coded), nbk // len(coded), nbk)[0],
                     pr.keyed_plan(KEY, len(coded), nbk // len(coded), nbk)[1], h // 8, w // 8)
            # decode the forged image with A's ORIGINAL plan (residual carries A's layout)
            yf = pr.rgb_to_y(forged.astype(np.float64))
            # A's plan was for (H8//8, W8//8); reuse if dims match, else skip
            if (h == H8) and (w == W8):
                rbf, _ = pr.extract_y(yf, plan, len(coded))
                decf, okf = pr.rs_decode_bits(rbf)
                copy_trials += 1
                if okf and decf == payload.tobytes():
                    copy_to_A += 1  # decodes to ORIGINAL A identity (copy exposed)
                # also check if it could pass as B's claimed identity
                claimedB = np.random.RandomState(7000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
                if okf and decf == claimedB.tobytes():
                    copy_to_B += 1

    L = []
    L.append("=== E2: security / false-accept on REAL images (Kodak) ===")
    L.append(f"key='{KEY}'  A={A}  RS(48,16)")
    L.append("")
    L.append(f"(A) Wrong-key read: trials={wk_trials} ({len(WRONG_KEYS)} keys x {len(DATA)} imgs)")
    L.append(f"    mean coded-bit BER = {wk_ber/wk_trials:.4f}  (ideal ~0.5)")
    L.append(f"    false accepts (decoded true payload) = {wk_false}/{wk_trials}")
    L.append("")
    L.append(f"(B) Forgery on UNMARKED images: trials={fa_trials}")
    L.append(f"    mean coded-bit BER vs claimed = {fa_ber/fa_trials:.4f}  (ideal ~0.5)")
    L.append(f"    false accepts (claimed payload decoded) = {fa_false}/{fa_trials}")
    L.append("")
    L.append(f"(C) Copy/transplant attack: trials={copy_trials}")
    L.append(f"    forged image decodes to ORIGINAL (A) identity = {copy_to_A}/{copy_trials}  (copy exposed)")
    L.append(f"    forged image passes as a NEW claimed (B) identity = {copy_to_B}/{copy_trials}  (must be 0)")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e2_security.txt"), "w") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
