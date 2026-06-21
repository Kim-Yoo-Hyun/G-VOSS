# H002 Summary Branch V2

Last updated: 2026-06-20

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

- revised raw-witness factorization은 당시 bootstrap slice에서 strong positive smoke를 보였다.
- 그러나 이는 train-only 158-row Codex bootstrap target 결과다.
- 이 positive wording은 이후 all-label-ready controlled posterior/error analysis에 의해
  현재 claim으로는 superseded되었고, 지금은 feature/family alignment blocker를 우선한다.
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
Historical allowed-at-that-checkpoint: revised raw-witness factorization looked
promising under train-only bootstrap labels.

Current superseding caveat: all-label-ready controlled posterior/error analysis
does not support a posterior improvement claim yet; it supports feature/family
alignment repair first.

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
At this earlier checkpoint, raw-witness residual factorization looked promising
for support_contact and relative_vertical under bootstrap labels. This claim is
now superseded by the all-label-ready controlled posterior/error analysis:
current evidence supports feature/family misalignment rather than a positive
posterior improvement claim.
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

## Full-Train Independent Support/Vertical V2 Target Independence Audit Update

2026-06-18에 v2 target independence audit을 수행했다. 핵심은 expected geometry
alignment와 harmful prior-label carryover를 분리해서 보는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_target_independence_audit_strict_blocked_construction_slice_available
validation_used = False
test_used = False
relation_rows = 106
relation_pos = 32
relation_neg = 74
errors = 0
relation_strict = none
relation_construction = rank_band_balanced_v2
next = revise_full_train_independent_support_vertical_v2_target_or_collect_independent_labels
```

Per-target decision:

| Target | Status | Strict Slice | Construction Slice |
| --- | --- | --- | --- |
| `geometry_validity_target_v2` | `blocked_no_controlled_slice` | `none` | `none` |
| `relation_reliability_target_v2` | `strict_blocked_construction_slice_available` | `none` | `rank_band_balanced_v2` |

Relation construction-only diagnostic slice:

```text
relation_reliability_target_v2/rank_band_balanced_v2.jsonl
rows = 62
positive = 31
negative = 31
harmful_prior_risk_count = 3
construction_risk_count = 0
```

해석:

- v2 target factorization은 구조적으로는 성공했다.
- 그러나 현재 Codex bootstrap target은 여전히 prior-label carryover가 남아 posterior
  method validation target으로 쓰기 어렵다.
- `rank_band_balanced_v2`는 plumbing/error diagnostic에는 쓸 수 있지만 method
  evidence로 쓰면 안 된다.
- 다음 단계는 target construction을 다시 바꾸거나 stronger independent labels를
  수집하는 결정이다.

## Full-Train Independent Support/Vertical V2 Target Path Decision Update

2026-06-18에 v2 target path decision을 수행했다. 결론은 rule-based Codex target을
다시 고치는 것이 아니라 stronger independent labels를 수집하는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_target_path_decision_collect_independent_labels
validation_used = False
test_used = False
collection_rows = 127
support = 72
vertical = 55
construction_rows = 62
labeler_header_leakage_hits = 0
next = full_train_independent_support_vertical_v2_independent_label_fill_or_human_review
```

Option verdict:

| Option | Verdict |
| --- | --- |
| `run_posterior_on_current_v2_target` | `reject` |
| `use_rank_band_balanced_v2_for_method_evidence` | `reject_for_method_evidence` |
| `revise_rule_based_codex_target_again` | `defer` |
| `collect_stronger_independent_labels` | `select` |
| `add_multi_view_as_model_input_now` | `defer` |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/94_full_train_independent_support_vertical_v2_target_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/internal_manifest_post_label_only.jsonl
```

해석:

- 현재 blocker는 posterior combiner capacity가 아니라 target independence다.
- 같은 Codex/witness-derived target을 다시 파생하면 prior-label carryover를 반복할
  가능성이 높다.
- multi-view는 아직 model input이 아니라 independent label audit evidence로 쓰는 것이
  맞다.
- posterior smoke는 strict independent relation-reliability target이 생길 때까지 계속
  blocked다.

## Full-Train Independent Support/Vertical V2 Independent Label Fill Update

2026-06-18에 independent collection sheet를 `(codex_independent_ver)` visible-only
bootstrap으로 채웠다. 이 단계는 human-confirmed review가 아니라, hidden manifest와 v2
Codex axes를 읽지 않는 별도 label-fill surface를 만드는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_independent_labels_filled_codex_independent_ver
validation_used = False
test_used = False
rows = 127
support = 72
vertical = 55
reliable = 32
unreliable = 70
uncertain = 25
geom_support = 81
geom_contra = 21
errors = 0
next = full_train_independent_support_vertical_v2_independent_label_ingestion
```

Independent axis count:

| Axis | Counts |
| --- | --- |
| `geometry_validity_independent` | `supports_predicate`:81, `contradicts_predicate`:21, `ambiguous`:17, `not_evaluable`:8 |
| `relation_reliability_independent` | `reliable`:32, `unreliable`:70, `uncertain`:25 |
| `primary_reason_independent` | `physically_supported_informative`:15, `annotation_sparsity_candidate`:17, `dense_or_trivial_relation`:41, `geometry_contradiction`:21, `visibility_or_evidence_gap`:17, `endpoint_identity_issue`:8, `better_alternative_predicate`:8 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/95_full_train_independent_support_vertical_v2_independent_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/completed_independent_collection_sheet_codex_independent_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/independent_labels.jsonl
```

해석:

- hidden manifest, v2 Codex axes, prior label/use, score/rank, `p_geom_valid`,
  `geometry_status`를 읽지 않은 visible-only fill이다.
- 하지만 human-confirmed label은 아니므로 paper evidence가 아니다.
- 같은 raw witness surface를 사용하므로 v2 target과 분포가 유사할 수 있다.
- 다음 단계는 independent ingestion과 strict target-independence audit이다.

## Full-Train Independent Support/Vertical V2 Independent Label Ingestion Update

2026-06-18에 `(codex_independent_ver)` visible-only label fill을 label-locked
target artifact로 ingest했다. 이 단계에서는 hidden manifest를 label lock 이후에만
join하고, independent label fields를 target/audit 전용으로 고정했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_independent_label_ingested_with_basic_probe_risk
validation_used = False
test_used = False
labels = 127
geometry_validity_independent_target = 102 rows, 81 positive, 21 negative
relation_reliability_independent_target = 102 rows, 32 positive, 70 negative
excluded = 25 per target
errors = 0
next = full_train_independent_support_vertical_v2_independent_target_independence_audit
```

Target count:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_independent_target` | 102 | 81 | 21 | 0.7941 | 25 |
| `relation_reliability_independent_target` | 102 | 32 | 70 | 0.3137 | 25 |

Basic probe:

| Target | Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_independent_target` | `target_independence_risk_hidden_metadata_correlated` | 6 | 1 |
| `relation_reliability_independent_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 1 |

주요 hidden risk:

| Target | Hidden Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| `geometry_validity_independent_target` | `relation_validity_label_hidden` | 0.8627 | 0.4491 | 1.0000 |
| `geometry_validity_independent_target` | `label_use_hidden` | 0.7941 | 0.3069 | 0.4269 |
| `relation_reliability_independent_target` | `relation_validity_label_hidden` | 0.7451 | 0.3166 | 0.6250 |
| `relation_reliability_independent_target` | `label_use_hidden` | 0.7353 | 0.3052 | 0.5216 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/96_full_train_independent_support_vertical_v2_independent_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/validated_independent_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/relation_reliability_independent_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/target_independence_probe.json
```

해석:

- independent labels는 artifact로 materialize됐다.
- geometry validity와 relation reliability는 분리된 target으로 생성됐다.
- ingestion error와 validation/test leakage는 없다.
- 하지만 basic probe에서 hidden prior-label/construction metadata와의 correlation이
  여전히 남아 있다.
- 이번 ingestion manifest에는 source score/rank와 `p_geom_valid`가 없으므로 posterior
  smoke 전에 post-label feature join도 별도 gate로 필요하다.
- 다음 단계는 posterior smoke가 아니라 independent target-independence audit이다.

## Full-Train Independent Support/Vertical V2 Independent Target Independence Audit Update

2026-06-18에 independent target-independence audit을 수행했다. 결론은 independent
visible-only label surface로 바꿔도 strict relation-reliability target은 아직 생기지
않는다는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_independent_target_independence_audit_strict_blocked_construction_slice_available
validation_used = False
test_used = False
relation_rows = 102
relation_pos = 32
relation_neg = 70
errors = 0
relation_strict = none
relation_construction = rank_band_balanced_independent
next = revise_independent_target_or_collect_human_confirmed_support_vertical_labels
```

Per-target decision:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_independent_target` | `blocked_no_controlled_slice` | 102 | 81 | 21 | `none` | `none` |
| `relation_reliability_independent_target` | `strict_blocked_construction_slice_available` | 102 | 32 | 70 | `none` | `rank_band_balanced_independent` |

Construction-only diagnostic slice:

```text
relation_reliability_independent_target/rank_band_balanced_independent.jsonl
rows = 62
positive = 31
negative = 31
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 1
```

Original target risks:

| Target | Risk | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | --- | ---: | ---: | ---: |
| `geometry_validity_independent_target` | harmful prior | `relation_validity_label_hidden` | 0.8627 | 0.4491 | 1.0000 |
| `geometry_validity_independent_target` | harmful prior | `label_use_hidden` | 0.7941 | 0.3069 | 0.4269 |
| `relation_reliability_independent_target` | harmful prior | `relation_validity_label_hidden` | 0.7451 | 0.3166 | 0.6250 |
| `relation_reliability_independent_target` | harmful prior | `label_use_hidden` | 0.7353 | 0.3052 | 0.5216 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/97_full_train_independent_support_vertical_v2_independent_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver/target_slices/relation_reliability_independent_target/rank_band_balanced_independent.jsonl
```

해석:

- Codex independent visible-only label은 labeler surface separation 측면에서는 이전보다
  낫다.
- 그러나 same raw witness surface와 기존 selected candidate construction의 영향이 남아
  hidden prior-label carryover를 제거하지 못했다.
- `rank_band_balanced_independent`는 diagnostic slice일 뿐 method-validation target이
  아니다.
- posterior smoke는 계속 blocked다.
- 다음 단계는 또 다른 Codex target revision보다 human-confirmed support/vertical label
  subset의 최소 설계를 결정하는 것이다.

## Full-Train Independent Support/Vertical V2 Human Label Path Update

2026-06-18에 human label path decision을 수행했다. 결론은 또 다른 Codex-derived
target revision을 main path로 두지 않고, human-confirmed support/vertical label을
수집하는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_human_label_path_decision_collect_human_confirmed_labels
validation_used = False
test_used = False
minimum_human_batch = 96 rows
minimum_est_binary = 81
minimum_est_positive = 32
minimum_est_negative = 49
full_human_batch = 127 rows
full_est_binary = 102
labeler_header_leakage_hits = 0
next = full_train_independent_support_vertical_v2_human_label_fill_or_external_review
```

Decision:

| Option | Verdict |
| --- | --- |
| `revise_codex_target_again` | `reject_as_main_path` |
| `use_rank_band_balanced_independent_for_method_evidence` | `reject_for_method_evidence` |
| `collect_minimum_human_batch_96` | `acceptable_first_batch` |
| `collect_full_human_batch_127` | `recommended` |
| `add_multi_view_as_model_input_now` | `defer` |

Batch plan:

| Batch | Rows | Estimated Binary | Estimated Positive | Estimated Negative | Role |
| --- | ---: | ---: | ---: | ---: | --- |
| `minimum_human_batch_96` | 96 | 81 | 32 | 49 | acceptable first batch |
| `full_human_batch_127` | 127 | 102 | 32 | 70 | recommended |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/98_full_train_independent_support_vertical_v2_human_label_path.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/human_collection_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/minimum_human_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/full_human_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/sampling_plan.json
```

해석:

- 현재 실패 원인은 posterior 결합 방식이 아니라 target independence다.
- full 127-row human batch가 권장된다. 비용이 작고 class/uncertainty/audit risk에 가장
  안전하다.
- 96-row minimum batch는 hypothesis-stage gate를 넘는 첫 batch로 쓸 수 있지만,
  target-independence audit이 실패하면 full 127로 확장해야 한다.
- 이 support/vertical batch는 hypothesis-stage target gate이며, broad paper-level
  posterior revival gate `>=150` binary rows를 대체하지 않는다.
- posterior smoke는 human label ingestion과 target-independence audit 전까지 계속
  blocked다.

## Full-Train Independent Support/Vertical V2 Human Label Fill Update

2026-06-18에 사용자의 요청에 따라 Codex가 human collection sheet의 `human_*` fields를
대신 채웠다. 이 값은 이후 hypothesis workflow에서는 human-confirmed로 취급하고 진행하되,
provenance는 `codex_proxy_user_review_pending`로 유지한다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_human_fields_filled_codex_proxy_user_review_pending
validation_used = False
test_used = False
minimum_rows = 96
minimum_binary = 81
minimum_positive = 32
minimum_negative = 49
full_rows = 127
full_binary = 102
full_positive = 32
full_negative = 70
errors = 0
next = full_train_independent_support_vertical_v2_human_label_ingestion
```

Provenance boundary:

```text
filled_by = codex_proxy
workflow_treatment = human_confirmed_by_user_request
user_review_pending = true
paper_evidence_allowed_before_user_confirmation = false
```

해석:

- Full 127-row batch가 primary path다.
- 102 binary rows, positive 32 / negative 70으로 support/vertical scoped
  hypothesis-stage gate는 넘는다.
- 이 fill은 target-independence audit을 진행하기 위한 pragmatic proxy다.
- 사용자 확인 전에는 independent external human annotation이나 paper-locked human label로
  주장하지 않는다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/99_full_train_independent_support_vertical_v2_human_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/completed_full_human_collection_sheet_codex_proxy_user_review_pending.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_fill_codex_proxy_user_review_pending/full_human_proxy_labels.jsonl
```

## Full-Train Independent Support/Vertical V2 Human Label Ingestion Update

2026-06-18에 full 127-row Codex proxy human sheet를 ingest하여 H002의 human-target
artifacts를 만들었다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_human_label_ingested_with_basic_probe_risk
labels = 127
geometry_validity_binary = 102
geometry_validity_positive = 81
geometry_validity_negative = 21
relation_reliability_binary = 102
relation_reliability_positive = 32
relation_reliability_negative = 70
errors = 0
validation_used = False
test_used = False
next = full_train_independent_support_vertical_v2_human_target_independence_audit
```

Target counts:

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_human_target` | 102 | 81 | 21 | 0.7941 | 25 |
| `relation_reliability_human_target` | 102 | 32 | 70 | 0.3137 | 25 |

Basic probe:

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_human_target` | `target_independence_risk_hidden_metadata_correlated` | 6 | 1 |
| `relation_reliability_human_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 1 |

해석:

- Ingestion은 성공했고 binary target artifact도 생성됐다.
- 그러나 basic probe는 hidden metadata correlation risk를 계속 표시한다.
- 따라서 posterior smoke는 아직 진행하지 않는다.
- 다음 단계는 `relation_reliability_human_target`에 대한 dedicated target-independence
  audit이다.
- 이 audit이 strict slice를 찾지 못하면 combiner를 강화하는 것이 아니라 label protocol
  또는 evidence source를 다시 봐야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/100_full_train_independent_support_vertical_v2_human_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/validated_human_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/geometry_validity_human_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/relation_reliability_human_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending/target_independence_probe.json
```

## Full-Train Independent Support/Vertical V2 Human Target Independence Audit Update

2026-06-18에 Codex proxy human targets를 대상으로 dedicated target-independence audit을
수행했다. 사용자의 요청에 따라 workflow상 human-confirmed로 취급하고 진행했지만,
실제 결과는 target-independence blocker가 유지된다는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_human_target_independence_audit_strict_blocked_construction_slice_available
validation_used = False
test_used = False
relation_rows = 102
relation_positive = 32
relation_negative = 70
errors = 0
relation_strict = none
relation_construction = rank_band_balanced_human
next = revise_human_label_protocol_or_add_external_review_evidence
```

Per-target result:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_human_target` | `blocked_no_controlled_slice` | 102 | 81 | 21 | `none` | `none` |
| `relation_reliability_human_target` | `strict_blocked_construction_slice_available` | 102 | 32 | 70 | `none` | `rank_band_balanced_human` |

Construction-only relation slice:

```text
relation_reliability_human_target/rank_band_balanced_human.jsonl
rows = 62
positive = 31
negative = 31
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 1
```

해석:

- proxy-human label로 바꿔도 strict relation-reliability slice는 생기지 않았다.
- `rank_band_balanced_human`은 construction diagnostic에는 쓸 수 있지만, harmful prior
  carryover가 남아 있어 posterior method validation에는 부족하다.
- 따라서 현재 blocker는 combiner capacity가 아니라 target/evidence independence다.
- 다음 단계는 posterior smoke가 아니라 `revise_human_label_protocol_or_add_external_review_evidence`다.
- 특히 candidate construction에 이미 들어간 hidden validity labels와 독립인 evidence source가
  필요하다. 여기서 multi-view/mesh/contact packet은 model input이 아니라 label/audit
  evidence로 먼저 쓰는 것이 맞다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/101_full_train_independent_support_vertical_v2_human_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending/target_slices/relation_reliability_human_target/rank_band_balanced_human.jsonl
```

## Full-Train Independent Support/Vertical V2 External Review Protocol Update

2026-06-18에 `revise_human_label_protocol_or_add_external_review_evidence` TODO를
진행했다. 결론은 stronger posterior combiner로 넘어가지 않고, external evidence 기반의
새 label protocol을 만드는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_external_review_protocol_ready
rows = 127
ready_packets = 124
packet_path_errors = 0
header_leakage_hits = 0
validation_used = False
test_used = False
next = fill_external_evidence_review_sheet_or_user_review
```

새 protocol의 핵심:

- 이전 sheet에 있던 numeric witness values와 positive/negative cue text를 제거했다.
- source score/rank, `p_geom_valid`, geometry status, previous proxy labels, hidden prior
  labels, v2 reference axes를 labeler-visible surface에서 제거했다.
- labeler는 multi-view packet, mesh packet, contact/context sheet만 보고 external
  evidence label을 채운다.
- multi-view/mesh/contact evidence는 아직 model input이 아니라 audit/label evidence다.
- target은 label lock 이후 `geometry_validity_external_target`과
  `relation_reliability_external_target`으로 derive한다.

