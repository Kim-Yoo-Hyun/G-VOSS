# H002 Summary Branch V2

Last updated: 2026-07-01 KST

## Current Title

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## Current Direction

H002는 3D Scene Graph relation source가 내는 단일 confidence score를 그대로
신뢰하지 않고, relation edge의 reliability를 다음 요소로 분해해 학습하고 검증하는
연구 방향이다.

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = predicate-geometry compatibility
Q_e = evidence quality / observability
R_e = final relation reliability decision
```

핵심 주장은 다음과 같다.

```text
relation source confidence is not relation reliability.
relation reliability requires semantic content, source confidence,
geometry evidence, semantic-geometry compatibility, and observability quality
to be separated before final decision.
```

이제 H002의 main method candidate는 단순한 posterior smoke가 아니라
`Predicate-Geometry Compatibility Learning for Factorized Relation Reliability`다.

## Why H002 Pivoted

기존 H002는 다음 명제를 중심으로 진행됐다.

```text
semantic score != geometry validity != relation reliability
```

초기 계획은 human/audit reliability target을 만들고,

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

형태의 factorized posterior가 `semantic_only`, `geometry_only`,
`semantic + geometry`보다 relation reliability를 잘 설명하는지 확인하는 것이었다.

그러나 v1-v81 단계에서 반복적으로 다음 병목이 확인됐다.

- binary accept/reject target이 positive-sparse하게 형성됐다.
- predicate, rank band, endpoint pair, object family, construction metadata가 label을
  쉽게 설명하는 shortcut risk가 컸다.
- target을 더 강하게 통제하면 mixed positive/negative strata 자체가 부족해졌다.
- `attached to`, `hanging on`, `connected to` 계열은 OBB/metric geometry만으로
  reliability label을 독립적으로 만들기 어려웠다.
- RGA benchmark와 failure taxonomy는 diagnostic으로는 유용하지만, 그 자체만으로
  top-tier method novelty를 만들기에는 약하다.

따라서 결론은 H002 가설이 틀렸다는 것이 아니라, **독립 reliability label을 먼저
만든 뒤 posterior를 학습한다는 route가 현재 artifact에서는 main method claim으로
충분하지 않다**는 것이다.

## New H002 Method

새 방향은 reliability target을 먼저 강하게 만드는 대신, relation reliability를
구성하는 evidence representation 자체를 더 명확하게 만든다.

```text
Geometry-only evidence encoder -> G_e
Semantic-content encoder -> T_e
Source-confidence encoder -> Z_e
Compatibility head, using T_e and G_e only -> C_e
Evidence-quality head -> Q_e
Two-head decision -> p_obs, p_rel
```

### 1. Semantic Content `T_e`

입력:

- predicate text or label
- relation family
- subject/object class
- optional class text embedding or ontology group

역할:

```text
T_e = what relation is being claimed
```

`T_e`는 predicate와 object semantics를 표현한다. Source score, rank, source id는
`T_e`에 넣지 않는다.

### 2. Source Confidence `Z_e`

입력:

- source relation score
- semantic rank
- source id
- source-specific calibration metadata, if available

역할:

```text
Z_e = how strongly the existing source believes the candidate
```

`Z_e`는 final reliability에서 source confidence를 반영하는 별도 factor다.
`C_e` 계산에는 넣지 않는다. 이 분리가 없으면 compatibility head가 기존 source score를
복사하는 shortcut을 배울 수 있다.

### 3. Geometry-Only Evidence `G_e`

입력:

- subject/object/pair point or mesh feature
- distance, height difference, overlap, contact, containment
- visibility-independent object-pair geometry feature
- relation-family-agnostic metric geometry vector

출력:

```text
G_e = predicate-independent geometry evidence representation
```

중요한 원칙:

- predicate text, source score, rank는 geometry encoder에 넣지 않는다.
- `G_e`는 scalar 하나가 아니라 vector 또는 token set으로 둔다.
- H001의 `p_geom_valid`는 rule-based geometry evidence baseline 또는 teacher signal로
  재사용할 수 있지만, main `G_e` input으로 직접 넣어 source/label shortcut을 만들지 않는다.

### 4. Predicate-Geometry Compatibility `C_e`

입력:

```text
T_e, G_e
```

출력:

```text
C_e = compatibility(T_e, G_e)
```

금지:

```text
C_e must not use Z_e.
```

이 head의 목적은 relation source score를 다시 예측하는 것이 아니라, predicate가 요구하는
geometry evidence와 실제 object-pair geometry가 호환되는지 학습하는 것이다.

### 5. Evidence Quality / Observability `Q_e`

입력:

- view availability
- same-frame visibility
- mesh completeness
- point coverage
- evidence agreement or conflict
- missing / unsupported state

출력:

```text
Q_e = evidence quality / observability representation
```

기존 H002의 `coverage`와 `uncertainty`는 이제 별도 main factors가 아니라 `Q_e`
안에서 함께 다룬다. `Q_e`는 relation의 참/거짓을 직접 결정하지 않고, 현재 evidence로
판단 가능한지와 abstain해야 하는지를 결정한다.

## Reliability And Abstain Decision

H002는 reliability와 abstain을 하나의 posterior로 직접 섞지 않는다. 두 head로 나눈다.

```text
p_obs = P(evidence is sufficient to decide | Q_e, optional geometry-quality fields)
p_rel = P(relation is reliable | evidence is observable, Z_e, C_e, optional T_e)
```

최종 결정:

```text
if p_obs < tau_obs:
  decision = abstain
elif p_rel >= tau_rel:
  decision = accept
else:
  decision = reject
```

이 구조에서 `Q_e`는 reject를 직접 만드는 factor가 아니라, 판단 가능성과 abstain을
담당한다.

## Factorized Energy

기존 `E_geom(G_e)`는 역할이 애매했으므로 축소한다. Predicate를 모르는 geometry 자체만으로
`close by`, `higher than`, `attached to`의 성립 여부를 결정할 수 없기 때문이다.

기본 energy:

```text
E_rel(e)
 = E_src(Z_e)
 + E_comp(C_e)
 + E_interaction(Z_e, C_e, T_e)

p_rel = sigmoid(-E_rel(e))
```

선택적 geometry-quality penalty:

```text
E_geom_quality(G_e)
```

이 term은 point cloud 누락, mesh artifact, impossible overlap 같은 geometry 자체의
품질/아티팩트에만 사용한다. Predicate와 geometry의 relation-specific 정합성은
`E_comp(C_e)`가 담당한다.

Observability head:

```text
p_obs = f_obs(Q_e, optional E_geom_quality)
```

## Contrastive Learning Policy

Contrastive positive를 source candidate 전체로 두면 source 오류를 그대로 학습한다.
따라서 positive는 다음 중 하나로 제한한다.

- official GT relation
- human/audit accept relation
- high-precision rule-verified subset
- cross-source agreement plus geometry-supported subset

Negative는 no-GT row 전체가 아니다. 3DSSG/Open3DSG 계열은 annotation incompleteness가
있으므로 `no GT = negative`라고 두지 않는다.

허용 negative:

- wrong-pair geometry
- shuffled geometry
- predicate flip within the same family
- subject/object swap
- same-scene negative
- same-family hard negative
- same-rank-band hard negative
- same-coverage hard negative
- relation-specific perturbation such as contact removal or vertical-order flip

## Role Of RGA

RGA는 이제 main method가 아니라 evaluation/diagnostic framework다.

RGA가 하는 일:

- semantic axis와 geometry axis의 mismatch를 측정한다.
- high-semantic/low-geometry와 low-semantic/high-geometry를 모두 기록한다.
- geometry evidence가 relation family별로 어디에서 실패하는지 taxonomy를 만든다.
- model이 geometry shortcut, predicate shortcut, rank shortcut을 쓰는지 control한다.
- final paper에서 recall/violation/reliability tradeoff를 설명하는 diagnostic table을 제공한다.

RGA가 하지 않는 일:

- RGA bucket 자체를 final reliability label로 쓰지 않는다.
- `p_geom_valid`를 relation reliability로 이름만 바꿔 쓰지 않는다.
- human/audit label 없이 posterior success를 주장하지 않는다.

## Evaluation Plan

### Main Metrics

- official GT relation Recall@K or mAP
- Geometry Violation@K
- semantic-geometry counterfactual sensitivity
- source transfer across VL-SAT and Open3DSG-style relation sources
- selective reliability under abstain
- calibration: ECE, Brier, AUPRC where target is valid

### Baselines

- source confidence only: `Z_e`
- semantic content + source confidence: `T_e + Z_e`
- geometry-only rule score, including H001 `p_geom_valid`
- `semantic_score * p_geom_valid`
- concat MLP over `T_e, Z_e, G_e, Q_e`
- compatibility-only: `C_e`
- reliability without `Q_e`
- full model: `T_e + Z_e + G_e + C_e + Q_e` with two-head decision

### Controls

- wrong-pair geometry
- shuffled geometry
- predicate flip
- subject/object swap
- source score/rank shuffle
- same-family hard negative
- same-rank-band hard negative
- same-coverage hard negative
- no-view / low-coverage / incomplete-mesh rows

## Relation Scope

Initial families:

- `proximity`: `close by`
- `relative_vertical`: `higher than`, `lower than`
- `support_contact`: `standing on`, `lying on`, `supported by`
- `attachment_deferred`: `attached to`, `hanging on`, `connected to`

Deferred expansion:

- `relative_horizontal`: `left`, `right`, `front`, `behind`
- `containment`: `inside`, `surrounding`
- open-vocabulary fallback predicates

## Stage History

H002의 v1-v81 기록은 posterior-target route의 failure analysis로 보존한다. 개별 stage
로그는 다음 병합 문서가 소유한다.

| Stage Range | Stage File | Main Finding |
| --- | --- | --- |
| v1-v9 | `stages/01_foundation_v1_v9.md` | 초기 RGA/posterior target은 endpoint, predicate, rank shortcut에 취약했다. |
| v10-v23 | `stages/02_proximity_v10_v23.md` | `close by`는 generality에는 중요하지만 current queue에서는 LH-only branch였다. |
| v24-v36 | `stages/03_physical_support_v24_v36.md` | support/contact와 relative vertical은 수량은 충분했지만 geometry-status shortcut이 강했다. |
| v37-v66 | `stages/04_attachment_v37_v66.md` | attachment 계열은 metric geometry만으로 독립 reliability target을 만들기 어려웠다. |
| v67-v81 | `stages/05_hanging_rga_v67_v81.md` | `hanging on` positive-anchor route도 positive-sparse와 matched-cell diversity blocker에 막혔다. |

이 기록의 의미는 “H002가 실패했다”가 아니라, final method가 단순 posterior target fitting이
아니라 geometry evidence representation과 compatibility learning으로 이동해야 한다는 근거다.

## Current TODO

Completed in this step:

```text
method_contract_v1
geometry_evidence_schema_v1
counterfactual_protocol_v1
prototype_dataset_contract_v1
smoke_baseline_plan_v1
prototype_dataset_materialization_v1
smoke_baseline_runner_v1
learned_smoke_runner_v1
attachment_numeric_geometry_materialization_v1
attachment_numeric_geometry_smoke_v1
attachment_smoke_path_decision_v1
attachment_shortcut_controlled_smoke_v1
attachment_controlled_expansion_plan_v1
attachment_controlled_candidate_materialization_v1
attachment_controlled_candidate_smoke_v1
attachment_controlled_candidate_path_decision_v1
attachment_independent_audit_subset_plan_v1
attachment_independent_audit_label_fill_v1
attachment_independent_audit_label_ingestion_v1
attachment_independent_target_independence_audit_v1
attachment_independent_target_repair_plan_v1
attachment_independent_positive_anchor_mining_plan_v1
attachment_independent_positive_anchor_candidate_mining_v1
attachment_independent_positive_anchor_packet_materialization_v1
attachment_independent_positive_anchor_label_fill_v1
attachment_independent_positive_anchor_label_ingestion_v1
attachment_independent_positive_anchor_target_independence_audit_v1
attachment_independent_positive_anchor_path_decision_after_audit_v1
compatibility_learning_scope_plan_v1
compatibility_dataset_v2_contract
compatibility_dataset_v2_materialization_plan
compatibility_dataset_v2_capacity_scan
compatibility_dataset_v2_candidate_materialization
```

Next TODO:

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```

Immediate purpose:

```text
materialize separate G_e point/mesh/contact/pose evidence and Q_e observability fields
emit model-safe/source/visual-audit/control manifests and feature statistics
keep multiview learned input blocked and validate wrong-view/shuffled-view controls as contracts
keep supported by diagnostic-only until subtype boundary is clearer
```

Current materialized dataset:

```text
artifact_root = artifacts/prototype_dataset_v1/
prototype_rows = 694
counterfactual_groups = 67
compatibility positive / negative / unknown = 67 / 67 / 560
reliability accept / reject / abstain = 101 / 442 / 151
validation_errors = 0
```

This dataset has now been consumed by both deterministic and learned smoke runners. It remains
the current train-only prototype source until attachment numeric `G_e` is materialized.

Current deterministic smoke result:

```text
artifact_root = artifacts/smoke_baseline_v1/
Task A compatibility rows = 134
source-only AUROC = 0.5008
semantic_score * p_geom_valid AUROC = 0.5317
generic geometry proxy AUROC = 0.6298
relation-conditioned geometry proxy AUROC = 0.6681
mean paired compatibility drop = 0.1411
Task B p_obs proxy macro-F1 = 0.7824
Task C full proxy macro-F1 = 0.3302
validation_errors = 0
overall = ready_for_learned_smoke
```

Interpretation:

- first smoke supports the claim that source confidence alone does not explain the compatibility
  target;
- geometry-derived signal is present, especially in `support_contact`;
- `relative_vertical` and predicate shortcut controls remain blockers for a learned method claim;
- deterministic smoke justified the learned train-internal smoke, which is now complete.

Current learned smoke result:

```text
artifact_root = artifacts/learned_smoke_v1/
Task A compatibility rows = 134
M1 source-only Z AUROC = 0.4885
M2 semantic+source T+Z AUROC = 0.9668
M3 p_geom_valid AUROC = 0.5507
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

- `C_e = compatibility(T_e, G_e)` is strongly better than source-only, rule-only
  `p_geom_valid`, geometry-only, and predicate/family shortcut probes in the current
  train-internal grouped-fold smoke.
- `M2 semantic+source T+Z` is also very strong, so this is not yet paper-ready evidence that the
  model has learned only principled compatibility.
- The next bottleneck is coverage of harder relation families. `attachment_deferred` needs numeric
  geometry evidence before a stronger neural/posterior combiner is meaningful.

Current attachment numeric geometry result:

```text
artifact_root = artifacts/attachment_numeric_geometry_v1/
rows = 240
numeric_g_rows = 240
attached to / hanging on / connected to = 82 / 96 / 62
compatibility positive / negative / unknown = 33 / 81 / 126
counterfactual_groups = 33
validation_errors = 0
artifact_next_at_creation = attachment_numeric_geometry_smoke_v1
```

Interpretation:

- attachment `G_e` now contains numeric distance, overlap, vertical, near-contact, and derived
  closeness/overlap features extracted from the locked v18 raw geometry block;
- source score/rank, machine hint, cell id, geometry status, witness score, and label fields are
  excluded from `G_e`;
- `attached to` and `hanging on` are smoke-ready under a binary geometry-support target, but class
  balance remains `33/81`;
- `connected to` is retained as diagnostic because current rows do not provide balanced physical
  compatibility labels.

Current attachment numeric geometry smoke result:

```text
artifact_root = artifacts/attachment_numeric_geometry_smoke_v1/
Task A compatibility rows = 114
positive / negative = 33 / 81
source-only Z AUROC = 0.4635
semantic+source T+Z AUROC = 0.8148
geometry-only G AUROC = 0.8949
compatibility T+G AUROC = 0.9282
factorized T+Z+G+Q AUROC = 0.9364
predicate/family shortcut AUROC = 0.5305
hidden construction probe AUROC = 0.8767
hidden witness score probe AUROC = 0.8010
connected diagnostic T+G AUROC = 0.9265
validation_errors = 0
overall = attachment_smoke_promising_but_requires_hidden_shortcut_review
```

Interpretation:

- attachment numeric `G_e` carries meaningful signal beyond source-only and predicate/family
  shortcuts;
- `T_e + G_e` improves over geometry-only for both `attached to` and `hanging on`;
- hidden construction probes are still high, so the next step must decide whether to repair the
  target/control design before merging attachment into the combined H002 prototype.

Current attachment path decision:

```text
decision = do_not_promote_attachment_to_combined_main_yet
selected_next = attachment_shortcut_controlled_smoke_v1
attachment_status = promising_diagnostic_extension_requiring_shortcut_control
```

Reason:

- attachment numeric `G_e` is useful, but target construction is still visible through hidden
  construction probes;
- hidden construction AUROC is `0.8767`, close enough to `T+G` AUROC `0.9282` to require control;
- cell distribution is imbalanced: A1 `8/10`, A2 `3/27`, H1 `21/5`, H2 `1/26`, U1 `0/13`;
- the next controlled slice should downsample within hidden cells to a balanced preview of about
  `34` rows before any combined-prototype promotion.

Current attachment shortcut-controlled smoke result:

```text
artifact_root = artifacts/attachment_shortcut_controlled_smoke_v1/
Task A controlled compatibility rows = 34
positive / negative = 17 / 17
pair groups = 17
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

- strict within-cell balancing removed the hidden construction shortcut seen in the previous
  attachment smoke;
- `T_e + G_e` still remains strong, so attachment should not be discarded;
- the slice is too small for paper evidence, so the next step is a larger controlled attachment
  mining plan rather than direct combined-prototype promotion.

Current attachment controlled expansion plan:

```text
artifact_root = artifacts/attachment_controlled_expansion_plan_v1/
selected_route = v20_endpoint_balanced_preview_400_repackage_with_numeric_geometry_join
target_rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 40 near/overlap diagnostic + 40 far/ambiguous diagnostic
validation_errors = 0
next = attachment_controlled_candidate_materialization_v1
```

Interpretation:

- v20 full-train endpoint-balanced capacity provides the best next expansion route;
- v21 strict same-predicate/rank/geometry/family route remains blocked by predicate imbalance;
- v22 `hanging on` strict route is useful diagnostic evidence but too narrow for attachment-family
  generality;
- `connected to` remains diagnostic until visual/mesh evidence can support functional connection;
- the v20 `400`-row preview has already been repackaged into the current H002 schema and consumed
  by the controlled candidate smoke.

Current attachment controlled candidate materialization:

```text
artifact_root = artifacts/attachment_controlled_candidates_v1/
rows = 400
primary_binary_rows = 320
diagnostic_connected_rows = 80
numeric_g_rows = 400
selected_prediction_matches = 400
pair_geometry_matches = 400
groups = 131
validation_errors = 0
next_at_completion = attachment_controlled_candidate_smoke_v1
```

Predicate and compatibility counts:

```text
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 80 unknown diagnostic rows
connected diagnostic tiers = 40 near/overlap + 40 far/ambiguous
```

Interpretation:

- the v20 `400`-row preview is now available in the current H002 `T_e/Z_e/G_e/Q_e` schema;
- attachment predicate rows themselves have unsupported verifier geometry, so the materializer joins
  same-directed-pair raw pair geometry from support/vertical geometry rows;
- all `400` selected pairs joined successfully, and the selected raw `G_e` source is
  `support_contact`;
- this is train-only hypothesis evidence; the follow-up controlled smoke is now complete.

Current attachment controlled candidate smoke:

```text
artifact_root = artifacts/attachment_controlled_candidate_smoke_v1/
Task A primary compatibility rows = 320
positive / negative = 160 / 160
connected diagnostic rows = 80
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
next = attachment_controlled_candidate_path_decision_v1
```

Interpretation:

- `G_e`, `T+G`, and `T+Z+G+Q` perfectly recover the current attachment proxy target;
- visible shortcut probes from predicate/family, source-rank, and endpoint-label-pair stay near
  chance, so source confidence and endpoint semantics do not explain this target;
- hidden construction probes are also perfect, so the target is still a geometry-proxy construction
  target rather than independent relation reliability evidence;
- use this result for path decision only, not direct paper promotion.

Current attachment controlled candidate path decision:

```text
decision = do_not_promote_400_row_attachment_proxy_labels
attachment_400_proxy_status = compatibility_proxy_pretraining_only
attachment_feature_schema_status = keep
attachment_proxy_label_status = do_not_use_as_paper_reliability_target
attachment_paper_evidence_status = not_promoted
selected_next = attachment_independent_audit_subset_plan_v1
```

Reason:

- the current proxy target is useful for testing whether `G_e` carries pair-geometry signal, but it
  is not an independent reliability target;
- hidden cell/construction probes reach AUROC `1.0000`, so more model capacity or a stronger
  combiner would solve the wrong bottleneck;
- attachment should not be discarded because visible shortcut probes are near chance and numeric
  `G_e` works well;
- the next principled step is to create a train-only visual/mesh/human-audited subset where labels
  are assigned from independent evidence rather than copied from proxy construction.

Current attachment independent audit subset plan:

```text
artifact_root = artifacts/attachment_independent_audit_subset_plan_v1/
selected_route = reuse_v20_packet_assets_with_blank_h002_independent_review_template
current_candidate_rows = 400
v20_packet_matched_rows = 298
selected_rows = 200
primary_rows = 160
connected_diagnostic_rows = 40
attached to = 80
hanging on = 80
connected to = 40 diagnostic
proxy positive / counterfactual negative / unknown = 80 / 80 / 40
T1_strong_pair_visual = 72
T2_individual_visual_plus_mesh = 128
validation_errors = 0
next = attachment_independent_audit_label_fill_v1
```

Interpretation:

- this plan reuses existing visual/mesh packet assets, not old proxy labels;
- the visible review template has blank label fields, so the next label fill can create an
  independent audit target;
- prior v20 labels are kept only in the hidden manifest for later provenance checks;
- this is the first attachment step after the pivot that directly attacks target independence.

Current attachment independent audit label fill:

```text
artifact_root = artifacts/attachment_independent_audit_label_fill_v1/
label_source = codex_visible_packet_label_v1
rows = 200
accept_reliable = 17
reject_unreliable = 91
abstain_uncertain = 92
primary_binary_preview = 17 accept / 91 reject
validation_errors = 0
next = attachment_independent_audit_label_ingestion_v1
```

Predicate-level distribution:

```text
attached to = 2 accept / 53 reject / 25 abstain
hanging on = 15 accept / 38 reject / 27 abstain
connected to = 40 abstain diagnostic
```

Interpretation:

- the independent label fill is positive-sparse, especially for `attached to`;
- this sparsity is not corrected by hand because it is evidence about the hard-relation target;
- the next gate is ingestion and target viability/shortcut audit, not posterior training.

Current attachment independent audit label ingestion:

```text
artifact_root = artifacts/attachment_independent_audit_label_ingestion_v1/
status = h002_attachment_independent_audit_label_ingested_positive_sparse_with_shortcut_risk
rows = 200
primary_binary_rows = 108
primary_binary_target = 17 positive / 91 negative
p_obs_target = 108 observable / 92 abstain-or-unobservable
validation_errors = 0
next = attachment_independent_target_independence_audit_v1
```

Shortcut / viability:

```text
minimum_positive_for_posterior_smoke = 30
primary_positive_rows = 17
primary_negative_rows = 91
class_mass_pass = false
model_shortcut_probe_risk_flags = 60
construction_proxy_probe_risk_flags = 19
label_derived_probe_risk_flags = 21
```

Interpretation:

- the new H002 factor-view materialization succeeded: `T_e`, diagnostic-only `Z_e`, `G_e`,
  `Q_e`, `C_e`/compatibility target, `p_obs`, and `p_rel` targets were emitted;
- the target remains useful as an independent diagnostic subset, but not yet as a posterior
  training/smoke target because the positive class has only 17 rows;
- hidden construction/source fields must be audited before any learned posterior smoke.

Current attachment independent target-independence audit:

```text
artifact_root = artifacts/attachment_independent_target_independence_audit_v1/
status = h002_attachment_independent_target_independence_audit_blocked_primary_positive_sparse
rows = 200
p_rel_primary_binary = 91 negative / 17 positive
c_e_compatibility_binary = 91 negative / 17 positive
p_obs_primary_binary = 108 observable / 52 abstain-or-unobservable
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
validation_errors = 0
next = attachment_independent_target_repair_plan_v1
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

- current primary `p_rel/C_e` target is not ready for posterior smoke;
- the bottleneck is target identifiability and positive sparsity, not the factorized combiner;
- the next step should repair the independent target definition/mining policy before adding model
  capacity.

Current attachment independent target repair plan:

```text
artifact_root = artifacts/attachment_independent_target_repair_plan_v1/
status = h002_attachment_independent_target_repair_plan_v1_ready
selected_route = new_positive_anchor_mining_with_packet_materialization
current_200 positive / negative = 17 / 91
all_v20_matched_298 positive / negative = 24 / 116
full_candidate_400 visible-rule positive / negative = 45 / 174
mixed_visible_pair_groups = 1
mixed_predicate_visible_pair_groups = 0
validation_errors = 0
next = attachment_independent_positive_anchor_mining_plan_v1
```

Interpretation:

- using the current rows or all existing v20-matched packet rows is insufficient;
- materializing the unmatched 102 rows would be diagnostic-only because predicate-visible-pair
  contrast remains absent;
- the selected repair is new positive-anchor mining with packet materialization and matched hard
  negatives.

Current attachment independent positive-anchor mining plan:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_mining_plan_v1/
status = h002_attachment_independent_positive_anchor_mining_plan_v1_ready
selected_route = train_only_positive_anchor_candidate_mining_then_packet_materialization
target_rows_before_audit = 560
primary_requested_rows_before_audit = 480
post_audit_min_accept_positive = 60
post_audit_min_reject_negative = 60
validation_errors = 0
next = attachment_independent_positive_anchor_candidate_mining_v1
```

Interpretation:

- next step is candidate mining, not posterior smoke;
- `hanging on` is the strongest primary positive-anchor route and requires at least 40 audit-accepted
  positives after packet review;
- `attached to` is promoted to primary only if at least 30 independent accepted positives survive;
- `connected to` remains diagnostic because functional connection evidence is not yet reliable;
- the key control is mixed endpoint-family/rank/coverage strata, not raw row count.

Current attachment independent positive-anchor candidate mining:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_candidate_mining_v1/
status = h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata
selected_rows = 560
primary_binary_selected = 467
primary_uncertain_buffer_selected = 13
diagnostic_selected = 80
complete_positive_negative_contrast_pairs = 143
validation_errors = 0
next = attachment_independent_positive_anchor_packet_materialization_v1
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

Mixed-strata result:

```text
endpoint_family_rank_coverage mixed groups = 55
endpoint_family_rank mixed groups = 61
visible_pair mixed groups = 58
rank_band mixed groups = 7
same_scene mixed groups = 40
same_scene_endpoint_family_rank mixed groups = 11
```

Interpretation:

- positive anchor mining is not treated as positive-only collection;
- source score/rank are hidden and are not selection scores;
- rank band, visible pair, endpoint family, and same-scene axes are used as contrast/control axes;
- `13` uncertain buffer rows are not binary target rows and must be handled separately after packet
  audit;
- posterior smoke remains blocked until label fill, ingestion, and target-independence audit pass.

Current attachment independent positive-anchor packet materialization:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_packet_materialization_v1/
status = h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill
packet_rows = 560
packet_status_counts = ready: 560
label_ready_rows = 560
non_ready_rows = 0
subject_image_rows = 560 / 560
object_image_rows = 560 / 560
contact_sheet_rows = 560 / 560
mesh_packet_rows = 560 / 560
visible_leakage_hits = 0
validation_errors = 0
next = attachment_independent_positive_anchor_label_fill_v1
```

Interpretation:

- all selected mixed-strata attachment candidates now have reviewer-facing visual/mesh packets;
- source score/rank, construction proxy, cell id, GT-match, scan id, and object ids remain hidden
  from label-facing surfaces;
- multi-view/mesh remains audit evidence only and is not a deployable model input at this stage;
- the next step is independent accept/reject/abstain label fill, followed by ingestion and
  target-independence audit before any posterior smoke.

Current attachment independent positive-anchor label fill:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_label_fill_v1/
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
next = attachment_independent_positive_anchor_label_ingestion_v1
```

Predicate-level distribution:

```text
attached to = 30 accept / 95 reject / 113 abstain
hanging on = 30 accept / 151 reject / 61 abstain
connected to = 80 abstain diagnostic
```

Interpretation:

- positive-anchor repair reached the pre-specified minimum positive gate exactly;
- this improves the previous independent attachment target from `17` positives to `60` primary
  positives, but the target is still not cleared for posterior smoke;
- the next gate is ingestion plus target-independence audit against hidden/control provenance,
  especially predicate, endpoint, rank, packet construction, and mixed-strata axes.

Current attachment independent positive-anchor label ingestion:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_label_ingestion_v1/
status = h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk
rows = 560
primary_binary_rows = 306
primary_positive_rows = 60
primary_negative_rows = 246
p_obs_rows = 560
p_obs_target = 306 observable / 254 abstain-or-unobservable
compatibility_binary_rows = 306
p_rel_rows = 306
geometry_support_rows = 306
evidence_quality_rows = 560
connected_diagnostic_rows = 80
validation_errors = 0
next = attachment_independent_positive_anchor_target_independence_audit_v1
```

Shortcut / viability summary:

```text
class_mass_pass = true
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

- positive-anchor repair solved the immediate class-mass blocker;
- target identifiability is still unresolved because visible endpoint semantics and hidden
  construction axes remain predictive;
- posterior smoke is still blocked. The next step is formal target-independence audit and
  controlled-slice selection.

