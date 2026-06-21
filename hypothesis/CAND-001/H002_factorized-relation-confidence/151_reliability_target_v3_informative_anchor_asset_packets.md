# Reliability Target V3 Informative Anchor Asset Packets

Date: 2026-06-20 KST

## Purpose

이 단계는 `150_reliability_target_v3_informative_anchor_candidate_mining.md`에서 남아 있던
`34`개 asset-needed informative-anchor row에 대해 evidence packet을 생성하고, 기존
packet-ready `126`개와 합쳐 full `160`-row label sheet를 packet-complete 상태로 만드는
것이다.

## Boundary

- Split: Open3DSG train only.
- Validation/test row는 사용하지 않았다.
- Label fill은 아직 수행하지 않았다.
- Posterior model은 학습하지 않았다.
- Multi-view/mesh packet은 audit/label evidence일 뿐, posterior input이 아니다.
- Hidden proxy/sampling field는 post-label-only manifest에만 유지했다.
- H001 artifact는 수정하지 않았다.

## Method

기존 `full_train_independent_asset_packets.py`의 packet 생성 로직을 재사용했다. 이번 단계에서는
informative-anchor candidate mining의 `asset_needed` `34`개 row에만 packet을 생성했다.

각 generated packet은 다음 asset을 포함한다.

```text
packet.md
contact_context_sheet.jpg
subject_*.jpg
object_*.jpg
mesh_packet.md
```

그 다음 기존 packet-ready `126`개 row의 packet path와 새로 생성한 `34`개 packet path를
통합해 full label sheet를 만들었다.

```text
informative_anchor_full_label_sheet.tsv
```

Hidden fields는 별도 post-label-only manifest에만 유지했다.

```text
informative_anchor_full_manifest_post_label_only.jsonl
```

## Results

```text
status = h002_reliability_target_v3_informative_anchor_asset_packets_ready
input selected rows = 160
asset-needed input rows = 34
generated packet rows = 34
generated non-ready rows = 0
full label sheet rows = 160
ready label rows = 160
packet path errors = 0
label-surface leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_label_fill
```

Category summary:

| Category | Rows | Ready | Generated | Existing | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 40 | 24 | 16 | 31 |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 40 | 18 | 22 | 20 |
| `trivial_room_surface_negative_proxy` | 40 | 40 | 19 | 21 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 40 | 15 | 25 | 16 | 24 | 28 |

Packet source:

| Source | Rows |
| --- | ---: |
| existing independent asset packet | 126 |
| generated informative-anchor asset packet | 34 |
| total full label sheet | 160 |

## Interpretation

이제 preferred route인 full `160`-row informative-anchor label fill이 가능하다. 이전 blocker는
target 자체가 아니라 `34`개 row의 evidence packet 부재였고, 이 blocker는 제거됐다.

중요한 점은 이 단계가 아직 H002 posterior를 검증한 것이 아니라는 점이다. 이 단계는 label fill을
가능하게 만든 evidence-readiness 단계다. H002 posterior smoke는 여전히 다음 순서를 거쳐야 한다.

1. full `160`-row label fill
2. label ingestion
3. target-independence audit
4. controlled slice가 통과할 때만 posterior smoke

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/asset_needed_manifest_with_packets_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/category_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/packets/
```

## Next TODO

```text
reliability_target_v3_informative_anchor_label_fill
```

Required next action:

- Fill the full `160`-row informative-anchor label sheet.
- Keep `informative_anchor_full_manifest_post_label_only.jsonl` hidden during fill.
- Treat proxy category as sampling provenance, not as target label.
- After fill, ingest labels and run target-independence audit before any posterior smoke.
