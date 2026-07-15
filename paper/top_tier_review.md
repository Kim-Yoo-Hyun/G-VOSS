# Top-Tier Style Review for RelCompat3D

Last updated: 2026-07-14 KST

## Compared Papers

- VL-SAT, CVPR 2023: method overview and failure example appear early; results are mostly table-led with concise interpretation.
- Open3DSG, 3DV 2024: overview figure explains inputs, learned components, and inference path in one visual.
- ConceptGraphs, ICRA 2024: quantitative graph-quality numbers are table-led; prose explains evaluation caveats and human-evaluation protocol.
- SG-PGM, CVPR 2024: Figure 1 combines method and downstream use; result sections use a main comparison table plus targeted plots.
- OCRL-3DSSG, NeurIPS 2025: diagnostic observations use a table/figure before the method claim; main quantitative comparisons are table-led.
- RelationField, CVPR 2025: result prose points to tables and emphasizes the
  comparison pattern rather than restating every cell; its method figure uses
  real visual inputs, sparse arrows, and a caption for detail.
- CrossOver, CVPR 2025: its overview and method figures pair real modality
  examples with a small number of large processing blocks rather than a dense
  slide-style flowchart.
- Hybrid Reciprocal Transformer, CVPR 2025: the text gives selected headline
  gains and a few ablation anchors while leaving the full grid in tables.
- Synthetic Visual Genome, CVPR 2025: the text reports key deltas and explains
  the ablation trend instead of enumerating every setting.
- Scene Graph-Grounded Image Generation, AAAI 2025: component-ablation prose
  explains which module matters and relies on the table for dense values.

Primary sources checked:

- https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.pdf
- https://darko-project.eu/wp-content/uploads/papers/2024/Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_Objects_and_Open-Set_Relationships.pdf
- https://concept-graphs.github.io/assets/pdf/2023-ConceptGraphs.pdf
- https://openaccess.thecvf.com/content/CVPR2024/html/Xie_SG-PGM_Partial_Graph_Matching_Network_with_Semantic_Geometric_Fusion_for_CVPR_2024_paper.html
- https://proceedings.neurips.cc/paper_files/paper/2025/file/605e02ae04cba1ebf6a08206299e76b9-Paper-Conference.pdf
- https://openaccess.thecvf.com/content/CVPR2025/papers/Koch_RelationField_Relate_Anything_in_Radiance_Fields_CVPR_2025_paper.pdf
- https://openaccess.thecvf.com/content/CVPR2025/papers/Sarkar_CrossOver_3D_Scene_Cross-Modal_Alignment_CVPR_2025_paper.pdf
- https://openaccess.thecvf.com/content/CVPR2025/papers/Fu_Hybrid_Reciprocal_Transformer_with_Triplet_Feature_Alignment_for_Scene_Graph_CVPR_2025_paper.pdf
- https://openaccess.thecvf.com/content/CVPR2025/papers/Park_Synthetic_Visual_Genome_CVPR_2025_paper.pdf
- https://ojs.aaai.org/index.php/AAAI/article/view/32823/34978

## Findings

1. Results prose had too many inline numeric values. Top-tier papers usually put dense numbers in tables and keep prose for interpretation. Action: move control numbers into a dedicated controls/diagnostics table and keep the paragraph explanatory.

2. The old Table 2 was a claim-boundary table. It is useful for internal defense, but unusual as a main paper table. Action: demote it to prose in Experimental Setup. The paper table sequence now prioritizes scope, main results, and controls.

3. Condition names were too implementation-facing. Action: use Source score,
   RelCompat3D product, Rank-average, RRF, Pooled product, and Hard geometry
   filter in reviewer-facing text. Raw implementation keys remain only in
   reproducibility records.

4. Figure 1 was too static and flowchart-like. It is now a white-background,
   three-panel vector figure: an actual object-pair point cloud, a sparse
   `T/G -> C` path with `Z` bypass, and the observed rank change. Long method
   details remain in the caption and Method section.

5. The active structure is now Introduction -> Related Work -> Method ->
   Experiments -> Discussion and Limitations -> Conclusion. Problem Setup is
   integrated into Method, while setup and results are grouped under
   Experiments. This removes duplicated row/factor definitions and keeps broad
   claim interpretation out of the result-specific prose.

6. Direct confidence-interval grids are uncommon in the closest 3DSSG result
   tables, but the resampling method is a scientific procedure rather than an
   internal term. Action: keep point estimates in Table 1 and retain one main-
   text sentence stating paired 95% bootstrap intervals over relation contexts.
   Exact resample counts and scan-cluster results remain in the supplement.

