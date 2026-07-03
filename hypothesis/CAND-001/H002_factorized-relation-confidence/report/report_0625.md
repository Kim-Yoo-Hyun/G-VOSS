# H002 Direction Transition Report

Date: 2026-06-25 KST

Working title:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## 1. Existing H002

기존 H002는 relation source가 제공하는 하나의 confidence score가 relation reliability를
충분히 설명하지 못한다는 문제에서 출발했다.

초기 핵심 명제는 다음이었다.

```text
semantic score != geometry validity != relation reliability
```

이를 검증하기 위해 H002는 `RGA(Relation-Geometric Agreement)` framework를 만들고,
relation candidate를 semantic axis, geometry axis, coverage, uncertainty, audit label로
분해했다.

초기 method 후보는 다음 posterior였다.

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

여기서:

- `S_e`: source semantic score/rank
- `G_e`: geometry validity or geometry evidence
- `C_e`: coverage
- `U_e`: uncertainty
- `R_e`: relation reliability

기존 실험 route는 human/audit reliability target을 만들고, 그 target이 shortcut 없이
독립적이면 factorized posterior smoke를 실행하는 방식이었다.

## 2. What Was Learned

v1-v81의 target construction 과정에서 다음 사실이 반복적으로 확인됐다.

1. row count 자체는 여러 relation family에서 충분했다.
2. 그러나 accept/reject target은 positive-sparse하게 형성되는 경우가 많았다.
3. target label은 predicate, rank band, endpoint pair, object family, geometry status,
   construction metadata로 쉽게 설명되는 경우가 많았다.
4. shortcut을 막기 위해 control을 강하게 걸면 mixed positive/negative strata가 부족해졌다.
5. `attached to`, `hanging on`, `connected to`는 metric geometry만으로 신뢰 가능한
   reliability label을 만들기 어렵다.
6. RGA benchmark/failure taxonomy는 diagnostic으로는 필요하지만, 단독으로 top-tier method
   novelty를 만들기에는 약하다.

따라서 기존 route의 병목은 posterior combiner가 약해서가 아니라, **posterior가 학습할
독립 reliability target을 현재 방식으로 안정적으로 만들기 어렵다**는 데 있었다.

## 3. Why The Direction Changes

기존 H002는 relation reliability를 예측하려 했지만, 실제로 더 근본적인 문제는
`G_e`와 `C_e`가 충분히 잘 정의되지 않았다는 점이다.

즉 질문을 다음처럼 바꿔야 한다.

기존 질문:

```text
Can a factorized posterior predict human/audit relation reliability labels?
```

새 질문:

```text
Can we learn predicate-geometry compatibility by separating semantic evidence,
geometry-only evidence, and observability quality?
```

이 전환은 H002의 핵심 주장을 버리는 것이 아니다. 오히려 기존 factorized claim을 더
강하게 구현한다.

기존 H002의 약점:

```text
S_e, G_e, C_e, U_e를 나눴지만 실제 학습 route는 flat posterior target fitting에 가까웠다.
```

새 H002의 강점:

```text
T_e, Z_e, G_e, C_e, Q_e를 구조적으로 분리하고,
C_e를 source score 없이 counterfactual compatibility learning으로 학습한다.
```

## 4. New H002

새 H002는 다음 구조로 진행한다.

```text
Geometry-only evidence encoder -> G_e
Semantic-content encoder -> T_e
Source-confidence encoder -> Z_e
Contrastive compatibility head: compatibility(T_e, G_e) -> C_e
Evidence-quality head -> Q_e
Two-head decision -> p_obs, p_rel
```

### 4.1 Geometry-Only Evidence Encoder

입력:

- object-pair point/mesh feature
- distance, height, overlap, contact, containment
- visibility-independent geometry

출력:

```text
G_e
```

중요한 원칙:

- predicate와 source score는 geometry encoder에 넣지 않는다.
- `G_e`는 source confidence shortcut을 배우지 않아야 한다.
- H001 `p_geom_valid`는 rule-based geometry evidence baseline 또는 teacher signal로
  재사용할 수 있다.

### 4.2 Semantic-Content Encoder

입력:

- predicate text/label
- subject/object class
- relation family

출력:

```text
T_e
```

`T_e`는 relation의 의미 내용만 표현한다. Source score, rank, source id는 넣지 않는다.

### 4.3 Source-Confidence Encoder

