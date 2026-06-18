# H002 Summary Branch V2

Last updated: 2026-06-18

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

## Current Full-Train Expansion

H002는 pilot 결과만으로 posterior를 판단하지 않기 위해 Open3DSG train full로
확장했다. 이 확장은 validation/test를 열지 않고 train split 안에서만 수행했다.

완료된 full-train stages:

| Stage | Status |
| --- | --- |
| full train source contract | ready |
| full train raw dump | ready |
| full train adapter export | ready |
| full train geometry join | ready |
| full train RGA rows | ready |
| full train controlled candidate mining | ready for controlled audit |
| full train controlled label readiness | not ready: no filled labels |
| full train codex label fill | ready for train-only posterior smoke |
| full train posterior smoke | proxy blocked |

Full-train RGA rows:

```text
4,818,996 rows
```

Mismatch queues:

| Queue | Rows |
| --- | ---: |
| `RGA-HL` | 1,828 |
| `RGA-LH` | 455,598 |

Primary train-full RGA metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 3.02% | 4.96% |
| `RGA-valid@K` | 61.90% | 52.39% |
| `RGA-coverage@K` | 2.91% | 9.86% |
| `RGA-uncertain@K` | 35.08% | 42.65% |
| `RGA-LH-tail@K` | 42.61% | 42.37% |

Controlled candidate mining:

| Item | Count |
| --- | ---: |
| candidates | 360 |
| unique scans | 92 |
| `HL` candidates | 83 |
| `LH` candidates | 277 |
| `LH exact/family` candidates | 122 |
| `LH no-GT` candidates | 77 |

해석:

```text
Full train에서도 high-semantic/low-geometry mismatch는 존재하지만, 더 큰 진단
질량은 low-semantic/high-geometry 쪽이다. 따라서 H002의 중심은 overconfidence
detector가 아니라 bidirectional RGA benchmark와 controlled audit protocol이다.
```

아직 posterior method claim은 하지 않는다. `proposed_audit_role`은 label이 아니며,
실제 `P(R_e=1 | S_e, G_e, C_e, U_e)` 검증은 controlled label readiness 이후에만
진행한다.

현재 full-train label readiness 결과:

```text
candidate sheet rows = 360
started rows = 0
completed rows = 0
usable binary rows = 0
status = not_ready_no_filled_labels
```

따라서 다음 단계는 posterior fitting이 아니라 full-train controlled label fill 또는
independent blind confirmation이다.

Full-train `(codex_ver_full_train)` fill 결과:

```text
rows = 360
completed rows = 360
usable binary rows = 173
positive rows = 74
negative rows = 99
excluded rows = 187
readiness = ready_for_train_only_full_posterior_smoke
```

이 결과는 다음 train-only posterior smoke를 실행할 수 있게 하지만, human-confirmed
label이 아니므로 paper-level evidence나 posterior method claim으로 쓰지 않는다. 또한
binary target은 여전히 queue/rank/family/proposed-role shortcut risk가 있으므로 다음
단계에서 proxy controls가 필수다.

Full-train posterior smoke 결과:

```text
target rows = 173
positive = 74
negative = 99
scan-grouped CV = 3 folds
factorized AUPRC = 0.7665
semantic_plus_geometry AUPRC = 0.7547
delta AUPRC = +0.0117
delta Brier = -0.0019
status = full_train_posterior_proxy_blocked
```

Proxy controls:

```text
proposed_role_only AUPRC = 1.0000
label_status_only AUPRC = 0.9473
```

따라서 full-train 규모에서도 현재 bootstrap target은 posterior method claim이 아니라
target-policy/label-policy entanglement를 보여준다. H002의 안정적인 중심은 계속 RGA
benchmark, bidirectional mismatch taxonomy, controlled audit protocol이다.

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
- rank-hidden independent label protocol은 `independent_label_protocol_ready`로
  생성됐다. 대상은 `support_contact=26`, `proximity=27`, `relative_vertical=34`,
  총 `87` rows이며, semantic rank/score, `p_geom_valid`, working label, queue,
  proposed stratum은 annotator에게 숨긴다.
- independent label ingestion tool은 `independent_label_ingestion_waiting_for_completed_labels`
  상태로 실행됐다. blind sheet `87` rows와 internal key `87` rows의 구조는 맞고,
  forbidden header leakage error는 없지만, 현재 completed label rows와 binary target
  rows는 모두 `0`이다.
- 따라서 다음 H002 gate는 residual/gated combiner가 아니라 rank-hidden blind label
  fill이다. completed labels가 ingest되어 binary target이 생기기 전까지 posterior method
  claim은 계속 blocked다.
- blind label fill 과정에서 기존 contact sheet 이미지가 hidden relation metadata를
  이미지 내부에 노출한다는 문제가 발견됐다. 따라서 original contact sheet를 그대로
  쓰지 않고 sanitized crop/contact-sheet asset을 새로 만들었다.
- `(codex_ver_blind)` visible-metadata bootstrap label을 sanitized blind sheet에 채웠고,
  `87` completed rows 중 binary-usable target `75` rows를 만들었다. Positive는 `46`,
  negative는 `29`, excluded는 `12` rows다.
- completed sheet를 independent ingestion에 다시 넣은 결과
  `independent_label_targets_ready`가 됐다: completed `87`, binary `75`,
  multiclass `87`, errors `0`, validation/test usage `False`.
- 단, 이 label은 human-confirmed가 아니므로 paper-level annotation evidence는 아니다.
  현재 의미는 train-only residual/gated combiner diagnostic을 재개할 수 있다는 것이다.
- independent combiner smoke는 `independent_combiner_no_strong_signal`로 완료됐다.
  Grouped-by-scan 기준 `factorized_reliability_posterior`는
  `semantic_plus_geometry` 대비 AUPRC `-0.0013`, Brier `+0.0016`으로 동률보다
  약간 나쁘다. `residual_reliability_model`은 AUPRC `-0.1010`,
  `gated_evidence_model`은 AUPRC `-0.0969`로 더 나쁘다.
- `factorized_reliability_posterior`는 `negative_rank_only`보다 AUPRC `+0.1412`,
  Brier `-0.0289`로 좋다. 따라서 이번 blocker는 단순 rank proxy가 아니라
  `semantic_plus_geometry`와 family/predicate label-policy entanglement다.
- Proxy controls에서 grouped `predicate_only` AUPRC `0.8650`, `family_only` AUPRC
  `0.8330`이 높다. 이는 `(codex_ver_blind)` bootstrap target이 family/predicate
  policy로 많이 설명됨을 의미한다.
- Family slice에서는 `proximity`에서만 gated/residual이 `semantic_plus_geometry`보다
  좋아 보인다. 그러나 `relative_vertical`과 `support_contact`에서는 support가 없고,
  `support_contact`는 positive `23` / negative `2`로 매우 불균형하다.
- 결론: H002 posterior method claim은 계속 blocked다. 다음 blocker는 model capacity가
  아니라 label policy / family-predicate bias audit이다.
- label policy audit은 `label_policy_entangled`로 완료됐다. Predicate/family majority
  rule만으로 target label의 `70.67%`를 설명할 수 있고, normalized mutual information은
  `predicate_label=0.2505`, `predicate_family=0.1931`, `rank_band=0.0980`이다.
- `standing on`은 `15/15` positive, `lower than`은 `2/2` negative,
  `support_contact`는 `23/25` positive라 현재 bootstrap target은 predicate/family
  policy로 강하게 설명된다.
- family-balanced와 predicate-balanced target variant를 만들었다. 둘 다 `44` rows,
  positive `22`, negative `22`다. `proximity_only` variant는 `27` rows,
  positive `15`, negative `12`다.
- policy-balanced grouped smoke에서도 posterior signal은 살아나지 않았다.
  `predicate_balanced`에서 `factorized - semantic_plus_geometry` AUPRC는 `+0.0013`,
  `gated - semantic_plus_geometry` AUPRC는 `-0.0016`이다.
  `proximity_only`에서는 `gated - semantic_plus_geometry` AUPRC가 `-0.0071`이다.
- 따라서 현재 H002 evidence는 "semantic score, geometry validity, relation reliability
  를 분리해야 한다"는 problem framing은 지지하지만,
  `P(R_e=1 | S_e,G_e,C_e,U_e)` posterior가 method contribution으로 충분하다는 증거는
  아직 없다.
- posterior 결합 방식 자체에는 개선 여지가 있다. 특히 semantic-prior residual,
  family-specific hierarchical posterior, coverage-gated geometry model,
  pairwise rank-matched ranking, debiased/orthogonalized factor posterior,
  selective/abstention-aware posterior, monotonic calibrated posterior는 현재 global
  logistic combiner보다 원리적으로 더 적합할 수 있다.
- 하지만 현재 가장 큰 blocker는 combiner architecture가 아니라 label-policy bias다.
  결합 방식을 강하게 만들면 `(codex_ver_blind)`의 predicate/family shortcut을 더 잘
  학습할 위험이 크다.
- 따라서 posterior path decision은 `posterior_path_deferred`로 고정했다. Posterior는
  버리지 않고 conditional future method candidate로 유지하지만, near-term H002 main
  contribution은 RGA benchmark / diagnostic framework / failure taxonomy로 둔다.
