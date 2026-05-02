# Paper Card

## Problem

3D scene graph prediction must infer relationships between objects in noisy, cluttered, partially scanned point-cloud scenes. Existing data-driven models often classify relationships from visual/geometric features independently and do not explicitly use commonsense or structured 3D spatial cues.

## Core Idea

The paper proposes `3D Spatial Multimodal Knowledge Accumulation (SMKA)`: use hierarchical physical-space structure, external commonsense knowledge, visual context, and textual facts to regularize relationship prediction in 3D scene graphs.

The key physical prior is a support hierarchy:

- layer 1: floor;
- layer 2: objects directly supported by the floor, such as bed, table, sofa;
- layer 3: objects usually supported by second-layer objects, such as pillow, cup, cushion.

## Input / Output

- Input: 3D point cloud scene with object instance information for PredCls/SGCls, or raw point cloud with detector proposals for SGDet.
- Output: semantic scene graph `G = {V, R}` with object nodes and predicate edges.

## Method

1. Build a hierarchical symbolic knowledge graph `Ks`.
   - Start from ConceptNet.
   - Filter to common 3D object categories from SUNRGBD and ScanNet.
   - Add hierarchical tokens for object support layers.
   - Add support edges between correlated nodes in neighboring layers.
2. Build a hierarchical visual graph `Gv`.
   - Use Point Cloud Transformer features for object visual features.
   - Encode bounding-box spatial features with an MLP.
   - Initialize semantic features using GloVe embeddings.
   - Route objects into hierarchy layers based on symbolic knowledge.
   - Add support-like edges when the symbolic knowledge graph suggests support.
3. Encode visual context with a region-aware graph network.
   - Objects sharing the same physical support are treated as contextual regions.
   - Node and edge hidden states are updated through message passing.
4. Accumulate 3D spatial multimodal knowledge `Km`.
   - Align symbolic graph entities with visual contextual features.
   - Use graph reasoning over the symbolic knowledge graph.
   - Produce multimodal node and edge knowledge embeddings.
5. Predict scene graph.
   - Fuse multimodal knowledge embeddings with visual contextual features.
   - Decode with a GCN.
   - Predict object classes and relationship classes using cross-entropy losses.

## Main Claims

- Hierarchical structures in 3D physical space help reduce ambiguity in relation prediction.
- External text knowledge alone is insufficient; it should be aligned with 3D visual/spatial context.
- Support hierarchy and multimodal knowledge improve relation prediction, robustness to noisy labels, and long-tail relation performance.

## Strengths

- Very relevant closed-set precedent for combining symbolic/textual knowledge with 3D spatial structure.
- Uses 3DSSG directly, so it is comparable with SGGpoint, KISG, VL-SAT, and later 3DSSG-style baselines.
- Makes support relations structurally important instead of treating all predicates as independent labels.
- Includes ablations for hierarchical tokens, support edges, visual graph construction, and multimodal knowledge embeddings.

## Limitations

- The method is closed-set; it does not solve open-vocabulary relation prediction.
- Geometry evidence is mostly latent or encoded through support hierarchy and graph features; predicted edges do not expose explicit evidence fields.
- It uses ConceptNet and learned hierarchical tokens, so the quality of symbolic filtering and support-layer assumptions matters.
- SGDet is bottlenecked by object detection; gains are smaller when raw point-cloud detection is required.
- The official code link is currently not accessible, which may affect reproducibility.

## Relevance to My Research

Fact: SMKA explicitly combines 3D spatial hierarchy, external textual knowledge, visual context, and relation prediction on 3DSSG.

Inference: This is a direct predecessor for CAND-001's core question, but it solves the problem through learned multimodal knowledge regularization rather than explicit relation-edge verification. CAND-001 can position itself as moving from `knowledge-guided relation prediction` to `evidence-grounded relation verification`, where edge outputs retain inspectable geometry evidence such as support/contact, relative pose, distance, containment, and violation status.

## Follow-up Questions

- Can CAND-001 use SMKA as a closed-set spatial-knowledge baseline or paper-level comparison?
- Which support/proximity predicates benefit from explicit geometry evidence beyond SMKA's latent support hierarchy?
- Can the support hierarchy be converted into deterministic or probabilistic edge evidence instead of only a learned prior?