입력:

- source score/rank
- source id
- source-specific calibration metadata

출력:

```text
Z_e
```

`Z_e`는 final reliability head에는 들어갈 수 있지만 compatibility head에는 넣지 않는다.
이렇게 해야 compatibility가 기존 relation score를 복사하지 않는다.

### 4.4 Contrastive Compatibility Head

입력:

```text
T_e, G_e
```

출력:

```text
C_e = semantic-geometry compatibility
```

금지:

```text
C_e must not use Z_e
```

학습:

- GT / audit-accepted / high-precision verified positive vs hard counterfactual
- true pair vs wrong-pair geometry
- shuffled geometry
- subject/object swap
- predicate flip
- same-scene hard negative
- same-family/rank matched negative

이 head의 목적은 relation label을 다시 맞추는 것이 아니라, predicate가 요구하는 geometry
evidence와 실제 object-pair geometry가 호환되는지 학습하는 것이다.

### 4.5 Evidence-Quality Head

입력:

- view availability
- same-frame visibility
- mesh completeness
- point coverage
- evidence agreement/conflict
- missing or unsupported state

출력:

```text
Q_e = evidence quality / observability
```

기존 `coverage`와 `uncertainty`는 `Q_e` 안에서 함께 다룬다.

### 4.6 Two-Head Reliability Decision

최종 decision은 reliability와 abstain을 분리한다.

```text
p_obs = P(evidence is sufficient to decide | Q_e)
p_rel = P(relation is reliable | evidence is observable, Z_e, C_e, optional T_e)
```

결정:

```text
p_obs low -> abstain
p_obs high and p_rel high -> accept
p_obs high and p_rel low -> reject
```

기본 relation energy:

```text
E_rel(e) = E_src(Z_e) + E_comp(C_e) + E_interaction(Z_e, C_e, T_e)
p_rel = sigmoid(-E_rel(e))
```

`E_geom(G_e)`는 기본 relation validity term으로 쓰지 않는다. Predicate를 모르는 geometry
자체만으로 relation 성립 여부를 판단할 수 없기 때문이다. 남긴다면 point cloud 누락,
mesh artifact, impossible overlap 같은 geometry 품질/아티팩트 penalty로만 쓴다.

## 5. Relation To Prior H002 Artifacts

기존 artifact는 폐기하지 않는다. 역할이 바뀐다.

| Existing Artifact Type | New Role |
| --- | --- |
| RGA rows | mismatch diagnosis and evaluation axis |
| human/audit labels | evaluation/calibration subset and high-precision positive source |
| `p_geom_valid` | geometry-only rule baseline or teacher |
| target-independence audits | shortcut-control design evidence |
| v1-v81 stage logs | evidence that target-first posterior route is weak |
| multi-view/mesh packets | future `Q_e` and hard-relation evidence, not immediate main input unless controlled |

## 6. Novelty Position

새 H002의 novelty는 "Transformer를 썼다" 또는 "semantic과 geometry를 결합했다"가 아니다.

주장해야 할 novelty:

```text
Existing relation confidence conflates semantic plausibility and geometric support.
We learn predicate-geometry compatibility from geometry-only evidence and semantic/source evidence,
then compute relation reliability with source confidence separated from compatibility
and observability handled as a selective decision head.
```

핵심 차별점:

1. geometry encoder에서 predicate/source score를 제외해 `G_e`를 독립 evidence로 만든다.
2. semantic content `T_e`와 source confidence `Z_e`를 분리한다.
3. `C_e = compatibility(T_e, G_e)`에서는 `Z_e`를 금지한다.
4. `Q_e`를 통해 evidence 부족과 true contradiction을 분리한다.
5. final decision은 `p_obs`와 `p_rel` 두 head로 계산한다.

## 2026-06-25 Method Contract And Factor Split

목적:

기존 posterior fitting 방향이 target shortcut에 막혔기 때문에, H002를 `semantic score`와
`geometry validity`의 단순 결합이 아니라 `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`, `p_obs`, `p_rel`로
분리된 compatibility-learning framework로 다시 고정했다.

결과:

`G_e`에는 predicate/source score를 넣지 않고, `T_e`와 `Z_e`를 분리하며, `C_e = compatibility(T_e, G_e)`에는
`Z_e`를 금지하는 원칙을 세웠다. 기존 RGA/audit/p_geom_valid 산출물은 폐기하지 않고 각각 diagnostic,
evaluation subset, geometry-only baseline/teacher 역할로 재배치했다. 다음 step은 이 계약에 맞는 prototype
schema와 counterfactual protocol을 만드는 것이었다.

