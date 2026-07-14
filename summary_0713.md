# RelCompat3D Paper Summary — 2026-07-13

이 문서는 2026-07-13 KST 기준 H001 paper의 연구 질문, method, experiment,
claim boundary, manuscript 상태를 한 번에 확인하기 위한 dated snapshot이다. 계속
변하는 canonical state는 `summary.md`와 `TODO.md`가 소유하며, 세부 수치와 재현
경로는 `results/h001_geom_reliability/report.md`와
`docs/reproducibility.md`를 따른다.

## 1. Executive Summary

- Paper title: **Beyond Semantic Confidence: Relation-Algebra-Constrained
  Compatibility for Reliable 3D Scene Graphs**
- Method name: **RelCompat3D**
- Target venue: **AAAI-27**
- Internal identifier: `H001` — manuscript-facing prose에서는 사용하지 않는다.
- 핵심 문제: 기존 relation predictor는 높은 semantic confidence를 부여하더라도,
  실제 ordered object pair의 3D geometry와 모순되는 relation을 상위에 배치할 수
  있다.
- 핵심 방법: source confidence와 predicate-conditioned geometric compatibility를
  분리해 학습하고, 같은 object pair의 geometry를 identity-preserving 방식으로
  결합한 뒤 기존 prediction을 재평가·재순위화한다.
- 핵심 novelty: 새로운 relation generator나 단일 fusion formula가 아니라,
  **factor-isolated post-source reliability layer, linked-counterfactual
  training, exact relation-algebra projection, 그리고 joint
  Recall–Violation–uncertainty contract**의 결합이다.
- 현재 근거: 고정된 3DSSG target에서 VL-SAT, Open3DSG, SGFN 세 source를 평가했다.
  Aggregate K=100에서 relation-algebra-constrained product는 세 source 모두에서 recall을 보존 또는
  개선하면서 verifier Violation을 낮춘다.
- 주요 한계: Violation은 independent human validity가 아니라 verifier-derived
  metric이고, support/contact는 family-wise regression이 있다. Dataset-level
  generalization은 최종 paper scope에서 제외했다.

현재 paper는 **source-level generalization을 보이는 scoped reliability paper**로
유지하는 것이 가장 강하면서 방어 가능한 상태다. SOTA relation generation,
universally best fusion, family-uniform improvement, dataset-level generalization은
주장하지 않는다.

## 2. Problem Definition

Relation candidate를 다음 identity-preserving row로 표현한다.

```text
e = (scan, context, subject_id, object_id, predicate, family, Z)
```

여기서 source relation score `Z`는 semantic plausibility나 source confidence를
나타내지만, 해당 predicate가 **그 ordered object pair의 실제 geometry와
일치하는지**를 명시적으로 보장하지 않는다. RelCompat3D가 다루는 failure는 다음과
같다.

```text
high semantic/source confidence
        +
predicate–geometry contradiction on the actual object pair
        =
semantically plausible but geometrically inconsistent relation
```

따라서 목표는 source model을 다시 학습하거나 graph를 새로 생성하는 것이 아니라,
geometry-checkable relation candidate에 대해 geometric compatibility를 추정하고
top-K ranking의 recall–reliability trade-off를 개선하는 것이다.

## 3. Method

### 3.1 Factor isolation

| Factor | 의미 | 사용 경계 |
| --- | --- | --- |
| `T_e` | predicate와 relation-family semantics | compatibility를 조건화할 수 있음 |
| `G_e` | 동일 ordered object pair의 predicate-independent raw geometry | source score, source identity 제외 |
| `Z_e` | source relation confidence | `C_e` 입력에서 금지 |
| `C_e` | `P(y_cal=1 \mid T_e,G_e)`로 추정한 calibrated compatibility | source-independent reliability factor |
| `S_e` | `F(Z_e,C_e)` | 최종 ranking 단계에서만 `Z_e`와 `C_e` 결합 |

핵심 leakage boundary는 다음과 같다.

```text
Z_e not in inputs(C_e)
```

`G_e`에는 pair distance와 scale, centroid/extent difference, OBB overlap,
point-level contact/support evidence가 포함된다. Predicate one-hot은 `T_e`,
predicate-signed vertical displacement와 같은 항목은 `T_e × G_e` interaction으로
분류한다. Source score, rank, source identity는 compatibility model에 넣지 않는다.

