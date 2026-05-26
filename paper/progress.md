# H001 Experiment Progress Rationale

Last updated: 2026-05-26 KST

This document explains why H001 moved from hypothesis checks to Docker paper
experiments, why each next experiment was introduced, and how the key results
should be interpreted. It is a progress rationale, not a replacement for
`paper/draft.md`, `paper/preview.md`, or the Docker result tables.

## Research Claim Being Tested

H001 does not propose a new 3D Scene Graph generator. It tests a narrower
reliability claim:

```text
For geometry-checkable 3D scene graph relation families, calibrated
geometry-consistency scoring can expose and reduce semantically plausible but
physically inconsistent relation predictions while reporting recall tradeoffs.
```

The claim is restricted to `support_contact`, `proximity`, and
`relative_vertical`. This scope exists because these families can be checked by
explicit 3D geometry. Functional, social, affordance, relative-horizontal, and
open-ended language relations were not promoted into the main claim because the
current verifier evidence does not cover them.

## Stage 1: H001-Mini Smoke

Why this stage was run:

- The first question was whether semantic predictions contain enough
  geometry-inconsistent rows to make a reliability layer meaningful.
- A small pilot was cheaper than immediately building Docker-scale experiments.

What it showed:

| condition | R@50 | R@100 | Violation@100 | interpretation |
| --- | ---: | ---: | ---: | --- |
| `semantic_only` | 0.8741 | 0.9263 | not final | source ranking baseline |
| `probabilistic_recalibrated` | 0.8831 | 0.9353 | 0.0193 | positive smoke signal |

Why we moved on:

- The signal was positive but not top-tier evidence.
- The pilot did not have enough denominator discipline, controls, or
  reproducibility guarantees.
- Next step therefore had to be a hardened held-out evaluation with fixed
  denominator and paper-safe metrics.

## Stage 2: Hardened VL-SAT Evaluation

Why this stage was run:

- `VL-SAT` had official code/checkpoint route and was the cleanest first
  relation-source anchor.
- The hypothesis needed a fixed held-out scope, exact prediction/GT row counts,
  and Docker-promotable artifacts.

Fixed scope:

| item | count |
| --- | ---: |
| scans | 127 |
| subgraphs | 388 |
| directed pairs | 25,916 |
| prediction rows | 673,816 |
| GT rows | 7,505 |
| in-scope GT denominator | 2,545 |

Key result:

| condition | R@50 | R@100 | Violation@50 | Violation@100 | reading |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 | reproduced source ranking |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 | recall-first calibrated setting |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 | stricter violation-first setting |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 | hard-filter diagnostic |

Interpretation:

- The main signal is not just hard pruning. `probabilistic_recalibrated`
  preserves or slightly improves exact-label recall while reducing violations.
- `rule_verified_point_subtype` is useful as a zero-violation diagnostic, but
  it should not be framed as the default method because a reviewer could read
  it as simply filtering away difficult relations.
- `family_specific_p_geom_valid` shows a stronger violation-reduction
  operating point and motivates family-specific calibration as an ablation.

Why we moved on:

- A single-source `VL-SAT` result could be attacked as a method-specific trick.
- The next required evidence was nontriviality controls and independent verifier
  checks.

## Stage 3: Nontriviality Controls

Why this stage was run:

- Reviewers would ask whether the gain comes from a trivial spatial heuristic.
- H001 needed to show that semantic confidence, object-pair identity, and
  calibrated geometry all matter.

Control result:

| control | R@50 | R@100 | Violation@100 | what it tests |
| --- | ---: | ---: | ---: | --- |
| `control_p_geom_valid_only` | 0.2028 | 0.5049 | 0.0701 | geometry alone is insufficient |
| `control_distance_only` | 0.3835 | 0.5642 | 0.0993 | distance alone is insufficient |
| `control_shuffled_geometry` | 0.9297 | 0.9788 | 0.0559 | geometry distribution is insufficient |
| `control_wrong_pair_geometry` | 0.9242 | 0.9788 | 0.0581 | correct object-pair identity matters |

Interpretation:

- Geometry-only and distance-only controls perform much worse, so the method is
  not a simple geometry heuristic.
