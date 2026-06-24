# H001_v2 Source Evaluation Result

Last updated: 2026-06-24 KST

Status: `h001_v2_fixed_tau_diagnostic_candidate_locked`

This file records the fixed-threshold source evaluation and tau corruption
controls for H001_v2. It uses the frozen calibration-selected policy only:

- `tau* = 0.20`
- `p_geom_valid >= 0.80`
- `alpha = 0.05`
- `delta = 0.05`

No threshold was selected from VL-SAT or Open3DSG source metrics.

## Artifacts

VL-SAT:

```text
hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/source_eval/vlsat_full_validation/
```

Open3DSG:

```text
hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/source_eval/open3dsg_recovery_relaxed_views_min2/
```

Each source directory contains:

- `manifest.json`
- `metrics.json`
- `report.md`
- `selected_predictions.jsonl`
- `selection_summary.json`
- `commands.md`

The `metrics.json` and `report.md` files include `semantic_only`,
`probabilistic_recalibrated`, `rule_verified_point_subtype`,
`h001_v2_risk_controlled_pooled_tau`, `control_shuffled_geometry_tau`, and
`control_wrong_pair_geometry_tau`.

## VL-SAT Point Metrics

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| `probabilistic_recalibrated` | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `h001_v2_risk_controlled_pooled_tau` | 0.3797 | 0.5541 | 0.6772 | 0.7485 | 0.7666 | 0.0018 | 0.0077 | 0.0125 | 0.0249 | 0.0482 |
| `control_shuffled_geometry_tau` | 0.1954 | 0.2384 | 0.2659 | 0.2797 | 0.2842 | 0.0150 | 0.0188 | 0.0345 | 0.0956 | 0.1785 |
| `control_wrong_pair_geometry_tau` | 0.1684 | 0.2125 | 0.2477 | 0.2656 | 0.2704 | 0.0182 | 0.0252 | 0.0422 | 0.1078 | 0.1850 |

VL-SAT selection:

- in-scope predictions: `220,848`
- eligible predictions: `76,060`
- threshold-excluded predictions: `144,788`
- selected@100: `53,056`
- missing verification / missing `p_geom_valid`: `0 / 0`
- control eligible predictions: shuffled `76,060`, wrong-pair `74,685`

Interpretation:

- H001_v2 is not competitive with `probabilistic_recalibrated` on VL-SAT.
- It reduces violation slightly versus `semantic_only` at K=5/10/20/50, but
  recall drops strongly and V@100 is slightly worse than `semantic_only`.
- The tau controls are clearly worse than H001_v2 at every K: recall drops by
  18.43-49.62 pp and violation increases by 1.31-13.67 pp depending on K and
  control. This supports that the fixed-threshold policy is using real
  edge-level geometry rather than merely changing top-K capacity.
- This is a recall-collapse warning for the pooled fixed threshold.

## Open3DSG Point Metrics

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| `probabilistic_recalibrated` | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `h001_v2_risk_controlled_pooled_tau` | 0.0740 | 0.1740 | 0.3147 | 0.4436 | 0.5587 | 0.1307 | 0.0993 | 0.0806 | 0.0634 | 0.0667 |
| `control_shuffled_geometry_tau` | 0.0277 | 0.0584 | 0.0989 | 0.1526 | 0.2009 | 0.3724 | 0.2465 | 0.1943 | 0.1929 | 0.2042 |
| `control_wrong_pair_geometry_tau` | 0.0151 | 0.0423 | 0.0801 | 0.1347 | 0.1820 | 0.2816 | 0.1881 | 0.1604 | 0.1775 | 0.1955 |

Open3DSG selection:

- in-scope predictions: `160,596`
- eligible predictions: `59,078`
- threshold-excluded predictions: `101,518`
- selected@100: `46,298`
- missing verification / missing `p_geom_valid`: `0 / 0`
- control eligible predictions: shuffled `59,078`, wrong-pair `57,768`

Interpretation:

- H001_v2 is strong against `semantic_only` on Open3DSG: recall improves at all
  K and violation drops sharply at all K.