Counts:

| Item | Count |
| --- | ---: |
| external review rows | 127 |
| `support_contact` rows | 72 |
| `relative_vertical` rows | 55 |
| ready packets | 124 |
| ready with packet caveat | 3 |
| packet path errors | 0 |
| labeler header leakage hits | 0 |

해석:

- 현재 문제는 combiner capacity가 아니라 target/evidence independence다.
- 새 sheet는 posterior feature로 쓸 numeric witness를 labeler-visible field에서 뺐기 때문에
  이전 proxy-human target보다 더 독립적인 audit path다.
- 이 단계는 label protocol을 만든 것이며, 아직 external label이 채워진 것은 아니다.
- posterior smoke는 external label ingestion과 target-independence audit 전까지 계속
  blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/102_full_train_independent_support_vertical_v2_external_review_protocol.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_evidence_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_review_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/reviewer_instructions.md
```

## Full-Train Independent Support/Vertical V2 External Review Fill Update

2026-06-18에 `fill_external_evidence_review_sheet_or_user_review` TODO를 진행했다.
사용자가 직접 채워야 하는 단계에 가깝지만, 요청에 따라 Codex가 대신 채우고 workflow상
user-requested review로 취급한다. 단, provenance는 실제 user/external human annotation이
아니라 `codex_proxy_user_requested`로 유지한다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_external_review_filled_codex_proxy_user_requested
rows = 127
reliable = 47
unreliable = 69
uncertain = 11
errors = 0
validation_used = False
test_used = False
next = external_evidence_review_label_ingestion
```

Label distribution:

| Field | Value | Count |
| --- | --- | ---: |
| `final_relation_reliability_external` | `reliable` | 47 |
| `final_relation_reliability_external` | `unreliable` | 69 |
| `final_relation_reliability_external` | `uncertain` | 11 |
| `visual_geometry_answer_external` | `supports_predicate` | 105 |
| `visual_geometry_answer_external` | `contradicts_predicate` | 11 |
| `visual_geometry_answer_external` | `uncertain` | 11 |

Boundary:

- hidden manifest를 읽지 않았다.
- numeric witness values를 읽지 않았다.
- previous proxy labels를 읽지 않았다.
- source score/rank를 읽지 않았다.
- `p_geom_valid`를 읽지 않았다.
- validation/test를 사용하지 않았다.
- posterior를 학습하지 않았다.

해석:

- 127-row external review sheet는 모두 채워졌다.
- schema validation error는 0이다.
- 이 fill은 이전 proxy-human label보다 target-construction leakage가 적은 surface에서
  만들어졌지만, 실제 independent external human annotation은 아니다.
- 다음 단계는 ingestion을 통해 `geometry_validity_external_target`과
  `relation_reliability_external_target`을 만들고, target-independence probe를 다시
  수행하는 것이다.
- posterior smoke는 external target audit 전까지 계속 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/103_full_train_independent_support_vertical_v2_external_review_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/completed_external_evidence_review_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/external_proxy_labels.jsonl
```

## Full-Train Independent Support/Vertical V2 External Review Ingestion Update

2026-06-18에 `external_evidence_review_label_ingestion` TODO를 진행했다. Completed
external review sheet를 ingest하여 external geometry/reliability targets를 만들고 basic
target-independence probe를 수행했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_external_review_ingested_with_basic_probe_risk
labels = 127
geometry_validity_binary = 116
geometry_validity_positive = 105
geometry_validity_negative = 11
relation_reliability_binary = 116
relation_reliability_positive = 47
relation_reliability_negative = 69
errors = 0
validation_used = False
test_used = False
next = external_evidence_review_target_independence_audit
```

Target counts:

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_external_target` | 116 | 105 | 11 | 0.9052 | 11 |
| `relation_reliability_external_target` | 116 | 47 | 69 | 0.4052 | 11 |

Basic probe:

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_external_target` | `target_independence_risk_hidden_metadata_correlated` | 8 | 3 |
| `relation_reliability_external_target` | `target_independence_risk_hidden_metadata_correlated` | 5 | 0 |

해석:

- External target ingestion은 성공했고 validation error는 0이다.
- `relation_reliability_external_target`은 116 binary rows, 47 positive / 69 negative로
  이전 human-proxy target보다 usable rows가 늘었다.
- relation reliability에서 visible non-target shortcut은 0으로 줄었다.
- 그러나 hidden metadata correlation risk가 5개 남아 있으므로 posterior smoke는 아직
  blocked다.
- 다음 단계는 dedicated target-independence audit이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/104_full_train_independent_support_vertical_v2_external_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/validated_external_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/geometry_validity_external_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/relation_reliability_external_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/target_independence_probe.json
```

## Full-Train Independent Support/Vertical V2 External Review Target Independence Audit Update

2026-06-18에 `external_evidence_review_target_independence_audit` TODO를 진행했다.
External review target이 posterior smoke에 들어갈 만큼 독립적인지 dedicated audit으로
확인했다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_external_review_target_independence_audit_strict_blocked_construction_slice_available
validation_used = False
test_used = False
relation_rows = 116
relation_positive = 47
relation_negative = 69
errors = 0
relation_strict = none
relation_construction = rank_band_balanced_external
next = revise_external_review_or_collect_true_user_labels
```

Per-target result:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_external_target` | `blocked_no_controlled_slice` | 116 | 105 | 11 | `none` | `none` |
| `relation_reliability_external_target` | `strict_blocked_construction_slice_available` | 116 | 47 | 69 | `none` | `rank_band_balanced_external` |

Construction-only relation slice:

```text
relation_reliability_external_target/rank_band_balanced_external.jsonl
rows = 70
positive = 35
negative = 35
harmful_prior_risk_count = 3
construction_risk_count = 0
expected_geometry_alignment_risk_count = 0
visible_non_target_risk_count = 0
```

해석:

- External review surface는 visible shortcut과 construction risk를 줄이는 데 효과가 있었다.
- 그러나 strict relation-reliability slice는 여전히 없다.
- 남은 blocker는 `relation_validity_label_hidden`, `label_use_hidden`,
  `posterior_target_y_hidden` carryover다.
- 현재 상태에서 posterior smoke를 실행하면 method validation이 아니라 hidden prior carryover
  fitting일 수 있다.
- 다음 단계는 `revise_external_review_or_collect_true_user_labels`다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/105_full_train_independent_support_vertical_v2_external_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/target_slices/relation_reliability_external_target/rank_band_balanced_external.jsonl
```

## Full-Train Independent Support/Vertical V2 True User Review Path Update

2026-06-19에 `revise_external_review_or_collect_true_user_labels` TODO를 진행했다.
결론은 proxy label을 method-validation evidence로 더 늘리지 않고, true user/external
review path를 여는 것이다.

실행:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_true_user_review_path_ready
rank_rows = 70
full_rows = 127
missing_rank_ids = 0
rank_header_leaks = 0
rank_packet_errors = 0
validation_used = False
test_used = False
next = fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels
```

Decision:

```text
collect_true_user_labels_on_rank_band70_first
```

Reason:

- revised external surface는 visible/construction shortcut을 줄였다.
- 그러나 proxy target은 harmful prior carryover를 제거하지 못했다.
- 따라서 proxy-only path는 diagnostic으로만 유지하고, method-validation target은 true
  user/external labels가 필요하다.
- first pass는 70-row `rank_band_balanced_external` slice가 가장 낫다.

Review batches:

| Batch | Rows | Role | Proxy Planning Balance |
| --- | ---: | --- | --- |
| `rank_band70` | 70 | recommended first pass | 35 positive / 35 negative by proxy target; planning only |
| `full127` | 127 | optional expansion | 47 positive / 69 negative among 116 binary rows by proxy target; planning only |

Leakage checks:

| Check | Count |
| --- | ---: |
| rank-band header leakage | 0 |
| full header leakage | 0 |
| rank-band packet path errors | 0 |
| full packet path errors | 0 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/106_full_train_independent_support_vertical_v2_true_user_review_path.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_path.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_rank_band70.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_full127.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_manifest_rank_band70_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/reviewer_instructions.md
```

## Full-Train Independent Support/Vertical V2 True User Review Fill Update

2026-06-19에 `fill_true_user_review_sheet_rank_band70_or_user_confirmed_labels` TODO를
진행했다. 사용자 요청에 따라 70-row `rank_band70` sheet를 Codex가 먼저 채웠고,
이 산출물은 `codex_proxy_true_user_review_pending_confirmation` 상태로 둔다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_true_user_review_rank_band70_filled_codex_proxy_pending_confirmation
rows = 70
reliable = 35
unreliable = 35
uncertain = 0
errors = 0
validation_used = False
test_used = False
next = true_user_review_rank_band70_label_ingestion
```

Boundary:

- Open3DSG train-only hypothesis-stage fill이다.
- validation/test는 사용하지 않았다.
- posterior를 학습하지 않았다.
- H001 artifact를 사용하거나 수정하지 않았다.
- hidden manifest, numeric witness values, previous proxy labels, source score/rank,
  `p_geom_valid`는 fill input으로 사용하지 않았다.
- 이 label은 실제 human/external annotation이 아니며, paper evidence로 쓰기 전에
  사용자 확인이 필요하다.

Filled label counts:

| Item | Count |
| --- | ---: |
| rows | 70 |
| reliable | 35 |
| unreliable | 35 |
| uncertain | 0 |
| validation errors | 0 |

Family counts:

| Family | Rows |
| --- | ---: |
| `relative_vertical` | 30 |
| `support_contact` | 40 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/107_full_train_independent_support_vertical_v2_true_user_review_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/completed_true_user_review_sheet_rank_band70_codex_proxy_pending_confirmation.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_fill_rank_band70_codex_proxy_pending_confirmation/true_user_proxy_labels_rank_band70.jsonl
```

## Full-Train Independent Support/Vertical V2 True User Review Ingestion Update

2026-06-19에 `true_user_review_rank_band70_label_ingestion` TODO를 진행했다.
70-row Codex-proxy pending-confirmation review labels를 ingest하고, target과 basic
target-independence probe를 생성했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_true_user_review_ingested_with_basic_probe_risk
labels = 70
geom_binary = 70
geom_pos = 69
geom_neg = 1
rel_binary = 70
rel_pos = 35
rel_neg = 35
errors = 0
validation_used = False
test_used = False
next = true_user_review_rank_band70_target_independence_audit
```

Target counts:

| Target | Rows | Pos | Neg | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_true_user_review_target` | 70 | 69 | 1 | 0.9857 | 0 |
| `relation_reliability_true_user_review_target` | 70 | 35 | 35 | 0.5000 | 0 |

Basic probe:

| Target | Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_true_user_review_target` | `target_independence_risk_hidden_metadata_correlated` | 8 | 3 |
| `relation_reliability_true_user_review_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 0 |

해석:

- ingestion과 target materialization은 성공했다.
- relation reliability target은 35/35로 균형이 맞고 visible shortcut은 0이다.
- 그러나 hidden prior carryover가 남아 있어 posterior smoke는 아직 blocked다.
- geometry validity target은 69/1로 거의 전부 positive라 현재 batch에서는 posterior
  target으로 약하다.
- 다음 단계는 dedicated target-independence audit이다.

Boundary:

- Open3DSG train-only hypothesis-stage ingestion이다.
- validation/test는 사용하지 않았다.
- posterior를 학습하지 않았다.
- H001 artifact를 사용하거나 수정하지 않았다.
- review fields, hidden metadata, previous proxy labels, multi-view packet paths는
  target/audit only이며 posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 아직 join하지 않았다.
- 이 label은 실제 human/external annotation이 아니며, paper evidence로 쓰기 전에
  사용자 확인이 필요하다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/108_full_train_independent_support_vertical_v2_true_user_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/validated_true_user_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/relation_reliability_true_user_review_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation/target_independence_probe.json
```

## Full-Train Independent Support/Vertical V2 True User Review Target Independence Audit Update

2026-06-19에 `true_user_review_rank_band70_target_independence_audit` TODO를 진행했다.
70-row Codex-proxy pending-confirmation true-user-review target이 posterior smoke에 들어갈
수 있는지 dedicated audit으로 확인했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_true_user_review_target_independence_audit_strict_blocked_construction_slice_available
relation_rows = 70
relation_pos = 35
relation_neg = 35
errors = 0
relation_strict = none
relation_construction = rank_band_balanced_true_user_review
validation_used = False
test_used = False
next = revise_true_user_review_target_or_collect_real_user_labels
```

Per-target decision:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_true_user_review_target` | `blocked_no_controlled_slice` | 70 | 69 | 1 | `none` | `none` |
| `relation_reliability_true_user_review_target` | `strict_blocked_construction_slice_available` | 70 | 35 | 35 | `none` | `rank_band_balanced_true_user_review` |

Relation target original hidden risks:

| Hidden Key | Majority Acc | NMI | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.8571 | 0.5096 | 0.8333 |
| `label_use_hidden` | 0.8571 | 0.4572 | 0.7537 |
| `posterior_target_y_hidden` | 0.8571 | 0.4572 | 0.7537 |

해석:

- relation reliability target은 35/35로 균형이 맞고 construction axis는 통제되어 있다.
- 하지만 hidden prior label structure와 강하게 연결되어 strict slice가 없다.
- `rank_band_balanced_true_user_review` construction-only slice는 70 rows, 35/35지만
  harmful prior risk 3개가 남아 method-validation evidence가 아니다.
- geometry target은 69/1로 거의 single-class라 posterior target으로 부적절하다.
- posterior smoke는 계속 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/109_full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation/slice_summaries.csv
```

## Full-Train Independent Support/Vertical V2 True User Review Target Path Decision Update

2026-06-19에 `revise_true_user_review_target_or_collect_real_user_labels` TODO를 진행했다.
결론은 posterior 결합 방식 개선이 아니라, 실제 독립 label 확보를 우선하는 것이다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_true_user_review_target_path_decision_collect_real_independent_labels
decision = collect_real_independent_labels_on_rank_band70_first
relation_rows = 70
relation_pos = 35
relation_neg = 35
relation_strict = none
relation_construction = rank_band_balanced_true_user_review
geometry_pos = 69
geometry_neg = 1
posterior_allowed = False
validation_used = False
test_used = False
next = collect_real_user_labels_on_rank_band70_sheet
```

해석:

- 현재 blocker는 posterior combiner capacity가 아니다.
- `geometry_validity_true_user_review_target`은 69/1로 거의 single-class라 discrimination
  target으로 약하다.
- `relation_reliability_true_user_review_target`은 35/35로 균형이 맞지만 hidden
  `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden` carryover가 남았다.
- construction-only slice는 diagnostic일 뿐 method-validation evidence가 아니다.
- 따라서 더 강한 combiner를 넣기 전에 실제 독립 reviewer label이 필요하다.

선택:

```text
collect_real_independent_labels_on_rank_band70_first
```

Real label collection packet:

| Item | Path / Count |
| --- | --- |
| review sheet | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_rank_band70.tsv` |
| review sheet rows + header | 71 |
| reviewer instructions | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/reviewer_instructions.md` |
| post-label manifest, audit only | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_manifest_rank_band70_post_label_only.jsonl` |
| post-label manifest rows | 70 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/110_full_train_independent_support_vertical_v2_true_user_review_target_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/real_label_collection_request.md
```

## Full-Train Independent Support/Vertical V2 User-Submitted Review Ingestion Update

2026-06-19에 사용자가 채웠다고 보고한 70-row `rank_band70` review sheet를 ingest했다.
이 단계는 posterior smoke가 아니라 target materialization과 기본 shortcut probe다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_user_submitted_review_ingested_with_basic_probe_risk
labels = 70
geometry_target_binary_rows = 68
geometry_pos = 57
geometry_neg = 11
relation_target_binary_rows = 68
relation_pos = 35
relation_neg = 33
ingestion_errors = 0
reviewer_id_caveat = True
validation_used = False
test_used = False
next = user_submitted_rank_band70_target_independence_audit
```

해석:

- relation reliability target은 35/33으로 균형이 좋고 visible shortcut은 0이다.
- geometry validity target은 57/11로 기존 69/1보다 낫지만 min class가 11이라 아직 작다.
- 두 target 모두 hidden metadata correlation risk가 남아 dedicated audit이 필요하다.
- sheet 내부 reviewer id가 `codex_packet_only_diagnostic`으로 남아 있으므로, 이 결과는
  verified independent external annotation이 아니라 user-submitted packet-only diagnostic으로
  기록한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/111_full_train_independent_support_vertical_v2_user_submitted_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/validated_user_submitted_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/relation_reliability_user_submitted_review_targets.jsonl
```

## Full-Train Independent Support/Vertical V2 User-Submitted Review Target Independence Audit Update

2026-06-19에 user-submitted target이 posterior smoke에 들어갈 수 있는지 dedicated
target-independence audit을 진행했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit_blocked
relation_rows = 68
relation_pos = 35
relation_neg = 33
errors = 0
relation_strict = none
relation_construction = none
reviewer_id_caveat = True
validation_used = False
test_used = False
next = confirm_reviewer_independence_or_collect_external_labels
```

Per-target decision:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_user_submitted_review_target` | `blocked_no_controlled_slice` | 68 | 57 | 11 | `none` | `none` |
| `relation_reliability_user_submitted_review_target` | `blocked_no_controlled_slice` | 68 | 35 | 33 | `none` | `none` |

해석:

- user-submitted label은 class balance 측면에서는 개선됐지만, strict target-independence를
  통과하지 못했다.
- relation target은 hidden `relation_validity_label_hidden`과 여전히 연결된다.
- construction-only slice도 없어서 이번 결과는 posterior method-validation evidence가 아니다.
- reviewer provenance caveat도 남아 있다.
- 따라서 posterior smoke는 계속 blocked이며, 다음 단계는 reviewer independence 확인 또는
  external label 재수집이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/112_full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/slice_summaries.csv
```

## Full-Train Independent Support/Vertical V2 Reviewer Provenance Decision Update