`y_cal`은 human physical-validity label이 아니다. Train/dev의 GT-positive rows와
high-margin counterfactual negatives로 구성한 calibration target이다. 현재 family
calibrator는 logistic model이며, training statistics로 feature를 표준화하고 고정된
optimizer 설정으로 학습한다.

### 3.2 Scoring conditions

| Condition | 정의 | Paper role |
| --- | --- | --- |
| Source score | 원래 source relation score | 기본 baseline |
| Family-calibrated product | `Z_e × C_e` | 주요 soft framework instantiation |
| Rank-average | context 내 `Z_e`와 `C_e` percentile rank의 평균 | scale-robust soft instantiation |
| Reciprocal Rank Fusion | fixed constant 60의 일반 rank fusion | strong comparator |
| Pooled-calibrator product | family를 구분하지 않은 compatibility product | family conditioning ablation |
| Hard geometry filter | rule-supported candidate만 유지 | zero-V diagnostic, proposed default가 아님 |
| Compatibility-only | `Z_e` 없이 calibrator만 사용 | no-source-score control; true G-only는 아님 |
| Distance-only | generic inverse-distance ranking | 단순 geometry heuristic control |
| Shuffled/wrong-pair geometry | geometry identity를 의도적으로 파괴 | identity-preserving join control |

Family product와 Rank-average는 **동등한 framework instantiation**으로 해석하지만,
모든 source와 K에서 둘 다 우월하다고 주장하지 않는다. Product는 작은 K에서도 더
안정적인 반면, rank fusion은 일부 K=100 operating point에서 더 강하다.

### 3.3 Falsification controls

- Wrong predicate: 동일 pair에서 inverse predicate를 넣었을 때 compatibility가
  감소하는지 확인한다.
- Wrong pair / shuffled geometry: 올바른 pair identity가 필요한지 확인한다.
- Close-by swap invariance: symmetric proximity relation의 endpoint swap을
  검사한다.
- Vertical inverse-equivariance: endpoint swap과 inverse predicate가 일관된지
  검사한다.
- Support/contact: 정확한 transformation rule 없이 blanket endpoint swap을
  적용하지 않는다.
- Factor audit: `T-only`, true `G-only`, additive `T+G`, interaction-aware
  `T×G`를 구분한다.

이 control들은 source score 복사, generic distance prior, 잘못된 object-pair join,
predicate를 무시한 geometry calibration이라는 단순 설명을 반증하기 위한 것이다.

## 4. Evaluation Contract

### 4.1 Main scope

- Main relation families:
  - `support_contact`
  - `proximity`
  - `relative_vertical`
- Official validation: 157 scans, 548 contexts
- Directed object pairs: 36,808
- 전체 GT relations: 11,254
- Main in-scope exact-label denominator: 3,972
- Family denominators:
  - support/contact: 1,816
  - proximity: 1,766
  - relative vertical: 390
- K grid: `{5, 10, 20, 50, 100}`
- Primary endpoint: K=100
- Canonical secondary endpoint: K=50
- Top-ranked operational endpoint: K=10

`has_in_scope_GT`는 ranking, filtering, routing에 사용하지 않고 Recall 계산에서만
참조한다. GT가 없는 context도 Violation 평가와 548-context paired bootstrap에
그대로 포함한다. Context에 prediction이 100개보다 적더라도 synthetic candidate를
추가하지 않는다.

### 4.2 Sources

| Source | 역할 | Candidate rows |
| --- | --- | ---: |
| VL-SAT | controlled closed-set reproduced anchor | 957,008 |
| Open3DSG | main open-vocabulary relation-source case study | 695,916 |
| SGFN `full_l160` | additional exact-label source evaluation | 957,008 |

Open3DSG는 selected official non-averaged checkpoint를 사용한다. Recovery branch는
548/548 contexts를 포함하며, unmodified public pipeline의 533/548 coverage는
sensitivity/provenance로 공개한다. 이 결과는 Open3DSG leaderboard reproduction이나
SOTA 주장을 위한 것이 아니다.

### 4.3 Split firewall and uncertainty

- Scan firewall: 1,061 train / 117 internal-dev / 157 final-validation
- Split overlap: 0
- Feature normalization과 model fitting: train-only
- Internal-dev: diagnostic와 사전 정의된 acceptance 확인에만 사용
- Final-validation: fitting row 0, locked model/score로 benchmark evaluation
- Source별 temperature, threshold, lambda, normalization 재조정 금지
- Paired uncertainty: 동일한 548-context bootstrap index를 모든 condition에 공유,
  1,000 resamples

