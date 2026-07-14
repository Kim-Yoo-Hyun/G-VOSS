# Paper Card

## Problem

Neural scene graph generators can produce outputs that violate spatial,
functional, or logical visual commonsense, especially under sparse relation
annotations.

## Core Idea

Mine dataset-specific commonsense constraints from training annotations,
compile them into an Answer Set Programming program, and refine fixed neural
SGG predictions by abductive inference at test time.

## Input / Output

- Input: object detections, ranked neural relation predictions, and pairwise 2D
  spatial facts.
- Output: a globally selected/refined scene graph that respects mined
  constraints while retaining neural confidence.

## Method

The method mines three rule groups: geometrically rooted spatial
distributions, functional cardinalities, and qualitative relational
regularities. The last group includes symmetry, inverse predicates, and
composition. Candidate rules are filtered by a model-prediction verifier and
then enforced through weighted abductive ASP inference.

## Main Claims

The paper claims model-agnostic post-hoc refinement without source-model
retraining, consistent gains across three image-SGG benchmarks and
architectures, and lower Constraint Violation Rate.

## Strengths

- Formal and explainable relation constraints.
- Explicit symmetry/inverse/composition support.
- Model-agnostic post-hoc deployment and a violation metric.

## Limitations

- The checked experiments are 2D/image SGG, not 3D ordered-pair physical
  compatibility on reconstructed geometry.
- Rules are dataset-specific and include a prediction-based verifier/tuning
  stage.
- The method performs global hard/declarative refinement rather than calibrated
  continuous source-excluded compatibility.

## Relevance to My Research

This is a direct H001 novelty threat. H001 must not claim the first post-hoc
constraint refinement, first relation-algebra correction, model-agnostic
refinement, or first violation-rate evaluation. The narrower distinction is a
continuous 3D same-pair compatibility factor with `Z` excluded, identity joins,
linked geometric counterfactuals, exact orbit projection, uncertainty, and
fixed 3DSSG source-level evaluation.

## Follow-up Questions

- Does a later version release code and clarify rule-verifier split usage?
- How does soft continuous geometry calibration compare with global ASP
  selection under incomplete 3D evidence?
