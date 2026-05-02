# Evaluation

## Dataset / Benchmark

SCOUT evaluates across:

- SymSearch: symbolic 3DSG benchmark built from InteriorGS.
- OmniGibson simulation benchmark extended with interactive object search.
- Real-world Toyota HSR mobile manipulator experiments.

SymSearch:

- Uses 10 indoor household scenes from InteriorGS.
- Uses 200 episodes.
- Uses 142 unique open-vocabulary object queries.
- Includes 61 categories not present in the training data.
- 115 target objects are not immediately observable and require interaction.
- Maximum episode length: 50 steps.

OmniGibson:

- 50 episodes.
- 50 unique BEHAVIOR-1K objects.
- 11 scenes.
- 27 objects not in the training data.
- 25 episodes require interactivity.
- Maximum episode length: 35 steps.
- Uses oracle magic open and ground-truth segmentation to isolate semantic reasoning from manipulation/perception failures.

Real world:

- Toyota HSR in a multi-room apartment with kitchen, office, and living room.
- 36 trials across 12 query object categories.
- 7 objects placed inside containers.

## Splits

The paper reports separate symbolic, simulation, and real-world evaluations. SymSearch results are averaged across 5 seeds.

## Metrics

- SR: Success Rate.
- SPL: Success weighted by Path Length.
- Number of high-level steps.
- Inference time.
- Runtime breakdown for real-world experiments.
- Real-world failure categories: perception, manipulation, reasoning.

## Baselines

- Random agent.
- CLIP similarity agent.
- SBERT similarity agent.
- MoMa-LLM.
- GODHS.
- SCOUT ablations:
  - no room influence, utility margin 0
  - no room influence
  - utility margin 0
  - full SCOUT

## Main Results

SymSearch Table II:

- Random agent: SR 0.337, SPL 0.072.
- CLIP similarity: SR 0.638, SPL 0.171.
- SBERT similarity: SR 0.683, SPL 0.179.
- MoMa-LLM: SR 0.827, SPL 0.256, inference 295s.
- GODHS: SR 0.906, SPL 0.161, inference 39s.
- SCOUT: SR 0.846, SPL 0.271, inference 6s.

OmniGibson Table II:

- CLIP similarity: SR 0.565, SPL 0.322.
- SBERT similarity: SR 0.632, SPL 0.241.
- MoMa-LLM: SR 0.696, SPL 0.257, inference 300s.
- GODHS: SR 0.478, SPL 0.087, inference 35s.
- SCOUT: SR 0.829, SPL 0.415, inference 1s.

Real world:

- Reports 64% success over 36 real-robot experiments.
- Average per-timestep runtime: scene graph construction 5.036s, node-selection inference 0.211s, navigation/manipulation execution 34.348s, total 39.596s.

## Reproducibility Notes

- Local PDF downloaded from arXiv.
- Official project page exists.
- Project page says code is coming soon as of 2026-04-29.
- SymSearch construction depends on InteriorGS annotations, room/door polygons, object bounding boxes, and manual nested-object relation annotation.
- LLM-generated relational datasets use gpt-4o according to the paper.

## Evaluation Weaknesses

- SymSearch is symbolic and removes many perception/control issues by design.
- OmniGibson uses oracle magic open and ground-truth segmentation, so it isolates reasoning but is not end-to-end.
- Real-world success is limited by perception and manipulation failures.
- It evaluates search efficiency and success, not relation-edge geometry violation.
- Learned common-sense priors may encode typical object placement and fail on atypical user-specific environments.
