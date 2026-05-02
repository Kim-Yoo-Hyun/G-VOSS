# Paper Card

## Problem

MLLMs have strong high-level semantic/common-sense reasoning, but they are weakly grounded in precise 3D geometry. For object placement, a system must satisfy both semantic plausibility and low-level geometric constraints such as contact, support, surface selection, and non-overhang.

## Core Idea

FirePlace uses an MLLM to propose high-level constraint outlines, then uses explicit 3D tools to resolve objects/surfaces, construct geometric constraints, solve for feasible placements, and finally prune candidates using MLLM common-sense judgment.

## Input / Output

- Input: existing 3D scene, transformable 3D object mesh, language placement instruction, camera/rendering access
- Output: transformation matrix / edited scene placing the new object

## Method

- Stage 1: Generate constraint outlines from language.
- Stages 2-4: Resolve anchor object and interaction surfaces; extract fine-grained planar surfaces; solve geometric constraints.
- Stage 5: Prune feasible placements with MLLM common-sense preference.
- Uses Batched Visual Selection to reduce MLLM selection errors over many candidate objects/surfaces.

## Main Claims

- MLLM semantic reasoning becomes more useful for 3D tasks when paired with explicit geometric processing tools.
- Fine-grained surface-level constraints outperform bounding-box-only placement reasoning.
- FirePlace produces placements that are physically feasible and semantically plausible.

## Strengths

- Directly demonstrates the semantic reasoning + geometric constraint pattern.
- Its constraint library is simple and interpretable.
- Evaluation includes geometry-related metrics and human preference, not only classification recall.
- Useful design reference for edge-level relation verification in 3DSG.

## Limitations

- It is an object placement method, not a 3D scene graph generation method.
- The dataset/task is custom placement-focused, not a standard 3DSG benchmark.
- Relies on rendered visual selection and tool pipelines, which may not map directly to scanned point clouds.

## Relevance to My Research

FirePlace is not a 3DSG baseline, but it strongly supports the thesis that LLM/MLLM semantic commonsense should be grounded through explicit 3D geometry. This pattern can be translated from object placement constraints into scene-graph edge verification.

## Follow-up Questions

1. Can FirePlace-style constraint functions be repurposed as 3DSG edge evidence?
2. Which constraints map cleanly to common 3DSSG predicates?
3. Can relation verification use surfaces and support/contact evidence without requiring full mesh-quality input?

