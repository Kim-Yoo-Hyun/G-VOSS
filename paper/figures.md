# RelCompat3D Figure Guide

Last updated: 2026-07-21 KST

이 문서는 현재 원고의 Figure 1--3이 각각 어떤 질문에 답하고, 어떤 정보만
보여주어야 하는지를 정의한다. 정확한 수치와 case identity는 experiment artifact에
근거하며, Figure는 서로 다른 역할을 맡는다.

1. **Figure 1:** high-scoring relation이 reconstructed ordered-pair geometry와
   충돌하는 failure를 한 사례로 보여준다.
2. **Figure 2:** RelCompat3D가 predicate/geometry와 predictor score를 어떻게
   분리하고 re-ranking에서 다시 결합하는지 보여준다.
3. **Figure 3:** Source, RelCompat3D-Linear, RelCompat3D-MLP의
   Recall--Violation operating point가 \(K\)에 따라 어떻게 변하는지 보여준다.

Figure 1의 단일 사례는 정량적 일반화 근거가 아니며, Figure 2의 rank 변화도
method illustration이다. Aggregate evidence는 Figure 3과 Table 1이 담당한다.

## 1. 공통 시각·표현 계약

- 배경은 흰색으로 유지한다.
- subject는 orange와 circle/solid box, object는 blue와 square/dashed box를 함께
  사용한다. 색만으로 identity를 구분하지 않는다.
- Source는 dark gray dashed line/circle, RelCompat3D-Linear는 teal solid
  line/square, RelCompat3D-MLP는 purple solid line/triangle로 표시한다.
- 최종 PDF 배치 기준으로 모든 label은 9 pt 이상, stroke는 0.5 pt 이상을 목표로
  한다.
- gradient, shadow, glow, 장식 icon, reviewer-response 문구, protocol chronology는
  넣지 않는다.
- generic metric 표기는 `Recall@K (%)`와 `Violation@K (%)`로 통일한다.
- `predictor score`는 calibrated probability로 표현하지 않는다.
- `compatibility`는 physical-validity probability가 아니라 ranking에 사용하는
  learned score다.
- Figure 안에 모든 수식, loss, estimator architecture를 넣지 않는다. 그림은
  시각적 질문 하나에 답하고, 정확한 정의는 Method가 담당한다.

권장 색상은 다음과 같다.

| 의미 | 색상 | 보조 encoding |
| --- | --- | --- |
| subject | `#D55E00` | circle, solid box |
| object | `#0072B2` | square/diamond, dashed box |
| Source | `#5F6368` | dashed line, circle |
| RelCompat3D-Linear | `#007C76` | solid line, square |
| RelCompat3D-MLP | `#6F42C1` | solid line, triangle |
| unresolved limitation | `#9A6700` | text label과 함께 사용 |

## 2. Figure 1 — High-Scoring Geometric Failure

### Figure의 목적

Figure 1은 다음 한 문장을 시각적으로 보여준다.

> A high predictor rank does not guarantee that the predicate agrees with the
> reconstructed geometry of the corresponding ordered object pair.

이 Figure는 method pipeline이나 aggregate performance를 설명하지 않는다. 독자가
Introduction 첫 페이지에서 failure와 re-ranking outcome을 즉시 이해하게 하는
motivation figure다.

### 보여줄 내용

1. 왼쪽에는 동일한 desk--ceiling ordered pair의 reconstructed point-cloud view를
   둔다.
2. desk가 ceiling 아래에 있는데도 Source가
   `desk higher than ceiling`을 높게 배치했다는 점을 표시한다.
3. 오른쪽 위에는 Source candidate graph와 rank 6을 표시한다.
4. 오른쪽 아래에는 같은 candidate가 RelCompat3D-Linear에서 rank 425로 이동한
   결과를 표시한다.
5. rank 425가 Top-50 밖이라는 결과는 caption에서 설명한다.

오른쪽 graph는 candidate의 rank 변화를 설명하는 schematic이다. Top-50 graph
자체를 재구성한 것으로 오해되지 않도록 `Source rank`와 `RelCompat3D-Linear rank`
label을 명확히 둔다.

### 고정 case

