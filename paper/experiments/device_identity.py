"""
PixelRoot device identity: sensor-held signing keys, manufacturer-certified
production lots, signed capture records, content fingerprints, and the
end-to-end verifier that combines them with the in-pixel payload and the ledger.

The sensor key is generated inside the chip at manufacture and never leaves it
(modelled by SensorChip, which exposes only its public key and a sign() call).
The manufacturer certifies the SHA-256 of each public key by sealing the
Merkle root of a production lot on chain (ledger.Registry / PixelRootRegistry).
Each capture produces a record that the chip signs; only the record's hash is
batched on chain. A verifier needs no secret beyond the in-pixel carrier key.

Dependencies: numpy, Pillow, scipy, cryptography, plus pixelroot.py and ledger.py.
"""
import hashlib
import io
import json

import numpy as np
from PIL import Image
from scipy.fft import dctn
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

import ledger
import pixelroot as pr

RECORD_VERSION = 2

# ----------------------------------------------------------------- sensors

class SensorChip:
    """A CMOS sensor with an on-die P-256 key pair. The private key is created
    inside the chip and is not exported; callers only get sign() and the
    public key. `serial` stands in for the OTP identity fuses."""

    def __init__(self, serial):
        self.serial = serial
        self._key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self._key.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)

    @property
    def key_hash(self):
        return hashlib.sha256(self.public_key).digest()

    def sign(self, message):
        return self._key.sign(message, ec.ECDSA(hashes.SHA256()))


class Manufacturer:
    """Certifies a production lot of sensors by sealing its Merkle root."""

    def __init__(self, name, registry):
        self.name, self.registry = name, registry
        registry.add_manufacturer(name)

    def produce_lot(self, n, prefix="S"):
        chips = [SensorChip(f"{prefix}{i:05d}") for i in range(n)]
        key_hashes = [c.key_hash for c in chips]
        lot_root = ledger.merkle_root(key_hashes)
        self.registry.register_lot(self.name, lot_root)
        for i, c in enumerate(chips):
            c.lot_root = lot_root
            c.lot_proof = ledger.merkle_proof(key_hashes, i)
        return chips, key_hashes

    def revoke(self, chip):
        self.registry.revoke_device(self.name, chip.lot_root, chip.key_hash, chip.lot_proof)

# ------------------------------------------------------- content fingerprint

FP_GRID = 4      # 4x4 tiles
FP_SIDE = 32     # each tile is box-downsampled to 32x32 luma
FP_KEEP = 8      # keep the 8x8 lowest DCT coefficients, minus DC -> 63 per tile
FP_FLOOR = 800.0 # energy floor so flat tiles (sky, walls) do not dominate


