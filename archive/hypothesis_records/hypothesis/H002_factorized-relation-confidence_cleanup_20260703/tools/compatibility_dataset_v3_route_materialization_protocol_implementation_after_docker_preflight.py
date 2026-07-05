#!/usr/bin/env python3
"""Validate H002 Docker route materialization output and write stage artifact."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PREFLIGHT_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton"
)
DEFAULT_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/materialization/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight"
)

EXPECTED_PREFLIGHT_STATUS = (
    "h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_ready"
)
EXPECTED_PREFLIGHT_NEXT = "compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight"
EXPECTED_MATERIALIZATION_SCHEMA = "h002_route_materialization_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_input_errors"
SELECTED_PATH = "docker_materialized_promoted_routes_select_materialization_schema_shortcut_audit"
NEXT_TODO = "compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization"

EXPECTED_FAMILIES = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}
EXPECTED_PREDICATES = {
    "relative_vertical": {"higher than", "lower than"},
    "size_relative": {"bigger than", "smaller than"},
    "relative_horizontal": {"left", "right", "front", "behind"},
    "support_contact": {"standing on", "lying on"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-stage-dir", type=Path, default=DEFAULT_PREFLIGHT_STAGE_DIR)
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
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


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


def validate_preflight(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PREFLIGHT_STATUS:
        errors.append(
            {
                "error_type": "unexpected_preflight_stage_status",
                "expected": EXPECTED_PREFLIGHT_STATUS,
                "actual": summary.get("status"),
            }
        )
    if summary.get("next_todo") != EXPECTED_PREFLIGHT_NEXT:
        errors.append(
            {
                "error_type": "unexpected_preflight_stage_next_todo",
                "expected": EXPECTED_PREFLIGHT_NEXT,
                "actual": summary.get("next_todo"),
            }
        )
    if int(summary.get("validation_errors", 0) or 0) != 0:
        errors.append({"error_type": "preflight_stage_validation_errors", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_run", "official_validation_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "preflight_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def validate_materialization(materialization_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required_files = {
        "route_rows": materialization_dir / "route_rows.jsonl",
        "model_safe_view": materialization_dir / "model_safe_view.jsonl",
        "hidden_manifest": materialization_dir / "hidden_manifest.jsonl",
        "row_manifest": materialization_dir / "row_manifest.json",
        "validation_errors": materialization_dir / "validation_errors.jsonl",
    }
    file_rows: list[dict[str, Any]] = []
    for name, path in required_files.items():
        exists = path.exists()
        count = line_count(path) if exists and path.suffix == ".jsonl" else ""
        file_rows.append({"name": name, "path": rel_path(path), "exists": str(exists), "line_count": count})
        if not exists:
            errors.append({"error_type": "missing_materialization_file", "name": name, "path": str(path)})
    if errors:
        return errors, {"files": file_rows}

    if manifest.get("schema_version") != EXPECTED_MATERIALIZATION_SCHEMA:
        errors.append(
            {
                "error_type": "unexpected_materialization_schema",
                "expected": EXPECTED_MATERIALIZATION_SCHEMA,
                "actual": manifest.get("schema_version"),
            }
        )
    if manifest.get("status") != "ready":
        errors.append({"error_type": "materialization_not_ready", "actual": manifest.get("status")})
    if manifest.get("row_counts", {}).get("validation_errors") != 0:
        errors.append(
            {
                "error_type": "materialization_validation_errors",
                "actual": manifest.get("row_counts", {}).get("validation_errors"),
            }
        )
    if (materialization_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "materialization_validation_error_rows_present"})

    route_rows = read_jsonl(materialization_dir / "route_rows.jsonl")
    model_rows = read_jsonl(materialization_dir / "model_safe_view.jsonl")
    hidden_rows = read_jsonl(materialization_dir / "hidden_manifest.jsonl")
    counts = {
        "route_rows": len(route_rows),
        "model_safe_view": len(model_rows),
        "hidden_manifest": len(hidden_rows),
    }
    if len(set(counts.values())) != 1:
        errors.append({"error_type": "row_count_mismatch", "counts": counts})

    route_ids = {row.get("unified_row_id") for row in route_rows}
    model_ids = {row.get("unified_row_id") for row in model_rows}
    hidden_ids = {row.get("unified_row_id") for row in hidden_rows}
    if route_ids != model_ids or route_ids != hidden_ids:
        errors.append(
            {
                "error_type": "unified_row_id_set_mismatch",
                "route_only": len(route_ids - model_ids - hidden_ids),
                "model_only": len(model_ids - route_ids - hidden_ids),
                "hidden_only": len(hidden_ids - route_ids - model_ids),
            }
        )

    family_counts = Counter(row["route_family"] for row in route_rows)
    predicate_counts: Counter[tuple[str, str]] = Counter((row["route_family"], row["predicate_label"]) for row in route_rows)
    label_counts: Counter[tuple[str, int]] = Counter((row["route_family"], int(row["target_y"])) for row in route_rows)

    actual_families = set(family_counts)
    if actual_families != EXPECTED_FAMILIES:
        errors.append({"error_type": "unexpected_route_families", "expected": sorted(EXPECTED_FAMILIES), "actual": sorted(actual_families)})
    for family in EXPECTED_FAMILIES:
        predicates = {predicate for fam, predicate in predicate_counts if fam == family}
        if predicates != EXPECTED_PREDICATES[family]:
            errors.append(
                {
                    "error_type": "unexpected_predicate_set",
                    "family": family,
                    "expected": sorted(EXPECTED_PREDICATES[family]),
                    "actual": sorted(predicates),
                }
            )
        if label_counts[(family, 0)] == 0 or label_counts[(family, 1)] == 0:
            errors.append(
                {
                    "error_type": "family_missing_binary_class",
                    "family": family,
                    "label_0": label_counts[(family, 0)],
                    "label_1": label_counts[(family, 1)],
                }
            )

    for row in model_rows[:]:
        if row.get("protocol_split") != "unassigned_pre_grouped_holdout":
            errors.append({"error_type": "unexpected_protocol_split", "row_id": row.get("unified_row_id"), "actual": row.get("protocol_split")})
            break
        policy = row.get("feature_use_policy", {})
        if policy.get("C_e_allowed_blocks") != ["T_e", "G_e"]:
            errors.append({"error_type": "invalid_C_e_allowed_blocks", "row_id": row.get("unified_row_id"), "actual": policy.get("C_e_allowed_blocks")})
            break
        blocks = row.get("feature_blocks", {})
        if not blocks.get("T_e") or not blocks.get("G_e"):
            errors.append({"error_type": "missing_T_or_G_block", "row_id": row.get("unified_row_id")})
            break

    boundary = manifest.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_run", "official_validation_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "materialization_boundary_not_false", "key": key, "actual": boundary.get(key)})

    route_count_rows = [
        {
            "route_family": family,
            "row_count": family_counts[family],
            "label_0": label_counts[(family, 0)],
            "label_1": label_counts[(family, 1)],
        }
        for family in sorted(family_counts)
    ]
    predicate_count_rows = [
        {"route_family": family, "predicate_label": predicate, "row_count": count}
        for (family, predicate), count in sorted(predicate_counts.items())
    ]
    details = {
        "files": file_rows,
        "counts": counts,
        "route_count_rows": route_count_rows,
        "predicate_count_rows": predicate_count_rows,
    }
    return errors, details


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "audit model_safe_view for blocked construction/source/hidden leakage",
            "check family/predicate/target shortcut risks before grouped metrics",
            "create grouped split only after schema audit passes",
            "keep C_e model input restricted to T_e and G_e unless a later protocol changes it",
        ],
        "must_not_do": [
            "treat materialization counts as performance metrics",
            "run official validation/test claims from this candidate-pool split",
            "move row-level JSONL dumps into results/",
            "train p_rel or p_obs before Q_e/Z_e usage policy is locked",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Route Materialization Protocol Implementation",
        "",
        "## Verdict",
        "",
        "Docker route materialization passed. This stage produced row-level protocol artifacts only; it did not run grouped evaluation or paper metrics.",
        "",
        "## Counts",
        "",
        "| Route family | Rows | Label 0 | Label 1 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in payload["route_count_table"]:
        lines.append(f"| `{row['route_family']}` | {row['row_count']} | {row['label_0']} | {row['label_1']} |")
    lines.extend(
        [
            "",
            "## Predicates",
            "",
            "| Route family | Predicate | Rows |",
            "| --- | --- | ---: |",
        ]
    )
    for row in payload["predicate_count_table"]:
        lines.append(f"| `{row['route_family']}` | `{row['predicate_label']}` | {row['row_count']} |")
    lines.extend(["", "## Boundary", ""])
    for key, value in payload["boundary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    preflight_summary = read_json(args.preflight_stage_dir / "summary.json")
    materialization_manifest = read_json(args.materialization_dir / "row_manifest.json")
    errors = validate_preflight(preflight_summary)
    mat_errors, details = validate_materialization(args.materialization_dir, materialization_manifest)
    errors.extend(mat_errors)

    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_route_materialization_protocol_errors",
        "next_todo": NEXT_TODO if not errors else EXPECTED_PREFLIGHT_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "input_artifacts": {
            "preflight_stage": rel_path(args.preflight_stage_dir),
            "materialization_runtime": rel_path(args.materialization_dir),
        },
        "runtime_outputs": {
            "route_rows": rel_path(args.materialization_dir / "route_rows.jsonl"),
            "model_safe_view": rel_path(args.materialization_dir / "model_safe_view.jsonl"),
            "hidden_manifest": rel_path(args.materialization_dir / "hidden_manifest.jsonl"),
            "row_manifest": rel_path(args.materialization_dir / "row_manifest.json"),
            "validation_errors": rel_path(args.materialization_dir / "validation_errors.jsonl"),
        },
        "row_counts": details.get("counts", {}),
        "route_count_table": details.get("route_count_rows", []),
        "predicate_count_table": details.get("predicate_count_rows", []),
        "file_manifest": details.get("files", []),
        "boundary": {
            "route_materialization_run": not errors,
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
            "protocol_split": "unassigned_pre_grouped_holdout",
        },
        "next_step_contract": next_contract(),
    }

    write_csv(args.output_dir / "materialization_manifest.csv", payload["file_manifest"])
    write_csv(args.output_dir / "route_count_table.csv", payload["route_count_table"])
    write_csv(args.output_dir / "predicate_count_table.csv", payload["predicate_count_table"])
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
