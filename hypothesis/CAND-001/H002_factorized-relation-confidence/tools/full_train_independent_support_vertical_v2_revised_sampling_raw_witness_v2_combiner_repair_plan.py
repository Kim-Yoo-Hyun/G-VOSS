#!/usr/bin/env python3
"""Combiner repair plan for H002 raw-witness v2 posterior."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_ERROR_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready"
DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--error-dir", type=Path, default=DEFAULT_ERROR_DIR)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def candidate_combiners() -> list[dict[str, Any]]:
    return [
        {
            "combiner_id": "C0_semantic_plus_geometry_legacy",
            "role": "reference",
            "capacity": "fixed_existing",
            "uses_semantic": True,
            "uses_legacy_p_geom": True,
            "uses_raw_witness": False,
            "uses_family_gate": False,
            "uses_endpoint_type": False,
            "rationale": "Keep the pre-v2 baseline as the primary reference.",
            "decision": "keep_reference",
        },
        {
            "combiner_id": "C1_raw_witness_only_v2",
            "role": "geometry_evidence_reference",
            "capacity": "low",
            "uses_semantic": False,
            "uses_legacy_p_geom": False,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Measure whether typed witness evidence alone carries reliability signal.",
            "decision": "keep_reference",
        },
        {
            "combiner_id": "C2_semantic_plus_raw_witness_v2",
            "role": "semantic_raw_reference",
            "capacity": "low",
            "uses_semantic": True,
            "uses_legacy_p_geom": False,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Direct replacement for semantic_plus_geometry without extra interactions.",
            "decision": "keep_reference",
        },
        {
            "combiner_id": "C3_linear_v2",
            "role": "current_best_simple_reference",
            "capacity": "low",
            "uses_semantic": True,
            "uses_legacy_p_geom": True,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Current strongest simple posterior by grouped AUPRC and Brier.",
            "decision": "promote_to_next_reference",
        },
        {
            "combiner_id": "C4_calibrated_linear_v2",
            "role": "calibration_repair_candidate",
            "capacity": "low",
            "uses_semantic": True,
            "uses_legacy_p_geom": True,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Keep the linear ranking signal but add train-only grouped calibration diagnostics.",
            "decision": "test_next",
        },
        {
            "combiner_id": "C5_constrained_monotonic_additive",
            "role": "principled_combiner_candidate",
            "capacity": "low_medium",
            "uses_semantic": True,
            "uses_legacy_p_geom": False,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Use predeclared monotonic evidence directions to reduce overfit and preserve interpretability.",
            "decision": "test_next",
        },
        {
            "combiner_id": "C6_family_gated_calibrated_mixture",
            "role": "family_heterogeneity_repair_candidate",
            "capacity": "medium",
            "uses_semantic": True,
            "uses_legacy_p_geom": False,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Allow support_contact and relative_vertical to use separate calibrated evidence weights without free endpoint shortcuts.",
            "decision": "test_next",
        },
        {
            "combiner_id": "C7_limited_interaction_model",
            "role": "upper_bound_candidate",
            "capacity": "medium",
            "uses_semantic": True,
            "uses_legacy_p_geom": True,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": False,
            "rationale": "Add only predeclared interactions such as semantic_x_raw, support_gate_x_gap, and vertical_gate_x_margin.",
            "decision": "test_after_C4_C6",
        },
        {
            "combiner_id": "C8_endpoint_type_ablation_only",
            "role": "shortcut_probe",
            "capacity": "low",
            "uses_semantic": True,
            "uses_legacy_p_geom": True,
            "uses_raw_witness": True,
            "uses_family_gate": True,
            "uses_endpoint_type": True,
            "rationale": "Endpoint type is too strong to ignore but must remain an ablation/control until shortcut risk is resolved.",
            "decision": "ablation_only",
        },
    ]


def control_matrix() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "K0_global_raw_witness_shuffle",
            "tests": "whether v2 gain follows the actual object pair geometry",
            "required": True,
            "failure_if": "candidate remains close to true raw-witness performance after global shuffle",
        },
        {
            "control_id": "K1_within_family_raw_witness_shuffle",
            "tests": "whether the gain is only relation-family distribution rather than pair-specific witness",
            "required": True,
            "failure_if": "within-family shuffle keeps most of the candidate gain",
        },
        {
            "control_id": "K2_wrong_pair_raw_witness",
            "tests": "whether candidate relies on actual subject-object pair geometry",
            "required": True,
            "failure_if": "wrong-pair witness does not collapse ranking/calibration",
        },
        {
            "control_id": "K3_family_only_offset",
            "tests": "free family prior shortcut",
            "required": True,
            "failure_if": "family-only baseline explains most of the gain",
        },
        {
            "control_id": "K4_no_family_local_normalization",
            "tests": "whether local normalization helps calibration or only adds noise",
            "required": True,
            "failure_if": "normalization hurts both ranking and brier in both families",
        },
        {
            "control_id": "K5_endpoint_type_only_or_ablation",
            "tests": "endpoint/object category shortcut risk",
            "required": True,
            "failure_if": "endpoint-only/ablation dominates while raw witness contribution disappears",
        },
        {
            "control_id": "K6_family_split_support_only_vertical_only",
            "tests": "support_contact-driven gain and relative_vertical calibration regression",
            "required": True,
            "failure_if": "overall positive result hides a negative or uncalibrated relative_vertical slice",
        },
    ]


def success_gates() -> dict[str, Any]:
    return {
        "split": "train_only_grouped_by_scan",
        "reference": "C3_linear_v2",
        "minimum_gate_for_new_primary": {
            "delta_auprc_vs_linear_min": 0.0,
            "delta_brier_vs_linear_max": 0.0,
            "delta_ece_vs_linear_max": 0.0,
            "new_errors_minus_fixes_vs_linear_max": 0,
        },
        "fallback_gate": {
            "allowed_if": "candidate ties linear within 0.01 AUPRC and improves Brier/ECE or threshold transfer",
            "claim": "calibration/threshold repair, not ranking improvement",
        },
        "family_gates": {
            "support_contact": {
                "delta_auprc_vs_semantic_plus_geometry_min": 0.10,
                "delta_brier_vs_semantic_plus_geometry_max": 0.0,
            },
            "relative_vertical": {
                "delta_auprc_vs_semantic_plus_geometry_min": 0.0,
                "delta_brier_vs_semantic_plus_geometry_max": 0.0,
                "note": "If Brier stays positive, vertical must be separated or treated as unresolved calibration.",
            },
        },
        "shortcut_gates": {
            "raw_witness_controls": "global/within-family/wrong-pair controls must remove most of the true raw-witness gain",
            "endpoint_control": "endpoint ablation cannot be the only source of gain for the main claim",
            "family_only_control": "family-only offset cannot explain the positive signal",
        },
        "blocked_paper_claim_until": [
            "combiner beats or calibrates against C3_linear_v2 under grouped split",
            "relative_vertical calibration regression is resolved or explicitly excluded",
            "endpoint shortcut control passes",
            "train-only result is later reproduced under a proper held-out protocol before paper metrics",
        ],
    }


def next_smoke_plan() -> dict[str, Any]:
    return {
        "next_todo": "revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke",
        "input_rows": "raw_witness_feature_join_v2/posterior_ready_rows.jsonl",
        "input_boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "review_fields_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
            "geometry_status_as_model_input": False,
        },
        "candidate_order": [
            "C0_semantic_plus_geometry_legacy",
            "C1_raw_witness_only_v2",
            "C2_semantic_plus_raw_witness_v2",
            "C3_linear_v2",
            "C4_calibrated_linear_v2",
            "C5_constrained_monotonic_additive",
            "C6_family_gated_calibrated_mixture",
            "C7_limited_interaction_model",
            "C8_endpoint_type_ablation_only",
        ],
        "metrics": [
            "AUROC",
            "AUPRC",
            "Brier",
            "ECE-5",
            "Accuracy@0.5",
            "threshold transfer fixes/adds",
            "family-slice deltas",
            "control deltas",
        ],
        "primary_reference": "C3_linear_v2",
        "paper_claim_allowed": False,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    q = summary["diagnostic_summary"]["quick_deltas"]
    lines = [
        "# H002 Raw-Witness V2 Combiner Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only planning step.",
        "- No validation/test rows are used.",
        "- No model is trained in this step.",
        "- This plan changes the next combiner comparison protocol, not the current results.",
        "- Results are not paper-level metrics.",
        "",
        "## Diagnosis Used",
        "",
        f"- Error status: `{summary['input']['error_status']}`",
        f"- Smoke status: `{summary['input']['smoke_status']}`",
        f"- Rows: `{summary['input']['rows']}`",
        f"- `family_shrinkage` vs `semantic_plus_geometry` dAUPRC: `{q['primary_vs_semantic_plus_geometry']['auprc']:.4f}`",
        f"- `linear_v2` vs `semantic_plus_geometry` dAUPRC: `{q['linear_vs_semantic_plus_geometry']['auprc']:.4f}`",
        f"- `family_shrinkage` vs `linear_v2` dAUPRC: `{q['primary_vs_linear']['auprc']:.4f}`",
        "",
        "## Combiner Candidates",
        "",
        "| ID | Role | Capacity | Decision | Rationale |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["combiner_candidates"]:
        lines.append(
            f"| `{row['combiner_id']}` | `{row['role']}` | `{row['capacity']}` | "
            f"`{row['decision']}` | {row['rationale']} |"
        )
    lines.extend(
        [
            "",
            "## Required Controls",
            "",
            "| Control | Tests | Failure If |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["control_matrix"]:
        lines.append(f"| `{row['control_id']}` | {row['tests']} | {row['failure_if']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    error_dir = as_abs(args.error_dir)
    smoke_dir = as_abs(args.smoke_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    error_summary = read_json(error_dir / "summary.json")
    smoke_summary = read_json(smoke_dir / "summary.json")
    summary = {
        "schema_version": "h002_raw_witness_v2_combiner_repair_plan_summary_v1",
        "status": "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "error_dir": rel_path(error_dir),
            "smoke_dir": rel_path(smoke_dir),
            "error_status": error_summary["status"],
            "smoke_status": smoke_summary["status"],
            "rows": error_summary["input"]["rows"],
            "positive": error_summary["input"]["positive"],
            "negative": error_summary["input"]["negative"],
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "changes_feature_contract": False,
            "changes_combiner_protocol": True,
            "paper_evidence_allowed": False,
        },
        "diagnostic_summary": {
            "diagnosis": error_summary["diagnosis"],
            "quick_deltas": error_summary["quick_deltas"],
            "claim_boundary": error_summary["claim_boundary"],
        },
        "combiner_candidates": candidate_combiners(),
        "control_matrix": control_matrix(),
        "success_gates": success_gates(),
        "next_smoke_plan": next_smoke_plan(),
        "decision": (
            "Proceed to a train-only combiner smoke that treats C3_linear_v2 as the current strongest simple "
            "reference. The next candidates must improve or calibrate against linear, keep endpoint features "
            "as ablation/control only, and resolve the relative_vertical Brier regression before any posterior "
            "method claim is allowed."
        ),
        "claim_boundary": {
            "allowed": (
                "The planning claim is that typed raw witness is promising but the posterior combiner is unsettled."
            ),
            "blocked": (
                "Do not claim family_shrinkage is final, do not claim broad family-general improvement, and do not "
                "promote train-only H002 posterior results to paper metrics."
            ),
        },
        "next_todo": "revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke",
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "success_gates.json", summary["success_gates"])
    write_json(output_dir / "next_smoke_plan.json", summary["next_smoke_plan"])
    write_csv(output_dir / "combiner_candidates.csv", summary["combiner_candidates"])
    write_csv(output_dir / "control_matrix.csv", summary["control_matrix"])
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    q = summary["diagnostic_summary"]["quick_deltas"]
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "candidate_count={candidate_count} control_count={control_count} "
        "d_auprc_linear_vs_sg={linear:.4f} d_auprc_primary_vs_linear={primary_linear:.4f} "
        "next={next_todo}".format(
            status=summary["status"],
            rows=summary["input"]["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            candidate_count=len(summary["combiner_candidates"]),
            control_count=len(summary["control_matrix"]),
            linear=q["linear_vs_semantic_plus_geometry"]["auprc"],
            primary_linear=q["primary_vs_linear"]["auprc"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
