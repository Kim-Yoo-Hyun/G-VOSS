# H001 Appendix And Supplement Plan

Last updated: 2026-05-28 KST

This file owns appendix/supplement material that is too detailed for the AAAI
main text but important for reviewer defense. It is not a new experiment-result
root. Source metrics and row artifacts remain under
`experiments/H001_geom_reliability/` and hypothesis-stage calibration artifacts
remain under `hypothesis/CAND-001/H001_geometry-grounded-verification/`.

## Current Appendix Role

The current main paper keeps three tables in the AAAI body: fixed H001 scope,
source-specific claim boundary, and Open3DSG-first source results. Appendix
material should defend provenance, denominator discipline, and residual risk
without broadening the claim.

Use this appendix only for:

- calibrator and threshold provenance;
- detailed controls and GT verifier evidence;
- detailed Open3DSG caveat/coverage accounting;
- detailed family rows and qualitative failure taxonomy;
- optional `relative_horizontal` scope-boundary diagnostics, if reported only
  as limitation/future-work evidence;
- optional `attachment_deferred` future-upgrade protocol, if reported only as a
  next-step physical relation family;
- Qwen-VL runtime status only as third-source extension material.

Do not use it to hide caveats that must remain visible in the main text.

## Appendix Table A1: Calibrator And Threshold Provenance

| Component | Frozen source | Key values / scope | Held-out use | Reviewer defense |
| --- | --- | --- | --- | --- |
| Predicate-family map | `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/predicate_mapping.json`; H001 tools `select_scope.py`, `export_calibration.py`, `prepare_open3dsg_adapter.py` | `support_contact`: `standing on`, `lying on`, `supported by`; `proximity`: `close by`; `relative_vertical`: `higher than`, `lower than` | Defines the H001 geometry-checkable denominator before source-result reporting; exact predicate-label recall is still used | Prevents post-hoc family selection and avoids relaxing recall labels into family matches |
| H001 denominator policy | `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/denominator_policy.json` | 7,505 GT rows; 2,545 in-scope GT rows; support/contact 1,199, proximity 1,128, relative vertical 218 | Used for VL-SAT and Open3DSG source-result metrics | Makes excluded families and denominator accounting explicit |
| Initial OBB rule thresholds | `artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/thresholds.json` | `h001-rules-v0`; `near_distance_norm_max=1.5`; `z_order_margin_m=0.02`; `z_gap_abs_max_m=0.1`; `geometry_score_pass_min=0.6` | Historical smoke-test rule source, not final held-out tuning | Shows rule development started before held-out source metrics; final claim uses later point/subtype policy |
| Proximity hard status policy | `hypothesis/.../tools/join_predictions.py` | Satisfied if projected overlap exists or `normalized_distance_xy <= 2.5`; violated if `normalized_distance_xy >= 3.5`; otherwise uncertain | Applied during row-preserving geometry join for prediction rows | Defends the distance-family rule as fixed and identity-preserving, not tuned per source result |
| Relative-vertical hard status policy | `hypothesis/.../tools/join_predictions.py` | Predicate-aligned vertical relation satisfied when aligned delta is at least `0.25m` and normalized aligned delta at least `0.15`; violated when both are at most `-0.25m` and `-0.15` | Applied during geometry join for `higher than` / `lower than` rows | Makes the vertical-order rule auditable and separate from semantic score |
| Support/contact OBB fallback | `hypothesis/.../tools/join_predictions.py` | Satisfied by projected overlap plus vertical gap `<=0.30m`; violated by no overlap, normalized XY distance `>=2.0`, and vertical gap `>=0.30m`; otherwise uncertain | Used as fallback/variant; primary support/contact policy uses point/subtype evidence when available | Prevents support/contact from becoming an unqualified OBB-only heuristic |
| Point support thresholds | `hypothesis/.../tools/export_point_support.py` | `ply_points_v1`; local vertical gap max `0.10m`; relaxed gap `0.15m`; min support points `10`; primary XY expansion `0.10m`; expansion steps `0.00/0.05/0.10/0.20m` | Supplies point/local evidence for support/contact verification and audit | Shows support/contact decisions use local point evidence, not only box overlap |
| Support/contact subtype thresholds | `hypothesis/.../tools/apply_verifier_v2.py` | `h001-verifier-v2`; satisfied score `0.70`; uncertain score `0.40`; low-gap pass/fail `0.08/0.18m`; robust-gap pass `0.10m`; soft penetration pass/max `0.15/0.45m`; plane gap pass/fail `0.08/0.22m` | Used for subtype-aware support/contact status variants and final `point_subtype` policy | Defends family-specific rules as declared operating points with uncertain handling |
| Calibration export | `artifacts/calibration/train_dev_calib/{manifest.json,table.jsonl,negatives.jsonl}` | 32 scans, 225 subgraphs, 2,565 positives, 3,244 counterfactual negatives; negative strategies include proximity far pair, support replacement, and vertical inversion | Fit source for `p_geom_valid`; does not use H001 held-out prediction failures | Separates calibrator fitting from held-out source-result reporting |
| Pooled calibrator | `artifacts/calibration/p_geom_valid_smoke/model.json`; `metrics.json` | Logistic model over geometry numeric features plus family/predicate indicators; train rows 4,616; dev rows 1,193; dev Brier 0.0495, AUROC 0.9822, AUPRC 0.9735 | Produces `probabilistic_recalibrated` score `semantic_score * p_geom_valid` | Establishes `p_geom_valid` as a learned reliability score, not a binary rule label |
| Family-specific calibrator | `artifacts/calibration/p_geom_valid_family/model.json`; `metrics.json` | Separate logistic model per family; dev AUROC support/contact 0.9831, proximity 1.0000, relative vertical 0.9982 | Produces the stricter `family_specific_p_geom_valid` operating point | Tests whether the result depends on pooling across relation families |
| GT verifier evaluation | `artifacts/evaluation/vlsat_closed_set/hardened/gt_eval/{metrics.json,report.md}` | 2,545 GT positives and 2,545 GT-derived negatives; positive nonviolated 0.9972; negative nonsatisfied 0.9694; AUROC/AUPRC 0.9779/0.9737 | Held-out verifier check; not used to fit thresholds or calibrators | Defends the geometry signal against the "hand-coded verifier" objection |
| Open3DSG caveat wording | `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md` | Averaged-BLIP variant, filtered train/dev, 377/388 covered H001 contexts, exact-label 2,545 denominator, residual calibration risk | Required wording for main source-result table and discussion | Prevents broad Open3DSG/SOTA overclaiming |

