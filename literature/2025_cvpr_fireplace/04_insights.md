# Insights

## Facts

- FirePlace integrates MLLM common-sense reasoning with explicit geometric constraints.
- Its constraint library includes Parallel, CloseTo, FarFrom, InfrontPlane, Contact, and NoOverhang.
- It evaluates physical feasibility, semantic alignment, plausibility, and visibility.

## Paper Claims

- MLLMs struggle with precise 3D spatial reasoning and fine-grained geometry unless supported by external 3D tools.
- Fine-grained geometry is more expressive than bounding boxes for placement tasks.

## Inferences

- FirePlace provides a concrete design pattern for CAND-001: semantic proposal first, geometric verification second.
- A 3DSG edge could store the same kind of constraint evidence FirePlace uses for object placement.
- The thesis contribution should avoid depending on MLLM-as-judge alone; deterministic geometry metrics are needed.

## Connection to Field Trends

- Bridges LLM/VLM reasoning and explicit 3D geometric constraints.
- Shows why "semantic reasoning" alone is insufficient for 3D tasks.

## Possible Contribution Angles

- Translate FirePlace-style constraints into edge-level relation verifiers for `on`, `inside`, `near`, `supporting`, `attached to`, `in front of`.
- Use geometry violation rate as a metric for open-vocabulary relation graphs.
- Evaluate whether MLLM relation proposals become more reliable after constraint-based filtering.

## What Would Change This Assessment

- If relation-level constraint extraction from noisy point clouds is unreliable, the project should start with mesh-quality scenes or a subset of geometric predicates.

