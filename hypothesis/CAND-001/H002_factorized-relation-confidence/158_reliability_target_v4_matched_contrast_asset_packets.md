# H002 Reliability Target V4 Matched Contrast Asset Packets

Date: 2026-06-20 KST

## Purpose

`reliability_target_v4_matched_contrast_asset_packets`는 v4 matched-contrast candidate mining에서
남아 있던 155개 `asset_needed` row에 대해 multi-view / mesh / contact-context evidence
packet을 생성하고, 기존 5개 packet-ready row와 합쳐 full 160-row label sheet를 만드는 단계다.

이 단계는 label fill이나 posterior smoke가 아니다. 목표는 label evidence surface를 준비하고,
packet coverage가 label fill로 넘어갈 만큼 충분한지 확인하는 것이다.

## Boundary

- Split: train-only
- Validation/test usage: none
- Label fill: not performed
- Posterior training/smoke: not performed
- H001 artifact modification: none
- Multi-view and mesh packets: audit/label evidence only, not posterior input
- Matched-contrast role, rank, semantic score, geometry status, and proxy fields remain hidden

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packets.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packets.py
```

## Result

```text
status = h002_reliability_target_v4_matched_contrast_asset_packets_partial
input selected rows = 160
asset-needed input rows = 155
generated packet rows = 155
generated ready rows = 135
generated partial rows = 20
existing packet-ready rows = 5
full label sheet rows = 160
ready label rows = 140
partial label rows = 20
packet path errors = 0
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_asset_packet_gap_audit
```

Partial rows:

| Item | Count |
| --- | ---: |
| partial generated rows | 20 |
| support_contact partial rows | 13 |
| relative_vertical partial rows | 7 |
| rows missing subject crop | 12 |
| rows missing object crop | 8 |

## Interpretation

- v4 asset packet generation produced usable packet files for every selected row:
  `packet path errors = 0`.
- Label-surface leakage is clean:
  contrast role, proxy, rank, semantic score, `p_geom`, geometry status, and target-construction
  fields are not exposed in the visible label sheet or packet text.
- However, the full 160-row sheet is not strictly packet-ready because 20 generated rows have only
  one endpoint crop available.
- Those 20 rows still have packet markdown, mesh packet, and contact/context sheet paths, but one
  of subject/object visual crops is absent.
- Therefore label fill should not proceed yet. The next step is a gap audit that decides whether
  these 20 rows are acceptable as `limited_view_evaluable`, should be marked `needs_more_evidence`,
  or should be replaced by new matched-contrast candidates.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/158_reliability_target_v4_matched_contrast_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/matched_contrast_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/matched_contrast_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/visible_value_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/stratum_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/packets/
```

## Next TODO

```text
reliability_target_v4_matched_contrast_asset_packet_gap_audit
```
