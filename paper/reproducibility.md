# RelCompat3D Reproducibility Checklist Plan

Last updated: 2026-07-29 KST

## 1. Venue Format

The submission uses the official AAAI-27 reproducibility checklist without
changing its questions or answer choices. Each completed response in the
checklist PDF is limited to `yes`, `partial`, `no`, or `NA`.

Section 2 is conditional. The official wording says to address its subquestions
only if the paper makes theoretical contributions. Because the parent answer is
`no`, the seven subquestion response fields are left blank. This is stricter
than writing `NA`: Questions 2.2--2.6 do not list `NA` as an allowed response,
while the template instructs authors to use only an option listed for an
applicable question. The template does not separately prescribe how an inactive
response field must be rendered. Leaving it blank follows the conditional
wording without inserting an unlisted answer.

The `Instructions for Authors` block is retained. The official AAAI-27 source
renders that block in standalone mode and explicitly tells authors to replace
only the response placeholders without modifying other lines. The AAAI-27 call
requires a completed checklist but does not instruct authors to remove the
front instructions. Deleting the block would therefore be a template change
without an official basis.

This follows the AAAI format more closely than the longer NeurIPS checklist
style. NeurIPS checklists commonly place an answer and a short justification
under each question. AAAI instead uses a compact status checklist and places
additional explanation in the Technical Supplement or post-acceptance release
documentation.

Authoritative sources:

- AAAI-27 Author Kit:
  <https://aaai.org/authorkit27/>, with its preserved template at
  `paper/aaai/official/ReproducibilityChecklist.tex`
- AAAI-26 Reproducibility Checklist, whose public wording uses the same
  conditional theory section:
  <https://aaai.org/conference/aaai/aaai-26/reproducibility-checklist/>
- AAAI-27 Main Technical Track call:
  <https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/>
- NeurIPS 2025 checklist policy:
  <https://neurips.cc/Conferences/2025/CallForPapers>
- Representative NeurIPS paper checklist with answer-plus-justification
  entries:
  <https://openreview.net/pdf?id=qae8I9PSoo>

## 2. Information That Belongs in the Checklist PDF

The checklist PDF should contain:

1. The official questions and section order.
2. One allowed status answer for every applicable question. Conditional
   subquestions remain unanswered when their parent condition is false.
3. No manuscript summary, result table, artifact inventory, or local runbook.
4. No claim that licensed third-party data or checkpoints are redistributed.
5. `no` for code-in-appendix questions because no Code and Data Supplement is
   uploaded during review, and `yes` for the planned post-acceptance release.

Current status pattern:

| Area | Status summary |
| --- | --- |
| General structure | `yes` |
| Theoretical contribution | `no`; conditional theory subquestions are left unanswered rather than assigned an unlisted `NA` |
| Dataset use and citation | `yes` |
| Unrestricted public availability of all data | `partial` |
| RelCompat3D preprocessing code in a review appendix | `no`; no Code and Data Supplement is uploaded |
| Complete experiment code in a review appendix | `no`; no Code and Data Supplement is uploaded |
| Public post-publication code release | `yes`; internal preparation begins after acceptance, with public release no later than paper publication |
| Randomness, metrics, run counts, intervals, and infrastructure | `yes` |
| Hyperparameter ranges and development search | `partial`; focused sensitivities are reported rather than an exhaustive search |
| Final settings used by the reported methods and controls | `yes`; main, supplement, and frozen protocols agree |

## 3. Public Reproducibility Information

The following information helps reviewers verify the claims and should remain
public in the main paper, technical supplement, post-acceptance code release, or its
README.

### Main paper

- Task definition and claim scope.
- Evaluated and re-ranked relation families.
- Train, development, and evaluation split roles and counts.
- Candidate identity and exact-match evaluation identity.
- Linear and MLP compatibility estimators.
- Loss definition and main loss constants.
- Transformation averaging and family-aware re-ranking.
- Recall and verifier-derived Violation definitions.
- Reported \(K\) values and paired scan-bootstrap protocol.
- Main baselines, controls, point/mesh audit, and scoped limitations.

### Technical supplement

- Complete counterfactual construction rules and row counts.
- Full estimator inputs, parameter counts, optimization steps, and learning
  rates.
- One-fit run policy and the distinction between scan-resampling intervals and
  retraining variance.
- Hardware, operating system, Docker, Python, and relevant library versions.
- Exact transformation and ranking guarantees with proofs.
- Sensitivity analyses, component removals, matched controls, point/mesh
  measurements, coverage, uncertainty, and per-family results.
- Open3DSG coverage handling and the ReplicaSSG/FROSS stress-test scope.

### Post-acceptance code and data release

