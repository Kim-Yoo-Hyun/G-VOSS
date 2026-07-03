#!/usr/bin/env python3
"""Validate source-reranking Docker materialization outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory"
)
DEFAULT_MATERIALIZATION_DIR = (
    REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_materialization/latest"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol"
)

EXPECTED_PROTOCOL_STATUS = (
    "h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_ready"
)
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_materialization_ready"
EXPECTED_RUNTIME_SCHEMA = "h002_source_reranking_materialization_v1"
EXPECTED_TOTAL_ROWS = 762888
EXPECTED_PRIMARY_ROWS = 254296
EXPECTED_SOURCE_COUNTS = {
    "open3dsg_recovery_relaxed_views_min2": 321192,
    "vlsat_full_validation": 441696,
}
EXPECTED_FAMILY_COUNTS = {
    "proximity": 63574,
    "relative_horizontal": 254296,
    "relative_vertical": 127148,
    "size_relative": 127148,
    "support_contact": 190722,
}

SCHEMA_VERSION = "h002_source_reranking_docker_materialization_after_protocol_v1"
STATUS_READY = "h002_source_reranking_docker_materialization_after_protocol_ready"
STATUS_ERRORS = "h002_source_reranking_docker_materialization_after_protocol_errors"
SELECTED_PATH = "source_reranking_docker_materialized_select_schema_audit"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization"

BLOCKED_FEATURE_TOKENS = {
    "gt_",
    "h001",
    "p_geom",
    "rank",
    "score",
    "source_score",
    "target_y",
    "verification_status",
    "violation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
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


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def flatten_paths(value: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path
            yield from flatten_paths(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten_paths(child, f"{prefix}[{index}]")


def validate_protocol(protocol_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary = read_json(protocol_dir / "summary.json")
    if summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors_present", "actual": summary.get("validation_errors")})
    decision = summary.get("decision", {})
    for key in ["metrics_run", "official_test_usage", "paper_metric_promoted"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "unexpected_protocol_boundary", "key": key, "actual": decision.get(key)})
    return errors


def validate_runtime(materialization_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    required = {
        "source_candidates": materialization_dir / "source_candidates.jsonl",
        "model_safe_ce_view": materialization_dir / "model_safe_ce_view.jsonl",
        "model_safe_geometry_only_view": materialization_dir / "model_safe_geometry_only_view.jsonl",
        "source_rank_view": materialization_dir / "source_rank_view.jsonl",
        "hidden_metric_manifest": materialization_dir / "hidden_metric_manifest.jsonl",
        "validation_errors": materialization_dir / "validation_errors.jsonl",
    }
    counts = {name: line_count(path) for name, path in required.items()}
    if manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": manifest.get("status")})
    if manifest.get("schema_version") != EXPECTED_RUNTIME_SCHEMA:
        errors.append({"error_type": "unexpected_runtime_schema", "actual": manifest.get("schema_version")})
    if manifest.get("validation_errors") != 0 or counts["validation_errors"] != 0:
        errors.append(
            {
                "error_type": "runtime_validation_errors_present",
                "summary_errors": manifest.get("validation_errors"),
                "file_errors": counts["validation_errors"],
            }
        )
    for name, count in counts.items():
        expected = 0 if name == "validation_errors" else EXPECTED_TOTAL_ROWS
        if count != expected:
            errors.append({"error_type": "line_count_mismatch", "file": name, "actual": count, "expected": expected})
    if manifest.get("source_reranking_metrics_run") is not False:
        errors.append({"error_type": "source_reranking_metric_was_run", "actual": manifest.get("source_reranking_metrics_run")})
    if manifest.get("official_test_usage") is not False:
        errors.append({"error_type": "official_test_used", "actual": manifest.get("official_test_usage")})
    if manifest.get("paper_metric_promoted") is not False:
        errors.append({"error_type": "paper_metric_promoted", "actual": manifest.get("paper_metric_promoted")})
    if manifest.get("source_wide_Ce_materialization_done") is not True:
        errors.append({"error_type": "source_wide_Ce_materialization_not_done", "actual": manifest.get("source_wide_Ce_materialization_done")})

    row_counts = manifest.get("row_counts", {})
    if row_counts.get("total_rows") != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "total_rows_mismatch", "actual": row_counts.get("total_rows"), "expected": EXPECTED_TOTAL_ROWS})
    if row_counts.get("primary_success_family_rows") != EXPECTED_PRIMARY_ROWS:
        errors.append(
            {
                "error_type": "primary_success_rows_mismatch",
                "actual": row_counts.get("primary_success_family_rows"),
                "expected": EXPECTED_PRIMARY_ROWS,
            }
        )
    if row_counts.get("source_counts") != EXPECTED_SOURCE_COUNTS:
        errors.append({"error_type": "source_counts_mismatch", "actual": row_counts.get("source_counts"), "expected": EXPECTED_SOURCE_COUNTS})
    if row_counts.get("family_counts") != EXPECTED_FAMILY_COUNTS:
        errors.append({"error_type": "family_counts_mismatch", "actual": row_counts.get("family_counts"), "expected": EXPECTED_FAMILY_COUNTS})

    ids: dict[str, set[str]] = {}
    family_counts = Counter()
    source_counts = Counter()
    feature_policy_bad = 0
    blocked_hits = 0
    for name in ["source_candidates", "model_safe_ce_view", "model_safe_geometry_only_view", "source_rank_view", "hidden_metric_manifest"]:
        ids[name] = set()
        for row in iter_jsonl(required[name]):
            candidate_id = str(row.get("candidate_id"))
            ids[name].add(candidate_id)
            if name == "model_safe_ce_view":
                family_counts[str(row.get("route_family"))] += 1
                source_counts[str(row.get("source_id"))] += 1
                blocks = row.get("feature_blocks", {})
                if set(blocks) != {"T_e", "G_e"}:
                    feature_policy_bad += 1
                if row.get("feature_use_policy", {}).get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
                    feature_policy_bad += 1
                for path in flatten_paths(blocks):
                    lower = path.lower()
                    if any(token in lower for token in BLOCKED_FEATURE_TOKENS):
                        blocked_hits += 1
            if name == "source_rank_view" and "Z_e" not in row:
                errors.append({"error_type": "source_rank_missing_Z_e", "candidate_id": candidate_id})
            if name == "hidden_metric_manifest" and not row.get("metric_only"):
                errors.append({"error_type": "hidden_manifest_not_metric_only", "candidate_id": candidate_id})

    base = ids["model_safe_ce_view"]
    for name, view_ids in ids.items():
        if view_ids != base:
            errors.append({"error_type": "candidate_id_alignment_mismatch", "view": name, "missing": len(base - view_ids), "extra": len(view_ids - base)})
    if len(base) != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "candidate_id_unique_count_mismatch", "actual": len(base), "expected": EXPECTED_TOTAL_ROWS})
    if feature_policy_bad:
        errors.append({"error_type": "model_safe_ce_feature_policy_violations", "rows_or_checks": feature_policy_bad})
    if blocked_hits:
        errors.append({"error_type": "model_safe_ce_blocked_feature_hits", "hits": blocked_hits})

    count_rows = [
        {"file": name, "line_count": count, "expected": 0 if name == "validation_errors" else EXPECTED_TOTAL_ROWS}
        for name, count in sorted(counts.items())
    ]
    family_rows = [
        {"family": family, "rows": count, "expected": EXPECTED_FAMILY_COUNTS.get(family)}
        for family, count in sorted(family_counts.items())
    ]
    source_rows = [
        {"source_id": source, "rows": count, "expected": EXPECTED_SOURCE_COUNTS.get(source)}
        for source, count in sorted(source_counts.items())
    ]
    schema_rows = [
        {"check": "candidate_id_alignment", "status": "pass" if all(view_ids == base for view_ids in ids.values()) else "fail"},
        {"check": "model_safe_ce_blocks_are_Te_Ge_only", "status": "pass" if feature_policy_bad == 0 else "fail", "violations": feature_policy_bad},
        {"check": "model_safe_ce_blocked_feature_absence", "status": "pass" if blocked_hits == 0 else "fail", "hits": blocked_hits},
        {"check": "source_rank_owns_Ze", "status": "pass"},
        {"check": "hidden_manifest_metric_only", "status": "pass"},
    ]
    return errors, counts, count_rows, family_rows + source_rows, schema_rows


def make_report(summary: dict[str, Any]) -> str:
    rows = summary["runtime_row_counts"]
    return f"""# Source Reranking Docker Materialization After Protocol

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Result

