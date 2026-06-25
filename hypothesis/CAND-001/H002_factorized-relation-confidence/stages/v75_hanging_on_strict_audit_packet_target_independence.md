# V75 Hanging-On Strict Audit Packet Target Independence

## 목적

v74에서 만든 `hanging on` strict target artifacts가 posterior smoke로 넘어갈 수
있는지 target-independence gate로 검사했다.

검사 기준은 다음과 같다.

- primary relation binary target이 충분한 class mass를 갖는가.
- predicate/rank/geometry bucket/object/endpoint/scan/source 계열 shortcut을 통제한 slice가 남는가.
- strict 또는 diagnostic clear slice가 있어 posterior가 실제 factorized evidence를 필요로 하는가.

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit
rows = 240
validation_errors = 0
posterior_smoke_allowed = false
```

Primary relation reliability target:

```text
binary_rows = 202
positive = 9
negative = 193
minimum_per_class_for_posterior = 60
class_mass_pass = false
strict_clear_slices = 0
diagnostic_clear_slices = 0
```

Shortcut and slice audit:

```text
full_quick_probe_risk_flags = 107
slice_audit_rows = 138
slice_risk_rows = 4278
slice_blocking_risk_flags = 1666
```

Top risk predictors:

```text
object_family_pair_hidden = 6
primary_reason_v22 = 6
review_uncertainty = 6
subject_label = 6
object_label = 5
review_endpoint_identity = 5
review_geometry_support = 5
shared_origin_frame_bucket = 5
```

Balanced relation-binary slices remain too small:

```text
full_balanced_slice = 18 rows, 9/9
same_visible_pair_slice = 0 rows
same_strict_group_slice = 12 rows, 6/6
same_scan_slice = 4 rows, 2/2
same_subject_label_slice = 14 rows, 7/7
same_object_label_slice = 18 rows, 9/9
```

## 해석

사용자가 물은 "아직까지 같은 문제가 반복되는가"에 대한 답은 `yes`다.
이번 v75 audit에서도 같은 형태의 target-construction 병목이 확인됐다.

반복되는 문제는 두 가지다.

1. Positive-sparse target:
   `hanging on` strict packet은 full train에서 후보 수량과 audit packet은 만들 수 있었지만,
   visual/mesh evidence 기준 accept가 9개뿐이다. 이 수량으로는 posterior가 factorized
   evidence를 학습했는지, 아니면 majority/reject prior를 따르는지 구분할 수 없다.

2. Shortcut-controlled slice 부족:
   균형 slice를 만들면 최대 `9/9` 수준에 머물고, 같은 visible endpoint pair 안에서는
   accept/reject contrast가 0개다. 따라서 posterior smoke를 돌려도 relation reliability의
   원리적 분해를 검증했다기보다 target construction artifact를 맞춘 결과로 보일 위험이 크다.

중요한 점은 이것이 H002 명제의 실패가 아니라는 것이다. H002가 요구하는 target은
`semantic score`, `geometry validity`, `coverage`, `uncertainty`를 분리해야만 풀리는
target이어야 한다. v75는 현재 `hanging on` strict target이 그 조건을 만족하지 못한다고
잠근 단계다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit/`
- Summary: `summary.json`
- Report: `report.md`
- Target decisions: `target_decisions.json`
- Class mass audit: `class_mass_audit.json`
- Shortcut risks: `full_shortcut_risks.json`, `risk_flag_summary.json`
- Slice audit: `controlled_slice_audit.csv`, `slice_risks.json`
- Validation errors: `validation_errors.jsonl`

## 다음 단계

`reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit`

다음 path decision에서는 다음 중 하나를 선택해야 한다.

- v22 `hanging on` strict target을 diagnostic-only negative target-construction evidence로 고정한다.
- 더 많은 positive anchor를 찾기 위해 `hanging on` positive-focused mining을 하되, endpoint/object shortcut을 새로 막는다.
- `attached to` relaxed diagnostic route나 multi-relation attachment route로 돌아갈지 판단한다.
- posterior smoke, stronger combiner, or current `9/193` target balancing은 현재 gate 기준으로는 진행하지 않는다.
