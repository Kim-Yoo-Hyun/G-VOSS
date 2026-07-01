# Compatibility Dataset V3 Support/Contact Evidence Probe Plan

Date: 2026-06-26 KST

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_ready
artifact_root = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan/
selected_route = support_contact_evidence_inventory_before_materialization_or_smoke
validation_errors = 0
next = compatibility_dataset_v3_support_contact_evidence_probe_runner
```

## Purpose

The v3 `relative_vertical` smoke passed as a scoped `C_e` mechanism proof. The next candidate
family is `support_contact`, but it should not be tested by directly reusing v2 generated
counterfactual rows.

The prior v2 support/contact branch failed for a clear reason:

```text
target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility
```

Therefore this step freezes a probe plan. The next runner must determine whether support/contact
has enough evidence to build a clean predicate-conditioned `C_e` target before any learned smoke.

## Prior Evidence

Support/contact capacity from the v2 full train-side scan:

```text
eligible positive / negative = 74,364 / 896
positive predicates = lying on 26,882 / standing on 23,713 / supported by 23,769
negative predicates = lying on 896 / standing on 0 / supported by 0
direct HL/LH predicate balance pass = false
generated counterfactual policy = wrong_pair_shuffle_and_contact_gap_perturbation_required
```

v2 materialized support/contact rows:

```text
support/contact positive / negative = 120 / 120
lying on positive / negative = 40 / 40
standing on positive / negative = 40 / 40
supported by positive / negative = 40 / 40
```

But the negatives were generated:

```text
wrong_pair_geometry = 40
shuffled_geometry = 40
contact_gap_or_overlap_perturbation = 40
```

v2 failure analysis showed:

```text
geometry-only AUROC > compatibility AUROC
wrong-T did not change predictions
support/contact shuffled-geometry false positive rate = 0.800
support/contact wrong-pair false positive rate = 0.425
contact gap/overlap perturbation false positive rate = 0.025
```

This means v2 support/contact was not a clean predicate-conditioned compatibility target.

## Current Evidence Availability

Available:

```text
distance
XY/3D separation
projected overlap / IoU
vertical gap
subject/object top/bottom z
raw witness numeric geometry coverage
```

Missing in the current numeric view:

```text
role / orientation / pose
explicit contact direction
surface normal
mesh evidence
multi-view or visual evidence
```

This is the main reason support/contact must be probed before another smoke.

## Probe Tasks

| Task | Question | Pass Condition |
| --- | --- | --- |
| `source_inventory` | How many support/contact rows exist by predicate, queue, scan, directed pair, and visible pair? | enough non-generated route capacity exists |
| `field_availability_audit` | Which evidence axes are present beyond distance/overlap/gap? | role/orientation/contact-direction evidence exists, or route to visual/mesh materialization |
| `same_or_near_geometry_group_probe` | Can same-G or near-G predicate alternatives be formed? | target design predicts `G_e`-only near chance |
| `negative_policy_audit` | Which negatives are primary vs control-only? | wrong-pair, shuffled-G, and gap perturbation stay control-only |
| `shortcut_precheck` | Can object class, structural object, source rank, predicate, or visible pair predict labels? | high/medium shortcut axes are controllable |

## Blocked Actions

```text
run_support_contact_learned_smoke_now = blocked
use_contact_gap_or_overlap_perturbation_as_primary_negative = blocked
claim_support_contact_generality_from_v2_smoke = blocked
promote_relative_vertical_result_to_broad_reliability = blocked
```

## Probe Contract

The next runner should produce:

```text
source_inventory.json
evidence_axis_inventory.csv
same_or_near_geometry_capacity.csv
negative_policy_audit.csv
shortcut_precheck.csv
path_decision.json
```

Support/contact materialization is allowed only if:

```text
non-generated candidate route exists
role/orientation/contact-direction or equivalent evidence axis exists
same-G or near-G groups are available at reportable scale
geometry-only is expected near chance
shortcut precheck is controllable
```

If these fail, the correct route is to defer support/contact as primary and move to visual/mesh
evidence materialization or keep support/contact diagnostic.

## Boundary

```text
train_only = true
runs_learned_smoke = false
validation_or_test_used = false
paper_evidence_allowed = false
h001_artifacts_modified = false
```
