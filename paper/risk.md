# RelCompat3D Reviewer-Risk Register

Last updated: 2026-07-18 KST

이 문서는 현재 submission claim에 영향을 주는 scientific/reviewer risk와
필수 방어만 소유한다. Historical mitigation log와 실행 산출물은 experiment
reports에 둔다.

## Risk Summary

| ID | risk | severity | current status |
| --- | --- | --- | --- |
| R1 | training target와 Violation verifier의 geometry overlap | critical | substantially mitigated, residual |
| R2 | 하나의 shared dataset target | high | disclosed, unresolved |
| R3 | support/contact evidence와 re-ranking scope | high | operationally contained |
| R4 | engineered-feature rescorer로 축소되는 novelty | high | partially mitigated |
| R5 | strong nonlinear/rank baselines | medium | matched comparison complete |
| R6 | Open3DSG candidate coverage/reproduction | medium | full official target + coverage sensitivity |

## R1. Construct Overlap

### Reviewer attack

> Compatibility를 학습할 때 사용한 distance/overlap/height primitive와
> Violation을 계산하는 verifier가 비슷하므로, method가 evaluation rule을 다시
> 학습한 것 아닌가?

### Facts

- 일부 geometry primitive와 threshold family가 target construction과 verifier에
  공통으로 사용된다.
- Wrong predicate/pair/shuffle와 transformation controls는 trivial copying을
  배제하지만 독립 ground truth를 만들지는 않는다.

### Current defense

- C를 constructed-target compatibility score라고 정의하고 physical-validity
  probability라고 부르지 않는다.
- Violation을 verifier-derived라고 부른다.
- verifier의 exact scalar를 제거한 train-only refit에서도 main behavior가
  대부분 유지된다.
- 관련 measurement family 전체를 제거하면 effect가 약해짐을 숨기지 않는다.
- counterfactual threshold와 negative cap sensitivity를 보고한다.
- Frozen `orthogonal_geometry_audit_v1` assigns point, mesh, and strict
  consensus statuses from raw instance vertices and area-weighted triangle
  surfaces without reading OBB inputs or existing verifier labels. At K=50 and
  K=100, every predictor has a negative paired scan-cluster consensus dV with
  95--98% supported-status coverage; strict binary-decision coverage is lower
  (71--84% at K=50) because disagreements remain uncertain. Separate point and
  mesh results agree in direction.
- Synthetic distance/elevation interventions produce 100% monotone frozen
  compatibility responses; raw point/mesh responses are 94.7--100% monotone.

### Still missing

- Point와 mesh가 동일한 reconstructed PLY surface와 dataset ontology를 공유하므로,
  independently sensed geometry 또는 human physical-validity reference는 아직 없다.

### Blocked wording

- human-validated physical correctness.
- independent physical ground-truth metric.
- calibrated probability of validity.

## R2. Shared Dataset Target

### Reviewer attack

> VL-SAT, Open3DSG, SGFN은 predictor만 다르고 같은 3DSSG/3RScan geometry와
> ontology를 사용하므로 generalization evidence가 제한적이다.

### Facts

- 세 predictor의 candidate distribution과 confidence scale은 다르다.
- dataset, GT ontology, reconstructed geometry는 공유한다.
- ReplicaSSG/FROSS stress test는 target-dependent하고 K=100에서 포화된다.

### Current defense

- Claim을 `behavior across three predictors on a shared target`으로 제한한다.
- External result를 supplement stress test로 보고하고 all-K curve와 saturation을
  공개한다.
- Abstract/Conclusion에서 dataset-level generalization을 사용하지 않는다.

### Still missing

- 충분한 exact-label candidate coverage를 가진 untouched external dataset에서의
  confirmation.

### Blocked wording

- cross-dataset generalization established.
- arbitrary-source/dataset robustness.

## R3. Support/Contact Applicability

### Reviewer attack

> 왜 세 family model을 학습하면서 support/contact에는 method를 적용하지 않는가?

### Facts

- Unrestricted product는 support/contact selection을 바꾸고 family Violation을
  악화시킬 수 있다.
- 현재 feature는 local contact, articulation, pose를 충분히 관측하지 않는다.
- Support/contact 전체에 적용 가능한 하나의 endpoint transformation이 없다.

### Current defense

- Primary ranking은 support/contact source order와 selection을 정확히 유지한다.
- Proximity/vertical에서만 compatibility를 사용한다.
- Figure 3에 unchanged residual failure를 포함한다.
- Family-wise metrics를 따로 보고한다.

### Still missing

- richer local point/mesh contact evidence와 predicate-specific transformation.

### Blocked wording

- family-uniform improvement.
- support/contact solved.
- 모든 relation에 보편적으로 적용되는 해결책.

## R4. Novelty Ceiling

### Reviewer attack

> 이 방법은 engineered geometry feature를 logistic regression으로 학습해 score를
> 곱하는 단순 post-processing 아닌가?

### Current defense

