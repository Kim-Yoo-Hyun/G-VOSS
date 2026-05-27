# Attachment Deferred Expansion Track

Last updated: 2026-05-28 KST

Status: `attachment_deferred_extractor_contract_ready_no_extraction`

This folder tracks the optional `attachment_deferred` expansion path for H001.
It is not part of the current AAAI main claim. It is the preferred next
relation-family expansion if the paper strategy pivots beyond the current
`support_contact`, `proximity`, and `relative_vertical` scope.

## Motivation

The current H001 denominator has 2,545 in-scope GT rows:

- `support_contact`: 1,199
- `proximity`: 1,128
- `relative_vertical`: 218

The `attachment_deferred` family adds 967 GT rows:

- `attached to`: 808
- `hanging on`: 126
- `connected to`: 33

If validated, the geometry-checkable denominator would expand from 2,545 to
3,512 GT rows. This is a smaller expansion than `relative_horizontal`, but it
fits H001's physical-consistency thesis better because attachment, hanging, and
connection imply contact, near-surface support, orientation, gravity, and object
affordance constraints.

Current source-row availability:

- VL-SAT prediction rows: 77,748
- Open3DSG prediction rows: 57,300

## Completed Scope Audit

Docker `attachment_deferred_scope_audit` completed on 2026-05-28 KST. This is
a no-training, no-inference planning audit, not a verifier and not source-metric
evidence.

Outputs:

- `scope_audit/manifest.json`
- `scope_audit/label_counts.json`
- `scope_audit/evidence_schema.json`
- `scope_audit/report.md`

Result summary:

- status: `attachment_deferred_scope_schema_ready_no_metric_execution`
- current H001 GT denominator: 2,545
- `attachment_deferred` GT rows: 967
- expanded candidate denominator if validated: 3,512 / 7,505
- source candidate rows: VL-SAT 77,748; Open3DSG 57,300
- existing geometry verification status: `unsupported` for both sources
- then-next gate: `G1_attachment_evidence_extractor_design` (now completed)

The scope audit freezes the first evidence-schema plan: reuse OBB
distance/overlap and segmented point evidence where available, add
attachment-specific surface/contact/normal/gravity fields before any verifier,
keep object affordance as optional context rather than proof, and preserve
exact predicate-label recall for `attached to`, `hanging on`, and
`connected to`.

## Completed G1 Extractor Contract

Docker `attachment_deferred_extractor_contract` completed on 2026-05-28 KST.
This is an extractor design and output-contract artifact only. It does not read
point clouds, assign `verification_status`, fit `p_geom_valid`, re-rank
predictions, or run metrics.

Outputs:

- `evidence_extractor/manifest.json`
- `evidence_extractor/extractor_contract.json`
- `evidence_extractor/output_schema.json`
- `evidence_extractor/field_catalog.json`
- `evidence_extractor/subtype_policy.json`
- `evidence_extractor/extraction_plan.json`
- `evidence_extractor/validation_plan.json`
- `evidence_extractor/example_row.json`
- `evidence_extractor/commands.md`
- `evidence_extractor/report.md`

Result summary:

- status: `attachment_deferred_extractor_contract_ready_no_extraction`
- required evidence groups: identity, OBB evidence, local point contact,
  surface candidates/normals, gravity cues, contradictory support cues, and
  affordance context
- forbidden extractor outputs: `verification_status`, `p_geom_valid`, recall
  credit, and reranking scores
- next gate: `G1b_attachment_evidence_extractor_dry_run`

## Why This Is Stronger Than Relative Horizontal

`relative_horizontal` has a larger denominator, but its meaning depends heavily
on coordinate-frame or annotator-viewpoint convention. The current audit found
nontrivial signal but blocked promotion because `front`/`behind` remains
ambiguous.

`attachment_deferred` is smaller but more aligned with the H001 failure
mechanism:

- a relation can be semantically plausible while physically unsupported;
- attachment should usually require object/surface adjacency or contact;
- hanging should respect gravity and near-wall/ceiling support;
- connection should have spatial adjacency and often class/part affordance.

The risk is complexity, not conceptual fit. Attachment requires richer evidence
than support/contact: wall/ceiling/furniture surface type, local point contact,
surface normals, hanging geometry, and object affordance cues.

## Claim Boundary

Allowed now:

- Treat `attachment_deferred` as the preferred next physical-relation expansion
  after the current AAAI path.
- Use it to motivate how H001 could move from pure spatial consistency toward
  simple functional precondition reasoning.
- Record denominator, source-row availability, and required gates.

Blocked now:

- Do not add `attachment_deferred` to the current AAAI main claim.
- Do not claim functional relation reasoning as solved.
- Do not run source metrics until the G1 evidence extractor, verifier policy,
  calibration, controls, GT verifier evaluation, and audit gates are designed
  and frozen.

## Upgrade Steps

G0. Scope audit

- Freeze predicate mapping: `attached to`, `hanging on`, `connected to`.
- Confirm GT denominator, per-label counts, source prediction rows, and covered
  object-pair geometry fields for VL-SAT and Open3DSG.
- Keep exact predicate-label recall; do not collapse labels into a family-level
  recall match.
- Status: completed as Docker no-training/no-inference scope/schema audit.

G1. Attachment evidence extractor contract

- Add surface evidence: floor/wall/ceiling/furniture candidate support surface,
  local surface normal, object-to-surface distance, projected overlap, and local
  point contact.
- Add gravity/orientation evidence for `hanging on`: object above/beside support
  surface, near vertical plane or ceiling, and no contradictory floor-support
  explanation.
- Add adjacency/continuity evidence for `connected to`: very small distance,
  local overlap/contact, and optional class-pair affordance cues.
- Record `uncertain` cases explicitly when mesh/point evidence is missing or the
  relation is likely functional rather than visible physical contact.
- Status: completed as Docker design/contract artifact. No extractor
  implementation, verifier, calibration, or metric run exists yet.

G1b. Extractor dry run

- Implement an evidence-only extractor that emits rows matching
  `evidence_extractor/output_schema.json`.
- Validate row preservation and schema compliance on a small GT/counterfactual
  dry run before any verifier policy.
- Keep `verification_status`, `p_geom_valid`, recall credit, and reranking
  scores out of the extractor output.
- Status: next gate.

G2. Verifier policy

- Define `satisfied`, `violated`, and `uncertain` for each subtype:
  `attached_to_surface`, `hanging_from_surface`, `connected_adjacent`.
- Use conservative violation rules first. For example, mark violated only when
  the object is clearly far from any plausible support/attachment surface or the
  support surface type contradicts the predicate.
- Avoid making class affordance alone a proof of physical validity.

G3. Calibration and counterfactuals

- Build train-dev positives and counterfactual negatives before held-out source
  metrics.
- Suggested negatives: wrong surface, far object pair, shuffled geometry,
  wrong-pair attachment, floor-support replacement for wall-hanging cases, and
  gravity-inconsistent hanging cases.
- Freeze thresholds and calibrator artifacts before held-out metrics.

G4. GT verifier evaluation and visual sanity

- Run GT-positive/counterfactual verifier evaluation.
- Add a targeted visual sanity check for attachment/hanging cases, because
  surface contact can be visually and geometrically subtle.
- Record whether failures are due to annotation noise, missing mesh/points,
  surface-normal errors, or genuinely bad verifier policy.

G5. Source-result metrics

- Run VL-SAT and Open3DSG metrics with `attachment_deferred` included only after
  G0-G4 pass.
- Report `R@K`, `Violation@K`, recall retention, exact-label denominator, and
  per-subtype family rows.
- Compare semantic-only, probabilistic calibrated, rule-verified, family-specific
  calibrated, geometry-only, distance/contact-only, shuffled-geometry, and
  wrong-pair controls.

G6. Function-reasoning pilot

- Optional after relation-level metrics pass.
- Keep it as a small case study unless a separate benchmark is introduced.
- Show simple physical precondition questions such as whether an object is
  plausibly wall-mounted, hanging, or physically connected based on the verified
  relation edge.
- Use this to motivate actionable/function-aware 3D scene graphs, not to claim
  general affordance or robotics task performance.

G7. Promotion gate

- Promote to the main claim only if the family reaches the same evidence level
  as the current H001 families: verifier policy, calibration, GT verifier
  evaluation, two source metrics, controls, bootstrap CI, and failure/audit
  evidence.

## Recommended Paper Strategy

Current AAAI path:

- Keep the main claim scoped to `support_contact`, `proximity`, and
  `relative_vertical`.
- Mention `attachment_deferred` only as the most plausible next physical-relation
  expansion, not as current metric evidence.

If upgrading H001:

1. Add `attachment_deferred` before retrying `relative_horizontal`.
2. Start from the completed scope audit and G1 extractor contract, then
   implement a schema-validated evidence-only dry run before held-out metrics.
3. Run a small GT/counterfactual verifier evaluation after the extractor dry
   run and verifier policy are frozen.
4. Only then run VL-SAT/Open3DSG source metrics and controls.
5. Add function-reasoning only as a secondary pilot after relation reliability
   is established.
