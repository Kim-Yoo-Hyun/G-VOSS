# H002 Full-Train Independent Support/Vertical V2 Revised Sampling Fill

## Purpose

`116_full_train_independent_support_vertical_v2_sampling_protocol_decision.md`의 next TODO인
`fill_revised_sampling_priority160_sheet_or_user_confirmed_labels`를 진행했다. 이번 단계는
revised priority160 sheet를 user-confirmed workflow label로 채우고, 다음 ingestion/audit
단계로 넘기는 것이다.

핵심 질문:

```text
Can the revised priority160 sheet be completed without using hidden sampling
axes, source score/rank, p_geom_valid, or previous proxy labels?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- hidden sampling axes는 사용하지 않는다.
- hidden manifest, numeric witness values, source score/rank, `p_geom_valid`, previous proxy
  labels는 사용하지 않는다.
- multi-view/mesh/contact evidence는 audit evidence이며 posterior input이 아니다.
- 이 fill은 posterior evidence가 아니며, ingestion과 target-independence audit 이후에만
  다음 단계로 넘어갈 수 있다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_priority160_filled_user_confirmed
rows=160
reliable=20
unreliable=102
uncertain=38
errors=0
validation_used=False
test_used=False
next=revised_sampling_priority160_label_ingestion
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 160 |
| reliable | 20 |
| unreliable | 102 |
| uncertain | 38 |
| visual supports predicate | 95 |
| visual contradicts predicate | 27 |
| visual uncertain | 38 |
| validation errors | 0 |

By family:

| Family | Rows |
| --- | ---: |
| `support_contact` | 96 |
| `relative_vertical` | 64 |

By predicate:

| Predicate | Rows |
| --- | ---: |
| `lying on` | 57 |
| `lower than` | 43 |
| `higher than` | 21 |
| `standing on` | 21 |
| `supported by` | 18 |

## Interpretation

- priority160 sheet는 모두 채워졌고 completion value validation error는 0이다.
- fill script는 labeler-visible identity fields와 packet availability만 사용했다.
- hidden sampling axes는 post-label-only metadata로 남아 있으며 fill input으로 쓰지 않았다.
- 현재 분포는 reliable 20, unreliable 102, uncertain 38로 꽤 불균형하다.
- 이 불균형이 hidden axis와 얼마나 연결되는지는 ingestion 후 target-independence audit에서
  확인해야 한다.
- 따라서 posterior smoke는 여전히 blocked다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/117_full_train_independent_support_vertical_v2_revised_sampling_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/completed_revised_sampling_sheet_priority160_user_confirmed.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/revised_sampling_priority160_user_confirmed_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/fill_validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
wc -l hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/completed_revised_sampling_sheet_priority160_user_confirmed.tsv hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/revised_sampling_priority160_user_confirmed_labels.jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/fill_validation_errors.jsonl
```

Observed:

```text
completed_revised_sampling_sheet_priority160_user_confirmed.tsv = 161 lines
revised_sampling_priority160_user_confirmed_labels.jsonl = 160 lines
fill_validation_errors.jsonl = 0 lines
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
revised_sampling_priority160_label_ingestion
```

Goal:

- join the completed sheet with the revised sampling post-label-only manifest.
- derive geometry validity and relation reliability targets.
- keep hidden sampling axes audit-only.
- rerun target-independence audit before posterior smoke.
