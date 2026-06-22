# H002 Feasibility Check

Last updated: 2026-06-22

## Question

현재 H002는 다음 분리를 전제로 한다.

```text
semantic score != geometry validity != relation reliability
```

현재 posterior framing:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

여기에 point cloud와 multi-view evidence를 함께 넣는 방향이 합리적인가?

## Verdict

합리적이다. 단, H002에서는 이를 **더 강한 relation predictor**로 정의하면 scope가
너무 커지고, 기존 3DSSG relation prediction과 차별성이 약해진다.

가장 방어 가능한 정의는 다음이다.

```text
RGA evidence axis expansion:
semantic-geometry agreement -> semantic-geometry-visual agreement
```

확장 posterior:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

where:

- `S_e`: source semantic score/rank.
- `G_3D_e`: point cloud, OBB, contact, distance, vertical order, overlap,
  containment, support geometry.
- `V_mv_e`: multi-view crop, co-visible image evidence, subject/object visibility,
  appearance-context evidence.
- `C_e`: geometry and view coverage.
- `U_e`: uncertainty, abstain, low-evidence state.

## Why This Fits H002

H002의 핵심은 relation confidence를 단일 점수로 보지 않고, edge-level reliability를
factorized evidence로 설명하는 것이다. 따라서 point cloud + multi-view는 새
generator가 아니라 evidence factor 확장으로 들어가는 것이 맞다.

현재 H002가 막힌 지점은 posterior model capacity가 아니라 target independence다.

Observed issue:

```text
strict/weak target: HL vs LH or satisfied vs unsatisfied shortcut risk
redesigned target: less shortcut-prone but only N=27
codex_ver labels: usable for plumbing smoke, not human-confirmed evidence
```

Multi-view evidence가 특히 도움이 될 수 있는 부분은 같은 geometry condition 안에서
다음 두 상태를 구분하는 것이다.

```text
true_underconfidence vs dense_relation_noise
```

즉, geometry는 satisfied이지만 relation이 실제로 informative한지, 단순히 dense하고
trivial한지 판단하는 데 visual context가 보조 evidence가 될 수 있다.

## What It Is Not

이 방향은 다음으로 쓰면 안 된다.

```text
point cloud + multi-view relation predictor
```

이렇게 정의하면 H002의 claim이 relation generation 자체로 넓어지고, reviewer는
기존 multi-modal 3D scene graph predictor와의 SOTA 비교를 요구할 가능성이 크다.

H002에서의 올바른 framing:

```text
multi-modal factorized relation reliability
```

or:

```text
visual-geometric evidence factor for RGA-based relation reliability
```

## Recommended Order

### Step 1. Use Multi-View As Audit Evidence First

Multi-view를 바로 model input으로 넣지 않는다. 먼저 다음 working label을 더 안정적인
review label로 바꾸는 confirmation evidence로 사용한다.

```text
uncertain_needs_visual_or_mesh
true_underconfidence
dense_relation_noise
annotation_sparsity
ontology_mismatch
```

이 단계의 목표:

- object pair가 실제로 같은 local context에 있는지 확인.
- subject/object visibility가 충분한지 확인.
- relation이 informative한지 dense/trivial한지 판단.
- geometry-satisfied relation이 visual context에서도 자연스러운지 확인.

### Step 2. Promote Multi-View To Deployable Evidence Factor

Audit schema와 input feature schema를 분리한 뒤 `V_mv_e`를 deployable factor로 승격한다.

Candidate `V_mv_e` features:

| Feature | Meaning |
| --- | --- |
| `co_visible_view_count` | subject/object가 같은 view에서 함께 보이는 횟수 |
| `subject_visibility_score` | subject crop visibility / area / truncation quality |
| `object_visibility_score` | object crop visibility / area / truncation quality |
| `pair_crop_quality` | pair crop이 relation 판단에 충분한지 |
| `view_context_support` | 주변 context가 relation을 지지하는지 |
| `visual_relation_score` | VLM/visual scorer가 relation을 지지하는 정도 |
| `view_disagreement` | view 간 relation evidence가 충돌하는 정도 |
| `occlusion_risk` | occlusion 때문에 relation 판단이 불안정한 정도 |
| `no_view_or_low_visibility` | view evidence가 없거나 부족한 coverage state |

Important rule:

```text
label/audit evidence must not be used as deployable input feature.
```

### Step 3. Shortcut-Controlled Smoke

Multi-view factor를 추가하면 비교군은 다음처럼 확장한다.

