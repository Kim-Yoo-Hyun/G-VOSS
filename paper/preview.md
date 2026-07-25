# RelCompat3D Current Paper Preview

Last updated: 2026-07-22 KST

이 문서는 현재 submission handoff snapshot만 소유한다. 상세 method와
experiment contract는 `paper/method.md`와 `paper/experiment.md`, section 논리는
`paper/outline.md`, reviewer 판단과 남은 위험은 `paper/review.md`와
`paper/risk.md`를 따른다.

## Current Identity

- Selected title: **RelCompat3D: Predicate–Geometry Compatibility for Re-Ranking
  3D Scene Graph Relations**
- Source status: the consolidated main and supplementary TeX titles use the
  selected `Re-Ranking` title.
- Method: **RelCompat3D**
- Venue source: `paper/aaai/`
- Selected main artifact: `paper/aaai/main_teaser_aaai27.pdf`
- Predictors: VL-SAT, Open3DSG, and the released SceneGraphFusion benchmark
  model (SGFN).
- Target: one shared 3DSSG/3RScan evaluation geometry and ontology.
- Re-ranking scope: proximity and vertical-order candidates.
- Preserved scope: support/contact candidates retain source order.
- Active protocol: strict train-only `no_family_indicator_v1` for the Linear
  heads, plus a compact shared nonlinear estimator.

## Current Claim

> RelCompat3D estimates predicate--geometry compatibility without using the
> source relation score or predictor identity, combines compatibility with the
> score only during family-aware re-ranking, and improves or ties the reported
> Recall--Violation point-estimate trade-off across three predictors on one
> shared 3DSSG target.

This is a scoped reliability claim. It does not claim:

- a new relation generator or open-vocabulary SOTA;
- a calibrated probability of physical validity;
- a universal/best fusion rule;
- support/contact correction;
- established cross-dataset generalization.

## Manuscript Structure

The active main source is consolidated into:

1. `sec/0_abstract.tex`
2. `sec/1_introduction.tex`
3. `sec/2_related_work.tex`
4. `sec/3_method.tex`
5. `sec/4_experiments.tex`
6. `sec/5_discussion_limitations.tex`
7. `sec/6_conclusion.tex`

The active technical supplement is `sec/supplement.tex`. Inactive relative-size
material is retained only in `sec/old.tex`.

Narrative order:

```text
observed ordered-pair failure
→ source-score / compatibility separation
→ linked counterfactual learning and transformation averaging
→ family-aware re-ranking
→ Recall–Violation evidence and controls
→ construct and scope limits
```

## Current Evidence

- 1,061 training, 117 development, and 157 evaluation scans.
- 548 evaluation contexts and 3,972 exact-match ground-truth relations.
- $K\in\{5,10,20,50,100\}$ reported for all three predictors.
- Source, RelCompat3D-Linear, RelCompat3D-MLP, RankAvg, RRF, and Product (all
  families) evaluated on the same candidate universe.
- K=50 matched controls for wrong predicate/pair, shuffled geometry,
  fixed-predicate endpoint swap, distance only, and compatibility only.
- Complete K=100 controls, feature-removal refits, counterfactual sensitivity,
  transformation checks, uncertainty, and family decomposition in the
  supplement.
- Paired scan-level bootstrap intervals with contexts retained within scans.
- Point- and mesh-based alternative audit that excludes OBB inputs and primary
  verifier labels, while still sharing reconstructed geometry and ontology.

K=50 point-estimate summary (%):

| predictor | Source R / V | Linear R / V | MLP R / V |
| --- | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | 92.72 / 1.89 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | 46.70 / 4.13 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | 74.57 / 2.58 |

At K=50, paired intervals support Recall increase and Violation decrease for
Open3DSG and SGFN. VL-SAT's Recall interval contains zero, while its Violation
interval is below zero. Across all 15 predictor--K cells, both proposed
variants have Recall point estimates no lower and Violation point estimates no
higher than Source; this statement is about point estimates, not universal
statistical dominance.

## Selected Figures and Tables

| item | selected content | canonical page |
| --- | --- | ---: |
| Figure 1 | Open3DSG `desk higher than ceiling`, rank 6 → 425 | 1 |
| Figure 2 | pair geometry and relation → compatibility → within-family score → family-aware re-ranking | 4 |
| Table 1 | all-K main comparisons for three predictors | 6 |
| Table 2 | K=50 matched Linear/MLP controls | 7 |
| Table 3 | K=50 point/mesh agreement audit for Linear | 7 |
| Figure 3 | Source/Linear/MLP Recall--Violation trajectories | 6 |

Figure 1 supplies motivation/outcome, Figure 2 explains mechanism, and Figure
3 reports aggregate behavior. The three-case qualitative grid, complete
controls, and all-K audit remain supplemental.

## Selected Main and Build State

| artifact | role | pages | SHA-256 |
| --- | --- | ---: | --- |
| `paper/aaai/main_teaser_aaai27.pdf` | **selected main submission PDF** | 9 | `b2219ed69acc1969d28b275c638f9328d096f7e62e0beb9a2d515530648cba15` |
| `paper/aaai/main_aaai27.pdf` | non-selected comparison build | 9 | `5b9d917a61fc9045f46aa477750590f40c621157068ae74dec1ccc5e8e7f113b` |
| `paper/aaai/supplement_aaai27.pdf` | technical supplement | 10 | `b9dc44ce09bb12d805472ead80bb72ca174cb844658929325917f59a7103226e` |
| `paper/aaai/reproducibility_checklist_aaai27.pdf` | standalone checklist | 2 | `cd12a07ab1f9067a73f7aec128d43721c00c71bc17130acc32f6d34b99079e59` |

The selected canonical teaser now builds from the consolidated
`user_v6`-aligned source as nine pages, with seven technical pages and
references on pages 7--9. It retains a 36.78-pt first-page vertical overfull and
one 4.43-pt overfull table row. Per the current decision, both warnings are
deferred until the final layout pass.

The existing verified release bundle
`release/relcompat3d_aaai27_openreview_20260720_084307/` already selects the teaser
layout but predates the latest source organization and must be regenerated
before upload.

## Current Scientific Limits

1. Compatibility construction and primary Violation share some OBB-derived
   geometric measurements.
2. The point/mesh audit is an alternative construct check, not independent
   physical-validity ground truth.
3. All three predictors use one shared dataset target.
4. Support/contact candidates are not re-ranked.
5. Linear, MLP, and rank-fusion methods occupy different operating points;
   formula superiority is not established.

Detailed attacks, defenses, and blocked wording are owned only by
`paper/risk.md`.

## Remaining Work

Required before submission:

- resolve the first-page vertical overfull and 4.43-pt overfull table row;
- regenerate the anonymous release bundle from the selected canonical source;
- verify live-form title, abstract, TL;DR, topics, and anonymity;
- complete OpenReview author metadata, conflicts, and reciprocal-reviewer
  declaration;
- decide the public license and post-acceptance artifact URL.

Optional scientific strengthening:

- independent reference labels or human alignment;
- an untouched external dataset with adequate candidate coverage;
- richer contact/pose evidence for support/contact.
