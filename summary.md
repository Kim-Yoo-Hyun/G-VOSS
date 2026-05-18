# H001 Research Summary

Last updated: 2026-05-15 KST

이 문서는 CAND-001 / H001의 현재 연구 정의, 필요성, 가설, metric,
비교군, 실험 세팅, contribution, 구현 방향, baseline 재현 가능성을 한곳에
정리한다.

## One-Line Summary

Fact:

- H001은 새로운 3DSSG generator를 제안하는 연구가 아니라, 기존 3DSSG
  relation predictor의 semantic relation prediction을 explicit 3D geometry
  evidence로 검증하고 보정하는 연구다.

Inference:

- 가장 방어 가능한 논문 framing은 `calibrated geometry-consistency evaluation
  and re-ranking framework for 3D scene graph relations`이다.

## Problem Definition

Fact:

- Open-vocabulary 또는 learned 3D Scene Graph predictor는 visual/language
  prior 때문에 의미상 그럴듯한 relation edge를 낼 수 있다.
- 그러나 이런 relation edge가 실제 3D geometry와는 맞지 않을 수 있다.
- H001은 전체 predicate를 다루지 않고, geometry로 검증 가능한 relation
  family에 집중한다.

Target families:

- `support_contact`
- `proximity`
- `relative_vertical`

Out of first-scope:

- full functional relation discovery
- relative-horizontal coordinate-frame claim
- online RGB-D graph generation
- robotics navigation
- broad open-vocabulary 3DSSG generation improvement

## Why This Research Is Needed

Fact:

- 3D Scene Graph는 relation prediction benchmark뿐 아니라 alignment,
  registration, navigation, planning, LLM/VLM reasoning 같은 downstream
  task에서도 structured scene representation으로 쓰인다.
- 기존 3DSSG metric인 R@K / mR@K는 semantic label recall은 보여주지만,
  top-k relation이 물리적 또는 기하학적으로 가능한지 직접 측정하지 않는다.
- VL-SAT, Open3DSG, CCL-3DSGG 등은 semantic 또는 open-vocabulary relation
  prediction을 강화하지만, relation edge마다 explicit geometry validity,
  evidence provenance, violation reason을 표준적으로 보고하지는 않는다.

Inference:

- Top-tier contribution을 만들려면 "semantic + geometry를 쓴다"가 아니라,
  relation edge의 reliability를 측정하고 개선하는 evaluation / re-ranking
  layer로 좁혀야 한다.
- H001의 필요성은 "더 높은 R@K"만이 아니라, R@K를 유지하면서
  geometry-inconsistent top-k relation을 줄이고 왜 실패했는지 분석 가능하게
  만드는 데 있다.

## Hypothesis

Main hypothesis:

```text
For geometry-checkable 3DSSG relation families, adding explicit 3D geometry
evidence and verification to candidate semantic relation edges will reduce
geometry-inconsistent relation predictions while preserving useful
predicate/triplet recall.
```

Operational form:

```text
semantic prediction score + frozen geometry evidence/verifier + calibrated
p_geom_valid -> reliability-aware reranking/filtering
```

Allowed current claim:

```text
On reproduced VL-SAT 3DSSG predictions, geometry-calibrated relation
verification improves relation reliability for geometry-checkable families by
reducing geometry-inconsistent top-k predictions while preserving or improving
useful recall.
```

Preferred upgraded claim after Open3DSG second-source evidence:

```text
Across reproduced VL-SAT and Open3DSG prediction sources, calibrated
geometry-consistency re-ranking improves relation reliability for
geometry-checkable 3DSSG families while preserving useful recall.
```

Not allowed now:

```text
The method broadly improves open-vocabulary 3D scene graph generation.
```

Not allowed now:

```text
The method is already baseline-agnostic across 3DSSG predictors.
```

## Method Contribution

Contribution should be stated as:

```text
calibrated geometry-consistency evaluation and re-ranking for 3D scene graph
relations
```

Core components:

| Component | Role |
| --- | --- |
| identity-preserving prediction rows | preserve scan/subgraph/object-pair identity across prediction, geometry, and GT joins |
| geometry evidence schema | attach auditable OBB, point/local, distance, vertical, contact, and support evidence to relation candidates |
| subtype-aware verifier | convert geometry evidence into `satisfied`, `uncertain`, or `violated` decisions |
| `p_geom_valid` calibration | estimate geometry-valid probability from frozen calibration data and counterfactual negatives |
| reliability-aware re-ranking/filtering | combine semantic score and calibrated geometry validity without replacing the base predictor |
| violation/recall evaluation layer | measure geometry reliability separately from standard recall |
| failure-analysis schema | explain whether failures come from semantic confusion, geometry violation, preprocessing, denominator coverage, or model/source limitations |

Avoid this framing:

```text
a rule verifier script for VL-SAT
```

## Experimental Setting

Fixed current setting:

| Item | Fixed value |
| --- | --- |
| dataset | official `3DSSG_subset` / 3RScan validation-derived held-out scope |
| implemented prediction source | reproduced `VL-SAT` / `vlsat_closed_set` |
| selected second-source path | Docker-reproduced `Open3DSG` |
| held-out scans | 127 |
| subgraphs | 388 |
| prediction rows | 673,816 |
| ground-truth rows | 7,505 |
| in-scope prediction rows | 155,496 |
| in-scope GT denominator | 2,545 |
| predicate families | `support_contact`, `proximity`, `relative_vertical` |
| frozen verifier policy | `point_subtype` |
| frozen pooled calibrator | `artifacts/calibration/p_geom_valid_smoke/model.json` |
| frozen family calibrator | `artifacts/calibration/p_geom_valid_family/model.json` |

Open3DSG metric-scope policy:

- in-scope GT denominator: 2,545 rows
- `support_contact`: 1,199
- `proximity`: 1,128
- `relative_vertical`: 218
- recall matching remains exact predicate-label matching
- family grouping is for reliability / violation reporting, not recall-label
  collapse
- filtered-train and covered-scope caveats must be reported

## Metrics

Prediction metrics:

- `R@50`
- `R@100`
- `Violation@50`
- `Violation@100`
- delta versus `semantic_only`
- relative violation reduction versus `semantic_only`
- recall retention

Verifier-validity metrics:

- GT-positive nonviolated rate
- GT-derived negative nonsatisfied rate
- `p_geom_valid` Brier
- `p_geom_valid` AUROC
- `p_geom_valid` AUPRC

Audit / sanity metrics:

- structured audit strict invalid-only precision
- structured audit quality-issue precision
- reduced visual spot-check target-bucket quality-issue rate
- reduced visual spot-check contradiction rate

## Comparison Groups

Primary conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | reproduced base predictor ranking |
| `probabilistic_recalibrated` | main recall-first H001 condition, semantic score combined with frozen pooled `p_geom_valid` |
| `rule_verified_point_subtype` | hard-filter diagnostic / zero-violation operating point |
| `family_specific_p_geom_valid` | stricter violation-first operating point |

Control conditions:

| Condition | What it tests |
| --- | --- |
| `control_p_geom_valid_only` | whether geometry alone explains the result |
| `control_distance_only` | whether a simple distance heuristic explains the result |
| `control_shuffled_geometry` | whether geometry distribution alone explains the result |
| `control_wrong_pair_geometry` | whether object-pair identity matters |

Cross-source comparison:

| Source | Role | Status |
| --- | --- | --- |
| `VL-SAT` | current implemented main source | reproduced and table-ready |
| Open3DSG | selected second-source / open-vocabulary source | official feature dump complete and Docker `feature_audit` ready; non-averaged BLIP projector checkpoint route failed three times with CUDA OOM; lower-memory `--avg_blip_emb` pilot completed and provenance/selection recorded 2 pilot checkpoints; full avg-BLIP training is running in tmux |
| Qwen-VL | optional modern VLM semantic-source extension | schema/parser/tiny pilot/pair crops ready; Qwen3-VL-4B cache ready; runtime preflight blocked while Open3DSG pilot training occupies the GPU; no inference |
| FROSS | optional online support/contact source | not full-family H001 evidence |

## What The Experiments Compare

RQ1:

```text
Does geometry-calibrated reranking improve recall while lowering
geometry-inconsistent top-k predictions compared with semantic-only ranking?
```

