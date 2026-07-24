# RelCompat3D `user_v4.tex` 통합 재검토

- 검토일: 2026-07-24
- 대상: `paper/user_v4.tex`
- 기준 제목: **RelCompat3D: Predicate–Geometry Compatibility for Re-ranking 3D Scene Graph Relations**
- 범위: transcript의 논리, 영어, claim, notation, figure와 table 참조, caption, 실험 근거, section별 역할
- 인용: 표기 방식은 검토하지 않았다. 선행연구나 section별 첫 약어에 인용이 존재하는지만 확인했다.
- 형식: `user_v4.tex`의 PDF와 페이지 배치는 이번 검토에서 확정하지 않았다.

상태 표시는 다음과 같다.

- `[x]` 해결 완료
- `[~]` 내용은 타당하지만 문장이나 배치 보완 필요
- `[ ]` 제출 전 수정 필요
- `[제외]` 사용자 판단에 따라 검토 대상에서 제외

## 전체 판단

`user_v4.tex`의 핵심 흐름은 accept 관점에서 정합하다.

1. Introduction은 high-scoring relation과 ordered-pair geometry의 불일치를 문제로 제기한다.
2. Method는 ordered-pair identity, source-score-excluded compatibility, transformation averaging, family-aware re-ranking으로 이 문제에 답한다.
3. Experiments는 Source 비교, matched fusion, ordered-pair controls, transformation controls, point- and mesh-based audit로 핵심 설계를 검증한다.
4. Discussion and Limitations는 shared-target 범위를 넘는 일반화를 주장하지 않는다.
5. Conclusion은 새로운 주장 없이 main result를 범위 안에서 요약한다.

치명적인 과학적 모순은 발견되지 않았다. 제출 전에 우선 고칠 사항은 다음 다섯 가지다.

1. Abstract의 `on a same ... validation set`을 고친다.
2. Table 3 헤더의 `$\Delta$V//`와 audit 본문의 `$K=50V$`를 고친다.
3. loss equation의 고정 숫자를 일반화된 hyperparameter 기호로 바꾼다.
4. $\sigma$, $\Delta z_i$, $\Delta z_i^{\rm norm}$, $\theta_q$를 정의한다.
5. Introduction에 연속해서 들어간 동일한 gap 문단 중 하나를 삭제한다.

영어와 압축 문제는 그다음 우선순위다.

## 기존 이슈 번호 재매핑

중복된 지적은 아래 통합 이슈에서 한 번만 설명한다.

| 기존 번호 | 현재 상태 | 처리 |
|---|---|---|
| 1--59 | `[x]` | `user_v4.tex`에서 재확인 완료 |
| 14 | `[x]` | Method 끝의 한 문장으로 supplement 범위를 안내하여 해결 |
| 60 | `[x]` | 재확인 완료 |
| 61 | `[x]` | 이전 collocation과 ordered-pair 표현을 재확인하여 해결 완료 |
| 62--75 | `[x]` | 재확인 완료 |
| 76 | `[x]` | shuffled-geometry control이 marginal geometry 대비 pair association을 직접 검사하므로 현재 해석은 충분 |
| 77--78 | `[x]` | 재확인 완료 |
| 79 | `[~]` | 통합 이슈 D에 병합 |
| 80--86 | `[x]` | 재확인 완료. 86번 score range 검증 결과는 아래에 보존 |
| 87 | `[제외]` | 사용자 요청에 따라 제외 |
| 88 | `[x]` | 533/548 상세와 sensitivity를 supplement에 두는 기존 paper policy를 재확인 |
| 89 | `[x]` | direct component removal 완료 |
| 90 | `[x]` | supplement의 $K=100$ family table과 all-$K$ artifacts가 contribution 범위를 충분히 뒷받침 |
| 91--92 | `[x]` | Figure와 Table의 역할 및 본문 참조 재확인 완료 |
| 93 | `[제외]` | 추가 limitation 제안에서 제외 |
| 94--97 | `[x]` | 재확인 완료 |
| 98 | `[ ]` | Table 3과 audit 본문의 남은 오탈자를 통합 이슈 D에서 처리 |
| 99--100 | `[x]` | contribution 압축과 story 연결 재확인 완료 |
| 101 | `[~]` | 통합 이슈 E |
| 102 | `[~]` | 통합 이슈 E와 주석 정리 항목에 병합 |
| 103--104 | `[x]` | notation table과 supplement 제목 반영 완료 |
| 105 | `[~]` | 문법 오탈자는 통합 이슈 A, 수식 기호는 통합 이슈 F에서 처리 |

