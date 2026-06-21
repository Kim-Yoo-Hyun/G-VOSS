# H002 Full-Train Independent Support/Vertical V2 Target Independence Audit

## Purpose

`92_full_train_independent_support_vertical_v2_label_ingestion.md`에서 v2 factual
axes로부터 `geometry_validity_target_v2`와 `relation_reliability_target_v2`를
분리해 materialize했다. 이번 단계는 이 target들이 posterior smoke에 들어갈 만큼
독립적인지 확인하고, controlled slice가 남는지 검사한다.

핵심 질문:

```text
Can we construct a train-only controlled target slice for relation reliability
that is not explained by harmful prior-label carryover or target-construction
metadata?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- label은 Codex bootstrap label이며 human-confirmed가 아니다.
- hidden metadata는 label-lock 이후 audit와 controlled-slice construction에만 사용한다.
- v2 target-derivation fields는 audit-only이며 posterior input이 아니다.
- multi-view는 audit evidence pointer일 뿐 posterior input이 아니다.
- paper-level posterior claim은 허용하지 않는다.

## Audit Modes

이번 v2 audit은 risk를 세 종류로 분리한다.

### Harmful Prior Carryover

이 mode는 이전 bootstrap label/use와의 직접 carryover를 본다. 이 risk가 남으면
posterior method validation으로 진행할 수 없다.

```text
relation_validity_label_hidden
label_use_hidden
posterior_target_y_hidden
```

### Construction Risk

이 mode는 selected target을 만든 queue/rank/role/label-match construction shortcut을
본다.

```text
rank_band_hidden
proposed_audit_role_hidden
queue_kind_hidden
label_match_status_hidden
```

### Expected Geometry Alignment

이 mode는 geometry target과 hidden geometry status의 정렬을 따로 보고한다.
geometry validity target에서는 어느 정도 기대되는 정렬이므로 harmful prior carryover와
같은 blocker로 취급하지 않는다.

```text
geometry_status_hidden
```

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
test_used=False
relation_rows=106
relation_pos=32
relation_neg=74
errors=0
relation_strict=none
relation_construction=rank_band_balanced_v2
next=revise_full_train_independent_support_vertical_v2_target_or_collect_independent_labels
```

## Per-Target Result

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_target_v2` | `blocked_no_controlled_slice` | 100 | 79 | 21 | `none` | `none` |
| `relation_reliability_target_v2` | `strict_blocked_construction_slice_available` | 106 | 32 | 74 | `none` | `rank_band_balanced_v2` |

Construction-only relation slice:

```text
relation_reliability_target_v2/rank_band_balanced_v2.jsonl
rows = 62
positive = 31
negative = 31
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 0
```

이 slice는 rank-band construction shortcut을 줄인 diagnostic에는 쓸 수 있지만,
harmful prior carryover가 남아 있으므로 posterior method validation에는 부족하다.

## Original Target Risks

### Geometry Validity Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.8600 | 0.4610 | 1.0000 |
| harmful prior carryover | `label_use_hidden` | 0.7900 | 0.3242 | 0.4476 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.7900 | 0.3242 | 0.4476 |
| construction | `proposed_audit_role_hidden` | 0.8100 | 0.2688 | 1.0000 |
| construction | `rank_band_hidden` | 0.8300 | 0.2065 | 0.6250 |
| visible non-target | `predicate_label` | 0.8200 | 0.1932 | 0.5500 |

### Relation Reliability Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.7547 | 0.3313 | 0.6250 |
| harmful prior carryover | `label_use_hidden` | 0.7453 | 0.3196 | 0.5235 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.7453 | 0.3196 | 0.5235 |
| construction | `rank_band_hidden` | 0.7075 | 0.1686 | 0.5556 |
| construction | `proposed_audit_role_hidden` | 0.7075 | 0.1630 | 1.0000 |
| construction | `queue_kind_hidden` | 0.6981 | 0.1410 | 0.3746 |
| expected geometry alignment | `geometry_status_hidden` | 0.6981 | 0.1410 | 0.3746 |
| visible non-target | `evidence_packet_status` | 0.7170 | 0.0376 | 0.7115 |

## Interpretation

이번 audit의 결론은 다음과 같다.

```text
V2 target factorization succeeded structurally, but the current Codex bootstrap
target is still not independent enough for posterior method validation.
```

좋아진 점:

- `geometry_validity_target_v2`와 `relation_reliability_target_v2`가 명확히 분리됐다.
- expected geometry alignment와 harmful prior-label carryover를 구분해 보고할 수 있게 됐다.
- relation reliability에서 `rank_band_balanced_v2` construction-only diagnostic slice가
  남았다.

막힌 점:

- relation reliability strict slice는 없다.
- `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden`
  carryover가 여전히 남는다.
- 따라서 posterior smoke를 method evidence로 진행하면 안 된다.

가능한 사용:

- `rank_band_balanced_v2`를 plumbing/error-analysis diagnostic으로 사용.
- v2 target revision 전후 비교 기준으로 사용.
- label policy가 target을 어떻게 shortcut으로 만들었는지 분석.

불가능한 사용:

- factorized posterior가 relation reliability를 잘 설명한다고 주장.
- 현재 v2 Codex bootstrap target을 independent label이라고 주장.
- paper-level posterior improvement claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/target_slices/
```

Construction-only diagnostic slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_independence_audit_codex_ver/target_slices/relation_reliability_target_v2/rank_band_balanced_v2.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_independence_audit.py
```

Observed:

```text
validation_used=False
test_used=False
errors=0
relation_strict=none
relation_construction=rank_band_balanced_v2
```

Line counts:

```text
relation_reliability_target_v2/original_v2.jsonl = 106
relation_reliability_target_v2/rank_band_balanced_v2.jsonl = 62
geometry_validity_target_v2/original_v2.jsonl = 100
validation_errors.jsonl = 0
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_independent_label_fill_or_human_review
```

Goal:

- target path decision은 `94_full_train_independent_support_vertical_v2_target_path_decision.md`에서 완료됐다.
- stronger independent label collection path를 선택했다.
- labeler-visible sheet를 실제 독립 reviewer 또는 human review로 채운다.
- keep posterior smoke blocked until strict relation-reliability target evidence exists.
