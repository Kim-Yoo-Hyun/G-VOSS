# Insights

## Facts

- SG-Nav is a NeurIPS 2024 paper.
- It constructs an online hierarchical 3DSG with object, group, and room nodes.
- It uses hierarchical chain-of-thought prompting over graph substructures for zero-shot object navigation.
- It evaluates on MP3D, HM3D, and RoboTHOR.
- It reports code on GitHub.

## Paper Claims

- 3D scene graph prompting provides richer context than prompting LLMs with nearby object category text.
- Graph hierarchy and edges improve zero-shot ObjectNav decision making.
- Graph-based re-perception helps the agent give up false-positive goal objects.

## Inferences

- SG-Nav reinforces that CAND-003 should not become "LLM reasons over 3DSG for navigation" as a broad claim; this is already done.
- Its re-perception mechanism is close in spirit to verifier/refiner logic, but it verifies goal-object credibility rather than relation-level geometric constraints.
- For CAND-003, a safer contribution is offline task-output verification using explicit relation evidence before moving into full navigation simulation.

## Connection to Field Trends

- Strengthens the navigation/search branch of LLM/VLM task reasoning on 3DSG.
- Shows that edge and hierarchy design matter for downstream task success.
- Connects 3DSG to explainable frontier selection and perception-error correction.

## Possible Contribution Angles

- Use SG-Nav as a downstream motivation, not first reproduction target.
- Borrow the idea of re-perception as verifier feedback, but apply it to relation claims or target-object decisions.
- Define an offline benchmark where the system must reject LLM target decisions inconsistent with support/contact/relative-position evidence.
- Compare text-only graph prompts, node-only graph prompts, and evidence-bearing relation-edge prompts.

## What Would Change This Assessment

- If CAND-003 shifts to embodied navigation, SG-Nav becomes a primary baseline.
- If CAND-003 stays offline, SG-Nav should remain a motivation and metric reference rather than a reproduction target.
