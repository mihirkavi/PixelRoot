# Independent pre-submission review of PixelRoot (and how it was addressed)

> This review was produced by an independent reviewer pass on the manuscript **before** the
> fixes in commit history after it. Every critical and major item was addressed:
> C1/C2 (fingerprint tile skipping, adaptive band projection): fingerprint v2 over the frame
> interior with no skipping; the adaptive attack is now evaluated in E6 and a transcoded
> verdict is defined as derivation, with pixel-exact certification reserved for V1.
> M1 lots keyed by (manufacturer, root); M2 sealing block number + anchor-hash check;
> M3 crop/resize claims narrowed; M4 multi-record store; M5 privacy claims fixed;
> M6 compromise window stated, capture counter added; M7 propositions restated; M8 Wilson CIs,
> PRNU wording; M9 micro-benchmark rebuilt from E5/E6; M10 length left to the author
> (cuts listed in submission/README_SUBMISSION.md); M11 code URL added.

---

# Independent pre-submission review: "PixelRoot: Hardware-Anchored, Sensor-Level Media Provenance with Real-Time Blockchain Notarization for Trustworthy Imaging"

Target venue: IEEE Transactions on Information Forensics and Security (TIFS)
Materials reviewed: `paper/pixelroot.tex` (1942 lines), `references.bib`, `pixelroot.pdf` (21 pp.), `experiments/*.py`, `experiments/results/*`, `experiments/tests/`, `contracts/src/PixelRootRegistry.sol`, `contracts/test/registry.test.js`, `submission/*`.
Line numbers refer to `pixelroot.tex` at commit 5e22603. Table and figure numbers follow the compiled PDF: Table I (compare), II (threats), III (micro), IV (robust), V (sweep), VI (loc), VII (E6 verdicts), VIII (E6 attacks); Fig. 1 (architecture) to Fig. 7 (results).
The blockchain is treated as a fixed design constraint. Every recommendation below keeps it.

Reviewer probes: I ran two adaptive attacks against the released verifier (`device_identity.Verifier`), using the same Kodak data, key, A=4, RS(48,16) and tau=0.286 as E6. Scripts: `/tmp/claude-0/-home-user-PixelRoot/196253f6-4466-5d6a-9bd5-002671515e04/scratchpad/probe/attacks.py` and `attacks2.py`. Visual example: `/tmp/claude-0/-home-user-PixelRoot/196253f6-4466-5d6a-9bd5-002671515e04/scratchpad/probe/out/attack2_example.png`. Nothing in the repository was modified.

---

## 1. Summary

The paper proposes a capture-time provenance system with four parts:
- a keyed, spread-spectrum, low-frequency (DCT (0,2)) in-pixel payload (128 bits, RS(48,16)), meant to be written by per-region or per-column sensor gain;
- a sensor-held ECDSA key certified on-chain by production-lot Merkle roots, with time-scoped revocation;
- a signed capture record binding the payload to file hashes, a 4x4-tile low-frequency content fingerprint, and an anchor block;
- Merkle-batched notarization in a permissionless registry contract.

The evaluation simulates the channel in software on the 24 Kodak images with real codecs (E1, E2), a per-pixel localization layer (E3), a PRNU baseline (E4), crypto and gas micro-benchmarks (E5), and an end-to-end device-identity study on 12 held-out images (E6).

The paper is far stronger than a typical "blockchain + watermark" submission. It admits that the in-pixel mark is copyable without the key, and it puts authenticity in a signed, content-bound record. The contract is small, tested, and uses domain-separated Merkle trees. The calibration and held-out split in E6 is good practice.

However, the central security claim (Prop. 4, "identity non-transferability", and the "0/240 forgeries" headline) rests on a content fingerprint and a tile-skipping rule that an adaptive attacker defeats easily. I demonstrate two practical acceptances of semantically altered images. There are also several design and implementation gaps on the ledger side:
- lot hijacking by front-running;
- block-number vs timestamp confusion in the capture-time bracket;
- results that are stale relative to the code;
- payload collisions in the record-store lookup.

Further problems:
- The evaluation is small: 24 images of 0.4 MP scanned film.
- A micro-benchmark table is stale.
- The paper is about twice the TIFS length norm.

## 2. Verdict

**Major revision before submission.** In its current form a TIFS security reviewer would likely recommend reject or major revision. The deciding issues are C1 and C2 below (the content binding is not secure against the obvious adaptive attacks), plus M1 to M4. All are fixable within the current architecture. The blockchain and device-identity layers can stay and are the paper's best parts. The fix list in section 9 is ordered so that the critical items come first.

---

## 3. Number audit

Legend: OK = matches the results file or code; MISMATCH = the paper's value differs; STALE = the value comes from an older design or run; UNVERIFIABLE = no results file or code output supports it.

