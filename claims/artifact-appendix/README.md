# Artifact Appendix draft

This directory contains the English appendix based on the supplied CCS 2026 AE
template. It documents the current implementation and scripts, not a proposed
future workflow. No protocol or benchmark changes are required by this document.

- `main.tex`: standalone document, author names, and submission metadata.
- `appendix.tex`: appendix body for editing or inclusion in the paper.
- `artifact-appendix.pdf`: compiled two-page preview.

## Before submission

Replace the five `TODO` macros in `main.tex`: download URL, archival DOI,
evaluated release/commit, contact email, and paper ID. Confirm the author block
and supply affiliations when integrating this appendix into the paper.
No availability or evaluation badge is claimed by this draft.

The evaluation scope is our entries in Tables 2 and 3 plus the correctness
suite. Baseline reruns, production security, and two-host network evaluation
are not claimed. Resource and time budgets are planning estimates from the
existing measurements; this documentation task does not rerun the full matrix.

Before depositing a release, include `claims/` and the accepted paper PDF in
the source package. Freeze and test the exact release before filling in its
identifier and DOI.

## Build

With a TeX installation containing `acmart`, `paralist`, `listings`, and `xurl`:

```bash
cd claims/artifact-appendix
latexmk -pdf main.tex
```

Alternatively, upload the two `.tex` files to Overleaf and select `main.tex`,
or run `tectonic main.tex`. Recheck the two-page limit after replacing metadata
or integrating into the paper. The supplied preview was compiled with Tectonic;
TeX tools are only needed to edit this document, not to run the FPSI artifact.

## References and provenance

Research notes and downloaded reference material are in
`others/ccs2025-ae-reference/` (local, git-ignored, excluded from releases).
That collection explicitly distinguishes standalone Artifact Appendices from
repository READMEs and ordinary paper appendices. ACM access restrictions
prevented retrieving standalone appendices for the selected cryptography papers;
the draft uses their public artifact documentation and an accessible CCS 2025
appendix as complementary references, not as interchangeable evidence.

The mandatory section organization and Version sentence follow
`others/ccs2026-ae-template.zip`. The supplied template attributes its lineage
to the CCS 2026/2025/2024, USENIX Security 2023, and EuroSys 2022 AE templates,
and the original Grigori Fursin/Bruce Childers template under CC BY 4.0.
The original ZIP is unchanged. The appendix's project-specific prose is new.