def _tile_box(W, H, tx, ty):
    return (tx * W // FP_GRID, ty * H // FP_GRID, (tx + 1) * W // FP_GRID, (ty + 1) * H // FP_GRID)


def fingerprint(rgb_u8):
    """Robust content fingerprint: for each tile of a 4x4 grid, the 63 lowest
    non-DC DCT coefficients of its 32x32 box-downsampled luma, quantised to int8
    with a per-tile scale (1,072 bytes). Stable under compression, noise, mild
    blur, rescaling and photometric edits; changes when a tile's content does."""
    g = Image.fromarray(np.asarray(rgb_u8, dtype=np.uint8)).convert("L")
    W, H = g.size
    feats = np.zeros((FP_GRID * FP_GRID, FP_KEEP * FP_KEEP - 1))
    for ty in range(FP_GRID):
        for tx in range(FP_GRID):
            a = np.asarray(g.crop(_tile_box(W, H, tx, ty)).resize((FP_SIDE, FP_SIDE), Image.BOX), dtype=np.float64)
            feats[ty * FP_GRID + tx] = dctn(a, norm="ortho")[:FP_KEEP, :FP_KEEP].ravel()[1:]
    return feats


def fp_distance(ref, test, skip=()):
    """Largest per-tile relative L2 distance ||ref - test|| / (||ref|| + floor),
    ignoring tiles in `skip` (tiles the verifier knows were cropped away)."""
    d = np.linalg.norm(ref - test, axis=1) / (np.linalg.norm(ref, axis=1) + FP_FLOOR)
    keep = [i for i in range(len(d)) if i not in set(skip)]
    return float(d[keep].max()) if keep else float("inf")


def fp_to_hex(fp):
    scale = np.maximum(np.abs(fp).max(axis=1), 1e-9) / 127.0
    q = np.round(fp / scale[:, None]).astype(np.int8)
    return (scale.astype(np.float32).tobytes() + q.tobytes()).hex()


def fp_from_hex(h):
    raw = bytes.fromhex(h)
    n = FP_GRID * FP_GRID
    scale = np.frombuffer(raw[: 4 * n], dtype=np.float32).astype(np.float64)
    q = np.frombuffer(raw[4 * n:], dtype=np.int8).astype(np.float64).reshape(n, -1)
    return q * scale[:, None]


def lost_tiles(offset):
    """Tiles that intersect the border a translational crop removed. `offset`
    is the block-grid resync offset (oy, ox) found by the in-pixel decoder."""
    oy, ox = offset
    rows = ({0} if oy < 0 else set()) | ({FP_GRID - 1} if oy > 0 else set())
    cols = ({0} if ox < 0 else set()) | ({FP_GRID - 1} if ox > 0 else set())
    return {r * FP_GRID + c for r in range(FP_GRID) for c in range(FP_GRID) if r in rows or c in cols}

# ------------------------------------------------------------ capture record

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def jpeg_bytes(rgb_u8, q=95):
    buf = io.BytesIO()
    Image.fromarray(rgb_u8).save(buf, format="JPEG", quality=q)
    return buf.getvalue()


def make_record(chip, payload, marked_u8, encoded, anchor):
    """Build and sign the capture record for one frame. Hashes cover the raw
    readout and the camera's own encoding (so V1 works on the delivered file);
    the fingerprint binds the in-pixel payload to this scene; `anchor` is a
    recent block (number, hash) giving a lower bound on capture time."""
    core = {
        "v": RECORD_VERSION,
        "sensor_pub": chip.public_key.hex(),
        "lot_root": chip.lot_root.hex(),
        "payload": bytes(payload).hex(),
        "h_raw": hashlib.sha256(marked_u8.tobytes()).hexdigest(),
        "h_enc": hashlib.sha256(encoded).hexdigest(),
        "fp": fp_to_hex(fingerprint(marked_u8)),
        "anchor_block": anchor[0],
        "anchor_hash": anchor[1].hex(),
    }
    sig = chip.sign(canonical(core))
    rec = {"core": core, "sig": sig.hex(), "lot_proof": [p.hex() for p in chip.lot_proof]}
    return rec


def record_hash(rec):
    return hashlib.sha256(canonical(rec["core"]) + bytes.fromhex(rec["sig"])).digest()


def check_signature(rec):
    pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(rec["core"]["sensor_pub"]))
    try:
        pub.verify(bytes.fromhex(rec["sig"]), canonical(rec["core"]), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False

# ----------------------------------------------------------------- verifier

class Verifier:
    """End-to-end verification of a questioned file. `index` maps an in-pixel
    payload to its published record and Merkle proof (the off-chain record
    store); `registry` is the ledger; `tau` bounds the fingerprint distance."""

    def __init__(self, registry, index, carrier_key, R_for, tau, max_off=28):
        self.registry, self.index, self.key = registry, index, carrier_key
        self.R_for, self.tau, self.max_off = R_for, tau, max_off

    def ledger_ok(self, rec, batch_root, proof):
        if not check_signature(rec):
            return False, "bad signature"
        core = rec["core"]
        key_hash = hashlib.sha256(bytes.fromhex(core["sensor_pub"])).digest()
        inc, t, dev = self.registry.verify_capture(
            batch_root, record_hash(rec), proof, bytes.fromhex(core["lot_root"]), key_hash,
            [bytes.fromhex(p) for p in rec["lot_proof"]])
        if not inc:
            return False, "not notarized"
        if not dev:
            return False, "sensor not valid at seal time"
        if core["anchor_block"] > t:
            return False, "anchor after seal"
        return True, "ok"

    def decode(self, rgb_u8):
        """In-pixel payload and block-grid offset. Tries the aligned grid first,
        then the resynchronisation search of Alg. 2."""
        y = pr.rgb_to_y(np.asarray(rgb_u8, dtype=np.float64))
        nbh, nbw = y.shape[0] // 8, y.shape[1] // 8
        bit_of, chip_of = pr.keyed_plan(self.key, 384, self.R_for(nbh * nbw), nbh * nbw)
        plan = (bit_of, chip_of, nbh, nbw)
        bits, _ = pr.extract_y(y, plan, 384)
        payload, ok = pr.rs_decode_bits(bits)
        if ok and payload.hex() in self.index:
            return payload, (0, 0)
        bits, _, off = pr.extract_resync(y, plan, 384, max_off=self.max_off)
        payload, ok = pr.rs_decode_bits(bits)
        return (payload if ok else None), off

    def verify(self, file_bytes, rgb_u8):
        payload, off = self.decode(rgb_u8)
        if payload is None or payload.hex() not in self.index:
            return "Unverified", "no payload"
        rec, batch_root, proof = self.index[payload.hex()]
        good, why = self.ledger_ok(rec, batch_root, proof)
        if not good:
            return "Unverified", why
        if file_bytes is not None and hashlib.sha256(file_bytes).hexdigest() in (rec["core"]["h_enc"], rec["core"]["h_raw"]):
            return "Camera-original", "exact"
        aligned = np.roll(np.roll(np.asarray(rgb_u8), -off[0], axis=0), -off[1], axis=1)
        d = fp_distance(fp_from_hex(rec["core"]["fp"]), fingerprint(aligned), lost_tiles(off))
        if d <= self.tau:
            return "Transcoded-consistent", f"fp {d:.3f}"
        return "Unverified", f"content mismatch {d:.3f}"