## Open3DSG Caveat Consistency Pass

Status: `completed_2026_05_27`

| Location | Required caveats | Status |
| --- | --- | --- |
| AAAI Experimental Setup | averaged-BLIP variant, checkpoint selected by train-dev loss, filtered train/dev split, covered H001 scope, `validation_missing_preprocessed:11`, exact-label 2,545 denominator | present in `paper/aaai/sec/5_experiments.tex` |
| AAAI Main Source Results Table | Open3DSG-first source role, averaged-BLIP, filtered train 3,744/3,852, validation 156/160, covered H001 377/388, exact-label denominator 2,545, `validation_missing_preprocessed:11`, residual calibration risk | present after 2026-05-27 caption update in `paper/aaai/sec/6_results.tex` |
| AAAI Results prose | within-source reliability, no official non-averaged Open3DSG leaderboard claim, same checkpoint/row contract/covered denominator | present in `paper/aaai/sec/6_results.tex` |
| Experiment artifact Table 6 | Open3DSG row must carry a caveat note or point to frozen caveat wording | present after 2026-05-27 regeneration from `build_tables.py` |
| Paper risk register | P2 provenance and Open3DSG caveat visibility risk | updated in `paper/risk.md` |

## Figure 3 Decision

Current decision: no new Figure 3 rendering work is required before the next
paper pass. The preferred draft is the geometry-backed point-cloud panel in
`paper/generated/figures/figure3_geometry_panels.svg`. A rendered scene-crop
upgrade is optional only if a deterministic crop/render path is added for the
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

## Attachment Deferred Upgrade Boundary

`attachment_deferred` is the preferred future relation-family upgrade if H001
is extended beyond the current AAAI scope. It is not current metric evidence.
Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run,
G1c point/surface validation, G2 conservative verifier-policy design, G3
train-dev calibration/counterfactual route, G4 GT policy smoke, G4b
error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a
pooled strict calibration fit, G5b bounded source scoring preflight, and G5c
full-source protocol freeze are complete with status
`attachment_deferred_full_source_protocol_frozen_no_metrics`.
The family adds 967 GT rows (`attached to`, `hanging on`, `connected to`) and
would increase the candidate denominator to 3,512 if validated. Candidate rows
exist for VL-SAT (77,748) and Open3DSG (57,300), but both are currently
verification-unsupported. Its conceptual fit is strong because attachment and
hanging have physical preconditions, G2 freezes 9 subtype policies with
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
rows. No full-source scoring or source metrics are computed. Promotion requires
full-source scoring, two-source metrics, controls, bootstrap CI, and failure
analysis; main-claim promotion also requires explicit final user confirmation.
G1c
produced 36/36 schema-valid point/surface-ready evidence rows with 0 validation
errors and no forbidden verifier/metric fields; 27/36 rows have near-contact
points under the 0.05m diagnostic threshold. A function-reasoning example may
be used only as a secondary pilot after the relation-level verifier and metrics
pass.

## Qwen-VL Boundary

Qwen-VL remains a third semantic source / modern VLM extension. It is not a
VL-SAT/Open3DSG replacement and not main paper metric evidence until all
remaining shards, parser validation, prediction aggregation/export, geometry
join, metrics, controls, bootstrap CI if reported, and audit are complete under
Docker.

## Validation

- Docker `table_builder` image rebuild:
  `logs/h001_geom_image_rebuild_table6_caveat_20260527_202425.log`, exit 0.
- Docker `table_builder` rerun:
  `logs/h001_table_builder_caveat_consistency_20260527_202425.log`, exit 0.
- AAAI PDF rebuild:
  `logs/h001_aaai_pdf_build_appendix_caveat_20260527_202734.log`, exit 0.
- PDF status: `paper/aaai/main.pdf`, 9 pages, US Letter, no missing citations,
  undefined references, overfull hboxes, LaTeX errors, or AAAI package errors
  found in the latest check.
