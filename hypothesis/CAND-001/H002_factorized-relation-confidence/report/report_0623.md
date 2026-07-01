# H002 Report 0623

Date: 2026-06-23 KST

Scope: H002 `factorized-relation-confidence`

Target venue direction: AAAI 2027

## 1. 연구 주제 및 문제 정의

### 연구 주제

H002는 3D Scene Graph relation edge의 신뢰도를 단일 confidence score로 보지 않고,
다음 요소로 분해해 relation-level reliability를 다시 정의하는 연구 방향이다.

```text
semantic score != geometry validity != relation reliability
```

즉, relation source가 `chair close by table`, `picture hanging on wall`,
`cabinet attached to wall` 같은 relation을 높은 score로 예측했다고 해서 그 edge가 실제
3D scene geometry에서 성립한다고 보지 않는다. 반대로 source score가 낮더라도 geometry상
성립 가능성이 높은 relation이 있을 수 있다.

H002의 중심 문제는 다음이다.

```text
기존 3D Scene Graph relation source의 semantic confidence는
relation-level physical/geometric reliability와 충분히 분리되어 있는가?
```

### 문제 정의

Relation candidate를 다음과 같이 둔다.

```text
e = (subject, predicate, object)
```

H002는 edge `e`에 대해 세 질문을 분리한다.

```text
1. semantic plausibility:
   relation source가 이 edge를 얼마나 그럴듯하게 보는가?

2. geometry validity:
   observed 3D evidence가 이 predicate를 지지하는가?

3. relation reliability:
   semantic evidence, geometry evidence, coverage, uncertainty를 함께 볼 때
   이 edge를 신뢰 가능한 scene-graph relation으로 받아들일 수 있는가?
```

현재 RGA framework의 문제 정의는 양방향 mismatch를 포함한다.

| Case | H002 Interpretation |
| --- | --- |
| high semantic + high geometry | semantic score와 geometry가 모두 지지 |
| high semantic + low geometry | semantic overconfidence / unsafe relation |
| low semantic + high geometry | semantic underconfidence / missed relation / annotation sparsity |
| semantic high or low + uncertain geometry | evidence 부족 또는 ambiguous relation |
| unsupported/missing geometry | 현재 verifier/evidence coverage 밖의 relation |

중요한 점은 H002가 단순히 geometry rule을 relation prediction 뒤에 붙이는 연구가 아니라는 것이다.
핵심은 source가 제공하는 하나의 relation confidence를 그대로 믿지 않고, 그 내부에 섞인
semantic plausibility와 geometry validity를 분리해 relation reliability를 재구성하는 것이다.

### 현재 claim boundary

현재까지 확정 가능한 사실:

- H002는 `semantic score`, `geometry validity`, `coverage`, `uncertainty`,
  `relation reliability`를 분리하는 RGA framework를 정의했다.
- 기존 proxy target들은 대부분 target construction shortcut에 취약했다.
- 따라서 현재 병목은 posterior combiner가 아니라, 독립적인 reliability target 확보이다.
- multi-view/mesh evidence는 현재 model input이 아니라 label/audit confirmation evidence다.

아직 주장하면 안 되는 내용:

- factorized posterior가 relation reliability를 개선한다고 확정할 수 없다.
- 현재 label이 paper-level human-confirmed benchmark라고 주장할 수 없다.
- validation/test generalization은 아직 보이지 않았다.
- `attached to`, `hanging on`, `connected to`, `close by`, `left/right/front/behind` 전체를
  H002가 해결했다고 주장할 수 없다.

## 2. 연구 방향성 및 핵심 아이디어

### 핵심 방향

H002의 연구 방향은 `Relation-Geometric Agreement (RGA)`를 중심으로 한다.

RGA는 각 relation candidate를 다음 축 위에 배치한다.

```text
RGA(e) = {
  semantic_axis(e),
  geometry_axis(e),
  label_or_audit_axis(e),
  coverage_state(e),
  uncertainty_state(e),
  disagreement_score(e)
}
```

이때 `p_geom_valid`는 geometry-only continuous evidence이며, 최종 reliability score가 아니다.
H002가 궁극적으로 검증하려는 posterior는 다음 형태다.

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

여기서:

| Symbol | Meaning |
| --- | --- |
| `S_e` | semantic evidence: source score/rank, semantic plausibility |
| `G_e` | geometry evidence: distance, contact, overlap, vertical order, attachment witness |
| `C_e` | coverage evidence: geometry/view/mesh evidence가 충분한지 |
| `U_e` | uncertainty evidence: ambiguous, missing, unsupported, annotation-sparse 상태 |