Current attachment independent positive-anchor target-independence audit:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/
status = h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk
rows = 560
p_rel_primary_binary = 306 rows, 60 positive / 246 negative
c_e_compatibility_binary = 306 rows, 60 positive / 246 negative
p_obs_primary_binary = 480 rows, 306 observable / 174 unobservable-or-abstain
geometry_support_binary = 306 rows, 60 supported / 246 unsupported
full_risk_flags = 112
p_rel_class_mass_pass = true
p_rel_strict_clear_slice_count = 0
p_rel_diagnostic_clear_slice_count = 0
validation_errors = 0
next = attachment_independent_positive_anchor_path_decision_after_audit_v1
```

Interpretation:

- class mass is now sufficient for a diagnostic smoke in principle;
- no strict or diagnostic controlled slice cleared shortcut risk, so the target is not yet
  identifiable as independent reliability evidence;
- the next step must choose a path after audit rather than run posterior smoke.

Current attachment independent positive-anchor path decision:

```text
artifact_root = artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1/
status = h002_attachment_independent_positive_anchor_path_decision_diagnostic_freeze
selected_path = freeze_positive_anchor_target_as_diagnostic_and_move_to_compatibility_learning_plan
posterior_smoke_allowed = false
validation_errors = 0
next = compatibility_learning_scope_plan_v1
```

Decision summary:

- attachment positive-anchor target is frozen as diagnostic-only;
- posterior smoke remains blocked;
- more same-policy positive-anchor mining is rejected because class mass is no longer the main
  blocker;
- label relaxation is rejected because it would tune the target to fit the model;
- attachment packets remain useful for `Q_e`, observability, hard-family failure taxonomy, and
  future verified positives;
- the next H002 step is method-level compatibility learning scope definition.

Current compatibility learning scope plan:

```text
artifact_root = artifacts/compatibility_learning_scope_plan_v1/
status = h002_compatibility_learning_scope_plan_ready
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next = compatibility_dataset_v2_contract
```

Selected family scope:

```text
primary_v1 = support_contact, relative_vertical
diagnostic_hard_family = attachment_like
future_generality = proximity
deferred = relative_horizontal, containment
```

Current counts:

```text
support_contact = 99 rows, compatibility 50 positive / 49 counterfactual negative
relative_vertical = 35 rows, compatibility 17 positive / 18 counterfactual negative
attachment_deferred = 560 rows, diagnostic-only
```

Interpretation:

- H002 no longer tries to prove the full method from the attachment positive-anchor reliability
  target;
- the v1 method scope should be built around compatibility learning on support/contact and
  relative vertical relations;
- attachment remains useful as a hard-family observability and failure-analysis branch;
- the next step is a v2 dataset contract for this selected scope.

Current compatibility dataset v2 contract:

```text
artifact_root = artifacts/compatibility_dataset_v2_contract/
status = h002_compatibility_dataset_v2_contract_ready
dataset_name = h002_compatibility_dataset_v2
selected_scope = primary_support_contact_relative_vertical_attachment_diagnostic
posterior_smoke_allowed = false
validation_errors = 0
next = compatibility_dataset_v2_materialization_plan
```

Dataset contract:

```text
primary = support_contact, relative_vertical
diagnostic = attachment_like
future = proximity
deferred = relative_horizontal, containment
```

Minimum materialization/requested class mass:

```text
support_contact requested 120/120, minimum reportable 60/60
relative_vertical requested 80/80, minimum reportable 60/60
overall primary Task A minimum 120/120
```

Interpretation:

- v2 no longer treats attachment labels as a primary `p_rel/C_e` target;
- v2 must expand relative vertical and preserve directional flip/swap controls;
- `C_e` is strictly `T_e + G_e`; `Z_e` is excluded from compatibility input;
- the next step is source/capacity inspection before materialization.

Current compatibility dataset v2 materialization plan:

```text
artifact_root = artifacts/compatibility_dataset_v2_materialization_plan/
status = h002_compatibility_dataset_v2_materialization_plan_ready
selected_route = v2_capacity_scan_before_materialization
direct_materialization_allowed = false
posterior_smoke_allowed = false
validation_errors = 0
next = compatibility_dataset_v2_capacity_scan
```

Current source check:

```text
prototype_v1 support_contact = 50/49
prototype_v1 relative_vertical = 17/18
all-label-ready reliability support_contact = 50/121
all-label-ready reliability relative_vertical = 20/40
v2 minimum reportable per primary family = 60/60
```

Interpretation:

- existing prototype/all-label-ready rows are useful seeds but cannot be promoted directly to
  `h002_compatibility_dataset_v2`;
- raw-witness feature join v2 is the best geometry feature adapter seed, but it must be repackaged
  from posterior-ready `baseline_inputs` into explicit `T_e/Z_e/G_e/Q_e` factor blocks;
- full-train capacity exists, so the correct next step is a v2-specific capacity scan with
  source/rank/endpoint/hidden-construction controls before row materialization or learned smoke.

Current compatibility dataset v2 capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v2_capacity_scan/
status = h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization
decision = capacity_pass_but_direct_hl_lh_target_blocked_generate_counterfactuals_and_repackage_raw_witness
row_materialization_allowed_with_controls = true
direct_hl_lh_target_allowed = false
learned_smoke_allowed = false
validation_errors = 0
next = compatibility_dataset_v2_candidate_materialization
```

Capacity:

```text
support_contact positive / negative = 74364 / 896
relative_vertical positive / negative = 111032 / 592
```

Predicate imbalance:

```text
support_contact positive = lying on 26882 / standing on 23713 / supported by 23769
support_contact negative = lying on 896 / standing on 0 / supported by 0
relative_vertical positive = higher than 55811 / lower than 55221
relative_vertical negative = higher than 1 / lower than 591
```

Interpretation:

- primary family class mass is no longer the bottleneck;
- direct HL/LH labels are still not usable because queue kind, geometry status, rank, and predicate
  direction would be shortcut targets;
- next materialization must generate controlled negatives and raw numeric `G_e`, not simply copy
  queue polarity into labels;
- `attachment_like` remains diagnostic-only for `Q_e` and failure taxonomy.

Current compatibility dataset v2 candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v2_candidate_materialization/
status = h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit
rows = 400
groups = 200
compatibility positive / negative = 200 / 200
raw_witness matched / requested = 400 / 400
learned_smoke_allowed = false
validation_errors = 0
next = compatibility_dataset_v2_schema_shortcut_audit
```

Family and predicate balance:

```text
support_contact positive / negative = 120 / 120
support_contact lying on = 40 / 40
support_contact standing on = 40 / 40
support_contact supported by = 40 / 40

relative_vertical positive / negative = 80 / 80
relative_vertical higher than = 40 / 40
relative_vertical lower than = 40 / 40
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

- direct HL/LH target construction is no longer copied into the primary label;
- v2 candidates now use generated counterfactual negatives and raw numeric geometry evidence;
- this is still not a learned result or human reliability target;
- the next gate must verify schema leakage and generated-counterfactual shortcut risk before any
  learned compatibility smoke.

Current compatibility dataset v2 schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v2_schema_shortcut_audit/
status = h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view
rows = 400
compatibility positive / negative = 200 / 200
schema_errors = 0
leakage_high_risk_probes = 7
full_factorized_view_allowed = false
sanitized_view_written = true
learned_smoke_allowed = false
next = compatibility_dataset_v2_sanitized_view_smoke_plan
```

Shortcut audit:

```text
predicate_label = 0.500
relation_family = 0.500
source_rank_band = 0.500
source_score_bin = 0.500

row_role = 1.000
counterfactual_type = 1.000
G_e.geometry_source = 1.000
Q_e.generated_counterfactual = 1.000
Q_e.evidence_conflict_flag = 1.000
geometry_status_baseline = 1.000
relation_source = 1.000
```

Interpretation:

- visible semantic/source axes are controlled well enough for the next sanitized smoke plan;
- raw construction metadata is a perfect shortcut and must stay audit-only;
- `Q_e` remains conceptually valid as evidence quality, but generated-counterfactual flags are
  not deployable observability evidence;
- the next step is a smoke plan over `sanitized_model_view.jsonl`, not raw `full_factorized`.

Current compatibility dataset v2 sanitized view smoke plan:

```text
artifact_root = artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/
status = h002_compatibility_dataset_v2_sanitized_view_smoke_plan_ready
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
smoke_ready_view_written = true
learned_smoke_executed = false
next = compatibility_dataset_v2_sanitized_view_smoke_runner
```

Additional finding:

```text
Z_e.source_score_inherited_for_counterfactual = 1.000 shortcut accuracy
```

Interpretation:

- the first sanitized view was still too broad for a learned smoke input;
- generated counterfactuals inherit source score/rank, so the boolean flag saying that the score
  was inherited is target construction metadata;
- the runner must use `smoke_ready_view.jsonl`, where `Z_e_safe` excludes this flag;
- the next smoke is Task-A compatibility only, not a real `p_obs` or human-reliability `p_rel`
  target.

Current compatibility dataset v2 sanitized view smoke runner:

```text
artifact_root = artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner/
status = h002_compatibility_dataset_v2_sanitized_view_smoke_runner_diagnostic_only_failed_controls
rows = 400
compatibility positive / negative = 200 / 200
paired groups = 200
validation_errors = 0
next = compatibility_dataset_v2_failure_analysis
```

Task-A AUROC:

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

Gate interpretation:

- dataset sanity passed;
- source/semantic/object-pair shortcut controls passed;
- predicate conditioning over geometry-only failed;
- corruption controls failed.

Research interpretation:

```text
The current v2 dataset proves that sanitized geometry contains signal, but it does not yet prove
predicate-geometry compatibility. The target is currently solvable as generic geometry
perturbation detection, especially in support/contact.
```

Next failure analysis should determine whether to redesign the target so the same geometry must be
judged against different predicates, or to build relation-family-specific compatibility tasks where
predicate conditioning is actually necessary.

Current compatibility dataset v2 failure analysis:

```text
artifact_root = artifacts/compatibility_dataset_v2_failure_analysis/
status = h002_compatibility_dataset_v2_failure_analysis_ready
rows = 400
compatibility positive / negative = 200 / 200
validation_errors = 0
primary_cause = target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility
next = compatibility_dataset_v2_target_redesign_plan
```

Diagnostic evidence:

```text
geometry-only M4 AUROC = 0.6731
compatibility M5 AUROC = 0.6250
wrong-T same-G AUROC = 0.6250
mean |M5 - wrongT| = 0.0
```

Counterfactual-type diagnosis:

```text
support_contact shuffled_geometry false positive rate = 0.800
support_contact wrong_pair_geometry false positive rate = 0.425
support_contact contact_gap_or_overlap_perturbation false positive rate = 0.025
relative_vertical predicate_flip false positive rate = 0.650
relative_vertical subject_object_swap false positive rate = 0.375
```

Conclusion:

```text
Sanitization solved source/semantic leakage, but the current v2 target still does not require
predicate-conditioned reasoning. The next dataset must make predicate semantics necessary by
evaluating the same or near-identical geometry under multiple predicates.
```

Current compatibility dataset v2 target redesign plan:

```text
artifact_root = artifacts/compatibility_dataset_v2_target_redesign_plan/
status = h002_compatibility_dataset_v2_target_redesign_plan_ready
selected_route = v3_same_geometry_multi_predicate_contract
validation_errors = 0
next = compatibility_dataset_v3_contract
```

Decision:

```text
Do not repair v2 with more generated negatives.
Do not use a stronger combiner before target identifiability is fixed.
Keep v2 as diagnostic-only negative evidence.
Start v3 with same-geometry multi-predicate contrast.
```

Primary v3 contract:

```text
same G_e + predicate A = positive
same G_e + predicate B = negative
```

Initial family:

```text
relative_vertical: higher than / lower than
```

Rationale:

- the same directed-pair geometry can be paired with both predicates;
- exactly one predicate should match the signed vertical order under a fixed margin;
- `G_e` alone cannot solve two labels assigned to the same geometry group;
- this directly tests whether `T_e` conditions the interpretation of `G_e`.

Support/contact is secondary until role/orientation or visual/mesh evidence exists. Current
support/contact rows are dominated by distance and overlap, so using them as primary v3 target
would likely repeat the geometry-only failure.

Current compatibility dataset v3 contract:

```text
artifact_root = artifacts/compatibility_dataset_v3_contract/
status = h002_compatibility_dataset_v3_contract_ready
dataset = h002_compatibility_dataset_v3_predicate_conditioned
selected_route = same_geometry_multi_predicate
primary_family = relative_vertical
secondary_family = support_contact
validation_errors = 0
next = compatibility_dataset_v3_capacity_scan
```

Contract:

```text
same directed pair + same G_e + higher than = one compatibility label
same directed pair + same G_e + lower than = opposite compatibility label
```

This makes `G_e` alone insufficient by construction. The future smoke is meaningful only if
`T_e + G_e` beats `G_e` alone, wrong-predicate same-geometry control degrades, shuffled-geometry
control degrades, and source/predicate/object-pair shortcut probes stay near chance.

The initial frozen vertical-margin contract is:

```text
abs(center_delta_z) >= 0.10m
abs(normalized_center_delta_z) >= 0.20
```

The next step is a capacity scan, not materialization. It must verify whether full train-side
candidate artifacts contain enough clear same-geometry `higher than` / `lower than` groups before
creating v3 rows.

Current compatibility dataset v3 capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v3_capacity_scan/
status = h002_compatibility_dataset_v3_capacity_scan_passed_ready_for_candidate_materialization
match_rows_scanned = 4,818,996
relative_vertical_rows = 370,692
clear_same_geometry_groups = 122,570
higher_positive_groups = 61,285
lower_positive_groups = 61,285
balanced_group_capacity = 122,570
candidate_materialization_allowed = true
requires_axis_controls = true
validation_errors = 0
next = compatibility_dataset_v3_candidate_materialization
```

Interpretation:

- v3 same-geometry higher/lower target is feasible at full train-side scale.
- the direction balance is strong enough to build a 200-group / 400-row controlled candidate set.
- support/contact remains secondary because current artifacts expose numeric OBB/raw features but
  not role/orientation, contact direction, surface normal, or visual/mesh evidence.
- materialization must control shortcut axes:

```text
high_risk_axes = visible_pair
medium_risk_axes = object_label, subject_label
```

Therefore the next materialization must balance `higher_positive` and `lower_positive`, prioritize
mixed-direction visible-pair cells, cap single-direction visible-pair cells, avoid structural-only
floor/wall/ceiling dominance, and report predicate-only / visible-pair-only /
predicate+visible-pair shortcut probes before any learned smoke.

Current compatibility dataset v3 candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_candidate_materialization/
status = h002_compatibility_dataset_v3_candidate_materialization_ready_for_schema_shortcut_audit
candidate_rows = 400
geometry_groups = 200
selected_visible_pair_cells = 100
higher_positive_groups = 100
lower_positive_groups = 100
compatibility positive / negative = 200 / 200
validation_errors = 0
next = compatibility_dataset_v3_schema_shortcut_audit
```

Selection policy:

```text
one higher_positive group + one lower_positive group per selected visible_pair cell
```

This directly controls the prior high-risk `visible_pair` axis. After materialization, the row-level
shortcut probes are:

```text
predicate_label majority accuracy = 0.500
visible_pair majority accuracy = 0.500
predicate + visible_pair majority accuracy = 0.500
subject_label majority accuracy = 0.500
object_label majority accuracy = 0.500
source_rank_band majority accuracy = 0.5375
```

No high-risk or medium-risk row-level shortcut axis remains in the candidate artifact. This is still
not learned-smoke evidence; the next formal schema shortcut audit must verify that hidden fields,
construction route, labels, group ids, and source-predicate provenance cannot leak into model views.

Current compatibility dataset v3 schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
candidate_rows = 400
smoke_ready_rows = 400
allowed_feature_high_or_medium_risk = 0
blocked_raw_high_risk_probes = 2
validation_errors = 0
next = compatibility_dataset_v3_sanitized_view_smoke_plan
```

Decision:

```text
candidate_rows.jsonl = full audit/provenance artifact, not model input
sanitized_model_view.jsonl = intermediate materialization view, not final smoke input
smoke_ready_view.jsonl = only allowed input source for next learned-smoke planning
```

Important fix:

```text
G_e_numeric.geometry_feature_hash
```

was present in the intermediate materialization view for group integrity, but it has been removed
from the final `smoke_ready_view.jsonl`. The smoke-ready feature root contains only:

```text
feature_blocks.T_e
feature_blocks.Z_e_safe
feature_blocks.G_e_numeric
feature_blocks.Q_e_safe
```

Allowed feature probes are low risk:

```text
predicate_label = 0.500
subject_label = 0.500
object_label = 0.500
subject_object_text = 0.500
source_rank_band = 0.5375
source_score_normalized = 0.5175
source_rank = 0.5375
single G_e numeric threshold probes = 0.500
```

Blocked raw high-risk probes are `raw_row_id` and `hidden_source_prediction_id`, both expected
identifier shortcuts. They remain outside model features.

Current compatibility dataset v3 sanitized-view smoke plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/
status = h002_compatibility_dataset_v3_sanitized_view_smoke_plan_ready
input_source = artifacts/compatibility_dataset_v3_schema_shortcut_audit/smoke_ready_view.jsonl
rows = 400
positive / negative = 200 / 200
paired_groups = 200
validation_errors = 0
learned_smoke_executed = false
next = compatibility_dataset_v3_sanitized_view_smoke_runner
```

Decision:

```text
smoke_ready_view.jsonl is the only allowed model-input source.
candidate_rows.jsonl and sanitized_model_view.jsonl remain audit/provenance artifacts.
```

The primary learned-smoke view is not plain concatenation. It is:

```text
M5b_compatibility_TG_interaction
```

using predicate-conditioned vertical interaction features such as:

```text
expected_z_sign(predicate) * center_delta_z_m
expected_z_sign(predicate) * normalized_center_delta_z
```

This directly tests the current H002 claim: the same predicate-independent `G_e` should be
interpreted differently depending on the semantic relation content `T_e`.

Planned comparisons:

```text
source-only Z_e_safe
semantic-only T_e
semantic + source
geometry-only G_e
plain T_e + G_e concat
predicate-conditioned T_e + G_e interaction
factorized T_e + Z_e_safe + G_e + Q_e
predicate/object/source shortcut probes
wrong-T same-G control
shuffled-G controls
```

Promotion requires source/semantic/geometry shortcut probes to stay near chance, `M5b` to pass the
absolute AUROC and gain gates, and wrong-T / shuffled-G controls to degrade. The plan itself is not
paper evidence; it only authorizes the next train-only smoke runner.

Current compatibility dataset v3 sanitized-view smoke runner:

```text
artifact_root = artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/
status = h002_compatibility_dataset_v3_sanitized_view_smoke_runner_passed_controls
rows = 400
positive / negative = 200 / 200
paired_groups = 200
epochs = 120
validation_errors = 0
next = compatibility_dataset_v3_result_review_and_family_extension_decision
```

Main metrics:

```text
M1 source-only Z_e_safe AUROC = 0.525975
M2 semantic-only T_e AUROC = 0.445225
M3 semantic + source AUROC = 0.515800
M4 geometry-only G_e AUROC = 0.500000
M5a plain T_e + G_e concat AUROC = 0.446300
M5b predicate-conditioned T_e + G_e interaction AUROC = 1.000000
M6 factorized T_e + Z_e + G_e + Q_e AUROC = 1.000000
C1 wrong-T same-G control AUROC = 0.000000
C2 shuffled-G global control AUROC = 0.477713
C3 shuffled-G within-predicate control AUROC = 0.515400
```

Paired result:

```text
mean compatible-minus-incompatible score = 0.812703
positive pairwise direction fraction = 1.0
```

Interpretation:

- this is the first clean positive learned-smoke result for the new H002 direction;
- the v2 failure mode is addressed: the target is no longer solvable by generic geometry-only
  perturbation detection;
- `G_e` alone is chance because the paired rows share identical geometry;
- plain `T_e + G_e` concat is also near chance, so the useful signal comes from explicit
  predicate-conditioned compatibility interaction;
- wrong-T inversion and shuffled-G degradation support that the smoke is using aligned
  semantic-geometry evidence rather than source score, object-pair, or predicate-only shortcuts.

Claim boundary:

```text
This is a relative_vertical C_e mechanism proof, not a broad relation reliability result.
```

The next decision should review whether to expand beyond `higher than` / `lower than`, and what
additional evidence is required before support/contact or attachment-like families can be tested
without falling back into shortcut-prone target construction.

Current compatibility dataset v3 result review and family extension decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision/
status = h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe
selected_path = accept_relative_vertical_Ce_mechanism_proof_and_probe_support_contact_evidence
validation_errors = 0
next = compatibility_dataset_v3_support_contact_evidence_probe_plan
```

Decision:

```text
relative_vertical v3 smoke = accepted as scoped C_e mechanism proof
broad relation reliability = not claimed
paper-level Docker result = not claimed
next family = support_contact, but evidence probe first
```

Allowed claim:

```text
scoped predicate-geometry compatibility mechanism for relative_vertical
```

Blocked claims:

```text
broad relation reliability
final p_rel / p_obs decision quality
all 3DSSG relation-family generality
paper-level Docker-reproduced result
```

Family decisions:

```text
relative_vertical = retain as core scoped mechanism proof
support_contact = best next extension candidate, probe evidence before smoke
attachment_like = diagnostic hard family until visual/mesh evidence axis is materialized
proximity = future generality, not current C_e primary
relative_horizontal = deferred until reference-frame contract
```

The next step must not directly run another support/contact smoke from v2 generated negatives.
It should first test whether current artifacts contain role/orientation/contact-direction evidence
that can make predicate semantics necessary rather than letting gap/overlap or generic geometry
perturbations dominate the label.

Current compatibility dataset v3 support/contact evidence probe plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan/
status = h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_ready
selected_route = support_contact_evidence_inventory_before_materialization_or_smoke
validation_errors = 0
next = compatibility_dataset_v3_support_contact_evidence_probe_runner
```

Prior support/contact evidence:

```text
eligible positive / negative = 74,364 / 896
direct HL/LH predicate balance pass = false
generated counterfactual policy = wrong_pair_shuffle_and_contact_gap_perturbation_required
v2 materialized support/contact positive / negative = 120 / 120
v2 primary cause = target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility
```

Current available evidence axes:

```text
available = distance, 3D/XY separation, projected overlap/IoU, vertical gap, object top/bottom z
partial = vertical gap and support-order proxies
missing = role/orientation/pose
missing = explicit contact direction
missing = surface normal
missing = mesh / visual / multi-view evidence
```

Blocked next actions:

```text
run_support_contact_learned_smoke_now
use_contact_gap_or_overlap_perturbation_as_primary_negative
claim_support_contact_generality_from_v2_smoke
promote_relative_vertical_result_to_broad_reliability
```

The next runner should produce a source inventory, evidence-axis inventory, same/near-geometry
capacity, negative-policy audit, shortcut precheck, and path decision before any support/contact
materialization or learned smoke is allowed.

Current compatibility dataset v3 support/contact evidence probe runner:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner/
status = h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke
selected_path = route_to_visual_mesh_or_role_orientation_evidence
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
```

Key counts:

```text
support_queue_rows = 161498
distinct_directed_pairs = 75763
distinct_visible_pairs = 4109
distinct_scans = 1157
exact multi-predicate mixed-geometry groups = 75
non-hard-surface exact candidate groups = 4
```

Path decision:

```text
support_contact_materialization_allowed = false
visual_mesh_or_role_orientation_required = true
diagnostic_only = true
missing_required_axes = role_orientation_pose, contact_direction_surface_normal, mesh_visual_multiview
```

Interpretation:

The raw support/contact queue is large, but it does not yet provide a clean compatibility target.
Current numeric evidence mostly exposes distance, overlap, vertical gap, and OBB top/bottom
signals. These are useful controls, but they are not enough to distinguish `standing on`, `lying
on`, and `supported by` as predicate-conditioned relation semantics. After avoiding hard-surface
dominance and construction/provenance shortcuts, only 4 non-hard-surface exact candidate groups
remain, so support/contact should not be promoted to learned smoke from the current numeric view.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan
```

This next step should specify how to add or recover role/orientation, contact direction, surface
normal, mesh, visual, or multi-view evidence while preserving the H002 factor boundary:
`T_e`/`Z_e`/`G_e`/`C_e`/`Q_e` separation, no source-score leakage into `C_e`, and no construction
proxy fields in model input.

Current compatibility dataset v3 support/contact visual-mesh evidence plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_ready
selected_route = mesh_pose_contact_first_multiview_audit_first
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
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

Decision:

```text
numeric_only_support_contact_smoke_allowed = false
mesh_pose_contact_evidence_required = true
multiview_model_input_allowed_now = false
multiview_audit_first = true
attachment_packets_reuse_as_labels = false
attachment_packet_builder_reuse_as_template = true
```

Interpretation:

The next support/contact extension should not be framed as simply adding RGB-D/multi-view input.
The more defensible route is to first derive predicate-independent mesh/pose/contact `G_e`:
instance point crops, PCA/pose/orientation cues, contact surface gap, support area, and local
surface normal alignment. Multi-view is useful, but at this stage it should be used as audit and
`Q_e` evidence first: co-visible frame count, crop quality, occlusion, and contact visibility.
Only after source inventory and shortcut controls pass should visual evidence become a deployable
model input.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
```

Current compatibility dataset v3 support/contact visual-mesh source inventory:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe
selected_path = mesh_pose_contact_feature_probe_before_materialization
validation_errors = 0
next = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan
```

Join coverage:

```text
support_rows = 161498
distinct_scans = 1157
distinct_directed_pairs = 75763
distinct_visible_pairs = 4109
scan_asset_complete_rate = 1.000000
semseg_both_objects_present_rate = 1.000000
mesh_contact_surface_possible_rate = 1.000000
sequence_multiview_possible_rate = 1.000000
```

Predicate and queue distribution:

```text
lying on = 60652
standing on = 50245
supported by = 50601
HL = 1069
LH = 160429
geometry_unsatisfied = 1069
geometry_satisfied = 160429
```

Decision:

```text
mesh_pose_contact_feature_probe_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
numeric_only_smoke_allowed = false
multiview_model_input_allowed_now = false
multiview_qe_audit_first = true
```

Interpretation:

The support/contact candidate rows can be joined to 3RScan mesh, aligned instance PLY, semseg OBB,
dominant normals, and sequence zips at full coverage. This removes the source-availability
blocker. However, it does not solve the target-identifiability problem by itself. Hard-surface
dominance remains high (`0.7023`), HL/LH is extremely imbalanced (`1069/160429`), and exact-pair
clean capacity remains only `4`. Therefore the next step is a feature probe that derives and
audits predicate-independent `G_e` candidates, not candidate materialization or learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan
```

Current compatibility dataset v3 support/contact mesh-pose-contact feature probe plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan/
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_ready
selected_route = semseg_obb_normal_full_probe_ply_contact_sample_probe
validation_errors = 0
next = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
```

Plan:

```text
Tier A = semseg OBB / dominant-normal features for all 161498 support/contact rows
Tier B = aligned PLY / mesh-contact features on a 1200-row stratified probe sample
Tier C = sequence / multi-view only as small audit and Q_e sample
```

Primary feature families:

```text
semseg_obb_pose
dominant_normal_alignment
obb_contact_proxy
aligned_ply_object_points
mesh_contact_surface
sequence_visibility_quality as Q_e only
```

Decision:

```text
feature_probe_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
multiview_qe_audit_first = true
paper_evidence_allowed = false
```

Interpretation:

This plan converts the previous "source exists" result into a concrete feature-probe contract.
The next runner should not train a model and should not create a compatibility target. Its job is
to verify whether support/contact has usable predicate-independent `G_e` beyond old OBB
distance/overlap/gap proxies. Required diagnostics are feature derivability, finite-value sanity,
predicate-wise variation, hard-surface sensitivity, queue sensitivity, blocked-field absence, and
old numeric proxy dominance.

Next:

```text
compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
```

Current compatibility dataset v3 support/contact mesh-pose-contact feature probe runner:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner/
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review
selected_path = review_mesh_pose_contact_features_before_materialization
validation_errors = 0
next = compatibility_dataset_v3_support_contact_feature_probe_result_review
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

Interpretation:

The source-availability and feature-derivability blockers are cleared for support/contact. The
branch can now inspect real mesh/pose/contact `G_e` candidates rather than only old
gap/overlap/distance proxies. However, this does not clear the target-construction blocker:
hard-surface dominance is still high (`0.7023`) and HL/LH is extremely imbalanced
(`1069/160429`). Therefore the next step is result review, not row materialization or learned
smoke.

Next:

```text
compatibility_dataset_v3_support_contact_feature_probe_result_review
```

Current compatibility dataset v3 support/contact feature probe result review:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review/
status = h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan
selected_path = select_pose_conditioned_same_geometry_support_contact_target_plan
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```

Gate result:

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
lying on vs standing on:
  pose_conditioned_contrast_candidate
  max_abs_standardized_delta = 0.4384

lying on vs supported by:
  pose_conditioned_contrast_candidate
  max_abs_standardized_delta = 0.3748

standing on vs supported by:
  collapse_or_superordinate_overlap
  max_abs_standardized_delta = 0.1398
```

Interpretation:

The feature probe clears the support/contact feature-availability blocker, but not the
target-construction blocker. The next support/contact target should not use HL/LH or
standing/support labels directly. It should build same-geometry predicate-flip rows where `G_e`
is held fixed and `T_e` changes between `lying on` and `standing on`. This preserves the H002
claim that compatibility depends on the interaction between semantic content and geometry
evidence, not geometry alone.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```

Current compatibility dataset v3 support/contact pose-conditioned target plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan
selected_path = capacity_scan_pose_conditioned_same_geometry_lying_standing_target
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```

Target definition:

```text
same G_e anchor + T_e = lying on
same G_e anchor + T_e = standing on
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

Design decisions:

```text
primary_contrast = lying on vs standing on
diagnostic_contrast = lying on vs supported by
excluded_primary_contrast = standing on vs supported by
candidate_materialization_allowed = false
learned_smoke_allowed = false
capacity_scan_allowed = true
```

Interpretation:

This plan converts support/contact from a generic geometry-verification target into a
predicate-conditioned compatibility target. The target is only meaningful if the same `G_e`
anchor is paired with both `lying on` and `standing on`, and if lying-like/upright anchors are
balanced. The next capacity scan must verify that such anchors exist in sufficient quantity while
controlling hard-surface, visible-pair, scan, source-score, and queue-kind shortcuts.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```

Current compatibility dataset v3 support/contact pose-conditioned capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_pose_conditioned_support_contact
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan
```

Capacity result:

```text
support_queue_rows = 161498
unique_directed_anchors = 75763
classified_anchors_for_selected_threshold = 4031
selected_anchor_groups = 200
selected_total_rows_if_materialized = 400
selected_state_counts = {
  lying_like_support_contact: 100,
  upright_support_contact: 100
}
selected_non_hard_surface_share = 1.0
selected_max_single_visible_pair_share = 0.035
selected_max_single_scan_share = 0.03
passes_materialization_capacity_gate = true
```

Interpretation:

The pose-conditioned `lying on` / `standing on` same-geometry target is feasible at the planned
400-row scale. This is stronger than the previous support/contact attempts because the selected
rows are balanced by anchor pose state, avoid hard-surface dominance in the selected preview, and
keep queue kind as audit-only. The next step is a materialization plan, not direct learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan
```

Current compatibility dataset v3 support/contact pose-conditioned candidate materialization plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_ready
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```

Plan:

```text
frozen_anchor_groups = 200
planned_rows = 400
state_counts = {
  lying_like_support_contact: 100,
  upright_support_contact: 100
}
predicate_counts_if_materialized = {
  lying on: 200,
  standing on: 200
}
label_counts_if_materialized = {
  0: 200,
  1: 200
}
```

Interpretation:

The next materializer is allowed to create the 400 candidate rows, but only by expanding the
frozen capacity-preview anchors. It may not change thresholds, refill anchors, use HL/LH as label,
or run learned smoke. Learned smoke remains blocked until the materialized rows pass schema and
shortcut audit.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```

Current compatibility dataset v3 support/contact pose-conditioned candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```

Materialized result:

```text
anchor_groups = 200
candidate_rows = 400
smoke_ready_rows = 400
hidden_manifest_rows = 400
label_counts = {
  0: 200,
  1: 200
}
predicate_counts = {
  lying on: 200,
  standing on: 200
}
state_counts = {
  lying_like_support_contact: 100,
  upright_support_contact: 100
}
semseg_complete_rows = 400
point_complete_rows = 240
hard_surface_rows = 0
```

Interpretation:

The frozen support/contact target has now been converted into concrete candidate rows. Each
anchor contributes two rows with identical `G_e` and different `T_e`, so the target directly tests
predicate-geometry compatibility rather than generic geometry validity. Optional aligned PLY point
features are incomplete for part of the dataset and are therefore exposed through `Q_e`, not used
as a hard materialization requirement. The smoke-ready view excludes scan/object ids, visible pair,
queue kind, source predicates, pose state, and `G_e_hash`. Learned smoke is still blocked until the
formal schema/shortcut audit passes.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit
```

Current compatibility dataset v3 support/contact pose-conditioned schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```

Audit result:

```text
candidate_rows = 400
smoke_ready_rows = 400
groups = 200
label_counts = {
  0: 200,
  1: 200
}
predicate_counts = {
  lying on: 200,
  standing on: 200
}
allowed_feature_high_or_medium_risk = 0
allowed_feature_high_risk = 0
blocked_feature_path_hits = 0
blocked_field_leakage_hits = 0
blocked_raw_high_risk_probes = 4
group_integrity_errors = 0
```

Interpretation:

The support/contact same-`G_e` target passes the schema-level identifiability gate. Predicate-only,
object-class-only, geometry-only, and `Q_e`-only single-field probes are all low risk. The only
high-risk probes are blocked raw/construction fields: row id, target label, hidden
pose-state-by-predicate, and hidden `G_e`-hash-by-predicate. Therefore the next step can plan a
learned smoke run over the stricter `feature_blocks` view, but learned smoke itself is still not
executed at this audit stage.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan
```

Current compatibility dataset v3 support/contact pose-conditioned sanitized-view smoke plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next = compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner
```

Plan:

```text
input_source = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/smoke_ready_view.jsonl
rows = 400
positive_rows = 200
negative_rows = 200
paired_groups = 200
semseg_complete_rows = 400
point_complete_rows = 240
primary_model = M5b_compatibility_TG_pose_interaction
```

Interpretation:

The smoke plan freezes the next learned-smoke contract without running a model. The runner must use
only the audited `feature_blocks` view, with `G_e_mesh_pose_contact` as the geometry block. The
primary model is the predicate-conditioned support/contact pose interaction view; semantic-only,
geometry-only, source-only, no-interaction concat, wrong-T same-G, and shuffled-G controls are
required before the result can be interpreted as compatibility evidence.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner
```

Current compatibility dataset v3 support/contact pose-conditioned sanitized-view smoke runner:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner_passed_controls
validation_errors = 0
overall = support_contact_pose_conditioned_smoke_passed_controls
next = compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```

Key result:

```text
rows = 400
paired_groups = 200
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

Interpretation:

The train-only support/contact smoke passes all predefined controls. Because the same `G_e` is
paired with both `lying on` and `standing on`, geometry-only and predicate-only shortcuts remain
near chance, while the predicate-conditioned pose interaction succeeds. Wrong-T inverts the model
and shuffled-G returns near chance, which supports aligned `T_e`-`G_e` compatibility rather than
metadata leakage. The result is currently a strong `C_e` mechanism proof for this scoped family,
not yet a broad relation-reliability or paper-level claim.

Next:

```text
compatibility_dataset_v3_support_contact_pose_conditioned_result_review
```

Current compatibility dataset v3 support/contact pose-conditioned result review:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis
selected_path = accept_support_contact_Ce_mechanism_proof_select_multi_family_synthesis
validation_errors = 0
next = compatibility_dataset_v3_multi_family_result_synthesis_plan
```

Decision:

The support/contact pose-conditioned result is accepted as a scoped `C_e` mechanism proof.
The allowed claim is deliberately narrow:

```text
predicate-independent support/contact G_e can become compatible or incompatible depending on
the semantic content T_e of lying on versus standing on.
```

This is important because the successful model is not merely using high source score, predicate
identity, object pair identity, quality flags, or geometry alone. The runner controls show:

```text
M5b_compatibility_TG_pose_interaction AUROC = 1.000
M4_geometry_only_G AUROC = 0.500
M5a_compatibility_TG_concat AUROC = 0.382
C1_wrong_T_same_G_control AUROC = 0.000
C2/C3 shuffled-G controls AUROC = 0.525 / 0.568
```

However, this remains a controlled compatibility target. It is not yet broad relation reliability,
not a final `p_rel` / `p_obs` result, not human-audited reliability performance, not all-family
generality, and not paper-level Docker evidence.

Updated interpretation:

- `relative_vertical` is the first scoped `C_e` mechanism result.
- `support_contact_pose_conditioned` is the second scoped `C_e` mechanism result.
- `supported by` remains diagnostic/superordinate.
- `attachment_like`, `proximity`, and `relative_horizontal` should not be added before the
  current two-family evidence is synthesized into one claim boundary.

Next:

```text
compatibility_dataset_v3_multi_family_result_synthesis_plan
```

Current compatibility dataset v3 multi-family result synthesis plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan/
status = h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_ready
selected_path = freeze_two_family_Ce_claim_select_independent_validity_target_plan
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_target_plan
```

Allowed claim after synthesis:

```text
Across relative-vertical and support/contact pose-conditioned relation families,
predicate-independent geometry evidence G_e is not sufficient by itself. Relation
compatibility requires an explicit semantic-geometry compatibility factor C_e that
conditions geometry interpretation on semantic content T_e.
```

Evidence summary:

```text
relative_vertical:
  predicates = higher than / lower than
  M5b AUROC = 1.000
  G-only AUROC = 0.500
  concat AUROC = 0.446
  wrong-T AUROC = 0.000
  shuffled-G AUROC = 0.478 / 0.515

support_contact_pose_conditioned:
  predicates = lying on / standing on
  M5b AUROC = 1.000
  G-only AUROC = 0.500
  concat AUROC = 0.382
  wrong-T AUROC = 0.000
  shuffled-G AUROC = 0.525 / 0.568
```

Interpretation:

H002 now has a coherent two-family `C_e` mechanism proof. The key result is not that a model can
detect geometric validity alone, but that the same predicate-independent geometry evidence must be
interpreted differently depending on semantic content. This is exactly the role of
`C_e = compatibility(T_e, G_e)`.

The synthesis also clarifies the current bottleneck. Adding another constructed family would not
answer the strongest reviewer question. The next problem is target independence: whether this
`C_e` factor helps on relation validity labels that are not generated by the same same-`G_e`
construction rule.

Blocked claims remain:

- broad 3D Scene Graph relation reliability;
- final `p_rel` / `p_obs` decision quality;
- human-audited relation reliability performance;
- all-family generality;
- paper-level Docker-reproduced evidence.

Next:

```text
compatibility_dataset_v3_independent_validity_target_plan
```

Current compatibility dataset v3 independent validity target plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_target_plan/
status = h002_compatibility_dataset_v3_independent_validity_target_plan_ready
selected_path = select_gt_anchored_train_validity_inventory_before_materialization
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_source_inventory
```

Decision:

The next target should be GT-anchored and train-side:

```text
GT_anchored_train_validity_target
```

Reason:

The current two-family same-`G_e` targets prove the `C_e` mechanism, but they are still constructed
compatibility labels. To move toward relation reliability, H002 needs labels whose source is
independent from the same-geometry construction rule. Official train GT is the strongest available
starting point, while `no-GT` rows must not be treated as negatives because 3DSSG annotations are
incomplete.

Target option decision:

```text
GT_anchored_train_validity = selected
human_audit_accept_reject = defer
cross_source_agreement = defer
high_precision_geometry_rule_subset = auxiliary_only
no_GT_as_negative = reject
```

Train GT capacity snapshot:

```text
relative_vertical:
  higher than = 1831
  lower than = 1831
  total = 3662

support_contact_pose_conditioned:
  standing on = 9992
  lying on = 2024
  total = 12016
```

The next source-inventory step must verify whether these GT anchors can be joined with Open3DSG
train raw-dump `Z_e`, geometry `G_e`, and matched hard negatives without using no-GT as a naive
negative label.

Next:

```text
compatibility_dataset_v3_independent_validity_source_inventory
```

Current compatibility dataset v3 independent validity source inventory:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_source_inventory/
status = h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan
selected_path = materialize_gt_anchored_independent_validity_rows
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_materialization_plan
```

Inventory result:

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
  no_gt_geometry_satisfied_abstain = 105242

support_contact_pose_conditioned:
  rows = 370692
  source_z_join_rate = 1.0
  geometry_g_join_rate = 1.0
  positive_exact_gt_satisfied = 7564
  strong_negative_gt_pair_other_predicate_unsatisfied = 1067
  no_gt_geometry_satisfied_abstain = 83463
```

Interpretation:

The independent validity route is feasible for both primary families. This is important because
H002 no longer has to rely only on constructed same-`G_e` compatibility labels. There are enough
train-side rows where an exact GT relation and satisfied geometry can form positives, and enough
GT-pair other-predicate / same-family mismatch rows with unsatisfied geometry can form strong
negative candidates.

The no-GT policy remains strict:

```text
no-GT is abstain/audit, not negative.
```

Next:

```text
compatibility_dataset_v3_independent_validity_materialization_plan
```

Current compatibility dataset v3 independent validity materialization plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_materialization_plan/
status = h002_compatibility_dataset_v3_independent_validity_materialization_plan_ready
selected_path = materialize_balanced_gt_anchored_independent_validity_candidates
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_candidate_materialization
```

Planned counts:

```text
planned_total_rows = 4027
planned_primary_binary_rows = 3200
planned_nonbinary_audit_or_abstain_rows = 827

relative_vertical:
  positive = 800
  negative = 800
  no-GT geometry-satisfied abstain/audit = 200
  geometry-uncertain abstain = 200
  exact-GT geometry-unsatisfied audit = 12

support_contact_pose_conditioned:
  positive = 800
  negative = 800
  no-GT geometry-satisfied abstain/audit = 200
  geometry-uncertain abstain = 200
  exact-GT geometry-unsatisfied audit = 15
```

Label policy:

```text
positive = exact GT match + geometry satisfied
negative = GT-pair other-predicate or same-family mismatch + geometry unsatisfied
abstain = no-GT geometry-supported or geometry-uncertain rows
audit_required = exact GT match + geometry unsatisfied
```

This is the first H002 plan that can test `C_e` and later `p_rel` on a label source independent of
the constructed same-`G_e` compatibility target. The strongest remaining blocker is now not class
mass, but schema/shortcut control after materialization.

Next:

```text
compatibility_dataset_v3_independent_validity_candidate_materialization
```

Current compatibility dataset v3 independent validity candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization/
status = h002_compatibility_dataset_v3_independent_validity_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```

Materialized counts:

```text
total_rows = 4027
primary_binary_rows = 3200
nonbinary_abstain_or_audit_rows = 827
primary_positive_rows = 1600
primary_negative_rows = 1600

relative_vertical = 2012
support_contact_pose_conditioned = 2015
```

Quota result:

```text
relative_vertical:
  positive exact-GT satisfied = 800
  strong negative GT-pair other-predicate unsatisfied = 800
  no-GT geometry-satisfied abstain/audit = 200
  geometry-uncertain abstain = 200
  exact-GT geometry-unsatisfied audit = 12

support_contact_pose_conditioned:
  positive exact-GT satisfied = 800
  strong negative GT-pair other-predicate unsatisfied = 800
  no-GT geometry-satisfied abstain/audit = 200
  geometry-uncertain abstain = 200
  exact-GT geometry-unsatisfied audit = 15
```

Important caveat:

```text
strict caps selected = 3491 rows
visible-pair-cap-relaxed fallback selected = 536 rows
cap_relaxation_used = true
```

This does not invalidate the independent validity target, but it changes the immediate risk. The
target is now class-balanced and GT-anchored, while shortcut risk through subject/object visible
pairs may be higher than planned. Therefore the next step is not learned smoke, but schema and
shortcut audit over the materialized `smoke_ready_view`.

Next:

```text
compatibility_dataset_v3_independent_validity_schema_shortcut_audit
```

Current compatibility dataset v3 independent validity schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next = compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```

Counts:

```text
candidate_rows = 4027
primary_binary_rows = 3200
sanitized_primary_rows = 3200
positive / negative = 1600 / 1600
```

Schema result:

```text
sanitized_blocked_feature_path_hits = 0
sanitized_blocked_field_leakage_hits = 0
```

Shortcut result:

```text
allowed_feature_high_or_medium_risk = 2
allowed_feature_high_risk = 1
allowed_feature_medium_risk = 1

predicate_x_class_pair accuracy = 0.976562
subject_object_class_pair accuracy = 0.840000
```

Construction-derived geometry summary fields are correctly identified as blocked:

```text
geometry_status = 1.000000
consistency_score = 1.000000
geometry_residual_proxy = 1.000000
geometry_axis = 1.000000
p_geom_valid = 0.750625
```

These fields are removed from the stricter sanitized primary view. However, the primary binary
target is still too predictable from semantic object-pair strata. This means the independent
validity target currently tests a biased candidate distribution more than it tests whether
`C_e = compatibility(T_e, G_e)` is necessary.

Therefore learned smoke remains blocked. The next step is a path decision: repair the target to
control object-pair / predicate-object-pair strata, or freeze this artifact as diagnostic evidence
that GT-anchored validity alone is not sufficient for a top-tier H002 claim.

Next:

```text
compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit
```

Current compatibility dataset v3 independent validity path decision after schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_independent_validity_path_decision_select_stratum_repair_capacity_scan
selected_path = freeze_current_target_diagnostic_select_full_train_stratum_repair_capacity_scan
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```

Decision:

```text
current independent-validity target = diagnostic only
learned smoke = blocked
paper evidence = blocked
full-train stratum repair capacity scan = selected next
```

Why the current artifact is not enough:

```text
predicate_x_class_pair shortcut accuracy = 0.976562
subject_object_class_pair shortcut accuracy = 0.840000

current artifact exact predicate_x_class_pair balanced capacity = 150
required repaired primary rows = 800
required repaired rows per class = 400
```

Repair-capacity table:

```text
family = 3200
predicate_label = 2374
subject_object_class_pair = 1024
predicate_x_class_pair = 150
predicate_x_class_pair_x_rank_band = 146
```

Interpretation:

The current artifact fixed class balance but not semantic-stratum balance. Dropping object labels
from `T_e` would hide the shortcut but would also weaken the H002 factor contract, because object
class semantics are part of the relation semantics. Therefore the more principled repair is not
feature deletion, but checking whether full train contains enough exact predicate/object-class
mixed strata to build a controlled target.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan
```

Current compatibility dataset v3 independent validity stratum repair capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_ready_for_materialization_plan
selected_path = materialize_exact_predicate_class_stratum_repaired_independent_validity_target
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```

Full train scan:

```text
total_match_rows = 4818996
selected_family_rows = 741384
primary_rows = 29121
primary_positive = 8704
primary_negative = 20417
source_z_join_rate_primary = 1.0
geometry_g_join_rate_primary = 1.0
```

Exact semantic-stratum capacity:

```text
predicate_x_class_pair groups = 3024
predicate_x_class_pair mixed_groups = 39
predicate_x_class_pair raw balanced capacity = 2384
predicate_x_class_pair scan-capped capacity = 2252
repair_ready = true
```

Axis comparison:

```text
family capacity = 4414
predicate_label capacity = 4414
subject_object_class_pair capacity = 11378
predicate_x_class_pair capacity = 2384
predicate_x_class_pair_x_rank_band capacity = 2378
```

Interpretation:

The previous 4027-row artifact failed because exact predicate-class mixed capacity inside that
sample was only `150`. Full train changes the situation: exact predicate-class balance is feasible
at a useful scale. Therefore the independent-validity route should not be abandoned yet. The next
step is to write a materialization plan that samples only from mixed exact predicate/object-class
strata, balances labels inside each retained stratum, and then repeats schema/shortcut audit.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan
```

Current compatibility dataset v3 independent validity stratum repair materialization plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready
selected_path = materialize_exact_predicate_class_balanced_independent_validity_rows
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```

Planned target:

```text
primary_rows = 1600
positive_rows = 800
negative_rows = 800
retained_exact_strata = 35
max_pairs_per_stratum = 125
```

Family distribution:

```text
relative_vertical = 1512
support_contact_pose_conditioned = 88
```

Interpretation:

The next repaired target explicitly addresses the failure cause found in the schema shortcut audit.
Instead of deleting object class semantics from `T_e`, it balances labels inside exact
`predicate_label + subject_class_label + object_class_label` strata. This preserves the H002 factor
contract while directly testing whether `C_e` and raw `G_e` can help after the strongest semantic
stratum shortcut is controlled.

Important caveat:

```text
this repaired target is not family-balanced generality evidence.
support/contact exact-stratum capacity is only a diagnostic slice.
```

Therefore, if the next materialized rows pass schema audit and later learned smoke, the strongest
claim is an independent-validity mechanism proof mainly for `relative_vertical`, with
support/contact retained as a capacity-limited stress slice. A broader family-general claim still
requires additional target construction or evidence expansion.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```

Current compatibility dataset v3 independent validity stratum repair candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```

Materialized target:

```text
primary_rows = 1600
positive_rows = 800
negative_rows = 800
retained_exact_strata = 35
scan_cap_relaxation_rows = 0
```

Family distribution:

```text
relative_vertical = 1512
support_contact_pose_conditioned = 88
```

Schema precheck:

```text
model_safe_view_forbidden_key_hits = 0
feature_block_forbidden_key_hits = 0
stratum_internal_balance_failures = 0
```

Interpretation:

The repaired independent-validity rows have now been materialized. This directly tests the previous
failure cause: if the next schema shortcut audit shows low `predicate_x_class_pair` probe accuracy,
the main blocker was target-construction imbalance rather than the H002 factor contract itself. If
the shortcut remains high, then independent-validity labels still carry hidden construction bias even
after exact semantic-stratum balance.

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```

Current compatibility dataset v3 independent validity stratum repair schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```

Audit result:

```text
model_safe_rows = 1600
label_counts = 800 / 800
critical_high_or_medium = 0
source_confidence_high_or_medium = 0
raw_geometry_high_or_medium = 0
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
```

Key shortcut probes:

```text
predicate_x_class_pair = 0.500000
subject_object_class_pair = 0.500000
predicate_label = 0.500000
rank_band = 0.553750
semantic_rank = 0.549375
semantic_score_norm = 0.525625
```

Interpretation:

This is the first independent-validity target stage where the previous `predicate_x_class_pair`
blocker is directly repaired rather than bypassed. The result supports the view that the earlier
failure was primarily a target-construction shortcut, not a necessary failure of the H002 factor
contract. Learned smoke can now be planned on the sanitized view.

Remaining caveat:

```text
support_contact_pose_conditioned remains diagnostic only in this repaired target.
```

Next:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan
```

Current compatibility dataset v3 independent validity stratum repair sanitized view smoke plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_ready
rows = 1600
positive_rows = 800
negative_rows = 800
validation_errors = 0
learned_smoke_executed = false
next = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```

Planned comparison:

```text
M1 semantic_only_T
M2 source_only_Z
M3 semantic_source_TZ
M4 geometry_only_G
M5 T_G_concat
M6 T_G_compatibility_interaction
M7 factorized_TZGQ
```

Interpretation gate:

Unlike the earlier same-geometry compatibility tasks, this repaired target is an
independent-validity target. Therefore `G_e_raw` can legitimately be predictive. The smoke runner
must treat geometry-only as a serious baseline:

```text
if geometry-only M4 is within 0.02 AUROC of M6/M7,
claim = geometry-dominance diagnostic, not factorized compatibility evidence.
```

Next at plan completion:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```

Current compatibility dataset v3 independent validity stratum repair sanitized view smoke runner:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_passed_controls
rows = 1600
positive_rows = 800
negative_rows = 800
groups = 1097
mixed_label_groups = 491
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```

Main metrics:

```text
M1 semantic_only_T AUROC = 0.416131
M2 source_only_Z AUROC = 0.568110
M3 semantic_source_TZ AUROC = 0.533226
M4 geometry_only_G AUROC = 0.527064
M5 T_G_concat AUROC = 0.480008
M6 T_G_compatibility_interaction AUROC = 0.995633
M7 factorized_TZGQ AUROC = 0.995280
C1 shuffled_G_global AUROC = 0.514618
C2 shuffled_G_within_predicate AUROC = 0.458553
C3 wrong_predicate_family_control AUROC = 0.026644
```

Interpretation:

The repaired target passes the planned train-only smoke gates. Semantic/source shortcut probes stay
below `0.60` AUROC, geometry-only is weak (`0.527064`), and the primary compatibility interaction
strongly improves over both semantic/source and geometry-only baselines. This supports the current
H002 mechanism claim that relation reliability should include a predicate-conditioned compatibility
term `C_e = compatibility(T_e, G_e)`.

Boundary:

This is not yet paper-level evidence and does not establish calibrated probability. The primary
models have high `ECE-10`, so the current result should be described as compatibility
discrimination/ranking evidence. `support_contact_pose_conditioned` remains diagnostic because it
contributes only `88` rows.

Next at runner completion:

```text
compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```

Current compatibility dataset v3 independent validity stratum repair smoke result review:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review/
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan
selected_path = accept_independent_validity_Ce_smoke_select_calibration_and_scope_plan
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_calibration_scope_plan
```

Decision:

The repaired independent-validity smoke is accepted as the current strongest H002 `C_e` mechanism
evidence. It fixes the two earlier blockers: semantic/source shortcut and geometry-only dominance.
The allowed claim is restricted to compatibility discrimination/ranking:

```text
C_e = compatibility(T_e, G_e)
```

Blocked claims remain:

- calibrated relation reliability posterior;
- paper-level result;
- held-out validation/test performance;
- broad all-relation 3DSSG reliability;
- support/contact independent-validity generality from this artifact;
- attachment/proximity/horizontal relation generality.

Key risks:

```text
primary ECE-10 = 0.480112
relative_vertical rows = 1512 / 1600
support_contact_pose_conditioned rows = 88 / 1600
```

Therefore the next route is not a larger architecture. The next route is calibration/scope planning:
decide whether H002 can move from `C_e` discrimination to calibrated reliability scoring, and
whether support/contact needs a separate balanced independent-validity target.

Next:

```text
compatibility_dataset_v3_independent_validity_calibration_scope_plan
```

Current compatibility dataset v3 independent validity calibration scope plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan/
status = h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing
selected_path = calibration_metric_audit_passed_select_support_contact_family_balancing
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

Decision:

The previous `ECE-10 = 0.480112` should not be treated as a valid binary probability-calibration
failure by itself. The old helper compared threshold correctness against the raw positive-class
score, so it penalized correct low positive scores on negative rows. Recomputing standard
probability calibration gives:

```text
M6_TG_compatibility_interaction probability ECE-10 = 0.046582
M6_TG_compatibility_interaction Brier = 0.020504
M7_factorized_TZGQ probability ECE-10 = 0.048281
```

This changes the blocker interpretation. The next immediate blocker is not calibration repair; it
is family scope. The current independent-validity result is still dominated by `relative_vertical`
(`1512 / 1600` rows), while `support_contact_pose_conditioned` has only `88` rows. Therefore the
next H002 route is to build a support/contact-balanced independent-validity plan.

Claim boundary:

- keep the current result as train-only `C_e` discrimination/ranking evidence;
- use corrected probability-ECE and Brier in future smoke runners;
- keep calibrated `p_rel` / `p_obs`, paper-level, held-out, and all-family claims blocked;
- do not promote a larger architecture before support/contact scope is repaired.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

Current compatibility dataset v3 independent validity support contact balancing plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_ready_for_materialization
selected_path = materialize_support_contact_primary_independent_validity_with_shortcut_audit
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```

Decision:

The support/contact blocker is not that the family lacks independent-validity capacity. The blocker
is that the previous exact predicate-class balance is too strict for this family:

```text
exact predicate-class support/contact rows = 88
lying on exact rows = 64
standing on exact rows = 24
```

At predicate level, support/contact has enough train-side GT-anchored independent-validity capacity:

```text
support/contact family scan-capped capacity = 2134
lying on scan-capped capacity = 1370
standing on scan-capped capacity = 764
```

Therefore the selected target is a predicate-balanced support/contact independent-validity
materialization contract:

```text
target rows = 1200
minimum rows = 800
lying on = 600 rows, 300/300 positive/negative
standing on = 600 rows, 300/300 positive/negative
```

This keeps the target GT-anchored while relaxing exact predicate-class balance. The relaxation is
not free: the next materializer must enforce class-pair, scan, directed-pair, and rank-band caps,
then run schema shortcut audit before any learned smoke.

Rejected alternatives:

- exact predicate-class balance as the main support/contact target, because it only gives `88` rows;
- pose-conditioned constructed target as main independent-validity evidence, because it is auxiliary
  `C_e` mechanism evidence rather than independent GT-anchored validity;
- larger architecture before support/contact-primary candidate materialization and shortcut audit;
- calibrated `p_rel` / `p_obs` claim before held-out/Docker/selective-decision gates.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```

Current compatibility dataset v3 independent validity support contact balancing candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next = compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```

Result:

The support/contact-primary independent-validity candidate set was materialized successfully:

```text
rows = 1200
positive / negative = 600 / 600
lying on = 300 positive + 300 negative
standing on = 300 positive + 300 negative
```

The materializer streamed the full train match rows:

```text
scanned rows = 4,818,996
support/contact family rows = 370,692
primary candidate rows = 8,631
lying on candidates = 1,643 positive / 685 negative
standing on candidates = 5,921 positive / 382 negative
```

The relaxed predicate-level balance did not create an immediate distribution-cap failure:

```text
max single scan share = 0.0108 <= 0.05
max single directed-pair share = 0.0017 <= 0.01
max single class-pair share = 0.0167 <= 0.10
max single rank-band share = 0.4017 <= 0.55
```

Schema precheck passed with zero forbidden construction-key hits in both model-safe view and feature
blocks. This fixes the support/contact row-count blocker, but it does not yet prove learned
compatibility. Because exact predicate-class balance was relaxed, the next mandatory step is schema
shortcut audit.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit
```

Current compatibility dataset v3 independent validity support contact balancing schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit_blocked_shortcut_risk
validation_errors = 1
next = compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

Result:

The schema audit did not find direct leakage from blocked construction fields into the sanitized
model view:

```text
sanitized_blocked_feature_path_hits = 0
model_feature_blocked_key_hits = 0
```

The target is still globally and predicate-internally balanced:

```text
rows = 1200
positive / negative = 600 / 600
lying on = 300 / 300
standing on = 300 / 300
```

However, the shortcut audit blocks learned smoke because allowed semantic class fields remain too
predictive:

```text
subject_class_label       accuracy = 0.804167  risk = medium
object_class_label        accuracy = 0.785000  risk = medium
subject_object_class_pair accuracy = 0.920000  risk = medium
predicate_x_class_pair    accuracy = 0.975833  risk = high
```

By contrast, source-confidence probes and raw-geometry single-field probes did not trigger
medium/high warnings:

```text
source_confidence_high_or_medium_risk = 0
raw_geometry_high_or_medium_risk = 0
```

Interpretation:

The support/contact row-count blocker has been fixed, but the relaxed predicate-level target still
has object-class composition shortcut risk. A learned smoke run on this view could overstate H002 by
learning class priors instead of `compatibility(T_e, G_e)`. The next step is a path decision: stronger
class-pair balancing or within-class contrast, object-class masking for a diagnostic smoke, or
diagnostic-only freeze.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit
```

Current compatibility dataset v3 independent validity support contact class pair repair capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_blocked_class_pair_diagnostic_possible
validation_errors = 1
next = compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

Purpose:

This stage tested the first-choice repair after support/contact shortcut audit: stronger class-pair
and within-class contrast. The strict desired condition is mixed accept/reject inside exact
`predicate + subject_class + object_class` strata.

Input capacity:

```text
scanned rows = 4,818,996
support/contact family rows = 370,692
primary support/contact candidate rows = 8,631
lying on positive / negative = 1,643 / 685
standing on positive / negative = 5,921 / 382
```

Repair capacity:

```text
class_pair mixed groups = 50
class_pair scan-capped capacity = 426

predicate_x_class_pair mixed groups = 13
predicate_x_class_pair scan-capped capacity = 88

predicate_x_class_pair_x_rank_band mixed groups = 18
predicate_x_class_pair_x_rank_band scan-capped capacity = 88
```

Strict predicate-class capacity by predicate:

```text
lying on scan-capped capacity = 64
standing on scan-capped capacity = 24
```

Interpretation:

The first-choice strict repair is not viable for a main support/contact learned-smoke target. It is
too small overall and especially too sparse for `standing on`. Relaxed `subject_class + object_class`
contrast has `426` scan-capped rows, but it cannot fully remove `predicate_x_class_pair` shortcut
risk, so it should be treated as diagnostic-only if used.

Next:

```text
compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan
```

