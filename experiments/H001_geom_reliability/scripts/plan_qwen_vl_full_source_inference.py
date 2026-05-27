#!/usr/bin/env python3
"""Freeze Qwen-VL full-source sharded inference runner policy without inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_qwen_vl_full_source_inference_plan_v1"
DEFAULT_QWEN_ROOT = "experiments/H001_geom_reliability/sources/qwen_vl"
DEFAULT_INPUT_DIR = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_input"
DEFAULT_CROP_DIR = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_crops/all"
DEFAULT_OUT = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan"
DEFAULT_RUNTIME_OUT = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime"
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
MODEL_DIR = (
    "local_dataset/model_cache/huggingface/qwen_vl/"
    "Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--qwen-root", type=Path, default=Path(DEFAULT_QWEN_ROOT))
    parser.add_argument("--input-dir", type=Path, default=Path(DEFAULT_INPUT_DIR))
    parser.add_argument("--crop-dir", type=Path, default=Path(DEFAULT_CROP_DIR))
    parser.add_argument("--runtime-out", type=Path, default=Path(DEFAULT_RUNTIME_OUT))
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            line = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
            handle.write(line)
            handle.write("\n")
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def runtime_paths(runtime_out: Path, shard_id: str) -> dict[str, Path]:
    return {
        "raw_response_jsonl": runtime_out / "raw_response" / f"{shard_id}.jsonl",
        "predictions_jsonl": runtime_out / "predictions" / f"{shard_id}.jsonl",
        "completed_jsonl": runtime_out / "progress" / f"{shard_id}.completed.jsonl",
        "manifest": runtime_out / "manifests" / f"{shard_id}.json",
        "dry_run_manifest": runtime_out / "dry_runs" / f"{shard_id}.json",
        "report": runtime_out / "reports" / f"{shard_id}.md",
    }


def build_shard_plan(repo_root: Path, shards: list[dict[str, Any]], runtime_out: Path) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for shard in shards:
        shard_id = str(shard["shard_id"])
        paths = runtime_paths(runtime_out, shard_id)
        log = f"logs/qwen_vl_full_source_infer_{shard_id}_${{ts}}.log"
        exit_file = f"logs/qwen_vl_full_source_infer_{shard_id}_${{ts}}.exit"
        dry_log = f"logs/qwen_vl_full_source_infer_dry_run_{shard_id}_${{ts}}.log"
        dry_exit = f"logs/qwen_vl_full_source_infer_dry_run_{shard_id}_${{ts}}.exit"
        planned.append(
            {
                "shard_id": shard_id,
                "row_start": int(shard["row_start"]),
                "row_end_exclusive": int(shard["row_end_exclusive"]),
                "row_count": int(shard["row_count"]),
                "input_jsonl": shard["input_jsonl"],
                "outputs": {key: relpath(repo_root, value) for key, value in paths.items()},
                "dry_run_log_template": dry_log,
                "dry_run_exit_template": dry_exit,
                "infer_log_template": log,
                "infer_exit_template": exit_file,
                "dry_run_command": (
                    "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
                    f"QWEN_VL_FULL_SOURCE_SHARD_ID={shard_id} "
                    "docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml "
                    "run --rm qwen_vl_full_source_infer_dry_run'"
                ),
                "infer_command": (
                    "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
                    f"QWEN_VL_FULL_SOURCE_SHARD_ID={shard_id} "
                    "docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml "
                    "run --rm qwen_vl_full_source_infer_shard'"
                ),
                "resume_rule": "skip record_id values present in completed_jsonl; append raw_response/prediction/completed rows; never delete partial output unless --overwrite is explicit",
            }
        )
    return planned


def build_contract(repo_root: Path, input_manifest: dict[str, Any], crop_manifest: dict[str, Any]) -> dict[str, Any]:
    counts = input_manifest.get("counts", {})
    crop_counts = crop_manifest.get("counts", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "full_source_inference_runner_frozen_no_inference",
        "role": "third_semantic_source_modern_vlm_extension",
        "runner_script": "experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_inference.py",
        "docker_compose": "experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml",
        "dry_run_service": "qwen_vl_full_source_infer_dry_run",
        "inference_service": "qwen_vl_full_source_infer_shard",
        "model": {
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "local_dir": MODEL_DIR,
        },
        "prompt_and_decoding": {
            "prompt_version": "semantic_only_v1",
            "temperature": 0.0,
            "top_p": 1.0,
            "max_new_tokens": 256,
            "seed": 20260527,
            "do_sample": False,
        },
        "scope": {
            "universe_rows": counts.get("universe_rows"),
            "inferable_input_rows": counts.get("input_rows"),
            "missing_rows": counts.get("missing_rows"),
            "shards": counts.get("shards"),
            "verified_unique_pair_crops": crop_counts.get("verified_existing"),
            "crop_preflight_status": crop_manifest.get("status"),
        },
        "resume_policy": {
            "resume_key": "record_id",
            "completed_file": "full_source_runtime/progress/<shard_id>.completed.jsonl",
            "append_outputs": [
                "full_source_runtime/raw_response/<shard_id>.jsonl",
                "full_source_runtime/predictions/<shard_id>.jsonl",
                "full_source_runtime/progress/<shard_id>.completed.jsonl",
            ],
            "overwrite_rule": "outputs may be deleted only by passing --overwrite explicitly",
            "completion_check": "prediction row count and completed row count must match the planned shard row_count, or the run is partial",
        },
        "promotion_rule": {
            "paper_metric": False,
            "replacement_for_vlsat_anchor": False,
            "replacement_for_open3dsg_anchor": False,
            "metric_promotion_requires": [
                "all shard manifests complete",
                "raw-response contract validation",
                "prediction-row adapter export",
                "H001 geometry join",
                "R@K and Violation@K metrics",
                "controls",
                "bootstrap CI if reported",
                "qualitative/failure audit",
            ],
        },
        "non_leakage": [
            "semantic-only prompt must not include p_geom_valid",
            "semantic-only prompt must not include verifier labels or GT labels",
            "geometry summaries are not used in the semantic-only prompt",
        ],
    }


def commands_md(repo_root: Path, out_dir: Path) -> str:
    rel_out = relpath(repo_root, out_dir)
    return f"""# Qwen-VL Full-Source Inference Runner Commands

