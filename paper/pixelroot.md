# PixelRoot: Hardware-Anchored, Sensor-Level Media Provenance with Real-Time Blockchain Notarization for Trustworthy Imaging

**Mihir Kavishwar** — PixelRoot Project — hello@mihirkavishwar.com

> Readable Markdown rendering of the manuscript. The authoritative,
> submission-ready version is `pixelroot.tex` (IEEE conference format) with
> citations in `references.bib`.

---

## Abstract

The realism of AI-generated "deepfake" imagery has outpaced the ability of society to tell synthetic media from camera-captured reality. Reactive, detector-based defenses are locked in an adversarial arms race and fail to generalize to unseen generators, while existing provenance schemes bind trust to *metadata* that can be stripped, edited, or transplanted. We present **PixelRoot**, a media-authenticity framework that moves the root of trust from metadata into the *pixels themselves*. At the instant of capture, a CMOS image sensor modulates a sparse, pseudorandomly selected set of pixels to embed a 128-bit provenance payload — the sensor's factory-burned device identity, a trusted timestamp, and a quantized capture location — protected by Reed–Solomon error correction. A SHA-256 commitment over the image and its payload is then notarized to a public blockchain within seconds of the shutter event, closing the window in which a forgery could be substituted. We contribute: (i) a structured literature survey unifying five previously disjoint research threads — deepfake detection, passive sensor forensics (PRNU), active watermarking, content-provenance standards (C2PA), and blockchain media integrity — and a gap analysis that motivates a *dual-binding* design; (ii) a formal architecture and threat model with a security argument against re-capture, metadata forgery, replay, compression-laundering, and PRNU fingerprint-copy attacks; (iii) an analysis of payload survivability under JPEG and H.264/HEVC compression that clarifies the fragile/semi-fragile trade-off; and (iv) an evaluation plan and a reference software implementation. We argue that, deployed as an OEM interoperability standard analogous to JPEG or 3GPP, sensor-level provenance plus real-time notarization can give legal, journalistic, third-party (3P), and life-saving applications an affirmative, hardware-rooted proof of authenticity rather than a probabilistic guess.

**Keywords:** media provenance, deepfakes, blockchain, CMOS image sensor, PRNU, digital watermarking, content authenticity, C2PA, image forensics, JPEG.

---

## 1. Introduction

Digital images and videos have become primary evidence in journalism, courts, insurance, humanitarian monitoring, and everyday social discourse. That evidentiary role is collapsing. Diffusion models, GANs, and neural rendering now synthesize photorealistic faces, scenes, and full videos that humans — and automated detectors — routinely fail to distinguish from reality [Croitoru 2024; Verdoliva 2020]. The harm is no longer hypothetical. Industry incident trackers attribute on the order of **\$1.2–1.3 billion in documented fraud losses to deepfakes in 2025, roughly tripling year over year**, with the overwhelming majority of losses originating on social-media platforms [Resemble AI 2025; Surfshark 2025]; enterprise surveys report that a majority of organizations experienced deepfake-related incidents with mean losses exceeding \$280,000 [IRONSCALES 2025]. Beyond fraud, non-consensual intimate imagery and election disinformation erode personal safety and institutional trust.

The dominant technical response has been **reactive detection**: train a classifier to spot the statistical fingerprints of a given generator. This strategy is structurally disadvantaged. Detectors overfit to the artifacts of the generators in their training set and degrade sharply on unseen models — recent in-the-wild benchmarks report **AUC drops of roughly 45–50%** relative to academic datasets [Deepfake-Eval-2024; Croitoru 2024]. Because every published detector also serves as a differentiable signal that the next generation of generators can be trained to defeat, detection is a perpetual "tug of war" the defender is not guaranteed to win [Tug-of-War 2024; Kaur 2024].

