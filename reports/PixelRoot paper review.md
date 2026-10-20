# PixelRoot: deep-dive peer review

**Manuscript:** *PixelRoot: Hardware-Anchored, Sensor-Level Media Provenance with Real-Time Blockchain Notarization for Trustworthy Imaging* (`paper/pixelroot.tex`, as on branch `claude/brave-volta-16f3hg`)
**Review style:** IEEE Transactions on Information Forensics and Security (TIFS), full paper
**Scope:** Everything is reviewed and strengthened inside the paper's own architecture: a sensor-embedded in-pixel binding plus a blockchain-notarized hard binding. The blockchain is treated as integral. Every recommendation below keeps it, and several give it a larger role.

**Basis:**
- I read the full manuscript, `registry.sol`, the Python harness (`experiments/pixelroot.py`, `e1`–`e5`), the Node.js prototype (`server/`) and `results/ALL_RESULTS.txt`.
- I ran one new experiment (§4.1): a keyless copy-and-removal attack. Its script is in `reports/pixelroot_review_keyless_attacks.py`.

---

## 1. Summary of the submission

PixelRoot proposes binding authenticity to a capture at the moment of exposure, in two independent ways:

1. **In-pixel ("soft") binding.** The sensor applies a keyed, spread-spectrum gain modulation. Each of 384 Reed–Solomon-coded bits (RS(48,16) over a 128-bit payload of ID, time and location) is spread over R keyed 8×8 blocks. Each bit is carried as a ±A ramp on the low-frequency (0,2) DCT basis, which a per-column or per-region gain profile can produce. Read-back works without the original: the detector projects each block onto that basis, removes the local average, de-spreads and RS-decodes.
2. **Hard binding.** The device computes h = SHA-256(I ‖ m), batches it into a Merkle tree and seals the root on a public chain through `PixelRootRegistry.register()`. Verifiers prove inclusion with `verifyInclusion()`.

Verification returns one of four verdicts: Camera-original (V1∧V2), Transcoded-consistent (V2), Exact-copy (V1) or Unverified.

The paper adds:
- a sensor-manufacturing feasibility analysis (conversion-gain selection, coded exposure, and 3D stacking with Cu–Cu bonding);
- an optional per-pixel tamper-localization layer;
- three security propositions;
- a measured robustness study on the 24 Kodak images with real libjpeg/WebP codecs;
- a privacy-preserving notarization design and an adoption path.

## 2. Assessment against the author's goals

