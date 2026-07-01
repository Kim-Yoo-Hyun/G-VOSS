#!/usr/bin/env python3
"""Audit H002 materialized model-safe rows for schema leakage and shortcut risk."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_materialization_schema_audit_v1"
EXPECTED_INPUT_SCHEMA = "h002_route_materialization_v1"

CE_ALLOWED_BLOCKS = ["T_e", "G_e"]
CE_BLOCKED_BLOCKS = ["Z_e", "Q_e", "extra_safe_blocks"]
EXPECTED_FAMILIES = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}

BLOCKED_CE_PATH_TOKENS = {
    "anchor_compatibility_state",
    "candidate_component",
    "candidate_role",
    "class_pair",
    "control",
    "direction_by_vote",
    "direction_by_volume",
    "directed_pair_key",
    "directed_pair_predicate_key",
    "geometry_status",
    "gt_compatible",
    "is_original_gt_anchor",
    "label_match_status",
    "machine_hint",
    "matched_gt",
    "matched_predicates",
    "p_geom_valid",
    "prediction_id",
    "queue_kind",
    "rank_band",
    "scan_id",
    "selected_frame_compatible",
    "semantic_rank",
    "semantic_score",
    "source_id",
    "source_line",
    "stratum_id",
    "subgraph_id",
    "target_pool",
    "target_role",
    "volume_ratio_band",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def flatten_paths(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_paths(child, child_prefix)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            child_prefix = f"{prefix}[{idx}]"
            yield from flatten_paths(child, child_prefix)
    else:
        yield prefix, value


def get_block(row: dict[str, Any], block_name: str) -> dict[str, Any]:
    blocks = row.get("feature_blocks", {})
    block = blocks.get(block_name, {})
    return block if isinstance(block, dict) else {}


def normalize_text(value: Any) -> str:
    if value is None:
        return "__MISSING__"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def categorical_value(row: dict[str, Any], probe: str) -> str:
    te = get_block(row, "T_e")
    if probe == "route_family":
        return normalize_text(row.get("route_family"))
    if probe == "predicate_label":
        return normalize_text(row.get("predicate_label"))
    if probe == "T_predicate":
        return normalize_text(te.get("predicate_label") or te.get("predicate_text"))
    if probe == "T_relation_family":
        return normalize_text(te.get("relation_family") or te.get("predicate_family"))
    if probe == "T_subject_class":
        return normalize_text(te.get("subject_class_label") or te.get("subject_class_text"))
    if probe == "T_object_class":
        return normalize_text(te.get("object_class_label") or te.get("object_class_text"))
    if probe == "T_class_pair":
        s = normalize_text(te.get("subject_class_label") or te.get("subject_class_text"))
        o = normalize_text(te.get("object_class_label") or te.get("object_class_text"))
        return f"{s}::{o}"
    if probe == "T_predicate_class_pair":
        return f"{categorical_value(row, 'T_predicate')}::{categorical_value(row, 'T_class_pair')}"
    if probe == "cv_group_id_metadata_only":
        return normalize_text(row.get("cv_group_id"))
    if probe == "source_artifact_metadata_only":
        return normalize_text(row.get("source_artifact"))
    raise KeyError(probe)


def majority_probe(rows: list[dict[str, Any]], probe: str, family: str | None = None) -> dict[str, Any]:
    selected = [row for row in rows if family is None or row.get("route_family") == family]
    value_labels: dict[str, Counter[int]] = defaultdict(Counter)
    for row in selected:
        value_labels[categorical_value(row, probe)][int(row["target_y"])] += 1
    correct = sum(max(counts.values()) for counts in value_labels.values())
    total = len(selected)
    acc = correct / total if total else 0.0
    pure_values = sum(1 for counts in value_labels.values() if len(counts) == 1)
    values = len(value_labels)
    max_bucket = max((sum(counts.values()) for counts in value_labels.values()), default=0)
    risk = "high" if total >= 100 and acc >= 0.95 else "medium" if total >= 100 and acc >= 0.80 else "low"
    return {
        "family": family or "ALL",
        "probe": probe,
        "rows": total,
        "unique_values": values,
        "max_bucket_rows": max_bucket,
        "pure_value_count": pure_values,
        "majority_accuracy": round(acc, 6),
        "risk": risk,
        "model_input_scope": "C_e_allowed" if probe.startswith("T_") else "metadata_only",
    }


def audit_schema(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    schema_errors: list[dict[str, Any]] = []
    blocked_hits: list[dict[str, Any]] = []
    block_presence_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    label_counts: Counter[tuple[str, int]] = Counter()
    family_counts: Counter[str] = Counter()

    for row in rows:
        row_id = row.get("unified_row_id")
        family = row.get("route_family")
        family_counts[family] += 1
        label_counts[(family, int(row.get("target_y", -1)))] += 1
        if row_id in seen_ids:
            schema_errors.append({"error_type": "duplicate_unified_row_id", "unified_row_id": row_id})
        seen_ids.add(row_id)
        if row.get("schema_version") != EXPECTED_INPUT_SCHEMA:
            schema_errors.append({"error_type": "unexpected_schema_version", "unified_row_id": row_id, "actual": row.get("schema_version")})
        if row.get("protocol_split") != "unassigned_pre_grouped_holdout":
            schema_errors.append({"error_type": "unexpected_protocol_split", "unified_row_id": row_id, "actual": row.get("protocol_split")})
        if row.get("paper_metric_ready") is not False:
            schema_errors.append({"error_type": "paper_metric_ready_not_false", "unified_row_id": row_id, "actual": row.get("paper_metric_ready")})
        policy = row.get("feature_use_policy", {})
        if policy.get("C_e_allowed_blocks") != CE_ALLOWED_BLOCKS:
            schema_errors.append({"error_type": "invalid_C_e_allowed_blocks", "unified_row_id": row_id, "actual": policy.get("C_e_allowed_blocks")})
        if policy.get("C_e_blocked_blocks") != CE_BLOCKED_BLOCKS:
            schema_errors.append({"error_type": "invalid_C_e_blocked_blocks", "unified_row_id": row_id, "actual": policy.get("C_e_blocked_blocks")})
        blocks = row.get("feature_blocks", {})
        for required in ["T_e", "G_e", "Q_e", "Z_e", "extra_safe_blocks"]:
            if required not in blocks:
                schema_errors.append({"error_type": "missing_feature_block", "unified_row_id": row_id, "block": required})

        for allowed_block in CE_ALLOWED_BLOCKS:
            for path, value in flatten_paths(blocks.get(allowed_block, {}), f"feature_blocks.{allowed_block}"):
                lower_path = path.lower()
                matched = sorted(token for token in BLOCKED_CE_PATH_TOKENS if token in lower_path)
                if matched:
                    blocked_hits.append(
                        {
                            "unified_row_id": row_id,
                            "route_family": family,
                            "predicate_label": row.get("predicate_label"),
                            "path": path,
                            "matched_tokens": "|".join(matched),
                            "value_preview": normalize_text(value)[:160],
                        }
                    )

    for family in sorted(family_counts):
        block_presence = Counter()
        family_rows = [row for row in rows if row.get("route_family") == family]
        for row in family_rows:
            blocks = row.get("feature_blocks", {})
            for block in ["T_e", "G_e", "Q_e", "Z_e", "extra_safe_blocks"]:
                if blocks.get(block):
                    block_presence[block] += 1
        block_presence_rows.append(
            {
                "route_family": family,
                "rows": family_counts[family],
                "label_0": label_counts[(family, 0)],
                "label_1": label_counts[(family, 1)],
                "T_e_present": block_presence["T_e"],
                "G_e_present": block_presence["G_e"],
                "Q_e_present": block_presence["Q_e"],
                "Z_e_present": block_presence["Z_e"],
                "extra_safe_blocks_present": block_presence["extra_safe_blocks"],
            }
        )

    actual_families = set(family_counts)
    if actual_families != EXPECTED_FAMILIES:
        schema_errors.append({"error_type": "unexpected_family_set", "expected": sorted(EXPECTED_FAMILIES), "actual": sorted(actual_families)})
    for family in EXPECTED_FAMILIES:
        if label_counts[(family, 0)] == 0 or label_counts[(family, 1)] == 0:
            schema_errors.append({"error_type": "family_missing_binary_label", "family": family})

    return schema_errors, blocked_hits, block_presence_rows


def split_readiness(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for family in sorted({row["route_family"] for row in rows}):
        family_rows = [row for row in rows if row["route_family"] == family]
        group_labels: dict[str, Counter[int]] = defaultdict(Counter)
        for row in family_rows:
            group_labels[normalize_text(row.get("cv_group_id"))][int(row["target_y"])] += 1
        group_count = len(group_labels)
        mixed_groups = sum(1 for counts in group_labels.values() if counts[0] > 0 and counts[1] > 0)
        pure_0 = sum(1 for counts in group_labels.values() if counts[0] > 0 and counts[1] == 0)
        pure_1 = sum(1 for counts in group_labels.values() if counts[1] > 0 and counts[0] == 0)
        max_group_rows = max((sum(counts.values()) for counts in group_labels.values()), default=0)
        group_majority_acc = sum(max(counts.values()) for counts in group_labels.values()) / len(family_rows)
        ready = group_count >= 30 and min(pure_0 + mixed_groups, pure_1 + mixed_groups) >= 10
        output.append(
            {
                "route_family": family,
                "rows": len(family_rows),
                "cv_group_count": group_count,
                "mixed_label_group_count": mixed_groups,
                "pure_label_0_group_count": pure_0,
                "pure_label_1_group_count": pure_1,
                "max_group_rows": max_group_rows,
                "group_majority_accuracy_metadata_only": round(group_majority_acc, 6),
                "split_ready": str(ready),
            }
        )
    return output


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = args.materialization_dir
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    manifest = read_json(materialization_dir / "row_manifest.json")
    rows = read_jsonl(materialization_dir / "model_safe_view.jsonl")
    schema_errors, blocked_hits, block_presence_rows = audit_schema(rows)

    probes = [
        "route_family",
        "predicate_label",
        "T_predicate",
        "T_relation_family",
        "T_subject_class",
        "T_object_class",
        "T_class_pair",
        "T_predicate_class_pair",
        "cv_group_id_metadata_only",
        "source_artifact_metadata_only",
    ]
    shortcut_rows: list[dict[str, Any]] = []
    for probe in probes:
        shortcut_rows.append(majority_probe(rows, probe))
    for family in sorted({row["route_family"] for row in rows}):
        for probe in probes:
            shortcut_rows.append(majority_probe(rows, probe, family=family))

    split_rows = split_readiness(rows)
    hard_errors = len(schema_errors) + len(blocked_hits)
    high_shortcut_rows = [
        row
        for row in shortcut_rows
        if row["risk"] == "high" and row["model_input_scope"] == "C_e_allowed"
    ]
    status = "ready" if hard_errors == 0 else "errors"
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    audit_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": created_at,
        "input_manifest_status": manifest.get("status"),
        "input_schema_version": manifest.get("schema_version"),
        "row_count": len(rows),
        "boundary": {
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
            "runtime_output_root": repo_rel(repo_root, out),
        },
        "audit_counts": {
            "schema_error_count": len(schema_errors),
            "blocked_C_e_field_hit_count": len(blocked_hits),
            "shortcut_probe_count": len(shortcut_rows),
            "high_C_e_allowed_shortcut_warning_count": len(high_shortcut_rows),
            "split_readiness_family_count": len(split_rows),
        },
        "block_presence_table": block_presence_rows,
        "next_required_gate": "grouped_split_protocol" if hard_errors == 0 else "fix_materialization_schema",
    }

    write_json(out / "audit_manifest.json", audit_manifest)
    write_jsonl(out / "schema_violations.jsonl", schema_errors)
    write_jsonl(out / "blocked_field_hits.jsonl", blocked_hits)
    write_csv(out / "block_presence_table.csv", block_presence_rows)
    write_csv(out / "shortcut_risk_table.csv", shortcut_rows)
    write_csv(out / "split_readiness_table.csv", split_rows)
    write_jsonl(out / "high_shortcut_warnings.jsonl", high_shortcut_rows)
    print(json.dumps(audit_manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
