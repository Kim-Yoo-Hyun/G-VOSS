# H002 Full-Train Independent Support/Vertical V2 User-Submitted Review Ingestion

## Purpose

`110_full_train_independent_support_vertical_v2_true_user_review_target_path_decision.md`에서
선택한 70-row `rank_band70` review sheet가 사용자에 의해 채워졌다고 보고되었다. 이번
단계는 그 sheet를 H002 train-only hypothesis artifact로 ingest하고, posterior smoke로
넘기기 전에 target materialization과 기본 shortcut probe를 수행한다.

핵심 질문:

```text
Does the completed rank_band70 sheet produce usable geometry-validity and
relation-reliability targets without immediately visible shortcut leakage?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- 사용자가 sheet를 채웠다고 보고했으므로 `user_submitted_completed_sheet=True`로 기록한다.
- 단, sheet 내부 `external_reviewer_id`가 모두 `codex_packet_only_diagnostic`이므로
  독립 external/human annotation으로 과장하지 않는다.
- review field와 hidden manifest join은 target/audit용이며 posterior input이 아니다.
- source score/rank, `p_geom_valid`, hidden prior labels는 label 작성 input으로 사용하지
  않았다는 전제를 artifact boundary에 기록한다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_user_submitted_review_ingested_with_basic_probe_risk
labels=70
geom_binary=68 geom_pos=57 geom_neg=11
rel_binary=68 rel_pos=35 rel_neg=33
errors=0
reviewer_id_caveat=True
validation_used=False test_used=False
next=user_submitted_rank_band70_target_independence_audit
```

## Completed Sheet Summary

| Field | Count |
| --- | ---: |
| rows | 70 |
| `external_reviewer_id=codex_packet_only_diagnostic` | 70 |
| `external_review_round=r1_20260619_packet_only` | 70 |
| visual pair evaluability `evaluable` | 68 |
| visual pair evaluability `occluded_or_unclear` | 2 |
| mesh pair evaluability `unclear` | 70 |
| visual geometry answer `supports_predicate` | 57 |
| visual geometry answer `contradicts_predicate` | 11 |
| visual geometry answer `uncertain` | 2 |
| final relation reliability `reliable` | 35 |
| final relation reliability `unreliable` | 33 |
| final relation reliability `uncertain` | 2 |

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_user_submitted_review_target` | 68 | 57 | 11 | 0.8382 | 2 |
| `relation_reliability_user_submitted_review_target` | 68 | 35 | 33 | 0.5147 | 2 |

## Basic Target-Independence Probe

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_user_submitted_review_target` | `target_independence_risk_hidden_metadata_correlated` | 2 | 0 |
| `relation_reliability_user_submitted_review_target` | `target_independence_risk_hidden_metadata_correlated` | 2 | 0 |

Interpretation:

- ingestion과 target materialization은 성공했다.
- geometry target은 기존 69/1보다 개선되어 57/11 binary target이 되었지만, negative
  count 11이라 아직 controlled posterior target으로 작다.
- relation reliability target은 35/33으로 균형이 좋고 visible shortcut은 0이다.
- 그러나 hidden metadata correlation risk가 남아 있어 dedicated target-independence
  audit 전에는 posterior smoke로 넘기지 않는다.
- reviewer id caveat 때문에 이 산출물은 user-submitted packet-only diagnostic으로 기록한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/111_full_train_independent_support_vertical_v2_user_submitted_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/validated_user_submitted_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/geometry_validity_user_submitted_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/relation_reliability_user_submitted_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/target_independence_probe.json
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
```

Observed:

```text
labels=70
geometry_target_binary_rows=68
relation_target_binary_rows=68
ingestion_errors=0
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
user_submitted_rank_band70_target_independence_audit
```

Goal:

- run dedicated target-independence audit on the user-submitted targets.
- check whether any strict or defensible controlled slice exists.
- keep posterior smoke blocked until target/evidence independence is defensible.
- keep reviewer-id caveat visible unless the user confirms the sheet provenance.
