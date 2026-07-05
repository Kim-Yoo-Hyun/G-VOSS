#!/usr/bin/env python3
"""Validate H002 grouped split protocol output and write stage artifact."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_AUDIT_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization"
)
DEFAULT_SPLIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/splits/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit"
)

EXPECTED_SCHEMA_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_ready"
)
EXPECTED_SCHEMA_AUDIT_NEXT = "compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit"
EXPECTED_SPLIT_SCHEMA = "h002_grouped_split_v1"
EXPECTED_ROW_COUNT = 6952
EXPECTED_GROUP_COUNT = 3684
SPLIT_RATIOS = {"internal_train": 0.70, "internal_dev": 0.15, "internal_heldout": 0.15}

SCHEMA_VERSION = "h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_v1"
STATUS_READY = "h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_input_errors"
SELECTED_PATH = "grouped_split_ready_select_grouped_eval_protocol"
NEXT_TODO = "compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-audit-stage-dir", type=Path, default=DEFAULT_SCHEMA_AUDIT_STAGE_DIR)
    parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
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
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(schema_stage: dict[str, Any], split_manifest: dict[str, Any], split_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if schema_stage.get("status") != EXPECTED_SCHEMA_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_schema_audit_stage_status", "actual": schema_stage.get("status")})
    if schema_stage.get("next_todo") != EXPECTED_SCHEMA_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_schema_audit_stage_next_todo", "actual": schema_stage.get("next_todo")})
    if int(schema_stage.get("validation_errors", 0) or 0) != 0:
        errors.append({"error_type": "schema_audit_stage_validation_errors", "actual": schema_stage.get("validation_errors")})

    required = [
        "split_manifest.json",
        "model_safe_split_view.jsonl",
        "split_assignments.jsonl",
        "group_manifest.jsonl",
        "route_split_counts.csv",
        "predicate_split_counts.csv",
        "leakage_audit.csv",
        "validation_errors.jsonl",
    ]
    for name in required:
        if not (split_dir / name).exists():
            errors.append({"error_type": "missing_split_file", "file": name})
    if errors:
        return errors

    if split_manifest.get("schema_version") != EXPECTED_SPLIT_SCHEMA:
        errors.append({"error_type": "unexpected_split_schema", "actual": split_manifest.get("schema_version")})
    if split_manifest.get("status") != "ready":
        errors.append({"error_type": "split_manifest_not_ready", "actual": split_manifest.get("status")})
    if split_manifest.get("official_validation_or_test") is not False:
        errors.append({"error_type": "official_validation_or_test_not_false", "actual": split_manifest.get("official_validation_or_test")})
    boundary = split_manifest.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_metric_run", "official_validation_usage", "official_test_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "split_boundary_not_false", "key": key, "actual": boundary.get(key)})

    row_counts = split_manifest.get("row_counts", {})
    if row_counts.get("input_model_safe_rows") != EXPECTED_ROW_COUNT or row_counts.get("model_safe_split_view") != EXPECTED_ROW_COUNT:
        errors.append({"error_type": "unexpected_split_row_count", "row_counts": row_counts})
    if row_counts.get("split_assignments") != EXPECTED_GROUP_COUNT or row_counts.get("group_manifest") != EXPECTED_GROUP_COUNT:
        errors.append({"error_type": "unexpected_split_group_count", "row_counts": row_counts})
    if row_counts.get("validation_errors") != 0:
        errors.append({"error_type": "split_validation_errors", "actual": row_counts.get("validation_errors")})
    if (split_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "split_validation_error_rows_present"})

    leakage = read_csv(split_dir / "leakage_audit.csv")
    for row in leakage:
        if row.get("status") != "pass" or row.get("violations") not in {"0", 0}:
            errors.append({"error_type": "leakage_audit_failed", "row": row})

    split_rows = read_jsonl(split_dir / "model_safe_split_view.jsonl")
    group_to_split: dict[str, set[str]] = defaultdict(set)
    for row in split_rows:
        group_to_split[row["cv_group_id"]].add(row["protocol_split"])
        if row.get("split_policy", {}).get("official_validation_or_test") is not False:
            errors.append({"error_type": "row_split_policy_not_internal", "unified_row_id": row.get("unified_row_id")})
            break
    leaked = [group for group, splits in group_to_split.items() if len(splits) > 1]
    if leaked:
        errors.append({"error_type": "cv_group_split_leakage", "count": len(leaked), "examples": leaked[:5]})

    route_rows = read_csv(split_dir / "route_split_counts.csv")
    seen_route_split = {(row["route_family"], row["protocol_split"]) for row in route_rows}
    families = sorted({row["route_family"] for row in route_rows})
    for family in families:
        total = sum(int(row["rows"]) for row in route_rows if row["route_family"] == family)
        for split, ratio in SPLIT_RATIOS.items():
            matching = [row for row in route_rows if row["route_family"] == family and row["protocol_split"] == split]
            if not matching:
                errors.append({"error_type": "missing_family_split_row", "family": family, "split": split})
                continue
            row = matching[0]
            rows = int(row["rows"])
            actual_ratio = rows / total if total else 0.0
            if abs(actual_ratio - ratio) > 0.03:
                errors.append({"error_type": "split_ratio_out_of_tolerance", "family": family, "split": split, "actual_ratio": actual_ratio, "target_ratio": ratio})
            if int(row["label_0"]) == 0 or int(row["label_1"]) == 0:
                errors.append({"error_type": "missing_label_in_family_split", "family": family, "split": split, "row": row})
    if len(seen_route_split) != len(families) * len(SPLIT_RATIOS):
        errors.append({"error_type": "unexpected_route_split_grid_size", "actual": len(seen_route_split), "families": families})
    return errors


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "define grouped evaluation model views and controls before running metrics",
            "evaluate only on internal_dev/internal_heldout from the H002 candidate pool",
            "report semantic-only, geometry-only, T+G concat, T x G compatibility, wrong-T, and shuffled-G",
            "keep official validation/test and paper-level wording blocked until external protocol exists",
        ],
        "must_not_do": [
            "call internal_heldout official validation or official test",
            "use cv_group_id/source_artifact as model features",
            "enable Q_e/Z_e in C_e without an explicit protocol change",
            "promote support_contact as fully solved based only on grouped evaluation",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Grouped Split Protocol",
        "",
        "## Verdict",
        "",
        "Grouped split protocol passed over the internal H002 candidate pool. The split uses `cv_group_id`, keeps all rows from the same group in one split, and does not use official validation/test.",
        "",
        "## Route Split Counts",
        "",
        "| Route family | Split | Rows | Label 0 | Label 1 | CV groups |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["route_split_counts"]:
        lines.append(
            f"| `{row['route_family']}` | `{row['protocol_split']}` | {row['rows']} | {row['label_0']} | {row['label_1']} | {row['cv_groups']} |"
        )
    lines.extend(["", "## Boundary", ""])
    for key, value in payload["boundary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    schema_stage = read_json(args.schema_audit_stage_dir / "summary.json")
    split_manifest = read_json(args.split_dir / "split_manifest.json")
    errors = validate_inputs(schema_stage, split_manifest, args.split_dir)
    route_rows = read_csv(args.split_dir / "route_split_counts.csv")
    predicate_rows = read_csv(args.split_dir / "predicate_split_counts.csv")
    leakage_rows = read_csv(args.split_dir / "leakage_audit.csv")

    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_grouped_split_protocol_errors",
        "next_todo": NEXT_TODO if not errors else EXPECTED_SCHEMA_AUDIT_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "input_artifacts": {
            "schema_audit_stage": rel_path(args.schema_audit_stage_dir),
            "split_runtime": rel_path(args.split_dir),
        },
        "runtime_outputs": {
            "split_manifest": rel_path(args.split_dir / "split_manifest.json"),
            "model_safe_split_view": rel_path(args.split_dir / "model_safe_split_view.jsonl"),
            "split_assignments": rel_path(args.split_dir / "split_assignments.jsonl"),
            "group_manifest": rel_path(args.split_dir / "group_manifest.jsonl"),
            "route_split_counts": rel_path(args.split_dir / "route_split_counts.csv"),
            "predicate_split_counts": rel_path(args.split_dir / "predicate_split_counts.csv"),
            "leakage_audit": rel_path(args.split_dir / "leakage_audit.csv"),
        },
        "row_counts": split_manifest.get("row_counts", {}),
        "split_ratios": split_manifest.get("split_ratios", {}),
        "route_split_counts": route_rows,
        "predicate_split_counts": predicate_rows,
        "leakage_audit": leakage_rows,
        "boundary": {
            "grouped_split_created": not errors,
            "paper_metric_produced": False,
            "grouped_holdout_metric_run": False,
            "official_validation_usage": False,
            "official_test_usage": False,
            "h001_artifacts_modified": False,
        },
        "next_step_contract": next_contract(),
    }

    write_csv(args.output_dir / "route_split_counts.csv", route_rows)
    write_csv(args.output_dir / "predicate_split_counts.csv", predicate_rows)
    write_csv(args.output_dir / "leakage_audit.csv", leakage_rows)
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
