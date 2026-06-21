# Endpoint-Controlled Candidate Mining

Date: 2026-06-20 KST

## Purpose

이 단계는 `131_endpoint_controlled_resampling_plan.md`에서 확인된 endpoint/object-type
shortcut을 줄이기 위한 train-only candidate mining이다.

직전 결과에서 strict `endpoint_flag_pattern` matching은 endpoint-only shortcut을
줄였지만 row가 `24`개뿐이었다. 따라서 posterior combiner를 다시 바꾸기 전에,
각 endpoint key 안에서 부족한 반대 label 후보를 추가로 확보해야 한다.

## Boundary

- Split: train only.
- Validation/test row는 사용하지 않았다.
- 새 posterior model은 학습하지 않았다.
- Endpoint flag는 sampling/audit control field이며 deployable posterior input이 아니다.
- Mined candidate는 label fill과 ingestion이 끝나기 전까지 target label이 아니다.
- H001 artifact는 수정하지 않았다.

## Method

Deficit plan의 각 `endpoint_flag_pattern`에 대해 필요한 label 방향을 유지했다.

```text
needed_label = positive or negative
```

후보는 두 단계로 선택했다.

1. `candidate_pool.jsonl` 중 기존 asset packet이 준비된 후보를 먼저 사용한다.
2. 부족분은 full-train `HL/LH` queue에서 같은 endpoint key와 needed label proxy에
   맞는 후보를 가져와 `asset_needed` 후보로 표시한다.

Label proxy는 target label이 아니라 candidate mining direction이다.

```text
positive proxy = low semantic + satisfied geometry 계열 후보
negative proxy = high semantic + violated/unsatisfied geometry 계열 후보
```

## Results

```text
status = h002_endpoint_controlled_candidate_mining_ready_needs_asset_packets
requested_deficit_labels = 62
selected_total = 62
selected_packet_ready = 53
selected_asset_needed = 9
residual_unfilled = 0
next = endpoint_controlled_asset_packet_generation
```

Label 방향별 선택:

| Source | Positive proxy | Negative proxy | Total |
| --- | ---: | ---: | ---: |
| packet-ready | 32 | 21 | 53 |
| asset-needed | 4 | 5 | 9 |
| total | 36 | 26 | 62 |

Endpoint deficit coverage:

| Item | Count |
| --- | ---: |
| endpoint deficit groups | 12 |
| groups with residual unfilled | 0 |
| total requested labels | 62 |
| total selected labels | 62 |

## Interpretation

Endpoint-controlled candidate mining is feasible. The capped deficit from the
resampling plan can be fully covered, but not entirely from existing packets.

The immediate blocker is not posterior capacity. The blocker is dataset/evidence
completion for endpoint-controlled label expansion:

- `53` candidates can be filled from existing packets.
- `9` candidates require new asset packet generation before label fill.
- Posterior smoke should not be rerun until the 9 asset-needed candidates are
  packetized, filled, ingested, and merged with the endpoint-controlled slice.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/deficit_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/selected_packet_ready_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/selected_asset_needed_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/selected_all_candidates_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/endpoint_controlled_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/endpoint_controlled_packet_ready_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/asset_request_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/asset_needed_manifest_post_label_only.jsonl
```

## Next TODO

```text
endpoint_controlled_asset_packet_generation
```

Required next action:

- Generate audit/asset packets for the `9` asset-needed candidates.
- Keep post-label-only manifest hidden from labeler-facing material.
- After packet generation, fill `53 + 9` endpoint-controlled labels.
- Ingest the filled labels and rerun endpoint-controlled target-independence checks before posterior smoke.
