# H002 Summary Branch V2

Last updated: 2026-06-22 KST

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
current_gate = v13 proximity LH scene/geometry label fill completed
current_status = visible-only scene/geometry proxy labels filled; positive-mass risk noted
posterior_evidence = false
paper_metric_evidence = false
validation_or_test_used = false
next_gate = reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
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
support_contact: standing on, lying on
relative_vertical: higher than, lower than
```

Active empirical branch:

```text
proximity: close by, scene/geometry-aware LH label ingestion
```

Deferred for generality:

```text
attachment_deferred: attached to, hanging on, connected to
relative_horizontal: left, right, front, behind
```

`close by` has now passed the train-only feasibility count gate only as an LH-only
branch, but the visible-only proxy target is blocked by object-pair shortcut risk.
The visible-only branch is frozen as diagnostic-only; the active path is
scene/geometry-aware label ingestion.

## Next TODO

```text
reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

Label-ingestion requirements:

1. Join `filled_label_sheet_v13.tsv` with `hidden_audit_manifest_v13.jsonl` only after labels are locked.
2. Produce multiclass target, binary accept/reject target, geometry-support target, and usefulness target.
3. Report positive mass explicitly; `accept_reliable_close_by = 39` is below the previous minimum-per-class gate.
4. Audit object-pair, scan, predicate, rank-band, machine-hint, geometry-bin, and construction-block shortcuts.
5. Check whether same visible object-pair blocks contain mixed accept/reject labels.
6. Do not run posterior smoke unless label ingestion and target-independence audit pass.

Posterior smoke remains blocked until the selected target passes target-independence audit.