Current compatibility dataset v3 independent validity support contact class pair repair path decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_freeze_independent_validity_diagnostic
selected_path = freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis
validation_errors = 0
next = compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze
```

Decision:

Support/contact independent-validity is frozen as diagnostic-only. The strict predicate-class repair
route is rejected because exact `predicate + subject_class + object_class` capacity is only `88`
scan-capped rows:

```text
lying on strict capacity = 64
standing on strict capacity = 24
```

The relaxed `subject_class + object_class` route has `426` scan-capped rows, but it does not control
`predicate_x_class_pair`, so it cannot repair the exact shortcut that blocked the previous target.
The object-class-masked route is also diagnostic-only because it removes part of deployable `T_e`.

Implication:

- do not run a main support/contact independent-validity learned smoke from the current
  Open3DSG train-side construction;
- retain support/contact as diagnostic evidence and scoped pose-conditioned `C_e` mechanism evidence;
- synthesize the current H002 scope around clean main evidence, diagnostic support/contact evidence,
  calibration blockers, and future target-source requirements.

Next:

```text
compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze
```

Current compatibility dataset v3 scope synthesis after support/contact independent-validity freeze:

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_ready
selected_path = freeze_current_scope_select_independent_target_source_decision
validation_errors = 0
next = compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

Synthesis:

The current H002 claim is now scoped to train-only predicate-conditioned compatibility `C_e`.
Semantic/source evidence and predicate-independent geometry are insufficient by themselves, while
`C_e = compatibility(T_e, G_e)` separates valid and invalid candidates on the exact-stratum repaired
target.

Current family scope:

```text
relative_vertical = main train-only C_e evidence
support_contact_pose_conditioned = scoped constructed C_e mechanism evidence
support_contact_independent_validity = diagnostic-only frozen
attachment_like = deferred
proximity = deferred
```

Main evidence:

```text
model = M6_TG_compatibility_interaction
primary AUROC = 0.9956328125
geometry-only AUROC = 0.5270640625
source-only AUROC = 0.56811015625
wrong-predicate AUROC = 0.02664375
family scope = relative_vertical_dominant
```

Support/contact boundary:

```text
independent-validity status = diagnostic-only frozen
strict predicate_x_class_pair capacity = 88
lying on strict capacity = 64
standing on strict capacity = 24
pose-conditioned status = scoped C_e mechanism evidence only
```

Calibration boundary:

```text
proper train-only probability ECE = 0.04658165053413088
Brier = 0.020503824238432555
calibrated p_rel/p_obs claim allowed = false
```

Interpretation:

The old ECE blocker is downgraded as a helper-definition issue, but H002 still cannot claim a
calibrated reliability posterior because the current target is train-only `C_e`, not held-out
relation reliability with an observability/selective-decision target. The next bottleneck is target
source and external validity, not architecture.

Next:

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

Current compatibility dataset v3 independent target-source decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/
status = h002_compatibility_dataset_v3_independent_target_source_decision_selected
selected_path = select_support_contact_visual_mesh_human_audit_with_size_containment_probe
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

Decision:

The next H002 route is not broad relation-type expansion and not immediate `relative_vertical`
Docker promotion. The selected main route is a support/contact human/visual/mesh audit target
source over:

```text
lying on
standing on
supported by
```

Reason:

- `relative_vertical` is the cleanest current train-only `C_e` evidence, but it is too narrow to
  resolve the independent relation-reliability target-source blocker.
- `support_contact` has enough raw family mass and mesh/pose/contact evidence, but the current
  Open3DSG train-side independent-validity target is shortcut-prone.
- The next experiment must create independent labels for `C_e`, `Q_e`, `p_obs`, and `p_rel` from
  visual/mesh evidence, then audit shortcut risk before any learned smoke.

Additional relation types:

```text
size_relative = bigger than / smaller than, optional feasibility probe
containment_inclusion = standing in / lying in / build in / part of / belonging to / cover / hanging in, high-risk optional probe
leaning against = future physical probe after mesh/pose schema
left/right/front/behind = deferred because of reference-frame ambiguity
same as / same symmetry as = not recommended for H002 main
```

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

Current support/contact visual/mesh audit target plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory
selected_path = plan_visual_mesh_audit_target_source_before_materialization
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

This plan fixes the independent target contract for `lying on`, `standing on`, and `supported by`
before any row materialization. The audit label source is visible visual/mesh evidence; source
score, rank, queue kind, old `geometry_status`, old `p_geom_valid`, and GT-missing status are
hidden from label creation.

Main target interpretation:

```text
C_e = predicate-geometry compatibility from T_e and predicate-independent G_e
Q_e = evidence quality / observability
p_obs = whether current evidence supports accept/reject judgment
p_rel = accept vs reject only after p_obs = 1
```

The planned audit target uses mixed strata rather than positive-only mining:

```text
target_total_rows = 480
minimum_total_rows = 360
minimum_per_predicate = 80
minimum_accept/reject/abstain = 80/80/60
```

Important boundary:

```text
No-GT is not a negative label.
supported by is broad/superordinate, not a clean binary negative for standing on.
```

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

Current support/contact visual/mesh audit source inventory:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization
selected_path = source_inventory_ready_packet_materialization_required
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

The source inventory selected 480 train-only rows under the fixed audit contract.

```text
lying on = 194
standing on = 156
supported by = 130
hidden queue kind = HL 112 / LH 368
hard surface rows = 90
all required raw sources exist = true
```

Cap gates passed:

```text
max scan rows = 4 <= 24
max subject-object class-pair rows = 13 <= 48
max directed-pair rows = 2 <= 2
hard-surface rows = 90 <= 288
hidden HL rows = 112 >= 60
```

The output is not label-ready yet. It is packet-materialization-ready: the visible sheet contains
`PACKET_PENDING/...` paths, while the hidden manifest stores source score/rank, queue kind,
`geometry_status`, `p_geom_valid`, label-match status, and construction stratum for later shortcut
audit.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

Current support/contact visual/mesh audit packet materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill
selected_path = packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

All 480 selected rows now have reviewer-facing packet assets.

```text
ready rows = 480
non-ready rows = 0
visible leakage hits = 0
lying on / standing on / supported by ready = 194 / 156 / 130
subject image rows = 480
object image rows = 480
pair crop rows = 480
mesh render rows = 480
multiview sheet rows = 480
```

The visible sheet is now label-ready:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/visible_review_sheet_with_packets.csv
```

Boundary: `mesh_contact_render.png` is currently a reviewer-facing mesh/geometry availability card,
not a full 3D contact-surface render. Hidden source score/rank, queue kind, old `geometry_status`,
old `p_geom_valid`, label-match status, construction bucket, prediction id, subject id, and object id
remain outside the visible sheet.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill
```

Current support/contact visual/mesh audit label fill:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_user_requested
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion
```

Label provenance:

```text
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
used_hidden_manifest = false
used_source_score_or_rank = false
used_old_geometry_status_or_p_geom_valid = false
```

Label counts:

```text
rows = 480
accept = 208
reject = 161
abstain = 111
observability sufficient = 480
```

By predicate:

```text
lying on = accept 53 / reject 87 / abstain 54
standing on = accept 73 / reject 63 / abstain 20
supported by = accept 82 / reject 11 / abstain 37
```

This is a user-requested Codex proxy label fill, not an independent blind human audit. It is useful
for the next H002 target-ingestion and shortcut-audit step, but it should not be framed as final
human-label evidence.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

Current support/contact visual/mesh class-pair repair path decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next = compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

Decision:

```text
run learned smoke on current repair target = reject
generic-endpoint filtered target = reject as main / optional diagnostic only
stricter within-predicate-class relabel = not a clean continuation of current proxy artifact
freeze support/contact visual-mesh class-pair repair = selected
```

Key evidence:

```text
p_rel/C_e binary rows = 304
p_rel/C_e binary counts = positive 198 / negative 106
predicate_x_class_pair p_rel majority accuracy = 1.0000
hidden predicate_class_pair p_rel majority accuracy = 1.0000
generic_endpoint_visible relation-multiclass majority accuracy = 0.6208
non-generic filtered predicate_x_class_pair p_rel majority accuracy = 1.0000
```

Interpretation:

The class-pair repair solved a row-mass problem but not the more important
target-identifiability problem. The current support/contact visual/mesh proxy
labels are too aligned with `predicate + class-pair` to serve as main `C_e` or
`p_rel` evidence. Therefore this branch preserves the result as diagnostic
evidence and avoids forcing a learned smoke test that would mainly prove the
shortcut.

Updated H002 boundary:

```text
relative_vertical = clean train-only C_e anchor
support/contact pose-conditioned target = scoped C_e mechanism evidence
support/contact visual/mesh class-pair repair = diagnostic negative result
calibrated p_rel / p_obs = still blocked
paper-level claim = not allowed
```

Next:

```text
compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

Current all-relation-family scope synthesis after support/contact visual/mesh diagnostic freeze:

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready
selected_path = all_relation_family_generalization_scan_with_proximity_first
validation_errors = 0
next = compatibility_dataset_v3_relation_family_generalization_capacity_scan
selected_first_active_family = proximity
selected_first_active_predicates = close by
```

Decision:

```text
run all relation-type model now = reject
all relation-family capacity scan = selected
proximity / close by first = selected
support/contact individual predicate scan = defer after proximity or parallel diagnostic
main claim only on successful families = reject as framing
```

The right paper-level framing is not to hide failed relation types. H002 should
define the same target-identifiability gates for all relation families, then use
passing families as main evidence and failing families as failure taxonomy /
claim-boundary evidence.

Priority:

```text
1. proximity / close by: GT 12300, H002 queue 171324
2. support_contact individual predicates: GT 12600, H002 queue 161498
3. relative_vertical: already clean C_e anchor, GT 3552, H002 queue 124604
4. size_relative: optional quick probe, GT 1822
5. containment_in: optional schema probe, GT 330
6. attachment_deferred: visual/mesh-heavy, GT 8767
7. relative_horizontal: reference-frame ambiguity, GT 36944
8. identity_symmetry / part_structural: diagnostic/defer
```

Important clarification:

Grouped support/contact failure does not prove that `standing on`, `lying on`,
and `supported by` each fail. The current visual/mesh class-pair repair showed
that the grouped proxy target is shortcut-prone. Individual predicate scans
remain valid follow-up probes, especially for `lying on` and `standing on`,
which already have pose-conditioned `C_e` mechanism evidence.

Next:

```text
compatibility_dataset_v3_relation_family_generalization_capacity_scan
```

Current relation-family generalization capacity scan:

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan/
status = h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready
selected_path = select_proximity_close_by_target_plan_with_all_family_eligibility_table
validation_errors = 0
next = compatibility_dataset_v3_proximity_close_by_target_plan
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

`close by` is the right next active family because it has enough row mass and
class-pair mixing. However, it is LH-only in the current queue. Therefore the
next target plan must avoid treating all no-GT pairs as negative and must include
distance-only controls. Otherwise H002 would collapse into a trivial proximity
verifier rather than predicate-geometry compatibility learning.

Support/contact individual predicates remain possible:

```text
standing on = queue 50245 / exact 5871 / mixed class-pair groups 96
lying on = queue 60652 / exact 1440 / mixed class-pair groups 75
supported by = queue 50601 / exact 491 / mixed class-pair groups 105
```

Grouped support/contact visual/mesh failure should therefore be read as a
grouped proxy-target failure, not as proof that every support/contact predicate
is impossible.

Next:

```text
compatibility_dataset_v3_proximity_close_by_target_plan
```

Current proximity close-by target plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_target_plan/
status = h002_compatibility_dataset_v3_proximity_close_by_target_plan_ready_for_source_inventory
selected_path = plan_close_by_source_inventory_for_near_far_hard_negative_target
validation_errors = 0
next = compatibility_dataset_v3_proximity_close_by_source_inventory
```

Full train close-by snapshot:

```text
close_by_rows = 185346
label_match_status = no_gt_for_pair 142571 / pair_has_other_predicate 33247 / exact_match 9528
geometry_status = satisfied 171326 / uncertain 7328 / unsatisfied 6692
rank_band = rank_gt1000 133872 / rank_501_1000 42864 / rank_201_500 8596 / rank_101_200 12 / top50 2
```

Interpretation:

The `close by` direction is viable enough to continue, but it must be framed as
a controlled proximity target, not as a no-GT-vs-GT classifier. `exact_match`
rows are positive-anchor candidates. `no_gt_for_pair` and
`pair_has_other_predicate` are not negative labels because proximity annotations
can be incomplete and dense. The next source inventory must mine scale-aware far
negatives and ambiguous rows from full train geometry, then check class-pair,
rank/source, and distance-only shortcuts.

The required controls are:

```text
semantic_only_T
source_only_Z
geometry_only_G
distance_only
T_plus_G_compatibility
p_geom_valid_rule
shuffled_geometry
wrong_pair_geometry
same-distance matched subset
```

Support/contact remains deferred to individual predicate probes after this
close-by inventory path:

```text
standing on
lying on
supported by
```

Next:

```text
compatibility_dataset_v3_proximity_close_by_source_inventory
```

Current proximity close-by source inventory:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory/
status = h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan
selected_path = select_close_by_candidate_materialization_plan_with_far_geometry_negatives_and_controls
validation_errors = 0
next = compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

Candidate inventory:

```text
close_by_rows = 185346
accept_anchor = 8682
reject_far_geometry = 6688
abstain_or_audit = 169972
gt_geometry_conflict = 4
near / ambiguous / far = 113280 / 58046 / 14020
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

The close-by path has enough source capacity for a controlled candidate
materialization plan. The reject pool is geometry-defined:

```text
label_match_status != exact_match
geometry_status == unsatisfied
normalized_distance_xy >= 2.5
```

Therefore it is not a naive `no_gt_for_pair = reject` target. However,
normalized-distance matched accept/reject capacity is zero, so `close by` has a
real distance-threshold risk. Any later smoke must include `distance_only`,
`p_geom_valid_rule`, class-pair/source baselines, shuffled geometry, wrong-pair
geometry, and a smaller raw-distance matched diagnostic subset.

Next:

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

Current proximity close-by candidate materialization plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready
selected_path = materialize_close_by_controlled_candidates_with_distance_controls
validation_errors = 0
warnings = 2
next = compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

Planned rows:

```text
planned_total_rows = 1284
primary_binary_rows = 800
  accept_anchor = 400
  reject_far_geometry = 400
abstain_qe_rows = 240
raw_distance_diagnostic_rows = 240
gt_geometry_conflict_audit_rows = 4
```

Required caps:

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

The close-by candidate path is feasible, but it is not yet a method result.
Because normalized-distance matched capacity is zero, `close by` can easily look
good by learning distance separation. Therefore the next materialized dataset
must preserve `distance_only`, `p_geom_valid_rule`, and raw-distance diagnostic
controls. Since many reject candidates still have `no_gt_for_pair` status, no-GT
and target-construction fields must remain hidden controls, not model inputs.

Next:

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

Current proximity close-by candidate materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization/
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next = compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit
```

Materialized rows:

```text
total_rows = 1284
primary_binary_rows = 800
raw_distance_diagnostic_rows = 240
abstain_qe_rows = 240
gt_geometry_conflict_audit_rows = 4
```

Precheck result:

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

Current proximity close-by schema shortcut audit:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut
validation_errors = 0
critical_blockers = 5
learned_smoke_allowed = false
main_claim_verdict = blocked_for_close_by_current_target
next = compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

Critical blockers:

```text
primary_binary normalized_distance_xy = acc 1.000000 / AUROC 1.000000
primary_binary normalized_distance_3d = acc 1.000000 / AUROC 1.000000
primary_binary distance_xy = acc 0.992500 / AUROC 0.999556
primary_binary distance_3d = acc 0.987500 / AUROC 0.998975
primary_binary p_geom_valid_rule = acc 0.991250 / AUROC 0.999594
```

Interpretation:

`close by` is currently a diagnostic proximity-family artifact, not a main H002
claim. The schema is clean, but the target is solved by distance and rule-based
geometry baselines. A learned compatibility model would not prove more than
`distance_only` or `p_geom_valid_rule` on this target. Therefore the next step is
path decision, not smoke.

Next:

```text
compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

Current proximity close-by path decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe
selected_path = freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe
validation_errors = 0
next = compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

Decision:

`close by` current target is frozen as diagnostic/generality evidence. It is not
used for learned smoke or the main H002 claim.

Why:

```text
normalized_distance_xy primary acc/AUROC = 1.000000 / 1.000000
normalized_distance_3d primary acc/AUROC = 1.000000 / 1.000000
distance_xy primary acc/AUROC = 0.992500 / 0.999556
distance_3d primary acc/AUROC = 0.987500 / 0.998975
p_geom_valid_rule primary acc/AUROC = 0.991250 / 0.999594
```

This means the current target tests distance thresholding, not `T_e-G_e`
compatibility learning. Stronger neural fusion would not fix this target
identifiability problem.

Next support/contact individual predicate priority:

```text
1. standing on = primary individual probe, queue 50245, exact 5871
2. lying on = secondary pose-conditioned probe, queue 60652, exact 1440
3. supported by = diagnostic superordinate probe, queue 50601, exact 491
```

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

Current support/contact individual predicate probe plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory
selected_path = plan_individual_support_contact_source_inventory_standing_primary_lying_secondary_supported_diagnostic
validation_errors = 0
next = compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

Decision:

```text
standing on = primary individual probe
lying on = secondary pose-conditioned probe
supported by = diagnostic superordinate probe
```

Why:

- grouped support/contact visual/mesh target remains diagnostic-only because
  predicate/class-pair/source shortcut risk was high.
- pose-conditioned `lying on` / `standing on` same-G result remains useful as a
  scoped `C_e` mechanism prior, but it is not independent `p_rel/p_obs`
  reliability evidence.
- `supported by` overlaps with standing/lying support states, so it is not a
  clean negative label for `standing on`.

Predicate capacity:

```text
standing on = queue 50245, exact 5871, mixed class-pair groups 96
lying on = queue 60652, exact 1440, mixed class-pair groups 75
supported by = queue 50601, exact 491, mixed class-pair groups 105
```

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

Current support/contact individual predicate source inventory:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_standing_lying_individual_predicate_cells_supported_by_diagnostic
validation_errors = 0
next = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

Answer:

Yes. Support/contact is now handled per relation type:

```text
standing on = primary individual probe
lying on = secondary individual / pose-conditioned probe
supported by = diagnostic superordinate probe
```

Source inventory:

```text
standing on = 50245 rows, class-pair balanced rows 382, mixed groups 13
lying on = 60652 rows, class-pair balanced rows 414, mixed groups 13
supported by = 50601 rows, class-pair balanced rows 164, mixed groups 45
```

Same-G anchor capacity:

```text
predicted same-pair standing+lying pairs = 35504
previous pose-conditioned classified anchors = 4031
previous selected balanced pose-conditioned anchors = 200
```

Decision:

- `standing on` and `lying on` proceed to candidate materialization plan.
- `supported by` remains diagnostic, not a clean negative for `standing on`.
- Hard-surface shortcut is high across all three predicates, so materialization must cap/stratify
  floor/table/wall-like endpoint pairs.

Next:

```text
compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

Current support/contact visual/mesh class-pair repair label ingestion:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_class_pair_repair_labels_run_shortcut_diagnostics
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
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

The class-pair repair improved binary row mass but did not solve target
identifiability. The current visible-label policy still maps `predicate +
class-pair` too directly to the proxy target. Generic endpoints are mostly an
abstain/multiclass shortcut rather than a binary `p_rel` shortcut.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion
```

Current support/contact visual/mesh class-pair repair label fill:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_for_class_pair_repair_user_requested
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

Label provenance:

```text
label_provenance = codex_visible_packet_proxy_labeler_user_requested
independent_human_audit = false
used_hidden_manifest = false
used_source_score_or_rank = false
used_old_geometry_status_or_p_geom_valid = false
used_label_match_status = false
```

Label counts:

```text
rows = 480
accept / reject / abstain = 198 / 106 / 176
lying on = accept 47 / reject 45 / abstain 68
standing on = accept 52 / reject 46 / abstain 62
supported by = accept 99 / reject 15 / abstain 46
observability sufficient = 480
```

Generic endpoint risk:

```text
generic_endpoint_rows = 100
generic_endpoint_labels = abstain 100
non_generic_labels = accept 198 / reject 106 / abstain 76
```

This fill completed the visible-packet label step for the class-pair repair
candidate set. The next step must join hidden fields after label lock and audit
whether the repair actually reduced class-pair/generic endpoint shortcuts.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

Current support/contact visual/mesh class-pair repair packet materialization:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill
selected_path = class_pair_repair_packet_assets_materialized_visible_sheet_ready_for_label_fill
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
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

The visible sheet for the next label fill is:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/visible_review_sheet_with_packets.csv
```

`repair_proxy_kind` remains hidden and sampling-only. The next step is to fill
labels from the visible packet fields only, then ingest the locked labels and
rerun class-pair/shortcut diagnostics.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill
```

Current support/contact visual/mesh audit path decision after label ingestion:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization
selected_path = class_pair_controlled_repair_first
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

The previous 480-row label target had enough binary mass but almost no exact
class-pair-controlled mixed target:

```text
class_pair mixed groups = 1
class_pair balanced rows = 2
predicate_x_class_pair mixed groups = 0
predicate_x_class_pair balanced rows = 0
```

Full train support/contact repair capacity is sufficient:

```text
source = train_hl_queue.jsonl + train_lh_queue.jsonl
source_rows_after_proxy_filter = 27201
predicate_x_class_pair mixed groups = 71
predicate_x_class_pair balanced raw rows = 960
validation/test used = false
```

Selected repair candidates:

```text
selected_rows = 480
lying on / standing on / supported by = 160 / 160 / 160
accept_like / reject_like = 240 / 240
each predicate x proxy-kind cell = 80
predicate_class_pair_groups = 68
max_scan_rows = 11
max_directed_pair_rows = 1
hard_surface_rows = 252
required_source_file_errors = 0
```

This keeps support/contact inside H002 without overclaiming the previous shortcut
target. The selected candidates are not final labels; `repair_proxy_kind` is used
only for sampling. The next step must materialize visible packets and refill
labels before any target ingestion or learned smoke.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

Current support/contact visual/mesh audit label ingestion:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_proxy_labels_run_independence_diagnostics_block_smoke_if_shortcut
validation_errors = 0
next = compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

Targets:

```text
rows = 480
relation multiclass = accept 208 / reject 161 / abstain 111
p_rel binary rows = 369
p_rel positive/negative = 208 / 161
C_e binary rows = 369
C_e positive/negative = 208 / 161
p_obs = all 480 positive
Q_e = all 480 sufficient
```

Shortcut audit result:

```text
learned_smoke_allowed = false
subject_object_class_pair p_rel majority accuracy = 0.9973
construction_bucket_hidden p_rel majority accuracy = 0.9106
label_match_status_hidden p_rel majority accuracy = 0.8726
object_label p_rel majority accuracy = 0.8428
```

The artifact solved the binary row-count problem but not the target-identifiability
problem. `p_rel` and `C_e` have enough accept/reject mass, but the proxy labels are
too correlated with class-pair and construction/source strata. Therefore this
stage is a diagnostic target artifact, not a learned-smoke input. `p_obs` and
`Q_e` also cannot be claimed here because every row is observable.

Next:

```text
compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

## 2026-06-29 Support/Contact Individual Predicate Candidate Materialization Plan Update

`support/contact` individual predicate candidate materialization plan을 실행했고, route-aware
materialization으로 진행 가능하다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_ready
selected_path = materialize_route_aware_standing_lying_candidates_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization
```

Planned rows:

```text
standing on = 160 clear_accept + 160 hard_reject_lying_like
lying on = 160 clear_accept + 160 hard_reject_standing_like
supported by diagnostic = 40 clear_accept + 40 hard_reject_no_support + 80 overlap_or_abstain
main compatibility rows = 640
diagnostic rows = 160
total rows = 800
```

Gate result:

```text
standing_class_pair_capacity = 382 / 320
lying_class_pair_capacity = 414 / 320
supported_by_diagnostic_capacity = 164 / 80
planned_total_rows = 800 / 800
supported_by_not_main_target = diagnostic_only
```

해석:

- `standing on`과 `lying on`은 compatibility-ready relation으로 실제 row materialization을 진행한다.
- `supported by`는 support/contact family coverage를 위한 diagnostic relation으로 유지한다.
- 이 단계는 plan만 생성했으며 row materialization, label fill, learned smoke, validation/test 사용은 없다.
- 다음 단계는 실제 800-row candidate materialization과 model-safe/hidden manifest 생성이다.

## 2026-06-29 Support/Contact Individual Predicate Candidate Materialization Update

`support/contact` individual predicate candidate materialization을 실행했고, 800-row train-only
candidate artifact를 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_route_aware_standing_lying_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit
```

Materialized rows:

```text
total_rows = 800
main_compatibility_rows = 640
diagnostic_rows = 160
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

중요한 caveat:

```text
max_rows_per_predicate_class_pair: plan 32 -> actual 200
max_rows_per_predicate_class_pair_rank: plan 24 -> actual 80
max_hard_surface_rows: plan 360 -> actual 640
```

해석:

- planned quota는 모두 채웠다.
- `G_e`는 H001 `p_geom_valid`가 아니라 semseg OBB 기반 mesh/pose/contact feature로 계산했다.
- `supported by`는 여전히 diagnostic이다.
- 다만 class-pair/rank/hard-surface cap relaxation이 필요했으므로 learned smoke는 아직 금지한다.
- 다음 단계는 schema/shortcut audit이며, 여기서 class-pair-only, rank/source-hidden,
  hard-surface-only, `T_only`, `G_only`, route-rule baseline을 먼저 검사해야 한다.

## 2026-06-29 Support/Contact Individual Predicate Schema Shortcut Audit Update

`support/contact` individual predicate schema/shortcut audit를 실행했고, sanitized-view smoke
plan으로 진행 가능하다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan
selected_path = schema_clean_allowed_shortcuts_low_hidden_construction_risk_reported
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan
```

Audit result:

```text
main_binary_rows = 640
diagnostic_rows = 160
sanitized_rows = 640
schema_leakage_hits = 0
allowed_high_risk_probes = 0
hidden_high_risk_probes = 2
```

Key shortcut probes:

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

High-risk hidden construction probes:

```text
hidden_label_match_status accuracy = 1.000
hidden_candidate_role accuracy = 1.000
```

해석:

- model-safe view에는 hidden/source/GT/H001 construction field leakage가 없다.
- allowed model-safe shortcut은 high-risk가 아니다.
- hidden construction fields는 label provenance이므로 perfect하게 맞지만 model input에서 제거되어 있다.
- 따라서 learned smoke를 바로 실행하지 않고, 먼저 sanitized-view smoke plan을 작성한다.

## 2026-06-29 Support/Contact Individual Predicate Sanitized View Smoke Plan Update

`support/contact` individual predicate sanitized-view smoke plan을 작성했고, train-only
learned smoke runner로 진행 가능하다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan/
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

Plan:

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

해석:

- `smoke_ready_view.jsonl`에는 `T_e`, `G_e_mesh_pose_contact`, `Q_e`만 feature로 남겼다.
- `source score/rank`, H001 `p_geom_valid`, `label_match_status`, `candidate_role`,
  raw `scan_id`는 model feature에서 제외했다.
- `cv_group_id`는 raw `scan_id`가 아니라 hash된 train-only split metadata다.
- 다음 runner에서 `M4/M5`가 `M2_geometry_only_G`와 거의 같으면 compatibility evidence가
  아니라 geometry-dominance diagnostic으로 낮춘다.

## 2026-06-29 Support/Contact Individual Predicate Sanitized View Smoke Runner Update

`support/contact` individual predicate train-only smoke runner를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner/
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

해석:

- semantic/class/quality shortcut은 낮다.
- geometry-only dominance도 아니다.
- predicate-geometry interaction은 `T_e`, `G_e`, `T+G`보다 개선된다.
- 하지만 primary AUROC `0.6316`은 planned gate `0.70`보다 낮으므로 main evidence가 아니라
  diagnostic evidence로 둔다.
- `Q_e`는 모든 row가 `mesh=True`, `point=False`, `view=False`라서 성능 변화가 없다.
- 다음 단계는 failure analysis이며, 현재 semseg OBB evidence만으로는 `standing on`/`lying on`
  compatibility를 충분히 분리하지 못하는 원인을 확인해야 한다.

## 2026-06-29 Support/Contact Individual Predicate Failure Analysis Update

`support/contact` individual predicate failure analysis를 실행했고, 현재 semseg OBB-only 결과는
diagnostic으로 고정한 뒤 point/multiview evidence plan으로 진행하기로 했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_ready_select_point_multiview_evidence_plan
selected_path = freeze_obb_only_diagnostic_select_point_multiview_evidence_plan
rows = 640
errors = 267
false_positive / false_negative = 144 / 123
high_confidence_errors = 12
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan
```

Failure profile:

```text
label_match_status = family_match: rows 320, error_rate 0.4500
label_match_status = exact_match:  rows 320, error_rate 0.3844
worst class pairs = shoes->floor, item->floor, picture->floor
best error feature AUC = subject_major_axis_upness 0.5705
Q_e profile = mesh=True|point=False|view=False for all 640 rows
```

해석:

- current support/contact individual predicate branch는 shortcut collapse가 아니다.
- geometry-only dominance도 아니다.
- 문제는 OBB pose/contact evidence가 `standing on`과 `lying on`을 충분히 분리할 만큼
  세밀하지 않다는 점이다.
- `family_match` negative는 물리적으로 불가능한 relation이라기보다 fine-grained predicate
  mismatch라서 label tightening이 필요할 수 있다.
- 따라서 stronger combiner를 먼저 넣지 말고, point/multiview evidence와 label review를 먼저 계획한다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Evidence Plan Update

`support/contact` individual predicate point/multiview evidence plan을 작성했고, 다음 단계는
source inventory로 고정했다. 이 단계는 feature extraction이나 learned smoke가 아니라
`G_e`와 `Q_e`를 분리한 evidence contract를 정의하는 단계다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan/
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

계획:

- `standing on`: upright pose, bottom contact, support surface below를 중심으로 `G_e`를 확장한다.
- `lying on`: horizontal pose, broad/elongated contact, support surface overlap을 중심으로 `G_e`를 확장한다.
- `supported by`: broad support/superordinate boundary 때문에 diagnostic-only로 유지한다.
- multiview crop은 audit label quality와 `Q_e` 판단에 먼저 사용하고, 즉시 learned visual input으로 넣지 않는다.
- promotion gate는 source inventory readiness, non-constant `Q_e`, clean factor boundary,
  grouped-CV AUROC `>= 0.70`, wrong-pair/shuffled-geometry/wrong-view controls로 둔다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Source Inventory Update

