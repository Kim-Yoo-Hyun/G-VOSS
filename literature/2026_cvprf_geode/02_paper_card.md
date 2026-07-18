# Paper Card

## Problem

Open-vocabulary 3D Scene Graph generators can rely on semantic co-occurrence
instead of explicit 3D layout, particularly for spatial predicates.

## Core Idea

GEODE represents object geometry and relation predicates as discrete tokens and
jointly denoises them. Each reverse step updates geometry before relations, so
predicate generation is conditioned on the newly recovered geometry.

## Input / Output

- Input: object nodes, object classes, scene-level condition, tokenized node
  position/size/orientation.
- Output: generated 3D scene graph with relation predicates.

## Method

- VQ encoders discretize node geometry and predicate semantics.
- A discrete diffusion model denoises geometry and relation tokens.
- A geometry-aware graph transformer couples node and edge updates.
- The geometry-to-relation schedule and relation-conditioned attention target
  spatial consistency during generation.

## Main Claims

The paper reports improved closed-set and open-vocabulary 3DSSG results, with
especially large gains on its spatial-predicate evaluation.

## Strengths

- Directly addresses semantic shortcuts in spatial relation generation.
- Tests geometry removal and reversed relation-to-geometry update order.
- Includes both standard and spatial-only 3DSSG metrics.

## Limitations

- Dataset evidence is limited to 3DSSG.
- Geometry codebooks, diffusion schedules, and upstream detectors are trained
  in separate stages.
- The method changes the generator and is not a reliability assessment for
  arbitrary fixed predictor outputs.

## Relevance to My Research

GEODE is a direct geometry-consistency boundary for H001. H001 cannot claim
novelty from conditioning predicates on geometry. Its distinct contribution is
post-prediction, source-score-excluded compatibility assessment, exact
endpoint/predicate transformation consistency, and family-aware re-ranking of
fixed candidate outputs.
