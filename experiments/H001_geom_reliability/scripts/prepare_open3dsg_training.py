#!/usr/bin/env python3
"""Prepare the Docker handoff contract for Open3DSG training reproduction."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_training_handoff_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--training-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_repro/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_handoff"),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def min_ready(values: dict[str, Any]) -> int:
    if not values:
        return 0
    return min(int(value) for value in values.values())


def payload_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    train = manifest.get("train_payload", {})
    expected = int(train.get("expected_scans", 1178))
    scan_dirs = int(train.get("existing_scan_dirs", 0))
    mesh_ready = min_ready(train.get("open3dsg_files", {}))
    sequence_ready = min_ready(train.get("sequence_files", {}))
    raw_ready = min_ready(train.get("raw_files", {}))
    blockers = []
    if scan_dirs < expected:
        blockers.append(f"train_scan_dirs:{scan_dirs}/{expected}")
    if mesh_ready < expected:
        blockers.append(f"train_open3dsg_mesh_texture:{mesh_ready}/{expected}")
    if sequence_ready < expected:
        blockers.append(f"train_sequence:{sequence_ready}/{expected}")
    if raw_ready < expected:
        blockers.append(f"train_raw_files:{raw_ready}/{expected}")
    return {
        "passed": not blockers,
        "expected_scans": expected,
        "train_scan_dirs": scan_dirs,
        "train_raw_files_min": raw_ready,
        "train_open3dsg_mesh_texture_min": mesh_ready,
        "train_sequence_min": sequence_ready,
        "blockers": blockers,
    }


def make_commands() -> dict[str, str]:
    compose = "experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml"
    root_compose = "experiments/H001_geom_reliability/compose.yaml"
    prefix = "sg docker -c 'env UID=$(id -u) GID=$(id -g)"
    return {
        "build_repro_image": f"sg docker -c 'docker compose -f {compose} build'",
        "env_check": f"{prefix} docker compose -f {compose} run --rm env_check'",
        "cache_preflight": f"{prefix} docker compose -f {compose} run --rm cache_preflight'",
        "refresh_training_root": f"{prefix} docker compose -f {root_compose} run --rm open3dsg_train_root'",
        "dump_features_3rscan": f"{prefix} docker compose -f {compose} run --rm dump_features_3rscan'",
        "train_pilot": f"{prefix} docker compose -f {compose} run --rm train_pilot'",
        "train_full": f"{prefix} docker compose -f {compose} run --rm train_full'",
        "eval_preflight": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            "OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt "
            f"docker compose -f {compose} run --rm eval_preflight'"
        ),
        "eval_h001_gt_objects": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            "OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt "
            f"docker compose -f {compose} run --rm eval_h001_gt_objects'"
        ),
    }


def make_report(payload: dict[str, Any]) -> str:
    gate = payload["gates"]["payload"]
    lines = [
        "# Open3DSG Training Handoff",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Payload Gate",
        "",
        f"- passed: `{gate['passed']}`",
        f"- train scan dirs: `{gate['train_scan_dirs']}/{gate['expected_scans']}`",
        f"- train raw files min: `{gate['train_raw_files_min']}/{gate['expected_scans']}`",
        f"- train mesh/texture min: `{gate['train_open3dsg_mesh_texture_min']}/{gate['expected_scans']}`",
        f"- train sequence min: `{gate['train_sequence_min']}/{gate['expected_scans']}`",
        "",
        "## Next Commands",
        "",
    ]
    for name in payload["recommended_order"]:
        lines.append(f"- `{name}`: `{payload['commands'][name]}`")
    if gate["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in gate["blockers"])
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This handoff fixes the Docker command order only. It does not train Open3DSG, create a checkpoint, or create second-source metric evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    training_manifest = args.training_manifest
    if not training_manifest.is_absolute():
        training_manifest = repo_root / training_manifest
    out_dir = args.out
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not training_manifest.exists():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "blocked_missing_training_manifest",
            "training_manifest": relpath(repo_root, training_manifest),
            "gates": {},
            "commands": make_commands(),
            "recommended_order": ["refresh_training_root"],
        }
        write_json(out_dir / "manifest.json", payload)
        (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")
        return 1

    manifest = load_json(training_manifest)
    gate = payload_gate(manifest)
    status = "ready_for_open3dsg_env_check" if gate["passed"] else "blocked_payload_incomplete"
    recommended = ["build_repro_image", "env_check", "cache_preflight"]
    if gate["passed"]:
        recommended.extend(["dump_features_3rscan", "train_pilot", "train_full", "eval_preflight", "eval_h001_gt_objects"])
    else:
        recommended.insert(0, "refresh_training_root")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "training_manifest": relpath(repo_root, training_manifest),
        "gates": {"payload": gate},
        "commands": make_commands(),
        "recommended_order": recommended,
        "artifacts": {
            "training_root": "local_dataset/Open3DSG_staged/training_repro",
            "checkpoint_dir": "local_dataset/Open3DSG_staged/training_repro/output/checkpoints",
            "open3dsg_compose": "experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml",
        },
    }
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "commands.md").write_text(make_report(payload), encoding="utf-8")
    (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
