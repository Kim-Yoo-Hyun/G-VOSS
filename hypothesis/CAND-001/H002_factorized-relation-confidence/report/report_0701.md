# H002 Hypothesis Report, 2026-07-01

## 1. 현재 가설과 방법

H002의 현재 연구명은 다음으로 둔다.

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

핵심 claim은 다음이다.

```text
3D Scene Graph relation reliability는 source confidence 하나나 고정된 semantic-geometry fusion으로 판단할 수 없다.
Relation family마다 필요한 evidence route가 다르며, 어떤 relation은 geometry-only로 충분하고,
어떤 relation은 predicate-geometry compatibility가 필요하며, 어떤 relation은 observability-aware abstention이나
semantic/structural reasoning이 필요하다.
```

현재 H002는 relation reliability를 다음 factor로 분리한다.

| Factor | 의미 | 현재 원칙 |
| --- | --- | --- |
| `T_e` | predicate/object semantic content | source score/rank를 넣지 않음 |
| `Z_e` | source confidence/rank | `C_e`에는 금지, 최종 reliability에는 later protocol에서만 사용 가능 |
| `G_e` | predicate-independent geometry evidence | predicate/source confidence를 넣지 않음 |
| `C_e` | compatibility between `T_e` and `G_e` | 현재 핵심 검증 대상 |
| `Q_e` | observability / evidence quality | relation truth가 아니라 판단 가능성 담당 |
| `p_obs` | evidence가 판단 가능한지 | 낮으면 abstain |
| `p_rel` | observable 조건에서 relation이 reliable한지 | accept/reject 판단 |

현재 핵심 method는 `C_e = compatibility(T_e, G_e)`를 먼저 검증하고, 이후 `Q_e`, `Z_e`를 포함한 `p_obs`, `p_rel` selective decision으로 확장하는 구조다.

## 2. 실험 목적

Hypothesis 단계의 목적은 paper-level SOTA 성능을 주장하는 것이 아니라 다음을 검증하는 것이다.

1. Relation confidence를 semantic/source score 하나로 보는 것이 충분하지 않은가.
2. Predicate-independent geometry evidence `G_e`와 semantic content `T_e`를 분리해도 relation validity를 설명할 수 있는가.
3. Relation family마다 필요한 evidence route가 다른가.
4. `T_e x G_e` interaction이 semantic-only, geometry-only, simple concat보다 의미 있는가.
5. Wrong predicate, shuffled geometry, wrong-pair geometry control에서 성능이 무너지는가.
6. 어떤 relation type은 learned compatibility가 아니라 geometry-only, observability-aware, decomposition/abstain route로 분류해야 하는가.

사용한 evidence는 train-side hypothesis artifacts다. 현재까지 official validation/test나 paper-level grouped heldout result는 사용하지 않았다.

## 3. 검증 지표와 비교군

주요 지표는 다음이다.

| 목적 | 지표 |
| --- | --- |
| binary compatibility/reliability | AUROC, AUPRC, accuracy, balanced accuracy, F1 |
| calibration 후보 | Brier, ECE-10 |
| shortcut audit | predicate/class/source/metadata majority accuracy, allowed-field shortcut warning |
| counterfactual control | wrong-T, shuffled-G, wrong-pair geometry degradation |
| split readiness | `cv_group_id` group count, mixed-label group count, group majority accuracy |

주요 비교군은 다음이다.

| 비교군 | 의미 |
| --- | --- |
| semantic-only `T_e` | predicate/object semantic만 사용 |
| source-only `Z_e` | source score/rank만 사용 |
| geometry-only `G_e` | predicate 없이 geometry만 사용 |
| simple concat `T_e + G_e` | interaction 없이 결합 |
| compatibility interaction `T_e x G_e` | predicate-conditioned geometry compatibility |
| factorized `T_e/Z_e/G_e/Q_e` | full factorized ablation |
| wrong-T control | geometry는 그대로 두고 predicate를 틀리게 넣음 |
| shuffled-G control | predicate와 geometry alignment를 깨뜨림 |
| wrong-pair geometry | 다른 object pair geometry를 붙임 |

