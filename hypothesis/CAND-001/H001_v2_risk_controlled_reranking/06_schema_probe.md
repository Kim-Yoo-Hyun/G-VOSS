# H001_v2 Calibration Schema Probe

Last updated: 2026-06-22 KST

This probe checks whether the existing H001 artifacts contain the fields needed
for a defensible H001_v2 threshold selector before any source metric is run.

## Checked Inputs

Calibration rows:

`archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/table.jsonl`

Calibration probability scores:

`archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/scores.jsonl`

Source geometry rows:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl
```

## Calibration Table Findings

`train_dev_calib/table.jsonl` has 5,809 rows:

| Family | geom_valid=1 | geom_valid=0 |
| --- | ---: | ---: |
| `proximity` | 1,060 | 1,054 |
| `relative_vertical` | 552 | 298 |
| `support_contact` | 953 | 1,892 |

Important fields:

- violation target: `label.geom_valid`
- family: `predicate.predicate_family`
- grouping: `scan_id`, `subgraph_id`, `candidate_id`
- semantic score/rank: present as schema fields but null for all 5,809 rows
- `geometry.features.consistency_score`: null for all 5,809 rows
- `p_geom_valid`: not present in this table

Implication:

- This table is useful for label and provenance checks.
- It is not sufficient by itself for H001_v2 threshold selection because it has
  no calibrated `p_geom_valid` and no source semantic ranking distribution.

## Calibration Score Findings

`p_geom_valid_smoke/scores.jsonl` has 5,809 rows and provides the deployable
score used by the H001 geometry join:

- `model_id`: `h001-p-geom-valid-smoke-v1`
- probability field: `p_geom_valid`
- target field: `label.geom_valid`
- split field: `role`

Role/family counts:

| Role | Family | geom_valid=1 | geom_valid=0 |
| --- | --- | ---: | ---: |
| `train` | `proximity` | 888 | 844 |
| `train` | `relative_vertical` | 388 | 188 |
| `train` | `support_contact` | 774 | 1,534 |
| `dev` | `proximity` | 172 | 210 |
| `dev` | `relative_vertical` | 164 | 110 |
| `dev` | `support_contact` | 179 | 358 |

Primary H001_v2 calibration set:

```text
p_geom_valid_smoke/scores.jsonl where role == "dev"
```

This gives 1,193 held-out calibration rows for threshold selection after the
geometry-validity model has already been fitted. `role == "train"` should not
be used to select `tau*`.

`p_geom_valid_family/scores.jsonl` also exists, but it uses
`p_geom_valid_family_specific` rather than the source-join field
`calibration.p_geom_valid`. It should remain a diagnostic/family-specific
control unless the H001_v2 protocol is explicitly re-frozen.

## Source Geometry Findings

For the H001 in-scope families (`support_contact`, `proximity`,
`relative_vertical`), both primary source geometry files contain the required
fields:

- semantic utility: `semantic.ranking_score`
- source predicate score: `semantic.predicate_score`
- semantic subgraph rank: `semantic.ranks.semantic_rank_in_subgraph`
- geometry probability: `calibration.p_geom_valid`
- violation status: `verification_status`
- grouping: `scan_id`, `subgraph_id`, `prediction_id`

VL-SAT in-scope rows:

| Status | Count |
| --- | ---: |
| `satisfied` | 89,116 |
| `uncertain` | 100,476 |
| `violated` | 31,256 |
| total | 220,848 |

Open3DSG in-scope rows:

| Status | Count |
| --- | ---: |
| `satisfied` | 68,054 |
| `uncertain` | 70,520 |
| `violated` | 22,022 |
| total | 160,596 |

For all in-scope source rows checked above, the following fields are non-null:

- `semantic.ranking_score`
- `semantic.predicate_score`
- `semantic.ranks.semantic_rank_in_subgraph`
- `calibration.p_geom_valid`

Out-of-scope or unsupported families can have null `p_geom_valid`; they must
remain outside H001_v2 primary selection and be counted as coverage exclusions.

## Protocol Consequence

The current artifacts support an edge-level risk threshold selector:

```text
r(e) = 1 - p_geom_valid(e)
eligible_tau(e) = r(e) <= tau
```

using held-out calibration rows from `p_geom_valid_smoke/scores.jsonl`.

The current artifacts do not support a calibration-split-derived top-K semantic
ranking guarantee, because the calibration score rows do not contain source
semantic ranking distributions. Therefore H001_v2 must phrase the primary
contract as:

> choose a fixed edge-level geometry-risk eligibility threshold from held-out
> calibration rows, then evaluate top-K recall/violation after semantic ranking
> within that fixed eligible set.

Top-K `Violation@K` remains the source evaluation metric, but it is not used to
choose `tau*`.

## Implementation Decision

First executable artifact:

```text
calibration-threshold dry run only
```

The dry run should:

- read only `p_geom_valid_smoke/scores.jsonl`;
- select `tau*` using `role == "dev"` rows only;
- report train rows only as provenance/diagnostic, not for selection;
- write under
  `hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/calibration_threshold_selection/`;
- not read VL-SAT/Open3DSG source metrics.

Source evaluation is blocked until the calibration-threshold dry run succeeds.
