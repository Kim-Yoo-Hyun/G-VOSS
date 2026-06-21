# H002 Reliability Target V4 Matched Contrast Asset Packet Gap Audit

Date: 2026-06-20 KST

## Purpose

`reliability_target_v4_matched_contrast_asset_packet_gap_audit`은 v4 asset packet generation에서
남은 20개 partial packet row를 label fill 전에 감사하는 단계다.

핵심 질문:

```text
Which partial packet rows can still be labeled under a limited-view caveat,
and which matched pairs must be excluded or replaced before label fill?
```

## Boundary

- Split: train-only
- Validation/test usage: none
- Label fill: not performed
- Posterior training/smoke: not performed
- Multi-view and mesh packets: audit/label evidence only, not posterior input
- Pair integrity rule: 한 row가 replacement-needed이면 matched pair 전체를 label fill에서 제외한다
- H001 artifacts: not modified

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packet_gap_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packet_gap_audit.py
```

Observed:

```text
status=h002_reliability_target_v4_matched_contrast_asset_packet_gap_audit_ready_for_label_readiness
rows=160
label_ready_rows=158
label_ready_pairs=79
excluded_pairs=1
limited_view=19
path_errors=0
leakage=0
validation_used=False
next=reliability_target_v4_matched_contrast_label_readiness
```

## Decision Policy

| Condition | Row Decision |
| --- | --- |
| complete packet | `label_ready` |
| one endpoint crop missing, mesh packet ready, contact/context sheet ready | `limited_view_evaluable` |
| one endpoint crop missing, relative-vertical family, mesh packet ready | `limited_view_evaluable` |
| both endpoint crops missing | `replacement_needed` |
| missing endpoint has generic label such as `object` | `replacement_needed` |
| otherwise insufficient packet evidence | `replacement_needed` |

Pair-level rule:

| Pair Condition | Pair Decision |
| --- | --- |
| both rows complete | `pair_ready` |
| at least one row is `limited_view_evaluable`, no replacement-needed row | `pair_ready_with_limited_view_caveat` |
| any row is `replacement_needed` | `exclude_pair_before_label_fill` |

## Result

```text
input rows = 160
input pairs = 80
label-ready rows = 158
label-ready pairs = 79
excluded rows = 2
excluded pairs = 1
limited-view rows kept = 19
replacement-needed rows = 1
output path errors = 0
visible leakage hits = 0
input validation errors = 0
```

Row decision counts:

| Decision | Rows |
| --- | ---: |
| `label_ready` | 140 |
| `limited_view_evaluable` | 19 |
| `replacement_needed` | 1 |

Pair decision counts:

| Decision | Pairs |
| --- | ---: |
| `pair_ready` | 60 |
| `pair_ready_with_limited_view_caveat` | 19 |
| `exclude_pair_before_label_fill` | 1 |

Label-ready role balance:

| Role | Rows |
| --- | ---: |
| `positive_proxy` | 79 |
| `negative_proxy` | 79 |

Label-ready family balance:

| Family | Rows |
| --- | ---: |
| `support_contact` | 90 |
| `relative_vertical` | 68 |

Excluded pair:

```text
v4pair_0042
```

Reason:

```text
one relative_vertical row had a missing endpoint crop for a generic `object` label,
so endpoint identity cannot be independently checked.
```

## Interpretation

- The packet gap no longer blocks v4 label preparation.
- 19/20 partial rows can be kept as `limited_view_evaluable` because mesh packet and
  contact/context evidence are available.
- 1 partial row is not acceptable because the missing endpoint has the generic label `object`.
- Because v4 matched contrast depends on pair integrity, the whole pair `v4pair_0042` is
  excluded before label fill.
- The resulting label-ready slice has `79` matched pairs and preserves role balance:
  `79` positive proxy rows and `79` negative proxy rows.
- Label fill still has not started. The next step is label-readiness validation over the
  158-row / 79-pair sheet.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/159_reliability_target_v4_matched_contrast_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/row_gap_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/partial_row_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/pair_gap_decisions.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/label_ready_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/label_ready_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/excluded_pair_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/excluded_pair_ids.txt
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/replacement_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/output_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/visible_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/packets/
```

## Next TODO

```text
reliability_target_v4_matched_contrast_label_readiness
```
