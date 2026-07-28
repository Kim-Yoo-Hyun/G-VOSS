# RelCompat3D Final Reviewer Assessment

Last updated: 2026-07-28 KST

## Review Target

The assessment covers the final main source, 10-page technical supplement,
2-page reproducibility checklist, and conservative anonymous code/data
archive.

## Summary

RelCompat3D addresses fixed 3D scene graph relations whose source scores do not
explicitly measure whether the corresponding ordered pair satisfies the
predicate geometrically. It learns Linear and MLP compatibility estimators
without source score or predictor identity, enforces applicable
endpoint/predicate identities through transformation averaging, and combines
compatibility with the source score during family-aware re-ranking. Across
Open3DSG, VL-SAT, and SGFN on the same 3DSSG validation split, both variants
have source-relative Recall point estimates no lower and verifier-derived
Violation point estimates no higher at all five reported cutoffs.

## Strengths

1. **Clear failure mechanism.** The paper distinguishes geometry-aware
   generation from an explicit estimate of same-pair predicate--geometry
   compatibility.
2. **Method/evidence alignment.** Ordered-pair identity, source-score
   exclusion, transformations, and family routing each have direct controls.
3. **Scoped statistical reporting.** Point estimates and paired intervals are
   clearly separated.
4. **Strong defensive supplement.** Simple baselines, score mappings, routing,
   component removals, seeds, oracles, and alternative audit measurements
   address likely reviewer questions.
5. **Reproducibility discipline.** Docker configuration, frozen protocols,
   compact evidence, manifests, and paper regeneration are provided within a
   conservative licensing boundary.

## Residual Major Concerns

### 1. Independent validity evidence

The primary verifier and compatibility construction share some OBB-derived
measurements. The point/mesh audit removes those inputs but still uses the same
reconstructed scenes and ontology. The manuscript correctly limits the claim
to verifier-derived reliability and does not present the audit as independent
ground truth.

### 2. Dataset generalization

The main result uses one 3DSSG validation split. Three predictors improve
cross-model evidence but do not establish cross-dataset generalization. The
ReplicaSSG/FROSS result is appropriately presented as a transfer stress test,
not a universal claim.

### 3. Incremental-method perception

A reviewer may view product scoring and post-hoc re-ranking as simple. The
paper’s novelty therefore depends on the full framework: explicit same-pair
compatibility, information separation, transformation identities,
family-composition preservation, and joint Recall--Violation evaluation.

## Residual Minor Concerns

- Support/contact is evaluated but not corrected.
- Open3DSG has a lower candidate-pool coverage ceiling than VL-SAT and SGFN.
- Product score is not mathematically invariant to arbitrary monotonic source
  mappings, although the fixed stress grid is stable.
- The supplement is dense, but its tables are organized around distinct
  reviewer questions.

## Soundness

The current claims are supported:

- all-\(K\) point-estimate statements match Table 1;
- \(K=50\) interval claims match paired scan-resampling results;
- controls support ordered-pair and predicate dependence;
- transformation and family-preservation properties are both proved and
  checked empirically;
- limitations prevent the audit from being overinterpreted.

## Significance and Novelty

The addressed failure matters when predicted scene graphs are reused for
reasoning, planning, grounding, or alignment. The strongest novelty framing is
not “adding geometry” but exposing and addressing the mismatch between source
relation score and explicit same-pair predicate--geometry compatibility.

## Clarity

The story is readable and consistent. The final terminology should remain:

- validation split for the dataset partition;
- validation scenes for the evaluated scenes;
- source relation score;
- ordered-pair measurements;
- verifier-derived Violation.

## Experimental Rigor

The main and supplement jointly cover:

- three source predictors;
- two estimators;
- matched fusion and routing comparisons;
- structural and component controls;
- paired confidence intervals;
- seed robustness;
- alternative geometry measurements;
- candidate-pool ceilings;
- transfer sensitivity.

This is sufficient for the scoped claim. An independent annotation audit would
be the most valuable future strengthening.

## Reproducibility

Checklist answers are internally consistent. `partial` is correctly retained
for unrestricted dataset availability, exhaustive development search,
third-party experiment code, permanent public code release, and inline
implementation comments.

## Expected Rating

**Weak Accept**, with meaningful Weak Reject risk from novelty and
single-dataset/construct-dependence concerns.

The evidence package is stronger than the initial method description alone
would suggest. Acceptance depends on reviewers accepting the scoped reliability
problem as substantive rather than viewing the method as a narrow re-ranking
heuristic.

## Submission Gate

Scientific content is ready to freeze. Remaining work is procedural:

1. generative-AI role documentation;
2. author metadata and OpenReview field verification.
