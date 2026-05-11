#!/usr/bin/env python3
"""Freeze Open3DSG checkpoint provenance and selection policy before training outputs exist."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_checkpoint_selection_v1"
STATUS_READY_MISSING = "checkpoint_selection_template_ready_checkpoint_missing"
STATUS_READY_WITH_CANDIDATES = "checkpoint_selection_template_ready_candidates_present"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro/output/checkpoints"),
    )
    parser.add_argument(
        "--feature-audit-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/dump_features/manifest.json"),
    )
    parser.add_argument(
        "--train-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--validation-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--env-check-report",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/env_check.md"),
    )
    parser.add_argument(
        "--cache-preflight-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/cache_preflight/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection"),
    )
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_checkpoint(path: Path, repo_root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "checkpoint_path": relpath(repo_root, path),
        "filename": path.name,
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "sha256": sha256_file(path),
        "source_stage": "unknown_until_record_filled",
        "paper_result_eligible": "unknown_until_policy_gate_passes",
    }


def record_template() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "open3dsg_checkpoint_provenance",
        "required_fields": {
            "checkpoint_id": "stable id assigned before H001 held-out metric inspection",
            "checkpoint_path": "relative path under local_dataset/Open3DSG_staged/training_repro/output/checkpoints",
            "checkpoint_sha256": "sha256 of checkpoint file",
            "checkpoint_size_bytes": "file size in bytes",
            "source_stage": "pilot | full | reduced_smoke",
            "paper_result_eligible": "true only for official BLIP TopK5/scales3 full-route checkpoints",
            "selection_role": "primary | fallback | smoke_only | rejected",
            "selection_reason": "predeclared reason, not based on H001 held-out metrics",
            "created_by_command": "exact Docker command that produced the checkpoint",
            "docker_image": "image tag or image id",
            "compose_file": "compose file path",
            "open3dsg_source_path": "source snapshot path",
            "feature_run_dir": "feature directory used by training",
            "feature_audit_manifest": "feature audit manifest path and hash",
            "train_split_manifest": "filtered train split/preprocess manifest path and hash",
            "validation_split_manifest": "filtered validation split/preprocess manifest path and hash",
            "env_check_artifact": "Docker env/CUDA report path",
            "cache_preflight_artifact": "model/cache preflight manifest path",
            "training_log_path": "log path under logs/ or Open3DSG output dir",
            "training_internal_metric_source": "training/validation metric source, if used for selection",
            "h001_eval_metric_seen_before_selection": "must be false for paper-result eligibility",
            "notes": "free text for non-selection operational details",
        },
    }


def selection_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_name": "h001_open3dsg_checkpoint_selection_policy",
        "selection_boundary": {
            "must_freeze_before": [
                "Open3DSG pilot checkpoint inspection",
                "Open3DSG full checkpoint inspection",
                "H001 raw dump generation",
                "H001 Open3DSG prediction JSONL export",
                "H001 Open3DSG metric computation",
            ],
            "forbidden_selection_signals": [
                "H001 held-out R@K",
                "H001 held-out violation rate",
                "H001 failure-analysis category distribution",
                "visual inspection of H001 held-out Open3DSG predictions",
            ],
            "allowed_selection_signals": [
                "predeclared route priority",
                "checkpoint file existence and checksum",
                "Docker preflight pass/fail",
                "official feature audit pass/fail",
                "training-internal train/validation logs that do not include H001 held-out scans",
            ],
        },
        "route_priority": [
            {
                "route": "official_full",
                "eligibility": "paper_result_eligible",
                "rule": "primary checkpoint if full route completes after official BLIP TopK5/scales3 feature audit pass",
            },
            {
                "route": "official_pilot",
                "eligibility": "pilot_evidence_only",
                "rule": "fallback for debugging/reporting progress; not final paper result unless full route is explicitly abandoned and claim is downgraded",
            },
            {
                "route": "reduced_smoke",
                "eligibility": "smoke_only_not_paper_result",
                "rule": "may validate plumbing only; never promote to paper-result evidence",
            },
        ],
        "primary_selection_rule": (
            "Select the first policy-eligible full-route checkpoint that satisfies provenance, "
            "feature-audit, Docker preflight, and no-held-out-selection gates. "
            "Do not choose among checkpoints using H001 held-out metric results."
        ),
        "reselection_rule": (
            "Changing the primary checkpoint after H001 held-out metric inspection requires a "
            "new schema version and must be reported as a deviation."
        ),
    }


def artifact_records(repo_root: Path, paths: dict[str, Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, path in paths.items():
        record: dict[str, Any] = {
            "name": name,
            "path": relpath(repo_root, path),
            "exists": path.exists(),
        }
        if path.exists() and path.is_file():
            record["sha256"] = sha256_file(path)
        records.append(record)
    return records


def source_statuses(paths: dict[str, Path]) -> dict[str, str | None]:
    payloads = {name: load_json_if_exists(path) for name, path in paths.items() if path.suffix == ".json"}
    feature = payloads.get("feature_audit_manifest")
    train_filter = payloads.get("train_filter_manifest")
    validation_filter = payloads.get("validation_filter_manifest")
    cache = payloads.get("cache_preflight_manifest")
    return {
        "feature_audit": (
            feature.get("selected_run_audit", {}).get("status") or feature.get("status")
            if isinstance(feature, dict)
            else None
        ),
        "train_filter": train_filter.get("status") if isinstance(train_filter, dict) else None,
        "validation_filter": validation_filter.get("status") if isinstance(validation_filter, dict) else None,
        "cache_preflight": cache.get("status") if isinstance(cache, dict) else None,
    }


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Checkpoint Selection",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Fact",
        "",
        "- The checkpoint provenance schema and selection policy are frozen before Open3DSG checkpoint outputs are inspected.",
        "- This artifact does not train Open3DSG, inspect held-out predictions, compute metrics, or select a real checkpoint.",
        "- Reduced-route checkpoints are smoke-only unless the paper claim is explicitly downgraded.",
        "",
        "## Selection Gate",
        "",
        "- Primary selection must not use H001 held-out metric results.",
        "- Full-route checkpoints have priority over pilot checkpoints.",
        "- A checkpoint can be paper-result eligible only after official feature audit, Docker preflight, provenance, and no-held-out-selection gates pass.",
        "",
        "## Current Candidates",
        "",
        f"- checkpoint dir: `{payload['checkpoint_dir']}`",
        f"- candidate checkpoints: `{payload['candidate_count']}`",
        f"- official feature audit status: `{payload['source_statuses']['feature_audit']}`",
        f"- train filter status: `{payload['source_statuses']['train_filter']}`",
        f"- validation filter status: `{payload['source_statuses']['validation_filter']}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.extend(
        [
            "",
            "## Generated Files",
            "",
            "- `selection_policy.json`",
            "- `record_template.json`",
            "- `manifest.json`",
            "- `commands.md`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def build_commands() -> str:
    return """# Open3DSG Checkpoint Selection Commands

