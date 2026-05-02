# Paper Card

## Problem

Embodied agents need compact scene memory for long-horizon exploration and reasoning. The paper argues that object-centric 3D scene graphs oversimplify spatial relationships by storing isolated objects and restrictive textual relations, making nuanced spatial questions difficult.

## Core Idea

3D-Mem represents explored regions with Memory Snapshots, which are informative multi-view images covering clusters of co-visible objects and their surroundings. It represents unexplored regions with Frontier Snapshots, which are glimpses of navigable frontiers. A VLM agent reasons over filtered memory/frontier snapshots to answer questions or choose exploration targets.

## Input / Output

- Input: RGB-D observations, camera poses, object detections, occupancy/frontier map, task question or navigation goal.
- Output: answer to embodied question, selected frontier/object/navigation target, and updated scene memory.

## Method

- Detect object instances and build an object set from RGB-D observations.
- Use co-visibility clustering to select Memory Snapshots that capture object clusters and background context.
- Add Frontier Snapshots for unexplored navigable regions.
- Incrementally update object sets, memory snapshots, and frontier snapshots during exploration.
- Use Prefiltering: ask the VLM to rank task-relevant object categories, then keep only snapshots containing those categories.
- Use VLM reasoning over memory and frontier images to decide whether to answer, explore, or navigate.
- Use Habitat-sim pathfinding for navigation in experiments.

## Main Claims

- Image-based memory snapshots capture spatial/contextual cues that object-centric 3DSG text relations miss.
- Frontier snapshots let the agent reason over both known and potentially useful unexplored regions.
- 3D-Mem improves embodied QA and lifelong object navigation over ConceptGraphs and VLM exploration baselines.
- The framework is training-free with respect to the VLM agent and can adapt to real robots.

## Strengths

- Directly states a limitation of object-centric 3DSG textual relations, which is central to CAND-003.
- Evaluates on active embodied QA, episodic-memory QA, and lifelong navigation.
- Uses strong baselines including ConceptGraphs with frontier snapshots and Explore-EQA.
- Code is public as of 2026-04-30.
- Gives concrete evidence that representation choice affects spatial reasoning and exploration efficiency.

## Limitations

- It is a broad embodied memory/exploration system, not a 3DSG relation verifier.
- The solution moves away from explicit 3DSG edges toward image snapshots, so it is not directly a 3D Scene Graph contribution.
- Evaluation depends on VLMs, GPT-style answer scoring, Habitat simulation, and subsets due to resource limits.
- Snapshot reasoning may improve answers without providing explicit relation-level provenance or geometry violation diagnosis.
- It does not solve relation-edge representation or geometry consistency metrics for 3DSG.

## Relevance to My Research

3D-Mem is a warning for CAND-003: if 3DSG edges stay as restrictive textual relations, VLM/image-memory systems can be more flexible for spatial reasoning. For CAND-003, the response should not be "use 3DSG text relations"; it should be "make 3DSG relation edges evidence-bearing and verifiable enough to support task reasoning."

## Follow-up Questions

1. Which 3D-Mem failure modes are caused by missing explicit geometry versus VLM image reasoning limits?
2. Can CAND-001 edge evidence address the critique that 3DSG relations are too restrictive?
3. Can A-EQA or EM-EQA provide a geometry-checkable subset for offline verifier evaluation?
4. Would image snapshots and explicit 3DSG geometry evidence be complementary rather than competing representations?
