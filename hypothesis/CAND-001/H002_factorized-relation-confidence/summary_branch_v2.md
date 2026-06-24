# H002 Summary Branch V2

Last updated: 2026-06-24 KST

## Research Direction

H002는 3D Scene Graph relation prediction에서 relation-level reliability를 다루는
독립 연구 방향이다. 핵심 문제는 relation source가 주는 하나의 semantic confidence를
그대로 믿지 않고, 그 score가 실제 3D geometry validity와 어떻게 일치하거나 충돌하는지
분리해서 보는 것이다.

핵심 주장:

```text
semantic score != geometry validity != relation reliability
```

H002의 목표는 이 mismatch를 양방향 relation-level reliability 문제로 정의하고,
`RGA(Relation-Geometric Agreement)` framework로 측정한 뒤, 충분히 독립적인 target이
확보될 때만 factorized reliability posterior를 검증하는 것이다.

현재 상태:

```text
current_gate = v22 hanging-on strict candidate mining completed
current_status = hanging-on strict 240-row candidate sheet is ready for source inventory
posterior_evidence = false
paper_metric_evidence = false
validation_or_test_used = false
next_gate = reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
```

## Motivation

기존 3D Scene Graph relation predictor는 relation 후보에 하나의 score 또는 rank를
부여한다. 이 score에는 semantic plausibility, object label prior, visual-language prior,
geometry cue, dataset frequency가 섞일 수 있다.

문제는 score가 높다고 해서 relation이 실제 3D geometry에서 성립한다는 뜻은 아니라는
점이다.

예:

- `chair close by table`은 semantic prior로는 그럴듯하지만 실제 거리상 가깝지 않을 수 있다.
- `object standing on table`은 label상 plausible해도 support/contact geometry가 없을 수 있다.
- `picture higher than sofa`는 vertical order는 맞아도 attachment/context evidence가 부족할 수 있다.
- 반대로 source가 낮게 ranking한 relation이 geometry상은 satisfied일 수 있다.

따라서 H002는 failure case를 양방향 mismatch로 본다.

```text
high semantic + low geometry = semantic overconfidence
low semantic + high geometry = semantic underconfidence or missed relation
```

## Problem Definition

Given a relation candidate:

```text
e = (subject, predicate, object)
```

H002는 다음 질문을 분리한다.

```text
1. semantic plausibility: relation source가 이 edge를 얼마나 그럴듯하게 보는가?
2. geometry validity: observed 3D geometry가 이 predicate를 지지하는가?
3. relation reliability: semantic, geometry, coverage, uncertainty를 함께 볼 때 이 edge를 신뢰할 수 있는가?
```

H002의 RGA state:

```text
RGA(e) = {
  semantic_axis,
  geometry_axis,
  label_or_audit_axis,
  coverage_state,
  uncertainty_state,
  disagreement_score
}
```

Target posterior 후보:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

단, 이 posterior는 현재 paper-level claim이 아니다. Target-independence gate가 통과되기
전에는 posterior smoke를 실행하지 않는다.

## Edge Components

| Component | Meaning | Role In H002 |
| --- | --- | --- |
| `semantic_score` | relation source가 부여한 relation confidence 또는 rank | semantic plausibility axis |
| `object_confidence` | subject/object class와 instance confidence | optional evidence; 현재 smoke에서는 제한적으로만 사용 |
| `geometry_evidence` | distance, vertical order, contact, overlap, support, containment 등 | relation-specific witness |
| `geometry_validity` | geometry상 relation이 성립할 가능성. 현재는 `p_geom_valid`와 deterministic `geometry_status`로 표현 | geometry-only baseline and evidence factor |
| `disagreement_score` | semantic score와 geometry validity의 불일치 | audit ranking and mismatch measurement |
| `coverage` | geometry/view/evidence가 충분한지 | invalid relation과 missing evidence를 분리 |
| `uncertainty` | 판단이 애매하거나 evidence가 부족한 상태 | hard binary target으로 강제하지 않음 |

## Literature Grounding

H002의 구성요소는 임의의 field 묶음이 아니라, scene graph prediction, object detection,
3D spatial perception, calibration, incomplete-label learning에서 반복적으로 쓰인
신뢰도 구성요소를 relation-level reliability 문제에 맞게 재배열한 것이다.

Relevant grounding:

- Visual relationship / scene graph generation은 object pair에 predicate score를 부여한다.
  `Visual Relationship Detection with Language Priors`, `Neural Motifs`는 relation score가
  object-pair semantic context와 language prior에 강하게 의존할 수 있음을 보여준다.
- 3DSSG 계열의 `VL-SAT`와 open-vocabulary `Open3DSG`는 relation source score가
  semantic plausibility와 visual-language prior를 포함할 수 있음을 보여준다.
- `SceneGraphFusion`, `Hydra`, 3D Scene Graph 계열은 relation이 3D spatial structure와
  함께 다뤄져야 함을 보여준다.
- Calibration과 selective prediction literature는 confidence와 correctness가 다를 수
  있으며, uncertainty와 abstention을 분리해야 함을 뒷받침한다.
- Incomplete annotation / positive-unlabeled learning 관점에서는 no-GT relation이 반드시
  invalid relation을 의미하지 않는다. H002의 `low semantic + high geometry` bucket은 이
  문제와 직접 연결된다.

## Proposed Framework

H002는 다음 순서로 진행한다.

1. RGA row construction:
   semantic rank/score, geometry status, `p_geom_valid`, coverage, label/audit state를
   row 단위로 기록한다.

2. Mismatch diagnosis:
   `RGA-HL`, `RGA-LH`, uncertain, missing/unsupported state를 분리한다.

3. Target construction:
   relation reliability target을 만들되, predicate/rank/object/endpoint shortcut으로 쉽게
   맞춰지면 posterior로 넘어가지 않는다.

4. Factorized posterior smoke:
   target-independence가 통과된 뒤에만 `semantic_only`, `geometry_only`,
   `semantic_plus_geometry`, `factorized_reliability_posterior`를 비교한다.

5. Controls:
   wrong-pair geometry, shuffled geometry, rank-band control, endpoint/object control,
   same-family control을 사용한다.

## Evaluation Target Policy

H002의 최종 검증은 기존 데이터셋 GT-only relation match로만 정의하지 않는다. 기존 GT는
중요하지만, H002의 핵심 claim은 relation edge가 evidence상 신뢰 가능한지를 보는 것이므로
primary target은 human-audited reliability label이어야 한다.

Target policy:

```text
primary target = human-audited reliability label
  accept_reliable / reject_unreliable / abstain_uncertain

auxiliary axis = existing GT relation match
  exact_match / family_match / pair_has_other_predicate / no_gt_for_pair

required analysis = mismatch table
  GT match & reliability accept
  GT match & reliability reject
  No GT & reliability accept
  No GT & reliability reject
  Abstain
```

이 정책의 이유는 다음과 같다.

- 기존 GT match만 쓰면 H002가 기존 relation prediction metric으로 축소된다.
- `no_gt_for_pair`가 반드시 unreliable relation을 뜻하지 않는다.
- `GT match & reliability reject`는 GT relation도 visual/geometry evidence와 충돌할 수 있음을
  보여주는 중요한 failure case다.
- `No GT & reliability accept`는 annotation sparsity 또는 under-annotated reliable relation을
  드러내는 case다.

따라서 H002는 human reliability label을 main target으로 두고, existing GT relation match는
reviewer-facing 연결고리와 mismatch 분석 축으로 유지한다.

## Stage Progression Summary

H002는 결과를 억지로 끼워맞춘 흐름이 아니라, posterior가 풀어야 할 target이 정말
relation reliability를 요구하는지 단계적으로 검증한 흐름이다. 각 stage의 상세 기록은
`stages/` 아래의 stage별 문서가 소유한다.

