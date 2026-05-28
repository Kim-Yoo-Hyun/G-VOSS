# Attachment Deferred Visual Sanity Guide

This queue is for G4b review before any attachment-deferred source metrics.

Allowed labels:

- `policy_correct`: the policy decision matches the visible geometry.
- `policy_too_strict`: a positive relation was marked violated despite visible
  evidence or reasonable annotation semantics.
- `policy_too_permissive`: a counterfactual was marked satisfied despite no
  convincing attachment/connection evidence.
- `counterfactual_seed_invalid`: the generated counterfactual is not a valid
  negative because the replacement object is actually in contact or plausibly
  related.
- `annotation_ambiguous`: the 3DSSG relation wording or object role is too
  ambiguous to use as strict calibration evidence.
- `geometry_evidence_bad`: segmented points, surface normal, object id, or mesh
  evidence is visibly wrong.
- `cannot_judge`: the case cannot be judged from available local artifacts.

Do not use this queue as source metric evidence. It is a pre-metric policy and
calibration-risk review queue.
