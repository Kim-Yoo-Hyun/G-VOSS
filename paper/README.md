# Paper Workspaces

Last updated: 2026-07-17 KST

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

- Paper-facing title: `Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking for 3D Scene Graphs`
- Target venue route: `paper/aaai/`
- Historical alternate route: `archive/paper/iccv/`
- Current claim style: scoped relation-reliability paper for
  3D Scene Graph relations whose consistency can be assessed from reconstructed
  ordered-pair geometry.
- Non-claim: broad open-vocabulary 3DSSG generation improvement.
- Active AAAI-27 Docker build: `paper/aaai/main_aaai27.pdf`, SHA256
  `5a3012f8d529e147f647c3a92d388940f675b2f98728371429a3a965e4d4f46f` (9 pages: main text
  through page 7, where references begin and continue through page 9),
  `paper/aaai/supplement_aaai27.pdf`, SHA256
  `a3138be52be01c5d30b0e9494c9f2cae0fa681868b8459fcd0281d4f274b6e8f`
  (5 pages), and
  `paper/aaai/reproducibility_checklist_aaai27.pdf`, SHA256
  `1c3efa0baeb0514da8b8587386cbe7ec1260b2358f5f9f04ad8cb2d015419d`
  (2 pages). Final main log:
  `logs/h001_main_claim_strengthening_final_20260717_193117.log`; final supplement log:
  `logs/h001_supplement_claim_strengthening_20260717_193117.log`; image:
  `h001-aaai27-tex:20260712`. Type 3 fonts, unresolved references/citations,
  LaTeX errors, and overfull boxes are zero.
- The active submission excludes Codex-derived physical-validity numbers. The
  separately built `paper/paper_nonsub/main_nonsub.pdf`, SHA256
  `c7518a7a2eec73783a87f4d5733b0fcd495fee3e50c6e4d4f9850cf7548496b9`,
  contains the reviewer-verified LLM diagnostic for internal/user review only.
- The manuscript narrative now proceeds failure -> structural cause -> factor
  isolation -> method -> experiments -> discussion/limitations. It uses six
  top-level sections; Problem Setup is inside Method, and Setup/results are
  grouped under Experiments. Figure 1 is failure-grounded,
  Figure 2 uses percentage axes and labels K=5/10/20/50/100 without a selected
  point marker. Figure 3 is a pair--evidence--outcome grid with proximity and
  relative-vertical corrections plus one residual support/contact case. The main comparison is one joint
  Recall/Violation table placed before its interpretation, followed by a
  single-column K=50/100 six-control table using the same public/full
  family-aware ranking procedure. Both tables use percentage points and concise condition
  names; all three figures are included as vector PDFs. Figure 3 additionally
  uses point shape and box line style so subject/object identity survives
  grayscale printing.
- Most recent verified OpenReview field bundle:
  `release/h001_aaai27_openreview_20260717_193626/`. Its anonymous 198-record
  source/evidence ZIP passes extracted-source Docker rebuild and canonical
  text-identity checks. The prior
  Replica-disclosure and other superseded PDFs are indexed under
  `archive/paper/aaai_snapshots/`; the 2026-07-12 bundle and compact tarball are
  historical handoff snapshots.
- RelCompat3D is framework-first. Its primary decision rule applies the strict
  train-only relation-consistent product within proximity/vertical
  source-family positions and preserves support/contact ordering. The all-family
  product, matched rank-average/RRF, and the nonlinear model are
  comparisons; none is claimed universally dominant. Pooled compatibility
  is an ablation, RRF a strong comparator, and compatibility-only ranking a
  control. Internal metric keys no longer appear in manuscript prose or
  rendered figures.
- Linked-counterfactual margin fitting with exact proximity symmetry and joint
  endpoint-swap/inverse-predicate transformation averaging defines the main
  compatibility model. All
  main comparators, uncertainty results, figures, and tables were regenerated
  together under `structured_main_v1/`; the internal orbit name is retained
  only for artifact provenance.
