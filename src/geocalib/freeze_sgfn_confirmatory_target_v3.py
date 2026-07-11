#!/usr/bin/env python3
"""Freeze the user-authorized SGFN full_l160 checkpoint URL erratum."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_sgfn_confirmatory_target_v3"
CORRECT_URL = (
    "https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/"
    "trained_models/SGFN_full_l160.zip"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v3"),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def protocol(payload: dict[str, Any]) -> str:
    return f"""# SGFN Confirmatory Target v3: User-Authorized Checkpoint Erratum

Frozen at UTC: `{payload['created_at_utc']}`  
Status: `{payload['status']}`

## Authorization and correction

The user explicitly authorized `v3 pre-inference erratum` on 2026-07-10 KST.
Target v1 mistakenly linked `SGFN_full_l20.zip`; Docker audit established that
archive has 20-object/8-relation classifier heads and is incompatible with the
intended `config_SGFN_full_l160.yaml`. The official repository separately lists
`SGFN_full_l160.zip` for the 160-object/26-relation setup.

This correction was frozen before downloading the correct archive, before
model construction/inference, and before any SGFN prediction, geometry join, or
metric. It changes only the checkpoint URL. Target v2's split correction remains
in force: source-native inference uses official `files/cvpr/test_scans.txt`,
which exactly equals the 157 scans underlying the frozen 548 H001 subgraphs.

## Final immutable target

- Source id: `sgfn_official_full_l160`.
- Code: official 3DSSG repository at commit
  `4b783ecdc6caba1515b361f8a0643d0c2d568f52`.
- Configuration: `configs/config_SGFN_full_l160.yaml`.
- Checkpoint: `{CORRECT_URL}`.
- Required compatibility: object head 160, relation head 26.
- Split: official `files/cvpr/test_scans.txt` (157 scans).
- Projection target: frozen 548 H001 subgraphs and 3,972 in-scope exact-label
  GT rows; source-missing edges are never synthesized.

## Locked analysis (unchanged)

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{{5,10,20,50,100}}`; primary K=100.
- Bootstrap: 1,000 H001-subgraph resamples, seed `20260710`.
- Validity gate: paired delta V@100 95% CI upper bound `< 0`.
- Recall guardrail: paired delta R@100 95% CI lower bound `> -0.01`.

No further checkpoint, split, score, family, K, fusion, denominator, or
missing-edge-policy change is permitted. All results must be reported.
"""


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    inputs = {
        "target_v1_manifest": root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v1/manifest.json",
        "target_v2_manifest": root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v2/manifest.json",
        "checkpoint_audit": root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v2/checkpoint_audit.json",
        "official_readme": root / "local_dataset/SceneGraphFusion_code/3DSSG/README.md",
        "source_config": root / "local_dataset/SceneGraphFusion_code/3DSSG/configs/config_SGFN_full_l160.yaml",
        "official_test_scans": root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/test_scans.txt",
        "h001_ground_truth": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
    }
    missing = [name for name, path in inputs.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")
    v2 = json.loads(inputs["target_v2_manifest"].read_text(encoding="utf-8"))
    audit = json.loads(inputs["checkpoint_audit"].read_text(encoding="utf-8"))
    correct_checkpoint = root / "local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l160.zip"
    downstream_roots = [
        root / "experiments/H001_geom_reliability/sources/sgfn/raw",
        root / "experiments/H001_geom_reliability/sources/sgfn/adapter",
        root / "experiments/H001_geom_reliability/sources/sgfn/geometry",
        root / "experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics",
    ]
    validations = {
        "user_authorized_v3_pre_inference_erratum_2026_07_10_kst": True,
        "target_v2_split_identity_passed": v2.get("split_identity_audit", {}).get("h001_equals_official_test") is True,
        "wrong_archive_audit_failed_as_expected": audit.get("status") == "blocked_checkpoint_incompatible_full_l160",
        "audit_confirms_no_result_information_seen": audit.get("decision_required", {}).get("result_information_seen") is False,
        "correct_checkpoint_not_downloaded_at_v3_freeze": not correct_checkpoint.exists(),
        "no_sgfn_downstream_results_exist": not any(
            path.exists() and any(path.iterdir()) for path in downstream_roots
        ),
        "official_readme_contains_correct_url": CORRECT_URL in inputs["official_readme"].read_text(encoding="utf-8"),
    }
    status = (
        "target_v3_frozen_pre_correct_checkpoint_pre_inference"
        if all(validations.values())
        else "blocked_target_v3_freeze_validation"
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "authorization": {
            "decision": "v3 pre-inference erratum allowed",
            "actor": "user",
            "date_kst": "2026-07-10",
        },
        "supersedes_for_execution": "sgfn_target_v2",
        "preserved_history": ["sgfn_target_v1", "sgfn_target_v2"],
        "correction": {
            "field": "checkpoint_url",
            "from": "SGFN_full_l20.zip",
            "to": "SGFN_full_l160.zip",
            "correct_url": CORRECT_URL,
            "expected_http_content_length": 86777444,
            "timing": "pre-correct-checkpoint-download, pre-inference, pre-metric",
        },
        "target": {
            "source_id": "sgfn_official_full_l160",
            "source_config": "configs/config_SGFN_full_l160.yaml",
            "source_native_split": "official files/cvpr/test_scans.txt",
            "expected_object_classes": 160,
            "expected_relation_classes": 26,
            "h001_subgraphs": 548,
            "h001_unique_scans": 157,
            "h001_in_scope_gt_denominator": 3972,
        },
        "locked_analysis": v2["locked_analysis"],
        "coverage_policy": v2["coverage_policy"],
        "validations": validations,
        "inputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in inputs.items()
        },
        "next_gates": [
            "download_correct_archive_and_sha256",
            "audit_160_object_26_relation_classifier_shapes",
            "freeze_pinned_sgfn_runtime",
            "source_native_test_split_inference",
            "identity_preserving_h001_projection",
            "geometry_join_and_locked_confirmatory_metrics",
        ],
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_v3_freeze",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "manifest.json", payload)
    (out / "protocol.md").write_text(protocol(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(root, out)}))
    return 0 if status.startswith("target_v3_frozen") else 2


if __name__ == "__main__":
    raise SystemExit(main())