2026-06-19에 `confirm_reviewer_independence_or_collect_external_labels` TODO를 진행했다.
artifact 수준 reviewer provenance와 target audit 결과를 함께 보고 다음 경로를 정했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_reviewer_provenance_decision_collect_external_labels
user_rows = 70
codex_like_rows = 70
independence_confirmed = False
relation_strict = none
relation_construction = none
external_rows = 127
validation_used = False
test_used = False
next = collect_external_full127_labels_with_fixed_reviewer_provenance
```

해석:

- 제출된 70-row sheet의 reviewer id는 전부 `codex_packet_only_diagnostic`이다.
- 따라서 artifact 수준에서는 독립 reviewer provenance가 확인되지 않는다.
- 다만 더 중요한 점은, provenance를 확인하더라도 112 audit에서 strict slice와
  construction-only slice가 모두 없었다는 점이다.
- 그래서 같은 70-row label을 reviewer id만 바꿔 posterior smoke로 넘기는 것은 방어하기 어렵다.
- 다음 경로는 full-127 external evidence review sheet를 fixed non-Codex reviewer provenance로
  다시 채우는 것이다.

External label path:

| Item | Count |
| --- | ---: |
| full external review rows | 127 |
| `support_contact` rows | 72 |
| `relative_vertical` rows | 55 |
| ready packets | 124 |
| ready with packet caveat | 3 |
| packet path errors | 0 |
| header leakage hits | 0 |

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/113_full_train_independent_support_vertical_v2_reviewer_provenance_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/provenance_confirmation_request.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_label_collection_request.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_evidence_review_sheet_full127_fixed_provenance.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_manifest_full127_post_label_only.jsonl
```

## Full-Train Independent Support/Vertical V2 User-Confirmed Review Ingestion Update

사용자가 70-row sheet를 직접 채운 것으로 취급하라고 명시했기 때문에, 2026-06-19에
user-confirmed artifact를 별도로 생성했다. 원본 sheet의 reviewer id는 그대로 보존하고,
사용자 확인을 별도 provenance override로 기록했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_user_confirmed_review_ingested_with_basic_probe_risk
labels = 70
geometry_target_binary_rows = 68
geometry_pos = 57
geometry_neg = 11
relation_target_binary_rows = 68
relation_pos = 35
relation_neg = 33
ingestion_errors = 0
user_confirmed = True
independent_verified = True
validation_used = False
test_used = False
next = user_confirmed_rank_band70_target_independence_audit
```

해석:

- provenance caveat는 user-confirmed artifact 안에서 해소했다.
- 하지만 label 값이 같으므로 target distribution도 기존 user-submitted target과 같다.
- 따라서 posterior smoke로 바로 가지 않고 target-independence audit을 다시 수행했다.

## Full-Train Independent Support/Vertical V2 User-Confirmed Review Target Independence Audit Update

2026-06-19에 user-confirmed target으로 dedicated target-independence audit을 다시 수행했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit_blocked
relation_rows = 68
relation_pos = 35
relation_neg = 33
errors = 0
relation_strict = none
relation_construction = none
user_confirmed = True
validation_used = False
test_used = False
next = expand_user_confirmed_labels_or_revise_sampling_protocol
```

Per-target decision:

| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_user_confirmed_review_target` | `blocked_no_controlled_slice` | 68 | 57 | 11 | `none` | `none` |
| `relation_reliability_user_confirmed_review_target` | `blocked_no_controlled_slice` | 68 | 35 | 33 | `none` | `none` |

해석:

- 사용자가 채운 것으로 취급해도 target-independence blocker는 해결되지 않았다.
- relation target은 균형이 좋지만 hidden `relation_validity_label_hidden`과 연결된다.
- construction-only slice도 없으므로 현재 70-row user-confirmed target은 posterior
  method-validation evidence로 쓰기 어렵다.
- 다음은 full-127로 확장할지, 아니면 hidden prior carryover를 줄이는 sampling protocol을
  먼저 재설계할지 결정하는 단계다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/114_full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/115_full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_ingestion_rank_band70/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/summary.json
```

## Full-Train Independent Support/Vertical V2 Sampling Protocol Decision Update

2026-06-19에 `expand_user_confirmed_labels_or_revise_sampling_protocol` TODO를 진행했다.
결론은 같은 protocol로 full-127만 확장하지 말고, hidden sampling axis를 더 균형 있게
통제하는 revised sampling을 먼저 쓰는 것이다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_sampling_protocol_decision_revise_sampling_first
decision = revise_sampling_first
all_candidates = 315
joined = 302
priority = 160
missing = 13
header_leakage = 0
validation_used = False
test_used = False
next = fill_revised_sampling_priority160_sheet_or_user_confirmed_labels
```

Option decision:

| Option | Verdict |
| --- | --- |
| `run_posterior_on_user_confirmed_rank70` | `reject` |
| `expand_full127_same_protocol_then_posterior` | `reject_as_direct_posterior_path` |
| `expand_full127_same_protocol_for_diagnostics` | `diagnostic_only` |
| `revise_sampling_protocol_before_next_labels` | `select` |

Revised priority batch:

| Axis | Counts |
| --- | --- |
| `queue_kind` | `HL:80`, `LH:80` |
| `geometry_status` | `unsatisfied:80`, `satisfied:80` |
| `predicate_family` | `support_contact:96`, `relative_vertical:64` |
| `label_match_status` | `exact_match:25`, `family_match:33`, `no_gt_for_pair:50`, `pair_has_other_predicate:52` |

해석:

- 70-row user-confirmed target은 provenance가 해결됐지만 strict/construction slice가 없다.
- 이전 full-127 proxy target도 strict slice가 없었다.
- 따라서 현재 blocker는 label 수만의 문제가 아니라 hidden prior/role carryover다.
- priority160 revised sheet는 HL/LH와 satisfied/unsatisfied를 80/80으로 맞춰 기존 70-row의
  편향을 직접 줄인다.
- posterior smoke는 계속 blocked이며, priority160 label lock 이후 다시 target-independence
  audit을 수행해야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/116_full_train_independent_support_vertical_v2_sampling_protocol_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_sampling_protocol_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_sheet_priority160.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_manifest_priority160_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_sheet_all_label_ready.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_manifest_all_label_ready_post_label_only.jsonl
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Fill Update

2026-06-19에 `fill_revised_sampling_priority160_sheet_or_user_confirmed_labels` TODO를
진행했다. revised priority160 sheet를 user-confirmed workflow label로 채웠다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
```

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_priority160_filled_user_confirmed
rows = 160
reliable = 20
unreliable = 102
uncertain = 38
errors = 0
validation_used = False
test_used = False
next = revised_sampling_priority160_label_ingestion
```

해석:

- priority160 sheet는 모두 채워졌고 fill validation error는 0이다.
- fill은 hidden sampling axes, source rank/score, `p_geom_valid`, previous proxy labels를 쓰지
  않도록 boundary를 기록했다.
- 결과 분포는 reliable 20, unreliable 102, uncertain 38로 불균형하다.
- 이 분포가 hidden queue/role/rank/family axis와 연결되는지는 ingestion 후 target-independence
  audit에서 확인해야 한다.
- posterior smoke는 계속 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/117_full_train_independent_support_vertical_v2_revised_sampling_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/completed_revised_sampling_sheet_priority160_user_confirmed.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_priority160_user_confirmed/revised_sampling_priority160_user_confirmed_labels.jsonl
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Ingestion/Audit Update

2026-06-19에 `revised_sampling_priority160_label_ingestion` TODO를 진행했다. completed
priority160 sheet를 post-label-only manifest와 join하고, target-independence audit까지
수행했다.

실행:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
```

Ingestion result:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_ingested_with_basic_probe_risk
labels = 160
geometry target = 122 rows, 95 positive, 27 negative, 38 excluded
relation target = 122 rows, 20 positive, 102 negative, 38 excluded
errors = 0
validation_used = False
test_used = False
next = revised_sampling_priority160_target_independence_audit
```

Target-independence audit result:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_blocked
relation_rows = 122
relation_pos = 20
relation_neg = 102
errors = 0
relation_strict = none
relation_construction = none
validation_used = False
test_used = False
next = revise_sampling_or_expand_revised_sampling_labels
```

해석:

- revised sampling은 previous proxy label carryover를 줄였지만, target-independence를 열지는
  못했다.
- relation reliability target은 20/102로 negative-heavy이며, strict slice와 construction-only
  slice가 모두 없다.
- 주요 risk는 `proposed_audit_role_hidden`, `rank_band_hidden`, `queue_kind_hidden`,
  `geometry_status_hidden`, 그리고 visible `predicate_label` shortcut이다.
- 따라서 현재 blocker는 posterior combiner가 아니라 target construction / sampling /
  label balance 문제다.
- 이 상태에서 posterior smoke를 수행하면 factorized reliability posterior가 아니라
  predicate/role/rank/queue shortcut을 맞추는 실험이 될 위험이 크다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/118_full_train_independent_support_vertical_v2_revised_sampling_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/119_full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_priority160_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_priority160_user_confirmed/summary.json
```

## Full-Train Independent Support/Vertical V2 All-Label-Ready Expansion Update

2026-06-19에 `revise_sampling_or_expand_revised_sampling_labels` TODO를 진행했다.
priority160이 relation-positive coverage 부족으로 막혔기 때문에, 기존 revised sampling protocol이
이미 생성한 all-label-ready 302개 후보를 모두 user-confirmed workflow labels로 확장했다.

결과:

```text
fill:
rows = 302
reliable = 70
unreliable = 161
uncertain = 71
errors = 0

ingestion:
labels = 302
geometry target = 231 rows, 198 positive, 33 negative
relation target = 231 rows, 70 positive, 161 negative
errors = 0

target-independence audit:
status = full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_relation_strict_slice_ready
relation_strict = rank_band_balanced_revised_sampling
strict rows = 134
strict pos/neg = 67/67
validation_used = False
test_used = False
next = revised_sampling_all_label_ready_source_feature_join
```

해석:

- priority160 failure는 posterior combiner 문제가 아니라 relation-positive coverage 부족 문제로
  보는 것이 맞다.
- all-label-ready expansion은 relation reliability target positive를 20에서 70으로 늘렸다.
- `rank_band_balanced_revised_sampling` strict relation slice가 134 rows / 67 positive /
  67 negative로 열렸다.
- 이 strict slice의 harmful prior, construction, expected geometry alignment, visible
  non-target risk count는 모두 0으로 보고되었다.
- 따라서 현재 H002는 처음으로 controlled posterior smoke를 준비할 수 있는 target/evidence
  contract에 도달했다.
- 다음 단계는 posterior를 바로 돌리는 것이 아니라, strict slice에 source semantic /
  geometry / coverage evidence를 join하고 forbidden fields를 제거한 posterior-ready table을
  만드는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/120_full_train_independent_support_vertical_v2_all_label_ready_expansion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_fill_all_label_ready_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_ingestion_all_label_ready_user_confirmed/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed/summary.json
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Source Feature Join Update

2026-06-19에 `revised_sampling_all_label_ready_source_feature_join` TODO를 진행했다.
strict relation slice `rank_band_balanced_revised_sampling`에 source semantic score/rank,
geometry evidence, coverage fields를 join하고 posterior-ready table을 생성했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_source_feature_join_ready
rows = 134
positive = 67
negative = 67
candidate_matches = 134
feature_leakage_hits = 0
validation_errors = 0
validation_used = False
test_used = False
next = revised_sampling_all_label_ready_controlled_posterior_smoke
```

Input contract:

- model input root는 `baseline_inputs`만 허용한다.
- review fields, target labels, hidden audit metadata, packet paths, multi-view evidence는 model input이 아니다.
- predicate label/family categorical shortcut도 input에서 제외했다.
- main views는 `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
  `semantic_geometry_coverage`, `factorized_reliability_posterior`다.

해석:

- H002는 controlled posterior smoke를 실행할 수 있는 posterior-ready artifact를 처음으로 확보했다.
- 아직 posterior를 학습하지 않았고, 결과 claim도 없다.
- 다음 단계의 smoke 결과도 train-only hypothesis diagnostic으로 제한해야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/121_full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/posterior_ready_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/input_contract.json
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Controlled Posterior Smoke Update

2026-06-19에 `revised_sampling_all_label_ready_controlled_posterior_smoke` TODO를 진행했다.
posterior-ready strict slice `rank_band_balanced_revised_sampling`에서 semantic-only,
geometry-only, semantic+geometry, factorized posterior를 train-only grouped-by-scan smoke로 비교했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_no_strong_signal
rows = 134
positive = 67
negative = 67
validation_used = False
test_used = False
d_auprc_factorized_vs_semantic_plus_geometry = -0.0058
d_auprc_factorized_vs_semantic_geometry_coverage = -0.0058
d_auprc_factorized_vs_semantic_only = -0.0150
d_auprc_factorized_vs_geometry_only = +0.0291
next = revised_sampling_all_label_ready_controlled_error_analysis
```

Grouped main metrics:

| View | AUROC | AUPRC | Brier | ECE-5 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3476 | 0.4574 | 0.3148 | 0.2310 |
| `geometry_only` | 0.3587 | 0.4132 | 0.3018 | 0.2104 |
| `semantic_plus_geometry` | 0.3881 | 0.4481 | 0.3098 | 0.2283 |
| `semantic_geometry_coverage` | 0.3881 | 0.4481 | 0.3098 | 0.2283 |
| `factorized_reliability_posterior` | 0.3858 | 0.4424 | 0.3157 | 0.1999 |

해석:

- target/evidence contract는 통과했지만, factorized posterior 자체는 강한 양성 신호를 보이지 않았다.
- factorized는 geometry-only보다 AUPRC가 높지만 semantic+geometry보다 낮다.
- ECE는 factorized가 낮지만 ranking과 Brier가 같이 좋아진 것은 아니다.
- 따라서 현재 blocker는 더 이상 target-independence가 아니라 feature/target/combiner failure
  원인 분석이다.
- 이 결과는 H002를 기각하는 것이 아니라, factorized 요소의 결합 방식 또는 feature definition이
  아직 현재 target을 설명하지 못한다는 evidence다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/122_full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready/comparisons.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Controlled Error Analysis Update

2026-06-19에 `revised_sampling_all_label_ready_controlled_error_analysis` TODO를 진행했다.
목적은 posterior smoke의 `no_strong_signal` 원인이 target, feature, combiner, family
heterogeneity 중 어디에 가까운지 분해하는 것이었다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis_ready_feature_family_misalignment
rows = 134
positive = 67
negative = 67
validation_used = False
test_used = False
d_auprc_factorized_vs_semantic_plus_geometry = -0.0058
d_brier_factorized_vs_semantic_plus_geometry = +0.0058
factorized_fixes_semantic_plus_geometry_errors = 5
factorized_adds_errors = 9
next = revised_sampling_all_label_ready_factor_definition_repair_plan
```

Family-level diagnosis:

| Family | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 99 | 50 | 49 | +0.0023 | +0.0044 | +2 |
| `relative_vertical` | 35 | 17 | 18 | -0.0813 | +0.0100 | +2 |

Quadrant-level diagnosis:

| Quadrant | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `LH_low_semantic_high_geometry` | 84 | 45 | 39 | -0.0201 | -0.0005 | +5 |
| `HH_high_semantic_high_geometry` | 22 | 12 | 10 | -0.0024 | +0.0060 | +1 |
| `LL_low_semantic_low_geometry` | 20 | 5 | 15 | -0.0001 | +0.0536 | 0 |
| `HL_high_semantic_low_geometry` | 8 | 5 | 3 | -0.0300 | -0.0477 | -2 |

진단:

- factorized posterior는 `semantic_plus_geometry`에 안정적 추가 신호를 주지 못했다.
- coverage factor는 all-label-ready strict slice에서 거의 상수처럼 동작한다.
- threshold 기준으로 factorized는 5개를 고치지만 9개의 새 오류를 만든다.
- `relative_vertical`은 factorized 후 ranking 신호가 크게 손상된다.
- `support_contact`는 AUPRC가 아주 조금 좋아지지만 Brier가 악화된다.
- 두 relation family의 효과 방향이 다르다.

현재 판단:

```text
semantic score != geometry validity != relation reliability
```

라는 H002의 문제 정의는 유지된다. 다만 현재 evidence는 "더 복잡한 posterior
combiner가 필요하다"가 아니라, posterior에 들어가는 factor definition이 아직
family-local reliability evidence로 정렬되지 않았다는 쪽을 지지한다.

따라서 다음 단계에서는 SOTA급 high-capacity combiner를 바로 가져오기보다,
`support_contact`와 `relative_vertical`에 대해 typed residual normalization,
family-local `p_geom_valid`, disagreement/underconfidence/overconfidence의 의미 정렬을
먼저 설계해야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/123_full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready/transfer_summary.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Factor Definition Repair Plan Update

2026-06-20 KST에 `revised_sampling_all_label_ready_factor_definition_repair_plan` TODO를 진행했다.
이 단계는 모델을 새로 학습하는 것이 아니라, controlled error analysis에서 확인한
`feature_family_misalignment`를 바탕으로 다음 feature contract를 고정하는 단계다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_ready
rows = 134
validation_used = False
test_used = False
changes_feature_contract = True
changes_combiner = False
raw_fields = 14
d_auprc_factorized_vs_semantic_plus_geometry = -0.0058
next = revised_sampling_all_label_ready_raw_witness_feature_join_v2
```

핵심 판단:

```text
p_geom_valid is geometry-only evidence, not relation reliability.
```

따라서 `p_geom_valid`를 폐기하지 않고 역할을 낮춘다.

- `p_geom_valid`: legacy geometry-only baseline 및 auxiliary scalar.
- raw witness residual: 다음 main geometry evidence.
- predicate family: free categorical shortcut이 아니라 deterministic typed witness router.
- posterior combiner: raw witness v2 smoke 전까지 high-capacity model로 확장하지 않음.

Repair factor contract:

| Factor | Scope | Role |
| --- | --- | --- |
| `FD0_typed_relation_router` | all | predicate를 relation-specific witness template로 route한다. |
| `FD1_support_contact_raw_witness` | `support_contact` | contact gap, xy support overlap, support distance를 분리한다. |
| `FD2_relative_vertical_order_witness` | `relative_vertical` | higher/lower를 signed vertical order와 margin으로 표현한다. |
| `FD3_family_local_normalization` | support/vertical | raw residual을 family 내부 scale로 normalize한다. |
| `FD4_uncertainty_and_boundary_evidence` | all | boundary/ambiguous geometry와 strong support/contradiction을 분리한다. |
| `FD5_optional_endpoint_type_ablation` | `support_contact` | endpoint type이 shortcut인지 ablation으로만 점검한다. |

확인된 raw witness fields:

```text
center_delta_z
distance_3d
distance_xy
normalized_center_delta_z
normalized_distance_3d
normalized_distance_xy
object_bottom_z
object_top_z
projected_iou_xy
projected_object_overlap_ratio
projected_subject_overlap_ratio
subject_bottom_z
subject_top_z
vertical_gap_subject_on_object
```

