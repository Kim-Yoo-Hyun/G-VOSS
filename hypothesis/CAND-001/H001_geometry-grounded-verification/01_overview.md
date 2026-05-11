# Overview

Last updated: 2026-05-07

## Role

This document records the compact H001 problem setting, hypothesis, final
hypothesis-stage status, and transition boundary.

Detailed stage logs were consolidated to reduce repeated gate/result text. The
canonical H001 files are now:

| File | Role |
| --- | --- |
| `01_overview.md` | problem, hypothesis, status, claim boundary |
| `02_method.md` | evidence schema, verifier, calibration, evaluation protocol, prediction join |
| `03_data_baseline.md` | `VL-SAT` layout, hardened scope, payload readiness |
| `04_results.md` | H001-Mini, hardened metrics, controls, GT evaluation, evidence lock |
| `05_audit.md` | structured audit and reduced visual sanity check |
| `06_second_source.md` | baseline matrix, FROSS/Open3DSG source/runtime decisions |
| `07_experiment_spec.md` | reportability, scoped experiment spec, Docker transition rule |

## Problem

Open-vocabulary and learned 3D scene graph predictors can produce relation
edges whose semantic label is plausible from visual or language priors but
inconsistent with explicit 3D geometry. H001 focuses on geometry-checkable
relation families where this failure mode can be measured and corrected without
claiming a new 3DSSG generator.

Target families:

- `support_contact`
- `proximity`
- `relative_vertical`

Out of scope for the first experiment:

- full functional relation discovery;
- online RGB-D graph generation;
- robotics navigation;
- broad open-vocabulary 3DSSG generation improvement.

## Hypothesis

H001:

```text
For geometry-checkable 3DSSG relation families, adding explicit 3D geometry
evidence and verification to candidate semantic relation edges will reduce
geometry-inconsistent relation predictions while preserving useful
predicate/triplet recall.
```

Operational form:

```text
semantic prediction score + frozen geometry evidence/verifier + calibrated
p_geom_valid -> reliability-aware reranking/filtering
```

Method framing:

```text
calibrated geometry-consistency evaluation and re-ranking framework
```

This framing treats the verifier as one component of a broader reusable
framework: identity-preserving prediction rows, geometry evidence, calibrated
`p_geom_valid`, reliability-aware reranking/filtering, and violation/recall
evaluation.

## Current Status

Status:

```text
hypothesis_stage_complete_for_geom_reliability_experiment
```

Facts:

- `VL-SAT` / `vlsat_closed_set` is the first learned prediction source.
- H001-Mini and hardened validation are complete.
- Hardened held-out scope has 127 scans, 388 subgraphs, 673,816 prediction
  rows, 7,505 ground-truth rows, 155,496 in-scope prediction rows, and an
  in-scope GT denominator of 2,545.
- `probabilistic_recalibrated` improves `semantic_only` R@50/R@100 and lowers
  Violation@50/@100 on the hardened scope.
- Nontriviality controls, structured audit, GT-based verifier evaluation, and
  reduced visual sanity check are complete.
- `07_experiment_spec.md` defines the scoped experiment transition and Docker
  requirement.

Inference:

- H001 is ready to enter a scoped `VL-SAT`-centered experiment phase if the user
  chooses to proceed.
- The preferred top-tier path is not a single-baseline-only justification; it is
  to add Open3DSG as a second prediction source after Dockerized checkpoint
  reproduction.
- It is not ready for baseline-agnostic or broad open-vocabulary claims until
  Open3DSG raw dump, JSONL export, geometry join, and metric evidence exist.

## Allowed Claim

Allowed scoped claim:

```text
On reproduced VL-SAT 3DSSG predictions, geometry-calibrated relation
verification improves relation reliability for geometry-checkable families by
reducing geometry-inconsistent top-k predictions while preserving or improving
useful recall.
```

Required caveat:

```text
This is a VL-SAT-centered reliability-layer result with a reduced 50-row visual
sanity check, not a final baseline-agnostic or broad open-vocabulary 3DSSG
claim.
```

Preferred upgraded claim after second-source evidence:

```text
Across reproduced VL-SAT and Open3DSG prediction sources, calibrated
geometry-consistency re-ranking improves relation reliability for
geometry-checkable 3DSSG families while preserving useful recall.
```

Not allowed:

```text
The method broadly improves open-vocabulary 3D scene graph generation.
```

Not allowed:

```text
The method is already baseline-agnostic across 3DSSG predictors.
```

## Transition Gate

User decision needed:

```text
Enter Docker-based H001 experiment workflow with VL-SAT table reproduction
first, then add Dockerized Open3DSG checkpoint reproduction as the selected
second-source expansion.
```

If the experiment phase is entered, paper-body experiment implementation must
be Docker-based and should start from the root proposed in `07_experiment_spec.md`:

```text
experiments/H001_geom_reliability/
```
