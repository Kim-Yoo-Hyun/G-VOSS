# Draft Figure Generation

Status: `draft_figures_generated_verified`

Generated outputs:

- `figure1_framework.svg`: method/framework schematic.
- `figure2_tradeoff.svg`: two-panel R@100 / Violation@100 tradeoff.
- `figure3_failure_cases.svg`: Open3DSG qualitative row-card panels.
- `figure3_geometry_panels.svg`: geometry-backed point-cloud panels for the
  same locked Open3DSG cases; preferred Figure 3 draft after the layout review.
- `figure2_data.json`: extracted numeric values used for Figure 2.
- `figure3_cases.json`: extracted case rows used for Figure 3.
- `figure3_geometry_cases.json`: source paths, object geometry stats, and
  measurements used for the geometry-backed Figure 3.
- `validation.json`: source-lock value and case-ID validation.
- `layout_review.md`: top-tier novelty/layout review, written after generation.
- `figure3_geometry_manifest.json`: geometry-backed Figure 3 generation
  manifest.
- `figure3_geometry_report.md`: geometry-backed Figure 3 reproduction report.

Validation rules:

- Verify Figure 2 values against `paper/figures.md`, Table 1, and Open3DSG `metrics.json`.
- Verify Figure 3 case IDs against `paper/figures.md` and Open3DSG `inspection.json`.
- Verify geometry-backed Figure 3 case IDs against `figure3_geometry_manifest.json`
  and parse the upgraded SVG as XML.
- Treat all SVGs as draft manuscript figures, not camera-ready final artwork.
