#!/usr/bin/env python3
"""Scan whether proximity/close-by can become the next H002 reliability target."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v9_predicate_rank_hint_controlled_path_decision_codex_proxy_user_requested"
DEFAULT_TRAIN_SUMMARY = RGA_ROOT / "train_rga_summary.json"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v10_proximity_relation_family_feasibility_scan"

EXPECTED_PATH_STATUS = "h002_reliability_target_v9_path_decision_select_proximity_v10"
NEXT_TODO = "reliability_target_v10_proximity_lh_only_path_decision"

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

PREVIEW_TARGET_PER_STRATUM = 80
PREVIEW_STRATA = ("exact_match", "pair_has_other_predicate", "no_gt_for_pair")
MAX_PER_SCAN = 4
MAX_PER_LABEL_PAIR = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--train-summary", type=Path, default=DEFAULT_TRAIN_SUMMARY)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
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
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stable_int(value: str) -> int:
    return int(stable_hash(value)[:12], 16)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    return {
        **row,
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "subject_object_label_pair": f"{subject_label}|{object_label}",
        "endpoint_cell": f"{endpoint_type(subject_label)}|{endpoint_type(object_label)}",
        "exact_endpoint_pair_key": f"{row.get('scan_id')}|{row.get('subgraph_id')}|{row.get('subject_id')}|{row.get('object_id')}",
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "generic_endpoint_pair": subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS,
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "semantic_score_norm_float": as_float(row.get("semantic_score_norm")),
        "p_geom_valid_float": as_float(row.get("p_geom_valid")),
    }


def validate_path_decision(path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": EXPECTED_PATH_STATUS, "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != "reliability_target_v10_proximity_relation_family_feasibility_scan":
        errors.append({"error_type": "unexpected_path_decision_next_todo", "actual": path_decision.get("next_todo")})
    boundary = path_decision.get("boundary", {})
    for key in ["validation_usage", "test_usage", "posterior_smoke_allowed", "trains_new_posterior", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "path_decision_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def read_proximity_queue_rows(hl_queue_path: Path, lh_queue_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    input_counts: dict[str, Any] = {
        "hl_queue_rows_read": 0,
        "lh_queue_rows_read": 0,
        "hl_proximity_rows": 0,
        "lh_proximity_rows": 0,
        "queue_proximity_rows": 0,
    }
    for queue_name, queue_path in [("hl", hl_queue_path), ("lh", lh_queue_path)]:
        for line_no, row in iter_jsonl(queue_path):
            input_counts[f"{queue_name}_queue_rows_read"] += 1
            if row.get("predicate_family") != "proximity" or norm(row.get("predicate_label")) != "close by":
                continue
            required = ["prediction_id", "scan_id", "subgraph_id", "subject_id", "subject_label", "object_id", "object_label"]
            missing = [field for field in required if field not in row]
            if missing:
                errors.append(
                    {
                        "error_type": "missing_required_field",
                        "queue": queue_name,
                        "line_no": line_no,
                        "missing": missing,
                        "prediction_id": row.get("prediction_id"),
                    }
                )
                continue
            enriched = enrich(row)
            enriched["source_queue_file"] = queue_path.name
            rows.append(enriched)
            input_counts[f"{queue_name}_proximity_rows"] += 1
            input_counts["queue_proximity_rows"] += 1
    return rows, input_counts, errors


def read_train_summary_family_counts(train_summary_path: Path) -> dict[str, Any]:
    summary = read_json(train_summary_path)
    family_tables = summary.get("family_tables", {})
    proximity_tables = {
        name: table.get("proximity", {})
        for name, table in family_tables.items()
        if isinstance(table, dict)
    }
    label_status = proximity_tables.get("label_status", {})
    return {
        "status": summary.get("status"),
        "validation_error_count": summary.get("validation", {}).get("validation_error_count"),
        "total_proximity_rows": int(sum(label_status.values())) if isinstance(label_status, dict) else 0,
        "geometry_status": proximity_tables.get("geometry_status", {}),
        "label_geometry_bucket": proximity_tables.get("label_geometry_bucket", {}),
        "label_match_status": label_status,
        "rga_top100": proximity_tables.get("rga_top100", {}),
    }


def counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def family_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counters = {
        "bucket_top100": Counter(row.get("bucket_top100") for row in rows),
        "bucket_top50": Counter(row.get("bucket_top50") for row in rows),
        "geometry_status": Counter(row.get("geometry_status") for row in rows),
        "label_geometry_bucket": Counter(row.get("label_geometry_bucket") for row in rows),
        "label_match_status": Counter(row.get("label_match_status") for row in rows),
        "rank_band": Counter(row.get("rank_band") for row in rows),
        "machine_hint": Counter(row.get("machine_hint") for row in rows),
        "scan_id": Counter(row.get("scan_id") for row in rows),
        "subject_object_label_pair": Counter(row.get("subject_object_label_pair") for row in rows),
        "endpoint_cell": Counter(row.get("endpoint_cell") for row in rows),
    }
    return {key: counter_dict(value) for key, value in counters.items()}


def majority_risk(rows: list[dict[str, Any]], predictor: str, label: str) -> dict[str, Any]:
    if not rows:
        return {
            "predictor": predictor,
            "label": label,
            "rows": 0,
            "majority_rule_accuracy": None,
            "majority_baseline_accuracy": None,
            "majority_excess_over_baseline": None,
            "risk_flag": False,
            "groups": 0,
            "top_groups": [],
        }
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(row.get(label, "missing"))] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    acc = correct / len(rows)
    top_groups = []
    for group_value, counter in groups.items():
        total = sum(counter.values())
        majority_label, majority_count = counter.most_common(1)[0]
        top_groups.append(
            {
                "group_value": group_value,
                "rows": total,
                "majority_label": majority_label,
                "majority_rate": majority_count / total,
                "label_counts": dict(counter),
            }
        )
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    return {
        "predictor": predictor,
        "label": label,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": acc,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": acc - baseline,
        "risk_flag": (acc >= 0.85 and acc - baseline >= 0.1) or any(item["rows"] >= 20 and item["majority_rate"] >= 0.95 for item in top_groups),
        "top_groups": top_groups[:12],
    }


def strict_lh_pool(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("bucket_top100") == "RGA-LH"
        and row.get("geometry_status") == "satisfied"
        and not row["structural_pair"]
        and not row["generic_endpoint_pair"]
        and row.get("label_match_status") in PREVIEW_STRATA
    ]


def preview_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["hard_room_surface_pair"],
        row["semantic_rank_int"],
        -row["p_geom_valid_float"],
        str(row.get("scan_id")),
        stable_int(str(row.get("prediction_id"))),
    )


def select_preview(pool: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pool:
        by_stratum[str(row.get("label_match_status"))].append(row)
    for rows in by_stratum.values():
        rows.sort(key=preview_sort_key)

    selected: list[dict[str, Any]] = []
    counters = {
        "scan": Counter(),
        "label_pair": Counter(),
        "endpoint_cell": Counter(),
    }
    used_prediction_ids: set[str] = set()
    stratum_selected = Counter()
    stratum_attempted = Counter()

    for stratum in PREVIEW_STRATA:
        for row in by_stratum.get(stratum, []):
            stratum_attempted[stratum] += 1
            if str(row.get("prediction_id")) in used_prediction_ids:
                continue
            scan = str(row.get("scan_id"))
            label_pair = str(row.get("subject_object_label_pair"))
            endpoint_cell = str(row.get("endpoint_cell"))
            if counters["scan"][scan] >= MAX_PER_SCAN:
                continue
            if counters["label_pair"][label_pair] >= MAX_PER_LABEL_PAIR:
                continue
            selected.append(row)
            used_prediction_ids.add(str(row.get("prediction_id")))
            counters["scan"][scan] += 1
            counters["label_pair"][label_pair] += 1
            counters["endpoint_cell"][endpoint_cell] += 1
            stratum_selected[stratum] += 1
            if stratum_selected[stratum] >= PREVIEW_TARGET_PER_STRATUM:
                break

    cap_summary = {
        "selected_rows": len(selected),
        "selected_by_label_match_status": dict(stratum_selected),
        "attempted_by_label_match_status": dict(stratum_attempted),
        "unique_scans": len(counters["scan"]),
        "unique_label_pairs": len(counters["label_pair"]),
        "unique_endpoint_cells": len(counters["endpoint_cell"]),
        "max_rows_per_scan": max(counters["scan"].values() or [0]),
        "max_rows_per_label_pair": max(counters["label_pair"].values() or [0]),
        "max_rows_per_endpoint_cell": max(counters["endpoint_cell"].values() or [0]),
        "scan_cap": MAX_PER_SCAN,
        "label_pair_cap": MAX_PER_LABEL_PAIR,
        "endpoint_cell_cap": None,
        "endpoint_cell_cap_disabled_reason": "strict proximity pool already excludes structural/generic endpoints; capping object|object would suppress usable object-object proximity rows",
    }
    return selected, cap_summary


def preview_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_v10_proximity_feasibility_preview_v1",
        "blind_review_id": "ftv10p_" + stable_hash(str(row.get("prediction_id")))[:12],
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "review_prompt": "Is this close-by relation meaningful and reliable for the shown subject-object pair, rather than dense proximity noise or a trivial room/structure relation?",
        "source_queue_hidden": row.get("bucket_top100"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "machine_hint_hidden": row.get("machine_hint"),
        "rank_band_hidden": row.get("rank_band"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair"),
        "endpoint_cell_hidden": row.get("endpoint_cell"),
        "exact_endpoint_pair_key_hidden": row.get("exact_endpoint_pair_key"),
        "structural_pair_hidden": row.get("structural_pair"),
        "hard_room_surface_pair_hidden": row.get("hard_room_surface_pair"),
        "generic_endpoint_pair_hidden": row.get("generic_endpoint_pair"),
        "label_fill_allowed": False,
        "posterior_input_allowed": False,
    }


def gate_summary(
    rows: list[dict[str, Any]],
    strict_pool: list[dict[str, Any]],
    preview: list[dict[str, Any]],
    summary_family_counts: dict[str, Any],
) -> dict[str, Any]:
    bucket = Counter(str(row.get("bucket_top100")) for row in rows)
    full_bucket = summary_family_counts.get("rga_top100", {}) or {}
    total_proximity_rows = int(summary_family_counts.get("total_proximity_rows") or len(rows))
    label_counts = Counter(str(row.get("label_match_status")) for row in strict_pool)
    preview_counts = Counter(str(row.get("label_match_status")) for row in preview)
    return {
        "total_proximity_rows_gate": {
            "value": total_proximity_rows,
            "queue_value": len(rows),
            "threshold": 10000,
            "pass": total_proximity_rows >= 10000,
        },
        "bidirectional_hl_lh_gate": {
            "hl_rows": int(full_bucket.get("RGA-HL", bucket.get("RGA-HL", 0)) or 0),
            "lh_rows": int(full_bucket.get("RGA-LH", bucket.get("RGA-LH", 0)) or 0),
            "threshold_per_side": 50,
            "pass": int(full_bucket.get("RGA-HL", bucket.get("RGA-HL", 0)) or 0) >= 50
            and int(full_bucket.get("RGA-LH", bucket.get("RGA-LH", 0)) or 0) >= 50,
        },
        "lh_pool_gate": {
            "value": len(strict_pool),
            "threshold": 160,
            "pass": len(strict_pool) >= 160,
        },
        "label_status_variety_gate": {
            "label_counts": dict(label_counts),
            "required": list(PREVIEW_STRATA),
            "pass": all(label_counts.get(name, 0) >= PREVIEW_TARGET_PER_STRATUM for name in PREVIEW_STRATA),
        },
        "preview_capacity_gate": {
            "value": len(preview),
            "threshold": PREVIEW_TARGET_PER_STRATUM * len(PREVIEW_STRATA),
            "preview_counts": dict(preview_counts),
            "pass": len(preview) >= PREVIEW_TARGET_PER_STRATUM * len(PREVIEW_STRATA),
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    gates = summary["feasibility_gates"]
    counts = summary["counts"]
    summary_counts = summary["train_summary_proximity_counts"]

    def fmt_float(value: Any) -> str:
        return "NA" if value is None else f"{value:.4f}"

    lines = [
        "# H002 V10 Proximity Feasibility Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Core Finding",
        "",
        "- `close by` / proximity has a large train-only candidate pool.",
        "- However, proximity is not a bidirectional HL/LH target in the current RGA queues.",
        "- It is viable only as an LH-only underconfidence/dense-noise feasibility branch unless another source of high-semantic/low-geometry proximity rows is constructed.",
        "",
        "## Gates",
        "",
        "```text",
        f"total_proximity_rows = {gates['total_proximity_rows_gate']['value']}",
        f"queue_proximity_rows = {gates['total_proximity_rows_gate']['queue_value']}",
        f"RGA-HL proximity rows = {gates['bidirectional_hl_lh_gate']['hl_rows']}",
        f"RGA-LH proximity rows = {gates['bidirectional_hl_lh_gate']['lh_rows']}",
        f"strict_lh_pool_rows = {gates['lh_pool_gate']['value']}",
        f"preview_rows = {gates['preview_capacity_gate']['value']}",
        f"bidirectional_hl_lh_gate = {gates['bidirectional_hl_lh_gate']['pass']}",
        f"lh_pool_gate = {gates['lh_pool_gate']['pass']}",
        "```",
        "",
        "## Main Counts",
        "",
        f"- full train proximity rga_top100: `{summary_counts['rga_top100']}`",
        f"- full train proximity geometry_status: `{summary_counts['geometry_status']}`",
        f"- full train proximity label_match_status: `{summary_counts['label_match_status']}`",
        f"- bucket_top100: `{counts['bucket_top100']}`",
        f"- geometry_status: `{counts['geometry_status']}`",
        f"- label_match_status: `{counts['label_match_status']}`",
        f"- rank_band: `{counts['rank_band']}`",
        f"- machine_hint: `{counts['machine_hint']}`",
        "",
        "## Shortcut Risks",
        "",
        "| Predictor | Label | Rows | Majority Acc | Baseline | Risk |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for risk in summary["shortcut_risks"]:
        acc = risk["majority_rule_accuracy"]
        base = risk["majority_baseline_accuracy"]
        lines.append(
            f"| `{risk['predictor']}` | `{risk['label']}` | {risk['rows']} | "
            f"{fmt_float(acc)} | {fmt_float(base)} | `{risk['risk_flag']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Selected next TODO: `{summary['next_todo']}`",
            "",
            "Posterior smoke remains blocked. Label fill also remains blocked until a path decision accepts LH-only proximity as a scoped target.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision_dir = as_abs(args.path_decision_dir)
    train_summary_path = as_abs(args.train_summary)
    hl_queue_path = as_abs(args.hl_queue)
    lh_queue_path = as_abs(args.lh_queue)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(path_decision_dir / "summary.json")
    validation_errors = validate_path_decision(path_decision)
    summary_family_counts = read_train_summary_family_counts(train_summary_path)
    rows, input_counts, read_errors = read_proximity_queue_rows(hl_queue_path, lh_queue_path)
    validation_errors.extend(read_errors[:100])

    counts = family_counts(rows)
    strict_pool = strict_lh_pool(rows)
    selected_preview, cap_summary = select_preview(strict_pool)
    preview_rows = [preview_row(row) for row in selected_preview]
    gates = gate_summary(rows, strict_pool, selected_preview, summary_family_counts)

    shortcut_risks = [
        majority_risk(strict_pool, "rank_band", "label_match_status"),
        majority_risk(strict_pool, "machine_hint", "label_match_status"),
        majority_risk(strict_pool, "subject_object_label_pair", "label_match_status"),
        majority_risk(strict_pool, "endpoint_cell", "label_match_status"),
        majority_risk(strict_pool, "scan_id", "label_match_status"),
    ]

    status = (
        "h002_reliability_target_v10_proximity_feasibility_lh_only_ready_not_bidirectional"
        if not validation_errors and gates["lh_pool_gate"]["pass"] and gates["preview_capacity_gate"]["pass"]
        else "h002_reliability_target_v10_proximity_feasibility_blocked"
    )
    decision = (
        "Proximity is feasible as a train-only LH-only diagnostic branch, but it is not feasible as a bidirectional semantic-geometry mismatch target because current RGA queues contain no proximity RGA-HL rows."
        if status.endswith("not_bidirectional")
        else "Proximity feasibility is blocked; inspect validation errors and capacity gates before continuing."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "feasibility_counts": output_dir / "feasibility_counts.csv",
        "shortcut_risks": output_dir / "shortcut_risks.json",
        "preview_candidates": output_dir / "preview_candidates.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v10_proximity_feasibility_scan_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "input_paths": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
            "train_summary": rel_path(train_summary_path),
            "hl_queue": rel_path(hl_queue_path),
            "lh_queue": rel_path(lh_queue_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "input_counts": input_counts,
        "train_summary_proximity_counts": summary_family_counts,
        "counts": counts,
        "strict_lh_pool": {
            "rows": len(strict_pool),
            "structural_pair_excluded": sum(1 for row in rows if row.get("bucket_top100") == "RGA-LH" and row.get("geometry_status") == "satisfied" and row["structural_pair"]),
            "generic_pair_excluded": sum(1 for row in rows if row.get("bucket_top100") == "RGA-LH" and row.get("geometry_status") == "satisfied" and row["generic_endpoint_pair"]),
        },
        "feasibility_gates": gates,
        "preview_selection": cap_summary,
        "shortcut_risks": shortcut_risks,
        "next_todo": NEXT_TODO,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "label_fill_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "proximity_rows_mixed_into_v8_v9_target": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["shortcut_risks"], shortcut_risks)
    write_jsonl(output_paths["preview_candidates"], preview_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(
        output_paths["feasibility_counts"],
        [
            {"category": category, "value": key, "count": count}
            for category, counter in counts.items()
            for key, count in counter.items()
        ],
    )
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"total_proximity_rows={summary['feasibility_gates']['total_proximity_rows_gate']['value']}")
    print(f"hl_rows={summary['feasibility_gates']['bidirectional_hl_lh_gate']['hl_rows']}")
    print(f"lh_rows={summary['feasibility_gates']['bidirectional_hl_lh_gate']['lh_rows']}")
    print(f"preview_rows={summary['feasibility_gates']['preview_capacity_gate']['value']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
