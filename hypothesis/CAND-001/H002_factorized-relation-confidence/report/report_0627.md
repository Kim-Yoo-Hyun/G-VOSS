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

따라서 현재 H002의 상태는 다음과 같이 정리한다.

- 현재 허용되는 claim은 train-only predicate-conditioned compatibility `C_e` mechanism evidence다.
- 선택된 main route는 relation-aware predicate-geometry compatibility routing이다.
- R7 attachment-observability는 shortcut risk 때문에 diagnostic/future boundary로 둔다.
- 아직 paper-level result, held-out/test performance, all-family reliability, calibrated `p_rel/p_obs`
  posterior claim은 금지한다.
- 다음 TODO는 R7 attachment-observability를 계속 수리할지, diagnostic으로 고정하고 paper-level
  route promotion으로 넘어갈지 결정하는 것이다.

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

목적:

현재 병목은 relation type 수가 부족한 것이 아니라, reliability target이 source score,
class prior, construction rule과 독립적인지 증명하기 어렵다는 점이다. 따라서
`relative_vertical`만 held-out/Docker로 승격하는 것은 H002의 범위를 너무 좁게 만들 수
있다.

결과:

다음 route는 `support_contact`의 visual/mesh/human-audit target으로 고정했다.
`standing on`, `lying on`, `supported by`를 중심으로 independent target source를 만들고,
`size_relative`와 containment 계열은 bounded feasibility probe로만 둔다. 다음 step은
`support_contact` audit target plan을 작성해, 어떤 evidence를 사람이 확인하고 어떤 field를
model input에서 숨길지 먼저 고정하는 것이다.

## 2026-06-28 Support/Contact Audit Target Plan

목적:

H002의 병목이 model combiner가 아니라 target-source independence라는 점을 확인했기 때문에,
`support_contact`를 visual/mesh/human-audit 기반 target으로 다시 설계했다. 목표는
`standing on`, `lying on`, `supported by`를 source score나 class prior가 아니라 실제 evidence로
판단할 수 있는지 확인하는 것이다.

결과:

Audit target plan과 source inventory를 고정했고, packet materialization으로 진행할 수 있음을 확인했다.
다음 step은 visible packet을 만들고, 사람이 볼 수 있는 evidence만으로 label을 채우는 것이었다.

## 2026-06-28 Visual/Mesh Audit Labeling

목적:

기존 proxy target이 class/predicate shortcut에 취약했기 때문에, visible packet 기반으로
`accept / reject / abstain`, observability, evidence quality를 다시 채워 independent target을 만들고자 했다.

결과:

Packet materialization, label fill, label ingestion은 완료됐지만, label이 여전히 construction bucket,
class pair, predicate source와 강하게 얽혔다. learned smoke로 바로 가면 H002 factorization을 검증하는
것이 아니라 shortcut을 학습할 위험이 컸다. 다음 step은 class-pair controlled repair였다.

## 2026-06-28 Class-Pair Repair

목적:

`support_contact` audit label에서 class-pair shortcut이 강했기 때문에, 같은 또는 유사한
class-pair 안에 accept/reject가 함께 존재하는 target을 다시 만들 수 있는지 확인했다.

결과:

Repair packet, label fill, ingestion까지 진행했지만 shortcut risk가 충분히 낮아지지 않았다.
따라서 이 branch는 diagnostic으로 고정했고, 다음 step은 현재까지의 relation-family scope를 다시
정리하는 것이었다.

## 2026-06-28 Relation-Family Scope And Proximity

목적:

`support_contact`만 파는 것이 H002 claim을 좁게 만들 수 있으므로, 다른 relation family로 확장 가능한지
확인했다. 특히 `close by`는 row 수가 많고 geometry evidence가 명확해 보였기 때문에 먼저 검토했다.

결과:

`close by`는 많은 row를 확보할 수 있었지만, target이 distance/normalized-distance로 거의 풀리는
geometry-easy route였다. 따라서 `T_e x G_e` interaction evidence가 아니라 geometry-only route
control/generality evidence로 두었다. 다음 step은 `standing on`, `lying on`, `supported by`를
개별 predicate로 다시 보는 것이었다.

## 2026-06-29 Support/Contact Individual Predicate Probe

목적:

family aggregate로 보면 `support_contact`가 흐려지므로, `standing on`, `lying on`, `supported by`를
분리해서 어떤 predicate가 compatibility target으로 의미가 있는지 확인했다.

결과:

`standing on`과 `lying on`은 pose/contact 기반 compatibility route로 가능성이 있었고,
point/multiview evidence를 추가했을 때 near-threshold signal을 보였다. 반면 `supported by`는
superordinate relation 성격이 강해서 clean binary target으로 쓰기 어렵다고 판단했다. 다음 step은
relation-aware route table과 ablation/table plan을 만드는 것이었다.

## 2026-06-29 Multi-Family Claim And Table Plan

목적:

각 relation을 같은 방식으로 처리하지 않고, relation family별로 필요한 evidence route가 다르다는
H002 claim을 정리하기 위해 route taxonomy와 table skeleton을 만들었다.

결과:

`relative_vertical`은 clean compatibility route, `support_contact`는 challenging compatibility route,
`close by`는 geometry-only control, attachment-like relation은 observability-heavy future route로 정리했다.
하지만 relation coverage가 아직 부족했으므로, 다음 step은 새로운 physical relation family를 추가로
검토하는 것이었다.

## 2026-06-29 Size-Relative Route

목적:

`higher/lower`만으로는 H002가 signed vertical rule처럼 보일 수 있으므로, `bigger than` / `smaller than`을
추가해 다른 physical comparison family에서도 `T_e x G_e` compatibility가 필요한지 검증했다.

결과:

`size_relative`는 same-G predicate flip target을 만들 수 있었고, smoke runner에서
`T_e` only, `G_e` only, plain concat은 실패한 반면 `T_e x G_e_size` interaction은 AUROC `0.9999`를 보였다.
wrong-T, shuffled-G, sign-flip controls도 무너졌다. 따라서 `size_relative`는 main mechanism evidence로
올릴 수 있지만, calibration claim은 아직 금지했다. 다음 step은 horizontal relation family였다.

## 2026-06-29 Relative-Horizontal Route

목적:

`left`, `right`, `front`, `behind`는 GT mass가 크고 중요한 spatial relation이지만 reference-frame ambiguity가
있다. 그래서 먼저 frame protocol을 고정한 뒤, frame-aware compatibility target으로 검증했다.

결과:

`scene_world_x/y` 기반 frame protocol, same-G predicate flip materialization, schema audit, smoke runner를
완료했다. `M4_TG_horizontal_interaction`은 AUROC `1.0000`을 보였고 semantic-only, geometry-only,
plain concat은 실패했다. wrong-T, sign-flip, subject/object swap controls도 붕괴했다. 단,
reference-frame caveat가 있으므로 frame-invariant claim은 금지했다. 다음 step은 route coverage sufficiency와
schema freeze였다.

## 2026-06-30 Schema Freeze And Promotion Protocol

목적:

route별 probe가 늘어나면서 target 정의가 흩어질 위험이 생겼다. Paper-level experiment로 가기 전에
각 route의 target semantics, model-safe fields, diagnostic/future boundary를 고정해야 했다.

결과:

현재 hypothesis-stage framework claim에는 `relative_vertical`, `size_relative`, `relative_horizontal`,
`support_contact` coverage가 충분하다고 판단했다. 이후 route-specific target manifest와 materialization
plan을 고정하고, `close by`, `supported by`, attachment-like relation을 각각 route-specific diagnostic으로
정리하는 방향으로 넘어갔다.

## 2026-06-30 R1 Close-By Geometry-Only Route

목적:

`close by`를 억지로 `T_e x G_e` interaction target으로 만들지 않고, proximity family가 geometry-only route로
충분한지를 명시적으로 검증했다.

결과:

`close by` control runner에서 normalized distance AUROC는 `1.0000`, source semantic score AUROC는
`0.5521`, class-pair-only accuracy는 `0.5038`이었다. shuffled-G와 wrong-pair geometry는 무너졌다.
따라서 `close by`는 interaction evidence가 아니라 geometry-only route evidence/control로 고정했다.
다음 step은 `supported by` decomposition이었다.

## 2026-06-30 R6 Supported-By Decomposition

목적:

`supported by`는 `standing on`/`lying on`의 clean negative가 아니라 broad support superordinate label이다.
따라서 binary compatibility가 아니라 accept/relabel/reject/abstain decomposition target이 필요한지 확인했다.

결과:

320-row balanced decomposition target은 만들 수 있었고 schema audit도 통과했다. Smoke에서는 `p_obs`와
observable `p_rel` signal이 있었지만, `Q_e`/`G_e`와 target construction이 너무 강하게 얽혀 있어
factorized success로 주장하기 어렵다고 판단했다. `supported by`는 main success가 아니라
superordinate decomposition diagnostic으로 고정했고, 다음 step은 R7 attachment observability였다.

## 2026-06-30 R7 Attachment Observability

목적:

`attached to`, `hanging on`, `connected to`는 point/OBB geometry만으로 판단하기 어려운 observability-heavy
relation이다. H002의 `Q_e`와 abstention route가 필요한 대표 family인지 확인했다.

결과:

처음 materialized 560-row artifact는 predicate/class-pair shortcut으로 blocked됐다. Full-train에서
class-pair repair capacity는 있었고 480-row packet을 다시 만들었지만, visible label ingestion 이후에도
`attached to`는 reject가 없고, `hanging on`은 class-pair shortcut이 남았다. 결국 R7은 current artifact에서는
learned smoke를 금지하고 diagnostic/future route로 고정했다. 다음 step은 전체 route scope synthesis였다.

## 2026-07-01 Scope Synthesis After R7 Freeze

목적:

R7을 diagnostic으로 고정한 뒤, H002가 어디까지 주장할 수 있고 무엇을 막아야 하는지 다시 정리했다.

결과:

Main mechanism은 `higher/lower`, `bigger/smaller`, `left/right/front/behind`, `standing/lying on`으로 유지했다.
`close by`는 geometry-only control, `supported by`는 superordinate diagnostic, attachment-like relation은
observability-heavy diagnostic/future boundary로 정리했다. 다음 step은 paper/framework readiness review였다.

## 2026-07-01 Paper/Framework Readiness Review

목적:

지금까지의 route-specific probe가 논문 수준 결과인지, 아니면 framework-ready hypothesis evidence인지
판단했다.

결과:

H002는 framework-ready이지만 paper-result-ready는 아니라고 판단했다. Route-specific mechanism evidence는
충분하지만, paper-level result로 승격하려면 Docker reproduction, held-out grouped evaluation,
target-independence replication, calibration/selective decision boundary, claim wording lock이 필요하다.
다음 step은 promotion gap plan이었다.

## 2026-07-01 Promotion Gap And Docker Protocol

목적:

H002 결과를 paper-level로 승격하려면 어떤 실험 gate가 필요한지 정의하고, host-only smoke에서 Docker 기반
재현 가능한 experiment로 옮길 준비를 했다.

결과:

Promotion gap plan과 Docker heldout protocol을 고정했다. Official validation/test는 아직 사용하지 않고,
H002 candidate pool에서 scan/endpoint leakage를 막는 grouped split을 우선 사용하기로 했다. 다음 step은
experiment/config/results skeleton 생성과 Docker preflight였다.

## 2026-07-01 Docker Experiment Skeleton And Preflight

목적:

H002를 실제 paper-level experiment 후보로 올릴 수 있도록 Docker 기반 실행 root를 만들고 mount/read-only
boundary를 확인했다.

결과:

`experiments/H002_compatibility_routing/`, `configs/h002/`, `results/h002_compatibility_routing/` skeleton을
만들고 Docker preflight를 통과했다. H001 artifacts는 read-only reference로만 다루도록 확인했다.
다음 step은 promoted route materialization이었다.

## 2026-07-01 Docker Route Materialization

목적:

Docker 안에서 promoted route rows를 재생성해, host-only smoke가 아니라 재현 가능한 experiment input을
만들 수 있는지 확인했다.

결과:

Docker materialization으로 총 `6952` rows를 생성했다. 구성은 `relative_vertical 1512`,
`size_relative 2400`, `relative_horizontal 2400`, `support_contact 640`이다. Validation errors는 `0`이고,
model-safe view는 `T_e + G_e` compatibility input으로 제한했다. 다음 step은 materialization schema/shortcut
audit와 grouped split/evaluation이다.
