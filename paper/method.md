# RelCompat3D Method Guide

Last updated: 2026-07-21 KST

이 문서는 RelCompat3D의 방법론을 논문에서 사용하는 공식 용어로 설명한다.
독자가 3D Scene Graph를 처음 보더라도 입력, 학습 target, loss,
endpoint/predicate transformation, score 결합, re-ranking과 각 구성요소를 확인하는
control을 순서대로 이해할 수 있도록 작성했다. 제출용 수식의 authoritative source는
`paper/aaai/sec/3_problem.tex` 및 `paper/aaai/sec/4_method.tex`이다.

### Research task

RelCompat3D가 푸는 task는 새로운 relation을 생성하는 것이 아니라, **기존
predictor가 만든 fixed relation candidates를 corresponding ordered-pair geometry와
대조해 compatibility를 추정하고 순위를 다시 정하는 것**이다. 입력 candidate와
predicate vocabulary는 유지하며, 출력은 같은 candidate universe에 대한 새로운
ranking이다.

### Core method contribution

핵심 contribution은 하나의 linear formula나 MLP architecture가 아니다. 다음 세
요소를 결합한 relation-reliability framework다.

1. predictor score와 predictor identity를 compatibility 입력에서 제외하고,
   predicate semantics와 candidate에 대응하는 ordered-pair measurements를 분리한다.
2. linked positive--counterfactual learning과 transformation averaging을 사용해
   predicate--geometry compatibility 및 relation-preserving consistency를 학습한다.
3. predictor score는 마지막 family-aware re-ranking에서만 결합하고,
   proximity/vertical-order만 다시 정렬하면서 support/contact는 source order로
   유지한다.

RelCompat3D-Linear와 RelCompat3D-MLP는 이 framework의 두 proposed
instantiation이다. 두 estimator의 차이는 compatibility parameterization이며,
framework contribution이나 fusion rule을 서로 다르게 정의하지 않는다.

## 1. 한 문장으로 보는 방법

RelCompat3D는 기존 relation predictor가 만든 candidate와 predictor relation score를
그대로 받은 뒤, **그 predicate가 corresponding ordered subject--object pair의
geometric measurements와 얼마나 잘 맞는지 별도로 점수화하고, 두 점수를 정의된
endpoint/predicate transformation을 갖는 relation에서만 결합해 순서를 다시 정한다.**

이 방법은 새로운 3D Scene Graph generator가 아니다. object detection,
segmentation, candidate generation 또는 predicate vocabulary를 바꾸지 않는다.

전체 흐름은 다음 여섯 단계다.

```text
기존 relation candidate와 predictor score Z
    → predicate semantics T와 ordered-pair measurements G를 분리
    → T와 G만으로 Linear 또는 MLP compatibility C를 계산
    → 의미가 보존되는 endpoint/predicate 변환의 score를 평균
    → proximity/vertical에서 Z × C^tr로 relation-family 내부 순서를 변경
    → support/contact는 source order로 유지한 top-K ranking
```

## 2. 입력 candidate를 어떻게 분해하는가

각 relation candidate를 다음 tuple로 나타낸다.

\[
r_i=(\text{scene},\text{context},s_i,o_i,p_i,a_i,Z_i).
\]

- \(s_i\): subject instance ID.
- \(o_i\): object instance ID.
- \(p_i\): predicted predicate, 예: `close by`, `higher than`.
- \(a_i\): mapped relation family.
- \(Z_i\): 기존 predictor가 출력한 predictor score.
- `context`: top-K ranking을 수행하는 scene subgraph 단위.

여기서 compatibility model의 두 입력과 predictor score를 분리한다.

\[
T_i=p_i=\text{predicate semantics},\qquad
G_i=\text{predicate-independent geometric measurements of the ordered pair},\qquad
Z_i=\text{predictor score}.
\]

### Predicate semantics \(T_i\)

- predicate identity: `close by`, `higher than`, `lower than`, `lying on` 등.
- 어떤 geometry 값이 어떤 방향으로 해석되어야 하는지 정한다.

### Relation family \(a_i\)

