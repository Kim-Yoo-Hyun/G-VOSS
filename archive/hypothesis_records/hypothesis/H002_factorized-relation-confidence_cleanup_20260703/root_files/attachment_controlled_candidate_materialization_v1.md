# H002 Attachment Controlled Candidate Materialization V1

Date: 2026-06-25 KST

## Purpose

`attachment_controlled_expansion_plan_v1`에서 선택한 v20 `400`-row endpoint-balanced preview를
현재 H002 compatibility-learning schema로 재패키징한다.

핵심은 attachment predicate 자체가 H001 verifier에서는 `unsupported_family`라 raw geometry가
null이라는 점을 처리하는 것이다. 따라서 같은 directed object pair에서 `support_contact` 또는
`relative_vertical` raw geometry를 가져와 predicate-independent `G_e`로 조인한다.

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_controlled_candidate_materialization_v1.py
```

Output:

```text
artifacts/attachment_controlled_candidates_v1/
```

## Result

```text
status = h002_attachment_controlled_candidate_materialization_v1_ready
rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
numeric_g_rows = 400
selected_prediction_matches = 400
pair_geometry_matches = 400
groups = 131
validation_errors = 0
```

Predicate counts:

```text
attached to = 160
hanging on = 160
connected to = 80
```

Compatibility counts:

```text
attached to: positive 80 / counterfactual_negative 80
hanging on: positive 80 / counterfactual_negative 80
connected to: unknown 80
```

Connected diagnostic counts:

```text
D1_connected_near_or_overlap_diagnostic = 40
D2_connected_far_or_functional_ambiguous_diagnostic = 40
```

## Geometry Join

Join strategy:

```text
selected prediction_id -> selected semantic/source/rank row
selected directed_pair_id -> support_contact or relative_vertical raw geometry row
```

Observed join summary:

```text
selected_prediction_matches = 400 / 400
pair_geometry_matches = 400 / 400
raw_pair_geometry_joined_rows = 400 / 400
raw_geometry_source_counts = support_contact: 400
```

The materializer uses `rg` to cache only rows matching the selected `prediction_id` or
`directed_pair_id` patterns before parsing. The cache is:

```text
artifacts/attachment_controlled_candidates_v1/matched_source_rows.jsonl
```

This cache is an intermediate artifact, not model input.

## Emitted Files

```text
candidate_rows.jsonl
compatibility_rows.jsonl
diagnostic_connected_rows.jsonl
counterfactual_groups.jsonl
baseline_view.jsonl
audit_view.jsonl
schema.json
summary.json
validation_errors.jsonl
report.md
```

## Field Boundary

Model input:

```text
T_e = predicate/object semantic content
Z_e = source confidence/rank
G_e = predicate-independent numeric pair geometry
Q_e = raw geometry availability and uncertainty/observability cues
```

Compatibility input:

```text
compatibility_main = T_e + G_e
```

`Z_e` is not included in `compatibility_main`.

Hidden/control-only fields:

```text
cell_id_hidden
proxy_role_hidden
provisional_status_hidden
capacity_evidence_tier_hidden
selection_route_level_hidden
visible_endpoint_pair_hidden
source_geometry_status_hidden
```

These are used for shortcut probes and audits only.

## Boundary

- train-only hypothesis artifact;
- no validation/test usage;
- no paper model training;
- no H001 artifact modification;
- `connected to` remains diagnostic rather than primary binary compatibility.

## Next TODO

```text
attachment_controlled_candidate_smoke_v1
```

