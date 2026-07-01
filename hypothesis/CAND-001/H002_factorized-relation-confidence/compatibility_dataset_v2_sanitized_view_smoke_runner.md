# Compatibility Dataset V2 Sanitized View Smoke Runner

Artifact root:

```text
artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner/
```

Status:

```text
status = h002_compatibility_dataset_v2_sanitized_view_smoke_runner_diagnostic_only_failed_controls
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
learned_smoke_executed = true
next_todo = compatibility_dataset_v2_failure_analysis
```

## Main Result

The sanitized smoke removed the previous construction shortcuts, but the primary compatibility
claim did not pass the controls.

Key Task-A AUROC:

| Model | AUROC | AUPRC | Accuracy |
| --- | ---: | ---: | ---: |
| `M1_source_only_Z_safe` | 0.5000 | 0.5091 | 0.5000 |
| `M2_semantic_only_T` | 0.4846 | 0.4953 | 0.4875 |
| `M3_semantic_source_TZ_safe` | 0.4797 | 0.4908 | 0.4825 |
| `M4_geometry_numeric_G` | 0.6731 | 0.6288 | 0.6175 |
| `M5_compatibility_TG_numeric` | 0.6250 | 0.5786 | 0.5900 |
| `M6_factorized_sanitized_TZGQ` | 0.6230 | 0.5788 | 0.5900 |
| `S1_predicate_family_shortcut` | 0.4479 | 0.4696 | 0.4700 |
| `S2_source_score_rank_shortcut` | 0.5000 | 0.5091 | 0.5000 |
| `S3_object_label_pair_shortcut` | 0.4885 | 0.4979 | 0.4850 |
| `C1_shuffled_G_within_family_control` | 0.6085 | 0.6332 | 0.5700 |
| `C2_wrong_T_same_G_control` | 0.6250 | 0.5786 | 0.5900 |

## Gate Result

```text
dataset_sanity = pass
against_source_semantic_shortcuts = pass
predicate_conditioning_over_geometry_only = fail
corruption_controls = fail
overall = diagnostic_only_failed_controls
```

The positive part:

```text
source-only = 0.5000
semantic-only = 0.4846
semantic+source = 0.4797
object-pair shortcut = 0.4885
M5 compatibility = 0.6250
```

So the target is not being solved by source score, rank, predicate, family, or object-pair priors.

The blocker:

```text
geometry-only G = 0.6731
T_e + G_e compatibility = 0.6250
wrong-T same-G control = 0.6250
```

This means the current v2 target does not yet require predicate-conditioned geometry reasoning.
Changing the predicate does not hurt the score, and geometry-only is stronger than `T_e + G_e`.

## Family-Level Result

Relative vertical:

```text
M4 geometry-only = 0.5000
M5 compatibility = 0.4788
C1 shuffled-G = 0.4458
C2 wrong-T = 0.4788
```

Support/contact:

```text
M4 geometry-only = 0.7492
M5 compatibility = 0.7043
C1 shuffled-G = 0.7065
C2 wrong-T = 0.7043
```

Interpretation:

- support/contact carries most of the learnable geometry signal;
- relative vertical is not learned under the current v2 construction;
- support/contact signal remains after shuffled-G and wrong-T controls, so the current target is
  likely driven by generic geometry perturbation or row-family geometry distribution rather than
  predicate-specific compatibility.

## What This Means

This smoke is not a failure of the broad H002 hypothesis, but it blocks promotion of the current
v2 dataset as evidence for `C_e = compatibility(T_e, G_e)`.

The current dataset proves:

```text
construction shortcuts can be removed;
source/semantic shortcuts are controlled;
numeric geometry contains nontrivial signal.
```

It does not yet prove:

```text
predicate semantics condition which geometry evidence matters.
```

## Next Failure Analysis

The next step should diagnose why the current v2 target is geometry-only-dominant.

Required checks:

1. Feature importance / ablation for geometry-only `M4`.
2. Family-specific error cases, especially support/contact false positives.
3. Why `C2_wrong_T_same_G_control` equals `M5`.
4. Whether support/contact negatives are mostly perturbation artifacts rather than semantic
   incompatibility.
5. Whether relative-vertical counterfactuals are too weak or too noisy.
6. Whether a stricter predicate-conditioned target should pair the same geometry with multiple
   predicates that require different evidence.

## Boundary

This runner:

- uses train-only data only;
- does not use validation/test data;
- does not train a paper model;
- does not create paper-level evidence;
- does not modify H001 artifacts.

## Next

```text
compatibility_dataset_v2_failure_analysis
```