Family label은 두 estimator에서 공통으로 endpoint/predicate transformation과
re-ranking 범위를 정한다. 다만 parameterization에 따른 역할은 다르다.

- **RelCompat3D-Linear:** family-specific head와 해당 head의 training-split
  normalization statistics를 선택한다. 각 head 안에서 family one-hot은 상수이므로
  입력하지 않는다.
- **RelCompat3D-MLP:** 하나의 nonlinear model이 모든 family를 공유하므로 family
  one-hot이 변하는 semantic input으로 들어간다.

따라서 Linear는 constant family input을 제거한 family-specific heads를 사용한다.
MLP의 family indicator는 shared model 안에서 candidate마다 달라지므로 bias와
중복되지 않는다.

### Geometric measurements of the ordered pair \(G_i\)

반드시 prediction candidate와 동일한 scene, subject ID, object ID에서 가져온다.

- OBB-derived 3D/XY center distance와 object scale로 정규화한 distance.
- OBB center의 relative height와 그 절댓값.
- OBB의 projected IoU와 subject/object 방향 projected overlap.
- OBB top/bottom height와 vertical-gap feature.
- predicate 방향으로 해석한 height difference는 위 pair measurement와 predicate의
  interaction으로 구성한다.

현재 compatibility model은 OBB에서 계산한 위 feature만 사용한다. Point-level
contact evidence는 Violation verifier의 support/contact 진단에는 쓰이지만,
compatibility model 입력이나 counterfactual 생성에는 쓰이지 않는다.

object category가 같다는 이유로 다른 chair, table, floor의 measurements를
가져오면 안 된다. 이 ordered-pair association이 wrong-pair control의 대상이다.

### Predictor score \(Z_i\)

기존 predictor가 relation candidate의 순위를 정할 때 사용하는 점수다. 반드시
calibrated probability인 것은 아니다. Predictor별 normalization이나 refitting은
적용하지 않는다. VL-SAT과 SGFN은 sigmoid relation score를, Open3DSG는 normalized
predicate-text embedding의 cosine similarity를 사용한다. 각 predictor는 독립적으로
ranking되므로 서로 다른 predictor의 \(Z_i\)를 직접 비교하지 않는다. Compatibility
model은 다음을 입력으로 받지 않는다.

- predictor score와 source rank.
- predictor 이름 또는 source ID.
- object-class features.

따라서 compatibility model은 predictor score를 그대로 복사할 수 없다.

### Evaluation scope와 re-ranking scope

보고하는 evaluation family는

\[
\mathcal A_{\mathrm{eval}}
=\{\mathrm{support/contact},\mathrm{proximity},\mathrm{vertical\ order}\}
\]

이다. 이 밖의 relation은 현재 scoped Recall/Violation 평가에 포함하지 않는다.
Compatibility로 순서를 바꾸는 family는 더 좁다.

\[
\mathcal A_{\mathrm{rank}}
=\{\mathrm{proximity},\mathrm{vertical\ order}\}.
\]

Support/contact는 richer local contact와 pose evidence가 필요하고 모든 predicate의
의미를 보존하는 하나의 endpoint transformation이 없으므로 source order를 유지한다.

## 3. Compatibility score는 무엇인가

RelCompat3D는 compatibility estimator의 functional form을 하나로 고정하지 않는다.
현재 논문은 같은 factor separation과 학습 target 아래 두 instantiation을 평가한다.

### RelCompat3D-Linear

각 relation family에 작은 linear model을 하나씩 사용한다.

\[
\ell_i^{\mathrm{lin}}=w_{a_i}^{\top}\Phi(T_i,G_i),\qquad
C_i^{\mathrm{lin}}=\sigma(\ell_i^{\mathrm{lin}})
=\frac{1}{1+e^{-\ell_i^{\mathrm{lin}}}}.
\]

- \(a_i\)는 relation family다.
- \(\ell_i^{\mathrm{lin}}\)은 제한이 없는 real-valued logit이다.
- \(C_i^{\mathrm{lin}}\in[0,1]\)는 predicate와 ordered-pair measurements의
  compatibility score다.

Family \(a_i\)가 head를 선택한 뒤, feature map은 실제 구현에 맞춰 다음처럼
구성된다.

