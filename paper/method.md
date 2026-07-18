# RelCompat3D Method Guide

Last updated: 2026-07-17 KST

이 문서는 RelCompat3D의 방법론을 논문 artifact 이름이나 연구 과정 용어 없이
설명한다. 독자가 3D Scene Graph를 처음 보더라도 입력, 학습 target, loss,
endpoint/predicate transformation, score 결합, re-ranking을 순서대로 이해할 수
있도록 작성했다. 제출용 수식의 authoritative source는 `paper/aaai/sec/3_problem.tex`
및 `paper/aaai/sec/4_method.tex`이다.

## 1. 한 문장으로 보는 방법

RelCompat3D는 기존 relation predictor가 만든 candidate와 source relation score를
그대로 받은 뒤, **그 predicate가 동일한 subject--object pair의 3D geometry와 얼마나
잘 맞는지 별도로 점수화하고, 두 점수를 geometry로 판단 가능한 relation에서만
결합해 순서를 다시 정한다.**

이 방법은 새로운 3D Scene Graph generator가 아니다. object detection,
segmentation, candidate generation 또는 predicate vocabulary를 바꾸지 않는다.

전체 흐름은 다음 여섯 단계다.

```text
기존 relation candidate와 source relation score Z
    → 동일 subject/object의 predicate T와 geometry G를 분리
    → T와 G만으로 compatibility C를 계산
    → 의미가 보존되는 endpoint/predicate 변환의 score를 평균
    → proximity/vertical에서 Z × C로 relation-family 내부 순서를 변경
    → support/contact는 source order로 유지한 top-K 출력
```

## 2. 입력 candidate를 어떻게 분해하는가

각 relation candidate를 다음 tuple로 나타낸다.

\[
r_i=(\text{scene},\text{context},s_i,o_i,p_i,Z_i).
\]

- \(s_i\): subject instance ID.
- \(o_i\): object instance ID.
- \(p_i\): predicted predicate, 예: `close by`, `higher than`.
- \(Z_i\): 기존 predictor가 출력한 source relation score.
- `context`: top-K ranking을 수행하는 scene subgraph 단위.

여기서 세 종류의 정보를 분리한다.

\[
T_i=\text{predicate semantics},\qquad
G_i=\text{predicate-independent pair-geometry measurements},\qquad
Z_i=\text{source relation score}.
\]

### Predicate semantics \(T_i\)

- predicate identity: `close by`, `higher than`, `lower than`, `lying on` 등.
- relation family: proximity, vertical order, support/contact.
- 어떤 geometry 값이 어떤 방향으로 해석되어야 하는지 정한다.

### Pair geometry \(G_i\)

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

object category가 같다는 이유로 다른 chair, table, floor의 geometry를 가져오면
안 된다. 이 instance-level association이 wrong-pair control의 대상이다.

### Source relation score \(Z_i\)

기존 predictor가 relation candidate의 순위를 정할 때 사용하는 점수다. 반드시
calibrated probability인 것은 아니다. Compatibility model은 다음을 입력으로
받지 않는다.

- source relation score와 source rank.
- predictor 이름 또는 source ID.
- object-class features.

따라서 compatibility model은 source relation score를 그대로 복사할 수 없다.

## 3. Compatibility score는 무엇인가

각 relation family에 작은 linear model을 하나씩 사용한다.

\[
\ell_i=w_{a_i}^{\top}\Phi(T_i,G_i),\qquad
C_i=\sigma(\ell_i)=\frac{1}{1+e^{-\ell_i}}.
\]

- \(a_i\)는 relation family다.
- \(\ell_i\)는 제한이 없는 real-valued logit이다.
- \(C_i\in[0,1]\)는 predicate와 pair geometry의 compatibility score다.

Feature map은 세 부분으로 구성된다.

\[
\Phi(T,G)=\left[\phi_T(T),\ \phi_G(G),\ \phi_{T\times G}(T,G)\right].
\]

1. \(\phi_T\): predicate/family indicator.
2. \(\phi_G\): predicate와 무관하게 계산한 pair-geometry measurements.
3. \(\phi_{T\times G}\): predicate 방향에 맞게 해석한 interaction.

예를 들어 base height difference가 같아도 `higher than`에는 양의 차이가,
`lower than`에는 음의 차이가 evidence가 된다. Interaction은 이 부호 관계를
명시한다.

중요한 해석:

> \(C_i\)는 아래에서 설명하는 constructed training target과의 compatibility를
> 나타내며, 사람 기준의 physical validity 확률은 아니다.

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

## 5. 학습 loss를 쉽게 풀어 쓰면

학습은 세 항을 더한다.

