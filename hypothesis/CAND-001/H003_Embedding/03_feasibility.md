# H003 Feasibility And Risk

Last updated: 2026-06-18 KST

## Feasibility Verdict

H003 is feasible as a hypothesis-stage prototype, but not yet ready as a paper-facing method claim.

The idea has stronger method novelty than explicit threshold rules, but only if the learned embedding demonstrates behavior that rules alone do not explain:

- transfer across relation sources.
- robustness on hard counterfactuals.
- calibrated validity probability.
- reduced shortcut reliance.
- useful recall/violation tradeoff.

If the embedding only distills explicit geometry rules, the contribution is weak.

## Main Risks

### Rule Distillation Risk

If most labels come from deterministic geometry rules, reviewers can argue that the model is only learning a softer copy of the rule.

Required mitigation:

- include explicit rule score as a baseline.
- report where learned embedding improves over rules.
- emphasize hard negatives and transfer, not only average validity classification.

### False Negative Risk

3DSSG annotations are sparse. Missing GT does not mean the relation is invalid.

Required mitigation:

- do not use unannotated pairs as default negatives.
- prefer counterfactual negatives derived from confirmed positives.
- record label provenance.
- separate `unknown` from `negative`.

### Shortcut Risk

The model may learn object-class priors such as `floor -> support` instead of relation-level compatibility.

Required mitigation:

- semantic-only baseline.
- geometry-only baseline.
- same object-class / different geometry contrast.
- same geometry / different predicate contrast.
- rank-matched controls if source score is included.

### Easy Negative Risk

Shuffled or impossible negatives can make the task too easy.

Required mitigation:

- include hard negatives within the same predicate family.
- include same-scene wrong-pair negatives.
- include near-threshold geometry cases.
- evaluate separately on easy and hard negatives.

### Scope Creep Risk

Adding raw point cloud, multi-view crops, VLM scoring, and relation generation at once turns H003 into a new 3DSSG predictor.

Required mitigation:

- first prototype uses compact geometry features.
- no raw point-cloud encoder in the first gate.
- no multi-view image encoder in the first gate.
- no claim of relation generation improvement.

## Minimum Prototype Design

The first feasible prototype should be small:

```text
Input:
  predicate family
  predicate label/text
  subject class
  object class
  compact object-pair geometry features
  source score/rank

Target:
  consistency_valid / consistency_invalid / unknown

Model:
  small MLP or two-tower embedding

Objective:
  binary consistency classification + margin ranking
```

No Docker experiment root is needed until this passes the hypothesis promotion gate.

## Candidate Relation Families

Start with the families that already have interpretable geometry:

- `support_contact`
- `relative_vertical`
- `proximity`

Potential second stage:

- `attached to`
- `hanging on`
- `connected to`

Reason:

- attachment/contact-style relations are better for visual-geometric witness evidence.
- proximity can be dense and less informative, so it is useful for stress testing but weak as the only family.

## Evidence Needed Before Implementation

Before writing model code, decide:

- exact row schema.
- exact positive label provenance.
- exact negative corruption set.
- split policy.
- hard-negative definition.
- baseline set.
- metric set.
- whether H003 uses only existing compact summaries or requires new data extraction.

## Recommendation

Proceed with H003 as a separate hypothesis branch from H001.

Do not merge it into GeoCalib unless the embedding clearly beats explicit rule scoring under hard-negative and transfer controls. The most defensible framing is:

> learned semantic-geometry compatibility for relation reliability, evaluated against explicit geometry verification as a strong diagnostic baseline.