7. A reviewer could attribute lower Violation to an uncertain-denominator
   artifact. Action: define decidable-only Violation, uncertainty rate, and the
   pessimistic bound in Experimental Setup; add the frozen three-source K=100
   sensitivity table to the supplement. All paired pessimistic-bound deltas
   favor the RelCompat3D product.

8. The method was under-specified for an ML reviewer. Action: state the
   family-specific logistic calibrator, standardized feature map, train-only
   imputation/normalization, BCE objective, L2 coefficient, optimizer steps,
   learning rate, feature counts, and the explicit `Z_e` exclusion.

9. Novelty could be blurred by current reliability/witness work. Action: add
   SCR-SSG, RelWitness, SGFormer++, RelGraphOV, and PUF and compare their task
   contracts against RelCompat3D's post-hoc predictor-agnostic compatibility and
   joint recall/violation/uncertainty evaluation contract.

10. The five-budget Recall and Violation tables were individually readable but
    forced reviewers to align two tables mentally. Action: use one joint table
    with paired R/V columns for every K. Keep Source score, the RelCompat3D
    product, rank-average, RRF, and pooled product; move hard filtering to the
    construction-diagnostic artifacts because its zero V is induced and it may
    return fewer than K rows.

11. Mechanism evidence was described across prose and supplement diagnostics
    but the six requested corruptions were not visible together. Action: add a
    K=50/100 fixed-model ablation table covering wrong predicate, wrong-pair
    geometry, shuffled geometry, label-fixed endpoint swap, distance-only, and
    compatibility-only ranking. The last condition removes Z but remains
    predicate-conditioned and is not called raw-G-only.

12. Table 2 is now a single-column K=50/100 control table with short
    reviewer-facing labels. This keeps the six requested controls visible
    without consuming a second full-width table.

13. Main-text numeric density is now limited to an abstract headline, two
    internal structural diagnostics, inferential directions, and one
    qualitative rank example. Full operating-point grids and corruption values
    remain in Tables 1--2; exact confidence intervals and secondary
    sensitivities remain in the supplement/artifacts.

## Current Editorial Decision

- Use one joint five-budget Recall/Violation table as the primary quantitative
  table; keep the fixed denominator in its caption and Experimental Setup.
- Keep a K=50/100 falsification and information-ablation table in the main
  paper, formatted as one column.
- Do not keep the old claim-boundary table in the main body.
- Keep Figure 2 as the compact tradeoff plot.
- Keep Figure 3 as qualitative/failure evidence, but it remains less central than Figure 1 and the main result table.
- Do not force a page break before references; the reviewed build lets
  references start after the conclusion to avoid a visibly empty column.
- Do not print full bootstrap ranges in the main source-result table. State the
  paired interval method once in Setup and use the supplement for the exact
  resampling specification and cluster sensitivity.
- `archive/paper/aaai_snapshots/20260625_top_tier_review.pdf` is the reviewed
  historical manuscript snapshot.
  Do not refresh it by simply copying the ignored `main.pdf` artifact; the
  reviewed PDF should reflect the current paper-facing edits made from this
  checklist.
- Current verified outputs are `main_aaai27.pdf` (9 pages, technical content
  through page 7),
  `supplement_aaai27.pdf` (3 pages), and the standalone 2-page checklist. The
  manuscript includes vector PDFs for all three figures and has no Type 3
  fonts. The active release ZIP contains the uncertainty script, fixed outputs,
  compose service, and current runbook.

## Current Acceptance Assessment

- Overall: borderline / weak-reject-to-weak-accept range, not accept-safe.
- Strongest defenses: concrete failure mechanism, explicit source-score
  exclusion, identity-preserving joins, linked counterfactuals, exact algebra
  projection, strong fusion/rescorer comparisons, all-K joint Recall--Violation
  reporting, uncertainty sensitivity, and family-wise failure disclosure.
- Remaining limits: compatibility and Violation share some geometric
  primitives; all three predictors share one dataset target; support/contact
  regresses; and a source-supervised nonlinear rescorer prevents best-rescorer
  or formula-superiority claims.
- A genuine independent human-alignment study could materially improve
  construct validity if human Violation@K reproduces the ranking direction and
  agreement/evidence-sufficiency are strong. It would not resolve the
  single-dataset scope or the novelty ceiling. Codex-to-Codex agreement alone
  does not provide this benefit.
