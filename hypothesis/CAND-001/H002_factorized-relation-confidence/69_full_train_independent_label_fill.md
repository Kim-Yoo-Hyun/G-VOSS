# H002 Full Train Independent Label Fill

Last updated: 2026-06-17

## Purpose

`68_full_train_independent_label_readiness.md`에서 355개 label-ready row가
독립 라벨링에 들어갈 수 있음을 확인했다. 이번 단계는 hidden metadata를 보지
않고 label-ready sheet의 visible surface만 사용해 `(codex_ver_full_train_independent)`
bootstrap label을 채운다.

핵심 질문:

```text
Can we fill a rank/role-hidden working target that is usable for the next
post-label ingestion and target-independence audit?
```

## Decision

Current status:

```text
full_train_independent_codex_labels_filled_not_human_confirmed
```

Meaning:

```text
355 rows are filled with codex-version independent labels. 283 rows are
binary-usable under the locked label policy: 155 positive and 128 negative.
```

This is still a bootstrap label result, not a human-confirmed paper label.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
```

Observed:

```text
status=full_train_independent_codex_labels_filled_not_human_confirmed rows=355 binary=283 positive=155 negative=128 excluded=72 validation_used=False
```

## Input

Readiness summary:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/summary.json
```

Label-ready sheets:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_priority_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_support_contact_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_relative_vertical_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_proximity_sheet_with_packets.tsv
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- `internal_key.jsonl` is not read.
- hidden target-construction metadata is not used.
- multi-view/mesh packet paths remain audit evidence references only.
- labels are marked `not_human_confirmed`.
- paper evidence and posterior claim remain blocked.

Not established:

- human-confirmed independent labels.
- target independence after hidden-key join.
- posterior method evidence.
- validation/test performance.

## Label Fill Policy

The fill policy uses visible labeler-facing fields only:

```text
subject_label
predicate_label
predicate_family
object_label
endpoint_pair_note
family_question
positive_cues
negative_cues
evidence_packet_status
packet_gap_decision
```

It does not use:

```text
prediction_id
proposed_audit_role
queue_kind
label_match_status
geometry_status
semantic_rank
semantic_score
p_geom_valid
disagreement_score
underconfidence_score
matched_gt
reason_codes
```

Primary label field:

```text
independent_relation_label
```

Binary policy:

| Target use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| excluded/multiclass-only | `ontology_mismatch`, `abstain_uncertain` |

## Result

Counts:

| Item | Rows |
| --- | ---: |
| filled rows | 355 |
| binary-usable rows | 283 |
| positive rows | 155 |
| negative rows | 128 |
| excluded/multiclass-only rows | 72 |

Label counts:

| Label | Rows |
| --- | ---: |
| `reliable_informative` | 128 |
| `annotation_sparsity_candidate` | 27 |
| `valid_but_trivial_dense` | 92 |
| `invalid_relation` | 24 |
| `invalid_pair` | 12 |
| `ontology_mismatch` | 8 |
| `abstain_uncertain` | 64 |

Family breakdown:

| Family | Label Distribution |
| --- | --- |
| `support_contact` | `reliable_informative=109`, `valid_but_trivial_dense=33`, `abstain_uncertain=26`, `annotation_sparsity_candidate=8`, `invalid_pair=7`, `invalid_relation=8`, `ontology_mismatch=8` |
| `relative_vertical` | `abstain_uncertain=38`, `valid_but_trivial_dense=26`, `annotation_sparsity_candidate=19`, `invalid_relation=16`, `reliable_informative=10`, `invalid_pair=2` |
| `proximity` | `valid_but_trivial_dense=33`, `reliable_informative=9`, `invalid_pair=3` |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/binary_targets_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_all_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_priority_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_support_contact_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_relative_vertical_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_proximity_sheet_codex_ver.tsv
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `completed_all_sheet_codex_ver.tsv` | 355 + header |
| `completed_priority_sheet_codex_ver.tsv` | 179 + header |
| `completed_support_contact_sheet_codex_ver.tsv` | 199 + header |
| `completed_relative_vertical_sheet_codex_ver.tsv` | 111 + header |
| `completed_proximity_sheet_codex_ver.tsv` | 45 + header |
| `labels.jsonl` | 355 |
| `binary_targets_preview.jsonl` | 283 |

## Interpretation

This step creates a workable full-train independent bootstrap target. The
important improvement over the previous controlled target is that this fill does
not read `proposed_audit_role`, `label_match_status`, `queue_kind`, rank,
semantic score, or geometry status.

However, it is still a Codex bootstrap target. The next step must join hidden
fields only after label lock, then audit whether the new target is still
recoverable from label-construction metadata. Posterior smoke should wait until
that ingestion/audit step is complete.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
```

Observed:

```text
validation_used=False
hidden_target_metadata_used=False
internal_key_read=False
```

## Next TODO

Completed next action:

```text
full_train_independent_label_ingestion
```

Result:

```text
full_train_independent_label_ingested_with_target_policy_risk
```

Ingestion succeeds with 355 validated labels, 283 binary targets, and 0 schema
errors. However, the basic group-level probe detects hidden metadata correlation
through `proposed_audit_role_hidden`.

Next action:

```text
full_train_independent_target_independence_audit
```

Goal:

- quantify target-policy shortcut risk.
- build controlled target slices if possible.
- decide whether posterior smoke can resume.
