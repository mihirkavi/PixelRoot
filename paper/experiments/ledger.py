"""
PixelRoot ledger primitives, mirrored exactly by contracts/src/PixelRootRegistry.sol.

Merkle construction (domain-separated SHA-256, sorted pairs, odd node promoted):
    leaf = SHA-256(0x00 || item)
    node = SHA-256(0x01 || min(a,b) || max(a,b))

`Registry` is an in-memory model of the contract's state machine (manufacturers,
production lots of sensor keys, device revocation, sealed capture batches). It
lets the Python experiments exercise the full verification path; the Solidity
contract itself is tested in contracts/test/.
"""
import hashlib


def sha256(b):
    return hashlib.sha256(b).digest()


def leaf_hash(item):
    return sha256(b"\x00" + item)


def node_hash(a, b):
    lo, hi = (a, b) if a <= b else (b, a)
    return sha256(b"\x01" + lo + hi)


def _levels(items):
    level = [leaf_hash(x) for x in items]
    levels = [level]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(node_hash(level[i], level[i + 1]) if i + 1 < len(level) else level[i])
        level = nxt
        levels.append(level)
    return levels


def merkle_root(items):
    assert items, "empty tree"
    return _levels(items)[-1][0]


def merkle_proof(items, index):
    proof = []
    for level in _levels(items)[:-1]:
        sib = index ^ 1
        if sib < len(level):
            proof.append(level[sib])
        index //= 2
    return proof


def verify(root, item, proof):
    node = leaf_hash(item)
    for sib in proof:
        node = node_hash(node, sib)
    return node == root


class Registry:
    """State-machine model of PixelRootRegistry; `now` is the block time."""

    def __init__(self):
        self.now = 1
        self.manufacturer_since, self.manufacturer_revoked = {}, {}
        self.lots, self.device_revoked, self.sealed = {}, {}, {}

    def tick(self, dt=12):
        self.now += dt

    def add_manufacturer(self, m):
        assert m not in self.manufacturer_since
        self.manufacturer_since[m] = self.now

    def revoke_manufacturer(self, m):
        assert m in self.manufacturer_since and m not in self.manufacturer_revoked
        self.manufacturer_revoked[m] = self.now

    def register_lot(self, m, lot_root):
        assert m in self.manufacturer_since and m not in self.manufacturer_revoked
        assert lot_root not in self.lots
        self.lots[lot_root] = (m, self.now)

    def revoke_device(self, m, lot_root, key_hash, proof):
        assert self.lots[lot_root][0] == m and verify(lot_root, key_hash, proof)
        self.device_revoked.setdefault((lot_root, key_hash), self.now)

    def register(self, root):
        assert root not in self.sealed
        self.sealed[root] = self.now

    def device_valid_at(self, lot_root, key_hash, proof, t):
        if lot_root not in self.lots:
            return False
        m, lot_t = self.lots[lot_root]
        if lot_t > t:
            return False
        if m in self.manufacturer_revoked and self.manufacturer_revoked[m] <= t:
            return False
        rev = self.device_revoked.get((lot_root, key_hash))
        if rev is not None and rev <= t:
            return False
        return verify(lot_root, key_hash, proof)

    def verify_capture(self, root, record_hash, proof, lot_root, key_hash, dev_proof):
        t = self.sealed.get(root)
        if t is None:
            return False, None, False
        return verify(root, record_hash, proof), t, self.device_valid_at(lot_root, key_hash, dev_proof, t)