- Dockerfile, Compose entry points, and exact execution commands.
- RelCompat3D source, preprocessing, adapters, metrics, controls, audits, and
  bootstrap code.
- Frozen protocol files, random seeds, model definitions, and hashes.
- Compact result manifests and instructions for obtaining external datasets
  and checkpoints.
- A clear reproduction-tier boundary: compact evidence validation, metric
  regeneration from frozen rows, and full source-predictor reproduction.

## 4. Information That Does Not Need to Appear in the Checklist PDF

The following information may be public in the post-acceptance code release or technical
supplement when useful, but repeating it in the checklist PDF adds length
without improving the checklist answers:

- exact model and protocol SHA256 values;
- every experiment directory and result-file path;
- full Docker commands and recovery commands;
- all table values, confidence intervals, or failure examples;
- the complete hyperparameter sensitivity grid;
- MLflow run identifiers and historical checkpoint comparisons;
- timestamps, build hashes, and release-bundle filenames;
- detailed cache, checkpoint, and dataset mount layouts.

## 5. Information That Should Not Be Published

The submission artifacts should exclude:

- absolute local filesystem paths and usernames;
- machine identifiers, serial numbers, access tokens, or private URLs;
- raw runtime logs and temporary build products;
- private or licensed datasets, scans, images, meshes, and checkpoints;
- large source-derived row dumps that cannot be redistributed under the source
  terms;
- obsolete experiment branches, superseded manuscript versions, and abandoned
  methods;
- unverified exploratory results or internal reviewer annotations;
- historical Qwen, H002, Codex-proxy, and other experiments outside the active
  RelCompat3D claim.

CPU/GPU model names, approximate memory, operating-system version, container
versions, and deterministic seeds are normal reproducibility information and
are not treated as private identifiers.

## 6. Question-by-Question Answer Rationale

The submitted checklist remains limited to the official status choices. This
section records the evidence behind every answer without adding prose to the
checklist PDF.

### 6.1 General Paper Structure

1. **Conceptual outline of the introduced method: `yes`.** Figure 2 and the
   Method section present the full sequence from predicate semantics and
   ordered-pair geometry to compatibility estimation, within-family scoring,
   and family-aware re-ranking. The equations define the compatibility and
   ranking scores used by both variants.
2. **Separation of facts, hypotheses, and speculation: `yes`.** The Results
   section distinguishes point estimates from paired confidence intervals.
   It consistently calls Violation a verifier-derived metric. The
   point-and-mesh audit is described as an alternative measure, and the
   Discussion states that it is not independent ground truth.
3. **Pedagogical references: `yes`.** The Introduction and Related Work cite
   the 3D scene graph task, 3RScan/3DSSG, the evaluated predictors, and relevant
   reliability literature. Dataset names, metrics, relation families, and
   method-specific terms are defined before they are used operationally.

### 6.2 Theoretical Contributions

4. **Theoretical contribution: `no`.** RelCompat3D is an empirical method and
   evaluation contribution. The supplement proves transformation and ranking
   properties as implementation guarantees, not as a separate theoretical
   contribution.
5. **Formal assumptions and restrictions: not answered.** This question
   applies only when Question 4 is `yes`. Its listed choices do not include
   `NA`.
6. **Formal statements of novel theoretical claims: not answered.** The paper
   does not claim new theorems, and the conditional theory list is inactive.
7. **Proofs of novel theoretical claims: not answered.** There are no claimed
   theoretical contributions requiring complete proofs.
8. **Proof sketches or intuitions for theoretical results: not answered.** The
   supplement nevertheless explains and proves the exact properties used by
   the implementation.
9. **Citations to theoretical tools: not answered.** No external theoretical
   result is presented as the basis of a novel theorem.
10. **Empirical demonstrations of theoretical claims: not answered.** Although
    this question offers `NA`, the full conditional list is left unanswered
    consistently after the parent `no`.
11. **Code used to eliminate or disprove theoretical claims: not answered.**
    This question also offers `NA`, but the paper does not conduct
    theory-elimination experiments and the parent condition is false.

### 6.3 Dataset Usage

12. **Reliance on datasets: `yes`.** The main evaluation uses 3RScan/3DSSG.
    The supplement also reports a ReplicaSSG/FROSS stress test.
13. **Motivation for the selected datasets: `yes`.** The shared 3DSSG target
    provides one ontology, geometry source, and evaluation scope for comparing
    three fixed predictors. The supplementary transfer test examines a change
    in ontology and geometry.
14. **Novel datasets included in a data appendix: `NA`.** The paper introduces
    no new dataset.
15. **Public release of novel datasets: `NA`.** No new dataset is claimed or
    collected.
16. **Citations for existing datasets: `yes`.** 3RScan, 3DSSG, ReplicaSSG, and
    the prediction sources are cited where their roles are introduced.