### 기존 1--59번 이슈 재확인 `[x]`

기존 문법, 용어, caption, metric, family-aware ranking, source-order preservation 관련 수정은 `user_v4.tex`에 유지되어 있다. 기존 14번은 Method 끝의 다음 문장으로 해결되었다.

> The supplement provides the complete counterfactual rules, optimization details, proofs, and matched controls.

이 문장은 main Method에서 생략한 재현 세부사항의 위치를 한 번만 안내한다. 같은 목록을 다른 문단에서 다시 쓸 필요는 없다.

### 기존 86번 score range 검증 `[x]`

평가에 사용한 proximity와 vertical-order candidates에서 source relation score는 모두 음수가 아니었다.

| Predictor | 관찰 범위 | Candidates | Negative | Exact zero |
|---|---:|---:|---:|---:|
| VL-SAT | $[5.30\times10^{-22},\,0.9954]$ | 110,424 | 0 | 0 |
| Open3DSG | $[0.6394,\,0.9281]$ | 79,722 | 0 | 0 |
| SGFN | $[4.61\times10^{-20},\,0.5846]$ | 110,424 | 0 | 0 |

Open3DSG의 전체 candidate 범위도 $[0.5772,\,0.9707]$로 음수가 없다. 따라서 현재 product ranking에서 음수 score로 순서가 역전되는 문제는 없다.

이 결과는 `paper/aaai/sec/supplement.tex`의 `Model and Preprocessing Details`에 Table~`\ref{tab:source-score-ranges}`로 반영했다. 표는 re-ranked proximity와 vertical-order candidates의 predictor별 count, minimum, maximum을 보고한다. 본문은 observed ranges가 calibrated probability intervals가 아니며 모든 score가 nonnegative임을 명시한다.

#### Main paper 반영 판단

Main에 범위 수치를 다시 넣을 필요는 없다. Problem Formulation의 `paper/user_v4.tex:79`는 predictor별 score의 종류를 설명하고, predictor 사이에서 score를 직접 비교하지 않는다고 이미 명시한다. Supplement 표가 product utility의 sign assumption과 재현성을 충분히 보완한다.

Main에서 이 사실을 꼭 연결해야 한다면 `paper/user_v4.tex:79`의 다음 문장 뒤에 넣는다.

> Candidates are ranked separately for each predictor, so existing scores are never compared across predictors.

선택적 추가 문장:

> All source scores observed in the re-ranked families are nonnegative, with predictor-specific ranges reported in the supplement.

이 문장은 정확하지만 main claim에 직접 필요한 결과는 아니다. 페이지가 제한되어 있다면 추가하지 않는 편을 권장한다.

### 기존 89번 direct component removal `[x]`

동일한 frozen rows와 family-aware route에서 linked pairwise loss와 transformation averaging을 각각 제거한 실험이 완료되었다.

- Pairwise loss 제거는 aggregate Recall과 Violation을 매우 작게 바꾼다.
- Transformation averaging 제거도 aggregate metric에는 작은 영향을 주지만 endpoint와 predicate의 exact consistency를 깨뜨린다.
- 따라서 pairwise loss는 training regularizer로 설명하는 것이 정확하다.
- Transformation averaging은 주요 metric gain의 원인보다 exact consistency guarantee로 설명하는 것이 정확하다.

이 결과는 `paper/aaai/sec/supplement.tex`의 `Guarantees and Compatibility Analyses`에 Table~`\ref{tab:component-removals}`와 해석 문단으로 반영했다. 표는 세 predictor의 $K=50$과 $K=100$에서 Full Linear, No pairwise loss, No transformation averaging을 비교한다. 본문은 no-pairwise condition이 refit 결과이고 no-averaging condition이 fitted full model에서 inference-time averaging만 제거한 결과임을 구분한다.

