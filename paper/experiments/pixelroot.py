"""
PixelRoot core: keyed spread-spectrum in-pixel embedding on REAL images, with a
real (libjpeg/WebP) codec attack suite. Faithful port of experiments/sim.js, but
operating on natural photographs (luminance channel of RGB) and using actual
image codecs rather than a luminance-only DCT JPEG approximation.

Carrier: the (u=0, v=2) 8x8 DCT basis -- a smooth horizontal (per-column) gain
ramp that is zero-mean over the block (imperceptible) and low-frequency (survives
JPEG). Payload bits are spread over R keyed blocks with antipodal +/-1 chips and
recovered by correlation de-spreading.

Author: PixelRoot project. Dependencies: numpy, Pillow, scikit-image.
"""
import hashlib
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from skimage.metrics import peak_signal_noise_ratio as sk_psnr
from skimage.metrics import structural_similarity as sk_ssim

# ----------------------------- carrier basis -----------------------------
def _dct_basis(u, v):
    """8x8 separable DCT-II basis image for indices (u,v), zero-mean if u or v>0."""
    x = np.arange(8)
    cu = np.cos((2 * x + 1) * u * np.pi / 16)
    cv = np.cos((2 * x + 1) * v * np.pi / 16)
    return np.outer(cu, cv)  # rows indexed by u-direction, cols by v-direction

P8 = _dct_basis(0, 2)            # horizontal ramp (per-column gain), zero-mean
P8_ENERGY = float(np.sum(P8 * P8))

# ----------------------------- Reed-Solomon ECC --------------------------
# The paper protects the 16-byte (128-bit) payload with Reed-Solomon ECC. We use
# a real RS codec (reedsolo) so the end-to-end decode is genuine, not simulated.
import reedsolo

PAYLOAD_BYTES = 16          # 128-bit provenance payload
RS_NSYM = 32                # parity symbols -> RS(48,16), corrects up to 16 byte errors

def rs_encode_bits(payload_bytes, nsym=RS_NSYM):
    """16 payload bytes -> RS codeword -> bit array (MSB first)."""
    rsc = reedsolo.RSCodec(nsym)
    code = bytes(rsc.encode(bytes(payload_bytes)))
    bits = np.unpackbits(np.frombuffer(code, dtype=np.uint8))
    return bits.astype(np.int8), len(code)

def rs_decode_bits(bits, nsym=RS_NSYM):
    """bit array -> bytes -> RS decode. Returns (payload_bytes or None, ok)."""
    nbytes = len(bits) // 8
    byte_arr = np.packbits(bits[: nbytes * 8].astype(np.uint8)).tobytes()
    rsc = reedsolo.RSCodec(nsym)
    try:
        dec = rsc.decode(byte_arr)[0]
        return bytes(dec[:PAYLOAD_BYTES]), True
    except reedsolo.ReedSolomonError:
        return None, False

# ----------------------------- keyed plan --------------------------------
def keyed_plan(key, payload_bits, R, n_blocks, salt=b""):
    """Deterministic keyed assignment of R distinct blocks (+antipodal chip) per
    payload bit. The deployed design keys a CSPRNG with the full digest
    s = SHA-256(key||salt) (see paper sec:select); this prototype reduces s to a
    32-bit seed because NumPy's legacy RandomState caps seeds at 2^32. This does
    not affect the measured robustness/false-accept results, which depend on key
    mismatch (wrong key -> wrong carriers), not on seed width."""
    seed = int.from_bytes(hashlib.sha256(bytes(str(key), "utf8") + salt).digest()[:4], "big")
    rng = np.random.RandomState(seed)
    perm = rng.permutation(n_blocks)
    need = payload_bits * R
    assert need <= n_blocks, f"need {need} blocks, have {n_blocks}"
    chosen = perm[:need]
    chips = rng.choice(np.array([-1, 1]), size=need)
    bit_of = np.full(n_blocks, -1, dtype=np.int32)
    chip_of = np.zeros(n_blocks, dtype=np.float64)
    bit_of[chosen] = np.repeat(np.arange(payload_bits), R)
    chip_of[chosen] = chips
    return bit_of, chip_of

