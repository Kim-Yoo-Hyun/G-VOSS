# RelCompat3D Current Paper Preview

Last updated: 2026-07-17 KST

이 문서는 H001 manuscript의 현재 handoff snapshot만 소유한다. Method와
experiment의 상세 설명은 각각 `paper/method.md`와 `paper/experiment.md`를
사용하고, 과거 연구 chronology는 experiment reports와 archive에서 확인한다.

## Current Identity

- Title: **Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking
  for 3D Scene Graphs**
- Method: **RelCompat3D**
- Venue source: `paper/aaai/`
- Main scope: proximity와 relative vertical re-ranking; support/contact는
  평가하지만 source order를 유지한다.
- Predictors: VL-SAT, Open3DSG, SceneGraphFusion.
- Target: shared 3DSSG/3RScan final-validation geometry and ontology.

## Current Claim

> RelCompat3D separates the source relation score from predicate–geometry
> compatibility, imposes the applicable proximity/vertical transformation
> consistency, and re-ranks only proximity/vertical relations. On a
> shared 3DSSG target, the resulting reliability layer shows
> Violation reductions and source-dependent Recall trade-offs across three
> relation predictors.

이 claim은 다음을 포함하지 않는다.

- 새로운 relation generator 또는 open-vocabulary SOTA.
- best/universal fusion formula.
- independent human physical-validity metric.
- cross-dataset generalization.
- support/contact improvement.

## Manuscript Structure

1. Introduction
2. Related Work
3. Method, including Problem Setup
4. Experiments, including setup and results
5. Discussion and Limitations
6. Conclusion

Narrative는 observed failure → structural cause → factor separation → method →
evidence → limitations 순서다.

## Current Evidence

- 1,061 training / 117 development / 157 final-evaluation scans.
- 548 evaluation contexts and 3,972 exact-label GT relations.
- K=`{5,10,20,50,100}`를 모두 Table 1과 Figure 2에 공개.
- Source, RelCompat3D, matched nonlinear model, RankAvg, RRF, all-family
  product를 동일 candidate universe에서 비교.
- Wrong predicate, wrong pair, shuffled geometry, label-fixed swap,
  distance-only, compatibility-only controls를 K=50/100에서 비교.
- 모든 K의 paired 1,000-resample scan-cluster interval과
  uncertainty/family sensitivity.
- Exact verifier scalar 및 관련 measurement family를 제거한 train-only refit.
- Counterfactual thresholds와 negative cap/pair-loss weight sensitivity.
- Preloaded rows와 pair geometry 이후의 compatibility/re-ranking만 재는
  single-process CPU benchmark와 parameter count.

K=50 percentage point summary:

| predictor | Source R / V | RelCompat3D R / V |
| --- | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 |

VL-SAT Recall interval은 0을 포함하므로 유의한 Recall gain으로 표현하지 않는다.
Open3DSG와 SGFN은 K=50에서 Recall 증가와 Violation 감소가 scan-cluster interval로
지지된다.

## Current Figures and Tables

- Figure 1: measured high-confidence Open3DSG failure에서 compatibility와
  family-aware re-ranking으로 이어지는 overview.
- Figure 2: 세 predictor의 percentage Recall--Violation trajectory.
- Figure 3: ordered pair → geometry evidence → ranking outcome grid.
- Table 1: 모든 K의 Recall/Violation percentage와 main/strong comparisons.
- Table 2: K=50/100 falsification 및 information controls.

재작업 명세는 `paper/figures.md`가 소유한다.

## Main Scientific Limits

1. Compatibility target과 Violation verifier가 일부 geometry primitive를
   공유한다.
2. 세 predictor가 하나의 dataset target을 공유한다.
3. Support/contact는 현재 evidence로 reliable하게 re-rank하지 않는다.
4. Nonlinear/rank fusion이 일부 operating point에서 강하므로 formula
   superiority를 주장하지 않는다.

상세 attack/defense map은 `paper/risk.md`를 따른다.

## Canonical Outputs

| artifact | path | SHA-256 |
| --- | --- | --- |
| main paper | `paper/aaai/main_aaai27.pdf` | `5a3012f8d529e147f647c3a92d388940f675b2f98728371429a3a965e4d4f46f` |
| supplement | `paper/aaai/supplement_aaai27.pdf` | `a3138be52be01c5d30b0e9494c9f2cae0fa681868b8459fcd0281d4f274b6e8f` |
| checklist | `paper/aaai/reproducibility_checklist_aaai27.pdf` | `1c3efa0baeb0514da8b8587386cbe7ec1260b2358f5f9f04ad8cb2d015419d` |

- Layout: 9/5/2 pages, US Letter.
- Main text continues through page 7; references begin on page 7 and continue
  through page 9.
- The current verified upload set is
  `release/h001_aaai27_openreview_20260717_193626/`; it contains the current
  transcript and an independently rebuildable anonymous 198-record source ZIP.

## Remaining User-Controlled Tasks

- OpenReview author order, profiles, affiliations/countries, conflicts.
- reciprocal reviewer nomination/eligibility declaration.
- final public code license and post-acceptance artifact URL.
- optional independent human alignment study.

## Reading Map

1. `paper/outline.md`: section logic and placement.
2. `paper/method.md`: method tutorial and equations.
3. `paper/experiment.md`: comparisons, metrics, statistics.
4. `paper/figures.md`: complete redraw specification.
5. `paper/risk.md`: scientific attack/defense register.
6. `paper/review.md`: three orthogonal reviewer assessments.
7. `docs/reproducibility.md`: exact recovery/build/release commands.