| Baseline | Inputs |
| --- | --- |
| `semantic_only` | `S_e` |
| `geometry_only` | `G_3D_e` |
| `visual_only` | `V_mv_e` |
| `geometry_plus_visual` | `G_3D_e + V_mv_e` |
| `semantic_plus_geometry_visual` | `S_e + G_3D_e + V_mv_e` |
| `factorized_reliability_posterior` | `S_e + G_3D_e + V_mv_e + C_e + U_e` |

Required controls:

- wrong-pair view.
- shuffled-view.
- shuffled-geometry.
- no-view / low-visibility rows.
- same-family controlled split.
- same-rank-band controlled split.
- same-geometry-status controlled split.

### Step 4. Relation Family Priority

`proximity` is currently useful for target debugging but is not the best
multi-view payoff relation family. `close by` can be geometry-satisfied while
still being dense and visually uninformative.

Higher-priority families:

```text
support_contact
attached to
hanging on
connected to
```

Rationale:

- contact/attachment/hanging relations have clearer visual-geometric witnesses.
- multi-view can help distinguish real physical attachment from geometric
  near-contact artifacts.
- relation informativeness is less dominated by dense proximity noise.

## Feasibility In Current H002

Feasible now:

- Use existing contact sheets and mesh links as audit evidence.
- Define the `V_mv_e` feature contract without running a new predictor.
- Add multi-view to the future RGA schema as an evidence axis.
- Run current `codex_ver` label smoke without visual features to keep the next
  gate clean.

Not yet feasible as a method claim:

- training a multi-view factorized posterior with paper-level evidence.
- claiming visual evidence improves reliability.
- using `(codex_ver)` labels as human-confirmed visual audit labels.
- evaluating attachment-style visual factors without a dedicated relation-family
  target and controls.

## Decision

Adopt this as a next H002 hypothesis extension, but do not inject `V_mv_e` into
the current base `S_e/G_e/C_e/U_e` posterior path.

Current immediate path:

```text
summary_branch_v2.md / stages/ -> v10/v11 proximity feasibility ->
v12 LH-only path decision -> v13 label readiness -> v14 label fill -> v15 label ingestion ->
v16 target-independence audit -> v17 path decision -> v18 scene/geometry-aware repair plan ->
v19 scene/geometry-aware candidate mining -> v20 scene/geometry-aware label fill ->
scene/geometry-aware label ingestion
```

Future multi-view path:

```text
current factorized posterior validation -> human-confirmed / independent target
evidence -> V_mv_e feature contract -> shortcut-controlled visual-geometric
reliability smoke -> relation-family expansion
```

Promotion rule:

```text
V_mv_e must not become a deployable model input before the current
S_e + G_e + C_e + U_e posterior passes the independent-target validation gate.
```

The strongest framing is:

```text
H002 extends RGA from semantic-geometry agreement to semantic-geometry-visual
agreement, while keeping source score, 3D geometry evidence, multi-view evidence,
coverage, uncertainty, and label/audit supervision explicitly separated.
```

## Factor Combination Feasibility

### Current Combination

현재 H002 smoke의 `factorized_reliability_posterior`는 이름상 posterior지만,
구현상으로는 아직 structured factor graph가 아니다.

Current implementation:

```text
x_e = concat(S_e, G_e, C_e, U_e, hand-coded interactions)
P(R_e = 1 | x_e) = sigmoid(w0 + w^T x_e)
```

구체적으로는 다음 방식이다.

- numeric feature는 standardization한다.
- categorical feature는 one-hot으로 바꾼다.
- `semantic`, `geometry`, `coverage`, `uncertainty`, selected interaction을
  하나의 flat feature vector로 합친다.
- L2-regularized logistic regression으로 train-only smoke를 돌린다.

장점:

- 단순하고 재현 가능하다.
- feature ablation과 proxy baseline 비교가 쉽다.
- small-label hypothesis stage에서 over-claim을 줄인다.

한계:

- `factorized`라는 이름과 달리 evidence factor의 역할이 구조적으로 분리되어
  있지는 않다.
- `coverage`와 `uncertainty`가 geometry evidence를 gate하지 않는다.
- semantic rank proxy가 강하면 linear combiner가 rank direction을 그대로 따라가기
  쉽다.
- relation family별 witness 차이를 충분히 반영하지 못한다.

### Candidate 1. Gated Evidence Model

Coverage와 uncertainty가 geometry evidence의 사용 여부를 gate한다.

