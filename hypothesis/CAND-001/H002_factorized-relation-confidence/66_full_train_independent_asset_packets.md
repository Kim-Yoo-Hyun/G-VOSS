# H002 Full Train Independent Asset Packets

Last updated: 2026-06-16

## Purpose

`65_full_train_independent_label_protocol.md`에서 만든 blind sheet는 metadata leakage를
막았지만, 실제 labeling에는 visual/geometry evidence packet이 필요했다.

이번 단계의 목적:

```text
Generate or link multi-view/mesh/point-cloud evidence packets for each blind
full-train row without exposing hidden target-construction metadata.
```

## Decision

Current status:

```text
full_train_independent_asset_packets_partial
```

Meaning:

```text
347 / 360 blind rows are packet-ready. 13 rows are partial because one or both
object-side multi-view crops are missing. Mesh packets exist for all rows.
```

This is not a posterior result and not a label result.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
```

Observed:

```text
status=full_train_independent_asset_packets_partial rows=360 status_counts={'partial': 13, 'ready': 347} leakage=pass validation_used=False
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- multi-view and mesh evidence are audit support only.
- original crop filenames are not exposed to annotators.
- packet paths are written into copies of the blind sheets, not into the original
  protocol sheets.

Not established:

- completed independent labels.
- label readiness.
- posterior method evidence.

## Packet Construction

For each blind row, the script creates:

```text
packet.md
contact_context_sheet.jpg
subject_*.jpg
object_*.jpg
mesh_packet.md
```

The image files are resized/sanitized copies:

```text
subject_01.jpg
object_01.jpg
...
```

This avoids exposing original Open3DSG crop filenames, which may contain
projection-quality strings.

`mesh_packet.md` links existing 3RScan mesh/point-cloud files:

```text
mesh.refined.v2.obj
labels.instances.annotated.v2.ply
labels.instances.align.annotated.v2.ply
semseg.v2.json
```

The packet text avoids rank, score, geometry status, queue, label-match status,
and proposed-role fields.

## Coverage

Packet coverage:

| Item | Rows |
| --- | ---: |
| total blind rows | 360 |
| packet-ready rows | 347 |
| partial rows | 13 |
| subject images linked | 353 |
| object images linked | 352 |
| contact/context sheets ready | 358 |
| mesh packets ready | 360 |

Family status:

| Family | Ready | Partial |
| --- | ---: | ---: |
| `support_contact` | 196 | 5 |
| `relative_vertical` | 106 | 8 |
| `proximity` | 45 | 0 |

Updated sheet status:

| Sheet | Ready | Partial |
| --- | ---: | ---: |
| `blind_all_sheet_with_packets.tsv` | 347 | 13 |
| `blind_priority_sheet_with_packets.tsv` | 174 | 6 |
| `blind_support_contact_sheet_with_packets.tsv` | 196 | 5 |
| `blind_relative_vertical_sheet_with_packets.tsv` | 106 | 8 |
| `blind_proximity_sheet_with_packets.tsv` | 45 | 0 |

## Non-Ready Rows

Non-ready manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/non_ready_packet_rows.jsonl
```

Partial rows:

| Blind ID | Family | Predicate | Missing Side |
| --- | --- | --- | --- |
| `ftind_507aafeec844` | `support_contact` | `lying on` | subject crop |
| `ftind_10ba1277c139` | `support_contact` | `supported by` | object crop |
| `ftind_3bc7e6e6dca0` | `support_contact` | `supported by` | object crop |
| `ftind_e448888d62f5` | `support_contact` | `supported by` | object crop |
| `ftind_1f2f0b4a815e` | `support_contact` | `supported by` | subject crop |
| `ftind_4336410ef557` | `relative_vertical` | `higher than` | object crop |
| `ftind_da5b33eafe5a` | `relative_vertical` | `higher than` | subject crop |
| `ftind_009bdaa1a9e0` | `relative_vertical` | `higher than` | both crops |
| `ftind_082efa588b99` | `relative_vertical` | `higher than` | object crop |
| `ftind_5883f99e1e92` | `relative_vertical` | `lower than` | object crop |
| `ftind_7d898538b783` | `relative_vertical` | `lower than` | subject crop |
| `ftind_7709e1f9e4c1` | `relative_vertical` | `lower than` | both crops |
| `ftind_d0eb5b038d1d` | `relative_vertical` | `lower than` | subject crop |

All partial rows still have mesh packets.

## Leakage Audit

Label-facing packet/sheet leakage audit:

```text
status = pass
```

Checked surfaces:

- packet text for sampled rows.
- mesh packet text for sampled rows.
- updated blind sheet field names.

The label-facing surfaces do not expose:

```text
score, rank, p_geom, geometry_status, h001_verification, queue,
label_match, proposed, role, candidate_axis, prediction_id,
final_controlled, failure_taxonomy, matched_gt, matched_predicate, bucket,
machine_hint, reason_code, semantic, consistency, disagreement, underconfidence
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_priority_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_support_contact_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_relative_vertical_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_proximity_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/packets/
```

Generated packet files:

```text
3808 files under packets/
```

## Interpretation

The asset packet stage is mostly ready but not fully clean. The correct next
step is not label fill and not posterior smoke. The partial rows need a small
gap audit:

- decide whether mesh-only evidence is enough for those 13 rows.
- recover missing crops if possible.
- or mark those rows as `packet_partial_exclude` before independent label fill.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
```

Observed:

```text
validation_used=False
leakage=pass
```

## Next TODO

Completed next action:

```text
full_train_asset_packet_gap_audit
```

Result:

```text
full_train_asset_packet_gap_audit_ready_for_label_readiness
```

355 / 360 rows are label-ready after gap audit. Five rows are excluded before
label fill.

Next action:

```text
full_train_independent_label_readiness
```
