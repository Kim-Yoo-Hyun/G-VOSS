# H002 Full-Train Independent Support/Vertical V2 External Review Target Independence Audit

## Purpose

`104_full_train_independent_support_vertical_v2_external_review_ingestion.md`에서 만든
external targets가 posterior smoke에 들어갈 만큼 독립적인지 검사했다.

핵심 질문:

```text
Does the revised external-review target clear harmful prior-label carryover
after hiding numeric witnesses, previous proxy labels, source rank, p_geom_valid,
and visible construction fields from the review surface?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- labels are user-requested Codex proxy external review fields.
- external review fields, hidden strata, previous proxy labels, and audit packet
  paths are not posterior inputs.
- hidden metadata는 label lock 이후 audit와 controlled-slice construction에만 쓴다.
- source score/rank와 `p_geom_valid` feature join은 여전히 pending이다.
- paper-level external human annotation claim은 아직 금지한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_external_review_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
test_used=False
relation_rows=116
relation_pos=47
relation_neg=69
errors=0
relation_strict=none
relation_construction=rank_band_balanced_external
next=revise_external_review_or_collect_true_user_labels
```

## Per-Target Result

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_external_target` | `blocked_no_controlled_slice` | 116 | 105 | 11 | `none` | `none` |
| `relation_reliability_external_target` | `strict_blocked_construction_slice_available` | 116 | 47 | 69 | `none` | `rank_band_balanced_external` |

Construction-only relation slice:

```text
relation_reliability_external_target/rank_band_balanced_external.jsonl
rows = 70
positive = 35
negative = 35
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 0
```

이 slice는 이전보다 훨씬 나은 diagnostic이다. visible shortcut과 construction risk는
0으로 줄었지만, harmful prior carryover가 남아 strict method-validation target은 아니다.

## Original Target Risks

### Geometry Validity Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.9310 | 0.3689 | 0.7143 |
| harmful prior carryover | `label_use_hidden` | 0.9052 | 0.1697 | 0.1848 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.9052 | 0.1697 | 0.1848 |
| construction | `rank_band_hidden` | 0.9052 | 0.4473 | 0.5000 |
| construction | `proposed_audit_role_hidden` | 0.9052 | 0.3769 | 0.5000 |
| visible non-target | `predicate_label` | 0.9052 | 0.3252 | 0.3462 |

### Relation Reliability Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.7845 | 0.4246 | 0.7826 |
| harmful prior carryover | `label_use_hidden` | 0.7845 | 0.3186 | 0.6067 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.7845 | 0.3186 | 0.6067 |
| construction | `rank_band_hidden` | 0.6983 | 0.1860 | 0.6667 |
| construction | `proposed_audit_role_hidden` | 0.6638 | 0.1692 | 0.7143 |
| expected geometry alignment | none | 0.0000 | 0.0000 | 0.0000 |
| visible non-target | none | 0.0000 | 0.0000 | 0.0000 |

## Interpretation

이번 audit의 결론:

```text
The revised external-review surface reduces visible and construction shortcut
risk, but the user-requested Codex proxy target still does not clear harmful
prior-label carryover.
```

좋아진 점:

- relation reliability binary rows가 116으로 늘었다.
- relation reliability original target에서 visible non-target risk가 0이다.
- `rank_band_balanced_external` diagnostic slice는 70 rows, 35/35로 이전
  `rank_band_balanced_human` 62 rows보다 크다.
- 이 diagnostic slice에서는 construction risk, expected geometry alignment risk,
  visible non-target risk가 모두 0이다.

막힌 점:

- strict relation-reliability slice는 없다.
- `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden`
  carryover가 여전히 남는다.
- geometry validity target은 class imbalance와 hidden/construction risk 때문에
  controlled target으로 쓰기 어렵다.
- 현재 상태에서 posterior smoke를 실행하면 relation reliability modeling인지 hidden prior
  carryover fitting인지 구분할 수 없다.

가능한 사용:

- `rank_band_balanced_external`을 plumbing/error-analysis diagnostic으로 사용.
- external review surface가 visible shortcut을 줄였다는 evidence로 사용.
- true user/external label collection 설계 근거로 사용.

불가능한 사용:

- factorized posterior performance claim.
- paper-level external human annotation claim.
- posterior method-validation target claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/105_full_train_independent_support_vertical_v2_external_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/target_slices/
```

Construction-only diagnostic slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/target_slices/relation_reliability_external_target/rank_band_balanced_external.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
```

Line counts:

```text
relation_reliability_external_target/original_external.jsonl = 116
relation_reliability_external_target/rank_band_balanced_external.jsonl = 70
geometry_validity_external_target/original_external.jsonl = 116
validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
106_full_train_independent_support_vertical_v2_true_user_review_path
```

Goal:

- The path decision and true-user review sheets were created in
  `106_full_train_independent_support_vertical_v2_true_user_review_path.md`.
- Current active next action is
  `fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels`.
