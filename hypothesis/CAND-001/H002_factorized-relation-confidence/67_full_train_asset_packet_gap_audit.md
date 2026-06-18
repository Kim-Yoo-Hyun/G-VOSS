# H002 Full Train Asset Packet Gap Audit

Last updated: 2026-06-16

## Purpose

`66_full_train_independent_asset_packets.md`에서 360개 blind row 중 13개가
partial packet으로 남았다. 이번 단계는 label fill 전에 partial row를 감사해
사용 가능 row와 제외 row를 분리한다.

핵심 질문:

```text
Which partial packet rows can still be independently labeled, and which rows
must be excluded before label fill?
```

## Decision

Current status:

```text
full_train_asset_packet_gap_audit_ready_for_label_readiness
```

Meaning:

```text
355 / 360 rows are label-ready after packet gap audit. 5 rows are excluded
before label fill.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
```

Observed:

```text
status=full_train_asset_packet_gap_audit_ready_for_label_readiness rows=360 label_ready=355 excluded=5 partial=13 validation_used=False
```

## Input

Packet manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/packet_manifest.jsonl
```

## Boundary

Established:

- train-only.
- no validation/test rows.
- no posterior is trained.
- this is not label fill.
- this only decides packet usability before independent label readiness.

## Decision Policy

The gap audit uses the following conservative policy:

| Condition | Decision |
| --- | --- |
| complete packet | `label_ready` |
| one endpoint crop missing, mesh packet ready, contact/context sheet ready | `label_ready_with_packet_caveat` |
| one endpoint crop missing, relative-vertical family, mesh packet ready | `label_ready_with_packet_caveat` |
| both subject/object crops missing | `exclude_before_label_fill` |
| missing endpoint has generic label such as `objects` | `exclude_before_label_fill` |
| otherwise insufficient evidence | `exclude_before_label_fill` |

For `label_ready_with_packet_caveat`, annotators must use low confidence or
`abstain_uncertain` if the missing endpoint identity cannot be checked.

## Result

Decision counts:

| Decision | Rows |
| --- | ---: |
| `label_ready` | 347 |
| `label_ready_with_packet_caveat` | 8 |
| `exclude_before_label_fill` | 5 |

Family decision counts:

| Family | Ready | Ready With Caveat | Excluded |
| --- | ---: | ---: | ---: |
| `support_contact` | 196 | 3 | 2 |
| `relative_vertical` | 106 | 5 | 3 |
| `proximity` | 45 | 0 | 0 |

Label-ready rows:

```text
355
```

Excluded rows:

```text
5
```

Excluded blind IDs:

```text
ftind_10ba1277c139
ftind_e448888d62f5
ftind_009bdaa1a9e0
ftind_082efa588b99
ftind_7709e1f9e4c1
```

## Partial Row Decisions

| Blind ID | Family | Predicate | Missing Side | Decision |
| --- | --- | --- | --- | --- |
| `ftind_507aafeec844` | `support_contact` | `lying on` | subject | `label_ready_with_packet_caveat` |
| `ftind_10ba1277c139` | `support_contact` | `supported by` | object | `exclude_before_label_fill` |
| `ftind_3bc7e6e6dca0` | `support_contact` | `supported by` | object | `label_ready_with_packet_caveat` |
| `ftind_e448888d62f5` | `support_contact` | `supported by` | object | `exclude_before_label_fill` |
| `ftind_1f2f0b4a815e` | `support_contact` | `supported by` | subject | `label_ready_with_packet_caveat` |
| `ftind_4336410ef557` | `relative_vertical` | `higher than` | object | `label_ready_with_packet_caveat` |
| `ftind_da5b33eafe5a` | `relative_vertical` | `higher than` | subject | `label_ready_with_packet_caveat` |
| `ftind_009bdaa1a9e0` | `relative_vertical` | `higher than` | subject/object | `exclude_before_label_fill` |
| `ftind_082efa588b99` | `relative_vertical` | `higher than` | object | `exclude_before_label_fill` |
| `ftind_5883f99e1e92` | `relative_vertical` | `lower than` | object | `label_ready_with_packet_caveat` |
| `ftind_7d898538b783` | `relative_vertical` | `lower than` | subject | `label_ready_with_packet_caveat` |
| `ftind_7709e1f9e4c1` | `relative_vertical` | `lower than` | subject/object | `exclude_before_label_fill` |
| `ftind_d0eb5b038d1d` | `relative_vertical` | `lower than` | subject | `label_ready_with_packet_caveat` |

## Label-Ready Sheets

Generated sheets:

| Sheet | Label-Ready | Excluded |
| --- | ---: | ---: |
| `label_ready_all_sheet_with_packets.tsv` | 355 | 5 |
| `label_ready_priority_sheet_with_packets.tsv` | 179 | 1 |
| `label_ready_support_contact_sheet_with_packets.tsv` | 199 | 2 |
| `label_ready_relative_vertical_sheet_with_packets.tsv` | 111 | 3 |
| `label_ready_proximity_sheet_with_packets.tsv` | 45 | 0 |

The label-ready sheets add:

```text
packet_gap_decision
packet_gap_reason
```

These fields do not expose rank, score, geometry status, queue, label-match
status, or proposed-role metadata.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/gap_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/excluded_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/excluded_blind_ids.txt
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_priority_sheet_with_packets.tsv
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `gap_decisions.jsonl` | 360 |
| `label_ready_packet_rows.jsonl` | 355 |
| `excluded_packet_rows.jsonl` | 5 |
| `label_ready_all_sheet_with_packets.tsv` | 355 + header |
| `label_ready_priority_sheet_with_packets.tsv` | 179 + header |

## Interpretation

The asset gap no longer blocks independent label readiness. The correct next
step is still not posterior smoke. The next step is to validate that the
label-ready sheets have the expected schema and enough family/label coverage
for independent label fill.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
```

Observed:

```text
validation_used=False
```

## Next TODO

Completed next action:

```text
full_train_independent_label_readiness
```

Result:

```text
full_train_independent_label_readiness_ready_for_label_fill
```

355 label-ready rows pass schema, leakage, packet-path, excluded-id, and
coverage checks.

Next action:

```text
full_train_independent_label_fill
```

Goal:

- fill independent labels without exposing hidden target-construction metadata.
- ingest labels with the locked schema.
- verify usable binary target counts before posterior smoke.
