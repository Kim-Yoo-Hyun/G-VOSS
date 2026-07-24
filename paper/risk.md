# RelCompat3D Reviewer-Risk Register

Last updated: 2026-07-23 KST

이 문서는 current submission claim에 영향을 주는 reviewer attack, verified
facts, defense, residual action, and blocked wording만 소유한다. Reviewer score와
overall assessment는 `paper/review.md`, experiment 계산법은
`paper/experiment.md`, 진행 상태는 `paper/progress.md`가 소유한다.

## Risk Summary

| ID | risk | severity | current status |
| --- | --- | --- | --- |
| R1 | compatibility construction and primary verifier overlap | critical | substantially mitigated; residual |
| R2 | one shared dataset target | high | disclosed; unresolved |
| R3 | support/contact outside re-ranking scope | high | operationally contained |
| R4 | novelty reduced to engineered rescoring | high | framing-dependent |
| R5 | strong nonlinear and rank-fusion alternatives | medium | matched comparisons complete |
| R6 | Open3DSG candidate coverage and reproduction | medium | full-target policy documented |
| R7 | selected canonical PDF and consolidated source diverge in layout | high | deferred; must close before upload |

## R1. Construct Dependence

**Reviewer attack**

> The model may be learning geometric rules that are also used by the primary
> Violation verifier, making the evaluation partly circular.

**Verified facts**

- Counterfactual construction and the primary verifier share some OBB-derived
  distance, overlap, height, and threshold families.
- Evaluation rows and verifier-status labels are not training examples.
- Wrong-pair/predicate/shuffle controls test whether the estimator ignores the
  candidate identity or predicate, but do not create independent ground truth.
- The point/mesh audit excludes OBB inputs and primary verifier labels but uses
  the same reconstructed geometry and ontology.

**Current defense**

- Define compatibility as a constructed-target ranking score, not a posterior
  probability of validity.
- Call the main metric `verifier-derived Violation@$K$`.
- Report feature-removal refits, threshold/counterfactual sensitivity, and
  point-/mesh-based alternative measurements.
- Keep exact-match Recall visible with Violation to expose task trade-offs.

**Residual action**

No additional experiment is required for the scoped submission. Independent
reference labels or human alignment would strengthen the claim but would open a
new evidence protocol.

**Blocked wording**

- human-validated or independently verified physical correctness;
- independent physical-validity ground truth;
- calibrated probability of validity.

## R2. Shared Dataset Target

**Reviewer attack**

> VL-SAT, Open3DSG, and SGFN differ as predictors but share the same 3DSSG
> geometry and relation ontology, so this is not cross-dataset evidence.

**Verified facts**

- Candidate distributions and native score contracts differ across predictors.
- Dataset, reconstruction, and evaluation ontology are shared.
- ReplicaSSG/FROSS is a supplemental stress test with target-dependent behavior
  and limited candidate coverage.

**Current defense**

- State `three predictors on one shared 3DSSG target` in Abstract, Results,
  Discussion, and Conclusion.
- Use the external result only as a transfer stress test.
- Separate cross-predictor robustness from dataset generalization.

**Residual action**

An untouched external dataset with adequate exact-label candidate coverage is
optional strengthening, not a requirement for the frozen claim.

**Blocked wording**

- cross-dataset generalization established;
- arbitrary-source or arbitrary-dataset robustness.

## R3. Support/Contact Scope

**Reviewer attack**

> Why evaluate support/contact if the proposed method does not re-rank it?

**Verified facts**

- Current measurements do not fully observe local contact, articulation, and
  pose.
- No single endpoint transformation preserves every support/contact predicate.
- Applying compatibility to all families can change selections and mask a
  support/contact regression.

**Current defense**

- Define evaluation and re-ranking scopes separately.
- Use the exact source-ranking support/contact subsequence in the primary rule.
- Report Product (all families) as a scope comparison rather than the method.
- Preserve family-specific metrics and a residual qualitative case in the
  supplement.

**Residual action**

Richer contact/pose evidence and predicate-specific transformations belong to a
future method extension.

**Blocked wording**

- support/contact solved;
- all-family or family-uniform improvement;
- universal relation re-ranking.

## R4. Novelty Ceiling

**Reviewer attack**

> RelCompat3D is an engineered geometry classifier followed by score
> multiplication and sorting.

**Verified facts**

- Linear features and product scoring are simple.
- Finite transformation averaging is a standard invariance construction.
- The method does not introduce a new geometry encoder or relation generator.
- Direct Linear removal shows only a small aggregate effect from the linked
  pairwise term.
- Removing transformation averaging changes aggregate metrics little but
  produces nonzero discrepancies between transformed representations, while
  the full method makes those discrepancies exactly zero.

**Current defense**

