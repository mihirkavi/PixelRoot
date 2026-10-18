# Regulatory drivers for AI-content labeling, watermarking and media provenance (2024–2027), status as of mid-October 2026

Method note: The search tool returned law-firm and tracker summaries. Direct fetches of primary sites (leginfo, EC digital-strategy, Sidley, Paul Weiss, Jones Day) failed with DNS errors in this environment, so most citations are secondary. Where a source says it is single-sourced or sources conflict, that is flagged. Citations to eur-lex and congress.gov for statute text are given for base facts that are long settled. Check them against the official text before quoting.

## 1. EU: AI Act Article 50, the Code of Practice, Digital Omnibus, DSA

### Takeaway
Article 50 has applied since 2 August 2026. Generative-AI providers must mark outputs in a machine-readable, detectable way. Deployers must disclose deepfakes. The Digital Omnibus gives systems already on the market before 2 Aug 2026 until 2 Dec 2026 to comply with Art 50(2) marking; new systems get no grace period. The voluntary Code of Practice was finalised on 10 June 2026. It sets a de facto technical bar of at least two machine-readable techniques (for example signed, tamper-evident metadata plus an imperceptible watermark). That bar fits C2PA-style manifests combined with watermarking.

### Cited Findings
- Article 50(2): providers of AI systems that generate synthetic audio, image, video or text must ensure outputs are "marked in a machine-readable format and detectable as artificially generated or manipulated". Solutions must be effective, interoperable, robust and reliable as far as technically feasible. Article 50(4): deployers of deepfakes must disclose that the content was artificially generated or manipulated. Art 50 applies from 2 Aug 2026 (Art 113). Fines under Art 99(4) are up to EUR 15M or 3% of worldwide turnover. — [Regulation (EU) 2024/1689, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj); [artificialintelligenceact.eu Art 50 guide](https://artificialintelligenceact.eu/transparency-rules-article-50/)
- The final Code of Practice on marking and labelling AI-generated content was published on 10 June 2026. It is voluntary, has Art 50(7) as its legal basis, and was drafted by independent experts under the AI Office. Section 1 covers providers (Art 50(2) marking and detection). Section 2 covers deployers (Art 50(4) deepfakes and public-interest text). — [European Commission press release IP/26/1328](https://ec.europa.eu/commission/presscorner/detail/en/ip_26_1328); [EC digital-strategy news](https://digital-strategy.ec.europa.eu/en/news/commission-publishes-code-practice-marking-and-labelling-ai-generated-content); [Jones Day](https://www.jonesday.com/en/insights/2026/06/european-commission-publishes-final-code-of-practice-on-marking-and-labelling-aigenerated-content)
- Provider commitments include at least two machine-readable techniques, for example digitally signed, tamper-evident metadata plus imperceptible watermarking. Providers must also prohibit users from stripping metadata, and detection must be offered. — [Jones Day](https://www.jonesday.com/en/insights/2026/06/european-commission-publishes-final-code-of-practice-on-marking-and-labelling-aigenerated-content); [getactready summary](https://getactready.com/blog/eu-ai-act-code-of-practice-marking-ai-content); [Bird & Bird](https://www.twobirds.com/en/insights/2026/taking-the-eu-ai-act-to-practice-the-final-transparency-code-of-practice)
- Deployer labels must be immediately recognisable without user interaction, perceivable at first exposure, and visible for a sufficient duration. Annex I provides common EU icons for labelling. — [Jones Day](https://www.jonesday.com/en/insights/2026/06/european-commission-publishes-final-code-of-practice-on-marking-and-labelling-aigenerated-content)
- The Code is not binding. Not signing exempts no one; non-signatories carry the burden of showing compliance by other means. — [nicfab analysis](https://www.nicfab.eu/en/posts/code-of-practice-transparency-ai-content/); [getactready](https://getactready.com/blog/eu-ai-act-code-of-practice-marking-ai-content)
- The Commission's Article 50 guidelines were finalised on 20 July 2026 and complete the guidance framework alongside the Code. — [Paul Weiss](https://www.paulweiss.com/insights/client-memos/eu-finalises-transparency-rules-for-ai-generated-content)
- Digital Omnibus: generative systems already on the market before 2 Aug 2026 have until 2 Dec 2026 to bring Art 50(2) marking and detection into conformity. Systems placed on the market on or after 2 Aug 2026 get no grace. Chatbot disclosure, deepfake labelling and emotion-recognition notices are unchanged and apply from 2 Aug 2026. — [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-article50-watermarking-deadline/); [Usercentrics](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-delay-article-50-transparency-consent/); [getactready, "grace period misread"](https://getactready.com/blog/eu-ai-act-watermarking-grace-period-misread)
- One analysis places the 2 Dec 2026 date in a new Art 111(4), not in Art 50 itself. — [Pharos](https://pharosproduction.com/insights/engineering/ai-act-article-50-transparency/)
- Sources conflict on the details. One describes the grace period as "compressed from six months to three", which differs from the roughly four-month figure elsewhere. Sources also differ on whether the Omnibus entered into force on 27 July 2026 or only on later Official Journal publication. — [Cookiebot](https://www.cookiebot.com/en/eu-ai-act-article-50-transparency-compliance/); [Formalize](https://formalize.com/en/blog/eu-ai-act-digital-omnibus); [Usercentrics](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-delay-article-50-transparency-consent/)
- The European AI Board's 17 Sept 2026 plenary reportedly set no new deadline and granted no further watermarking relief (single source). — [CSA note](https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-article50-watermarking-deadline/)
- DSA angle: Art 35(1)(k) lists, among the risk-mitigation measures for very large online platforms and search engines, ensuring that generated or manipulated image, audio or video that appreciably resembles existing persons, objects, places or events and falsely appears authentic is "distinguishable through prominent markings" when presented on their interfaces. — [Regulation (EU) 2022/2065, EUR-Lex](https://eur-lex.europa.eu/eli/reg/2022/2065/oj)

### Inferences
- The two-technique floor (metadata plus watermark) creates direct EU demand for C2PA Content Credentials paired with invisible watermarking, and for detection APIs or verifiers.
- AI Act Art 50 puts the duty on generators and deployers, and DSA Art 35 on platforms that show content. Together they cover content from generation through distribution.
- The Code addresses only synthetic content. Nothing in the EU framework requires authenticity marking of camera-captured media.

### Gaps
- The Code's exact text could not be fetched. I could not confirm whether it names C2PA or ISO/IEC standards, how fingerprinting and logging are treated, or the signatory list.
- Exact Official Journal citation and entry-into-force date of the Digital Omnibus are unverified.
- No DSA enforcement action specifically on deepfake marking was found.

## 2. United States: federal, California, other states, evidence rules

### Takeaway
Federally, only the TAKE IT DOWN Act (2025) is in force. It is a takedown and criminal regime for non-consensual intimate imagery, including AI forgeries, not a labeling mandate. The NO FAKES Act is still a bill. California's AI Transparency Act (SB 942 as amended by AB 853) is the main US provenance mandate:
- Generative-AI providers since 2 Aug 2026.
- Large platforms from 1 Jan 2027.
- Capture-device makers from 1 Jan 2028. This is the clearest law anywhere that requires authenticity or provenance options for real captured media.

Proposed FRE 707 was not advanced in 2026.

### Cited Findings
- TAKE IT DOWN Act: signed 19 May 2025. It criminalises publishing non-consensual intimate imagery, including "digital forgeries". Covered platforms had one year, to 19 May 2026, to set up a notice-and-removal process with removal within 48 hours. The FTC enforces. — [S.146, congress.gov](https://www.congress.gov/bill/119th-congress/senate-bill/146)
- The platform duties took effect on 19 May 2026. FTC Chairman Ferguson sent warning letters to 15 platforms, among them Alphabet, Amazon, Apple, Meta, Microsoft, TikTok, Reddit, Snap and X, and launched the TakeItDown.ftc.gov reporting portal. One tracker found no FTC enforcement cases as of 10 Jul 2026. — [stackcyber tracker](https://stackcyber.com/posts/ai-deepfake-laws); [vorplabs tracker](https://vorplabs.com/ai-regulatory-updates/deepfake-laws)
- NO FAKES Act of 2026 (S.4591 / H.R.8915): reintroduced and advanced by Senate Judiciary by voice vote in June 2026. Sources give 18 or 22 June. It was placed on the Senate calendar on 24 June. The House bill was referred to Judiciary on 20 May. Neither chamber has passed it. The 2026 version adds a DMCA-style counter-notice process. — [congress.gov S.4591](https://www.congress.gov/bill/119th-congress/senate-bill/4591); [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/06/senate-judiciary-committee-advances-legislation-to-protect-name); [Manatt](https://www.manatt.com/insights/newsletters/client-alert/congress-reintroduces-the-no-fakes-act-what-s-new-in-the-2026-bill); [ByteBack Law](https://www.bytebacklaw.com/2026/08/a-federal-shift-in-ai-and-the-right-of-publicity-no-fakes-act-advances-in-congress/)
- California AB 853 (signed 13 Oct 2025, Ch. 674) amended SB 942 and moved its operative date from 1 Jan 2026 to 2 Aug 2026. — [Orrick InfoBytes](https://infobytes.orrick.com/2025-10-17/california-delays-its-ai-transparency-act-and-passes-new-content-laws/); [GovBuddy](https://www.govbuddy.com/california/bills/ab-853/)
- SB 942 core duties (covered providers with more than 1M monthly users):
  - Offer a free AI-detection tool.
  - Embed latent disclosures in AI-generated image, video and audio.
  - Offer an optional manifest disclosure.
  - Penalty: $5,000 per violation, with each day counted separately.

  — [Orrick](https://infobytes.orrick.com/2025-10-17/california-delays-its-ai-transparency-act-and-passes-new-content-laws/); [Terms.law](https://terms.law/california-ai-laws/); [Crowell](https://www.crowell.com/en/insights/client-alerts/californias-ai-transparency-act-caita-may-be-amended-to-regulate-social-media-platforms)
- AB 853 platform duties: large online platforms take on provenance-detection and disclosure duties from 1 Jan 2027. — [Vensure summary](https://dev2.vensure.com/employment-law-updates/california-ai-transparency-act-new-disclosure-and-detection-requirements-for-ai-content/); [Crowell](https://www.crowell.com/en/insights/client-alerts/californias-ai-transparency-act-caita-may-be-amended-to-regulate-social-media-platforms)
- AB 853 capture devices: from 1 Jan 2028, makers of capture devices first produced for sale in California on or after that date must give users an option to include a latent disclosure in captured content, including the manufacturer name. "Capture device" covers cameras, phones with built-in cameras or microphones, and voice recorders. — [Sidley-hosted AB 853 text](https://www.sidley.com/en/-/media/resource-pages/ai-monitor/laws-and-regulations/cal-ab853-california-ai-transparency-act.pdf?la=en)
- Election deepfakes: about 30 states regulate AI deepfakes in political ads as of 5 Oct 2026. Four prohibit some deceptive candidate deepfakes, 26 require disclaimers, and one had its law blocked. Another tracker counts at least 28. — [thepoliticalgroup tracker](https://www.thepoliticalgroup.com/ai-laws/topic/political-deepfake-laws); [NCSL](https://www.ncsl.org/elections-and-campaigns/artificial-intelligence-ai-in-elections-and-campaigns); [govfacts](https://govfacts.org/elections-voting/running-elections/election-security-audits/states-are-building-a-patchwork-of-laws-to-regulate-election-deepfakes/)
- California AB 2655 and AB 2839 were struck down or enjoined in *Kohls v. Bonta* on First Amendment and vagueness grounds. The Ninth Circuit appeal is pending. — [HLLI case page](https://hlli.org/kohls-v-bonta/)
- Minnesota's election-deepfake statute (Minn. Stat. § 609.771) remains in force. The Eighth Circuit affirmed denial of a preliminary injunction on 9 Feb 2026 in *Kohls v. Ellison*, and *X Corp. v. Ellison* continues. — [Reason/Volokh](https://reason.com/volokh/2026/02/09/no-preliminary-injunction-in-challenge-to-minnesota-election-deepfake-law-but-challenge-goes-on/); [X Corp complaint, govinfo](https://www.govinfo.gov/content/pkg/USCOURTS-mnd-0_25-cv-01649/pdf/USCOURTS-mnd-0_25-cv-01649-1.pdf)
- Federal executive action: EO "Ensuring a National Policy Framework for Artificial Intelligence" was signed 11 Dec 2025. It directed a DOJ AI Litigation Task Force to challenge state AI laws; the Attorney General established it on 9 Jan 2026. It carves out child-safety laws from proposed preemption. No deepfake-specific carve-out was found. Sources conflict on the EO number (14257 vs 14365). — [Ropes & Gray](https://www.ropesgray.com/en/insights/alerts/2025/12/trump-attempts-to-preempt-state-ai-regulation-through-executive-order); [Jenner](https://www.jenner.com/en/news-insights/client-alerts/trump-administration-issues-executive-order-in-attempt-to-preempt-state-ai-laws); [ZwillGen](https://www.zwillgen.com/artificial-intelligence/trump-executive-order-targets-state-ai-laws/)
- The EO does not itself invalidate state laws. They remain enforceable absent court action or congressional preemption. — [Jenner](https://www.jenner.com/en/news-insights/client-alerts/trump-administration-issues-executive-order-in-attempt-to-preempt-state-ai-laws)
- Proposed FRE 707 (machine-generated evidence would have to meet Rule 702 reliability standards):
  - It was published for comment in 2025.
  - In May 2026 the Evidence Advisory Committee recommended no action on 707, revised it, and sent it for further study. It advanced amendments to Rules 609, 902(1) and 104 instead.
  - The Committee scheduled a mini-conference on draft Rules 707 and 901(c) (deepfake authentication) for 15 Oct 2026; no outcome was found.
  - One secondary source says no version can take effect before 1 Dec 2029.

  — [Advisory Committee report, May 2026 (uscourts.gov)](https://www.uscourts.gov/sites/default/files/document/advisory_committee_on_evidence_rules_may_2026.pdf); [Regulayer](https://regulayer.com/laws/federal-rule-of-evidence-707-machine-generated-evidence); [caseread](https://www.caseread.ai/blog/fre-707-ai-generated-evidence); [NYC Bar comments](https://www.nycbar.org/reports/comments-on-proposed-federal-rule-of-evidence-707-and-amendments-to-rule-609/)

### Inferences
- California is the US anchor of demand. Generator latent disclosures are live now. Platforms must read and display provenance from 2027. Device makers need capture-side provenance from 2028. That staged rollout pushes C2PA-compatible signing into phones and cameras sold in the US.
- Federal rules target harms (NCII takedown, likeness rights) rather than labeling. Courts' work on authenticating AI-era evidence (draft Rule 901(c)) could create demand for provenance as proof of authenticity, but not before about 2029.
- Federal preemption litigation against state AI laws is a risk to California's regime. No challenge specifically to SB 942 or AB 853 was found.

### Gaps
- The enrolled AB 853 text could not be fetched. Still unconfirmed:
  - the platform-size threshold and exact display duties;
  - whether the device option is opt-in or on by default;
  - whether C2PA is referenced (only "widely adopted standards" type language is likely);
  - the GenAI hosting-platform duties.
- No specific FTC TAKE IT DOWN enforcement action after July 2026 was found.
- The outcome of the 15 Oct 2026 FRE 707 and 901(c) meeting was not found.

## 3. India: IT Rules amendments on synthetically generated information (SGI)

### Takeaway
MeitY notified the amendments on 10 Feb 2026 (G.S.R. 120(E)), in force from 20 Feb 2026. Non-prohibited SGI must be clearly and prominently labelled and, where feasible, carry permanent metadata or unique identifiers. The draft rule that watermarks cover 10% of the visual area was dropped. Further tightening was proposed in April 2026 and an advisory issued in October 2026.

### Cited Findings
- The rules were notified on 10 Feb 2026 as G.S.R. 120(E) and came into force on 20 Feb 2026. SGI means audio, visual or audio-visual material that appears real. AI-generated text is excluded. — [DSCI](https://www.dsci.in/resource/content/it-amendment-rules-2026); [MediaNama](https://www.medianama.com/2026/02/223-meity-amendments-it-rules-synthetic-media-deepfakes/); [Freshfields](https://www.freshfields.com/en/our-thinking/blogs/technology-quotient/india-targets-deepfakes-and-ai-generated-content-key-changes-under-meitys-2026-102mjwn)
- The October 2025 draft's requirement that watermarks cover at least 10% of the visual area was dropped. Final rules require SGI to be "clearly and prominently labelled" and, where feasible, to carry permanent metadata or unique identifiers that help trace the generating resource. Takedown on court or government orders was cut from 36 hours to 3 hours. — [HLC](https://www.hlc.com/en/publications/india-introduces-mandatory-labelling-for-ai-and-3hour-takedown-for-illegal-content); [ANM Global](https://anmglobal.net/articles/regulating-synthetic-content-key-implications-of-the-it-rules-amendment-2026); [S.S. Rana](https://ssrana.in/articles/india-tightens-oversight-on-ai-generated-content-under-it-rules/); [MeitY FAQ (Oct 2025 draft)](https://www.meity.gov.in/static/uploads/2025/10/065b6deb585441b5ccdf8be42502a49c.pdf)
- A draft amendment of 21 Apr 2026 proposed continuous, clearly visible labels for the full duration of content, with comments due by 7 May 2026. Its notification was not confirmed. — [iPleaders](https://blog.ipleaders.in/it-rules-2026/)
- An October 2026 MeitY advisory reportedly widens labelling duties for social media beyond synthetic content (single source, MediaNama exclusive). — [MediaNama](https://www.medianama.com/2026/10/223-meity-labelling-social-media-synthetic-content/)

### Inferences
- India's "metadata or unique identifier where feasible" duty is a direct demand driver for embedded provenance (C2PA or similar), alongside visible labels. The 3-hour takedown also rewards fast detection.

### Gaps
- Whether the April 2026 draft was notified, and the exact scope of the October 2026 advisory, are unconfirmed.

## 4. China: Measures for Labeling AI-Generated Synthetic Content

### Takeaway
In force since 1 Sept 2025 together with mandatory national standard GB 45438-2025. Explicit (visible) labels and implicit (metadata) labels are required. Distribution platforms must detect and label content. This is the most prescriptive regime in force, but it covers synthetic content only.

### Cited Findings
- The Measures were issued in March 2025 by the CAC and other ministries. Sources give the issue date as 7, 14 or 17 March. They took effect on 1 Sept 2025 alongside GB 45438-2025 and cover AI text, images, audio, video and virtual scenes. — [HSF Kramer](https://www.hsfkramer.com/notes/tmt/2025-posts/China-Releases-Laws-to-Mandate-Labelling-of-AIGC); [Allen & Gledhill](https://www.allenandgledhill.com/cn/publication/articles/30284/further-regulates-ai-generated-content); [DS Avocats](https://www.dsavocats.com/mailing/Asia%20News/20250326%20Flash%20Info%20EN.pdf)
- Explicit labels are visible text, watermark, audio or rhythm cues, specified in the standard. Implicit labels are file metadata embedded per the standard's format rules. Platforms must check for implicit labels, label suspected AI content, and verify that apps offering generation services comply. — [OCPL substack](https://ocpl.substack.com/p/labelling-ai-generated-content-in); [aiforlawyers](https://aiforlawyers.substack.com/p/a-glimpse-of-the-future-why-chinas); [Allen & Gledhill](https://www.allenandgledhill.com/cn/publication/articles/30284/further-regulates-ai-generated-content)
- A review about ten months in reports widespread watermark-removal tools, unlabeled AI video on major platforms, and human creators wrongly flagged as AI. — [OCPL substack](https://ocpl.substack.com/p/labelling-ai-generated-content-in)

### Inferences
- China's metadata scheme is a national standard, not C2PA. Global providers face a dual-format burden. The false-positive problem shows why authenticity signals on real content would help.

### Gaps
- The primary CAC text was not reviewed. Article numbers and whether the GB standard allows digital watermarks as an implicit label are unverified.

## 5. Other jurisdictions: UK, South Korea, Denmark

### Takeaway
- **South Korea:** the AI Basic Act has been in force since 22 Jan 2026. It requires generative-AI output labelling (visible or invisible marks, with clear disclosure for deepfakes). Fines are deferred for at least a year.
- **UK:** the regime is harm-based (intimate-image abuse offences and Online Safety Act hash matching). It has no provenance or labeling mandate.
- **Denmark:** the likeness-copyright amendment was re-introduced on 8 Oct 2026 and is not yet adopted.

### Cited Findings
- South Korea:
  - The AI Basic Act and its Enforcement Decree took effect on 22 Jan 2026. Some sources say 29 Jan.
  - Generative outputs must be labelled. Providers can choose visible marks or invisible ones (watermark or metadata). Realistic deepfakes must be clearly disclosed.
  - Fines up to KRW 30M apply after a grace period of at least one year (roughly Jan 2027, approximate).
  - A pending amendment would defer generative-AI labelling by three years; its passage was not confirmed.

  — [Korea Times](https://www.koreatimes.co.kr/amp/business/tech-science/20260129/industry-on-edge-as-ai-basic-act-takes-effect); [PetaPixel](https://petapixel.com/2026/01/29/south-korea-launches-landmark-laws-requiring-labels-on-ai-generated-content/); [Tech Policy Press](https://www.techpolicy.press/south-korea-may-regret-being-first-with-new-ai-law/); [ELBA Corp](https://www.elbacorp.com/en/blog/ai-video-labeling-rules-guide); [Folio](https://www.folioapp.co.uk/story/7?date=2026-05-17)
- UK:
  - Ofcom launched an enforcement programme expecting platforms to have hash matching for intimate image abuse, including AI deepfakes, by 30 Sept 2026.
  - Ofcom opened an investigation into X over Grok sexual deepfakes on 12 Jan 2026.
  - No Ofcom provenance or watermark guidance was found.

  — [Ofcom](https://www.ofcom.org.uk/online-safety/illegal-and-harmful-content/ofcom-to-crack-down-on-spread-of-illegal-intimate-images-and-deepfakes-boosting-protections-for-women-and-girls-online); [Ofcom roadmap](https://www.ofcom.org.uk/online-safety/illegal-and-harmful-content/roadmap-to-regulation); [bratby.law](https://bratby.law/ofcom-x-online-safety-act-enforcement/)
- UK creation offence: the Data (Use and Access) Act 2025 reportedly made creating or requesting non-consensual intimate deepfakes an offence from 6 Feb 2026. A reported 48-hour removal duty in a Crime and Policing Act 2026 is unverified. — [findcheapbroadband explainer (secondary)](https://findcheapbroadband.com/blog/ofcom-deepfake-intimate-image-rules/)
- Denmark:
  - The Copyright Act amendment gives people rights over realistic digital imitations of their face, voice and body, plus performer protection. It lasts 50 years after death, with satire and parody exceptions.
  - Earlier targets of 31 Mar 2026 and July 2026 slipped after a snap election. A bill was (re)introduced on 8 Oct 2026, aiming for effect around the turn of the year (single-source status).

  — [European Parliament EPRS briefing](https://www.europarl.europa.eu/RegData/etudes/ATAG/2026/782611/EPRS_ATA(2026)782611_EN.pdf); [Verfassungsblog](https://verfassungsblog.de/copyrighting-voice-and-image/); [Schjødt](https://schjodt.com/news/owning-the-self-denmarks-copyright-turn-against-deepfakes); [aipolicydesk](https://www.aipolicydesk.com/blog/denmark-deepfake-bill-faces-voices-consent-2026)

### Inferences
- The UK and Denmark create demand for detection, takedown and likeness-matching tools rather than for provenance marking.
- Korea adds a further jurisdiction where metadata or watermarking satisfies the law, with the timing risk of the deferral amendment.

### Gaps
- No primary text was found for the Korean Enforcement Decree or the UK Acts. The UK Online Safety Act's own provisions on AI labeling were not found.

## 6. Do any laws require or encourage capture-device authenticity marking of real media?

### Takeaway
Yes, but only one enacted law: California AB 853. From 1 Jan 2028 it requires capture-device makers to offer a latent provenance disclosure option on new devices sold in California. It is an opt-in option for users, not a mandatory signature on every capture. All other regimes found (EU Art 50 and Code, China, India, Korea) mark synthetic content only, or label content on platforms.

### Cited Findings
- AB 853 requires capture-device makers (cameras, phones, voice recorders) to provide a user option for a latent disclosure, including the manufacturer name, on devices first produced for sale in California on or after 1 Jan 2028. — [Sidley-hosted AB 853 text](https://www.sidley.com/en/-/media/resource-pages/ai-monitor/laws-and-regulations/cal-ab853-california-ai-transparency-act.pdf?la=en); [Orrick](https://infobytes.orrick.com/2025-10-17/california-delays-its-ai-transparency-act-and-passes-new-content-laws/)
- Large platforms must detect and surface provenance data from 1 Jan 2027, so signed authentic content would be read and displayed downstream. — [Vensure](https://dev2.vensure.com/employment-law-updates/california-ai-transparency-act-new-disclosure-and-detection-requirements-for-ai-content/)
- India's October 2026 advisory reportedly extends labelling beyond synthetic content. Its scope is unclear and it is not a capture-side requirement. — [MediaNama](https://www.medianama.com/2026/10/223-meity-labelling-social-media-synthetic-content/)

### Inferences
- The case for authentic-media provenance rests on California's 2027–2028 deadlines and on evidence-rule pressure (draft FRE 901(c)), not on EU or Asian mandates. Provenance vendors serving device makers and platforms have a fixed date to plan around.

### Gaps
- No law outside California mandating or incentivising camera-side signing was found. EU, UK and Korean proposals were not found in this search.
