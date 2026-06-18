# H003 Semantic-Geometry Consistency Embedding

Last updated: 2026-06-18 KST

## Status

- Stage: hypothesis formulation.
- Folder: `hypothesis/CAND-001/H003_Embedding/`
- Short name: `H003 / Embedding`
- Working method name: `Semantic-Geometry Consistency Embedding`
- Boundary: do not modify H001/GeoCalib experiment, result, paper, or release artifacts from this branch.

## Core Idea

H003 studies whether relation validity in 3D Scene Graphs can be learned as a compatibility space between semantic relation representations and object-pair geometry representations.

The basic hypothesis is:

> valid relation tuples should be close in a learned semantic-geometry embedding space, while invalid or counterfactual relation tuples should be far apart.

Example:

```text
chair -- standing on -- floor
```

If the observed geometry supports the relation, the semantic representation of the predicate/object tuple and the geometry representation of the object pair should be aligned.

Counterexample:

```text
chair -- standing on -- wall
```

If the tuple is semantically or physically inconsistent with the observed object-pair geometry, the two representations should be separated.

## Research Question

Can relation-level physical consistency be learned as a semantic-geometry compatibility representation, rather than evaluated only through explicit relation-family rules?

More concretely:

```text
compatibility(predicate, object semantics, object-pair geometry, source score)
  -> relation validity / consistency score
```

## Relation To Earlier Branches

H001/GeoCalib:

- evaluates and reranks existing relation predictions using calibrated geometry-consistency evidence.
- uses explicit relation-family geometry policies and reports recall/violation tradeoff.
- remains the completed paper-facing reliability layer.

H002:

- factorizes relation confidence into semantic and geometry channels.
- frames the problem as RGA and posterior reliability estimation.

H003:

- turns semantic-geometry agreement into a learned representation problem.
- treats explicit geometry rules and counterfactual corruptions as supervision, controls, or baselines rather than as the final method itself.
- is methodologically stronger only if it shows transfer, hard-negative robustness, calibration, or generalization beyond explicit rule scoring.

## Initial Claim Boundary

Do not claim:

- broad 3DSSG SOTA improvement.
- replacement of H001/GeoCalib main results.
- open-vocabulary relation generation improvement.
- learned model superiority before shortcut controls and held-out validation pass.

Allowed hypothesis-stage claim:

> Relation validity may be represented as a learned semantic-geometry compatibility space, where valid relation tuples are aligned and counterfactual or geometry-inconsistent tuples are separated. This could support source-transfer reliability scoring if it outperforms explicit rules on hard negatives and calibration without hiding recall tradeoffs.

## Success Criteria

H003 becomes worth promoting beyond hypothesis stage if a small controlled prototype shows:

- positive tuples and hard counterfactual negatives separate better than source-score-only and geometry-rule-only baselines.
- learned compatibility reduces `Violation@K` or false-valid rate without recall collapse.
- results hold under scene-level held-out split.
- object-class shortcut controls pass.
- wrong-pair, shuffled-geometry, subject/object swap, and predicate-family flip controls produce expected score drops.
- calibration metrics such as ECE/Brier/AUPRC improve or remain competitive against explicit rule scoring.

## Falsification Conditions

H003 should be deprioritized if:

- the embedding mostly learns trivial object-class priors.
- geometry-rule negatives are too easy and do not test real relation validity.
- learned compatibility does not outperform explicit rule score on hard negatives.
- missing GT annotations create excessive false negatives.
- source transfer across VL-SAT/Open3DSG/Qwen-style outputs fails.
- performance gains disappear under scene-level split or same-family/rank-matched controls.

