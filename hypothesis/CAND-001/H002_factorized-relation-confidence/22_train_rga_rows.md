# H002 Train RGA Rows

Last updated: 2026-06-12

## Purpose

이 단계는 Open3DSG train pilot에서 H002의 `RGA(Relation-Geometric Agreement)`
row contract를 실제 artifact로 고정한다. 이전 gate까지 확보한 semantic prediction
row와 geometry verification row에 train GT relation을 직접 join해서 다음 상태를
계산한다.

- semantic high/low axis
- geometry satisfied/unsatisfied/uncertain/unsupported axis
- exact predicate match / family match / same-pair other predicate / no-GT pair
- `RGA-HL@K`, `RGA-LH-tail@K`
- train HL/LH audit queue

중요 boundary:

```text
This is train-pilot hypothesis evidence only.
It is not held-out validation/test evidence and not a paper-level result.
```

## Input Artifacts

Predictions:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
```

Geometry:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/verification.jsonl
```

Train GT subset:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
```

Counts:

| Input | Rows / Contexts |
| --- | ---: |
| prediction rows | 118,560 |
| geometry rows | 118,560 |
| GT relation rows | 2,723 |
| prediction contexts | 100 |
| GT contexts | 100 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_rows.py
```

The tool writes:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_rga_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_hl_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_lh_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/report.md
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_rows.py
```

Status:

```text
status: ready
validation_error_count: 0
```

## Row Contract Decisions

H002 status mapping:

| H001 status | H002 geometry status |
| --- | --- |
| `satisfied` | `satisfied` |
| `violated` | `unsatisfied` |
| `uncertain` | `uncertain` |
| `unsupported` | `unsupported` |

`p_geom_valid` handling:

```text
p_geom_valid is geometry-only continuous evidence.
It is not posterior_edge_valid.
```

따라서 deterministic `RGA-HL/RGA-LH` bucket은 `p_geom_valid` threshold가 아니라
frozen geometry status로 정한다. `p_geom_valid`는 continuous
`disagreement_score`와 `underconfidence_score` 계산에만 사용한다.

Semantic normalization:

```text
semantic_score_norm = 1 - (rank_in_context - 1) / (context_prediction_count - 1)
normalization_rule = rank_in_context_linear_v0
```

Label matching:

| Status | Meaning |
| --- | --- |
| `exact_match` | same subject/object/predicate in train GT |
| `family_match` | same subject/object and same predicate family, different predicate label |
| `pair_has_other_predicate` | same subject/object has GT relation but different family |
| `no_gt_for_pair` | no GT relation for the directed pair |

## Output Counts

Line counts:

| Artifact | Rows |
| --- | ---: |
| `match_rows.jsonl` | 118,560 |
| `train_hl_queue.jsonl` | 47 |
| `train_lh_queue.jsonl` | 11,588 |

Validation:

| Check | Value |
| --- | ---: |
| rows written | 118,560 |
| prediction-geometry mismatches | 0 |
| missing identity rows | 0 |
| `posterior_edge_valid` non-null rows | 0 |
| `violated -> unsatisfied` mapping errors | 0 |
| validation/full_validation provenance matches | 0 |

Geometry status:

| H002 status | Rows |
| --- | ---: |
| `satisfied` | 12,285 |
| `uncertain` | 11,841 |
| `unsatisfied` | 3,234 |
| `unsupported` | 91,200 |

Family geometry status:

| Family | Satisfied | Uncertain | Unsatisfied | Unsupported |
| --- | ---: | ---: | ---: | ---: |
| `proximity` | 4,312 | 128 | 120 | 0 |
| `relative_vertical` | 2,764 | 3,592 | 2,764 | 0 |
| `support_contact` | 5,209 | 8,121 | 350 | 0 |
| `attachment_deferred` | 0 | 0 | 0 | 13,680 |
| `relative_horizontal` | 0 | 0 | 0 | 18,240 |
| `unsupported_first_pass` | 0 | 0 | 0 | 59,280 |

Label status:

| Label status | Rows |
| --- | ---: |
| `exact_match` | 1,980 |
| `family_match` | 3,962 |
| `pair_has_other_predicate` | 27,546 |
| `no_gt_for_pair` | 85,072 |

Label-geometry buckets:

| Bucket | Rows |
| --- | ---: |
| `RGA-TP-GS` | 653 |
| `RGA-TP-GU` | 2 |
| `RGA-TP-GC` | 1,325 |
| `RGA-FP-GS` | 11,632 |
| `RGA-FP-GU` | 3,232 |
| `RGA-FP-GC` | 101,716 |

## RGA Metrics

Primary high-semantic metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 2.35% | 3.87% |
| `RGA-valid@K` | 63.53% | 57.41% |
| `RGA-nonviolated@K` | 97.65% | 96.13% |
| `RGA-uncertain@K` | 34.12% | 38.71% |
| `RGA-coverage@K` | 3.40% | 12.14% |

Primary low-semantic tail metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-LH-tail@K` | 44.78% | 44.32% |
| `RGA-LL-tail@K` | 11.88% | 12.19% |
| `RGA-LU-tail@K` | 43.34% | 43.49% |

Top100 denominators:

| Group | Total | Covered | Satisfied | Unsatisfied | Uncertain | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| top100 | 10,000 | 1,214 | 697 | 47 | 470 | 8,786 |
| tail > 100 | 108,560 | 26,146 | 11,588 | 3,187 | 11,371 | 82,414 |

## Interpretation

Train pilot에서 high-semantic / low-geometry(`RGA-HL`)는 존재하지만 Top100 기준
47행으로 작다. 반대로 low-semantic / high-geometry(`RGA-LH`)는 11,588행으로 크다.
이는 H002를 단순 overconfidence detector로만 두면 약하고, bidirectional mismatch
benchmark로 보는 방향이 더 타당하다는 초기 신호다.

다만 `RGA-LH`를 바로 missed relation이나 graph promotion 후보로 해석하면 안 된다.
LH는 다음 경우가 섞여 있을 수 있다.

- 실제 semantic underconfidence
- GT annotation sparsity
- predicate ontology/granularity mismatch
- dense relation such as `close by`
- source false positive or object-pair mismatch
- geometry witness artifact

따라서 다음 gate는 LH/HL queue audit이다. 특히 LH에서 `exact_match`,
`family_match`, `pair_has_other_predicate`, `no_gt_for_pair`를 분리해 봐야 H002가
relation reliability를 실제로 설명하는지 판단할 수 있다.

## Current Boundary

Established:

- train-only Open3DSG pilot RGA rows are materialized.
- prediction and geometry rows are row-preserved.
- direct train GT match status is available for all prediction rows.
- deterministic geometry status and continuous `p_geom_valid` are separated.
- `posterior_edge_valid` remains undefined/null.

Not established:

- RGA-LH rows are meaningful promotion candidates.
- `RGA-HL`/`RGA-LH` generalize beyond this train pilot.
- factorized reliability posterior improves over semantic-only, geometry-only,
  or semantic+geometry baselines.
- paper-level held-out metrics.

## Next TODO

Next document:

```text
23_train_rga_audit.md
```

Required next work:

- stratify `train_hl_queue.jsonl` and `train_lh_queue.jsonl` by family, rank band,
  label status, and reason code.
- create a compact manual/visual audit seed rather than inspecting all 11,588 LH
  rows.
- decide whether LH is mostly source-underconfidence/annotation-coverage signal
  or mostly dense/geometry-trivial noise.
- if the audit is meaningful, define the first factorized reliability baseline
  contract using train rows only.
