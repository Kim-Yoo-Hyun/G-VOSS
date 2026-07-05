#!/usr/bin/env python3
"""Materialize frozen H002 support/contact pose-conditioned candidate rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan"
)
DEFAULT_ANCHOR_PREVIEW = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"
    / "anchor_candidate_preview.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization"
EXPECTED_CAPACITY_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_ready_for_candidate_materialization_plan"
)
EXPECTED_TARGET_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_v1"
ROW_SCHEMA_NAME = "h002_support_contact_pose_conditioned_candidate_row_v1"
SMOKE_VIEW_SCHEMA = "h002_support_contact_pose_conditioned_smoke_ready_candidate_view_v1"
DATASET_NAME = "h002_support_contact_pose_conditioned_candidates_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_ready_for_schema_shortcut_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit"

PRIMARY_PREDICATES = ["lying on", "standing on"]
POSE_STATES = ["lying_like_support_contact", "upright_support_contact"]
EXPECTED_LABEL_RULE = {
    "lying_like_support_contact": {"lying on": 1, "standing on": 0},
    "upright_support_contact": {"lying on": 0, "standing on": 1},
}
EXPECTED_ANCHORS = 200
EXPECTED_ROWS = 400

SEMSEG_FIELDS = [
    "abs_surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "subject_vertical_extent_ratio",
    "subject_flatness_ratio",
    "subject_major_axis_upness",
    "obb_contact_likelihood_proxy",
]
POINT_FIELD_MAP = {
    "point_abs_surface_gap_optional": "point_abs_surface_gap",
    "point_contact_candidate_ratio_optional": "point_contact_candidate_ratio",
    "point_subject_bottom_band_density_optional": "point_subject_bottom_band_density",
    "point_object_top_band_density_optional": "point_object_top_band_density",
}
HIDDEN_SMOKE_KEYS = {
    "anchor_pose_state",
    "scan_id",
    "subject_id",
    "object_id",
    "visible_pair",
    "hard_surface_pair",
    "source_predicates",
    "queue_kinds",
    "G_e_hash",
    "controls_hidden",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--anchor-preview", type=Path, default=DEFAULT_ANCHOR_PREVIEW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"check": "empty", "status": "pass"}]
        fields = ["check", "status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(payload: Any, length: int = 20) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def bool_value(value: Any) -> bool:
    return bool(value)


def split_visible_pair(value: Any) -> tuple[str, str]:
    text = str(value or "")
    marker = " [REL] "
    if marker not in text:
        return "", ""
    subject, obj = text.split(marker, 1)
    return subject.strip(), obj.strip()


def compact_predicate(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def make_g_e(anchor: dict[str, Any]) -> dict[str, float | None]:
    semseg = anchor.get("G_e_semseg_subset") or {}
    point = anchor.get("G_e_point_optional_subset") or {}
    g_e: dict[str, float | None] = {}
    for field in SEMSEG_FIELDS:
        g_e[field] = safe_float(semseg.get(field))
    for output_field, input_field in POINT_FIELD_MAP.items():
        g_e[output_field] = safe_float(point.get(input_field))
    return g_e


def make_q_e(anchor: dict[str, Any], g_e: dict[str, float | None]) -> dict[str, bool]:
    semseg_complete = all(g_e.get(field) is not None for field in SEMSEG_FIELDS)
    point_complete = all(g_e.get(field) is not None for field in POINT_FIELD_MAP)
    return {
        "aligned_ply_point_features_available": bool(anchor.get("G_e_point_optional_subset")),
        "hard_surface_pair_allowed": not bool_value(anchor.get("hard_surface_pair")),
        "point_feature_complete": point_complete,
        "semseg_obb_available": semseg_complete,
    }


def nested_key_hits(payload: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(nested_key_hits(value, forbidden))
    elif isinstance(payload, list):
        for value in payload:
            hits.extend(nested_key_hits(value, forbidden))
    return hits


def load_plan(plan_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        read_json(plan_dir / "summary.json"),
        read_json(plan_dir / "materialization_contract.json"),
        read_json(plan_dir / "path_decision.json"),
        read_json(plan_dir / "output_manifest_contract.json"),
    )


def validate_plan(
    plan_summary: dict[str, Any],
    contract: dict[str, Any],
    path_decision: dict[str, Any],
    output_contract: dict[str, Any],
    plan_dir: Path,
    anchor_preview: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"scope": "plan_summary", "field": "status", "observed": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"scope": "plan_summary", "field": "next_todo", "observed": plan_summary.get("next_todo")})
    if plan_summary.get("capacity_status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"scope": "plan_summary", "field": "capacity_status", "observed": plan_summary.get("capacity_status")})
    if plan_summary.get("target_plan_status") != EXPECTED_TARGET_PLAN_STATUS:
        errors.append({"scope": "plan_summary", "field": "target_plan_status", "observed": plan_summary.get("target_plan_status")})
    if int(plan_summary.get("validation_errors", -1)) != 0:
        errors.append({"scope": "plan_summary", "field": "validation_errors", "observed": plan_summary.get("validation_errors")})
    validation_path = plan_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"scope": "plan_validation_errors", "field": "validation_errors.jsonl", "observed": "non_empty"})

    if contract.get("dataset_name") != DATASET_NAME:
        errors.append({"scope": "materialization_contract", "field": "dataset_name", "observed": contract.get("dataset_name")})
    if contract.get("expected_rows") != EXPECTED_ROWS:
        errors.append({"scope": "materialization_contract", "field": "expected_rows", "observed": contract.get("expected_rows")})
    if contract.get("rows_per_anchor") != 2:
        errors.append({"scope": "materialization_contract", "field": "rows_per_anchor", "observed": contract.get("rows_per_anchor")})
    if contract.get("primary_predicates") != PRIMARY_PREDICATES:
        errors.append({"scope": "materialization_contract", "field": "primary_predicates", "observed": contract.get("primary_predicates")})
    if contract.get("label_rule") != EXPECTED_LABEL_RULE:
        errors.append({"scope": "materialization_contract", "field": "label_rule", "observed": contract.get("label_rule")})
    split_policy = contract.get("split_policy", {})
    if split_policy.get("split") != "train" or split_policy.get("validation_usage") or split_policy.get("test_usage"):
        errors.append({"scope": "materialization_contract", "field": "split_policy", "observed": split_policy})

    expected_anchor_rel = contract.get("frozen_anchor_source")
    if expected_anchor_rel and rel_path(anchor_preview) != expected_anchor_rel:
        errors.append(
            {
                "scope": "materialization_contract",
                "field": "frozen_anchor_source",
                "expected": expected_anchor_rel,
                "observed": rel_path(anchor_preview),
            }
        )

    if path_decision.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"scope": "path_decision", "field": "status", "observed": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"scope": "path_decision", "field": "next_todo", "observed": path_decision.get("next_todo")})
    if not path_decision.get("candidate_materialization_allowed"):
        errors.append({"scope": "path_decision", "field": "candidate_materialization_allowed", "observed": False})
    if path_decision.get("learned_smoke_allowed"):
        errors.append({"scope": "path_decision", "field": "learned_smoke_allowed", "observed": True})
    if path_decision.get("paper_evidence_allowed"):
        errors.append({"scope": "path_decision", "field": "paper_evidence_allowed", "observed": True})

    expected_counts = output_contract.get("expected_counts", {})
    if expected_counts.get("rows") != EXPECTED_ROWS or expected_counts.get("anchor_groups") != EXPECTED_ANCHORS:
        errors.append({"scope": "output_manifest_contract", "field": "expected_counts", "observed": expected_counts})
    if output_contract.get("post_materialization_required_next") != NEXT_TODO:
        errors.append(
            {
                "scope": "output_manifest_contract",
                "field": "post_materialization_required_next",
                "observed": output_contract.get("post_materialization_required_next"),
            }
        )
    return errors


def validate_anchor_preview(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    anchor_ids = [str(row.get("anchor_id", "")) for row in anchors]
    if len(anchors) != EXPECTED_ANCHORS:
        errors.append({"scope": "anchor_preview", "field": "row_count", "observed": len(anchors)})
    duplicates = [anchor_id for anchor_id, count in Counter(anchor_ids).items() if count > 1]
    if duplicates:
        errors.append({"scope": "anchor_preview", "field": "duplicate_anchor_id", "observed": duplicates[:10]})
    state_counts = Counter(str(row.get("anchor_pose_state")) for row in anchors)
    if state_counts != Counter({"lying_like_support_contact": 100, "upright_support_contact": 100}):
        errors.append({"scope": "anchor_preview", "field": "anchor_pose_state_counts", "observed": dict(state_counts)})

    for row in anchors:
        anchor_id = str(row.get("anchor_id", ""))
        state = str(row.get("anchor_pose_state", ""))
        if state not in EXPECTED_LABEL_RULE:
            errors.append({"scope": "anchor_preview", "anchor_id": anchor_id, "field": "anchor_pose_state", "observed": state})
            continue
        if bool_value(row.get("hard_surface_pair")):
            errors.append({"scope": "anchor_preview", "anchor_id": anchor_id, "field": "hard_surface_pair", "observed": True})
        subject_label, object_label = split_visible_pair(row.get("visible_pair"))
        if not subject_label or not object_label:
            errors.append({"scope": "anchor_preview", "anchor_id": anchor_id, "field": "visible_pair", "observed": row.get("visible_pair")})
        target_rows = row.get("target_rows_preview")
        if not isinstance(target_rows, list) or len(target_rows) != 2:
            errors.append({"scope": "anchor_preview", "anchor_id": anchor_id, "field": "target_rows_preview_len", "observed": target_rows})
            continue
        observed = {str(item.get("predicate_label")): int(item.get("compatibility_y", -1)) for item in target_rows}
        if observed != EXPECTED_LABEL_RULE[state]:
            errors.append({"scope": "anchor_preview", "anchor_id": anchor_id, "field": "target_rows_preview", "observed": observed})
        g_e = make_g_e(row)
        missing_semseg = [field for field in SEMSEG_FIELDS if g_e.get(field) is None]
        if missing_semseg:
            errors.append(
                {
                    "scope": "anchor_preview",
                    "anchor_id": anchor_id,
                    "field": "G_e_required_semseg_missing_or_nonfinite",
                    "observed": missing_semseg,
                }
            )
    return errors


def build_rows(anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_rows: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []

    for anchor in anchors:
        anchor_id = str(anchor["anchor_id"])
        state = str(anchor["anchor_pose_state"])
        subject_label, object_label = split_visible_pair(anchor.get("visible_pair"))
        g_e = make_g_e(anchor)
        q_e = make_q_e(anchor, g_e)
        g_hash = stable_hash(g_e)
        target_rows = sorted(anchor["target_rows_preview"], key=lambda item: PRIMARY_PREDICATES.index(item["predicate_label"]))

        for target in target_rows:
            predicate = str(target["predicate_label"])
            y = int(target["compatibility_y"])
            row_id = f"h002_sc_pose_{anchor_id}_{compact_predicate(predicate)}"
            t_e = {
                "object_class_label": object_label,
                "predicate_label": predicate,
                "predicate_text": predicate,
                "relation_family": "support_contact_pose_conditioned",
                "subject_class_label": subject_label,
            }
            z_e = {
                "source_rank_available": False,
                "source_score_available": False,
            }
            labels = {
                "compatibility_y": y,
                "label_source": "pose_conditioned_same_G_predicate_flip",
                "target_family": "support_contact_pose_conditioned",
            }
            hidden = {
                "G_e_hash": g_hash,
                "anchor_pose_state": state,
                "hard_surface_pair": bool_value(anchor.get("hard_surface_pair")),
                "object_id": anchor.get("object_id"),
                "queue_kinds": anchor.get("queue_kinds", []),
                "scan_id": anchor.get("scan_id"),
                "source_predicates": anchor.get("source_predicates", []),
                "subject_id": anchor.get("subject_id"),
                "visible_pair": anchor.get("visible_pair"),
            }
            candidate_rows.append(
                {
                    "G_e_mesh_pose_contact": g_e,
                    "Q_e_safe": q_e,
                    "T_e": t_e,
                    "Z_e_safe": z_e,
                    "anchor_id": anchor_id,
                    "controls_hidden": hidden,
                    "cv_group_id": anchor_id,
                    "dataset_name": DATASET_NAME,
                    "labels": labels,
                    "row_id": row_id,
                    "row_schema_name": ROW_SCHEMA_NAME,
                    "source_dataset": "open3dsg_train_full",
                    "split": "train",
                }
            )
            smoke_rows.append(
                {
                    "G_e_mesh_pose_contact": g_e,
                    "Q_e_safe": q_e,
                    "T_e": t_e,
                    "Z_e_safe": z_e,
                    "cv_group_id": anchor_id,
                    "row_id": row_id,
                    "schema_version": SMOKE_VIEW_SCHEMA,
                    "target_y": y,
                }
            )
            hidden_rows.append(
                {
                    "G_e_hash": g_hash,
                    "anchor_id": anchor_id,
                    "anchor_pose_state": state,
                    "compatibility_y": y,
                    "hard_surface_pair": bool_value(anchor.get("hard_surface_pair")),
                    "object_id": anchor.get("object_id"),
                    "predicate_label": predicate,
                    "queue_kinds": anchor.get("queue_kinds", []),
                    "row_id": row_id,
                    "scan_id": anchor.get("scan_id"),
                    "source_predicates": anchor.get("source_predicates", []),
                    "subject_id": anchor.get("subject_id"),
                    "visible_pair": anchor.get("visible_pair"),
                }
            )
    return candidate_rows, smoke_rows, hidden_rows


def validate_materialized(
    candidate_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    precheck: list[dict[str, Any]] = []
    row_count = len(candidate_rows)
    anchor_ids = [str(row["anchor_id"]) for row in candidate_rows]
    labels = Counter(int(row["labels"]["compatibility_y"]) for row in candidate_rows)
    predicates = Counter(str(row["T_e"]["predicate_label"]) for row in candidate_rows)
    states = Counter(str(row["anchor_pose_state"]) for row in hidden_rows if row["predicate_label"] == "lying on")
    hard_surface_rows = sum(1 for row in hidden_rows if row.get("hard_surface_pair"))
    point_complete_rows = sum(1 for row in candidate_rows if row["Q_e_safe"]["point_feature_complete"])
    semseg_complete_rows = sum(1 for row in candidate_rows if row["Q_e_safe"]["semseg_obb_available"])

    rows_by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    smoke_by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        rows_by_anchor[str(row["anchor_id"])].append(row)
    for row in smoke_rows:
        smoke_by_anchor[str(row["cv_group_id"])].append(row)

    same_g_pass = True
    paired_label_pass = True
    rows_per_anchor_pass = True
    for anchor_id, rows in rows_by_anchor.items():
        if len(rows) != 2:
            rows_per_anchor_pass = False
        g_hashes = {stable_hash(row["G_e_mesh_pose_contact"]) for row in rows}
        if len(g_hashes) != 1:
            same_g_pass = False
        if sum(int(row["labels"]["compatibility_y"]) for row in rows) != 1:
            paired_label_pass = False

    smoke_hidden_hits = Counter()
    for row in smoke_rows:
        smoke_hidden_hits.update(nested_key_hits(row, HIDDEN_SMOKE_KEYS))
    smoke_hidden_absent = not smoke_hidden_hits

    checks = [
        ("row_count", row_count == EXPECTED_ROWS, row_count),
        ("anchor_count", len(rows_by_anchor) == EXPECTED_ANCHORS, len(rows_by_anchor)),
        ("rows_per_anchor", rows_per_anchor_pass, dict(Counter(len(rows) for rows in rows_by_anchor.values()))),
        ("label_balance", labels == Counter({0: 200, 1: 200}), dict(labels)),
        ("predicate_counts", predicates == Counter({"lying on": 200, "standing on": 200}), dict(predicates)),
        ("anchor_state_counts", states == Counter({"lying_like_support_contact": 100, "upright_support_contact": 100}), dict(states)),
        ("same_G_e_pair_integrity", same_g_pass, "same hash per anchor"),
        ("paired_label_integrity", paired_label_pass, "one positive and one negative per anchor"),
        ("smoke_ready_row_count", len(smoke_rows) == EXPECTED_ROWS, len(smoke_rows)),
        ("hidden_manifest_row_count", len(hidden_rows) == EXPECTED_ROWS, len(hidden_rows)),
        ("semseg_complete_rows", semseg_complete_rows == EXPECTED_ROWS, semseg_complete_rows),
        ("point_complete_rows_optional", point_complete_rows <= EXPECTED_ROWS, point_complete_rows),
        ("smoke_ready_hidden_token_absent", smoke_hidden_absent, dict(smoke_hidden_hits)),
        ("grouped_cv_anchor_id_present", all(row.get("cv_group_id") for row in smoke_rows), "cv_group_id"),
        ("hard_surface_rows", hard_surface_rows == 0, hard_surface_rows),
        ("learned_smoke_blocked", True, "blocked_until_schema_shortcut_audit"),
    ]
    for check_name, passed, observed in checks:
        precheck.append({"check": check_name, "observed": json.dumps(observed, sort_keys=True), "status": "pass" if passed else "fail"})
        if not passed and check_name != "learned_smoke_allowed":
            errors.append({"scope": "materialized_rows", "field": check_name, "observed": observed})

    summary_counts = {
        "anchor_groups": len(rows_by_anchor),
        "hard_surface_rows": hard_surface_rows,
        "hidden_manifest_rows": len(hidden_rows),
        "label_counts": {str(k): labels[k] for k in sorted(labels)},
        "point_complete_rows": point_complete_rows,
        "predicate_counts": {k: predicates[k] for k in PRIMARY_PREDICATES},
        "row_count": row_count,
        "semseg_complete_rows": semseg_complete_rows,
        "smoke_ready_rows": len(smoke_rows),
        "state_counts": {state: states[state] for state in POSE_STATES},
    }
    return errors, precheck, summary_counts


def build_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    paths = summary["output_paths"]
    return "\n".join(
        [
            "# H002 Support/Contact Pose-Conditioned Candidate Materialization",
            "",
            "## Status",
            "",
            f"- status: `{summary['status']}`",
            f"- selected_path: `{summary['selected_path']}`",
            f"- validation_errors: `{summary['validation_errors']}`",
            f"- next_todo: `{summary['next_todo']}`",
            "",
            "## Materialized Dataset",
            "",
            f"- dataset_name: `{summary['dataset_name']}`",
            f"- anchors: `{counts['anchor_groups']}`",
            f"- rows: `{counts['row_count']}`",
            f"- labels: `{counts['label_counts']}`",
            f"- predicates: `{counts['predicate_counts']}`",
            f"- pose states: `{counts['state_counts']}`",
            f"- hard_surface_rows: `{counts['hard_surface_rows']}`",
            "",
            "## Boundary",
            "",
            "- Uses train-side frozen anchor preview only.",
            "- Expands each anchor into `lying on` and `standing on` rows with identical `G_e`.",
            "- Does not select additional anchors, change thresholds, run learned smoke, train a model, or use validation/test rows.",
            "- `scan_id`, endpoint ids, visible pair, queue kinds, source predicates, pose state, and `G_e_hash` are hidden/audit-only fields.",
            "- `smoke_ready_candidate_view.jsonl` is only a schema-audit input; learned smoke remains blocked until the next shortcut audit passes.",
            "",
            "## Outputs",
            "",
            f"- candidate rows: `{paths['candidate_rows']}`",
            f"- smoke-ready candidate view: `{paths['smoke_ready_candidate_view']}`",
            f"- hidden manifest: `{paths['hidden_manifest']}`",
            f"- schema shortcut precheck: `{paths['schema_shortcut_precheck']}`",
            f"- manifest: `{paths['manifest']}`",
            f"- validation errors: `{paths['validation_errors']}`",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    plan_summary, contract, path_decision, output_contract = load_plan(args.plan_dir)
    errors.extend(validate_plan(plan_summary, contract, path_decision, output_contract, args.plan_dir, args.anchor_preview))

    anchors: list[dict[str, Any]] = []
    if not args.anchor_preview.exists():
        errors.append({"scope": "input", "field": "anchor_preview", "observed": rel_path(args.anchor_preview), "error": "missing"})
    else:
        anchors = read_jsonl(args.anchor_preview)
        errors.extend(validate_anchor_preview(anchors))

    candidate_rows: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    precheck_rows: list[dict[str, Any]] = []
    counts: dict[str, Any] = {
        "anchor_groups": 0,
        "hard_surface_rows": 0,
        "hidden_manifest_rows": 0,
        "label_counts": {},
        "predicate_counts": {},
        "row_count": 0,
        "smoke_ready_rows": 0,
        "state_counts": {},
    }

    if not errors:
        candidate_rows, smoke_rows, hidden_rows = build_rows(anchors)
        materialized_errors, precheck_rows, counts = validate_materialized(candidate_rows, smoke_rows, hidden_rows)
        errors.extend(materialized_errors)

    output_paths = {
        "candidate_rows": args.output_dir / "candidate_rows.jsonl",
        "hidden_manifest": args.output_dir / "hidden_manifest.jsonl",
        "manifest": args.output_dir / "manifest.json",
        "report": args.output_dir / "report.md",
        "schema_shortcut_precheck": args.output_dir / "schema_shortcut_precheck.csv",
        "smoke_ready_candidate_view": args.output_dir / "smoke_ready_candidate_view.jsonl",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    write_jsonl(output_paths["candidate_rows"], candidate_rows)
    write_jsonl(output_paths["smoke_ready_candidate_view"], smoke_rows)
    write_jsonl(output_paths["hidden_manifest"], hidden_rows)
    write_csv(output_paths["schema_shortcut_precheck"], precheck_rows)
    write_jsonl(output_paths["validation_errors"], errors)

    status = STATUS_ERROR if errors else STATUS_READY
    manifest = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": True,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_candidate_materialization",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": DATASET_NAME,
        "input_paths": {
            "anchor_preview": rel_path(args.anchor_preview),
            "plan_dir": rel_path(args.plan_dir),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "plan_status": plan_summary.get("status"),
        "row_schema_name": ROW_SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "smoke_view_schema": SMOKE_VIEW_SCHEMA,
        "status": status,
    }
    write_json(output_paths["manifest"], manifest)

    summary = {
        "boundary": manifest["boundary"],
        "capacity_status": plan_summary.get("capacity_status"),
        "counts": counts,
        "created_at_utc": manifest["created_at_utc"],
        "dataset_name": DATASET_NAME,
        "input_paths": manifest["input_paths"],
        "manifest_path": rel_path(output_paths["manifest"]),
        "next_todo": NEXT_TODO,
        "output_paths": manifest["output_paths"],
        "path_decision": {
            "candidate_materialization_complete": not errors,
            "learned_smoke_allowed": False,
            "next_todo": NEXT_TODO,
            "paper_evidence_allowed": False,
            "rationale": "Candidate rows are materialized from the frozen anchor preview; learned smoke remains blocked until schema shortcut audit.",
            "schema_shortcut_audit_allowed": not errors,
            "selected_path": "run_schema_shortcut_audit_before_learned_smoke",
            "status": status,
            "validation_errors": len(errors),
        },
        "plan_status": plan_summary.get("status"),
        "row_schema_name": ROW_SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "selected_path": "materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview",
        "smoke_view_schema": SMOKE_VIEW_SCHEMA,
        "status": status,
        "target_plan_status": plan_summary.get("target_plan_status"),
        "validation_errors": len(errors),
    }
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
