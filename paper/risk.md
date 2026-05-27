# H001 Paper Reviewer-Risk Register

Last updated: 2026-05-28 KST

Scope: this file tracks paper-body risks for the current AAAI manuscript under
`paper/aaai/`. The goal is not sentence polish; it is to prevent reviewer attacks
on logic, evidence, novelty, scope, and reproducibility.

## Current Verdict

The paper direction is viable as a scoped relation-reliability paper, not as a
broad open-vocabulary 3DSSG generation paper. The strongest contribution remains:

> Existing 3DSSG relation sources can assign high semantic confidence to
> physically inconsistent relation edges; H001 contributes a calibrated
> geometry-consistency evaluation and re-ranking framework that makes this
> failure measurable, reduces violations under explicit recall tradeoffs, and
> reports controls, GT/counterfactual verifier checks, and failure analysis.

The main rejection risks are not that the topic is unimportant. They are:

- the method could be read as a hand-coded verifier/post-processing script;
- Open3DSG is the main source but uses a reproduced averaged-BLIP variant with
  filtered coverage;
- the measured relation-family scope may look narrow if reviewers expect broad
  spatial-relation coverage;
- future `attachment_deferred` expansion could be attacked as affordance guessing
  unless the physical evidence schema is separated from class priors;
- controls and GT verifier evidence may look under-specified in the main text;
- audit wording may look non-anonymous or overfit to an internal reference;
- novelty can be blurred by recent relation-witness/calibrated-witness work.

## Mitigation Status

Updated on 2026-05-27 KST after main-text patches, Docker bootstrap CI,
Docker PDF rebuilds, and the appendix/provenance pass:

- P0 main-text mitigation: completed. `paper/aaai/sec/6_results.tex` no longer
  names the internal reviewer id or reports private-reference matching.
- P1 main-text mitigation: completed. `paper/aaai/sec/6_results.tex` now states
  that the original control suite numbers are from the VL-SAT controlled anchor
  and adds Open3DSG control numbers for distance-only, geometry-only,
  shuffled-geometry, and wrong-pair geometry.
- P2 main-text mitigation: completed. `paper/aaai/sec/4_method.tex` now states
  that the predicate-family map, hard-rule thresholds, counterfactual
  construction, and calibrator files are fixed from train-dev calibration
  artifacts before held-out source-result reporting.
- P5 main-text mitigation: completed. `paper/aaai/sec/3_problem.tex` now
  specifies top-K grouping, violation denominator status handling, and that only
  `violated` rows count as violations.
- P4 main-text mitigation: completed. `paper/aaai/sec/2_related_work.tex` now
  explains why RelWitness is closest prior art but not a direct baseline unless
  its outputs can be mapped to the same row/denominator/violation protocol.
- P3 main-text mitigation: completed. Open3DSG wording was tightened to
  `main open-vocabulary relation-source case study` and `source-output
  reliability evidence`, avoiding broad generation or SOTA framing.
- P6 main-text mitigation: completed. Downstream claims were softened to
  motivation/future evaluation rather than measured downstream performance.
- P7 Docker bootstrap CI: completed. `bootstrap_ci` reports 1,000 subgraph
  resamples with status `ready` and no warnings. Open3DSG family-specific
  deltas remain positive for \rAt{100} and negative for \vAt{100}; VL-SAT
  recall deltas remain modest while violation reductions are stable.
- P8 appendix/provenance pass: completed. `paper/appendix.md` now records the
  calibrator/threshold provenance table, Open3DSG caveat consistency pass,
  Figure 3 final-polish boundary, and Qwen-VL third-source boundary. Docker
  `table_builder` was rebuilt and rerun so experiment Table 6 carries the
  Open3DSG caveat note.