| Stage | Stage File | What Was Tested | Main Problem | Why Next |
| --- | --- | --- | --- | --- |
| v1 | `stages/v1_rga_pilot.md` | RGA axis와 초기 factorized posterior pilot | rank/family/predicate shortcut으로 posterior gain 설명 가능 | full-train과 independent target 필요 |
| v2 | `stages/v2_full_train_support_vertical.md` | full-train `support_contact`/`relative_vertical` pipeline | prior label carryover와 endpoint/object shortcut | target construction을 더 강하게 통제 |
| v3 | `stages/v3_positive_anchor_endpoint.md` | positive-anchor와 object/endpoint-controlled target | positive sparse, object label/endpoint shortcut | reliable/unreliable matched contrast 필요 |
| v4 | `stages/v4_matched_contrast.md` | matched contrast target | binary target size 작음, hidden metadata risk | 더 넓은 cell contrast 탐색 |
| v5 | `stages/v5_cell_contrast.md` | object/geometry cell contrast | direct reliable/unreliable contrast 부족 | uncertainty를 별도 target state로 유지 |
| v6 | `stages/v6_uncertainty_shortcut.md` | `accept/reject/abstain` schema와 shortcut-controlled queue | object/category cell shortcut 지배 | object-cell evidence contrast로 이동 |
| v7 | `stages/v7_object_cell_contrast.md` | object-cell evidence contrast | strict-group/object-pair shortcut 제거 실패 | exact endpoint-pair counterfactual 필요 |
| v8 | `stages/v8_endpoint_pair_counterfactual.md` | same endpoint-pair predicate counterfactual | `predicate_label`, `rank_band_hidden`, `machine_hint_hidden` shortcut 잔존 | predicate/rank/hint 직접 통제 필요 |
| v9 | `stages/v9_predicate_rank_hint.md` | predicate/rank/hint controlled exact-pair feasibility | exact pair 내부 rank와 predicate가 구조적으로 얽힘 | path decision 필요 |
| v10 | `stages/v10_proximity_path_decision.md` | v9 이후 target route 결정 | support/vertical exact-pair는 diagnostic-only로 고정해야 함 | `close by` proximity feasibility scan으로 relation-family 확장 |
| v11 | `stages/v11_proximity_feasibility.md` | `close by` / proximity train-only feasibility | current RGA queue에서는 `RGA-HL = 0`, `RGA-LH = 171324`로 bidirectional target 아님 | LH-only proximity path decision 필요 |
| v12 | `stages/v12_proximity_lh_path_decision.md` | proximity LH-only branch 채택 여부 | RGA 자체를 LH-only로 줄이면 핵심 claim이 약해짐 | RGA는 bidirectional 유지, 다음 empirical branch는 LH-only label readiness |
| v13 | `stages/v13_proximity_lh_label_readiness.md` | proximity LH-only label-ready sheet 준비 | label-ready는 target-valid와 다름; rank diversity가 약함 | label fill 후 target-independence audit 필요 |
| v14 | `stages/v14_proximity_lh_label_fill.md` | visible-only proxy label fill | text-only proxy label이라 hidden shortcut 독립성 미검증 | label ingestion 후 shortcut audit 필요 |
| v15 | `stages/v15_proximity_lh_label_ingestion.md` | filled labels와 hidden audit manifest join | object-pair shortcut이 target을 강하게 설명 | target-independence audit에서 controlled slice 여부 판단 |
| v16 | `stages/v16_proximity_lh_target_independence.md` | proxy target independence audit | strict/diagnostic slice 0개, object-pair mixed contrast 0개 | path decision after audit 필요 |
| v17 | `stages/v17_proximity_lh_path_after_audit.md` | blocked audit 이후 경로 결정 | visible-only label path는 posterior target으로 부적합 | scene/geometry-aware target repair plan |
| v18 | `stages/v18_proximity_scene_geometry_repair_plan.md` | scene/geometry-aware repair plan과 capacity 확인 | target은 아직 미채움; candidate mining 필요 | scene/geometry-aware candidate mining |
| v19 | `stages/v19_proximity_scene_geometry_candidate_mining.md` | scene/geometry-aware 240-row candidate sheet 생성 | 아직 label fill/ingestion 전이라 posterior evidence 아님 | scene/geometry-aware label fill |
| v20 | `stages/v20_proximity_scene_geometry_label_fill.md` | reviewer-visible scene/geometry evidence만으로 proxy label fill | binary usable은 176개지만 positive가 39개라 class-mass risk 존재 | label ingestion 후 shortcut/positive-mass audit |
| v21 | `stages/v21_proximity_scene_geometry_label_ingestion.md` | locked labels와 hidden audit manifest join, target material 생성 | same-pair mixed contrast는 생겼지만 positive sparse와 shortcut risk 잔존 | target-independence audit |
| v22 | `stages/v22_proximity_scene_geometry_target_independence.md` | reliability/geometry-support/usefulness target independence audit | reliability는 positive-sparse, 모든 target에서 strict clear slice 0개 | path decision after audit |
| v23 | `stages/v23_proximity_scene_geometry_path_decision.md` | proximity branch 이후 경로 결정 | proximity는 primary posterior target으로 부적합 | physical relation-family feasibility scan |
| v24 | `stages/v24_physical_relation_family_feasibility.md` | `support_contact`/`attachment_deferred`/`relative_vertical` train-only capacity scan | row mass는 충분하지만 HL/LH imbalance, one-predicate capacity concentration, attachment unsupported가 남음 | `support_contact` sampling plan |
| v25 | `stages/v25_physical_relation_family_sampling_plan.md` | 240-row quota/cap/label-surface sampling plan | 아직 실제 rows는 선택하지 않음; queue bucket은 target label이 아님 | physical relation-family candidate mining |
| v26 | `stages/v26_physical_relation_family_candidate_mining.md` | v25 quota를 실제 240-row label-ready sheet로 materialize | `standing on` HL은 hard endpoint shortcut 때문에 제외하고 `lying on` HL로 fallback | visible-only label fill |
| v27 | `stages/v27_physical_relation_family_label_fill.md` | v14 physical sheet에 visible-only proxy labels를 채움 | positive count가 48로 이전 50-class-mass gate보다 2개 부족 | label ingestion and target-independence audit |
| v28 | `stages/v28_physical_relation_family_label_ingestion.md` | filled labels와 hidden audit manifest join, target material 생성 | class mass fail과 quick-probe risk 64개가 남음 | target-independence audit |
| v29 | `stages/v29_physical_relation_family_target_independence.md` | v14 target-independence audit | `48/152` positive-sparse, strict/diagnostic clear slice 0개, shortcut risk 잔존 | path decision after audit |
| v30 | `stages/v30_physical_relation_family_path_decision.md` | v14 이후 path decision | 단순 positive 추가나 balanced full slice 사용은 shortcut 문제를 해결하지 못함 | v15 witness-matched physical relation-family repair plan |
| v31 | `stages/v31_physical_relation_family_repair_plan.md` | v15 witness-matched repair contract 고정 | 아직 후보 capacity는 검증하지 않음; posterior는 계속 금지 | v15 capacity scan |
| v32 | `stages/v32_physical_relation_family_capacity_scan.md` | v15 repair contract의 train-only capacity scan | row/cap capacity는 충분하지만 mixed witness stratum이 0개 | path decision after capacity scan |
| v33 | `stages/v33_physical_relation_family_path_decision.md` | v15 capacity 이후 path decision | same-witness HL/LH matching이 H002 mismatch 정의와 충돌 | v16 controlled cross-stratum support/contact contrast plan |
| v34 | `stages/v34_cross_stratum_contrast_plan.md` | v16 cross-stratum quota/block/label-surface/audit plan | 아직 실제 block capacity는 검증하지 않음 | v16 capacity scan |
| v35 | `stages/v35_cross_stratum_capacity_scan.md` | v16 cross-stratum train-only capacity/control scan | raw quota는 충분하지만 HL/LH가 `geometry_status`와 사실상 일치하고 mixed block이 4개뿐임 | path decision after capacity scan |
| v36 | `stages/v36_cross_stratum_path_decision.md` | v16 capacity failure 이후 route 결정 | cap 완화나 추가 mining은 construction shortcut을 허용함 | v17 attachment-deferred witness schema probe plan |
| v37 | `stages/v37_attachment_witness_schema_plan.md` | `attached to`/`hanging on`/`connected to` typed witness schema와 capacity-scan contract | schema 전 attachment는 556,038 rows가 모두 unsupported/checkable 0 | attachment witness schema capacity scan |
| v38 | `stages/v38_attachment_witness_capacity_scan.md` | attachment rows에 pair-level raw geometry를 join하고 typed witness capacity scan | capacity는 통과했지만 아직 label target 독립성은 검증 전 | path decision after capacity scan |
| v39 | `stages/v39_attachment_path_decision.md` | capacity 통과 이후 attachment route 경로 결정 | `connected to`는 OBB만으로 functional connection을 확정하기 어려움 | v18 attachment candidate mining |
| v40 | `stages/v40_attachment_candidate_mining.md` | v18 hidden-field-safe attachment candidate packet 생성 | 아직 label fill/ingestion 전이라 posterior target 아님 | visible-only label fill |
| v41 | `stages/v41_attachment_label_fill.md` | v18 visible-only proxy label fill | primary positive가 33개라 posterior smoke 불가 | label ingestion |
| v42 | `stages/v42_attachment_label_ingestion.md` | filled labels와 hidden audit manifest join, target artifacts 생성 | positive-sparse와 quick-probe risk 102개가 남음 | target-independence audit |
| v43 | `stages/v43_attachment_target_independence.md` | v18 attachment target-independence audit | primary binary `33/81`, strict/diagnostic clear slice 0개, shortcut risk 잔존 | path decision after audit |
| v44 | `stages/v44_attachment_path_decision.md` | v18 audit 이후 path decision | v18은 target-independent posterior target이 아님 | v19 independent-evidence repair plan |
| v45 | `stages/v45_attachment_independent_evidence_repair_plan.md` | independent evidence contract, label schema, source inventory contract | 실제 row별 visual/mesh source coverage는 아직 unknown | source inventory |
| v46 | `stages/v46_attachment_source_inventory.md` | row별 multi-view/sequence/mesh/source availability inventory | strong same-frame co-visible evidence는 43/240으로 제한적 | audit packet plan |
| v47 | `stages/v47_attachment_audit_packet_plan.md` | tiered visible schema and hidden asset manifest plan | 아직 실제 packet files는 materialize 전 | audit packet materialization |
| v48 | `stages/v48_attachment_audit_packet_materialization.md` | neutral packet-local image copies and visible review sheet | leakage review는 아직 별도 gate 전 | leakage review |
| v49 | `stages/v49_attachment_audit_packet_leakage_review.md` | formal visible-sheet/markdown/image-name leakage review | 아직 label fill 전 | packet label fill |
| v50 | `stages/v50_attachment_audit_packet_label_fill.md` | leakage-reviewed packet label fill | primary binary가 `26/99`로 positive-sparse risk 유지 | label ingestion |
| v51 | `stages/v51_attachment_audit_packet_label_ingestion.md` | filled labels와 hidden packet manifest를 사후 join해 target artifacts 생성 | class mass fail과 quick-probe risk 43개 | target-independence audit |
| v52 | `stages/v52_attachment_audit_packet_target_independence.md` | v19 target class mass and shortcut-independence audit | primary binary `26/99`, strict/diagnostic clear slice 0개 | path decision after audit |
| v53 | `stages/v53_attachment_audit_packet_path_decision.md` | v19 audit-packet target 이후 path decision | v19은 positive-sparse와 shortcut risk 때문에 posterior target이 아님 | v20 endpoint-balanced counterfactual repair plan |
| v54 | `stages/v54_attachment_endpoint_balanced_repair_plan.md` | v20 endpoint-balanced counterfactual repair contract 고정 | 아직 capacity scan 전이라 mining/label/posterior evidence 아님 | v20 capacity scan |
| v55 | `stages/v55_attachment_endpoint_balanced_capacity_scan.md` | full train attachment pool에서 exact endpoint/family/scan-balanced contrast capacity scan | capacity는 통과했지만 아직 candidate sheet/label/posterior evidence 아님 | v20 candidate mining |
| v56 | `stages/v56_attachment_endpoint_balanced_candidate_mining.md` | v55 preview를 320-row hidden-field-safe candidate sheet로 materialize | 아직 source inventory/label/posterior evidence 아님 | v20 source inventory |
| v57 | `stages/v57_attachment_endpoint_balanced_source_inventory.md` | v20 selected rows source inventory | source inventory는 통과했지만 audit packet/label/posterior evidence 아님 | v20 audit packet plan |
| v58 | `stages/v58_attachment_endpoint_balanced_audit_packet_plan.md` | v20 tiered visible packet schema and hidden asset manifest plan | packet materialization/label/posterior evidence 아님 | v20 audit packet materialization |
| v59 | `stages/v59_attachment_endpoint_balanced_audit_packet_materialization.md` | v20 tiered audit packet materialization with neutral visible assets and hidden GT-match axis | leakage review/label/posterior evidence 아님 | v20 leakage review |
| v60 | `stages/v60_attachment_endpoint_balanced_audit_packet_leakage_review.md` | v20 visible sheet/markdown/image-name formal leakage review | label/posterior evidence 아님 | v20 packet label fill |
| v61 | `stages/v61_attachment_endpoint_balanced_audit_packet_label_fill.md` | v20 leakage-reviewed packet label fill | primary labels are positive-sparse (`25/182/49`), connected rows remain diagnostic-only | v20 label ingestion |
| v62 | `stages/v62_attachment_endpoint_balanced_audit_packet_label_ingestion.md` | user-filled labels와 hidden manifest/GT axis 사후 join | primary binary `25/182`, quick-probe risk 70개 | target-independence audit |
| v63 | `stages/v63_attachment_endpoint_balanced_audit_packet_target_independence.md` | v20 primary/auxiliary targets의 class mass와 shortcut-controlled slice audit | primary binary `25/182`, strict/diagnostic clear slice `0/0`, risk flag 82개 | path decision after audit |
| v64 | `stages/v64_attachment_endpoint_balanced_audit_packet_path_decision.md` | v20 audit 이후 route 결정 | current 320-row target은 posterior 부적합, 단 sampling artifact 가능성은 남음 | v21 conditional contrast capacity scan |
| v65 | `stages/v65_attachment_conditional_contrast_capacity_scan.md` | full-train attachment pool에서 conditional contrast capacity 확인 | strict condition은 `hanging on`에만 mixed stratum이 남고 `attached to`는 빠짐 | path decision after capacity scan |
| v66 | `stages/v66_attachment_conditional_contrast_path_decision.md` | v21 capacity 이후 route 결정 | two-predicate strict primary는 불가, relaxed two-predicate는 shortcut risk | v22 hanging-on strict packet plan |
| v67 | `stages/v67_hanging_on_strict_packet_plan.md` | `hanging on` strict packet plan과 hidden-only dry-run preview | 아직 visible packet/candidate sheet/label/posterior evidence 아님 | v22 hanging-on strict candidate mining |
| v68 | `stages/v68_hanging_on_strict_candidate_mining.md` | `hanging on` strict 240-row visible candidate sheet와 hidden manifest 생성 | 아직 source inventory/packet assets/label/posterior evidence 아님 | v22 source inventory |