다음 smoke 비교군:

- `semantic_only`
- `legacy_geometry_only`
- `semantic_plus_geometry`
- `raw_witness_only_v2`
- `semantic_plus_raw_witness_v2`
- `factorized_reliability_posterior_v2_linear`
- `factorized_reliability_posterior_v2_family_shrinkage`
- `endpoint_type_ablation`

필수 controls:

- `raw_witness_shuffle_global`
- `raw_witness_shuffle_within_family`
- `wrong_pair_raw_witness`
- `family_only_offset`
- `no_family_local_normalization`
- `legacy_p_geom_only`

해석:

- H002의 문제 정의인 `semantic score != geometry validity != relation reliability`는 유지된다.
- 다만 현재 실패 원인은 relation reliability posterior 자체의 부재가 아니라, posterior에 넣는
  geometry evidence가 `p_geom_valid` scalar로 너무 많이 접혀 있다는 점이다.
- 따라서 다음 단계는 combiner를 SOTA급으로 바꾸는 것이 아니라, raw witness feature join v2를 통해
  relation-specific geometry evidence를 복원하는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/124_full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/input_contract_v2.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/next_smoke_plan.json
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness Feature Join V2 Update

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_feature_join_v2` TODO를 진행했다.
목적은 all-label-ready posterior rows에 `match_rows.geometry.raw_features`를
`prediction_id` 기준으로 join하고, 다음 posterior smoke가 사용할 typed raw-witness
views와 controls를 실제 `baseline_inputs`로 만드는 것이다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready
rows = 134
positive = 67
negative = 67
raw_matches = 134 / 134
validation_errors = 0
feature_leakage_hits = 0
validation_used = False
test_used = False
next = revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke
```

Raw witness join:

| Item | Count |
| --- | ---: |
| requested prediction ids | 134 |
| matched prediction ids | 134 |
| match rows scanned until complete | 3,978,876 |
| raw fields | 14 |

Main views:

- `semantic_only`
- `legacy_geometry_only`
- `semantic_plus_geometry`
- `raw_witness_only_v2`
- `semantic_plus_raw_witness_v2`
- `factorized_reliability_posterior_v2_linear`
- `factorized_reliability_posterior_v2_family_shrinkage`
- `endpoint_type_ablation`

Control views:

- `raw_witness_shuffle_global`
- `raw_witness_shuffle_within_family`
- `wrong_pair_raw_witness`
- `family_only_offset`
- `no_family_local_normalization`
- `legacy_p_geom_only`

해석:

- H002는 이제 `p_geom_valid` scalar와 typed raw witness evidence를 명시적으로 분리해 비교할 수 있다.
- `p_geom_valid`는 legacy geometry evidence로 남고, v2 posterior의 main geometry input은
  support/vertical typed raw witness block이 된다.
- 이 artifact는 feature contract readiness이지 posterior improvement evidence가 아니다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/125_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/input_contract_v2.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/posterior_ready_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/feature_ranges.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/family_local_stats.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Posterior Smoke Update

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke`
TODO를 진행했다. 이 단계는 `p_geom_valid` scalar만 쓰던 이전 posterior가 실패한 뒤,
typed relation-specific raw witness evidence를 실제 posterior input으로 넣었을 때
H002 가설이 살아나는지 보는 train-only grouped smoke다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_positive_smoke
rows = 134
positive = 67
negative = 67
validation_used = False
test_used = False
d_auprc_shrinkage_vs_semantic_plus_geometry = +0.1622
d_auroc_shrinkage_vs_semantic_plus_geometry = +0.2350
d_brier_shrinkage_vs_semantic_plus_geometry = -0.0115
d_auprc_raw_witness_only_v2_vs_legacy_geometry_only = +0.1955
d_auprc_shrinkage_vs_global_shuffle = +0.1205
d_auprc_shrinkage_vs_wrong_pair = +0.1708
next = revised_sampling_all_label_ready_raw_witness_v2_error_analysis
```

Grouped main metrics:

| View | AUROC | AUPRC | Brier | Accuracy@0.5 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3476 | 0.4574 | 0.3148 | 0.3731 |
| `legacy_geometry_only` | 0.3587 | 0.4132 | 0.3018 | 0.3955 |
| `semantic_plus_geometry` | 0.3881 | 0.4481 | 0.3098 | 0.4179 |
| `raw_witness_only_v2` | 0.6191 | 0.6087 | 0.2990 | 0.5746 |
| `semantic_plus_raw_witness_v2` | 0.6115 | 0.6222 | 0.3087 | 0.5597 |
| `factorized_reliability_posterior_v2_linear` | 0.6293 | 0.6246 | 0.2966 | 0.5821 |
| `factorized_reliability_posterior_v2_family_shrinkage` | 0.6231 | 0.6103 | 0.2983 | 0.6269 |

해석:

- 이전 실패 원인은 `factorized posterior`라는 framing 자체라기보다, posterior에 들어간
  geometry evidence가 `p_geom_valid` scalar로 너무 압축되어 있었던 문제일 가능성이 커졌다.
- `raw_witness_only_v2`가 `legacy_geometry_only`보다 크게 좋아졌으므로, H002의 geometry axis는
  relation-specific raw witness residual을 가져야 한다.
- raw-witness global shuffle, within-family shuffle, wrong-pair control이 true raw-witness posterior보다
  낮게 나와서 단순 family/row shortcut만으로는 gain을 설명하기 어렵다.
- 다만 `factorized_reliability_posterior_v2_family_shrinkage`는 `linear`보다 AUPRC/Brier에서
  약간 낮다. 따라서 현재 결론은 "typed raw witness evidence가 필요하다"이지,
  "family shrinkage 결합 방식이 최선이다"가 아니다.
- `support_contact`가 주된 positive signal이다. `relative_vertical`은 AUPRC가 소폭 개선되지만
  Brier가 악화되어 calibration 또는 target ambiguity 분석이 필요하다.

H002에 대한 의미:

```text
semantic score != p_geom_valid scalar != typed geometry witness != relation reliability
```

이 결과는 H002를 "더 복잡한 combiner" 문제가 아니라 "relation-specific evidence factor를
어떻게 구성하고 결합할 것인가" 문제로 다시 정렬한다. 다음 단계는 성능을 높이기 위한
무작정 SOTA combiner 도입이 아니라, error analysis를 통해 어떤 factor가 실제로 reliability를
설명했고 어디에서 실패했는지 확인하는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/126_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready/family_deltas.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Error Analysis Update

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_v2_error_analysis` TODO를
진행했다. 이 단계는 새 모델을 학습하지 않고, `126`의 grouped-by-scan prediction을
row/family/feature-slice 수준으로 분해했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_ready_support_driven_linear_gap
rows = 134
validation_used = False
test_used = False
d_auprc_family_shrinkage_vs_semantic_plus_geometry = +0.1622
d_brier_family_shrinkage_vs_semantic_plus_geometry = -0.0115
d_auprc_linear_v2_vs_semantic_plus_geometry = +0.1764
d_auprc_family_shrinkage_vs_linear_v2 = -0.0143
next = revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan
```

Diagnostic flags:

- `typed_raw_witness_v2_adds_stable_signal_over_semantic_plus_geometry`
- `raw_witness_controls_reduce_gain`
- `family_shrinkage_not_best_combiner_for_ranking_or_brier`
- `linear_v2_is_current_strongest_simple_posterior`
- `family_local_normalization_mainly_improves_calibration_not_ranking`
- `support_contact_drives_positive_signal`
- `relative_vertical_has_calibration_regression`
- `family_effect_is_heterogeneous`
- `endpoint_type_ablation_has_nontrivial_signal_and_needs_shortcut_control`

핵심 해석:

- `typed raw witness evidence`는 H002의 main geometry evidence axis로 유망하다.
- 하지만 positive signal은 주로 `support_contact`에서 나온다.
- `relative_vertical`은 AUPRC가 일부 좋아지지만 Brier/calibration이 악화된다.
- `linear_v2`가 `family_shrinkage`보다 AUPRC/Brier 기준으로 좋다.
- `family_shrinkage`는 threshold transfer 측면에서 error 추가가 적지만, final combiner로
  고정하기에는 근거가 부족하다.
- `endpoint_type_ablation`이 강한 signal을 보이므로 endpoint/object-type shortcut을 다음 smoke에서
  반드시 control해야 한다.

따라서 현재 H002의 더 정확한 중간 결론은 다음이다.

```text
typed raw witness evidence is necessary, but the posterior combiner and
shortcut controls are not settled.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/127_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/transfer_vs_semantic_plus_geometry.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready/transfer_vs_primary.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Repair Plan Update

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan`
TODO를 진행했다. 이 단계는 새 모델을 학습하지 않고, 다음 combiner smoke의 후보,
controls, success gate를 고정했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_ready
rows = 134
validation_used = False
candidate_count = 9
control_count = 7
d_auprc_linear_v2_vs_semantic_plus_geometry = +0.1764
d_auprc_family_shrinkage_vs_linear_v2 = -0.0143
next = revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke
```

Combiner candidates:

| ID | Role | Decision |
| --- | --- | --- |
| `C0_semantic_plus_geometry_legacy` | legacy reference | keep |
| `C1_raw_witness_only_v2` | geometry evidence reference | keep |
| `C2_semantic_plus_raw_witness_v2` | semantic/raw reference | keep |
| `C3_linear_v2` | current strongest simple reference | next primary reference |
| `C4_calibrated_linear_v2` | calibration repair | test next |
| `C5_constrained_monotonic_additive` | principled low-capacity combiner | test next |
| `C6_family_gated_calibrated_mixture` | family heterogeneity repair | test next |
| `C7_limited_interaction_model` | upper-bound candidate | test after C4-C6 |
| `C8_endpoint_type_ablation_only` | shortcut probe | ablation only |

Required controls:

- global raw-witness shuffle.
- within-family raw-witness shuffle.
- wrong-pair raw witness.
- family-only offset.
- no family-local normalization.
- endpoint type only / endpoint ablation.
- support-only and vertical-only family split.

Success gate:

```text
reference = C3_linear_v2
new primary must satisfy:
  delta_auprc_vs_linear >= 0
  delta_brier_vs_linear <= 0
  delta_ece_vs_linear <= 0
  new_errors_minus_fixes_vs_linear <= 0
```

Fallback:

```text
If a candidate ties linear within 0.01 AUPRC and improves Brier/ECE or threshold
transfer, it can be treated as calibration/threshold repair, not ranking improvement.
```

해석:

- 다음 smoke의 질문은 더 이상 "raw witness가 old semantic+geometry를 이기는가"가 아니다.
- 이제 질문은 "raw witness 기반 posterior가 `linear_v2`를 이기거나 calibration/threshold를
  개선하는가"다.
- endpoint type은 유용하지만 shortcut 가능성이 크므로 main evidence가 아니라 ablation/control로만 둔다.
- `relative_vertical` Brier regression이 해결되지 않으면 vertical은 별도 unresolved calibration slice로
  남긴다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/128_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/combiner_candidates.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/control_matrix.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/success_gates.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/next_smoke_plan.json
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Smoke

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke`
TODO를 진행했다. 이 단계는 validation/test를 사용하지 않고, full-train
all-label-ready 134-row support/vertical slice에서 C0-C8 combiner 후보와 K0-K5
shortcut/control 후보를 grouped-by-scan 방식으로 비교했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_no_new_primary
rows = 134
positive = 67
negative = 67
validation_used = False
best_candidate = C4_calibrated_linear_v2
best_delta_auprc_vs_C3_linear_v2 = -0.0139
primary_passes = 0
fallback_passes = 0
next = revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis
```

Grouped split 기준 주요 결과:

| View | AUROC | AUPRC | Brier | ECE | Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| `C0_semantic_plus_geometry_legacy` | 0.3881 | 0.4481 | 0.3098 | 0.2283 | 0.4179 |
| `C1_raw_witness_only_v2` | 0.6191 | 0.6087 | 0.2990 | 0.2238 | 0.5746 |
| `C2_semantic_plus_raw_witness_v2` | 0.6115 | 0.6222 | 0.3087 | 0.2705 | 0.5597 |
| `C3_linear_v2` | 0.6293 | 0.6246 | 0.2966 | 0.2335 | 0.5821 |
| `C4_calibrated_linear_v2` | 0.5471 | 0.6107 | 0.2879 | 0.2161 | 0.5149 |
| `C5_constrained_monotonic_additive` | 0.4676 | 0.5477 | 0.3105 | 0.2697 | 0.4552 |
| `C6_family_gated_calibrated_mixture` | 0.5636 | 0.5720 | 0.3037 | 0.2234 | 0.5672 |
| `C7_limited_interaction_model` | 0.5727 | 0.5757 | 0.3112 | 0.2480 | 0.5522 |
| `C8_endpoint_type_ablation_only` | 0.8291 | 0.7935 | 0.1731 | 0.1011 | 0.7761 |

핵심 해석:

- C4-C7 중 C3 `linear_v2`를 primary 또는 fallback gate로 대체한 후보는 없다.
- C4는 Brier/ECE를 개선하지만 AUPRC와 threshold transfer에서 C3보다 약하다.
- C6/C7은 `relative_vertical` 일부를 개선하지만 `support_contact` 손실이 커서
  shared combiner로 고정하기 어렵다.
- `K5_endpoint_type_only`가 AUROC 0.9581 / AUPRC 0.9369로 모든 combiner를 압도해,
  현재 target slice에 endpoint/object-type shortcut 위험이 매우 크다.
- 다만 C3는 global/within-family shuffle, wrong-pair raw witness, family-only
  offset control보다 높으므로 pair-specific raw witness evidence 자체는 여전히
  의미가 있다.

현재 결론:

```text
Changing the combiner alone is not sufficient. H002 should next explain whether
the blocker is target shortcut, endpoint leakage, family-specific evidence
heterogeneity, or calibration-only gain without ranking improvement.
```

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/129_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/family_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready/gate_evaluation.csv
```

## Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness V2 Combiner Error Analysis

2026-06-20 KST에 `revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis`
TODO를 진행했다. 이 단계는 새 posterior model을 학습하지 않고, 129번 combiner smoke의
grouped prediction을 post-hoc으로 분석했다.

결과:

```text
status = full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_ready_endpoint_control_needed
rows = 134
positive = 67
negative = 67
endpoint_d_auprc_vs_c3 = +0.3124
endpoint_new_errors_minus_fixes = -38
endpoint_shortcut_severity = severe
next = revised_sampling_all_label_ready_endpoint_controlled_resampling_plan
```

핵심 진단:

- C4-C7은 `C3_linear_v2`를 대체하지 못한다.
- C4는 `support_contact`를 일부 개선하지만 `relative_vertical`을 크게 손상한다.
- C6/C7은 `relative_vertical`에는 도움이 되지만 `support_contact`를 손상한다.
- pair-specific raw witness는 global shuffle / wrong-pair control 대비 여전히 의미가 있다.
- 그러나 `K5_endpoint_type_only`가 C3보다 훨씬 강하다.
- 따라서 현재 primary blocker는 posterior combiner capacity가 아니라 endpoint/object-type shortcut이다.

Endpoint shortcut 결과:

| Control | dAUROC vs C3 | dAUPRC vs C3 | dBrier vs C3 | dECE vs C3 | dAcc vs C3 | Fixes C3 | Adds Error | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `K5_endpoint_type_only` | +0.3288 | +0.3124 | -0.2088 | -0.1181 | +0.2836 | 44 | 6 | -38 |

Shortcut indicators:

```text
endpoint_flag_rows_in_pure_groups = 100 / 134
endpoint_label_rows_in_pure_groups_min2 = 67 / 134
```

Candidate transfer vs C3:

| Candidate | Fixes C3 | Adds Error | New-Fix | dAUPRC | dBrier | dECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C4_calibrated_linear_v2` | 16 | 25 | +9 | -0.0139 | -0.0087 | -0.0173 |
| `C5_constrained_monotonic_additive` | 8 | 25 | +17 | -0.0769 | +0.0139 | +0.0362 |
| `C6_family_gated_calibrated_mixture` | 8 | 10 | +2 | -0.0526 | +0.0071 | -0.0101 |
| `C7_limited_interaction_model` | 7 | 11 | +4 | -0.0488 | +0.0146 | +0.0146 |

Decision:

```text
Do not pursue a higher-capacity or family-separated posterior as the immediate
next step. Build endpoint-controlled resampling first, then retest whether C3
still remains the bottleneck.
```

현재 해석:

- H002는 여전히 `semantic score != geometry validity != relation reliability`라는
  문제 정의를 유지한다.
- 하지만 현재 134-row support/vertical target slice에서는 relation reliability보다
  endpoint/object-type pattern이 label을 과도하게 설명한다.
- 따라서 다음 원리적 작업은 combiner를 바꾸는 것이 아니라, target construction에서
  endpoint shortcut을 낮추는 것이다.
- endpoint-controlled slice가 만들어진 뒤에도 C3가 막히면 그때 family-separated posterior,
  stronger calibrated combiner, 또는 multi-view audit evidence를 검토한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/130_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/row_diagnostics.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/candidate_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/family_tradeoff.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/endpoint_flag_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/endpoint_label_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/feature_target_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/representative_rows.jsonl
```

## Endpoint-Controlled Resampling Plan

2026-06-20 KST에 `revised_sampling_all_label_ready_endpoint_controlled_resampling_plan`
TODO를 진행했다. 이 단계는 새 posterior model을 학습하지 않고, endpoint/object-type
shortcut을 줄이는 resampling protocol의 feasibility를 확인했다.

결과:

```text
status = h002_endpoint_controlled_resampling_plan_ready_needs_label_expansion
rows = 134
positive = 67
negative = 67
strict_endpoint_seed_rows = 24
relaxed_object_role_seed_rows = 44
strict_endpoint_d_auprc_vs_c3 = -0.0112
relaxed_object_role_d_auprc_vs_c3 = +0.0780
needed_positive_labels_to_cap = 36
needed_negative_labels_to_cap = 26
next = revised_sampling_endpoint_controlled_candidate_mining
```

Protocol comparison:

| Protocol | Matching Keys | Rows | Endpoint dAUPRC vs C3 | Interpretation |
| --- | --- | ---: | ---: | --- |
| `P0_current_all` | none | 134 | +0.3167 | shortcut-dominated |
| `P3_object_role` | `object_role` | 44 | +0.0780 | relaxed diagnostic only |
| `P5_family_object_subject_role` | `predicate_family + object_role + subject_role` | 24 | -0.0112 | shortcut reduced, too small |
| `P7_strict_endpoint_flag` | `endpoint_flag_pattern` | 24 | -0.0112 | primary protocol, needs expansion |
| `P9_endpoint_label_pattern` | `subject + predicate + object` | 0 | nan | too strict |

