# H002 Full-Train Independent Support/Vertical V2 Human Label Fill

## Purpose

`98_full_train_independent_support_vertical_v2_human_label_path.md`에서 만든
human collection sheet를 사용자 요청에 따라 Codex가 대신 채웠다.

이번 단계의 역할은 다음과 같다.

- minimum 96-row sheet와 full 127-row sheet의 `human_*` fields를 채운다.
- 채운 값은 hypothesis workflow에서는 user-requested human-confirmed proxy로 취급한다.
- 단, provenance는 실제 외부 human annotation이 아니라
  `codex_proxy_user_review_pending`로 유지한다.
- paper-level evidence로 사용하기 전에는 사용자 확인이 필요하다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- source score/rank, `p_geom_valid`, hidden target, previous label은 labeler-visible
  field로 쓰지 않는다.
- Codex가 채운 값은 사용자가 확인하기 전까지 external human annotation이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_human_fields_filled_codex_proxy_user_review_pending
min_rows=96 min_binary=81 min_pos=32 min_neg=49
full_rows=127 full_binary=102 full_pos=32 full_neg=70
errors=0 validation_used=False test_used=False
next=full_train_independent_support_vertical_v2_human_label_ingestion
```

## Output Summary

| Batch | Rows | Binary | Positive | Negative | Uncertain | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `minimum_human_batch_96` | 96 | 81 | 32 | 49 | 15 | 0 |
| `full_human_batch_127` | 127 | 102 | 32 | 70 | 25 | 0 |

Interpretation:

- Full 127-row batch가 primary path다.
- 102 binary rows는 support/vertical scoped hypothesis-stage gate를 넘는다.
- Positive 32 / negative 70으로 class imbalance는 존재하지만 per-class minimum은 넘는다.
- `uncertain` 25 rows는 hard target에서 제외하고 audit/coverage evidence로 유지한다.

## Provenance

이번 fill은 다음 의미로만 사용한다.

```text
filled_by = codex_proxy
user_request = treat_as_human_confirmed_for_next_hypothesis_steps
user_review_pending = true
paper_evidence_allowed_before_user_confirmation = false
```

따라서 이후 ingestion과 target-independence audit은 진행할 수 있지만, 논문 claim에서는
다음처럼 써야 한다.

```text
human-confirmed by user review, pending final user acceptance
```

사용자 확인 전에는 다음 표현을 쓰지 않는다.

```text
independent human annotation completed
paper-locked human labels
external human-confirmed benchmark
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/completed_minimum_human_collection_sheet_codex_proxy_user_review_pending.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/completed_full_human_collection_sheet_codex_proxy_user_review_pending.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/minimum_human_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/full_human_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/fill_validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
```

Observed line counts:

```text
completed_minimum_human_collection_sheet_codex_proxy_user_review_pending.tsv = 96 rows + header
completed_full_human_collection_sheet_codex_proxy_user_review_pending.tsv = 127 rows + header
minimum_human_proxy_labels.jsonl = 96
full_human_proxy_labels.jsonl = 127
fill_validation_errors.jsonl = 0
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_human_label_ingestion
```

Goal:

- ingest the full 127-row filled sheet.
- derive `geometry_validity_human_target`.
- derive `relation_reliability_human_target`.
- keep `uncertain` rows excluded from binary targets.
- run a basic leakage/shortcut probe before the dedicated target-independence audit.
