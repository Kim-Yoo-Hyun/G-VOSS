# H002 Report 0627

작성일: 2026-06-27 KST

## 목적

이 문서는 H002의 현재 relation type별 결과와 전체 상태를 정리한다. 범위는
`hypothesis/CAND-001/H002_factorized-relation-confidence/` 내부 train-only
hypothesis artifact다. Validation/test row는 사용하지 않았고, 현재 결과는 paper-level
evidence가 아니라 H002 방향성 검증 기록이다.

현재 H002의 working title은 다음과 같다.

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

핵심 factor contract는 다음으로 유지한다.

```text
T_e = semantic content
Z_e = source confidence / rank
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence quality / observability
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

## 결론 요약

현재 artifact 기준으로 강하게 말할 수 있는 것은 broad relation reliability가 아니라
train-only `C_e` mechanism이다.

- `higher than` / `lower than`은 현재 가장 깨끗한 main evidence다. 같은 geometry
  evidence `G_e`가 predicate semantic content `T_e`에 따라 compatible/incompatible로
  바뀐다는 점을 잘 보여준다.
- `lying on` / `standing on`은 pose-conditioned same-geometry contrast에서는 좋은
  `C_e` mechanism evidence를 보였고, point/multiview individual-predicate smoke에서는
  near-threshold compatibility-route signal을 보였다. 내부 gate는 diagnostic으로 유지하지만,
  논문에서는 support/contact를 fully solved family가 아니라 main compatibility-route evidence로
  사용할 수 있다.
- `close by`는 row 수는 충분하지만 LH-only로 치우치고 reliable positive가 적어
  diagnostic/generality evidence로 유지한다.
- `attached to` / `hanging on` / `connected to`는 visual/mesh observability와
  target independence가 병목이다. 특히 `connected to`는 functional relation이라
  단순 contact geometry로 reliability를 확정하기 어렵다.
- `left/right/front/behind/in front of`는 reference-frame protocol/source inventory,
  train-only same-G materialization, schema/shortcut audit, smoke-plan freeze, learned smoke
  runner, result review까지 완료했다. `M4_TG_horizontal_interaction`은 controls를 통과했고,
  main train-only frame-aware `C_e` mechanism evidence로 배치했다.

따라서 현재 H002의 상태는 다음과 같다.

```text
allowed_now = train-only predicate-conditioned compatibility C_e evidence
selected_main_route = relation-aware predicate-geometry compatibility routing
current_gate = R7 attachment-observability class-pair repair blocked by shortcut risk
blocked_now = paper-level result, held-out/test performance, all-family reliability,
              calibrated p_rel/p_obs posterior, support/contact independent-validity main result,
              close-by main claim under current target, R7 learned smoke under current target
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit
```

## Relation Type별 결과

### 요약 테이블

| Relation type | Family | 현재 역할 | 핵심 수치/결과 | 현재 판단 |
| --- | --- | --- | --- | --- |
| `higher than` | `relative_vertical` | main train-only `C_e` evidence | initial same-G smoke: `M5b` AUROC `1.000`, geometry-only `0.442`, source-only `0.494`, wrong-T `0.000` | 가장 강한 relation-level evidence |
| `lower than` | `relative_vertical` | main train-only `C_e` evidence | initial same-G smoke: `M5b` AUROC `1.000`, geometry-only `0.558`, source-only `0.515`, wrong-T `0.000` | 가장 강한 relation-level evidence |
| `higher/lower` combined | `relative_vertical` | current primary family | repaired exact-stratum target `1512` rows, `M6_TG_compatibility_interaction` AUROC `0.999990`, geometry-only `0.524527`, source-only `0.573820` | 현재 H002의 primary evidence |
| `lying on` | `support_contact_pose_conditioned` | compatibility-route evidence with caveat | same-G pose-conditioned smoke: `M5b` AUROC `1.000`; point/multiview individual-predicate smoke: `M8` AUROC `0.692578` | weaker support/contact slice |
| `standing on` | `support_contact_pose_conditioned` | compatibility-route evidence with caveat | same-G pose-conditioned smoke: `M5b` AUROC `1.000`; point/multiview individual-predicate smoke: `M8` AUROC `0.707930` | stronger support/contact slice |
| `lying/standing` independent validity | `support_contact_independent_validity` | diagnostic-only frozen | primary candidate `8631`; strict `predicate_x_class_pair` capacity `88` rows (`lying on = 64`, `standing on = 24`) | main target으로 부적합 |
| `supported by` | `support_contact` | feature probe / deferred | feature probe에서는 `standing on`과 superordinate overlap이 커서 clean opposing label로 쓰기 어려움 | 현재 learned smoke target에서 제외 |
| `close by` | `proximity` | diagnostic/generality | full train proximity queue `171324` rows, `RGA-HL = 0`, `RGA-LH = 171324`; v13 reliability binary `176` rows with `39/137` accept/reject | LH-only diagnostic, main `C_e`/posterior target 아님 |
| `attached to` | `attachment_like` | diagnostic/deferred | R7 class-pair repair observable p_rel `172/0`; visible-packet policy에서 reject 없음 | single-class diagnostic-only |
| `hanging on` | `attachment_like` | diagnostic/deferred | R7 class-pair repair observable p_rel `86/90`, but subject/class-pair predictors reach acc `1.0` | current target shortcut-blocked |
| `connected to` | `attachment_like` | diagnostic-only | positive-anchor route에서 `80` diagnostic rows. Functional connection ambiguity 때문에 binary compatibility target으로 쓰지 않음 | geometry-only로 확정 어려움 |
| `left/right/front/behind/in front of` | `relative_horizontal` | main train-only frame-aware `C_e` evidence | smoke rows `2,400`, labels `1,200/1,200`, `M4_TG_horizontal_interaction` AUROC `1.0000`, semantic-only `0.4558`, geometry-only `0.5000`, concat `0.4558`, controls collapse/invert; `in front of` excluded | main mechanism evidence with reference-frame caveat |

### 1. Relative Vertical: `higher than`, `lower than`

Artifact fact:

- Initial v3 same-geometry multi-predicate smoke:
  - `higher than`: `M5b_compatibility_TG_interaction` AUROC `1.000`.
  - `lower than`: `M5b_compatibility_TG_interaction` AUROC `1.000`.
  - geometry-only는 각각 `0.4421`, `0.5579` 수준이었다.
  - source-only는 각각 `0.4941`, `0.5152` 수준이었다.
  - wrong-T same-G control은 `0.000`이었다.
- Repaired independent-validity exact-stratum target:
  - family rows: `1512`.
  - positive/negative: `756/756`.
  - `M6_TG_compatibility_interaction` AUROC `0.9999895019736289`.
  - geometry-only AUROC `0.5245268889448783`.
  - source-only AUROC `0.5738203717701073`.

Interpretation:

`relative_vertical`은 현재 H002의 가장 강한 증거다. 중요한 점은 `G_e` 자체가
정답을 다 맞추는 것이 아니라, `T_e`와 `G_e`의 compatibility interaction이 필요하다는
것이다. 따라서 이 family는 H002의 `semantic score != geometry validity != relation
reliability` 문제의 구조를 가장 깨끗하게 보여준다.

단, 이 결과는 train-only이고 `higher/lower`라는 signed vertical relation에 강하게
집중되어 있다. 따라서 all-family reliability나 paper-level performance로 바로 쓰면 안 된다.

### 2. Support/Contact: `lying on`, `standing on`, `supported by`

Artifact fact:

- Mesh/pose/contact feature probe:
  - support/contact queue rows: `161498`.
  - Tier A semseg OBB/normal records: `161498`.
  - Tier B aligned PLY/contact-proxy records: `1200`.
  - `lying on` vs `standing on`은 pose-conditioned contrast candidate로 남았다.
  - `standing on` vs `supported by`는 superordinate overlap이 커서 clean opposing label로
    쓰기 어렵다고 판단했다.
- Pose-conditioned same-geometry target:
  - rows: `400`.
  - `lying on`: `200` rows, `M5b` AUROC `1.000`, geometry-only `0.500`.
  - `standing on`: `200` rows, `M5b` AUROC `1.000`, geometry-only `0.500`.
- Independent-validity target:
  - support/contact primary candidate rows: `8631`.
  - predicate-balanced 1200-row target은 `lying on = 300/300`,
    `standing on = 300/300`으로 만들 수 있었다.
  - 하지만 schema shortcut audit에서 `subject_class_label`, `object_class_label`,
    `subject_object_class_pair`, `predicate_x_class_pair`가 critical shortcut으로 남았다.
  - strict `predicate + subject_class + object_class` capacity는 `88` rows뿐이었다.
    - `lying on = 64`
    - `standing on = 24`
  - relaxed class-pair capacity는 `426` rows였지만 predicate-class shortcut을 완전히
    제거하지 못해 diagnostic-only로 남겼다.

Interpretation:

`lying on` / `standing on`은 `C_e` mechanism 자체는 잘 보인다. 같은 geometry라도 누워 있는
pose인지 서 있는 pose인지에 따라 predicate compatibility가 달라지는 구조가 있기 때문이다.

그러나 independent-validity target으로 바꾸는 순간 object-class와 predicate-class shortcut이
너무 강하게 남는다. 현재 Open3DSG train-side source만으로는 support/contact를 main reliability
claim으로 올리기 어렵다. 이 family를 main으로 쓰려면 human/visual/mesh audit 또는 다른 GT/source
축이 필요하다.

`supported by`는 현재 evidence probe 단계에서만 의미가 있다. `standing on`과 계층적으로 겹치는
superordinate predicate 성격이 강해서, 현 target에서는 clean negative/positive opposing label로
사용하지 않았다.

### 3. Proximity: `close by`

Artifact fact:

- Full train proximity feasibility:
  - total proximity rows: `185346`.
  - queue proximity rows: `171324`.
  - `RGA-HL proximity rows = 0`.
  - `RGA-LH proximity rows = 171324`.
  - strict LH pool rows: `50966`.
- V12 visible-only label fill:
  - rows: `240`.
  - accept/reject/abstain: `36/71/133`.
  - binary usable rows: `107`.
  - quick probe shortcut risk flags: `10`.
- V13 scene/geometry-aware label ingestion:
  - rows: `240`.
  - binary rows: `176`.
  - accept/reject: `39/137`.
  - abstain: `64`.
  - geometry support target: `121/55`.
  - quick probe risk flags: `32`.
- V13 target-independence audit:
  - full quick-probe risk flags: `41`.
  - slice blocking risk flags: `517`.
  - strict clear slices: `0`.
  - diagnostic clear slices: `0`.

Interpretation:

`close by`는 수량이 부족한 문제가 아니라 target definition 문제다. 현재 queue에서는
high-semantic + low-geometry 쪽이 사실상 없고 LH-only로 치우친다. 또한 가까움 자체가 dense
relation noise, annotation sparsity, trivial local context와 섞인다.

따라서 `close by`는 H002 generality와 failure taxonomy에는 유용하지만, 현재 단계의 main
posterior target이나 main `C_e` proof로 쓰기는 어렵다.

### 4. Attachment-Like: `attached to`, `hanging on`, `connected to`

Artifact fact:

- Numeric geometry materialization:
  - total rows: `240`.
  - predicate counts:
    - `attached to = 82`
    - `hanging on = 96`
    - `connected to = 62`
  - compatibility binary rows: `114`.
  - compatibility positive/negative: `33/81`.
  - by predicate:
    - `attached to`: positive `11`, counterfactual negative `38`, unknown `33`.
    - `hanging on`: positive `22`, counterfactual negative `43`, unknown `31`.
    - `connected to`: unknown `62`.
- Numeric geometry smoke:
  - compatibility `TG` AUROC `0.9281705948372615`.
  - factorized `TZGQ` AUROC `0.9364010475121586`.
  - geometry-only `G` AUROC `0.8948746726524505`.
  - source AUROC `0.46352413019079686`.
  - hidden construction probe AUROC `0.8767302656191545`.
- Shortcut-controlled small slice:
  - rows: `34`.
  - positive/negative: `17/17`.
  - compatibility `TG` AUROC `0.9550173010380623`.
  - factorized `TZGQ` AUROC `0.9688581314878892`.
  - geometry-only AUROC `0.7231833910034602`.
  - hidden probes near chance.
- 400-row controlled candidate:
  - candidate rows: `400`.
  - primary rows: `320`.
  - positive/negative: `160/160`.
  - compatibility/factorized AUROC `1.000`.
  - geometry-only AUROC `1.000`.
  - hidden proxy audit failed because hidden proxy also AUROC `1.000`.
- 560-row positive-anchor independent audit:
  - rows: `560`.
  - predicate counts:
    - `attached to = 238`
    - `hanging on = 242`
    - `connected to = 80`
  - review relation reliability:
    - accept `60`
    - reject `246`
    - abstain `254`
  - primary binary target: `60/246`.
  - p_obs target: `306/254`.
  - full risk flags: `112`.
  - strict clear slices: `0`.
  - diagnostic clear slices: `0`.

Interpretation:

Attachment-like relation은 가장 중요한 future direction 후보지만, 현재 main evidence는 아니다.
초기 numeric/controlled smoke에서는 signal이 보였지만, 더 독립적인 audit target으로 가면
positive-sparse와 shortcut risk가 반복된다.

`attached to`와 `hanging on`은 visual/mesh evidence가 없으면 접촉, 부착점, orientation, functional
plausibility를 구분하기 어렵다. `connected to`는 더 강하게 functional/semantic relation이라서
contact/near geometry만으로 reliability label을 확정하기 어렵다.

따라서 attachment-like family는 `Q_e`와 observability의 필요성을 보여주는 diagnostic evidence로
유지하고, main으로 승격하려면 independent visual/mesh audit target source가 먼저 필요하다.

### 5. Relative Horizontal: `left`, `right`, `front`, `behind`

Artifact fact:

현재 H002에서는 `left/right/front/behind` relation을 materialization하거나 learned smoke로
검증하지 않았다.

Interpretation:

이 family는 geometry evidence 자체보다 reference frame 정의가 먼저 필요하다. `front`와 `behind`는
object intrinsic orientation, room coordinate, camera/viewer frame 중 어느 기준인지에 따라
정답이 달라진다. 따라서 현재 H002의 핵심 병목인 target-identifiability와 별도의 ambiguity를
가져오므로 보류했다.

## 현재 상태 정리

### 현재 가능한 주장

현재 가능한 주장은 다음으로 제한한다.

```text
H002 shows train-only evidence that relation reliability benefits from
predicate-conditioned semantic-geometry compatibility C_e.
```

좀 더 구체적으로는:

- `T_e`와 `G_e`를 독립적으로 두고, `C_e = compatibility(T_e, G_e)`를 학습하는 구조가
  `relative_vertical`에서 semantic/source-only와 geometry-only보다 강한 구분력을 보였다.
- `support_contact_pose_conditioned`에서도 같은 `G_e`가 `lying on` / `standing on` semantic
  content에 따라 compatible/incompatible로 바뀌는 mechanism은 확인됐다.
- 그러나 이것은 아직 `p_rel/p_obs` reliability posterior 전체가 잘 된다는 뜻은 아니다.

### 현재 막힌 주장

아래 주장은 아직 막혀 있다.

- paper-level held-out/test result.
- calibrated `p_rel` / `p_obs` posterior.
- all-family 3DSSG relation reliability.
- support/contact independent-validity main result.
- attachment/proximity/horizontal generality.
- VL-SAT/Open3DSG test-level recall/violation improvement under H002 method.

### 병목의 원인

현재 병목은 combiner architecture가 약해서가 아니다. 더 큰 Transformer나 MoE를 붙이기 전에
다음이 먼저 해결되어야 한다.

1. Target independence
   - label이 `predicate_label`, object class, endpoint pair, rank band, geometry status로 쉽게
     맞춰지면 factorized reliability를 증명하지 못한다.

2. Positive-sparse target
   - `close by`, `attachment_like`, `hanging on`에서 accept/reliable positive가 너무 적거나
     특정 object/anchor에 몰린다.

3. Observability and evidence quality
   - attachment-like relation은 point/OBB geometry만으로 판단하기 어려운 경우가 많다.
   - `Q_e`가 필요한 이유는 이 지점에서 분명하지만, 아직 deployable `Q_e` target은 없다.

4. Relation-family heterogeneity
   - `higher/lower`는 clean signed vertical compatibility.
   - `lying/standing`은 pose-conditioned physical compatibility.
   - `close by`는 dense proximity/usefulness problem.
   - `attached/hanging/connected`는 visual/mesh/functional evidence problem.
   - 따라서 하나의 scalar geometry validity로 모든 family를 설명하기 어렵다.

### 다음 결정 지점

다음 TODO는 이미 고정되어 있다.

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```

선택지는 네 가지다.

1. `relative_vertical` held-out/Docker promotion
   - 장점: 현재 가장 깨끗한 evidence를 paper-like protocol로 승격 가능.
   - 단점: relation scope가 좁고, top-tier novelty가 `higher/lower`에 갇힐 수 있음.

2. human/visual/mesh audited support/contact target
   - 장점: `support_contact`를 main family로 만들 수 있는 가장 직접적인 경로.
   - 단점: 새 label/audit workload가 필요하고, visual/mesh evidence boundary를 엄격히 관리해야 함.

3. cross-source agreement target
   - 장점: Open3DSG train-side target shortcut을 줄일 수 있음.
   - 단점: source disagreement가 reliability GT인지, source-specific bias인지 분리해야 함.

