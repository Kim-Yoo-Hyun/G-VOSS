# H001 Relation 검증 요약

Last updated: 2026-06-09 KST

## 목적

이 문서는 H001에서 왜 몇 개의 semantic relation을 골랐는지, 무엇을
검증했는지, 어떤 metric으로 가설을 확인했는지, 결과가 무엇을
의미하는지, 그리고 다음 방향이 무엇인지 한국어로 정리한다.

핵심 질문은 다음과 같다.

```text
Semantic score가 높은 3D Scene Graph relation prediction이 실제 3D geometry
상에서도 성립하는가?
```

H001의 현재 논문 claim은 모든 3DSSG relation을 다루는 것이 아니라,
geometry로 검증 가능한 relation family에서 semantic plausibility와 physical
consistency가 어긋나는 failure mode를 정량화하고 줄이는 것이다.

## 선택한 Relation

현재 main claim에 포함되는 relation family는 세 개다.

| Family | Predicate labels | Full-validation GT rows | 왜 선택했는가 | Geometry evidence |
| --- | --- | ---: | --- | --- |
| `support_contact` | `standing on`, `lying on`, `supported by` | 1,816 | 접촉, 지지면, 수직 gap처럼 3D geometry로 검증 가능한 물리 관계다. | point/local contact, support plane, vertical gap, OBB overlap, support subtype |
| `proximity` | `close by` | 1,766 | 의미적으로 가까워 보이는 객체쌍이 실제 공간에서 가까운지 직접 검증할 수 있다. | 3D distance, normalized XY distance, object scale-aware distance |
| `relative_vertical` | `higher than`, `lower than` | 390 | 위/아래 관계는 객체 중심과 높이 범위의 순서로 검증 가능하다. | centroid height, OBB vertical extent, vertical-order consistency |
| total | 6 labels | 3,972 | full official `3DSSG_subset` validation에서 H001 metric denominator로 사용한다. | identity-preserving prediction row + geometry join |

이 선택은 “잘 되는 relation만 사후적으로 고른 것”이 아니라, relation의
semantic meaning이 3D geometry evidence로 반증 가능한가를 기준으로 정했다.
Recall은 exact predicate-label matching으로 계산하고, family grouping은
violation 검증과 reliability 분석에만 사용한다.

Main claim에 넣지 않은 relation도 명시적으로 추적했다.

| Track | Labels | 현재 판단 |
| --- | --- | --- |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | 좌표계/frame ambiguity가 커서 main claim에 넣지 않는다. Best frame의 macro strict purity는 0.7725이고 `front`/`behind` strict purity는 0.7445다. |
| `relative_lateral` | `left`, `right` | left/right만 분리하면 가능성이 있었지만, train/dev lock에서 dev strict purity가 0.6975라 source metric으로 승격하지 않는다. |
| `attachment_deferred` | `attached to`, `hanging on`, `connected to` | H001을 확장할 때 가장 유망한 physical-relation upgrade다. G5d full-source metric까지 완료됐지만, current AAAI main claim에는 사용자 최종 확인 전까지 넣지 않는다. |
| Qwen-VL source | H001 families | modern VLM third-source extension으로만 유지한다. 아직 full-source metric evidence가 아니다. |

## 검증한 것

H001이 검증한 것은 단순히 “geometry를 추가하면 좋아진다”가 아니다.
다음 세 가지를 분리해서 확인했다.

1. Semantic-only prediction의 top-K relation 중 geometry-inconsistent relation이 존재하는가?
2. Frozen geometry evidence와 `p_geom_valid`를 이용한 re-ranking이 violation을 줄이면서 recall을 유지하거나 개선하는가?
3. 이 개선이 geometry-only, distance-only, shuffled geometry, wrong-pair geometry 같은 trivial control로 설명되지 않는가?

평가 source는 두 개다.

| Source | 역할 | Full-validation status |
| --- | --- | --- |
| `VL-SAT` / `vlsat_closed_set` | controlled reproduced anchor | 157 scans, 548 contexts, 957,008 prediction rows, 3,972 H001-family GT rows |
| `Open3DSG` | main open-vocabulary relation-source case study | 548/548 recovery branch, 695,916 prediction rows, 3,972 H001-family GT rows |

Open3DSG는 selected official non-avg checkpoint를 사용했고,
full-validation main branch는 `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`와 two-scan
relaxed view regeneration을 적용한 548/548 recovery-policy variant다. 원본
source route 533/548 branch는 sensitivity check로 남긴다.

