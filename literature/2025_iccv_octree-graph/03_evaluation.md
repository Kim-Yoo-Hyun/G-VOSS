# Evaluation

## Dataset / Benchmark

- Zero-shot 3D semantic segmentation:
  - Replica: 8 scenes, following ConceptGraphs / ConceptFusion / HOV-SG settings.
  - ScanNet: 5 scenes.
- Zero-shot 3D instance segmentation:
  - ScanNet200 validation set: 312 scenes, 200 categories.
- Text-based object retrieval:
  - Sr3D, following BBQ's setup with 526 free-form queries from 8 scenes.
- Path planning:
  - HM3DSem, 8 scenes used in HOV-SG.
- Real-world validation:
  - RGB-D scan with Intel RealSense D435i; robotic dog and drone demonstrations.

## Splits

- The paper follows prior open-vocabulary 3D scene understanding settings for Replica, ScanNet, Sr3D, and HM3DSem.
- ScanNet200 validation set is used for instance segmentation.

## Metrics

- Semantic segmentation: `mIoU`, `F-mIoU`, `mAcc`.
- Instance segmentation: `AP`, `AP50`, `AP25`, plus AP range from 50% to 95%.
- Object retrieval: `Acc@0.1`, `Acc@0.25`, based on 3D bounding-box IoU.
- Path planning: success rate with endpoint thresholds `s = 1.0m`, `0.5m`, `0.25m`.
- Spatial representation: `Effective Occupancy Ratio (EOR)` / `mEOR`.
- Efficiency: storage and path planning time.

## Baselines

- Semantic segmentation: ConceptFusion, ConceptGraphs, HOV-SG.
- Instance segmentation: Mask3D, Open3DIS, OpenMask3D, OVIR-3D, SAM3D, SAI3D, Mask-Clustering.
- Object retrieval: ConceptGraphs, Open-Fusion, BBQ.
- Path planning: HOV-SG.
- Representation efficiency: point cloud and traditional octree.

## Main Results

Semantic segmentation:

- On Replica with OVSeg backbone, `Ours` reaches `0.320 mIoU`, `0.553 F-mIoU`, `0.414 mAcc`.
- On ScanNet with OVSeg backbone, `Ours` reaches `0.393 mIoU`, `0.508 F-mIoU`, `0.601 mAcc`.
- The paper reports improvement over HOV-SG by `+8.9% mIoU` and `+11.0% mAcc` on Replica, and `+17.1% mIoU` and `+17.0% mAcc` on ScanNet under the same settings.

Instance segmentation:

- Fully zero-shot setting on ScanNet200: `Ours` reports `14.3 AP`, `25.8 AP50`, `33.6 AP25`.
- The paper reports gains over the previous strongest fully zero-shot method by `+2.3 AP`, `+3.5 AP50`, and `+2.5 AP25`.

Text-based object retrieval:

- Sr3D: `Ours Octree-Graph+LLM` reports `0.26 Acc@0.1` and `0.23 Acc@0.25`.
- BBQ deductive baseline reports `0.23 Acc@0.1` and `0.18 Acc@0.25`.
- The paper reports `+3.0% Acc@0.1` and `+5.0% Acc@0.25` over BBQ.

Path planning:

- HM3DSem success rate:
  - HOV-SG: `55.25` at `s=1.0m`, `46.75` at `s=0.5m`, `32.16` at `s=0.25m`.
  - Octree-Graph: `97.88` at `s=1.0m`, `96.88` at `s=0.5m`, `96.38` at `s=0.25m`.

Representation efficiency:

- Replica scene average:
  - point cloud: `18.5MB`;
  - traditional octree: `17.6KB`, `0.0057 mEOR`;
  - adaptive-octree: `29.8KB`, `0.0108 mEOR`.
- ScanNet scene average:
  - point cloud: `6.4MB`;
  - traditional octree: `41.1KB`, `0.0041 mEOR`;
  - adaptive-octree: `69.3KB`, `0.0070 mEOR`.

Path planning efficiency:

- A* with Octree-Graph: `268.41KB`, `0.032s`.
- A* with point cloud: `71.16MB`, `2.154s`.
- Jump Point Search with Octree-Graph: `268.41KB`, `0.081s`.
- Jump Point Search with point cloud: `71.16MB`, `2.153s`.

## Reproducibility Notes

- Code repository is public: https://github.com/yifeisu/OV-Octree-Graph.
- The repository provides environment setup, third-party dependencies, pretrained checkpoint instructions, and dataset preparation notes.
- Reproduction is non-trivial because the stack depends on CropFormer, CLIP, OVSeg, TAP, Detectron2, PyTorch3D, MinkowskiEngine, ScanNet access, and dataset-specific preprocessing.
- The method is described as training-free, but the pipeline relies on pretrained 2D/VLM models and posed RGB-D / reconstructed point clouds.

## Evaluation Weaknesses

- There is no direct 3DSSG-style relation-edge evaluation such as predicate R@K, triplet R@K, or mR@K.
- Relation semantics are evaluated indirectly through object retrieval and path planning, not through open-vocabulary relation correctness.
- The strongest results may be driven partly by better instance construction and feature aggregation rather than the graph edge representation alone.
- Path planning is a useful embodied metric, but it may shift a CAND-001 thesis away from relation verification into navigation-system engineering.