```text
P(R=1) = sigmoid(f_sem(S) + gate(C,U) * f_geom(G) + f_uncertainty(U))
```

Why useful:

- `missing`, `unsupported`, `uncertain` geometry를 낮은 reliability와 같은 값으로
  뭉개지 않는다.
- H002의 핵심 구분인 `geometry validity != relation reliability`를 구조적으로
  반영한다.
- multi-view가 들어올 때 `view_coverage`도 같은 gate로 처리할 수 있다.

Risk:

- 현재 codex target이 rank-confounded이면 gated model도 rank proxy를 넘는다는
  주장을 하기 어렵다.

Priority:

```text
high
```

### Candidate 2. Residual Reliability Model

Semantic prior가 설명한 뒤 남는 residual을 geometry/coverage/uncertainty가 설명하는지
검증한다.

```text
logit P(R=1) = logit P_sem(R=1 | S) + Delta(G,C,U)
```

Core question:

```text
Does non-semantic evidence explain relation reliability beyond semantic rank?
```

Why useful:

- 현재 blocker인 `negative_rank_only`와 직접 맞붙는다.
- reviewer defense가 명확하다.
- H002의 다음 gate인 target independence audit과 잘 맞는다.

Priority:

```text
highest for the next modeling check
```

### Candidate 3. Pairwise Rank-Matched Ranking Loss

Pointwise binary classification 대신 matched pair에서 positive score가 negative score보다
높아지도록 학습한다.

```text
score(e_pos) > score(e_neg)
```

Recommended pair condition:

- same predicate family.
- same predicate label if possible.
- same geometry status.
- same coverage state.
- close `rank_in_context`.

Why useful:

- Earlier rank-matched pilot results, now summarized in `summary_branch_v2.md`
  and `stages/v1_rga_pilot.md`,
  suggested pairwise accuracy can be more favorable than grouped metrics.
- 현재 label size가 작기 때문에 pairwise objective가 target 구조에 더 맞을 수 있다.

Risk:

- pair construction itself can become a shortcut.
- paper claim에는 independent label/audit가 필요하다.

Priority:

```text
high after residual model
```

### Candidate 4. Monotonic / Constrained Additive Model

각 factor를 additive function으로 두되, 물리적으로 자연스러운 monotonic constraint를
둔다.

```text
reliability = f1(S) + f2(G) + f3(C) + f4(U)
```

Possible constraints:

- `p_geom_valid`가 증가할수록 reliability는 감소하지 않는다.
- uncertainty가 증가할수록 confidence는 증가하지 않는다.
- missing/unsupported geometry에서는 geometry factor의 영향이 제한된다.

Why useful:

- 해석 가능성이 높다.
- top-tier reviewer가 요구할 수 있는 "왜 단순한 결합이 아닌가"에 답하기 쉽다.

Priority:

```text
medium-high
```

### Candidate 5. Product-of-Experts / Log-Odds Factor Model

각 evidence factor를 별도 calibrated expert로 만들고 log-odds space에서 결합한다.

```text
logit P(R=1) =
  alpha_sem logit P_sem
  + alpha_geom logit P_geom
  + alpha_cov logit P_cov
  + alpha_unc logit P_unc
```

Why useful:

- `semantic`, `geometry`, `coverage`, `uncertainty` calibration을 분리해서 보고할
  수 있다.
- 현재 flat logistic보다 `factorized posterior`라는 이름에 더 가깝다.

Risk:

- 각 expert를 안정적으로 calibrate할 independent label 수가 아직 부족하다.

Priority:

```text
medium
```

### Candidate 6. Mixture-of-Experts By Relation Family

Relation family별로 다른 evidence combiner를 사용한다.

```text
P(R=1) = sum_k pi_k(predicate_family, coverage) * expert_k(S,G,C,U)
```

Why useful:

- `close by`, `supporting`, `higher than`, `attached to`는 필요한 witness가 다르다.
- multi-view evidence의 의미도 relation family별로 다르다.

Risk:

- 현재 H002 controlled target은 사실상 `proximity / close by`에 집중되어 있어
  mixture를 학습할 데이터가 부족하다.

Priority:

```text
medium now, high after relation-family expansion
```

### Candidate 7. Debiased / Orthogonalized Factor Model

Non-semantic factor에서 rank가 설명하는 부분을 제거한 뒤 posterior에 넣는다.

```text
G_res = G - E[G | rank_band, semantic_score]
U_res = U - E[U | rank_band, semantic_score]
P(R=1 | S, G_res, U_res, C)
```

