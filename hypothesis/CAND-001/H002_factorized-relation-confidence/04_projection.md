# H002 Projection

Last updated: 2026-06-11

## Purpose

이 문서는 `h002_rga_edge_v0` projection validator의 실행 계약을 정의한다.
`01_rga.md`는 metric contract, `02_schema.md`는 row schema, `03_smoke.md`는
read-only smoke plan이다. `04_projection.md`는 그 다음 단계로, 실제 validator가
어떤 입력을 읽고 어떤 summary를 내야 하는지 고정한다.

이 문서는 아직 row-level H002 artifact를 만들지 않는다. 현재 단계의 목표는 H001
artifacts를 수정하지 않고 RGA projection 가능성을 검증하는 compact summary
contract를 고정하는 것이다.

## Projection Mode

Initial mode:

```text
validate_only
```

Allowed behavior:

- read H001 source artifacts.
- validate row count, key parity, required fields, geometry status mapping.
- derive dry RGA bucket counts.
- emit compact summary if implementation is later requested.

Forbidden behavior:

- modify H001 artifacts.
- tune thresholds on validation rows.
- create `posterior_edge_valid` from `p_geom_valid`.
- drop `unsupported` or `missing` rows from coverage accounting.
- claim paper-level H002 results from smoke/projection summaries.

## Proposed Output Location

If a validator is implemented, outputs should live under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/rga_smoke/
```

Proposed files:

```text
artifacts/rga_smoke/
  vlsat_summary.json
  open3dsg_recovery_summary.json
  report.md
```

Row-level output is deferred. If row-level rows are later needed, use:

```text
artifacts/rga_smoke/rows/
  vlsat_rga_edges.jsonl
  open3dsg_recovery_rga_edges.jsonl
```

Do not create row-level artifacts unless the compact summary shows zero
blocking validation errors.

## Input Contract

### `vlsat`

```text
source_id: vlsat
scope_id: full_official_validation
root: experiments/H001_geom_reliability/sources/vlsat/full_validation/
prediction_path: adapter/predictions.jsonl
geometry_path: geometry/verification.jsonl
failure_rows_path: failure_rows/rows.jsonl
gt_path: adapter/ground_truth.jsonl
metrics_path: metrics/metrics.json
```

Expected rows:

- prediction rows: 957,008
- geometry rows: 957,008
- failure rows: 59,841
- GT rows: 11,254

### `open3dsg_recovery_relaxed_views_min2`

```text
source_id: open3dsg_recovery_relaxed_views_min2
scope_id: full_official_validation_recovery
root: experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/
prediction_path: adapter/predictions.jsonl
geometry_path: geometry/verification.jsonl
failure_rows_path: failure_rows/rows.jsonl
gt_path: null
metrics_path: metrics/metrics.json
source_caveat: recovery-policy variant; not unmodified Open3DSG preprocessing
```

Expected rows:

- prediction rows: 695,916
- geometry rows: 695,916
- failure rows: 82,155

## Future CLI Contract

If implemented, the validator should expose a small CLI:

```bash
python tools/project_rga.py \
  --source vlsat \
  --mode validate-only \
  --output artifacts/rga_smoke/vlsat_summary.json

python tools/project_rga.py \
  --source open3dsg_recovery_relaxed_views_min2 \
  --mode validate-only \
  --output artifacts/rga_smoke/open3dsg_recovery_summary.json
```

Required options:

- `--source`: one of `vlsat`, `open3dsg_recovery_relaxed_views_min2`.
- `--mode`: initially only `validate-only`.
- `--output`: compact summary JSON path.

Disallowed initial options:

- no threshold override.
- no validation-tuned normalization.
- no row filter that removes unsupported families.
- no posterior model option.

## Projection Algorithm

Validator steps:

1. Load source config.
2. Assert required input files exist.
3. Count prediction, geometry, failure, and GT rows.
4. Check prediction-geometry key parity by `prediction_id`.
5. Stream `geometry/verification.jsonl` as the primary projection input.
6. For each row, extract identity, edge, predicate, semantic, geometry, and
   provenance fields according to `02_schema.md`.
7. Map H001 `verification_status` to H002 `geometry_status`.
8. Derive `top50_semantic` and `top100_semantic` from
   `semantic.ranks.semantic_rank_in_subgraph`.
9. Derive `RGA` buckets for top-50 and top-100.
10. Load failure-row match status as partial label evidence, keyed by
    `prediction_id`.
11. Keep label fields unavailable for rows absent from failure rows.
12. Set all posterior fields to `null`.
13. Emit compact validation summary.

## Status Mapping

Geometry mapping:

| H001 `verification_status` | H002 `geometry_status` | RGA geometry axis |
| --- | --- | --- |
| `satisfied` | `satisfied` | `H` |
| `violated` | `unsatisfied` | `L` |
| `uncertain` | `uncertain` | `U` |
| `unsupported` | `unsupported` | `M` |
| missing row | `missing` | `M` |

Label mapping from failure rows:

| H001 failure-row `match_status` | H002 fields |
| --- | --- |
| `exact_match` | `label_match = 1`, `family_match = 1` |
| `family_match` | `label_match = 0`, `family_match = 1` |
| `no_gt_for_pair` | `label_match = 0`, `family_match = 0` |
| `pair_has_other_predicate` | `label_match = 0`, `family_match = 0` |
| unavailable | `label_match = null`, `family_match = null` |

RGA bucket mapping:

```text
semantic_axis_topK = "H" if semantic_rank_in_subgraph <= K else "L"
geometry_axis =
  "H" for satisfied
  "L" for unsatisfied
  "U" for uncertain
  "M" for unsupported or missing

