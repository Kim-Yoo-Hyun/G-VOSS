# Paper Card

## Problem

Open-world interactive object search requires relational semantic reasoning. Embedding similarity can miss task-relevant relations such as room-object containment or object-object co-occurrence, while online LLM planning is too slow and expensive for real-time robot deployment.

## Core Idea

SCOUT searches directly over a 3D Scene Graph by assigning utility scores to rooms, frontiers, objects, and containers. The utility approximates how informative a node is for locating the target query, using LLM-distilled relational priors for room-object containment and object-object co-occurrence.

## Input / Output

- Input: open-vocabulary object query, online 3DSG built from RGB-D observations and pose estimates.
- Output: high-level node to explore, grounded to low-level navigation or manipulation policy.

## Method

- Build an online hierarchical 3DSG with rooms, regions/frontiers, objects/containers, and nested objects.
- Estimate node utility using room-object containment and object-object co-occurrence.
- Generate relational semantic datasets offline by prompting an LLM for household object categories and relation labels/scores.
- Train lightweight MLP models over frozen text embeddings to predict containment and co-occurrence scores.
- During search, score actionable nodes, apply a utility margin, and select a nearby high-utility node.
- Map node affordances to low-level actions such as navigating to a frontier or opening a container.
- Introduce SymSearch, a symbolic benchmark for scalable relational semantic reasoning over 3DSGs.

## Main Claims

- Relational utility models capture search-relevant semantics better than generic text or vision-language embedding similarity.
- Offline LLM distillation can approximate LLM-level relational reasoning with much lower inference cost.
- SCOUT outperforms embedding-based search and matches or exceeds LLM-based planners on symbolic and simulation benchmarks while being much faster.
- SCOUT transfers to real-world mobile manipulation search.

## Strengths

- Very relevant to CAND-003's object search / task decision branch.
- Explicitly introduces a symbolic 3DSG benchmark, SymSearch, for relational semantic reasoning.
- Separates high-level semantic reasoning from low-level navigation/manipulation execution.
- Reports SR, SPL, high-level steps, inference time, and real-world failure modes.
- Provides a practical alternative to online LLM calls.

## Limitations

- arXiv preprint / under review as of 2026-04-29.
- Code is not yet available according to the project page.
- Depends heavily on the quality of generated 3DSGs and real-time perception.
- Utility priors encode typical household relations and may fail for user-specific or unusual object placement.
- It evaluates search utility rather than explicit geometry violation checking.

## Relevance to My Research

SCOUT makes relational semantic reasoning over 3DSG a strong prior-art boundary for CAND-003. It suggests that the first CAND-003 benchmark should be careful: object search can quickly become a full robot/search project. The narrower thesis angle is to use relation-level geometry evidence to verify or correct LLM/VLM task outputs, while SCOUT/SymSearch can inform search-oriented evaluation.

## Follow-up Questions

1. Can SymSearch be adapted into an offline verifier benchmark without running full embodied simulation?
2. Can CAND-001 edge evidence distinguish relational semantic priors from geometric consistency?
3. Can verifier metrics complement SCOUT's utility-search metrics by identifying invalid relation assumptions?
4. Would learned utility from LLM priors conflict with measured 3D geometry in unusual scenes?
