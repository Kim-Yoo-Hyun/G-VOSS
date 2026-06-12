# H001 Relation 검증 요약

Last updated: 2026-06-12 KST

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
| Qwen-VL source | H001 families | modern VLM third-source extension evidence로 유지한다. Historical 127-scan downstream metric은 완료됐고, full official validation branch도 187/187 shards, 46,506/46,506 inference rows, adapter/geometry/metrics/bootstrap/failure rows까지 완료됐다. Full-validation Qwen은 semantic_only R@50/R@100 `0.2815/0.3600`, V@50/@100 `0.1226/0.1246`; probabilistic_recalibrated R@50/R@100 `0.3215/0.3653`, V@50/@100 `0.0795/0.1166`; rule_verified는 violation `0.0`이다. 다만 recall 수준이 VL-SAT/Open3DSG보다 낮고 end-to-end 3DSSG reproduction이 아니므로 현재 main claim/table에는 자동 승격하지 않는다. |

## 검증한 것

H001이 검증한 것은 단순히 “geometry를 추가하면 좋아진다”가 아니다.
다음 세 가지를 분리해서 확인했다.

1. Semantic-only prediction의 top-K relation 중 geometry-inconsistent relation이 존재하는가?
2. Frozen geometry evidence와 `p_geom_valid`를 이용한 re-ranking이 violation을 줄이면서 recall을 유지하거나 개선하는가?
3. 이 개선이 geometry-only, distance-only, shuffled geometry, wrong-pair geometry 같은 trivial control로 설명되지 않는가?

평가 main source는 두 개이고, Qwen-VL은 별도의 third-source extension으로
추적한다.

| Source | 역할 | Full-validation status |
| --- | --- | --- |
| `VL-SAT` / `vlsat_closed_set` | controlled reproduced anchor | 157 scans, 548 contexts, 957,008 prediction rows, 3,972 H001-family GT rows |
| `Open3DSG` | main open-vocabulary relation-source case study | 548/548 recovery branch, 695,916 prediction rows, 3,972 H001-family GT rows |
| Qwen-VL | modern VLM third-source extension | 157 scans, 548 contexts, 46,506 inferable Qwen input rows, 35,131 exported predictions, 3,972 H001-family GT rows |

Open3DSG는 selected official non-avg checkpoint를 사용했고,
full-validation main branch는 `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`와 two-scan
relaxed view regeneration을 적용한 548/548 recovery-policy variant다. 원본
source route 533/548 branch는 sensitivity check로 남긴다.

## Validation 경로의 구체적 의미

H001의 핵심은 두 semantic relation source를 같은 row contract, 같은 geometry
join, 같은 metric으로 평가하는 것이다. 따라서 VL-SAT와 Open3DSG의 모델 내부가
다르더라도, 최종 비교는 `(scan, subgraph, subject id, object id, predicate,
semantic score)` prediction row에 frozen geometry evidence를 붙인 뒤 수행한다.

| Route | 어떻게 진행했는가 | 왜 필요한가 |
| --- | --- | --- |
| `VL-SAT full validation` | 공개 `3DSSG_subset` validation 범위의 157 scans / 548 contexts 전체를 사용했다. VL-SAT staged runtime에서 candidate directed pair 36,808개와 26개 predicate에 대해 957,008 prediction row를 export했고, 그중 H001 relation family의 GT denominator는 3,972 rows다. 이후 adapter export, geometry join, metric evaluation, controls, bootstrap CI, GT verifier evaluation, failure row/qualitative queue를 같은 Docker protocol로 생성했다. | VL-SAT는 controlled reproduced anchor다. Closed-set 성격이 강해 recall이 높고 denominator가 안정적이므로, H001 metric과 verifier가 정상 동작하는지 보여주는 기준 source로 쓴다. |
| `Open3DSG full-validation recovery branch` | selected official non-avg BLIP checkpoint를 사용하되, Open3DSG source preprocessing에서 탈락하던 15 contexts까지 포함하기 위해 `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`와 two-scan relaxed view regeneration을 적용했다. 이 branch는 548/548 contexts, raw dump 26,938 rows, adapter 695,916 prediction rows, geometry 695,916 rows, H001 GT denominator 3,972 rows를 만든다. | 현재 paper-facing Open3DSG main route다. 목적은 공식 validation denominator 전체를 다루면서, semantic-only Open3DSG prediction에도 같은 geometry-consistency failure와 re-ranking 효과가 나타나는지 확인하는 것이다. 단, preprocessing policy를 완화했으므로 recovery-policy caveat를 반드시 명시한다. |
| `Open3DSG partial-validation / official preprocessing route` | Open3DSG의 원본 source preprocessing gate를 따른다. 이 gate는 충분한 object-to-image visibility metadata가 없는 context를 drop하며, full validation에서 533/548 contexts만 loadable하다. 이 route는 adapter 690,924 prediction rows와 대응 geometry/metrics/failure artifacts를 만든다. | “recovery branch가 결과를 만들기 위해 튜닝된 것 아닌가?”라는 공격을 막기 위한 sensitivity route다. 15 contexts가 빠진 이유는 GT annotation이 없어서가 아니라 Open3DSG runtime/preprocess visibility policy가 해당 contexts를 처리하지 못했기 때문이다. |

