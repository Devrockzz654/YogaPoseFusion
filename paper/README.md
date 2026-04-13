# IEEE Conference Paper Draft

This folder contains a publication-ready IEEE-style LaTeX draft for YogaPoseFusion.

## Files
- `main.tex`: full manuscript in `IEEEtran` conference format.
- `references.bib`: bibliography entries used by the draft.

## Build
From `/Volumes/Dev/Project2/YogaPoseFusion/paper`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If you use `latexmk`:

```bash
latexmk -pdf main.tex
```

## Before Submission
- Replace placeholder author block in `main.tex`.
- Update affiliations and emails.
- Add conference-specific paper ID/copyright blocks if required.
- Verify references and formatting against your target venue CFP.
- Optionally add qualitative figures (overlay screenshots, UI snapshots, confusion matrix image).