Point/multiview source inventory를 실행했고, 800개 train-only 후보 row가 모두
point/mesh/multiview materialization-ready임을 확인했다. 이 결과는 learned smoke를
허용한다는 뜻이 아니라, `G_e`와 `Q_e`를 분리한 materialization plan으로 넘어갈 수
있다는 뜻이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory/
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

`Q_e`는 이전 OBB-only smoke와 달리 non-constant하게 구성 가능하다.

```text
limited = 419
sufficient = 373
uncertain_or_low_observability = 8
```

주요 `Q_e` reason:

```text
low_semseg_segment_count = 345
low_crop_score = 98
few_cropped_instance_views = 60
```

해석:

- point-pair crop, mesh contact patch, multiview packet은 모두 source-ready다.
- 다음 단계는 feature extraction 자체가 아니라 materialization plan이다.
- visual/multiview는 계속 audit/`Q_e` first이며, learned visual input은 아직 금지한다.
- materialization 이후에는 OBB-only / point-only / mesh-contact-only / wrong-pair /
  shuffled-geometry / wrong-view / shuffled-view controls가 필요하다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Materialization Plan Update

Point/multiview materialization plan을 작성했고, 다음 단계는 실제 materialization이다. 이
단계는 learned smoke가 아니라 `G_e`와 `Q_e`를 분리한 model-safe artifact를 만드는
단계다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_ready
selected_path = plan_gq_separated_materialization_with_controls
rows = 800
main_rows = 640
diagnostic_rows = 160
Q_e states = limited 419 / sufficient 373 / uncertain_or_low_observability 8
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```

고정한 feature blocks:

```text
T_e
G_e_obb_baseline
G_e_point_pose
G_e_contact_patch
Q_e_observability
V_mv_audit_manifest
Z_e_safe
```

고정한 controls:

```text
OBB-only baseline
point-only ablation
mesh/contact-only ablation
wrong-pair geometry
shuffled geometry global / within predicate
wrong-view
shuffled-view
class-pair/rank/source shortcut probe
```

해석:

- 다음 단계는 `model_safe_view.jsonl`, `source_manifest.jsonl`, `visual_audit_manifest.jsonl`,
  `control_manifest.jsonl`, `feature_stats.json`을 실제로 만드는 것이다.
- visual/multiview learned embedding은 여전히 금지한다.
- source paths, scan ids, candidate role, label-match status, GT ids, H001 `p_geom_valid`,
  source score/rank는 `C_e` model-safe input에서 제외한다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Materialization Update

Point/multiview materialization을 실행했고, 실제 `G_e`/`Q_e` separated artifact를 만들었다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/
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

생성한 artifact:

```text
model_safe_view.jsonl = 800 rows
source_manifest.jsonl = 800 rows
visual_audit_manifest.jsonl = 800 rows
control_manifest.jsonl = 800 rows
feature_stats.json = finite/range audit
validation_errors.jsonl = 0 rows
```

해석:

- OBB-only branch에서 부족했던 point-derived pose/contact proxy와 non-constant `Q_e`를 붙였다.
- `G_e`에는 predicate/source score/target construction field를 넣지 않았다.
- `Q_e`는 evidence availability와 observability만 담고 relation truth를 직접 담지 않는다.
- multiview는 learned visual feature가 아니라 audit/`Q_e` metadata다.
- `supported by`는 계속 diagnostic-only다.
- 다음 단계는 schema/shortcut audit다. 여기서 raw point/contact feature나 `Q_e` state만으로
  target이 쉽게 맞으면 learned compatibility smoke를 진행하지 않는다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Schema Shortcut Audit Update

Point/multiview materialized dataset의 schema/shortcut audit를 실행했고, smoke planning으로
넘길 수 있는 상태가 됐다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit/
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

주요 결과:

```text
top_allowed_probe = model_T_predicate_x_class_pair
top_allowed_probe_accuracy = 0.684375
top_allowed_probe_risk = low
top_single_geometry_probe_accuracy <= 0.540625
hidden_candidate_role / hidden_label_match_status / hidden_machine_hint = 1.0 high risk
```

해석:

- 허용된 `T_e/G_e/Q_e` model-safe feature만으로는 target을 쉽게 맞추지 못했다.
- 이 결과는 point/contact/observability evidence를 붙인 뒤에도 target이 trivial shortcut이
  아니라는 최소 조건을 통과했다는 뜻이다.
- hidden construction field 3개는 완벽 shortcut이므로 `source_manifest`에만 유지하고, 다음
  smoke plan에서도 금지 field로 둔다.
- 다음은 smoke runner가 아니라 smoke plan이다. model views, controls, gate를 먼저 고정한다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Smoke Plan Update

Point/multiview smoke plan을 작성했고, 다음 단계는 실제 train-only smoke runner다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan/
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

고정한 main comparison:

```text
M1_semantic_only_T
M2_obb_geometry_only
M3_point_pose_only
M4_contact_patch_only
M5_point_contact_geometry
M6_TG_obb_concat
M7_TG_point_contact_concat
M8_TG_point_contact_interaction
M9_TGQ_factorized_observability
```

해석:

- `M8_TG_point_contact_interaction`이 primary compatibility smoke다.
- `M2/M6`은 기존 OBB-only branch와 비교하기 위한 baseline이다.
- `M3/M4/M5`는 point pose와 contact patch 중 어떤 `G_e`가 실제로 기여하는지 보는 ablation이다.
- `M9`은 `Q_e`가 C_e를 보조하는지 확인하는 diagnostic이지, Q_e가 relation truth를 직접 결정하는 모델이 아니다.
- runner 결과에서 `M5` geometry-only가 `M8`과 거의 같으면 compatibility claim이 아니라 geometry-dominance diagnostic으로 낮춘다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Smoke Runner Update

Point/multiview smoke runner를 실행했고, 결과는 near-threshold diagnostic-only다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_diagnostic_only_failed_controls
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
validation_errors = 0
primary_model = M8_TG_point_contact_interaction
M8 AUROC = 0.699375
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis
```

핵심 비교:

```text
M1 semantic-only T = 0.442480
M2 OBB geometry-only = 0.464077
M3 point-pose only = 0.494673
M4 contact-patch only = 0.465952
M5 point+contact geometry-only = 0.470249
M6 old OBB T+G = 0.430010
M7 point/contact T+G concat = 0.434658
M8 point/contact predicate-geometry interaction = 0.699375
M9 T+G+Q observability diagnostic = 0.694619
```

해석:

- `M8`은 semantic-only, OBB-only, point-only, contact-only, point+contact geometry-only,
  old OBB T+G, plain point/contact concat을 모두 크게 넘었다.
- wrong-T control은 `0.273125`, shuffled-G controls는 `0.506240 / 0.463857`로 무너졌다.
  즉 모델이 단순히 row prior나 geometry-only shortcut을 복사한 것은 아니다.
- 하지만 plan에서 고정한 primary gate는 `M8 AUROC >= 0.70`이고, 실제 값은 `0.699375`다.
  gate를 사후 완화하지 않기 위해 diagnostic-only failed-controls로 유지한다.
- predicate slice는 `standing on` `0.707930`, `lying on` `0.692578`이다. 병목은 주로
  `lying on` slice에 있다.
- `M9`이 `M8`보다 낮고 `C4_shuffled_Q`가 거의 동일하므로, 현재 `Q_e`는 truth signal이
  아니라 observability metadata라는 경계를 유지한다.

다음 TODO는 failure analysis다. 특히 `lying on` 오류가 pose ambiguity, point crop quality,
class-pair distribution, thresholding, 또는 current interaction feature 설계 중 어디서 오는지
확인해야 한다.

## 2026-06-29 Support/Contact Point/Multiview Failure Analysis Update

Point/multiview smoke 결과를 failure analysis로 해석했고, internal gate와 paper-facing claim을
분리하는 결론을 확정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_ready_for_result_review
selected_path = keep_internal_near_threshold_diagnostic_use_as_paper_compatibility_route_evidence
rows = 640
errors = 227
false_positive / false_negative = 108 / 119
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position
```

핵심 판단:

- 내부적으로는 `M8 = 0.699375 < 0.70`이므로 near-threshold diagnostic status를 유지한다.
- 논문에서는 `support/contact = main compatibility-route evidence with caveat`로 사용할 수 있다.
- 금지 표현은 `support/contact is fully solved` 또는 `strong absolute support/contact performance`다.
- 허용 표현은 `support/contact requires predicate-geometry interaction; semantic-only, geometry-only,
  and plain concatenation fail, while wrong-T and shuffled-G controls collapse`다.

Failure shape:

```text
lying on AUROC = 0.692578, error_rate = 0.362500
standing on AUROC = 0.707930, error_rate = 0.346875
Q_e sufficient AUROC = 0.772590
Q_e limited AUROC = 0.638494
```

해석:

- `standing on`은 heuristic gate를 넘고, `lying on`이 aggregate를 끌어내린다.
- `Q_e`는 truth signal로 쓰면 안 된다. `M9`이 `M8`보다 낮고 shuffled-Q가 거의 동일하기 때문이다.
- 하지만 `Q_e`는 p_obs/observability axis로는 중요하다. sufficient evidence slice가 limited slice보다
  훨씬 깨끗하다.
- 가장 어려운 class-pair는 `item->floor`, `shoes->floor`, `picture->floor`, `object->floor`로,
  generic/small/thin floor objects에서 pose ambiguity와 observability 문제가 크다.

다음 TODO는 result review and claim position이다. 이 단계에서 support/contact를 H002 paper-facing
relation-aware route table에 어떤 표현으로 넣을지 고정한다.

## 2026-06-29 Support/Contact Point/Multiview Result Review And Claim Position Update

Support/contact point/multiview branch의 paper-facing 위치를 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis
selected_path = paper_position_support_contact_compatibility_route_evidence_with_caveat_keep_internal_near_threshold
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview
```

고정한 claim position:

```text
support/contact = main compatibility-route evidence with caveat
support/contact != fully solved relation family
support/contact != high absolute-performance branch
Q_e != relation truth signal
```

Paper-facing allowed wording:

```text
For support/contact relations, predicate-geometry interaction provides the strongest signal,
while semantic-only, geometry-only, and plain concatenation baselines fail and wrong-predicate
or shuffled-geometry controls collapse.
```

Relation route table:

```text
relative_vertical = main clean mechanism evidence
support_contact = main challenging compatibility-route evidence with caveat
support_contact_superordinate / supported by = diagnostic only
proximity / close by = geometry-easy control, diagnostic/generality
attachment_like = observability-heavy future/diagnostic
relative_horizontal = reference-frame deferred
```

이제 다음 단계는 더 많은 relation type을 추가하는 것이 아니라, 현재 두 main route
(`relative_vertical`, `support_contact`)와 diagnostic/future routes를 하나의 H002 claim
synthesis로 묶는 것이다.

## 2026-06-29 Multi-Family Claim Synthesis After Support/Contact Point/Multiview Update

`relative_vertical`, support/contact point/multiview, proximity diagnostic, attachment deferral을
하나의 H002 paper-framework skeleton으로 묶었다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready
selected_path = freeze_relation_aware_compatibility_routing_claim_select_ablation_table_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis
```

고정한 short claim:

```text
relation-aware predicate-geometry compatibility routing
```

현재 허용되는 claim은 broad relation reliability가 아니라 train-only mechanism claim이다.
`relative_vertical`은 clean `C_e` mechanism evidence이고, `support_contact`는 challenging
compatibility-route evidence with caveat다. `close by`는 geometry-easy diagnostic/generality
control이고, `attachment_like`는 visual/mesh observability-heavy future route다.

Family route table:

```text
relative_vertical = main clean compatibility mechanism
support_contact = main challenging compatibility route with caveat
supported by = diagnostic / superordinate support taxonomy
close by = geometry-easy diagnostic/generality control
attachment_like = observability-heavy future route
relative_horizontal = reference-frame deferred
```

Blocked claims:

```text
paper-level performance
held-out/test relation reliability
all relation-family generality
support/contact fully solved
Q_e as relation truth
final calibrated p_rel/p_obs results
```

다음 단계는 더 많은 relation family를 즉시 추가하는 것이 아니라, 현재 claim skeleton을
main table, ablation, controls, reviewer-risk wording으로 바꾸는 것이다.

## 2026-06-29 Ablation And Table Plan After Multi-Family Synthesis Update

Multi-family claim skeleton을 논문 표와 ablation/control contract로 변환했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_ready
selected_path = freeze_candidate_ablation_contract_select_relation_family_coverage_gap_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan
```

고정한 candidate table/ablation contract:

```text
T1 = Predicate-Geometry Compatibility Mechanism
T2 = Relation-Aware Evidence Routing Taxonomy
T3 = Geometry-Easy and Observability-Heavy Diagnostics
T4 = Claim Boundary and Reviewer Risk
```

필수 ablation:

```text
constant_or_label_prior
T_e semantic content only
Z_e source confidence only
G_e geometry-only
T_e + G_e plain concat
C_e predicate-geometry interaction
C_e + Q_e selective decision
C_e + Q_e + Z_e final p_rel
fixed fusion without route
```

필수 controls:

```text
wrong predicate same geometry
shuffled geometry global
shuffled geometry within predicate/family
class-pair only
source/rank only
distance or p_geom_valid only
Q_e shuffled or Q_e only
scan and endpoint leakage
```

핵심 판단:

- H002의 다음 병목은 relation family 추가가 아니라 paper-level promotion protocol이다.
- `C_e`에는 `Z_e`를 넣지 않는다. Source confidence는 final `p_rel` ablation에만 허용한다.
- `Q_e`는 truth가 아니라 `p_obs`/abstain 축으로 평가한다.
- 현재 artifact는 train-only hypothesis contract이며 paper evidence가 아니다.
- 최종 main table이나 Docker promotion 전에는 남은 relation-family coverage/gap audit이 필요하다.
- 남은 주요 family는 `relative_horizontal`, `attachment_deferred`, `containment_in`,
  `size_relative`, `part_structural`, `identity_symmetry`다.

## 2026-06-29 Relation-Family Coverage Gap Audit After Ablation/Table Plan Update

Candidate table/ablation contract 이후 남은 Open3DSG/3DSSG relation-family gap을 정리했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan/
status = h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready
selected_path = select_size_relative_schema_probe_keep_horizontal_reference_frame_protocol_second
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit
```

핵심 수치:

```text
families = 10
predicates = 29
families_in_current_queue = 3
families_missing_current_queue = 7
gt_total_all_rows = 79704
queue_total_all_rows = 457426
```

Family decisions:

```text
size_relative = next active schema/source-adapter probe
relative_horizontal = high-value gap, reference-frame protocol required first
relative_vertical = current clean anchor
support_contact = caveated compatibility route
proximity = geometry-easy diagnostic/control
attachment_deferred = visual/mesh observability-heavy future route
containment_in = future containment schema
part_structural = diagnostic/out-of-scope for current physical compatibility
identity_symmetry = separate semantic/identity task
```

`size_relative`를 다음 active probe로 선택한 이유는 새 physical relation family이면서 geometry evidence
설계 비용이 낮기 때문이다. `bigger than` / `smaller than`은 object scale, volume, height,
footprint area 기반 `G_e`를 만들 수 있고 predicate-flip compatibility test도 가능하다.
단, geometry-only로 너무 쉽게 풀릴 수 있으므로 same-geometry, predicate-flip, class-pair,
source-rank control이 필요하다.

`relative_horizontal`은 GT mass가 가장 크지만 reference-frame ambiguity 때문에 바로 mining하면 안 된다.
먼저 world/viewer/camera/object-centric frame 중 어떤 protocol을 사용할지 결정해야 한다.

## 2026-06-29 Size-Relative Schema Probe Plan After Coverage Gap Audit Update

Coverage/gap audit에서 선택한 `size_relative` family에 대해 schema/source-adapter probe plan을
고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit/
status = h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_ready
selected_path = size_relative_source_inventory_with_semseg_obb_scale_features
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan
```

Scope:

```text
family = size_relative
predicates = bigger than, smaller than
GT counts = 911 / 911
current_h002_queue_count = 0
```

핵심 schema:

```text
T_e = predicate text/label and optional object class text
G_e_size = OBB/extent/volume/area/height ratios, excluding predicate and source score
Q_e_size = OBB availability and ambiguous-size-band evidence
C_e = compatibility(T_e, G_e_size), excluding Z_e
```

핵심 target idea는 same-G predicate flip이다.

```text
same subject/object geometry
row 1: predicate = bigger than
row 2: predicate = smaller than
```

이 구조에서는 `G_e_size`가 두 row에서 동일하므로 geometry-only가 binary compatibility target을
쉽게 풀면 안 된다. 성능 향상은 `T_e x G_e_size` interaction에서 나와야 한다.

다음 source inventory에서 측정할 것:

```text
bigger/smaller GT anchor counts
scan/object id join rate against semseg.v2.json
pair OBB availability
size-ratio margin distribution
ambiguous-band row count
class-pair and structural-object mass
same-G predicate-flip capacity
```

주의:

- no-GT pair를 false로 쓰지 않는다.
- source/GT/construction label을 model-safe `G_e`에 넣지 않는다.
- size-relative가 geometry-only threshold로만 풀리면 H002 main compatibility evidence가 아니라
  geometry-easy diagnostic으로 내려야 한다.

## 2026-06-29 Size-Relative Source Inventory After Schema Probe Plan Update

Schema/source-adapter plan에 따라 train-side `bigger than` / `smaller than` anchor와
3RScan `semseg.v2.json` OBB join 가능성을 확인했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan/
status = h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready
selected_path = size_relative_inventory_ready_for_candidate_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

핵심 수치:

```text
train_anchor_rows = 1846
bigger than / smaller than = 923 / 923
unique_directed_pair_predicate = 1846
semseg OBB join = 1846 / 1846
volume_compatible / ambiguous / opposes = 1760 / 50 / 36
strict_compatible_unique_flip_groups = 1728
strict_compatible_same_g_predicate_flip_rows = 3456
structural_pair_rows = 0
```

판단:

- `size_relative`는 source/OBB capacity 측면에서 다음 materialization-plan 단계로 진행 가능하다.
- 단순히 `subject volume > object volume` 같은 threshold를 쓰면 geometry-only verifier가 되므로
  H002의 main claim으로는 부족하다.
- 따라서 다음 단계는 같은 subject/object geometry `G_e_size`를 공유하는 두 row를 만들고,
  `T_e = bigger than` / `T_e = smaller than` predicate flip으로 compatibility label이 바뀌는
  구조를 고정해야 한다.
- 이 구조에서 geometry-only는 두 row를 구분하지 못해야 하고, `T_e x G_e_size` interaction만
  compatibility를 설명해야 한다.
- class-pair mass는 `box->box`, `chair->chair`, `pillow->pillow` 등 same-class pair에 집중되어
  있다. 하지만 각 class pair 안에 `bigger`와 `smaller`가 함께 있으므로 materialization에서
  class-pair cap과 blocked-field policy를 유지하면 source inventory 단계의 blocker는 아니다.

다음 TODO:

```text
compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

## 2026-06-29 Size-Relative Candidate Materialization Plan After Source Inventory Update

Source inventory가 충분하다는 것을 확인한 뒤, 실제 row 생성 전에 materialization contract를
고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_size_relative_same_g_predicate_flip_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```

Frozen primary plan:

```text
primary_groups = 1200
primary_rows = 2400
positive_rows = 1200
negative_rows = 1200
subject_bigger_groups = 600
subject_smaller_groups = 600
bigger than rows = 1200
smaller than rows = 1200
```

Diagnostic-only plan:

```text
ambiguous_size_rows = 100
gt_geometry_conflict_audit_rows = 72
```

핵심 design은 same-G predicate flip이다.

```text
same scan + same subject + same object + same G_e_size
row A: T_e = bigger than
row B: T_e = smaller than
```

이렇게 해야 `G_e_size`만 보는 geometry-only model이 primary binary compatibility target을
풀 수 없다. `size_relative`에서 H002가 보여야 하는 것은 `subject가 더 큰가`라는 rule 자체가
아니라, 같은 geometry evidence가 predicate semantic content에 따라 compatible/incompatible로
바뀐다는 점이다.

Model-safe boundary:

- main view allowed: `T_e.predicate_text`, continuous `G_e_size` log-ratio fields
- `Q_e` view allowed: signless margin, OBB availability
- blocked from first main view: class labels, class-pair, GT/source/construction fields,
  discretized direction fields, `volume_ratio_band`, scan/object ids, `Z_e`

다음 TODO:

```text
compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```

## 2026-06-29 Size-Relative Candidate Materialization After Plan Update

Frozen plan에 따라 `size_relative` same-G predicate-flip rows를 materialize했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = size_relative_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```

핵심 수치:

```text
candidate_rows = 2572
primary_compatibility_rows = 2400
diagnostic_ambiguous_size_rows = 100
audit_gt_geometry_conflict_rows = 72
model_safe_main_rows = 2400
model_safe_qe_rows = 2572
group_rows = 1286
hidden_rows = 2572
```

Primary target:

```text
C_e positive / negative = 1200 / 1200
subject_bigger / subject_smaller groups = 600 / 600
bigger than / smaller than total rows = 1286 / 1286
```

Schema precheck:

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1200
max_groups_per_class_pair = 232 / 240
max_groups_per_class_pair_direction = 116 / 120
max_groups_per_scan = 13 / 24
```

판단:

- `size_relative` row materialization은 성공했다.
- same-G paired structure가 보존되어 primary group마다 같은 `G_e_size`에 대해
  `bigger than`과 `smaller than` 두 row가 존재한다.
- class/source/GT/construction/discretized direction field는 hidden manifest로 분리했다.
- 아직 learned smoke는 실행하지 않았으므로, 다음 단계는 schema/shortcut audit이다.
- 따라서 이 결과는 materialization 완료이지, size-relative compatibility claim 통과가 아니다.

다음 TODO:

```text
compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```

## 2026-06-29 Size-Relative Schema Shortcut Audit After Materialization Update

Materialized `size_relative` rows에 대해 schema leakage, 단일 factor shortcut, hidden
construction shortcut, group integrity를 점검했다. learned smoke는 실행하지 않았다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/
status = h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = size_relative_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit
```

핵심 수치:

```text
primary_rows = 2400
C_e positive / negative = 1200 / 1200
feature_path_violations = 0
group_integrity_errors = 0
smoke_ready_rows = 2400
```

Shortcut audit:

```text
T_predicate_label_only = 0.500
T_relation_family_only = 0.500
G_exact_tuple_only = 0.500
G_single_ratio probes = 0.500 AUROC each
TG_exact_interaction = 1.000
```

Hidden probe:

```text
class_pair/source_predicate/anchor_predicate/direction/scan/volume_band = 0.500
original_gt_anchor_flag = 1.000
direction_x_candidate_predicate = 1.000
```

판단:

- `T_e` 단독과 `G_e_size` 단독은 target을 풀 수 없다.
- `T_e x G_e_size` interaction이 의도한 compatibility signal이다.
- `original_gt_anchor_flag`와 `direction_x_candidate_predicate`는 construction metadata라
  hidden manifest에만 남기고 model-safe feature에서 제외했다.
- 따라서 다음 단계는 smoke-ready view를 바탕으로 learned smoke plan을 고정하는 것이다.
  아직 size-relative가 해결됐거나 paper-level result가 된 것은 아니다.

## 2026-06-29 Size-Relative Sanitized View Smoke Plan After Schema Audit Update

Schema audit을 통과한 `size_relative` rows를 runner-ready view로 정리하고, learned smoke
비교군과 control gate를 고정했다. 이 단계에서는 모델 학습을 실행하지 않았다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit/
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

Planned comparisons:

```text
M1_semantic_only_T
M2_geometry_only_G_size
M3_TG_concat_no_interaction
M4_TG_size_interaction  # primary
```

Required controls:

```text
wrong-T same-G
shuffled-G global
shuffled-G within predicate
sign-flipped G
no-interaction concat
```

판단:

- 다음 단계는 learned smoke runner 실행이다.
- `size_relative`에서 확인할 것은 geometry-only 성능이 아니라, 같은 `G_e_size`가
  `bigger than` / `smaller than` predicate에 따라 다르게 해석되는지다.
- runner가 통과하더라도 이는 train-only mechanism evidence이며, paper-level result로
  승격하려면 Docker 재현성과 held-out protocol이 필요하다.

## 2026-06-29 Size-Relative Sanitized View Smoke Runner After Plan Update

`size_relative` runner-ready view에 대해 train-only grouped-CV learned smoke를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan/
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls
overall = size_relative_smoke_passed_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_smoke_result_review_after_runner
```

핵심 metric:

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

판단:

- `size_relative`는 train-only smoke 기준으로 통과했다.
- semantic-only, geometry-only, exact tuple, plain concat이 모두 실패하고,
  `T_e x G_e_size` interaction만 target을 회복했다.
- wrong-T와 sign-flipped-G는 거의 완전히 반전되고, shuffled-G는 chance 근처로 무너진다.
- 따라서 이 결과는 relation-family routing에서 `size_relative = compatibility route`
  evidence로 쓸 수 있다.
- 다만 ECE가 높으므로 calibrated reliability probability claim은 아직 불가하다.
- 다음 단계는 result review에서 claim 위치와 paper-promotion boundary를 정하는 것이다.

## 2026-06-29 Size-Relative Smoke Result Review After Runner Update

`size_relative` smoke runner 결과를 H002 claim boundary 안에서 리뷰했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_size_relative_as_main_compatibility_route_evidence_keep_calibration_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative
```

Claim position:

- `size_relative`는 H002의 `main compatibility-route mechanism evidence`로 둔다.
- 이유는 geometry-only가 아니라 `T_e x G_e_size` interaction만 target을 풀기 때문이다.
- 같은 size-ratio evidence가 `bigger than`과 `smaller than`에서 반대로 해석되어야 하므로,
  이 family는 predicate-conditioned geometry compatibility를 보여주는 clean route다.
- 이 결과는 `C_e = compatibility(T_e, G_e)`의 증거이지 calibrated `p_rel`/`p_obs` 증거가 아니다.
- `M4_TG_size_interaction` AUROC는 `0.9999`지만 ECE가 `0.4950`이므로 probability
  calibration claim은 금지한다.
- 아직 train-only grouped-CV smoke라 paper-level result도 아니다.

Next:

```text
compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative
```

이 다음 단계에서는 기존 `relative_vertical`, `support_contact`, `close by`, `attachment_like`
route와 함께 `size_relative`를 multi-family evidence-routing synthesis에 반영해야 한다.

## 2026-06-29 Multi-Family Claim Synthesis After Size-Relative Update

`size_relative` result review를 기존 H002 multi-family synthesis에 반영했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_size_relative_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis
```

Updated route map:

```text
relative_vertical = clean compatibility mechanism / main
size_relative = clean compatibility mechanism / main with calibration caveat
support_contact = challenging compatibility route / main_with_caveat
proximity = geometry-easy control / diagnostic
attachment_like = observability-heavy future_or_diagnostic
support_contact_superordinate = diagnostic taxonomy
relative_horizontal = reference-frame deferred
```

현재 H002의 허용 가능한 claim은 다음처럼 정리한다.

```text
relation families require different evidence routes, and clean size/vertical
routes plus challenging support/contact controls support explicit
predicate-geometry compatibility rather than fixed score fusion.
```

해석:

- `size_relative`는 `relative_vertical`에 이어 두 번째 clean `C_e` mechanism anchor다.
- `support_contact`는 성능이 완전히 높지는 않지만 challenging compatibility route를 보여주는
  caveated evidence로 유지한다.
- `close by`는 geometry-only로 풀리는 family라 main learned compatibility target이 아니라
  geometry-easy control로 둔다.
- `attachment_like`와 `relative_horizontal`은 각각 observability와 reference-frame 문제가
  풀리기 전까지 future/deferred route다.
- 아직 H002는 paper-level performance, calibrated `p_rel`/`p_obs`, all-family generality를
  주장하지 않는다.

## 2026-06-29 Ablation And Table Plan Update After Size-Relative Synthesis

`size_relative`를 반영한 H002 table/ablation/control/promotion-gate 계약을 갱신했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis_ready
selected_path = freeze_size_relative_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan
```

Updated candidate tables:

```text
T1 Predicate-Geometry Compatibility Mechanism:
  relative_vertical, size_relative, support_contact

T2 Relation-Aware Evidence Routing Taxonomy:
  clean route, challenging route, geometry-easy diagnostic, observability-heavy route,
  superordinate diagnostic, reference-frame deferred

T3 Diagnostic Boundary Cases:
  close by, supported by, attached to, hanging on, connected to, horizontal relations

T4 Calibration and Claim Boundary:
  calibrated p_rel/p_obs, paper-level result, all-family generality, geometry-only claim blocks
```

핵심 비교군:

```text
T_e only
Z_e only where available
G_e only
T_e + G_e plain concat
C_e = interaction(T_e, G_e)
wrong-T
shuffled-G
sign-flip where meaningful
Q_e-only / shuffled-Q for p_obs boundary
```

판단:

- 이제 table plan은 `relative_vertical`, `size_relative`, `support_contact` 세 route를
  main mechanism rows로 포함한다.
- `size_relative`의 높은 AUROC는 calibration claim이 아니라 clean `C_e` mechanism row다.
- 다음은 Docker가 아니라 route coverage sufficiency review다. 현재 family coverage가
  충분한지, 아니면 추가 relation family를 더 해야 하는지 먼저 결정해야 한다.

## 2026-06-29 Route Coverage Sufficiency Review After Size-Relative Table Plan

현재 H002 table plan의 relation-family coverage가 promotion planning으로 넘어가기에
충분한지 검토했다. 결론은 충분하지 않으며, 사용자 판단에 맞춰 추가 relation family를
더 확인한 뒤 최종 claim boundary를 정하는 방향을 선택했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready
selected_path = coverage_not_sufficient_add_relation_family_sweep_before_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review
```

Decision:

```text
coverage_sufficient_for_promotion = false
selected_next_mode = broad_schema_first_family_sweep
```

Expansion queue:

```text
1. relative_horizontal
   - left / right / front / behind / in front of
   - 먼저 reference-frame protocol이 필요하다.

2. containment_in
   - standing in / lying in / hanging in / inside
   - containment ratio 기반 schema/capacity probe가 필요하다.

3. attachment_deferred
   - attached to / hanging on / connected to / mounted on
   - visual/mesh/Q_e observability protocol이 필요하다.

4. part_structural
   - build in / leaning against / belonging to / part of / cover
   - main C_e가 아니라 diagnostic/out-of-scope boundary 확인이 목적이다.

5. identity_symmetry
   - same as / same symmetry as
   - physical compatibility claim에서 제외할 근거를 기록한다.
```