즉, `full-validation recovery branch`는 결과를 좋게 만들기 위해 H001 verifier나
threshold를 바꾼 것이 아니다. Open3DSG preprocessing에서 누락된 contexts를
denominator에 포함시키기 위해 loadability policy를 완화한 branch다. 따라서 본문에는
548/548 recovery result를 main table로 쓰되, unmodified 533/548 source route를
appendix/sensitivity evidence로 함께 남기는 것이 가장 투명하다.

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

## 비교군과 score 계산의 구체적 의미

모든 condition은 같은 prediction row를 출발점으로 한다. 먼저 source model이 낸
relation score 또는 rank를 `semantic_ranking_score`로 정규화한다. 그 다음
geometry join이 subject/object pair의 3D geometry evidence를 붙인다. 여기에는
object-pair 3D distance, normalized XY distance, vertical center/range order,
support plane/contact gap, OBB overlap, point/local contact, support subtype
reason 등이 포함된다. Frozen verifier는 이를 바탕으로 row를 `satisfied`,
`uncertain`, `violated`, `unsupported`로 나누고, train/train-dev-derived
calibrator는 같은 evidence를 `p_geom_valid`라는 0과 1 사이의 reliability score로
변환한다.

`p_geom_valid`는 “정답 확률”이 아니라 “이 row의 predicate가 해당 object-pair
geometry와 양립할 가능성”이다. 예를 들어 `higher than`인데 subject의 높이가
object보다 낮으면 `p_geom_valid`가 낮아지고, `close by`인데 normalized XY distance가
작으면 높아진다. `support_contact`에서는 단순히 중심이 가까운지가 아니라, 지지면,
수직 gap, 접촉 subtype, 물체 크기와 범위를 함께 본다.

## Continuous calibrated geometry-consistency score

H001의 main method는 hard threshold 하나로 relation을 맞다/틀리다로 자르는
방식이 아니다. Hard-rule status는 해석 가능성과 `Violation@K` 계산을 위한
diagnostic layer이고, main re-ranking은 continuous calibrated geometry-consistency
score인 `p_geom_valid`를 사용한다.

전체 흐름은 다음과 같다.

```text
prediction row
-> identity-preserving geometry join
-> continuous geometry feature vector
-> train/dev-fitted logistic calibrator
-> p_geom_valid
-> semantic_score * p_geom_valid
-> reliability-aware re-ranking
```

### 1. Geometry feature 계산

각 prediction row는 `(scan_id, subgraph/context_id, subject_id, object_id,
predicate)` identity를 유지한 채 같은 object pair의 3D geometry와 join된다.
이때 사용되는 기본 geometry source는 3RScan/3DSSG object OBB/AABB와, support
relation의 경우 point/local-surface evidence다.

주요 continuous features는 다음과 같다.

