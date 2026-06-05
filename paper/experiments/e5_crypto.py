"""
E5 -- Cryptographic micro-benchmarks, Merkle batching, RS false-accept bound.
Validates C7 (Prop. 3), C10 (timing), C11 (notarization O(1) amortization).

Outputs: results/e5_crypto.txt
"""
import os, time, hashlib, math
from math import comb
import numpy as np

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
    """Seed derivation + keyed carrier-selection time (128 bits x R=25 over 32400
    blocks for a 1080p frame), pure-Python reference."""
    key = b"PIXELROOT-OEM-KEY-v2"
    payload = np.random.RandomState(1).randint(0, 256, 16, dtype=np.uint8).tobytes()
    n_blocks = (1920 // 8) * (1080 // 8)
    REP = 200
    t0 = time.perf_counter()
    for _ in range(REP):
        seed = int.from_bytes(hashlib.sha256(key + payload).digest()[:4], "big")
        rng = np.random.RandomState(seed)
        sel = rng.permutation(n_blocks)[:3200]
        chips = rng.choice(np.array([-1, 1]), size=3200)
    dt = (time.perf_counter() - t0) / REP * 1000
    return dt, n_blocks

def merkle_root(leaves):
    """Binary Merkle with sorted-pair SHA-256 (matches registry.sol verifyInclusion)."""
    level = list(leaves)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else level[i]
            lo, hi = (a, b) if a <= b else (b, a)
            nxt.append(hashlib.sha256(lo + hi).digest())
        level = nxt
    return level[0]

def bench_merkle():
    rows = []
    for N in [1, 100, 10_000]:
        leaves = [hashlib.sha256(f"img{i}".encode()).digest() for i in range(N)]
        t0 = time.perf_counter()
        root = merkle_root(leaves)
        dt = (time.perf_counter() - t0) * 1000
        path_len = max(0, math.ceil(math.log2(N))) if N > 1 else 0
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

def gas_estimate(batch):
    """Analytic EVM gas for the register() path (1 zero->nonzero SSTORE + event +
    base tx + calldata), amortized over a Merkle batch. verifyInclusion is a view
    call (0 on-chain gas)."""
    base_tx = 21000
    sstore_zero_to_nonzero = 20000
    log_event = 375 + 3 * 375 + 256  # LOG + topics + data (approx)
    calldata = 4 * 16 + 68 * 32      # selector + ~2 words nonzero calldata (approx)
    per_tx = base_tx + sstore_zero_to_nonzero + log_event + calldata
    return per_tx, per_tx / batch

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
    L.append(f"   seed derivation + carrier selection (128b x R=25, {nblk} blocks): {seed_dt:.3f} ms")
    L.append("")
    L.append("[C11] Merkle batching (sorted-pair SHA-256, matches registry.sol):")
    L.append(f"   {'N leaves':<12}{'build (ms)':<14}{'path len':<12}{'proof bytes'}")
    for N, dt, pl, pb in merkle:
        L.append(f"   {N:<12}{dt:<14.3f}{pl:<12}{pb}")
    L.append("   On-chain gas (analytic EVM):")
    for b in [1, 100, 10000]:
        per_tx, per_img = gas_estimate(b)
        L.append(f"     batch={b:<6} per-tx={per_tx} gas   amortized/image={per_img:.2f} gas")
    L.append("   (verifyInclusion is a view call: 0 on-chain gas; proof verified off-chain)")
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
