# Paper Card

## Problem

기존 3D scene graph prediction은 고정된 object class와 predicate label set에 의존한다. 이 때문에 rare object, fine-grained object, open-set relationship을 표현하기 어렵고, downstream language query나 robotics reasoning에서 필요한 관계 표현이 제한된다.

## Core Idea

Open3DSG는 3D point cloud 기반 GNN의 node/edge feature를 2D vision-language foundation model feature space에 distill한다. Inference 시에는 object node를 open-vocabulary query로 분류하고, object class context와 edge embedding을 InstructBLIP 계열 QFormer/LLM에 넣어 relationship을 생성한다.

## Input / Output

- Input: point cloud, class-agnostic instance mask, optional RGB-D frames with pose for feature distillation/fusion
- Output: open-vocabulary object labels and open-set inter-object relationship descriptions

## Method

- Construct initial graph from object instances and instance-pair union boxes.
- Encode object nodes using PointNet-style features.
- Encode predicate edges from object-pair point sets.
- Distill node features from OpenSeg / CLIP-aligned 2D features.
- Distill edge features from InstructBLIP visual features.
- Query object labels with CLIP text embeddings.
- Generate relationship text with an LLM conditioned on edge embedding and predicted object labels.
- Map generated relationships back to 3DSSG labels using BERT embeddings for closed-set evaluation.

## Main Claims

- First 3D point-cloud method for open-vocabulary 3D scene graph prediction with open-set relationships.
- CLIP-like discriminative predicate querying is weak for relationships; generative LLM-based relation prediction performs better.
- Open-vocabulary 3DSG is useful for rare/fine-grained object and relation descriptions.

## Strengths

- Directly targets the open-vocabulary gap in 3DSG.
- Makes relationship edges queryable/promptable rather than fixed to dataset labels.
- Provides a useful baseline for semantic relation proposal in CAND-001.
- Explicitly reports limitations related to LLM hallucination and imperfect geometric understanding.

## Limitations

- Closed-set quantitative evaluation still maps generated relation text back to 3DSSG's fixed relation labels.
- Overall zero-shot results lag strong fully supervised methods in standard 3DSSG metrics.
- Relationship diversity remains limited.
- The paper reports LLM-typical hallucinations and cases of imperfect geometric understanding, e.g. contradictory spatial relations.

## Relevance to My Research

Open3DSG is the main semantic-reasoning side baseline for a geometry-grounded relation graph. It can propose open-set semantic relations, but its own limitations point directly to the need for explicit geometric evidence and verification on relation edges.

## Follow-up Questions

1. Which Open3DSG errors are semantic hallucinations versus geometry violations?
2. Can a geometry verifier reduce wrong open-set relationships without collapsing open-vocabulary expressivity?
3. Can generated relation text be evaluated with a geometry-consistency metric rather than only mapped to 3DSSG labels?

