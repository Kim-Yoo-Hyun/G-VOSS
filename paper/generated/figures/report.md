# Draft Figure Generation

Status: `draft_figures_generated_verified`

Generated outputs:

- `figure1_framework.svg`: method/framework schematic.
- `figure2_tradeoff.svg`: two-panel R@100 / Violation@100 tradeoff.
- `figure3_failure_cases.svg`: Open3DSG qualitative row-card panels.
- `figure2_data.json`: extracted numeric values used for Figure 2.
- `figure3_cases.json`: extracted case rows used for Figure 3.
- `validation.json`: source-lock value and case-ID validation.
- `layout_review.md`: top-tier novelty/layout review, written after generation.

Validation rules:

- Verify Figure 2 values against `paper/figures.md`, Table 1, and Open3DSG `metrics.json`.
- Verify Figure 3 case IDs against `paper/figures.md` and Open3DSG `inspection.json`.
- Treat all SVGs as draft manuscript figures, not camera-ready final artwork.
