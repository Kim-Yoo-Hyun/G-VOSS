# RelCompat3D Reviewer Assessment and Risk Register

Last updated: 2026-07-29 KST

This document combines the reviewer-style assessment and the remaining
scientific, reproducibility, and submission risks. Detailed manuscript editing
history remains in `user_feedback.md`.

## 1. Reviewer Summary

RelCompat3D addresses fixed 3D scene graph relations whose source scores do not
explicitly estimate whether the corresponding ordered pair satisfies the
predicate geometrically. It learns Linear and MLP compatibility estimators
without the source relation score or predictor identity, enforces applicable
endpoint/predicate identities through transformation averaging, and combines
compatibility with the source score during family-aware re-ranking. Across
Open3DSG, VL-SAT, and SGFN on the same 3DSSG validation split, both variants
have Recall point estimates no lower and verifier-derived Violation point
estimates no higher than Source at all five reported cutoffs.

## 2. Strengths

1. **Clear failure mechanism:** geometry-aware prediction is distinguished
   from an explicit estimate of same-pair predicate--geometry compatibility.
2. **Method/evidence alignment:** source-score exclusion, ordered-pair
   association, transformation averaging, and family routing have direct
   controls.
3. **Scoped statistical reporting:** all-\(K\) point estimates and paired
   interval claims are kept distinct.
4. **Defensive evidence:** simple baselines, score mappings, routing controls,
   component removals, seed analysis, oracles, and alternative measurements
   address likely reviewer questions.
5. **Reproducibility discipline:** Docker configuration, frozen protocols,
   compact evidence, manifests, and paper regeneration are available within a
   conservative licensing boundary.

## 3. Consolidated Risks and Defenses

| Risk | Severity | Current defense and boundary |
| --- | --- | --- |
| Construct dependence | High | Evaluation labels do not enter training, feature removals separate shared primitives, and the point/mesh audit excludes OBB inputs and primary labels. The audit still uses the same scenes and ontology, so the paper does not claim independent physical-validity ground truth. |
| One validation split | High | Three predictors provide cross-predictor evidence and ReplicaSSG/FROSS is a transfer stress test. The paper explicitly does not claim dataset-level generalization. |
| Incremental-method perception | High | The contribution is framed as the full reliability framework: same-pair compatibility, input separation, counterfactual learning, exact transformation averaging, family-composition preservation, and joint Recall--Violation evaluation. |
| Support/contact scope | Medium | Support/contact is evaluated but retains source order because richer contact and pose evidence is required and no single endpoint transformation preserves all predicates. Product (all families) is a scope comparison. |
| Comparator trade-offs | Medium | No universal SOTA claim is made. Table 1 reports Recall--Violation trade-offs and restricts bold values to comparable composition-preserving rows. |
| Open3DSG candidate ceiling | Medium | Candidate-pool coverage and three Recall oracles quantify missing candidates. RelCompat3D is presented only as fixed-pool re-ranking. |
| Source-score scaling | Medium | A fixed smooth mapping grid is stable in all Linear and all but one MLP setting. Percentile stress exposes small Recall sensitivity, so the paper avoids `scale-invariant`. |
| Reproducibility and licensing | Medium | The archive contains RelCompat3D code, Docker files, protocols, compact outputs, schemas, exporters, and manifests. Licensed data, stable identifiers, row bundles, and third-party checkpoints are excluded. Checklist answers remain `partial` where required. |
| Dense supplement | Low | The main paper is self-contained and each supplementary table addresses a distinct reviewer question. Full grids are kept machine-readable. |
| Source/PDF synchronization | Procedural | Closed after every clean build by page, font, warning, hash, manifest, anonymity, and extracted-source checks. |
| Generative-AI documentation | Submission-critical | The authors must document the actual role of generative AI according to AAAI policy. |

## 4. Soundness

The scoped claims are supported:

- all-\(K\) point-estimate statements match Table 1;
- \(K=50\) interval statements match paired scan-resampling results;
- controls support dependence on the predicate and corresponding ordered-pair
  measurements;
- transformation and family-preservation properties are proved and checked;
- limitations prevent the primary verifier and point/mesh audit from being
  overinterpreted.

## 5. Significance and Novelty

The failure matters when relation rankings are reused for reasoning, planning,
grounding, or alignment. The strongest framing is not “adding geometry.” It is
the mismatch between a source relation score and an explicit estimate of
same-pair predicate--geometry compatibility, together with a constrained
reliability layer that can be applied to fixed predictors.

The main reject risk is that a reviewer may still view product scoring and
post-hoc re-ranking as incremental. The complete control package and the
predictor-dependent source-score analysis are therefore central to the novelty
argument.

## 6. Clarity and Reporting Invariants

Use consistently:

- `validation split` for the dataset partition;
- `validation scenes` for the evaluated scenes;
- `source relation score`;
- `ordered-pair measurements`;
- `fixed relation predictions`;
- `family-aware re-ranking`;
- `verifier-derived Violation`;
- `point estimates` for the all-\(K\) source-relative result;
- `alternative geometric measurements`, not independent ground truth.

## 7. Experimental Rigor

The main and supplement jointly cover three source predictors, two estimators,
matched fusion and routing comparisons, structural and component controls,
paired intervals, seed robustness, alternative geometry measurements,
candidate-pool ceilings, uncertainty policies, and transfer sensitivity. This
is sufficient for the scoped claim. Independently annotated validity labels
and additional datasets would be the strongest future extensions.

## 8. Reproducibility

Checklist answers are internally consistent. `partial` is retained for
unrestricted dataset availability, exhaustive development search, complete
third-party experiment code, permanent public release, and inline
implementation comments.

## 9. Expected Rating

**Weak Accept**, with meaningful Weak Reject risk from novelty and the
single-dataset/construct-dependence concerns.

The evidence package is stronger than the method description alone. Acceptance
depends on reviewers recognizing scoped geometric reliability as a substantive
problem rather than treating RelCompat3D as only a narrow re-ranking heuristic.

## 10. Remaining Author Actions

1. document the actual generative-AI role;
2. verify author order, affiliations, profiles, conflicts, topics, title,
   abstract, and TL;DR in the submission system;
3. upload the canonical main, supplement, checklist, and code/data archive;
4. reopen every uploaded artifact and verify filenames, anonymity, and page
   boundaries.
