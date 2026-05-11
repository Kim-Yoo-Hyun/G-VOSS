#!/usr/bin/env python3
"""Preflight the Open3DSG training route for H001."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"
DEFAULT_OPEN3DSG_SOURCE = Path("/tmp/open3dsg_source")
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "training_route"
DEFAULT_PYTHON = REPO_ROOT / "local_dataset" / "VLSAT_staged" / "multiview_venv" / "bin" / "python"

REQUIRED_SCAN_FILES = [
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
]

REQUIRED_MODULES = [
    "torch",
    "pytorch_lightning",
    "transformers",
    "clip",
    "tensorflow",
    "cv2",
    "open3d",
    "easydict",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_OPEN3DSG_SOURCE)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_scans(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("scans", [])


def relationship_stats(path: Path) -> dict[str, Any]:
    scans = load_scans(path)
    return {
        "path": relpath(path),
        "exists": path.exists(),
        "subgraphs": len(scans),
        "unique_scans": len({scan.get("scan") for scan in scans}),
        "relations": sum(len(scan.get("relationships", [])) for scan in scans),
    }


def data_dict_name(split: Any) -> str:
    return f"data_dict_{str(hex(int(split)))[-1]}.pkl"


def expected_preprocessed(relationships: list[dict[str, Any]], preprocessed_root: Path) -> dict[str, Any]:
    expected = []
    for rel in relationships:
        scan_id = rel.get("scan")
        split = rel.get("split")
        if scan_id is None or split is None:
            continue
        expected.append(preprocessed_root / scan_id / data_dict_name(split))
    ready = [path for path in expected if path.exists()]
    return {
        "expected": len(expected),
        "ready": len(ready),
        "missing": len(expected) - len(ready),
    }


def scan_payload_counts(scan_ids: set[str], scans_root: Path) -> dict[str, Any]:
    counts = {name: 0 for name in REQUIRED_SCAN_FILES}
    sequence_info = 0
    sequence_color = 0
    existing_scan_dirs = 0
    for scan_id in sorted(scan_ids):
        scan_dir = scans_root / scan_id
        if scan_dir.is_dir():
            existing_scan_dirs += 1
        for name in REQUIRED_SCAN_FILES:
            if (scan_dir / name).exists():
                counts[name] += 1
        if (scan_dir / "sequence" / "_info.txt").exists():
            sequence_info += 1
        if any((scan_dir / "sequence").glob("*.color.jpg")):
            sequence_color += 1
    return {
        "unique_scans": len(scan_ids),
        "existing_scan_dirs": existing_scan_dirs,
        "required_files": counts,
        "sequence_info": sequence_info,
        "sequence_color": sequence_color,
    }


def module_checks(python: Path) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    if not python.exists():
        return {module: {"status": "not_checked", "reason": f"missing python: {relpath(python)}"} for module in REQUIRED_MODULES}
    for module in REQUIRED_MODULES:
        code = (
            "import importlib; "
            f"m=importlib.import_module({module!r}); "
            "print(getattr(m, '__version__', 'unknown'))"
        )
        proc = subprocess.run(
            [str(python), "-c", code],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        checks[module] = {
            "status": "ready" if proc.returncode == 0 else "missing",
            "version": proc.stdout.strip() if proc.returncode == 0 else None,
            "error": proc.stderr.strip().splitlines()[-1] if proc.returncode else None,
        }
    return checks


def gpu_info() -> dict[str, Any]:
    proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0:
        return {"status": "not_available", "gpus": [], "recommended_official_gpus": 4}
    gpus = []
    for line in proc.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",", 1)]
        gpus.append({"name": parts[0], "memory": parts[1] if len(parts) > 1 else "unknown"})
    return {
        "status": "ready" if gpus else "not_available",
        "gpus": gpus,
        "gpu_count": len(gpus),
        "recommended_official_gpus": 4,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    env_missing = [k for k, v in manifest["environment"]["modules"].items() if v["status"] != "ready"]
    lines = [
        "# Open3DSG Training Route",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Decision",
        "",
        manifest["decision"],
        "",
        "## Source Facts",
        "",
        f"- Official training command: `{manifest['source_facts']['official_training_command']}`",
        f"- Official test command requires checkpoint: `{manifest['source_facts']['test_requires_checkpoint']}`",
        f"- Training source supports 3RScan route: `{manifest['source_facts']['supports_3rscan_fit']}`",
        "",
        "## Dataset Readiness",
        "",
        f"- Official full 3DSSG train split: {manifest['official_3dssg_train']['subgraphs']} subgraphs, {manifest['official_3dssg_train']['unique_scans']} unique scans.",
        f"- Current staged train split: {manifest['staged_train']['subgraphs']} subgraphs.",
        f"- H001 staged validation/test split: {manifest['staged_validation']['subgraphs']} subgraphs, {manifest['staged_validation']['unique_scans']} unique scans.",
        f"- Full-train preprocessed pickles ready: {manifest['full_train_preprocessed']['ready']} / {manifest['full_train_preprocessed']['expected']}.",
        f"- Full-train view pickles ready: {manifest['full_train_views']['ready']} / {manifest['official_3dssg_train']['unique_scans']}.",
        "",
        "## Local Payload",
        "",
        f"- Full-train scan dirs ready: {manifest['full_train_payload']['existing_scan_dirs']} / {manifest['full_train_payload']['unique_scans']}.",
        f"- Full-train sequence color ready: {manifest['full_train_payload']['sequence_color']} / {manifest['full_train_payload']['unique_scans']}.",
        "",
        "## Environment",
        "",
        f"- Python: `{manifest['environment']['python']}`",
        f"- Missing modules: `{env_missing}`",
        f"- GPU count: `{manifest['hardware'].get('gpu_count', 0)}`; official README example uses `{manifest['hardware']['recommended_official_gpus']}` GPUs.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    lines.extend(["", "## Next Action", "", manifest["next_action"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    subset_root = args.local_dataset / "3DSSG_subset"
    staged_subset_root = args.staged_root / "data" / "3RScan" / "3DSSG_subset"
    preprocessed_root = args.staged_root / "output" / "datasets" / "OpenSG_3RScan" / "preprocessed"
    views_root = args.staged_root / "output" / "datasets" / "OpenSG_3RScan" / "views"
    scans_root = args.local_dataset / "3RScan" / "scans"

    official_train_scans = load_scans(subset_root / "relationships_train.json")
    official_train_scan_ids = {scan.get("scan") for scan in official_train_scans if scan.get("scan")}
    full_train_preprocessed = expected_preprocessed(official_train_scans, preprocessed_root)
    full_train_views_ready = sum(1 for scan_id in official_train_scan_ids if (views_root / f"{scan_id}_object2image.pkl").exists())
    modules = module_checks(args.python)
    hardware = gpu_info()

    blockers: list[str] = []
    if relationship_stats(staged_subset_root / "relationships_train.json")["subgraphs"] == 0:
        blockers.append("empty_staged_train_split")
    if full_train_preprocessed["ready"] < full_train_preprocessed["expected"]:
        blockers.append(
            f"missing_full_train_preprocessed:{full_train_preprocessed['ready']}/{full_train_preprocessed['expected']}"
        )
    if full_train_views_ready < len(official_train_scan_ids):
        blockers.append(f"missing_full_train_views:{full_train_views_ready}/{len(official_train_scan_ids)}")
    payload = scan_payload_counts(official_train_scan_ids, scans_root)
    if payload["existing_scan_dirs"] < payload["unique_scans"]:
        blockers.append(f"missing_full_train_scan_dirs:{payload['existing_scan_dirs']}/{payload['unique_scans']}")
    missing_modules = sorted(key for key, value in modules.items() if value["status"] != "ready")
    if missing_modules:
        blockers.append("missing_training_python_modules:" + ",".join(missing_modules))
    if hardware.get("gpu_count", 0) < 4:
        blockers.append(f"compute_below_official_example_gpus:{hardware.get('gpu_count', 0)}/4")

    status = "training_route_feasibility_ready" if not blockers else "training_route_not_immediate"
    if blockers:
        decision = (
            "Do not start Open3DSG training as the next execution step. The route is possible only as a "
            "separate reproduction investment after full train payload/preprocessing, environment setup, and "
            "compute planning. It should not block the H001 hypothesis unless a second-source Open3DSG metric "
            "is required."
        )
        next_action = (
            "Choose between two branches: wait for a trusted trained checkpoint, or create a dedicated "
            "Open3DSG training reproduction plan that stages full train data and installs the missing training environment."
        )
    else:
        decision = (
            "The Open3DSG training route is preflight-ready. Starting training is still a research-budget decision "
            "because it would create a separate baseline reproduction track."
        )
        next_action = (
            "Decide whether to launch the dedicated Open3DSG training run or keep waiting for a trusted trained checkpoint."
        )

    manifest: dict[str, Any] = {
        "schema_version": "h001_open3dsg_training_route_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "decision": decision,
        "source_facts": {
            "source": relpath(args.open3dsg_source),
            "official_training_command": "python open3dsg/scripts/run.py --epochs 100 --batch_size 4 --gpus 4 --workers 8 --use_rgb --dataset scannet --clip_model OpenSeg --blip --load_features [path to precomputed 2D features]",
            "test_requires_checkpoint": "python open3dsg/script/run.py --test --dataset 3rscan --checkpoint [path to checkpoint] ...",
            "supports_3rscan_fit": True,
            "leakage_guard": "Do not train on H001 hardened validation/test scans used for second-source evaluation.",
        },
        "official_3dssg_train": relationship_stats(subset_root / "relationships_train.json"),
        "official_3dssg_validation": relationship_stats(subset_root / "relationships_validation.json"),
        "staged_train": relationship_stats(staged_subset_root / "relationships_train.json"),
        "staged_validation": relationship_stats(staged_subset_root / "relationships_validation.json"),
        "full_train_payload": payload,
        "full_train_preprocessed": full_train_preprocessed,
        "full_train_views": {
            "ready": full_train_views_ready,
            "expected": len(official_train_scan_ids),
        },
        "current_h001_preprocessed": {
            "ready": sum(1 for _ in preprocessed_root.rglob("data_dict_*.pkl")) if preprocessed_root.exists() else 0,
            "note": "H001 validation/test preprocessed pickles are not a valid training set.",
        },
        "environment": {
            "python": relpath(args.python),
            "modules": modules,
        },
        "hardware": hardware,
        "blockers": blockers,
        "next_action": next_action,
    }

    write_json(args.output_dir / "manifest.json", manifest)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
