#!/usr/bin/env python3
"""Docker preflight for H002 compatibility-routing promotion."""

from __future__ import annotations

import argparse
import errno
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_PROTOCOL_STATUS = (
    "h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready"
)
EXPECTED_SKELETON_STATUS = (
    "h002_compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan_ready"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--local-dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


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


def git_commit(repo_root: Path) -> str:
    head = repo_root / ".git/HEAD"
    if not head.exists():
        return "unknown_no_git_head"
    value = head.read_text(encoding="utf-8").strip()
    if value.startswith("ref: "):
        ref = repo_root / ".git" / value.split(" ", 1)[1]
        if ref.exists():
            return ref.read_text(encoding="utf-8").strip()
    return value


def path_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }


def write_probe(path: Path) -> dict[str, Any]:
    probe = path / ".h002_readonly_probe"
    result: dict[str, Any] = {"path": str(path), "write_succeeded": False, "error": ""}
    try:
        probe.write_text("probe\n", encoding="utf-8")
        result["write_succeeded"] = True
        try:
            probe.unlink()
        except OSError as exc:
            result["cleanup_error"] = f"{type(exc).__name__}: {exc}"
    except OSError as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["errno"] = exc.errno
        result["read_only_like_error"] = exc.errno in {errno.EROFS, errno.EACCES, errno.EPERM}
    return result


def check_summary(
    name: str,
    path: Path,
    expected_status: str,
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    if not path.exists():
        errors.append({"check": name, "error_type": "missing_summary", "path": str(path)})
        return {"path": str(path), "exists": False}
    summary = read_json(path)
    actual = summary.get("status")
    validation_errors = summary.get("validation_errors", summary.get("validation_error_count", 0))
    status = {"path": str(path), "exists": True, "status": actual, "validation_errors": validation_errors}
    if actual != expected_status:
        errors.append(
            {
                "check": name,
                "error_type": "unexpected_status",
                "expected": expected_status,
                "actual": actual,
            }
        )
    if validation_errors != 0:
        errors.append({"check": name, "error_type": "validation_errors_present", "actual": validation_errors})
    return status


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    required_paths = {
        "repo_root": repo_root,
        "local_dataset_root": args.local_dataset_root,
        "h002_experiment_readme": repo_root / "experiments/H002_compatibility_routing/README.md",
        "h002_commands": repo_root / "experiments/H002_compatibility_routing/commands.md",
        "h002_config_readme": repo_root / "configs/h002/README.md",
        "h002_results_readme": repo_root / "results/h002_compatibility_routing/README.md",
        "h002_compose": repo_root / "configs/h002/compose.yaml",
        "h002_dockerfile": repo_root / "configs/h002/Dockerfile",
        "h002_preflight_script": repo_root / "experiments/H002_compatibility_routing/scripts/preflight.py",
        "h001_results": repo_root / "results/h001_geom_reliability",
        "h001_archive_experiment": repo_root / "archive/experiments/H001_geom_reliability",
    }
    path_checks = {name: path_status(path) for name, path in required_paths.items()}
    for name, status in path_checks.items():
        if not status["exists"]:
            errors.append({"check": name, "error_type": "missing_required_path", "path": status["path"]})

    protocol_summary = check_summary(
        "protocol_summary",
        repo_root
        / "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
        / "compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan/summary.json",
        EXPECTED_PROTOCOL_STATUS,
        errors,
    )
    skeleton_summary = check_summary(
        "skeleton_summary",
        repo_root
        / "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
        / "compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan/summary.json",
        EXPECTED_SKELETON_STATUS,
        errors,
    )

    h001_readonly_probes = {
        "h001_results": write_probe(repo_root / "results/h001_geom_reliability")
        if (repo_root / "results/h001_geom_reliability").exists()
        else {"path": str(repo_root / "results/h001_geom_reliability"), "missing": True},
        "h001_archive_experiment": write_probe(repo_root / "archive/experiments/H001_geom_reliability")
        if (repo_root / "archive/experiments/H001_geom_reliability").exists()
        else {"path": str(repo_root / "archive/experiments/H001_geom_reliability"), "missing": True},
    }
    for name, result in h001_readonly_probes.items():
        if result.get("write_succeeded"):
            errors.append({"check": name, "error_type": "h001_reference_path_writable", "path": result.get("path")})
        if result.get("missing"):
            errors.append({"check": name, "error_type": "h001_reference_path_missing", "path": result.get("path")})

    payload = {
        "schema_version": "h002_docker_preflight_v1",
        "status": "ready" if not errors else "errors",
        "created_at_utc": now,
        "git_commit": git_commit(repo_root),
        "boundary": {
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
        },
        "path_checks": path_checks,
        "protocol_summary": protocol_summary,
        "skeleton_summary": skeleton_summary,
        "h001_readonly_probes": h001_readonly_probes,
        "outputs": {
            "mount_check": str(out / "mount_check.json"),
            "run_manifest": str(out / "run_manifest.json"),
            "validation_errors": str(out / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
    }
    write_json(out / "mount_check.json", payload)
    write_json(out / "run_manifest.json", payload)
    write_jsonl(out / "validation_errors.jsonl", errors)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
