# H002 RGA Framework

Last updated: 2026-06-18

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

### Current Full-Train Extension

Documents:

```text
53_full_train_scope_contract.md
54_full_train_source_runner.md
55_full_train_runtime_stage.md
56_full_train_raw_dump.md
57_full_train_adapter_export.md
58_full_train_geometry_join.md
59_full_train_rga_rows.md
60_full_train_controlled_mining.md
84_full_train_independent_support_vertical_audit_packet.md
85_full_train_independent_support_vertical_label_readiness.md
86_full_train_independent_support_vertical_label_fill.md
87_full_train_independent_support_vertical_label_ingestion.md
88_full_train_independent_support_vertical_target_independence_audit.md
89_full_train_independent_support_vertical_label_policy_revision.md
90_full_train_independent_support_vertical_v2_label_readiness.md
91_full_train_independent_support_vertical_v2_label_fill.md
92_full_train_independent_support_vertical_v2_label_ingestion.md
```

Current full-train status:

| Stage | Status |
| --- | --- |
| source contract | `ready` |
| raw dump | `ready` |
| adapter export | `ready` |
| geometry join | `ready` |
| RGA rows | `ready` |
| controlled candidate mining | `ready_for_controlled_audit` |
| controlled label readiness | `not_ready_no_filled_labels` |
| controlled codex label fill | `ready_for_train_only_full_posterior_smoke` |
| controlled posterior smoke | `full_train_posterior_proxy_blocked` |
| selected support/vertical audit packet | `ready` |
| selected support/vertical v1 label policy | `blocked_by_target_carryover` |
| selected support/vertical v2 label readiness | `ready_for_fill` |
| selected support/vertical v2 label fill | `filled_no_direct_target` |
| selected support/vertical v2 label ingestion | `ingested_with_target_risk` |

Full-train RGA rows:

```text
4,818,996 prediction rows
```

Full-train mismatch queues:

| Queue | Rows |
| --- | ---: |
| `RGA-HL` | 1,828 |
| `RGA-LH` | 455,598 |

Controlled mining output:

| Item | Count |
| --- | ---: |
| candidate rows | 360 |
| unique scans | 92 |
| `HL` candidates | 83 |
| `LH` candidates | 277 |

Interpretation:

```text
Full train confirms that the main available diagnostic mass is not only
high-semantic/low-geometry overconfidence. Low-semantic/high-geometry candidates
are much larger, so H002 remains a bidirectional RGA and audit framework.
```

Boundary:

```text
The full-train candidate roles are not labels. Posterior training still requires
controlled label readiness.
```

Current label readiness:

```text
candidate sheet rows = 360
started review rows = 0
usable binary targets = 0
binary target files = empty
```

Current bootstrap label readiness:

```text
label source = codex_ver_full_train_policy_bootstrap
completed review rows = 360
usable binary targets = 173
positive rows = 74
negative rows = 99
status = ready_for_train_only_full_posterior_smoke
```

Boundary:

```text
codex_ver_full_train labels are not human-confirmed and do not support a
paper-level posterior claim. They only unlock train-only posterior smoke and
shortcut/proxy controls.
```

Posterior smoke result:

```text
factorized - semantic_plus_geometry grouped AUPRC = +0.0117
factorized - semantic_plus_geometry grouped Brier = -0.0019
proposed_role_only AUPRC = 1.0000
label_status_only AUPRC = 0.9473
```

Interpretation:

```text
The current full-train bootstrap target is dominated by label-policy proxies.
This supports RGA/audit framing, not a factorized posterior method claim.
```

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

### Stage 30. Independent Label Ingestion

Document:

```text
47_independent_label_ingestion.md
```

Purpose:

- validate completed rank-hidden blind sheets.
- join completed labels back to `internal_key.jsonl`.
- materialize independent binary and multiclass targets.
- keep hidden semantic/geometry/rank provenance out of deployable input
  features.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/schema.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/validated_labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/multiclass_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/ingestion_errors.jsonl