RQ2:

```text
Is the improvement nontrivial, or can it be explained by geometry-only ranking,
distance heuristics, shuffled geometry, or wrong-pair geometry?
```

RQ3:

```text
Does the verifier agree with held-out GT-positive relations and reject
deterministic GT-derived counterfactual negatives?
```

RQ4:

```text
Do structured audit and reduced visual sanity-check evidence support the
interpretation that violation labels correspond to real relation-quality
issues?
```

Optional RQ5:

```text
Does the same geometry-consistency framework improve reliability when the
semantic source is a modern VLM rather than a trained 3DSSG predictor?
```

## Current Evidence

Fact:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 |

Fact:

- GT positives: 2,545
- GT-derived negatives: 2,545
- GT-positive nonviolated rate: 0.9972
- GT-derived negative nonsatisfied rate: 0.9694
- `p_geom_valid` AUROC/AUPRC: 0.9779 / 0.9737
- reduced visual sanity-check target quality-issue rate: 0.9333
- reduced visual sanity-check contradiction rate: 0.0333

Inference:

- The current evidence supports a scoped `VL-SAT`-centered reliability-layer
  claim.
- It does not yet support a baseline-agnostic or broad open-vocabulary 3DSSG
  improvement claim.

## Required Tables And Figures

Required tables:

| Table | Content |
| --- | --- |
| Table 1 | main held-out prediction result |
| Table 2 | nontriviality controls |
| Table 3 | GT-based verifier evaluation |
| Table 4 | structured audit and reduced visual sanity check |
| Table 5 | source-specific claim boundary and blocked extensions |
| Table 6 | cross-source result, blocked until real Open3DSG metrics exist |
| Table 7 | optional Qwen-VL modern semantic-source result |
| Table 8 | optional SceneFun3D/FunGraph3D functional/robotics result |

Required figures:

| Figure | Content |
| --- | --- |
| Figure 1 | framework pipeline: prediction rows, geometry evidence, verifier, `p_geom_valid`, reranking/filtering |
| Figure 2 | reliability-recall tradeoff across operating points |
| Figure 3 | traceable qualitative cases from audit / visual sanity-check artifacts |

## Main Baselines And Reproducibility

Fact:

- Current main baseline set: `VL-SAT` + Open3DSG.
- `VL-SAT` is already reproduced as the implemented main source.
- Open3DSG is the required second-source anchor for the top-tier path.
- SGFormer is a plausible optional closed-set comparison only after its model
  release, checkpoint path, and dataset contract are verified in Docker.

Baseline selection policy:

1. If official pre-trained weights exist, first run the author's evaluation path
   as a Docker sanity check and record whether the reported table can be
   re-evaluated under the same dataset split.
2. Regardless of pre-trained weights, run or attempt Docker re-training with the
   paper's exposed hyperparameters. If hyperparameters, exact split, or
   checkpoints are missing, record that as a reproducibility limitation instead
   of silently changing the claim.
3. H001 paper tables should not copy original paper Table 1/Table 2 directly.
   They should re-evaluate each baseline through the same H001 prediction-row,
   geometry-join, verifier, and recall/violation metric contract.

| Baseline paper | Current H001 role | Official code | Pre-trained baseline checkpoint | Re-training possible | Current decision |
| --- | --- | --- | --- | --- | --- |
| `VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud` | Primary reproducible baseline / closed-set 3DSSG anchor | Yes: `wz7in/CVPR2023-VLSAT` | Yes. Official README links a Google Drive `checkpoint`, and mentions `clip_adapter/checkpoint/origin_mean.pth`. GitHub Releases are empty, so checkpoint is Drive-based. | Yes. README gives dependencies, data preparation, multi-view generation, CLIP adapter training, default config, and train/eval commands. | Best first baseline. Use for pre-trained re-eval, retraining attempt, H001 Table 1/2/controls, and ablations. |
| `Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships` | Required second-source / open-vocabulary anchor | Yes: `boschresearch/Open3DSG`; repo is archived/read-only as of 2026-05-15 check | No trusted final trained Open3DSG checkpoint confirmed in the official repo. Component downloads exist for OpenSeg, BLIP2 positional embedding, and PointNet/PointNet2, but test still requires `--checkpoint [path to checkpoint]`. | Yes, but heavy. README gives setup, data prep, preprocessing, optional 2D feature dump, train, and test commands. Feature dump can require about 300GB per dataset. | Continue Docker reproduction and generate our own checkpoint with provenance. This is not the easiest baseline, but it is the most important second-source defense. |
| `SGFormer: Semantic Graph Transformer for Point Cloud-based 3D Scene Graph Generation` | Optional additional closed-set baseline | Yes: `Andy20178/SGFormer` | Official README states code and model release, but the actual checkpoint asset/path still needs Docker-side verification. | Likely possible. README gives dataset, install, training, and inference commands, but commands include local absolute paths and 3DSSG-O27R16 / 160O26R setup details that need cleanup. | Use only after `VL-SAT` and Open3DSG. Good candidate if a clean checkpoint download and split-compatible adapter are confirmed. |

