# Insights

## Facts

- OpenFunGraph is a CVPR 2025 Highlight paper.
- It introduces functional 3D scene graphs with object nodes, interactive element nodes, and functional relationship edges.
- It evaluates on extended SceneFun3D and a newly collected FunGraph3D dataset.
- It compares against adapted Open3DSG and ConceptGraphs baselines.
- It demonstrates downstream 3D inventory question answering and robotic manipulation.

## Paper Claims

- Existing 3D scene graph methods are mostly constrained to object nodes and spatial relationships.
- Functional reasoning requires modeling interactive elements such as handles, knobs, buttons, switches, and remote controls.
- Open-vocabulary foundation models can infer functional 3D scene graphs without task-specific training.
- Sequential functional reasoning is more effective than asking an LLM to infer all functional edges at once.

## Inferences

- This paper raises the novelty bar for CAND-001. A broad "open-vocabulary semantic 3DSG" thesis would be too close to existing top-tier work.
- CAND-001 should keep the first thesis prototype on geometry-checkable relation verification, not functional relationship discovery.
- Functional relations are attractive but require part-level interactive element detection, common-sense reasoning, and sometimes interaction evidence. That would expand the thesis into robotics/affordance territory.
- OpenFunGraph's evaluation decomposition is valuable for CAND-001: node detection, node association, edge prediction, and overall triplet metrics can inspire a cleaner relation-grounding evaluation.

## Connection to Field Trends

- Confirms that 3D scene graph research is moving beyond static object-object spatial relationships.
- Connects 3DSG to affordance understanding, VLM/LLM reasoning, 3D QA, and robotic manipulation.
- Shows that Open3DSG and ConceptGraphs are now baseline systems rather than distant related work.
- Supports the trend that evaluation is moving toward downstream usability and open-vocabulary graph retrieval.

## Possible Contribution Angles

- Keep CAND-001 core scope: geometry-grounded verification for spatial/support/containment/proximity relation edges.
- Add an optional extension: local functional relation verification where geometry can help, e.g., handle attached to door, knob part of cabinet.
- Avoid remote functional relations in the first prototype because they can require interaction videos or world knowledge not inferable from static geometry.
- Borrow OpenFunGraph's node/triplet recall style but add geometry-consistency and violation metrics.

## What Would Change This Assessment

- If the research goal shifts toward robotics manipulation, OpenFunGraph becomes a primary baseline rather than a novelty-boundary paper.
- If FunGraph3D is easy to access and small enough to prototype quickly, it can be a secondary benchmark after 3DSSG.
- If CAND-001 includes functional relations, the hypothesis must separate local geometry-verifiable relations from remote common-sense relations.
