# H002 Reliability Target V3 Positive-Anchor Plan

Date: 2026-06-20 KST

## Purpose

이 단계는 endpoint-controlled target path decision 이후, posterior smoke로 바로
넘어가지 않고 relation reliability target 자체를 다시 정의하기 위한 단계다.

이전 binary target은 다음 상태들을 모두 negative로 접었다.

- geometry contradiction
- trivial dense relation
- ontology / predicate granularity mismatch
- uncertain / not enough evidence

그 결과 relation reliability positive가 `2/32`로 너무 sparse해졌고, negative-majority
baseline만으로 `0.9412`가 나왔다. 따라서 현재 문제는 posterior combiner가 약한 것이
아니라, reliability target이 H002가 구분하려는 원인을 충분히 분리하지 못하는 것이다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training: not run.
- H001 artifacts: not modified.
- Multi-view / mesh evidence: audit packet evidence only, not model input.
- Hidden construction fields: post-label manifest에만 저장하고 label sheet에는 노출하지
  않는다.

## Command

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_positive_anchor_plan.py
```

## Result

```text
status = h002_reliability_target_v3_positive_anchor_plan_ready
selected_rows = 160
label_surface_leakage_hits = 0
packet_path_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_fill
```

## V3 Label Axes

V3 target은 binary reliability를 바로 묻지 않고, relation reliability를 구성하는 원인을
분해한다.

| Axis | Values | Role |
| --- | --- | --- |
| `endpoint_identity_v3` | `both_valid`, `subject_invalid`, `object_invalid`, `pair_invalid`, `uncertain` | subject/object pair 자체가 맞는지 확인 |
| `pair_evaluability_v3` | `evaluable`, `partially_evaluable`, `not_evaluable`, `uncertain` | 현재 evidence로 판단 가능한지 확인 |
| `geometry_support_v3` | `supports_predicate`, `contradicts_predicate`, `ambiguous`, `not_evaluable` | geometry가 predicate를 지지/반박하는지 확인 |
| `relation_usefulness_v3` | `informative`, `trivial_dense_or_room_structure`, `ontology_mismatch`, `uncertain` | geometry가 맞더라도 relation이 유의미한지 분리 |
| `relation_reliability_v3` | `reliable`, `unreliable_geometry`, `unreliable_trivial`, `unreliable_ontology`, `uncertain` | posterior target으로 derive할 최종 multi-class state |
| `primary_reason_v3` | controlled reason code | binary target으로 접기 전 failure 원인 기록 |
| `uncertainty_reason_v3` | controlled reason code | abstain/audit 대상 분리 |

핵심은 `geometry_support_v3`와 `relation_reliability_v3`를 동일하게 취급하지 않는
것이다. Geometry가 satisfied여도 relation이 trivial하거나 ontology granularity mismatch면
reliable positive가 아닐 수 있다.

## Sampling Plan

기존 independent asset packet manifest와 full-train RGA queue만 사용했다. 새로 validation
또는 test를 열지 않았고, 새 posterior feature도 만들지 않았다.

선택한 positive-anchor sheet는 4개 bucket을 40개씩 포함한다.

| Sampling Bucket | Rows | Support | Vertical | Unique Scans | Intended Role |
| --- | ---: | ---: | ---: | ---: | --- |
| `reliable_positive_anchor` | 40 | 20 | 20 | 32 | reliable positive mass 확보 |
| `geometry_contradiction_negative` | 40 | 20 | 20 | 31 | geometry contradiction negative |
| `trivial_dense_negative` | 40 | 20 | 20 | 21 | geometry-supported but unreliable/trivial negative |
| `ontology_or_uncertain_negative` | 40 | 30 | 10 | 21 | family/ontology granularity mismatch negative |

Candidate pool availability:

| Pool | Available |
| --- | ---: |
| `reliable_positive_anchor` | 57 |
| `geometry_contradiction_negative` | 80 |
| `trivial_dense_negative` | 103 |
| `ontology_or_uncertain_negative` | 46 |

## Interpretation

이 단계는 H002의 문제 정의를 더 강하게 만든다.

- `semantic score != geometry validity != relation reliability`를 target construction
  수준에서 보존한다.
- reliable positive를 의도적으로 확보하되, geometry-supported row를 무조건 positive로
  바꾸지 않는다.
- posterior smoke는 아직 금지한다. V3 label fill과 target-independence audit이 끝난 뒤에만
  binary 또는 multi-class reliability target을 derive할 수 있다.
- label sheet는 score, rank, queue, `p_geom_valid`, `geometry_status`,
  `label_match_status`, expected role 같은 hidden construction field를 포함하지 않는다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/138_reliability_target_v3_positive_anchor_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_positive_anchor_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_label_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_positive_anchor_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_positive_anchor_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_candidate_pool_packet_ready.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_bucket_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/packet_path_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_label_fill
```

다음 단계에서는 160-row v3 sheet의 human fields를 채운다. 사용자 지시에 따라 Codex가
proxy로 먼저 채우더라도, 이 label은 hypothesis-stage train-only evidence로만 취급한다.
Posterior smoke는 label ingestion과 target-independence audit 이후에만 재개한다.
