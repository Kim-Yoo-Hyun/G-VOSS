# H002 Full Train Independent Label Protocol

Last updated: 2026-06-16

## Purpose

`64_full_train_label_policy_audit.md`에서 확인된 blocker는 다음이었다.

```text
full_train_label_policy_entangled
```

현재 `(codex_ver_full_train)` target은 `proposed_audit_role`과
`label_match_status`로 거의 복원된다. 따라서 posterior를 다시 학습하는 대신,
rank/status/role/GT-match 정보를 숨긴 독립 label protocol을 먼저 만든다.

핵심 질문:

```text
Can we construct a full-train labeling surface that does not expose the metadata
that created the previous target?
```

## Decision

Current status:

```text
full_train_independent_label_protocol_ready_needs_asset_packets
```

Meaning:

```text
The blind labeling surface is ready, but actual labeling should wait until
multi-view/mesh/point-cloud evidence packets are generated or linked.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
```

Observed:

```text
status=full_train_independent_label_protocol_ready_needs_asset_packets rows=360 families={'proximity': 45, 'relative_vertical': 114, 'support_contact': 201} leakage=pass validation_used=False
```

## Input

Input candidate pool:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_pool.jsonl
```

Policy audit reference:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/summary.json
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- `V_mv_e` is not model input.
- multi-view/mesh/point-cloud evidence is audit support only.
- `proposed_audit_role`, `label_match_status`, `queue_kind`,
  `geometry_status`, semantic rank, semantic score, `p_geom_valid`, bucket,
  matched-GT fields, and reason codes are hidden from annotators.

Not established:

- completed independent labels.
- human-confirmed target.
- posterior method evidence.
- paper-level performance.

## Blind Sheet Design

Shown fields:

```text
blind_review_id
asset_request_id
scan_id
scene_context_id
subject_id / subject_label
predicate_label / predicate_family
object_id / object_label
family_question
positive_cues / negative_cues
evidence_packet_status
multiview_packet
pointcloud_or_mesh_packet
contact_or_context_sheet
review fields
```

Hidden fields:

```text
prediction_id
review_id
proposed_audit_role
role_reason
label_match_status
queue_kind
candidate_axis
geometry_status
h001_verification_status
semantic_rank
rank_band
semantic_score_raw
semantic_score_norm
p_geom_valid
consistency_score
disagreement_score
underconfidence_score
label_geometry_bucket
bucket_top50
bucket_top100
machine_hint
matched_gt_ids
matched_predicates
reason_codes
```

Hidden fields are stored only in:

```text
internal_key.jsonl
```

## Leakage Audit

Blind sheet field-name leakage audit:

```text
status = pass
```

Forbidden blind-field substrings:

```text
score
rank
p_geom
geometry_status
h001_verification
queue
label_match
proposed
role
candidate_axis
prediction_id
final_controlled
failure_taxonomy
matched_gt
matched_predicate
bucket
machine_hint
reason_code
semantic
consistency
disagreement
underconfidence
```

No forbidden field names are exposed in the blind sheets.

## Candidate Counts

Full blind sheet:

| Family | Rows |
| --- | ---: |
| `support_contact` | 201 |
| `relative_vertical` | 114 |
| `proximity` | 45 |
| total | 360 |

Priority blind sheet:

| Family | Rows |
| --- | ---: |
| `support_contact` | 90 |
| `relative_vertical` | 60 |
| `proximity` | 30 |
| total | 180 |

Predicates:

| Predicate | Rows |
| --- | ---: |
| `lying on` | 81 |
| `supported by` | 64 |
| `standing on` | 56 |
| `lower than` | 67 |
| `higher than` | 47 |
| `close by` | 45 |

Hidden metadata distribution is still recorded for post-label audit:

| Hidden Key | Distribution |
| --- | --- |
| `queue_kind` | `HL=83`, `LH=277` |
| `geometry_status` | `unsatisfied=83`, `satisfied=277` |
| `label_match_status` | `exact=75`, `family=68`, `pair_other=106`, `no_gt=111` |

## Label Schema

Primary field:

```text
independent_relation_label
```

Allowed labels:

```text
reliable_informative
valid_but_trivial_dense
annotation_sparsity_candidate
ontology_mismatch
invalid_relation
invalid_pair
visibility_or_geometry_artifact
abstain_uncertain
```

Binary mapping for later diagnostics:

| Use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass-only | `ontology_mismatch`, `abstain_uncertain` |

Supporting fields:

```text
subject_identity_valid
object_identity_valid
object_pair_visible
relation_visible_or_inferable
visual_3d_support
relation_informativeness
confidence
evidence_notes
```

## Asset Packet Requirement

The blind sheets are not yet label-ready because evidence packet paths are empty:

```text
evidence_packet_status = needs_asset_generation
```

Generated asset request manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/asset_request_manifest.jsonl
```

Requested evidence:

- subject/object multi-view crops.
- co-visible contact/context sheet.
- object-pair point-cloud or mesh crop.
- optional instance segmentation overlay.

Important boundary:

```text
These assets are audit evidence only. They do not become V_mv_e model input
until the S_e/G_e/C_e/U_e factorized posterior has independent-label support.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_all_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_priority_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_support_contact_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_relative_vertical_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_proximity_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/internal_key.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/asset_request_manifest.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `blind_all_sheet.tsv` | 360 + header |
| `blind_priority_sheet.tsv` | 180 + header |
| `blind_support_contact_sheet.tsv` | 201 + header |
| `blind_relative_vertical_sheet.tsv` | 114 + header |
| `blind_proximity_sheet.tsv` | 45 + header |
| `internal_key.jsonl` | 360 |
| `asset_request_manifest.jsonl` | 360 |

## Interpretation

This step fixes the exact failure found in `64_full_train_label_policy_audit.md`
at the protocol level: the annotator cannot see the target-construction
metadata that made the previous target recoverable.

However, this does not yet create a usable target. The next requirement is
evidence packet generation and then label readiness.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
```

Observed:

```text
validation_used=False
leakage=pass
```

## Next TODO

Completed next action:

```text
full_train_independent_asset_packets
```

Result:

```text
full_train_independent_asset_packets_partial
```

347 / 360 rows are packet-ready, 13 rows are partial, and label-facing leakage
audit passes. The next action is a gap audit before independent label fill.

Next action:

```text
full_train_asset_packet_gap_audit
```
