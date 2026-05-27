#!/usr/bin/env python3
"""Run guarded Qwen-VL cache/runtime/tiny-inference smoke checks."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_qwen_vl_contract import parse_response


SCHEMA_VERSION = "h001_qwen_vl_runtime_smoke_v1"
PREDICTION_SCHEMA_VERSION = "h001_qwen_vl_prediction_v2"
BASELINE_NAME = "qwen_vl_semantic_source"
DEFAULT_MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
DEFAULT_MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
DEFAULT_MODEL_DIR = (
    "local_dataset/model_cache/huggingface/qwen_vl/"
    "Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17"
)
DEFAULT_INPUT_JSONL = "experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot/input.jsonl"
PROMPT_VERSION = "semantic_only_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["cache_verify", "preflight", "tiny_inference"], required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--input-jsonl", type=Path, default=Path(DEFAULT_INPUT_JSONL))
    parser.add_argument("--model-id", default=os.environ.get("QWEN_VL_MODEL_ID", DEFAULT_MODEL_ID))
    parser.add_argument(
        "--model-revision",
        default=os.environ.get("QWEN_VL_MODEL_REVISION", DEFAULT_MODEL_REVISION),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path(os.environ.get("QWEN_VL_LOCAL_DIR", DEFAULT_MODEL_DIR)),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/runtime_smoke"),
    )
    parser.add_argument("--baseline-run-id", default="qwen3_vl_4b_tiny_smoke_v1")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--max-gpu-memory-used-mb", type=int, default=8192)
    parser.add_argument("--max-gpu-utilization", type=int, default=35)
    parser.add_argument("--fail-if-gpu-busy", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_jsonl_with_lines(path: Path) -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append((json.loads(line), line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def run_text(command: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def package_status() -> dict[str, Any]:
    packages: dict[str, Any] = {}
    for package in ["torch", "transformers", "huggingface_hub", "qwen_vl_utils", "PIL"]:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            packages[package] = {"available": True, "version": version}
        except Exception as exc:  # noqa: BLE001
            packages[package] = {"available": False, "error": repr(exc)}
    return packages


def gpu_status() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total",
        "--format=csv,noheader,nounits",
    ]
    code, stdout, stderr = run_text(command)
    status: dict[str, Any] = {"available": code == 0, "returncode": code}
    if stderr:
        status["stderr"] = stderr[:500]
    if code != 0 or not stdout:
        return status
    first = stdout.splitlines()[0]
    parts = [part.strip() for part in first.split(",")]
    if len(parts) >= 5:
        status.update(
            {
                "timestamp": parts[0],
                "name": parts[1],
                "utilization_gpu_percent": int(float(parts[2])),
                "memory_used_mb": int(float(parts[3])),
                "memory_total_mb": int(float(parts[4])),
            }
        )
    return status


def cache_status(model_dir: Path) -> dict[str, Any]:
    files = [path for path in model_dir.rglob("*") if path.is_file()] if model_dir.exists() else []
    weights = [
        path
        for path in files
        if path.suffix in {".safetensors", ".bin", ".pt"} or path.name.endswith(".safetensors.index.json")
    ]
    required = ["config.json"]
    missing_required = [name for name in required if not (model_dir / name).is_file()]
    optional_processor = [
        "tokenizer_config.json",
        "preprocessor_config.json",
        "processor_config.json",
        "generation_config.json",
    ]
    present_optional = [name for name in optional_processor if (model_dir / name).is_file()]
    total_bytes = sum(path.stat().st_size for path in files)
    errors: list[str] = []
    if not model_dir.exists():
        errors.append("model_dir_missing")
    if missing_required:
        errors.extend(f"missing_required:{name}" for name in missing_required)
    if not weights:
        errors.append("no_weight_files")
    return {
        "model_dir": str(model_dir),
        "exists": model_dir.exists(),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "total_gb": round(total_bytes / (1024**3), 3),
        "weight_file_count": len(weights),
        "missing_required": missing_required,
        "present_optional": present_optional,
        "errors": errors,
        "ready": not errors,
    }


def gpu_is_busy(gpu: dict[str, Any], args: argparse.Namespace) -> bool:
    if not gpu.get("available"):
        return True
    memory_used = int(gpu.get("memory_used_mb", 0))
    utilization = int(gpu.get("utilization_gpu_percent", 0))
    return memory_used > args.max_gpu_memory_used_mb or utilization > args.max_gpu_utilization


def decoding(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "backend": "qwen_vl_runtime_smoke",
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
    }


def build_prompt(row: dict[str, Any]) -> str:
    candidates = ", ".join(row["candidate_predicates"])
    return (
        "You are given an indoor scene crop. The subject is marked with a red box "
        "and the object is marked with a blue box when boxes are visible.\n"
        f"Subject: {row['subject_label']} (id {row['subject_id']}).\n"
        f"Object: {row['object_label']} (id {row['object_id']}).\n"
        f"Allowed predicates: {candidates}.\n"
        "Use only the visual evidence and object labels. Do not assume hidden 3D geometry.\n"
        "Return strict JSON only, with this schema: "
        '{"answer_is_visible": true or false, "predictions": '
        '[{"predicate": "<allowed predicate>", "confidence": 0.0-1.0, '
        '"rationale_short": "<brief reason>"}]}. '
        "If no relation is visually supported, return an empty predictions list."
    )


def pair_crop_path(repo_root: Path, row: dict[str, Any]) -> Path:
    for item in row.get("crop_paths", []):
        if item.get("role") == "pair":
            return resolve(repo_root, Path(item["path"]))
    raise ValueError(f"row has no pair crop path: {row.get('record_id')}")


def extract_strict_json(text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    stripped = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()
        warnings.append("raw_response_code_fence_stripped")
    if not stripped.startswith("{") or not stripped.endswith("}"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]
            warnings.append("raw_response_json_substring_extracted")
    return stripped, warnings


def load_processor_and_model(model_dir: Path) -> tuple[Any, Any, dict[str, Any]]:
    import torch
    from transformers import AutoProcessor

    metadata: dict[str, Any] = {}
    processor = AutoProcessor.from_pretrained(
        str(model_dir), local_files_only=True, trust_remote_code=True
    )
    errors: list[str] = []
    model = None
    for class_name in [
        "AutoModelForImageTextToText",
        "AutoModelForVision2Seq",
        "AutoModelForCausalLM",
    ]:
        try:
            transformers = importlib.import_module("transformers")
            model_class = getattr(transformers, class_name)
            model = model_class.from_pretrained(
                str(model_dir),
                local_files_only=True,
                trust_remote_code=True,
                torch_dtype="auto",
                device_map="auto",
                low_cpu_mem_usage=True,
            )
            metadata["model_loader_class"] = class_name
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{class_name}:{type(exc).__name__}:{str(exc)[:240]}")
    if model is None:
        raise RuntimeError("; ".join(errors))
    metadata["processor_class"] = processor.__class__.__name__
    metadata["model_class"] = model.__class__.__name__
    metadata["torch_cuda_available"] = bool(torch.cuda.is_available())
    return processor, model, metadata


def generate_response(processor: Any, model: Any, image_path: Path, prompt: str, args: argparse.Namespace) -> str:
    from qwen_vl_utils import process_vision_info

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        do_sample=False,
        temperature=None,
        top_p=None,
    )
    if len(inputs.input_ids) != len(generated_ids):
        raise RuntimeError(
            f"generation_batch_size_mismatch:{len(inputs.input_ids)}!={len(generated_ids)}"
        )
    trimmed = [
        output_ids[len(input_ids) :]
        for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
    ]
    return processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]


def prediction_row(
    input_row: dict[str, Any],
    input_line: str,
    raw_response: str,
    extra_warnings: list[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    parser_status, predictions, warnings = parse_response(
        raw_response, list(input_row.get("candidate_predicates", []))
    )
    return {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "record_id": input_row["record_id"],
        "scan_id": input_row["scan_id"],
        "subgraph_id": input_row["subgraph_id"],
        "split": "smoke",
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
        "warnings": extra_warnings + warnings,
    }


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Runtime Smoke",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This is a runtime smoke gate only. It is not a paper metric and does not replace the Open3DSG reproduction anchor.",
        "",
        "## Model",
        "",
        f"- model id: `{manifest['model']['model_id']}`",
        f"- revision: `{manifest['model']['model_revision']}`",
        f"- local dir: `{manifest['model']['model_dir']}`",
        "",
        "## Cache",
        "",
        f"- ready: `{manifest['cache']['ready']}`",
        f"- file count: `{manifest['cache']['file_count']}`",
        f"- weight files: `{manifest['cache']['weight_file_count']}`",
        f"- total GB: `{manifest['cache']['total_gb']}`",
        "",
        "## GPU",
        "",
        f"- available: `{manifest['gpu'].get('available')}`",
        f"- memory used MB: `{manifest['gpu'].get('memory_used_mb')}`",
        f"- utilization %: `{manifest['gpu'].get('utilization_gpu_percent')}`",
        "",
    ]
    if "runtime" in manifest:
        lines.extend(
            [
                "## Runtime",
                "",
                f"- model loaded: `{manifest['runtime'].get('model_loaded')}`",
                f"- processor class: `{manifest['runtime'].get('processor_class')}`",
                f"- model class: `{manifest['runtime'].get('model_class')}`",
                "",
            ]
        )
    if "tiny_inference" in manifest:
        lines.extend(
            [
                "## Tiny Inference",
                "",
                f"- attempted rows: `{manifest['tiny_inference']['attempted_rows']}`",
                f"- output rows: `{manifest['tiny_inference']['output_rows']}`",
                f"- parser status counts: `{manifest['tiny_inference']['parser_status_counts']}`",
                "",
            ]
        )
    if manifest.get("blockers"):
        lines.extend(["## Blockers", ""])
        lines.extend(f"- `{item}`" for item in manifest["blockers"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_jsonl = resolve(repo_root, args.input_jsonl)
    model_dir = resolve(repo_root, args.model_dir)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cache = cache_status(model_dir)
    packages = package_status()
    gpu = gpu_status()
    blockers: list[str] = []
    runtime: dict[str, Any] = {"model_loaded": False}
    tiny: dict[str, Any] | None = None

    if args.mode == "cache_verify":
        status = "model_cache_ready" if cache["ready"] else "blocked_model_cache_missing"
        blockers.extend(cache["errors"])
    else:
        if not cache["ready"]:
            blockers.extend(cache["errors"])
        missing_packages = [name for name, item in packages.items() if not item.get("available")]
        if missing_packages:
            blockers.extend(f"missing_package:{name}" for name in missing_packages)
        busy = gpu_is_busy(gpu, args)
        if args.fail_if_gpu_busy and busy:
            blockers.append(
                "gpu_busy_or_unavailable:"
                f"memory_used_mb={gpu.get('memory_used_mb')},"
                f"utilization={gpu.get('utilization_gpu_percent')}"
            )
        status = "blocked_runtime_preflight" if blockers else "runtime_preflight_ready"

        processor = None
        model = None
        if not blockers:
            try:
                processor, model, runtime_meta = load_processor_and_model(model_dir)
                runtime.update(runtime_meta)
                runtime["model_loaded"] = True
                status = "runtime_preflight_passed"
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"model_load_failed:{type(exc).__name__}:{str(exc)[:500]}")
                status = "blocked_runtime_preflight"

        if args.mode == "tiny_inference" and not blockers and processor is not None and model is not None:
            rows = load_jsonl_with_lines(input_jsonl)[: args.limit]
            raw_rows: list[dict[str, Any]] = []
            output_rows: list[dict[str, Any]] = []
            row_errors: list[str] = []
            for input_row, input_line in rows:
                try:
                    image_path = pair_crop_path(repo_root, input_row)
                    generated = generate_response(
                        processor, model, image_path, build_prompt(input_row), args
                    )
                    raw_response, extraction_warnings = extract_strict_json(generated)
                    raw_rows.append(
                        {
                            "record_id": input_row["record_id"],
                            "raw_response": raw_response,
                            "generated_text": generated,
                        }
                    )
                    output_rows.append(
                        prediction_row(
                            input_row, input_line, raw_response, extraction_warnings, args
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    row_errors.append(
                        f"{input_row.get('record_id', 'unknown')}:{type(exc).__name__}:{str(exc)[:300]}"
                    )
            write_jsonl(out_dir / "raw_response.jsonl", raw_rows)
            write_jsonl(out_dir / "predictions.jsonl", output_rows)
            tiny = {
                "attempted_rows": len(rows),
                "output_rows": len(output_rows),
                "raw_response_jsonl": relpath(repo_root, out_dir / "raw_response.jsonl"),
                "predictions_jsonl": relpath(repo_root, out_dir / "predictions.jsonl"),
                "parser_status_counts": dict(Counter(row["parser_status"] for row in output_rows)),
                "row_errors": row_errors,
            }
            if row_errors:
                blockers.extend(row_errors)
                status = "tiny_inference_smoke_partial_or_failed"
            else:
                status = "tiny_inference_smoke_passed"

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "mode": args.mode,
        "status": status,
        "blockers": blockers,
        "model": {
            "model_id": args.model_id,
            "model_revision": args.model_revision,
            "model_dir": relpath(repo_root, model_dir),
        },
        "cache": cache,
        "packages": packages,
        "gpu": gpu,
        "promotion_rule": {
            "paper_metric": False,
            "replacement_for_open3dsg_anchor": False,
            "allowed_role": "modern_vlm_semantic_source_extension_smoke",
        },
        "outputs": {
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
    }
    if args.mode in {"preflight", "tiny_inference"}:
        manifest["runtime"] = runtime
    if tiny is not None:
        manifest["tiny_inference"] = tiny

    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