현재 가장 중요한 비교는 `T_e x G_e`가 `T_e-only`, `G_e-only`, `T+G concat`, `wrong-T`, `shuffled-G`보다 나은지다.

## 4. 검증한 relation type과 기준

Relation family는 같은 target으로 모두 묶지 않고, 필요한 evidence route 기준으로 분류했다.

| Route | Relation type | 현재 역할 |
| --- | --- | --- |
| predicate-geometry compatibility | `higher than`, `lower than` | main candidate |
| predicate-geometry compatibility | `bigger than`, `smaller than` | main candidate |
| frame-aware compatibility | `left`, `right`, `front`, `behind` | main candidate |
| challenging compatibility | `standing on`, `lying on` | main evidence with caveat |
| geometry-only route | `close by` | control / route taxonomy evidence |
| superordinate decomposition | `supported by` | diagnostic / relabel / abstain route |
| observability-aware route | `attached to`, `hanging on`, `connected to` | diagnostic / future route |
| deferred feasibility | containment, cover, leaning, identity/symmetry, semantic/structural relations | future / separate route |

Main candidate로 올리는 기준은 다음이다.

1. binary target이 label-balanced이거나 최소한 evaluation 가능할 것.
2. `T_e + G_e` allowed view에 hidden/source/construction leakage가 없을 것.
3. semantic-only/source-only/geometry-only shortcut이 target을 쉽게 풀지 못할 것.
4. `T_e x G_e` interaction이 controls 대비 의미 있게 좋아질 것.
5. wrong-T 또는 shuffled-G에서 성능이 떨어질 것.
6. grouped split을 만들 수 있을 만큼 `cv_group_id`와 mixed-label group이 충분할 것.

## 5. 현재까지 잘 된 부분

### 5.1 Relative Vertical

대상 relation은 `higher than`, `lower than`이다.

Repaired independent-validity target에서 train-only grouped-CV smoke가 통과했다.

| Model | AUROC |
| --- | ---: |
| semantic-only `T_e` | 0.416 |
| source-only `Z_e` | 0.568 |
| geometry-only `G_e` | 0.527 |
| simple concat `T+G` | 0.480 |
| compatibility interaction `T_e x G_e` | 0.996 |
| shuffled-G global | 0.515 |
| wrong predicate control | 0.027 |

해석: predicate와 geometry가 올바르게 align될 때만 성능이 높아진다. Geometry-only나 semantic/source-only가 아니라 compatibility signal이 핵심이라는 H002 claim을 가장 깔끔하게 지지한다.

### 5.2 Size Relative

대상 relation은 `bigger than`, `smaller than`이다.

| Model / result | 값 |
| --- | ---: |
| primary compatibility AUROC | 0.9999 |
| accuracy | 0.9933 |
| positive / negative | 1200 / 1200 |

해석: size relation은 same-G predicate flip 구조에서 매우 clean한 compatibility route다. 단, task가 너무 clean하기 때문에 paper에서는 strong positive evidence로 쓰되, 이것만으로 broad reliability claim을 만들면 안 된다.

### 5.3 Relative Horizontal

대상 relation은 `left`, `right`, `front`, `behind`이다.

| Model / result | 값 |
| --- | ---: |
| primary compatibility AUROC | 1.0000 |
| accuracy | 1.0000 |
| positive / negative | 1200 / 1200 |

해석: frame-aware relation도 route-specific target을 만들면 clean하게 풀린다. 단, 최종 paper에서는 reference-frame 정의와 `front/behind` ambiguity를 명시해야 한다.

### 5.4 Support / Contact

대상 relation은 `standing on`, `lying on`이다.

| Model | AUROC |
| --- | ---: |
| semantic-only `T_e` | 0.442 |
| point/contact geometry-only | 0.470 |
| simple `T+G` concat | 0.435 |
| predicate-geometry interaction | 0.699 |
| factorized observability | 0.695 |
| wrong-T same-G | 0.273 |
| shuffled-G global | 0.506 |

