# H002 Summary Branch V2

Last updated: 2026-06-13

## Research Direction

H002는 3D Scene Graph relation prediction에서 relation-level reliability를
다루는 독립 연구 방향이다. 핵심 문제는 relation predictor의 semantic score와
관측된 3D geometry validity가 서로를 충분히 설명하는지, 그리고 기존 relation metric이
이 차이를 충분히 드러내는지 묻는 것이다.

핵심 관점:

```text
semantic plausibility != geometric validity
```

따라서 H002는 relation confidence를 단일 점수로 보지 않고, 최소한 다음 두 축으로
분리한다.

- `semantic plausibility`: source model이 relation label을 얼마나 그럴듯하게
  보는가.
- `geometric satisfiability`: 해당 relation이 관측된 3D object geometry에서
  성립 가능한가.

H002의 목표는 이 mismatch를 양방향 relation-level reliability 문제로 정의하고,
`Relation-Geometric Agreement (RGA)`라는 benchmark/diagnostic framework로
측정하는 것이다.

Bidirectional mismatch:

```text
high semantic + low geometry  = semantic overconfidence / unsafe relation
low semantic + high geometry  = semantic underconfidence / missed or under-ranked relation
```

## Research Background

3D Scene Graph는 object node와 relation edge를 통해 scene structure를 표현한다.
최근 3DSSG, open-vocabulary 3DSG, VLM-based scene graph 방법은 semantic relation
prediction 능력을 확장하고 있지만, relation score가 실제 3D scene의 physical or
geometric consistency와 calibration되어 있는지는 별도 문제다.

예를 들어 다음과 같은 relation은 semantic text/image prior만으로 그럴듯하게
보일 수 있다.

- `standing on`
- `supported by`
- `close by`
- `higher than`
- `lower than`
- `inside`
- `attached to`

하지만 3D geometry에서는 support/contact, vertical order, distance, overlap,
containment, orientation 같은 relation-specific witness가 필요하다. Semantic score가
높아도 geometry witness가 없으면 relation edge는 downstream reasoning, robot
planning, spatial QA, object search에서 신뢰하기 어렵다.

## Motivation

기존 relation prediction metric은 주로 label correctness 또는 triplet recall을
측정한다. 그러나 label이 맞는지와 geometry상 성립하는지는 같은 질문이 아니다.

H002가 보는 failure mode는 이제 단방향이 아니라 양방향이다.

```text
High semantic relation confidence, low or uncertain geometric validity.
Low semantic relation confidence, high geometric satisfiability.
```

첫 번째는 semantic overconfidence 문제다. Semantic source가 그럴듯하다고 본 relation이
관측 geometry에서 성립하지 않는 경우다. 두 번째는 semantic underconfidence 문제다.
Source가 낮게 평가하거나 top-K 밖에 둔 relation이 geometry상 성립 가능하고, GT annotation
또는 predicate ontology 관점에서는 missing/under-ranked relation일 수 있는 경우다.

두 경우 모두 단순 false positive 또는 false negative와 다르다. 어떤 relation은 GT
label에는 없지만 geometry상 plausible할 수 있고, 어떤 relation은 exact label은 맞지만
관측 geometry evidence가 불충분하거나 모순될 수 있다. 따라서 relation reliability를
평가하려면 semantic score, label match, geometry satisfiability, geometry coverage,
object-pair validity를 분리해야 한다.

## Limitation Of Existing Work

기존 연구의 한계는 다음처럼 정리된다.

1. **Label-centric metric 한계**
   - Recall/mAP는 relation label correctness를 보지만, 해당 relation이 observed
     3D geometry에서 성립하는지 별도로 묻지 않는다.

2. **Geometry-aware method의 evaluation 한계**
   - Geometry feature를 relation prediction에 넣는 연구는 있어도, semantic score와
     geometric validity가 언제 충돌하는지를 benchmark axis로 분리하지 않는 경우가
     많다.

3. **Open-vocabulary relation의 reliability 한계**
   - VLM/LLM 기반 relation은 semantic prior가 강하지만, relation-specific geometric
     witness 없이 plausible relation을 과신할 수 있다.

4. **Annotation incompleteness 문제**
   - GT relation annotation은 sparse할 수 있다. 어떤 prediction은 GT에는 없지만
     geometry상 satisfied일 수 있다. 기존 metric은 이를 source false positive,
     missing annotation, relation ambiguity 중 무엇으로 봐야 하는지 분리하지 못한다.

## Problem Definition

H002의 독립 문제 정의:

```text
Given a 3D scene graph relation candidate e = (subject, predicate, object),
evaluate whether its semantic plausibility agrees with its geometric
satisfiability under observed 3D evidence.
```

H002는 relation edge를 다음 상태로 분해한다.

```text
RGA(e) = {
  semantic_axis,
  label_axis,
  geometry_axis,
  coverage_state,
  uncertainty_state
}
```

핵심 bucket:

- `RGA-HH`: high semantic / geometry satisfied
- `RGA-HL`: high semantic / geometry unsatisfied
- `RGA-HU`: high semantic / geometry uncertain
- `RGA-HM`: high semantic / geometry missing or unsupported
- `RGA-LH`: low semantic / geometry satisfied
- `RGA-LL`: low semantic / geometry unsatisfied

Label-geometry bucket:

- exact-label match + geometry satisfied
- exact-label match + geometry violated
- exact-label match + geometry uncertain
- no-GT pair + geometry satisfied
- pair has other predicate + geometry satisfied

이 문제정의의 핵심은 `semantic_score`와 `geometric_validity`를 결합하기 전에 먼저
둘의 agreement/disagreement를 양방향으로 측정하는 것이다. `RGA-HL`은 semantic
overconfidence를, `RGA-LH`는 semantic underconfidence 또는 geometry-supported missed
candidate를 드러낸다.

## Edge Component Rationale And Literature Grounding

