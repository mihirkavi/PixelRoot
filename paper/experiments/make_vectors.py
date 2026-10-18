"""Emit Merkle test vectors from ledger.py for the Solidity tests (contracts/test)."""
import json, os, ledger

out = {}
for n in [1, 2, 3, 7, 16]:
    items = [ledger.sha256(f"item-{n}-{i}".encode()) for i in range(n)]
    root = ledger.merkle_root(items)
    out[str(n)] = {
        "root": "0x" + root.hex(),
        "items": ["0x" + x.hex() for x in items],
        "proofs": [["0x" + p.hex() for p in ledger.merkle_proof(items, i)] for i in range(n)],
    }
    assert all(ledger.verify(root, items[i], ledger.merkle_proof(items, i)) for i in range(n))
path = os.path.join(os.path.dirname(__file__), "..", "contracts", "test", "vectors.json")
with open(path, "w") as f:
    json.dump(out, f, indent=1)
print("wrote", os.path.normpath(path))
