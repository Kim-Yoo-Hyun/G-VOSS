# H002 Schema

Last updated: 2026-06-11

## Purpose

이 문서는 H002의 `RGA(Relation-Geometric Agreement)` contract를 실제
identity-preserving edge row schema로 내리는 초안이다. 목표는 H001
full-validation artifacts를 수정하지 않고, `VL-SAT`와 Open3DSG recovery branch의
prediction/geometry/failure rows를 H002 diagnostic row로 projection할 수 있는지
확인하는 것이다.

이 단계는 schema contract다. 새 metric 결과를 생성하지 않았고, paper experiment
evidence로 승격하지 않는다.

## Input Inventory

Primary source artifacts:

| Source | Prediction rows | Geometry rows | Failure rows | GT rows | Primary paths |
| --- | ---: | ---: | ---: | ---: | --- |
| `VL-SAT` full validation | 957,008 | 957,008 | 59,841 | 11,254 | `experiments/H001_geom_reliability/sources/vlsat/full_validation/` |
| Open3DSG recovery | 695,916 | 695,916 | 82,155 | use source/metric joins | `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/` |

Available files:

- `adapter/predictions.jsonl`: identity, predicate, source scores, source ranks.
- `geometry/verification.jsonl`: geometry features, verifier status,
  `p_geom_valid`, selected policy, provenance.
- `failure_rows/rows.jsonl`: top-K/failure-oriented rows with GT match status,
  top-K membership, rerank effect, taxonomy.
- `adapter/ground_truth.jsonl`: GT rows for `VL-SAT` full-validation scope.
- `metrics/metrics.json`: H001 condition-level metrics; not enough by itself
  for H002 row projection.

Source count facts:

- `VL-SAT` geometry status totals: satisfied 89,116, uncertain 100,476,
  violated 31,256, unsupported 736,160.
- Open3DSG recovery geometry status totals: satisfied 68,054, uncertain 70,520,
  violated 22,022, unsupported 535,320.
- `VL-SAT` failure-row GT match status totals: exact_match 3,850, family_match
  2,843, no_gt_for_pair 38,525, pair_has_other_predicate 14,623.
- Open3DSG recovery failure-row GT match status totals: exact_match 2,665,
  family_match 2,739, no_gt_for_pair 60,485, pair_has_other_predicate 16,266.

## Schema Version

Initial schema id:

```text
h002_rga_edge_v0
```

This schema is intentionally a projection schema. It must preserve H001 source
row identity and provenance, and it must not rewrite or overwrite H001 artifacts.

## Row Contract

Each H002 row represents one source prediction edge.

```text
{
  schema_version: "h002_rga_edge_v0",
  record_type: "h002_rga_edge",

  source: SourceBlock,
  identity: IdentityBlock,
  edge: EdgeBlock,
  predicate: PredicateBlock,
  semantic: SemanticBlock,
  geometry: GeometryBlock,
  label: LabelBlock,
  rga: RGABlock,
  posterior: PosteriorBlock,
  provenance: ProvenanceBlock
}
```

## Source Block

```text
source = {
  source_id: string,
  baseline_name: string,
  baseline_run_id: string,
  split_name: string,
  scope_id: string,
  source_schema_version: string
}
```

Mapping:

- `source_id`: derived from artifact root, e.g. `vlsat` or
  `open3dsg_recovery_relaxed_views_min2`.
- `baseline_name`: from prediction/verification row.
- `baseline_run_id`: from prediction/verification row.
- `split_name`: from prediction/verification row.
- `scope_id`: fixed H002 string for the branch, e.g.
  `full_official_validation`.
- `source_schema_version`: H001 input row schema, e.g. `h001_prediction_v1`.

## Identity Block

```text
identity = {
  prediction_id: string,
  scan_id: string,
  subgraph_id: string,
  subject_id: int,
  object_id: int,
  directed_pair_id: string,
  row_key: string
}
```

Rules:

- `prediction_id` is the primary join key between `predictions.jsonl` and
  `verification.jsonl`.
- `directed_pair_id` is derived as
  `{scan_id}:{subgraph_id}:{subject_id}:{object_id}`.
- `row_key` is derived as
  `{prediction_id}` for source prediction rows.
- H002 must fail projection if `prediction_id`, `scan_id`, `subgraph_id`,
  `subject_id`, or `object_id` is missing.

## Edge Block

```text
edge = {
  subject_label: string,
  object_label: string,
  subject_node_index: int | null,
  object_node_index: int | null,
  edge_index: int | null,
  edge_source: string | null
}
```

Mapping:

- `subject_*` and `object_*` fields come from H001 `edge`.
- Node indices may be unavailable across sources and must remain nullable.

## Predicate Block

