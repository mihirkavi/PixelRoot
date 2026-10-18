# Submitting PixelRoot to arXiv and IEEE TIFS

Target journal: **IEEE Transactions on Information Forensics and Security** (regular
paper), formatted with the `IEEEtran` journal class. The same sources produce the
arXiv preprint.

## 1. Build everything

```
cd paper/submission
bash make_bundle.sh
```

It compiles each bundle from a clean copy and fails on unresolved references.
Outputs in `paper/submission/dist/`:

| File | Use |
|---|---|
| `pixelroot.pdf` | IEEE "Main Document – PDF" slot; also the PDF to proof-read |
| `pixelroot_submission.zip` | IEEE "Main Manuscript" (LaTeX) slot: `pixelroot.tex`, `references.bib`, `pixelroot.bbl`, `figures/`, `contracts/src/PixelRootRegistry.sol` |
| `pixelroot_arxiv.tar.gz` | arXiv upload: the same sources with the `.bbl` instead of the `.bib` (arXiv does not run BibTeX); verified to compile with pdfLaTeX alone |
| `pixelroot_supplementary.zip` | Optional supplementary material: experiment code, results, contract and tests (no image data) |

The cover letter (`cover_letter.tex` / `.txt`) and the conflict-of-interest
statement (`conflict_of_interest.tex` / `.txt`) are standalone; compile with
`pdflatex` if the portal wants PDFs.

## 2. Before you submit (decisions only you can make)

1. **Length.** The manuscript is about 21 two-column pages. IEEE Signal Processing
   Society journals have historically set about 10 pages as the standard length,
   with mandatory charges for every page beyond that (historically $220/page) and a
   hard ceiling. Check the current TIFS *Information for Authors* page. To fit
   without touching the blockchain or the device-identity layer, the independent
   review suggests moving to supplementary material: the manufacturing analysis
   M1–M3 with Figs. 2–5, the per-pixel localization layer (E3) and the PRNU baseline
   (E4); and dropping the step-by-step list, the micro-benchmark table, Listing 1
   and the Applications section. The arXiv version can stay long.
2. **Code availability.** The paper cites `https://github.com/mihirkavi/PixelRoot`.
   Make the repository public (or replace the URL with a Zenodo DOI) before
   submitting.
3. **Title.** The title says "Real-Time Blockchain Notarization"; the paper measures
   gas but not public-network latency (future work F4). Consider "Capture-Time" if
   reviewers object.
4. **References to verify by hand** (details could not be checked from primary
   sources in this environment): `gowal2025synthid`, `yang2024steganalysis`,
   `fernandez2024videoseal`, `c2pa2026security`, `prnubench2025`, `tugofwar2024`,
   `resemble2025threat`, `surfshark2025fraud`, `ironscales2025`, and the other
   2025–2026 web sources. Also consider citing the Digimarc patents on in-sensor
   watermarking (e.g. "Digital watermarking CMOS sensor") once you confirm their
   numbers and status.
5. **Reproduce on your machine** (optional but recommended): `bash
   ../experiments/fetch_data.sh`, then run the scripts listed in
   `experiments/EXPERIMENT_PLAN.md`; every number in the paper is in
   `experiments/results/`.

## 3. arXiv

1. Create an account at arxiv.org (use an institutional or professional email if
   possible) and add your ORCID.
2. Primary category: **cs.CR** (Cryptography and Security); cross-list **cs.CV** and
   **eess.IV**. A first submission to cs.CR may need an **endorsement** from an
   established cs.CR author; arXiv shows the endorsement request link during
   submission. Allow a few days.
3. Upload `dist/pixelroot_arxiv.tar.gz`. arXiv compiles with pdfLaTeX and the
   bundle has been tested that way. Check the generated PDF carefully.
4. Metadata: copy the title, and paste the abstract as plain text (no LaTeX
   macros: write PixelRoot, 128-bit, Reed-Solomon, Q20, 78%, etc.). Comments field,
   for example: "21 pages, 8 figures, 9 tables. Submitted to IEEE Transactions on
   Information Forensics and Security. Code: https://github.com/mihirkavi/PixelRoot".
5. License: choose the **arXiv non-exclusive distribution license** (the default).
   It is compatible with later transferring copyright to IEEE. Avoid CC BY
   unless you plan to pay for open access.
6. IEEE allows posting the submitted version on arXiv. If the paper is accepted,
   update the arXiv entry with the IEEE copyright notice and the DOI, as IEEE's
   policy requires.

## 4. IEEE TIFS (IEEE Author Portal / ScholarOne)

1. Log in with your IEEE account and ORCID; choose *IEEE Transactions on
   Information Forensics and Security* → *Regular Paper*.
2. Pick EDICS / subject areas close to: multimedia forensics, watermarking and
   data hiding, hardware security, applied cryptography.
3. Upload slots:

| Portal slot | Required? | Upload |
|---|---|---|
| Main Manuscript (LaTeX) | Required | `dist/pixelroot_submission.zip` |
| Main Document – PDF | Required | `dist/pixelroot.pdf` |
| Conflict of Interest | Required | `conflict_of_interest.pdf` (compile the `.tex`) |
| Cover letter | Recommended | `cover_letter.pdf` (compile the `.tex`) |
| Supplementary Material for Review | Optional | `dist/pixelroot_supplementary.zip` |

4. In the cover letter / comments, mention the arXiv preprint and its identifier
   once you have it.
5. Check the current TIFS instructions on reviewer anonymity. If the portal asks
   for an anonymized manuscript, remove the author block, the PixelRoot project
   affiliation, and the GitHub URL, and rebuild the bundle.

## 5. What has been checked

- `make_bundle.sh` builds all three archives from scratch with no undefined
  citations or references; the arXiv tarball compiles with pdfLaTeX only.
- Contract: 18 Hardhat tests (`cd ../contracts && npm ci && npm test`).
- Python: 21 unit tests (`cd ../experiments && python3 -m pytest -q tests`).
- Every quantitative claim was audited against `experiments/results/` by an
  independent review pass; its findings were fixed in this version.
