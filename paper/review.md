# GeoCalib Orthogonal Persona Review

Last updated: 2026-06-24 KST

Scope reviewed: current GeoCalib/H001 claim, contribution framing, method
definition, main AAAI manuscript source, compact result tables, bootstrap CI,
paper risk register, and H001_v2 family-conditional risk status.

This is an internal review. It separates observed facts from reviewer-style
inference and assumes the current paper claim remains scoped to
geometry-checkable 3D Scene Graph relation reliability.

## Overall Verdict

Fact:

- The current paper is not framed as a new 3D Scene Graph generator.
- The current claim is a reliability-layer claim for `support_contact`,
  `proximity`, and `relative_vertical`.
- The main paper evidence uses VL-SAT full official validation and Open3DSG
  full-validation `recovery_relaxed_views_min2/`.
- The main metric table reports K = `{5,10,20,50,100}` and keeps K=1 outside
  paper metrics.
- `semantic_score * p_geom_valid` is now presented as the `lambda=1` case of a
  risk-aware soft re-ranking objective.
- `family_conditional_risk` is reported as a family-conditional calibrated risk
  operating point, while legacy metric JSON keys remain unchanged.

Inference:

- The paper is currently viable as a scoped reliability/evaluation-method paper
  if the manuscript keeps the claim narrow and explicit.
- The contribution is defensible when presented as a calibrated
  geometry-consistency evaluation and re-ranking framework with row identity,
  calibration, controls, recall/violation tradeoff, and provenance.
- The paper becomes vulnerable if it claims broad open-vocabulary 3DSSG
  improvement, source-agnostic SOTA, or downstream reasoning improvement.

## Persona 1: Skeptical 3DSSG / CV Reviewer

Primary question: is this more than a post-hoc verifier for a narrow subset of
relations?

Strengths:

- The failure mode is concrete: high semantic confidence can conflict with
  object-pair geometry.
- The paper correctly avoids claiming full 3DSSG generation improvement.
- Using both VL-SAT and Open3DSG helps avoid a single-source reliability story.
- Low-K results are useful because top-ranked relations are the ones most likely
  to be consumed by downstream systems.

Concerns:

- The relation scope is narrow. `support_contact`, `proximity`, and
  `relative_vertical` are defensible, but reviewers may ask why horizontal,
  attachment, functional, or affordance-heavy relations are excluded.
- Open3DSG is a reproduced selected-checkpoint and recovery-policy branch, not a
  clean official benchmark comparison. The manuscript must keep this caveat
  visible.
- `rule_verified` can look like hard filtering rather than a framework if it is
  not clearly described as a diagnostic operating point.
- The method section still needs to make the "why this form is necessary" logic
  stronger than "we add geometry".

Likely review stance:

- Weak accept if scoped as a reliability-layer paper with explicit caveats.
- Weak reject if the paper reads as a broad 3DSSG method or SOTA claim.

Required defense:

- State early that the contribution is not relation generation.
- Tie each chosen relation family to observable physical constraints.
- Put Open3DSG recovery-policy caveats directly in the main table caption and
  experiment setup.
- Keep `relative_horizontal`, `attachment_deferred`, and Qwen-VL as appendix or
  future/extension tracks unless explicitly promoted with the same evidence
  gates.

## Persona 2: ML Calibration / Reliability Reviewer

Primary question: is the scoring method principled, calibrated, and protected
from tuning leakage?

Strengths:

- Recasting `semantic_score * p_geom_valid` as the `lambda=1` case of
  risk-aware soft re-ranking is a strong improvement over describing it as
  simple multiplication.
- The train-dev provenance for `p_geom_valid`, hard-rule thresholds,
  counterfactual construction, and predicate-family mapping is essential and
  should remain prominent.
- GT-positive/counterfactual verifier evidence gives the geometry signal a
  calibration story beyond source-result post-processing.
- `family_conditional_risk` is a principled extension: relation families have
  different geometry-risk surfaces, so a pooled calibrator may be miscalibrated.

Concerns:

- `lambda=1` is defensible as a fixed objective case, but reviewers may still
  ask why not calibrate semantic scores or learn the optimal combination.
- `family_conditional_risk` is strong empirically, especially on Open3DSG, but
  it should be described as an operating point unless the paper explicitly
  promotes it as the main method.
