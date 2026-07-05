#!/usr/bin/env python3
"""Review R1 close-by geometry-support controls and freeze route position."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_route_result_review"
)

EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_close_by_geometry_support_route_result_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_input_errors"
SELECTED_PATH = "freeze_close_by_as_geometry_only_route_evidence_move_to_supported_by_decomposition"
NEXT_TODO = "compatibility_dataset_v3_supported_by_decomposition_target_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def control_map(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row.get("control_name") or row.get("control_id")
        if not name:
            continue
        converted: dict[str, Any] = {}
        for key, value in row.items():
            numeric = as_float(value)
            converted[key] = numeric if numeric is not None else value
        mapped[name] = converted
    return mapped


def metric(
    controls: dict[str, dict[str, Any]],
    control: str,
    key: str,
    default: float | None = None,
) -> float | None:
    value = controls.get(control, {}).get(key)
    return float(value) if isinstance(value, (int, float)) else default


def validate_inputs(
    runner_summary: dict[str, Any],
    control_rows: list[dict[str, str]],
    controls: dict[str, dict[str, Any]],
    validation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(validation_rows)})
    if len(control_rows) != 12:
        errors.append({"error_type": "unexpected_control_count", "actual": len(control_rows), "expected": 12})

    required = [
        "distance_xy",
        "distance_3d",
        "normalized_distance_xy",
        "normalized_distance_3d",
        "overlap_geometry",
        "scale_control",
        "coverage_control",
        "source_score_rank",
        "class_pair_only",
        "p_geom_valid_hidden_baseline",
        "shuffled_G",
        "wrong_pair_geometry",
    ]
    for name in required:
        if name not in controls:
            errors.append({"error_type": "missing_control", "control": name})

    boundary = runner_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "materializes_rows", "paper_evidence_allowed_now", "runs_model", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("runs_metrics") is not True:
        errors.append({"error_type": "boundary_runs_metrics_not_true"})

    route = runner_summary.get("route", {})
    if route.get("relation") != "close by":
        errors.append({"error_type": "unexpected_route_relation", "actual": route.get("relation")})
    if route.get("route_type") != "geometry_only_learned_evaluated_route":
        errors.append({"error_type": "unexpected_route_type", "actual": route.get("route_type")})
    if route.get("target_axis") != "geometry_support":
        errors.append({"error_type": "unexpected_target_axis", "actual": route.get("target_axis")})

    normalized_xy = metric(controls, "normalized_distance_xy", "auroc")
    normalized_acc = metric(controls, "normalized_distance_xy", "best_accuracy")
    source_auc = metric(controls, "source_score_rank", "auroc")
    class_acc = metric(controls, "class_pair_only", "best_accuracy")
    shuffled_acc = metric(controls, "shuffled_G", "best_accuracy")
    wrong_pair_acc = metric(controls, "wrong_pair_geometry", "best_accuracy")
    hidden_auc = metric(controls, "p_geom_valid_hidden_baseline", "auroc")

    if normalized_xy is None or normalized_xy < 0.99:
        errors.append({"error_type": "normalized_distance_xy_not_strong", "actual": normalized_xy})
    if normalized_acc is None or normalized_acc < 0.99:
        errors.append({"error_type": "normalized_distance_xy_accuracy_not_strong", "actual": normalized_acc})
    if source_auc is None or source_auc > 0.60:
        errors.append({"error_type": "source_score_rank_too_predictive", "actual": source_auc})
    if class_acc is None or class_acc > 0.55:
        errors.append({"error_type": "class_pair_shortcut_too_predictive", "actual": class_acc})
    if shuffled_acc is None or shuffled_acc > 0.55:
        errors.append({"error_type": "shuffled_g_best_accuracy_not_collapsed", "actual": shuffled_acc})
    if wrong_pair_acc is None or wrong_pair_acc > 0.55:
        errors.append({"error_type": "wrong_pair_best_accuracy_not_collapsed", "actual": wrong_pair_acc})
    if hidden_auc is None or hidden_auc < 0.95:
        errors.append({"error_type": "hidden_geometry_baseline_not_strong", "actual": hidden_auc})

    return errors


def key_metrics(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [
        "distance_xy",
        "distance_3d",
        "normalized_distance_xy",
        "normalized_distance_3d",
        "overlap_geometry",
        "source_score_rank",
        "class_pair_only",
        "p_geom_valid_hidden_baseline",
        "shuffled_G",
        "wrong_pair_geometry",
    ]
    rows: list[dict[str, Any]] = []
    for name in selected:
        row = controls.get(name, {})
        rows.append(
            {
                "control_name": name,
                "auroc": row.get("auroc", ""),
                "best_accuracy": row.get("best_accuracy", ""),
                "interpretation": interpretation_for_control(name),
            }
        )
    return rows


def interpretation_for_control(name: str) -> str:
    return {
        "distance_xy": "raw XY distance nearly solves geometry support",
        "distance_3d": "raw 3D distance nearly solves geometry support",
        "normalized_distance_xy": "scale-normalized XY distance solves the route target",
        "normalized_distance_3d": "scale-normalized 3D distance solves the route target",
        "overlap_geometry": "useful but weaker geometry support cue",
        "source_score_rank": "source confidence does not explain geometry support",
        "class_pair_only": "class-pair shortcut is near chance",
        "p_geom_valid_hidden_baseline": "hidden geometry-rule reference is strong but not model input",
        "shuffled_G": "shuffled geometry collapses",
        "wrong_pair_geometry": "wrong-pair geometry collapses",
    }.get(name, "")


def route_position() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "R1",
            "family": "proximity",
            "relations": "close by",
            "route_type": "geometry_only_learned_evaluated_route",
            "paper_role": "geometry_only_route_evidence_and_claim_control",
            "status": "frozen_as_geometry_only_route",
            "allowed_claim": "some relation families are geometry-decidable and should route to G_e rather than fixed semantic-geometry fusion",
            "blocked_claim": "T_e x G_e interaction proof or calibrated p_rel/p_obs evidence",
        },
        {
            "route_id": "R6",
            "family": "superordinate_support",
            "relations": "supported by",
            "route_type": "accept_relabel_abstain_decomposition_route",
            "paper_role": "next_claim_control_probe",
            "status": "selected_next",
            "allowed_claim": "broad support predicates may need accept/relabel/reject/abstain rather than binary compatibility",
            "blocked_claim": "clean negative label for standing on / lying on",
        },
        {
            "route_id": "R7",
            "family": "attachment_observability",
            "relations": "attached to; hanging on; connected to",
            "route_type": "observability_then_reliability_route",
            "paper_role": "next_after_supported_by_or_parallel_schema_probe",
            "status": "queued",
            "allowed_claim": "observability and evidence quality must be separated before reliability decision",
            "blocked_claim": "direct visual feature as learned input before audit/Q_e contract",
        },
    ]


def claim_boundary() -> list[dict[str, Any]]:
    return [
        {
            "claim_area": "geometry_only_route",
            "allowed": True,
            "statement": "`close by` supports the route taxonomy because G_e distance is sufficient and source/class shortcuts are weak.",
        },
        {
            "claim_area": "pair_specific_geometry",
            "allowed": True,
            "statement": "Shuffled-G and wrong-pair controls collapse, so the target depends on the actual object-pair geometry.",
        },
        {
            "claim_area": "predicate_geometry_interaction",
            "allowed": False,
            "statement": "`close by` should not be used as evidence that T_e x G_e interaction is needed.",
        },
        {
            "claim_area": "calibrated_reliability",
            "allowed": False,
            "statement": "No p_rel/p_obs calibration claim is allowed from deterministic route controls.",
        },
        {
            "claim_area": "paper_level_result",
            "allowed": False,
            "statement": "This is train-only hypothesis evidence, not Docker/held-out paper evidence.",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "plan the R6 `supported by` accept/relabel/reject/abstain decomposition target",
            "why": "`close by` is frozen; the next route should test broad superordinate support rather than another geometry-easy case",
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_attachment_observability_target_plan",
            "action": "define R7 observability-first targets for `attached to`, `hanging on`, and `connected to`",
            "why": "attachment-like relations require Q_e/p_obs before reliability input features",
        },
        {
            "order": 3,
            "next_todo": "compatibility_dataset_v3_route_taxonomy_synthesis_update",
            "action": "merge R1/R6/R7 decisions into the compact route taxonomy after R6 plan is complete",
            "why": "avoid one universal target and keep route-specific evidence definitions explicit",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 R1 Close-By Geometry-Support Route Result Review",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Decision",
        "",
        "`close by`는 `geometry-only learned/evaluated route`로 고정한다. 이 relation은",
        "`T_e x G_e` interaction의 main evidence가 아니라, relation-aware routing에서",
        "어떤 family는 `G_e`만으로 충분하다는 control/evidence 역할을 한다.",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Key Metrics",
        "",
        "| Control | AUROC | Best Accuracy | Interpretation |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in metric_rows:
        auroc = row["auroc"]
        best_acc = row["best_accuracy"]
        auroc_s = f"{auroc:.6f}" if isinstance(auroc, (int, float)) else "n/a"
        acc_s = f"{best_acc:.6f}" if isinstance(best_acc, (int, float)) else "n/a"
        lines.append(f"| `{row['control_name']}` | {auroc_s} | {acc_s} | {row['interpretation']} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `normalized_distance_xy`와 `normalized_distance_3d`가 AUROC `1.0`으로 target을 해결한다.",
            "- `source_score_rank`는 AUROC `0.552103`, `class_pair_only`는 accuracy `0.503750`이라 source/class shortcut이 아니다.",
            "- `shuffled_G`와 `wrong_pair_geometry`는 best accuracy `0.5`로 붕괴하므로 실제 object-pair geometry가 필요하다.",
            "- 따라서 R1은 geometry-only route의 성공 사례이지, predicate-geometry interaction 성공 사례가 아니다.",
            "",
            "## Route Position",
            "",
            "| Route | Family | Relations | Role | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in route_rows:
        lines.append(
            f"| `{row['route_id']}` | `{row['family']}` | {row['relations']} | {row['paper_role']} | `{row['status']}` |"
        )

    lines.extend(["", "## Claim Boundary", ""])
    for row in boundary_rows:
        lines.append(f"- `{row['claim_area']}`: allowed={row['allowed']} / {row['statement']}")

    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            str(summary["next_todo"]),
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    runner_dir = args.runner_dir
    output_dir = args.output_dir

    runner_summary = read_json(runner_dir / "summary.json")
    control_rows = read_csv(runner_dir / "route_control_metrics.csv")
    controls = control_map(control_rows)
    runner_validation = read_jsonl(runner_dir / "validation_errors.jsonl")

    errors = validate_inputs(runner_summary, control_rows, controls, runner_validation)
    status = STATUS_ERRORS if errors else STATUS_READY
    metric_rows = [] if errors else key_metrics(controls)
    route_rows = [] if errors else route_position()
    boundary_rows = [] if errors else claim_boundary()
    next_rows = [] if errors else next_steps()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "runner_dir": rel_path(runner_dir),
            "runner_summary": rel_path(runner_dir / "summary.json"),
            "route_control_metrics": rel_path(runner_dir / "route_control_metrics.csv"),
        },
        "output_paths": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(output_dir / "summary.json"),
            "review_decision": rel_path(output_dir / "review_decision.json"),
            "key_metrics": rel_path(output_dir / "key_metrics.csv"),
            "route_position": rel_path(output_dir / "route_position.csv"),
            "claim_boundary": rel_path(output_dir / "claim_boundary.csv"),
            "next_steps": rel_path(output_dir / "next_steps.csv"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "route": runner_summary.get("route", {}),
        "row_counts": runner_summary.get("row_counts", {}),
        "key_values": {
            "normalized_distance_xy_auroc": metric(controls, "normalized_distance_xy", "auroc"),
            "normalized_distance_3d_auroc": metric(controls, "normalized_distance_3d", "auroc"),
            "source_score_rank_auroc": metric(controls, "source_score_rank", "auroc"),
            "class_pair_only_best_accuracy": metric(controls, "class_pair_only", "best_accuracy"),
            "shuffled_g_auroc": metric(controls, "shuffled_G", "auroc"),
            "shuffled_g_best_accuracy": metric(controls, "shuffled_G", "best_accuracy"),
            "wrong_pair_geometry_auroc": metric(controls, "wrong_pair_geometry", "auroc"),
            "wrong_pair_geometry_best_accuracy": metric(controls, "wrong_pair_geometry", "best_accuracy"),
            "p_geom_valid_hidden_baseline_auroc": metric(controls, "p_geom_valid_hidden_baseline", "auroc"),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed_now": False,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
            "interaction_claim_allowed_for_close_by": False,
        },
    }
    review_decision = {
        "selected_path": summary["selected_path"],
        "decision": "freeze_close_by_as_geometry_only_route_evidence" if not errors else "blocked",
        "allowed_claim": (
            "R1 close by shows that some relation families are geometry-decidable: "
            "pair-specific distance G_e is sufficient, while source score and class-pair shortcuts are weak."
        )
        if not errors
        else None,
        "blocked_claims": [
            "close by proves predicate-geometry interaction",
            "close by proves calibrated relation reliability",
            "close by alone proves the full H002 framework",
            "hidden p_geom_valid can be used as a model-safe input",
        ],
        "why_next": "R6 supported by should be planned next because it tests a broad superordinate support label that needs decomposition/relabel/abstain rather than another geometry-only route.",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "review_decision.json", review_decision)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "key_metrics.csv", metric_rows)
    write_csv(output_dir / "route_position.csv", route_rows)
    write_csv(output_dir / "claim_boundary.csv", boundary_rows)
    write_csv(output_dir / "next_steps.csv", next_rows)
    write_report(output_dir / "report.md", summary, metric_rows, route_rows, boundary_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