H002의 edge representation은 임의로 만든 field 묶음이 아니라, scene graph
prediction, object detection, 3D spatial perception, calibration, incomplete-label
learning에서 반복적으로 쓰인 신뢰도 구성요소를 relation-level reliability 문제에 맞게
재배열한 것이다.

### 1. Semantic Score

정의:

```text
semantic_score = relation source가 predicate edge에 부여한 relation confidence
```

근거:

- Visual Relationship Detection과 Scene Graph Generation은 object pair에 대해
  predicate/relation score를 예측하는 문제로 정식화된다. `Visual Relationship
  Detection with Language Priors`는 subject-object pair의 visual predicate와 language
  prior를 결합해 relationship likelihood를 예측한다.
  Source: https://arxiv.org/abs/1608.00187
- `Neural Motifs`는 scene graph parsing에서 object labels와 context가 relation
  labels를 강하게 예측한다는 점을 보였고, relation prediction이 object-pair semantic
  context에 크게 의존함을 보여준다.
  Source: https://openaccess.thecvf.com/content_cvpr_2018/CameraReady/4272.pdf
- 3DSSG 영역에서는 `VL-SAT`가 3D scene graph predicate prediction을 visual-linguistic
  semantics로 보강한다. 이는 relation source score가 semantic prior를 강하게 포함할
  수 있음을 보여준다.
  Source: https://arxiv.org/abs/2303.14408
- Open-vocabulary 3DSG에서는 `Open3DSG`가 open-set relationship prediction을
  queryable object/relation setting으로 확장한다. 이 경우 relation score는 closed-set
  classifier confidence뿐 아니라 language-conditioned plausibility까지 포함할 수 있다.
  Source: https://arxiv.org/abs/2402.12259

H002에서의 역할:

- `semantic_score`는 relation source가 "이 relation이 그럴듯하다"고 보는 정도다.
- 하지만 semantic score는 geometry validity와 같은 것이 아니다.
- 따라서 H002는 semantic score를 final reliability로 쓰지 않고, geometry axis와
  비교할 한 축으로 둔다.

### 2. Object Confidence

정의:

```text
object_confidence = subject/object class와 object instance detection의 신뢰도
```

근거:

- Object detection은 objectness score와 class score를 통해 detection confidence를
  표현한다. `Faster R-CNN`의 RPN은 object bounds와 objectness score를 예측하고,
  downstream detection은 class-specific score를 사용한다.
  Source: https://arxiv.org/abs/1506.01497
- 3D object detection에서도 object proposal, semantic class, bounding box confidence가
  relation reasoning의 전제가 된다. `VoteNet`은 point cloud에서 object centers,
  3D boxes, semantic classes를 예측한다.
  Source: https://openaccess.thecvf.com/content_ICCV_2019/papers/Qi_Deep_Hough_Voting_for_3D_Object_Detection_in_Point_Clouds_ICCV_2019_paper.pdf
- Scene graph에서는 object label이 relation label을 강하게 제약한다. `Neural Motifs`의
  분석처럼 object label/context가 relation prediction에 큰 영향을 주므로, subject/object
  confidence는 edge reliability의 독립 factor가 될 수 있다.
  Source: https://openaccess.thecvf.com/content_cvpr_2018/CameraReady/4272.pdf
- 3DSSG에서도 object representation quality가 predicate reasoning에 영향을 준다는
  최근 연구 흐름이 있다. Object feature quality가 낮으면 relation accuracy가 같이
  흔들리는 구조이기 때문이다.
  Source: https://openreview.net/forum?id=LjmXrUsSrg

H002에서의 역할:

- 잘못된 object class나 object instance가 주어지면 relation edge가 semantic/geometry
  양쪽에서 모두 왜곡된다.
- 따라서 H002의 full reliability model에서는 subject/object confidence를 별도 factor로
  둔다.
- 현재 H002 smoke에서는 object confidence가 source artifact에 항상 존재하지 않으므로
  optional/unavailable field로 둔다.

### 3. Geometry Evidence

정의:

```text
geometry_evidence = 거리, 높이 차이, 접촉, support, overlap, containment,
orientation 등 relation-specific geometric witness
```

근거:

- 3D scene graph의 장점은 object와 relation을 3D 공간 구조 위에 둔다는 점이다.
  Stanford `3D Scene Graph`는 3D 공간에서 spatially consistent 2D scene graph를
  계산하고 relation을 수치적으로 정량화할 수 있음을 강조한다.
  Source: https://3dscenegraph.stanford.edu/images/3DSceneGraph.pdf
- `SceneGraphFusion`은 RGB-D sequence에서 incremental 3D scene graph를 만들며,
  partial/missing graph data와 geometric reconstruction context가 relation prediction에
  중요함을 보여준다.
  Source: https://openaccess.thecvf.com/content/CVPR2021/papers/Wu_SceneGraphFusion_Incremental_3D_Scene_Graph_Prediction_From_RGB-D_Sequences_CVPR_2021_paper.pdf
- `Hydra`는 real-time 3D scene graph construction and optimization을 spatial perception
  system으로 다룬다. 3D scene graph가 robot mental model로 쓰이려면 semantic labels뿐
  아니라 spatial structure가 필요하다는 방향과 맞다.
  Source: https://www.roboticsproceedings.org/rss18/p050.pdf
- `RelWitness`는 relation witness를 "관측 scene에서 relation을 observable하게 만드는
  concrete visual-geometric cue"로 정의한다. 이는 H002의 geometry evidence 설계와
  가장 직접적으로 연결된다.
  Source: https://arxiv.org/html/2605.20823v2

H002에서의 역할:

- Geometry evidence는 relation family마다 다르다.
- `on/supporting`은 support/contact/vertical gap이 필요하고, `close by`는 distance와
  overlap이 필요하며, `higher/lower`는 vertical order가 필요하다.
- H002는 geometry evidence를 하나의 generic distance score로 축소하지 않고,
  relation-specific witness로 기록한다.

### 4. Geometry Validity

정의:

```text
geometry_validity = 관측된 geometry evidence가 해당 relation을 지지할 가능성
```

근거:

- `RelWitness`는 visual-geometric witness verifier를 통해 unannotated relation
  candidates를 verified missing positive, reliable negative, uncertain unlabeled case로
  나누는 방향을 제안한다.
  Source: https://arxiv.org/html/2605.20823v2
- Incomplete-label scene graph 연구는 unannotated relation을 단순 negative로 취급하면
  문제가 생긴다고 본다. `Scene Graph Prediction with Limited Labels`는 sparse,
  incomplete relationship labels를 다루기 위해 probabilistic relationship labels와
  factor graph-based generative model을 사용한다.
  Source: https://arxiv.org/abs/1904.11622
- 2D scene graph 쪽에서도 missing relation을 보완하거나 impute하는 연구가 반복되어
  왔다. `Not All Relations Are Equal`은 missing informative relations를 impute하는
  방향을 제안한다.
  Source: https://openaccess.thecvf.com/content/CVPR2022/papers/Goel_Not_All_Relations_Are_Equal_Mining_Informative_Labels_for_Scene_CVPR_2022_paper.pdf

H002에서의 역할:

- Geometry validity는 hard rule label만이 아니라, geometry evidence가 relation을
  얼마나 지지하는지 나타내는 reliability signal이다.
- 단, H002의 `RGA-HL`은 probability threshold로 만들지 않는다. Primary bucket은
  deterministic geometry status로 만들고, probability는 disagreement/uncertainty 분석에
  사용한다.

### 5. Disagreement Score

정의:

```text
disagreement_score = semantic_score와 geometry_validity 사이의 불일치 정도
```

근거:

- Confidence calibration 연구는 model confidence와 empirical correctness가 일치하는지
  측정한다. `On Calibration of Modern Neural Networks`는 reliability diagram과 ECE를
  통해 confidence와 accuracy의 gap을 측정하는 표준 문제를 만든다.
  Source: https://arxiv.org/pdf/1706.04599
- `Measuring Calibration in Deep Learning`은 ECE 같은 calibration metric이 실제로
  confidence와 correctness 차이를 요약하는 방식과 그 한계를 분석한다.
  Source: https://openaccess.thecvf.com/content_CVPRW_2019/papers/Uncertainty%20and%20Robustness%20in%20Deep%20Visual%20Learning/Nixon_Measuring_Calibration_in_Deep_Learning_CVPRW_2019_paper.pdf
- H002의 disagreement는 일반 classification calibration과 다르다. 여기서 비교하는 것은
  `confidence vs label accuracy`가 아니라 `semantic relation confidence vs geometric
  satisfiability`다.

H002에서의 역할:

- Disagreement score는 high semantic / low geometry edge를 정량화한다.
- 예:

```text
disagreement_score = max(0, semantic_score_norm - geometry_validity)
```

- 이 score는 final answer가 아니라 audit prioritization, failure taxonomy, source
  comparison을 위한 diagnostic이다.

### 6. Uncertainty

정의:

```text
uncertainty = evidence가 부족하거나 relation-specific witness가 ambiguous한 상태
```

근거:

- Incremental 3D scene graph에서는 partial observation과 missing graph data가 자연스럽게
  발생한다. `SceneGraphFusion`은 incremental reconstruction setting에서 partial/missing
  data를 다루는 attention mechanism을 제안한다.
  Source: https://openaccess.thecvf.com/content/CVPR2021/papers/Wu_SceneGraphFusion_Incremental_3D_Scene_Graph_Prediction_From_RGB-D_Sequences_CVPR_2021_paper.pdf
- `RelWitness`도 unannotated relation을 positive/negative로 바로 결정하지 않고 uncertain
  unlabeled case로 둘 수 있는 구조를 둔다.
  Source: https://arxiv.org/html/2605.20823v2
- Calibration/uncertainty 연구에서는 confidence와 error/uncertainty mismatch를 별도로
  측정한다. 이는 H002가 `uncertain`을 valid나 invalid에 섞지 않고 별도 bucket으로
  두는 근거가 된다.
  Source: https://proceedings.nips.cc/paper/2020/file/d3d9446802a44259755d38e6d163e820-Paper.pdf

H002에서의 역할:

- `uncertain`은 실패가 아니라 관측/geometry evidence가 부족한 상태다.
- H002는 `uncertain`을 `valid` 또는 `invalid`로 강제하지 않는다.
- 이 선택은 relation-level reliability에서 coverage와 observability를 분리하기 위해
  필요하다.

## Core Hypothesis

H002의 core hypothesis:

```text
3D Scene Graph relation reliability cannot be fully evaluated by semantic score
or label recall alone. Relation confidence must be audited through
bidirectional semantic-geometric agreement, because semantic plausibility and
geometric satisfiability can diverge in both directions at relation level.
```

더 구체적인 검증 가설:

1. Semantic top-K relation 중 geometry-supported, geometry-violated,
   geometry-uncertain, geometry-unsupported row의 비율은 source별로 다르다.
2. Exact-label correctness와 geometry satisfiability는 완전히 같은 축이 아니다.
3. GT에는 없는 relation 중 geometry상 satisfied인 row가 존재하며, 이는 annotation
   sparsity, relation ambiguity, source false positive를 분리해 audit해야 한다.
4. Semantic top-K 밖의 relation 중 geometry상 satisfied인 row가 존재하며, 이는
   source underconfidence, annotation coverage, ontology mismatch, geometry-trivial
   relation을 분리해 audit해야 한다.
5. H002가 독립 연구가 되려면 `RGA`가 기존 label recall 또는 violation metric이
   드러내지 못하는 denominator/uncertainty/annotation-incompleteness insight를
   제공해야 한다.

## Proposed Framework

H002의 framework는 method-first가 아니라 benchmark-first 구조다.

### 1. Relation Candidate Projection

각 source relation prediction을 identity-preserving row로 정리한다.

필수 field:

- source id
- scan/subgraph id
- subject/object id
- predicate label/family
- semantic score/rank
- geometry status
- label match status
- provenance

### 2. Geometry Satisfiability Axis

Relation family별 geometric witness를 사용해 relation edge를 다음 상태로 둔다.

- `satisfied`
- `violated`
- `uncertain`
- `unsupported`
- `missing`

중요한 원칙:

- `uncertain`을 valid 또는 invalid로 섞지 않는다.
- `unsupported`를 제거하지 않고 coverage로 보고한다.
- `violated`는 `p_geom_valid` threshold가 아니라 deterministic geometry status로
  정의한다.

### 3. RGA Metric Layer

주요 metric:

- `RGA-HL@K`: semantic top-K 중 geometry-unsatisfied 비율.
- `RGA-LH-tail@K`: semantic top-K 밖 또는 low-rank band 중 geometry-satisfied 비율.
- `RGA-valid@K`: semantic top-K 중 geometry-satisfied 비율.
- `RGA-uncertain@K`: semantic top-K 중 geometry-uncertain 비율.
- `RGA-coverage@K`: semantic top-K 중 geometry-checkable 비율.
- label-geometry cross-tab: exact/family/no-GT status와 geometry status의 조합.

### 4. Annotation/Metric Disagreement Audit

`no_gt_for_pair + geometry_satisfied` row를 audit하여 다음을 분리한다.

- annotation sparsity
- source false positive
- label granularity mismatch
- object-pair mismatch
- genuinely valid unlabeled relation
- relation ambiguity

### 5. Bidirectional Mismatch Audit

`RGA-HL`과 `RGA-LH`를 함께 audit한다.

- `RGA-HL`: high semantic but geometry unsatisfied/uncertain.
  - relation suppression, relabel, repair 후보.
- `RGA-LH`: low semantic or outside-top-K but geometry satisfied.
  - missed relation discovery, annotation sparsity, ontology mismatch,
    delayed promotion 후보.

단, `RGA-LH`는 자동 promotion signal이 아니다. 특히 `close by`, `higher than`,
`standing on floor` 같은 relation은 geometry상 쉽게 성립할 수 있으므로 object-pair
validity와 relation informativeness audit이 필요하다.

### 6. Optional Rescoring

Factor graph 또는 posterior rescoring은 현재 H002의 core claim이 아니다.
RGA benchmark가 충분히 독립적인 문제로 성립한 뒤에만 다음 형태로 확장한다.

```text
P(edge reliability | semantic evidence, label evidence, geometry evidence,
coverage, uncertainty)
```

이 단계 전에는 `posterior_edge_valid`를 `p_geom_valid`와 동일시하지 않는다.

## Initial Evidence

현재 H002의 hypothesis-stage 진단은 다음을 보였다.

1. 전체 prediction/geometry row projection은 두 source에서 가능하다.
   - `VL-SAT`: 957,008 rows
   - Open3DSG recovery: 695,916 rows

2. Semantic top-K 기준 RGA coverage는 약 1/3 수준이다.
   - 많은 relation row가 current geometry policy 밖에 있다.
   - 이는 relation-level reliability에서 coverage 자체가 중요한 denominator임을
     보여준다.

3. H001과 같은 scoped selection을 쓰면 `RGA-HL@K`는 기존 `Violation@K`로
   붕괴한다.
   - 따라서 `RGA-HL@K`를 단순 replacement metric으로 주장하면 안 된다.

4. All-row direct GT join에서 exact-label + hard geometry violation은 매우 적다.
   - `VL-SAT`: 14 rows
   - Open3DSG recovery: 11 rows

5. 남는 주요 신호는 `no_gt_for_pair + geometry_satisfied`다.
   - `VL-SAT`: 66,342 rows
   - Open3DSG recovery: 49,775 rows

6. High-rank no-GT+satisfied audit에서 round-1과 second-review가 모두 H002의 claim
   boundary를 좁혔다.
   - Direct second-review patch 후 positive-signal bucket:
     `label_granularity_mismatch + annotation_sparsity_likely +
     plausible_unlabeled_relation = 182 / 192`.
   - 그러나 `support_contact / plausible_unlabeled_relation`은 endpoint identity와
     predicate semantics에 민감하다.
   - 따라서 geometry-satisfied row를 missing positive로 바로 승격하지 않는다.

7. `RGA-LH` diagnostic은 low-semantic/high-geometry mismatch가 두 source에서 모두
   큰 규모로 존재함을 보였다.
   - Combined `RGA-LH-tail`: 134,177 rows.
   - Combined `RGA-LH-tail` rate: 0.3904.
   - Exact-match LH: 1,976 rows.
   - no-GT LH: 103,167 rows.
   - 이는 H002가 `RGA-HL`만이 아니라 `RGA-LH`까지 포함하는 bidirectional benchmark로
     가야 함을 뒷받침한다.

현재 해석:

```text
H002의 강한 방향은 factor graph rescoring이 아니라 bidirectional RGA benchmark와
annotation / metric disagreement audit이다.
```

## Experiment Plan

### Dataset / Source

초기 source:

- `VL-SAT`
- Open3DSG recovery branch

향후 확장 후보:

- Qwen-VL relation source
- ReplicaSSG or ScanNet-derived graph
- manually audited subset

### Metrics

Primary:

- `RGA-HL@50`, `RGA-HL@100`
- `RGA-LH-tail@50`, `RGA-LH-tail@100`, or rank-band `RGA-LH`
- `RGA-valid@50`, `RGA-valid@100`
- `RGA-uncertain@50`, `RGA-uncertain@100`
- `RGA-coverage@50`, `RGA-coverage@100`
- exact-label / family-label / no-GT label-geometry cross-tab

Diagnostic:

- exact+violated count
- exact+uncertain count
- no-GT+satisfied count
- pair-other+satisfied count
- per-family target counts
- visual/annotation audit taxonomy

### Baselines

Core executable comparison:

1. `semantic-only`
   - source relation score/rank만 사용한다.
2. `geometry-only`
   - `p_geom_valid`를 사용한다.
   - 여기서 `p_geom_valid`는 geometry evidence/residual에서 만든 calibrated
     geometry validity proxy다.
3. `semantic + geometry`
   - semantic score와 `p_geom_valid`의 product 또는 2-factor calibrated score를
     사용한다.
   - H001에서 확보한 geometry-aware reranking evidence를 이 baseline으로 재사용할
     수 있다.
4. `factorized reliability posterior`
   - semantic score, object confidence, geometry factor, uncertainty, provenance를
     분리해 relation-level reliability posterior를 계산한다.

Diagnostic ablations:

- hard-rule/status-only filter
- no-uncertainty posterior
- no-object-confidence posterior
- pooled vs family-specific geometry calibration

H002가 주장해야 하는 것은 baseline performance improvement가 아니라, 기존 metric이
분리하지 못하는 agreement/coverage/annotation states를 드러내는 것이다.

## Current Decision

현재 판단:

```text
H002는 H001에서 확보한 geometry validity factor를 기반으로 relation-level
reliability를 양방향 RGA benchmark/problem으로 확장하는 branch로 유지한다.
단, hypothesis-stage diagnostics는 train set에서 다시 수행해야 한다.
```

Scope correction:

- `14_lh_diagnostic.md`와 `15_lh_audit.md`는 H001 `full_validation` artifacts에서
  만든 결과다.
- 따라서 현재 두 문서는 workflow feasibility / held-out diagnostic 용도로만 둔다.
- hypothesis selection, threshold choice, method design, baseline contract는 train-set
  RGA diagnostic 이후에만 진행한다.

Blocked:

- factor graph method claim
- H002가 기존 geometry recalibration보다 원리적으로 우월하다는 claim
- exact-label-correct relation이 자주 geometry-violated라는 claim
- validation-derived LH audit 결과를 hypothesis evidence로 사용하는 것

Allowed:

- semantic score와 geometric validity의 양방향 mismatch를 relation-level reliability
  문제로 정의
- RGA benchmark/diagnostic framework
- coverage, uncertainty, annotation incompleteness audit
- no-GT but geometry-satisfied relation의 taxonomy 분석
- low-semantic but geometry-satisfied relation의 source-underconfidence /
  annotation-coverage / ontology-mismatch audit

## Current Train Gate

완료된 gate:

```text
18_train_source_contract.md
19_train_raw_dump_runner.md
20_train_adapter_export.md
21_train_geometry_join.md
22_train_rga_rows.md
23_train_rga_audit.md
24_train_manual_audit.md
25_factor_contract.md
26_factor_dataset.md
27_factor_smoke.md
28_shortcut_control.md
29_target_redesign.md
30_redesigned_target_smoke.md
31_human_confirmation_protocol.md
```

결과:

- Open3DSG train pilot scope를 validation artifact 없이 고정했다.
- `relationships_train_pilot.json` 기준으로 100 train subgraphs / 100 scans를 선택했다.
- primary geometry-checkable families인 `proximity`, `relative_vertical`,
  `support_contact`가 모두 pilot 안에 포함된다.
- Open3DSG adapter `contract-only` check에서 100 contexts를 정상 확인했다.
- H002 전용 Open3DSG train pilot runtime을
  `local_dataset/Open3DSG_staged/h002_train_pilot_runtime`에 stage했다.
- Docker preflight는 container 내부에서 `status: ready`로 통과했다.
- PyTorch GPU check에서 `torch.cuda.is_available() == True`, `cuda_count == 1`을
  확인했다.
- train raw dump job은 `exit code 0`, `100/100` batches로 완료됐다.
- raw dump는 4,626 rows를 생성했고, H002 repair 후 4,615 rows로 adapter에 입력했다.
- adapter export는 `status: ready`, `118,560` prediction rows, duplicate prediction id
  `0`으로 완료됐다.
- H001 adapter의 hardcoded validation provenance는 H002 post-fix로
  `relationships_train_pilot.json`으로 정규화했다.
- train geometry join은 `status: ready`, `118,560` verification rows,
  row mismatch `0`으로 완료됐다.
- geometry-checkable rows는 `27,360`, unsupported-family rows는 `91,200`이다.
- selected `point_subtype` policy 기준 status는 `satisfied=12,285`,
  `uncertain=11,841`, `violated=3,234`, `unsupported=91,200`이다.
- train RGA row export는 `status: ready`, `118,560` rows, validation error `0`으로
  완료됐다.
- H002 status 기준 geometry는 `satisfied=12,285`, `uncertain=11,841`,
  `unsatisfied=3,234`, `unsupported=91,200`이다.
- train Top100 기준 `RGA-HL@100=3.87%`, `RGA-valid@100=57.41%`,
  `RGA-uncertain@100=38.71%`, `RGA-coverage@100=12.14%`다.
- train tail 기준 `RGA-LH-tail@100=44.32%`, `RGA-LL-tail@100=12.19%`,
  `RGA-LU-tail@100=43.49%`다.
- train audit queue는 `HL=47` rows, `LH=11,588` rows다.
- `posterior_edge_valid`는 전부 null이고, `p_geom_valid`는 geometry-only continuous
  evidence로만 유지했다.
- train RGA audit seed는 `status: ready`, total `217` rows로 생성됐다.
- HL은 `47/47` rows 전부 seed에 포함했고, LH는 priority/stratified sampling으로
  `170/11,588` rows를 seed에 포함했다.
- LH exact/family-positive rows는 `1,146` rows (`9.89%`)이고, no-GT rows는
  `7,985` rows (`68.91%`)다.
- LH no-GT 중 proximity는 `3,070` rows (`38.45%`)라 dense spatial relation noise
  위험이 크다.
- factorized reliability는 `P(R_e | S_e, L_e, G_e, C_e, U_e)` 형태로 정리했지만,
  아직 factor weight나 calibrated posterior는 학습하지 않았다.
