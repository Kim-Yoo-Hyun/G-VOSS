#!/usr/bin/env python3
"""Analyze why relative_vertical failed after grouped evaluation review."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner"
DEFAULT_SPLIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/splits/latest"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review"

EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_input_errors"
SELECTED_PATH = "repair_grouped_eval_compatibility_feature_extractor_then_rerun"
NEXT_TODO = "compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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
                fields.append(key)
                seen.add(key)
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
        output = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(output) or math.isinf(output):
        return None
    return output


def average_ranks(scores: list[float]) -> list[float]:
    indexed = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    pos = 0
    while pos < len(indexed):
        end = pos + 1
        while end < len(indexed) and indexed[end][1] == indexed[pos][1]:
            end += 1
        avg = (pos + 1 + end) / 2.0
        for idx in range(pos, end):
            ranks[indexed[idx][0]] = avg
        pos = end
    return ranks


def auc(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = average_ranks(scores)
    rank_sum_pos = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    return (rank_sum_pos - positives * (positives + 1) / 2.0) / (positives * negatives)


def flatten_numeric(prefix: str, value: Any) -> dict[str, float]:
    output: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            output.update(flatten_numeric(f"{prefix}.{key}", child))
    elif isinstance(value, bool):
        output[prefix] = 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        output[prefix] = float(value)
    return output


def runner_numeric_probe(g_block: dict[str, Any], suffix: str) -> tuple[str | None, float | None]:
    flattened = flatten_numeric("G", g_block)
    matches = [(key, value) for key, value in flattened.items() if key.endswith(suffix)]
    return matches[0] if matches else (None, None)


def raw_gvec(row: dict[str, Any]) -> dict[str, float]:
    try:
        gvec = row["feature_blocks"]["G_e"]["G_e_raw"]["raw_geometry_feature_vector"]
    except KeyError:
        return {}
    return gvec if isinstance(gvec, dict) else {}


def predicate_sign(row: dict[str, Any]) -> float:
    predicate = str(row.get("predicate_label") or "")
    if predicate == "higher than":
        return 1.0
    if predicate == "lower than":
        return -1.0
    return 0.0


def metric_row(
    rows: list[dict[str, str]],
    *,
    level: str,
    route_family: str,
    predicate_label: str,
    protocol_split: str,
    view_id: str,
) -> dict[str, str] | None:
    for row in rows:
        if (
            row.get("level") == level
            and row.get("route_family") == route_family
            and row.get("predicate_label") == predicate_label
            and row.get("protocol_split") == protocol_split
            and row.get("view_id") == view_id
        ):
            return row
    return None


def validate_inputs(
    review_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    route_metrics: list[dict[str, str]],
    review_errors: list[dict[str, Any]],
    eval_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_summary_validation_errors", "actual": review_summary.get("validation_errors")})
    if review_errors:
        errors.append({"error_type": "review_validation_error_rows_present", "rows": len(review_errors)})
    if eval_errors:
        errors.append({"error_type": "eval_validation_error_rows_present", "rows": len(eval_errors)})
    rv_rows = [row for row in rows if row.get("route_family") == "relative_vertical"]
    if not rv_rows:
        errors.append({"error_type": "missing_relative_vertical_rows"})
    if not route_metrics:
        errors.append({"error_type": "missing_route_metrics"})
    return errors


def split_feature_probe(rows: list[dict[str, Any]], route_metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    rv_rows = [row for row in rows if row.get("route_family") == "relative_vertical"]
    split_names = ["internal_train", "internal_dev", "internal_heldout"]
    predicates = ["ALL", "higher than", "lower than"]

    for split in split_names:
        for predicate in predicates:
            bucket = [row for row in rv_rows if row.get("protocol_split") == split]
            if predicate != "ALL":
                bucket = [row for row in bucket if row.get("predicate_label") == predicate]
            labels = [int(row["target_y"]) for row in bucket]
            signs = [predicate_sign(row) for row in bucket]
            true_cdz = [sign * float(raw_gvec(row).get("center_delta_z", 0.0)) for row, sign in zip(bucket, signs)]
            true_norm_cdz = [
                sign * float(raw_gvec(row).get("normalized_center_delta_z", 0.0))
                for row, sign in zip(bucket, signs)
            ]
            true_gap = [
                sign * float(raw_gvec(row).get("vertical_gap_subject_on_object", 0.0))
                for row, sign in zip(bucket, signs)
            ]
            runner_values: list[float] = []
            runner_keys: list[str] = []
            for row, sign in zip(bucket, signs):
                key, value = runner_numeric_probe(row["feature_blocks"]["G_e"], "center_delta_z")
                runner_keys.append(key or "missing")
                runner_values.append(sign * float(value if value is not None else 0.0))
            m4_metric = (
                metric_row(
                    route_metrics,
                    level="route_family" if predicate == "ALL" else "predicate",
                    route_family="relative_vertical",
                    predicate_label="ALL" if predicate == "ALL" else predicate,
                    protocol_split=split,
                    view_id="M4_TxG_compatibility",
                )
                if split != "internal_train"
                else None
            )
            probes.append(
                {
                    "protocol_split": split,
                    "predicate_label": predicate,
                    "rows": len(bucket),
                    "positive": sum(labels),
                    "negative": len(labels) - sum(labels),
                    "oracle_auc_signed_center_delta_z": auc(labels, true_cdz),
                    "oracle_auc_signed_normalized_center_delta_z": auc(labels, true_norm_cdz),
                    "oracle_auc_signed_vertical_gap": auc(labels, true_gap),
                    "runner_candidate_auc_suffix_center_delta_z": auc(labels, runner_values),
                    "runner_candidate_selected_key": Counter(runner_keys).most_common(1)[0][0] if runner_keys else "missing",
                    "runner_candidate_unique_values": len(set(runner_values)),
                    "reported_M4_auroc": as_float(m4_metric.get("auroc")) if m4_metric else None,
                    "reported_M4_balanced_accuracy": as_float(m4_metric.get("balanced_accuracy")) if m4_metric else None,
                }
            )
    return probes


def collision_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rv_rows = [row for row in rows if row.get("route_family") == "relative_vertical"]
    output: list[dict[str, Any]] = []
    for suffix, expected_key in [
        ("center_delta_z", "G.G_e_raw.raw_geometry_feature_vector.center_delta_z"),
        ("normalized_center_delta_z", "G.G_e_raw.raw_geometry_feature_vector.normalized_center_delta_z"),
        ("vertical_gap_subject_on_object", "G.G_e_raw.raw_geometry_feature_vector.vertical_gap_subject_on_object"),
    ]:
        keys = []
        values = []
        for row in rv_rows:
            key, value = runner_numeric_probe(row["feature_blocks"]["G_e"], suffix)
            keys.append(key or "missing")
            values.append(value)
        key_counts = Counter(keys)
        selected_key, selected_count = key_counts.most_common(1)[0]
        output.append(
            {
                "suffix": suffix,
                "expected_raw_key": expected_key,
                "runner_selected_key": selected_key,
                "selected_count": selected_count,
                "rows": len(rv_rows),
                "is_collision": selected_key != expected_key,
                "is_harmful_collision": "raw_geometry_feature_available_mask" in selected_key,
                "unique_selected_values": len(set(values)),
                "selected_key_is_availability_mask": "raw_geometry_feature_available_mask" in selected_key,
            }
        )
    return output


def write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    probes: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
) -> None:
    heldout_all = next(
        item
        for item in probes
        if item["protocol_split"] == "internal_heldout" and item["predicate_label"] == "ALL"
    )
    lines = [
        "# H002 Relative-Vertical Failure Analysis",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Verdict",
        "",
        "The grouped `relative_vertical` failure is primarily an implementation-level feature extraction failure, not evidence that the route is intrinsically invalid.",
        "",
        f"On internal heldout, explicit `predicate_sign * raw_geometry_feature_vector.center_delta_z` has AUROC `{heldout_all['oracle_auc_signed_center_delta_z']:.6f}`, while the grouped runner's suffix-based compatibility feature has AUROC `{heldout_all['runner_candidate_auc_suffix_center_delta_z']:.6f}`.",
        "",
        "The runner selected the availability-mask key instead of the raw geometry value:",
        "",
        "| Suffix | Expected raw key | Runner selected key | Harmful collision |",
        "| --- | --- | --- | --- |",
    ]
    for item in collisions:
        lines.append(
            f"| `{item['suffix']}` | `{item['expected_raw_key']}` | `{item['runner_selected_key']}` | {item['is_harmful_collision']} |"
        )
    lines.extend(
        [
            "",
            "## Split And Predicate Probe",
            "",
            "| Split | Predicate | Rows | Oracle signed center-dz AUROC | Oracle signed gap AUROC | Runner suffix center-dz AUROC | Reported M4 AUROC |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in probes:
        if item["protocol_split"] == "internal_train":
            reported = ""
        else:
            reported = f"{item['reported_M4_auroc']:.6f}" if item["reported_M4_auroc"] is not None else ""
        lines.append(
            "| {protocol_split} | `{predicate_label}` | {rows} | {oracle_auc_signed_center_delta_z:.6f} | {oracle_auc_signed_vertical_gap:.6f} | {runner_candidate_auc_suffix_center_delta_z:.6f} | {reported} |".format(
                reported=reported,
                **item,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The target is separable by the intended signed vertical geometry in train/dev/heldout.",
            "- The grouped runner's `numeric_value(..., 'center_delta_z')` lookup collides with `raw_geometry_feature_available_mask.center_delta_z` and returns `1.0` instead of the actual z difference.",
            "- As a result, `C.sign_x_center_delta_z` becomes effectively predicate sign only, not predicate-conditioned geometry.",
            "- `M3_T_plus_G_concat` cannot solve this route because raw `G_e` is predicate-independent and `higher than` / `lower than` require sign-conditioned interpretation.",
            "- Therefore, `relative_vertical` should not be dropped yet. The next step is to repair the grouped runner's compatibility feature extraction and rerun evaluation.",
            "",
            "## Boundary",
            "",
            "- No official validation/test used.",
            "- No paper-level metric produced.",
            "- No `p_obs` / `p_rel` claim enabled.",
            "- H001 artifacts remain untouched.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    review_errors = read_jsonl(args.review_dir / "validation_errors.jsonl")
    eval_errors = read_jsonl(args.eval_dir / "validation_errors.jsonl")
    split_rows = read_jsonl(args.split_dir / "model_safe_split_view.jsonl")
    route_metrics = read_csv(args.eval_dir / "route_metrics.csv")

    validation_errors = validate_inputs(review_summary, split_rows, route_metrics, review_errors, eval_errors)
    probes = split_feature_probe(split_rows, route_metrics)
    collisions = collision_summary(split_rows)

    collision_count = sum(1 for item in collisions if item["is_collision"])
    harmful_collision_count = sum(1 for item in collisions if item["is_harmful_collision"])
    heldout_all = next(
        item
        for item in probes
        if item["protocol_split"] == "internal_heldout" and item["predicate_label"] == "ALL"
    )
    if heldout_all["oracle_auc_signed_center_delta_z"] != 1.0:
        validation_errors.append(
            {
                "error_type": "unexpected_oracle_vertical_auc",
                "actual": heldout_all["oracle_auc_signed_center_delta_z"],
            }
        )
    if harmful_collision_count == 0:
        validation_errors.append({"error_type": "expected_harmful_feature_suffix_collision_not_detected"})

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_failure_analysis_inputs",
        "next_todo": NEXT_TODO if not validation_errors else "fix_relative_vertical_failure_analysis_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "model_safe_split_view": rel_path(args.split_dir / "model_safe_split_view.jsonl"),
            "route_metrics": rel_path(args.eval_dir / "route_metrics.csv"),
        },
        "boundary": {
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "diagnosis": {
            "primary_failure_cause": "compatibility_feature_extractor_suffix_collision",
            "relative_vertical_intrinsic_failure": False,
            "target_separable_by_intended_signed_vertical_geometry": True,
            "heldout_oracle_signed_center_delta_z_auroc": heldout_all["oracle_auc_signed_center_delta_z"],
            "heldout_runner_suffix_center_delta_z_auroc": heldout_all["runner_candidate_auc_suffix_center_delta_z"],
            "feature_collision_count": collision_count,
            "harmful_feature_collision_count": harmful_collision_count,
        },
        "next_required_action": "repair grouped runner to select explicit raw geometry feature paths before rerunning grouped eval",
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_csv(args.output_dir / "feature_probe.csv", probes)
    write_csv(args.output_dir / "feature_collision_audit.csv", collisions)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_report(args.output_dir / "report.md", summary=summary, probes=probes, collisions=collisions)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
