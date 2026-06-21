# H002 Reliability Target V4 Matched Contrast Candidate Mining

Date: 2026-06-20 KST

## Purpose

`reliability_target_v4_matched_contrast_candidate_mining`은 v4 matched-contrast plan에서
고른 80개 contrast pair / 160개 row를 실제 label package로 고정하는 단계다.

이 단계의 목표는 posterior를 실행하는 것이 아니라 다음을 준비하는 것이다.

- labeler에게 보이는 visible label sheet
- label 이후에만 조인할 hidden manifest
- 기존 packet-ready row만 모은 fallback sheet
- 155개 asset-needed row에 대한 packet request plan
- contrast role, stratum, rank, semantic score, geometry status, proxy field가 label surface에
  노출되지 않았는지 검증

## Boundary

- Split: train-only
- Validation/test usage: none
- Label fill: not performed
- Posterior training/smoke: not performed
- H001 artifact modification: none
- Multi-view: audit/label evidence only, not posterior input
- Matched-contrast role is a sampling proxy only, not a target label

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_candidate_mining.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_candidate_mining.py
```

## Result

```text
status = h002_reliability_target_v4_matched_contrast_candidate_mining_ready_needs_asset_packets
label rows = 160
contrast pairs = 80
positive proxy rows = 80
negative proxy rows = 80
support_contact rows = 90
relative_vertical rows = 70
packet-ready rows = 5
asset-needed rows = 155
label-surface leakage hits = 0
packet path errors = 0
input validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_asset_packets
```

Hidden diagnostic distribution:

| Field | Counts |
| --- | --- |
| `geometry_status_hidden` | `satisfied:80`, `unsatisfied:80` |
| `rank_band_hidden` | `top50:5`, `top100_only:75`, `rank_101_200:38`, `rank_201_500:29`, `rank_501_1000:13` |
| `label_match_status_hidden` | `exact_match:5`, `family_match:6`, `pair_has_other_predicate:37`, `no_gt_for_pair:112` |

## Interpretation

- v4 matched-contrast label package는 생성됐다.
- 그러나 full label fill로 바로 넘어가기에는 evidence packet coverage가 너무 낮다:
  `5/160` row만 packet-ready이고 `155/160` row는 asset-needed다.
- packet-ready fallback sheet는 format/debug sanity에는 쓸 수 있지만, posterior reopening에는
  너무 작다.
- 다음 단계는 label fill이 아니라 asset packet generation이다.
- Posterior smoke는 reviewed labels를 ingest하고 target-independence audit이 통과하기 전까지
  계속 block한다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/selected_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/stratum_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/v4_label_schema.json
```

## Next TODO

```text
reliability_target_v4_matched_contrast_asset_packets
```