현재 v9 결과는 다음과 같다.

```text
eligible_pairs = 9984
eligible_rows = 19968
strict_v9_exact_pair_feasible = false
rank_band -> predicate majority accuracy = 0.9229
baseline = 0.4976
```

이 결과는 row count 부족이 아니라 target-independence failure다.

v10 path decision 결과는 다음과 같다.

```text
selected_path = v10_proximity_relation_family_feasibility_scan
next_todo = reliability_target_v10_proximity_relation_family_feasibility_scan
posterior_smoke_allowed = false
```

이 결정은 relation type을 무작정 넓히는 것이 아니라, v9에서 드러난
`rank_band -> predicate` entanglement를 피할 수 있는 새로운 target construction route를
찾기 위한 것이다.

v11 proximity feasibility 결과는 다음과 같다.

```text
status = h002_reliability_target_v10_proximity_feasibility_lh_only_ready_not_bidirectional
total_proximity_rows = 185346
queue_proximity_rows = 171324
RGA-HL proximity rows = 0
RGA-LH proximity rows = 171324
strict_lh_pool_rows = 50966
preview_rows = 240
validation_errors = 0
```

이 결과는 `close by`가 H002 generality 확장에는 중요하지만, 현재 artifact 기준으로는
양방향 mismatch benchmark가 아니라 `low semantic + high geometry`를 세분화하는
LH-only branch라는 뜻이다. 즉, proximity의 다음 질문은 "semantic overconfidence까지 함께
풀 수 있는가"가 아니라 "geometry-supported low-rank proximity가 true underconfidence인지,
dense proximity noise인지, annotation sparsity인지 구분할 수 있는가"이다.

v12 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v10_proximity_lh_path_decision_select_lh_only_label_readiness
selected_path = v12_proximity_lh_only_label_readiness
next_todo = reliability_target_v12_proximity_lh_only_label_readiness
```

중요한 claim boundary:

```text
RGA framework = bidirectional HL/LH mismatch
current empirical branch = proximity LH-only
```

따라서 H002 방향은 바뀐 것이 아니다. RGA의 원래 정의는 유지하고, 현재 데이터가 실제로
제공하는 failure mode인 `low semantic + high geometry`를 먼저 검증한다.

v13 label readiness 결과는 다음과 같다.

```text
status = h002_reliability_target_v12_proximity_lh_only_label_readiness_ready
rows = 240
visible_leakage_hits = 0
validation_errors = 0
label_match_status_hidden = exact_match:80, pair_has_other_predicate:80, no_gt_for_pair:80
rank_band_hidden = rank_101_200:2, rank_201_500:238
next_todo = reliability_target_v12_proximity_lh_only_label_fill
```

이 결과는 label sheet가 준비됐다는 뜻이지 target-independence가 확보됐다는 뜻은 아니다.
특히 rank band가 거의 `rank_201_500`에 몰려 있으므로 label ingestion 이후 rank leakage와
object/scan shortcut audit이 반드시 필요하다.

v14 label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v12_proximity_lh_only_label_filled_codex_proxy_visible_only
accept_reliable_close_by = 36
reject_unreliable_close_by = 71
abstain_uncertain = 133
binary_usable_rows = 107
hidden_audit_manifest_read = false
validation_errors = 0
next_todo = reliability_target_v12_proximity_lh_only_label_ingestion
```

이 label은 visible object-pair text만 사용한 conservative proxy다. 따라서 이것은
posterior evidence가 아니라 ingestion 및 target-independence audit으로 넘어가기 위한
hypothesis-stage target material이다.

v15 label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v12_proximity_lh_only_label_ingested_with_probe_risk
multiclass_rows = 240
binary_rows = 107
abstain_rows = 133
quick_probe_risk_flags = 10
validation_errors = 0
next_todo = reliability_target_v12_proximity_lh_only_target_independence_audit
```

Quick probe에서 강한 shortcut이 확인됐다.

```text
subject_object_label_pair_hidden -> binary accuracy = 1.0000
subject_object_visible_pair -> binary accuracy = 1.0000
scan_id -> binary accuracy = 0.9720
```

따라서 현재 target은 ingested 상태지만 posterior-ready가 아니다. 이 결과는 H002 가설이
틀렸다는 뜻이 아니라, visible-only proxy label이 object-pair semantics에 의해 거의 결정된다는
진단이다.

v16 target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v12_proximity_lh_only_independence_blocked_object_pair_shortcut
binary_rows = 107
strict_slices = 0
diagnostic_slices = 0
subject_object_visible_pair_binary_mixed_groups = 0
subject_object_label_pair_hidden_binary_mixed_groups = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v12_proximity_lh_only_path_decision_after_audit
```

핵심 blocker:

```text
subject_object_label_pair_hidden -> binary accuracy = 1.0000
subject_object_visible_pair -> binary accuracy = 1.0000
scan_id -> binary accuracy = 0.9720
```

즉, current proximity LH-only proxy target은 object-pair identity로 풀린다. 이는 H002의
semantic/geometry/reliability factorization claim에 대한 반증이 아니라, visible-only proxy label
construction이 posterior validation target으로 부적합하다는 증거다.

v17 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v12_proximity_lh_path_decision_select_scene_geometry_repair
visible_only_branch = diagnostic_only_negative_evidence
selected_path = v13_proximity_lh_scene_geometry_repair_plan
next_todo = reliability_target_v13_proximity_lh_scene_geometry_repair_plan
posterior_smoke_allowed = false
```

즉, 실패한 것은 H002 방향이 아니라 다음 경로다.

```text
visible object-pair text -> proxy label -> posterior target
```

다음 target repair는 같은 object-pair 내부에서도 reliable / unreliable `close by`가 갈릴 수
있도록 scene/geometry-aware evidence를 사용해야 한다. 이 evidence는 label/audit evidence로만
사용하고, `machine_hint`, `label_match_status`, source rank, target construction bucket은 여전히
label shortcut으로 금지한다.

v18 repair plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_ready
repair_pool_rows = 50966
visible_pair_groups = 5122
v13_block_candidate_groups = 1510
strong_v13_block_candidate_groups = 778
candidate_capacity_cap8 = 11520
next_todo = reliability_target_v13_proximity_lh_scene_geometry_candidate_mining
posterior_smoke_allowed = false
```

이 결과는 proximity branch가 수량 부족으로 막힌 것이 아니라는 뜻이다. 다음 문제는
같은 visible object-pair 내부에서도 scene context에 따라 `close by` reliability가 달라질 수
있도록 local layout, binned geometry witness, nearest-neighbor/density context, duplicate-object
context를 visible evidence로 포함하는 candidate sheet를 만드는 것이다.

v19 candidate mining 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_ready_for_label_fill
selected_rows = 240
selected_blocks = 30
rows_per_block = 8
unique_scans = 182
unique_subgraphs = 196
raw_feature_joined_rows = 240
visible_leakage_hits = 0
validation_errors = 0
next_todo = reliability_target_v13_proximity_lh_scene_geometry_label_fill
```

v19의 핵심은 v12와 달리 labeler가 object-pair text만 보고 판단하지 않도록 visible
evidence surface를 확장한 것이다. `semantic_rank`, `semantic_score_norm`, `p_geom_valid`,
`rank_band`, `label_match_status`, `machine_hint`, `target_construction_block`, raw geometry
features는 hidden audit manifest에만 둔다.

v20 label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_label_filled_codex_proxy_visible_only
rows = 240
accept_reliable_close_by = 39
reject_dense_relation_noise = 82
reject_trivial_or_context_only = 55
abstain_uncertain = 64
positive_rows = 39
negative_rows = 137
binary_usable_rows = 176
hidden_audit_manifest_read = false
validation_errors = 0
next_todo = reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

이 결과는 v14 visible-only proxy보다 binary usable row가 늘었다는 점에서는 개선이다.
하지만 positive row가 `39`개로 이전 post-label gate의 minimum-per-class `50` 기준에 못
미친다. 따라서 v20은 posterior-ready target이 아니라 label ingestion과 target-independence
audit으로 넘어가기 위한 target material이다. positive를 억지로 늘리기 위해 label 기준을
완화하지 않은 것은 의도된 보수적 선택이다.

v21 label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_positive_sparse_with_probe_risk
rows = 240
multiclass_rows = 240
binary_rows = 176
abstain_rows = 64
geometry_support_rows = 176
usefulness_rows = 176
reliability_positive_rows = 39
reliability_negative_rows = 137
geometry_support_positive_rows = 121
geometry_support_negative_rows = 55
same_block_mixed_reliability_binary_groups = 22
same_visible_pair_mixed_reliability_binary_groups = 22
quick_probe_risk_flags = 32
validation_errors = 0
next_todo = reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit
```

v21에서 v12 대비 좋아진 점은 same block / same visible object-pair 내부 mixed
accept/reject contrast가 `22`개 생겼다는 것이다. 즉 object-pair identity만으로 전부 결정되는
v12 proxy path보다는 나아졌다. 그러나 reliability positive가 `39`개로 sparse하고,
`p_geom_bin_hidden`, `scan_id`, `geometry_witness_summary_v13`, `nearest_neighbor_context_v13`
등에서 quick-probe shortcut risk가 남아 있다. 따라서 이 target은 아직 posterior-ready가
아니며, 다음 단계는 target-independence audit이다.

v22 target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
relation_binary_rows = 176
relation_binary_counts = 0:137, 1:39
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
geometry_support_counts = 1:121, 0:55
geometry_support_class_mass_pass = true
geometry_support_strict_clear_slices = 0
usefulness_counts = 0:137, 1:39
full_quick_probe_risk_flags = 41
slice_blocking_risk_flags = 517
validation_errors = 0
next_todo = reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit
```

결론은 v13 proximity scene-geometry branch가 v12보다 contrast는 나아졌지만 posterior-ready는
아니라는 것이다. Primary relation reliability target은 positive `39`개로 posterior gate
`50`개를 넘지 못하고, diagnostic slice에서도 residual shortcut risk가 남는다. Geometry-support
target은 class mass는 있지만 auxiliary target이며 strict independent slice가 없어 reliability
target을 대체할 수 없다.

v23 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_select_physical_relation_feasibility
selected_path = freeze_v13_proximity_diagnostic_select_v14_physical_relation_family_feasibility
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_feasibility_scan
```

결정은 proximity를 버리는 것이 아니다. `close by`는 다음 역할로 고정한다.

```text
diagnostic_only_generality_and_limitation_evidence
```

즉, proximity는 dense relation noise와 LH-only branch의 한계를 보여주는 evidence로 남긴다.
하지만 primary posterior target으로는 사용하지 않는다. 더 많은 `close by` positive를 지금
채굴하면 conservative label policy를 무너뜨리거나 `p_geom_bin` / geometry-witness text shortcut을
강화할 가능성이 크다. 따라서 다음 primary target repair route는 physical relation family
feasibility로 이동한다.

