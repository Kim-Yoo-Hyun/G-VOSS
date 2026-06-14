# H002 Controlled Label Target

Last updated: 2026-06-13

## Purpose

`35_factorized_validation_plan.md`에서 정한 최소 조건에 맞게, 현재 strict target
`27` rows를 확장할 수 있는 controlled review target을 만든다.

Core requirement:

```text
same-family
same-geometry-status
same-rank-band
same-source
no visual input
```

Current posterior remains:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

`V_mv_e` is still deferred.

## Design Decision

Primary target family:

```text
predicate_family = proximity
predicate_label = close by
geometry_status = satisfied
semantic_rank > 100
```

Why:

- It preserves the current strict target's core question:

```text
geometry validity != relation reliability
```

- It avoids the old `satisfied vs unsatisfied` shortcut.
- It keeps one predicate family and one predicate label.
- It allows rank-band stratification.
- It targets the key distinction:

```text
reliable/informative proximity
vs
dense/trivial proximity
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_label_target.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_label_target.py
```

Status:

```text
ready_controlled_review_queue_no_labels
```

Boundary:

```text
split = train_only
validation usage = false
test usage = false
final labels created = false
paper result = false
V_mv_e model input allowed = false
posterior claim allowed = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/existing_strict_seed_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/contact_sheets/
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/report.md
```

## Selection Policy

The mined queue uses sampling priors, not labels.

Candidate reliable seed:

```text
label_match_status in {exact_match, pair_has_other_predicate}
non-structural subject/object endpoints
subject label != object label
```

Candidate dense-noise seed:

```text
label_match_status = no_gt_for_pair
structural endpoint OR generic endpoint OR same endpoint label
```

Important:

```text
proposed_review_stratum is not a final label.
```

Human/independent review must still fill `final_controlled_label`.

## Candidate Counts

Mined controlled queue:

| Item | Count |
| --- | ---: |
| rows | 96 |
| `candidate_reliable_promote_seed` | 48 |
| `candidate_unreliable_dense_noise_seed` | 48 |
| contact sheets | 96 |
| mesh links | 96 |
| family | `proximity` only |
| predicate | `close by` only |
| geometry status | `satisfied` only |

Existing strict seed:

| Item | Count |
| --- | ---: |
| rows | 27 |
| `existing_strict_reliable_seed` | 16 |
| `existing_strict_dense_seed` | 11 |
| contact sheets | 27 |
| mesh links | 27 |

Combined review queue:

| Item | Count |
| --- | ---: |
| rows | 123 |
| contact sheets | 123 |
| mesh links | 123 |

## Rank-Band Control

The mined controlled queue is balanced by rank band and proposed stratum.

| Rank band | Reliable seed | Dense seed |
| --- | ---: | ---: |
| `rank_201_500` | 16 | 16 |
| `rank_501_1000` | 16 | 16 |
| `rank_gt1000` | 16 | 16 |

This is the primary queue for the next human/independent label pass.

## Target Minimum Check

The structural target minimum from `35_factorized_validation_plan.md` was:

```text
usable rows >= 60
per-class rows >= 20
```

The mined candidate queue provides:

```text
rows = 96
candidate class minimum = 48
```

Therefore it is structurally enough for a review pass. It is not yet enough for
training because final labels are still empty.

## Review Fields

The generated sheets contain blank review fields:

| Field | Values |
| --- | --- |
| `object_pair_valid` | yes / no / uncertain |
| `predicate_visually_plausible` | yes / no / uncertain |
| `geometry_witness_correct` | yes / no / uncertain |
| `relation_informative` | yes / no / uncertain |
| `relation_trivial_or_dense` | yes / no / uncertain |
| `annotation_missing_or_sparse` | yes / no / uncertain |
| `ontology_or_granularity_issue` | yes / no / uncertain |
| `segmentation_or_instance_issue` | yes / no / uncertain |
| `final_controlled_label` | controlled label below |
| `confidence` | high / medium / low |

Allowed final labels:

| Final label | Use |
| --- | --- |
| `reliable_promote` | binary positive |
| `unreliable_dense_noise` | binary negative |
| `relabel_only` | exclude from binary target |
| `invalid_pair` | exclude |
| `geometry_artifact` | exclude |
| `abstain_uncertain` | exclude |

## Why Not Support Contact Yet

`support_contact` remains promising, but it lacks balanced negative candidates in
the current audited pool.

Current state:

```text
support_contact extension rows = 26
working labels = true_underconfidence 21, annotation_sparsity 5
```

Therefore support-contact should remain a separate future stratum. It should not
be pooled into the primary factorized validation target yet.

## Current Decision

Established:

- controlled mined queue exists.
- primary target keeps same family, same predicate, same geometry status.
- rank bands are balanced.
- all mined rows have contact sheets and mesh links.
- proposed strata are sampling priors only.
- no final labels were created.
- no validation/test rows were used.
- `V_mv_e` was not added as model input.

Not established:

- human-confirmed controlled labels.
- usable binary rows after exclusion.
- factorized posterior advantage.
- paper-level evidence.

## Next TODO

Next document:

```text
37_controlled_label_readiness.md
```

Required next work:

- check whether `mined_controlled_sheet.tsv` or `combined_review_sheet.tsv` has
  filled human/independent labels.
- validate allowed values and required fields.
- compute usable binary rows after exclusions.
- verify per-class minimum.
- only then decide whether current `S_e + G_e + C_e + U_e` posterior fitting can
  resume.
