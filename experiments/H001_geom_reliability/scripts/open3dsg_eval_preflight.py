#!/usr/bin/env python3
"""Guard Open3DSG H001 eval until checkpoint, runtime paths, and raw-dump contract are ready."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_eval_preflight_v1"
RAW_SCHEMA_VERSION = "h001_open3dsg_raw_dump_v1"
EXPECTED_CONTEXTS = 388


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
    )
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--subset-json",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--raw-dump-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/eval_preflight"),
    )
    parser.add_argument("--ensure-dirs", action="store_true")
    parser.add_argument("--check-imports", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_selected_scans(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def is_writable_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".h001_eval_", dir=path, delete=True):
            return True
    except OSError:
        return False


def resolve_checkpoint(repo_root: Path, checkpoint_arg: Path | None) -> Path | None:
    checkpoint = checkpoint_arg or (Path(os.environ["OPEN3DSG_CHECKPOINT"]) if os.environ.get("OPEN3DSG_CHECKPOINT") else None)
    return resolve(repo_root, checkpoint) if checkpoint is not None else None


def checkpoint_gate(repo_root: Path, checkpoint: Path | None) -> dict[str, Any]:
    blockers: list[str] = []
    if checkpoint is None:
        blockers.append("missing_checkpoint_env:OPEN3DSG_CHECKPOINT")
        return {
            "passed": False,
            "checkpoint": None,
            "exists": False,
            "bytes": 0,
            "blockers": blockers,
        }
    allowed_suffixes = {".ckpt", ".pt", ".pth"}
    exists = checkpoint.is_file()
    size = checkpoint.stat().st_size if exists else 0
    if not exists:
        blockers.append(f"missing_checkpoint_file:{checkpoint}")
    if checkpoint.suffix and checkpoint.suffix not in allowed_suffixes:
        blockers.append(f"unexpected_checkpoint_suffix:{checkpoint.suffix}")
    if exists and size <= 0:
        blockers.append(f"empty_checkpoint_file:{checkpoint}")
    return {
        "passed": not blockers,
        "checkpoint": relpath(repo_root, checkpoint),
        "exists": exists,
        "bytes": size,
        "blockers": blockers,
    }


def runtime_gate(repo_root: Path, runtime_root: Path, raw_dump_jsonl: Path, ensure_dirs: bool) -> dict[str, Any]:
    data_dir = Path(os.environ.get("OPEN3DSG_DATA", runtime_root / "data"))
    output_dir = Path(os.environ.get("OPEN3DSG_DATA_OUT", runtime_root / "output"))
    source_root = runtime_root / "source/open3dsg_source"
    checkpoint_dir = output_dir / "checkpoints"
    hf_home = Path(os.environ.get("HF_HOME", repo_root / "local_dataset/model_cache/huggingface"))
    torch_home = Path(os.environ.get("TORCH_HOME", repo_root / "local_dataset/model_cache/torch"))
    transformers_cache = Path(os.environ.get("TRANSFORMERS_CACHE", hf_home))
    home_dir = Path(os.environ.get("HOME", repo_root / "local_dataset/model_cache/home"))
    xdg_cache_home = Path(os.environ.get("XDG_CACHE_HOME", repo_root / "local_dataset/model_cache/xdg"))

    required_dirs = {
        "runtime_root": runtime_root,
        "source_root": source_root,
        "data_dir": data_dir,
        "output_dir": output_dir,
        "checkpoint_dir": checkpoint_dir,
    }
    required_files = {
        "open3dsg_run_script": source_root / "open3dsg/scripts/run.py",
        "relationships_validation": data_dir / "3RScan/3DSSG_subset/relationships_validation.json",
        "validation_scans": data_dir / "3RScan/3DSSG_subset/validation_scans.txt",
        "classes": data_dir / "3RScan/3DSSG_subset/classes.txt",
        "relationships": data_dir / "3RScan/3DSSG_subset/relationships.txt",
        "blip2_positional_embedding": checkpoint_dir / "blip2_positional_embedding.pt",
        "pointnet_checkpoint": checkpoint_dir / "pointnet.pth",
        "pointnet2_ulip_checkpoint": checkpoint_dir / "pointnet2_ulip.pt",
        "openseg_saved_model": checkpoint_dir / "openseg/saved_model.pb",
    }
    managed_dirs = {
        "raw_dump_dir": raw_dump_jsonl.parent,
        "hf_home": hf_home,
        "torch_home": torch_home,
        "transformers_cache": transformers_cache,
        "home_dir": home_dir,
        "xdg_cache_home": xdg_cache_home,
        "clip_cache_dir": home_dir / ".cache/clip",
    }
    if ensure_dirs:
        for path in managed_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    for name, path in required_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_required_dir:{name}:{path}")
    for name, path in required_files.items():
        if not path.is_file():
            blockers.append(f"missing_required_file:{name}:{path}")
    for name, path in managed_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_managed_dir:{name}:{path}")
        elif not is_writable_dir(path):
            blockers.append(f"not_writable_dir:{name}:{path}")

    paths = {**required_dirs, **required_files, **managed_dirs}
    return {
        "passed": not blockers,
        "blockers": blockers,
        "paths": {name: str(path) for name, path in paths.items()},
    }


def scope_gate(repo_root: Path, subset_json: Path, selected_scans: Path) -> dict[str, Any]:
    blockers: list[str] = []
    counts = {"selected_scans": 0, "contexts": 0}
    if not selected_scans.is_file():
        blockers.append(f"missing_selected_scans:{selected_scans}")
        return {"passed": False, "counts": counts, "blockers": blockers}
    if not subset_json.is_file():
        blockers.append(f"missing_subset_json:{subset_json}")
        return {"passed": False, "counts": counts, "blockers": blockers}
    selected = read_selected_scans(selected_scans)
    subset = load_json(subset_json)
    contexts = [
        entry
        for entry in subset.get("scans", [])
        if str(entry.get("scan")) in selected
    ]
    counts = {"selected_scans": len(selected), "contexts": len(contexts)}
    if len(contexts) != EXPECTED_CONTEXTS:
        blockers.append(f"unexpected_h001_context_count:{len(contexts)}/{EXPECTED_CONTEXTS}")
    return {
        "passed": not blockers,
        "counts": counts,
        "selected_scans": relpath(repo_root, selected_scans),
        "subset_json": relpath(repo_root, subset_json),
        "blockers": blockers,
    }


def import_gate(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"passed": True, "enabled": False, "modules": {}, "cuda": {}, "blockers": []}
    modules: dict[str, Any] = {}
    blockers: list[str] = []
    for name in ("torch", "pytorch_lightning", "tensorflow", "open3d", "transformers", "clip", "open_clip"):
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - runs inside Docker.
            modules[name] = {"imported": False, "error": repr(exc)}
            blockers.append(f"import_failed:{name}:{exc}")
            continue
        modules[name] = {"imported": True, "version": getattr(module, "__version__", None)}
    cuda: dict[str, Any] = {}
    if modules.get("torch", {}).get("imported"):
        torch = importlib.import_module("torch")
        cuda = {
            "is_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "torch_version": getattr(torch, "__version__", None),
        }
        if not cuda["is_available"]:
            blockers.append("cuda_unavailable")
        if cuda["device_count"] <= 0:
            blockers.append("cuda_device_count_zero")
    return {"passed": not blockers, "enabled": True, "modules": modules, "cuda": cuda, "blockers": blockers}


def raw_dump_contract(repo_root: Path, raw_dump_jsonl: Path) -> dict[str, Any]:
    required_fields = [
        "schema_version",
        "record_type",
        "baseline_run_id",
        "scan_id",
        "subset_split_id",
        "subgraph_id",
        "edge.subject_id",
        "edge.object_id",
        "predicate_scores[].predicate_label",
        "predicate_scores[].score",
    ]
    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "record_type": "open3dsg_raw_prediction",
        "raw_dump_jsonl": relpath(repo_root, raw_dump_jsonl),
        "status": "contract_ready_raw_dump_missing" if not raw_dump_jsonl.exists() else "raw_dump_present",
        "required_identity_fields": required_fields,
        "adapter_command": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) "
            f"OPEN3DSG_RAW_DUMP_JSONL=/workspace/{relpath(repo_root, raw_dump_jsonl)} "
            "docker compose -f experiments/H001_geom_reliability/compose.yaml "
            "run --rm open3dsg_adapter_raw_dump'"
        ),
        "claim_boundary": "This contract is not second-source metric evidence until the raw dump exists, converts to prediction JSONL, joins with geometry, and evaluates.",
    }


def make_report(payload: dict[str, Any]) -> str:
    checkpoint = payload["gates"]["checkpoint"]
    runtime = payload["gates"]["runtime"]
    scope = payload["gates"]["scope"]
    imports = payload["gates"]["imports"]
    raw = payload["raw_dump_contract"]
    lines = [
        "# Open3DSG Eval Preflight",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Gates",
        "",
        f"- checkpoint: `{checkpoint['passed']}`",
        f"- runtime: `{runtime['passed']}`",
        f"- scope: `{scope['passed']}`",
        f"- imports: `{imports['passed']}`",
        "",
        "## Checkpoint",
        "",
        f"- path: `{checkpoint['checkpoint']}`",
        f"- exists: `{checkpoint['exists']}`",
        f"- bytes: `{checkpoint['bytes']}`",
        "",
        "## Scope",
        "",
        f"- selected scans: `{scope['counts']['selected_scans']}`",
        f"- contexts: `{scope['counts']['contexts']}`",
        "",
        "## Raw Dump Contract",
        "",
        f"- status: `{raw['status']}`",
        f"- raw dump JSONL: `{raw['raw_dump_jsonl']}`",
        f"- schema version: `{raw['schema_version']}`",
        "",
        "## Imports",
        "",
    ]
    for name, module in imports["modules"].items():
        lines.append(f"- {name}: `{'ok' if module.get('imported') else 'failed'}` `{module.get('version')}`")
    cuda = imports.get("cuda", {})
    if cuda:
        lines.extend(
            [
                f"- CUDA available: `{cuda.get('is_available')}`",
                f"- CUDA device count: `{cuda.get('device_count')}`",
                f"- torch: `{cuda.get('torch_version')}`",
            ]
        )
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runtime_root = resolve(repo_root, args.runtime_root).resolve()
    selected_scans = resolve(repo_root, args.selected_scans)
    subset_json = resolve(repo_root, args.subset_json)
    raw_dump_jsonl = resolve(repo_root, args.raw_dump_jsonl)
    out_dir = resolve(repo_root, args.out)
    assert selected_scans is not None
    assert subset_json is not None
    assert raw_dump_jsonl is not None
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = resolve_checkpoint(repo_root, args.checkpoint)
    checkpoint_result = checkpoint_gate(repo_root, checkpoint)
    runtime_result = runtime_gate(
        repo_root=repo_root,
        runtime_root=runtime_root,
        raw_dump_jsonl=raw_dump_jsonl,
        ensure_dirs=args.ensure_dirs,
    )
    scope_result = scope_gate(repo_root=repo_root, subset_json=subset_json, selected_scans=selected_scans)
    import_result = import_gate(enabled=args.check_imports)
    blockers = [
        *checkpoint_result["blockers"],
        *runtime_result["blockers"],
        *scope_result["blockers"],
        *import_result["blockers"],
    ]
    status = "ready" if not blockers else "blocked"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "repo_root": str(repo_root),
        "runtime_root": relpath(repo_root, runtime_root),
        "gates": {
            "checkpoint": checkpoint_result,
            "runtime": runtime_result,
            "scope": scope_result,
            "imports": import_result,
        },
        "raw_dump_contract": raw_dump_contract(repo_root, raw_dump_jsonl),
        "blockers": blockers,
        "next_action": (
            "Run eval_h001_gt_objects or raw-dump hook with this checkpoint."
            if status == "ready"
            else "Provide a valid OPEN3DSG_CHECKPOINT and fix blockers before running Open3DSG eval."
        ),
    }
    write_json(out_dir / "manifest.json", payload)
    write_json(out_dir / "raw_dump_contract.json", payload["raw_dump_contract"])
    (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir), "blockers": blockers}, sort_keys=True))
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