4. H002를 mechanism evidence로 멈추고 H001/GeoCalib paper path로 복귀
   - 장점: 현재 AAAI 2027 관점에서는 H001/GeoCalib이 더 완성된 paper path.
   - 단점: H002의 더 큰 contribution은 후속 연구로 남음.

현재 판단은 2번 또는 3번을 선택하지 않는 한 H002를 broad top-tier method로 밀기 어렵다는 것이다.
반대로 2번/3번이 성립하면 H002는 단순 geometry re-ranking이 아니라
`predicate-geometry compatibility learning + observability-aware reliability`로 다시 강해질 수 있다.

## 2026-06-28 Decision Update

다음 target-source route를 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/
status = h002_compatibility_dataset_v3_independent_target_source_decision_selected
selected_path = select_support_contact_visual_mesh_human_audit_with_size_containment_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan
```

Selected main route:

```text
support_contact_human_visual_mesh_audit_target
```

선택 이유는 relation type 수가 부족해서가 아니라 target-source independence가 현재 병목이기
때문이다. 따라서 `relative_vertical`만 held-out/Docker promotion하는 것은 보류하고,
`lying on`, `standing on`, `supported by`에 대해 visual/mesh/human audit 기반의 independent
target source를 설계하는 쪽을 선택했다.

추가 relation type은 main route가 아니라 bounded probe로 둔다.

```text
size_relative = bigger than / smaller than, optional feasibility probe, GT total 1822
containment_inclusion = standing in / lying in / build in / part of / belonging to / cover / hanging in, high-risk optional probe, GT total 847
leaning against = future probe, GT total 184
left/right/front/behind = deferred because of reference-frame ambiguity
same as / same symmetry as = not recommended for H002 main
```

## Source Artifacts

주요 근거 artifact:

- `artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/summary.json`
- `artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/target_source_contract.json`
- `artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/summary.json`
- `artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/family_scope.csv`
- `artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/metrics_by_predicate.json`
- `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/metrics_by_family.json`
- `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/metrics.json`
- `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/metrics_by_predicate.json`
- `artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan/summary.json`
- `artifacts/attachment_numeric_geometry_v1/summary.json`
- `artifacts/attachment_numeric_geometry_smoke_v1/summary.json`
- `artifacts/attachment_shortcut_controlled_smoke_v1/summary.json`
- `artifacts/attachment_controlled_candidate_smoke_v1/summary.json`
- `artifacts/attachment_independent_positive_anchor_label_ingestion_v1/summary.json`
- `artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/summary.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v10_proximity_relation_family_feasibility_scan/summary.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v13_proximity_lh_scene_geometry_label_ingestion/summary.json`
- `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit/summary.json`

## 2026-06-28 Audit Target Plan Update

Support/contact visual/mesh audit target plan을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory
selected_path = plan_visual_mesh_audit_target_source_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory
```

선택 relation은 그대로 둔다.

```text
lying on
standing on
supported by
```

이 단계의 의미는 row를 생성하거나 label을 채운 것이 아니라, 독립 audit target source의
contract를 먼저 고정한 것이다. 핵심 정책은 다음과 같다.

- label source는 visible visual/mesh evidence다.
- `source_score`, `rank`, `queue_kind`, old `geometry_status`, old `p_geom_valid`는 label 작성
  중 숨긴다.
- `No-GT`는 negative label이 아니다.
- `supported by`는 broad/superordinate support relation이므로 `standing on`의 clean negative로
  자동 사용하지 않는다.
- `C_e`, `Q_e`, `p_obs`, `p_rel`을 분리하고, abstain row를 `p_rel`의 false negative로
  취급하지 않는다.

Planned audit size:

```text
target_total_rows = 480
minimum_total_rows = 360
minimum_per_predicate = 80
minimum_accept/reject/abstain = 80/80/60
```

Prior source capacity:

```text
support/contact rows = 161498
distinct scans = 1157
distinct directed pairs = 75763
lying on = 60652
standing on = 50245
supported by = 50601
scan asset complete rate = 1.0
mesh contact surface possible rate = 1.0
sequence multiview possible rate = 1.0
```

## 2026-06-28 Audit Source Inventory Update

Support/contact visual/mesh audit source inventory를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization
selected_path = source_inventory_ready_packet_materialization_required
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization
```

Selected source:

```text
selected_rows = 480
lying on = 194
standing on = 156
supported by = 130
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

이 결과는 label-ready가 아니라 packet-materialization-ready다. Visible sheet에는
`PACKET_PENDING/...` 경로만 있고, `source_score`, `rank`, `queue_kind`, old
`geometry_status`, old `p_geom_valid`, label-match status는 hidden manifest에만 남겼다.
다음 단계는 이 480개 row에 대해 실제 point/mesh/multiview packet asset을 생성하거나
조립하는 것이다.

## 2026-06-28 Audit Packet Materialization Update

Support/contact visual/mesh audit packet materialization을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/
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
lying on | ready = 194
standing on | ready = 156
supported by | ready = 130
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

Visible label sheet:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization/visible_review_sheet_with_packets.csv
```

주의할 점은 `mesh_contact_render.png`가 full 3D contact-surface rendering이 아니라
reviewer-facing mesh/geometry availability card라는 것이다. 현재 label fill은 pair crop,
multi-view crop sheet, mesh/geometry source availability를 함께 보고 진행할 수 있다. 실제
3D contact-surface render가 필요하면 후속 asset hardening TODO로 분리해야 한다.

## 2026-06-28 Audit Label Fill Update

Support/contact visual/mesh audit label fill을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion
```

Provenance:

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

이 결과는 사용자가 요청한 Codex proxy label fill이며 독립 blind human audit이 아니다. 다음
단계에서는 label lock 이후 hidden manifest를 join해서 `C_e`, `Q_e`, `p_obs`, `p_rel` target을
생성하고, target-independence 및 shortcut audit을 먼저 수행해야 한다.

## 2026-06-28 Audit Label Ingestion Update

Support/contact visual/mesh audit label ingestion을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke
selected_path = ingest_proxy_labels_run_independence_diagnostics_block_smoke_if_shortcut
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion
```

Target materialization:

```text
rows = 480
relation multiclass = accept 208 / reject 161 / abstain 111
p_rel binary rows = 369
p_rel target = positive 208 / negative 161
C_e binary rows = 369
C_e target = positive 208 / negative 161
p_obs target = positive 480 / negative 0
Q_e target = sufficient 480
```

Shortcut audit:

```text
learned_smoke_allowed = false
subject_object_class_pair p_rel majority accuracy = 0.9973
construction_bucket_hidden p_rel majority accuracy = 0.9106
label_match_status_hidden p_rel majority accuracy = 0.8726
object_label p_rel majority accuracy = 0.8428
```

해석: accept/reject 수량은 충분하지만, current proxy target은 class-pair와 hidden
construction/source strata에 너무 강하게 묶여 있다. 따라서 이 산출물은 target plumbing과
failure diagnosis 용도로 유지하고, learned smoke나 paper-level evidence로 승격하지 않는다.
다음 단계는 class-pair/semantic-stratum repair를 더 시도할지, 아니면 support/contact
visual/mesh audit을 diagnostic-only로 freeze할지 결정하는 path decision이다.

## 2026-06-28 Class-Pair Repair Decision Update

Support/contact visual/mesh audit의 path decision을 진행했고, freeze가 아니라
class-pair controlled repair-first를 선택했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization
selected_path = class_pair_controlled_repair_first
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization
```

현재 480-row proxy label artifact의 control capacity:

```text
class_pair mixed groups = 1
class_pair balanced rows = 2
predicate_x_class_pair mixed groups = 0
predicate_x_class_pair balanced rows = 0
```

즉 기존 label target을 그대로 학습하면 class-pair shortcut을 피할 수 없다. 반면 train full
support/contact queue에는 repair capacity가 충분했다.

```text
source = train_hl_queue.jsonl + train_lh_queue.jsonl
source_rows_after_proxy_filter = 27201
class_pair mixed groups = 313
class_pair balanced raw rows = 13020
predicate_x_class_pair mixed groups = 71
predicate_x_class_pair balanced raw rows = 960
validation/test used = false
```

새로 선택한 repair candidate:

```text
selected_rows = 480
lying on = 160
standing on = 160
supported by = 160
accept_like = 240
reject_like = 240
each predicate x proxy-kind cell = 80
predicate_class_pair_groups = 68
max_scan_rows = 11
max_directed_pair_rows = 1
hard_surface_rows = 252
required_source_file_errors = 0
```

중요한 경계: `repair_proxy_kind`는 sampling-only이며 final target이 아니다. 다음 단계에서
이 480개 후보에 대해 visible packet을 다시 만들고, hidden/source/proxy field를 보지 않고
label fill을 다시 해야 한다. 그 이후 post-lock hidden join과 shortcut audit을 재실행해야
support/contact를 main evidence로 올릴 수 있는지 판단할 수 있다.

## 2026-06-28 Class-Pair Repair Packet Materialization Update

Class-pair controlled repair 후보 480개에 대해 visible packet materialization을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/
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
lying on ready = 160
standing on ready = 160
supported by ready = 160
accept_like ready = 240
reject_like ready = 240
subject_image_rows = 480
object_image_rows = 480
pair_crop_rows = 480
mesh_render_rows = 480
multiview_sheet_rows = 480
```

다음 visible label sheet:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization/visible_review_sheet_with_packets.csv
```

주의: `repair_proxy_kind`는 여전히 hidden sampling-only field이고, label target이 아니다.
또한 `mesh_contact_render.png`는 full contact-surface render가 아니라 evidence availability
card다. 첫 visual sanity check에서 generic `object->box` 같은 row가 시각적으로 약할 수
있음을 확인했으므로, label fill 이후 generic-class subset은 별도 risk로 추적해야 한다.

## 2026-06-28 Class-Pair Repair Label Fill Update

Class-pair repair packet 480개에 대해 visible-field-only Codex proxy label fill을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_proxy_labels_filled_for_class_pair_repair_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion
```

Provenance:

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
accept = 198
reject = 106
abstain = 176
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

해석: class-pair repair label fill은 완료됐지만 아직 learned smoke로 넘어가면 안 된다. 다음
단계에서 post-lock hidden join을 통해 `C_e`, `Q_e`, `p_obs`, `p_rel` target을 만들고,
class-pair shortcut과 generic endpoint shortcut이 실제로 줄었는지 확인해야 한다.

## 2026-06-28 Class-Pair Repair Label Ingestion Update

Class-pair repair labels를 post-lock으로 hidden manifest와 join하고 target/shortcut audit을
완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion/
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
p_rel target = positive 198 / negative 106
C_e binary rows = 304
C_e target = positive 198 / negative 106
p_obs target = positive 480 / negative 0
Q_e target = sufficient 480
```

Shortcut audit:

```text
learned_smoke_allowed = false
predicate_x_subject_object_class_pair_visible p_rel majority accuracy = 1.0000
predicate_class_pair_hidden p_rel majority accuracy = 1.0000
hidden_stratum_hidden p_rel majority accuracy = 1.0000
subject_label p_rel majority accuracy = 0.7007
object_label p_rel majority accuracy = 0.6875
generic_endpoint_visible relation_multiclass majority accuracy = 0.6208
```

해석: class-pair repair는 row-count 문제를 개선했지만, target-identifiability 문제는 아직
해결하지 못했다. 특히 visible-label policy가 `predicate + class-pair`에 강하게 묶여 있어
해당 feature만으로 binary target이 완전히 복원된다. Generic endpoint는 binary `p_rel`에서는
abstain으로 빠지지만, multiclass target에서는 강한 abstain shortcut이다. 따라서 learned smoke는
계속 금지하고, 다음 path decision에서 stricter visual/human relabel, generic-filtered target,
또는 diagnostic freeze 중 하나를 선택해야 한다.

## 2026-06-28 Class-Pair Repair Path Decision Update

Class-pair repair label ingestion 이후 route decision을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion/
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze
```

결론은 support/contact visual/mesh class-pair repair를 diagnostic-only로 freeze하는 것이다.
현재 artifact는 `p_rel`/`C_e` binary row가 `304`개이고 positive/negative가 `198/106`으로
row mass는 충분하지만, target이 독립적이지 않다.

```text
predicate_x_class_pair p_rel majority accuracy = 1.0000
hidden predicate_class_pair p_rel majority accuracy = 1.0000
generic_endpoint_visible relation-multiclass majority accuracy = 0.6208
non-generic filtered predicate_x_class_pair p_rel majority accuracy = 1.0000
```

Route decision:

- Current target learned smoke는 reject.
- Generic-endpoint filtered target은 main evidence로 reject, optional diagnostic only.
- Current artifact를 재사용한 stricter relabel은 reject as continuation.
- Support/contact visual/mesh class-pair repair는 diagnostic negative result로 보존.

현재 H002 evidence boundary는 다음과 같이 유지한다.

```text
relative_vertical = clean train-only C_e anchor
support/contact pose-conditioned target = scoped C_e mechanism evidence
support/contact visual/mesh class-pair repair = diagnostic negative result
calibrated p_rel / p_obs = still blocked
paper-level claim = not allowed
```

## 2026-06-28 Relation-Family Scope Synthesis Update

Support/contact visual/mesh diagnostic freeze 이후 H002의 다음 route를 전체 relation-family
관점으로 재정리했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze/
status = h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready
selected_path = all_relation_family_generalization_scan_with_proximity_first
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_generalization_capacity_scan
selected_first_active_family = proximity
selected_first_active_predicates = close by
```

핵심 판단은 다음과 같다.

- `close by` / proximity를 첫 active probe로 진행한다.
- 하지만 바로 `close by`만 main claim으로 고정하지 않는다.
- 모든 relation family에 대해 같은 target-identifiability gate를 먼저 적용한다.
- 성공 family는 main evidence candidate로, 실패 family는 failure taxonomy와 claim boundary로 보고한다.
- `standing on`, `lying on`, `supported by`는 grouped support/contact 실패와 별개로 individual predicate scan 가능성을 남긴다.

Family priority:

```text
proximity / close by = GT 12300, H002 queue 171324, selected first active probe
support_contact = GT 12600, H002 queue 161498, individual predicate probe possible
relative_vertical = GT 3552, H002 queue 124604, already clean C_e anchor
size_relative = GT 1822, optional quick probe
containment_in = GT 330, optional schema probe
attachment_deferred = GT 8767, visual/mesh-heavy deferred
relative_horizontal = GT 36944, reference-frame ambiguity deferred
identity_symmetry / part_structural = diagnostic/defer
```

Open3DSG train-full에서 실제 관측된 GT predicate는 25개이며, official/mapped inventory에는
train-full count가 0인 `inside`, `in front of`, `mounted on`, `none`까지 포함해 29개를 유지한다.

## 2026-06-28 Relation-Family Capacity Scan Update

