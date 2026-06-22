# CAND-001 Hypothesis Branches

Last updated: 2026-06-22 KST

이 폴더는 CAND-001에서 H001 이후에 열린 hypothesis-stage branch를 관리한다. H001/GeoCalib의 paper-facing experiment, result, and manuscript files are not owned here and must not be modified from this branch.

## Active Branches

| Branch | Name | Status | Role |
| --- | --- | --- | --- |
| `H002_factorized-relation-confidence/` | Factorized Relation Confidence | hypothesis / validation design | Relation confidence를 semantic channel과 geometry channel로 factorize하고 RGA/posterior framing을 검증한다. |
| `H003_Embedding/` | Semantic-Geometry Consistency Embedding | hypothesis formulation | Relation validity를 semantic representation과 object-pair geometry representation의 compatibility embedding으로 학습할 수 있는지 검토한다. |
| `H001_v2_risk_controlled_reranking/` | Risk-Controlled Geometry Reranking | protocol freeze | H001의 reliability-layer 핵심은 유지하되 `semantic_score * p_geom_valid` 결합을 predeclared violation-risk constraint 기반 reranking으로 발전시킨다. |

## Boundary

- H001/GeoCalib is treated as a completed prior branch for this workspace.
- H001_v2 may read H001 artifacts only through documented read-only inventories
  and must write to its own branch artifact root.
- H003 may cite H001 concepts such as geometry consistency, counterfactual controls, and recall/violation tradeoff, but it must not edit, rerun, or reinterpret H001 locked results without explicit user direction.
- H003 must stay in hypothesis stage until its target definition, label source, negative sampling policy, and shortcut controls are frozen.

## Recommended Reading Order For H001_v2

1. `H001_v2_risk_controlled_reranking/01_overview.md`
2. `H001_v2_risk_controlled_reranking/02_risk_control_protocol.md`
3. `H001_v2_risk_controlled_reranking/03_dataset_and_artifact_contract.md`
4. `H001_v2_risk_controlled_reranking/04_evaluation_plan.md`
5. `H001_v2_risk_controlled_reranking/05_source_inventory.md`
6. `H001_v2_risk_controlled_reranking/06_schema_probe.md`
7. `H001_v2_risk_controlled_reranking/artifacts/calibration_threshold_selection/report.md`
8. `H001_v2_risk_controlled_reranking/07_source_eval_contract.md`
9. `H001_v2_risk_controlled_reranking/TODO.md`

## Recommended Reading Order For H003

1. `H003_Embedding/01_overview.md`
2. `H003_Embedding/02_method.md`
3. `H003_Embedding/03_feasibility.md`
4. `H003_Embedding/04_dataset_contract.md`
5. `H003_Embedding/05_smoke_protocol.md`
6. `H003_Embedding/TODO.md`
