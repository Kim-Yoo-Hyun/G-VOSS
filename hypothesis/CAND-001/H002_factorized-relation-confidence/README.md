# H002 Factorized Relation Confidence

Current working title:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## Current Status

```text
current_direction = predicate_geometry_compatibility_learning
current_gate = compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries
previous_route = RGA benchmark / target-identifiability first, posterior later
new_route = T_e + Z_e + G_e + C_e + Q_e with two-head p_obs / p_rel decision
posterior_smoke_allowed = false
learned_smoke_allowed_next = completed_internal_grouped_eval_with_family_review
validation_or_test_used = false
paper_level_ready = false
framework_ready_hypothesis_stage = true
experiment_root_skeleton_created = true
docker_preflight_run = true
route_materialization_run = true
materialization_schema_audit_run = true
grouped_split_protocol_run = true
grouped_eval_protocol_run = true
grouped_eval_runner_run = true
grouped_holdout_run = true_internal_candidate_pool_only
claim_boundary_review_run = true
official_validation_test_protocol_plan_run = true
official_validation_usage = false
official_validation_inventory_counted = true
official_source_inventory_run = true
official_source_inventory_ready = true
official_candidate_materialization_protocol_run = true
official_candidate_materialization_docker_run = true
official_candidate_rows_materialized = true
official_candidate_materialization_schema_audit_run = true
official_candidate_materialization_schema_audit_ready = true_with_support_contact_shortcut_caveat
official_metric_protocol_freeze_run = true
official_metric_protocol_freeze_ready = true
official_metric_runner_run = true
official_validation_metric_produced = true
official_metric_runner_ready = true_with_caveats
official_metric_result_review_run = true
paper_level_experiment_execution_gate = passed_with_caveats
paper_result_promotion = not_yet
h001_artifacts_read_only_inventory = true
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

H002는 기존 `factorized posterior target fitting` route에서 전환했다. 전환 이유는
v1-v81 target-construction 과정에서 posterior가 학습할 독립 reliability target이
positive-sparse하거나 shortcut-prone하게 반복 형성됐기 때문이다. 새 H002는 posterior
combiner를 먼저 키우지 않고, relation reliability를 구성하는 evidence representation을
다음처럼 구조적으로 분리한다.

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence quality / observability
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

기존 `coverage`와 `uncertainty`는 `Q_e` 안에서 함께 다룬다. `Q_e`는 relation의
참/거짓을 직접 결정하지 않고 abstain/selective decision을 담당한다.

## Canonical Files

| File | Role |
| --- | --- |
| `README.md` | H002 folder map and current status |
| `summary_branch_v2.md` | current research framing, method direction, TODO, and compact stage interpretation |
| `RGA_framework.md` | RGA diagnostic/evaluation definitions under the compatibility-learning direction |
| `compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit.md` | official validation metric protocol freeze after schema audit |
| `tools/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit.py` | validates schema-audit inputs and writes official metric protocol artifacts |
| `compatibility_dataset_v3_official_metric_runner_after_protocol_freeze.md` | official validation metric runner output summary and caveats |
| `tools/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze.py` | validates Docker official metric outputs and writes runner-stage artifacts |
| `compatibility_dataset_v3_official_metric_result_review_after_runner.md` | official metric result review and paper-level execution gate decision |
| `tools/compatibility_dataset_v3_official_metric_result_review_after_runner.py` | validates official metric outputs and writes result-review gate artifacts |
| `report/report_0702.md` | Korean paper-level experiment gate report after official metric runner |
| `report_0701.md` | Korean hypothesis-stage synthesis report covering claim, method, validation purpose, metrics, relation-family results, blockers, and next steps |
| `compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes.md` | paper/framework readiness review after route-specific probes; separates candidate main rows, diagnostic boundaries, promotion gaps, and blocked claims |
| `tools/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes.py` | validates route-specific artifact readiness and writes the readiness review artifact |
| `compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review.md` | promotion gap plan defining Docker, held-out, calibration, target-independence, and claim-wording gates before paper-level promotion |
| `tools/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review.py` | validates readiness input and writes the staged promotion plan artifact |
| `compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan.md` | Docker and grouped-holdout protocol plan; defines proposed H002 experiment/config/results roots, mounts, split policy, output manifests, controls, and pass/fail gates without creating roots |
| `tools/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan.py` | validates promotion-gap input and writes the Docker/held-out protocol artifact |
| `compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan.md` | validates the H002 experiment/config/results skeleton creation and records owner updates |
| `tools/compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan.py` | checks skeleton owner files and writes the skeleton validation artifact |
| `compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton.md` | records Docker preflight implementation and successful mount/status/read-only boundary check |
| `tools/compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton.py` | validates the Docker preflight run output and writes the preflight stage artifact |
| `compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight.md` | records Docker route materialization output, row counts, feature boundary, and no-metric boundary |
| `tools/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight.py` | validates materialized route rows/model-safe view/hidden manifest and writes the stage artifact |
| `compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization.md` | records Docker materialization schema/leakage/shortcut/split-readiness audit |
| `tools/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization.py` | validates schema audit runtime output and writes the stage artifact |
| `compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit.md` | records internal grouped split creation over the 6952 materialized H002 rows, leakage audit, family split counts, and no-metric boundary |
| `tools/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit.py` | validates grouped split runtime outputs and writes the stage artifact |
| `compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split.md` | records grouped evaluation model views, metric contract, blocked features, output contract, and no-metric boundary |
| `tools/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split.py` | validates grouped split inputs and writes the grouped evaluation protocol artifact |
| `compatibility_dataset_v3_grouped_eval_runner_after_protocol.md` | records Docker grouped evaluation runner execution, internal heldout metrics, controls, family-level behavior, and no-paper-metric boundary |
| `tools/compatibility_dataset_v3_grouped_eval_runner_after_protocol.py` | validates grouped evaluation runtime outputs and writes the stage artifact |
| `compatibility_dataset_v3_grouped_eval_result_review_after_runner.md` | reviews grouped evaluation outputs, assigns family-level claim status, and selects relative-vertical failure analysis before claim lock |
| `tools/compatibility_dataset_v3_grouped_eval_result_review_after_runner.py` | validates grouped runner outputs and writes family decision and predicate review artifacts |
| `compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review.md` | diagnoses the grouped relative-vertical failure as a compatibility feature-extraction issue rather than an intrinsic route failure |
| `tools/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review.py` | audits explicit signed vertical geometry versus runner suffix-based feature extraction and writes repair-next artifact |
| `compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis.md` | records grouped-eval feature extractor repair, Docker rerun, repaired family decisions, and next claim-boundary review |
| `tools/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis.py` | validates the repaired runner/review artifacts and writes the feature-repair stage artifact |
| `compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review.md` | locks allowed and blocked H002 claims after repaired grouped evaluation |
| `tools/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review.py` | validates repaired grouped-eval artifacts and writes claim-boundary, family-role, blocked-claim, and promotion-gap artifacts |
| `compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review.md` | defines the official validation/test protocol plan after claim-boundary lock |
| `tools/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review.py` | validates claim-boundary input, inventories local official split capacity, and writes source/metric/promotion protocol artifacts |
| `compatibility_dataset_v3_official_source_inventory_after_protocol_plan.md` | inventories official validation GT/geometry/source candidate availability after protocol planning |
| `tools/compatibility_dataset_v3_official_source_inventory_after_protocol_plan.py` | streams official validation GT and read-only H001 source artifacts to write source inventory artifacts |
| `compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory.md` | freezes official validation candidate materialization protocol before Docker implementation |
| `tools/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory.py` | validates source inventory and writes row schema, family route, source bridge, blocked-field, and audit contracts |
| `compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol.md` | records Docker official validation candidate materialization output and no-metric boundary |
| `tools/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol.py` | validates Docker materialization outputs, row counts, blocked field absence, and next audit contract |
| `compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation.md` | records official materialization schema/shortcut audit and metric-freeze caveats |
| `tools/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation.py` | validates Docker schema audit outputs and writes metric protocol freeze contract |
| `method_contract_v1.md` | field boundary and train/audit/label input contract for `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e` |
| `geometry_evidence_schema_v1.md` | relation-family geometry-only evidence schema and H001 `p_geom_valid` role |
| `counterfactual_protocol_v1.md` | positive/negative construction, hard-negative matching, no-GT handling, and source-score leakage controls |
| `prototype_dataset_contract_v1.md` | train-only prototype row schema, file layout, label axes, model views, and baseline-ready fields |
| `smoke_baseline_plan_v1.md` | controlled smoke comparison plan, baselines, metrics, controls, and promotion gates |
| `prototype_dataset_materialization_v1.md` | materialization runner, input mapping, output artifact, validation, and current result interpretation |
| `tools/prototype_dataset_materialization_v1.py` | train-only adapter that materializes `artifacts/prototype_dataset_v1/` |
| `smoke_baseline_runner_v1.md` | deterministic smoke runner, metric outputs, gates, and current result interpretation |
| `tools/smoke_baseline_runner_v1.py` | diagnostic runner for source/geometry/shortcut baselines over `artifacts/prototype_dataset_v1/` |
| `learned_smoke_runner_v1.md` | train-internal learned smoke runner, grouped-fold metrics, shortcut probes, and next-step gate |
| `tools/learned_smoke_runner_v1.py` | pure-Python grouped-CV logistic runner for compatibility, observability, and reliability smoke tasks |
| `attachment_numeric_geometry_materialization_v1.md` | attachment-deferred numeric `G_e` materialization, counts, caveats, and next smoke gate |
| `tools/attachment_numeric_geometry_materialization_v1.py` | train-only adapter that extracts attachment numeric `G_e` from locked v18 raw geometry fields |
| `attachment_numeric_geometry_smoke_v1.md` | attachment-specific smoke metrics, hidden shortcut audit, and path-decision gate |
| `tools/attachment_numeric_geometry_smoke_v1.py` | pure-Python grouped-CV smoke runner for attachment compatibility/reliability diagnostics |
| `attachment_smoke_path_decision_v1.md` | attachment promotion decision, blocker analysis, and shortcut-controlled next step |
| `attachment_shortcut_controlled_smoke_v1.md` | strict within-cell balanced attachment smoke result and next expansion decision |
| `tools/attachment_shortcut_controlled_smoke_v1.py` | pure-Python controlled-slice runner for attachment shortcut probes |
| `attachment_controlled_expansion_plan_v1.md` | larger attachment controlled mining/materialization plan |
| `tools/attachment_controlled_expansion_plan_v1.py` | validates existing capacity artifacts and writes the expansion plan artifact |
| `attachment_controlled_candidate_materialization_v1.md` | 400-row attachment controlled candidate materialization result |
| `tools/attachment_controlled_candidate_materialization_v1.py` | joins selected preview rows with raw pair geometry and emits H002 schema rows |
| `attachment_controlled_candidate_smoke_v1.md` | 400-row attachment controlled smoke result with shortcut probes |
| `tools/attachment_controlled_candidate_smoke_v1.py` | source/geometry/compatibility/shortcut smoke runner for controlled attachment candidates |
| `attachment_controlled_candidate_path_decision_v1.md` | attachment 400-row proxy promotion decision and independent-audit next route |
| `attachment_independent_audit_subset_plan_v1.md` | blind review subset plan using current H002 rows and reusable v20 packet assets |
| `tools/attachment_independent_audit_subset_plan_v1.py` | deterministic planner for the 200-row attachment independent audit subset |
| `attachment_independent_audit_label_fill_v1.md` | visible-packet Codex proxy label fill for the 200-row independent audit subset |
| `tools/attachment_independent_audit_label_fill_v1.py` | reviewer-visible-field-only label fill runner |
| `attachment_independent_audit_label_ingestion_v1.md` | post-lock ingestion of independent audit labels into `C_e`, `Q_e`, `p_obs`, and `p_rel` targets |
| `tools/attachment_independent_audit_label_ingestion_v1.py` | hidden-manifest join, target materialization, and shortcut/viability diagnostics |
| `attachment_independent_target_independence_audit_v1.md` | formal target-independence audit for independent attachment `C_e`, `Q_e`, `p_obs`, and `p_rel` targets |
| `tools/attachment_independent_target_independence_audit_v1.py` | target-level predictor-risk and controlled-slice audit runner |
| `attachment_independent_target_repair_plan_v1.md` | repair decision after blocked independent attachment target audit |
| `tools/attachment_independent_target_repair_plan_v1.py` | capacity check and route-selection runner for attachment target repair |
| `attachment_independent_positive_anchor_mining_plan_v1.md` | positive-anchor mining contract after attachment target repair |
| `tools/attachment_independent_positive_anchor_mining_plan_v1.py` | writes the positive-anchor query specs, field boundary, and next-runner contract |
| `attachment_independent_positive_anchor_candidate_mining_v1.md` | mixed-strata attachment candidate mining result |
| `tools/attachment_independent_positive_anchor_candidate_mining_v1.py` | mines train-only positive anchors with matched hard negatives and hidden/visible manifests |
| `attachment_independent_positive_anchor_packet_materialization_v1.md` | packet materialization result for the 560 mixed-strata attachment candidates |
| `tools/attachment_independent_positive_anchor_packet_materialization_v1.py` | creates reviewer-facing visual/mesh packets and label-ready manifests |
| `attachment_independent_positive_anchor_label_fill_v1.md` | visible-packet proxy label fill for the 560 positive-anchor attachment packets |
| `tools/attachment_independent_positive_anchor_label_fill_v1.py` | fills accept/reject/abstain review fields without reading hidden/source/proxy fields |
| `attachment_independent_positive_anchor_label_ingestion_v1.md` | post-lock ingestion of the 560 positive-anchor labels into target/factor/control artifacts |
| `tools/attachment_independent_positive_anchor_label_ingestion_v1.py` | joins locked labels with hidden/control provenance and emits target/shortcut diagnostics |
| `attachment_independent_positive_anchor_target_independence_audit_v1.md` | target-independence audit showing class mass repaired but no controlled slice cleared |
| `tools/attachment_independent_positive_anchor_target_independence_audit_v1.py` | predictor-risk and controlled-slice audit for positive-anchor `C_e`, `Q_e`, `p_obs`, and `p_rel` targets |
| `attachment_independent_positive_anchor_path_decision_after_audit_v1.md` | path decision freezing the positive-anchor attachment target as diagnostic-only |
| `tools/attachment_independent_positive_anchor_path_decision_after_audit_v1.py` | route-selection runner after the positive-anchor target-independence audit |
| `compatibility_learning_scope_plan_v1.md` | H002 method-level family scope after attachment diagnostic freeze |
| `tools/compatibility_learning_scope_plan_v1.py` | scope-plan runner selecting primary, diagnostic, future, and deferred relation families |
| `compatibility_dataset_v2_contract.md` | concrete v2 dataset contract for selected H002 compatibility scope |
| `tools/compatibility_dataset_v2_contract.py` | writes v2 dataset row schema, family quotas, blocked fields, and control gates |
| `compatibility_dataset_v2_materialization_plan.md` | source inventory and route decision before v2 row materialization |
| `tools/compatibility_dataset_v2_materialization_plan.py` | validates available seeds and writes the v2 materialization route/capacity-scan plan |
| `compatibility_dataset_v2_capacity_scan.md` | full-train support/contact and relative-vertical capacity scan under the v2 contract |
| `tools/compatibility_dataset_v2_capacity_scan.py` | scans HL/LH queues for class mass, factor separability, and shortcut risk before materialization |
| `compatibility_dataset_v2_candidate_materialization.md` | controlled v2 candidate row materialization with generated counterfactuals |
| `tools/compatibility_dataset_v2_candidate_materialization.py` | selects anchors, joins raw-witness `G_e`, generates counterfactual rows, and emits v2 candidate artifacts |
| `compatibility_dataset_v2_schema_shortcut_audit.md` | schema leakage and generated-counterfactual shortcut audit for v2 candidate rows |
| `tools/compatibility_dataset_v2_schema_shortcut_audit.py` | writes shortcut probes, blocked-field list, and sanitized v2 model view |
| `compatibility_dataset_v2_sanitized_view_smoke_plan.md` | learned-smoke protocol and stricter smoke-ready view contract for v2 |
| `tools/compatibility_dataset_v2_sanitized_view_smoke_plan.py` | writes `smoke_ready_view.jsonl`, model view whitelist, blocked fields, and runner gates |
| `compatibility_dataset_v2_sanitized_view_smoke_runner.md` | train-only learned smoke result over v2 smoke-ready rows |
| `tools/compatibility_dataset_v2_sanitized_view_smoke_runner.py` | pure-Python grouped-CV runner for sanitized v2 compatibility, shortcut, and corruption controls |
| `compatibility_dataset_v2_failure_analysis.md` | diagnosis of sanitized v2 smoke failure and target-redesign requirements |
| `tools/compatibility_dataset_v2_failure_analysis.py` | joins smoke predictions with audit-only provenance to analyze geometry-only dominance and failed controls |
| `compatibility_dataset_v2_target_redesign_plan.md` | v3 same-geometry multi-predicate target redesign after v2 failure analysis |
| `tools/compatibility_dataset_v2_target_redesign_plan.py` | writes route decisions, family routes, gate contract, and selected v3 contract path |
| `compatibility_dataset_v3_contract.md` | v3 predicate-conditioned same-geometry multi-predicate dataset contract |
| `tools/compatibility_dataset_v3_contract.py` | writes v3 row schema, family contract, blocked fields, model views, and smoke gates |
| `compatibility_dataset_v3_capacity_scan.md` | full train-side capacity scan for v3 same-geometry vertical groups |
| `tools/compatibility_dataset_v3_capacity_scan.py` | scans `match_rows.jsonl` for same-G higher/lower capacity and axis-control risk |
| `compatibility_dataset_v3_candidate_materialization.md` | controlled 400-row v3 same-G higher/lower candidate materialization result |
| `tools/compatibility_dataset_v3_candidate_materialization.py` | materializes v3 candidate rows with matched visible-pair axis controls |
| `compatibility_dataset_v3_schema_shortcut_audit.md` | formal schema and shortcut audit for v3 candidate rows and smoke-ready view |
| `tools/compatibility_dataset_v3_schema_shortcut_audit.py` | emits stricter `smoke_ready_view.jsonl` and audits allowed/blocked feature shortcuts |
| `compatibility_dataset_v3_sanitized_view_smoke_plan.md` | frozen train-only learned-smoke input contract, model views, controls, and gates for v3 |
| `tools/compatibility_dataset_v3_sanitized_view_smoke_plan.py` | writes the v3 smoke plan artifact without running a learned model |
| `compatibility_dataset_v3_sanitized_view_smoke_runner.md` | train-only grouped-CV v3 learned-smoke result and gate interpretation |
| `tools/compatibility_dataset_v3_sanitized_view_smoke_runner.py` | pure-Python grouped-CV runner for v3 compatibility, shortcut, wrong-T, and shuffled-G controls |
| `compatibility_dataset_v3_result_review_and_family_extension_decision.md` | decision accepting v3 as scoped `relative_vertical` `C_e` proof and selecting support/contact evidence probe |
| `tools/compatibility_dataset_v3_result_review_and_family_extension_decision.py` | writes v3 result review, route table, family table, and next-plan contract |
| `compatibility_dataset_v3_support_contact_evidence_probe_plan.md` | support/contact evidence probe contract before materialization or learned smoke |
| `tools/compatibility_dataset_v3_support_contact_evidence_probe_plan.py` | writes support/contact evidence-axis, route, blocked-action, and runner contract artifacts |
| `compatibility_dataset_v3_support_contact_evidence_probe_runner.md` | support/contact evidence probe result blocking numeric-only smoke |
| `tools/compatibility_dataset_v3_support_contact_evidence_probe_runner.py` | scans support/contact train queues and v2 diagnostics for source inventory, evidence-axis availability, shortcut risk, and path decision |
| `compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan.md` | support/contact mesh/pose/contact and multi-view audit-first evidence extension plan |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan.py` | writes source snapshot, evidence-axis plan, factor boundary, route decision, and source-inventory runner contract |
| `compatibility_dataset_v3_support_contact_visual_mesh_source_inventory.md` | source join inventory for support/contact mesh/pose/contact evidence |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory.py` | scans support/contact train queue rows against 3RScan mesh, semseg, aligned PLY, sequence, and packet-template sources |
| `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan.md` | feature-probe plan for support/contact mesh/pose/contact `G_e` candidates |
| `tools/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan.py` | writes feature family plan, probe metrics, sampling policy, leakage controls, and runner contract |
| `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner.md` | executed support/contact mesh/pose/contact feature probe result |
| `tools/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner.py` | derives Tier A semseg OBB/normal features and Tier B aligned PLY contact-proxy features |
| `compatibility_dataset_v3_support_contact_feature_probe_result_review.md` | decision after reviewing support/contact feature probe diagnostics |
| `tools/compatibility_dataset_v3_support_contact_feature_probe_result_review.py` | reviews feature derivability, predicate contrast, shortcut risk, and next target-design route |
| `compatibility_dataset_v3_support_contact_pose_conditioned_target_plan.md` | target-design plan for support/contact same-geometry `lying on` / `standing on` compatibility |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan.py` | writes target contract, row schema, quota plan, model/control plan, and capacity-scan contract |
| `compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan.md` | capacity scan result for pose-conditioned same-geometry support/contact anchors |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan.py` | scans train-side support/contact anchors under the frozen target contract |
| `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan.md` | materialization policy for the frozen 200-anchor support/contact target |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan.py` | writes materialization contract, row schema, blocked fields, output manifest, and downstream gates |
| `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization.md` | materialized 400-row same-`G_e` support/contact candidate dataset |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization.py` | expands frozen 200 anchors into candidate rows, smoke-ready view, hidden manifest, and precheck artifacts |
| `compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit.md` | schema leakage and single-field shortcut audit for pose-conditioned support/contact rows |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit.py` | writes stricter smoke-ready view, shortcut probes, blocked-field audit, and group-integrity audit |
| `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan.md` | frozen learned-smoke input contract, model views, controls, and gates for support/contact pose-conditioned rows |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan.py` | writes the train-only smoke plan artifact without running a learned model |
| `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner.md` | train-only grouped-CV smoke result for support/contact predicate-geometry compatibility |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner.py` | runs support/contact pose-conditioned learned smoke with wrong-T and shuffled-G controls |
| `compatibility_dataset_v3_support_contact_pose_conditioned_result_review.md` | decision accepting support/contact pose-conditioned result as scoped `C_e` mechanism proof |
| `tools/compatibility_dataset_v3_support_contact_pose_conditioned_result_review.py` | reviews runner gates, claim boundary, family route, caveats, and next synthesis contract |
| `compatibility_dataset_v3_multi_family_result_synthesis_plan.md` | two-family `C_e` claim boundary, reviewer-risk decision, and next independent-validity target plan |
| `tools/compatibility_dataset_v3_multi_family_result_synthesis_plan.py` | synthesizes relative-vertical and support/contact result reviews into one route decision artifact |
| `compatibility_dataset_v3_independent_validity_target_plan.md` | GT-anchored train-side independent validity target contract and source-inventory route |
| `tools/compatibility_dataset_v3_independent_validity_target_plan.py` | compares target-source options, counts train GT capacity, and writes the independent-validity plan artifact |
| `compatibility_dataset_v3_independent_validity_source_inventory.md` | source/GT/geometry/hard-negative inventory for independent validity materialization feasibility |
| `tools/compatibility_dataset_v3_independent_validity_source_inventory.py` | streams train `match_rows.jsonl` and writes family inventory, capacity gates, target pools, and previews |
| `compatibility_dataset_v3_independent_validity_materialization_plan.md` | row quota, schema, matching, no-GT abstain, and audit-gate plan for independent validity rows |
| `tools/compatibility_dataset_v3_independent_validity_materialization_plan.py` | validates source inventory and writes the frozen candidate materialization contract |
| `compatibility_dataset_v3_independent_validity_candidate_materialization.md` | materialized GT-anchored independent validity candidate rows, quota audit, cap-relaxation note, and next audit boundary |
| `tools/compatibility_dataset_v3_independent_validity_candidate_materialization.py` | streams train `match_rows.jsonl`, emits candidate rows, model-safe view, hidden manifest, quota audit, and schema precheck |
| `compatibility_dataset_v3_independent_validity_schema_shortcut_audit.md` | schema leakage and shortcut-risk audit for the independent validity candidate artifact |
| `tools/compatibility_dataset_v3_independent_validity_schema_shortcut_audit.py` | writes sanitized primary view and audits allowed/blocked single-feature shortcuts before learned smoke |
| `compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit.md` | route decision after independent validity shortcut audit blocked learned smoke |
| `tools/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit.py` | computes current-artifact repair capacity and selects the full-train stratum-repair capacity scan |
| `compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan.md` | full-train exact semantic-stratum repair capacity scan for independent validity |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan.py` | scans train `match_rows.jsonl` for exact predicate-class mixed strata and writes repair capacity artifacts |
| `compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan.md` | exact predicate-class balanced materialization plan for repaired independent-validity rows |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan.py` | writes stratum quotas, schema boundary, blocked-field table, and next materialization contract |
| `compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization.md` | materialized exact-stratum repaired train-only independent-validity rows |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization.py` | streams train `match_rows.jsonl`, applies exact-stratum quotas, and writes candidate/model-safe/hidden artifacts |
| `compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit.md` | schema leakage and residual shortcut audit for exact-stratum repaired rows |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit.py` | audits model-safe view, critical semantic/source probes, raw geometry probes, and hidden construction probes |
| `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan.md` | learned-smoke input, baseline, control, and gate contract for repaired sanitized rows |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan.py` | writes `smoke_ready_view.jsonl`, model views, controls, gates, profile, and input manifest |
| `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner.md` | train-only grouped-CV learned smoke result for the repaired sanitized rows |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner.py` | pure-Python grouped-CV runner for semantic/source/geometry/compatibility/factorized views and controls |
| `compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review.md` | result review, claim boundary, family scope, and next-route decision after the repaired smoke passed |
| `tools/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review.py` | validates runner outputs and writes claim boundary, route decision, family scope, and reviewer-risk artifacts |
| `compatibility_dataset_v3_independent_validity_calibration_scope_plan.md` | calibration metric audit and next-scope decision after the repaired smoke review |
| `tools/compatibility_dataset_v3_independent_validity_calibration_scope_plan.py` | recomputes proper binary calibration metrics, writes route decisions, and selects support/contact balancing |
| `compatibility_dataset_v3_independent_validity_support_contact_balancing_plan.md` | support/contact-primary independent-validity capacity diagnosis and materialization contract |
| `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan.py` | validates prior artifacts, compares support/contact capacity routes, and writes the selected materialization contract |
| `compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization.md` | materialized support/contact-primary independent-validity candidate dataset and cap/schema precheck summary |
| `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization.py` | streams train match rows, materializes 1200 support/contact rows, and writes model-safe/hidden manifests |
| `compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit.md` | schema leakage and residual shortcut audit for support/contact-primary independent-validity rows |
| `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit.py` | audits model-safe rows, critical semantic/source probes, raw geometry probes, source-confidence probes, and hidden construction probes |
| `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan.md` | full-train support/contact class-pair and predicate-class repair capacity scan |
| `tools/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan.py` | scans support/contact train rows for within-class mixed accept/reject capacity after shortcut audit |
| `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan.md` | path decision freezing support/contact independent-validity as diagnostic-only |
| `tools/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan.py` | validates repair-capacity result and writes the route decision table |
| `compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze.md` | H002 scope synthesis after freezing support/contact independent-validity |
| `tools/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze.py` | writes current claim boundary, family scope, reviewer risks, route decision, and next target-source contract |
| `compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis.md` | decision selecting the next independent target source after scope synthesis |
| `tools/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis.py` | writes target-source route decision, support/contact audit contract, optional relation probes, and reviewer risks |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion.md` | post-lock ingestion of support/contact visual/mesh audit labels into `C_e`, `Q_e`, `p_obs`, and `p_rel` targets |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion.py` | joins locked labels with hidden manifest, emits target artifacts, and runs shortcut diagnostics |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion.md` | class-pair controlled repair decision and train-full repair candidate mining result |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion.py` | scans train-full support/contact queues, verifies repair capacity, and emits a 480-row class-pair-controlled repair candidate set |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization.md` | visible packet materialization result for the 480 class-pair repair candidates |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization.py` | materializes pair crop, mesh card, and multi-view sheet assets for class-pair repair candidates |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill.md` | visible-field-only Codex proxy label fill for the 480 class-pair repair packets |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill.py` | fills repair packet labels without hidden proxy/source/old-geometry fields |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion.md` | post-lock target ingestion and shortcut audit for class-pair repair labels |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion.py` | joins locked repair labels with hidden manifest and audits class-pair/generic shortcuts |
| `compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion.md` | path decision freezing support/contact visual/mesh class-pair repair as diagnostic-only |
| `tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion.py` | validates repair label ingestion, checks generic-filtered alternative, and writes route/risk decisions |
| `compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze.md` | all-relation-family scope synthesis selecting proximity / `close by` as the first active probe |
| `tools/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze.py` | counts Open3DSG train-full relation types, H002 queue coverage, family priorities, and route decision |
| `compatibility_dataset_v3_relation_family_generalization_capacity_scan.md` | all-family capacity scan selecting proximity / `close by` target plan next |
| `tools/compatibility_dataset_v3_relation_family_generalization_capacity_scan.py` | scans H002 queue status, class-pair mixing, and per-predicate capacity across relation families |
| `compatibility_dataset_v3_proximity_close_by_target_plan.md` | proximity / `close by` target contract before materialization or learned smoke |
| `tools/compatibility_dataset_v3_proximity_close_by_target_plan.py` | writes close-by label policy, evidence schema, hard-negative controls, shortcut gates, and source-inventory contract |
| `compatibility_dataset_v3_proximity_close_by_source_inventory.md` | train-only close-by source inventory and materialization route decision |
| `tools/compatibility_dataset_v3_proximity_close_by_source_inventory.py` | scans close-by near/far/abstain capacity, feature availability, matched controls, and gates |
| `compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan.md` | close-by candidate materialization quota, cap, model-view, and control contract |
| `tools/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan.py` | writes the close-by materialization plan without selecting rows |
| `compatibility_dataset_v3_proximity_close_by_candidate_materialization.md` | materialized close-by train-only rows, model-safe view, hidden manifest, quota/cap/schema precheck |
| `tools/compatibility_dataset_v3_proximity_close_by_candidate_materialization.py` | materializes close-by candidate rows from the frozen plan |
| `compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit.md` | schema leakage and shortcut-risk audit blocking close-by learned smoke |
| `tools/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit.py` | audits distance/source/class/p_geom shortcuts over primary and diagnostic close-by rows |
| `compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit.md` | path decision freezing close-by as diagnostic/generality evidence and selecting support/contact individual probes |
| `tools/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit.py` | validates close-by audit blockers and writes route, risk, and next-probe artifacts |
| `compatibility_dataset_v3_support_contact_individual_predicate_probe_plan.md` | plan for predicate-specific `standing on`, `lying on`, and `supported by` source inventory after close-by freeze |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan.py` | validates prior support/contact and close-by artifacts, writes predicate plan, evidence policy, gates, and route decisions |
| `compatibility_dataset_v3_support_contact_individual_predicate_source_inventory.md` | full-train source inventory for separate `standing on`, `lying on`, and `supported by` support/contact probes |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory.py` | scans train-side RGA queues, role capacity, same-G anchors, source availability, and shortcut risks by predicate |
| `compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan.md` | route-aware materialization plan for `standing on` / `lying on` main compatibility rows and `supported by` diagnostic rows |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan.py` | validates source inventory and writes quotas, route table, model-view contract, blocked fields, and shortcut-audit plan |
| `compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization.md` | materialized 800-row support/contact individual predicate candidate set with cap-relaxation warning |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization.py` | streams train RGA queues, selects route-aware rows, computes semseg OBB `G_e`, and emits model-safe/hidden artifacts |
| `compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit.md` | schema leakage and shortcut audit for the 800-row support/contact individual predicate artifact |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit.py` | audits model-safe/hidden shortcut probes and emits a 640-row sanitized smoke-planning view |
| `compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan.md` | train-only learned-smoke input contract, model views, controls, and gates for support/contact individual predicates |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan.py` | writes `smoke_ready_view.jsonl`, plan files, model views, controls, gates, and input manifest |
| `compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner.md` | train-only grouped-CV smoke result for support/contact individual predicate compatibility |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner.py` | runs `T_e`, `G_e`, interaction, factorized, wrong-T, and shuffled-G smoke controls |
| `compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis.md` | failure analysis and route decision after weak support/contact individual predicate smoke |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis.py` | joins predictions, smoke-ready features, and hidden provenance to analyze failure axes |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan.md` | point/multiview evidence plan after OBB-only support/contact diagnostic freeze |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan.py` | validates failure-analysis inputs, checks asset readiness, and writes `G_e`/`Q_e` separation and source-inventory contract |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory.md` | source inventory for point-pair, mesh contact, multiview packet, and non-constant `Q_e` readiness |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory.py` | joins 800 train-only candidates with 3RScan assets and writes `G_e`/`Q_e` materialization contract |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan.md` | materialization plan for separate `G_e` point/mesh/contact/pose and `Q_e` observability blocks |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan.py` | writes feature-block schema, model views, controls, blocked fields, output schema, and runner contract |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization.md` | materialized `G_e` point/contact, `Q_e` observability, source/visual audit manifests, and control manifest |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization.py` | parses aligned PLY point stats, emits model-safe rows, hidden manifests, feature stats, and validation audit |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit.md` | schema leakage and shortcut audit for point/contact/observability materialized rows |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit.py` | audits model-safe feature paths, allowed/hidden shortcut probes, controls, and emits smoke-ready rows |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan.md` | train-only smoke input contract, model views, controls, and gates for point/contact/observability rows |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan.py` | writes normalized `smoke_ready_view.jsonl`, model views, control plan, gate plan, feature manifest, and input manifest |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner.md` | train-only grouped-CV point/contact/observability smoke result and near-threshold diagnostic interpretation |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner.py` | pure-Python grouped-CV runner for point/contact `C_e`, `Q_e`, shortcut, wrong-T, and shuffled-G/Q controls |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis.md` | near-threshold failure analysis, slice diagnosis, and paper-facing support/contact claim boundary |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis.py` | joins smoke predictions with model-safe, source, visual, and control manifests for post-hoc diagnostic analysis |
| `compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position.md` | final support/contact claim-position decision before multi-family synthesis |
| `tools/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position.py` | validates failure analysis and writes claim position, relation-route table, and reviewer-risk artifacts |
| `compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview.md` | multi-family H002 claim skeleton, relation route roles, blocked claims, and next ablation/table planning gate |
| `tools/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview.py` | validates relative/support/proximity/attachment inputs and writes claim skeleton, family route, evidence, reviewer-risk, and next-plan artifacts |
| `compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis.md` | candidate H002 table, ablation, control, reviewer-risk, and promotion-boundary contract before final main-table selection |
| `tools/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis.py` | validates the multi-family synthesis artifact and writes table specs, ablation matrix, control matrix, promotion gates, and wording constraints |
| `compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan.md` | all-family coverage/gap audit after candidate table planning, including next active relation-family probe decision |
| `tools/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan.py` | validates candidate table and all-relation inventory artifacts, writes family/predicate coverage gap tables, and selects the next schema probe |
| `compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit.md` | size-relative schema/source-adapter probe plan for `bigger than` / `smaller than` |
| `tools/compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit.py` | validates coverage audit inputs and writes size-relative source adapter, geometry schema, target construction, controls, and model-view contracts |
| `compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan.md` | train-side `bigger than` / `smaller than` source inventory, OBB join, size-margin, class-pair, and same-G predicate-flip capacity result |
| `tools/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan.py` | scans 3DSSG train relations against 3RScan semseg OBBs and writes size-relative source inventory artifacts without materializing model rows |
| `compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory.md` | frozen size-relative same-G predicate-flip row quota, model-safe schema, blocked fields, controls, caps, and output manifest plan |
| `tools/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory.py` | validates source inventory and writes the size-relative materialization contract without creating rows |
| `compatibility_dataset_v3_size_relative_candidate_materialization_after_plan.md` | materialized size-relative same-G predicate-flip rows, model-safe views, hidden/group manifests, and schema precheck |
| `tools/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan.py` | materializes train-only size-relative candidates from 3DSSG/3RScan sources under the frozen plan |
| `compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization.md` | schema leakage, single-feature shortcut, hidden construction, and group-integrity audit for size-relative rows |
| `tools/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization.py` | audits materialized size-relative rows and emits the 2400-row smoke-ready view |
| `compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit.md` | train-only runner-ready view, model comparisons, controls, and gates for size-relative learned smoke |
| `tools/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit.py` | writes the size-relative smoke plan artifact without running a learned model |
| `compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan.md` | train-only grouped-CV size-relative learned smoke result and control interpretation |
| `tools/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan.py` | runs the size-relative smoke models, wrong-T/shuffled-G/sign-flip controls, and paired-margin audit |
| `compatibility_dataset_v3_size_relative_smoke_result_review_after_runner.md` | claim-position review for the passed size-relative smoke result |
| `tools/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner.py` | validates the size-relative runner artifact and freezes route role, calibration caveat, and next synthesis step |
| `compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative.md` | updated multi-family evidence-routing synthesis after adding size-relative |
| `tools/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative.py` | validates prior synthesis and size-relative review, then writes updated route/evidence/risk tables and next table-plan contract |
| `compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis.md` | updated table, ablation, control, and promotion-gate contract after size-relative synthesis |
| `tools/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis.py` | validates the size-relative-aware synthesis and writes updated table/ablation/control/gate artifacts |
| `compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan.md` | route-coverage sufficiency review selecting additional relation-family sweep before promotion |
| `tools/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan.py` | validates the size-relative-aware table plan and writes coverage decision, expansion queue, and next sweep contract |
| `compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review.md` | schema-first additional family sweep plan with predicate-level fallback policy |
| `tools/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review.py` | validates the coverage review and writes family sweep, predicate fallback, probe queue, and execution gate artifacts |
| `compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan.md` | reference-frame protocol for `left`/`right`/`front`/`behind`/`in front of` before source inventory |
| `tools/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan.py` | validates the sweep plan and writes frame protocol, evidence schema, controls, blocked fields, and source-inventory contract |
| `compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan.md` | train-side source inventory for relative-horizontal anchors, frame availability, axis alignment, and shortcut concentration |
| `tools/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan.py` | scans 3DSSG train/full relation sources and 3RScan centroid/OBB/view availability before materialization |
| `compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory.md` | frozen train-only materialization quota, frame, Q_e, feature, control, and output contract for relative-horizontal rows |
| `tools/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory.py` | validates the source inventory and writes the relative-horizontal materialization plan artifact |
| `compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan.md` | materialized train-only same-G relative-horizontal rows, model-safe views, hidden manifest, group manifest, and schema precheck |
| `tools/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan.py` | materializes `left/right` and `front/behind` same-G predicate-flip rows with Q_e diagnostics under the frozen plan |
| `compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization.md` | schema leakage and shortcut audit for relative-horizontal materialized rows, plus smoke-ready view generation |
| `tools/compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization.py` | audits T-only/G-only/hidden construction shortcuts and emits relative-horizontal `smoke_ready_view.jsonl` |
| `compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit.md` | train-only relative-horizontal smoke input contract, model views, controls, and promotion gates |
| `tools/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit.py` | writes runner-ready `smoke_ready_view.jsonl`, smoke plan, model/control/gate plans, and input manifest |
| `compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan.md` | train-only grouped-CV relative-horizontal smoke result and control interpretation |
| `tools/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan.py` | runs semantic-only, geometry-only, concat, interaction, wrong-T, shuffled-G, sign-flip, wrong-frame, and endpoint-swap controls |
| `compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner.md` | route-position decision after relative-horizontal smoke runner |
| `tools/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner.py` | validates relative-horizontal runner outputs and writes route/claim/risk artifacts |
| `compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal.md` | updated multi-family route synthesis after adding relative-horizontal |
| `tools/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal.py` | merges previous route synthesis with relative-horizontal review artifacts |
| `compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis.md` | table, ablation, control, and promotion-gate contract after relative-horizontal synthesis |
| `tools/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis.py` | validates the updated synthesis and emits table/ablation/control/gate artifacts |
| `compatibility_dataset_v3_supported_by_decomposition_smoke_runner.md` | train-only R6 `supported by` decomposition smoke result and diagnostic interpretation |
| `tools/compatibility_dataset_v3_supported_by_decomposition_smoke_runner.py` | runs grouped-CV p_obs/p_rel decomposition smoke with `T_e`, `G_e`, `Q_e`, shuffled controls, and hidden probes |
| `compatibility_dataset_v3_supported_by_decomposition_smoke_result_review.md` | review decision freezing R6 as superordinate-support diagnostic, not main factorized-route success |
| `tools/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review.py` | validates R6 runner outputs and writes route position, claim boundary, reviewer risks, and next route-map update |
| `compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review.md` | updated H002 route map after R6 diagnostic freeze and selected R7 attachment observability next |
| `tools/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review.py` | merges R6 review with frozen route manifests and writes updated route map, deltas, boundaries, and next active route |
| `compatibility_dataset_v3_attachment_observability_target_plan.md` | R7 target/evidence plan for `attached to`, `hanging on`, and diagnostic `connected to` before materialization |
| `tools/compatibility_dataset_v3_attachment_observability_target_plan.py` | validates route-map/manifest inputs and writes the R7 observability-first target contract, gates, and next source-inventory plan |
| `compatibility_dataset_v3_attachment_observability_source_inventory.md` | R7 source inventory showing `attached to`/`hanging on` materialization readiness and `connected to` topology diagnostic boundary |
| `tools/compatibility_dataset_v3_attachment_observability_source_inventory.py` | streams full-train R7 candidates, checks scan/packet evidence availability, and writes route readiness before materialization |
| `compatibility_dataset_v3_attachment_observability_materialization_plan.md` | plan for model-safe R7 `G_e`/`Q_e` materialization, hidden targets, controls, and connected-to diagnostic boundary |
| `tools/compatibility_dataset_v3_attachment_observability_materialization_plan.py` | validates R7 source inventory and writes row quotas, factor blocks, output contract, blocked fields, controls, and next materialization step |
| `compatibility_dataset_v3_attachment_observability_materialization.md` | materialized R7 train-only source/model-safe/target/hidden/control views with `G_e`/`Q_e` separation |
| `tools/compatibility_dataset_v3_attachment_observability_materialization.py` | writes R7 materialization artifacts and validates that model-safe rows exclude hidden construction fields and targets |
| `compatibility_dataset_v3_attachment_observability_schema_shortcut_audit.md` | R7 model-safe leakage and shortcut audit; blocks learned smoke because class-pair shortcuts solve current p_obs/p_rel targets |
| `tools/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit.py` | audits R7 materialization, writes shortcut probes, diagnostic profiles, and blocked smoke-ready views |
| `compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit.md` | path decision selecting one full-train class-pair-balanced R7 repair mining attempt before diagnostic freeze |
| `tools/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit.py` | validates R7 audit blockers, computes current repair capacity, and writes next mining contract |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan.md` | R7 repair mining plan that requires exact predicate/class-pair capacity scan before packet mining |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan.py` | validates the R7 path decision and writes quota, field-boundary, seed-cell, and capacity-scan contracts |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan.md` | R7 full-train exact predicate/class-pair capacity scan; passes candidate-mining gate for `attached to` and `hanging on` |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan.py` | streams full-train R7 rows, computes mixed accept/reject proxy capacity under scan caps, and selects candidate mining next |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining.md` | R7 controlled train-only candidate mining result for `attached to` and `hanging on` before packet materialization |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining.py` | mines exact predicate/class-pair mixed candidate rows and writes internal candidates, packet requests, quota audit, and group manifest |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan.md` | R7 packet/material evidence generation plan for the 480 class-pair repair candidates |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan.py` | validates candidate inputs, inventories scan/mesh/multiview readiness, and writes visible/hidden packet planning artifacts |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization.md` | R7 packet materialization result; 480 label-ready visible packets for `attached to`/`hanging on` |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization.py` | materializes reviewer-facing packets, visible review sheet, hidden asset manifest, readiness manifest, and leakage checks |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill.md` | R7 visible packet label-fill result for the 480 class-pair repair packets |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill.py` | fills observability/relation/evidence-quality/endpoint labels from the visible sheet and packet assets only |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion.md` | R7 label ingestion result and target viability summary before schema/shortcut audit |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion.py` | ingests visible labels, joins hidden audit fields after label lock, writes target rows, viability, risk register, and model-input boundary |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit.md` | R7 class-pair repair schema/shortcut audit blocking learned smoke due class-prior shortcuts |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit.py` | audits R7 class-pair repair targets, writes shortcut probes, controlled-strata capacity, and diagnostic model view |
| `compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit.md` | path decision freezing current R7 class-pair repair as diagnostic and selecting scope synthesis |
| `tools/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit.py` | validates R7 shortcut blockers and writes diagnostic-freeze route, risk, and next-scope contract |
| `compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze.md` | H002 route-scope synthesis after freezing current R7 artifact as diagnostic |
| `tools/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze.py` | updates family/evidence route tables, freezes R7 as diagnostic/future, and selects paper/framework readiness review |
| `report/report_0627.md` | current relation type results and H002 status summary after scope synthesis |
| `report/report_0625.md` | transition report from old H002 to new H002 |
| `report/report_0623.md` | earlier report before the 2026-06-25 direction transition |
| `report/feasibility_check.md` | posterior combiner, multi-view, and risk-aware reranking feasibility notes |
| `stages/` | grouped v1-v81 stage history |
| `artifacts/` | raw per-stage outputs and generated audit artifacts |