중요한 판단:

- 현재 `relative_vertical`, `size_relative`, `support_contact` 세 main mechanism rows는
  유용하지만 final coverage로는 부족하다.
- 그러나 모든 relation family를 하나의 모델에 바로 넣으면 안 된다. relation family마다
  필요한 evidence schema와 target identifiability가 다르기 때문이다.
- 따라서 다음 단계는 all-family model training이 아니라 schema-first sweep plan이다.

## 2026-06-29 Additional Relation-Family Sweep Plan After Coverage Review

coverage review 이후 남은 relation family를 어떤 순서로 확인할지, 그리고 family-level
결과가 실패할 때 relation type별 probe로 내려가는 fallback rule을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review/
status = h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready
selected_path = plan_schema_first_family_sweep_with_predicate_level_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan
```

Counts:

```text
family_sweep_rows = 5
predicate_fallback_policy_rows = 24
predicate_probe_rows = 20
execution_gate_rows = 5
predicate_gap_rows = 29
```

Sweep order:

```text
1. relative_horizontal
   - left / right / front / behind / in front of
   - reference-frame protocol 먼저 필요

2. containment_in
   - standing in / lying in / hanging in / inside
   - containment schema/capacity probe

3. attachment_deferred
   - attached to / hanging on / connected to / mounted on
   - visual/mesh/Q_e observability protocol

4. part_structural
   - build in / leaning against / belonging to / part of / cover
   - structural/semantic boundary scan

5. identity_symmetry
   - same as / same symmetry as
   - out-of-scope rationale/count audit
```

새로 고정한 운영 원칙:

- multi-predicate family가 family-level에서 실패해도 family 전체를 바로 버리지 않는다.
- 각 relation type별로 schema, capacity, shortcut probe를 다시 본다.
- predicate-level로 성공한 relation은 predicate-level evidence로 남기고, 실패한 sibling은
  diagnostic/deferred/out-of-scope로 분리한다.
- 이 원칙은 support/contact의 `standing on`, `lying on`, `supported by` 같은 경우에도
  그대로 적용한다.

따라서 다음 H002 작업은 바로 model training이 아니라
`relative_horizontal`의 reference-frame protocol을 먼저 정의하는 것이다.

## 2026-06-29 Relative-Horizontal Reference-Frame Protocol Plan

`relative_horizontal` family를 바로 materialization하지 않고, reference-frame ambiguity를
먼저 protocol로 고정했다. 이 family는 `left`, `right`, `front`, `behind`, `in front of`가
포함되며, frame이 달라지면 relation label의 의미가 바뀔 수 있다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_reference_frame_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan
```

생성된 schema/control:

```text
frame_protocol_rows = 4
predicate_protocol_rows = 5
geometry_schema_rows = 5
qe_schema_rows = 5
target_construction_rows = 5
control_rows = 7
blocked_field_rows = 8
model_view_rows = 5
```

핵심 factor contract:

```text
T_e = horizontal predicate text/label
G_e_horizontal = predicate-independent signed horizontal displacement under a frozen frame
Q_e_frame = frame availability, frame disagreement, near-axis-boundary ambiguity
C_e = compatibility(T_e, G_e_horizontal), excluding Z_e
```

Frame policy:

- `scene_aligned_world_xy`: 첫 source inventory 후보.
- `view_or_camera_frame`: audit/Q_e-first 후보. 여러 view가 서로 다른 판단을 줄 수 있다.
- `object_centric_front_axis`: semantic object-front orientation이 없으면 diagnostic/deferred.
- `layout_or_room_frame`: diagnostic.

Predicate-level fallback:

- family-level route가 실패하면 `left/right`, `front/behind`, `in front of alias`로 나눈다.
- `in front of`는 `front`와 alias인지 source inventory에서 확인하기 전까지 diagnostic이다.

필수 control:

```text
same-G predicate flip
wrong-frame rotation
axis sign flip
subject-object swap
predicate alias audit
class-pair/source shortcut audit
axis-boundary abstain
```

다음 단계는 train-side source inventory다. 이 단계에서 GT anchor count, 3RScan
centroid/OBB join rate, same-G predicate-flip capacity, frame availability, `front` vs
`in front of` alias behavior, class/scan/endpoint concentration을 측정해야 한다.

## 2026-06-29 Relative-Horizontal Source Inventory After Reference-Frame Protocol

`relative_horizontal` train-side source inventory를 실행했다. 이 단계는 row materialization이
아니며, frame 후보와 capacity를 측정하는 source audit이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_inventory_ready_for_candidate_materialization_plan_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory
```

Predicate inventory:

```text
left = 12,016 train / 45,357 full
right = 12,016 train / 45,357 full
front = 6,766 train / 24,165 full
behind = 6,766 train / 24,165 full
in front of = 0 train / 0 full
```

Source join:

```text
centroid_pair_join_rate = 1.0
obb_pair_join_rate = 1.0
camera_pose_rate = 1.0 for observed anchors
unique horizontal anchor scans = 1,142
```

Selected axis candidates:

```text
left/right:
  axis = scene_world_x
  left sign = negative
  alignment = 0.765667
  compatible unique = 16,958
  same-G predicate-flip rows = 33,916

front/behind:
  axis = scene_world_y
  front sign = negative
  alignment = 0.755649
  compatible unique = 9,296
  same-G predicate-flip rows = 18,592
```

Shortcut/concentration:

```text
top_scan_fraction = 0.004845
top_class_pair_fraction = 0.087211
```

판단:

- `left/right`와 `front/behind`는 materialization plan으로 넘어갈 수 있다.
- 그러나 alignment가 약 `0.76` 수준이므로, world-frame geometry가 정답이라는 claim은 금지한다.
- 다음 materialization plan에서는 frame-disagreement, opposing rows, near-axis-boundary rows를
  `Q_e` 또는 diagnostic으로 분리해야 한다.
- `in front of`는 현재 source에서 관측되지 않으므로 first materialization main row에 넣지 않는다.

## 2026-06-29 Relative-Horizontal Candidate Materialization Plan After Source Inventory

`relative_horizontal` source inventory 결과를 기반으로 train-only candidate materialization
계약을 고정했다. 이 단계는 실제 row를 만들지 않고, quota와 control을 고정하는 plan이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory/
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

left rows = 600
right rows = 600
front rows = 600
behind rows = 600
in front of rows = 0
```

Diagnostic quota:

```text
axis_boundary_diagnostic_groups = 160
axis_boundary_diagnostic_rows = 320
opposing_frame_diagnostic_groups = 160
opposing_frame_diagnostic_rows = 320
```

Target construction:

```text
same directed-pair geometry
same G_e_horizontal
two rows differ only by T_e predicate
left/right pair or front/behind pair
```

따라서 geometry-only model은 같은 group 안의 positive/negative를 구분할 수 없어야 한다.
성공 signal은 `T_e x G_e_horizontal` interaction에서 나와야 한다.

중요한 boundary:

- `in front of`는 source에서 0개이므로 main binary row에 넣지 않는다.
- axis-boundary와 frame-disagreement/opposing rows는 `Q_e` 또는 diagnostic으로 분리한다.
- selected world-frame alignment가 약 `0.76`이므로 `relative_horizontal solved` claim은 금지한다.
- 다음 단계는 실제 train-only row materialization이다.

## 2026-06-29 Relative-Horizontal Candidate Materialization After Plan

`relative_horizontal` train-only candidate rows를 실제로 materialize했다. 이 단계는
learned smoke가 아니라 schema/shortcut audit 전 row artifact 생성이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = relative_horizontal_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization
```

Materialized rows:

```text
candidate_rows = 3,040
group_rows = 1,520
model_safe_main_rows = 2,400
model_safe_qe_rows = 3,040

primary_groups = 1,200
primary_rows = 2,400
primary_positive_rows = 1,200
primary_negative_rows = 1,200

axis_boundary_diagnostic_rows = 320
frame_disagreement_diagnostic_rows = 320
```

Primary balance:

```text
left rows = 600
right rows = 600
front rows = 600
behind rows = 600

positive left rows = 300
positive right rows = 300
positive front rows = 300
positive behind rows = 300
```

Schema precheck:

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1,200
diagnostic_c_label_errors = 0
scan_max_groups = 11
class_pair_max_groups = 109
class_pair_axis_pair_max_groups = 59
```

해석:

- 같은 primary group의 두 row는 동일한 `G_e_horizontal`을 공유하고 `T_e` predicate만 다르다.
- predicate-only shortcut을 줄이기 위해 positive predicate를 `left/right/front/behind` 각각
  `300`개로 맞췄다.
- axis-boundary와 frame-disagreement row는 binary `C_e`에 넣지 않고 `Q_e`/diagnostic으로
  분리했다.
- 다음 단계는 이 materialized view가 실제로 shortcut-free인지 확인하는 schema/shortcut audit이다.

## 2026-06-29 Relative-Horizontal Schema Shortcut Audit After Materialization

`relative_horizontal` materialized rows에 대해 schema leakage와 shortcut risk를 점검했다.
이 단계는 learned smoke가 아니라 smoke-ready view를 만들 수 있는지 확인하는 audit이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization/
status = h002_compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = relative_horizontal_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit
```

Gate result:

```text
primary_rows = 2,400
smoke_ready_rows = 2,400
schema_leakage_pass = true
allowed_single_feature_pass = true
group_integrity_pass = true
```

Main shortcut probes:

```text
T_predicate_label_only = 0.500
T_relation_family_only = 0.500
G_exact_tuple_only = 0.500
G_single_delta_x_subject_minus_object = 0.500
G_single_delta_y_subject_minus_object = 0.500
G_single_horizontal_distance = 0.500

TG_exact_interaction = 1.000
TG_signed_rule_interaction = 1.000
```

Hidden probes:

```text
hidden_axis_pair_only = 0.500
hidden_class_pair_only = 0.500
hidden_scan_only = 0.500
hidden_source_predicate_only = 0.500
hidden_selected_axis_bucket_only = 0.500

hidden_selected_frame_compatible = 1.000
hidden_source_predicate_x_candidate_predicate = 1.000
hidden_selected_axis_bucket_x_candidate_predicate = 1.000
```

해석:

- `T_e` alone, `G_e` alone, class-pair, scan, source predicate는 모두 near-chance다.
- `T_e x G_e_horizontal` interaction만 target을 설명한다.
- high hidden probes는 construction/label proxy이므로 model-safe view에서 제외되어야 한다.
- 이 audit는 relative-horizontal을 paper evidence로 승격하지 않는다. 다만 learned smoke plan으로
  넘어갈 수 있는 train-only schema gate는 통과했다.

## 2026-06-29 Relative-Horizontal Sanitized View Smoke Plan After Schema Audit

`relative_horizontal` learned smoke를 실행하기 전에 runner input, model views, controls,
promotion gates를 고정했다. 이 단계는 learned model을 실행하지 않는다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit/
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_plan_after_schema_audit_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan
```

Frozen input:

```text
rows = 2,400
positive = 1,200
negative = 1,200
cv_groups = 1,200
paired_groups = 1,200
predicate_counts = left/right/front/behind each 600
feature_blocks = T_e + G_e_horizontal
```

Planned main comparison:

```text
M1_semantic_only_T
M2_geometry_only_G_horizontal
M3_TG_concat_no_interaction
M4_TG_horizontal_interaction
```

Required controls:

```text
C1_wrong_T_same_G
C2_shuffled_G_global
C3_shuffled_G_within_predicate
C4_axis_sign_flipped_G
C5_wrong_frame_xy_swap
C6_subject_object_swap
no_interaction_concat
```

Promotion gates:

```text
M1/M2/S1/S2 AUROC <= 0.60
M4 AUROC >= 0.95
M4 gain over single-factor baselines >= 0.30
wrong-T / shuffled-G controls <= 0.60 or invert
sign-flip, wrong-frame, subject-object swap must degrade or invert
paired score margin pass rate >= 0.90
```

해석:

- `relative_horizontal` smoke는 `T_e x G_e_horizontal` compatibility가 실제로 학습 가능한지
  확인하는 train-only mechanism test다.
- horizontal relation은 reference-frame ambiguity가 있으므로 wrong-frame x/y swap control을
  반드시 포함해야 한다.
- `in front of`는 여전히 source에서 관측되지 않았으므로 이번 primary smoke에서 제외한다.
- 다음 단계는 이 frozen plan을 따라 learned smoke runner를 구현/실행하는 것이다.

## 2026-06-29 Relative-Horizontal Sanitized View Smoke Runner After Plan

`relative_horizontal` learned smoke를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan_passed_controls
validation_errors = 0
learned_smoke_executed = true
paper_evidence_allowed = false
next_todo = compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner
```

Main result:

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

해석:

- `relative_horizontal`은 train-only same-G predicate-flip target에서 강한
  `T_e x G_e_horizontal` compatibility route를 보인다.
- semantic-only, geometry-only, exact-geometry shortcut, additive concat은 target을 풀지 못한다.
- wrong predicate, shuffled geometry, wrong frame, sign flip, endpoint swap control은
  collapse 또는 inversion을 보인다.
- 단, 이 결과는 frozen reference-frame protocol에 의존하므로 paper-level claim으로 올리기 전
  result review에서 route position을 정해야 한다.

## 2026-06-29 Relative-Horizontal Smoke Result Review After Runner

`relative_horizontal` smoke runner 결과를 리뷰하고 route position을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_relative_horizontal_as_main_compatibility_route_evidence_with_reference_frame_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal
```

Decision:

- `relative_horizontal`은 H002의 `main compatibility-route mechanism evidence`로 둔다.
- 단, `left/right/front/behind`는 reference-frame convention에 의존하므로
  frame-aware route로만 claim한다.
- `in front of`는 현재 train-side source에서 관측되지 않았으므로 primary claim에서 제외한다.
- `p_rel`/`p_obs` calibration, paper-level result, complete horizontal ontology coverage는
  여전히 claim하지 않는다.

Implication:

- H002 multi-family route map은 이제 `relative_vertical`, `size_relative`,
  `relative_horizontal`, `support_contact`, `proximity`를 함께 정리해야 한다.
- 다음 단계는 multi-family synthesis update다.

## 2026-06-29 Multi-Family Claim Synthesis After Relative-Horizontal

`relative_horizontal` result review를 H002 multi-family route map에 반영했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_relative_horizontal_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis
```

Updated route map:

```text
relative_vertical = clean sign compatibility route
size_relative = clean size-comparison compatibility route
relative_horizontal = frame-aware directional compatibility route
support_contact = challenging compatibility route with caveat
proximity = geometry-easy diagnostic/control
attachment_like = observability-heavy future/deferred
```

현재 허용되는 claim:

```text
Different relation families require different evidence routes, and explicit
T_e x G_e compatibility is necessary in clean vertical, size, and frame-aware
horizontal families while remaining useful but harder in support/contact.
```

여전히 금지되는 claim:

- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- complete horizontal ontology coverage including `in front of`
- support/contact fully solved
- geometry-only relation reliability

다음 단계는 relative-horizontal을 포함한 ablation/table plan update다.

## 2026-06-29 Ablation And Table Plan Update After Relative-Horizontal

`relative_horizontal`을 포함한 table/ablation/control/gate 계약을 갱신했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis/
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

Controls:

- semantic-only / geometry-only / plain concat / `T_e x G_e`
- wrong-T
- shuffled-G global / within predicate
- sign-flip
- wrong-frame x/y swap for `relative_horizontal`
- subject/object endpoint swap for directional relations

다음 단계는 현재 route coverage가 충분한지 검토하는 것이다.

## 2026-06-30 Route-Coverage Sufficiency Review After Relative-Horizontal Table Plan

`relative_horizontal`까지 포함한 table plan을 기준으로 route coverage sufficiency를
검토했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready
selected_path = coverage_sufficient_for_hypothesis_framework_proceed_to_schema_freeze_promotion_protocol_no_new_family_now
validation_errors = 0
next_todo = compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review
```

판단:

- 현재 H002는 relation family discovery를 더 진행하기보다 schema freeze와 promotion
  protocol로 넘어갈 수 있다.
- main mechanism rows는 `relative_vertical`, `size_relative`, `relative_horizontal`,
  `support_contact`로 유지한다.
- `proximity`는 geometry-easy control/generality, `attachment_like`는
  observability-heavy future/deferred, `supported by`와 containment/part/identity 계열은
  diagnostic/future/out-of-scope boundary로 둔다.
- 이 결론은 all-family generality나 paper-level reliability claim을 허용하지 않는다.

다음 단계는 H002 schema freeze와 promotion protocol 작성이다.

## 2026-06-30 Schema Freeze And Promotion Protocol After Route-Coverage Review

사용자 정정에 따라 H002의 target 정의를 relation-specific evidence route 중심으로
다시 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review/
status = h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready
selected_path = freeze_route_specific_target_definitions_and_promotion_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze
```

핵심 정정:

```text
learned compatibility target인지 아닌지가 아니라,
어떤 evidence route와 target semantics를 요구하는지가 핵심이다.
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

다음 단계는 route-specific target manifest plan이다. 각 route별 model-safe view,
hidden construction fields, target axes, controls, and artifact roots를 명시해야 한다.

## 2026-06-30 Route-Specific Target Manifest Plan After Schema Freeze

route-specific target manifest plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze/
status = h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready
selected_path = freeze_per_route_target_manifests_select_manifest_consistency_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan
```

생성된 manifest:

- `route_target_manifest.csv`
- `route_field_manifest.csv`
- `route_hidden_manifest.csv`
- `route_control_manifest.csv`
- `route_artifact_root_plan.csv`
- `route_promotion_priority.csv`

핵심 target axes:

| Route | Target Axis | Label Space |
| --- | --- | --- |
| `close by` | `geometry_support` | `geometry_supported`, `geometry_unsupported`, `abstain` |
| predicate-geometry routes | `predicate_geometry_compatibility` | `compatible`, `incompatible`, `abstain` |
| `supported by` | `accept_relabel_abstain` | `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`, `abstain` |
| attachment route | `observability_then_reliability` | `observable_accept`, `observable_reject`, `unobservable_abstain`, `functional_or_topology_uncertain` |

이 단계는 row materialization이나 model run을 하지 않았다. 다음 단계는 manifest consistency
audit이다.

## 2026-06-30 Route-Specific Target Manifest Consistency Audit After Plan

route-specific target manifest consistency audit를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan/
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

보존된 계약:

- `close by = geometry_support`
- `supported by = accept_relabel_abstain`
- attachment route = `observability_then_reliability`
- `C_e` excludes `Z_e`
- hidden construction fields are not model-safe

다음 단계는 route-specific target materialization plan이다. 이 audit는 통과했지만, 아직
row materialization은 수행하지 않았다.

## 2026-06-30 Route-Specific Target Materialization Plan After Manifest Audit

route-specific target materialization plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit/
status = h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready
selected_path = freeze_materialization_waves_select_close_by_geometry_support_route_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```

Materialization waves:

| Wave | Routes | Purpose |
| --- | --- | --- |
| `W0` | `R2-R5` | 기존 main-route artifacts 정규화 |
| `W1` | `R1 close by` | 첫 concrete `geometry_support` route plan |
| `W2` | `R6 supported by` | superordinate decomposition / relabel / abstain |
| `W3` | `R7 attachment` | observability schema audit |
| `W4` | `R8-R10` | leaning / cover / containment capacity-schema audit |
| `W5` | `R11-R13` | boundary/future manifests |

Selected first follow-up:

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
```

다음 단계는 `close by` geometry-support materialization plan이다. 이 단계에서도 아직 실제
row materialization 여부를 별도 gate로 확인해야 한다.

## 2026-06-30 R1 Close-By Geometry-Support Materialization Plan After Route Plan

`close by` geometry-support materialization plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready
selected_path = materialize_r1_close_by_as_geometry_support_route_root_not_interaction_claim
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan
```

결정:

- `R1 close by`는 `geometry_support` route root로 materialize할 계획이다.
- 기존 close-by row material을 재사용하되, target을 `C_e_label`이 아니라
  `geometry_support_label`로 정규화한다.
- `C_e` predicate-geometry interaction은 R1에서 `not_applicable`로 둔다.
- `T_e`는 annotation/baseline용, `Z_e`는 source baseline용, `G_e`는 primary route
  evidence, `Q_e`는 coverage/abstain용으로 분리한다.
- distance dominance는 이 route에서 expected behavior다. 단, 이 결과를
  predicate-geometry interaction evidence로 쓰면 안 된다.

Planned row material:

| Component | Rows | Use |
| --- | ---: | --- |
| primary geometry-support binary | 800 | geometry-supported vs unsupported |
| Q_e / abstain diagnostics | 240 | coverage, ambiguity, uncertain geometry |
| raw-distance diagnostic | 240 | raw-vs-normalized distance and scale control |
| GT/geometry conflict audit | 4 | audit only |

다음 단계는 `artifacts/route_specific_targets/r1_proximity/` 아래에 실제 route root를
materialize하는 것이다. Learned smoke와 paper-level claim은 아직 막혀 있다.

## 2026-06-30 R1 Close-By Geometry-Support Route Materialization After Plan

`R1 close by` route root를 materialize했다.

```text
artifact_root = artifacts/route_specific_targets/r1_proximity/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready
selected_path = materialized_r1_close_by_geometry_support_route_root
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization
```

생성 파일:

- `summary.json`
- `schema.json`
- `model_safe_rows.jsonl`
- `hidden_manifest.jsonl`
- `audit_view.jsonl`
- `control_manifest.json`
- `split_or_group_manifest.json`
- `report.md`
- `validation_errors.jsonl`
- `row_counts.csv`
- `label_counts.csv`

Materialized rows:

| Component | Rows |
| --- | ---: |
| total | 1,284 |
| primary geometry-support binary | 800 |
| Q_e / abstain diagnostics | 240 |
| raw-distance diagnostic | 240 |
| GT/geometry conflict audit | 4 |

핵심 변환:

- legacy `C_e_label`을 route-specific `geometry_support_label`로 바꿨다.
- `c_e_interaction_label`은 모든 row에서 `not_applicable`이다.
- primary binary는 `geometry_supported=400`, `geometry_unsupported=400`이다.
- 전체 label count는 `geometry_supported=520`, `geometry_unsupported=520`,
  `abstain=240`, `audit_required=4`이다.

해석:

- 이 route는 `close by`가 geometry-only route로 충분히 설명되는지를 다룬다.
- distance dominance는 expected route property다.
- 이 결과는 `T_e x G_e` interaction evidence가 아니다.
- learned smoke와 paper-level claim은 아직 막혀 있다.

다음 단계는 route root의 schema/shortcut audit이다.

## 2026-06-30 R1 Close-By Geometry-Support Schema Audit After Materialization

R1 `close by` route root의 schema/shortcut-boundary audit를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization/
status = h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready
selected_path = r1_close_by_schema_pass_select_geometry_route_control_runner_plan
validation_errors = 0
passed_checks = 75
total_checks = 75
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan
```

감사 결과:

- required route files present;
- route contract and `target_axis=geometry_support` preserved;
- row count and route-row-id consistency passed;
- primary label balance passed: `geometry_supported=400`, `geometry_unsupported=400`;
- legacy `C_e_label` absent from `model_safe_rows.jsonl`;
- blocked hidden/construction fields absent from model-safe feature blocks;
- `c_e_interaction_label=not_applicable` for all `1,284` rows;
- distance / scale / coverage controls ready;
- wording guard passed.

해석:

- `close by`에서 distance dominance는 expected route property다.
- 이 branch의 실패 조건은 hidden construction leakage, label imbalance, control missing, wording drift다.
- R1은 geometry-only route evidence이며, learned interaction smoke는 허용하지 않는다.

다음 단계는 geometry-only route control runner plan이다.

## 2026-06-30 R1 Close-By Geometry-Support Route Control Runner Plan

R1 `close by` geometry-only route control runner plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready
selected_path = plan_r1_close_by_geometry_only_route_controls_no_interaction_runner
validation_errors = 0
planned_controls = 12
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner
```

계획한 controls:

- `distance_xy`
- `distance_3d`
- `normalized_distance_xy`
- `normalized_distance_3d`
- `overlap_geometry`
- `scale_control`
- `coverage_control`
- `source_score_rank`
- `class_pair_only`
- `p_geom_valid_hidden_baseline`
- `shuffled_G`
- `wrong_pair_geometry`

해석:

- 이 runner는 deterministic geometry-only controls만 실행한다.
- `close by`의 distance dominance는 expected route property로 보고한다.
- `T_e x G_e` interaction smoke는 R1에서 계속 금지한다.
- 이 plan은 metric을 실행하지 않았으므로 paper-level evidence가 아니다.

다음 단계는 실제 route control runner 실행이다.

## 2026-06-30 R1 Close-By Geometry-Support Route Control Runner

R1 `close by` geometry-only route controls를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready
selected_path = ran_r1_close_by_geometry_only_route_controls_no_interaction_model
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_result_review
```

주요 결과:

| Control | AUROC / Accuracy |
| --- | ---: |
| `distance_xy` AUROC | 0.999556 |
| `distance_3d` AUROC | 0.998975 |
| `normalized_distance_xy` AUROC | 1.000000 |
| `normalized_distance_3d` AUROC | 1.000000 |
| `overlap_geometry` AUROC | 0.892500 |
| `source_score_rank` semantic AUROC | 0.552103 |
| `class_pair_only` accuracy | 0.503750 |
| hidden `p_geom_valid` AUROC | 0.999594 |
| `shuffled_G` AUROC | 0.336178 |
| `wrong_pair_geometry` AUROC | 0.006272 |

해석:

- `close by`는 geometry-only route로 보는 것이 맞다.
- source semantic score와 class-pair shortcut은 target을 설명하지 못한다.
- normalized distance는 target을 완전히 설명한다.
- shuffled-G와 wrong-pair geometry가 무너지므로 pair-specific geometry signal이다.
- 이 결과는 `T_e x G_e` interaction evidence가 아니다.

다음 단계는 R1 결과 review와 route role freeze다.

## 2026-06-30 R1 Close-By Geometry-Support Route Result Review

R1 `close by` 결과 review를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_result_review/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready
selected_path = freeze_close_by_as_geometry_only_route_evidence_move_to_supported_by_decomposition
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_target_plan
```

최종 판단:

- `close by`는 `geometry-only learned/evaluated route`로 고정한다.
- normalized distance가 AUROC `1.000000`으로 route target을 해결한다.
- source semantic score AUROC `0.552103`, class-pair-only accuracy `0.503750`이라
  source/class shortcut으로 해석하지 않는다.
- shuffled-G와 wrong-pair geometry는 best accuracy `0.5`로 붕괴한다.
- 따라서 실제 pair-specific `G_e`가 필요하지만, `T_e x G_e` interaction이 필요하다는
  증거는 아니다.

H002 claim에서의 위치:

- allowed: relation family마다 evidence route가 다르고, proximity/`close by`는
  geometry-only route가 충분할 수 있다.
- blocked: `close by`를 compatibility interaction, calibrated `p_rel/p_obs`, 또는
  paper-level held-out result로 주장하는 것.

다음 단계는 R6 `supported by`를 binary compatibility가 아니라
accept/relabel/reject/abstain decomposition route로 설계하는 것이다.

## 2026-06-30 R6 Supported-By Decomposition Target Plan

R6 `supported by` target plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_target_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready
selected_path = plan_supported_by_superordinate_accept_relabel_reject_abstain_route
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan
```

핵심 결정:

- `supported by`는 clean binary compatibility target이 아니다.
- `standing on` / `lying on`과 동시에 참일 수 있는 broad superordinate support label이다.
- 따라서 R6 target은 `accept_broad_support`, `relabel_to_subtype`,
  `reject_no_support`, `abstain`으로 분해한다.

근거:

- 기존 supported-by diagnostic rows는 `160`개다.
- 역할별 seed는 `clear_accept=40`, `hard_reject_no_support=40`,
  `overlap_or_abstain=80`이다.
- visual proxy label에서 `supported by = accept 82 / reject 11 / abstain 37`이다.
- class-pair repair 이후에도 `supported by = accept 99 / reject 15 / abstain 46`으로
  reject가 부족하고 class-pair shortcut risk가 남아 있다.

다음 단계:

- R6 candidate materialization plan에서 각 label 최소 60 rows, 목표 80 rows를 계획한다.
- same class-pair 안에 accept/relabel/reject/abstain이 섞이도록 mining해야 한다.
- generic endpoint만 abstain으로 가는 shortcut을 막아야 한다.
- no-GT는 자동 reject가 아니라 audit/abstain 후보로만 둔다.

## 2026-06-30 R6 Supported-By Candidate Materialization Plan

R6 candidate materialization plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready
selected_path = plan_320row_supported_by_decomposition_with_240row_min_viable_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization
```

계획:

- preferred target은 `320` rows, label당 `80` rows다.
- minimum viable fallback은 `240` rows, label당 `60` rows다.
- labels는 `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`,
  `abstain`이다.

현재 source capacity:

```text
supported_by_rows = 50601
supported_by_class_pair_balanced_rows = 164
supported_by_class_pair_rank_balanced_rows = 130
clear_accept_rows = 491
hard_reject_no_support_rows = 12712
overlap_or_abstain_rows = 37398
existing_supported_by_diagnostic_rows = 160
```

materialization gate:

- same-class-pair mixed labels를 최소 `12` cells 확보한다.
- hard-surface share를 `0.55` 이하로 제한한다.
- generic endpoint abstain share를 `0.50` 이하로 제한한다.
- no-GT는 자동 reject로 쓰지 않는다.
- source score/rank, queue kind, GT match, old geometry status, `p_geom_valid`,
  construction bucket은 hidden only다.

## 2026-06-30 R6 Supported-By Candidate Materialization

R6 `supported by` candidate rows를 materialize했다.

```text
artifact_root = artifacts/route_specific_targets/r6_superordinate_support/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_preferred_320row_target
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit
```

결과:

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

gate 결과:

- preferred 320-row target을 달성했고 fallback은 필요하지 않았다.
- max rows per scan은 `5/12`, directed pair는 `1/1`, class-pair는 `4/16`이다.
- hard-surface share는 `0.278125/0.55`다.
- generic endpoint abstain share는 `0.175/0.50`이다.
- model-safe rows에 blocked hidden fields는 없다.

다음 단계는 learned smoke가 아니라 schema/shortcut audit이다.

