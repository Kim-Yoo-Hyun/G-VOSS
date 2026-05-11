#!/usr/bin/env python3
"""Guard Open3DSG heavy Docker commands until data and runtime paths are ready."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_training_preflight_v5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--mode", choices=["dump_features", "train_pilot", "train_full"], required=True)
    parser.add_argument("--ensure-dirs", action="store_true")
    parser.add_argument("--check-imports", action="store_true")
    parser.add_argument(
        "--training-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_repro/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_preflight"),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def min_count(values: dict[str, Any]) -> int:
    if not values:
        return 0
    return min(int(value) for value in values.values())


def payload_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    train = manifest.get("train_payload", {})
    train_dev = manifest.get("train_dev_payload", {})
    expected = int(train.get("expected_scans", 1178))
    scan_dirs = int(train.get("existing_scan_dirs", 0))
    raw_files = min_count(train.get("raw_files", {}))
    mesh_texture = min_count(train.get("open3dsg_files", {}))
    sequence = min_count(train.get("sequence_files", {}))
    validation_expected = int(train_dev.get("expected_scans", 0))
    validation_scan_dirs = int(train_dev.get("existing_scan_dirs", 0))
    validation_raw_files = min_count(train_dev.get("raw_files", {}))
    validation_mesh_texture = min_count(train_dev.get("open3dsg_files", {}))
    validation_sequence = min_count(train_dev.get("sequence_files", {}))
    blockers = []
    if scan_dirs < expected:
        blockers.append(f"train_scan_dirs:{scan_dirs}/{expected}")
    if raw_files < expected:
        blockers.append(f"train_raw_files:{raw_files}/{expected}")
    if mesh_texture < expected:
        blockers.append(f"train_mesh_texture:{mesh_texture}/{expected}")
    if sequence < expected:
        blockers.append(f"train_sequence:{sequence}/{expected}")
    if validation_scan_dirs < validation_expected:
        blockers.append(f"validation_scan_dirs:{validation_scan_dirs}/{validation_expected}")
    if validation_raw_files < validation_expected:
        blockers.append(f"validation_raw_files:{validation_raw_files}/{validation_expected}")
    if validation_mesh_texture < validation_expected:
        blockers.append(f"validation_mesh_texture:{validation_mesh_texture}/{validation_expected}")
    if validation_sequence < validation_expected:
        blockers.append(f"validation_sequence:{validation_sequence}/{validation_expected}")
    return {
        "passed": not blockers,
        "expected_scans": expected,
        "train_scan_dirs": scan_dirs,
        "train_raw_files_min": raw_files,
        "train_mesh_texture_min": mesh_texture,
        "train_sequence_min": sequence,
        "validation_expected_scans": validation_expected,
        "validation_scan_dirs": validation_scan_dirs,
        "validation_raw_files_min": validation_raw_files,
        "validation_mesh_texture_min": validation_mesh_texture,
        "validation_sequence_min": validation_sequence,
        "blockers": blockers,
    }


def read_relationships(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    payload = load_json(path)
    scans = payload.get("scans", [])
    return scans if isinstance(scans, list) else []


def relationship_preprocessed_path(training_root: Path, relationship: dict[str, Any]) -> Path | None:
    scan = relationship.get("scan")
    split = relationship.get("split")
    if not scan or split is None:
        return None
    try:
        split_key = str(hex(int(split)))[-1]
    except (TypeError, ValueError):
        return None
    return (
        training_root
        / "output"
        / "datasets"
        / "OpenSG_3RScan"
        / "preprocessed"
        / str(scan)
        / f"data_dict_{split_key}.pkl"
    )


def runtime_split_gate(training_root: Path, split: str) -> dict[str, Any]:
    relationships_path = (
        training_root / "data" / "3RScan" / "3DSSG_subset" / f"relationships_{split}.json"
    )
    relationships = read_relationships(relationships_path)
    scans = sorted({str(row.get("scan")) for row in relationships if row.get("scan")})
    views_root = training_root / "output" / "datasets" / "OpenSG_3RScan" / "views"
    preprocessed_root = training_root / "output" / "datasets" / "OpenSG_3RScan" / "preprocessed"

    ready_views = 0
    missing_view_examples: list[str] = []
    for scan_id in scans:
        path = views_root / f"{scan_id}_object2image.pkl"
        if path.is_file() and path.stat().st_size > 0:
            ready_views += 1
        elif len(missing_view_examples) < 10:
            missing_view_examples.append(str(path))

    ready_preprocessed = 0
    missing_preprocessed_examples: list[str] = []
    invalid_relationship_rows = 0
    for relationship in relationships:
        path = relationship_preprocessed_path(training_root, relationship)
        if path is None:
            invalid_relationship_rows += 1
            continue
        if path.is_file() and path.stat().st_size > 0:
            ready_preprocessed += 1
        elif len(missing_preprocessed_examples) < 10:
            missing_preprocessed_examples.append(str(path))

    return {
        "relationships": str(relationships_path),
        "expected_scans": len(scans),
        "ready_views": ready_views,
        "expected_subgraphs": len(relationships),
        "ready_preprocessed": ready_preprocessed,
        "invalid_relationship_rows": invalid_relationship_rows,
        "missing_view_examples": missing_view_examples,
        "missing_preprocessed_examples": missing_preprocessed_examples,
    }


def runtime_stage_gate(repo_root: Path, mode: str) -> dict[str, Any]:
    training_root = env_path(
        "OPEN3DSG_BASE", repo_root / "local_dataset/Open3DSG_staged/training_repro"
    )
    views_root = training_root / "output" / "datasets" / "OpenSG_3RScan" / "views"
    preprocessed_root = training_root / "output" / "datasets" / "OpenSG_3RScan" / "preprocessed"
    train = runtime_split_gate(training_root, "train")
    validation = runtime_split_gate(training_root, "validation")

    blockers: list[str] = []
    if not Path(train["relationships"]).is_file():
        blockers.append(f"missing_train_relationships:{train['relationships']}")
    if not Path(validation["relationships"]).is_file():
        blockers.append(f"missing_validation_relationships:{validation['relationships']}")
    if train["invalid_relationship_rows"]:
        blockers.append(f"invalid_train_relationship_rows:{train['invalid_relationship_rows']}")
    if validation["invalid_relationship_rows"]:
        blockers.append(
            f"invalid_validation_relationship_rows:{validation['invalid_relationship_rows']}"
        )

    requires_preprocess = mode in {"dump_features", "train_pilot", "train_full"}
    if requires_preprocess:
        if train["ready_views"] < train["expected_scans"]:
            blockers.append(f"train_views:{train['ready_views']}/{train['expected_scans']}")
        if train["ready_preprocessed"] < train["expected_subgraphs"]:
            blockers.append(
                f"train_preprocessed:{train['ready_preprocessed']}/{train['expected_subgraphs']}"
            )
        if validation["ready_views"] < validation["expected_scans"]:
            blockers.append(
                f"validation_views:{validation['ready_views']}/{validation['expected_scans']}"
            )
        if validation["ready_preprocessed"] < validation["expected_subgraphs"]:
            blockers.append(
                f"validation_preprocessed:{validation['ready_preprocessed']}/{validation['expected_subgraphs']}"
            )

    return {
        "passed": not blockers,
        "training_root": str(training_root),
        "relationships_train": train["relationships"],
        "relationships_validation": validation["relationships"],
        "views_root": str(views_root),
        "preprocessed_root": str(preprocessed_root),
        "expected_train_scans": train["expected_scans"],
        "ready_train_views": train["ready_views"],
        "expected_train_subgraphs": train["expected_subgraphs"],
        "ready_train_preprocessed": train["ready_preprocessed"],
        "expected_validation_scans": validation["expected_scans"],
        "ready_validation_views": validation["ready_views"],
        "expected_validation_subgraphs": validation["expected_subgraphs"],
        "ready_validation_preprocessed": validation["ready_preprocessed"],
        "missing_train_view_examples": train["missing_view_examples"],
        "missing_train_preprocessed_examples": train["missing_preprocessed_examples"],
        "missing_validation_view_examples": validation["missing_view_examples"],
        "missing_validation_preprocessed_examples": validation["missing_preprocessed_examples"],
        "blockers": blockers,
    }


def env_path(name: str, fallback: Path) -> Path:
    value = os.environ.get(name)
    if value:
        return Path(value)
    return fallback


def is_writable_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".h001_write_", dir=path, delete=True):
            return True
    except OSError:
        return False


def dir_has_content(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False


def check_paths(repo_root: Path, mode: str, ensure_dirs: bool) -> dict[str, Any]:
    training_root = env_path(
        "OPEN3DSG_BASE", repo_root / "local_dataset/Open3DSG_staged/training_repro"
    )
    data_dir = env_path("OPEN3DSG_DATA", training_root / "data")
    output_dir = env_path("OPEN3DSG_DATA_OUT", training_root / "output")
    source_root = training_root / "source/open3dsg_source"
    feature_root = output_dir / "features"
    feature_run_dir = env_path(
        "OPEN3DSG_FEATURE_RUN_DIR",
        feature_root / "clip_features_h001_official_blip_top5_scales3",
    )
    feature_load_dir = env_path("OPEN3DSG_FEATURE_LOAD_DIR", feature_run_dir)
    checkpoint_dir = output_dir / "checkpoints"
    hf_home = env_path("HF_HOME", repo_root / "local_dataset/model_cache/huggingface")
    torch_home = env_path("TORCH_HOME", repo_root / "local_dataset/model_cache/torch")
    transformers_cache = env_path("TRANSFORMERS_CACHE", hf_home)
    home_dir = env_path("HOME", repo_root / "local_dataset/model_cache/home")
    xdg_cache_home = env_path("XDG_CACHE_HOME", repo_root / "local_dataset/model_cache/xdg")
    clip_cache_dir = home_dir / ".cache/clip"

    required_existing_dirs = {
        "training_root": training_root,
        "source_root": source_root,
        "data_dir": data_dir,
    }
    required_existing_files = {
        "open3dsg_run_script": source_root / "open3dsg/scripts/run.py",
        "base_open3dsg_helpers_adjectives": training_root / "open3dsg/helpers/nature_adjectives.txt",
        "base_open3dsg_helpers_words": training_root / "open3dsg/helpers/nature_words.txt",
    }
    managed_dirs = {
        "output_dir": output_dir,
        "feature_root": feature_root,
        "feature_run_dir": feature_run_dir,
        "checkpoint_dir": checkpoint_dir,
        "hf_home": hf_home,
        "torch_home": torch_home,
        "transformers_cache": transformers_cache,
        "home_dir": home_dir,
        "xdg_cache_home": xdg_cache_home,
        "clip_cache_dir": clip_cache_dir,
    }

    if ensure_dirs:
        for path in managed_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    for name, path in required_existing_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_required_dir:{name}:{path}")

    for name, path in required_existing_files.items():
        if not path.is_file():
            blockers.append(f"missing_required_file:{name}:{path}")

    for name, path in managed_dirs.items():
        if not path.is_dir():
            blockers.append(f"missing_managed_dir:{name}:{path}")
        elif not is_writable_dir(path):
            blockers.append(f"not_writable_dir:{name}:{path}")

    if mode in {"train_pilot", "train_full"}:
        if not feature_load_dir.is_dir():
            blockers.append(f"missing_feature_load_dir:{feature_load_dir}")
        elif not dir_has_content(feature_load_dir):
            blockers.append(f"missing_feature_outputs:{feature_load_dir}")

    paths = {**required_existing_dirs, **managed_dirs, **required_existing_files}
    paths["feature_load_dir"] = feature_load_dir
    return {
        "passed": not blockers,
        "blockers": blockers,
        "paths": {name: str(path) for name, path in paths.items()},
    }


def check_imports(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"passed": True, "enabled": False, "modules": {}, "cuda": {}, "blockers": []}

    modules: dict[str, Any] = {}
    blockers: list[str] = []
    for name in ("torch", "pytorch_lightning", "tensorflow", "open3d", "transformers"):
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - this runs inside the Docker env.
            modules[name] = {"imported": False, "error": repr(exc)}
            blockers.append(f"import_failed:{name}:{exc}")
            continue
        modules[name] = {
            "imported": True,
            "version": getattr(module, "__version__", None),
        }

    cuda: dict[str, Any] = {}
    torch_module = None
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

    return {
        "passed": not blockers,
        "enabled": True,
        "modules": modules,
        "cuda": cuda,
        "blockers": blockers,
    }


def make_report(payload: dict[str, Any]) -> str:
    path_gate_result = payload["gates"]["paths"]
    import_gate_result = payload["gates"]["imports"]
    runtime_gate_result = payload["gates"]["runtime_stage"]
    source_entrypoint = path_gate_result.get("paths", {}).get("open3dsg_run_script")
    cuda = import_gate_result.get("cuda", {})
    modules = import_gate_result.get("modules", {})
    lines = [
        "# Open3DSG Training Preflight",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Mode: `{payload['mode']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Gates",
        "",
        f"- payload: `{payload['gates']['payload']['passed']}`",
        f"- runtime stage: `{payload['gates']['runtime_stage']['passed']}`",
        f"- paths: `{payload['gates']['paths']['passed']}`",
        f"- imports: `{payload['gates']['imports']['passed']}`",
        "",
        "## Payload",
        "",
    ]
    payload_gate_result = payload["gates"]["payload"]
    lines.extend(
        [
            f"- train scan dirs: `{payload_gate_result['train_scan_dirs']}/{payload_gate_result['expected_scans']}`",
            f"- train raw files min: `{payload_gate_result['train_raw_files_min']}/{payload_gate_result['expected_scans']}`",
            f"- train mesh/texture min: `{payload_gate_result['train_mesh_texture_min']}/{payload_gate_result['expected_scans']}`",
            f"- train sequence min: `{payload_gate_result['train_sequence_min']}/{payload_gate_result['expected_scans']}`",
            f"- validation scan dirs: `{payload_gate_result['validation_scan_dirs']}/{payload_gate_result['validation_expected_scans']}`",
            f"- validation raw files min: `{payload_gate_result['validation_raw_files_min']}/{payload_gate_result['validation_expected_scans']}`",
            f"- validation mesh/texture min: `{payload_gate_result['validation_mesh_texture_min']}/{payload_gate_result['validation_expected_scans']}`",
            f"- validation sequence min: `{payload_gate_result['validation_sequence_min']}/{payload_gate_result['validation_expected_scans']}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Runtime Stage",
            "",
            f"- train views: `{runtime_gate_result['ready_train_views']}/{runtime_gate_result['expected_train_scans']}`",
            f"- train preprocessed: `{runtime_gate_result['ready_train_preprocessed']}/{runtime_gate_result['expected_train_subgraphs']}`",
            f"- validation views: `{runtime_gate_result['ready_validation_views']}/{runtime_gate_result['expected_validation_scans']}`",
            f"- validation preprocessed: `{runtime_gate_result['ready_validation_preprocessed']}/{runtime_gate_result['expected_validation_subgraphs']}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Source",
            "",
            f"- Open3DSG run script: `{source_entrypoint}`",
            "",
            "## Imports",
            "",
            f"- CUDA available: `{cuda.get('is_available')}`",
            f"- CUDA device count: `{cuda.get('device_count')}`",
            f"- torch CUDA build: `{cuda.get('torch_version')}`",
            f"- CUDA device: `{cuda.get('device_name')}`",
            f"- required CUDA arch: `{cuda.get('required_arch')}`",
            f"- torch supported arch list: `{', '.join(cuda.get('supported_arch_list', []))}`",
        ]
    )
    for name in ("torch", "pytorch_lightning", "tensorflow", "open3d", "transformers"):
        module = modules.get(name, {})
        lines.append(f"- {name}: `{'ok' if module.get('imported') else 'failed'}` `{module.get('version')}`")
    blockers = payload["blockers"]
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    training_manifest = args.training_manifest
    if not training_manifest.is_absolute():
        training_manifest = repo_root / training_manifest
    out_dir = args.out
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    blockers: list[str] = []
    if training_manifest.exists():
        manifest = load_json(training_manifest)
        payload = payload_gate(manifest)
    else:
        payload = {"passed": False, "blockers": [f"missing_training_manifest:{training_manifest}"]}

    path_gate = check_paths(repo_root=repo_root, mode=args.mode, ensure_dirs=args.ensure_dirs)
    runtime_stage = runtime_stage_gate(repo_root=repo_root, mode=args.mode)
    import_gate = check_imports(enabled=args.check_imports)
    blockers.extend(payload.get("blockers", []))
    blockers.extend(runtime_stage.get("blockers", []))
    blockers.extend(path_gate.get("blockers", []))
    blockers.extend(import_gate.get("blockers", []))

    status = "ready" if not blockers else "blocked"
    result = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "status": status,
        "repo_root": str(repo_root),
        "training_manifest": relpath(repo_root, training_manifest),
        "ensure_dirs": bool(args.ensure_dirs),
        "check_imports": bool(args.check_imports),
        "gates": {
            "payload": payload,
            "runtime_stage": runtime_stage,
            "paths": path_gate,
            "imports": import_gate,
        },
        "blockers": blockers,
        "next_action": (
            "Run the protected Open3DSG command."
            if status == "ready"
            else "Generate train/validation view/preprocessed pickles or fix missing/writable runtime directories before running heavy Open3DSG commands."
        ),
    }
    write_json(out_dir / f"{args.mode}.json", result)
    (out_dir / f"{args.mode}.md").write_text(make_report(result), encoding="utf-8")
    print(json.dumps({"mode": args.mode, "status": status, "blockers": blockers}, sort_keys=True))
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