v14 physical relation-family feasibility의 후보는 다음이다.

```text
support_contact: standing on, lying on
attachment_deferred: attached to, hanging on, connected to
relative_vertical: higher than, lower than
```

역할 구분:

- `support_contact`: first feasibility anchor. 다만 old exact-pair rank/predicate construction은 반복하지 않는다.
- `attachment_deferred`: novelty-oriented feasibility candidate. witness schema와 audit evidence가 필요하다.
- `relative_vertical`: control family. geometry-easy relation이라 primary novelty target보다는 control에 가깝다.

v24 feasibility scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred
selected_route = support_contact_primary_anchor_with_relative_vertical_control_attachment_schema_probe
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_sampling_plan
```

Family-level 결과:

```text
support_contact:
  match_rows = 556038
  checkable_rows = 556038
  HL/LH rows = 1069 / 160429
  same_predicate_HL_LH_capacity = 2138
  verdict = primary sampling anchor

attachment_deferred:
  match_rows = 556038
  checkable_rows = 0
  unsupported_share = 1.0
  verdict = defer until witness schema

relative_vertical:
  match_rows = 370692
  checkable_rows = 370692
  HL/LH rows = 759 / 123845
  same_predicate_HL_LH_capacity = 1518
  verdict = control family
```

이 결과는 수량 부족이 아니라 target construction 문제가 계속 핵심 blocker임을 보여준다.
`support_contact`는 다음 anchor로 충분하지만, HL/LH queue imbalance와 `lying on` 중심
capacity concentration이 있으므로 queue bucket을 reliability label로 쓰면 안 된다.
`relative_vertical`은 geometry-easy control로 유용하지만 novelty target은 아니다.
`attachment_deferred`는 중요한 future extension이지만 현재 geometry policy에서는
`unsupported_family`라 relation-specific witness schema가 먼저 필요하다.

v25 sampling plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_sampling_plan_ready_for_candidate_mining
selected_route = support_contact_primary_anchor_relative_vertical_control
target_queue_rows = 240
primary_anchor_rows = 160
control_rows = 80
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_candidate_mining
```

Quota:

```text
support_contact / lying on / HL = 68
support_contact / lying on / LH = 68
support_contact / standing on / HL = 12
support_contact / standing on / LH = 12
relative_vertical / lower than / HL = 40
relative_vertical / lower than / LH = 40
```

현재 primary target에서 제외한 cell:

```text
support_contact / supported by: LH-only and outside the narrow current core
relative_vertical / higher than: HL capacity is one row
attachment_deferred: geometry unsupported until witness schema exists
```

따라서 다음 단계는 이 quota와 cap policy에 맞춰 실제 240-row candidate sheet를 만드는
candidate mining이다. 이때도 HL/LH bucket은 sampling axis일 뿐 reliability label이 아니다.

v26 candidate mining 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_candidate_mining_ready_for_label_fill
selected_rows = 240
support_contact_rows = 160
relative_vertical_rows = 80
unique_scans = 202
unique_subgraphs = 222
unique_directed_pairs = 240
raw_feature_joined_rows = 240
visible_leakage_hits = 0
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_label_fill
```

Effective quota:

```text
S1_support_lie_hl = 80
S2_support_lie_lh = 68
S3_support_stand_hl = 0
S4_support_stand_lh = 12
V1_vertical_lower_hl = 40
V2_vertical_lower_lh = 40
```

`standing on` HL은 raw 17개가 있었지만 모두 `floor` 또는 `wall` 같은 hard room-surface
subject를 포함했다. 이것을 유지하면 support-contact target이 hard-room-surface shortcut으로
무너질 수 있으므로 12개 quota를 `lying on` HL로 옮겼다. 결과적으로 current primary sheet는
hard endpoint row와 floor-as-object row를 모두 0으로 유지한다.

v27 label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_label_filled_codex_proxy_visible_only
rows = 240
relation_reliability_state_v14 = accept_reliable:48, reject_unreliable:152, abstain_uncertain:40
geometry_support_state_v14 = supports:48, contradicts:152, ambiguous:40
binary_usable_rows = 200
hidden_audit_manifest_read = false
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_label_ingestion
```

Family-level breakdown:

```text
support/contact relation = accept:16, reject:114, abstain:30
relative vertical relation = accept:32, reject:38, abstain:10
```

이 결과는 v13 proximity보다 binary usable row가 많지만, positive count가 `48`개로 이전
minimum-per-class gate `50`보다 2개 부족하다. 따라서 v27은 posterior evidence가 아니라
label ingestion과 target-independence audit으로 넘길 수 있는 target material이다. Hidden
audit manifest는 읽지 않았고, validation/test도 사용하지 않았다.

v28 label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_label_ingested_positive_sparse_with_probe_risk
rows = 240
multiclass_rows = 240
binary_rows = 200
geometry_support_rows = 200
usefulness_rows = 200
endpoint_rows = 240
coverage_rows = 240
abstain_rows = 40
binary_target = 1:48, 0:152
geometry_support_target = 1:48, 0:152
usefulness_target = 1:48, 0:152
quick_probe_risk_flags = 64
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_target_independence_audit
```

Target viability:

```text
minimum_per_class_for_posterior = 50
reliability_positive_rows = 48
reliability_negative_rows = 152
class_mass_pass = false
same_quota_cell_mixed_reliability_binary_groups = 3
same_visible_pair_mixed_reliability_binary_groups = 11
same_predicate_mixed_reliability_binary_groups = 3
```

v28은 v12처럼 object-pair identity만으로 완전히 결정되는 target은 아니다. 하지만 positive가
`48`개라 class-mass gate를 통과하지 못하고, quick probe에서 visible witness text와 quota/geometry
metadata가 label을 강하게 설명한다. 따라서 posterior smoke는 여전히 금지되며 다음 단계는
target-independence audit이다.

v29 target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
rows = 240
relation_binary_rows = 200
relation_binary_counts = 0:152, 1:48
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
full_quick_probe_risk_flags = 65
slice_audit_rows = 174
slice_risk_rows = 3828
slice_blocking_risk_flags = 1171
posterior_allowed = false
validation_errors = 0
next_todo = reliability_target_v14_physical_relation_family_path_decision_after_audit
```

Target decision:

```text
relation_binary = blocked_positive_sparse
geometry_support_binary = auxiliary_or_diagnostic_positive_sparse
usefulness_binary = auxiliary_or_diagnostic_positive_sparse
relation_multiclass = auxiliary_or_diagnostic_positive_sparse
endpoint_multiclass = auxiliary_or_diagnostic_positive_sparse
coverage_multiclass = single_class_provenance_only
```

중요한 nuance는 balanced full slice가 `96` rows (`48/48`)로 존재한다는 점이다. 그러나 이 slice도
`scan_id`, `subject_label`, `object_label`, visible/hidden object-pair, `quota_cell_id_hidden`,
`machine_hint_hidden`, `rank_band_hidden`, visible witness summary shortcut risk를 제거하지 못한다.
따라서 현재 v14 target은 row 수와 relation family가 개선됐지만, posterior method claim으로 넘어갈
수 있는 독립 target은 아니다.

v30 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v14_physical_relation_family_path_decision_select_v15_repair_plan
selected_path = freeze_v14_diagnostic_select_v15_witness_matched_physical_relation_repair_plan
relation_binary_counts = 0:152, 1:48
relation_class_mass_pass = false
relation_strict_clear_slice_count = 0
relation_diagnostic_clear_slice_count = 0
posterior_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_repair_plan
```

선택한 판단:

```text
v14_role = diagnostic_only_negative_evidence
next_route = v15_physical_relation_family_repair_plan
```

단순히 reliable positive를 2개 더 추가하는 것은 reject했다. 이유는 numeric class-mass gate는
통과시킬 수 있어도 balanced `48/48` full slice 내부에 남아 있는 `scan_id`, object labels,
visible/hidden pair identity, quota cell, rank band, machine hint, direct witness-summary shortcut을
해결하지 못하기 때문이다. v15는 positive mass를 늘리는 동시에 witness/predicate/queue/rank/geometry
strata 안에서 accept/reject가 섞이도록 sampling과 label surface를 고쳐야 한다.

v31 repair plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v15_physical_relation_family_repair_plan_ready_for_capacity_scan
selected_route = support_contact_witness_matched_repair_with_relative_vertical_control
quota_plan_total_rows = 240
support_contact_candidate_target_rows = 224
relative_vertical_control_rows = 16
minimum_binary_positive_after_label_fill = 60
minimum_binary_negative_after_label_fill = 60
minimum_mixed_witness_strata_before_label_fill = 8
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_capacity_scan
```

v31은 label fill이나 posterior smoke가 아니다. v31은 다음 candidate mining이 따라야 할
repair contract를 고정한 단계다. 핵심 변화는 `relative_vertical` control을 80개에서 16개로
줄이고, `support_contact`를 primary target으로 224-row 후보까지 늘리는 것이다. 또한
visible label surface에서 `geometry_status`, `p_geom_valid`, `machine_hint`, direct witness
summary를 금지하고, candidate matching axis를 `predicate_label`, source queue, `rank_band`,
`geometry_status`, `p_geom_bin`, coarse witness bin, reason signature, endpoint generic state로
고정했다. 따라서 다음 단계는 이 조건을 만족하는 support/contact 후보 capacity가 실제 train
queue에 있는지 확인하는 것이다.

v32 capacity scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v15_physical_relation_family_capacity_scan_blocked_capacity_or_mixed_strata
eligible_target_rows = 107303
support_contact_rows_available = 51491
support_contact_rows_after_caps = 224
support_contact_mixed_witness_strata = 0
selection_preview_rows = 240
selection_deficits = {}
selected_queue_kind = LH:240
selected_geometry_status = satisfied:240
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan
```

중요한 점은 candidate row count가 부족하지 않다는 것이다. `lying on`은 hard filter 이후
27,778개, `standing on`은 23,713개, `lower than`은 55,812개가 남았다. Cap을 적용해도
240-row preview를 채울 수 있었다. 그러나 preview는 전부 `LH`와 `satisfied` 쪽에서
나왔고, support/contact mixed witness stratum은 0개였다. 따라서 v15의 "same witness
stratum 안에서 HL/LH를 같이 요구한다"는 gate는 현재 RGA construction과 구조적으로 맞지
않는다. 다음 path decision은 mixed-stratum 조건을 완화할지, cross-stratum contrast로
재정의할지, 또는 `attachment_deferred` witness schema probe로 이동할지 결정해야 한다.

v33 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v15_physical_relation_family_path_decision_select_cross_stratum_support_contact_contrast
selected_path = reject_same_witness_select_v16_cross_stratum_support_contact_contrast
support_contact_rows_available = 51491
support_contact_rows_after_caps = 224
support_contact_mixed_witness_strata = 0
selected_by_queue = LH:240
selected_by_geometry_status = satisfied:240
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_plan
```

선택한 판단은 다음이다.

```text
same_witness_hl_lh_matching = reject
support_contact_family = keep
next_route = controlled_cross_stratum_support_contact_contrast
attachment_deferred = deferred_backup_schema_probe
```

