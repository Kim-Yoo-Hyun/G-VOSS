# RelCompat3D Reproducibility Checklist Plan

Last updated: 2026-07-26 KST

## 1. Venue Format

The submission uses the official AAAI-27 reproducibility checklist without
changing its questions or answer choices. Each response in the checklist PDF is
limited to `yes`, `partial`, `no`, or `NA`.

This follows the AAAI format more closely than the longer NeurIPS checklist
style. NeurIPS checklists commonly place an answer and a short justification
under each question. AAAI instead uses a compact status checklist and places
additional explanation in the technical supplement or code/data documentation.

Authoritative sources:

- AAAI-27 Author Kit and the preserved template at
  `paper/aaai/official/ReproducibilityChecklist.tex`
- AAAI Reproducibility Checklist:
  <https://aaai.org/conference/aaai/aaai-23/reproducibility-checklist/>
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
2. One allowed status answer for every question.
3. No manuscript summary, result table, artifact inventory, or local runbook.
4. No claim that licensed third-party data or checkpoints are redistributed.
5. `partial` wherever the paper provides the new RelCompat3D code but relies on
   external datasets, source predictors, checkpoints, or an undecided public
   license.

Current status pattern:

| Area | Status summary |
| --- | --- |
| General structure | `yes` |
| Theoretical contribution | `no`; the supplement still proves implementation guarantees |
| Dataset use and citation | `yes` |
| Unrestricted public availability of all data | `partial` |
| RelCompat3D preprocessing and experiment code in the anonymous archive | `partial` because licensed data and third-party predictors remain external |
| Public post-publication code release | `partial` until the license and permanent URL are fixed |
| Randomness, metrics, run counts, intervals, and infrastructure | `yes` |
| Exhaustive hyperparameter search and every third-party default | `partial` |

## 3. Public Reproducibility Information

The following information helps reviewers verify the claims and should remain
public in the main paper, technical supplement, anonymous code archive, or its
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

### Anonymous code and data archive

- Dockerfile, Compose entry points, and exact execution commands.
- RelCompat3D source, preprocessing, adapters, metrics, controls, audits, and
  bootstrap code.
- Frozen protocol files, random seeds, model definitions, and hashes.
- Compact result manifests and instructions for obtaining external datasets
  and checkpoints.
- A clear reproduction-tier boundary: compact evidence validation, metric
  regeneration from frozen rows, and full source-predictor reproduction.

## 4. Information That Does Not Need to Appear in the Checklist PDF

The following information may be public in the code archive or technical
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

## 6. Answer Rationale

The checklist itself stays compact. The reason for each non-`yes` answer is:

- **Theoretical contribution: `no`.** RelCompat3D is an empirical method
  contribution. The supplement proves exact transformation and ranking
  properties as implementation guarantees, not as theoretical novelty; the
  conditional theory questions are therefore `NA`.
- **Existing datasets publicly available: `partial`.** The underlying
  3DSSG/3RScan and ReplicaSSG assets are accessed under the terms of the
  original providers, and this paper does not redistribute licensed scans or
  third-party checkpoints.
- **Unavailable datasets described: `partial`.** The manuscript and supplement
  describe the split, relation scope, source dependencies, evaluation mapping,
  and Open3DSG coverage policy, while raw licensed inputs remain external.
- **Hyperparameter ranges: `partial`.** Final settings and focused sensitivity
  analyses are reported, but no exhaustive search over every design choice is
  claimed.
- **Preprocessing and complete experiment code: `partial`.** The new
  RelCompat3D pipeline is included, but third-party source repositories,
  licensed inputs, checkpoints, and large regenerable caches are external.
- **Post-publication public code: `partial`.** The anonymous code archive is
  prepared, but the permanent public URL and license are not yet frozen.
- **Implementation comments: `partial`.** Core scripts and runbooks document
  the implementation, but not every adapter line contains a paper-section
  reference.
- **All final hyperparameters: `partial`.** RelCompat3D parameters, ranking
  constants, audit rules, and seeds are frozen; all historical or
  third-party predictor defaults are not duplicated in the paper.

## 7. Release Files

- Checklist source:
  `paper/aaai/reproducibility_checklist.tex`
- Standalone wrapper:
  `paper/aaai/reproducibility_checklist_main.tex`
- Canonical submission PDF:
  `paper/aaai/reproducibility_checklist_aaai27.pdf`
- Canonical PDF SHA256:
  `a346d55325dc63f7e9324cd0dc34dbcc0e72abc6ad3836f730d39c370477e212`

Before submission, verify that the PDF uses US Letter pages, has no unresolved
references, contains no Type 3 or Identity-H fonts, and matches the current
main paper, supplement, and anonymous code archive.