| Goal | Current status | After the revisions proposed here |
|---|---|---|
| Solves the problem end to end ("all-encompassing") | Partial. Photos only; no video results. V1 is unusable on files people actually receive (§4.3). | The hard binding covers the distributed encodings and video segments (§5.1, §5.6). |
| Robust | Good against compression; weak against geometry; **broken by a keyless copy attack** (§4.1). | The copy attack is defeated by an on-chain content binding (§5.2). |
| Extremely simple | No. Three key and identity mechanisms, four verdicts, a payload layout that varies with the payload, and an unspecified V2 trust model. | One rule ties both bindings: the pixels carry an ID, and the chain says what that ID must look like (§5.2). |
| Extremely reliable | Text overclaimed (fixed in PR #2). The security propositions do not model a realistic attacker (§4.2). | Security stated as an attacker game, with measured confidence intervals (§5.8). |
| Foundation for video provenance | Not yet. No video experiment, and a mark identical in every frame invites averaging (§4.6). | Segment Merkle trees on chain, with per-segment carrier keys (§5.6). |

**Verdict: major revision.** The core idea of combining an in-pixel binding with a public ledger is sound, timely and well motivated. The accompanying research report shows how pressing the problem is: credentials are stripped on upload, and regulators now expect two marking techniques. The current manuscript has one security flaw that must be fixed before acceptance (§4.1), one design gap in the hard binding (§4.3), an implementation mismatch in the blockchain component (§4.4), and no video evaluation. All four can be fixed **inside** the existing architecture, and doing so makes the blockchain more central, not less.

---

## 3. Strengths

1. **The right problem framing.** Provenance needs a binding that survives metadata stripping. The research report found that none of eight platforms preserved C2PA credentials on video (Washington Post, Oct 2025). That is exactly the gap PixelRoot targets.
2. **A complementary pair of bindings.** A brittle cryptographic commitment paired with a robust in-pixel signal is the correct shape. The EU AI Act Code of Practice (June 2026) independently arrives at "at least two machine-readable techniques".
3. **The public ledger as a trust-minimizing timestamp.** The argument against relying on a single time-stamping authority (§Discussion) is strengthened by the Nikon Z6 III incident. A vendor-controlled trust root failed there, and validators did not check revocation. Of all the components in the system, the ledger is the one no single party can rewrite.
4. **A JPEG-aware carrier choice.** A low-frequency DCT carrier aligned to the 8×8 grid, with host suppression and RS coding, is a solid and well-understood design. The measured raw BER stays near 2% down to Q10.
5. **Honest scope statements.** The paper separates what is measured, prototyped and analyzed. It reports the failures under rotation and resized-crop, and it makes a concrete, tiered hardware ask.
6. **A privacy design** (salted leaves, pseudonymous IDs, optional location, GDPR erasure via off-chain deletion) that is ahead of most blockchain-provenance proposals.
7. **Reproducible artifacts:** released scripts, pinned dependencies, and results that I could trace end to end.

---

## 4. Major weaknesses

### 4.1 A copy attack succeeds with no key and no original (critical)

**Why the attack works.** The detector's host-suppressed projection (`_project_field`) uses only public information: the (0,2) basis and a 5×5 local-mean filter. Anyone can therefore compute the mark's estimate from a single marked image. With R·n_c equal to the block count, **every block is a carrier**, so nothing about the block positions is secret. Only the chip signs are, and the estimate captures the signs directly.

**What I measured.** I ran this attack against the paper's own code (`pixelroot.py`, A=4, RS(48,16)). The setup was 12 natural 512×512 crops (scikit-image sample images; the Kodak host was unreachable), with R=10. The attacker has one marked image, no key and no original.

| Attacker's source image | Genuine decode | Keyless copy → forged image B decodes as A's payload | Keyless removal → payload still decodes |
|---|---|---|---|
| Lossless marked image | 8/12 | **64/88 (73%)** | 0/8 |
| Shared JPEG Q75 copy | 8/12 | **61/88 (69%)** | 0/8 |

**What this means.**
- A real PixelRoot identity can be stamped onto a deepfake from a single public post, including a recompressed one.
- Under the paper's Definition 1, this is a successful forgery: the verdict would be "Transcoded-consistent".
- The same estimate also removes the mark completely, though removal only leads to "Unverified", which is fail-safe.

**How the paper's own tests missed this.**
- E2(C) used the true original image to compute the residual, which overstates how hard the attack is.
- E2(C) counted success only if the forged image matched a *fresh random* identity, which a copied mark can never match. The "0/17" figure is therefore not evidence of security.
- The text calls the 15/17 case "copy exposed". It is the opposite.

**Fix:** §5.2, an on-chain content binding. Report this attack in the paper; it strengthens the case for the blockchain.

### 4.2 The security propositions do not model the attacker that matters

- **Proposition 2** bounds the probability of *guessing the whole layout*. That is not the attacker's task. The attacker needs to estimate the signal well enough to copy or remove it, which §4.1 shows is easy. Also, with m = N_B (the evaluated setting) the binomial term is 1.
- The claim "observing many images leaks nothing" assumes s = H(k‖m). The code uses SHA-256(k) only, so every image from an OEM shares one layout. A fixed layout is exposed to averaging (Yang et al., NeurIPS 2024) and to PRNU-style estimation.
- **Proposition 3** assumes per-bit error p≈½ independent of the claimed codeword. That holds for an unmarked image, but not for an image carrying a copied mark of the claimed payload.
- **Proposition 1** proves only an *upper* bound on capture time (the image existed by block t_b). It says nothing about a *lower* bound (§5.5).

**Fix.** Replace Propositions 2–3 with an explicit game. The attacker gets q marked images (optionally recompressed) and must output an image that is (a) accepted with a target identity m* and (b) not derived from the capture registered for m*. Then prove the bound *with* the on-chain content binding of §5.2, where the attacker's advantage reduces to colliding a robust fingerprint against a committed one plus the RS false-accept term.

### 4.3 The hard binding (V1) cannot be checked on what people actually receive

The leaf is h = SHA-256(I ‖ m) over the lossless readout I. Every recipient receives a JPEG, HEIC or MP4 encoding. The paper itself says V1 is "destroyed by any re-encoding", and the camera's *own* encoder is a re-encoding. So, as specified:
- "Camera-original" is reachable only by someone holding the raw frame.
- In practice, V1 is never available to a platform or a court that holds the delivered file.

**Fix:** §5.1, commit the emitted encodings, and for video the segments.

### 4.4 The blockchain implementation does not match the paper or the off-chain code

These are concrete, verifiable defects in the component the user regards as integral:

1. **Hash mismatch.** `registry.sol` hashes Merkle pairs with `keccak256`. The off-chain builder in `e5_crypto.py` uses SHA-256 and claims it "matches registry.sol". A proof built off-chain will **never** verify on-chain.
2. **No leaf/node domain separation.** With raw 32-byte leaves and pair hashing that is otherwise identical, an internal node can be presented as a leaf. Standard practice is to hash leaves with a distinct prefix or to double-hash them, as OpenZeppelin's MerkleProof guidance does.
3. **The last node is duplicated on odd levels.** `e5_crypto.py` pads with a copy of the last node. This permits the CVE-2012-2459-style mutation (two different leaf lists with the same root). Pad with a fixed zero node, or commit the leaf count into the root.
4. **`register()` is permissionless and unauthenticated.**
   - Anyone can seal any root.
   - `submitter` and `leafCount` are attacker-chosen and unverified.
   - Front-running a pending root records the attacker as submitter.

   The timestamp guarantee survives, because the earliest sealing is still correct. But the event data the paper suggests courts rely on ("bind a root to a device class") does not. The "rotating device pseudonym signs the register call" design is described but not implemented.
5. **`block.timestamp` is proposer-influenced** (seconds of skew on PoS Ethereum, more on some L2s). This is fine for proof of existence, but state the bound.
6. **The prototype's "blockchain" is `crypto.randomBytes(32)`** (`server/pixelroot.js:172`). The paper does label notarization as simulated, but the abstract's "real-time blockchain notarization" and "within seconds of the shutter" are unmeasured.
7. **The gas estimate** omits cold-slot access (EIP-2929, +2,100 gas) and uses an ad-hoc calldata term. Measure it on a testnet instead (§5.4).

### 4.5 Physical realism of the embedding

1. **Gain is multiplicative; the experiments add.** Equation (embed) and the code add Δ = A·σ·c·Φ to luma. A sensor gain change produces Δ ∝ (scene signal) × g(x,y):
   - In dark regions the mark vanishes.
   - In bright regions it clips at saturation.
   - The SNR follows exposure, not a fixed A.

   None of this is simulated. Simulate multiplicative gain in the linear RAW domain, followed by demosaicing, white balance, a tone curve, denoising and sharpening. Even a simple open ISP pipeline would do, run on any public RAW set.
2. **Per-column gain cannot produce a block-keyed layout.**
   - A per-column profile g(x) applies the same gain to every row of a column, so all blocks in a block-column share one chip sign.
   - The keyed layout needs independent signs per block. That requires per-region control, or per-column gain re-programmed at line rate during rolling-shutter readout.
   - The claim that "even per-column control realizes it" must be qualified, or the line-rate re-programming path argued for explicitly.
3. **Interaction with fixed-pattern-noise and lens-shading correction.** These are already flagged as future work (E5), but they determine whether the mark survives the camera's own pipeline. At minimum, add a simulation.

### 4.6 There is no video evaluation, although video is the motivating case

- The title, abstract and discussion position PixelRoot for video. No video is evaluated.
- A mark identical in every frame is the easiest possible case for an averaging attacker: averaging n frames of one shot removes scene variation by about √n.
- Video watermark results in the research notes show Video Seal falling to chance at H.264 CRF 45 (COVER benchmark). This must be measured, not assumed.

**Fix:** §5.6.

### 4.7 Screen re-capture by a genuine device

A genuine PixelRoot camera filming a deepfake on a monitor produces a fully valid Camera-original record. The paper's treatment ("exposes back-dating") answers a different attack. The attacker does not back-date; they present the re-capture as a live event.

The ledger cannot fix this alone, but it can carry the evidence. Commit capture-time liveness signals into the on-chain record, so a verifier can check them later:
- depth or ToF data, as Sony does;
- focus distance;
- moiré statistics.

### 4.8 The key architecture is unspecified, and one leak compromises the whole fleet

- A single symmetric OEM key k is shared fleet-wide. Extracting it from any one secure element lets an attacker forge V2 for every device.
- Assumption A1 covers the OTP ID, not k.
- There is no device-level key, no revocation path, and no statement of what happens to past captures when a key leaks. The Nikon case shows this is the realistic failure, not a theoretical one.

**Fix:** §5.3.

### 4.9 Novelty and related work

- **Sensor-level watermarking has prior art that should be cited and differentiated:**
  - the Digimarc patent family "Digital watermarking CMOS sensor" (US7688994, US8280098) and "Digital watermarking image signals on-chip" (US8457346);
  - Blythe & Fridrich, "Secure Digital Camera" (DFRWS 2004);
  - Mohanty et al.'s CMOS watermarking chip.
- **Foundational spread-spectrum work is missing:** Cox et al. (1997); Hartung & Girod (1998).
- **Attack literature is missing:** the Kutter copy attack (2000), regeneration removal (Zhao et al., NeurIPS 2024), averaging (Yang et al., 2024) and WAVES-based attacks beyond the benchmark itself.
- **Industrial systems are missing:** SynthID, Video Seal/Pixel Seal, TrustMark, and C2PA 2.2's watermark-to-manifest resolution ("Durable Content Credentials").
- **Table I** marks C2PA ✗ for "survives meta-strip". That is no longer accurate for C2PA with soft bindings and should become "partial".
- **Narrow the novelty claim.** The defensible novelty is the combination: a hardware-originated spread-spectrum mark whose identity is resolved and content-bound through a public ledger, plus the tiered sensor ask. This review's fixes make that claim stronger.

---

## 5. Revisions that keep the architecture

These are the substance of the review. Each one keeps the sensor mark and the blockchain, and uses the chain to close a gap above.

### 5.1 Commit what is distributed (fixes §4.3)

Make the Merkle leaf a small record, not a single hash:

```
leaf = H( 0x00 ‖ H(raw I) ‖ H(encoded JPEG/HEIC bytes) ‖ H(m) ‖ salt )
```

- V1 on a delivered file now succeeds whenever the file is the camera's own encoding, which is the common case for journalism and courts.
- Raw-domain forensics remain possible.
- The verdict list stays the same; "Camera-original" simply becomes reachable in practice.

### 5.2 Content-bound IDs on chain (fixes §4.1, §4.2, and the payload-dependence gap)

This is the single most important change, and it makes the blockchain do real work.

1. **Pixels carry an ID.** The in-pixel payload is the identifier of the on-chain record (for example 64–96 bits). An ID derived from the leaf, such as `ID = trunc(leaf)`, suffices. The full m (device pseudonym, time, location) lives in the off-chain record committed by that leaf.
   - This removes the circular "verifier needs m′ to find the carriers" problem.
   - The carrier layout depends only on the device key and a per-asset nonce. The nonce is also committed in the record, so it is never derived from m.
2. **The record carries a content fingerprint.** The record commits a robust perceptual fingerprint F(I) of the image (or of each video segment, §5.6): for example PDQ, or the projection field itself at coarse resolution.
3. **The verifier checks the binding.** It extracts the ID from the pixels, retrieves the record via the on-chain root, and accepts V2 only if `dist(F(I′), F_committed) ≤ τ`.
4. **Why the copy attack now fails.** A transplanted ID resolves to a record whose fingerprint describes a *different* image. A keyless forgery now has to collide the fingerprint as well. That is a measurable, tunable false-accept rate to report alongside the RS bound.
5. **Privacy.** A perceptual fingerprint reveals coarse content. Keep it off-chain, encrypted under a key held by the holder or the OEM, and committed by hash on chain. It is disclosed only when someone verifies. This matches the paper's existing salted-commitment model.

**Experiment to add:** re-run E2(C) and the keyless attack of §4.1 with the fingerprint check. Target: 0 accepted forgeries, with the fingerprint false-accept rate reported at τ.

### 5.3 Per-device keys, an on-chain key registry and revocation (fixes §4.8)

- **Derive per-device keys:** `k_dev = KDF(k_OEM_root, device_pseudonym)`. Only k_dev leaves the secure element's protection, and only for its own captures.
- **Extend the contract with a device-key registry:**
  - `registerDevice(pseudonymKeyHash, attestationRoot)`
  - `revokeDevice(pseudonymKeyHash)`, which records the block number.
- **Revocation becomes a ledger fact, not a validator option.** `verifyInclusion` returns `(included, sealedAt, deviceRevokedAt)`. A capture sealed *before* revocation stays valid; captures after it fail. This is exactly the "valid at time of capture" semantics that certificate revocation lists struggle to provide, and it directly addresses the Nikon lesson.
- **Require registration to be signed** by a registered device or batcher key. This closes the unauthenticated `register()` problem (§4.4-4).

### 5.4 Two-speed notarization: substantiate "real-time" (fixes §4.4-6/7)

- **Fast path.** Commit batches every few seconds to a low-latency chain or L2 rollup (sub-minute finality). Each capture's leaf includes the previous batch root, chaining batches.
- **Settlement path.** Periodically checkpoint fast-path roots to a high-security L1.
- **Offline capture.** Queue the leaf in the secure element with a monotonic counter, so gaps are detectable.
- **Measure on a public testnet:**
  - shutter-to-inclusion latency (p50/p95);
  - finality time;
  - gas per batch, including EIP-2929 costs;
  - cost per image at N = 1, 100 and 10⁴.

  Replace "real-time" with the measured number.

### 5.5 Bracket capture time with blocks: a lower bound only a blockchain gives

Before exposure, fetch a recent block hash (or a public randomness beacon value) and include a short prefix of it in the payload m, and therefore in the pixels.

- The image provably could not have been captured before that block, because the mark depends on a value that did not exist yet. Proposition 1 already gives the upper bound.
- Capture time is now *bracketed* between two public blocks, which neither a time-stamping authority nor C2PA timestamps provide.
- This directly counters footage pre-produced and later passed off as "live".
- It is a strong, distinctive contribution: add it as a new Proposition 1b.

### 5.6 Video as Merkle trees of segments (fixes §4.6)

- **Segment leaves.** Commit each 1–2 s CMAF/GOP segment as a leaf. The clip root is a leaf in the device batch, so trimming is still provable: a clip subset proves inclusion of its segments.
- **Per-segment carrier keys.** Derive them as `k_seg = KDF(k_dev, nonce, segment_index)`, so the mark differs every segment. Averaging within a segment still helps the attacker; quantify how many frames per segment make the estimate usable, and choose the segment length accordingly.
- **Per-segment IDs.** Each segment carries its own short ID and fingerprint (§5.2), so a re-encoded clip of any length resolves to its exact segments on chain.
- **Experiments:**
  - H.264 and HEVC at CRF 23/28/35/45;
  - frame-rate conversion;
  - a platform-style transcoding ladder;
  - one live upload/download round-trip on a major platform;
  - the averaging attack across frames.

### 5.7 Publicly verifiable V2 through commit-reveal on chain (fixes the G4 gap)

- **At capture,** commit `H(k_asset)` in the record.
- **Later, reveal `k_asset`** in a reveal transaction, either when the owner publishes or after a delay Δ, in the style of TESLA delayed key disclosure.
- **Anyone can then run V2 publicly.** Revealing one asset's key reveals nothing about other assets, because the keys are derived per asset.
- **The obvious risk is now covered.** Once a key is revealed, an attacker could re-embed that asset's mark elsewhere. The content-bound fingerprint (§5.2) defeats this.
- **Value.** This gives the "fully public verification" the paper lists as future work, using the chain.

### 5.8 Evaluation upgrades for reliability claims

1. **Wilson 95% confidence intervals** on every k/24 figure. For example 23/24 → [0.79, 0.99] and 0/1200 → [0, 0.0032]. 24 images cannot support "≈96%" without them.
2. **Larger, camera-native data:** RAW datasets (e.g. MIT-Adobe FiveK, RAISE) for the multiplicative-gain simulation (§4.5), plus Dresden or VISION for multi-device PRNU.
3. **Name the failing frame.** Characterize the one texture-heavy frame that fails at every A ≤ 6, and say whether adaptive amplitude would fix it.
4. **Report the attacks in the main robustness table:**
   - keyless copy (§4.1) and averaging, before and after §5.2;
   - regeneration (diffusion re-encode).

   Regeneration will remove the mark. That is acceptable: report it as fail-safe "Unverified", which is the paper's own semantics.
5. **Resolution scaling.** R grows with resolution: a 12 MP frame has about 190k blocks, so R≈490. Report BER against resolution, because Kodak's 0.4 MP understates real-world robustness.
6. **Geometric synchronization.** The paper names a sync template as the fix for rotation and resized-crop. Implement it, or keep the limitation explicit in the abstract.

### 5.9 Writing, consistency and claims

- **Already fixed in PR #2:** PSNR, resize, crop and JPEG counts; the Proposition 1–3 wording; disclosure of the prototype seed; the benchmark frame size.
- **Still open:**
  - the off-chain/on-chain hash mismatch (§4.4-1);
  - Table I's C2PA row;
  - E2(C)'s "copy exposed" framing (§4.1);
  - "Samsung signs captures" (it signs AI-edited images only);
  - "losses tripling" (the trackers report roughly 4× *incidents*; losses are not comparable year on year);
  - vendor statistics in the introduction, which need a "vendor-reported, lower bound" qualifier.
- **Tone down absolute claims:**
  - "never certifies a manipulated artifact" (false under §4.1 until §5.2 lands);
  - "affirmative, hardware-rooted proof";
  - "practical irrelevance".

---

## 6. Minor issues

1. The abstract lists five contributions in about 250 words. Trim to the three that are measured, and move the feasibility and privacy items to the introduction.
2. Algorithm 1 sets the gain ramp *before* exposure, then reads out. For M3 (digital gain on a stacked die) the order is the reverse. Show both.
3. Equation (residual) divides by ⟨Φ,Φ⟩, but the code also subtracts a 5×5 local mean, so the "host suppression" is not in the equations. Add it.
4. `extract_resync` searches ±28 px in E1, but the text says "small range". State the range and its cost: 225 coarse plus 49 fine decodes per image.
5. The localization layer (E3) uses δ=4 per-pixel ±1 noise, which is fragile and copyable in the same way as §4.1. Say so, or bind it to the record too.
6. `fragile_pattern` and `keyed_plan` both use 32-bit NumPy seeds. State that the full CSPRNG is a requirement for deployment, not just a convenience.
7. Figure 1's "Exact-copy" path (V1 only) is in Algorithm 2 but not in the figure.
8. The privacy section should state who can link a pseudonym to a device (OEM only?) and under what legal process.
9. "Real-time" appears in the title. Either measure it (§5.4) or soften it to "capture-time".
10. The reference list is missing the works in §4.9. Several existing citations are vendor blogs; prefer primary sources where they exist.

---

## 7. Prioritized revision list

| Priority | Item | Section | Effort |
|---|---|---|---|
| **P0** | On-chain content-bound IDs; re-run the copy and keyless attacks | §5.2, §4.1 | Medium |
| **P0** | Fix the keccak/SHA-256 Merkle mismatch, leaf domain separation and odd-node padding | §4.4 | Small |
| **P0** | Commit the encoded outputs in the leaf so V1 works on delivered files | §5.1 | Small |
| **P0** | Correct E2(C) framing and Propositions 2–3 into an attacker game | §4.2 | Medium |
| **P1** | Video segment Merkle trees + per-segment keys + H.264/HEVC experiments | §5.6 | Large |
| **P1** | Per-device keys, on-chain device registry and revocation; authenticated `register()` | §5.3 | Medium |
| **P1** | Testnet deployment: latency, finality, gas; replace "real-time" with numbers | §5.4 | Medium |
| **P1** | Multiplicative-gain RAW→ISP simulation; per-column vs per-region correction | §4.5 | Medium |
| **P2** | Block-hash lower bound on capture time (Proposition 1b) | §5.5 | Small |
| **P2** | Commit-reveal for public V2 | §5.7 | Medium |
| **P2** | Related work and novelty narrowing; Table I update | §4.9 | Small |
| **P2** | Confidence intervals, RAW datasets, resolution scaling, attack rows | §5.8 | Medium |
| **P3** | Re-capture liveness signals committed on chain | §4.7 | Small (design) |
| **P3** | Minor issues 1–10 | §6 | Small |

## 8. Questions for the author

1. Is the in-pixel payload meant to be decodable *without* any external record? Section 5.2 assumes not, and that the chain is the resolver. If it is meant to be self-contained, how does the verifier obtain m′ after stripping?
2. Which chain or L2 is targeted, and what finality and fees does that imply for "real-time"?
3. Is k per OEM, per device model, or per device? What is the recovery plan if it leaks?
4. Can column PGA gains on the target sensors be re-programmed at line rate? If not, which tier delivers the block-keyed layout?
5. For video, is the mark applied on every frame or only on keyframes, and how does that interact with the encoder's motion-compensated prediction?

---

## Appendix A: Reproducing the keyless attack (§4.1)

```
pip install numpy pillow scikit-image scipy reedsolo
python3 reports/pixelroot_review_keyless_attacks.py
```

The script imports `paper/experiments/pixelroot.py` unchanged and embeds with the paper's parameters (A=4, RS(48,16)) on 512×512 crops of scikit-image sample photos. The attacker then:
1. estimates the mark from one marked image, without the key, using the public (0,2) basis and the same 5×5 local-mean suppression as the detector;
2. adds 1.5× the estimate to a different image (copy), or subtracts 1.2× it from the marked image (removal);
3. is judged with the true key.

Results were measured on 2026-10-18 (the Kodak host was blocked from this environment):

```
source=lossless  images=12  R=10
  genuine decode          8/12
  keyless copy -> forged B decodes as A's payload: 64/88
  keyless removal -> payload still decodes:        0/8
source=JPEG Q75  images=12  R=10
  genuine decode          8/12
  keyless copy -> forged B decodes as A's payload: 61/88
  keyless removal -> payload still decodes:        0/8
```

Caveats:
- The test set is small and texture-heavy: grass, gravel and brick crops are among the 4 that fail even genuine decoding. Re-run on Kodak to obtain numbers comparable to Table II.
- The copy and removal gains (1.5×, 1.2×) were not tuned. A tuned attacker would do better.
