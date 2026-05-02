# Evaluation

## Dataset / Benchmark

Custom large-scale 3DSG environments:

- Office environment: 37 rooms and about 150 interactable assets/objects in the paper text.
- Home environment: three-storey house, 28 rooms and 112 objects.
- PMLR abstract describes environments spanning up to 3 floors and 36 rooms with 140 assets and objects.

Evaluation tasks:

- 90 instructions grouped into four difficulty levels.
- Includes semantic search tasks and long-horizon interactive planning tasks.

## Splits

The evaluation separates:

- Simple Search
- Complex Search
- Simple Planning
- Long-Horizon Planning

## Metrics

Semantic search:

- Success rate in finding a suitable task-relevant subgraph.
- Qualitative comparison with human search sequence.

Causal planning:

- Correctness: whether the plan aligns with the intended task goal.
- Executability: whether the plan satisfies scene graph constraints and can be executed.
- Error types: missing action, missing pose, wrong action, incomplete search, hallucinated nodes.

Scalability:

- Token count for full graph vs collapsed graph.
- Token progression during semantic search.

## Baselines

Semantic search:

- Human baseline
- SayPlan with GPT-3.5
- SayPlan with GPT-4

Causal planning:

- LLM-As-Planner: open-loop full action sequence
- LLM+P: path planner but no iterative replanning
- SayPlan: semantic search + path planner + iterative replanning

## Main Results

Semantic search:

- Human baseline: 100% on simple and complex search in both environments.
- SayPlan with GPT-4: 86.7% on Simple Search and 73.3% on Complex Search in both Office and Home.
- SayPlan with GPT-3.5: 6.6% / 0.0% in Office and 0.0% / 0.0% in Home.

Graph token compression:

- Table 2 reports Office full graph 6,731 tokens vs collapsed graph 878 tokens.
- Table 2 reports Home full graph 6,598 tokens vs collapsed graph 1,817 tokens.
- Paper text reports large initial-token reductions enabled by collapsed graph search.

Causal planning:

- Simple planning correctness: 93.3% for LLM+P, LLM-As-Planner, and SayPlan.
- Simple planning executability: LLM+P 13.3%, LLM-As-Planner 80.0%, SayPlan 100.0%.
- Long-horizon correctness: LLM+P 33.3%, LLM-As-Planner 66.7%, SayPlan 73.3%.
- Long-horizon executability: LLM+P 0.0%, LLM-As-Planner 13.3%, SayPlan 86.6%.
- SayPlan eliminates most missing-action, missing-pose, wrong-action, and incomplete-search errors, but still has hallucinated-node errors in 6.67% of tasks.

## Reproducibility Notes

- Local PDF downloaded from PMLR.
- Project page exists with videos and summary.
- Code was not found in this pass.
- Reproduction requires the custom 3DSG environments, graph simulator, task set, prompts, and path planner integration.

## Evaluation Weaknesses

- Custom task set and environments limit direct comparison.
- Human correctness/executability judgments can be partly subjective.
- Simulator feedback quality depends on manually captured predicates, affordances, and failure messages.
- It evaluates plan feasibility, but not fine-grained metric geometry consistency.
- Assumes a pre-built static scene graph.