An alternative philosophy inverts the problem: instead of trying to prove a piece of media is *fake*, prove that a piece of media is *real* by binding it, at creation time, to a trustworthy origin. This is the **provenance** paradigm now embodied by the C2PA Content Credentials standard and by secure-capture products such as Truepic and ProofMode [C2PA 2024; Truepic 2024; ProofMode 2023; Google 2025]. These systems are a major advance, but they share a structural weakness: the authenticity claim is carried in a **signed metadata container** attached to the file. Metadata can be deliberately stripped by platforms, lost in transcoding, or the binding itself can be attacked (a 2025 camera firmware deployment had to revoke all certificates after a signing vulnerability). If the credential is removed, the pixels carry no inherent evidence of their origin.

### 1.1 The PixelRoot thesis

A robust root of trust for visual media should live where the information actually is: **in the pixels, anchored to physical hardware, and witnessed by an immutable public ledger.** PixelRoot embeds a provenance payload *into the pixel values* at the moment of capture through controlled per-pixel sensor gain modulation, and *simultaneously* notarizes a cryptographic commitment of the image to a blockchain. This yields two independent bindings:

- a **hard binding** — a SHA-256 commitment recorded on-chain, giving an immutable, publicly verifiable timestamp of existence; and
- a **soft, in-pixel binding** — a sparse, error-corrected signature tied to the sensor's factory identity that travels *with the pixels* even if the file container and its metadata are destroyed.

The two are complementary: the hard binding gives cryptographic non-repudiation but is destroyed by any re-encoding; the in-pixel binding tolerates mild processing and survives metadata stripping, but is statistically softer. **Together they cover each other's failure modes.**

### 1.2 Contributions

1. **A unifying survey and gap analysis** (§3) spanning deepfake generation/detection, passive PRNU forensics, active watermarking, provenance standards, and blockchain media integrity, showing no prior work simultaneously achieves (a) a hardware root of trust, (b) survival of metadata stripping, and (c) public real-time notarization.
2. **A formal architecture** (§5) for sensor-level payload embedding: the 128-bit metadata layout, payload-seeded PRNG pixel selection, Reed–Solomon protection, gain modulation, and a smart-contract notarization protocol.
3. **A threat model and security analysis** (§4, §6) covering re-capture, metadata forgery, replay, compression-laundering, deepfake substitution, and the PRNU fingerprint-copy attack.
4. **A compression-robustness analysis** (§7) relating JPEG quantization and H.264/HEVC coding to payload bit-error rate, and a discussion of the semantic-authenticity boundary.
5. **An evaluation plan and reference implementation** (§8) grounded in an open prototype, plus a roadmap toward an OEM standard (§9).

---

## 2. Background

### 2.1 The CMOS imaging pipeline

A camera integrates photo-generated charge in each photosite, converts it to a voltage, applies analog gain, and digitizes it. Manufacturing imperfections make each photosite's response slightly non-uniform; this multiplicative **photo-response non-uniformity (PRNU)** is a stable, device-unique noise pattern long used as a forensic "sensor fingerprint" [Lukáš 2006; Chen 2008]. Crucially, many sensors expose programmable per-column/per-region analog gain and exposure registers, and embed a factory-burned identifier in one-time-programmable (OTP) memory. PixelRoot **repurposes these existing controls**: rather than only *reading* the passive PRNU after the fact, it *actively writes* a chosen, error-corrected signal during exposure and ties it to the OTP identity.

### 2.2 Lossy compression: JPEG and MPEG/H.26x

Media is almost never stored losslessly. JPEG applies a block DCT, quantizes coefficients with a quality-dependent matrix that preferentially discards high-frequency energy, and entropy-codes the result [Wallace 1992]. Video codecs (MPEG-2, H.264/AVC, HEVC) add motion-compensated inter-frame prediction, integer transforms, in-loop deblocking, and group-of-pictures (GOP) structure [Wiegand 2003; Sullivan 2012]. All are *lossy and spatially redistributive* — exactly why any embedded signal must survive quantization (§7).

### 2.3 Cryptographic and blockchain primitives

PixelRoot relies on standard primitives: a collision-resistant hash (SHA-256 [NIST 2015]) for commitments and PRNG seeding; Reed–Solomon codes [Reed 1960] for error correction; Merkle trees [Merkle 1987] for batching many commitments into one on-chain transaction; and a public append-only ledger [Nakamoto 2008; Wood 2014] as an immutable timestamping witness. Large artifacts are *referenced*, not stored, on-chain, optionally via content-addressed storage [Benet 2014]. Hardware attestation of the signing environment follows trusted-computing practice [TCG 2019; Google 2025].

