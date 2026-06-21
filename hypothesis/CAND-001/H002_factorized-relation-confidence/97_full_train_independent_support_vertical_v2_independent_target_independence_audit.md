# H002 Full-Train Independent Support/Vertical V2 Independent Target Independence Audit

## Purpose

`96_full_train_independent_support_vertical_v2_independent_label_ingestion.md`에서
materialize한 independent targets가 posterior smoke에 들어갈 만큼 독립적인지
검사했다. 이번 audit은 기존 v2 target audit과 같은 원칙을 쓰되, target 이름과 label
source를 independent visible-only bootstrap으로 바꿔 다시 수행한 것이다.

핵심 질문:

```text
Can we construct a strict train-only relation-reliability slice that is not
explained by harmful prior-label carryover or target-construction metadata?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- hidden metadata는 independent label lock 이후 audit와 controlled-slice construction에만
  사용한다.
- independent label fields, hidden strata, v2 reference axes는 posterior input이 아니다.
- source score/rank와 `p_geom_valid` feature join은 여전히 pending이다.
- multi-view는 audit evidence pointer일 뿐 model input이 아니다.
- label source는 `codex_independent_support_vertical_visible_only_bootstrap`이며,
  human-confirmed paper evidence가 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_independent_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
test_used=False
relation_rows=102
relation_pos=32
relation_neg=70
errors=0
relation_strict=none
relation_construction=rank_band_balanced_independent
next=revise_independent_target_or_collect_human_confirmed_support_vertical_labels
```

## Per-Target Result

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_independent_target` | `blocked_no_controlled_slice` | 102 | 81 | 21 | `none` | `none` |
| `relation_reliability_independent_target` | `strict_blocked_construction_slice_available` | 102 | 32 | 70 | `none` | `rank_band_balanced_independent` |

Construction-only relation slice:

```text
relation_reliability_independent_target/rank_band_balanced_independent.jsonl
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
Codex independent visible-only labels improve the label-surface separation, but
they still do not provide a strict relation-reliability target for posterior
method validation.
```

좋아진 점:

- independent target ingestion 자체는 깨끗하다.
- target rows는 102개이고 validation error는 0이다.
- relation reliability에서 62-row `rank_band_balanced_independent` diagnostic slice가
  남는다.
- construction risk는 이 diagnostic slice에서 0으로 줄일 수 있다.

막힌 점:

- strict relation-reliability slice는 없다.
- `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden`
  carryover가 여전히 남는다.
- geometry target도 strict/diagnostic slice로 쓰기 어렵다.
- source score/rank와 `p_geom_valid`가 아직 join되지 않았더라도, target gate가 먼저
  막혀 있으므로 posterior smoke로 진행하면 안 된다.

가능한 사용:

- `rank_band_balanced_independent`를 plumbing/error-analysis diagnostic으로 사용.
- independent target이 왜 strict target이 되지 못하는지 failure analysis에 사용.
- human-confirmed label collection 설계의 근거로 사용.

불가능한 사용:

- factorized posterior가 relation reliability를 잘 설명한다고 주장.
- 현재 `(codex_independent_ver)` label을 paper-level independent annotation으로 주장.
- posterior performance claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/97_full_train_independent_support_vertical_v2_independent_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/target_slices/
```

Construction-only diagnostic slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/target_slices/relation_reliability_independent_target/rank_band_balanced_independent.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
```

Observed:

```text
validation_used=False
test_used=False
errors=0
relation_strict=none
relation_construction=rank_band_balanced_independent
```

Line counts:

```text
relation_reliability_independent_target/original_independent.jsonl = 102
relation_reliability_independent_target/rank_band_balanced_independent.jsonl = 62
geometry_validity_independent_target/original_independent.jsonl = 102
validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
98_full_train_independent_support_vertical_v2_human_label_path.md
```

Current next action:

```text
full_train_independent_support_vertical_v2_human_label_fill_or_external_review
```

Goal:

- fill the human sheet externally or with a clearly marked non-human placeholder only if explicitly requested.
- after filled labels exist, create human label ingestion.
- derive `geometry_validity_human_target` and `relation_reliability_human_target`.
- rerun target-independence audit.
- keep posterior smoke blocked until strict relation-reliability target evidence exists.