| # | Location (line) | Paper says | Measured / computed | Source | Status |
|---|---|---|---|---|---|
| 1 | Abstract L121, L1329-1330, Fig. 7 caption | 22-23/24 decode to JPEG Q20; 21/24 at Q10 | Q95..Q20 = 23 (Q30 = 22); Q10 = 21 | e1_robustness.txt | OK |
| 2 | Abstract L122 | 38 dB PSNR | 38.20 dB | e1 | OK |
| 3 | Abstract L122, cover letter | 0/1224 false accepts | 0/1200 wrong-key + 0/24 unmarked (two different tests pooled) | e2_security.txt | OK, but say it is two tests |
| 4 | Abstract L124; L942, L1228, L1682 | 78% keyless copy success | 61/78 = 78.2% | e6 (3) | OK |
| 5 | Abstract L124-125; L1892 | 0 of 240 forgeries | 78+78+60+24 = 240, 0 accepted | e6 (3), (4a), (4b) | OK. Trials are highly correlated (12 base images); see M8 |
| 6 | Abstract L126; L1696, L1849 | 46.6k / 46,605 gas per batch | 46605 | gas_report.json | OK |
| 7 | L756, L1596-1599, Table VI | AUC 0.974 / 0.954; F1 0.74 / 0.56; IoU 0.59 / 0.39; TPR/FPR 0.914/0.037 and 0.927/0.104 | identical | e3_localization.txt | OK |
| 8 | L772-773 | 24 bits per coordinate is about 1e-4 degree resolution | 360/2^24 = 2.1e-5 deg (lon), 1.1e-5 deg (lat) | arithmetic | MISMATCH (about 5x too coarse) |
| 9 | L837 | gain ramp is a "~1-2%" modulation | A * max abs(Phi_{0,2}) = 4 * 0.924 = 3.7 GL, about 3% at mid-gray and more in dark areas | code `P8` | MISMATCH (imprecise) |
| 10 | L844-845, L1493-1495 | 38.2 dB at A=4; 41.2 dB at A=3; SSIM 0.942 | 38.20 / 41.21 / 0.9420 | e1 | OK |
| 11 | L869 | raw BER near 2% through aggressive JPEG | Q10 0.0218 (Q5 0.22) | e1 | OK |
| 12 | L978-979 | 63 coeffs/tile, 1,072 bytes | 16x63 int8 + 16x4 B scales = 1072 | device_identity.py | OK |
| 13 | L988, L1695 | record about 3 KB | 2986 B | e6 (6) | OK |
| 14 | L1032, L1436, L1655 | 16-case Hardhat suite | 16 `it(...)` | registry.test.js | OK |
| 15 | L1438 | 18 Python unit tests | 9 parametrized + 9 = 18 | tests/test_ledger_identity.py | OK |
| 16 | L1140-1141 | N_B=6144, n_c=384, R=16, m=N_B, 2^-6144 < 1e-1849 | R = 6144//384 = 16; log10 2^-6144 = -1849.5 | e1/e6 code | Numbers OK; the formula is wrong (see M9) |
| 17 | L1142-1143, L1515-1517, Table IV | wrong-key BER 0.4996, 0/1200 | 0.4996, 0/1200 | e2 | OK |
| 18 | L1166, L1521 | false-decode bound <= 1.8e-65 | 1.833e-65 | e5_crypto.txt | OK |
| 19 | L1230, L1684 | 0/156 copy forgeries accepted | 0 + 0 of 78 + 78 | e6 (3) | OK |
| 20 | L1232, Table VIII | 0/60 transplant | 5 x 0/12 | e6 (4a) | OK |
| 21 | L1261, L1387, L1689 | 24/24 splices of 6-12% area rejected; 21/24 still decode | 25%/35% side = 6.25%/12.25% area; 21/24; 0 accepted | e6 (4b) | OK |
| 22 | L1341-1343 | resize BER 0.016 to 0.026 (0.75x), 0.042 (0.5x); 22/24, 16/24; JPEG70+0.75x 22/24 | 0.0259 / 0.0419; 22, 16; 22 | e1 | OK |
| 23 | L1350 | 15 x 57 + 7 = 862 decodes for +/-28 px | range(-28,29,4) = 15; 57; refine 7 | pixelroot.extract_resync with max_off=28 | OK |
| 24 | L1351-1352 | older stride-4 search decoded only 20/24 at BER 0.11 on 2% crops | not in any results file | none | UNVERIFIABLE / STALE (revision history; delete) |
| 25 | L1353-1354 | 1/2/3% crops: 23/24 each, BER <= 0.020, shifts up to 23 px | 23/24; 0.0171-0.0195; 0.03 x 768 = 23 | e1 | OK, but only crop+pad to the same size (M3) |
| 26 | L1446 | seed derivation + full carrier generation take "tens of microseconds" | 0.482 ms (and e5 times the stale payload-dependent seed SHA(k‖m), 128 bits x R=25) | e5_crypto.txt, e5_crypto.py `bench_seed_select` | MISMATCH + STALE |
| 27 | L1447, Table III | SHA-256 over 1080p frame takes 3.09 ms (Node.js) | Python e5: 4.12 ms; no Node output in repo | e5; sim.js prints no timings | UNVERIFIABLE |
| 28 | L1448 | 6 MP RGB frame takes about 8.5 ms in the Python harness (e5_crypto.py) | 13.23 ms | e5_crypto.txt | MISMATCH |
| 29 | Table III (all rows) | 128 b / 128 positions; seed 0.0024 ms; full signature 0.018 ms; determinism, tamper rows | no results file contains these; "128 positions" is the retired single-pixel v1 design | sim.js, results.txt | STALE / UNVERIFIABLE (delete the table) |
| 30 | L1498-1499 | mean raw BER about 1.6%, up to 13% | 0.0161, max 0.1328 | e1 | OK |
| 31 | L1503-1504 | "21-22/24 under WebP, resize 0.75-1.5x, photometric edits, and combined JPEG+resize" | photometric 21-23 (B0.9, C0.9, G0.9 = 23) | e1 | MISMATCH (minor) |
| 32 | Table IV WebP row | BER 0.022 | 0.0214 / 0.0240 | e1 | MISMATCH (minor); write 0.021-0.024 |
| 33 | Table IV noise / blur / photometric / crop rows | 0.017 / 0.018 / 0.017 / 0.019 | 0.0161-0.0183 / 0.0177 / 0.0157-0.0181 / 0.0171-0.0195 | e1 | OK (state "mean" or give ranges) |
| 34 | Table V, A=0.5 | PSNR "inf / 58+" | e1: inf (the mark is rounded away entirely); "58" is the old synthetic sim (results.txt 58.2 dB) | e1_curve.csv, results.txt | STALE; write "inf (mark quantized away)" |
| 35 | Table V other rows | 51.2 / 48.2 / 44.2 / 41.2 / 38.2 / 35.2; BER and decode counts | identical | e1 | OK |
| 36 | L1517-1519, Table IV | unmarked BER 0.494, 0/24 | 0.4937, 0/24 | e2 | OK |
| 37 | L1523, Table IV | copy attack: 15/17 decode source payload | 15/17 | e2 | OK |
| 38 | L1641-1642 | NCC margin +0.019 (clean) to +0.004 (Q50); PCE drops about 18% | 0.0855-0.0669 = 0.0186; 0.0737-0.0694 = 0.0043; 260.7 to 212.9 = -18.3% | e4_prnu.txt | OK numerically; the conclusion is not supported (M8) |
| 39 | L1664-1667 | tau = 0.286; held-out genuine max 0.082; different images min 0.866, median 1.24; more than 3x margin each side | 0.286 (midpoint of 0.092 / 0.481); 0.082; 0.866; 1.240; 3.49x / 3.03x | e6 (1) | OK. Held-out splice distances are not reported |
| 40 | L1670, Table VII | Camera-original 12/12 | 12/12 | e6 (2) | OK (V1 on the very file that was committed is tautological) |
| 41 | L1672-1674 | 11/12 for JPEG to Q20, noise, blur, resize, photometric, crops, combos; 9-10/12 for Q10, WebP q60, 0.5x | Brightness 1.1 = 10/12; others as stated | e6 (2) | MISMATCH (minor: "photometric" should be 10-11/12, as Table VII already says) |
| 42 | L1675-1676 | every genuine Unverified is a payload-decode failure, never the fingerprint | the results file does not log reasons | e6_device_identity.py prints counts only | UNVERIFIABLE; print the reason breakdown |
| 43 | L1680-1684, Table VIII | keyless copy from Q75 with gain 1.5: 61/78; with original 70/78 | as in code and results | e6 | OK |
| 44 | L1688 | alpha = 1 forgery has PSNR 12.2 dB to B | 12.2 | e6 (4a) | OK |
| 45 | L1691, Table VIII | every record and ledger attack handled (9 checks) | the committed code now has a 10th check ("anchor hash not the chain's") and a verifier anchor-hash test, but the committed results file was produced before it and lacks that row | git show HEAD; e6 code vs results | STALE; re-run E6 and add the row |
| 46 | L1693-1699 | 3.7 ms sign, 0.12 ms ECDSA verify, 4.1 ms full verify; 51,355 / 65,419 gas; 4.66 gas/image at N = 1e4 | 3.7 / 0.118 / 4.1; 51355 / 65419; 4.66 | e6 (6), gas_report.json, e5 | OK |
| 47 | L1027, e5 | proof length ceil(log2 N) | 14 for 1e4 | e5 | OK |
| 48 | L1416 | O(1) ledger lookup at upload | needs a record-store lookup plus O(log N) Merkle and lot proofs | design | Overclaim |
| 49 | L513-514, L737 | future work "(E4)", "(E5)" | E4 / E5 are also the names of the PRNU and crypto experiments; Sec. "(E6)" is both an experiment and a future-work item (L1647 vs L1781) | — | Label collision |
| 50 | L148-153, L162 | fraud losses of $1.2-1.3B, $280k; 45-50% AUC drop | vendor and grey literature | bib | Not checkable here; soften or attribute ("vendor reports estimate...") |