# ----------------------------- color helpers -----------------------------
def rgb_to_y(arr):
    """BT.601 luma from float RGB [0,255]."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return 0.299 * r + 0.587 * g + 0.114 * b

def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)

def to_blocks(y):
    """H x W -> (H/8, W/8, 8, 8) view-compatible copy."""
    H, W = y.shape
    return y.reshape(H // 8, 8, W // 8, 8).transpose(0, 2, 1, 3)

def from_blocks(b):
    nbh, nbw, _, _ = b.shape
    return b.transpose(0, 2, 1, 3).reshape(nbh * 8, nbw * 8)

# ----------------------------- embed / extract ---------------------------
def embed_rgb(rgb, bits, key, R, A, salt=b""):
    """Embed payload into the Y channel of an RGB image; return marked RGB uint8
    and the plan (for extraction). Operates on the 8x8-cropped region."""
    H, W, _ = rgb.shape
    H8, W8 = (H // 8) * 8, (W // 8) * 8
    rgb = rgb[:H8, :W8]
    y = rgb_to_y(rgb)
    nbh, nbw = H8 // 8, W8 // 8
    n_blocks = nbh * nbw
    bit_of, chip_of = keyed_plan(key, len(bits), R, n_blocks, salt)
    sign = (2 * bits.astype(np.float64) - 1)  # +/-1 per payload bit
    amp = np.zeros(n_blocks)
    assigned = bit_of >= 0
    amp[assigned] = A * chip_of[assigned] * sign[bit_of[assigned]]
    amp2d = amp.reshape(nbh, nbw)
    yb = to_blocks(y).copy()
    yb += amp2d[:, :, None, None] * P8[None, None, :, :]
    y_marked = from_blocks(yb)
    # add the Y delta back to RGB (modulate luma -> distribute to channels)
    dy = (y_marked - y)
    out = rgb + dy[..., None]
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    return out, (bit_of, chip_of, nbh, nbw)

from scipy.ndimage import uniform_filter

def _project_field(y, nbh, nbw, suppress=True):
    """Project every 8x8 block onto the carrier; optionally cancel the (smoothly
    varying) host content by subtracting a local average of the projection field.
    The embedded chips are zero-mean random per block, so they survive the
    high-pass while the host's low-frequency (0,2)-coefficient is removed."""
    yb = to_blocks(y[: nbh * 8, : nbw * 8])
    proj = np.sum(yb * P8[None, None, :, :], axis=(2, 3)) / P8_ENERGY  # nbh x nbw
    if suppress:
        proj = proj - uniform_filter(proj, size=5, mode="nearest")
    return proj.reshape(-1)

def extract_y(y, plan, payload_bits, offset=(0, 0), suppress=True):
    """Correlation de-spread decode; offset shifts the block grid (resync)."""
    bit_of, chip_of, nbh, nbw = plan
    oy, ox = offset
    if oy or ox:
        y = np.roll(np.roll(y, -oy, axis=0), -ox, axis=1)
    proj = _project_field(y, nbh, nbw, suppress)
    assigned = bit_of >= 0
    contrib = proj[assigned] * chip_of[assigned]
    acc = np.bincount(bit_of[assigned], weights=contrib, minlength=payload_bits)
    bits = (acc >= 0).astype(np.int8)
    conf = float(np.sum(np.abs(acc)))
    return bits, conf

