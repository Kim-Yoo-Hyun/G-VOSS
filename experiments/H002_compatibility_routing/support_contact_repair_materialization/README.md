# Support/Contact Repair Materialization

This folder stores repaired support/contact materialization outputs for H002.

## Role

The materialization tests whether `standing on` / `lying on` can provide a
shortcut-controlled binary target after the support/contact repair decision.

## Current Output

```text
latest/
```

Key files:

| File | Role |
| --- | --- |
| `row_manifest.json` | status, counts, gate decision, and next TODO |
| `schema_precheck.json` | blocked-field, label-balance, and capacity checks |
| `validation_errors.jsonl` | empty when schema/materialization validation passes |
| `gate_failures.jsonl` | scientific gate failures such as insufficient binary capacity |
| `model_safe_binary_no_class.jsonl` | strict binary `T_e + G_e` view without class labels |
| `model_safe_binary_with_class_semantic.jsonl` | binary semantic-content view with class labels |
| `model_safe_binary_geometry_only.jsonl` | binary geometry-only control view |
| `model_safe_selective_no_class.jsonl` | full selective view with abstain diagnostics |
| `hidden_manifest.jsonl` | hidden class/source/provenance fields |
| `group_manifest.jsonl` | object-pair group decisions |
| `class_pair_quota.csv` | mixed class-pair capacity table |
| `pose_proxy_diagnostics.csv` | support/upright/lying proxy diagnostics |

## Boundary

The current materialization is valid but not metric-ready. Mixed-class-pair
control leaves only 40 binary rows over four class-pairs, so the next step is a
capacity decision rather than a metric rerun.
