# Evaluation

## Dataset / Benchmark

- Extended SceneFun3D:
  - The paper randomly selects 20 scenes, 8 from validation and 12 from test.
  - It annotates functional 3D scene graphs for these scenes.
  - Since the authors do not have physical access to these environments, evaluation is restricted to visually unambiguous functional relationships.
  - Reported annotations: 212 interactive elements, 195 functional relationships, 105 corresponding objects.
- FunGraph3D:
  - Newly collected real-world dataset.
  - 14 in-the-wild scenes: 6 kitchens, 2 living rooms, 3 bedrooms, 3 bathrooms.
  - 201 interactive elements, 228 functional relationships, 146 objects of interest.
  - Includes high-resolution laser scans, iPad RGB-D videos, egocentric human-scene interaction videos, and functional graph annotations.

## Splits

- SceneFun3D: 20 selected scenes from validation/test splits.
- FunGraph3D: newly collected scenes; the paper reports evaluation on the dataset rather than a large train/test split.
- OpenFunGraph is an inference pipeline rather than a task-specific supervised training method.

## Metrics

- Node Recall@K:
  - Node retrieval succeeds if a predicted node has non-zero 3D IoU with a ground-truth node and the ground-truth label ranks within top-K by CLIP text similarity.
  - Reports object nodes, interactive element nodes, and overall nodes.
  - Uses `R@3` and `R@10`.
- Triplet Recall@K:
  - A triplet is retrieved only if object, interactive element, and relationship are all retrieved.
  - Relationship matching uses BERT embedding similarity between predicted and ground-truth relationship descriptions.
  - Reports node association, edge prediction, and overall triplets.
  - Uses `R@5` and `R@10`.

## Baselines

- Open3DSG*:
  - Adapted with LLM prompts for functional relationships.
- Open3DSG* dagger:
  - Uses OpenFunGraph's fused 3D nodes for fairer comparison because Open3DSG normally assumes ground-truth node instance segmentation.
- ConceptGraph*:
  - Adapted prompts for functional relationship inference.
- ConceptGraph* + IED:
  - Adds OpenFunGraph's interactive element detection to ConceptGraph-style pipeline.

## Main Results

### Node Evaluation

| Dataset | Method | Overall Nodes R@3 | Overall Nodes R@10 |
| --- | --- | ---: | ---: |
| SceneFun3D | Open3DSG* | 56.7 | 64.7 |
| SceneFun3D | Open3DSG* dagger | 37.4 | 43.0 |
| SceneFun3D | ConceptGraph* | 28.3 | 31.4 |
| SceneFun3D | ConceptGraph* + IED | 60.1 | 66.0 |
| SceneFun3D | OpenFunGraph | 73.0 | 82.8 |
| FunGraph3D | Open3DSG* | 33.4 | 43.6 |
| FunGraph3D | Open3DSG* dagger | 20.2 | 29.4 |
| FunGraph3D | ConceptGraph* | 20.1 | 25.2 |
| FunGraph3D | ConceptGraph* + IED | 38.9 | 45.0 |
| FunGraph3D | OpenFunGraph | 55.5 | 65.8 |

### Triplet Evaluation

| Dataset | Method | Overall Triplets R@5 | Overall Triplets R@10 |
| --- | --- | ---: | ---: |
| SceneFun3D | Open3DSG* | 32.7 | 45.7 |
| SceneFun3D | Open3DSG* dagger | 21.6 | 28.1 |
| SceneFun3D | ConceptGraph* | 4.7 | 6.4 |
| SceneFun3D | ConceptGraph* + IED | 34.3 | 44.5 |
| SceneFun3D | OpenFunGraph | 60.4 | 70.3 |
| FunGraph3D | Open3DSG* | 10.5 | 20.0 |
| FunGraph3D | Open3DSG* dagger | 7.3 | 13.5 |
| FunGraph3D | ConceptGraph* | 1.1 | 2.5 |
| FunGraph3D | ConceptGraph* + IED | 10.3 | 18.9 |
| FunGraph3D | OpenFunGraph | 29.8 | 45.0 |

## Reproducibility Notes

- Code is available at `https://github.com/ZhangCYG/OpenFunGraph`.
- Dataset is hosted at `https://huggingface.co/OpenFunGraph`.
- The pipeline depends on multiple external foundation models and APIs, including RAM++, GroundingDINO, LLAVA v1.6, and GPT-4.
- Reproduction may require access to model weights, API calls, high-quality poses/depth, and dataset download permissions.

## Evaluation Weaknesses

- The datasets are small compared with 3DSSG/ScanNet-scale evaluation.
- Open-vocabulary label matching with CLIP/BERT similarity is useful but may hide semantic ambiguity.
- Functional correctness can require interaction evidence; static 3D geometry may not be enough.
- It does not evaluate ordinary spatial/support relation geometry consistency.
- It is a strong benchmark for functional relations, but a risky first benchmark for a 3-6 month CAND-001 prototype.
