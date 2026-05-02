# Experiment

Last updated: 2026-05-03

## Goal

Test whether explicit 3D geometry evidence can make 3DSSG relation edges inspectable and verifiable.

The first experiment is a smoke test, not a benchmark.

## Scope

Input:

- one validated 3DSSG/3RScan scan;
- ground-truth relation tuples;
- instance geometry from `semseg.v2.json` and PLY object points.

Output:

```text
edge evidence
rule verifier decisions
manual review labels
point-level support/contact comparison
subtype-aware support/contact consistency scores
```

## Predicate Families

| Family | Labels | Current use |
| --- | --- | --- |
| `proximity` | `close by` | primary smoke-test signal |
| `relative_vertical` | `higher than`, `lower than` | primary smoke-test signal |
| `support_contact` | `standing on`, `lying on`, `supported by` | primary research target, needs point evidence |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | diagnostic only |

Unsupported/deferred:

- appearance/common-sense relations;
- attachment and containment until stronger surface evidence is available;
- full functional relations.

## Phases

Phase A:

```text
export relation-level geometry evidence
```

Phase B:

```text
apply deterministic h001-rules-v0 verifier
```

Manual review:

```text
classify uncertain/violated cases by failure source
```

Phase C:

```text
add PLY point-level local support evidence for support/contact
```

Phase D:

```text
apply h001-rules-v1 and inspect remaining support/contact failures
```

Phase E:

```text
apply subtype-aware support/contact verifier
```

Phase F:

```text
design probabilistic geometry consistency calibration
```

Phase G:

```text
define prediction-level violation/recall evaluation protocol
```

Later:

```text
multi-scan validation
prediction-level baseline evaluation
```

## Metrics

Smoke-test metrics:

- edge export coverage;
- join failures;
- status counts by predicate family;
- manual review labels;
- OBB-only to point-level status transitions.
- v1 to v2 support/contact status transitions;
- subtype counts and consistency-score distributions.
- calibration target, label source, and score-to-probability design.
- violation rate, consistency-filtered recall, recall retention, and benchmark contribution boundary.

Not yet benchmark metrics:

- R@K / mR@K;
- triplet recall;
- consistency-filtered recall on model predictions.

## Current Finding

The useful split is:

```text
OBB-only evidence: proximity and vertical are usable.
point/local-surface evidence: needed for support/contact.
subtype-aware evidence: needed for legged floor support, soft support, and rigid object-on-furniture.
calibration: needs multi-scan positives, counterfactual negatives, and scan-level split.
evaluation: must compare semantic-only predictions against rule/probabilistic verification under recall retention.
horizontal evidence: blocked by coordinate-frame ambiguity.
```

## Next

Use `20_layout.md`, `21_eval_path.md`, and `artifacts/layout/vlsat/report.md` as the local layout compatibility and eval path result. Next, write the faithful `VL-SAT` layout prep staging policy before prediction-level evaluation.