```

Result:

```text
status = independent_label_ingestion_waiting_for_completed_labels
```

Counts:

| Item | Count |
| --- | ---: |
| blind sheet rows | 87 |
| internal key rows | 87 |
| completed label rows | 0 |
| binary target rows | 0 |
| ingestion errors | 0 |

Decision:

```text
The ingestion path is ready, but no independent labels are completed yet.
Residual/gated combiner diagnostics remain blocked until rank-hidden labels are
filled and ingested.
```

### Stage 31. Blind Label Fill

Document:

```text
48_blind_label_fill.md
```

Purpose:

- fill rank-hidden blind labels with `(codex_ver_blind)` bootstrap labels.
- fix asset-level leakage in the original contact sheets by generating sanitized
  crop paths and sanitized contact sheets.
- rerun independent label ingestion on the completed sheet.
- produce binary targets for train-only residual/gated combiner diagnostics.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_sanitized.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/report.md
```

Result:

```text
status = independent_label_targets_ready
```

Counts:

| Item | Count |
| --- | ---: |
| completed label rows | 87 |
| binary target rows | 75 |
| positive rows | 46 |
| negative rows | 29 |
| excluded rows | 12 |
| ingestion errors | 0 |

Boundary:

```text
codex_ver_blind labels are bootstrap labels, not human-confirmed labels.
```

Decision:

```text
H002 can proceed to train-only independent combiner diagnostics, but cannot
claim paper-level human-label evidence or posterior method advantage from these
labels alone.
```

### Stage 32. Independent Combiner Smoke

Document:

```text
49_independent_combiner_smoke.md
```

Purpose:

- join `independent_label_ingestion_codex_ver/binary_targets.jsonl` to deployable
  feature rows.
- evaluate semantic-only, geometry-only, semantic+geometry, factorized,
  residual, and gated evidence views.
- compare against rank, family, predicate, and `p_geom_valid` proxy controls.
- report grouped-by-scan, family-slice, and rank-matched pairwise diagnostics.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/family_slices.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/matched_pairs.jsonl
```

Result:

```text
status = independent_combiner_no_strong_signal
```

Grouped-by-scan main deltas:

| Comparison | Delta AUPRC | Delta Brier |
| --- | ---: | ---: |
| `factorized - semantic_plus_geometry` | -0.0013 | +0.0016 |
| `residual - semantic_plus_geometry` | -0.1010 | +0.0184 |
| `gated - semantic_plus_geometry` | -0.0969 | +0.0186 |
| `factorized - negative_rank_only` | +0.1412 | -0.0289 |

Interpretation:

```text
Factorized beats the negative-rank proxy, but it does not beat
semantic_plus_geometry. Residual/gated variants are worse overall. The current
bootstrap label policy is strongly entangled with family/predicate semantics.
```

Decision:

```text
Independent combiner plumbing is complete, but posterior method claims remain
blocked. The next blocker is label-policy and family/predicate bias.
```

### Stage 33. Label Policy Audit

Document:

```text
50_label_policy_audit.md
```

Purpose:

- test whether `(codex_ver_blind)` labels are recoverable from family/predicate
  policy.
- export family-balanced, predicate-balanced, and proximity-only target variants.
- rerun train-only grouped smoke on those variants.
- decide whether posterior method claims remain plausible.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/group_policy_table.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/comparisons.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/family_balanced_codex_ver_blind.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/predicate_balanced_codex_ver_blind.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/proximity_only_codex_ver_blind.jsonl
```

Result:

```text
status = label_policy_entangled
```

Main finding:

| Key | Majority Accuracy | NMI |
| --- | ---: | ---: |
| `predicate_family` | 0.7067 | 0.1931 |
| `predicate_label` | 0.7067 | 0.2505 |
| `rank_band` | 0.6533 | 0.0980 |

Balanced target result:

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `family_balanced_codex_ver_blind` | 44 | 22 | 22 |
| `predicate_balanced_codex_ver_blind` | 44 | 22 | 22 |
| `proximity_only_codex_ver_blind` | 27 | 15 | 12 |