- If family-specific calibration rows are small, the paper should avoid
  implying a broad learned relation-validity model.
- `p_geom_valid > 0.9` residual failure cases must stay visible; otherwise
  calibration claims will look overstated.

Likely review stance:

- Positive if the method is framed as calibrated risk scoring with frozen
  provenance and residual-risk disclosure.
- Negative if it appears tuned on validation source metrics or as an unprincipled
  product score.

Required defense:

- Keep the utility form:
  `U_lambda(i) = log semantic_score_i - lambda * (-log p_geom_valid_i)`.
- Explicitly state that `lambda=1` is not selected from held-out source results.
- Report pooled and family-conditional risk as operating points, not as hidden
  cherry-picked replacements.
- Separate true controls from operating points: geometry-only, distance-only,
  shuffled geometry, and wrong-pair geometry are controls; family-conditional
  risk is not a generic control.

## Persona 3: Experimental Design / Statistics Reviewer

Primary question: do the metrics and comparisons support the claim without
masking recall loss or denominator artifacts?

Strengths:

- Reporting both `R@K` and `Violation@K` directly addresses the recall-filtering
  objection.
- The K grid `{5,10,20,50,100}` is useful because low-K exposes top-rank
  reliability, while K=50/100 preserve continuity with the older locked result.
- The control suite is strong: geometry-only, distance-only, shuffled geometry,
  and wrong-pair geometry test important alternative explanations.
- Bootstrap CI over subgraphs is a reasonable evaluation-context uncertainty
  check.

Concerns:

- Some paper-facing documents still mix historical 127-scan numbers,
  full-validation numbers, and recovery-branch numbers. This is a real
  consistency risk before submission.
- `results/h001_geom_reliability/report.md` still opens with older-looking
  VL-SAT/Open3DSG summary values while later tables and manuscript use the
  full-validation route. This can confuse artifact reviewers.
- Bootstrap CI is currently explained as evaluation-context uncertainty, not
  training variance. That distinction must be preserved.
- Low-K results should not be described as newly discovered post-hoc evidence.
  They should be a frozen diagnostic/reporting grid.

Likely review stance:

- Positive if denominator, K grid, recovery policy, and bootstrap interpretation
  are consistent across manuscript and artifacts.
- Negative if table/prose/report values appear inconsistent or cherry-picked.

Required defense:

- Before final submission, run a consistency pass over `paper/preview.md`,
  `paper/README.md`, `results/h001_geom_reliability/report.md`, and artifact
  bundle docs.
- Use one canonical source-result table for full-validation claims.
- Keep historical 127-scan and R2 results in appendix/sensitivity only.
- Do not claim low-K CI unless low-K bootstrap is explicitly generated and
  reported.

## Persona 4: Reproducibility / Artifact Reviewer

Primary question: can the result be verified, recovered, and understood from the
release without local hidden state?

Strengths:

- Docker-based experiment discipline is a major asset.
- The repository now separates code/configs/results/archive/paper more clearly.
- Artifact bundle inventory, checksums, row counts, and verification script are
  already present.
- The latest artifact bundle verification passed after checksum regeneration.
- AAAI PDF build is reproducible by Docker and currently produces a 9-page US
  Letter PDF with Type 1 fonts.

Concerns:

- Large data, checkpoints, raw dumps, and model caches are intentionally outside
  Git. This is correct, but the paper/release must make restoration steps very
  explicit.
- Open3DSG recovery depends on selected checkpoint provenance and relaxed view
  regeneration. Artifact reviewers may see this as fragile unless the exact
  branch policy is documented.
- Any stale upload bundle or flattened package made before the low-K and
  family-conditional naming pass is invalid.
- Because multiple source routes exist, users may run the wrong one unless the
  README points to the canonical path.

Likely review stance:

- Positive if the release contains exact commands, checksums, row counts, and
  clear "included vs not included" artifact policy.
- Negative if results require guessing which Open3DSG branch or table is the
  selected one.

Required defense:

- Regenerate any final upload archive from the current checkout only.
- Keep `docs/reproducibility.md` as the authoritative recovery runbook.
- Include the latest checksum manifest and verification log in the final bundle.
- In the paper, avoid saying "Open3DSG benchmark result"; say "Open3DSG
  relation-source case study under the reported checkpoint and recovery-policy
  branch."

