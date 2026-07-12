# Top-Tier Style Review for GeoCalib

Last updated: 2026-07-12 KST

## Compared Papers

- VL-SAT, CVPR 2023: method overview and failure example appear early; results are mostly table-led with concise interpretation.
- Open3DSG, 3DV 2024: overview figure explains inputs, learned components, and inference path in one visual.
- ConceptGraphs, ICRA 2024: quantitative graph-quality numbers are table-led; prose explains evaluation caveats and human-evaluation protocol.
- SG-PGM, CVPR 2024: Figure 1 combines method and downstream use; result sections use a main comparison table plus targeted plots.
- OCRL-3DSSG, NeurIPS 2025: diagnostic observations use a table/figure before the method claim; main quantitative comparisons are table-led.

Primary sources checked:

- https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.pdf
- https://darko-project.eu/wp-content/uploads/papers/2024/Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_Objects_and_Open-Set_Relationships.pdf
- https://concept-graphs.github.io/assets/pdf/2023-ConceptGraphs.pdf
- https://openaccess.thecvf.com/content/CVPR2024/html/Xie_SG-PGM_Partial_Graph_Matching_Network_with_Semantic_Geometric_Fusion_for_CVPR_2024_paper.html
- https://proceedings.neurips.cc/paper_files/paper/2025/file/605e02ae04cba1ebf6a08206299e76b9-Paper-Conference.pdf

## Findings

1. Results prose had too many inline numeric values. Top-tier papers usually put dense numbers in tables and keep prose for interpretation. Action: move control numbers into a dedicated controls/diagnostics table and keep the paragraph explanatory.

2. The old Table 2 was a claim-boundary table. It is useful for internal defense, but unusual as a main paper table. Action: demote it to prose in Experimental Setup. The paper table sequence now prioritizes scope, main results, and controls.

3. Condition names were too implementation-facing. Action: use Source score,
   Family-calibrated product, Rank-average fusion, Pooled-calibrator ablation,
   and Hard geometry filter in reviewer-facing tables. Raw implementation keys
   remain only in reproducibility records.

4. Figure 1 was too static and flowchart-like. Top-tier first figures often show a motivating failure example plus the method path. Action: regenerate Figure 1 as a failure-example-to-method schematic showing semantic-only failure, same-pair geometry join, calibrated re-ranking, and controls.

5. The overall paper structure is basically sound: Introduction -> Related Work -> Problem -> Method -> Experimental Setup -> Results -> Limitations -> Conclusion. The main risk was not section order, but over-defensive artifacts in the main body and dense inline result prose.

6. Direct bootstrap-interval notation is not typical in the closest 3DSSG
   result tables. Action: keep the main source-result table as point estimates,
   describe bootstrap as an internal stability check in prose, and leave raw
   interval details in the experiment artifact rather than the main manuscript.

7. A reviewer could attribute lower Violation to an uncertain-denominator
   artifact. Action: define decidable-only Violation, uncertainty rate, and the
   pessimistic bound in Experimental Setup; add the frozen three-source K=100
   sensitivity table to the supplement. All paired pessimistic-bound deltas
   favor Family-calibrated product.

8. The method was under-specified for an ML reviewer. Action: state the
   family-specific logistic calibrator, standardized feature map, train-only
   imputation/normalization, BCE objective, L2 coefficient, optimizer steps,
   learning rate, feature counts, and the explicit `Z_e` exclusion.

9. Novelty could be blurred by current reliability/witness work. Action: add
   SCR-SSG, RelWitness, SGFormer++, RelGraphOV, and PUF and compare their task
   contracts against GeoCalib's post-hoc source-independent compatibility and
   joint recall/violation/uncertainty evaluation contract.

## Current Editorial Decision

- Keep Table 1 as scope/denominator table because the claim depends on denominator transparency.
- Use the main source-result table as the primary quantitative table.
- Add a controls/diagnostics table.
- Do not keep the old claim-boundary table in the main body.
- Keep Figure 2 as the compact tradeoff plot.
- Keep Figure 3 as qualitative/failure evidence, but it remains less central than Figure 1 and the main result table.
- Do not force a page break before references; the reviewed build lets
  references start after the conclusion to avoid a visibly empty column.
- Do not print bootstrap confidence ranges in the main source-result table or
  primary results prose. Use point estimates for the paper-facing comparison
  and cite bootstrap only as a stability check if needed.
- `archive/paper/aaai_snapshots/20260625_top_tier_review.pdf` is the reviewed
  historical manuscript snapshot.
  Do not refresh it by simply copying the ignored `main.pdf` artifact; the
  reviewed PDF should reflect the current paper-facing edits made from this
  checklist.
- Current verified outputs are `main_aaai27.pdf` (9 pages, 7 technical),
  `supplement_aaai27.pdf` (2 pages), and the standalone 2-page checklist. The
  active release ZIP contains the uncertainty script, frozen outputs, compose
  service, and current runbook.