해석: 절대 성능은 clean pass라고 보기 어렵지만, 패턴은 중요하다. Geometry-only와 concat은 실패하고, `T_e x G_e` interaction만 의미 있게 오른다. 따라서 support/contact는 “fully solved”가 아니라 “compatibility interaction이 필요한 challenging route”로 두는 것이 맞다.

### 5.5 Docker Materialization / Schema Audit

2026-07-01 기준으로 promoted route candidate pool을 Docker에서 materialize하고 schema audit까지 통과했다.

| Route family | Rows | Label 0 | Label 1 | Split ready |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 1512 | 756 | 756 | True |
| `size_relative` | 2400 | 1200 | 1200 | True |
| `relative_horizontal` | 2400 | 1200 | 1200 | True |
| `support_contact` | 640 | 320 | 320 | True |

Audit result:

| Check | Count |
| --- | ---: |
| schema errors | 0 |
| blocked `C_e` field hits in `T_e + G_e` | 0 |
| high-risk `C_e` allowed shortcut warnings | 0 |
| shortcut probes | 50 |

해석: H002는 hypothesis-stage route-specific smoke에서 paper-promotion 준비 단계로 넘어갈 최소 조건을 만족했다. 다만 아직 grouped heldout metric은 없다.

## 6. 잘 안 된 부분과 이유

### 6.1 초기 posterior target route

초기에는 `P(edge reliability | semantic evidence, geometry evidence, coverage, uncertainty)` 형태의 posterior를 바로 검증하려 했다. 하지만 v1-v81 과정에서 독립 reliability target이 반복적으로 positive-sparse하거나 shortcut-prone하게 형성됐다.

문제 원인:

- accept/reject가 predicate, class pair, source rank, construction bucket으로 쉽게 맞춰짐.
- `abstain/uncertain`이 너무 많아 binary usable row가 부족한 경우가 많았음.
- target이 relation reliability가 아니라 target construction rule을 학습할 위험이 컸음.

결론: posterior combiner를 먼저 키우는 대신, `T_e`, `G_e`, `C_e`, `Q_e`, `Z_e`를 분리하고 route-specific target을 먼저 검증하는 방향으로 전환했다.

### 6.2 Close By

`close by`는 normalized distance만으로 AUROC 1.0에 가까웠다.

해석:

- 실패가 아니라 geometry-only route라는 뜻이다.
- `T_e x G_e` interaction을 증명하는 main target으로는 부적합하다.
- H002 route taxonomy에서는 “어떤 relation은 geometry-only route로 충분하다”는 control evidence로 사용한다.

### 6.3 Supported By

`supported by`는 broad superordinate relation이다.

관찰:

- `p_obs`는 Q/observability로 잘 설명된다.
- observable `p_rel`에서는 geometry/Q가 너무 강하거나 target construction signal이 강하다.
- hidden construction fields는 audit-only에서 매우 강한 shortcut이 된다.

해석:

- clean binary compatibility target으로 두기 어렵다.
- `standing on`, `lying on`, `attached support`, `abstain/relabel`로 decomposition하는 route가 더 적절하다.

### 6.4 Attachment-like Relations

대상은 `attached to`, `hanging on`, `connected to`였다.

문제:

- `attached to`는 accept-only 또는 class-pair shortcut 문제가 반복됐다.
- `hanging on`은 일부 repair 가능성이 있었지만 class-pair shortcut risk가 남았다.
- `connected to`는 physical topology/functional evidence가 부족해 diagnostic에 머물렀다.

해석:

- 이 family는 `C_e` binary target보다 `Q_e`, visual/mesh observability, topology evidence가 먼저 필요하다.
- 현재는 main learned target이 아니라 observability-aware future route가 맞다.

## 7. 현재 결론

현재 hypothesis-level 결론은 다음이다.

1. H002의 핵심 주장인 `semantic score != geometry validity != relation reliability`는 여전히 유효하다.
2. 더 정확한 framing은 fixed fusion이 아니라 relation-aware evidence routing이다.
3. `relative_vertical`, `size_relative`, `relative_horizontal`은 clean compatibility route로 강하다.
4. `support_contact`는 interaction 필요성을 보여주는 challenging route evidence다.
5. `close by`는 geometry-only route control로 유효하다.
6. `supported by`와 attachment-like relations는 decomposition/observability route로 남겨야 한다.
7. 아직 paper-level claim은 아니다. Docker materialization과 schema audit은 통과했지만 grouped heldout evaluation과 calibration/selective decision은 아직 없다.

