# C2PA / Content Credentials and Capture-Time Hardware Signing (state as of Oct 2026, video focus)

Method note: built from web search results. WebFetch could not resolve the primary domains (spec.c2pa.org, arxiv.org, washingtonpost.com, security.googleblog.com), so primary documents were not read in full. Many platform and device claims come from search snippets of secondary or vendor blogs. Treat those as provisional; they are marked.

## 1. C2PA spec version and features (hard/soft bindings, video/live, trust list, conformance). What changed in 2025–2026?

### Takeaway
The spec moved quickly: 2.1 (2024) standardized watermark declarations, 2.2 (May 2025) added soft-binding resolution and recovery, 2.3 (Dec 2025) added live-stream signing over DASH/HLS, and 2.4 is listed (reportedly Apr 2026). Governance also changed. A Conformance Program with assurance levels and an official Trust List launched in mid/late 2025, and the Interim Trust List was frozen on 1 Jan 2026.

### Cited Findings
- Spec 2.2 is dated 2025-05-01. Its version history lists the Soft Binding Resolution API supplementary specs, new ingredient-assertion fields for recovering manifests via soft bindings, multi-part asset support, and improved soft-binding assertions. Live video is not in 2.2 — [C2PA Spec 2.2 PDF](https://spec.c2pa.org/specifications/specifications/2.2/specs/_attachments/C2PA_Specification.pdf); [C2PA spec 2.4 HTML (version history)](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html), via search snippet
- Spec 2.3 (Dec 2025) adds live video streaming support, extends live-stream temporal ranges to allow undefined end times, adds validation procedures for soft bindings, and clarifies BMFF (MP4) hashing — [C2PA spec version history](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html), via search snippet
- Irdeto says 2.3 defines how to sign live and broadcast media delivered over DASH and HLS — [Irdeto](https://irdeto.com/blog/extending-trust-into-live-video-with-c2pa). The mechanism is described as signing each CMAF segment independently as it is produced, which keeps existing streaming infrastructure working — [5centscdn](https://www.5centscdn.net/blog/what-is-c2pa-content-provenance/) (vendor blog)
- Conflict: c2paviewer.com says 2.2 added streaming support. That contradicts the official version history, which places live streaming in 2.3 — [c2paviewer](https://c2paviewer.com/articles/c2pa-spec-versions-file-formats)
- Version 2.4 exists on the official spec site. A secondary timeline dates it to April 2026 — [ppc.land](https://ppc.land/c2pa/). Its contents were not verified.
- C2PA 2.1 added a standard way to declare a watermark and its algorithm, a registry of supported watermark technologies, and a Soft Binding Resolution API to retrieve manifests from a watermark or fingerprint. Digimarc co-chaired the watermarking task force — [Digimarc](https://digimarc.com/blog/c2pa-21-strengthening-content-credentials-digital-watermarks)
- "Durable Content Credentials" means three things together: a signed manifest (hard binding), an invisible watermark, and a fingerprint, so provenance can be recovered after metadata is stripped — [CAI: three pillars](https://contentauthenticity.org/blog/three-pillars-of-provenance); [CAI open-source docs](https://opensource.contentauthenticity.org/docs/durable-cr/)
- The official soft-binding algorithm list shows Digimarc's watermark covering audio, video, text and images, Adobe TrustMark variant Q covering images only, and ISCC fingerprinting covering video — [C2PA soft-binding algorithm list](https://spec.c2pa.org/softbinding-alg-list/softbinding-algorithm-list.json), via search snippet. TrustMark is MIT-licensed open source — [CAI TrustMark docs](https://opensource.contentauthenticity.org/docs/trustmark/c2pa/)
- Adobe and Digimarc demonstrated interoperable durable credentials: one browser extension detects both watermarks and retrieves the matching manifest — [CAI blog](https://contentauthenticity.org/blog/digital-watermarking-interoperable-durable-content-credentials) (2024-era material)
- The Conformance Program soft-launched on 4 June 2025, starting with self-assertion and two assurance levels — [Trust over IP EGWG talk by Scott Perry](https://www.trustoverip.org/blog/2025/05/20/egwg-2025-05-15-the-c2pa-conformance-program-scott-perry/). Full public launch was reportedly Oct 2025 — [Wikipedia: Content Credentials](https://en.wikipedia.org/wiki/Content_Credentials), via search snippet. A Nov 2025 slide deck lists "INITIAL (v.1.0) 2Q2026?", which suggests the program was still maturing — [LF Decentralized Trust ToIP Summit slides](https://www.lfdecentralizedtrust.org/hubfs/2025-11-19%20ToIP%20Summit%20-%20C2PA%20+%20CAWG.pptx.pdf?hsLang=en)
- The Interim Trust List (ITL), a list of CAs used by early implementations, was frozen on 1 Jan 2026 and replaced by the official C2PA Trust List. Content signed with an ITL certificate while it was valid stays valid under the legacy model. Conforming generator and validator products are listed publicly — [softwareseni](https://www.softwareseni.com/the-c2pa-trust-layer-in-2026-where-it-works-and-where-it-breaks) (secondary)
- DigiCert (Aug 2026) argues that conformant C2PA signing needs more than an SDK, because certificates must come from trust-list CAs and keys must be protected — [DigiCert](https://www.digicert.com/jp/blog/why-c2pa-signing-requires-more-than-an-sdk) (vendor, snippet only)

### Inferences
- For video, the spec now covers file-based MP4/BMFF hashing (with per-segment/fragment hashing) and live CMAF segment signing. The standards gap for live video has closed on paper. Deployment evidence for live-stream C2PA in production is thin; I found only vendor blogs.
- Soft bindings only work if a resolver service (a manifest repository) exists and is queried. Recovery after stripping therefore depends on someone running that infrastructure, which a new system would need to provide or plug into.
- Assurance levels (AL1/AL2) now separate "any signer on the trust list" from "hardware-backed, attested signer". That separation matters more than the bare fact that something is C2PA-signed.

### Gaps
- Could not read the 2.3/2.4 change logs directly; the exact 2.4 features and date are unverified.
- No independent data on how many validators (Adobe Verify, browser extensions) implement the 2.3 live-stream validation.
- No confirmed official date for the full public launch of the Conformance Program; the June 2025 soft launch is better sourced.

## 2. Which devices and platforms ship C2PA; which display or preserve it; how often is it stripped?

### Takeaway
Capture-time signing ships on a few pro cameras (Leica, Sony, Nikon Z6 III until it was suspended) and, at scale, on the Google Pixel 10 for photos. Video signing at capture ships mainly on Sony pro bodies for newsrooms. Samsung signs only AI-edited images, and Apple does not ship C2PA. Distribution is the weak point: in the Washington Post's Oct 2025 test, none of eight major platforms kept Content Credentials on an uploaded AI video, and only YouTube disclosed anything.

### Cited Findings
**Cameras and phones**
- Google Pixel 10 Pixel Camera reached C2PA Conformance Assurance Level 2, which Google calls the highest level currently defined. It uses Tensor G5, the certified Titan M2 chip and Android hardware-backed key attestation. Google says AL2 for a mobile app is currently possible only on Android — [Google Security Blog, Sep 2025](https://security.googleblog.com/2025/09/pixel-android-trusted-images-c2pa-content-credentials.html?hl=fr); [Google blog](https://blog.google/security/pixel-android-trusted-images-c2pa-content-credentials/)
- On Pixel 10, on-device trusted timestamps keep images verifiable after certificates expire, even for offline captures. Certificate handling is designed so images cannot be linked to each other or to the creator (unlinkable, one-time keys) — [The Hacker News](https://thehackernews.com/2025/09/google-pixel-10-adds-c2pa-support-to.html?hl=en). Coverage describes Pixel 10 as signing every photo by default — [lumethic](https://www.lumethic.com/en/articles/smartphones-c2pa-content-credentials) (secondary)
- Pixel 10 video signing: no source found confirming it. Coverage describes the feature as photo-focused — [attesttrail](https://attesttrail.com/blog/c2pa-cameras-support) (secondary)
- Samsung Galaxy S25 (Unpacked, 22 Jan 2025) applies Content Credentials to images edited with Galaxy AI tools (Generative Edit, Sketch to Image, Portrait Studio, Drawing Assist, AI Sticker). It does not sign ordinary captures — [TechCrunch](https://techcrunch.com/2025/01/22/samsung-unpacked-samsungs-galaxy-s25-will-support-content-credentials-to-identify-ai-generated-images); [c2paviewer](https://c2paviewer.com/articles/samsung-galaxy-s25-c2pa); [lumethic](https://www.lumethic.com/en/articles/smartphones-c2pa-content-credentials)
- Apple iPhone has no native C2PA as of 2026 sources. A single secondary source claims Apple is testing an "Apple Reference Image" capture mode in the iOS 27 beta, but its link to C2PA is unconfirmed — [lumethic](https://www.lumethic.com/en/articles/smartphones-c2pa-content-credentials). Treat this as a rumor.
- Leica: the M11-P (2023) was the first production camera with signing. M11-D, SL3-S and the Q3 family are reported as supported, the Q3 via a Dec 2025 firmware update. No source confirms Leica video signing — [attesttrail](https://attesttrail.com/blog/c2pa-cameras-support); [getkepla](https://www.getkepla.com/blog/content-credentials-c2pa) (secondary)
- Sony: C2PA video recording launched on 30 Oct 2025 for the Alpha 1 II, Alpha 9 III, FX3, FX30 and PXW-Z300, as a paid service for news organizations. Camera Verify (beta) added video verification in March 2026, via a verification URL plus an "Image Verification Pre-check SDK" that newsrooms can run in their own systems. Checks cover camera-origin signature, capture time and, on supported models, 3D depth detection of a real subject. Limits: MP4 only at 222 Mbps or lower; no 8K; no slow/quick motion; no depth check on the PXW-Z300. A trim function lets editors cut segments while keeping signatures — [Sony EU press](https://www.sony.eu/presscentre/enhancing-content-integrity-sony-launches-comprehensive-video-authenticity-verification-for-news-media); [Newsshooter Mar 2026](https://www.newsshooter.com/2026/03/12/sonys-camera-authenticity-solution-now-supports-video/); [SVG](https://www.sportsvideo.org/2026/03/16/sony-expands-camera-authenticity-solution-to-support-video/); [Alpha Universe](https://alphauniverse.com/stories/sony-launches-first-video-ready-camera-authenticity-solution-for-newsrooms/)
- Nikon: the Z6 III was the only Nikon body with consumer C2PA capture. The Z9, Z8 and Zf were not supported as of May 2026, and the service was suspended (see section 3) — [attesttrail](https://attesttrail.com/blog/c2pa-cameras-support)
- Canon EOS R1 / R5 Mark II: sources conflict. Some blogs list them as signing, but an Aug 2026 review could not verify a shipping C2PA camera from Canon, Panasonic or Fujifilm — [attesttrail](https://attesttrail.com/blog/c2pa-cameras-support) vs. [getkepla](https://www.getkepla.com/blog/content-credentials-c2pa). Status unconfirmed.
- Qualcomm Snapdragon 8 Gen 3 works with Truepic to support Content Credentials for photos and videos at the chipset level — [CAI How it works](https://contentauthenticity.org/how-it-works). Shipping OEM use is unverified.

**Platforms**
- Washington Post test, 22 Oct 2025 (Kevin Schaul): an AI-generated video with Content Credentials was uploaded to eight major platforms. None kept the Content Credentials data on the video or let users reach it. Only YouTube showed any disclosure, inside the expanded description. Facebook and TikTok had earlier said they would show such markers — [Washington Post](https://www.washingtonpost.com/technology/2025/10/22/ai-deepfake-sora-platforms-c2pa/) (via search snippet; full article not accessible); [Fred Ritchin commentary](https://fredritchin.substack.com/p/major-platforms-are-not-labeling)
- YouTube added automatic AI labelling in May 2026 that can use C2PA metadata among other signals. This postdates the WaPo test — [Washington Times](https://www.washingtontimes.com/news/2026/may/28/youtube-automatically-detecting-content-ai-generated/)
- LinkedIn shows a "CR" icon and a provenance panel on images that carry credentials — [makeinfluence](https://www.makeinfluence.com/en/academy/content-credentials-c2pa-how-platforms-label-ai-assisted-content) (secondary; images, not confirmed for video)
- TikTok has read Content Credentials for auto-labelling AI content since May 2024. Its label counts vary by source (1.3B vs 3B+). It was reportedly promoted to the C2PA steering committee in July 2026 — [ppc.land](https://ppc.land/c2pa/); [makeinfluence](https://www.makeinfluence.com/en/academy/content-credentials-c2pa-how-platforms-label-ai-assisted-content) (secondary, unverified)
- Meta reads C2PA/IPTC signals to apply "AI info" labels but serves files with the metadata stripped. Testing found it stripped credentials on video upload. Meta joined the C2PA steering committee in Sep 2024 — secondary only: [medium/theDevDesigns](https://medium.com/@theDevDesigns/provenance-that-actually-survives-upload-how-i-keep-content-credentials-intact-or-at-least-a13d85f36687)
- Cloudflare Images can preserve Content Credentials through transformations (a per-zone dashboard toggle) and appends its own signed actions, such as resize. Announced Feb 2025 — [Cloudflare docs](https://developers.cloudflare.com/images/optimization/transformations/preserve-content-credentials/); [Cloudflare blog](https://blog.cloudflare.com/preserve-content-credentials-with-cloudflare-images/). This covers images; no Cloudflare Stream video equivalent was found.
- X: no evidence found that it reads or displays C2PA.
- One explainer says social platforms strip all embedded metadata, C2PA manifests included, as a standard upload step — [softwareseni](https://www.softwareseni.com/durable-content-credentials-how-provenance-survives-metadata-stripping/) (secondary)

### Inferences
- The device side is getting better: the Pixel 10 at AL2 is the first mass-market default-on capture signing. For video, though, the only well-documented shipping capture signer is Sony's pro newsroom pipeline, which is paid, format-restricted and verified through a Sony service. Consumer video provenance at capture is essentially absent as of Oct 2026.
- Platforms use C2PA mainly as an input signal for AI labels, not as a provenance chain they pass on to viewers. A downloaded or re-shared copy loses the manifest, so any system built on embedded manifests alone fails at the first social hop.
- Sony's trim-while-preserving-signature feature shows that video editing workflows need provenance-aware tools. Ordinary edits break hard bindings.

### Gaps
- No quantitative stripping-rate study beyond the WaPo 8-platform test (n=1 video). The WaPo platform-by-platform list and company responses could not be read directly.
- Pixel 10 video signing and Leica video are unconfirmed. The Galaxy S26's behaviour rests on a single secondary source.
- No primary confirmation that LinkedIn displays credentials for video.

## 3. Documented failures and attacks

### Takeaway
The Nikon Z6 III episode (Sep 2025) showed that a legitimate device key can sign fabricated content, and that revocation is weakly enforced by validators. Academic work in 2026 (formal analysis and an IACR ePrint) found that timestamps can be swapped, revocation is under-specified, metadata and manifest-store regions are not fully bound, and provenance can contradict watermarks. Stripping and the analog hole remain the dominant practical failures.

### Cited Findings
- Nikon Z6 III: photographer Adam Horshack found that multiple-exposure mode (firmware 2.00, which introduced C2PA) let fabricated or AI-generated images receive valid Nikon C2PA signatures. Nikon confirmed the issue on 4 Sep 2025, suspended the Nikon Authenticity Service, and announced revocation of all certificates issued from launch to suspension. Affected images "cannot be used as proof of provenance" — [PetaPixel](https://petapixel.com/2025/09/22/nikon-cant-fully-solve-the-z6-iiis-c2pa-problems-alone/); [NikonRumors](https://nikonrumors.com/2025/09/21/nikon-sent-out-a-new-notice-informing-users-that-all-c2pa-certificates-issued-will-be-revoked.aspx/amp/); [Videomaker](https://www.videomaker.com/news/nikon-announces-temporary-suspension-of-its-authenticity-service/)
- Heise reports that standard validation procedures did not check whether a camera certificate was revoked, so validators might still accept the signatures. A full fix probably requires Z6 III firmware — [heise](https://heise.de/-10667707); [heise lessons learnt](https://heise.de/-10672949). The service remained suspended as of early 2026 — [c2paviewer, Feb 2026](https://c2paviewer.com/articles/nikon-cameras-c2pa)
- "Verifying Provenance of Digital Media: Why the C2PA Specifications Fall Short" (arXiv 2604.24890, Apr 2026, Golaszewski et al. per search summary) used formal analysis. Findings: trusted timestamps can be replaced or modified without detection; validators may accept conflicting timestamps; and in one test a revoked camera certificate was still reported valid by a validator — [arXiv 2604.24890](https://arxiv.org/html/2604.24890v1) (search summary only)
- "Security Analysis of C2PA and its Implementation" (IACR ePrint 2026/804): inadequate revocation rules create serious vulnerabilities, and bits in the asset's metadata or the manifest store can be changed without invalidating the claim signature — [IACR ePrint 2026/804](https://eprint.iacr.org/2026/804.pdf) (search summary only)
- "Authenticated Contradictions from Desynchronized Provenance and Watermarking" (arXiv 2603.02378) describes an "Integrity Clash": a valid C2PA manifest claims human authorship while the pixels carry an AI watermark, and both checks pass on their own. The attack is procedural, since the spec does not require an AI-origin assertion. The paper also says manifests can be stripped and reattached with altered assertions (re-signing), and that soft-binding collisions can let crafted content inherit legitimate provenance — [arXiv 2603.02378](https://arxiv.org/html/2603.02378v1)
- A 2026 survey states C2PA cannot stop compromised issuers or signers from attesting to inauthentic data — [arXiv 2606.00621](https://arxiv.org/html/2606.00621v1)
- Wikipedia reports an Oct 2026 researcher demonstration that a signer can exclude an entire file from signature calculations, allowing undetected alteration. This is unverified and single-source — [Wikipedia: Content Credentials](https://en.wikipedia.org/wiki/Content_Credentials)
- CNET-type coverage notes that Sora videos carried C2PA, but running them through watermark-removal or third-party apps and re-downloading defeats detection — [Yahoo/CNET](https://tech.yahoo.com/ai/chatgpt/articles/deepfakes-winning-tell-video-real-100000053.html). Screenshots and re-exports strip manifests — [aibuzz](https://aibuzz.blog/ai-watermarking-vs-metadata-vs-fingerprinting/)
- Analog hole / re-capture: no specific 2025–26 study was found. Sony's 3D depth detection on stills, and on some video models, is an explicit countermeasure to re-photographing a screen — [Sony EU press](https://www.sony.eu/presscentre/enhancing-content-integrity-sony-launches-comprehensive-video-authenticity-verification-for-news-media)

### Inferences
- The Nikon case is the key lesson. Hardware signing attests that "this device signed this", not that "this depicts reality". Any firmware path that composites (multiple exposure, in-camera AI, overlays) breaks the semantics. Revocation must be enforced in validators, and timestamps must be bound robustly, so that pre-compromise content stays valid and post-compromise content is rejected.
- Re-signing attacks mean a valid signature from some trust-list member is weak evidence. A verifier must check who signed and at what assurance level.

### Gaps
- Could not read the full papers; author lists and exact attack conditions come from search summaries.
- No published re-capture (analog-hole) success rates against C2PA-signed video were found.
- No public data on how many trust-list certificates have been revoked beyond Nikon.

## 4. Secure-capture products and what they do for video

### Takeaway
Truepic (enterprise SDK, Qualcomm integration), ProofMode (Guardian Project, open source), Starling Lab (capture-store-verify with decentralized storage) and Numbers Protocol (blockchain registration) all handle photos and video to some degree. Their video specifics are poorly documented in 2025–26 sources. Sony's newsroom service is the best-documented camera-native video product.

### Cited Findings
- Truepic was a C2PA founding member. It built a prototype on Snapdragon 865 that produced C2PA-sealed media, and Qualcomm's Snapdragon 8 Gen 3 camera system works with Truepic to support Content Credentials for photos and videos — [Truepic blog](https://www.truepic.com/blog/truepic-breakthrough-charts-a-path-for-restoring-trust-in-photos-and-videos-at-internet-scale); [CAI](https://contentauthenticity.org/how-it-works)
- ProofMode (Guardian Project) adds device sensor metadata, hardware fingerprinting, cryptographic signing and third-party notarization. It signs photos and videos on Android with GPS and timestamps — [CAI](https://contentauthenticity.org/how-it-works); [DeFake blog](https://blog.defake.app/digital-media-provenance-a-guide-to-verifying-content/)
- Starling Lab's framework is Capture, Store, Verify, aiming for a root of trust at capture in hardware or firmware. It distributed libProofMode and used IPFS, Filecoin and NEAR with Numbers Protocol (e.g. "Mom I See War") — [Starling Framework](https://starlinglab.org/starling-framework/); [Starling history](https://starlinglab.org/?lab=history)
- Numbers Protocol: Capture → Certify → Check, with on-chain registration at capture via the Numbers Capture app — [Melcher System Consulting](https://melchersystem.com/authenticity-content-provenance/securing-the-visual-record-a-strategic-and-technical-guide-to-content-provenance-and-authenticity/) (secondary)
- Sony Camera Verify (video, Mar 2026): see section 2. It covers C2PA video signing, a hosted verification URL, an on-prem pre-check SDK and trim-preserving signatures — [Newsshooter](https://www.newsshooter.com/2026/03/12/sonys-camera-authenticity-solution-now-supports-video/)

### Inferences
- The software-only capture apps (ProofMode, Numbers) cannot reach AL2-style hardware attestation on iOS. Google says AL2 for an app is Android-only. Cross-platform capture apps therefore face a ceiling on trust level.
- Anchoring hashes in a blockchain or registry (Starling, Numbers) survives metadata stripping only if verifiers can look content up by a robust fingerprint. That is the same dependency as C2PA soft bindings.

### Gaps
- No 2025–26 primary documentation found on Truepic's video-specific features (e.g. per-segment signing, live) or on ProofMode video formats and limits.

## 5. Criticisms of C2PA

### Takeaway
The main criticisms are privacy and identity leakage, "absence means nothing" (or worse, absence treated as suspicion), low visibility and awareness, stripping, and the gap between "signed" and "true". Even the NSA-led guidance warns about the implicit-suspicion problem.

### Cited Findings
- World Privacy Forum: identity data in a distributed manifest cannot be retroactively removed. Civil-society experts warn of "persecution through metadata" identifying a device and owner. WPF also notes the framework treats a missing signed claim as an indication of untrustworthiness — [World Privacy Forum](https://worldprivacyforum.org/posts/privacy-identity-and-trust-in-c2pa/)
- US NSA/partner Cybersecurity Information Sheet (Jan 2025) warns that large-scale use could lead the public to treat media without Content Credentials as suspect without reasonable justification — [media.defense.gov CSI](https://media.defense.gov/2025/Jan/29/2003634788/-1/-1/0/CSI-CONTENT-CREDENTIALS.PDF)
- Commentators argue that absence is not evidence of manipulation, since most media lacks credentials because tools never added them or a later step stripped them. Treating absence as suspicious penalizes legit content while forged-but-signed content passes — [truescreen](https://truescreen.io/articles/c2pa-standard-history-limitations/); [mashop](https://mashop.app/blog/content-credentials-c2pa-what-it-proves) (secondary)
- A Fortune investigation (Sep 2025) reportedly found the standard "puts user privacy on the line" — cited via [World Privacy Forum](https://worldprivacyforum.org/posts/privacy-identity-and-trust-in-c2pa/) (not read directly)
- Visibility: in the WaPo test, only YouTube showed any disclosure, and it was buried in the description — [Washington Post](https://www.washingtonpost.com/technology/2025/10/22/ai-deepfake-sora-platforms-c2pa/)
- Policy view: platforms should be required to preserve and display provenance where present, which in the US likely needs legislation — [AI Policy Bulletin](https://www.aipolicybulletin.org/articles/deepfake-policy-is-focused-on-the-wrong-end-of-the-problem)

### Inferences (implications for a new provenance system)
- Do not rely only on embedded manifests. Pair them with a robust soft binding (video-capable watermark or fingerprint) and a lookup service, or provenance dies at the first upload.
- Bind at capture with hardware-attested keys (AL2-style), and treat compositing or AI firmware modes as separate, labelled actions. Enforce revocation and trusted timestamps in the verifier, not just in the spec.
- Show who signed and at what assurance level, not a binary "verified" badge. Design for the reality that most authentic content carries no credential.
- Make privacy the default: unlinkable or one-time certificates as on Pixel, and optional identity assertions.
- Video needs edit-tolerant provenance (segment-level hashes, trims, re-encodes) and live-segment signing per C2PA 2.3.

### Gaps
- No consumer-awareness survey of Content Credentials (e.g. % of the public who recognize the CR icon) was found. This is a notable gap.
- The Fortune investigation was not accessed directly.