- P9 scope-expansion track: scope audit, coordinate audit, and bucket inspection
  are complete, not metric evidence. The current paper claim remains the
  three-family scoped relation-reliability claim. `relative_horizontal` is the
  preferred expansion candidate because it adds 3,570 candidate GT rows
  (`left`, `right`, `front`, `behind`) and would expand the denominator from
  2,545 to 6,115 if validated. Docker `relative_horizontal_scope_audit`
  confirms VL-SAT has 103,664 candidate prediction rows and Open3DSG has 76,400
  candidate prediction rows, but both are currently `unsupported` by the
  verifier. Docker `relative_horizontal_coordinate_audit` is blocked for
  promotion: the best frame is `scan_left_neg_x_front_neg_y`, macro strict
  purity is 0.7725, strict eligible share is 0.6403, `left`/`right` purity is
  0.8005, `front`/`behind` purity is 0.7445, inverse-pair consistency is 1.0,
  and the wrong-frame gap is 0.1231. Docker
  `relative_horizontal_bucket_inspection` adds threshold-free diagnostics:
  `front`/`behind` strict match:contradiction is 2.9143, sign-only purity is
  0.7491, and ambiguity buckets remain large (`axis_margin_ambiguous` 230,
  `conflicting_axis_dominates` 430, `strong_projected_overlap` 44). The
  recommendation is `do_not_promote_relative_horizontal_to_main_claim`. This is
  useful appendix/limitation evidence but cannot support a broader main claim.
  Current AAAI-path decision is to stop here rather than run expanded-family
  metrics; future promotion requires resolving the `front`/`behind` ambiguity
  and completing the full verifier/calibration/metrics/control/bootstrap/audit
  path.
  Reviewer-facing wording should report the threshold-free evidence first:
  selected frame, per-label GT purity, inverse consistency, wrong-frame gap,
  match/contradiction ratio, and ambiguity buckets. The predeclared purity gate
  is a conservative non-promotion rule, not an official benchmark threshold and
  not a success claim.
- P10 attachment-deferred upgrade: Docker G0 scope/schema audit and G1
  extractor contract completed, no metric execution. This is the preferred
  future relation-family upgrade because it adds 967 GT rows and aligns with
  physical consistency better than relative-horizontal frame semantics. It is
  not part of the current AAAI claim. The audit freezes candidate denominator
  3,512 if validated, source rows VL-SAT 77,748 / Open3DSG 57,300, existing
  verification status `unsupported`, and the extractor contract freezes
  evidence-only output fields. Required defense before promotion: a G1b
  schema-validated extractor dry run for surface type, local contact, surface
  normals, gravity/hanging, contradictory support cues, and
  object-affordance-as-context; train-dev calibration/counterfactuals; GT
  verifier evaluation; VL-SAT/Open3DSG metrics; controls; bootstrap CI; and
  visual audit. Reviewer risk is high if the rule uses object class affordance
  as proof rather than as optional context; the current contract explicitly
  forbids that.
- Verification: Docker bootstrap log `logs/h001_bootstrap_ci_20260526_182034.log`
  exited 0. Docker PDF rebuild `logs/h001_aaai_pdf_build_20260526_182458.log`
  exited 0; `paper/aaai/main.pdf` remains 9 pages with technical content before
  references/checklist, and no missing citations, undefined references,
  overfull hboxes, LaTeX errors, or AAAI package errors were found.
- Latest appendix/caveat PDF rebuild:
  `logs/h001_aaai_pdf_build_appendix_caveat_20260527_202734.log` exited 0;
  `paper/aaai/main.pdf` remains 9 pages, US Letter, with no missing citations,
  undefined references, overfull hboxes, LaTeX errors, or AAAI package errors.

Remaining after P0-P9:

- No P2 provenance blocker remains. Future supplement work should only expand
  details if the target venue requires a separate supplementary PDF.
- P9 is an optional claim-expansion track, not a blocker for the current paper
  claim. Its coordinate audit and bucket inspection are blocked for promotion,
  so the AAAI path freezes it as a disciplined scope-boundary defense rather
  than as a broader-coverage claim. It can strengthen the "framework can scale
  to more spatial relations" defense only if a follow-up resolves the
  `front`/`behind` frame ambiguity and then passes verifier design, calibration,
  controls, Open3DSG/VL-SAT metrics, bootstrap CI, and failure/audit gates.
- P10 is a future-upgrade track, not a current-paper blocker. G0 scope/schema
  audit and G1 extractor contract are complete. If pursued, G1b evidence-only
  extractor dry run should happen before retrying relative-horizontal metrics
  because it is more aligned with H001's physical-consistency mechanism.
  Function reasoning should remain a secondary case study until the attachment
  relation reliability result itself is established.

## Priority Order

### P0. Remove Anonymity And Internal-Audit Wording Risk

Reviewer attack:

> The paper exposes reviewer identity or reports an internal self-check as if it
> were independent human evaluation.