Decision:

```text
The current bootstrap target is too entangled with predicate/family policy to
support posterior novelty. H002 should not escalate the posterior method claim
without new human labels or a much tighter target protocol.
```

### Stage 34. Posterior Path Decision

Document:

```text
51_posterior_path_decision.md
```

Purpose:

- decide whether the posterior remains a method candidate.
- answer whether changing posterior combination could improve H002.
- separate model-formulation potential from current label-policy blocker.
- define minimum evidence required to revive posterior claims.

Decision:

```text
posterior_path_deferred
```

Meaning:

```text
Posterior remains a conditional future method candidate, but it should not be
the near-term H002 main contribution.
```

Current best main direction:

```text
RGA benchmark / diagnostic framework / failure taxonomy
```

Posterior revival candidates:

| Candidate | Role |
| --- | --- |
| semantic-prior residual posterior | strongest conceptual match |
| family-specific hierarchical posterior | useful after family-balanced labels |
| coverage-gated geometry model | useful after uncertainty-rich labels |
| pairwise rank-matched reliability ranking | useful for small controlled labels |
| debiased/orthogonalized factor posterior | tests independent geometry signal |
| selective/abstention-aware posterior | models uncertain/unsupported cases |
| monotonic calibrated posterior | improves calibration defensibility |

Feasibility-check reuse rule:

```text
feasibility_check.md is reused as the method map, but with staged entry.
```

Immediate use:

- multi-view/mesh/contact-sheet evidence is audit evidence, not model input.
- use it to distinguish `true_underconfidence`, `dense_relation_noise`,
  `annotation_sparsity`, `ontology_mismatch`, and visual/mesh uncertainty.
- keep relation-family expansion in the order
  `support_contact -> attachment_deferred -> relative_vertical`.

Deferred use:

- `V_mv_e` enters the posterior only after the current
  `S_e + G_e + C_e + U_e` target passes an independent-label gate.
- residual/gated/pairwise/debiased/product-of-experts/hierarchical/monotonic
  combiners are posterior revival candidates, not current main-claim evidence.

Minimum revival gate:

```text
human-confirmed predicate/family-controlled labels, >=150 binary usable rows,
per-family minority >=15, grouped CV gain over semantic_plus_geometry, and
predicate/family/rank proxy controls passed.
```

### Stage 35. RGA Main Framing

Document:

```text
52_rga_main_framing.md
```

Purpose:

- reframe near-term H002 around RGA benchmark, diagnostic framework, and failure
  taxonomy.
- keep posterior as a conditional method candidate.
- adopt full-train expansion before opening validation/test.
- connect `feasibility_check.md` to audit evidence and posterior revival.

Decision:

```text
full_train_expansion_before_validation
```

Meaning:

```text
Expand H002 from the Open3DSG train pilot to full train, keep validation/test
closed, use RGA as the main framework, and use full train to mine controlled
labels and test whether posterior signal survives shortcut controls.
```

Full-train expansion purpose:

- pilot train failure does not falsify H002 posterior on the full train
  distribution.
- full train can provide more balanced family/predicate/rank-controlled targets.
- validation/test must remain closed until target, features, metrics, baselines,
  and posterior combiner are frozen.

Immediate full-train gates:

1. freeze full-train source scope and row identity.
2. generate full-train RGA rows for train split only.
3. measure RGA-HL/RGA-LH, coverage, uncertainty, and label-axis distributions.
4. mine controlled label targets with at least 150 binary rows and family
   minority support.
5. run train-only grouped CV against semantic, geometry, semantic+geometry, and
   proxy controls.

Next document:

```text
53_full_train_scope_contract.md
```

### Stage 36. Full Train Scope Contract

Document:

```text
53_full_train_scope_contract.md
```

Purpose:

- define full-train source scope before any execution.
- separate the full-train artifact root from the train-pilot root.
- decide which pilot tools can be reused and which must be parameterized.
- keep validation/test closed.

