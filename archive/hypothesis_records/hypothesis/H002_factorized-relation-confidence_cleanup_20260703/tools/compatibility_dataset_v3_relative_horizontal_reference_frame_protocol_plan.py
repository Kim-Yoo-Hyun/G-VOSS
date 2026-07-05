#!/usr/bin/env python3
"""Plan the H002 relative-horizontal reference-frame protocol."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SWEEP_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan"
)

EXPECTED_SWEEP_STATUS = "h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready"
EXPECTED_SWEEP_NEXT = "compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan_input_errors"
SELECTED_PATH = "relative_horizontal_reference_frame_source_inventory_before_materialization"
NEXT_TODO = "compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan"

RELATIVE_HORIZONTAL_PREDICATES = ["left", "right", "front", "behind", "in front of"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP_DIR)
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    sweep_summary: dict[str, Any],
    family_sweep: list[dict[str, str]],
    predicate_queue: list[dict[str, str]],
    sweep_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if sweep_summary.get("status") != EXPECTED_SWEEP_STATUS:
        errors.append({"input": "sweep", "error_type": "unexpected_status", "actual": sweep_summary.get("status")})
    if sweep_summary.get("next_todo") != EXPECTED_SWEEP_NEXT:
        errors.append({"input": "sweep", "error_type": "unexpected_next_todo", "actual": sweep_summary.get("next_todo")})
    if sweep_summary.get("validation_errors") != 0:
        errors.append({"input": "sweep", "error_type": "validation_errors_present", "actual": sweep_summary.get("validation_errors")})
    if read_jsonl(sweep_dir / "validation_errors.jsonl"):
        errors.append({"input": "sweep", "error_type": "validation_error_rows_present"})

    boundary = sweep_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"input": "sweep", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    relative_rows = [row for row in family_sweep if row.get("family") == "relative_horizontal"]
    if not relative_rows:
        errors.append({"input": "family_sweep", "error_type": "missing_relative_horizontal"})
    else:
        row = relative_rows[0]
        if row.get("rank") != "1":
            errors.append({"input": "family_sweep", "error_type": "relative_horizontal_not_first", "actual": row.get("rank")})
        if row.get("next_todo_if_selected") != EXPECTED_SWEEP_NEXT:
            errors.append(
                {
                    "input": "family_sweep",
                    "error_type": "unexpected_relative_horizontal_next",
                    "actual": row.get("next_todo_if_selected"),
                }
            )

    queue_predicates = {
        row.get("predicate")
        for row in predicate_queue
        if row.get("family") == "relative_horizontal"
    }
    missing = sorted(set(RELATIVE_HORIZONTAL_PREDICATES) - queue_predicates)
    if missing:
        errors.append({"input": "predicate_queue", "error_type": "missing_relative_horizontal_predicates", "missing": missing})
    return errors


def frame_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "frame_id": "scene_aligned_world_xy",
            "route_status": "source_inventory_first",
            "definition": "Use the aligned 3RScan/scene coordinate frame and evaluate signed horizontal displacement on x/y axes.",
            "allowed_for_main": "conditional",
            "required_evidence": "stable aligned coordinate frame; gravity axis known; x/y axes documented",
            "main_risk": "left/right/front/behind labels may not be annotated in this global frame",
            "q_e_if_missing_or_conflicting": "frame_ambiguous",
        },
        {
            "frame_id": "view_or_camera_frame",
            "route_status": "audit_or_Q_e_first",
            "definition": "Use image/view direction where left/right are relative to an observer or camera.",
            "allowed_for_main": "not_until_view_source_and_wrong_view_controls_exist",
            "required_evidence": "co-visible view, camera extrinsic, subject/object projected positions",
            "main_risk": "multiple views can disagree; selecting a convenient view is a shortcut",
            "q_e_if_missing_or_conflicting": "view_frame_unavailable_or_disagrees",
        },
        {
            "frame_id": "object_centric_front_axis",
            "route_status": "diagnostic_or_deferred",
            "definition": "Use subject/object canonical orientation to define front/behind.",
            "allowed_for_main": "no_for_initial_protocol",
            "required_evidence": "semantic object front orientation, not just OBB major axis",
            "main_risk": "OBB axes are geometric, not semantic front directions",
            "q_e_if_missing_or_conflicting": "object_front_axis_unknown",
        },
        {
            "frame_id": "layout_or_room_frame",
            "route_status": "diagnostic",
            "definition": "Use room-layout axes if a layout coordinate system is available.",
            "allowed_for_main": "no_for_initial_protocol",
            "required_evidence": "room/layout frame with documented orientation",
            "main_risk": "layout frame can differ from annotator/camera frame",
            "q_e_if_missing_or_conflicting": "layout_frame_unknown",
        },
    ]


def predicate_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "predicate": "left",
            "axis_pair": "left/right",
            "initial_role": "primary_reference_axis",
            "candidate_positive_condition": "subject has negative or positive signed lateral offset under the frozen frame, depending on the selected convention",
            "hard_negative": "same pair geometry with predicate `right`",
            "required_controls": "axis sign flip; wrong-frame rotation; subject-object swap",
            "fallback_if_family_fails": "run left/right-only probe before discarding relative_horizontal",
        },
        {
            "predicate": "right",
            "axis_pair": "left/right",
            "initial_role": "primary_reference_axis",
            "candidate_positive_condition": "opposite signed lateral offset from `left` under the same frozen frame",
            "hard_negative": "same pair geometry with predicate `left`",
            "required_controls": "axis sign flip; wrong-frame rotation; subject-object swap",
            "fallback_if_family_fails": "run left/right-only probe before discarding relative_horizontal",
        },
        {
            "predicate": "front",
            "axis_pair": "front/behind",
            "initial_role": "primary_reference_axis_with_frame_caveat",
            "candidate_positive_condition": "subject has signed longitudinal offset under the frozen front axis",
            "hard_negative": "same pair geometry with predicate `behind`",
            "required_controls": "front-axis reversal; wrong-frame rotation; view-frame disagreement",
            "fallback_if_family_fails": "run front/behind-only probe; demote if front-axis contract is unavailable",
        },
        {
            "predicate": "behind",
            "axis_pair": "front/behind",
            "initial_role": "primary_reference_axis_with_frame_caveat",
            "candidate_positive_condition": "opposite signed longitudinal offset from `front` under the same frozen frame",
            "hard_negative": "same pair geometry with predicate `front` or `in front of`",
            "required_controls": "front-axis reversal; wrong-frame rotation; view-frame disagreement",
            "fallback_if_family_fails": "run front/behind-only probe; demote if front-axis contract is unavailable",
        },
        {
            "predicate": "in front of",
            "axis_pair": "front/behind",
            "initial_role": "secondary_or_diagnostic_alias",
            "candidate_positive_condition": "same as `front` only if label ontology confirms alias behavior",
            "hard_negative": "same pair geometry with predicate `behind`",
            "required_controls": "alias consistency with `front`; front-axis reversal",
            "fallback_if_family_fails": "keep diagnostic unless alias mapping is verified in source inventory",
        },
    ]


def geometry_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "block": "G_e_horizontal",
            "field": "delta_centroid_xy",
            "definition": "subject centroid minus object centroid projected to the scene horizontal plane",
            "predicate_independent": True,
            "allowed_model_input": True,
            "use": "raw horizontal geometry evidence before predicate interpretation",
            "risk": "axis convention can encode the target if frame is chosen post hoc",
        },
        {
            "block": "G_e_horizontal",
            "field": "signed_lateral_offset",
            "definition": "delta projected onto the selected lateral axis",
            "predicate_independent": True,
            "allowed_model_input": True,
            "use": "shared evidence for left/right compatibility",
            "risk": "must be identical for same-G left/right predicate-flip rows",
        },
        {
            "block": "G_e_horizontal",
            "field": "signed_longitudinal_offset",
            "definition": "delta projected onto the selected front/back axis",
            "predicate_independent": True,
            "allowed_model_input": True,
            "use": "shared evidence for front/behind compatibility",
            "risk": "front axis must be frozen before target construction",
        },
        {
            "block": "G_e_horizontal",
            "field": "horizontal_distance",
            "definition": "Euclidean distance in the horizontal plane",
            "predicate_independent": True,
            "allowed_model_input": True,
            "use": "near/far and ambiguity support, not direction by itself",
            "risk": "can become proximity shortcut if target rows differ in distance distribution",
        },
        {
            "block": "G_e_horizontal",
            "field": "overlap_or_same_position_margin",
            "definition": "extent overlap and small-offset band around zero signed offset",
            "predicate_independent": True,
            "allowed_model_input": True,
            "use": "Q_e ambiguity support for relations too close to directional boundary",
            "risk": "do not force binary labels near zero-margin rows",
        },
    ]


def qe_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "block": "Q_e_frame",
            "field": "reference_frame_available",
            "definition": "selected frame and axis convention are documented for the scan/pair",
            "decision_role": "p_obs",
            "not_relation_truth": True,
        },
        {
            "block": "Q_e_frame",
            "field": "frame_disagreement_flag",
            "definition": "world/view/object/layout frame variants disagree on predicate sign",
            "decision_role": "abstain_or_diagnostic",
            "not_relation_truth": True,
        },
        {
            "block": "Q_e_frame",
            "field": "near_axis_boundary_flag",
            "definition": "absolute signed offset below frozen margin threshold",
            "decision_role": "abstain_or_low_observability",
            "not_relation_truth": True,
        },
        {
            "block": "Q_e_frame",
            "field": "camera_view_available",
            "definition": "at least one co-visible RGB-D frame with usable projection exists",
            "decision_role": "view-frame audit only at first",
            "not_relation_truth": True,
        },
        {
            "block": "Q_e_frame",
            "field": "object_front_axis_available",
            "definition": "semantic object-facing orientation is available from a trusted source",
            "decision_role": "front/behind observability",
            "not_relation_truth": True,
        },
    ]


def target_construction_rows() -> list[dict[str, Any]]:
    return [
        {
            "target_component": "gt_anchor",
            "definition": "exact train-side GT relation for left/right/front/behind/in front of",
            "allowed_for_main": True,
            "requirements": "frame contract selected before anchor use; both endpoint centroids/OBBs available",
            "leakage_control": "GT predicate hidden from model-safe rows",
        },
        {
            "target_component": "same_geometry_predicate_flip",
            "definition": "create the opposite predicate over the same directed pair geometry",
            "allowed_for_main": True,
            "requirements": "left<->right or front/in-front-of<->behind pair; identical G_e for both rows",
            "leakage_control": "generated flip flag hidden; paired rows share CV group",
        },
        {
            "target_component": "wrong_frame_counterfactual",
            "definition": "evaluate labels under a rotated/reversed frame as a control, not as a new main target",
            "allowed_for_main": False,
            "requirements": "frozen wrong-frame transform",
            "leakage_control": "wrong-frame id hidden from main model view",
        },
        {
            "target_component": "frame_ambiguous_rows",
            "definition": "rows where world/view/object/layout frames disagree or signed margin is near zero",
            "allowed_for_main": False,
            "requirements": "sent to Q_e/p_obs or diagnostic abstain",
            "leakage_control": "do not force accept/reject labels",
        },
        {
            "target_component": "no_gt_pairs",
            "definition": "object pairs without horizontal relation annotation",
            "allowed_for_main": False,
            "requirements": "diagnostic only unless independently audited",
            "leakage_control": "do not treat missing GT as false",
        },
    ]


def control_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "H1",
            "name": "same-G predicate flip",
            "requirement": "left/right and front/behind paired rows must have identical G_e and differ only in T_e predicate",
            "blocks_materialization": True,
        },
        {
            "control_id": "H2",
            "name": "wrong-frame rotation",
            "requirement": "rotate or swap frame axes; compatibility should collapse if frame evidence is essential",
            "blocks_promotion": True,
        },
        {
            "control_id": "H3",
            "name": "axis sign flip",
            "requirement": "flip lateral or longitudinal signed offset; predictions should invert or degrade",
            "blocks_promotion": True,
        },
        {
            "control_id": "H4",
            "name": "subject-object swap",
            "requirement": "swap endpoints and verify directional relation changes consistently",
            "blocks_promotion": True,
        },
        {
            "control_id": "H5",
            "name": "predicate alias audit",
            "requirement": "`front` and `in front of` cannot be merged until source inventory confirms alias behavior",
            "blocks_materialization": False,
        },
        {
            "control_id": "H6",
            "name": "class-pair/source shortcut",
            "requirement": "class-pair, predicate frequency, source score/rank, and scan/endpoint probes must not solve the target",
            "blocks_promotion": True,
        },
        {
            "control_id": "H7",
            "name": "axis-boundary abstain",
            "requirement": "near-zero signed-offset rows become Q_e/abstain diagnostics, not binary labels",
            "blocks_materialization": True,
        },
    ]


def blocked_field_rows() -> list[dict[str, Any]]:
    return [
        {"field": "gt_predicate_label", "reason": "target source", "allowed_in_model": False},
        {"field": "generated_flip_flag", "reason": "construction metadata", "allowed_in_model": False},
        {"field": "target_compatibility_label", "reason": "label", "allowed_in_model": False},
        {"field": "chosen_frame_matches_gt", "reason": "post-hoc target shortcut", "allowed_in_model": False},
        {"field": "direction_bucket_left_right_front_behind", "reason": "discretized construction proxy", "allowed_in_model": False},
        {"field": "source_score_or_rank", "reason": "Z_e not allowed in C_e test", "allowed_in_model": False},
        {"field": "scan_or_endpoint_id_raw", "reason": "identity leakage", "allowed_in_model": False},
        {"field": "frame_disagreement_label", "reason": "Q_e/audit field, not relation truth", "allowed_in_model": False},
    ]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "view": "T_only",
            "allowed_blocks": "predicate text/label; optional object class text",
            "purpose": "semantic-only baseline",
            "must_exclude": "G_e; Q_e; Z_e; GT/construction fields",
        },
        {
            "view": "G_only",
            "allowed_blocks": "G_e_horizontal raw signed offsets and distance only",
            "purpose": "geometry-only collapse check under same-G predicate flips",
            "must_exclude": "predicate; source score; GT/construction fields",
        },
        {
            "view": "TG_concat",
            "allowed_blocks": "T_e + G_e_horizontal",
            "purpose": "plain fusion baseline",
            "must_exclude": "Z_e and construction fields",
        },
        {
            "view": "C_e_interaction",
            "allowed_blocks": "predicate-conditioned interaction between T_e and G_e_horizontal",
            "purpose": "main compatibility mechanism probe",
            "must_exclude": "Z_e; GT/construction fields; frame labels derived from target",
        },
        {
            "view": "C_e_plus_Q",
            "allowed_blocks": "C_e + Q_e_frame",
            "purpose": "selective decision / p_obs diagnostic after compatibility is established",
            "must_exclude": "Q_e as direct relation truth",
        },
    ]


def next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Scan train-side relative-horizontal anchors and geometry/view sources before materializing rows.",
        "must_measure": [
            "left/right/front/behind/in-front-of GT anchor counts",
            "3RScan semseg OBB and centroid join rate",
            "scene-aligned horizontal-axis availability",
            "camera/view-frame availability if image frames are needed",
            "same-G predicate-flip capacity for left/right and front/behind",
            "front vs in-front-of alias behavior",
            "near-axis-boundary ambiguous row count",
            "class-pair, scan, and endpoint concentration",
        ],
        "must_not_do": [
            "do not materialize model rows yet",
            "do not train a learned smoke model",
            "do not use validation/test",
            "do not select a frame after seeing target performance",
            "do not treat no-GT pairs as false",
            "do not merge front and in front of before alias audit",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Relative-Horizontal Reference-Frame Protocol Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Decision

`relative_horizontal` is not ready for direct materialization. The first requirement is
a reference-frame protocol because `left`, `right`, `front`, `behind`, and `in front of`
can change meaning under world, view, layout, or object-centric frames.

## Protocol

The initial route is source inventory first:

```text
T_e = horizontal predicate text/label
G_e_horizontal = predicate-independent horizontal displacement under a frozen frame
Q_e_frame = frame availability, frame disagreement, and near-axis-boundary ambiguity
C_e = compatibility(T_e, G_e_horizontal), excluding Z_e
```

World/scene-aligned `xy` geometry is the first source-inventory candidate, but it is
not accepted as the main frame until wrong-frame, sign-flip, subject/object swap, and
frame-disagreement controls are defined.

## Predicate-Level Fallback

If the family-level probe fails, do not discard the whole family. Split into:

```text
left/right
front/behind
in front of alias/diagnostic
```

Each subset gets its own schema, capacity, shortcut, and route decision.

## Boundary

This is a train-only protocol artifact. It does not use validation/test, train a model,
or promote H002 to paper evidence.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sweep_summary = read_json(args.sweep_dir / "summary.json")
    family_sweep = read_csv(args.sweep_dir / "family_sweep_plan.csv")
    predicate_queue = read_csv(args.sweep_dir / "predicate_probe_queue.csv")
    validation_errors = validate_inputs(sweep_summary, family_sweep, predicate_queue, args.sweep_dir)

    frame_rows = frame_protocol_rows()
    predicate_rows = predicate_protocol_rows()
    geometry_rows = geometry_schema_rows()
    qe_rows = qe_schema_rows()
    target_rows = target_construction_rows()
    control_rows = control_plan_rows()
    blocked_rows = blocked_field_rows()
    view_rows = model_view_rows()
    next_contract = next_runner_contract()

    if not any(row["frame_id"] == "scene_aligned_world_xy" for row in frame_rows):
        validation_errors.append({"error_type": "missing_world_frame_candidate"})
    if not any(row["frame_id"] == "view_or_camera_frame" for row in frame_rows):
        validation_errors.append({"error_type": "missing_view_frame_candidate"})
    if not any(row["predicate"] == "in front of" and "diagnostic" in row["initial_role"] for row in predicate_rows):
        validation_errors.append({"error_type": "missing_in_front_of_diagnostic_role"})
    if not any(row["name"] == "wrong-frame rotation" for row in control_rows):
        validation_errors.append({"error_type": "missing_wrong_frame_control"})
    if not any(row["name"] == "same-G predicate flip" for row in control_rows):
        validation_errors.append({"error_type": "missing_same_g_predicate_flip_control"})
    if not any(row["field"] == "source_score_or_rank" and row["allowed_in_model"] is False for row in blocked_rows):
        validation_errors.append({"error_type": "missing_source_score_block"})
    if not any(row["view"] == "C_e_interaction" for row in view_rows):
        validation_errors.append({"error_type": "missing_compatibility_model_view"})

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if validation_errors else SELECTED_PATH,
        "next_todo": None if validation_errors else NEXT_TODO,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "sweep_plan": rel_path(args.sweep_dir),
            "sweep_summary": rel_path(args.sweep_dir / "summary.json"),
            "family_sweep_plan": rel_path(args.sweep_dir / "family_sweep_plan.csv"),
            "predicate_probe_queue": rel_path(args.sweep_dir / "predicate_probe_queue.csv"),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "frame_protocol": rel_path(args.output_dir / "frame_protocol.csv"),
            "predicate_protocol": rel_path(args.output_dir / "predicate_protocol.csv"),
            "geometry_evidence_schema": rel_path(args.output_dir / "geometry_evidence_schema.csv"),
            "qe_observability_schema": rel_path(args.output_dir / "qe_observability_schema.csv"),
            "target_construction_plan": rel_path(args.output_dir / "target_construction_plan.csv"),
            "control_plan": rel_path(args.output_dir / "control_plan.csv"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "model_views": rel_path(args.output_dir / "model_views.csv"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "frame_protocol_rows": len(frame_rows),
            "predicate_protocol_rows": len(predicate_rows),
            "geometry_schema_rows": len(geometry_rows),
            "qe_schema_rows": len(qe_rows),
            "target_construction_rows": len(target_rows),
            "control_rows": len(control_rows),
            "blocked_field_rows": len(blocked_rows),
            "model_view_rows": len(view_rows),
        },
        "selected_family": "relative_horizontal",
        "selected_predicates": RELATIVE_HORIZONTAL_PREDICATES,
        "initial_route": "source_inventory_before_materialization",
        "predicate_level_fallback": "left/right, front/behind, and in-front-of alias diagnostics if family-level route fails",
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_protocol_plan",
            "test_usage": False,
            "validation_usage": False,
            "materializes_rows": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "frame_protocol.csv", frame_rows)
    write_csv(args.output_dir / "predicate_protocol.csv", predicate_rows)
    write_csv(args.output_dir / "geometry_evidence_schema.csv", geometry_rows)
    write_csv(args.output_dir / "qe_observability_schema.csv", qe_rows)
    write_csv(args.output_dir / "target_construction_plan.csv", target_rows)
    write_csv(args.output_dir / "control_plan.csv", control_rows)
    write_csv(args.output_dir / "blocked_fields.csv", blocked_rows)
    write_csv(args.output_dir / "model_views.csv", view_rows)
    write_json(args.output_dir / "next_runner_contract.json", next_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_report(args.output_dir / "report.md", summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
