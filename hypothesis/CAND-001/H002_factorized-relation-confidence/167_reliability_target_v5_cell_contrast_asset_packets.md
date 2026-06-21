# Reliability Target V5 Cell Contrast Asset Packets

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packets` TODO를
진행했다. 이 단계는 v5 cell-contrast candidate mining에서 남아 있던 `78`개
asset-needed row에 대해 multi-view / mesh / contact-context evidence packet을 생성하고,
기존 `2`개 packet-ready row와 합쳐 full `80`-row label sheet를 만드는 단계다.

이 단계는 label fill이나 posterior smoke가 아니다. 목표는 label evidence surface를 준비하고,
packet coverage가 label fill로 넘어갈 만큼 충분한지 확인하는 것이다.

## Boundary

- Split: train-only
- Validation/test usage: none
- Label fill: not performed
- Posterior training/smoke: not performed
- H001 artifact modification: none
- Multi-view and mesh packets: audit/label evidence only, not posterior input
- Cell contrast role, rank, semantic score, geometry status, and proxy fields remain hidden

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packets.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packets.py
```

## Result

```text
status = h002_reliability_target_v5_cell_contrast_asset_packets_partial
input selected rows = 80
asset-needed input rows = 78
generated packet rows = 78
generated ready rows = 66
generated non-ready rows = 12
existing packet-ready rows = 2
full label sheet rows = 80
ready label rows = 68
packet path errors = 1
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v5_cell_contrast_asset_packet_gap_audit
```

Non-ready rows:

| Item | Count |
| --- | ---: |
| partial generated rows | 12 |
| support_contact partial rows | 6 |
| relative_vertical partial rows | 6 |
| rows missing subject crop | 6 |
| rows missing object crop | 7 |
| rows missing contact/context sheet | 1 |
| rows missing mesh packet | 0 |

The single packet path error is:

```text
blind_review_id = ftv5cc_0a7d66060905
field = contact_or_context_sheet
error_type = empty_packet_path
row_number = 67
```

## Interpretation

v5 asset packet generation produced packet files for most selected rows and kept the label surface clean:
field/value leakage and packet-text leakage are all `0`. However, the full `80`-row sheet is not
label-fill-ready because `12` generated rows are partial and one partial row has an empty
`contact_or_context_sheet` path.

The main failure mode is not target construction leakage; it is evidence coverage. Most partial rows still
have `packet.md`, mesh packet, and at least one endpoint crop, but one side of the subject/object visual
crop is missing. The next step should audit whether these rows are acceptable as limited-view evidence,
should be marked `needs_more_evidence`, or should be replaced before label fill.

Posterior smoke remains blocked until v5 labels are filled, ingested, and target-independence audit passes.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/167_reliability_target_v5_cell_contrast_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_contrast_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_contrast_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/label_surface_leakage_audit.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/packets/
```

## Next TODO

```text
reliability_target_v5_cell_contrast_asset_packet_gap_audit
```