## New Method Sketch

```text
Geometry-only evidence encoder -> G_e
Semantic-content encoder -> T_e
Source-confidence encoder -> Z_e
Compatibility head: compatibility(T_e, G_e) -> C_e
Evidence-quality head -> Q_e
Decision heads -> p_obs, p_rel
```

Key principles:

- predicate/source score must not enter the geometry-only evidence encoder;
- source confidence `Z_e` must not enter the compatibility head;
- `G_e` should be vector/token evidence, not only a scalar;
- H001 `p_geom_valid` can be reused as a rule-based geometry baseline or teacher;
- compatibility positives must be GT, audit-accepted, or high-precision verified subsets;
- no-GT rows are not automatically negatives;
- RGA remains diagnostic/evaluation, not the main method claim.

## Immediate TODO

1. `compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes`
   - decide which H002 route-specific artifacts can support a paper/framework plan and which remain diagnostic/future.
   - produce allowed/blocked claim table, candidate main table rows, promotion requirements, and reviewer-risk checklist.
   - keep current R7 artifact diagnostic-only and do not claim calibrated `p_rel` / `p_obs`.

## Current Prototype Dataset

Default materialization output:

```text
artifacts/prototype_dataset_v1/
```

Current counts:

```text
prototype_rows = 694
counterfactual_groups = 67
compatibility positive / negative / unknown = 67 / 67 / 560
reliability accept / reject / abstain = 101 / 442 / 151
validation_errors = 0
```

Interpretation:

- `support_contact` and `relative_vertical` are compatibility-smoke-ready with numeric `G_e`.
- `attachment_deferred` numeric `G_e` is materialized separately in
  `artifacts/attachment_numeric_geometry_v1/`; it is not merged into `prototype_dataset_v1`.

## Current Smoke Result

Default deterministic smoke output:

```text
artifacts/smoke_baseline_v1/
```

Key result:

```text
Task A rows = 134
source-only AUROC = 0.5008
semantic_score * p_geom_valid AUROC = 0.5317
generic geometry proxy AUROC = 0.6298
relation-conditioned geometry proxy AUROC = 0.6681
mean paired compatibility drop = 0.1411
validation_errors = 0
overall = ready_for_learned_smoke
```

Caveat:

- `support_contact` carries most of the geometry-proxy signal.
- `relative_vertical` is not yet strong under the current cleaned `G_e` proxy.
- predicate prevalence was non-trivial, so the learned smoke included predicate/family
  shortcut controls before selecting the next step.

## Current Learned Smoke Result

Default learned smoke output:

```text
artifacts/learned_smoke_v1/
```

Key result:

```text
Task A compatibility rows = 134
M1 source-only Z AUROC = 0.4885
M3 p_geom_valid rule AUROC = 0.5507
M4 geometry-only G AUROC = 0.7634
M5 compatibility T+G AUROC = 0.9728
M6 factorized T+Z+G+Q AUROC = 0.9748
S1 predicate/family shortcut AUROC = 0.5978
Task B M6 observability AUROC = 1.0000
Task C M6 reliability AUROC = 0.9648
two-head accept/reject/abstain macro-F1 = 0.5062
validation_errors = 0
overall = learned_smoke_promising_but_needs_family_shortcut_review
```

Interpretation:

- `C_e = compatibility(T_e, G_e)` has strong train-internal grouped-fold signal against
  source-only and predicate/family shortcut probes.
- `T_e + Z_e` is also very strong, so this is still hypothesis evidence, not paper evidence.
- The next useful step is to materialize harder numeric geometry evidence for
  `attachment_deferred`; simply increasing the posterior combiner is not the bottleneck.

## Current Attachment Numeric Geometry Result

Default attachment numeric geometry output:

```text
artifacts/attachment_numeric_geometry_v1/
```

Key result:

```text
rows = 240
numeric_g_rows = 240
attached to / hanging on / connected to = 82 / 96 / 62
compatibility positive / negative / unknown = 33 / 81 / 126
counterfactual_groups = 33
connected_diagnostic_rows = 62
validation_errors = 0
artifact_next_at_creation = attachment_numeric_geometry_smoke_v1
```

Interpretation:

- `attached to` and `hanging on` now have numeric geometry evidence and binary
  geometry-support compatibility rows.
- `connected to` is materialized as numeric geometry diagnostic only because it lacks a balanced
  physical compatibility target.
- Construction shortcuts such as cell id, machine hint, geometry status, and witness scores are
  excluded from `G_e` and retained only under `hidden_control`.

## Current Attachment Smoke Result

Default attachment smoke output:

```text
artifacts/attachment_numeric_geometry_smoke_v1/
```

Key Task A result:

```text
Task A compatibility rows = 114
positive / negative = 33 / 81
source-only Z AUROC = 0.4635
semantic+source T+Z AUROC = 0.8148
geometry-only G AUROC = 0.8949
compatibility T+G AUROC = 0.9282
factorized T+Z+G+Q AUROC = 0.9364
predicate/family shortcut AUROC = 0.5305
hidden construction probe AUROC = 0.8767
validation_errors = 0
overall = attachment_smoke_promising_but_requires_hidden_shortcut_review
```

Interpretation:

- attachment numeric `G_e` has a real signal: geometry-only beats source-only and predicate/family
  shortcut probes.
- `T_e + G_e` improves over geometry-only on `attached to` and `hanging on`.
- hidden construction probes remain high, so the next step is a path decision rather than direct
  paper-claim promotion.

## Current Attachment Path Decision

Decision:

```text
do_not_promote_attachment_to_combined_main_yet
next = attachment_shortcut_controlled_smoke_v1
```