Supplement 해석은 다음 범위를 유지한다.

> Removing the linked pairwise term changes aggregate metrics only marginally. Removing transformation averaging has similarly small aggregate effects but breaks exact endpoint and predicate consistency. The averaging step therefore provides an exact consistency guarantee rather than the main source of the aggregate gains.

#### Main paper 반영 판단

Main paper에 별도 table이나 수치를 추가할 필요는 없다. Main contribution은 transformation averaging을 aggregate gain의 유일한 원인으로 주장하지 않고 exact consistency guarantee로 설명한다. Method의 group-averaging 식과 supplement의 direct removal이 이 claim을 충분히 뒷받침한다.

다만 reviewer가 main ablation과 supplement evidence의 연결을 바로 찾을 수 있도록 한 문장 pointer는 복원하는 편이 좋다. `paper/user_v4.tex:290`의 Compatibility-only 해석 문장 바로 다음, 현재 주석 처리된 line 291 위치에 넣는다.

권장:

> The supplement reports feature-removal analyses, direct component removals, transformation checks, and matched controls for both estimators.

Main에서 `pairwise loss removal changes little`을 별도로 강조할 필요는 없다. 이는 pairwise term을 main gain으로 과장하지 않게 해 주지만, 상세 효과는 supplement에서 확인하는 편이 본문 흐름과 페이지 효율에 더 적합하다.

### 기존 88번 Open3DSG coverage 위치 `[x]`

Repository의 paper policy를 다시 확인했다. Main result는 public-pipeline predictions와 full 548-context denominator를 사용한다. Public-eligible 533-context route와 recovered 548-context route는 sensitivity evidence다. 상세 533/548 수치와 15 empty contexts는 supplement에 유지하기로 이미 결정되어 있다.

`paper/aaai/sec/supplement.tex`은 다음을 모두 제공한다.

- public preprocessing의 533/548 coverage
- 누락된 15 contexts를 empty candidate sets로 처리하는 main denominator
- public eligible, public full target, recovered full coverage의 sensitivity table

따라서 `user_v4.tex`의 다음 문장만으로 main evaluation scope는 충분하다.

> All evaluations use the same scope: 157 scans, 548 relation contexts, and 3,972 exact-match ground-truth relations ...

Main에 533/548 상세 문장을 추가하라는 이전 통합 이슈 B는 삭제한다.

## 현재 미해결 통합 이슈

### 통합 이슈 A. 남은 문법 오류 `[ ]`

- 연결 번호: 105
- 심각도: 높음
- 위치: Abstract, `paper/user_v4.tex:3`

원문:

> ... on a same 3D Semantic Scene Graph (3DSSG) validation set.

`a same`은 문법적으로 맞지 않다. Abstract 안에서 약어를 풀어 쓰면서 shared evaluation scope를 유지하려면 다음처럼 고친다.

권장:

> ... on a shared 3D Semantic Scene Graph (3DSSG) validation set.

이전 검토에서 지적한 `assign high scores`, `corresponding ordered pair`, `reconstructed ordered-pair geometry`, `\tau_a` 정의 순서는 현재 `user_v4.tex:21`, `user_v4.tex:23`, `user_v4.tex:87`, `user_v4.tex:123--125`에서 해결되어 있다. 같은 의미가 이미 충분히 구현됐으므로 이슈로 남기지 않는다.

### 기존 90번 relation-family evidence `[x]`

Contribution 3의 predictor-dependent behavior는 Table 1과 Figure 3이 뒷받침한다. Relation-family-dependent behavior는 support/contact preservation, Product (all families), supplement의 $K=100$ family table이 뒷받침한다. Released artifacts에는 나머지 $K$ 값도 있다.

Main의 다음 문장은 특정한 모든 $K$ 값을 PDF table로 제공한다고 주장하지 않는다.

> The supplement reports per-family metrics and the family composition of the selected top-$K$ predictions.

$K=100$ family table도 selected top-$K$ predictions에 해당하므로 의미상 충분하다. 권장 버전과 정확히 같지 않다는 이유만으로 이슈를 유지하지 않는다.

### 통합 이슈 D. Table 3과 audit 본문의 오탈자 `[ ]`

