# RelCompat3D Reviewer-Risk Register

Last updated: 2026-07-28 KST

## Risk Summary

| Risk | Severity | Current treatment |
| --- | --- | --- |
| Construct dependence | High | Scoped claim, dependency matrix, feature removals, point/mesh audit |
| Single validation split | High | Explicit limitation and transfer stress test |
| Incremental/simple-method perception | High | Mechanism framing and matched baselines/controls |
| Support/contact not re-ranked | Medium | Explicit scope and preserved-order guarantee |
| Candidate-pool ceiling | Medium | Candidate coverage and Recall oracle |
| Source-score scale sensitivity | Medium | Pre-specified mapping stress test |
| Dense supplement | Low | Main self-contained, full rows moved to artifacts |
| Source/PDF synchronization | Closed | Final 9/10/2-page build and release are synchronized |
| Generative-AI documentation | Submission-critical | Author action required |

## R1. Construct Dependence

### Risk

Compatibility construction and the primary verifier share some OBB-derived
measurements. A reviewer may argue that lower Violation is partly aligned with
the evaluation construct.

### Current Defense

- Evaluation rows and verifier labels do not enter training construction.
- Source score and predictor identity are excluded from compatibility.
- Feature-removal analyses separate exact, related, and alternative evidence.
- Point/mesh audit excludes OBB inputs and primary labels.
- Uncertainty-policy variants preserve the source-relative direction.
- Discussion states that the audit is not independent ground truth.

### Remaining Boundary

Only an independently defined human or external reference label would support
a broader physical-validity claim. The paper does not make that claim.

## R2. Single 3DSSG Validation Split

### Risk

Three predictors on the same split provide cross-predictor evidence but not
dataset-level generalization.

### Current Defense

- Introduction identifies the official 3DSSG validation split.
- Discussion explicitly limits the interpretation.
- ReplicaSSG/FROSS is reported only as a transfer stress test.

### Required Wording

Use **validation split** for the partition and **validation scenes** for the
evaluated scenes. Avoid treating `shared` as evidence of cross-dataset
generality.

## R3. Support/Contact Scope

### Risk

The method evaluates support/contact but leaves it in source order.

### Current Defense

- richer contact and pose evidence is required;
- no single endpoint swap preserves every predicate in the family;
- the ranking rule exactly preserves the support/contact subsequence;
- Product (all families) demonstrates the effect of changing this scope.

This is a stated design boundary, not a hidden failure.

## R4. Novelty Ceiling

### Risk

Product scoring and re-ranking may appear incremental.

### Current Defense

The contribution is the relation-consistent reliability framework:

- explicit same-pair compatibility task;
- source-score exclusion;
- ordered-pair identity;
- counterfactual construction;
- exact transformation averaging;
- family-composition preservation;
- joint Recall--Violation evaluation.

Simple robust-density, rank-fusion, component-removal, and routing controls
show that the contribution is not only one fusion formula.

## R5. Comparator Trade-offs

### Risk

No method dominates every metric, predictor, and cutoff.

### Current Defense

The paper reports the trade-offs rather than claiming SOTA. Product is a scope
comparison. Bold values in Table 1 are restricted to comparable
composition-preserving methods.

## R6. Open3DSG Coverage

### Risk

Open3DSG candidate-pool coverage is 79.68%, below the 99.72% of VL-SAT and
SGFN.

### Current Defense

The supplement reports family-aware, family-count, and unconstrained Recall
oracles. The paper claims re-ranking of fixed candidates and never claims to
recover missing relations.

## R7. Source-Score Scale

### Risk

The product utility is not invariant to arbitrary monotonic rescaling.

### Current Defense

Five fixed smooth non-identity mappings preserve the source-relative conclusion
for all Linear cases and all but one MLP comparison. Percentile stress reveals
small Recall sensitivity without increased Violation. The manuscript avoids
the term `scale-invariant`.

## R8. Reproducibility and Licensing

### Risk

Full regeneration needs licensed data, third-party predictors, checkpoints,
and row-level inputs.

### Current Defense

The archive includes executable RelCompat3D code, Docker configuration, frozen
protocols, model locks, compact outputs, schemas, exporters, and manifests.
Licensed raw data, stable source identifiers, and source-derived row bundles
are conservatively excluded.

Checklist answers remain `partial` where this boundary prevents an
unrestricted all-in-one release.

## R9. Submission Synchronization

### Risk

Uploading PDFs or ZIPs built before the latest section edits would create a
source/artifact mismatch.

### Current State

Closed. The latest Introduction, Discussion, and Conclusion wording is present
in the 9/10/2-page canonical PDFs and current release. Outer and inner
manifests, extracted-source builds, text hashes, fonts, anonymity, and page
boundaries pass.

## R10. Policy and Metadata

### Remaining Author Actions

- document the actual generative-AI role according to AAAI policy;
- enter and verify author list, order, affiliations, profiles, and conflicts;
- confirm title, abstract, TL;DR, topics, and reciprocal-review requirements;
- upload before the deadline and verify every file in OpenReview.

## Reporting Invariants

Always preserve:

- `point estimates` for the all-\(K\) claim;
- `verifier-derived Violation`;
- `same 3DSSG validation split`;
- `shared 3DSSG validation scenes`;
- `fixed relation predictions`;
- `support/contact candidates retain source order`;
- `alternative geometric measurement`, not independent ground truth.

## Current Recommendation

Freeze scientific content. Do not add new experiments or broaden claims at
submission time. Only the policy and submission-metadata gates remain.