Current weakness:

- Mitigated in `paper/aaai/sec/6_results.tex` on 2026-05-26. The prior draft
  mentioned `reviewer-confirmed by yhkim` and `private-reference match 1.0000`;
  those phrases were removed from the main manuscript.

Required fix:

- Remove personal identifier from the main manuscript.
- Replace the sentence with scoped wording such as:
  `A 50-row internal visual spot-check reaches a target-bucket quality-issue
  rate of 0.9333 and contradiction rate of 0.0333. We use it only as sanity and
  failure-mechanism evidence, not as a large-scale or blinded human audit.`
- Keep detailed provenance in internal notes, not in anonymous main text.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
- `experiments/H001_geom_reliability/tables/table4_audit.md`

### P1. Clarify Controls Source, Denominator, And Placement

Reviewer attack:

> The controls are reported, but it is unclear whether they apply to the main
> Open3DSG result or only to VL-SAT; therefore the nontriviality defense may not
> support the main open-vocabulary case study.

Current weakness:

- Mitigated in `paper/aaai/sec/6_results.tex` on 2026-05-26. The text now
  states that the original control-suite numbers are from the VL-SAT controlled
  anchor under the 2,545-row denominator and adds Open3DSG control numbers for
  the main source-output case study. The main text still compresses controls
  into prose to preserve the AAAI page budget.

Required fix:

- State the source and denominator inline before the control numbers.
- If these controls are VL-SAT-only, say so explicitly and frame them as
  controlled-anchor nontriviality evidence.
- If Open3DSG controls exist, add one compact sentence or appendix table pointer
  for the Open3DSG control results.
- Add a supplement table for controls if page budget blocks a main table.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `experiments/H001_geom_reliability/tables/table2_controls.md`
- `paper/outline.md`

### P2. Strengthen Calibrator / Verifier Provenance

Reviewer attack:

> This is a hand-coded rule verifier, or the rules/calibration were tuned after
> looking at held-out predictions.

Current weakness:

- Mitigated in `paper/aaai/sec/4_method.tex` on 2026-05-26. The main text now
  states that the predicate-family map, hard-rule thresholds, counterfactual
  construction, and calibrator files are fixed from train-dev calibration
  artifacts before held-out source-result reporting.
- GT/counterfactual checks may look circular unless the data split and negative
  construction are explicit; a supplement table would still strengthen this.

Required fix:

- Add one main-text sentence in Method or Experimental Setup:
  `All family mappings, hard-rule thresholds, counterfactual construction, and
  calibrator parameters are fixed from the train-dev calibration artifacts before
  held-out source-result reporting.`
- Create or reference an appendix/supplement table listing family, evidence
  fields, threshold/config source, calibrator artifact, and held-out use.
- Keep `p_geom_valid` described as a reliability score, not a correctness proof.

Evidence / affected files:

- `paper/aaai/sec/4_method.tex`
- `paper/aaai/sec/5_experiments.tex`
- `hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
- `hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
- `experiments/H001_geom_reliability/manifest.lock.json`

### P3. Defend Open3DSG Main-Source Status Without Overclaiming

Reviewer attack:

> If Open3DSG is not an exact official reproduction, why is it the main
> open-vocabulary result?

Current weakness:

- The paper does state averaged-BLIP, filtered split, covered scope, and exact
  denominator caveats.
- The risk is wording: `main open-vocabulary case study` can be interpreted as a
  broad Open3DSG/SOTA claim unless the case-study boundary stays visible.

Required fix:

- Prefer `main open-vocabulary relation-source case study` or
  `Open3DSG source-output reliability case study`.
- Avoid `Open3DSG improvement` unless the sentence says improvement is within
  the reproduced averaged-BLIP source, fixed denominator, and H001 families.
- Keep Table 3 caption caveats visible.

Evidence / affected files:

- `paper/aaai/sec/0_abstract.tex`
- `paper/aaai/sec/5_experiments.tex`
- `paper/aaai/sec/6_results.tex`
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`

### P4. Explain Why Closest Recent Work Is Not A Direct Baseline

Reviewer attack:

> RelWitness or other recent relation-witness/calibration work is closest; why
> not compare directly?

Current weakness:

- Related Work acknowledges RelWitness and distinguishes H001 conceptually.
- It does not yet say why RelWitness is not a direct experimental baseline under
  the current source-output reliability contract.

Required fix:

- Add one sentence after the RelWitness paragraph:
  `We therefore treat RelWitness as closest prior art for witness-based
  open-vocabulary generation, but not as a direct baseline for H001's
  post-source reliability contract unless its outputs can be mapped to the same
  row, denominator, and geometry-violation protocol.`

Evidence / affected files:

- `paper/aaai/sec/2_related_work.tex`
- `literature/2026_arxiv_relwitness/`
- `paper/outline.md`

### P5. Add Metric Definition Detail For Violation@K

Reviewer attack:

> Violation@K is not sufficiently specified: what is the ranking group, what
> happens to uncertain rows, and how is top-K formed?

Current weakness:

- `paper/aaai/sec/3_problem.tex` defines exact-label recall and Violation@K, but
  the grouping and uncertain-row handling could be clearer.

Required fix:

- Add a short metric-detail sentence:
  `Top-K is computed per evaluated subgraph/source ranking over in-scope rows;
  violated rows contribute to Violation@K, while uncertain or missing-evidence
  rows are retained with their recorded status and are not counted as violations
  unless the family rule marks them violated.`
- If this is not exactly the implementation, update the sentence to match the
  metric code before inserting it.

Evidence / affected files:

- `paper/aaai/sec/3_problem.tex`
- `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json`
- `experiments/H001_geom_reliability/tables/table1_main_prediction.md`

### P6. Lower Unsupported Downstream Claims

Reviewer attack:

> The paper mentions downstream reasoning, grounding, alignment, or embodied
> decision modules, but does not test downstream tasks.

Current weakness:

- The motivation is valid, but some Results/Conclusion phrasing can sound like a
  downstream performance claim.

Required fix:

- Use `may mislead` or `motivates downstream evaluation` instead of implying
  measured downstream degradation/improvement.
- Keep downstream tasks as motivation and future work.

Evidence / affected files:

- `paper/aaai/sec/6_results.tex`
- `paper/aaai/sec/8_conclusion.tex`

### P7. Add Confidence Intervals

Reviewer attack:

> VL-SAT gains are small; are they stable?

Status:

- Completed as a Docker paper experiment artifact under
  `experiments/H001_geom_reliability/bootstrap_ci/`.
- The CI is a subgraph-level evaluation-context bootstrap, not repeated training
  variance.
- Main use: defend that the Open3DSG family-specific tradeoff is not a single
  aggregate artifact; keep VL-SAT as controlled-anchor evidence because its
  recall deltas are small.

Key result:

- Open3DSG `family_specific` vs `semantic_only`: \rAt{100} delta +10.22
  percentage points, 95% CI +7.94 to +12.54; \vAt{100} delta -8.84 points, 95%
  CI -9.41 to -8.28.
- VL-SAT `family_specific` vs `semantic_only`: \rAt{100} delta +0.20 points with
  CI crossing zero; \vAt{100} delta -1.59 points with negative CI.

Evidence / affected files:

- `experiments/H001_geom_reliability/bootstrap_ci/summary.md`
- `experiments/H001_geom_reliability/bootstrap_ci/summary.json`
- `experiments/H001_geom_reliability/scripts/bootstrap_metrics.py`
- `paper/aaai/sec/6_results.tex`

### P9. Test Scope Expansion With Relative Horizontal Relations

Reviewer attack:

> The current relation scope is too narrow. The work may be a well-engineered
> verifier for support/proximity/vertical predicates, not a framework that can
> scale to broader spatial-relation reliability.

Current decision:

- Keep the current main paper claim unchanged: scoped relation reliability for
  `support_contact`, `proximity`, and `relative_vertical`.
- Add `relative_horizontal` as a separate validation track, not as immediate
  main evidence. The first Docker scope audit is complete and records that both
  VL-SAT and Open3DSG relative-horizontal rows are currently unsupported by the
  verifier. The coordinate-frame protocol is frozen and the first Docker
  coordinate audit is complete, but it is blocked for main-claim promotion
  because macro strict purity is 0.7725 and `front`/`behind` purity is 0.7445.
- Treat success as evidence that the framework can expand to another large
  spatial family; treat failure or ambiguity as a limitation/future-work result
  rather than weakening the locked main claim.

Why this family:

- It is the largest excluded geometry-adjacent family in the fixed H001
  denominator: 3,570 GT rows, covering `left`, `right`, `front`, and `behind`.
- If validated, the geometry-checkable denominator would expand from 2,545 to
  6,115 GT rows, covering about 81% of the 7,505 held-out GT rows.
- It tests whether H001 is a framework over relation-level geometry reliability
  rather than a hand-crafted rule set for support/proximity/vertical cases.

Main risk:

- `left/right/front/behind` may depend on an annotation coordinate frame,
  room/scan frame, object-centric frame, or viewpoint convention. If the frame
  is wrong, the verifier can look wrong even when the framework is coherent.
  Therefore coordinate-frame validation must precede metric promotion.

Promotion gates before main-claim use:

1. Freeze the `relative_horizontal` label semantics and coordinate-frame
   hypothesis from dataset documentation and empirical label checks.
2. Produce a denominator/coverage audit for GT rows and source prediction rows,
   including excluded or ambiguous cases.
3. Define a deterministic geometry status policy with `satisfied`, `violated`,
   and `uncertain` handling, plus a wrong-frame/axis-flip control.
4. Build train-dev calibration and counterfactual negatives without using
   held-out prediction failures.
5. Run GT-positive/counterfactual verifier evaluation and a targeted visual
   sanity check for horizontal labels.
6. Run VL-SAT and Open3DSG source-result metrics with the expanded family
   included, preserving exact predicate-label recall.
7. Add nontriviality controls: geometry-only, distance-only if relevant,
   shuffled geometry, wrong-pair geometry, and wrong-frame/axis-flip geometry.
8. Run bootstrap CI and failure analysis at the same standard used for the
   current paper claim.

Pass / fail rule:

- Pass: `relative_horizontal` reaches the same evidence standard as the current
  H001 families and improves the recall/violation tradeoff under transparent
  frame and denominator caveats. It may then be promoted from appendix/track
  evidence into the main paper claim.
- Partial: it has useful metrics but unresolved frame ambiguity or weak visual
  audit. Keep it as appendix evidence that motivates broader validation.
- Fail: frame semantics are too ambiguous or controls show the result is a
  coordinate artifact. Keep the current claim unchanged and report the failure
  as a limitation/future-work boundary.

Reviewer-defense wording rule:

- Do not frame the result as "we set 0.80 and missed it" in isolation.
- Frame it as a threshold-free diagnostic: best deterministic frame is clearly
  above wrong-frame alternatives and inverse labels are perfectly consistent,
  but `front`/`behind` remains less stable than `left`/`right`.
- Use the predeclared gate only to justify not broadening the main claim
  post-hoc.

Evidence / affected files:

- `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`
- `experiments/H001_geom_reliability/sources/relative_horizontal/README.md`
- `experiments/H001_geom_reliability/sources/relative_horizontal/scope_audit/`
- `experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_frame_protocol.md`
- `experiments/H001_geom_reliability/sources/relative_horizontal/coordinate_audit/`
- future Docker artifacts under
  `experiments/H001_geom_reliability/sources/relative_horizontal/`
- `paper/aaai/sec/5_experiments.tex` only if the track reaches promotion level
- `paper/aaai/sec/7_limitations.tex` if the track remains partial or failed

## Recommended Immediate Sequence

1. P9: inspect the `relative_horizontal` `front`/`behind`
   ambiguity/contradiction buckets before deciding whether a verifier policy is
   defensible. Do not change the current paper claim during this gate.
2. P0-P8: completed for the current claim; keep the manuscript wording scoped
   during any paper polish.
3. Qwen-VL: keep as a deferred third semantic-source extension until GPU
   runtime is acceptable and full Docker metric/audit promotion can run.

## What Not To Do

- Do not broaden the claim to baseline-agnostic or full open-vocabulary 3DSSG
  generation.
- Do not present Qwen-VL as evidence unless it receives full Docker metric,
  denominator, geometry join, and audit treatment.
- Do not hide Open3DSG averaged-BLIP, filtered split, covered-scope, exact-label
  denominator, or residual calibration-risk caveats.
- Do not describe the 50-row visual spot-check as large-scale, strictly blinded,
  or independent.
- Do not add `relative_horizontal` to the main claim until coordinate-frame
  semantics, denominator, calibration, controls, metrics, bootstrap CI, and
  failure/audit evidence reach the current H001 evidence standard.
