# H001 Appendix And Supplement Plan

Last updated: 2026-06-25 KST

This file owns appendix/supplement material that is too detailed for the AAAI
main text but important for reviewer defense. It is not a new experiment-result
root. Source metrics and row artifacts remain under
`experiments/H001_geom_reliability/` and hypothesis-stage calibration artifacts
remain under `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/`.

## Current Appendix Role

The current main paper keeps the joint five-budget source table and the
K=50/100 routed ablation table in the AAAI body. Detailed confidence intervals,
family slices, method diagnostics, and external transfer remain supplemental.

## ReplicaSSG/FROSS Negative-Transfer Appendix

The disclosure decision is to report the final unchanged-method
ReplicaSSG/FROSS evaluation as a retrospective transfer stress test. The
separate AAAI supplement source is `paper/aaai/supplement.tex`, with the result
table in `paper/aaai/sec/a_external_transfer.tex`. It reports all K values over
11 scenes, 4,293 candidates, and 172 exact-label GT relations; paired joint
improvements at K=10 and K=50; the K=100 saturation; the 44.19% candidate
ceiling; and source-score quantization. It must not be framed as untouched
confirmation or established dataset-level generalization.
Appendix material should defend provenance, denominator discipline, and
residual risk without broadening the claim.

Use this appendix only for:

- calibrator and threshold provenance;
- detailed controls and GT verifier evidence;
- detailed Open3DSG caveat/coverage accounting;
- detailed family rows and qualitative failure taxonomy;
- optional `relative_horizontal` scope-boundary diagnostics, if reported only
  as limitation/future-work evidence;
- optional `attachment_deferred` future-upgrade protocol, if reported only as a
  next-step physical relation family;
- Qwen-VL full-validation extension evidence only as third-source material,
  unless explicitly promoted.
- low-K K = `{5,10,20,50,100}` provenance/details for the main table; K=1
  remains sanity-check only. Current point-metric roots are
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/`
  and
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`.

Do not use it to hide caveats that must remain visible in the main text.

## Appendix Table A1: Calibrator And Threshold Provenance

