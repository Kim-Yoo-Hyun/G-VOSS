# V62 Attachment Endpoint-Balanced Audit Packet Label Ingestion

## Purpose

v61에서 잠근 user-filled visible packet labels를 hidden materialized manifest와 사후
join해 target artifacts와 GT/reliability mismatch analysis axis를 만든다.

이 단계에서 hidden manifest는 label lock 이후에만 읽는다. Hidden fields와 existing
GT-match axis는 target construction, provenance, shortcut audit, mismatch analysis 용도이며
model input이 아니다.

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_positive_sparse_with_probe_risk
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit
rows = 320
validation_errors = 0
posterior_smoke_allowed = false
```

Target artifacts:

```text
multiclass_rows = 320
primary_binary_rows = 207
connected_diagnostic_rows = 64
geometry_support_rows = 219
endpoint_identity_rows = 320
coverage_rows = 320
uncertainty_rows = 320
abstain_rows = 113
```

Primary relation reliability target:

```text
positive = 25
negative = 182
minimum_per_class_for_posterior = 60
class_mass_pass = false
```

Existing GT relation match auxiliary axis:

```text
exact_match = 1
family_match = 5
pair_has_other_predicate = 81
no_gt_for_pair = 233
```

GT/reliability mismatch table:

```text
GT match & reliability accept = 0
GT match & reliability reject = 1
GT match & abstain = 5
No GT/current relation & reliability accept = 25
No GT/current relation & reliability reject = 181
No GT/current relation & abstain = 108
```

Shortcut diagnostics:

```text
quick_probe_risk_flags = 70
same_scan_mixed_primary_binary_groups = 3
same_visible_pair_mixed_primary_binary_groups = 0
same_predicate_mixed_primary_binary_groups = 2
same_evidence_tier_mixed_primary_binary_groups = 2
```

## Interpretation

The ingestion step is valid, but the target is not posterior-ready. The primary
binary target is strongly positive-sparse (`25/182`) and quick probes flag many
shortcut risks. This means the next step must be target-independence audit, not
posterior smoke or stronger combiner experiments.

The GT/reliability table is still useful. It shows the required auxiliary axis is
now connected to the human-audited reliability labels:

- `No GT/current relation & reliability accept = 25` supports the annotation
  sparsity / under-annotated reliable-relation analysis path.
- `GT match & reliability reject = 1` is a potential GT-vs-visible-evidence
  conflict case.
- Most rows remain no-GT reject or abstain, so this target remains conservative.

## Boundary

- Train-only H002 hypothesis artifact.
- Existing GT-match axis was joined only after label lock.
- Hidden fields are not model inputs.
- No validation/test rows used.
- No posterior trained or evaluated.
- Multi-view/mesh remains audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit
```
