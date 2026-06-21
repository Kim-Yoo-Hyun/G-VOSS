# H002 Reliability Target V3 Informative Anchor Target Independence Audit

Date: 2026-06-20 KST

## Purpose

`153_reliability_target_v3_informative_anchor_label_ingestion.md`에서 만든
informative-anchor v3 target이 posterior smoke로 넘어갈 수 있는지 감사했다.

핵심 질문:

```text
Did informative-anchor sampling create an independent relation reliability target,
or did it mostly encode anchor category, endpoint/object structure, and rank-band shortcuts?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training/smoke: not run.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- Hidden provenance/sampling fields are used only after label lock for audit and slice construction.
- V3 review fields, hidden buckets, audit packet paths, and multi-view evidence are not posterior inputs.
- Majority-baseline excess is reported so target imbalance is not mistaken for real signal.
- H001 artifacts: not modified.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_target_independence_audit.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_target_independence_audit_blocked
rel=82/35/47
rel_status=blocked_no_controlled_slice
geom=85/72/13
geom_status=blocked_positive_sparse
use=85/37/48
use_status=blocked_no_controlled_slice
errors=0
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_informative_anchor_path_decision
```

## Result

Status:

```text
h002_reliability_target_v3_informative_anchor_target_independence_audit_blocked
```

Decision:

```text
No posterior-ready main reliability target exists.
```

## Per-Target Decisions

| Target | Rows | Positive | Negative | Status | Strict Slice | Diagnostic Slice |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `relation_reliability_v3_binary_target` | 82 | 35 | 47 | `blocked_no_controlled_slice` | none | none |
| `geometry_support_v3_binary_target` | 85 | 72 | 13 | `blocked_positive_sparse` | none | none |
| `relation_usefulness_v3_binary_target` | 85 | 37 | 48 | `blocked_no_controlled_slice` | none | none |

## Main Reliability Target Risks

| Risk Mode | Key | Majority Baseline | Majority Acc | Excess | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| anchor_sampling | `anchor_category_hidden` | 0.5732 | 0.9634 | 0.3902 | 0.8083 | 0.9688 |
| endpoint_object_structure | `subject_object_family_cell_hidden` | 0.5732 | 1.0000 | 0.4268 | 1.0000 | 1.0000 |
| endpoint_object_structure | `endpoint_flag_pattern_hidden` | 0.5732 | 0.9756 | 0.4024 | 0.8878 | 1.0000 |
| endpoint_object_structure | `object_family_cell_hidden` | 0.5732 | 0.9512 | 0.3780 | 0.8559 | 1.0000 |
| visible_object_identity | `object_label` | 0.5732 | 0.9512 | 0.3780 | 0.8559 | 1.0000 |
| visible_object_identity | `subject_label` | 0.5732 | 0.9146 | 0.3415 | 0.7937 | 1.0000 |
| construction | `rank_band_hidden` | 0.5732 | 0.7927 | 0.2195 | 0.4393 | 1.0000 |
| expected_geometry_alignment | `geometry_status_hidden` | 0.5732 | 0.7927 | 0.2195 | 0.3603 | 0.6488 |

## Controlled Slice Check

Representative `relation_reliability_v3_binary_target` slices:

| Slice | Rows | Positive | Negative | Positive Sparse | Anchor Risk | Endpoint/Object Risk | Construction Risk | Object Risk | Strict | Diagnostic |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| `original_informative_anchor_v3` | 82 | 35 | 47 | `False` | 2 | 4 | 3 | 2 | `False` | `False` |
| `family_balanced_v3` | 64 | 32 | 32 | `False` | 2 | 4 | 3 | 2 | `False` | `False` |
| `predicate_balanced_v3` | 56 | 28 | 28 | `False` | 2 | 4 | 3 | 2 | `False` | `False` |
| `rank_band_balanced_v3` | 34 | 17 | 17 | `True` | 2 | 4 | 0 | 2 | `False` | `False` |
| `geometry_status_balanced_v3` | 34 | 17 | 17 | `True` | 2 | 4 | 1 | 2 | `False` | `False` |
| `anchor_category_balanced_v3` | 6 | 3 | 3 | `True` | 0 | 4 | 1 | 2 | `False` | `False` |
| `endpoint_pattern_balanced_v3` | 4 | 2 | 2 | `True` | 2 | 2 | 3 | 2 | `False` | `False` |

## Interpretation

Informative-anchor sampling solved one earlier failure but exposed a deeper one.

- It fixed the most obvious positive-sparsity problem for the main reliability target:
  `35` positive / `47` negative is usable mass.
- However, the target is still not independent enough for posterior smoke.
  Anchor category, endpoint/object structure, object labels, and rank band explain the
  label too strongly.
- Family-balanced and predicate-balanced slices preserve enough rows, but they still
  carry the same anchor/object/endpoint risks.
- Anchor/category or endpoint-matched slices remove one shortcut but collapse to very
  small balanced sets, so they are positive-sparse again.
- `geometry_support` remains useful as an RGA evidence axis, but it is not a usable
  main reliability target here because it is `72` positive / `13` negative.

This means the current blocker is still target construction, not posterior capacity or
combiner architecture.

## Next Path Options

The next TODO is a path decision, not posterior smoke.

| Option | Verdict | Reason |
| --- | --- | --- |
| posterior smoke now | reject | no strict/diagnostic controlled reliability slice |
| use geometry support as main target | reject | collapses reliability into geometry validity and is positive-heavy |
| accept full informative-anchor target | reject | target can be explained by anchor/object/endpoint shortcuts |
| create a narrower controlled slice | plausible but row-limited | anchor/endpoint matching collapses to tiny sets |
| revise sampling around repeated object-pair families | plausible | may reduce object/endpoint identity shortcuts |
| keep H002 as RGA diagnostic/decomposition only | fallback | if independent target remains unavailable |

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/154_reliability_target_v3_informative_anchor_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_informative_anchor_path_decision
```

Goal:

- Decide whether to resample, narrow to a controlled diagnostic slice, redesign the target, or stop the posterior path.
- Do not use validation/test.
- Do not add multi-view as posterior input yet.
- Do not run posterior smoke until an independent reliability target exists.
