# Paper Card

## Problem

기존 3D Scene Graph는 대부분 object node와 spatial relation edge에 집중한다. 이런 graph는 `on`, `in`, `near`, `mounted on` 같은 공간 관계를 표현할 수 있지만, 실제 interaction에 필요한 `handle opens cabinet`, `switch controls light`, `remote controls TV` 같은 functional relationship은 잘 표현하지 못한다.

## Core Idea

OpenFunGraph는 traditional 3DSG를 functional 3D scene graph로 확장한다. Graph는 object node, interactive element node, functional relationship edge로 구성되며, relation은 local relation과 remote relation으로 나뉜다. Training data가 부족하므로 VLM/LLM/foundation model을 이용해 open-vocabulary 방식으로 node detection, node description, functional edge inference를 수행한다.

## Input / Output

- Input: posed RGB-D frames of an unseen indoor environment.
- Intermediate nodes: objects `O` and interactive elements `I`, such as handles, knobs, buttons, switches, remote controls.
- Output: directed functional 3D scene graph `G = (O, I, R)`.
- Edge direction: interactive element node -> object node.
- Edge type: functional relationship description, with local or remote relation.

## Method

- Detect object candidates with RAM++ tags and GroundingDINO prompts.
- Generate interactive element prompts using GPT-4 from detected object tags, then detect small interactive elements with object-assisted prompts such as `door. handle`.
- Fuse multi-view 2D detections into 3D node candidates using posed RGB-D geometry.
- Generate multi-view language descriptions for object nodes using LLAVA v1.6 and GPT-4 summarization.
- Generate descriptions for small interactive elements using enlarged crops and visual highlighting.
- Infer local functional relationships using 3D spatial overlap plus LLM common-sense reasoning.
- Infer remote functional relationships using a sequential strategy:
  - LLM proposes likely object targets for unassigned interactive elements.
  - VLM assesses pair feasibility from top views.
  - LLM assigns relative confidence and relationship descriptions with global context.
- Combine local and remote subgraphs into a final functional 3D scene graph.

## Main Claims

- Functional 3D scene graphs extend traditional 3DSG beyond spatial relationships.
- Interactive elements should be first-class graph nodes.
- Functional relationships can be inferred in an open-vocabulary way using VLM/LLM common-sense knowledge.
- OpenFunGraph outperforms adapted Open3DSG and ConceptGraphs baselines on functional graph prediction.
- Functional 3D scene graphs support downstream 3D question answering and robotic manipulation.

## Strengths

- Very strong novelty-boundary paper for CAND-001.
- Makes explicit that spatial relation-only 3DSG is insufficient for high-level interaction.
- Introduces a dataset and evaluation protocol for functional 3D scene graphs.
- Separates node detection, node association, edge prediction, and overall triplet recall.
- Shows that simply prompting Open3DSG or ConceptGraphs for functional relationships is not enough.
- Provides concrete examples where remote relation reasoning needs more than geometric proximity.

## Limitations

- Heavily depends on foundation models and prompt quality.
- Functional relation inference is not trained end-to-end and may inherit VLM/LLM hallucination.
- Functional relationships can require evidence from interaction videos; static geometry alone is insufficient for some edges.
- The datasets are relatively small: FunGraph3D has 14 scenes.
- The evaluation uses embedding-based open-vocabulary retrieval, which may not fully capture physical correctness.
- The method targets functional relations, not the geometry-consistency verification of ordinary spatial predicates.

## Relevance to My Research

OpenFunGraph is the clearest warning that CAND-001 should not be framed as "semantic+geometry 3DSG" in a broad sense. Top-tier work already expands 3DSG into open-vocabulary functional reasoning with interactive elements and LLM/VLM inference. For CAND-001, this suggests a narrower initial scope: start with geometry-checkable spatial/support/containment relations and explicitly evaluate edge evidence and violation. Functional relation can become a secondary extension after a spatial relation verifier is stable.

## Follow-up Questions

1. Should CAND-001 include functional relations, or keep them out of the first thesis prototype?
2. Can local functional relations be partially verified with geometry evidence such as overlap/contact/support?
3. How should remote functional relations be represented if static geometry cannot verify them?
4. Can CAND-001 borrow OpenFunGraph's decomposition into node association, edge prediction, and overall triplet recall?
5. Is FunGraph3D accessible enough to be used as a secondary benchmark?
