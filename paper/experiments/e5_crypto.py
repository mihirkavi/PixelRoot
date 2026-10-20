"""
E5 -- Cryptographic micro-benchmarks, Merkle batching, RS false-accept bound.
Validates C7 (Prop. 3), C10 (timing), C11 (notarization O(1) amortization).

Outputs: results/e5_crypto.txt
"""
import os, time, hashlib, json
from math import comb
import numpy as np

import ledger
import pixelroot as pr

OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)

def bench_sha256():
    res = {}
    for label, nbytes in [("5.9 MB frame", 5_900_000),
                          ("6 MP RGB (2832x2122x3=18MB)", 2832 * 2122 * 3),
                          ("1080p RGB (6.2MB)", 1920 * 1080 * 3)]:
        data = np.random.RandomState(0).randint(0, 256, nbytes, dtype=np.uint8).tobytes()
        # warm up
        hashlib.sha256(data).digest()
        t0 = time.perf_counter()
        REP = 20
        for _ in range(REP):
            hashlib.sha256(data).digest()
        dt = (time.perf_counter() - t0) / REP * 1000
        res[label] = dt
    return res

def bench_seed_select():
    """Carrier-layout generation as deployed in pixelroot.keyed_plan (key-only
    seed, permutation of all blocks, antipodal chips) for 384 RS-coded bits over
    a 1080p frame (32,400 blocks, R = 84)."""
    n_blocks = (1920 // 8) * (1080 // 8)
    R = n_blocks // 384
    REP = 200
    t0 = time.perf_counter()
    for _ in range(REP):
        pr.keyed_plan("PIXELROOT-OEM-KEY-v2", 384, R, n_blocks)
    dt = (time.perf_counter() - t0) / REP * 1000
    return dt, n_blocks

def bench_merkle():
    rows = []
    for N in [1, 100, 10_000]:
        leaves = [hashlib.sha256(f"img{i}".encode()).digest() for i in range(N)]
        t0 = time.perf_counter()
        root = ledger.merkle_root(leaves)
        dt = (time.perf_counter() - t0) * 1000
        path_len = len(ledger.merkle_proof(leaves, 0))
        assert ledger.verify(root, leaves[0], ledger.merkle_proof(leaves, 0))
        proof_bytes = 32 * path_len
        rows.append((N, dt, path_len, proof_bytes))
    return rows

def rs_false_accept_bound(n_s=48, k=16, p=0.5):
    """Prob a random read-back decodes to a SPECIFIC claimed RS codeword by chance.
    RS(n_s,k) corrects t=(n_s-k)/2 symbol errors; a symbol (byte) matches by chance
    with q=(1-p)^8 wrong... here per-bit p=1/2 -> per-byte match prob = 2^-8.
    Accept iff received word within t symbols of the claimed codeword, i.e. >= n_s-t
    symbols match: tail of Binomial(n_s, 2^-8)."""
    t = (n_s - k) // 2
    qbyte = (1 - p) ** 8  # = 2^-8 for p=0.5
    # P[match >= n_s - t]
    prob = 0.0
    need = n_s - t
    for j in range(need, n_s + 1):
        prob += comb(n_s, j) * (qbyte ** j) * ((1 - qbyte) ** (n_s - j))
    return t, prob

GAS_REPORT = os.path.join(OUT, "gas_report.json")


def measured_gas():
    """Gas measured by the Hardhat test suite (contracts/test/registry.test.js)
    on PixelRootRegistry v2; None if `npm test` has not been run."""
    if not os.path.exists(GAS_REPORT):
        return None
    with open(GAS_REPORT) as f:
        return json.load(f)


def main():
    sha = bench_sha256()
    seed_dt, nblk = bench_seed_select()
    merkle = bench_merkle()
    t, fa = rs_false_accept_bound()
    L = []
    L.append("=== E5: crypto micro-benchmarks, Merkle batching, RS false-accept bound ===")
    L.append(f"Platform: Python {os.sys.version.split()[0]} hashlib (OpenSSL SHA-NI if available)")
    L.append("")
    L.append("[C10] SHA-256 commitment timing (mean of 20 runs):")
    for k, v in sha.items():
        L.append(f"   {k:<34} {v:.2f} ms")
    L.append(f"   carrier layout (384 coded bits x R=84, {nblk} blocks, keyed_plan): {seed_dt:.3f} ms")
    L.append("")
    L.append("[C11] Merkle batching (domain-separated sorted-pair SHA-256; ledger.py == PixelRootRegistry.sol):")
    L.append(f"   {'N leaves':<12}{'build (ms)':<14}{'path len':<12}{'proof bytes'}")
    for N, dt, pl, pb in merkle:
        L.append(f"   {N:<12}{dt:<14.3f}{pl:<12}{pb}")
    gas = measured_gas()
    if gas is None:
        L.append("   On-chain gas: run `npm test` in contracts/ to measure (writes results/gas_report.json)")
    else:
        L.append(f"   On-chain gas (measured, Hardhat EVM, {gas['evm']}):")
        for b in [1, 100, 10000]:
            per_tx = gas["register"]
            L.append(f"     batch={b:<6} per-tx={per_tx} gas   amortized/image={per_tx / b:.2f} gas")
        L.append(f"     registerLot={gas['registerLot']}  revokeDevice={gas['revokeDevice']}"
                 f"  verifyCapture (eth_call)={gas['verifyCapture']}")
    L.append("   (verification paths are view calls: no on-chain gas is paid to verify)")
    L.append("")
    L.append("[C7] RS(48,16) soft false-accept bound (Prop. 3), per-bit p=1/2:")
    L.append(f"   corrects t={t} byte errors; P[random read decodes to a claimed payload]")
    L.append(f"   = {fa:.3e}   (empirical E2: 0/1200 wrong-key, 0/24 forgery)")
    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(OUT, "e5_crypto.txt"), "w") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
