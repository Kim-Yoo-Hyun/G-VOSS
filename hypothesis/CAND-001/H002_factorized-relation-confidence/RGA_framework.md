# H002 RGA Framework

Last updated: 2026-06-13

## Purpose

`RGA(Relation-Geometric Agreement)`는 H002의 핵심 benchmark/diagnostic
framework다. 목표는 3D Scene Graph relation edge의 reliability를 단일 confidence로
보지 않고, semantic evidence와 geometry evidence가 서로 일치하는지 relation-level로
분해해 측정하는 것이다.

핵심 질문:

```text
Does semantic plausibility agree with geometric satisfiability?
```

RGA는 scoring model이 아니다. `p_geom_valid`를 다른 이름으로 바꾼 것도 아니다.
RGA는 relation candidate를 semantic axis, geometry axis, label axis, coverage axis,
uncertainty axis 위에 배치하고, 기존 label-recall metric이나 geometry-only violation
metric이 숨기는 mismatch state를 드러내는 framework다.

## Core View

H002의 출발점은 다음 분리다.

```text
semantic score != geometry validity != relation reliability
```

따라서 relation edge `e = (subject, predicate, object)`에 대해 RGA는 다음 joint state를
기록한다.

```text
RGA(e) = {
  semantic_axis(e),
  geometry_axis(e),
  label_axis(e),
  coverage_state(e),
  uncertainty_state(e),
  disagreement_score(e)
}
```

이 프레임워크에서 중요한 failure/candidate는 양방향이다.

| Case | Meaning |
| --- | --- |
| high semantic + low geometry | semantic overconfidence; source trusts a relation that geometry contradicts |
| low semantic + high geometry | semantic underconfidence, missed relation, annotation sparsity, or ontology mismatch candidate |
| high semantic + uncertain geometry | source trusts a relation whose physical status cannot be decided |
| high semantic + unsupported geometry | current verifier cannot evaluate this relation family |

## Unit Of Analysis

RGA의 기본 단위는 aggregate metric이 아니라 identity-preserving prediction row다.

Required identity:

```text
source_id
scan_id
subgraph_id
subject_id
object_id
predicate_label
predicate_family
prediction_id
semantic_rank_in_subgraph
semantic_score_raw
semantic_score_norm
geometry_status
p_geom_valid, if available
label_match_status, if GT/audit matching is available
provenance
```

현재 H002 train pilot의 row artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
```

Count:

```text
118,560 prediction rows
```

## Evidence Axes

### 1. Semantic Axis

Semantic axis는 relation source가 해당 edge를 얼마나 그럴듯하게 보는지 나타낸다.
서로 다른 source의 raw score calibration이 다를 수 있으므로, H002의 primary metric은
rank 기반이다.

Default top-K:

```text
K = 50
K = 100
```

Definition:

```text
semantic_high_K(e) = semantic_rank_in_subgraph(e) <= K
semantic_low_K(e)  = semantic_rank_in_subgraph(e) > K
```

현재 train RGA에서는 cross-source 비교가 아니라 Open3DSG train pilot 내부 진단이므로
rank-normalized semantic score도 함께 기록한다.

```text
semantic_score_norm =
  1 - (rank_in_context - 1) / (context_prediction_count - 1)
