# H001 Research Summary

Last updated: 2026-05-21 KST

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
| Open3DSG | selected second-source / open-vocabulary source | Docker-reproduced avg-BLIP checkpoint, H001 eval features, raw dump identity with clean v14 streaming provenance, adapter export, geometry join, metric eval, Table 6 hook, real failure rows, qualitative case sample, qualitative inspection, and paper caveat wording are ready |
| Qwen-VL | optional modern VLM semantic-source extension | schema/parser/tiny pilot/pair crops ready; Qwen3-VL-4B cache ready; runtime preflight not rerun after Open3DSG jobs completed; no inference |
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

Open3DSG second-source result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

Fact:

- GT positives: 2,545
- GT-derived negatives: 2,545
- GT-positive nonviolated rate: 0.9972
- GT-derived negative nonsatisfied rate: 0.9694
- `p_geom_valid` AUROC/AUPRC: 0.9779 / 0.9737
- reduced visual sanity-check target quality-issue rate: 0.9333
- reduced visual sanity-check contradiction rate: 0.0333

Inference:

- The current evidence supports a measured cross-source reliability-layer claim
  within H001 families across `VL-SAT` and Open3DSG.
- It supports a cross-source reliability-layer claim only within the measured
  H001 families and closed-set/GT-object setting.
- It does not yet support a broad open-vocabulary 3DSSG generation improvement
  claim.

## Required Tables And Figures

Required tables:

| Table | Content |
| --- | --- |
| Table 1 | main held-out prediction result |
| Table 2 | nontriviality controls |
| Table 3 | GT-based verifier evaluation |
| Table 4 | structured audit and reduced visual sanity check |
| Table 5 | source-specific claim boundary and blocked extensions |
| Table 6 | cross-source `VL-SAT` + Open3DSG result; ready, with Open3DSG caveats |
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
| `Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships` | Required second-source / open-vocabulary anchor | Yes: `boschresearch/Open3DSG`; repo is archived/read-only as of 2026-05-15 check | No trusted final trained Open3DSG checkpoint confirmed in the official repo. Component downloads exist for OpenSeg, BLIP2 positional embedding, and PointNet/PointNet2, but test still requires `--checkpoint [path to checkpoint]`. | Yes, but heavy. README gives setup, data prep, preprocessing, optional 2D feature dump, train, and test commands. Feature dump can require about 300GB per dataset. | Docker reproduction produced an explicitly labeled avg-BLIP checkpoint and H001 metrics. Use as second-source evidence with the frozen `paper_caveats/` wording: filtered-train, averaged-BLIP, covered-scope, `validation_missing_preprocessed:11`, exact-label denominator, and residual calibration-risk caveats; clean v14 streaming raw-dump provenance is available. |
| `SGFormer: Semantic Graph Transformer for Point Cloud-based 3D Scene Graph Generation` | Optional additional closed-set baseline | Yes: `Andy20178/SGFormer` | Official README states code and model release, but the actual checkpoint asset/path still needs Docker-side verification. | Likely possible. README gives dataset, install, training, and inference commands, but commands include local absolute paths and 3DSSG-O27R16 / 160O26R setup details that need cleanup. | Use only after `VL-SAT` and Open3DSG. Good candidate if a clean checkpoint download and split-compatible adapter are confirmed. |

Recommended baseline order:

| Priority | Baseline | Reason |
| --- | --- | --- |
| 1 | `VL-SAT` | best fit for the user's criteria: official code, Drive checkpoint, default config, train/eval commands, already adapted to H001 |
| 2 | Open3DSG | necessary for top-tier second-source and open-vocabulary defense; checkpoint and H001 metrics are now Docker-reproduced by us |
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
- Open3DSG metric/join contract, real adapter export, geometry join, metric eval, and Table 6 hook
- Open3DSG failure-analysis schema and synthetic smoke generator
- Open3DSG real failure-analysis rows and qualitative failure-case sampler
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
- Full avg-BLIP training completed and Docker checkpoint selection selected
  `epoch=13-step=13104.ckpt` before H001 held-out inspection.
- H001 held-out eval feature cache is complete for the covered loadable scope:
  shard loop exit 0, `377/377` complete feature ids, and `1131` `.pt` files.
  Docker `feature_audit_h001_eval` has missing complete feature ids `0`, while
  retaining the known `validation_missing_preprocessed:11` caveat.
- The feature-ready raw dump reached the full context load but failed before
  writing `raw_dump/raw.jsonl` because of Docker shared-memory / DataLoader
  worker errors. The SHM retry avoided that failure but exposed an avg-BLIP
  Float/BFloat16 mismatch in relationship generation. The dtype retry avoided
  that mismatch but exposed a legacy BLIP `max_length` generation validation
  error under current Transformers. Source patch schema
  `h001_open3dsg_source_patch_v12` aligns relationship image embeddings to the
  loaded BLIP model dtype, switches BLIP generation to `max_new_tokens`, and
  enabled the canonical raw dump retry.
  The guarded generation retry reached Lightning `Testing DataLoader 0`
  `377/377` and wrote `19162` rows to `raw_dump/raw.jsonl`; the container
  then ended with exit code `137`. Docker `open3dsg_raw_dump_identity` reports
  `raw_dump_identity_audit_ready` with no blockers.
- The v13 clean raw-dump-only source rerun ended with exit `137` before raw
  writing because raw export still occurred only at `on_test_epoch_end`.
- Source patch `h001_open3dsg_source_patch_v14` added per-batch raw streaming,
  a resumable `.completed.jsonl`, partial-row repair, and no streaming-mode
  `test_step_outputs` accumulation. The first v14 streaming run exited `137`
  before the first streamed batch, and the retry exited `137` after 294/377
  completed batches. The same-path resume
  `h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227` completed with
  exit `0`: manifest status `raw_dump_stream_complete`, 377/377 completed
  batches, 19,162 rows, dropped/invalid partial rows 0/0. Its SHA256 matches
  canonical `raw_dump/raw.jsonl`, so clean raw-dump source-process provenance is
  now available; earlier exit-137 attempts remain historical run records.