- train manual-audit review bundle은 `status: ready`, `217` rows, contact sheets
  `217`장으로 생성됐다.
- all audit seed rows have subject/object visual assets and mesh/instance links.
- machine-assisted working labels are `ontology_mismatch=63`,
  `true_underconfidence=48`, `semantic_overconfidence=45`,
  `annotation_sparsity=28`, `uncertain_needs_visual_or_mesh=22`,
  `dense_relation_noise=11`.
- working labels are not paper-locked human annotations. Human-confirmed share is
  `0.0`.
- agent visual spot-check는 2건만 수행했고, `semantic_overconfidence` 1건과
  `true_underconfidence` 1건이 working label과 일치했다.
- train factor contract는 `status: ready`로 생성됐다.
- deployable posterior는 `P(R_e=1 | S_e, G_e, C_e, U_e)`로 고정하고,
  `P(R_e=1 | S_e, L_e, G_e, C_e, U_e)`는 oracle diagnostic only로 분리했다.
- `L_e`는 train supervision, calibration target, evaluation stratification,
  oracle diagnostic에는 사용할 수 있지만 deployment-time input feature로는 금지했다.
- strict target은 positive `48`, negative `45`, excluded `124`, usable `93` rows다.
- weak target은 positive `76`, negative `56`, excluded `85`, usable `132` rows다.
- main baseline contract는 `semantic_only`, `geometry_only`,
  `semantic_plus_geometry`, `factorized_reliability_posterior` 4개로 고정했다.
- train factor dataset은 `status: ready`로 생성됐다.
- deployable feature rows는 `118,560`개이며, label/audit evidence는 deployable
  feature block에서 제외했다.
- factor target join은 `217/217` rows로 누락 없이 완료됐다.
- strict smoke input은 `93` rows (`positive=48`, `negative=45`)이고, weak smoke
  input은 `132` rows (`positive=76`, `negative=56`)다.
- forbidden deployable feature key scan에서 target/label leakage는 발견되지 않았다.
- 이 단계에서도 validation artifact는 사용하지 않았다.
- train factor smoke는 `status: ready_with_shortcut_caveat`로 완료됐다.
- strict train-internal 5-fold에서는 네 baseline 모두 AUROC/AUPRC `1.0`에 도달했다.
  이는 posterior novelty 증거가 아니라 strict target이 HL-vs-LH shortcut에 가깝다는
  증거로 해석해야 한다.
- weak train-internal 5-fold에서는 `semantic_only=0.9563/0.9681`,
  `geometry_only=0.9603/0.9701`, `semantic_plus_geometry=0.9739/0.9813`,
  `factorized_reliability_posterior=0.9746/0.9818` AUROC/AUPRC를 보였다.
- weak에서 factorized posterior가 가장 높지만, `semantic_plus_geometry` 대비 차이가
  작고 target construction에 의존하므로 method advantage claim은 금지한다.
- strict shortcut audit에서 negative `45/45` rows는
  `top100_and_unsatisfied=1`, positive `48/48` rows는
  `tail_gt100_and_satisfied=1`로 완전히 분리됐다.
- train shortcut control은 `status: ready_target_not_independent`로 완료됐다.
- explicit RGA shortcut, deterministic geometry status, semantic rank/top-K,
  predicate category를 제거해도 strict target은 `continuous_core`와
  `geometry_continuous_only`에서 train-internal 5-fold AUROC/AUPRC `1.0/1.0`을
  유지했다.
- weak target도 shortcut control 후 `continuous_core=0.9495/0.9620`,
  `geometry_continuous_only=0.9610/0.9715` AUROC/AUPRC를 보여 현재 target이 여전히
  construction signal에 강하게 의존함을 확인했다.
- 결론: 현재 target은 representation plumbing/debugging에는 유용하지만,
  `factorized_reliability_posterior` novelty를 검증할 독립 target은 아니다.
- train target redesign은 `status: ready_target_v2_contract`로 완료됐다.
- 이전 `strict_binary_target`과 `weak_binary_target`은 method claim용 target에서
  제외했다. 이유는 `HL vs LH` 또는 `satisfied vs unsatisfied`를 거의 그대로
  재구성하기 때문이다.
- target v2의 primary target은 `strict_proximity_informativeness`로 고정했다:
  `geometry_status=satisfied`, `predicate_family=proximity` 안에서
  `true_underconfidence` positive `16` rows와 `dense_relation_noise` negative `11`
  rows를 비교한다.
- target v2 sensitivity target은 `weak_satisfied_actionability`로 두었다:
  `geometry_status=satisfied` 안에서 `true_underconfidence + annotation_sparsity`
  positive `76` rows와 `dense_relation_noise` negative `11` rows를 비교한다.
- `ontology_mismatch`는 binary target이 아니라 relabel-only로, `semantic_overconfidence`
  는 RGA-HL diagnostic으로, `uncertain_needs_visual_or_mesh`는 abstain으로 분리했다.
- posterior 성능 claim은 human-confirmed label 전까지 금지한다.
- redesigned target smoke는 `status: ready_plumbing_only`로 완료됐다.
- `strict_proximity_informativeness`는 train-internal 5-fold 기준
  `drop_direct_identity=0.8864/0.9217`, `safe_continuous=0.8409/0.8975`,
  `geometry_continuous_only=0.8523/0.8986`, `semantic_raw_only=0.5483/0.7204`
  AUROC/AUPRC를 보였다.
- strict target v2는 이전 target보다 shortcut-prone하지 않지만 `N=27`이라 posterior
  evidence가 아니라 human confirmation 후보로만 둔다.
- `weak_satisfied_actionability`는 `safe_continuous=0.9115/0.9877`,
  `semantic_raw_only=0.8906/0.9855` AUROC/AUPRC로 높게 나오며, family/source selection
  bias가 남아 sensitivity-only로 유지한다.