Rationale:

- `T_e + G_e` is strong enough to keep attachment as a promising extension.
- hidden construction probe is also high: AUROC `0.8767`.
- hidden cells are label-imbalanced, e.g. `H1_hanging_anchor_supported_candidate` has
  `21/5` positive/negative while `H2_hanging_no_anchor_or_floor_supported_candidate` has `1/26`.
- a strict within-cell balanced control can test whether the signal survives without construction
  cell shortcuts.

## Current Attachment Shortcut-Controlled Smoke Result

Default controlled smoke output:

```text
artifacts/attachment_shortcut_controlled_smoke_v1/
```

Key result:

```text
Task A controlled compatibility rows = 34
positive / negative = 17 / 17
pair groups = 17
hidden cells = 4
source-only Z AUROC = 0.5467
geometry-only G AUROC = 0.7232
compatibility T+G AUROC = 0.9550
factorized T+Z+G+Q AUROC = 0.9689
predicate/family shortcut AUROC = 0.5000
hidden construction probe AUROC = 0.5000
hidden witness score probe AUROC = 0.5000
validation_errors = 0
overall = attachment_controlled_smoke_passed_promote_to_larger_controlled_mining
```

Interpretation:

- the previous hidden construction shortcut does not survive strict within-cell balancing;
- `T_e + G_e` remains strong against source-only, geometry-only, predicate/family shortcut, and
  hidden probes;
- the slice is only `34` rows, so this is a go/no-go diagnostic for larger controlled mining, not
  paper evidence.

Follow-up completed:

```text
attachment_controlled_expansion_plan_v1
```

## Current Attachment Controlled Expansion Plan

Default plan output:

```text
artifacts/attachment_controlled_expansion_plan_v1/
```

Selected route:

```text
v20_endpoint_balanced_preview_400_repackage_with_numeric_geometry_join
```

Target contract:

```text
target_rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 40 near/overlap diagnostic + 40 far/ambiguous diagnostic
validation_errors = 0
```

Interpretation:

- `attachment_shortcut_controlled_smoke_v1` justified expansion beyond the `34`-row diagnostic;
- v20 full-train capacity already provides a feasible `400`-row endpoint-balanced preview;
- v21 strict same-predicate/rank/geometry/family route remains blocked by predicate imbalance;
- `connected to` remains diagnostic until visual/mesh evidence can support functional connection.

Follow-up completed:

```text
attachment_controlled_candidate_materialization_v1
```

## Current Attachment Controlled Candidate Materialization

Default materialization output:

```text
artifacts/attachment_controlled_candidates_v1/
```

Key result:

```text
rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
numeric_g_rows = 400
selected_prediction_matches = 400
pair_geometry_matches = 400
groups = 131
validation_errors = 0
```

Predicate and target counts:

```text
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 40 near/overlap diagnostic + 40 far/ambiguous diagnostic
```

Interpretation:

- all selected v20 preview rows were matched to source prediction rows;
- all selected directed pairs were joined with raw pair geometry;
- raw `G_e` source is `support_contact` for all 400 rows, which is acceptable because `G_e` is
  predicate-independent pair geometry rather than attachment-label evidence;
- hidden construction fields remain outside model input and are retained only for shortcut probes.

Next at completion:

```text
attachment_controlled_candidate_smoke_v1
```

## Current Attachment Controlled Candidate Smoke

Default smoke output:

```text
artifacts/attachment_controlled_candidate_smoke_v1/
```

Key Task A result:

```text
Task A primary compatibility rows = 320
positive / negative = 160 / 160
source-only Z AUROC = 0.4585
semantic+source T+Z AUROC = 0.4798
geometry-only G AUROC = 1.0000
compatibility T+G AUROC = 1.0000
factorized T+Z+G+Q AUROC = 1.0000
predicate/family shortcut AUROC = 0.4876
source-rank shortcut AUROC = 0.4908
endpoint-label-pair shortcut AUROC = 0.5074
hidden cell/construction probe AUROC = 1.0000
validation_errors = 0
overall = attachment_controlled_candidate_smoke_promising_but_hidden_proxy_dominates
```

Interpretation:

- `G_e` explains the proxy compatibility target and beats source/rank/endpoint visible shortcuts;
- hidden construction probes also perfectly explain the label, so this is not independent
  reliability evidence yet;
- the result should be used for path decision, not direct paper promotion.

Next at completion:

```text
attachment_controlled_candidate_path_decision_v1
```

## Current Attachment Controlled Candidate Path Decision

Decision:

```text
attachment_400_proxy_status = compatibility_proxy_pretraining_only
attachment_feature_schema_status = keep
attachment_proxy_label_status = do_not_use_as_paper_reliability_target
attachment_paper_evidence_status = not_promoted
```

Reason:

- the 400-row proxy set is useful because `G_e` and `T+G` recover the proxy while source/rank/endpoint
  shortcuts stay near chance;
- hidden cell/construction probes are also perfect, so the proxy labels are not independent
  reliability labels;
- stronger combiners are not the next bottleneck; the next bottleneck is independent audit labels.

Next:

```text
attachment_independent_audit_subset_plan_v1
```

## Current Attachment Independent Audit Subset Plan

Default output:

```text
artifacts/attachment_independent_audit_subset_plan_v1/
```

Result:

```text
selected_route = reuse_v20_packet_assets_with_blank_h002_independent_review_template
selected_rows = 200
primary_rows = 160
connected_diagnostic_rows = 40
attached to = 80
hanging on = 80
connected to = 40 diagnostic
T1_strong_pair_visual = 72
T2_individual_visual_plus_mesh = 128
validation_errors = 0
```

Boundary:

- prior v20 labels are hidden provenance only;
- current proxy labels are not promoted;
- visible review label fields are blank;
- multi-view/mesh packet evidence is audit evidence, not model input.

Next:

```text
attachment_independent_audit_label_fill_v1
```

## Current Attachment Independent Audit Label Fill

Default output:

```text
artifacts/attachment_independent_audit_label_fill_v1/
```

Result:

```text
label_source = codex_visible_packet_label_v1
rows = 200
accept_reliable = 17
reject_unreliable = 91
abstain_uncertain = 92
primary_binary_preview = 17 accept / 91 reject
validation_errors = 0
```

Predicate-level distribution:

```text
attached to = 2 accept / 53 reject / 25 abstain
hanging on = 15 accept / 38 reject / 27 abstain
connected to = 40 abstain diagnostic
```

Boundary:

- hidden manifest not used for label decisions;
- prior v20 labels not used;
- source score/rank not used;
- proxy construction label not used;
- positive sparsity is preserved rather than tuned away.

Next:

```text
attachment_independent_audit_label_ingestion_v1
```

## Current Attachment Independent Audit Label Ingestion

Default output:

```text
artifacts/attachment_independent_audit_label_ingestion_v1/
```

Result:

```text
status = h002_attachment_independent_audit_label_ingested_positive_sparse_with_shortcut_risk
rows = 200
primary_binary_rows = 108
primary_binary_target = 17 positive / 91 negative
p_obs_target = 108 observable / 92 abstain-or-unobservable
geometry_support = 17 supported / 63 unsupported / 120 uncertain
validation_errors = 0
```

Shortcut / viability:

```text
minimum_positive_for_posterior_smoke = 30
primary_positive_rows = 17
class_mass_pass = false
model_shortcut_probe_risk_flags = 60
construction_proxy_probe_risk_flags = 19
label_derived_probe_risk_flags = 21
posterior_smoke_allowed = false
```

Interpretation:

- the post-lock join and factor-view materialization succeeded;
- `p_obs` can be studied on all 200 rows, but `p_rel`/`C_e` binary is positive-sparse;
- source/proxy construction fields are still diagnostic-only, but shortcut probes must be audited;
- learned posterior smoke remains blocked until target-independence is checked.

Next:

```text
attachment_independent_target_independence_audit_v1
```

## Current Attachment Independent Target Independence Audit

Default output:

```text
artifacts/attachment_independent_target_independence_audit_v1/
```

Result:

```text
status = h002_attachment_independent_target_independence_audit_blocked_primary_positive_sparse
rows = 200
p_rel_primary_binary = 91 negative / 17 positive
c_e_compatibility_binary = 91 negative / 17 positive
p_obs_primary_binary = 108 observable / 52 abstain-or-unobservable
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
validation_errors = 0
```

Risk flags:

```text
full_risk_flags = 97
construction_proxy_or_source_hidden = 26
visible_semantic_or_packet = 29
instance_or_scan_id = 21
label_derived_auxiliary = 21
```

Interpretation:

- `p_rel/C_e` is blocked by positive sparsity: only 17 accept-positive rows;
- no strict or diagnostic clear controlled slice exists for the primary target;
- `p_obs` has enough class mass, but is still entangled with visible/evidence and construction
  fields;
- next step is target repair, not posterior smoke.

Next:

```text
attachment_independent_target_repair_plan_v1
```

## Current Attachment Independent Target Repair Plan

Default output:

```text
artifacts/attachment_independent_target_repair_plan_v1/
```

Result:

```text
status = h002_attachment_independent_target_repair_plan_v1_ready
selected_route = new_positive_anchor_mining_with_packet_materialization
current_200 positive / negative = 17 / 91
all_v20_matched_298 positive / negative = 24 / 116
full_candidate_400 visible-rule positive / negative = 45 / 174
full_candidate_400 mixed_visible_pair_groups = 1
full_candidate_400 mixed_predicate_visible_pair_groups = 0
validation_errors = 0
```

Decision:

- do not train posterior from the current attachment target;
- do not relax `uncertain` into `accept`;
- do not treat all 400 proxy candidates as paper evidence;
- mine new high-precision accept-positive anchors and matched hard negatives.

Next:

```text
attachment_independent_positive_anchor_mining_plan_v1
```

## Current Attachment Positive Anchor Mining Plan

Default output:

```text
artifacts/attachment_independent_positive_anchor_mining_plan_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_mining_plan_v1_ready
selected_route = train_only_positive_anchor_candidate_mining_then_packet_materialization
target_rows_before_audit = 560
primary_requested_rows_before_audit = 480
post_audit_min_accept_positive = 60
post_audit_min_reject_negative = 60
validation_errors = 0
```

Query plan:

```text
hanging on positive anchors = 120 requested, audit accept gate >= 40
hanging on hard negatives = 120 requested, audit reject gate >= 60
attached to structural positive anchors = 120 requested, audit accept gate >= 30
attached to hard negatives = 120 requested, audit reject gate >= 60
connected to diagnostic = 80 requested, primary gate disabled
```

Interpretation:

- the next step should mine new candidates rather than train a posterior;
- `hanging on` is the strongest primary anchor route;
- `attached to` is primary only if the independent audit yields enough accepted positives;
- `connected to` remains diagnostic until functional connection evidence is available;
- source score/rank, proxy role, cell id, prior labels, and GT-match status remain hidden from
  label fill and forbidden for `C_e`.

Next:

```text
attachment_independent_positive_anchor_candidate_mining_v1
```

## Current Attachment Positive Anchor Candidate Mining

Default output:

```text
artifacts/attachment_independent_positive_anchor_candidate_mining_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata
selected_rows = 560
primary_binary_selected = 467
primary_uncertain_buffer_selected = 13
diagnostic_selected = 80
complete_positive_negative_contrast_pairs = 143
validation_errors = 0
```

Query counts:

```text
Q1_hanging_on_positive_anchor = 116
Q2_hanging_on_hard_negative = 120
Q3_attached_to_structural_positive_anchor = 118
Q4_attached_to_hard_negative = 113
Q5_connected_near_or_overlap_diagnostic = 40
Q5_connected_far_or_functional_ambiguous_diagnostic = 40
Q6_primary_uncertain_buffer = 13
```

Mixed-strata summary:

```text
endpoint_family_rank_coverage mixed groups = 55, balanced rows = 214
endpoint_family_rank mixed groups = 61, balanced rows = 280
visible_pair mixed groups = 58, balanced rows = 312
rank_band mixed groups = 7, balanced rows = 452
same_scene mixed groups = 40, balanced rows = 86
same_scene_endpoint_family_rank mixed groups = 11, balanced rows = 28
```

Interpretation:

- candidate mining did not simply add positive rows;
- source score/rank are not used as selection scores and remain hidden from label fill;
- positive anchors are paired with hard negatives in mixed strata when possible;
- `13` primary uncertain rows are buffer rows because the de-duplicated v18/v20 seed pool has
  `467` unique attached/hanging binary rows, not the requested `480`;
- selected rows are ready for packet materialization, not posterior smoke.

Next:

```text
attachment_independent_positive_anchor_packet_materialization_v1
```

## Current Attachment Positive Anchor Packet Materialization

Default output:

```text
artifacts/attachment_independent_positive_anchor_packet_materialization_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill
packet_rows = 560
packet_status_counts = ready: 560
label_ready_rows = 560
non_ready_rows = 0
visible_leakage_hits = 0
validation_errors = 0
```

Coverage:

```text
subject_image_rows = 560 / 560
object_image_rows = 560 / 560
contact_sheet_rows = 560 / 560
mesh_packet_rows = 560 / 560
total_subject_images = 2174
total_object_images = 2204
```

Interpretation:

- all selected mixed-strata candidates now have reviewer-facing visual/mesh packets;
- source score/rank, construction proxy, cell id, GT-match, scan id, and object ids remain hidden
  from label-facing surfaces;
- multi-view/mesh is audit evidence only, not model input;
- the batch is ready for independent label fill, not posterior smoke.

Next:

```text
attachment_independent_positive_anchor_label_fill_v1
```

## Current Attachment Positive Anchor Label Fill

Default output:

```text
artifacts/attachment_independent_positive_anchor_label_fill_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_label_fill_v1_completed
rows = 560
accept_reliable = 60
reject_unreliable = 246
abstain_uncertain = 254
primary_binary_preview_rows = 306
primary_positive_rows = 60
primary_negative_rows = 246
connected_diagnostic_rows = 80
validation_errors = 0
```

Predicate-level distribution:

```text
attached to = 30 accept / 95 reject / 113 abstain
hanging on = 30 accept / 151 reject / 61 abstain
connected to = 80 abstain diagnostic
```

Interpretation:

- positive-anchor repair reached the minimum primary positive gate exactly: `60` accept rows;
- the target is much less positive-sparse than the previous `17/91` independent attachment target;
- labels are still proxy audit labels and are not posterior/paper evidence;
- the next step must join hidden/control provenance and audit shortcut/target independence.

Next:

```text
attachment_independent_positive_anchor_label_ingestion_v1
```

## Current Attachment Positive Anchor Label Ingestion

Default output:

```text
artifacts/attachment_independent_positive_anchor_label_ingestion_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk
rows = 560
primary_binary_rows = 306
primary_binary_target = 60 positive / 246 negative
p_obs_target = 306 observable / 254 abstain-or-unobservable
connected_diagnostic_rows = 80
validation_errors = 0
```

Viability:

```text
class_mass_pass = true
minimum_positive_for_posterior_smoke = 60
minimum_negative_for_posterior_smoke = 60
primary_positive_rows = 60
primary_negative_rows = 246
```

Shortcut diagnostics:

```text
quick_probe_risk_flags = 98
model_shortcut_probe_risk_flags = 75
construction_proxy_probe_risk_flags = 42
label_derived_probe_risk_flags = 23

same_query_mixed_primary_binary_groups = 5
same_proxy_role_mixed_primary_binary_groups = 3
same_cell_mixed_primary_binary_groups = 5
same_rank_band_mixed_primary_binary_groups = 5
same_predicate_mixed_primary_binary_groups = 2
same_visible_pair_mixed_primary_binary_groups = 2
```

Interpretation:

- the positive-anchor target has enough positive/negative mass for a diagnostic smoke in terms of
  row count;
- shortcut risk remains substantial, especially visible endpoint/semantic fields and hidden
  query/cell/construction axes;
- posterior smoke is still blocked until a formal target-independence audit identifies usable
  controlled slices.

Next:

```text
attachment_independent_positive_anchor_target_independence_audit_v1
```

## Current Attachment Positive Anchor Target Independence Audit

Default output:

```text
artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk
rows = 560
p_rel_primary_binary = 60 positive / 246 negative
c_e_compatibility_binary = 60 positive / 246 negative
p_obs_primary_binary = 306 observable / 174 unobservable-or-abstain
p_rel_class_mass_pass = true
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
full_risk_flags = 112
validation_errors = 0
```

Risk summary:

```text
construction_proxy_or_source_hidden = 36
instance_or_scan_id = 32
label_derived_auxiliary = 21
visible_semantic_or_packet = 20
official_gt_axis = 3
```

Interpretation:

- positive-anchor mining and label ingestion repaired the class-mass blocker;
- target independence is still not repaired because no strict or diagnostic controlled slice clears
  shortcut risk;
- posterior smoke remains blocked;
- the next step is a path decision, not a stronger posterior combiner.

Next:

```text
attachment_independent_positive_anchor_path_decision_after_audit_v1
```

## Current Attachment Positive Anchor Path Decision

Default output:

```text
artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1/
```

Result:

```text
status = h002_attachment_independent_positive_anchor_path_decision_diagnostic_freeze
selected_path = freeze_positive_anchor_target_as_diagnostic_and_move_to_compatibility_learning_plan
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_learning_scope_plan_v1
```

Input audit snapshot:

```text
rows = 560
p_rel_primary_binary = 306 rows, 60 positive / 246 negative
c_e_compatibility_binary = 306 rows, 60 positive / 246 negative
p_obs_primary_binary = 480 rows, 306 observable / 174 unobservable-or-abstain
p_rel_class_mass_pass = true
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
full_risk_flags = 112
same_visible_pair_rows = 8
same_predicate_visible_pair_rows = 0
construction_endpoint_strict_rows = 0
```

Decision:

- do not run posterior smoke on this target;
- do not mine more positive anchors with the same policy;
- do not relax abstain/accept labels to satisfy the posterior;
- keep attachment positive-anchor packets as diagnostic `Q_e`, hard-family, and failure-taxonomy
  evidence;
- move H002 back to method-level compatibility learning scope definition.

Next:

```text
compatibility_learning_scope_plan_v1
```

## Current Compatibility Learning Scope Plan

Default output:

```text
artifacts/compatibility_learning_scope_plan_v1/
```

Result:

```text
status = h002_compatibility_learning_scope_plan_ready
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_contract
```

Selected scope:

```text
primary_v1 = support_contact, relative_vertical
diagnostic_hard_family = attachment_like
future_generality = proximity
deferred = relative_horizontal, containment
```

Current prototype family counts:

```text
support_contact = 99 rows, 50 positive / 49 counterfactual_negative
relative_vertical = 35 rows, 17 positive / 18 counterfactual_negative
attachment_deferred = 560 rows, diagnostic-only after target freeze
```

Interpretation:

- `support_contact` is the strongest current primary compatibility family;
- `relative_vertical` remains primary but needs v2 expansion and directional controls;
- `attachment_like` is not discarded, but is limited to `Q_e`, observability, failure taxonomy, and
  future verified-positive mining;
- `proximity` is a future generality branch;
- `relative_horizontal` and `containment` are deferred until reference-frame or containment
  geometry contracts exist.

Next:

```text
compatibility_dataset_v2_contract
```

## Current Compatibility Dataset V2 Contract

Default output:

```text
artifacts/compatibility_dataset_v2_contract/
```

Result:

```text
status = h002_compatibility_dataset_v2_contract_ready
dataset_name = h002_compatibility_dataset_v2
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_materialization_plan
```

Family contract:

```text
support_contact requested = 120 positive / 120 negative, minimum reportable = 60 / 60
relative_vertical requested = 80 positive / 80 negative, minimum reportable = 60 / 60
attachment_like = diagnostic-only, not primary p_rel/C_e
proximity = future generality
```

Blocking conditions:

- `C_e` uses `T_e + G_e` only;
- `Z_e` is forbidden in compatibility input;
- `G_e` cannot contain predicate, source score/rank, GT/audit labels, or construction keys;
- `no_gt_for_pair` is unknown, not negative;
- `relative_vertical` requires predicate flip or subject/object swap controls;
- H001 `p_geom_valid` is baseline/teacher/ablation only.

Next:

```text
compatibility_dataset_v2_materialization_plan
```

## Current Compatibility Dataset V2 Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v2_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v2_materialization_plan_ready
selected_route = v2_capacity_scan_before_materialization
direct_materialization_allowed = false
posterior_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_capacity_scan
```

Current class-mass check:

```text
prototype_v1 support_contact = 50/49, relative_vertical = 17/18
all-label-ready reliability support_contact = 50/121, relative_vertical = 20/40
v2 minimum reportable per primary family = 60/60
```

Decision:

- do not directly materialize v2 from prototype or all-label-ready rows;
- use raw-witness feature join v2 as a train-only feature-adapter seed;
- repackage rows into `T_e/Z_e/G_e/Q_e` before any compatibility learning;
- run a v2-specific full-train capacity scan first;
- keep `attachment_like` diagnostic-only for `Q_e`, observability, and failure taxonomy.

Next:

```text
compatibility_dataset_v2_capacity_scan
```

## Current Compatibility Dataset V2 Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v2_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization
decision = capacity_pass_but_direct_hl_lh_target_blocked_generate_counterfactuals_and_repackage_raw_witness
row_materialization_allowed_with_controls = true
direct_hl_lh_target_allowed = false
learned_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_candidate_materialization
```

Family capacity:

```text
support_contact positive / negative = 74364 / 896
relative_vertical positive / negative = 111032 / 592
```

Predicate balance caveat:

```text
support_contact positive = lying on 26882 / standing on 23713 / supported by 23769
support_contact negative = lying on 896 / standing on 0 / supported by 0
relative_vertical positive = higher than 55811 / lower than 55221
relative_vertical negative = higher than 1 / lower than 591
```

Interpretation:

- class mass is sufficient for both primary families;
- direct HL/LH target construction is still blocked because queue kind, geometry status, rank, and
  predicate direction can shortcut the label;
- v2 materialization is allowed only with generated counterfactual controls and raw-witness `G_e`
  repackaging;
- learned smoke remains blocked until the materialized candidate rows pass schema and hidden
  shortcut audits.

Next:

```text
compatibility_dataset_v2_candidate_materialization
```

## Current Compatibility Dataset V2 Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v2_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit
rows = 400
groups = 200
compatibility positive / negative = 200 / 200
raw_witness matched / requested = 400 / 400
learned_smoke_allowed = false
validation_errors = 0
next_todo = compatibility_dataset_v2_schema_shortcut_audit
```

Family/predicate balance:

```text
support_contact = 120 positive / 120 negative
  lying on = 40 / 40
  standing on = 40 / 40
  supported by = 40 / 40

relative_vertical = 80 positive / 80 negative
  higher than = 40 / 40
  lower than = 40 / 40
```

Generated counterfactuals:

```text
support_contact wrong_pair_geometry = 40
support_contact shuffled_geometry = 40
support_contact contact_gap_or_overlap_perturbation = 40
relative_vertical predicate_flip = 40
relative_vertical subject_object_swap = 40
```

Interpretation:

- direct HL/LH labels are not used as the primary target;
- each positive anchor is paired with one generated negative;
- raw numeric `G_e` was joined for all selected anchors;
- `C_e` remains restricted to `T_e + G_e`;
- learned smoke is still blocked until schema/hidden-shortcut audit passes.

Next:

```text
compatibility_dataset_v2_schema_shortcut_audit
```

## Current Compatibility Dataset V2 Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v2_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view
rows = 400
compatibility positive / negative = 200 / 200
schema_errors = 0
leakage_high_risk_probes = 7
full_factorized_view_allowed = false
sanitized_view_written = true
learned_smoke_allowed = false
next_todo = compatibility_dataset_v2_sanitized_view_smoke_plan
```

Shortcut probe result:

```text
predicate_label accuracy = 0.500
relation_family accuracy = 0.500
source_rank_band accuracy = 0.500
source_score_bin accuracy = 0.500

row_role accuracy = 1.000
counterfactual_type accuracy = 1.000
G_e.geometry_source accuracy = 1.000
Q_e.generated_counterfactual accuracy = 1.000
Q_e.evidence_conflict_flag accuracy = 1.000
geometry_status_baseline accuracy = 1.000
relation_source accuracy = 1.000
```

Interpretation:

- the v2 candidate set is balanced at semantic/source shortcut axes;
- raw construction metadata perfectly exposes generated negatives;
- raw `full_factorized`, `obs_head`, `baseline_view`, and `audit_view` must not be model inputs;
- the audit writes `sanitized_model_view.jsonl`, preserving `T_e`, `Z_e`, numeric `G_e`, and
  sanitized `Q_e` while removing construction fields.

Next:

```text
compatibility_dataset_v2_sanitized_view_smoke_plan
```

## Current Compatibility Dataset V2 Sanitized View Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v2_sanitized_view_smoke_plan_ready
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
smoke_ready_view_written = true
learned_smoke_executed = false
next_todo = compatibility_dataset_v2_sanitized_view_smoke_runner
```

Additional blocked shortcut:

```text
Z_e.source_score_inherited_for_counterfactual accuracy = 1.000
```

Interpretation:

- the previous `sanitized_model_view.jsonl` is still an intermediate artifact, not the final smoke
  input;
- the next runner must read
  `artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/smoke_ready_view.jsonl`;
- `smoke_ready_view.jsonl` keeps `T_e`, `Z_e_safe`, numeric `G_e`, and `Q_e_safe`;
- `source_score_inherited_for_counterfactual` is removed from `Z_e_safe`;
- next comparison is source-only, semantic-only, geometry-only, compatibility `T_e + G_e`,
  sanitized factorized, shortcut probes, shuffled-geometry control, and wrong-predicate control.

Next:

```text
compatibility_dataset_v2_sanitized_view_smoke_runner
```

## Current Compatibility Dataset V2 Sanitized View Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner/
```

Result:

```text
status = h002_compatibility_dataset_v2_sanitized_view_smoke_runner_diagnostic_only_failed_controls
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
learned_smoke_executed = true
next_todo = compatibility_dataset_v2_failure_analysis
```

Key AUROC:

```text
source-only Z_e_safe = 0.5000
semantic-only T_e = 0.4846
semantic + source = 0.4797
object-pair shortcut = 0.4885
geometry-only G_e = 0.6731
compatibility T_e + G_e = 0.6250
factorized sanitized = 0.6230
shuffled-G control = 0.6085
wrong-T same-G control = 0.6250
```

Interpretation:

- source/semantic/object-pair shortcuts are controlled;
- numeric geometry has real signal;
- current `T_e + G_e` compatibility does not beat geometry-only;
- wrong-predicate control does not degrade from `T_e + G_e`;
- therefore current v2 target is geometry-only-dominant and not yet evidence for
  predicate-conditioned compatibility learning.

Next:

```text
compatibility_dataset_v2_failure_analysis
```

## Current Compatibility Dataset V2 Failure Analysis

Default output:

```text
artifacts/compatibility_dataset_v2_failure_analysis/
```

Result:

```text
status = h002_compatibility_dataset_v2_failure_analysis_ready
rows = 400
compatibility positive / negative = 200 / 200
validation_errors = 0
primary_cause = target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility
next_todo = compatibility_dataset_v2_target_redesign_plan
```

Key diagnosis:

```text
geometry-only M4 AUROC = 0.6731
compatibility M5 AUROC = 0.6250
wrong-T same-G AUROC = 0.6250
mean |M5 - wrongT| = 0.0
```

Counterfactual-type finding:

```text
support_contact shuffled_geometry false positive rate = 0.800
support_contact wrong_pair_geometry false positive rate = 0.425
support_contact contact_gap_or_overlap_perturbation false positive rate = 0.025
relative_vertical predicate_flip false positive rate = 0.650
relative_vertical subject_object_swap false positive rate = 0.375
```

Interpretation:

- input sanitization worked: source/semantic shortcut probes are near chance;
- the current target is still solved by generic geometry shifts, especially support/contact
  distance and overlap features;
- wrong-predicate control is identical to `T_e + G_e`, so predicate semantics are not controlling
  geometry use;
- the next target must create same-geometry or near-identical-geometry multi-predicate contrasts.

Next:

```text
compatibility_dataset_v2_target_redesign_plan
```

## Current Compatibility Dataset V2 Target Redesign Plan

Default output:

```text
artifacts/compatibility_dataset_v2_target_redesign_plan/
```

Result:

```text
status = h002_compatibility_dataset_v2_target_redesign_plan_ready
selected_route = v3_same_geometry_multi_predicate_contract
validation_errors = 0
next_todo = compatibility_dataset_v3_contract
```

Decision:

- do not repair v2 by adding more generated negatives;
- do not switch to a stronger combiner before target redesign;
- keep v2 as diagnostic-only negative evidence;
- define v3 as a predicate-conditioned target where the same or near-identical `G_e` appears with
  multiple `T_e` alternatives.

Primary v3 route:

```text
relative_vertical: higher than / lower than same-geometry contrast
```

Support/contact policy:

```text
secondary until role/orientation/visual/mesh evidence probe passes
```

Required v3 gates:

```text
same_geometry_group_integrity
geometry_only_near_chance
predicate_conditioning_gain
wrong_predicate_degradation
source_semantic_shortcut_control
```

Next:

```text
compatibility_dataset_v3_contract
```

## Current Compatibility Dataset V3 Support/Contact Evidence Probe Runner

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke
selected_path = route_to_visual_mesh_or_role_orientation_evidence
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
```

Key counts:

```text
support_queue_rows = 161498
distinct_directed_pairs = 75763
distinct_visible_pairs = 4109
exact multi-predicate mixed-geometry groups = 75
non-hard-surface exact candidate groups = 4
```

Decision:

- current numeric support/contact artifacts are not enough for clean `C_e` smoke;
- distance, overlap, and vertical-gap proxies are available but insufficient as primary evidence;
- role/orientation, contact direction, surface normal, mesh, visual, and multi-view evidence are
  missing from the current numeric view;
- hidden construction/provenance probes remain high-risk and must stay blocked;
- support/contact should proceed through a visual/mesh or role/orientation evidence plan, not a
  numeric-only learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
```

## Current Compatibility Dataset V3 Support/Contact Visual-Mesh Evidence Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_ready
selected_route = mesh_pose_contact_first_multiview_audit_first
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
```

Source snapshot:

```text
3RScan scan dirs = 1335
mesh refined obj = 1335
aligned instance ply = 1335
sequence.zip = 1335
visual contact sheets = 192
visual support/contact sheets = 64
attachment packet template dirs = 560
```

Plan decision:

- numeric-only support/contact smoke remains blocked;
- mesh/pose/contact evidence is the primary next `G_e` candidate;
- multi-view is audit / `Q_e` first, not immediate model input;
- attachment packet assets can be reused as renderer/template references, not as support/contact
  labels;
- next step is source inventory and candidate-row join feasibility, not learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
```

## Current Compatibility Dataset V3 Support/Contact Visual-Mesh Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe
selected_path = mesh_pose_contact_feature_probe_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan
```

Join coverage:

```text
support_rows = 161498
distinct_scans = 1157
distinct_directed_pairs = 75763
scan_asset_complete_rate = 1.000000
semseg_both_objects_present_rate = 1.000000
mesh_contact_surface_possible_rate = 1.000000
sequence_multiview_possible_rate = 1.000000
```

Decision:

- source join is strong enough for a mesh/pose/contact feature feasibility probe;
- candidate materialization and learned smoke remain blocked;
- high risks for later materialization/smoke are hard-surface dominance, HL/LH imbalance, and
  same exact-pair clean capacity;
- multi-view remains audit / `Q_e` first, not immediate model input.

Next:

```text
compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan
```

## Current Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_ready
selected_route = semseg_obb_normal_full_probe_ply_contact_sample_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
```

Probe design:

- Tier A: derive semseg OBB and dominant-normal features for all `161,498` support/contact rows;
- Tier B: derive aligned PLY / mesh-contact features on a `1,200` row stratified probe sample;
- Tier C: keep sequence/multi-view as small audit / `Q_e` sample only.

Decision:

- feature probe is allowed;
- candidate materialization and learned smoke remain blocked;
- model-safe feature output must exclude source score, rank, queue kind, geometry status, labels,
  and construction proxies;
- the runner must report derivability, finite-value sanity, hard-surface sensitivity, queue
  sensitivity, and old numeric proxy dominance.

Next:

```text
compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
```

## Current Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Runner

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review
selected_path = review_mesh_pose_contact_features_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_feature_probe_result_review
```

Counts:

```text
support_rows = 161498
tier_a_records = 161498
tier_b_records = 1200
tier_b_distinct_scans = 654
tier_b_hard_surface_rows = 408
tier_b_non_hard_surface_rows = 792
```

Gate result:

```text
tier_a_derivability_pass = true
tier_a_finite_pass = true
tier_b_sample_pass = true
model_safe_blocked_fields_absent = true
new_features_not_old_proxy_pass = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
paper_evidence_allowed = false
```

Decision:

- semseg OBB / dominant-normal features are derivable for all support/contact rows;
- aligned PLY contact-proxy features are derivable for the stratified 1,200-row probe sample;
- the model-safe preview excludes source score, rank, queue kind, geometry status, labels, and
  construction proxies;
- the new features are not flagged as direct copies of old numeric proxy fields;
- hard-surface dominance and HL/LH queue imbalance remain high-risk audit issues.

Next:

```text
compatibility_dataset_v3_support_contact_feature_probe_result_review
```

## Current Compatibility Dataset V3 Support/Contact Feature Probe Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan
selected_path = select_pose_conditioned_same_geometry_support_contact_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```

Review result:

```text
all_reviewed_features_derivable = true
old_numeric_proxy_dominance_high_count = 0
pose_conditioned_predicate_contrast_exists = 2
standing_supported_as_primary_negative_pair = fail
hard_surface_shortcut_control_needed = block_direct_materialization
queue_kind_target_independence = block_direct_materialization
same_exact_pair_clean_capacity = block_exact_pair_route
```

Predicate-pair interpretation:

```text
lying on vs standing on = pose_conditioned_contrast_candidate
lying on vs supported by = pose_conditioned_contrast_candidate
standing on vs supported by = collapse_or_superordinate_overlap
```

Decision:

- support/contact feature availability is now strong enough for a target-design plan;
- direct materialization is still blocked;
- learned smoke is still blocked;
- the next target should use same-geometry predicate flips, mainly `lying on` vs `standing on`;
- `supported by` should be diagnostic/superordinate, not a clean negative for `standing on`.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan
selected_path = capacity_scan_pose_conditioned_same_geometry_lying_standing_target
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```

Target contract:

```text
primary_contrast = lying on vs standing on
diagnostic_contrast = lying on vs supported by
excluded_primary_contrast = standing on vs supported by
rows_per_anchor = 2
same_G_e_required = true
```

Label policy:

```text
lying-like support/contact pose:
  lying on = positive
  standing on = negative

upright support/contact pose:
  standing on = positive
  lying on = negative
```

Quota gate for the next capacity scan:

```text
target_anchor_groups = 200
minimum_anchor_groups = 120
minimum_lying_like_anchors = 60
minimum_upright_anchors = 60
minimum_non_hard_surface_share = 0.30
max_single_visible_pair_share = 0.12
max_single_scan_share = 0.10
```

Decision:

- capacity scan is allowed;
- candidate materialization remains blocked;
- learned smoke remains blocked;
- `supported by` remains diagnostic/superordinate rather than primary negative;
- `queue_kind`, source score/rank, geometry status, visible pair, and anchor pose state remain
  audit/control only.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_pose_conditioned_support_contact
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan
```

Capacity:

```text
support_queue_rows = 161498
unique_directed_anchors = 75763
classified_anchors_for_selected_threshold = 4031
selected_anchor_groups = 200
selected_total_rows_if_materialized = 400
selected_state_counts = 100 lying-like / 100 upright
selected_non_hard_surface_share = 1.0
selected_max_single_visible_pair_share = 0.035
selected_max_single_scan_share = 0.03
```

Decision:

- capacity scan passed the frozen gate;
- candidate materialization plan is allowed;
- actual candidate materialization remains blocked;
- learned smoke remains blocked;
- queue kind remains audit-only and must not enter model input.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_ready
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```

Materialization contract:

```text
frozen_anchor_source = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/anchor_candidate_preview.jsonl
anchor_groups = 200
rows_per_anchor = 2
planned_rows = 400
positive_rows = 200
negative_rows = 200
lying_on_rows = 200
standing_on_rows = 200
```

Decision:

- candidate materialization is allowed;
- learned smoke remains blocked;
- paper evidence remains blocked;
- materializer must reuse the frozen 200 anchors exactly;
- next post-materialization gate must be schema/shortcut audit.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```

Materialized counts:

```text
anchor_groups = 200
candidate_rows = 400
positive_rows = 200
negative_rows = 200
lying_on_rows = 200
standing_on_rows = 200
lying_like_anchors = 100
upright_anchors = 100
semseg_complete_rows = 400
point_complete_rows = 240
hard_surface_rows = 0
```

Decision:

- candidate materialization is complete;
- schema/shortcut audit is allowed;
- learned smoke remains blocked;
- paper evidence remains blocked;
- optional aligned PLY point/contact evidence is represented through `Q_e`, not treated as a
  required field.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```

Shortcut audit:

```text
candidate_rows = 400
smoke_ready_rows = 400
groups = 200
allowed_feature_high_or_medium_risk = 0
blocked_feature_path_hits = 0
blocked_field_leakage_hits = 0
blocked_raw_high_risk_probes = 4
group_integrity_errors = 0
```

Decision:

- schema and single-field shortcut audit passed;
- all allowed single semantic, geometry, and `Q_e` probes are low risk;
- high-risk probes appear only in blocked raw fields such as row id, target label, hidden
  pose-state/predicate, and hidden `G_e` hash/predicate;
- sanitized-view smoke plan is allowed;
- learned smoke remains blocked until the smoke plan is written.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Sanitized View Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner
```

Plan counts:

```text
rows = 400
positive_rows = 200
negative_rows = 200
paired_groups = 200
semseg_complete_rows = 400
point_complete_rows = 240
```

Primary planned model:

```text
M5b_compatibility_TG_pose_interaction
```

Decision:

- learned-smoke runner implementation is allowed;
- runner must read only the audited `smoke_ready_view.jsonl`;
- `G_e_mesh_pose_contact` replaces the older relative-vertical `G_e_numeric` block;
- learned smoke has not been run yet;
- paper evidence remains blocked.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Sanitized View Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner_passed_controls
validation_errors = 0
overall = support_contact_pose_conditioned_smoke_passed_controls
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```

Key metrics:

```text
M1_source_only_Z_safe AUROC = 0.500
M2_semantic_only_T AUROC = 0.382
M4_geometry_only_G AUROC = 0.500
M5a_compatibility_TG_concat AUROC = 0.382
M5b_compatibility_TG_pose_interaction AUROC = 1.000
M6_factorized_sanitized_TZGQ_pose_interaction AUROC = 1.000
C1_wrong_T_same_G_control AUROC = 0.000
C2_shuffled_G_global_control AUROC = 0.525
C3_shuffled_G_within_predicate_control AUROC = 0.568
paired_mean_positive_minus_negative = 0.915326
```

Decision:

- all predefined smoke gates passed;
- this is a strong train-only `C_e` mechanism proof for support/contact pose-conditioned
  compatibility;
- it is not yet paper evidence;
- result review is required before claiming broad relation reliability.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```

## Current Compatibility Dataset V3 Support/Contact Pose-Conditioned Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis
selected_path = accept_support_contact_Ce_mechanism_proof_select_multi_family_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_result_synthesis_plan
```

Decision:

- the support/contact pose-conditioned smoke is accepted as a scoped `C_e` mechanism proof;
- the allowed claim is predicate-geometry compatibility for `lying on` / `standing on`
  support/contact relations;
- broad relation reliability, final `p_rel` / `p_obs`, human-audited reliability, all-family
  generality, and paper-level Docker evidence remain blocked;
- `relative_vertical` and `support_contact_pose_conditioned` should now be synthesized before
  adding attachment, proximity, or horizontal relations.

Main caveats:

```text
constructed_target = high
too_clean_auc = medium
calibration_not_established = medium
paper_evidence_not_yet = high
```

Next:

```text
compatibility_dataset_v3_multi_family_result_synthesis_plan
```

## Current Compatibility Dataset V3 Multi-Family Result Synthesis Plan

Default output:

```text
artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_ready
selected_path = freeze_two_family_Ce_claim_select_independent_validity_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_target_plan
```

Allowed current claim:

```text
Across relative-vertical and support/contact pose-conditioned relation families,
predicate-independent geometry evidence G_e is not sufficient by itself. Relation
compatibility requires an explicit semantic-geometry compatibility factor C_e that
conditions geometry interpretation on semantic content T_e.
```

Decision:

- `relative_vertical` and `support_contact_pose_conditioned` are now the two core scoped `C_e`
  mechanism results;
- adding attachment/proximity immediately is deferred because it does not resolve the constructed
  target caveat;
- broad relation reliability, final `p_rel` / `p_obs`, and paper-level Docker evidence remain
  blocked;
- the next step is an independent train-side validity target plan.

Next:

```text
compatibility_dataset_v3_independent_validity_target_plan
```

## Current Compatibility Dataset V3 Independent Validity Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_target_plan_ready
selected_path = select_gt_anchored_train_validity_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_source_inventory
```

Decision:

- select `GT_anchored_train_validity_target` as the next independent target route;
- use official train GT as the primary label source;
- keep `relative_vertical` and `support_contact_pose_conditioned` as primary families;
- reject `no-GT = negative`;
- reject existing validation/no-GT manual labels as train-side target evidence;
- defer cross-source and human-audit targets until the GT/source/geometry inventory shows what is
  missing.

Train GT capacity snapshot:

```text
relative_vertical = 3662
  higher than = 1831
  lower than = 1831

support_contact_pose_conditioned = 12016
  standing on = 9992
  lying on = 2024
```

Next:

```text
compatibility_dataset_v3_independent_validity_source_inventory
```

## Current Compatibility Dataset V3 Independent Validity Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan
selected_path = materialize_gt_anchored_independent_validity_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_materialization_plan
```

Inventory:

```text
total_match_rows_scanned = 4818996
selected_primary_rows = 741384
families_ready = relative_vertical, support_contact_pose_conditioned
```

Family capacity:

```text
relative_vertical:
  rows = 370692
  source_z_join_rate = 1.0
  geometry_g_join_rate = 1.0
  positive_exact_gt_satisfied = 1140
  strong_negative_gt_pair_other_predicate_unsatisfied = 19350
  no_gt_satisfied_abstain = 105242

support_contact_pose_conditioned:
  rows = 370692
  source_z_join_rate = 1.0
  geometry_g_join_rate = 1.0
  positive_exact_gt_satisfied = 7564
  strong_negative_gt_pair_other_predicate_unsatisfied = 1067
  no_gt_satisfied_abstain = 83463
```

Decision:

- independent validity materialization planning is feasible for both primary families;
- no-GT rows remain abstain/audit candidates, not negative labels;
- learned smoke and `p_rel` / `p_obs` promotion remain blocked until materialized rows pass
  schema/shortcut audit.

Next:

```text
compatibility_dataset_v3_independent_validity_materialization_plan
```

## Current Compatibility Dataset V3 Independent Validity Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_materialization_plan_ready
selected_path = materialize_balanced_gt_anchored_independent_validity_candidates
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_candidate_materialization
```

Planned counts:

```text
planned_total_rows = 4027
planned_primary_binary_rows = 3200
planned_nonbinary_audit_or_abstain_rows = 827
```

Primary binary plan:

```text
relative_vertical:
  positive = 800
  negative = 800

support_contact_pose_conditioned:
  positive = 800
  negative = 800
```

Nonbinary plan:

```text
no-GT + geometry satisfied abstain/audit = 400
geometry uncertain abstain = 400
exact-GT + geometry unsatisfied audit_required = 27
```

Decision:

- candidate materialization is allowed for the frozen plan;
- no-GT rows are still never negative labels;
- learned smoke remains blocked until materialized rows pass schema/shortcut audit.

Next:

```text
compatibility_dataset_v3_independent_validity_candidate_materialization
```

## Current Compatibility Dataset V3 Independent Validity Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```

Materialized counts:

```text
materialized_total_rows = 4027
materialized_primary_binary_rows = 3200
materialized_nonbinary_rows = 827
primary_positive_rows = 1600
primary_negative_rows = 1600

relative_vertical = 2012
support_contact_pose_conditioned = 2015
```

Selection note:

```text
strict_scan_and_visible_pair_caps: selected 3491 rows
relax_visible_pair_cap_for_deficits: selected 536 rows
cap_relaxation_used = true
```

Decision:

- frozen quotas were fully materialized;
- no-GT rows were kept as abstain/audit, not negative;
- `candidate_rows.jsonl` keeps hidden construction fields for audit while
  `smoke_ready_view.jsonl` removes them;
- visible-pair cap relaxation makes schema/shortcut audit mandatory before learned smoke.

Next:

```text
compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Independent Validity Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```

Counts:

```text
candidate_rows = 4027
primary_binary_rows = 3200
sanitized_primary_rows = 3200
primary_positive_rows = 1600
primary_negative_rows = 1600
```

Audit result:

```text
sanitized_blocked_feature_path_hits = 0
sanitized_blocked_field_leakage_hits = 0
allowed_feature_high_or_medium_risk = 2
blocked_construction_high_risk = 4
```

Blocking probes:

```text
predicate_x_class_pair = 0.976562
subject_object_class_pair = 0.840000
```

Interpretation:

- schema cleanup works: the stricter `sanitized_primary_view.jsonl` removes construction-derived
  `geometry_status`, `p_geom_valid`, `consistency_score`, and `geometry_residual_proxy`;
- target independence still fails because allowed semantic object-pair strata predict the primary
  label too well;
- learned smoke remains blocked.

Next:

```text
compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Independent Validity Path Decision After Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_path_decision_select_stratum_repair_capacity_scan
selected_path = freeze_current_target_diagnostic_select_full_train_stratum_repair_capacity_scan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```

Decision:

- current independent-validity target is frozen as diagnostic evidence;
- learned smoke remains blocked;
- current artifact repair is rejected because exact `predicate_x_class_pair` balance has only
  `150` rows;
- full-train stratum-repair capacity scan is selected next.

Current-artifact repair capacity:

```text
family balanced capacity = 3200
predicate_label balanced capacity = 2374
subject_object_class_pair balanced capacity = 1024
predicate_x_class_pair balanced capacity = 150
predicate_x_class_pair_x_rank_band balanced capacity = 146
```

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_ready_for_materialization_plan
selected_path = materialize_exact_predicate_class_stratum_repaired_independent_validity_target
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```

Full-train counts:

```text
total_match_rows = 4818996
selected_family_rows = 741384
primary_rows = 29121
primary_positive = 8704
primary_negative = 20417
```

Repair capacity:

```text
predicate_x_class_pair mixed_groups = 39
predicate_x_class_pair raw balanced capacity = 2384
predicate_x_class_pair scan-capped capacity = 2252
repair_ready = true
```

Decision:

- full train has enough exact semantic-stratum capacity to attempt repair;
- current independent-validity target remains diagnostic, but the independent-validity route is not
  abandoned;
- next step is a materialization plan that balances labels within each exact `predicate_x_class_pair`
  stratum.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready
selected_path = materialize_exact_predicate_class_balanced_independent_validity_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```

Planned repaired target:

```text
planned_primary_rows = 1600
planned_positive_rows = 800
planned_negative_rows = 800
retained_exact_strata = 35
max_pairs_per_stratum = 125
```

Family scope:

```text
relative_vertical = 1512 rows
support_contact_pose_conditioned = 88 rows
```

Decision:

- materialize a train-only exact `predicate_label + subject_class_label + object_class_label`
  balanced target next;
- keep `geometry_status`, `p_geom_valid`, `consistency_score`, residual summaries, target pools,
  and hidden GT provenance out of the model-safe view;
- treat support/contact as a diagnostic slice in this repaired independent-validity target because
  exact-stratum capacity is only `88` rows after scan caps.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```

Materialized counts:

```text
materialized_primary_rows = 1600
positive_rows = 800
negative_rows = 800
retained_exact_strata = 35
scan_cap_relaxation_rows = 0
```

Family scope:

```text
relative_vertical = 1512 rows
support_contact_pose_conditioned = 88 rows
```

Schema precheck:

```text
model_safe_view_forbidden_key_hits = 0
feature_block_forbidden_key_hits = 0
stratum_internal_balance_failures = 0
```

Decision:

- exact predicate/object-class balanced train rows were materialized successfully;
- `model_safe_view.jsonl` excludes `geometry_status`, `p_geom_valid`, `consistency_score`, residual
  fields, target pools, hidden GT provenance, and selection metadata;
- learned smoke remains blocked until the repaired target passes schema/shortcut audit.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```

Counts:

```text
model_safe_rows = 1600
label_counts = 800 / 800
retained_exact_strata = 35
```

Shortcut result:

```text
critical_high_or_medium = 0
source_confidence_high_or_medium = 0
raw_geometry_high_or_medium = 0
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
```

Key probes:

```text
predicate_x_class_pair = 0.500000
subject_object_class_pair = 0.500000
predicate_label = 0.500000
rank_band = 0.553750
semantic_rank = 0.549375
semantic_score_norm = 0.525625
```

Decision:

- exact predicate/object-class balancing fixed the previous `predicate_x_class_pair` shortcut
  blocker;
- construction fields remain predictive in hidden audit fields but do not leak into model-safe
  feature blocks;
- learned smoke is now allowed as a next planned stage, but not yet executed.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Sanitized View Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_ready
rows = 1600
positive / negative = 800 / 800
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```

Planned views:

```text
M1 = semantic_only_T
M2 = source_only_Z
M3 = semantic_source_TZ
M4 = geometry_only_G
M5 = T_G_concat
M6 = T_G_compatibility_interaction
M7 = factorized_TZGQ
```

Controls:

```text
shuffled_G_global
shuffled_G_within_predicate
wrong_predicate_family
no_interaction_concat
```

Key gates:

- semantic/source shortcut AUROC should stay `<= 0.60`;
- primary `M6` or `M7` should reach `>= 0.65` AUROC;
- primary view should beat max semantic/source baseline by `>= 0.05` AUROC;
- if geometry-only `M4` is within `0.02` AUROC of the factorized view, the result is a
  geometry-dominance diagnostic rather than factorized compatibility evidence;
- support/contact remains diagnostic because it has only `88` rows.

Next at plan completion:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Sanitized View Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_passed_controls
rows = 1600
positive / negative = 800 / 800
groups = 1097
mixed_label_groups = 491
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```

Key metrics:

```text
M1_semantic_only_T = 0.416131 AUROC
M2_source_only_Z = 0.568110 AUROC
M3_semantic_source_TZ = 0.533226 AUROC
M4_geometry_only_G = 0.527064 AUROC
M5_TG_concat = 0.480008 AUROC
M6_TG_compatibility_interaction = 0.995633 AUROC
M7_factorized_TZGQ = 0.995280 AUROC
C1_shuffled_G_global = 0.514618 AUROC
C2_shuffled_G_within_predicate = 0.458553 AUROC
C3_wrong_predicate_family_control = 0.026644 AUROC
```

Interpretation:

- The repaired target no longer collapses to semantic/source shortcut probes.
- It also does not collapse to geometry-only: `M6 - M4 = 0.468569` AUROC.
- The signal appears specifically in predicate-conditioned compatibility interaction.
- Probability calibration is not claimed here; this runner's old `ECE-10` helper was later
  downgraded by the calibration scope plan.
