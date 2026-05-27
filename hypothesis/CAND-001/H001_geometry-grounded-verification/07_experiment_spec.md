# Experiment Spec

Last updated: 2026-05-19

## Role

This document merges reportability, final claim scope, and the scoped main
experiment implementation spec.

Merged former files:

- `15_reportability.md`
- `23_experiment_spec.md`

## Reportability Verdict

Status:

```text
hypothesis_stage_complete_for_geom_reliability_experiment
```

Fact:

- H001 is viable as a scoped research direction.
- Hardened `VL-SAT` evidence is meaningful and survives a larger held-out
  validation scope.
- G3 controls, structured audit, reduced visual sanity check, and GT-based
  verifier evaluation are complete.
- Arbitrary-baseline and broad open-vocabulary generation claims remain
  blocked beyond measured `VL-SAT` + Open3DSG H001-family evidence.
- The selected top-tier reproduction path produced Open3DSG second-source
  adapter evidence from a Docker-reproduced checkpoint.
- The Open3DSG failure-analysis taxonomy is locked before metric/failure
  inspection and must not be changed after seeing Open3DSG failures without a
  schema version bump.
- The Open3DSG failure-analysis row generator skeleton has a Docker synthetic
  smoke output with 6 rows, 6 primary categories, and 0 validation errors. This
  is contract evidence only, not Open3DSG metric evidence.
- The Open3DSG metric/join runner contract has Docker outputs with
  `input_contract.json`, `output_contract.json`, `metrics.json`,
  `manifest.json`, `commands.md`, and `report.md`. Real Open3DSG prediction
  JSONL, H001 GT JSONL, and geometry verification JSONL are now present; real
  metrics are stored under `experiments/H001_geom_reliability/sources/open3dsg/metrics/`.
- The Open3DSG checkpoint provenance/selection policy has a Docker template
  output under `checkpoint_selection/`. It freezes the primary-selection rule
  before checkpoint inspection and forbids using H001 held-out metrics,
  failure-analysis distribution, or held-out visual inspection to choose the
  primary checkpoint.
- The Open3DSG raw-dump identity checklist has a Docker output under
  `raw_dump_identity/`. It fixes the raw-dump identity denominator to 127 scans,
  388 contexts, and 25,916 directed pairs before raw dump conversion.
- The Open3DSG metric-scope policy has a Docker output under `metric_scope/`.
  It freezes predicate-family mapping, exact-label recall matching, the 2,545
  row in-scope GT denominator, and filtered-train/covered-scope caveats before
  real metric execution.
- Docker table builder has a Table 6 hook that reads the real Open3DSG metrics
  and now marks Table 6 ready with no blockers, scoped to measured H001
  families.
- A modern-VLM semantic-source extension using `Qwen2.5-VL` or `Qwen3-VL` is
  allowed only as a third semantic source / modern VLM extension, not as a
  replacement for the VL-SAT controlled anchor or Open3DSG reproduction anchor.
- The Qwen-VL runtime plan has fixed the recommended primary model to
  `Qwen/Qwen3-VL-4B-Instruct` revision
  `ebb281ec70b05090aa6165b016eac8ec08e71b17`, with local-dir
  `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`.
- The Qwen-VL tiny pilot has 30/30 rendered pair crops after shared-view
  selection gating. Qwen3-VL-4B model cache verification, Docker runtime
  preflight, 3-row tiny inference smoke, and runtime raw-response contract
  validation are ready. The full-source promotion protocol is frozen under
  `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/` with
  127 scans, 388 contexts, 25,916 directed pairs, a maximum 77,748 all-pairs x
  family query rows, and the same 2,545-row in-scope GT denominator.
- The Qwen-VL full-source input audit is ready under
  `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/` with
  77,748 universe query rows, 33,384 inferable input rows, 44,364 missing rows,
  134 shards, and 0 input contract errors.
- The Qwen-VL full-source crop render/preflight is ready under
  `experiments/H001_geom_reliability/sources/qwen_vl/full_source_crops/` with
  33,384 input rows, 11,128 unique pair crops, 11,128 verified crops, and 0
  crop errors. No Qwen model load or inference was run in this crop gate.