- 결론: 다음 작업은 추가 fitting이 아니라 human confirmation protocol이다.
- human confirmation protocol은 `status: ready_protocol_no_human_labels`로 생성됐다.
- strict primary queue는 `27` rows이고 contact sheet `27/27`, mesh link `27/27`를
  가진다.
- weak extension queue는 `87` rows이고 contact sheet `87/87`, mesh link `87/87`를
  가진다.
- final human label은 `reliable_promote -> positive`,
  `unreliable_dense_noise -> negative`, `relabel_only / abstain_uncertain /
  invalid_pair / geometry_artifact -> excluded`로 고정했다.
- hypothesis-stage posterior plumbing smoke 재개 조건은 strict 27 rows completion,
  required field completion, usable binary rows `>=20`, per-class rows `>=8`이다.
- paper-level label-quality gate는 2 reviewers, exact final-label agreement `>=0.75`
  또는 conflict adjudication을 요구한다.
- 사용자 지시에 따라 strict primary queue 27 rows에 Codex bootstrap label을
  `(codex_ver)` reviewer id로 채웠다.
- original blank `strict_review_sheet.tsv`는 human review template로 보존했고,
  Codex-filled sheet는 `strict_review_sheet_codex_ver.tsv`로 분리했다.
- Codex label mapping은 `true_underconfidence -> reliable_promote -> 1`,
  `dense_relation_noise -> unreliable_dense_noise -> 0`이다.
- readiness validation 결과는 `ready_for_train_only_codex_plumbing_smoke`다:
  completed rows `27/27`, usable binary rows `27`, positive `16`, negative `11`,
  missing required fields `0`, invalid values `0`, per-class minimum `11`.
- `(codex_ver)` label은 human-confirmed label이 아니며, paper evidence,
  posterior advantage claim, reviewer agreement evidence로 사용할 수 없다.
- point cloud + multi-view를 H002에 넣는 방향은 합리적이지만, 새 relation
  predictor가 아니라 RGA evidence axis expansion으로 정의해야 한다. 즉,
  `P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)` 형태의
  semantic-geometry-visual agreement 확장으로 본다.
- multi-view는 즉시 model input으로 넣지 않고, 먼저 audit/confirmation evidence로
  사용해 `true_underconfidence`, `dense_relation_noise`, `annotation_sparsity`,
  `uncertain_needs_visual_or_mesh`를 human-confirmable label로 바꾸는 데 사용한다.
- `(codex_ver)` strict label smoke는 `ready_plumbing_only_codex_labels`로 완료됐다.
  train-internal 5-fold에서 `semantic_only` AUROC/AUPRC `0.6080/0.7431`,
  `geometry_only` `0.8523/0.8986`, `semantic_plus_geometry` `0.8864/0.9217`,
  `factorized_reliability_posterior` `0.8864/0.9339`를 보였다.
- 이 smoke는 `N=27`이고 Codex bootstrap label이므로 posterior advantage가 아니라
  pipeline viability만 보여준다. 다음 gate는 multi-view audit protocol이다.
- multi-view audit protocol은 `ready_audit_only_vmv_deferred`로 생성됐다.
  현재 결정은 `V_mv_e`를 model input으로 추가하지 않고, 기존
  `P(R_e = 1 | S_e, G_e, C_e, U_e)` 검증을 먼저 수행하는 것이다.
- multi-view audit sheet는 strict proximity current target `27` rows,
  future-family `support_contact` `26` rows, lower-priority `relative_vertical`
  `34` rows를 포함한다. 모든 candidate `87` rows는 contact sheet와 mesh link를
  가진다.
- factorized validation plan은 `ready_validation_plan_vmv_deferred`로 생성됐다.
  현재 검증 대상은 `P(R_e = 1 | S_e, G_e, C_e, U_e)`이며, `V_mv_e`는 model input에서
  제외된다.
- hypothesis-stage target minimum은 human-confirmed 또는 independent audit label
  `60` usable rows, per-class `20` rows로 고정했다. `(codex_ver)` label은 충분하지
  않다.
- `factorized_reliability_posterior`가 H002 가설을 지지하려면
  `semantic_plus_geometry` 대비 AUPRC `>= +0.03` 또는 Brier `<= -0.02`를 보여야
  하며, AUROC drop은 `0.02` 이하여야 한다. 이 조건은 same-family,
  same-geometry-status, same-rank-band control 아래에서만 해석한다.
- controlled label target은 `ready_controlled_review_queue_no_labels`로 생성됐다.
  primary mined queue는 `proximity/close by`, `geometry_status=satisfied`,
  `semantic_rank>100`만 사용하며, rank band별 reliable seed `16`개와 dense seed
  `16`개씩 총 `96` rows다.
- existing strict seed `27` rows를 합친 combined review queue는 `123` rows이며,
  모든 rows는 contact sheet와 mesh link를 가진다. proposed stratum은 sampling prior일
  뿐 final label이 아니며, training 재개 전 human/independent label이 필요하다.
- controlled label readiness는 `not_ready_no_filled_labels`로 확인됐다. 현재
  `mined_controlled`는 completed `0/96`, usable binary `0`, `combined_review`는
  completed `0/123`, usable binary `0`이다.
- 따라서 current `P(R_e = 1 | S_e, G_e, C_e, U_e)` posterior fitting은 아직 재개하지
  않는다. 다음 gate는 controlled review sheet에 human/independent label을 채운 뒤
  readiness validator를 다시 통과하는 것이다.
- 사용자 지시에 따라 controlled sheets를 `(codex_ver)` bootstrap label로 먼저 채웠다.
  원본 blank sheet는 보존했고 `*_codex_ver.tsv`를 별도로 생성했다.
- Codex-filled target은 `mined_controlled` `96` rows (`positive=48`, `negative=48`),
  `combined_review` `123` rows (`positive=64`, `negative=59`)이다.
