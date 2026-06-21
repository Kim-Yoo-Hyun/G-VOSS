# H002 Reliability Target V4 Matched Contrast Plan

Date: 2026-06-20 KST

## Purpose

`155_reliability_target_v3_informative_anchor_path_decision.md`에서 선택한
`matched_contrast_reliability_target_v4` 방향을 실제 train-only queue에서 계획 가능할지
확인했다.

핵심 질문:

```text
Can we construct positive and negative reliability candidates inside matched
predicate / endpoint-object / rank strata, rather than using separate anchor buckets?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Labels: not filled.
- Posterior model: not trained.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence, not posterior input.
- Contrast roles are sampling proxies only, not target labels.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_plan.py
```

Observed:

```text
status=h002_reliability_target_v4_matched_contrast_plan_ready_with_asset_requests
selected_level=predicate_object_rank_controlled
rows=160
pairs=80
packet_ready=5
asset_needed=155
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v4_matched_contrast_candidate_mining
```

## Result

Status:

```text
h002_reliability_target_v4_matched_contrast_plan_ready_with_asset_requests
```

Selected matching level:

```text
predicate_object_rank_controlled
```

Selected keys:

```text
predicate_label
endpoint_flag_pattern_hidden
object_family_cell_hidden
```

Rank policy:

```text
post_selection_quota_and_audit_control
```

## Matching Level Inventory

| Matching Level | Rank Exact | Eligible Groups | Pair Capacity | Verdict |
| --- | --- | ---: | ---: | --- |
| `strict_predicate_object_rank` | `True` | 0 | 0 | infeasible |
| `family_object_rank` | `True` | 0 | 0 | infeasible |
| `family_endpoint_rank` | `True` | 0 | 0 | infeasible |
| `predicate_object_rank_controlled` | `False` | 114 | 275 | selected |
| `family_object_rank_controlled` | `False` | 138 | 316 | feasible fallback |
| `family_endpoint_rank_controlled` | `False` | 6 | 319 | broad fallback |

## Interpretation

Exact rank-band matching is too strict for the current Open3DSG train queue.
When `rank_band_hidden` is included as an exact matching key, there is no usable
contrast capacity.

This does not mean v4 is impossible. It means rank must be handled differently:

```text
match predicate + endpoint/object structure exactly,
then control rank by quota and post-label shortcut audit.
```

This is still a meaningful improvement over v3 because v3 used separate
positive-like and negative-like anchor buckets. v4 will compare candidate
positive and candidate negative rows inside the same predicate/object endpoint
stratum.

## Preview Selection

| Item | Count |
| --- | ---: |
| selected rows | 160 |
| selected contrast pairs | 80 |
| positive proxy rows | 80 |
| negative proxy rows | 80 |
| unique scans | 136 |
| unique physical pairs | 158 |
| packet-ready rows | 5 |
| asset-needed rows | 155 |
| `support_contact` rows | 90 |
| `relative_vertical` rows | 70 |

Rank-band distribution in the preview:

| Rank Band | Rows |
| --- | ---: |
| `top50` | 5 |
| `top100_only` | 75 |
| `rank_101_200` | 38 |
| `rank_201_500` | 29 |
| `rank_501_1000` | 13 |

## Risk And Caveat

The plan is feasible, but packet coverage is poor:

```text
packet_ready = 5 / 160
asset_needed = 155 / 160
```

Therefore the next candidate mining stage must either:

- generate asset packets for the selected v4 rows, or
- explicitly choose a much smaller packet-ready-only fallback with a coverage caveat.

The preferred path is to generate asset packets because packet-ready-only would likely
reintroduce a coverage/source shortcut.

## Posterior Reopen Gate

Posterior smoke remains blocked until all conditions hold:

- relation reliability binary target has at least `20` positive and `20` negative rows.
- strict or explicitly defensible diagnostic controlled slice exists.
- anchor/category shortcut risk is zero on the selected slice.
- endpoint/object and visible object-label shortcuts are not sufficient to explain the target.
- rank-band and geometry-status controls do not dominate the selected slice.
- validation/test usage remains `False`.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/156_reliability_target_v4_matched_contrast_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/matching_level_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/selected_strata_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/selected_strata_preview.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/seed_preview_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/asset_request_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/sampling_contract.json
```

## Next TODO

```text
reliability_target_v4_matched_contrast_candidate_mining
```

Goal:

- turn the v4 plan into a label/candidate sheet.
- keep contrast roles hidden from the label surface.
- prepare asset packet requests for the 155 asset-needed rows.
- keep posterior smoke blocked.