## Metric 설명

| Metric / condition | 의미 | 왜 가설 검증에 필요한가 |
| --- | --- | --- |
| `R@50`, `R@100` | 각 subgraph에서 top-K prediction 안에 GT predicate-label이 exact match로 들어오는 비율 | Geometry-aware re-ranking이 useful relation recall을 희생하는지만 보지 않도록 한다. |
| `Violation@50`, `Violation@100` | top-K prediction 중 frozen geometry verifier가 `violated`로 판단한 비율 | “semantic score는 높지만 geometry 상 성립하지 않는가?”를 직접 측정한다. |
| `semantic_only` | 원래 prediction source의 semantic ranking | baseline failure mode를 측정하는 기준점이다. |
| `probabilistic_recalibrated` | `semantic_score * p_geom_valid`로 re-ranking | semantic plausibility와 calibrated geometry validity를 결합했을 때 reliability가 좋아지는지 본다. |
| `rule_verified_point_subtype` | `violated` row를 hard-filter하는 diagnostic condition | violation을 0으로 만들 수 있는지와 그때 recall cost가 어떤지 보는 upper-bound/operating point다. |
| `family_specific_p_geom_valid` | family별 calibrator를 사용하는 stricter condition | relation family마다 geometry evidence의 scale이 다르므로 family-specific calibration이 유리한지 본다. |
| `control_p_geom_valid_only` | semantic score 없이 geometry validity만으로 ranking | geometry만으로 relation prediction이 되는지 확인한다. 낮아야 정상이다. |
| `control_distance_only` | 단순 거리 heuristic ranking | 결과가 단순 거리 규칙으로 설명되는지 반박한다. |
| `control_shuffled_geometry` | geometry distribution은 보존하되 object-pair identity를 섞음 | instance-specific geometry가 필요한지 확인한다. |
| `control_wrong_pair_geometry` | 다른 object-pair의 geometry를 붙임 | 같은 scene의 geometry라도 정확한 pair identity가 중요함을 확인한다. |
| GT verifier evaluation | GT positives와 deterministic counterfactual negatives를 verifier가 구분하는지 평가 | verifier/calibrator가 arbitrary hand-coded rule이 아니라 GT-consistent signal을 갖는지 확인한다. |
| Bootstrap CI | subgraph resampling으로 point estimate의 안정성을 본다 | 단일 평균 수치가 특정 subgraph 구성에만 의존하는지 점검한다. |
| Failure cases / qualitative queue | 실제 prediction, GT, geometry join에서 나온 case를 family별로 해석 | metric이 의미하는 failure mechanism을 정성적으로 설명한다. |

이 metric set이 중요한 이유는 H001의 가설이 두 축을 동시에 요구하기 때문이다.

```text
Reliability improves only if Violation@K decreases while R@K is preserved or
explicitly measured as a tradeoff.
```

Violation만 줄이고 recall이 무너지는 것은 좋은 relation predictor가 아니다.
반대로 recall만 유지하고 geometry-inconsistent relation을 그대로 두는 것도
H001의 failure mode를 해결하지 못한다.

## 정량 결과

### VL-SAT full-validation

| Condition | R@50 | R@100 | V@50 | V@100 | 해석 |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 | semantic ranking만으로도 recall은 높지만, top-K 안에 geometry violation이 남아 있다. |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 | recall이 올라가면서 violation도 감소한다. |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 | hard filtering은 violation을 제거하지만 recall operating point로는 보수적이다. |
| `family_specific_p_geom_valid` | 0.9288 | 0.9683 | 0.0206 | 0.0333 | 더 stricter한 violation-first operating point다. |

Bootstrap 기준으로 VL-SAT full-validation에서
`probabilistic_recalibrated`는 semantic-only 대비 R@100을 +0.53 pp 높이고
V@100을 -0.72 pp 낮췄다. `family_specific_p_geom_valid`는 R@100 +0.48 pp,
V@100 -1.43 pp다.

### Open3DSG full-validation recovery branch

| Condition | R@50 | R@100 | V@50 | V@100 | 해석 |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 | open-vocabulary source에서는 semantic-only ranking의 geometry violation이 더 크게 나타난다. |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 | R@50은 소폭 낮아지지만 R@100은 크게 올라가고 violation은 크게 감소한다. |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 | hard-filter diagnostic에서도 recall이 semantic-only보다 유지/개선된다. |
| `family_specific_p_geom_valid` | 0.4658 | 0.6047 | 0.0286 | 0.0341 | 가장 강한 Open3DSG operating point다. recall과 violation이 동시에 개선된다. |