Decision:

```text
full_train_scope_contract_ready_no_execution
```

Scope:

```text
open3dsg_train_full
```

Expected planning counts from the existing pilot manifest:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| ready candidate train contexts | 3,738 |
| dropped preprocess-not-ready contexts | 108 |
| dropped no-relationship contexts | 6 |

Artifact root:

```text
artifacts/train_rga_full/open3dsg_train_full/
```

Key implementation decision:

```text
The pilot source-contract runner is not reusable as-is because it selects one
representative subgraph per scan. Full train requires all ready train contexts.
```

Next document:

```text
54_full_train_source_runner.md
```

### Stage 37. Full Train Source Runner

Document:

```text
54_full_train_source_runner.md
```

Purpose:

- implement the all-ready full-train source contract runner.
- create the full-train source contract artifact.
- verify train-only provenance and no validation/test source leakage.

Added tool:

```text
tools/full_train_source_contract.py
```

Result:

```text
status = full_train_source_contract_ready
```

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/source_contract/
```

Counts:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| ready candidate contexts | 3,738 |
| selected contexts | 3,738 |
| selected scans | 1,157 |
| selected relationships | 79,704 |
| dropped preprocess-not-ready | 108 |
| dropped no-relationship | 6 |

Primary family coverage:

| Family | GT relations |
| --- | ---: |
| `support_contact` | 12,600 |
| `proximity` | 12,300 |
| `relative_vertical` | 3,552 |

Next document:

```text
55_full_train_runtime_stage.md
```

### Stage 38. Full Train Runtime Stage

Document:

```text
55_full_train_runtime_stage.md
```

Purpose:

- parameterize the H002 runtime staging tool for full train.
- create `compose.open3dsg_train_full.yaml`.
- stage an isolated full-train Open3DSG runtime.
- run Docker preflight before raw dump launch.

Decision:

```text
full_train_runtime_preflight_ready
```

Runtime root:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
```

Runtime stage result:

| Item | Count |
| --- | ---: |
| contexts | 3,738 |
| selected scans | 1,157 |
| linked scans | 1,157 |
| sequence-ready scans | 1,157 |
| missing feature contexts | 0 |

Docker preflight:

| Gate | Passed |
| --- | --- |
| checkpoint | true |
| runtime | true |
| scope | true |
| imports | true |

Raw dump contract:

```text
contract_ready_raw_dump_missing
```

Next document:

```text
56_full_train_raw_dump.md
```

### Stage 39. Full Train Raw Dump

Document:

```text
56_full_train_raw_dump.md
```

Purpose:

- launch the full-train Open3DSG raw dump in a resumable background session.
- keep log and exit files under `logs/`.
- block adapter export until raw dump completeness is verified.

Current status:

```text
full_train_raw_dump_complete
```

tmux session:

```text
h002_open3dsg_train_full_raw_20260615_180429
```

Log:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.log
```

Exit file:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.exit
```

Completion evidence:

| Item | Count / Status |
| --- | ---: |
| process exit code | 0 |
| stream manifest status | `raw_dump_stream_complete` |
| completed batches | 3,738 |
| raw rows | 186,218 |
| completed rows | 3,738 |

Raw repair/dedup:

| Item | Count / Status |
| --- | ---: |
| repair status | `ready` |
| input rows | 186,218 |
| output rows | 186,139 |
| duplicate groups | 79 |
| duplicate extra rows | 79 |
| malformed identity rows | 0 |
| noncontiguous subgraph repeats | 0 |

Key artifacts:

```text
artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.jsonl
artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl
artifacts/train_rga_full/open3dsg_train_full/raw_dump/stream_manifest.json
artifacts/train_rga_full/open3dsg_train_full/raw_dump/repair_manifest.json
```

Next document:

```text
57_full_train_adapter_export.md
```

### Stage 40. Full Train Adapter Export

Document:

```text
57_full_train_adapter_export.md
```