- Tie the method form directly to the diagnosed score/compatibility mismatch.
- Present the contribution as one contract combining:
  source-score exclusion, ordered-pair identity, linked counterfactual learning,
  exact applicable transformations, and family-aware output preservation.
- Use Linear and MLP as two estimators within the same framework.
- Distinguish fixed-output reliability assessment from generator-internal
  geometry conditioning and declarative constraint refinement.

**Allowed novelty statement**

> RelCompat3D is a factor-separated reliability framework for fixed relation
> predictions that couples linked counterfactual compatibility learning,
> exact relation-transformation consistency, and family-scoped re-ranking.

**Blocked wording**

- novel multiplication/fusion rule;
- novel group-averaging theorem;
- universal geometry encoder or best rescorer.

## R5. Comparator Trade-offs

**Reviewer attack**

> If an MLP or rank fusion has better Recall or Violation at some settings, why
> is the proposed scoring rule necessary?

**Verified facts**

- Linear and MLP occupy different Recall--Violation operating points.
- RankAvg/RRF can lower Violation at some larger $K$ values but lose more Recall
  at smaller $K$ values.
- Product (all families) changes the method's family scope.
- No ranking rule dominates all predictors and reported $K$ values.

**Current defense**

- Treat Linear and MLP as equal proposed estimators.
- Match candidate universe and family-aware ranking procedure across
  comparators.
- Claim framework-level behavior rather than formula superiority.
- Report all five $K$ values and predictor-specific trade-offs.

**Blocked wording**

- consistently dominates;
- state-of-the-art rescorer;
- universally superior estimator or fusion.

## R6. Open3DSG Coverage

**Reviewer attack**

> Public Open3DSG preprocessing does not provide candidates for every official
> context, so the evaluation target may be ambiguous.

**Verified facts**

- The official evaluation universe contains 548 contexts and 3,972 exact-label
  ground-truth relations.
- Missing public candidate lists are treated as empty; the GT denominator is
  retained.
- Ground-truth availability is not used to include, filter, or rank candidates.
- Coverage sensitivity is supplemental.

**Current defense**

- Describe the full-target empty-list policy in Experimental Setup or the
  supplement.
- Keep exact Recall and verifier denominators reproducible.
- Avoid leaderboard or full-reproduction claims.

**Blocked wording**

- complete standard Open3DSG reproduction;
- official Open3DSG SOTA or leaderboard result.

## R7. Selected PDF vs. Consolidated Source

**Reviewer/administrative attack**

> The submitted source may rebuild to a PDF that exceeds the AAAI limit or
> differs from the selected review PDF.

**Verified facts**

- Selected main: `paper/aaai/main_teaser_aaai27.pdf`, 9 pages, SHA-256
  `ac0313df7248da518488f0f39ab7d6cce42d1ac2cc6d5f234fc2aee4631e588c`.
- It contains seven technical pages and references on pages 7--9.
- The freshly consolidated teaser source currently builds to 10 pages and has
  one 4.43-pt overfull table row.
- Pre/post section-consolidation PDF text is identical, so file merging did not
  create the discrepancy.
- The user has selected the canonical teaser layout and explicitly deferred
  page compression and overfull repair to the next pass.

**Required closure before upload**

1. Restore a compliant selected teaser build without margin changes, type
   reduction, or negative spacing.
2. Fix the overfull table row.
3. Rebuild canonical main/supplement/checklist from the consolidated source.
4. Refresh hashes and regenerate the anonymous source/release bundle.
5. Verify extracted-source rebuild, pages, fonts, citations, anonymity, and
   archive integrity.

**Blocked action**

- Uploading the old canonical PDF with a source archive that rebuilds to the
  10-page variant.

## Reporting Invariants

- Report every $K\in\{5,10,20,50,100\}$; K=50 is intermediate, not selected.
- Distinguish point-estimate non-degradation from confidence-interval support.
- Treat uncertain verifier rows according to the declared denominator and do
  not call them satisfied.
- Do not use hard-filter V=0 as primary evidence because it may return fewer
  than $K$ candidates.
- Keep Surface/point-mesh values distinct from primary Violation values.
- Refer to the released SceneGraphFusion model as SGFN after its local
  definition and citation.

## Claim Contract

Allowed:

> Across three relation predictors on one shared 3DSSG target, both RelCompat3D
> estimators improve or tie the reported Source Recall--Violation point
> estimates while preserving the source family sequence and support/contact
> candidate order.

Not allowed:

- independent physical-validity validation;
- all-relation or support/contact improvement;
- dataset-level generalization;
- universal/best fusion;
- 3D scene graph generation SOTA.

## Submission Gate

Scientific evidence is complete for the scoped claim. Submission readiness is
blocked only by R7 and external form metadata: author profiles/order,
affiliations/countries, conflicts, reciprocal-reviewer declaration, final live
title/abstract/TL;DR/topics, license, and artifact URL.