Primary `V@K`는 selected row 중 verifier status가 `violated`인 비율이다. 추가로
decidable-only V, uncertainty rate, uncertainty를 violation으로 계산한 pessimistic V,
status coverage를 함께 보고한다. 세 source 모두에서 Family product가 K=100의
decidable-only V, uncertainty rate, pessimistic V를 낮췄으므로 aggregate V 개선은
uncertain row를 단순 승격한 결과가 아니다.

## 5. Main Results

### 5.1 Framework-level K=100 comparison

| Source | Condition | R@100 | verifier V@100 |
| --- | --- | ---: | ---: |
| VL-SAT | Source score | 0.9635 | 0.0476 |
| VL-SAT | Family product | 0.9683 | 0.0333 |
| VL-SAT | Rank-average | 0.9597 | 0.0259 |
| VL-SAT | RRF | 0.9698 | 0.0251 |
| Open3DSG | Source score | 0.5161 | 0.1242 |
| Open3DSG | Family product | 0.6047 | 0.0341 |
| Open3DSG | Rank-average | 0.6052 | 0.0532 |
| Open3DSG | RRF | 0.6196 | 0.0789 |
| SGFN | Source score | 0.9235 | 0.0630 |
| SGFN | Family product | 0.9416 | 0.0381 |
| SGFN | Rank-average | 0.9476 | 0.0277 |
| SGFN | RRF | 0.9192 | 0.0284 |

핵심 해석은 다음과 같다.

- Open3DSG에서 Family product는 R@100을 `0.5161 → 0.6047`로 높이고 V@100을
  `0.1242 → 0.0341`로 낮춘다. Paired delta는 dR `+0.0886`
  `[+0.0669,+0.1096]`, dV `-0.0901` `[-0.0949,-0.0853]`이다.
- VL-SAT는 이미 recall이 포화에 가깝다. Product는 R@100을
  `0.9635 → 0.9683`, V@100을 `0.0476 → 0.0333`으로 바꾼다.
- SGFN에서 Product는 R@100을 `0.9235 → 0.9416`, V@100을
  `0.0630 → 0.0381`로 바꾸며 joint criterion을 통과한다. Rank-average도
  R/V `0.9476/0.0277`로 같은 K=100 framework gate를 만족한다.
- 두 soft instantiation이 함께 gate를 만족한다는 주장은 **SGFN K=100**에만
  적용한다. 작은 K에서 지속되는 trade-off 개선은 Product에 한정해 표현한다.
- RRF의 결과는 source-dependent하다. VL-SAT K=100에서는 강하지만 Open3DSG에서
  Product보다 V가 높고, SGFN에서는 recall guard를 만족하지 못한다.

### 5.2 Strong nonlinear baseline

69-parameter source-supervised nonlinear rescorer는 SGFN에서 R/V를 K=10
`0.5441/0.0120`, K=50 `0.8681/0.0186`, K=100 `0.9466/0.0279`로 만든다. 이
baseline은 exact source-specific development labels와 source confidence를 사용해
RelCompat3D보다 supervision이 강하다. 결과적으로 다음 표현은 금지된다.

- Family product가 가장 좋은 rescorer라는 주장
- 새 scoring formula 자체가 핵심 novelty라는 주장
- Product가 모든 strong fusion보다 우월하다는 주장

대신 `Z`를 compatibility 학습에서 배제한 source-independent factorization과 joint
evaluation framework를 contribution으로 둔다.

### 5.3 Family heterogeneity

Aggregate 개선은 family-uniform하지 않다. SGFN의 support/contact verifier V는
`+0.00450` `[+0.00370,+0.00532]` 증가하고, 같은 방향이 VL-SAT과 Open3DSG에서도
관찰된다. Proximity와 relative vertical, 그리고 global top-K의 family composition
변화가 전체 개선을 주로 만든다. 따라서 다음을 명시한다.

- support/contact solved claim 금지
- every-family improvement claim 금지
- aggregate와 within-family/global-top-K slice를 함께 공개

## 6. Secondary and Diagnostic Evidence

### 6.1 Relative size

`bigger than` / `smaller than`을 별도 `relative_size` family로 평가했다.

- 기존 1,061/117/157 firewall과 548 contexts 유지
- Size GT denominator: 170
- Four-family denominator: 4,142
- Source score/rank/object class/final-validation label을 `C_e`에서 제외
- Learned input과 verifier가 정확히 같은 rule을 재사용하지 않도록 disjoint point
  subsets와 서로 다른 robust extent estimator 사용
