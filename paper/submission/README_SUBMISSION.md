# IEEE TIFS submission checklist

Target: **IEEE Transactions on Information Forensics and Security** (regular paper).
Manuscript formatted with the standard `IEEEtran` **journal** class (two-column, 10 pt).

## What to upload to each IEEE Author Portal slot

| Portal slot | Required? | What to upload | Source in this repo |
|---|---|---|---|
| **Main Manuscript (LaTeX)** | Required | `pixelroot_submission.zip` (the LaTeX bundle) | built by `make_bundle.sh` |
| **Main Document – PDF** | Required | `pixelroot.pdf` (compiled, double-column) | `submission/pixelroot.pdf` |
| **Conflict of Interest** | Required | `conflict_of_interest.pdf` | compile `submission/conflict_of_interest.tex` (or use `.txt`) |
| Supplementary Material for Review | Optional | `pixelroot_supplementary.zip` (experiment scripts, plan, manufacturing notes) | built by `make_bundle.sh` |
| Main Document – Tracked Changes | Optional | skip for a first/new submission (only for revisions) | — |
| Image | Optional | not needed — all figures are embedded in the manuscript | `figures/*.pdf` |
| Previously Published – Statement/Files | Optional | not applicable (original, unpublished work) | — |
| Cover letter / Comments | Optional (recommended) | `cover_letter.pdf` | compile `submission/cover_letter.tex` (or use `.txt`) |
| LaTeX Supplementary File | Optional | not needed (no separate TeX supplement) | — |
| Supporting Documents | Optional | not applicable | — |

## Main Manuscript bundle contents (`pixelroot_submission.zip`)

A single archive is acceptable for the Main Manuscript slot. It contains:

- `pixelroot.tex` — the manuscript (`\documentclass[journal]{IEEEtran}`)
- `references.bib` — bibliography database
- `registry.sol` — Solidity listing pulled in via `\lstinputlisting`
- `figures/` — all six embedded figures as vector PDFs

`IEEEtran.cls` and `IEEEtran.bst` are **not** bundled because the IEEE production
system and Overleaf provide them. If you compile in a minimal local TeX install,
run `tlmgr install ieeetran` first.

### Compile order (produces the required `pixelroot.pdf`)
```
pdflatex pixelroot
bibtex   pixelroot
pdflatex pixelroot
pdflatex pixelroot
```
Or, with a self-contained engine (no system TeX needed):
```
tectonic -X compile pixelroot.tex   # runs BibTeX and all passes automatically
```
The portal has **two** required manuscript slots: upload the LaTeX bundle to
*Main Manuscript* and the compiled `pixelroot.pdf` to *Main Document – PDF*.

## Formatting compliance notes

- **Document class**: `\documentclass[journal]{IEEEtran}` (TIFS is a Transactions,
  two-column journal). The conference-only `\IEEEoverridecommandlockouts` has been
  removed; the author block uses the journal `\thanks{}` form.
- **Conflict of interest**: disclosed *inside* the manuscript (a `Conflict of
  Interest` section and an author `\thanks`) **and** provided as a separate
  document, as the portal requires both.
- **Index Terms**: present via `\begin{IEEEkeywords}`.
- **No supplementary material in the Main Manuscript**: experiment code and notes
  ship only in the optional supplementary archive.
- **Figures embedded**: all figures are `\includegraphics` of vector PDFs in
  `figures/`, so the separate "Image" slot is not required.
