# Paper Card

## Problem

Supervised 3D scene graph learning needs object-level labels and relationship annotations, but 3DSSG-style relation labels are expensive and limited. Generic point-cloud pretraining does not optimize the graph structure needed for scene graph prediction.

## Core Idea

SGRec3D pretrains a 3D scene graph encoder with an object-level scene reconstruction pretext task. The model reconstructs object bounding boxes and shape encodings from a graph bottleneck, then discards the decoder and fine-tunes the encoder for object and predicate prediction.

## Input / Output

- Input: object instance point sets, object-pair point sets, bounding boxes
- Pretraining output: reconstructed object-level scene geometry
- Fine-tuning output: object node classes and predicate edge labels

## Method

- Build a graph from object instances and pairwise object neighborhoods.
- Encode node and edge features from point sets.
- Use a graph neural network as bottleneck.
- Decode object layout and shape representation for reconstruction.
- Fine-tune the pretrained encoder on 3DSSG labels.

## Main Claims

- First self-supervised pretraining approach designed specifically for 3D scene graph prediction.
- Graph-structured reconstruction pretraining is more useful than generic point-cloud contrastive pretraining for 3DSG.
- It improves label efficiency and performs well with limited scene graph labels.

## Strengths

- Directly geometry-aware: the pretext task forces object layout and relative scene structure into the graph representation.
- Uses additional 3D datasets without requiring scene graph labels.
- Provides a strong closed-set baseline for object/predicate/relationship prediction.

## Limitations

- Closed-set object and predicate prediction.
- Evaluation is still mainly standard 3DSSG recall / mean recall.
- Semantic open-world relation reasoning is outside the paper's scope.
- Predicate metrics may be saturated on 3DSSG, which can hide meaningful differences.

## Relevance to My Research

SGRec3D is the geometry/representation-learning side baseline. It supports the claim that graph-aware geometric pretraining matters, but does not solve open-vocabulary semantic reasoning. This makes it complementary to Open3DSG.

## Follow-up Questions

1. Can SGRec3D-style graph bottleneck features be reused as geometry evidence for open-vocabulary relation verification?
2. Which geometric predicates in 3DSSG are rule-checkable and which require semantic/functional reasoning?
3. Is a reconstruction pretext task enough for relation grounding, or do we need explicit support/contact/containment objectives?