## 2026-06-30 R6 Supported-By Schema Shortcut Audit

R6 `supported by` decomposition rows의 schema/shortcut audit를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_plan
```

결과:

- rows: `320`
- label balance: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`, `abstain 80`
- observable rows: `240`
- schema leakage hits: `0`
- allowed high-risk probes: `0`
- allowed medium-risk probes: `10`
- hidden high-risk probes: `8`

해석:

- model-safe `T_e/G_e/Q_e` 안에는 source/rank/GT/construction field leakage가 없다.
- allowed high-risk shortcut은 없으므로 R6 smoke plan으로 넘어갈 수 있다.
- medium-risk allowed probes는 `G_e`의 contact/vertical/overlap feature가 decomposition label에 실제로 기여할 가능성을 보여준다.
- hidden `evidence_reason`, `label_match_status`, `candidate_role`, `machine_hint`, `matched_predicates`는 target을 복사할 수 있으므로 반드시 model input에서 제외해야 한다.
- 이 단계는 learned performance가 아니라 target/schema viability 확인이다.

## 2026-06-30 R6 Supported-By Smoke Plan

R6 `supported by` decomposition smoke plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_runner
```

runner-ready target:

- total rows: `320`
- 4-way decomposition: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`, `abstain 80`
- `p_obs`: observable `240`, abstain `80`
- observable `p_rel` binary: accept-or-relabel `160`, reject `80`
- observable `p_rel` 3-way: `80/80/80`
- CV groups: `257`

계획된 task:

- `T0_decomposition_4way`
- `T1_p_obs_binary`
- `T2_p_rel_binary_observable`
- `T3_p_rel_3way_observable`

계획된 비교군:

- `T_e` only
- `G_e` only
- `Q_e` only
- `T_e + G_e`
- `G_e + Q_e`
- `T_e + G_e + Q_e` factorized route
- shuffled `G_e`, shuffled `Q_e`, hidden source/rank, hidden construction probes

해석:

- 이제 R6에 대해서만 train-only learned smoke runner를 실행할 수 있다.
- `Q_e`는 `p_obs`에는 강하게 작동할 수 있지만, observable `p_rel`을 혼자 풀면 relation reliability가 아니라 observability shortcut으로 해석해야 한다.
- 이 단계는 smoke 실행 전 protocol freeze이며 learned 결과가 아니다.

## 2026-06-30 R6 Supported-By Smoke Runner

R6 `supported by` decomposition smoke runner를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_runner/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_q_observability_diagnostic
validation_errors = 0
learned_smoke_executed = true
epochs = 5
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_result_review
```

핵심 결과:

- `p_obs`: `M6_TGQ` AUROC `0.978802`, Q-only AUROC `1.000000`
- observable `p_rel` binary: `M6_TGQ` AUROC `0.831328`
- observable `p_rel` binary: `G_e + Q_e` AUROC `0.905703`
- observable `p_rel` binary: Q-only AUROC `0.880547`
- observable `p_rel` binary: best single `G_e` AUROC `0.888984`
- shuffled `G_e`: AUROC `0.540703 / 0.459063`
- observable `p_rel` 3-way: M6 macro OVR AUROC `0.773047`, macro F1 `0.540704`
- hidden construction p_rel probe: AUROC `1.000000`

판단:

- `p_obs`는 잘 풀리며, 여기서 `Q_e`가 강한 것은 정상이다.
- 그러나 observable `p_rel`에서도 `Q_e`와 `G_e+Q_e`가 full `T_e+G_e+Q_e`보다 강하다.
- 따라서 R6 `supported by`는 현재 main factorized-route success가 아니라,
  superordinate support decomposition / observability-geometry diagnostic으로 기록한다.
- hidden construction field가 p_rel을 완전히 복사할 수 있으므로 source/rank/GT/construction
  provenance는 계속 audit-only다.

다음 TODO는 `compatibility_dataset_v3_supported_by_decomposition_smoke_result_review`다. 이 단계에서
`supported by`를 diagnostic/future route로 고정할지, target을 재설계할지, 기존 route map에서
`standing on`/`lying on` compatibility와 얼마나 분리할지 결정한다.

## 2026-06-30 R6 Supported-By Smoke Result Review

R6 `supported by` smoke result review를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update
selected_path = freeze_supported_by_as_superordinate_decomposition_diagnostic_keep_out_of_main_factorized_success
validation_errors = 0
next_todo = compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review
```

결정:

- `supported by`는 main factorized-route success가 아니라 `superordinate_support`
  decomposition diagnostic으로 고정한다.
- 근거는 observable `p_rel`에서 full `T_e+G_e+Q_e`보다 `G_e+Q_e`와 Q-only가 강하다는 점이다.
- 이 결과는 broad support label이 accept/relabel/reject/abstain route를 필요로 한다는 근거로 사용한다.
- `standing on` / `lying on`은 별도의 support/contact predicate-level compatibility route로 유지한다.
- calibrated `p_rel`, paper-level evidence, all-family solved reliability claim은 계속 blocked다.

다음 TODO는 `compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review`다.

## 2026-06-30 Route Map Update After R6 Review

R6 `supported by` review 결과를 H002 route map에 반영했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review/
status = h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready
selected_path = merge_r6_diagnostic_boundary_select_attachment_observability_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_target_plan
```

변경 사항:

- R6 `supported by`: `diagnostic_frozen_not_main_factorized_success`로 고정.
- R5 `standing on` / `lying on`: broad `supported by`와 분리된 support/contact compatibility route로 유지.
- R7 `attached to` / `hanging on` / `connected to`: 다음 active route로 선택.
- main mechanism families는 `relative_vertical`, `size_relative`, `relative_horizontal`,
  `support_contact`로 유지.
- diagnostic/control families는 `proximity`, `superordinate_support`로 정리.

다음 TODO는 `compatibility_dataset_v3_attachment_observability_target_plan`이다. 이 단계는 row
materialization이나 learned smoke가 아니라 target/evidence boundary 정의부터 시작해야 한다.

## 2026-06-30 R7 Attachment Observability Target Plan

R7 `attached to` / `hanging on` / `connected to` target plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_target_plan/
status = h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory
selected_path = plan_r7_attachment_observability_first_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_source_inventory
```

핵심 결정:

- R7은 observability-first route로 둔다.
- `p_obs`와 `Q_e` schema를 먼저 세우고, observable row에서만 `p_rel`을 정의한다.
- `attached to`와 `hanging on`은 primary observability-then-reliability predicate다.
- `connected to`는 physical/topological/functional connection evidence가 명시되기 전까지 diagnostic이다.
- 이전 attachment positive-anchor `560` rows는 direct training target이 아니라 source-count,
  packet, shortcut-risk evidence로만 재사용한다.

기존 attachment label snapshot:

- rows: `560`
- predicate counts: `attached to 238`, `hanging on 242`, `connected to 80`
- review labels: `accept 60`, `reject 246`, `abstain 254`
- old binary target shortcut-risk flags: `98`
- strict/diagnostic clear slices in target-independence audit: `0 / 0`

해석:

이 단계는 attachment를 다시 learned smoke로 밀어붙이는 것이 아니라, 이전 shortcut-prone
binary target을 버리고 observability route로 target semantics를 재정의한 것이다. 따라서 다음
작업은 row materialization이 아니라 source inventory다. 구체적으로 predicate별 candidate 수,
packet availability, point/mesh evidence, visual/multiview evidence, endpoint identity,
topology/functional ambiguity를 먼저 센다.

## 2026-06-30 R7 Attachment Observability Source Inventory

R7 source inventory를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_source_inventory/
status = h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan
selected_path = r7_source_inventory_supports_attached_hanging_materialization_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization_plan
```

full-train candidate capacity:

- `attached to`: `185,346` rows, exact GT match `6,190`, unsupported old geometry `185,346`
- `hanging on`: `185,346` rows, exact GT match `939`, unsupported old geometry `185,346`
- `connected to`: `185,346` rows, exact GT match `174`, unsupported old geometry `185,346`
- unique scans: `1,157`
- unique directed pairs: `185,346`
- all `1,157` scans have multiview, sequence, mesh-ready, and point/mesh-ready source files.

existing packet reuse:

- total packet rows: `560`
- `attached to`: `238` rows, all packet/mesh/multiview/audit ready, strong same-frame pair visual `46`
- `hanging on`: `242` rows, all packet/mesh/multiview/audit ready, strong same-frame pair visual `58`
- `connected to`: `80` rows, all packet/mesh/multiview/audit ready, strong same-frame pair visual `12`,
  explicit topology/functional source rows `0`

판단:

- `attached to`와 `hanging on`은 R7 observability materialization plan으로 진행 가능하다.
- `connected to`는 후보 수와 packet은 충분하지만, explicit topology/functional evidence가 없으므로
  primary reliability target이 아니라 diagnostic route로 유지한다.
- 모든 R7 predicate가 기존 geometry verifier에서 `unsupported`인 것은 H002 방향과 충돌하지 않는다.
  오히려 attachment route는 old `p_geom_valid`가 아니라 point/mesh/multiview 기반 `Q_e`와
  model-safe `G_e`를 새로 정의해야 함을 보여준다.
- 다음 TODO는 row를 바로 만들기보다 materialization plan이다. 이 plan에서 `review_*`, source rank,
  packet id, construction field를 model input에서 차단하고, `p_obs` 먼저, observable subset에서만
  `p_rel`을 정의해야 한다.

## 2026-06-30 R7 Attachment Observability Materialization Plan

R7 materialization plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready
selected_path = plan_primary_attached_hanging_gq_materialization_keep_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization
```

planned waves:

- W1 primary `attached to` / `hanging on`: `480` rows
- W2 diagnostic `connected to`: `80` rows
- W3 full-train expansion: deferred

materialization contract:

- `source_rows.jsonl`, `model_safe_view.jsonl`, `target_manifest.jsonl`,
  `hidden_manifest.jsonl`, `control_manifest.jsonl`, `schema_audit_inputs.json`를 분리해서 만든다.
- `T_e`: predicate/object semantic content만 허용한다.
- `G_e_attachment`: pair distance/gap, OBB overlap, point/mesh contact proxy, anchor surface proxy,
  relative pose, vertical offset, floor/support confound, normal/orientation proxy를 재계산하거나 추출한다.
  construction proxy나 old `p_geom_valid`를 그대로 복사하지 않는다.
- `Q_e_observability`: mesh/multiview/contact sheet readiness, subject/object image count,
  same-frame co-visibility, same-view weak availability, scan mesh/point/multiview availability를 담는다.
  `review_coverage`, `review_endpoint_identity`, `review_uncertainty`는 feature로 금지한다.
- hidden `Z_e`: source score/rank/query/proxy/GT fields는 hidden audit only다.
- targets: `p_obs` 먼저, `p_rel_observable`은 observable `attached to` / `hanging on`에만 정의한다.
- `connected to`는 explicit topology/functional evidence가 없으므로 primary `p_rel`을 만들지 않는다.

target caveat:

- locked target snapshot은 `p_obs` observable/abstain `306/254`, observable `p_rel`
  accept/reject `60/246`이다.
- 따라서 materialization은 가능하지만 learned reliability success는 아직 주장할 수 없다.
- 다음 materialization 후 반드시 schema shortcut audit을 먼저 해야 하며, class-pair/query/rank/packet/review
  leakage probe와 wrong-`T_e`, shuffled-`G_e`, shuffled-`Q_e`, no-view/low-evidence controls가 필요하다.

## 2026-06-30 R7 Attachment Observability Materialization

R7 materialization을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_r7_gq_separated_source_target_hidden_control_views
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_schema_shortcut_audit
```

핵심 수치:

- total rows: `560`
- primary route: `attached to 238`, `hanging on 242`
- diagnostic route: `connected to 80`
- geometry available: `560/560`
- model-safe rows / target rows / hidden rows: `560 / 560 / 560`
- control manifest rows: `7`
- `p_obs_target`: observable `306`, abstain/not-observable `254`
- observable `p_rel`: accept `60`, reject `246`, not-defined `254`

분리 원칙:

- `model_safe_view.jsonl`에는 `T_e`, derived `G_e_attachment`, `Q_e_observability`만 둔다.
- hidden `Z_e`, source score/rank, ids, packet paths, review labels, target labels은 model-safe view에서 제외했다.
- mesh/multiview raw input은 아직 모델 입력이 아니며, derived availability와 observability feature로만 사용했다.

판단:

이번 단계는 learned result가 아니라 schema-audit-ready dataset materialization이다.
`connected to`는 explicit topology/functional evidence가 없어 diagnostic으로 유지한다.
observable `p_rel`은 `60/246`으로 positive sparse하므로, 바로 smoke runner로 가지 않고
schema shortcut audit이 먼저 필요하다.

## 2026-06-30 R7 Attachment Observability Schema Shortcut Audit

R7 schema shortcut audit을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_blocked_shortcut_risk
selected_path = blocked_allowed_model_safe_shortcut_risk
validation_errors = 0
learned_smoke_allowed = false
next_todo = compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit
```

핵심 수치:

- rows: `560`
- `p_obs` rows: `560`, labels `306/254`
- observable `p_rel` rows: `306`, labels `60/246`
- schema leakage hits: `0`
- allowed high-risk blockers: `4`
- allowed medium-risk probes: `45`
- hidden high-risk probes: `5`

critical blockers:

- `p_obs:T_subject_object_pair` accuracy `0.958929`
- `p_obs:T_predicate_x_class_pair` accuracy `1.000000`
- `p_rel_observable:T_subject_object_pair` accuracy `0.986928`
- `p_rel_observable:T_predicate_x_class_pair` accuracy `1.000000`

해석:

`model_safe_view`에 target, hidden id, source score/rank, packet path, review label이 직접 새는 문제는 없다.
하지만 현재 560-row R7 target은 predicate/class-pair strata만으로 거의 복원된다. 따라서 이 artifact로
learned smoke를 실행하면 model이 attachment observability나 predicate-geometry compatibility를 배운 것이
아니라 endpoint semantic prior를 외운 것으로 해석될 위험이 크다.

판단:

R7 route 자체를 버리는 것은 아니다. 다만 현재 reused packet target은 learned target으로 부적합하다.
다음 단계는 path decision이다. 선택지는 class-pair-balanced R7 contrast를 새로 mining하거나, R7을
diagnostic/qualitative route로 고정하거나, 다음 learned target을 다른 route로 옮기는 것이다.

## 2026-06-30 R7 Attachment Observability Path Decision

R7 path decision을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining
selected_path = attempt_one_class_pair_balanced_r7_repair_before_diagnostic_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan
```

현재 560-row artifact 내부 repair capacity:

- `p_obs` subject/object-pair mixed groups `21`, balanced capacity `46`
- `p_obs` exact predicate x subject/object-pair mixed groups `0`, balanced capacity `0`
- observable `p_rel` subject/object-pair mixed groups `2`, balanced capacity `8`
- observable `p_rel` exact predicate x subject/object-pair mixed groups `0`, balanced capacity `0`

판단:

현재 artifact는 exact predicate/class-pair 내부에서 positive/negative가 섞인 target을 제공하지 않는다.
따라서 resampling으로 repair할 수 없고, learned smoke를 돌리면 class-pair prior memorization 문제가
반복된다. 하지만 full train source inventory는 `attached to`와 `hanging on` 각각 `185,346` candidate를
갖고 있으므로 R7을 바로 버리지 않고, 한 번의 class-pair-balanced repair mining pass를 시도한다.

선택:

- current 560-row learned smoke: reject
- object label 제거로 shortcut 회피: reject
- current 560-row만 재샘플링: reject
- `connected to` primary 승격: defer
- R7 즉시 diagnostic freeze: fallback, not selected yet
- full-train class-pair-balanced repair mining: selected next

다음 단계에서 repair mining이 실패하면 R7은 diagnostic/qualitative observability route로 고정하고,
다음 learned target은 다른 route로 이동하는 것이 맞다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Mining Plan

R7 class-pair repair mining plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready
selected_path = plan_exact_predicate_class_pair_capacity_scan_before_packet_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan
```

핵심 결정:

- candidate mining이나 packet materialization을 바로 시작하지 않는다.
- 먼저 full-train R7 후보에서 exact `predicate_label + subject_label + object_label` 기준 capacity scan을 실행한다.
- `attached to`와 `hanging on`만 primary repair predicate로 둔다.
- `connected to`는 explicit topology/functional evidence가 없으므로 diagnostic이다.

quota:

- `attached to`: capacity pass 후 최대 `240` packet rows, post-label accept/reject 최소 `50/100`
- `hanging on`: capacity pass 후 최대 `240` packet rows, post-label accept/reject 최소 `50/100`
- `connected to`: primary packet rows `0`, diagnostic only

capacity gate:

- balanced primary rows `>= 400`
- positive rows `>= 100`
- exact predicate/class-pair mixed strata `>= 20`

이 단계는 plan artifact이며 label fill, row materialization, packet creation, learned smoke는 실행하지 않았다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Capacity Scan

R7 class-pair repair capacity scan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining
selected_path = exact_predicate_class_pair_repair_candidate_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining
```

exact `predicate_label + subject_label + object_label` capacity:

- mixed groups: `4,616`
- raw balanced rows: `81,724`
- scan-capped balanced rows: `73,636`
- accept/reject/uncertain proxy rows: `79,491 / 257,849 / 33,352`

predicate별 결과:

- `attached to`: mixed groups `3,232`, scan-capped balanced rows `50,662`,
  accept/reject/uncertain `54,034 / 108,852 / 22,460`
- `hanging on`: mixed groups `1,384`, scan-capped balanced rows `22,974`,
  accept/reject/uncertain `25,457 / 148,997 / 10,892`

해석:

이전 560-row R7 artifact가 class-pair shortcut에 막힌 것은 R7 relation 자체에
mixed contrast가 없어서가 아니라, 재사용한 packet sampling이 exact predicate/class-pair
내 accept/reject contrast를 담지 못했기 때문이다. full-train 기준으로는 `attached to`와
`hanging on` 모두 class-pair-controlled repair candidate mining을 진행할 수 있다.

단, 이 결과는 proxy capacity scan이다. 아직 human/packet label, model-safe row, learned
smoke가 없으므로 H002 observability route의 성능 근거가 아니다. 다음 단계는 candidate mining이며,
그 뒤 packet/label ingestion과 schema/shortcut audit이 필요하다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Candidate Mining

R7 class-pair repair candidate mining을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan
```

선택된 후보:

- total rows: `480`
- predicate counts: `attached to 240`, `hanging on 240`
- proxy quota per predicate: accept `80`, reject `120`, uncertain `40`
- unique scans: `340`
- unique exact predicate/class-pair groups: `160`
- mixed exact class-pair groups: `attached to 80`, `hanging on 80`
- coverage: `joined_no_uncertainty_flags 279`, `joined_with_uncertainty_flags 201`
- geometry bucket: `far_separated 240`, `mid_or_ambiguous 80`, near/overlap-family `160`

해석:

R7은 여전히 learned evidence가 아니라 candidate 준비 단계다. 하지만 이전 blocker였던 exact
predicate/class-pair shortcut 문제는 candidate source 단계에서 repair 가능하다. 각 selected exact
class-pair group 안에 accept/reject proxy가 같이 들어가도록 구성했기 때문에, 다음 label ingestion 후
class-pair shortcut audit을 다시 걸 수 있다.

주의:

object label은 `wall`, `ceiling` 같은 anchor-heavy 분포를 갖는다. 이는 attachment/hanging route의
도메인 특성상 자연스럽지만, reviewer-risk 관점에서는 object-label prior가 target을 설명하는지 반드시
추후 schema/shortcut audit에서 다시 확인해야 한다. `connected to`는 explicit topology/functional evidence
부족으로 계속 diagnostic이다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Packet Materialization Plan

R7 class-pair repair packet materialization plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization
```

결과:

- visible packet plan rows: `480`
- hidden asset manifest rows: `480`
- evidence inventory rows: `480`
- `attached to`: `240`, `hanging on`: `240`
- evidence tier: `T1_pair_multiview_ready 480`
- scan/mesh/semseg/sequence ready: `480/480`
- subject/object multiview ready: `480/480`
- shared view ready: `480/480`
- shared frame ready: `64/480`
- limited/not-ready rows: `0`

해석:

이번 단계는 실제 packet을 만들지 않고, packet 생성 계약과 visible/hidden field boundary를 고정했다.
visible plan row에는 scan id, instance id, source/rank, proxy role, GT status, construction bucket,
file path를 넣지 않았고, hidden manifest에만 packet 생성을 위한 provenance를 보존했다.

따라서 R7은 packet materialization으로 넘어갈 수 있다. 하지만 아직 label fill, label ingestion,
schema/shortcut audit, learned smoke가 없으므로 H002 observability route의 성능 근거는 아니다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Packet Materialization

R7 class-pair repair packet materialization을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill
```

결과:

- packet rows: `480`
- label-ready rows: `480`
- non-ready rows: `0`
- `attached to|ready`: `240`
- `hanging on|ready`: `240`
- subject image rows: `480`
- object image rows: `480`
- pair crop rows: `480`
- observability card rows: `480`
- multiview sheet rows: `480`
- total subject thumbnails copied: `2772`
- total object thumbnails copied: `2804`
- visible leakage hits: `0`

해석:

이제 R7 `attached to`/`hanging on` class-pair repair 후보는 visible-only label fill을 진행할
수 있다. 단, 이 단계는 packet asset과 label-ready sheet를 만든 것이며 아직 relation reliability
label, target ingestion, schema/shortcut audit, learned smoke는 없다.

중요한 field boundary:

- visible sheet에는 packet path, scan id, instance id, source/rank, proxy role, GT status,
  construction bucket을 넣지 않았다.
- packet path와 source asset provenance는 hidden manifest에만 있다.
- multi-view/mesh는 현재 audit evidence이며 model input이 아니다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Label Fill

R7 class-pair repair visible packet label fill을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_completed
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion
```

label counts:

- total rows: `480`
- observability: `observable 455`, `uncertain 25`
- relation label: `accept 258`, `reject 90`, `abstain 132`
- evidence quality: `sufficient 458`, `partial 22`
- endpoint identity: `clear 476`, `ambiguous 4`

predicate별 relation label:

- `attached to|accept`: `172`
- `attached to|abstain`: `68`
- `attached to|reject`: `0`
- `hanging on|accept`: `86`
- `hanging on|reject`: `90`
- `hanging on|abstain`: `64`

해석:

visible packet label artifact는 ingestion 단계로 넘어갈 수 있다. 다만 `attached to`는 현재
visible-only 보수 label 기준에서 reject가 없으므로, 이 predicate 단독으로는 balanced binary
target이 아닐 가능성이 높다. 다음 ingestion과 schema/shortcut audit에서 observable target,
relation target, predicate별 target을 분리해 balance와 shortcut risk를 다시 확인해야 한다.

경계:

- visible review sheet와 packet assets만 사용했다.
- hidden manifest, source confidence/rank, GT status, construction bucket, existing target은 사용하지 않았다.
- label ingestion, model-safe row, learned smoke는 아직 실행하지 않았다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Label Ingestion

R7 class-pair repair label ingestion을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit
```

target artifacts:

- ingested target rows: `480`
- multiclass rows: `480`
- observability binary rows: `480`
- observable relation binary rows: `348`

target summary:

- relation multiclass: `accept 258`, `reject 90`, `abstain 132`
- observability: `observable 455`, `uncertain 25`
- `p_obs`: positive `455`, negative `25`
- observable `p_rel`: rows `348`, accept `258`, reject `90`
- `attached to` observable `p_rel`: accept `172`, reject `0`
- `hanging on` observable `p_rel`: accept `86`, reject `90`

판단:

combined observable `p_rel`과 `hanging on` observable `p_rel`은 schema/shortcut audit으로
넘길 수 있는 class mass를 갖는다. 반대로 `p_obs`는 negative가 `25`로 sparse하고,
`attached to` 단독 `p_rel`은 reject가 없으므로 diagnostic-only로 취급해야 한다.

quick shortcut preview는 `20`개 risk flag를 냈다. 특히 class-pair, subject label,
predicate, decision reason, hidden exact class-pair/id 계열이 target을 쉽게 설명할 가능성이 있다.
따라서 다음 단계는 learned smoke가 아니라 schema/shortcut audit이다.

## 2026-07-01 R7 Attachment Observability Class-Pair Repair Schema Shortcut Audit

R7 class-pair repair target에 대해 schema/shortcut audit을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_blocked_shortcut_risk
selected_path = block_learned_smoke_select_path_decision
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit
```

target viability:

- relation multiclass: `480` rows, `accept 258 / reject 90 / abstain 132`, diagnostic-only
- `p_obs`: `455/25`, negative-sparse
- combined observable `p_rel`: `348` rows, `258/90`, mass는 충분하지만 shortcut audit 필요
- `attached to` observable `p_rel`: `172/0`, single-class diagnostic-only
- `hanging on` observable `p_rel`: `86/90`, mass는 충분하지만 shortcut audit 필요

audit result:

- allowed high-risk blockers: `14`
- combined observable `p_rel`은 `predicate_subject_object_class_pair`만으로 majority accuracy `1.0`
  이다.
- `hanging on` observable `p_rel`은 `subject_label`, `subject_object_class_pair`,
  `predicate_subject_object_class_pair`가 각각 majority accuracy `1.0`이다.
- exact `predicate_subject_object_class_pair` 기준 mixed groups는 combined `p_rel`과
  `hanging on` 모두 `0`이다.

판단:

R7 class-pair repair는 label mass를 개선했지만 independent learned-smoke target을 만들지는
못했다. 현재 label은 attachment/observability compatibility보다 object-class/endpoint prior로
설명된다. 따라서 이 artifact로 learned smoke를 실행하면 H002의 `C_e`/`Q_e` 구조를 검증하는 것이
아니라 class prior memorization을 검증하게 된다.

R7 route 자체를 폐기하는 것은 아니다. 다만 현재 artifact는 diagnostic evidence로 고정하고,
다음 path decision에서 다음 중 하나를 선택해야 한다.

- R7을 diagnostic/qualitative observability route로 freeze
- truly mixed same-class-pair visual accept/reject row를 다시 mining
- R7을 binary `p_rel`보다 `p_obs`/abstention route로 재정의

## 2026-07-01 R7 Attachment Observability Class-Pair Repair Path Decision

R7 class-pair repair schema/shortcut audit 이후 path decision을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze
```

결정:

현재 R7 `attached to` / `hanging on` class-pair repair artifact는 diagnostic evidence로 freeze한다.
learned smoke, calibrated `p_rel`, calibrated `p_obs`, paper-level reliability evidence로 사용하지 않는다.

이유:

- row count 문제가 아니다. combined observable `p_rel`은 `258/90`, `hanging on`은 `86/90`으로
  수량만 보면 가능해 보인다.
- 하지만 combined `p_rel`은 `predicate_subject_object_class_pair`만으로 accuracy `1.0`이다.
- `hanging on`은 `subject_label`, `subject_object_class_pair`만으로도 accuracy `1.0`이다.
- `attached to`는 observable `p_rel`이 `172/0` single-class다.
- `p_obs`는 `455/25`로 negative-sparse하다.
- 한 번의 full-train class-pair repair mining을 이미 수행했는데, visible label 이후 exact class-pair
  mixed capacity가 `0`으로 붕괴했다.

reject한 route:

- current combined `p_rel` learned smoke
- `hanging on` only learned smoke
- 같은 proxy recipe로 class-pair repair mining 반복

defer한 route:

- truly mixed same-class-pair visual row mining
- low-observability/occlusion-focused `p_obs` route

해석:

R7은 H002 route taxonomy에서 observability-heavy relation family로 유지한다. 다만 현재 artifact는
main learned route가 아니라 negative/diagnostic result다. R7을 나중에 다시 살리려면 source proxy
bucket이 아니라 visible/mesh evidence-first target construction이 필요하다.

## 2026-07-01 Scope Synthesis After R7 Diagnostic Freeze

R7 diagnostic freeze 이후 H002 route scope synthesis를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze_ready
selected_path = scope_sufficient_after_r7_freeze_select_paper_framework_readiness_review
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes
```

결정:

현재 H002 route coverage는 hypothesis-stage relation-aware evidence routing framework를 논의하기에
충분하다. 새 relation family mining은 지금 추가하지 않는다. 다음 병목은 family 부족이 아니라,
어떤 artifact와 claim을 paper/framework planning으로 승격할 수 있는지 readiness를 점검하는 것이다.

최종 route boundary:

- main mechanism evidence: `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact`
- geometry-easy control/generality: `close by`
- superordinate decomposition diagnostic: `supported by`
- observability-heavy diagnostic/future: `attached to`, `hanging on`, `connected to`
- future/separate route: containment, `cover`, `leaning against`, identity/symmetry, semantic/structural relations

해석:

R7 freeze는 H002의 main mechanism claim을 약화시키기보다 claim boundary를 선명하게 만든다.
H002는 “모든 relation을 해결했다”가 아니라, relation family마다 필요한 evidence route와 target
definition이 다르다는 framework다. 따라서 R7은 current artifact로는 main learned evidence가
아니지만, observability-aware route가 왜 필요한지 보여주는 diagnostic boundary로 유지한다.

blocked claims:

- all-family generality
- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- current R7 learned reliability
- support/contact fully solved

## 2026-07-01 Paper/Framework Readiness Review

Route-specific probe 이후 paper/framework readiness review를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes/
status = h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_ready
selected_path = readiness_review_completed_select_promotion_gap_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review
```

핵심 판단:

현재 H002는 hypothesis-stage framework로는 준비됐다. 즉, relation-aware evidence routing
claim을 구성할 수 있고 candidate main mechanism table을 정의할 수 있다. 하지만 아직
paper-level result는 아니다. Docker 재현, held-out grouped evaluation, calibration/selective
decision, claim wording lock이 남아 있다.

candidate main mechanism rows:

- `relative_vertical`: `higher than`, `lower than`
- `size_relative`: `bigger than`, `smaller than`
- `relative_horizontal`: `left`, `right`, `front`, `behind`
- `support_contact`: `standing on`, `lying on`

diagnostic/control/boundary rows:

- `close by`: geometry-only route control
- `supported by`: superordinate support decomposition / relabel / abstain diagnostic
- `attached to`, `hanging on`, `connected to`: observability-heavy diagnostic/future boundary
- containment, `cover`, `leaning against`, identity/symmetry, semantic/structural relations: deferred taxonomy boundary

현재 blocked claims:

- paper-level reliability improvement
- calibrated `p_rel` / `p_obs`
- all-family generality
- current R7 attachment-like learned reliability
- support/contact fully solved
- complete 3DSSG relation coverage

