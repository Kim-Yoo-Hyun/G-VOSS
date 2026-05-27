# Attachment Deferred Evidence Extractor Contract

Status: `attachment_deferred_extractor_contract_ready_no_extraction`
Created at: `2026-05-27T16:14:41+00:00`

## Claim Boundary

This is a G1 design artifact, not a verifier and not metric evidence. It keeps
`attachment_deferred` outside the current AAAI main claim.

## Contract Files

- `extractor_contract.json`
- `output_schema.json`
- `field_catalog.json`
- `subtype_policy.json`
- `extraction_plan.json`
- `validation_plan.json`
- `example_row.json`
- `commands.md`

## Required Evidence Groups

- identity-preserving source row fields
- reusable OBB distance/overlap/vertical evidence
- local point contact and contact patch proxies
- surface candidate type and surface normal class
- gravity/hanging cues
- contradictory floor/table support cues
- object-class affordance as context only, never as proof

## Explicit Non-Outputs

The extractor must not emit `verification_status`, `p_geom_valid`, recall
credit, or reranking scores. Those belong to later verifier, calibration, and
metric gates.

## Next Gate

`G1b_attachment_evidence_extractor_dry_run`

## Blockers Before Source Metrics

- `extractor_implementation_not_written`
- `point_contact_estimator_not_validated`
- `surface_candidate_estimator_not_validated`
- `normal_classification_not_validated`
- `gravity_and_contradictory_support_cues_not_validated`
- `schema_validation_dry_run_not_executed`
- `attachment_verifier_policy_not_frozen`
- `train_dev_calibration_not_built`
- `source_metrics_not_run`
