# RelCompat3D Figure Redraw Specification

Last updated: 2026-07-17 KST

이 문서는 Figure 1--3을 Illustrator, Figma, Inkscape, PowerPoint 또는 다른
vector 도구로 다시 그릴 때 따라야 할 완전한 제작 명세다. 논문의 claim과
수치가 바뀌지 않는 한 아래 정보와 case identity를 그대로 유지한다.

## 1. 공통 제작 원칙

### 전달해야 하는 하나의 이야기

세 그림은 다음 순서로 읽혀야 한다.

1. Figure 1: 높은 source relation score가 실제 pair geometry와 어긋날 수 있고,
   RelCompat3D가 이를 어떻게 평가하고 re-ranking하는지 설명한다.
2. Figure 2: 이 re-ranking이 세 predictor와 여러 K에서 Recall--Violation
   trade-off를 어떻게 바꾸는지 정량적으로 보여준다.
3. Figure 3: 실제 object pair에서 어떤 evidence 때문에 rank가 바뀌는지와,
   현재 적용하지 않는 support/contact failure를 함께 보여준다.

### 시각 규칙

- 배경: 흰색.
- 출력: SVG와 vector PDF를 기본으로 하고 PNG는 preview로만 사용한다.
- 전체 폭 figure의 권장 원본 크기: 1,500 px. LaTeX에서는 약
  `0.98\linewidth`로 삽입한다.
- 최종 PDF에서 가장 작은 본문 글씨가 7.5 pt보다 작아지지 않도록 한다.
  1,500 px 원본 기준 권장 최소 font는 22 px이다.
- panel title: 26--30 px, bold.
- 주요 block title 및 핵심 수치: 22--25 px, bold.
- 보조 설명: 22 px 이상.
- 한 figure 안에서 font family와 weight 체계를 통일한다. Helvetica, Arial,
  Source Sans, 또는 Inter 계열처럼 인쇄 가독성이 높은 sans-serif를 권장한다.
- 색상만으로 의미를 구분하지 않는다. 색과 함께 marker shape, line style,
  label을 사용한다.
- 권장 색:
  - subject: vermillion/red `#D62728`, circular points, solid box
  - object: blue `#2563EB`, square points, dashed box
  - Source ranking: dark gray `#4B5563`
  - RelCompat3D: teal/green `#059669`
  - successful correction: blue `#0369A1`
  - residual limitation: amber `#B45309`
  - neutral border/grid: `#CBD5E1` / `#E5E7EB`
- main figure에 reviewer response, audit status, protocol chronology, artifact
  key 같은 연구 과정 및 관리 문구를 넣지 않는다.
- metric은 `Recall@K (%)`와 `Violation@K (%)`로 쓴다. Recall은 오른쪽,
  Violation은 아래쪽이 좋은 방향이다.
- Figure 2에서 K=50을 outline, halo, star 또는 별도 색으로 강조하지 않는다.
  K=`{5,10,20,50,100}`을 모두 보여준다.

### Figure label 용어 고정

| 의미 | Figure에서 사용할 label |
| --- | --- |
| predictor가 제공한 원래 점수 | `Source score Z` |
| predicate 입력 | `Predicate T` |
| 동일 ordered pair의 geometry | `Pair geometry G` |
| T와 G로 계산한 점수 | `Compatibility C(T,G)` |
| 의미가 같은 변환의 score 결합 | `transformation averaging` |
| 최종 family별 순위 변경 | `Family-aware re-ranking` |
| proximity/vertical 처리 | `re-ranked` |
| support/contact 처리 | `source order` 또는 `kept in source order` |
| 평가 지표 | `Exact-label Recall@K`, `Verifier-derived Violation@K` |

Figure의 짧은 label에서는 `Source score Z`를 사용하되, 본문과 caption에서는
이 값이 predictor의 `source relation score`이며 calibrated probability가 아님을
명확히 한다.

## 2. Figure 1 — Failure Mechanism and Method Overview

### 그림이 답해야 하는 질문

> 왜 높은 relation score만으로는 실제 3D pair의 geometric consistency를
> 보장할 수 없으며, RelCompat3D는 무엇을 분리하고 어떻게 다시 결합하는가?

