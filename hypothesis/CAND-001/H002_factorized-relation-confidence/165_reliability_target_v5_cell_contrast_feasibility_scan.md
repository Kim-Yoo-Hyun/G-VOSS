# Reliability Target V5 Cell Contrast Feasibility Scan

2026-06-21 KST에 `reliability_target_v5_cell_contrast_feasibility_scan` TODO를
진행했다. 이 단계는 v4에서 드러난 subject/object-family shortcut을 줄일 수 있는지,
새 label round 전에 full train-only pool에서 capacity만 확인하는 gate다. Label fill,
posterior smoke, validation/test 사용은 하지 않았다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Labels: not filled.
- Posterior model: not trained.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence, not posterior input.
- Cell contrast roles are sampling proxies only, not target labels.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_feasibility_scan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_feasibility_scan.py
```

Observed:

```text
status=h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining
selected_level=strict_predicate_subject_object_endpoint
rows=80
pairs=40
cells=21
max_cell_share=0.0500
packet_ready=2
asset_needed=78
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v5_cell_contrast_candidate_mining
```

## Result

Status:

```text
h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining
```

Selected matching level:

```text
strict_predicate_subject_object_endpoint
```

Selected keys:

```text
predicate_label
subject_label_norm
object_label_norm
endpoint_flag_pattern_hidden
```

## Why This Matters

v4의 blocker는 class imbalance가 아니었다. v4는 relation reliability target을 `23/24`로
균형 있게 만들었지만, exact subject/object-family control이 불가능했다.

v5 scan은 다음 질문에 답한다.

```text
same predicate + subject/object label + endpoint pattern 안에서
reliable-like와 unreliable-like 후보를 둘 다 찾을 수 있는가?
```

결과는 가능하다는 쪽이다. strict level에서도:

- eligible groups: `137`
- balanced pair capacity: `167`
- positive proxy capacity: `2164`
- negative proxy capacity: `170`
- distinct subject-object-family cells: `137`
- support/vertical both represented

즉, v4에서 label 후 `subject_object_family_cell_balanced_v4 = 0 rows`였던 문제는
full train pool의 capacity 부족 때문만은 아니다. 더 엄격한 cell-level sampling으로 label sheet를
다시 만들 여지가 있다.

## Matching Level Inventory

| Matching Level | Eligible Groups | Pair Capacity | Positive Capacity | Negative Capacity | Geometry Neg | Trivial Neg | Meets Minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `strict_predicate_subject_object_endpoint` | 137 | 167 | 2164 | 170 | 170 | 0 | true |
| `family_subject_object_endpoint` | 219 | 270 | 8733 | 271 | 271 | 0 | true |
| `subject_object_family_cell` | 219 | 270 | 8733 | 271 | 271 | 0 | true |
| `object_family_with_endpoint` | 138 | 316 | 59895 | 316 | 316 | 0 | true |
| `object_family_cell` | 303 | 64017 | 87043 | 76369 | 526 | 75843 | true |
| `endpoint_family_cell` | 6 | 319 | 87054 | 319 | 319 | 0 | true |

Interpretation:

- `strict_predicate_subject_object_endpoint`가 가장 방어 가능한 level이다.
- 더 broad한 `object_family_cell`은 capacity는 크지만 object/family shortcut을 다시 키울 위험이 있다.
- 따라서 다음 label round는 broad fallback이 아니라 strict level에서 시작해야 한다.

## Selected Preview

Preview selection:

| Item | Count |
| --- | ---: |
| selected rows | 80 |
| selected pairs | 40 |
| selected mixed cells | 21 |
| max single-cell rows | 4 |
| max single-cell share | 0.0500 |
| packet-ready rows | 2 |
| asset-needed rows | 78 |
| unique scans | 67 |
| unique physical pairs | 80 |

Family balance:

| Family | Rows |
| --- | ---: |
| `support_contact` | 48 |
| `relative_vertical` | 32 |

Role balance:

| Role | Rows |
| --- | ---: |
| `positive_proxy` | 40 |
| `negative_proxy` | 40 |

Rank-band distribution:

| Rank Band | Rows |
| --- | ---: |
| `top50` | 2 |
| `top100_only` | 38 |
| `rank_101_200` | 20 |
| `rank_201_500` | 16 |
| `rank_501_1000` | 4 |

## Feasibility Gates

| Gate | Result |
| --- | --- |
| minimum capacity | true |
| recommended capacity | true |
| minimum mixed cells | true |
| selected preview target rows | true |
| selected preview target pairs | true |
| selected preview minimum cells | true |
| single-cell share <= 0.20 | true |
| both families represented | true |
| asset path explicit | true |

## Caveat

Feasibility는 통과했지만, packet coverage는 낮다.

```text
packet_ready = 2 / 80
asset_needed = 78 / 80
```

따라서 다음 단계는 posterior가 아니라 `reliability_target_v5_cell_contrast_candidate_mining`이다.
그 단계에서 selected rows를 label sheet로 만들고, asset packet generation/readiness path를 명시해야 한다.

## Interpretation

이번 결과는 H002를 계속 진행할 근거를 준다.

- v4의 실패 원인은 “relation reliability idea가 불가능하다”가 아니라 “v4 label construction이 exact object-cell control을 만들지 못했다”에 더 가깝다.
- full train-only pool에는 strict cell contrast capacity가 존재한다.
- 단, proxy role은 label이 아니므로 v5 label fill 이후 target-independence audit을 다시 통과해야 한다.
- posterior smoke는 여전히 blocked다.

## Next TODO

```text
reliability_target_v5_cell_contrast_candidate_mining
```

Goal:

- strict predicate+subject/object+endpoint cell 기준으로 candidate sheet를 만든다.
- cell contrast roles는 hidden sampling proxy로 유지한다.
- label surface에는 semantic rank, geometry status, p_geom_valid, source queue, hidden cell metadata를 노출하지 않는다.
- asset-needed `78` rows에 대한 packet generation/readiness path를 준비한다.
- posterior smoke는 label fill, ingestion, target-independence audit 전까지 계속 막는다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/165_reliability_target_v5_cell_contrast_feasibility_scan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_feasibility_scan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/matching_level_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/selected_cell_preview.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/seed_preview_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/asset_request_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/feasibility_contract.json
```