- 이 결정은 `feasibility_check.md`의 방법을 폐기한다는 뜻이 아니다. 해당 문서는
  H002의 staged method map으로 유지한다. 지금 즉시 쓰는 부분은 multi-view/mesh/contact
  sheet를 audit/confirmation evidence로 사용하는 것, `true_underconfidence`와
  `dense_relation_noise`를 구분하는 label protocol, 그리고 relation-family 확장 순서
  `support_contact -> attachment_deferred -> relative_vertical`이다.
- 반대로 아직 쓰지 않는 부분은 `V_mv_e`를 deployable model input으로 넣는 것이다.
  `P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)`는 현재
  `S_e + G_e + C_e + U_e` independent-target gate가 통과된 뒤의 확장으로 남긴다.
- Posterior 결합 방식 개선도 `feasibility_check.md`의 후보를 따른다. Residual,
  gated, pairwise rank-matched, debiased/orthogonalized, product-of-experts,
  family-specific mixture/hierarchical, monotonic calibrated posterior는 모두
  future revival path로 유지하되, 현재 main claim 근거로 쓰지 않는다.
- posterior claim을 revive하려면 human-confirmed 또는 independent labels가 필요하다:
  binary usable rows `>=150`, positive/negative 각각 `>=50`, at least 2 families with
  both classes, per-family minority `>=15`, predicate/family/rank proxy controls pass,
  grouped CV에서 `semantic_plus_geometry` 대비 AUPRC `>= +0.03` 또는 Brier `<= -0.02`.
- H002 main framing은 `full_train_expansion_before_validation`으로 업데이트했다.
  현재 pilot train 결과는 H002 posterior를 최종 반박하지 않는다. 정확한 의미는
  "현재 Open3DSG train pilot + codex/bootstrap label + 75 binary target에서는 posterior
  method claim을 방어할 만큼 강한 증거가 없다"이다.
- 따라서 다음 방향은 validation을 열지 않고 전체 train으로 확장하는 것이다. Full train
  확장의 목적은 더 큰 relation distribution에서 RGA-HL/RGA-LH, coverage, uncertainty,
  label-axis 분포를 측정하고, family/predicate/rank shortcut을 통제한 controlled label
  target을 더 크게 mine하는 것이다.
- Validation/test는 target definition, feature schema, family set, metric, baseline,
  posterior combiner가 freeze된 뒤에만 사용한다. 지금 validation을 보면 held-out
  evaluation이 아니라 development feedback이 되어 H002 claim을 약화시킨다.
- `52_rga_main_framing.md`는 H002 near-term contribution을 RGA benchmark / diagnostic
  framework / failure taxonomy로 고정하고, posterior는 full-train controlled-label gate
  이후 revive할 conditional method candidate로 둔다.
- Full-train scope contract는 `full_train_scope_contract_ready_no_execution`으로
  작성됐다. Scope name은 `open3dsg_train_full`이고, artifact root는
  `artifacts/train_rga_full/open3dsg_train_full/`이다.
- Full train은 pilot처럼 한 scan당 대표 subgraph를 고르는 것이 아니라, train-origin
  Open3DSG-ready 전체 context를 대상으로 한다. 기존 pilot manifest 기준 planning count는
  official train subset `3,852` contexts, ready candidate `3,738` contexts,
  preprocess-not-ready drop `108`, no-relationship drop `6`이다. 실제 full-train
  source contract 실행 시 이 수치는 다시 계산하고 input hash와 함께 고정해야 한다.
- 기존 `train_source_contract.py`는 full train에 그대로 쓰면 안 된다. 현재 selection rule이
  one-subgraph-per-scan pilot selection이기 때문이다. 다음 gate는 all-ready-train-context
  selection mode를 가진 full-train source runner를 만들거나 parameterize하는 것이다.
- `stage_train_raw_dump_runtime.py`, Open3DSG adapter export, raw repair,
  provenance fix, H001 geometry joiner, `train_rga_rows.py`는 개념적으로 재사용 가능하지만,
  full-train path, scope id, provenance wording, source-contract count field를
  parameterize해야 한다.
- Full-train source runner `tools/full_train_source_contract.py`를 추가하고 실행했다.
  Source contract status는 `full_train_source_contract_ready`다.
- Full-train source contract는 `selection_mode=all_ready_train_contexts`로
  `3,738` contexts, `1,157` scans, `79,704` GT relations를 선택했다. Drop reason은
  preprocess-not-ready `108`, no-relationship `6`, view-not-ready `0`,
  missing-subset-entry `0`이다.
- Primary family coverage는 `support_contact=12,600`, `proximity=12,300`,
  `relative_vertical=3,552` GT relations다. 전체 selected family count는
  `relative_horizontal=36,944`, `attachment_deferred=8,767`,
  `unsupported_first_pass=5,541`도 함께 보존한다.
- Generated source-contract artifact에는 `full_validation`, `relationships_validation`,
  `relationships_test` path string이 없다. Runtime 단계에서는 Open3DSG upstream
  `--test` 제약 때문에 isolated H002 runtime 안에서만 train subset을 validation filename으로
  stage할 수 있다.
- Full-train runtime stage는 `full_train_runtime_preflight_ready`로 완료됐다. 기존
  `stage_train_raw_dump_runtime.py`를 parameterize했고,
  `compose.open3dsg_train_full.yaml`을 추가했다.
- Runtime root는 `local_dataset/Open3DSG_staged/h002_train_full_runtime`이다. Runtime
  staging 결과는 contexts `3,738`, selected scans `1,157`, linked scans `1,157`,
  sequence-ready scans `1,157`, feature missing contexts `0`, blockers `0`이다.
- Docker preflight도 ready다. Gates는 checkpoint/runtime/scope/imports 모두 true이고,
  scope는 selected scans `1,157`, contexts `3,738`이다. CUDA는 available true,
  device count `1`, torch `2.8.0+cu128`로 확인됐다.
- Full-train raw dump는 `full_train_raw_dump_complete`로 확인됐다. Session은
  `h002_open3dsg_train_full_raw_20260615_180429`, log는
  `logs/h002_open3dsg_train_full_raw_20260615_180429.log`, exit file은
  `logs/h002_open3dsg_train_full_raw_20260615_180429.exit`이고 exit code는 `0`이다.
- Stream manifest status는 `raw_dump_stream_complete`, completed batches는 `3,738`,
  raw rows는 `186,218`, completed rows는 `3,738`이다. NCCL teardown warning은 있었지만
  manifest completeness와 exit code 기준 completion blocker는 아니다.
- Raw repair/dedup도 완료됐다. `raw.dedup.jsonl`은 `186,139` rows이며, duplicate
  groups `79`, duplicate extra rows `79`, malformed identity rows `0`,
  noncontiguous subgraph repeats `0`, repair status `ready`다.
- Full-train adapter export는 `full_train_adapter_export_ready`로 완료됐다. 기존 pilot
  exporter는 full-train에서 모든 prediction row를 메모리에 올리는 위험이 있어,
  H002 전용 streaming exporter `tools/export_full_train_adapter.py`를 추가했다.
- Adapter export 결과는 contexts `3,738`, raw rows read `186,139`, prediction rows
  `4,818,996`, subgraphs written `3,738`, errors `0`, warnings `793`이다. Warning은
  outside-context filtered `786`, same-endpoint skipped `7`이며 adapter-contract
  filter로 기록한다.
- Prediction provenance는
  `artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json`
  을 가리킨다. `predictions.jsonl` 내부에서 `relationships_validation` 또는
  `h001_validation` provenance string은 검출되지 않았다.
- Full-train adapter family row count는 `support_contact=556,038`,
  `proximity=185,346`, `relative_vertical=370,692`,
  `relative_horizontal=741,384`, `attachment_deferred=556,038`,
  `unsupported_first_pass=2,409,498`이다.
- Full-train geometry join은 `full_train_geometry_join_ready_with_exit_file_caveat`로
  완료됐다. Session은 `h002_open3dsg_train_full_geometry_20260616_120342`, log는
  `logs/h002_open3dsg_train_full_geometry_20260616_120342.log`이다. 계획한 exit file은
  생성되지 않았지만 tmux session과 join process는 종료됐고, manifest/status/row count
  기준 artifact는 ready다.
- Geometry join 입력은 `4,818,996` prediction rows와 `1,157` selected train scans이다.
  출력 `verification.jsonl`도 `4,818,996` rows이며 rows_preserved `true`, errors `0`,
  warnings `9`다.
- Full-train geometry status는 `satisfied=474,898`, `uncertain=490,410`,
  `violated=146,768`, `unsupported=3,706,920`이다. Primary geometry-checkable rows와
  `p_geom_valid` scored rows는 각각 `1,112,076`이다.
- Full-train RGA row construction은 `full_train_rga_rows_ready_with_exit_file_caveat`로
  완료됐다. Session은 `h002_open3dsg_train_full_rga_20260616_161755`, log는
  `logs/h002_open3dsg_train_full_rga_20260616_161755.log`이다. 계획한 exit file은
  생성되지 않았지만 tmux session과 process는 종료됐고, summary/log/row count 기준
  artifact는 ready다.
- `train_rga_rows.py`는 full-train artifact provenance를 위해 `--label-source`,
  `--source-caveat`, `--split-boundary` arguments를 추가했다. 기존 pilot default는
  유지한다.