### 전체 구성

- 권장 canvas: 1,500 × 430 px.
- 왼쪽에서 오른쪽으로 3개 panel을 배치한다.
  - Panel (a), 약 0--445 px: observed failure.
  - Panel (b), 약 445--1,080 px: compatibility estimation and score fusion.
  - Panel (c), 약 1,080--1,500 px: re-ranking and evaluation.
- Panel 사이에는 옅은 vertical separator를 둔다.
- 흐름은 반드시 `(a) observed pair → (b) compatibility → (c) ranking`이어야
  한다. 역방향 arrow나 여러 갈래 feedback arrow는 사용하지 않는다.

### Panel (a): High-scoring relation contradicted by geometry

표시할 실제 case:

| 항목 | 값 |
| --- | --- |
| source | Open3DSG |
| relation | `heater → close by → trash can` |
| subject | heater, instance 14 |
| object | trash can, instance 24 |
| source relation score | `Z = 0.853` |
| source rank | `19` |
| measured XY center distance | `4.33 m` |
| compatibility | `C = 0.0027`, figure에서는 `0.003`으로 표시 가능 |
| RelCompat3D rank | `178` |
| Product (all families) rank | `304`; Figure 1에는 생략하고 Figure 3/source record에 유지 |

그릴 요소:

1. 실제 ordered-pair point cloud의 top-down XY projection.
2. heater는 red circle/solid box, trash can은 blue square/dashed box로 표시한다.
3. 두 instance center를 점으로 표시하고 dashed line으로 연결한다.
4. 축의 오른쪽 아래에 `x`, 왼쪽 위에 `y`를 표시한다.
5. object category만으로 관계가 성립하는 것처럼 보이지 않도록 실제 두
   instance의 거리와 위치를 크게 보여준다.
6. plot 아래에 다음 세 줄을 둔다.
   - `heater → close by → trash can`
   - `Open3DSG: Z = 0.853; rank 19`
   - `XY center distance = 4.33 m`
7. 마지막 줄은 evidence 강조색을 사용할 수 있지만, 경고 icon이나
   `invalid` stamp처럼 verifier가 정답이라고 단정하는 표현은 사용하지 않는다.

Plot source:

- scan: `4fbad32f-465b-2a5d-8408-146ab1d72808`
- subgraph: `4fbad32f-465b-2a5d-8408-146ab1d72808_2`
- source file:
  `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/datasets/OpenSG_3RScan/preprocessed/4fbad32f-465b-2a5d-8408-146ab1d72808/data_dict_2.pkl`
- recommended plot bounds:
  - x: `[-0.494, 4.289]`
  - y: `[-3.620, 1.950]`

### Panel (b): What is separated and what is combined

이 panel의 핵심은 `compatibility model이 source score를 복사하지 않는다`는
사실을 복잡한 방어 문구 없이 구조로 보여주는 것이다.

왼쪽 입력 block 3개:

1. `Predicate T`
   - 내용: `close by / proximity`
   - 의미: 어떤 predicate를 검사하는지 알려준다.
2. `Pair geometry G`
   - 내용: `distance, height, overlap`
   - 의미: 동일 subject/object instance의 reconstructed geometry다.
3. `Source score Z`
   - 내용: `used only in re-ranking`
   - 의미: 원래 predictor의 relation score이며 calibrated probability로 가정하지
     않는다.

중앙 compatibility block:

- 제목: `Compatibility C(T,G)`
- 입력 arrow는 T와 G에서만 들어온다.
- block 내부의 짧은 설명:
  - `linked counterfactual ordering`
  - `transformation averaging`
- case 출력: `C = 0.003`
- block 아래 또는 내부에 `Compatibility inputs: T and G`라고 쓴다.
- `Z is forbidden`, `leakage boundary` 같은 방어형 문구는 쓰지 않는다.

Score fusion block:

- Source score Z는 compatibility block을 거치지 않고 fusion block으로
  바로 연결한다.
- compatibility output도 fusion block으로 연결한다.
- 식: `S = Z × C(T,G)`.
- 보조 label: `within applicable family`.
- 독자가 multiplication이 posterior probability라고 오해하지 않도록
  `probability` 또는 `Product of Experts`라는 표현은 사용하지 않는다.