Generate this plan:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_inference_plan'
```

Build the Qwen runtime image after runner changes:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build qwen_vl_full_source_infer_dry_run qwen_vl_full_source_infer_shard'
```

Dry-run one shard without model load or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_dry_run'
```

Launch one inference shard in a timestamped background job:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
shard=qwen_full_source_shard_0000
tmux new-session -d -s h001_qwen_vl_infer_${{shard}} "cd /home/yoohyun/research && bash -lc 'sg docker -c '\\''env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=${{shard}} docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_shard'\\''; rc=\\$?; printf \"%s\\n\" \"\\$rc\" > logs/qwen_vl_full_source_infer_${{shard}}_${{ts}}.exit; exit \"\\$rc\"' > logs/qwen_vl_full_source_infer_${{shard}}_${{ts}}.log 2>&1"
```

Plan outputs:

- `{rel_out}/manifest.json`
- `{rel_out}/runner_contract.json`
- `{rel_out}/shards.jsonl`
- `{rel_out}/commands.md`
- `{rel_out}/report.md`
"""


def report_md(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    return f"""# Qwen-VL Full-Source Inference Runner Plan

Status: `{manifest['status']}`
Created at: `{manifest['created_at']}`

## Scope

- inferable input rows: `{counts['input_rows']}`
- missing rows: `{counts['missing_rows']}`
- shards: `{counts['shards']}`
- verified unique pair crops: `{counts['verified_unique_pair_crops']}`
- target role: `third_semantic_source_modern_vlm_extension`

## Policy