- Full-train RGA output은 `match_rows.jsonl=4,818,996` rows,
  `train_hl_queue.jsonl=1,828` rows, `train_lh_queue.jsonl=455,598` rows다.
  Summary status는 `ready`, validation error count는 `0`, prediction-geometry
  mismatches는 `0`이다.
- Top100 기준 full-train RGA bucket은 `RGA-HH=19,300`, `RGA-HL=1,828`,
  `RGA-HU=15,714`, `RGA-HM=336,910`, `RGA-LH=455,598`, `RGA-LL=144,940`,
  `RGA-LU=474,696`, `RGA-LM=3,370,010`이다.
- Full-train RGA metrics는 K=100 기준 `RGA-HL@100=4.96%`,
  `RGA-valid@100=52.39%`, `RGA-coverage@100=9.86%`,
  `RGA-LH-tail@100=42.37%`다. Pilot과 마찬가지로 HL보다 LH diagnostic mass가 훨씬
  크므로 H002는 overconfidence-only가 아니라 bidirectional RGA로 유지한다.
- 아직 완료되지 않은 것은 controlled-label mining, posterior revival smoke다.
  Validation/test는 계속 사용하지 않는다.

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
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/ingestion_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/47_independent_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_independent_blind_codex_labels.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/48_blind_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_combiner_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/family_slices.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/pairwise.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/matched_pairs.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/49_independent_combiner_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/label_policy_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/group_policy_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/family_balanced_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/predicate_balanced_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/proximity_only_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/50_label_policy_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/51_posterior_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/52_rga_main_framing.md
hypothesis/CAND-001/H002_factorized-relation-confidence/53_full_train_scope_contract.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_source_contract.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/source_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/train_contexts.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/54_full_train_source_runner.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/stage_train_raw_dump_runtime.py
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/runtime_stage/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/preflight/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/55_full_train_runtime_stage.md
hypothesis/CAND-001/H002_factorized-relation-confidence/56_full_train_raw_dump.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/export_full_train_adapter.py
hypothesis/CAND-001/H002_factorized-relation-confidence/57_full_train_adapter_export.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/stream_manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/repair_manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/58_full_train_geometry_join.md
hypothesis/CAND-001/H002_factorized-relation-confidence/59_full_train_rga_rows.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/train_rga_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/train_hl_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/train_lh_queue.jsonl
logs/h002_open3dsg_train_full_geometry_20260616_120342.log
logs/h002_open3dsg_train_full_rga_20260616_161755.log
logs/h002_open3dsg_train_full_raw_20260615_180429.log
logs/h002_open3dsg_train_full_raw_20260615_180429.exit
```

## Next Gate

다음 gate:

```text
full_train_independent_support_vertical_label_ingestion
```

목표:

- completed label sheet와 `internal_reference_post_label_only.jsonl`을 label-lock 이후 join한다.
- filled labels를 validated labels, binary targets, multiclass labels로 export한다.
- bootstrap label과 hidden audit metadata 사이의 shortcut risk를 다시 검사한다.
- labeler surface에서 `proposed_audit_role`, `label_match_status`, `queue_kind`,
  `geometry_status`, rank band 같은 target-construction metadata를 계속 숨긴다.
- multi-view는 아직 model input이 아니라 audit evidence로만 둔다.
- validation/test는 계속 사용하지 않는다.

Continue condition:

- ingestion이 completion schema의 allowed values를 만족한다.
- binary usable target이 support/vertical posterior smoke에 충분하다.
- hidden metadata correlation risk를 다시 정량화한다.
- positive-looking slice result를 paper-level posterior claim으로 승격하지 않는다.

Stop condition:

- upgraded combiner가 hidden audit metadata나 label-construction metadata를 input으로
  요구하면 진행하지 않는다.
- validation/test provenance가 섞이면 H002 hypothesis-stage evidence로도 사용하지 않는다.
- 단순히 더 큰 classifier로 성능만 올리는 방향이면 method claim으로 사용하지 않는다.
- Codex bootstrap target에서만 좋은 결과가 나오면 paper-level posterior claim으로
  승격하지 않는다.

## Full-Train Label Policy Audit Update

2026-06-16에 full-train posterior smoke 이후 label-policy audit을 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
```

결과:

```text
status = full_train_label_policy_entangled
rows = 173
positive = 74
negative = 99
validation_used = False
proposed_audit_role majority accuracy / NMI = 1.0000 / 1.0000
label_match_status majority accuracy / NMI = 0.9942 / 0.9550
```

해석:

- `proposed_audit_role`은 현재 binary target을 완전히 복원한다.
- `label_match_status`도 현재 target을 거의 완전히 복원한다.
- `queue_kind`, `geometry_status`, `rank_band`도 majority accuracy 약 `0.9075`로
  강한 shortcut이다.
- `predicate_family` 자체는 강한 target constructor가 아니지만, `predicate_label`은
  중간 수준의 policy signal을 갖는다.

Original full-train grouped metrics:

| View | AUROC | AUPRC | Brier |
| --- | ---: | ---: | ---: |
| `semantic_plus_geometry` | 0.9044 | 0.7547 | 0.1188 |
| `factorized_reliability_posterior` | 0.9085 | 0.7665 | 0.1170 |
| `label_status_only` | 0.9916 | 0.9473 | 0.0087 |
| `proposed_role_only` | 1.0000 | 1.0000 | 0.0035 |

결론:

```text
Full-train expansion supports RGA/failure-taxonomy framing, but the current
codex_ver_full_train target does not validate the factorized posterior method.
```

따라서 H002의 현재 main direction은 다음과 같이 고정한다.

```text
RGA benchmark / diagnostic framework first,
factorized posterior only after independent label target.
```

추가된 문서와 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/64_full_train_label_policy_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/report.md
```

## Full-Train Independent Label Protocol Update

2026-06-16에 label-policy entanglement를 피하기 위한 full-train blind protocol을
추가했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
```

결과:

```text
status = full_train_independent_label_protocol_ready_needs_asset_packets
rows = 360
families = support_contact:201, relative_vertical:114, proximity:45
priority_sheet = 180 rows
leakage = pass
validation_used = False
```

Blind sheet에서 숨긴 정보:

- `proposed_audit_role`
- `label_match_status`
- `queue_kind`
- `geometry_status`
- semantic rank / rank band
- semantic score
- `p_geom_valid`
- matched GT fields
- bucket/reason/machine hint fields

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/65_full_train_independent_label_protocol.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_protocol.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_all_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/blind_priority_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/internal_key.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_protocol/asset_request_manifest.jsonl
```

해석:

```text
Protocol-level target leakage is addressed, but independent labels are not yet
available because evidence packets are still missing.
```

따라서 다음 단계는 label fill이나 posterior smoke가 아니라:

```text
full_train_independent_asset_packets
```

## Full-Train Independent Asset Packet Update

2026-06-16에 blind row별 evidence packet을 생성했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
```

결과:

```text
status = full_train_independent_asset_packets_partial
rows = 360
ready = 347
partial = 13
leakage = pass
validation_used = False
```

Coverage:

| Item | Count |
| --- | ---: |
| subject images linked | 353 / 360 |
| object images linked | 352 / 360 |
| contact/context sheets ready | 358 / 360 |
| mesh packets ready | 360 / 360 |

Family status:

| Family | Ready | Partial |
| --- | ---: | ---: |
| `support_contact` | 196 | 5 |
| `relative_vertical` | 106 | 8 |
| `proximity` | 45 | 0 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/66_full_train_independent_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/blind_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_asset_packets/packets/
```

해석:

```text
Packet generation is mostly ready, but label fill must wait until the 13 partial
rows are audited.
```

이 audit 이후 진행할 단계는 controlled posterior smoke였고, 아래 update에서
완료했다:

```text
full_train_asset_packet_gap_audit
```

## Full-Train Asset Packet Gap Audit Update

2026-06-16에 partial packet 13개를 감사해 label-ready row와 제외 row를 분리했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
```

결과:

```text
status = full_train_asset_packet_gap_audit_ready_for_label_readiness
rows = 360
label_ready = 355
excluded = 5
partial = 13
validation_used = False
```

Decision counts:

| Decision | Rows |
| --- | ---: |
| `label_ready` | 347 |
| `label_ready_with_packet_caveat` | 8 |
| `exclude_before_label_fill` | 5 |

Family decision counts:

| Family | Ready | Ready With Caveat | Excluded |
| --- | ---: | ---: | ---: |
| `support_contact` | 196 | 3 | 2 |
| `relative_vertical` | 106 | 5 | 3 |
| `proximity` | 45 | 0 | 0 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/67_full_train_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/label_ready_all_sheet_with_packets.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/asset_packet_gap_audit/excluded_blind_ids.txt
```

해석:

```text
Asset packet gap is no longer the blocker. H002 can move to independent label
readiness, but not to label fill or posterior smoke yet.
```

이 gap audit 이후 진행할 단계는 다음 readiness update에서 완료했다:

```text
full_train_independent_label_readiness
```

## Full-Train Independent Label Readiness Update

2026-06-17에 label-ready sheet가 독립 라벨링에 들어갈 수 있는지 검증했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
```

결과:

```text
status = full_train_independent_label_readiness_ready_for_label_fill
rows = 355
excluded = 5
errors = 0
leakage = 0
validation_used = False
```

Coverage:

| Sheet | Rows | Scans | Minimum | Status |
| --- | ---: | ---: | ---: | --- |
| `all` | 355 | 92 | 300 | `pass` |
| `priority` | 179 | 66 | 150 | `pass` |
| `support_contact` | 199 | 70 | 150 | `pass` |
| `relative_vertical` | 111 | 43 | 80 | `pass` |
| `proximity` | 45 | 15 | 30 | `pass` |

All-sheet predicate coverage:

| Predicate | Rows |
| --- | ---: |
| `lying on` | 81 |
| `lower than` | 66 |
| `supported by` | 62 |
| `standing on` | 56 |
| `higher than` | 45 |
| `close by` | 45 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/68_full_train_independent_label_readiness.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ready_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_readiness/label_ingestion_schema.json
```

해석:

```text
Label surface construction is no longer the blocker. The next blocker is actual
independent label fill and post-label ingestion.
```

이 readiness update 이후 진행할 단계는 label fill이었고, 아래
`Full-Train Independent Label Fill Update`에서 완료했다:

```text
full_train_independent_label_fill
```

## Full-Train Independent Label Fill Update

2026-06-17에 rank/role-hidden label-ready sheet에
`(codex_ver_full_train_independent)` bootstrap label을 채웠다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
```

결과:

```text
status = full_train_independent_codex_labels_filled_not_human_confirmed
rows = 355
binary = 283
positive = 155
negative = 128
excluded = 72
validation_used = False
```

Label counts:

| Label | Rows |
| --- | ---: |
| `reliable_informative` | 128 |
| `annotation_sparsity_candidate` | 27 |
| `valid_but_trivial_dense` | 92 |
| `invalid_relation` | 24 |
| `invalid_pair` | 12 |
| `ontology_mismatch` | 8 |
| `abstain_uncertain` | 64 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/69_full_train_independent_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/completed_all_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_fill_codex_ver/binary_targets_preview.jsonl
```

해석:

```text
The new codex-version label target is now filled without reading hidden
construction metadata, but it is still not human-confirmed. The next blocker is
post-label ingestion and target-independence audit.
```

이 label fill update 이후 진행할 단계는 ingestion이었고, 아래
`Full-Train Independent Label Ingestion Update`에서 완료했다:

```text
full_train_independent_label_ingestion
```

## Full-Train Independent Label Ingestion Update

2026-06-17에 completed label을 label lock 이후 `internal_key.jsonl`과 join해
binary/multiclass/posterior diagnostic target을 materialize했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
```

결과:

```text
status = full_train_independent_label_ingested_with_target_policy_risk
labels = 355
binary = 283
positive = 155
negative = 128
errors = 0
probe = target_independence_risk_hidden_metadata_correlated
validation_used = False
```

Target probe:

| Source | Group Key | Majority Acc | NMI |
| --- | --- | ---: | ---: |
| `hidden_post_label_audit` | `proposed_audit_role_hidden` | 0.7208 | 0.2897 |
| `hidden_post_label_audit` | `label_match_status_hidden` | 0.6678 | 0.1584 |
| `visible_label_surface` | `predicate_label` | 0.6961 | 0.1318 |
| `visible_label_surface` | `predicate_family` | 0.6961 | 0.1222 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/70_full_train_independent_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_label_ingestion_codex_ver/target_independence_probe.json
```

해석:

```text
Ingestion itself is clean, but the new target still has hidden metadata
correlation risk. The next step is not posterior smoke; it is a dedicated
target-independence audit.
```

이 ingestion update 이후 진행할 단계는 target-independence audit이었고, 아래
`Full-Train Independent Target Independence Audit Update`에서 완료했다:

```text
full_train_independent_target_independence_audit
```

## Full-Train Independent Target Independence Audit Update

2026-06-17에 ingested target의 hidden metadata shortcut risk를 정량화하고,
controlled slice를 구성했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
```

결과:

```text
status = full_train_independent_target_independence_audit_controlled_slice_ready
recommended = proposed_role_balanced_codex_ver
rows = 158
positive = 79
negative = 79
validation_used = False
```

Original target risk:

| Hidden Key | Majority Acc | NMI |
| --- | ---: | ---: |
| `proposed_audit_role_hidden` | 0.7208 | 0.2897 |

Recommended controlled slice:

| Slice | Rows | Positive | Negative | Hidden Risks |
| --- | ---: | ---: | ---: | ---: |
| `proposed_role_balanced_codex_ver` | 158 | 79 | 79 | 0 |

Other usable controlled slices:

| Slice | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `label_status_balanced_codex_ver` | 188 | 94 | 94 |
| `family_balanced_codex_ver` | 172 | 86 | 86 |
| `predicate_balanced_codex_ver` | 172 | 86 | 86 |
| `queue_family_balanced_codex_ver` | 162 | 81 | 81 |
| `rank_family_balanced_codex_ver` | 152 | 76 | 76 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/71_full_train_independent_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_target_independence_audit_codex_ver/target_slices/proposed_role_balanced_codex_ver.jsonl
```

해석:

```text
The original ingested target is still shortcut-risky. Posterior smoke can resume
only as train-only diagnostics on the proposed-role-balanced controlled slice.
```

이 target-independence audit 이후 진행할 단계는 controlled posterior smoke였고,
아래 update에서 완료했다:

```text
full_train_independent_controlled_posterior_smoke
```

## Full-Train Independent Controlled Posterior Smoke Update

2026-06-17에 `proposed_role_balanced_codex_ver` controlled slice에서 train-only
posterior smoke를 실행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
```

결과:

```text
status = full_train_independent_controlled_posterior_no_strong_signal
rows = 158
positive = 79
negative = 79
validation_used = False
d_auprc_factorized_vs_semantic_plus_geometry = -0.0047
d_auprc_factorized_vs_semantic_only = -0.0039
d_auprc_factorized_vs_geometry_only = +0.1155
```

Scan-grouped main metrics:

| View | AUROC | AUPRC | Brier | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.6623 | 0.6291 | 0.2360 | 0.6076 |
| `geometry_only` | 0.4575 | 0.5098 | 0.2559 | 0.4810 |
| `semantic_plus_geometry` | 0.6640 | 0.6300 | 0.2341 | 0.6392 |
| `factorized_reliability_posterior` | 0.6531 | 0.6253 | 0.2363 | 0.5823 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/72_full_train_independent_controlled_posterior_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_posterior_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/comparisons.csv
```

해석:

```text
The controlled smoke is executable, but the current factorized combination does
not beat semantic_plus_geometry. H002 should move to controlled error/feature
analysis before changing claims or adding modalities.
```

이 smoke 이후 진행할 단계는 controlled error analysis였고, 아래 update에서
완료했다:

```text
full_train_independent_controlled_error_analysis
```

## Full-Train Independent Controlled Error Analysis Update

2026-06-17에 controlled posterior smoke output을 대상으로 train-only error
analysis를 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_error_analysis.py
```

결과:

```text
status = full_train_independent_controlled_error_analysis_ready_for_combiner_design
rows = 158
validation_used = False
factorized_wrong_sg_correct = 10
factorized_correct_sg_wrong = 1
mean_brier_delta_factorized_minus_sg = +0.0021
next = full_train_independent_combiner_upgrade_design
```

핵심 해석:

- 현재 factorized posterior는 `semantic_plus_geometry`가 맞춘 threshold decision을
  더 많이 망가뜨린다.
- `semantic_high_geometry_low` 구간에서 factorized가 특히 손해를 본다
  (`Delta AUPRC F-SG=-0.0670`, `Mean Brier Delta=+0.0235`).
- `semantic_geometry_close` 구간에서는 factorized가 도움이 된다
  (`Delta AUPRC F-SG=+0.0344`, `Mean Brier Delta=-0.0014`).
- family별 양상이 다르다. `support_contact`는 ranking 이득과 calibration 손해가
  동시에 있고, `proximity`는 ranking 손해와 Brier 이득이 동시에 있다.

결론:

```text
Current one-size factorized posterior is not the right final combiner. The next
step should design a SOTA-style but hypothesis-stage-safe combiner: family-gated
calibrated fusion, residual correction over semantic_plus_geometry, and
uncertainty-gated geometry use.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/73_full_train_independent_controlled_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/slice_errors.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/feature_summary.csv
```

이 error analysis 이후 진행할 단계는 combiner upgrade design이었고, 아래
update에서 완료했다:

```text
full_train_independent_combiner_upgrade_design
```

## Full-Train Independent Combiner Upgrade Design Update