Purpose:

- convert repaired full-train Open3DSG raw rows into identity-preserving
  prediction rows.
- avoid the existing pilot exporter's list-in-memory path at full-train scale.
- preserve train subset provenance.
- keep validation/test closed.

Added tool:

```text
tools/export_full_train_adapter.py
```

Decision:

```text
full_train_adapter_export_ready
```

Result:

| Item | Count / Status |
| --- | ---: |
| contexts | 3,738 |
| raw rows read | 186,139 |
| prediction rows | 4,818,996 |
| subgraphs written | 3,738 |
| conversion errors | 0 |
| adapter warnings | 793 |
| `relationships_validation`/`h001_validation` in prediction provenance | no match |

Warning breakdown:

| Warning | Count |
| --- | ---: |
| `raw_edge_outside_context_filtered` | 786 |
| `same_endpoint_skipped` | 7 |

Key artifact:

```text
artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
```

Family prediction rows:

| Family | Rows |
| --- | ---: |
| `support_contact` | 556,038 |
| `proximity` | 185,346 |
| `relative_vertical` | 370,692 |
| `relative_horizontal` | 741,384 |
| `attachment_deferred` | 556,038 |
| `unsupported_first_pass` | 2,409,498 |

Next action:

```text
full_train_geometry_join
```

### Stage 41. Full Train Geometry Join

Document:

```text
58_full_train_geometry_join.md
```

Purpose:

- join full-train prediction rows with H001 frozen geometry verifier evidence.
- preserve all full-train prediction rows.
- produce deterministic geometry status and geometry-only `p_geom_valid`.
- keep validation/test closed.

Current status:

```text
full_train_geometry_join_ready_with_exit_file_caveat
```

tmux session:

```text
h002_open3dsg_train_full_geometry_20260616_120342
```

Input:

| Item | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| selected train scans | 1,157 |

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/geometry/
```

Completion gate:

```text
manifest.status = ready
counts.predictions = 4,818,996
counts.verification_rows = 4,818,996
counts.rows_preserved = true
errors = []
```

Result:

| Item | Count / Status |
| --- | ---: |
| manifest status | `ready` |
| verification rows | 4,818,996 |
| rows preserved | true |
| primary family rows | 1,112,076 |
| unsupported family rows | 3,706,920 |
| calibration scored rows | 1,112,076 |
| warnings | 9 |
| exit file | missing wrapper caveat |

Status counts:

| Status | Rows |
| --- | ---: |
| `satisfied` | 474,898 |
| `uncertain` | 490,410 |
| `violated` | 146,768 |
| `unsupported` | 3,706,920 |

Next action:

```text
full_train_rga_rows
```

### Stage 42. Full Train RGA Rows

Document:

```text
59_full_train_rga_rows.md
```

Purpose:

- join full-train prediction rows, geometry verification rows, and train GT
  relation labels.
- compute full-train RGA buckets and label-axis distribution.
- produce HL/LH queues for later controlled label mining.
- keep validation/test closed.

Current status:

```text
full_train_rga_rows_ready_with_exit_file_caveat
```

tmux session:

```text
h002_open3dsg_train_full_rga_20260616_161755
```

Input:

| Item | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| selected train contexts | 3,738 |
| selected train scans | 1,157 |
| selected GT relations | 79,704 |

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
```

Completion gate:

```text
summary.status = ready
validation.rows_written = 4,818,996
validation.prediction_geometry_mismatches = 0
validation.validation_error_count = 0
```

Result:

| Item | Count / Status |
| --- | ---: |
| summary status | `ready` |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| rows written | 4,818,996 |
| prediction-geometry mismatches | 0 |
| validation errors | 0 |
| HL queue rows | 1,828 |
| LH queue rows | 455,598 |
| exit file | missing wrapper caveat |

Primary full-train RGA metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 3.02% | 4.96% |
| `RGA-valid@K` | 61.90% | 52.39% |
| `RGA-coverage@K` | 2.91% | 9.86% |
| `RGA-LH-tail@K` | 42.61% | 42.37% |