All-relation-family scope synthesis 이후 current H002 queue를 기준으로 capacity scan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan/
status = h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready
selected_path = select_proximity_close_by_target_plan_with_all_family_eligibility_table
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_target_plan
```

`close by` 결과:

```text
queue_rows = 171324
HL rows = 0
LH rows = 171324
label_match_status = no_gt_for_pair 130125 / pair_has_other_predicate 31675 / exact_match 9524
geometry_status = satisfied 171324
mixed class-pair groups exact-vs-other = 1292
balanced rows exact-vs-other = 15444
```

해석: `close by`는 수량과 class-pair mixing이 충분해 다음 target plan으로 진행할 가치가
있다. 하지만 현재 queue가 LH-only이므로, no-GT pair를 자동 negative로 쓰는 target은 금지해야
한다. 다음 target plan은 same-distance/similar-distance hard negative, object scale, coverage,
distance-only control을 명시해야 한다.

Support/contact individual predicate capacity:

```text
standing on = queue 50245 / exact 5871 / mixed class-pair groups 96
lying on = queue 60652 / exact 1440 / mixed class-pair groups 75
supported by = queue 50601 / exact 491 / mixed class-pair groups 105
```

따라서 grouped support/contact failure는 각 predicate가 모두 불가능하다는 뜻이 아니다. 다만
현재 순서는 `close by` target plan을 먼저 진행하고, support/contact 개별 predicate probe는 그
이후 또는 parallel diagnostic으로 남긴다.

## 2026-06-28 Proximity Close-By Target Plan Update

`close by` target plan을 실행했고, 다음 단계로 source inventory를 선택했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_target_plan/
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

핵심 판단:

- `close by`는 row mass가 충분하므로 H002 generality probe로 진행할 가치가 있다.
- `exact_match`는 positive-anchor 후보가 될 수 있다.
- `no_gt_for_pair`와 `pair_has_other_predicate`는 negative label이 아니다.
- negative는 scale-aware far pair, same-class-pair far pair, same-distance hard negative처럼
  별도로 구성해야 한다.
- `distance_only` baseline을 반드시 둔다. `close by`는 거리만으로 맞는 쉬운 target이 될 수
  있기 때문이다.
- `p_geom_valid`는 main target이 아니라 H001-style rule baseline 또는 teacher 후보로만 둔다.
- `Z_e` source score/rank는 `C_e`에 넣지 않고, 후속 final decision baseline에서만 사용한다.

다음 source inventory가 확인해야 할 것은 다음이다.

```text
near/far/ambiguous bucket counts by normalized distance and object scale
exact-match positive-anchor capacity
far hard-negative capacity not derived from no-GT status alone
same-class-pair and same-rank-band mixed capacity
same-distance matched subset capacity
G_e/Q_e feature availability
candidate materialization route decision
```

Support/contact는 다음 순서로 보류한다.

```text
standing on individual predicate probe
lying on individual predicate probe
supported by individual predicate probe
```

## 2026-06-28 Proximity Close-By Source Inventory Update

`close by` source inventory를 실행했고, candidate materialization plan으로 넘어갈 수 있다고
판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory/
status = h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan
selected_path = select_close_by_candidate_materialization_plan_with_far_geometry_negatives_and_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

Candidate policy:

```text
near = normalized_distance_xy <= 0.8
far = normalized_distance_xy >= 2.5
accept_anchor = exact_match + satisfied + near
reject_far_geometry = non-exact + unsatisfied + far
abstain_or_audit = uncertain, ambiguous, or non-exact near
```

Candidate counts:

```text
close_by_rows = 185346
accept_anchor = 8682
reject_far_geometry = 6688
abstain_or_audit = 169972
gt_geometry_conflict = 4
near / ambiguous / far = 113280 / 58046 / 14020
```

중요한 점은 `reject_far_geometry`가 `no_gt_for_pair`로 정의되지 않았다는 것이다.
Reject 후보는 far geometry와 unsatisfied geometry status에 의해 정의된다. 다만 reject 후보의
label status는 다음과 같다.

```text
reject_label_status_counts = no_gt_for_pair 6138 / pair_has_other_predicate 550
```

즉 missing GT를 label로 쓰지 않지만, 최종 materialization에서는 이 점이 reviewer risk로 남는다.
따라서 candidate plan에서는 geometry evidence와 hidden label/source axis를 엄격히 분리해야 한다.

Control capacity:

```text
class_pair mixed groups = 529
class_pair balanced rows = 3684
class_pair_rank mixed groups = 550
class_pair_rank balanced rows = 3280
raw_distance_bin mixed groups = 6
raw_distance_bin balanced rows = 804
norm_distance_bin mixed groups = 0
norm_distance_bin balanced rows = 0
scan mixed groups = 520
scan balanced rows = 7656
```

해석:

- class-pair / class-pair+rank control은 materialization에 충분하다.
- raw-distance matched subset은 가능하지만 작으므로 diagnostic subset으로 둔다.
- normalized-distance matched subset은 0이다. 현재 target이 normalized distance로 near/far를
  나누기 때문이다.
- 따라서 `close by`는 반드시 `distance_only`와 `p_geom_valid_rule` baseline을 포함해야 한다.
  이 family의 결과는 “거리 하나로 충분하다”가 아니라, proximity relation에서 distance/scale/overlap
  evidence와 semantic/source/confidence 축을 어떻게 분리하고 통제하는지가 핵심이다.

Available current `G_e`:

```text
distance_3d, distance_xy, normalized_distance_3d, normalized_distance_xy,
projected_iou_xy, projected_subject/object_overlap_ratio,
center_delta_z, normalized_center_delta_z, subject/object top-bottom z
```

Missing/deferred evidence:

```text
subject_object_full_xyz_extent = source adapter needed
multi_view_visibility = audit extension only, not current input
```

## 2026-06-28 Proximity Close-By Candidate Materialization Plan Update

`close by` candidate materialization plan을 작성했고, 실제 candidate materialization으로 넘어갈
수 있다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready
selected_path = materialize_close_by_controlled_candidates_with_distance_controls
validation_errors = 0
warnings = 2
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

Planned quotas:

```text
planned_total_rows = 1284
primary_binary_rows = 800
  accept_anchor = 400
  reject_far_geometry = 400
abstain_qe_rows = 240
  near_nonexact_satisfied = 120
  ambiguous_distance = 80
  geometry_uncertain = 40
raw_distance_diagnostic_rows = 240
  accept = 120
  reject = 120
gt_geometry_conflict_audit_rows = 4
```

Sampling caps:

```text
max_rows_per_scan = 18
max_rows_per_class_pair = 48
max_rows_per_class_pair_rank = 24
max_rows_per_directed_pair = 2
max_rows_per_raw_distance_bin = 80
```

필수 model/control views:

```text
T_only
Z_only
G_only
distance_only
p_geom_valid_rule
T_plus_G_compatibility
T_plus_G_plus_Q
class_pair_only
source_only_Z
shuffled_geometry
wrong_pair_geometry
raw_distance_diagnostic_subset
```

Warnings:

```text
normalized_distance_matched_capacity_zero
reject_pool_contains_no_gt_rows
```

해석:

- 모든 quota/cap gate는 통과했다.
- 다만 `close by`는 normalized-distance separation으로 쉽게 풀릴 수 있으므로, `distance_only`
  baseline 없이 H002 claim으로 쓰면 안 된다.
- `reject_far_geometry`는 geometry-defined target이지만 `no_gt_for_pair` status가 많이 포함되므로,
  no-GT status와 candidate bucket은 hidden control로만 보관한다.
- 다음 candidate materialization 이후 schema/shortcut audit을 통과해야 learned smoke로 갈 수 있다.

## 2026-06-28 Proximity Close-By Candidate Materialization Update

`close by` candidate materialization을 실행했고 계획한 row를 모두 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization/
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

Quota/cap/schema precheck:

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

Model-safe view에서 `label_match_status`, `geometry_status`, `candidate_bucket`,
`distance_bucket`, identity fields, and `p_geom_valid`는 제거했고 hidden manifest에만 보관했다.

## 2026-06-28 Proximity Close-By Schema Shortcut Audit Update

`close by` schema/shortcut audit를 실행했고, learned smoke를 block했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut
validation_errors = 0
critical_blockers = 5
learned_smoke_allowed = false
main_claim_verdict = blocked_for_close_by_current_target
next_todo = compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

Critical blockers:

```text
primary_binary:normalized_distance_xy = acc 1.000000 / AUROC 1.000000
primary_binary:normalized_distance_3d = acc 1.000000 / AUROC 1.000000
primary_binary:distance_xy = acc 0.992500 / AUROC 0.999556
primary_binary:distance_3d = acc 0.987500 / AUROC 0.998975
primary_binary:p_geom_valid_rule = acc 0.991250 / AUROC 0.999594
```

Raw-distance diagnostic subset도 normalized distance로 풀렸다.

```text
raw_distance_diagnostic:normalized_distance_xy = acc 1.000000 / AUROC 1.000000
raw_distance_diagnostic:normalized_distance_3d = acc 1.000000 / AUROC 1.000000
raw_distance_diagnostic:p_geom_valid_rule = acc 0.995833 / AUROC 0.994097
```

해석:

- `close by` materialization 자체는 성공했다.
- Schema leakage는 없다.
- 하지만 현재 target은 distance/rule geometry baseline이 이미 거의 완전히 푼다.
- 따라서 현재 `close by` target으로 learned smoke를 돌려도 H002의 `T_e-G_e compatibility`
  claim을 증명하지 못한다.
- `close by`는 현재 main claim이 아니라 proximity-family diagnostic/generality evidence다.

## 2026-06-28 Proximity Close-By Path Decision Update

`close by` path decision을 실행했고, current target을 diagnostic/generality evidence로
freeze했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe
selected_path = freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

결론:

- current `close by` target은 materialization과 schema-cleanliness 측면에서는 성공했다.
- 하지만 `normalized_distance_xy/3d`, raw distance, and `p_geom_valid_rule`가 target을 거의
  완전히 풀기 때문에, learned smoke는 H002의 factor separation을 증명하지 못한다.
- `close by`는 relation-family generality/failure taxonomy evidence로 유지한다.
- 다음은 grouped support/contact를 재사용하지 않고, `standing on`, `lying on`, `supported by`
  개별 predicate probe plan으로 간다.

Support/contact individual priority:

```text
1. standing on = primary probe, queue 50245, exact 5871, mixed class-pair groups 96
2. lying on = secondary pose-conditioned probe, queue 60652, exact 1440, mixed class-pair groups 75
3. supported by = diagnostic superordinate probe, queue 50601, exact 491, mixed class-pair groups 105
```

## 2026-06-28 Support/Contact Individual Predicate Probe Plan Update

`support/contact` individual predicate probe plan을 실행했고, source inventory로 넘어갈 수
있다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory
selected_path = plan_individual_support_contact_source_inventory_standing_primary_lying_secondary_supported_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_source_inventory
```

Predicate별 역할:

```text
standing on = primary individual probe
lying on = secondary pose-conditioned probe
supported by = diagnostic superordinate probe
```

핵심 판단:

- grouped support/contact target은 main learned target으로 재사용하지 않는다.
- `lying on` / `standing on` pose-conditioned result는 `C_e` mechanism prior로만 사용한다.
- `supported by`는 `standing on`의 negative가 아니라 superordinate diagnostic으로 둔다.
- 다음 source inventory에서 class-pair, rank/source, hard-surface, no-GT, same-G anchor control을
  통과해야 materialization과 learned smoke로 갈 수 있다.

## 2026-06-28 Support/Contact Individual Predicate Source Inventory Update

`support/contact` individual predicate source inventory를 실행했고, `standing on`과 `lying on`은
candidate materialization plan으로 진행 가능하다고 판단했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan
selected_path = plan_candidate_materialization_for_standing_lying_individual_predicate_cells_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan
```

Relation type별 결과:

```text
standing on = primary, rows 50245, class-pair balanced rows 382, mixed groups 13
lying on = secondary, rows 60652, class-pair balanced rows 414, mixed groups 13
supported by = diagnostic, rows 50601, class-pair balanced rows 164, mixed groups 45
```

해석:

- 현재는 `support/contact`를 하나로 보지 않고 relation type별로 따로 본다.
- `standing on`과 `lying on`은 candidate plan으로 진행 가능하다.
- `supported by`는 수량은 있지만 superordinate relation이므로 main binary target이 아니라 diagnostic으로 둔다.
- hard-surface share가 약 69-71%로 높기 때문에 다음 materialization plan에서 반드시 cap/stratify해야 한다.

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

Planned quota:

```text
standing on = 320 rows, 160 clear_accept / 160 hard_reject_lying_like
lying on = 320 rows, 160 clear_accept / 160 hard_reject_standing_like
supported by = 160 diagnostic rows
total = 800 rows
```

해석:

- `standing on`과 `lying on`은 `T_e`와 predicate-independent `G_e`의 compatibility를
  검증할 수 있는 main candidate로 남긴다.
- `supported by`는 `standing on`/`lying on`과 의미적으로 겹치는 superordinate relation이므로
  main binary target이 아니라 diagnostic/Q_e evidence로 둔다.
- 이 단계는 plan만 생성했으며 아직 row materialization, label fill, learned smoke,
  validation/test 사용은 없다.

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

Rows:

```text
total_rows = 800
main_compatibility_rows = 640
supported_by_diagnostic_rows = 160
standing on = 160 / 160
lying on = 160 / 160
supported by = 40 / 40 / 80 diagnostic
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

해석:

- planned quota는 채웠지만, cap relaxation이 필요했다.
- 따라서 이 artifact는 바로 learned smoke로 가지 않고 schema/shortcut audit로 넘어간다.
- 다음 audit에서 class-pair, rank/source, hard-surface, source/GT hidden field shortcut이 강하면
  이 target은 diagnostic으로 내려야 한다.

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

Audit counts:

```text
main_binary_rows = 640
diagnostic_rows = 160
sanitized_rows = 640
schema_leakage_hits = 0
allowed_high_risk_probes = 0
hidden_high_risk_probes = 2
```

해석:

- model-safe `T_e`와 single `G_e` probes는 high-risk shortcut을 만들지 않았다.
- hidden `label_match_status`와 `candidate_role`은 accuracy `1.0`으로 label을 재구성하지만,
  model-safe view에는 없다.
- cap relaxation으로 우려했던 class-pair/rank/hard-surface probes도 high-risk가 아니었다.
- 다음 단계는 640-row sanitized view에 대한 smoke plan 작성이다.

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

해석:

- `smoke_ready_view.jsonl`에는 model feature로 `T_e`, `G_e_mesh_pose_contact`, `Q_e`만 남겼다.
- raw `scan_id`는 feature로 노출하지 않고 hash된 `cv_group_id` split metadata로만 사용한다.
- H001 `p_geom_valid`, source score/rank, label-match/candidate-role construction field는 제외했다.
- runner 결과에서 `M2_geometry_only_G`가 `M4/M5`와 거의 같으면 support/contact individual
  predicate result는 geometry-dominance diagnostic으로 낮춘다.

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

Main metrics:

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

- shortcut controls와 shuffled/wrong controls는 통과했다.
- geometry-only dominance는 아니다.
- `M4`는 `T_e`, `G_e`, plain `T+G`보다 낫다.
- 그러나 primary AUROC `0.6316`은 planned gate `0.70`보다 낮으므로 support/contact
  individual predicate branch는 아직 main evidence가 아니다.
- `Q_e`는 모든 row가 동일한 evidence profile이어서 효과가 없었다.
- 다음 단계는 error/failure analysis이며, semseg OBB만으로 충분하지 않은지, label이
  noisy한지, point/multiview evidence가 필요한지 분리해야 한다.

## 2026-06-29 Support/Contact Individual Predicate Failure Analysis Update

`support/contact` individual predicate failure analysis를 실행했고, current semseg OBB-only
branch는 diagnostic으로 freeze한 뒤 point/multiview evidence plan으로 진행하기로 했다.

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

판단:

- support/contact individual predicate result는 shortcut collapse가 아니다.
- geometry-only dominance도 아니다.
- 다만 OBB pose/contact evidence만으로는 `standing on`/`lying on` fine-grained
  compatibility를 main evidence 수준으로 분리하지 못한다.
- `family_match` negative는 물리적으로 불가능한 relation이라기보다 subtype mismatch일
  가능성이 있으므로 label tightening도 함께 필요하다.
- stronger combiner보다 point/multiview evidence와 label review가 먼저다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Evidence Plan Update

Point/multiview evidence plan을 작성했고, current branch는 source inventory 단계로
넘어간다. 이 단계는 model capacity 확장이 아니라 evidence axis 재정의다.

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

판단:

- 현재 800개 candidate row는 point/mesh/sequence asset readiness가 모두 충족된다.
- `G_e`는 point/mesh/contact/pose evidence로 확장하되 predicate/source/label field를 넣지 않는다.
- `Q_e`는 point density, mesh completeness, contact patch support, co-visible view count,
  crop quality, occlusion/conflict/missing status로 별도 materialization한다.
- multiview는 audit과 `Q_e` 확인에 먼저 쓰고, learned visual input은 wrong-view/shuffled-view
  control이 정의된 뒤에만 고려한다.
- `supported by`는 main binary target이 아니라 diagnostic-only로 유지한다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Source Inventory Update

Point/multiview source inventory를 실행했고, current 800 candidate rows가 materialization
planning으로 넘어갈 수 있음을 확인했다.

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

`Q_e` state plan:

```text
limited = 419
sufficient = 373
uncertain_or_low_observability = 8
```

주요 reason:

```text
low_semseg_segment_count = 345
low_crop_score = 98
few_cropped_instance_views = 60
```

판단:

- OBB-only branch의 `Q_e` constant 문제는 point/multiview source feature로 해결 가능하다.
- 아직 learned smoke나 visual model input을 허용하지 않는다.
- 다음 단계는 `G_e` point/mesh/contact/pose와 `Q_e` observability를 분리해 materialize하는
  계획을 고정하는 것이다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Materialization Plan Update

Materialization plan을 작성했고, 다음 단계는 실제 `G_e`/`Q_e` separated artifact를
만드는 것이다.

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

Required controls:

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

판단:

- Materialization은 learned smoke가 아니다.
- `model_safe_view.jsonl`에는 factor-separated safe fields만 들어가야 한다.
- source paths, scan ids, candidate role, label-match status, GT ids, H001 `p_geom_valid`,
  source score/rank는 `C_e` input에서 제외한다.
- `supported by`는 diagnostic-only로 유지한다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Materialization Update

`support/contact` individual predicate point/multiview materialization을 실행했고, 다음
schema/shortcut audit로 넘어갈 수 있는 artifact를 만들었다.

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

생성한 파일:

```text
model_safe_view.jsonl = 800 rows
source_manifest.jsonl = 800 rows
visual_audit_manifest.jsonl = 800 rows
control_manifest.jsonl = 800 rows
feature_stats.json = finite/range audit
validation_errors.jsonl = 0 rows
```

판단:

- point-level geometry를 붙였다는 것만으로 support/contact main claim이 가능해진 것은 아니다.
- 다음 schema/shortcut audit에서 predicate/class-pair/source/rank/raw geometry/`Q_e` shortcut을
  다시 확인해야 한다.
- multiview는 아직 learned visual feature가 아니라 audit/observability evidence다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Schema Shortcut Audit Update

Point/multiview materialized dataset의 schema/shortcut audit를 실행했다.

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

Top allowed probe:

```text
model_T_predicate_x_class_pair acc = 0.684375, risk = low
```

Hidden high-risk probes:

```text
hidden_candidate_role acc = 1.0
hidden_label_match_status acc = 1.0
hidden_machine_hint acc = 1.0
```

판단:

- 현재 point/contact/observability model-safe view는 smoke plan으로 넘어갈 수 있다.
- hidden construction fields는 여전히 완벽 shortcut이므로 source manifest에만 둔다.
- 다음 단계는 `OBB-only`, `point-only`, `contact-only`, `point+contact`, `T+G`, `T+G+Q`
  model view와 shuffled/wrong-pair controls를 고정하는 smoke plan이다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Smoke Plan Update

Point/multiview smoke plan을 작성했다. 아직 learned smoke를 실행하지 않았고, runner가
읽을 train-only grouped-CV input과 비교군만 고정했다.

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

Planned main model:

```text
M8_TG_point_contact_interaction
```

Planned comparisons:

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
- runner에서 `M8`이 `M5` geometry-only와 거의 같으면 compatibility learning이 아니라
  geometry-dominance diagnostic으로 해석한다.
- `M8`이 기존 `M6` OBB T+G를 명확히 넘지 못하면 point/contact evidence expansion의
  의의도 약해진다.

## 2026-06-29 Support/Contact Individual Predicate Point/Multiview Smoke Runner Update

Point/multiview runner를 실행했다. 결과는 near-threshold diagnostic-only다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_diagnostic_only_failed_controls
rows = 640
positive / negative = 320 / 320
predicate_counts = lying on 320 / standing on 320
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis
```

Main AUROC:

```text
M1_semantic_only_T = 0.442480
M2_obb_geometry_only = 0.464077
M3_point_pose_only = 0.494673
M4_contact_patch_only = 0.465952
M5_point_contact_geometry = 0.470249
M6_TG_obb_concat = 0.430010
M7_TG_point_contact_concat = 0.434658
M8_TG_point_contact_interaction = 0.699375
M9_TGQ_factorized_observability = 0.694619
```

Controls:

```text
S1_predicate_label_shortcut = 0.422490
S2_class_pair_shortcut = 0.472783
S3_quality_only_shortcut = 0.481484
C1_wrong_T_same_G = 0.273125
C2_shuffled_G_global = 0.506240
C3_shuffled_G_within_predicate = 0.463857
C4_shuffled_Q = 0.699297
```

판단:

- 기존 OBB-only support/contact runner보다 훨씬 강하다. point-derived pose/contact
  evidence 자체는 geometry-only로 거의 chance 수준이지만, predicate-conditioned interaction을
  만들면 AUROC가 `0.699375`까지 오른다.
- 사전에 고정한 primary gate가 `0.70`이므로 통과로 처리하지 않는다.
- `standing on` slice는 `0.707930`으로 gate를 넘고, `lying on` slice는 `0.692578`로
  aggregate gate를 끌어내린다.
- 따라서 다음 작업은 모델 결합 방식 튜닝이 아니라 failure analysis다. `lying on`의
  pose ambiguity, class-pair 분포, point crop quality, feature proxy 설계를 먼저 확인해야 한다.

## 2026-06-29 Support/Contact Point/Multiview Failure Analysis Update

Point/multiview failure analysis를 실행했고, internal gate와 paper-facing claim을 분리하는
방향을 선택했다.

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

Slice findings:

```text
lying on AUROC = 0.692578, error_rate = 0.362500
standing on AUROC = 0.707930, error_rate = 0.346875
Q_e sufficient AUROC = 0.772590
Q_e limited AUROC = 0.638494
```

판단:

- 내부적으로는 frozen `0.70` gate를 못 넘겼으므로 near-threshold diagnostic으로 둔다.
- 논문에서는 support/contact를 `fully solved`로 쓰지 않고 `compatibility-route evidence`로 쓴다.
- `Q_e`는 truth signal이 아니라 p_obs/observability axis로 해석한다.
- 어려운 slice는 generic/small/thin floor-object class-pair(`item->floor`, `shoes->floor`,
  `picture->floor`, `object->floor`)에 집중된다.

## 2026-06-29 Support/Contact Point/Multiview Result Review And Claim Position Update

Support/contact point/multiview branch의 논문 내 역할을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis
selected_path = paper_position_support_contact_compatibility_route_evidence_with_caveat_keep_internal_near_threshold
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview
```

고정한 표현:

```text
support/contact = main compatibility-route evidence with caveat
support/contact != fully solved relation family
Q_e = observability / p_obs axis
Q_e != relation truth
```

Route table:

```text
relative_vertical: main clean compatibility mechanism
support_contact: main challenging compatibility route with caveat
supported by: diagnostic / superordinate support taxonomy
close by: geometry-easy diagnostic/generality control
attachment_like: observability-heavy future route
relative_horizontal: reference-frame deferred
```

판단:

- 이 단계 이후 바로 combiner를 키우는 것은 보류한다.
- 다음은 multi-family claim synthesis다. 여기서 H002의 최종 paper-framework skeleton,
  relation route table, claim boundary, reviewer-risk wording을 하나로 묶는다.

## 2026-06-29 Multi-Family Claim Synthesis After Support/Contact Point/Multiview Update

Multi-family claim synthesis를 실행했고, H002의 현재 paper-framework skeleton을 다음으로
고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready
selected_path = freeze_relation_aware_compatibility_routing_claim_select_ablation_table_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis
```

Short claim:

```text
relation-aware predicate-geometry compatibility routing
```

Route table:

```text
relative_vertical = main clean compatibility mechanism
support_contact = main challenging compatibility route with caveat
supported by = diagnostic / superordinate support taxonomy
close by = geometry-easy diagnostic/generality control
attachment_like = observability-heavy future route
relative_horizontal = reference-frame deferred
```

이 결론은 broad relation reliability claim이 아니다. 현재 artifact가 허용하는 것은
train-only mechanism claim이다. `relative_vertical`은 clean `C_e` evidence이고,
`support_contact`는 near-threshold지만 baseline/control 대비 predicate-geometry interaction이
필요하다는 route evidence다. `close by`는 current target에서 geometry-only dominance가 너무 강해
main compatibility proof가 아니라 geometry-easy diagnostic/generality evidence로 둔다.

Blocked claims:

```text
paper-level performance
held-out/test relation reliability
all relation-family generality
support/contact fully solved
Q_e as relation truth
final calibrated p_rel/p_obs results
```

따라서 다음 TODO는 새 model run이 아니라, 현재 claim skeleton을 main table, ablation,
control, reviewer-risk wording으로 변환하는 ablation/table plan이다.

## 2026-06-29 Ablation And Table Plan After Multi-Family Synthesis Update

Ablation/table plan을 실행했고, H002를 paper-facing 실험으로 승격하기 전에 필요한 표,
ablation, control, promotion gate를 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_ready
selected_path = freeze_candidate_ablation_contract_select_relation_family_coverage_gap_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan
```

Candidate table/ablation contract:

```text
T1 Predicate-Geometry Compatibility Mechanism
T2 Relation-Aware Evidence Routing Taxonomy
T3 Geometry-Easy and Observability-Heavy Diagnostics
T4 Claim Boundary and Reviewer Risk
```

핵심 ablation:

```text
T_e only
Z_e only
G_e only
T_e + G_e plain concat
C_e interaction(T_e, G_e)
C_e + Q_e selective decision
C_e + Q_e + Z_e final p_rel
fixed fusion without relation-aware route
```

필수 control:

```text
wrong-T same-G
shuffled-G global
shuffled-G within predicate/family
class-pair only
source/rank only
distance or p_geom_valid only
Q_e shuffled or Q_e only
scan/endpoint leakage
```

Promotion gate:

- frozen schema
- Docker reproduction
- grouped held-out evaluation
- core `C_e` ablation with CI/bootstrap
- counterfactual controls
- route taxonomy boundary
- `Q_e`/`p_obs` separation
- claim wording lock

따라서 다음 작업은 H002를 실제 paper-level evidence로 올릴 Docker protocol이 아니라,
남은 relation-family coverage/gap audit이다. 이 단계 전까지는 H002 결과를 최종 논문 본문
성능표로 쓰지 않는다.

남은 주요 gap:

```text
relative_horizontal = left, right, front, behind, in front of
attachment_deferred = attached to, hanging on, mounted on, connected to
containment_in = inside, standing in, lying in, hanging in
size_relative = bigger than, smaller than
part_structural = part of, belonging to, build in, cover, leaning against
identity_symmetry = same as, same symmetry as
```

## 2026-06-29 Relation-Family Coverage Gap Audit After Ablation/Table Plan Update

Relation-family coverage/gap audit을 실행했고, 현재 H002 queue가 전체 relation type을 커버하지
않는다는 점을 명시했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan/
status = h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready
selected_path = select_size_relative_schema_probe_keep_horizontal_reference_frame_protocol_second
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit
```

Coverage summary:

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

판단:

- 최종 main table은 아직 만들면 안 된다.
- `size_relative`는 새 physical relation family를 추가하는 가장 낮은 비용의 probe다.
- `relative_horizontal`은 GT mass가 가장 크지만 reference-frame protocol 없이는 label 의미가 흔들린다.
- `attachment_deferred`는 중요하지만 visual/mesh observability source가 먼저 필요하다.
- `part_structural`과 `identity_symmetry`는 현재 H002 physical compatibility main claim과는 분리한다.

## 2026-06-29 Size-Relative Schema Probe Plan After Coverage Gap Audit Update

`size_relative` family에 대한 schema/source-adapter probe plan을 작성했다.

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

Schema:

```text
T_e = predicate text/label and optional object class text
G_e_size = OBB/extent/volume/area/height ratios, excluding predicate and source score
Q_e_size = OBB availability and ambiguous-size-band evidence
C_e = compatibility(T_e, G_e_size), excluding Z_e
```

Main control:

```text
same subject/object geometry
row 1: predicate = bigger than
row 2: predicate = smaller than
```

판단:

- `size_relative`는 새 physical relation family를 추가하는 낮은 비용의 probe다.
- 하지만 단순 size threshold verifier로 끝나면 H002 main compatibility claim이 약해진다.
- 따라서 source inventory는 same-G predicate-flip capacity와 geometry-only shortcut risk를 먼저 측정해야 한다.
- `no-GT` pair는 negative로 쓰지 않는다.
- `Z_e`는 첫 `C_e` probe에서 제외한다.

## 2026-06-29 Size-Relative Source Inventory After Schema Probe Plan Update

`size_relative` family의 source inventory를 실행했다. 이 단계는 train-side 관계 source와
3RScan semseg OBB를 join해 materialization 가능성을 측정한 것이며, model row materialization과
learned smoke는 수행하지 않았다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan/
status = h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready
selected_path = size_relative_inventory_ready_for_candidate_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory
```

Source counts:

```text
train_relationship_source = local_dataset/3DSSG_subset/relationships_train.json
train anchors = 1846
bigger than / smaller than = 923 / 923
unique_directed_pair_predicate = 1846
semseg files requested/found = 401 / 401
pair OBB join = 1846 / 1846
```

OBB size-ratio diagnosis:

```text
volume compatible = 1760
ambiguous = 50
opposes = 36
strong_ge_1.50 = 1680
medium_1.25_1.50 = 78
weak_1.15_1.25 = 38
ambiguous_lt_1.15 = 50
```

Same-G predicate-flip capacity:

```text
strict compatible unique groups = 1728
strict same-G predicate-flip rows = 3456
by predicate = bigger than 864 / smaller than 864
structural pair fraction = 0.0
```

판단:

- `size_relative`는 다음 materialization-plan 단계로 진행할 수 있다.
- 다만 이 family는 size ratio가 강하기 때문에 geometry-only score가 잘 되는 결과만으로는
  H002 novelty가 약하다.
- 따라서 다음 plan은 반드시 same-G predicate flip을 사용해야 한다. 같은 `G_e_size`에서
  `bigger than`과 `smaller than` row의 target이 바뀌어야 하며, geometry-only view는 이
  target을 풀 수 없어야 한다.
- class-pair는 대부분 same-class pair에 집중된다. 이 자체는 size relation의 자연스러운
  annotation 구조이지만, 다음 schema에서는 class-pair/source/GT/construction field를 model-safe
  view에서 제외하고 class-pair cap을 둬야 한다.

## 2026-06-29 Size-Relative Candidate Materialization Plan After Source Inventory Update

Source inventory 이후 실제 row를 생성하기 전 materialization plan을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_size_relative_same_g_predicate_flip_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_candidate_materialization_after_plan
```

Primary plan:

```text
primary groups = 1200
primary rows = 2400
positive / negative = 1200 / 1200
subject_bigger / subject_smaller groups = 600 / 600
bigger than / smaller than rows = 1200 / 1200
```

Diagnostic rows:

```text
ambiguous size rows = 100
GT-geometry conflict audit rows = 72
```

Schema decision:

- main compatibility view는 `T_e.predicate_text`와 continuous `G_e_size` log-ratio만 허용한다.
- class label, class-pair, source/GT/construction fields, discretized geometry direction,
  `volume_ratio_band`, scan/object id, `Z_e`는 첫 main view에서 막는다.
- ambiguous size rows는 `Q_e`/abstain diagnostic으로만 쓰고 primary binary `C_e`에는 넣지 않는다.
- GT와 volume direction이 충돌하는 row는 annotation/noise audit로만 둔다.

Control decision:

- geometry-only는 same-G paired target에서 near-chance여야 한다.
- semantic-only도 near-chance여야 한다.
- `T_e x G_e_size` interaction이 main signal이어야 한다.
- wrong-T와 shuffled-G control이 collapse해야 한다.

판단:

`size_relative`는 row capacity가 충분하지만, 단순 size threshold로 풀면 H002 contribution이
약해진다. 따라서 다음 materialization은 same-G predicate flip 구조를 반드시 유지해야 한다.

## 2026-06-29 Size-Relative Candidate Materialization After Plan Update

Frozen plan에 따라 `size_relative` candidate rows를 materialize했다. 이 단계는 row 생성과
schema precheck까지만 수행했고, learned smoke는 실행하지 않았다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/
status = h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = size_relative_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization
```

Generated rows:

```text
candidate_rows = 2572
primary_compatibility_rows = 2400
diagnostic_ambiguous_size_rows = 100
audit_gt_geometry_conflict_rows = 72
model_safe_main_rows = 2400
model_safe_qe_rows = 2572
hidden_rows = 2572
group_rows = 1286
```

Primary balance:

```text
C_e positive / negative = 1200 / 1200
subject_bigger / subject_smaller groups = 600 / 600
bigger than / smaller than rows = 1286 / 1286 overall
```

Schema precheck:

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1200
max class-pair groups = 232 / 240
max class-pair-direction groups = 116 / 120
max scan groups = 13 / 24
```

판단:

- Materialization은 정상 완료됐다.
- Primary row들은 같은 `G_e_size`를 공유하는 `bigger than` / `smaller than` paired rows다.
- Model-safe main view에는 predicate text와 continuous size-ratio geometry만 들어간다.
- Class/source/GT/construction/discretized direction fields는 hidden manifest로 분리했다.
- 아직 schema/shortcut audit 전이므로 이 결과를 size-relative result로 주장하면 안 된다.

## 2026-06-29 Size-Relative Schema Shortcut Audit After Materialization Update

`size_relative` materialized rows의 schema/shortcut audit을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/
status = h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan
selected_path = size_relative_smoke_ready_view_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit
```

Audit summary:

```text
primary_rows = 2400
C_e positive / negative = 1200 / 1200
feature_path_violations = 0
group_integrity_errors = 0
smoke_ready_rows = 2400
```

Shortcut probes:

```text
T_predicate_label_only = 0.500
G_exact_tuple_only = 0.500
single G_e_size ratio probes = 0.500 AUROC
TG_exact_interaction = 1.000
```

Hidden probes:

```text
class_pair/source/anchor/direction/scan/volume_band = 0.500
original_gt_anchor_flag = 1.000
direction_x_candidate_predicate = 1.000
```

Interpretation:

- 단일 predicate 또는 단일 geometry evidence로는 compatibility target이 풀리지 않는다.
- `T_e x G_e_size` interaction만 target을 복원한다.
- high hidden probes는 construction metadata이며 model-safe feature가 아니다.
- 다음 단계는 learned smoke를 바로 실행하는 것이 아니라, smoke-ready view와 control protocol을
  고정하는 plan 단계다.

## 2026-06-29 Size-Relative Sanitized View Smoke Plan After Schema Audit Update

`size_relative` learned smoke를 위한 runner-ready view와 comparison contract를 고정했다.
모델 학습은 아직 실행하지 않았다.

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

Frozen gates:

```text
single-factor baselines <= 0.60 AUROC
M4_TG_size_interaction >= 0.95 AUROC
M4 gain over best single factor >= 0.30 AUROC
wrong-T / shuffled-G controls must degrade
paired margin pass rate >= 0.90
```

Interpretation:

- `size_relative` smoke는 단순 size geometry rule이 아니라 `T_e x G_e_size`
  compatibility를 검증한다.
- 같은 geometry evidence가 `bigger than`과 `smaller than`에서 반대로 해석되어야 한다.
- 다음 단계는 train-only grouped-CV smoke runner다.

## 2026-06-29 Size-Relative Sanitized View Smoke Runner After Plan Update