Recommended matching key:

```text
endpoint_flag_pattern =
  endpoint_object_floor_like_flag
  endpoint_object_support_surface_like_flag
  endpoint_object_wall_like_flag
  endpoint_subject_room_surface_flag
  relative_vertical_gate
  support_contact_gate
```

Decision:

```text
The current all-label-ready pool is not sufficient for endpoint-controlled posterior
smoke. Use strict endpoint_flag_pattern matching as the primary resampling protocol,
then mine additional candidates for missing positive/negative labels per endpoint key.
```

해석:

- endpoint shortcut을 원리적으로 줄이려면 exact endpoint flag 안에서 positive/negative를 맞춰야 한다.
- 현재 pool에서 이 조건을 걸면 24 rows만 남아 posterior smoke에는 부족하다.
- relaxed object-role control은 row 수를 44로 늘리지만 endpoint-only signal이 여전히 남는다.
- exact subject/object label matching은 너무 엄격해 balanced row가 0이다.
- 따라서 다음 단계는 stronger combiner가 아니라 endpoint-key별 missing opposite-label candidate mining이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/131_endpoint_controlled_resampling_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_resampling_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/protocol_candidates.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/endpoint_key_groups.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/endpoint_label_deficits.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/strict_endpoint_seed_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_resampling_plan_all_label_ready/relaxed_object_role_seed_rows.jsonl
```

## Endpoint-Controlled Candidate Mining

2026-06-20 KST에 `revised_sampling_endpoint_controlled_candidate_mining` TODO를
진행했다. 이 단계는 새 posterior model을 학습하지 않고, strict
`endpoint_flag_pattern` resampling에 필요한 부족 label 후보를 train split에서만
mining했다.

결과:

```text
status = h002_endpoint_controlled_candidate_mining_ready_needs_asset_packets
requested_deficit_labels = 62
selected_total = 62
selected_packet_ready = 53
selected_asset_needed = 9
residual_unfilled = 0
next = endpoint_controlled_asset_packet_generation
```

선택된 후보의 label 방향:

| Source | Positive proxy | Negative proxy | Total |
| --- | ---: | ---: | ---: |
| packet-ready | 32 | 21 | 53 |
| asset-needed | 4 | 5 | 9 |
| total | 36 | 26 | 62 |

해석:

- 12개 endpoint deficit group의 residual은 모두 0으로 줄일 수 있다.
- 즉, endpoint-controlled target repair는 데이터 측면에서 feasible하다.
- 하지만 9개 후보는 기존 audit packet이 없으므로, label fill 전에 asset packet
  generation이 필요하다.
- 따라서 다음 단계는 posterior 결합 방식 변경이 아니라, `9` asset-needed 후보의
  packet 생성과 `53 + 9` label batch 구성이다.
- Endpoint fields는 계속 sampling/audit control일 뿐이며, deployable posterior input으로
  승격하지 않는다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/132_endpoint_controlled_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/deficit_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/selected_all_candidates_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/endpoint_controlled_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_candidate_mining/asset_request_manifest.jsonl
```

## Endpoint-Controlled Asset Packets

2026-06-20 KST에 `endpoint_controlled_asset_packet_generation` TODO를 진행했다.
이 단계는 새 posterior model을 학습하지 않고, endpoint-controlled 후보 중 기존 packet이
없던 `9`개 row의 audit packet을 생성한 뒤 기존 packet-ready `53`개와 합쳐 full
`62`-row label sheet를 준비했다.

결과:

```text
status = h002_endpoint_controlled_asset_packets_ready
generated_packet_rows = 9
generated_non_ready_rows = 0
full_label_sheet_rows = 62
packet_status_counts = ready: 62
packet_path_errors = 0
label_surface_leakage = pass
next = endpoint_controlled_label_fill
```

구성:

| Source | Rows |
| --- | ---: |
| existing packet-ready candidates | 53 |
| newly generated asset-needed candidates | 9 |
| total label sheet rows | 62 |

Family count:

| Family | Rows |
| --- | ---: |
| `support_contact` | 37 |
| `relative_vertical` | 25 |

해석:

- endpoint-controlled target repair의 packet blocker는 제거됐다.
- full `62`-row label sheet가 packet-ready 상태가 되었고, packet path error는 0이다.
- label surface leakage audit도 pass다.
- 이 결과는 posterior 성능 증거가 아니라 label fill을 위한 evidence-readiness artifact다.
- 다음 단계는 `endpoint_controlled_label_fill`이며, 이후 ingestion과 target-independence
  audit이 끝나기 전까지 posterior smoke를 다시 돌리지 않는다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/133_endpoint_controlled_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_asset_packet_generation.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/endpoint_controlled_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/endpoint_controlled_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/asset_needed_manifest_with_packets_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_asset_packets/packets/
```

## Endpoint-Controlled Label Fill

2026-06-20 KST에 `endpoint_controlled_label_fill` TODO를 진행했다. 이 단계는
packet-ready `62`-row endpoint-controlled sheet를 Codex proxy로 채운 것이다.
Hidden endpoint/sampling manifest, score/rank, `p_geom_valid`, geometry status, numeric
witness values는 fill input으로 사용하지 않았다.

결과:

```text
status = h002_endpoint_controlled_label_fill_ready_for_ingestion
rows = 62
reliable = 2
unreliable = 32
uncertain = 28
validation_errors = 0
validation_used = False
test_used = False
next = endpoint_controlled_label_ingestion
```

Family count:

| Family | Rows |
| --- | ---: |
| `support_contact` | 37 |
| `relative_vertical` | 25 |

Geometry answer:

| Answer | Rows |
| --- | ---: |
| `supports_predicate` | 23 |
| `contradicts_predicate` | 11 |
| `uncertain` | 28 |

해석:

- Label fill 자체는 schema validation error 0으로 완료됐다.
- 하지만 `reliable=2/62`라서 binary positive target이 매우 부족하다.
- 따라서 이 결과는 posterior smoke를 여는 evidence가 아니라, ingestion과
  target-independence audit에서 target viability를 판단하기 위한 intermediate artifact다.
- 다음 ingestion에서 uncertain 처리 정책과 positive sparsity를 명시적으로 다뤄야 한다.
- Positive가 계속 2개뿐이면 현재 endpoint-controlled fill은 method-validation target이 아니라
  failure diagnosis로 봐야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/134_endpoint_controlled_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/completed_endpoint_controlled_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/endpoint_controlled_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
```

## Endpoint-Controlled Label Ingestion

2026-06-20 KST에 `endpoint_controlled_label_ingestion` TODO를 진행했다. 이 단계는
62개 endpoint-controlled Codex-proxy label을 target artifact로 ingest하고, label lock
이후 hidden endpoint manifest를 join해 geometry validity target과 relation
reliability target을 분리했다. Posterior는 학습하지 않았다.

결과:

```text
status = h002_endpoint_controlled_label_ingested_positive_sparse
labels = 62
geometry_validity_binary = 34
geometry_validity_positive_negative = 23/11
relation_reliability_binary = 34
relation_reliability_positive_negative = 2/32
ingestion_errors = 0
validation_used = False
test_used = False
next = endpoint_controlled_target_independence_audit
```

Target count:

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_endpoint_controlled_target` | 34 | 23 | 11 | 0.6765 | 28 |
| `relation_reliability_endpoint_controlled_target` | 34 | 2 | 32 | 0.0588 | 28 |

해석:

- 같은 binary slice에서 geometry validity는 `23/11`로 나뉘지만 relation reliability는
  `2/32`로 거의 전부 negative다.
- 따라서 H002의 핵심 주장인 `semantic score != geometry validity != relation
  reliability`가 target construction 관점에서도 유지된다.
- 특히 `geometry validity`가 높아도 relation이 informative하고 ontology-compatible하며
  annotation/audit 관점에서 reliable하다는 뜻은 아니다.
- 하지만 이 ingestion은 posterior 성능 증거가 아니다. Relation reliability target의
  positive가 너무 적어 현재 target으로 posterior smoke를 돌리면 target 편향 또는
  construction shortcut을 학습할 위험이 크다.
- 다음 단계는 `endpoint_controlled_target_independence_audit`이며, 이 audit 전까지
  posterior smoke는 계속 block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/135_endpoint_controlled_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/validated_endpoint_controlled_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/geometry_validity_endpoint_controlled_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/relation_reliability_endpoint_controlled_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_ingestion_codex_proxy_user_requested/shortcut_audit.csv
```

## Endpoint-Controlled Target Independence Audit

2026-06-20 KST에 `endpoint_controlled_target_independence_audit` TODO를 진행했다.
이 단계는 endpoint-controlled ingestion으로 생성한 target이 posterior smoke로 넘어갈 수
있는지 확인했다. Posterior는 학습하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_endpoint_controlled_target_independence_audit_blocked_positive_sparse
relation_rows = 34
relation_positive_negative = 2/32
relation_majority_baseline = 0.9412
validation_errors = 0
relation_strict_slice = none
relation_diagnostic_slice = none
validation_used = False
test_used = False
next = endpoint_controlled_target_path_decision
```

Per-target decision:

| Target | Status | Rows | Pos | Neg | Strict Slice | Diagnostic Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `geometry_validity_endpoint_controlled_target` | `blocked_no_controlled_slice` | 34 | 23 | 11 | `none` | `none` |
| `relation_reliability_endpoint_controlled_target` | `blocked_positive_sparse` | 34 | 2 | 32 | `none` | `none` |

해석:

- Endpoint-controlled resampling은 필요한 방향이었지만, 현재 label outcome은 posterior-ready
  target을 만들지 못했다.
- Relation reliability target은 `2/32`라서 negative-majority baseline만으로 `0.9412`가
  나온다.
- 이 상태에서 posterior smoke를 돌리면 factorized reliability 결합 방식을 검증하는 것이 아니라
  positive-sparse target과 construction artifact를 맞추는 실험이 된다.
- Geometry validity target은 `23/11`로 더 낫지만, 전체 row가 `34`개뿐이고 strict slice가
  없으므로 method evidence로 승격할 수 없다.
- 따라서 현재 blocker는 posterior combiner가 아니라 target construction / sampling /
  positive label coverage다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/136_endpoint_controlled_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/relation_reliability_endpoint_controlled_target_positive_rows.jsonl
```

## Endpoint-Controlled Target Path Decision

2026-06-20 KST에 `endpoint_controlled_target_path_decision` TODO를 진행했다. 이
단계는 endpoint-controlled audit 결과 이후 posterior smoke를 열지, combiner를 바꿀지,
target/sampling을 수정할지 결정했다.

결과:

```text
status = h002_endpoint_controlled_target_path_decision_revise_target_v3_positive_anchor_sampling
selected = revise_reliability_target_v3_and_positive_anchor_sampling
relation_reliability_positive_negative = 2/32
geometry_validity_positive_negative = 23/11
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_positive_anchor_plan
```

선택한 경로:

```text
revise_reliability_target_v3_and_positive_anchor_sampling
```

Option decision:

| Option | Verdict | Reason |
| --- | --- | --- |
| posterior smoke now | `reject` | relation reliability가 `2/32`이고 controlled slice가 없다. |
| combiner upgrade now | `reject` | blocker는 target construction과 positive coverage다. |
| geometry validity as main target | `reject_for_reliability_claim` | geometry validity는 relation reliability가 아니다. |
| same endpoint labels more | `defer` | 현재 positive rate로 20 positives를 얻으려면 약 306 additional rows가 필요하다. |
| reliability = geometry-supported | `reject_as_shortcut` | H002의 핵심 구분을 없앤다. |
| target v3 + positive-anchor sampling | `select` | sparse positive와 mixed failure reason을 직접 다룬다. |
| multi-view model input now | `reject_now` | clean target 전에는 feature gain과 shortcut이 분리되지 않는다. |

해석:

- 현재 결과는 semantic-geometry 정합이 좋다는 뜻이 아니다.
- 현재 binary relation reliability target이 uncertain, trivial dense relation,
  ontology mismatch, geometry contradiction을 모두 negative로 접으면서 reliable positive가
  거의 사라졌다는 뜻이다.
- 따라서 posterior 결합 방식을 바꾸기 전에 target schema와 sampling을 바꿔야 한다.
- Geometry validity target은 `23/11`이라 diagnostic mass가 있지만, 이것을 main
  reliability target으로 쓰면 H002가 geometry-only verifier로 축소된다.

다음 target v3 방향:

| Axis | Values |
| --- | --- |
| `geometry_support` | `supports_predicate`, `contradicts_predicate`, `ambiguous`, `not_evaluable` |
| `relation_usefulness` | `informative`, `trivial_dense_or_room_structure`, `ontology_mismatch`, `uncertain` |
| `relation_reliability` | `reliable`, `unreliable_geometry`, `unreliable_trivial`, `unreliable_ontology`, `uncertain` |

Binary posterior target은 각 axis에 충분한 label mass가 생긴 뒤에만 derive한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/137_endpoint_controlled_target_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/target_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/v3_positive_anchor_plan.json
```

## Reliability Target V3 Positive-Anchor Plan

2026-06-20 KST에 `reliability_target_v3_positive_anchor_plan` TODO를 진행했다. 이
단계는 posterior smoke가 아니라, relation reliability target을 다시 만들기 위한 v3
multi-axis label schema와 160-row train-only positive-anchor sheet를 생성한 단계다.

결과:

```text
status = h002_reliability_target_v3_positive_anchor_plan_ready
selected_rows = 160
label_surface_leakage_hits = 0
packet_path_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_fill
```

선택한 4개 bucket:

| Bucket | Rows | Support | Vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: |
| `reliable_positive_anchor` | 40 | 20 | 20 | 32 |
| `geometry_contradiction_negative` | 40 | 20 | 20 | 31 |
| `trivial_dense_negative` | 40 | 20 | 20 | 21 |
| `ontology_or_uncertain_negative` | 40 | 30 | 10 | 21 |

V3 label axis:

| Axis | Values |
| --- | --- |
| `endpoint_identity_v3` | `both_valid`, `subject_invalid`, `object_invalid`, `pair_invalid`, `uncertain` |
| `pair_evaluability_v3` | `evaluable`, `partially_evaluable`, `not_evaluable`, `uncertain` |
| `geometry_support_v3` | `supports_predicate`, `contradicts_predicate`, `ambiguous`, `not_evaluable` |
| `relation_usefulness_v3` | `informative`, `trivial_dense_or_room_structure`, `ontology_mismatch`, `uncertain` |
| `relation_reliability_v3` | `reliable`, `unreliable_geometry`, `unreliable_trivial`, `unreliable_ontology`, `uncertain` |

해석:

- 이 단계는 `semantic score != geometry validity != relation reliability` 구분을
  target construction에 반영한다.
- Geometry가 satisfied라고 해서 relation reliability를 positive로 자동 처리하지 않는다.
- Reliable positive, geometry contradiction, trivial dense relation, ontology/granularity
  mismatch를 분리해서 posterior target 이전의 원인 label을 확보한다.
- Label sheet에는 score, rank, queue, `p_geom_valid`, `geometry_status`,
  `label_match_status`, expected role 같은 construction field를 노출하지 않았다.
- Posterior smoke는 아직 진행하지 않는다. V3 label fill, ingestion, target-independence
  audit 이후에만 binary 또는 multi-class reliability target을 derive한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/138_reliability_target_v3_positive_anchor_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_positive_anchor_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_positive_anchor_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_positive_anchor_plan/v3_positive_anchor_manifest_post_label_only.jsonl
```

## Reliability Target V3 Label Fill

2026-06-20 KST에 `reliability_target_v3_label_fill` TODO를 진행했다. 사용자가 직접 채워야
하는 단계로 두지 않고, 사용자 요청에 따라 Codex proxy로 160-row v3 sheet를 채웠다.

경계:

- Open3DSG train-only.
- Validation/test row 사용 없음.
- Posterior 학습 없음.
- 실제 독립 human annotation 아님.
- Label decision에는 labeler-visible identity field와 packet path availability만 사용.
- Hidden sampling category, expected role, source score/rank, `p_geom_valid`,
  `geometry_status`, `label_match_status`, numeric witness value는 label decision에 사용하지
  않음.
- Hidden manifest는 label fill 이후 diagnostic bucket count에만 조인.

결과:

```text
status = h002_reliability_target_v3_label_filled_codex_proxy_user_requested
rows = 160
reliable = 32
unreliable_geometry = 21
unreliable_trivial = 57
unreliable_ontology = 0
uncertain = 50
validation_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_ingestion
```

V3 axis count:

| Value | Count |
| --- | ---: |
| `geometry_support_v3=supports_predicate` | 92 |
| `geometry_support_v3=contradicts_predicate` | 21 |
| `geometry_support_v3=ambiguous` | 47 |
| `relation_usefulness_v3=informative` | 34 |
| `relation_usefulness_v3=trivial_dense_or_room_structure` | 58 |
| `relation_usefulness_v3=ontology_mismatch` | 21 |
| `relation_usefulness_v3=uncertain` | 47 |

Post-label hidden bucket diagnostic:

| Hidden Bucket | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `reliable_positive_anchor` | 40 | 7 | 0 | 8 | 25 |
| `geometry_contradiction_negative` | 40 | 1 | 18 | 14 | 7 |
| `trivial_dense_negative` | 40 | 10 | 3 | 19 | 8 |
| `ontology_or_uncertain_negative` | 40 | 14 | 0 | 16 | 10 |

해석:

- Positive-anchor sampling은 label coverage를 늘렸지만, hidden positive-anchor bucket이
  visible-heuristic proxy fill에서 자동으로 reliable positive가 되지는 않았다.
- 따라서 v3 label ingestion과 target-independence audit 없이 posterior smoke를 재개하면
  안 된다.
- 현재 산출물은 label completion artifact이며, paper-level human annotation evidence가
  아니다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/139_reliability_target_v3_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/completed_v3_positive_anchor_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/bucket_diagnostics_post_label_only.csv
