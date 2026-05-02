# CAND-001 Hypotheses

Last updated: 2026-05-03

## Source Candidate

- Candidate: `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source file: `literature/CAND-001.md`
- Recommended formulation: `Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations`

## Candidate Direction

Given object instances and candidate semantic relations in a 3D indoor scene, construct relation edges that store both semantic predicate information and explicit geometry evidence, then verify or refine those relations using geometry-consistency checks.

## Active Hypothesis

| ID | Title | Folder | Status |
| --- | --- | --- | --- |
| H001 | Geometry-grounded verification of open-vocabulary 3DSSG relations | `H001_geometry-grounded-verification/` | layout checker run |

## H001 Files

- `01_problem.md`: problem
- `02_hypothesis.md`: hypothesis statement and success/falsification criteria
- `03_feasibility.md`: feasibility
- `04_experiment.md`: experiment
- `05_evidence_schema.md`: evidence schema
- `06_rule_verifier.md`: rule verifier
- `07_stage_log.md`: merged execution and stage log
- `13_subtypes.md`: support/contact subtype decision
- `14_verifier_v2.md`: subtype-aware verifier contract and one-scan result
- `15_calibration.md`: probabilistic geometry consistency calibration design
- `16_evaluation.md`: prediction-level violation/recall evaluation protocol
- `17_subset.md`: multi-scan/subset strategy decision
- `18_baseline.md`: prediction-level baseline decision
- `19_schema.md`: prediction JSONL schema and adapter contract
- `20_layout.md`: VL-SAT local layout compatibility check
- `tools/check_layout.py`: VL-SAT layout checker
- `artifacts/layout/vlsat/`: latest layout checker output

## Candidate-Level Assumptions

- 3DSSG / 3RScan is the primary benchmark path.
- Official `3DSSG_subset` is the primary split and relation-subgraph source.
- `VL-SAT` / `vlsat_closed_set` is the first prediction-level learned baseline.
- The first prototype should use ground-truth object instances or reliable instance masks.
- The first predicate subset should focus on support/contact, proximity, and relative position.
- Full functional relation discovery is out of first scope.
- Full robotics navigation or online RGB-D graph generation is out of first scope.

## Candidate-Level Risks

- 3DSSG relation labels may be noisy or too coarse for geometry-consistency evaluation.
- Coordinate-frame handling may affect left/right/front/behind relations.
- A simple geometry verifier may reduce violations but also remove valid semantic relations.
- Baseline reproduction may become the main time sink if attempted before verifier sanity checks.

## Calibration Status

`15_calibration.md` defines the probabilistic calibration design, but `p_geom_valid` has not been fitted or evaluated yet.

Calibration implementation requires:

- official `3DSSG_subset` train/validation split and a train-derived dev slice;
- calibration table schema;
- counterfactual negative generation;
- held-out calibration metrics.

## Next Gate

Decide the minimal `VL-SAT` eval path before implementing prediction-level evaluation.
