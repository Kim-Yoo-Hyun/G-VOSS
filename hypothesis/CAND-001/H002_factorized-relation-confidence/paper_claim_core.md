# H002 Paper Claim Core

Last updated: 2026-07-11 KST

## Problem

Relation predictors rank semantically plausible edges with a single source
confidence, but that score does not identify whether the predicate is compatible
with the observed object-pair geometry. A fixed semantic-geometry fusion is also
insufficient because different relation families require different evidence.

## Scoped Claim

H002 proposes relation-aware evidence routing and quantitatively validates its
predicate-geometry compatibility route on geometry-checkable comparison
relations. It does not claim that reliable relation estimation is solved for all
3D relation families.

## Representation

\[
T_e=f_T(p,c_s,c_o),\qquad
G_e=f_G(x_s,x_o),\qquad
Z_e=f_Z(s_{\rm src},r_{\rm src})
\]

\[
C_e^{\rm raw}=f_C(T_e,G_e),\qquad Z_e\notin f_C.
\]

- `T_e`: predicate and endpoint semantic content
- `G_e`: predicate-independent geometry evidence
- `Z_e`: source confidence and rank
- `C_e^{raw}`: train-only logistic predicate-geometry compatibility in \([0,1]\)

The main score is

\[
\widetilde Z_e=\operatorname{MinMax}_{\rm source}(Z_e),\qquad
\widetilde C_e=\operatorname{MinMax}_{\rm source,family}(C_e^{\rm raw}),
\qquad S_2(e)=\widetilde Z_e\,\widetilde C_e.
\]

Its risk-aware form is

\[
\log S_2(e)
=\log\widetilde Z_e-\lambda[-\log\widetilde C_e],\qquad \lambda=1.
\]

\(\lambda=1\) is the parameter-free product score; it avoids validation-tuned
risk weighting. Scores are clamped at \(\epsilon=10^{-6}\) before the log
interpretation. Both normalization bounds use labels neither for fitting nor
selection. H002 reports sensitivity rather than claiming normalization invariance.

## Route Protocol

| Decision question | Route |
| --- | --- |
| Is metric geometry sufficient? | geometry-only |
| Does the predicate change geometry interpretation? | compatibility |
| Is an external reference frame required? | frame-aware compatibility |
| Are contact, pose, or local surface cues required? | hard physical route |
| Is evidence availability itself uncertain? | observability-aware route |
| Is the relation primarily ontological or structural? | semantic/structural route |

The protocol is a framework map, not evidence that every route is solved.

## Evaluation

- Dataset: official 3DSSG validation split
- Sources: VL-SAT and Open3DSG validation predictions
- Open3DSG boundary: open-vocabulary source, closed-vocabulary 3DSSG mapping for quantitative Recall
- Baseline: `S0_source_score`
- Main score: `S2_source_x_Ce`
- Metrics: Recall@K and custom Violation@K
- K grid: 5, 10, 20, 50, 100
- Uncertainty: 1,000 grouped bootstrap replicates

The logistic compatibility model is fit on 4,868 internal-train rows. Official
validation rows are evaluation-only.

## Main Result

For higher/lower and bigger/smaller, aggregated over the two sources:

| K | S0 Recall | S2 Recall | Delta Recall, 95% CI | S0 Violation | S2 Violation | Delta Violation, 95% CI |
| ---: | ---: | ---: | --- | ---: | ---: | --- |
| 5 | 0.3447 | 0.3526 | +0.0079 [-0.0060, 0.0226] | 0.2952 | 0.0545 | -0.2407 [-0.2544, -0.2277] |
| 10 | 0.4717 | 0.5136 | +0.0420 [0.0232, 0.0621] | 0.3022 | 0.0723 | -0.2299 [-0.2397, -0.2202] |
| 20 | 0.6429 | 0.7245 | +0.0816 [0.0481, 0.1180] | 0.3436 | 0.1005 | -0.2431 [-0.2519, -0.2351] |
| 50 | 0.8492 | 0.9524 | +0.1032 [0.0689, 0.1407] | 0.4252 | 0.1660 | -0.2592 [-0.2662, -0.2524] |

\(K=5\) Recall CI includes zero and is not used as a strong Recall claim.
\(K=100\) is treated as saturation analysis.

## Mechanism Controls

- semantic-only
- geometry-only
- plain `T_e+G_e` concatenation
- wrong predicate
- shuffled geometry
- wrong-pair geometry
- source-rank-only and class-pair shortcut probes

These controls test whether \(C_e\) depends on the matched predicate and
object-pair geometry rather than copying \(Z_e\) or a construction field.

## Route Status

- **Main:** relative vertical and relative size comparison.
- **Caveated:** left/right; Open3DSG gains are large, while VL-SAT trades small Recall loss for lower Violation.
- **Control:** close by is geometry-decidable and does not establish interaction necessity.
- **Failure:** front/behind remains reference-frame/depth ambiguous.
- **Diagnostic:** support/contact has 35 positives and 347 negatives, a 0.908 majority baseline, and its proxy target is exactly recovered by the construction rule. It is not an independent reliability target.

## Claim Boundary

Allowed:

- source-independent predicate-geometry compatibility improves validation-level reranking on scoped comparison relations
- route families require different evidence
- support/contact exposes the need for richer independent evidence

Blocked:

- all-relation reliable 3D scene graph framework solved
- official test, leaderboard, or SOTA claim
- support/contact, learned `G_e`, or calibrated `p_obs/p_rel` solved
- normalization-invariant improvement

## Authoritative Outputs

- `experiments/H002_compatibility_routing/source_reranking_evaluation/latest/`
- `experiments/H002_compatibility_routing/source_reranking_ci/latest/`
- `experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/`
- `experiments/H002_compatibility_routing/relative_horizontal_split_route_scorer/latest/`
- `experiments/H002_compatibility_routing/main_validation_table_refresh/latest/`
- `experiments/H002_compatibility_routing/support_contact_independent_target_repair_diagnostic_freeze/latest/`
- `paper/h002_compatibility_routing/aaai2027/`