| Feature | 계산 | 의미 |
| --- | --- | --- |
| `distance_xy` | `sqrt((sx - ox)^2 + (sy - oy)^2)` | subject/object center의 수평 거리 |
| `normalized_distance_xy` | `distance_xy / mean(subject_diag_xy, object_diag_xy)` | object scale에 대한 상대적 수평 거리 |
| `distance_3d` | 3D center distance | 전체 공간 거리 |
| `normalized_distance_3d` | `distance_3d / mean(subject_diag_3d, object_diag_3d)` | object scale에 대한 상대적 3D 거리 |
| `center_delta_z` | `subject_center_z - object_center_z` | subject가 object보다 위/아래인지 |
| `normalized_center_delta_z` | `center_delta_z / mean(subject_height, object_height)` | object height에 대한 상대적 vertical order |
| `projected_subject_overlap_ratio` | XY projection intersection / subject XY area | subject footprint가 object footprint와 겹치는 정도 |
| `projected_object_overlap_ratio` | XY projection intersection / object XY area | object footprint가 subject footprint와 겹치는 정도 |
| `vertical_gap_subject_on_object` | `subject_bottom_z - object_top_z` | subject가 object 위에 놓였을 때의 vertical gap |

여기서 `normalized_distance_xy`가 중요한 이유는 absolute meter threshold가 object
크기에 민감하기 때문이다. 작은 object 두 개의 1m 거리와 sofa/table 같은 큰 object의
1m 거리는 relation 의미가 다를 수 있다. 따라서 H001은 object-pair의 평균 XY
diagonal로 나눈 scale-aware distance를 쓴다.

### 2. Calibration data

`p_geom_valid` calibrator는 held-out validation result를 보고 맞춘 것이 아니라,
train/train-dev-derived calibration rows에서 fitting한다.

Calibration rows는 두 종류다.

| Row type | 의미 |
| --- | --- |
| GT-positive row | 3DSSG annotation에 실제로 존재하는 H001-family relation |
| deterministic counterfactual negative | GT-positive relation을 기하학적으로 성립하지 않도록 뒤집거나 pair를 바꾼 negative |

Counterfactual negative는 단순 absent-edge negative가 아니다. 예를 들어
`higher than` / `lower than`의 방향을 반대로 만들거나, `close by`가 성립하기 어려운
far pair를 구성하거나, support relation에서 support geometry가 맞지 않는 pair를
만든다. 이 rows는 verifier가 GT-positive를 과도하게 reject하지 않고, 명백한
counterfactual을 satisfied로 받아들이지 않는지 확인하기 위한 calibration signal이다.

### 3. Logistic calibration

Calibrator는 geometry numeric features와 predicate family/label indicator를 입력으로
받는 작은 logistic regression model이다. 쉽게 말하면 “이 object-pair geometry와
predicate가 서로 양립할 확률”을 출력하도록 학습한 score 변환기다. Semantic score는
`p_geom_valid` fitting에 사용하지 않는다. 즉, `p_geom_valid`는 source model이 얼마나
자신 있어 하는지가 아니라, geometry만 봤을 때 relation이 물리적으로 양립 가능한지를
나타낸다.

개념적으로는 다음과 같다.

```text
x = standardized_geometry_features
    + family_one_hot
    + predicate_one_hot

logit = w · x
p_geom_valid = sigmoid(logit)
```

