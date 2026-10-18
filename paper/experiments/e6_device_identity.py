"""
E6 -- Device identity and content binding on REAL images (Kodak).

Exercises the full PixelRoot verification path: sensor-held P-256 keys certified
on chain by production lot, chip-signed capture records (raw hash, camera-encoding
hash, content fingerprint, block anchor), Merkle-batched notarization, in-pixel
payload decoding, and the verifier's verdicts. Measures:

  (1) fingerprint separation: genuine-under-processing vs. different-image
  (2) end-to-end verdicts under the benign attack suite
  (3) copy attacks (keyless estimate, and with the original) -- watermark level
      vs. end-to-end acceptance
  (4) coarse-structure transplant (adaptive copy attack) and splices
  (5) cryptographic/ledger attacks (tampered record, uncertified or revoked
      sensor, anchor/seal ordering)
  (6) per-capture cost (sign/verify time, record size)

Outputs: results/e6_device_identity.txt
"""
import glob
import hashlib
import io
import json
import os
import time

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


def benign_attacks():
    """The supported envelope of Table II (no rotation / resized-crop)."""
    out = []
    for name, fn, _ in pr.standard_attacks():
        if "[lim]" in name or name == "JPEG Q5":
            continue
        out.append((name, fn))
    return out


def keyless_mark_estimate(y, nbh, nbw, gain):
    yb = pr.to_blocks(y[: nbh * 8, : nbw * 8])
    proj = np.sum(yb * pr.P8, axis=(2, 3)) / pr.P8_ENERGY
    hp = proj - uniform_filter(proj, size=5, mode="nearest")
    return pr.from_blocks(gain * hp[:, :, None, None] * pr.P8[None, None])


def lowpass(rgb, side=16):
    """Coarse structure: downsample to side x side and back (bilinear)."""
    h, w, _ = rgb.shape
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    return np.asarray(im.resize((side, side), Image.BOX).resize((w, h), Image.BILINEAR), dtype=np.float64)


