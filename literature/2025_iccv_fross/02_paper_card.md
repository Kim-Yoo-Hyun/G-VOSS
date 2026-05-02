# Paper Card

## Problem

Most 3D semantic scene graph generation methods are offline and require full scene data, instance-segmented point clouds, dense reconstruction, or complete image sequences. This is not ideal for robotics and AR systems that need online, low-latency updates.

## Core Idea

FROSS generates 2D scene graphs from RGB-D frames, lifts detected objects and relations into 3D, represents objects as 3D Gaussian distributions, and incrementally merges local scene graphs into a global 3D semantic scene graph.

## Input / Output

- Input: RGB-D image sequence with camera poses.
- Output: online global 3D semantic scene graph with object nodes represented as 3D Gaussian distributions and relation edges.

## Method

- Use RT-DETR object detection and EGTR relationship extraction to generate 2D scene graphs.
- Convert 2D bounding boxes to 2D Gaussian distributions.
- Back-project them into 3D using depth and camera pose.
- Merge 3D object Gaussians using class labels and statistical distance.
- Keep relation edges through lifted and merged graph updates.

## Main Claims

- FROSS is faster-than-real-time for online 3D semantic scene graph generation.
- Approximate 3D object location is often enough for high-level semantic scene graph applications.
- ReplicaSSG extends Replica with inter-object relationship annotations for more comprehensive evaluation.

## Strengths

- Important benchmark/reference for online 3D SSG.
- Introduces ReplicaSSG, directly relevant to dataset feasibility for CAND-001.
- Reports both performance and latency.
- Shows that 2D SG quality strongly affects final 3D SSG quality.

## Limitations

- Relation quality depends heavily on 2D scene graph generation.
- ReplicaSSG performance is limited by domain mismatch because the 2D SG model is trained on Visual Genome.
- Gaussian object representation trades precise geometry for speed; this may be insufficient for fine support/contact verification.

## Relevance to My Research

FROSS is less central than 3DSSG for the first thesis prototype, but it matters for online/real-time and ReplicaSSG evaluation. It also shows that relation accuracy and system speed can be evaluated together.

## Follow-up Questions

1. Is ReplicaSSG accessible and suitable for geometry-consistency evaluation?
2. Are FROSS relations too coarse for support/contact verification?
3. Can CAND-001 run as a geometry verifier on top of FROSS's online graph?