def extract_resync(y, plan, payload_bits, max_off=8):
    """Coarse-to-fine block-grid offset search (max confidence). Coarse stride-4
    pass over +/-max_off, then a +/-3 refine around the best coarse offset."""
    def best_over(offs_y, offs_x, best):
        for oy in offs_y:
            for ox in offs_x:
                bits, conf = extract_y(y, plan, payload_bits, (oy, ox))
                if best is None or conf > best[1]:
                    best = (bits, conf, (oy, ox))
        return best
    coarse = list(range(-max_off, max_off + 1, 4))
    best = best_over(coarse, coarse, None)
    cy, cx = best[2]
    fine_y = range(max(-max_off, cy - 3), min(max_off, cy + 3) + 1)
    fine_x = range(max(-max_off, cx - 3), min(max_off, cx + 3) + 1)
    best = best_over(fine_y, fine_x, best)
    return best

# ----------------------------- metrics -----------------------------------
def psnr(a, b):
    return float(sk_psnr(a.astype(np.uint8), b.astype(np.uint8), data_range=255))

def ssim(a, b):
    return float(sk_ssim(a.astype(np.uint8), b.astype(np.uint8), channel_axis=2, data_range=255))

def ber(a, b):
    a = np.asarray(a).astype(np.int8); b = np.asarray(b).astype(np.int8)
    return float(np.mean(a != b))

# ----------------------------- attacks (real codecs) ---------------------
def att_jpeg(rgb_u8, Q):
    buf = io.BytesIO()
    Image.fromarray(rgb_u8).save(buf, format="JPEG", quality=int(Q))  # libjpeg, 4:2:0
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("RGB"), dtype=np.uint8)

def att_webp(rgb_u8, Q):
    buf = io.BytesIO()
    Image.fromarray(rgb_u8).save(buf, format="WEBP", quality=int(Q))
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("RGB"), dtype=np.uint8)

def att_noise(rgb_u8, sigma, seed=0):
    rng = np.random.RandomState(seed)
    n = rng.normal(0, sigma, rgb_u8.shape)
    return np.clip(np.round(rgb_u8 + n), 0, 255).astype(np.uint8)

def att_blur(rgb_u8, radius):
    return np.asarray(Image.fromarray(rgb_u8).filter(ImageFilter.GaussianBlur(radius)), dtype=np.uint8)

def att_resize(rgb_u8, factor):
    im = Image.fromarray(rgb_u8)
    w, h = im.size
    small = im.resize((max(8, int(w * factor)), max(8, int(h * factor))), Image.BILINEAR)
    back = small.resize((w, h), Image.BILINEAR)
    return np.asarray(back, dtype=np.uint8)

def att_rotate(rgb_u8, deg):
    im = Image.fromarray(rgb_u8).rotate(deg, resample=Image.BILINEAR, expand=False)
    return np.asarray(im, dtype=np.uint8)

def att_brightness(rgb_u8, f):
    return np.asarray(ImageEnhance.Brightness(Image.fromarray(rgb_u8)).enhance(f), dtype=np.uint8)

def att_contrast(rgb_u8, f):
    return np.asarray(ImageEnhance.Contrast(Image.fromarray(rgb_u8)).enhance(f), dtype=np.uint8)

def att_gamma(rgb_u8, g):
    lut = np.clip(((np.arange(256) / 255.0) ** g) * 255.0, 0, 255).astype(np.uint8)
    return lut[rgb_u8]

def att_crop_pad(rgb_u8, frac):
    """Translational crop: drop a top-left border of frac and edge-replicate-pad
    back to original size. This is a PURE integer shift of the block grid, which
    the resync search recovers (no rescaling)."""
    h, w, _ = rgb_u8.shape
    cy, cx = int(h * frac), int(w * frac)
    cropped = rgb_u8[cy:, cx:]
    return np.pad(cropped, ((0, cy), (0, cx), (0, 0)), mode="edge")

def att_resized_crop(rgb_u8, frac):
    """WAVES-style resized-crop: center-crop then rescale back (changes grid scale,
    not just a shift) -- a harder geometric attack reported separately."""
    h, w, _ = rgb_u8.shape
    cy, cx = int(h * frac), int(w * frac)
    cropped = rgb_u8[cy:h - cy, cx:w - cx]
    return np.asarray(Image.fromarray(cropped).resize((w, h), Image.BILINEAR), dtype=np.uint8)