| Component | Frozen source | Key values / scope | Held-out use | Reviewer defense |
| --- | --- | --- | --- | --- |
| Predicate-family map | `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/predicate_mapping.json`; H001 tools `select_scope.py`, `export_calibration.py`, `prepare_open3dsg_adapter.py` | `support_contact`: `standing on`, `lying on`, `supported by`; `proximity`: `close by`; `relative_vertical`: `higher than`, `lower than` | Defines the H001 geometry-checkable denominator before source-result reporting; exact predicate-label recall is still used | Prevents post-hoc family selection and avoids relaxing recall labels into family matches |
| H001 denominator policy | `results/h001_geom_reliability/full_validation_transition/scope_contract/{scope_contract.json,report.md}` | 11,254 GT rows; 3,972 in-scope measured-family GT rows; support/contact 1,816, proximity 1,766, relative vertical 390 | Used for VL-SAT full-validation and Open3DSG full-validation source-result metrics | Makes excluded families and denominator accounting explicit |
| Initial OBB rule thresholds | `artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/thresholds.json` | `h001-rules-v0`; `near_distance_norm_max=1.5`; `z_order_margin_m=0.02`; `z_gap_abs_max_m=0.1`; `geometry_score_pass_min=0.6` | Historical smoke-test rule source, not final held-out tuning | Shows rule development started before held-out source metrics; final claim uses later point/subtype policy |
| Proximity hard status policy | `src/geocalib/join_predictions.py` | Satisfied if projected overlap exists or `normalized_distance_xy <= 2.5`; violated if `normalized_distance_xy >= 3.5`; otherwise uncertain | Applied during row-preserving geometry join for prediction rows | Defends the distance-family rule as fixed and identity-preserving, not tuned per source result |
| Relative-vertical hard status policy | `src/geocalib/join_predictions.py` | Predicate-aligned vertical relation satisfied when aligned delta is at least `0.25m` and normalized aligned delta at least `0.15`; violated when both are at most `-0.25m` and `-0.15` | Applied during geometry join for `higher than` / `lower than` rows | Makes the vertical-order rule auditable and separate from semantic score |
| Support/contact OBB fallback | `src/geocalib/join_predictions.py` | Satisfied by projected overlap plus vertical gap `<=0.30m`; violated by no overlap, normalized XY distance `>=2.0`, and vertical gap `>=0.30m`; otherwise uncertain | Used as fallback/variant; primary support/contact policy uses point/subtype evidence when available | Prevents support/contact from becoming an unqualified OBB-only heuristic |
| Point support thresholds | `src/geocalib/export_point_support.py` | `ply_points_v1`; local vertical gap max `0.10m`; relaxed gap `0.15m`; min support points `10`; primary XY expansion `0.10m`; expansion steps `0.00/0.05/0.10/0.20m` | Supplies point/local evidence for support/contact verification and audit | Shows support/contact decisions use local point evidence, not only box overlap |
| Support/contact subtype thresholds | `src/geocalib/apply_verifier_v2.py` | `h001-verifier-v2`; satisfied score `0.70`; uncertain score `0.40`; low-gap pass/fail `0.08/0.18m`; robust-gap pass `0.10m`; soft penetration pass/max `0.15/0.45m`; plane gap pass/fail `0.08/0.22m` | Used for subtype-aware support/contact status variants and final `point_subtype` policy | Defends family-specific rules as declared operating points with uncertain handling |
| Calibration export | `artifacts/calibration/train_dev_calib/{manifest.json,table.jsonl,negatives.jsonl}` | 32 scans, 225 subgraphs, 2,565 positives, 3,244 counterfactual negatives; negative strategies include proximity far pair, support replacement, and vertical inversion | Fit source for `p_geom_valid`; does not use H001 held-out prediction failures | Separates calibrator fitting from held-out source-result reporting |
| Pooled calibrator | `artifacts/calibration/p_geom_valid_smoke/model.json`; `metrics.json` | Logistic model over geometry numeric features plus family/predicate indicators; train rows 4,616; dev rows 1,193; dev Brier 0.0495, AUROC 0.9822, AUPRC 0.9735 | Produces `probabilistic_recalibrated` score `semantic_score * p_geom_valid` | Establishes `p_geom_valid` as a learned reliability score, not a binary rule label |
| Family-specific calibrator | `artifacts/calibration/p_geom_valid_family/model.json`; `metrics.json` | Separate logistic model per family; dev AUROC support/contact 0.9831, proximity 1.0000, relative vertical 0.9982 | Produces the `family_conditional_risk` operating point | Tests whether geometry risk should be pooled or calibrated by relation family |
| GT verifier evaluation | `experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/{metrics.json,report.md}` | 3,972 GT positives and 3,972 GT-derived negatives; positive nonviolated 0.9965; negative nonsatisfied 0.9673; AUROC/AUPRC 0.9772/0.9729; Brier 0.0543 | Held-out verifier check; not used to fit thresholds or calibrators | Defends the geometry signal against the "hand-coded verifier" objection |
| Open3DSG caveat wording | `experiments/H001_geom_reliability/open3dsg_official_route_v1/evaluation/`; recovery details in `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` | Main route: public predictions from 533 contexts evaluated on the official 548-context/3,972-GT target, with no predictions in 15 missing contexts. Eligible-533 and recovered-548 are sensitivities. | Required wording for setup and supplement | Prevents broad Open3DSG/SOTA overclaiming and avoids presenting recovery as the unmodified route |

## Full Official Validation Transition

Status: `full_validation_primary_route_public_full_target`

The paper-facing primary route is now the full official `3DSSG_subset`
validation split. VL-SAT full-validation is the controlled-anchor result, and
Open3DSG public-pipeline predictions are evaluated on the complete official
548-context target, with no predictions assigned to the 15 missing contexts.
The eligible 533-context and recovered 548-context routes remain supplement
sensitivities. The target full split has 157
scans, 548 contexts, 36,808 candidate directed pairs, 957,008 expected VL-SAT
prediction rows, 11,254 GT rows, and 3,972 in-scope measured-family GT rows.

Scope contract:

```text
results/h001_geom_reliability/full_validation_transition/scope_contract/
```

This artifact freezes the denominator, selected scans, context list, local
payload/preprocess readiness, output paths, and command templates. It is not
metric evidence.