이 결정의 핵심은 H002의 원래 문제 정의와 맞추는 것이다. H002는 `high semantic + low
geometry`와 `low semantic + high geometry`가 relation reliability를 어떻게 다르게 설명하는지
보려는 branch다. 따라서 HL과 LH가 같은 geometry witness bucket 안에 있어야 한다는 조건은
문제 정의와 충돌한다. v16은 HL/LH를 서로 다른 disagreement state로 두되, predicate, source
queue, rank band, scan/object distribution, endpoint type, coverage, reason family,
`p_geom_bin`, `geometry_status`를 control/audit axis로 고정한다. 단순히 조건을 완화하는 것이
아니라, same-witness matching을 cross-stratum controlled contrast로 바꾸는 것이다.

v34 cross-stratum plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v16_cross_stratum_support_contact_contrast_plan_ready_for_capacity_scan
quota_plan_total_rows = 240
lying_on_eligible_hl = 896
lying_on_eligible_lh = 26882
standing_on_eligible_hl = 0
standing_on_eligible_lh = 23713
primary_quota = lying_on HL:100, lying_on LH:100
diagnostic_quota = standing_on LH:24, lower_than LH:16
minimum_post_label_binary_rows = 120
minimum_post_label_positive_rows = 50
minimum_post_label_negative_rows = 50
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan
```

v34는 label target을 만든 것이 아니라 capacity scan 전에 지켜야 할 contract를 만든 것이다.
`lying on`은 HL/LH 양쪽 후보가 있으므로 primary balanced contrast로 사용한다. `standing on`은
eligible HL이 0개라 primary target이 아니라 diversity/diagnostic row로만 둔다. Label surface는
`queue_kind`, `rank_band`, `geometry_status`, `p_geom_valid`, `machine_hint`, `label_match_status`,
quota cell, `RGA-HL`, `RGA-LH`를 금지한다. Post-label target-independence audit은 queue-only,
geometry-status-only, p-geom-bin-only, predicate/rank/source, scan/object/pair identity,
reason-family-only, quota-cell-only, block-id-only probe를 포함해야 한다.

v35 capacity scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_blocked_capacity_or_controls
eligible_target_rows = 106712
P1_lie_hl_primary_overconfidence eligible = 896 / target 100
P2_lie_lh_primary_underconfidence eligible = 26882 / target 100
D1_stand_lh_diversity_diagnostic eligible = 23713 / target 24
C1_vertical_lower_control eligible = 55221 / target 16
selected_by_cell = P1:52, P2:98
primary_mixed_blocks_available = 4
selected_primary_blocks_with_both_sides = 2
capacity_pass = false
validation_errors = 0
next_todo = reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan
```

핵심 문제는 row count가 아니라 independence/control이다. `lying on` HL 896개는 모두
`geometry_status = unsatisfied`이고, LH 26,882개는 모두 `geometry_status = satisfied`다.
따라서 지금 label sheet를 만들면 future posterior가 factorized relation reliability가 아니라
`HL -> unsatisfied`, `LH -> satisfied`라는 construction shortcut을 학습할 위험이 크다.
v35는 H002 가설을 반박한 것이 아니라, 현재 v16 target route를 posterior-ready target으로
승격하면 안 된다는 사전 차단 evidence다.

v36 path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v16_cross_stratum_path_decision_select_attachment_deferred_witness_schema_probe
selected_path = freeze_v16_diagnostic_select_v17_attachment_deferred_witness_schema_probe
v16_disposition = v16_cross_stratum_support_contact_contrast_frozen_as_diagnostic_only
next_route = attachment_deferred_witness_schema_probe
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v17_attachment_deferred_witness_schema_probe_plan
```

선택 이유는 v16의 failed caps가 단순히 보수적인 조건이 아니라 target independence를 지키기 위한
필수 경고였기 때문이다. `geometry_status`와 `reason_family` cap을 완화하면 label sheet는 만들 수
있겠지만, 그 target은 relation reliability가 아니라 `HL/unsatisfied` 대 `LH/satisfied`라는
construction artifact가 된다. 따라서 v16은 diagnostic-only로 고정하고, 단일 support gap으로 쉽게
환원되지 않는 `attached to`, `hanging on`, `connected to`에 대해 먼저 typed witness schema를
정의하는 route로 이동한다. Multi-view는 이 route에서도 처음에는 deployable input이 아니라
audit/confirmation evidence로만 둔다.

v37 attachment witness schema plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_probe_plan_ready_for_capacity_scan
attachment_rows = 556038
attached_to_rows = 185346
hanging_on_rows = 185346
connected_to_rows = 185346
checkable_rows_before_schema = 0
unsupported_share_before_schema = 1.0
minimum_raw_feature_join_coverage = 0.95
preview_total_rows = 240
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v17_attachment_deferred_witness_schema_capacity_scan
```

v17은 attachment를 곧바로 label target으로 쓰지 않는다. 현재 RGA에서 attachment row는 모두
`unsupported_family`이므로, 먼저 같은 `directed_pair_id`를 가진 support/vertical row의
pair-level raw geometry를 join해서 `near_contact_distance`, `projected_overlap`,
`relative_vertical_anchor`, `floor_support_confound`, `anchor_affordance_bucket`, `coverage`,
`uncertainty` witness가 capacity를 갖는지 확인해야 한다. `connected to`는 OBB geometry만으로
functional connection을 확정하기 어렵기 때문에 capacity scan에서도 diagnostic role로 둔다.

v38 attachment witness capacity scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_passed_ready_for_path_decision
attachment_rows = 556038
joined_rows = 556038
raw_feature_join_coverage = 1.000000
pair_geometry_join_keys = 185346
capacity_pass = true
validation_errors = 0
next_todo = reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan
```

Cell capacity:

```text
A1 attached supported = 54034
A2 attached contradicted/uncertain = 131312
H1 hanging supported = 25457
H2 hanging contradicted/uncertain = 159889
C1 connected near/overlap diagnostic = 105712
C2 connected contradicted/uncertain diagnostic = 79634
U1 missing/uncertain coverage audit = 381295
```

Capped preview:

```text
selected_preview_rows = 240
selection_deficits = {}
selected_scan_count = 202
selected_subgraph_count = 230
selected_directed_pair_count = 240
selected_visible_pair_count = 199
```

따라서 attachment route는 schema capacity 관점에서 막히지 않았다. 다만 이 결과는 label sheet도
posterior evidence도 아니다. 다음 단계에서는 이 preview를 label-ready candidate mining으로
승격할지, `connected to`를 diagnostic-only로 유지할지, multi-view audit packet을 먼저 요구할지
결정해야 한다.

v39 attachment path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v17_attachment_deferred_witness_schema_path_decision_select_attachment_candidate_mining
selected_path = select_v18_attachment_deferred_candidate_mining_attached_hanging_primary_connected_diagnostic
primary_relation_scope = attached to, hanging on
diagnostic_relation_scope = connected to
candidate_mining_allowed = true
label_sheet_allowed_now = false
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v18_attachment_deferred_candidate_mining
```

이 결정은 capacity-passed preview를 곧바로 label sheet로 승격하지 않는다. v18에서 해야 할 일은
hidden-field-safe candidate packet을 새로 만드는 것이다. `cell_id`, `provisional_status`,
`anchor_bucket`, `rank_band`, `machine_hint`, `geometry_status`, `reason_family`,
`sampling_queue`는 label/model surface에서 숨겨야 한다. `connected to`는 가까움/overlap으로
가능성을 볼 수는 있지만 functional connection은 OBB geometry만으로 확정하기 어렵기 때문에
현재 primary binary target이 아니라 diagnostic/audit row로 둔다. Multi-view는 여전히
deployable model input이 아니라 audit/confirmation evidence다.

v40 attachment candidate mining 결과는 다음과 같다.

```text
status = h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill
selected_rows = 240
primary_binary_candidate_rows = 160
diagnostic_rows = 60
uncertainty_audit_rows = 20
attached_to_rows = 82
hanging_on_rows = 96
connected_to_rows = 62
unique_scans = 202
unique_subgraphs = 230
unique_directed_pairs = 240
visible_leakage_hits = 0
validation_errors = 0
next_todo = reliability_target_v18_attachment_deferred_label_fill
```

v40의 중요한 점은 label-ready sheet와 hidden audit manifest를 분리했다는 것이다. Visible sheet에는
relation text, endpoint labels, 3D layout summary, coverage summary, ambiguity summary만 포함한다.
`cell_id`, `provisional_status`, `anchor_bucket`, `rank_band`, `machine_hint`,
`geometry_status`, `reason_family`, `sampling_queue`, semantic rank/score, raw features는 hidden
manifest로 분리했다. 따라서 이 단계는 target construction progress이지, 아직 reliability label이나
posterior evidence가 아니다.

v41 attachment label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v18_attachment_deferred_label_filled_codex_proxy_visible_only
rows = 240
accept_reliable_attachment = 33
reject_unreliable_attachment = 81
abstain_uncertain = 64
diagnostic_connected_possible = 37
diagnostic_connected_ambiguous = 25
binary_primary_usable_rows = 114
primary_positive_rows = 33
primary_negative_rows = 81
diagnostic_rows = 62
hidden_audit_manifest_read = false
validation_errors = 0
next_todo = reliability_target_v18_attachment_deferred_label_ingestion
```

이 결과는 label material로는 유효하지만 posterior-ready target은 아니다. `attached to` /
`hanging on` primary 후보에서 binary usable row가 114개이고 positive가 33개라, 이전 gate의
`usable_binary_rows >= 120`, `accept_rows >= 50`, `reject_rows >= 50` 기준을 통과하지 못한다.
따라서 다음 단계는 posterior smoke가 아니라 filled labels를 hidden manifest와 join해 target
artifact를 만들고 quick probe 및 target-independence audit 준비를 하는 label ingestion이다.

v42 attachment label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse_with_probe_risk
rows = 240
multiclass_rows = 240
binary_rows = 114
diagnostic_connected_rows = 62
geometry_support_rows = 154
usefulness_rows = 114
endpoint_rows = 240
coverage_rows = 240
abstain_rows = 126
positive_rows = 33
negative_rows = 81
class_mass_pass = false
quick_probe_risk_flags = 102
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v18_attachment_deferred_target_independence_audit
```

v42의 의미는 명확하다. Attachment route는 label artifact까지 만들 수 있었지만, 현재 상태에서
posterior를 돌리면 안 된다. 첫째, primary binary target의 positive가 33개라 class mass gate를
통과하지 못한다. 둘째, quick probe risk flag가 102개라 label이 `cell_id_hidden`,
`candidate_role_hidden`, `predicate_label`, `subject_object_visible_pair`, visible geometry summary
같은 construction/visible grouping field로 쉽게 설명될 가능성이 높다. 따라서 다음 단계는
posterior smoke가 아니라 target-independence audit이다.

