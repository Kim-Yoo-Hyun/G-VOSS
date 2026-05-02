# Evaluation

## Dataset / Benchmark

- 3DSSG.
- ReplicaSSG: Replica dataset extended with inter-object relationship annotations.

## Splits

FROSS evaluates on 3DSSG and ReplicaSSG. It reports results with predicted 2D scene graphs and with ground-truth 2D scene graphs.

## Metrics

- Relationship recall.
- Object recall.
- Predicate recall.
- Object mean recall.
- Predicate mean recall.
- Latency and FPS.

The supplementary clarifies that the recall metric follows Wu et al. and is closer to recall with graph constraints than standard 2D SG Recall@N.

## Baselines

- IMP.
- VGfM.
- 3DSSG.
- SGFN.
- Wu et al.
- Kim et al.

## Main Results

On 3DSSG:

- FROSS: relation recall 27.9, object recall 62.4, predicate recall 33.0, object mRecall 63.8, predicate mRecall 18.0.
- FROSS w/ ground-truth 2D SG: relation recall 55.8, object recall 88.6, predicate recall 56.0, object mRecall 93.3, predicate mRecall 56.8.

On ReplicaSSG:

- FROSS: relation recall 22.3, object recall 26.1, predicate recall 27.8, object mRecall 28.8, predicate mRecall 20.4.
- FROSS w/ ground-truth 2D SG: relation recall 67.6, object recall 89.1, predicate recall 67.6, object mRecall 92.6, predicate mRecall 82.6.

Runtime:

- Object detection latency: 2.31 ms.
- Relationship extraction latency: 4.51 ms.
- 3D SSG merging latency: 0.12 ms.
- FPS: 144.09.

## Reproducibility Notes

- Code and dataset are publicly linked in the paper: https://github.com/Howardkhh/FROSS.
- The method depends on RGB-D frames and camera trajectories; it also evaluates ORB-SLAM3 estimated trajectories on ReplicaSSG.

## Evaluation Weaknesses

- Heavy dependence on 2D SG quality.
- Predicates are still predefined, not open-vocabulary.
- Gaussian object approximation is fast but may be too coarse for fine-grained geometry evidence like physical support and contact.
- ReplicaSSG's domain shift from Visual Genome-trained 2D SG models causes lower recall.