Bootstrap 기준으로 Open3DSG full-validation recovery branch에서
`probabilistic_recalibrated`는 semantic-only 대비 R@100을 +5.61 pp 높이고
V@100을 -4.31 pp 낮췄다. `family_specific_p_geom_valid`는 R@100 +8.86 pp,
V@100 -9.01 pp다.

### GT-based verifier evaluation

| Item | Value |
| --- | ---: |
| GT positives | 3,972 |
| GT-derived counterfactual negatives | 3,972 |
| GT-positive nonviolated rate | 0.9965 |
| GT-derived negative nonsatisfied rate | 0.9673 |
| `p_geom_valid` AUROC / AUPRC | 0.9772 / 0.9729 |

Family별로도 verifier signal은 대체로 안정적이다.

| Family | Positive nonviolated | Negative nonsatisfied | AUROC |
| --- | ---: | ---: | ---: |
| `proximity` | 1.0000 | 1.0000 | 0.9976 |
| `relative_vertical` | 0.9949 | 0.9949 | 0.8960 |
| `support_contact` | 0.9934 | 0.9295 | 0.9924 |

이 결과는 verifier가 GT-positive relation을 대부분 잘못 reject하지 않고,
deterministic counterfactual negative를 대부분 satisfied로 보지 않는다는 뜻이다.
따라서 H001의 geometry signal은 단순한 사후 filtering rule이 아니라
GT-consistent reliability signal로 볼 수 있다.

## Control 결과 해석

Control 결과는 H001의 개선이 trivial하지 않음을 보여준다.

VL-SAT full-validation에서 geometry-only ranking은 R@100 0.5184, distance-only는
R@100 0.5554로 semantic-aware condition보다 크게 낮다. Distance-only의
V@100은 0.0981로 semantic-only의 0.0476보다 나쁘다. Shuffled geometry와
wrong-pair geometry는 semantic score를 유지해도 V@100이 각각 0.0588,
0.0601로 악화된다. 즉, 단순히 “가까운 것만 올리면 된다”거나 “geometry
분포만 있으면 된다”가 아니다.

Open3DSG에서는 control 차이가 더 크다. Shuffled geometry와 wrong-pair geometry의
R@100은 각각 0.2543, 0.2331로 무너지고 V@100은 약 0.20까지 증가한다.
반면 family-specific condition은 R@100 0.6047, V@100 0.0341이다. 이는
object-pair identity-preserving geometry join이 핵심임을 보여준다.

## 정성 결과

Full-validation failure-analysis queue도 같은 failure mechanism을 지지한다.

| Source | Selected cases | Geometry-aware reranking demotion | Promoted / retained | High `p_geom_valid` but rule-violated |
| --- | ---: | ---: | ---: | ---: |
| VL-SAT | 36 | 28 | 8 | 7 |
| Open3DSG recovery | 36 | 25 | 11 | 8 |

정성적으로는 다음 패턴이 반복된다.

- `proximity`: `close by`가 semantic하게 그럴듯해도 실제 normalized XY distance가 멀어 `far_in_normalized_xy`로 demotion된다.
- `relative_vertical`: `higher than` / `lower than`이 객체 height ordering과 반대일 때 `vertical_order_contradicts_predicate`로 demotion된다.
- `support_contact`: `standing on`, `lying on`, `supported by`가 surface/contact evidence와 맞지 않을 때 `plane_gap_large`, `positive_float_gap_large`, support subtype reason으로 demotion된다.
- 일부 case는 geometry-aware score가 오히려 ranking을 올리거나 유지한다. 그래서 H001은 hard filtering만 주장하지 않고, recall/violation tradeoff를 함께 보고한다.
- 일부 rule-violated case가 여전히 높은 `p_geom_valid`를 갖는다. 이 residual calibration risk 때문에 probabilistic, family-specific, rule-verified condition을 분리해서 보고한다.

이 정성 결과는 대표 human audit metric은 아니지만, 정량 metric이 가리키는
failure mechanism이 실제 object-pair relation 수준에서 발생함을 설명하는
reviewer-defense evidence다.

## 결과가 시사하는 바

현재 결과는 H001의 핵심 가설을 지지한다.

