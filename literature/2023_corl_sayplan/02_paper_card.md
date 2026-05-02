# Paper Card

## Problem

LLM-based robot planners need grounding in large multi-room and multi-floor environments. Passing the full environment to the LLM does not scale, and open-loop LLM plans often contain infeasible actions or hallucinated objects.

## Core Idea

SayPlan uses a hierarchical 3D Scene Graph as a scalable planning substrate. The LLM first performs semantic search over a collapsed 3DSG to identify a task-relevant subgraph, then generates a high-level plan. A classical path planner fills navigation steps, and a scene-graph simulator verifies the plan and gives feedback for iterative replanning.

## Input / Output

- Input: natural-language task instruction, pre-built hierarchical 3DSG, prompt, memory of expanded nodes.
- Output: executable high-level plan for a mobile manipulator, with navigation steps inserted by a path planner.

## Method

- Collapse the full 3DSG to expose only high-level nodes.
- Let the LLM call `expand_node` and `contract_node` to search for task-relevant rooms/assets/objects.
- Use a task-specific explored subgraph for planning instead of the full graph.
- Use a classical path planner, such as Dijkstra, to connect high-level navigation nodes.
- Verify the generated full plan in a scene graph simulator.
- Feed simulator error messages back to the LLM until the plan is executable or the replanning limit is reached.

## Main Claims

- Hierarchical 3DSGs let LLM planners scale to large indoor environments.
- Semantic search reduces token footprint while preserving task-relevant context.
- Scene-graph simulator feedback and iterative replanning improve executability by correcting infeasible actions.

## Strengths

- Foundational CAND-003 reference for `3DSG + LLM task planning`.
- Cleanly separates semantic search, causal planning, path planning, and verification.
- Uses explicit graph predicates, affordances, states, and topology rather than only text.
- Evaluates both correctness and executability, which is closer to CAND-003's invalid decision metric than ordinary QA accuracy.

## Limitations

- Requires a pre-built 3DSG.
- Assumes static objects after map generation.
- Depends on the scene graph simulator's predicate and affordance coverage.
- LLM still struggles with negation, distance-based reasoning, count-based reasoning, and hallucinated nodes.
- Custom environments/tasks make direct benchmark comparison difficult.

## Relevance to My Research

SayPlan is the foundational baseline for CAND-003's planning/search side. It already uses a verifier-like scene graph simulator, so CAND-003 should not claim novelty from iterative replanning alone. The useful gap is finer geometry-aware verification of task outputs and explicit decomposition of invalid decisions into semantic, graph, and geometry errors.

## Follow-up Questions

1. Can CAND-001 relation evidence serve as a lightweight scene graph simulator for spatial QA/task-query decisions?
2. Can CAND-003 report verifier correction precision instead of only plan executability?
3. Can a first prototype avoid full robot execution by evaluating target-object or spatial-answer verification offline?
4. What parts of SayPlan's simulator correspond to geometry-checkable 3DSG relation edges?