- Transformation averaging has one compact exact-consistency proposition;
  family-sequence preservation is explained as a direct construction property.
  The supplement proves or verifies both. It also reports three strict
  train-only verifier-primitive holdouts: exact-scalar removal preserves nearly
  the full result, while broader removal exposes the remaining dependence on
  correlated geometry.
- The supplement reports paired scan-cluster intervals for all five K values
  and a bounded CPU benchmark for the re-ranking layer. The latter times only
  compatibility, transformation averaging, sorting, and output assembly from
  preloaded rows; it is not end-to-end source inference latency.
- Main Table 1 directly includes the matched MLP under the same ranking procedure; pooled product is
  now a supplement-only family-conditioning ablation. A nine-condition
  train-only counterfactual-policy sensitivity varies thresholds, negative
  count, and pairwise-loss weight. All variants preserve the three-source
  K=50/100 point-estimate direction, with at most `.0023/.0011` R/V change at
  K=50 and `.0040/.0020` at K=100.
- The active scientific scope is cross-predictor evidence on one shared
  3DSSG/3RScan target.
  ReplicaSSG/FROSS appears only as a supplemental retrospective transfer stress
  test with all K values and explicit K=100 saturation.
- H001 now uses the factor contract `T_e` = predicate/family semantics, `G_e`
  = predicate-independent pair-geometry measurements, `Z_e` = source relation score,
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
- `preview.md`: current paper handoff snapshot. Owns the current claim,
  evidence summary, canonical build/release pointers, and remaining user tasks.
- `outline.md`: current six-section manuscript plan. Owns the causal narrative,
  contribution statements, section responsibilities, and figure/table placement.
- `method.md`: accessible method guide. Owns factor definitions, training
  targets and losses, exact transformation consistency, score combination, and
  family-aware ranking in implementation-faithful mathematical form.
- `experiment.md`: accessible experiment guide. Owns evaluation questions,
  comparison methods, metrics, uncertainty analysis, statistical procedure,
  and result-reading rules.
- `progress.md`: current completion ledger. Owns completed components, fixed
  decisions, deferred tracks, and remaining work; it is not a historical run log.
- `draft.md`: first-pass manuscript prose. Owns the readable paper body from
  title through conclusion before final venue-specific compression.
- `figures.md`: complete Figure 1--3 redraw specification. Owns canvas and panel
  composition, visual flow, exact values and plot coordinates, source cases,
  captions, and figure non-claims.
- `risk.md`: reviewer-risk register. Owns attack surface, weakness/mitigation
  tracking, and priority order for logic, novelty, evidence, and
  reproducibility defenses.
- `review.md`: consolidated three-persona review. Owns the current assessment of
  novelty, experimental validity, writing/presentation, and submission readiness.
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
4. `paper/outline.md`
5. `paper/method.md`
6. `paper/experiment.md`
7. `paper/figures.md`
8. `paper/risk.md`
9. `paper/review.md`
10. `paper/appendix.md`
11. `paper/draft.md`
12. `paper/aaai/README.md`

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
- If completion status, deferred tracks, or remaining work changes, update
  `progress.md`.
- If paper structure, contribution wording, or table/figure placement changes,
  update `outline.md`.
- If the implemented factorization, objectives, algebraic consistency, or
  ranking procedure changes, update `method.md`.
- If comparisons, metrics, statistical procedures, or evaluation interpretation
  changes, update `experiment.md`.
- If prose changes, update `draft.md` or the active venue source under
  `paper/aaai/`.
- If figure claims, source rows, values, or captions change, update
  `figures.md` before regenerating assets.
- If reviewer attack mitigation changes, update `risk.md`.
- If supplement/appendix provenance or detailed caveat accounting changes,
  update `appendix.md`.
- If build commands, style files, or PDF status change, update the relevant
  venue folder README.
