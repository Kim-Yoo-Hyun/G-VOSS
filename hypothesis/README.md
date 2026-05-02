# Hypothesis Index

Last updated: 2026-05-03

이 폴더는 literature candidate를 검증 가능한 research hypothesis로 좁히는 산출물을 저장한다. workflow와 작성 규칙은 `docs/hypothesis.md`를 따른다.

## Active Candidate

- `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source: `literature/CAND-001.md`
- Status: hypothesis workflow initialized; Phase A evidence export completed; Phase B verifier smoke test completed; manual review completed; `ply_points_v1` support/contact extractor completed; comparison report completed; `tools/apply_rules_v1.py` completed; v1 review queue triage completed; visual inspection completed; support/contact subtype decision completed; verifier v2 contract written; `tools/apply_verifier_v2.py` implemented; v2 one-scan smoke test passed; probabilistic calibration design written; violation/recall evaluation protocol written; official `3DSSG_subset`-based multi-scan/subset strategy decided; prediction-level baseline selected as `VL-SAT` / `vlsat_closed_set`; prediction JSONL schema written; VL-SAT local layout compatibility checked; `tools/check_layout.py` implemented and run; old stage docs consolidated into `07_stage_log.md`

## Hypothesis Registry

| Hypothesis | Folder | Status | Next Gate |
| --- | --- | --- | --- |
| H001: Geometry-grounded verification of open-vocabulary 3DSSG relations | `hypothesis/CAND-001/H001_geometry-grounded-verification/` | Layout checker run | VL-SAT minimal eval path decision |

## Current Gate

Local dataset validation is passed for one sample scan. The `VL-SAT` local layout checker is implemented and reports default-layout `blocked`. The current gate is the minimal `VL-SAT` eval path decision.

Confirmed:

- `local_dataset/3DSSG` has full annotation files.
- `local_dataset/3DSSG_subset` has official subset train/validation files.
- `local_dataset/3RScan/files` has metadata and split files.
- `local_dataset/3RScan/download_3rscan.py` is present and passes compile/help checks.
- Sample scan `f62fd5fd-9a3f-2f44-883a-1e5cf819608e` has the three required sample payload files.

Implementation guardrail:

- avoid full VL-SAT/Open3DSG reproduction until local layout prep and a minimal `VL-SAT` eval path are fixed.

Current artifact:

- script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_evidence.py`
- output: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/`
- Phase A result: 772 edges exported, validation passed, 0 errors
- Stage log: `hypothesis/CAND-001/H001_geometry-grounded-verification/07_stage_log.md`
- Phase B script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/apply_rules_v0.py`
- Phase B result: 772 verifier decisions, validation passed, primary metric denominator 129
- Manual review: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/review_report.md`
- Manual labels: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/review_labels.jsonl`
- Phase C script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_point_support.py`
- Phase C result: 32 support/contact records, 19 point-satisfied, 13/16 floor-support recovered
- Comparison report: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/comparison_report.md`
- Phase D script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/apply_rules_v1.py`
- Phase D result: 772 edges preserved, support/contact 19 satisfied / 1 uncertain / 12 violated, validation passed
- V1 review triage: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/v1_review_report.md`
- Visual inspection labels: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/visual_inspection/labels.jsonl`
- Support/contact subtype decision: `hypothesis/CAND-001/H001_geometry-grounded-verification/13_subtypes.md`
- Verifier v2 contract: `hypothesis/CAND-001/H001_geometry-grounded-verification/14_verifier_v2.md`
- Verifier v2 script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/apply_verifier_v2.py`
- Verifier v2 result: 772 edges preserved, support/contact 31 satisfied / 1 uncertain / 0 violated, validation passed
- Calibration design: `hypothesis/CAND-001/H001_geometry-grounded-verification/15_calibration.md`
- Evaluation protocol: `hypothesis/CAND-001/H001_geometry-grounded-verification/16_evaluation.md`
- Subset strategy: `hypothesis/CAND-001/H001_geometry-grounded-verification/17_subset.md`
- Baseline decision: `hypothesis/CAND-001/H001_geometry-grounded-verification/18_baseline.md`
- Prediction schema: `hypothesis/CAND-001/H001_geometry-grounded-verification/19_schema.md`
- Layout compatibility: `hypothesis/CAND-001/H001_geometry-grounded-verification/20_layout.md`
- Layout checker script: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/check_layout.py`
- Layout checker output: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/layout/vlsat/`
- Calibration implementation status: not started; blocked by calibration table schema, counterfactual negatives, and additional scan payloads.

Subset decision:

- use official `3DSSG_subset` as the primary split and relation-subgraph source;
- keep full 3DSSG annotation as auxiliary evidence for coverage checks, compatibility checks, and counterfactual negatives.

## Blocked Items

- Full baseline reproduction is blocked until local `VL-SAT` layout prep and minimal eval path are fixed.
- Experiment folder creation is blocked until the first prediction-level run is actually implemented.
- Paper-writing workflow is out of scope.
