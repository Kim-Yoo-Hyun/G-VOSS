# Experiment Spec

Last updated: 2026-06-12

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

- H001 is viable as a scoped top-tier direction in the full-validation regime.
- Main AAAI claim scope is the official `3DSSG_subset` 157-scan / 548-context full
  validation split, scoped to measured
  `support_contact`, `proximity`, `relative_vertical`.
- The main Docker result route is `VL-SAT` full-validation + Open3DSG recovery
  branch (`full_validation/recovery_relaxed_views_min2/`, 548/548 contexts), with
  both sources kept in the same fixed split.
- Open3DSG pipeline completion includes checkpoint provenance freeze, identity-preserving
  raw dump, prediction adapter export, geometry join, Table 6 metrics, bootstrap CI,
  full failure rows, deterministic failure inspection, and fixed caveat wording.
- Open3DSG historical/sensitivity branches remain: `533/548` covered branch and
  earlier `377/388` full-historical route.
- Qwen-VL full source route is complete but explicitly fixed as third-source /
  appendix extension for the current AAAI direction.

Inference:

- H001 has entered the Docker experiment implementation phase with measured
  `VL-SAT` + Open3DSG evidence on aligned full-validation scope.
- The preferred top-tier claim is cross-source but scoped: measured geometry-consistency
  reliability, not broad open-vocabulary 3DSSG generation improvement.

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
locked-schema failure-analysis rows are complete. It must retain selected
official non-avg checkpoint provenance, filtered train/dev provenance,
full-validation exact-label denominator, recovery-policy disclosure,
533/548 unmodified-source-route sensitivity, appendix-only historical
127-scan sensitivity, and residual calibration-risk caveats.
Clean-exit raw-dump provenance is available for the paper-facing 548/548
recovery branch. Older historical raw-dump/provenance notes remain local to
their sensitivity branches.
The paper-facing Open3DSG caveat wording is frozen under
`experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`.

Preferred modern-VLM extension claim after Qwen-VL validation:

```text
When relation candidates or validity judgments are produced by a modern
open-vocabulary VLM such as Qwen2.5-VL or Qwen3-VL from object-pair multi-view
crops, calibrated 3D geometry-consistency evidence improves relation
reliability for geometry-checkable families.
```

This extension claim is now supported as appendix/extension evidence only:
Docker Qwen-VL full official validation inference, parser validation, adapter
export, geometry join, metrics/controls, bootstrap CI, failure rows, and
deterministic qualitative inspection are complete. It must not be described as
an Open3DSG checkpoint reproduction result, a VL-SAT/Open3DSG replacement, or
an end-to-end 3DSSG generation result.

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
| dataset | official `3DSSG_subset` / 3RScan full validation split |
| prediction source | reproduced `VL-SAT` full validation plus Open3DSG full-validation recovery branch |
| held-out scans | 157 |
| contexts | 548 |
| candidate directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG recovery prediction rows | 695,916 |
| ground-truth rows | 11,254 |
| in-scope GT denominator | 3,972 |
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
Can the framework be upgraded from the current spatial/support families to
attachment-style physical relations (`attached to`, `hanging on`, `connected
to`) before attempting broader functional or affordance reasoning?
```

Current RQ6 boundary:

- `attachment_deferred` is the preferred future relation-family upgrade because
  it stays close to physical consistency while adding 967 GT rows.
- It is not part of the current AAAI claim.
- Docker G0 scope/schema audit is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/scope_audit/`
  with status `attachment_deferred_scope_schema_ready_no_metric_execution`.
- Docker G1 extractor contract is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor/`
  with status `attachment_deferred_extractor_contract_ready_no_extraction`.
- Docker G1b evidence-only dry run is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/extractor_dry_run/`
  with status `attachment_deferred_extractor_dry_run_ready_no_verifier`.
- The dry run emits surface type, local contact/near-contact, surface normal,
  gravity/hanging cue, contradictory support cue, and
  object-affordance-as-context fields as evidence-only rows before any
  verifier, calibration, or source metric run. It produced 36/36 schema-valid
  rows with 0 validation errors, but all rows remained `partial` at G1b because
  point-contact evidence was reserved for the subsequent G1c validator.
- The extractor contract and dry-run validator forbid `verification_status`,
  `p_geom_valid`, recall credit, and reranking scores.
- Docker G1c point/surface estimator validation is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/point_surface_validation/`
  with status `attachment_deferred_point_surface_validation_ready_no_verifier`.
  It produced 36/36 ready rows, 36 point/normal-available rows, 27
  near-contact rows, and 0 validation errors while preserving the no
  verifier/metric-field boundary.
- Docker G2 verifier-policy design is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/verifier_policy/`
  with status
  `attachment_deferred_verifier_policy_ready_no_decisions_no_metrics`. It
  freezes 9 subtype policies and conservative threshold defaults, but emits no
  decision rows, calibration, source scoring, or metrics.
