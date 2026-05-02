# Problem

Last updated: 2026-04-30

## Problem Statement

Current 3D Scene Graph methods can predict object-object relations, and recent methods can improve relation prediction with edge features, spatial knowledge, visual-language semantics, or open-vocabulary prompts. However, the final relation edge is usually still a label or text prediction. It does not explicitly expose why the relation is geometrically valid, which 3D evidence supports it, or which constraints it violates.

H001 studies whether relation edges in 3DSSG-style indoor scenes can be made more reliable by attaching explicit geometry evidence and using that evidence to verify or recalibrate semantic relation predictions.

## What This Is Not

- Not a new full open-vocabulary 3D Scene Graph pipeline.
- Not full 3D reconstruction.
- Not robotics navigation.
- Not OpenFunGraph-style full functional relation discovery.
- Not a replacement for Open3DSG, CCL-3DSGG, VL-SAT, SGGpoint, or SMKA.

## Current Evidence

Fact:

- `3DSSG` provides the benchmark anchor for object-node and relation-edge prediction.
- `SGGpoint` makes relation edges first-class learned representations with EdgeGCN.
- `SMKA` shows that support hierarchy and symbolic/text knowledge improve 3DSSG relation prediction.
- `VL-SAT` shows that visual-language semantics improve long-tail and unseen relation triplets.
- `Open3DSG` and `CCL-3DSGG` make open-vocabulary 3D relation prediction a real baseline space.
- `FirePlace` supports the broader claim that 3D geometric constraints can refine LLM/VLM common-sense reasoning.

Inference:

- CAND-001 should not claim novelty from "using geometry" or "using spatial knowledge" alone.
- The sharper problem is edge-level evidence: relation edges should carry inspectable geometric support, violation status, confidence, and provenance.

## Research Value

This problem is valuable because relation predictions are used downstream for scene understanding, query, planning, and embodied reasoning. A relation graph that says `cup on table` without exposing contact/support evidence is harder to debug and easier to hallucinate. A geometry-grounded edge can support both standard graph prediction metrics and reliability-oriented metrics such as violation rate.

## Target Setting

- Indoor 3D scene.
- Object instances are known or provided by a reliable source.
- Candidate relation labels or texts are given by ground truth, closed-set baseline, open-vocabulary baseline, or controlled semantic proposal.
- Geometry evidence is computed from object point clouds, bounding boxes, positions, and local spatial context.

## Assumptions

- 3DSSG / 3RScan contains enough support/contact, proximity, and relative-position relations to evaluate a first verifier.
- Object instance geometry is available from 3RScan files.
- A geometry-checkable predicate subset can be separated from purely semantic or functional relations.
- A verifier can be evaluated even before reproducing every baseline end-to-end.

## Out of Scope

- Full predicate space verification.
- Functional relation discovery such as `switch controls light`.
- Dynamic/online scene graph generation.
- LLM planning or robot navigation.
- Reconstructing object geometry from raw RGB-D as part of the first experiment.
