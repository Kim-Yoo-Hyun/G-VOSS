#!/usr/bin/env python3
"""Analyze failure modes of support/contact individual-predicate smoke."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner"
)
DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis"
)

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner_diagnostic_only_failed_controls"
)
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_ready_select_point_multiview_evidence_plan"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_input_errors"
SELECTED_PATH = "freeze_obb_only_diagnostic_select_point_multiview_evidence_plan"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan"

PRIMARY_MODEL = "M4_TG_predicate_geometry_interaction"
FULL_MODEL = "M5_TGQ_factorized_observability"

GEOMETRY_FIELDS = [
    "abs_surface_gap_subject_bottom_to_object_top",
    "center_delta_z",
    "center_distance_xy",
    "normal_alignment",
    "normalized_center_distance_xy",
    "obb_contact_likelihood_proxy",
    "object_flatness_ratio",
    "object_major_axis_upness",
    "object_minor_axis_upness",
    "object_normal_upness",
    "object_vertical_extent_ratio",
    "subject_flatness_ratio",
    "subject_major_axis_upness",
    "subject_minor_axis_upness",
    "subject_normal_upness",
    "subject_vertical_extent_ratio",
    "support_area_proxy",
    "support_normal_verticality",
    "surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "xy_overlap_object_ratio",
    "xy_overlap_subject_ratio",
]

BIN_FIELDS = [
    "subject_flatness_ratio",
    "subject_major_axis_upness",
    "subject_vertical_extent_ratio",
    "xy_overlap_min_ratio",
    "obb_contact_likelihood_proxy",
    "abs_surface_gap_subject_bottom_to_object_top",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_hash(value: str, prefix: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def resolve_repo_path(text: str) -> Path:
    path = Path(text)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def auc_pairwise(scores: list[float], labels: list[int]) -> float | None:
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / total


def oriented_auc(scores: list[float], labels: list[int]) -> float | None:
    auc = auc_pairwise(scores, labels)
    if auc is None:
        return None
    return max(auc, 1.0 - auc)


def mean_or_none(values: Iterable[float]) -> float | None:
    vals = list(values)
    return mean(vals) if vals else None


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def load_joined_rows(plan_dir: Path, runner_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    plan_summary = read_json(plan_dir / "summary.json")
    smoke_path = resolve_repo_path(plan_summary["output_paths"]["smoke_ready_view"])
    hidden_path = resolve_repo_path(plan_summary["input_paths"]["hidden_manifest_for_group_metadata"])
    prediction_path = runner_dir / "predictions.jsonl"

    smoke_rows = read_jsonl(smoke_path)
    hidden_rows = read_jsonl(hidden_path)
    pred_rows = read_jsonl(prediction_path)

    smoke_by_example = {row.get("example_id"): row for row in smoke_rows}
    hidden_by_example = {stable_hash(str(row.get("row_id")), "ex"): row for row in hidden_rows}

    joined: list[dict[str, Any]] = []
    for pred in pred_rows:
        example_id = pred.get("row_id")
        smoke = smoke_by_example.get(example_id)
        hidden = hidden_by_example.get(example_id)
        if smoke is None:
            errors.append({"error_type": "missing_smoke_row", "example_id": example_id})
            continue
        if hidden is None:
            errors.append({"error_type": "missing_hidden_row", "example_id": example_id})
            hidden = {}
        feature_blocks = smoke.get("feature_blocks", {})
        t = feature_blocks.get("T_e", {})
        g = feature_blocks.get("G_e_mesh_pose_contact", {})
        q = feature_blocks.get("Q_e", {})
        label = int(pred.get("label"))
        score = safe_float(pred.get(PRIMARY_MODEL), 0.5)
        pred_label = 1 if score >= 0.5 else 0
        joined.append(
            {
                "candidate_role": hidden.get("candidate_role", "missing"),
                "class_pair": f"{t.get('subject_class_text')}->{t.get('object_class_text')}",
                "example_id": example_id,
                "geometry": g,
                "group_id": pred.get("group_id"),
                "hidden_class_pair": hidden.get("class_pair"),
                "label": label,
                "label_match_status": hidden.get("label_match_status", "missing"),
                "matched_predicates": "|".join(str(item) for item in hidden.get("matched_predicates", [])),
                "object": t.get("object_class_text"),
                "p_geom_valid": safe_float(hidden.get("p_geom_valid"), 0.0),
                "pred": pred_label,
                "predicate": t.get("predicate_label"),
                "rank_band": hidden.get("rank_band", "missing"),
                "reason_codes": list(hidden.get("reason_codes", [])),
                "route_name": hidden.get("route_name", "missing"),
                "scan_hash": pred.get("group_id"),
                "score": score,
                "subject": t.get("subject_class_text"),
                "q_profile": f"mesh={bool(q.get('mesh_semseg_obb_available'))}|point={bool(q.get('point_feature_available'))}|view={bool(q.get('multi_view_feature_available'))}",
            }
        )
    return joined, errors


def validate_inputs(runner_summary: dict[str, Any], runner_validation_rows: list[dict[str, Any]], joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if int(runner_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if runner_validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(runner_validation_rows)})
    counts = runner_summary.get("counts", {})
    if counts.get("rows") != 640 or counts.get("positive") != 320 or counts.get("negative") != 320:
        errors.append({"error_type": "unexpected_runner_counts", "counts": counts})
    if len(joined) != 640:
        errors.append({"error_type": "unexpected_joined_rows", "rows": len(joined)})
    return errors


def is_error(row: dict[str, Any]) -> bool:
    return int(row["pred"]) != int(row["label"])


def error_type(row: dict[str, Any]) -> str:
    if not is_error(row):
        return "correct"
    return "false_positive" if int(row["pred"]) == 1 else "false_negative"


def profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(int(row["label"]) for row in rows)
    errors = [row for row in rows if is_error(row)]
    fps = [row for row in errors if error_type(row) == "false_positive"]
    fns = [row for row in errors if error_type(row) == "false_negative"]
    high_conf = [
        row
        for row in errors
        if (int(row["label"]) == 0 and float(row["score"]) >= 0.75)
        or (int(row["label"]) == 1 and float(row["score"]) <= 0.25)
    ]
    return {
        "accuracy": round(1.0 - len(errors) / max(len(rows), 1), 6),
        "error_rate": round(len(errors) / max(len(rows), 1), 6),
        "errors": len(errors),
        "false_negative": len(fns),
        "false_positive": len(fps),
        "high_confidence_errors": len(high_conf),
        "negative": labels[0],
        "positive": labels[1],
        "rows": len(rows),
    }


def axis_profile(rows: list[dict[str, Any]], axis: str, min_rows: int = 4) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if axis == "reason_code":
        for row in rows:
            codes = row.get("reason_codes") or ["none"]
            for code in codes:
                groups[str(code)].append(row)
    else:
        for row in rows:
            groups[str(row.get(axis, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for value, group_rows in groups.items():
        if len(group_rows) < min_rows:
            continue
        prof = profile(group_rows)
        labels = [int(row["label"]) for row in group_rows]
        scores = [float(row["score"]) for row in group_rows]
        out.append(
            {
                "axis": axis,
                "value": value,
                "auroc": round_or_none(auc_pairwise(scores, labels)),
                "mean_negative_score": round_or_none(mean_or_none(row["score"] for row in group_rows if int(row["label"]) == 0)),
                "mean_positive_score": round_or_none(mean_or_none(row["score"] for row in group_rows if int(row["label"]) == 1)),
                **prof,
            }
        )
    return sorted(out, key=lambda row: (-float(row["error_rate"]), -int(row["rows"]), str(row["value"])))


def geometry_profile(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    labels = [int(row["label"]) for row in rows]
    error_labels = [1 if is_error(row) else 0 for row in rows]
    for field in GEOMETRY_FIELDS:
        values = [safe_float(row["geometry"].get(field), 0.0) for row in rows]
        correct_values = [value for value, row in zip(values, rows) if not is_error(row)]
        error_values = [value for value, row in zip(values, rows) if is_error(row)]
        pos_values = [value for value, label in zip(values, labels) if label == 1]
        neg_values = [value for value, label in zip(values, labels) if label == 0]
        out.append(
            {
                "feature": field,
                "error_auc_oriented": round_or_none(oriented_auc(values, error_labels)),
                "label_auc_oriented": round_or_none(oriented_auc(values, labels)),
                "mean_correct": round_or_none(mean_or_none(correct_values)),
                "mean_error": round_or_none(mean_or_none(error_values)),
                "mean_negative": round_or_none(mean_or_none(neg_values)),
                "mean_positive": round_or_none(mean_or_none(pos_values)),
                "rows": len(rows),
            }
        )
    return sorted(out, key=lambda row: (-(row["error_auc_oriented"] or 0.0), -(row["label_auc_oriented"] or 0.0)))


def quantile_bins(values: list[float], bins: int = 4) -> list[float]:
    if not values:
        return []
    ordered = sorted(values)
    cuts: list[float] = []
    for idx in range(1, bins):
        pos = int(round(idx * (len(ordered) - 1) / bins))
        cuts.append(ordered[pos])
    return cuts


def bin_name(value: float, cuts: list[float]) -> str:
    prev = "-inf"
    for idx, cut in enumerate(cuts):
        if value <= cut:
            return f"bin{idx + 1}:{prev}..{cut:.6g}"
        prev = f"{cut:.6g}"
    return f"bin{len(cuts) + 1}:{prev}..inf"


def geometry_bin_profile(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for field in BIN_FIELDS:
        values = [safe_float(row["geometry"].get(field), 0.0) for row in rows]
        cuts = quantile_bins(values, 4)
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for value, row in zip(values, rows):
            groups[bin_name(value, cuts)].append(row)
        for name, group_rows in sorted(groups.items()):
            prof = profile(group_rows)
            out.append(
                {
                    "bin": name,
                    "feature": field,
                    "mean_score": round_or_none(mean_or_none(row["score"] for row in group_rows)),
                    **prof,
                }
            )
    return out


def high_confidence_error_cases(rows: list[dict[str, Any]], max_cases: int = 80) -> list[dict[str, Any]]:
    errors = [row for row in rows if is_error(row)]
    def severity(row: dict[str, Any]) -> float:
        return abs(float(row["score"]) - 0.5)
    selected = sorted(errors, key=severity, reverse=True)[:max_cases]
    out: list[dict[str, Any]] = []
    for row in selected:
        g = row["geometry"]
        out.append(
            {
                "candidate_role": row.get("candidate_role"),
                "class_pair": row.get("class_pair"),
                "error_type": error_type(row),
                "label": row.get("label"),
                "label_match_status": row.get("label_match_status"),
                "matched_predicates": row.get("matched_predicates"),
                "p_geom_valid_hidden": row.get("p_geom_valid"),
                "pred": row.get("pred"),
                "predicate": row.get("predicate"),
                "rank_band": row.get("rank_band"),
                "reason_codes": row.get("reason_codes"),
                "row_id": row.get("example_id"),
                "score": round(float(row.get("score")), 6),
                "subject_major_axis_upness": g.get("subject_major_axis_upness"),
                "subject_flatness_ratio": g.get("subject_flatness_ratio"),
                "subject_vertical_extent_ratio": g.get("subject_vertical_extent_ratio"),
                "xy_overlap_min_ratio": g.get("xy_overlap_min_ratio"),
                "obb_contact_likelihood_proxy": g.get("obb_contact_likelihood_proxy"),
            }
        )
    return out


def route_decision_rows(summary: dict[str, Any], axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fp = summary["failure_profile"]["false_positive"]
    fn = summary["failure_profile"]["false_negative"]
    primary = summary["runner_snapshot"]["primary_auroc"]
    geometry = summary["runner_snapshot"]["geometry_only_auroc"]
    q_profile = summary["q_profile"]
    family_match_rows = [
        row
        for row in axis_rows
        if row.get("axis") == "label_match_status" and row.get("value") == "family_match"
    ]
    family_match_error_rate = family_match_rows[0]["error_rate"] if family_match_rows else None
    return [
        {
            "route": "freeze_current_semseg_obb_only_support_contact_as_diagnostic",
            "verdict": "selected_now",
            "evidence": f"Primary AUROC {primary:.4f}; geometry-only {geometry:.4f}; FP/FN={fp}/{fn}; Q profile {q_profile}.",
            "reason": "Current OBB pose/contact evidence has real interaction signal but not enough separability for main evidence.",
            "next_action": "do_not_promote_to_main_claim",
        },
        {
            "route": "add_point_or_multiview_evidence_for_support_contact",
            "verdict": "selected_next",
            "evidence": "All rows have mesh=True, point=False, view=False, so Q_e cannot express observability and contact/pose is OBB-only.",
            "reason": "standing/lying distinction often depends on object pose, contact surface, and visual orientation that OBB features only approximate.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "repair_or_tighten_family_match_labels",
            "verdict": "defer_but_needed",
            "evidence": f"family_match error_rate={family_match_error_rate}",
            "reason": "Many negatives are subtype/family mismatch rows rather than visually impossible relations; stricter label policy may be required.",
            "next_action": "combine_with_point_multiview_packet_review",
        },
        {
            "route": "lower_primary_gate_and_accept_current_result",
            "verdict": "reject",
            "evidence": f"Primary AUROC {primary:.4f} is below the predeclared 0.70 gate.",
            "reason": "Lowering the gate after observing the result would overstate the evidence.",
            "next_action": "keep_diagnostic",
        },
        {
            "route": "swap_to_stronger_combiner_immediately",
            "verdict": "reject",
            "evidence": "Plain concat fails, interaction helps, but Q_e is constant and G_e is OBB-only.",
            "reason": "The bottleneck is evidence/label quality, not only classifier capacity.",
            "next_action": "do_not_add_SOTA_combiner_before_evidence_repair",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], axis_rows: list[dict[str, Any]], geom_rows: list[dict[str, Any]]) -> None:
    top_class_pairs = [row for row in axis_rows if row.get("axis") == "class_pair"][:8]
    top_label_status = [row for row in axis_rows if row.get("axis") == "label_match_status"]
    top_geom = geom_rows[:8]
    lines = [
        "# H002 Support/Contact Individual Predicate Failure Analysis",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"rows = {summary['failure_profile']['rows']}",
        f"errors = {summary['failure_profile']['errors']}",
        f"false_positive / false_negative = {summary['failure_profile']['false_positive']} / {summary['failure_profile']['false_negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Finding",
        "",
        "The support/contact individual-predicate branch is not failing because of semantic/class shortcut",
        "or geometry-only dominance. It has a real predicate-geometry interaction signal, but the current",
        "semseg OBB-only evidence is too weak to separate `standing on` from `lying on` reliably enough.",
        "",
        "```text",
        f"primary AUROC = {summary['runner_snapshot']['primary_auroc']}",
        f"geometry-only AUROC = {summary['runner_snapshot']['geometry_only_auroc']}",
        f"semantic-only AUROC = {summary['runner_snapshot']['semantic_only_auroc']}",
        f"plain concat AUROC = {summary['runner_snapshot']['plain_concat_auroc']}",
        "```",
        "",
        "## Label/Construction Axes",
        "",
        "| Axis | Value | Rows | Error Rate | FP | FN | AUROC |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in top_label_status:
        lines.append(
            f"| `{row['axis']}` | `{row['value']}` | {row['rows']} | {row['error_rate']} | "
            f"{row['false_positive']} | {row['false_negative']} | {row['auroc']} |"
        )
    lines.extend(
        [
            "",
            "## Class-Pair Failure Concentration",
            "",
            "| Class Pair | Rows | Error Rate | FP | FN | Mean Pos Score | Mean Neg Score |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in top_class_pairs:
        lines.append(
            f"| `{row['value']}` | {row['rows']} | {row['error_rate']} | {row['false_positive']} | "
            f"{row['false_negative']} | {row['mean_positive_score']} | {row['mean_negative_score']} |"
        )
    lines.extend(
        [
            "",
            "## Geometry Feature Diagnosis",
            "",
            "| Feature | Error AUC | Label AUC | Mean Error | Mean Correct |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in top_geom:
        lines.append(
            f"| `{row['feature']}` | {row['error_auc_oriented']} | {row['label_auc_oriented']} | "
            f"{row['mean_error']} | {row['mean_correct']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Freeze current semseg OBB-only support/contact individual predicate result as diagnostic.",
            "- Do not lower the planned gate after seeing AUROC `0.6316`.",
            "- Do not add a stronger combiner before evidence repair.",
            "- Next, plan point/multiview evidence for this family because current `Q_e` is constant:",
            "",
            "```text",
            str(summary["q_profile"]),
            "```",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runner_summary = read_json(args.runner_dir / "summary.json")
    runner_validation_rows = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    joined, join_errors = load_joined_rows(args.plan_dir, args.runner_dir)
    errors = validate_inputs(runner_summary, runner_validation_rows, joined)
    errors.extend(join_errors)

    failure_prof = profile(joined)
    axis_rows: list[dict[str, Any]] = []
    for axis in [
        "predicate",
        "class_pair",
        "subject",
        "object",
        "candidate_role",
        "label_match_status",
        "matched_predicates",
        "rank_band",
        "route_name",
        "q_profile",
        "reason_code",
    ]:
        axis_rows.extend(axis_profile(joined, axis))
    geom_rows = geometry_profile(joined)
    bin_rows = geometry_bin_profile(joined)
    error_cases = high_confidence_error_cases(joined)
    q_profile = dict(Counter(row["q_profile"] for row in joined))

    runner_metrics = runner_summary.get("key_metrics", {})
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "failure_profile": failure_prof,
        "input_paths": {
            "plan_root": rel_path(args.plan_dir),
            "runner_root": rel_path(args.runner_dir),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {
            "axis_failure_profile": rel_path(args.output_dir / "axis_failure_profile.csv"),
            "geometry_bin_profile": rel_path(args.output_dir / "geometry_bin_profile.csv"),
            "geometry_feature_profile": rel_path(args.output_dir / "geometry_feature_profile.csv"),
            "hard_error_cases": rel_path(args.output_dir / "hard_error_cases.jsonl"),
            "report": rel_path(args.output_dir / "report.md"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "q_profile": q_profile,
        "runner_snapshot": {
            "geometry_only_auroc": runner_metrics.get("M2_geometry_only_G", {}).get("auroc"),
            "plain_concat_auroc": runner_metrics.get("M3_TG_concat", {}).get("auroc"),
            "primary_auroc": runner_metrics.get(PRIMARY_MODEL, {}).get("auroc"),
            "semantic_only_auroc": runner_metrics.get("M1_semantic_only_T", {}).get("auroc"),
            "shuffled_g_global_auroc": runner_metrics.get("C2_shuffled_G_global", {}).get("auroc"),
            "shuffled_g_within_predicate_auroc": runner_metrics.get("C3_shuffled_G_within_predicate", {}).get("auroc"),
            "wrong_t_auroc": runner_metrics.get("C1_wrong_T_same_G", {}).get("auroc"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": STATUS_READY if not errors else STATUS_ERROR,
        "validation_errors": len(errors),
    }
    route_rows = route_decision_rows(summary, axis_rows)

    write_csv(args.output_dir / "axis_failure_profile.csv", axis_rows)
    write_csv(args.output_dir / "geometry_feature_profile.csv", geom_rows)
    write_csv(args.output_dir / "geometry_bin_profile.csv", bin_rows)
    write_csv(args.output_dir / "route_decision.csv", route_rows)
    write_jsonl(args.output_dir / "hard_error_cases.jsonl", error_cases)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, axis_rows, geom_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