```

## Reliability Target V3 Label Ingestion

2026-06-20 KST에 `reliability_target_v3_label_ingestion` TODO를 진행했다. 이 단계는
completed v3 sheet를 ingest하고, H002 target을 `relation reliability`, `geometry support`,
`relation usefulness`로 분리해 materialize한 단계다. Posterior는 학습하지 않았다.

결과:

```text
status = h002_reliability_target_v3_label_ingested_with_probe_risk
rows = 160
ingestion_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_target_independence_audit
```

Binary target count:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 110 | 32 | 78 | 0.2909 | 50 |
| `geometry_support_v3_binary_target` | 113 | 92 | 21 | 0.8142 | 47 |
| `relation_usefulness_v3_binary_target` | 113 | 34 | 79 | 0.3009 | 47 |

Multiclass reliability target:

| Class | Rows |
| --- | ---: |
| `reliable` | 32 |
| `unreliable_geometry` | 21 |
| `unreliable_trivial` | 57 |
| `unreliable_ontology` | 0 |
| `uncertain` | 50 |

Probe result:

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |

해석:

- Endpoint-controlled v2에서 문제가 됐던 positive-sparse target은 개선됐다.
- Relation reliability binary target은 `32/78`로, posterior smoke를 위한 최소 target mass는
  생겼다.
- 하지만 hidden metadata와 visible object-label shortcut이 여전히 강하다.
- 특히 `endpoint_flag_pattern_hidden`, `sampling_category_hidden`, `geometry_status_hidden`,
  `label_match_status_hidden`, `subject_label`, `object_label`이 target과 얽혀 있다.
- 따라서 posterior smoke를 바로 재개하면 factorized reliability를 검증하는 것이 아니라
  construction shortcut을 맞출 위험이 크다.
- 다음 단계는 dedicated target-independence audit이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/140_reliability_target_v3_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/validated_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
```

## Reliability Target V3 Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_target_independence_audit` TODO를 진행했다. 이
단계는 v3 target을 posterior에 넣기 전에 hidden bucket, endpoint flag, construction
field, subject/object label shortcut을 통제한 slice가 존재하는지 확인한 것이다.
Posterior는 학습하지 않았다.

결과:

```text
status = h002_reliability_target_v3_target_independence_audit_blocked_no_controlled_slice
relation_rows = 110
relation_pos = 32
relation_neg = 78
errors = 0
relation_strict = none
relation_diagnostic = none
validation_used = False
test_used = False
next = reliability_target_v3_path_decision
```

Target별 decision:

| Target | Status | Rows | Positive | Negative | Strict Slice | Diagnostic Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `relation_reliability_v3_binary_target` | `blocked_no_controlled_slice` | 110 | 32 | 78 | `none` | `none` |
| `geometry_support_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 92 | 21 | `none` | `none` |
| `relation_usefulness_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 34 | 79 | `none` | `none` |

Relation reliability target의 주요 shortcut risk:

| Risk | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| endpoint pattern | `endpoint_flag_pattern_hidden` | 0.9182 | 0.5978 | 1.0000 |
| object identity | `object_label` | 0.9545 | 0.8587 | 1.0000 |
| object identity | `subject_label` | 0.9091 | 0.7070 | 1.0000 |
| hidden provenance | `sampling_category_hidden` | 0.7091 | 0.1640 | 0.4364 |
| construction | `rank_band_hidden` | 0.7182 | 0.1680 | 0.6667 |
| geometry alignment | `geometry_status_hidden` | 0.7091 | 0.1499 | 0.3723 |

해석:

- v3 target은 positive-sparse 문제를 줄였지만 target independence를 확보하지 못했다.
- `sampling_category_balanced_v3`는 `64` rows `32/32`로 균형은 맞지만 endpoint,
  construction, subject/object label risk가 남는다.
- `rank_band_balanced_v3`도 `62` rows `31/31`로 균형은 맞지만 endpoint/object risk가
  남는다.
- endpoint/object-balanced slice는 너무 작거나 hidden/construction risk가 남는다.
- 따라서 다음 단계는 posterior smoke가 아니라 `reliability_target_v3_path_decision`이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/141_reliability_target_v3_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Reliability Target V3 Path Decision

2026-06-20 KST에 `reliability_target_v3_path_decision` TODO를 진행했다. 이 단계는
v3 target-independence audit 실패 이후 posterior smoke를 열지, combiner를 바꿀지, 아니면
target pool을 다시 설계할지 결정한 것이다.

결과:

```text
status = h002_reliability_target_v3_path_decision_object_endpoint_controlled_sampling_first
selected = revise_v3_object_endpoint_controlled_sampling
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_controlled_plan
```

선택:

```text
revise_v3_object_endpoint_controlled_sampling
```

판단:

- posterior smoke를 지금 실행하지 않는다.
- combiner upgrade도 지금 진행하지 않는다.
- `geometry_support_v3_binary_target`을 main reliability target으로 대체하지 않는다.
- 같은 v3 Codex-proxy label을 더 모으는 것도 main path가 아니다.
- v3 axis는 유지하되, 다음 label pool은 object/endpoint-controlled sampling으로 다시 만든다.

이유:

현재 relation reliability target은 `110` rows, `32/78` positive/negative로 positive mass는
있다. 하지만 strict/diagnostic controlled slice가 없고, `object_label`, `subject_label`,
`endpoint_flag_pattern_hidden`이 target을 강하게 설명한다. 이 상태에서 posterior 성능이
좋아져도, 그것이 semantic/geometry/coverage/uncertainty factor 결합 때문인지 object/endpoint
shortcut 때문인지 분리할 수 없다.

따라서 다음 단계는 더 강한 결합기가 아니라 target pool 통제다. Object label은 relation
reasoning에서 유효한 context지만, object label이 target을 거의 단독으로 설명하면 H002의
factorized reliability claim을 검증할 수 없다. 다음 sampling은 object label을 숨기는 것이
아니라, 같은 또는 near-matched `subject_label/object_label` cell 안에서 positive/negative
candidate가 같이 나오도록 구성해야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/142_reliability_target_v3_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/element_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/next_sampling_plan.json
```

## Reliability Target V3 Object/Endpoint-Controlled Plan

2026-06-20 KST에 `reliability_target_v3_object_endpoint_controlled_plan` TODO를 진행했다.
이 단계는 label fill이 아니라, 다음 v3 label pool을 만들기 위한 object/endpoint control
cell feasibility를 계산한 것이다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_controlled_plan_ready_broader_mining_required
candidates = 302
strict_eligible_rows = 73
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_candidate_mining
```

Candidate inventory:

| Item | Count |
| --- | ---: |
| ready packets | 347 |
| packet-ready support/vertical candidate rows | 302 |
| candidate-positive proxy rows | 222 |
| candidate-negative proxy rows | 80 |
| support_contact rows | 196 |
| relative_vertical rows | 106 |

Cell feasibility:

| Cell Type | Cells | Eligible Cells | Strong Cells | Eligible Rows | Pos Proxy | Neg Proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `subject_object_family` | 139 | 12 | 3 | 73 | 36 | 37 |
| `subject_object` | 119 | 13 | 3 | 89 | 46 | 43 |
| `object_family` | 54 | 10 | 4 | 163 | 91 | 72 |
| `object_predicate` | 89 | 5 | 2 | 73 | 22 | 51 |
| `endpoint_family` | 12 | 10 | 6 | 274 | 194 | 80 |
| `predicate_label` | 5 | 4 | 3 | 242 | 162 | 80 |

Recommended tiers:

| Tier | Cells | Suggested Pos Proxy | Suggested Neg Proxy | Suggested Total |
| --- | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 12 | 26 | 25 | 51 |
| `T2_object_family_fallback` | 4 | 23 | 19 | 42 |
| `T3_endpoint_family_balance` | 6 | 34 | 31 | 65 |

해석:

- strict `subject_label/object_label/predicate_family` cell은 필요하지만 단독으로 충분하지 않다.
- strict cell에는 eligible row가 `73`개뿐이고 strong cell은 `3`개다.
- 따라서 다음 candidate mining은 strict matched cell을 우선하되, `object_family` fallback과
  `endpoint_family` balance를 함께 사용해야 한다.
- candidate-positive/negative proxy는 sampling stratum일 뿐 target label이 아니다.
- posterior smoke는 계속 block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/143_reliability_target_v3_object_endpoint_controlled_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_controlled_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/candidate_pool_internal_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/recommended_sampling_cells.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/recommended_sampling_cells.json
```

## Reliability Target V3 Object/Endpoint Candidate Mining

2026-06-20 KST에 `reliability_target_v3_object_endpoint_candidate_mining` TODO를
진행했다. 이 단계는 object/endpoint-controlled sampling plan을 실제 train-only v3 label
sheet로 변환한 것이다. Label fill, ingestion, posterior smoke는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_candidate_mining_ready_with_selection_deficit
requested = 158
selected = 130
residual = 28
candidate-positive proxy strata = 68
candidate-negative proxy strata = 62
label_surface_leakage_hits = 0
packet_path_errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_object_endpoint_label_fill
```

Tier summary:

| Tier | Rows | Pos Proxy | Neg Proxy | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 50 | 25 | 25 | 22 | 28 | 29 |
| `T2_object_family_fallback` | 31 | 14 | 17 | 23 | 8 | 27 |
| `T3_endpoint_family_balance` | 49 | 29 | 20 | 32 | 17 | 33 |

해석:

- 새 sheet는 `130` rows이며, `70` unique scans와 `118` unique physical pairs를 포함한다.
- plan의 `158` rows보다 작아진 이유는 T1/T2/T3 cell overlap과 duplicate-pair /
  scan-diversity cap 때문이다.
- Labeler-visible TSV에는 proxy class, sampling tier/cell, semantic rank/score,
  `p_geom_valid`, geometry status, label-match status, endpoint flag pattern, matched-predicate
  hint가 들어가지 않는다.
- 위 hidden construction field는 post-label-only manifest에만 저장했다.
- 따라서 이 단계는 posterior evidence가 아니라, target-independence를 다시 검증하기 위한
  label sheet 준비 단계다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/144_reliability_target_v3_object_endpoint_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/object_endpoint_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/object_endpoint_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/selection_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/tier_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/v3_label_schema.json
```

## Reliability Target V3 Object/Endpoint Label Fill

2026-06-20 KST에 `reliability_target_v3_object_endpoint_label_fill` TODO를 진행했다.
이 단계는 object/endpoint-controlled `130`-row v3 sheet를 hypothesis-stage Codex proxy
label로 채운 것이다. Label ingestion과 posterior smoke는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_label_filled_codex_proxy_user_requested
rows = 130
reliable = 8
unreliable_geometry = 26
unreliable_trivial = 73
unreliable_ontology = 0
uncertain = 23
input_errors = 0
fill_validation_errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_object_endpoint_label_ingestion
```

Geometry support:

| Geometry support | Count |
| --- | ---: |
| `supports_predicate` | 85 |
| `contradicts_predicate` | 26 |
| `ambiguous` | 19 |

Relation usefulness:

| Usefulness | Count |
| --- | ---: |
| `informative` | 10 |
| `trivial_dense_or_room_structure` | 75 |
| `ontology_mismatch` | 26 |
| `uncertain` | 19 |

핵심 해석:

```text
geometry_support != relation_reliability
```

이번 fill은 H002의 핵심 분리 주장을 다시 보여준다. `supports_predicate`는 `85`개지만,
relation reliability에서 `reliable`은 `8`개뿐이다. 나머지 상당수는 geometry상 predicate가
성립하더라도 `trivial_dense_or_room_structure`로 떨어진다. 즉 geometry validity는 relation
reliability의 필요 evidence일 수 있지만 충분조건은 아니다.

다만 이 결과는 바로 posterior smoke를 열어도 된다는 뜻이 아니다. `reliable=8`이라 main
relation reliability binary target이 다시 positive-sparse일 가능성이 높다. 다음 ingestion은
geometry-support target, usefulness target, relation-reliability target을 분리해서 만들고,
그 뒤 target-independence audit으로 endpoint/object shortcut과 positive-sparse risk를 다시
검증해야 한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/145_reliability_target_v3_object_endpoint_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/completed_object_endpoint_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/object_endpoint_v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
```

## Reliability Target V3 Object/Endpoint Label Ingestion

2026-06-20 KST에 `reliability_target_v3_object_endpoint_label_ingestion` TODO를
진행했다. 이 단계는 object/endpoint-controlled `130`개 v3 label을 ingest하고,
relation reliability, geometry support, relation usefulness target을 분리해 만든 것이다.
Posterior smoke는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_label_ingested_positive_sparse_with_probe_risk
rows = 130
relation reliability target = 107 rows, 8 positive, 99 negative
geometry support target = 111 rows, 85 positive, 26 negative
relation usefulness target = 111 rows, 10 positive, 101 negative
ingestion_errors = 0
probe = target_independence_risk_hidden_metadata_correlated
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_object_endpoint_target_independence_audit
```

Target summary:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 107 | 8 | 99 | 0.0748 | 23 |
| `geometry_support_v3_binary_target` | 111 | 85 | 26 | 0.7658 | 19 |
| `relation_usefulness_v3_binary_target` | 111 | 10 | 101 | 0.0901 | 19 |

핵심 해석:

- `geometry_support_v3_binary_target`은 충분한 mass가 있다.
- 하지만 H002의 main target인 `relation_reliability_v3_binary_target`은 `8/107`
  positive라 posterior-ready가 아니다.
- `relation_usefulness_v3_binary_target`도 `10/111` positive라 positive-sparse다.
- quick probe는 hidden/visible shortcut risk를 flag하지만, reliability target 자체가
  extreme imbalance라 majority-baseline artifact와 true shortcut을 분리해야 한다.

따라서 다음 단계는 posterior가 아니라 target-independence audit이다. 이 audit은
“object/endpoint control이 실패했다”라고 바로 결론내리기보다, 실패 원인을 다음 중 하나로
분리해야 한다.

- true endpoint/object shortcut risk
- positive-sparse target artifact
- trivial room/surface relation over-sampling
- relation reliability definition이 너무 엄격한 문제
- geometry-support target과 reliability target의 목표 차이

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/146_reliability_target_v3_object_endpoint_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/validated_object_endpoint_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Reliability Target V3 Object/Endpoint Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_object_endpoint_target_independence_audit` TODO를
진행했다. 이 단계는 object/endpoint-controlled v3 target failure가 실제 shortcut인지,
positive-sparse target artifact인지 분리하기 위한 train-only 감사다. Posterior smoke는
실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_target_independence_audit_reliability_blocked_geometry_support_available
relation reliability target = 107 rows, 8 positive, 99 negative, blocked_positive_sparse
geometry support target = 111 rows, 85 positive, 26 negative, blocked_no_controlled_slice
relation usefulness target = 111 rows, 10 positive, 101 negative, blocked_positive_sparse
validation_errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_path_decision
```

핵심 해석:

- `relation_reliability_v3_binary_target`은 `8/107` positive라 posterior-ready가 아니다.
- `relation_usefulness_v3_binary_target`도 `10/111` positive라 positive-sparse다.
- `geometry_support_v3_binary_target`은 `85/26`으로 mass가 있지만 strict/diagnostic
  controlled slice가 없다.
- 따라서 geometry-support를 main target으로 바꾸면 H002의 핵심 구분인
  `semantic score != geometry validity != relation reliability`를 잃고, geometry-only
  verifier로 축소될 위험이 있다.

이번 단계의 결론은 posterior 결합 방식이 먼저가 아니라 target path decision이 먼저라는
것이다. 현재 병목은 factorized posterior가 약해서라기보다, relation reliability로 학습할
수 있는 target이 충분히 독립적이고 균형 있게 구성되지 않았다는 데 있다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/147_reliability_target_v3_object_endpoint_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Reliability Target V3 Object/Endpoint Path Decision

2026-06-20 KST에 `reliability_target_v3_object_endpoint_path_decision` TODO를 진행했다.
이 단계는 object/endpoint-controlled v3 target audit 이후 posterior smoke를 열지,
geometry-support를 main target으로 바꿀지, 혹은 target/sampling을 다시 수정할지 결정한
것이다. Posterior smoke와 combiner upgrade는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_object_endpoint_path_decision_informative_anchor_sampling
selected = revise_v3_informative_positive_anchor_sampling
relation reliability target = 107 rows, 8 positive, 99 negative
geometry supports-predicate rows = 85
unreliable_trivial rows = 73
trivial_dense_or_room_structure rows = 75
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_plan
```

결정:

- posterior smoke는 실행하지 않는다.
- combiner upgrade도 하지 않는다.
- `geometry_support_v3_binary_target`을 main target으로 바꾸지 않는다.
- `geometry_support`는 RGA decomposition/evidence axis로만 유지한다.
- 다음 경로는 object/endpoint control을 유지한 채 informative reliable positive anchor를
  별도로 찾는 것이다.

이 결론이 중요한 이유는, 현재 H002의 실패가 단순한 모델 결합 방식 문제가 아니기 때문이다.
Object/endpoint control 이후에도 `geometry_support_v3.supports_predicate`는 `85`개지만
`relation_reliability_v3.reliable`은 `8`개뿐이다. 반면
`relation_reliability_v3.unreliable_trivial`은 `73`개이고
`relation_usefulness_v3.trivial_dense_or_room_structure`는 `75`개다.

즉, 현재 병목은 다음과 같다.

```text
geometry상 성립하는 relation edge가 많아도, 그것이 scene graph에서 informative하고
reliable한 relation이라는 뜻은 아니다.
```

따라서 같은 object/endpoint sampling을 더 모으는 것은 primary path로 부적절하다.
대신 다음 단계는 `support_contact`와 `relative_vertical`에서 non-room, non-trivial,
object-level relation positive를 의도적으로 찾고, geometry contradiction / trivial
room-surface / uncertain-ontology negative를 함께 구성하는 것이다.

Posterior reopen gate:

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 방어 가능한 diagnostic controlled slice가 존재한다.
- `trivial_dense_or_room_structure`가 negative target을 단독 지배하지 않는다.
- object-label-only 및 endpoint-only probe가 target을 설명하지 않는다.
- validation/test usage는 계속 `False`다.

Fallback:

다음 informative-anchor mining에서도 controlled reliability target을 만들지 못하면, H002를
posterior method claim으로 강제하지 않는다. 그 경우 H002는 RGA diagnostic/decomposition
framework로 정리하는 것이 더 방어 가능하다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/148_reliability_target_v3_object_endpoint_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/target_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/next_plan.json
```

## Reliability Target V3 Informative Anchor Plan