- The Qwen-VL full-source inference runner/resume plan is ready under
  `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/`
  with 33,384 planned rows, 134 shards, `record_id` resume key, and no plan
  blockers. Shard `qwen_full_source_shard_0000` completed and validated with
  250 prediction rows, 250 raw responses, parser status `parsed:250`, and 0
  validation errors/warnings. Full-source Qwen paper-metric evaluation has not
  run.
- Robotics/functionality benchmarks such as `SceneFun3D` and `FunGraph3D` are
  relevant expansion targets for functional 3D scene graph reliability, but
  they change the claim from spatial relation reliability to functional or
  affordance relation reliability.

Inference:

- H001 has entered the Docker experiment implementation phase with measured
  `VL-SAT` + Open3DSG evidence.
- The preferred top-tier claim should be cross-source but scoped: measured
  H001-family geometry-consistency reliability, not broad open-vocabulary 3DSSG
  generation improvement.

## Paper Experiment Strategy

The paper strategy is layered, not a single benchmark replacement.

| Layer | Role | Benchmark / Source | Claim enabled |
| --- | --- | --- | --- |
| Main anchor | 3DSSG relation reliability | `3DSSG` / 3RScan with `VL-SAT` | scoped reliability-layer result |
| Reproduction anchor | cross-source 3DSSG evidence | Docker-reproduced `Open3DSG` on `3DSSG` / 3RScan | measured reliability trend within H001 relation families |
| Third semantic source | trend-aligned modern VLM evidence | `Qwen2.5-VL` or `Qwen3-VL` object-pair adapter | modern VLM semantic-source reliability extension |
| Robotics/functionality expansion | optional broader application | `SceneFun3D` / `FunGraph3D` | functional or affordance relation reliability |

Priority:

1. Keep `VL-SAT` and Open3DSG on `3DSSG` / 3RScan as the main 3DSSG
   relation-reliability path.
2. Add Qwen-VL only as a Docker-reproducible third semantic source / modern VLM extension.
3. Treat `SceneFun3D` / `FunGraph3D` as an optional follow-up if the paper
   pivots toward robotics, manipulation, or functional scene graphs.

Do not present Qwen-VL or functional-graph results as replacements for
Open3DSG reproduction unless the research question is explicitly rewritten.

## Allowed Claim

Use this as the main scoped claim:

```text
On reproduced VL-SAT 3DSSG predictions, geometry-calibrated relation
verification improves relation reliability for geometry-checkable families by
reducing geometry-inconsistent top-k predictions while preserving or improving
useful recall.
```

Fallback caveat:

```text
The VL-SAT-only result is a fallback reliability-layer result with a reduced
50-row visual sanity check, not a broad open-vocabulary 3DSSG claim.
```

Preferred current top-tier claim:

```text
Across reproduced VL-SAT and Open3DSG prediction sources, calibrated
geometry-consistency re-ranking improves relation reliability for
geometry-checkable 3DSSG families while preserving useful recall.
```

This upgraded claim is now enabled only within the measured H001 families and
closed-set/GT-object setting because Open3DSG checkpoint reproduction, raw
dump, JSONL export, geometry verification JSONL, metric evaluation, and
locked-schema failure-analysis rows are complete. It must retain filtered-train,
averaged-BLIP, covered-scope, exact-label denominator, residual calibration
risk, and `validation_missing_preprocessed:11` caveats.
Clean v14 streaming raw-dump provenance is available; earlier exit-137 attempts
remain historical run records.
The paper-facing Open3DSG caveat wording is frozen under
`experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/`.

Preferred modern-VLM extension claim after Qwen-VL validation:

```text
When relation candidates or validity judgments are produced by a modern
open-vocabulary VLM such as Qwen2.5-VL or Qwen3-VL from object-pair multi-view
crops, calibrated 3D geometry-consistency evidence improves relation
reliability for geometry-checkable families.
```

This extension claim is blocked until a Docker-reproducible Qwen-VL adapter,
frozen prompt/output schema, identity-preserving prediction JSONL, geometry
join, and metric evaluation are complete. It must not be described as an
Open3DSG checkpoint reproduction result.

Optional robotics/functionality extension claim after SceneFun3D/FunGraph3D
validation:

```text
For functional or affordance-oriented 3D scene graph relations, calibrated
geometry evidence can expose and reduce physically inconsistent functional
relation predictions while preserving task-relevant recall.
```