## Persona 5: Paper Positioning / Top-Tier Novelty Reviewer

Primary question: is the paper's contribution crisp enough for a top-tier AI,
CV, ML, or robotics venue?

Strengths:

- The paper has a clear reliability failure mechanism, not just a motivation:
  semantic confidence is not calibrated to relation-level physical consistency.
- The contribution stack is coherent: row standardization, identity-preserving
  geometry join, calibrated geometry validity, operating points, recall/violation
  evaluation, and controls.
- The title `GeoCalib` is appropriate and avoids internal H001 naming.
- The paper's strongest sentence is the scoped claim that calibrated
  geometry-consistency scoring exposes and reduces physically inconsistent
  relation predictions while preserving recall tradeoffs.

Concerns:

- The method can still read procedural if the manuscript over-describes scripts
  and under-emphasizes the failure mechanism and design necessity.
- The strongest empirical row may be `family_conditional_risk`, while the paper
  still says the current main route remains pooled `probabilistic_recalibrated`
  unless explicitly promoted. The manuscript should not leave readers unsure
  which operating point is the method's default.
- Qwen-VL, H002, attachment, and lateral tracks are useful research context but
  can dilute the paper if they appear in the main story.
- Figure 1 and Figure 2 must visually communicate the contribution; if they look
  like a processing pipeline only, novelty may seem weaker.

Likely review stance:

- Positive if the paper sells a falsifiable reliability framework and keeps
  extensions out of the main claim.
- Negative if the paper tries to be method, benchmark, source reproduction,
  open-vocabulary result, and VLM extension all at once.

Required defense:

- Keep the three contributions short and specific.
- In the abstract and introduction, say "calibrated geometry-consistency
  evaluation and re-ranking framework" rather than "geometry verifier".
- Put `family_conditional_risk` in the paper as a named operating point, but
  explicitly state whether it is reported as an additional operating point or as
  the promoted main score.
- Avoid adding more experiments unless they close a specific reviewer attack.

## Cross-Persona Consensus

Strongest current claim:

```text
For geometry-checkable 3D Scene Graph relation families, GeoCalib shows that
semantic relation confidence is not reliably calibrated to object-pair physical
consistency, and that calibrated geometry-risk re-ranking can reduce top-K
geometric violations under explicit recall tradeoffs across VL-SAT and Open3DSG.
```

Current contribution strength:

- Clear failure mechanism.
- Practical framework with identity-preserving row contract.
- Calibrated geometry validity rather than only hard rules.
- Recall/violation metric pair.
- Cross-source evidence with explicit caveats.
- Nontriviality controls and GT/counterfactual verifier checks.

Main residual risks:

- Narrow relation scope.
- Open3DSG selected-checkpoint and recovery-policy caveats.
- Potential reading as rule-based post-processing.
- Stale/inconsistent planning documents and compact result summaries.
- Ambiguity over whether `family_conditional_risk` is only an operating point or
  the promoted main method.
- Release/package correctness.

## Recommended Priority

P0 before submission:

- Make all current paper-facing docs agree on the latest build log and selected
  full-validation route.
- Fix or clearly annotate stale `results/h001_geom_reliability/report.md` fields
  that still reflect historical values.
- Decide one final wording for the default method:
  `probabilistic_recalibrated` as default with `family_conditional_risk` as an
  additional operating point, or explicitly promote family-conditional risk.
- Regenerate the final flattened/upload package only after this decision.

P1 before submission:

- Add a short limitations paragraph explaining why horizontal, attachment, and
  functional relations are not in the main scope.
- Ensure Figure 1 states failure cause and design necessity, not just pipeline
  steps.
- Keep low-K as top-rank reliability diagnostic and avoid implying K was chosen
  after seeing results.

P2 optional:

- Add a small appendix table separating operating points from true controls.
- Include Qwen-VL only as an appendix/extension paragraph unless promoted with
  the full evidence gates.
- Do not run more H001_v2 experiments unless they change the default-method
  decision.

## Final Recommendation

Proceed with the current scoped GeoCalib paper, but tighten consistency and
method-default wording before submission. The paper's best defense is not more
experiments; it is disciplined framing: calibrated geometry-consistency
reliability for measured 3DSSG relation families, explicit recall/violation
tradeoffs, and transparent caveats.
