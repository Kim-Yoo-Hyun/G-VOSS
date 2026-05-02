# Paper Card

## Problem

LLM-based 3D scene understanding methods often encode objects with coordinates, point features, or visual features, but do not explicitly encode semantic relationships between objects. This weakens queries that depend on relations such as left of, behind, near, or on.

## Core Idea

3DGraphLLM builds a learnable 3D scene graph representation for LLM input. Each object is represented by object identifier tokens, 2D/3D object features, and a small local subgraph of semantic relation embeddings to its nearest neighbors. The graph is flattened into token embeddings and fed to an LLM for 3D referred object grounding, dense scene captioning, and 3D QA.

## Input / Output

- Input: object point-cloud proposals from ground-truth or instance segmentation, multi-view 2D features, 3D object features, semantic relation features, natural-language query.
- Output: object identifier(s), caption, or text answer depending on the 3D vision-language task.

## Method

- Use object point clouds as scene graph nodes.
- Add learnable object identifier tokens to the LLM vocabulary.
- Extract 2D object features with DINOv2 from projected multi-view masks.
- Extract 3D object features with Uni3D.
- Extract semantic edge features with VL-SAT before the relation classification head.
- Project 2D object, 3D object, and semantic relation features into the LLM token embedding space.
- Flatten the graph by representing each object as a local k-nearest-neighbor subgraph of triplets `(object_i, relation_ij, object_j)`.
- Use `k = 2` nearest neighbors in main experiments to reduce token length.
- Train in two stages: pre-train with ground-truth instance segmentation, then fine-tune with predicted instance segmentation.

## Main Claims

- Adding semantic scene graph edges improves LLM performance on 3D vision-language tasks compared with object-only learnable representations.
- A compact local-subgraph representation can use far fewer tokens than text-heavy scene descriptions.
- The method improves ScanRefer, Multi3DRefer, Scan2Cap, ScanQA, and SQA3D over the Chat-Scene baseline.

## Strengths

- Direct evidence that semantic 3DSG relations are useful as LLM input, not only as post-hoc labels.
- Covers multiple offline 3D vision-language tasks relevant to CAND-003.
- Includes ablations for semantic edges, object proposal quality, nearest-neighbor count, and graph-token representation.
- Code is public as of 2026-04-30.
- Provides a useful baseline for "graph-to-LLM representation without explicit verifier."

## Limitations

- The contribution is representation learning, not explicit geometry verification or violation diagnosis.
- Relation features come from VL-SAT latent semantic edge features and are not exposed as inspectable geometric evidence.
- Evaluation uses standard task metrics, not geometry violation rate, hallucination taxonomy, or verifier precision.
- Training is non-trivial: the paper reports LoRA fine-tuning on 4 NVIDIA A100 GPUs for about 24 hours.
- The graph token count still grows with edge count, so richer relation neighborhoods are resource-limited.

## Relevance to My Research

3DGraphLLM sets a clear boundary for CAND-003: using 3DSG semantic relations as LLM input is already an ICCV 2025 direction. CAND-003 should not propose only a better graph serialization or tokenization. The defensible gap is to add explicit relation-level geometry evidence and task-output verification on top of, or against, graph-to-LLM representation baselines.

## Follow-up Questions

1. Can CAND-003 use 3DGraphLLM-style outputs as unverified LLM/VLM task decisions?
2. Which 3DGraphLLM benchmarks contain geometry-checkable answer or object-reference failures?
3. Can relation-edge evidence from CAND-001 be attached to the same local subgraph triplets?
4. How often do semantic edge embeddings improve answers while still hiding geometry inconsistency?