실제 pooled calibrator artifact는 다음 파일이다.

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json
```

이 model의 구조는 다음과 같다.

| 항목 | 실제 내용 |
| --- | --- |
| model type | binary logistic regression |
| model id | `h001-p-geom-valid-smoke-v1` |
| input dimension | 29 features = bias 1 + numeric 19 + family one-hot 3 + predicate one-hot 6 |
| output | `p_geom_valid = sigmoid(w · x)`, 0과 1 사이의 geometry-validity probability |
| training source | `train_dev_calib` rows |
| train/dev split | scan-id 기반 train/dev split |
| train rows | 4,616 = positives 2,050 + negatives 2,566 |
| dev rows | 1,193 = positives 515 + negatives 678 |
| hyperparameters | epochs 800, learning rate 0.2, L2 0.0001, calibration bins 10 |
| semantic score usage | 사용하지 않음 |

입력 feature는 크게 네 묶음이다.

| Feature group | 실제 feature |
| --- | --- |
| 거리/scale | `distance_3d`, `distance_xy`, `normalized_distance_3d`, `normalized_distance_xy` |
| vertical order | `center_delta_z`, `normalized_center_delta_z`, `abs_center_delta_z`, `abs_normalized_center_delta_z` |
| overlap/contact | `projected_iou_xy`, `projected_subject_overlap_ratio`, `projected_object_overlap_ratio`, `vertical_gap_subject_on_object`, `abs_vertical_gap_subject_on_object` |
| object height/range | `subject_bottom_z`, `subject_top_z`, `object_bottom_z`, `object_top_z` |
| predicate-aligned vertical | `predicate_aligned_center_delta_z`, `predicate_aligned_normalized_center_delta_z` |
| categorical indicators | `family:proximity`, `family:relative_vertical`, `family:support_contact`, and six predicate one-hot labels |

숫자 feature는 train rows의 평균/표준편차로 standardization된다. 예를 들어
`normalized_distance_xy`는 그대로 threshold로 자르는 값이 아니라,
train-set mean/std로 표준화되어 logistic model의 한 입력 차원이 된다. Feature가
missing이면 해당 feature의 train mean으로 대체되므로, calibrator는 row를 drop하지
않고 가능한 한 모든 geometry-available prediction에 확률을 낸다.

학습 label은 다음과 같이 정의된다.

| Label | 의미 |
| --- | --- |
| `geom_valid = 1` | train/dev GT-positive relation 또는 geometry가 predicate와 양립하도록 구성된 positive row |
| `geom_valid = 0` | deterministic counterfactual negative, 즉 predicate 방향/pair/geometry가 성립하지 않도록 만든 negative row |

따라서 `p_geom_valid`는 “source가 이 relation을 얼마나 좋아하는가”가 아니라
“geometry feature만 봤을 때 이 relation이 GT-positive 쪽에 가까운가,
counterfactual-negative 쪽에 가까운가”를 나타낸다. Pooled calibrator의 dev 성능은
Brier 0.0495, NLL 0.1812, ECE 0.0456, AUROC 0.9822, AUPRC 0.9735다. 이 수치는
calibrator가 train/dev calibration rows에서 valid/invalid geometry를 강하게
구분한다는 근거지만, held-out prediction의 모든 case를 완벽히 맞춘다는 뜻은 아니다.

Family-specific control은 별도 artifact를 사용한다.

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json
```

이 model은 pooled model 하나가 아니라 `proximity`, `relative_vertical`,
`support_contact` 각각에 대해 별도의 logistic regression을 fitting한다. 목적은
거리 기반 relation, vertical-order relation, support/contact relation의 feature scale과
의미가 다르기 때문에, family별 calibration이 recall/violation tradeoff를 더 잘 맞추는지
확인하는 것이다. Dev 기준 family-specific AUROC/AUPRC는 `proximity` 1.0000/1.0000,
`relative_vertical` 0.9982/0.9989, `support_contact` 0.9831/0.9675다.

Prediction row에 적용될 때 output은 geometry verification JSONL의 `calibration`
필드에 저장된다.

```json
{
  "calibration": {
    "model_id": "h001-p-geom-valid-smoke-v1",
    "model_path": ".../p_geom_valid_smoke/model.json",
    "p_geom_valid": 0.87,
    "p_geom_invalid": 0.13,
    "p_final_product": 0.6264
  }
}
```

여기서 `p_geom_invalid = 1 - p_geom_valid`이고, `p_final_product`는 source의
`predicate_score`가 있을 때 `predicate_score * p_geom_valid`로 계산한 값이다.
위 예시는 `predicate_score = 0.72`일 때 `0.72 * 0.87 = 0.6264`가 되는 형태를
보여준다.
실제 metric evaluation의 `probabilistic_recalibrated` condition은 같은 원리로
`semantic_ranking_score * p_geom_valid`를 사용해 ranking을 다시 만든다.

중요한 해석은 다음과 같다.

- `p_geom_valid`가 높다: geometry feature가 GT-positive calibration rows와 유사하다.
- `p_geom_valid`가 낮다: geometry feature가 counterfactual negative와 유사하다.
- `p_geom_valid`는 hard rule status가 아니다. `satisfied/violated/uncertain`은
  diagnostic label이고, `p_geom_valid`는 continuous probability score다.
- `semantic_score`는 calibrator 입력이 아니다. Semantic score는 calibrator가 출력한
  `p_geom_valid`와 나중에 곱해져 re-ranking에 쓰인다.
- 따라서 H001은 “geometry rule로 prediction을 대체”하는 것이 아니라, semantic source
  score를 physical-consistency probability로 보정한다.

### 4. Re-ranking score

Main re-ranking은 hard-rule label을 직접 score로 쓰지 않고 다음 product score를 쓴다.

```text
geometry-aware score = semantic_ranking_score * p_geom_valid
```