2026-06-20 KST에 `reliability_target_v3_informative_anchor_plan` TODO를 진행했다.
이 단계는 object/endpoint control을 유지하면서 `floor`, `wall`, `ceiling` 중심의 trivial
room/surface relation dominance를 cap하고, informative reliable positive가 될 가능성이 높은
row를 별도 sampling category로 구성하기 위한 plan이다. Label fill과 posterior는 실행하지
않았다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_plan_ready_with_asset_requests
full train support/vertical rows = 286102
informative positive proxy rows = 87054
geometry contradiction negative proxy rows = 1828
trivial room/surface negative proxy rows = 180518
uncertain/ontology proxy rows = 16702
selected seed rows = 160
selected packet-ready rows = 126
selected asset-needed rows = 34
selected scans = 94
selected physical pairs = 160
selected support_contact = 76
selected relative_vertical = 84
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_candidate_mining
```

Sampling category:

| Category | Requested | Selected | Available | Packet-Ready Selected | Asset-Needed Selected |
| --- | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 40 | 87,054 | 40 | 0 |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 1,828 | 40 | 0 |
| `trivial_room_surface_negative_proxy` | 40 | 40 | 180,518 | 21 | 19 |
| `uncertain_or_ontology_negative_proxy` | 40 | 40 | 16,702 | 25 | 15 |

핵심 해석:

- Informative positive proxy 후보는 충분하다.
- 기존 object/endpoint attempt에서 빠진 것은 geometry support 자체가 아니라 non-trivial
  reliable relation positive를 적극적으로 찾는 sampling axis다.
- `floor`, `wall`, `ceiling`은 제거하지 않고 trivial negative로 유지하되 cap한다.
- selected seed `160`개 중 `34`개는 asset packet이 필요하다.
- 다음 candidate mining 단계에서는 packet generation/request 경로와 packet-ready-only fallback
  중 무엇을 사용할지 명시해야 한다.
- Posterior smoke는 계속 block한다.

Posterior reopen gate는 유지한다.

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 방어 가능한 diagnostic controlled slice가 존재한다.
- `trivial_dense_or_room_structure`가 target을 단독 지배하지 않는다.
- object-label-only 및 endpoint-only probe가 target을 설명하지 않는다.
- validation/test usage는 계속 `False`다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/149_reliability_target_v3_informative_anchor_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/category_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/seed_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/selection_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_plan/sampling_contract.json
```

## Reliability Target V3 Informative Anchor Candidate Mining

2026-06-20 KST에 `reliability_target_v3_informative_anchor_candidate_mining` TODO를
진행했다. 이 단계는 informative-anchor plan의 160개 train-only seed를 label sheet로
변환하고, hidden proxy/sampling field를 label surface에서 제거했는지 확인하는 단계다.
Label fill과 posterior는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_candidate_mining_ready_needs_asset_packets
full label sheet rows = 160
packet-ready fallback label sheet rows = 126
asset-needed rows = 34
unique scans = 94
unique physical pairs = 160
support_contact rows = 76
relative_vertical rows = 84
label-surface leakage hits = 0
packet path errors = 0
validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_asset_packets
```

Category summary:

| Category | Rows | Packet Ready | Asset Needed | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 18 | 22 | 20 |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 24 | 16 | 31 |
| `trivial_room_surface_negative_proxy` | 40 | 21 | 19 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 25 | 15 | 16 | 24 | 28 |

해석:

- Preferred route는 full 160-row sheet를 유지하는 것이다.
- Packet-ready fallback은 126-row label fill로 바로 갈 수 있지만, trivial room/surface
  negative와 uncertain/ontology negative를 각각 21/40, 25/40만 포함한다.
- 따라서 packet-ready fallback은 category coverage caveat가 있는 backup route이고, primary
  route는 34개 asset-needed row의 packet을 먼저 생성하거나 연결하는 것이다.
- Candidate mining은 아직 reliability target을 만든 단계가 아니다. H002 posterior smoke는
  label fill, ingestion, target-independence audit이 통과하기 전까지 계속 block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/150_reliability_target_v3_informative_anchor_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/category_summary.csv
```

## Reliability Target V3 Informative Anchor Asset Packets

2026-06-20 KST에 `reliability_target_v3_informative_anchor_asset_packets` TODO를 진행했다.
이 단계는 candidate mining에서 남아 있던 `34`개 asset-needed row에 packet을 생성하고,
기존 packet-ready `126`개와 합쳐 full `160`-row label sheet를 packet-complete 상태로 만드는
작업이다. Label fill과 posterior는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_asset_packets_ready
input selected rows = 160
asset-needed input rows = 34
generated packet rows = 34
generated non-ready rows = 0
full label sheet rows = 160
ready label rows = 160
packet path errors = 0
label-surface leakage hits = 0
validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_label_fill
```

Category summary:

| Category | Rows | Ready | Generated | Existing | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 40 | 24 | 16 | 31 |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 40 | 18 | 22 | 20 |
| `trivial_room_surface_negative_proxy` | 40 | 40 | 19 | 21 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 40 | 15 | 25 | 16 | 24 | 28 |

해석:

- 이제 preferred route인 full `160`-row informative-anchor label fill이 가능하다.
- 이전 blocker는 target이나 posterior 결합 방식이 아니라 evidence packet 부재였다.
- 이 단계는 H002 posterior를 검증한 것이 아니라 label-readiness를 확보한 단계다.
- 다음 label fill에서도 proxy category는 label target으로 쓰면 안 되고, sampling provenance로만
  남겨야 한다.
- Posterior smoke는 label fill, ingestion, target-independence audit이 통과하기 전까지 계속
  block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/151_reliability_target_v3_informative_anchor_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/asset_needed_manifest_with_packets_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/category_summary.csv
```

## Reliability Target V3 Informative Anchor Label Fill

2026-06-20 KST에 `reliability_target_v3_informative_anchor_label_fill` TODO를 진행했다.
이 단계는 full `160`-row packet-complete informative-anchor sheet를 user-requested Codex proxy로
채우는 작업이다. Hidden proxy/sampling/source/geometry field는 label decision 전에 사용하지
않았고, label fill 이후 diagnostics에만 조인했다. Posterior는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_label_filled_codex_proxy_user_requested
rows = 160
reliable = 35
unreliable_geometry = 13
unreliable_trivial = 34
unreliable_ontology = 0
uncertain = 78
input validation errors = 0
fill validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_label_ingestion
```

Axis counts:

| Axis | Value | Count |
| --- | --- | ---: |
| geometry_support | `supports_predicate` | 72 |
| geometry_support | `contradicts_predicate` | 13 |
| geometry_support | `ambiguous` | 75 |
| relation_usefulness | `informative` | 37 |
| relation_usefulness | `trivial_dense_or_room_structure` | 35 |
| relation_usefulness | `ontology_mismatch` | 13 |
| relation_usefulness | `uncertain` | 75 |

Post-label anchor-category diagnostics:

| Anchor Category | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 32 | 0 | 0 | 8 |
| `geometry_contradiction_negative_proxy` | 40 | 1 | 13 | 18 | 8 |
| `trivial_room_surface_negative_proxy` | 40 | 2 | 0 | 16 | 22 |
| `uncertain_or_ontology_negative_proxy` | 40 | 0 | 0 | 0 | 40 |

해석:

- Informative-anchor sampling은 object/endpoint attempt의 reliable `8` rows를 `35` rows로
  늘렸다.
- 하지만 여전히 `supports_predicate != reliable`이다. `72` rows가 predicate를 geometry상
  support하지만, reliable은 `35` rows다.
- `uncertain=78`이 크므로 binary target derivation 후 실제 usable row 수를 확인해야 한다.
- 새로 생성한 asset packet `34` rows가 모두 uncertain으로 채워졌으므로 packet-source confounding을
  ingestion/audit에서 반드시 확인해야 한다.
- 이 결과는 label-readiness 및 target 후보 evidence이지 posterior method evidence가 아니다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/152_reliability_target_v3_informative_anchor_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/completed_informative_anchor_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/informative_anchor_v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
```

## Reliability Target V3 Informative Anchor Label Ingestion

2026-06-20 KST에 `reliability_target_v3_informative_anchor_label_ingestion` TODO를 진행했다.
이 단계는 filled v3 labels를 ingest하고 relation reliability, geometry support, relation
usefulness target을 분리해 만드는 작업이다. Posterior는 실행하지 않았다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_label_ingested_with_probe_risk
rows = 160
relation reliability binary = 82 rows, 35 positive, 47 negative
geometry support binary = 85 rows, 72 positive, 13 negative
relation usefulness binary = 85 rows, 37 positive, 48 negative
ingestion errors = 0
relation reliability probe = target_independence_risk_hidden_metadata_correlated
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_target_independence_audit
```

Binary target counts:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 82 | 35 | 47 | 0.4268 | 78 |
| `geometry_support_v3_binary_target` | 85 | 72 | 13 | 0.8471 | 75 |
| `relation_usefulness_v3_binary_target` | 85 | 37 | 48 | 0.4353 | 75 |

Probe summary:

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 13 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |

해석:

- Informative-anchor path는 처음으로 usable relation reliability binary target mass를 만들었다:
  `35` positive / `47` negative.
- 이는 object/endpoint attempt의 relation reliability `8` positive / `99` negative보다 크게 낫다.
- 하지만 target-independence probe가 hidden/visible shortcut risk를 강하게 띄운다.
- 가장 중요한 위험은 `anchor_category_hidden`, endpoint pattern, object labels, subject/object family cells,
  rank band가 target을 설명할 수 있다는 점이다.
- 따라서 이 결과는 posterior smoke를 여는 근거가 아니라, target-independence audit으로 넘어갈 근거다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/153_reliability_target_v3_informative_anchor_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/validated_informative_anchor_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_posterior_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Reliability Target V3 Informative Anchor Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_informative_anchor_target_independence_audit` TODO를
진행했다. 이 단계는 informative-anchor v3 target이 posterior smoke로 넘어갈 수 있는지,
또는 anchor/object/endpoint/rank shortcut으로 설명되는지를 확인하는 감사다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_target_independence_audit_blocked
relation reliability = 82 rows, 35 positive, 47 negative, blocked_no_controlled_slice
geometry support = 85 rows, 72 positive, 13 negative, blocked_positive_sparse
relation usefulness = 85 rows, 37 positive, 48 negative, blocked_no_controlled_slice
validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_path_decision
```

핵심 해석:

- Informative-anchor sampling은 relation reliability target의 positive mass를 확보했다.
  즉, 기존 object/endpoint attempt의 `8` positive 문제는 해결했다.
- 하지만 posterior-ready target은 아직 아니다.
- `anchor_category_hidden` alone gives majority accuracy `0.9634` against a
  `0.5732` majority baseline, and object/endpoint structure is even stronger.
- `subject_object_family_cell_hidden` reaches majority accuracy `1.0000`, while
  `endpoint_flag_pattern_hidden` reaches `0.9756`.
- Visible object identity도 강하다: `object_label` majority accuracy `0.9512`,
  `subject_label` majority accuracy `0.9146`.
- Family-balanced (`64` rows, `32/32`) and predicate-balanced (`56` rows, `28/28`)
  slices still retain anchor/object/endpoint risks.
- Anchor/category-balanced (`6` rows, `3/3`) and endpoint-balanced (`4` rows, `2/2`)
  slices are too small, so shortcut은 줄어도 posterior target으로 쓸 수 없다.
- `geometry_support`는 RGA evidence axis로 중요하지만 `72/13`이라 main reliability
  target으로 쓰면 reliability를 geometry validity로 다시 합치는 문제가 생긴다.

따라서 현재 blocker는 posterior 결합 방식이나 SOTA combiner 부재가 아니라 target
construction이다. 다음 단계는 posterior smoke가 아니라 path decision이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/154_reliability_target_v3_informative_anchor_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Reliability Target V3 Informative Anchor Path Decision

2026-06-20 KST에 `reliability_target_v3_informative_anchor_path_decision` TODO를
진행했다. 이 단계는 informative-anchor v3 target-independence audit 이후 posterior를
강행할지, geometry-support target으로 바꿀지, 같은 방식으로 더 label을 모을지, 아니면
target construction 자체를 바꿀지 결정하는 gate다.

결과:

```text
status = h002_reliability_target_v3_informative_anchor_path_decision_matched_contrast_v4
selected_path = revise_to_matched_contrast_reliability_target_v4
relation reliability = 82 rows, 35 positive, 47 negative, blocked_no_controlled_slice
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_plan
```

선택한 방향:

```text
matched_contrast_reliability_target_v4
```

이 결정을 내린 이유:

- v3는 positive sparsity를 해결했다. 따라서 문제는 더 이상 단순히 positive가 부족한 것이 아니다.
- 하지만 v3는 `anchor_category_hidden`, endpoint/object structure, object labels, rank band가
  target을 설명하는 문제를 해결하지 못했다.
- 즉, posterior를 지금 돌리면 factorized reliability를 학습하는 것이 아니라 target construction
  artifact를 학습할 가능성이 높다.
- geometry-support는 `72/13`으로 mass가 있지만, 이것을 main target으로 쓰면 H002의 핵심 구분인
  `semantic score != geometry validity != relation reliability`가 무너진다.
- family-balanced / predicate-balanced slice는 row 수는 남지만 shortcut이 남고, anchor/endpoint
  balanced slice는 너무 작아진다.

따라서 다음 target은 다음 방식이어야 한다.

```text
same predicate / endpoint-object / rank stratum 안에서
reliable edge와 unreliable edge를 contrast
```

v4 matching axes:

- `predicate_family`
- `predicate_label` when enough rows exist
- `endpoint_flag_pattern_hidden`
- `object_family_cell_hidden` or `endpoint_family_cell_hidden`
- `rank_band_hidden`

v4 posterior reopen gate:

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 명시적으로 방어 가능한 diagnostic controlled slice가 존재한다.
- selected slice에서 anchor/category shortcut risk가 `0`이어야 한다.
- endpoint/object 및 visible object-label shortcut만으로 target을 설명할 수 없어야 한다.
- rank-band와 geometry-status control이 selected slice를 지배하지 않아야 한다.
- validation/test usage는 계속 `False`다.

Fallback:

- v4 matched contrast도 independent target을 만들지 못하면, H002는 posterior method claim으로
  억지로 끌고 가지 않는다.
- 그 경우 H002는 RGA diagnostic/decomposition framework로 정리한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/155_reliability_target_v3_informative_anchor_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/next_plan.json
```

## Reliability Target V4 Matched Contrast Plan

2026-06-20 KST에 `reliability_target_v4_matched_contrast_plan` TODO를 진행했다.
이 단계는 v3 path decision에서 선택한 matched-contrast 방향을 실제 train-only queue에서
구성할 수 있는지 확인하는 planning gate다. Label fill, ingestion, posterior smoke는
진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_plan_ready_with_asset_requests
selected_matching_level = predicate_object_rank_controlled
selected_matching_keys = predicate_label, endpoint_flag_pattern_hidden, object_family_cell_hidden
rank_control_policy = post_selection_quota_and_audit_control
selected rows = 160
selected contrast pairs = 80
packet_ready = 5
asset_needed = 155
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_candidate_mining
```

Matching level inventory:

| Matching Level | Rank Exact | Eligible Groups | Pair Capacity | Verdict |
| --- | --- | ---: | ---: | --- |
| `strict_predicate_object_rank` | `True` | 0 | 0 | infeasible |
| `family_object_rank` | `True` | 0 | 0 | infeasible |
| `family_endpoint_rank` | `True` | 0 | 0 | infeasible |
| `predicate_object_rank_controlled` | `False` | 114 | 275 | selected |
| `family_object_rank_controlled` | `False` | 138 | 316 | feasible fallback |
| `family_endpoint_rank_controlled` | `False` | 6 | 319 | broad fallback |

해석:

- Exact rank-band matching은 현재 train queue에서 불가능하다.
- 따라서 v4는 rank를 exact matching key로 쓰지 않고, post-selection quota와 target-independence
  audit control로 처리해야 한다.
- 선택된 construction은 `predicate_label + endpoint_flag_pattern + object_family_cell`을 match하고,
  rank-band는 별도 quota/audit으로 통제하는 방식이다.
- 이 방식은 v3보다 강하다. v3는 positive-like anchor bucket과 negative-like anchor bucket을
  따로 구성했지만, v4는 같은 predicate/object endpoint stratum 내부에서 contrast한다.
- 다만 packet coverage가 매우 낮다: `5/160`만 packet-ready이고 `155/160`은 asset-needed다.
- 다음 단계는 v4 candidate mining과 asset packet request를 함께 준비하는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/156_reliability_target_v4_matched_contrast_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/matching_level_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/selected_strata_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/selected_strata_preview.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/seed_preview_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/asset_request_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_plan/sampling_contract.json
```

## Reliability Target V4 Matched Contrast Candidate Mining

2026-06-20 KST에 `reliability_target_v4_matched_contrast_candidate_mining` TODO를 진행했다.
이 단계는 v4 matched-contrast plan의 80개 contrast pair / 160개 row를 실제 label package와
asset request plan으로 고정하는 작업이다. Label fill, ingestion, posterior smoke는 진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_candidate_mining_ready_needs_asset_packets
label rows = 160
contrast pairs = 80
positive proxy rows = 80
negative proxy rows = 80
support_contact rows = 90
relative_vertical rows = 70
packet-ready rows = 5
asset-needed rows = 155
asset request rows = 155
label-surface leakage hits = 0
packet path errors = 0
input validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_asset_packets
```

핵심 해석:

- v4의 label sheet와 post-label hidden manifest는 준비됐다.
- Label surface에는 contrast role, stratum, rank, semantic score, geometry status, proxy field를
  노출하지 않았다.
- `geometry_status_hidden`은 `satisfied:80`, `unsatisfied:80`으로 proxy-level 균형을 갖는다.
- 다만 evidence packet coverage는 아직 부족하다. 기존 packet-ready row는 `5/160`뿐이고,
  `155/160`은 asset-needed다.
- packet-ready fallback sheet는 format/debug sanity에는 쓸 수 있지만 posterior reopening에는
  너무 작다.
- 따라서 다음 단계는 label fill이 아니라 v4 asset packet generation이다.
- Posterior는 reviewed labels를 ingest하고 target-independence audit이 통과하기 전까지 계속
  block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/157_reliability_target_v4_matched_contrast_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/matched_contrast_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_candidate_mining/v4_label_schema.json
```

## Reliability Target V4 Matched Contrast Asset Packets

