# Paper Workspaces

Last updated: 2026-07-14 KST

This directory contains paper-writing artifacts. It is a manuscript workspace,
not an experiment-result root. Paper-result runtime records live under
`experiments/`, compact paper-facing summaries live under `results/`, and
paper-level framing rules live in `docs/paper.md`.

## Active Workspaces

| Workspace | Role |
| --- | --- |
| root files and `aaai/` | RelCompat3D / H001 AAAI manuscript route |
| `paper_nonsub/` | non-submission Codex proxy-audit analysis; never package as human evidence |
| `h002_compatibility_routing/` | standalone H002 paper workspace for semantic-geometry compatibility routing |

## Current H001 Route

- Paper-facing title: `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations`
- Target venue route: `paper/aaai/`
- Historical alternate route: `archive/paper/iccv/`
- Current claim style: scoped relation-reliability paper for
  geometry-checkable 3D Scene Graph relation families.
- Non-claim: broad open-vocabulary 3DSSG generation improvement.
- Active AAAI-27 Docker build: `paper/aaai/main_aaai27.pdf`, SHA256
  `49459774de4bd244af34de48a06a867b0b14694215ff29fd35e17c8a5e64106f` (8 pages: technical
  content through page 7 and references on pages 7--8),
  `paper/aaai/supplement_aaai27.pdf`, SHA256
  `7fcbf062b3d5bf8224feef20afdb52acd14dc5602d397d0c8022456310e261ce`
  (2 pages), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf`, SHA256
  `fbd076b1789fe0fb1a50c67aa6bb113654b87fe23d09a3b1c5826f02805fe05a`
  (2 pages). Final main log:
  `logs/h001_main_figure_refresh_20260714.log`; final supplement log:
  `logs/h001_supplement_text_refresh_20260714.log`; image:
  `h001-aaai27-tex:20260712`. Type 3 fonts, unresolved references/citations,
  LaTeX errors, and overfull boxes are zero.
- The active submission excludes Codex-derived physical-validity numbers. The
  separately built `paper/paper_nonsub/main_nonsub.pdf`, SHA256
  `52dc1c775ede032df45f345999f6421cadbb331856a5e4862c083c29f9ee7287`,
  contains the two-pass non-human diagnostic for internal/user review only.
- The manuscript narrative now proceeds failure -> structural cause -> factor
  isolation -> method -> experiments -> discussion/limitations. It uses six
  top-level sections; Problem Setup is inside Method, and Setup/results are
  grouped under Experiments. Figure 1 is failure-grounded,
  Figure 2 connects K=5/10/20/50/100 for three sources, and Figure 3 shows two
  corrections plus one residual failure. The main comparison is one joint
  Recall/Violation table followed by a single-column K=50/100 six-control
  ablation table. All three figures are included as vector PDFs.
- Active OpenReview field bundle:
  `release/h001_aaai27_openreview_20260714_170829/`. It contains exact copies
  of the canonical 8/2/2-page PDFs plus a focused anonymous structured-main
  ZIP. The prior Replica-disclosure and other superseded PDFs are indexed under
  `archive/paper/aaai_snapshots/`; the 2026-07-12 bundle and compact tarball are
  historical handoff snapshots.
- RelCompat3D is framework-first. Its main method is the strict train-only
  relation-algebra-constrained product $ZC_{alg}(T,G)$; the evaluated
  scale-robust rank-average is a second instantiation. Neither is claimed
  universally dominant. Pooled compatibility
  is an ablation, RRF a strong comparator, and compatibility-only ranking a
  control. Internal metric keys no longer appear in manuscript prose or
  rendered figures.
- Linked-counterfactual margin fitting with exact proximity-swap/vertical-
  inverse orbit projection is promoted as the main compatibility model. All
  main comparators, uncertainty results, figures, and tables were regenerated
  together under `structured_main_v1/`; the internal orbit name is retained
  only for artifact provenance.
- The active scientific scope is cross-predictor evidence on one shared
  3DSSG/3RScan target.
  ReplicaSSG/FROSS is excluded from the submission route.
- H001 now uses the factor contract `T_e` = predicate/family semantics, `G_e`
  = raw predicate-independent same-pair geometry, `Z_e` = source relation score,
  and `C_e = sigmoid(h_a(Phi(T_e,G_e)))`, with `Z_e notin C_e` and
  `S_e = F(Z_e,C_e)`. `C_e` scores a constructed positive/counterfactual
  target and is not a physical-validity probability. The legacy
  `p_geom_valid`-only condition is not
  true `G_e`-only because its calibrator retains `T_e`/interaction features.
- `h001_factor_isolation_protocol_v1` implementation is complete. The later
  `train_only_reestablishment_v1` strict reconstruction is also complete and
  passes its frozen internal-dev/final aggregate gates. Detailed provenance
  classification is owned by `docs/paper.md` and the experiment report rather
  than duplicated in this workspace index.
- The frozen uncertainty-sensitivity audit reports decidable-only V,
  uncertainty rate, pessimistic V, and coverage on all three sources. The
  structured-product deltas remain negative under every violation definition, and
  the supplement now exposes constructed-target discrimination,
  scan-cluster sensitivity, family composition, and uncertainty results.
- H001_v2 fixed-`tau*` and pooled lambda-soft reranking are diagnostic
  candidate evidence only; they do not replace the current RelCompat3D main
  result route.
- Remaining paper-work class: enter author profiles/countries and reciprocal
  reviewer in OpenReview, decide the final public license/post-acceptance
  artifact URL, and collect the optional independent human labels. The
  human-alignment guide, mandatory-adjudication validator, Human V evaluator,
  and Codex--human evaluator are frozen and dry-run verified; no human number
  is claimed while their status remains awaiting labels.
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
- `paper_nonsub/`: H001 non-submission manuscript variant containing the
  Codex proxy-audit appendix and explicit non-human limitations.
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
