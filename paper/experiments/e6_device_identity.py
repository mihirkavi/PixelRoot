"""
E6 -- Device identity and content binding on REAL images (Kodak).

Exercises the full PixelRoot verification path: sensor-held P-256 keys certified
on chain by production lot, chip-signed capture records (raw hash, camera-encoding
hash, content fingerprint, block anchor, counter), Merkle-batched notarization,
in-pixel payload decoding, and the verifier's verdicts. The fingerprint threshold
is calibrated on the even-indexed images; everything reported is measured on the
odd-indexed (held-out) images. Measures:

  (1) fingerprint separation: genuine-under-processing vs. splices vs. other images
  (2) end-to-end verdicts under the benign attack suite (with reasons)
  (3) cross-scene copy attacks (keyless estimate, and with the original)
  (4) non-adaptive local edits (splices, small patches) and adaptive attacks:
      shift-to-hide splices and fingerprint-band projection
  (5) cryptographic/ledger attacks (tampered record, uncertified or revoked
      sensor, anchor/seal ordering and anchor hash, burst captures)
  (6) per-capture cost (sign/verify time, record size)

Outputs: results/e6_device_identity.txt
"""
import glob
import io
import json
import math
import os
import time
from collections import Counter

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter

import device_identity as di
import ledger
import pixelroot as pr

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sorted(glob.glob(os.path.join(HERE, "data/kodak/*.png")))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
KEY, A = "PIXELROOT-OEM-KEY-v2", 4.0
R_FOR = lambda n_blocks: n_blocks // 384


