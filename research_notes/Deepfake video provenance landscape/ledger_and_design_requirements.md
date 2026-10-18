# Ledger Notarization for Media and Design Requirements for a Foundational Video Provenance System

Research note: nist.gov, nvlpubs.nist.gov, airc.nist.gov and aigl.blog could not be reached from this research environment (DNS failure), so NIST AI 100-4 is cited from search-result summaries and secondary sources, not the primary PDF. Other findings come from search-result summaries plus primary pages where they were indexed.

## Deployed ledger notarization for media: what worked, what didn't, costs, latency, privacy

### Takeaway
Ledger notarization has been piloted widely: ProofMode with OpenTimestamps, Starling with Filecoin/IPFS, Reuters/Canon with Hedera, Fox Verify on Polygon, and Numbers Protocol. What it proves is narrow. A timestamp shows that a hash existed at a given time. It does not show who made the content or whether it is true. The trustworthiness comes from signing at capture and from editorial process. Transparency logs (the Certificate Transparency / Sigstore Rekor model) give public, append-only auditability without consensus costs, and C2PA itself works without any blockchain.

### Cited Findings
- **ProofMode (Guardian Project and WITNESS):** an Android camera app that adds "cryptographic digital signatures, third-party notarization, hardware authentication and additional supporting metadata" to photos and video at capture. It can send a "fingerprint" of the proof to Filecoin/IPFS so the content's existence is recorded on public ledgers and storage. — [Filecoin ecosystem: ProofMode](https://fil.org/ecosystem-explorer/proofmode-by-guardian-project)
- ProofMode is described as built partly on OpenTimestamps. The source for this is conference talk descriptions, not official ProofMode documentation, and the exact integration was not confirmed. — [MERGE-it 2025 talk](https://pretalx.com/merge-it-2025/talk/LSJ87Y/); [SFSCON talk](https://www.sfscon.it/talks/timestamping-with-opentimestamps/)
- **OpenTimestamps cost and latency:**
  - It batches many timestamps into one Bitcoin transaction through a Merkle tree, so each stamp is nearly free. — [loxal: Bitcoin notary](https://www.loxal.net/article/tech/BitCoin-notary.html)
  - Confirmation takes "a few hours". — [opentimestamps-client (PyPI)](https://pypi.python.org/pypi/opentimestamps-client)
  - Independent verification needs a local Bitcoin Core node, though a pruned node works. — [PyPI](https://pypi.python.org/pypi/opentimestamps-client)
  - "The blockchain only proves that a document existed at a certain time, not who created or signed it." — [loxal](https://www.loxal.net/article/tech/BitCoin-notary.html)
- **Starling Lab (Stanford and USC):**
  - Its framework has three modules, capture, store and verify, with IPFS/Filecoin used in all three. Its creators say it is meant to augment existing verification, not replace it. — [Filecoin blog: Starling Framework](https://filecoin.io/blog/starling-framework)
  - Deployments include Reuters photos of polling places on Super Tuesday, and a Rolling Stone archive on Bosnian war crimes registered on Numbers Protocol and stored on Filecoin/IPFS. — [Filecoin case study](https://filecoin.io/case-studies/starling-lab)
  - The founder names time pressure as the core problem for newsrooms, which have "hours or minutes — maybe less" to verify before publishing. — [Filecoin blog](https://filecoin.io/blog/meet-filecoin-s-collaborators-jonathan-dotan-starling-framework-for-data-integrity)
- **Reuters / Canon / Starling pilot (August 2023):**
  - A prototype Canon camera signed each image at capture with a device-specific key.
  - Pixels, GPS and metadata were registered on a public blockchain, with copies kept in two cryptographic archives.
  - Edit logs were registered on the Hedera public ledger.
  - Consumers verify by comparing the image's hash against the ledger.
  - Field use: Reuters photographer Violeta Santos Moura used it on the Ukraine front line.
  - Source: [Thomson Reuters press release](https://www.thomsonreuters.com/en/press-releases/2023/august/reuters-new-proof-of-concept-employs-authentication-system-to-securely-capture-store-and-verify-photographs); [Canon release](https://global.canon/en/news/2023/20230831.html); [PetaPixel](https://petapixel.com/2023/08/31/canon-and-reuters-develop-new-photo-authentication-technology)
- **Fox Verify (January 2024):**
  - An open-source protocol on Polygon PoS. Publishers sign content with private keys and register it on-chain, and smart contracts can manage access and AI licensing.
  - It had 89,000 pieces of content registered at public beta.
  - Coverage notes it "doesn't prove ownership" by itself but allows "public dispute and interrogation of content metadata."
  - It is positioned largely as an IP and AI-licensing tool.
  - Source: [Polygon blog](https://polygon.technology/blog/fox-corporation-taps-polygon-pos-to-power-verify-an-open-protocol-for-content-and-image-verification); [The Block](https://www.theblock.co/post/271288/fox-corporation-polygon-labs-verify); [NewscastStudio](https://www.newscaststudio.com/2024/01/09/fox-launches-verify-open-source-protocol-to-address-ais-intellectual-property-challenges/)
- **Numbers Protocol:**
  - Its Capture app seals photo metadata on its own chain and records later edits. — [TechCrunch 2021](https://techcrunch.com/2021/01/12/numbers-protocols-blockchain-camera-capture-app-safeguards-the-integrity-of-photos/)
  - From February 22, 2023, registration cost a fixed 0.025 NUM plus about 0.0004 NUM in gas, payable in a token or in "Capture Credits". — [Numbers blog](https://www.numbersprotocol.io/blog/photo-registration-upgrade-exclusive-airdrop-for-active-users)
  - Later posts mention evaluating Layer 2s (Arbitrum, Optimism, Base) to cut fees. — [Numbers blog: cross-chain](https://numbersprotocol.io/blog/cross-chain-tracking-expanding-provenance-across-blockchains)
- **Transparency logs as a non-blockchain alternative:**
  - A SoK paper says using a blockchain for log consistency "can be expensive because of transaction costs and has slow finality". The alternative is independent witnesses co-signing checkpoints, which has its own availability risk when too few witnesses take part. — [SoK: Log-Based Transparency Enhancing Technologies (arXiv 2305.01378)](https://arxiv.org/pdf/2305.01378)
  - Certificate Transparency is a publicly verifiable append-only log built without a blockchain. — [the morning paper](https://blog.acolyer.org/2014/10/09/certificate-transparency/)
  - Sigstore's own engineers said the Rekor v1 API was "complex and inefficient" and that "privacy and redaction is not easily supportable in the current design". Rekor v2 borrows Certificate Transparency's simplifications to cut operating cost. — [SigstoreCon 2024: Rekor v2](https://sigstoreconday2024.sched.com/event/1n4pT/rekor-v2-whats-next-for-sigstores-transparency-log-hayden-blauzvern-colleen-murphy-google)
- C2PA relies on signed credentials and a trust list, not a blockchain. This comes from show notes summarising a Hany Farid podcast discussion; it is not a direct quote from him. — [The FAIK Files ep. 70 notes](https://thecyberwire.com/podcasts/the-faik-files/70/notes)

### Inferences
- All of these systems put the trust at capture (a device key or hardware signature), not on the ledger. The ledger adds two things:
  - a hard-to-backdate existence timestamp
  - a public, tamper-evident registry that survives the publisher.
- A Certificate Transparency / Rekor-style append-only Merkle log, run by several operators with independent witnesses, provides both properties. It avoids token economics, gas fees, finality delays and the reputational "crypto" baggage. Anchoring the log's checkpoint root to a public chain from time to time (the OpenTimestamps pattern) is a cheap optional extra.
- **Privacy risk:** anything written to an immutable public ledger cannot be redacted. For activists, only hashes should be published, never metadata such as GPS or device IDs. Sigstore's admitted redaction difficulty supports this conclusion.
- None of these deployments shows consumer-scale adoption. All are pilots, newsroom tools or B2B licensing plays.

### Gaps
- No independent evaluation was found on whether ledger anchoring changed outcomes, for example evidence admitted in court or a debunk sped up, compared with signatures alone.
- No current (2024–2026) cost or usage figures were found for Numbers Protocol or Fox Verify. Whether the Reuters/Canon pilot was productised is unconfirmed.
- No documented use of Sigstore/Rekor specifically for media provenance was found.
- How ProofMode integrates OpenTimestamps is not confirmed from primary documentation.

## Expert critiques: WITNESS, Partnership on AI, NIST AI 100-4, Farid, blockchain critiques

### Takeaway
Expert bodies agree that no single technique is sufficient. They also agree that provenance shows origin and edit history, not truth, and that authenticity infrastructure can exclude or endanger vulnerable creators unless it is voluntary, privacy-preserving and works on low-end devices.

### Cited Findings
- **WITNESS, "Ticks or It Didn't Happen" (December 2019):**
  - It sets out 14 dilemmas for authenticity infrastructure, to be addressed early rather than patched later. — [WITNESS Lab](https://lab.witness.org/ticks-or-it-didnt-happen/); [PDF](https://lab.witness.org/wp-content/uploads/sites/29/2019/12/Ticks_or_it_didn%E2%80%99t_happen_WITNESS.pdf)
  - Dilemma 1 is inclusion and exclusion. Dilemma 2 is that the tools could be used for surveillance. Dilemma 14 asks whether blockchain can be trusted "if people can no longer be trusted". — [WITNESS PDF](https://lab.witness.org/wp-content/uploads/sites/29/2019/12/Ticks_or_it_didn%E2%80%99t_happen_WITNESS.pdf)
  - **The "tick" problem:** if every piece of media is expected to carry a tick, people who cannot or do not want to generate one are disadvantaged. Verification should be "a choice, not an obligation" (quoting Zeynep Tufekci). — [WITNESS PDF](https://lab.witness.org/wp-content/uploads/sites/29/2019/12/Ticks_or_it_didn%E2%80%99t_happen_WITNESS.pdf)
  - **Exclusion:** users with older phones, non-English speakers and people with patchy connectivity or GPS may be left out. Jailbroken or rooted devices "will not be able to capture verifiable audiovisual material". — [WITNESS PDF](https://lab.witness.org/wp-content/uploads/sites/29/2019/12/Ticks_or_it_didn%E2%80%99t_happen_WITNESS.pdf)
  - WITNESS took part in the C2PA harms and misuse assessment and pushes for "provenance and authenticity infrastructure" led by human rights. — [WITNESS blog: C2PA harms](https://blog.witness.org/2021/12/witness-and-the-c2pa-harms-and-misuse-assessment-process/); [WITNESS blog 2022](https://blog.witness.org/2022/01/potentially-systematic-provenance-and-authenticity-infrastructure/)
- **NIST AI 100-4 (final, November 2024):**
  - It surveys provenance tracking, labelling (watermarking), detection and testing for synthetic content. — [NIST publication page](https://nist.gov/publications/reducing-risks-posed-synthetic-content-overview-technical-approaches-digital-content); [Baker McKenzie summary](https://insightplus.bakermckenzie.com/bm/data-technology/united-states-ai-safety-institute-releases-its-first-synthetic-content-guidance-report-nist-ai-100-4)
  - CDT's comment on the April 2024 draft quotes it as saying "none of these techniques can be considered comprehensive solutions". Whether that wording survived into the final text was not verified. — [CDT comment](https://cdt.org/wp-content/uploads/2024/06/5.31.24-CDT-Comment-on-NIST-AI-100-4.pdf)
  - Secondary summaries say the approaches have "significant limitations, both technical and social". — [AIGL summary (search snippet)](https://www.aigl.blog/nist-reducing-risks-posed-by-synthetic-content-an-overview-of-technical-approaches-to-digital-content-transparency/)
  - Summaries also say many approaches' efficacy is "not fully examined yet" and wide deployment on mobile may be "years away". — [CSA community post](https://circle.cloudsecurityalliance.org/discussion/nist-trustworthy-and-responsible-ai-nist-ai-100-4-reducing-risks-posed-by-synthetic-content)
- **Partnership on AI:**
  - The 2024 lessons-learned paper on applying PAI's Synthetic Media Framework to 11 cases (BBC, OpenAI, TikTok and others) recommends using more than one disclosure mechanism. It also calls for clearer thresholds for when content is "synthetic enough" to need direct disclosure. — [arXiv 2407.13025](https://arxiv.org/pdf/2407.13025)
  - PAI's November 2024 case studies (Meta, Microsoft, Thorn, Truepic, Stanford HAI) name three challenges: disclosing AI-edited versus AI-generated content, label fatigue, and the limited effect of direct disclosure on AI-generated CSAM. — [PAI Nov 2024 announcement](https://partnershiponai.org/nov-2024-synthetic-media-case-studies-announcement/)
- **Hany Farid:**
  - Cointelegraph reports Farid said a finished blockchain solution to deepfakes is "years away" because of its complexity. — [Cointelegraph](https://cointelegraph.com/news/blockchain-might-be-a-silver-bullet-for-fighting-deepfakes)
  - Podcast show notes summarise his view that C2PA uses signed credentials and a trust list, not blockchain. — [FAIK Files](https://thecyberwire.com/podcasts/the-faik-files/70/notes)
- **Provenance is not truth:**
  - C2PA does not detect deepfakes. — [Reality Defender](https://www.realitydefender.com/insights/provenance-and-synthetic-media-detection)
  - Provenance proves origin, "not necessarily truthfulness". — [Rubinlake tech radar](https://rubinlake.com/en/technology-radar/ai-security-and-governance/digital-provenance)

### Inferences
- The strongest critique is social, not cryptographic. A system that makes credentials the norm risks discrediting authentic footage from the people who most need to be believed, such as bystanders, activists and people on cheap phones. A foundation must therefore treat a missing credential as "unknown", never as "fake".
- No expert source found argues that a blockchain is needed. WITNESS raises it only as a dilemma, and Farid is reported as sceptical of blockchain timelines.

### Gaps
- Direct NIST AI 100-4 text could not be retrieved: the final report's specific findings on watermark removal, metadata stripping, detection false positives and privacy are unverified here.
- No verbatim Farid quote on blockchain was found, and no peer-reviewed academic critique specific to blockchain for media provenance was retrieved.

## Design requirements for a provenance foundation, and how layered approaches combine

### Takeaway
The emerging consensus architecture has three layers. A signed manifest (hard binding) shows tampering. A watermark and/or fingerprint (soft binding) recovers the manifest after metadata is stripped or the file is transcoded. A public, durable registry or lookup resolves soft-binding IDs back to manifests. Around these sit human-rights requirements: the system is voluntary, it minimises privacy exposure, it works on low-end devices, and a missing credential means "unknown".

### Cited Findings
- **Soft binding recovers stripped credentials:** manifests embedded in the file can be removed. Watermarks or fingerprints let the credential be found again from a stored copy, which is the "Durable Content Credentials" design. — [C2PA FAQ](https://c2pa.org/faq/); [CAI open-source docs: Durable CR](https://opensource.contentauthenticity.org/docs/durable-cr/); [CAI blog](https://contentauthenticity.org/blog/durable-content-credentials)
- **Watermark capacity:** a watermark carries very little data, so it encodes only a short identifier that serves as a lookup key into a manifest repository. — [CAI blog](https://contentauthenticity.org/blog/durable-content-credentials)
- **Hard versus soft binding:** hard bindings detect alteration, while soft bindings are built to survive it. — [PPC Land](https://ppc.land/c2pa/)
- **Soft-binding weaknesses:** soft bindings are not unique by construction and are weaker against collision attacks. Durability comes from lookup, not from the original signature surviving. — [CASRAI guide](https://casrai.org/guides/c2pa-content-credentials-explained)
- **Combining methods:** combining a watermark with a fingerprint improves robustness, and C2PA requires approved soft-binding algorithms. — [CAI Durable CR docs](https://opensource.contentauthenticity.org/docs/durable-cr/); [TrustMark + C2PA](https://opensource.contentauthenticity.org/docs/trustmark/c2pa/)
- **Platform behaviour:** stripping differs by platform and upload path. LinkedIn and Cloudflare Images reportedly keep credentials. — [SoftwareSeni](https://www.softwareseni.com/durable-content-credentials-how-provenance-survives-metadata-stripping)
- **Device and inclusion requirements:** WITNESS stresses older phones, connectivity, language and rooted devices. — [WITNESS PDF](https://lab.witness.org/wp-content/uploads/sites/29/2019/12/Ticks_or_it_didn%E2%80%99t_happen_WITNESS.pdf)
- **Time to verify:** newsrooms have minutes to hours. — [Filecoin / Starling](https://filecoin.io/blog/meet-filecoin-s-collaborators-jonathan-dotan-starling-framework-for-data-integrity)
- **Public verifiability without consensus:** append-only logs with independent monitors and witnesses provide it. The log's security rests on its witnesses, not on the operator's honesty. — [SoK arXiv 2305.01378](https://arxiv.org/pdf/2305.01378); [First AI Movers radar](https://radar.firstaimovers.com/transparency-logs-a-record-no-one-can-quietly-change-summary-a-transpa)

### Inferences
These are the requirements implied for a minimal foundation:
1. **Hard binding:** hash and sign at capture or at publish, using C2PA-compatible manifests.
2. **Soft binding:** a robust, low-payload watermark ID plus a perceptual fingerprint for files whose metadata was stripped or that were re-encoded.
3. **Registry:** a public, append-only, multi-operator Merkle transparency log mapping content hashes and soft-binding IDs to manifests.
   - Store only hashes and opt-in metadata, to protect privacy.
   - Optionally anchor its root to a public chain.
4. **Key compromise handling:** a log-backed revocation and key-rotation history, so verifiers can tell "signed before the compromise" from "signed after". This follows from the CT and Sigstore design pattern; no source in this note states it explicitly for media.
5. **User experience:** three states, "verified origin", "verified AI-generated" and "no information". "No information" must be neutral, because the implied-truth and WITNESS "tick" concerns cut in both directions.
6. **Defence in depth:** treat soft-binding matches as probabilistic because of collision risk. Confirm them against the hard-bound manifest where one exists, and show near-matches as "similar to" rather than "is".

### Gaps
- No primary source was found that states key-compromise recovery requirements for C2PA signers, such as CRL/OCSP use or timestamp authority practice. This needs a follow-up check against the C2PA specification's trust-model section.
- No quantitative robustness figures (survival rates under transcoding or screen recording) were found for the TrustMark or video watermarks.

## Video-specific provenance: segments, live streams, Merkle structures, edits and clips

### Takeaway
C2PA covers whole and fragmented MP4 for video on demand. Live streaming is in active development, with two approaches: per-segment signatures with short-lived session keys carried in `emsg` boxes, and per-segment Merkle data. Verification and UI in players is still largely left unspecified, and clipping and re-editing on social platforms remains the main unsolved gap.

### Cited Findings
- **Irdeto's "Verifiable Segment Info" approach for live video:**
  - The C2PA manifest sits in the initialisation segment of each track, as for video on demand.
  - Each live segment carries a small, standardised C2PA Event Message Box (`emsg`) with its signature and sequence position.
  - The signatures come from short-lived asymmetric "session keys".
  - Putting a full manifest in every segment is an alternative where bandwidth is not a constraint.
  - Source: [Irdeto blog](https://irdeto.com/blog/extending-trust-into-live-video-with-c2pa)
- **Bandwidth overhead:** Unified Streaming's proof of concept cut overhead to about 0.56% with C2PA session keys. Prior work on per-segment manifests reported about 5% for representations below 1.5 Mbps. Its threat model is a man-in-the-middle swapping segments or manifests. — [Unified Streaming presentation](https://www.unified-streaming.com/presentations/when-a-man-in-the-middle-tries-crashing-the-live-streaming-party-the-c2pa-bouncer-steps-in)
- **Player-side handling (THEOplayer/Dolby):**
  - It reads the manifest store from the initialisation segment and per-segment Merkle tree data ("purpose merkle") from ISOBMFF `uuid` boxes.
  - The player itself "does not validate C2PA signatures, evaluate trust lists, or make any trust decisions".
  - Source: [THEOplayer C2PA metadata docs](https://docs-preview.optiview.dolby.com/pr-833/theoplayer/how-to-guides/web/miscellaneous/c2pa-metadata/)
- Adobe Research notes that C2PA specifies how manifests are generated for fMP4, but "verification and visualization ... is left unspecified". Its paper builds a dash.js client validator to fill that gap. — [Adobe Research: Content authenticity with DASH](https://research.adobe.com/publication/integrating-content-authenticity-with-dash-video-streaming)
- One vendor document says fragmented formats are supported but need static packaging. This predates the live work above. — [GL Systemhaus](https://www.gl-systemhaus.de/hubfs/gl-systemhaus.de/PDF/product-page_c2pa_use-cases.pdf)

### Inferences
- Per-segment hashing with Merkle aggregation is the natural basis for clip verification. A short clip cut on segment or GOP boundaries could in principle be checked against the signed Merkle root. Clips that are re-encoded, cropped or screen-recorded cannot, so they would need the soft-binding and fingerprint layer, such as per-segment perceptual hashes registered in the log.
- Session keys bring their own key-management and revocation problem for live video.

### Gaps
- The C2PA specification text for live streaming was not retrieved, so box names and key-rotation details come from vendors.
- No source was found on how social platforms (YouTube, TikTok, X) handle C2PA on video uploads end to end, or on standard ways to prove a clip came from a credentialed parent video.

## How users respond to provenance labels

### Takeaway
The evidence is mixed. Provenance labels can raise trust in the outlet, but users often misunderstand them and confuse "provenance is credible" with "content is true". Meta's 2024 "Made with AI" mislabelling of lightly edited real photos shows that binary AI labels driven by metadata produce false positives and backlash. The implied-truth effect means that unlabelled content gains unearned credibility.

### Cited Findings
- **Large positive study:** in an experiment with 6,114 participants across the US, UK and Norway, C2PA provenance metadata improved perceived image transparency and credibility and raised trust in the news source (ICWSM). — [ICWSM paper](https://ojs.aaai.org/index.php/ICWSM/article/view/42749)
  - A replication call notes its code and data could not be found, so the result is unreplicated. — [ReScience replication issue](https://github.com/ReScience/call-for-replication/issues/9)
- **Mixed result (n=202, University of Bergen):** labels raised trust in the article but not in the image or article selection, and many participants misread what the labels meant. — [CEUR-WS short paper](https://ceur-ws.org/Vol-4056/short4.pdf)
- **Social media study (n=595, US/UK):** provenance information often lowered trust and made users doubt deceptive media, especially when it revealed compositing. Users confused media credibility with provenance credibility. — [arXiv 2303.12118](https://ar5iv.labs.arxiv.org/html/2303.12118)
- **Label detail:** more detail improves perceived label transparency but does not change engagement (CSCW 2025 companion). — [arXiv 2510.19024](https://arxiv.org/pdf/2510.19024.pdf)
- **AI labels and accuracy:** headlines labelled "AI-generated" are seen as less credible even when they are accurate. — [ICWSM 2025](https://ojs.aaai.org/index.php/ICWSM/article/download/42721/50281/46822)
- **Implied-truth effect (Pennycook and Rand):** labelling some false items makes unlabelled items seem more credible. Adding "verified" tags to true items reduced the effect. — [MIT News](https://news.mit.edu/2020/warning-labels-fake-news-trustworthy-0303)
  - A later thesis found that labelling both true and false items did not reduce the implied-truth effect. — [Wooster thesis](https://openworks.wooster.edu/independentstudy/9915)
- **Meta 2024:**
  - In May 2024, "Made with AI" labels hit real photos that had only basic or generative-fill edits, triggered by C2PA and IPTC metadata.
  - In July 2024, Meta renamed the label "AI info", admitting the old wording did not make clear that AI might only have been used for editing.
  - The detection method did not change.
  - Critics said clicking the new label still showed essentially the same message.
  - Source: [TechCrunch](https://techcrunch.com/2024/07/01/meta-changes-its-label-from-made-with-ai-to-ai-info-to-indicate-use-of-ai-in-photos/); [Digital Camera World](https://digitalcameraworld.com/news/meta-update-its-made-with-ai-labels-after-backlash-but-is-it-enough-to-protect-photographers)
- PAI's case studies (including Meta's) identify label fatigue and the AI-edited versus AI-generated distinction as live problems. — [PAI Nov 2024](https://partnershiponai.org/nov-2024-synthetic-media-case-studies-announcement/)

### Inferences
- Labels should communicate provenance facts (who captured or published it, when, and what edits were made), not verdicts on truth. Binary "AI / not AI" badges cause false-positive backlash and the implied-truth effect.
- The "no information" state must be explicitly neutral, and any ecosystem should expect a long period in which most authentic video carries no credential. That makes the liar's dividend risk real: people can wave away real footage that lacks a credential.

### Gaps
- No peer-reviewed study specific to video provenance labels was found; all the studies above use images or headlines.
- No empirical study measuring the liar's dividend in the context of provenance labels was found in this search.
