# Evaluation

## Dataset / Benchmark

- 3D-POPE: object-presence hallucination probing benchmark for 3D-LLMs.
- HEAL: embodied hallucination probing set with scene-task inconsistencies.

## Splits

3D-POPE:

- Random
- Popular
- Adversarial

HEAL probes include:

- Distractor Injection
- Object Removal
- Scene-Object Synonymous
- Scene-Task Contradiction
- Baseline comparison

## Metrics

3D-POPE:

- Accuracy
- Precision
- Recall
- F1-score
- Yes-rate as a proxy for over-affirmation / hallucination bias

HEAL:

- CHAIR object hallucination rate
- CHAIR state hallucination rate

## Baselines

3D-POPE:

- Random baseline
- 3D-LLM
- 3D-VisTA
- LEO

HEAL:

- Llama-3-8B-Instruct
- Qwen-14B-Instruct
- Gemma-2-9b-it
- DS-R1-Distil-LLaMA-8B

## Main Results

3D-POPE:

- Random split: 3D-VCD reports precision 62.16, recall 92.90, F1 74.48, accuracy 67.99, Yes-rate 75.15.
- Popular split: 3D-VCD reports precision 52.35, recall 92.86, F1 66.95, accuracy 54.00, Yes-rate 89.02.
- Adversarial split: 3D-VCD reports precision 52.90, recall 92.59, F1 67.32, accuracy 54.92, Yes-rate 87.82.
- Compared with 3D-LLM on Random, Yes-rate drops from 99.81 to 75.15 and accuracy increases from 50.07 to 67.99.

HEAL:

- Under Distractor Injection, Qwen-14B-Instruct state hallucination drops from 16.45 to 5.00 with 3D-VCD.
- Qwen-14B-Instruct object hallucination drops from 4.13 to 3.55.
- Llama-3-8B-Instruct object hallucination drops from 2.58 to 2.39, but its state hallucination rises from 9.49 to 12.43 in the reported table.
- Supplementary analysis reports strong Scene-Task Contradiction improvement for Qwen-14B, object hallucination 53.9 to 1.5.

## Reproducibility Notes

- Local PDF downloaded.
- Project page exists, but code and data are marked "coming soon" as of 2026-04-29.
- 3D-POPE evaluation requires object-centric scene graph JSON with categories, centroids, and extents.
- HEAL evaluation uses adversarial/clean prompt pairs and scene descriptions.

## Evaluation Weaknesses

- 3D-VCD improves hallucination metrics but does not directly evaluate downstream navigation or manipulation task success.
- Some HEAL improvements are model/probe dependent, so "reduces hallucination" should be read per probe/model rather than as uniformly true.
- Yes-rate and CHAIR are useful but do not expose which specific geometric relation was violated.
- Relation-edge provenance and verifier precision are not evaluated.
