# H001 AAAI-27 Submission Plan

Last updated: 2026-06-13 KST

This file fixes the submission-side decisions that are not scientific
experiment results. It should be updated only when portal instructions,
artifact release policy, or checklist answers change.

## Official Instruction Check

Checked on 2026-06-13 KST:

- AAAI-27 Main Technical Track call:
  `https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/`
- AAAI-27 OpenReview group:
  `https://openreview.net/group?id=AAAI.org%2F2027%2FConference`
- AAAI-27 Author Kit:
  `https://aaai.org/authorkit27/`

AAAI-27 public facts:

- Author registration opens: 2026-06-17 AoE.
- Paper submission opens: 2026-06-24 AoE.
- Abstract deadline: 2026-07-21 23:59 UTC-12.
- Full paper deadline: 2026-07-28 23:59 UTC-12.
- Supplementary material and code deadline: 2026-07-31 23:59 UTC-12.
- Main-track submissions allow up to 7 pages of technical content plus
  additional pages solely for references.
- Authors may submit supplementary technical appendix, multimedia, and code/data,
  but reviewers are not required to review supplementary material. Critical
  evidence must remain in the main paper.
- A reproducibility checklist is required.
- The OpenReview AAAI-27 group page is public, but detailed submission form
  fields are not inspectable from the public group page at this time.

Decision:

- Keep the paper self-contained. Do not move claim-critical tables, caveats,
  controls, or failure evidence out of the main PDF.
- Re-check the OpenReview form after the paper-submission portal opens on
  2026-06-24 AoE, because final field names and upload constraints are portal
  state, not fully specified on the public group page.
- Regenerate the flattened source/PDF package from the latest GeoCalib source
  before upload. The previous package
  `release/h001_aaai27_submission_20260613_004455/` predates the latest
  GeoCalib/Figure 1 pass and is only a historical hygiene check.

## Artifact / URL / DOI Decision

Review-phase decision:

- Do not put an external web URL in the anonymous review manuscript unless the
  final AAAI/OpenReview form explicitly asks for one.
- Prefer OpenReview supplementary upload for anonymous review artifacts, because
  review artifacts should be fixed at submission time and should not depend on a
  mutable external webpage.
- Use the verified local full-validation result bundle as the primary result
  artifact:

```text
release/h001_full_validation_results_20260611_025158.tar.zst
sha256: d7d8678c5dfc4c2dda54c781220951386cb08cc2d7ca6b5cec908ee9e5e76cea
size: 1.4G / 1502684667 bytes
```

Post-acceptance/public-release decision:

- Source code: release the tracked source/runbook repository on GitHub after
  anonymization is no longer required.
- Fixed paper-result artifact: mint a Zenodo DOI for the exact full-validation
  result bundle and cite that DOI in the camera-ready/release materials.
- Optional mirror: use a Hugging Face Dataset or institutional storage mirror
  only as a convenience copy, not as the canonical DOI.
- License remains a release blocker. Do not upgrade checklist code-release
  answers to `yes` until source-code license and artifact license notes are
  actually fixed.

## Supplementary Upload Decision

Decision:

- Upload code/data supplementary material if the AAAI/OpenReview portal accepts
  the current size and format.
- Do not create a separate technical appendix PDF for the current route. The
  main paper already contains claim-critical evidence, and the existing
  supplementary need is reproducibility support rather than extra argumentation.

Preferred review supplement contents:

1. `release/h001_full_validation_results_20260611_025158.tar.zst`
2. `release/h001_full_validation_results_20260611_025158.sha256`
3. `release/h001_full_validation_results_20260611_025158.manifest.md`
4. `experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/`

If the portal requires a `.zip` container, create a ZIP wrapper around those
files only at upload time. Current disk pressure is high enough that a duplicate
1.4G wrapper should not be kept unless the portal requires it.

If the portal size limit is below the 1.4G result bundle, use the result bundle
manifest and row-count/checksum files as the submitted representative subset,
then provide the full bundle through the post-acceptance Zenodo DOI.

## Checklist Answer Audit

Current policy:

- Keep code/data/license/public-release items as `partial` until the upload
  artifact and release license are fixed.
- Upgrade computing-infrastructure answer to `yes` because the checklist now
  states the concrete GPU, OS, memory, Docker version, image IDs, and software
  versions, and a separate manifest exists.
- Keep significance-testing answer as `partial`; paired bootstrap CIs are
  reported, but no repeated-run variance or Wilcoxon-style test is claimed.
- Keep hyperparameter/config answer as `partial`; operating points and major
  policies are fixed in paper/artifacts, but a single exhaustive public config
  table for every threshold is not yet a release artifact.