\[
\Phi(T_i,G_i)=
\left[1;\phi_T(T_i);\operatorname{std}_{\rm tr}(G_i);
\operatorname{std}_{\rm tr}(\phi_\times(T_i,G_i))\right],
\]

여기서 명시적인 interaction은 다음 두 signed-height feature다.

\[
\phi_\times(T_i,G_i)=
[d(p_i)\Delta z_i,\ d(p_i)\Delta z_i^{\rm norm}],
\]

\(d(p)=1\)은 `higher than`, \(-1\)은 `lower than`, 그 외 predicate는 0이다.
따라서 두 explicit interaction term은 vertical-order predicate에서만 활성화된다.
\(\phi_T\)는 predicate indicator만 포함한다. Family indicator는 포함하지 않는다.
\(\operatorname{std}_{\rm tr}\)는 training split의 mean/std만 사용하고 missing value를
training mean으로 대체한다. Full outer product나 모든 predicate--geometry 조합을
사용하지 않는다.

예를 들어 base height difference가 같아도 `higher than`에는 양의 차이가,
`lower than`에는 음의 차이가 evidence가 된다. Interaction은 이 부호 관계를
명시한다.

중요한 해석:

> \(C_i^q\)는 아래에서 설명하는 constructed training target과의 compatibility를
> 나타내며, 사람 기준의 physical validity 확률은 아니다.

### RelCompat3D-MLP

두 번째 instantiation은 모든 family가 공유하는 hidden width 2의 ReLU MLP다.
입력은 다음으로 구성된다.

- family one-hot 3개와 predicate one-hot 6개.
- Linear와 같은 17개 ordered-pair geometric measurements.
- predicate-signed height interaction 2개.
- 두 directional overlap ratio의 합 1개.

총 29개 입력을 사용하며, logit은 다음과 같다.

\[
h_i=\operatorname{ReLU}(W\Psi_i+b),\qquad
\ell_i^{\mathrm{mlp}}=v^\top h_i+b_o+\beta^\top\phi_T(T_i),\qquad
C_i^{\mathrm{mlp}}=\sigma(\ell_i^{\mathrm{mlp}}).
\]

MLP도 predictor score, rank, predictor identity, object class를 입력하지 않는다.
69개 parameter를 가지며, Linear와 동일한 training rows, constructed targets,
linked-pair loss, transformation averaging, product ranking score, family-aware re-ranking을
사용한다. 두 모델의 차이는 compatibility parameterization과 nonlinear
flexibility다.

MLP 구현과 검증 결과의 기준 파일은 다음과 같다.

