# Attachment Subtype Redesign v2

Status: `attachment_subtype_v2_frozen_no_refit_no_source_metrics`

## Outcome

The legacy nine-subtype design is replaced by three independent axes:
predicate semantics, physical mechanism, and observability/applicability.
Ambiguous, occluded, and functional cases are no longer physical subtypes or
automatic calibration targets.

This stage migrates and audits the existing artifacts only. It fits no model,
changes no source ranking, computes no new source metric, and does not expand
the RelCompat3D main claim.

## Audit

- migrated train/dev rows: 761
- legacy strict rows: 325
- legacy strict rows with an `ambiguous_*` subtype: 199
- v2 candidate strict-calibration rows before mechanism review: 311
- rows requiring mechanism review: 62
- official-validation evidence rows audited: 190722
- official-validation bidirectional-compatibility coverage: 74433
- official-validation positive-only coverage: 19287
- official-validation abstained rows: 97002

## Frozen Boundary

`attached to` and `hanging on` receive mechanism-specific direct-geometry
routes. `connected to` receives positive-only direct-contact evidence until the
dataset ontology distinguishes direct from mediated connections. Unresolved or
insufficient rows abstain and use a neutral compatibility factor rather than
being treated as violations.

No blanket endpoint swap is permitted. Attached-to and hanging-on are
directional; connected-to swap invariance is allowed only after an independent
ontology audit confirms symmetry.

## Next Gate

Complete the frozen mechanism/observability review queue, rebuild calibration
targets without legacy ambiguous-policy labels, verify nonempty train and
internal-dev support for every promoted mechanism, and only then freeze/refit a
v2 compatibility model. Source metrics remain blocked until that model hash and
its controls are frozen.
