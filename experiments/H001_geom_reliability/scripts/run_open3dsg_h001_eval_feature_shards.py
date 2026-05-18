#!/usr/bin/env python3
"""Run bounded Open3DSG H001 eval feature shards until completion or failure."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CHECKPOINT = (
    "/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/"
    "363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/"
    "epoch=13-step=13104.ckpt"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--compose",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml"),
    )
    parser.add_argument(
        "--feature-run-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/h001_runtime/output/features/"
            "clip_features_h001_eval_blip_top5_scales3"
        ),
    )
    parser.add_argument(
        "--relationships",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/"
            "relationships_validation.json"
        ),
    )
    parser.add_argument(
        "--preprocessed-root",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/h001_runtime/output/datasets/"
            "OpenSG_3RScan/preprocessed"
        ),
    )
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--max-new-ids", type=int, default=5)
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="0 means run until covered scope is complete or an iteration fails.",
    )
    parser.add_argument("--blip-embed-chunk-size", type=int, default=1)
    parser.add_argument("--blip-projector-chunk-size", type=int, default=1)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def split_suffix(split_value: Any) -> str:
    return str(hex(int(split_value)))[-1]


def expected_loadable_ids(relationships_path: Path, preprocessed_root: Path) -> list[str]:
    payload = json.loads(relationships_path.read_text(encoding="utf-8"))
    ids: list[str] = []
    for item in payload.get("scans", []):
        scan = item.get("scan")
        split = item.get("split")
        if scan is None or split is None:
            continue
        suffix = split_suffix(split)
        pkl_path = preprocessed_root / str(scan) / f"data_dict_{suffix}.pkl"
        if pkl_path.is_file():
            ids.append(f"{scan}-{suffix}")
    return ids


def feature_role_dirs(feature_run_dir: Path) -> list[Path]:
    if not feature_run_dir.is_dir():
        return []
    return sorted(path for path in feature_run_dir.iterdir() if path.is_dir())


def complete_feature_ids(feature_run_dir: Path) -> set[str]:
    role_dirs = feature_role_dirs(feature_run_dir)
    role_sets = [{path.stem for path in role_dir.glob("*.pt")} for role_dir in role_dirs]
    if not role_sets:
        return set()
    return set.intersection(*role_sets)


def first_missing(loadable_ids: list[str], complete_ids: set[str]) -> str | None:
    for feature_id in loadable_ids:
        if feature_id not in complete_ids:
            return feature_id
    return None


def count_total_pt(feature_run_dir: Path) -> int:
    return sum(1 for role_dir in feature_role_dirs(feature_run_dir) for _ in role_dir.glob("*.pt"))


def run_shard(args: argparse.Namespace, repo_root: Path) -> int:
    env = os.environ.copy()
    env.update(
        {
            "UID": str(os.getuid()),
            "GID": str(os.getgid()),
            "OPEN3DSG_CHECKPOINT": args.checkpoint,
            "OPEN3DSG_FEATURE_SHARD_ONLY_MISSING": "1",
            "OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS": str(args.max_new_ids),
            "OPEN3DSG_BLIP_EMBED_CHUNK_SIZE": str(args.blip_embed_chunk_size),
            "OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE": str(args.blip_projector_chunk_size),
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True,max_split_size_mb:64",
        }
    )
    cmd = [
        "docker",
        "compose",
        "-f",
        str(resolve(repo_root, args.compose)),
        "run",
        "--rm",
        "dump_features_h001_eval",
    ]
    print("H001 shard loop command:", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=repo_root, env=env, check=False).returncode


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    feature_run_dir = resolve(repo_root, args.feature_run_dir)
    relationships_path = resolve(repo_root, args.relationships)
    preprocessed_root = resolve(repo_root, args.preprocessed_root)
    loadable_ids = expected_loadable_ids(relationships_path, preprocessed_root)
    target = len(set(loadable_ids))
    iteration = 0

    print(
        json.dumps(
            {
                "event": "h001_eval_feature_shard_loop_start",
                "created_at": utc_now(),
                "target_loadable_ids": target,
                "max_new_ids": args.max_new_ids,
                "max_iterations": args.max_iterations,
                "feature_run_dir": str(feature_run_dir),
            },
            sort_keys=True,
        ),
        flush=True,
    )

    while True:
        iteration += 1
        complete_before = complete_feature_ids(feature_run_dir)
        before_count = len(complete_before)
        missing_before = first_missing(loadable_ids, complete_before)
        print(
            json.dumps(
                {
                    "event": "h001_eval_feature_shard_iteration_start",
                    "iteration": iteration,
                    "complete_before": before_count,
                    "target_loadable_ids": target,
                    "total_pt_before": count_total_pt(feature_run_dir),
                    "first_missing_before": missing_before,
                    "created_at": utc_now(),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if before_count >= target:
            print(
                json.dumps(
                    {
                        "event": "h001_eval_feature_shard_loop_complete",
                        "complete_ids": before_count,
                        "target_loadable_ids": target,
                        "created_at": utc_now(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0
        if args.max_iterations > 0 and iteration > args.max_iterations:
            print(
                json.dumps(
                    {
                        "event": "h001_eval_feature_shard_loop_paused_max_iterations",
                        "complete_ids": before_count,
                        "target_loadable_ids": target,
                        "created_at": utc_now(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0

        rc = run_shard(args, repo_root)
        complete_after = complete_feature_ids(feature_run_dir)
        after_count = len(complete_after)
        missing_after = first_missing(loadable_ids, complete_after)
        print(
            json.dumps(
                {
                    "event": "h001_eval_feature_shard_iteration_end",
                    "iteration": iteration,
                    "exit_code": rc,
                    "complete_before": before_count,
                    "complete_after": after_count,
                    "target_loadable_ids": target,
                    "total_pt_after": count_total_pt(feature_run_dir),
                    "first_missing_after": missing_after,
                    "created_at": utc_now(),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if rc != 0:
            return rc
        if after_count <= before_count:
            print(
                json.dumps(
                    {
                        "event": "h001_eval_feature_shard_loop_stopped_no_progress",
                        "complete_ids": after_count,
                        "target_loadable_ids": target,
                        "created_at": utc_now(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