## 8. 다음 단계

바로 다음 TODO는 다음이다.

```text
compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit
```

해야 할 일:

1. `6952` materialized rows에 대해 grouped split protocol을 만든다.
2. split group은 `cv_group_id`를 기본으로 사용한다.
3. 같은 group/endpoint/source row가 train/dev/heldout에 동시에 들어가지 않도록 한다.
4. route family별 label balance와 group count를 split manifest에 기록한다.
5. official validation/test가 아니라 H002 candidate-pool internal grouped split임을 명시한다.
6. 이후 Docker grouped evaluation을 실행한다.

그 다음 단계:

1. `C_e` grouped heldout metrics:
   - semantic-only
   - geometry-only
   - `T+G` concat
   - `T x G` compatibility
   - wrong-T
   - shuffled-G
2. support/contact failure taxonomy:
   - standing/lying ambiguity
   - point/contact evidence insufficiency
   - Q_e rescue risk
3. optional calibration:
   - `p_rel`
   - `p_obs`
   - ECE/Brier/NLL/selective risk
4. claim wording lock:
   - framework-ready인지 paper-result-ready인지 분리
   - all-family solved claim 금지
   - relation-aware route taxonomy claim으로 제한

## 9. 추후 더 진행하면 좋은 내용

추가 검증 후보는 다음 순서가 좋다.

1. Grouped heldout evaluation:
   현재 hypothesis smoke가 train-only이므로 가장 먼저 필요하다.

2. Human/visual audit target:
   GT match와 human-audited reliability target을 연결해야 reviewer가 “기존 GT 기준 성능은?”이라고 물었을 때 답할 수 있다.

3. `Q_e` and abstention:
   `attached to`, `hanging on`, `connected to`, `inside`, `cover`는 binary `C_e`보다 observability-aware abstention이 더 적합하다.

4. Multi-view / mesh evidence:
   바로 learned visual encoder로 넣기보다 audit evidence와 `Q_e` materialization부터 시작해야 한다.

5. Predicate-conditioned point/mesh encoder:
   support/contact와 attachment에서 hand-crafted geometry evidence가 부족하면 `predicate-guided geometry evidence`를 학습하는 방향을 검토할 수 있다.

6. Existing GT relation match:
   `GT match & reliability accept/reject`, `No GT & reliability accept/reject`, `Abstain` table을 만들면 기존 GT-only evaluation의 incomplete annotation 문제를 분석할 수 있다.

7. Route taxonomy expansion:
   containment, cover, leaning, identity/symmetry, part-of/belonging-to는 같은 binary compatibility target으로 넣지 말고 route definition을 먼저 설계해야 한다.

## 10. 현재 claim boundary

현재 말할 수 있는 것:

```text
Hypothesis-stage evidence supports a relation-aware compatibility framework:
different 3D scene graph relation families require different evidence routes, and several route-specific targets show that predicate-geometry compatibility can outperform semantic-only, geometry-only, and naive fusion baselines under counterfactual controls.
```

아직 말하면 안 되는 것:

```text
H002 improves 3DSSG performance on official validation/test.
H002 solves all relation types.
H002 produces calibrated relation reliability posterior.
H002 has paper-level grouped heldout metrics.
Attachment/connected/support-superordinate relations are solved.
```

다음 grouped split과 Docker evaluation이 완료되어야 H002를 paper-result-ready 방향으로 판단할 수 있다.

## 2026-07-01 Grouped Split Protocol

목적:

H002 candidate pool 안에서 scan/endpoint leakage를 막고, train/dev/heldout을 분리해 internal heldout 평가를 할 수 있는지 확인했다.
이 단계는 official validation/test가 아니라 hypothesis-stage grouped split gate다.

결과:

총 `6952` materialized rows를 grouped split했고 group leakage는 없었다. Split은 `relative_horizontal`, `relative_vertical`,
`size_relative`, `support_contact`를 포함한다. 다음 step은 metric runner가 아니라, 어떤 model view와 controls를 평가할지 먼저
고정하는 grouped evaluation protocol이었다.

## 2026-07-01 Grouped Evaluation Protocol

목적:

Grouped split 결과를 바로 metric으로 돌리기 전에, `C_e` claim에 허용되는 input과 비교군을 고정했다. 특히 source confidence `Z_e`와
observability `Q_e`가 compatibility metric에 섞이지 않도록 막는 것이 중요했다.

결과:

Main `C_e` metric은 `T_e`와 `G_e`만 사용하도록 고정했다. 비교군은 semantic-only, geometry-only, plain concat, `T_e x G_e`
compatibility, wrong-`T`, shuffled-`G` control이다. `Z_e`는 source-confidence baseline/final reliability용으로, `Q_e`는 selective
abstention용으로 분리했다.

## 2026-07-01 Grouped Evaluation Runner

목적:

고정된 grouped protocol로 internal heldout에서 `T_e x G_e` compatibility가 baselines와 controls보다 강한지 확인했다.

결과:

전체 heldout에서는 `M4_TxG_compatibility`가 AUROC `0.925990`으로 강했고, wrong-`T`와 shuffled-`G` controls는 무너졌다. 하지만
family별로 보면 `size_relative`와 `relative_horizontal`은 강하고, `support_contact`는 partial, `relative_vertical`은 실패처럼 보였다.
다음 step은 aggregate success가 아니라 family별 result review였다.

## 2026-07-01 Grouped Evaluation Result Review

목적:

전체 평균이 좋은 결과를 그대로 claim으로 올리지 않고, family별로 claim-supporting / partial / failed 상태를 구분했다.

결과:

`size_relative`와 `relative_horizontal`은 main internal compatibility evidence로 유지했다. `support_contact`는 challenging route로
해석했고, `relative_vertical`은 failure analysis가 필요하다고 판단했다. 다음 step은 relative-vertical failure가 scientific negative인지
implementation issue인지 확인하는 것이었다.

## 2026-07-01 Relative-Vertical Failure Analysis

목적:

`relative_vertical`이 이전 train-only smoke에서는 강했는데 grouped heldout에서 실패한 이유를 확인했다.

결과:

실패 원인은 method failure가 아니라 feature extractor bug였다. Runner가 실제 `center_delta_z` 값을 읽지 않고 availability mask를
먼저 잡아 `predicate_sign * 1.0`에 가까운 feature를 만들고 있었다. 따라서 `relative_vertical`을 제외하지 않고 explicit raw geometry
path를 읽도록 runner를 수정하기로 했다.

## 2026-07-01 Grouped Eval Feature Extractor Repair

목적:

Suffix 기반 numeric lookup을 제거하고, relation-specific geometry를 explicit raw path에서 읽도록 고쳐 grouped evaluation을 다시 실행했다.

결과:

Repair 후 `relative_vertical` AUROC는 `0.999921`로 회복됐다. Overall `M4_TxG_compatibility`는 AUROC `0.984976`이며, wrong-`T`와
shuffled-`G` controls도 적절히 무너졌다. `relative_horizontal`, `relative_vertical`, `size_relative`는 main internal evidence가 됐고,
`support_contact`는 partial/challenging으로 남겼다.

## 2026-07-01 Repaired Grouped-Eval Claim Boundary Review

목적:

Repaired grouped result를 어디까지 주장할 수 있는지 정리했다. Internal candidate-pool heldout과 paper-level official result를
구분하는 것이 핵심이었다.

결과:

허용 claim은 internal grouped holdout에서 `C_e = compatibility(T_e, G_e)`가 baselines와 controls보다 강하다는 것이다. 금지 claim은
official validation/test improvement, calibrated `p_rel/p_obs`, support/contact solved claim, all-relation generalization이다. 다음 step은
official validation/test protocol을 별도로 정의하는 것이었다.