- Against `probabilistic_recalibrated`, the result is mixed: recall improves at
  K=10/20/50 but drops at K=5/100; violation is worse at K=5/10/20/50 and
  better only at K=100.
- The tau controls are clearly worse than H001_v2 at every K: recall drops by
  4.63-37.66 pp and violation increases by 7.98-24.17 pp depending on K and
  control. This is positive evidence that the Open3DSG gain is
  geometry-specific rather than a capacity artifact.
- This is promising as a diagnostic but not a clean method improvement over
  H001_v1.

## Current Judgment

Fact:

- The fixed-threshold runner is implemented and both source point metrics are
  generated under the H001_v2 artifact root.
- H001_v2-specific `control_shuffled_geometry_tau` and
  `control_wrong_pair_geometry_tau` are implemented and generated for both
  sources under the same artifact root.
- The path decision is fixed: this result is a diagnostic candidate, not a
  replacement for the current H001/GeoCalib main result.
- H001 locked source metrics, paper files, and result bundles were not modified.
- No-overwrite and read-only-root guards were tested.

Inference:

- H001_v2 should not be promoted to the current GeoCalib main paper table.
- The tau controls strengthen the geometry-specificity argument: replacing real
  edge geometry with shuffled or wrong-pair geometry degrades both recall and
  violation consistently on both sources.
- The pooled threshold is too conservative or misaligned for VL-SAT top-K
  recall, even though it gives useful Open3DSG semantic-only correction.
- The current paper should keep the existing H001/GeoCalib `semantic_score *
  p_geom_valid` style soft re-ranking and its current reported operating
  points.

## Locked Decision

- Use H001_v2 fixed-`tau*` results as diagnostic evidence only.
- Keep the current H001/GeoCalib main paper results unchanged.
- Do not add fixed-`tau*` rows to the main source-result table.
- Do not run fixed-`tau*` bootstrap unless the result is explicitly needed as
  appendix/supplement diagnostic evidence.

## Follow-Up Method Directions

These were the H001_v2-style directions after the fixed-threshold diagnostic.
The family-specific soft-risk route has since been formalized in
`11_family_conditional_risk_result.md`; the remaining open extension is
coverage-aware reporting.

| Direction | What it does | Why it is more promising than fixed hard tau |
| --- | --- | --- |
| `coverage-aware` | Treats covered, unsupported, missing, and uncertain geometry as explicit states instead of collapsing them into keep/drop behavior. A relation can retain semantic utility when geometry is not evaluable, but the output must expose coverage and uncertainty. | Avoids mistaking missing geometry for invalid geometry and makes recall loss attributable. Best used as a schema/reporting and fallback component. |
| `family-conditional calibrated risk` | Uses separate soft geometry-risk calibrators for `support_contact`, `proximity`, and `relative_vertical` rather than one pooled risk surface. | Different relation families have different geometry noise and violation priors; a pooled risk score can over-filter one family while under-controlling another. Formalized in `11_family_conditional_risk_result.md`. |
| `risk-aware soft reranking` | Replaces hard filtering with a continuous utility such as semantic utility minus a predeclared geometry-risk penalty, or semantic score weighted by calibrated validity with an explicit risk budget. | Preserves top-K recall better than hard thresholding while still penalizing high-risk geometry. This is the most natural H001_v2 successor if the method is reopened. |

Current priority after the family-conditional formalization:

1. Keep fixed-`tau*` as diagnostic only.
2. Treat `family_conditional_risk` as the selected H001_v2 method-development
   candidate.
3. Keep `coverage-aware` reporting as the next guardrail and fallback
   mechanism.

## Next TODO

1. No active H001_v2 source-metric rerun.
2. Completed follow-up: family-conditional calibrated risk is documented in
   `11_family_conditional_risk_result.md`.
3. Optional future work: design coverage-aware reporting/scoring so missing,
   unsupported, and uncertain geometry states remain explicit.
4. Do not change `tau*`, `alpha`, `delta`, or the K grid based on these source
   metrics.