Endpoint/predicate transformation을 시각화하는 최소 요소:

- proximity 옆에 작은 double arrow 또는 swap icon:
  `close by(s,o) = close by(o,s)`.
- vertical 옆에 작은 inverse pair:
  `higher(s,o) = lower(o,s)`.
- 긴 group-theory notation은 Figure 1에 넣지 않고 Method와 caption에서
  설명한다.

### Panel (c): Re-ranking and outputs

상단 rank movement:

- 왼쪽 큰 숫자 `19`, 아래 `source rank`.
- 오른쪽 큰 숫자 `178`, 아래 `re-ranked`.
- 두 숫자 사이에 오른쪽 arrow.
- 오른쪽 숫자는 method color로 표시한다.

Family-aware re-ranking block:

- 제목: `Family-aware re-ranking`.
- 두 줄:
  - `proximity / vertical: re-ranked`
  - `support/contact: source order`
- 구현 내부 이름이나 reviewer-response 문구를 추가하지 않는다.
- family composition이 보존됨을 보여주고 싶으면
  `P–S–V–P → P–S–V–P`처럼 relation-family sequence가 유지되는 작은 예시를
  추가할 수 있다.

Evaluation block:

- 제목: `Joint evaluation`.
- `Exact-label Recall@K ↑`.
- `Verifier-derived Violation@K ↓`.
- uncertainty/CI/Docker/provenance는 Figure 1에 넣지 않는다.

### Figure 1 arrow 목록

다음 arrow만 필요하다.

1. T → compatibility.
2. G → compatibility.
3. compatibility → product score.
4. Z → product score.
5. product score → family-aware re-ranking.
6. re-ranking → rank change / joint evaluation.

Arrow가 box나 text를 가로지르지 않게 한다. 모든 arrow 방향은
left-to-right 또는 top-to-bottom이어야 한다.

### Figure 1에 넣지 않을 요소

- learned point-cloud encoder, energy head, observability head, abstention.
- relative size, horizontal relation, attachment extension.
- Rank-average, RRF, MLP baseline 목록.
- training row count, optimizer steps, Docker command.
- proposition 번호, bootstrap, human/LLM audit.
- `predictor-agnostic`이라는 넓은 label. 필요한 경우 caption에서
  `the compatibility inputs exclude predictor identity and source score`라고
  정확히 쓴다.

### 권장 caption

> **Failure mechanism and RelCompat3D overview.** A high-scoring Open3DSG
> relation is contradicted by the actual ordered-pair geometry. RelCompat3D
> preserves relation-candidate identity, isolates predicate semantics T,
> predicate-independent pair-geometry measurements G, and source relation score Z,
> and estimates transformation-averaged
> compatibility without Z.
> Family-aware re-ranking moves the shown proximity relation from rank 19 to
> 178 while leaving support/contact selections unchanged. Linked-counterfactual
> and transformation controls test the separation; evaluation jointly reports
> exact-label recall and verifier-derived violation.

## 3. Figure 2 — Recall–Violation Trajectories

### 그림이 답해야 하는 질문

> Source ranking에서 RelCompat3D ranking으로 바꾸었을 때, K가 증가하는
> 동안 Recall과 Violation의 operating point가 어디로 움직이는가?

### 전체 구성

- 권장 canvas: 1,500 × 430 px.
- 세 panel을 가로로 배치한다.
  - (a) VL-SAT
  - (b) Open3DSG
  - (c) SGFN
- 권장 plot rectangle:
  - VL-SAT: `(x=70, y=70, width=380, height=280)`
  - Open3DSG: `(x=560, y=70, width=380, height=280)`
  - SGFN: `(x=1050, y=70, width=380, height=280)`
- x-axis: `Recall@K (%)`.
- y-axis: `Violation@K (%) ↓`.
- 모든 수치는 0--1 fraction이 아니라 0--100 percentage point로 표시한다.
- Source: gray dashed line + circle marker.
- RelCompat3D: teal solid line + square marker.
- 선은 각 condition 안에서 K=5 → 10 → 20 → 50 → 100 순으로 연결한다.
- K label은 RelCompat3D square 근처에 `5`, `10`, `20`, `50`, `100`으로
  표시한다. Source point는 같은 K 순서를 따르므로 label을 중복하지 않는다.
