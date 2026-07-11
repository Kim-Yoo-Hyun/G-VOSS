#!/usr/bin/env python3
"""Freeze a fresh official 3DSSG/SGPN semantic-source evaluation before inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_3dssg_confirmatory_target_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
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


def read_scans(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    if out.exists():
        raise FileExistsError(f"target_freeze_already_exists:{out}")
    paths = {
        "official_readme": root / "local_dataset/SceneGraphFusion_code/3DSSG/README.md",
        "official_source_config": root / "local_dataset/SceneGraphFusion_code/3DSSG/configs/config_3DSSG_full_l160.yaml",
        "runtime_config": root / "configs/h001/3dssg_full_l160_confirmatory.yaml",
        "official_test_scans": root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/test_scans.txt",
        "official_validation_annotations": root / "local_dataset/3DSSG_subset/relationships_validation.json",
        "ground_truth": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
        "existing_family_model": root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json",
        "factor_protocol": root / "experiments/H001_geom_reliability/factor_isolation_protocol/frozen_v1/manifest.json",
        "factor_models": root / "experiments/H001_geom_reliability/factor_isolation_protocol/fitted_v1/models.json",
        "factor_model_manifest": root / "experiments/H001_geom_reliability/factor_isolation_protocol/fitted_v1/manifest.json",
        "calibration_train_scans": root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/h001_calib_pilot/train_scans.txt",
        "calibration_dev_scans": root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/h001_calib_pilot/dev_scans.txt",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_freeze_inputs:{missing}")
    factor_manifest = json.loads(paths["factor_model_manifest"].read_text(encoding="utf-8"))
    official_scans = read_scans(paths["official_test_scans"])
    calibration_scans = read_scans(paths["calibration_train_scans"]) | read_scans(paths["calibration_dev_scans"])
    target_output_root = root / "experiments/H001_geom_reliability/sources/3dssg_full_l160"
    prior_result_paths = [
        target_output_root / "raw/raw.jsonl",
        target_output_root / "adapter/predictions.jsonl",
        target_output_root / "geometry/verification.jsonl",
        target_output_root / "confirmatory_metrics/summary.json",
    ]
    validations = {
        "official_source_is_sgpn": "method: sgpn" in (root / "local_dataset/SceneGraphFusion_code/3DSSG/configs/method/config_base_3DSSG.yaml").read_text(encoding="utf-8"),
        "official_checkpoint_url_in_readme": "trained_models/3DSSG_full_l160.zip" in paths["official_readme"].read_text(encoding="utf-8"),
        "official_source_split_157_scans": len(official_scans) == 157,
        "target_disjoint_from_calibration_32_scans": not (official_scans & calibration_scans),
        "factor_models_frozen": factor_manifest.get("status") == "factor_models_frozen_pre_fresh_source_inference",
        "no_prior_target_results": not any(path.exists() for path in prior_result_paths),
        "ground_truth_hash_matches_frozen_protocol": sha256_file(paths["ground_truth"]) == "f1b11210efa3bc349e765bfeb11b6f0016c4142667f9afbe48b61df0c5042a5c",
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "target_frozen_pre_checkpoint_download_pre_inference" if all(validations.values()) else "blocked_target_freeze",
        "freshness": {
            "fresh_dimension": "previously_unseen_semantic_source",
            "semantic_source": "official SceneGraphFusion 3DSSG_full_l160 (SGPN implementation)",
            "dataset_target": "3DSSG official validation annotations, source-native alias files/cvpr/test_scans.txt",
            "dataset_target_previously_observed": True,
            "semantic_source_predictions_previously_observed": False,
            "calibration_target_scan_overlap": sorted(official_scans & calibration_scans),
        },
        "target": {
            "source_id": "3dssg_official_full_l160",
            "method": "sgpn",
            "checkpoint_url": "https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/trained_models/3DSSG_full_l160.zip",
            "expected_object_classes": 160,
            "expected_relation_classes": 26,
            "official_scans": 157,
            "evaluation_contexts": 548,
            "in_scope_exact_label_denominator": 3972,
            "coverage_policy": "all 548 contexts; no GT-conditioned filtering; no synthetic source edges",
        },
        "locked_scores": {
            "framework_instantiations": {
                "calibrated_product": "semantic_score * p_geom_valid_family",
                "rank_average": "equal mean of deterministic within-context percentile ranks of semantic_score and p_geom_valid_family",
            },
            "continuity_comparators": ["semantic_only", "pooled_calibration", "geometry_only_family", "reciprocal_rank_fusion_c60"],
            "factor_conditions_all_reported_no_winner_selection": ["M_T", "M_G", "M_add", "M_int"],
            "factor_fusions": ["semantic_score_times_C_condition", "equal_percentile_rank_average"],
            "forbidden": ["source_specific_recalibration", "lambda_tuning", "temperature_tuning", "threshold_tuning", "feature_selection", "condition_winner_promotion"],
        },
        "locked_evaluation": {
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "bootstrap_unit": "subgraph_id",
            "bootstrap_resamples": 1000,
            "bootstrap_seed": 20260710,
            "recall_guardrail": "paired delta_R_at_100_ci95_lower_gt_-0.01 versus semantic_only",
            "validity_gate": "paired delta_verifier_V_at_100_ci95_upper_lt_0 versus semantic_only",
            "joint_framework_gate": "both calibrated_product and rank_average must independently pass recall_guardrail and validity_gate",
            "family_reporting": ["support_contact", "proximity", "relative_vertical"],
            "denominators": "exact-label Recall denominator 3972; verifier V denominator actual selected checkable rows",
        },
        "validations": validations,
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256_file(path)} for name, path in paths.items()},
        "pre_inference_output_absence": [relpath(root, path) for path in prior_result_paths],
        "interpretation_boundary": {
            "confirmatory_for": "cross-source generalization of the frozen framework scores to an unseen official semantic source",
            "not_confirmatory_for": ["a new dataset", "human physical validity", "broad SOTA", "unique optimality of a fusion formula"],
            "verifier_V_is_diagnostic": True,
        },
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_target_freeze",
    }
    write_json(out, payload)
    print(json.dumps({"status": payload["status"], "validations": validations, "out": relpath(root, out)}))
    return 0 if payload["status"].startswith("target_frozen") else 2


if __name__ == "__main__":
    raise SystemExit(main())
