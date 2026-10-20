"""Keyless copy and removal attacks against the PixelRoot in-pixel channel.
Attacker holds ONE marked image, no key, no original. Estimates the mark as the
host-suppressed (0,2)-projection field (public basis) and (a) pastes it onto a
different image, (b) subtracts it from the marked image."""
import sys, numpy as np
sys.path.insert(0, "/home/user/PixelRoot/paper/experiments")
import pixelroot as pr
from skimage import data
from scipy.ndimage import uniform_filter

S = 512; NB = S // 8
imgs = []
for n in ['astronaut','camera','immunohistochemistry','retina','hubble_deep_field','moon','grass','gravel','brick']:
    a = getattr(data, n)()
    if a.ndim == 2: a = np.stack([a]*3, -1)
    a = a[..., :3].astype(np.float64)
    H, W = a.shape[:2]
    for y0 in range(0, H - S + 1, S):
        for x0 in range(0, W - S + 1, S):
            imgs.append((f"{n}@{y0},{x0}", a[y0:y0+S, x0:x0+S]))
KEY, A = "PIXELROOT-OEM-KEY-v2", 4.0

def est_mark(y, nbh, nbw, gain=1.0):
    yb = pr.to_blocks(y[:nbh*8, :nbw*8])
    proj = np.sum(yb * pr.P8, axis=(2, 3)) / pr.P8_ENERGY
    hp = proj - uniform_filter(proj, size=5, mode="nearest")
    return pr.from_blocks(gain * hp[:, :, None, None] * pr.P8[None, None])

def decode(rgb_u8, plan, coded):
    y = pr.rgb_to_y(rgb_u8.astype(np.float64))
    bits, _ = pr.extract_y(y, plan, len(coded))
    dec, ok = pr.rs_decode_bits(bits)
    return pr.ber(coded, bits), dec, ok

for jpegQ in [None, 75]:
    copy_ok = rem_ok = base_ok = trials = 0
    for i, (na, rgbA) in enumerate(imgs):
        payload = np.random.RandomState(i).randint(0, 256, 16).astype(np.uint8)
        coded, _ = pr.rs_encode_bits(payload)
        nb = NB * NB
        R = nb // len(coded)
        marked, plan = pr.embed_rgb(rgbA, coded, KEY, R, A)
        if jpegQ: marked = pr.att_jpeg(marked, jpegQ)   # attacker sees a shared JPEG
        b, dec, ok = decode(marked, plan, coded); good = bool(ok and dec == payload.tobytes()); base_ok += good
        if not good: continue
        mk = est_mark(pr.rgb_to_y(marked.astype(np.float64)), NB, NB, gain=1.5)
        # (a) copy onto every other image
        for j, (nb_, rgbB) in enumerate(imgs):
            if j == i: continue
            forged = np.clip(np.round(rgbB + mk[..., None]), 0, 255).astype(np.uint8)
            _, d, o = decode(forged, plan, coded)
            copy_ok += o and d == payload.tobytes(); trials += 1
        # (b) removal
        cleaned = np.clip(np.round(marked.astype(np.float64) - mk[..., None] / 1.5 * 1.2), 0, 255).astype(np.uint8)
        _, d, o = decode(cleaned, plan, coded); rem_ok += o and d == payload.tobytes()
    n = len(imgs)
    print(f"source={'JPEG Q%d' % jpegQ if jpegQ else 'lossless'}  images={n}  R={R}")
    print(f"  genuine decode          {base_ok}/{n}")
    print(f"  keyless copy -> forged B decodes as A's payload: {copy_ok}/{trials}")
    print(f"  keyless removal -> payload still decodes:        {rem_ok}/{base_ok}")
