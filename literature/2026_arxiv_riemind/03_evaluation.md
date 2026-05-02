# Evaluation

## Dataset / Benchmark

- VSI-Bench static spatial questions.
- Original VSI-Bench has around 5,000 QA pairs from 288 real videos.
- Videos come from validation sets of ARKitScenes, ScanNet, and ScanNet++.
- RieMind discards dynamic route-planning and order-appearance questions, leaving 4,185 static questions across six question types.

## Splits

The paper uses the static portion of VSI-Bench. It builds 3DSGs from ground-truth annotations to isolate reasoning from perception.

## Metrics

- Accuracy / score per question type.
- Average score across static question types.
- Tool-call complexity by question type.

Question types:

- Object Count
- Absolute Distance
- Object Size
- Room Size
- Relative Distance
- Relative Direction

## Baselines

- Base VLMs without tools: Qwen2.5-VL-7B, GPT-4o.
- Proprietary VLMs: GPT-4o, Gemini-1.5 Flash, Gemini-1.5 Pro.
- Open-source VLMs: InternVL3-78B, LLaVA-NeXT-Video-7B/72B, Qwen2.5-VL-7B, LLaVA-OneVision-7B/72B.
- Fine-tuned spatial reasoning models: SpaceR, VG-LLM, ViLaSR, Spatial-MLLM, VLM-3R, OCR, ViCA, SpaceMind.

## Main Results

- Qwen2.5-VL-7B base average: 31.2.
- Qwen2.5-VL-7B agent + tools average: 64.1.
- GPT-4o base average: 35.3.
- GPT-4o agent + tools average: 85.2.
- GPT-4.1 agent + tools average: 89.5.
- Closest fine-tuned baseline reported in the table: SpaceMind average 73.6.
- The paper reports an average increase of about 16 points over the closest fine-tuned spatial QA model and large improvements over base VLMs.

Important nuance:

- Absolute metric tasks improve strongly.
- Relative direction remains compositionally hard because it needs multi-step frame/orientation reasoning.
- Qwen2.5-VL-7B agent underperforms its base version on Relative Direction, suggesting tool access alone is insufficient when the model cannot execute longer reasoning chains reliably.

## Reproducibility Notes

- Local PDF downloaded.
- Code/project page not found.
- End-to-end reproduction requires access to VSI-Bench static split and ground-truth annotations from ARKitScenes, ScanNet, and ScanNet++.
- The reported setup is not a perception benchmark because the 3DSG is instantiated from ground truth.

## Evaluation Weaknesses

- Upper-bound evaluation may overstate real deployment performance.
- The tool interface is deterministic, but the LLM's tool selection and multi-step reasoning can still fail.
- The benchmark is spatial QA, not directly task planning or robot decision refinement.
- It does not report a verifier-style metric such as invalid answer rejection precision or geometry violation rate.