This claim is blocked until the relation families, ground-truth denominator,
functionality-specific verifier rules, dataset license/access, baseline outputs,
geometry join, and metric protocol are fixed. It must not be mixed with the
current `3DSSG` spatial-relation claim without a separate table and claim
boundary.

Not allowed:

```text
The method broadly improves open-vocabulary 3D scene graph generation.
```

Not allowed:

```text
The method is already baseline-agnostic across 3DSSG predictors.
```

Not allowed:

```text
Results on functional 3D scene graph benchmarks prove the current spatial
3DSSG relation claim, or vice versa.
```

## Fixed Inputs

| Item | Fixed value |
| --- | --- |
| dataset | official `3DSSG_subset` / 3RScan validation-derived held-out scope |
| prediction source | reproduced `VL-SAT` / `vlsat_closed_set` |
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

No experiment implementation may retune scan scope, verifier, thresholds, or
calibration models on held-out prediction rows.

## Research Questions

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

Optional RQ6:

```text
Can the framework be transferred from spatial 3DSSG relations to functional or
affordance relations without changing the claim boundary?
```

## Metrics And Conditions

Primary conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | reproduced `VL-SAT` ranking baseline |
| `probabilistic_recalibrated` | main H001 recall-first condition |
| `rule_verified_point_subtype` | hard-filter diagnostic / zero-violation operating point |
| `family_specific_p_geom_valid` | stricter violation-first operating point |
| `qwen_vl_semantic_only` | third-source modern-VLM semantic-source baseline |
| `qwen_vl_geometry_reranked` | third-source modern-VLM semantic source plus H001 geometry-consistency reranking |

Control conditions:

| Condition | Purpose |
| --- | --- |
| `control_p_geom_valid_only` | tests whether semantics remain necessary |
| `control_distance_only` | tests simple distance heuristic explanation |
| `control_shuffled_geometry` | tests whether geometry distribution alone explains the signal |
| `control_wrong_pair_geometry` | tests whether object-pair identity matters |

Prediction metrics:

- `R@50`
- `R@100`
- `Violation@50`
- `Violation@100`
- delta versus `semantic_only`
- relative violation reduction versus `semantic_only`

Verifier-validity metrics:

- GT-positive nonviolated rate
- GT-derived negative nonsatisfied rate
- `p_geom_valid` AUROC/AUPRC

Audit metrics:

- structured audit strict invalid-only precision
- structured audit quality-issue precision
- reduced visual spot-check target-bucket quality-issue rate
- reduced visual spot-check contradiction rate

## Required Tables

| Table | Content |
| --- | --- |
| Table 1 | main held-out prediction result |
| Table 2 | nontriviality controls |
| Table 3 | GT-based verifier evaluation |
| Table 4 | structured audit and reduced visual sanity check |
| Table 5 | source-specific claim boundary and blocked extensions |
| Table 6 | cross-source result; Open3DSG hook is now ready for measured H001-family evidence, with broader claims still blocked |
| Table 7 | third-source modern-VLM semantic-source result, added only after Qwen-VL adapter metric evidence exists |
| Table 8 | optional functional/robotics benchmark result, added only after SceneFun3D/FunGraph3D protocol evidence exists |

## Required Figures

| Figure | Content |
| --- | --- |
| Figure 1 | framework pipeline: relation predictions, identity-preserving rows, geometry evidence, verifier, `p_geom_valid`, reranking/filtering |
| Figure 2 | reliability-recall tradeoff across main operating points |
| Figure 3 | traceable qualitative cases from audit/visual sanity-check artifacts |

## Docker Requirement

Paper-body experiment implementation must be Docker-based.

Rules:

- do not promote host-only outputs to paper experiment results;
- provide a Dockerfile or compose file before generating final tables;
- pin Python/system dependencies in the experiment root;
- mount large dataset/runtime roots such as `local_dataset/` instead of copying
  them into tracked artifacts;
- record the exact Docker command used for every table/report artifact;
- keep debugging or smoke runs separate from Docker-reproducible paper
  experiment outputs.

## Proposed Experiment Workflow Root

Created after the user explicitly entered the experiment phase:

```text
experiments/H001_geom_reliability/
```

Proposed minimal contents:

```text
experiments/H001_geom_reliability/README.md
experiments/H001_geom_reliability/Dockerfile
experiments/H001_geom_reliability/compose.yaml
experiments/H001_geom_reliability/manifest.json
experiments/H001_geom_reliability/commands.md
experiments/H001_geom_reliability/sources/vlsat/
experiments/H001_geom_reliability/sources/open3dsg/
experiments/H001_geom_reliability/tables/
experiments/H001_geom_reliability/figures/
experiments/H001_geom_reliability/report.md
```

Root naming rationale:

```text
H001_geom_reliability
```

The experiment root is framework-level rather than `VL-SAT`-only because the
preferred top-tier path includes Open3DSG second-source metrics after the first
`VL-SAT` table reproduction.

Current implementation status:

```text
docker_vlsat_table_reproduction_ready
```

The root contains a Docker table builder that generated Table 1-6,
`manifest.lock.json`, `report.md`, and figure specs from locked hypothesis
artifacts.

## Implementation Sequence

E0 freeze manifest:

- collect exact input artifact paths;
- record checksums or row counts;
- fail if counts differ from this spec.

E1 result collector:

- read existing locked hypothesis artifacts;
- normalize metrics into table-ready JSON/CSV;
- avoid rerunning `VL-SAT` unless an input artifact is missing or invalid.

E2 table builder:

- generate the five required tables;
- preserve full precision in machine-readable outputs;
- round only in markdown/LaTeX reports.

E3 figure-case selector:

- select traceable qualitative cases;
- record why each case is representative;
- avoid insufficient-geometry cases unless explicitly used as failure/ambiguity.

E4 experiment report:

- separate `Fact`, `Inference`, and `Claim boundary`;
- include exact commands and artifact paths;
- state that the experiment is scoped to measured H001 families across `VL-SAT`
  and Open3DSG, not broad open-vocabulary 3DSSG generation.

E5 optional extension gate:

- selected reproduction extension is `Open3DSG`, not FROSS;
- create a Dockerized Open3DSG checkpoint reproduction plan if the paper target
  requires cross-predictor evidence;
- use the pre-locked Open3DSG failure-analysis schema under
  `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`;
- Open3DSG checkpoint, identity-preserving raw dump, prediction JSONL export,
  geometry join, metric suite, real failure-analysis rows, and qualitative case
  queue are now ready;
- retain the frozen Open3DSG caveat wording from `paper_caveats/`;
- keep FROSS as a support/contact-only fallback smoke source, not the main
  second-source path.

E6 optional modern-VLM semantic-source gate:

- Qwen-VL is an additional trend-aligned third semantic-source track, not the
  VL-SAT controlled anchor or Open3DSG reproduction anchor;
- current contract/cache status: frozen input JSON Schema, output JSONL
  contract, Docker validator/parser skeleton, 30-row non-held-out tiny pilot
  scope, and 30/30 rendered pair crops are ready under
  `experiments/H001_geom_reliability/sources/qwen_vl/`; Qwen3-VL-4B model
  cache verification, runtime preflight, 3-row tiny inference smoke, and
  runtime raw-response validation are ready;
- current full-source promotion plan status is
  `full_source_promotion_plan_frozen_no_metric_run`; the frozen metric scope is
  127 scans, 388 contexts, 25,916 directed pairs, up to 77,748 all-pairs x
  family query rows, and 2,545 in-scope GT rows;
- current full-source input status is
  `full_source_input_ready_with_missing_rows_no_inference`; it has 33,384
  inferable rows and 134 shards;
- current full-source crop status is
  `full_source_crop_preflight_ready_no_inference`; it verifies 11,128 unique
  pair crops for the 33,384 inferable input rows and ran no Qwen inference;
- current full-source inference runner status is
  `full_source_inference_runner_frozen_no_inference`; shard 0000 status is
  `complete_validated_non_metric`; remaining shard loop status is
  `running_non_metric` in tmux `h001_qwen_vl_infer_remaining`, run id
  `20260527_023111`, for `qwen_full_source_shard_0001` through
  `qwen_full_source_shard_0133`;
- use the locked primary model `Qwen/Qwen3-VL-4B-Instruct` revision
  `ebb281ec70b05090aa6165b016eac8ec08e71b17` first, with local-dir
  `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`;
- fall back to `Qwen/Qwen2.5-VL-3B-Instruct` only if Qwen3-VL runtime support
  blocks progress, and record the fallback revision/local-dir before running;