Other code/results consistency notes:
- `ALL_RESULTS.txt` is consistent with the individual files.
- `results.txt` at the experiments root is the old synthetic-sim output, which shows 0.0000 BER everywhere. Remove it from the supplement so reviewers do not mistake it for the current results.

---

## 4. Internal consistency issues

### 4.1 Notation collisions (fix with a symbol table)

| Symbol | Meanings |
|---|---|
| sigma | bit sign `sigma = 2b-1` (L832, Eq. embed), ECDSA signature (L878, L911, Eq. record), Gaussian noise/blur std (L1502, Tables IV and VII) |
| lambda | longitude (Eq. payload, L766, L772), lot Merkle root (L892, L959, L1051, L1823); Alg. 1 patches this with `lambda_geo` (L897) but Eq. L766 does not |
| t | timestamp in m (L765), RS correction capability (L1157), tile index in Eq. fpdist (L982), and t_b (block time) |
| H | frame height (L798, Alg. 1/2), hash function `\mathcal H` |
| r | capture record (Eq. record) vs RS redundancy in `t = floor(r/2)` (L1157) |
| m | payload (bold m) vs number of carrier blocks `m = n_c R` (L1134) |
| n_s | number of RS symbols (Prop. 3, L1157) vs sealing block number (Prop. 5, L1200) |
| A, B | amplitude A vs images "A" and "B" in the copy attack (L1523, L1686) |
| delta | resync offset delta* vs localization amplitude delta = 4 (L1590) |
| phi / varphi | latitude phi vs fingerprint energy floor varphi (L985) |
| x, y in Phi_{u,v}(x,y) | x must be the row index for "(0,2) is constant down each column" (L1347) and "low horizontal frequency" (L830) to hold (the code uses `np.outer(cu, cv)` with rows = u). Standard DCT notation has x horizontal. State the convention |

### 4.2 Stale text from older designs

