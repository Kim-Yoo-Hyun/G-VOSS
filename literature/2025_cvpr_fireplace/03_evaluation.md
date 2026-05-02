# Evaluation

## Dataset / Benchmark

- 50 photorealistic 3D scenes with fixed camera viewpoints.
- 266 placement tasks created by selecting an object, captioning its placement, removing it, then evaluating whether methods place it back appropriately.

## Splits

The paper describes a custom evaluation setup rather than a standard train/test split for 3DSG.

## Metrics

- Min L2 Error: closest translation error across tries.
- Mean L2 Error: average translation error.
- Energy Score: proportion of generated constraints with low energy at ground-truth placements.
- Plausibility Score: Gemini-based evaluation from 1 to 4.
- Visibility Score: whether the inserted object remains observable in the placement rendering.
- Human preference study: physics, semantic alignment, common sense.

## Baselines

- LayoutGPT
- Holodeck
- Ablations: no constraints, no visual selection, no fine-grained geometry, no common-sense pruning, no visual scaling

## Main Results

- FirePlace reports lower L2 errors than LayoutGPT and Holodeck.
- Reported mean L2 error: LayoutGPT 132.96 cm, Holodeck 137.60 cm, FirePlace 69.89 cm.
- Reported plausibility score: LayoutGPT 2.14, Holodeck 2.13, FirePlace 2.95.
- User preference study reports FirePlace preferred over Holodeck and LayoutGPT on physics, semantics, and common sense.
- Human judgments agree with plausibility metrics 89.82% of the time when a clear winner is decided.

## Reproducibility Notes

- Public code/project page was not found during this pass.
- The evaluation depends on custom photorealistic 3D scenes and placement task generation.

## Evaluation Weaknesses

- Not directly a 3D scene graph benchmark.
- Uses MLLM-as-judge for plausibility; useful but should be paired with deterministic geometric checks for a thesis.
- Object placement constraints do not cover all 3DSG relation types, especially semantic/functional relations.