def wilson(k, n, z=1.96):
    """Wilson 95% interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} [95% CI {lo:.2f}-{hi:.2f}]"


def benign_attacks():
    """The supported envelope of Table II (no rotation / resized-crop)."""
    return [(n, f) for n, f, _ in pr.standard_attacks() if "[lim]" not in n and n != "JPEG Q5"]


def keyless_mark_estimate(y, nbh, nbw, gain):
    yb = pr.to_blocks(y[: nbh * 8, : nbw * 8])
    proj = np.sum(yb * pr.P8, axis=(2, 3)) / pr.P8_ENERGY
    hp = proj - uniform_filter(proj, size=5, mode="nearest")
    return pr.from_blocks(gain * hp[:, :, None, None] * pr.P8[None, None])


def shift_down_right(img, s):
    """Content moves down-right by s px; the top-left border is edge-padded."""
    H, W, _ = img.shape
    return np.pad(img[: H - s, : W - s], ((s, 0), (s, 0), (0, 0)), mode="edge")


def band_project(f_u8, ref_u8):
    """Adaptive attack: give every fingerprint cell of the interior the luma mean
    it has in the reference, so the forged image's fingerprint matches the
    record's while sub-cell detail of the inserted content remains."""
    out = f_u8.astype(np.float64).copy()
    yf = np.asarray(Image.fromarray(f_u8).convert("L"), np.float64)
    yr = np.asarray(Image.fromarray(ref_u8).convert("L"), np.float64)
    H, W = yf.shape
    M, G, S = di.FP_MARGIN, di.FP_GRID, di.FP_SIDE
    h, w = H - 2 * M, W - 2 * M
    for ty in range(G):
        for tx in range(G):
            y0, y1 = M + ty * h // G, M + (ty + 1) * h // G
            x0, x1 = M + tx * w // G, M + (tx + 1) * w // G
            for cy in range(S):
                for cx in range(S):
                    a0, a1 = y0 + cy * (y1 - y0) // S, y0 + (cy + 1) * (y1 - y0) // S
                    b0, b1 = x0 + cx * (x1 - x0) // S, x0 + (cx + 1) * (x1 - x0) // S
                    out[a0:a1, b0:b1] += yr[a0:a1, b0:b1].mean() - yf[a0:a1, b0:b1].mean()
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def main():
    reg = ledger.Registry()
    oem = di.Manufacturer("OEM-A", reg)
    chips, _ = oem.produce_lot(8)
    reg.tick()

    # ---------------- capture: embed, sign, batch, notarize ----------------
    caps, records, t_sign = [], [], []
    for idx, path in enumerate(DATA):
        rgb = pr.load_rgb(path)
        payload = np.random.RandomState(1000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
        coded, _ = pr.rs_encode_bits(payload)
        H8, W8 = (rgb.shape[0] // 8) * 8, (rgb.shape[1] // 8) * 8
        marked, plan = pr.embed_rgb(rgb, coded, KEY, R_FOR((H8 // 8) * (W8 // 8)), A)
        enc = di.jpeg_bytes(marked, 95)
        chip = chips[idx % len(chips)]
        t0 = time.perf_counter()
        rec = di.make_record(chip, payload, marked, enc, (reg.now, reg.block_hash(reg.now)))
        t_sign.append(time.perf_counter() - t0)
        caps.append({"rgb": rgb[:H8, :W8], "marked": marked, "enc": enc, "payload": payload,
                     "coded": coded, "plan": plan, "rec": rec, "chip": chip})
        records.append(rec)
    reg.tick()
    hashes = [di.record_hash(r) for r in records]
    batch_root = ledger.merkle_root(hashes)
    reg.register(batch_root)
    index = {}
    for i, c in enumerate(caps):
        index.setdefault(c["payload"].tobytes().hex(), []).append((c["rec"], batch_root, ledger.merkle_proof(hashes, i)))

    n = len(caps)
    cal = [i for i in range(n) if i % 2 == 0]
    test = [i for i in range(n) if i % 2 == 1]

    def donor_of(i, skip=5):
        for d in range(skip, skip + n):
            j = (i + d) % n
            if j != i and caps[j]["rgb"].shape == caps[i]["rgb"].shape:
                return j

    # ---------------- (1) fingerprint calibration (even images) ----------------
    attacks = benign_attacks()
    fps = [di.fingerprint(c["marked"]) for c in caps]
    attacked = {(i, name): fn(caps[i]["marked"])[: caps[i]["marked"].shape[0], : caps[i]["marked"].shape[1]]
                for i in range(n) for name, fn in attacks}

    def true_offset(i, name):
        if not name.startswith("Crop"):
            return (0, 0)
        frac = int(name.split()[1].rstrip("%")) / 100
        H, W, _ = caps[i]["marked"].shape
        return (-int(H * frac), -int(W * frac))

    def genuine_dist(i, name):
        off = true_offset(i, name)
        al = np.roll(np.roll(attacked[(i, name)], -off[0], axis=0), -off[1], axis=1)
        return di.fp_distance(fps[i], di.fingerprint(al))

    def splices(i, k):
        a_ = caps[i]
        H, W, _ = a_["marked"].shape
        donor = caps[donor_of(i)]["rgb"]
        out = []
        for frac in (0.25, 0.35):
            sh, sw = int(H * frac), int(W * frac)
            y0, x0 = k.randint(0, H - sh), k.randint(0, W - sw)
            f = a_["marked"].copy()
            f[y0:y0 + sh, x0:x0 + sw] = donor[y0:y0 + sh, x0:x0 + sw].astype(np.uint8)
            out.append(pr.att_jpeg(f, 90))
        return out

    cal_gen = [genuine_dist(i, name) for i in cal for name, _ in attacks]
    cal_spl = [di.fp_distance(fps[i], di.fingerprint(f)) for i in cal for f in splices(i, np.random.RandomState(100 + i))]
    gmax, smin = max(cal_gen), min(cal_spl)
    tau = round((gmax + smin) / 2, 3) if smin > gmax else round(gmax, 3)
    ver = di.Verifier(reg, index, KEY, R_FOR, tau)
    test_gen = [genuine_dist(i, name) for i in test for name, _ in attacks]
    test_imp = [di.fp_distance(fps[i], fps[j]) for i in test for j in test if i != j]

    # ---------------- (2) end-to-end verdicts (held-out images) ----------------
    verdicts, reasons, t_verify = {}, Counter(), []
    for i in test:
        c = caps[i]
        t0 = time.perf_counter()
        v, why = ver.verify(c["enc"], np.asarray(Image.open(io.BytesIO(c["enc"])).convert("RGB")))
        t_verify.append(time.perf_counter() - t0)
        verdicts.setdefault("Camera JPEG (exact file)", []).append(v)
        for name, _ in attacks:
            v, why = ver.verify(None, attacked[(i, name)])
            verdicts.setdefault(name, []).append(v)
            if v == "Unverified":
                reasons["content mismatch" if why.startswith("content") else why] += 1
    unmarked = [ver.verify(None, caps[i]["rgb"].astype(np.uint8))[0] for i in test]
    processed = [k for k in verdicts if k != "Camera JPEG (exact file)"]
    genuine_total = sum(len(verdicts[k]) for k in processed)
    genuine_ok = sum(verdicts[k].count("Transcoded-consistent") for k in processed)

    # ---------------- (3) cross-scene copy attacks (held-out) ----------------
    copy = {"keyless": [0, 0, 0], "with-original": [0, 0, 0]}  # trials, wm decodes A, accepted
    for i in test:
        a = caps[i]
        shared = pr.att_jpeg(a["marked"], 75)  # attacker only has a shared JPEG
        est = keyless_mark_estimate(pr.rgb_to_y(shared.astype(np.float64)), a["plan"][2], a["plan"][3], 1.5)
        resid = a["marked"].astype(np.float64) - a["rgb"]
        for j in test:
            b = caps[j]
            if j == i or b["rgb"].shape != a["rgb"].shape:
                continue
            for kind, delta in (("keyless", est[..., None]), ("with-original", resid)):
                forged = np.clip(np.round(b["rgb"] + delta), 0, 255).astype(np.uint8)
                bits, _ = pr.extract_y(pr.rgb_to_y(forged.astype(np.float64)), a["plan"], len(a["coded"]))
                dec, ok = pr.rs_decode_bits(bits)
                copy[kind][0] += 1
                copy[kind][1] += int(ok and dec == a["payload"].tobytes())
                copy[kind][2] += int(ver.verify(None, forged)[0] != "Unverified")

    # ---------------- (4) local edits: non-adaptive and adaptive (held-out) ----------------
    local = {}

    def tally(name, img):
        v, why = ver.verify(None, img)
        t = local.setdefault(name, [0, 0, 0])
        t[0] += 1
        t[1] += int(why != "no payload")
        t[2] += int(v != "Unverified")

    detail = []  # adaptive: how much donor detail survives in the patch
    for i in test:
        a = caps[i]
        b = caps[donor_of(i)]["rgb"]
        H, W, _ = a["marked"].shape
        for f in splices(i, np.random.RandomState(100 + i)):
            tally("Splice 25-35% side, JPEG Q90", f)
        k = np.random.RandomState(200 + i)
        M = di.FP_MARGIN
        for ps in (64, 96, 128):
            y0, x0 = k.randint(M, H - M - ps), k.randint(M, W - M - ps)
            f = a["marked"].copy()
            f[y0:y0 + ps, x0:x0 + ps] = b[y0:y0 + ps, x0:x0 + ps].astype(np.uint8)
            tally(f"Patch {ps}x{ps} px, JPEG Q90", pr.att_jpeg(f, 90))
        # shift-to-hide: foreign content near the border, then an 8 px shift
        th = H // 4
        for nm, sl in (("Shift+splice: top tile row", (slice(0, th + 8), slice(0, W))),
                       ("Shift+splice: 128 px patch, corner", (slice(H - 160, H - 32), slice(W - 160, W - 32)))):
            f = a["marked"].copy()
            f[sl] = b[sl].astype(np.uint8)
            tally(nm, pr.att_jpeg(shift_down_right(f, 8), 90))
        # fingerprint-band projection (adaptive): paste, then match every fingerprint cell
        ps = 96
        y0, x0 = H // 2 - ps // 2, W // 2 - ps // 2
        f = a["marked"].copy()
        f[y0:y0 + ps, x0:x0 + ps] = b[y0:y0 + ps, x0:x0 + ps].astype(np.uint8)
        for _ in range(2):
            f = band_project(f, a["marked"])
        g = pr.att_jpeg(f, 90)
        tally("Adaptive: 96 px patch + band projection", g)
        lum = lambda u: np.asarray(Image.fromarray(u).convert("L"), np.float64)[y0:y0 + ps, x0:x0 + ps]
        pa, pb, po = lum(g), lum(b.astype(np.uint8)), lum(a["marked"])
        detail.append((np.corrcoef((pa - po).ravel(), (pb - po).ravel())[0, 1], np.mean(np.abs(pa - po))))
        if i == test[3]:
            pad = 48
            crop = lambda u: u[y0 - pad:y0 + ps + pad, x0 - pad:x0 + ps + pad]
            strip = np.concatenate([crop(a["marked"]), crop(g), crop(b.astype(np.uint8))], axis=1)
            Image.fromarray(strip).save(os.path.join(OUT, "e6_adaptive_example.png"))

    # ---------------- (5) cryptographic / ledger attacks ----------------
    crypto = []
    c0 = caps[0]
    rec, root, proof = index[c0["payload"].tobytes().hex()][0]

    def check(name, expect_ok, rec_, root_, proof_):
        ok, why = ver.ledger_ok(rec_, root_, proof_)
        crypto.append((name, "accepted" if ok else f"rejected ({why})", ok == expect_ok))

    check("genuine record", True, rec, root, proof)
    t_rec = json.loads(json.dumps(rec)); t_rec["core"]["fp"] = di.fp_to_hex(fps[1])
    check("record edited to another image's fingerprint", False, t_rec, root, proof)
    t_rec = json.loads(json.dumps(rec)); t_rec["core"]["h_enc"] = "00" * 32
    check("record with altered file hash", False, t_rec, root, proof)
    rogue = di.SensorChip("ROGUE"); rogue.manufacturer = "OEM-A"; rogue.lot_root = chips[0].lot_root; rogue.lot_proof = chips[0].lot_proof
    r_rec = di.make_record(rogue, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    reg.tick(); r_root = ledger.merkle_root([di.record_hash(r_rec)]); reg.register(r_root)
    check("uncertified sensor key (claims a real lot)", False, r_rec, r_root, [])
    f_rec = json.loads(json.dumps(r_rec)); f_rec["sig"] = rec["sig"]
    check("genuine signature on a forged record", False, f_rec, r_root, [])
    victim = chips[1]
    pre = di.make_record(victim, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    reg.tick(); pre_root = ledger.merkle_root([di.record_hash(pre)]); reg.register(pre_root)
    reg.tick(); oem.revoke(victim); reg.tick()
    post = di.make_record(victim, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    post_root = ledger.merkle_root([di.record_hash(post)]); reg.register(post_root)
    check("revoked sensor, sealed before revocation", True, pre, pre_root, [])
    check("revoked sensor, sealed after revocation", False, post, post_root, [])
    late = di.make_record(chips[2], c0["payload"], c0["marked"], c0["enc"], (reg.now + 10_000, b"\3" * 32))
    reg.tick(); late_root = ledger.merkle_root([di.record_hash(late)]); reg.register(late_root)
    check("anchor block later than seal (time inconsistency)", False, late, late_root, [])
    pre_dated = di.make_record(chips[3], c0["payload"], c0["marked"], c0["enc"], (1, b"\4" * 32))
    reg.tick(); pd_root = ledger.merkle_root([di.record_hash(pre_dated)]); reg.register(pd_root)
    check("anchor hash not the chain's (forged early anchor)", False, pre_dated, pd_root, [])
    check("record not notarized", False, caps[3]["rec"], ledger.sha256(b"unsealed"), [])
    # burst: a second frame captured in the same second carries the same payload
    bs = caps[test[0]]
    frame2, _ = pr.embed_rgb(np.clip(bs["rgb"] + 3, 0, 255), bs["coded"], KEY,
                             R_FOR(bs["plan"][2] * bs["plan"][3]), A)
    b_rec = di.make_record(bs["chip"], bs["payload"], frame2, di.jpeg_bytes(frame2, 95),
                           (reg.now, reg.block_hash(reg.now)))
    reg.tick(); b_root = ledger.merkle_root([di.record_hash(b_rec)]); reg.register(b_root)
    index[bs["payload"].tobytes().hex()].append((b_rec, b_root, []))
    v1, _ = ver.verify(None, pr.att_jpeg(bs["marked"], 80))
    v2, _ = ver.verify(None, pr.att_jpeg(frame2, 80))
    crypto.append(("burst: two records share one payload; both resolve",
                   f"first {v1}, second {v2}", v1 == v2 == "Transcoded-consistent"))

    # ---------------- (6) cost ----------------
    rec_size = len(di.canonical(c0["rec"]))
    t_ecdsa = []
    for _ in range(200):
        t0 = time.perf_counter(); di.check_signature(c0["rec"]); t_ecdsa.append(time.perf_counter() - t0)

    # ---------------- report ----------------
    L = []
    L.append("=== E6: device identity + content binding on REAL images (Kodak) ===")
    sizes = sorted({tuple(c['rgb'].shape[:2]) for c in caps})
    L.append(f"images={n} sizes={sizes} A={A} RS(48,16) sensors=8 (P-256, on-die)  lot+batch sealed on ledger")
    L.append(f"fingerprint: {di.FP_GRID}x{di.FP_GRID} tiles over the interior (margin {di.FP_MARGIN} px), "
             f"{di.FP_SIDE}x{di.FP_SIDE} cells per tile, {di.FP_KEEP}x{di.FP_KEEP} DCT incl. DC")
    L.append(f"calibration images={len(cal)} (even indices); all results below are on the {len(test)} held-out images")
    L.append("")
    L.append("(1) Fingerprint distance (max per-tile relative L2)")
    L.append(f"    calibration: genuine under benign suite max {gmax:.3f}   25-35% splices min {smin:.3f}   -> tau={tau}")
    L.append(f"    held-out:    genuine max {max(test_gen):.3f} (p99 {np.percentile(test_gen, 99):.3f})"
             f"   different images min {min(test_imp):.3f} (median {np.median(test_imp):.3f})")
    L.append("")
    L.append("(2) End-to-end verdicts (CO = Camera-original, TC = Transcoded-consistent, U = Unverified)")
    L.append(f"    {'Condition':<26}{'CO':>4}{'TC':>5}{'U':>5}")
    for name, vs in verdicts.items():
        L.append(f"    {name:<26}{vs.count('Camera-original'):>4}{vs.count('Transcoded-consistent'):>5}{vs.count('Unverified'):>5}")
    L.append(f"    {'Unmarked originals':<26}{unmarked.count('Camera-original'):>4}"
             f"{unmarked.count('Transcoded-consistent'):>5}{unmarked.count('Unverified'):>5}")
    L.append(f"    processed genuine copies verified: {rate(genuine_ok, genuine_total)}")
    L.append(f"    reasons for Unverified genuine verdicts: {dict(reasons)}")
    L.append("")
    L.append("(3) Cross-scene copy attacks (A's mark onto a different image B)")
    for kind, (tr, wm, acc) in copy.items():
        L.append(f"    {kind:<14} watermark decodes A's payload={wm}/{tr}  end-to-end accepted={rate(acc, tr)}")
    L.append("")
    L.append("(4) Local edits of a genuine capture (accepted = verified as Transcoded-consistent)")
    for name, (tr, dec, acc) in local.items():
        L.append(f"    {name:<42} payload decodes={dec}/{tr}  accepted={rate(acc, tr)}")
    L.append(f"    adaptive patches: donor-detail correlation {np.mean([d[0] for d in detail]):.2f}, "
             f"mean |change| inside patch {np.mean([d[1] for d in detail]):.1f} gray levels")
    L.append("")
    L.append("(5) Cryptographic / ledger attacks")
    for name, res, as_expected in crypto:
        L.append(f"    {'PASS' if as_expected else 'FAIL'}  {name:<52} {res}")
    L.append("")
    L.append("(6) Cost per capture")
    L.append(f"    record size (canonical JSON incl. signature + lot proof): {rec_size} B")
    L.append(f"    chip signing (incl. fingerprint): {1000*np.mean(t_sign):.1f} ms   "
             f"ECDSA P-256 verify: {1000*np.median(t_ecdsa):.3f} ms   full verify of a file: {1000*np.mean(t_verify):.1f} ms")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e6_device_identity.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
