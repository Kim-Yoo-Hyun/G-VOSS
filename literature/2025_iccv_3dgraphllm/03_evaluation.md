# Evaluation

## Dataset / Benchmark

- ScanRefer: single-object 3D referred object grounding on ScanNet.
- Multi3DRefer: multi-object referred object grounding.
- Scan2Cap: 3D dense scene captioning.
- ScanQA: 3D visual question answering.
- SQA3D: situated 3D question answering.
- Training data also includes ScanNet, 3RScan, RioRefer, Nr3D, and 3RQA-derived task variants.

## Splits

- The paper follows the standard benchmark validation strategy used by Chat-Scene and the respective datasets.
- Main experiments use predicted instance segmentation, with ablations for ground-truth segmentation, Mask3D, and OneFormer3D.

## Metrics

- ScanRefer: `Acc@0.25`, `Acc@0.5`.
- Multi3DRefer: `F1@0.25`, `F1@0.5`.
- Scan2Cap: `CIDEr@0.5`, `BLEU-4@0.5`.
- ScanQA: `CIDEr`, `BLEU-4`.
- SQA3D: exact match accuracy (`EM`).
- Efficiency: input tokens per scene and inference speed.

## Baselines

- Main baseline: Chat-Scene.
- Expert / specialized models include MVT, 3DVG-Trans, ViL3DRel, M3DRef-CLIP, Scan2Cap, ScanQA, SQA3D, 3D-VisTA, BUTD-DETR, PQ3D, and ZSVG3D.
- LLM-based comparisons include 3D-LLM, Chat-3D v2, Scene-LLM, LEO, LL3DA, Grounded 3D-LLM, Robin3D, and GPT4Scene variants.

## Main Results

### Task Performance

Main comparison against Chat-Scene:

| Method | ScanRefer Acc@0.25 | ScanRefer Acc@0.5 | Multi3DRefer F1@0.25 | Multi3DRefer F1@0.5 | Scan2Cap CIDEr@0.5 | Scan2Cap B-4@0.5 | ScanQA CIDEr | ScanQA B-4 | SQA3D EM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Chat-Scene | 55.5 | 50.2 | 57.1 | 52.4 | 77.1 | 36.3 | 87.7 | 14.3 | 54.6 |
| 3DGraphLLM, Vicuna-1.5 | 58.6 | 53.0 | 61.9 | 57.3 | 79.2 | 34.7 | 91.2 | 13.7 | 55.1 |
| 3DGraphLLM, LLAMA3-8B | 62.4 | 56.6 | 64.7 | 59.9 | 81.0 | 36.5 | 88.8 | 15.9 | 55.9 |

### Efficiency

The paper reports roughly `800` input tokens per scene for 3DGraphLLM versus `10400` for GPT4Scene. Reported inference speed is approximately:

| Dataset | 3DGraphLLM sec | GPT4Scene sec |
| --- | ---: | ---: |
| ScanRefer | 0.4 | 1.9 |
| Multi3DRefer | 0.5 | 2.0 |
| Scan2Cap | 0.9 | 2.2 |
| ScanQA | 0.4 | 1.9 |
| SQA3D | 0.4 | 1.7 |

### Semantic Edge Ablation

With LLAMA3-8B and ScanNet training, adding two nearest-neighbor semantic edges improves:

- ScanRefer `Acc@0.5`: 52.0 to 54.3.
- Multi3DRefer `F1@0.5`: 55.1 to 57.3.
- Scan2Cap `CIDEr@0.5`: 80.0 to 85.6.

With full pre-training and ScanNet+3RScan data, the LLAMA3-8B version reaches 56.6 ScanRefer `Acc@0.5` and 59.9 Multi3DRefer `F1@0.5`.

## Reproducibility Notes

- Code is public: https://github.com/CognitiveAISystems/3DGraphLLM
- Repository includes preprocessing, dataset pointers, training scripts, inference scripts, and a demo.
- Reported setup uses LLAMA3-8B-Instruct or Vicuna-1.5-7B with LoRA rank 16.
- The paper reports about 24 hours of training on 4 NVIDIA A100 GPUs.
- Reproduction requires object proposals, multi-view image features, 3D point features, and VL-SAT relation features.

## Evaluation Weaknesses

- Standard captioning and QA metrics may not capture valid spatial answers with wording different from references.
- The paper itself notes that n-gram metrics can penalize correct spatial descriptions that reference cues missing in the ground truth caption.
- No explicit metric separates semantic reasoning error, perception error, relation error, and geometry violation.
- Grounding improvements show relation usefulness, but not whether predicted relations are geometrically valid.