v43 attachment target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v18_attachment_deferred_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
rows = 240
relation_binary_rows = 114
relation_binary_counts = {'0': 81, '1': 33}
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
connected_diagnostic_rows = 62
connected_diagnostic_counts = {'diagnostic_connected_possible': 37, 'diagnostic_connected_ambiguous': 25}
geometry_support_rows = 154
geometry_support_counts = {'0': 81, '1': 73}
full_quick_probe_risk_flags = 119
slice_blocking_risk_flags = 3163
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v18_attachment_deferred_path_decision_after_audit
```

v43의 의미도 분명하다. Attachment route는 typed witness schema와 label material까지는
성공했지만, posterior target으로는 아직 실패했다. Primary relation binary는 positive class가
33개라 작고, balanced full slice를 만들어도 object pair, scan, cell/queue/reason/machine hint,
geometry/witness summary shortcut이 남는다. `connected to` diagnostic target은 functional
connection ambiguity를 드러내는 데는 유용하지만 main reliability target이 아니다.
Geometry-support target은 `81/73`으로 class mass는 통과하지만 auxiliary evidence target이므로
relation reliability를 대체할 수 없다. 따라서 다음 단계는 posterior smoke가 아니라 path
decision이다.

v44 attachment path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v18_attachment_deferred_path_decision_select_v19_independent_evidence_repair_plan
selected_path = freeze_v18_attachment_diagnostic_select_v19_independent_evidence_repair_plan
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_repair_plan
relation_binary_counts = {'0': 81, '1': 33}
relation_class_mass_pass = false
relation_strict_clear_slice_count = 0
relation_diagnostic_clear_slice_count = 0
posterior_smoke_allowed = false
multi_view_as_model_input = false
validation_errors = 0
```

v44의 판단은 다음과 같다. v18 attachment target은 H002 가설의 실패가 아니라
target-construction negative evidence다. 현재 blocker는 posterior 결합 방식이 약해서가 아니라,
label target이 geometry/witness summary 및 construction metadata에 너무 가깝다는 점이다.
따라서 v18은 diagnostic-only로 고정하고, 다음 route는 independent evidence repair plan으로
간다. 여기서 multi-view 또는 mesh는 label/audit confirmation evidence로만 허용하고, 아직
deployable model input으로 넣지 않는다.

v45 attachment independent-evidence repair plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_ready_for_source_inventory
selected_route = independent_visual_or_mesh_audit_packet_before_labels
primary_scope = attached to, hanging on
diagnostic_scope = connected to
source_probe_exists = true
source_probe_sample_multi_view_dirs = 40
source_probe_sample_sequence_dirs = 40
multi_view_as_model_input = false
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_source_inventory
```

v45의 핵심은 label/audit supervision으로 쓰는 독립 evidence와 deployable model input feature를
분리하는 것이다. `A_ind_e`는 현재 label/audit decision에만 쓰고, `V_mv_e`는 future deployable
visual evidence factor로만 남긴다. 즉 multi-view가 존재한다는 이유만으로 posterior input에
넣지 않는다. 다음 단계는 v18 rows에 대해 subject/object crop count, same-view/co-visible
candidate, sequence context, mesh/point availability, audit-ready decision을 정식 inventory로
계산하는 것이다.

v46 attachment source inventory 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_source_inventory_ready
rows = 240
primary_rows = 160
primary_both_have_crop_rows = 160
primary_possible_covisible_or_same_view_rows = 160
primary_audit_ready_rows = 160
strong_pair_visual_ready_rows = 43
rows_by_visual_context_state = {'same_view_rank_weak_proxy': 197, 'same_frame_covisible_strong': 43}
rows_by_audit_ready_state = {'individual_visual_plus_mesh_audit_ready': 197, 'strong_pair_visual_audit_ready': 43}
unique_scans = 202
scan_exists = 202
multi_view_exists = 202
sequence_exists = 202
mesh_ready = 202
source_inventory_gate_pass = true
validation_errors = 0
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan
```

v46의 의미는 source availability가 충분하다는 것이지, 모든 row가 직접적인 visual-confirmed
relation이라는 뜻은 아니다. Exact origin-frame overlap이 있는 `strong_pair_visual_audit_ready`
row는 43개뿐이고, 나머지 대부분은 subject/object individual crops plus mesh/sequence context다.
따라서 다음 audit packet은 `strong_pair_visual_audit_ready`와
`individual_visual_plus_mesh_audit_ready`를 분리해야 한다. 후자는 relation co-visibility가 아니라
object identity와 mesh/context confirmation evidence로 해석해야 한다.

v47 attachment audit packet plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan_ready_for_materialization
rows = 240
primary_attachment_reliability_candidate = 160
connected_diagnostic_only = 62
uncertainty_or_coverage_audit_only = 18
T1_strong_pair_visual = 43
T2_individual_visual_plus_mesh = 197
primary_T1_strong_pair_visual = 31
primary_T2_individual_visual_plus_mesh = 129
primary_attached_to = T1 17, T2 63
primary_hanging_on = T1 14, T2 66
audit_packet_plan_gate_pass = true
validation_errors = 0
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization
```

v47에서는 reviewer-visible schema와 hidden asset manifest plan을 분리했다. Visible packet에는
`scan_id`, `subgraph_id`, instance id, `geometry_status_hidden`, `rank_band_hidden`,
`machine_hint_hidden`, `raw_features_hidden`, v18 label state/target/reason/review note를 넣지 않는다.
Asset path와 scan/instance id는 materialization용 hidden manifest에만 둔다.

v48 attachment audit packet materialization 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization_ready_for_leakage_review
visible_review_rows = 240
packet_dirs = 240
materialized_hidden_manifest_rows = 240
total_materialized_images = 4466
visible_leakage_hits = 0
validation_errors = 0
primary_attachment_reliability_candidate = 160
connected_diagnostic_only = 62
uncertainty_or_coverage_audit_only = 18
T1_strong_pair_visual = 43
T2_individual_visual_plus_mesh = 197
primary_T1_strong_pair_visual = 31
primary_T2_individual_visual_plus_mesh = 129
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review
```

v48은 actual label fill이 아니다. Reviewer-visible packet은 neutral local filenames
(`subject_crop_01.jpg`, `object_view_01.jpg` 등)만 사용하고, source path / scan id /
subgraph id / instance id / original filename은 `materialized_hidden_manifest.jsonl`에만 둔다.
Internal leakage scan은 0 hit이지만, label fill 전 formal leakage review가 별도 gate로 필요하다.

v49 attachment audit packet leakage review 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review_passed_ready_for_label_fill
visible_sheet_rows = 240
packet_markdown_files = 240
packet_dirs = 240
neutral_image_files = 4466
hidden_manifest_rows = 240
hidden_rows_with_source_paths = 240
hidden_rows_with_scan_ids = 240
visible_leakage_hits = 0
validation_errors = 0
formal_leakage_review_pass = true
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill
```

v49는 reviewer-visible surface가 clean하다는 의미다. 아직 repaired relation reliability label이
생긴 것은 아니며, target-independence도 아직 검증 전이다. 다음 label fill은 packet image와
visible context만 보고 수행해야 하고, hidden manifest는 label 이후 ingestion/audit join에만 사용한다.

v50 attachment audit packet label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_filled_codex_visible_packet
rows = 240
review_relation_reliability = {
  accept_reliable_attachment: 26,
  reject_unreliable_attachment: 99,
  abstain_uncertain: 53,
  diagnostic_connected_possible: 15,
  diagnostic_connected_ambiguous: 47
}
review_geometry_support = {supports: 41, contradicts: 99, ambiguous: 100}
review_uncertainty = {low: 28, medium: 135, high: 15, diagnostic_only: 62}
binary_primary_usable_rows = 125
primary_positive_rows = 26
primary_negative_rows = 99
diagnostic_connected_rows = 62
validation_errors = 0
hidden_manifest_read = false
posterior_smoke_allowed = false
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion
```

v50은 label materialization gate는 통과했지만 posterior gate를 통과한 것은 아니다.
Primary binary preview가 `26/99`라 positive-sparse risk가 남는다. 이 결과는 v19의
independent audit packet이 효과 없다는 결론이 아니라, filled label을 hidden metadata와
join한 뒤 class mass, predicate/tier balance, endpoint/object-label shortcut, T1/T2 evidence-tier
shortcut을 별도로 audit해야 한다는 의미다.

v51 attachment audit packet label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_positive_sparse_with_probe_risk
rows = 240
multiclass_rows = 240
primary_binary_rows = 125
connected_diagnostic_rows = 62
geometry_support_rows = 140
uncertainty_rows = 240
abstain_rows = 115
primary_binary_target = {1: 26, 0: 99}
geometry_support_target = {1: 41, 0: 99}
connected_diagnostic_target = {
  diagnostic_connected_possible: 15,
  diagnostic_connected_ambiguous: 47
}
class_mass_pass = false
quick_probe_risk_flags = 43
same_scan_mixed_primary_binary_groups = 4
same_visible_pair_mixed_primary_binary_groups = 0
same_predicate_mixed_primary_binary_groups = 2
same_evidence_tier_mixed_primary_binary_groups = 2
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit
```

v51은 target artifact를 만들었지만 posterior-ready target을 만든 것은 아니다. 특히
primary binary positive가 26개로 minimum-per-class 50 기준에 못 미치고, visible pair 내부
mixed binary group이 0개라 endpoint identity가 label을 과도하게 설명할 수 있다. 따라서
다음 단계는 posterior가 아니라 target-independence audit이다.

v52 attachment audit packet target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
relation_binary_rows = 125
relation_binary_counts = {1: 26, 0: 99}
relation_class_mass_pass = false
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
geometry_support_rows = 140
geometry_support_counts = {1: 41, 0: 99}
connected_diagnostic_rows = 62
connected_diagnostic_counts = {
  diagnostic_connected_possible: 15,
  diagnostic_connected_ambiguous: 47
}
full_quick_probe_risk_flags = 56
slice_blocking_risk_flags = 1185
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_path_decision_after_audit
```

주요 shortcut은 visible endpoint pair, scan/subgraph grouping, subject label, primary reason이다.
`subject_object_visible_pair`만으로 relation binary를 1.0 accuracy로 맞출 수 있고,
`scan_id_hidden`/`subgraph_id_hidden`도 각각 0.968/0.992 accuracy를 보인다. 따라서 v19
packet target은 label provenance는 개선했지만 posterior-ready method target은 아니다.

v53 attachment audit packet path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v19_attachment_deferred_audit_packet_path_decision_select_v20_endpoint_balanced_counterfactual_repair_plan
selected_path = freeze_v19_audit_packet_diagnostic_select_v20_endpoint_balanced_counterfactual_repair_plan
relation_binary_counts = {1: 26, 0: 99}
geometry_support_counts = {1: 41, 0: 99}
connected_diagnostic_counts = {
  diagnostic_connected_possible: 15,
  diagnostic_connected_ambiguous: 47
}
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan
```

이 결정은 v19를 버린다는 뜻이 아니라, v19를 negative target-construction evidence로 고정한다는
뜻이다. 현재 문제는 결합 방식이 약한 것이 아니라 target이 endpoint/object/predicate/scan
shortcut으로 설명될 수 있다는 점이다. 따라서 v20은 full train attachment candidate pool에서
endpoint-balanced / counterfactual target을 새로 설계해야 한다.

v54 endpoint-balanced counterfactual repair plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan_ready_for_capacity_scan
route = endpoint_balanced_counterfactual_repair
primary_predicates = attached to, hanging on
diagnostic_predicates = connected to
candidate_sample_size_options = 240, 320, 400
default_candidate_sheet_if_capacity_allows = 320
post_label_accept_min = 60
post_label_reject_min = 60
post_label_usable_binary_min = 160
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan
```

