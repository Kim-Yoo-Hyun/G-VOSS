# Paper Workflow

Last updated: 2026-05-14

This document manages paper-level framing for H001/CAND-001: novelty, contribution boundary, reviewer-defense logic, and the minimum experiment evidence needed before paper writing. It does not replace `docs/hypothesis.md`, `07_experiment_spec.md`, or Docker experiment artifacts.

## Source Note

- Checked on: 2026-05-14
- Reference: [Motivation is not Novelty](https://gisbi-kim.github.io/motivation-is-not-novelty/)
- Usage: paper-framing heuristic, not scientific evidence about 3D Scene Graphs.

## Novelty Rule

Fact from the reference:

- Motivation is not novelty. "Existing methods fail under X, so we add module Y" is still a motivation-level argument unless the paper explains why the failure happens and why Y must take its proposed form.
- A top-tier pattern is: define a concrete failure mode, explain the underlying cause, derive the method from that cause, then verify the design through ablation, controls, generality checks, and failure analysis.
- Strong novelty is not merely a new component, combination, dataset use, or larger experiment. It is the insight that turns an observed failure into a necessary method design.

H001 rule:

- Do not claim novelty as "we add geometry", "we combine semantic and geometry", "we use a VLM", or "we implement a verifier".
- Claim novelty as a calibrated geometry-consistency evaluation/re-ranking framework that targets a specific failure: semantically plausible 3D relation predictions can be physically inconsistent because semantic confidence is not calibrated to relation-level geometry.

## Current One-Liner

Draft:

> Semantic relation predictors can rank plausible 3D Scene Graph relations without calibrating them to relation-level physical consistency; calibrated geometry-consistency scoring exposes this failure mode and re-ranks predictions to reduce geometric violations while making recall tradeoffs measurable.

This is the preferred direction because it contains both cause diagnosis and method principle. The wording should still be tightened after Open3DSG second-source metrics are available.

## H001 Fit To Top-Tier Pattern

Facts:

- H001 already has a concrete failure target: geometry-checkable relation families such as `support_contact`, `proximity`, and `relative_vertical`.
- Hypothesis-stage `VL-SAT` evidence includes semantic-only vs calibrated geometry variants, family-specific controls, evidence lock, GT-based verifier evaluation, and a reduced visual sanity check.
- The Open3DSG path is in progress as second-source evidence. Full Open3DSG metrics, checkpoint provenance, raw-dump identity checks, and failure-analysis tables are not complete yet.
- Qwen-VL is currently an optional modern semantic-source extension, not the main baseline replacement.

Inference:

- The direction is aligned with the top-tier pattern if the paper is framed around failure mechanism plus calibrated geometry-consistency, not around a verifier script.
- The current evidence is stronger than a motivation-only project because it already has scoped metrics, controls, and audit artifacts.
- The top-tier risk remains real until second-source Open3DSG results and failure taxonomy are completed. Without them, the paper may be attacked as a single-baseline reliability tool rather than a general 3DSSG contribution.

User judgment needed:

- Whether to keep the final paper claim as a scoped reliability layer or push for broader open-vocabulary 3DSSG improvement depends on Open3DSG metric quality and failure-analysis strength.

## Reviewer Attack Surface

Likely reviewer questions:

- Is this just a hand-coded geometry verifier?
- Does geometry re-ranking improve relation prediction or only filter easy cases?
- Are gains caused by a narrow subset of relation labels?
- Does the method preserve useful recall, or does it trade recall for fewer violations?
- Does the result generalize beyond `VL-SAT` and one closed-set prediction source?
- Are the geometry rules calibrated, or manually chosen after looking at the test set?
- Are skipped Open3DSG train/eval samples changing the denominator in a way that favors H001?
- Does Qwen-VL add scientific evidence, or only a modern engineering option?

Required defense:

- Present the method as a calibrated framework with explicit design choices, not as a script.
- Include semantic-only, rule-only, calibrated, and family-specific variants.
- Include wrong-pair or shuffled-geometry controls to show the geometry signal is not accidental.
- Report recall and violation metrics together.
- Keep denominator and filtered-split caveats visible in every table using Open3DSG.
- Use Open3DSG as second-source evidence before broad claims.
- Treat Qwen-VL as optional semantic-source extension unless it receives the same Docker, metric, and audit treatment.

## Main Paper Evidence Checklist

Minimum table/figure set before paper writing:

- Table 1: dataset/split/scope and denominator audit.
- Table 2: semantic-only vs rule-only vs calibrated geometry-consistency re-ranking.
- Table 3: family-specific results for `support_contact`, `proximity`, and `relative_vertical`.
- Table 4: calibration and threshold ablations.
- Table 5: control experiments such as wrong-pair and shuffled-geometry.
- Table 6: Open3DSG second-source metrics with exact scope and blocked/filtered sample accounting.
- Figure 1: failure mechanism and framework overview.
- Figure 2: qualitative failure taxonomy with examples where semantic plausibility and physical consistency diverge.

## Non-Claims

Do not claim these until evidence exists:

- Broad SOTA improvement for open-vocabulary 3DSSG.
- Baseline-agnostic improvement across arbitrary relation predictors.
- Qwen-VL as a replacement main baseline.
- Geometry rules as universally correct relation semantics.
- Full Open3DSG reproducibility until checkpoint, feature dump, metric join, and raw identity checks pass.

## Next Paper-Framing Step

After Open3DSG feature dump and training/metric transition finish, update this document with:

- The final H001 one-liner.
- The exact Open3DSG second-source table status.
- Which reviewer attacks are resolved by evidence and which remain as limitations.
- Whether the paper should target a scoped reliability-layer claim or a broader open-vocabulary 3DSSG improvement claim.