Recommended baseline order:

| Priority | Baseline | Reason |
| --- | --- | --- |
| 1 | `VL-SAT` | best fit for the user's criteria: official code, Drive checkpoint, default config, train/eval commands, already adapted to H001 |
| 2 | Open3DSG | necessary for top-tier second-source and open-vocabulary defense, even though final checkpoint must be produced by us |
| 3 | SGFormer | optional extra closed-set comparison if checkpoint and dataset adapter verify cleanly |

Not current main baselines:

| Paper / source | Why it matters | Current status |
| --- | --- | --- |
| `CCL-3DSGG` | strong CVPR 2024 open-vocabulary 3DSGG paper-level competitor | no official code/checkpoint path confirmed in the current pass |
| `SGGpoint` | edge-oriented 3DSSG relation baseline and source of cleaned 3DSSG-O27R16 setup | official implementation exists, but pre-trained weight / easy re-eval path is not confirmed |
| `SMKA` | spatial-knowledge closed-set baseline | paper-level baseline to avoid overclaiming spatial-knowledge novelty |
| FROSS | online 3D SSG / ReplicaSSG direction | optional route only; does not cover all H001 families |
| `Qwen2.5-VL` / `Qwen3-VL` | modern VLM semantic-source extension | optional extension, not replacement for Open3DSG |

## Implementation Direction

Paper-body experiment rule:

- final experiment outputs must be Docker-generated;
- host-only outputs are not paper-result evidence;
- long-running I/O or training jobs run in background sessions with logs;
- exact commands, working directory, expected outputs, and verification commands
  must be recorded.

Current experiment root:

```text
experiments/H001_geom_reliability/
```

Implemented / ready:

- Docker table builder for locked `VL-SAT` artifacts
- Table 1-6 placeholder/report generation
- locked input manifest
- Open3DSG checkpoint reproduction plan
- Open3DSG post-dump handoff gates
- Open3DSG checkpoint provenance/selection template
- Open3DSG raw-dump identity checklist
- Open3DSG metric-scope policy
- Open3DSG metric/join blocked-input contract
- Open3DSG failure-analysis schema and synthetic smoke generator
- Qwen-VL input/output schema, parser skeleton, tiny pilot, model-lock plan,
  and 30/30 pair-crop rendering

Current data/runtime status:

- Open3DSG official BLIP TopK5/scales3 feature dump is complete.
- Docker `feature_audit` passed on 2026-05-15 KST with status `ready` and
  blockers none.
- Feature root:
  `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/`.
- Current feature coverage: 3900/3900 complete feature ids.
- Split coverage: train 3744/3744, validation 156/156, missing complete 0,
  missing preprocessed 0.
- Each required feature directory has 3900 `.pt` files:
  `export_obj_clip_valids`, `export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1`,
  and `export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998`.
- The first Open3DSG checkpoint pilot launched in tmux
  `h001_open3dsg_train_pilot` on 2026-05-15 13:18 KST, reached epoch 0
  step 1419/3744, and failed with CUDA OOM during BLIP projector forward.
  Exit code was 1 and no `.ckpt` file was found.
- The first retry used source patch schema `h001_open3dsg_source_patch_v5`
  with chunked BLIP projector forward and
  `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=4`. It reached epoch 0 step 235/3744
  and failed with CUDA OOM while an unrelated `conceptgraph` container had
  expanded GPU usage. Exit code was 1 and no `.ckpt` file was found.
