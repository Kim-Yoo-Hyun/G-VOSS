# Paper Card

## Problem

Early 3D scene graph methods often treated inter-object relations as secondary outputs of node/object reasoning. This weakens relation prediction because the visual and structural cues inside graph edges are not modeled explicitly.

## Core Idea

SGGpoint proposes a 3D point-based scene graph generation framework with an EdgeGCN reasoning module. It treats nodes and edges as paired representations and lets edge features influence node evolution while node features influence edge evolution.

## Input / Output

- Input: 3D point cloud and class-agnostic instance masks.
- Output: scene graph `G = (V, E)` where nodes are object classes and edges are structural relationship classes.

## Method

- The framework has three stages: scene graph construction, scene graph reasoning, and scene graph inference.
- A shared point cloud backbone extracts point-wise features from coordinates, RGB color, and normal vectors.
- Node features are created by pooling point-wise features inside each instance mask.
- Directional edge features are initialized from subject/object node features and their differences.
- EdgeGCN has two evolution streams:
  - node evolution with twinning edge attention,
  - edge evolution with twinning node attention.
- NodeMLP and EdgeMLP predict object classes and relationship classes.
- Training uses multi-class cross entropy for node and edge recognition.

## Main Claims

- Explicit edge-oriented reasoning improves 3D point-based scene graph generation.
- Multi-dimensional edge features should not be treated as by-products of node recognition.
- Twinning interactions between nodes and edges improve both object and relation prediction.
- EdgeGCN is also useful for general graph representation learning tasks.

## Strengths

- Very direct precedent for CAND-001's edge-centered formulation.
- Provides a closed-set 3DSSG baseline where relation edges are first-class representations.
- Uses a cleaned 3DSSG-O27R16 dataset with structural relationship labels.
- Reports object, predicate, and relationship triplet metrics separately.
- Shows that edge modeling improves relationship prediction, not only node classification.

## Limitations

- The relation labels are closed-set and structural; there is no open-vocabulary relation prediction.
- Edge features are learned latent representations, not explicit evidence records.
- The method does not attach interpretable geometry evidence such as contact/support ratio, containment, distance, or topological context to each edge.
- The cleaned 3DSSG-O27R16 dataset uses 27 object classes and 16 relationship categories, which may not match later 3DSSG settings.
- It does not address LLM/VLM hallucination or semantic relation grounding.

## Relevance to My Research

SGGpoint is a strong baseline and conceptual anchor for CAND-001. It says the important part of 3D scene graph reasoning is not only object nodes but relation edges. CAND-001 can build on this by making edge features explicit, semantically grounded, and geometrically verifiable.

## Follow-up Questions

1. Which SGGpoint edge features are most related to geometry-checkable relations?
2. Can explicit geometric evidence improve over EdgeGCN's latent edge representation?
3. How compatible is 3DSSG-O27R16 with later Open3DSG / CCL-3DSGG evaluation settings?
4. Can SGGpoint serve as a closed-set baseline for a CAND-001 verifier?