- 연결 번호: 79, 98
- 심각도: 높음
- 위치: Experiments, Table 3 `paper/user_v4.tex:299--300`, Point- and Mesh-Based Consistency Audit `paper/user_v4.tex:315`

#### D-1. Table 3 헤더 오류

원문:

```tex
Predictor & Source & Linear & $\Delta$V//
& Coverage (M/D) \\
```

권장:

```tex
Predictor & Source & Linear & $\Delta V$ & Coverage (M/D) \\
```

현재 caption은 Source, Linear, $\Delta V$, coverage를 모두 설명하므로 헤더 수정 후에는 row와 column 의미가 충분하다. CI range를 main table에 다시 넣을 필요는 없다. Paired intervals는 supplement에 유지하면 된다.

#### D-2. audit 본문의 metric 오탈자

원문:

> Table~\ref{tab:surface-audit} reports the $K=50V$ audit for RelCompat3D-Linear.

`$K=50V$`는 정의되지 않은 표기다.

권장:

> Table~\ref{tab:surface-audit} reports the $K=50$ audit for RelCompat3D-Linear.

이후의 `All changes are reductions except the SGFN tie at $K=5$`는 이전의 모호한 `same direction`을 이미 정확하게 대체한다. 따라서 결과 해석 문장은 추가 이슈로 남기지 않는다.

### 통합 이슈 E. Introduction과 Related Work 압축 `[~]`

- 연결 번호: 101
- 심각도: 중간
- 위치: Introduction `paper/user_v4.tex:23--26`, Related Work `paper/user_v4.tex:45--47`

#### E-1. Introduction에 같은 gap 문단이 연속으로 두 번 존재

`paper/user_v4.tex:23--24`와 `paper/user_v4.tex:26`은 모두 다음 논리를 반복한다.

- 기존 predictor도 geometry를 사용한다.
- source relation score는 ordered-pair compatibility를 직접 추정하지 않는다.
- 따라서 $T$, $G$, $Z$를 분리한다.

두 문단을 모두 둘 필요가 없다. 짧은 `paper/user_v4.tex:26`을 남기고 `paper/user_v4.tex:23--24`를 삭제한다. 26번 줄만으로도 기존 연구가 geometry를 무시한다는 잘못된 framing을 피하고, gap과 설계 동기를 연결한다.

#### E-2. Related Work의 downstream-use 열거

원문:

> Open-vocabulary 3D perception provides queryable object and region features, and graph systems connect features to compact scene representations for querying, planning, navigation, online mapping, and language interaction.

`querying, planning, navigation, online mapping, and language interaction`은 논문의 reliability gap을 설명하는 데 모두 필요하지 않다. `querying`과 embodied interaction만 남겨도 downstream importance가 유지된다.

권장:

> Open-vocabulary 3D perception provides queryable object and region features, and graph systems use them for querying and embodied interaction.

다음 문장의 열거도 의미를 유지하면서 묶을 수 있다.

원문:

> Recent 3D scene graph methods extend this direction to open-vocabulary objects, open-set relations, vision-language model (VLM) features, online graph generation, and functional relations.

권장:

> Recent 3D scene graph methods extend this direction to open-vocabulary objects and relations, online generation, and functional reasoning.

#### E-3. 같은 subsection의 fixed-generator 대비 반복

`3D Scene Graph Prediction` subsection의 첫 문단은 이미 다음 차이를 설명한다.

> These methods and RelCompat3D both use reconstructed scene evidence, but they optimize relation generation, whereas RelCompat3D re-ranks fixed relation candidates after prediction.

둘째 문단의 다음 두 문장은 같은 대비를 반복한다.

> These methods broaden the candidate vocabulary and downstream uses. RelCompat3D keeps each predictor fixed and tests whether its selected predicate is compatible with the reconstructed geometry of the corresponding ordered pair.

첫 문장은 앞의 method 열거를 요약할 뿐 새 정보를 거의 추가하지 않는다. 삭제해도 된다. 둘째 문장은 fixed predictor 대비를 반복하므로 reliability question에 초점을 맞춘 다음 문장으로 바꾼다.

권장:

> RelCompat3D instead asks whether an already predicted predicate is supported by the reconstructed geometry of its ordered pair.