bucket_topK = "RGA-" + semantic_axis_topK + geometry_axis
```

Important guard:

- `RGA-HL` must only mean semantic top-K plus deterministic geometry
  `unsatisfied`.
- It must not mean low `p_geom_valid`.

## Summary Schema

Initial summary schema:

```text
h002_rga_projection_summary_v0
```

Required fields:

```text
{
  schema_version,
  source_id,
  scope_id,
  mode,
  created_at,
  input_paths,
  input_counts,
  projected_counts,
  key_parity,
  required_field_check,
  geometry_status_counts,
  rga_bucket_top50_counts,
  rga_bucket_top100_counts,
  rga_metric_dry,
  failure_row_label_status_counts,
  posterior_guard,
  provenance_caveats,
  validation_errors,
  status
}
```

Required `status` values:

- `ready_for_rga_diagnostic`
- `ready_for_rga_diagnostic_with_caveat`
- `blocked`

## Read-Only Precheck

Read-only checks on 2026-06-11 showed:

| Source | Prediction rows | Geometry rows | Key mismatches | Missing required fields |
| --- | ---: | ---: | ---: | ---: |
| `vlsat` | 957,008 | 957,008 | 0 | 0 |
| `open3dsg_recovery_relaxed_views_min2` | 695,916 | 695,916 | 0 | 0 |

These checks support implementing a compact projection validator.

## Expected Dry RGA Buckets

Dry bucket counts are computed from H001 `verification_status`, not from
`p_geom_valid` thresholds.

### Top-50

| Source | `RGA-HH` | `RGA-HL` | `RGA-HU` | `RGA-HM` | `RGA-LH` | `RGA-LL` | `RGA-LU` | `RGA-LM` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 7,449 | 116 | 1,534 | 18,301 | 81,667 | 31,140 | 98,942 | 717,859 |
| `open3dsg_recovery_relaxed_views_min2` | 4,480 | 2,159 | 3,036 | 17,725 | 63,574 | 19,863 | 67,484 | 517,595 |

### Top-100

| Source | `RGA-HH` | `RGA-HL` | `RGA-HU` | `RGA-HM` | `RGA-LH` | `RGA-LL` | `RGA-LU` | `RGA-LM` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 13,432 | 337 | 4,121 | 36,910 | 75,684 | 30,919 | 96,355 | 699,250 |
| `open3dsg_recovery_relaxed_views_min2` | 9,561 | 3,118 | 7,195 | 34,830 | 58,493 | 18,904 | 63,325 | 500,490 |

Dry metric denominators:

| Source | K | Covered top-K denominator | Top-K rows | `RGA-HL@K` | `RGA-valid@K` | `RGA-uncertain@K` | `RGA-coverage@K` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 50 | 9,099 | 27,400 | 0.0127 | 0.8187 | 0.1686 | 0.3321 |
| `vlsat` | 100 | 17,890 | 54,800 | 0.0188 | 0.7508 | 0.2304 | 0.3265 |
| `open3dsg_recovery_relaxed_views_min2` | 50 | 9,675 | 27,400 | 0.2232 | 0.4630 | 0.3138 | 0.3531 |
| `open3dsg_recovery_relaxed_views_min2` | 100 | 19,874 | 54,704 | 0.1569 | 0.4811 | 0.3620 | 0.3633 |

Interpretation boundary:

- These are smoke/projection sanity counts, not final H002 results.
- Open3DSG top-100 rows are 54,704, not 54,800, because the source prediction
  universe does not provide 100 rows for every context under this ranking
  contract.
- The current RGA coverage is low because unsupported families remain included
  in top-K coverage accounting.

## Validation Errors

The validator must treat these as blocking:

- missing required input file.
- prediction and geometry row count mismatch.
- prediction-geometry key mismatch.
- missing required identity field.
- unknown `verification_status`.
- top-K bucket count not summing to total projection rows.
- non-null posterior fields in `validate_only` mode.
- missing Open3DSG recovery caveat.

The validator must treat these as warnings:

- label unavailable for rows not present in failure rows.
- `p_geom_valid` unavailable for unsupported families.
- `semantic_score_norm` unavailable for cross-source rank-normalized
  disagreement.
- Open3DSG top-100 row count below contexts times 100.

## Acceptance Gate

H002 can move from projection contract to RGA diagnostic if:

- both sources pass key parity.
- both sources pass required field checks.
- projected row count equals geometry row count.
- `posterior_non_null_count = 0`.
- dry `RGA-HL` is computed from deterministic status only.
- compact summary records source caveats and unsupported-family coverage.

If this gate fails, H002 should not proceed to factor graph design.

## Next TODO

Next document:

```text
05_diagnostic.md
```

Recommended next work:

- Run or implement the compact projection validator.
- Save only summary artifacts under `artifacts/rga_smoke/`.
- Use the summary to decide whether `RGA-HL@K` adds information beyond H001
  `Violation@K`.
- If it does not, stop H002 as an independent branch and fold the analysis into
  H001.
