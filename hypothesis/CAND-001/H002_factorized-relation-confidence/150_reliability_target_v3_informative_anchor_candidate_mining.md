# H002 Reliability Target V3 Informative Anchor Candidate Mining

Date: 2026-06-20 KST

## Purpose

`149_reliability_target_v3_informative_anchor_plan.md`에서 만든 160개 seed candidate를
실제 v3 label sheet와 post-label-only manifest로 변환했다.

핵심 질문:

```text
Can we prepare an informative-anchor label sheet while keeping proxy categories
hidden and preserving the option to request missing asset packets?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test row는 사용하지 않았다.
- Label fill은 하지 않았다.
- Posterior model은 학습하지 않았다.
- H001 artifact는 수정하지 않았다.
- Multi-view / pointcloud / contact sheet는 audit/label evidence이며 model input이 아니다.
- Informative-anchor proxy category는 sampling stratum일 뿐 target label이 아니다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_candidate_mining.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_candidate_mining.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_candidate_mining_ready_needs_asset_packets
full=160
ready=126
asset_needed=34
leakage=0
packet_errors=0
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_informative_anchor_asset_packets
```

## Result

Status:

```text
h002_reliability_target_v3_informative_anchor_candidate_mining_ready_needs_asset_packets
```

Decision:

```text
The informative-anchor full label sheet is prepared, and a packet-ready fallback
sheet is also available. Because 34 selected rows still need asset packets,
generate/request those packets before the preferred balanced label fill. Use
the packet-ready fallback only with an explicit coverage caveat.
```

## Counts

| Item | Count |
| --- | ---: |
| selected seed rows | 160 |
| full label sheet rows | 160 |
| packet-ready fallback rows | 126 |
| asset-needed rows | 34 |
| support_contact | 76 |
| relative_vertical | 84 |
| unique scans | 94 |
| unique physical pairs | 160 |
| label-surface leakage hits | 0 |
| packet path errors | 0 |
| validation errors | 0 |

Category summary:

| Category | Rows | Packet Ready | Asset Needed | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 18 | 22 | 20 |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 24 | 16 | 31 |
| `trivial_room_surface_negative_proxy` | 40 | 21 | 19 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 25 | 15 | 16 | 24 | 28 |

## Label Sheets

Two label sheets were produced:

- `informative_anchor_label_sheet.tsv`: full 160-row sheet. It includes `asset_needed`
  rows with empty packet paths.
- `informative_anchor_packet_ready_label_sheet.tsv`: 126-row fallback sheet containing
  only packet-ready rows.

Preferred path:

```text
asset packet generation/request for 34 rows -> full 160-row label fill
```

Fallback path:

```text
packet-ready-only 126-row label fill with an explicit category coverage caveat
```

The preferred path is better because the full sheet preserves the intended `40/40/40/40`
category balance. The packet-ready fallback under-represents the two categories that most
need negative/uncertain supervision:

- `trivial_room_surface_negative_proxy`: 21/40 packet-ready.
- `uncertain_or_ontology_negative_proxy`: 25/40 packet-ready.

## Safety Checks

- Label-surface leakage hits: `0`.
- Packet path errors: `0`.
- Duplicate physical pair keys: `0`.
- Hidden proxy fields are stored only in `informative_anchor_manifest_post_label_only.jsonl`.
- The visible sheet does not expose `anchor_category`, `p_geom_valid`, `geometry_status`,
  semantic score/rank, endpoint flag pattern, matched predicates, or reason codes.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/150_reliability_target_v3_informative_anchor_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/category_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/selected_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/v3_label_schema.json
```

## Next TODO

```text
reliability_target_v3_informative_anchor_asset_packets
```

Goal:

- Generate or attach asset packets for the 34 `asset_needed` rows.
- Preserve the 160-row balanced informative-anchor label sheet as the preferred route.
- Keep packet-ready-only label fill as a fallback, not the primary route.
- Keep posterior smoke blocked until label fill, ingestion, and target-independence audit pass.
