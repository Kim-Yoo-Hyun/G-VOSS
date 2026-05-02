# Paper Card

## Problem

3D semantic scene graph prediction in point cloud는 object instance와 relation triplet을 예측하지만, point cloud는 주로 geometry structure를 담고 semantic clue가 약하다. 또한 3DSSG predicate distribution은 long-tail이며, semantic predicates는 `standing on` 같은 빈번한 geometric predicates보다 희소하다.

## Core Idea

VL-SAT는 training stage에서만 2D visual semantics와 language semantics를 사용하는 multi-modal oracle model을 만들고, 이 oracle의 structural semantic knowledge를 3D-only model에 전달한다. Inference stage에서는 3D point cloud만 사용한다.

## Input / Output

- Input during training: 3D point cloud, class-agnostic instance masks, associated 2D image patches / multi-view image semantics, language triplet text embeddings.
- Input during inference: 3D point cloud and class-agnostic instance masks.
- Output: directed 3D semantic scene graph with object labels and predicate labels.

## Method

- Base 3D model follows a common GNN-based 3DSSG pipeline with node encoder, edge encoder, scene graph reasoning, object classifier, and predicate classifier.
- Node features are extracted from segmented object point sets using a PointNet-style encoder.
- Edge features encode geometric differences between linked instances: point mean, standard deviation, bounding box size, volume ratio, and maximum side length ratio.
- Oracle model uses visual features from 2D image patches associated with each point cloud instance, while keeping 3D geometric edge encoding.
- Node-level and edge-level collaboration are implemented with multi-head cross-attention between the 3D model and oracle model.
- Node-level collaboration uses a distance-aware mask; edge-level collaboration attends over edges without a distance mask.
- CLIP text embeddings of ground-truth triplet templates provide triplet-level regularization.
- The oracle helps training through back-propagated gradient flows; the 3D model remains 3D-only at inference.

## Main Claims

- VL-SAT is the first visual-linguistic knowledge transfer scheme applied to 3DSSG prediction in point cloud.
- Visual-linguistic semantics can improve discrimination of long-tailed and ambiguous semantic relations.
- The scheme improves multiple 3DSSG backbones, including SGFN and SGGpoint.
- It is especially helpful for tail relations and unseen triplets.

## Strengths

- Directly addresses the gap between geometry-heavy point clouds and semantic relation prediction.
- Uses 2D/language information only at training time, so inference remains practical for 3D-only setups.
- Provides strong evidence that semantic relation prediction benefits from external visual-linguistic semantics.
- Evaluates long-tail predicates and unseen triplets, which are important for CAND-001.
- Shows that SGGpoint can be boosted by semantic assistance, making the SGGpoint/VL-SAT pair useful as a baseline family.

## Limitations

- The output relation labels remain closed-set 3DSSG predicates.
- Geometry is used as learned edge feature and attention context, not as explicit verifiable evidence attached to each edge.
- The method improves relation classification but does not introduce a geometry-consistency metric or violation detector.
- It requires paired 2D views and preprocessing during training.
- It does not solve open-vocabulary relation generation; it is a semantic-assistance method for closed-set 3DSSG.

## Relevance to My Research

VL-SAT is a direct support paper for CAND-001 because it shows that 3DSSG relation prediction needs semantic assistance beyond raw geometry. It also shows the limitation that semantic knowledge is still absorbed into latent features rather than represented as explicit edge evidence. CAND-001 can position itself after VL-SAT by asking whether semantic relation proposals can be explicitly verified or refined using geometry evidence instead of only improving closed-set classification.

## Follow-up Questions

1. Which predicates improved most because of language semantics, and which remain geometry-limited?
2. Can VL-SAT-style semantic assistance be combined with an explicit geometry verifier?
3. Does tail predicate improvement come from better semantic discrimination or from dataset co-occurrence priors?
4. Can a CAND-001 evaluator separate semantic correctness from physical/geometric consistency?