- Failure cause에서 factor separation의 필요성을 도출한다.
- Source score와 predictor identity를 compatibility에서 제외한다.
- Positive/counterfactual pair의 ordering을 직접 학습한다.
- Proximity symmetry와 vertical inverse consistency를 inference에서 정확히
  만족시킨다.
- Identity-preserving joins, wrong-pair/predicate/transformation controls를
  하나의 falsification contract로 제시한다.
- Family-aware sorting이 every-K family composition과 support/contact order를
  보존한다.
- GEODE처럼 geometry를 generator 내부에 넣는 최신 방법과 달리, fixed candidate
  output에서 source score를 compatibility 입력과 분리하고 relation
  transformation을 보장한다는 경계를 Related Work에 명시한다.

### Residual limit

- Feature와 model 자체는 작고 engineered다.
- Contribution을 novel geometry encoder나 universal rescorer로 높일 근거는 없다.

### Correct novelty statement

> The contribution is a factor-separated reliability layer that combines
> linked counterfactual compatibility learning, exact relation-transformation
> consistency, and family-scoped re-ranking for fixed relation outputs.

## R5. Strong Comparators

### Reviewer attack

> 더 큰 MLP나 일반 rank fusion이 같은 또는 더 좋은 결과를 얻는다면 product가
> 왜 method인가?

### Facts

- RelCompat3D-MLP는 Open3DSG에서 Linear보다 일부 K의 Recall이 더 높지만
  Violation도 더 높다.
- RankAvg/RRF는 일부 large-K Violation을 낮추지만 low-budget Recall loss가 크다.
- Unrestricted product는 aggregate Recall이 높을 수 있지만 family scope를
  바꾼다.
- 하나의 comparator가 모든 source와 K에서 joint objective를 지배하지 않는다.

### Current defense

- 모든 strong comparator를 같은 family-aware ranking procedure로 평가한다.
- Main Table 1에 RelCompat3D-Linear와 RelCompat3D-MLP를 두 proposed capacity로
  직접 포함하고, principal controls와 surface audit를 두 capacity 모두에 적용한다.
- Product utility를 best formula가 아니라 두 compatibility capacity가 공유하는
  parameter-free ranking rule로 설명한다.
- Framework novelty와 fusion choice를 분리한다.
- 모든 K의 scan-cluster interval을 공개해 일부 budget의 point-estimate 개선을
  일괄적인 통계적 우월성으로 확대하지 않는다.

### Blocked wording

- state-of-the-art rescorer.
- formula superiority.
- consistently dominates rank fusion/nonlinear models.

## R6. Open3DSG Coverage

### Reviewer attack

> Open3DSG public preprocessing이 모든 official context에 candidate를 만들지
> 못한다면 main 수치는 어떤 target을 평가한 것인가?

### Facts

- Public candidate lists가 없는 context도 official 548-context target에는
  포함한다.
- Main evaluation은 해당 context를 empty candidate list로 처리하고 3,972 GT
  Recall denominator를 유지한다.
- Candidate가 제공된 context만 따로 평가한 결과와 추가 preprocessing으로
  모든 context의 candidate를 구성한 결과는 supplement sensitivity다.

### Current defense

- Main은 public predictions를 official 548-context target 전체에서 평가한다.
- Ground-truth availability는 inclusion/ranking에 사용하지 않는다.
- Coverage sensitivity의 conclusion direction이 일치한다.
- 자세한 preprocessing 수치는 main narrative가 아니라 supplement와 공개 산출물에
  둔다.

### Blocked wording

- complete standard Open3DSG reproduction.
- Open3DSG leaderboard/SOTA result.

## Additional Reporting Risks

### K selection

- 모든 K={5,10,20,50,100}를 main table과 Figure 2에 남긴다.
- K=50을 intermediate reported budget으로만 사용하고 outline하지 않는다.
- 모든 K에서 유의한 Recall improvement를 주장하지 않는다.

### Hard filter

- V=0은 construction이고 K보다 적은 행을 선택할 수 있다.
- Primary comparator가 아니라 diagnostic으로 유지한다.

### Uncertainty denominator

- all-status V, decidable-only V, uncertainty rate, pessimistic V를 함께
  sensitivity로 보고한다.
- uncertain을 satisfied라고 표현하지 않는다.

## Claim Contract

Allowed:

> RelCompat3D reduces verifier-derived Violation with source-dependent Recall
> trade-offs across three relation predictors on a shared 3DSSG target, while
> retaining source order for relation families outside its geometric
> re-ranking scope.

Not allowed:

- independent physical-validity validation.
- all-relation or support/contact improvement.
- dataset-level generalization.
- universal/best fusion.
- complete open-vocabulary graph-generation improvement.

## Submission Gate

Scientific gate는 canonical PDF와 anonymous source bundle이 current tables,
figures, and claim을 재현하면 충족된다. 현재 남은 required task는 author metadata,
reciprocal reviewer declaration, license/artifact URL, 그리고 사용자가 다시 그린
figure의 source-lock verification이다.