- K=50에 별도 outline을 사용하지 않는다.
- panel별 axis range가 다르므로 caption에 이를 밝힌다.

### 권장 axis range

| panel | Recall x-range (%) | Violation y-range (%) | 이유 |
| --- | ---: | ---: | --- |
| VL-SAT | 36.48--100.00 | 0.00--5.32 | near-ceiling Recall과 작은 V 변화를 읽기 위함 |
| Open3DSG | 0.00--62.28 | 0.00--58.18 | low-K source violation과 method shift를 모두 포함 |
| SGFN | 24.98--99.22 | 1.90--6.77 | 작은 V 차이를 읽으면서 전체 K curve 유지 |

축 범위는 panel 간 직접적인 절대 기울기 비교를 위한 것이 아니다. source 간
비교는 Table 1의 실제 수치로 수행하고, plot은 각 source 내부 trajectory를
읽기 위한 것이다.

### 점의 정확한 데이터 좌표

각 점은 `(Recall@K %, Violation@K %)`이다.

#### VL-SAT

| K | Source circle | RelCompat3D square |
| ---: | ---: | ---: |
| 5 | (41.94, 0.29) | (42.07, 0.15) |
| 10 | (63.22, 0.82) | (63.39, 0.57) |
| 20 | (80.74, 1.42) | (80.82, 1.14) |
| 50 | (92.72, 2.68) | (92.77, 1.97) |
| 100 | (96.35, 4.76) | (96.58, 2.95) |

#### Open3DSG

| K | Source circle | RelCompat3D square |
| ---: | ---: | ---: |
| 5 | (3.42, 52.05) | (3.73, 0.94) |
| 10 | (9.87, 32.89) | (11.35, 2.33) |
| 20 | (19.89, 20.99) | (23.62, 3.13) |
| 50 | (40.43, 13.87) | (44.18, 3.42) |
| 100 | (51.11, 12.42) | (56.92, 3.24) |

#### SGFN

| K | Source circle | RelCompat3D square |
| ---: | ---: | ---: |
| 5 | (31.17, 2.37) | (31.17, 2.37) |
| 10 | (39.75, 3.49) | (39.75, 3.47) |
| 20 | (49.12, 3.22) | (49.14, 2.97) |
| 50 | (74.02, 3.85) | (74.50, 2.63) |
| 100 | (92.35, 6.30) | (93.03, 3.50) |

### 권장 canvas에서의 approximate pixel 위치

아래 좌표는 위 plot rectangle과 axis range를 사용한 `(x,y)` 위치다. 최종
정렬은 label collision을 피하도록 1--3 px 조정할 수 있지만 데이터 좌표는
바꾸지 않는다.

| panel | condition | K5 | K10 | K20 | K50 | K100 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| VL-SAT | Source | (103,335) | (230,307) | (335,275) | (407,209) | (428,99) |
| VL-SAT | RelCompat3D | (104,342) | (231,320) | (335,290) | (407,246) | (430,195) |
| Open3DSG | Source | (581,100) | (620,192) | (681,249) | (807,283) | (872,290) |
| Open3DSG | RelCompat3D | (583,346) | (629,339) | (704,335) | (830,334) | (907,334) |
| SGFN | Source | (1082,323) | (1126,259) | (1174,274) | (1301,238) | (1395,97) |
| SGFN | RelCompat3D | (1082,323) | (1126,260) | (1174,288) | (1304,308) | (1398,258) |

다른 canvas를 사용할 때의 변환식:

```text
x_pixel = plot_left + (Recall - x_min) / (x_max - x_min) * plot_width
y_pixel = plot_top + plot_height
          - (Violation - y_min) / (y_max - y_min) * plot_height
```

### Label 배치

- K label은 method square에서 기본적으로 10--14 px 위에 둔다.
- VL-SAT K=100 label은 오른쪽 경계를 넘지 않도록 약간 왼쪽으로 이동한다.
- SGFN K=10과 K=20 label이 겹치면 K=10은 왼쪽, K=20은 오른쪽으로
  12--16 px 이동한다.
