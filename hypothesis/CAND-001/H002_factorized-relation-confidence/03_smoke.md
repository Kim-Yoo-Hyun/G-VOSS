# H002 Smoke Plan

Last updated: 2026-06-11

## Purpose

이 문서는 H002 `h002_rga_edge_v0` projection을 실제로 구현하기 전의 smoke plan이다.
목표는 H001 full-validation artifacts를 수정하지 않고, `VL-SAT`와 Open3DSG recovery
branch가 H002 RGA row로 lossless하게 projection 가능한지 확인하는 것이다.

이 단계에서는 새 H002 JSONL output을 만들지 않는다. 모든 명령은 read-only
diagnostic이어야 한다. Output artifact가 필요해지면 다음 문서에서 별도 script와
artifact path를 고정한다.

## Scope

Primary sources:

| Source | Scope | Prediction rows | Geometry rows | Failure rows |
| --- | --- | ---: | ---: | ---: |
| `vlsat` | full official validation | 957,008 | 957,008 | 59,841 |
| `open3dsg_recovery_relaxed_views_min2` | full official validation recovery branch | 695,916 | 695,916 | 82,155 |

Primary input roots:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/
```

Required input files per source:

- `adapter/predictions.jsonl`
- `geometry/verification.jsonl`
- `failure_rows/rows.jsonl`
- `adapter/ground_truth.jsonl`, if available
- `metrics/metrics.json`
- `adapter/manifest.json`
- `geometry/manifest.json`
- `failure_rows/manifest.json`

## Read-Only Smoke Commands

Run from repo root:

```bash
cd /home/yoohyun/research

VLSAT=experiments/H001_geom_reliability/sources/vlsat/full_validation
OPEN=experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2
```

### G0. File Existence

```bash
test -s "$VLSAT/adapter/predictions.jsonl"
test -s "$VLSAT/geometry/verification.jsonl"
test -s "$VLSAT/failure_rows/rows.jsonl"
test -s "$VLSAT/adapter/ground_truth.jsonl"
test -s "$VLSAT/metrics/metrics.json"

test -s "$OPEN/adapter/predictions.jsonl"
test -s "$OPEN/geometry/verification.jsonl"
test -s "$OPEN/failure_rows/rows.jsonl"
test -s "$OPEN/metrics/metrics.json"
```

Pass condition:

- all files exist and are non-empty.

### G1. Row Count Parity

```bash
wc -l \
  "$VLSAT/adapter/predictions.jsonl" \
  "$VLSAT/geometry/verification.jsonl" \
  "$VLSAT/failure_rows/rows.jsonl" \
  "$VLSAT/adapter/ground_truth.jsonl"

wc -l \
  "$OPEN/adapter/predictions.jsonl" \
  "$OPEN/geometry/verification.jsonl" \
  "$OPEN/failure_rows/rows.jsonl"
```

Expected:

| Source | File | Expected rows |
| --- | --- | ---: |
| `vlsat` | `adapter/predictions.jsonl` | 957,008 |
| `vlsat` | `geometry/verification.jsonl` | 957,008 |
| `vlsat` | `failure_rows/rows.jsonl` | 59,841 |
| `vlsat` | `adapter/ground_truth.jsonl` | 11,254 |
| `open3dsg_recovery_relaxed_views_min2` | `adapter/predictions.jsonl` | 695,916 |
| `open3dsg_recovery_relaxed_views_min2` | `geometry/verification.jsonl` | 695,916 |
| `open3dsg_recovery_relaxed_views_min2` | `failure_rows/rows.jsonl` | 82,155 |

Pass condition:

- prediction row count equals geometry row count for each source.
- failure row count is treated as partial diagnostic coverage, not all-row
  label coverage.

### G2. Prediction-Geometry Key Parity

```bash
comm -3 \
  <(jq -r '.prediction_id' "$VLSAT/adapter/predictions.jsonl" | sort) \
  <(jq -r '.prediction_id' "$VLSAT/geometry/verification.jsonl" | sort) \
  | head

comm -3 \
  <(jq -r '.prediction_id' "$OPEN/adapter/predictions.jsonl" | sort) \
  <(jq -r '.prediction_id' "$OPEN/geometry/verification.jsonl" | sort) \
  | head
