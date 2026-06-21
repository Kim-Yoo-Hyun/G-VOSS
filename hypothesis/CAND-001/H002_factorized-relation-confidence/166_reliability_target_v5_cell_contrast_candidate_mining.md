# Reliability Target V5 Cell Contrast Candidate Mining

2026-06-21 KST에 `reliability_target_v5_cell_contrast_candidate_mining` TODO를
진행했다. 이 단계는 v5 feasibility scan의 strict cell contrast preview를 실제
label sheet / manifest / asset request plan으로 변환하는 준비 단계다. Label fill,
posterior training, validation/test 사용은 하지 않았다.

## Boundary

- Split은 train-only다.
- validation/test row는 사용하지 않았다.
- Label은 아직 채우지 않았다.
- Posterior는 학습하지 않았다.
- H001 artifact는 수정하지 않았다.
- Multi-view는 audit/label evidence로만 남기고 model input으로 쓰지 않았다.
- Cell contrast role, cell key, rank, semantic score, geometry status, proxy label은
  label surface에서 숨겼다.

## Result

```text
status = h002_reliability_target_v5_cell_contrast_candidate_mining_ready_needs_asset_packets
selected_level = strict_predicate_subject_object_endpoint
label rows = 80
contrast pairs = 40
contrast cells = 21
packet_ready = 2
asset_needed = 78
asset_request_rows = 78
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_asset_packets
```

주요 분포:

```text
family = support_contact:48, relative_vertical:32
hidden role = positive_proxy:40, negative_proxy:40
source queue = HL:40, LH:40
geometry status = satisfied:40, unsatisfied:40
rank band = top50:2, top100_only:38, rank_101_200:20, rank_201_500:16, rank_501_1000:4
label match = no_gt_for_pair:66, pair_has_other_predicate:13, family_match:1
```

검증 결과:

```text
duplicate visible ids = 0
input validation errors = 0
label surface field leakage hits = 0
label surface value leakage hits = 0
packet path errors = 0
visible field count = 27
```

## Interpretation

v5 candidate package는 만들어졌지만, label fill을 바로 진행할 수 있는 상태는 아니다.
전체 `80` rows 중 packet-ready row가 `2`개뿐이고, `78` rows는 asset packet 생성이
필요하다. 따라서 현재 산출물은 posterior smoke를 여는 evidence가 아니라, blind label
round를 시작하기 위한 candidate/asset 준비물이다.

중요한 개선점은 visible label sheet에서 target shortcut 후보를 제거했다는 점이다. Hidden
manifest에는 cell contrast role, source queue, rank band, geometry status 등이 남아 있지만,
labeler가 보는 surface에는 노출되지 않는다. 이후 label이 채워지면 ingestion과
target-independence audit을 다시 통과해야 posterior smoke를 열 수 있다.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/selected_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/v5_label_schema.json
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_asset_packets
```

Goal:

- generate or verify asset packets for the `78` asset-needed rows.
- keep label fill blocked until asset packet coverage is sufficient.
- preserve the blind label-surface contract.
- keep posterior smoke blocked until label fill, ingestion, and target-independence audit pass.