이 plan은 candidate mining이나 label fill이 아니다. 다음 capacity scan은 exact visible
endpoint-pair mixed contrast를 우선 평가하고, 부족하면 subject/object-family, predicate,
evidence-tier, scan-balanced counterfactual fallback이 가능한지 계산해야 한다.

v55 endpoint-balanced counterfactual capacity scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan_passed_ready_for_candidate_mining
capacity_pass = true
selected_capacity_route = exact_endpoint_pair_mixed_contrast_primary
attachment_rows = 556038
primary_rows = 370692
diagnostic_rows = 185346
raw_feature_join_coverage = 1.0
exact_endpoint_pair_mixed_groups = 4616
exact_endpoint_pair_balanced_pairs = 26054
object_family_mixed_groups = 168
scan_balanced_mixed_blocks = 2309
N=240/320/400 feasible = true/true/true
default_next_candidate_size = 320
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining
```

v55의 의미는 row capacity 문제가 해결됐다는 것이다. 그러나 아직 target이 valid하다는 뜻은
아니다. 다음 candidate mining은 exact endpoint-pair mixed contrast route를 유지하면서 hidden
sampling fields를 visible label surface에서 제거해야 한다. Label fill과 target-independence audit이
통과되기 전까지 posterior smoke는 계속 금지된다.

v56 endpoint-balanced counterfactual candidate mining 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining_ready_for_source_inventory
selected_rows = 320
primary_binary_candidate_rows = 256
connected_diagnostic_rows = 64
attached_to_rows = 128
hanging_on_rows = 128
connected_to_rows = 64
attached to positive/negative proxy = 64/64
hanging on positive/negative proxy = 64/64
connected to near/far diagnostic = 32/32
unique_scans = 247
unique_subgraphs = 294
unique_visible_endpoint_pairs = 104
visible_leakage_hits = 0
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory
```

v56은 candidate sheet를 만들었지만 label-ready benchmark를 만든 것은 아니다. v20은
multi-view/mesh를 deployable input이 아니라 label/audit confirmation evidence로 사용하기로
했으므로, 다음 단계는 새 320개 row에 대해 source inventory를 확인해야 한다.

v57 endpoint-balanced counterfactual source inventory 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory_ready_for_audit_packet_plan
rows = 320
audit_ready_rows = 320
both_have_crop_rows = 320
primary_rows = 256
primary_both_have_crop_rows = 256
primary_possible_covisible_or_same_view_rows = 256
primary_audit_ready_rows = 256
connected_diagnostic_rows = 64
connected_diagnostic_audit_ready_rows = 64
strong_pair_visual_ready_rows = 75
same_frame_covisible_strong = 75
same_view_rank_weak_proxy = 245
individual_visual_plus_mesh_audit_ready = 245
unique_scans = 247
scan_exists / multi_view_exists / sequence_exists / mesh_ready = 247 / 247 / 247 / 247
source_inventory_gate_pass = true
posterior_smoke_allowed = false
validation_errors = 0
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan
```

v57은 320-row candidate set이 audit packet으로 진행될 source evidence를 갖는다는 점을
확인했다. 하지만 strong same-frame co-visible evidence는 75개뿐이므로, 다음 packet plan은
75개 T1 strong pair visual evidence와 245개 T2 individual-view-plus-mesh evidence를 분리해
보존해야 한다. 이 단계는 label fill, target ingestion, target-independence audit, posterior
smoke가 아니다.

v58 endpoint-balanced counterfactual audit packet plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan_ready_for_materialization
rows = 320
primary_attachment_reliability_candidate = 256
connected_diagnostic_only = 64
attached to / hanging on / connected to = 128 / 128 / 64
T1_strong_pair_visual = 75
T2_individual_visual_plus_mesh = 245
primary_T1_strong_pair_visual = 62
primary_T2_individual_visual_plus_mesh = 194
connected_T1_strong_pair_visual = 13
connected_T2_individual_visual_plus_mesh = 51
attached to T1/T2 = 27 / 101
hanging on T1/T2 = 35 / 93
audit_packet_plan_gate_pass = true
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization
```

v58은 visible packet template, visible schema, audit packet contract, hidden asset manifest plan을
만들었다. Visible packet에는 scan/subgraph/instance ids, proxy role, selection route, typed
witness, rank, source score, `p_geom_valid`, geometry status, raw feature path가 들어가지 않는다.
Hidden asset manifest에만 source path와 construction metadata가 남으며, 다음 단계에서 neutral
packet-local name으로 materialize해야 한다.

v59 endpoint-balanced counterfactual audit packet materialization 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization_ready_for_leakage_review
visible_review_rows = 320
packet_dirs = 320
materialized_hidden_manifest_rows = 320
total_materialized_images = 5836
visible_leakage_hits = 0
validation_errors = 0
T1_strong_pair_visual = 75
T2_individual_visual_plus_mesh = 245
primary_T1_strong_pair_visual = 62
primary_T2_individual_visual_plus_mesh = 194
gt_match_axis_joined_rows = 320
gt_label_match_status = exact_match:1, family_match:5, pair_has_other_predicate:81, no_gt_for_pair:233
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review
```

v59는 packet materialization 단계에서 future evaluation policy도 보존했다. Human-audited
reliability label은 아직 존재하지 않지만, 이후 label ingestion 시 existing GT relation match와
결합할 수 있도록 hidden materialized manifest에 GT-match auxiliary axis를 join했다. 이 GT axis는
visible packet에는 노출하지 않는다.

v60 endpoint-balanced counterfactual audit packet leakage review 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review_passed_ready_for_label_fill
visible_sheet_rows = 320
packet_markdown_files = 320
packet_dirs = 320
neutral_image_files = 5836
hidden_manifest_rows = 320
hidden_rows_with_source_paths = 320
hidden_rows_with_scan_ids = 320
hidden_rows_with_gt_match_axis = 320
visible_leakage_hits = 0
validation_errors = 0
formal_leakage_review_pass = true
gt_label_match_status = exact_match:1, family_match:5, pair_has_other_predicate:81, no_gt_for_pair:233
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill
```

v60은 label fill 전 reviewer-visible surface의 정보 누출을 점검한 gate다. Visible sheet,
packet markdown, neutral packet-local image filenames에는 source path, scan/subgraph/instance id,
prediction id, geometry status, rank/score, `p_geom_valid`, raw feature field, GT-match field,
RGA bucket label이 노출되지 않았다. Hidden materialized manifest에는 label ingestion 이후
mismatch analysis를 위해 source path, scan id, existing GT-match auxiliary axis가 보존되어 있다.
따라서 다음 단계는 hidden manifest를 읽지 않고 leakage-reviewed packet surface만 사용해
human-audited reliability label을 채우는 것이다.

v61 endpoint-balanced counterfactual audit packet label fill 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_filled_user_visible_packet
visible_sheet_rows = 320
review_fields_filled = 320/320
hidden_manifest_read_for_labeling = false
validation_errors = 0
relation_reliability = accept_reliable:25, reject_unreliable:182, abstain_uncertain:113
primary_relation_reliability = accept_reliable:25, reject_unreliable:182, abstain_uncertain:49
connected_relation_reliability = abstain_uncertain:64
geometry_support = supported:61, unsupported:158, uncertain:101
endpoint_identity = clear_endpoint_identity:259, uncertain_endpoint_identity:61
coverage = sufficient:75, limited:245
uncertainty = none:134, visual_ambiguous:61, functional_connection_ambiguous:53, ontology_ambiguous:37, mesh_needed:35
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion
```

v61 label fill은 user-filled visible packet labels를 검증하고 잠근 단계다. Label decisions
used only the leakage-reviewed visible sheet and packet-local visual evidence. Hidden manifest,
source paths, scan ids, GT-match axis, rank/score, geometry status, and `p_geom_valid` were
not used. The `connected to` rows remain diagnostic-only and were not converted into final
reliable positives. The primary relation labels are positive-sparse (`25` accept vs `182`
reject), so posterior smoke remains blocked until label ingestion and target-independence
audit prove that a controlled non-shortcut slice exists.

v62 endpoint-balanced counterfactual audit packet label ingestion 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingested_positive_sparse_with_probe_risk
rows = 320
multiclass_rows = 320
primary_binary_rows = 207
primary_binary_target = positive:25, negative:182
connected_diagnostic_rows = 64
geometry_support_rows = 219
endpoint_identity_rows = 320
coverage_rows = 320
uncertainty_rows = 320
gt_label_match_status = exact_match:1, family_match:5, pair_has_other_predicate:81, no_gt_for_pair:233
quick_probe_risk_flags = 70
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit
```

v62에서 required GT/reliability mismatch table도 생성했다.

```text
GT match & reliability accept = 0
GT match & reliability reject = 1
GT match & abstain = 5
No GT/current relation & reliability accept = 25
No GT/current relation & reliability reject = 181
No GT/current relation & abstain = 108
```

이 결과는 H002의 evaluation target policy를 실제 artifact로 연결한다. 다만 primary binary
target이 `25/182`로 positive-sparse이고, quick-probe risk flag가 70개라 posterior smoke는
계속 금지된다. 다음 단계는 target-independence audit이다.

v63 endpoint-balanced counterfactual audit packet target-independence audit 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk
rows = 320
primary_binary_rows = 207
primary_binary_target = positive:25, negative:182
relation_strict_clear_slices = 0
relation_diagnostic_clear_slices = 0
full_quick_probe_risk_flags = 82
slice_blocking_risk_flags = 1112
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit
```

Auxiliary targets도 main reliability target을 대체하지 못했다.

```text
geometry_support_binary = 219 rows, 61/158, class mass pass, strict clear 0
endpoint_identity_binary = 320 rows, 259/61, class mass pass, strict clear 0
coverage_binary = 320 rows, 75/245, class mass pass, strict clear 0
uncertainty_multiclass = 320 rows, min class 35, class sparse
connected_diagnostic = 64 rows, single class abstain_uncertain
```

핵심 해석은 다음이다. v20은 exact endpoint-pair capacity, packet leakage, source inventory,
GT-match axis 보존까지는 개선했지만, final relation reliability target은 여전히 posterior
검증용으로 충분하지 않다. Positive가 `25`개라 class-mass gate를 통과하지 못하고, balanced
`25/25` slice를 만들어도 predicate, review geometry support, endpoint identity, uncertainty,
subject/object label, visible pair, scan/subgraph id가 label을 설명한다. 특히
`review_geometry_support`가 relation binary를 거의 직접 설명하므로, 이 target으로 posterior를
돌리면 factorized reliability posterior의 효과가 아니라 geometry-support review target을
재현한 효과로 보일 위험이 크다.

따라서 v63 결론은 H002 가설의 실패가 아니라, v20 attachment-deferred audit-packet route가
posterior-ready target을 만들지 못했다는 target-construction negative evidence다. 다음 단계는
posterior가 아니라 path decision이다.

v64 endpoint-balanced counterfactual audit packet path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_select_v21_conditional_contrast_capacity_scan
selected_path = freeze_v20_audit_packet_diagnostic_select_v21_conditional_contrast_capacity_scan
next_todo = reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan
validation_errors = 0
posterior_smoke_allowed = false
```

