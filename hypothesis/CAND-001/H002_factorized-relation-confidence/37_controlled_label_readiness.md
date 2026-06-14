# H002 Controlled Label Readiness

Last updated: 2026-06-13

## Purpose

`36_controlled_label_target.md`에서 만든 controlled review target이 current
factorized posterior smoke에 사용할 수 있는지 검증한다.

검증 대상은 다음 posterior다.

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

`V_mv_e`는 아직 model input으로 추가하지 않는다. Multi-view는 현재 단계에서
audit/confirmation evidence로만 둔다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_label_readiness.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_label_readiness.py
```

Result:

```text
status=not_ready_no_filled_labels mined_completed=0/96 combined_completed=0/123 mined_binary=0 combined_binary=0 validation_used=False
```

## Input Sheets

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet.tsv
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/mined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/combined_binary_targets.jsonl
```

## Required Review Fields

The validator requires these fields before a row can be counted as completed:

```text
reviewer_id
review_round
object_pair_valid
predicate_visually_plausible
geometry_witness_correct
relation_informative
relation_trivial_or_dense
final_controlled_label
confidence
```

Allowed yes/no/uncertain fields:

```text
object_pair_valid
predicate_visually_plausible
geometry_witness_correct
relation_informative
relation_trivial_or_dense
annotation_missing_or_sparse
ontology_or_granularity_issue
segmentation_or_instance_issue
```

Allowed final labels:

| Final label | Binary use |
| --- | --- |
| `reliable_promote` | positive |
| `unreliable_dense_noise` | negative |
| `relabel_only` | exclude |
| `invalid_pair` | exclude |
| `geometry_artifact` | exclude |
| `abstain_uncertain` | exclude |

## Readiness Result

| Sheet | Status | Rows | Started | Completed | Binary rows | Per-class min | Missing required | Invalid values |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `mined_controlled` | `not_ready_no_filled_labels` | 96 | 0 | 0 | 0 | 0 | 96 | 0 |
| `combined_review` | `not_ready_no_filled_labels` | 123 | 0 | 0 | 0 | 0 | 123 | 0 |

The generated binary target files are currently empty:

```text
mined_binary_targets.jsonl = 0 rows
combined_binary_targets.jsonl = 0 rows
```

## Decision

The controlled target is structurally ready but not label-ready.

Established:

- `mined_controlled_sheet.tsv` has 96 controlled candidate rows.
- `combined_review_sheet.tsv` has 123 rows after adding the existing strict seed.
- Required review fields and allowed values are now machine-checkable.
- No validation/test rows were used.

Not established:

- human-confirmed or independent controlled labels.
- usable binary target rows.
- per-class minimum.
- factorized posterior advantage.
- paper-level evidence.

Therefore current posterior fitting remains blocked.

## Boundary

This step is only a train-set readiness check.

```text
split = train_only
validation usage = false
test usage = false
paper result = false
posterior claim allowed = false
V_mv_e model input allowed = false
```

Important:

```text
proposed_review_stratum != final label
```

The sampling priors in `36_controlled_label_target.md` must not be used as
training labels.

## Next TODO

Next required gate:

```text
fill_controlled_review_labels
```

Practical next document after labels exist:

```text
38_controlled_posterior_smoke.md
```

Required before `38_controlled_posterior_smoke.md`:

- fill `mined_controlled_sheet.tsv` or `combined_review_sheet.tsv` with
  human/independent labels.
- rerun `controlled_label_readiness.py`.
- require usable binary rows `>= 60`.
- require per-class rows `>= 20`.
- use only train-set rows.
- keep `V_mv_e` out of model input.
