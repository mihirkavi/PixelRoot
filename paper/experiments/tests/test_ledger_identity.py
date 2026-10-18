"""Unit tests for ledger.py (Merkle + registry model) and device_identity.py.
Run from paper/experiments:  python3 -m pytest -q tests"""
import hashlib
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import device_identity as di  # noqa: E402
import ledger  # noqa: E402
import pixelroot as pr  # noqa: E402

H = lambda s: hashlib.sha256(s.encode()).digest()


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 13, 33])
def test_every_proof_verifies(n):
    items = [H(f"x{i}") for i in range(n)]
    root = ledger.merkle_root(items)
    for i in range(n):
        assert ledger.verify(root, items[i], ledger.merkle_proof(items, i))


def test_wrong_item_or_proof_fails():
    items = [H(f"x{i}") for i in range(6)]
    root = ledger.merkle_root(items)
    assert not ledger.verify(root, H("other"), ledger.merkle_proof(items, 0))
    assert not ledger.verify(root, items[0], ledger.merkle_proof(items, 1))


def test_internal_node_is_not_a_leaf():
    items = [H(f"x{i}") for i in range(4)]
    root = ledger.merkle_root(items)
    internal = ledger.node_hash(ledger.leaf_hash(items[0]), ledger.leaf_hash(items[1]))
    sibling = ledger.node_hash(ledger.leaf_hash(items[2]), ledger.leaf_hash(items[3]))
    assert not ledger.verify(root, internal, [sibling])


def test_no_duplicate_last_node_mutation():
    a, b, c = H("a"), H("b"), H("c")
    assert ledger.merkle_root([a, b, c]) != ledger.merkle_root([a, b, c, c])


def test_vectors_file_matches():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "contracts", "test", "vectors.json")
    with open(path) as f:
        vec = json.load(f)
    for v in vec.values():
        items = [bytes.fromhex(x[2:]) for x in v["items"]]
        assert "0x" + ledger.merkle_root(items).hex() == v["root"]


def test_registry_revocation_is_time_scoped():
    reg = ledger.Registry()
    oem = di.Manufacturer("OEM", reg)
    chips, keys = oem.produce_lot(3)
    reg.tick()
    c = chips[1]
    t_before = reg.now
    reg.tick()
    oem.revoke(c)
    t_rev = reg.now
    assert reg.device_valid_at(c.lot_root, c.key_hash, c.lot_proof, t_before)
    assert not reg.device_valid_at(c.lot_root, c.key_hash, c.lot_proof, t_rev)
    assert reg.device_valid_at(chips[0].lot_root, chips[0].key_hash, chips[0].lot_proof, t_rev)


def test_lot_after_capture_does_not_validate():
    reg = ledger.Registry()
    oem = di.Manufacturer("OEM", reg)
    t0 = reg.now
    reg.tick()
    chips, _ = oem.produce_lot(2)
    assert not reg.device_valid_at(chips[0].lot_root, chips[0].key_hash, chips[0].lot_proof, t0)


def _scene(seed=0, h=256, w=256):
    rng = np.random.RandomState(seed)
    base = rng.uniform(0, 255, (h // 32, w // 32, 3))
    img = np.kron(base, np.ones((32, 32, 1)))
    return np.clip(img + rng.normal(0, 6, img.shape), 0, 255)


def test_fingerprint_roundtrip_and_separation():
    a = _scene(0).astype(np.uint8)
    b = _scene(1).astype(np.uint8)
    fa = di.fingerprint(a)
    back = di.fp_from_hex(di.fp_to_hex(fa))
    assert di.fp_distance(fa, back) < 0.01
    assert di.fp_distance(fa, di.fingerprint(pr.att_jpeg(a, 50))) < 0.1
    assert di.fp_distance(fa, di.fingerprint(b)) > 0.5


def test_record_signature_detects_tampering():
    reg = ledger.Registry()
    oem = di.Manufacturer("OEM", reg)
    chips, _ = oem.produce_lot(1)
    img = _scene(2).astype(np.uint8)
    rec = di.make_record(chips[0], b"\x01" * 16, img, di.jpeg_bytes(img), (reg.now, b"\0" * 32))
    assert di.check_signature(rec)
    rec["core"]["payload"] = "02" * 16
    assert not di.check_signature(rec)


def test_lost_tiles_follow_crop_direction():
    assert di.lost_tiles((0, 0)) == set()
    top_left = di.lost_tiles((-5, -5))
    assert 0 in top_left and di.FP_GRID * di.FP_GRID - 1 not in top_left
    assert len(top_left) == 2 * di.FP_GRID - 1