1. Semantic-only relation predictor는 높은 semantic score를 가진 relation이라도 3D geometry와 모순되는 prediction을 낸다.
2. 이 모순은 `support_contact`, `proximity`, `relative_vertical`처럼 geometry-checkable relation family에서 정량적으로 측정 가능하다.
3. Frozen geometry evidence와 train/train-dev-derived `p_geom_valid`를 사용하면 violation을 줄이면서 recall을 유지하거나 개선할 수 있다.
4. 개선은 단순 geometry-only, distance-only, shuffled geometry, wrong-pair geometry로 설명되지 않는다.
5. VL-SAT와 Open3DSG 두 source에서 같은 방향의 evidence가 나오므로, single-baseline-only claim보다 강한 scoped cross-source reliability claim이 가능하다.

다만 claim boundary도 분명하다.

- 현재 결과는 broad open-vocabulary 3DSSG generation 성능 향상이 아니다.
- closed-set / GT-object setting에서 measured H001 families에 대한 relation reliability evidence다.
- Open3DSG full-validation main branch는 548/548 recovery-policy variant이므로, `min_visible=2`와 relaxed two-scan views caveat를 숨기면 안 된다.
- `relative_horizontal`, `relative_lateral`, `attachment_deferred`, Qwen-VL은 현재 main claim에 자동으로 포함되지 않는다.

## 다음 방향

이미 완료된 핵심 단계는 다음과 같다.

1. 검증 가능한 relation family를 `support_contact`, `proximity`, `relative_vertical`로 고정했다.
2. VL-SAT full official validation metric bundle을 생성했다.
3. Open3DSG selected checkpoint와 full-validation recovery branch를 생성했다.
4. 두 source 모두에서 prediction export, geometry join, metric evaluation, controls, bootstrap CI, failure rows, qualitative queue를 완료했다.
5. GT-based verifier evaluation으로 verifier/calibrator가 GT-positive와 counterfactual negative를 구분함을 확인했다.
6. Relation expansion 후보를 별도 track으로 검토했고, 현재 main claim에 넣을 것과 넣지 않을 것을 구분했다.

따라서 현재 paper-facing 다음 방향은 core metric을 더 늘리는 것이 아니라,
다음 작업을 안정적으로 마무리하는 것이다.

| Priority | Next direction | 이유 |
| --- | --- | --- |
| P0 | paper main text와 appendix에서 full-validation result, Open3DSG recovery caveat, exact-label denominator, residual calibration risk를 일관되게 반영 | reviewer가 denominator 조작, hand-coded verifier, recall sacrifice를 공격하지 못하게 해야 한다. |
| P1 | artifact bundle / reproducibility package 정리 | Docker 재현성, checkpoint, row-level JSONL, metric/report provenance를 공개 가능한 형태로 고정해야 한다. |
| P2 | Figure / qualitative examples를 metric과 연결 | “semantic score는 높지만 geometry 상 성립하지 않음”을 직관적으로 보여줘야 한다. |
| P3 | `attachment_deferred`를 future upgrade 또는 appendix evidence로 둘지 결정 | G5d metric은 나왔지만 Open3DSG denominator 768/967, `connected to` dev strict absence, visual/failure audit caveat가 남아 있다. |
| P4 | Qwen-VL full-source loop는 GPU runtime이 안정될 때 third-source extension으로 재개 | main baseline 대체가 아니라 modern VLM semantic-source extension으로만 의미가 있다. |

`attachment_deferred`는 future work로만 남기기에는 아까운 결과가 있다.
G5d full-source scoring은 69/69 shards, 135,048 scored rows, validation errors 0으로
완료되었다. VL-SAT에서는 `rule_verified_attachment_policy`가 R@100 0.9380,
V@100 0.0215이고, Open3DSG에서는 R@100 0.9245, V@100 0.0842다. 하지만
Open3DSG exact-label denominator가 768/967이고, `attached to` noise와
`connected to` dev strict absence가 남아 있으므로, 현 AAAI main claim에 넣기
전에는 별도 failure/visual audit과 사용자 최종 확인이 필요하다.

최종적으로 H001의 현재 가장 안전한 논문 방향은 다음 문장이다.

```text
Across reproduced VL-SAT and Open3DSG prediction sources on geometry-checkable
3DSSG relation families, calibrated geometry-consistency re-ranking exposes
and reduces semantically plausible but physically inconsistent relation
predictions while preserving explicit recall tradeoffs.
```

이 문장은 motivation이 아니라 검증 가능한 failure mode, metric, control,
cross-source evidence, 그리고 명확한 claim boundary를 함께 포함한다.
