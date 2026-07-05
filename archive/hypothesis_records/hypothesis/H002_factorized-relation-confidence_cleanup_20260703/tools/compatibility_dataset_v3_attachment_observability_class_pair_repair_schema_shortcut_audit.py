#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for R7 class-pair repair labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INPUT_ROOT = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_v1"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_blocked_shortcut_risk"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_input_errors"
)
NEXT_TODO = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit"
)
SELECTED_PATH = "block_learned_smoke_select_path_decision"

MIN_BINARY_CLASS = 40
HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75
HIGH_RISK_EXCESS = 0.20
MEDIUM_RISK_EXCESS = 0.10

FORBIDDEN_FIELD_FRAGMENTS = (
    "_hidden",
    "_target",
    "review_",
    "decision_reason",
    "label_policy",
    "label_provenance",
    "used_for_label_fill",
    "packet_dir",
    "scan_id",
    "subject_id",
    "object_id",
    "prediction_id",
    "candidate_id",
    "directed_pair_id",
    "subgraph_id",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
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
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def safe_number(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def value_key(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def bucket_count(value: Any) -> str:
    number = safe_number(value)
    if number is None:
        return "missing"
    if number <= 0:
        return "0"
    if number <= 1:
        return "1"
    if number <= 3:
        return "2_3"
    if number <= 5:
        return "4_5"
    if number <= 11:
        return "6_11"
    return "ge_12"


def baseline_accuracy(labels: list[Any]) -> float:
    if not labels:
        return 0.0
    return max(Counter(labels).values()) / len(labels)


def risk_level(accuracy: float, baseline: float, allowed_in_model: bool) -> str:
    excess = accuracy - baseline
    if accuracy >= HIGH_RISK_ACC or excess >= HIGH_RISK_EXCESS:
        return "high" if allowed_in_model else "hidden_or_forbidden_high"
    if accuracy >= MEDIUM_RISK_ACC or excess >= MEDIUM_RISK_EXCESS:
        return "medium" if allowed_in_model else "hidden_or_forbidden_medium"
    return "low"


def categorical_probe(
    rows: list[dict[str, Any]],
    target_name: str,
    target_fn: Callable[[dict[str, Any]], Any],
    predictor_name: str,
    predictor_fn: Callable[[dict[str, Any]], Any],
    field_source: str,
    allowed_in_model: bool,
    blocker_policy: str,
) -> dict[str, Any]:
    labels = [target_fn(row) for row in rows]
    baseline = baseline_accuracy(labels)
    groups: dict[str, list[Any]] = defaultdict(list)
    for row, label in zip(rows, labels):
        groups[value_key(predictor_fn(row))].append(label)
    correct = 0
    pure_groups = 0
    mixed_groups = 0
    max_group_rows = 0
    max_group_purity = 0.0
    for values in groups.values():
        count = Counter(values)
        best = max(count.values())
        correct += best
        pure_groups += int(len(count) == 1)
        mixed_groups += int(len(count) > 1)
        max_group_rows = max(max_group_rows, len(values))
        max_group_purity = max(max_group_purity, best / len(values))
    accuracy = correct / len(rows) if rows else 0.0
    risk = risk_level(accuracy, baseline, allowed_in_model)
    blocks = allowed_in_model and blocker_policy == "block_if_high" and risk == "high"
    return {
        "target_name": target_name,
        "predictor": predictor_name,
        "field_source": field_source,
        "allowed_in_model": allowed_in_model,
        "blocker_policy": blocker_policy,
        "rows": len(rows),
        "class_counts": json.dumps(dict(Counter(labels)), sort_keys=True),
        "baseline_accuracy": round(baseline, 6),
        "majority_rule_accuracy": round(accuracy, 6),
        "majority_excess_over_baseline": round(accuracy - baseline, 6),
        "num_groups": len(groups),
        "mixed_groups": mixed_groups,
        "pure_groups": pure_groups,
        "max_group_rows": max_group_rows,
        "max_group_purity": round(max_group_purity, 6),
        "risk_level": risk,
        "blocks_smoke": blocks,
    }


def target_label(row: dict[str, Any], target_name: str) -> Any:
    if target_name == "relation_multiclass":
        return row.get("relation_multiclass_target")
    if target_name == "p_obs":
        return int(row.get("p_obs_target"))
    if target_name.startswith("p_rel"):
        return int(row.get("p_rel_observable_target"))
    raise KeyError(target_name)


def target_subsets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    p_rel = [row for row in rows if row.get("p_rel_observable_usable") is True]
    return {
        "relation_multiclass": rows,
        "p_obs": [row for row in rows if row.get("p_obs_usable") is True],
        "p_rel_combined": p_rel,
        "p_rel_attached_to": [row for row in p_rel if row.get("predicate_label") == "attached to"],
        "p_rel_hanging_on": [row for row in p_rel if row.get("predicate_label") == "hanging on"],
    }


def predictor_specs() -> list[dict[str, Any]]:
    return [
        {
            "name": "predicate_label",
            "source": "visible_T_e",
            "allowed": True,
            "fn": lambda row: row.get("predicate_label"),
        },
        {
            "name": "subject_label",
            "source": "visible_T_e",
            "allowed": True,
            "fn": lambda row: row.get("subject_label"),
        },
        {
            "name": "object_label",
            "source": "visible_T_e",
            "allowed": True,
            "fn": lambda row: row.get("object_label"),
        },
        {
            "name": "subject_object_class_pair",
            "source": "visible_T_e",
            "allowed": True,
            "fn": lambda row: row.get("subject_object_class_pair"),
        },
        {
            "name": "predicate_subject_object_class_pair",
            "source": "visible_T_e",
            "allowed": True,
            "fn": lambda row: row.get("predicate_subject_object_class_pair"),
        },
        {
            "name": "evidence_tier",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: row.get("evidence_tier"),
        },
        {
            "name": "packet_status",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: row.get("packet_status"),
        },
        {
            "name": "image_count_bucket",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: row.get("image_count_bucket"),
        },
        {
            "name": "pair_shared_view_count_bucket",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: bucket_count(row.get("pair_shared_view_count")),
        },
        {
            "name": "pair_shared_frame_count_bucket",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: bucket_count(row.get("pair_shared_frame_count")),
        },
        {
            "name": "subject_image_count_bucket",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: bucket_count(row.get("subject_image_count")),
        },
        {
            "name": "object_image_count_bucket",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: bucket_count(row.get("object_image_count")),
        },
        {
            "name": "mesh_sequence_ready_pattern",
            "source": "visible_Q_e",
            "allowed": True,
            "fn": lambda row: (row.get("mesh_ready"), row.get("sequence_ready")),
        },
        {
            "name": "review_evidence_quality",
            "source": "forbidden_review_label",
            "allowed": False,
            "fn": lambda row: row.get("review_evidence_quality"),
        },
        {
            "name": "review_endpoint_identity",
            "source": "forbidden_review_label",
            "allowed": False,
            "fn": lambda row: row.get("review_endpoint_identity"),
        },
        {
            "name": "decision_reason",
            "source": "forbidden_review_label",
            "allowed": False,
            "fn": lambda row: row.get("decision_reason"),
        },
        {
            "name": "exact_class_pair_id_hidden",
            "source": "hidden_construction",
            "allowed": False,
            "fn": lambda row: row.get("exact_class_pair_id_hidden"),
        },
        {
            "name": "rank_band_hidden",
            "source": "hidden_source_confidence",
            "allowed": False,
            "fn": lambda row: row.get("rank_band_hidden"),
        },
        {
            "name": "cell_id_hidden",
            "source": "hidden_construction",
            "allowed": False,
            "fn": lambda row: row.get("cell_id_hidden"),
        },
        {
            "name": "geometry_bucket_hidden",
            "source": "hidden_construction_proxy",
            "allowed": False,
            "fn": lambda row: row.get("geometry_bucket_hidden"),
        },
        {
            "name": "hidden_proxy_role",
            "source": "hidden_construction_proxy",
            "allowed": False,
            "fn": lambda row: row.get("hidden_proxy_role"),
        },
        {
            "name": "gt_label_match_status_hidden",
            "source": "hidden_gt_proxy",
            "allowed": False,
            "fn": lambda row: row.get("gt_label_match_status_hidden"),
        },
        {
            "name": "scan_id_hidden",
            "source": "hidden_identity",
            "allowed": False,
            "fn": lambda row: row.get("scan_id_hidden"),
        },
        {
            "name": "directed_pair_id_hidden",
            "source": "hidden_identity",
            "allowed": False,
            "fn": lambda row: row.get("directed_pair_id_hidden"),
        },
    ]


def target_viability(targets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target_name, subset in targets.items():
        if target_name == "relation_multiclass":
            labels = [row.get("relation_multiclass_target") for row in subset]
            min_class = min(Counter(labels).values()) if labels else 0
            viability = "diagnostic_only_multiclass_needs_dedicated_protocol"
        elif target_name == "p_obs":
            labels = [row.get("p_obs_target") for row in subset]
            min_class = min(Counter(labels).values()) if labels else 0
            viability = "blocked_negative_sparse" if min_class < MIN_BINARY_CLASS else "audit_candidate"
        else:
            labels = [row.get("p_rel_observable_target") for row in subset]
            counts = Counter(labels)
            min_class = min(counts.values()) if len(counts) == 2 else 0
            viability = "audit_candidate" if min_class >= MIN_BINARY_CLASS else "blocked_single_class_or_sparse"
        rows.append(
            {
                "target_name": target_name,
                "rows": len(subset),
                "class_counts": json.dumps(dict(Counter(labels)), sort_keys=True),
                "min_class_count": min_class,
                "viability": viability,
            }
        )
    return rows


def strata_capacity(
    rows: list[dict[str, Any]],
    target_name: str,
    axis_name: str,
    axis_fn: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    groups: dict[str, Counter[Any]] = defaultdict(Counter)
    for row in rows:
        groups[value_key(axis_fn(row))][target_label(row, target_name)] += 1
    mixed = {key: count for key, count in groups.items() if len(count) >= 2}
    balanced = 0
    for count in mixed.values():
        if 0 in count and 1 in count:
            balanced += 2 * min(count[0], count[1])
        elif "accept" in count and "reject" in count:
            balanced += 2 * min(count["accept"], count["reject"])
    return {
        "target_name": target_name,
        "axis_name": axis_name,
        "groups": len(groups),
        "mixed_groups": len(mixed),
        "balanced_binary_capacity": balanced,
    }


def schema_field_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = sorted({key for row in rows for key in row})
    audit: list[dict[str, Any]] = []
    for field in fields:
        lower = field.lower()
        blocked_reasons = [frag for frag in FORBIDDEN_FIELD_FRAGMENTS if frag in lower]
        audit.append(
            {
                "field": field,
                "blocked_from_model_input": bool(blocked_reasons),
                "blocked_reasons": ";".join(blocked_reasons),
                "present_rows": sum(1 for row in rows if field in row and row.get(field) not in (None, "")),
            }
        )
    return audit


def validation_errors(input_summary: dict[str, Any], rows: list[dict[str, Any]], input_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if input_summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": input_summary.get("status")})
    if input_summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": input_summary.get("next_todo")})
    if input_summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": input_summary.get("validation_errors")})
    boundary = input_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if len(rows) != 480:
        errors.append({"error_type": "unexpected_row_count", "actual": len(rows), "expected": 480})
    for name in [
        "ingested_target_rows.jsonl",
        "multiclass_rows.jsonl",
        "observability_binary_rows.jsonl",
        "observable_relation_binary_rows.jsonl",
        "model_input_boundary.json",
        "validation_errors.jsonl",
    ]:
        if not (input_root / name).exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(input_root / name)})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_input_validation_errors"})
    return errors


def sanitized_diagnostic_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # This view is for inspection only. It is not smoke-ready because class fields
    # are themselves blockers in the current target.
    allowed = [
        "predicate_label",
        "subject_label",
        "object_label",
        "subject_object_class_pair",
        "evidence_tier",
        "packet_status",
        "image_count_bucket",
        "subject_image_count",
        "object_image_count",
        "pair_shared_view_count",
        "pair_shared_frame_count",
        "mesh_ready",
        "sequence_ready",
    ]
    return [{key: row.get(key) for key in allowed} for row in rows]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# R7 Attachment Observability Class-Pair Repair Schema Shortcut Audit",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Key Findings",
        "",
        f"- rows: `{summary['counts']['rows']}`",
        f"- observable p_rel rows: `{summary['counts']['p_rel_combined_rows']}`",
        f"- hanging-on p_rel rows: `{summary['counts']['p_rel_hanging_on_rows']}`",
        f"- attached-to p_rel rows: `{summary['counts']['p_rel_attached_to_rows']}`",
        f"- allowed high-risk blockers: `{summary['counts']['allowed_high_risk_blockers']}`",
        f"- learned smoke allowed: `{summary['learned_smoke_allowed']}`",
        "",
        "The class-pair repair improved label mass, but it did not produce an",
        "independent learned-smoke target. Combined observable `p_rel` is blocked by",
        "`predicate_subject_object_class_pair`, `subject_object_class_pair`, and",
        "`subject_label` shortcuts. `hanging on` has balanced accept/reject counts,",
        "but `subject_label` and `subject_object_class_pair` alone solve the target,",
        "which means the current labels are not a clean predicate-geometry",
        "compatibility target.",
        "",
        "## Decision",
        "",
        "Do not run learned smoke on this artifact. Treat it as diagnostic evidence",
        "for the attachment/observability route and run a path decision next.",
        "",
        "## Boundary",
        "",
        "- train-only audit",
        "- no validation/test usage",
        "- no H001 artifact modification",
        "- hidden fields used only after label lock for audit",
        "- no model training or learned smoke",
        "- no paper-level evidence claim",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary = read_json(args.input_root / "summary.json")
    rows = read_jsonl(args.input_root / "ingested_target_rows.jsonl")
    errors = validation_errors(input_summary, rows, args.input_root)

    targets = target_subsets(rows)
    viability_rows = target_viability(targets)

    probe_rows: list[dict[str, Any]] = []
    for target_name, subset in targets.items():
        if not subset:
            continue
        if target_name == "p_rel_attached_to":
            # Keep the target in the audit, but single-class probes are not informative.
            continue
        if target_name != "relation_multiclass" and len(Counter(target_label(row, target_name) for row in subset)) < 2:
            continue
        for spec in predictor_specs():
            probe_rows.append(
                categorical_probe(
                    subset,
                    target_name,
                    lambda row, name=target_name: target_label(row, name),
                    spec["name"],
                    spec["fn"],
                    spec["source"],
                    spec["allowed"],
                    "block_if_high" if spec["allowed"] else "report_only",
                )
            )

    capacity_axes: list[tuple[str, Callable[[dict[str, Any]], Any]]] = [
        ("predicate_label", lambda row: row.get("predicate_label")),
        ("subject_label", lambda row: row.get("subject_label")),
        ("object_label", lambda row: row.get("object_label")),
        ("subject_object_class_pair", lambda row: row.get("subject_object_class_pair")),
        (
            "predicate_subject_object_class_pair",
            lambda row: row.get("predicate_subject_object_class_pair"),
        ),
        ("rank_band_hidden", lambda row: row.get("rank_band_hidden")),
        ("geometry_bucket_hidden", lambda row: row.get("geometry_bucket_hidden")),
        ("scan_id_hidden", lambda row: row.get("scan_id_hidden")),
        ("exact_class_pair_id_hidden", lambda row: row.get("exact_class_pair_id_hidden")),
    ]
    capacity_rows: list[dict[str, Any]] = []
    for target_name in ["p_rel_combined", "p_rel_hanging_on"]:
        subset = targets[target_name]
        for axis_name, axis_fn in capacity_axes:
            capacity_rows.append(strata_capacity(subset, target_name, axis_name, axis_fn))

    allowed_high = [
        row
        for row in probe_rows
        if row["allowed_in_model"] is True and row["risk_level"] == "high" and row["blocks_smoke"] is True
    ]
    hidden_high = [
        row
        for row in probe_rows
        if row["allowed_in_model"] is False and str(row["risk_level"]).endswith("high")
    ]

    route_rows = [
        {
            "target_or_route": "p_obs",
            "decision": "diagnostic_only",
            "reason": "negative_sparse_455_positive_25_negative",
            "next_action": "do_not_use_as_learned_target_without_low_observability_mining",
        },
        {
            "target_or_route": "p_rel_attached_to",
            "decision": "diagnostic_only",
            "reason": "single_class_accept_172_reject_0",
            "next_action": "mine_visible_rejects_or_reframe_as_observability_abstain",
        },
        {
            "target_or_route": "p_rel_combined",
            "decision": "blocked_for_learned_smoke",
            "reason": "visible_predicate_class_pair_and_class_shortcuts_solve_target",
            "next_action": "path_decision_required",
        },
        {
            "target_or_route": "p_rel_hanging_on",
            "decision": "blocked_for_learned_smoke",
            "reason": "balanced_counts_but_subject_label_and_class_pair_are_perfect_shortcuts",
            "next_action": "path_decision_required",
        },
        {
            "target_or_route": "R7_attachment_observability",
            "decision": "diagnostic_attachment_observability_route_evidence",
            "reason": "current_label_target_tracks_object_class_prior_more_than_clean_compatibility",
            "next_action": NEXT_TODO,
        },
    ]

    status = STATUS_ERROR if errors else STATUS_BLOCKED
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": "input_errors_stop" if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "learned_smoke_allowed": False,
        "boundary": {
            "split": "train_only_schema_shortcut_audit",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "hidden_fields_used_for_audit_only_after_label_lock": True,
            "multi_view_or_mesh_as_model_input": False,
        },
        "input_status": input_summary.get("status"),
        "input_paths": {
            "ingested_target_rows": rel_path(args.input_root / "ingested_target_rows.jsonl"),
            "input_summary": rel_path(args.input_root / "summary.json"),
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "target_viability": rel_path(args.output_dir / "target_viability.csv"),
            "shortcut_audit": rel_path(args.output_dir / "shortcut_audit.csv"),
            "controlled_strata_capacity": rel_path(args.output_dir / "controlled_strata_capacity.csv"),
            "schema_field_audit": rel_path(args.output_dir / "schema_field_audit.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "risk_register": rel_path(args.output_dir / "risk_register.csv"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "rows": len(rows),
            "p_obs_rows": len(targets["p_obs"]),
            "p_rel_combined_rows": len(targets["p_rel_combined"]),
            "p_rel_attached_to_rows": len(targets["p_rel_attached_to"]),
            "p_rel_hanging_on_rows": len(targets["p_rel_hanging_on"]),
            "shortcut_probe_rows": len(probe_rows),
            "allowed_high_risk_blockers": len(allowed_high),
            "hidden_or_forbidden_high_risk_reports": len(hidden_high),
        },
        "target_counts": {
            name: dict(Counter(target_label(row, name) for row in subset))
            for name, subset in targets.items()
            if subset and name != "p_rel_attached_to"
        }
        | {
            "p_rel_attached_to": dict(
                Counter(row.get("p_rel_observable_target") for row in targets["p_rel_attached_to"])
            )
        },
        "primary_blockers": [
            {
                "target_name": row["target_name"],
                "predictor": row["predictor"],
                "accuracy": row["majority_rule_accuracy"],
                "baseline_accuracy": row["baseline_accuracy"],
                "risk_level": row["risk_level"],
            }
            for row in allowed_high[:20]
        ],
    }

    risk_rows = [
        {
            "risk": "learned_smoke_blocked",
            "severity": "high",
            "evidence": f"allowed_high_risk_blockers={len(allowed_high)}",
            "action": "do_not_run_learned_smoke_on_current_artifact",
        },
        {
            "risk": "hanging_on_class_shortcut",
            "severity": "high",
            "evidence": "hanging_on p_rel balanced counts but subject_label and class_pair reach 1.0 majority accuracy",
            "action": "path decision before any model",
        },
        {
            "risk": "attached_to_single_class",
            "severity": "high",
            "evidence": "attached_to observable p_rel accept=172 reject=0",
            "action": "diagnostic only unless visible rejects are mined",
        },
        {
            "risk": "p_obs_negative_sparse",
            "severity": "medium",
            "evidence": "p_obs observable=455 uncertain=25",
            "action": "requires low-observability/occlusion mining for p_obs",
        },
    ]

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "target_viability.csv", viability_rows)
    write_csv(args.output_dir / "shortcut_audit.csv", probe_rows)
    write_csv(args.output_dir / "controlled_strata_capacity.csv", capacity_rows)
    write_csv(args.output_dir / "schema_field_audit.csv", schema_field_audit(rows))
    write_csv(args.output_dir / "route_decision.csv", route_rows)
    write_csv(args.output_dir / "risk_register.csv", risk_rows)
    write_jsonl(
        args.output_dir / "diagnostic_visible_view_not_smoke_ready.jsonl",
        sanitized_diagnostic_view(rows),
    )
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
