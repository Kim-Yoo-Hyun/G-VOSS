# V66 Attachment Conditional Contrast Path Decision

## 목적

v21 full-train conditional contrast capacity scan 이후 다음 H002 route를 결정했다.
핵심 질문은 strict condition을 통과한 `hanging on`만 primary로 좁힐지, `attached to`까지
relaxed condition으로 함께 primary에 둘지였다.

## Strict Condition의 의미

strict condition은 데이터셋이 제공한 정답 rule이 아니다. H002에서 target construction을
검증하기 위해 만든 control rule이다.

```text
strict_spec = same_predicate_rank_geometry_family
fields = predicate_label + rank_band + geometry_bucket + object_family_pair
```

필요한 이유는 posterior target이 다음 쉬운 축 하나만으로 풀리는 것을 막기 위해서다.

- `predicate_label`: predicate만 보면 label이 갈리는 문제 방지
- `rank_band`: source rank 또는 semantic score band만 보면 label이 갈리는 문제 방지
- `geometry_bucket`: coarse geometry validity만 보면 label이 갈리는 문제 방지
- `object_family_pair`: object category prior만 보면 label이 갈리는 문제 방지

즉 strict condition은 final ontology나 model input rule이 아니라, factorized reliability
posterior가 실제로 semantic/geometry/coverage/uncertainty의 잔여 신호를 요구하는지 확인하기
위한 target-independence control이다.

## 입력

- Input artifact: `reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan/summary.json`
- v21 strict spec: `same_predicate_rank_geometry_family`
- v21 diagnostic spec: `same_predicate_rank_family`

## 결과

```text
status = h002_reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_select_v22_hanging_on_strict_packet_plan
selected_path = freeze_v21_capacity_diagnostic_select_hanging_on_strict_primary_attached_to_diagnostic_relaxed_probe
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan
validation_errors = 0
posterior_smoke_allowed = false
```

Capacity snapshot:

```text
strict_mixed_groups = 258
strict_balanced_capacity = 4507
strict_by_predicate = hanging on only
diagnostic_mixed_groups = 591
diagnostic_balanced_capacity = 53539
diagnostic_by_predicate = attached to + hanging on
```

## 결정

`hanging on`을 strict primary 후보로 남긴다.

`attached to`는 diagnostic/relaxed probe로 낮춘다.

`connected to`는 계속 diagnostic-only로 둔다.

## 왜 이 결정인가

`hanging on`은 strict condition 안에서도 mixed proxy strata가 남는다. 이는 predicate, rank,
coarse geometry bucket, object-family prior를 통제해도 reliability 후보가 갈릴 수 있다는
뜻이다. 따라서 다음 label packet을 만들 가치가 있다.

반대로 `attached to`는 relaxed diagnostic spec에서는 mixed capacity가 크지만, strict spec에서는
사라진다. 즉 `attached to`를 현재 primary에 포함하려면 geometry bucket control을 풀어야 한다.
그 상태에서 posterior 성능이 좋아져도 factorized reliability가 아니라 coarse geometry bucket
shortcut을 학습한 결과로 보일 위험이 크다.

## 다음 단계

```text
reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan
```

v22에서 해야 할 일:

- primary scope를 `hanging on`으로 고정한다.
- `attached to`와 `connected to`는 diagnostic-only로 둔다.
- packet rows target은 240으로 계획한다.
- pre-label gate는 strict mixed group, balanced capacity, scan cap, endpoint-pair cap, leakage 0을 요구한다.
- label fill, ingestion, posterior smoke는 v22 packet plan 이후에도 바로 허용하지 않는다.

## 산출물

- Script: `tools/reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan/`
- Summary: `summary.json`
- Path decision: `path_decision.json`
- Report: `report.md`