v64의 핵심 판단은 다음이다. 현재 320-row packet이 우연히 reject-heavy였을 가능성은 남아
있으므로, 이 결과만으로 `attachment_deferred` 전체나 H002 factorization을 기각하지 않는다.
하지만 현재 target은 positive `25`개, strict/diagnostic clear slice `0/0`이고 shortcut risk가
남아 있으므로 posterior smoke, balanced `25/25` slice, stronger combiner, geometry-support-as-primary,
connected-to-primary는 모두 reject한다.

따라서 다음 route는 더 많은 label을 같은 방식으로 바로 채우는 것이 아니라, full train
attachment pool에서 조건부 contrast capacity가 실제로 있는지 먼저 확인하는 것이다. v21은
다음 질문에 답해야 한다.

```text
same predicate + same/near geometry-support proxy 안에도 accept/reject 후보가 있는가?
same predicate + same rank band 안에도 accept/reject 후보가 있는가?
same evidence tier + same coverage state 안에도 mixed reliability 후보가 있는가?
same object-pair family 안에도 mixed reliability 후보가 있는가?
uncertainty/coverage 때문에 abstain이 reject와 분리되는가?
```

이 단계는 H002의 factor 분해가 의미 있는 target이 full train에 존재하는지 확인하는 capacity
scan이지, posterior evidence가 아니다.

v65 conditional contrast capacity scan 결과는 다음과 같다.

```text
status = h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_blocked_predicate_imbalanced_strict_capacity
primary_rows = 370692
diagnostic_connected_rows = 185346
joined_rows = 556038
unique_scans = 1157
unique_subgraphs = 3738
unique_visible_pairs = 7995
accept_proxy_supported_candidate = 79491
reject_proxy_contradicted_candidate = 257849
uncertain_proxy = 33352
strict_spec = same_predicate_rank_geometry_family
strict_mixed_groups = 258
strict_balanced_capacity = 4507
strict_by_predicate = hanging_on_only
diagnostic_spec = same_predicate_rank_family
diagnostic_mixed_groups = 591
diagnostic_balanced_capacity = 53539
capacity_pass = false
failed_check = strict_spec_each_primary_predicate_mixed_min_10
validation_errors = 0
posterior_smoke_allowed = false
next_todo = reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan
```

해석은 다음이다. Full-train에는 conditional contrast proxy가 전혀 없는 것이 아니다.
`same predicate + rank + object-family` 수준에서는 `attached to`와 `hanging on` 모두
supported/contradicted proxy가 함께 존재한다. 그러나 strict condition인
`same predicate + rank + geometry bucket + object-family`까지 고정하면 mixed stratum이
`hanging on`에만 남고 `attached to`에서는 사라진다. 따라서 v21은 곧바로 label packet이나
posterior smoke로 넘어갈 수 없다.

이 결과는 H002 factorization의 실패가 아니라, primary predicate scope를 더 정확히 정해야
한다는 target-construction evidence다. 다음 path decision에서는 `hanging on`을 strict
primary로 좁히거나, `attached to`를 diagnostic/relaxed branch로 낮추는 선택을 검토해야 한다.
Relaxed diagnostic spec만 사용하면 수량은 커지지만 shortcut risk가 다시 커지므로, 바로
posterior smoke로 넘어가는 것은 금지한다.

v65에서 relation scope도 함께 정리했다. 다른 relation들도 train-only/full-train artifact에서
확인했지만, 현재 active primary target은 아니다.

| Relation | Full-Train Checked | Current Role | Reason |
| --- | --- | --- | --- |
| `close by` | true | diagnostic/generality evidence | current RGA queue가 `RGA-HL = 0`, `RGA-LH = 171324`인 LH-only branch |
| `standing on` | true | diagnostic support/contact branch | hard room-surface filter와 side/geometry shortcut issue |
| `lying on` | true | diagnostic support/contact branch | row mass는 충분하지만 HL/LH가 geometry status와 너무 강하게 정렬 |
| `supported by` | true | excluded from current primary | LH-only 또는 current core 밖 |
| `higher than` | true | relative-vertical control examined | HL capacity가 너무 작음 |
| `lower than` | true | relative-vertical control used | geometry-easy control family |
| `attached to` | true | active but strict-v21 blocked | strict condition에서 mixed proxy stratum 부족 |
| `hanging on` | true | active v21-supported | strict condition에서도 mixed proxy stratum 존재 |
| `connected to` | true | diagnostic-only | functional connection ambiguity 때문에 OBB/point geometry만으로 primary reliability 판단이 어려움 |

v66 conditional contrast path decision 결과는 다음과 같다.

```text
status = h002_reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_select_v22_hanging_on_strict_packet_plan
selected_path = freeze_v21_capacity_diagnostic_select_hanging_on_strict_primary_attached_to_diagnostic_relaxed_probe
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan
validation_errors = 0
posterior_smoke_allowed = false
```

strict condition의 성격도 명시했다.

```text
strict_spec = same_predicate_rank_geometry_family
fields = predicate_label + rank_band + geometry_bucket + object_family_pair
is_dataset_ground_truth_rule = false
is_h002_control_rule = true
```

즉 strict condition은 데이터셋의 GT rule이나 최종 model input rule이 아니라, target이
predicate, rank, coarse geometry bucket, object-family prior 중 하나만으로 풀리는 것을 막기
위한 H002 control rule이다. 이전 stage들이 반복적으로 shortcut 문제에 막혔기 때문에,
posterior claim 전에 이런 control이 필요하다.

v66의 결정은 다음이다.

```text
primary = hanging on strict conditional contrast
diagnostic = attached to relaxed/diagnostic probe
diagnostic_only = connected to
```

이 결정을 선택한 이유는 `hanging on`만 strict condition 안에서 mixed proxy strata를 유지하기
때문이다. `attached to`는 relaxed diagnostic spec에서는 수량이 충분하지만, strict spec에서는
사라진다. 따라서 `attached to`까지 primary에 넣으려면 geometry bucket control을 풀어야 하고,
이 경우 이후 posterior 성능이 좋아져도 factorized reliability가 아니라 coarse geometry bucket
shortcut 효과로 보일 위험이 크다.

v67 hanging-on strict packet plan 결과는 다음과 같다.

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan_ready_for_candidate_mining
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining
full_train_hanging_on_rows = 185346
strict_groups = 2222
strict_mixed_groups = 258
strict_balanced_capacity = 4507
dry_run_selected_rows = 240
dry_run_selected_role_counts = 120 / 120
dry_run_selected_strict_groups = 95
scan_count = 192
visible_endpoint_pair_count = 193
max_rows_per_scan = 4
max_rows_per_visible_endpoint_pair = 5
max_rows_per_strict_group = 4
validation_errors = 0
posterior_smoke_allowed = false
```

v67의 의미는 `hanging on` strict route가 pre-label packet planning 관점에서는 충분히 가능하다는
것이다. 240-row hidden-only preview가 95개 strict group과 192개 scan에 분산되므로, 이전 단계에서
문제가 됐던 scan/object/endpoint concentration risk가 상대적으로 낮다.

단, v67은 visible label sheet나 packet asset을 만든 단계가 아니다. `hidden_selection_preview.jsonl`은
candidate mining을 위한 internal dry-run artifact이며, reviewer-visible surface에는 rank,
geometry bucket, object-family, GT match, planned proxy role, strict group value를 노출하면 안 된다.
다음 단계는 이 plan을 사용해 hidden-field-safe candidate sheet를 만드는 것이다.

v68 hanging-on strict candidate mining 결과는 다음과 같다.

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_ready_for_source_inventory
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
candidate_rows = 240
visible_rows = 240
hidden_rows = 240
visible_leakage_hits = 0
validation_errors = 0
posterior_smoke_allowed = false
```

Hidden distribution:

```text
predicate_counts = hanging on: 240
planned_proxy_role_counts = 120 / 120
rank_band_counts = top100_only: 18, rank_101_200: 94, rank_201_500: 128
geometry_bucket_counts = near_overlap: 164, loose_near_no_overlap: 52, loose_near_overlap: 16, near_no_overlap: 8
coverage_proxy_counts = joined_no_uncertainty_flags: 117, joined_with_uncertainty_flags: 123
uncertainty_bucket_counts = none: 117, visual_or_mesh_needed: 123
gt_label_match_status_counts = no_gt_for_pair: 164, pair_has_other_predicate: 76
strict_group_count = 95
scan_count = 192
visible_endpoint_pair_count = 193
```

v68은 source ids, rank band, geometry bucket, object-family pair, GT-match status, planned proxy
role, strict group id를 hidden manifest에만 보존하고, visible candidate sheet에는 relation text와
blank review fields만 노출한다. 이 단계는 source inventory를 시작하기 위한 candidate artifact이지,
label-ready audit packet이나 posterior evidence가 아니다.

## Current Claim Boundary

Allowed:

- H002 frames relation reliability as a factorized semantic/geometry/coverage/uncertainty problem.
- RGA exposes bidirectional semantic-geometry mismatch.
- Current evidence shows target construction is the main blocker before posterior method claims.
- Exact endpoint-pair control is useful but insufficient when source rank and predicate are structurally entangled.
- Proximity has enough train-only LH candidates for a scoped repair branch, but current RGA queues do not provide proximity HL candidates.

Blocked:

- factorized posterior improves relation reliability.
- current labels are paper-level human-confirmed benchmark labels.
- validation/test generalization has been shown.
- bidirectional `close by` reliability has been solved by current H002.
- `attached to`, `hanging on`, `connected to`, `left/right/front/behind` are solved by current H002.
- multi-view evidence is a deployable posterior input.

## Baselines For Future Smoke

When a clean target exists, the main comparison should include:

```text
semantic_only
geometry_only
semantic_plus_geometry
factorized_reliability_posterior
```

Optional additional combiners from `feasibility_check.md`:

- coverage-gated geometry model
- residual reliability model
- pairwise rank-matched ranking
- monotonic calibrated additive model
- product-of-experts / log-odds factor model
- relation-family mixture-of-experts
- debiased / orthogonalized factor model

These are not next until target-independence is fixed.

## Relation Scope

Current core:

```text
attachment_deferred: hanging on strict source inventory, attached to and connected to diagnostic
```

Previous train-only/full-train branches:

```text
support_contact: standing on, lying on as diagnostic target-construction evidence
relative_vertical: higher than, lower than as control/diagnostic evidence
proximity: close by as LH-only diagnostic/generality evidence
```

Active empirical branch:

```text
reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
```

Deferred for generality:

```text
relative_horizontal: left, right, front, behind
```

`close by` has now passed the train-only feasibility count gate only as an LH-only
branch, but the visible-only proxy target is blocked by object-pair shortcut risk.
The visible-only branch is frozen as diagnostic-only; the active path is
attachment-deferred conditional contrast path decision.

## Next TODO

```text
reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
```

v22 source-inventory requirements:

1. Use train-only rows only.
2. Do not run posterior smoke.
3. Fix primary relation scope to `hanging on`.
4. Keep `attached to` and `connected to` diagnostic-only.
5. Use v68 `hidden_candidate_manifest.jsonl` and `candidate_rows.jsonl` as inputs.
6. Inventory scan, multi-view, sequence, mesh, subject/object crop, and packet-source availability for all 240 candidates.
7. Do not expose source paths or construction metadata in the visible sheet.
8. Keep multi-view/mesh as audit/confirmation evidence only.
9. Do not run packet materialization, label fill, ingestion, target-independence audit, or posterior smoke in source inventory.

Posterior smoke remains blocked until the selected target passes target-independence audit.