2026-06-18에 controlled error analysis를 근거로 upgraded combiner 설계를
고정했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_design.py
```

결과:

```text
status = full_train_independent_combiner_upgrade_design_ready_for_smoke
candidates = 5
validation_used = False
trains_new_model = False
next = full_train_independent_combiner_upgrade_smoke
```

결정:

```text
Generic high-capacity combiner is deferred. The next smoke should evaluate
failure-analysis-driven SOTA-style combiners: residual logit calibration,
family-gated residual fusion, and uncertainty-gated geometry use.
```

다음 smoke의 upgraded candidates:

| Candidate | Role | Reason |
| --- | --- | --- |
| `C1_residual_logit_calibrator` | primary | `semantic_plus_geometry`를 대체하지 않고 보정한다 |
| `C2_family_gated_residual` | primary if regularized | family별 geometry behavior 차이를 반영한다 |
| `C3_uncertainty_gated_geometry` | secondary | geometry를 항상 쓰지 않고 uncertainty/gate로 조절한다 |

보류한 후보:

- `C4_monotonic_gbdt_calibrator`: 158-row bootstrap target에서는 overfit 위험이 크다.
- `C5_graph_factor_rescoring`: edge-local combiner가 먼저 검증되어야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/74_full_train_independent_combiner_upgrade_design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_design.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/candidate_matrix.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_design_codex_ver/smoke_plan.json
```

이 design 이후 진행할 단계는 combiner upgrade smoke였고, 아래 update에서
완료했다:

```text
full_train_independent_combiner_upgrade_smoke
```

## Full-Train Independent Combiner Upgrade Smoke Update

2026-06-18에 combiner upgrade design에서 고정한 3개 후보를 train-only controlled
slice에서 smoke했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_smoke.py
```

결과:

```text
status = full_train_independent_combiner_upgrade_no_safe_gain
rows = 158
validation_used = False
best_upgraded = C2_family_gated_residual
d_auprc_vs_semantic_plus_geometry = +0.0070
d_brier_vs_semantic_plus_geometry = +0.0062
progress_views = none
next = full_train_independent_combiner_upgrade_error_analysis
```

Grouped main metrics:

| View | Kind | AUROC | AUPRC | Brier | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `semantic_plus_geometry` | baseline | 0.6640 | 0.6300 | 0.2341 | 0.6392 |
| `current_factorized_reliability_posterior` | baseline | 0.6531 | 0.6253 | 0.2363 | 0.5823 |
| `C1_residual_logit_calibrator` | upgraded | 0.6581 | 0.6271 | 0.2356 | 0.6139 |
| `C2_family_gated_residual` | upgraded | 0.6520 | 0.6370 | 0.2404 | 0.6139 |
| `C3_uncertainty_gated_geometry` | upgraded | 0.6704 | 0.6247 | 0.2329 | 0.6456 |

Threshold transfer vs `semantic_plus_geometry`:

| View | Fixes | New Mistakes | New-Fix |
| --- | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | 1 | 10 | +9 |
| `C1_residual_logit_calibrator` | 1 | 5 | +4 |
| `C2_family_gated_residual` | 4 | 8 | +4 |
| `C3_uncertainty_gated_geometry` | 4 | 3 | -1 |

해석:

- `C2`는 AUPRC를 올리지만 Brier와 threshold transfer가 나쁘다.
- `C3`는 AUROC, Brier, threshold transfer를 개선하지만 AUPRC가 낮아진다.
- pre-defined progression threshold를 만족한 upgraded combiner는 없다.
- 따라서 더 큰 generic combiner로 바로 넘어가지 않고, 먼저 upgraded combiner
  error analysis가 필요하다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/75_full_train_independent_combiner_upgrade_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/slice_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_smoke_codex_ver/threshold_transfer.csv
```

이 smoke 이후 진행할 단계는 combiner upgrade error analysis였고, 아래 update에서
완료했다:

```text
full_train_independent_combiner_upgrade_error_analysis
```

## Full-Train Independent Combiner Upgrade Error Analysis Update

2026-06-18에 combiner upgrade smoke 결과를 post-hoc 분석했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_error_analysis.py
```

결과:

```text
status = full_train_independent_combiner_upgrade_error_analysis_ready_for_decision
validation_used = False
hidden_used = False
c2_pos_rank_improved = 28
c3_new_fix = -1
next = full_train_independent_combiner_path_decision
```

핵심 진단:

```text
C2_ranking_gain_is_not_calibrated_safe
C3_threshold_transfer_is_safer_than_C2
C3_calibration_gain_trades_off_ranking
C2_family_gate_overcorrects_support_contact
C3_is_promising_for_relative_vertical_not_global
```

Rank/probability movement vs `semantic_plus_geometry`:

| View | Pos Rank Improved | Pos Rank Worsened | Neg Demoted | Neg Promoted | Mean Pos Prob Delta | Mean Neg Prob Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C2_family_gated_residual` | 28 | 48 | 43 | 30 | +0.0212 | +0.0024 |
| `C3_uncertainty_gated_geometry` | 42 | 31 | 37 | 29 | +0.0155 | -0.0047 |

해석:

- `C2`는 일부 ranking signal을 만들지만 positive/negative probability를 같이 올려
  calibration-safe하지 않다.
- `C2`는 `support_contact`와 `semantic_high_geometry_low`에서 과보정한다.
- `C3`는 threshold/Brier 측면에서 더 안전하고 `relative_vertical` 및
  `semantic_high_geometry_low`에서 유망하다.
- 하지만 `C3`는 `support_contact` ranking을 망가뜨려 global AUPRC가 낮다.

결론:

```text
Do not add a generic high-capacity combiner yet. Decide whether H002 should keep
this as a negative boundary or revise relation-family-specific factors before
another smoke.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/76_full_train_independent_combiner_upgrade_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/rank_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/slice_deltas.csv
```

이 분석은 다음 path decision으로 이어졌고, 해당 결정은 아래 update에서 완료했다:

```text
full_train_independent_combiner_path_decision
```

## Full-Train Independent Combiner Path Decision Update

2026-06-18에 combiner/posterior path decision을 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_path_decision.py
```

결과:

```text
status = full_train_independent_combiner_path_decision_factor_revision_first
selected_path = B_factor_revision_first
validation_used = False
posterior_claim_allowed = False
next = full_train_independent_factor_revision_design
```

결정:

```text
H002는 계속 진행한다. 다만 현재 posterior performance 결과는 negative/partial
boundary로 고정하고, generic high-capacity combiner를 바로 추가하지 않는다.
다음 단계는 relation-family-specific deployable factor revision이다.
```

왜 이 결정인가:

- `C2_family_gated_residual`은 AUPRC를 올리지만 calibration과 threshold decision을
  안전하게 개선하지 못했다.
- `C3_uncertainty_gated_geometry`는 threshold/Brier에는 유리하지만 support_contact
  ranking을 손상시켰다.
- 따라서 병목은 generic combiner capacity 부족이 아니라 factor/family-specific
  evidence 설계 문제에 가깝다.

Factor revision 우선순위:

1. `support_contact_factor_split`
2. `relative_vertical_order_residual`
3. `coverage_uncertainty_factor`
4. `family_shrinkage_gate`
5. `target_confirmation_gate`

Claim boundary:

```text
Allowed: RGA exposes semantic/geometric mismatch and current posterior combiners
have family-specific failure modes under a controlled train-only target.

Blocked: factorized reliability posterior improves relation reliability over
semantic_plus_geometry.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/77_full_train_independent_combiner_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/decision_options.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_path_decision_codex_ver/factor_revision_plan.csv
```

따라서 다음 단계는:

```text
full_train_independent_factor_revision_design
```

## Full-Train Independent Factor Revision Design Update

2026-06-18에 relation-family-specific factor revision design을 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_factor_revision_design.py
```

결과:

```text
status = full_train_independent_factor_revision_design_ready
factors = 5
families = 6
validation_used = False
posterior_claim_allowed = False
next = full_train_independent_revised_factor_dataset
```

핵심 결정:

```text
다음 smoke 전에 revised deployable factor block을 먼저 materialize한다.
p_geom_valid 하나로 접힌 geometry evidence를 raw witness 기반 factor로 펼치고,
support_contact와 relative_vertical을 별도 factor로 분리한다.
```

Full-train geometry availability:

| Family | Rows | Raw Feature Rows | Raw Coverage | Satisfied | Unsatisfied | Uncertain | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 556,038 | 556,038 | 1.0000 | 178,968 | 15,472 | 361,598 | 0 |
| `relative_vertical` | 370,692 | 370,692 | 1.0000 | 124,604 | 124,604 | 121,484 | 0 |
| `proximity` | 185,346 | 185,346 | 1.0000 | 171,326 | 6,692 | 7,328 | 0 |
| `attachment_deferred` | 556,038 | 0 | 0.0000 | 0 | 0 | 0 | 556,038 |
| `relative_horizontal` | 741,384 | 0 | 0.0000 | 0 | 0 | 0 | 741,384 |
| `unsupported_first_pass` | 2,409,498 | 0 | 0.0000 | 0 | 0 | 0 | 2,409,498 |

고정한 factor contract:

1. `FR1_support_contact_witness_split`
2. `FR2_relative_vertical_order_residual`
3. `FR3_coverage_uncertainty_gate`
4. `FR4_family_shrinkage_residual`
5. `FR5_target_confirmation_gate`

중요한 boundary:

- `geometry_status`의 satisfied/unsatisfied를 main score shortcut으로 쓰지 않는다.
- posterior가 배울 주 신호는 continuous raw geometry witness다.
- `attachment_deferred`, `relative_horizontal`, `unsupported_first_pass`는 현재 unsupported라
  다음 smoke input 확장에서 제외한다.