```text
predicate = {
  predicate_label: string,
  predicate_family: string,
  predicate_vocab: string,
  raw_3dssg_predicate_id: int | null,
  source_predicate_index: int | null
}
```

Mapping:

- Use H001 `predicate.predicate_label`.
- Use H001 `predicate.predicate_family`.
- `source_predicate_index` maps from `vlsat_predicate_index` or
  `open3dsg_predicate_index` when available.

Supported H002 geometry families in the current H001 artifacts:

- `support_contact`
- `proximity`
- `relative_vertical`

Unsupported or future families in current artifacts:

- `attachment_deferred` in the full-validation H001 branch used here.
- `relative_horizontal`
- `unsupported_first_pass`

Unsupported families must remain rows with `geometry_status = unsupported`; they
must not be silently dropped because they affect `RGA-coverage`.

## Semantic Block

```text
semantic = {
  semantic_score_raw: float | null,
  semantic_score_type: string | null,
  semantic_score_norm: float | null,
  rank_in_context: int | null,
  predicate_rank_for_pair: int | null,
  top50_semantic: bool,
  top100_semantic: bool,
  context_prediction_count: int | null,
  normalization_rule: string
}
```

Mapping:

- `semantic_score_raw` = H001 `scores.ranking_score` or
  `semantic.ranking_score`.
- `semantic_score_type` = H001 `scores.ranking_score_type` when available.
- `rank_in_context` = H001 `ranks.semantic_rank_in_subgraph`.
- `predicate_rank_for_pair` = H001 `ranks.predicate_rank_for_pair`.
- `top50_semantic` = `rank_in_context <= 50`.
- `top100_semantic` = `rank_in_context <= 100`.

Default normalization:

```text
semantic_score_norm = semantic_score_raw
normalization_rule = "native_probability_or_source_score_passthrough_v0"
```

This is acceptable only for within-source diagnostics. For cross-source
comparison, use rank normalization:

```text
semantic_score_norm =
  1 - (rank_in_context - 1) / (context_prediction_count - 1)
normalization_rule = "rank_in_context_linear_v0"
```

`context_prediction_count` must be derived per `(source_id, subgraph_id)` before
using rank normalization. If it is missing, cross-source `RGA-disagreement`
must be marked unavailable.

## Geometry Block

```text
geometry = {
  geometry_status: string,
  h001_verification_status: string | null,
  geometry_available: bool,
  geometry_checkable: bool,
  geometry_source: string | null,
  consistency_score: float | null,
  geometry_residual_proxy: float | null,
  p_geom_valid: float | null,
  p_geom_invalid: float | null,
  reason_codes: list[string],
  raw_features: object | null,
  selected_policy: string | null
}
```

Status mapping:

| H001 status | H002 `geometry_status` |
| --- | --- |
| `satisfied` | `satisfied` |
| `violated` | `unsatisfied` |
| `uncertain` | `uncertain` |
| `unsupported` | `unsupported` |
| missing verification row | `missing` |

Continuous fields:

- `consistency_score` comes from H001 `consistency_score` or
  `verification.consistency_score`.
- `p_geom_valid` comes from H001 `calibration.p_geom_valid`.
- `p_geom_invalid` comes from H001 `calibration.p_geom_invalid`.
- `raw_features` comes from H001 `geometry.features`.

Initial residual proxy:

```text
geometry_residual_proxy =
  1 - consistency_score, if consistency_score is available
  null, otherwise
```

This proxy is only for schema smoke and disagreement diagnostics. A future
factor graph must replace it with relation-family-specific residuals before
claiming method novelty.

## Label Block

```text
label = {
  label_match: int | null,
  label_match_status: string,
  family_match: int | null,
  matched_gt_ids: list[string],
  matched_predicates: list[string],
  in_h001_denominator: bool | null,
  label_source: string
}
```

Preferred mapping:

- From `failure_rows/rows.jsonl` when `prediction_id` is present there.
- `exact_match` maps to `label_match = 1`.
- `family_match` maps to `label_match = 0`, `family_match = 1`.
- `no_gt_for_pair` maps to `label_match = 0`.
- `pair_has_other_predicate` maps to `label_match = 0`.
- No failure-row match maps to `label_match = null`,
  `label_match_status = unavailable`.

GT direct-join mapping is allowed later, using:

```text
(scan_id, subgraph_id, subject_id, object_id, predicate_label)
```

as exact-label key. This is needed for full all-row label-geometry buckets, but
it is not required for the first RGA schema smoke.

Important boundary:

- `failure_rows/rows.jsonl` is top-K/failure-oriented, not all prediction rows.
- Therefore label fields derived only from failure rows must not be used as
  all-row label-match statistics.

## RGA Block

```text
rga = {
  bucket_top50: string | null,
  bucket_top100: string | null,
  geometry_axis: string,
  semantic_axis_top50: string,
  semantic_axis_top100: string,
  label_geometry_bucket: string | null,
  disagreement_score: float | null,
  coverage_state: string
}
```

