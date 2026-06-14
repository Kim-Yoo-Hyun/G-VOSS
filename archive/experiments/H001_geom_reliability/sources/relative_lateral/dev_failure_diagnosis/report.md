# Relative Lateral Dev Failure Diagnosis

Status: `relative_lateral_dev_failure_diagnosis_ready_no_policy_change_no_source_metrics`
Created at: `2026-06-06T08:04:08.262357+00:00`

## Boundary

This diagnosis reads the frozen train/dev policy-lock rows only. It does
not change the policy, does not read source predictions, does not compute
source metrics, and does not change the paper claim.

## Counts

| Item | Count |
|---|---:|
| dev GT-positive rows | 378 |
| positive strict contradiction rows | 72 |
| positive strict contradiction physical pairs | 36 |
| positive strict contradiction same-label share | 0.5278 |
| positive uncertain rows | 140 |
| positive uncertain physical pairs | 70 |
| positive uncertain same-label share | 0.4857 |
| all focus rows including counterfactual mirrors | 424 |
| all focus physical pairs | 106 |

## Bucket Summary

| Bucket | Rows | Physical pairs | Same-label share | Top reasons | Top projection support |
|---|---:|---:|---:|---|---|
| `positive_strict_contradiction` | 72 | 36 | 0.5278 | `no_strict_ambiguity_flag:72` | `lateral_sign_contradicts_label:72` |
| `positive_uncertain` | 140 | 70 | 0.4857 | `axis_margin_ambiguous:10, axis_margin_ambiguous+conflicting_axis_dominates:46, axis_margin_ambiguous+conflicting_axis_dominates+strong_projected_overlap:2` | `lateral_sign_contradicts_label_with_strict_ambiguity:14, lateral_sign_supports_label_but_strict_ambiguity:64, other:62` |
| `counterfactual_false_satisfaction` | 72 | 36 | 0.5278 | `no_strict_ambiguity_flag:72` | `lateral_sign_supports_label:72` |
| `counterfactual_uncertain` | 140 | 70 | 0.4857 | `axis_margin_ambiguous:10, axis_margin_ambiguous+conflicting_axis_dominates:46, axis_margin_ambiguous+conflicting_axis_dominates+strong_projected_overlap:2` | `lateral_sign_contradicts_label_with_strict_ambiguity:64, lateral_sign_supports_label_but_strict_ambiguity:14, other:62` |

## Interpretation

- Strict contradictions are symmetric left/right sign conflicts at pair level, not random row noise.
- Strict contradictions are concentrated in two dev scans and about half involve same-label object pairs such as pillow-pillow or box-box.
- Most uncertain rows are not sign failures; they are caused by conflicting orthogonal-axis dominance, meaning the pair is more front/back separated than laterally separated under the frozen scan frame.
- Uncertain rows also contain many repeated-object cases, so a visual/frame-metadata study would be needed before treating this as broadly valid lateral evidence.
- The dev split is therefore a coordinate/frame-orientation boundary case for lateral promotion, not a source-prediction metric issue.

## Recommendation

- Do not promote `relative_lateral` to main claim from the current strict
  policy-lock result.
- Do not tune the frozen validation policy to fix this dev split.
- If this family is kept, frame it as caveated appendix evidence or run
  a separate predeclared frame/annotation study before source metrics.