| 항목 | 값 |
| --- | --- |
| predictor | Open3DSG |
| scan/context | `c2d99345-1947-2fbf-818d-90ea82acef29` / suffix `_2` |
| relation | `desk → higher than → ceiling` |
| subject/object | desk instance 16 / ceiling instance 6 |
| predictor score | 0.8709 |
| Source rank | 6 |
| RelCompat3D-Linear rank | 425 |
| measured evidence | subject--object center Δz = −2.00 m |
| transformation-consistent compatibility | \(1.83\times10^{-7}\); Figure에는 생략 가능 |
| primary verifier status | violated |

`rank 6 → 425`는 RelCompat3D-Linear의 결과다. `RelCompat3D`만 쓰면 두 proposed
estimator가 동일 rank를 냈다고 읽힐 수 있으므로 caption에서는 Linear variant를
명시한다.

### Figure 1에서 주장하지 않는 것

- 이 한 사례가 전체 dataset의 평균 효과를 증명한다.
- reconstructed point cloud가 독립적인 physical-validity ground truth다.
- RelCompat3D가 support/contact 또는 모든 relation family를 수정한다.
- rank 425 자체가 calibrated invalidity score다.

### 권장 caption

> **A high-scoring relation contradicted by reconstructed ordered-pair
> geometry.** Open3DSG ranks `desk higher than ceiling` at 6, although the
> reconstructed point-cloud view places the desk below the ceiling.
> RelCompat3D-Linear demotes the same candidate to rank 425, outside the
> Top-50.

## 3. Figure 2 — Compatibility and Re-Ranking Overview

### Figure의 목적

Figure 2는 다음 질문에 답한다.

> RelCompat3D는 predictor score를 compatibility input에서 어떻게 분리하고,
> learned compatibility를 언제 ranking에 다시 결합하는가?

Figure 2는 Figure 1의 failure를 반복하는 것이 아니라 method의 factor separation과
정보 흐름을 설명한다.

### Panel (a): Pair Geometry and Relation

- Open3DSG의 `heater close by trash can` candidate를 사용한다.
- reconstructed ordered pair의 top-down XY projection을 보여준다.
- heater와 trash can의 center를 연결하고 XY center distance 4.33 m를 표시한다.
- 아래에는 relation triplet을 표시한다.
- 이 panel의 역할은 category-level plausibility와 instance-level pair evidence가
  다를 수 있음을 보여주는 것이다.

고정 값은 다음과 같다.

| 항목 | 값 |
| --- | --- |
| scan/subgraph | `4fbad32f-465b-2a5d-8408-146ab1d72808` / suffix `_2` |
| relation | `heater → close by → trash can` |
| subject/object | heater instance 14 / trash can instance 24 |
| predictor score | 0.853 |
| Source rank | 19 |
| XY center distance | 4.33 m |
| RelCompat3D-Linear compatibility | 약 0.003 |
| RelCompat3D-Linear rank | 178 |

### Panel (b): Compatibility and Re-Ranking

정보 흐름은 다음과 같이 단순하게 유지한다.

```text
Predicate semantics T ─┐
                       ├─> Predicate–geometry compatibility
Pair measurements G ───┘

Predictor score Z ───────────────┐
Compatibility ───────────────────┼─> within-family score
                                 └─> family-aware re-ranking
```

핵심 표현 계약:

- compatibility block의 권장 label은 `Predicate–Geometry Compatibility`다.
- \(T\)와 \(G\)만 compatibility block으로 들어간다.
- \(Z\)는 compatibility block을 우회해 within-family score에만 들어간다.
- proximity와 vertical-order는 compatibility를 사용해 family 내부에서
  re-rank한다.
- support/contact는 source order를 유지한다. 공간이 부족하면 이 범위는 Method
  본문에서 설명하고 Figure에 억지로 추가하지 않는다.

Figure 내부나 caption에 \(C^{\rm tr}(T,G)\)를 반드시 반복할 필요는 없다. 수식을
생략하더라도 `transformation-consistent compatibility`라는 의미는 Method에서
정확히 정의한다. Figure에 기호를 쓸 경우에는 최종 score인
`Compatibility C^tr(T,G)`만 사용하고 base compatibility \(C\)와 혼용하지 않는다.

Linear와 MLP의 내부 architecture, BCE, pairwise loss, transformation equation은
Figure 2에 넣지 않는다. 두 estimator가 framework의 instantiation이라는 사실은
caption이 아니라 Method에서 설명한다.

### Figure 2가 전달해야 하는 outcome

