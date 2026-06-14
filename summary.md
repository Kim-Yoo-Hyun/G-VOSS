# H001 / GeoCalib Research Summary

## Research Direction

H001의 연구 방향은 새로운 3D Scene Graph generator를 만드는 것이 아니라,
이미 생성된 3DSSG relation predictions의 신뢰도를 explicit 3D geometry
evidence로 평가하고 보정하는 것이다.

Paper-facing method/title name은 `GeoCalib`이다. `H001`은 내부
hypothesis/experiment 식별자와 파일 경로명으로 유지한다.

현재 가장 방어 가능한 논문 framing은 다음과 같다.

```text
GeoCalib: calibrated geometry-consistency evaluation and re-ranking framework
for 3D scene graph relation-source outputs
```

이 방향은 `RelWitness`와 의도적으로 다르다. `RelWitness`는 open-vocabulary
3DSSG에서 unannotated relation을 visual-geometric witness로 검증해 학습
supervision으로 사용하는 문제를 다룬다. H001은 이미 나온 `VL-SAT`,
Open3DSG, Qwen-VL 같은 relation source의 output row가 실제 object-pair
geometry와 얼마나 일치하는지 측정하고, 그 reliability signal로 ranking을
보정하는 문제를 다룬다.

따라서 H001은 다음을 주장하지 않는다.

- visual-geometric witness 자체의 최초 제안
- broad open-vocabulary 3DSSG generation improvement
- relation generation model 또는 incomplete-supervision learning method
- 모든 relation family와 모든 baseline에 대한 일반 성능 향상

H001이 주장하는 것은 더 좁고 검증 가능한 범위다.

```text
For geometry-checkable 3DSSG relation families, semantic relation scores can be
miscalibrated with respect to physical consistency; calibrated geometry-
consistency scoring exposes this failure and can reduce geometric violations
while reporting the recall tradeoff.
```

## Current Paper State

Fact:

- Active venue source: `paper/aaai/`.
- Paper title: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D
  Scene Graph Relations`.
- Main source-result table now reports `K={5,10,20,50,100}` for Recall and
  Violation; `K=1` remains excluded by the frozen low-K protocol.
- Low-K sweep artifacts are ready under
  `experiments/H001_geom_reliability/k_sweep/`, with source metrics in separate
  `metrics_k_sweep/` roots so the locked `metrics/` outputs are not
  overwritten.
- Figure 1 has been redrawn as a three-panel evidence-record framework
  schematic; generated assets are
  `paper/generated/figures/figure1_framework.{svg,png}`.
- Latest Docker PDF build:
  `logs/h001_aaai_pdf_build_geocalib_figure_20260613_104500.log`, exit 0.
  `paper/aaai/main.pdf` has 9 pages, no LaTeX errors, missing citations, final
  undefined references, overfull hboxes, or Type 3 fonts.
- The previous flattened package
  `release/h001_aaai27_submission_20260613_004455/` predates the latest
  GeoCalib/Figure 1 pass and must be regenerated before upload.

Inference:

- The main metric story is stable enough for the current scoped AAAI paper.
  Remaining work is submission hygiene and release/supplement packaging, not a
  new core H001 experiment.
- Low-K results are useful as top-rank reliability evidence, especially for
  Open3DSG, but should be interpreted as part of the same recall-violation
  protocol rather than as a separate cherry-picked claim.

## Research Background

3D Scene Graph는 object node와 relation edge로 3D scene을 구조화하여 scene
understanding, spatial reasoning, alignment, grounding, navigation, planning,
robotics, VLM/LLM reasoning에 활용되는 representation이다. 3DSSG/3RScan은
indoor scene graph relation prediction의 대표적 benchmark이며, 기존 평가는
주로 predicate/triplet `R@K`, `mR@K`처럼 semantic label recall을 중심으로
이루어졌다.

최근 연구는 closed-set relation prediction에서 open-vocabulary relation,
language-aligned 3D feature, VLM 기반 scene reasoning, functional relation,
open-world graph representation으로 확장되고 있다. `VL-SAT`는 visual-
linguistic semantics assisted training을 통해 closed-set 3DSSG relation
prediction을 강화하고, Open3DSG는 queryable object와 open-set relationship을
다루며, Qwen-VL 같은 modern VLM은 image/crop 기반 semantic relation source로
활용 가능하다.

동시에 `RelWitness`처럼 relation-level visual-geometric witness와 calibrated
witness quality를 직접 다루는 최근 연구가 등장했다. 이 때문에 H001은
"geometry evidence를 쓴다" 또는 "witness를 쓴다"를 novelty로 삼으면 안 된다.
H001의 배경은 geometry-aware 3DSSG가 부족하다는 일반론이 아니라, relation
source가 이미 점수를 낸 이후에도 그 점수가 실제 object-pair physical
consistency를 잘 반영하는지는 별도로 검증되어야 한다는 점이다.

## Motivation

3D Scene Graph relation은 downstream system이 scene을 이해하고 행동하는
interface가 될 수 있다. 이때 relation edge가 semantic category 또는 language
prior 관점에서는 그럴듯하더라도, 실제 3D geometry와 맞지 않으면 graph는
spatial reasoning에 위험한 representation이 된다.

예를 들어 `chair standing on floor`, `object near table`, `lamp higher than
desk` 같은 relation은 단순히 object category 조합으로 plausible한지보다,
해당 subject-object instance pair의 실제 접촉, 거리, vertical ordering이
relation을 만족하는지가 중요하다.

기존 `R@K` 중심 평가는 top-k 안에 GT predicate가 들어오는지를 측정하지만,
top-k relation이 geometry-consistent한지, semantic score가 physical validity와
얼마나 calibration되어 있는지, 그리고 geometry-aware re-ranking이 recall을
얼마나 보존하면서 violation을 줄이는지는 직접 보여주지 않는다.

따라서 H001의 motivation은 다음 질문으로 정리된다.

```text
Can we evaluate and re-rank existing 3DSSG relation predictions using explicit
object-pair geometry so that semantically plausible but physically inconsistent
relations are exposed and reduced under a transparent recall-violation tradeoff?
```

## Limitation of Existing Work

기존 3DSSG 연구의 한계는 "geometry를 전혀 쓰지 않는다"가 아니다. 많은 방법이
point-cloud feature, edge feature, spatial prior, language feature,
semantic-geometric fusion을 이미 사용한다. H001이 문제 삼는 한계는 더
구체적이다.

첫째, standard relation prediction metric은 semantic recall 중심이다.
`R@50`, `R@100`, `mR@K`는 exact predicate label이 top-k 안에 있는지는
측정하지만, 그 relation이 same subject-object pair의 3D geometry에서 가능한지
직접 측정하지 않는다.

둘째, relation score가 physical consistency score로 calibration되어 있다는
보장이 없다. Open-vocabulary 또는 VLM 기반 source일수록 object category,
language prior, image evidence만으로 plausible relation을 높게 줄 수 있지만,
그 relation이 실제 3D scene에서 접촉, 거리, 상대 높이 조건을 만족하는지는
별도 문제다.

셋째, source마다 output format, object-pair identity, denominator, missing
context, candidate-pair coverage가 다르다. 동일한 reliability claim을 하려면
prediction row를 표준화하고, geometry join과 GT denominator를 명시해야 한다.

넷째, 단순한 geometry-only heuristic 또는 distance heuristic으로 충분한지
검증해야 한다. H001은 geometry signal을 사용하지만, geometry만으로 relation
prediction을 대체한다고 주장하지 않는다. semantic source score와 calibrated
geometry validity가 함께 필요하다는 점을 controls로 보여야 한다.

다섯째, `RelWitness`는 visual-geometric relation witness와 calibrated witness
quality를 이미 제안하므로, H001은 witness/calibration 자체를 novelty로 주장할
수 없다. H001의 차별점은 existing relation-source outputs에 대한
identity-preserving reliability evaluation/re-ranking protocol, denominator
discipline, `Violation@K`, source controls, and reproduced Docker evidence다.

## Problem Definition

입력은 3D scene, object instances, 그리고 relation source가 생성한 scored
relation predictions이다. 각 prediction은 다음 형태의 directed object-pair
relation row로 표준화된다.

```text
(source, scan_id, context_id, subject_id, object_id, predicate,
 predicate_family, semantic_score, rank, provenance)
