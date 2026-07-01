#!/usr/bin/env python3
"""Validate the Docker official candidate materialization output for H002."""

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

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory"
DEFAULT_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_materialization/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol"

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready"
EXPECTED_MATERIALIZATION_STATUS = "h002_official_candidate_materialization_ready"
EXPECTED_SCHEMA = "h002_official_candidate_materialization_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_errors"
SELECTED_PATH = "official_materialization_ready_select_schema_shortcut_audit"
NEXT_TODO = "compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation"

EXPECTED_FAMILIES = {"relative_horizontal", "relative_vertical", "size_relative", "support_contact"}
BLOCKED_MODEL_SAFE_KEYS = {
    "source_score",
    "ranking_score",
    "semantic_rank",
    "source_id",
    "h001_p_geom_valid",
    "h001_verification_status",
    "label_match_status",
    "geometry_status",
    "candidate_bucket",
    "construction_bucket",
    "distance_bucket",
    "rank_band",
    "gt_exact_match_flag",
    "counterfactual_type",
    "target_generation_rule",
    "old_proxy_label",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(iter_jsonl(path))


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
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def flatten_paths(value: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield child_prefix
            yield from flatten_paths(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten_paths(child, f"{prefix}[{index}]")


def blocked_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for path in flatten_paths(row):
        if path.split(".")[-1] in BLOCKED_MODEL_SAFE_KEYS:
            hits.append(path)
    return hits


def validate(
    *,
    protocol_summary: dict[str, Any],
    row_manifest: dict[str, Any],
    runtime_errors: list[dict[str, Any]],
    materialization_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors", "actual": protocol_summary.get("validation_errors")})
    if row_manifest.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": row_manifest.get("status")})
    if row_manifest.get("schema_version") != EXPECTED_SCHEMA:
        errors.append({"error_type": "unexpected_materialization_schema", "actual": row_manifest.get("schema_version")})
    if row_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "materialization_manifest_validation_errors", "actual": row_manifest.get("validation_errors")})
    if runtime_errors:
        errors.append({"error_type": "runtime_validation_error_rows_present", "rows": len(runtime_errors)})
    for key in ["official_validation_metric_produced", "official_test_usage", "paper_metric_produced", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if row_manifest.get(key) is not False:
            errors.append({"error_type": "unexpected_metric_boundary", "key": key, "actual": row_manifest.get(key)})

    paths = {
        "candidate_rows": materialization_dir / "candidate_rows.jsonl",
        "model_safe_view": materialization_dir / "model_safe_view.jsonl",
        "hidden_manifest": materialization_dir / "hidden_manifest.jsonl",
        "validation_errors": materialization_dir / "validation_errors.jsonl",
    }
    counts = {name: line_count(path) for name, path in paths.items()}
    manifest_counts = row_manifest.get("row_counts", {})
    for name in ["candidate_rows", "model_safe_view", "hidden_manifest"]:
        if counts[name] != int(manifest_counts.get(name, -1)):
            errors.append({"error_type": "manifest_count_mismatch", "file": name, "line_count": counts[name], "manifest": manifest_counts.get(name)})
    if counts["validation_errors"] != 0:
        errors.append({"error_type": "nonempty_runtime_validation_errors", "line_count": counts["validation_errors"]})

    family_counts: Counter[str] = Counter()
    family_label_counts: Counter[tuple[str, int]] = Counter()
    origin_counts: Counter[str] = Counter()
    blocked_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    duplicate_ids = 0
    schema_bad = 0
    policy_bad = 0
    missing_g = 0
    for index, row in enumerate(iter_jsonl(paths["model_safe_view"]), start=1):
        candidate_id = row.get("candidate_id")
        if candidate_id in seen_ids:
            duplicate_ids += 1
        seen_ids.add(candidate_id)
        if row.get("schema_version") != EXPECTED_SCHEMA:
            schema_bad += 1
        family = str(row.get("route_family"))
        family_counts[family] += 1
        family_label_counts[(family, int(row.get("target_y", -1)))] += 1
        origin_counts[str(row.get("candidate_origin"))] += 1
        policy = row.get("feature_use_policy", {})
        if policy.get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
            policy_bad += 1
        blocks = row.get("feature_blocks", {})
        g = blocks.get("G_e", {})
        if not isinstance(g, dict) or not g.get("g_e_available") or not g.get("g_e_feature_vector"):
            missing_g += 1
        hits = blocked_hits(row)
        if hits:
            blocked_rows.append(
                {
                    "line": index,
                    "candidate_id": candidate_id,
                    "route_family": family,
                    "predicate_label": row.get("predicate_label"),
                    "hits": "|".join(hits),
                }
            )

    for family in EXPECTED_FAMILIES:
        if family_counts[family] <= 0:
            errors.append({"error_type": "missing_family_rows", "family": family})
        if family_label_counts[(family, 0)] <= 0 or family_label_counts[(family, 1)] <= 0:
            errors.append(
                {
                    "error_type": "family_missing_binary_labels",
                    "family": family,
                    "label_0": family_label_counts[(family, 0)],
                    "label_1": family_label_counts[(family, 1)],
                }
            )
    if duplicate_ids:
        errors.append({"error_type": "duplicate_candidate_ids", "count": duplicate_ids})
    if schema_bad:
        errors.append({"error_type": "model_safe_schema_mismatch_rows", "count": schema_bad})
    if policy_bad:
        errors.append({"error_type": "model_safe_policy_bad_rows", "count": policy_bad})
    if missing_g:
        errors.append({"error_type": "missing_g_e_rows", "count": missing_g})
    if blocked_rows:
        errors.append({"error_type": "model_safe_blocked_field_hits", "rows": len(blocked_rows)})

    family_rows = []
    for family in sorted(family_counts):
        family_rows.append(
            {
                "route_family": family,
                "rows": family_counts[family],
                "label_0": family_label_counts[(family, 0)],
                "label_1": family_label_counts[(family, 1)],
            }
        )
    origin_rows = [{"candidate_origin": key, "rows": value} for key, value in sorted(origin_counts.items())]
    return errors, counts, family_rows, origin_rows + blocked_rows[:20]


def write_report(path: Path, summary: dict[str, Any], family_rows: list[dict[str, Any]], counts: dict[str, int]) -> None:
    lines = [
        "# H002 Official Candidate Materialization Docker Implementation",
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
        "## Runtime Counts",
        "",
        "| File | Rows |",
        "| --- | ---: |",
    ]
    for name in ["candidate_rows", "model_safe_view", "hidden_manifest", "validation_errors"]:
        lines.append(f"| `{name}` | {counts.get(name, 0)} |")
    lines.extend(["", "## Family Counts", "", "| Family | Rows | Label 0 | Label 1 |", "| --- | ---: | ---: | ---: |"])
    for row in family_rows:
        lines.append(f"| `{row['route_family']}` | {row['rows']} | {row['label_0']} | {row['label_1']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Docker official validation candidate materialization completed.",
            "- This stage generated rows only; no official metric was computed.",
            "- Official test was not used.",
            "- `p_rel` / `p_obs` remain disabled.",
            "- Next stage is materialization schema/shortcut audit.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol_summary = read_json(args.protocol_dir / "summary.json")
    row_manifest = read_json(args.materialization_dir / "row_manifest.json")
    runtime_errors = read_jsonl(args.materialization_dir / "validation_errors.jsonl")
    validation_errors, counts, family_rows, diagnostic_rows = validate(
        protocol_summary=protocol_summary,
        row_manifest=row_manifest,
        runtime_errors=runtime_errors,
        materialization_dir=args.materialization_dir,
    )
    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_official_materialization",
        "next_todo": NEXT_TODO if not validation_errors else "fix_official_candidate_materialization",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "row_manifest": rel_path(args.materialization_dir / "row_manifest.json"),
            "materialization_dir": rel_path(args.materialization_dir),
        },
        "output_artifacts": {
            "file_counts": rel_path(args.output_dir / "file_counts.csv"),
            "family_counts": rel_path(args.output_dir / "family_counts.csv"),
            "diagnostic_rows": rel_path(args.output_dir / "diagnostic_rows.csv"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "runtime_summary": row_manifest.get("row_counts", {}),
        "boundary": {
            "candidate_rows_materialized": True,
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
    }
    next_runner_contract = {
        "next_todo": NEXT_TODO,
        "runner_purpose": "Audit official materialized model-safe/hidden views for leakage and shortcut risk before metrics.",
        "input_root": rel_path(args.materialization_dir),
        "must_not_do": [
            "compute official validation metrics",
            "touch official test",
            "enable p_rel/p_obs",
            "promote row counts as paper results",
        ],
    }
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_runner_contract.json", next_runner_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "file_counts.csv", [{"file": key, "rows": value} for key, value in counts.items()])
    write_csv(args.output_dir / "family_counts.csv", family_rows)
    write_csv(args.output_dir / "diagnostic_rows.csv", diagnostic_rows)
    write_report(args.output_dir / "report.md", summary, family_rows, counts)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
