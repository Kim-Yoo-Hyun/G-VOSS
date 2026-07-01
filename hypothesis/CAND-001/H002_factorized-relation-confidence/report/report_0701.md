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

## 11. 2026-07-01 추가 진행: Grouped Split Protocol

`compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit`를 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split
```

`6952`개 materialized row와 `3684`개 `cv_group_id` group을 내부 split으로 나누었다.

| Route family | Train rows | Dev rows | Heldout rows |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 1680 | 360 | 360 |
| `relative_vertical` | 1059 | 227 | 226 |
| `size_relative` | 1680 | 360 | 360 |
| `support_contact` | 449 | 97 | 94 |

누수 검증 결과:

- `cv_group_single_split` violation: `0`
- official validation/test usage: `0`
- split validation errors: `0`

해석:

- 이제 H002 candidate pool 안에서 grouped train/dev/heldout 분리는 준비됐다.
- 아직 성능 metric은 없다.
- 이 heldout은 official validation/test가 아니라 H002 내부 candidate-pool heldout이다.
- 다음 단계는 grouped evaluation protocol을 먼저 정의하는 것이다.

다음 단계에서 바로 실행할 비교군:

- semantic-only
- geometry-only
- `T_e + G_e` concat
- `T_e x G_e` compatibility
- wrong-`T_e` control
- shuffled-`G_e` control

`Q_e`와 `Z_e`는 아직 `C_e` metric에 섞지 않는다. `Q_e`는 selective /
abstention 평가에서, `Z_e`는 source-confidence baseline 또는 final reliability
head에서 별도로 검증한다.

## 12. 2026-07-01 추가 진행: Grouped Evaluation Protocol

`compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split`를 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_runner_after_protocol
```

이번 단계에서 한 일:

- `internal_train`, `internal_dev`, `internal_heldout` 사용 방식을 고정했다.
- `C_e` target의 model view를 고정했다.
- main `C_e`에서 사용할 수 있는 factor를 `T_e`, `G_e`로 제한했다.
- `Z_e`, `Q_e`는 diagnostic-only로 남겼다.
- required metrics와 breakdown을 고정했다.
- wrong-`T_e`, shuffled-`G_e` controls를 필수화했다.

이번 단계에서 하지 않은 일:

- grouped metric 실행하지 않음.
- official validation/test 사용하지 않음.
- paper-level result 생성하지 않음.
- `p_obs` / `p_rel` calibration claim 생성하지 않음.

다음 runner가 비교해야 하는 model view:

| View | 역할 |
| --- | --- |
| `M1_T_semantic_only` | semantic-content baseline |
| `M2_G_geometry_only` | geometry-only baseline |
| `M3_T_plus_G_concat` | simple fusion baseline |
| `M4_TxG_compatibility` | primary compatibility model |
| `C1_wrong_T_control` | semantic condition counterfactual |
| `C2_shuffled_G_control` | geometry counterfactual |

해석:

이제 H002는 metric 실행 직전 단계까지 왔다. 다음 단계에서 runner를 구현해도
되지만, 결과는 여전히 internal H002 candidate-pool heldout 결과로 표현해야 한다.
official validation/test 또는 paper-level claim으로 부르려면 별도의 external
evaluation protocol과 result-review가 필요하다.

## 13. 2026-07-01 추가 진행: Grouped Evaluation Runner

`compatibility_dataset_v3_grouped_eval_runner_after_protocol`를 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_result_review_after_runner
```

실행한 Docker command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval
```

출력 위치:

- `experiments/H002_compatibility_routing/evaluation/latest/`
- `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol/`

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

- 전체 aggregate에서는 `T_e x G_e` compatibility가 매우 강하게 보인다.
- wrong-`T_e`와 shuffled-`G_e` control이 무너져서, 단순한 source confidence 또는
  geometry-only shortcut만은 아니라는 근거가 있다.
- 하지만 relation family별로 보면 결과가 다르다.
- `size_relative`, `relative_horizontal`은 강한 compatibility-route evidence다.
- `support_contact`는 partial evidence이며 challenging route로 해석해야 한다.
- `relative_vertical`은 현재 target/feature/split 구성에서 실패했다.