- **G4 (L505-510)** says the in-pixel binding needs a key-holding verifier and that public-key verification is future work. This contradicts L1009-1015 and L1797-1805, which say the OEM may publish k so that anyone can run V2. Rewrite G4.
- **L810-811**: "or the repetition coding evaluated in §eval". The evaluation uses RS plus spreading. Delete.
- **"Redesigned"** carrier/channel (L255, L1321, L1477), "naive designs" (L824), "earlier designs confused" (L840), "An earlier search..." (L1351-1352), "The earlier fragile/semi-fragile tension is thus resolved" (L1332-1333). These leak revision history that a reader of a new paper does not have. Delete.
- **L1424-1430**: "register/verify service with simulated notarization", "legacy v1 (120-bit) and v2 (128-bit) payload ... fixing a coordinate-packing precision bug". This is obsolete now that a contract and a Python identity layer exist. Delete.
- **Table III and L1441-1451**: Node.js micro-benchmark of the single-pixel v1 prototype ("128 positions"). Delete.
- **`e5_crypto.py::bench_seed_select`**: seeds with `SHA256(key + payload)`, i.e. the retired payload-dependent seed s = H(k‖m), and uses 128 bits x R=25 rather than 384 coded bits. Fix the script, then re-run.
- **Table V "58+"**: from the old synthetic sim.
- **Seed definition**: the paper (Eq. at L798, Fig. 6 caption, Alg. 1 L902, Alg. 2 L1078) uses SHA-256(k‖W‖H). The code uses `SHA256(key‖salt)` with an empty salt (no W, H), reduced to 32 bits. L804-806 discloses the 32-bit reduction but describes the seed as SHA-256(k), which contradicts the equation. Either implement W‖H or state the deviation exactly.
- **`submission/README_SUBMISSION.md`** still lists `registry.sol` (now `contracts/src/PixelRootRegistry.sol`) and "six embedded figures" (there are seven, including TikZ Fig. 1).
- **Searched for and found nothing (good):** "Exact-copy", "OEM secret", "analytic gas", "three propositions", "h = SHA(I‖m)". The old `registry.sol` (leaf = SHA256(I‖m), keccak) was correctly deleted.

### 4.3 Algorithms vs text vs code

- **Decoder.** Eq. (residual), Eq. (despread) and Alg. 2 line 5 describe a plain projection. The code (`pixelroot._project_field`) subtracts a 5x5 local mean of the projection field (host suppression) before de-spreading, and the method relies on it. L850-851 ("no estimate of the block's 'original' brightness is needed, because the AC basis is orthogonal to the DC term") is misleading: host content in the (0,2) coefficient is exactly what the high-pass removes. The keyless copy attack (E6) uses the same high-pass. Put it in Eq. (residual) and Alg. 2.
- **Resync order.** Alg. 2 always runs the resync search. `Verifier.decode` first tries the aligned grid and accepts if the payload is in the index, and only then searches. Minor; align them.
- **Tile skipping.** Alg. 2 line 7 (`d(F(r), F(I'_delta*)) <= tau`) and Prop. 4(ii) state a full-fingerprint test. The code skips every tile in the first or last tile row and column whenever the resync offset is non-zero (`lost_tiles`): 7 of 16 tiles, about 44% of the frame, for any 1-px shift. L1067 mentions "ignoring the tiles that a crop removed", but Prop. 4 does not. This is critical (C1).
- **V1 claim.** V1 text (L1055-1056) says a match "proves that this exact file came from a certified sensor". Prop. 1 assumes only collision resistance and A3, so it proves existence before t_b, not sensor origin. Either add EUF-CMA and A5 to Prop. 1 or point to Prop. 4.
- **Anchor validity.** L1052 calls a record valid if "its anchor precedes t_b". Prop. 5 additionally requires that hash_beta equals the canonical hash. The committed verifier now checks the hash (`ledger_ok`), but:
  - the reported E6 results predate that check (row 45 above);
  - the contract stores `block.timestamp` while the anchor holds a block number, so the comparison mixes units (M2);
  - L1052 and the step list omit the hash check.
- **Threat table (Table II).**
  - "Splice / inpaint: A4 -> P4", but P4 also needs A3 and A5.
  - "Launder / regenerate -> P2, P3": P2 (wrong-key read) is irrelevant to laundering.
  - "Rogue manufacturer -> P4": P4 says nothing about manufacturer revocation or lot timing.
  - "Sensor-key theft -> P4": P4 excludes holders of unrevoked keys; the revocation-window risk is not covered by any proposition.
- **Retroactive lots.** L1273-1274 says that "a hostile manufacturer cannot revoke another manufacturer's sensors (both enforced by the contract and tested)". This is false under front-running (M1). The test only covers the non-adversarial ordering.
- **Revocation enforcement.** L965-966 says revocation is "enforced by the contract's own verification call, not left to validator policy". `verifyCapture` is a view call that the verifier chooses to make; this is the same trust model as checking a CRL. Soften.
- **Hardware claims.** L612-614 says the per-column/per-region tier is "realizable on conventional sensors today", and the Fig. 2 caption says "realizable today". L593-597 correctly says per-column gain must be reprogrammed at line rate "which column front-ends must be shown to support". Make the claims agree.
- **"Photo-electron domain."** L928-929 and L1790-1791 call per-region conversion-gain switching modulation "in the photo-electron domain". Conversion gain acts at charge-to-voltage conversion. Only M2 (exposure gating) acts on photo-electrons.
- **Bits per pixel.** L661: "ample for 1-2 bits/pixel". The scheme carries 384 coded bits over about 393k pixels (about 0.001 bit/pixel). Delete or rephrase.
- **Fig. 5 caption (L718).** Quotes the 0.4 µm research pitch as if it were the production stack; L699 says production pitch is below 2 µm.
- **E3 key.** The localization pattern is "keyed to the payload" (L751-752). The code keys it only to the key and frame size (`fragile_pattern(shape, key)`), so it is identical for every image of a given size. A splice from another marked image of the same size at the same location carries a valid pattern, and the pattern can be estimated by averaging. Fix the text or the code.
- **Proposition numbering.** Five propositions, all `\label`ed and `\ref`ed correctly. L1833 hard-codes "Proposition~1"; use `\ref{prop:v1}`.
- **Real-time.** Table I gives PixelRoot a "Real-time ✓". Notarization latency is explicitly untested (L511-514, future item E4). Mark it "design" or footnote it.

---

## 5. Technical issues (ranked)

### CRITICAL

**C1. The tile-skipping rule lets an attacker splice into about 44% of the frame (`lost_tiles`, Alg. 2, Prop. 4).**
`Verifier.verify` re-aligns by the resync offset and drops every tile in the border row and column on the offset's side (`lost_tiles`). The offset is attacker-controlled: any translation of a few pixels makes it non-zero. The attacker can therefore put foreign content anywhere in the last tile row or column (or the first, by shifting the other way), shift by 8 px, and those tiles are never compared.