- Source rank: 19.
- illustrated re-ranked position: 178.
- 이 rank change는 RelCompat3D-Linear가 만든 결과다.
- aggregate Recall/Violation은 이 Figure에 넣지 않는다.

### 권장 caption

> **RelCompat3D overview.** (a) Open3DSG ranks `heater close by trash can`
> at 19, although the reconstructed ordered pair has an XY center distance of
> 4.33 m. (b) RelCompat3D estimates compatibility from predicate semantics and
> ordered-pair measurements without using the predictor score. The predictor
> score is introduced only during within-family re-ranking. The illustrated
> rank change from 19 to 178 is produced by RelCompat3D-Linear.

## 4. Figure 3 — Recall–Violation Trajectories

### Figure의 목적

Figure 3는 다음 정량적 질문에 답한다.

> Source에서 RelCompat3D-Linear 또는 RelCompat3D-MLP로 바꾸었을 때,
> exact-match Recall과 verifier-derived Violation의 joint operating point가
> \(K\in\{5,10,20,50,100\}\)에서 어떻게 이동하는가?

Table 1이 정확한 수치를 제공한다면, Figure 3는 그 수치를 다시 나열하기보다
각 predictor 안에서 right/down movement와 K에 따른 trajectory를 보여준다.

### Plot 구성

- panel: (a) VL-SAT, (b) Open3DSG, (c) SGFN.
- x-axis: `Recall@K (%)`; 오른쪽이 좋다.
- y-axis: `Violation@K (%)`; 아래쪽이 좋다.
- Source: gray dashed line + circle.
- RelCompat3D-Linear: teal solid line + square.
- RelCompat3D-MLP: purple solid line + triangle.
- 각 line은 \(K=5\rightarrow10\rightarrow20\rightarrow50\rightarrow100\) 순으로
  연결한다.
- K label은 Source trajectory에만 표시한다.
- predictor별 axis range가 다르므로 caption에 이를 명시한다.
- K=50만 star, halo, 별도 색으로 강조하지 않는다.

권장 axis range:

| panel | Recall range (%) | Violation range (%) |
| --- | ---: | ---: |
| VL-SAT | 36--100 | 0--6 |
| Open3DSG | 0--70 | 0--70 |
| SGFN | 20--100 | 0--10 |

### 최신 Figure 3 좌표

아래 값은 active evaluation artifact의 percentage 값이며, 각 point는
`(Recall@K, Violation@K)`다. Figure 3는 총 45 points
\(3\text{ predictors}\times3\text{ rankings}\times5K\)를 포함한다.

#### VL-SAT

| K | Source | RelCompat3D-Linear | RelCompat3D-MLP |
| ---: | ---: | ---: | ---: |
| 5 | (41.94, 0.29) | (42.07, 0.15) | (42.09, 0.15) |
| 10 | (63.22, 0.82) | (63.39, 0.57) | (63.47, 0.51) |
| 20 | (80.74, 1.42) | (80.82, 1.14) | (80.92, 1.09) |
| 50 | (92.72, 2.68) | (92.77, 1.97) | (92.72, 1.89) |
| 100 | (96.35, 4.76) | (96.58, 2.95) | (96.50, 2.96) |

#### Open3DSG

| K | Source | RelCompat3D-Linear | RelCompat3D-MLP |
| ---: | ---: | ---: | ---: |
| 5 | (3.42, 52.05) | (3.73, 0.94) | (3.70, 4.95) |
| 10 | (9.87, 32.89) | (11.38, 2.33) | (11.78, 4.97) |
| 20 | (19.89, 20.99) | (23.62, 3.13) | (24.67, 4.56) |
| 50 | (40.43, 13.87) | (44.18, 3.42) | (46.70, 4.13) |
| 100 | (51.11, 12.42) | (56.85, 3.24) | (59.89, 3.71) |

#### SGFN

| K | Source | RelCompat3D-Linear | RelCompat3D-MLP |
| ---: | ---: | ---: | ---: |
| 5 | (31.17, 2.37) | (31.17, 2.37) | (31.17, 2.37) |
| 10 | (39.75, 3.49) | (39.75, 3.47) | (39.75, 3.47) |
| 20 | (49.12, 3.22) | (49.14, 2.97) | (49.19, 2.96) |
| 50 | (74.02, 3.85) | (74.50, 2.63) | (74.57, 2.58) |
| 100 | (92.35, 6.30) | (93.03, 3.50) | (92.88, 3.50) |

