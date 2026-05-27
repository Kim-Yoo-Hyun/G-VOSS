#!/usr/bin/env python3
"""Run or dry-run Qwen-VL full-source inference shards."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_qwen_vl_runtime_smoke import (
    BASELINE_NAME,
    DEFAULT_MODEL_DIR,
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_REVISION,
    PROMPT_VERSION,
    build_prompt,
    cache_status,
    decoding,
    extract_strict_json,
    generate_response,
    gpu_is_busy,
    gpu_status,
    load_processor_and_model,
    package_status,
    pair_crop_path,
    relpath,
    resolve,
)
from validate_qwen_vl_contract import parse_response


SCHEMA_VERSION = "h001_qwen_vl_full_source_inference_v1"
PREDICTION_SCHEMA_VERSION = "h001_qwen_vl_prediction_v2"
RAW_RESPONSE_SCHEMA_VERSION = "h001_qwen_vl_raw_response_v1"
DEFAULT_INPUT_JSONL = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl"
DEFAULT_SHARDS_JSONL = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/shards.jsonl"
DEFAULT_OUT_ROOT = "experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dry_run", "infer_shard"], required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--input-jsonl", type=Path, default=Path(DEFAULT_INPUT_JSONL))
    parser.add_argument("--shards-jsonl", type=Path, default=Path(DEFAULT_SHARDS_JSONL))
    parser.add_argument("--shard-id", default=os.environ.get("QWEN_VL_FULL_SOURCE_SHARD_ID", "qwen_full_source_shard_0000"))
    parser.add_argument("--out-root", type=Path, default=Path(DEFAULT_OUT_ROOT))
    parser.add_argument("--model-id", default=os.environ.get("QWEN_VL_MODEL_ID", DEFAULT_MODEL_ID))
    parser.add_argument("--model-revision", default=os.environ.get("QWEN_VL_MODEL_REVISION", DEFAULT_MODEL_REVISION))
    parser.add_argument("--model-dir", type=Path, default=Path(os.environ.get("QWEN_VL_LOCAL_DIR", DEFAULT_MODEL_DIR)))
    parser.add_argument("--baseline-run-id", default="qwen3_vl_4b_full_source_semantic_v1")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20260527)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-gpu-memory-used-mb", type=int, default=8192)
    parser.add_argument("--max-gpu-utilization", type=int, default=35)
    parser.add_argument("--fail-if-gpu-busy", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_jsonl_with_lines(path: Path) -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.strip():
                rows.append((json.loads(line), line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(canonical_line(row))
    handle.write("\n")
    handle.flush()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def load_shards(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["shard_id"]): row for row, _ in read_jsonl_with_lines(path)}


def select_shard_rows(
    rows: list[tuple[dict[str, Any], str]], shard: dict[str, Any], limit: int
) -> list[tuple[dict[str, Any], str]]:
    start = int(shard["row_start"])
    end = int(shard["row_end_exclusive"])
    selected = rows[start:end]
    if limit > 0:
        selected = selected[:limit]
    return selected


def completed_record_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for row, _ in read_jsonl_with_lines(path):
        record_id = row.get("record_id")
        if isinstance(record_id, str):
            ids.add(record_id)
    return ids


def output_paths(out_root: Path, shard_id: str) -> dict[str, Path]:
    return {
        "raw_response_jsonl": out_root / "raw_response" / f"{shard_id}.jsonl",
        "predictions_jsonl": out_root / "predictions" / f"{shard_id}.jsonl",
        "completed_jsonl": out_root / "progress" / f"{shard_id}.completed.jsonl",
        "manifest": out_root / "manifests" / f"{shard_id}.json",
        "dry_run_manifest": out_root / "dry_runs" / f"{shard_id}.json",
        "report": out_root / "reports" / f"{shard_id}.md",
    }


def prediction_row(
    input_row: dict[str, Any],
    input_line: str,
    raw_response: str,
    parser_status: str,
    predictions: list[dict[str, Any]],
    warnings: list[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "record_id": input_row["record_id"],
        "scan_id": input_row["scan_id"],
        "subgraph_id": input_row["subgraph_id"],
        "split": input_row.get("split", "held_out"),
        "subject_id": input_row["subject_id"],
        "object_id": input_row["object_id"],
        "predicate_family": input_row["predicate_family"],
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": args.baseline_run_id,
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "prompt_version": PROMPT_VERSION,
        "input_record_sha256": hashlib.sha256(input_line.encode("utf-8")).hexdigest(),
        "decoding": decoding(args),
        "raw_response": raw_response,
        "parser_status": parser_status,
        "predictions": predictions,
        "warnings": warnings,
    }


def raw_response_row(
    input_row: dict[str, Any],
    shard_id: str,
    raw_response: str,
    generated_text: str,
    status: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": RAW_RESPONSE_SCHEMA_VERSION,
        "record_id": input_row["record_id"],
        "scan_id": input_row["scan_id"],
        "subgraph_id": input_row["subgraph_id"],
        "subject_id": input_row["subject_id"],
        "object_id": input_row["object_id"],
        "predicate_family": input_row["predicate_family"],
        "shard_id": shard_id,
        "status": status,
        "raw_response": raw_response,
        "generated_text": generated_text,
        "warnings": warnings,
    }


def completed_row(input_row: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "record_id": input_row["record_id"],
        "status": status,
        "completed_at": utc_now(),
    }


def dry_run(
    repo_root: Path,
    selected_rows: list[tuple[dict[str, Any], str]],
) -> tuple[list[str], dict[str, Any]]:
    missing_crops: list[str] = []
    family_counts: Counter[str] = Counter()
    pair_paths: set[str] = set()
    for row, _ in selected_rows:
        family_counts[str(row.get("predicate_family"))] += 1
        try:
            crop_path = pair_crop_path(repo_root, row)
        except Exception as exc:  # noqa: BLE001
            missing_crops.append(f"{row.get('record_id')}:pair_crop_path_error:{type(exc).__name__}:{exc}")
            continue
        pair_paths.add(relpath(repo_root, crop_path))
        if not crop_path.exists():
            missing_crops.append(f"{row.get('record_id')}:missing_pair_crop:{relpath(repo_root, crop_path)}")
    return missing_crops, {
        "selected_rows": len(selected_rows),
        "unique_pair_crops": len(pair_paths),
        "family_counts": dict(family_counts),
    }


def run_inference(
    repo_root: Path,
    selected_rows: list[tuple[dict[str, Any], str]],
    paths: dict[str, Path],
    args: argparse.Namespace,
) -> dict[str, Any]:
    if args.overwrite:
        for key in ("raw_response_jsonl", "predictions_jsonl", "completed_jsonl"):
            paths[key].unlink(missing_ok=True)

    done = completed_record_ids(paths["completed_jsonl"])
    to_run = [(row, line) for row, line in selected_rows if row["record_id"] not in done]
    processor, model, runtime_meta = load_processor_and_model(resolve(repo_root, args.model_dir))
    parser_counts: Counter[str] = Counter()
    row_status_counts: Counter[str] = Counter()
    paths["raw_response_jsonl"].parent.mkdir(parents=True, exist_ok=True)
    paths["predictions_jsonl"].parent.mkdir(parents=True, exist_ok=True)
    paths["completed_jsonl"].parent.mkdir(parents=True, exist_ok=True)

    with paths["raw_response_jsonl"].open("a", encoding="utf-8") as raw_handle, paths[
        "predictions_jsonl"
    ].open("a", encoding="utf-8") as pred_handle, paths["completed_jsonl"].open(
        "a", encoding="utf-8"
    ) as completed_handle:
        for input_row, input_line in to_run:
            try:
                image_path = pair_crop_path(repo_root, input_row)
                generated = generate_response(processor, model, image_path, build_prompt(input_row), args)
                raw_response, extraction_warnings = extract_strict_json(generated)
                parser_status, predictions, parser_warnings = parse_response(
                    raw_response, list(input_row.get("candidate_predicates", []))
                )
                warnings = extraction_warnings + parser_warnings
                status = "ok"
            except Exception as exc:  # noqa: BLE001
                generated = ""
                raw_response = ""
                parser_status = "runtime_error"
                predictions = []
                warnings = [f"runtime_error:{type(exc).__name__}:{str(exc)[:300]}"]
                status = "runtime_error"
            append_jsonl(
                raw_handle,
                raw_response_row(input_row, args.shard_id, raw_response, generated, status, warnings),
            )
            append_jsonl(
                pred_handle,
                prediction_row(
                    input_row,
                    input_line,
                    raw_response,
                    parser_status,
                    predictions,
                    warnings,
                    args,
                ),
            )
            append_jsonl(completed_handle, completed_row(input_row, status))
            parser_counts[parser_status] += 1
            row_status_counts[status] += 1

    prediction_rows = count_lines(paths["predictions_jsonl"])
    raw_rows = count_lines(paths["raw_response_jsonl"])
    completed_rows = count_lines(paths["completed_jsonl"])
    return {
        "runtime": runtime_meta,
        "previously_completed_rows": len(done),
        "newly_attempted_rows": len(to_run),
        "prediction_rows": prediction_rows,
        "raw_response_rows": raw_rows,
        "completed_rows": completed_rows,
        "parser_status_counts_new": dict(parser_counts),
        "row_status_counts_new": dict(row_status_counts),
    }


def render_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Qwen-VL Full-Source Shard Runner",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        f"- mode: `{manifest['mode']}`",
        f"- shard id: `{manifest['shard_id']}`",
        f"- selected rows: `{counts['selected_rows']}`",
        f"- unique pair crops: `{counts.get('unique_pair_crops')}`",
        "",
        "## Outputs",
        "",
    ]
    for key, value in manifest["outputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    if manifest.get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in manifest["blockers"][:80])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_jsonl = resolve(repo_root, args.input_jsonl)
    shards_jsonl = resolve(repo_root, args.shards_jsonl)
    out_root = resolve(repo_root, args.out_root)
    model_dir = resolve(repo_root, args.model_dir)
    paths = output_paths(out_root, args.shard_id)

    input_rows = read_jsonl_with_lines(input_jsonl)
    shards = load_shards(shards_jsonl)
    if args.shard_id not in shards:
        raise ValueError(f"unknown_shard_id:{args.shard_id}")
    selected_rows = select_shard_rows(input_rows, shards[args.shard_id], args.limit)

    missing_crops, dry_counts = dry_run(repo_root, selected_rows)
    blockers = list(missing_crops)
    runtime_result: dict[str, Any] | None = None
    cache = cache_status(model_dir)
    gpu = gpu_status() if args.mode == "infer_shard" else {"available": None}
    packages = package_status() if args.mode == "infer_shard" else {}

    if args.mode == "infer_shard":
        if not cache["ready"]:
            blockers.extend(cache["errors"])
        missing_packages = [name for name, item in packages.items() if not item.get("available")]
        blockers.extend(f"missing_package:{name}" for name in missing_packages)
        if args.fail_if_gpu_busy and gpu_is_busy(gpu, args):
            blockers.append(
                "gpu_busy_or_unavailable:"
                f"memory_used_mb={gpu.get('memory_used_mb')},"
                f"utilization={gpu.get('utilization_gpu_percent')}"
            )
        if not blockers:
            runtime_result = run_inference(repo_root, selected_rows, paths, args)

    if args.mode == "dry_run":
        status = "full_source_inference_shard_dry_run_ready" if not blockers else "blocked_full_source_inference_shard_dry_run"
        write_json(paths["dry_run_manifest"], {})
        manifest_path = paths["dry_run_manifest"]
    elif blockers:
        status = "blocked_full_source_inference_shard"
        manifest_path = paths["manifest"]
    else:
        expected_rows = len(selected_rows)
        prediction_rows = int(runtime_result["prediction_rows"]) if runtime_result else 0
        if prediction_rows >= expected_rows:
            status = "full_source_inference_shard_complete"
        else:
            status = "full_source_inference_shard_partial"
        manifest_path = paths["manifest"]

    outputs = {
        "dry_run_manifest": relpath(repo_root, paths["dry_run_manifest"]),
        "manifest": relpath(repo_root, paths["manifest"]),
        "report": relpath(repo_root, paths["report"]),
        "raw_response_jsonl": relpath(repo_root, paths["raw_response_jsonl"]),
        "predictions_jsonl": relpath(repo_root, paths["predictions_jsonl"]),
        "completed_jsonl": relpath(repo_root, paths["completed_jsonl"]),
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "mode": args.mode,
        "status": status,
        "shard_id": args.shard_id,
        "role": "third_semantic_source_modern_vlm_extension",
        "paper_metric": False,
        "input": {
            "input_jsonl": relpath(repo_root, input_jsonl),
            "shards_jsonl": relpath(repo_root, shards_jsonl),
            "row_start": int(shards[args.shard_id]["row_start"]),
            "row_end_exclusive": int(shards[args.shard_id]["row_end_exclusive"]),
            "limit": args.limit,
        },
        "model": {
            "model_id": args.model_id,
            "model_revision": args.model_revision,
            "model_dir": relpath(repo_root, model_dir),
        },
        "decoding": decoding(args),
        "cache": cache if args.mode == "infer_shard" else {"checked": False},
        "packages": packages,
        "gpu": gpu,
        "counts": dry_counts,
        "runtime_result": runtime_result,
        "blockers": blockers,
        "outputs": outputs,
        "promotion_rule": {
            "replacement_for_vlsat_anchor": False,
            "replacement_for_open3dsg_anchor": False,
            "metric_promotion_requires": [
                "all_shards_complete",
                "contract_validation",
                "adapter_export",
                "geometry_join",
                "metrics",
                "controls",
                "bootstrap_ci_if_reported",
                "failure_audit",
            ],
        },
    }
    write_json(manifest_path, manifest)
    write_json(paths["report"].with_suffix(".json"), manifest)
    paths["report"].parent.mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "shard_id": args.shard_id, "out": relpath(repo_root, manifest_path)}, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
