# H002 Reliability Target V3 Informative Anchor Plan

Date: 2026-06-20 KST

## Purpose

`148_reliability_target_v3_object_endpoint_path_decision.md`에서 선택한
`revise_v3_informative_positive_anchor_sampling` 경로를 실제 train-only sampling plan으로
구체화했다.

핵심 질문:

```text
Can we construct a new label pool where reliable positives are not dominated by
floor/wall/ceiling or trivial room/surface relations?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test row는 사용하지 않았다.
- Label fill은 하지 않았다.
- Posterior model은 학습하지 않았다.
- H001 artifact는 수정하지 않았다.
- Multi-view는 계속 audit/label evidence이며 model input이 아니다.
- Candidate proxy category는 sampling stratum일 뿐 target label이 아니다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_plan.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_plan_ready_with_asset_requests
total=286102
selected=160
packet_ready=126
asset_needed=34
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_informative_anchor_candidate_mining
```

## Result

Status:

```text
h002_reliability_target_v3_informative_anchor_plan_ready_with_asset_requests
```

Decision:

```text
Plan a new train-only informative-anchor label pool. Retain object/endpoint
controls, cap floor/wall/ceiling trivial relations, and explicitly separate
informative positives, geometry contradiction negatives, trivial room/surface
negatives, and uncertain/ontology negatives.
```

## Candidate Inventory

Full train `support_contact` / `relative_vertical` RGA rows:

| Category | Rows |
| --- | ---: |
| `informative_reliable_positive_proxy` | 87,054 |
| `geometry_contradiction_negative_proxy` | 1,828 |
| `trivial_room_surface_negative_proxy` | 180,518 |
| `uncertain_or_ontology_negative_proxy` | 16,702 |
| total | 286,102 |

Seed selection:

| Anchor Category | Requested | Selected | Available | Packet-Ready Selected | Asset-Needed Selected |
| --- | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 40 | 87,054 | 40 | 0 |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 1,828 | 40 | 0 |
| `trivial_room_surface_negative_proxy` | 40 | 40 | 180,518 | 21 | 19 |
| `uncertain_or_ontology_negative_proxy` | 40 | 40 | 16,702 | 25 | 15 |

Selected seed summary:

| Item | Count |
| --- | ---: |
| selected seed rows | 160 |
| selected packet-ready rows | 126 |
| selected asset-needed rows | 34 |
| unique scans | 94 |
| unique physical pairs | 160 |
| `support_contact` selected | 76 |
| `relative_vertical` selected | 84 |

## Interpretation

이 결과는 중요한 방향 전환을 가능하게 한다.

이전 object/endpoint-controlled label 결과에서는 geometry-supported row가 많았지만
대부분 `trivial_dense_or_room_structure`로 떨어졌다. 이번 plan은 그 실패를 직접 겨냥한다.

```text
geometry-supported row를 더 모으는 것이 아니라,
informative reliable positive가 될 가능성이 있는 row를 따로 mine한다.
```

구체적으로:

- `floor`, `wall`, `ceiling`은 제거하지 않는다. 대신 trivial negative category로 cap을 둔다.
- positive proxy는 non-room, object-level support/vertical relation을 우선한다.
- negative proxy는 geometry contradiction, trivial room/surface, uncertain/ontology를 분리한다.
- object/endpoint controls는 유지한다.
- selected 160개 중 34개는 asset packet이 필요하므로, 다음 candidate mining 단계에서
  packet request 또는 packet-ready-only fallback을 명시해야 한다.

## Sampling Contract

Target rows:

| Category | Target Rows |
| --- | ---: |
| `informative_reliable_positive_proxy` | 40 |
| `geometry_contradiction_negative_proxy` | 40 |
| `trivial_room_surface_negative_proxy` | 40 |
| `uncertain_or_ontology_negative_proxy` | 40 |

Controls:

- Per-category family cap: `24`.
- Per-scan cap: `4`.
- Per-physical-pair cap: `1`.
- `floor`, `wall`, `ceiling` are capped room-surface labels.
- `armchair`, `bed`, `bench`, `cabinet`, `chair`, `counter`, `desk`, `shelf`, `sofa`, `stool`, `table` 등은 support-surface positive bias로 사용한다.
- Hidden fields such as `anchor_category`, `p_geom_valid`, `geometry_status`, `semantic_rank`, `semantic_score`, `queue_kind`, `endpoint_flag_pattern` remain invisible to labelers.

## Posterior Gate

Posterior smoke는 계속 막는다. 다시 열려면:

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 방어 가능한 diagnostic controlled slice가 존재한다.
- `trivial_dense_or_room_structure`가 target을 단독 지배하지 않는다.
- object-label-only 및 endpoint-only probe가 target을 설명하지 않는다.
- validation/test usage는 계속 `False`다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/149_reliability_target_v3_informative_anchor_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/category_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/seed_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/selection_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/sampling_contract.json
```

## Next TODO

```text
reliability_target_v3_informative_anchor_candidate_mining
```

Goal:

- Convert the 160 seed candidates into an informative-anchor label sheet.
- Generate or request packets for the 34 asset-needed seed rows, or explicitly use a packet-ready-only fallback.
- Keep proxy categories hidden from labelers.
- Keep posterior smoke blocked until label ingestion and target-independence audit pass.
