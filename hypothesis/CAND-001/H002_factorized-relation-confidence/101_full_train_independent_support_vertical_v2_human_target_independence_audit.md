# H002 Full-Train Independent Support/Vertical V2 Human Target Independence Audit

## Purpose

`100_full_train_independent_support_vertical_v2_human_label_ingestion.md`에서 만든
Codex-proxy human targets가 posterior smoke에 들어갈 만큼 독립적인지 검사했다.

핵심 질문:

```text
Can the user-requested human-proxy relation reliability target avoid harmful
prior-label carryover and construction shortcuts?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- workflow에서는 사용자 요청에 따라 human-confirmed로 취급한다.
- provenance는 `codex_proxy_user_review_pending`이다.
- 사용자 최종 확인 전에는 external human annotation 또는 paper-locked human label로
  주장하지 않는다.
- hidden metadata는 label lock 이후 audit와 controlled-slice construction에만 쓴다.
- human label fields, hidden strata, v2 reference axes는 posterior input이 아니다.
- source score/rank와 `p_geom_valid` feature join은 여전히 pending이다.
- multi-view는 audit evidence일 뿐 model input이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_human_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
test_used=False
relation_rows=102
relation_pos=32
relation_neg=70
errors=0
relation_strict=none
relation_construction=rank_band_balanced_human
next=revise_human_label_protocol_or_add_external_review_evidence
```

## Per-Target Result

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_human_target` | `blocked_no_controlled_slice` | 102 | 81 | 21 | `none` | `none` |
| `relation_reliability_human_target` | `strict_blocked_construction_slice_available` | 102 | 32 | 70 | `none` | `rank_band_balanced_human` |

Construction-only relation slice:

```text
relation_reliability_human_target/rank_band_balanced_human.jsonl
rows = 62
positive = 31
negative = 31
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 1
```

이 slice는 rank-band construction shortcut을 줄인 diagnostic에는 쓸 수 있지만,
harmful prior carryover가 남아 있으므로 posterior method validation에는 부족하다.

## Original Target Risks

### Geometry Validity Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.8627 | 0.4491 | 1.0000 |
| harmful prior carryover | `label_use_hidden` | 0.7941 | 0.3069 | 0.4269 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.7941 | 0.3069 | 0.4269 |
| construction | `proposed_audit_role_hidden` | 0.8137 | 0.2674 | 1.0000 |
| construction | `rank_band_hidden` | 0.8333 | 0.2060 | 0.6250 |
| visible non-target | `predicate_label` | 0.8235 | 0.1986 | 0.5545 |

### Relation Reliability Target

| Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| harmful prior carryover | `relation_validity_label_hidden` | 0.7451 | 0.3166 | 0.6250 |
| harmful prior carryover | `label_use_hidden` | 0.7353 | 0.3052 | 0.5216 |
| harmful prior carryover | `posterior_target_y_hidden` | 0.7353 | 0.3052 | 0.5216 |
| construction | `rank_band_hidden` | 0.6961 | 0.1521 | 0.5556 |
| construction | `proposed_audit_role_hidden` | 0.6961 | 0.1455 | 1.0000 |
| construction | `queue_kind_hidden` | 0.6863 | 0.1234 | 0.3694 |
| expected geometry alignment | `geometry_status_hidden` | 0.6863 | 0.1234 | 0.3694 |
| visible non-target | `evidence_packet_status` | 0.7059 | 0.0372 | 0.7000 |

## Interpretation

이번 audit의 결론:

```text
Treating the Codex-filled fields as human-confirmed for workflow progression
does not solve the target-independence blocker.
```

좋아진 점:

- full 127-row proxy-human sheet를 ingest했고 validation error는 0이다.
- relation reliability target은 102 binary rows, positive 32 / negative 70이다.
- 62-row `rank_band_balanced_human` construction diagnostic slice는 있다.

막힌 점:

- strict relation-reliability slice는 없다.
- `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden`
  carryover가 여전히 남는다.
- geometry validity target도 strict/diagnostic target으로 쓰기 어렵다.
- 현재 상태에서 posterior smoke를 실행하면 target construction shortcut을 더 잘 맞추는지
  relation reliability를 더 잘 설명하는지 구분하기 어렵다.

가능한 사용:

- `rank_band_balanced_human`을 plumbing/error-analysis diagnostic으로 사용.
- label protocol이 왜 여전히 독립 target을 만들지 못하는지 failure analysis에 사용.
- 다음 label/evidence revision의 설계 근거로 사용.

불가능한 사용:

- factorized posterior가 relation reliability를 잘 설명한다고 주장.
- 현재 proxy-human labels를 paper-level external human annotation으로 주장.
- posterior performance claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/101_full_train_independent_support_vertical_v2_human_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/target_slices/
```

Construction-only diagnostic slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/target_slices/relation_reliability_human_target/rank_band_balanced_human.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
```

Observed:

```text
validation_used=False
test_used=False
errors=0
relation_strict=none
relation_construction=rank_band_balanced_human
```

Line counts:

```text
relation_reliability_human_target/original_human.jsonl = 102
relation_reliability_human_target/rank_band_balanced_human.jsonl = 62
geometry_validity_human_target/original_human.jsonl = 102
validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
102_full_train_independent_support_vertical_v2_external_review_protocol
```

Goal:

- The protocol revision was completed in
  `102_full_train_independent_support_vertical_v2_external_review_protocol.md`.
- Current active next action is `fill_external_evidence_review_sheet_or_user_review`.
