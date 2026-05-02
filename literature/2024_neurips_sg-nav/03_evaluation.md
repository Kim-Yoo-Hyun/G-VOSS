# Evaluation

## Dataset / Benchmark

SG-Nav evaluates object-goal navigation on:

- MP3D / Matterport3D
- HM3D
- RoboTHOR

Reported validation setup:

- MP3D: 11 indoor scenes, 21 object goal categories, 2,195 object-goal navigation episodes.
- HM3D: 20 validation environments, 6 goal object categories, 2,000 validation episodes.
- RoboTHOR: 15 validation environments, 12 goal object categories, 1,800 validation episodes.

## Splits

The paper reports validation-set evaluation for ObjectNav benchmarks. It compares supervised, unsupervised, and zero-shot methods.

## Metrics

- SR: Success Rate.
- SPL: Success weighted by Path Length.
- SoftSPL: navigation progress and efficiency metric, reported in ablations.

## Baselines

Supervised / non-zero-shot:

- SemEXP
- PONI
- ProcTHOR

Unsupervised / not fully zero-shot:

- ZSON
- ProcTHOR-ZS

Zero-shot:

- CoW
- ESC
- L3MVN
- OpenFMNav
- VLFM

SG-Nav variants:

- SG-Nav-LLaMA
- SG-Nav-GPT
- SG-Nav without scene graph / re-perception
- SG-Nav without re-perception
- room/group node ablations
- edge ablations
- prompting ablations

## Main Results

Table 1:

- SG-Nav-LLaMA: MP3D SR/SPL 40.1/16.0, HM3D 53.9/24.8, RoboTHOR 47.3/23.7.
- SG-Nav-GPT: MP3D SR/SPL 40.2/16.0, HM3D 54.0/24.9, RoboTHOR 47.5/24.0.
- Prior strong zero-shot baselines include OpenFMNav at MP3D 37.2/15.7, HM3D 52.5/24.1, RoboTHOR 44.1/23.3; VLFM at MP3D 36.2/15.9, HM3D 52.4/30.3, RoboTHOR 42.3/23.0.

Table 2:

- Without SG and re-perception: MP3D SR 25.7, HM3D SR 38.6, RoboTHOR SR 34.9.
- Without re-perception: MP3D SR 36.5, HM3D SR 49.6, RoboTHOR SR 41.9.
- Full SG-Nav: MP3D SR 40.1, HM3D SR 53.9, RoboTHOR SR 47.3.

Other ablations:

- Room and group nodes both help; removing group nodes hurts more than removing room nodes on MP3D.
- Complete graph edges improve over node-only graphs.
- Hierarchical graph structure and CoT prompting improve MP3D SR compared with plain text prompting.

## Reproducibility Notes

- Local PDF downloaded from NeurIPS proceedings.
- Official code exists at https://github.com/bagh2178/SG-Nav.
- GitHub README includes Matterport3D data setup, ObjectNav episode data, GLIP, SAM, GroundingDINO, and Ollama instructions.
- The system depends on Habitat-style ObjectNav data, 2D/3D segmentation components, VLM/LLM dependencies, and GPU setup.

## Evaluation Weaknesses

- Navigation success mixes reasoning, perception, mapping, and low-level navigation quality.
- The reported gain is not an isolated verifier metric.
- Relation edges are useful for prompting, but the evaluation does not measure edge correctness or geometry violation directly.
- Perception failure correction is handled through re-perception credibility, not through explicit relation evidence or constraint checking.