따라서 다음 H002 TODO는 추가 model fitting이 아니라 result review다. Review에서는
family별로 claim-supporting, diagnostic, failed, target-repair-needed 상태를
나누고, official validation/test 또는 paper-level claim으로 확장하기 전에 어떤
external protocol이 필요한지 정해야 한다.

## 14. 2026-07-01 추가 진행: Grouped Evaluation Result Review

`compatibility_dataset_v3_grouped_eval_result_review_after_runner`를 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review
```

Family-level 판정:

| Family | Heldout M4 AUROC | Status | 현재 역할 |
| --- | ---: | --- | --- |
| `relative_horizontal` | 0.969537 | claim-supporting | main compatibility-route evidence |
| `relative_vertical` | 0.457834 | failed | repair/exclude 필요 |
| `size_relative` | 0.999969 | claim-supporting | main compatibility-route evidence |
| `support_contact` | 0.616395 | partial | challenging compatibility-route evidence |

해석:

- 전체 평균만 보면 H002의 `T_e x G_e` compatibility가 매우 강해 보인다.
- 하지만 family별로 보면 모든 relation이 같은 방식으로 풀리지 않는다.
- `size_relative`와 `relative_horizontal`은 현재 H002의 핵심 compatibility evidence로
  사용할 수 있다.
- `support_contact`는 의미 있는 partial signal이 있지만 solved relation family로
  주장하면 안 된다.
- `relative_vertical`은 현재 grouped heldout에서 실패했다. 특히 wrong-`T_e`와
  shuffled-`G_e` control이 compatibility signal을 충분히 입증하지 못한다.

따라서 다음 작업은 `relative_vertical` failure analysis다. 확인해야 할 항목은
target construction, predicate direction/sign feature, wrong-`T_e` control behavior,
split composition, 그리고 해당 family를 repair할지 main claim에서 제외할지의 판단이다.

## 15. 2026-07-01 추가 진행: Relative-Vertical Failure Analysis

`compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review`를
완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis
```

핵심 결과:

| Probe | Internal heldout AUROC |
| --- | ---: |
| intended `predicate_sign * raw_geometry_feature_vector.center_delta_z` | 1.000000 |
| runner suffix-based `center_delta_z` candidate | 0.504808 |
| reported grouped `M4_TxG_compatibility` | 0.457834 |

원인:

- grouped runner의 `numeric_value(..., "center_delta_z")`가 실제 raw z difference를
  읽지 않았다.
- 대신 `raw_geometry_feature_available_mask.center_delta_z=True`를 먼저 선택했다.
- 그래서 `C.sign_x_center_delta_z`가 `predicate_sign * actual_z_delta`가 아니라
  사실상 `predicate_sign * 1.0`이 됐다.

판단:

- `relative_vertical`을 main claim에서 제외할 단계가 아니다.
- 현재 실패는 scientific negative result가 아니라 implementation repair-needed 상태다.
- `higher than` / `lower than`은 predicate-conditioned geometry interpretation이 필요한
  대표 case이므로, H002 claim에는 오히려 중요한 family다.

다음 작업:

`h002-grouped-eval` runner가 suffix match가 아니라 explicit raw geometry path를 읽도록
수정하고, grouped evaluation을 재실행해야 한다.

## 16. 2026-07-01 추가 진행: Grouped Eval Feature Extractor Repair

`compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis`를
완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

수정 내용:

- grouped eval runner의 `compatibility_features()`에서 suffix 기반 numeric lookup을 제거했다.
- relation-specific geometry를 explicit raw path로 읽도록 수정했다.
- `center_delta_z`는 이제 `G_e_raw.raw_geometry_feature_vector.center_delta_z`를 읽는다.
- Docker `h002-grouped-eval`을 다시 실행했고, grouped runner/review validators도 다시 통과했다.

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

- `relative_vertical`은 repaired grouped result에서 강한 claim-supporting evidence가 됐다.
- 세 clean route인 `relative_horizontal`, `relative_vertical`, `size_relative`는
  `T_e x G_e` compatibility claim을 지지한다.