# ----------------------------- per-pixel localization layer --------------
def fragile_pattern(shape, key):
    seed = int.from_bytes(hashlib.sha256(b"frag" + bytes(str(key), "utf8")).digest()[:4], "big")
    rng = np.random.RandomState(seed)
    return rng.choice(np.array([-1.0, 1.0]), size=shape)

def embed_fragile_rgb(rgb, key, delta):
    """Add a keyed +/-delta per-pixel pattern to the luma -> RGB. Returns marked
    uint8 RGB and the pattern (verifier-side known from the key)."""
    H, W, _ = rgb.shape
    pat = fragile_pattern((H, W), key)
    out = np.clip(np.round(rgb + delta * pat[..., None]), 0, 255).astype(np.uint8)
    return out, pat

def fragile_block_stat(y, pat, bs):
    """Per-block matched-filter statistic mean((y-meanblk)*(pat-meanblk)). Genuine
    block ~ delta, tampered (foreign / no pattern) block ~ 0."""
    H, W = y.shape
    nbh, nbw = H // bs, W // bs
    yb = y[: nbh * bs, : nbw * bs].reshape(nbh, bs, nbw, bs).transpose(0, 2, 1, 3)
    pb = pat[: nbh * bs, : nbw * bs].reshape(nbh, bs, nbw, bs).transpose(0, 2, 1, 3)
    ym = yb.mean(axis=(2, 3), keepdims=True)
    pm = pb.mean(axis=(2, 3), keepdims=True)
    stat = ((yb - ym) * (pb - pm)).mean(axis=(2, 3))
    return stat  # nbh x nbw

def standard_attacks():
    """WAVES-aligned suite: name -> (callable(rgb_u8)->rgb_u8, needs_resync)."""
    A = []
    for q in [95, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5]:
        A.append((f"JPEG Q{q}", lambda im, q=q: att_jpeg(im, q), False))
    for q in [80, 60]:
        A.append((f"WebP q{q}", lambda im, q=q: att_webp(im, q), False))
    for s in [2, 5, 10, 20]:
        A.append((f"Noise s{s}", lambda im, s=s: att_noise(im, s), False))
    for r in [0.5, 1.0]:
        A.append((f"Blur r{r}", lambda im, r=r: att_blur(im, r), False))
    for f in [0.5, 0.75, 1.5]:
        A.append((f"Resize {f}x", lambda im, f=f: att_resize(im, f), False))
    for f in [0.9, 1.1]:
        A.append((f"Brightness {f}", lambda im, f=f: att_brightness(im, f), False))
    for f in [0.9, 1.1]:
        A.append((f"Contrast {f}", lambda im, f=f: att_contrast(im, f), False))
    for g in [0.9, 1.1]:
        A.append((f"Gamma {g}", lambda im, g=g: att_gamma(im, g), False))
    for frac in [0.01, 0.02, 0.03]:
        A.append((f"Crop {int(frac*100)}%", lambda im, frac=frac: att_crop_pad(im, frac), True))
    # geometric-limit attacks (expected to need explicit sync; reported separately)
    for d in [1, 2]:
        A.append((f"Rotate {d}deg [lim]", lambda im, d=d: att_rotate(im, d), True))
    A.append(("ResizedCrop 3% [lim]", lambda im: att_resized_crop(im, 0.03), True))
    # combos
    A.append(("JPEG70+Resize0.75", lambda im: att_jpeg(att_resize(im, 0.75), 70), False))
    A.append(("JPEG50+Noise5", lambda im: att_noise(att_jpeg(im, 50), 5), False))
    A.append(("Resize0.75+JPEG40", lambda im: att_jpeg(att_resize(im, 0.75), 40), False))
    return A
