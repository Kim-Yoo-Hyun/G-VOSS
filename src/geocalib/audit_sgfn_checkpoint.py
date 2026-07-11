#!/usr/bin/env python3
"""Audit the frozen SGFN checkpoint archive against the full_l160 contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch


SCHEMA_VERSION = "h001_sgfn_checkpoint_audit_v1"
EXPECTED = {
    "obj_predictor.fc3.weight": [160, 256],
    "obj_predictor.fc3.bias": [160],
    "rel_predictor.fc3.weight": [26, 256],
    "rel_predictor.fc3.bias": [26],
}
CORRECT_OFFICIAL_URL = (
    "https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/"
    "trained_models/SGFN_full_l160.zip"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    archive = resolve(root, args.archive)
    target_manifest = resolve(root, args.target_manifest)
    out = resolve(root, args.out)
    if not archive.exists() or not target_manifest.exists():
        raise FileNotFoundError(
            f"missing_input:archive={archive.exists()}:target={target_manifest.exists()}"
        )

    target = json.loads(target_manifest.read_text(encoding="utf-8"))
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        model_members = [name for name in names if name.endswith("/model_best.pt")]
        if len(model_members) != 1:
            raise ValueError(f"expected_one_model_best:{model_members}")
        model_bytes = bundle.read(model_members[0])

    with tempfile.NamedTemporaryFile(suffix=".pt") as handle:
        handle.write(model_bytes)
        handle.flush()
        checkpoint = torch.load(handle.name, map_location="cpu", weights_only=False)
    state = checkpoint.get("model", {})
    observed = {
        key: list(state[key].shape) if key in state else None
        for key in EXPECTED
    }
    compatibility = {
        key: observed[key] == expected for key, expected in EXPECTED.items()
    }
    compatible = all(compatibility.values())
    status = "checkpoint_compatible_full_l160" if compatible else "blocked_checkpoint_incompatible_full_l160"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "target_status": target.get("status"),
        "archive": {
            "path": relpath(root, archive),
            "sha256": sha256_file(archive),
            "size_bytes": archive.stat().st_size,
            "member_count": len(names),
            "model_member": model_members[0],
            "checkpoint_top_level_keys": sorted(checkpoint.keys()),
            "state_dict_key_count": len(state),
        },
        "expected_full_l160_classifier_shapes": EXPECTED,
        "observed_classifier_shapes": observed,
        "shape_checks": compatibility,
        "compatibility_gate_passed": compatible,
        "finding": (
            "archive contains a 20-object/8-relation model, not the locked 160-object/26-relation model"
            if not compatible
            else "archive classifier shapes match full_l160"
        ),
        "official_source_evidence": {
            "source_readme": "local_dataset/SceneGraphFusion_code/3DSSG/README.md",
            "readme_declares_separate_160_26_checkpoint": True,
            "correct_full_l160_url": CORRECT_OFFICIAL_URL,
            "correct_url_http_head_observed_2026_07_10": {
                "status": 200,
                "content_length": 86777444,
            },
        },
        "decision_required": {
            "reason": "target v1 explicitly forbids checkpoint substitution after an incompatible archive",
            "option_recommended": "freeze_v3_pre_inference_erratum_with_official_full_l160_url_then_continue",
            "option_strict": "mark_sgfn_target_blocked_and_select_a_new_untouched_source_under_a_new_protocol",
            "result_information_seen": False,
            "sgfn_predictions_or_metrics_exist": False,
        },
        "inputs": {
            "target_manifest": {
                "path": relpath(root, target_manifest),
                "sha256": sha256_file(target_manifest),
            }
        },
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_checkpoint_audit",
    }
    write_json(out, payload)
    print(json.dumps({"status": status, "observed": observed, "out": relpath(root, out)}))
    return 0 if compatible else 2


if __name__ == "__main__":
    raise SystemExit(main())