`size_relative` learned smoke runner를 실행했고, control gate를 통과했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan/
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls
overall = size_relative_smoke_passed_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_smoke_result_review_after_runner
```

Metrics:

```text
M1_semantic_only_T = 0.4707 AUROC
M2_geometry_only_G_size = 0.5000 AUROC
M3_TG_concat_no_interaction = 0.4707 AUROC
M4_TG_size_interaction = 0.9999 AUROC
C1_wrong_T_same_G = 0.00009 AUROC
C2_shuffled_G_global = 0.4931 AUROC
C3_shuffled_G_within_predicate = 0.4767 AUROC
C4_sign_flipped_G_control = 0.00008 AUROC
paired positive-margin fraction = 0.9933
```

Interpretation:

- 단일 semantic factor와 단일 geometry factor는 모두 target을 풀지 못했다.
- plain concat도 실패했으므로 `T_e x G_e_size` interaction의 필요성이 드러난다.
- wrong-T, shuffled-G, sign-flip controls가 모두 의도대로 붕괴했다.
- 이 결과는 `size_relative`를 H002의 compatibility-route evidence로 올릴 수 있음을
  보여준다.
- 단, calibration evidence는 아니다. `M4`는 ranking/decision은 강하지만 ECE가 높다.

## 2026-06-29 Size-Relative Smoke Result Review After Runner Update

`size_relative` smoke 통과 결과의 claim 위치와 paper-promotion boundary를 리뷰했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_size_relative_as_main_compatibility_route_evidence_keep_calibration_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative
```

Decision:

- `size_relative`는 H002의 `main compatibility-route mechanism evidence`로 둔다.
- 핵심은 size geometry가 단독으로 충분하다는 것이 아니라, 같은 `G_e_size`가
  `bigger than`과 `smaller than` predicate에 따라 반대로 해석되어야 한다는 점이다.
- `T_e` only `0.4707`, `G_e_size` only `0.5000`, plain concat `0.4707`,
  `T_e x G_e_size` `0.9999` AUROC 패턴이 이 결론을 뒷받침한다.
- wrong-T, shuffled-G, sign-flipped-G control이 모두 무너져 단일 factor shortcut이 아니라
  predicate-conditioned geometry signal임을 확인했다.
- 단, ECE가 `0.4950`이므로 calibrated `p_rel`/`p_obs` claim은 아직 불가하다.
- 이 결과는 train-only hypothesis-stage evidence이며 paper-level result가 아니다.

## 2026-06-29 Multi-Family Claim Synthesis After Size-Relative Update

`size_relative` result review를 H002 relation-aware evidence-routing synthesis에 통합했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_size_relative_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis
```

Updated evidence rows:

```text
relative_vertical = primary 1.0000, G-only 0.5000, concat 0.4463
size_relative = primary 0.9999, G-only 0.5000, concat 0.4707
support_contact = primary 0.6994, G-only 0.4702, concat 0.4347
proximity = geometry-easy diagnostic/control
attachment_like = observability-heavy future/diagnostic
```

판단:

- `size_relative`를 포함해도 H002는 geometry-only framework가 아니다.
- clean route 두 개(`relative_vertical`, `size_relative`)는 mechanism evidence이고,
  `support_contact`는 challenging route evidence다.
- `close by`는 geometry-only로 풀리는 control family로 남긴다.
- 다음 작업은 기존 ablation/table plan을 `size_relative` 포함 버전으로 갱신하는 것이다.

## 2026-06-29 Ablation And Table Plan Update After Size-Relative Synthesis

`size_relative`를 반영한 table/ablation/control/promotion gate 계약을 갱신했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis_ready
selected_path = freeze_size_relative_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan
```

Updated main mechanism table:

```text
T1 rows = relative_vertical / size_relative / support_contact
relative_vertical signal = 1.0000
size_relative signal = 0.9999
support_contact signal = 0.6994
```

Required controls:

```text
wrong predicate same geometry
shuffled geometry global
shuffled geometry within predicate/family
sign-flipped geometry where meaningful
class-pair only
source/rank only
distance or p_geom_valid only
Q_e-only / shuffled-Q
scan and endpoint leakage
```

Promotion gates:

- schema freeze
- route coverage sufficiency review
- Docker reproduction
- grouped held-out evaluation
- core `C_e` ablation
- counterfactual controls
- calibration boundary
- `Q_e`/`p_obs` separation
- claim wording lock

판단:

- 현재 표 구조는 H002의 방법론 claim을 정리하기에는 충분히 명확해졌다.
- 하지만 final paper route로 가기 전, 현재 relation coverage가 충분한지 판단해야 한다.
- 특히 reviewer가 “clean route가 너무 rule-like하다” 또는 “support/contact가 약하다”고
  공격할 수 있으므로, 다음 단계에서 relation-family coverage sufficiency를 평가해야 한다.

## 2026-06-29 Route Coverage Sufficiency Review After Size-Relative Table Plan

현재 table plan이 H002 promotion planning으로 넘어가기에 충분한지 검토했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready
selected_path = coverage_not_sufficient_add_relation_family_sweep_before_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review
```

결론:

- 현재 coverage는 promotion planning에 충분하지 않다.
- `relative_vertical`, `size_relative`, `support_contact`는 현재 main mechanism rows로
  유지하되, 여기서 멈추면 reviewer가 cherry-picking으로 공격할 가능성이 높다.
- 따라서 다른 relation family를 추가로 확인하고, 그 결과를 보고 최종 claim boundary를
  정한다.

Expansion queue:

```text
1. relative_horizontal
   - left / right / front / behind / in front of
   - GT mass가 크지만 reference-frame ambiguity가 있으므로 protocol 먼저 필요.

2. containment_in
   - standing in / lying in / hanging in / inside
   - low count이지만 geometry-checkable containment family라 schema probe 가치가 있음.

3. attachment_deferred
   - attached to / hanging on / connected to / mounted on
   - visual/mesh/Q_e observability-heavy route.

4. part_structural
   - build in / leaning against / belonging to / part of / cover
   - geometry compatibility main claim보다 structural/semantic boundary 확인용.

5. identity_symmetry
   - same as / same symmetry as
   - physical compatibility claim에서 제외할 out-of-scope 근거 기록용.
```

주의:

- 모든 relation family를 하나의 learned model에 바로 넣지 않는다.
- 먼저 family별 schema/source adapter/target-identifiability를 확인한다.
- 그 다음 main/diagnostic/future/out-of-scope를 다시 판단한다.

## 2026-06-29 Additional Relation-Family Sweep Plan After Coverage Review

coverage review의 결론을 실행 가능한 sweep plan으로 바꾸었다. 이 단계는 learned smoke나
paper promotion이 아니라, 남은 family들의 evidence route를 schema-first로 정리하기 위한
계획 고정이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review/
status = h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready
selected_path = plan_schema_first_family_sweep_with_predicate_level_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan
```

생성된 artifact:

```text
family_sweep_rows = 5
predicate_fallback_policy_rows = 24
predicate_probe_rows = 20
execution_gate_rows = 5
predicate_gap_rows = 29
```

선택한 sweep 순서:

```text
1. relative_horizontal
2. containment_in
3. attachment_deferred
4. part_structural
5. identity_symmetry
```

가장 중요한 추가 원칙은 다음이다.

```text
If a multi-predicate family fails at family level, observe and decide each
relation type separately.
```

즉, 하나의 family 안에 여러 relation type이 있을 때 family aggregate가 실패해도 전체를
버리지 않는다. relation type별로 schema/capacity/shortcut 결과를 다시 보고, 성공한
predicate는 predicate-level evidence로 남기며 실패한 predicate는 diagnostic, deferred,
out-of-scope로 분리한다. 이 원칙은 support/contact의 `standing on`, `lying on`,
`supported by`에도 적용된다.

## 2026-06-29 Relative-Horizontal Reference-Frame Protocol Plan

`relative_horizontal` family의 첫 단계를 완료했다. 이 단계는 row materialization이나
learned smoke가 아니라, `left/right/front/behind/in front of`를 어떤 frame에서 해석할지
정하는 protocol이다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_reference_frame_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan
```

현재 판단:

- `relative_horizontal`은 아직 direct target materialization 대상이 아니다.
- 먼저 reference frame을 고정해야 한다.
- `scene_aligned_world_xy`는 source inventory의 첫 후보지만, label이 이 frame을 따른다는
  보장은 아직 없다.
- `view_or_camera_frame`은 multi-view disagreement가 생길 수 있으므로 audit/Q_e-first로 둔다.
- `object_centric_front_axis`는 semantic front orientation이 없으면 diagnostic/deferred다.
- `in front of`는 `front` alias인지 확인 전까지 diagnostic이다.

Factor contract:

```text
T_e = horizontal predicate text/label
G_e_horizontal = signed horizontal displacement under frozen frame
Q_e_frame = frame availability / frame disagreement / near-axis-boundary ambiguity
C_e = compatibility(T_e, G_e_horizontal), excluding Z_e
```

필수 controls:

```text
same-G predicate flip
wrong-frame rotation
axis sign flip
subject-object swap
predicate alias audit
class-pair/source shortcut audit
axis-boundary abstain
```

다음 source inventory에서는 GT anchor count, centroid/OBB join rate, same-G predicate-flip
capacity, frame availability, `front`와 `in front of` alias behavior, class/scan/endpoint
concentration을 측정한다.

## 2026-06-29 Relative-Horizontal Source Inventory After Reference-Frame Protocol

`relative_horizontal` source inventory를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready
selected_path = relative_horizontal_inventory_ready_for_candidate_materialization_plan_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory
```

결과 요약:

```text
left = 12,016 train rows
right = 12,016 train rows
front = 6,766 train rows
behind = 6,766 train rows
in front of = 0 train rows
centroid_pair_join_rate = 1.0
obb_pair_join_rate = 1.0
```

선택된 frame 후보:

```text
left/right = scene_world_x, left negative, alignment 0.765667
front/behind = scene_world_y, front negative, alignment 0.755649
```

해석:

- 수량과 source join은 충분하다.
- 하지만 alignment가 완전하지 않으므로 `relative_horizontal`은 clean route가 아니라
  frame-aware compatibility route로 다뤄야 한다.
- opposing rows와 axis-boundary rows는 binary label로 억지로 넣지 말고 `Q_e` 또는 diagnostic
  row로 분리해야 한다.
- `in front of`는 현재 source에서 관측되지 않았으므로 `front`와 merge하지 않는다.

## 2026-06-29 Relative-Horizontal Candidate Materialization Plan After Source Inventory

`relative_horizontal` candidate materialization plan을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory/
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_ready
selected_path = materialize_relative_horizontal_same_g_predicate_flip_rows_with_frame_qe_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan
```

Frozen row plan:

```text
primary_groups = 1,200
primary_rows = 2,400
positive_rows = 1,200
negative_rows = 1,200
left/right groups = 600
front/behind groups = 600
in front of rows = 0
```

Diagnostic row plan:

```text
axis_boundary_diagnostic_rows = 320
opposing_frame_diagnostic_rows = 320
```

의미:

- `relative_horizontal`은 이제 materialization을 해볼 수 있다.
- 하지만 frame alignment가 약 `0.76`이므로, clean solved relation이라고 말하면 안 된다.
- main target은 same-G predicate flip으로 만들고, axis-boundary/opposing-frame row는
  `Q_e`/diagnostic으로 분리한다.
- 이후 smoke에서 geometry-only, semantic-only, wrong-T, sign-flip, wrong-frame,
  subject/object swap, class-pair hidden probe를 반드시 확인해야 한다.

## 2026-06-29 Relative-Horizontal Candidate Materialization After Plan

`relative_horizontal` candidate rows를 materialize했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan/
status = h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan_ready_for_schema_shortcut_audit
selected_path = relative_horizontal_same_g_candidates_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization
```

Materialized result:

```text
candidate_rows = 3,040
group_rows = 1,520
model_safe_main_rows = 2,400
model_safe_qe_rows = 3,040

primary_groups = 1,200
primary_rows = 2,400
primary_positive_rows = 1,200
primary_negative_rows = 1,200

left/right groups = 600
front/behind groups = 600
axis_boundary_diagnostic_rows = 320
frame_disagreement_diagnostic_rows = 320
```

Precheck:

```text
blocked_model_input_hits = 0
group_integrity_errors = 0
paired_geometry_control_groups = 1,200
diagnostic_c_label_errors = 0
scan_max_groups = 11 <= 24
class_pair_max_groups = 109 <= 160
class_pair_axis_pair_max_groups = 59 <= 80
```

판단:

- `relative_horizontal`은 row materialization 단계는 통과했다.
- 같은 `G_e_horizontal`에서 predicate만 바꾼 primary group이므로, 다음 audit에서
  geometry-only와 predicate-only가 실제로 무력한지 확인해야 한다.
- positive predicate를 `left/right/front/behind` 각각 `300`개로 맞췄기 때문에 단순
  predicate prior는 의도적으로 약화했다.
- frame alignment 자체가 완전하지 않으므로, axis-boundary와 frame-disagreement row는 계속
  `Q_e`/diagnostic으로만 다룬다.

## 2026-06-29 Relative-Horizontal Schema Shortcut Audit After Materialization

`relative_horizontal` materialized rows의 schema/shortcut audit를 완료했다.

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

Main probes:

```text
T_predicate_label_only = 0.500
T_relation_family_only = 0.500
G_exact_tuple_only = 0.500
G_single_delta_x = 0.500
G_single_delta_y = 0.500
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
hidden_selected_axis_bucket_x_candidate_predicate = 1.000
```

판단:

- `relative_horizontal` target은 schema/shortcut gate를 통과했다.
- `T_e` alone과 `G_e_horizontal` alone은 모두 near-chance이며, 의도한 `T_e x G_e`
  interaction만 높다.
- hidden high-risk field는 construction proxy이므로 model-safe view에서 제외된 상태로만
  관리한다.
- 다음 단계는 learned smoke가 아니라 smoke input/model/control/gate를 고정하는
  sanitized-view smoke plan이다.

## 2026-06-29 Relative-Horizontal Sanitized View Smoke Plan After Schema Audit

`relative_horizontal` smoke plan을 고정했다.

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
positive / negative = 1,200 / 1,200
cv_groups = 1,200
paired_groups = 1,200
predicate_counts = left/right/front/behind each 600
feature_blocks = T_e + G_e_horizontal
```

Planned models:

```text
M1_semantic_only_T
M2_geometry_only_G_horizontal
M3_TG_concat_no_interaction
M4_TG_horizontal_interaction
```

Controls:

```text
wrong_T_same_G
shuffled_G_global
shuffled_G_within_predicate
axis_sign_flipped_G
wrong_frame_xy_swap
subject_object_swap
no_interaction_concat
```

판단:

- smoke plan은 정상적으로 고정됐다.
- runner는 `smoke_ready_view.jsonl`의 `feature_blocks`만 읽어야 한다.
- `relative_horizontal`은 방향성과 reference frame이 핵심이므로 wrong-frame, sign-flip,
  subject/object swap control이 필수다.
- 다음 단계는 learned smoke runner 구현/실행이다.

## 2026-06-29 Relative-Horizontal Sanitized View Smoke Runner After Plan

`relative_horizontal` train-only grouped-CV smoke를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_sanitized_view_smoke_runner_after_plan/
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

판단:

- `relative_horizontal`은 `T_e x G_e_horizontal` interaction이 필요한 clean mechanism
  route로 보인다.
- 단일 factor와 additive concat은 풀지 못했고, corruption controls는 collapse/inversion을 보였다.
- 단, reference-frame protocol 의존성이 있으므로 바로 paper main table로 올리기보다
  result review에서 route role을 먼저 결정해야 한다.

## 2026-06-29 Relative-Horizontal Smoke Result Review After Runner

`relative_horizontal` result review를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_relative_horizontal_as_main_compatibility_route_evidence_with_reference_frame_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal
```

판단:

- `relative_horizontal`은 H002의 main train-only `C_e` mechanism evidence로 둔다.
- 단, 이 route는 반드시 reference-frame-aware claim으로 제한한다.
- `in front of`는 현재 source에서 관측되지 않아 excluded/deferred로 둔다.
- calibrated `p_rel`/`p_obs`, paper-level result, complete horizontal ontology claim은 금지한다.
- 다음 단계는 multi-family route synthesis 업데이트다.

## 2026-06-29 Multi-Family Claim Synthesis After Relative-Horizontal

`relative_horizontal`을 포함한 multi-family route synthesis를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_relative_horizontal_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis
```

현재 route map:

| Family | Route | Role |
| --- | --- | --- |
| `relative_vertical` | clean sign compatibility | main mechanism evidence |
| `size_relative` | clean size compatibility | main mechanism evidence with calibration caveat |
| `relative_horizontal` | frame-aware directional compatibility | main mechanism evidence with reference-frame caveat |
| `support_contact` | point/contact/pose compatibility | challenging evidence with caveat |
| `proximity` | distance geometry | diagnostic/control |
| `attachment_like` | visual/mesh observability | future/deferred |

판단:

- H002는 이제 “고정 fusion”이 아니라 relation-aware evidence routing claim으로 정리된다.
- Clean route 3개가 모두 `T_e` only, `G_e` only, concat 실패와 interaction/control success를 보인다.
- support/contact는 near-threshold이지만 challenging compatibility route로 유지한다.
- 다음 단계는 이 route map에 맞춘 ablation/table plan update다.

## 2026-06-29 Ablation And Table Plan Update After Relative-Horizontal

`relative_horizontal`을 포함한 table/ablation/control/gate plan을 갱신했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis/
status = h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_ready
selected_path = freeze_relative_horizontal_aware_table_contract_select_route_coverage_sufficiency_review
validation_errors = 0
next_todo = compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan
```