Full-train top100 buckets:

| Bucket | Rows |
| --- | ---: |
| `RGA-HH` | 19,300 |
| `RGA-HL` | 1,828 |
| `RGA-HU` | 15,714 |
| `RGA-HM` | 336,910 |
| `RGA-LH` | 455,598 |
| `RGA-LL` | 144,940 |
| `RGA-LU` | 474,696 |
| `RGA-LM` | 3,370,010 |

Next action:

```text
full_train_controlled_label_mining
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

## Current Open3DSG Full Train Instantiation

Scope:

```text
Open3DSG train full
3,738 train subgraphs
1,157 scans
4,818,996 prediction rows
```

Current completed stages:

- full-train source contract.
- isolated full-train runtime stage.
- Docker preflight.
- raw dump completion.
- raw repair/dedup.
- streaming adapter export.
- streaming geometry join.
- full-train RGA row construction.
- controlled HL/LH candidate mining.
- controlled codex label readiness.
- controlled `(codex_ver_full_train)` label fill.
- train-only posterior smoke.
- label-policy audit.
- independent blind label protocol.
- independent asset packet generation.
- asset packet gap audit.

Current full-train diagnostic status:

```text
full_train_independent_combiner_path_decision_factor_revision_first
```

Core finding:

- Full-train RGA exposes large bidirectional mismatch mass:
  `RGA-HL@100=4.96%`, `RGA-LH-tail@100=42.37%`.
- The controlled bootstrap target is executable with 173 binary rows.
- `factorized_reliability_posterior` is only slightly better than
  `semantic_plus_geometry` on the bootstrap target.
- `proposed_audit_role` and `label_match_status` recover the target almost
  perfectly, so the current target cannot validate posterior novelty.
- A rank/role-hidden independent label protocol is now ready.
- Independent asset packets are ready for 347/360 rows and partial for 13/360
  rows; label-facing leakage audit passes.
- Asset packet gap audit keeps 355/360 rows for label fill and excludes 5 rows
  before label fill.
- Independent label readiness passes on 355/360 rows: schema/path/leakage errors
  are 0, and the 179-row priority sheet is also ready.
- Codex-version independent label fill produces 355 labels with 283 binary-usable
  rows: 155 positive and 128 negative. These are bootstrap labels, not
  human-confirmed paper evidence.
- Independent label ingestion succeeds with 355 validated labels, 283 binary
  targets, and 0 schema errors, but a basic target probe detects hidden metadata
  correlation through `proposed_audit_role_hidden` (NMI 0.2897).
- Target-independence audit confirms the original 283-row target is risky, but
  `proposed_role_balanced_codex_ver` remains as a 158-row controlled slice with
  79 positive and 79 negative rows and no hidden group risk under the audit
  thresholds.
- Controlled posterior smoke on that slice is executable but shows no strong
  factorized advantage: grouped AUPRC delta is -0.0047 versus
  `semantic_plus_geometry`, -0.0039 versus `semantic_only`, and +0.1155 versus
  `geometry_only`.
- Controlled error analysis shows why the current combiner is not enough:
  factorized posterior creates more threshold mistakes than it fixes relative to
  `semantic_plus_geometry` (`factorized_wrong_sg_correct=10`,
  `factorized_correct_sg_wrong=1`). The failure is structured by relation family
  and mismatch direction, so the next method step should design a family-gated,
  residual, uncertainty-gated combiner rather than adding a larger generic
  classifier.
- Combiner upgrade design is now fixed as a train-only hypothesis-stage plan:
  first smoke `C1_residual_logit_calibrator`, `C2_family_gated_residual`, and
  `C3_uncertainty_gated_geometry`; defer generic high-capacity GBDT-style and
  graph factor rescoring until edge-local evidence is stronger.
- Combiner upgrade smoke shows no safe gain over `semantic_plus_geometry`:
  `C2_family_gated_residual` gives the best upgraded AUPRC delta (+0.0070) but
  worsens Brier (+0.0062), while `C3_uncertainty_gated_geometry` improves AUROC,
  Brier, and threshold transfer but lowers AUPRC. No upgraded view passes the
  pre-defined progression rule.
- Combiner upgrade error analysis identifies the blocker: C2 is a
  ranking-oriented family gate with calibration damage and support-contact
  overcorrection, while C3 is safer for threshold/Brier and promising for
  `relative_vertical` / high-semantic-low-geometry slices but hurts global
  support-contact ranking. This points to a path decision before adding model
  capacity.
- Path decision keeps H002 active but freezes the current posterior performance
  result as a negative/partial boundary. The selected next path is
  relation-family-specific factor revision before any new smoke. Generic
  high-capacity combiners remain deferred, and posterior improvement over
  `semantic_plus_geometry` remains a blocked claim.
- Factor revision design confirms that full-train raw geometry witness fields
  are available for `support_contact`, `relative_vertical`, and `proximity`, but
  not for unsupported families. The next step is to materialize revised factor
  blocks from continuous raw geometry evidence rather than using
  `geometry_status` as a reliability shortcut.
- Revised factor dataset materialization joins raw geometry witness fields for
  all 158 controlled rows and adds D1-D4 revised factor views with zero
  forbidden feature-key hits. This prepares the train-only revised factor smoke
  but still does not support any posterior performance claim.
- Revised factor smoke is positive under train-only scan-grouped folds:
  D1-D4 all improve over `semantic_plus_geometry`, with D4 reaching AUPRC
  +0.1241 and Brier -0.0462. This is promising hypothesis-stage evidence, but
  it remains blocked from paper-level posterior claims until error analysis,
  shortcut controls, and stronger independent labels are complete.
- Revised factor error analysis shows that D4's gain is not explained solely by
  `predicate_family`: a family-only offset control has almost no AUPRC gain,
  while raw-only witness control has strong train-only signal. This keeps the
  raw-witness factorization path alive but makes raw-witness shortcut controls
  the next required gate.
- Revised factor shortcut controls show that row-specific raw witness alignment
  matters: global raw-witness shuffle flips D4's AUPRC delta negative, and
  within-family shuffle leaves only a small fraction of the original gain.
  However, proximity remains unsafe as a ranking claim and typed family
  interaction still needs family-wise audit. The next gate is therefore claim
  boundary definition, not another capacity increase.
- Revised factor claim boundary is now fixed as a hypothesis-stage diagnostic
  claim. The selected scope is `support_contact + relative_vertical`; proximity
  is excluded from the main posterior claim and preserved as a failure/risk
  slice. The method boundary is `RGA-scoped raw-witness residual reliability
  layer`, not D4 typed family interaction as a final combiner.
- The selected support/vertical audit packet is ready: 127 selected train-only
  rows, 72 support_contact and 55 relative_vertical, all with label-ready
  evidence packets. Labeler-visible sheets expose relation candidate, raw
  witness values, and asset pointers, while hidden target-construction metadata
  is kept in a post-label internal reference only. Leakage audit is zero-hit.
- Support/vertical label readiness is ready for fill: the 127-row sheet passes
  header, path, hidden-reference, risk-slice, and leakage checks. Allowed review
  values and the label-to-binary policy are frozen in a completion schema.
- Support/vertical Codex-version label fill is complete for 127 selected rows:
  114 binary-usable labels, 40 positives, 74 negatives, and 13 excluded rows.
  The fill used only visible relation fields and raw witness values; hidden
  internal reference and target-construction metadata were not read. These are
  bootstrap labels, not human-confirmed paper evidence.
- Support/vertical label ingestion is complete with 127 validated labels, 114
  binary targets, 40 positives, 74 negatives, and 0 ingestion errors. The
  post-label probe detects hidden metadata correlation
  (`relation_validity_label_hidden` NMI 0.5710, `label_use_hidden` NMI 0.4506,
  `rank_band_hidden` NMI 0.2128), so posterior smoke remains blocked until a
  dedicated target-independence audit constructs or rejects a controlled slice.
- Support/vertical target-independence audit rejects a strict controlled target:
  no slice clears prior-label carryover from `relation_validity_label_hidden`
  and `label_use_hidden`. A 70-row `rank_band_balanced_codex_ver` construction-only
  diagnostic slice remains, but it is not sufficient for posterior method
  validation. The next gate is label-policy revision, not posterior smoke.
- Support/vertical label policy v2 is now defined: direct
  `independent_relation_label` is removed from the labeler surface, review is
  split into factual axes, and geometry validity / relation reliability targets
  are derived only after label lock. The v2 sheet has 127 rows, with 72
  support_contact and 55 relative_vertical rows.
- Support/vertical v2 label readiness is complete: the 127-row fill sheet passes
  schema, packet-path, family-partition, proximity-exclusion, and leakage checks.
  This unlocks factual-axis fill, not posterior training or paper-level claims.
- Support/vertical v2 factual-axis fill is complete: 127 rows are filled with
  endpoint, visibility, geometry answer, evidence strength, informativeness,
  ontology fit, and uncertainty fields. Direct reliability labels and binary
  targets are still absent; ingestion must derive targets only after label lock.
- Support/vertical v2 ingestion is complete: `geometry_validity_target_v2` has
  100 binary rows with 79 positives and 21 negatives, while
  `relation_reliability_target_v2` has 106 binary rows with 32 positives and 74
  negatives. Basic probe still finds hidden prior-label/construction correlation,
  so posterior smoke remains blocked until dedicated v2 target-independence audit.

## Claim Boundary

Allowed current claim:

```text
RGA provides a train-only framework for separating semantic confidence,
geometric satisfiability, coverage, uncertainty, and label/audit evidence at
relation-edge level.
```

Allowed current diagnostic claim:

```text
On the Open3DSG train full split, RGA exposes both high-semantic/low-geometry
and low-semantic/high-geometry states. The low-semantic/high-geometry state is
large but requires independent audit because it mixes true underconfidence,
annotation sparsity, ontology mismatch, and dense relation noise.
```

Allowed current revised-factor diagnostic claim:

```text
Under train-only Codex bootstrap labels, revised raw-witness factorization is
promising for support_contact and relative_vertical. Its gain largely disappears
when raw witness blocks are shuffled, so the current positive smoke is not
explained by predicate-family categorical shortcut alone.
```

Allowed current method-boundary claim:

```text
The defensible H002 method boundary is an RGA-scoped raw-witness residual
reliability layer for support_contact and relative_vertical. D4-style typed
family interactions are an experimental ablation, not the final method claim.
```

Blocked claims:

- RGA itself improves relation prediction.
- RGA-LH rows are automatically valid missing positives.
- working labels are paper-locked human annotations.
- `p_geom_valid` is full relation reliability.
- the factorized posterior outperforms rank-controlled baselines.
- proximity is a safe main ranking claim.
- typed family interaction is the final method design.
- the current `(codex_ver_full_train)` bootstrap target validates posterior
  novelty.
- blind labels are human-confirmed.
- label-ready status is a relation reliability label.
- codex-version independent labels alone validate posterior novelty.
- held-out validation/test conclusions.

## Next Step

The next H002 step is:

```text
full_train_independent_support_vertical_v2_target_independence_audit
```

Goal:

- determine whether strict controlled target slices exist for geometry validity
  and relation reliability.
- separate expected geometry alignment from harmful prior-label carryover.
- decide whether posterior smoke can proceed or v2 label policy/selection must
  be revised again.
- keep proximity outside the main label-ingestion path and preserve it as risk slice.
- keep generic high-capacity combiners deferred.
- keep the decision hypothesis-stage and train-only.
- keep multi-view as audit evidence only, not posterior input.
- keep validation/test unavailable.
- continue without paper-level posterior performance claims.