이 design의 의미는 다음과 같다.

- semantic source가 relation plausibility를 제공한다.
- `p_geom_valid`가 same object-pair의 physical consistency를 보정한다.
- geometry가 낮은 row는 top-K에서 내려간다.
- geometry가 높은 row는 semantic score가 충분할 때 유지되거나 올라간다.
- row를 무조건 삭제하지 않으므로 recall/violation tradeoff를 측정할 수 있다.

따라서 H001의 핵심은 `normalized_distance_xy <= 2.5` 같은 숫자 하나가 아니라,
continuous geometry evidence를 calibrated reliability score로 바꾸고 semantic score와
결합하는 것이다.

### 5. 왜 hard gate도 같이 쓰는가

Hard gate는 main score가 아니라 다음 목적을 가진다.

| 용도 | 설명 |
| --- | --- |
| `Violation@K` 계산 | top-K 안에 명백히 geometry와 모순되는 row가 얼마나 있는지 측정 |
| `rule_verified_point_subtype` diagnostic | conservative hard-filter operating point에서 recall cost 확인 |
| failure reason 부여 | `far_in_normalized_xy`, `vertical_order_contradicts_predicate`, `plane_gap_large`처럼 왜 문제가 되는지 설명 |
| qualitative case 해석 | reviewer가 실제 object-pair 단위로 failure mechanism을 이해하도록 지원 |

즉, hard gate는 논문의 주된 novelty가 아니라, continuous score가 무엇을 줄이는지
해석하고 metric화하기 위한 diagnostic layer다.

## Hard-rule status와 threshold 기준

H001 verifier는 각 prediction row를 `satisfied`, `uncertain`, `violated`,
`unsupported` 중 하나로 분류한다. 이 분류는 official 3DSSG benchmark threshold가
아니라, validation/test 결과를 보기 전에 고정한 operational diagnostic gate다.
Benchmark가 `close by`의 normalized distance threshold를 제공하지 않기 때문에,
H001은 물리적으로 명확한 positive/negative 영역과 ambiguous band를 분리한다.

### 공통 status 의미

| Status | 의미 | metric에서의 역할 |
| --- | --- | --- |
| `satisfied` | 해당 predicate가 same object-pair geometry와 명확히 양립한다고 판단 | violation이 아님 |
| `uncertain` | geometry가 부족하거나 margin이 애매해 hard valid/invalid로 자르지 않음 | violation으로 세지 않되, 신뢰도 해석에는 caveat |
| `violated` | predicate 의미와 geometry evidence가 명확히 모순됨 | `Violation@K` numerator에 포함 |
| `unsupported` | 현재 H001 geometry-checkable family 밖의 predicate | H001-family metric claim에서 제외 |

`unsupported`는 “틀렸다”는 뜻이 아니다. 예를 들어 `same as`, `part of`,
`attached to` 같은 relation은 현재 main H001 family가 아니므로 이 verifier로
valid/invalid를 판정하지 않는다. Missing geometry는 대체로 `uncertain` 또는 별도
missing-geometry caveat로 관리한다.

### `proximity`

대상 predicate:

```text
close by
```

계산:

```text
distance_xy = sqrt((sx - ox)^2 + (sy - oy)^2)
mean_diag_xy = (subject_diag_xy + object_diag_xy) / 2
normalized_distance_xy = distance_xy / mean_diag_xy
overlap = projected_subject_overlap_ratio > 0
          OR projected_object_overlap_ratio > 0
```

Status rule:

| Status | 기준 | Reason code |
| --- | --- | --- |
| `satisfied` | `overlap == true` OR `normalized_distance_xy <= 2.5` | `near_in_xy_or_projected_overlap` |
| `violated` | `normalized_distance_xy >= 3.5` | `far_in_normalized_xy` |
| `uncertain` | `2.5 < normalized_distance_xy < 3.5` 또는 feature missing | `proximity_margin_ambiguous`, `missing_normalized_distance_xy` |

`2.5`와 `3.5`는 official benchmark threshold가 아니다. 가까운 영역과 먼 영역을
명확히 나누고, 그 사이를 uncertain으로 남기기 위한 frozen operational gate다.
Main re-ranking에서는 이 hard label 자체보다 continuous `normalized_distance_xy`와
overlap feature가 `p_geom_valid`에 들어간다.

