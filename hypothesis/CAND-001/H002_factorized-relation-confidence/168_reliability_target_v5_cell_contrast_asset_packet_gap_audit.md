# Reliability Target V5 Cell Contrast Asset Packet Gap Audit

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packet_gap_audit`
TODO를 진행했다. 이 단계는 v5 asset packet generation에서 남은 partial packet row를
label fill 전에 감사하는 단계다.

핵심 질문:

```text
Which partial packet rows can still be labeled under a limited-view caveat,
and which cell-contrast pairs must be excluded or replaced before label fill?
```

## Boundary

- Split: train-only
- Validation/test usage: none
- Label fill: not performed
- Posterior training/smoke: not performed
- Multi-view and mesh packets: audit/label evidence only, not posterior input
- Pair integrity rule: 한 row가 replacement-needed이면 cell-contrast pair 전체를 label fill에서 제외한다
- H001 artifacts: not modified

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packet_gap_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packet_gap_audit.py
```

Observed:

```text
status=h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness
rows=80
label_ready_rows=72
label_ready_pairs=36
excluded_pairs=4
limited_view=6
path_errors=0
leakage=0
validation_used=False
next=reliability_target_v5_cell_contrast_label_readiness
```

## Decision Policy

| Condition | Row Decision |
| --- | --- |
| complete packet | `label_ready` |
| one endpoint crop missing, mesh packet ready, contact/context sheet ready | `limited_view_evaluable` |
| one endpoint crop missing, relative-vertical family, mesh packet ready | `limited_view_evaluable` |
| both endpoint crops missing | `replacement_needed` |
| missing endpoint has generic label such as `object` | `replacement_needed` |
| otherwise insufficient packet evidence | `replacement_needed` |

Pair-level rule:

| Pair Condition | Pair Decision |
| --- | --- |
| both rows complete | `pair_ready` |
| at least one row is `limited_view_evaluable`, no replacement-needed row | `pair_ready_with_limited_view_caveat` |
| any row is `replacement_needed` | `exclude_pair_before_label_fill` |

## Result

```text
input rows = 80
input pairs = 40
label-ready rows = 72
label-ready pairs = 36
excluded rows = 8
excluded pairs = 4
limited-view rows kept = 6
replacement-needed rows = 5
output path errors = 0
visible leakage hits = 0
input validation errors = 0
```

Row decision counts:

| Decision | Rows |
| --- | ---: |
| `label_ready` | 68 |
| `limited_view_evaluable` | 7 |
| `replacement_needed` | 5 |

Pair decision counts:

| Decision | Pairs |
| --- | ---: |
| `pair_ready` | 30 |
| `pair_ready_with_limited_view_caveat` | 6 |
| `exclude_pair_before_label_fill` | 4 |

Label-ready role balance:

| Role | Rows |
| --- | ---: |
| `positive_proxy` | 36 |
| `negative_proxy` | 36 |

Label-ready family balance:

| Family | Rows |
| --- | ---: |
| `support_contact` | 44 |
| `relative_vertical` | 28 |

Excluded pairs:

```text
v5cell_0013
v5cell_0014
v5cell_0033
v5cell_0034
```

## Interpretation

- The packet gap no longer blocks v5 label preparation.
- `36` cell-contrast pairs remain label-ready, preserving role balance:
  `36` positive proxy rows and `36` negative proxy rows.
- `6` limited-view rows are kept because one endpoint crop is missing but mesh and contact/context
  evidence are sufficient for label audit.
- `5` rows are replacement-needed. Because v5 uses pair-level contrast, this excludes `4` whole pairs
  before label fill.
- The previous empty `contact_or_context_sheet` path is removed from the label-ready sheet because its
  pair is excluded.
- Label fill still has not started. The next step is label-readiness validation over the
  `72`-row / `36`-pair sheet.

Posterior smoke remains blocked until v5 labels are filled, ingested, and target-independence audit passes.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/168_reliability_target_v5_cell_contrast_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/row_gap_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/partial_row_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/pair_gap_decisions.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/excluded_pair_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/excluded_pair_ids.txt
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/replacement_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/output_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/visible_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/packets/
```

## Next TODO

```text
reliability_target_v5_cell_contrast_label_readiness
```