- The runner is frozen, but no Qwen model load or full-source inference is run by this plan.
- Inference must run shard-wise through Docker with timestamped logs under `logs/`.
- Resume key is `record_id`; partial shard outputs are append-resumed via `completed.jsonl`.
- Qwen outputs remain non-metric until contract validation, adapter export, geometry join, metrics, controls, bootstrap, and audit complete.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    qwen_root = resolve(repo_root, args.qwen_root)
    input_dir = resolve(repo_root, args.input_dir)
    crop_dir = resolve(repo_root, args.crop_dir)
    runtime_out = resolve(repo_root, args.runtime_out)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_manifest = load_json(input_dir / "manifest.json")
    crop_manifest = load_json(crop_dir / "manifest.json")
    status = load_json(qwen_root / "status.json")
    runtime_smoke = load_json(qwen_root / "runtime_smoke/tiny_inference/manifest.json")
    shards = read_jsonl(input_dir / "shards.jsonl")
    planned_shards = build_shard_plan(repo_root, shards, runtime_out)
    runner_contract = build_contract(repo_root, input_manifest, crop_manifest)

    blockers: list[str] = []
    if input_manifest.get("status") != "full_source_input_ready_with_missing_rows_no_inference":
        blockers.append(f"input_status:{input_manifest.get('status')}")
    if crop_manifest.get("status") != "full_source_crop_preflight_ready_no_inference":
        blockers.append(f"crop_status:{crop_manifest.get('status')}")
    input_rows = input_manifest.get("counts", {}).get("input_rows")
    crop_rows = crop_manifest.get("counts", {}).get("selected_input_rows")
    if input_rows != crop_rows:
        blockers.append(f"input_crop_row_mismatch:{input_rows}!={crop_rows}")
    if runtime_smoke.get("status") != "tiny_inference_smoke_passed":
        blockers.append(f"runtime_smoke_status:{runtime_smoke.get('status')}")

    shards_sha = write_jsonl(out_dir / "shards.jsonl", planned_shards)
    write_json(out_dir / "runner_contract.json", runner_contract)
    write_text(out_dir / "commands.md", commands_md(repo_root, out_dir))

    counts = {
        "input_rows": input_rows,
        "missing_rows": input_manifest.get("counts", {}).get("missing_rows"),
        "shards": len(planned_shards),
        "planned_rows": sum(int(item["row_count"]) for item in planned_shards),
        "verified_unique_pair_crops": crop_manifest.get("counts", {}).get("verified_existing"),
    }
    family_counts = Counter()
    for item in planned_shards:
        family_counts.update({"planned_shards": 1})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "full_source_inference_runner_frozen_no_inference" if not blockers else "blocked_full_source_inference_runner_plan",
        "blockers": blockers,
        "role": "third_semantic_source_modern_vlm_extension",
        "paper_metric": False,
        "counts": counts,
        "inputs": {
            "qwen_status": relpath(repo_root, qwen_root / "status.json"),
            "input_manifest": relpath(repo_root, input_dir / "manifest.json"),
            "input_jsonl": relpath(repo_root, input_dir / "input.jsonl"),
            "input_jsonl_sha256": sha256_file(input_dir / "input.jsonl"),
            "crop_manifest": relpath(repo_root, crop_dir / "manifest.json"),
            "runtime_smoke_manifest": relpath(repo_root, qwen_root / "runtime_smoke/tiny_inference/manifest.json"),
        },
        "outputs": {
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "runner_contract": relpath(repo_root, out_dir / "runner_contract.json"),
            "shards_jsonl": relpath(repo_root, out_dir / "shards.jsonl"),
            "commands": relpath(repo_root, out_dir / "commands.md"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "hashes": {
            "planned_shards_jsonl_sha256": shards_sha,
        },
        "qwen_status_snapshot": {
            "status": status.get("status"),
            "runtime_smoke": status.get("runtime_gpu_smoke", {}).get("status"),
            "crop_status": status.get("full_source_crop_render", {}).get("status"),
        },
        "next_action": "Run qwen_vl_full_source_infer_dry_run for shard 0000, then launch inference shards only as background jobs.",
    }
    write_json(out_dir / "manifest.json", manifest)
    write_text(out_dir / "report.md", report_md(manifest))
    print(json.dumps({"status": manifest["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
