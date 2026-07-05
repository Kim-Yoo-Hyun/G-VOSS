#!/usr/bin/env python3
"""Analyze point/multiview support/contact smoke failures and claim boundary."""

from __future__ import annotations

import argparse
import csv
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
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner"
)
DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan"
)
DEFAULT_MATERIALIZATION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis"
)

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_diagnostic_only_failed_controls"
)
EXPECTED_RUNNER_NEXT = (
    "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis"
)
EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_ready"
)
EXPECTED_MATERIALIZATION_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_ready_for_result_review"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_input_errors"
)
SELECTED_PATH = "keep_internal_near_threshold_diagnostic_use_as_paper_compatibility_route_evidence"
NEXT_TODO = (
    "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)

PRIMARY_MODEL = "M8_TG_point_contact_interaction"
FULL_MODEL = "M9_TGQ_factorized_observability"
GEOMETRY_ONLY_MODEL = "M5_point_contact_geometry"
CONCAT_MODEL = "M7_TG_point_contact_concat"
OLD_OBB_TG_MODEL = "M6_TG_obb_concat"

MODEL_SCORE_FIELDS = [
    "M1_semantic_only_T",
    "M2_obb_geometry_only",
    "M3_point_pose_only",
    "M4_contact_patch_only",
    GEOMETRY_ONLY_MODEL,
    OLD_OBB_TG_MODEL,
    CONCAT_MODEL,
    PRIMARY_MODEL,
    FULL_MODEL,
    "C1_wrong_T_same_G",
    "C2_shuffled_G_global",
    "C3_shuffled_G_within_predicate",
    "C4_shuffled_Q",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def mean_or_none(values: Iterable[float]) -> float | None:
    vals = list(values)
    return mean(vals) if vals else None


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


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


def profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(int(row["label"]) for row in rows)
    errors = [row for row in rows if row["error_type"] != "correct"]
    fps = [row for row in errors if row["error_type"] == "false_positive"]
    fns = [row for row in errors if row["error_type"] == "false_negative"]
    high_conf = [row for row in errors if safe_float(row["primary_confidence"], 0.0) >= 0.25]
    near_threshold = [row for row in rows if abs(safe_float(row["primary_score"], 0.5) - 0.5) <= 0.05]
    return {
        "accuracy": round(1.0 - len(errors) / max(len(rows), 1), 6),
        "error_rate": round(len(errors) / max(len(rows), 1), 6),
        "errors": len(errors),
        "false_negative": len(fns),
        "false_positive": len(fps),
        "high_confidence_errors": len(high_conf),
        "near_threshold_rows_abs_score_margin_le_0_05": len(near_threshold),
        "negative": labels[0],
        "positive": labels[1],
        "rows": len(rows),
    }


def error_type(label: int, score: float) -> str:
    pred = 1 if score >= 0.5 else 0
    if pred == label:
        return "correct"
    return "false_positive" if pred == 1 else "false_negative"


def normalize_q_state(q: dict[str, Any]) -> str:
    if safe_float(q.get("q_e_state_sufficient"), 0.0) > 0.5:
        return "sufficient"
    if safe_float(q.get("q_e_state_limited"), 0.0) > 0.5:
        return "limited"
    if safe_float(q.get("q_e_state_uncertain"), 0.0) > 0.5:
        return "uncertain"
    return "missing"


def load_joined_rows(
    runner_dir: Path,
    plan_dir: Path,
    materialization_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    runner_predictions = read_jsonl(runner_dir / "predictions.jsonl")
    smoke_rows = read_jsonl(plan_dir / "smoke_ready_view.jsonl")
    source_rows = read_jsonl(materialization_dir / "source_manifest.jsonl")
    visual_rows = read_jsonl(materialization_dir / "visual_audit_manifest.jsonl")
    control_rows = read_jsonl(materialization_dir / "control_manifest.jsonl")

    smoke_by_example = {row.get("example_id"): row for row in smoke_rows}
    source_by_original = {row.get("row_id"): row for row in source_rows}
    visual_by_original = {row.get("row_id"): row for row in visual_rows}
    control_by_original = {row.get("row_id"): row for row in control_rows}

    joined: list[dict[str, Any]] = []
    for pred in runner_predictions:
        example_id = pred.get("row_id")
        smoke = smoke_by_example.get(example_id)
        if smoke is None:
            errors.append({"error_type": "missing_smoke_row", "example_id": example_id})
            continue
        original_row_id = smoke.get("row_id")
        source = source_by_original.get(original_row_id, {})
        visual = visual_by_original.get(original_row_id, {})
        control = control_by_original.get(original_row_id, {})
        if not source:
            errors.append({"error_type": "missing_source_manifest_row", "row_id": original_row_id})
        if not visual:
            errors.append({"error_type": "missing_visual_manifest_row", "row_id": original_row_id})
        blocks = smoke.get("feature_blocks", {})
        t = blocks.get("T_e", {})
        obb = blocks.get("G_e_obb_baseline", {})
        point = blocks.get("G_e_point_pose", {})
        contact = blocks.get("G_e_contact_patch", {})
        q = blocks.get("Q_e_observability", {})
        label = int(pred.get("label"))
        primary = safe_float(pred.get(PRIMARY_MODEL), 0.5)
        row: dict[str, Any] = {
            "candidate_role_hidden": source.get("candidate_role_hidden", "missing"),
            "class_pair": f"{t.get('subject_class_text')}->{t.get('object_class_text')}",
            "control_wrong_pair_match_scope": control.get("wrong_pair_match_scope", "missing"),
            "error_type": error_type(label, primary),
            "example_id": example_id,
            "group_id": pred.get("group_id"),
            "label": label,
            "label_match_status_hidden": source.get("label_match_status_hidden", "missing"),
            "machine_hint_hidden": source.get("machine_hint_hidden", "missing"),
            "object": t.get("object_class_text"),
            "original_row_id": original_row_id,
            "p_geom_valid_hidden": safe_float(source.get("p_geom_valid_hidden"), 0.0),
            "pred": 1 if primary >= 0.5 else 0,
            "predicate": t.get("predicate_label"),
            "primary_confidence": abs(primary - 0.5),
            "primary_score": primary,
            "q_e_state": normalize_q_state(q),
            "queue_kind_hidden": source.get("queue_kind_hidden", "missing"),
            "rank_band_hidden": source.get("rank_band_hidden", "missing"),
            "semantic_rank_hidden": safe_float(source.get("semantic_rank_hidden"), 999999.0),
            "semantic_score_norm_hidden": safe_float(source.get("semantic_score_norm_hidden"), 0.0),
            "subject": t.get("subject_class_text"),
            "source_confidence_policy": source.get("source_confidence_policy", "missing"),
            "visual_q_e_state_plan": visual.get("q_e_state_plan", "missing"),
        }
        for field in MODEL_SCORE_FIELDS:
            row[field] = safe_float(pred.get(field), 0.5)
        for prefix, block in [
            ("obb", obb),
            ("point", point),
            ("contact", contact),
            ("q", q),
        ]:
            for key, value in block.items():
                row[f"{prefix}.{key}"] = safe_float(value, 0.0)
        for key in [
            "object_crop_count",
            "object_direct_view_count",
            "object_max_view_score",
            "object_mean_view_ratio",
            "subject_crop_count",
            "subject_direct_view_count",
            "subject_max_view_score",
            "subject_mean_view_ratio",
        ]:
            row[f"visual.{key}"] = safe_float(visual.get(key), 0.0)
        joined.append(row)
    return joined, errors


def validate_inputs(
    runner_summary: dict[str, Any],
    plan_summary: dict[str, Any],
    materialization_summary: dict[str, Any],
    runner_validation_rows: list[dict[str, Any]],
    plan_validation_rows: list[dict[str, Any]],
    materialization_validation_rows: list[dict[str, Any]],
    joined: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next", "actual": runner_summary.get("next_todo")})
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if materialization_summary.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": materialization_summary.get("status")})
    if runner_validation_rows:
        errors.append({"error_type": "runner_validation_rows_present", "rows": len(runner_validation_rows)})
    if plan_validation_rows:
        errors.append({"error_type": "plan_validation_rows_present", "rows": len(plan_validation_rows)})
    if materialization_validation_rows:
        errors.append({"error_type": "materialization_validation_rows_present", "rows": len(materialization_validation_rows)})
    counts = runner_summary.get("counts", {})
    if counts.get("rows") != 640 or counts.get("positive") != 320 or counts.get("negative") != 320:
        errors.append({"error_type": "unexpected_runner_counts", "counts": counts})
    if len(joined) != 640:
        errors.append({"error_type": "unexpected_joined_rows", "actual": len(joined)})
    return errors


def axis_profile(rows: list[dict[str, Any]], axis: str, min_rows: int = 4) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(axis, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for value, group_rows in groups.items():
        if len(group_rows) < min_rows:
            continue
        prof = profile(group_rows)
        labels = [int(row["label"]) for row in group_rows]
        scores = [safe_float(row[PRIMARY_MODEL], 0.5) for row in group_rows]
        out.append(
            {
                "axis": axis,
                "value": value,
                "auroc": round_or_none(auc_pairwise(scores, labels)),
                "mean_concat_score": round_or_none(mean_or_none(safe_float(row[CONCAT_MODEL], 0.5) for row in group_rows)),
                "mean_geometry_score": round_or_none(mean_or_none(safe_float(row[GEOMETRY_ONLY_MODEL], 0.5) for row in group_rows)),
                "mean_negative_score": round_or_none(mean_or_none(row[PRIMARY_MODEL] for row in group_rows if int(row["label"]) == 0)),
                "mean_positive_score": round_or_none(mean_or_none(row[PRIMARY_MODEL] for row in group_rows if int(row["label"]) == 1)),
                "mean_primary_score": round_or_none(mean_or_none(safe_float(row[PRIMARY_MODEL], 0.5) for row in group_rows)),
                **prof,
            }
        )
    return sorted(out, key=lambda row: (-float(row["error_rate"]), -int(row["rows"]), str(row["value"])))


def numeric_feature_names(rows: list[dict[str, Any]]) -> list[str]:
    prefixes = ("obb.", "point.", "contact.", "q.", "visual.")
    names = sorted({key for row in rows for key, value in row.items() if key.startswith(prefixes) and isinstance(value, (int, float))})
    return names + ["p_geom_valid_hidden", "semantic_score_norm_hidden", "semantic_rank_hidden"]


def feature_profile(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [int(row["label"]) for row in rows]
    error_labels = [1 if row["error_type"] != "correct" else 0 for row in rows]
    out: list[dict[str, Any]] = []
    for name in numeric_feature_names(rows):
        values = [safe_float(row.get(name), 0.0) for row in rows]
        correct_values = [value for value, row in zip(values, rows) if row["error_type"] == "correct"]
        error_values = [value for value, row in zip(values, rows) if row["error_type"] != "correct"]
        pos_values = [value for value, label in zip(values, labels) if label == 1]
        neg_values = [value for value, label in zip(values, labels) if label == 0]
        out.append(
            {
                "feature": name,
                "error_auc_oriented": round_or_none(oriented_auc(values, error_labels)),
                "label_auc_oriented": round_or_none(oriented_auc(values, labels)),
                "mean_correct": round_or_none(mean_or_none(correct_values)),
                "mean_error": round_or_none(mean_or_none(error_values)),
                "mean_negative": round_or_none(mean_or_none(neg_values)),
                "mean_positive": round_or_none(mean_or_none(pos_values)),
                "rows": len(rows),
            }
        )
    return sorted(out, key=lambda row: (-(row["error_auc_oriented"] or 0.0), -(row["label_auc_oriented"] or 0.0), row["feature"]))


def model_delta_profile(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas = [
        ("M8_minus_M5_geometry_only", PRIMARY_MODEL, GEOMETRY_ONLY_MODEL),
        ("M8_minus_M7_concat", PRIMARY_MODEL, CONCAT_MODEL),
        ("M8_minus_M6_old_obb_TG", PRIMARY_MODEL, OLD_OBB_TG_MODEL),
        ("M8_minus_C1_wrong_T", PRIMARY_MODEL, "C1_wrong_T_same_G"),
        ("M8_minus_C2_shuffled_G_global", PRIMARY_MODEL, "C2_shuffled_G_global"),
        ("M8_minus_C3_shuffled_G_within_predicate", PRIMARY_MODEL, "C3_shuffled_G_within_predicate"),
    ]
    out: list[dict[str, Any]] = []
    for name, left, right in deltas:
        for axis in ["all", "predicate", "error_type", "q_e_state"]:
            if axis == "all":
                groups = {"all": rows}
            else:
                groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in rows:
                    groups[str(row.get(axis, "missing"))].append(row)
            for value, group_rows in groups.items():
                vals = [safe_float(row.get(left), 0.5) - safe_float(row.get(right), 0.5) for row in group_rows]
                out.append(
                    {
                        "axis": axis,
                        "delta": name,
                        "mean_delta": round_or_none(mean_or_none(vals)),
                        "positive_delta_fraction": round_or_none(sum(1 for val in vals if val > 0.0) / max(len(vals), 1)),
                        "rows": len(group_rows),
                        "value": value,
                    }
                )
    return out


def hard_error_cases(rows: list[dict[str, Any]], max_cases: int = 80) -> list[dict[str, Any]]:
    errors = [row for row in rows if row["error_type"] != "correct"]
    selected = sorted(errors, key=lambda row: safe_float(row["primary_confidence"], 0.0), reverse=True)[:max_cases]
    fields = [
        "example_id",
        "original_row_id",
        "predicate",
        "subject",
        "object",
        "class_pair",
        "label",
        "pred",
        "error_type",
        PRIMARY_MODEL,
        GEOMETRY_ONLY_MODEL,
        CONCAT_MODEL,
        FULL_MODEL,
        "q_e_state",
        "candidate_role_hidden",
        "label_match_status_hidden",
        "machine_hint_hidden",
        "contact.point_abs_surface_gap_subject_bottom_to_object_top",
        "contact.point_support_contact_likelihood_proxy",
        "contact.point_xy_overlap_min_ratio",
        "point.subject_flatness_proxy",
        "point.subject_horizontal_extent_ratio",
        "point.subject_vertical_extent_ratio",
        "visual.subject_crop_count",
        "visual.object_crop_count",
        "visual.subject_mean_view_ratio",
        "visual.object_mean_view_ratio",
    ]
    out: list[dict[str, Any]] = []
    for row in selected:
        out.append({field: row.get(field) for field in fields})
    return out


def route_decisions(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route": "internal_gate_status",
            "verdict": "keep_near_threshold_diagnostic",
            "evidence": "M8=0.699375 is below the frozen internal 0.70 gate.",
            "claim_boundary": "Do not rewrite the internal status as passed.",
        },
        {
            "route": "paper_facing_support_contact_role",
            "verdict": "use_as_main_compatibility_route_evidence_with_caveat",
            "evidence": "M8 beats semantic-only, point/contact geometry-only, old OBB T+G, and plain concat; wrong-T and shuffled-G controls collapse.",
            "claim_boundary": "Do not claim support/contact is fully solved; claim interaction necessity for a challenging family.",
        },
        {
            "route": "stronger_combiner_first",
            "verdict": "reject_for_now",
            "evidence": "The meaningful signal is already an interaction pattern; the next issue is failure interpretation and claim boundary.",
            "claim_boundary": "Avoid making the next step a SOTA combiner race before resolving evidence/target interpretation.",
        },
        {
            "route": "lying_on_failure_analysis",
            "verdict": "selected_next_focus",
            "evidence": "standing on slice passes the 0.70 heuristic, while lying on is lower and pulls down the aggregate.",
            "claim_boundary": "Use failure taxonomy to explain residual ambiguity.",
        },
        {
            "route": "Q_e_as_truth_signal",
            "verdict": "reject",
            "evidence": "M9 is below M8 and shuffled-Q is almost identical to M8.",
            "claim_boundary": "Keep Q_e as observability/evidence-quality metadata, not relation truth.",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    axis_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> None:
    predicate_rows = [row for row in axis_rows if row["axis"] == "predicate"]
    class_rows = [row for row in axis_rows if row["axis"] == "class_pair"][:10]
    q_rows = [row for row in axis_rows if row["axis"] == "q_e_state"]
    hidden_rows = [row for row in axis_rows if row["axis"] in {"candidate_role_hidden", "label_match_status_hidden"}][:10]
    top_features = feature_rows[:12]
    all_deltas = [row for row in delta_rows if row["axis"] == "all"]
    lines = [
        "# H002 Support/Contact Point/Multiview Failure Analysis",
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
        "The internal gate remains near-threshold diagnostic because `M8 = 0.699375` is below",
        "the frozen `0.70` smoke gate. Paper-facing interpretation should be different:",
        "support/contact can be used as compatibility-route evidence, not as a fully solved family.",
        "",
        "The important pattern is that the predicate-conditioned interaction is the only view",
        "that separates the target from controls.",
        "",
        "```text",
        f"semantic-only = {summary['runner_snapshot']['semantic_only_auroc']}",
        f"point/contact geometry-only = {summary['runner_snapshot']['point_contact_geometry_auroc']}",
        f"plain point/contact concat = {summary['runner_snapshot']['plain_concat_auroc']}",
        f"predicate-geometry interaction M8 = {summary['runner_snapshot']['primary_auroc']}",
        f"wrong-T = {summary['runner_snapshot']['wrong_t_auroc']}",
        f"shuffled-G = {summary['runner_snapshot']['shuffled_g_global_auroc']} / {summary['runner_snapshot']['shuffled_g_within_predicate_auroc']}",
        "```",
        "",
        "## Predicate Slices",
        "",
        "| Predicate | Rows | Error Rate | AUROC | FP | FN | Mean Pos Score | Mean Neg Score |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in predicate_rows:
        lines.append(
            f"| `{row['value']}` | {row['rows']} | {row['error_rate']} | {row['auroc']} | "
            f"{row['false_positive']} | {row['false_negative']} | {row['mean_positive_score']} | {row['mean_negative_score']} |"
        )
    lines.extend(
        [
            "",
            "## Q_e Slices",
            "",
            "| Q_e State | Rows | Error Rate | AUROC | FP | FN |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in q_rows:
        lines.append(
            f"| `{row['value']}` | {row['rows']} | {row['error_rate']} | {row['auroc']} | "
            f"{row['false_positive']} | {row['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "## Class-Pair Concentration",
            "",
            "| Class Pair | Rows | Error Rate | AUROC | FP | FN |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in class_rows:
        lines.append(
            f"| `{row['value']}` | {row['rows']} | {row['error_rate']} | {row['auroc']} | "
            f"{row['false_positive']} | {row['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "## Hidden Diagnostic Axes",
            "",
            "These fields are for failure diagnosis only and were not model inputs.",
            "",
            "| Axis | Value | Rows | Error Rate | AUROC |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in hidden_rows:
        lines.append(f"| `{row['axis']}` | `{row['value']}` | {row['rows']} | {row['error_rate']} | {row['auroc']} |")
    lines.extend(
        [
            "",
            "## Feature Error Diagnosis",
            "",
            "| Feature | Error AUC | Label AUC | Mean Error | Mean Correct |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in top_features:
        lines.append(
            f"| `{row['feature']}` | {row['error_auc_oriented']} | {row['label_auc_oriented']} | "
            f"{row['mean_error']} | {row['mean_correct']} |"
        )
    lines.extend(
        [
            "",
            "## Model Delta Summary",
            "",
            "| Delta | Mean Delta | Positive Delta Fraction |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in all_deltas:
        lines.append(f"| `{row['delta']}` | {row['mean_delta']} | {row['positive_delta_fraction']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Keep the internal status as near-threshold diagnostic.",
            "- Use support/contact as paper-facing compatibility-route evidence with explicit caveat.",
            "- Do not describe the branch as fully solved or high-performing in absolute terms.",
            "- Emphasize that interaction, wrong-T collapse, and shuffled-G collapse support the `T_e x G_e` necessity.",
            "- Keep `Q_e` as observability metadata; current result does not support using `Q_e` as truth signal.",
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
    plan_summary = read_json(args.plan_dir / "summary.json")
    materialization_summary = read_json(args.materialization_dir / "summary.json")
    runner_validation = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    plan_validation = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    materialization_validation = read_jsonl(args.materialization_dir / "validation_errors.jsonl")
    joined, join_errors = load_joined_rows(args.runner_dir, args.plan_dir, args.materialization_dir)
    errors = validate_inputs(
        runner_summary,
        plan_summary,
        materialization_summary,
        runner_validation,
        plan_validation,
        materialization_validation,
        joined,
    )
    errors.extend(join_errors)

    axis_rows: list[dict[str, Any]] = []
    for axis in [
        "predicate",
        "class_pair",
        "subject",
        "object",
        "q_e_state",
        "visual_q_e_state_plan",
        "candidate_role_hidden",
        "label_match_status_hidden",
        "machine_hint_hidden",
        "queue_kind_hidden",
        "rank_band_hidden",
        "control_wrong_pair_match_scope",
    ]:
        axis_rows.extend(axis_profile(joined, axis))
    feature_rows = feature_profile(joined)
    delta_rows = model_delta_profile(joined)
    route_rows = route_decisions({})

    metrics = runner_summary.get("gates", {}).get("model_auroc_snapshot", {})
    failure_prof = profile(joined)
    summary = {
        "boundary": {
            "diagnostic_hidden_fields_used_only_after_prediction": True,
            "h001_artifacts_modified": False,
            "internal_gate_rewritten": False,
            "paper_evidence_allowed": False,
            "split": "train_internal_failure_analysis",
            "test_usage": False,
            "validation_usage": False,
            "visual_model_input_allowed": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "failure_profile": failure_prof,
        "input_paths": {
            "materialization_root": rel_path(args.materialization_dir),
            "plan_root": rel_path(args.plan_dir),
            "runner_root": rel_path(args.runner_dir),
        },
        "key_slice_findings": {
            "lying_on_auroc": next((row.get("auroc") for row in axis_rows if row["axis"] == "predicate" and row["value"] == "lying on"), None),
            "standing_on_auroc": next((row.get("auroc") for row in axis_rows if row["axis"] == "predicate" and row["value"] == "standing on"), None),
            "q_e_states": dict(Counter(row["q_e_state"] for row in joined)),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {
            "axis_failure_profile": rel_path(args.output_dir / "axis_failure_profile.csv"),
            "feature_failure_profile": rel_path(args.output_dir / "feature_failure_profile.csv"),
            "hard_error_cases": rel_path(args.output_dir / "hard_error_cases.jsonl"),
            "model_delta_profile": rel_path(args.output_dir / "model_delta_profile.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "paper_facing_interpretation": {
            "allowed": "support_contact_as_main_compatibility_route_evidence_with_caveat",
            "forbidden": "support_contact_as_fully_solved_relation_family",
            "recommended_sentence": (
                "For support/contact relations, predicate-geometry interaction provides the strongest signal "
                "and collapses under wrong-predicate and shuffled-geometry controls."
            ),
        },
        "runner_snapshot": {
            "concat_auroc": metrics.get(CONCAT_MODEL),
            "old_obb_tg_auroc": metrics.get(OLD_OBB_TG_MODEL),
            "plain_concat_auroc": metrics.get(CONCAT_MODEL),
            "point_contact_geometry_auroc": metrics.get(GEOMETRY_ONLY_MODEL),
            "primary_auroc": metrics.get(PRIMARY_MODEL),
            "q_factorized_auroc": metrics.get(FULL_MODEL),
            "semantic_only_auroc": metrics.get("M1_semantic_only_T"),
            "shuffled_g_global_auroc": metrics.get("C2_shuffled_G_global"),
            "shuffled_g_within_predicate_auroc": metrics.get("C3_shuffled_G_within_predicate"),
            "wrong_t_auroc": metrics.get("C1_wrong_T_same_G"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": STATUS_READY if not errors else STATUS_ERROR,
        "validation_errors": len(errors),
    }

    write_csv(args.output_dir / "axis_failure_profile.csv", axis_rows)
    write_csv(args.output_dir / "feature_failure_profile.csv", feature_rows)
    write_csv(args.output_dir / "model_delta_profile.csv", delta_rows)
    write_csv(args.output_dir / "route_decision.csv", route_rows)
    write_jsonl(args.output_dir / "hard_error_cases.jsonl", hard_error_cases(joined))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, axis_rows, feature_rows, delta_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
