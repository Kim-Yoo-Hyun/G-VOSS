# Insights

## Facts

- SayPlan is a CoRL 2023 Oral paper.
- It uses 3DSG hierarchy for LLM semantic search and task planning.
- It combines an LLM, a classical path planner, and a scene graph simulator.
- It evaluates 90 tasks across large-scale office and home environments.
- It reports large gains in plan executability from iterative replanning.

## Paper Claims

- Hierarchical 3DSGs make LLM task planning scalable in large multi-room/multi-floor environments.
- Semantic search lets the LLM reason over task-relevant subgraphs instead of the full scene graph.
- Iterative replanning with scene graph simulator feedback corrects infeasible actions and avoids planning failures.

## Inferences

- SayPlan makes `3DSG + LLM task planning + verifier feedback` prior art for CAND-003.
- CAND-003 should not become a broad LLM robot planner unless that becomes the thesis direction.
- The most useful takeaway is the evaluation decomposition: semantic search success, plan correctness, plan executability, and error types.
- For a smaller thesis cut, CAND-003 can borrow the verifier-feedback idea but apply it to offline graph-query/spatial-answer decisions rather than full mobile manipulation plans.

## Connection to Field Trends

- Anchors the CoRL 2023 starting point for LLM task reasoning over 3DSG.
- Shows that downstream usability metrics are already important: executability matters more than only language plausibility.
- Connects 3DSG hierarchy, semantic search, and verification feedback.

## Possible Contribution Angles

- Define an offline `answer executability` or `decision validity` metric analogous to SayPlan's plan executability.
- Use CAND-001 geometry evidence as a fine-grained verifier below SayPlan's symbolic simulator layer.
- Evaluate whether geometry-aware feedback reduces invalid LLM outputs without building a full robot stack.
- Create a taxonomy aligned with SayPlan errors: missing action/object, unreachable target, wrong relation, hallucinated node, geometry violation.

## What Would Change This Assessment

- If SayPlan code/environments are released and easy to run, it becomes a strong baseline for CAND-003's planning side.
- If CAND-003 shifts to navigation/search simulation, SayPlan should be treated as a primary baseline rather than only a literature anchor.
- If the thesis remains offline QA/query verification, SayPlan is mainly a design and metric reference.