### `relative_vertical`

대상 predicates:

```text
higher than, lower than
```

계산:

```text
center_delta_z = subject_center_z - object_center_z
normalized_center_delta_z = center_delta_z / mean(subject_height, object_height)
```

Predicate 방향에 맞춰 aligned value를 만든다.

```text
if predicate == "higher than":
    aligned = center_delta_z
    aligned_norm = normalized_center_delta_z

if predicate == "lower than":
    aligned = -center_delta_z
    aligned_norm = -normalized_center_delta_z
```

Status rule:

| Status | 기준 | Reason code |
| --- | --- | --- |
| `satisfied` | `aligned >= 0.25m` AND `aligned_norm >= 0.15` | `vertical_order_matches_predicate` |
| `violated` | `aligned <= -0.25m` AND `aligned_norm <= -0.15` | `vertical_order_contradicts_predicate` |
| `uncertain` | 위/아래 차이가 작거나 feature missing | `vertical_margin_ambiguous`, `missing_vertical_delta` |

여기서도 hard threshold는 diagnostic gate다. Continuous calibration에서는
`center_delta_z`, `normalized_center_delta_z`, `predicate_aligned_center_delta_z`,
`predicate_aligned_normalized_center_delta_z`가 그대로 feature로 들어간다.

### `support_contact`

대상 predicates:

```text
standing on, lying on, supported by
```

Support/contact는 단순 center distance만으로는 부족하다. H001은 OBB fallback과
point/local-surface subtype evidence를 함께 둔다.

OBB fallback 계산:

```text
overlap = projected_subject_overlap_ratio > 0
          OR projected_object_overlap_ratio > 0
vertical_gap_subject_on_object = subject_bottom_z - object_top_z
normalized_distance_xy = distance_xy / mean_diag_xy
```

OBB fallback status rule:

| Status | 기준 | Reason code |
| --- | --- | --- |
| `satisfied` | `overlap == true` AND `abs(vertical_gap_subject_on_object) <= 0.30m` | `projected_overlap_and_small_vertical_gap` |
| `violated` | `overlap == false` AND `normalized_distance_xy >= 2.0` AND `abs(vertical_gap_subject_on_object) >= 0.30m` | `no_projected_overlap_and_large_gap` |
| `uncertain` | 위 조건으로 명확히 자르기 어려운 경우 또는 feature missing | `support_contact_obb_ambiguous`, `missing_support_contact_geometry` |

Paper-facing selected rule은 `point_subtype` variant다. 이 variant는 support/contact
predicate를 subtype으로 나눈 뒤 point/local evidence를 사용한다.

| Subtype | 예 | 핵심 evidence |
| --- | --- | --- |
| `legged_floor_support` | object가 floor 위에 서 있음 | low-percentile support gap, support point density |
| `soft_support_contact` | pillow/cushion/blanket/clothes 등 soft object | penetration 허용 범위, positive float gap, support density |
| `rigid_object_on_furniture` | table/desk/shelf/chair/bed 등 rigid support | horizontal support plane, plane gap, plane confidence, local support points |
| `geometry_quality_uncertain` | segmentation/instance issue | hard valid/invalid로 자르지 않고 uncertain |

Point/local support threshold는 다음과 같다.

| Threshold | 값 | 의미 |
| --- | ---: | --- |
| `min_support_points_under_subject` | 10 | subject 아래 support object point가 충분히 있어야 함 |
| `xy_expansion_steps_m` | 0.00, 0.05, 0.10, 0.20 | subject footprint 주변 local support search 확장 |
| `max_expansion_for_primary_m` | 0.10m | primary local support로 인정하는 최대 XY 확장 |
| `local_vertical_gap_abs_max_m` | 0.10m | local point support gap satisfied 기준 |
| `local_vertical_gap_abs_relaxed_m` | 0.15m | uncertain band 기준 |
| `plane_gap_pass_abs_m` | 0.08m | rigid support plane gap pass 기준 |
| `plane_gap_fail_abs_m` | 0.22m | rigid support plane gap fail 기준 |
| `plane_min_inlier_count` | 10 | horizontal plane 추정 최소 inlier |
| `satisfied_score_min` | 0.70 | subtype consistency score가 이 이상이면 satisfied |
| `uncertain_score_min` | 0.40 | 이 이상 0.70 미만이면 uncertain, 그 미만은 violated |

