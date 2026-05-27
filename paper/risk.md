# H001 Paper Reviewer-Risk Register

Last updated: 2026-05-26 KST

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
- controls and GT verifier evidence may look under-specified in the main text;
- audit wording may look non-anonymous or overfit to an internal reference;
- novelty can be blurred by recent relation-witness/calibrated-witness work.

## Mitigation Status

Updated on 2026-05-26 KST after main-text patches, Docker bootstrap CI, and
Docker PDF rebuilds:

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
- Verification: Docker bootstrap log `logs/h001_bootstrap_ci_20260526_182034.log`
  exited 0. Docker PDF rebuild `logs/h001_aaai_pdf_build_20260526_182458.log`
  exited 0; `paper/aaai/main.pdf` remains 9 pages with technical content before
  references/checklist, and no missing citations, undefined references,
  overfull hboxes, LaTeX errors, or AAAI package errors were found.

Remaining after P0-P7:

- A supplement table for calibrator/threshold provenance would still strengthen
  P2, but the main-text blocker is mitigated.

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

## Recommended Immediate Sequence

1. P0: anonymize/remove internal audit wording in `sec/6_results.tex`.
2. P1: clarify controls source/denominator and decide whether controls stay as
   main prose or move to supplement table.
3. P2: add calibrator/threshold freeze provenance sentence and supplement table
   plan.
4. P5: tighten `Violation@K` metric definition.
5. P4: add one RelWitness non-baseline sentence.
6. P3 and P6: run a wording pass to keep Open3DSG and downstream claims scoped.
7. P7: completed as Docker subgraph bootstrap CI; keep wording scoped to
   evaluation-context uncertainty, not repeated-training variance.

## What Not To Do

- Do not broaden the claim to baseline-agnostic or full open-vocabulary 3DSSG
  generation.
- Do not present Qwen-VL as evidence unless it receives full Docker metric,
  denominator, geometry join, and audit treatment.
- Do not hide Open3DSG averaged-BLIP, filtered split, covered-scope, exact-label
  denominator, or residual calibration-risk caveats.
- Do not describe the 50-row visual spot-check as large-scale, strictly blinded,
  or independent.
