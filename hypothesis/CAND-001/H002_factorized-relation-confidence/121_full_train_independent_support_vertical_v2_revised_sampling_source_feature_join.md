# H002 Full-Train Independent Support/Vertical V2 Revised Sampling Source Feature Join

## Purpose

`120_full_train_independent_support_vertical_v2_all_label_ready_expansion.md`의 next TODO인
`revised_sampling_all_label_ready_source_feature_join`을 진행했다. strict relation slice
`rank_band_balanced_revised_sampling`에 source semantic score/rank, geometry evidence, coverage
fields를 join하고, posterior smoke가 읽을 수 있는 input table을 만들었다.

핵심 질문:

```text
Can the strict relation-reliability slice be converted into a posterior-ready
feature table without leaking review fields, hidden audit metadata, target
labels, packet paths, or multi-view evidence into model inputs?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- active target slice는 `rank_band_balanced_revised_sampling`이다.
- review fields, hidden audit metadata, target labels, packet paths, multi-view evidence는 model input이 아니다.
- predicate label/family categorical shortcut도 model input에서 제외했다.
- 이 단계는 source feature join과 input contract 검증이며 posterior performance evidence가 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_source_feature_join_ready
rows=134
pos=67
neg=67
candidate_matches=134
leakage=0
errors=0
validation_used=False
test_used=False
next=revised_sampling_all_label_ready_controlled_posterior_smoke
```

## Input Views

Main views:

| View | Inputs |
| --- | --- |
| `semantic_only` | semantic score raw/norm, semantic rank features |
| `geometry_only` | `p_geom_valid`, inverse geometry score, consistency score |
| `semantic_plus_geometry` | semantic + geometry |
| `semantic_geometry_coverage` | semantic + geometry + source coverage |
| `factorized_reliability_posterior` | semantic + geometry + coverage + disagreement/residual interactions |

Diagnostic views:

| View | Purpose |
| --- | --- |
| `coverage_only` | checks whether coverage flags alone explain the target |
| `semantic_score_only` | source confidence scalar baseline |
| `rank_only` | rank-only shortcut diagnostic |
| `p_geom_valid_only` | geometry-only scalar diagnostic |
| `residual_reliability_model` | semantic/geometry residual without coverage block |

## Counts

| Item | Count |
| --- | ---: |
| strict slice rows | 134 |
| posterior-ready rows | 134 |
| positive | 67 |
| negative | 67 |
| candidate pool rows | 360 |
| candidate pool matches | 134 |
| feature leakage hits | 0 |
| validation errors | 0 |

By family:

| Family | Rows |
| --- | ---: |
| `relative_vertical` | 35 |
| `support_contact` | 99 |

By predicate:

| Predicate | Rows |
| --- | ---: |
| `higher than` | 16 |
| `lower than` | 19 |
| `lying on` | 30 |
| `standing on` | 37 |
| `supported by` | 32 |

## Input Contract

Allowed model input root:

```text
baseline_inputs
```

Forbidden as model input:

- review fields
- target labels
- hidden audit metadata
- packet paths
- multi-view evidence
- queue/role/rank-band construction axes
- predicate label/family categorical shortcuts

Feature leakage check result:

```text
feature_leakage.jsonl = 0 lines
validation_errors.jsonl = 0 lines
```

## Interpretation

- target/evidence contract는 posterior smoke를 위한 최소 조건을 만족했다.
- strict slice 134 rows는 67/67로 balanced이며 candidate pool source features가 모두 join되었다.
- `baseline_inputs`에는 deployable source features만 있다.
- audit-only review fields와 hidden sampling axes는 posterior-ready row에 넣지 않았다.
- multi-view/mesh packet path도 input feature에서 제외했다.
- 다음 단계에서 controlled posterior smoke를 수행할 수 있지만, 그 결과도 hypothesis-stage train-only
  smoke이며 paper-level claim은 아니다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/121_full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/posterior_ready_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/input_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/feature_ranges.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/feature_leakage.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/validation_errors.jsonl
```

## Verification

Observed:

```text
posterior_ready_rows.jsonl = 134
feature_leakage.jsonl = 0
validation_errors.jsonl = 0
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
revised_sampling_all_label_ready_controlled_posterior_smoke
```

Goal:

- run train-only controlled posterior smoke on `posterior_ready_rows.jsonl`.
- compare `semantic_only`, `geometry_only`, `semantic_plus_geometry`, and
  `factorized_reliability_posterior`.
- treat result as hypothesis-stage diagnostic, not paper-level evidence.
