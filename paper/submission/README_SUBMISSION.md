# Submitting PixelRoot to IEEE TIFS and arXiv

One source, two versions (switch `\ifshort` in `pixelroot.tex`):

| Version | Source | Pages | Used for |
|---|---|---|---|
| TIFS submission | `pixelroot_tifs.tex` (defines the switch and inputs `pixelroot.tex`) | 13, incl. references | IEEE TIFS main manuscript |
| Full (extended) | `pixelroot.tex` | 20 | arXiv preprint; TIFS supplementary material |

The TIFS version moves the manufacturing analysis (M1–M3, Figs. 2–5), the
per-pixel localization (E3) and PRNU (E4) experiments, the background, the
detailed related work and threat catalogue, the micro-benchmarks, the contract
listing and the applications section into the extended version. The blockchain,
the device-identity layer, all propositions and the E1/E2/E6 evaluation are in
both versions.

## 1. Build

```
cd paper/submission
bash make_bundle.sh
```

To regenerate the figures first: `bash ../figures/src/build.sh` (TikZ schematics)
and `python3 ../experiments/make_figures.py` (plots, from `experiments/results/`).

The script compiles both versions from a clean copy and fails if either has
unresolved references or if the TIFS version exceeds 13 pages. Outputs in `dist/`:

| File | Use |
|---|---|
| `pixelroot_tifs.pdf` | IEEE "Main Document – PDF" |
| `pixelroot_tifs_submission.zip` | IEEE "Main Manuscript" (LaTeX: `pixelroot_tifs.tex`, `pixelroot.tex`, `references.bib`, `pixelroot_tifs.bbl`, `figures/`, `contracts/src/…sol`) |
| `pixelroot_supplementary.zip` | IEEE "Supplementary Material": the extended version PDF, code, results, contract and tests |
| `pixelroot_arxiv.tar.gz` | arXiv upload: full version, `.bbl` instead of `.bib`; verified to compile with pdfLaTeX alone |
| `pixelroot_full.pdf` | what arXiv will render, for proofreading |

`arxiv_metadata.txt` and `arxiv_abstract.txt` hold the arXiv form fields. The
cover letter and conflict-of-interest statement are standalone (`.tex`/`.txt`).

## 2. Compliance check (verified 19 Oct 2026)

| Rule | Source | Status |
|---|---|---|
| TIFS regular paper: initial submission ≤ 13 double-column pages at 10 pt, **including** references; revised ≤ 16 | IEEE SPS *Information for Authors* | **Met**: 13 pages (enforced by the build) |
| Single-spaced, double-column submission | SPS AE guidelines | Met (`IEEEtran` journal) |
| Mandatory overlength charges beyond 10 *published* pages ($220/page in the SPS page) | SPS *Information for Authors* | Applies if accepted: 13 pages → about 3 overlength pages |
| Abstract 150–250 words, index terms | IEEE journal template | Met (245 words; 10 index terms) |
| Disclose AI-generated content in the acknowledgments: system, sections, extent | IEEE PSPB Operations Manual 8.2.1.B.10 | **Met**: Acknowledgment names Claude (Anthropic), the sections and the extent. **You must review and confirm it** (§3) |
| Authors take responsibility; AI cannot be an author; significant AI use reported | arXiv policy (Jan 2023) | Met: same disclosure in the arXiv version; sole human author |
| Preprint posted before acceptance carries IEEE's submission notice | IEEE preprint policy | **Met**: arXiv version's first-page footnote has the exact notice |
| After acceptance: add IEEE copyright notice; after publication: add DOI / full citation | IEEE preprint policy | To do later |
| Conflict-of-interest statement | TIFS portal | Met (in paper and as a separate file) |
| Fonts embedded, no Type 3 | IEEE PDF requirements | Met (all fonts embedded and subset, none Type 3; checked by `pdffonts`) |
| Figures legible at print size, no overlaps | IEEE graphics guidelines | Met: schematics are TikZ sources in `figures/src/` drawn at printed size in Times; plots and the photo figure come from `experiments/make_figures.py` (photo panels ≥ 300 dpi) |
| arXiv: TeX source, pdfLaTeX, `.bbl` named like the main file, allowed filename characters, figures included (PDF/PNG) | arXiv submission help | Met (checked by the build) |
| arXiv CS: review/position papers need prior peer review | arXiv blog, 31 Oct 2025 | Not applicable: original research with new system, code and experiments (state this if a moderator asks) |
| arXiv abstract ≤ 1,920 characters, plain text | arXiv form | Met: 1,468 characters (`arxiv_abstract.txt`) |

## 3. You must do these (they cannot be done for you)

1. **Read and confirm the AI disclosure** (Acknowledgment, both versions). It
   states that Claude drafted and revised text, wrote and ran code, and checked
   numbers, and that you directed and reviewed everything. Edit it if any part is
   inaccurate (for example, if AI was also used in earlier drafts), and actually
   review the AI-written sections before submitting: you take responsibility for
   every claim.
2. **Make the code public**: the paper cites `https://github.com/mihirkavi/PixelRoot`.
   Make it public (or archive a release on Zenodo and cite the DOI).
3. **Accounts**: IEEE Author Portal account with ORCID; arXiv account (endorsement
   may be required for a first cs.CR submission).
4. **Order**: submit to TIFS first (or the same day), then post on arXiv; add the
   arXiv identifier to the TIFS submission comments.
5. **Proofread** `dist/pixelroot_tifs.pdf` and `dist/pixelroot_full.pdf` end to end.

## 4. arXiv steps

1. Start a new submission; license: *arXiv.org perpetual, non-exclusive license*.
2. Categories: primary **cs.CR**; cross-list **cs.CV**, **eess.IV**.
3. Upload `dist/pixelroot_arxiv.tar.gz`; process; check the rendered PDF matches
   `dist/pixelroot_full.pdf` (20 pages).
4. Paste the fields from `arxiv_metadata.txt` and the abstract from
   `arxiv_abstract.txt`.

## 5. IEEE TIFS steps (IEEE Author Portal)

1. Select *IEEE Transactions on Information Forensics and Security* → *Regular Paper*.
2. Upload:

| Portal slot | Upload |
|---|---|
| Main Manuscript (LaTeX) | `dist/pixelroot_tifs_submission.zip` |
| Main Document – PDF | `dist/pixelroot_tifs.pdf` |
| Conflict of Interest | `conflict_of_interest.pdf` (compile the `.tex`) |
| Cover letter | `cover_letter.pdf` (compile the `.tex`) |
| Supplementary Material for Review | `dist/pixelroot_supplementary.zip` |

3. Choose subject areas near: multimedia forensics; watermarking and data hiding;
   hardware security; applied cryptography and blockchain.
4. Check the portal's instructions on reviewer anonymity; if an anonymized
   manuscript is required, remove the author block and the GitHub URL and rebuild.

## 6. Already verified in this repository

- Contract: 18 Hardhat tests (`cd ../contracts && npm ci && npm test`).
- Python: 21 unit tests (`cd ../experiments && python3 -m pytest -q tests`).
- Every number in both versions comes from `experiments/results/`; an independent
  review pass audited them (`reports/PixelRoot independent review.md`).
- References: the entries an earlier pass could not verify (SynthID-Image,
  Video Seal, the steganalysis/averaging paper, the C2PA security analysis) were
  checked against arXiv and IACR ePrint listings.
