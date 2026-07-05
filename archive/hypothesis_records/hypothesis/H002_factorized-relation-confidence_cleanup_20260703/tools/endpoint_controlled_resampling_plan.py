#!/usr/bin/env python3
"""Plan endpoint-controlled resampling for H002 support/vertical labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/row_diagnostics.jsonl"
)
DEFAULT_INPUT_SUMMARY = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/summary.json"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_resampling_plan_all_label_ready"

C3_VIEW = "C3_linear_v2"
ENDPOINT_VIEW = "K5_endpoint_type_only"
STRICT_KEY = "endpoint_flag_pattern"
TARGET_PER_CLASS_PER_KEY = 8
MIN_POSTERIOR_ROWS = 80
TARGET_EXPANDED_ROWS = 120


PROTOCOLS = [
    {
        "protocol_id": "P0_current_all",
        "description": "No endpoint control; current all-label-ready slice.",
        "keys": [],
        "role": "current_shortcut_diagnostic",
    },
    {
        "protocol_id": "P1_family_only",
        "description": "Balance only within relation family.",
        "keys": ["predicate_family"],
        "role": "insufficient_endpoint_control",
    },
    {
        "protocol_id": "P2_predicate_label",
        "description": "Balance within predicate label.",
        "keys": ["predicate_label"],
        "role": "insufficient_endpoint_control",
    },
    {
        "protocol_id": "P3_object_role",
        "description": "Balance within coarse endpoint object role.",
        "keys": ["object_role"],
        "role": "relaxed_endpoint_control",
    },
    {
        "protocol_id": "P4_family_object_role",
        "description": "Balance within relation family and coarse endpoint object role.",
        "keys": ["predicate_family", "object_role"],
        "role": "relaxed_endpoint_control",
    },
    {
        "protocol_id": "P5_family_object_subject_role",
        "description": "Balance within family, object role, and subject room-surface role.",
        "keys": ["predicate_family", "object_role", "subject_role"],
        "role": "near_strict_endpoint_control",
    },
    {
        "protocol_id": "P6_predicate_object_role",
        "description": "Balance within predicate label and coarse endpoint object role.",
        "keys": ["predicate_label", "object_role"],
        "role": "predicate_relaxed_control",
    },
    {
        "protocol_id": "P7_strict_endpoint_flag",
        "description": "Balance within the exact endpoint flag pattern.",
        "keys": [STRICT_KEY],
        "role": "strict_endpoint_control_seed",
    },
    {
        "protocol_id": "P8_strict_endpoint_flag_rank",
        "description": "Balance within exact endpoint flag pattern and semantic rank bin.",
        "keys": [STRICT_KEY, "rank_bin"],
        "role": "strict_endpoint_plus_rank_control_seed",
    },
    {
        "protocol_id": "P9_endpoint_label_pattern",
        "description": "Balance within exact subject-predicate-object label pattern.",
        "keys": ["endpoint_label_pattern"],
        "role": "too_strict_endpoint_label_control",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--input-summary", type=Path, default=DEFAULT_INPUT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-per-class-per-key", type=int, default=TARGET_PER_CLASS_PER_KEY)
    parser.add_argument("--min-posterior-rows", type=int, default=MIN_POSTERIOR_ROWS)
    parser.add_argument("--target-expanded-rows", type=int, default=TARGET_EXPANDED_ROWS)
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


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


def sf(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def rank_bin(row: dict[str, Any]) -> str:
    rank = sf(row.get("semantic_rank"), 9999.0)
    if rank < 50:
        return "rank_lt50"
    if rank < 100:
        return "rank_50_99"
    if rank < 200:
        return "rank_100_199"
    return "rank_ge200"


def object_role(row: dict[str, Any]) -> str:
    roles = []
    if sf(row.get("endpoint_object_floor_like_flag")) >= 0.5:
        roles.append("floor")
    if sf(row.get("endpoint_object_support_surface_like_flag")) >= 0.5:
        roles.append("support_surface")
    if sf(row.get("endpoint_object_wall_like_flag")) >= 0.5:
        roles.append("wall")
    return "+".join(roles) if roles else "object_other"


def subject_role(row: dict[str, Any]) -> str:
    return "subject_room_surface" if sf(row.get("endpoint_subject_room_surface_flag")) >= 0.5 else "subject_other"


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = json.loads(json.dumps(rows))
    for row in output:
        row["rank_bin"] = rank_bin(row)
        row["object_role"] = object_role(row)
        row["subject_role"] = subject_role(row)
    return output


def group_rows(rows: list[dict[str, Any]], keys: list[str]) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(field, "missing")) for field in keys) if keys else ("all",)
        groups[key].append(row)
    return dict(groups)


def select_balanced(rows: list[dict[str, Any]], keys: list[str]) -> tuple[list[dict[str, Any]], dict[tuple[str, ...], list[dict[str, Any]]]]:
    groups = group_rows(rows, keys)
    selected = []
    for key in sorted(groups):
        group = groups[key]
        positives = sorted([row for row in group if int(row["target"]) == 1], key=lambda row: row["prediction_id"])
        negatives = sorted([row for row in group if int(row["target"]) == 0], key=lambda row: row["prediction_id"])
        take = min(len(positives), len(negatives))
        selected.extend(positives[:take])
        selected.extend(negatives[:take])
    return selected, groups


def metrics_for(rows: list[dict[str, Any]], view: str) -> dict[str, Any] | None:
    if not rows or len({int(row["target"]) for row in rows}) < 2:
        return None
    labels = [int(row["target"]) for row in rows]
    scores = [sf(row[f"prob_{view}"], 0.5) for row in rows]
    return smoke.metrics(labels, scores)


def metric_delta(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any]:
    left = left or {}
    right = right or {}
    output = {}
    for key in ["auroc", "auprc", "brier", "ece_5bin", "accuracy_at_0_5"]:
        if left.get(key) is None or right.get(key) is None:
            output[key] = None
        else:
            output[key] = left[key] - right[key]
    return output


def endpoint_purity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = group_rows(rows, [STRICT_KEY])
    pure_rows = 0
    max_purity = 0.0
    weighted_purity_sum = 0.0
    for group in groups.values():
        positives = sum(1 for row in group if int(row["target"]) == 1)
        rate = positives / len(group)
        purity = abs(rate - 0.5)
        max_purity = max(max_purity, purity)
        weighted_purity_sum += purity * len(group)
        if rate in {0.0, 1.0}:
            pure_rows += len(group)
    return {
        "endpoint_flag_groups": len(groups),
        "endpoint_flag_pure_rows": pure_rows,
        "endpoint_flag_pure_row_rate": pure_rows / len(rows) if rows else None,
        "endpoint_flag_max_purity_from_balance": max_purity if rows else None,
        "endpoint_flag_weighted_purity_from_balance": weighted_purity_sum / len(rows) if rows else None,
    }


def protocol_summary(rows: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    selected, groups = select_balanced(rows, protocol["keys"])
    target_counts = Counter(int(row["target"]) for row in selected)
    group_counts = []
    for key, group in groups.items():
        pos = sum(1 for row in group if int(row["target"]) == 1)
        neg = len(group) - pos
        group_counts.append((key, pos, neg, len(group)))
    both_groups = sum(1 for _, pos, neg, _ in group_counts if pos > 0 and neg > 0)
    pure_groups = sum(1 for _, pos, neg, _ in group_counts if pos == 0 or neg == 0)
    c3_metrics = metrics_for(selected, C3_VIEW)
    endpoint_metrics = metrics_for(selected, ENDPOINT_VIEW)
    delta = metric_delta(endpoint_metrics, c3_metrics)
    purity = endpoint_purity(selected)
    shortcut_reduced = (
        selected
        and delta.get("auprc") is not None
        and delta["auprc"] <= 0.05
        and (purity.get("endpoint_flag_weighted_purity_from_balance") or 0.0) <= 0.10
    )
    enough_rows = len(selected) >= MIN_POSTERIOR_ROWS
    return {
        "protocol_id": protocol["protocol_id"],
        "role": protocol["role"],
        "description": protocol["description"],
        "matching_keys": "+".join(protocol["keys"]) if protocol["keys"] else "none",
        "selected_rows": len(selected),
        "selected_positive": target_counts[1],
        "selected_negative": target_counts[0],
        "retention_rate": len(selected) / len(rows) if rows else None,
        "group_count": len(groups),
        "both_class_group_count": both_groups,
        "pure_group_count": pure_groups,
        "dropped_rows": len(rows) - len(selected),
        "enough_rows_for_posterior_smoke": enough_rows,
        "endpoint_shortcut_reduced": bool(shortcut_reduced),
        "usable_now_for_posterior": bool(enough_rows and shortcut_reduced),
        "c3_auroc": c3_metrics.get("auroc") if c3_metrics else None,
        "c3_auprc": c3_metrics.get("auprc") if c3_metrics else None,
        "c3_brier": c3_metrics.get("brier") if c3_metrics else None,
        "endpoint_auroc": endpoint_metrics.get("auroc") if endpoint_metrics else None,
        "endpoint_auprc": endpoint_metrics.get("auprc") if endpoint_metrics else None,
        "endpoint_brier": endpoint_metrics.get("brier") if endpoint_metrics else None,
        "endpoint_delta_auroc_vs_c3": delta.get("auroc"),
        "endpoint_delta_auprc_vs_c3": delta.get("auprc"),
        "endpoint_delta_brier_vs_c3": delta.get("brier"),
        "endpoint_delta_ece_vs_c3": delta.get("ece_5bin"),
        **purity,
    }


def group_count_rows(rows: list[dict[str, Any]], keys: list[str], protocol_id: str) -> list[dict[str, Any]]:
    outputs = []
    for key, group in sorted(group_rows(rows, keys).items(), key=lambda item: (-len(item[1]), item[0])):
        positives = sum(1 for row in group if int(row["target"]) == 1)
        negatives = len(group) - positives
        outputs.append(
            {
                "protocol_id": protocol_id,
                "matching_keys": "+".join(keys) if keys else "none",
                "key_value": " | ".join(key),
                "rows": len(group),
                "positive": positives,
                "negative": negatives,
                "balanced_selectable_rows": 2 * min(positives, negatives),
                "is_pure": positives == 0 or negatives == 0,
                "positive_rate": positives / len(group),
                "purity_from_balance": abs(positives / len(group) - 0.5),
            }
        )
    return outputs


def endpoint_deficits(rows: list[dict[str, Any]], target_per_class: int) -> list[dict[str, Any]]:
    outputs = []
    for key, group in sorted(group_rows(rows, [STRICT_KEY]).items(), key=lambda item: (-len(item[1]), item[0])):
        positives = sum(1 for row in group if int(row["target"]) == 1)
        negatives = len(group) - positives
        if len(group) < 2:
            desired = 0
        else:
            desired = min(target_per_class, max(positives, negatives))
        need_positive = max(0, desired - positives)
        need_negative = max(0, desired - negatives)
        if need_positive == 0 and need_negative == 0:
            priority = "filled_or_no_action"
        elif positives == 0 or negatives == 0:
            priority = "high_pure_endpoint_group"
        else:
            priority = "medium_imbalanced_endpoint_group"
        outputs.append(
            {
                "endpoint_flag_pattern": " | ".join(key),
                "rows": len(group),
                "positive": positives,
                "negative": negatives,
                "current_balanced_rows": 2 * min(positives, negatives),
                "desired_per_class_cap": desired,
                "need_positive_labels": need_positive,
                "need_negative_labels": need_negative,
                "priority": priority,
                "positive_rate": positives / len(group),
            }
        )
    return outputs


def sanitize_row(row: dict[str, Any], protocol_id: str) -> dict[str, Any]:
    fields = [
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        "target",
        "target_reason",
        "endpoint_flag_pattern",
        "endpoint_label_pattern",
        "object_role",
        "subject_role",
        "rank_bin",
        "semantic_score_norm",
        "semantic_rank",
        "p_geom_valid",
        "strong_raw_witness_score",
        "prob_C3_linear_v2",
        "prob_K5_endpoint_type_only",
    ]
    output = {field: row.get(field) for field in fields}
    output["protocol_id"] = protocol_id
    output["record_type"] = "h002_endpoint_controlled_resampling_seed_row"
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Endpoint-Controlled Resampling Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only planning artifact.",
        "- No validation/test rows are used.",
        "- No new posterior model is trained.",
        "- Endpoint/object-type fields are used only for target/control construction, not deployable model evidence.",
        "- Results are not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Protocol Candidates",
        "",
        "| Protocol | Keys | Rows | Retention | Endpoint dAUPRC vs C3 | Endpoint AUROC | C3 AUPRC | Usable Now |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["protocol_candidates"]:
        lines.append(
            f"| `{row['protocol_id']}` | `{row['matching_keys']}` | {row['selected_rows']} | "
            f"{fmt(row['retention_rate'])} | {fmt(row['endpoint_delta_auprc_vs_c3'])} | "
            f"{fmt(row['endpoint_auroc'])} | {fmt(row['c3_auprc'])} | `{row['usable_now_for_posterior']}` |"
        )
    lines.extend(
        [
            "",
            "## Recommended Protocol",
            "",
            f"- Primary key: `{summary['recommended_protocol']['primary_matching_key']}`",
            f"- Existing strict seed rows: `{summary['recommended_protocol']['strict_seed_rows']}`",
            f"- Minimum posterior rows: `{summary['recommended_protocol']['min_posterior_rows']}`",
            f"- Expanded target rows: `{summary['recommended_protocol']['target_expanded_rows']}`",
            f"- Target per endpoint key/class cap: `{summary['recommended_protocol']['target_per_class_per_key']}`",
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_rows = as_abs(args.input_rows)
    input_summary = as_abs(args.input_summary)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = enrich_rows(smoke.read_jsonl(input_rows))
    previous_summary = read_json(input_summary)

    validation_errors = []
    if previous_summary.get("next_todo") != "revised_sampling_all_label_ready_endpoint_controlled_resampling_plan":
        validation_errors.append({"error_type": "unexpected_previous_next_todo", "value": previous_summary.get("next_todo")})
    if previous_summary.get("boundary", {}).get("validation_usage") is not False:
        validation_errors.append({"error_type": "previous_summary_validation_usage_not_false"})
    if previous_summary.get("boundary", {}).get("test_usage") is not False:
        validation_errors.append({"error_type": "previous_summary_test_usage_not_false"})
    for row in rows:
        required = [f"prob_{C3_VIEW}", f"prob_{ENDPOINT_VIEW}", STRICT_KEY, "target"]
        missing = [field for field in required if field not in row]
        if missing:
            validation_errors.append({"error_type": "row_missing_required_field", "prediction_id": row.get("prediction_id"), "missing": missing})

    protocol_rows = [protocol_summary(rows, protocol) for protocol in PROTOCOLS] if not validation_errors else []
    protocol_by_id = {row["protocol_id"]: row for row in protocol_rows}
    strict_seed, _ = select_balanced(rows, [STRICT_KEY]) if not validation_errors else ([], {})
    relaxed_seed, _ = select_balanced(rows, ["object_role"]) if not validation_errors else ([], {})
    group_rows_output = []
    for protocol in PROTOCOLS:
        if protocol["protocol_id"] in {"P7_strict_endpoint_flag", "P3_object_role", "P5_family_object_subject_role"}:
            group_rows_output.extend(group_count_rows(rows, protocol["keys"], protocol["protocol_id"]))
    deficits = endpoint_deficits(rows, args.target_per_class_per_key) if not validation_errors else []
    total_needed = {
        "positive": sum(row["need_positive_labels"] for row in deficits),
        "negative": sum(row["need_negative_labels"] for row in deficits),
    }
    any_usable = any(row["usable_now_for_posterior"] for row in protocol_rows)
    status = (
        "h002_endpoint_controlled_resampling_plan_input_errors"
        if validation_errors
        else "h002_endpoint_controlled_resampling_plan_ready_needs_label_expansion"
    )
    next_todo = (
        "fix_endpoint_controlled_resampling_plan_inputs"
        if validation_errors
        else "revised_sampling_endpoint_controlled_candidate_mining"
    )
    decision = (
        "Input errors block endpoint-controlled planning."
        if validation_errors
        else (
            "The current all-label-ready pool is not sufficient for endpoint-controlled posterior smoke: "
            f"strict endpoint-flag matching leaves only {len(strict_seed)} rows, below the "
            f"{args.min_posterior_rows}-row minimum. Use the strict endpoint flag as the primary "
            "matching key for the next label-expansion pass; keep coarse object-role matching only as a "
            "relaxed diagnostic seed."
        )
    )

    recommended = {
        "primary_matching_key": STRICT_KEY,
        "primary_protocol_id": "P7_strict_endpoint_flag",
        "relaxed_diagnostic_key": "object_role",
        "relaxed_protocol_id": "P3_object_role",
        "strict_seed_rows": len(strict_seed),
        "relaxed_seed_rows": len(relaxed_seed),
        "min_posterior_rows": args.min_posterior_rows,
        "target_expanded_rows": args.target_expanded_rows,
        "target_per_class_per_key": args.target_per_class_per_key,
        "current_pool_usable_without_more_labels": any_usable,
        "label_deficit_to_cap": total_needed,
        "do_not_use_endpoint_as_model_input": True,
        "keep_c3_as_reference": True,
    }
    target_counts = Counter(int(row["target"]) for row in rows)
    summary = {
        "schema_version": "h002_endpoint_controlled_resampling_plan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_paths": {
            "row_diagnostics": rel_path(input_rows),
            "previous_summary": rel_path(input_summary),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "new_model_training": False,
            "endpoint_as_main_model_evidence": False,
            "paper_metric_evidence": False,
        },
        "rows": len(rows),
        "positive": target_counts[1],
        "negative": target_counts[0],
        "validation_errors": validation_errors,
        "protocol_candidates": protocol_rows,
        "recommended_protocol": recommended,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_dir / "summary.json", summary)
    write_csv(output_dir / "protocol_candidates.csv", protocol_rows)
    write_csv(output_dir / "endpoint_key_groups.csv", group_rows_output)
    write_csv(output_dir / "endpoint_label_deficits.csv", deficits)
    write_jsonl(output_dir / "strict_endpoint_seed_rows.jsonl", [sanitize_row(row, "P7_strict_endpoint_flag") for row in strict_seed])
    write_jsonl(output_dir / "relaxed_object_role_seed_rows.jsonl", [sanitize_row(row, "P3_object_role") for row in relaxed_seed])
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"rows={summary['rows']} pos={summary['positive']} neg={summary['negative']}")
    print(f"strict_endpoint_seed_rows={len(strict_seed)}")
    print(f"relaxed_object_role_seed_rows={len(relaxed_seed)}")
    if protocol_by_id:
        strict = protocol_by_id["P7_strict_endpoint_flag"]
        relaxed = protocol_by_id["P3_object_role"]
        print(f"strict_endpoint_d_auprc_vs_c3={fmt(strict['endpoint_delta_auprc_vs_c3'])}")
        print(f"relaxed_object_role_d_auprc_vs_c3={fmt(relaxed['endpoint_delta_auprc_vs_c3'])}")
    print(f"needed_positive_labels_to_cap={total_needed['positive']}")
    print(f"needed_negative_labels_to_cap={total_needed['negative']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