- run Qwen-VL only through Docker with fixed decoding parameters, prompt
  template, output parser, and artifact manifest;
- input should be identity-preserving object-pair records with scan,
  subgraph, subject id, object id, object labels, selected multi-view crops,
  and optional frozen geometry summary;
- output should be prediction JSONL compatible with the H001 geometry join:
  relation candidate, semantic confidence or calibrated proxy score, raw text
  answer, parser status, and source model metadata;
- compare `qwen_vl_semantic_only` against `qwen_vl_geometry_reranked` with the
  same relation-family metric suite used for `VL-SAT` and Open3DSG;
- report Qwen-VL results as third-source modern-VLM semantic-source evidence,
  not as a trained 3DSSG model, VL-SAT replacement, or Open3DSG checkpoint
  reproduction.

E7 optional robotics/functionality benchmark gate:

- `SceneFun3D` / `FunGraph3D` is an optional application expansion, not the
  main 3DSSG benchmark replacement;
- before implementation, freeze the target relation families and decide which
  geometry evidence is meaningful for functional or affordance relations;
- use only Docker-reproducible dataset staging, baseline/adapted-baseline
  outputs, prediction JSONL export, geometry join, and metric generation;
- keep spatial relation metrics and functional relation metrics in separate
  tables;
- report functionality results as transfer/application evidence, not as proof
  that the method broadly solves open-vocabulary 3DSSG generation.

## Acceptance Criteria

The scoped experiment phase is ready for paper drafting only if:

- all fixed input counts match this spec;
- final table/report artifacts are generated by documented Docker commands;
- all required tables are generated from locked artifacts;
- qualitative examples have traceable source rows;
- report wording stays within the allowed scoped claim;
- broad open-vocabulary generation blockers remain explicit unless new
  metric-bearing source/task evidence is added.

The preferred top-tier phase is ready only if, in addition:

- Open3DSG checkpoint reproduction is Docker-documented;
- Open3DSG raw outputs preserve scan/subgraph/object-pair identity;
- Open3DSG prediction JSONL, geometry join, and metric tables are generated by
  documented Docker commands;
- Open3DSG failure-analysis rows are generated from the locked schema and
  taxonomy designed before metric inspection;
- filtered-train, averaged-BLIP, covered-scope, residual calibration risk, and
  `validation_missing_preprocessed:11` caveats are visible through `paper_caveats/`;
- cross-predictor claims are limited to measured predicate families.

The optional modern-VLM phase is ready only if, in addition:

- Qwen-VL model id/revision, prompt schema, decoding settings, parser,
  contract validator, full-source input universe, crop audit, missing-row
  policy, shard list, and runner resume policy are frozen before held-out metric
  inspection;
- Qwen-VL reserved crop paths are rendered or verified before model inference
  (ready as `full_source_crop_preflight_ready_no_inference`);
- Qwen-VL outputs preserve scan/subgraph/object-pair identity;
- Qwen-VL prediction JSONL, geometry join, and metric tables are generated by
  documented Docker commands;
- claims are limited to measured relation families and to semantic-source
  reliability, not end-to-end 3DSSG generation.

The optional robotics/functionality phase is ready only if, in addition:

- the benchmark is staged with documented Docker commands and license/access
  notes;
- functional relation labels, denominator, and evaluation metrics are fixed
  before metric inspection;
- functionality-specific geometry rules are frozen separately from the current
  `support_contact`, `proximity`, and `relative_vertical` verifier;
- results are reported as application transfer evidence with separate
  limitations.

## User Decision Gate

User judgment needed:

```text
Proceed toward paper drafting with the Docker-generated VL-SAT and Open3DSG
measured H001-family evidence, after final Open3DSG caveat wording.
```

Optional follow-up judgment:

```text
Add Qwen2.5-VL or Qwen3-VL as a third semantic source / modern VLM extension
after recording the Open3DSG reproduction anchor and without promoting Qwen-VL
prompt outputs to end-to-end 3DSSG training evidence.
```

Optional robotics/functionality judgment:

```text
Add SceneFun3D/FunGraph3D only if the paper scope expands from spatial
relation reliability to robotics-oriented functional relation reliability, with
a separate verifier contract and claim boundary.
```
