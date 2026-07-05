#!/usr/bin/env python3
"""Plan the scene/geometry-aware repair route for the H002 proximity LH target."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_path_decision_after_audit"
DEFAULT_FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v10_proximity_relation_family_feasibility_scan"
DEFAULT_TARGET_AUDIT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_target_independence_audit"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_repair_plan"

EXPECTED_PATH_STATUS = "h002_reliability_target_v12_proximity_lh_path_decision_select_scene_geometry_repair"
EXPECTED_PATH_NEXT = "reliability_target_v13_proximity_lh_scene_geometry_repair_plan"
EXPECTED_TARGET_AUDIT_STATUS = "h002_reliability_target_v12_proximity_lh_only_independence_blocked_object_pair_shortcut"
EXPECTED_FEASIBILITY_STATUS = "h002_reliability_target_v10_proximity_feasibility_lh_only_ready_not_bidirectional"

NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_candidate_mining"

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {
    "floor",
    "wall",
    "ceiling",
    "room",
    "door",
    "doorframe",
    "window",
    "blinds",
    "curtain",
}
GENERIC_LABELS = {"object", "item", "stuff", "thing"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--feasibility-dir", type=Path, default=DEFAULT_FEASIBILITY_DIR)
    parser.add_argument("--target-audit-dir", type=Path, default=DEFAULT_TARGET_AUDIT_DIR)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any, default: int = 999999) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def endpoint_type(label: str) -> str:
    if label in HARD_ROOM_SURFACES:
        return f"hard_room_surface:{label}"
    if label in STRUCTURAL_CONTEXT:
        return f"structural_context:{label}"
    return "object"


def p_geom_bin(value: Any) -> str:
    score = as_float(value)
    if score is None:
        return "missing"
    if score >= 0.95:
        return "very_high"
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium"
    return "low"


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    p_geom = as_float(row.get("p_geom_valid"))
    return {
        **row,
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "subject_object_label_pair": f"{subject_label}|{object_label}",
        "endpoint_cell": f"{endpoint_type(subject_label)}|{endpoint_type(object_label)}",
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "generic_endpoint_pair": subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS,
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "p_geom_valid_float": p_geom,
        "p_geom_bin": p_geom_bin(p_geom),
    }


def validate_inputs(path_decision: dict[str, Any], feasibility: dict[str, Any], target_audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": EXPECTED_PATH_STATUS, "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_decision_next", "expected": EXPECTED_PATH_NEXT, "actual": path_decision.get("next_todo")})
    if feasibility.get("status") != EXPECTED_FEASIBILITY_STATUS:
        errors.append({"error_type": "unexpected_feasibility_status", "expected": EXPECTED_FEASIBILITY_STATUS, "actual": feasibility.get("status")})
    if target_audit.get("status") != EXPECTED_TARGET_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_target_audit_status", "expected": EXPECTED_TARGET_AUDIT_STATUS, "actual": target_audit.get("status")})

    for name, payload in [("path_decision", path_decision), ("feasibility", feasibility), ("target_audit", target_audit)]:
        if payload.get("validation_errors") not in (0, None):
            errors.append({"error_type": "input_validation_errors_present", "input": name, "actual": payload.get("validation_errors")})
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "input_boundary_violation", "input": name, "key": key, "actual": boundary.get(key)})
    return errors


def read_repair_pool(lh_queue_path: Path) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    counts = Counter()
    errors: list[dict[str, Any]] = []
    for line_no, row in iter_jsonl(lh_queue_path):
        counts["lh_queue_rows_read"] += 1
        if row.get("predicate_family") != "proximity" or norm(row.get("predicate_label")) != "close by":
            continue
        counts["proximity_rows"] += 1
        enriched = enrich(row)
        if row.get("bucket_top100") != "RGA-LH":
            counts["not_rga_lh"] += 1
            continue
        if row.get("geometry_status") != "satisfied":
            counts["not_geometry_satisfied"] += 1
            continue
        if enriched["structural_pair"]:
            counts["structural_pair_excluded"] += 1
            continue
        if enriched["generic_endpoint_pair"]:
            counts["generic_endpoint_pair_excluded"] += 1
            continue
        if not row.get("prediction_id"):
            errors.append({"error_type": "missing_prediction_id", "line_no": line_no})
            continue
        rows.append(enriched)
        counts["repair_pool_rows"] += 1
    return rows, dict(counts), errors


def counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def group_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["subject_object_label_pair"])].append(row)

    inventory: list[dict[str, Any]] = []
    for label_pair, group_rows in grouped.items():
        scan_ids = {str(row.get("scan_id")) for row in group_rows}
        subgraphs = {str(row.get("subgraph_id")) for row in group_rows}
        label_match = Counter(str(row.get("label_match_status")) for row in group_rows)
        machine_hint = Counter(str(row.get("machine_hint")) for row in group_rows)
        rank_band = Counter(str(row.get("rank_band")) for row in group_rows)
        p_bins = Counter(str(row.get("p_geom_bin")) for row in group_rows)
        p_values = [row["p_geom_valid_float"] for row in group_rows if row.get("p_geom_valid_float") is not None]
        ranks = [row["semantic_rank_int"] for row in group_rows if row.get("semantic_rank_int") != 999999]
        row_count = len(group_rows)
        scene_context_diverse = len(scan_ids) >= 3 or len(subgraphs) >= 4
        hidden_axis_diverse = len(label_match) >= 2 and len(rank_band) >= 2
        geometry_witness_diverse = len(p_bins) >= 2 or (p_values and max(p_values) - min(p_values) >= 0.15)
        v13_block_candidate = row_count >= 6 and scene_context_diverse and (hidden_axis_diverse or geometry_witness_diverse)
        strong_v13_block_candidate = row_count >= 8 and scene_context_diverse and hidden_axis_diverse and geometry_witness_diverse
        inventory.append(
            {
                "subject_object_label_pair": label_pair,
                "rows": row_count,
                "unique_scans": len(scan_ids),
                "unique_subgraphs": len(subgraphs),
                "label_match_status_values": len(label_match),
                "machine_hint_values": len(machine_hint),
                "rank_band_values": len(rank_band),
                "p_geom_bin_values": len(p_bins),
                "p_geom_min": min(p_values) if p_values else None,
                "p_geom_max": max(p_values) if p_values else None,
                "semantic_rank_min": min(ranks) if ranks else None,
                "semantic_rank_max": max(ranks) if ranks else None,
                "scene_context_diverse": scene_context_diverse,
                "hidden_axis_diverse": hidden_axis_diverse,
                "geometry_witness_diverse": geometry_witness_diverse,
                "v13_block_candidate": v13_block_candidate,
                "strong_v13_block_candidate": strong_v13_block_candidate,
                "label_match_status_counts": json.dumps(counter_dict(label_match), sort_keys=True),
                "machine_hint_counts": json.dumps(counter_dict(machine_hint), sort_keys=True),
                "rank_band_counts": json.dumps(counter_dict(rank_band), sort_keys=True),
                "p_geom_bin_counts": json.dumps(counter_dict(p_bins), sort_keys=True),
            }
        )
    inventory.sort(
        key=lambda row: (
            not row["strong_v13_block_candidate"],
            not row["v13_block_candidate"],
            -int(row["rows"]),
            -int(row["unique_scans"]),
            str(row["subject_object_label_pair"]),
        )
    )
    return inventory


def plan_readiness(inventory: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_groups = [row for row in inventory if row["v13_block_candidate"]]
    strong_groups = [row for row in inventory if row["strong_v13_block_candidate"]]
    candidate_capacity = sum(min(int(row["rows"]), 8) for row in candidate_groups)
    strong_capacity = sum(min(int(row["rows"]), 8) for row in strong_groups)
    return {
        "repair_pool_rows": len(rows),
        "visible_pair_groups": len(inventory),
        "v13_block_candidate_groups": len(candidate_groups),
        "strong_v13_block_candidate_groups": len(strong_groups),
        "candidate_capacity_cap8": candidate_capacity,
        "strong_candidate_capacity_cap8": strong_capacity,
        "minimum_same_pair_mixed_groups_goal": 20,
        "candidate_group_goal_pass": len(candidate_groups) >= 20,
        "candidate_capacity_goal_pass": candidate_capacity >= 240,
        "recommended_label_sheet_rows": 240,
        "recommended_pair_blocks": 30,
        "recommended_rows_per_pair_block": 8,
        "posterior_smoke_allowed": False,
    }


def evidence_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v13_proximity_scene_geometry_evidence_contract_v1",
        "purpose": "Make proximity labels depend on local scene/geometry context instead of object-pair text alone.",
        "reviewer_visible_fields": [
            "blind_review_id",
            "review_card",
            "candidate_relation",
            "subject_label",
            "predicate_label",
            "object_label",
            "scene_context_summary_v13",
            "geometry_witness_summary_v13",
            "nearest_neighbor_context_v13",
            "local_density_context_v13",
            "duplicate_or_many_alternatives_context_v13",
            "crop_or_layout_evidence_v13",
            "review_question_v13",
            "relation_reliability_state_v13",
            "scene_usefulness_state_v13",
            "primary_reason_v13",
            "uncertainty_reason_v13",
            "review_notes_v13",
        ],
        "reviewer_hidden_audit_fields": [
            "scan_id",
            "subgraph_id",
            "subject_id",
            "object_id",
            "prediction_id",
            "source_queue",
            "semantic_rank",
            "semantic_score_norm",
            "p_geom_valid",
            "rank_band",
            "label_match_status",
            "machine_hint",
            "subject_object_label_pair",
            "target_construction_block",
        ],
        "allowed_visible_evidence": [
            "binned distance/overlap witness, not p_geom_valid",
            "object layout or crop evidence",
            "nearest-neighbor rank within the local object layout",
            "number of plausible nearby alternatives",
            "duplicate same-label object context",
            "short natural-language geometry witness explanation",
        ],
        "forbidden_visible_evidence": [
            "source semantic rank or score",
            "machine_hint",
            "label_match_status",
            "GT matched predicate names",
            "target construction bucket",
            "posterior score",
            "raw p_geom_valid numeric value",
        ],
    }


def target_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_v13_proximity_scene_geometry_target_schema_v1",
        "primary_target": "relation_reliability_state_v13",
        "relation_reliability_state_v13": [
            "accept_reliable_close_by",
            "reject_dense_relation_noise",
            "reject_trivial_or_context_only",
            "abstain_uncertain",
        ],
        "binary_mapping": {
            "accept_reliable_close_by": 1,
            "reject_dense_relation_noise": 0,
            "reject_trivial_or_context_only": 0,
            "abstain_uncertain": None,
        },
        "scene_usefulness_state_v13": [
            "useful_local_relation",
            "redundant_dense_neighborhood",
            "trivial_global_context",
            "not_evaluable",
        ],
        "primary_reason_v13": [
            "mutual_nearest_or_functional_neighbor",
            "clear_local_adjacency",
            "many_equally_near_alternatives",
            "duplicate_object_ambiguity",
            "structural_or_room_context_only",
            "geometry_evidence_insufficient",
            "visual_or_layout_evidence_insufficient",
        ],
        "uncertainty_reason_v13": [
            "none",
            "missing_layout_context",
            "occlusion_or_crop_gap",
            "ambiguous_dense_cluster",
            "object_identity_uncertain",
            "relation_definition_uncertain",
        ],
    }


def candidate_mining_contract(readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_v13_proximity_scene_geometry_candidate_mining_contract_v1",
        "next_todo": NEXT_TODO,
        "candidate_source": "train-only proximity RGA-LH rows with geometry_status=satisfied",
        "sampling_unit": "subject_object_label_pair block",
        "target_sheet_shape": {
            "recommended_rows": readiness["recommended_label_sheet_rows"],
            "recommended_pair_blocks": readiness["recommended_pair_blocks"],
            "recommended_rows_per_pair_block": readiness["recommended_rows_per_pair_block"],
        },
        "block_requirements": [
            "each selected subject_object_label_pair should have at least 6-8 candidate rows",
            "each block should span at least 3 scans or 4 subgraphs when possible",
            "each block should include hidden rank/label-match/p_geom diversity for post-label audit",
            "visible label surface must include local scene/geometry context, not only object labels",
        ],
        "post_label_gates": {
            "minimum_binary_rows": 120,
            "minimum_per_class": 50,
            "minimum_same_pair_mixed_groups": 20,
            "strict_slice_required_before_posterior": True,
            "posterior_smoke_allowed_before_gate": False,
        },
        "fallbacks_if_label_balance_fails": [
            "mine additional blocks from candidate groups with high scene-context diversity",
            "increase rows per pair block before changing relation family",
            "do not relabel by hidden label_match_status or machine_hint",
            "if same-pair mixed groups remain near zero, freeze proximity as diagnostic-only and route to attachment_deferred",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    readiness = summary["readiness"]
    lines = [
        "# H002 V13 Proximity LH Scene/Geometry Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Proceed to scene/geometry-aware candidate mining for the proximity LH branch. Do not run posterior smoke yet.",
        "",
        "## Why This Repair",
        "",
        "v12 failed because visible object-pair text determined the proxy label. v13 changes the label evidence, not the posterior model: the reviewer-visible packet must expose local scene/geometry context so the same object-pair can become reliable in one scene and unreliable in another.",
        "",
        "## Mining Capacity Snapshot",
        "",
        "```text",
        f"repair_pool_rows = {readiness['repair_pool_rows']}",
        f"visible_pair_groups = {readiness['visible_pair_groups']}",
        f"v13_block_candidate_groups = {readiness['v13_block_candidate_groups']}",
        f"strong_v13_block_candidate_groups = {readiness['strong_v13_block_candidate_groups']}",
        f"candidate_capacity_cap8 = {readiness['candidate_capacity_cap8']}",
        f"candidate_group_goal_pass = {readiness['candidate_group_goal_pass']}",
        f"candidate_capacity_goal_pass = {readiness['candidate_capacity_goal_pass']}",
        "```",
        "",
        "## Contract",
        "",
        "- Candidate source: train-only `close by` / proximity `RGA-LH` rows with satisfied geometry.",
        "- Sampling unit: subject-object visible label pair block.",
        "- Target label sheet: about 240 rows from about 30 pair blocks, 6-8 rows per block.",
        "- Required visible evidence: local layout, binned geometry witness, nearest-neighbor/density context, duplicate-object context.",
        "- Forbidden visible evidence: semantic rank, machine hint, label-match status, GT matched predicates, target bucket, posterior score.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
        "Posterior smoke remains blocked until the repaired target passes target-independence audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision_dir = as_abs(args.path_decision_dir)
    feasibility_dir = as_abs(args.feasibility_dir)
    target_audit_dir = as_abs(args.target_audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(path_decision_dir / "summary.json")
    feasibility = read_json(feasibility_dir / "summary.json")
    target_audit = read_json(target_audit_dir / "summary.json")
    validation_errors = validate_inputs(path_decision, feasibility, target_audit)

    repair_pool, input_counts, read_errors = read_repair_pool(args.lh_queue)
    validation_errors.extend(read_errors[:100])
    inventory = group_inventory(repair_pool)
    readiness = plan_readiness(inventory, repair_pool)
    status = (
        "h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_ready"
        if not validation_errors and readiness["candidate_group_goal_pass"] and readiness["candidate_capacity_goal_pass"]
        else "h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_blocked"
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "repair_plan": output_dir / "repair_plan.json",
        "evidence_contract": output_dir / "evidence_contract.json",
        "target_schema": output_dir / "target_schema_v13.json",
        "candidate_mining_contract": output_dir / "candidate_mining_contract.json",
        "repair_group_inventory": output_dir / "repair_group_inventory.csv",
        "top_repair_groups": output_dir / "top_repair_groups.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    repair_plan = {
        "schema_version": "h002_v13_proximity_scene_geometry_repair_plan_v1",
        "selected_route": "scene_geometry_aware_proximity_lh_target_repair",
        "repair_target": "relation_reliability_for_close_by_under_low_semantic_high_geometry",
        "main_change_from_v12": "label evidence changes from visible object-pair text to local scene/geometry evidence",
        "v12_branch_role": "diagnostic_only_negative_evidence",
        "not_changed": [
            "RGA framework remains bidirectional HL/LH",
            "multi-view remains audit evidence, not model input",
            "posterior smoke remains blocked",
            "train-only hypothesis stage",
        ],
        "required_artifacts_next": [
            "scene/geometry-aware candidate sheet",
            "hidden audit manifest",
            "review cards with local layout and binned geometry witness",
            "label schema with accept/reject/abstain",
            "post-label target-independence audit",
        ],
    }
    summary = {
        "schema_version": "h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
            "feasibility_summary": rel_path(feasibility_dir / "summary.json"),
            "target_audit_summary": rel_path(target_audit_dir / "summary.json"),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "input_counts": input_counts,
        "readiness": readiness,
        "repair_plan": repair_plan,
        "next_todo": NEXT_TODO,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "rga_redefined_as_lh_only": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["repair_plan"], repair_plan)
    write_json(output_paths["evidence_contract"], evidence_contract())
    write_json(output_paths["target_schema"], target_schema())
    write_json(output_paths["candidate_mining_contract"], candidate_mining_contract(readiness))
    write_csv(output_paths["repair_group_inventory"], inventory)
    write_jsonl(output_paths["top_repair_groups"], inventory[:80])
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    readiness = summary["readiness"]
    print(f"status={summary['status']}")
    print(f"repair_pool_rows={readiness['repair_pool_rows']}")
    print(f"v13_block_candidate_groups={readiness['v13_block_candidate_groups']}")
    print(f"candidate_capacity_cap8={readiness['candidate_capacity_cap8']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