17. **Public availability of all existing datasets: `partial`.** The datasets
    and source models are obtainable through their providers, but some require
    provider-controlled access or acceptance of external terms. The submission
    does not redistribute licensed scans, meshes, RGB-D data, stable source
    identifiers, source-derived row bundles, or third-party checkpoints. It
    provides code, schemas, aggregate outputs, expected manifests, and
    deterministic exporters for use after obtaining the original datasets
    under their terms.
18. **Description of data that are not freely redistributable: `partial`.**
    The main paper and supplement report the split roles and sizes, relation
    scope, source dependencies, evaluation mapping, and Open3DSG coverage
    policy. These descriptions and deterministic preparation commands do not
    replace the licensed source assets, and publicly available alternatives
    would not reproduce the same benchmark target.

### 6.4 Computational Experiments

19. **Computational experiments: `yes`.** The reported claims are supported by
    model fitting, re-ranking, controls, sensitivity analyses, and geometric
    audits.
20. **Development ranges and selection criteria: `partial`.** The supplement
    reports the final settings and focused, pre-specified sensitivity values.
    It does not claim an exhaustive search over every architecture,
    construction rule, and threshold.
21. **Preprocessing code: `no`.** No Code and Data Supplement is uploaded
    during review. Preprocessing inputs and operations are instead described
    in the Technical Supplement.
22. **All experiment and analysis source code: `no`.** No code appendix is
    included in the review submission.
23. **Post-publication public code release: `yes`.** This answer commits to
    public release by paper publication. Internally, the RelCompat3D
    implementation, evaluation scripts, and machine-readable results are
    prepared after acceptance. Third-party assets remain subject to their
    original licenses.
24. **Implementation comments with paper references: `partial`.** Core source
    modules, command entry points, schemas, and runbooks document the
    implementation and paper-facing outputs. Not every adapter statement has
    an inline reference to a paper section.
25. **Random-seed policy: `yes`.** Each reported condition uses a fixed seed
    and one fit. The supplement also evaluates five seeds chosen before
    training and states that the active model was not reselected from those
    results.
26. **Computing infrastructure: `yes`.** The supplement explicitly reports
    the pinned Python 3.11.9, NumPy 1.26.4, and Pillow 10.4.0 Docker stack,
    Linux 6.17, an Intel Core Ultra 7 265KF CPU, CPU-only re-ranking, and
    366.5 MiB peak RSS. Source-predictor inference is identified as a separate
    source-specific stage.
27. **Metric definitions and motivation: `yes`.** The main paper formally
    defines exact-match Recall@\(K\) and verifier-derived Violation@\(K\).
    Their joint use separates retrieval coverage from compatibility with the
    reconstructed ordered-pair geometry.
28. **Number of algorithm runs: `yes`.** The supplement states one fit for
    each reported condition, 1,000 paired scan-level bootstrap resamples, five
    pre-specified training seeds for the seed analysis, and five repetitions
    for the runtime measurement.
29. **Variation and confidence information: `yes`.** The paper reports paired
    95% bootstrap intervals, seed means and standard deviations, coverage and
    uncertainty variants, and point-and-mesh audit results.
30. **Statistical assessment of changes: `yes`.** Recall and Violation changes
    use paired scan-level bootstrap intervals. All contexts from a sampled scan
    are resampled together, and the same resamples are shared across compared
    conditions. Claims of detectable change are based on whether the paired
    interval excludes zero in the stated direction.
31. **Final hyperparameters: `yes`.** The main paper and supplement specify the
    loss constants, estimator architectures, optimizer, step counts, learning
    rates, transformation sets, ranking rule, evaluated \(K\) values,
    bootstrap count, audit thresholds, and seed policy. The three source
    predictors provide frozen relation scores and are not refitted for
    RelCompat3D.

## 7. Release Files

- Checklist source:
  `paper/aaai/reproducibility_checklist.tex`
- Standalone wrapper:
  `paper/aaai/reproducibility_checklist_main.tex`
- Canonical submission PDF:
  `paper/aaai/reproducibility_checklist_aaai27.pdf`
- Canonical PDF SHA256:
  `eafbba13031b1e6ecd6acc3afaaa64576a0dbda1b581c383a782ba177741c5ad`
- Review upload boundary: main paper, reproducibility checklist, and Technical
  Supplement only. No Media or Code and Data Supplement is uploaded.
- Local post-acceptance code/data staging remains under `release/` and is not a
  review artifact.

The clean Docker build was verified on 2026-07-29 KST. The checklist is a
two-page US Letter PDF using PDF 1.5. It has no unresolved references,
overfull boxes, Type 3 fonts, Identity-H fonts, or unembedded fonts. Its source
matches the current checklist answers and Technical Supplement boundary.