Probe (`attacks2.py`): a 128x128 foreign patch (about 4% of the frame, comparable to the paper's 6-12% splices) placed in the bottom-right tile, then JPEG Q90.
- Without a shift: 0/12 accepted.
- With an 8-px shift: **11/12 accepted as Transcoded-consistent** (the 12th failed payload decode).
- Whole-row or whole-column replacement plus shift: 3/12 accepted each.

E6 never combines a splice with a shift, so the "0/240" and "24/24 splices rejected" claims do not cover this. Prop. 4(ii) is false as implemented.

Fix (no architecture change):
- recompute the fingerprint on the overlap only, shifting the tile grid by the offset and dropping only the strip actually lost;
- cap the ignored area (e.g. at most the padded strip, under 5%);
- or put the original frame size and the crop box in the record and refuse V2 when the lost area exceeds a bound.
Then add "splice + shift" to E6.

**C2. The content fingerprint is a ~32x32 low-pass thumbnail; an adaptive attacker can match it exactly while changing the semantics.**
F keeps the 8x8 lowest DCT coefficients of each tile's 32x32 box-downsample. That is an effective resolution of about 8x8 cells per tile, i.e. 24x16-px cells on a 768x512 image (and about 125-px cells on a 12 MP image). DC is also excluded, so tile brightness is free.

The paper's "adaptive" attacker (L1685-1688) blends a 16x16 low-pass, which is coarser than the fingerprint itself, so it cannot match F. The natural adaptive attacker projects the edit onto the fingerprint's null space.

Probe (`attacks.py`): paste a 96x96 foreign patch at the image centre, apply one projection step per tile (nearest-upsampled 32x32 DCT-band correction, 3 iterations), then JPEG Q90.
- **11/12 accepted** (d = 0.006-0.014, against tau = 0.286). The 12th failed payload decode.
- Before projection, the naive patch was already accepted in 3/12 (d = 0.15-0.24 < tau).
- The visual example `out/attack2_example.png` shows an aircraft cockpit inserted into a beach scene, accepted as Transcoded-consistent. The crude nearest-neighbour projection leaves blocky artifacts; a smooth least-squares projection would hide them better.

Prop. 4's escape clause ("content within tau of a genuinely captured frame") is therefore reachable for meaningful semantic edits: object insertion or removal, faces, text, plates. The "Splice / inpaint" row of Table II and L1384-1388 understate this.

Required:
- (a) Evaluate this attacker and report acceptance against edit size.
- (b) Strengthen F within the architecture. Options: a higher-resolution and/or multi-scale fingerprint; including DC; a semi-fragile robust hash with a known security analysis; a learned perceptual hash with an adversarial evaluation; or binding F to the in-pixel per-pixel layer.
- (c) Rephrase Prop. 4 and the abstract to claim "consistency with a captured frame at resolution X", not "non-transferable identity".
- (d) Report the minimum detectable edit area as a curve (the paper currently tests only 6-12% splices, which are also the calibration class for tau).

### MAJOR

**M1. Lot hijacking by front-running `registerLot` (contract).**
`lots` is keyed only by `lotRoot`, and the first active manufacturer to submit a root owns it. A malicious but admitted manufacturer (the paper's "rogue manufacturer") that sees an honest `registerLot(root)` in the mempool can submit the same root first. It then:
- (i) owns the honest lot, so `revokeDevice` passes `lot.manufacturer == msg.sender` and it can revoke the honest sensors;
- (ii) makes the honest lot's validity depend on its own revocation status;
- (iii) blocks the honest registration ("lot exists").
This contradicts L1273-1274.

Fixes:
- key lots by `(manufacturer, lotRoot)` and put the manufacturer in the record;
- or put the manufacturer address inside the lot leaves (leaf = H(0x00 ‖ mfr ‖ keyHash));
- or use commit-reveal.
Also add a test with two manufacturers racing.

Smaller contract notes:
- The lot tree and the batch tree share the same leaf/node tags. Use distinct domain tags per tree.
- ECDSA malleability: (r, n-s) yields a different record hash. This is harmless, but say that V1/V2 use the exact sigma, or use low-s normalization.
- `register` is permissionless and write-once. Front-running a capture root only seals it earlier, so it is harmless, but say so.
- Governance is a single address with power to admit rogue manufacturers. It is a trust anchor, which weakens the "no single point of trust" argument (L1835-1847). State the governance threat model (multisig or timelock, admission delay).

**M2. The capture-time bracket (Prop. 5) is not implemented as stated.**
- Units. The anchor is a block number (`anchor_block`), while `sealedAt` is `block.timestamp`. In the Python model, `Registry.now` serves as both (`tick(dt=12)`). On a real chain, "anchor_block > t" compares about 2e7 with about 1.8e9 and never fires. Store `block.number` at sealing (or compare the anchor block's timestamp).
- Hash check. The anchor-hash check is off-chain only. EVM `blockhash` covers 256 blocks, so verifiers need an archive node or a light client. Say so.
- Stale results. The anchor-hash check was added to `Verifier.ledger_ok` and E6 in the last commit, but `results/e6_device_identity.txt` was not regenerated: it has no "anchor hash not the chain's" row, and its genuine records were built with the old anchor format. Re-run E6 and add the row to Table VIII.
- Prop. 5 also needs an assumption about anchor freshness. An offline device's anchor can be days old, which gives a weak lower bound. Discuss it.

**M3. Real crops and resizes change W and H and break V2; the evaluation uses size-preserving variants.**
- The deployed seed is SHA-256(k‖W‖H) and the code's permutation depends on `n_blocks`. Any operation that changes frame size (a true crop, a platform downscale, a 1080-px social-media resize) yields a different carrier layout.
- E1/E6 "Crop 1-3%" is a top-left crop **edge-padded back to the original size** (`att_crop_pad`), and "Resize" is a **round-trip back to the original size** (`att_resize`). Neither occurs on real platforms.
- Claims at L1353-1355, L1500-1504, L1672-1674 and the abstract/contribution "resize ... crop" robustness overstate the envelope.
Fix:
- make the layout independent of the questioned frame size (e.g. key the layout on a canonical grid, or put the original W, H in the payload or a sync template and search candidate sizes);
- or state plainly that V2 requires the original geometry, and test true crops and true downscales (expect Unverified).

**M4. Payload uniqueness and the record-store lookup.**
- m = ID‖t‖geo with a one-second t. Burst mode, video, and multi-camera phones produce several captures with identical m. `Verifier` keys the index by payload in a dict, so later records overwrite earlier ones, and Alg. 2 does `store.lookup(m)` returning one record.
- A holder of an extracted key (inside the adversary model, L494) can publish records carrying a victim's m and shadow the victim (griefing or denial of verification).
- The record store is also a new availability and censorship dependency: V1 needs the record too.
Fix:
- add a per-capture counter or nonce to m (or reduce t to make room);
- let lookup return all records for m and accept if any passes;
- specify the store's trust model: untrusted, append-only, content-addressed (e.g. IPFS or blob data with the root on-chain), and optionally emit a per-batch payload index on-chain.
This keeps the blockchain central.

**M5. Privacy claims are inconsistent.**
- L768-771 promise a rotating 48-bit pseudonymous ID "unlinkable to the physical device without OEM cooperation".
- But every published record carries the sensor's long-term pk, and V2 lets anyone holding a marked image (and k, which the paper proposes to publish) fetch that record. All published images of a device are therefore trivially linkable, which L1820-1821 concedes.
- Contribution 7 (L262-266) and L1807-1831 ("no raw PII ever touches the chain", ZK selective disclosure, GDPR) promise more than is designed. The ZK proof is unspecified, and a hash of personal data can still be personal data.
Either drop the rotating-ID claim, or make the record pseudonymous (DAA or group signatures, already cited as future work) and qualify the contribution.

**M6. Revocation semantics under key extraction.**
Revocation is time-scoped by sealing time and cannot be backdated. An adversary who extracts a key (in scope) can sign and seal an unbounded number of forged records (arbitrary m and F, hence deepfakes) before revocation, and those stay valid forever. "A residual risk, bounded per device" (L1268-1269) is misleading: it is bounded in devices, not in forgeries.
Options:
- a governance or manufacturer "compromised-since" field that invalidates captures sealed after a declared compromise time (with evidence and a delay);
- rate limits per key per batch;
- surfacing "key later revoked" to verifiers even for earlier captures.
State the trade-off with honest captures.

**M7. Prop. 2 is mis-specified and largely irrelevant; Prop. 3 assumptions.**
- With m = N_B (all blocks are carriers), the binomial is 1. The secret is the assignment of blocks to coded bits plus chips, roughly N_B!/(R!)^{n_c} x 2^m, not a subset.
- More importantly, the prototype seed is 32 bits, so the effective key space is 2^32 (brute-forceable). By the paper's own Remark (L1146-1151), reading or guessing the layout is not what security rests on.
- Recommendation: drop Prop. 2 (keep one sentence and the empirical wrong-key result), or restate it correctly as a statement about full-width keys only.
- Prop. 3 assumes independent bits with p = 1/2. Host content and the high-pass make bits correlated. Present it as a heuristic bound, or state the model explicitly.
- Prop. 3 bounds decoding to a given payload, but V2 accepts any payload present in the store. Use a union bound over the store size (still negligible, but say it).

**M8. Evaluation scale, statistics and baseline.**
- Data. 24 Kodak images: 1990s scanned film, 768x512 (0.4 MP), not sensor-captured. E6 uses 12 held-out images.
- Confidence intervals. Wilson 95% intervals: 23/24 -> [0.80, 0.99]; 11/12 -> [0.65, 0.99]; 9/12 -> [0.47, 0.91]; 0/240 -> upper 1.6% (but the trials are correlated, so the effective n is about 12). Report CIs.
- Scale. Evaluate on a few hundred to a few thousand modern camera images (e.g. RAISE, DIV2K, MIT-Adobe 5K, Dresden or VISION JPEGs) at native resolution. The fingerprint's semantic resolution degrades at 12+ MP (C2).
- tau calibration. tau is calibrated against the same splice class (25-35% side) that is later tested. Report held-out splice distances and a detection curve against splice size and position.
- Attack chain. Attacks are applied to the raw marked frame, not to the camera's delivered JPEG (`attacked` is built from `marked`), so double compression is untested.
- Reason breakdown for "Unverified" is not logged (row 42).
- PRNU baseline (E4) is not credible:
  - both fingerprints are estimated from the same 12 training images;
  - the denoiser is a Gaussian stand-in;
  - the impostor NCC is 0.067 against a genuine 0.086 (it should be about 0);
  - attribution stays 1.000 at Q50 and PCE stays at about 213, far above the usual threshold of about 60.
  The data do not show PRNU "fragility"; they show the opposite. Drop E4 or redo it properly on VISION or Dresden.
- Imperceptibility. At 2x zoom the (0,2) carrier is visible as faint period-8 vertical striping in flat sky (see the left panel of the probe image). Report a perceptual metric (LPIPS, or a JND-based visibility test) and include a visual figure. E1 and E3 are never combined, so their joint fidelity (about 35 dB expected) is unreported.

**M9. Stale or unbacked micro-benchmarks.** Table III, L1446 and L1448 (rows 26-29). Replace them with e5 numbers after fixing `bench_seed_select`.

**M10. Length.** 21 pages against a TIFS norm of about 10 (overlength charges and editor pushback). See section 6.

**M11. Reproducibility statement without an artifact link.** L1917-1932 and L1434 say the code is "released", but no URL or DOI is given. Add a repository or archive DOI (e.g. Zenodo), or state "provided as supplementary material".

### MINOR

1. L772-773: coordinate resolution about 2e-5 degrees, not 1e-4 (row 8). L837: "~1-2%" should be about 3% (row 9).
2. Table V "inf / 58+": explain that A = 0.5 rounds to zero in 8-bit.
3. L1503-1504, L1672-1674: photometric counts (rows 31, 41). Table IV WebP BER range (row 32).
4. L1416 "O(1) ledger lookup": overclaim.
5. L1836 "a compromised or coerced CA": should be TSA.
6. L1852 cites ProofMode for OpenTimestamps: cite OpenTimestamps directly.
7. The Definition of forgery (L1108-1113) is circular ("up to the transformations the verifier is designed to tolerate"). Give a security game (adversary capabilities, oracle access to captures, winning condition defined via F and tau).
8. L1211 "Each accepted verdict rests on exponential barriers": the fingerprint is not an exponential barrier (C2).
9. A3 on rollups (L511-513) depends on sequencer and fraud-proof assumptions. State which chain class A3 assumes.
10. L1229-1232 "does not help until the forgery has become the source image": at alpha = 1 it is still rejected, so the sentence is speculative. Rephrase to what was measured.
11. Experiments use random 16-byte payloads, not the ID‖t‖geo structure. Say so (it matters for M4).
12. `\paragraph{...}` titles ending in "." render as ".:" in IEEEtran: "capacitance).:", "pixels).:", "bonding).:", "trade-offs.:", "two-layer mark.:" (L648, L673, L693, L724, L746). Remove the trailing periods.
13. Three overfull hboxes; font warning `OT1/ptm/m/scit` (`\textsc` inside `\emph`). The PDF Title metadata is empty: add `\hypersetup{pdftitle=...}`.
14. The future-work list labels E1-E6 (L1774-1782) collide with the experiment names. Rename them F1-F6 and fix L514 and L737.
15. L634 "Because a reviewer (and an OEM) will ask": inappropriate in a paper.
16. Tone: "honest" (L724, L1338, L1506, L1860), "decisive enabler", "Crucially", "resolved by construction, not asserted", "practical irrelevance" (L1906-1907), "Life-saving" heading (L1409). The word "real" appears 44 times; keep it once in the methodology.

---

## 6. Presentation and length

The current length is 21 pages; the target is about 10-11. None of the cuts below touches the blockchain or the device-identity layer.

| Cut | Est. saving |
|---|---|
| Move §IV-B (manufacturing M1-M3) and Figs. 2-5 (four `figure*` floats) to supplementary material; keep a 1-paragraph summary of the gain spectrum and the hardware "ask" | ~3.0 pp |
| Drop Fig. 6 (datapath): it duplicates Fig. 1 and Alg. 1. Drop the "Step-by-step" paragraph (L920-936), which duplicates Alg. 1 | ~0.8 pp |
| Drop Table III, the micro-benchmark paragraph, and the v1/v2 prototype paragraph (L1423-1474); one sentence of e5 timings suffices | ~0.6 pp |
| Move Listing 1 (Solidity) to the supplement; describe the interface in 4 lines | ~0.6 pp |
| Compress Sec. II Background (CMOS, codecs, primitives) to one paragraph | ~0.6 pp |
| Compress Related Work to about 1 column (keep Table I) | ~0.8 pp |
| Delete Sec. VIII "Applications" (fold 2 sentences into the intro) | ~0.4 pp |
| Video subsection (no experiments): 2 sentences in Discussion | ~0.3 pp |
| E3 per-pixel localization (needs hardware not assumed elsewhere) and E4 PRNU (flawed): move to the supplement or drop; keep one sentence on E3 | ~1.0 pp |
| Discussion: condense privacy, "why a ledger", adoption, and OEM standard by about 50%; merge "Failure-safe semantics" into the Verdicts paragraph | ~0.8 pp |
| Contributions: 7 items to 4; shorten the intro fraud-statistics paragraph; merge the Conflict of Interest, Reproducibility and Data Availability sections | ~0.5 pp |
| Remove the threat-catalogue prose that duplicates Table II (keep the table plus 3-4 sentences on non-obvious rows) | ~0.5 pp |

The total is about 9.5 pp, which lands at about 11 pages. Use part of the freed space for the C1/C2 evaluation, CIs, and a larger dataset.

Overclaiming to fix:
- Title and abstract say "Real-Time Blockchain Notarization" and "sensor embeds". Latency is not measured, and the embedding is simulated in software. Abstract: say "simulated sensor-gain embedding"; title: consider "Ledger-Anchored".
- "No prior approach occupies the intersection" (L439-441): C2PA 2.x soft binding (TrustMark / Digimarc watermark plus a manifest repository) combined with hardware signing and ProofMode/OpenTimestamps comes close. Position the paper as co-design and identity binding. Also cite capture-to-blockchain systems such as Numbers Protocol / Capture Cam and Starling Lab's Filecoin/IPFS pipelines.
- The Table I "Real-time ✓" (see 4.3).

## 7. References

All 71 distinct cited keys resolve in `references.bib`. One entry, `rfc6962`, is unused: remove it or cite it in the Merkle discussion. BibTeX reports no warnings. Entries whose details I could not confirm or that look inconsistent (flagged only; no replacements proposed):

| Key | Concern |
|---|---|
| `c2pa2026security` | ePrint 2026/804 and the Nikon Z6 III C2PA incident (Sept 2025) are load-bearing for L181-184, L966, L1838, L1846. Verify the ePrint number, author list, and that the paper actually documents the certificate revocation and "revoked certificates kept validating" |
| `tcg_sony2022` | The key says Sony but the text (L653) says Samsung. Verify the manufacturer, title ("World's First 16:4:1 ..."), authors, and EI 2022 ISS-257 |
| `pixelparallel3layer2021` | Key says 2021, entry says 2022. Article ID ISS-258 sits right after ISS-257 above, and the booktitle is spelled differently ("Imaging Sensors and Systems" vs "Image Sensors and Imaging Systems"). Verify |
| `hdrcis2024review` | Key says 2024, entry says 2025 (Chips 4(1):8). Verify |
| `baker_dcg_thesis` | Key says "baker", author is "Sahu, Suat U." (Boise State 2008). Verify author and title |
| `dcg_fdshared2020` | SSDM 2020, partial author list, no pages or DOI. Verify |
| `prnubench2025` | Typed `@inproceedings` with an arXiv booktitle; author "Croitoru ... and others" unverified |
| `tugofwar2024` | arXiv:2407.06174 "Sun, Hai and others": unverified authorship and title |
| `dlwatermarking2026`, `cstfmark2026`, `fragile2025hybrid`, `cucu_hybridbond2025`, `svgain2025` | Recent articles I could not verify (volume, article numbers, DOIs) |
| `videowatermark2018survey` | Asikuzzaman & Pickering's known survey is in IEEE TCSVT 2018; the Applied Sciences 8(10):1891 attribution looks doubtful. Verify |
| `hevcwatermark2020` | Tew & Wong in IEEE Access 8 (2020): no pages or DOI; verify |
| `dps_meta_brillnics2025`, `sony3wafer2024` | Plausible; verify the DOIs |
| `truepic2024capture`, `imec_w2w2024` | URL is the site root only; give the specific page and an access date |
| `ironscales2025`, `resemble2025threat`, `surfshark2025fraud` | Grey literature; no URL for IRONSCALES. TIFS reviewers discount vendor statistics; attribute them explicitly ("vendor estimates") |
| `trustedcomputing` | Generic; cite the specific TPM 2.0 Library spec revision |
| `merkle1987digital` | CRYPTO '87 appeared in LNCS 293 (1988); add the publisher |
| Style | Mixed initials and full names, mixed title case; arXiv items typed as `@article` with arXiv in `journal`. Normalize for IEEEtran |

## 8. Submission readiness

**arXiv**
- `make_bundle.sh` builds a tarball containing a `.bbl`, removes `references.bib`, and test-compiles with pdflatex only. Good.
- The bundle is not flat: it has `figures/` and `contracts/src/PixelRootRegistry.sol` (for `\lstinputlisting`). arXiv accepts subdirectories. If flat files are required, change `\graphicspath{{figures/}}`, the `\includegraphics` names, and the listing path, or inline the listing (better: move it to the supplement, see section 6).
- My clean compile of a copy (pdflatex, bibtex, pdflatex x2) succeeds: 21 pages, no undefined references, 3 overfull boxes, one font-shape warning.
- Before posting: set PDF metadata, decide on the IEEE preprint notice (IEEE allows posting the submitted version; add the IEEE copyright notice upon acceptance), and make sure `pixelroot.md` and `results.txt` (stale) are not in any bundle.

**IEEE TIFS**
- IEEEtran journal class, keywords, and an abstract of about 244 words (within the 250 limit): OK.
- Length: 21 pp (see section 6).
- Biographies and photo are needed at the final stage.
- The `\thanks` should follow IEEE "Manuscript received ..." conventions at acceptance.
- Supplementary zip: remove the stale `results.txt`, and regenerate `e6_device_identity.txt` and `e5_crypto.txt` after the fixes.
- README_SUBMISSION lists a non-existent `registry.sol` and "six figures".
- Add an artifact URL or DOI.
- The cover letter repeats the "240 forgeries" and "0/1224" claims; update it after C1/C2.

## 9. Prioritized fix list

1. **(C1)** Fix `lost_tiles`: compare only the actually-lost strip, cap the ignored area, and re-test with "splice + shift". Update Alg. 2 and Prop. 4.
2. **(C2)** Add the fingerprint-null-space adaptive attacker to E6; report acceptance against edit size; strengthen F (resolution, DC, multi-scale or robust hash); restate Prop. 4 and the abstract claims accordingly.
3. **(M1)** Key lots by (manufacturer, root), or put the manufacturer in the leaves; add a front-running test; correct L1273-1274.
4. **(M2)** Store `block.number` at sealing, or compare anchor timestamps; document the off-chain anchor-hash check; re-run E6 (the anchor-hash row is missing) and update Table VIII and L1052.
5. **(M3)** Make the layout independent of the questioned size, or state the geometry limitation; test true crops and downscales; fix the abstract, L1353 and L1500-1504.
6. **(M4)** Make the payload unique per capture (counter or nonce); multi-record lookup; specify the store's trust and availability model (content-addressed, root on-chain).
7. **(M5, M6)** Reconcile the privacy claims (rotating ID vs pk linkability; ZK and GDPR wording). Specify compromise-window semantics for revocation.
8. **(M7)** Fix or drop Prop. 2; state the Prop. 3 model and the union bound; align Prop. 1 with the V1 claim.
9. **(M8)** Larger, modern dataset at native resolution; CIs; held-out splice-size curve; attack the delivered JPEG; log rejection reasons; drop or redo E4; add perceptual fidelity.
10. **(M9, M11)** Delete Table III and the stale timings; fix `bench_seed_select`; add an artifact link.
11. **(M10)** Apply the cuts in section 6 (target about 11 pp).
12. Consistency: symbol table (sigma, lambda, t, H, r, m, n_s, A, delta, phi); G4; the decoder's high-pass in Eq. (residual) and Alg. 2; seed W‖H; delete revision-history phrases; rename future-work labels; fix the ".:" headings.
13. References: verify the flagged entries (especially `c2pa2026security` and `tcg_sony2022`), remove `rfc6962`, normalize styles.
14. Bundles: README, `results.txt`, metadata, regenerated results, updated cover letter.