2026-06-20 KST에 `reliability_target_v4_matched_contrast_asset_packets` TODO를 진행했다.
이 단계는 v4 matched-contrast candidate mining에서 남아 있던 155개 `asset_needed` row에
multi-view / mesh / contact-context evidence packet을 생성하고, 기존 5개 packet-ready row와
합쳐 full 160-row label sheet를 만드는 작업이다. Label fill, ingestion, posterior smoke는
진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_asset_packets_partial
input selected rows = 160
asset-needed input rows = 155
generated packet rows = 155
generated ready rows = 135
generated partial rows = 20
existing packet-ready rows = 5
full label sheet rows = 160
ready label rows = 140
partial label rows = 20
packet path errors = 0
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_asset_packet_gap_audit
```

Partial row breakdown:

| Item | Count |
| --- | ---: |
| `support_contact` partial rows | 13 |
| `relative_vertical` partial rows | 7 |
| missing subject crop rows | 12 |
| missing object crop rows | 8 |

핵심 해석:

- 모든 row의 label-facing packet path는 존재한다. 즉 path-level packet generation은 성공했다.
- Label surface와 packet text에는 contrast role, rank, semantic score, `p_geom`, geometry status,
  target-construction proxy가 노출되지 않았다.
- 하지만 20개 row는 한쪽 endpoint crop이 없어 strict packet-ready가 아니다.
- 이 20개 row는 packet markdown, mesh packet, contact/context sheet는 존재하지만 subject/object
  crop 중 하나가 빠져 있다.
- 따라서 label fill로 바로 넘어가지 않는다. 다음 단계는 partial packet row를
  `limited_view_evaluable`, `needs_more_evidence`, or replacement-needed로 판정하는 gap audit이다.
- Posterior는 reviewed labels를 ingest하고 target-independence audit이 통과하기 전까지 계속
  block한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/158_reliability_target_v4_matched_contrast_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/matched_contrast_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/matched_contrast_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/label_surface_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/visible_value_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/stratum_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packets/packets/
```

## Reliability Target V4 Matched Contrast Asset Packet Gap Audit

2026-06-20 KST에 `reliability_target_v4_matched_contrast_asset_packet_gap_audit` TODO를
진행했다. 이 단계는 v4 asset packet generation에서 남은 20개 partial row를 label fill 전에
감사하고, v4 matched contrast의 pair integrity를 보존하기 위해 replacement-needed row가
포함된 pair를 제외하는 gate다. Label fill, ingestion, posterior smoke는 진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_asset_packet_gap_audit_ready_for_label_readiness
input rows = 160
input pairs = 80
label-ready rows = 158
label-ready pairs = 79
excluded rows = 2
excluded pairs = 1
limited-view rows kept = 19
replacement-needed rows = 1
role balance = positive_proxy 79, negative_proxy 79
ready family counts = support_contact 90, relative_vertical 68
output path errors = 0
visible leakage hits = 0
input validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_label_readiness
```

핵심 해석:

- 19/20 partial rows는 `limited_view_evaluable`로 유지했다. 이유는 한쪽 endpoint crop은
  빠져 있지만 mesh packet과 contact/context evidence가 있기 때문이다.
- 1개 row는 `replacement_needed`로 판정했다. missing endpoint가 generic `object` label이라
  endpoint identity를 독립적으로 확인하기 어렵기 때문이다.
- v4는 pair contrast가 핵심이므로 replacement-needed row가 포함된 `v4pair_0042` 전체를
  label fill에서 제외했다.
- 결과적으로 `79` matched pairs / `158` rows가 label-ready로 남았다.
- positive/negative proxy role balance는 `79/79`로 유지된다.
- 다음 단계는 label fill이 아니라, 이 158-row sheet의 schema, packet path, excluded-pair
  removal, role balance, leakage를 검증하는 label-readiness gate다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/159_reliability_target_v4_matched_contrast_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/row_gap_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/partial_row_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/pair_gap_decisions.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/label_ready_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/label_ready_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/excluded_pair_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/excluded_pair_ids.txt
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/replacement_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/output_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/visible_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_asset_packet_gap_audit/packets/
```

## Reliability Target V4 Matched Contrast Label Readiness

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_readiness` TODO를
진행했다. 이 단계는 gap audit 이후 남은 `158` rows / `79` matched pairs sheet가
visible-only label fill로 넘어가도 되는지 검증하는 gate다. Label fill, ingestion,
posterior smoke는 진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_label_readiness_ready_for_label_fill
label-ready rows = 158
label-ready pairs = 79
ready rows = 139
limited-view rows = 19
ready family counts = support_contact 90, relative_vertical 68
role balance = positive_proxy 79, negative_proxy 79
expected columns match = true
input validation errors = 0
sheet validation errors = 0
packet path errors = 0
leakage hits = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_label_fill
```

핵심 해석:

- 158-row / 79-pair v4 matched-contrast sheet는 label fill로 넘어갈 수 있다.
- 이 단계의 성과는 posterior 성능이 아니라 label-fill readiness다.
- hidden proxy role, rank, semantic score, geometry status, target-construction proxy는
  label surface에서 계속 숨겨져 있다.
- multi-view / mesh / contact-context packet은 audit/label evidence로만 쓰고, 아직
  posterior input으로 승격하지 않는다.
- Posterior smoke는 label fill, ingestion, target-independence audit이 통과할 때까지
  계속 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/160_reliability_target_v4_matched_contrast_label_readiness.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/label_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/pair_readiness.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/input_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/sheet_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/leakage_hits.jsonl
```

## Reliability Target V4 Matched Contrast Label Fill

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_fill` TODO를 진행했다.
이 단계는 158-row / 79-pair v4 matched-contrast sheet를 visible-only 기준으로 채우는
단계다. Ingestion, target-independence audit, posterior smoke는 진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_label_filled_codex_proxy_user_requested
rows = 158
reliable = 23
unreliable = 24
uncertain = 111
binary target rows = 47
binary positive rows = 23
binary negative rows = 24
geometry support = supports 30, contradicts 17, ambiguous 111
input validation errors = 0
fill validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_label_ingestion
```

핵심 해석:

- Binary usable rows는 `47`개이고 `23/24`로 positive/negative가 거의 균형이다.
- 하지만 `111/158` rows가 `uncertain`이라 conservative proxy label set이다.
- Hidden role/source diagnostics는 label lock 이후에만 join했다.
- `positive_proxy` side는 `12 reliable / 10 unreliable / 57 uncertain`,
  `negative_proxy` side는 `11 reliable / 14 unreliable / 54 uncertain`이다.
- 즉 matched role 자체가 label을 trivially 결정하지는 않는다.
- 다만 pair-level direct contrast는 약하다. `reliable/unreliable` direct pair는 `1/79`뿐이다.
- 따라서 다음 단계는 posterior가 아니라 label ingestion과 target-independence audit이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/161_reliability_target_v4_matched_contrast_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/completed_v4_matched_contrast_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/v4_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/pair_post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
```

## Reliability Target V4 Matched Contrast Label Ingestion

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_ingestion` TODO를
진행했다. 이 단계는 v4 proxy labels를 ingest해서 relation reliability, geometry support,
relation usefulness target artifacts로 분리하는 단계다. Posterior candidate file은 생성했지만
posterior smoke는 진행하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_label_ingested_with_probe_risk
rows = 158
relation reliability binary = 47 rows, 23 positive, 24 negative
geometry support binary = 47 rows, 30 positive, 17 negative
relation usefulness binary = 50 rows, 25 positive, 25 negative
ingestion errors = 0
relation reliability probe = target_independence_risk_hidden_metadata_correlated
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_target_independence_audit
```

Probe 결과:

- `relation_reliability_v4_binary_target`: hidden risks `3`, visible risks `2`.
- `geometry_support_v4_binary_target`: hidden risks `3`, visible risks `4`.
- `relation_usefulness_v4_binary_target`: hidden risks `3`, visible risks `2`.
- Relation reliability의 가장 큰 risk는 `subject_object_family_cell_hidden`, `endpoint_flag_pattern_hidden`,
  `object_family_cell_hidden`, visible `subject_label`, visible `object_label`이다.

핵심 해석:

- Relation reliability target은 `23/24`로 balanced target mass를 확보했다.
- 그러나 object/family cell과 visible object label이 target을 설명할 위험이 크다.
- 따라서 posterior smoke는 여전히 blocked다.
- 다음 단계는 target-independence audit으로 controlled slice가 남는지 확인하는 것이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/162_reliability_target_v4_matched_contrast_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/validated_v4_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/geometry_support_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_usefulness_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_posterior_candidates.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Reliability Target V4 Matched Contrast Target Independence Audit

2026-06-21 KST에 `reliability_target_v4_matched_contrast_target_independence_audit` TODO를
진행했다. 이 단계는 v4 matched-contrast target이 posterior smoke를 허용할 만큼
target-independent한지 확인하는 단계다. Posterior는 학습하지 않았고, validation/test는
사용하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_target_independence_audit_blocked
validation_errors = 0
relation reliability = 47 rows, 23 positive, 24 negative
geometry support = 47 rows, 30 positive, 17 negative
relation usefulness = 50 rows, 25 positive, 25 negative
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_path_decision
```

핵심 해석:

- v4는 `23/24` relation reliability balance를 만들었지만 posterior-ready target은 아니다.
- `matched_contrast_role_hidden` 자체는 original target의 주된 shortcut이 아니었다.
- 하지만 relation reliability label은 `subject_object_family_cell_hidden`에 완전히 묶여 있다
  (`NMI=1.0000`, majority accuracy `1.0000`).
- visible `subject_label`도 target을 강하게 설명한다 (`NMI=0.7764`, majority accuracy `0.9149`).
- `endpoint_flag_pattern_hidden`, `endpoint_family_cell_hidden`, `object_family_cell_hidden`,
  visible `object_label` risk도 남아 있다.
- 18개 controlled slice를 만들었지만 relation reliability에 strict/diagnostic posterior-ready
  slice는 없었다.

따라서 현재 문제는 posterior 결합 방식보다 target construction이다. 지금 posterior smoke를
실행하면 relation reliability를 배운 것인지 object/family shortcut을 배운 것인지 방어할 수 없다.
다음 단계는 `reliability_target_v4_matched_contrast_path_decision`이다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/163_reliability_target_v4_matched_contrast_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_table.csv
```

## Reliability Target V4 Matched Contrast Path Decision

2026-06-21 KST에 `reliability_target_v4_matched_contrast_path_decision` TODO를
진행했다. 이 단계는 v4 target-independence audit이 blocked 된 뒤 다음 target construction
방향을 고정하는 단계다. Posterior는 실행하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_path_decision_select_v5_cell_contrast_feasibility
selected_path = v5_cell_contrast_feasibility_scan
relation reliability = 47 rows, 23 positive, 24 negative
direct reliable/unreliable pair contrast = 1 / 79 pairs
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_feasibility_scan
```

핵심 해석:

- v4는 class balance와 matched-role shortcut 문제를 개선했다.
- 그러나 target은 여전히 subject/object-family cell에 종속되어 있다.
- current v4의 `subject_object_family_cell_balanced_v4` slice는 `0` rows라 exact object-cell
  control이 불가능하다.
- pairwise target도 direct reliable/unreliable contrast가 `1/79` pairs뿐이라 아직 사용할 수 없다.
- 따라서 posterior smoke를 열지 않고, 같은 v4 sampling을 단순 확장하지도 않는다.

선택한 다음 경로는 `v5_cell_contrast_feasibility_scan`이다. 이 단계는 label fill 전에 full train pool에서
same subject/object/family cell 내부에 reliable-like와 unreliable-like 후보가 함께 존재하는지
확인한다. Feasibility가 없으면 H002 posterior track을 멈추고 RGA diagnostic/decomposition
framework로 정리한다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/164_reliability_target_v4_matched_contrast_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/next_plan.json
```

## Reliability Target V5 Cell Contrast Feasibility Scan

2026-06-21 KST에 `reliability_target_v5_cell_contrast_feasibility_scan` TODO를
진행했다. 이 단계는 label fill 전에 full train-only pool에서 exact cell-level contrast capacity가
있는지만 확인하는 gate다. Posterior는 실행하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining
selected_level = strict_predicate_subject_object_endpoint
selected rows = 80
selected pairs = 40
selected mixed cells = 21
max_cell_share = 0.0500
packet_ready = 2
asset_needed = 78
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_candidate_mining
```

핵심 해석:

- strict predicate + subject/object label + endpoint pattern level에서도 mixed proxy capacity가 있다.
- eligible groups는 `137`, balanced pair capacity는 `167`이다.
- selected preview는 `40` pairs / `80` rows / `21` cells로 single-cell concentration이 낮다.
- family distribution은 `support_contact:48`, `relative_vertical:32`다.
- packet coverage는 낮다: `2/80` ready, `78/80` asset-needed.

따라서 H002를 바로 freeze할 필요는 없다. 다만 이것은 posterior를 여는 결과가 아니라
v5 candidate mining과 asset packet path를 정당화하는 결과다. v5 label fill 이후에도
target-independence audit을 다시 통과해야 posterior smoke를 열 수 있다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/165_reliability_target_v5_cell_contrast_feasibility_scan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_feasibility_scan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/matching_level_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/selected_cell_preview.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/seed_preview_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/asset_request_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/feasibility_contract.json
```

## Reliability Target V5 Cell Contrast Candidate Mining

2026-06-21 KST에 `reliability_target_v5_cell_contrast_candidate_mining` TODO를
진행했다. 이 단계는 strict predicate+subject/object+endpoint cell 안에서 positive-like와
negative-like proxy를 paired candidate로 묶고, labeler에게 보이는 정보와 hidden post-label
manifest를 분리하는 단계다. Posterior는 실행하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_candidate_mining_ready_needs_asset_packets
selected_level = strict_predicate_subject_object_endpoint
label rows = 80
contrast pairs = 40
contrast cells = 21
packet_ready = 2
asset_needed = 78
asset_request_rows = 78
field leakage = 0
value leakage = 0
packet path errors = 0
input validation errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_asset_packets
```

핵심 해석:

- v5 candidate mining은 posterior-ready result가 아니라 label round 준비물이다.
- Blind label sheet는 `80` rows / `40` pairs / `21` cells로 구성되며, hidden role은
  `positive_proxy:40`, `negative_proxy:40`으로 균형을 맞췄다.
- Source queue와 geometry status도 각각 `HL:40`/`LH:40`, `satisfied:40`/`unsatisfied:40`이다.
- Family는 `support_contact:48`, `relative_vertical:32`다.
- Label surface leakage check가 `0`이라 target shortcut 후보가 labeler에게 직접 보이지 않는다.
- 다만 packet-ready row가 `2`개뿐이므로, full label fill 전에 `78`개 asset-needed row의
  packet generation/readiness가 필요하다.

따라서 다음 단계는 label fill이 아니라 `reliability_target_v5_cell_contrast_asset_packets`다.
이후 v5 label fill, ingestion, target-independence audit을 통과해야만 posterior smoke를 다시 열 수 있다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/166_reliability_target_v5_cell_contrast_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/selected_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/v5_label_schema.json
```

## Reliability Target V5 Cell Contrast Asset Packets

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packets` TODO를
진행했다. 이 단계는 v5 candidate mining의 `78` asset-needed rows에 evidence packet을
생성하고, 기존 `2` packet-ready rows와 합쳐 full `80`-row label sheet를 만드는 단계다.
Posterior는 실행하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_asset_packets_partial
input selected rows = 80
asset-needed input rows = 78
generated packet rows = 78
generated ready rows = 66
generated non-ready rows = 12
existing packet-ready rows = 2
full label sheet rows = 80
ready label rows = 68
packet path errors = 1
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v5_cell_contrast_asset_packet_gap_audit
```

핵심 해석:

- v5 asset packet generation은 target construction 문제를 새로 만든 것이 아니라 evidence
  coverage 문제를 드러냈다.
- Label surface leakage와 visible value leakage는 모두 `0`이다.
- `68/80` rows는 ready이고 `12/80` rows는 partial이다.
- Partial rows는 `support_contact:6`, `relative_vertical:6`이며, 주된 원인은 endpoint crop
  부족이다 (`subject` crop missing `6`, `object` crop missing `7`).
- Mesh packet은 partial rows에서도 모두 존재한다.
- 단 `ftv5cc_0a7d66060905`는 `contact_or_context_sheet`가 비어 있어 packet path error `1`이 있다.

따라서 다음 단계는 label fill이 아니라 `reliability_target_v5_cell_contrast_asset_packet_gap_audit`다.
이 gap audit에서 partial rows를 limited-view evaluable로 유지할지, replacement/needs-more-evidence로
보낼지 결정해야 한다. Posterior smoke는 여전히 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/167_reliability_target_v5_cell_contrast_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_contrast_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_contrast_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/label_surface_leakage_audit.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/pair_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_summary.csv
```

## Reliability Target V5 Cell Contrast Asset Packet Gap Audit

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packet_gap_audit`
TODO를 진행했다. 이 단계는 v5 asset packet generation의 partial rows를 label fill 전에
감사하고, v5 pair contrast 구조를 보존하기 위해 replacement-needed row가 있는 pair 전체를
제외하는 단계다. Posterior는 실행하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness
input rows = 80
input pairs = 40
label-ready rows = 72
label-ready pairs = 36
excluded rows = 8
excluded pairs = 4
limited-view rows kept = 6
replacement-needed rows = 5
output path errors = 0
visible leakage hits = 0
input validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v5_cell_contrast_label_readiness
```

핵심 해석:

- Gap audit 이후 label-ready sheet는 `72` rows / `36` pairs다.
- Hidden role balance는 `positive_proxy:36`, `negative_proxy:36`으로 유지됐다.
- Family balance는 `support_contact:44`, `relative_vertical:28`이다.
- `6` limited-view rows는 유지하고, `5` replacement-needed rows 때문에 `4` pairs를 제외했다.
- 제외 pair는 `v5cell_0013`, `v5cell_0014`, `v5cell_0033`, `v5cell_0034`다.
- 이전 단계에서 있던 empty `contact_or_context_sheet` 문제는 해당 pair가 제외되면서
  label-ready sheet에서는 path error `0`이 됐다.

따라서 다음 단계는 label fill이 아니라 `reliability_target_v5_cell_contrast_label_readiness`다.
Readiness 단계에서 expected columns, packet paths, role balance, leakage, readiness status를
검증한 뒤 label fill로 넘어갈 수 있다. Posterior smoke는 여전히 blocked다.

생성된 주요 artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/168_reliability_target_v5_cell_contrast_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/row_gap_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/partial_row_decisions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/pair_gap_decisions.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/excluded_pair_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/excluded_pair_ids.txt
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/replacement_request_plan.jsonl
```
