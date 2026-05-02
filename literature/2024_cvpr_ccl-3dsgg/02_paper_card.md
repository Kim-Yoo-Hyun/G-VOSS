# Paper Card

## Problem

3D Scene Graph Generation models depend on dense object and predicate labels, and closed-set training limits recognition of novel objects and predicates. CCL-3DSGG targets open-vocabulary 3DSGG with less dependence on ground-truth 3DSG annotation.

## Core Idea

The paper trains a 3DSG feature extractor by aligning point-cloud graph features with CLIP-based text and image features. It decomposes captions into word-level components that better match object/predicate/attribute labels and uses multi-view image contrastive learning to improve spatial predicate representation.

## Input / Output

- Input: unlabeled 3D point clouds with class-agnostic instance segmentation, image-text pairs, multi-view images
- Output: object and predicate predictions, including novel object/predicate classes through prompt-feature similarity

## Method

- Build unclassified 3D scene graph features from point cloud instances and instance pairs.
- Use grammar parsing to split text into object, predicate, adjective, and related word components.
- Use adjective exchange to generate harder negative text samples.
- Align text features with 3DSG features through Text-3DSG contrastive loss.
- Align image features with 3DSG features through multi-view Image-3DSG contrastive loss.
- During inference, compute cosine similarity between prompts and learned 3DSG features for open-vocabulary recognition.

## Main Claims

- CCL-3DSGG can learn useful 3DSG features without ground-truth object/predicate annotations.
- The method improves supervised, unsupervised, open-vocabulary, and zero-shot 3DSGG results.
- Grammar parsing and text contrastive loss are critical for word-level 3DSGG tasks.

## Strengths

- Direct baseline for CAND-001's open-vocabulary side.
- Evaluates both open-vocabulary and zero-shot splits on 3DSSG.
- Explicitly targets novel object and predicate recognition.
- Reports that multi-view image loss helps spatial predicate discrimination.

## Limitations

- The paper still depends on 3DSSG-style closed relation labels for quantitative evaluation.
- Qualitative results are provided for ScanNet because ground-truth 3DSG labels are missing.
- It does not directly evaluate whether predicted predicates are geometrically consistent.
- The authors note that inference could better use pixel features when images are available.

## Relevance to My Research

CCL-3DSGG is the cleanest open-vocabulary baseline to compare against if CAND-001 becomes the primary thesis direction. It strengthens semantic/open-vocabulary relation prediction, but it does not solve relation grounding through explicit geometric evidence.

## Follow-up Questions

1. Can CCL-3DSGG predictions be post-verified by geometry evidence?
2. Which of its open-vocabulary or zero-shot errors are geometry contradictions?
3. Can CAND-001 reuse its feature extractor and add edge-level geometry verification?

