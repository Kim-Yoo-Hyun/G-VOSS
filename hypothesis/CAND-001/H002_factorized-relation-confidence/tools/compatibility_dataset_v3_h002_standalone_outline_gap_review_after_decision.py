#!/usr/bin/env python3
"""Review H002 standalone outline gaps before paper-workspace promotion."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
DEFAULT_DECISION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan"
)
DEFAULT_TABLE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
)
DEFAULT_POBS_CI_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision"
)

EXPECTED_DECISION_STATUS = "h002_paper_outline_or_integration_decision_after_insertion_plan_ready"
EXPECTED_DECISION_NEXT = "compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision"
EXPECTED_DECISION_PATH = "open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root"
EXPECTED_POBS_CI_STATUS = "h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready"
SCHEMA_VERSION = "h002_standalone_outline_gap_review_after_decision_v1"
STATUS_READY = "h002_standalone_outline_gap_review_after_decision_ready"
STATUS_ERROR = "h002_standalone_outline_gap_review_after_decision_input_errors"
SELECTED_PATH = "keep_outline_candidate_do_not_promote_paper_workspace_yet_resolve_gap_pack"
NEXT_TODO = "compatibility_dataset_v3_h002_gap_resolution_plan_after_outline_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    parser.add_argument("--pobs-ci-dir", type=Path, default=DEFAULT_POBS_CI_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate(
    decision: dict[str, Any],
    pobs_ci: dict[str, Any],
    main_rows: list[dict[str, str]],
    caveat_rows: list[dict[str, str]],
    control_rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision.get("status") != EXPECTED_DECISION_STATUS:
        errors.append({"error_type": "unexpected_decision_status", "actual": decision.get("status")})
    if decision.get("selected_path") != EXPECTED_DECISION_PATH:
        errors.append({"error_type": "unexpected_decision_path", "actual": decision.get("selected_path")})
    if decision.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append({"error_type": "unexpected_decision_next_todo", "actual": decision.get("next_todo")})
    if decision.get("validation_errors") != 0:
        errors.append({"error_type": "decision_validation_errors", "actual": decision.get("validation_errors")})
    if pobs_ci.get("status") != EXPECTED_POBS_CI_STATUS:
        errors.append({"error_type": "unexpected_pobs_ci_status", "actual": pobs_ci.get("status")})
    if pobs_ci.get("validation_errors") != 0:
        errors.append({"error_type": "pobs_ci_validation_errors", "actual": pobs_ci.get("validation_errors")})
    if len(main_rows) != 5:
        errors.append({"error_type": "unexpected_main_table_rows", "actual": len(main_rows)})
    if len(caveat_rows) != 3:
        errors.append({"error_type": "unexpected_caveat_rows", "actual": len(caveat_rows)})
    if len(control_rows) != 15:
        errors.append({"error_type": "unexpected_control_rows", "actual": len(control_rows)})
    if line_count(args.decision_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "decision_validation_error_file_not_empty"})
    return errors


def gap_matrix() -> list[dict[str, Any]]:
    return [
        {
            "area": "claim_and_novelty",
            "readiness": "partial",
            "severity": "high",
            "current_evidence": "Factorized T_e/G_e/Z_e/Q_e framing, validation reranking table, controls, p_obs/p_rel stress test.",
            "gap": "Need a sharper design-necessity argument that fixed fusion and source confidence fail for identifiable reasons, not only because H002 metrics are better.",
            "required_action": "Write a one-page novelty thesis linking failure cause -> factor separation -> C_e -> selective p_obs/p_rel.",
            "promotion_condition": "Paper outline must state a falsifiable mechanism claim and reviewer-facing simpler-baseline answer.",
        },
        {
            "area": "main_tables",
            "readiness": "mostly_ready",
            "severity": "medium",
            "current_evidence": "Main validation table, caveat rows, compact controls, mechanism metrics, p_obs/p_rel CI.",
            "gap": "Tables exist as artifacts but not yet organized into a final paper table plan with captions, ordering, and appendix split.",
            "required_action": "Freeze Table 1-5 contents and decide which rows are main vs appendix.",
            "promotion_condition": "All paper tables have caption, claim sentence, blocked wording, and source artifact path.",
        },
        {
            "area": "figures",
            "readiness": "not_ready",
            "severity": "high",
            "current_evidence": "No H002 figure specs are currently frozen.",
            "gap": "Need framework diagram, score-flow diagram, route-family/failure taxonomy figure, and possibly reliability/coverage plot.",
            "required_action": "Create figure plan with panels, inputs, outputs, and exact artifact sources.",
            "promotion_condition": "At least one method figure and one result/failure figure are specified before paper workspace promotion.",
        },
        {
            "area": "related_work",
            "readiness": "not_ready",
            "severity": "high",
            "current_evidence": "Outline lists related-work categories only.",
            "gap": "Need source-grounded related-work map for 3DSSG relation prediction, reliability/calibration/selective prediction, factorized/multimodal fusion, and geometry-aware relation verification.",
            "required_action": "Build related-work matrix from primary sources and mark novelty threat vs H002 claim.",
            "promotion_condition": "Every method claim has at least one contrast class and reviewer-risk note.",
        },
        {
            "area": "ablations_and_baselines",
            "readiness": "partial",
            "severity": "high",
            "current_evidence": "Semantic-only, geometry-only, concat, T x G compatibility, wrong-T, shuffled-G, source baseline, S2 source x C_e.",
            "gap": "Need final ablation contract across mechanism table, source-reranking table, p_obs/p_rel stress test, and support/contact failure route.",
            "required_action": "Freeze baseline list and ensure each contribution has a corresponding ablation/control.",
            "promotion_condition": "Ablation table answers: why not source-only, geometry-only, concat, C_e-only, shuffled/wrong-T, fixed fusion.",
        },
        {
            "area": "calibration_and_selective_prediction",
            "readiness": "partial",
            "severity": "high",
            "current_evidence": "p_obs/p_rel selective stress test passed; p_rel ECE@10 = 0.171030, p_rel AUROC CI [0.715937, 0.730900].",
            "gap": "Calibrated p_obs/p_rel paper claim remains blocked by ECE and synthetic unobservable labels.",
            "required_action": "Decide whether p_obs/p_rel is method component only or needs independent observability labels/calibration repair.",
            "promotion_condition": "Standalone paper must not overclaim p_obs/p_rel; calibrated result claim requires separate label/calibration evidence.",
        },
        {
            "area": "official_test_and_benchmark_boundary",
            "readiness": "bounded",
            "severity": "medium",
            "current_evidence": "Official 3DSSG validation split, VL-SAT/Open3DSG validation predictions, official test blocked.",
            "gap": "Need paper-safe evaluation wording explaining why validation is used and what is not claimed.",
            "required_action": "Freeze benchmark boundary paragraph and appendix provenance note.",
            "promotion_condition": "No official-test/SOTA/leaderboard/unconstrained-open-set wording appears in outline or tables.",
        },
        {
            "area": "support_contact_failure_taxonomy",
            "readiness": "partial",
            "severity": "high",
            "current_evidence": "Support/contact hard route is diagnostic/failure taxonomy; not solved.",
            "gap": "Need qualitative examples and taxonomy wording showing why contact/pose/observability-heavy relations need richer evidence.",
            "required_action": "Select representative failure cases and link them to missing geometry/visual evidence.",
            "promotion_condition": "Support/contact appears as limitation/failure route, not as success row.",
        },
        {
            "area": "open3dsg_boundary",
            "readiness": "bounded",
            "severity": "medium",
            "current_evidence": "Open3DSG is used as open-vocabulary source but evaluated after closed-vocabulary 3DSSG mapping.",
            "gap": "Need concise wording to prevent open-set GT overclaim.",
            "required_action": "Add footnote/caption line to paper outline and table plan.",
            "promotion_condition": "Every Open3DSG metric caption states closed-vocabulary 3DSSG mapping.",
        },
        {
            "area": "paper_workspace_promotion",
            "readiness": "not_ready",
            "severity": "high",
            "current_evidence": "Standalone outline candidate exists; no H001 edit; no new paper root.",
            "gap": "Need gap-resolution plan before creating a durable paper workspace.",
            "required_action": "Resolve table/figure/related-work/ablation/failure wording gaps or explicitly accept them as scope boundaries.",
            "promotion_condition": "User explicitly approves paper workspace creation after gap-resolution plan.",
        },
    ]


def table_plan() -> list[dict[str, Any]]:
    return [
        {
            "table_id": "T1",
            "title": "Mechanism Evaluation by Route Family",
            "status": "needs_caption_freeze",
            "main_or_appendix": "main",
            "artifact_source": "experiments/H002_compatibility_routing/official_evaluation/latest/",
            "claim": "T x G compatibility is stronger than semantic-only, geometry-only, and concat for the supported route families.",
        },
        {
            "table_id": "T2",
            "title": "Source Reranking Recall@K / Violation@K",
            "status": "available",
            "main_or_appendix": "main",
            "artifact_source": "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/main_validation_table.csv",
            "claim": "S2_source_x_Ce improves validation-level recall/violation tradeoff over source score for primary success families.",
        },
        {
            "table_id": "T3",
            "title": "Counterfactual Controls",
            "status": "available_but_needs_wording",
            "main_or_appendix": "main_or_appendix",
            "artifact_source": "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/control_table_compact.csv",
            "claim": "Wrong-T and shuffled-C_e controls worsen compatibility-specific violation-risk ranking.",
        },
        {
            "table_id": "T4",
            "title": "p_obs / p_rel Selective Stress Test",
            "status": "available_as_stress_test_only",
            "main_or_appendix": "appendix_or_analysis",
            "artifact_source": "artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/bootstrap_ci.csv",
            "claim": "Selective-decision layer is plausible but not a calibrated benchmark claim.",
        },
        {
            "table_id": "T5",
            "title": "Failure Taxonomy and Route Boundary",
            "status": "needs_materialization",
            "main_or_appendix": "analysis",
            "artifact_source": "support_contact_harder and p_obs/p_rel qualitative artifacts",
            "claim": "Support/contact and observability-heavy routes expose the limits of current geometry evidence.",
        },
    ]


def figure_plan() -> list[dict[str, Any]]:
    return [
        {
            "figure_id": "F1",
            "title": "H002 Factorized Reliability Framework",
            "status": "missing",
            "panels": "T_e/G_e/Z_e/Q_e -> C_e -> S2 reranking -> p_obs/p_rel selective decision",
            "required_artifact": "method diagram spec",
        },
        {
            "figure_id": "F2",
            "title": "Score Flow and Leakage Boundary",
            "status": "missing",
            "panels": "C_e excludes Z_e; hidden GT/violation labels are metric-only; source score joins only at final reranking",
            "required_artifact": "schema boundary diagram spec",
        },
        {
            "figure_id": "F3",
            "title": "Recall-Violation Tradeoff",
            "status": "missing",
            "panels": "S0 vs S2 across K={5,10,20,50,100}",
            "required_artifact": "line plot from main_validation_table.csv",
        },
        {
            "figure_id": "F4",
            "title": "Failure Taxonomy Examples",
            "status": "missing",
            "panels": "support/contact, p_obs abstain, false accept/reject examples",
            "required_artifact": "selected qualitative rows and visual/geometry evidence plan",
        },
    ]


def promotion_gate() -> list[dict[str, Any]]:
    return [
        {"gate": "G1_claim_thesis", "pass": False, "reason": "Need sharper design-necessity narrative."},
        {"gate": "G2_table_plan", "pass": False, "reason": "Tables exist but final main/appendix placement is not frozen."},
        {"gate": "G3_figure_plan", "pass": False, "reason": "No figure specs are frozen."},
        {"gate": "G4_related_work", "pass": False, "reason": "Related-work matrix and novelty-threat mapping are not prepared."},
        {"gate": "G5_ablation_contract", "pass": False, "reason": "Ablation/control table contract needs final paper-level consolidation."},
        {"gate": "G6_calibration_boundary", "pass": True, "reason": "Boundary is clear: p_obs/p_rel stress test only, no calibrated claim."},
        {"gate": "G7_benchmark_boundary", "pass": True, "reason": "Validation-only and no-SOTA/no-test wording are locked."},
        {"gate": "G8_failure_taxonomy", "pass": False, "reason": "Support/contact qualitative taxonomy still needs paper-facing examples."},
        {"gate": "G9_workspace_promotion", "pass": False, "reason": "Do not create a new paper root yet."},
    ]


def report_text(status: str, errors: list[dict[str, Any]]) -> str:
    return f"""# H002 Standalone Outline Gap Review

