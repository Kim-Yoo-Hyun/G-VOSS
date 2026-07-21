# RelCompat3D Orthogonal Reviewer Assessment

Last updated: 2026-07-18 KST

이 문서는 세 가지 orthogonal reviewer persona의 현재 평가만 소유한다. Detailed
risk와 mitigation은 `paper/risk.md`, style/figure 제작 규칙은
`paper/figures.md`, experiment 계산법은 `paper/experiment.md`를 따른다.

## Overall Assessment

- Current range: borderline, weak reject to weak accept.
- 가장 강한 점: concrete failure mechanism, source-score separation,
  exact relation-transformation consistency, matched family-aware comparisons,
  joint Recall--Violation reporting.
- 가장 큰 불확실성: verifier construct validity와 single-dataset target.
- 논문이 accept되는 경로는 broad SOTA가 아니라 scoped reliability method와
  falsifiable empirical analysis다.
- 이번 pass에서 GEODE direct boundary, all-K scan-cluster intervals, bounded
  CPU/parameter evidence, grayscale-safe figures가 추가되었다. 이들은 novelty
  설명, statistical reporting, reproducibility, presentation을 보강하지만 두
  핵심 위험인 independent construct validity와 single-dataset scope를 없애지는
  않는다.

## Reviewer A — Method and Novelty

### Summary

The paper studies a specific failure of 3D Scene Graph relation predictors:
high relation confidence can be inconsistent with the reconstructed geometry of
the same object pair. RelCompat3D separates predicate–geometry compatibility
from the source relation score, trains the compatibility score with linked
counterfactuals, enforces proximity/vertical transformation consistency, and
uses the score only in supported relation families.

### Strengths

- Failure cause와 method form이 직접 연결된다. 단순히 “geometry를 추가한다”는
  motivation보다 강하다.
- Compatibility model이 source score와 predictor identity를 입력으로 받지 않는
  구조가 명확하다.
- BCE만 쓰지 않고 linked-pair ordering을 추가해 positive와 counterfactual의
  상대 순서를 직접 학습한다.
- Proximity symmetry와 vertical inverse relation을 inference 계산으로 정확히
  만족시킨다.
- Family-aware re-ranking은 support/contact evidence의 한계를 method 안에서
  처리한다.
- GEODE와의 경계가 generator-internal geometry conditioning 대 fixed-output
  reliability assessment로 명확해져 contemporaneous novelty threat가 줄었다.

### Concerns

- Small linear model과 engineered geometry features 때문에 post-processing
  calibration으로 축소 해석될 수 있다.
- Product 자체는 새로운 fusion equation이 아니며, RelCompat3D-MLP가
  Open3DSG에서 더 높은 Recall을 얻는 operating point가 있다.
- Relation algebra가 proximity/vertical의 작은 transformation set에만 적용되어
  general structured reasoning으로 읽기는 어렵다.

### Required clarification in the paper

- Novelty는 multiplication이 아니라 factor separation, linked
  counterfactual ordering, exact transformation consistency, family-aware
  ranking contract의 결합이라고 써야 한다.
- `best rescorer`, `universal fusion`, `calibrated physical-validity probability`
  표현을 사용하지 않아야 한다.
- 왜 source score를 compatibility에 넣지 않는지와 왜 support/contact를 그대로
  두는지를 Method에서 직관적으로 설명해야 한다.

### Reviewer-style score

- Soundness: 3.5 / 4
- Novelty: 2.5 / 4
- Significance: 2.5 / 4
- Recommendation: 5 / 10, borderline
- Confidence: 4 / 5

### Representative comment

> The method is more principled than a generic rescorer because its factors and
> transformations are explicitly constrained. However, the novelty claim must
> center on this structured reliability contract rather than on the product
> score or classifier capacity.

## Reviewer B — Experimental Validity and Statistics

### Summary

The evaluation compares Source and RelCompat3D across three predictors on the
same 3DSSG target, reports all K values, and pairs exact-label Recall with
verifier-derived Violation. Matched family-aware fusion baselines and targeted
falsification controls are included.

### Strengths

- Recall과 Violation을 같은 table에서 보고해 filtering-only explanation을
  직접 차단한다.
- K={5,10,20,50,100} 전체를 공개해 특정 K만 선택했다는 우려를 줄인다.
- RelCompat3D-MLP, RankAvg, RRF가 같은 family sequence와 support/contact order를
  사용하므로 primary comparison이 공정하다.
- Wrong predicate, wrong pair, shuffled geometry, endpoint transformation,
  distance-only, no-source-score가 중요한 alternative explanation을 검사한다.
