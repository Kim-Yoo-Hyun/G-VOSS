# p_obs / p_rel Materialization

## Role

This folder owns the runtime materialization for the H002 selective-decision
extension:

```text
p_obs = can this edge be judged with available evidence?
p_rel = is this edge reliable when observable?
```

It creates separate model-safe views for `Q_e` and `p_rel` so observability
features do not get mixed with hidden labels or construction fields.

## Current Output

```text
latest/model_safe_qe_view.jsonl
latest/model_safe_prel_view.jsonl
latest/hidden_selective_labels.jsonl
latest/materialization_manifest.json
latest/validation_errors.jsonl
```

## Boundary

The missing-evidence rows are stress-test controls derived from existing
official-validation rows. They are not independent human observability labels.
Use this output to test the selective-decision mechanics before promoting any
paper-level p_obs / p_rel claim.