이렇게 하면 첫 문단은 `generation versus re-ranking`, 둘째 문단은 `vocabulary expansion versus geometric support`를 각각 담당한다.

현재 `user_v4.tex`의 Method에는 이전의 중복 control 목록이 더 이상 없다. Experiments의 `paper/user_v4.tex:167`만 실제 perturbation 범위를 설명하므로 유지한다.

Introduction과 Related Work 합계에서 약 120--160 words를 줄일 수 있다. 가장 큰 삭제는 중복 Introduction 문단이다. 그다음으로 downstream-use 열거와 fixed-generator 대비를 압축한다.

### 통합 이슈 F. Loss equation 일반화와 기호 정의 `[ ]`

- 연결 항목: F14, F16
- 심각도: 높음
- 위치: Method, Linear Estimator `paper/user_v4.tex:101--110`, Nonlinear Estimator `paper/user_v4.tex:112--121`, training objective `paper/user_v4.tex:127--136`

#### F-1. Loss equation의 고정 숫자

현재 loss equation은 margin weight `0.25`, margin `1`, regularization coefficient `10^{-4}`를 수식에 직접 넣는다. 이는 implementation choice가 method definition처럼 보이게 한다.

현재:

```tex
\mathcal L_q=\mathcal L_{\rm BCE}
+0.25\,\mathbb E_{\mathcal P}
\left[\log\left(1+e^{1-(\ell^q_{i^+}-\ell^q_{i^-})}\right)\right]
+10^{-4}\mathcal R(\theta_q).
```

현재 `user_v4.tex:134--143`에는 일반화된 수식이 이미 들어갔지만, 수식 뒤의 설명은 이전 숫자 중심 표현을 유지한다. Lines 125--143을 다음 문단 전체로 정리한다.

권장 본문:

```tex
Training combines this augmentation with a linked positive--counterfactual
ranking loss. For every linked positive--counterfactual pair
$(i^+,i^-)\in\mathcal P$, the logits
$\ell_i^q=f_q(T_i,a_i,G_i)$ receive a margin penalty:
\begin{equation}
\begin{aligned}
\mathcal L_q={}&\mathcal L_{\rm BCE}
+\lambda_{\rm pair}\,\mathbb E_{\mathcal P}
\left[\operatorname{softplus}
\left(m-(\ell^q_{i^+}-\ell^q_{i^-})\right)\right]\\
&+\lambda_{\rm reg}\mathcal R(\theta_q).
\end{aligned}
\end{equation}
Here $\mathcal L_{\rm BCE}$ is binary cross-entropy over positive and
counterfactual examples. The second term is a softplus margin-ranking loss
with margin $m$. We set $m=1$, $\lambda_{\rm pair}=0.25$, and
$\lambda_{\rm reg}=10^{-4}$ in all experiments. These values are shared
across estimators and predictors without predictor-specific search.
$\mathcal R$ is an $\ell_2$ penalty on the non-bias parameters in
$\theta_q$, where $\theta_q$ denotes the trainable parameters of estimator
$q$. Both estimators are fitted exclusively on the training split.
```

이 구성은 method definition의 $m$, $\lambda_{\rm pair}$,
$\lambda_{\rm reg}$과 실제 설정값을 분리한다. 기존 설명의 다음 두 부분은 삭제한다.

- `with margin $m=1$ and weight 0.25`
- `The pairwise weight and the $\ell_2$ coefficient $10^{-4}$ are shared ...`

`user_v4.tex:126--133`의 이전 loss equation 주석도 최종 수식을 남긴 뒤 삭제한다.

#### F-2. 수식 기호 정의

Equation 순서는 compatibility, Linear features, MLP, loss, transformation averaging, ranking, Recall, Violation으로 자연스럽다. 재정의나 순서 충돌도 없다. 다만 다음 기호는 최초 사용 시 정의가 부족하다.

- $\sigma$: logistic sigmoid임을 명시한다.
- $\theta_q$: estimator $q$의 trainable parameters임을 명시한다.
- $\Delta z_i$: subject center height minus object center height임을 명시한다.
- $\Delta z_i^{\rm norm}$: $\Delta z_i$를 두 OBB height의 평균으로 나눈 값임을 명시한다.