```

문제는 각 prediction row에 대해 다음을 판단하는 것이다.

```text
Does this semantically scored relation hold for the same subject-object pair
under explicit 3D geometry evidence?
```

H001의 main scope는 geometry로 직접 검증 가능한 relation family에 제한된다.

| Family | Example predicates | Geometry evidence |
| --- | --- | --- |
| `support_contact` | `standing on`, `lying on`, `supported by` | contact/near-contact, vertical ordering, support-surface plausibility |
| `proximity` | `near`, `close to`, `next to` | object-pair distance, normalized distance, distance threshold/band |
| `relative_vertical` | `higher than`, `lower than`, `above`, `below` | signed vertical offset, z-extents, centroid/OBB vertical ordering |

현재 main claim에서 제외되는 범위는 다음과 같다.

- broad open-vocabulary 3DSSG generation
- arbitrary relation discovery
- functional/affordance relation generation
- full relative-horizontal claim
- attachment/hanging/connection relation의 main claim 승격
- robotics navigation 또는 downstream task 성능 향상

확장 후보는 별도 track으로 관리한다. `attachment_deferred`는 future physical
relation upgrade 후보이며, `relative_lateral`과 `relative_horizontal`은 현재
coordinate-frame ambiguity와 strict-purity issue 때문에 main claim으로
승격하지 않는다. Qwen-VL은 modern VLM semantic source extension이며,
full official validation metric은 완료됐지만 별도 승격 판단 전까지 main claim
source가 아니다.

## Core Hypothesis

H001의 핵심 가설은 다음과 같다.

```text
For geometry-checkable 3DSSG relation families, explicit object-pair geometry
evidence can identify relation predictions whose semantic confidence is
miscalibrated with physical consistency. Combining semantic score with
calibrated geometry validity can reduce geometry-inconsistent top-k relations
while preserving useful predicate/triplet recall.
```

이 가설은 세 부분으로 나뉜다.

1. Failure hypothesis:
   semantic score가 높은 relation 중 일부는 same object-pair geometry와
   모순된다.

2. Signal hypothesis:
   object-pair geometry에서 계산한 `p_geom_valid`는 GT-positive relation과
   deterministic counterfactual negative를 구분하는 reliability signal이다.

3. Re-ranking hypothesis:
   `semantic_score * p_geom_valid` 또는 family-specific geometry score를
   사용하면 semantic-only ranking보다 `Violation@K`를 낮출 수 있고, 이때
   `R@K` 손실 또는 이득을 명시적으로 보고할 수 있다.

이 가설은 "relation을 새로 생성한다"가 아니라 "이미 생성된 relation prediction
row의 reliability를 평가하고 보정한다"는 문제를 겨냥한다. 따라서 RelWitness와
같은 witness-supervised generator와 동일한 claim이 아니다.

## Proposed Framework

H001 framework는 단일 rule verifier가 아니라, relation-source output을 받아
geometry-consistency reliability를 계산하고 re-ranking/evaluation까지 수행하는
pipeline이다.

### 1. Source Adapter

각 baseline/source의 output을 공통 JSONL row contract로 변환한다.

Required fields:

- `source`: `vlsat_closed_set`, `open3dsg_ov`, `qwen_vl` 등
- `scan_id`, `context_id`: validation scene/context identity
- `subject_id`, `object_id`: 3DSSG/3RScan object instance identity
- `subject_label`, `object_label`
- `predicate`, `predicate_family`, `predicate_subtype`
- `semantic_score`: source가 제공하거나 rank에서 유도한 relation confidence
- `semantic_rank`: source-internal ranking
- `provenance`: checkpoint, split, output path, parser/runtime status

이 단계의 목적은 source별 내부 구현 차이를 제거하는 것이 아니라, 같은
object-pair와 같은 denominator에서 비교 가능하도록 row identity를 보존하는
것이다.

### 2. Identity-Preserving Geometry Join

각 prediction row를 동일한 `scan_id/context_id/subject_id/object_id`의 3D
geometry와 join한다. 이때 wrong object pair, shuffled geometry, missing view,
missing object mapping을 별도로 기록한다.

Geometry evidence includes:

- object OBB center, size, min/max z, vertical extents
- object point/mesh availability
- pair centroid distance and closest-point/contact distance
- subject-object vertical offset
- horizontal/vertical overlap indicators when available
- family-specific raw feature values
- geometry availability and failure reason

이 join이 H001의 핵심이다. geometry signal이 같은 object pair에 붙지 않으면,
relation reliability를 평가하는 것이 아니라 scene-level prior를 섞는 것이 되기
때문이다.

### 3. Family-Specific Geometry Evidence

각 predicate는 geometry-checkable family로 mapping된다.

`support_contact`:

- subject가 object 위에 있거나 object가 subject를 support하는지 확인한다.
- contact 또는 near-contact distance가 작아야 한다.
- subject bottom과 object top의 vertical order가 support direction과 맞아야
  한다.
- point/OBB 기반 evidence가 모두 불확실하면 `uncertain`으로 남긴다.

`proximity`:

- subject-object 거리, normalized distance, closest-point/OBB distance를
  계산한다.
- 가까운 relation은 threshold/band 안에 들어와야 한다.
- 너무 멀면 `violated`, boundary 영역이면 `uncertain`으로 둔다.

`relative_vertical`:

- subject와 object의 z-center, min/max z, vertical offset을 계산한다.
- `higher/above` 계열은 subject가 object보다 충분히 위에 있어야 한다.
- `lower/below` 계열은 반대 방향을 요구한다.
- vertical difference가 작거나 overlap이 커서 판단이 모호하면 `uncertain`으로
  처리한다.

### 4. Rule Verifier

Family-specific evidence를 `satisfied`, `violated`, `uncertain`으로 변환한다.
`rule_verified_point_subtype`은 가장 엄격한 diagnostic variant다. 이 variant는
violation을 거의 제거할 수 있지만, recall을 희생할 수 있으므로 default method가
아니라 strict upper-bound/diagnostic condition으로 보고한다.

### 5. Calibrated `p_geom_valid`

Hard rule만 사용하면 relation을 지나치게 prune할 수 있다. 따라서 H001은
train/train-dev-derived calibration rows와 deterministic counterfactual
negatives를 사용해 frozen calibrator를 만든다.

출력은 다음 확률이다.

```text
p_geom_valid = P(relation geometry is valid | family-specific geometry features)
```

사용 원칙:

- validation/test source-result를 보고 threshold를 조정하지 않는다.
- global calibrator와 family-specific calibrator를 분리해 보고한다.
- `p_geom_valid`는 hard validity label이 아니라 reliability score다.
- residual calibration risk가 있으므로 probabilistic, rule-verified,
  family-specific variants를 함께 보고한다.

### 6. Re-ranking / Filtering Conditions

동일한 source predictions에 대해 여러 condition을 비교한다.

| Condition | Scoring / selection rule | Purpose |
| --- | --- | --- |
| `semantic_only` | original semantic score/rank | source baseline |
| `probabilistic_recalibrated` | `semantic_score * p_geom_valid` | recall-preserving geometry-aware re-ranking |
| `rule_verified_point_subtype` | keep/rank only rule-satisfied rows, reject violated rows | strict zero-violation diagnostic |
| `family_specific_p_geom_valid` | family-specific calibrated geometry validity with semantic score | stronger family-aware operating point |
| `control_p_geom_valid_only` | `p_geom_valid` only | test whether geometry alone is sufficient |
| `control_distance_only` | distance-based score only | test simple distance heuristic |
| `control_shuffled_geometry` | semantic score with geometry score shuffled across rows | test whether geometry identity matters |
| `control_wrong_pair_geometry` | semantic score with geometry from a wrong object pair | test object-pair identity preservation |

### 7. Evaluation And Failure Analysis

The framework reports relation quality through both semantic recall and
geometry reliability.

- `R@K` for `K={5,10,20,50,100}`: exact-label predicate/triplet recall under
  fixed GT denominator.
- `Violation@K` for `K={5,10,20,50,100}`: fraction of top-k selected rows that
  are geometry-violated among geometry-checkable predictions.
- `K=1` is excluded from paper-metric consideration because it is too noisy and
  source-rank sensitive.
- recall-retention / violation-reduction tradeoff: whether violation reduction
  is achieved by simply pruning recall.
- GT verifier evaluation: GT-positive nonviolated rate, deterministic
  counterfactual negative nonsatisfied rate, `p_geom_valid` AUROC/AUPRC/Brier.
- bootstrap CI: subgraph-level confidence intervals for key deltas.
- failure rows: semantic confusion, geometry violation, uncertain evidence,
  source-denominator issue, preprocessing/context coverage issue.
- qualitative inspection: representative cases explaining when semantic
  plausibility and physical consistency diverge.

## Experiment Plan(Metric, Baseline)

### Validation Scope

Paper-facing main experiments use the full official `3DSSG_subset` validation
scope.

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| candidate directed pairs | 36,808 |
| GT rows | 11,254 |
| H001-family GT rows | 3,972 |
| target families | `support_contact`, `proximity`, `relative_vertical` |

The historical 127-scan scope is retained only as sensitivity/history and
should not be the main paper route.

### Baseline / Source Plan

| Source | Role | Current use |
| --- | --- | --- |
| `VL-SAT` | controlled reproduced anchor | main full-validation source; stable closed-set 3DSSG baseline |
| Open3DSG | open-vocabulary second-source evidence | main full-validation second source using selected recovery branch, with unmodified-source covered branch as sensitivity |
| Qwen-VL | modern VLM semantic-source extension | full official validation downstream metrics ready; appendix/extension evidence only for the current AAAI route |
| `semantic_only` | source-output baseline condition | original source score without geometry re-ranking |
| `probabilistic_recalibrated` | primary H001 re-ranking condition | semantic score multiplied by calibrated `p_geom_valid` |
| `rule_verified_point_subtype` | strict diagnostic | shows hard-rule violation removal and recall tradeoff |
| `family_specific_p_geom_valid` | family-aware operating point | tests whether family-specific calibration improves violation reduction |
| geometry/distance/shuffled/wrong-pair controls | nontriviality controls | defend against geometry-only, distance-only, and identity-free explanations |

Open3DSG must be reported with explicit provenance: the official preprocessing
route covers 533/548 contexts, while the selected paper-facing full-denominator
branch recovers 548/548 by lowering the visible-object gate to `min_visible=2`
and regenerating relaxed views for two scans. The recovery branch is useful
because it evaluates the full official validation denominator, but it must be
described as a recovery-policy variant rather than unmodified Open3DSG
preprocessing.

Qwen-VL now follows the same full official validation row contract, crop/view
coverage accounting, adapter export, geometry join, metric evaluation,
bootstrap CI, and failure analysis. Full-validation Qwen results support the
same H001 failure mechanism but remain third-source extension evidence by
default: semantic_only R@50/R@100 is `0.2815/0.3600`, probabilistic
recalibration improves this to `0.3215/0.3653`, and Violation@50 drops from
`0.1226` to `0.0795`. The recall level is much lower than VL-SAT/Open3DSG, so
Qwen should not replace the two main sources without a separate claim decision.

### Metrics

Main metrics:

- exact-label `R@K` for `K={5,10,20,50,100}`
- `Violation@K` for `K={5,10,20,50,100}`
- recall delta and violation delta against `semantic_only`
- subgraph bootstrap confidence intervals for key deltas

Verifier-validity metrics:

- GT-positive nonviolated rate
- deterministic counterfactual negative nonsatisfied rate
- `p_geom_valid` AUROC
- `p_geom_valid` AUPRC
- Brier score / calibration risk

Control metrics:

- `control_p_geom_valid_only` vs `semantic_only`
- `control_distance_only` vs `semantic_only`
- `control_shuffled_geometry` vs calibrated condition
- `control_wrong_pair_geometry` vs calibrated condition

Reporting requirements:

- Always report denominator: scans, contexts, directed pairs, GT rows,
  H001-family GT rows, source prediction rows, geometry-checkable rows.
- Always separate source metric evidence from preprocessing/runtime caveats.
- Always distinguish full official validation from historical 127-scan
  sensitivity.
- Do not promote Qwen-VL, attachment, relative-horizontal, or functional
  relation claims into the main paper unless they pass the same Docker,
  denominator, metric, control, bootstrap, and audit standard.