- model: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/nonlinear/models.json`
  (SHA256 `ccf4107c06d95161df8ecb1948b37f781025407d7b3596ddd6886394a2976c3e`).
- matched structural controls:
  `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/mlp_ablation/`
  (summary SHA256
  `83e85bbb9c940644ece4d0322db6ea2f7c98dccfbd11a62ff1efbf47295484ce`).
- point/mesh agreement audit:
  `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/mlp_surface_audit/`
  (summary SHA256
  `c77c94024fe9de09afbe9ad418f97945a114087cb0199a00079b77df83c3bd55`).

이 경로들은 MLP가 기존 baseline의 명칭만 바꾼 것이 아니라, Linear와 같은 method
definition 아래에서 별도로 검증된 nonlinear compatibility instantiation임을
기록한다.

## 4. Positive와 counterfactual negative를 어떻게 만드는가

### Positive

Training split의 measured-family ground-truth relation을 positive로 사용한다.
Final evaluation split의 GT는 학습 target 생성에 사용하지 않는다.

### Proximity negative

같은 scene context에서 먼 ordered pair를 찾는다.

- normalized XY distance가 2.5 이상.
- 두 방향 projected overlap이 사실상 0.
- 거리가 큰 pair부터 선택.

이 pair에 `close by`가 맞다고 가정하면 positive와 반대되는 geometry가 된다.

### Vertical-order negative

동일한 subject/object pair에서 predicate를 뒤집는다.

- `higher than` ↔ `lower than`.
- absolute height difference가 0.25 m 이상.
- normalized absolute height difference가 0.15 이상.

즉 pair geometry는 유지하고 predicate direction만 틀리게 만든다.

### Support/contact negative

같은 context 안에서 subject 또는 object endpoint를 다른 instance로 교체한다.

- 이미 support/contact GT로 알려진 pair는 제외.
- floor가 subject인 pair는 제외.
- 다음 세 조건 중 두 개 이상을 만족해야 한다.
  - normalized XY distance ≥ 2.0.
  - projected overlap이 0.
  - vertical gap ≥ 0.30 m.

### Negative 수 제한

- positive 하나당 최대 2개.
- context--family당 최대 200개.
- family별 positive 수의 최대 3배.

이 제한은 쉬운 negative가 지나치게 반복되는 것을 줄인다. Family 수를 억지로
동일하게 맞추지는 않는다.

### Training construction과 evaluation verifier의 관계

Evaluation row, predictor score, verifier-status label은 training example을 만드는
데 사용하지 않는다. 다만 counterfactual construction과 primary verifier는 일부
OBB-derived measurement를 공유하며, 일부 family에서는 threshold도 공유한다.
따라서 Violation@K는 independent physical-validity ground truth가 아니라
verifier-derived evaluation measure다. Surface-based audit과 feature-removal
analysis는 이 overlap을 검사하지만 완전히 제거하지는 않는다.

## 5. 학습 loss를 쉽게 풀어 쓰면

학습은 세 항을 더한다.

\[
\mathcal L=\mathcal L_{\mathrm{BCE}}
+0.25\mathcal L_{\mathrm{pair}}
+10^{-4}\mathcal R(\theta).
\]

### 5.1 Binary cross-entropy

각 training example이 positive인지 counterfactual negative인지 맞히게 한다.

\[
\mathcal L_{\mathrm{BCE}}
=-\frac1N\sum_i
\left[y_i\log C_i+(1-y_i)\log(1-C_i)\right].
\]

- positive는 \(y_i=1\).
- negative는 \(y_i=0\).
- positive에 낮은 C를 주거나 negative에 높은 C를 주면 loss가 커진다.

### 5.2 Linked positive–counterfactual ordering loss

Positive와 그 positive에서 만든 negative를 직접 연결한다. 원하는 조건은

\[
\ell_{i^+}>\ell_{i^-}+1
\]

이다. 실제 loss는 부드럽게 미분 가능한 형태다.

\[
\mathcal L_{\mathrm{pair}}
=\frac1{|\mathcal P|}\sum_{(i^+,i^-)\in\mathcal P}
\log\left(1+e^{1-(\ell_{i^+}-\ell_{i^-})}\right).
\]

- logit 차이가 margin 1보다 크면 penalty가 작다.
- negative가 positive보다 높으면 penalty가 빠르게 커진다.
- BCE가 각 example의 label을 학습한다면, pair loss는 두 example의 **순서**를 직접
  학습한다.

### 5.3 L2 regularization

\(10^{-4}\mathcal R(\theta)\)는 bias를 제외한 weight가 지나치게 커지는 것을
억제한다. 같은 coefficient를 Linear와 MLP에 사용한다.

### 학습 세부 사항

- numeric feature의 mean/std와 missing-value 대체값은 training split에서만
  계산한다.
- Linear: deterministic full-batch optimization 800 steps, learning rate 0.2.
- MLP: deterministic full-batch optimization 120 steps, learning rate 0.02.
- Linear family별 parameter 수는 proximity 21개, vertical order 22개,
  support/contact 23개이며 세 head에 저장된 수는 총 66개다. Primary
  proximity/vertical path가 평가하는 parameter는 43개다.
- MLP는 shared 69-parameter model이다.
- 60,208 training examples, 33,961 linked pairs.
- transformation-consistent augmentation 이후 86,032 optimization examples.
- margin은 1, pairwise weight는 0.25, L2 coefficient는 \(10^{-4}\)로 두
  estimator와 predictor에 동일하게 사용한다. Predictor별 hyperparameter search는
  수행하지 않으며 one-factor sensitivity는 supplement에 보고한다.

두 estimator 모두 작은 model이지만 서로 다른 parameterization을 제공한다. 이
구현 수치는 main Figure에는 넣지 않는다.

Frozen training-only Linear model files는
`experiments/H001_geom_reliability/no_family_indicator_v1/fit/`에 있다.
Structured model SHA256은
`08cd309bbacead29dd9f76cd3845e3625de72423e45c242e33114ca686e2c01c`,
strict model SHA256은
`5b6423d0825395990b00663fc0004799268d87c9480493895d01d1c3ef9c3218`이다.
MLP model artifact SHA256은
`ccf4107c06d95161df8ecb1948b37f781025407d7b3596ddd6886394a2976c3e`다.

## 6. Endpoint/predicate transformation은 무엇을 하는가

여기서 transformation은 **subject와 object를 바꾸었을 때 predicate가 어떻게
변해야 하는지 이미 알려진 관계 규칙**이다. Base model의 출력이 이 규칙을
자동으로 만족한다고 가정하지 않고, 의미가 같은 입력들의 score를 inference에서
평균해 최종 compatibility가 규칙을 정확히 만족하게 한다. 이 최종 score를
transformation-consistent compatibility \(C^{\mathrm{tr},q}\)로 표기하며
\(q\in\{\mathrm{lin},\mathrm{mlp}\}\)다.

### Proximity symmetry

`close by`는 endpoint 순서가 바뀌어도 같은 관계다. 학습된 base model이 두
방향에 조금 다른 값을 내더라도 inference에서 평균한다.

\[
C^{\mathrm{tr},q}(\text{close},s,o)
=\frac12\left[
C^q(\text{close},s,o)+C^q(\text{close},o,s)
\right]
=C^{\mathrm{tr},q}(\text{close},o,s).
\]

### Joint endpoint swap and inverse-predicate transformation

Endpoint를 바꾸면 predicate도 반대로 바뀌어야 한다. 따라서

\[
C^{\mathrm{tr},q}(\text{higher},s,o)
=\frac12\left[
C^q(\text{higher},s,o)+C^q(\text{lower},o,s)
\right]
=C^{\mathrm{tr},q}(\text{lower},o,s).
\]

`lower than`도 같은 방식으로 처리한다.

### 평균을 쓰는 이유

원래 입력과 의미상 동일한 transformed input의 score를 평균하면, 변환 전후에
동일한 최종 score가 보장된다. 이 consistency는 loss가 잘 학습되기를 기대하는
것이 아니라 inference 계산 자체로 정확히 성립한다.

### Support/contact

`standing on`, `lying on`, `supported by`를 하나의 규칙으로 endpoint-swap할
수 없다. 또한 현재 geometry는 local contact와 pose를 충분히 관측하지 못한다.
따라서 RelCompat3D re-ranking에서는 이 family를 source order로 유지한다.
Support/contact compatibility head는 `Product (all families)` 비교를 위해 유지하지만,
RelCompat3D의 primary ranking에는 사용하지 않는다.

## 7. Predictor score와 compatibility를 어떻게 결합하는가

순서를 다시 정하는 family 집합
\(\mathcal A_{\mathrm{rank}}=\{\mathrm{proximity},\mathrm{vertical\ order}\}\)에
대해 각 candidate의 within-family ranking score를 다음처럼 정의한다.

\[
u_i^q=
\begin{cases}
Z_iC_i^{\mathrm{tr},q}, & a_i\in\mathcal A_{\mathrm{rank}},\\
Z_i, & a_i=\mathrm{support/contact}.
\end{cases}
\]

이 score로 각 relation family 안의 candidate 순서를 정한다.

- Z가 높고 C도 높으면 높은 score를 유지한다.
- Z가 높더라도 C가 매우 낮으면 내려간다.
- C가 높더라도 Z가 낮으면 geometry만으로 지나치게 올라가지 않는다.

두 값이 양수일 때

\[
\log u_i^q=\log Z_i+\log C_i^{\mathrm{tr},q}
\]

이므로 compatibility는 log-score에 하나의 항으로 더해진다. 추가 fusion
weight는 사용하지 않는다. 이 식을 확률 posterior로 해석하지 않는다.

## 8. Family-aware re-ranking을 단계별로 보면

단순히 모든 family를 한꺼번에 하나의 product로 정렬하면 support/contact까지
순서가 바뀌고 family composition이 크게 달라질 수 있다. RelCompat3D의 ranking rule은 다음처럼
동작한다.

### Step 1: Source ranking에서 family sequence를 기록

예를 들어 원래 ranking의 family가

```text
P, S, V, P, S, V
```

라고 하자. P는 proximity, S는 support/contact, V는 vertical이다.

### Step 2: Family별 ordered candidate list를 만든다

- P list: 선택한 estimator의 \(u^q=ZC^{\mathrm{tr},q}\) 내림차순.
- V list: 선택한 estimator의 \(u^q=ZC^{\mathrm{tr},q}\) 내림차순.
- S list: source ranking에서 support/contact candidate만 뽑은 subsequence 그대로.

### Step 3: 원래 relation-family position을 다시 채운다

원래 sequence의 첫 글자가 P이면 P list에서 아직 선택하지 않은 첫 candidate를
사용한다. 다음이 S이면 S list, 다음이 V이면 V list에서 같은 방식으로 선택한다.

결과 family sequence는 여전히

```text
P, S, V, P, S, V
```

이다. 바뀌는 것은 P끼리와 V끼리의 내부 순서뿐이다.

### 이 re-ranking이 보장하는 것

- 모든 top-K prefix에서 family 개수가 source ranking과 같다.
- support/contact candidate의 상대 순서와 선택이 같다.
- proximity와 vertical만 compatibility의 영향을 받는다.
- 별도의 threshold나 학습되는 fusion parameter가 없다.
- re-ranked family의 score tie는 exact relation-candidate identity의 deterministic
  order로 해결한다. Support/contact는 source subsequence 자체를 유지한다.

또한 prefix 길이 \(K\)와 family별 자리 수를 고정하면, 각 re-ranked family에서
필요한 수만큼 utility가 가장 높은 candidate를 선택한다.
따라서 같은 family count와 support/contact subsequence를 보존하는 ranking 중
선택된 proximity/vertical candidate의 utility 합이 최대다. 이는 fusion formula의
전역적 최적성이나 Recall--Violation 최적성을 뜻하지 않고, 주어진 제약 아래의
prefix selection 성질이다.

## 9. 전체 inference algorithm

```text
for each relation context:
    1. predictor score Z로 원래 candidate ranking을 만든다.
    2. 각 candidate의 동일 subject/object geometry G를 가져온다.
    3. 선택한 Linear 또는 MLP estimator로 compatibility C^q를 계산한다.
    4. proximity는 endpoint-swap score와 평균한다.
    5. vertical은 endpoint-swap + inverse-predicate score와 평균한다.
    6. proximity/vertical candidate score u^q를 Z × C^{tr,q}로 계산한다.
    7. source ranking의 family sequence는 그대로 유지한다.
    8. 각 proximity/vertical position은 해당 family의 새 score 순서로 채운다.
    9. support/contact position은 source order로 채운다.
    10. 완성된 ranking에서 top-K를 선택한다.