- Support/contact remains diagnostic in this artifact because it has only `88` rows.

Next at runner completion:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```

## Current Compatibility Dataset V3 Independent Validity Stratum Repair Smoke Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan
selected_path = accept_independent_validity_Ce_smoke_select_calibration_and_scope_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_calibration_scope_plan
```

Decision:

- accept the repaired independent-validity smoke as the strongest current H002 `C_e` mechanism evidence;
- keep calibrated posterior reliability blocked because primary `ECE-10 = 0.480112`;
- keep paper-level and held-out claims blocked because this is train-only hypothesis evidence;
- keep support/contact primary generality blocked because this artifact has only `88` support/contact rows;
- select calibration/scope planning before adding a larger combiner or creating a paper experiment root.

Next:

```text
compatibility_dataset_v3_independent_validity_calibration_scope_plan
```

## Current Compatibility Dataset V3 Independent Validity Calibration Scope Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing
selected_path = calibration_metric_audit_passed_select_support_contact_family_balancing
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

Decision:

- downgrade the old runner `ECE-10` as a helper-definition artifact, not a valid binary
  probability-calibration gate by itself;
- use corrected probability-ECE / Brier in future H002 smoke runners;
- keep calibrated `p_rel` / `p_obs`, paper-level, held-out, and all-family claims blocked;
- select support/contact independent-validity balancing as the next route because the current
  evidence is `relative_vertical` dominant (`1512 / 1600`) and support/contact has only `88` rows.

Key calibration audit:

```text
M6 legacy runner ECE-10 = 0.480112
M6 probability ECE-10 = 0.046582
M6 Brier = 0.020504
M7 probability ECE-10 = 0.048281
```

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

## Current Compatibility Dataset V3 Independent Validity Support Contact Balancing Plan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_ready_for_materialization
selected_path = materialize_support_contact_primary_independent_validity_with_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```

Decision:

- reject exact predicate-class balance as the support/contact primary balancing unit because it
  leaves only `88` support/contact rows;
- reject the old pose-conditioned `400`-row target as main independent-validity evidence because
  it is constructed `C_e` mechanism evidence, not GT-anchored independent validity;
- select predicate-balanced support/contact independent-validity materialization with `1200` target
  rows and `800` minimum rows.

Capacity:

```text
support/contact family scan-capped capacity = 2134
lying on scan-capped capacity = 1370
standing on scan-capped capacity = 764
target rows = 1200
lying on target = 600 rows, 300/300 positive/negative
standing on target = 600 rows, 300/300 positive/negative
```

Boundary:

- keep calibrated `p_rel` / `p_obs`, paper-level, held-out, all-family, and learned-smoke claims
  blocked;
- require class-pair, scan, directed-pair, rank-band, and schema shortcut audits before any learned
  smoke.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```

## Current Compatibility Dataset V3 Independent Validity Support Contact Balancing Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```

Materialized counts:

```text
candidate_rows = 1200
model_safe_view = 1200
hidden_manifest = 1200
positive / negative = 600 / 600
lying on = 300 positive + 300 negative
standing on = 300 positive + 300 negative
```

Source scan:

```text
scanned rows = 4,818,996
support/contact family rows = 370,692
primary candidate rows = 8,631
lying on candidates = 1,643 positive / 685 negative
standing on candidates = 5,921 positive / 382 negative
```

Cap audit:

```text
max single scan share = 0.0108
max single directed-pair share = 0.0017
max single class-pair share = 0.0167
max single rank-band share = 0.4017
```

All cap and schema prechecks passed. Model-safe view has zero forbidden construction-key hits.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Independent Validity Support Contact Balancing Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

The `1200`-row support/contact-primary candidate set remains label-balanced:

```text
positive / negative = 600 / 600
lying on = 300 / 300
standing on = 300 / 300
```

Schema leakage checks passed:

```text
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
```

Shortcut audit result:

```text
critical_high_or_medium_risk = 4
source_confidence_high_or_medium_risk = 0
raw_geometry_high_or_medium_risk = 0
blocked_hidden_high_risk = 6
```

The blocking allowed probes are `subject_class_label`, `object_class_label`,
`subject_object_class_pair`, and `predicate_x_class_pair`. `predicate_label`
itself is balanced at `0.500000`, and `rank_band` remains low risk, but the
object-class composition is still too predictive. Learned smoke is therefore
blocked until a path decision is made.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Independent Validity Support Contact Class Pair Repair Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_blocked_class_pair_diagnostic_possible
validation_errors = 1
next_todo = compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

Full train-side support/contact capacity:

```text
scanned rows = 4,818,996
support/contact family rows = 370,692
primary candidate rows = 8,631
lying on positive / negative = 1,643 / 685
standing on positive / negative = 5,921 / 382
```

Repair capacity:

```text
class_pair scan-capped capacity = 426
predicate_x_class_pair scan-capped capacity = 88
predicate_x_class_pair_x_rank_band scan-capped capacity = 88
```

Strict predicate-class capacity by predicate:

```text
lying on = 64
standing on = 24
```

Interpretation:

- strict `predicate + subject_class + object_class` repair is not viable as a main support/contact
  target;
- relaxed `subject_class + object_class` contrast is possible only as a small diagnostic;
- learned smoke remains blocked until a diagnostic/freeze path decision is made.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

## Current Compatibility Dataset V3 Independent Validity Support Contact Class Pair Repair Path Decision

Default output:

```text
artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_freeze_independent_validity_diagnostic
selected_path = freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze
```

Decision:

- reject strict support/contact `predicate + subject_class + object_class` repair as a main target;
- defer relaxed class-pair and object-class-masked settings as optional diagnostic only;
- freeze support/contact independent-validity as diagnostic-only;
- keep earlier pose-conditioned support/contact as scoped `C_e` mechanism evidence;
- move to H002 scope synthesis.

Main capacity reason:

```text
predicate_x_class_pair scan-capped capacity = 88
lying on strict capacity = 64
standing on strict capacity = 24
class_pair relaxed diagnostic capacity = 426
```

Next:

```text
compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze
```

## Current Compatibility Dataset V3 Scope Synthesis After Support Contact Independent Validity Freeze

Default output:

```text
artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/
```

Result:

```text
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_ready
selected_path = freeze_current_scope_select_independent_target_source_decision
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

Current claim boundary:

```text
H002 supports train-only predicate-conditioned compatibility C_e evidence.
It does not yet support paper-level, held-out, all-family, support/contact
independent-validity, or calibrated p_rel/p_obs claims.
```

Family scope:

```text
relative_vertical = main train-only C_e evidence
support_contact_pose_conditioned = scoped constructed C_e mechanism evidence
support_contact_independent_validity = diagnostic-only frozen
attachment_like = deferred
proximity = deferred
```

Key evidence:

```text
M6_TG_compatibility_interaction AUROC = 0.9956328125
geometry-only AUROC = 0.5270640625
source-only AUROC = 0.56811015625
wrong-predicate AUROC = 0.02664375
support/contact strict predicate-class capacity = 88
```

Next:

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

## Current Compatibility Dataset V3 Independent Target Source Decision

Default output:

```text
artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/
```

Result:

```text
status = h002_compatibility_dataset_v3_independent_target_source_decision_selected
selected_path = select_support_contact_visual_mesh_human_audit_with_size_containment_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

Decision:

```text
selected_main_route = support_contact_human_visual_mesh_audit_target
selected_predicates = lying on, standing on, supported by
optional_probe = size_relative first; containment_inclusion second
```

Interpretation:

- The current H002 bottleneck is target-source independence, not relation-type count.
- `relative_vertical` is retained as clean train-only `C_e` anchor evidence.
- `support_contact` is selected because it is the best path to test independent reliability with
  visual/mesh evidence.
- `bigger than` / `smaller than` and containment/inclusion are optional diagnostic probes, not the
  next main route.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory
selected_path = plan_visual_mesh_audit_target_source_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

Target contract:

```text
selected_predicates = lying on, standing on, supported by
target_total_rows = 480
minimum_total_rows = 360
minimum_per_predicate = 80
minimum_accept/reject/abstain = 80/80/60
```

Interpretation:

- The target source is visual/mesh audit evidence, not source score, rank, queue kind, old
  `geometry_status`, old `p_geom_valid`, or GT-missing status.
- `No-GT` is never a negative label by itself.
- `supported by` is broad/superordinate and is not used as a clean negative for `standing on`.
- `C_e`, `Q_e`, `p_obs`, and `p_rel` are separated: abstain/observability rows are not false
  negatives for relation reliability.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization
selected_path = source_inventory_ready_packet_materialization_required
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

Selected source:

```text
selected_rows = 480
lying on / standing on / supported by = 194 / 156 / 130
hidden queue_kind = HL 112 / LH 368
label_match_status = exact_match 180 / family_match 85 / no_gt_for_pair 149 / pair_has_other_predicate 66
all_required_sources_exist = true
```

Cap gates:

```text
max_scan_rows = 4 <= 24
max_subject_object_class_pair_rows = 13 <= 48
max_directed_pair_rows = 2 <= 2
hard_surface_rows = 90 <= 288
hidden_HL_rows = 112 >= 60
```

Interpretation:

- The visible label sheet has 480 blank review rows but still uses `PACKET_PENDING/...` paths.
- The hidden manifest keeps source score/rank, queue kind, old `geometry_status`, old
  `p_geom_valid`, and label-match status out of the review sheet.
- This is source-ready and packet-materialization-ready, not label-ready.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Packet Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill
selected_path = packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

Packet readiness:

```text
packet_rows = 480
ready = 480
non_ready = 0
visible_leakage_hits = 0
lying on / standing on / supported by ready = 194 / 156 / 130
```

Evidence readiness:

```text
subject_image_rows = 480
object_image_rows = 480
pair_crop_rows = 480
mesh_render_rows = 480
multiview_sheet_rows = 480
total_subject_images = 1884
total_object_images = 1884
```

Boundary:

- The visible sheet is now label-ready.
- `mesh_contact_render.png` is a reviewer-facing mesh/geometry availability card, not a full 3D
  contact-surface render.
- Hidden source score/rank, queue kind, old `geometry_status`, old `p_geom_valid`, label-match
  status, construction bucket, prediction id, subject id, and object id remain outside the visible
  sheet.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Fill

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion
```

Label provenance:

```text
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
used_hidden_manifest = false
used_source_score_or_rank = false
used_old_geometry_status_or_p_geom_valid = false
```

Counts:

```text
rows = 480
accept / reject / abstain = 208 / 161 / 111
observability sufficient = 480
lying on = accept 53 / reject 87 / abstain 54
standing on = accept 73 / reject 63 / abstain 20
supported by = accept 82 / reject 11 / abstain 37
```

Interpretation:

- This is a user-requested Codex proxy label fill, not an independent blind human audit.
- The next step must join hidden metadata after label lock and run target-independence/shortcut
  audits before any learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Path Decision

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

Decision:

- Do not run learned smoke on the current support/contact visual/mesh class-pair repair target.
- Freeze this artifact as diagnostic-only.
- Keep `relative_vertical` as the clean train-only `C_e` anchor.
- Keep support/contact pose-conditioned evidence as scoped mechanism evidence.
- Keep calibrated `p_rel` / `p_obs`, support/contact main claim, and paper-level claim blocked.

Key evidence:

```text
p_rel/C_e binary rows = 304
p_rel/C_e binary counts = positive 198 / negative 106
predicate_x_class_pair p_rel majority accuracy = 1.0000
hidden predicate_class_pair p_rel majority accuracy = 1.0000
generic_endpoint_visible relation-multiclass majority accuracy = 0.6208
non-generic filtered p_rel rows = 304
non-generic filtered predicate_x_class_pair p_rel majority accuracy = 1.0000
```

Interpretation:

- The repair fixed binary row mass but not target identifiability.
- Generic endpoint filtering helps the multiclass abstain shortcut only; it does not fix the
  binary `p_rel` / `C_e` shortcut.
- A stricter within-`predicate_x_class_pair` relabel is not a clean continuation of the current
  proxy artifact. It would need a new independent visual/mesh audit protocol or a different
  source construction.

Next:

```text
compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

## Current Compatibility Dataset V3 Relation-Family Scope Synthesis After Visual/Mesh Freeze

Default output:

```text
artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze/
```

Result:

```text
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready
selected_path = all_relation_family_generalization_scan_with_proximity_first
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_generalization_capacity_scan
selected_first_active_family = proximity
selected_first_active_predicates = close by
```

Open3DSG train-full relation inventory:

```text
scans = 3738
relations = 79704
unique predicates with GT count > 0 = 25
official/mapped predicates in inventory = 29
```

Family priority:

```text
proximity / close by = selected first active probe, GT 12300, H002 queue 171324
support_contact = individual predicate probe possible, GT 12600, H002 queue 161498
relative_vertical = already clean anchor, GT 3552, H002 queue 124604
size_relative = optional quick probe, GT 1822
containment_in = optional schema probe, GT 330
attachment_deferred = defer visual/mesh-heavy, GT 8767
relative_horizontal = defer reference-frame ambiguity, GT 36944
identity_symmetry / part_structural = diagnostic/defer
```

Decision:

- Do not run all relation-type models immediately.
- Do run all-relation-family capacity/shortcut eligibility scan next.
- Use `close by` as the first active family.
- Keep `standing on`, `lying on`, and `supported by` as individual predicate probes because grouped
  support/contact failure does not prove each predicate fails.
- In final paper framing, successful families can be main evidence only if failed families and failure
  causes are also reported to avoid cherry-picking.

Next:

```text
compatibility_dataset_v3_relation_family_generalization_capacity_scan
```

## Current Compatibility Dataset V3 Relation-Family Generalization Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready
selected_path = select_proximity_close_by_target_plan_with_all_family_eligibility_table
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_target_plan
```

Close-by snapshot:

```text
queue_rows = 171324
HL rows = 0
LH rows = 171324
label_match_status = no_gt_for_pair 130125 / pair_has_other_predicate 31675 / exact_match 9524
geometry_status = satisfied 171324
mixed class-pair groups exact-vs-other = 1292
balanced rows exact-vs-other = 15444
```

Interpretation:

- `close by` has enough count and class-pair mixing to justify a target plan.
- It is LH-only in the current queue, so a naive binary target would be dangerous.
- The next target plan must not treat all no-GT `close by` pairs as negatives.
- The target needs same-distance / similar-distance hard negatives, object-scale controls, coverage controls, and distance-only baselines.

Support/contact individual predicate capacity remains nonzero:

```text
standing on = queue 50245 / exact 5871 / mixed class-pair groups 96
lying on = queue 60652 / exact 1440 / mixed class-pair groups 75
supported by = queue 50601 / exact 491 / mixed class-pair groups 105
```

This means grouped support/contact failure does not prove each predicate fails. Per-predicate support/contact
probes are still possible after `close by` or as parallel diagnostics.

Next:

```text
compatibility_dataset_v3_proximity_close_by_target_plan
```

## Current Compatibility Dataset V3 Proximity Close-By Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_target_plan_ready_for_source_inventory
selected_path = plan_close_by_source_inventory_for_near_far_hard_negative_target
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_source_inventory
```

Full train close-by snapshot:

```text
close_by_rows = 185346
label_match_status = no_gt_for_pair 142571 / pair_has_other_predicate 33247 / exact_match 9528
geometry_status = satisfied 171326 / uncertain 7328 / unsatisfied 6692
rank_band = rank_gt1000 133872 / rank_501_1000 42864 / rank_201_500 8596 / rank_101_200 12 / top50 2
```

Decision:

- Proceed with `close by` first.
- Do not use `no_gt_for_pair` or `pair_has_other_predicate` as automatic reject labels.
- Treat `exact_match` as a positive-anchor source, then verify scale-aware geometry and coverage.
- Mine hard negatives from far/similar-distance pair geometry in full train rows, not from missing GT alone.
- Keep `distance_only`, `p_geom_valid_rule`, source-only, class-pair-only, shuffled-geometry, and wrong-pair controls.
- Defer `standing on`, `lying on`, and `supported by` to individual predicate probes after this inventory.

Boundary:

```text
split = train_only_target_plan
validation_usage = false
test_usage = false
materializes_rows = false
fills_labels = false
runs_learned_smoke = false
paper_evidence_allowed = false
```

Next:

```text
compatibility_dataset_v3_proximity_close_by_source_inventory
```

## Current Compatibility Dataset V3 Proximity Close-By Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan
selected_path = select_close_by_candidate_materialization_plan_with_far_geometry_negatives_and_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

Candidate inventory:

```text
close_by_rows = 185346
accept_anchor = 8682
reject_far_geometry = 6688
abstain_or_audit = 169972
gt_geometry_conflict = 4
```

Bucket policy:

```text
near = normalized_distance_xy <= 0.8
far = normalized_distance_xy >= 2.5
ambiguous = otherwise
```

Control capacity:

```text
class_pair balanced rows = 3684
class_pair_rank balanced rows = 3280
raw_distance_bin balanced rows = 804
norm_distance_bin balanced rows = 0
scan balanced rows = 7656
```

Interpretation:

- Source inventory gates passed, so proceed to candidate materialization planning.
- Reject candidates are based on far geometry, not no-GT status alone.
- `no_gt_for_pair` near rows remain `abstain_or_audit`, not negative.
- Normalized-distance matched capacity is zero, so `distance_only` must be a mandatory baseline and raw-distance matched rows should be a diagnostic subset.
- `p_geom_valid` remains baseline-only.

Boundary:

```text
split = train_only_source_inventory
validation_usage = false
test_usage = false
materializes_rows = false
fills_labels = false
runs_learned_smoke = false
paper_evidence_allowed = false
```

Next:

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

## Current Compatibility Dataset V3 Proximity Close-By Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready
selected_path = materialize_close_by_controlled_candidates_with_distance_controls
validation_errors = 0
warnings = 2
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

Planned rows:

```text
planned_total_rows = 1284
primary_binary_rows = 800
primary_accept = 400
primary_reject = 400
abstain_qe_rows = 240
raw_distance_diagnostic_rows = 240
gt_geometry_conflict_audit_rows = 4
```

Caps:

```text
max_rows_per_scan = 18
max_rows_per_class_pair = 48
max_rows_per_class_pair_rank = 24
max_rows_per_directed_pair = 2
max_rows_per_raw_distance_bin = 80
```

Required controls:

```text
class_pair_only
source_only_Z
distance_only
p_geom_valid_rule
raw_distance_diagnostic_subset
shuffled_geometry
wrong_pair_geometry
```

Warnings:

```text
normalized_distance_matched_capacity_zero
reject_pool_contains_no_gt_rows
```

Interpretation:

- Proceed to materialization.
- Do not claim close-by evidence without `distance_only` and `p_geom_valid_rule` baselines.
- Keep no-GT/reject construction fields hidden.
- Schema and shortcut audit is mandatory before learned smoke.

Next:

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

## Current Compatibility Dataset V3 Proximity Close-By Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit
```

Materialized rows:

```text
total_rows = 1284
primary_binary_rows = 800
raw_distance_diagnostic_rows = 240
abstain_qe_rows = 240
gt_geometry_conflict_audit_rows = 4
```

Prechecks:

```text
quota_audit = pass
cap_audit = pass
schema_precheck = pass
max_scan_rows = 15 / 18
max_directed_pair_rows = 1 / 2
max_primary_class_pair_rows = 6 / 48
max_primary_class_pair_rank_rows = 2 / 24
max_raw_distance_bin_rows = 50 / 80
```

## Current Compatibility Dataset V3 Proximity Close-By Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut
validation_errors = 0
critical_blockers = 5
learned_smoke_allowed = false
main_claim_verdict = blocked_for_close_by_current_target
next_todo = compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

Critical blockers:

```text
primary_binary normalized_distance_xy = accuracy 1.000000 / AUROC 1.000000
primary_binary normalized_distance_3d = accuracy 1.000000 / AUROC 1.000000
primary_binary distance_xy = accuracy 0.992500 / AUROC 0.999556
primary_binary distance_3d = accuracy 0.987500 / AUROC 0.998975
primary_binary p_geom_valid_rule = accuracy 0.991250 / AUROC 0.999594
```

Interpretation:

- `close by` current target is valid as diagnostic proximity-family evidence.
- It is not valid as a main H002 claim because distance/rule geometry baselines already solve it.
- The next action is a path decision, not learned smoke.

Next:

```text
compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Proximity Close-By Path Decision

Default output:

```text
artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe
selected_path = freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

Decision:

- Freeze current `close by` target as diagnostic/generality evidence.
- Do not run learned smoke on the current `close by` target.
- Do not promote current `close by` target as the main H002 claim.
- Select support/contact individual predicate probe planning next.

Next probe priority:

```text
1. standing on = primary individual probe, queue 50245, exact 5871, mixed class-pair groups 96
2. lying on = secondary pose-conditioned probe, queue 60652, exact 1440, mixed class-pair groups 75
3. supported by = diagnostic superordinate probe, queue 50601, exact 491, mixed class-pair groups 105
```

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Probe Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory
selected_path = plan_individual_support_contact_source_inventory_standing_primary_lying_secondary_supported_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

Decision:

- Do not reuse grouped support/contact as a main learned target.
- Use `standing on` as the primary individual predicate probe.
- Use `lying on` as the secondary pose-conditioned probe.
- Use `supported by` as a diagnostic superordinate probe, not as a clean negative for `standing on`.
- Do not run learned smoke until source inventory, materialization, and shortcut audit pass.

Predicate priority:

```text
standing on = primary, queue 50245, exact 5871, mixed class-pair groups 96
lying on = secondary, queue 60652, exact 1440, mixed class-pair groups 75
supported by = diagnostic, queue 50601, exact 491, mixed class-pair groups 105
```

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_standing_lying_individual_predicate_cells_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

Predicate-level result:

```text
standing on = primary, rows 50245, class-pair balanced rows 382, mixed groups 13
lying on = secondary, rows 60652, class-pair balanced rows 414, mixed groups 13
supported by = diagnostic, rows 50601, class-pair balanced rows 164, mixed groups 45
```

Decision:

- `standing on` and `lying on` are ready for a candidate materialization plan.
- `supported by` remains diagnostic/superordinate, not a clean binary target.
- Hard-surface, class-pair, rank/source, no-GT, and same-G controls are required before materialization.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_ready
selected_path = materialize_route_aware_standing_lying_candidates_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization
```

Planned quota:

```text
standing on = 160 clear_accept + 160 hard_reject_lying_like
lying on = 160 clear_accept + 160 hard_reject_standing_like
supported by diagnostic = 40 clear_accept + 40 hard_reject_no_support + 80 overlap_or_abstain
main compatibility rows = 640
diagnostic rows = 160
total rows = 800
```

Materialization gates:

```text
standing_class_pair_capacity = 382 / 320
lying_class_pair_capacity = 414 / 320
supported_by_diagnostic_capacity = 164 / 80
planned_total_rows = 800 / 800
supported_by_not_main_target = diagnostic_only
```

Decision:

- `standing on` and `lying on` are selected as route-aware compatibility-ready materialization targets.
- `supported by` remains diagnostic/superordinate and is excluded from the main binary learned target.
- This is still a plan: no rows, labels, learned smoke, validation, or test evidence were generated in this step.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_route_aware_standing_lying_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit
```

Materialized rows:

```text
total_rows = 800
main_compatibility_rows = 640
supported_by_diagnostic_rows = 160
standing on = 160 clear_accept + 160 hard_reject_lying_like
lying on = 160 clear_accept + 160 hard_reject_standing_like
supported by = 40 clear_accept + 40 hard_reject_no_support + 80 overlap_or_abstain
unique_scans = 357
hard_surface_rows = 474
```

Schema precheck:

```text
model_safe_rows = 800
hidden_manifest_rows = 800
blocked_fields_absent_from_model_safe = true
finite_G_e_rows = 800
learned_smoke_allowed = false
```

Cap relaxation:

```text
max_rows_per_predicate_class_pair: plan 32 -> actual 200
max_rows_per_predicate_class_pair_rank: plan 24 -> actual 80
max_hard_surface_rows: plan 360 -> actual 640
```

Interpretation:

- The planned 800 rows were materialized from train-only Open3DSG RGA queues.
- `G_e` is newly computed from semseg OBB mesh/pose/contact features, not from H001 `p_geom_valid`.
- Source score/rank, GT match fields, `p_geom_valid`, old geometry status, scan/object identity, candidate role, and route name are hidden-only.
- Because cap relaxation was required, this artifact must pass schema/shortcut audit before any learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
selected_path = schema_clean_allowed_shortcuts_low_hidden_construction_risk_reported
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan
```

Audit counts:

```text
main_binary_rows = 640
diagnostic_rows = 160
sanitized_rows = 640
schema_leakage_hits = 0
allowed_high_risk_probes = 0
hidden_high_risk_probes = 2
```

Key probes:

```text
model_T_predicate_label accuracy = 0.500
model_T_subject_object_class_pair accuracy = 0.514
hidden_hard_surface_pair accuracy = 0.503
hidden_rank_band accuracy = 0.516
hidden_predicate_class_pair accuracy = 0.684
hidden_predicate_class_pair_rank accuracy = 0.706
best single G_e probe accuracy <= 0.530
hidden_p_geom_valid accuracy = 0.527
```

Hidden construction notes:

```text
hidden_label_match_status accuracy = 1.000
hidden_candidate_role accuracy = 1.000
```

Interpretation:

- Model-safe fields are schema-clean and allowed shortcut probes are low risk.
- Hidden construction fields are perfect if leaked, but they are absent from the model-safe view.
- The artifact is ready for a sanitized-view smoke plan, not for direct learned smoke execution.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Sanitized View Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan_ready
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
cv_groups = 258
mixed_label_cv_groups = 155
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner
```

Planned views:

```text
M1 = semantic_only_T
M2 = geometry_only_G
M3 = T_G_concat
M4 = T_G_predicate_geometry_interaction
M5 = T_G_Q_factorized_observability
```

Controls:

```text
wrong_T_same_G
shuffled_G_global
shuffled_G_within_predicate
no_interaction_concat
```

Key gates:

- semantic/quality shortcuts should remain `<= 0.60` AUROC;
- primary `M4` or `M5` should reach `>= 0.70` AUROC;
- primary `M4/M5` should beat `max(M1, M2)` by `>= 0.05` AUROC;
- if `M2_geometry_only_G` is within `0.02` AUROC of `M4/M5`, the result is
  geometry-dominance diagnostic rather than factorized compatibility evidence;
- learned smoke has not been run yet;
- paper evidence remains blocked.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Sanitized View Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner_diagnostic_only_failed_controls
rows = 640
positive / negative = 320 / 320
groups = 258
mixed_label_groups = 155
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis
```

Key metrics:

```text
M1_semantic_only_T AUROC = 0.4108
M2_geometry_only_G AUROC = 0.5092
M3_TG_concat AUROC = 0.4538
M4_TG_predicate_geometry_interaction AUROC = 0.6316
M5_TGQ_factorized_observability AUROC = 0.6316
C1_wrong_T_same_G AUROC = 0.3589
C2_shuffled_G_global AUROC = 0.5223
C3_shuffled_G_within_predicate AUROC = 0.4695
```

Interpretation:

- Shortcut controls passed.
- Geometry-only dominance did not occur.
- Predicate-geometry interaction improves over `T_e`, `G_e`, and plain concat.
- Primary signal is still below the planned `0.70` AUROC gate, so this remains diagnostic.
- `Q_e` adds no effect because all rows have mesh OBB evidence but no point/multiview evidence.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Failure Analysis

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_ready_select_point_multiview_evidence_plan
selected_path = freeze_obb_only_diagnostic_select_point_multiview_evidence_plan
rows = 640
errors = 267
false_positive / false_negative = 144 / 123
high_confidence_errors = 12
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan
```

Key diagnosis:

- Current support/contact individual-predicate failure is not caused by semantic shortcut or
  geometry-only dominance.
- `M4/M5` interaction improves over `T_e`, `G_e`, and plain concat, but only reaches `0.6316`
  AUROC.
- Worst class-pair slices include `shoes->floor`, `item->floor`, and `picture->floor`.
- `label_match_status=family_match` rows are hard subtype mismatch negatives, not necessarily
  physically impossible support/contact rows.
- Geometry features that explain error are weak: best error-oriented feature AUC is only
  `0.5705`.
- `Q_e` is constant: `mesh=True|point=False|view=False` for all `640` rows.

Decision:

- freeze current semseg OBB-only result as diagnostic;
- do not lower the planned gate after seeing the result;
- do not add a stronger combiner before evidence repair;
- next, plan point/multiview evidence and label-tightening review for support/contact.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Evidence Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_ready_for_source_inventory
selected_path = g_q_separated_audit_first_point_multiview_source_inventory
candidate_rows = 800
main_rows = 640
diagnostic_rows = 160
unique_scans = 357
point_ready_rows = 800
mesh_ready_rows = 800
multiview_ready_rows = 800
all_ready_rows = 800
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory
```

Evidence decision:

- `G_e` and `Q_e` must be materialized separately.
- `G_e` should use point/mesh/contact/pose evidence without predicate/source/label fields.
- `Q_e` should represent evidence sufficiency: point density, mesh completeness, view count,
  crop quality, occlusion, conflict, and missing-evidence status.
- Multiview crops are audit and `Q_e` support first, not immediate learned visual input.
- `standing on` remains the upright-pose / bottom-contact route.
- `lying on` remains the horizontal-pose / broad-contact route.
- `supported by` remains diagnostic-only until subtype boundary is clearer.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_ready_for_materialization_plan
selected_path = source_inventory_ready_for_gq_separated_materialization_plan
rows = 800
unique_scans = 357
point_pair_crop_possible = 800 / 800
mesh_contact_patch_possible = 800 / 800
multiview_packet_possible = 800 / 800
g_e_point_mesh_ready = 800 / 800
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan
```

`Q_e` is no longer constant under the planned source features:

```text
limited = 419
sufficient = 373
uncertain_or_low_observability = 8
```

Main `Q_e` reason codes:

```text
low_semseg_segment_count = 345
low_crop_score = 98
few_cropped_instance_views = 60
```

Decision:

- proceed to `G_e` / `Q_e` separated materialization planning;
- do not run learned smoke yet;
- do not use multiview as learned visual input yet;
- keep `supported by` diagnostic-only;
- require OBB-only, point-only, mesh/contact-only, wrong-pair, shuffled-geometry, wrong-view,
  and shuffled-view controls after materialization.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_ready
selected_path = plan_gq_separated_materialization_with_controls
rows = 800
main_rows = 640
diagnostic_rows = 160
Q_e states = limited 419 / sufficient 373 / uncertain_or_low_observability 8
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```

Planned feature blocks:

```text
T_e
G_e_obb_baseline
G_e_point_pose
G_e_contact_patch
Q_e_observability
V_mv_audit_manifest
Z_e_safe
```

Required controls after materialization:

```text
OBB-only baseline
point-only ablation
mesh/contact-only ablation
wrong-pair geometry
shuffled geometry, global and within predicate
wrong-view
shuffled-view
class-pair/rank/source shortcut probe
```

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_gq_separated_point_mesh_view_audit_rows
rows = 800
main_rows = 640
diagnostic_rows = 160
point_stats_found_rows = 800
predicate_counts = lying on 320 / standing on 320 / supported by 160
Q_e states = limited 419 / sufficient 373 / uncertain_or_low_observability 8
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit
```

Materialized files:

```text
model_safe_view.jsonl = 800 rows
source_manifest.jsonl = 800 rows
visual_audit_manifest.jsonl = 800 rows
control_manifest.jsonl = 800 rows
feature_stats.json = finite/range audit
validation_errors.jsonl = 0 rows
```

판단:

- point-derived `G_e`와 observability `Q_e`를 분리해 실제 artifact로 만들었다.
- multiview는 audit/`Q_e` metadata로만 유지했고 learned visual input으로 쓰지 않았다.
- source confidence `Z_e`, scan/object ids, GT match, H001 `p_geom_valid`는 `model_safe_view`
  밖의 hidden manifest에만 둔다.
- 다음 단계는 schema/shortcut audit다. 여기서 raw geometry, predicate/class pair, `Q_e`
  state만으로 label이 쉽게 맞으면 learned smoke로 넘기지 않는다.

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
main_binary_rows = 640
diagnostic_rows = 160
smoke_ready_rows = 640
target_counts = 320 / 320
schema_leakage_hits = 0
allowed_high_risk_probes = 0
allowed_medium_risk_probes = 0
hidden_high_risk_probes = 3
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan
```

Top allowed model-safe probe:

```text
model_T_predicate_x_class_pair acc = 0.684375, risk = low
```

판단:

- 새 point/contact/observability model-safe view는 schema leakage 없이 smoke planning으로 넘길 수 있다.
- hidden `candidate_role`, `label_match_status`, `machine_hint`는 label을 완벽히 설명하므로
  이후에도 절대 model input으로 사용하면 안 된다.
- 다음 단계는 learned smoke 실행이 아니라 smoke plan 작성이다.

## Current Compatibility Dataset V3 Support/Contact Individual Predicate Point/Multiview Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_ready
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
cv_groups = 258
mixed_label_cv_groups = 155
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner
```

Primary model view:

```text
M8_TG_point_contact_interaction
```

Required comparisons:

```text
M1 semantic-only
M2 OBB geometry-only
M3 point-pose only
M4 contact-patch only
M5 point+contact geometry-only
M6 old OBB T+G
M7 point/contact T+G concat
M8 point/contact predicate-geometry interaction
M9 T+G+Q observability diagnostic
```

판단:

- 다음 단계는 smoke runner다.
- runner는 `smoke_ready_view.jsonl`만 읽어야 한다.
- `Z_e`, source score/rank, H001 `p_geom_valid`, scan/object ids, visual paths, hidden construction
  fields는 여전히 model input 금지다.

Decision:

- proceed to actual materialization;
- keep learned smoke blocked;
- keep multiview learned input blocked;
- keep `supported by` diagnostic-only;
- validate finite numeric features and blocked-field absence before any smoke.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Label Ingestion

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_class_pair_repair_labels_run_shortcut_diagnostics
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

Target counts:

```text
rows = 480
relation multiclass = accept 198 / reject 106 / abstain 176
p_rel binary rows = 304
p_rel positive/negative = 198 / 106
C_e binary rows = 304
C_e positive/negative = 198 / 106
p_obs = all 480 positive
Q_e = all 480 sufficient
```

Shortcut result:

```text
learned_smoke_allowed = false
predicate_x_subject_object_class_pair_visible p_rel majority accuracy = 1.0000
predicate_class_pair_hidden p_rel majority accuracy = 1.0000
subject_label p_rel majority accuracy = 0.7007
object_label p_rel majority accuracy = 0.6875
generic_endpoint_visible relation_multiclass majority accuracy = 0.6208
```

Interpretation:

- Binary mass improved and is usable in count terms.
- The target is still not smoke-ready because `predicate + class-pair` and
  endpoint labels reconstruct the proxy label too easily.
- Generic endpoints explain a large abstain shortcut in the multiclass target.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Label Fill

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_for_class_pair_repair_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

Label provenance:

```text
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
used_visible_review_sheet = true
used_packet_paths = true
used_hidden_manifest = false
used_source_score_or_rank = false
used_old_geometry_status_or_p_geom_valid = false
used_label_match_status = false
```

Label counts:

```text
rows = 480
accept / reject / abstain = 198 / 106 / 176
observability sufficient = 480
lying on = accept 47 / reject 45 / abstain 68
standing on = accept 52 / reject 46 / abstain 62
supported by = accept 99 / reject 15 / abstain 46
```

Generic endpoint risk:

```text
generic_endpoint_rows = 100
generic_endpoint_labels = abstain 100
non_generic_labels = accept 198 / reject 106 / abstain 76
```

Interpretation: the repair candidate set is now label-filled, but it is not
smoke-ready until post-lock ingestion checks whether class-pair and generic-label
shortcuts are actually controlled.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Packet Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill
selected_path = class_pair_repair_packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
```

Packet readiness:

```text
packet_rows = 480
label_ready_rows = 480
non_ready_rows = 0
visible_leakage_hits = 0
lying on / standing on / supported by ready = 160 / 160 / 160
accept_like / reject_like ready = 240 / 240
subject_image_rows = 480
object_image_rows = 480
pair_crop_rows = 480
mesh_render_rows = 480
multiview_sheet_rows = 480
```

Visible label sheet:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/visible_review_sheet_with_packets.csv
```

Boundary: `repair_proxy_kind` remains hidden and sampling-only. `mesh_contact_render.png` is
still an evidence-availability card, not a full 3D contact-surface render. Some
generic class labels such as `object` remain visually weak and should be tracked
in the next label fill and post-lock shortcut audit.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Path Decision After Label Ingestion

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization
selected_path = class_pair_controlled_repair_first
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

Train split boundary:

```text
source = artifacts/train_rga_full/open3dsg_train_full/rga/train_hl_queue.jsonl
source = artifacts/train_rga_full/open3dsg_train_full/rga/train_lh_queue.jsonl
validation_usage = false
test_usage = false
```

Current 480-row label artifact has almost no exact control capacity:

```text
class_pair mixed groups = 1
class_pair balanced rows = 2
predicate_x_class_pair mixed groups = 0
predicate_x_class_pair balanced rows = 0
```

Full train support/contact repair capacity is sufficient:

```text
source_rows_after_proxy_filter = 27201
predicate_x_class_pair mixed groups = 71
predicate_x_class_pair balanced raw rows = 960
```

Selected repair candidate set:

```text
selected_rows = 480
lying on / standing on / supported by = 160 / 160 / 160
accept_like / reject_like = 240 / 240
each predicate x proxy-kind cell = 80
predicate_class_pair_groups = 68
max_scan_rows = 11
max_directed_pair_rows = 1
required_source_file_errors = 0
```

Boundary: `repair_proxy_kind` is sampling-only and not a final target. The final
target still requires visible packet materialization, visible-field-only label
fill, post-lock hidden join, and shortcut audit.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

## Current Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Ingestion

Default output:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion/
```

Result:

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_proxy_labels_run_independence_diagnostics_block_smoke_if_shortcut
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

Target counts:

```text
rows = 480
relation multiclass = accept 208 / reject 161 / abstain 111
p_rel binary rows = 369
p_rel binary target = positive 208 / negative 161
C_e binary rows = 369
C_e binary target = positive 208 / negative 161
p_obs target = positive 480 / negative 0
Q_e ordinal = sufficient 480
```

Shortcut diagnosis:

```text
learned_smoke_allowed = false
subject_object_class_pair p_rel majority accuracy = 0.9973
construction_bucket_hidden p_rel majority accuracy = 0.9106
label_match_status_hidden p_rel majority accuracy = 0.8726
object_label p_rel majority accuracy = 0.8428
```

Interpretation:

- The binary `p_rel` and `C_e` target counts are sufficient.
- The target is still not acceptable for learned smoke because class-pair and
  construction/source fields can almost reconstruct the proxy labels.
- `p_obs` and `Q_e` are degenerate in this artifact because every packet is
  observable enough for the proxy labeler.
- Next step is a path decision: repair the target with stricter class-pair
  controls, or freeze this support/contact visual/mesh audit as diagnostic-only.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

## Current Size-Relative Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready
selected_path = size_relative_inventory_ready_for_candidate_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

Key counts:

```text
train anchors = 1846
bigger than / smaller than = 923 / 923
semseg OBB join = 1846 / 1846
volume compatible / ambiguous / opposes = 1760 / 50 / 36
strict same-G flip groups = 1728
strict same-G flip rows = 3456
```

Interpretation:

- `size_relative` has enough train-side source capacity for a materialization-plan
  step.
- `G_e_size` must remain predicate/source independent.
- The next plan must use same-G predicate flip rows, because a simple size threshold
  would otherwise turn this family into a geometry-only verifier rather than a
  predicate-geometry compatibility test.
- Class-pair mass is mostly same-class, but `bigger/smaller` are balanced inside
  those pairs; class-pair and construction fields remain blocked from the model view.

## Current Size-Relative Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_size_relative_same_g_predicate_flip_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```

Frozen plan:

```text
primary_groups = 1200
primary_rows = 2400
positive_rows = 1200
negative_rows = 1200
subject_bigger_groups = 600
subject_smaller_groups = 600
ambiguous_diagnostic_rows = 100
gt_geometry_conflict_audit_rows = 72
```

Interpretation:

- The next materialization must create two candidate rows per group with identical
  `G_e_size` and flipped `T_e` predicates.
- The first main model-safe view allows predicate text plus continuous size-ratio
  geometry only; class labels, class-pair, GT/source labels, construction fields,
  discretized direction fields, and `Z_e` are blocked.
- Geometry-only success is not a valid H002 main claim for this family. The required
  signal is `T_e x G_e_size` compatibility, verified by wrong-T and shuffled-G controls.

## Current Size-Relative Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = size_relative_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```

Counts:

```text
candidate_rows = 2572
primary_compatibility_rows = 2400
diagnostic_ambiguous_size_rows = 100
audit_gt_geometry_conflict_rows = 72
model_safe_main_rows = 2400
model_safe_qe_rows = 2572
group_rows = 1286
```

Precheck:

```text
primary C_e positive / negative = 1200 / 1200
subject_bigger / subject_smaller groups = 600 / 600
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1200
max class-pair groups = 232 / 240
max class-pair-direction groups = 116 / 120
max scan groups = 13 / 24
```

Interpretation:

- The artifact is ready for schema/shortcut audit.
- The primary rows preserve the intended same-G predicate-flip structure.
- Hidden/source/class/construction fields are separated into `hidden_manifest.jsonl`.
- No learned smoke has been run, so size-relative is not yet a passed H002 result.

## Current Size-Relative Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = size_relative_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit
```

Counts:

```text
primary_rows = 2400
primary C_e positive / negative = 1200 / 1200
feature_path_violations = 0
group_integrity_errors = 0
smoke_ready_rows = 2400
```

Probe result:

```text
T_predicate_label_only = 0.500
G_exact_tuple_only = 0.500
G_single_ratio probes = 0.500 AUROC each
TG_exact_interaction = 1.000
hidden class/source/scan/volume probes = 0.500
hidden construction probes = 1.000, audit-only
```

Interpretation:

- Model-safe `T_e` alone and `G_e_size` alone cannot solve the target.
- The intended signal is the `T_e x G_e_size` compatibility interaction.
- Hidden construction shortcuts are present but remain outside model-safe features.
- The next stage may define the train-only learned smoke plan, but size-relative is
  still not a paper-level result.

## Current Size-Relative Sanitized View Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan
```

Runner-ready view:

```text
rows = 2400
C_e positive / negative = 1200 / 1200
cv_groups = 1200
paired groups = 1200
predicate_counts = bigger than 1200 / smaller than 1200
feature blocks = T_e + G_e_size
```

Frozen comparison:

```text
primary = M4_TG_size_interaction
single-factor baseline max = 0.60 AUROC
primary gate = 0.95 AUROC
primary gain gate = +0.30 over best single-factor baseline
controls = wrong-T, shuffled-G global, shuffled-G within predicate, sign-flipped G, no-interaction concat
```

Interpretation:

- This step only freezes the learned-smoke protocol.
- The next step may implement and run the train-only grouped-CV smoke runner.
- A passing runner would support a `size_relative` compatibility route, not a final
  paper-level claim.

## Current Size-Relative Sanitized View Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls
overall = size_relative_smoke_passed_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_smoke_result_review_after_runner
```

Main metrics:

```text
M1_semantic_only_T AUROC = 0.4707
M2_geometry_only_G_size AUROC = 0.5000
M3_TG_concat_no_interaction AUROC = 0.4707
M4_TG_size_interaction AUROC = 0.9999
C1_wrong_T_same_G AUROC = 0.00009
C2_shuffled_G_global AUROC = 0.4931
C3_shuffled_G_within_predicate AUROC = 0.4767
C4_sign_flipped_G_control AUROC = 0.00008
paired positive-margin fraction = 0.9933
```

Interpretation:

- `size_relative` passed the train-only compatibility smoke.
- The result supports `T_e x G_e_size` compatibility, not geometry-only scoring.
- The output probability is not a calibration claim because ECE remains high.
- The next step is result review and claim-position decision before any paper-level
  promotion.

## Current Size-Relative Smoke Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_size_relative_as_main_compatibility_route_evidence_keep_calibration_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative
```

Decision:

- `size_relative` is positioned as `main compatibility-route mechanism evidence`.
- The evidence is the interaction pattern: `T_e` only `0.4707`, `G_e_size` only
  `0.5000`, plain concat `0.4707`, but `T_e x G_e_size` `0.9999` AUROC.
- Wrong-T `0.00009`, shuffled-G `0.4931/0.4767`, and sign-flipped-G `0.00008`
  confirm that the signal depends on predicate-conditioned geometry.
- The result does not support calibrated `p_rel` or `p_obs` because ECE remains high.
- It remains train-only hypothesis-stage evidence, not paper-level result.

## Current Multi-Family Synthesis After Size-Relative

Default output:

```text
artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative/
```

Result:

```text
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_size_relative_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis
```

Updated route roles:

```text
relative_vertical = clean compatibility mechanism / main
size_relative = clean compatibility mechanism / main with calibration caveat
support_contact = challenging compatibility route / main with caveat
proximity = geometry-easy control / diagnostic
attachment_like = observability-heavy future route
support_contact_superordinate = diagnostic taxonomy
relative_horizontal = reference-frame deferred
```

Interpretation:

- `size_relative` adds a second clean mechanism route next to `relative_vertical`.
- The current H002 claim is now relation-aware evidence routing, not a fixed universal
  semantic-geometry fusion formula.
- The claim remains train-only and mechanism-level.
- Calibrated `p_rel`/`p_obs`, paper-level performance, and all-family generality remain
  blocked.
- The previous ablation/table plan predates `size_relative`, so the next step is an
  updated table-plan contract rather than Docker promotion.

## Current Ablation And Table Plan Update After Size-Relative

Default output:

```text
artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis/
```

Result:

```text
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis_ready
selected_path = freeze_size_relative_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan
```

Updated candidate tables:

```text
T1 = Predicate-Geometry Compatibility Mechanism
     rows: relative_vertical, size_relative, support_contact
T2 = Relation-Aware Evidence Routing Taxonomy
T3 = Diagnostic Boundary Cases
T4 = Calibration and Claim Boundary
```

Required main comparisons:

```text
T_e only
Z_e only where available
G_e only
T_e + G_e plain concat
C_e = interaction(T_e, G_e)
wrong-T
shuffled-G
sign-flip where meaningful
Q_e controls for p_obs, not relation truth
```

Interpretation:

- The table plan now includes `size_relative` as a clean mechanism row.
- It still blocks calibrated `p_rel`/`p_obs`, paper-level performance, all-family
  generality, support/contact solved wording, and geometry-only framework wording.
- The next step is to decide whether the current route coverage is sufficient or
  another relation family is needed before promotion planning.

## Current Route Coverage Sufficiency Review

Default output:

```text
artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready
selected_path = coverage_not_sufficient_add_relation_family_sweep_before_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review
```

Decision:

- Current coverage is not sufficient for promotion planning.
- The current three main rows are useful but not enough to stop exploration:
  `relative_vertical`, `size_relative`, `support_contact`.
- Do not train one all-family model immediately because missing families need their
  own evidence schema/source adapter first.
- Proceed with a schema-first family sweep, then judge the final claim boundary.

Expansion queue:

```text
1. relative_horizontal = reference-frame protocol and schema probe
2. containment_in = containment geometry schema/capacity probe
3. attachment_deferred = visual/mesh/Q_e protocol
4. part_structural = diagnostic boundary scan
5. identity_symmetry = out-of-scope rationale/count audit
```

## Current Additional Relation-Family Sweep Plan

Default output:

```text
artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready
selected_path = plan_schema_first_family_sweep_with_predicate_level_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan
```

Selected sweep order:

```text
1. relative_horizontal = reference-frame protocol and schema probe
2. containment_in = containment geometry schema/capacity probe
3. attachment_deferred = visual/mesh/Q_e protocol
4. part_structural = diagnostic boundary scan
5. identity_symmetry = out-of-scope rationale/count audit
```

Predicate-level fallback policy:

- If a multi-predicate family fails at family level, do not discard the whole
  family.
- Run relation-type-level schema, capacity, and shortcut probes.
- A successful predicate may become predicate-level evidence, while failed
  siblings remain diagnostic/deferred/out-of-scope.
- This policy is explicitly encoded for current expansion families and for the
  support/contact example predicates `standing on`, `lying on`, and `supported by`.

## Current Relative-Horizontal Reference-Frame Protocol Plan

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_reference_frame_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan
```

Protocol decision:

- `relative_horizontal` is not materialized yet.
- `left`, `right`, `front`, `behind`, and `in front of` require a frozen reference-frame
  contract before target construction.
- `scene_aligned_world_xy` is the first source-inventory candidate.
- `view_or_camera_frame` is audit/Q_e-first because multiple views can disagree.
- `object_centric_front_axis` is diagnostic/deferred unless semantic object-front
  orientation exists.
- `in front of` remains a secondary/diagnostic alias until the source inventory checks
  whether it behaves like `front`.

Required controls:

```text
same-G predicate flip
wrong-frame rotation
axis sign flip
subject-object swap
predicate alias audit
class-pair/source shortcut audit
axis-boundary abstain
```

## Current Relative-Horizontal Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_inventory_ready_for_candidate_materialization_plan_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory
```

Key counts:

```text
left/right train rows = 12,016 / 12,016
front/behind train rows = 6,766 / 6,766
in front of train rows = 0
centroid_pair_join_rate = 1.0
obb_pair_join_rate = 1.0
camera_pose_rate = 1.0 for observed anchors
```

Selected source-inventory axis candidates:

```text
left/right: scene_world_x, left = negative, alignment = 0.765667
front/behind: scene_world_y, front = negative, alignment = 0.755649
```

Interpretation:

- `left/right` and `front/behind` have enough train-side material for a candidate
  materialization plan.
- The selected frame candidates are not clean enough to be treated as final labels
  without `Q_e` filtering.
- `in front of` is not observed and must remain diagnostic, not merged with `front`.

## Previous Relative-Horizontal Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_relative_horizontal_same_g_predicate_flip_rows_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan
```

Frozen quota:

```text
primary_groups = 1,200
primary_rows = 2,400
positive_rows = 1,200
negative_rows = 1,200
left/right groups = 600
front/behind groups = 600
in front of rows = 0
```

Diagnostic rows are kept outside primary binary `C_e`:

```text
axis_boundary_diagnostic_rows = 320
opposing_frame_diagnostic_rows = 320
```

Main caveat:

- `relative_horizontal` is materialization-ready, not solved.
- The selected world-frame alignment remains about `0.76`, so frame disagreement
  and axis-boundary rows must be handled through `Q_e`/diagnostics.
 
## Current Relative-Horizontal Candidate Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = relative_horizontal_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization
```

Counts:

```text
candidate_rows = 3,040
primary_rows = 2,400
primary_groups = 1,200
axis_boundary_diagnostic_rows = 320
frame_disagreement_diagnostic_rows = 320
model_safe_main_rows = 2,400
```

Precheck:

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1,200
primary_label_counts = 1,200 / 1,200
primary_predicate_counts = left/right/front/behind each 600
```

Main caveat:

- This is still materialization, not a learned result.
- The next gate is schema/shortcut audit before any relative-horizontal smoke.
- `in front of` remains absent and excluded from the primary binary target.

## Current Relative-Horizontal Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = relative_horizontal_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit
```