세 위치에 나누어 넣는 것이 가장 자연스럽다.

##### F-2-1. $\sigma$

`paper/user_v4.tex:90`의 compatibility equation 바로 뒤, 현재 `then average over ...` 문장 앞에 넣는다.

추가:

> Here $\sigma$ denotes the logistic sigmoid.

그다음 현재 line 91의 `then average`를 `We then average`로 바꾼다. 완성된 연결은 다음과 같다.

> Here $\sigma$ denotes the logistic sigmoid. We then average over the valid family-specific endpoint/predicate transformations to obtain the transformation-consistent score $C_i^{\mathrm{tr},q}$.

##### F-2-2. $\Delta z_i$와 $\Delta z_i^{\rm norm}$

`paper/user_v4.tex:107`의 Linear feature equation 바로 뒤, 현재 `Here $\phi_T$ contains predicate indicators ...` 문장 앞에 넣는다.

추가:

> Let $z_{s_i}$ and $z_{o_i}$ denote the vertical coordinates of the subject and object OBB centers, and let $h_{s_i}$ and $h_{o_i}$ denote their OBB heights. We define $\Delta z_i=z_{s_i}-z_{o_i}$ and $\Delta z_i^{\rm norm}=2\Delta z_i/(h_{s_i}+h_{o_i})$.

이후 현재 `Here $\phi_T$ ...` 문장을 그대로 유지한다.

##### F-2-3. $\theta_q$

$\theta_q$는 compatibility equation이 아니라 loss의 regularization term에서 처음 필요하다. 따라서 별도 앞 문단에 넣지 않고 F-1의 loss 설명 안에서 정의한다.

> $\mathcal R$ is an $\ell_2$ penalty on the non-bias parameters in $\theta_q$, where $\theta_q$ denotes the trainable parameters of estimator $q$.

이 세 정의를 반영하면 현재 정의된 `\tau_a`와 함께 F16의 notation 검사가 완료된다.

#### F-3. Compact MLP configuration의 근거

Supplement는 두 hidden units, 69 parameters, optimization steps, learning rates를 보고한다. Counterfactual threshold와 pair-weight sensitivity도 제공한다. 다만 two-hidden-unit width를 선택한 이유는 문장으로 설명하지 않는다.

Main에 근거를 넣는다면 `paper/user_v4.tex:111`의 다음 문장 바로 뒤에 둔다.

> RelCompat3D-MLP uses one shared single-hidden-layer ReLU network with two hidden units.

추가:

> The two-unit design has 69 parameters, compared with 66 across the three Linear heads, and tests a nonlinear compatibility function without substantially increasing model size.

그 뒤에 현재 문장을 이어 쓴다.

> Its input $\Psi_i$ contains family and predicate indicators, ...

이 문장은 configuration의 선택 이유를 parameter count와 직접 연결한다. 별도의 width sweep을 main에 추가할 필요는 없다. 같은 수치는 supplement의 architecture details에도 이미 존재한다.

## 현재 주석 처리된 문장 정리

`user_v4.tex`에는 manuscript prose와 관련된 주석이 다섯 개 있다.

| 위치 | 주석 내용 | 판단 | 권장 처리 |
|---|---|---|---|
| Experiments, Baselines and Training, line 168 | `, with exact transformations in the supplement` | 불완전한 문장 조각이며 Method의 supplement pointer와 겹침 | 삭제 |
| Experiments, Metrics, line 182 | uncertainty, decidable-only Violation, coverage 수식 전체 | line 181의 active sentence가 같은 내용을 짧게 안내함 | 삭제 |
| Results, comparator discussion, line 232 | family-specific results가 support/contact regression과 함께 나타날 수 있다는 문장 | line 231의 `changes support/contact selections`만으로 현재 scope 설명이 충분함 | 삭제 |
| Results, comparator discussion, line 233 | pooled family-conditioning ablation 안내 | pooled model이 `user_v4.tex` main setup에서 더 이상 소개되지 않음 | 삭제 |
| Ablations and Controls, line 291 | feature removal, linked ordering, transformation checks, matched controls 안내 | main control table 밖의 중요한 검증 위치를 알려줌 | 짧게 복원 |