- multi-view는 계속 audit evidence로만 둔다.
- generic high-capacity combiner는 아직 보류한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/78_full_train_independent_factor_revision_design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_factor_revision_design.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/design.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/factor_contracts.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/feature_spec.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_factor_revision_design_codex_ver/availability_by_family.csv
```

따라서 다음 단계는:

```text
full_train_independent_revised_factor_dataset
```

## Full-Train Independent Revised Factor Dataset Update

2026-06-18에 revised factor dataset materialization을 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_dataset.py
```

결과:

```text
status = full_train_independent_revised_factor_dataset_ready
rows = 158
matched = 158
forbidden_hits = 0
validation_used = False
next = full_train_independent_revised_factor_smoke
```

Join summary:

```text
input rows = 158
unique prediction ids = 158
matched raw geometry ids = 158
missing ids = 0
match_rows scanned until complete = 4,046,423
```

Family counts:

| Family | Rows | Raw Feature Rows |
| --- | ---: | ---: |
| `support_contact` | 72 | 72 |
| `relative_vertical` | 55 | 55 |
| `proximity` | 31 | 31 |

Materialized views:

```text
D1_revised_residual_base
D2_support_contact_split_residual
D3_relative_vertical_order_residual
D4_coverage_uncertainty_shrinkage
```

Feature schema:

| View | Numeric Features | Categorical Features |
| --- | ---: | ---: |
| `D1_revised_residual_base` | 37 | 0 |
| `D2_support_contact_split_residual` | 50 | 0 |
| `D3_relative_vertical_order_residual` | 47 | 0 |
| `D4_coverage_uncertainty_shrinkage` | 70 | 3 |

Leakage check:

```text
forbidden_feature_key_hits = 0
geometry_status_as_model_input = False
hidden_metadata_as_model_input = False
multi_view_as_model_input = False
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/79_full_train_independent_revised_factor_dataset.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_dataset.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/revised_factor_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/feature_schema.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/leakage_report.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/report.md
```

따라서 다음 단계는:

```text
full_train_independent_revised_factor_smoke
```

## Full-Train Independent Revised Factor Smoke Update

2026-06-18에 revised factor smoke를 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_smoke.py
```

결과:

```text
status = full_train_independent_revised_factor_smoke_positive
rows = 158
validation_used = False
best_revised = D4_coverage_uncertainty_shrinkage
d_auprc_vs_sg = +0.1241
d_brier_vs_sg = -0.0462
progress_views = D1,D2,D3,D4
next = full_train_independent_revised_factor_error_analysis
```

Grouped main result:

| View | AUROC | AUPRC | Brier | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `semantic_plus_geometry` | 0.6640 | 0.6300 | 0.2341 | 0.6392 |
| `current_factorized_reliability_posterior` | 0.6531 | 0.6253 | 0.2363 | 0.5823 |
| `D1_revised_residual_base` | 0.7782 | 0.7116 | 0.1905 | 0.7468 |
| `D2_support_contact_split_residual` | 0.7846 | 0.7193 | 0.1901 | 0.7215 |
| `D3_relative_vertical_order_residual` | 0.7895 | 0.7382 | 0.1870 | 0.7342 |
| `D4_coverage_uncertainty_shrinkage` | 0.7879 | 0.7541 | 0.1879 | 0.7342 |

Threshold transfer vs `semantic_plus_geometry`:

| View | Fixes | New Mistakes | New-Fix |
| --- | ---: | ---: | ---: |
| `current_factorized_reliability_posterior` | 1 | 10 | +9 |
| `D1_revised_residual_base` | 26 | 9 | -17 |
| `D2_support_contact_split_residual` | 21 | 8 | -13 |
| `D3_relative_vertical_order_residual` | 24 | 9 | -15 |
| `D4_coverage_uncertainty_shrinkage` | 21 | 6 | -15 |

Slice clues for D4:

| Slice | Rows | SG AUPRC | D4 AUPRC | SG Brier | D4 Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 72 | 0.7121 | 0.8566 | 0.2233 | 0.1607 |
| `relative_vertical` | 55 | 0.6729 | 0.7922 | 0.2200 | 0.1793 |
| `proximity` | 31 | 0.3960 | 0.3407 | 0.2843 | 0.2665 |
| `semantic_high_geometry_low` | 16 | 0.6983 | 0.9583 | 0.2391 | 0.1328 |
| `semantic_low_geometry_high` | 97 | 0.5903 | 0.7271 | 0.2379 | 0.1872 |

해석:

- revised raw-witness factorization은 H002에서 처음으로 strong positive smoke를 보였다.
- 그러나 이는 train-only 158-row Codex bootstrap target 결과다.
- `proximity` AUPRC가 낮아졌고, D4의 family categorical feature가 shortcut인지 확인해야 한다.
- 따라서 다음 단계는 performance claim이 아니라 revised factor error analysis다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/80_full_train_independent_revised_factor_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/threshold_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_smoke_codex_ver/slice_metrics.csv
```

따라서 다음 단계는:

```text
full_train_independent_revised_factor_error_analysis
```

## Full-Train Independent Revised Factor Error Analysis Update

2026-06-18에 revised factor smoke 결과를 post-hoc 분석했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_error_analysis.py
```

결과:

```text
status = full_train_independent_revised_factor_error_analysis_ready
validation_used = False
family_only_d_auprc = -0.0000
raw_only_d_auprc = +0.0794
next = full_train_independent_revised_factor_shortcut_controls
```

핵심 진단:

```text
all_revised_views_improve_global_ranking
all_revised_views_improve_global_calibration
family_categorical_not_sole_gain_source
family_interactions_add_ranking_gain_beyond_d1
proximity_ranking_regresses_despite_brier_gain
raw_witness_control_has_strong_signal
```

Shortcut controls:

| Control | AUROC | AUPRC | Brier | dAUPRC vs SG | dBrier vs SG | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `family_only_offset_control` | 0.6632 | 0.6299 | 0.2329 | -0.0000 | -0.0012 | +1 |
| `raw_only_offset_control` | 0.7718 | 0.7094 | 0.1959 | +0.0794 | -0.0382 | -16 |

해석:

- D4 gain은 단순 family categorical shortcut만으로 설명되지 않는다.
- D1은 family categorical feature가 없는데도 이미 `semantic_plus_geometry` 대비
  AUPRC +0.0816, Brier -0.0437, New-Fix -17을 보였다.
- 하지만 raw-only offset control이 강한 신호를 보이므로, raw witness가 bootstrap target
  construction을 반영한 shortcut인지 반드시 확인해야 한다.

Key D4 slices:

| Slice | Rows | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: |
| `support_contact` | 72 | +0.1445 | -0.0626 | -4 |
| `relative_vertical` | 55 | +0.1194 | -0.0407 | -8 |
| `proximity` | 31 | -0.0553 | -0.0178 | -3 |
| `semantic_low_geometry_high` | 97 | +0.1367 | -0.0506 | -12 |
| `semantic_high_geometry_low` | 16 | +0.2601 | -0.1063 | -2 |

Claim boundary:

```text
Allowed: revised raw-witness factorization is promising under train-only
bootstrap labels.

Blocked: paper-level posterior improvement claim.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/81_full_train_independent_revised_factor_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/shortcut_controls.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/slice_deltas.csv
```

따라서 다음 단계는:

```text
full_train_independent_revised_factor_claim_boundary
```

## Full-Train Independent Revised Factor Shortcut Controls Update

2026-06-18에 raw witness shuffle과 family interaction ablation을 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_shortcut_controls.py
```

결과:

```text
status = full_train_independent_revised_factor_shortcut_controls_ready
validation_used = False
all_d4_d_auprc = +0.1241
global_shuffle_retention = -0.6119
within_shuffle_retention = 0.1565
next = full_train_independent_revised_factor_claim_boundary
```

핵심 control:

| Setting | View | dAUPRC vs SG | dBrier vs SG |
| --- | --- | ---: | ---: |
| `all_families` | `D4_coverage_uncertainty_shrinkage` | +0.1241 | -0.0462 |
| `all_families` | `D4_raw_witness_shuffle_global` | -0.0759 | +0.0291 |
| `all_families` | `D4_raw_witness_shuffle_within_family` | +0.0194 | +0.0021 |
| `all_families` | `D4_no_explicit_family_indicators` | +0.1124 | -0.0468 |
| `all_families` | `D4_no_typed_family_interaction` | +0.0827 | -0.0416 |
| `support_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0870 | -0.0399 |
| `proximity_only` | `D4_coverage_uncertainty_shrinkage` | -0.0917 | +0.0290 |

진단:

```text
global_raw_witness_shuffle_substantially_reduces_gain
within_family_raw_witness_alignment_matters
typed_family_interaction_adds_global_signal_but_needs_familywise_audit
support_vertical_scope_does_not_dominate_all_family_scope
proximity_slice_is_not_a_safe_ranking_claim
```

해석:

- D4 gain은 raw witness alignment를 깨뜨리면 대부분 사라진다.
- `predicate_family` 또는 `family_*` indicator만으로는 D4 gain을 설명하기 어렵다.
- typed family interaction은 전체 setting에서는 추가 signal을 만들지만, family-wise
  안정성은 아직 확정되지 않았다.
- proximity는 현재 posterior ranking claim에 넣기 위험하다.
- 다음 단계는 성능 개선이 아니라 H002의 최소 defensible claim boundary를 정하는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/82_full_train_independent_revised_factor_shortcut_controls.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_shortcut_controls.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/control_comparisons.csv
```