Support/contact의 최종 status는 subtype별 consistency score로 결정된다.

```text
score >= 0.70 -> satisfied
0.40 <= score < 0.70 -> uncertain
score < 0.40 -> violated
```

단, rigid support에서 horizontal plane 자체가 추정되지 않으면 hard violation으로
밀어붙이지 않고 `uncertain`으로 둔다. 이는 support/contact가 segmentation quality와
local surface reconstruction에 민감하기 때문이다.

| Condition | 실제 ranking score / 처리 | 의미하는 비교 질문 |
| --- | --- | --- |
| `semantic_only` | 원래 source의 `semantic_ranking_score`만 사용한다. | geometry를 전혀 보지 않았을 때의 기본 failure와 recall을 측정한다. |
| `probabilistic_recalibrated` | `semantic_ranking_score * p_geom_valid`로 re-ranking한다. Row를 강제로 삭제하지 않고, geometry validity가 낮은 prediction을 아래로 내린다. | semantic plausibility와 calibrated physical consistency를 함께 보았을 때 violation이 줄고 recall이 유지되는가? |
| `rule_verified_point_subtype` | frozen rule verifier가 `violated`로 판정한 row를 hard-filter한다. `support_contact`에서는 point/local contact와 support subtype evidence를 우선 사용하고, 다른 family는 OBB/centroid 기반 evidence로 위임한다. | violation을 거의 0으로 만드는 보수적 operating point에서 recall cost가 얼마나 되는가? 단순 probability가 아니라 rule-level contradiction을 제거하면 어떤 일이 생기는가? |
| `family_specific_p_geom_valid` | `semantic_ranking_score * p_geom_valid_family_specific`로 re-ranking한다. Family별로 distance, vertical order, support evidence의 scale과 의미가 다르므로 별도 calibration을 사용한다. | 하나의 global geometry score보다 relation family별 calibration이 reliability/recall tradeoff를 더 잘 맞추는가? |
| `control_p_geom_valid_only` | `p_geom_valid`만으로 ranking한다. semantic score는 버린다. | geometry validity만으로 relation prediction을 잘할 수 있는가? 낮은 성능이면 H001이 geometry-only predictor가 아니라 semantic+geometry reliability framework라는 점을 보여준다. |
| `control_distance_only` | `1 / (1 + distance_3d)`로 ranking한다. 여기서 `distance_3d`는 geometry join이 계산한 object-pair 3D distance feature이며, 가까운 pair일수록 점수가 높다. | 결과가 “가까운 물체쌍을 위로 올린 것”만으로 설명되는가? 특히 `higher/lower`나 `support`는 단순 거리만으로는 predicate meaning을 설명할 수 없다. |
| `control_shuffled_geometry` | `semantic_ranking_score * shuffled_family_p_geom_valid`를 사용한다. Family별 geometry score 분포는 보존하지만, prediction row와 geometry score의 identity를 섞는다. | 개선이 단순히 좋은 score 분포를 곱해서 생긴 것인가, 아니면 정확한 object-pair geometry가 붙어야 하는가? |
| `control_wrong_pair_geometry` | `semantic_ranking_score * wrong_pair_p_geom_valid`를 사용한다. 같은 평가 protocol 안에서 다른 object-pair의 geometry validity를 붙인다. | 같은 scene 또는 같은 distribution의 geometry라도 subject-object identity가 틀리면 개선이 사라지는가? |

이 비교군이 중요한 이유는 reviewer가 제기할 수 있는 단순 대안을 직접 막기
때문이다. `control_distance_only`가 높으면 “그냥 가까운 순서로 정렬하면 된다”는
해석이 가능하고, `control_p_geom_valid_only`가 높으면 “semantic model 없이 geometry
rule만 쓰면 된다”는 해석이 가능하다. 하지만 현재 결과에서는 semantic score, pair
identity, family-specific geometry evidence가 함께 있을 때 가장 안정적인
recall/violation tradeoff가 나온다.

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

이를 더 풀어 쓰면 다음과 같다. `GT-positive relation`은 3DSSG annotation에 실제로
존재한다고 표시된 relation row다. 만약 verifier가 이런 row를 자주 `violated`로
판정한다면, H001 verifier는 dataset의 ground-truth semantics와 충돌하는 잘못된
rule일 가능성이 크다. 현재 positive nonviolated rate 0.9965는 GT-positive 3,972개
중 대부분을 `satisfied` 또는 `uncertain`으로 남기고, 잘못된 hard rejection을 거의
하지 않는다는 뜻이다.

