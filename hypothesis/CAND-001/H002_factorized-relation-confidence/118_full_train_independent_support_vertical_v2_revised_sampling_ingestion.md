# H002 Full-Train Independent Support/Vertical V2 Revised Sampling Ingestion

## Purpose

`117_full_train_independent_support_vertical_v2_revised_sampling_fill.md`에서 채운
priority160 user-confirmed workflow labels를 post-label-only manifest와 결합하고,
geometry-validity target 및 relation-reliability target을 생성했다.

핵심 질문:

```text
Does the revised priority160 sampling sheet produce a label-locked target
artifact that can proceed to target-independence audit?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- completed priority160 labels는 user-confirmed workflow labels로 취급한다.
- hidden sampling axes는 label lock 이후 audit-only metadata로만 join한다.
- review fields와 hidden sampling axes는 posterior input이 아니다.
- multi-view/mesh packet path는 audit evidence이며 deployable posterior input이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_ingested_with_basic_probe_risk
labels=160
geom_binary=122 geom_pos=95 geom_neg=27
rel_binary=122 rel_pos=20 rel_neg=102
errors=0
user_confirmed=True
validation_used=False test_used=False
next=revised_sampling_priority160_target_independence_audit
```

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_revised_sampling_user_confirmed_target` | 122 | 95 | 27 | 0.7787 | 38 |
| `relation_reliability_revised_sampling_user_confirmed_target` | 122 | 20 | 102 | 0.1639 | 38 |

By family for relation reliability:

| Family | Positive | Negative |
| --- | ---: | ---: |
| `relative_vertical` | 11 | 24 |
| `support_contact` | 9 | 78 |

## Basic Probe

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_revised_sampling_user_confirmed_target` | `target_independence_risk_hidden_metadata_correlated` | 2 | 2 |
| `relation_reliability_revised_sampling_user_confirmed_target` | `target_independence_risk_hidden_metadata_correlated` | 4 | 1 |

## Interpretation

- revised priority160 artifact는 정상적으로 materialize되었다.
- ingestion validation error는 0이다.
- 하지만 relation reliability target이 20/102로 심하게 negative-heavy다.
- geometry target도 95/27로 positive-heavy라 class balance가 좋지 않다.
- basic probe가 hidden construction axis 및 visible predicate shortcut risk를 잡았다.
- 따라서 posterior smoke로 바로 가지 않고 dedicated target-independence audit을 수행해야 한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/118_full_train_independent_support_vertical_v2_revised_sampling_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/validated_revised_sampling_user_confirmed_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/geometry_validity_revised_sampling_user_confirmed_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/relation_reliability_revised_sampling_user_confirmed_posterior_rows.jsonl
```

## Verification

Observed:

```text
validated_revised_sampling_user_confirmed_labels.jsonl = 160
geometry_validity_revised_sampling_user_confirmed_targets.jsonl = 122
relation_reliability_revised_sampling_user_confirmed_targets.jsonl = 122
excluded_revised_sampling_user_confirmed_targets.jsonl = 76
ingestion_errors.jsonl = 0
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
revised_sampling_priority160_target_independence_audit
```

Goal:

- evaluate whether any strict or construction-only controlled slice exists.
- keep posterior smoke blocked until target-independence clears.
