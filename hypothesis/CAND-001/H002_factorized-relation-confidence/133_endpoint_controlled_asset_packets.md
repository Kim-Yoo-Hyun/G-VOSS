# Endpoint-Controlled Asset Packets

Date: 2026-06-20 KST

## Purpose

이 단계는 `132_endpoint_controlled_candidate_mining.md`에서 선택된 endpoint-controlled
후보 중 기존 audit packet이 없던 `9`개 row에 대해 evidence packet을 생성하고, 기존
packet-ready `53`개와 합쳐 full `62`-row label sheet를 준비하는 것이다.

## Boundary

- Split: train only.
- Validation/test row는 사용하지 않았다.
- 새 posterior model은 학습하지 않았다.
- Multi-view/mesh evidence는 audit/label evidence일 뿐, posterior input이 아니다.
- Endpoint flag와 hidden sampling axes는 post-label-only manifest에만 둔다.
- H001 artifact는 수정하지 않았다.

## Method

기존 `full_train_independent_asset_packets.py`의 packet 생성 로직을 재사용했다.
이번 단계에서는 endpoint-controlled asset request `9`개에만 적용했다.

각 generated packet은 다음 asset을 포함한다.

```text
packet.md
contact_context_sheet.jpg
subject_*.jpg
object_*.jpg
mesh_packet.md
```

그 다음 기존 packet-ready `53`개 row의 packet path와 새로 생성한 `9`개 packet path를
통합해 labeler-facing sheet를 만들었다.

```text
endpoint_controlled_full_label_sheet.tsv
```

Hidden fields는 별도 post-label-only manifest에만 유지했다.

```text
endpoint_controlled_full_manifest_post_label_only.jsonl
```

## Results

```text
status = h002_endpoint_controlled_asset_packets_ready
generated_packet_rows = 9
generated_non_ready_rows = 0
full_label_sheet_rows = 62
packet_status_counts = ready: 62
packet_path_errors = 0
label_surface_leakage = pass
next = endpoint_controlled_label_fill
```

Family count:

| Family | Rows |
| --- | ---: |
| `support_contact` | 37 |
| `relative_vertical` | 25 |

Packet source:

| Source | Rows |
| --- | ---: |
| existing packet-ready rows | 53 |
| newly generated asset-needed rows | 9 |
| total label sheet rows | 62 |

## Interpretation

The endpoint-controlled label batch is now packet-ready. The previous blocker
was not posterior capacity but missing audit evidence for `9` selected candidates.
That blocker is removed:

- all `9` generated packets are `ready`;
- all `62` label rows have packet paths;
- label-surface leakage audit passes;
- no validation/test data was used.

This still does not validate H002 posterior novelty. It only prepares the next
label-fill step needed before endpoint-controlled target-independence audit and
posterior smoke.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_asset_packet_generation.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/endpoint_controlled_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/endpoint_controlled_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/asset_needed_manifest_with_packets_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/packets/
```

## Next TODO

```text
endpoint_controlled_label_fill
```

Required next action:

- Fill the 62-row endpoint-controlled label sheet.
- Keep `endpoint_controlled_full_manifest_post_label_only.jsonl` hidden during fill.
- After fill, ingest labels and run endpoint-controlled target-independence audit before any posterior smoke.