Gate:

```text
schema_leakage_pass = true
allowed_single_feature_pass = true
group_integrity_pass = true
smoke_ready_rows = 2,400
```

Main probes:

```text
T_predicate_label_only = 0.500
G_exact_tuple_only = 0.500
G_single_delta_x = 0.500
G_single_delta_y = 0.500
G_single_horizontal_distance = 0.500
TG_signed_rule_interaction = 1.000
```

Interpretation:

- `T_e` alone and `G_e_horizontal` alone do not solve the materialized target.
- The intended signal is the interaction between predicate and signed horizontal
  geometry.
- Hidden construction proxies are high, but they are absent from the model-safe
  smoke-ready view.

## Current Relative-Horizontal Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan
```

Frozen input:

```text
rows = 2,400
positive / negative = 1,200 / 1,200
cv_groups = 1,200
paired_groups = 1,200
predicate_counts = left/right/front/behind each 600
feature_blocks = T_e + G_e_horizontal
```

Primary comparison:

```text
M1_semantic_only_T
M2_geometry_only_G_horizontal
M3_TG_concat_no_interaction
M4_TG_horizontal_interaction
```

Required controls:

```text
wrong_T_same_G
shuffled_G_global
shuffled_G_within_predicate
axis_sign_flipped_G
wrong_frame_xy_swap
subject_object_swap
no_interaction_concat
```

Main caveat:

- This is a smoke plan, not a learned result.
- The runner must prove the signal survives wrong-T, shuffled-G, wrong-frame,
  sign-flip, and endpoint-swap controls.
- Validation/test and paper evidence remain blocked.

## Current Relative-Horizontal Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan_passed_controls
validation_errors = 0
learned_smoke_executed = true
next_todo = compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner
```

Main metrics:

```text
M1_semantic_only_T AUROC = 0.4558
M2_geometry_only_G_horizontal AUROC = 0.5000
M3_TG_concat_no_interaction AUROC = 0.4558
M4_TG_horizontal_interaction AUROC = 1.0000
paired_margin_fraction = 1.0000
```

Controls:

```text
C1_wrong_T_same_G AUROC = 0.0000
C2_shuffled_G_global AUROC = 0.4942
C3_shuffled_G_within_predicate AUROC = 0.5052
C4_axis_sign_flipped_G AUROC = 0.0000
C5_wrong_frame_xy_swap AUROC = 0.2385
C6_subject_object_swap AUROC = 0.0000
```

Interpretation:

- `relative_horizontal` now has a clean train-only compatibility mechanism smoke.
- The result supports `T_e x G_e_horizontal` interaction, not semantic-only,
  geometry-only, or additive concat.
- It remains hypothesis diagnostic, not paper evidence.
- The next review must decide whether this route is main mechanism evidence,
  reference-frame diagnostic evidence, or a future/control route.

## Current Relative-Horizontal Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_relative_horizontal_as_main_compatibility_route_evidence_with_reference_frame_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal
```

Decision:

- `relative_horizontal` is promoted inside H002 as `main compatibility-route mechanism evidence`.
- The claim is frame-aware: `left/right/front/behind` require an explicit reference-frame convention.
- `in front of` is absent in the current train-side source and remains excluded.
- Calibration, held-out paper evidence, and complete horizontal ontology coverage remain blocked.

## Current Multi-Family Synthesis

Default output:

```text
artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal/
```

Result:

```text
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_relative_horizontal_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis
```

Current route map:

```text
relative_vertical = clean sign compatibility route
size_relative = clean size-comparison compatibility route
relative_horizontal = frame-aware directional compatibility route
support_contact = challenging compatibility route with caveat
proximity = geometry-easy diagnostic/control
attachment_like = observability-heavy future/deferred
```

Interpretation:

- H002 now has three clean route anchors and one challenging route.
- The method claim remains train-only mechanism evidence, not paper-level performance.
- The next step is to write the `close by` geometry-support materialization plan.

## Current Table And Ablation Plan

Default output:

```text
artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis/
```

Result:

```text
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_ready
selected_path = freeze_relative_horizontal_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan
```

Candidate tables:

```text
T1 = Predicate-Geometry Compatibility Mechanism
T2 = Relation-Aware Evidence Routing Taxonomy
T3 = Diagnostic Boundary Cases
T4 = Calibration and Claim Boundary
```

Main mechanism rows:

```text
relative_vertical
size_relative
relative_horizontal
support_contact
```

Horizontal-specific controls now include wrong-frame x/y swap, selected-axis
sign flip, and subject/object endpoint swap. This table update led to the
route-coverage sufficiency review below.

## Current Route-Coverage Sufficiency Review

Default output:

```text
artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready
selected_path = coverage_sufficient_for_hypothesis_framework_proceed_to_schema_freeze_promotion_protocol_no_new_family_now
validation_errors = 0
next_todo = compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review
```

Decision:

- 현재 route coverage는 H002 hypothesis-stage framework claim에는 충분하다.
- 새로운 relation family를 즉시 추가하지 않고 schema freeze / promotion protocol로
  넘어간다.
- 단, all-family generality, calibrated `p_rel`/`p_obs`, complete horizontal
  ontology, held-out/test reliability, paper-level result, solved support/contact
  claim은 여전히 금지한다.

## Current Schema Freeze And Promotion Protocol

Default output:

```text
artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready
selected_path = freeze_route_specific_target_definitions_and_promotion_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze
```

Frozen route taxonomy:

| Route | Relations | Role |
| --- | --- | --- |
| geometry-only learned/evaluated | `close by` | claim/control evidence |
| predicate-geometry interaction | `higher/lower`, `bigger/smaller`, `left/right/front/behind`, `standing/lying on` | main mechanism evidence |
| superordinate decomposition / relabel / abstain | `supported by` | claim/control or next probe |
| observability-aware | `attached to`, `hanging on`, `connected to` | next probe / future evidence |
| contact-orientation | `leaning against` | next feasibility |
| occlusion/coverage | `cover` | next feasibility |
| containment | `standing in`, `lying in`, `hanging in`, `inside` | next feasibility |
| identity/symmetry | `same as`, `same symmetry as` | separate route candidate |
| semantic/structural | `part of`, `belonging to` | boundary/future |
| embedded-structure | `build in` | future feasibility |

Decision:

- H002는 모든 relation을 하나의 target definition이나 하나의 fixed fusion head로
  처리하지 않는다.
- 각 relation family마다 target semantics와 evidence route를 다르게 정의한다.
- 다음 단계는 각 route별 model-safe fields, hidden fields, labels, controls, and
  artifact roots를 manifest로 고정하는 것이다.

## Current Route-Specific Target Manifest Plan

Default output:

```text
artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready
selected_path = freeze_per_route_target_manifests_select_manifest_consistency_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan
```

This artifact freezes:

- route target manifest rows: `13`
- route field manifest rows: `13`
- route hidden manifest rows: `13`
- route control manifest rows: `13`
- route artifact root plan rows: `13`
- route promotion priority rows: `13`

Key target axes:

| Route | Target Axis | Label Space |
| --- | --- | --- |
| `close by` | `geometry_support` | `geometry_supported`, `geometry_unsupported`, `abstain` |
| main interaction routes | `predicate_geometry_compatibility` | `compatible`, `incompatible`, `abstain` |
| `supported by` | `accept_relabel_abstain` | `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`, `abstain` |
| attachment route | `observability_then_reliability` | `observable_accept`, `observable_reject`, `unobservable_abstain`, `functional_or_topology_uncertain` |

Boundary:

- This step does not materialize rows.
- This step does not run a model.
- The next step is a manifest consistency audit before any route-specific
  materialization or smoke run.

## Current Route-Specific Target Manifest Consistency Audit

Default output:

```text
artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready
selected_path = manifest_consistency_pass_select_route_target_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit
```

Audit result:

```text
audit_rows = 49
pass = 49
fail = 0
```

Preserved contracts:

- `close by` remains `geometry_support`, not predicate-geometry interaction.
- `supported by` remains `accept_relabel_abstain`, not a clean binary support target.
- attachment remains `observability_then_reliability`.
- `C_e` excludes `Z_e`.
- hidden construction fields remain excluded from model-safe / `C_e` inputs.

Next action:

- write the route-specific target materialization plan;
- prioritize close-by geometry-only and supported-by decomposition routes;
- keep actual row materialization blocked until that plan passes.

## Current Route-Specific Target Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready
selected_path = freeze_materialization_waves_select_close_by_geometry_support_route_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```

Materialization waves:

| Wave | Routes | Purpose |
| --- | --- | --- |
| `W0` | `R2-R5` | normalize existing main-route artifacts into route-specific roots |
| `W1` | `R1 close by` | first concrete `geometry_support` route plan |
| `W2` | `R6 supported by` | superordinate decomposition / relabel / abstain route |
| `W3` | `R7 attached/hanging/connected` | observability schema audit before materialization |
| `W4` | `R8-R10` | leaning, cover, containment capacity/schema audits |
| `W5` | `R11-R13` | boundary/future manifests |

Selected first follow-up:

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
```

Boundary:

- This step still did not materialize rows.
- This step still did not run a model.
- The next step must preserve that `close by` is geometry-only route evidence, not
  `T_e x G_e` interaction evidence.

## Current R1 Close-By Geometry-Support Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready
selected_path = materialize_r1_close_by_as_geometry_support_route_root_not_interaction_claim
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan
```

Planned route:

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
planned_route_root = artifacts/route_specific_targets/r1_proximity/
```

Rows planned for reuse:

| Component | Rows | Role |
| --- | ---: | --- |
| primary geometry-support binary | 800 | `geometry_supported` vs `geometry_unsupported` |
| Q_e / abstain diagnostics | 240 | coverage, ambiguity, or uncertain geometry |
| raw-distance diagnostic | 240 | raw-vs-normalized distance and scale control |
| GT/geometry conflict audit | 4 | audit only, not training |

Boundary:

- `close by` is geometry-only route evidence, not `T_e x G_e` interaction evidence.
- `G_e` is the primary route evidence.
- `Q_e` controls abstain/coverage, not relation truth.
- Actual route-root row materialization is still the next gate.

## Current R1 Close-By Route Root

Default output:

```text
artifacts/route_specific_targets/r1_proximity/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready
selected_path = materialized_r1_close_by_geometry_support_route_root
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization
```

Materialized rows:

| Component | Rows |
| --- | ---: |
| total | 1,284 |
| primary geometry-support binary | 800 |
| Q_e / abstain diagnostics | 240 |
| raw-distance diagnostic | 240 |
| GT/geometry conflict audit | 4 |

Label conversion:

```text
legacy C_e_label -> geometry_support_label
c_e_interaction_label = not_applicable
```

Primary binary balance:

```text
geometry_supported = 400
geometry_unsupported = 400
```

Boundary:

- This route root materializes rows but still does not run a model.
- It is train-only and uses no validation/test split.
- `close by` remains geometry-only route evidence.
- Next step is schema/shortcut audit of the route root.

## Current R1 Close-By Schema Audit

Default output:

```text
artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready
selected_path = r1_close_by_schema_pass_select_geometry_route_control_runner_plan
validation_errors = 0
passed_checks = 75
total_checks = 75
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan
```

Passed checks:

- required route files present;
- route contract and `target_axis=geometry_support` preserved;
- row count and route-row-id consistency passed;
- primary label balance passed: `400/400`;
- legacy `C_e_label` absent;
- blocked hidden/construction fields absent from model-safe feature blocks;
- `c_e_interaction_label=not_applicable` for all `1,284` rows;
- distance / scale / coverage controls ready;
- wording guard passed.

Boundary:

- Distance dominance remains an expected route property.
- R1 `close by` still cannot be used as learned interaction evidence.
- Next step may plan a geometry-only route control runner.

## Current R1 Close-By Control Runner Plan

Default output:

```text
artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready
selected_path = plan_r1_close_by_geometry_only_route_controls_no_interaction_runner
validation_errors = 0
planned_controls = 12
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner
```

Planned controls:

- raw and normalized distance geometry baselines;
- overlap geometry diagnostic;
- raw-vs-normalized scale control;
- coverage / abstain control;
- source score and rank-only baseline;
- class-pair hidden audit;
- hidden `p_geom_valid` reference diagnostic;
- shuffled-G and wrong-pair geometry controls.

Boundary:

- This step did not run metrics.
- This step did not train a model.
- R1 still remains geometry-only route evidence, not interaction evidence.

## Current R1 Close-By Control Runner Result

Default output:

```text
artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready
selected_path = ran_r1_close_by_geometry_only_route_controls_no_interaction_model
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_result_review
```

Key controls:

| Control | AUROC / Accuracy |
| --- | ---: |
| `distance_xy` AUROC | 0.999556 |
| `distance_3d` AUROC | 0.998975 |
| `normalized_distance_xy` AUROC | 1.000000 |
| `normalized_distance_3d` AUROC | 1.000000 |
| `source_score_rank` semantic AUROC | 0.552103 |
| `class_pair_only` accuracy | 0.503750 |
| `p_geom_valid_hidden_baseline` AUROC | 0.999594 |
| `shuffled_G` AUROC | 0.336178 |
| `wrong_pair_geometry` AUROC | 0.006272 |

Interpretation:

- R1 `close by` is a geometry-only route.
- Distance dominance is expected and not a failure.
- Source score and class-pair do not explain the target.
- Shuffled and wrong-pair geometry collapse.
- This is still not `T_e x G_e` interaction evidence.

## 2026-06-30 R1 Close-By Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_close_by_geometry_support_route_result_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready
selected_path = freeze_close_by_as_geometry_only_route_evidence_move_to_supported_by_decomposition
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_target_plan
```

Interpretation:

- R1 `close by` is frozen as geometry-only learned/evaluated route evidence.
- It is not `T_e x G_e` interaction evidence.
- Source score and class-pair shortcuts remain weak.
- Pair-specific `G_e` is required because shuffled/wrong-pair geometry controls collapse.
- The next route is R6 `supported by` as an accept/relabel/reject/abstain decomposition target.

## 2026-06-30 R6 Supported-By Decomposition Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready
selected_path = plan_supported_by_superordinate_accept_relabel_reject_abstain_route
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan
```

Interpretation:

- `supported by` is not a clean binary compatibility target.
- R6 uses `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`, and `abstain`.
- Existing supported-by proxy labels are reject-sparse: visual audit `82/11/37`, class-pair repair `99/15/46`.
- Candidate materialization must mine explicit no-support contradictions and mixed same-class-pair route labels.
- Learned smoke stays blocked until materialization and schema/shortcut audit pass.

## 2026-06-30 R6 Supported-By Candidate Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready
selected_path = plan_320row_supported_by_decomposition_with_240row_min_viable_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization
```

Interpretation:

- Preferred R6 materialization target is `320` rows: `80` per decomposition label.
- Minimum viable fallback is `240` rows: `60` per decomposition label.
- Current source capacity is sufficient for planning: supported-by rows `50,601`,
  clear accept `491`, hard reject/no-support `12,712`, overlap/abstain `37,398`.
- Materialization must enforce same-class-pair mixed labels, hard-surface cap,
  generic-endpoint abstain cap, no-GT-not-negative policy, and hidden source/rank fields.
- Learned smoke remains blocked until materialized rows pass schema/shortcut audit.

## 2026-06-30 R6 Supported-By Candidate Materialization

Default output:

```text
artifacts/route_specific_targets/r6_superordinate_support/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_preferred_320row_target
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit
```

Counts:

```text
total_rows = 320
accept_broad_support = 80
relabel_to_subtype = 80
reject_no_support = 80
abstain = 80
unique_scans = 257
unique_class_pairs = 173
mixed_class_pair_cells = 80
hard_surface_rows = 89
generic_abstain_rows = 14
finite_G_e_rows = 320
```

Interpretation:

- Preferred 320-row target passed; fallback was not needed.
- Model-safe rows contain `T_e`, `G_e`, `Q_e`, and decomposition labels only.
- Source/rank/GT/old geometry/`p_geom_valid` fields remain hidden-manifest only.
- Next step is schema/shortcut audit before any learned smoke.

## 2026-06-30 R6 Supported-By Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_plan
```

Counts:

```text
rows = 320
label_counts = accept_broad_support 80 / relabel_to_subtype 80 / reject_no_support 80 / abstain 80
observable_rows = 240
schema_leakage_hits = 0
allowed_high_risk_probes = 0
allowed_medium_risk_probes = 10
hidden_high_risk_probes = 8
```

Interpretation:

- R6 model-safe feature blocks have no hidden/source/GT/construction leakage.
- No allowed model-safe probe is high-risk, so smoke planning is allowed.
- Medium-risk allowed probes are expected because support decomposition should depend partly on `G_e` support/contact evidence.
- Hidden construction/audit fields can copy the target if leaked; keep `evidence_reason`, `label_match_status`, `candidate_role`, `machine_hint`, and `matched_predicates` out of model inputs.
- This is not learned evidence yet. It only unlocks the train-only smoke plan.

## 2026-06-30 R6 Supported-By Smoke Plan

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_runner
```

Runner-ready target structure:

```text
rows = 320
decomposition labels = accept_broad_support 80 / relabel_to_subtype 80 / reject_no_support 80 / abstain 80
p_obs = observable 240 / abstain 80
p_rel_binary = accept_or_relabel 160 / reject 80
p_rel_3way = accept_broad_support 80 / relabel_to_subtype 80 / reject_no_support 80
cv_groups = 257
mixed_label_cv_groups = 39
```

Planned tasks:

- `T0_decomposition_4way`
- `T1_p_obs_binary`
- `T2_p_rel_binary_observable`
- `T3_p_rel_3way_observable`

Planned primary model:

- `M6_TGQ_factorized_route`

Interpretation:

- The next step is now allowed to run train-only learned smoke for R6.
- Hidden source/rank/`p_geom_valid` and construction probes remain audit-only.
- This smoke plan does not promote any paper-level claim.

## 2026-06-30 R6 Supported-By Smoke Runner

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_runner/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_q_observability_diagnostic
validation_errors = 0
learned_smoke_executed = true
epochs = 5
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_result_review
```

Key metrics:

```text
T1 p_obs M6_TGQ AUROC = 0.978802
T1 p_obs Q-only AUROC = 1.000000
T2 observable p_rel M6_TGQ AUROC = 0.831328
T2 observable p_rel GQ AUROC = 0.905703
T2 observable p_rel Q-only AUROC = 0.880547
T2 observable p_rel best single G_e AUROC = 0.888984
T2 shuffled-G AUROC = 0.540703 / 0.459063
T3 observable p_rel 3-way M6 macro OVR AUROC = 0.773047
hidden construction p_rel AUROC = 1.000000
```

Gate interpretation:

- `p_obs` signal passed; `Q_e` is expected to dominate observability.
- Observable `p_rel` has signal, but `M6_TGQ` does not outperform `G_e + Q_e`.
- `Q_e` alone is too predictive for observable `p_rel`, so this is not clean factorized reliability evidence.
- Shuffled `G_e` controls degrade, so geometry is still involved.
- Hidden construction fields perfectly predict p_rel if leaked; they remain audit-only.

Conclusion:

- R6 `supported by` is useful as a superordinate support decomposition and observability/geometry diagnostic.
- It should not be promoted as a main factorized-route success before result review.

## 2026-06-30 R6 Supported-By Smoke Result Review

Default output:

```text
artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update
selected_path = freeze_supported_by_as_superordinate_decomposition_diagnostic_keep_out_of_main_factorized_success
validation_errors = 0
next_todo = compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review
```

Decision:

- R6 `supported by` is frozen as `superordinate_support` decomposition diagnostic.
- It is not a main factorized-route success because observable `p_rel` is better explained by `G_e + Q_e` and Q-only routes than by the full `T_e + G_e + Q_e` route.
- It remains useful as evidence that broad support labels need accept/relabel/reject/abstain routing.
- `standing on` / `lying on` remain separate support/contact predicate-level compatibility evidence.
- `attached to` / `hanging on` / `connected to` remain queued as observability-first route candidates after route-map update.

## 2026-06-30 Route Map Update After R6 Review

Default output:

```text
artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review/
```

Result:

```text
status = h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready
selected_path = merge_r6_diagnostic_boundary_select_attachment_observability_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_target_plan
```

Route updates:

- R6 `supported by`: frozen as diagnostic broad-label decomposition boundary.
- R5 `standing on` / `lying on`: preserved as separate support/contact compatibility route.
- R7 `attached to` / `hanging on` / `connected to`: selected as the next active observability-first route.
- Main mechanism families remain `relative_vertical`, `size_relative`, `relative_horizontal`, and `support_contact`.
- Diagnostic/control families are `proximity` and `superordinate_support`.

## 2026-06-30 R7 Attachment Observability Target Plan

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_target_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory
selected_path = plan_r7_attachment_observability_first_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_source_inventory
```

Decision:

- R7 `attached to` / `hanging on` / `connected to` is planned as an
  observability-first route.
- `p_obs` must be constructed and audited before `p_rel`.
- `p_rel` is only valid for observable rows; unobservable or topology/functional
  ambiguous rows route to abstain/diagnostic states.
- `attached to` and `hanging on` are primary observability-then-reliability
  predicates.
- `connected to` remains diagnostic until physical/topological/functional
  connection evidence is explicit.
- Previous 560 positive-anchor attachment rows are reused only as source-count,
  packet, and shortcut-risk evidence, not as direct training targets.

Boundary:

- No row materialization in this step.
- No learned smoke in this step.
- Multi-view/mesh evidence remains audit/source-inventory evidence until
  model-safe `G_e`/`Q_e` schemas are materialized.

## 2026-06-30 R7 Attachment Observability Source Inventory

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_source_inventory/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan
selected_path = r7_source_inventory_supports_attached_hanging_materialization_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization_plan
```

Full-train inventory:

- `attached to`: `185,346` candidate rows, `6,190` exact GT matches, `185,346`
  unsupported by the old geometry verifier.
- `hanging on`: `185,346` candidate rows, `939` exact GT matches, `185,346`
  unsupported by the old geometry verifier.
- `connected to`: `185,346` candidate rows, `174` exact GT matches, `185,346`
  unsupported by the old geometry verifier.
- R7 full-train rows cover `1,157` unique scans and `185,346` unique directed
  pairs; all `1,157` scans have multiview, sequence, mesh-ready, and point/mesh
  source files.

Packet reuse inventory:

- Existing R7 packet rows: `560`.
- `attached to`: `238` packet rows, all packet/mesh/multiview/audit ready,
  `46` strong same-frame pair visual rows.
- `hanging on`: `242` packet rows, all packet/mesh/multiview/audit ready,
  `58` strong same-frame pair visual rows.
- `connected to`: `80` packet rows, all packet/mesh/multiview/audit ready,
  but `0` explicit topology/functional-connection source rows.

Decision:

- `attached to` and `hanging on` are ready for an observability materialization
  plan.
- `connected to` stays diagnostic until explicit topology or functional
  connection evidence exists.
- No row materialization or learned smoke was run in this step.

## 2026-06-30 R7 Attachment Observability Materialization Plan

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready
selected_path = plan_primary_attached_hanging_gq_materialization_keep_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization
```

Planned waves:

- W1 primary `attached to` / `hanging on`: `480` rows.
- W2 diagnostic `connected to`: `80` rows.
- W3 full-train expansion: deferred; no rows now.

Materialization contract:

- Write `source_rows.jsonl`, `model_safe_view.jsonl`, `target_manifest.jsonl`,
  `hidden_manifest.jsonl`, `control_manifest.jsonl`, and
  `schema_audit_inputs.json`.
- `T_e`, `G_e_attachment`, `Q_e_observability`, hidden `Z_e`, and targets must
  be separated.
- `p_obs` is materialized before `p_rel`.
- `p_rel_observable` is defined only for observable `attached to` / `hanging on`
  rows.
- `connected to` has no primary `p_rel` target because explicit topology or
  functional-connection source evidence is absent.
- Learned smoke remains blocked until schema shortcut audit.

Risk:

- Observable `p_rel` target has accept/reject `60/246`, so positive sparsity
  remains a risk.
- Prior shortcut-risk flags were `98`; class-pair/query/rank/packet/review
  leakage probes are mandatory before learned claims.

## 2026-06-30 R7 Attachment Observability Materialization

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_materialization/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_r7_gq_separated_source_target_hidden_control_views
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_schema_shortcut_audit
```

Materialized rows:

- Total rows: `560`
- Primary observability route: `attached to 238`, `hanging on 242`
- Diagnostic route: `connected to 80`
- Geometry-available rows: `560/560`
- Model-safe rows: `560`
- Hidden manifest rows: `560`
- Target manifest rows: `560`
- Control manifest rows: `7`

Target snapshot:

- `p_obs_target`: observable/decidable `306`, abstain/not-observable `254`
- `p_rel_observable_target`: accept `60`, reject `246`, not-defined `254`
- `p_rel_observable` is defined only for observable primary `attached to` /
  `hanging on` rows.
- `connected to` remains diagnostic because explicit topology/functional
  connection evidence is absent.

Factor separation:

- `model_safe_view.jsonl` contains only `T_e`, derived `G_e_attachment`, and
  `Q_e_observability` fields.
- `target_manifest.jsonl` owns `p_obs`, observable `p_rel`, and multiclass
  reliability labels.
- `hidden_manifest.jsonl` owns candidate ids, scan/object ids, packet paths,
  source score/rank, review labels, and construction/audit fields.
- Multi-view and mesh are not raw model inputs in this step; only derived
  availability and geometry/observability features are exposed.

Boundary:

- No learned smoke was run.
- No validation/test split was used.
- H001 artifacts were not modified.
- Learned smoke remains blocked until
  `compatibility_dataset_v3_attachment_observability_schema_shortcut_audit`
  verifies that model-safe features do not leak target construction shortcuts.

## 2026-06-30 R7 Attachment Observability Schema Shortcut Audit

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_blocked_shortcut_risk
selected_path = blocked_allowed_model_safe_shortcut_risk
validation_errors = 0
learned_smoke_allowed = false
next_todo = compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit
```