- Codex-filled readiness는 `ready_for_train_only_controlled_posterior_smoke`로
  통과했다. 단, `codex_ver`는 sampling prior bootstrap이므로 human/independent label
  requirement를 만족하지 않는다.
- controlled posterior smoke는 `ready_plumbing_only_controlled_codex_labels`로
  완료됐다. `mined_controlled_codex_ver`에서 factorized posterior는
  `semantic_plus_geometry` 대비 AUPRC `+0.0006`, Brier `-0.0012`로 거의 동률이다.
- `combined_controlled_codex_ver`에서는 AUPRC `+0.0337`, Brier `-0.0081`이지만,
  Codex label과 existing strict seed가 포함된 plumbing-only 결과이므로 posterior
  advantage claim에는 사용할 수 없다.
- 현재 해석은 명확하다: H002 posterior implementation은 real label을 받을 준비가
  됐지만, H002 hypothesis 자체는 `codex_ver` label로 검증되지 않았다.
- 사용자 지시에 따라 hypothesis-stage에서는 `(codex_ver)`를 real label로 취급하는
  working assumption을 추가했다. 이 가정 아래에서도 결론은 보수적이다:
  `combined_controlled_codex_ver`는 AUPRC `+0.0337`로 약한 positive signal을 보이지만,
  `mined_controlled_codex_ver`는 AUPRC `+0.0006`으로 factorized advantage를 지지하지
  않는다.
- 또한 `drop_direct_identity_rank`와 `safe_continuous` control에서 성능이 near-random으로
  붕괴하므로, 현재 signal이 `C_e/U_e`의 독립 기여인지 semantic/rank/target construction
  artifact인지 아직 분리되지 않았다.
- 따라서 real-label assumption 아래에서도 H002는 "weak conditional support" 단계이며,
  다음 hypothesis-stage 검증은 grouped CV, factor ablation, rank-band/target-variant
  stability, proxy-baseline audit, bootstrap CI, calibration check다.
- scan-grouped controlled smoke를 실행했다. `mined_controlled_codex_ver`에서는
  factorized posterior가 `semantic_plus_geometry` 대비 AUPRC `+0.0341`, Brier
  `-0.0234`로 numeric threshold를 만족했다. `combined_controlled_codex_ver`에서는
  AUPRC `+0.0268`, Brier `-0.0082`로 약하지만 threshold에는 조금 부족하다.
- factor ablation 결과 `S+G+C`는 `S+G`와 동일했고, gain은 `S+G+U`에서 발생했다.
  즉 현재 controlled target에서는 coverage factor보다 uncertainty/disagreement factor가
  signal을 만든다.
- 그러나 `negative_rank_only` proxy가 factorized posterior보다 강하다:
  mined AUPRC `0.9589` vs factorized `0.9409`, combined AUPRC `0.7094` vs
  factorized `0.6801`. 따라서 현재는 factorized reliability signal이 semantic rank
  artifact와 분리됐다고 말할 수 없다.
- 현재 결론: `codex_ver`를 real label로 취급해도 H002는 reliability framing에 대한
  conditional support는 있지만, factorized posterior method contribution은 아직
  rank-proxy debias를 통과해야 한다.
- rank-proxy debias check 결과는 `rank_proxy_not_debiased`다. Full factorized posterior는
  `negative_rank_only`보다 약했다: mined AUPRC `0.9409` vs `0.9589`, combined AUPRC
  `0.6801` vs `0.7094`.
- `negative_rank_plus_factorized_no_rank`도 `negative_rank_only`보다 나빴다:
  mined AUPRC `-0.0491`, Brier `+0.0286`, combined AUPRC `-0.0141`, Brier `+0.0164`.
- 즉 non-rank factorized evidence를 rank proxy에 더해도 추가 설명력이 생기지 않았다.
  현재 H002 posterior signal은 semantic rank / underconfidence proxy로 설명 가능하다.
- 따라서 다음 문제는 model capacity가 아니라 target construction이다. `proximity/close by`
  + `geometry_status=satisfied` 안에서도 positive/negative가 rank proxy로 분리된다면,
  factorized reliability method claim은 방어하기 어렵다.

핵심 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/source_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter_contract/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/runtime_stage/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/preflight/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_pilot.yaml
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/stream_manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.dedup.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/verification.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry/h002_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_rga_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_hl_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_lh_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/train_rga_audit_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/audit_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/hl_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/lh_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/working_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/needs_human_confirmation.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/manual_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/train_manual_audit_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/spotcheck_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/contact_sheets/
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/feature_blocks.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/baseline_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/deployable_features_all.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/target_joined.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/strict_smoke.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/weak_smoke.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/dataset_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/predictions_*.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/predictions_*.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_assignments.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/predictions_*.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/feasibility_check.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/primary_strict_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/support_contact_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/all_candidate_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/mined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/combined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/mined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/combined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/40_real_label_claim_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/41_grouped_control_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/42_rank_proxy_debias.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/within_rank_stability.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/matched_pairs.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/43_within_rank_stability.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/rank_matched_target.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pair_records.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/44_rank_matched_target.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/feature_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/metadata_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/45_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_protocol.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/internal_key.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/46_independent_label_protocol.md
```

## Next Gate

다음 gate:

```text
47_independent_label_ingestion.md
```

목표:

- completed blind sheet를 검증하고 `internal_key.jsonl`에 join하는 절차를 정의한다.
- hidden fields가 deployable feature로 새지 않도록 ingestion schema를 고정한다.
- independent binary/multiclass target을 materialize할 준비를 한다.
- residual/gated combiner diagnostic을 위한 target contract를 만든다.
- validation/test는 계속 사용하지 않는다.

Continue condition:

- completed blind labels가 schema-valid이고, rank/score/working-label leakage 없이
  binary target으로 변환 가능하면 residual/gated combiner diagnostic으로 진행한다.

Stop condition:

- completed labels가 없거나 blind protocol을 지키지 못하면 H002는 posterior method
  claim을 중단하고 RGA benchmark/failure-analysis claim으로 축소한다.