- Shuffled and wrong-pair controls degrade behavior, supporting the
  identity-preserving join as part of the contribution.

Why we moved on:

- Controls defended the re-ranking mechanism, but not the verifier itself.
- The next step was to test whether `p_geom_valid` separates GT-positive
  relations from deterministic counterfactual negatives.

## Stage 4: GT-Based Verifier Evaluation

Why this stage was run:

- A human audit would be slow and subjective if used as the primary verifier
  validation.
- GT positives and controlled counterfactual negatives provide a lower-burden
  evaluation of the geometry-validity signal.

Result:

| metric | rows | value |
| --- | ---: | ---: |
| GT-positive nonviolated rate | 2,545 | 0.9972 |
| GT-derived negative nonsatisfied rate | 2,545 | 0.9694 |
| `p_geom_valid` AUROC | 5,090 | 0.9779 |
| `p_geom_valid` AUPRC | 5,090 | 0.9737 |
| `p_geom_valid` Brier | 5,090 | 0.0538 |

Interpretation:

- The verifier signal has strong GT-positive/counterfactual support.
- This supports `p_geom_valid` as a reliability signal, while not proving
  physical correctness for every predicted row.

Why we moved on:

- GT/counterfactual evaluation does not replace qualitative sanity checks.
- The next step was a reduced visual/structured audit to confirm that flagged
  relation-quality issues correspond to plausible visual/geometric failures.

## Stage 5: Structured Audit And Reduced Visual Sanity

Why this stage was run:

- The method needed reviewer-defense evidence that violation labels correspond
  to meaningful relation-quality problems.
- A full large-scale human audit was not necessary for the hypothesis gate once
  GT-based verifier evaluation existed.

Result:

| source | rows | metric | value | caveat |
| --- | ---: | --- | ---: | --- |
| structured audit | 250 | quality-issue precision | 0.8933 | non-independent structured audit |
| visual spot-check | 50 | target-bucket quality-issue rate | 0.9333 | reviewer `yhkim`, reduced sanity check |
| visual spot-check | 50 | contradiction rate | 0.0333 | target-bucket contradiction |

Interpretation:

- The audit supports the failure interpretation.
- It must not be described as a large-scale or strictly blinded independent
  human study.

Why we moved on:

- At this point the hypothesis was sufficiently supported for a scoped
  `VL-SAT` reliability claim.
- For top-tier positioning, however, a single-source result was still weak.
- The next required experiment was a second-source relation predictor.

## Stage 6: Experiment Transition Gate

Why this gate existed:

- Hypothesis-stage artifacts were enough to decide feasibility, but not enough
  for paper-result claims.
- The user set a rule that paper experiments must be Docker reproducible.

What changed:

- H001 moved from hypothesis scripts/artifacts into
  `experiments/H001_geom_reliability/`.
- Docker table generation produced Table 1-6, locked manifests, reports, and
  paper-ready metric artifacts.

Interpretation:

- This transition prevented host-only or one-off outputs from becoming paper
  evidence.
- It also made later Open3DSG work compatible with the same row contract,
  geometry join, and metric evaluation.

## Stage 7: Open3DSG Second-Source Reproduction

Why this stage was run:

- A `VL-SAT`-only claim could be attacked as baseline-specific.
- Open3DSG was selected over a single-baseline justification because it is a
  stronger top-tier defense: it tests whether the same reliability layer works
  on a different relation source with open-vocabulary motivation.

Why this took many substeps:

- No trusted final trained Open3DSG checkpoint was confirmed in the official
  repository.
- Therefore we needed Dockerized payload staging, feature dump, training,
  checkpoint selection, H001 eval feature generation, raw-dump identity audit,
  adapter export, geometry join, metric evaluation, and caveat wording.

Key caveats:

- The result is a Docker-reproduced averaged-BLIP variant.
- Train split is filtered to 3,744/3,852 preprocessed-ready subgraphs.
- Train-dev validation is 156/160 subgraphs.
- H001 covered loadable eval scope is 377/388 contexts with
  `validation_missing_preprocessed:11`.
