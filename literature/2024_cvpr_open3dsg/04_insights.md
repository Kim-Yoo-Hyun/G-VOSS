# Insights

## Facts

- Open3DSG predicts open-vocabulary object labels and open-set relationships from 3D point clouds.
- It uses OpenSeg-like features for object nodes and InstructBLIP/LLM-style features for predicate edges.
- It quantitatively evaluates on 3DSSG using standard object/predicate/triplet recall metrics.
- The paper explicitly mentions relationship diversity limitations, LLM hallucinations, and imperfect geometric understanding.

## Paper Claims

- Generative LLM-based relationship prediction is better suited than CLIP-like discriminative querying for compositional relationships.
- Open3DSG can express rare and specific object/relation descriptions beyond fixed training labels.

## Inferences

- Open3DSG is a strong semantic proposal model, but not a complete semantic+geometry verification model.
- Its limitations are well aligned with CAND-001: relation hallucination and geometric inconsistency can be reframed as edge-level grounding failures.
- The most promising extension is not to replace Open3DSG, but to add relation evidence: support/contact/containment/relative pose/topology confidence.

## Connection to Field Trends

- Fits the open-vocabulary / open-world 3DSG trend.
- Provides a bridge from VLM/LLM semantic reasoning to 3D scene graph edges.
- Highlights that open-vocabulary expressivity needs geometry-aware validation.

## Possible Contribution Angles

- Geometry-grounded verifier for Open3DSG relation outputs.
- New metric: semantic relation correctness conditioned on geometry consistency.
- Edge schema that stores both generated semantic relation and explicit geometric evidence.

## What Would Change This Assessment

- If Open3DSG already exposes robust geometry-grounded edge evidence internally and evaluates it, the novelty of CAND-001 would shrink.
- If open-set relationship evaluation cannot be made reliable, the project should pivot toward closed-set geometry consistency first.