```

Pass condition:

- command prints no rows for both sources.

Failure implication:

- H002 cannot produce identity-preserving all-row RGA projection until the
  missing keys are explained.

### G3. Required Field Presence

```bash
jq -r '
  select(
    (.prediction_id == null) or
    (.scan_id == null) or
    (.subgraph_id == null) or
    (.edge.subject_id == null) or
    (.edge.object_id == null) or
    (.predicate.predicate_label == null) or
    (.predicate.predicate_family == null) or
    (.semantic.ranks.semantic_rank_in_subgraph == null) or
    (.verification_status == null)
  )
  | .prediction_id
' "$VLSAT/geometry/verification.jsonl" | head

jq -r '
  select(
    (.prediction_id == null) or
    (.scan_id == null) or
    (.subgraph_id == null) or
    (.edge.subject_id == null) or
    (.edge.object_id == null) or
    (.predicate.predicate_label == null) or
    (.predicate.predicate_family == null) or
    (.semantic.ranks.semantic_rank_in_subgraph == null) or
    (.verification_status == null)
  )
  | .prediction_id
' "$OPEN/geometry/verification.jsonl" | head
```

Pass condition:

- command prints no rows for both sources.

### G4. Geometry Status Distribution

```bash
jq -r '.verification_status' "$VLSAT/geometry/verification.jsonl" \
  | sort | uniq -c

jq -r '.verification_status' "$OPEN/geometry/verification.jsonl" \
  | sort | uniq -c