- Scan-cluster resampling은 같은 scan 안의 context dependence를 반영한다.
- 모든 K의 scan-cluster interval을 공개하므로 broad point trend와 budget별
  statistical support를 구분할 수 있다.
- Exact verifier scalar 제거와 threshold sensitivity는 literal rule copying
  우려를 완화한다.
- Point/mesh surface audit는 OBB input과 primary verifier label을 읽지 않고도
  세 predictor의 Violation 변화 방향을 재현하며, synthetic interventions도
  expected monotonic response를 검사한다.

### Concerns

- Compatibility target과 primary Violation verifier가 일부 OBB
  distance/overlap/vertical primitive를 공유한다. Surface audit는 exact-rule
  overlap을 줄이지만 같은 reconstructed surface와 ontology를 공유하므로 독립
  physical-validity ground truth는 아니다.
- 세 predictor가 같은 dataset/ontology/geometry target을 사용한다.
- Support/contact는 primary ranking에서 unchanged이므로 전체 relation
  reliability improvement가 아니다.
- Open3DSG의 public pipeline에서 candidate가 없는 context가 있으며, full-target
  처리를 독자가 재현할 수 있어야 한다.

### Required clarification in the paper

- Violation은 항상 verifier-derived라고 부른다.
- 3,972 Recall denominator와 actual selected-row V denominator를 명시한다.
- VL-SAT K=50 Recall interval이 0을 포함하므로 significant Recall gain이라고
  쓰지 않는다.
- Cross-predictor evidence와 cross-dataset generalization을 구분한다.
- Hard filter의 V=0은 construction이고 K보다 적은 행을 반환할 수 있음을
  supplement에서 설명한다.

### Reviewer-style score

- Soundness: 3 / 4
- Experimental rigor: 3.5 / 4
- Construct validity: 2.5 / 4
- Recommendation: 5 / 10, borderline
- Confidence: 5 / 5

### Representative comment

> The comparisons are unusually careful for a re-ranking paper, especially the
> matched ranking procedure and scan-level intervals. My main hesitation is that the
> training target and evaluation verifier are not fully independent, and the
> three predictors do not constitute three dataset tests.

## Reviewer C — Writing, Presentation, and Reproducibility

### Summary

The manuscript uses a conventional six-section structure. The main table
reports all K values in percentage points; the method and qualitative figures
connect an observed failure to the proposed compatibility layer and its
remaining family boundary.

### Strengths

- Introduction의 failure → cause → design 흐름이 명확하다.
- Problem Setup을 Method에, setup/results를 Experiments에 넣은 구조가 자연스럽다.
- Abstract는 dense 숫자나 limitation list 없이 문제, 방법, 결과 방향을
  전달한다.
- Table 1과 Table 2가 result prose 전에 나타나며, percentage scale과 짧은
  condition 이름을 사용한다.
- Figure 1은 실제 pair geometry, factor flow, rank outcome을 한 장에 담는다.
- Figure 2는 all-K trajectory를 보여주고 K=50을 시각적으로 선택하지 않는다.
- Figure 3은 success 두 개와 residual failure 하나를 대칭적으로 보여준다.
- Figure 3의 point shape와 box line style, Figure 2의 marker/line encoding을
  실제 PDF grayscale에서 확인했다.
- Supplement의 runtime 표는 측정 경계를 명시하고 source pipeline latency로
  과장하지 않는다.
- Docker source, checklist, checksums, extracted-source rebuild가 준비되어 있다.

### Concerns

- Method 용어가 압축되면 algebra projection과 family sorting이 처음 읽는
  reviewer에게 어려울 수 있다.
- Figure 글씨가 최종 two-column width에서 작아질 위험이 있다.
- Limitation을 지나치게 반복하면 논문이 contribution보다 방어에 집중한 것처럼
  보일 수 있다.
- Open3DSG preprocessing 세부가 main narrative를 방해하지 않으면서도 supplement에서
  재현 가능해야 한다.

### Required revision check

- 새 figure는 `paper/figures.md`의 font, case, data-coordinate specification을
  따라야 한다.
- Method는 `paper/method.md`처럼 BCE, pair ordering, transformation averaging,
  family sorting을 단계별로 설명해야 한다.
- Results prose는 dense table 값을 반복하지 않고 비교 pattern과 interval
  interpretation에 집중해야 한다.
- Discussion에서 shared target, construct overlap, support/contact, formula
  non-dominance를 한 번씩만 다룬다.

### Reviewer-style score

- Clarity: 3.5 / 4
- Reproducibility: 4 / 4
- Presentation: 3 / 4
- Recommendation: 6 / 10, weak accept
- Confidence: 4 / 5

