#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pickle
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_feature_audit_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Open3DSG dumped 2D feature outputs for H001 training reproduction."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--feature-root",
        type=Path,
        default=None,
        help="Feature root. Defaults to local_dataset/Open3DSG_staged/training_repro/output/features.",
    )
    parser.add_argument(
        "--preprocessed-root",
        type=Path,
        default=None,
        help="Preprocessed root. Defaults to local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/preprocessed.",
    )
    parser.add_argument(
        "--relationships-root",
        type=Path,
        default=None,
        help="3DSSG_subset root. Defaults to local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Audit artifact dir. Defaults to experiments/H001_geom_reliability/sources/open3dsg/dump_features.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Specific clip_features_* run dir to audit. Defaults to latest under feature-root.",
    )
    parser.add_argument(
        "--inspect-pickles",
        action="store_true",
        help="Load preprocessed pickles to read scan_id. Default derives scan_id from relationship metadata for fast coverage audit.",
    )
    parser.add_argument("--write", action="store_true", help="Write manifest.json and report.md.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_relationships(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    scans = payload.get("scans", [])
    if not isinstance(scans, list):
        raise ValueError(f"Invalid relationships file: {path}")
    return scans


def split_suffix(split_value: Any) -> str:
    return str(hex(int(split_value)))[-1]


def expected_feature_ids(
    relationships: list[dict[str, Any]], preprocessed_root: Path, inspect_pickles: bool = False
) -> dict[str, Any]:
    ids: list[str] = []
    missing_preprocessed: list[dict[str, Any]] = []
    pickle_fallbacks: list[dict[str, Any]] = []
    duplicates: dict[str, int] = defaultdict(int)

    for item in relationships:
        scan = item.get("scan")
        split = item.get("split")
        if scan is None or split is None:
            missing_preprocessed.append(
                {"scan": scan, "split": split, "reason": "missing_scan_or_split"}
            )
            continue
        pkl_path = preprocessed_root / str(scan) / f"data_dict_{split_suffix(split)}.pkl"
        if not pkl_path.is_file():
            missing_preprocessed.append(
                {
                    "scan": scan,
                    "split": split,
                    "path": str(pkl_path),
                    "reason": "missing_preprocessed_pickle",
                }
            )
            continue
        if not inspect_pickles:
            feature_id = f"{scan}-{split_suffix(split)}"
            pickle_fallbacks.append(
                {
                    "scan": scan,
                    "split": split,
                    "path": str(pkl_path),
                    "fallback_feature_id": feature_id,
                    "reason": "metadata_derived_without_pickle_load",
                }
            )
            ids.append(feature_id)
            duplicates[feature_id] += 1
            continue
        try:
            with pkl_path.open("rb") as f:
                data_dict = pickle.load(f)
            feature_id = data_dict.get("scan_id")
        except ModuleNotFoundError as exc:
            feature_id = f"{scan}-{split_suffix(split)}"
            pickle_fallbacks.append(
                {
                    "scan": scan,
                    "split": split,
                    "path": str(pkl_path),
                    "fallback_feature_id": feature_id,
                    "reason": f"pickle_optional_dependency_missing:{exc}",
                }
            )
        except Exception as exc:  # noqa: BLE001 - audit should record every load failure.
            missing_preprocessed.append(
                {
                    "scan": scan,
                    "split": split,
                    "path": str(pkl_path),
                    "reason": f"pickle_load_failed:{exc}",
                }
            )
            continue
        if not feature_id:
            missing_preprocessed.append(
                {
                    "scan": scan,
                    "split": split,
                    "path": str(pkl_path),
                    "reason": "missing_scan_id_in_pickle",
                }
            )
            continue
        feature_id = str(feature_id)
        ids.append(feature_id)
        duplicates[feature_id] += 1

    duplicate_ids = {key: value for key, value in duplicates.items() if value > 1}
    return {
        "relationship_rows": len(relationships),
        "expected_ids": ids,
        "unique_expected_ids": sorted(set(ids)),
        "duplicate_expected_ids": duplicate_ids,
        "missing_preprocessed": missing_preprocessed,
        "pickle_fallbacks": pickle_fallbacks,
    }


def classify_feature_subdir(name: str) -> str:
    if name.startswith("export_obj_clip_emb"):
        return "object_embeddings"
    if name.startswith("export_obj_clip_valids"):
        return "object_valids"
    if name.startswith("export_rel_clip_emb"):
        return "relation_embeddings"
    return "unknown"


def list_feature_runs(feature_root: Path) -> list[dict[str, Any]]:
    if not feature_root.is_dir():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(feature_root.iterdir()):
        if not path.is_dir() or not path.name.startswith("clip_features_"):
            continue
        files = list(path.rglob("*.pt"))
        runs.append(
            {
                "name": path.name,
                "path": str(path),
                "mtime": path.stat().st_mtime,
                "pt_files": len(files),
                "subdirs": sorted(child.name for child in path.iterdir() if child.is_dir()),
            }
        )
    return sorted(runs, key=lambda item: (item["mtime"], item["name"]))


def audit_run(run_dir: Path, expected_by_split: dict[str, dict[str, Any]]) -> dict[str, Any]:
    subdir_records: list[dict[str, Any]] = []
    role_to_ids: dict[str, set[str]] = defaultdict(set)
    unknown_dirs: list[str] = []

    if run_dir.is_dir():
        for subdir in sorted(child for child in run_dir.iterdir() if child.is_dir()):
            role = classify_feature_subdir(subdir.name)
            ids = {path.stem for path in subdir.glob("*.pt") if path.is_file()}
            subdir_records.append(
                {
                    "name": subdir.name,
                    "role": role,
                    "pt_files": len(ids),
                    "sample_ids": sorted(ids)[:5],
                }
            )
            if role == "unknown":
                unknown_dirs.append(subdir.name)
            else:
                role_to_ids[role].update(ids)

    required_roles = ["object_embeddings", "object_valids", "relation_embeddings"]
    expected_all: set[str] = set()
    split_coverage: dict[str, Any] = {}
    complete_all_roles: set[str] | None = None

    for role in required_roles:
        role_ids = role_to_ids.get(role, set())
        complete_all_roles = set(role_ids) if complete_all_roles is None else complete_all_roles & role_ids
    if complete_all_roles is None:
        complete_all_roles = set()

    for split_name, split_data in expected_by_split.items():
        expected_ids = set(split_data["unique_expected_ids"])
        expected_all.update(expected_ids)
        missing_by_role = {
            role: sorted(expected_ids - role_to_ids.get(role, set()))
            for role in required_roles
        }
        complete_for_split = expected_ids & complete_all_roles
        split_coverage[split_name] = {
            "expected_unique": len(expected_ids),
            "complete_all_roles": len(complete_for_split),
            "missing_complete": len(expected_ids - complete_for_split),
            "missing_complete_sample": sorted(expected_ids - complete_for_split)[:20],
            "missing_by_role": {role: len(ids) for role, ids in missing_by_role.items()},
            "missing_by_role_sample": {
                role: ids[:20] for role, ids in missing_by_role.items() if ids
            },
            "duplicate_expected_ids": split_data["duplicate_expected_ids"],
            "missing_preprocessed": len(split_data["missing_preprocessed"]),
            "missing_preprocessed_sample": split_data["missing_preprocessed"][:20],
            "pickle_fallbacks": len(split_data["pickle_fallbacks"]),
            "pickle_fallback_sample": split_data["pickle_fallbacks"][:20],
        }

    extras_by_role = {
        role: sorted(role_to_ids.get(role, set()) - expected_all) for role in required_roles
    }
    missing_all_complete = expected_all - complete_all_roles
    blockers: list[str] = []
    if not run_dir.is_dir():
        blockers.append(f"missing_run_dir:{run_dir}")
    missing_roles = [role for role in required_roles if not role_to_ids.get(role)]
    for role in missing_roles:
        blockers.append(f"missing_feature_role:{role}")
    for split_name, split_data in expected_by_split.items():
        if split_data["missing_preprocessed"]:
            blockers.append(
                f"{split_name}_missing_preprocessed:{len(split_data['missing_preprocessed'])}"
            )
    if missing_all_complete:
        blockers.append(f"missing_complete_feature_ids:{len(missing_all_complete)}")

    return {
        "run_dir": str(run_dir),
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "required_roles": required_roles,
        "subdirs": subdir_records,
        "unknown_dirs": unknown_dirs,
        "expected_unique_total": len(expected_all),
        "complete_all_roles_total": len(expected_all & complete_all_roles),
        "missing_complete_total": len(missing_all_complete),
        "missing_complete_sample": sorted(missing_all_complete)[:50],
        "extras_by_role": {role: len(ids) for role, ids in extras_by_role.items()},
        "extras_by_role_sample": {
            role: ids[:20] for role, ids in extras_by_role.items() if ids
        },
        "split_coverage": split_coverage,
    }


def build_report(manifest: dict[str, Any], repo_root: Path) -> str:
    audit = manifest["selected_run_audit"]
    lines = [
        "# Open3DSG Feature Dump Audit",
        "",
        f"Status: `{audit['status']}`",
        f"Generated: `{manifest['generated_at']}`",
        f"ID strategy: `{manifest['id_strategy']}`",
        f"Feature root: `{rel_path(Path(manifest['feature_root']), repo_root)}`",
        f"Selected run: `{rel_path(Path(audit['run_dir']), repo_root)}`",
        "",
        "## Coverage",
        "",
        f"- Expected unique feature ids: {audit['expected_unique_total']}",
        f"- Complete ids across object embeddings, object valids, and relation embeddings: {audit['complete_all_roles_total']}",
        f"- Missing complete ids: {audit['missing_complete_total']}",
    ]
    if audit["blockers"]:
        lines.append(f"- Blockers: `{', '.join(audit['blockers'])}`")
    else:
        lines.append("- Blockers: none")
    lines.extend(["", "## Split Coverage", ""])
    for split_name, split_data in audit["split_coverage"].items():
        lines.extend(
            [
                f"### {split_name}",
                "",
                f"- Expected unique ids: {split_data['expected_unique']}",
                f"- Complete all roles: {split_data['complete_all_roles']}",
                f"- Missing complete: {split_data['missing_complete']}",
                f"- Missing preprocessed: {split_data['missing_preprocessed']}",
                "",
            ]
        )
    lines.extend(["## Feature Subdirs", ""])
    for subdir in audit["subdirs"]:
        lines.append(
            f"- `{subdir['name']}`: role `{subdir['role']}`, files {subdir['pt_files']}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    feature_root = (
        args.feature_root
        or repo_root / "local_dataset/Open3DSG_staged/training_repro/output/features"
    ).resolve()
    preprocessed_root = (
        args.preprocessed_root
        or repo_root
        / "local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/preprocessed"
    ).resolve()
    relationships_root = (
        args.relationships_root
        or repo_root / "local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset"
    ).resolve()
    output_dir = (
        args.output_dir
        or repo_root / "experiments/H001_geom_reliability/sources/open3dsg/dump_features"
    ).resolve()

    expected_by_split: dict[str, dict[str, Any]] = {}
    for split_name in ("train", "validation"):
        relationships_path = relationships_root / f"relationships_{split_name}.json"
        relationships = load_relationships(relationships_path)
        expected_by_split[split_name] = expected_feature_ids(
            relationships, preprocessed_root, inspect_pickles=args.inspect_pickles
        )

    runs = list_feature_runs(feature_root)
    if args.run_dir is not None:
        selected_run = args.run_dir.resolve()
    elif runs:
        selected_run = Path(runs[-1]["path"]).resolve()
    else:
        selected_run = feature_root / "missing_clip_features_run"

    audit = audit_run(selected_run, expected_by_split)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "repo_root": str(repo_root),
        "feature_root": str(feature_root),
        "preprocessed_root": str(preprocessed_root),
        "relationships_root": str(relationships_root),
        "id_strategy": "pickle_scan_id" if args.inspect_pickles else "relationship_scan_split_suffix",
        "feature_runs": runs,
        "selected_run_audit": audit,
    }

    if args.write:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (output_dir / "report.md").write_text(
            build_report(manifest, repo_root), encoding="utf-8"
        )

    print(json.dumps({"status": audit["status"], "blockers": audit["blockers"]}))


if __name__ == "__main__":
    main()
