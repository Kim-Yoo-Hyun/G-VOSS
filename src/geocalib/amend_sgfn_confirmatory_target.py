#!/usr/bin/env python3
"""Freeze the pre-inference SGFN split-identity correction as target v2."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_sgfn_confirmatory_target_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v2"),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_lines(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


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
    identity = payload["split_identity_audit"]
    return f"""# SGFN Confirmatory Target v2: Pre-Inference Split Erratum

Frozen at UTC: `{payload['created_at_utc']}`  
Status: `{payload['status']}`

## Erratum

Target v1 named `files/cvpr/validation_scans.txt` while also locking projection
into the existing 548 H001 evaluation subgraphs. A pre-inference identity audit
showed these two sets have zero overlap. The 548 H001 subgraphs contain
`{identity['h001_scan_count']}` unique scans and exactly equal the official SGFN
`files/cvpr/test_scans.txt` set (`{identity['test_intersection']}` / `{identity['official_test_count']}`),
whereas overlap with `validation_scans.txt` is `{identity['validation_intersection']}`.

This v2 contract corrects only the source split name and scan-list input. It was
frozen after checkpoint bytes were downloaded but before the archive was opened
or audited, before model construction/inference, and before any SGFN score or
H001 metric existed. Target v1 remains preserved as the failed preflight record.

## Immutable target

- Source/model/checkpoint: unchanged (`sgfn_official_full_l160`).
- Source-native inference split: official `files/cvpr/test_scans.txt`.
- Projection target: the already frozen 548 H001 evaluation subgraphs.
- H001 exact-label denominator: 3,972 in-scope GT rows.
- Missing source edges: never synthesized; coverage reported explicitly.

## Locked analysis (unchanged from v1)

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{{5,10,20,50,100}}`; primary K=100.
- Bootstrap: 1,000 H001-subgraph resamples, seed `20260710`.
- Validity gate: paired delta V@100 95% CI upper bound `< 0`.
- Recall guardrail: paired delta R@100 95% CI lower bound `> -0.01`.

No checkpoint, score, family, K, fusion, denominator, or missing-edge policy may
be changed after this point. All results must be reported regardless of direction.
"""


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    paths = {
        "target_v1_manifest": root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v1/manifest.json",
        "h001_subset": root / "local_dataset/3DSSG_subset/relationships_validation.json",
        "official_train_scans": root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/train_scans.txt",
        "official_validation_scans": root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/validation_scans.txt",
        "official_test_scans": root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/test_scans.txt",
        "base_confirmatory_manifest": root / "experiments/H001_geom_reliability/confirmatory_evaluation/frozen_v1/manifest.json",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")

    subset = json.loads(paths["h001_subset"].read_text(encoding="utf-8"))
    h001_scans = {str(row["scan"]) for row in subset.get("scans", [])}
    train_scans = read_lines(paths["official_train_scans"])
    validation_scans = read_lines(paths["official_validation_scans"])
    test_scans = read_lines(paths["official_test_scans"])
    downstream_roots = [
        root / "experiments/H001_geom_reliability/sources/sgfn/raw",
        root / "experiments/H001_geom_reliability/sources/sgfn/adapter",
        root / "experiments/H001_geom_reliability/sources/sgfn/geometry",
        root / "experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics",
    ]
    downstream_outputs_absent = not any(
        path.exists() and any(path.iterdir()) for path in downstream_roots
    )
    identity = {
        "h001_scan_count": len(h001_scans),
        "official_train_count": len(train_scans),
        "official_validation_count": len(validation_scans),
        "official_test_count": len(test_scans),
        "train_intersection": len(h001_scans & train_scans),
        "validation_intersection": len(h001_scans & validation_scans),
        "test_intersection": len(h001_scans & test_scans),
        "h001_equals_official_test": h001_scans == test_scans,
    }
    validations = {
        "target_v1_precedes_erratum": json.loads(
            paths["target_v1_manifest"].read_text(encoding="utf-8")
        ).get("status") == "target_frozen_pre_checkpoint_pre_inference",
        "v1_validation_mapping_is_zero_coverage": identity["validation_intersection"] == 0,
        "h001_target_exactly_equals_official_test": identity["h001_equals_official_test"],
        "no_sgfn_predictions_geometry_or_metrics_exist": downstream_outputs_absent,
    }
    status = (
        "target_v2_frozen_pre_checkpoint_audit_pre_inference"
        if all(validations.values())
        else "blocked_split_erratum_validation"
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "supersedes_for_execution": "sgfn_target_v1",
        "preservation_rule": "v1 remains immutable as failed pre-inference split preflight",
        "correction": {
            "from": "official files/cvpr/validation_scans.txt",
            "to": "official files/cvpr/test_scans.txt",
            "reason": "H001 548-subgraph target exactly equals official SGFN test split and has zero overlap with official validation split",
            "timing": "after checkpoint byte download; before archive open/audit, model inference, adapter export, geometry join, or metric computation",
        },
        "target": {
            "source_id": "sgfn_official_full_l160",
            "source_native_split": "official files/cvpr/test_scans.txt",
            "h001_subgraphs": 548,
            "h001_unique_scans": len(h001_scans),
            "h001_in_scope_gt_denominator": 3972,
        },
        "locked_analysis": {
            "families": ["support_contact", "proximity", "relative_vertical"],
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "main_score": "semantic_score * p_geom_valid_family",
            "comparators": [
                "semantic_only",
                "pooled_calibration",
                "geometry_only_family",
                "rank_average_fusion",
                "reciprocal_rank_fusion_c60",
            ],
            "bootstrap_unit": "H001 subgraph_id",
            "n_bootstrap": 1000,
            "seed": 20260710,
            "recall_guardrail": "delta_R_at_100_ci95_lower_gt_-0.01",
            "validity_gate": "delta_V_at_100_ci95_upper_lt_0",
        },
        "coverage_policy": {
            "missing_source_edges": "not synthesized; reported as missing coverage",
            "missing_subgraphs": "retained in GT denominator with zero matching predictions",
            "posthoc_recovery_forbidden": True,
        },
        "split_identity_audit": identity,
        "validations": validations,
        "inputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_amend",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "manifest.json", payload)
    (out / "protocol.md").write_text(protocol(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(root, out), "identity": identity}))
    return 0 if status.startswith("target_v2_frozen") else 2


if __name__ == "__main__":
    raise SystemExit(main())
