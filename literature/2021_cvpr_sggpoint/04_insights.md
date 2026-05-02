# Insights

## Facts

- SGGpoint is a CVPR 2021 paper.
- It proposes EdgeGCN for explicit edge-oriented graph reasoning in 3D point-based scene graph generation.
- It uses 3DSSG-O27R16, a cleaned version of 3DSSG derived from 3RScan + 3DSSG, with 27 object classes and 16 relationship categories.
- It improves real-world 3D scan relation metrics over naive GCN-style reasoning.
- It is used as a baseline and reference model in later work such as VL-SAT.

## Paper Claims

- Existing scene graph reasoning tends to treat edges as secondary to nodes.
- Multi-dimensional edge features should be modeled explicitly.
- Twinning interactions between node and edge streams improve scene graph representation learning.
- Edge-oriented reasoning is useful not only for 3D scene graph generation but also for general graph representation learning.

## Inferences

- SGGpoint is the strongest existing closed-set precedent for CAND-001's edge-centered design.
- However, SGGpoint's edge representation is latent and discriminative, not evidence-based or verifiable.
- CAND-001 can be framed as moving from `edge feature learning` to `edge evidence representation + consistency verification`.
- If CAND-001 stays on 3DSSG, SGGpoint should be included as a baseline or at least a paper-level baseline.

## Connection to Field Trends

- Provides the edge-reasoning branch of 3DSSG history before later visual-language and open-vocabulary methods.
- Helps separate two threads:
  - SGGpoint: geometry/edge reasoning in closed-set 3DSG.
  - VL-SAT/Open3DSG/CCL-3DSGG: visual-language/open-vocabulary semantic relation prediction.
- CAND-001 sits between these threads by asking for semantic relation edges with explicit geometry evidence.

## Possible Contribution Angles

- Use SGGpoint's EdgeGCN as a closed-set relation baseline, then add explicit geometry evidence to predicted edges.
- Compare latent edge features against hand-designed or learned evidence attributes such as support/contact, containment, distance, and relative pose.
- Evaluate whether geometry evidence improves relation consistency even when standard triplet recall changes little.
- Use SGGpoint's 3DSSG-O27R16 preprocessing as a reference, but avoid locking the thesis to reduced 16-relation labels unless necessary.

## What Would Change This Assessment

- If SGGpoint code/data preprocessing is hard to reproduce, it remains a conceptual baseline.
- If later baselines such as SGRec3D or VL-SAT dominate SGGpoint by a large margin in accessible settings, SGGpoint should become historical context rather than an experiment target.
- If CAND-001 moves toward open-vocabulary robotics mapping, SGGpoint becomes less central than ConceptGraphs, OVSG, or HOV-SG.