---

## 3. Related Work and Literature Survey

### 3.1 Deepfake generation and detection
Surveys by Verdoliva [2020], Mirsky & Lee [2021], and Croitoru et al. [2024] chart the progression from face-swap GANs to diffusion models and NeRFs across image, video, audio, and multimodal content. The recurring finding is poor **cross-generator generalization**: detectors trained on one family of fakes collapse on another [Croitoru 2024; Kaur 2024]. Deepfake-Eval-2024 quantifies this at 45–50% AUC degradation versus curated sets [Chandra 2025]. Generation vs. detection is increasingly framed as adversarial co-evolution in which detectors feed gradient signal to the next generator [Tug-of-War 2024]. **Limitation:** detection is reactive, probabilistic, and structurally one step behind; it cannot offer affirmative, durable proof a specific artifact is genuine.

### 3.2 Passive sensor forensics (PRNU)
PRNU source identification [Lukáš 2006], extended to integrity verification [Chen 2008], estimates a camera fingerprint from residual noise and correlates it (e.g., via peak-to-correlation energy) with a questioned image; benchmarks track modern-device accuracy [PRNU-Bench 2025]. Integrity surveys situate PRNU among splicing/copy-move/double-compression detectors [Korus 2017; Piva 2013]. **Limitations:** (i) PRNU is *passive* — needs a reference fingerprint and many images per device, and degrades on compressed/low-res media; (ii) it is vulnerable to the **fingerprint-copy (PRNU-copy) attack**, where an adversary estimates a victim's fingerprint from public images and transplants it into a forgery. The triangle test detects naïve copies but is itself defeated by improved, dispersed copy attacks [Goljan 2011] — a live cat-and-mouse. PixelRoot differs by *actively* embedding a *chosen, keyed, error-corrected* payload bound to the OTP identity and a ledger timestamp, rather than relying on an involuntary, copyable noise pattern.

### 3.3 Active authentication: digital watermarking
Watermarks are **robust** (survive processing, for copyright), **fragile** (break on any edit, for tamper localization), or **semi-fragile** (tolerate benign ops like JPEG but break on malicious edits) [Begum 2020; SciRep 2025]. Classic methods embed in DCT/DWT/SVD coefficients; recent work uses learned encoders/decoders [Sensors 2026]. Video schemes embed in H.264/HEVC transform coefficients or motion vectors and must fight quantization and motion-compensation drift [Asikuzzaman 2018; Tew 2020; CSTFMark 2026]. **Limitation:** watermarking alone provides no *public, time-anchored* record and no *hardware* root — a watermark embeddable in software is embeddable by an attacker. PixelRoot treats its in-pixel payload as a *semi-fragile, hardware-originated* watermark whose trust is bootstrapped by on-chain notarization and OTP identity.

### 3.4 Provenance standards and secure capture
C2PA Content Credentials define a signed manifest of assertions (capture device, time, edit history) bound to the asset by a hard hash, verifiable offline via a certificate chain [C2PA 2024]. Hardware-backed signing has reached consumer devices — Google Pixel signs photos with keys in the Titan M2 secure element plus an on-device timestamp authority [Google 2025] — and Leica/Sony/Samsung ship C2PA. Truepic's Controlled Capture verifies device integrity via attestation before on-device signing [Truepic 2024]; ProofMode captures sensor metadata, signs with per-capture keys, and registers hashes to public ledgers (OpenTimestamps/Bitcoin) [ProofMode 2023]. **Limitations:** the binding lives in a *detachable manifest*. If a platform strips metadata (many do) or transcodes the asset, the credential is lost and the bare pixels are again unverifiable; certificate compromise revokes trust wholesale. PixelRoot is **complementary** to C2PA — it can populate C2PA assertions — but additionally places a redundant proof *inside the pixels*, surviving manifest loss.

