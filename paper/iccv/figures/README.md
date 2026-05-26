# Figure Conversion Notes

The manuscript source currently expects converted PNG figures:

- `../generated/figures/figure1_framework.png`
- `../generated/figures/figure2_tradeoff.png`
- `../generated/figures/figure3_geometry_panels.png`

The tracked source figures currently exist as SVG:

- `../generated/figures/figure1_framework.svg`
- `../generated/figures/figure2_tradeoff.svg`
- `../generated/figures/figure3_geometry_panels.svg`

This host currently lacks `pdflatex`, `latexmk`, `rsvg-convert`, and `inkscape`,
so PDF conversion/build was not run. PNG conversion was done with
`google-chrome --headless --screenshot` on 2026-05-25:

- `figure1_framework.png`: 1280 x 650
- `figure2_tradeoff.png`: 1280 x 620
- `figure3_geometry_panels.png`: 1280 x 910

The LaTeX source uses visible placeholders when converted figure files are
missing.
