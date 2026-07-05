#!/usr/bin/env python3
"""Design artifact for H002 upgraded reliability combiners."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_ERROR_DIR = RGA_ROOT / "independent_controlled_error_analysis_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_combiner_upgrade_design_codex_ver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--error-dir", type=Path, default=DEFAULT_ERROR_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def slice_lookup(error_summary: dict[str, Any], slice_name: str) -> list[dict[str, Any]]:
    return [row for row in error_summary["slice_errors"] if row["slice_name"] == slice_name]


def candidate_matrix() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "C1_residual_logit_calibrator",
            "priority": 1,
            "status": "next_smoke_primary",
            "principle": "stacked residual calibration",
            "definition": (
                "Train a regularized residual on top of semantic_plus_geometry: "
                "logit(P)=logit(P_sg)+delta(S,G,D,U)."
            ),
            "why_needed": (
                "semantic_plus_geometry is the strongest simple baseline; the combiner "
                "should correct it rather than replace it."
            ),
            "deployable_inputs": (
                "semantic score/rank, p_geom_valid, consistency, disagreement, "
                "underconfidence, overconfidence"
            ),
            "forbidden_inputs": (
                "queue_kind, proposed_audit_role, label_match_status, "
                "geometry_status_hidden, rank_band_hidden, labeler confidence"
            ),
            "smoke_role": "primary upgraded combiner",
            "main_risk": "may overfit small 158-row bootstrap target",
            "mitigation": "use strong L2, scan-grouped folds, and compare to unchanged base",
        },
        {
            "candidate_id": "C2_family_gated_residual",
            "priority": 2,
            "status": "next_smoke_primary_if_regularized",
            "principle": "family-gated calibrated fusion",
            "definition": (
                "Use relation family as a deployable gate and shrink family-specific "
                "residual weights toward a global residual."
            ),
            "why_needed": (
                "support_contact, relative_vertical, and proximity show different "
                "geometry/calibration behavior."
            ),
            "deployable_inputs": (
                "predicate_family plus C1 deployable evidence; predicate_family is "
                "derived from the candidate relation label"
            ),
            "forbidden_inputs": (
                "all hidden audit metadata and all post-label target-construction metadata"
            ),
            "smoke_role": "family-conditioned upgraded combiner",
            "main_risk": "family rows are small and can memorize slice artifacts",
            "mitigation": "hierarchical shrinkage and no per-predicate free model at N=158",
        },
        {
            "candidate_id": "C3_uncertainty_gated_geometry",
            "priority": 3,
            "status": "next_smoke_secondary",
            "principle": "uncertainty-gated evidence use",
            "definition": (
                "Learn a soft geometry gate from deployable uncertainty proxies and apply "
                "geometry boost/penalty only when the gate is confident."
            ),
            "why_needed": (
                "geometry-only is weak globally but useful in selected regimes; global "
                "geometry penalties damage HL cases."
            ),
            "deployable_inputs": (
                "semantic entropy/proximity-to-0.5, rank, p_geom_valid, consistency, "
                "absolute disagreement, feature missing flags if available"
            ),
            "forbidden_inputs": "labeler confidence and hidden audit labels",
            "smoke_role": "ablation of gated geometry usage",
            "main_risk": "current feature export has limited explicit coverage evidence",
            "mitigation": "treat consistency as the current proxy and log coverage as missing",
        },
        {
            "candidate_id": "C4_monotonic_gbdt_calibrator",
            "priority": 4,
            "status": "defer_until_larger_label_set",
            "principle": "nonlinear calibrated tabular combiner",
            "definition": (
                "Use a monotonic constrained GBDT-style calibrator over S/G/D/U factors "
                "after label count increases."
            ),
            "why_needed": (
                "Can model nonlinear relation between disagreement, geometry, and reliability."
            ),
            "deployable_inputs": "same deployable evidence as C1-C3",
            "forbidden_inputs": "hidden audit metadata and validation/test tuning",
            "smoke_role": "future stronger nonlinear combiner",
            "main_risk": "too flexible for the current 158-row controlled slice",
            "mitigation": "defer until human-confirmed or larger independent labels exist",
        },
        {
            "candidate_id": "C5_graph_factor_rescoring",
            "priority": 5,
            "status": "defer_until_edge_local_signal_is_validated",
            "principle": "factor graph relation reliability",
            "definition": (
                "Promote local edge reliability into graph-level rescoring after edge-local "
                "combiner proves useful."
            ),
            "why_needed": "H002 final direction can use graph consistency, but local reliability must work first.",
            "deployable_inputs": "edge reliability factors plus graph consistency factors",
            "forbidden_inputs": "post-label audit role and target construction metadata",
            "smoke_role": "future graph-level extension",
            "main_risk": "scope expansion before edge-local evidence is stable",
            "mitigation": "blocked until upgraded edge combiner beats simple baselines",
        },
    ]


def smoke_plan() -> dict[str, Any]:
    return {
        "next_todo": "full_train_independent_combiner_upgrade_smoke",
        "split_policy": "train_only",
        "active_target": "proposed_role_balanced_codex_ver",
        "primary_eval": "train_internal_grouped_by_scan",
        "baseline_views": [
            "semantic_only",
            "geometry_only",
            "semantic_plus_geometry",
            "current_factorized_reliability_posterior",
            "residual_reliability_model",
        ],
        "upgraded_views": [
            "C1_residual_logit_calibrator",
            "C2_family_gated_residual",
            "C3_uncertainty_gated_geometry",
        ],
        "deferred_views": [
            "C4_monotonic_gbdt_calibrator",
            "C5_graph_factor_rescoring",
        ],
        "required_controls": [
            "scan-grouped folds",
            "same controlled slice",
            "same train-only provenance",
            "no hidden audit metadata as input",
            "no validation/test tuning",
            "compare against semantic_plus_geometry as the base to beat",
            "report family and direction slices",
            "report threshold error transfer: factorized_wrong_sg_correct vs factorized_correct_sg_wrong",
        ],
        "progression_thresholds": {
            "minimum_for_hypothesis_progress": {
                "delta_auprc_vs_semantic_plus_geometry": ">= +0.01 or clear Brier improvement",
                "delta_brier_vs_semantic_plus_geometry": "<= -0.005 preferred",
                "threshold_error_transfer": "new mistakes should not exceed fixed mistakes",
            },
            "not_paper_claim": "Any positive result remains bootstrap-train-only until human-confirmed labels or stronger independent target exists.",
        },
    }


def design_requirements(error_summary: dict[str, Any]) -> list[dict[str, Any]]:
    family_rows = slice_lookup(error_summary, "predicate_family")
    direction_rows = slice_lookup(error_summary, "direction_bin")
    return [
        {
            "requirement_id": "R1_do_not_replace_strong_base",
            "evidence": (
                "semantic_plus_geometry beats current factorized on grouped AUPRC and Brier."
            ),
            "design_consequence": "use residual correction over semantic_plus_geometry",
        },
        {
            "requirement_id": "R2_family_conditioning",
            "evidence": "; ".join(
                f"{row['slice_value']}: dAUPRC={fmt(row['delta_auprc_factorized_minus_sg'])}, "
                f"dBrier={fmt(row['mean_brier_delta_factorized_minus_sg'])}"
                for row in family_rows
            ),
            "design_consequence": "use family gate with shrinkage, not one global geometry weight",
        },
        {
            "requirement_id": "R3_direction_conditioning",
            "evidence": "; ".join(
                f"{row['slice_value']}: dAUPRC={fmt(row['delta_auprc_factorized_minus_sg'])}, "
                f"dBrier={fmt(row['mean_brier_delta_factorized_minus_sg'])}"
                for row in direction_rows
            ),
            "design_consequence": "separate HL, LH, and close-agreement behavior through deployable factor interactions",
        },
        {
            "requirement_id": "R4_calibration_guard",
            "evidence": (
                "current factorized has mean Brier delta +0.0021 and creates 10 SG-correct "
                "threshold mistakes while fixing only 1."
            ),
            "design_consequence": "optimize calibration and threshold transfer, not AUPRC alone",
        },
        {
            "requirement_id": "R5_no_hidden_metadata",
            "evidence": "prior target-independence audit found hidden metadata correlation in the original target",
            "design_consequence": "keep queue/status/role fields as post-hoc diagnostics only",
        },
    ]


def build_summary(error_summary: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_independent_combiner_upgrade_design_summary_v0",
        "status": "full_train_independent_combiner_upgrade_design_ready_for_smoke",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "error_summary": smoke.rel_path(DEFAULT_ERROR_DIR / "summary.json"),
            "error_status": error_summary.get("status"),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "hidden_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
        },
        "design_requirements": design_requirements(error_summary),
        "candidate_matrix": candidate_matrix(),
        "smoke_plan": smoke_plan(),
        "decision": (
            "Proceed to a train-only upgraded combiner smoke with residual, family-gated, "
            "and uncertainty-gated candidates. Do not use a generic high-capacity model "
            "as the first upgrade because the current evidence points to structured "
            "family/direction failures and the controlled target has only 158 rows."
        ),
        "next_todo": "full_train_independent_combiner_upgrade_smoke",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_design_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Combiner Upgrade Design",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only design artifact.",
        "- No new model is trained in this step.",
        "- No validation/test rows are used.",
        "- Hidden audit metadata remains post-hoc diagnostic only.",
        "- Multi-view remains audit evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Design Requirements",
        "",
        "| ID | Evidence | Consequence |",
        "| --- | --- | --- |",
    ]
    for row in summary["design_requirements"]:
        lines.append(f"| `{row['requirement_id']}` | {row['evidence']} | {row['design_consequence']} |")
    lines.extend(
        [
            "",
            "## Candidate Matrix",
            "",
            "| Priority | Candidate | Status | Principle | Smoke Role |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for row in summary["candidate_matrix"]:
        lines.append(
            f"| {row['priority']} | `{row['candidate_id']}` | `{row['status']}` | "
            f"{row['principle']} | {row['smoke_role']} |"
        )
    lines.extend(
        [
            "",
            "## Primary Decision",
            "",
            summary["decision"],
            "",
            "## Next Smoke Views",
            "",
            "Baselines:",
            "",
        ]
    )
    for item in summary["smoke_plan"]["baseline_views"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Upgraded views:", ""])
    for item in summary["smoke_plan"]["upgraded_views"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Required controls:", ""])
    for item in summary["smoke_plan"]["required_controls"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_json(output_dir / "smoke_plan.json", summary["smoke_plan"])
    write_csv(
        output_dir / "candidate_matrix.csv",
        summary["candidate_matrix"],
        [
            "candidate_id",
            "priority",
            "status",
            "principle",
            "definition",
            "why_needed",
            "deployable_inputs",
            "forbidden_inputs",
            "smoke_role",
            "main_risk",
            "mitigation",
        ],
    )
    write_csv(
        output_dir / "design_requirements.csv",
        summary["design_requirements"],
        ["requirement_id", "evidence", "design_consequence"],
    )
    write_design_report(output_dir / "design.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    error_dir = smoke.as_abs(args.error_dir)
    output_dir = smoke.as_abs(args.output_dir)
    error_summary = read_json(error_dir / "summary.json")
    summary = build_summary(error_summary, output_dir)
    summary["input"]["error_summary"] = smoke.rel_path(error_dir / "summary.json")
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        "status={status} candidates={candidates} validation_used={validation_used} "
        "trains_new_model={trains_new_model} next={next_todo}".format(
            status=summary["status"],
            candidates=len(summary["candidate_matrix"]),
            validation_used=summary["boundary"]["validation_usage"],
            trains_new_model=summary["boundary"]["trains_new_model"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