Why useful:

- 현재 가장 큰 confounder인 semantic rank proxy를 직접 통제한다.
- "rank가 설명한 뒤에도 geometry/uncertainty signal이 남는가?"를 직접 검증한다.

Risk:

- small-N에서 residualization 자체가 불안정할 수 있다.

Priority:

```text
high as an audit/control, medium as final model
```

## Recommended Combination Path

현재 H002의 다음 결합 방식은 다음 순서가 가장 방어 가능하다.

```text
1. Residual Reliability Model
2. Gated Evidence Model
3. Pairwise Rank-Matched Ranking Loss
4. Debiased / Orthogonalized Factor Audit
5. Product-of-Experts calibration
6. Relation-family Mixture-of-Experts
```

Immediate recommendation:

```text
Do not train a larger generic model yet.
First test whether non-rank evidence explains residual relation reliability
after semantic/rank proxy is controlled.
```

Reason:

- Earlier rank-matched target diagnostics, now consolidated in `summary_branch_v2.md`
  and `stages/`,
  showed that factorized posterior was still weaker than a rank-only proxy under
  grouped CV.
- Pairwise signal exists, but grouped method support is not stable.
- Therefore the next problem is label/target independence and residual evidence,
  not model capacity.

## Multi-View Extension By Relation Family

If H002 expands beyond `proximity` using point cloud + multi-view evidence, the
best order is not uniform across relation families.

### 1. `support_contact`

Best first multi-view family.

Why:

- 3D witness is relatively concrete: contact/near-contact, vertical support,
  support area, normal alignment, stable OBB relation.
- Multi-view can verify whether contact is visually plausible or merely a point
  cloud/OBB artifact.
- It is closer to current H001/H002 geometry machinery than attachment.

Recommended evidence:

```text
G_3D_e: contact distance, vertical order, support overlap, surface normal cue
V_mv_e: co-visible contact crop, contact boundary visibility, occlusion risk
C_e: point coverage + view coverage
U_e: contact ambiguity / occluded support boundary
```

Best framing:

```text
visual-geometric support reliability
```

### 2. `attachment_deferred`

Most promising for novelty, but second in execution order.

Why:

- `attached to`, `hanging on`, `connected to` are less likely to collapse into
  dense proximity noise.
- Multi-view can distinguish real attachment/hanging plausibility from mere
  geometric closeness.
- This family better motivates semantic-geometry-visual agreement.

Risk:

- It needs a dedicated ontology and witness schema.
- `connected to` may require relation-specific caveats because visual contact and
  functional connection are not always the same.
- Current H001 attachment evidence is not yet promoted to the main claim, so H002
  should not inherit it as paper-ready evidence.

Recommended evidence:

```text
G_3D_e: contact/near-contact, relative pose, hanging direction, support/anchor plausibility
V_mv_e: attachment boundary visibility, hanging visual cue, connector/handle/cable cue
C_e: mesh/view coverage around contact region
U_e: occlusion, thin-structure missingness, anchor ambiguity
```

Best framing:

```text
visual-geometric evidence factor for attachment reliability
```

### 3. `relative_vertical`

Useful control family, but not the best first multi-view payoff.

Why:

- 3D geometry already captures most of the relation: higher/lower/above/below are
  largely metric vertical-order questions.
- Multi-view can help with object identity and occlusion, but adds less direct
  relation evidence than for contact/attachment.
- It is valuable as a negative/control family: if multi-view improves only
  vertical relations, the method may just be using easier object visibility cues.

Recommended evidence:

```text
G_3D_e: centroid/OBB vertical difference, overlap, relative height confidence
V_mv_e: object visibility, occlusion, same-view confirmation
C_e: point coverage and vertical extent reliability
U_e: partial object observation / truncated object geometry
```

Best framing:

```text
coverage-aware vertical relation reliability control
```

## Multi-View Execution Order

Recommended order:

```text
1. support_contact
2. attachment_deferred
3. relative_vertical
```

Rationale:

- `support_contact` is the best feasibility-to-payoff tradeoff.
- `attachment_deferred` is the strongest novelty extension but requires more
  schema work.
- `relative_vertical` is useful as a control and robustness family, but multi-view
  is less central to the relation.

Important rule:

```text
V_mv_e should first be used as audit/confirmation evidence, not deployable model
input, until S_e + G_e + C_e + U_e passes an independent-target gate.
```
