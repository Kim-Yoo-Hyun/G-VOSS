# H002 Full Train Label Readiness

Last updated: 2026-06-16

## Purpose

`60_full_train_controlled_mining.md`에서 만든 full-train controlled candidate
sheet가 posterior target으로 사용할 준비가 되었는지 검증한다.

이 단계의 목적:

- blank review fields가 target으로 변환되지 않는지 확인한다.
- `proposed_audit_role`이 final label로 사용되지 않는지 확인한다.
- filled label이 들어왔을 때의 minimum readiness gate를 고정한다.
- validation/test row를 계속 사용하지 않는다.

## Decision

Current status:

```text
not_ready_no_filled_labels
```

Meaning:

```text
The full-train candidate sheet is structurally valid, but no controlled labels
are filled yet. Therefore posterior fitting remains blocked.
```

This is the expected result for the current blank sheet.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py
```

Input:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_pool.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/summary.json
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py
```

Result:

```text
status=not_ready_no_filled_labels rows=360 started=0 completed=0 binary=0 validation_used=False
```

## Output Artifacts

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness/
```

Files:

| Artifact | Rows / Status |
| --- | ---: |
| `summary.json` | written |
| `report.md` | written |
| `binary_targets.jsonl` | 0 rows |
| `multiclass_review_rows.jsonl` | 0 rows |
| `invalid_rows.jsonl` | 0 rows |

## Readiness Result

Sheet status:

| Item | Count |
| --- | ---: |
| rows | 360 |
| started rows | 0 |
| completed rows | 0 |
| blank rows | 360 |
| usable binary rows | 0 |
| invalid values | 0 |
| incomplete started rows | 0 |

Candidate consistency:

| Check | Result |
| --- | --- |
| sheet rows | 360 |
| candidate pool rows | 360 |
| mining summary rows | 360 |
| row counts match | true |

Schema checks:

| Check | Result |
| --- | --- |
| schema valid | true |
| no invalid values | true |
| no incomplete started rows | true |

Target checks:

| Gate | Result |
| --- | --- |
| usable binary rows >= 150 | false |
| positive rows >= 50 | false |
| negative rows >= 50 | false |
| binary rows per queue >= 50 | false |
| families with both classes >= 2 | false |
| per-family minority >= 15 in at least 2 families | false |

## Fixed Readiness Gate

Full-train controlled labels can be used for train-only posterior smoke only if:

```text
schema_valid = true
invalid_value_count = 0
incomplete_started_rows = 0
usable_binary_rows >= 150
positive_rows >= 50
negative_rows >= 50
binary_rows_per_queue >= 50
families_with_both_binary_classes >= 2
at least 2 families have minority-class count >= 15
```

Allowed binary mapping:

| Final controlled label | Posterior target |
| --- | ---: |
| `reliable_promote` | 1 |
| `unreliable_dense_noise` | 0 |
| `relabel_only` | exclude |
| `invalid_pair` | exclude |
| `geometry_artifact` | exclude |
| `abstain_uncertain` | exclude |

Required review fields:

```text
reviewer_id
review_round
object_pair_valid
predicate_visually_plausible
geometry_witness_correct
relation_informative
relation_trivial_or_dense
final_controlled_label
failure_taxonomy_label
confidence
```

## Boundary

Established:

- full-train candidate sheet schema is valid.
- candidate pool and sheet row counts match.
- blank review fields are not converted into binary targets.
- generated target files are empty.
- validation/test rows are unused.

Not established:

- human-confirmed labels.
- independent blind labels.
- usable binary target rows.
- posterior revival evidence.
- paper-level result.

Important:

```text
proposed_audit_role != final_controlled_label
```

## Interpretation

This gate prevents the previous target-construction shortcut from reappearing at
full-train scale. The 360 candidates are enough for audit, but they are not yet
supervision. The next scientific step is label fill/confirmation, not posterior
training.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py
```

Observed:

```text
status=not_ready_no_filled_labels
binary_targets.jsonl = 0 rows
multiclass_review_rows.jsonl = 0 rows
invalid_rows.jsonl = 0 rows
```

## Next TODO

Completed next action:

```text
fill_full_train_controlled_labels
```

Result:

```text
62_full_train_label_fill.md
```

Original goal:

- fill or independently confirm full-train controlled labels.
- keep `proposed_audit_role` hidden from any human/independent label decision if
  possible.
- produce at least 150 usable binary labels with balanced positive/negative,
  queue, and family coverage.
- keep validation/test unavailable.
