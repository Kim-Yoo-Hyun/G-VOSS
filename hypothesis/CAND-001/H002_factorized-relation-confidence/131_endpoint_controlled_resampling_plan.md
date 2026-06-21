# Endpoint-Controlled Resampling Plan

## Purpose

`130_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.md`
의 next TODO인 `revised_sampling_all_label_ready_endpoint_controlled_resampling_plan`을
진행했다.

핵심 질문:

```text
Can the current all-label-ready support/vertical slice be resampled so that
endpoint/object-type shortcut no longer dominates the target?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test row는 사용하지 않았다.
- 새 posterior model은 학습하지 않았다.
- endpoint/object-type feature는 target/control construction에만 사용하고, deployable
  model evidence로 사용하지 않는다.
- 결과는 hypothesis-stage planning artifact이며 paper-level metric evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_resampling_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_resampling_plan.py
```

Observed:

```text
status=h002_endpoint_controlled_resampling_plan_ready_needs_label_expansion
rows=134
pos=67
neg=67
strict_endpoint_seed_rows=24
relaxed_object_role_seed_rows=44
strict_endpoint_d_auprc_vs_c3=-0.0112
relaxed_object_role_d_auprc_vs_c3=0.0780
needed_positive_labels_to_cap=36
needed_negative_labels_to_cap=26
next=revised_sampling_endpoint_controlled_candidate_mining
```

## Result

Status:

```text
h002_endpoint_controlled_resampling_plan_ready_needs_label_expansion
```

현재 all-label-ready 134-row pool만으로는 endpoint-controlled posterior smoke를 바로
진행하지 않는다. 이유는 다음과 같다.

- strict endpoint-flag matching은 endpoint shortcut을 거의 제거하지만 24 rows만 남는다.
- relaxed object-role matching은 44 rows를 남기지만 endpoint-only가 아직 C3보다 AUPRC
  `+0.0780` 높다.
- exact subject-predicate-object endpoint label pattern은 너무 엄격해서 balanced row가 0이다.

## Protocol Candidates

| Protocol | Matching Keys | Rows | Retention | Endpoint dAUPRC vs C3 | Endpoint AUROC | C3 AUPRC | Usable Now |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `P0_current_all` | `none` | 134 | 1.0000 | +0.3167 | 0.9581 | 0.6246 | false |
| `P1_family_only` | `predicate_family` | 132 | 0.9851 | +0.3114 | 0.9573 | 0.6292 | false |
| `P2_predicate_label` | `predicate_label` | 100 | 0.7463 | +0.3153 | 0.9538 | 0.6218 | false |
| `P3_object_role` | `object_role` | 44 | 0.3284 | +0.0780 | 0.7655 | 0.6501 | false |
| `P4_family_object_role` | `predicate_family + object_role` | 44 | 0.3284 | +0.1325 | 0.7521 | 0.5942 | false |
| `P5_family_object_subject_role` | `predicate_family + object_role + subject_role` | 24 | 0.1791 | -0.0112 | 0.5243 | 0.6298 | false |
| `P6_predicate_object_role` | `predicate_label + object_role` | 30 | 0.2239 | +0.0540 | 0.7489 | 0.6947 | false |
| `P7_strict_endpoint_flag` | `endpoint_flag_pattern` | 24 | 0.1791 | -0.0112 | 0.5243 | 0.6298 | false |
| `P8_strict_endpoint_flag_rank` | `endpoint_flag_pattern + rank_bin` | 22 | 0.1642 | +0.0735 | 0.5289 | 0.5843 | false |
| `P9_endpoint_label_pattern` | `endpoint_label_pattern` | 0 | 0.0000 | nan | nan | nan | false |

해석:

- `P7_strict_endpoint_flag`가 shortcut control 관점에서는 가장 원리적으로 맞다.
- 하지만 `P7`은 24 rows라 posterior smoke, family split, calibration 판단에 부족하다.
- `P3_object_role`은 row 수는 조금 늘지만 shortcut이 충분히 제거되지 않는다.
- 따라서 `P7`을 primary matching key로 유지하고 label expansion을 진행해야 한다.

## Recommended Protocol

Primary matching key:

```text
endpoint_flag_pattern
```

`endpoint_flag_pattern`은 다음 요소로 구성한다.

```text
endpoint_object_floor_like_flag
endpoint_object_support_surface_like_flag
endpoint_object_wall_like_flag
endpoint_subject_room_surface_flag
relative_vertical_gate
support_contact_gate
```

Protocol:

1. 각 `endpoint_flag_pattern` 안에서 positive/negative를 맞춘다.
2. 기존 `rank_band` balance는 secondary audit key로 유지하되, endpoint control보다 우선하지 않는다.
3. exact subject/object class label은 primary key로 쓰지 않는다. 현재 pool에서는 너무 엄격해서 0 rows가 남는다.
4. `object_role`은 relaxed diagnostic seed로만 둔다.
5. endpoint/object-type feature는 posterior input으로 사용하지 않는다.

Current seed:

```text
strict_endpoint_seed_rows = 24
relaxed_object_role_seed_rows = 44
minimum_posterior_rows = 80
target_expanded_rows = 120
target_per_endpoint_key_per_class_cap = 8
```

Label expansion deficit under the capped endpoint-key plan:

```text
needed_positive_labels_to_cap = 36
needed_negative_labels_to_cap = 26
```

즉, 현재 라벨만 재배열하는 것으로는 부족하고, endpoint key별로 부족한 반대편 label을
추가로 찾아야 한다.

## Decision

현재 결론:

```text
The current all-label-ready pool is not sufficient for endpoint-controlled posterior
smoke. Use strict endpoint_flag_pattern matching as the primary resampling protocol,
then mine additional candidates for missing positive/negative labels per endpoint key.
```

이 결정은 H002의 방향을 바꾸는 것이 아니다. 오히려 기존 failure 원인을 더 엄격히
제거하는 단계다.

- combiner를 강하게 만들기 전에 target shortcut을 줄인다.
- C3는 current reference로 유지한다.
- typed raw witness는 main geometry evidence axis로 유지한다.
- family-separated posterior는 endpoint-controlled slice가 확보된 뒤로 미룬다.

Allowed claim:

```text
Train-only planning shows that endpoint-controlled matching is necessary before
interpreting further posterior-combiner improvements, because the current
all-label-ready slice is either shortcut-dominated or too small after strict
endpoint control.
```

Blocked claims:

- current 134-row slice is sufficient for endpoint-controlled posterior smoke.
- object-role-only relaxed matching fully removes endpoint shortcut.
- endpoint/object-type features should be promoted to deployable model input.
- stronger combiner or family-separated posterior should be tested before endpoint-controlled label expansion.
- validation/test performance can be inferred from this planning artifact.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/131_endpoint_controlled_resampling_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_resampling_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/protocol_candidates.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/endpoint_key_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/endpoint_label_deficits.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/strict_endpoint_seed_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/relaxed_object_role_seed_rows.jsonl
```

Artifact row counts:

```text
protocol_candidates.csv = 11 lines
endpoint_key_groups.csv = 31 lines
endpoint_label_deficits.csv = 14 lines
strict_endpoint_seed_rows.jsonl = 24
relaxed_object_role_seed_rows.jsonl = 44
```

## Next TODO

```text
revised_sampling_endpoint_controlled_candidate_mining
```

Goal:

- mine additional train-only candidates for endpoint keys that lack opposite-label examples.
- prioritize pure endpoint groups where current labels are all positive or all negative.
- keep endpoint fields as sampling/audit fields only.
- produce a candidate packet for label fill before rerunning posterior smoke.
