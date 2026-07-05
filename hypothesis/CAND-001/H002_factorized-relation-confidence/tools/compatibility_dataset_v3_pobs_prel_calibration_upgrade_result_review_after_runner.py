#!/usr/bin/env python3
"""Review the H002 p_obs / p_rel calibration-upgrade runner output."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner"

EXPECTED_RUNTIME_STATUS = "h002_pobs_prel_calibration_upgrade_ready"
SCHEMA_VERSION = "h002_pobs_prel_calibration_upgrade_result_review_after_runner_v1"
STATUS_READY = "h002_pobs_prel_calibration_upgrade_result_review_after_runner_ready"
STATUS_ERROR = "h002_pobs_prel_calibration_upgrade_result_review_after_runner_input_errors"
NEXT_TODO = "compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
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


def by_metric(rows: list[dict[str, str]], name: str) -> dict[str, str]:
    for row in rows:
        if row.get("metric_name") == name:
            return row
    return {}


def run(args: argparse.Namespace) -> dict[str, Any]:
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    summary = read_json(args.runtime_dir / "summary.json")
    if summary.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors", "actual": summary.get("validation_errors")})

    calibration_rows = read_csv(args.runtime_dir / "calibration_metrics.csv")
    control_rows = read_csv(args.runtime_dir / "missing_evidence_control_metrics.csv")
    selective_rows = read_csv(args.runtime_dir / "selective_metrics.csv")
    route_rows = read_csv(args.runtime_dir / "failure_route_connection.csv")
    bootstrap_rows = read_csv(args.runtime_dir / "bootstrap_ci.csv")

    pobs_cal = by_metric(calibration_rows, "p_obs_calibrated")
    prel_raw = by_metric(calibration_rows, "p_rel_raw")
    prel_cal = by_metric(calibration_rows, "p_rel_calibrated")
    pobs_audit = by_metric(calibration_rows, "p_obs_vs_asset_observability")
    decision = by_metric(selective_rows, "accept_reject_abstain_calibrated")
    aurc = by_metric(selective_rows, "AURC")
    controls_min_abstain = min(float(row["abstain_rate"]) for row in control_rows if row["control_type"] != "observed_original")

    six_checks = [
        {
            "item": "1_Qe_observability_label",
            "status": "completed_but_not_sufficient_for_calibrated_claim",
            "evidence": f"asset_audit_rows={summary['row_counts']['asset_audit_rows']}; labels={summary['asset_observability_label_counts']}",
            "interpretation": "Actual 3RScan scan/multiview assets were checked, but all official observed rows were observable; no real unobservable negative was found.",
        },
        {
            "item": "2_calibration_split",
            "status": "completed",
            "evidence": f"calibration_split={summary['claim_boundary']['calibration_split']}; selected={summary['selected_calibrators']}",
            "interpretation": "Calibration was selected on internal_dev, not by official-validation tuning.",
        },
        {
            "item": "3_calibration_metric",
            "status": "completed_failed_for_prel_calibrated_claim",
            "evidence": f"p_rel raw ECE={prel_raw.get('ECE_10')}; calibrated ECE={prel_cal.get('ECE_10')}; calibrated AUROC={prel_cal.get('auroc')}",
            "interpretation": "p_rel discrimination remains above 0.70 AUROC, but calibration worsened and ECE remains too high.",
        },
        {
            "item": "4_selective_prediction_metric",
            "status": "completed_passed_as_stress_test",
            "evidence": f"macro_F1={decision.get('macro_F1')}; AURC={aurc.get('AURC')}",
            "interpretation": "Selective accept/reject/abstain behavior remains usable as stress-test evidence.",
        },
        {
            "item": "5_missing_evidence_controls",
            "status": "completed_passed",
            "evidence": f"min_non_observed_abstain_rate={controls_min_abstain}",
            "interpretation": "no-view, low-visibility, missing-mesh, shuffled-view, and wrong-pair controls all force abstention.",
        },
        {
            "item": "6_failure_route_connection",
            "status": "completed_partially_blocked",
            "evidence": "; ".join(f"{row['route_family']}={row['rows']}" for row in route_rows),
            "interpretation": "support_contact is connected; attachment_like and containment have no rows in current runtime, so empirical p_obs/p_rel claims are blocked for those routes.",
        },
    ]
    write_csv(out / "six_experiment_review.csv", six_checks)

    claim_decision = [
        {
            "claim": "calibrated_pobs_prel_reliability_is_solved",
            "decision": "blocked",
            "reason": "p_rel calibration failed on official validation; asset-audit observability labels lack real negative/ambiguous rows; attachment/containment rows absent.",
        },
        {
            "claim": "pobs_prel_selective_layer_as_framework_component",
            "decision": "allowed",
            "reason": "Selective stress-test and missing-evidence controls pass; keep as framework component with bounded wording.",
        },
        {
            "claim": "pobs_prel_main_quantitative_paper_result",
            "decision": "not_allowed_yet",
            "reason": "Requires independent negative observability labels, representative calibration split, and failure-route materialization.",
        },
    ]
    write_csv(out / "claim_decision.csv", claim_decision)

    report = [
        "# p_obs / p_rel Calibration Upgrade Result Review",
        "",
        "## Summary",
        "",
        "The six requested checks were executed, but the calibrated quantitative claim does not pass.",
        "",
        "## Key Results",
        "",
        f"- `p_obs` calibrated ECE@10: `{pobs_cal.get('ECE_10')}`",
        f"- `p_rel` raw ECE@10: `{prel_raw.get('ECE_10')}`",
        f"- `p_rel` calibrated ECE@10: `{prel_cal.get('ECE_10')}`",
        f"- `p_rel` calibrated AUROC: `{prel_cal.get('auroc')}`",
        f"- decision macro-F1: `{decision.get('macro_F1')}`",
        f"- AURC: `{aurc.get('AURC')}`",
        f"- asset audit label counts: `{summary['asset_observability_label_counts']}`",
        "",
        "## Decision",
        "",
        "`calibrated p_obs/p_rel reliability is solved` remains blocked.",
        "",
        "Reasons:",
        "",
        "- actual asset audit found all official observed rows observable, so it did not produce real unobservable negatives;",
        "- internal-dev isotonic calibration overfit or mismatched official validation distribution, worsening `p_rel` ECE;",
        "- attachment/containment routes are not materialized in the current p_obs/p_rel runtime;",
        "- missing-evidence controls pass, but they are still synthetic controls.",
        "",
        "Paper-safe wording: H002 includes `p_obs/p_rel` as a selective-decision framework component and shows a stress-test with missing-evidence controls. It should not claim calibrated p_obs/p_rel reliability is solved.",
    ]
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_dir": rel_path(args.runtime_dir),
        "validation_errors": len(errors),
        "six_checks_completed": True,
        "calibrated_quantitative_claim_pass": False,
        "pobs_prel_framework_component_allowed": True,
        "next_todo": NEXT_TODO,
    }
    write_json(out / "summary.json", payload)
    write_jsonl(out / "validation_errors.jsonl", errors)

    stage_file = H2_ROOT / "compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner",
                "",
                f"status = {payload['status']}",
                f"artifact_root = {rel_path(out)}/",
                f"validation_errors = {payload['validation_errors']}",
                "calibrated_quantitative_claim_pass = false",
                "pobs_prel_framework_component_allowed = true",
                f"next_todo = {payload['next_todo']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    print(json.dumps(run(parse_args()), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