### 3.5 Blockchain-based media integrity
A large body of work anchors media hashes (exact and perceptual) to smart contracts, storing bulk content off-chain in IPFS [Qureshi 2021; Benet 2014]. Hasan & Salah use blockchain and smart contracts to trace deepfake video provenance back to a trusted original [Hasan 2019]; later systems combine perceptual hashing, watermarking, and Ethereum/Polygon contracts for video copyright/integrity [PLOS 2024; Frontiers 2025]. **Limitations:** these systems hash media *after* capture, typically in software at upload time, leaving a tampering window and no hardware root; exact hashes die on re-encoding while perceptual hashes trade away cryptographic guarantees. PixelRoot narrows the window to the shutter event and adds a hardware-anchored in-pixel binding the ledger alone cannot provide.

### 3.6 Gap analysis

| Approach | HW root | Survives meta-strip | Public ledger | Affirmative proof | Real-time |
|---|:--:|:--:|:--:|:--:|:--:|
| Deepfake detectors | ✗ | — | ✗ | ✗ | ✓ |
| PRNU forensics | partial | ✓ | ✗ | partial | ✗ |
| Watermarking | ✗ | ✓ | ✗ | partial | ✓ |
| C2PA / Truepic | ✓ | ✗ | optional | ✓ | ✓ |
| Blockchain hashing | ✗ | ✗ | ✓ | ✓ | partial |
| **PixelRoot (this work)** | ✓ | ✓ | ✓ | ✓ | ✓ |

No prior approach simultaneously offers a hardware root of trust, survival of metadata stripping, **and** public real-time notarization. PixelRoot is, to our knowledge, the first design to combine sensor-level in-pixel embedding with capture-time blockchain notarization at that intersection.

---

## 4. Threat Model and Design Goals

**Assumptions.** (A1) The sensor OTP identity and gain registers are written at manufacture and not feasibly re-programmable in the field; (A2) the capture-time signing/notarization environment is attested via a secure element [Google 2025; Truepic 2024]; (A3) the blockchain is append-only and economically infeasible to rewrite in the relevant timeframe [Nakamoto 2008]; (A4) standard crypto primitives are secure [NIST 2015].

**Adversary.** May forge/edit file metadata; generate a deepfake or Photoshop a real image; re-encode/transcode/compress; re-photograph a screen (analog "re-capture"); attempt PRNU fingerprint-copy [Goljan 2011]; and replay or back-date claims. **Cannot** economically clone a specific physical CMOS die or rewrite ledger history.

**Design goals.** G1 Affirmative authenticity · G2 Hardware root · G3 Metadata-independence · G4 Public verifiability · G5 Minimal capture latency · G6 Imperceptibility · G7 Standardizability.

---

## 5. The PixelRoot Architecture

### 5.1 Provenance payload
The payload **m** is a fixed-width 128-bit record (v2):

```
m = ID(48 bits)  ||  t(32 bits)  ||  (φ, λ)(48 bits: 24 per coordinate)
```

`ID` is the sensor's OTP device identifier (modeled as a 48-bit MAC-style value), `t` a Unix timestamp from an attested RTC/NTP source, and `(φ, λ)` a quantized lat/long (~1e-4 degree resolution). Location may be omitted or salted for privacy (§9).

### 5.2 Keyed pixel selection
The carrier pixels are chosen by a PRNG seeded by the payload:

```
s = trunc_32( SHA-256( k || m ) )
```

Positions `{(r_i, c_i)}` are drawn without repetition from the H×W grid using a PRNG keyed by `s`. Because the seed derives from **m** (and an OEM secret key `k`), a verifier told the claimed **m** can regenerate the exact positions, while an attacker without **m**/`k` cannot localize or enumerate the carriers.

### 5.3 Error-corrected encoding
The 128 payload bits are expanded with a Reed–Solomon code [Reed 1960] into `n_b = 128 + r` coded bits (`r ≈ 30` parity in the prototype), tolerating burst errors from compression and mild edits. Let `b_i ∈ {0,1}` be the i-th coded bit.

### 5.4 Sensor-level gain modulation (embedding)
During exposure, each selected photosite's analog gain is nudged multiplicatively:

```
g_i = 1 + α · b_i ,   α ≈ 0.02
```

so a "1" raises the pixel response by ~2% (~0.01 EV) and a "0" is nominal. The perturbation is sub-perceptual and spread across ~10² of millions of pixels (G6). This is an **active, hardware-rooted, semi-fragile watermark**, distinct from the involuntary PRNU that passive forensics merely observes.

### 5.5 Commitment and notarization
Immediately after readout the device computes the hard binding

```
h = SHA-256( I || m )
```

over the (lossless) image `I` and payload, then submits `h` (optionally with a device pseudonym and coarse time/location) to a notarization smart contract. For scale, many commitments are aggregated into a Merkle tree [Merkle 1987] and only the root is written on-chain; the contract emits an event whose block timestamp is the public "proof of existence" [ProofMode 2023]. If connectivity is briefly unavailable, `h` is queued in secure storage and submitted on reconnect, with the latency recorded.

**Algorithm 1 — capture-time embed-and-notarize**
```
1.  ID ← readOTP();  t ← attestedClock();  (φ,λ) ← gps()
2.  m  ← ID || t || (φ,λ)
3.  s  ← trunc_32(SHA-256(k || m))
4.  b  ← ReedSolomonEncode(m)
5.  P  ← PRNGselect(s, |b|, H, W)          # carrier pixels
6.  for each (r_i,c_i) in P:
7.      setGain(r_i, c_i, 1 + α·b_i)
8.  I  ← expose&readout()
9.  h  ← SHA-256(I || m)
10. notarize(h)                            # Merkle-batched on-chain commit
11. store I (lossless preferred) with m in C2PA manifest
```

### 5.6 Verification
Given a questioned image `I'` and a claimed payload `m'` (from the manifest, the on-chain record, or asserted by a party):

- **(V1) Hard binding / ledger check.** Recompute `h' = SHA-256(I' || m')` and confirm it appears in the ledger (directly or via a Merkle proof to the recorded root). A match proves `I'` existed bit-for-bit at the recorded block time. Conclusive but brittle: any re-encoding breaks it.
- **(V2) In-pixel binding check.** Regenerate `s` and the carrier set `P` from `m'` (and `k`), read back the relative gain at each carrier to recover noisy coded bits, Reed–Solomon-decode to `m̂`, and test `m̂ == m'`. The bit-error rate (BER) and decode success form a soft authenticity score that degrades gracefully under compression (§7). A keyed, spread carrier set means an attacker who edits/splices without knowing `P` corrupts the signature detectably.

A piece of media is accepted at the strongest supported level: **V1∧V2** (pristine original), **V2 only** (transcoded but pixel-consistent), or **V1 only** (exact copy, manifest intact).

---

## 6. Security Analysis

- **Deepfake / synthetic substitution.** A fully AI-generated image was never exposed on a genuine sensor: no valid on-chain commitment (V1 fails) and no payload-consistent, keyed in-pixel signature tied to a real OTP identity (V2 fails). The attacker would have to forge a ledger entry (infeasible, A3) or embed a valid signature without the OEM key and sensor (infeasible, A1–A2).
- **Metadata forgery / stripping.** Editing or removing metadata cannot manufacture a matching ledger commitment, nor create the in-pixel binding (G3). Stripping metadata downgrades a credential-only scheme to "unverifiable," but PixelRoot still recovers **m** from the pixels via V2.
- **Re-capture (photo-of-a-screen).** Re-photographing authentic media on a genuine PixelRoot sensor produces a *new* payload and a *new* commitment; it cannot reproduce the original's ledger entry. The provenance correctly reflects the re-capture event and time, exposing back-dating. Liveness heuristics (moiré, depth) [Truepic 2024] augment this.
- **Replay / back-dating.** Notarization binds to a block timestamp; the earliest provable existence is the block time. Reactive detection fundamentally lacks this property.
- **PRNU fingerprint-copy.** The strongest hardware-targeted attack against passive forensics transplants a victim's estimated PRNU [Goljan 2011]. PixelRoot resists because (i) its signature is an *active, keyed* code, not the involuntary PRNU, so copying passive noise does not reproduce carrier bits without the OEM key `k`; (ii) even a perfectly transplanted signature must still match an on-chain commitment made at capture by a genuine device (V1/A3); and (iii) triangle-test countermeasures remain a forensic backstop on the passive channel. PixelRoot converts a soft, copyable fingerprint into a key-protected, ledger-witnessed credential.
- **Compression-laundering.** Aggressive re-encoding breaks V1 and, past a threshold, V2 (§7); but this yields a *negative* result ("cannot verify"), never a *false positive* ("verified authentic"). **PixelRoot fails safe** — it never certifies a manipulated artifact as genuine; it only declines to certify.