```

Expected:

| Source | `satisfied` | `uncertain` | `violated` | `unsupported` |
| --- | ---: | ---: | ---: | ---: |
| `vlsat` | 89,116 | 100,476 | 31,256 | 736,160 |
| `open3dsg_recovery_relaxed_views_min2` | 68,054 | 70,520 | 22,022 | 535,320 |

H002 mapping:

| H001 `verification_status` | H002 `geometry_status` |
| --- | --- |
| `satisfied` | `satisfied` |
| `violated` | `unsatisfied` |
| `uncertain` | `uncertain` |
| `unsupported` | `unsupported` |

Pass condition:

- counts match expected manifest values.
- `unsupported` rows remain present.

### G5. Semantic Top-K Distribution

```bash
jq -r '
  (.semantic.ranks.semantic_rank_in_subgraph // .ranks.semantic_rank_in_subgraph) as $rank
  | if $rank <= 50 then "top50"
    elif $rank <= 100 then "top100_only"
    else "outside_top100"
    end
' "$VLSAT/geometry/verification.jsonl" | sort | uniq -c

jq -r '
  (.semantic.ranks.semantic_rank_in_subgraph // .ranks.semantic_rank_in_subgraph) as $rank
  | if $rank <= 50 then "top50"
    elif $rank <= 100 then "top100_only"
    else "outside_top100"
    end
' "$OPEN/geometry/verification.jsonl" | sort | uniq -c
```

Pass condition:

- every row maps to exactly one top-K bucket.
- `top50 + top100_only + outside_top100` equals total geometry rows.

### G6. RGA Bucket Dry Count

This command computes dry RGA buckets directly from H001 verifier status. It
must not use `p_geom_valid` thresholds.

```bash
jq -r '
  def geom_axis:
    if .verification_status == "satisfied" then "H"
    elif .verification_status == "violated" then "L"
    elif .verification_status == "uncertain" then "U"
    elif .verification_status == "unsupported" then "M"
    else "M"
    end;
  (.semantic.ranks.semantic_rank_in_subgraph // .ranks.semantic_rank_in_subgraph) as $rank
  | (if $rank <= 50 then "H" else "L" end) + geom_axis
' "$VLSAT/geometry/verification.jsonl" | sort | uniq -c

jq -r '
  def geom_axis:
    if .verification_status == "satisfied" then "H"
    elif .verification_status == "violated" then "L"
    elif .verification_status == "uncertain" then "U"
    elif .verification_status == "unsupported" then "M"
    else "M"
    end;
  (.semantic.ranks.semantic_rank_in_subgraph // .ranks.semantic_rank_in_subgraph) as $rank
  | (if $rank <= 50 then "H" else "L" end) + geom_axis
' "$OPEN/geometry/verification.jsonl" | sort | uniq -c
```

Interpretation:

- `HL` is the dry `RGA-HL@50` numerator candidate.
- `HH` is the dry `RGA-HH@50` numerator candidate.
- `HU` is semantic top-50 with uncertain geometry.
- `HM` is semantic top-50 outside current geometry coverage.

Pass condition:

- bucket counts sum to total geometry rows.
- `HL` is based only on `verification_status = violated`.
- `p_geom_valid` does not define the bucket.

### G7. Failure-Row Label Coverage

```bash
jq -r '.ground_truth.match_status // "missing"' \
  "$VLSAT/failure_rows/rows.jsonl" | sort | uniq -c

jq -r '.ground_truth.match_status // "missing"' \
  "$OPEN/failure_rows/rows.jsonl" | sort | uniq -c
```

Expected:

| Source | `exact_match` | `family_match` | `no_gt_for_pair` | `pair_has_other_predicate` |
| --- | ---: | ---: | ---: | ---: |
| `vlsat` | 3,850 | 2,843 | 38,525 | 14,623 |
| `open3dsg_recovery_relaxed_views_min2` | 2,665 | 2,739 | 60,485 | 16,266 |

Pass condition:

- status values match the expected enum.
- no `missing` status appears in failure rows.

Boundary:

- These label fields are not all-row GT labels.
- All-row label-geometry bucket reporting requires a separate direct GT join.

### G8. Posterior Guard

There is no command yet. The projection script must enforce:

```text
posterior.posterior_edge_valid = null
posterior.posterior_model_id = null
posterior.factor_contribution = null
posterior.abstain_or_promote = null
```

Pass condition:

- H002 smoke does not copy `p_geom_valid` into `posterior_edge_valid`.

## Expected Minimal Smoke Report

When a future script is allowed, the first report should contain only summary
counts and no row-level metric claim:

```text
source_id
input_prediction_rows
input_geometry_rows
projected_rows
prediction_geometry_key_mismatch_count
geometry_status_counts
rga_bucket_top50_counts
rga_bucket_top100_counts
failure_row_label_status_counts
unsupported_family_rows
missing_geometry_rows
posterior_non_null_count
validation_errors
```

Expected first-pass acceptance:

| Source | Projected rows | Key mismatches | Posterior non-null | Required status |
| --- | ---: | ---: | ---: | --- |
| `vlsat` | 957,008 | 0 | 0 | ready for RGA diagnostic |
| `open3dsg_recovery_relaxed_views_min2` | 695,916 | 0 | 0 | ready with recovery-branch caveat |

## Failure Conditions

H002 smoke fails if any of the following happens:

- prediction and geometry row counts differ without a documented reason.
- `prediction_id` parity fails.
- required identity fields are missing.
- unsupported geometry rows are dropped.
- `RGA-HL` is derived from `p_geom_valid` threshold instead of deterministic
  `verification_status = violated`.
- `uncertain` rows are counted as either valid or invalid in the primary bucket.
- `posterior_edge_valid` is filled before the factor graph spec exists.
- Open3DSG recovery provenance is omitted.
- validation rows are used to tune threshold, bucket, or normalization policy.

## What This Smoke Can Prove

This smoke can prove:

- H001 artifacts are row-wise reusable for H002 RGA projection.
- H002 can preserve identity, source score, geometry status, and provenance.
- `RGA-HL`, `RGA-HU`, and `RGA-coverage` can be computed without changing H001.
- H002 can test whether RGA is more than a rename of H001 `Violation@K`.

This smoke cannot prove:

- factor graph posterior is useful.
- H002 improves over H001.
- RGA is paper-level novelty.
- all-row label-geometry agreement is valid without direct GT join.

## Next TODO

If this smoke plan is accepted, the next document should be `04_projection.md`
or a small `tools/project_rga.py` spec under the H002 folder.

Recommended next step:

- Implement a read-only projection validator first.
- It should emit only a compact summary unless the user explicitly asks for
  row-level H002 artifacts.
- If row-level artifacts are created, place them under
  `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/rga_smoke/`
  and keep H001 artifacts unchanged.
