# Insights

## Facts

- 3D-VCD is listed as CVPR 2026 on the official project page and as accepted at CVPR 2026 in the arXiv comments.
- It builds distorted 3D scene graphs through semantic and geometric perturbations.
- It evaluates on 3D-POPE and HEAL.
- It is training-free and operates at inference time.
- Project page says code and data are coming soon as of 2026-04-29.

## Paper Claims

- Existing 2D inference-time hallucination mitigation does not transfer cleanly to embodied 3D reasoning.
- 3D hallucinations should be tested by perturbing structured 3D contexts, not only pixels.
- Contrastive decoding over original and distorted 3D scene graphs improves grounded reasoning.

## Inferences

- 3D-VCD makes "scene-graph perturbation for hallucination mitigation" a prior-art boundary for CAND-003.
- CAND-003 should avoid claiming novelty from negative scene graph contexts alone.
- A stronger thesis gap is verifier-oriented: identify which relation, object, or geometry constraint made an answer/action invalid.
- CAND-001 edge evidence could support more targeted perturbations than 3D-VCD's object-category and coordinate/extent corruptions.

## Connection to Field Trends

- Confirms that 3D-LLM evaluation is moving toward hallucination and grounded reliability.
- Connects 3DSG representation to inference-time reliability, not only representation or retrieval.
- Supports CAND-003's focus on invalid decision rate and hallucination rate as first-class metrics.

## Possible Contribution Angles

- Compare post-hoc geometry verifier correction against contrastive decoding-style mitigation.
- Use relation-edge evidence to create structured negative contexts, e.g. flip support/contact or relative-position evidence.
- Report whether verifier corrections reduce over-affirmation without suppressing valid rare relations.
- Build a diagnostic taxonomy: nonexistent object, wrong relation, impossible support/contact, unreachable target, semantic mismatch.

## What Would Change This Assessment

- If 3D-VCD code/data are released and easy to run, it should become a direct baseline for CAND-003.
- If relation perturbation ablations become central in a later version, CAND-003 must move further toward explicit verifier metrics and failure decomposition.