## 2026-06-25 Prototype Dataset And Baseline Smoke

목적:

새 H002 구조가 실제 row schema로 표현되는지 확인하고, source-only / geometry-only / simple fusion / compatibility
view가 분리 가능한지 train-only prototype으로 먼저 검증했다.

결과:

초기 prototype과 smoke baseline은 row materialization과 기본 metric plumbing을 통과했다. Learned smoke에서는
`T+G` compatibility가 source-only, `p_geom_valid`, geometry-only보다 강하게 보였지만, family/predicate shortcut과
observability/reliability target independence가 아직 불안정했다. 다음 step은 hard relation인 attachment 계열에서
numeric `G_e`가 의미 있는지 확인하는 것이었다.

## 2026-06-25 Attachment Numeric Geometry Probe

목적:

`attached to`, `hanging on`, `connected to`에서 hand-crafted numeric geometry가 `C_e` evidence로 쓸 수 있는지 확인했다.
특히 source score를 복사하지 않고 predicate-independent `G_e`가 compatibility signal을 제공하는지 보려 했다.

결과:

Attachment numeric smoke에서는 `T+G`와 full factorized view가 높게 나왔지만, hidden construction probe도 높게 나왔다.
Strict hidden-cell balanced slice에서는 signal이 유지됐으나 row 수가 작았다. 따라서 이 branch는 paper-level reliability
근거가 아니라 diagnostic geometry-proxy evidence로 유지하고, independent visual/mesh audit label을 만들기로 했다.

## 2026-06-25 Attachment Independent Audit Attempt

목적:

Attachment proxy target이 construction-defined라는 문제를 피하기 위해, visible packet 기반의 independent accept/reject/abstain
label을 만들고 `C_e`, `Q_e`, `p_obs`, `p_rel` target으로 ingestion하려 했다.

결과:

초기 independent audit은 positive-sparse했고 target-independence audit에서 construction/source/visible semantic shortcut risk가
크게 남았다. Full candidate를 늘려도 controlled contrast가 거의 없었기 때문에, 단순 label relaxation이나 posterior smoke는
금지했다. 다음 step은 positive anchor를 새로 mining해 mixed strata를 확보하는 것이었다.

## 2026-06-26 Attachment Positive-Anchor Repair

목적:

Positive만 더 모으는 방식이 아니라, source score/rank와 무관하게 visual/mesh evidence 기준으로 clear accept와 hard reject가
같이 존재하는 mixed strata를 만들 수 있는지 확인했다.

결과:

560-row positive-anchor packet은 class mass gate를 가까스로 통과했지만, target-independence audit에서 strict/diagnostic clear
slice가 없었다. 즉 positive 수는 늘었지만 label이 여전히 construction/provenance/visible semantic shortcuts와 얽혀 있었다.
Attachment는 posterior smoke 없이 diagnostic/future route로 고정했고, H002 main은 `C_e` mechanism 검증으로 좁혔다.

## 2026-06-26 Compatibility Dataset v2

목적:

Attachment 대신 `support_contact`와 `relative_vertical`을 중심으로 `C_e = compatibility(T_e, G_e)`가 source/semantic shortcut 없이
검증될 수 있는지 v2 dataset을 만들었다.

결과:

v2는 schema shortcut을 줄인 뒤 learned smoke까지 진행했지만, 실패 원인이 명확했다. Target이 predicate-conditioned
compatibility가 아니라 geometry perturbation detection으로 풀렸다. Geometry-only가 강하고 wrong-predicate control이 무너지지
않았기 때문에, 더 강한 combiner를 쓰기 전에 target definition을 바꿔야 했다. 다음 step은 same-geometry multi-predicate contrast였다.

## 2026-06-26 Compatibility Dataset v3 Relative-Vertical

목적:

같은 `G_e`를 두 predicate 후보와 결합해 하나는 compatible, 하나는 incompatible이 되도록 만들어, geometry-only로는 풀 수 없고
`T_e x G_e` interaction이 필요한 target을 만들고자 했다.

결과:

`higher than` / `lower than` same-geometry contrast는 shortcut audit을 통과했고, learned smoke에서 compatibility interaction은
AUROC `1.0` 수준, geometry-only와 semantic/source baselines는 near chance였다. wrong-T와 shuffled-G controls도 무너졌다. 따라서
`relative_vertical`은 scoped train-only `C_e` mechanism proof로 받아들였다.

## 2026-06-26 Support/Contact Evidence Probe

목적:

`support_contact`를 바로 learned smoke로 넣으면 v2의 geometry-perturbation failure가 반복될 수 있어, 먼저 어떤 evidence가 필요한지
점검했다.

결과:

Numeric OBB/distance/overlap만으로는 role, orientation, contact direction, surface normal, mesh/visual evidence가 부족했다. Source
inventory와 mesh/pose/contact feature probe를 진행한 결과, `lying on` vs `standing on`은 pose-conditioned contrast 후보가 될 수
있지만 `supported by`는 superordinate overlap 때문에 clean binary target으로 쓰기 어렵다고 판단했다.

## 2026-06-26 Support/Contact Pose-Conditioned C_e

목적:

`standing on`과 `lying on`을 같은 support/contact family로 뭉개지 않고, pose-conditioned same-`G_e` contrast로 predicate-geometry
compatibility를 검증했다.

결과:

`lying on` / `standing on` pose-conditioned target은 schema/shortcut audit을 통과했고, learned smoke에서 compatibility interaction이
강하게 통과했다. 다만 target이 constructed mechanism proof이므로 broad relation reliability나 paper-level evidence로 승격하지 않았다.
`support_contact`는 main compatibility-route evidence지만 fully solved family는 아니라고 정리했다.

## 2026-06-27 Multi-Family Synthesis

목적:

`relative_vertical`과 `support_contact_pose_conditioned` 결과를 하나의 H002 claim으로 합칠 수 있는지, 또는 relation family를 더
추가해야 하는지 판단했다.

결과:

두 family 모두 predicate-independent `G_e`만으로는 부족하고 `C_e = compatibility(T_e, G_e)`가 필요하다는 mechanism evidence를
보였다. 그러나 아직 broad relation reliability, calibrated `p_rel/p_obs`, all-family generality, paper-level Docker evidence는 막았다.
다음 step은 constructed same-`G_e` mechanism proof를 넘어 independent validity target을 만들 수 있는지 확인하는 것이었다.

## 2026-06-27 Independent Validity Target Attempt

목적:

`C_e`가 constructed target뿐 아니라 GT-anchored independent validity target에서도 의미 있는지 확인하려 했다. No-GT를 negative로
쓰지 않고, GT-supported positive와 hard negative를 분리하는 방향을 택했다.

결과:

초기 independent validity target은 row 수는 충분했지만 predicate/class-pair shortcuts가 강했다. Exact semantic-stratum repair를 통해
`relative_vertical` 중심 target은 안정화됐고 `C_e` smoke가 강하게 통과했다. 반면 `support_contact`는 exact-stratum capacity가 작아
diagnostic slice로만 남았다.

## 2026-06-27 Calibration And Support/Contact Balancing

목적:

Independent validity smoke의 calibration 해석을 바로 posterior claim으로 올려도 되는지 확인하고, support/contact를 primary
independent-validity family로 복구할 수 있는지 추가로 검사했다.

결과:

Calibration metric 정의는 일부 수정됐지만, target이 train-only `C_e`이므로 calibrated `p_rel/p_obs` claim은 여전히 금지했다.
Support/contact balancing은 predicate-level balance까지는 가능했지만 object-class composition shortcut이 너무 강했다. Strict
predicate-class repair capacity도 88 rows에 그쳐 main learned smoke로는 부족했다.

## 2026-06-27 Scope Synthesis

목적:

Support/contact independent-validity repair가 막힌 뒤, H002가 현재 어디까지 주장할 수 있는지 정리했다.

결과:

현재 허용되는 claim은 train-only predicate-conditioned compatibility `C_e` evidence다. `relative_vertical`은 가장 강한 independent-validity
mechanism evidence이고, `support_contact_pose_conditioned`은 constructed compatibility-route evidence로 남긴다. `support_contact`
independent-validity, attachment-like hard relations, calibrated posterior, held-out/test result는 아직 막혀 있다. 다음 step은 independent
target source decision과 이후 paper-level promotion gate를 별도로 설계하는 것이다.