- Training preflight schema `h001_open3dsg_training_preflight_v6` now records
  GPU free/total memory and blocks `train_pilot`/`train_full` if
  `OPEN3DSG_MIN_GPU_FREE_MB` is not met. Docker preflight passed at
  2026-05-15 13:49 KST with 30019/32100 MB free and threshold 18000 MB.
- Retry2 used `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1`, reached epoch 0
  step 699/3744, and failed with CUDA OOM in the chunked BLIP projector path.
  Exit code was 1 and no `.ckpt` file was found.
- The selected lower-memory route is Open3DSG's existing `--avg_blip_emb`
  option, which is compatible with the official `[num_edges, 257, 1408]`
  BLIP feature tensors and skips the train-time BLIP projector. This is a
  reproducible Open3DSG averaged-BLIP variant, not the exact non-averaged
  projector route.
- Avg-BLIP pilot completed with exit code 0, global step 936, val/loss
  0.37145, and two `avg_blip_pilot` checkpoints. Docker
  `open3dsg_checkpoint_selection` was refreshed with schema
  `h001_open3dsg_checkpoint_selection_v2`, candidate_count 2, and
  paper-result eligible candidates 0.
- Full avg-BLIP training is running in tmux
  `h001_open3dsg_train_full_avg_blip`; Docker container
  `open3dsg-train_full_avg_blip-run-b642ae11a484`; log
  `logs/open3dsg_train_full_avg_blip_20260515_172644.log`; exit file
  `logs/open3dsg_train_full_avg_blip_20260515_172644.exit`; run record
  `experiments/H001_geom_reliability/sources/open3dsg/train_pilot/full_avg_blip_20260515_172644.md`.
- No Open3DSG metric evidence exists yet.

Next required data-dependent sequence:

1. Wait for full avg-BLIP Open3DSG checkpoint training to exit.
2. Verify full avg-BLIP exit code and checkpoint path.
3. Refresh checkpoint provenance/selection before held-out metric/failure
   inspection.
4. Run identity-preserving raw dump.
5. Export Open3DSG prediction JSONL.
6. Join with geometry verification and GT.
7. Run the same H001 metric suite.
8. Generate real failure-analysis rows from the locked schema.

Optional extension sequence:

- Qwen-VL runtime preflight after GPU availability, then 1-3 crop tiny inference smoke; keep as non-metric extension evidence.
- Reduced checkpoint smoke only if official route is intentionally paused or
  declared too slow; it must not become paper-result evidence.
- SceneFun3D/FunGraph3D only if the paper scope expands to functional or
  affordance relation reliability with a separate contract.

## Reviewer-Risk Defense

Likely reviewer attacks:

- "This is only a rule-based post-processing script."
- "The result is a VL-SAT-specific trick."
- "The claim overstates open-vocabulary or baseline-agnostic improvement."
- "Violation improves only because recall is pruned."
- "The denominator or filtered training split is cherry-picked."
- "The relation families are too narrow."

Required defenses:

- keep method framing as calibrated geometry-consistency evaluation and
  re-ranking, not a rule script;
- report recall and violation together;
- include semantic-only, calibrated, hard-filter, family-specific, and control
  conditions;
- report in-scope denominator, excluded rows, filtered train/validation counts,
  and covered Open3DSG contexts;
- add Open3DSG second-source metrics before making cross-predictor claims;
- treat Qwen-VL and functional/robotics benchmarks as separate optional tracks.

## Sources Checked

- Checked / updated: 2026-05-15 KST
- `VL-SAT` official repository: https://github.com/wz7in/CVPR2023-VLSAT
- `VL-SAT` CVF page: https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.html
- `Open3DSG` official repository: https://github.com/boschresearch/Open3DSG
- `Open3DSG` CVF/arXiv paper: https://arxiv.org/abs/2402.12259
- `CCL-3DSGG` CVF page: https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html
- `SGFormer` official repository: https://github.com/Andy20178/SGFormer
- `SGGpoint` official repository: https://github.com/chaoyivision/SGGpoint