---

## 7. Robustness Under Compression

The central tension: the hard binding (V1) is *fragile* by design — ideal for a pristine original — while real-world distribution demands *semi-fragile* survivability (V2).

### 7.1 JPEG
JPEG's quantization matrix scales with quality factor `Q` and most aggressively discards high-frequency DCT energy [Wallace 1992]. A ~2% gain perturbation at isolated pixels is partly high-frequency and is therefore attenuated as `Q` drops. To survive, the in-pixel channel should (i) place carriers to influence *mid-frequency* DCT coefficients of their 8×8 blocks, as in semi-fragile DCT watermarking [Begum 2020; SciRep 2025]; (ii) lean on Reed–Solomon parity to absorb residual errors; and (iii) use soft, correlation-based read-back rather than a hard per-pixel threshold. Expected behavior: near-zero BER at `Q ≳ 90`, graceful rise through mid quality, decode failure (safe "cannot verify") at low `Q`. The exact crossover is the key quantity to characterize (§8).

### 7.2 Video: MPEG / H.264 / HEVC
Video adds motion-compensated prediction, integer transforms, in-loop deblocking, and GOP structure [Wiegand 2003; Sullivan 2012]. The watermarking literature shows embedding survives best in mid-frequency transform coefficients and that I-frame perturbations propagate ("drift") through a GOP, so embedding is often confined to portions of the GOP [Asikuzzaman 2018; Tew 2020; CSTFMark 2026]. Practical PixelRoot design: embed the per-(key)frame payload at capture, and commit a Merkle root over keyframe hashes so frame-level verification localizes tampering. Learned, codec-aware embedding now survives non-differentiable H.264 [CSTFMark 2026] and is a natural upgrade path.

### 7.3 The semantic-authenticity boundary
A benign filter may alter carriers enough to fail V2 even though the image's *meaning* is unchanged (false alarm), while a malicious edit might in principle preserve carriers. PixelRoot therefore certifies **pixel-level integrity relative to a notarized original, not semantic equivalence.** This cleanly separates "bit-for-bit original" (V1), "faithfully transcoded" (V2), and "cannot establish provenance," and composes with perceptual-hash / content-similarity layers [PLOS 2024] for softer "same-scene" judgments.

---

## 8. Applications: Human-in-the-Loop Trust

PixelRoot keeps a human or institutional verifier in the loop with hardware-rooted evidence rather than a model's opinion.

- **Legal / evidentiary.** Chain-of-custody for photo/video evidence benefits from an immutable, independently timestamped capture-time commitment, reducing disputes over authenticity and time of creation [Korus 2017].
- **Journalism / third-party (3P) verification.** Platforms and fact-checkers verify against the public ledger without contacting the source — valuable for conflict and human-rights documentation, where ProofMode-style field capture is already deployed [ProofMode 2023].
- **Life-saving / high-assurance.** Insurance inspections, telemedicine imagery, infrastructure monitoring, and emergency reporting need affirmative proof an image is a real, current capture — the "prevent rather than detect" posture argued by secure-capture vendors [Truepic 2024].
- **Platform-scale screening.** Platforms perform an O(1) ledger lookup at upload to label assets "camera-original," "transcoded-but-consistent," or "unverified," shifting the default from "trust until debunked" to "label by provenance."

---

## 9. Evaluation Plan and Reference Implementation