Counts:

- rows: `560`
- `p_obs` rows: `560`, labels `306/254`
- observable `p_rel` rows: `306`, labels `60/246`
- schema leakage hits: `0`
- allowed high-risk blockers: `4`
- allowed medium-risk probes: `45`
- hidden high-risk probes: `5`

Critical blockers:

- `p_obs:T_subject_object_pair` accuracy `0.958929`
- `p_obs:T_predicate_x_class_pair` accuracy `1.000000`
- `p_rel_observable:T_subject_object_pair` accuracy `0.986928`
- `p_rel_observable:T_predicate_x_class_pair` accuracy `1.000000`

Decision:

- The materialized view is schema-clean: hidden ids, source score/rank, packet
  paths, review labels, and targets do not leak into `model_safe_view.jsonl`.
- The target is still shortcut-prone because predicate/class-pair strata nearly
  reconstruct both `p_obs` and observable `p_rel`.
- Do not run learned smoke from this R7 artifact.
- Next step is a path decision: mine class-pair-balanced R7 contrasts, freeze R7
  as diagnostic, or move the next learned target to another route.

## 2026-06-30 R7 Attachment Observability Path Decision

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining
selected_path = attempt_one_class_pair_balanced_r7_repair_before_diagnostic_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan
```

Current artifact repair capacity:

- `p_obs` subject/object-pair mixed groups: `21`, balanced capacity `46`
- `p_obs` exact predicate x subject/object-pair mixed groups: `0`, balanced capacity `0`
- observable `p_rel` subject/object-pair mixed groups: `2`, balanced capacity `8`
- observable `p_rel` exact predicate x subject/object-pair mixed groups: `0`, balanced capacity `0`

Decision:

- Reject learned smoke on the current 560-row R7 artifact.
- Reject dropping object labels from `T_e`; that would hide the problem by
  weakening semantic content.
- Reject repairing only the current 560 rows because exact predicate/class-pair
  mixed capacity is zero.
- Keep `connected to` diagnostic until explicit topology/functional evidence is
  available.
- Select one full-train class-pair-balanced repair mining attempt for
  `attached to` and `hanging on`.
- If repair mining cannot produce mixed exact predicate/class-pair label cells,
  freeze R7 as diagnostic/qualitative observability evidence and move the next
  learned target elsewhere.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Mining Plan

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready
selected_path = plan_exact_predicate_class_pair_capacity_scan_before_packet_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan
```

Decision:

- Do not start candidate mining or packet materialization yet.
- First run a full-train capacity scan over exact
  `predicate_label + subject_label + object_label` cells.
- Use `attached to` and `hanging on` as primary repair predicates.
- Keep `connected to` diagnostic.
- Minimum gates for the next capacity scan:
  - balanced primary rows `>= 400`
  - positive rows `>= 100`
  - exact predicate/class-pair mixed strata `>= 20`

Quota plan:

- `attached to`: request up to `240` packet rows if capacity passes, with
  post-label minimum accept/reject `50/100`.
- `hanging on`: request up to `240` packet rows if capacity passes, with
  post-label minimum accept/reject `50/100`.
- `connected to`: `0` primary packet rows; diagnostic only.

Boundary:

- No labels were filled.
- No rows were materialized.
- No learned smoke was run.
- Capacity/proxy fields remain hidden selection-only and are not model input.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Capacity Scan

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining
selected_path = exact_predicate_class_pair_repair_candidate_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining
```

Exact `predicate_label + subject_label + object_label` capacity:

- mixed groups: `4,616`
- raw balanced rows: `81,724`
- scan-capped balanced rows: `73,636`
- accept/reject/uncertain proxy rows: `79,491 / 257,849 / 33,352`

Per predicate:

- `attached to`: `3,232` mixed groups, `50,662` scan-capped balanced rows
- `hanging on`: `1,384` mixed groups, `22,974` scan-capped balanced rows

Decision:

- The previous 560-row R7 failure was a sampling/packet reuse problem, not a
  full-train capacity problem.
- Proceed to controlled candidate mining for `attached to` and `hanging on`.
- Keep `connected to` diagnostic because explicit topology/functional evidence
  is still missing.
- Do not treat this as learned H002 evidence yet: labels are proxy capacity only,
  and candidate mining must still be followed by packet/label ingestion and
  schema/shortcut audit before any learned smoke.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Candidate Mining

Default output:

```text
artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining/
```

Result:

```text
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan
```

Selected candidates:

- total rows: `480`
- predicates: `attached to 240`, `hanging on 240`, `connected to 0`
- per predicate proxy quota: accept `80`, reject `120`, uncertain `40`
- unique scans: `340`
- unique exact predicate/class-pair groups: `160`
- mixed exact class-pair groups: `attached to 80`, `hanging on 80`

Decision:

- The R7 repair path remains active because controlled candidate mining can
  produce mixed exact-class cells for both primary predicates.
- `connected to` remains diagnostic and is not included in primary packets.
- The next step is packet materialization planning, not label ingestion or
  learned smoke.
- Object-label/anchor priors may still be predictive, so a schema/shortcut audit
  after label ingestion remains mandatory.

## Stage History

Detailed stage history is grouped under:

- `stages/01_foundation_v1_v9.md`
- `stages/02_proximity_v10_v23.md`
- `stages/03_physical_support_v24_v36.md`
- `stages/04_attachment_v37_v66.md`
- `stages/05_hanging_rga_v67_v81.md`

These records explain why the old target-first posterior route was not promoted:
row count was often sufficient, but target independence, class balance, and shortcut
controls repeatedly failed.

## Guardrails

- H002 hypothesis work uses train-only evidence unless explicitly promoted.
- Validation/test must not be used for target construction.
- Hidden construction fields are audit/control only, not model input.
- Multi-view/mesh may be used as observability or hard-relation evidence only after
  provenance and shortcut controls are specified.
- H001 experiment and paper outputs are not modified from this branch.

## 2026-07-01 Route Materialization Protocol Implementation

Docker route materialization을 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight/
status = h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready
selected_path = docker_materialized_promoted_routes_select_materialization_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization
```

Runtime outputs:

- `experiments/H002_compatibility_routing/materialization/latest/route_rows.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/model_safe_view.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/hidden_manifest.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/row_manifest.json`

Materialized promoted route rows:

| Route family | Rows | Label 0 | Label 1 |
| --- | ---: | ---: | ---: |
| `relative_vertical` | 1512 | 756 | 756 |
| `size_relative` | 2400 | 1200 | 1200 |
| `relative_horizontal` | 2400 | 1200 | 1200 |
| `support_contact` | 640 | 320 | 320 |

Boundary: this stage produced row-level route materialization only. It did not run grouped-holdout metrics, official validation/test, or paper-level H002 metrics. `C_e` compatibility remains restricted to `T_e + G_e`; `Q_e` and `Z_e` are stored for later `p_obs` / `p_rel` protocols but blocked from the next compatibility audit.

## 2026-07-01 Materialization Schema Audit

Docker materialization schema audit을 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization/
status = h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_ready
selected_path = schema_audit_passed_select_grouped_split_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit
```

Runtime outputs:

- `experiments/H002_compatibility_routing/schema_audit/latest/audit_manifest.json`
- `experiments/H002_compatibility_routing/schema_audit/latest/schema_violations.jsonl`
- `experiments/H002_compatibility_routing/schema_audit/latest/blocked_field_hits.jsonl`
- `experiments/H002_compatibility_routing/schema_audit/latest/high_shortcut_warnings.jsonl`
- `experiments/H002_compatibility_routing/schema_audit/latest/shortcut_risk_table.csv`
- `experiments/H002_compatibility_routing/schema_audit/latest/split_readiness_table.csv`

Audit result:

- schema errors: `0`
- blocked `C_e` field hits in `T_e + G_e`: `0`
- high-risk `C_e` allowed shortcut warnings: `0`
- shortcut probes: `50`
- split-ready route families: `4/4`

Boundary: this stage is still not a learned metric or paper-level result. It only confirms that the materialized candidate pool is schema-clean and ready for grouped split protocol design.

## 2026-07-01 Grouped Split Protocol

Docker grouped split protocol을 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit/
status = h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready
selected_path = grouped_split_ready_select_grouped_eval_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split
```

Runtime outputs:

- `experiments/H002_compatibility_routing/splits/latest/model_safe_split_view.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/split_assignments.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/group_manifest.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/split_manifest.json`
- `experiments/H002_compatibility_routing/splits/latest/route_split_counts.csv`
- `experiments/H002_compatibility_routing/splits/latest/predicate_split_counts.csv`
- `experiments/H002_compatibility_routing/splits/latest/leakage_audit.csv`
- `experiments/H002_compatibility_routing/splits/latest/validation_errors.jsonl`

Split result:

| Route family | Train rows | Dev rows | Heldout rows |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 1680 | 360 | 360 |
| `relative_vertical` | 1059 | 227 | 226 |
| `size_relative` | 1680 | 360 | 360 |
| `support_contact` | 449 | 97 | 94 |

Audit result:

- input rows: `6952`
- split groups: `3684`
- `cv_group_single_split` violations: `0`
- official validation/test usage: `0`
- validation errors: `0`

Boundary: this stage created only the internal candidate-pool split. It did not run grouped-holdout metrics, official validation/test, or paper-level H002 metrics. The next step is to write the grouped evaluation protocol before any metric run.

## 2026-07-01 Grouped Evaluation Protocol

Grouped evaluation protocol을 작성하고 검증했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
status = h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready
selected_path = grouped_eval_protocol_ready_select_grouped_eval_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_runner_after_protocol
```

Scope:

- target: `C_e`
- train split: `internal_train`
- dev split: `internal_dev`
- heldout split: `internal_heldout`
- rows: `6952`
- main `C_e` input: `T_e + G_e`
- blocked from main `C_e`: `Z_e`, `Q_e`, `extra_safe_blocks`

Required model views:

- `M0_constant`
- `M1_T_semantic_only`
- `M2_G_geometry_only`
- `M3_T_plus_G_concat`
- `M4_TxG_compatibility`
- `C1_wrong_T_control`
- `C2_shuffled_G_control`
- diagnostic-only `D1_Z_source_confidence_diagnostic`
- diagnostic-only `D2_Q_observability_diagnostic`

Boundary: this stage is protocol-only. It did not run grouped metrics, official validation/test, paper-level metrics, or `p_obs` / `p_rel` calibration.

## 2026-07-01 Grouped Evaluation Runner

Docker grouped evaluation runner를 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol/
status = h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready
selected_path = grouped_eval_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_result_review_after_runner
```

Internal heldout overall:

| View | AUROC | Balanced acc | Macro-F1 |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.454321 | 0.473511 | 0.472981 |
| `M2_G_geometry_only` | 0.487690 | 0.487514 | 0.439911 |
| `M3_T_plus_G_concat` | 0.465868 | 0.487921 | 0.487420 |
| `M4_TxG_compatibility` | 0.925990 | 0.819719 | 0.819214 |
| `C1_wrong_T_control` | 0.066622 | 0.177321 | 0.176676 |
| `C2_shuffled_G_control` | 0.500808 | 0.496282 | 0.494069 |

Internal heldout `M4_TxG_compatibility` by family:

| Route family | Rows | AUROC | Interpretation |
| --- | ---: | ---: | --- |
| `relative_horizontal` | 360 | 0.969537 | strong |
| `relative_vertical` | 226 | 0.457834 | failed / review required |
| `size_relative` | 360 | 0.999969 | strong |
| `support_contact` | 94 | 0.616395 | partial / challenging |

Boundary: this stage generated internal candidate-pool metrics, not official validation/test or paper-level results. The next step is a result review before any claim promotion.

## 2026-07-01 Grouped Evaluation Result Review

Grouped evaluation 결과를 family별로 리뷰했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/
status = h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready
selected_path = grouped_review_ready_select_relative_vertical_failure_analysis
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review
```

Family decision:

| Route family | Heldout AUROC | Status | Role |
| --- | ---: | --- | --- |
| `relative_horizontal` | 0.969537 | claim-supporting | main compatibility-route evidence |
| `relative_vertical` | 0.457834 | failed | do not promote without repair |
| `size_relative` | 0.999969 | claim-supporting | main compatibility-route evidence |
| `support_contact` | 0.616395 | partial | challenging compatibility-route evidence |

Interpretation:

- Aggregate `T_e x G_e` signal is strong, but it is not uniformly family-safe.
- `size_relative` and `relative_horizontal` can support the compatibility-route claim.
- `support_contact` should be framed as partial/challenging evidence, not solved.
- `relative_vertical` must be analyzed or repaired before claim lock because wrong-`T_e` and shuffled-`G_e` controls do not establish a usable compatibility signal for the current target.

## 2026-07-01 Relative-Vertical Failure Analysis

Grouped review에서 failed로 표시된 `relative_vertical`의 원인을 분석했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/
status = h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready
selected_path = repair_grouped_eval_compatibility_feature_extractor_then_rerun
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis
```

결론:

- `relative_vertical` 자체가 실패한 것이 아니라 grouped runner의 compatibility feature
  extraction이 잘못됐다.
- Intended feature인 `predicate_sign * raw_geometry_feature_vector.center_delta_z`는
  internal heldout에서 AUROC `1.000000`이다.
- Runner가 suffix로 `center_delta_z`를 찾을 때 실제 raw value가 아니라
  `raw_geometry_feature_available_mask.center_delta_z`를 먼저 잡아 AUROC `0.504808`
  수준의 거의 무의미한 feature가 들어갔다.
- 따라서 다음 작업은 `relative_vertical` 제외가 아니라 grouped runner의 explicit
  raw geometry path repair와 grouped eval rerun이다.

## 2026-07-01 Grouped Eval Feature Extractor Repair

Relative-vertical failure analysis에서 확인한 feature extraction 문제를 수정하고,
Docker grouped evaluation을 다시 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/
status = h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready
selected_path = feature_extractor_repair_ready_select_claim_boundary_review
validation_errors = 0
next_todo = compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

Repair summary:

- `run_grouped_eval.py`의 compatibility feature lookup을 suffix match에서 explicit raw
  geometry path로 변경했다.
- `center_delta_z`는 이제 `G_e_raw.raw_geometry_feature_vector.center_delta_z`를 읽는다.
- Repair probe에서 raw value와 repaired numeric value가 정확히 일치했다.
- `h002-grouped-eval` Docker service를 재실행했고 validation errors는 `0`이다.

Repaired internal heldout:

| Route family | Heldout AUROC | Status |
| --- | ---: | --- |
| `relative_horizontal` | 0.969568 | claim-supporting |
| `relative_vertical` | 0.999921 | claim-supporting |
| `size_relative` | 0.999969 | claim-supporting |
| `support_contact` | 0.610960 | partial/challenging |

Current interpretation:

- `relative_vertical`은 repaired grouped result에서 claim-supporting evidence로 복구됐다.
- 현재 claim-supporting families는 `relative_horizontal`, `relative_vertical`,
  `size_relative`다.
- `support_contact`는 여전히 partial/challenging으로 남긴다.
- 다음 단계는 repaired grouped result 기준의 claim-boundary review다.

## 2026-07-01 Repaired Grouped-Eval Claim Boundary Review

Repaired grouped evaluation 결과를 기준으로 H002의 allowed claim과 blocked claim을
명시적으로 잠갔다.

```text
artifact_root = artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/
status = h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready
selected_path = claim_boundary_locked_select_official_validation_test_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

Allowed hypothesis-stage claim:

- `C_e = compatibility(T_e, G_e)`는 internal grouped holdout에서 semantic-only,
  geometry-only, plain concat, wrong-`T_e`, shuffled-`G_e`보다 강하다.
- relation family마다 필요한 evidence route가 다르며, 하나의 fixed
  semantic-geometry fusion으로 묶으면 안 된다.
- `support_contact`는 partial/challenging route로 남긴다.

Family claim roles:

| Route family | Heldout M4 AUROC | Claim role |
| --- | ---: | --- |
| `relative_horizontal` | 0.969568 | main internal compatibility evidence |
| `relative_vertical` | 0.999921 | main internal compatibility evidence |
| `size_relative` | 0.999969 | main internal compatibility evidence |
| `support_contact` | 0.610960 | partial/challenging evidence |

Blocked claim:

- official validation/test improvement claim.
- calibrated `p_rel` / `p_obs` reliability claim.
- solved `support_contact` claim.
- all-relation-family generalization claim.
- aggregate-only `M4` claim.

다음 단계는 내부 candidate-pool metric을 paper metric으로 승격하는 것이 아니라,
official validation/test protocol을 먼저 정의하는 것이다.

## 2026-07-01 Official Validation/Test Protocol Plan

Claim-boundary review 이후 official validation/test로 넘어가기 위한 protocol plan을
작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/
status = h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready
selected_path = official_protocol_ready_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

정책:

- official validation을 먼저 inventory / metric-freeze 대상으로 사용한다.
- test는 local label file 또는 evaluation server가 확인되고 protocol이 완전히 freeze된
  뒤에만 single final evaluation으로 사용한다.
- 현재 internal grouped metrics는 hypothesis-stage evidence이며 paper metric이 아니다.

Local official split inventory:

| Split | Scans | Relations | Note |
| --- | ---: | ---: | --- |
| `train` | 3852 | 81190 | reference only |
| `validation` | 548 | 11254 | primary official inventory / future metric split |
| `test` | 0 | 0 | local `relationships_test.json` not found |

Promoted family validation capacity:

| Family | Validation count |
| --- | ---: |
| `relative_horizontal` | 5474 |
| `relative_vertical` | 390 |
| `size_relative` | 170 |
| `support_contact` | 1589 |

다음 단계는 official source inventory다. GT relation뿐 아니라 object geometry join,
VL-SAT source candidate, Open3DSG source candidate availability를 확인해야 한다.

## 2026-07-01 Official Source Inventory After Protocol Plan

Official validation/test protocol plan 이후 official validation source inventory를
완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
status = h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready
selected_path = official_source_inventory_ready_select_candidate_materialization_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory
```

GT/object geometry inventory:

| Family | GT relations | Unique scans | OBB pair coverage | Status |
| --- | ---: | ---: | ---: | --- |
| `relative_horizontal` | 5474 | 155 | 1.000000 | candidate_ready |
| `relative_vertical` | 390 | 63 | 1.000000 | candidate_ready |
| `size_relative` | 170 | 35 | 1.000000 | candidate_ready |
| `support_contact` | 1589 | 156 | 1.000000 | candidate_ready |

Source inventory:

- `vlsat_full_validation` and `open3dsg_recovery_relaxed_views_min2` both have
  promoted-predicate candidate rows on official validation.
- H001 geometry verification is checkable for `relative_vertical` and
  `support_contact`.
- H001 geometry verification is unsupported for `relative_horizontal` and
  `size_relative`, so official materialization must build H002-specific `G_e`
  instead of treating H001 `p_geom_valid` as the main evidence.
- `support_contact` remains diagnostic/challenging and must not be described as
  solved.

Boundary:

- no official validation metric,
- no official test usage,
- no paper-level result,
- no calibrated `p_rel` / `p_obs` claim,
- H001 artifacts were used as read-only inventory only.

The next stage is official candidate materialization protocol, not metric
execution.

## 2026-07-01 Official Candidate Materialization Protocol After Source Inventory

Official source inventory 이후 official candidate materialization protocol을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
status = h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready
selected_path = official_candidate_materialization_protocol_ready_select_docker_materializer
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol
```

Protocol decision:

- primary route는 official validation GT 기반 `GT_counterfactual_mechanism`이다.
- source candidates는 VL-SAT / Open3DSG recovery read-only bridge로만 둔다.
- `relative_horizontal`과 `size_relative`은 H001 `p_geom_valid`가 아니라 H002-specific
  `G_e`를 새로 구성해야 한다.
- `relative_vertical`과 `support_contact`의 H001 `p_geom_valid`도 main `G_e`가 아니라
  hidden/diagnostic bridge로만 둔다.
- `source_score`, rank, H001 verification status, construction bucket, GT exact-match
  flag 등은 main `C_e` model-safe features에서 금지한다.
- `p_rel` / `p_obs`는 여전히 blocked다.

Family route contract:

| Route family | GT rows | Role |
| --- | ---: | --- |
| `relative_horizontal` | 5474 | main frame-aware compatibility route |
| `relative_vertical` | 390 | main signed-geometry compatibility route |
| `size_relative` | 170 | main size compatibility route |
| `support_contact` | 1589 | diagnostic/challenging route |

다음 단계는 hypothesis 문서가 아니라 `experiments/H002_compatibility_routing`에서
Docker official materializer를 구현하는 것이다. 이 단계도 metric이 아니라 row
materialization 및 schema validation까지만 수행한다.

## 2026-07-01 Official Candidate Materialization Docker Implementation

Official candidate materialization Docker service를 구현하고 실행했다.

```text
runtime_root = experiments/H002_compatibility_routing/official_materialization/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol/
status = h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready
selected_path = official_materialization_ready_select_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation
```

Docker command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-materialize-candidates
```

Materialized rows:

| File | Rows |
| --- | ---: |
| `candidate_rows.jsonl` | 23062 |
| `model_safe_view.jsonl` | 23062 |
| `hidden_manifest.jsonl` | 23062 |
| `validation_errors.jsonl` | 0 |

Family label counts:

| Route family | Label 0 | Label 1 | Total |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 13290 | 5474 | 18764 |
| `relative_vertical` | 390 | 390 | 780 |
| `size_relative` | 170 | 170 | 340 |
| `support_contact` | 1589 | 1589 | 3178 |

Boundary:

- official validation candidate rows는 materialized 됐다.
- official validation metric은 아직 없다.
- official test는 사용하지 않았다.
- paper-level result는 아직 없다.
- 다음 단계는 schema/shortcut audit이다.

## 2026-07-01 Official Candidate Materialization Schema Audit

Official materialized rows의 schema/shortcut/control-readiness audit을 Docker로 실행하고
stage artifact로 잠갔다.

```text
runtime_root = experiments/H002_compatibility_routing/official_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation/
status = h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats
selected_path = schema_audit_ready_select_official_metric_protocol_freeze
validation_errors = 0
shortcut_warnings = 1
next_todo = compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

Audit result:

- schema violations: `0`
- blocked field hits: `0`
- model-safe/hidden alignment: `23062/23062`, missing `0`
- control readiness blockers: `0`
- high shortcut warnings: `1`

Critical caveat:

- `support_contact` has a high `predicate_x_class_pair` shortcut warning
  (`majority_accuracy = 0.993707`).
- Therefore `support_contact` remains challenging/diagnostic and must not be
  claimed as solved.
- Official metric protocol must report per-family, macro-family, weighted-family,
  and route-control metrics; aggregate alone is not acceptable because
  `relative_horizontal` has dataset weight `0.813633`.

## 2026-07-01 Official Metric Protocol Freeze

Official validation metric을 실행하기 전에 metric, model view, control, aggregation,
and claim boundary를 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
status = h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready
selected_path = official_metric_protocol_frozen_select_official_metric_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_runner_after_protocol_freeze
```

Locked protocol:

- official validation rows are eval-only.
- primary metric is `macro_family_AUROC`.
- weighted-family and overall AUROC are secondary.
- main `C_e` uses `T_e` and `G_e` only.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, and hidden construction fields are excluded from main `C_e`.
- wrong-`T`, shuffled-`G`, subject/object swap, sign flip, and horizontal frame controls are required.
- `support_contact` remains challenging/diagnostic, not solved.

Boundary:

- official metric has still not been computed.
- official test has not been used.
- paper-level result has not been promoted.

## 2026-07-01 Official Metric Runner

Frozen protocol을 따르는 Docker official metric runner를 실행했다.

```text
runtime_root = experiments/H002_compatibility_routing/official_evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
status = h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats
selected_path = official_metric_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_result_review_after_runner
```

Main snapshot:

- `M4_TxG_compatibility` macro-family AUROC: `0.8355465299908279`
- weighted-family AUROC: `0.7207808044279794`
- overall AUROC: `0.724835499373417`
- baselines: `M1_T` macro AUROC `0.41763347769299586`,
  `M2_G` macro AUROC `0.5`, `M3_T+G` macro AUROC `0.4169228221289655`

Family behavior:

- `relative_vertical`: M4 AUROC `0.9913214990138067`
- `size_relative`: M4 AUROC `0.9995847750865052`
- `relative_horizontal`: M4 AUROC `0.7195682002313144`, but frame-control review needed
- `support_contact`: M4 AUROC `0.6317116456316851`, challenging/diagnostic only

Control caveats:

- wrong-`T` and shuffled-`G` controls degrade strongly at macro level.
- horizontal frame swap control has weak margin: delta AUROC `0.03814880004643195`.

Boundary:

- official validation metric has been produced.
- official validation was eval-only.
- official test was not used.
- paper-level result has not been promoted.
- `p_rel` / `p_obs` remain disabled.

## 2026-07-02 Official Metric Result Review

Official validation metric runner 결과를 paper-level experiment gate 관점에서 검토했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
status = h002_compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries
selected_path = official_metric_review_ready_select_claim_boundary_lock
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

Gate decision:

- `paper_level_experiment_execution_gate = passed_with_caveats`
- `paper_result_promotion = not_yet`
- `next_action = claim_boundary_lock`

Family boundary:

- `relative_vertical`: paper candidate main evidence
- `size_relative`: paper candidate main evidence
- `relative_horizontal`: paper candidate with frame-control caveat
- `support_contact`: diagnostic/challenging only

Blocked claims:

- all-relation generalization
- solved support/contact
- strong frame-invariant horizontal claim
- calibrated `p_rel` / `p_obs`
- source reranking / recall tradeoff
- official test result
