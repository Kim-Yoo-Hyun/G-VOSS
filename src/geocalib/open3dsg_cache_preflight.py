#!/usr/bin/env python3
"""Check Open3DSG model/cache readiness before feature dump or training."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_cache_preflight_v2"
GB = 1024**3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--training-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/cache_preflight"),
    )
    parser.add_argument("--ensure-dirs", action="store_true")
    parser.add_argument("--check-imports", action="store_true")
    parser.add_argument("--require-model-cache", action="store_true")
    parser.add_argument("--min-free-gb", type=float, default=300.0)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_writable_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".h001_cache_", dir=path, delete=True):
            return True
    except OSError:
        return False


def dir_size_bytes(path: Path, limit_files: int = 20000) -> tuple[int, int, bool]:
    total = 0
    count = 0
    truncated = False
    if not path.exists():
        return total, count, truncated
    for child in path.rglob("*"):
        count += 1
        if count > limit_files:
            truncated = True
            break
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total, count, truncated


def path_has_content(path: Path) -> bool:
    if path.is_file():
        return path.stat().st_size > 0
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False


def first_cache_path(paths: list[Path]) -> Path:
    for path in paths:
        if path_has_content(path):
            return path
    return paths[0]


def disk_gate(paths: dict[str, Path], min_free_gb: float) -> dict[str, Any]:
    checked: dict[str, Any] = {}
    blockers: list[str] = []
    seen_devices: set[tuple[int, int]] = set()
    for name, path in paths.items():
        probe = path if path.exists() else path.parent
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        try:
            stat = probe.stat()
            device = (stat.st_dev, stat.st_ino if probe.is_mount() else stat.st_dev)
            usage = shutil.disk_usage(probe)
        except OSError as exc:
            blockers.append(f"disk_probe_failed:{name}:{path}:{exc}")
            continue
        free_gb = usage.free / GB
        checked[name] = {
            "path": str(path),
            "probe": str(probe),
            "free_gb": round(free_gb, 3),
            "total_gb": round(usage.total / GB, 3),
        }
        if device in seen_devices:
            continue
        seen_devices.add(device)
        if free_gb < min_free_gb:
            blockers.append(f"low_disk_free:{name}:{free_gb:.1f}GB<{min_free_gb:.1f}GB")
    return {"passed": not blockers, "min_free_gb": min_free_gb, "paths": checked, "blockers": blockers}


def path_gate(repo_root: Path, training_root: Path, ensure_dirs: bool) -> dict[str, Any]:
    hf_home = Path(os.environ.get("HF_HOME", repo_root / "local_dataset/model_cache/huggingface"))
    torch_home = Path(os.environ.get("TORCH_HOME", repo_root / "local_dataset/model_cache/torch"))
    transformers_cache = Path(os.environ.get("TRANSFORMERS_CACHE", hf_home))
    home = Path(os.environ.get("HOME", repo_root / "local_dataset/model_cache/home"))
    xdg_cache_home = Path(os.environ.get("XDG_CACHE_HOME", repo_root / "local_dataset/model_cache/xdg"))
    output_dir = Path(os.environ.get("OPEN3DSG_DATA_OUT", training_root / "output"))
    checkpoint_dir = output_dir / "checkpoints"
    feature_dir = output_dir / "features"
    source_root = training_root / "source/open3dsg_source"
    clip_cache = home / ".cache/clip"

    required_dirs = {
        "training_root": training_root,
        "source_root": source_root,
        "checkpoint_dir": checkpoint_dir,
    }
    managed_dirs = {
        "hf_home": hf_home,
        "torch_home": torch_home,
        "transformers_cache": transformers_cache,
        "home": home,
        "xdg_cache_home": xdg_cache_home,
        "clip_cache": clip_cache,
        "feature_dir": feature_dir,
    }
    required_files = {
        "open3dsg_run_script": source_root / "open3dsg/scripts/run.py",
        "open3dsg_sgpn": source_root / "open3dsg/models/sgpn.py",
        "blip2_positional_embedding": checkpoint_dir / "blip2_positional_embedding.pt",
        "pointnet_checkpoint": checkpoint_dir / "pointnet.pth",
        "pointnet2_ulip_checkpoint": checkpoint_dir / "pointnet2_ulip.pt",
        "openseg_saved_model": checkpoint_dir / "openseg/saved_model.pb",
    }

    if ensure_dirs:
        for path in managed_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    for name, path in required_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_required_dir:{name}:{path}")
    for name, path in managed_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_managed_dir:{name}:{path}")
        elif not is_writable_dir(path):
            blockers.append(f"not_writable_dir:{name}:{path}")
    for name, path in required_files.items():
        if not path.exists():
            blockers.append(f"missing_required_file:{name}:{path}")

    hf_instructblip_paths = [
        hf_home / "hub/models--Salesforce--instructblip-vicuna-7b",
        hf_home / "models--Salesforce--instructblip-vicuna-7b",
        transformers_cache / "models--Salesforce--instructblip-vicuna-7b",
    ]
    cache_hints = {
        "hf_instructblip_vicuna_7b": first_cache_path(hf_instructblip_paths),
        "clip_cache_dir": clip_cache,
        "torch_hub": torch_home / "hub",
    }
    for name, path in cache_hints.items():
        if not path_has_content(path):
            warnings.append(f"model_cache_missing_or_empty:{name}:{path}")

    all_paths = {**required_dirs, **managed_dirs, **required_files, **cache_hints}
    sizes = {}
    for name, path in all_paths.items():
        size, count, truncated = dir_size_bytes(path) if path.is_dir() else (path.stat().st_size if path.exists() else 0, 1 if path.exists() else 0, False)
        sizes[name] = {"bytes": size, "entries": count, "truncated": truncated}

    return {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "paths": {name: str(path) for name, path in all_paths.items()},
        "sizes": sizes,
    }


def import_gate(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"passed": True, "enabled": False, "modules": {}, "cuda": {}, "blockers": []}
    modules: dict[str, Any] = {}
    blockers: list[str] = []
    for name in ("torch", "transformers", "tensorflow", "clip", "open_clip"):
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - runs inside Docker.
            modules[name] = {"imported": False, "error": repr(exc)}
            blockers.append(f"import_failed:{name}:{exc}")
            continue
        modules[name] = {"imported": True, "version": getattr(module, "__version__", None)}

    cuda: dict[str, Any] = {}
    if modules.get("torch", {}).get("imported"):
        torch_module = importlib.import_module("torch")
        arch_list = list(torch_module.cuda.get_arch_list())
        device_name = None
        device_capability = None
        required_arch = None
        if torch_module.cuda.device_count() > 0:
            device_name = torch_module.cuda.get_device_name(0)
            capability = torch_module.cuda.get_device_capability(0)
            device_capability = list(capability)
            required_arch = f"sm_{capability[0]}{capability[1]}"
        cuda = {
            "is_available": bool(torch_module.cuda.is_available()),
            "device_count": int(torch_module.cuda.device_count()),
            "torch_version": getattr(torch_module, "__version__", None),
            "device_name": device_name,
            "device_capability": device_capability,
            "required_arch": required_arch,
            "supported_arch_list": arch_list,
        }
        if not cuda["is_available"]:
            blockers.append("cuda_unavailable")
        if cuda["device_count"] <= 0:
            blockers.append("cuda_device_count_zero")
        if required_arch and arch_list and required_arch not in arch_list:
            blockers.append(
                f"torch_cuda_arch_incompatible:{device_name}:{required_arch}:supported={','.join(arch_list)}"
            )
    return {"passed": not blockers, "enabled": True, "modules": modules, "cuda": cuda, "blockers": blockers}


def make_report(payload: dict[str, Any]) -> str:
    paths = payload["gates"]["paths"]
    disk = payload["gates"]["disk"]
    imports = payload["gates"]["imports"]
    lines = [
        "# Open3DSG Cache Preflight",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Gates",
        "",
        f"- paths: `{paths['passed']}`",
        f"- disk: `{disk['passed']}`",
        f"- imports: `{imports['passed']}`",
        f"- require model cache: `{payload['require_model_cache']}`",
        "",
        "## Disk",
        "",
    ]
    for name, info in disk["paths"].items():
        lines.append(f"- {name}: `{info['free_gb']}GB free` at `{info['probe']}`")
    lines.extend(["", "## Required Local Model Files", ""])
    for name in (
        "blip2_positional_embedding",
        "pointnet_checkpoint",
        "pointnet2_ulip_checkpoint",
        "openseg_saved_model",
    ):
        path = paths["paths"].get(name)
        size = paths["sizes"].get(name, {}).get("bytes")
        lines.append(f"- {name}: `{path}` `{size}` bytes")
    lines.extend(["", "## Cache Hints", ""])
    for warning in paths["warnings"]:
        lines.append(f"- `{warning}`")
    if not paths["warnings"]:
        lines.append("- no missing cache hints")
    lines.extend(["", "## Imports", ""])
    for name, module in imports["modules"].items():
        lines.append(f"- {name}: `{'ok' if module.get('imported') else 'failed'}` `{module.get('version')}`")
    cuda = imports.get("cuda", {})
    if cuda:
        lines.extend(
            [
                f"- CUDA available: `{cuda.get('is_available')}`",
                f"- CUDA device count: `{cuda.get('device_count')}`",
                f"- CUDA device: `{cuda.get('device_name')}`",
                f"- required CUDA arch: `{cuda.get('required_arch')}`",
                f"- torch supported arch list: `{', '.join(cuda.get('supported_arch_list', []))}`",
            ]
        )
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{warning}`" for warning in payload["warnings"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    training_root = resolve(repo_root, args.training_root).resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = path_gate(repo_root=repo_root, training_root=training_root, ensure_dirs=args.ensure_dirs)
    disk = disk_gate(
        {
            "training_root": training_root,
            "hf_home": Path(os.environ.get("HF_HOME", repo_root / "local_dataset/model_cache/huggingface")),
            "torch_home": Path(os.environ.get("TORCH_HOME", repo_root / "local_dataset/model_cache/torch")),
        },
        min_free_gb=args.min_free_gb,
    )
    imports = import_gate(enabled=args.check_imports)
    blockers = [*paths["blockers"], *disk["blockers"], *imports["blockers"]]
    warnings = list(paths["warnings"])
    if args.require_model_cache:
        blockers.extend(paths["warnings"])
        warnings = []
    status = "ready" if not blockers and not warnings else "ready_with_cache_warnings" if not blockers else "blocked"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "repo_root": str(repo_root),
        "training_root": relpath(repo_root, training_root),
        "ensure_dirs": bool(args.ensure_dirs),
        "require_model_cache": bool(args.require_model_cache),
        "gates": {"paths": paths, "disk": disk, "imports": imports},
        "blockers": blockers,
        "warnings": warnings,
        "next_action": (
            "Continue payload staging; warm missing model caches before feature dump if network access during feature dump is not desired."
            if status != "blocked"
            else "Fix blockers before running Open3DSG feature dump or training."
        ),
    }
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if status != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
