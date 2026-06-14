#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_full_validation_feature_seed_v1"
ROLE_PREFIXES = {
    "object_embeddings": "export_obj_clip_emb",
    "object_valids": "export_obj_clip_valids",
    "relation_embeddings": "export_rel_clip_emb",
}
REQUIRED_ROLES = tuple(ROLE_PREFIXES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Open3DSG full-validation feature cache from compatible existing feature runs."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--relationships-json",
        type=Path,
        required=True,
        help="3DSSG_subset relationships JSON defining the full validation scope.",
    )
    parser.add_argument(
        "--preprocessed-root",
        type=Path,
        required=True,
        help="Open3DSG preprocessed root for the target full-validation runtime.",
    )
    parser.add_argument(
        "--target-run-dir",
        type=Path,
        required=True,
        help="Target clip_features_* run directory to materialize.",
    )
    parser.add_argument(
        "--source-run-dir",
        type=Path,
        action="append",
        required=True,
        help="Compatible source clip_features_* run directory. Can be passed multiple times.",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def split_suffix(split_value: Any) -> str:
    return str(hex(int(split_value)))[-1]


def role_dirs(run_dir: Path) -> dict[str, Path]:
    dirs: dict[str, Path] = {}
    if not run_dir.is_dir():
        return dirs
    for child in run_dir.iterdir():
        if not child.is_dir():
            continue
        for role, prefix in ROLE_PREFIXES.items():
            if child.name.startswith(prefix):
                dirs[role] = child
    return dirs


def load_expected_ids(relationships_json: Path, preprocessed_root: Path) -> dict[str, Any]:
    payload = json.loads(relationships_json.read_text(encoding="utf-8"))
    scans = payload.get("scans", [])
    expected: list[str] = []
    missing_preprocessed: list[dict[str, Any]] = []
    for row in scans:
        scan = row.get("scan")
        split = row.get("split")
        if scan is None or split is None:
            missing_preprocessed.append({"scan": scan, "split": split, "reason": "missing_scan_or_split"})
            continue
        suffix = split_suffix(split)
        pkl_path = preprocessed_root / str(scan) / f"data_dict_{suffix}.pkl"
        if not pkl_path.is_file():
            missing_preprocessed.append(
                {
                    "scan": str(scan),
                    "split": int(split),
                    "feature_id": f"{scan}-{suffix}",
                    "path": str(pkl_path),
                    "reason": "missing_preprocessed_pickle",
                }
            )
            continue
        expected.append(f"{scan}-{suffix}")
    return {
        "relationship_rows": len(scans),
        "expected_ids": sorted(set(expected)),
        "missing_preprocessed": missing_preprocessed,
    }


def complete_ids(run_dir: Path) -> set[str]:
    dirs = role_dirs(run_dir)
    role_id_sets: list[set[str]] = []
    for role in REQUIRED_ROLES:
        role_dir = dirs.get(role)
        if role_dir is None:
            role_id_sets.append(set())
        else:
            role_id_sets.append({path.stem for path in role_dir.glob("*.pt") if path.is_file()})
    if not role_id_sets:
        return set()
    complete = role_id_sets[0]
    for ids in role_id_sets[1:]:
        complete &= ids
    return complete


def find_source_for_id(source_dirs: list[Path], feature_id: str) -> tuple[Path, dict[str, Path]] | None:
    for source_dir in source_dirs:
        dirs = role_dirs(source_dir)
        if all(role in dirs and (dirs[role] / f"{feature_id}.pt").is_file() for role in REQUIRED_ROLES):
            return source_dir, {role: dirs[role] / f"{feature_id}.pt" for role in REQUIRED_ROLES}
    return None


def link_one(src: Path, dst: Path, dry_run: bool) -> str:
    if dst.exists():
        return "exists"
    if dry_run:
        return "dry_run"
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.link(src, dst)
    return "linked"


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    expected = load_expected_ids(args.relationships_json, args.preprocessed_root)
    target_dirs = role_dirs(args.target_run_dir)
    missing_target_role_dirs = [role for role in REQUIRED_ROLES if role not in target_dirs]
    if missing_target_role_dirs:
        # Mirror the first source run's role subdir names so target naming stays contract-compatible.
        first_source_dirs = role_dirs(args.source_run_dir[0])
        for role in missing_target_role_dirs:
            source_role_dir = first_source_dirs.get(role)
            if source_role_dir is None:
                continue
            target_role_dir = args.target_run_dir / source_role_dir.name
            if not args.dry_run:
                target_role_dir.mkdir(parents=True, exist_ok=True)
            target_dirs[role] = target_role_dir

    before_complete = complete_ids(args.target_run_dir)
    expected_ids = set(expected["expected_ids"])
    missing_before = sorted(expected_ids - before_complete)

    hardlinked_ids: list[str] = []
    missing_in_sources: list[str] = []
    operations: dict[str, int] = defaultdict(int)
    source_usage: dict[str, int] = defaultdict(int)

    for feature_id in missing_before:
        source_record = find_source_for_id(args.source_run_dir, feature_id)
        if source_record is None:
            missing_in_sources.append(feature_id)
            continue
        source_dir, source_paths = source_record
        for role, src in source_paths.items():
            target_role_dir = target_dirs[role]
            status = link_one(src, target_role_dir / f"{feature_id}.pt", args.dry_run)
            operations[status] += 1
        hardlinked_ids.append(feature_id)
        source_usage[str(source_dir)] += 1

    after_complete = complete_ids(args.target_run_dir) if not args.dry_run else before_complete | set(hardlinked_ids)
    missing_after = sorted(expected_ids - after_complete)
    blockers: list[str] = []
    if expected["missing_preprocessed"]:
        blockers.append(f"missing_preprocessed:{len(expected['missing_preprocessed'])}")
    if missing_after:
        blockers.append(f"missing_complete_features_after_seed:{len(missing_after)}")
    if missing_in_sources:
        blockers.append(f"missing_in_source_runs:{len(missing_in_sources)}")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "feature_seed_ready_with_caveats" if blockers else "feature_seed_ready",
        "generated_at": utc_now(),
        "dry_run": args.dry_run,
        "relationships_json": rel_path(args.relationships_json, repo_root),
        "preprocessed_root": rel_path(args.preprocessed_root, repo_root),
        "target_run_dir": rel_path(args.target_run_dir, repo_root),
        "source_run_dirs": [rel_path(path, repo_root) for path in args.source_run_dir],
        "expected_feature_ids": len(expected_ids),
        "target_complete_before": len(before_complete),
        "target_missing_before": len(missing_before),
        "hardlinked_ids": len(hardlinked_ids),
        "hardlinked_id_sample": hardlinked_ids[:20],
        "source_usage": {rel_path(Path(path), repo_root): count for path, count in source_usage.items()},
        "operations": dict(operations),
        "target_complete_after": len(after_complete),
        "target_missing_after": len(missing_after),
        "target_missing_after_sample": missing_after[:20],
        "missing_in_sources": len(missing_in_sources),
        "missing_in_sources_sample": missing_in_sources[:20],
        "missing_preprocessed": len(expected["missing_preprocessed"]),
        "missing_preprocessed_sample": expected["missing_preprocessed"][:20],
        "blockers": blockers,
        "claim_limit": "Feature seeding only materializes compatible Docker-generated Open3DSG feature caches; remaining missing preprocess contexts must be reported as source-runtime caveats.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Open3DSG Full-Validation Feature Seed",
        "",
        f"- Status: `{manifest['status']}`",
        f"- Expected feature ids with preprocess: {manifest['expected_feature_ids']}",
        f"- Target complete before: {manifest['target_complete_before']}",
        f"- Hardlinked ids: {manifest['hardlinked_ids']}",
        f"- Target complete after: {manifest['target_complete_after']}",
        f"- Missing after seed: {manifest['target_missing_after']}",
        f"- Missing preprocess contexts: {manifest['missing_preprocessed']}",
        f"- Source usage: `{manifest['source_usage']}`",
        "",
        "This is not a metric result. It records cache materialization before Docker feature audit, raw dump, adapter export, geometry join, metrics, controls, bootstrap CI, and table/caveat regeneration.",
    ]
    (out_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "blockers": blockers, "hardlinked_ids": len(hardlinked_ids)}))
    return 0 if not missing_after and not missing_in_sources else 1


if __name__ == "__main__":
    raise SystemExit(main())
