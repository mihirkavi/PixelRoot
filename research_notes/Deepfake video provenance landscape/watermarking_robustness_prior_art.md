# Invisible Watermarking for Images/Video: Robustness, Attacks, and Sensor-Level Prior Art

Research note scope: production watermarks and their robustness, the strongest attacks, video-specific problems, prior art for in-camera/sensor watermarking (to judge PixelRoot's novelty), and perceptual hashing as an alternative soft binding. Research date: 2026-10-18.

Method caveat: in this session, direct page fetches of arxiv.org, patents.google.com and USPTO failed with DNS errors, so most findings below come from search-result summaries of primary pages: arXiv abstracts, proceedings pages, vendor docs and patent texts. Where a number appears only in a secondary source, these notes say so. Exact table values should be checked against the PDFs before publication.

---

## 1. State of the art production watermarks and published robustness (esp. video)

### Takeaway
Production watermarks (SynthID, Video Seal/Pixel Seal, TrustMark) handle everyday edits such as JPEG, moderate crops and brightness changes well. Video watermarks lose much of their accuracy under strong H.264/HEVC compression. One third-party benchmark found Video Seal falls to chance-level bit accuracy at H.264 CRF 45. No vendor I found publishes robustness numbers for screen re-recording or social-platform transcoding. Google's verification service is closed to the public, so SynthID cannot be checked independently by outsiders.

### Cited Findings
- **SynthID-Image (Google DeepMind, arXiv 2510.09263, Oct 2025, Gowal et al.)**
  - The paper covers requirements, threat models and deployment for watermarking at internet scale, with goals of effectiveness, fidelity, robustness and security. — [arXiv 2510.09263](https://arxiv.org/abs/2510.09263)
  - It has been applied to more than 10 billion images and video frames.
  - The verification service is limited to trusted testers.
  - The paper benchmarks an external variant, SynthID-O (available through partnerships), against other post-hoc methods and reports state-of-the-art quality and robustness to common perturbations. — [arXiv 2510.09263](https://arxiv.org/abs/2510.09263)
  - The paper's own threat model has two attacker goals: removal (a false negative) and forgery (a false positive). It notes that paired original and watermarked content "significantly simplifies attacks, especially for post-hoc systems like SynthID-Image." — [arXiv PDF 2510.09263](https://arxiv.org/pdf/2510.09263)
  - Google's comparison ran TrustMark without error correction (100 bits per 256×256). — [arXiv PDF 2510.09263](https://arxiv.org/pdf/2510.09263)
- **SynthID Detector (May 20, 2025, I/O)**
  - It is a portal: users upload text, image, audio or video, and it checks for SynthID and highlights the likely-watermarked parts.
  - Google reported more than 10 billion watermarked items at launch.
  - It only detects Google's SynthID, not other vendors' marks. — [Google blog](https://blog.google/innovation-and-ai/products/google-synthid-ai-content-detector/); [Neowin](https://www.neowin.net/news/google-announces-synthid-detector-that-identifies-ai-generated-content/)
- **SynthID Text** was open-sourced in October 2024 as a logits processor. Gemini's production keys are not public. — [Google AI for Developers](https://ai.google.dev/responsible/docs/safeguards/synthid); [HPCwire](https://www.hpcwire.com/aiwire/2024/10/29/google-deepmind-open-sources-its-ai-text-watermarking-tool/)
- **Meta Video Seal (arXiv 2412.09492, Dec 2024)**
  - It is an open-source neural video watermark.
  - Meta's announcement claims robustness to compression, cropping and brightness changes, and says it beats baselines "especially under challenging distortions combining geometric transformations and video compression." — [Maginative](https://www.maginative.com/article/meta-releases-video-seal-an-open-source-watermarking-tool-for-ai-video/); [arXiv 2412.09492](https://arxiv.org/pdf/2412.09492)
- **Independent H.264 numbers for Video Seal (COVER paper, arXiv 2609.26236)**
  - Bit accuracy under H.264 was about 94.2% at CRF 23, 62.1% at CRF 35 and 50.5% at CRF 45 (chance).
  - The average across 12 codec settings was 67.1%. — [COVER, arXiv 2609.26236](https://arxiv.org/pdf/2609.26236)
- **Meta Pixel Seal (arXiv 2512.16874, Dec 2025)** is Meta's follow-up. It says "compression algorithms such as H.264 and HEVC present a significantly greater challenge, resulting in lower bit recovery rates across all methods" than geometric or value attacks, and claims it still outperforms prior methods. — [Pixel Seal, arXiv 2512.16874](https://arxiv.org/pdf/2512.16874)
- **Adobe TrustMark (arXiv 2311.18297, open source)**
  - Payload is 100 bits. The default is variant Q with BCH_5, which protects 61 data bits with 35 ECC bits and corrects 5 bit flips. BCH_SUPER protects 40 bits and corrects 8 flips. — [TrustMark config docs](https://opensource.contentauthenticity.org/docs/trustmark/python/config)
  - The FAQ claims Q reaches >96% bit accuracy at about 42–45 dB PSNR under severe noise, and P reaches about 95% at 48–50 dB. — [TrustMark FAQ](https://raw.githubusercontent.com/adobe/trustmark/main/FAQ.md)
  - The FAQ contradicts the config docs, citing about 70 protected bits and 4 flips. — [TrustMark FAQ](https://opensource.contentauthenticity.org/docs/tm-faq)
  - TrustMark is the watermark C2PA uses for "durable content credentials" (watermark plus manifest lookup). — [CAI durable CR docs](https://opensource.contentauthenticity.org/docs/durable-cr/tm-faq)
- **Camera-side provenance today is signatures, not watermarks.**
  - Sony's Camera Authenticity Solution signs images in camera, with keys held in the hardware chipset. It adds C2PA format support (Alpha 1, 7S III, 7 IV, 9 III) plus 3D depth data, because "a digital signature alone cannot determine whether the captured image is of an actual 3D subject." — [Amateur Photographer](https://amateurphotographer.com/latest/photo-news/sony-announces-new-in-camera-authenticity-technology); [Photography News](https://www.photographynews.co.uk/?p=63806)
  - The Camera Verify beta followed in June 2025. — [Newsshooter](https://www.newsshooter.com/2025/06/25/sony-releases-beta-version-of-camera-verify/)

### Inferences
- The COVER numbers suggest that neural video marks trained around moderate CRF do not survive aggressive platform re-encoding. A low-frequency DCT spread-spectrum design (PixelRoot) aims at exactly the band H.264 keeps (low frequencies survive quantization). This is a reasonable design rationale, but it has to be shown on the same CRF sweep (e.g., CRF 23/35/45, plus HEVC/AV1/VP9) to be comparable.
- Sony's choice of signature plus depth, rather than a watermark, shows that the camera industry treats in-pixel marks as unproven. A PixelRoot-style sensor watermark would complement C2PA as a soft binding rather than compete with it.

### Gaps
- I could not retrieve Video Seal's own H.264/HEVC tables or SynthID's per-attack video numbers (the arXiv fetch failed).
- I found no public robustness figures from Digimarc, Steg.AI or IMATAG for video transcoding or screen recording. Vendor claims are mostly marketing, and I found no independent evaluations of them.
- No source quantified survival through specific social platforms' pipelines (TikTok, YouTube, WhatsApp) for any of these marks.

---

## 2. Strongest attacks: removal, forgery/copy, averaging/collusion, spoofing, impossibility results

### Takeaway
Low-perturbation (pixel-level) watermarks can be removed by diffusion or VAE regeneration with little quality loss. There are proofs (Zhao et al.) and theory showing a fundamental miss/false-alarm trade-off (Saberi et al.). Practical universal attacks exist too: UnMarker (IEEE S&P 2025), and MarkNull reports 100% removal success against SynthID-Image for several attacks. Content-agnostic, fixed-pattern marks are additionally exposed to averaging attacks (Yang et al., NeurIPS 2024), which recover the carrier and enable both removal and forgery. This is the classic estimation/copy-attack failure (Kutter et al. 2000).

### Cited Findings
- **Regeneration removal (Zhao et al., NeurIPS 2024, "Invisible Image Watermarks Are Provably Removable Using Generative AI")**
  - The attack adds noise, then reconstructs the image with a denoiser or diffusion model.
  - The authors give formal proofs and experiments showing pixel-level watermarks are removable (four schemes tested), with better quality than earlier attacks.
  - They recommend semantic watermarks.
  - The early arXiv draft claimed all invisible watermarks; the NeurIPS version narrows the claim to pixel-level schemes. — [NeurIPS 2024 proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/10272bfd0371ef960ec557ed6c866058-Abstract.html); [arXiv 2306.01953](https://arxiv.org/html/2306.01953v3)
- **Saberi et al. (ICLR 2024)**
  - For low-perturbation watermarks, diffusion purification creates a fundamental trade-off between missed detections and false alarms.
  - For high-perturbation marks, a model-substitution adversarial attack removes them.
  - **Spoofing:** with only black-box access, an attacker can craft a "watermarked noise image" that, added to real images, makes them falsely flagged as watermarked.
  - The paper also proves a robustness/reliability trade-off for deepfake classifiers. — [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/744e09d3213ee53de88f04164a9b06ab-Abstract-Conference.html); [OpenReview PDF](https://openreview.net/pdf/c27ed3d4b062895eb6037f109a8345e569bab7f9.pdf)
- **WAVES benchmark (ICML 2024, arXiv 2401.08573)**
  - It reports TPR@0.1%FPR under classical distortions, regeneration (single diffusion/VAE plus multi-step "rinsing") and adversarial attacks. — [WAVES](https://arxiv.org/html/2401.08573v3)
  - Per summaries: Stable Signature is highly vulnerable to regeneration, and Tree-Ring is vulnerable to grey-box embedding and surrogate-detector adversarial attacks. — [Liner review](https://liner.com/review/benchmarking-robustness-image-watermarks)
  - An independent 2024 reproduction found that single regeneration and rinsing drove Stable Signature TPR@0.1%FPR to 0.000. — [arXiv 2412.12511](https://arxiv.org/pdf/2412.12511)
- **UnMarker (Kassis & Hengartner, IEEE S&P 2025, DOI 10.1109/SP61157.2025.00005)**
  - It is presented as the first practical universal attack on defensive watermarking. It needs no detector feedback and no knowledge of the scheme.
  - Against non-semantic marks it disrupts high-frequency spectral amplitudes. Against semantic marks it uses learned filters to create low-frequency inconsistencies.
  - It cuts the best detection rate against semantic watermarks to 43%. — [arXiv 2405.08363](https://arxiv.org/html/2405.08363v2)
  - It needs an A100 40GB, and some outputs show "slightly visible changes."
  - Google DeepMind disputed the reported SynthID removal rate. — [IEEE Spectrum](https://spectrum.ieee.org/ai-watermark-remover)
  - A secondary source gives a 79% SynthID removal figure and mislabels the venue as USENIX Security; treat it as unverified. — [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/909/reverse-synthid-broken-google-ai-watermark-spectral-analysis)
  - A 2026 follow-up argues that removal leaves its own forensic traces, so "removal success" benchmarks are incomplete. — [HF papers 2605.09203](https://huggingface.co/papers/2605.09203.md)
- **MarkNull (arXiv 2608.10166, 2026)**
  - It reports that SynthID-Image resists simple attacks but fails catastrophically against advanced ones, with 100% attack success for several baselines (Imprint, UnMarker, DA).
  - It attributes the failure to post-hoc embedding being weak against latent-space manipulation. — [MarkNull](https://arxiv.org/pdf/2608.10166)
- **Reverse-SynthID (community GitHub project, 2025–26)**
  - It claims spectral analysis, with no neural model, can detect and remove the SynthID pattern from Gemini images, with about 91% "watermark energy" removal.
  - This is unreviewed and unverified. — [pasqualepillitteri.it write-up](https://pasqualepillitteri.it/en/news/909/reverse-synthid-broken-google-ai-watermark-spectral-analysis); [repo index](https://docsearch.algolia.com/mcp/docs/repo/aloshdenny/reverse-synthid)
- **Averaging attack (Yang et al., NeurIPS 2024, "Can Simple Averaging Defeat Modern Watermarks?")**
  - Averaging many watermarked images reveals the underlying pattern, which can then be used for removal or forgery. It works grey-box and black-box, even when several patterns are mixed.
  - Content-agnostic fixed-pattern schemes are the most vulnerable.
  - For Tree-Ring, the extracted pattern can forge convincing marks on clean images.
  - Proposed mitigations are content-adaptive embedding, steganalysis-aware evaluation and multi-key assignment. — [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/67b2e2e895380fa6acd537c2894e490e-Abstract.html); [arXiv 2406.09026](https://arxiv.org/html/2406.09026v1)
  - Follow-up schemes evaluate with up to 5,000 averaged images. — [MOLM arXiv 2510.00293](https://arxiv.org/pdf/2510.00293)
  - CLUE-MARK (lattice/CLWE-based) survives the attack, whereas Tree-Ring and Gaussian Shading do not. — [CLUE-MARK arXiv 2411.11434](https://arxiv.org/pdf/2411.11434)
  - Older patents propose shifting or rotating templates randomly per image so they cancel under averaging. — [USPTO 7702125](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7702125)
  - A 2026 multi-screen collusion paper subtracts averaged residuals from captured images. — [arXiv 2607.23553](https://arxiv.org/pdf/2607.23553)
- **Copy attack (Kutter, Voloshynovskiy & Herrigel, SPIE EI 2000)**
  - The attacker estimates the watermark by spatial denoising/filtering, adapts it, and adds it to a different image. No algorithm or key knowledge is needed. It was effective against commercial schemes.
  - The defense is to bind the payload to the image content (Barr, Bradley & Hannigan, Digimarc, ICASSP 2003). — [Wikipedia: Copy attack](https://en.wikipedia.org/wiki/Copy_attack); [UNIGE archive](https://archive-ouverte.unige.ch/unige:47812)
- **Analogous attack on sensor fingerprints (PRNU fingerprint-copy)**
  - The attacker estimates a victim camera's PRNU from public photos and adds it to a foreign image so it passes the correlation test.
  - Goljan, Fridrich & Chen proposed the "triangle test" to detect this.
  - Improved block-wise attacks significantly degrade the triangle test (Li et al., arXiv 1707.07795). — [arXiv 1707.07795](https://ar5iv.labs.arxiv.org/html/1707.07795); [Barni et al. arXiv 1805.02899](https://arxiv.org/pdf/1805.02899); [arXiv 1907.04025](https://arxiv.org/pdf/1907.04025)
- **Text watermark spoofing:** DITTO (arXiv 2510.10987) reports effective spoofing of SynthID-Text via knowledge distillation. — [DITTO](https://arxiv.org/pdf/2510.10987)

### Inferences (directly relevant to PixelRoot's design)
- **A fixed, keyed, content-agnostic carrier is the textbook averaging/copy-attack target.** PixelRoot's carrier is antipodal keyed chips on a fixed low-frequency DCT basis per 8×8 block, applied as a sensor gain pattern. If the chip sequence and layout are the same for every frame from a device (or every device), then averaging frames (very easy in video: one clip has thousands of frames) estimates the carrier. That enables:
  - removal: subtract it;
  - forgery: add it to deepfake frames, so a fake inherits "captured by sensor X." This is worse for a provenance system than removal, because it creates false authenticity.
  - Mitigations from the literature are:
    - per-frame key rotation or keyed per-frame permutation/shifts (so the pattern cancels under averaging);
    - content binding (payload derived from a hash of robust frame content, per Barr et al. 2003);
    - cryptographic coupling to a C2PA signature, so the watermark is only a lookup key and never proof by itself.
- **A multiplicative gain watermark behaves like PRNU.** Per-column or per-region gain modulation is physically the same kind of signal as PRNU or column fixed-pattern noise: a multiplicative K·I term. The PRNU fingerprint-copy literature therefore transfers directly. An attacker with public footage from a device can estimate the gain pattern the same way PRNU is estimated, and paste it. The triangle-test-style defenses and their known weaknesses apply too.
- **Regeneration attacks will likely remove a low-amplitude mark.** Zhao et al.'s proof covers marks with bounded pixel perturbation, so diffusion regeneration is expected to remove a low-amplitude sensor mark. For a capture-provenance system, though, removal only gives a false negative ("unverified"). That is the expected failure mode for any soft binding, and it is less dangerous than spoofing. PixelRoot's claims should be framed as "presence implies a likely genuine capture; absence implies nothing."

### Gaps
- No source evaluated a sensor-gain or PRNU-like multiplicative watermark against WAVES-style regeneration specifically.
- Saberi's spoofing result was shown for learned watermarks. I found no direct evaluation of their black-box spoofing against a classic keyed spread-spectrum DCT mark, though the copy attack (2000) covers that case conceptually.

---

## 3. Video-specific challenges (temporal drift, frame dropping, screen re-recording, platform transcoding)

### Takeaway
Codec compression is the dominant failure mode for current neural video marks (Pixel Seal and COVER both say so). Camcorder or screen recapture is a compound geometric-plus-photometric attack that remains largely unsolved at good visual quality. Frame-rate changes and frame blending break per-frame synchronization unless the payload is repeated per frame or per short window.

### Cited Findings
- H.264/HEVC give lower bit recovery than geometric or valuemetric attacks for all methods tested (Meta, Pixel Seal). — [arXiv 2512.16874](https://arxiv.org/pdf/2512.16874)
- In the COVER benchmark, Video Seal's H.264 bit accuracy fell from 94.2% at CRF 23 to 50.5% at CRF 45. — [arXiv 2609.26236](https://arxiv.org/pdf/2609.26236)
- Camcorder recapture combines rotation, translation, scaling, moiré and lighting change. Spreading the mark over many frequency coefficients helps it survive sensor noise. — [arXiv 2209.13206](https://arxiv.org/pdf/2209.13206)
- The CamMark benchmark simulates recapture with perspective and lens distortion, unsynchronized frame rates with frame blending, rescaling, and auto gain/white balance. — [CamMark, Univ. Mannheim](https://madoc.bib.uni-mannheim.de/38490/)
- Real cinema camcorder datasets evaluate better than simulators. — [SciTePress 2018](https://www.scitepress.org/papers/2018/66172/66172.pdf)
- Screen-shooting robustness at high visual quality is described as still unsolved in a 2026 preprint (moiré, gamut shift, perspective warp). — [arXiv 2603.26766](https://arxiv.org/pdf/2603.26766)
- Newer 2026 video watermark preprints target codec robustness explicitly: COVER (generative video priors) and Asymmetric Phase Coding. — [COVER](https://arxiv.org/pdf/2609.26236); [arXiv 2608.29212](https://arxiv.org/pdf/2608.29212)

### Inferences
- A sensor-level mark gets one property for free: it is present in every captured frame, so frame dropping, trimming and frame-rate conversion only lose redundancy, not sync. That holds as long as each frame (or a short window) carries the full RS-coded payload.
  - The risk is the opposite one: identical per-frame carriers maximize averaging-attack exposure (section 2).
  - Temporal frame blending (frame-rate conversion) also averages adjacent frames' carriers. That is harmless if the carriers are identical, and destructive if they are rotated per frame. There is a design tension between collusion resistance and robustness to frame-rate conversion.
- **Screen re-recording:** a capture-time mark identifies the camera that captured the screen, not the original source. In a provenance framing, a phone filming a deepfake on a monitor will itself produce a "genuine capture" mark. This is the "analog hole" / re-photography attack, which signature-based C2PA also suffers from. Sony addresses it with depth data. PixelRoot needs a stated answer, e.g., depth, moiré or flat-scene detection.
- **Geometric sync:** a block-aligned 8×8 DCT carrier assumes the 8×8 grid is preserved. Cropping by a non-multiple of 8 or rescaling (platform downscale from 4K to 1080p/720p) shifts the grid, so the detector needs a sync/registration search or a template. This is a known weakness of block-DCT schemes.

### Gaps
- I found no peer-reviewed study measuring watermark survival through actual TikTok, Instagram, YouTube or WhatsApp pipelines in 2024–2026. This is an empirical gap PixelRoot could fill.
- Temporal-drift metrics for neural video watermarks (e.g., flicker) were not retrieved.

---

## 4. Prior art: in-camera / sensor-level / image-sensor watermarking

### Takeaway
Sensor-level watermarking is not new as a concept. Digimarc holds a patent family titled "Digital watermarking CMOS sensor" (US7688994, US8280098), plus "Digital watermarking image signals on-chip" (US8457346) and "Noise influenced watermarking" (US8565473). These explicitly claim introducing the watermark during capture by "providing slight variations to physical characteristics of a set of the plurality of pixels." Academic work includes VLSI/CMOS watermarking chips (Mohanty et al., ~0.35 µm chip; Toronto's JAWS-in-VLSI), the Blythe & Fridrich "Secure Digital Camera" (DFRWS 2004), and recent in-sensor PUF authentication. PixelRoot's possible novelty is narrow: the specific combination of an RS-coded keyed antipodal spread-spectrum payload on a low-frequency DCT basis, realized through per-column/per-region analog gain, built for robustness through modern codecs and tied to provenance. A claim of "first sensor-level watermark" would be contradicted by prior art.

### Cited Findings
- **Digimarc "Digital watermarking CMOS sensor" (US7688994; also US8280098)**
  - Watermark embedding circuits sit on the same silicon as the sensor array, or on a separate chip fed by the sensor; embedding is "preferably integrated on-chip."
  - Co-locating the circuits with the sensor "allows for generation of the watermark based on characteristics inherent to variations in the physical sensor," which "may allow for unique identification of specific sensors." — [Google Patents US7688994](https://patents.google.com/patent/US7688994); [USPTO 7688994](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7688994); [USPTO 8280098](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8280098)
- **Same patent family, physical-variation claim:** a method "providing slight variations to physical characteristics of a set of the plurality of pixels … so as to introduce the digital watermark component during image capture." — [USPTO 7688994 / family search results](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7688994)
- **"Digital watermarking image signals on-chip" (US8457346)** and the related "Methods involving maps, imagery, video and steganography" family (US8023691, US8976998, US9792661)
  - They describe embedding a fixed watermark component at the pixel level during capture.
  - A detector checks the component to verify sensor integrity. — [USPTO 8457346](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8457346); [USPTO 9792661](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9792661)
- **"Noise influenced watermarking methods and apparatus" (US8565473)** — [USPTO 8565473](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8565473)
- **A related patent describes a watermarking chip** with a DCT circuit, quantizer, watermark generator and embedder operating on sensor output. Its background cites:
  - the University of Toronto port of the JAWS video watermark algorithm to VLSI for real-time embedding;
  - Mohanty et al.'s 0.35 µm CMOS watermarking chip, with a 2004 follow-on built into a digital still camera architecture.
  - (These are citations as summarized by the search tool, not read first-hand.) — [Google Patents US7688994 citations](https://patents.google.com/patent/US7688994); [USPTO 7616777 "Digital watermarking methods, systems and apparatus"](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7616777)
- **Blythe & Fridrich, "Secure Digital Camera," DFRWS 2004**
  - The camera embeds, losslessly (reversibly), data identifying the photographer (an iris biometric captured simultaneously), the camera and the time, and verifies integrity, for chain of custody in court. — [DFRWS](https://dfrws.org/presentation/secure-digital-camera/); [Binghamton news](https://discovere.binghamton.edu/news/securing-digital-imagery-from-fakery-572.html)
- **In-sensor PUF (NDSS VehicleSec 2024 poster)**
  - An in-sensor physical unclonable function uses each pixel's capacitive-well self-discharge behavior, for sensor sourcing and image authentication. Images are verified against a tag and the sensor ID. — [NDSS VehicleSec 2024 poster](https://www.ndss-symposium.org/wp-content/uploads/vehiclesec2024-10-poster.pdf)
- **PRNU camera identification (Lukáš, Fridrich & Goljan)** is the classic passive sensor fingerprint. It is a multiplicative pixel-gain non-uniformity, so it is structurally analogous to a deliberate gain-modulated watermark. It is forgeable via fingerprint-copy (section 2). — [ResearchGate: Digital Camera Identification From Sensor Pattern Noise](https://www.researchgate.net/publication/3455253_Digital_Camera_Identification_From_Sensor_Pattern_Noise); [arXiv 1707.07795](https://ar5iv.labs.arxiv.org/html/1707.07795)
- **Shipping camera provenance (Sony)** uses a hardware-key in-camera signature plus C2PA and depth, not a pixel watermark. — [Amateur Photographer](https://amateurphotographer.com/latest/photo-news/sony-announces-new-in-camera-authenticity-technology)

### Inferences (novelty assessment for PixelRoot)
- **Prior art clearly covers:**
  1. embedding a watermark at or in the image sensor during capture (Digimarc family);
  2. doing so by varying physical pixel characteristics (Digimarc claim language), which overlaps conceptually with gain modulation;
  3. DCT-domain embedding in on-chip hardware (watermarking-chip patent, Mohanty);
  4. sensor-unique marks (Digimarc, PRNU, PUF);
  5. keyed spread-spectrum DCT watermarking with antipodal chips and ECC in general. Cox et al. 1997 spread-spectrum and Hartung & Girod 1998 video spread-spectrum are foundational, but I did not verify them via sources in this session; see Gaps.
- **Possibly novel (needs a claim-level check):**
  - using the existing per-column/per-region programmable analog/digital gain stage (already present in CMOS image sensors for column FPN correction) as the embedding actuator;
  - the particular payload layout (low-frequency DCT basis per 8×8 block, keyed antipodal chips, RS code) tuned to survive H.264/HEVC;
  - binding it to a C2PA-style provenance chain for deepfake defense.
  - The novelty argument is strongest as "a practical, codec-robust realization of an old idea using existing sensor hardware, with a security analysis," not as a new concept.
- **Patent status:** the Digimarc CMOS-sensor family likely stems from ~2000–2001 priority filings. If so, the base patents would have expired (20-year term) and would be prior art, not live blockers. The dates and expiry were NOT verified here (the patent pages were not fetchable), so this is unverified.

### Gaps
- I could not open the full patent texts to confirm priority dates, assignee, claims about gain/amplifier modulation, or legal status. Recommend a manual Google Patents check of US7688994, US8280098, US8457346 and US8565473, plus a forward-citation search.
- I did not find Sony or Samsung patents on sensor-level watermarking specifically. Samsung's provenance features did not appear in results.
- I found no 2023–2026 peer-reviewed paper on in-sensor robust watermarking for provenance, which is weak evidence of a recent-literature gap.
- Foundational spread-spectrum references (Cox, Kilian, Leighton & Shamoon 1997; Hartung & Girod 1998) are not cited above because I did not retrieve them in this session. They should be cited in the paper.

---

## 5. Perceptual hashing / fingerprinting as alternative soft bindings

### Takeaway
Perceptual hashes (PDQ, TMK+PDQF, NeuralHash, PhotoDNA) need no embedding, so they cannot be "removed." They are, by design, not collision-resistant. NeuralHash second-preimage collisions appeared within 48 hours of its 2021 extraction. A 2026 USENIX paper gives black-box exact collisions in NeuralHash and lower-threshold near-collisions in PhotoDNA. As a soft binding, a hash is only safe as a lookup key into a signed manifest, never as proof.

### Cited Findings
- NeuralHash was extracted by GitHub user AsuharietYgvar in August 2021. Apple said that version was not the final one. — [The Register](https://www.theregister.com/2021/08/18/apples_csam_hashing/)
- "Within 48 hours" multiple second-preimage collisions were created. Intel's Cory Cornelius made a beagle collide with a gray square. — [Bugs in our Pockets, arXiv 2110.07450](https://arxiv.org/pdf/2110.07450)
- Perceptual hashes are designed not to be second-preimage resistant (Jonathan Mayer). — [Educated Guesswork](https://educatedguesswork.org/posts/perceptual-hash/); [mjtsai](https://mjtsai.com/blog/2021/08/18/)
- Roboflow found 2 natural collisions between semantically different ImageNet images. — [Roboflow](https://blog.roboflow.com/neuralhash-collision/)
- Leblanc-Albarel & Preneel (USENIX Security 2026) produced black-box exact NeuralHash collisions and PhotoDNA near-collisions at lower thresholds than previously reported. — [USENIX Sec '26](https://www.usenix.org/conference/usenixsecurity26/presentation/leblanc-albarel); [IACR ePrint 2024/1869](https://eprint.iacr.org/2024/1869)
- C2PA's "durable content credentials" combine watermark (TrustMark) and/or fingerprint lookup to recover stripped manifests. — [CAI docs](https://opensource.contentauthenticity.org/docs/durable-cr/tm-faq)

### Inferences
- Hashing and watermarking fail in opposite ways:
  - hashes resist removal but are easy to collide or forge;
  - fixed-carrier watermarks are easy to average and copy.
- A layered design is the defensible position: signature (C2PA), plus watermark as a recovery key, plus fingerprint match against a registry. That design accepts that each soft binding alone is attackable.

### Gaps
- I found no published attack specifically on Meta's PDQ or TMK+PDQF in this search, though PDQ is believed to share the generic perceptual-hash weakness. This needs a targeted search.
- I found no data on perceptual video hash robustness to deepfake face swaps (whether a face-swapped clip still matches the original's hash, which would cause false provenance).
