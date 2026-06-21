# H003 Dataset Contract

Last updated: 2026-06-20 KST

## Status

- Stage: hypothesis dataset contract.
- Scope: M1 schema and M5 counterfactual benchmark contract.
- Boundary: this contract does not create or modify H001/GeoCalib experiment,
  paper, result, or release artifacts.

## First Source Scope

The first H003 smoke should use a read-only row export from existing CAND-001
artifacts. It should not rerun or edit H001 paper-facing outputs.

Allowed first-gate source scope:

- one relation source at a time.
- train or train-dev style rows only for model development.
- existing compact semantic and geometry summaries if available.
- optional use of external/audit labels only as targets, never as input fields.

Disallowed first-gate scope:

- modifying H001/GeoCalib locked results.
- using H001 validation/test paper metrics as model-selection targets.
- reading posterior target fields as deployable input features.
- treating missing GT as a negative label.
- mixing generated counterfactual negatives across train/dev/test split groups.

Recommended first source:

```text
Open3DSG-derived CAND-001 train rows, read-only export
```

Reason:

- enough row volume for controlled negatives.
- open-vocabulary relation-source behavior is relevant to the semantic/geometry
  mismatch question.
- H002 already exposed the need for independent target handling.

VL-SAT can be used as the second source after the contract passes on one source.

## M1 Edge Row Schema

Minimum row:

```text
{
  row_id,
  source_id,
  source_run_id,
  scan_id,
  scene_context_id,
  subject_id,
  object_id,
  subject_label,
  object_label,
  predicate_label,
  predicate_text,
  predicate_family,
  semantic_evidence,
  geometry_evidence,
  coverage_evidence,
  uncertainty_evidence,
  interaction_features,
  label_provenance,
  target_label,
  corruption_provenance,
  split_id,
  counterfactual_group_id
}
```

### Semantic Evidence

Allowed fields:

- `source_score_raw`
- `source_score_normalized`
- `source_rank`
- `predicate_label`
- `predicate_text`
- `predicate_family`
- `subject_label`
- `object_label`
- optional predicate/object text embeddings

Notes:

- source scores from different systems must keep `source_id`.
- cross-source score calibration must be reported separately.

### Geometry Evidence

Allowed fields:

- compact object-pair geometry features.
- centroid delta.
- normalized distance.
- vertical order features.
- object size / bbox / OBB features.
- overlap or projected-overlap features.
- contact/support evidence features.
- relation-family-specific residuals.
- optional explicit geometry score such as `p_geom_valid`, if treated as a
  deployable rule-derived feature and compared against `explicit_rule_score`.

M2 embedding should prefer compact raw geometry features as the primary geometry
input. `p_geom_valid` can be used for M3 posterior and as a baseline, but H003
must report whether the learned method is merely distilling this field.

### Coverage Evidence

Allowed fields:

- `coverage_state`
- `geometry_evaluable`
- `unsupported_relation_family`
- `missing_geometry`
- `low_visibility_or_low_evidence`
- `coverage_source`

Coverage evidence is not a negative label. It tells the model whether a geometry
judgment is available and how much weight it should receive.

### Uncertainty Evidence

Allowed fields:

- `uncertainty_state`
- `near_threshold_geometry`
- `identity_uncertain`
- `ambiguous_relation`
- `visual_mesh_disagreement`, if independently available
- `insufficient_evidence`

Uncertainty evidence must be deployable at test time. Human review labels can be
targets but not input uncertainty features unless the downstream setting includes
human review.

### Interaction Features

Allowed first-gate interactions:

- `high_semantic_low_geometry`
- `high_semantic_unsupported_geometry`
- `low_semantic_high_geometry`
- `semantic_rank_band x geometry_status`
- `predicate_family x coverage_state`
- `source_id x predicate_family`

Interactions are explicit in M3 so that M2 can later be tested against a strong,
interpretable baseline.

## Label Policy

Labels are target/provenance fields, not deployable input fields.

Allowed label provenance:

| Label Provenance | Meaning | First-Gate Use |
| --- | --- | --- |
| `confirmed_positive` | GT or audit-confirmed relation with geometry support. | train/dev/eval target |
| `weak_positive` | high semantic + high geometry relation with no independent confirmation. | train-only or ablation |
| `generated_negative` | counterfactual negative derived from a confirmed/weak source row. | train/dev/eval target if grouped |
| `audit_negative` | audit-confirmed invalid relation. | train/dev/eval target |
| `unknown` | missing evidence, sparse annotation, unsupported family, or unresolved identity. | exclude from binary target |

Hard rule:

```text
missing GT != negative
```

## Negative Sampling Policy

Allowed corruption types:

| Corruption | Description | Difficulty |
| --- | --- | --- |
| `wrong_pair_same_scene` | attach predicate/semantic tuple to another pair in the same scene. | hard |
| `wrong_pair_cross_scene` | attach geometry from another scene. | easy/medium |
| `swap_subject_object` | swap subject/object identities and geometry direction. | medium/hard |
| `shuffle_geometry_same_family` | shuffle geometry among the same predicate family. | hard |
| `predicate_family_flip` | keep geometry but flip predicate family. | hard |
| `vertical_order_inversion` | invert up/down evidence for vertical relations. | hard |
| `support_contact_removed` | remove or contradict contact/support evidence. | hard if realistic |
| `distance_perturbation` | push proximity geometry outside the plausible range. | medium |

Each generated negative must preserve:

- original positive `row_id`.
- `counterfactual_group_id`.
- corruption type.
- corruption source row if any.
- split id inherited from the original row.

## Split Policy

Minimum:

- scene-level split.
- no shared `scan_id` between train/dev/test.
- original rows and all derived counterfactuals stay in the same split.

Recommended first split:

```text
train: train scenes
dev: held-out train/dev scenes
test: reserved until the model and corruption policy are frozen
```

Do not use paper-facing validation/test metrics to select H003 thresholds,
model family, or corruption policy.

## Shortcut Controls

Required controls:

- semantic-only.
- geometry-only.
- same-class / different-geometry.
- same-geometry / different-predicate.
- same-rank-band.
- same-family counterfactual.
- source-score removed.
- explicit-rule-score removed.

Report failures as H003 evidence. Do not tune the target until the control
passes unless the target policy is explicitly revised and versioned.

## Dataset Contract Gate

This contract is complete enough to draft the smoke protocol. Implementation can
begin only after an exact source path whitelist and row-export manifest are
written.

