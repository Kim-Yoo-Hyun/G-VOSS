# Compatibility Dataset V3 Independent Validity Support Contact Balancing Candidate Materialization

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```

## Purpose

이 단계는 support/contact를 `88`-row diagnostic slice가 아니라 primary independent-validity
family로 만들기 위해, 직전 balancing plan에서 선택한 `1200`-row predicate-balanced target을
실제로 materialize한다.

## Materialized Dataset

```text
candidate_rows = 1200
model_safe_view = 1200
hidden_manifest = 1200
smoke_ready_view = 1200
validation_errors = 0
```

Label balance:

```text
positive rows = 600
negative rows = 600

lying on = 600 rows
  positive = 300
  negative = 300

standing on = 600 rows
  positive = 300
  negative = 300
```

Candidate pool before sampling:

```text
scanned rows = 4,818,996
selected support/contact family rows = 370,692
primary candidate rows = 8,631

lying on positive = 1,643
lying on negative = 685
standing on positive = 5,921
standing on negative = 382
```

## Cap Audit

The materializer used predicate-level balancing with class-pair, scan, directed-pair, and rank-band
caps.

```text
max single scan share = 0.0108  <= 0.05
max single directed-pair share = 0.0017 <= 0.01
max single class-pair share = 0.0167 <= 0.10
max single rank-band share = 0.4017 <= 0.55
```

All cap checks passed without cap relaxation.

## Schema Precheck

Passed:

- row ids are unique;
- all rows are train split;
- primary row count is `1200`;
- global label balance is `600 / 600`;
- predicate-internal label balance is `300 / 300` for both `lying on` and `standing on`;
- model-safe view contains zero forbidden construction keys;
- feature blocks contain zero forbidden construction keys.

Blocked model-input fields remain hidden-only:

```text
geometry_status
p_geom_valid
consistency_score
geometry_residual_proxy
label_match_status
matched_gt_ids
matched_predicates
target_pool
selection_pass
hidden provenance
```

## Interpretation

This fixes the immediate support/contact quantity blocker. The exact predicate-class constraint was
too strict for support/contact, but a predicate-balanced GT-anchored target can be materialized while
keeping distribution caps under control.

This is still not learned evidence. Because the balance unit was relaxed, the next step must audit
whether `predicate_label`, object class pair, rank band, source score, or geometry feature shortcuts
can predict the target before any learned smoke.

## Boundary

Allowed now:

- train-only support/contact-primary independent-validity candidate artifact;
- schema shortcut audit preparation;
- future learned-smoke input after audit passes.

Blocked:

- calibrated `p_rel` / `p_obs`;
- learned smoke before schema shortcut audit;
- paper-level H002 result;
- held-out performance;
- all-family relation reliability.

## Next

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```