반대로 `deterministic counterfactual negative`는 GT-positive row에서 predicate
방향이나 geometry 의미가 성립하지 않도록 만든 negative row다. 예를 들어 위/아래
관계를 뒤집거나, 실제로 가까운 pair가 아닌 관계를 가까운 관계처럼 두는 식으로
geometry 상 성립하면 안 되는 비교군을 만든다. Verifier가 이런 negative를 자주
`satisfied`로 본다면 너무 느슨한 rule이 된다. 현재 negative nonsatisfied rate
0.9673은 counterfactual negative 대부분을 `violated` 또는 `uncertain`으로 처리하고,
잘못해서 “geometry가 만족된다”고 받아들이는 경우가 적다는 뜻이다.

따라서 `p_geom_valid`는 임의로 만든 penalty가 아니라, GT-positive와 deterministic
negative를 높은 AUROC/AUPRC로 구분하는 reliability signal이다. 이 신호를 semantic
score에 곱하면 “의미적으로 그럴듯한 prediction” 중에서도 실제 3D geometry와 맞는
row를 더 위에 두고, geometry와 모순되는 row를 아래로 내릴 수 있다.

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

쉽게 말하면 qualitative cases는 “숫자가 왜 그렇게 나왔는지”를 실제 relation row
단위로 보여주는 해석 자료다. 예를 들어 Open3DSG가 `floor -> ceiling`에 대해
`higher than`을 높은 semantic rank로 낼 수 있다. 두 object label은 scene 안에서
자주 함께 등장하므로 semantic model 입장에서는 그럴듯해 보일 수 있다. 하지만
geometry를 보면 floor는 ceiling보다 낮으므로 이 relation은 물리적으로 반대다.
이때 geometry-aware re-ranking은 해당 row의 `p_geom_valid`를 낮게 주고 top-K 밖으로
내린다.

또 다른 예로 `object -> ceiling`에 대해 `standing on`이 semantic top-K에 들어올 수
있다. 단어만 보면 object가 어떤 surface 위에 있을 법하지만, 실제 support plane과
vertical gap을 보면 ceiling 위에 서 있는 물체가 아니므로 `plane_gap_large`나 support
subtype reason으로 demotion된다. `close by`도 마찬가지다. 두 물체가 한 scene에 같이
등장한다는 사실만으로는 충분하지 않고, normalized XY distance가 실제로 가까워야
한다.

반대로 promoted/retained case는 H001이 단순히 prediction을 삭제하는 방법이 아님을
보여준다. Semantic rank는 낮았지만 geometry가 강하게 지지하는 relation은
geometry-aware score에서 위로 올라갈 수 있다. 그래서 본 논문은 “violation을 줄였다”
뿐 아니라 `R@K`와 `Violation@K`를 같이 보고한다. 만약 demotion만 있었다면 recall
sacrifice라는 공격을 받기 쉽지만, 현재 qualitative case와 metric은 geometry가
불일치 row를 내리고, 일부 일치 row를 유지하거나 올리는 방향으로 작동함을 보여준다.

마지막으로, `p_geom_valid`가 높지만 hard rule상 `violated`로 남는 case도 있다. 이
case들은 calibration이 완벽하지 않다는 residual risk를 드러낸다. 그래서 H001은
`probabilistic_recalibrated` 하나만 보고하지 않고, `rule_verified_point_subtype`,
`family_specific_p_geom_valid`, GT verifier evaluation, qualitative queue를 함께
제시한다. 이는 약점을 숨기는 것이 아니라, reliability layer의 operating point와
한계를 분리해서 보고하는 방식이다.

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
| P4 | Qwen-VL은 appendix/extension evidence로 유지할지, main/table로 승격할지 명시적 paper-claim decision 필요 | full official validation downstream metric까지 완료됐다. 다만 Qwen은 crop 기반 modern VLM semantic source이고 recall이 VL-SAT/Open3DSG보다 낮으므로, 현재는 main baseline 대체보다 modern VLM third-source extension으로 쓰는 편이 안전하다. |

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