- Wrong predicate, endpoint swap + inverse predicate, common-scale invariance,
  wrong pair, shuffled geometry, OBB-only, point-only controls 수행

Four-family K=100 `(dR,dV)`는 VL-SAT `(+0.00483,-0.02393)`, Open3DSG
`(+0.06977,-0.10402)`, SGFN `(+0.02559,-0.03590)`이며 paired CI gate를 모두
통과한다. 그러나 fixed robust-point rule이 learned product와 같거나 더 강하고,
decidable GT에서 rule agreement가 1.0이다. 따라서 relative size는 main claim의
핵심 learned-method 증거가 아니라 **main text의 scope 확장 한 문장과 supplement의
full result**로만 사용한다.

### 6.2 ReplicaSSG/FROSS transfer

ReplicaSSG/FROSS는 `untouched prospective confirmation`이 아니라
**cross-dataset transfer stress test and development diagnostic**이다.

- Initial K=100 Source R/V: `0.3605/0.1967`
- Family product: `0.3605/0.1967` — 변화 없음
- Rank-average: `0.3314/0.0384` — V는 크게 감소하지만 recall guard 실패
- Bounded-fusion development의 all-scene 결과는 `0.3547/0.0393`이지만,
  leave-one-scene-out은 `0.3198/0.0384`이고 recall guard를 통과하지 못함

이 결과는 raw-product score-scale sensitivity, K=100 context saturation,
excessive rank displacement, geometry representation shift, ontology imbalance를
드러낸다. Dataset-level generalization claim은 현재 차단되어 있다.

### 6.3 Attachment subtype redesign v2

Attachment는 predicate semantics, physical mechanism,
observability/applicability를 분리하는 taxonomy로 재설계했다.

- Migrated train/dev rows: 761
- Direct bidirectional compatibility rows: 74,433
- Positive-only rows: 19,287
- Abstained rows: 97,002
- `connected to`는 direct/mediated ontology가 불분명해 neutral/positive-only로 처리
- Blanket endpoint swap 금지

Retrospective bounded diagnostic은 VL-SAT K=100만 통과하며 Open3DSG K=100과
VL-SAT K=50에서 실패한다. 또한 V가 legacy attachment policy를 사용한다. 따라서
attachment는 main paper contribution이나 relation-family scope에 포함하지 않는다.
향후 promotion에는 100-row mechanism review, target/verifier rebuild, train/dev
support 확인, 새로운 model/score hash lock이 필요하다.

### 6.4 Other branches

- Qwen-VL: full official-validation downstream은 완료됐지만 third-source / modern
  VLM extension으로 유지하며 active main claim에는 넣지 않는다.
- Relative horizontal/lateral: control gate를 통과하지 못해 main claim 밖에 둔다.
- Codex LLM proxy: 두 blinded pass는 non-submission diagnostic에만 보존한다. Active
  AAAI paper와 submission bundle에는 포함하지 않는다.
- Human validity: 488-item protocol과 evaluator는 준비됐지만 independent human
  reference는 아직 없다. Human V@K를 주장하지 않는다.
- H002: 별도 hypothesis/paper branch이며 H001 manuscript와 evidence를 섞지 않는다.

## 7. Contributions and Claim Boundary

### 7.1 Paper contributions

1. **Failure and evaluation:** semantic confidence가 actual ordered-pair
   geometry consistency를 보장하지 않는 post-source failure를 정의하고,
   exact-label Recall, verifier Violation, uncertainty, coverage를 함께 측정한다.
2. **Factor-isolated reliability layer:** `T`, predicate-independent `G`, source
   confidence `Z`, compatibility `C`를 분리하고 `Z not in C`를 강제하며,
   identity-preserving geometry join과 falsification controls를 제공한다.
3. **Scoped empirical evidence:** VL-SAT, Open3DSG, SGFN 세 predictor에서 고정된
   geometry-identifiable 3DSSG target의 source-level generalization을 보이고,
   family heterogeneity와 cross-dataset transfer failure를 숨기지 않는다.

### 7.2 허용되는 main claim

> For geometry-checkable 3D Scene Graph relation families, RelCompat3D exposes
> and reduces semantically plausible but geometrically inconsistent relation
> predictions through a factor-isolated post-source reliability layer, while
> explicitly reporting recall, verifier-violation, uncertainty, and coverage
> trade-offs.

