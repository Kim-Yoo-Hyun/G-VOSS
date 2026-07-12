# Human Physical-Validity Annotation Guide

Addendum frozen at UTC: `2026-07-12T04:03:46Z`  
Applies to protocol: `h001_physical_validity_audit_v1`

This addendum clarifies annotation fields before any independent human label is
collected. It does not change the 488-item sample, evidence, label ontology,
relation-family scope, score definitions, or estimands.

## Allowed evidence and blinding

Each first-pass annotator may read `protocol.md`, exactly one of
`annotator_a.csv` or `annotator_b.csv`, and the evidence paths in that sheet.
Inspect the geometry projection and colored pair PLY for every row; use the RGB
pair crop only when its path is nonempty. Subject points are red and object
points are blue.

Do not inspect the other annotator sheet, `private_sidecar.jsonl`, Codex labels,
source predictions, scores, ranks, verifier outputs, sampling strata, GT
membership, result tables, or evaluation outputs before both first-pass sheets
are locked.

## Label definitions

- `physically_valid`: visible geometry supports the stated directed relation.
- `physically_invalid`: visible geometry contradicts the stated relation.
- `ambiguous`: evidence is present, but the relation remains physically
  indeterminate or semantically underspecified.
- `unobservable`: reconstruction, segmentation, crop, or occlusion prevents a
  defensible physical judgment.

Use object-pair geometry rather than category plausibility. For support/contact,
judge direct contact and support configuration; for proximity, judge distance
relative to object extent and scene context; for vertical relations, judge the
directed vertical ordering.

## Confidence

- `high`: the label is directly supported by multiple consistent geometric
  cues and is unlikely to change under another view of the same evidence.
- `medium`: the label is defensible, but one cue is noisy, partial, or near a
  relation boundary; the overall conclusion is still stable.
- `low`: the label is tentative and could change under another reasonable
  interpretation of the available evidence. Every low-confidence row is
  adjudicated even when the two first-pass labels agree.

Confidence expresses certainty in the selected four-class label, including an
`ambiguous` or `unobservable` decision; it is not source-model confidence.

## Evidence sufficiency

Enter lowercase `true` when the available evidence is sufficient to defend the
selected `physically_valid`, `physically_invalid`, or `ambiguous` label. Enter
lowercase `false` only when the evidence itself is inadequate, and then use
`unobservable`. Thus `unobservable` and `evidence_sufficient=false` must occur
together; `ambiguous` means that evidence exists but the physical
interpretation is indeterminate.

## Primary reason codes

Use exactly one code:

- `geometry_supports_relation`: the visible geometry supports a valid label.
- `contact_or_support_missing`: required contact/support geometry is absent or
  contradicted.
- `distance_inconsistent`: pair distance is incompatible with the predicate.
- `vertical_order_inconsistent`: directed vertical order is contradicted.
- `predicate_semantically_underspecified`: visible evidence permits multiple
  physically reasonable interpretations of the predicate.
- `segmentation_or_reconstruction_issue`: geometry is missing, fused, broken,
  or assigned to the wrong instance.
- `occlusion_or_insufficient_evidence`: the relevant configuration cannot be
  observed reliably.
- `other`: none of the above; a nonempty explanation in `notes` is required.

Use `geometry_supports_relation` for `physically_valid`. Use a contradiction
code or explained `other` for `physically_invalid`. Use
`predicate_semantically_underspecified` or explained `other` for `ambiguous`.
Use one of the two evidence-failure codes for `unobservable`.

## Required fields and provenance

Fill all 488 rows in the assigned shuffled order. Do not edit immutable columns,
delete rows, add rows, or reorder the sheet. Required fields are
`physical_validity_label`, `confidence`, `primary_reason_code`,
`evidence_sufficient`, `reviewer_id`, and ISO-8601 `reviewed_at`; `notes` is
optional except where required above. One non-proxy pseudonymous reviewer ID
must be used throughout each sheet, and annotator A and B must use different
IDs.

## Adjudication

After both first-pass sheets are locked, a third distinct human receives only
the required adjudication queue and its public evidence. A row requires
adjudication if the first-pass labels disagree, either confidence is `low`, or
either label is `ambiguous` or `unobservable`. The adjudicator records both
first-pass labels, one final four-class label, a reason, a distinct non-proxy
ID, and an ISO-8601 timestamp. Non-required rows must remain unadjudicated.