- Open3DSG method points는 y값이 가까우므로 label을 위쪽에 두고 x축과
  겹치지 않게 한다.
- legend는 Figure 상단 오른쪽에 두되 panel (c) title과 겹치지 않는다.

### Figure 2에서 주장할 수 있는 것과 없는 것

표현 가능:

- Open3DSG에서 큰 down/right shift가 보인다.
- VL-SAT과 SGFN에서는 Recall 변화가 작지만 V가 낮아지는 구간이 있다.
- behavior는 source와 K에 따라 다르다.

표현 금지:

- 모든 K에서 모든 source의 Recall이 통계적으로 유의하게 개선된다.
- 한 fusion formula가 모든 operating point에서 우월하다.
- panel별 축 범위가 다른데 line slope를 source 간 성능 크기로 비교한다.

### 권장 caption

> **Recall–Violation trajectories.** Each line connects
> K∈{5,10,20,50,100} for one predictor and ranking rule. Rightward and downward
> movement is preferred. Labels mark K on the RelCompat3D curve; Source points
> follow the same sequence. Axis ranges differ by predictor.

## 4. Figure 3 — Pair–Evidence–Outcome Analysis

### 그림이 답해야 하는 질문

> 어떤 실제 geometric evidence가 proximity/vertical prediction을
> demote하며, 왜 support/contact는 현재 그대로 남겨 두는가?

### 전체 구성

- 권장 canvas: 1,500 × 580 px.
- 3개 column:
  - (a) Proximity correction.
  - (b) Vertical-order correction.
  - (c) Support/contact residual.
- 각 column은 위에서 아래로 같은 세 row를 가진다.
  1. `Ordered pair`
  2. `Geometry evidence`
  3. `Ranking outcome`
- 세 column의 card 높이와 baseline을 정확히 맞춘다.
- correction은 blue, residual은 amber로 표시한다. red/green만으로
  success/failure를 구분하지 않는다.

### Column (a): Proximity correction

Header:

- `(a) Proximity correction`
- `heater → close by → trash can`

Ordered-pair card:

- top-down XY projection.
- subject heater는 red circle/solid box, object trash can은 blue square/dashed box.
- centers를 dashed line으로 연결.
- plot bounds x `[-0.494, 4.289]`, y `[-3.620, 1.950]`.

Evidence card:

- title: `Geometry evidence`.
- primary value: `XY center distance = 4.33 m`.
- explanation: `large separation for close by`.

Outcome card:

- `source rank 19 → RelCompat3D rank 178`.
- `Z = 0.853, C = 0.003`.
- `Demoted: inconsistent proximity`.
- Product (all families) rank 304는 main card에는 넣지 않아도 된다.

Source identity:

- `open3dsg_case_001`
- scan/subgraph와 pickle path는 Figure 1 specification과 동일하다.
- verifier status: violated.
- pair의 GT predicate는 `right`; `close by` exact-label GT는 아니다.

### Column (b): Vertical-order correction

Header:

- `(b) Vertical-order correction`
- `floor → higher than → curtain`

Ordered-pair card:

- elevation x--Z projection.
- subject floor는 red circle/solid box, object curtain은 blue square/dashed box.
- centers를 dashed line으로 연결.
- plot bounds x `[-0.793, 3.088]`, z `[-1.992, 0.912]`.

Evidence card:

- primary value: `subject–object center Δz = −1.02 m`.
- explanation: `subject lies below the object`.
- minus sign은 hyphen이 아니라 typographic minus를 사용한다.

Outcome card:

- `source rank 1 → RelCompat3D rank 430`.
- `Z = 0.871, C < 0.001`.
- 실제 C: `0.00000297`.
- `Demoted: inverted vertical order`.

Source identity:

- `open3dsg_case_019`
- scan: `c2d99343-1947-2fbf-808f-92dbb7d47aa5`
- subgraph: `c2d99343-1947-2fbf-808f-92dbb7d47aa5_1`
- subject floor instance 1, object curtain instance 10.
- source file:
  `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/datasets/OpenSG_3RScan/preprocessed/c2d99343-1947-2fbf-808f-92dbb7d47aa5/data_dict_1.pkl`