Authoritative numeric source:

- `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/metrics.csv`
- `paper/generated/figures/figure2_data.json`

수동 redraw나 외부 Google Slides asset은 위 좌표와 대조해야 한다. 과거
`paper/Figure3.png` 또는 screenshot의 point가 다르면 screenshot이 아니라 위
artifact를 따른다.

### Figure 3 해석 범위

Figure에서 직접 읽을 수 있는 내용:

- Open3DSG에서 두 variant 모두 큰 right/down shift를 보인다.
- VL-SAT은 Source Recall이 높아 Recall 이동은 작고 Violation 감소가 주로 보인다.
- SGFN은 K=5에서 완전히 tied이고, 이후 K에서 변화가 커진다.
- Linear와 MLP는 서로 다른 operating point를 만들며 어느 하나가 모든 predictor와
  K에서 우월하지 않다.

Figure만으로 주장하면 안 되는 내용:

- 모든 Recall 변화가 statistically significant하다.
- line slope를 predictor 간 성능 크기로 직접 비교할 수 있다.
- 하나의 estimator나 fusion formula가 모든 operating point를 지배한다.
- 세 predictor 결과가 cross-dataset generalization을 증명한다.

### Bar graph 대안

Absolute Recall/Violation bar graph는 Table 1과 중복되고 60개 이상의 bar가 생기므로
main Figure로 권장하지 않는다. Bar 형식이 필요하다면 supplement에서 다음 변화량을
표시한다.

- ΔRecall = RelCompat3D − Source.
- Violation reduction = Source − RelCompat3D.
- predictor별 small multiple, \(K\in\{5,10,20,50,100\}\), Linear/MLP grouped bars.

Main Figure 3는 두 metric의 joint operating point를 보여주는 trajectory가 더
적합하다.

### 권장 caption

> **Recall@K--Violation@K trajectories.** Each line connects
> \(K\in\{5,10,20,50,100\}\) for Source, RelCompat3D-Linear, and
> RelCompat3D-MLP. Rightward and downward movement is preferred. Numbers label
> \(K\) along the Source trajectory; all curves follow the same order. Axis
> ranges differ by predictor.

## 5. Supplementary Qualitative Evidence

Main Figure 1이 vertical demotion을, Figure 2가 proximity demotion과 method
flow를 이미 보여주므로 full three-case grid를 main에 추가하면 중복이 크다.
Supplement에는 다음 세 역할을 분리한 qualitative grid를 유지할 수 있다.

| 역할 | relation | rank change | evidence |
| --- | --- | ---: | --- |
| proximity correction | `heater → close by → trash can` | 19 → 178 | XY distance 4.33 m |
| vertical correction | `floor → higher than → curtain` | 1 → 430 | center Δz = −1.02 m |
| support/contact residual | `door → lying on → floor` | 21 → 21 | contact evidence unresolved |

각 column은 `ordered-pair view → measured evidence → rank/outcome` 순서로 읽혀야
한다. Residual case는 geometry-only로 옳거나 틀렸다고 단정하지 않고, source order로
유지되는 범위를 보여준다.

## 6. Figure source and verification

| Figure | numeric/case source | manuscript asset role |
| --- | --- | --- |
| Figure 1 | `paper/generated/figures/main_case_manifest.json`의 demoted vertical case | motivation/failure |
| Figure 2 | locked `open3dsg_case_001` source row | method overview |
| Figure 3 | active `metrics.csv`와 `figure2_data.json` | aggregate all-K result |
| supplementary qualitative grid | `paper/aaai/supplement_figures/qualitative_geometry_panels.png` | success/failure scope |

최종 검증 체크리스트:

1. Figure 1의 pair, predicate, rank 6→425가 동일 artifact에 연결되는가.
2. Figure 2의 distance 4.33 m와 rank 19→178이 Linear result와 일치하는가.
3. Figure 2 compatibility block에 predictor score \(Z\)가 입력되지 않는가.
4. Figure 3의 45개 point가 위 표와 active CSV에 일치하는가.
5. support/contact를 method가 corrected한 것처럼 표시하지 않는가.
6. 모든 figure text와 stroke가 최종 PDF 배치에서 읽을 수 있는가.
7. caption이 single-case illustration과 aggregate evidence를 구분하는가.
