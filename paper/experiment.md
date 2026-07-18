# RelCompat3D Experiment Guide

Last updated: 2026-07-17 KST

이 문서는 현재 논문의 experiment가 어떤 질문을 검증하고, 어떤 조건을 같은
기준으로 비교하며, Recall과 Violation을 어떻게 계산하는지를 설명한다. Code
directory 이름이나 연구 과정의 condition key 대신 paper-facing 이름만 사용한다.
정확한 실행 명령과 artifact path는 `docs/reproducibility.md` 및
`experiments/H001_geom_reliability/README.md`가 소유한다.

## 1. 실험이 답하려는 질문

### Q1. 원래 source relation score에는 geometric inconsistency가 남아 있는가?

Source ranking의 top-K에서 verifier-derived Violation을 측정한다. 높은 source
relation score만으로 실제 same-pair geometry와 맞는 관계가 보장되는지 확인한다.

### Q2. Compatibility re-ranking이 Violation만 낮추고 Recall을 잃는가?

Source ranking과 RelCompat3D ranking을 동일 candidate, context, K, GT
denominator에서 비교한다. Recall과 Violation을 반드시 함께 본다.

### Q3. 단순한 fusion이나 더 큰 model로 같은 결과를 얻을 수 있는가?

Rank-average, Reciprocal Rank Fusion, 같은 supervision을 받는 nonlinear model,
Pooled product, Product (all families)를 비교한다.

### Q4. 결과가 predicate, pair identity, geometry를 실제로 사용하는가?

Wrong predicate, Wrong pair, Shuffled geometry, Fixed-label swap,
Distance only, No source score control을 같은 family-aware re-ranking으로 비교한다.

### Q5. Support/contact까지 같은 방식으로 바꿔도 되는가?

모든 family에 product를 적용한 결과와 proximity/vertical만 re-ranking한 결과를
비교한다. Support/contact regression이 발생하는지 family별로 확인한다.

### Q6. 특정 threshold나 verifier scalar를 그대로 재현한 것인가?

Negative 생성 threshold를 바꿔 다시 학습하고, verifier가 사용하는 exact
measurement 또는 관련 measurement family를 제거한 model을 비교한다.

## 2. Data split과 information firewall

| 역할 | scans | 사용 목적 |
| --- | ---: | --- |
| training | 1,061 | target 생성, normalization, missing-value 처리, model fitting |
| internal development | 117 | model design, relation transformation, family scope 결정 및 diagnostic |
| final evaluation | 157 | 최종 Recall/Violation 및 paired interval 계산 |

Final evaluation 정보는 feature normalization, target generation, parameter
fitting에 사용하지 않는다. Ground truth는 final evaluation에서 Recall을 계산할
때만 사용하며 candidate를 filter하거나 rank하는 데 사용하지 않는다.

## 3. Evaluation target

- dataset/geometry: shared 3DSSG/3RScan final-validation target.
- scans: 157.
- relation contexts: 548.
- exact-label ground-truth denominator: 3,972.
- evaluated families:
  - proximity.
  - relative vertical order.
  - support/contact.
- reported budgets: K=`{5,10,20,50,100}`.
- candidate가 K개보다 적은 context에는 synthetic candidate를 추가하지 않는다.

세 relation predictor를 평가한다.

| predictor | 역할 |
| --- | --- |
| VL-SAT | 강한 closed-set relation predictor |
| Open3DSG | open-vocabulary relation-source case |
| SceneGraphFusion (SGFN) | online/incremental 3D scene-graph predictor |

세 predictor가 서로 다른 candidate score를 제공하지만 geometry, ontology,
evaluation target은 공유한다. 따라서 이 실험은 **세 predictor가 shared target에서
보이는 behavior**를 평가하며 cross-dataset generalization을 증명하지 않는다.

Open3DSG는 public preprocessing에서 candidate가 생성되지 않은 official context도
548-context target에 남기고 empty candidate list로 평가한다. 이렇게 해야 GT가
있는 context만 선택하는 bias를 피할 수 있다. Candidate가 제공된 context만 따로
평가한 결과와 추가 preprocessing으로 모든 context의 candidate를 구성한 결과는
supplement sensitivity다.