\[
\mathcal L=\mathcal L_{\mathrm{BCE}}
+0.25\mathcal L_{\mathrm{pair}}
+10^{-4}\lVert w\rVert_2^2.
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

### 5.2 Linked-pair ordering loss

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

\(10^{-4}\lVert w\rVert_2^2\)는 작은 training set에서 weight가 지나치게
커지는 것을 억제한다.

### 학습 세부 사항

- numeric feature의 mean/std와 missing-value 대체값은 training split에서만
  계산한다.
- deterministic full-batch optimization 800 steps.
- learning rate 0.2.
- family별 parameter 수는 22--24개이며 세 head에 저장된 수는 총 69개다.
  Primary proximity/vertical path가 평가하는 parameter는 45개다.
- 60,208 training examples, 33,961 linked pairs.
- transformation-consistent augmentation 이후 86,032 optimization examples.

이 수치는 model capacity가 매우 작다는 것을 보여주기 위한 것이며, main
Figure에는 넣지 않는다.

## 6. Endpoint/predicate transformation은 무엇을 하는가

여기서 transformation은 **subject와 object를 바꾸었을 때 predicate가 어떻게
변해야 하는지 이미 알려진 관계 규칙**이다. Base model의 출력이 이 규칙을
자동으로 만족한다고 가정하지 않고, 의미가 같은 입력들의 score를 inference에서
평균해 최종 compatibility가 규칙을 정확히 만족하게 한다. 이 최종 score를
transformation-consistent compatibility \(C^{\mathrm{tr}}\)로 표기한다.

### Proximity symmetry

`close by`는 endpoint 순서가 바뀌어도 같은 관계다. 학습된 base model이 두
방향에 조금 다른 값을 내더라도 inference에서 평균한다.

\[
C^{\mathrm{tr}}(\text{close},s,o)
=\frac12\left[
C(\text{close},s,o)+C(\text{close},o,s)
\right]
=C^{\mathrm{tr}}(\text{close},o,s).
\]

### Vertical inverse relation

Endpoint를 바꾸면 predicate도 반대로 바뀌어야 한다. 따라서

\[
C^{\mathrm{tr}}(\text{higher},s,o)
=\frac12\left[
C(\text{higher},s,o)+C(\text{lower},o,s)
\right]
=C^{\mathrm{tr}}(\text{lower},o,s).
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

## 7. Source relation score와 compatibility를 어떻게 결합하는가

Geometry compatibility를 적용하는 proximity와 vertical candidate에는

\[
S_i=Z_iC_i^{\mathrm{tr}}
\]

를 사용한다.

- Z가 높고 C도 높으면 높은 score를 유지한다.
- Z가 높더라도 C가 매우 낮으면 내려간다.
- C가 높더라도 Z가 낮으면 geometry만으로 지나치게 올라가지 않는다.

두 값이 양수일 때

\[
\log S_i=\log Z_i+\log C_i^{\mathrm{tr}}
\]

이므로 compatibility는 log-score에 하나의 항으로 더해진다. 추가 fusion
weight는 사용하지 않는다. 이 식을 확률 posterior로 해석하지 않는다.

## 8. Family-aware re-ranking을 단계별로 보면

단순히 모든 family를 한꺼번에 S로 정렬하면 support/contact까지 순서가 바뀌고
family composition이 크게 달라질 수 있다. RelCompat3D의 ranking rule은 다음처럼
동작한다.

### Step 1: Source ranking에서 family sequence를 기록

예를 들어 원래 ranking의 family가

```text
P, S, V, P, S, V
```

라고 하자. P는 proximity, S는 support/contact, V는 vertical이다.

### Step 2: Family별 ordered candidate list를 만든다

- P list: \(ZC^{\mathrm{tr}}\) 내림차순.
- V list: \(ZC^{\mathrm{tr}}\) 내림차순.
- S list: 원래 \(Z\) 내림차순 그대로.

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

또한 prefix 길이 (K)와 family별 자리 수를 고정하면, 각 proximity/vertical
family에서 필요한 수만큼 (ZC^{\mathrm{tr}})가 가장 높은 candidate를 선택한다.
따라서 같은 family count와 support/contact subsequence를 보존하는 ranking 중
선택된 proximity/vertical candidate의 utility 합이 최대다. 이는 fusion formula의
전역적 최적성이나 Recall--Violation 최적성을 뜻하지 않고, 주어진 제약 아래의
prefix selection 성질이다.

## 9. 전체 inference algorithm

```text
for each relation context:
    1. source relation score Z로 원래 candidate ranking을 만든다.
    2. 각 candidate의 동일 subject/object geometry G를 가져온다.
    3. predicate T와 geometry G로 compatibility C를 계산한다.
    4. proximity는 endpoint-swap score와 평균한다.
    5. vertical은 endpoint-swap + inverse-predicate score와 평균한다.
    6. proximity/vertical candidate score를 Z × C로 계산한다.
    7. source ranking의 family sequence는 그대로 유지한다.
    8. 각 proximity/vertical position은 해당 family의 새 score 순서로 채운다.
    9. support/contact position은 source order로 채운다.
    10. 완성된 ranking에서 top-K를 선택한다.
```

## 10. 비교용 결합 방식

RelCompat3D product 외에 score scale에 덜 민감한 두 방법을 비교한다.

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

이 두 방식과 nonlinear model도 동일한 family-aware re-ranking을 적용해 ranking
procedure가 아니라 score 결합 차이를 비교한다.

## 11. 방법이 주장하지 않는 것

- C는 독립 human physical-validity probability가 아니다.
- multiplication이 유일하거나 최적인 fusion이라는 주장이 아니다.
- support/contact error를 해결했다는 주장이 아니다.
- 새로운 object detector, relation generator, open-vocabulary vocabulary를
  제안하지 않는다.
- 세 predictor 결과는 하나의 shared 3DSSG target에서의 cross-predictor
  behavior이며 cross-dataset generalization이 아니다.

## 12. 논문에서 사용할 용어

사용:

- source relation score.
- predicate semantics.
- same-pair geometry.
- predicate–geometry compatibility.
- relation-consistent compatibility.
- transformation averaging.
- family-aware re-ranking.
- support/contact kept in source order.

사용하지 않음:

- 구현 파일에서만 사용하는 축약명이나 실험 식별자.
- source relation score를 calibrated probability처럼 읽히게 하는 표현.
- 구현 세부 절차를 전면에 내세우는 label.
- compatibility를 physical-validity probability로 해석하는 표현.
- 모든 relation family와 dataset에 보편적으로 적용되는 최적 rescorer.