- Product (all families) rank: 431.
- verifier status: violated.

### Column (c): Support/contact residual

Header:

- `(c) Support/contact residual`
- `door → lying on → floor`

Ordered-pair card:

- elevation x--Z projection.
- subject door는 red circle/solid box, object floor는 blue square/dashed box.
- centers를 dashed line으로 연결.
- plot bounds x `[-5.442, 4.539]`, z `[-2.036, 0.676]`.

Evidence card:

- primary value: `bottom-to-top gap = −0.06 m`.
- explanation: `contact evidence remains unresolved`.
- 이 case를 geometry-only로 명확히 맞거나 틀렸다고 단정하지 않는다.

Outcome card:

- `source rank 21 → RelCompat3D rank 21`.
- `Z = 0.843, C = 0.998`.
- `Unchanged: kept in source order`.
- Product (all families)라면 rank 10이 되지만, 논문의 family-aware ranking은
  support/contact에 이 product를 사용하지 않는다는 사실을 caption 또는 본문에서
  설명할 수 있다.

Source identity:

- `open3dsg_case_026`
- scan: `e61b0e02-bada-2f31-82d0-80fc5c70bd6f`
- subgraph: `e61b0e02-bada-2f31-82d0-80fc5c70bd6f_1`
- subject door instance 30, object floor instance 1.
- source file:
  `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/datasets/OpenSG_3RScan/preprocessed/e61b0e02-bada-2f31-82d0-80fc5c70bd6f/data_dict_1.pkl`
- verifier status: violated.

### Figure 3에 scene image를 추가하고 싶을 때

- RGB screenshot 또는 전체 scene rendering은 위와 동일한 scan/subgraph와
  instance ID를 사용해 deterministic하게 재생성할 수 있을 때만 넣는다.
- scene crop을 추가한다면 각 column의 첫 card를 `Scene / ordered pair`로
  나누고, scene에서 subject/object를 같은 red/blue로 표시한다.
- 다른 scan의 prettier image로 교체하거나 object category만 같은 pair를
  사용하면 안 된다. rank, C, evidence가 모두 현재 case identity에 묶여 있기
  때문이다.
- deterministic scene rendering이 없으면 현재 ordered-pair point-cloud
  view가 더 정확하다. 이를 `RGB scene`이라고 부르지 않는다.

### 권장 caption

> **Pair–evidence–outcome analysis.** Each column links an ordered-pair
> point-cloud view to its measured geometric evidence and ranking outcome. The
> first two violations are demoted; the contact-heavy residual is kept in
> source order. Subjects use circular points and solid boxes; objects use
> square points and dashed boxes, in addition to red/blue color.

## 5. Figure source and verification map

| figure | numeric/case source | generation reference |
| --- | --- | --- |
| Figure 1 | `paper/generated/figures/figure3_geometry_cases.json` | `paper/scripts/render_figure3_geometry_panels.py` |
| Figure 2 | `paper/generated/figures/figure2_data.json` | `paper/scripts/generate_draft_figures.py` |
| Figure 3 | `paper/generated/figures/figure3_geometry_cases.json` | `paper/scripts/render_figure3_geometry_panels.py` |

현재 generated assets는 redraw의 visual reference일 뿐이다. 새 그림이 완성되면
다음 검증을 수행한다.

1. Figure 2의 30개 점이 위 좌표와 일치하는지 확인한다.
2. Figure 1/3의 case ID, rank, Z, C, distance/Δz/gap을 확인한다.
3. subject/object 색·marker·box pattern과 ordered direction이 뒤바뀌지 않았는지 확인한다.
4. Figure 1의 compatibility block에 source relation score Z의 arrow가
   들어가지 않았는지 확인한다.
5. support/contact가 method에 의해 corrected된 것처럼 표현되지 않았는지
   확인한다.
6. PDF 전체 폭에서 가장 작은 글씨가 읽히는지 확인한다.
7. SVG XML parse, vector PDF conversion, Type 3 font 부재를 확인한다.