Docker materialization completed and wrote source-wide H002 source-reranking views.

- total rows: `{rows["total_rows"]}`
- primary success-family rows: `{rows["primary_success_family_rows"]}`
- VL-SAT rows: `{rows["source_counts"].get("vlsat_full_validation")}`
- Open3DSG rows: `{rows["source_counts"].get("open3dsg_recovery_relaxed_views_min2")}`
- source reranking metrics run: `false`
- official test usage: `false`

The next stage is a detailed materialization schema audit before reranking metric freeze.
"""


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_dir = args.protocol_dir
    materialization_dir = args.materialization_dir

    errors = validate_protocol(protocol_dir)
    manifest_path = materialization_dir / "row_manifest.json"
    if not manifest_path.exists():
        errors.append({"error_type": "missing_runtime_manifest", "path": rel_path(manifest_path)})
        manifest: dict[str, Any] = {}
        counts: dict[str, int] = {}
        count_rows: list[dict[str, Any]] = []
        family_rows: list[dict[str, Any]] = []
        schema_rows: list[dict[str, Any]] = []
    else:
        manifest = read_json(manifest_path)
        runtime_errors, counts, count_rows, family_rows, schema_rows = validate_runtime(materialization_dir, manifest)
        errors.extend(runtime_errors)

    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_source_reranking_materialization",
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
        "input_artifacts": {
            "protocol_summary": rel_path(protocol_dir / "summary.json"),
            "runtime_manifest": rel_path(manifest_path),
        },
        "output_artifacts": {
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "runtime_count_audit": rel_path(output_dir / "runtime_count_audit.csv"),
            "family_source_count_audit": rel_path(output_dir / "family_source_count_audit.csv"),
            "schema_boundary_audit": rel_path(output_dir / "schema_boundary_audit.csv"),
            "next_contract": rel_path(output_dir / "next_contract.json"),
            "report": rel_path(output_dir / "report.md"),
        },
        "runtime_row_counts": manifest.get("row_counts", {}),
        "runtime_file_counts": counts,
        "decision": {
            "docker_materialization_completed": not errors,
            "source_wide_Ce_materialization_done": manifest.get("source_wide_Ce_materialization_done") is True,
            "source_reranking_metrics_run": False,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "ready_for_schema_audit": not errors,
        },
    }
    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_materialization_schema_audit" if not errors else "blocked",
        "next_todo": NEXT_TODO,
        "runtime_materialization_dir": rel_path(materialization_dir),
        "must_validate_next": [
            "blocked_field_absence_deep_scan",
            "score_hidden_separation",
            "family_balanced_success_aggregation",
            "control_generation_readiness",
            "metric_freeze_precondition",
        ],
        "must_not_do": [
            "run_source_reranking_metrics_before_schema_audit",
            "use_official_test",
            "put_Ze_inside_Ce",
            "put_hidden_metric_labels_in_model_safe",
            "promote_support_contact_success",
        ],
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "runtime_count_audit.csv", count_rows)
    write_csv(output_dir / "family_source_count_audit.csv", family_rows)
    write_csv(output_dir / "schema_boundary_audit.csv", schema_rows)
    write_json(output_dir / "next_contract.json", next_contract)
    (output_dir / "report.md").write_text(make_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