- `support_contact`는 여전히 partial/challenging으로 남기며 solved family로 주장하면 안 된다.
- 이 결과는 여전히 H002 internal candidate-pool heldout이며 official validation/test나
  paper-level result가 아니다.

## 17. 2026-07-01 추가 진행: Repaired Grouped-Eval Claim Boundary Review

`compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review`를 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

이 단계의 목적은 repaired grouped result를 그대로 paper claim으로 올리는 것이 아니라,
현재 가설 단계에서 허용되는 claim과 아직 막힌 claim을 분리하는 것이다.

허용되는 claim:

- `C_e = compatibility(T_e, G_e)`는 internal grouped holdout에서 semantic-only,
  geometry-only, plain concat, wrong-`T_e`, shuffled-`G_e`보다 강한 discrimination을
  보인다.
- relation family마다 필요한 evidence route가 다르므로, fixed semantic-geometry fusion
  하나로 모든 relation reliability를 판단하면 안 된다.
- `relative_horizontal`, `relative_vertical`, `size_relative`는 main internal
  compatibility evidence로 사용할 수 있다.
- `support_contact`는 partial/challenging evidence로만 둔다.

Family claim role:

| Family | Heldout M4 AUROC | 현재 claim role |
| --- | ---: | --- |
| `relative_horizontal` | 0.969568 | main internal compatibility evidence |
| `relative_vertical` | 0.999921 | main internal compatibility evidence |
| `size_relative` | 0.999969 | main internal compatibility evidence |
| `support_contact` | 0.610960 | partial/challenging evidence |

Blocked claim:

- official validation/test 개선 claim.
- calibrated `p_rel` / selective `p_obs` claim.
- `support_contact` solved claim.
- all-relation generalization claim.
- aggregate `M4` AUROC만으로 H002가 성립했다는 claim.

따라서 다음 단계는 official validation/test protocol plan이다. 즉, 어떤 official split과
source candidate를 사용할지, metric과 baseline/control을 어떻게 고정할지, 그리고 현재
internal candidate-pool 결과를 어떤 조건에서 paper metric으로 승격할 수 있는지 먼저
정의해야 한다.

## 18. 2026-07-01 추가 진행: Official Validation/Test Protocol Plan

`compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review`를
완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

이 단계는 official validation metric을 실행한 것이 아니라, official split 사용 정책과
metric/source protocol을 정의한 것이다.

정책:

- official validation을 먼저 inventory 및 metric-freeze 대상으로 사용한다.
- test는 local label file 또는 evaluation server가 있고, protocol/code/metric/wording이
  모두 freeze된 뒤에만 single final evaluation으로 사용한다.
- 현재 internal grouped metric은 paper metric이 아니다.
- 현재 공식 route는 `C_e` mechanism 검증이며, `p_rel` / `p_obs`는 아직 optional future
  protocol이다.

Local `3DSSG_subset` split inventory:

| Split | Scans | Relations | 역할 |
| --- | ---: | ---: | --- |
| `train` | 3852 | 81190 | reference only |
| `validation` | 548 | 11254 | primary official inventory / future metric split |
| `test` | 0 | 0 | local `relationships_test.json` 없음 |

Validation family capacity:

| Family | Validation count | Predicate counts |
| --- | ---: | --- |
| `relative_horizontal` | 5474 | `left=1713`, `right=1713`, `front=1024`, `behind=1024` |
| `relative_vertical` | 390 | `higher than=195`, `lower than=195` |
| `size_relative` | 170 | `bigger than=85`, `smaller than=85` |
| `support_contact` | 1589 | `standing on=1357`, `lying on=232` |

다음 source route:

- Primary: `GT_counterfactual_mechanism`
- Secondary bridge: `VL-SAT_source_candidates`
- Secondary bridge: `Open3DSG_source_candidates`
- Test: deferred

다음 단계에서는 official validation의 GT relation, object geometry join, VL-SAT source
candidate, Open3DSG source candidate availability를 실제로 inventory해야 한다.

## 19. 2026-07-01 추가 진행: Official Source Inventory After Protocol Plan

