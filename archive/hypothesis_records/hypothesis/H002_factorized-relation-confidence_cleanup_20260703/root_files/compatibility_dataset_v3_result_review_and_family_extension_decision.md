# Compatibility Dataset V3 Result Review And Family Extension Decision

Date: 2026-06-26 KST

## Status

```text
status = h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe
artifact_root = artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision/
selected_path = accept_relative_vertical_Ce_mechanism_proof_and_probe_support_contact_evidence
validation_errors = 0
next = compatibility_dataset_v3_support_contact_evidence_probe_plan
```

## Decision

The v3 `relative_vertical` smoke is accepted as a scoped `C_e` mechanism proof.

```text
allowed_claim = scoped predicate-geometry compatibility mechanism for relative_vertical
```

It is not promoted to broad relation reliability or paper-level evidence.

Blocked claims:

```text
broad relation reliability
final p_rel / p_obs decision quality
all 3DSSG relation-family generality
paper-level Docker-reproduced result
```

## Evidence

The passed smoke used 400 train-only rows, 200 positive and 200 negative, organized as 200
same-geometry groups. Each group shares identical `G_e` and changes the predicate between
`higher than` and `lower than`.

```text
M5b predicate-conditioned T_e + G_e interaction AUROC = 1.000000
M4 geometry-only G_e AUROC = 0.500000
M5a plain T_e + G_e concat AUROC = 0.446300
C1 wrong-T same-G control AUROC = 0.000000
C2 shuffled-G global control AUROC = 0.477713
C3 shuffled-G within-predicate control AUROC = 0.515400
paired compatible-minus-incompatible mean = 0.812703
```

Interpretation:

- `G_e` alone is chance because paired rows share identical geometry.
- Plain concatenation is not enough.
- The explicit predicate-conditioned interaction is what solves the target.
- Wrong-T inverts the signal.
- Shuffled-G controls degrade to near chance.

This fixes the v2 failure mode where the target was solvable as generic geometry perturbation
detection rather than predicate-conditioned compatibility.

## Family Extension Decision

| Family | Decision | Reason |
| --- | --- | --- |
| `relative_vertical` | retain as scoped mechanism proof | clean same-G higher/lower compatibility target passed all controls |
| `support_contact` | selected next, but evidence probe first | best next family for physical generality, but prior rows were geometry-perturbation dominated |
| `attachment_like` | defer as primary | needs mesh/multi-view/observability evidence; previous audit targets were shortcut-prone |
| `proximity` | defer | current single-predicate distance setting collapses toward geometry verification |
| `relative_horizontal` | defer | needs coordinate/reference-frame contract |

## Why Not Immediate Support/Contact Smoke

The prior v2 support/contact branch showed a geometry-only-dominant failure. If we directly run
another learned smoke using gap/overlap perturbation negatives, we may only prove that the model
detects generic contact geometry shifts.

The next support/contact step must first check whether the available artifacts expose evidence that
can make predicate semantics necessary:

```text
object role
pose/orientation
contact direction
surface normal
mesh evidence
multi-view evidence
```

If these are absent, support/contact should remain secondary until new evidence axes are
materialized.

## Next Plan Contract

```text
next = compatibility_dataset_v3_support_contact_evidence_probe_plan
```

The next probe must answer:

1. Do current artifacts expose role/orientation/contact-direction evidence beyond generic
   gap/overlap?
2. Can same-G or near-G groups be formed where `T_e` changes validity without changing generic
   `G_e` distribution?
3. Can geometry-only remain near chance under the candidate target?
4. Are source score, object pair, floor/wall/ceiling, and predicate shortcuts controllable?
5. Is multi-view/mesh evidence required before support/contact can be a fair `C_e` target?

## Boundary

```text
train_only = true
validation_or_test_used = false
runs_new_learned_smoke = false
paper_evidence_allowed = false
h001_artifacts_modified = false
```
