# Paper Card

## Problem

3D scene understanding should model not only object semantics but also object relationships, attributes, and context in 3D space. Before 3DSSG, real-world 3D semantic scene graph data with rich inter-object relationships was limited.

## Core Idea

The paper introduces 3DSSG, a semantic 3D scene graph dataset built on 3RScan, and proposes a PointNet + GCN model to predict semantic scene graphs from class-agnostic instance-segmented 3D point clouds.

## Input / Output

- Input: 3D point cloud with class-agnostic instance segmentation.
- Output: semantic scene graph with object nodes, node attributes/class hierarchy, and relationship edges.

## Method

- Extract object point sets for nodes using ObjPointNet.
- Extract object-pair point sets from union bounding boxes using RelPointNet.
- Process relationship triplets with a GCN.
- Predict object classes and multi-predicate relationship labels.

## Main Claims

- 3DSSG provides large-scale semantic 3D scene graph annotations for real-world indoor scans.
- Semantic scene graphs can support cross-domain retrieval between 2D images and 3D scans.
- Multi-predicate prediction is important because multiple relationships can be valid between one object pair.

## Strengths

- Canonical dataset and problem setting for 3D scene graph generation.
- Its relationship taxonomy is explicitly semantic and geometric: spatial/proximity, support, and comparative relationships.
- Provides direct evidence that geometry-aware support/proximity information is built into the 3DSG problem.

## Limitations

- The original prediction model is closed-set.
- Later papers often use reduced class/predicate sets for benchmarking.
- The dataset provides labels but does not by itself solve open-vocabulary semantic reasoning.
- Geometry correctness is partly embedded in annotations rather than evaluated as a separate evidence channel.

## Relevance to My Research

3DSSG is the canonical anchor for CAND-001. It defines the object/relation setting and gives closed-set comparability. Its support/proximity/comparative taxonomy suggests a natural split between semantic labels and explicit geometric evidence.

## Follow-up Questions

1. Which 3DSSG predicates are directly geometry-checkable?
2. Which predicates need semantic or functional commonsense beyond geometry?
3. Can 3DSSG annotations be converted into a dual-channel edge schema?