마지막 주석은 다음처럼 복원하는 것이 좋다.

> The supplement reports feature-removal analyses, direct component removals, transformation checks, and matched controls for both estimators.

중복을 피하려면 Method 끝의 pointer는 다음처럼 줄인다.

> The supplement provides the complete counterfactual rules, optimization details, and proofs.

이렇게 하면 Method pointer는 재현 세부사항을 담당하고 Results pointer는 추가 검증을 담당한다. 역할이 겹치지 않는다. 삭제 대상으로 분류한 주석은 version control에 남으므로 source에 계속 보존할 필요가 없다.

## F4--F20 처리 여부

| 항목 | 상태 | `user_v4.tex` 기준 판단 |
|---|---|---|
| F4 Figure와 Table 본문 참조 | `[x]` | Figure 1--3과 Table 1--3이 모두 본문에서 최소 한 번 호출된다. |
| F5 caption 명확성 | `[~]` | Figure 1--3과 Table 1--2는 목적, metric, 비교 대상을 충분히 설명한다. Table 3도 caption은 충분하며 헤더의 `//`만 수정하면 된다. |
| F6 section별 첫 줄임말 인용 존재 | `[x]` | Introduction, Related Work, Method, Experiments, Discussion, Conclusion에서 첫 predictor, dataset, benchmark 약어의 문장에 인용이 존재한다. 인용 표기 방식은 판단하지 않았다. |
| F7 `A's B` 자제 | `[x]` | prose에서 해당 영어 소유격을 발견하지 않았다. `of` 또는 명사 수식 구조를 사용한다. |
| F9 용어 통일 | `[x]` | source relation score, ordered pair, ordered-pair geometry, exact-match Recall, verifier-derived Violation, vertical-order가 문법적 역할에 맞게 통일되어 있다. |
| F11 em dash 자제 | `[x]` | em dash를 사용하지 않는다. LaTeX의 `--`는 compound 또는 range 표기다. |
| F12 긴 문장 | `[x]` | 긴 문장은 candidate identity와 feature definition 같은 수학적 정의에 집중되어 있다. 일반 prose의 호흡은 충분히 짧다. 권장 버전과 다르다는 이유만으로 추가 분할 이슈를 만들지 않는다. |
| F14 수식의 숫자 일반화 | `[ ]` | loss equation의 `0.25`, `1`, `10^{-4}`를 통합 이슈 F처럼 일반화해야 한다. Feature intercept `1`과 $d(p)$의 sign mapping은 hyperparameter가 아니므로 유지한다. |
| F15 hyperparameter 근거 | `[~]` | train/dev split 역할과 counterfactual-policy sensitivity는 충분하다. Two-hidden-unit width의 선택 이유만 통합 이슈 F처럼 한 문장으로 보완한다. |
| F16 수식과 기호 점검 | `[~]` | equation 순서와 수학적 연결은 맞고 `\tau_a`도 정의되어 있다. 통합 이슈 F의 $\sigma$, $\theta_q$, $\Delta z_i$, $\Delta z_i^{\rm norm}$ 정의가 남았다. |
| F17 contribution bullet 간결성 | `[x]` | 세 bullet이 각각 한 문장이고 problem, method, evaluation role을 핵심 위주로 전달한다. |
| F18 story 일관성 | `[x]` | failure, factor separation, pair identity, transformations, family-aware ranking, audit가 Method와 Experiments의 직접 근거에 연결된다. |
| F19 Introduction과 Related Work 중복 | `[~]` | Introduction lines 23--26의 동일 gap 문단을 하나 삭제하고, 통합 이슈 E의 downstream-use와 fixed-generator 대비를 압축하면 해결된다. |
| F20 Intro와 Related Work 압축 | `[~]` | 통합 이슈 E의 구체적 삭제와 교체를 적용하면 약 120--160 words를 줄일 수 있다. 현재 Method의 control 목록 중복은 이미 해결되어 있다. 직접 manuscript를 수정하지는 않았다. |

## Section별 최종 체크