## 목적

H002 standalone paper-outline candidate가 실제 paper workspace로 승격될 만큼
준비됐는지 점검했다.

## 결과

```text
status = {status}
selected_path = {SELECTED_PATH}
validation_errors = {len(errors)}
next_todo = {NEXT_TODO}
```

결론은 아직 paper workspace로 승격하지 않는 것이다. H002는 standalone outline
candidate로 유지하되, figure plan, related-work matrix, ablation contract,
support/contact failure taxonomy, and final table placement를 먼저 정리해야 한다.
"""


def main() -> int:
    args = parse_args()
    decision = read_json(args.decision_dir / "summary.json")
    pobs_ci = read_json(args.pobs_ci_dir / "summary.json")
    main_rows = read_csv(args.table_dir / "main_validation_table.csv")
    caveat_rows = read_csv(args.table_dir / "source_family_caveats.csv")
    control_rows = read_csv(args.table_dir / "control_table_compact.csv")
    errors = validate(decision, pobs_ci, main_rows, caveat_rows, control_rows, args)
    status = STATUS_ERROR if errors else STATUS_READY

    args.output_dir.mkdir(parents=True, exist_ok=True)
    gaps = gap_matrix()
    gates = promotion_gate()
    write_csv(args.output_dir / "gap_matrix.csv", gaps)
    write_csv(args.output_dir / "table_plan.csv", table_plan())
    write_csv(args.output_dir / "figure_plan.csv", figure_plan())
    write_csv(args.output_dir / "promotion_gate.csv", gates)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(report_text(status, errors), encoding="utf-8")

    blocking_gates = [row["gate"] for row in gates if not row["pass"]]
    high_gaps = [row["area"] for row in gaps if row["severity"] == "high"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected_path": SELECTED_PATH,
        "decision": {
            "standalone_outline_candidate_remains_selected": True,
            "promote_to_new_paper_workspace_now": False,
            "h001_manuscript_edit_now": False,
            "new_top_level_paper_folder_now": False,
            "official_test_claim_allowed": False,
            "calibrated_pobs_prel_claim_allowed": False,
        },
        "gap_summary": {
            "gap_rows": len(gaps),
            "high_severity_gap_areas": high_gaps,
            "promotion_gates": len(gates),
            "blocking_gates": blocking_gates,
            "ready_gates": [row["gate"] for row in gates if row["pass"]],
        },
        "input_artifacts": {
            "decision": rel_path(args.decision_dir),
            "main_table": rel_path(args.table_dir / "main_validation_table.csv"),
            "control_table": rel_path(args.table_dir / "control_table_compact.csv"),
            "pobs_ci": rel_path(args.pobs_ci_dir),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "gap_matrix": rel_path(args.output_dir / "gap_matrix.csv"),
            "table_plan": rel_path(args.output_dir / "table_plan.csv"),
            "figure_plan": rel_path(args.output_dir / "figure_plan.csv"),
            "promotion_gate": rel_path(args.output_dir / "promotion_gate.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
    }
    write_json(args.output_dir / "summary.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