- Docker G3 train-dev calibration/counterfactual route is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/calibration_counterfactuals/`
  with status
  `attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics`.
  It prepares 315 train/dev positive seeds and 446 counterfactual negative seeds
  with held-out scan overlap 0, but emits no decision rows, fitted calibration,
  source scoring, or metrics. The dev split has no `connected to` positive seed,
  so any future connected-to family-specific calibration claim requires pooled
  calibration, augmented dev selection, or explicit limitation.
- Docker G4 GT policy smoke is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/`
  with status `attachment_deferred_gt_policy_smoke_ready_no_source_metrics`.
  It applies the frozen policy to 36 smoke rows and 761 train/dev seed rows,
  with positive nonviolated 0.9048, counterfactual nonsatisfied 0.8274,
  positive strict satisfied 0.3841, counterfactual strict violated 0.4574, and
  uncertain rate 0.4323. It fits no `p_geom_valid` calibrator and runs no
  source metrics.
- Docker G4b error/visual sanity planning is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/`
  with status `attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics`.
  It freezes 436 review cases, a label-diverse 50-row visual sanity queue, and
  761 calibration-filter rows. Strict candidates are 121 positives and 204
  negatives; 77 false-satisfied counterfactuals, 30 false-violated positives,
  and 329 uncertain rows require review/exclusion/soft-label policy before
  calibration.
- Docker G4c strict-only calibration-filter freeze is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/`
  with status `attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics`.
  It freezes 325 strict calibration rows: 121 strict positives, 204 strict
  negatives, and 436 excluded non-strict rows. `connected to` has no dev strict
  rows, so future family-specific calibration needs pooled calibration,
  augmented dev selection, or an explicit caveat.
- Docker G5a pooled strict calibration fit is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/`
  with status `attachment_deferred_calibration_fit_ready_no_source_metrics`.
  It fits model `h001-attachment-deferred-p-geom-valid-strict-v1` on 242 train
  rows and evaluates on 83 dev rows with dev Brier/NLL/ECE 0.0010/0.0077/0.0071
  and dev AUROC/AUPRC 1.0/1.0. This is calibration-readiness evidence only:
  the strict subset is nearly separable, `connected to` has no dev strict rows,
  and no source predictions are scored.
- Docker G5b bounded source scoring preflight is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/`
  with status `attachment_deferred_source_scoring_preflight_ready_no_metrics`.
  It scores 120 scan-diverse source rows, 60 from VL-SAT and 60 from Open3DSG,
  with evidence ready 120/120 and validation errors 0. This is bounded contract
  evidence only: no full-source scoring, R@K, Violation@K, controls, bootstrap
  CI, or audit is computed.
- Docker G5c full-source scoring/metric protocol freeze is complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/full_source_protocol/`
  with status `attachment_deferred_full_source_protocol_frozen_no_metrics`.
  It freezes 69 deterministic shards for 135,048 full-source rows, output
  schema, source-specific exact-label denominators, metric conditions, and
  control order. VL-SAT covers 967/967 attachment GT rows; Open3DSG covers
  768/967 and must report 199 missing exact-label GT rows as a caveat.
- Docker G5d full-source scoring, source metrics, controls, and bootstrap CI are
  complete under
  `experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`
  with status `attachment_deferred_g5d_full_source_metrics_ready`.
  This remains appendix/preliminary extension evidence because it uses the older
  H001 388/377-context scope, Open3DSG covers only 768/967 exact-label
  attachment rows, `connected to` lacks dev strict rows, and post-G5d
  failure/visual audit is not complete.
- Adding `attachment_deferred` to the main AAAI claim requires explicit final
  user confirmation even after the remaining evidence gates pass.
- Function reasoning should be evaluated only as a secondary pilot after
  attachment relation reliability passes its own verifier/calibration/source
  metric gates.

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
- contract/cache status: frozen input JSON Schema, output JSONL contract,
  Docker validator/parser skeleton, 30-row non-held-out tiny pilot scope,
  Qwen3-VL-4B model cache verification, runtime preflight, 3-row tiny
  inference smoke, runtime raw-response validation, and historical full-source
  route are ready under `experiments/H001_geom_reliability/sources/qwen_vl/`;
- historical 127-scan full-source route is complete but remains non-main
  extension/sanity evidence;
- paper-facing full official validation route is complete through input audit,
  crop preflight, 187/187 shard inference, parser validation, adapter export,
  geometry join, metrics/controls, bootstrap CI, failure rows, and deterministic
  qualitative case inspection;
- current full-validation counts are 110,424 universe query rows, 46,506
  inferable rows, 63,918 missing query rows, 187 shards, 35,131 exported
  predictions, 32,236 in-scope predictions, and 3,972 H001-family GT rows;
- current full-validation metrics are semantic_only R@50/R@100
  `0.2815/0.3600`, probabilistic_recalibrated `0.3215/0.3653`,
  rule_verified_point_subtype `0.3009/0.3630`, and family_specific control
  `0.3379/0.3653`;
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
- selected official non-avg checkpoint, filtered train/dev provenance,
  full-validation exact-label denominator, 548/548 recovery policy, 533/548
  unmodified-source-route sensitivity, appendix-only historical 127-scan
  sensitivity, and residual calibration-risk caveats are visible in paper
  setup/results/captions and experiment table-caveat artifacts;
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