```

Semantic axis가 답하는 질문:

```text
Did the relation source rank this edge highly?
```

### 2. Geometry Axis

Geometry axis는 관측된 3D evidence가 해당 relation predicate를 지지하는지 본다.
현재 H002는 H001에서 동결한 relation-family geometry verifier를 읽어서 사용한다.

H001 status to H002 status:

| H001 status | H002 geometry status |
| --- | --- |
| `satisfied` | `satisfied` |
| `violated` | `unsatisfied` |
| `uncertain` | `uncertain` |
| `unsupported` | `unsupported` |
| missing join | `missing` |

Important rule:

```text
RGA-HL/RGA-LH bucket is determined by deterministic geometry_status,
not by thresholding p_geom_valid.
```

`p_geom_valid`는 geometry-only continuous evidence다. H002에서는 다음 용도로만 쓴다.

- `geometry_only` baseline score.
- semantic-geometry continuous disagreement.
- later factorized reliability posterior의 geometry factor.

Geometry axis가 답하는 질문:

```text
Does observed 3D geometry support this relation predicate?
```

### 3. Label Axis

Label axis는 GT relation 또는 audit label과의 관계를 기록한다. RGA의 deployable
posterior input으로 쓰는 것이 아니라, train/evaluation supervision과 diagnostic
stratification에 사용한다.

Train pilot label states:

| Label Status | Meaning |
| --- | --- |
| `exact_match` | same subject/object/predicate exists in train GT |
| `family_match` | same pair has a same-family predicate |
| `pair_has_other_predicate` | same pair has another GT predicate |
| `no_gt_for_pair` | no GT relation for the directed object pair |

Label axis가 답하는 질문:

```text
Is this edge supported by the annotation ontology, and if not, what kind of mismatch is it?
```

### 4. Coverage Axis

Coverage axis는 geometry verifier가 해당 row를 평가할 수 있었는지 기록한다.

Coverage states:

| Geometry Status | Coverage State |
| --- | --- |
| `satisfied` | `covered_checkable` |
| `unsatisfied` | `covered_checkable` |
| `uncertain` | `covered_checkable_uncertain` |
| `unsupported` | `unsupported_family` |
| `missing` | `missing_geometry` |

Coverage axis가 필요한 이유:

- unsupported relation family를 invalid geometry로 오해하지 않기 위해서.
- missing geometry를 model failure로 오해하지 않기 위해서.
- top-K metric denominator를 명확히 하기 위해서.

Coverage axis가 답하는 질문:

```text
Was this edge actually evaluable by the current geometry policy?
```

### 5. Uncertainty Axis

Uncertainty axis는 geometry가 애매하거나 evidence가 부족한 경우를 valid/invalid에
강제로 넣지 않는다.

Uncertainty examples:

```text
geometry_status = uncertain
ambiguous relation-specific residual
low point/view evidence
semantic-geometry conflict
unsupported family under current verifier
```

Uncertainty axis가 답하는 질문:

```text
Should the framework make a hard keep/reject decision, or abstain/audit?
```

## RGA Buckets

RGA는 semantic axis와 geometry axis를 결합해 bucket을 만든다.

| Bucket | Semantic | Geometry | Interpretation |
| --- | --- | --- | --- |
| `RGA-HH` | high | satisfied | source trusts an edge that geometry supports |
| `RGA-HL` | high | unsatisfied | semantic overconfidence |
| `RGA-HU` | high | uncertain | high semantic but geometry cannot decide |
| `RGA-HM` | high | unsupported/missing | high semantic outside current geometry coverage |
| `RGA-LH` | low | satisfied | semantic underconfidence or missed/under-ranked candidate |
| `RGA-LL` | low | unsatisfied | low semantic and invalid geometry |
| `RGA-LU` | low | uncertain | low semantic with ambiguous geometry |
| `RGA-LM` | low | unsupported/missing | low semantic outside current geometry coverage |

When label evidence exists, RGA also records label-geometry buckets.

| Bucket | Label Axis | Geometry | Interpretation |
| --- | --- | --- | --- |
| `RGA-TP-GS` | exact label match | satisfied | label-correct and geometry-supported |
| `RGA-TP-GU` | exact label match | unsatisfied | label-correct but geometry-contradicted |
| `RGA-FP-GS` | no exact label match | satisfied | no label credit but geometry-supported |
| `RGA-FP-GU` | no exact label match | unsatisfied | no label credit and geometry-contradicted |
| `RGA-*-GC` | any label state | uncertain/unsupported/missing | coverage or uncertainty case |

이 label-geometry table이 중요한 이유는 label-centric metric과 geometry-centric metric이
서로 다른 질문을 하기 때문이다.

```text
label correctness asks: is this annotated as correct?
geometry satisfiability asks: is this physically supported by observed 3D evidence?
relation reliability asks: should this edge be trusted under both evidence types and coverage limits?
```

## Metrics

All RGA metrics report numerator and denominator. Unsupported/missing rows are
not silently dropped; they are reported as coverage.

### `RGA-HL@K`

High semantic / low geometry failure rate.

```text
RGA-HL@K =
  count(e in TopK_semantic and geometry_status = unsatisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This measures semantic overconfidence under checkable geometry.

### `RGA-valid@K`

Strict geometry-supported rate among semantically selected rows.

```text
RGA-valid@K =
  count(e in TopK_semantic and geometry_status = satisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

`uncertain` is not counted as valid.

### `RGA-nonviolated@K`

H001-compatible non-violation style rate.

```text
RGA-nonviolated@K =
  count(e in TopK_semantic and geometry_status in {satisfied, uncertain})
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This is reported only for comparison. It is less strict than `RGA-valid@K`.

### `RGA-uncertain@K`

Ambiguous geometry rate among semantically selected rows.

```text
RGA-uncertain@K =
  count(e in TopK_semantic and geometry_status = uncertain)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

### `RGA-coverage@K`

How much of the selected semantic top-K can be checked by the current geometry
policy.

```text
RGA-coverage@K =
  count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
  / count(e in TopK_semantic)
```

### `RGA-LH-tail@K`

Low semantic / high geometry candidate rate.

```text
RGA-LH-tail@K =
  count(e not in TopK_semantic and geometry_status = satisfied)
  / count(e not in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

Important interpretation:

```text
RGA-LH is not automatic graph promotion.
```

It must be audited because it can mean:

- true semantic underconfidence.
- annotation sparsity.
- ontology or predicate granularity mismatch.
- dense/trivial relation, especially `close by`.
- object-pair error.
- geometry artifact.

### Continuous Disagreement

RGA also records continuous mismatch using `semantic_score_norm` and `p_geom_valid`.

Overconfidence score:

```text
max(0, semantic_score_norm - p_geom_valid)
```

Underconfidence score:

```text
max(0, p_geom_valid - semantic_score_norm)
```

This continuous signal is useful for ranking audit candidates and later posterior
features, but it does not replace deterministic RGA buckets.

## Framework Pipeline

RGA is implemented as a staged framework.

### Stage 1. Train Source Contract

Document:

```text
18_train_source_contract.md
```

Purpose:

- select train-only Open3DSG pilot scope.
- avoid validation leakage.
- freeze 100 train subgraphs / 100 scans.
- preserve source provenance.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
```

### Stage 2. Source Prediction Export

Documents:

```text
19_train_raw_dump_runner.md
20_train_adapter_export.md
```

Purpose:

- run Open3DSG train pilot raw dump.
- adapt raw source predictions into identity-preserving H001/H002 prediction rows.
- fix provenance so prediction rows point to `relationships_train_pilot.json`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
```

Count:

```text
118,560 rows
```

### Stage 3. Geometry Join

Document:

```text
21_train_geometry_join.md
```

Purpose:

- attach H001 frozen geometry verifier outputs to each prediction row.
- preserve row identity.
- record deterministic geometry status and continuous `p_geom_valid`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/geometry/verification.jsonl
```

Current geometry status:

| Status | Rows |
| --- | ---: |
| `satisfied` | 12,285 |
| `uncertain` | 11,841 |
| `violated` / H002 `unsatisfied` | 3,234 |
| `unsupported` | 91,200 |

### Stage 4. RGA Row Construction

Document:

```text
22_train_rga_rows.md
```

Purpose:

- join prediction rows, geometry rows, and train GT subset.
- compute RGA buckets, label-geometry buckets, disagreement scores, coverage.
- keep `posterior_edge_valid = null`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
```

Primary train metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 2.35% | 3.87% |
| `RGA-valid@K` | 63.53% | 57.41% |
| `RGA-nonviolated@K` | 97.65% | 96.13% |
| `RGA-uncertain@K` | 34.12% | 38.71% |
| `RGA-coverage@K` | 3.40% | 12.14% |
| `RGA-LH-tail@K` | 44.78% | 44.32% |

Top100 denominator:

| Group | Total | Covered | Satisfied | Unsatisfied | Uncertain | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| top100 | 10,000 | 1,214 | 697 | 47 | 470 | 8,786 |
| tail > 100 | 108,560 | 26,146 | 11,588 | 3,187 | 11,371 | 82,414 |

### Stage 5. RGA Audit Seed

Document:

```text
23_train_rga_audit.md
```

Purpose:

- do not inspect all 11,588 LH rows manually.
- create compact audit seed.
- preserve strata by queue, family, rank band, and label status.

Audit seed:

| Queue | Source Rows | Seed Rows |
| --- | ---: | ---: |
| `HL` | 47 | 47 |
| `LH` | 11,588 | 170 |
| total | 11,635 | 217 |

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/audit_seed.jsonl
```

### Stage 6. Manual-Audit Preparation

Document:

```text
24_train_manual_audit.md
```

Purpose:

- generate contact sheets and mesh/instance links.
- assign machine-assisted working labels.
- keep human-confirmed labels separate.

Working label distribution:

| Working Label | Rows |
| --- | ---: |
| `ontology_mismatch` | 63 |
| `true_underconfidence` | 48 |
| `semantic_overconfidence` | 45 |
| `annotation_sparsity` | 28 |
| `uncertain_needs_visual_or_mesh` | 22 |
| `dense_relation_noise` | 11 |

Boundary:

```text
working label != paper-locked human annotation
human_confirmed_share = 0.0
```

### Stage 7. Factor Contract

Document:

```text
25_factor_contract.md
```

Purpose:

- connect RGA diagnostics to a later factorized reliability posterior.
- define target modes.
- freeze leakage rules.
- define main baselines.

Deployable posterior:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Oracle diagnostic only:

```text
P(R_e = 1 | S_e, L_e, G_e, C_e, U_e)
```

Main baseline set:

| Baseline | Feature Blocks |
| --- | --- |
| `semantic_only` | `S_e` |
| `geometry_only` | `G_e + C_e` |
| `semantic_plus_geometry` | `S_e + G_e` |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e + interactions` |

`L_e` is supervision/evaluation/oracle evidence only. It is not a deployable
input feature.

### Stage 8. Factor Dataset

Document:

```text
26_factor_dataset.md
```

Purpose:

- materialize deployable feature rows from train RGA rows.
- join audit targets without leaking label/audit evidence into deployable inputs.
- create strict and weak train-only smoke inputs.
- freeze the concrete files used by the next posterior smoke fitting step.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/deployable_features_all.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/strict_smoke.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/weak_smoke.jsonl
```

Counts:

| Artifact | Rows |
| --- | ---: |
| `deployable_features_all.jsonl` | 118,560 |
| `target_joined.jsonl` | 217 |
| `strict_smoke.jsonl` | 93 |
| `weak_smoke.jsonl` | 132 |

Boundary:

```text
no validation usage
no label/audit evidence in deployable feature blocks
no paper-level performance claim
```

### Stage 9. Factor Smoke

Document:

```text
27_factor_smoke.md
```

Purpose:

- run train-only smoke fitting for the four planned baseline views.
- check whether the current strict/weak targets are independent enough for
  posterior interpretation.
- report shortcut risk before any method claim.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/report.md
```

Main finding:

```text
status = ready_with_shortcut_caveat
```

Strict target is too close to the RGA bucket construction. The smoke therefore
validates the executable pipeline but does not validate posterior novelty.

### Stage 10. Shortcut Control

Document:

```text
28_shortcut_control.md
```

Purpose:

- remove target-construction shortcut feature groups.
- test whether strict/weak targets remain predictable after controls.
- decide whether posterior performance is interpretable.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/report.md
```

Main finding:

```text
status = ready_target_not_independent
```

The strict target remains perfectly predictable even with continuous-only
geometry evidence. This means the current target validates feature plumbing, not
posterior novelty.

### Stage 11. Target Redesign

Document:

```text
29_target_redesign.md
```

Purpose:

- replace shortcut-prone strict/weak targets.
- define within-geometry-supported reliability targets.
- separate relabel-only and abstain labels from binary reliability labels.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_contract.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
```

Main finding:

```text
status = ready_target_v2_contract
```

The primary target is `strict_proximity_informativeness`: geometry-satisfied
proximity rows only, with `true_underconfidence` as positive and
`dense_relation_noise` as negative. It has 16 positives and 11 negatives, so it
is a small plumbing-smoke target, not paper evidence.

### Stage 12. Redesigned Target Smoke

Document:

```text
30_redesigned_target_smoke.md
```

Purpose:

- test target v2 with direct target identity features removed.
- verify whether the redesigned target still collapses to a trivial score.
- decide whether human confirmation is worth running.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/report.md
```

Main finding:

```text
status = ready_plumbing_only
```

The strict target v2 is less shortcut-prone than the previous target but has only
27 rows. It justifies a human confirmation protocol, not a posterior performance
claim.

### Stage 13. Human Confirmation Protocol

Document:

```text
31_human_confirmation_protocol.md
```

Purpose:

- define human confirmation fields for target v2.
- create strict and weak review sheets.
- define when human labels can be used for posterior-training evidence.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_sheet.tsv
```

Main finding:

```text
status = ready_protocol_no_human_labels
```

The protocol is ready, but no human label has been filled. Posterior claims
remain blocked.

### Stage 14. Human Label Readiness

Document:

```text
32_human_label_readiness.md
```

Purpose:

- fill the strict primary sheet with a temporary `(codex_ver)` reviewer label.
- validate required fields and allowed values.
- compute usable binary posterior targets after exclusion.
- decide whether train-only posterior plumbing smoke can resume.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_summary.json
```

Main finding:

```text
status = ready_for_train_only_codex_plumbing_smoke
```

Counts:

```text
strict rows = 27
usable binary rows = 27
positive targets = 16
negative targets = 11
missing required fields = 0
invalid values = 0
```

Boundary:

```text
(codex_ver) labels are not human-confirmed labels.
```

They can support a train-only plumbing smoke but cannot support paper evidence,
posterior advantage claims, or reviewer agreement.

### Stage 15. Multi-View Feasibility Check

Document:

```text
feasibility_check.md
```

Purpose:

- decide whether point cloud + multi-view belongs in H002.
- prevent the scope from drifting into a generic stronger relation predictor.
- define multi-view as an RGA evidence-axis extension.

Main verdict:

```text
reasonable, but only as evidence factor expansion
```

Future posterior form:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

where `V_mv_e` is multi-view crop, co-visible image, visibility, occlusion, and
appearance-context evidence.

Boundary:

```text
Use multi-view as audit/confirmation evidence before using it as model input.
```

### Stage 16. Codex Label Smoke

Document:

```text
33_codex_label_smoke.md
```

Purpose:

- join `(codex_ver)` strict binary targets to target-v2 feature rows.
- run train-only posterior plumbing smoke.
- verify semantic-only, geometry-only, semantic+geometry, and factorized inputs.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/report.md
```

Main finding:

```text
status = ready_plumbing_only_codex_labels
```

Train-internal 5-fold AUROC/AUPRC:

```text
semantic_only = 0.6080 / 0.7431
geometry_only = 0.8523 / 0.8986
semantic_plus_geometry = 0.8864 / 0.9217
factorized_reliability_posterior = 0.8864 / 0.9339
```

Interpretation:

- posterior pipeline can consume `(codex_ver)` labels.
- `p_geom_valid` alone is not relation reliability for the strict target.
- this is not posterior advantage evidence because labels are not human-confirmed
  and `N=27`.

### Stage 17. Multi-View Audit Protocol

Document:

```text
34_multiview_audit_protocol.md
```

Purpose:

- fix the order: validate current factorized posterior before adding `V_mv_e`.
- use multi-view only as audit/confirmation evidence for now.
- create review sheets for current strict labels and future support-contact audit.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/primary_strict_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/support_contact_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/all_candidate_sheet.tsv
```

Main finding:

```text
status = ready_audit_only_vmv_deferred
```

Counts:

```text
primary strict proximity rows = 27
support_contact extension rows = 26
relative_vertical lower-priority rows = 34
all candidates = 87
contact sheet coverage = 87 / 87
mesh link coverage = 87 / 87
```

Boundary:

```text
deployable_vmv_features_created = false
model_input_expansion_allowed_now = false
```

Current rule:

```text
Validate P(R_e = 1 | S_e, G_e, C_e, U_e) first.
Use multi-view only for audit evidence until that gate passes.
```

### Stage 18. Factorized Validation Plan

Document:

```text
35_factorized_validation_plan.md
```

Purpose:

- define when the current factorized posterior can support the H002 hypothesis.
- fix the minimal independent/human-confirmed label target.
- fix controls before any posterior advantage claim.
- keep `V_mv_e` out of model input.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/report.md
```

Main finding:

```text
status = ready_validation_plan_vmv_deferred
```

Target minimum:

```text
hypothesis-stage usable rows >= 60
per-class rows >= 20
label source = human-confirmed or independent audit
codex_ver sufficient = false
```

Required controls:

```text
same-family
same-geometry-status
same-rank-band
same-source for current pilot
no visual input
```

Acceptance rule:

```text
factorized_reliability_posterior must beat semantic_plus_geometry by
AUPRC >= +0.03 or Brier <= -0.02, with AUROC drop <= 0.02, under the
controlled label target.
```

### Stage 19. Controlled Label Target

Document:

```text
36_controlled_label_target.md
```

Purpose:

- expand the current strict target into a controlled human-review candidate set.
- preserve same-family, same-geometry-status, same-source, and rank-band controls.
- create review sheets without creating final labels.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_queue.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_queue.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet.tsv
```

Main finding:

```text
status = ready_controlled_review_queue_no_labels
```

Mined controlled queue:

```text
rows = 96
predicate_family = proximity
predicate_label = close by
geometry_status = satisfied
semantic_rank > 100
candidate_reliable_promote_seed = 48
candidate_unreliable_dense_noise_seed = 48
rank_201_500 = 32
rank_501_1000 = 32
rank_gt1000 = 32
contact_sheet coverage = 96 / 96
mesh link coverage = 96 / 96
```

Combined with existing strict seed:

```text
combined review rows = 123
```

Boundary:

```text
proposed_review_stratum is not a final label.
final labels created = false.
```

### Stage 20. Controlled Label Readiness

Document:

```text
37_controlled_label_readiness.md
```

Purpose:

- validate whether controlled review sheets have filled final labels.
- check required fields and allowed values.
- export binary targets only from allowed final labels.
- block posterior fitting until target minimum is satisfied.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/mined_binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/combined_binary_targets.jsonl
```

Main finding:

```text
status = not_ready_no_filled_labels
```

Readiness result:

| Sheet | Rows | Completed | Binary rows | Per-class min |
| --- | ---: | ---: | ---: | ---: |
| `mined_controlled` | 96 | 0 | 0 | 0 |
| `combined_review` | 123 | 0 | 0 | 0 |

Decision:

```text
current posterior fitting remains blocked.
```

The next gate is to fill controlled review labels with human/independent review,
then rerun the readiness validator. Proposed review strata remain sampling priors
and are not labels.

### Stage 21. Controlled Codex Labels

Document:

```text
38_controlled_codex_labels.md
```

Purpose:

- fill controlled review sheets with `(codex_ver)` bootstrap labels after user
  request.
- preserve original blank review sheets.
- rerun readiness on Codex-filled sheets.
- keep the label source boundary explicit.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/summary.json
```

Main finding:

```text
status = controlled_codex_ver_labels_filled_not_human_confirmed
```

Counts:

| Sheet | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `mined_controlled` | 96 | 48 | 48 |
| `combined_review` | 123 | 64 | 59 |

Readiness:

```text
status = ready_for_train_only_controlled_posterior_smoke
```

Boundary:

```text
codex_ver labels are sampling-prior bootstrap labels, not human-confirmed labels.
```

### Stage 22. Controlled Posterior Smoke

Document:

```text
39_controlled_posterior_smoke.md
```

Purpose:

- join controlled Codex labels to deployable feature rows.
- run the four planned baseline views.
- verify end-to-end posterior plumbing under train-only constraints.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/metrics.csv
```

Train-internal 5-fold main result:

| Target | `semantic_plus_geometry` AUPRC | `factorized` AUPRC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | 0.9546 | 0.9552 | +0.0006 | -0.0012 |
| `combined_controlled_codex_ver` | 0.7321 | 0.7658 | +0.0337 | -0.0081 |

Decision:

```text
posterior plumbing works, but H002 hypothesis is not validated by codex_ver labels.
```

The next scientific gate is human/independent controlled labels, not more model
fitting on Codex labels.

### Stage 23. Real Label Assumption Claim Audit

Document:

```text
40_real_label_claim_audit.md
```

Purpose:

- follow the user-directed assumption that `(codex_ver)` controlled labels are
  treated as real labels for hypothesis-stage analysis.
- reinterpret the controlled posterior smoke under that assumption.
- identify what still blocks a strong H002 posterior claim.

Working assumption:

```text
artifact provenance = codex_ver
current interpretation = user-directed real-label assumption
```

Main finding:

```text
weak conditional support only
```

Reinterpreted result:

| Target | Delta AUPRC | Delta Brier | Verdict |
| --- | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0006 | -0.0012 | insufficient |
| `combined_controlled_codex_ver` | +0.0337 | -0.0081 | weak positive signal |

Main blocker:

```text
factorized gain is not yet isolated from rank/identity/target-construction effects.
```

Evidence:

- `drop_direct_identity` collapses back to `semantic_plus_geometry` behavior.
- `drop_direct_identity_rank` and `safe_continuous` are near random.
- mined-only target does not show meaningful factorized gain.

Next required checks:

- scan-grouped CV.
- explicit `S+G`, `S+G+C`, `S+G+U`, `S+G+C+U` ablation.
- rank-band and strict-seed dependence analysis.
- proxy baselines such as rank-only and rank-band-only.
- paired bootstrap CI.
- calibration analysis with Brier/ECE/reliability bins.

### Stage 24. Grouped Control Smoke

Document:

```text
41_grouped_control_smoke.md
```

Purpose:

- treat `(codex_ver)` as real label under the user-directed hypothesis-stage
  assumption.
- rerun controlled posterior smoke with `scan_id` grouped folds.
- add explicit factor ablations and rank proxy baselines.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/metrics.csv
```

Grouped result:

| Target | Factorized - `S+G` AUPRC | Factorized - `S+G` Brier | Verdict |
| --- | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0341 | -0.0234 | numeric pass |
| `combined_controlled_codex_ver` | +0.0268 | -0.0082 | weak / below AUPRC threshold |

Factor ablation:

```text
S+G+C adds no signal.
S+G+U carries the gain.
```

Critical blocker:

```text
negative_rank_only beats factorized_reliability_posterior.
```

Proxy evidence:

| Target | Factorized AUPRC | `negative_rank_only` AUPRC |
| --- | ---: | ---: |
| `mined_controlled_codex_ver` | 0.9409 | 0.9589 |
| `combined_controlled_codex_ver` | 0.6801 | 0.7094 |

Decision:

```text
H002 has conditional support for the reliability framing, but not yet strong
support for the factorized posterior as a method contribution.
```

### Stage 25. Rank Proxy Debias

Document:

```text
42_rank_proxy_debias.md
```

Purpose:

- test whether factorized posterior beats a simple rank-derived proxy.
- remove rank-derived features and evaluate non-rank evidence.
- add non-rank evidence to `negative_rank_only` and check whether it improves.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/metrics.csv
```

Main finding:

```text
status = rank_proxy_not_debiased
```

Critical comparisons:

| Target | Left | Right | Delta AUPRC | Delta Brier |
| --- | --- | --- | ---: | ---: |
| `mined_controlled_codex_ver` | `factorized` | `negative_rank_only` | -0.0179 | +0.0041 |
| `combined_controlled_codex_ver` | `factorized` | `negative_rank_only` | -0.0293 | +0.0187 |
| `mined_controlled_codex_ver` | `negative_rank + factorized_no_rank` | `negative_rank_only` | -0.0491 | +0.0286 |
| `combined_controlled_codex_ver` | `negative_rank + factorized_no_rank` | `negative_rank_only` | -0.0141 | +0.0164 |

Decision:

```text
The current controlled-label signal is still explainable by semantic rank /
underconfidence proxy. H002 should not claim a factorized-posterior method
contribution yet.
```

Implication:

```text
The next blocker is target construction, not model capacity.
```

### Stage 26. Within-Rank Stability

Document:

```text
43_within_rank_stability.md
```

Purpose:

- evaluate whether factorized evidence remains useful inside fixed rank bands.
- compare factorized posterior against `negative_rank_only` within each band.
- build rank-matched positive/negative pairs using `rank_in_context`.
- check whether the current controlled target is independent enough from
  semantic-rank construction.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/matched_pairs.jsonl
```

Result:

```text
status = within_rank_mixed
```

Primary grouped comparison:

| Target | Rank band | `factorized - negative_rank_only` AUPRC | `factorized - negative_rank_only` Brier |
| --- | --- | ---: | ---: |
| `mined_controlled_codex_ver` | `rank_201_500` | -0.0917 | +0.0727 |
| `mined_controlled_codex_ver` | `rank_501_1000` | -0.0545 | +0.0116 |
| `mined_controlled_codex_ver` | `rank_gt1000` | +0.0000 | +0.0020 |
| `combined_controlled_codex_ver` | `rank_201_500` | -0.0917 | +0.0727 |
| `combined_controlled_codex_ver` | `rank_501_1000` | -0.0545 | +0.0116 |
| `combined_controlled_codex_ver` | `rank_gt1000` | +0.0000 | +0.0020 |

Pairwise observation:

| Target | Rank band | Pairs | Mean rank gap | Factorized | `negative_rank_only` |
| --- | --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `rank_201_500` | 16 | 32.06 | 0.8750 | 0.8438 |
| `mined_controlled_codex_ver` | `rank_501_1000` | 16 | 11.56 | 0.8125 | 0.6875 |
| `mined_controlled_codex_ver` | `rank_gt1000` | 16 | 51.38 | 0.9375 | 0.9375 |

Decision:

```text
Within-rank evidence is mixed. Pairwise rank-matched checks show that relation
evidence can help inside some bands, but grouped primary-band metrics still do
not consistently beat the negative-rank proxy.
```

Implication:

```text
The next step is a stricter rank-matched target, not a larger posterior model.
```

### Stage 27. Rank-Matched Target

Document:

```text
44_rank_matched_target.md
```

Purpose:

- build a stricter controlled target by directly matching positive and negative
  rows with close `rank_in_context`.
- exclude large-gap non-tail pairs from primary smoke metrics.
- keep `tail` pairs as exploratory rows only.
- rerun train-only scan-grouped posterior smoke on the stricter target.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pair_records.jsonl
```

Result:

```text
status = rank_matched_mixed
```

Target construction:

| Target | Scope | Rows | Pairs | Mean rank gap | Max rank gap | Evaluated |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `mined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 14.56 | 47.00 | yes |
| `combined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 14.56 | 47.00 | yes |
| `combined_tail_exploratory_gap500_codex_ver` | tail exploratory | 22 | 11 | 103.91 | 367.00 | no |

Primary grouped comparison:

| Left | Right | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: |
| `factorized_reliability_posterior` | `semantic_plus_geometry` | +0.0245 | -0.0144 |
| `factorized_reliability_posterior` | `negative_rank_only` | -0.0239 | +0.0029 |
| `negative_rank_plus_factorized_no_rank` | `negative_rank_only` | -0.0490 | +0.0223 |
| `negative_rank_plus_disagreement` | `negative_rank_only` | -0.0049 | -0.0002 |

Pairwise observation:

| Target | Pairs | Factorized | `negative_rank_only` | `factorized_no_rank` | `p_geom_valid_raw` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mined_rank_matched_gap50_codex_ver` | 43 | 0.8605 | 0.8372 | 0.6512 | 0.5349 |

Decision:

```text
Rank-matched target is mixed. The stricter target reduces large rank-gap
shortcuts, but factorized posterior still does not beat negative_rank_only under
scan-grouped CV. Pairwise evidence remains mildly favorable but insufficient.
```

Implication:

```text
The next blocker is label/target independence. The current codex target is not
independent enough to support a posterior method claim.
```

### Stage 28. Target Independence Audit

Document:

```text
45_target_independence_audit.md
```

Purpose:

- diagnose why `negative_rank_only` remains strong after rank matching.
- separate target construction effects from deployable evidence effects.
- audit whether current codex labels are independent enough to support a
  posterior method claim.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/feature_summaries.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/metadata_summaries.csv
```

Result:

```text
status = target_independence_not_established
```

Main evidence:

| Check | Result |
| --- | --- |
| Mean matched rank gap | 14.56 |
| Positive has worse source rank share | 0.8140 |
| `negative_rank_only_raw` pairwise accuracy | 0.8372 |
| `p_geom_valid_raw` pairwise accuracy | 0.5349 |
| `final_controlled_label` row-majority purity | 1.0000 |
| `proposed_review_stratum` row-majority purity | 1.0000 |
| `mined` vs `combined` primary target Jaccard | 1.0000 |

Decision:

```text
Current codex-controlled rank-matched labels are still not independent enough
from semantic-rank / underconfidence construction to support a posterior method
claim.
```

Implication:

```text
H002 should continue the RGA framework and target construction work, but pause
posterior method claims until rank-hidden independent audit labels exist.
```

### Stage 29. Independent Label Protocol

Document:

```text
46_independent_label_protocol.md
```

Purpose:

- define rank-hidden independent label collection for H002.
- create blind review sheets that hide semantic rank, semantic score,
  `p_geom_valid`, working label, queue identity, and proposed stratum.
- use multi-view/mesh assets as audit evidence only, not deployable model input.
- prioritize relation families for future semantic-geometry-visual agreement.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/internal_key.jsonl
```

Result:

```text
status = independent_label_protocol_ready
```

Candidate counts:

| Family | Rows | Role |
| --- | ---: | --- |
| `support_contact` | 26 | first multi-view reliability family |
| `proximity` | 27 | current debugging family |
| `relative_vertical` | 34 | control / robustness family |
| `attachment_deferred` | 0 | future high-novelty family; separate generator needed |

Label mapping:

| Binary use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass only | `ontology_mismatch`, `abstain_uncertain` |

Decision:

```text
Independent label protocol is ready. H002 should collect or fill rank-hidden
labels before any stronger posterior method claim.
```

Combiner follow-up after labels:

```text
residual reliability model -> gated evidence model -> pairwise rank-matched
ranking diagnostic -> debiased factor audit
```

## RGA To Factorized Reliability

RGA is the measurement framework. Factorized reliability posterior is the later
method candidate.

The relation is:

```text
RGA rows -> audit labels/targets -> feature blocks -> posterior smoke model
```

RGA provides:

- semantic axis features.
- geometry axis features.
- coverage states.
- uncertainty states.
- label/audit targets.
- mismatch buckets for evaluation.

The posterior should learn:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

The future multi-view extension is:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

This is an evidence-axis extension, not a new scene graph generator.

It should not simply learn:

```text
semantic_score * p_geom_valid
```

because that simple product cannot represent:

- unsupported geometry as coverage/abstention.
- uncertain geometry as uncertainty.
- low-semantic/high-geometry underconfidence.
- label granularity or ontology mismatch.
- dense relation noise.

## Current Open3DSG Train Pilot Instantiation

Scope:

```text
Open3DSG train pilot
100 train subgraphs
100 scans
118,560 prediction rows
```

Geometry-checkable families:

```text
proximity
relative_vertical
support_contact
```

Unsupported in current verifier:

```text
relative_horizontal
attachment_deferred
unsupported_first_pass
```

Primary observation:

- `RGA-HL@100 = 3.87%`: high semantic but geometry unsatisfied exists, but is not
  the dominant train pilot signal.
- `RGA-LH-tail@100 = 44.32%`: low semantic but geometry satisfied is large.
- LH is mixed: true underconfidence, annotation sparsity, ontology mismatch,
  dense relation noise, and uncertain cases.
- Therefore H002 must remain bidirectional and audit-aware.

## Claim Boundary

Allowed current claim:

```text
RGA provides a train-only framework for separating semantic confidence,
geometric satisfiability, coverage, uncertainty, and label/audit evidence at
relation-edge level.
```

Allowed current diagnostic claim:

```text
On the Open3DSG train pilot, RGA exposes both high-semantic/low-geometry and
low-semantic/high-geometry states. The low-semantic/high-geometry state is large
but requires audit because it mixes true underconfidence, annotation sparsity,
ontology mismatch, and dense relation noise.
```

Blocked claims:

- RGA itself improves relation prediction.
- RGA-LH rows are automatically valid missing positives.
- working labels are paper-locked human annotations.
- `p_geom_valid` is full relation reliability.
- the factorized posterior outperforms rank-controlled baselines.
- held-out validation/test conclusions.

## Next Step

The next H002 step is:

```text
47_independent_label_ingestion.md
```

Goal:

- define completed blind-sheet validation and join-back to `internal_key.jsonl`.
- prevent hidden fields from leaking into deployable features.
- materialize independent binary/multiclass targets.
- prepare residual/gated combiner diagnostics.
- continue without validation/test rows.