따라서 다음 단계는:

```text
full_train_independent_revised_factor_claim_boundary
```

## Full-Train Independent Revised Factor Claim Boundary Update

2026-06-18에 80-82번 revised factor 결과를 바탕으로 H002의 claim boundary를
고정했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_claim_boundary.py
```

결과:

```text
status = full_train_independent_revised_factor_claim_boundary_ready
validation_used = False
scope = support_contact + relative_vertical
proximity_d_auprc = -0.0917
next = full_train_independent_support_vertical_audit_packet
```

Evidence table:

| Role | Setting | View | dAUPRC vs SG | dBrier vs SG |
| --- | --- | --- | ---: | ---: |
| main positive | `support_contact_only` | `D4_coverage_uncertainty_shrinkage` | +0.1572 | -0.0724 |
| main positive | `relative_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0627 | -0.0396 |
| combined scope | `support_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0870 | -0.0399 |
| excluded slice | `proximity_only` | `D4_coverage_uncertainty_shrinkage` | -0.0917 | +0.0290 |
| negative control | `all_families` | `D4_raw_witness_shuffle_global` | -0.0759 | +0.0291 |
| within-family control | `all_families` | `D4_raw_witness_shuffle_within_family` | +0.0194 | +0.0021 |
| simplified ablation | `support_vertical_only` | `D4_no_typed_family_interaction` | +0.0758 | -0.0348 |

허용 claim:

```text
RGA is a train-only diagnostic framework for decomposing relation reliability.
Raw-witness residual factorization is promising for support_contact and
relative_vertical under current bootstrap labels.
```

막힌 claim:

```text
H002 posterior is a paper-level performance improvement.
Proximity is solved.
Typed family interaction is the final combiner.
Codex bootstrap labels are human-confirmed labels.
Validation/test generalization is established.
```

해석:

- H002의 core method boundary는 `RGA-scoped raw-witness residual reliability layer`다.
- D4 typed family interaction은 아직 final method claim으로 고정하지 않는다.
- proximity는 main posterior claim에서 제외하고 failure/risk slice로 둔다.
- 다음 단계는 selected scope의 independent audit packet이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/83_full_train_independent_revised_factor_claim_boundary.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_claim_boundary.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/claim_table.csv
```

따라서 다음 단계는:

```text
full_train_independent_support_vertical_audit_packet
```

## Full-Train Independent Support/Vertical Audit Packet Update

2026-06-18에 claim-boundary selected scope인 `support_contact + relative_vertical`에
대해 independent audit packet을 만들었다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_audit_packet.py
```

결과:

```text
status = full_train_independent_support_vertical_audit_packet_ready
validation_used = False
selected_rows = 127
support = 72
vertical = 55
leakage_hits = 0
next = full_train_independent_support_vertical_label_readiness
```

Packet 구성:

| Item | Count |
| --- | ---: |
| selected rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| ready packet rows | 124 |
| ready with packet caveat rows | 3 |
| missing packet rows | 0 |
| proximity risk rows | 31 |
| labeler leakage hits | 0 |
| packet text leakage hits | 0 |

Labeler-visible sheet에는 다음을 노출한다.

- subject/object/predicate relation candidate.
- family-specific audit question/cues.
- multi-view packet, mesh packet, contact/context sheet path.
- raw witness values: distance, vertical gap, overlap, support-contact gap,
  relative-vertical signed margin/sign agreement.
- reviewer fill-in fields.

Labeler-visible sheet에는 다음을 노출하지 않는다.

- source score/rank.
- `p_geom_valid`.
- `geometry_status`.
- posterior target `y`.
- bootstrap relation label.
- `label_match_status`, `proposed_audit_role`, `queue_kind`, `rank_band`.
- prediction id.

Hidden metadata는 다음 파일에만 보존한다.

```text
internal_reference_post_label_only.jsonl
```

`proximity`는 main audit packet에서 제외하고 다음 risk slice에 보존한다.

```text
proximity_risk_slice_post_label_only.jsonl
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/84_full_train_independent_support_vertical_audit_packet.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_audit_packet.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/support_vertical_audit_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/internal_reference_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/proximity_risk_slice_post_label_only.jsonl
```

따라서 다음 단계는:

```text
full_train_independent_support_vertical_label_readiness
```

## Full-Train Independent Support/Vertical Label Readiness Update

2026-06-18에 selected support/vertical audit sheet의 label-fill readiness를 검증했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_readiness.py
```

결과:

```text
status = full_train_independent_support_vertical_label_readiness_ready_for_label_fill
validation_used = False
rows = 127
errors = 0
leakage = 0
next = full_train_independent_support_vertical_label_fill
```

Coverage:

| Sheet | Rows | Scans | Status |
| --- | ---: | ---: | --- |
| `support_vertical` | 127 | 41 | `pass` |
| `support_contact` | 72 | 33 | `pass` |
| `relative_vertical` | 55 | 23 | `pass` |

Readiness checks:

| Check | Count |
| --- | ---: |
| readiness errors | 0 |
| leakage hits | 0 |
| review-started rows | 0 |
| selected label-ready rows | 127 |
| internal reference rows | 127 |
| proximity risk rows | 31 |

Label fill용 schema:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/completion_schema.json
```

Label fill sheet:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/support_vertical_label_fill_sheet.tsv
```

따라서 다음 단계는:

```text
full_train_independent_support_vertical_label_fill
```

## Full-Train Independent Support/Vertical Label Fill Update

2026-06-18에 selected support/vertical 127-row sheet를 `(codex_ver)` bootstrap label로
채웠다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_labels_filled_codex_ver
validation_used = False
rows = 127
binary = 114
positive = 40
negative = 74
excluded = 13
errors = 0
next = full_train_independent_support_vertical_label_ingestion
```

Label counts:

| Label | Rows |
| --- | ---: |
| `reliable_informative` | 14 |
| `annotation_sparsity_candidate` | 26 |
| `valid_but_trivial_dense` | 45 |
| `invalid_relation` | 21 |
| `invalid_pair` | 8 |
| `abstain_uncertain` | 13 |

Family breakdown:

| Family | Labels |
| --- | --- |
| `support_contact` | `abstain_uncertain:9`, `annotation_sparsity_candidate:12`, `invalid_pair:6`, `invalid_relation:13`, `reliable_informative:6`, `valid_but_trivial_dense:26` |
| `relative_vertical` | `abstain_uncertain:4`, `annotation_sparsity_candidate:14`, `invalid_pair:2`, `invalid_relation:8`, `reliable_informative:8`, `valid_but_trivial_dense:19` |

Boundary:

```text
label_source = codex_ver_support_vertical_visible_witness_bootstrap
human_confirmed = False
hidden_internal_reference_read = False
hidden_target_metadata_used = False
source_score_or_rank_used = False
p_geom_valid_used = False
geometry_status_used = False
posterior_claim_allowed = False
```

해석:

- selected support/vertical rows는 모두 completion schema에 맞게 채워졌다.
- binary usable rows는 114개이며 positive:negative는 40:74다.
- label distribution이 negative-heavy이므로 ingestion 이후 target independence와
  family/predicate shortcut audit가 필요하다.
- 이 label은 human-confirmed가 아니며 paper-level evidence가 아니다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/86_full_train_independent_support_vertical_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/completed_support_vertical_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/binary_targets_preview.jsonl
```

Allowed `independent_relation_label`:

```text
reliable_informative
valid_but_trivial_dense
annotation_sparsity_candidate
ontology_mismatch
invalid_relation
invalid_pair
visibility_or_geometry_artifact
abstain_uncertain
```

Binary policy:

```text
positive = reliable_informative, annotation_sparsity_candidate
negative = valid_but_trivial_dense, invalid_relation, invalid_pair, visibility_or_geometry_artifact
exclude_or_multiclass_only = ontology_mismatch, abstain_uncertain
```

Hidden reference policy:

```text
hidden_fields_must_not_be_visible_before_label_lock = true
hidden_fields_must_not_be_model_inputs = true
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/85_full_train_independent_support_vertical_label_readiness.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/completion_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/support_vertical_label_fill_sheet.tsv
```

이 label fill update 이후 진행할 단계는 ingestion이었고, 아래
`Full-Train Independent Support/Vertical Label Ingestion Update`에서 완료했다:

```text
full_train_independent_support_vertical_label_ingestion
```

## Full-Train Independent Support/Vertical Label Ingestion Update

2026-06-18에 completed support/vertical labels를 label-lock 이후
`internal_reference_post_label_only.jsonl`과 join해 validated labels, binary targets,
multiclass targets, posterior diagnostic rows로 materialize했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_label_ingested_with_target_risk
validation_used = False
labels = 127
binary = 114
positive = 40
negative = 74
excluded = 13
errors = 0
probe = target_independence_risk_hidden_metadata_correlated
next = full_train_independent_support_vertical_target_independence_audit
```

Target artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/87_full_train_independent_support_vertical_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/shortcut_audit.csv
```

Target probe:

| Hidden Key | NMI | Majority Acc | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.5710 | 0.8421 | 0.9583 |
| `label_use_hidden` | 0.4506 | 0.8333 | 0.6667 |
| `rank_band_hidden` | 0.2128 | 0.6930 | 0.7778 |
| `proposed_audit_role_hidden` | 0.1672 | 0.6491 | 0.5000 |
| `queue_kind_hidden` | 0.1634 | 0.6491 | 0.4376 |
| `geometry_status_hidden` | 0.1634 | 0.6491 | 0.4376 |

해석:

- ingestion 자체는 성공했다.
- hidden provenance는 label-lock 이후에만 join됐다.
- hidden target-construction metadata는 audit-only이며 posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 labeler에게는 숨겼고, label-lock 이후
  deployable evidence candidate로만 보존했다.
- `proximity`는 main target에서 제외하고 risk slice로 유지한다.
- target probe에서 hidden metadata correlation이 남아 있으므로 posterior smoke는 아직
  허용하지 않는다.

따라서 다음 단계는:

```text
full_train_independent_support_vertical_target_independence_audit
```

## Full-Train Independent Support/Vertical Target Independence Audit Update

2026-06-18에 selected support/vertical 114-row binary target의 strict hidden
carryover와 construction shortcut을 분리해 audit했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_target_independence_audit_strict_blocked_construction_slice_available
validation_used = False
rows = 114
positive = 40
negative = 74
errors = 0
strict = none
construction = rank_band_balanced_codex_ver
next = full_train_independent_support_vertical_label_policy_revision
```

Strict hidden risks:

| Hidden Key | NMI | Majority Acc | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.5710 | 0.8421 | 0.9583 |
| `label_use_hidden` | 0.4506 | 0.8333 | 0.6667 |
| `rank_band_hidden` | 0.2128 | 0.6930 | 0.7778 |
| `proposed_audit_role_hidden` | 0.1672 | 0.6491 | 0.5000 |
| `queue_kind_hidden` | 0.1634 | 0.6491 | 0.4376 |
| `geometry_status_hidden` | 0.1634 | 0.6491 | 0.4376 |

해석:

- strict controlled slice는 없다.
- `rank_band_balanced_codex_ver`는 70 rows, 35 positive, 35 negative의
  construction-only diagnostic slice로 남는다.
- 그러나 prior bootstrap label carryover가 남아 있으므로 posterior smoke를 method
  evidence로 진행하면 안 된다.
- 다음 단계는 model capacity나 combiner가 아니라 label policy revision이다.

## Full-Train Independent Support/Vertical Label Policy Revision Update

2026-06-18에 support/vertical label policy를 v2로 개정했다. 핵심 변경은
`independent_relation_label`을 labeler-visible field에서 제거하고, factual axes를
채운 뒤 post-label로 target을 derive하는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
```

결과:

```text
status = full_train_independent_support_vertical_label_policy_revision_ready_for_v2_readiness
validation_used = False
rows = 127
support = 72
vertical = 55
same_label = 72
same_use = 95
next = full_train_independent_support_vertical_v2_label_readiness
```

Policy failure evidence:

| Source Key | Target | Majority Acc | NMI |
| --- | --- | ---: | ---: |
| `hidden.relation_validity_label_hidden` | `independent_relation_label` | 0.6142 | 0.4583 |
| `hidden.label_use_hidden` | `label_use` | 0.7480 | 0.3595 |
| `relation_informativeness` | `independent_relation_label` | 0.8268 | 0.7937 |
| `visual_3d_support` | `independent_relation_label` | 0.6457 | 0.5585 |
| `confidence` | `independent_relation_label` | 0.5118 | 0.3160 |

V2 review axes:

```text
endpoint_validity_v2
pair_visibility_v2
relation_geometry_answer_v2
geometry_evidence_strength_v2
relation_informativeness_v2
ontology_fit_v2
uncertainty_reason_v2
audit_notes_v2
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/89_full_train_independent_support_vertical_label_policy_revision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/v2_completion_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/v2_feature_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/support_vertical_v2_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/carryover_table.csv
```

해석:

- v1 label은 prior label/use carryover가 크다.
- v2는 direct reliability label을 제거하고 geometry validity와 relation reliability
  target을 post-label로 derive한다.
- reviewer confidence/visibility/informativeness fields는 posterior input이 아니라
  audit-only target derivation fields로 둔다.
- v2 readiness는 다음 structural gate다.

## Full-Train Independent Support/Vertical V2 Label Readiness Update

2026-06-18에 support/vertical v2 factual-axis sheet의 label-fill readiness를
검증했다. 이 단계는 label을 채우거나 posterior를 학습하지 않고, direct target
shortcut이 제거된 상태로 v2 fill을 시작할 수 있는지 확인한다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_label_readiness_ready_for_fill
validation_used = False
rows = 127
support = 72
vertical = 55
errors = 0
leakage = 0
started = 0
next = full_train_independent_support_vertical_v2_label_fill
```

Coverage:

| Sheet | Rows | Scans | Packet Status |
| --- | ---: | ---: | --- |
| `support_vertical` | 127 | 41 | `ready`: 124, `ready_with_packet_caveat`: 3 |
| `support_contact` | 72 | 33 | `ready`: 70, `ready_with_packet_caveat`: 2 |
| `relative_vertical` | 55 | 23 | `ready`: 54, `ready_with_packet_caveat`: 1 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/90_full_train_independent_support_vertical_v2_label_readiness.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/support_vertical_v2_label_fill_sheet.tsv
```

해석:

- v2 fill sheet는 schema, packet path, family partition, proximity exclusion,
  leakage check를 통과했다.
- labeler-visible surface에는 direct reliability label, binary target, score/rank,
  hidden geometry status, hidden label match, prediction id가 없다.
- 이 결과는 posterior 성능 증거가 아니라, target shortcut을 줄인 v2 factual-axis
  label fill을 시작할 수 있다는 structural readiness evidence다.
- 다음 단계는 `full_train_independent_support_vertical_v2_label_fill`이다.

## Full-Train Independent Support/Vertical V2 Label Fill Update

2026-06-18에 support/vertical v2 factual-axis fill을 완료했다. 이 단계는 direct
relation reliability label이나 binary target을 만들지 않고, factual review axes만
채운다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_labels_filled_codex_ver
validation_used = False
test_used = False
rows = 127
support = 72
vertical = 55
fill_errors = 0
header_errors = 0
next = full_train_independent_support_vertical_v2_label_ingestion
```

주요 axis count:

| Axis | Counts |
| --- | --- |
| `relation_geometry_answer_v2` | `supports_predicate`:81, `contradicts_predicate`:21, `ambiguous`:17, `not_evaluable`:8 |
| `geometry_evidence_strength_v2` | `strong`:20, `moderate`:80, `weak`:19, `none`:8 |
| `relation_informativeness_v2` | `informative`:40, `redundant_room_structure`:45, `uncertain`:42 |
| `ontology_fit_v2` | `fits_predicate`:81, `better_alternative_predicate`:8, `ontology_mismatch`:13, `uncertain`:25 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/91_full_train_independent_support_vertical_v2_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/factual_labels.jsonl
```

해석:

- v2 fill은 factual-axis bootstrap label surface를 만든 것이다.
- direct relation reliability label, binary target, posterior target은 만들지 않았다.
- hidden prior label/use, source score/rank, `p_geom_valid`, `geometry_status`,
  `label_match`, `prediction_id`는 읽지 않았다.
- 다음 단계는 post-label ingestion에서 geometry validity target과 relation reliability
  target을 분리해 derive하고, shortcut/carryover risk를 다시 audit하는 것이다.

## Full-Train Independent Support/Vertical V2 Label Ingestion Update

2026-06-18에 support/vertical v2 factual-axis labels를 label-lock 이후 hidden
reference와 조인하고, target을 두 개로 분리해 materialize했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_label_ingested_with_target_risk
validation_used = False
test_used = False
labels = 127
geometry_validity_binary = 100
geometry_validity_positive = 79
geometry_validity_negative = 21
relation_reliability_binary = 106
relation_reliability_positive = 32
relation_reliability_negative = 74
errors = 0
next = full_train_independent_support_vertical_v2_target_independence_audit
```

Target 분리:

| Target | Rows | Positive | Negative | Excluded |
| --- | ---: | ---: | ---: | ---: |
| `geometry_validity_target_v2` | 100 | 79 | 21 | 27 |
| `relation_reliability_target_v2` | 106 | 32 | 74 | 21 |

Basic post-label probe:

| Target | Probe Status | Main Risk |
| --- | --- | --- |
| `geometry_validity_target_v2` | `target_independence_risk_hidden_metadata_correlated` | `relation_validity_label_hidden` NMI 0.4610 |
| `relation_reliability_target_v2` | `target_independence_risk_hidden_metadata_correlated` | `relation_validity_label_hidden` NMI 0.3313 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/92_full_train_independent_support_vertical_v2_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/relation_reliability_targets_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/relation_reliability_posterior_rows_v2.jsonl
```

해석:

- v2 ingestion은 성공했다.
- `semantic score != geometry validity != relation reliability` 분리가 artifact로
  구현됐다.
- 하지만 basic probe에서 hidden prior label/use 및 construction metadata와의 상관이
  남아 있으므로 posterior smoke를 바로 진행하지 않는다.
- 다음 단계는 dedicated v2 target-independence audit이다.