Candidate table structure:

| Table | Role | Rows |
| --- | --- | --- |
| `T1` | Predicate-Geometry Compatibility Mechanism | `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact` |
| `T2` | Relation-Aware Evidence Routing Taxonomy | main/diagnostic/future/deferred route families |
| `T3` | Diagnostic Boundary Cases | `close by`, `supported by`, attachment-like, `in front of` |
| `T4` | Calibration and Claim Boundary | blocked claims, caveats, promotion gates |

판단:

- `relative_horizontal` 전용 wrong-frame / sign-flip / endpoint-swap controls가 table plan에 포함됐다.
- H002는 여전히 train-only mechanism evidence 단계다.
- 다음 단계는 현재 route coverage가 충분한지 판단하는 sufficiency review다.

## 2026-06-30 Route-Coverage Sufficiency Review After Relative-Horizontal Table Plan

route coverage sufficiency review를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready
selected_path = coverage_sufficient_for_hypothesis_framework_proceed_to_schema_freeze_promotion_protocol_no_new_family_now
validation_errors = 0
next_todo = compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review
```

판단:

- 현재 route coverage는 H002 hypothesis-stage framework claim에는 충분하다.
- 새 relation family를 즉시 추가하지 않고 schema freeze / promotion protocol로 넘어간다.
- main mechanism rows는 `relative_vertical`, `size_relative`, `relative_horizontal`,
  `support_contact`로 유지한다.
- `close by`는 geometry-easy diagnostic/control, attachment-like relation은
  observability-heavy future/deferred, containment/part/identity 계열은 boundary로 둔다.
- all-family generality, calibrated `p_rel`/`p_obs`, held-out/test reliability,
  complete horizontal ontology, support/contact solved claim은 여전히 금지한다.

## 2026-06-30 Schema Freeze And Promotion Protocol After Route-Coverage Review

route-specific target definition과 promotion protocol을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review/
status = h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready
selected_path = freeze_route_specific_target_definitions_and_promotion_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze
```

판단:

- H002는 relation을 learned target인지 아닌지로 나누지 않는다.
- 각 relation family가 어떤 evidence route와 target semantics를 요구하는지를 고정한다.
- `close by`는 geometry-only learned/evaluated route다.
- `supported by`는 superordinate support decomposition / relabel / abstain route다.
- `attached to`, `hanging on`, `connected to`는 observability-aware route다.
- `cover`, `leaning against`, containment 계열은 next feasibility routes다.
- `same as`, `same symmetry as`는 identity/symmetry route다.
- `part of`, `belonging to`는 semantic/structural route다.

다음 단계는 route-specific target manifest plan이다.

## 2026-06-30 Route-Specific Target Manifest Plan After Schema Freeze

route-specific target manifest plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze/
status = h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready
selected_path = freeze_per_route_target_manifests_select_manifest_consistency_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan
```

판단:

- 각 route별 target axis, label space, positive/negative/abstain definition을 manifest로 고정했다.
- 각 route별 model-safe view, hidden manifest, audit view 이름과 artifact root를 고정했다.
- `close by`는 `geometry_support` target이다.
- `supported by`는 `accept_relabel_abstain` target이다.
- attachment route는 `observability_then_reliability` target이다.
- main interaction routes는 `predicate_geometry_compatibility` target이다.
- row materialization, learned smoke, Docker/paper promotion은 아직 하지 않는다.

다음 단계는 manifest consistency audit이다.

## 2026-06-30 Route-Specific Target Manifest Consistency Audit After Plan

route-specific target manifest consistency audit를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan/
status = h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready
selected_path = manifest_consistency_pass_select_route_target_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit
```

결과:

- `49/49` audit checks pass.
- `close by`는 `geometry_support`로 유지됐다.
- `supported by`는 `accept_relabel_abstain`으로 유지됐다.
- attachment route는 `observability_then_reliability`로 유지됐다.
- `C_e`는 `Z_e`를 사용하지 않는 계약으로 유지됐다.
- hidden construction fields는 model-safe / `C_e` input에서 제외된다.

다음 단계는 route-specific target materialization plan이다.

## 2026-06-30 Route-Specific Target Materialization Plan After Manifest Audit

route-specific target materialization plan을 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit/
status = h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready
selected_path = freeze_materialization_waves_select_close_by_geometry_support_route_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```

결정:

- first concrete follow-up은 `R1 close by` geometry-support route다.
- `close by`는 `T_e x G_e` interaction 증거가 아니라 geometry-only learned/evaluated
  route 증거로 유지한다.
- `supported by`는 그 다음 priority로 두고, binary target이 아니라
  accept/relabel/reject/abstain decomposition route로 계획한다.
- attachment는 바로 materialize하지 않고 observability schema audit를 먼저 둔다.
- 실제 row materialization, learned smoke, Docker/paper promotion은 아직 하지 않는다.

## 2026-06-30 R1 Close-By Geometry-Support Materialization Plan

R1 `close by` materialization plan을 route-specific framework에 맞게 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready
selected_path = materialize_r1_close_by_as_geometry_support_route_root_not_interaction_claim
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan
```

핵심 판단:

- 기존 `close by` shortcut audit에서 distance/normalized-distance가 target을 거의 완전히
  푸는 것은 실패가 아니라 R1 geometry-only route의 expected behavior로 재해석한다.
- 단, 이 결과는 `T_e x G_e` interaction evidence가 아니다.
- 다음 materialization에서는 `C_e_label`이라는 표현을 `geometry_support_label`로 정규화한다.
- `T_e`와 `Z_e`는 route score input이 아니라 annotation/source baseline으로 둔다.
- `G_e`가 primary route evidence이고, `Q_e`는 abstain/coverage split만 담당한다.

다음 단계:

- `artifacts/route_specific_targets/r1_proximity/`에 route root materialization.
- distance/scale/coverage controls를 함께 emit.
- 이후 schema/shortcut audit에서 distance dominance를 blocker가 아니라 route property로 보고,
  non-geometry leakage와 wording drift를 blocker로 본다.

## 2026-06-30 R1 Close-By Route Root Materialization

R1 `close by` route root를 생성했다.

```text
artifact_root = artifacts/route_specific_targets/r1_proximity/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready
selected_path = materialized_r1_close_by_geometry_support_route_root
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization
```

결과:

- train-only rows: `1,284`
- primary binary rows: `800`
- primary binary balance: `400/400`
- Q_e / abstain diagnostics: `240`
- raw-distance diagnostics: `240`
- GT/geometry conflict audit: `4`

중요한 정리:

- `C_e_label`을 route-specific `geometry_support_label`로 대체했다.
- `c_e_interaction_label`은 `not_applicable`로 고정했다.
- `T_e`는 annotation/source-baseline 비교용이고, route score를 정의하지 않는다.
- `Z_e`는 source baseline 비교용이고, route score를 정의하지 않는다.
- `G_e`가 R1의 primary route evidence다.
- `Q_e`는 coverage/abstain 판단용이다.

따라서 `close by`는 H002에서 main interaction evidence가 아니라 geometry-only route evidence다.

## 2026-06-30 R1 Close-By Schema Audit

R1 `close by` route root schema audit를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization/
status = h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready
selected_path = r1_close_by_schema_pass_select_geometry_route_control_runner_plan
validation_errors = 0
passed_checks = 75
total_checks = 75
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan
```

통과한 핵심 항목:

- `model_safe_rows.jsonl`에 legacy `C_e_label`이 남아 있지 않다.
- hidden construction fields는 model-safe feature block에 없다.
- primary geometry-support labels는 `400/400`으로 균형이다.
- 모든 `1,284` rows에서 `c_e_interaction_label=not_applicable`이다.
- distance / normalized-distance / scale / coverage controls를 다음 runner에서 사용할 준비가 되어 있다.
- report/schema/control wording은 `close by`를 geometry-only route로 유지한다.

따라서 다음 단계는 `close by`를 interaction model로 학습하는 것이 아니라, geometry-only route
control runner를 계획하는 것이다.

## 2026-06-30 R1 Close-By Control Runner Plan

R1 `close by` geometry-only route control runner plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready
selected_path = plan_r1_close_by_geometry_only_route_controls_no_interaction_runner
validation_errors = 0
planned_controls = 12
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_control_runner
```

계획된 runner는 metric을 아직 실행하지 않는다. 다음 runner에서 보고할 항목은 다음이다.

- raw and normalized distance geometry baselines;
- overlap geometry diagnostic;
- raw-vs-normalized scale control;
- coverage / abstain control;
- source score and rank-only baseline;
- class-pair hidden audit;
- hidden `p_geom_valid` reference diagnostic;
- shuffled-G and wrong-pair geometry controls.

중요한 claim boundary:

- R1 `close by`는 geometry-only route evidence다.
- R1은 `T_e x G_e` interaction evidence가 아니다.
- distance dominance는 success/failure가 아니라 이 route의 expected property다.

## 2026-06-30 R1 Close-By Control Runner Result

R1 `close by` deterministic control runner를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready
selected_path = ran_r1_close_by_geometry_only_route_controls_no_interaction_model
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_result_review
```

핵심 결과:

| Control | AUROC / Accuracy |
| --- | ---: |
| `distance_xy` AUROC | 0.999556 |
| `distance_3d` AUROC | 0.998975 |
| `normalized_distance_xy` AUROC | 1.000000 |
| `normalized_distance_3d` AUROC | 1.000000 |
| `overlap_geometry` AUROC | 0.892500 |
| source semantic score AUROC | 0.552103 |
| class-pair-only accuracy | 0.503750 |
| hidden `p_geom_valid` AUROC | 0.999594 |
| `shuffled_G` AUROC | 0.336178 |
| `wrong_pair_geometry` AUROC | 0.006272 |

판단:

- `close by`는 source confidence보다 geometry evidence가 지배적인 relation이다.
- class-pair만으로는 target을 설명하지 못한다.
- wrong/shuffled geometry control이 무너지므로 실제 pair geometry를 보고 있다.
- 따라서 R1은 H002의 geometry-only route 대표 사례로 둘 수 있지만, interaction-route
  evidence로 쓰면 안 된다.

## 2026-06-30 R1 Close-By Result Review And Next Route Decision

R1 `close by` deterministic control 결과를 review하고 route 역할을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_route_result_review/
status = h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready
selected_path = freeze_close_by_as_geometry_only_route_evidence_move_to_supported_by_decomposition
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_target_plan
```

주요 판단:

- `close by`는 geometry-only learned/evaluated route evidence/control이다.
- normalized distance AUROC `1.000000`, hidden `p_geom_valid` AUROC `0.999594`로
  geometry evidence가 충분하다.
- source semantic score AUROC `0.552103`, class-pair-only accuracy `0.503750`라서
  source confidence나 class-pair shortcut만으로 target을 설명하지 못한다.
- shuffled-G와 wrong-pair geometry는 best accuracy `0.5`로 무너지므로 실제 pair geometry가
  필요하다.
- 이 결과는 `T_e x G_e` interaction evidence가 아니라, relation-aware evidence routing에서
  proximity family가 geometry-only route로 처리될 수 있음을 보여주는 evidence다.

다음 route는 R6 `supported by`다. `supported by`는 `standing on`/`lying on`의 clean
negative가 아니라 broad superordinate support relation이므로
accept/relabel/reject/abstain decomposition target으로 설계한다.

## 2026-06-30 R6 Supported-By Decomposition Target Plan

R6 `supported by` target plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_target_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready
selected_path = plan_supported_by_superordinate_accept_relabel_reject_abstain_route
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan
```

판단:

- `supported by`는 binary accept/reject target으로 쓰기 어렵다.
- 이 label은 `standing on`/`lying on`보다 넓은 superordinate support relation이라,
  subtype과 동시에 참일 수 있다.
- 따라서 R6는 `accept_broad_support`, `relabel_to_subtype`,
  `reject_no_support`, `abstain` target으로 분해한다.

현재 evidence:

- existing diagnostic rows: `160`
- diagnostic role seeds: `clear_accept=40`, `hard_reject_no_support=40`,
  `overlap_or_abstain=80`
- visual label supported-by counts: accept `82`, reject `11`, abstain `37`
- class-pair repair supported-by counts: accept `99`, reject `15`, abstain `46`

해석:

- reject가 부족하므로 기존 proxy label을 바로 binary smoke로 쓰면 안 된다.
- candidate materialization은 explicit no-support contradiction을 별도로 mining해야 한다.
- same class-pair 안에서 mixed labels를 확보해야 class-pair shortcut을 줄일 수 있다.
- generic endpoint가 abstain을 독점하지 않도록 non-generic ambiguous/low-observability rows가 필요하다.

## 2026-06-30 R6 Supported-By Candidate Materialization Plan

R6 `supported by` candidate materialization plan을 작성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready
selected_path = plan_320row_supported_by_decomposition_with_240row_min_viable_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization
```

계획된 quota:

- `accept_broad_support`: preferred `80`, minimum `60`
- `relabel_to_subtype`: preferred `80`, minimum `60`
- `reject_no_support`: preferred `80`, minimum `60`
- `abstain`: preferred `80`, minimum `60`

source capacity:

- total `supported by` rows: `50,601`
- class-pair balanced rows: `164`
- class-pair/rank balanced rows: `130`
- clear accept rows: `491`
- hard reject/no-support rows: `12,712`
- overlap/abstain rows: `37,398`

중요한 제약:

- materialization은 `320` rows를 목표로 하되, strict balance가 안 되면 `240` rows fallback을 허용한다.
- same class-pair 안에 mixed route labels가 있어야 한다.
- generic endpoint만으로 abstain이 결정되면 안 된다.
- no-GT는 negative가 아니라 audit/abstain 후보로만 둔다.
- learned smoke는 materialization 이후 schema/shortcut audit를 통과할 때까지 금지한다.

## 2026-06-30 R6 Supported-By Candidate Materialization

R6 `supported by` candidate materialization을 실행했다.

```text
artifact_root = artifacts/route_specific_targets/r6_superordinate_support/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_preferred_320row_target
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit
```

materialized rows:

- total rows: `320`
- `accept_broad_support`: `80`
- `relabel_to_subtype`: `80`
- `reject_no_support`: `80`
- `abstain`: `80`

selection diagnostics:

- unique scans: `257`
- unique class pairs: `173`
- mixed class-pair cells: `80`
- max rows per scan: `5/12`
- max rows per directed pair: `1/1`
- max rows per class pair: `4/16`
- hard-surface share: `0.278125/0.55`
- generic endpoint abstain share: `0.175/0.50`
- finite `G_e`: `320/320`

해석:

- R6는 기존 우려와 달리 preferred 320-row materialization 자체는 가능했다.
- 다만 이 결과는 target construction이 가능하다는 뜻이지, learned compatibility가 된다는 뜻은 아니다.
- 다음 단계에서 class-pair-only, source/rank hidden, generic-endpoint-only, hard-surface slice,
  wrong-pair/shuffled-G controls를 검사해야 한다.

## 2026-06-30 R6 Supported-By Schema Shortcut Audit

R6 `supported by` decomposition target의 schema/shortcut audit를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_plan
```

핵심 결과:

- rows: `320`
- labels: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`, `abstain 80`
- observable rows: `240`
- schema leakage hits: `0`
- allowed high-risk probes: `0`
- allowed medium-risk probes: `10`
- hidden high-risk probes: `8`

상위 allowed probes:

- `model_G_e_obb_contact_likelihood_proxy` on observable 3-way: AUROC `0.874609`
- `model_G_e_center_delta_z` on 4-way: AUROC `0.866094`
- `model_G_e_support_area_proxy` / `xy_overlap_min_ratio` on observable 3-way: AUROC `0.794219`

상위 hidden/control risk:

- `hidden_evidence_reason`, `audit_evidence_reason`: acc `1.0`
- observable 3-way에서 `hidden_label_match_status`, `hidden_candidate_role`, `hidden_machine_hint`, `hidden_matched_predicates`: acc `1.0`

판단:

- R6 row schema는 smoke plan으로 넘어갈 수 있다.
- 단, hidden construction field가 target을 복사할 수 있으므로 smoke runner는 `T_e`, `G_e_mesh_pose_contact`, `Q_e`만 사용해야 한다.
- 이 결과는 아직 learned smoke나 paper evidence가 아니다.

## 2026-06-30 R6 Supported-By Smoke Plan

R6 `supported by` decomposition smoke plan을 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_runner
```

runner-ready rows:

- rows: `320`
- labels: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`, `abstain 80`
- `p_obs`: observable `240`, abstain `80`
- `p_rel_binary`: accept-or-relabel `160`, reject `80`
- `p_rel_3way`: `accept_broad_support 80`, `relabel_to_subtype 80`, `reject_no_support 80`
- CV groups: `257`
- mixed-label CV groups: `39`

planned tasks:

- `T0_decomposition_4way`
- `T1_p_obs_binary`
- `T2_p_rel_binary_observable`
- `T3_p_rel_3way_observable`

planned models:

- `M1_T_class_only`
- `M2_G_geometry_only`
- `M3_Q_observability_only`
- `M4_TG_concat`
- `M5_GQ_route`
- `M6_TGQ_factorized_route`

핵심 boundary:

- hidden source/rank/`p_geom_valid`는 audit-only다.
- hidden construction field는 audit-only다.
- `Q_e`가 `p_obs`를 잘 푸는 것은 정상일 수 있지만, observable `p_rel`까지 혼자 풀면 target 문제가 된다.
- 이 plan은 learned smoke 실행이 아니라 다음 runner의 contract freeze다.

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

metric snapshot:

- `T1 p_obs M6_TGQ`: AUROC `0.978802`
- `T1 p_obs Q-only`: AUROC `1.000000`
- `T2 observable p_rel M6_TGQ`: AUROC `0.831328`
- `T2 observable p_rel GQ`: AUROC `0.905703`
- `T2 observable p_rel Q-only`: AUROC `0.880547`
- `T2 observable p_rel best single G_e`: AUROC `0.888984`
- `T2 shuffled-G`: AUROC `0.540703 / 0.459063`
- `T3 observable p_rel 3-way M6`: macro OVR AUROC `0.773047`, macro F1 `0.540704`
- hidden construction p_rel probe: AUROC `1.000000`

gate result:

- data integrity: pass
- p_obs signal: pass
- p_rel signal: pass
- p_rel gain over best component: fail
- Q boundary on observable p_rel: fail
- shortcut/single-factor boundary: pass
- shuffled-G degradation: pass
- shuffled-Q boundary: pass

판단:

- R6 `supported by`는 relation-aware route map에서 중요한 diagnostic이다.
- 하지만 현재 결과는 factorized `T_e + G_e + Q_e` route가 필요하다는 증거가 아니라,
  broad support decomposition이 `Q_e`/`G_e` target construction에 강하게 묶여 있음을 보여준다.
- 따라서 R6는 `standing on`/`lying on`과 같은 clean support/contact compatibility route와 분리한다.
- paper-facing으로는 “superordinate support labels need decomposition or abstention” 근거로 사용할 수 있지만,
  calibrated `p_rel` success나 all-family reliability success로 쓰면 안 된다.

## 2026-06-30 R6 Supported-By Smoke Result Review

R6 `supported by` smoke result review를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review/
status = h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update
selected_path = freeze_supported_by_as_superordinate_decomposition_diagnostic_keep_out_of_main_factorized_success
validation_errors = 0
next_todo = compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review
```

route decision:

- R6 `supported by`: `diagnostic_frozen_not_main_factorized_success`
- R3 `standing on` / `lying on`: `kept_separate_from_supported_by`
- R7 `attached to` / `hanging on` / `connected to`: `queued_after_route_map_update`

claim boundary:

- allowed: broad `supported by`는 accept/relabel/reject/abstain decomposition이 필요하다.
- allowed: `Q_e`는 p_obs와 observability-dominated relation label을 드러내는 데 유용하다.
- blocked: R6가 factorized `T_e+G_e+Q_e` p_rel success라는 주장.
- blocked: calibrated `p_rel`, paper-level result, all-family solved reliability claim.

판단:

R6는 H002에서 버리는 relation이 아니라, route taxonomy의 필요성을 보여주는 diagnostic이다.
다만 main mechanism table에서 `standing on`/`lying on`과 같은 predicate-level support/contact
compatibility evidence와 섞으면 claim이 약해진다. 다음 단계는 route map에 이 경계를 반영하는 것이다.

## 2026-06-30 Route Map Update After R6 Review

R6 `supported by` diagnostic boundary를 H002 route map에 병합했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review/
status = h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready
selected_path = merge_r6_diagnostic_boundary_select_attachment_observability_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_target_plan
```

route delta:

- R6 status: `included_as_decomposition_route_candidate` -> `diagnostic_frozen_not_main_factorized_success`
- R6 paper role: `claim_control_or_next_probe` -> `diagnostic_broad_label_decomposition_boundary`
- R5 boundary: `standing on` / `lying on`은 `supported by`와 분리 유지
- R7 next active route: `attached to` / `hanging on` / `connected to`

현재 H002 route map:

- main mechanism: `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact`
- diagnostic/control: `proximity`, `superordinate_support`
- next observability route: `attachment_observability`
- next feasibility fallback: `leaning against`
- later/future/boundary: `cover`, containment, identity/symmetry, semantic/structural, `build in`

판단:

이 업데이트로 `supported by`를 억지로 main success에 넣지 않고도 H002의 route-aware claim을 유지할 수 있다.
다음 단계는 R7 target plan에서 visual/multiview를 바로 learned input으로 넣는 것이 아니라,
`Q_e`/`p_obs`와 model-safe evidence boundary를 먼저 정의하는 것이다.

## 2026-06-30 R7 Attachment Observability Target Plan

R7 `attached to` / `hanging on` / `connected to`를 observability-first route로 계획했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_target_plan/
status = h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory
selected_path = plan_r7_attachment_observability_first_source_inventory_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_source_inventory
```

정리:

- 이 단계는 row materialization이나 learned smoke가 아니다.
- `p_obs`가 먼저이며, `p_rel`은 observable row에서만 정의한다.
- `attached to`와 `hanging on`은 primary observability-then-reliability route로 둔다.
- `connected to`는 physical/topological/functional connection evidence가 명시되기 전까지 diagnostic이다.
- 이전 attachment `560` positive-anchor label artifact는 `accept 60`, `reject 246`,
  `abstain 254`였고 shortcut-risk flags가 `98`이었으므로 direct training target으로 쓰지 않는다.

다음 TODO는 `compatibility_dataset_v3_attachment_observability_source_inventory`다. 이 단계에서
predicate별 candidate count, packet/point/mesh/visual evidence availability, endpoint identity,
topology/functional ambiguity를 먼저 세고, 그 결과가 통과해야 model-safe `G_e`/`Q_e` materialization으로
넘어간다.

## 2026-06-30 R7 Attachment Observability Source Inventory

R7 `attached to` / `hanging on` / `connected to` source inventory를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_source_inventory/
status = h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan
selected_path = r7_source_inventory_supports_attached_hanging_materialization_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization_plan
```

핵심 수치:

- full-train R7 후보: `attached to 185,346`, `hanging on 185,346`,
  `connected to 185,346`
- unique scans: `1,157`
- unique directed pairs: `185,346`
- old geometry verifier status: all R7 rows `unsupported`
- scan source files: all `1,157` scans have multiview, sequence, mesh-ready,
  and point/mesh-ready files
- packet reuse rows: `560`
- `attached to`: `238` ready packets, `46` strong same-frame pair visual rows
- `hanging on`: `242` ready packets, `58` strong same-frame pair visual rows
- `connected to`: `80` ready packets, `12` strong same-frame pair visual rows,
  explicit topology source rows `0`

판단:

`attached to`와 `hanging on`은 R7 observability materialization plan으로 진행한다.
`connected to`는 topology/functional connection source가 명시되기 전까지 diagnostic으로 둔다.
이 단계는 row materialization도 learned smoke도 아니며, 다음 단계에서 model-safe `G_e`/`Q_e`
schema와 shortcut controls를 먼저 계획해야 한다.

## 2026-06-30 R7 Attachment Observability Materialization Plan

R7 materialization plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready
selected_path = plan_primary_attached_hanging_gq_materialization_keep_connected_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_materialization
```

계획:

- primary wave: `attached to` / `hanging on` `480` rows
- diagnostic wave: `connected to` `80` rows
- full-train expansion: deferred

핵심 계약:

- `T_e`, `G_e_attachment`, `Q_e_observability`, hidden `Z_e`, target manifest를 분리한다.
- `G_e_attachment`는 scan/mesh/point evidence에서 재계산하거나 추출해야 하며, old
  construction proxy나 old `p_geom_valid`를 그대로 feature로 복사하지 않는다.
- `Q_e`는 evidence availability를 담고, `review_coverage`, `review_endpoint_identity`,
  `review_uncertainty` 같은 reviewer decision은 feature로 금지한다.
- `p_obs`가 먼저이며, `p_rel_observable`은 observable `attached to` / `hanging on`에만 둔다.
- `connected to`는 explicit topology/functional evidence가 없으므로 primary `p_rel`을 만들지 않는다.

주의:

locked target snapshot은 `p_obs 306/254`, observable `p_rel accept/reject 60/246`이다.
따라서 next materialization은 artifact 생성 단계이지, learned reliability claim 단계가 아니다.
row materialization 이후에는 schema shortcut audit이 먼저 필요하다.

## 2026-06-30 R7 Attachment Observability Materialization

R7 materialization을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit
selected_path = materialized_r7_gq_separated_source_target_hidden_control_views
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_schema_shortcut_audit
```

결과:

- rows: `560`
- `attached to`: `238`
- `hanging on`: `242`
- `connected to`: `80`
- geometry available rows: `560/560`
- model-safe rows: `560`
- target rows: `560`
- hidden rows: `560`
- control rows: `7`
- `p_obs_target`: `1:306`, `0:254`
- `p_rel_observable_target`: `1:60`, `0:246`, `None:254`

중요한 점:

- `T_e`, derived `G_e_attachment`, `Q_e_observability`만 model-safe view에 둔다.
- source score/rank, ids, packet paths, review labels, target labels은 hidden/target manifest에 분리했다.
- raw multi-view/mesh는 아직 모델 입력이 아니며, availability와 observability feature로만 사용했다.
- `connected to`는 topology/functional evidence가 없어 diagnostic으로 유지한다.
- positive sparse `p_rel` 때문에 바로 learned smoke로 가지 않는다. 다음 단계는 schema shortcut audit이다.

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

결과:

- rows: `560`
- `p_obs` rows: `560`, labels `306/254`
- observable `p_rel` rows: `306`, labels `60/246`
- schema leakage hits: `0`
- allowed high-risk blockers: `4`
- allowed medium-risk probes: `45`
- hidden high-risk probes: `5`

critical blockers:

- `p_obs:T_subject_object_pair`: accuracy `0.958929`
- `p_obs:T_predicate_x_class_pair`: accuracy `1.000000`
- `p_rel_observable:T_subject_object_pair`: accuracy `0.986928`
- `p_rel_observable:T_predicate_x_class_pair`: accuracy `1.000000`

판단:

`model_safe_view`에는 hidden id, source score/rank, packet path, review label, target label이 새지 않았다.
하지만 현재 R7 target은 predicate/class-pair만으로 거의 복원된다. 따라서 learned smoke를 진행하면
attachment observability나 predicate-geometry compatibility를 검증하는 것이 아니라 class-pair prior를
학습하는 실험이 된다.

다음 단계는 smoke runner가 아니라 path decision이다. R7을 계속 살리려면 같은 predicate와 유사/동일
class-pair 안에서 accept/reject가 함께 존재하는 contrast를 다시 mining해야 한다. 그렇지 않으면 R7은
diagnostic/qualitative route로 고정하고 다음 learned target을 다른 route로 이동하는 것이 맞다.

## 2026-06-30 R7 Attachment Observability Path Decision

R7 path decision을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining
selected_path = attempt_one_class_pair_balanced_r7_repair_before_diagnostic_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan
```

current artifact repair capacity:

- `p_obs` subject/object-pair mixed groups: `21`, balanced capacity `46`
- `p_obs` exact predicate x subject/object-pair mixed groups: `0`, balanced capacity `0`
- observable `p_rel` subject/object-pair mixed groups: `2`, balanced capacity `8`
- observable `p_rel` exact predicate x subject/object-pair mixed groups: `0`, balanced capacity `0`

결정:

- 현재 560-row artifact로 learned smoke를 실행하지 않는다.
- object label을 `T_e`에서 제거하는 방식은 사용하지 않는다. 이는 shortcut을 해결하는 것이 아니라
  semantic factor 자체를 약화시키는 것이다.
- current artifact만 재샘플링하는 repair는 불가능하다. 가장 강한 shortcut인 exact predicate x class-pair
  기준 mixed capacity가 `0`이다.
- `connected to`는 explicit topology/functional evidence가 없으므로 계속 diagnostic이다.
- full train source inventory에는 `attached to`와 `hanging on` 각각 `185,346` 후보가 있으므로, 한 번의
  class-pair-balanced repair mining pass를 시도한다.
- repair mining이 실패하면 R7은 diagnostic/qualitative observability route로 고정한다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Mining Plan

R7 class-pair repair mining plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready
selected_path = plan_exact_predicate_class_pair_capacity_scan_before_packet_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan
```

계획:

- 바로 candidate mining을 하지 않는다.
- 먼저 exact `predicate_label + subject_label + object_label` 기준 full-train capacity scan을 한다.
- capacity pass 후 packet rows는 `attached to 240`, `hanging on 240`까지 계획한다.
- post-label minimum은 predicate별 accept/reject `50/100`이다.
- `connected to`는 primary quota `0`이고 diagnostic이다.

다음 capacity gate:

- balanced primary rows `>= 400`
- positive rows `>= 100`
- exact predicate/class-pair mixed strata `>= 20`

이 단계에서는 label fill, row materialization, packet creation, learned smoke를 실행하지 않았다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Capacity Scan

R7 exact predicate/class-pair repair capacity scan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining
selected_path = exact_predicate_class_pair_repair_candidate_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining
```

핵심 결과:

- exact `predicate_label + subject_label + object_label` mixed groups: `4,616`
- exact class-pair raw balanced rows: `81,724`
- exact class-pair scan-capped balanced rows: `73,636`
- total accept/reject/uncertain proxy rows: `79,491 / 257,849 / 33,352`

predicate별 capacity:

- `attached to`: `3,232` mixed groups, `50,662` scan-capped balanced rows
- `hanging on`: `1,384` mixed groups, `22,974` scan-capped balanced rows

판단:

capacity gate가 통과했으므로 R7을 바로 diagnostic freeze할 필요는 없다. 이전 560-row
artifact의 shortcut 문제는 sampling artifact로 보는 것이 타당하다. 다음에는 full-train pool에서
exact predicate/class-pair가 섞인 controlled candidate rows를 mining한다.

경계:

- train-only proxy capacity scan이다.
- row/packet/label/model을 만들지 않았다.
- `connected to`는 계속 diagnostic이다.
- 이 결과는 candidate mining을 진행해도 된다는 근거이지, H002 observability route의 learned 성능
  근거는 아니다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Candidate Mining

R7 class-pair repair candidate mining을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan
```

후보 구성:

- total rows: `480`
- `attached to`: `240` rows
- `hanging on`: `240` rows
- `connected to`: `0` primary rows
- predicate별 proxy quota: accept `80`, reject `120`, uncertain `40`
- unique scans: `340`
- unique exact class-pair groups: `160`
- mixed exact class-pair groups: `attached to 80`, `hanging on 80`

주요 분포:

- role counts: accept proxy `160`, reject proxy `240`, uncertain proxy `80`
- coverage: `joined_no_uncertainty_flags 279`, `joined_with_uncertainty_flags 201`
- geometry bucket: `far_separated 240`, `mid_or_ambiguous 80`, near/overlap-family `160`
- GT status: `no_gt_for_pair 449`, `exact_match 10`, `family_match 14`, `pair_has_other_predicate 7`

판단:

이 결과는 R7 route를 계속 진행할 수 있다는 근거다. 이전 blocker였던 exact class-pair contrast 부족은
candidate source 단계에서 해결 가능하다. 다만 아직 packet, label, schema audit, learned smoke가 없으므로
성능 근거로 쓰면 안 된다.

다음 단계:

`packet_request_manifest.jsonl`을 입력으로 packet/material evidence generation plan을 만든다. 이때
multi-view/mesh는 label quality와 `Q_e` 확인용 evidence로 먼저 사용하고, learned input으로 승격하지 않는다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Packet Materialization Plan

R7 class-pair repair 후보 `480`개에 대해 packet/material evidence generation plan을 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_ready
selected_path = class_pair_repair_packet_materialization_plan_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization
```

evidence readiness:

- `T1_pair_multiview_ready`: `480/480`
- scan/mesh/semseg/sequence ready: `480/480`
- subject/object multiview ready: `480/480`
- shared view ready: `480/480`
- shared frame ready: `64/480`
- limited rows: `0`
- not-ready rows: `0`

artifact:

- `packet_plan_rows.jsonl`: reviewer-visible plan rows `480`
- `hidden_asset_manifest_plan.jsonl`: hidden provenance/asset rows `480`
- `evidence_inventory_by_candidate.jsonl`: evidence readiness rows `480`
- `visible_label_schema.json`
- `packet_materialization_contract.json`
- `quota_audit.csv`
- `evidence_tier_audit.csv`

판단:

이전 candidate mining 결과는 packet materialization으로 진행 가능하다. 이번 단계에서 실제 packet
이미지나 label은 만들지 않았다. visible plan은 relation text, evidence tier, image/mesh readiness,
blank review fields만 포함하며 scan id, instance id, source/rank, proxy role, GT status, construction
bucket, path는 hidden manifest에만 남겼다.

다음 단계는 actual packet materialization이다. 이 단계에서도 multi-view/mesh는 먼저 `Q_e`와 audit
label quality를 위한 evidence로 사용하고, learned input으로 바로 승격하지 않는다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Packet Materialization

R7 class-pair repair 후보 `480`개에 대해 실제 packet asset과 label-ready visible sheet를 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill
selected_path = attachment_observability_packets_ready_for_label_fill
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill
```

packet readiness:

- packet rows: `480`
- label-ready rows: `480`
- non-ready rows: `0`
- `attached to|ready`: `240`
- `hanging on|ready`: `240`
- `T1_pair_multiview_ready|ready`: `480`
- subject image rows: `480`
- object image rows: `480`
- pair crop rows: `480`
- observability card rows: `480`
- multiview sheet rows: `480`
- total subject thumbnails copied: `2772`
- total object thumbnails copied: `2804`
- visible leakage hits: `0`