### Representative comment

> The paper is well organized and unusually transparent. Acceptance will depend
> less on adding more tables and more on ensuring that the method figure and
> explanation make the structural contribution immediately understandable.

## Consensus Decision

세 reviewer가 공통으로 인정하는 contribution:

1. same-pair geometric inconsistency라는 구체적 failure.
2. source relation score와 compatibility의 분리.
3. linked counterfactual ordering과 exact relation transformation.
4. family-aware re-ranking과 matched comparisons.
5. joint Recall--Violation evaluation.

공통 blocking concern:

1. independent physical-validity ground truth 부재; surface audit가 exact-rule
   overlap은 완화함.
2. single shared dataset target.

Acceptance 가능성을 가장 크게 낮추는 실수:

- product formula를 핵심 novelty로 과장.
- 세 predictor를 dataset generalization으로 표현.
- support/contact를 해결했다고 표현.
- Figure 1을 dense engineering pipeline으로 다시 그림.
- Table 수치를 본문에서 반복해 contribution 흐름을 약화.

현재 권장 decision:

> Submit as a scoped reliability-method paper after final figure redraw and
> author-metadata completion. Do not broaden the scientific claim without new
> independent evidence.

## Final Transcript Pass

### Abstract

- 정확한 benchmark 수치를 나열하지 않고 problem, factor separation,
  transformation consistency, evaluation scope, result direction만 전달한다.
- `lower or tied Violation point estimates`와 `preserving or improving Recall
  point estimates`는 모든 공개 K의 표와 일치한다.
- `physical validity`, `generalization`, `best`처럼 현재 evidence보다 강한 단어는
  없다.

### Introduction and Contributions

- Failure → structural cause → factor separation → ranking rule → evaluation
  순서가 유지된다.
- Contribution 1은 problem/evaluation, 2는 method, 3은 evidence와 failure scope를
  담당해 중복이 적다.
- 세 predictor를 shared-target behavior로 한정하며 dataset transfer로 확대하지
  않는다.

### Related Work

- GEODE, RelGraphOV, TAD는 generator 내부의 geometry/transformation 처리와,
  Neau et al.은 fixed-output constraint refinement와 비교된다.
- RelCompat3D의 차이는 continuous same-pair 3D compatibility, source-score
  exclusion, endpoint/predicate transformation, joint Recall--Violation
  evaluation으로 한정된다. 선행연구가 하지 않은 것을 과도하게 주장하지 않는다.

### Method

- 실제 입력이 OBB-derived distance/height/overlap/gap임을 정확히 쓰며 point-level
  contact evidence를 model input으로 오인시키지 않는다.
- BCE, linked-pair ordering loss, transformation averaging, family-aware sorting
  순서가 원리적으로 연결된다.
- Transformation consistency만 compact proposition으로 유지한다. 이는 finite
  group averaging의 표준 불변성을 실제 proximity/vertical transformation에
  연결한다. Family-sequence와 support/contact prefix preservation은 ordered-list
  construction의 직접적인 성질로 평문 처리해 자명한 sorting을 이론 novelty처럼
  보이게 하지 않는다.
- Product는 parameter-free ranking rule로만 설명하며 probability posterior나
  formula superiority로 해석하지 않는다.

### Experiments and Results

- Split, denominator, candidate inclusion, baselines, uncertainty, scan-cluster
  unit이 재현 가능하게 정의된다.
- K=10--50 문장은 Recall과 Violation의 **point estimates**에 한정되고, K=50의
  interval 해석은 predictor별로 정확하다. Supplement는 K=5--100의 interval을
  전부 공개한다.
- Runtime은 preloaded rows/precomputed geometry 이후만 측정했다고 쓰므로
  end-to-end latency로 오인될 여지를 제한한다.
- Table 수치를 본문에서 반복하기보다 comparator trade-off, control failure,
  family boundary를 설명한다.

### Discussion and Conclusion

- Construct overlap, shared target, support/contact residual을 각각 한 번만
  설명해 방어 문구 반복이 과하지 않다.
- Conclusion은 observed shared-target behavior만 요약하며 외부 dataset이나
  physical validity로 claim을 넓히지 않는다.

### Transcript verdict

문법, 용어 통일, claim--evidence 대응, compact proposition 표기, section 순서에서 제출을
막는 오류는 발견되지 않았다. 현재 남은 acceptance ceiling은 transcript 문제가
아니라 independent human reference와 broader dataset evidence다. 사용자가 정한
다음 순서대로 human alignment를 먼저 수행하고, 그 뒤 external-dataset test를
별도 protocol로 여는 것이 맞다.