| Section | 상태 | 판단 |
|---|---|---|
| Abstract | `[~]` | 문제, 방법, 결과, audit가 모두 있고 정의되지 않은 수학 기호나 citation이 없다. `on a same` 문법 오류만 고치면 된다. |
| Introduction | `[~]` | problem, gap, method, evaluation, contributions의 흐름이 좋다. 연속된 동일 gap 문단과 Related Work 중복을 줄여야 한다. |
| Related Work | `[~]` | subsection별 연구와 차이는 명시된다. downstream-use와 fixed-generator 대비를 압축할 수 있다. |
| Method | `[~]` | 수식 흐름, estimator 구분, transformation 정의는 정합하다. loss hyperparameter 일반화와 일부 기호 정의가 남았다. |
| Experiments | `[~]` | main result, controls, audit가 claim과 대응한다. Table 3 헤더와 `$K=50V$` 오탈자를 고쳐야 한다. |
| Discussion and Limitations | `[x]` | shared-target 범위를 명시하고 과도한 일반화를 피한다. 추가 limitation 확대는 권장하지 않는다. |
| Conclusion | `[x]` | 새 주장 없이 motivating problem과 reported point estimates를 연결한다. |

## Introduction claim과 evidence 연결

| Introduction의 claim 또는 design | Method 대응 | Experiment 대응 | 판단 |
|---|---|---|---|
| high score와 ordered-pair geometry의 불일치 | compatibility formulation | Figure 1, Table 1, Figure 3 | 충분 |
| source relation score와 compatibility 분리 | $C_i^q$에서 $Z_i$ 제외 | Compatibility only, RankAvg, RRF | 충분 |
| ordered-pair identity 보존 | pair identity와 relation identity 정의 | Wrong pair, Shuffled geometry | 충분 |
| relation-preserving transformations | transformation orbit와 averaging | Fixed-predicate swap, exact checks, component removal | 충분 |
| family-aware re-ranking | $u_i^q$와 family list | Table 1, Product (all families), family slices | 충분 |
| alternative geometric measure | main verifier와 분리된 audit | Table 3와 supplement all-$K$ audit | 충분 |

Introduction에서 강조했지만 근거가 없는 main claim은 발견되지 않았다. 반대로 main experiment 중 Introduction에 전혀 예고되지 않은 핵심 결과도 없다.

## Figure와 Table 참조 및 caption

모든 Figure와 Table은 본문에서 최소 한 번 참조된다.

| Artifact | 본문 참조 | Caption 판단 |
|---|---|---|
| Figure 1 | Introduction | failure case, source, relation, rank change를 설명한다. |
| Figure 2 | Method overview | input separation, source score 사용 시점, rank change를 설명한다. |
| Figure 3 | Recall--Violation Results | metric 방향, $K$ 순서, predictor별 axis 차이를 설명한다. |
| Table 1 | Recall--Violation Results | target, metrics, Source, ranking rules를 설명한다. |
| Table 2 | Ablations and Controls | Linear controls와 MLP full row의 역할을 설명한다. |
| Table 3 | Audit subsection | 헤더 오류를 고치면 row와 column 의미가 충분하다. |

Figure 3와 Table 2 caption에 shared target 설명을 반복해서 추가할 필요는 없다. Experimental Setup과 Table 1이 공통 평가 범위를 정의하고, 해당 artifact가 본문에서 바로 연결된다.

## 제출 전 수정 우선순위

### P0

1. 통합 이슈 A의 Abstract 문법 오류를 고친다.
2. 통합 이슈 D의 Table 3 헤더와 `$K=50V$`를 고친다.
3. 통합 이슈 F처럼 loss equation의 고정 숫자를 일반화한다.
4. 통합 이슈 F의 누락된 기호를 정의한다.

### P1

5. Introduction의 중복 gap 문단을 하나 삭제한다.
6. Related Work의 downstream 열거와 fixed-generator 대비를 압축한다.
7. Compact MLP width의 선택 이유를 supplement에 한 문장으로 설명한다.

### P2

8. 주석 네 개를 삭제하고 Results의 추가-evidence pointer 하나를 짧게 복원한다.

이 수정 후에는 transcript의 scientific scope를 더 넓히기보다 페이지 배치, overfull, final title, anonymous release consistency를 확인하는 단계로 넘어가는 것이 적절하다.
