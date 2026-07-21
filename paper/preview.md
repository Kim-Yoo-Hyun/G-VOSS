# RelCompat3D Current Paper Preview

Last updated: 2026-07-20 KST

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
- Active model: `no_family_indicator_v1`; `T_i=p_i`, while the family label
  selects the head/procedure without entering the feature vector. The three
  heads store 66 parameters and the primary path evaluates 43.

## Current Claim

> RelCompat3D separates the predictor score from predicate–geometry
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
- 548 evaluation contexts and 3,972 exact-match GT relations.
- K=`{5,10,20,50,100}`를 모두 Table 1과 Figure 2에 공개.
- Source, RelCompat3D-Linear, RelCompat3D-MLP, RankAvg, RRF, product applied to
  all relation families를 동일 candidate universe에서 비교.
- Wrong predicate, wrong pair, shuffled geometry, fixed-predicate endpoint swap,
  distance-only, compatibility-only controls를 K=50/100에서 비교.
- 모든 K의 paired 1,000-resample intervals from a cluster bootstrap over scans와
  uncertainty/family sensitivity.
- Exact verifier scalar 및 관련 measurement family를 제거한 train-only refit.
- Counterfactual thresholds와 negative cap/pair-loss weight sensitivity.
- OBB inputs와 primary verifier labels를 읽지 않는 point/mesh surface audit,
  strict consensus, intervals from a cluster bootstrap over scans, coverage, synthetic interventions.
- Preloaded rows와 pair geometry 이후의 compatibility/re-ranking만 재는
  single-process CPU benchmark와 parameter count.

K=50 percentage point summary:

| predictor | Source R / V | Linear R / V | MLP R / V |
| --- | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | 92.72 / 1.89 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | 46.70 / 4.13 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | 74.57 / 2.58 |

VL-SAT Recall interval은 0을 포함하므로 유의한 Recall gain으로 표현하지 않는다.
Open3DSG와 SGFN은 K=50에서 Recall 증가와 Violation 감소가 intervals from a
cluster bootstrap over scans로 지지된다.

## Current Figures and Tables

- Figure 1: measured high-confidence Open3DSG failure에서 compatibility와
  family-aware re-ranking으로 이어지는 overview.
- Figure 2: Source, RelCompat3D-Linear, RelCompat3D-MLP의 세-predictor
  percentage Recall--Violation trajectory.
- Selected teaser variant: full-width first-page pair-level Top-50 exchange
  (desk--ceiling leaves, desk--chair enters), followed by the teaser-specific
  full-width method overview. The three-case qualitative grid is in the
  supplement for both main variants to keep the body at seven pages.
- Table 1: 모든 K의 Recall/Violation percentage와 main/strong comparisons.
- Table 2: Linear/MLP의 K=50 wrong-predicate, wrong-pair, shuffled-geometry,
  fixed-label swap, distance-only, compatibility-only matched controls.
- Table 3: K=50 point--mesh-consensus Surface-V의 Source와 Linear 결과,
  paired scan-cluster 95% CI, measured/decidable coverage. MLP surface audit은
  supplement에 유지한다. 선택된 teaser에서는
  Table 2와 page 7 상단에 좌우 one-column 형태로 배치한다.
- Supplement: all-K point/mesh/consensus audit, coverage, thresholds, and
  interventions. Surface-V는 primary Violation과 절대값을 직접 비교하지 않는다.
- Supplement tables: complete Linear/MLP K=100 controls.

재작업 명세는 `paper/figures.md`가 소유한다.

## Main Scientific Limits

1. Compatibility target과 primary Violation verifier가 일부 OBB geometry
   primitive를 공유한다. Point/mesh surface audit가 exact-rule overlap을
   줄이지만 동일 reconstructed surface와 ontology는 공유한다.
2. 세 predictor가 하나의 dataset target을 공유한다.
3. Support/contact는 현재 evidence로 reliable하게 re-rank하지 않는다.
4. Nonlinear/rank fusion이 일부 operating point에서 강하므로 formula
   superiority를 주장하지 않는다.

상세 attack/defense map은 `paper/risk.md`를 따른다.

## Canonical Outputs

| artifact | path | SHA-256 |
| --- | --- | --- |
| main paper | `paper/aaai/main_aaai27.pdf` | `5b9d917a61fc9045f46aa477750590f40c621157068ae74dec1ccc5e8e7f113b` |
| teaser comparison | `paper/aaai/main_teaser_aaai27.pdf` | `ac0313df7248da518488f0f39ab7d6cce42d1ac2cc6d5f234fc2aee4631e588c` |
| supplement | `paper/aaai/supplement_aaai27.pdf` | `b9dc44ce09bb12d805472ead80bb72ca174cb844658929325917f59a7103226e` |
| checklist | `paper/aaai/reproducibility_checklist_aaai27.pdf` | `cd12a07ab1f9067a73f7aec128d43721c00c71bc17130acc32f6d34b99079e59` |

- Layout: default main 9, teaser main 9, supplement 10, checklist 2 US-Letter
  pages. Both main variants end technical content on page 7. The default begins
  references in the remaining page-7 column; the teaser begins them on page 8.
- `release/h001_aaai27_openreview_20260720_084307/` is the latest verified
  pre-table-layout bundle. Regenerate it before upload so its teaser `main.pdf`
  matches the canonical table-layout revision above.

## Remaining User-Controlled Tasks

- OpenReview author order, profiles, affiliations/countries, conflicts.
- upload layout은 first-page teaser main으로 선택됨; current caption revision을
  반영한 release regeneration이 필요함.
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