## 4. 비교 조건

### 4.1 기본 비교

#### Source

원래 predictor의 source relation score \(Z\) 내림차순이다. Geometry
compatibility를 추가하지 않는 기준점이다.

#### RelCompat3D

- proximity와 vertical: transformation-averaged compatibility와 source relation
  score의 product \(ZC\)로 relation-family 내부를 정렬한다.
- support/contact: source order로 유지한다.
- source ranking의 relation-family sequence를 그대로 유지한다.

이 조건이 paper의 RelCompat3D ranking rule이다.

### 4.2 같은 family-aware re-ranking을 사용하는 강한 비교군

아래 방법은 모두 같은 family sequence와 support/contact source order를 사용한다.
차이는 proximity/vertical 내부의 결합 score뿐이다.

| 이름 | 결합 방식 | 확인하는 질문 |
| --- | --- | --- |
| Matched MLP | T, G, T×G를 입력으로 하는 작은 nonlinear compatibility model | linear model보다 capacity가 큰 model이 항상 우월한가? |
| Rank-average | source percentile rank와 compatibility percentile rank의 평균 | raw score scale 차이 없이도 같은 효과가 나는가? |
| RRF | source rank와 compatibility rank의 reciprocal-rank 합 | 일반적인 rank fusion이 더 강한가? |

Matched MLP는 RelCompat3D와 같은 training examples, constructed labels, split,
source-score exclusion을 사용한다. 따라서 label advantage가 아니라 model capacity를
비교한다.

### 4.3 Mechanism과 scope를 확인하는 비교

#### Product (all families)

\(ZC\)를 support/contact까지 모든 family에 적용한다. Main table에서는
`Product (all families)`로 표기한다. Aggregate Recall이 커질 수 있지만
support/contact selection이 바뀌고 Violation이 악화될 수 있다. RelCompat3D가
family-aware re-ranking을 사용하는 이유를 확인한다.

#### Pooled product

Family별 model 대신 모든 family에 하나의 compatibility model을 사용한다.
Family-specific geometry interpretation이 필요한지 확인한다.

#### Hard geometry filter

Verifier가 violated 또는 unsupported로 판단한 candidate를 제거한다. Violation이
0이 되는 것은 구성상 당연하며, K보다 적은 candidate를 반환할 수 있다. Soft
re-ranking의 강한 대안이 아니라 Recall--coverage trade-off를 보여주는 diagnostic이다.

#### Exact-label nonlinear rescorer

SGFN exact-label correctness를 직접 supervision으로 사용하는 더 강한 model이다.
RelCompat3D와 supervision이 다르므로 apples-to-apples baseline이 아니라 source-
specific upper comparison이다.

## 5. Falsification과 information ablation

모든 main control은 Source와 동일한 candidate universe, public/full 548-context
target, 같은 family-aware re-ranking을 사용한다.

| control | 실제로 바꾸는 것 | 결과가 나빠질 때 지지되는 해석 |
| --- | --- | --- |
| Wrong predicate | 동일 pair에서 다른/inverse predicate로 compatibility 계산 | model이 predicate meaning을 사용함 |
| Wrong pair | 다른 object pair의 geometry를 연결 | instance identity가 필요함 |
| Shuffled geometry | geometry를 context/candidates 사이에서 섞음 | geometry distribution만으로 충분하지 않음 |
| Fixed-label swap | subject/object를 바꾸되 predicate label은 유지 | vertical direction이 중요함 |
| Distance only | geometry를 pair distance 하나로 축소 | method가 단일 distance threshold가 아님 |
| No source score | compatibility만으로 ranking | geometry가 source relation score를 대체하지 않음 |

Proximity는 endpoint swap 후에도 predicate가 같아야 한다. Vertical은 endpoint
swap과 동시에 `higher than`/`lower than`을 뒤집어야 한다. Support/contact에는
일괄 endpoint-swap control을 적용하지 않는다.

추가 factor ablation:

- predicate only.
- predicate-independent geometry only.
- predicate와 geometry의 additive combination.
- predicate-conditioned geometry interaction.

이 비교는 compatibility가 어느 factor를 사용하는지 확인한다. Main result의
ranking comparison과 분리해 development diagnostic으로 해석한다.

## 6. Top-K selection

각 context \(c\)에서 Source는 \(Z\)로 전체 candidate를 정렬한다. RelCompat3D와
matched fusion baselines는 source-ranked relation-family sequence를 유지하면서
proximity/vertical 내부만 각 결합 score로 다시 정렬하고, support/contact는 source
order로 유지한다. 이렇게 얻은 condition \(m\)의 상위 K개를
\(L_K^{(m)}(c)\)라고 한다. K보다 candidate가 적으면 존재하는 candidate만 선택한다.

Tie는 deterministic instance/predicate identity order로 해결해 모든 condition과
bootstrap replicate에서 같은 입력이 같은 결과를 내게 한다.

## 7. Recall@K

Context \(c\)의 exact-label ground-truth set을 \(Y_c\)라 하면

\[
\mathrm{Recall@K}
=\frac{\sum_c |L_K(c)\cap Y_c|}
{\sum_c |Y_c|}.
\]

현재 denominator는 모든 source와 condition에서 3,972로 고정된다.

Exact-label match는 subject ID, object ID, predicate label이 모두 같아야 한다.
Family만 같거나 synonym mapping만 같은 relation은 Recall numerator로 세지 않는다.

예시:

- GT가 `(chair, higher than, table)`인데 prediction이
  `(chair, lower than, table)`이면 family는 같아도 incorrect다.
- 동일 predicate라도 다른 chair instance를 사용하면 incorrect다.

Recall이 높을수록 GT relation을 ranking 안에 더 많이 보존했다는 뜻이다.

## 8. Verifier-derived Violation@K

선택된 relation 중 geometry verifier가 처리 가능한 candidate의 집합을 \(D_K\)라 한다.
각 candidate의 status는 satisfied, uncertain, violated 중 하나다.

\[
\mathrm{Violation@K}
=\frac{\sum_{i\in D_K}\mathbf 1[v_i=\mathrm{violated}]}
{|D_K|}.
\]

- numerator: violated candidate 수.
- denominator: satisfied + uncertain + violated candidate 수.
- uncertain은 violation numerator에는 들어가지 않지만 satisfied로 선언되지도
  않는다.
- denominator는 condition과 K에서 실제 선택된 geometry-checkable candidate 수다.

Violation은 낮을수록 좋다. 하지만 hard filter처럼 candidate를 제거하면 쉽게 낮아질 수
있으므로 Recall 및 coverage와 함께 해석해야 한다.

## 9. Uncertainty sensitivity

### Decidable-only violation

Uncertain을 제외하고 satisfied/violated만 분모로 사용한다.

\[
V_{\mathrm{dec}}
=\frac{N_{\mathrm{violated}}}
{N_{\mathrm{satisfied}}+N_{\mathrm{violated}}}.
\]

### Uncertainty rate

\[
U=\frac{N_{\mathrm{uncertain}}}
{N_{\mathrm{satisfied}}+N_{\mathrm{uncertain}}+N_{\mathrm{violated}}}.
\]

### Pessimistic violation

Uncertain을 모두 violation이라고 가정한다.

\[
V_{\mathrm{pess}}
=\frac{N_{\mathrm{violated}}+N_{\mathrm{uncertain}}}
{N_{\mathrm{satisfied}}+N_{\mathrm{uncertain}}+N_{\mathrm{violated}}}.
\]

Main conclusion이 \(V_{\mathrm{dec}}\)와 \(V_{\mathrm{pess}}\)에서도 유지되는지
확인해, uncertain denominator가 개선을 만든 것이 아닌지 검사한다.

## 10. Family-wise evaluation

Aggregate top-K 안에서 support/contact, proximity, vertical의 Recall과 Violation을
각각 계산한다. 또한 각 family가 선택된 top-K prediction에서 몇 개를 차지하는지
보고한다.