`compatibility_dataset_v3_official_source_inventory_after_protocol_plan`을 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory
```

이 단계는 official validation metric을 만든 것이 아니라, official validation에서 H002
promoted route를 구성할 수 있는지 확인한 inventory 단계다.

Official validation GT/object geometry inventory:

| Family | GT relations | Unique scans | OBB pair coverage | 판단 |
| --- | ---: | ---: | ---: | --- |
| `relative_horizontal` | 5474 | 155 | 1.000000 | candidate-ready |
| `relative_vertical` | 390 | 63 | 1.000000 | candidate-ready |
| `size_relative` | 170 | 35 | 1.000000 | candidate-ready |
| `support_contact` | 1589 | 156 | 1.000000 | diagnostic/challenging |

Read-only source candidate inventory:

| Source | `relative_horizontal` | `relative_vertical` | `size_relative` | `support_contact` |
| --- | ---: | ---: | ---: | ---: |
| `vlsat_full_validation` | 147232 | 73616 | 73616 | 73616 |
| `open3dsg_recovery_relaxed_views_min2` | 107064 | 53532 | 53532 | 53532 |

중요한 caveat:

- H001 geometry verification은 `relative_vertical`과 `support_contact`만 checkable하다.
- `relative_horizontal`과 `size_relative`은 H001 verification에서는 unsupported라서,
  H002 official materialization에서 새 `G_e`를 구성해야 한다.
- 따라서 H001 `p_geom_valid`를 그대로 H002 main geometry evidence로 재사용하면 안 된다.
- `support_contact`는 source row와 geometry row가 충분하지만 내부 결과상 partial/challenging
  route이므로 solved claim으로 올리면 안 된다.

현재까지의 결론:

- official validation에서 candidate materialization protocol로 넘어갈 재료는 있다.
- 하지만 아직 official validation/test 성능 개선, paper metric, calibrated `p_rel/p_obs`
  claim은 없다.
- 당시 다음 단계는 metric runner가 아니라 official candidate materialization protocol이었다.

## 20. 2026-07-01 추가 진행: Official Candidate Materialization Protocol

`compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory`를
완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol
```

이 단계는 paper-level metric 실행이 아니라 official validation row materialization으로
넘어가기 위한 protocol freeze다.

핵심 protocol:

- official validation GT relation을 primary anchor로 사용한다.
- 같은 object pair에서 predicate counterfactual을 생성한다.
- `relative_horizontal`, `relative_vertical`, `size_relative`, `support_contact`별로
  다른 `G_e`를 구성한다.
- VL-SAT/Open3DSG recovery rows는 source bridge/provenance로만 사용한다.
- `Z_e`인 source score/rank와 H001 `p_geom_valid`는 main `C_e` model-safe view에서
  제외한다.

Family route:

| Family | GT rows | 현재 역할 |
| --- | ---: | --- |
| `relative_horizontal` | 5474 | main frame-aware compatibility route |
| `relative_vertical` | 390 | main signed-geometry compatibility route |
| `size_relative` | 170 | main size compatibility route |
| `support_contact` | 1589 | diagnostic/challenging support-contact route |

Blocked fields:

- source score/rank/source id,
- H001 `p_geom_valid`와 verification status,
- label/geometry/candidate/construction bucket,
- distance/rank band,
- GT exact-match flag,
- counterfactual generation rule.

다음 단계부터는 실제 구현 위치가 hypothesis 폴더가 아니라
`experiments/H002_compatibility_routing`이다. 다음 Docker service는
`h002-official-materialize-candidates`이며, 아직 metric runner가 아니라 materialization
runner다.

## 21. 2026-07-01 추가 진행: Official Candidate Materialization Docker Implementation

