#!/usr/bin/env python3
"""Freeze the Open3DSG post-feature-dump handoff gates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_post_dump_handoff_v1"
DEFAULT_EXPECTED_TRAIN = 3744
DEFAULT_EXPECTED_VALIDATION = 156
REQUIRED_ROLES = {
    "object_valids": "export_obj_clip_valids",
    "object_embeddings": "export_obj_clip_emb",
    "relation_embeddings": "export_rel_clip_emb",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--feature-run-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/output/features/"
            "clip_features_h001_official_blip_top5_scales3"
        ),
    )
    parser.add_argument(
        "--feature-audit-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/dump_features/manifest.json"),
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro/output/checkpoints"),
    )
    parser.add_argument(
        "--raw-dump-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl"),
    )
    parser.add_argument(
        "--adapter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter/manifest.json"),
    )
    parser.add_argument(
        "--metrics-json",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/post_dump_handoff"),
    )
    parser.add_argument("--expected-train", type=int, default=DEFAULT_EXPECTED_TRAIN)
    parser.add_argument("--expected-validation", type=int, default=DEFAULT_EXPECTED_VALIDATION)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "unreadable_json"}


def role_for_dir(name: str) -> str | None:
    for role, prefix in REQUIRED_ROLES.items():
        if name.startswith(prefix):
            return role
    return None


def count_features(feature_run_dir: Path, expected_total: int) -> dict[str, Any]:
    role_ids: dict[str, set[str]] = {role: set() for role in REQUIRED_ROLES}
    subdirs: list[dict[str, Any]] = []
    unknown_subdirs: list[str] = []

    if feature_run_dir.is_dir():
        for child in sorted(feature_run_dir.iterdir()):
            if not child.is_dir():
                continue
            role = role_for_dir(child.name)
            ids = {path.stem for path in child.glob("*.pt") if path.is_file()}
            subdirs.append(
                {
                    "name": child.name,
                    "role": role or "unknown",
                    "pt_files": len(ids),
                    "sample_ids": sorted(ids)[:5],
                }
            )
            if role is None:
                unknown_subdirs.append(child.name)
            else:
                role_ids[role].update(ids)

    complete_ids: set[str] | None = None
    for role in REQUIRED_ROLES:
        complete_ids = set(role_ids[role]) if complete_ids is None else complete_ids & role_ids[role]
    complete_ids = complete_ids or set()
    by_role = {role: len(ids) for role, ids in sorted(role_ids.items())}
    missing_by_role = {role: max(expected_total - count, 0) for role, count in by_role.items()}
    complete_count = len(complete_ids)
    progress = complete_count / expected_total if expected_total else 0.0
    blockers: list[str] = []
    if not feature_run_dir.is_dir():
        blockers.append(f"missing_feature_run_dir:{feature_run_dir}")
    for role, count in by_role.items():
        if count < expected_total:
            blockers.append(f"{role}:{count}/{expected_total}")
    if complete_count < expected_total:
        blockers.append(f"complete_all_roles:{complete_count}/{expected_total}")
    return {
        "feature_run_dir_exists": feature_run_dir.is_dir(),
        "expected_total": expected_total,
        "expected_train": DEFAULT_EXPECTED_TRAIN,
        "expected_validation": DEFAULT_EXPECTED_VALIDATION,
        "complete_all_roles": complete_count,
        "missing_complete_all_roles": max(expected_total - complete_count, 0),
        "progress_fraction": progress,
        "progress_percent": round(progress * 100.0, 4),
        "by_role": by_role,
        "missing_by_role": missing_by_role,
        "subdirs": subdirs,
        "unknown_subdirs": unknown_subdirs,
        "complete_sample": sorted(complete_ids)[:20],
        "blockers": blockers,
    }


def docker_commands() -> dict[str, str]:
    repro_compose = "experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml"
    h001_compose = "experiments/H001_geom_reliability/compose.yaml"
    env = "env UID=$(id -u) GID=$(id -g)"
    return {
        "feature_audit": (
            f"sg docker -c '{env} docker compose -f {repro_compose} run --rm feature_audit'"
        ),
        "train_pilot": (
            f"sg docker -c '{env} docker compose -f {repro_compose} run --rm train_pilot'"
        ),
        "train_full": (
            f"sg docker -c '{env} docker compose -f {repro_compose} run --rm train_full'"
        ),
        "eval_preflight": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            "OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt "
            f"docker compose -f {repro_compose} run --rm eval_preflight'"
        ),
        "eval_h001_gt_objects": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            "OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt "
            f"docker compose -f {repro_compose} run --rm eval_h001_gt_objects'"
        ),
        "adapter_raw_dump": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            "OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl "
            f"docker compose -f {h001_compose} run --rm open3dsg_adapter_raw_dump'"
        ),
        "failure_analysis_real_guard": (
            "# blocked: add/run the real Open3DSG failure-analysis generator only after "
            "prediction JSONL, GT join, geometry join, and metrics exist; "
            f"the current Docker smoke service in {h001_compose} is not metric evidence"
        ),
    }


def gate_payload(
    repo_root: Path,
    feature_counts: dict[str, Any],
    feature_audit: dict[str, Any] | None,
    checkpoint_dir: Path,
    raw_dump_jsonl: Path,
    adapter_manifest: dict[str, Any] | None,
    metrics_json: Path,
) -> dict[str, Any]:
    checkpoint_files = sorted(checkpoint_dir.glob("*.ckpt")) if checkpoint_dir.is_dir() else []
    feature_dump_complete = feature_counts["complete_all_roles"] >= feature_counts["expected_total"]
    audit_status = None
    if feature_audit is not None:
        audit_status = feature_audit.get("selected_run_audit", {}).get("status") or feature_audit.get("status")
    adapter_status = adapter_manifest.get("status") if adapter_manifest else None
    return {
        "feature_dump_complete": {
            "passed": feature_dump_complete,
            "requires": "complete ids across object_valids, object_embeddings, relation_embeddings equal expected train+validation total",
            "blockers": feature_counts["blockers"],
        },
        "official_feature_audit": {
            "passed": audit_status == "ready",
            "status": audit_status or "not_run_or_missing",
            "requires": "Docker feature_audit manifest selected_run_audit.status == ready",
            "manifest": relpath(repo_root, repo_root / "experiments/H001_geom_reliability/sources/open3dsg/dump_features/manifest.json"),
        },
        "checkpoint_available": {
            "passed": bool(checkpoint_files),
            "checkpoint_count": len(checkpoint_files),
            "sample_checkpoints": [relpath(repo_root, path) for path in checkpoint_files[:5]],
            "requires": "train_pilot/full produces a checkpoint with explicit path recorded before eval",
        },
        "raw_dump_available": {
            "passed": raw_dump_jsonl.exists(),
            "raw_dump_jsonl": relpath(repo_root, raw_dump_jsonl),
            "requires": "identity-preserving Open3DSG raw dump with scan/subgraph/object-pair ids",
        },
        "adapter_ready": {
            "passed": adapter_status == "ready",
            "status": adapter_status or "not_run_or_missing",
            "requires": "open3dsg_adapter_raw_dump converts the raw dump to H001 prediction JSONL with zero errors",
        },
        "metrics_ready": {
            "passed": metrics_json.exists(),
            "metrics_json": relpath(repo_root, metrics_json),
            "requires": "Open3DSG prediction JSONL, GT join, geometry join, and H001 metric suite complete",
        },
    }


def status_from_gates(gates: dict[str, Any]) -> str:
    if not gates["feature_dump_complete"]["passed"]:
        return "waiting_for_feature_dump_completion"
    if not gates["official_feature_audit"]["passed"]:
        return "ready_for_feature_audit"
    if not gates["checkpoint_available"]["passed"]:
        return "ready_for_checkpoint_training"
    if not gates["raw_dump_available"]["passed"]:
        return "blocked_raw_dump_missing_after_checkpoint"
    if not gates["adapter_ready"]["passed"]:
        return "ready_for_open3dsg_adapter"
    if not gates["metrics_ready"]["passed"]:
        return "ready_for_open3dsg_metric_join"
    return "ready_for_real_failure_analysis_rows"


def render_commands(payload: dict[str, Any]) -> str:
    commands = payload["commands"]
    order = payload["handoff_order"]
    lines = [
        "# Open3DSG Post-Dump Handoff Commands",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "Run from the repository root.",
        "",
        "## Ordered Commands",
        "",
    ]
    for name in order:
        lines.extend([f"### {name}", "", "```bash", commands[name], "```", ""])
    lines.extend(
        [
            "## Hard Gates",
            "",
            "- Do not run `train_pilot` until Docker `feature_audit` reports `ready` on the official BLIP TopK5/scales3 run.",
            "- Do not run `train_full` until the pilot checkpoint path and logs are recorded.",
            "- Do not run Open3DSG evaluation without a recorded `OPEN3DSG_CHECKPOINT` path.",
            "- Do not run adapter/metrics until an identity-preserving raw dump exists.",
            "- Do not promote reduced/pilot feature routes to paper-result evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def render_report(payload: dict[str, Any]) -> str:
    feature = payload["feature_progress"]
    lines = [
        "# Open3DSG Post-Dump Handoff",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Feature Progress",
        "",
        f"- feature run: `{payload['inputs']['feature_run_dir']}`",
        f"- complete feature ids: `{feature['complete_all_roles']}/{feature['expected_total']}`",
        f"- progress: `{feature['progress_percent']:.2f}%`",
        f"- missing complete ids: `{feature['missing_complete_all_roles']}`",
        "",
        "## Gates",
        "",
    ]
    for gate_name, gate in payload["gates"].items():
        passed = gate.get("passed")
        lines.append(f"- `{gate_name}`: `{passed}`")
        blockers = gate.get("blockers")
        if blockers:
            lines.append(f"  blockers: `{', '.join(blockers[:5])}`")
    lines.extend(
        [
            "",
            "## Transition Rule",
            "",
            "The current handoff is a reproducibility/claim-boundary artifact only. It does not train Open3DSG, create a checkpoint, inspect metric failures, or create paper-result evidence.",
            "",
            "Real Open3DSG second-source claims remain blocked until feature audit, checkpoint reproduction, identity-preserving raw dump, prediction JSONL export, geometry join, metric run, and locked-schema failure-analysis rows are complete.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    feature_run_dir = resolve(repo_root, args.feature_run_dir)
    feature_audit_manifest = resolve(repo_root, args.feature_audit_manifest)
    checkpoint_dir = resolve(repo_root, args.checkpoint_dir)
    raw_dump_jsonl = resolve(repo_root, args.raw_dump_jsonl)
    adapter_manifest_path = resolve(repo_root, args.adapter_manifest)
    metrics_json = resolve(repo_root, args.metrics_json)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    expected_total = args.expected_train + args.expected_validation
    feature_counts = count_features(feature_run_dir, expected_total)
    feature_counts["expected_train"] = args.expected_train
    feature_counts["expected_validation"] = args.expected_validation
    feature_audit = load_json_if_exists(feature_audit_manifest)
    adapter_manifest = load_json_if_exists(adapter_manifest_path)
    gates = gate_payload(
        repo_root=repo_root,
        feature_counts=feature_counts,
        feature_audit=feature_audit,
        checkpoint_dir=checkpoint_dir,
        raw_dump_jsonl=raw_dump_jsonl,
        adapter_manifest=adapter_manifest,
        metrics_json=metrics_json,
    )
    status = status_from_gates(gates)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "inputs": {
            "feature_run_dir": relpath(repo_root, feature_run_dir),
            "feature_audit_manifest": relpath(repo_root, feature_audit_manifest),
            "checkpoint_dir": relpath(repo_root, checkpoint_dir),
            "raw_dump_jsonl": relpath(repo_root, raw_dump_jsonl),
            "adapter_manifest": relpath(repo_root, adapter_manifest_path),
            "metrics_json": relpath(repo_root, metrics_json),
        },
        "feature_progress": feature_counts,
        "gates": gates,
        "commands": docker_commands(),
        "handoff_order": [
            "feature_audit",
            "train_pilot",
            "train_full",
            "eval_preflight",
            "eval_h001_gt_objects",
            "adapter_raw_dump",
            "failure_analysis_real_guard",
        ],
        "claim_boundary": {
            "current_artifact": "post-dump command/gate handoff only",
            "not_evidence": [
                "Open3DSG checkpoint quality",
                "Open3DSG metric result",
                "real failure-analysis labels",
            ],
            "paper_claim_unblocked_after": [
                "official feature_audit ready",
                "Docker checkpoint reproduction",
                "identity-preserving raw dump",
                "prediction JSONL export",
                "geometry join and H001 metrics",
                "locked-schema real failure-analysis rows",
            ],
        },
    }
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "commands.md").write_text(render_commands(payload), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "complete_feature_ids": feature_counts["complete_all_roles"],
                "expected_feature_ids": expected_total,
                "progress_percent": feature_counts["progress_percent"],
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
