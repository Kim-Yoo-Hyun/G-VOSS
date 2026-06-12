# H002 Summary Branch V2

Last updated: 2026-06-12

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
```

## Next Gate

다음 gate:

```text
26_factor_dataset.md
```

목표:

- train-only deployable feature rows를 `match_rows.jsonl`에서 materialize한다.
- `factor_targets.jsonl`를 217 audit rows에 join한다.
- strict/weak target subsets를 validation 없이 준비한다.
- `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
  `factorized_reliability_posterior` smoke-fitting inputs를 만든다.

Continue condition:

- train-set RGA diagnostic에서 exact-match LH 또는 audited no-GT LH의 의미 있는
  source-underconfidence / annotation-coverage / ontology-mismatch signal이 확인되면
  H002는 bidirectional RGA benchmark branch로 계속 진행한다.

Stop condition:

- `RGA-LH`가 대부분 geometry-trivial relation, source false positive, object-pair
  mismatch, geometry artifact라면 H002는 bidirectional benchmark가 아니라 H001 기반
  failure analysis 확장으로 축소한다.