- Recall is exact predicate-label recall over the 2,545-row H001-family
  denominator.

Open3DSG result:

| condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

Interpretation:

- Open3DSG supports the cross-source reliability claim within measured H001
  families.
- The pattern is not identical to VL-SAT, which is useful: the framework is an
  operating-point/evaluation layer rather than a source-specific metric trick.
- The caveats are part of the result and must remain visible.

Why we moved on:

- Metrics alone do not explain why rows fail or whether residual risk remains.
- The next step was failure-analysis rows and qualitative inspection.

## Stage 8: Open3DSG Failure Analysis

Why this stage was run:

- Top-tier novelty needs "why the failure happens," not only metric deltas.
- Failure analysis connects semantic plausibility to physical inconsistency and
  exposes residual calibration risk.

Result:

| item | value |
| --- | ---: |
| real failure-analysis rows | 57,736 |
| validation errors | 0 |
| visual-audit queue rows | 6,162 |
| qualitative cases inspected | 36 |
| demoted by geometry-aware re-ranking | 23 |
| rule-violated with `p_geom_valid > 0.9` | 10 |

Interpretation:

- Qualitative rows support the paper's failure mechanism: predicted relations
  can be semantically plausible but physically inconsistent for the object pair.
- The 10 high-confidence rule-violated cases show residual calibration risk.
  This is why the paper reports probabilistic, rule-verified, and
  family-specific operating points separately.

Why we moved on:

- With VL-SAT, controls, GT verifier evaluation, audit sanity, Open3DSG metrics,
  and failure analysis complete, the hypothesis had enough paper-facing
  evidence for a scoped reliability paper.
- The next stage became paper writing, not another heavy baseline by default.

## Optional Branches And Why They Are Not Main Evidence Yet

### Qwen-VL

Why it exists:

- Qwen-VL is a modern VLM semantic-source extension and helps align the project
  with recent VLM/open-vocabulary trends.

Current status:

- Input schema, output JSONL contract, parser, tiny pilot scope, pair crops,
  model-lock plan, and Qwen3-VL-4B cache are ready.
- Runtime preflight and tiny inference smoke have not been promoted to metrics.

Why not main evidence:

- No full prediction JSONL, geometry join, denominator, metrics, or audit exists
  yet.
- It cannot replace Open3DSG as the current second-source anchor.

### FROSS / Functional Benchmarks

Why considered:

- They are relevant for online or functional/robotics scene graph directions.

Why not main evidence:

- FROSS does not cover all H001 target families cleanly.
- SceneFun3D/FunGraph3D would require a separate relation contract, denominator,
  verifier, and claim boundary.

## Current Paper-Ready Interpretation

Allowed:

- H001 is a calibrated geometry-consistency evaluation/re-ranking framework.
- It reduces geometry violations under measurable recall tradeoffs on measured
  `VL-SAT` and Open3DSG H001-family scopes.
- It provides controls, GT-based verifier support, denominator transparency,
  and failure-analysis evidence.

Not allowed:

- Broad open-vocabulary 3DSSG generation improvement.
- Arbitrary-baseline or baseline-agnostic generality.
- Exact official non-averaged Open3DSG reproduction.
- Guaranteed physical correctness.

## Current Paper Stage

The current paper body is in `paper/draft.md` and now runs from Title through
Conclusion. The current target-venue LaTeX source is in `paper/aaai/`, using
the latest public AAAI-26 style route until the exact target-year AAAI kit is
fixed. Docker PDF build verification is complete with `h001-aaai-tex:20260526`:
`main.pdf` builds to 9 total pages, technical content occupies pages 1-7,
references are on page 8, the AAAI reproducibility checklist is on page 9,
BibTeX uses 19 entries, and there are no missing citations, undefined refs,
overfull hboxes, LaTeX errors, or AAAI package errors.
Open3DSG-first table ordering is preserved: the manuscript treats Open3DSG as
the main open-vocabulary case study and VL-SAT as the controlled anchor.
Paper-result
experiments should remain Docker
reproducible, and optional Qwen/FROSS/functional extensions should not change
the main claim unless they receive the same row contract, metric, denominator,
and audit treatment.