artifact:

- `visible_review_sheet.csv`
- `packet_manifest.jsonl`
- `materialized_hidden_manifest.jsonl`
- `label_ready_manifest.jsonl`
- `non_ready_packet_rows.jsonl`
- `visible_leakage_hits.jsonl`
- `validation_errors.jsonl`
- per-row `packets/<review_row_id>/packet.md`

판단:

R7 class-pair repair route는 이제 visible-only label fill로 넘어갈 수 있다. 아직 label은 채우지
않았고, target ingestion, schema/shortcut audit, learned smoke도 실행하지 않았다. 따라서 이 결과는
observability route의 성능 근거가 아니라, label-ready packet artifact가 준비됐다는 뜻이다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Label Fill

R7 class-pair repair packet `480`개에 대해 visible-only label fill을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_completed
selected_path = codex_visible_packet_labels_filled_user_requested
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion
```

label distribution:

- total rows: `480`
- `review_observability_label`: `observable 455`, `uncertain 25`
- `review_relation_label`: `accept 258`, `reject 90`, `abstain 132`
- `review_evidence_quality`: `sufficient 458`, `partial 22`
- `review_endpoint_identity`: `clear 476`, `ambiguous 4`
- `packet_asset_count=4`: `480`

predicate by relation label:

- `attached to|accept`: `172`
- `attached to|abstain`: `68`
- `attached to|reject`: `0`
- `hanging on|accept`: `86`
- `hanging on|reject`: `90`
- `hanging on|abstain`: `64`

판단:

label fill 자체는 통과했다. 하지만 `attached to`가 reject 없이 accept/abstain으로만 채워졌기 때문에,
next ingestion에서 predicate별 target을 그대로 합치면 shortcut 또는 imbalance 문제가 다시 생길 수 있다.
따라서 다음 단계의 핵심은 label ingestion 후 다음을 분리해 보는 것이다.

- multiclass: accept/reject/abstain
- observability: observable vs uncertain/not observable
- observable relation: accept vs reject among observable rows
- predicate-specific relation target
- combined attachment-observability route target

이 결과는 아직 learned smoke 허용 근거가 아니다. ingestion과 schema/shortcut audit이 먼저 필요하다.

## 2026-06-30 R7 Attachment Observability Class-Pair Repair Label Ingestion

R7 class-pair repair visible labels를 target artifact로 ingestion했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit
selected_path = ingest_visible_packet_labels_run_schema_shortcut_audit_next
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit
```

target rows:

- `ingested_target_rows.jsonl`: `480`
- `multiclass_rows.jsonl`: `480`
- `observability_binary_rows.jsonl`: `480`
- `observable_relation_binary_rows.jsonl`: `348`

target viability:

- relation multiclass: `accept 258`, `reject 90`, `abstain 132`
- `p_obs`: positive `455`, negative `25` -> negative-sparse diagnostic-only
- combined observable `p_rel`: rows `348`, accept `258`, reject `90` -> schema audit 가능
- `attached to` observable `p_rel`: accept `172`, reject `0` -> single-class diagnostic-only
- `hanging on` observable `p_rel`: accept `86`, reject `90` -> schema audit 가능

shortcut preview:

- risk flags: `20`
- 대표 risk: visible `subject_label`, `subject_object_class_pair`, `predicate_subject_object_class_pair`,
  hidden `exact_class_pair_id`, hidden id/provenance fields, and label-derived `decision_reason`.

판단:

R7 ingestion은 성공했지만 learned smoke는 아직 금지다. 다음 schema/shortcut audit에서 다음 세 가지를
분리해서 판단해야 한다.

- combined observable `p_rel`을 class-pair/predicate shortcut 없이 사용할 수 있는가?
- `hanging on` 단독 target은 충분히 독립적인가?
- `attached to`는 negative mining/label repair 없이 diagnostic으로 고정해야 하는가?

## 2026-07-01 R7 Attachment Observability Class-Pair Repair Schema Shortcut Audit

R7 class-pair repair schema/shortcut audit을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_blocked_shortcut_risk
selected_path = block_learned_smoke_select_path_decision
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit
```

핵심 결과:

- rows: `480`
- combined observable `p_rel`: `348` rows, accept/reject `258/90`
- `hanging on` observable `p_rel`: `176` rows, accept/reject `86/90`
- `attached to` observable `p_rel`: `172` rows, accept/reject `172/0`
- allowed high-risk shortcut blockers: `14`
- learned smoke allowed: `false`

shortcut 결과:

- combined observable `p_rel`은 `predicate_subject_object_class_pair`만으로 majority accuracy
  `1.0`이다.
- `hanging on` 단독 `p_rel`은 label mass가 균형적이지만, `subject_label`,
  `subject_object_class_pair`, `predicate_subject_object_class_pair`가 모두 majority accuracy
  `1.0`이다.
- exact class-pair 기준 mixed groups가 `0`이므로 current artifact 안에서 resampling만으로는
  clean compatibility target을 만들 수 없다.

관계 타입별 판단 업데이트:

- `attached to`: 현재 visible-packet label policy에서는 observable reject가 없어 diagnostic-only다.
- `hanging on`: binary mass는 좋지만 class-pair shortcut이 완전하므로 learned smoke 금지다.
- `connected to`: 이전 계획대로 diagnostic-only다. explicit topology/functional connection evidence
  없이는 binary physical compatibility target으로 쓰기 어렵다.

전체 판단:

R7은 relation-aware evidence routing에서 중요한 observability-heavy family지만, 현재 artifact는
main learned `C_e`/`Q_e` evidence로 승격할 수 없다. 다음 단계는 path decision이며, R7을
diagnostic freeze할지, truly mixed same-class-pair accept/reject를 다시 mining할지, 또는 `p_obs`
/ abstention route로 재정의할지 결정해야 한다.

## 2026-07-01 R7 Attachment Observability Class-Pair Repair Path Decision

R7 class-pair repair path decision을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_freeze_diagnostic
selected_path = freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze
```

결정:

현재 R7 class-pair repair artifact는 diagnostic-only로 고정한다. learned smoke, calibrated
`p_rel`, calibrated `p_obs`, paper-level reliability evidence로 승격하지 않는다.

reject:

- combined observable `p_rel` learned smoke: `predicate_subject_object_class_pair`가 target을
  accuracy `1.0`으로 복원한다.
- `hanging on` only learned smoke: `subject_label`과 `subject_object_class_pair`가 target을
  accuracy `1.0`으로 복원한다.
- 같은 proxy recipe의 재-mining: full-train exact class-pair repair를 이미 한 번 수행했지만,
  visible label 이후 mixed class-pair capacity가 `0`으로 붕괴했다.

defer:

- truly mixed same-class-pair visual accept/reject mining
- low-observability / occlusion-focused `p_obs` route

현재 relation type별 업데이트:

- `attached to`: diagnostic/future only. Current visible target is `172/0`.
- `hanging on`: diagnostic/future only under current artifact. Counts are balanced, but target independence fails.
- `connected to`: diagnostic-only. Functional/topological evidence가 별도로 필요하다.

다음 scope synthesis에서는 R7을 observability-heavy diagnostic boundary로 명시하고, H002의 main
claim이 어떤 relation families에 근거하는지 다시 정리해야 한다.

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

새 relation family mining은 지금 추가하지 않는다. 현재 route coverage는 hypothesis-stage
framework claim에는 충분하다. 다음 단계는 paper/framework readiness review다.

최종 route boundary:

| Scope | Relations/Families | Status |
| --- | --- | --- |
| main mechanism | `higher/lower`, `bigger/smaller`, `left/right/front/behind`, `standing/lying on` | retain |
| geometry-easy control | `close by` | retain as control/generality |
| superordinate diagnostic | `supported by` | retain as diagnostic |
| observability-heavy boundary | `attached to`, `hanging on`, `connected to` | current artifact diagnostic-only |
| future/separate | containment, `cover`, `leaning against`, identity/symmetry, semantic/structural | defer |

의미:

R7은 current learned evidence가 아니지만 H002 route taxonomy에서 중요한 boundary다. 이 결과는
“attachment-like relation은 source proxy와 class-pair만으로 만든 binary target이 아니라,
visible/mesh/topology evidence와 `Q_e` 중심의 observability-aware target construction이 필요하다”는
점을 보여준다.

blocked claims는 유지한다.

- all-family generality
- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- current R7 learned reliability
- support/contact fully solved

## 2026-07-01 Paper/Framework Readiness Review

R7 diagnostic freeze와 scope synthesis 이후 paper/framework readiness review를 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes/
status = h002_compatibility_dataset_v3_paper_framework_readiness_review_after_route_specific_probes_ready
selected_path = readiness_review_completed_select_promotion_gap_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review
```

결론:

현재 H002는 framework-ready, not paper-result-ready 상태다. 지금까지의 route-specific probe는
relation-aware evidence routing framework와 candidate main mechanism table을 구성하기에는 충분하다.
하지만 논문 결과로 승격하려면 Docker reproduction, held-out grouped evaluation, calibration/selective
decision, target-independence replication, claim wording lock이 필요하다.

candidate main mechanism rows:

| Family | Relations | 현재 역할 |
| --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | clean `T_e x G_e` mechanism anchor |
| `size_relative` | `bigger than`, `smaller than` | clean mechanism anchor with calibration caveat |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | frame-aware mechanism anchor |
| `support_contact` | `standing on`, `lying on` | challenging compatibility-route evidence with caveat |

diagnostic/control/boundary rows:

| Family | Relations | 현재 역할 |
| --- | --- | --- |
| `proximity` | `close by` | geometry-only route control |
| `support_contact_superordinate` | `supported by` | superordinate decomposition / relabel / abstain diagnostic |
| `attachment_like` | `attached to`, `hanging on`, `connected to` | observability-heavy diagnostic/future boundary |
| future/separate routes | containment, `cover`, `leaning against`, identity/symmetry, semantic/structural | deferred taxonomy boundary |

따라서 다음 단계는 새 relation family mining이 아니라 promotion gap plan이다. 즉, 어떤 claim을 어떤
실험 gate를 통과해야 paper-level로 올릴 수 있는지 명시해야 한다.

## 2026-07-01 Promotion Gap Plan

Paper/framework readiness review를 promotion gap plan으로 구체화했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review/
status = h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_ready
selected_path = promotion_gap_plan_ready_select_docker_heldout_protocol_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan
```

결론:

H002는 paper-level result로 바로 승격하지 않는다. 현재 결과는 hypothesis-stage route-specific
mechanism evidence이며, paper result로 쓰려면 아래 gate가 필요하다.

| Gate | 의미 |
| --- | --- |
| Docker reproduction | host-only train smoke가 아니라 container에서 row/materialization/control/metric을 재생성 |
| Held-out grouped evaluation | scan 및 endpoint-pair leakage 없이 route signal이 유지되는지 확인 |
| Calibration/selective decision | `C_e`와 별도로 `p_rel`, `p_obs`를 주장하려면 ECE/Brier/NLL/selective-risk 필요 |
| Target-independence replication | class-pair, source/rank, endpoint, wrong-T, shuffled-G shortcut audit 반복 |
| Claim wording lock | all-family, R7 learned reliability, support/contact fully-solved claim 차단 |

승격 후보는 `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact`로 유지한다.
다만 `support_contact`는 “fully solved”가 아니라 challenging compatibility-route evidence로만 둔다.

`close by`, `supported by`, R7 attachment-like relation, future/separate routes는 현재 promotion path에서
paper-level main result로 올리지 않는다. 이들은 relation-aware routing claim의 control/diagnostic/boundary
evidence로 사용한다.

다음 작업은 Docker experiment root를 바로 만드는 것이 아니라, 먼저
`compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan`에서 data mount,
split policy, output manifest, leakage audit, controls를 고정하는 것이다.

## 2026-07-01 Docker Heldout Protocol Plan

Docker + grouped-holdout protocol plan을 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan/
status = h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready
selected_path = docker_heldout_protocol_ready_select_experiment_root_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan
```

이번 단계에서는 실험 root를 만들지 않았다. 즉, `experiments/H002_compatibility_routing/`,
`configs/h002/`, `results/h002_compatibility_routing/`는 future root로만 제안했다.

제안된 protocol:

| Item | 내용 |
| --- | --- |
| source pool | H002 candidate source pool |
| official validation/test | 사용하지 않음 |
| primary split group | `scan_id` |
| secondary leakage guard | endpoint pair |
| split ratio | train/dev/heldout = 70/15/15 by groups |
| promoted routes | `relative_vertical`, `size_relative`, `relative_horizontal`, `support_contact` |
| diagnostic/deferred | `close by`, `supported by`, R7 attachment-like, future/separate routes |

future Docker services:

- `h002-protocol-check`
- `h002-materialize-routes`
- `h002-shortcut-audit`
- `h002-grouped-eval`
- `h002-calibration`, optional

pass/fail gates:

- D0: protocol artifact validation errors 0 and no experiment root created
- D1: Docker mount/preflight pass
- D2: route row materialization pass
- D3: grouped holdout and controls pass
- D4: optional calibration/selective-risk pass
- D5: claim wording lock pass

다음 단계에서 experiment/config/results skeleton을 만들 경우, durable root 생성 규칙에 따라
`experiments/README.md`, `configs/README.md`, `docs/index.md`, root `TODO.md`를 함께 갱신해야 한다.

## 2026-07-01 Experiment Root Skeleton

Docker heldout protocol 이후 H002 skeleton을 생성했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan/
status = h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_ready
selected_path = experiment_config_results_skeleton_created_select_docker_preflight_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton
```

생성한 root:

| Root | 역할 |
| --- | --- |
| `experiments/H002_compatibility_routing/` | future H002 Docker experiment workspace |
| `configs/h002/` | future H002 Docker config root |
| `results/h002_compatibility_routing/` | future compact H002 result summaries |

현재는 skeleton 단계이므로 다음은 paper metric이 아니라 Docker preflight implementation이다.
Preflight는 mount, prior artifact status, output root, H001 read-only boundary를 먼저 확인해야 한다.

## 2026-07-01 Docker Preflight Implementation

H002 Docker preflight service를 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton/
status = h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_ready
selected_path = docker_preflight_passed_select_route_materialization_protocol_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight
```

추가한 실행 파일:

| File | 역할 |
| --- | --- |
| `configs/h002/Dockerfile` | H002 minimal Docker image |
| `configs/h002/compose.yaml` | `h002-protocol-check` service |
| `experiments/H002_compatibility_routing/scripts/preflight.py` | mount/status/read-only preflight |

실행:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-protocol-check
```

Preflight output:

```text
experiments/H002_compatibility_routing/preflight/latest/mount_check.json
experiments/H002_compatibility_routing/preflight/latest/run_manifest.json
experiments/H002_compatibility_routing/preflight/latest/validation_errors.jsonl
```

검증 결과:

- exit 0
- validation errors 0
- H002 protocol/skeleton artifact status 확인
- `local_dataset/` mount 확인
- H001 result/archive experiment roots read-only 확인
- paper metric, grouped holdout, official validation/test 없음

다음은 route materialization protocol implementation이다. 아직 `h002-materialize-routes`,
`h002-shortcut-audit`, `h002-grouped-eval`, `h002-calibration`은 구현/실행하지 않는다.

## 2026-07-01 Route Materialization Protocol Implementation

Docker preflight 이후 H002 promoted route materialization을 구현하고 실행했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight/
status = h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready
selected_path = docker_materialized_promoted_routes_select_materialization_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization
```

추가/수정한 실행 파일:

| File | 역할 |
| --- | --- |
| `experiments/H002_compatibility_routing/scripts/materialize_routes.py` | promoted route rows, model-safe view, hidden manifest materialization |
| `configs/h002/compose.yaml` | `h002-materialize-routes` service |
| `tools/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight.py` | runtime materialization output validation and stage artifact writer |

실행:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes
```

Runtime output:

```text
experiments/H002_compatibility_routing/materialization/latest/route_rows.jsonl
experiments/H002_compatibility_routing/materialization/latest/model_safe_view.jsonl
experiments/H002_compatibility_routing/materialization/latest/hidden_manifest.jsonl
experiments/H002_compatibility_routing/materialization/latest/row_manifest.json
experiments/H002_compatibility_routing/materialization/latest/validation_errors.jsonl
```

Materialized rows:

| Route family | Rows | Label 0 | Label 1 | Predicates |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 1512 | 756 | 756 | `higher than`, `lower than` |
| `size_relative` | 2400 | 1200 | 1200 | `bigger than`, `smaller than` |
| `relative_horizontal` | 2400 | 1200 | 1200 | `left`, `right`, `front`, `behind` |
| `support_contact` | 640 | 320 | 320 | `standing on`, `lying on` |

검증 결과:

- 총 row `6952`.
- route/model-safe/hidden manifest line count 일치.
- validation errors `0`.
- `C_e` input contract은 `T_e + G_e`로 제한.
- `Q_e`와 `Z_e`는 이후 `p_obs`/`p_rel` protocol을 위해 저장하지만 다음 compatibility audit에는 사용하지 않는다.
- grouped-holdout metric, official validation/test, paper-level H002 metric은 아직 없다.