## 2026-07-01 Official Validation/Test Protocol Plan

목적:

Internal grouped result를 paper-level result로 착각하지 않도록, official validation/test 사용 정책과 source protocol을 먼저 고정했다.

결과:

Official validation은 inventory/metric-freeze 대상으로 먼저 사용하고, test는 protocol과 wording이 모두 고정된 뒤 single final evaluation으로만
사용하기로 했다. Local test label은 없었고, validation에는 promoted families를 구성할 충분한 GT capacity가 있었다. 다음 step은 official
validation source inventory였다.

## 2026-07-01 Official Source Inventory

목적:

Official validation에서 H002 promoted routes를 구성할 수 있는지, GT relation과 object geometry, VL-SAT/Open3DSG source candidate가
join 가능한지 확인했다.

결과:

`relative_horizontal`, `relative_vertical`, `size_relative`, `support_contact` 모두 validation GT와 OBB pair coverage가 충분했다. 다만
H001 `p_geom_valid`는 `relative_horizontal`과 `size_relative`에 그대로 쓸 수 없기 때문에 H002용 `G_e`를 새로 구성해야 했다. 다음 step은
candidate materialization protocol freeze였다.

## 2026-07-01 Official Candidate Materialization Protocol

목적:

Official validation row를 만들기 전에 anchor, counterfactual, model-safe field, hidden field, source bridge 사용 원칙을 고정했다.

결과:

Official validation GT relation을 primary anchor로 사용하고, 같은 object pair에서 predicate counterfactual을 생성하는 방향을 택했다.
VL-SAT/Open3DSG rows는 source bridge/provenance로만 사용하고, `Z_e`, H001 `p_geom_valid`, construction buckets는 main `C_e` model-safe
view에서 제외했다. 다음 step은 Docker materialization이었다.

## 2026-07-01 Official Candidate Materialization Docker Implementation

목적:

Hypothesis 폴더의 host-only 산출물이 아니라 Docker 기반으로 official validation candidate rows를 재생성할 수 있는지 확인했다.

결과:

Docker materialization으로 `23062` rows를 생성했고 validation errors는 없었다. Family 구성은 `relative_horizontal 18764`,
`relative_vertical 780`, `size_relative 340`, `support_contact 3178`이다. 아직 metric은 계산하지 않았고, 다음 step은 schema/shortcut audit였다.

## 2026-07-01 Official Candidate Schema Audit

목적:

Official materialized model-safe view에 hidden construction field, label-derived field, source score, H001 `p_geom_valid`, GT leakage가
들어가지 않았는지 확인했다.

결과:

Schema violations와 blocked field hits는 없었다. 다만 `support_contact`에서 `predicate_x_class_pair` shortcut이 매우 강해
challenging/diagnostic route로만 해석해야 한다는 caveat가 남았다. 다음 step은 family imbalance와 controls를 반영한 metric protocol freeze였다.

## 2026-07-01 Official Metric Protocol Freeze

목적:

Official validation metric을 실행하기 전에 primary metric, aggregation, allowed input, controls, claim boundary를 고정했다.

결과:

Primary metric은 `macro_family_AUROC`로 고정했고, weighted/overall AUROC는 secondary로 두었다. Main `C_e` input은 `T_e`와 `G_e`만
허용했다. wrong-`T`, shuffled-`G`, subject/object swap, sign flip, horizontal frame control을 required control로 두고, `support_contact`는
solved claim에서 제외했다.

## 2026-07-01 Official Metric Runner

목적:

Frozen protocol에 따라 Docker official validation metric을 실행해 paper-level review 후보 결과를 만들었다.

결과:

Official validation에서 `M4_TxG_compatibility`는 macro-family AUROC `0.835547`, weighted-family AUROC `0.720781`, overall AUROC
`0.724835`를 보였다. Family별로는 `relative_vertical 0.991321`, `size_relative 0.999585`, `relative_horizontal 0.719568`,
`support_contact 0.631712`다. 이 결과는 생성됐지만 아직 paper-level result로 승격하지 않았고, 다음 step은 result review와 claim-boundary lock이다.