RelCompat3D ranking에서는 support/contact selection과 family composition이 Source와
동일하다. 따라서 이 family의 metric이 바뀌면 implementation 오류다.

Family-wise 결과는 다음을 구분한다.

- aggregate gain이 proximity에서 오는가.
- vertical이 Violation reduction을 주도하는가.
- support/contact error가 그대로 남는가.
- 한 family를 제거해 aggregate metric만 좋아진 것은 아닌가.

## 11. Paired scan-cluster confidence interval

548 contexts는 157 scans 안에 중첩되어 있으므로 context를 완전히 독립적인
sample로 보지 않는다.

1. 157 scan ID를 replacement와 함께 1,000번 resample한다.
2. 선택된 scan의 모든 context를 함께 가져온다.
3. 같은 resample index를 Source와 모든 비교 condition에 사용한다.
4. 각 replicate에서
   \(\Delta R=R_{\mathrm{method}}-R_{\mathrm{source}}\),
   \(\Delta V=V_{\mathrm{method}}-V_{\mathrm{source}}\)를 계산한다.
5. 2.5와 97.5 percentile을 paired 95% interval로 보고한다.

해석:

- Recall interval 전체가 0보다 크면 scan-level resampling에서 Recall gain이
  지지된다.
- Violation interval 전체가 0보다 작으면 Violation reduction이 지지된다.
- point estimate가 좋아도 interval이 0을 포함하면 statistical improvement라고
  단정하지 않는다.

548-context paired bootstrap은 finer-grained sensitivity로만 사용한다.

## 12. Main result를 읽는 법

K=50 percentage point snapshot:

| predictor | Source R / V | RelCompat3D R / V | 변화의 핵심 |
| --- | ---: | ---: | --- |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | Recall은 near-ceiling, V 감소 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | Recall 증가와 큰 V 감소 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | 작은 Recall 증가와 V 감소 |

모든 budget의 paired scan-cluster delta는 다음과 같다. 값은 percentage
point이며 대괄호는 95% interval이다.

| predictor | K | ΔRecall [95% interval] | ΔViolation [95% interval] |
| --- | ---: | ---: | ---: |
| VL-SAT | 5 | +0.13 [0.00, +0.25] | −0.15 [−0.30, −0.03] |
|  | 10 | +0.18 [+0.05, +0.34] | −0.26 [−0.45, −0.10] |
|  | 20 | +0.08 [−0.03, +0.19] | −0.28 [−0.44, −0.15] |
|  | 50 | +0.05 [−0.05, +0.19] | −0.70 [−0.88, −0.55] |
|  | 100 | +0.23 [+0.05, +0.49] | −1.82 [−1.99, −1.66] |
| Open3DSG | 5 | +0.30 [+0.12, +0.52] | −51.11 [−54.38, −48.14] |
|  | 10 | +1.49 [+1.01, +1.97] | −30.56 [−32.71, −28.43] |
|  | 20 | +3.73 [+3.01, +4.50] | −17.86 [−19.03, −16.66] |
|  | 50 | +3.75 [+2.96, +4.49] | −10.45 [−11.05, −9.86] |
|  | 100 | +5.82 [+4.70, +6.95] | −9.17 [−9.63, −8.73] |
| SGFN | 5 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
|  | 10 | 0.00 [0.00, 0.00] | −0.02 [−0.06, 0.00] |
|  | 20 | +0.03 [−0.08, +0.14] | −0.25 [−0.44, −0.11] |
|  | 50 | +0.48 [+0.28, +0.70] | −1.22 [−1.42, −1.02] |
|  | 100 | +0.68 [+0.43, +0.98] | −2.80 [−3.04, −2.57] |

따라서 VL-SAT에서는 Recall gain을 유의하다고 쓰지 않고, “detectable Recall
loss 없이 lower Violation”으로 해석한다. Open3DSG와 SGFN은 두 metric 방향이
모두 paired interval로 지지된다.

