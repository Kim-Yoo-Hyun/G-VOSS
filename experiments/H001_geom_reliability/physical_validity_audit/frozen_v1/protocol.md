# Independent Physical-Validity Audit Protocol

Frozen at UTC: `2026-07-10T06:18:49.518091+00:00`  
Protocol status: `frozen_awaiting_independent_human_labels`  
Protocol version: `h001_physical_validity_audit_v1`

## Estimand and scope

The primary estimand is design-weighted human `Violation@K` for
`semantic_only` and `family_conditional_risk` at K = `{5,10,20,50,100}`,
reported overall and by `support_contact`, `proximity`, and
`relative_vertical`. The audit covers both global in-scope ranking and
within-family ranking. `ambiguous` and `unobservable` are never silently counted
as valid; they are excluded from the binary denominator and reported as audit
coverage.

## Blinding and evidence

Annotators see only relation text, an RGB pair crop when available, raw
orthographic point projections, and a colored pair PLY (subject red, object
blue). RGB availability is reported as evidence coverage but is not an
eligibility rule because the raw 3D pair evidence is complete. Public sheets
exclude source identity, semantic score, geometry score, all ranks, verifier
status, GT membership, sampling stratum, and current method condition. The
private sidecar must not be opened by annotators before both sheets are locked.

## Labels

- `physically_valid`: the stated directed relation is supported by the visible
  reconstructed geometry and RGB evidence.
- `physically_invalid`: the evidence contradicts the stated relation.
- `ambiguous`: evidence is available but the physical interpretation is not
  sufficiently determinate.
- `unobservable`: reconstruction, segmentation, crop, or occlusion prevents a
  defensible judgment.

For `standing on`/`lying on`/`supported by`, judge direct contact and support
configuration, not object-category plausibility. For `close by`, judge pairwise
distance relative to object extent and scene context. For `higher than` and
`lower than`, judge the directed vertical ordering of the instances.

## Annotation and adjudication

Two independent annotators complete `annotator_a.csv` and `annotator_b.csv` in
their separately shuffled order. They must not discuss rows during first pass.
Agreement is reported before adjudication. All disagreements, and any row with
low confidence, `ambiguous`, or `unobservable`, enter a blinded adjudication
pass. The adjudicated label is the primary analysis; single-rater results may
only be described as preliminary.

## Sampling and inference

Candidates are the union of top-100 predictions under both conditions. Fixed
strata cross source, ranking context, predicate family, condition-membership
signature, and rank band. Each nonempty stratum contributes up to
`4` hash-randomized rows. Duplicate
physical relation items are labeled once. The private sidecar records each
item's union inclusion probability and Horvitz--Thompson design weight. CIs are
cluster-bootstrap intervals over subgraphs/scans with design weights retained.
Raw semantic calibration is reported with weighted Brier, AUROC, AUPRC, ECE,
and reliability bins. A monotone Platt map is fit and evaluated by five-fold
cross-fitting with complete scan groups held out; no row is scored by a map fit
using labels from the same scan.

## Frozen exclusions

No score tuning, threshold selection, family removal, K removal, label collapse,
or audit-row replacement is allowed after either annotator begins. Missing or
corrupt evidence remains in the accounting and is labeled `unobservable`; it is
not replaced post hoc.