`h002-official-materialize-candidates` Docker service를 구현하고 실행했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation
```

생성 위치:

```text
experiments/H002_compatibility_routing/official_materialization/latest/
```

생성된 row:

| Output | Rows |
| --- | ---: |
| `candidate_rows.jsonl` | 23062 |
| `model_safe_view.jsonl` | 23062 |
| `hidden_manifest.jsonl` | 23062 |
| `validation_errors.jsonl` | 0 |

Family별 label 구성:

| Family | Reject/counterfactual | Accept/GT | Total |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 13290 | 5474 | 18764 |
| `relative_vertical` | 390 | 390 | 780 |
| `size_relative` | 170 | 170 | 340 |
| `support_contact` | 1589 | 1589 | 3178 |

중요한 경계:

- official validation candidate rows는 생성됐지만 metric은 아직 계산하지 않았다.
- official test는 사용하지 않았다.
- paper-level result도 아니다.
- 다음 단계는 schema/shortcut audit이다. 특히 `relative_horizontal`의 1:3 label imbalance,
  object class/predicate shortcut, counterfactual construction leakage, hidden field leakage를
  먼저 확인해야 한다.

## 22. 2026-07-01 추가 진행: Official Candidate Materialization Schema Audit

Official materialized rows에 대한 schema/shortcut/control-readiness audit을 완료했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats
validation_errors = 0
shortcut_warnings = 1
next_todo = compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

통과한 항목:

| 항목 | 결과 |
| --- | ---: |
| schema violations | 0 |
| blocked field hits | 0 |
| runtime validation errors | 0 |
| model-safe rows | 23062 |
| hidden rows | 23062 |
| model-safe/hidden mismatch | 0 |
| control-readiness blockers | 0 |

핵심 caveat:

- `support_contact`에서 `predicate_x_class_pair` shortcut이 매우 강하다.
- Majority accuracy는 `0.993707`이다.
- 따라서 `support_contact`는 official metric에 포함하더라도 challenging/diagnostic route로
  해석해야 하며 solved claim으로 올리면 안 된다.

Metric protocol에 반드시 들어가야 하는 것:

- per-family AUROC,
- macro-family AUROC,
- weighted-family AUROC,
- overall AUROC는 secondary,
- wrong-`T` control,
- shuffled-`G` control,
- route-specific control,
- `Z_e` source score/rank exclusion,
- `support_contact` challenging-route wording.

## 23. 2026-07-01 추가 진행: Official Metric Protocol Freeze

Schema audit 이후 official validation metric을 실행하기 전, metric protocol을 고정했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_runner_after_protocol_freeze
```

고정된 내용:

- official validation rows는 eval-only로만 사용한다.
- trainable model view는 internal train에서 fit하고 internal dev에서만 selection/threshold를 정한다.
- primary metric은 `macro_family_AUROC`이다.
- weighted-family AUROC와 overall AUROC는 secondary다.
- main `C_e` input은 `T_e`와 `G_e`만 허용한다.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields는 main `C_e`에서 제외한다.
- wrong-`T`, shuffled-`G`, subject/object swap, sign flip, horizontal frame control을 required control로 둔다.
- `support_contact`는 challenging/diagnostic route이며 solved claim으로 올리지 않는다.

출력 artifact:

```text
artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

이 단계도 metric runner가 아니므로 official validation metric, official test result, paper-level
result는 아직 없다.

## 24. 2026-07-01 추가 진행: Official Metric Runner

Frozen protocol을 따르는 Docker official validation metric runner를 구현하고 실행했다.

현재 상태:

```text
status = h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_result_review_after_runner
```

Docker command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-metric-runner
```

결과 위치:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
```

주요 metric:

| View | Macro-family AUROC | Weighted-family AUROC | Overall AUROC |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.417633 | 0.455374 | 0.404333 |
| `M2_G_geometry_only` | 0.500000 | 0.500000 | 0.528329 |
| `M3_T_plus_G_concat` | 0.416923 | 0.454625 | 0.406137 |
| `M4_TxG_compatibility` | 0.835547 | 0.720781 | 0.724835 |

Family-level M4:

- `relative_vertical`: AUROC `0.991321`
- `size_relative`: AUROC `0.999585`
- `relative_horizontal`: AUROC `0.719568`
- `support_contact`: AUROC `0.631712`

해석 전 caveat:

- `support_contact`는 여전히 challenging/diagnostic이다.
- `relative_horizontal`은 horizontal frame-swap control delta가 `0.038149`로 약해서
  frame-aware claim을 강하게 쓰기 전에 result review가 필요하다.
- official validation metric은 생성됐지만 paper-level result로 승격하지 않았다.
  다음 단계는 result review와 claim-boundary lock이다.
