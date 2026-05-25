# Figure Conversion Notes

The manuscript source currently expects converted PDF figures:

- `../generated/figures/figure1_framework.pdf`
- `../generated/figures/figure2_tradeoff.pdf`
- `../generated/figures/figure3_geometry_panels.pdf`

The tracked source figures currently exist as SVG:

- `../generated/figures/figure1_framework.svg`
- `../generated/figures/figure2_tradeoff.svg`
- `../generated/figures/figure3_geometry_panels.svg`

This host currently lacks `pdflatex`, `latexmk`, `rsvg-convert`, and `inkscape`,
so the PDF conversion/build was not run. The LaTeX source uses visible
placeholders when converted figure files are missing.

