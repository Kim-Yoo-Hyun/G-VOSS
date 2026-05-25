# H001 Figure Source Lock

Last updated: 2026-05-22 KST

Status: `figure3_geometry_upgrade_generated`

This file locks the paper-facing source claims and data artifacts for Figure
1-3 before drawing. It is a planning artifact, not a generated figure output.
It supersedes the older generated `figure_specs.md` source note where it
conflicts, especially for Figure 3.

Generated draft outputs and the geometry-backed Figure 3 upgrade are available
under `paper/generated/figures/`. They are manuscript-planning figures, not
camera-ready final artwork.

## Global Rules

- Figures must support the scoped relation-reliability claim only.
- Do not use figures to claim broad open-vocabulary 3DSSG generation
  improvement, arbitrary-baseline generality, or exact non-averaged Open3DSG
  reproduction.
- Figure captions must report recall and violation jointly when showing
  performance.
- Open3DSG visual or metric content must retain the averaged-BLIP,
  filtered-train/dev, covered-scope, exact-label denominator,
  `validation_missing_preprocessed:11`, and residual-calibration caveats.
- Qwen-VL does not appear in Figure 1-3 unless it is promoted with full Docker
  metric, denominator, and audit treatment.

## Figure 1

Locked claim:

> Semantic relation rows need identity-preserving geometry evidence and
> calibrated geometry-consistency scoring before they can be used as reliable
> relation predictions.

Locked visual form:

- Method/framework diagram.
- No numerical result claim.
- Show the pipeline:
  `relation source predictions` -> `standardized row contract` ->
  `identity-preserving geometry join` -> `family-specific verifier` ->
  `p_geom_valid calibration` -> `probabilistic / rule-verified /
  family-specific operating points` -> `R@K + Violation@K evaluation`.

Source artifacts:

- `paper/draft.md`, Sections 3-4.
- `hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`.
- `experiments/H001_geom_reliability/manifest.lock.json`.

Caption constraint:

- Use "calibrated geometry-consistency evaluation and re-ranking framework."
- Do not call the method a verifier script.

## Figure 2

Locked claim:

> Geometry-consistency re-ranking changes the recall-violation operating point;
> useful settings must be evaluated by recall and violation together.

Locked visual form:

- Two-panel recall-violation tradeoff plot using `R@100` and `Violation@100`.
- Panel A: primary `VL-SAT` result from Table 1.
- Panel B: Open3DSG second-source result from Docker metrics.
- Use separate panel axes or clear panel labels, because absolute recall is not
  directly comparable across the closed-set VL-SAT source and the reproduced
  averaged-BLIP Open3DSG variant.
- Draw arrows from `semantic_only` to `probabilistic_recalibrated`,
  `family_specific_p_geom_valid`, and `rule_verified_point_subtype`.
- Lower `Violation@100` is better; higher `R@100` is better.

Locked data:

| source | condition | R@100 | Violation@100 |
| --- | --- | ---: | ---: |
| VL-SAT | `semantic_only` | 0.9894 | 0.0469 |
| VL-SAT | `probabilistic_recalibrated` | 0.9921 | 0.0391 |
| VL-SAT | `family_specific_p_geom_valid` | 0.9914 | 0.0310 |
| VL-SAT | `rule_verified_point_subtype` | 0.9890 | 0.0000 |
| Open3DSG | `semantic_only` | 0.4963 | 0.1195 |
| Open3DSG | `probabilistic_recalibrated` | 0.5580 | 0.0803 |
| Open3DSG | `family_specific_p_geom_valid` | 0.5984 | 0.0311 |
| Open3DSG | `rule_verified_point_subtype` | 0.5238 | 0.0000 |

Source artifacts:

- `experiments/H001_geom_reliability/tables/table1_main_prediction.md`.
- `experiments/H001_geom_reliability/tables/table1_main_prediction.json`.
- `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json`.
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`.

Caption constraint:

- State that Open3DSG is a Docker-reproduced averaged-BLIP second-source
  variant under the covered H001 scope, not a broad SOTA comparison.
- Do not hide Open3DSG caveats in appendix only.

## Figure 3

Locked claim:

> The failure mode is family-structured: semantic plausibility can conflict
> with proximity, vertical-order, or support/contact geometry, and residual
> calibration risk remains even after probabilistic re-ranking.

Locked visual form:

- Four evidence panels from traceable Open3DSG qualitative inspection rows.
- Current preferred draft is the geometry-backed point-cloud panel generated
  from Open3DSG preprocessed object payloads. The older row-card SVG remains a
  traceable fallback.
- If later upgraded to rendered scene crops, the render script must preserve
  these same case IDs.
- Do not mix VL-SAT visual sanity-check examples into the main Figure 3 unless
  the caption separates them from Open3DSG deterministic qualitative inspection.

Locked cases:

| panel | case | role | family | predicate | pair | semantic -> geometry rank | p_geom_valid | reason |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| A | `open3dsg_case_001` | proximity demotion | `proximity` | `close by` | heater -> trash can | 17 -> 263 | 0.2304 | `far_in_normalized_xy` |
| B | `open3dsg_case_005` | vertical demotion | `relative_vertical` | `higher than` | desk -> lamp | 25 -> 422 | 0.0019 | `vertical_order_contradicts_predicate` |
| C | `open3dsg_case_010` | support/contact demotion | `support_contact` | `lying on` | lamp -> side table | 21 -> 401 | 0.0248 | `positive_float_gap_large` |
| D | `open3dsg_case_007` | residual calibration risk | `relative_vertical` | `lower than` | chair -> floor | 339 -> 50 | 0.9994 | `vertical_order_contradicts_predicate` |

Source artifacts:

- `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`.
- `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.json`.
- `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/report.md`.
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`.
- `local_dataset/Open3DSG_staged/h001_runtime/output/datasets/OpenSG_3RScan/preprocessed/`
  for ignored preprocessed object point-cloud payloads used by
  `paper/scripts/render_figure3_geometry_panels.py`.

Caption constraint:

- Say this is qualitative reviewer-defense / failure-mechanism evidence.
- Do not report the 36-case queue as a representative human audit or a new
  metric.
- Include residual calibration risk: 10/36 sampled rule-violated cases have
  `p_geom_valid > 0.9`.

## Drawing Order

Completed:

1. Figure 2 was generated first from locked numeric values.
2. Figure 1 was generated as a clean framework schematic.
3. Figure 3 was generated as row-card evidence panels.
4. Figure 3 was upgraded to geometry-backed point-cloud panels for the same
   locked case IDs.

Generated files:

| file | role |
| --- | --- |
| `paper/generated/figures/figure1_framework.svg` | draft method/framework schematic |
| `paper/generated/figures/figure2_tradeoff.svg` | draft two-panel R@100 / Violation@100 tradeoff |
| `paper/generated/figures/figure3_failure_cases.svg` | draft Open3DSG qualitative row-card panels |
| `paper/generated/figures/figure3_geometry_panels.svg` | preferred draft Open3DSG geometry-backed failure panels |
| `paper/generated/figures/figure2_data.json` | extracted values used for Figure 2 |
| `paper/generated/figures/figure3_cases.json` | extracted case rows used for Figure 3 |
| `paper/generated/figures/figure3_geometry_cases.json` | geometry measurements and source paths for upgraded Figure 3 |
| `paper/generated/figures/manifest.json` | generation manifest |
| `paper/generated/figures/validation.json` | source-lock validation |
| `paper/generated/figures/report.md` | generation report |
| `paper/generated/figures/layout_review.md` | layout and top-tier novelty review |
| `paper/generated/figures/figure3_geometry_manifest.json` | generation manifest for geometry-backed Figure 3 |
| `paper/generated/figures/figure3_geometry_report.md` | geometry-backed Figure 3 report |

## Validation Checklist

- Figure 1 has no unbacked performance claim.
- Figure 2 values match Table 1 and Open3DSG `metrics.json`.
- Figure 2 separates VL-SAT and Open3DSG panels and keeps Open3DSG caveats.
- Figure 3 uses the locked case IDs above.
- Captions do not use broad SOTA, baseline-agnostic, or exact non-averaged
  Open3DSG language.

Validation result:

- `paper/generated/figures/validation.json`: `passed`
- SVG XML parse: `passed` for Figure 1-3
- Layout/top-tier novelty review: `passed_with_figure3_geometry_upgrade`
- Geometry-backed Figure 3 manifest: `figure3_geometry_panels_generated_verified`
- Geometry-backed Figure 3 SVG XML parse: `passed`
- Next: review `paper/draft.md` section structure and decide whether Section 5 should remain separate or merge into a shorter Experimental Setup section

## Layout And Novelty Review

Decision:

- Figure 1: keep revised draft. It now shows failure mechanism -> cause ->
  design necessity before the framework pipeline.
- Figure 2: keep draft. It is the strongest evidence figure because it directly
  shows the recall-violation tradeoff.
- Figure 3: use the geometry-backed point-cloud panel as the preferred draft.
  It keeps the same locked case IDs and is stronger than the row-card fallback.
  A later scene-crop upgrade is optional only if a deterministic crop/render
  path is added.

Review record:

- `paper/generated/figures/layout_review.md`