- Docker `open3dsg_adapter_raw_dump` is ready: `19162` raw rows -> `496600`
  prediction rows, with `62` raw rows filtered outside the fixed H001 object
  context and counted in the manifest.
- Docker `open3dsg_geometry_join` is ready: `496600/496600` rows preserved,
  `114600` geometry-checkable rows scored, and G2 variants emitted
  (`obb_only`, `point_subtype`, `point_subtype_no_soft_support`).
- Docker `open3dsg_metric_eval` is ready with no blockers. Key Open3DSG
  H001-family metrics are: semantic_only R@50/R@100 `0.3945/0.4963`,
  Violation@50/@100 `0.1326/0.1195`; probabilistic_recalibrated
  R@50/R@100 `0.3843/0.5580`, Violation@50/@100 `0.0575/0.0803`;
  rule_verified_point_subtype R@50/R@100 `0.4149/0.5238`,
  Violation@50/@100 `0.0/0.0`; family_specific control R@50/R@100
  `0.4530/0.5984`, Violation@50/@100 `0.0228/0.0311`.
- Docker `table_builder` regenerated Table 6 from
  `sources/open3dsg/metrics/metrics.json`; Open3DSG Table 6 hook status is
  `ready`.
- Docker `open3dsg_failure_generator_real` is ready: it generated 57,736 real
  failure-analysis rows from semantic top-100 or geometry-reranked top-100
  union per subgraph, with 0 validation errors. Primary categories include
  semantic_false_positive 27,326, insufficient_geometry_evidence 20,828,
  semantic_and_geometry_failure 5,183, geometry_contradiction 979,
  predicate_family_ambiguity 1,727, rank_only_failure 433, and
  true_positive_supported 1,260. Visual-audit queue rows: 6,162.
- Docker `open3dsg_failure_case_sampler` is ready: it selected 36
  high-severity visual-audit qualitative candidates from 6,162 candidate rows.
  The sample covers geometry_contradiction 14 and
  semantic_and_geometry_failure 22, across proximity 8, relative_vertical 18,
  and support_contact 10. This is a qualitative inspection queue, not an
  additional metric or representative human audit.
- Docker `open3dsg_failure_case_inspection` is ready: it generated
  `failure_cases/{inspection.json,inspection.md}` with 36 inspected cases,
  23/36 demoted by geometry-aware reranking, 13/36 promoted or retained, and
  10/36 rule-violated cases with `p_geom_valid > 0.9`. This supports the
  failure-mechanism narrative while also exposing residual calibration risk.
- Docker `open3dsg_paper_caveats` is ready: it generated
  `paper_caveats/{manifest.json,report.md}` and freezes filtered-train
  3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered
  loadable scope 377/388 contexts, `validation_missing_preprocessed:11`,
  averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and
  residual calibration-risk wording.

Current paper handoff:

- `paper/preview.md` is ready and summarizes current results, caveats,
  reviewer-defense map, optional extension boundary, and recovery files.
- `paper/outline.md` is ready with English/Korean paper skeleton, section-level
  evidence placement, recommended title, title alternatives, three contribution
  statements, abstract skeleton, Introduction logic, Open3DSG caveat placement,
  reviewer-defense plan, manuscript-ready table/figure caption drafts, and
  claim-consistency review across title, contribution, abstract, Introduction,
  table captions, and figure captions. Cross-source results and failure
  analysis are empirical validation, not a fourth contribution.
- `paper/draft.md` is ready as reviewed first-pass manuscript prose covering Related
  Work, Problem Formulation, Method, Experimental Setup, Results/Discussion,
  and Limitations. It still needs citation replacement.
- `paper/figures.md` is ready and locks Figure 1-3 claims/assets before drawing:
  Figure 1 method framework, Figure 2 two-panel R@100/Violation@100 tradeoff,
  and Figure 3 Open3DSG qualitative case panels.
- `paper/generated/figures/` is ready with verified draft SVGs:
  `figure1_framework.svg`, `figure2_tradeoff.svg`, and
  `figure3_failure_cases.svg`. Validation passed for locked Figure 2 values,
  Figure 3 case IDs, and SVG XML parsing.
- `paper/generated/figures/layout_review.md` is ready. Figure 1 was revised to
  foreground failure mechanism -> cause -> design necessity; Figure 2 is kept
  as the strongest recall/violation evidence; Figure 3 is accepted as a draft
  row-card placeholder with a later rendered/crop upgrade recommended for final
  top-tier presentation.

Next required drafting step:

1. Replace Related Work citation placeholders in `paper/draft.md` with final
   BibTeX-style keys.
2. Defer Table 6/Open3DSG caveat compression until the paper-body logic is
   readable end to end;
   keep averaged-BLIP, filtered-train/dev, covered-scope, exact-label denominator,
   `validation_missing_preprocessed:11`, and residual calibration-risk caveats
   explicit for now.
3. Keep a later optional figure-upgrade task for rendered/crop Figure 3
   evidence if a deterministic path is added.

Reproducibility/GitHub portability note:

- `docs/reproducibility.md` records the 2026-05-21 `.gitignore` audit.
- GitHub can carry the runbooks, Docker setup, scripts, reports, compact
  manifests, tables/metric summaries, and paper planning docs.
- Large datasets, checkpoints, features, raw dumps, prediction/verification/
  failure JSONL rows, and model caches remain intentionally ignored and must be
  rebuilt/downloaded or transferred separately on another computer.

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
