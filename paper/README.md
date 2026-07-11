# Paper Workspaces

Last updated: 2026-07-12 KST

This directory contains paper-writing artifacts. It is a manuscript workspace,
not an experiment-result root. Paper-result runtime records live under
`experiments/`, compact paper-facing summaries live under `results/`, and
paper-level framing rules live in `docs/paper.md`.

## Active Workspaces

| Workspace | Role |
| --- | --- |
| root files and `aaai/` | GeoCalib / H001 AAAI manuscript route |
| `h002_compatibility_routing/` | standalone H002 paper workspace for semantic-geometry compatibility routing |

## Current H001 Route

- Paper-facing title: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`
- Target venue route: `paper/aaai/`
- Historical alternate route: `archive/paper/iccv/`
- Current claim style: scoped relation-reliability paper for
  geometry-checkable 3D Scene Graph relation families.
- Non-claim: broad open-vocabulary 3DSSG generation improvement.
- Active AAAI-27 Docker build: `paper/aaai/main_aaai27.pdf` (9 pages: technical
  content through page 7 and references only on pages 8--9),
  `paper/aaai/supplement_aaai27.pdf` (1 page), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Final main log:
  `logs/h001_aaai27_main_build_20260712.log`; triplet verification log:
  `logs/h001_aaai27_final_triplet_build_20260712.log`; image:
  `h001-aaai27-tex:20260712`. Type 3 fonts, unresolved references/citations,
  LaTeX errors, and overfull boxes are zero.
- Active OpenReview field bundle:
  `release/h001_aaai27_openreview_20260712_083625/`. The prior
  Replica-disclosure PDF and compact tarball are historical snapshots.
- GeoCalib is framework-first. Its two soft fusion instantiations are the
  calibrated product (`family_conditional_risk = semantic_score *
  p_geom_valid_family`) and the pre-specified scale-robust rank-average.
  Neither is claimed universally dominant. Pooled calibration is an ablation,
  RRF a strong comparator, and calibrator-only/no-source-score ranking a
  control.
- H001 now uses the factor contract `T_e` = predicate/family semantics, `G_e`
  = raw predicate-independent same-pair geometry, `Z_e` = source confidence,
  and `C_e = P(y_cal=1 | T_e,G_e)`, with `Z_e notin C_e` and
  `S_e = F(Z_e,C_e)`. `y_cal` is the constructed calibration target rather
  than direct human validity. The legacy `p_geom_valid`-only condition is not
  true `G_e`-only because its calibrator retains `T_e`/interaction features.
- `h001_factor_isolation_protocol_v1` implementation is complete. The later
  `train_only_reestablishment_v1` strict reconstruction is also complete and
  passes its frozen internal-dev/final aggregate gates. Detailed provenance
  classification is owned by `docs/paper.md` and the experiment report rather
  than duplicated in this workspace index.
- H001_v2 fixed-`tau*` and pooled lambda-soft reranking are diagnostic
  candidate evidence only; they do not replace the current GeoCalib main
  result route.
- Remaining paper-work class: enter author profiles/countries and reciprocal
  reviewer in OpenReview, decide the final public license/post-acceptance
  artifact URL, and optionally run the independent human-alignment study.
  Target-year policy, standalone checklist, supplement choice, upload ZIP, and
  current PDF/source sanity checks are complete.

## Current H002 Route

- Paper-facing title: `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`
- Workspace: `paper/h002_compatibility_routing/`
- Current claim style: validation-level source-reranking and reliability-layer
  paper over VL-SAT/Open3DSG validation predictions.
- Main score: `S2_source_x_Ce = normalized_source_score(Z_e) * normalized_C_e`,
  where raw `C_e` is computed from `T_e`, `G_e`, and their explicit interaction
  before source score is used.
- Framework map: relation-aware evidence routing. Current quantitative claim is
  deliberately scoped to the comparison route (`relative_vertical`,
  `size_relative`) plus caveated `left/right`; support/contact remains
  hard-route failure taxonomy.
- Current split: official 3DSSG validation split, not official test.
- Non-claims: SOTA/leaderboard, official test benchmark, solved
  support/contact, calibrated `p_obs/p_rel` solved reliability.
- H001 manuscript files under `paper/aaai/` are not edited by H002 workspace
  promotion.

## File Roles

- `README.md`: folder entry point. Owns the paper workspace map, file roles,
  reading order, and update ownership.
- `h002_compatibility_routing/README.md`: H002 standalone paper workspace entry
  point. Owns H002 claim boundary, paper file roles, and source artifact map.
- `h002_compatibility_routing/aaai2027/`: canonical H002 AAAI manuscript,
  supplement, checklist, bibliography, figure/table assets, and build runbook.
- `h002_compatibility_routing/risk.md`: H002 reviewer-risk and claim-boundary register.
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
- `review.md`: orthogonal persona review. Owns the current multi-reviewer
  assessment of claim, contribution, method, experiment design, and submission
  risks.
- `appendix.md`: appendix/supplement plan. Owns calibrator/threshold
  provenance, detailed caveat consistency checks, appendix table candidates,
  optional Figure 3 decision notes, and Qwen-VL extension boundary.
- `references.bib`: shared BibTeX bibliography for draft and venue-specific
  LaTeX sources.
- `top_tier_review.md`: comparison-driven paper style review and table/figure
  layout decision log.
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
5. `paper/review.md`
6. `paper/appendix.md`
7. `paper/outline.md`
8. `paper/draft.md`
9. `paper/figures.md`
10. `paper/aaai/README.md`

For H002 paper-writing work:

1. `docs/paper.md`
2. `hypothesis/CAND-001/H002_factorized-relation-confidence/README.md`
3. `hypothesis/CAND-001/H002_factorized-relation-confidence/paper_claim_core.md`
4. `hypothesis/CAND-001/H002_factorized-relation-confidence/method_contract_v1.md`
5. `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md`
6. `paper/h002_compatibility_routing/README.md`
7. `paper/h002_compatibility_routing/risk.md`
8. `paper/h002_compatibility_routing/aaai2027/README.md`
9. `paper/h002_compatibility_routing/aaai2027/main.tex`

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
