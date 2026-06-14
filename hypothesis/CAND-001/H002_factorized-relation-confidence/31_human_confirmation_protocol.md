# H002 Human Confirmation Protocol

Last updated: 2026-06-13

## Purpose

`30_redesigned_target_smoke.md`는 target v2가 이전 target보다 덜 shortcut-prone하지만,
machine-assisted working labels만으로 posterior evidence를 주장할 수 없다는 결론을
냈다.

이 문서는 target v2를 human-confirmed label로 바꾸기 위한 confirmation protocol을
고정한다.

Core rule:

```text
No posterior claim before human-confirmed target labels.
```

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/working_labels.jsonl
```

Input queues:

| Queue | Rows | Role |
| --- | ---: | --- |
| `strict_proximity_informativeness` | 27 | primary confirmation queue |
| `weak_satisfied_actionability` | 87 | extension queue after strict passes |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/human_confirmation_protocol.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/human_confirmation_protocol.py
```

Status:

```text
ready_protocol_no_human_labels
```

Boundary:

```text
split = train_only
validation usage = false
paper result = false
human labels filled = false
posterior claim allowed = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/report.md
```

Asset coverage:

| Queue | Rows | Contact sheets | Mesh links |
| --- | ---: | ---: | ---: |
| strict primary | 27 | 27 | 27 |
| weak extension | 87 | 87 | 87 |

Missing manual/asset joins:

```text
0
```

## Review Fields

Required review fields:

| Field | Values |
| --- | --- |
| `reviewer_id` | free text |
| `review_round` | integer |
| `object_pair_valid` | yes / no / uncertain |
| `predicate_visually_plausible` | yes / no / uncertain |
| `geometry_witness_correct` | yes / no / uncertain |
| `relation_informative` | yes / no / uncertain |
| `relation_trivial_or_dense` | yes / no / uncertain |
| `annotation_missing_or_sparse` | yes / no / uncertain |
| `ontology_or_granularity_issue` | yes / no / uncertain |
| `segmentation_or_instance_issue` | yes / no / uncertain |
| `final_human_label` | controlled label below |
| `confidence` | high / medium / low |
| `notes` | free text |

## Final Human Labels

| Final label | Posterior target | Meaning |
| --- | --- | --- |
| `reliable_promote` | 1 | valid object pair, plausible predicate, correct geometry witness, informative relation |
| `unreliable_dense_noise` | 0 | geometry-supported but too trivial/dense/unhelpful to promote |
| `relabel_only` | exclude | useful only after predicate canonicalization |
| `abstain_uncertain` | exclude | visual/mesh evidence insufficient or ambiguous |
| `invalid_pair` | exclude | invalid object pair or segmentation/instance issue |
| `geometry_artifact` | exclude | geometry witness is wrong or unreliable |

Mapping rule:

```text
positive posterior target = reliable_promote
negative posterior target = unreliable_dense_noise
all other final labels = excluded from binary posterior target
```

## Review Order

Primary order:

1. Review all 27 `strict_proximity_informativeness` rows.
2. Check whether enough binary labels remain after exclusions.
3. Only if strict queue passes, extend to `weak_satisfied_actionability`.

Reason:

- strict queue controls `geometry_status=satisfied`.
- strict queue controls `predicate_family=proximity`.
- strict queue is the least-confounded current target.
- weak queue is larger but still family-confounded.

## Acceptance Criteria

### Hypothesis-Stage Minimum

This permits only train-only posterior plumbing smoke.

| Criterion | Required |
| --- | --- |
| reviewers | 1 |
| strict rows completed | 27 |
| required fields complete | yes |
| usable binary rows after exclusion | at least 20 |
| per-class minimum after exclusion | at least 8 |
| allowed use | train-only posterior plumbing smoke |

### Paper-Evidence Minimum

This still does not create held-out evidence. It only upgrades label quality.

| Criterion | Required |
| --- | --- |
| reviewers | 2 |
| strict rows completed | 27 |
| agreement | `>= 0.75` exact final-label agreement or all conflicts adjudicated |
| usable binary rows after exclusion | at least 20 |
| per-class minimum after exclusion | at least 8 |
| required action | adjudicate disagreement before any posterior claim |

Important:

```text
Even after paper-evidence minimum, validation/test evidence is still absent.
```

## Current Boundary

Established:

- human confirmation fields are fixed.
- final human label ontology is fixed.
- strict primary review queue exists.
- weak extension review queue exists.
- all review rows have contact sheets and mesh links.
- no human label has been filled yet.
- no validation rows were used.

Not established:

- human-confirmed labels.
- reviewer agreement.
- posterior-training-ready target.
- posterior advantage.
- paper-level result.

## Next TODO

Next document:

```text
32_human_label_readiness.md
```

Required next work:

- check whether `strict_review_sheet.tsv` has human-filled labels.
- validate required fields and allowed values.
- compute usable binary target counts after exclusion.
- compute reviewer agreement if two reviewers exist.
- decide whether posterior fitting can resume as train-only plumbing smoke.
