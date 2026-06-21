# H002 Full-Train Independent Support/Vertical V2 True User Review Fill

## Purpose

`106_full_train_independent_support_vertical_v2_true_user_review_path.md`에서 만든
70-row `rank_band70` true-user review sheet를 채웠다.

중요한 boundary:

- 이 단계의 fill은 실제 human/external reviewer가 직접 확정한 label이 아니다.
- 사용자 요청에 따라 다음 workflow 진행을 위해 Codex가 proxy로 채웠다.
- 따라서 산출물은 `codex_proxy_true_user_review_pending_confirmation` 상태다.
- 다음 ingestion 단계에서는 workflow상 user-confirmed label처럼 다룰 수 있지만,
  paper evidence 또는 method-validation evidence로 쓰기 전에는 사용자 확인이 필요하다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- multi-view/mesh/contact packet은 review evidence이며 model input이 아니다.
- hidden manifest, numeric witness values, previous proxy labels, source score/rank,
  `p_geom_valid`는 fill input으로 사용하지 않는다.
- visible review sheet identity fields와 packet availability만 사용했다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_true_user_review_rank_band70_filled_codex_proxy_pending_confirmation
rows=70
reliable=35
unreliable=35
uncertain=0
errors=0
validation_used=False
test_used=False
next=true_user_review_rank_band70_label_ingestion
```

## Filled Label Summary

| Item | Count |
| --- | ---: |
| rows | 70 |
| reliable | 35 |
| unreliable | 35 |
| uncertain | 0 |
| validation errors | 0 |

Family counts:

| Family | Rows |
| --- | ---: |
| `relative_vertical` | 30 |
| `support_contact` | 40 |

Packet status:

| Packet Status | Rows |
| --- | ---: |
| `ready` | 67 |
| `ready_with_packet_caveat` | 3 |

Visual geometry answer:

| Answer | Rows |
| --- | ---: |
| `supports_predicate` | 69 |
| `contradicts_predicate` | 1 |

## Interpretation

이 fill은 review sheet plumbing을 열기 위한 controlled proxy다.
balanced 35/35 target은 다음 ingestion과 target-independence audit을 실행하기에
형식적으로 충분하지만, 아직 다음 두 claim은 막혀 있다.

- Codex proxy label이 실제 true user/external label이라는 claim.
- 이 target으로 posterior novelty 또는 paper-level 성능을 검증했다는 claim.

따라서 다음 단계의 목적은 성능 주장이 아니라, `rank_band70` filled label을 ingest하고
이 target도 shortcut/hidden-prior 문제를 갖는지 다시 audit하는 것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/107_full_train_independent_support_vertical_v2_true_user_review_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/completed_true_user_review_sheet_rank_band70_codex_proxy_pending_confirmation.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/true_user_proxy_labels_rank_band70.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/fill_validation_errors.jsonl
```

## Verification

Line counts:

```text
completed_true_user_review_sheet_rank_band70_codex_proxy_pending_confirmation.tsv = 70 rows + header
true_user_proxy_labels_rank_band70.jsonl = 70
fill_validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
108_full_train_independent_support_vertical_v2_true_user_review_ingestion.md
```

Previous next action:

```text
true_user_review_rank_band70_label_ingestion
```

Goal:

- ingest the 70-row Codex-proxy pending-confirmation review labels.
- preserve `actual_true_user_reviewer=False` and `user_confirmation_pending=True`.
- derive relation reliability target from filled review fields.
- run a target-independence probe after ingestion.
- keep posterior smoke blocked unless the ingested target has a strict or defensible controlled slice.

New next action:

```text
true_user_review_rank_band70_target_independence_audit
```
