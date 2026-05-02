# Evaluation

## Dataset / Benchmark

- A-EQA / OpenEQA: active embodied question answering in HM3D scenes.
- EM-EQA: episodic-memory embodied QA with provided trajectories from ScanNet and HM3D.
- GOAT-Bench: multimodal lifelong object navigation in unknown HM3D scenes.

## Splits

- A-EQA has 557 questions from 63 HM3D scenes. Main evaluation uses a 184-question subset also referenced by OpenEQA.
- EM-EQA contains over 1600 questions from 152 ScanNet and HM3D scenes.
- GOAT-Bench main evaluation uses a 1/10-size subset of the `Val Unseen` split: one exploration episode for each of 36 scenes, totaling 278 navigation subtasks.
- The appendix also reports full-set numbers for A-EQA and GOAT-Bench.

## Metrics

- A-EQA: `LLM-Match`, `LLM-Match SPL`.
- EM-EQA: average number of frames and `LLM-Match`.
- GOAT-Bench: success rate and SPL.
- The paper uses GPT-style LLM matching for open-ended answer evaluation.

## Baselines

- Blind LLMs: GPT-4, GPT-4o.
- Question-agnostic exploration: ConceptGraphs scene-graph captions, Sparse Voxel Map captions, LLaVA frame captions, Multi-Frame.
- VLM exploration: Explore-EQA, ConceptGraphs with Frontier Snapshots.
- GOAT-Bench baselines: Modular GOAT, Modular CLIP on Wheels, SenseAct-NN Skill Chain, SenseAct-NN Monolithic.
- Ablation: 3D-Mem without memory.

## Main Results

### A-EQA

| Method | LLM-Match | LLM-Match SPL |
| --- | ---: | ---: |
| GPT-4 | 35.5 | N/A |
| GPT-4o | 35.9 | N/A |
| CG Scene-Graph Captions | 34.4 | 6.5 |
| SVM Scene-Graph Captions | 34.2 | 6.4 |
| LLaVA-1.5 Frame Captions | 38.1 | 7.0 |
| Multi-Frame | 41.8 | 7.5 |
| Explore-EQA | 46.9 | 23.4 |
| CG w/ Frontier Snapshots | 47.2 | 33.3 |
| 3D-Mem | 52.6 | 42.0 |
| Human Agent | 85.1 | N/A |

### EM-EQA

| Method | Avg. Frames | LLM-Match |
| --- | ---: | ---: |
| Blind LLM | 0 | 35.5 |
| CG Captions | 0 | 34.4 |
| SVM Captions | 0 | 34.2 |
| Frame Captions | 0 | 38.1 |
| Multi-Frame | 3.0 | 48.1 |
| 3D-Mem | 3.1 | 57.2 |
| Human | Full | 86.8 |

### GOAT-Bench

| Method | Success Rate | SPL |
| --- | ---: | ---: |
| Modular GOAT | 24.9 | 17.2 |
| Modular CLIP on Wheels | 16.1 | 10.4 |
| SenseAct-NN Skill Chain | 29.5 | 11.3 |
| SenseAct-NN Monolithic | 12.3 | 6.8 |
| 3D-Mem w/o memory, open-sourced VLM | 40.6 | 14.6 |
| 3D-Mem, open-sourced VLM | 49.6 | 29.4 |
| Explore-EQA, GPT-4o | 55.0 | 37.9 |
| CG w/ Frontier Snapshots, GPT-4o | 61.5 | 45.3 |
| 3D-Mem w/o memory, GPT-4o | 58.6 | 38.5 |
| 3D-Mem, GPT-4o | 69.1 | 48.9 |

### Full-Set Reference

- GOAT-Bench full set: 3D-Mem success rate 62.9, SPL 44.7.
- A-EQA full set: 3D-Mem LLM-Match 53.3, LLM-Match SPL 38.0.

## Reproducibility Notes

- Code is public: https://github.com/UMass-Embodied-AGI/3D-Mem
- The repository includes scripts for A-EQA and GOAT-Bench evaluation.
- Reproduction requires HM3D train/val data, Habitat-sim, OpenAI API setup for GPT-4o experiments, and several 3D/vision dependencies.
- The official repository provides A-EQA subsets and GOAT-Bench `val_unseen` data files.

## Evaluation Weaknesses

- Main paper uses subsets for A-EQA and GOAT-Bench because of resource limits.
- `LLM-Match` depends on LLM-as-judge evaluation.
- Strong performance depends on VLM/API quality and prompt behavior.
- The paper compares against 3DSG-caption representations, but not against explicit geometry-verifier 3DSG edges.
- It measures task success and efficiency, not relation-level correctness or geometry violation rates.