Framework instantiation에 관한 허용 문장은 다음 수준이다.

> At the frozen K=100 SGFN endpoint, both the calibrated product and a
> pre-specified parameter-free rank fusion satisfy the joint recall–violation
> criterion, showing that the aggregate benefit is not tied to a single fusion
> formula. The calibrated product additionally preserves the trade-off across
> smaller operating budgets.

### 7.3 금지되는 claim

- New 3D Scene Graph generator 또는 broad open-vocabulary generation improvement
- 3DSSG SOTA / Open3DSG leaderboard reproduction
- Universally best scoring formula 또는 best rescorer
- 모든 source, family, K에서 recall과 V 동시 개선
- Support/contact 해결
- Independent human physical validity 또는 Human V@K
- Arbitrary-source / arbitrary-dataset generalization
- ReplicaSSG/FROSS prospective confirmation
- Relative size를 learned-method superiority의 핵심 증거로 사용
- Attachment, relative horizontal/lateral, Qwen-VL을 main claim으로 자동 승격

## 8. Reviewer-Risk Assessment

### 8.1 Construct validity — 미해결

Compatibility target과 Violation verifier가 일부 engineered geometry primitives를
공유한다. Wrong-predicate, wrong-pair, swap/inverse controls와 uncertainty sensitivity는
단순 자기복제를 완화하지만 independent construct validity를 완성하지 않는다.
Human alignment 또는 독립 측정 기반 validity study가 있으면 가장 직접적으로
보강되는 부분이다.

### 8.2 Novelty ceiling — 관리 가능하지만 제한적

Reviewer가 방법을 “engineered geometry feature를 사용한 calibration/reranking”으로
축소 해석할 수 있다. 방어 포인트는 단일 product formula가 아니라 다음 묶음이다.

- post-source reliability problem formulation
- source-confidence leakage boundary
- identity-preserving same-pair geometry join
- `T/G/Z/C` factor isolation
- wrong-predicate/wrong-pair/transformation falsification
- Recall–Violation–uncertainty–coverage joint evaluation

Strong nonlinear baseline 때문에 formula optimality는 주장할 수 없지만, 그 대신
source-independent compatibility와 source-specific rescorer의 supervision boundary를
명확히 비교한다. 2026-07-13 Docker development에서는 여섯 structured candidate 중
linked-counterfactual margin + exact orbit projection만 frozen gate를 통과했다. 이
model은 main compatibility로 승격되었고 proximity swap과 vertical inverse error를 정확히 0으로 만들면서
VL-SAT/Open3DSG/SGFN의 K=100 Recall continuity를 유지한다. 또한 SGFN-supervised
nonlinear rescorer를 VL-SAT/Open3DSG에 그대로 적용하면 낮은 K에서 Recall이 크게
감소한다. 따라서 novelty는 generic recalibration보다 강해졌지만, best-rescorer나
first constraint-refinement claim은 여전히 금지된다.

### 8.3 Generalization — 3DSSG source-level로 확정

세 predictor에 대한 결과는 같은 fixed 3DSSG target에서 source-level generalization을
지지한다. Dataset-level generalization은 active contribution이 아니며,
ReplicaSSG/FROSS는 submission에서 제외된 archived development provenance다.

### 8.4 Family nonuniformity — 반드시 공개

Support/contact regression을 aggregate 평균으로 가리면 reviewer 신뢰가 크게
떨어진다. Main text와 supplement에서 within-family result와 global-top-K family
composition을 함께 유지해야 한다.

## 9. Manuscript State

### 9.1 Structure

Active paper는 다음 6-section 구조다.

1. Introduction
2. Related Work
3. Method
   - Problem Setup
   - Factor-Isolated Geometric Compatibility
   - Re-ranking and Falsification Controls
4. Experiments
   - Experimental Setup
   - Cross-Source Results
   - Strong Comparisons and Diagnostics
   - Qualitative Analysis
5. Discussion and Limitations
6. Conclusion

서술은 `observed failure → structural cause → factor-isolation necessity → method →
evidence → scope and limitations` 순서를 따른다.

### 9.2 Figures

- **Figure 1:** 실제 Open3DSG high-confidence failure에서 시작해 identity-preserving
  row, `T/G/Z/C` factorization, `Z not in C`, compatibility scoring, re-ranking,
  falsification controls, joint evaluation으로 이어지는 four-stage pipeline.
- **Figure 2:** VL-SAT/Open3DSG/SGFN의 K=`{5,10,20,50,100}`
  Recall–Violation trajectory. K=100 primary, K=50 secondary, K=10 operational.