Geometry axis:

| `geometry_status` | `geometry_axis` |
| --- | --- |
| `satisfied` | `H` |
| `unsatisfied` | `L` |
| `uncertain` | `U` |
| `unsupported` | `M` |
| `missing` | `M` |

Semantic axis:

```text
semantic_axis_top50 = "H" if top50_semantic else "L"
semantic_axis_top100 = "H" if top100_semantic else "L"
```

Bucket rule:

```text
bucket_topK = "RGA-" + semantic_axis_topK + geometry_axis
```

Examples:

- top-K semantic edge + unsatisfied geometry = `RGA-HL`.
- top-K semantic edge + satisfied geometry = `RGA-HH`.
- top-K semantic edge + uncertain geometry = `RGA-HU`.
- top-K semantic edge + unsupported or missing geometry = `RGA-HM`.

Coverage state:

| `geometry_status` | `coverage_state` |
| --- | --- |
| `satisfied` | `covered_checkable` |
| `unsatisfied` | `covered_checkable` |
| `uncertain` | `covered_checkable_uncertain` |
| `unsupported` | `unsupported_family` |
| `missing` | `missing_geometry` |

Disagreement score:

```text
disagreement_score =
  max(0, semantic_score_norm - p_geom_valid)
```

If either field is unavailable, set `disagreement_score = null`.

## Posterior Block

```text
posterior = {
  posterior_edge_valid: float | null,
  posterior_model_id: string | null,
  factor_contribution: object | null,
  abstain_or_promote: string | null
}
```

Current H002 status:

- `posterior_edge_valid = null`
- `posterior_model_id = null`
- `factor_contribution = null`
- `abstain_or_promote = null`

Reason:

- H002 has not yet defined or fit the factor graph.
- `p_geom_valid` is available as the geometry-only calibrated validity proxy and
  may be used as a baseline score or as a geometry factor.
- `posterior_edge_valid` should not simply copy `p_geom_valid`; the posterior is
  reserved for the factorized relation-reliability estimate that can include
  semantic score, object confidence, geometry evidence, uncertainty, and
  provenance.

## Provenance Block

```text
provenance = {
  created_by: string,
  created_at: string | null,
  input_prediction_path: string,
  input_geometry_path: string,
  input_failure_rows_path: string | null,
  input_gt_path: string | null,
  h001_joiner: string | null,
  selected_verification_policy: string | null,
  source_caveat: string | null,
  notes: list[string]
}
```

Source caveats:

- `VL-SAT`: controlled full-validation source.
- Open3DSG recovery: full-denominator recovery-policy variant using
  `recovery_relaxed_views_min2`; must be reported as recovery branch, not
  unmodified Open3DSG preprocessing.

## Projection Feasibility

### `VL-SAT`

Ready for first H002 projection:

- prediction identity is available.
- source rank and source score are available.
- geometry verification status is available for all prediction rows.
- `p_geom_valid` is available for geometry-checkable families.
- GT rows are available.
- failure rows provide GT match status for selected top-K/failure rows.

Known limitations:

- many rows are unsupported because they are outside current H001 geometry
  families.
- direct all-row exact-label matching still needs an H002 join script.
- `geometry_residual_proxy` is not a final family-specific residual.

### Open3DSG Recovery

Ready for first H002 projection:

- prediction identity is available.
- source rank and source score are available.
- geometry verification status is available for all prediction rows.
- `p_geom_valid` is available for geometry-checkable families.
- failure rows provide GT match status for selected top-K/failure rows.

Known limitations:

- this branch has recovery-policy caveats and must keep that provenance.
- direct all-row exact-label matching should use the same GT denominator policy
  as H001 metrics.
- `geometry_residual_proxy` is not a final family-specific residual.

## Validation Checks For A Future Export Script

Minimum checks before writing any H002 projected JSONL:

- row count equals input prediction row count unless an explicit filter is
  declared.
- every projected row has `prediction_id`.
- every projected row has exactly one geometry status.
- all `unsupported` and `missing` rows remain in output.
- `posterior_edge_valid` is null until the factor graph is defined.
- `RGA-HL` rows are not inferred from `p_geom_valid` alone; they require
  `geometry_status = unsatisfied`.
- source-specific caveats are copied into provenance.
- validation/test rows are not used to tune semantic or geometry thresholds.

## Next TODO

The next H002 document should be `03_inventory.md` or `03_smoke.md`.

Recommended next step:

- Write a no-output smoke plan for projecting `VL-SAT` and Open3DSG rows into
  `h002_rga_edge_v0`.
- Specify exact commands, expected row counts, and validation checks.
- Only after the smoke plan is frozen, implement a small projection script under
  the H002 folder if needed.
