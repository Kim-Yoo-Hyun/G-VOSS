#!/usr/bin/env python3
"""Validate H002 Docker preflight implementation and run output."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SKELETON_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan"
)
DEFAULT_PREFLIGHT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/preflight/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton"
)

EXPECTED_SKELETON_STATUS = (
    "h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_ready"
)
EXPECTED_SKELETON_NEXT = "compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton"
EXPECTED_PREFLIGHT_STATUS = "ready"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton_input_errors"
)
SELECTED_PATH = "docker_preflight_passed_select_route_materialization_protocol_implementation"
NEXT_TODO = "compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skeleton-dir", type=Path, default=DEFAULT_SKELETON_DIR)
    parser.add_argument("--preflight-dir", type=Path, default=DEFAULT_PREFLIGHT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def validation_count(summary: dict[str, Any]) -> int:
    for key in ("validation_errors", "validation_error_count"):
        if key in summary:
            return int(summary.get(key) or 0)
    return 0


def validate_inputs(
    skeleton_summary: dict[str, Any],
    preflight_manifest: dict[str, Any],
    skeleton_dir: Path,
    preflight_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if skeleton_summary.get("status") != EXPECTED_SKELETON_STATUS:
        errors.append(
            {
                "error_type": "unexpected_skeleton_status",
                "expected": EXPECTED_SKELETON_STATUS,
                "actual": skeleton_summary.get("status"),
            }
        )
    if skeleton_summary.get("next_todo") != EXPECTED_SKELETON_NEXT:
        errors.append(
            {
                "error_type": "unexpected_skeleton_next_todo",
                "expected": EXPECTED_SKELETON_NEXT,
                "actual": skeleton_summary.get("next_todo"),
            }
        )
    if validation_count(skeleton_summary) != 0:
        errors.append({"error_type": "skeleton_validation_errors", "actual": validation_count(skeleton_summary)})
    skeleton_validation = skeleton_dir / "validation_errors.jsonl"
    if skeleton_validation.exists() and skeleton_validation.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "skeleton_validation_error_rows_present"})

    if preflight_manifest.get("status") != EXPECTED_PREFLIGHT_STATUS:
        errors.append(
            {
                "error_type": "unexpected_preflight_status",
                "expected": EXPECTED_PREFLIGHT_STATUS,
                "actual": preflight_manifest.get("status"),
            }
        )
    if validation_count(preflight_manifest) != 0:
        errors.append({"error_type": "preflight_validation_errors", "actual": validation_count(preflight_manifest)})
    preflight_validation = preflight_dir / "validation_errors.jsonl"
    if preflight_validation.exists() and preflight_validation.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "preflight_validation_error_rows_present"})

    boundary = preflight_manifest.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_run", "official_validation_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "preflight_boundary_not_false", "key": key, "actual": boundary.get(key)})

    readonly = preflight_manifest.get("h001_readonly_probes", {})
    for name in ["h001_results", "h001_archive_experiment"]:
        result = readonly.get(name, {})
        if result.get("write_succeeded") is not False or result.get("read_only_like_error") is not True:
            errors.append({"error_type": "h001_readonly_probe_failed", "name": name, "result": result})
    return errors


def implementation_manifest(preflight_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    files = [
        ("Dockerfile", REPO_ROOT / "configs/h002/Dockerfile"),
        ("compose", REPO_ROOT / "configs/h002/compose.yaml"),
        ("preflight_script", REPO_ROOT / "experiments/H002_compatibility_routing/scripts/preflight.py"),
        ("mount_check", REPO_ROOT / "experiments/H002_compatibility_routing/preflight/latest/mount_check.json"),
        ("run_manifest", REPO_ROOT / "experiments/H002_compatibility_routing/preflight/latest/run_manifest.json"),
        ("preflight_validation_errors", REPO_ROOT / "experiments/H002_compatibility_routing/preflight/latest/validation_errors.jsonl"),
    ]
    return [
        {
            "name": name,
            "path": rel_path(path),
            "exists": str(path.exists()),
            "role": "docker_preflight_implementation" if name in {"Dockerfile", "compose", "preflight_script"} else "docker_preflight_output",
            "git_commit": preflight_manifest.get("git_commit", ""),
        }
        for name, path in files
    ]


def boundary_rows(preflight_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, value in preflight_manifest.get("boundary", {}).items():
        rows.append({"boundary": key, "value": str(value)})
    rows.append({"boundary": "h001_results_readonly", "value": str(preflight_manifest["h001_readonly_probes"]["h001_results"].get("read_only_like_error"))})
    rows.append(
        {
            "boundary": "h001_archive_experiment_readonly",
            "value": str(preflight_manifest["h001_readonly_probes"]["h001_archive_experiment"].get("read_only_like_error")),
        }
    )
    return rows


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "implement Docker route materialization protocol before any grouped metric run",
            "write materialization output under experiments/H002_compatibility_routing/ only",
            "keep results/h002_compatibility_routing compact-only",
            "preserve model-safe and hidden-manifest separation",
        ],
        "must_not_do": [
            "run grouped-holdout metrics before route rows and split manifest exist",
            "write row-level dumps to results/",
            "use H001 artifacts as writable inputs",
            "call the H002 candidate-pool holdout official validation/test",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Docker Preflight Implementation",
        "",
        "## Verdict",
        "",
        "Docker preflight implementation passed. No paper metric, grouped holdout, or official validation/test was run.",
        "",
        "## Outputs",
        "",
        "| File | Role | Exists |",
        "| --- | --- | --- |",
    ]
    for row in payload["implementation_manifest"]:
        lines.append("| {path} | {role} | {exists} |".format(**row))
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "| Boundary | Value |",
            "| --- | --- |",
        ]
    )
    for row in payload["boundary_checks"]:
        lines.append("| {boundary} | {value} |".format(**row))
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    skeleton_summary = read_json(args.skeleton_dir / "summary.json")
    preflight_manifest = read_json(args.preflight_dir / "run_manifest.json")
    errors = validate_inputs(skeleton_summary, preflight_manifest, args.skeleton_dir, args.preflight_dir)

    impl = implementation_manifest(preflight_manifest)
    boundaries = boundary_rows(preflight_manifest)
    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_docker_preflight_errors",
        "next_todo": NEXT_TODO if not errors else EXPECTED_SKELETON_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "boundary": {
            "docker_preflight_run": not errors,
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
        },
        "input_artifacts": {
            "skeleton": rel_path(args.skeleton_dir),
            "preflight_output": rel_path(args.preflight_dir),
        },
        "decision_summary": {
            "docker_preflight": "passed" if not errors else "blocked",
            "next_step": "route_materialization_protocol_implementation",
            "h001_readonly_confirmed": not errors,
            "paper_metrics_produced": False,
        },
        "implementation_manifest": impl,
        "boundary_checks": boundaries,
        "next_step_contract": next_contract(),
    }

    write_csv(args.output_dir / "implementation_manifest.csv", impl)
    write_csv(args.output_dir / "boundary_checks.csv", boundaries)
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