**Reference implementation.** An open software prototype of the PixelRoot core implements the payload layout, SHA-256 seeding, PRNG carrier selection, gain-value generation, image hashing, and a register/verify service with *simulated* notarization. It implements a legacy v1 (120-bit) and current v2 (128-bit) payload (the latter fixing a coordinate-packing precision bug), validating the encode/verify round-trip and the metadata→seed→position determinism end-to-end before silicon.

**Proposed experiments.**
1. *Imperceptibility (G6):* PSNR/SSIM of embedded vs. nominal capture across `α ∈ [0.01, 0.05]` and carrier counts.
2. *Compression robustness:* BER and RS decode-success of V2 vs. JPEG `Q ∈ [50,100]` and vs. H.264/HEVC at varied QP/bitrate; report the safe "cannot verify" crossover.
3. *Latency (G5):* shutter→hash and hash→on-chain confirmation on testnets, including offline-queue behavior.
4. *Security:* empirical false-accept under deepfake substitution, metadata forgery, re-capture, and a simulated PRNU-copy attack; confirm zero false-accepts (fail-safe).
5. *Capacity/ECC trade-off:* payload size vs. parity vs. robustness.
6. *Baselines:* vs. metadata-only C2PA (manifest stripped) and software upload-time hashing, on survival of metadata removal and transcode.

---

## 10. Discussion: Limitations, Privacy, Standardization

- **Hardware dependency.** Strongest guarantees need sensor + secure-element support; legacy devices can run a software-only attested variant that still notarizes a capture-time hash (à la C2PA/ProofMode) without the hardware-rooted in-pixel binding.
- **Privacy.** `ID`, time, and location can be PII. We recommend on-chain pseudonyms, optional/omittable and salted location, and selective disclosure, so the public record proves *existence and integrity* without revealing the photographer's identity or precise whereabouts.
- **Failure-safe semantics.** PixelRoot declines rather than falsely certifies under heavy laundering; downstream policy must treat "unverified" as "unknown," not "fake."
- **Toward an OEM standard.** The lesson of JPEG [Wallace 1992] and 3GPP is that interoperability comes from a shared standard, not point products. We propose PixelRoot as a cross-OEM capture-provenance profile that (a) fixes payload layout, ECC, and the keyed selection function; (b) reuses C2PA manifests to transport assertions; and (c) standardizes the notarization contract interface, so any platform can verify any vendor's media. Consumer hardware-backed C2PA signing [Google 2025; Truepic 2024] shows the ecosystem is ready for the signing half; PixelRoot adds the in-pixel, ledger-witnessed half.

---

## 11. Conclusion and Future Work

Reactive deepfake detection cannot win a generator-vs-detector arms race, and metadata-only provenance breaks the moment a credential is stripped. PixelRoot relocates the root of trust into the pixels and onto a public ledger: a hardware-anchored, error-corrected, keyed signature embedded by the CMOS sensor at capture, plus a real-time blockchain commitment. This dual binding gives affirmative, publicly verifiable, hardware-rooted proof of authenticity that survives metadata loss and fails safe under laundering. Future work: silicon-level validation on sensors with per-region gain control, codec-aware learned embedding for video [CSTFMark 2026], privacy-preserving selective disclosure, formal modeling of the V2 soft-authenticity score, and pursuing PixelRoot as an open cross-OEM standard. We view this as a foundational — if not all-encompassing — step toward driving deepfake-driven disinformation toward practical irrelevance for media that matters.

**Reproducibility & disclosure.** The reference implementation is part of the open PixelRoot project. On-chain notarization in the current prototype is *simulated* and labeled as such; results reported as "planned" are part of the evaluation roadmap (§9).

---

## References

See `references.bib` for full BibTeX entries. Key sources:

1. L. Verdoliva, "Media Forensics and DeepFakes: An Overview," *IEEE J. Sel. Topics Signal Process.*, 2020.
2. Y. Mirsky, W. Lee, "The Creation and Detection of Deepfakes: A Survey," *ACM Comput. Surv.*, 2021.
3. F.-A. Croitoru et al., "Deepfake Media Generation and Detection in the Generative AI Era: A Survey and Outlook," arXiv:2411.19537, 2024.
4. N. A. Chandra et al., "Deepfake-Eval-2024," arXiv:2503.02857, 2025.
5. "The Tug-of-War Between Deepfake Generation and Detection," arXiv:2407.06174, 2024.
6. A. Kaur et al., "Deepfake Video Detection: Challenges and Opportunities," *Artif. Intell. Rev.*, 2024.
7. Resemble AI, "The 2025 Deepfake Threat Report," 2025.
8. Surfshark Research, "Deepfake-Related Fraud Losses by Social Media Platform, 2025."
9. IRONSCALES, "Beyond Detection: The Reality of Deepfake Attacks," Fall 2025.
10. J. Lukáš, J. Fridrich, M. Goljan, "Digital Camera Identification From Sensor Pattern Noise," *IEEE TIFS*, 2006.
11. M. Chen, J. Fridrich, M. Goljan, J. Lukáš, "Determining Image Origin and Integrity Using Sensor Noise," *IEEE TIFS*, 2008.
12. M. Goljan, J. Fridrich, M. Chen, "Defending Against Fingerprint-Copy Attack in Sensor-Based Camera Identification," *IEEE TIFS*, 2011.
13. PRNU-Bench, arXiv:2509.17581, 2025.
14. P. Korus, "Digital Image Integrity — A Survey," *Digital Signal Processing*, 2017.
15. A. Piva, "An Overview on Image Forensics," *ISRN Signal Processing*, 2013.
16. M. Begum, M. S. Uddin, "Digital Image Watermarking Techniques: A Review," *Information*, 2020.
17. "Deep Learning for Image Watermarking: A Comprehensive Review," *Sensors*, 2026.
18. "A Robust Fragile Watermarking Approach … Hybrid Transforms," *Scientific Reports*, 2025.
19. M. Asikuzzaman, M. R. Pickering, "A Survey on Robust Video Watermarking Algorithms," *Applied Sciences*, 2018.
20. Y. Tew, K. Wong, "HEVC Watermarking Techniques … Challenges and Opportunities," *IEEE Access*, 2020.
21. "CSTFMark: Robust Video Watermarking Against H.264/AVC …," *J. King Saud Univ. CIS*, 2026.
22. C2PA, "Technical Specification (Content Credentials), v2.x," 2024.
23. Google, "Pixel and Android … C2PA Content Credentials," 2025.
24. Truepic, "Controlled Capture and the Lens SDK," 2024.
25. Starling Lab & Guardian Project, "ProofMode," 2023.
26. S. Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System," 2008.
27. G. Wood, "Ethereum Yellow Paper," 2014.
28. J. Benet, "IPFS — Content Addressed, Versioned, P2P File System," arXiv:1407.3561, 2014.
29. H. R. Hasan, K. Salah, "Combating Deepfake Videos Using Blockchain and Smart Contracts," *IEEE Access*, 2019.
30. A. Qureshi, D. Megías, "Blockchain-Based Multimedia Content Protection: Review and Open Challenges," *Applied Sciences*, 2021.
31. "Blockchain for Video Watermarking … Perceptual Hash Function," *PLOS ONE*, 2024.
32. "Decentralizing Video Copyright Protection …," *Frontiers in AI*, 2025.
33. G. K. Wallace, "The JPEG Still Picture Compression Standard," *IEEE Trans. Consumer Electron.*, 1992.
34. T. Wiegand et al., "Overview of the H.264/AVC Video Coding Standard," *IEEE TCSVT*, 2003.
35. G. J. Sullivan et al., "Overview of the HEVC Standard," *IEEE TCSVT*, 2012.
36. I. S. Reed, G. Solomon, "Polynomial Codes Over Certain Finite Fields," *J. SIAM*, 1960.
37. R. C. Merkle, "A Digital Signature Based on a Conventional Encryption Function," *CRYPTO '87*.
38. NIST, "FIPS PUB 180-4: Secure Hash Standard," 2015.
39. Trusted Computing Group, "TPM 2.0 Library Specification," 2019.
