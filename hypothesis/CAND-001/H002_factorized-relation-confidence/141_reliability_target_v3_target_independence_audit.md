# H002 Reliability Target V3 Target Independence Audit

Date: 2026-06-20 KST

## Purpose

이 단계는 `140_reliability_target_v3_label_ingestion.md`에서 materialize한 v3 target이
posterior smoke에 쓸 수 있을 만큼 독립적인지 확인한다. 핵심은 positive mass가 생겼는지가
아니라, target이 hidden sampling bucket, endpoint flag, object label 같은 shortcut으로 쉽게
맞춰지는지를 보는 것이다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training: not run.
- H001 artifacts: not modified.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- Hidden metadata is used only after label lock for audit and slice construction.
- V3 review fields, hidden buckets, audit packet paths, and multi-view evidence are not posterior inputs.
- Geometry alignment risk is reported separately from hidden provenance and object-label shortcut risk.

## Command

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_target_independence_audit.py
```

## Result

```text
status = h002_reliability_target_v3_target_independence_audit_blocked_no_controlled_slice
relation_rows = 110
relation_pos = 32
relation_neg = 78
errors = 0
relation_strict = none
relation_diagnostic = none
validation_used = False
test_used = False
next = reliability_target_v3_path_decision
```

Decision:

```text
No controlled relation reliability slice clears hidden, endpoint, construction,
and object-label shortcut checks.
```

## Per-Target Decisions

| Target | Status | Rows | Positive | Negative | Strict Slice | Diagnostic Slice | Geometry-Only Slice |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `relation_reliability_v3_binary_target` | `blocked_no_controlled_slice` | 110 | 32 | 78 | `none` | `none` | `none` |
| `geometry_support_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 92 | 21 | `none` | `none` | `none` |
| `relation_usefulness_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 34 | 79 | `none` | `none` | `none` |

## Main Reliability Target Risks

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| hidden provenance | `sampling_category_hidden` | 0.7091 | 0.1640 | 0.4364 |
| hidden provenance | `expected_v3_role_hidden` | 0.7091 | 0.1640 | 0.4364 |
| endpoint pattern | `endpoint_flag_pattern_hidden` | 0.9182 | 0.5978 | 1.0000 |
| construction | `rank_band_hidden` | 0.7182 | 0.1680 | 0.6667 |
| construction | `queue_kind_hidden` | 0.7091 | 0.1499 | 0.3723 |
| expected geometry alignment | `geometry_status_hidden` | 0.7091 | 0.1499 | 0.3723 |
| visible object identity | `object_label` | 0.9545 | 0.8587 | 1.0000 |
| visible object identity | `subject_label` | 0.9091 | 0.7070 | 1.0000 |

Interpretation:

- `relation_reliability_v3_binary_target`의 positive sparsity는 이전보다 개선됐다.
- 하지만 target independence는 해결되지 않았다.
- 특히 endpoint flag pattern과 subject/object label만으로 target을 강하게 예측할 수 있다.
- 따라서 지금 posterior smoke를 돌리면 factorized reliability를 검증하는 것이 아니라
  endpoint/object shortcut을 맞출 위험이 크다.

## Controlled Slice Check

Representative relation reliability slices:

| Slice | Rows | Positive | Negative | Hidden Risk | Endpoint Risk | Construction Risk | Object Risk | Strict | Diagnostic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `sampling_category_balanced_v3` | 64 | 32 | 32 | 0 | 1 | 1 | 2 | `False` | `False` |
| `rank_band_balanced_v3` | 62 | 31 | 31 | 0 | 1 | 0 | 2 | `False` | `False` |
| `endpoint_pattern_balanced_v3` | 18 | 9 | 9 | 2 | 0 | 2 | 2 | `False` | `False` |
| `subject_label_balanced_v3` | 20 | 10 | 10 | 2 | 1 | 2 | 1 | `False` | `False` |
| `object_label_balanced_v3` | 10 | 5 | 5 | 2 | 1 | 3 | 1 | `False` | `False` |

Balanced slices do exist, but they do not clear the shortcut checks. Some remove
hidden bucket imbalance, but endpoint/object risk remains. Endpoint/object-balanced
slices are too small or still carry construction risks.

## Interpretation

이번 audit의 의미는 다음과 같다.

- Positive-sparse target 문제는 줄었다.
- 그러나 posterior-ready target 문제는 아직 해결되지 않았다.
- 현재 v3 Codex-proxy target은 visible object identity와 endpoint structure에 너무 많이
  얽혀 있다.
- `geometry_support_v3_binary_target`은 사실상 geometry status와 relation surface를
  재학습할 위험이 크고, `relation_usefulness_v3_binary_target`도 object shortcut이 강하다.
- 따라서 다음 단계는 combiner upgrade나 posterior smoke가 아니라 path decision이다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/141_reliability_target_v3_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_path_decision
```

이 path decision에서는 다음 중 어떤 방향으로 갈지 정해야 한다.

- v3 label policy를 다시 수정한다.
- endpoint/object-controlled resampling을 더 확장한다.
- Codex proxy target을 폐기하고 실제 independent human/audit label을 모은다.
- posterior smoke를 계속 보류하고 RGA target construction 문제를 먼저 논문화 가능한
  diagnostic claim으로 정리한다.