Reviewer-defense wording:

```text
Final family mapping, verifier policies, counterfactual construction, and
p_geom_valid calibration are fixed from train/train-dev artifacts before
validation source-result reporting. H001-Mini is hypothesis/feasibility
evidence and is not used as a paper metric or calibrator-fitting split.
```

The AAAI source-result table should use the full-validation route only:
VL-SAT full-validation plus Open3DSG full-validation 548/548 recovery. Required
appendix note: public/full-target is primary; recovered 548 is a sensitivity
using `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed view regeneration for two
scans, while the 533/548 covered branch shows the unmodified source-route
denominator behavior. Historical 127-scan Open3DSG results should appear only
in an appendix/sensitivity table comparing the old 377/388 branch against the
R2 388/388 branch.

## Historical Open3DSG Sensitivity Table Policy

Status: `r2_388_representative_historical_sensitivity`

Use this table only in appendix/supplement or paper-planning artifacts. Do not
replace the main source-result table with it, because the main paper-facing
denominator is the full official validation route.

| branch | role | contexts | R2 status / caveat | use |
| --- | --- | ---: | --- | --- |
| old avg-BLIP branch | comparison row | 377/388 | clean v14 raw provenance; `validation_missing_preprocessed:11` | shows historical covered-loadable behavior |
| R2 covered-recovery branch | representative historical sensitivity | 388/388 | complete downstream metrics/bootstrap; raw process exits 137 after finalization; provenance review confirms clean-return raw files are row/predicate-score equivalent after excluding run metadata | shows missing 11 contexts did not drive the trend |

R2-minus-old effect size: R@100 changes by about +0.28 percentage points across
the main Open3DSG conditions, while Violation@100 changes by +0.00 to +0.13
points. This is robustness evidence, not a new main-result route.

## Open3DSG Caveat Consistency Pass

Status: `full_validation_primary_route_regenerated`

2026-06-05 re-check result: the AAAI source-result route now uses VL-SAT
full-validation and Open3DSG `recovery_relaxed_views_min2/` as the paper-facing
primary route. Historical 127-scan / averaged-BLIP wording is sensitivity
history only and should not be used for main result claims.

| Location | Required caveats | Status |
| --- | --- | --- |
| AAAI Experimental Setup | full official validation scope; selected official non-avg Open3DSG checkpoint; filtered train/dev provenance; 548/548 recovery branch; 533/548 covered branch as sensitivity; historical 377/388 vs R2 388/388 only as appendix sensitivity | updated in `paper/aaai/sec/5_experiments.tex` |
| AAAI Table 3 / Main Source Results Table | Open3DSG-first source role, full-validation 548/548 recovery branch, exact-label denominator 3,972, recovery-policy caveat, residual calibration risk; no historical 127-scan rows in main table | updated in `paper/aaai/sec/6_results.tex` |
| AAAI Results prose | within-source reliability, no Open3DSG leaderboard/SOTA claim, same checkpoint/row contract/full-validation denominator, recovery-policy disclosure | updated in `paper/aaai/sec/6_results.tex` |
| AAAI Limitations | selected non-avg checkpoint, filtered train/dev provenance, recovery-policy branch, scoped relation-reliability interpretation, no broad SOTA claim | updated in `paper/aaai/sec/7_limitations.tex` |
| Experiment artifact Table 6 | Open3DSG row must carry selected non-avg checkpoint, filtered train/dev, full-validation exact-label denominator, 548/548 recovery policy, residual calibration-risk note, 533/548 full-validation sensitivity, and appendix-only historical 377/388 vs R2 388/388 sensitivity | updated in `results/h001_geom_reliability/tables/table6_cross_source_status.*` |
| Paper risk register | P2 provenance and Open3DSG caveat visibility risk | updated in `paper/risk.md` |
| R1 exact non-avg BLIP retry | Supplies the selected full-validation checkpoint provenance; historical 127-scan avg-BLIP remains sensitivity evidence | completed and selected official non-avg checkpoint; downstream non-avg and full-validation recovery artifacts are recorded under `sources/open3dsg/non_avg/` and `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` |

## Figure 3 Decision

Current decision: Figure 3 uses two geometry-identifiable corrections
(`open3dsg_case_001` proximity and `open3dsg_case_019` relative vertical) plus
one residual support/contact violation (`open3dsg_case_026`). The preferred
draft is the geometry-backed point-cloud panel in
`paper/generated/figures/figure3_geometry_panels.svg`. A rendered scene-crop
upgrade is optional only if a deterministic crop/render path preserves these
same locked case IDs.

## Relative Horizontal Boundary

`relative_horizontal` is not part of the current main claim. The Docker
scope audit, coordinate audit, and bucket inspection are complete, but they are
diagnostic rather than metric evidence. The current recommendation is
`do_not_promote_relative_horizontal_to_main_claim`: the selected scan frame has
inverse consistency 1.0 and wrong-frame gap 0.1231, but `front`/`behind`
remains ambiguous with strict purity 0.7445 and large ambiguity buckets. The
current AAAI-path decision is to freeze this as appendix/limitation evidence,
not to run expanded-family metrics. If mentioned, use it only to show
disciplined scope control and the future validation requirement: targeted
`front`/`behind` visual/frame-metadata analysis before any expanded-family
metrics.

`relative_lateral` was tested as a narrower left/right-only split after the
full `relative_horizontal` audit. It is also not part of the current main
claim. The policy-freeze artifact records 2,264 GT rows and selected frame
`scan_left_neg_x_front_neg_y`, with lateral-only strict purity 0.8005 and
distinct-left-axis wrong-frame gap 0.0998. However, the train/dev policy lock is
caveated: train positive strict purity is 0.8738, but dev positive strict purity
is only 0.6975. The dev failure diagnosis shows that strict contradictions are
72 rows / 36 physical pairs concentrated in two scans, about half involve
same-label object pairs, and uncertain rows are mostly orthogonal-axis dominance
cases. Current decision: stop `relative_lateral` as appendix/future-work
boundary evidence and do not run paper-facing source metrics from the current
strict policy.

## Attachment Deferred Upgrade Boundary

`attachment_deferred` is the preferred future relation-family upgrade if H001
is extended beyond the current AAAI scope. It is not current main-claim
evidence.
Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run,
G1c point/surface validation, G2 conservative verifier-policy design, G3
train-dev calibration/counterfactual route, G4 GT policy smoke, G4b
error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a
pooled strict calibration fit, G5b bounded source scoring preflight, G5c
full-source protocol freeze, and G5d full-source scoring/metrics/controls/
bootstrap are complete with status
`attachment_deferred_g5d_full_source_metrics_ready`.
The family adds 967 GT rows (`attached to`, `hanging on`, `connected to`) and
would increase the candidate denominator to 3,512 if validated. Candidate rows
exist for VL-SAT (77,748) and Open3DSG (57,300). G5d shows source-level
evidence, but it is still not sufficient for main-claim promotion. Its
conceptual fit is strong because attachment and hanging have physical
preconditions, G2 freezes 9 subtype policies with
conservative near-contact, uncertain-band, clear-far, contact-point, and
contact-patch defaults, G3 prepares 315 positive seeds plus 446 counterfactual
seeds with held-out overlap 0, and G4 applies the frozen policy to 36 smoke rows
plus 761 train/dev seed rows. G4 results are positive nonviolated 0.9048,
counterfactual nonsatisfied 0.8274, positive strict satisfied 0.3841,
counterfactual strict violated 0.4574, and uncertain rate 0.4323. G4b freezes
436 review cases, a 50-row visual sanity queue, 121 strict positive candidates,
204 strict negative candidates, 77 false-satisfied counterfactuals, 30
false-violated positives, and 329 uncertain rows. G4c freezes 325 strict
calibration rows and excludes 436 non-strict rows; `connected to` has no dev
strict rows. G5a fits pooled model
`h001-attachment-deferred-p-geom-valid-strict-v1` with dev Brier/NLL/ECE
0.0010/0.0077/0.0071 and dev AUROC/AUPRC 1.0/1.0 on 83 strict rows. These
metrics are calibration-readiness only because the strict subset is
policy-selected and nearly separable. G5b scores 120 scan-diverse bounded
source rows, with evidence ready 120/120 and validation errors 0. G5c freezes
69 deterministic full-source shards for 135,048 rows, source-specific covered
denominators, metric conditions, and controls: VL-SAT covers 967/967 attachment
GT rows while Open3DSG covers 768/967 and must report 199 missing exact-label GT
rows. G5d then scores 135,048 full-source rows with validation errors 0 and
computes source metrics/controls/bootstrap. It is not main-claim evidence
because `attached to` remains noisy, `connected to` lacks dev strict rows,
Open3DSG misses 199 exact-label GT rows, and additional failure/visual audit is
still needed. Main-claim promotion also requires explicit final user
confirmation.
G1c
produced 36/36 schema-valid point/surface-ready evidence rows with 0 validation
errors and no forbidden verifier/metric fields; 27/36 rows have near-contact
points under the 0.05m diagnostic threshold. A function-reasoning example may
be used only as a secondary pilot after the relation-level verifier and metrics
pass.

The legacy nine-subtype ontology is superseded for future development by
`subtype_redesign_v2/`, which separates predicate semantics, physical
mechanism, and observability/applicability. Its 761-row migration finds that
199/325 legacy strict rows used `ambiguous_*` subtypes and freezes 311 candidate
strict rows plus a 100-row mechanism-review queue. The 190,722-row official-
validation route audit assigns 74,433 rows to bidirectional compatibility,
19,287 to positive-only evidence, and 97,002 to abstention. A raw selective
product fails both source K=100 gates. A bounded multiplier passes VL-SAT K=100
but fails Open3DSG K=100 and VL-SAT K=50. These are transparent retrospective
development diagnostics, not supplement result evidence, and do not change
the active manuscript.

## Relative-Size Supplement Promotion

The user approved `relative_size` only as one main-text scope sentence and a
full technical-supplement section. `paper/aaai/sec/a_relative_size.tex` owns the
1,061/117/157 firewall, T/G/T-by-G feature contract, disjoint point-view
verifier, all-source K=`{5,10,20,50,100}` paired intervals, four-family K=100
result, global composition change, point/OBB baselines, rank-average boundary,
and residual same-segmentation construct caveat. The family stays out of Figure
1, the contribution list, and the headline learned-method evidence because the
fixed robust-point rule matches or improves its Violation.

## Qwen-VL Boundary

Qwen-VL remains a third semantic source / modern VLM extension. It is not a
VL-SAT/Open3DSG replacement. Full official validation downstream is complete for
the extension route: 157 scans / 548 contexts / 110,424 query rows / 46,506
inferable input rows / 35,131 exported predictions / 32,236 in-scope
predictions / 3,972 measured-family GT rows, with parser validation, adapter
export, geometry join, metrics/controls, bootstrap CI, 31,881 failure rows, and
36 deterministic qualitative cases. Keep it in appendix/extension framing
unless the user explicitly promotes it into the main claim.

## Validation

- Docker full-validation caveat consistency pass after R1 selection:
  the paper-facing route is now Open3DSG
  `full_validation/recovery_relaxed_views_min2/` with the selected official
  non-avg checkpoint, filtered train/dev provenance, exact-label 3,972
  denominator, recovery-policy caveat, 533/548 covered-branch sensitivity note,
  and residual calibration-risk wording. Historical `open3dsg_paper_caveats`
  remains local to the 127-scan averaged-BLIP branch.
- Docker `table_builder` image rebuild:
  `logs/h001_geom_image_rebuild_table6_caveat_20260527_202425.log`, exit 0.
- Docker `table_builder` rerun:
  `logs/h001_table_builder_caveat_consistency_20260527_202425.log`, exit 0.
- AAAI PDF rebuild:
  `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`, exit 0.
- Historical PDF status: the transient family-main `main.pdf` had 10 pages,
  US Letter, technical content pages 1-7, references pages 8-9, checklist page
  10; Type 1 fonts only; no
  missing citations, undefined references, overfull hboxes, LaTeX errors, or
  AAAI package errors found in that targeted check. Superseded PDFs are indexed
  under `archive/paper/aaai_snapshots/`; current outputs are the three
  `paper/aaai/*_aaai27.pdf` files.
