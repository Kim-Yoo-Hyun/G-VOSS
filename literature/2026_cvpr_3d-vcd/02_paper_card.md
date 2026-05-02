# Paper Card

## Problem

3D-LLM embodied agents can produce plausible but ungrounded outputs. In 3D environments, hallucinations come from object presence, spatial layout, and geometric grounding failures rather than only 2D pixel inconsistencies.

## Core Idea

3D-VCD performs inference-time contrastive decoding over structured 3D scene graphs. It compares model logits under the original 3D context and a distorted 3D context, then suppresses tokens that remain likely even when the scene graph has been semantically or geometrically corrupted.

## Input / Output

- Input: object-centric 3D scene representation or scene graph, textual query/task, MLLM.
- Output: grounded text response with hallucination-prone tokens suppressed at decoding time.

## Method

- Serialize object-centric 3D scene graph context with object categories, centroids, and extents.
- Construct distorted scene graph variants through semantic and geometric perturbations.
- For 3D-POPE, distort object categories, coordinates, and extents.
- For HEAL, use paired clean/adversarial task contexts as contrastive contexts.
- Compute original logits and distorted-context logits.
- Fuse logits as contrastive decoding: original context is promoted and distorted context is penalized.
- Requires no retraining and no architecture change.

## Main Claims

- 3D-VCD is the first inference-time visual contrastive decoding framework for hallucination mitigation in 3D embodied agents.
- Structured 3D perturbations are more appropriate for embodied hallucination mitigation than 2D pixel perturbations.
- Training-free contrastive decoding improves grounded reasoning across 3D-POPE and HEAL.

## Strengths

- Very direct CAND-003 evidence for hallucination mitigation over structured 3D representations.
- Uses explicit semantic/geometric perturbations of scene graphs.
- Evaluates with hallucination-oriented metrics, not only task accuracy.
- Training-free and potentially easy to plug into existing 3D-LLM systems.

## Limitations

- Code and data are marked "coming soon" on the project page as of 2026-04-29.
- It mitigates hallucination at decoding time, but does not itself build better relation evidence.
- Main formulation is object-centric; relation semantics are perturbed structurally in ablations but not treated as inspectable relation-edge evidence.
- It improves grounding but does not directly decompose failures into perception error, graph error, semantic reasoning error, and geometry violation.

## Relevance to My Research

3D-VCD is a close CAND-003 competitor because it already uses distorted 3D scene graphs for inference-time hallucination mitigation. CAND-003 should therefore focus on explicit verifier metrics and relation-evidence provenance rather than claiming novelty from perturbing 3D scene graphs alone.

## Follow-up Questions

1. Can CAND-001 edge evidence be used to generate more meaningful negative contexts than random coordinate/extent noise?
2. Can verifier outcomes be combined with contrastive decoding, or should they be evaluated as a separate post-hoc correction layer?
3. Which CAND-003 metric best captures "corrected invalid task output" beyond Yes-rate and CHAIR?
4. Does perturbing relation edges expose different hallucination patterns from perturbing object categories and extents?