### 핵심 아이디어

H002의 핵심 아이디어는 다음 네 가지로 요약된다.

1. RGA metric / benchmark:
   기존 relation recall/mAP만으로는 semantic score와 geometry validity의 mismatch를 볼 수 없다.
   RGA는 `RGA-HL`, `RGA-LH`, uncertain, unsupported/missing bucket을 분리해 mismatch를
   관측 가능하게 만든다.

2. Factorized relation reliability:
   단순 `semantic score * p_geom_valid`가 아니라, semantic, geometry, coverage, uncertainty를
   서로 다른 evidence factor로 취급한다. 이후 target-independence gate가 통과되면
   `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
   `factorized_reliability_posterior`를 비교한다.

3. Independent audit evidence:
   현재까지 반복에서 proxy label이 geometry summary, rank, predicate, object pair,
   machine hint 같은 shortcut에 쉽게 의존한다는 문제가 확인됐다. 따라서 multi-view/mesh는
   지금 model input이 아니라 label/audit confirmation evidence로만 사용한다.

4. Relation-family expansion with typed witnesses:
   `support_contact`, `relative_vertical`, `proximity`, `attachment_deferred`를 단계적으로
   검토했다. 현재 active empirical branch는 `attachment_deferred`이며, primary predicate는
   `attached to`, `hanging on`, diagnostic-only predicate는 `connected to`다.

### 현재 active branch

현재 active branch는 다음이다.

```text
attachment_deferred_independent_evidence_audit_packet_leakage_review
```

이 branch의 목적은 바로 label을 채우는 것이 아니라, label fill 전에 reviewer-visible audit packet이
construction metadata를 누출하지 않는지 확인하는 것이다.

현재 materialized packet은 두 evidence tier를 분리한다.

| Tier | Meaning | Current Count |
| --- | --- | --- |
| `T1_strong_pair_visual` | subject/object가 같은 frame visual context를 공유 | total 43, primary 31 |
| `T2_individual_visual_plus_mesh` | subject/object 개별 crop + mesh/sequence context | total 197, primary 129 |

T2는 직접적인 co-visible relation evidence가 아니라, object identity와 mesh/context를 확인하기 위한
audit evidence로 해석해야 한다.

## 3. 관련 연구 및 주요 베이스라인

### 3D Scene Graph 및 3DSSG 계열

사실: 3D Scene Graph는 object node와 relation edge를 통해 3D scene의 semantic/spatial structure를
표현하는 방향이다.

관련 primary sources:

- `3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera`,
  ICCV 2019 / arXiv 2019.
  Link: https://arxiv.org/abs/1910.02527
- `Learning 3D Semantic Scene Graphs from 3D Indoor Reconstructions`,
  3DSSG, arXiv 2020.
  Link: https://arxiv.org/abs/2004.03967
- 3DSSG project page.
  Link: https://3dssg.github.io/

H002와의 연결:

- 기존 3DSSG-style relation prediction은 relation edge에 score/rank를 부여한다.
- H002는 이 score가 relation reliability와 같은지 묻는다.
- 즉, H002는 새로운 scene graph backbone보다 relation confidence의 의미와 calibration을 다룬다.

### Closed-set / point-cloud based relation source

관련 primary source:

- `VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud`,
  CVPR 2023.
  Link: https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.html
  Code: https://github.com/wz7in/CVPR2023-VLSAT

H002에서의 baseline 역할:

- `VL-SAT`는 closed-set 3DSSG relation source로 볼 수 있다.
- H002에서는 relation source confidence/rank를 `S_e`로 사용하고,
  geometry evidence와의 mismatch를 RGA로 평가할 수 있다.

### Open-vocabulary 3D Scene Graph 계열

관련 primary sources:

- `Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships`,
  CVPR 2024 / arXiv 2024.
  Link: https://arxiv.org/abs/2402.12259
  Code: https://github.com/boschresearch/Open3DSG
- `ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning`,
  project page.
  Link: https://concept-graphs.github.io/
- `HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation`,
  arXiv 2024.
  Link: https://arxiv.org/html/2403.17846v2

H002와의 연결:

- Open-vocabulary relation source는 더 풍부한 relation text를 생성할 수 있지만,
  generated relation이 geometry상 검증 가능한지 별도 문제가 남는다.
- H002는 open relation을 typed geometry witness family로 나누고,
  relation reliability를 `semantic-geometry-coverage-uncertainty` 관점에서 평가할 수 있다.

### Online / incremental 3D scene graph construction

관련 primary sources:

- `Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction and Optimization`,
  arXiv 2022.
  Link: https://arxiv.org/abs/2201.13360
- `Incremental 3D Scene Graph Prediction from RGB-D Sequences`,
  arXiv 2021.
  Link: https://arxiv.org/abs/2103.14898

H002와의 연결:

- Hydra/online 3D scene graph 계열은 graph가 관측과 함께 갱신될 수 있음을 보여준다.
- H002가 relation reliability layer를 안정화하면, 이후 stale edge removal,
  relation update, graph repair로 확장할 수 있다.

### Calibration / uncertainty / selective prediction 관점

H002의 `semantic score != reliability` 주장은 confidence calibration 및 selective prediction과
직접 연결된다.

H002에서의 적용:

- `semantic_only`: source score/rank만 사용.
- `geometry_only`: `p_geom_valid` 또는 typed geometry witness만 사용.
- `semantic_plus_geometry`: semantic score와 geometry score의 단순 결합.
- `factorized_reliability_posterior`: semantic, geometry, coverage, uncertainty를 분리해 결합.
- `abstain / uncertainty`: evidence가 부족하거나 ambiguous한 row를 forced binary label로 만들지 않음.

### 주요 베이스라인

Target-independent label이 확보된 뒤 비교할 주요 baseline은 다음이다.

| Baseline | Meaning | Purpose |
| --- | --- | --- |
| `semantic_only` | relation source score/rank만 사용 | 기존 confidence가 충분한지 확인 |
| `geometry_only` | `p_geom_valid` 또는 typed witness만 사용 | geometry rule만으로 충분한지 확인 |
| `semantic_plus_geometry` | semantic과 geometry의 단순 결합 | factorization 필요성 확인 |
| `factorized_reliability_posterior` | `S_e, G_e, C_e, U_e` factor 결합 | H002의 핵심 method candidate |
| `wrong-pair geometry control` | 다른 object pair geometry를 붙임 | 실제 geometry를 보는지 확인 |
| `shuffled geometry control` | geometry evidence를 shuffle | spurious correlation 검증 |
| `same-family / same-rank-band control` | predicate/rank shortcut 통제 | target independence 검증 |

추가 combiner 후보:

- coverage-gated geometry model
- residual reliability model
- pairwise rank-matched ranking
- monotonic calibrated additive model
- product-of-experts / log-odds factor model
- relation-family mixture-of-experts
- debiased / orthogonalized factor model

단, 이들은 target-independence가 확보된 뒤에만 실험해야 한다.

## 4. 현재까지의 진행 상황

### 전체 진행 요약

H002는 여러 target construction route를 시도했고, 대부분 posterior로 바로 갈 수 없다는
negative evidence를 얻었다. 이 negative evidence는 실패가 아니라, relation reliability target이
얼마나 쉽게 shortcut에 오염되는지 확인한 과정이다.

현재까지의 핵심 stage 흐름:

| Stage Range | Main Focus | 결론 |
| --- | --- | --- |
| v1-v9 | RGA pilot, endpoint-pair counterfactual | exact pair 수량은 있으나 predicate/rank entanglement가 큼 |
| v10-v23 | `close by` / proximity LH-only branch | generality evidence로는 유용하나 primary posterior target은 아님 |
| v24-v36 | `support_contact`, `relative_vertical`, cross-stratum contrast | row count는 충분하나 geometry/status shortcut이 강함 |
| v37-v44 | `attachment_deferred` witness schema, candidate, label, audit | v18 label target은 positive-sparse + shortcut risk로 posterior 부적합 |
| v45-v48 | independent evidence repair, source inventory, audit packet plan/materialization | label fill 전 독립 visual/mesh audit packet 확보 중 |

### v18 attachment target 결과

v18은 `attached to`, `hanging on`, `connected to` relation을 다뤘다.

v18 label ingestion 이후:

```text
multiclass rows = 240
primary binary rows = 114
positive / negative = 33 / 81
connected diagnostic rows = 62
geometry-support rows = 154
quick-probe risk flags = 102
```

v18 target-independence audit 이후:

```text
relation binary = 114 rows
positive / negative = 33 / 81
strict clear slice = 0
diagnostic clear slice = 0
full quick-probe risk flags = 119
slice-level blocking risk flags = 3163
```

판단:

- v18은 H002 가설을 반박한 것이 아니라, current target construction이 posterior target으로
  부적합하다는 negative evidence다.
- 원인은 posterior combiner가 약해서가 아니라, label surface가 geometry/witness summary 및
  construction metadata에 너무 가까웠기 때문이다.

### v45-v48 independent evidence branch

v45 independent evidence repair plan:

```text
selected_route = independent_visual_or_mesh_audit_packet_before_labels
primary_scope = attached to, hanging on
diagnostic_scope = connected to
multi_view_as_model_input = false
posterior_smoke_allowed = false
```

v46 source inventory:

```text
rows = 240
primary_rows = 160
primary_both_have_crop_rows = 160
primary_audit_ready_rows = 160
unique_scans = 202
scan_exists = 202
multi_view_exists = 202
sequence_exists = 202
mesh_ready = 202
source_inventory_gate_pass = true
```

중요 caveat:

```text
T1_strong_pair_visual = 43 total / 31 primary
T2_individual_visual_plus_mesh = 197 total / 129 primary
```

즉, 대부분의 row는 direct same-frame co-visible evidence가 아니라
individual visual crops plus mesh/sequence evidence다.

v47 audit packet plan:

```text
rows = 240
primary_attachment_reliability_candidate = 160
connected_diagnostic_only = 62
uncertainty_or_coverage_audit_only = 18
visible schema leakage protection = pass
```

v48 audit packet materialization:

```text
visible_review_rows = 240
packet_dirs = 240
materialized_hidden_manifest_rows = 240
total_materialized_images = 4466
visible_leakage_hits = 0
validation_errors = 0
```

현재 next gate:

```text
reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review
```

### 현재 실험적으로 확인된 문제

1. Target construction shortcut:
   object pair, predicate, rank band, geometry status, machine hint, witness summary가 label을 쉽게 설명한다.

2. Positive sparsity:
   일부 proxy label에서는 binary usable row는 있어도 positive row가 부족하다.

3. Geometry-only target confusion:
   `geometry_support`는 class mass가 좋아도 relation reliability 자체를 대체하지 못한다.

4. Multi-view evidence의 이중성:
   visual evidence는 유용하지만, 바로 model input으로 넣으면 "extra visual feature로 성능이 오른 것"으로
   보일 수 있다. 따라서 현재는 audit/confirmation evidence로만 사용한다.

5. Relation-family별 난이도 차이:
   `close by`는 LH-only로 치우치고, `support_contact`는 geometry status shortcut이 강하며,
   `attachment_deferred`는 visual/mesh audit이 없으면 reliability label이 불안정하다.

## 5. 향후 실험 및 논문 작성 계획 (타겟 학회: AAAI 2027)

### 단기 TODO

1. Formal leakage review:
   v48 visible sheet, packet markdown, neutral image filenames에서 source path, scan id,
   instance id, geometry status, rank, machine hint, old label/review note가 노출되지 않는지
   독립적으로 확인한다.

2. Audit label protocol:
   `T1_strong_pair_visual`과 `T2_individual_visual_plus_mesh`를 분리한 label protocol을 만든다.
   `T2`는 direct co-visible relation evidence가 아니므로 더 보수적인 label state를 허용해야 한다.

3. Independent label fill:
   leakage review 통과 후에만 reviewer-visible packet 기반으로 label을 채운다.
   label candidates:

   ```text
   accept_reliable_attachment
   reject_unreliable_attachment
   abstain_uncertain
   diagnostic_connected_possible
   diagnostic_connected_ambiguous
   ```

4. Label ingestion and target-independence audit:
   label fill 후 hidden manifest와 join하고, predicate/rank/object/endpoint/evidence-tier shortcut을
   다시 audit한다.

5. Posterior smoke gate:
   target-independence gate가 통과할 때만 posterior smoke를 실행한다.

### 중기 실험 계획

Clean target이 확보되면 다음 비교를 수행한다.

```text
semantic_only
geometry_only
semantic_plus_geometry
factorized_reliability_posterior
wrong-pair geometry control
shuffled geometry control
same-family / same-rank-band control
```

필수 metric:

| Metric | Purpose |
| --- | --- |
| AUROC / AUPRC | relation reliability binary 또는 multiclass target 성능 |
| Brier / ECE | posterior calibration |
| invalid edge precision | unreliable edge 검출 |
| coverage-aware abstention | uncertain/unsupported를 잘 분리하는지 |
| shortcut-control delta | geometry/semantic factor가 shortcut이 아닌지 |
| RGA bucket transition | HL/LH/uncertain 상태가 어떻게 바뀌는지 |

Relation-family extension:

- Primary: `attached to`, `hanging on`
- Diagnostic: `connected to`
- Generality evidence: `close by`, `support_contact`, `relative_vertical`
- Future expansion: `left`, `right`, `front`, `behind`

### AAAI 2027 논문 framing

가능한 paper-level framing:

```text
Relation Confidence is Not Relation Reliability:
Factorized Semantic-Geometric Agreement for 3D Scene Graph Edges
```

핵심 contribution 후보:

1. Problem formulation:
   기존 3D Scene Graph relation confidence를 relation-level reliability와 구분하고,
   semantic-geometric mismatch를 양방향으로 정의한다.

2. RGA framework:
   `RGA-HL`, `RGA-LH`, uncertain, unsupported/missing state를 분리해 기존 relation recall/mAP가
   숨기는 failure mode를 측정한다.

3. Independent target construction protocol:
   shortcut-prone proxy labels를 배제하고, visual/mesh audit evidence와 deployable model input을
   분리하는 target construction gate를 제안한다.

4. Factorized reliability posterior:
   충분히 독립적인 target이 확보된 뒤 `S_e, G_e, C_e, U_e`를 결합해 relation reliability를 추정한다.

5. Controls and failure analysis:
   wrong-pair geometry, shuffled geometry, same-rank/family control, evidence-tier control로
   방법이 실제 relation reliability를 학습하는지 검증한다.

### AAAI 2027 reviewer-risk checklist

Reviewer가 물을 가능성이 높은 질문과 현재 대응 방향:

| Reviewer Question | Current Answer |
| --- | --- |
| 단순 geometry post-filter 아닌가? | H002는 geometry rule이 아니라 semantic, geometry, coverage, uncertainty를 분리한 reliability framework다. |
| label target이 geometry rule을 그대로 복사한 것 아닌가? | 현재는 그 위험을 인정하고, independent visual/mesh audit packet을 별도 gate로 만들고 있다. |
| multi-view를 넣어서 성능이 좋아진 것 아닌가? | 현재 multi-view는 model input이 아니라 label/audit confirmation evidence다. |
| `connected to`는 functional relation이라 geometry로 어려운 것 아닌가? | 현재 diagnostic-only로 유지한다. Primary claim은 `attached to`, `hanging on` 중심이다. |
| target construction 실패가 너무 많은 것 아닌가? | 이 실패 자체가 relation reliability target이 shortcut에 취약하다는 evidence이며, 최종 논문에서는 target-independence protocol의 필요성을 뒷받침한다. |
| validation/test 결과는? | 아직 없음. Hypothesis 단계는 train-only이며, target freeze 이후에만 validation/test로 이동한다. |

### 논문 작성 전 필수 gate

AAAI 2027 submission-level claim을 만들려면 다음이 먼저 필요하다.

1. v48 packet formal leakage review 통과.
2. independent audit labels 생성.
3. target-independence audit 통과.
4. posterior smoke에서 factorized model이 baseline 대비 의미 있는 gain을 보임.
5. wrong-pair / shuffled / same-rank control에서 gain이 유지됨.
6. train-only에서 method/target/protocol freeze.
7. validation 또는 held-out split에서 final metric report.
8. failure analysis와 qualitative packet examples 정리.
9. `connected to`를 main claim에서 제외하거나, 별도 functional-evidence protocol을 마련.

### 현재 판단

Inference:

현재 H002는 아직 posterior method claim 단계가 아니라, target construction과 evidence independence를
정리하는 단계다. 그러나 이 방향은 억지로 기존 결과를 끼워맞추는 것이 아니라, 반복적으로 드러난
문제 원인인 shortcut-prone reliability target을 원리적으로 해결하려는 흐름이다.

AAAI 2027 관점에서 가장 방어 가능한 claim은 다음 순서다.

```text
1. Relation confidence와 relation reliability는 다르다.
2. 이 차이는 RGA mismatch로 관측 가능하다.
3. 기존 proxy target은 shortcut에 취약하다.
4. 따라서 independent evidence 기반 target construction gate가 필요하다.
5. 그 target이 확보된 뒤 factorized posterior가 의미 있는지 검증한다.
```

현재 바로 주장 가능한 것은 1-4의 hypothesis-stage evidence이며, 5는 아직 다음 단계 실험이 필요하다.
