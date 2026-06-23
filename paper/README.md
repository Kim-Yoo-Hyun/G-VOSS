# GeoCalib / H001 Paper Workspace

Last updated: 2026-06-23 KST

This directory contains paper-writing artifacts for GeoCalib/H001. It is a
manuscript workspace, not an experiment-result root. Paper-result runtime
records live under `experiments/H001_geom_reliability/`, compact paper-facing
summaries live under `results/h001_geom_reliability/`, and paper-level framing
rules live in `docs/paper.md`.

## Current Route

- Paper-facing title: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`
- Target venue route: `paper/aaai/`
- Historical alternate route: `archive/paper/iccv/`
- Current claim style: scoped relation-reliability paper for
  geometry-checkable 3D Scene Graph relation families.
- Non-claim: broad open-vocabulary 3DSSG generation improvement.
- Latest known Docker build: `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log`, exit 0, 9 pages.
- Remaining paper-work class: portal/form verification, artifact URL/DOI,
  supplementary/code-data decision, checklist answer pass, low-K artifact
  inclusion in the release/package plan, and final PDF/source sanity checks.

## File Roles

- `README.md`: folder entry point. Owns the paper workspace map, file roles,
  reading order, and update ownership.
- `preview.md`: current paper handoff snapshot. Owns current claim, secured
  evidence, key metrics, caveats, reviewer-defense map, and recovery file list.
- `progress.md`: experiment progression rationale. Owns why each hypothesis and
  experiment stage was run, why the next stage was needed, and how results
  should be interpreted.
- `outline.md`: paper structure plan. Owns title candidates, contribution
  statements, abstract/Introduction skeletons, section roles, evidence
  placement, table/figure plan, and claim-consistency guardrails.
- `draft.md`: first-pass manuscript prose. Owns the readable paper body from
  title through conclusion before final venue-specific compression.
- `figures.md`: figure source lock. Owns Figure 1-3 claims, source artifacts,
  locked values/cases, caption constraints, and figure non-claims.
- `risk.md`: reviewer-risk register. Owns attack surface, weakness/mitigation
  tracking, and priority order for logic, novelty, evidence, and
  reproducibility defenses.
- `appendix.md`: appendix/supplement plan. Owns calibrator/threshold
  provenance, detailed caveat consistency checks, appendix table candidates,
  optional Figure 3 decision notes, and Qwen-VL extension boundary.
- `references.bib`: shared BibTeX bibliography for draft and venue-specific
  LaTeX sources.
- `aaai/`: current AAAI-style LaTeX source, official style files, Docker build
  route, PDF build status, and venue-local README.
- `archive/paper/iccv/`: historical ICCV-style LaTeX source route. Keep as
  alternate history unless the target venue changes back.
- `generated/figures/`: generated draft figure assets, validation files, and
  figure reports.
- `scripts/`: scripts for generating draft figures and geometry-backed panels.

## Reading Order

For paper-writing work:

1. `docs/paper.md`
2. `paper/README.md`
3. `paper/preview.md`
4. `paper/risk.md`
5. `paper/appendix.md`
6. `paper/outline.md`
7. `paper/draft.md`
8. `paper/figures.md`
9. `paper/aaai/README.md`

For experiment result or artifact recovery, start from
`docs/reproducibility.md`, not this folder.

## Update Rules

- If file roles or paper workspace ownership changes, update this README.
- If claim boundary, novelty, or reviewer-defense rules change, update
  `docs/paper.md`, `summary.md`, and the relevant paper planning file.
- If current evidence, caveats, or recovery files change, update `preview.md`.
- If experiment-stage rationale changes, update `progress.md`.
- If paper structure, contribution wording, or table/figure placement changes,
  update `outline.md`.
- If prose changes, update `draft.md` or the active venue source under
  `paper/aaai/`.
- If figure claims, source rows, values, or captions change, update
  `figures.md` before regenerating assets.
- If reviewer attack mitigation changes, update `risk.md`.
- If supplement/appendix provenance or detailed caveat accounting changes,
  update `appendix.md`.
- If build commands, style files, or PDF status change, update the relevant
  venue folder README.