## 2026-07-01 Promotion Gap Plan

Paper/framework readiness review 이후 promotion gap plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review/
status = h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_ready
selected_path = promotion_gap_plan_ready_select_docker_heldout_protocol_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan
```

핵심 결정:

H002는 train-only route probe에서 바로 paper result로 넘어가면 안 된다. 다음 단계는
Docker + held-out grouped protocol plan이다. 이 단계에서도 아직 experiment root를 만들지 않고,
어떤 data mount, split, output manifest, leakage audit, control table이 필요한지 먼저 고정한다.

승격 후보 route:

- `relative_vertical`: `higher than`, `lower than`
- `size_relative`: `bigger than`, `smaller than`
- `relative_horizontal`: `left`, `right`, `front`, `behind`
- `support_contact`: `standing on`, `lying on`

현재 path에서 paper-level로 승격하지 않는 route:

- `close by`: geometry-only route control
- `supported by`: superordinate decomposition / relabel / abstain diagnostic
- `attached to`, `hanging on`, `connected to`: observability-heavy diagnostic/future boundary
- containment, `cover`, `leaning against`, identity/symmetry, semantic/structural: deferred route taxonomy

승격 gate:

1. Docker reproduction
2. held-out grouped evaluation
3. calibration/selective decision, only if `p_rel` / `p_obs` claim is kept
4. target-independence replication
5. paper claim wording lock

따라서 다음 H002 작업은 새 model이나 새 relation mining이 아니라
`compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan`이다.

## 2026-07-01 Docker Heldout Protocol Plan

Promotion gap plan 이후 Docker + grouped-holdout protocol plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan/
status = h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready
selected_path = docker_heldout_protocol_ready_select_experiment_root_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan
```

핵심 결정:

아직 `experiments/H002_compatibility_routing/`, `configs/h002/`,
`results/h002_compatibility_routing/`는 만들지 않았다. 이번 단계는 protocol plan만 고정한다.

제안된 future roots:

- `experiments/H002_compatibility_routing/`
- `configs/h002/`
- `results/h002_compatibility_routing/`

승격 후보 route는 그대로 유지한다.

- `relative_vertical`
- `size_relative`
- `relative_horizontal`
- `support_contact`

중요한 경계:

현재 heldout은 H002 candidate source pool 안에서 `scan_id`와 endpoint pair를 기준으로 나누는
grouped holdout이다. 공식 validation/test를 사용한 것이 아니며, 공식 split을 채택하려면 별도
protocol이 필요하다.

Docker protocol이 요구하는 산출물:

- mount check
- split manifest
- route rows
- model-safe view
- hidden manifest
- route metrics
- control metrics
- leakage audit
- validation errors file

다음 단계는 protocol을 바탕으로 minimal experiment/config/results skeleton을 만드는 것이다. 그때는
durable root가 생기므로 `experiments/README.md`, `configs/README.md`, `docs/index.md`, root
`TODO.md`도 함께 갱신해야 한다.

## 2026-07-01 Experiment Root Skeleton

Docker heldout protocol plan 이후 H002 experiment/config/results skeleton을 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan/
status = h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_ready
selected_path = experiment_config_results_skeleton_created_select_docker_preflight_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton
```

생성한 durable roots:

- `experiments/H002_compatibility_routing/`
- `configs/h002/`
- `results/h002_compatibility_routing/`

업데이트한 owner/index:

- `experiments/README.md`
- `configs/README.md`
- `results/README.md`
- `docs/index.md`
- root `TODO.md`

현재 경계:

- Docker preflight는 아직 실행하지 않았다.
- grouped-holdout metric은 아직 없다.
- official validation/test는 사용하지 않았다.
- paper-level H002 metric은 아직 없다.
- H001 artifact는 수정하지 않았다.

다음 작업은 `configs/h002/compose.yaml`과 최소 preflight runner를 구현하고, Docker 안에서 mount와
이전 artifact status를 확인하는 것이다.

## 2026-07-01 Docker Preflight Implementation

H002 Docker preflight service를 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton/
status = h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_ready
selected_path = docker_preflight_passed_select_route_materialization_protocol_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight
```

구현한 파일:

- `configs/h002/Dockerfile`
- `configs/h002/compose.yaml`
- `experiments/H002_compatibility_routing/scripts/preflight.py`

실행한 명령:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-protocol-check
```

결과:

- Docker preflight exit 0.
- mount/status check validation errors 0.
- `results/h001_geom_reliability/` read-only 확인.
- `archive/experiments/H001_geom_reliability/` read-only 확인.
- route materialization은 아직 하지 않았다.
- grouped-holdout metric은 아직 없다.
- official validation/test는 사용하지 않았다.
- paper-level H002 metric은 아직 없다.

preflight output:

- `experiments/H002_compatibility_routing/preflight/latest/mount_check.json`
- `experiments/H002_compatibility_routing/preflight/latest/run_manifest.json`
- `experiments/H002_compatibility_routing/preflight/latest/validation_errors.jsonl`

다음 단계는 Docker route materialization protocol implementation이다. 즉, route rows,
model-safe view, hidden manifest, row manifest를 어떤 schema로 생성할지 먼저 구현하고 검증해야 한다.

## 2026-07-01 Route Materialization Protocol Implementation

H002 Docker route materialization service를 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight/
status = h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready
selected_path = docker_materialized_promoted_routes_select_materialization_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization
```

실행한 명령:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes
```

생성한 runtime output:

- `experiments/H002_compatibility_routing/materialization/latest/route_rows.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/model_safe_view.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/hidden_manifest.jsonl`
- `experiments/H002_compatibility_routing/materialization/latest/row_manifest.json`
- `experiments/H002_compatibility_routing/materialization/latest/validation_errors.jsonl`

Promoted route materialization count:

| Route family | Rows | Label 0 | Label 1 |
| --- | ---: | ---: | ---: |
| `relative_vertical` | 1512 | 756 | 756 |
| `size_relative` | 2400 | 1200 | 1200 |
| `relative_horizontal` | 2400 | 1200 | 1200 |
| `support_contact` | 640 | 320 | 320 |

총 `6952` row가 materialize되었고 validation errors는 `0`이다.

중요한 boundary:

- 이 단계는 metric이 아니라 row-level protocol materialization이다.
- grouped-holdout, official validation/test, paper-level H002 metric은 아직 없다.
- `protocol_split`은 아직 `unassigned_pre_grouped_holdout`이다.
- 다음 `C_e` audit에서는 `T_e + G_e`만 compatibility input으로 허용한다.
- `Q_e`와 `Z_e`는 저장만 하고, 다음 compatibility audit에는 input으로 넣지 않는다.

## 2026-07-01 Materialization Schema Audit

H002 Docker materialization schema audit service를 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization/
status = h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_ready
selected_path = schema_audit_passed_select_grouped_split_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit
```

실행한 명령:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialization-schema-audit
```

결과:

- schema errors: `0`
- blocked `C_e` field hits in `T_e + G_e`: `0`
- high-risk `C_e` allowed shortcut warnings: `0`
- shortcut probes: `50`
- split-ready route families: `4/4`

Split readiness:

| Route family | Rows | CV groups | Mixed-label groups | Split ready |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 1512 | 1026 | 486 | `True` |
| `size_relative` | 2400 | 1200 | 1200 | `True` |
| `relative_horizontal` | 2400 | 1200 | 1200 | `True` |
| `support_contact` | 640 | 258 | 155 | `True` |

Boundary:

- 이 단계는 schema/leakage/split-readiness audit이다.
- grouped-holdout metric, official validation/test, paper-level H002 metric은 아직 없다.
- 다음 단계는 materialized H002 candidate pool에 대한 grouped split protocol이다.

## 2026-07-01 Grouped Split Protocol

H002 Docker grouped split service를 구현하고 검증했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit/
status = h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready
selected_path = grouped_split_ready_select_grouped_eval_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split
```

실행한 명령:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-split
```

생성한 runtime output:

- `experiments/H002_compatibility_routing/splits/latest/model_safe_split_view.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/split_assignments.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/group_manifest.jsonl`
- `experiments/H002_compatibility_routing/splits/latest/split_manifest.json`
- `experiments/H002_compatibility_routing/splits/latest/route_split_counts.csv`
- `experiments/H002_compatibility_routing/splits/latest/predicate_split_counts.csv`
- `experiments/H002_compatibility_routing/splits/latest/leakage_audit.csv`

결과:

- `6952` row 전체가 `internal_train`, `internal_dev`, `internal_heldout`으로 split되었다.
- `3684`개 `cv_group_id` group이 split assignment를 받았다.
- `cv_group_single_split` violation은 `0`이다.
- official validation/test usage는 `0`이다.
- grouped heldout metric은 아직 없다.

Route split summary:

| Route family | Train rows | Dev rows | Heldout rows |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 1680 | 360 | 360 |
| `relative_vertical` | 1059 | 227 | 226 |
| `size_relative` | 1680 | 360 | 360 |
| `support_contact` | 449 | 97 | 94 |

Boundary:

- 이 split은 H002 candidate pool 내부 split이다.
- official validation/test가 아니며, paper metric도 아니다.
- 다음 단계는 grouped evaluation protocol 작성이다.
- grouped evaluation에서는 semantic-only, geometry-only, `T_e + G_e` concat,
  `T_e x G_e` compatibility, wrong-`T_e`, shuffled-`G_e`를 먼저 비교해야 한다.

## 2026-07-01 Grouped Evaluation Protocol

H002 grouped evaluation protocol을 작성하고 검증했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
status = h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready
selected_path = grouped_eval_protocol_ready_select_grouped_eval_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_runner_after_protocol
```

평가 scope:

- target: `C_e`
- train split: `internal_train`
- dev split: `internal_dev`
- heldout split: `internal_heldout`
- rows: `6952`
- official validation/test: 사용하지 않음
- paper metric: 생성하지 않음

Model view contract:

| View | 의미 |
| --- | --- |
| `M0_constant` | majority/prior sanity baseline |
| `M1_T_semantic_only` | `T_e`만 쓰는 semantic-content baseline |
| `M2_G_geometry_only` | `G_e`만 쓰는 predicate-independent geometry baseline |
| `M3_T_plus_G_concat` | explicit interaction 없는 단순 concat baseline |
| `M4_TxG_compatibility` | primary predicate-geometry compatibility model |
| `C1_wrong_T_control` | wrong semantic condition control |
| `C2_shuffled_G_control` | shuffled geometry control |
| `D1_Z_source_confidence_diagnostic` | source confidence diagnostic only |
| `D2_Q_observability_diagnostic` | observability diagnostic only |

Boundary:

- main `C_e`에는 `T_e`와 `G_e`만 사용한다.
- `Z_e`와 `Q_e`는 diagnostic-only이며, `p_rel` / `p_obs` claim은 아직 켜지 않는다.
- 다음 단계는 grouped evaluation runner 구현이다.

## 2026-07-01 Grouped Evaluation Runner

H002 grouped evaluation runner를 Docker로 실행하고, stage artifact 검증까지 완료했다.

```text
runtime_output = experiments/H002_compatibility_routing/evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol/
status = h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready
selected_path = grouped_eval_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_result_review_after_runner
```

이번 실행은 `internal_train`으로 학습하고 `internal_dev`, `internal_heldout`에 대해
metric을 생성했다. official validation/test는 사용하지 않았고, paper-level result도
생성하지 않았다. Main `C_e` model은 protocol대로 `T_e`와 `G_e`만 사용했으며,
`Z_e`와 `Q_e`는 diagnostic-only로 유지했다.

Internal heldout overall:

| Model view | AUROC | Balanced acc | Macro-F1 |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.454321 | 0.473511 | 0.472981 |
| `M2_G_geometry_only` | 0.487690 | 0.487514 | 0.439911 |
| `M3_T_plus_G_concat` | 0.465868 | 0.487921 | 0.487420 |
| `M4_TxG_compatibility` | 0.925990 | 0.819719 | 0.819214 |
| `C1_wrong_T_control` | 0.066622 | 0.177321 | 0.176676 |
| `C2_shuffled_G_control` | 0.500808 | 0.496282 | 0.494069 |

Internal heldout `M4_TxG_compatibility` by family:

| Family | AUROC | Balanced acc | Macro-F1 | Rows |
| --- | ---: | ---: | ---: | ---: |
| `relative_horizontal` | 0.969537 | 0.908333 | 0.908333 | 360 |
| `relative_vertical` | 0.457834 | 0.499606 | 0.488899 | 226 |
| `size_relative` | 0.999969 | 0.994444 | 0.994444 | 360 |
| `support_contact` | 0.616395 | 0.595109 | 0.595011 | 94 |

해석:

- Aggregate metric은 `T_e x G_e` compatibility가 `T_e`-only, `G_e`-only, 단순
  concat, wrong-`T_e`, shuffled-`G_e`보다 강한 signal을 갖는다는 점을 보인다.
- 그러나 family-level 결과는 균일하지 않다.
- `size_relative`와 `relative_horizontal`은 현재 materialized target에서 강한
  compatibility-route evidence다.
- `support_contact`는 partial/challenging compatibility evidence다. 절대 성능보다
  baseline/control 대비 interaction 필요성을 중심으로 해석해야 한다.
- `relative_vertical`은 현재 grouped heldout에서 실패한다. target construction,
  feature definition, direction/predicate symmetry, or split composition 문제를
  result-review에서 분리해야 한다.

따라서 다음 단계는 model을 더 돌리는 것이 아니라 result review다. 어떤 family를
claim-supporting evidence로 둘지, 어떤 family를 diagnostic/failure evidence로 둘지,
그리고 `relative_vertical`을 repair할지 제외할지 결정해야 한다.

## 2026-07-01 Grouped Evaluation Result Review

Grouped evaluation 결과를 family별로 리뷰하고 claim boundary를 임시 판정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/
status = h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready
selected_path = grouped_review_ready_select_relative_vertical_failure_analysis
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review
```

Family-level 판정:

| Family | Heldout M4 AUROC | Status | Role |
| --- | ---: | --- | --- |
| `relative_horizontal` | 0.969537 | claim-supporting | main compatibility-route evidence |
| `relative_vertical` | 0.457834 | failed | do not promote without repair |
| `size_relative` | 0.999969 | claim-supporting | main compatibility-route evidence |
| `support_contact` | 0.616395 | partial | challenging compatibility-route evidence |

이 판정은 H002 방향을 약화시키는 것이 아니라 claim을 더 정밀하게 만든다. 현재
aggregate result만 사용하면 `relative_vertical` 실패가 가려진다. 반대로 family-level로
분리하면 H002의 핵심 주장인 relation-aware evidence route가 더 명확해진다.

현재 논문 claim에 가까운 표현은 다음이다.

```text
Predicate-geometry compatibility can be learned for selected relation families,
but the required evidence route and target reliability differ by relation family.
```

즉, 모든 family가 같은 `C_e` head로 해결됐다고 주장하면 안 된다. `size_relative`와
`relative_horizontal`은 compatibility-route evidence로 쓸 수 있고, `support_contact`는
partial/challenging evidence로 제한해야 하며, `relative_vertical`은 실패 원인을 분석한
뒤 repair하거나 main claim에서 제외해야 한다.

## 2026-07-01 Relative-Vertical Failure Analysis

Grouped result review 이후 `relative_vertical` 실패 원인을 분석했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/
status = h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready
selected_path = repair_grouped_eval_compatibility_feature_extractor_then_rerun
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis
```

핵심 결론:

- `relative_vertical` 실패는 relation family 자체의 실패가 아니라 grouped runner의
  compatibility feature extraction 문제다.
- Intended feature인 `predicate_sign * raw_geometry_feature_vector.center_delta_z`는
  internal heldout에서 AUROC `1.000000`이다.
- 그러나 runner의 suffix-based `center_delta_z` candidate는 AUROC `0.504808`이다.
- 원인은 `numeric_value(..., "center_delta_z")`가 실제 raw value가 아니라
  `raw_geometry_feature_available_mask.center_delta_z`를 먼저 선택한 것이다.
- 따라서 현재 `M4_TxG_compatibility`의 `relative_vertical` failure는 scientific
  negative result가 아니라 implementation repair-needed 상태다.

이 분석은 H002 claim에 중요하다. `higher than` / `lower than`은 같은 z-axis evidence를
predicate에 따라 반대로 해석해야 하므로 `T_e x G_e` interaction이 필요한 대표 route다.
따라서 다음 단계에서는 `relative_vertical`을 버리지 말고, grouped runner가 explicit raw
geometry path를 읽도록 고친 뒤 grouped evaluation을 재실행해야 한다.

## 2026-07-01 Grouped Eval Feature Extractor Repair

`relative_vertical` failure analysis에서 확인된 grouped eval runner의 feature extraction
문제를 수정하고 Docker grouped evaluation을 재실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/
status = h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready
selected_path = feature_extractor_repair_ready_select_claim_boundary_review
validation_errors = 0
next_todo = compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

수정 내용:

- `compatibility_features()`가 suffix match로 geometry 값을 찾지 않도록 수정했다.
- `center_delta_z`, `normalized_center_delta_z`, size ratio, horizontal delta,
  support/contact gap/overlap을 explicit raw geometry path로 읽도록 했다.
- Repair probe에서 `center_delta_z` raw value와 repaired numeric value가 일치했다.

Repaired internal heldout:

| Family | Heldout M4 AUROC | Status |
| --- | ---: | --- |
| `relative_horizontal` | 0.969568 | claim-supporting |
| `relative_vertical` | 0.999921 | claim-supporting |
| `size_relative` | 0.999969 | claim-supporting |
| `support_contact` | 0.610960 | partial/challenging |

Overall heldout:

| View | AUROC |
| --- | ---: |
| `M1_T_semantic_only` | 0.454321 |
| `M2_G_geometry_only` | 0.487690 |
| `M3_T_plus_G_concat` | 0.465868 |
| `M4_TxG_compatibility` | 0.984976 |
| `C1_wrong_T_control` | 0.014425 |
| `C2_shuffled_G_control` | 0.493975 |

해석:

- `relative_vertical`은 implementation repair 후 claim-supporting evidence로 복구됐다.
- 현재 claim-supporting internal evidence는 `relative_horizontal`,
  `relative_vertical`, `size_relative`다.
- `support_contact`는 여전히 partial/challenging route로 남긴다.
- 아직 official validation/test나 paper-level result는 아니다. 다음 단계는 repaired
  grouped result 기준의 claim-boundary review다.

## 2026-07-01 Repaired Grouped-Eval Claim Boundary Review

수리된 grouped evaluation 결과를 기준으로 H002의 hypothesis-stage claim boundary를
고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/
status = h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready
selected_path = claim_boundary_locked_select_official_validation_test_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

현재 허용되는 claim은 다음으로 제한한다.

- `C_e = compatibility(T_e, G_e)`는 internal grouped holdout에서 `T_e` only,
  `G_e` only, plain `T_e + G_e`, wrong-`T_e`, shuffled-`G_e`보다 강한
  discrimination을 보인다.
- relation family마다 필요한 evidence route가 다르며, fixed semantic-geometry fusion
  하나로 모든 relation을 처리한다고 주장하면 안 된다.
- `relative_horizontal`, `relative_vertical`, `size_relative`는 main internal
  compatibility evidence다.
- `support_contact`는 partial/challenging evidence이며 solved family가 아니다.

현재 blocked claim은 다음이다.

- official validation/test relation prediction metric 개선.
- calibrated `p_rel` 또는 selective `p_obs` reliability.
- `support_contact` solved claim.
- 모든 3DSSG relation type으로의 일반화.
- aggregate `M4` AUROC만으로 H002 전체를 입증했다는 주장.

따라서 다음 단계는 추가 내부 grouped metric이 아니라 official validation/test protocol
plan이다. 내부 candidate-pool metric을 paper metric으로 승격하려면, official split,
source candidate extraction, metric target, leakage/shortcut audit, paper table wording을
먼저 고정해야 한다.

## 2026-07-01 Official Validation/Test Protocol Plan

Claim-boundary review 이후 official validation/test protocol plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/
status = h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready
selected_path = official_protocol_ready_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

핵심 결정:

- official validation을 먼저 사용한다.
- test는 local label file 또는 evaluation server가 확인되고, protocol/code/metric/wording이
  freeze된 뒤에만 single final evaluation으로 사용한다.
- 이번 단계는 official validation metric이 아니라 split inventory와 protocol planning이다.
- 현재 H002 paper promotion의 primary route는 `GT_counterfactual_mechanism`이고,
  `VL-SAT_source_candidates`와 `Open3DSG_source_candidates`는 source bridge route로 둔다.
- `p_rel` / `p_obs`는 아직 optional future protocol이다.

Local `3DSSG_subset` inventory:

| Split | Scans | Relations |
| --- | ---: | ---: |
| `train` | 3852 | 81190 |
| `validation` | 548 | 11254 |
| `test` | 0 | 0 |

Validation family capacity:

| Family | Count |
| --- | ---: |
| `relative_horizontal` | 5474 |
| `relative_vertical` | 390 |
| `size_relative` | 170 |
| `support_contact` | 1589 |

다음 단계는 official source inventory다. 확인해야 할 것은 validation GT relation capacity만이
아니라, object geometry join 가능성, VL-SAT/Open3DSG source prediction 후보 가용성,
그리고 local test file 부재 또는 대체 evaluation route다.

## 2026-07-01 Official Source Inventory After Protocol Plan

`compatibility_dataset_v3_official_source_inventory_after_protocol_plan`을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
status = h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready
selected_path = official_source_inventory_ready_select_candidate_materialization_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory
```

이 단계의 목적은 official validation metric을 실행하는 것이 아니라, official split에서
H002 promoted route를 materialize할 수 있는지 확인하는 것이다.

GT/object geometry inventory:

| Family | Validation GT relations | Unique scans | OBB pair coverage | Status |
| --- | ---: | ---: | ---: | --- |
| `relative_horizontal` | 5474 | 155 | 1.000000 | candidate_ready |
| `relative_vertical` | 390 | 63 | 1.000000 | candidate_ready |
| `size_relative` | 170 | 35 | 1.000000 | candidate_ready |
| `support_contact` | 1589 | 156 | 1.000000 | candidate_ready |

Source bridge inventory:

- `vlsat_full_validation` source candidates: `relative_horizontal 147232`,
  `relative_vertical 73616`, `size_relative 73616`, `support_contact 73616`.
- `open3dsg_recovery_relaxed_views_min2` source candidates:
  `relative_horizontal 107064`, `relative_vertical 53532`, `size_relative 53532`,
  `support_contact 53532`.
- H001 geometry verification is checkable for `relative_vertical` and
  `support_contact`, but unsupported for `relative_horizontal` and
  `size_relative`.

따라서 다음 protocol에서 중요한 것은 H001 `p_geom_valid`를 그대로 H002의 main `G_e`로
재사용하는 것이 아니라, family별로 H002-specific geometry evidence를 materialize하는
것이다. 특히 `relative_horizontal`은 reference-frame-aware `G_e`, `size_relative`은
size-ratio `G_e`가 필요하다. `support_contact`는 source/geometry candidate가 충분하지만
내부 결과상 partial/challenging route이므로 solved family로 승격하지 않는다.

Boundary:

- official validation metric 생성 없음.
- official test 사용 없음.
- paper-level result 생성 없음.
- calibrated `p_rel` / `p_obs` claim 생성 없음.
- H001 source artifacts는 read-only inventory로만 사용.

당시 다음 단계는 official candidate materialization protocol이었다. 이 단계에서
model-safe view, hidden manifest, GT/counterfactual construction, source candidate bridge,
family별 `G_e` construction, leakage/shortcut audit contract를 고정해야 했다.

## 2026-07-01 Official Candidate Materialization Protocol

`compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory`를
완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
status = h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready
selected_path = official_candidate_materialization_protocol_ready_select_docker_materializer
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol
```

이번 단계의 결정:

- official validation GT를 primary anchor로 사용한다.
- 같은 object pair에서 predicate counterfactual을 만든다.
- family-specific `G_e`를 H002에서 직접 구성한다.
- H001 VL-SAT/Open3DSG source artifacts는 read-only secondary bridge로만 사용한다.
- `source_score`, rank, H001 `p_geom_valid`, construction proxy는 main `C_e`
  model-safe features에서 금지한다.
- 아직 row materialization, official validation metric, paper metric은 없다.

Family route contract:

| Route family | GT rows | Role | `G_e` policy |
| --- | ---: | --- | --- |
| `relative_horizontal` | 5474 | main frame-aware route | OBB centroid 기반 signed horizontal/depth deltas |
| `relative_vertical` | 390 | main signed-geometry route | OBB center/bottom/top vertical deltas |
| `size_relative` | 170 | main size route | OBB axes, volume, height, footprint size ratios |
| `support_contact` | 1589 | diagnostic/challenging route | contact gap, vertical order, footprint overlap, pose proxy |

다음 단계는 `/home/yoohyun/research/experiments/H002_compatibility_routing`에서
Docker service `h002-official-materialize-candidates`를 구현하는 것이다. 이 구현은
paper-level metric 실행이 아니라 official validation candidate rows, model-safe view,
hidden manifest, row manifest, validation errors를 생성하는 materialization 단계다.

## 2026-07-01 Official Candidate Materialization Docker Implementation

`h002-official-materialize-candidates` Docker service를 구현하고 실행했다.

```text
runtime_root = experiments/H002_compatibility_routing/official_materialization/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol/
status = h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready
selected_path = official_materialization_ready_select_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation
```

Runtime output:

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

Candidate origins:

- official GT positive: `7623`
- same-pair predicate counterfactual: `15439`

해석:

- official validation candidate rows는 Docker에서 생성됐다.
- 이 결과는 아직 metric이 아니라 materialized dataset artifact다.
- main `C_e` feature boundary는 `T_e` + H002-specific `G_e`이고, `Q_e`/`Z_e`는
  diagnostic-only다.
- 다음 단계는 model-safe view와 hidden manifest의 schema/shortcut audit이다.

## 2026-07-01 Official Candidate Materialization Schema Audit

Official materialized rows의 schema/shortcut/control-readiness audit을 완료했다.

```text
runtime_root = experiments/H002_compatibility_routing/official_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation/
status = h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats
selected_path = schema_audit_ready_select_official_metric_protocol_freeze
validation_errors = 0
shortcut_warnings = 1
next_todo = compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

통과한 항목:

- schema violations: `0`
- blocked field hits in main `T_e`/`G_e`: `0`
- model-safe/hidden candidate id alignment: `23062/23062`
- runtime validation errors: `0`
- control-readiness blockers: `0`

Label balance:

| Route family | Rows | Label 0 | Label 1 | Dataset weight |
| --- | ---: | ---: | ---: | ---: |
| `relative_horizontal` | 18764 | 13290 | 5474 | 0.813633 |
| `relative_vertical` | 780 | 390 | 390 | 0.033822 |
| `size_relative` | 340 | 170 | 170 | 0.014743 |
| `support_contact` | 3178 | 1589 | 1589 | 0.137802 |

Caveat:

- `support_contact`에서 `predicate_x_class_pair` majority accuracy가 `0.993707`이다.
- 이는 `support_contact`를 solved/main claim으로 올릴 수 없다는 강한 근거다.
- 다음 metric protocol은 family-wise, macro-average, weighted-average, route controls를
  반드시 포함해야 한다. Overall aggregate는 `relative_horizontal`에 지배될 수 있으므로
  secondary metric으로만 둔다.

## 2026-07-01 Official Metric Protocol Freeze

Official validation metric을 실행하기 전에 metric protocol을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
status = h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready
selected_path = official_metric_protocol_frozen_select_official_metric_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_runner_after_protocol_freeze
```

고정된 핵심 계약:

- official validation rows는 eval-only다.
- trainable view는 internal train에서 fit하고 internal dev에서만 selection/threshold를 정한다.
- primary metric은 `macro_family_AUROC`이다.
- weighted-family AUROC와 overall AUROC는 secondary다.
- main `C_e`는 `T_e`와 `G_e`만 사용한다.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields는 main `C_e`에서 제외한다.
- wrong-`T`, shuffled-`G`, subject/object swap, sign flip, horizontal frame control을 보고해야 한다.
- `support_contact`는 challenging/diagnostic route로 보고하며 solved claim으로 올리지 않는다.

이 단계는 protocol freeze이며 official validation metric이나 paper-level result를 만들지 않았다.

## 2026-07-01 Official Metric Runner

Frozen protocol에 따라 Docker official validation metric runner를 실행했다.

```text
runtime_root = experiments/H002_compatibility_routing/official_evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
status = h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats
selected_path = official_metric_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_result_review_after_runner
```

Main result:

| View | Macro-family AUROC | Weighted-family AUROC | Overall AUROC |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.417633 | 0.455374 | 0.404333 |
| `M2_G_geometry_only` | 0.500000 | 0.500000 | 0.528329 |
| `M3_T_plus_G_concat` | 0.416923 | 0.454625 | 0.406137 |
| `M4_TxG_compatibility` | 0.835547 | 0.720781 | 0.724835 |

Family-level M4:

- `relative_vertical`: AUROC `0.991321`
- `size_relative`: AUROC `0.999585`
- `relative_horizontal`: AUROC `0.719568`, but frame-control margin is weak
- `support_contact`: AUROC `0.631712`, challenging/diagnostic only

Control result:

- M4 beats semantic-only, geometry-only, and concat at macro-family level.
- wrong-`T`, shuffled-`G`, subject/object swap, and sign flip controls degrade.
- horizontal frame-swap control has weak macro delta `0.038149`, so
  `relative_horizontal` needs result review before a strong claim.

Boundary:

- official validation metric exists now.
- official validation was eval-only.
- official test was not used.
- paper-level H002 result has not been promoted.
- `p_rel` / `p_obs` remain disabled.

## 2026-07-02 Official Metric Result Review

Official metric runner 결과를 paper-level experiment gate 관점에서 검토했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
status = h002_compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries
selected_path = official_metric_review_ready_select_claim_boundary_lock
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

Gate decision:

- Docker official metric runner: pass
- official validation eval-only / official test unused: pass
- main `C_e` feature boundary `T_e + G_e`: pass
- primary metric vs baselines: pass
- wrong-`T` / shuffled-`G` controls: pass
- `relative_horizontal` frame control: caveat
- `support_contact`: diagnostic only
- paper promotion: conditional pass, not final promotion

Family claim boundary:

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

별도 보고서:

```text
report/report_0702.md
```
