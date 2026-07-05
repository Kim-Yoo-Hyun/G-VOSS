#!/usr/bin/env python3
"""Validate the H002 experiment/config/results skeleton after the Docker protocol."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan"
)

EXPERIMENT_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing"
CONFIG_ROOT = REPO_ROOT / "configs/h002"
RESULTS_ROOT = REPO_ROOT / "results/h002_compatibility_routing"

EXPECTED_PROTOCOL_STATUS = (
    "h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready"
)
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_input_errors"
)
SELECTED_PATH = "experiment_config_results_skeleton_created_select_docker_preflight_implementation"
NEXT_TODO = "compatibility_dataset_v3_docker_preflight_implementation_after_experiment_root_skeleton"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    protocol_summary: dict[str, Any],
    protocol_scope: list[dict[str, str]],
    protocol_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append(
            {
                "error_type": "unexpected_protocol_status",
                "expected": EXPECTED_PROTOCOL_STATUS,
                "actual": protocol_summary.get("status"),
            }
        )
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append(
            {
                "error_type": "unexpected_protocol_next_todo",
                "expected": EXPECTED_PROTOCOL_NEXT,
                "actual": protocol_summary.get("next_todo"),
            }
        )
    if validation_count(protocol_summary) != 0:
        errors.append({"error_type": "protocol_validation_errors", "actual": validation_count(protocol_summary)})
    boundary = protocol_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "official_validation_usage", "new_model_or_smoke_run"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "protocol_boundary_not_false", "key": key, "actual": boundary.get(key)})
    validation_file = protocol_dir / "validation_errors.jsonl"
    if validation_file.exists() and validation_file.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "protocol_validation_error_rows_present"})

    promoted = [row for row in protocol_scope if row.get("protocol_role") == "promoted_candidate"]
    if len(promoted) != 4:
        errors.append({"error_type": "unexpected_promoted_route_count", "actual": len(promoted)})
    return errors


def skeleton_files() -> list[dict[str, Any]]:
    return [
        {
            "path": EXPERIMENT_ROOT / "README.md",
            "owner": "experiment root status and boundary",
            "required": True,
        },
        {
            "path": EXPERIMENT_ROOT / "commands.md",
            "owner": "future Docker command index",
            "required": True,
        },
        {
            "path": CONFIG_ROOT / "README.md",
            "owner": "H002 Docker config status and planned services",
            "required": True,
        },
        {
            "path": RESULTS_ROOT / "README.md",
            "owner": "compact result root boundary",
            "required": True,
        },
    ]


def skeleton_manifest(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in files:
        path = item["path"]
        rows.append(
            {
                "path": rel_path(path),
                "exists": str(path.exists()),
                "owner": item["owner"],
                "required": str(item["required"]),
                "role": "durable_root_owner_file",
            }
        )
    return rows


def owner_update_matrix() -> list[dict[str, Any]]:
    return [
        {
            "file": "experiments/README.md",
            "update": "add H002 skeleton root and paper-result boundary",
            "status": "required_this_step",
        },
        {
            "file": "configs/README.md",
            "update": "add h002 config skeleton pointer",
            "status": "required_this_step",
        },
        {
            "file": "results/README.md",
            "update": "add h002 compact result skeleton pointer",
            "status": "required_this_step",
        },
        {
            "file": "docs/index.md",
            "update": "add H002 experiment/config/results navigation pointers",
            "status": "required_this_step",
        },
        {
            "file": "TODO.md",
            "update": "advance H002 next TODO",
            "status": "required_this_step",
        },
    ]


def next_step_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "implement a Docker preflight service before any materialization or metric run",
            "create configs/h002/compose.yaml and any minimal preflight script in the next gate",
            "verify mounts and previous artifact statuses inside Docker",
            "keep grouped holdout language separate from official validation/test",
        ],
        "must_not_do": [
            "run H002 paper metrics before preflight passes",
            "write row-level dumps to results/h002_compatibility_routing/",
            "modify H001 artifacts",
            "claim calibrated p_rel/p_obs without calibration metrics",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Experiment Root Skeleton",
        "",
        "## Verdict",
        "",
        (
            "The H002 experiment/config/results skeleton exists, but no Docker service, model run, "
            "grouped-holdout metric, or paper-level result exists yet."
        ),
        "",
        "## Skeleton Files",
        "",
        "| Path | Exists | Owner |",
        "| --- | --- | --- |",
    ]
    for row in payload["skeleton_manifest"]:
        lines.append("| {path} | {exists} | {owner} |".format(**row))
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No paper-level H002 metric was produced.",
            "- No official validation/test was used.",
            "- H001 artifacts remain read-only.",
            "- The next step is Docker preflight implementation.",
            "",
            "## Next",
            "",
            f"`{NEXT_TODO}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    protocol_scope = read_csv(args.protocol_dir / "protocol_scope.csv")
    errors = validate_inputs(protocol_summary, protocol_scope, args.protocol_dir)

    files = skeleton_files()
    manifest = skeleton_manifest(files)
    for row in manifest:
        if row["required"] == "True" and row["exists"] != "True":
            errors.append({"error_type": "missing_skeleton_file", "path": row["path"]})

    owner_updates = owner_update_matrix()
    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_missing_skeleton_or_owner_files",
        "next_todo": NEXT_TODO if not errors else EXPECTED_PROTOCOL_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "official_validation_usage": False,
            "new_model_or_smoke_run": False,
            "docker_preflight_run": False,
            "grouped_holdout_run": False,
            "paper_metric_produced": False,
            "h001_artifacts_modified": False,
            "experiment_root_skeleton_created": not errors,
        },
        "input_artifacts": {"docker_heldout_protocol_plan": rel_path(args.protocol_dir)},
        "decision_summary": {
            "experiment_root": rel_path(EXPERIMENT_ROOT),
            "config_root": rel_path(CONFIG_ROOT),
            "results_root": rel_path(RESULTS_ROOT),
            "skeleton_status": "created_no_metrics" if not errors else "blocked",
            "next_step": "docker_preflight_implementation",
        },
        "skeleton_manifest": manifest,
        "owner_update_matrix": owner_updates,
        "next_step_contract": next_step_contract(),
    }

    write_csv(args.output_dir / "skeleton_manifest.csv", manifest)
    write_csv(args.output_dir / "owner_update_matrix.csv", owner_updates)
    write_json(args.output_dir / "next_contract.json", next_step_contract())
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