모든 K와 strong comparator의 정확한 수치는 main Table 1에 둔다. 본문은 각
cell을 반복하지 않고 다음 pattern을 설명한다.

- product는 rank fusion의 low-budget Recall loss를 줄인다.
- nonlinear model은 Open3DSG Recall을 더 높이지만 V도 더 높다.
- Product (all families)는 aggregate Recall을 높일 수 있지만 family scope를
  바꾼다.
- 하나의 comparator가 모든 predictor와 K에서 joint objective를 지배하지 않는다.

## 13. Threshold와 construct-overlap sensitivity

### Counterfactual threshold

Training-only refit에서 하나씩 바꾼다.

- proximity distance: 2.0 / 2.5 / 3.0.
- vertical margin: 0.20 / 0.25 / 0.30 m.
- negative cap: 1 / 2 / 4 per positive.
- pairwise-loss weight: 0.125 / 0.25 / 0.5.

다른 요소는 default로 유지한다. 결과가 특정 threshold 하나에만 의존하는지
검사한다.

### Held-out geometry primitive

Training feature에서 다음을 제거하고 다시 학습한다.

1. verifier가 직접 소비하는 exact scalar.
2. 해당 distance/vertical measurement family 전체.
3. alternative geometry evidence만 남긴 조건.

Exact scalar 제거에서 결과가 유지되면 단일 verifier 값의 복사는 배제할 수 있다.
관련 measurement family 전체를 제거했을 때 effect가 약해지는 것은 broader
construct dependence가 남아 있음을 뜻한다.

## 14. Computational cost

CPU benchmark는 relation candidates와 pair geometry가 memory에 준비된 시점부터
compatibility 계산, transformation averaging, family별 정렬, output 조립까지를
측정한다. Source predictor inference, 3D reconstruction, geometry association, JSONL
parsing, metric, bootstrap은 포함하지 않으므로 end-to-end latency로 해석하지
않는다.

- 환경: Intel Core Ultra 7 265KF, Python 3.11.9, NumPy 1.26.4.
- 실행: CPU process/thread 각 1개, warm-up 1회 후 5회 측정의 median.
- VL-SAT: 110,424 scored candidates, 2.492 s total, 4.548 ms/context.
- Open3DSG public predictions: 79,722 scored candidates, 1.828 s total,
  3.430 ms/nonempty context.
- SGFN: 110,424 scored candidates, 2.512 s total, 4.584 ms/context.
- 저장된 세 family head는 69 parameters이고, primary proximity/vertical
  inference가 실제 사용하는 것은 45 parameters이다. 학습되는 fusion
  parameter는 없다.
- Preloaded candidates를 포함한 peak process RSS는 366.9 MiB다.

이 수치는 compatibility layer 자체가 가벼움을 보여주지만 source model 전체의
속도나 memory cost를 대표하지 않는다.

## 15. 외부 dataset stress test

ReplicaSSG/FROSS에서 target-specific refitting 없이 적용한 결과는 supplement에
stress test로 보고한다. K=10과 K=50에서는 joint improvement가 있지만 K=100은
source-score quantization과 candidate support ceiling 때문에 거의 변화가 없다.

이 결과의 역할:

- score scale과 ontology shift의 failure mechanism 확인.
- dataset-level generalization claim의 근거가 아님.
- main Figure 1--3에는 넣지 않음.

## 16. 실험 해석에서 피해야 하는 표현

- 모든 source와 모든 K에서 Recall이 유의하게 개선되었다.
- Violation이 independent human physical validity다.
- V=0인 hard filter가 가장 reliable한 방법이다.
- 세 predictor 결과가 dataset-level generalization을 증명한다.
- nonlinear baseline보다 항상 우월하다.
- support/contact를 해결했다.
- K=50이 실제 deployment에서 canonical budget이다.

정확한 표현:

> 모든 K를 공개하고, K=50은 curve 중간의 descriptive reference로 해석한다.
> RelCompat3D는 shared 3DSSG target의 세 predictor에서 source-dependent
> Recall--Violation trade-off를 보이며, proximity와 vertical에서 가장
> 명확한 개선을 보인다.