- **Figure 3:** 큰 point-cloud view를 사용한 성공 correction 2개와 residual
  support/contact failure 1개. Source/compatibility score와 rank 변화 포함.

### 9.3 Verified PDFs

| Artifact | Pages | SHA-256 |
| --- | ---: | --- |
| `paper/aaai/main_aaai27.pdf` | 9 | `4a85b126deba1ce6206d2de39fdc77f5a57a0efa33bcc3a59c25d9b90903ee4f` |
| `paper/aaai/supplement_aaai27.pdf` | 3 | `0ce55c91db031a19b6fb8b4044b1659757e4eac8448d6605250c5d0b9e0706e0` |
| `paper/aaai/reproducibility_checklist_aaai27.pdf` | 2 | `3f833f615d895d9022d36855072f0349f1e013adfc0aca191e8c76cfdcb22d5e` |

Main paper는 US-Letter 9 pages이며 technical content는 page 7까지, page 8–9는
references only다. 세 PDF 모두 Type 3 font, unresolved citation/reference,
blocking LaTeX error, overfull box가 0이다.

Codex-derived validity result는 active submission에 없다. 해당 분석은
`paper/paper_nonsub/`에만 격리되어 있다.

## 10. Artifact Map

| 역할 | Canonical path |
| --- | --- |
| Current research story | `summary.md` |
| Mutable task board | `TODO.md` |
| Paper workspace map | `paper/README.md` |
| Paper handoff snapshot | `paper/preview.md` |
| Reviewer risks | `paper/risk.md` |
| Figure contract | `paper/figures.md` |
| Active AAAI source | `paper/aaai/` |
| Compact paper-facing results | `results/h001_geom_reliability/` |
| Main experiment runbook | `experiments/H001_geom_reliability/README.md` |
| Exact experiment commands | `experiments/H001_geom_reliability/commands.md` |
| Train-only reconstruction | `experiments/H001_geom_reliability/train_only_reestablishment_v1/` |
| Factor-isolation protocol | `experiments/H001_geom_reliability/factor_isolation_protocol/` |
| Relative-size extension | `experiments/H001_geom_reliability/relative_size_v1/` |
| Attachment v2 diagnostic | `archive/experiments/H001_geom_reliability/sources/attachment_deferred/subtype_redesign_v2/` |
| Recovery/cleanup runbook | `docs/reproducibility.md` |
| Historical hypothesis records | `archive/hypothesis_records/hypothesis/` |

## 11. Remaining TODO

### Submission-critical

1. 완료: current three PDFs와 focused anonymized code/data artifact를
   `release/h001_aaai27_openreview_20260713_233949/`에 묶고 outer/inner
   checksum, archive extraction, structured manifest, author-path 검증을
   통과했다. 2026-07-12 bundle은 superseded snapshot이다.
2. OpenReview author order와 profile 연결, countries, conflicts, qualified
   reciprocal reviewer를 입력한다.
3. Title, TLDR, topics/keywords, public code license, post-acceptance artifact
   URL을 최종 확정한다.
4. 최종 PDF/source lock 뒤 main/supplement/checklist와 field metadata의 title,
   anonymity, page count, references, figures, artifact URL을 한 번 더 대조한다.

### Optional scientific strengthening

1. 가장 큰 미해결 위험은 independent construct validity다. 이를 실제로 닫으려면
   frozen 488-item protocol에 두 independent human annotations와 blinded
   adjudication을 채우고, 최종 human reference에 대해 Human V@K 및 Codex–human
   alignment를 계산해야 한다.
2. Attachment를 확장하려면 현재 validation diagnostic을 더 tuning하지 말고,
   mechanism review와 rebuilt verifier를 완료한 뒤 train/internal-dev에서 새 model과
   score를 lock하고 별도 evaluation을 수행한다.
3. 완료: projected pairwise candidate를 main method로 승격하고 strict
   train-only route 하나에서 rank-average, RRF, pooled, hard-filter,
   compatibility-only, uncertainty, family-wise CI, Figures 1--3를 모두
   재생성했다. Historical family product는 continuity reference로만 남는다.

현재 scoped RelCompat3D claim을 유지하는 데 새로운 main-source metric experiment는
필수적이지 않다. 제출 전 우선순위는 **OpenReview author metadata 완성 → final
public license/artifact URL 결정 → live-form cross-file consistency audit**이다.