Freeze or refresh the checkpoint selection template:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_checkpoint_selection'
```

Use this template after `train_pilot` or `train_full` creates checkpoints. The primary checkpoint must be recorded before any H001 held-out Open3DSG metric or failure inspection.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    checkpoint_dir = resolve(repo_root, args.checkpoint_dir)
    source_paths = {
        "feature_audit_manifest": resolve(repo_root, args.feature_audit_manifest),
        "train_filter_manifest": resolve(repo_root, args.train_filter_manifest),
        "validation_filter_manifest": resolve(repo_root, args.validation_filter_manifest),
        "env_check_report": resolve(repo_root, args.env_check_report),
        "cache_preflight_manifest": resolve(repo_root, args.cache_preflight_manifest),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = [inspect_checkpoint(path, repo_root) for path in sorted(checkpoint_dir.glob("*.ckpt"))] if checkpoint_dir.is_dir() else []
    blockers: list[str] = []
    if not checkpoint_dir.is_dir():
        blockers.append(f"missing_checkpoint_dir:{relpath(repo_root, checkpoint_dir)}")
    if not candidates:
        blockers.append("no_checkpoint_candidates")

    statuses = source_statuses(source_paths)
    if statuses["feature_audit"] != "ready":
        blockers.append(f"official_feature_audit_not_ready:{statuses['feature_audit']}")
    if statuses["train_filter"] != "filter_applied":
        blockers.append(f"train_filter_not_applied:{statuses['train_filter']}")
    if statuses["validation_filter"] != "filter_applied":
        blockers.append(f"validation_filter_not_applied:{statuses['validation_filter']}")

    policy = selection_policy()
    template = record_template()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": STATUS_READY_WITH_CANDIDATES if candidates else STATUS_READY_MISSING,
        "checkpoint_dir": relpath(repo_root, checkpoint_dir),
        "candidate_count": len(candidates),
        "candidate_checkpoints": candidates,
        "source_statuses": statuses,
        "feature_audit_status": statuses["feature_audit"],
        "source_artifacts": artifact_records(repo_root, source_paths),
        "selection_policy": "selection_policy.json",
        "record_template": "record_template.json",
        "blockers": blockers,
        "claim_boundary": (
            "This artifact freezes provenance and selection policy only. It is not a checkpoint, "
            "not Open3DSG metric evidence, and not permission to select a checkpoint using H001 held-out metrics."
        ),
        "next_action_after_checkpoint": (
            "Fill a checkpoint provenance record before raw dump/eval; then run eval_preflight with the selected checkpoint."
        ),
    }

    write_json(out_dir / "selection_policy.json", policy)
    write_json(out_dir / "record_template.json", template)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "commands.md").write_text(build_commands(), encoding="utf-8")
    (out_dir / "report.md").write_text(build_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "candidate_count": manifest["candidate_count"],
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
