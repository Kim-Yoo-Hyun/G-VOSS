# Additional Relation-Family Sweep Plan After Coverage Review

## Status

```text
status = h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready
selected_path = plan_schema_first_family_sweep_with_predicate_level_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan
```

This step does not run a learned model. It freezes the next schema-first sweep plan
after the route-coverage review concluded that the current H002 evidence is not
sufficient for promotion planning.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review.py
```

## Artifact Root

```text
artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review/
```

Key outputs:

- `summary.json`
- `family_sweep_plan.csv`
- `predicate_fallback_policy.csv`
- `predicate_probe_queue.csv`
- `execution_gates.csv`
- `next_execution_queue.csv`
- `predicate_gap_snapshot.csv`
- `report.md`
- `validation_errors.jsonl`

## Counts

```text
family_sweep_rows = 5
predicate_fallback_policy_rows = 24
predicate_probe_rows = 20
execution_gate_rows = 5
predicate_gap_rows = 29
```

## Selected Sweep Order

```text
1. relative_horizontal
   - left / right / front / behind / in front of
   - next: compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan

2. containment_in
   - standing in / lying in / hanging in / inside
   - next: compatibility_dataset_v3_containment_schema_capacity_plan

3. attachment_deferred
   - attached to / hanging on / connected to / mounted on
   - next: compatibility_dataset_v3_attachment_visual_mesh_qe_protocol_plan

4. part_structural
   - build in / leaning against / belonging to / part of / cover
   - next: compatibility_dataset_v3_part_structural_boundary_scan_plan

5. identity_symmetry
   - same as / same symmetry as
   - next: compatibility_dataset_v3_identity_symmetry_exclusion_audit_plan
```

## Predicate-Level Fallback Rule

The user rule is now encoded as a formal fallback policy:

```text
If a multi-predicate family fails at family level, observe and decide each relation
type separately.
```

Meaning:

- Do not discard a whole relation family just because its aggregate family-level
  target fails.
- If a family contains several predicates, run predicate-level schema, capacity,
  and shortcut probes before freezing the family as diagnostic or deferred.
- Successful predicates may become predicate-level evidence.
- Failed sibling predicates should be reported as diagnostic, deferred, or
  out-of-scope rather than averaged into a solved-family claim.

This policy is important for support/contact-like families: `standing on`,
`lying on`, and `supported by` can have different evidence requirements even when
their family-level aggregate looks weak.

## Boundary

```text
split = train_only_sweep_plan
trains_new_model = false
runs_new_learned_smoke = false
validation_usage = false
test_usage = false
paper_evidence_allowed = false
h001_artifacts_modified = false
all_family_model_training_allowed = false
```

## Interpretation

The current decision is not to train one all-family model. The next move is to
define relation-family evidence routes first, starting with relative-horizontal
reference-frame semantics. After each family-level probe, the fallback policy
requires predicate-level inspection when the family aggregate is ambiguous or
fails.
