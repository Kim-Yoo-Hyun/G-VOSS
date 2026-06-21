# H002 Full-Train Independent Support/Vertical V2 Sampling Protocol Decision

## Purpose

`115_full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.md`의
next TODO인 `expand_user_confirmed_labels_or_revise_sampling_protocol`을 진행했다.
이번 단계는 단순 full-127 확장과 sampling protocol 재설계 중 어떤 경로가 현재 H002
blocker를 원리적으로 더 잘 해결하는지 결정하고, revised sampling label surface를 생성한다.

핵심 질문:

```text
Should H002 expand the same label protocol to full-127, or revise sampling first
to reduce hidden prior/role carryover before posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- multi-view/mesh/contact evidence는 label/audit evidence이며 posterior input이 아니다.
- hidden sampling axes는 post-label-only audit metadata이며 labeler-visible field에 넣지 않는다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_sampling_protocol_decision_revise_sampling_first
decision=revise_sampling_first
all_candidates=315
joined=302
priority=160
missing=13
header_leakage=0
validation_used=False
test_used=False
next=fill_revised_sampling_priority160_sheet_or_user_confirmed_labels
```

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_on_user_confirmed_rank70` | `reject` | 70-row user-confirmed target에 strict/construction relation slice가 없다. |
| `expand_full127_same_protocol_then_posterior` | `reject_as_direct_posterior_path` | 이전 full-127 proxy audit도 strict relation slice를 만들지 못했다. |
| `expand_full127_same_protocol_for_diagnostics` | `diagnostic_only` | sample size를 키울 수는 있지만 hidden prior carryover를 직접 해결하지 않는다. |
| `revise_sampling_protocol_before_next_labels` | `select` | 현재 blocker는 posterior capacity가 아니라 target/evidence independence이므로 hidden queue/role/rank/family axis를 먼저 통제해야 한다. |

## Evidence Used

| Artifact | Relation Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | ---: | ---: | ---: | --- | --- |
| user-confirmed rank-band 70 | 68 | 35 | 33 | `none` | `none` |
| previous full-127 external proxy | 116 | 47 | 69 | `none` | `rank_band_balanced_external` |

해석:

- 70-row는 provenance가 해결됐지만 target-independence가 해결되지 않았다.
- full-127 proxy는 sample size를 키웠지만 strict slice가 없었다.
- 따라서 같은 protocol로 127개를 다시 채우는 것은 diagnostic으로는 가능하지만 posterior
  method-validation path로는 약하다.
- 다음 label surface는 hidden sampling axis를 더 균형 있게 만들고, 그 axis를 labeler에게
  노출하지 않는 방식이어야 한다.

## Revised Sampling Surface

Input pool:

| Item | Count |
| --- | ---: |
| support/vertical candidate pool rows | 315 |
| packet-joined label-ready rows | 302 |
| missing/unready packet or request rows | 13 |
| header leakage hits | 0 |

Priority batch:

| Axis | Counts |
| --- | --- |
| `queue_kind` | `HL:80`, `LH:80` |
| `geometry_status` | `unsatisfied:80`, `satisfied:80` |
| `predicate_family` | `support_contact:96`, `relative_vertical:64` |
| `label_match_status` | `exact_match:25`, `family_match:33`, `no_gt_for_pair:50`, `pair_has_other_predicate:52` |

The revised priority batch is intentionally not the previous 70-row rank-band slice.
It is a broader support/vertical batch that balances over hidden queue and geometry-status
axes while keeping role/rank/family metadata hidden until after label lock.

## Generated Label Packets

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_sheet_priority160.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_manifest_priority160_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_sheet_all_label_ready.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_manifest_all_label_ready_post_label_only.jsonl
```

Line counts:

```text
revised_sampling_sheet_priority160.tsv = 161 lines
revised_sampling_manifest_priority160_post_label_only.jsonl = 160 lines
revised_sampling_sheet_all_label_ready.tsv = 303 lines
revised_sampling_manifest_all_label_ready_post_label_only.jsonl = 302 lines
missing_or_unready_rows.jsonl = 13 lines
header_leakage_hits.jsonl = 0 lines
```

## Labeler-Visible / Hidden Contract

Labeler-visible:

- relation identity
- family question
- packet paths
- external review completion fields

Post-label-only hidden metadata:

- `queue_kind`
- `geometry_status`
- `proposed_audit_role`
- `label_match_status`
- `rank_band`
- semantic rank/score
- `p_geom_valid`

These hidden fields are only for target-independence audit and cannot be posterior input.

## Decision

선택:

```text
revise_sampling_protocol_before_next_labels
```

Current posterior status:

```text
blocked
```

Reason:

- H002의 현재 실패 원인은 label 수만 부족한 것이 아니라 hidden prior/role carryover다.
- full-127 same-protocol expansion은 construction-only diagnostic은 만들 수 있지만 strict
  method-validation target을 보장하지 않는다.
- revised priority160 sheet는 HL/LH와 satisfied/unsatisfied를 80/80으로 맞춰, 기존 70-row가
  거의 LH/satisfied에 치우친 문제를 직접 줄인다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/116_full_train_independent_support_vertical_v2_sampling_protocol_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/reviewer_instructions.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_review_schema.json
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
```

Observed:

```text
all_candidates=315
joined=302
priority=160
missing=13
header_leakage=0
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
fill_revised_sampling_priority160_sheet_or_user_confirmed_labels
```

Goal:

- fill or user-confirm the revised `priority160` sheet.
- keep hidden sampling metadata post-label-only.
- ingest labels after label lock.
- rerun target-independence audit before any posterior smoke.
- keep posterior smoke blocked until strict or defensible controlled relation-reliability target evidence exists.
