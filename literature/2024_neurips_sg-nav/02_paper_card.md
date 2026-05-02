# Paper Card

## Problem

Zero-shot object navigation methods often prompt an LLM with nearby object category text. This loses scene context and spatial/functional relationships, so the LLM cannot reason deeply about where the goal object is likely to be.

## Core Idea

SG-Nav constructs an online hierarchical 3D Scene Graph and prompts an LLM with graph substructures using hierarchical chain-of-thought. The graph stores object, group, and room nodes plus edges, then maps LLM subgraph scores to frontier exploration decisions. It also uses graph-based re-perception to reject false-positive goal detections.

## Input / Output

- Input: streaming posed RGB-D observations, object-goal category text, online 3D scene graph, occupancy map.
- Output: navigation action / selected frontier toward the goal object, with LLM-derived explanation over graph substructures.

## Method

- Build an online hierarchical 3DSG with object, group, and room nodes.
- Incrementally register object nodes using open-vocabulary 3D instance segmentation.
- Build room and group nodes, then connect nodes with affiliation, spatial, and functional edges.
- Reduce graph-construction cost by predicting many object-pair relationships in a single LLM prompt and pruning less informative edges.
- Divide the scene graph into subgraphs and prompt the LLM with hierarchical chain-of-thought.
- Interpolate subgraph probability scores to frontiers and select the highest-scoring frontier.
- Use graph-based re-perception: if the detector sees a possible goal object, accumulate credibility from related subgraphs before stopping.

## Main Claims

- 3D scene graph prompting preserves richer scene context than nearby-object text prompting.
- Hierarchical graph structure and edges improve LLM reasoning for zero-shot object navigation.
- Re-perception helps correct false-positive goal detections.
- SG-Nav achieves stronger zero-shot object navigation performance than prior zero-shot methods across MP3D, HM3D, and RoboTHOR.

## Strengths

- Direct CAND-003 evidence that task decisions can be made over online 3DSG structure.
- Uses graph edges and hierarchy explicitly, not just object category lists.
- Provides navigation metrics across three established ObjectNav benchmarks.
- Includes ablations for scene graph, re-perception, room/group hierarchy, edges, and CoT prompting.
- Code is available on GitHub as of 2026-04-29.

## Limitations

- Still a full navigation system, which is broader than a small first CAND-003 verifier.
- Relies on online 3D instance segmentation; perception errors remain a bottleneck.
- The graph is used for LLM prompting and frontier scoring, not for explicit relation-level geometry violation diagnosis.
- Handles object-goal navigation, not general spatial QA, placement, or manipulation task reasoning.

## Relevance to My Research

SG-Nav is a strong CAND-003 navigation-side baseline. It shows that online 3DSG structure improves LLM zero-shot navigation and that re-perception can correct perception-driven false positives. For CAND-003, the gap is to move from graph prompting and re-perception toward explicit relation-edge evidence and verifier metrics for invalid task outputs.

## Follow-up Questions

1. Can CAND-001 relation evidence support a lightweight SG-Nav-style frontier or target verifier?
2. Can graph-based re-perception be generalized from false-positive goal detection to wrong-relation / impossible-action detection?
3. Would offline target-object decision verification reproduce part of SG-Nav's benefit without simulator complexity?
4. Which SG-Nav errors are semantic reasoning errors, perception errors, or geometry consistency errors?