```

## 10. 비교 조건이 분리하는 요소

### Alternative fusion rules

두 RelCompat3D instantiation은 모두 product ranking score를 사용한다. 이 product와
비교하기 위해 score scale에 덜 민감한 두 fusion baseline을 둔다. Rank-average와
RRF는 Linear compatibility를 사용하되 동일한 family-aware re-ranking procedure를
적용한다.

### Rank-average

한 context 안에서 source score rank와 compatibility rank를 각각 percentile로
바꾸고 평균한다.

\[
S_i^{\mathrm{rank}}=\frac12(q_i^Z+q_i^C).
\]

원래 score의 절대 scale은 버리고 두 ranking의 상대 위치만 사용한다.

### Reciprocal Rank Fusion

\[
S_i^{\mathrm{RRF}}
=\frac1{60+r_i^Z}+\frac1{60+r_i^C}.
\]

상위 rank에 더 큰 값을 주는 일반적인 rank-fusion 방식이다. Constant 60은
모든 predictor와 K에서 동일하게 사용한다.

RelCompat3D-MLP는 fusion baseline이 아니라 compatibility parameterization이 다른
proposed instantiation이다. 따라서 Linear와 MLP의 차이는 compatibility model을, Rank-average와
RRF의 차이는 score 결합 방식을 검증한다.

### Method-component controls

아래 control은 새로운 proposed method가 아니라, 같은 candidate와 family-aware
re-ranking을 유지한 채 한 요소만 바꾸는 개입이다. 따라서 결과 변화는 어떤 입력이나
구조가 필요한지를 해석하는 데 사용한다.

| Control | 유지하는 요소 | 바꾸는 요소 | 확인하는 가정 |
| --- | --- | --- | --- |
| Wrong predicate | ordered pair, \(G_i\), \(Z_i\) | compatibility에 넣는 predicate \(T_i\) | predicate meaning과 geometry의 대응이 필요한가? |
| Wrong pair | predicate, \(Z_i\) | 다른 object pair의 \(G_i\) | candidate와 같은 ordered pair의 measurements가 필요한가? |
| Shuffled geometry | candidate와 predicate, \(Z_i\) | candidates 사이에서 \(G_i\)를 섞음 | geometry의 전체 분포가 아니라 pair-specific evidence가 필요한가? |
| Fixed-label swap | predicate, \(Z_i\) | subject/object measurements를 바꾸고 predicate는 고정 | vertical relation에서 endpoint와 inverse predicate를 함께 바꿔야 하는가? |
| Distance only | candidate universe와 family sequence | compatibility model을 하나의 pair-distance ordering으로 대체 | 여러 geometry measurements와 predicate conditioning이 필요한가? |
| Compatibility only | \(T_i\), \(G_i\), \(C_i^{\mathrm{tr},q}\) | predictor score \(Z_i\)를 결합에서 제거 | geometry compatibility만으로 semantic relevance를 보존할 수 있는가? |

Wrong predicate와 Fixed-label swap은 다른 개입이지만, vertical-order candidate에서는
둘 다 signed predicate--geometry relation을 반대로 만들 수 있다. 따라서 aggregate
결과가 비슷하더라도 서로 완전히 독립된 두 증거로 세지 않는다. Distance only는
Linear/MLP head를 사용하지 않으므로 두 estimator에 공통인 control이다.

논문 본문의 one-column ablation table은 RelCompat3D-Linear의 full method와 여섯
controls를 \(K\in\{50,100\}\)에서 보고하고, 같은 표에 RelCompat3D-MLP의 full-method
operating point를 포함한다. MLP에 동일하게 적용한 complete controls는 supplement에
둔다. 따라서 main table의 corruption/control 해석은 Linear에 한정하고, MLP row는
효과가 하나의 linear compatibility parameterization에만 나타나는지 확인하는
comparison으로 읽는다.

## 11. 방법이 주장하지 않는 것

- C는 독립 human physical-validity probability가 아니다.
- multiplication이 유일하거나 최적인 fusion이라는 주장이 아니다.
- MLP가 Linear보다 또는 Linear가 MLP보다 보편적으로 우수하다는 주장이 아니다.
- support/contact error를 해결했다는 주장이 아니다.
- 새로운 object detector, relation generator, open-vocabulary vocabulary를
  제안하지 않는다.
- 세 predictor 결과는 하나의 shared 3DSSG target에서 predictor 간 behavior를
  비교한 것이며 cross-dataset generalization이 아니다.

## 12. 논문에서 사용할 용어

사용:

- predictor score.
- predicate semantics.
- geometry of the corresponding ordered pair.
- predicate–geometry compatibility.
- transformation-consistent compatibility.
- transformation averaging.
- family-aware re-ranking.
- support/contact candidates kept in source order.

사용하지 않음:

- 구현 파일에서만 사용하는 축약명이나 실험 식별자.
- predictor score를 calibrated probability처럼 읽히게 하는 표현.
- 구현 세부 절차를 전면에 내세우는 label.
- compatibility를 physical-validity probability로 해석하는 표현.
- 모든 relation family와 dataset에 보편적으로 적용되는 최적 rescorer.