def main():
    reg = ledger.Registry()
    oem = di.Manufacturer("OEM-A", reg)
    chips, _ = oem.produce_lot(8)
    reg.tick()

    # ---------------- capture: embed, sign, batch, notarize ----------------
    caps = []
    records = []
    t_sign = []
    for idx, path in enumerate(DATA):
        rgb = pr.load_rgb(path)
        payload = np.random.RandomState(1000 + idx).randint(0, 256, pr.PAYLOAD_BYTES).astype(np.uint8)
        coded, _ = pr.rs_encode_bits(payload)
        H8, W8 = (rgb.shape[0] // 8) * 8, (rgb.shape[1] // 8) * 8
        R = R_FOR((H8 // 8) * (W8 // 8))
        marked, plan = pr.embed_rgb(rgb, coded, KEY, R, A)
        enc = di.jpeg_bytes(marked, 95)
        anchor = (reg.now, reg.block_hash(reg.now))
        chip = chips[idx % len(chips)]
        t0 = time.perf_counter()
        rec = di.make_record(chip, payload, marked, enc, anchor)
        t_sign.append(time.perf_counter() - t0)
        caps.append({"rgb": rgb[:H8, :W8], "marked": marked, "enc": enc, "payload": payload,
                     "coded": coded, "plan": plan, "rec": rec, "chip": chip})
        records.append(rec)
    reg.tick()
    hashes = [di.record_hash(r) for r in records]
    batch_root = ledger.merkle_root(hashes)
    reg.register(batch_root)
    index = {c["payload"].tobytes().hex(): (c["rec"], batch_root, ledger.merkle_proof(hashes, i)) for i, c in enumerate(caps)}

    # ---------------- (1) fingerprint calibration (even images) ----------------
    attacks = benign_attacks()
    n = len(caps)
    cal = [i for i in range(n) if i % 2 == 0]
    test = [i for i in range(n) if i % 2 == 1]
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
        return di.fp_distance(fps[i], di.fingerprint(al), di.lost_tiles(off))

    def splices(i, k):
        a_ = caps[i]
        H, W, _ = a_["marked"].shape
        donor = next(caps[(i + 5 + d) % n]["rgb"] for d in range(n)
                     if caps[(i + 5 + d) % n]["rgb"].shape[:2] == (H, W) and (i + 5 + d) % n != i)
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
    verdicts = {}
    t_verify = []
    for i in test:
        c = caps[i]
        t0 = time.perf_counter()
        v, _ = ver.verify(c["enc"], np.asarray(Image.open(io.BytesIO(c["enc"])).convert("RGB")))
        t_verify.append(time.perf_counter() - t0)
        verdicts.setdefault("Camera JPEG (exact file)", []).append(v)
        for name, _ in attacks:
            verdicts.setdefault(name, []).append(ver.verify(None, attacked[(i, name)])[0])
    unmarked = [ver.verify(None, caps[i]["rgb"].astype(np.uint8))[0] for i in test]

    # ---------------- (3) copy attacks (held-out images) ----------------
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

    # ---------------- (4a) coarse-structure transplant (held-out) ----------------
    alphas = [0.25, 0.5, 0.75, 0.9, 1.0]
    transplant = {al: [0, 0, [], []] for al in alphas}  # trials, accepted, psnr vs B, psnr vs A
    for k_, i in enumerate(test):
        a = caps[i]
        j = next(test[(k_ + d) % len(test)] for d in range(1, len(test))
                 if caps[test[(k_ + d) % len(test)]]["rgb"].shape == a["rgb"].shape)
        b = caps[j]
        resid = a["marked"].astype(np.float64) - a["rgb"]
        for al in alphas:
            base = b["rgb"] + al * (lowpass(a["marked"].astype(np.float64)) - lowpass(b["rgb"]))
            forged = np.clip(np.round(base + resid), 0, 255).astype(np.uint8)
            t = transplant[al]
            t[0] += 1
            t[1] += int(ver.verify(None, forged)[0] != "Unverified")
            t[2].append(pr.psnr(b["rgb"].astype(np.uint8), forged))
            t[3].append(pr.psnr(a["marked"], forged))

    # ---------------- (4b) splices (held-out) ----------------
    splice = [0, 0, 0]  # trials, payload still decodes, accepted
    for i in test:
        for f in splices(i, np.random.RandomState(100 + i)):
            v, why = ver.verify(None, f)
            splice[0] += 1
            splice[1] += int(why != "no payload")
            splice[2] += int(v != "Unverified")

    # ---------------- (5) cryptographic / ledger attacks ----------------
    crypto = []
    c0 = caps[0]
    rec, root, proof = index[c0["payload"].tobytes().hex()]

    def check(name, expect_ok, rec_, root_, proof_):
        ok, why = ver.ledger_ok(rec_, root_, proof_)
        crypto.append((name, "accepted" if ok else f"rejected ({why})", ok == expect_ok))

    check("genuine record", True, rec, root, proof)
    t_rec = json.loads(json.dumps(rec)); t_rec["core"]["fp"] = di.fp_to_hex(fps[1])
    check("record edited to another image's fingerprint", False, t_rec, root, proof)
    t_rec = json.loads(json.dumps(rec)); t_rec["core"]["h_enc"] = "00" * 32
    check("record with altered file hash", False, t_rec, root, proof)
    # uncertified sensor: a chip from a manufacturer that never registered its lot
    rogue = di.SensorChip("ROGUE"); rogue.lot_root = chips[0].lot_root; rogue.lot_proof = chips[0].lot_proof
    r_rec = di.make_record(rogue, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    reg.tick(); r_root = ledger.merkle_root([di.record_hash(r_rec)]); reg.register(r_root)
    check("uncertified sensor key (claims a real lot)", False, r_rec, r_root, [])
    # signature transplanted from a genuine record onto a forged core
    f_rec = json.loads(json.dumps(r_rec)); f_rec["sig"] = rec["sig"]
    check("genuine signature on a forged record", False, f_rec, r_root, [])
    # revocation: capture before revocation stays valid, capture after fails
    victim = chips[1]
    pre = di.make_record(victim, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    reg.tick(); pre_root = ledger.merkle_root([di.record_hash(pre)]); reg.register(pre_root)
    reg.tick(); oem.revoke(victim); reg.tick()
    post = di.make_record(victim, c0["payload"], c0["marked"], c0["enc"], (reg.now, reg.block_hash(reg.now)))
    post_root = ledger.merkle_root([di.record_hash(post)]); reg.register(post_root)
    check("revoked sensor, sealed before revocation", True, pre, pre_root, [])
    check("revoked sensor, sealed after revocation", False, post, post_root, [])
    # record claiming a block anchor later than its sealing time
    late = di.make_record(chips[2], c0["payload"], c0["marked"], c0["enc"], (reg.now + 10_000, b"\3" * 32))
    reg.tick(); late_root = ledger.merkle_root([di.record_hash(late)]); reg.register(late_root)
    check("anchor block later than seal (time inconsistency)", False, late, late_root, [])
    # pre-dated record: claims an old anchor block but cannot know its hash in advance
    pre_dated = di.make_record(chips[3], c0["payload"], c0["marked"], c0["enc"], (1, b"\4" * 32))
    reg.tick(); pd_root = ledger.merkle_root([di.record_hash(pre_dated)]); reg.register(pd_root)
    check("anchor hash not the chain's (forged early anchor)", False, pre_dated, pd_root, [])
    check("record not notarized", False, caps[3]["rec"], ledger.sha256(b"unsealed"), [])

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
    L.append("")
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
    L.append("")
    L.append("(3) Copy attacks (A's mark onto a different image B)")
    for kind, (tr, wm, acc) in copy.items():
        L.append(f"    {kind:<14} trials={tr}  watermark decodes A's payload={wm}  end-to-end accepted={acc}")
    L.append("")
    L.append("(4a) Coarse-structure transplant: B + alpha*(lowres(A)-lowres(B)) + A's mark")
    for al, (tr, acc, pb, pa) in transplant.items():
        L.append(f"    alpha={al:<5} accepted={acc}/{tr}  PSNR(forged,B)={np.mean(pb):.1f} dB  PSNR(forged,A)={np.mean(pa):.1f} dB")
    L.append(f"(4b) Splices (25%/35% side, then JPEG Q90): trials={splice[0]}  payload still decodes={splice[1]}"
             f"  accepted={splice[2]}")
    L.append("")
    L.append("(5) Cryptographic / ledger attacks")
    for name, res, as_expected in crypto:
        L.append(f"    {'PASS' if as_expected else 'FAIL'}  {name:<48} {res}")
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
