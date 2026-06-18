# H002 Full Train Independent Label Readiness

Last updated: 2026-06-17

## Purpose

`67_full_train_asset_packet_gap_audit.md` 이후 355개 row가 label-ready로
남았다. 이번 단계는 independent label fill 전에 labeler-facing sheet가 실제로
사용 가능한지 검증한다.

핵심 질문:

```text
Are the full-train independent label-ready sheets safe and sufficient for
rank/role-hidden label fill?
```

## Decision

Current status:

```text
full_train_independent_label_readiness_ready_for_label_fill
```

Meaning:

```text
The 355-row label-ready all sheet and 179-row priority sheet pass schema,
leakage, packet-path, excluded-id, and coverage checks.
```

This is not a posterior result and not a completed label result.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
```

Observed:

```text
status=full_train_independent_label_readiness_ready_for_label_fill rows=355 excluded=5 errors=0 leakage=0 validation_used=False
```

## Input

Label-ready sheets:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_priority_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_support_contact_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_relative_vertical_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_proximity_sheet_with_packets.tsv
```

Reference protocol and hidden key:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/internal_key.jsonl
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- no labels are filled in this step.
- multi-view and mesh packets are audit evidence only.
- hidden fields are not joined until after independent labels are locked.

Not established:

- completed independent labels.
- usable positive/negative binary target.
- factorized posterior improvement.
- paper-level performance.

## Readiness Checks

The script checks:

- exact label-ready sheet schema.
- forbidden hidden-metadata header fragments.
- forbidden hidden-metadata text fragments in label-facing sheet text.
- packet file existence for `multiview_packet`, `pointcloud_or_mesh_packet`,
  and `contact_or_context_sheet`.
- no excluded blind IDs appear in label-ready sheets.
- all `blind_review_id` values are present in the hidden `internal_key`.
- reviewer fields are still empty before label fill.
- family/predicate coverage remains above minimum thresholds.
- packet text does not expose rank, score, queue, label-match, role, semantic
  score, `p_geom_valid`, or other target-construction metadata.

## Result

Readiness result:

| Check | Count |
| --- | ---: |
| label-ready rows | 355 |
| excluded rows | 5 |
| readiness errors | 0 |
| leakage hits | 0 |
| review-started rows | 0 |

Coverage:

| Sheet | Rows | Scans | Minimum | Status |
| --- | ---: | ---: | ---: | --- |
| `all` | 355 | 92 | 300 | `pass` |
| `priority` | 179 | 66 | 150 | `pass` |
| `support_contact` | 199 | 70 | 150 | `pass` |
| `relative_vertical` | 111 | 43 | 80 | `pass` |
| `proximity` | 45 | 15 | 30 | `pass` |

All-sheet family coverage:

| Family | Rows |
| --- | ---: |
| `support_contact` | 199 |
| `relative_vertical` | 111 |
| `proximity` | 45 |

All-sheet predicate coverage:

| Predicate | Rows |
| --- | ---: |
| `lying on` | 81 |
| `lower than` | 66 |
| `supported by` | 62 |
| `standing on` | 56 |
| `higher than` | 45 |
| `close by` | 45 |

## Ingestion Schema

Prepared:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ingestion_schema.json
```

Required completion fields:

```text
reviewer_id
review_round
subject_identity_valid
object_identity_valid
object_pair_visible
relation_visible_or_inferable
visual_3d_support
relation_informativeness
independent_relation_label
confidence
```

Primary label field:

```text
independent_relation_label
```

Binary policy for later train-only posterior diagnostics:

| Use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass-only | `ontology_mismatch`, `abstain_uncertain` |

Important boundary:

```text
internal_key.jsonl is joined only after labels are completed and locked.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ready_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/readiness_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/coverage.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ingestion_schema.json
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `label_ready_manifest.jsonl` | 355 |
| `readiness_errors.jsonl` | 0 |
| `leakage_hits.jsonl` | 0 |

## Interpretation

The current blocker has moved from label surface construction to actual
independent label fill. The next step is still not posterior smoke. H002 should
first fill independent labels, ingest them with the locked schema, and only then
test whether `S_e/G_e/C_e/U_e` factorization explains relation reliability.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
```

Observed:

```text
validation_used=False
errors=0
leakage=0
```

## Next TODO

Completed next action:

```text
full_train_independent_label_fill
```

Result:

```text
full_train_independent_codex_labels_filled_not_human_confirmed
```

355 rows are filled with codex-version independent labels. 283 rows are
binary-usable: 155 positive and 128 negative.

Next action:

```text
full_train_independent_label_ingestion
```

Goal:

- join completed labels with hidden provenance only after label lock.
- materialize independent binary/multiclass targets.
- audit whether the new target is still explained by hidden construction metadata.
- only after ingestion and audit, decide whether posterior smoke can resume.
