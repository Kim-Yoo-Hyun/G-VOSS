# Figure Layout Review

Last updated: 2026-07-19 KST

Status: `current_camera_ready_figures_verified`

## Review Basis

The comparison used the accepted AAAI papers stored under
`paper/reference_AAAI/` and official proceedings versions of adjacent
top-tier vision papers:

- Kim, Lee, and Kwak, *Improving Target Presence and Plurality Recognition for
  Generalized Referring Image Segmentation*, AAAI 2026, local reference PDF.
- Kang, Mun, and Han, *Towards Oracle Knowledge Distillation with Neural
  Architecture Search*, AAAI 2020, local reference PDF.
- Jung et al., *Real-Time Object Tracking via Meta-Learning: Efficient Model
  Adaptation and One-Shot Channel Pruning*, AAAI 2020, local reference PDF.
- Yu et al., *Open-World 3D Scene Graphs for Zero-Shot Reasoning*, AAAI 2026:
  https://ojs.aaai.org/index.php/AAAI/article/download/37391/41353
- Feng et al., *3D Spatial Multimodal Knowledge Accumulation for Scene Graph
  Prediction in Point Clouds*, CVPR 2023:
  https://openaccess.thecvf.com/content/CVPR2023/papers/Feng_3D_Spatial_Multimodal_Knowledge_Accumulation_for_Scene_Graph_Prediction_in_CVPR_2023_paper.pdf
- Wang et al., *OED: Towards One-stage End-to-End Dynamic Scene Graph
  Generation*, CVPR 2024:
  https://openaccess.thecvf.com/content/CVPR2024/papers/Wang_OED_Towards_One-stage_End-to-End_Dynamic_Scene_Graph_Generation_CVPR_2024_paper.pdf

The accepted examples do not impose one visual template. Their shared pattern
is semantic economy: white page background, containers around actual modules
or branches, a limited stream palette, short labels, consistent sans-serif
type, and qualitative panels dominated by visual evidence rather than interface
chrome.

## Diagnosis of the Previous Draft

- Figure 1 used nested tinted regions, many border colors, long explanatory
  labels, and repeated output cards. The hierarchy was visually heavier than
  the scientific distinction among predicate semantics, pair measurements,
  source relation score, compatibility, and re-ranking.
- Figure 3 resembled a diagnostic dashboard: large cards and colored panel
  fields competed with the point clouds, while evidence and rank changes were
  too small at final two-column scale.
- Figure 2 already followed a conventional quantitative-plot structure. Its
  main issue was typographic inconsistency with the manuscript, not the chart
  composition.
- Rasterized or fallback system fonts were the likely source of the apparent
  broken/odd type. Editable SVGs now use TeX Gyre Heros/Helvetica-compatible
  typography, while the manuscript imports high-resolution PNGs to avoid
  CID/Identity-H font dependencies.

## Implemented Decisions

| Figure | Final design decision | Rationale |
| --- | --- | --- |
| Figure 1 | Three white panels separated by thin rules; boxes only around the input, compatibility, product, and family-aware re-ranking modules | Preserves the failure-to-method flow without turning the overview into a colored infographic |
| Figure 2 | Keep the three predictor trajectories; unify typography, percentage axes, marker shapes, and restrained Source/RelCompat3D colors | The plot already carries the strongest quantitative relationship and benefits from minimal intervention |
| Figure 3 | Unboxed three-column point-cloud/evidence/outcome grid with shared baselines and thin separators | Makes measured geometry and rank changes primary; the residual case remains visibly distinct without a warning card |
| Teaser | Pair-level Top-50 exchange with one relation leaving and one entering; retain the later full-width framework figure | Separates an illustrative outcome from the method mechanism; the teaser variant omits only the overlapping qualitative grid to preserve the seven-page technical limit |

The shared palette is limited to subject vermillion, object blue, RelCompat3D
teal, residual ochre, and neutral gray. Identity is also encoded by point shape
and box line style so color is not the sole carrier. Gradients, shadows, large
pastel panel fills, decorative icons, and reviewer-process language are absent.

## Verification

- Canonical Figure 1--3 and teaser manuscript assets are 2,400-pixel PNGs with
  at least 300 ppi effective resolution; compiled PDFs contain no Type 3, CID,
  or Identity-H fonts.
- The default and teaser manuscripts are 9-page US-Letter PDFs; technical
  content ends on page 7 and pages 8--9 contain references only.
- No unresolved references/citations, overfull boxes, LaTeX errors, or blocking
  build warnings remain.
- The redesign changes no cases, scores, ranks, metric values, or scientific
  claims. Exact content and redraw constraints are owned by
  `paper/figures.md`.
