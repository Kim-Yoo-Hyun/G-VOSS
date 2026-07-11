#!/usr/bin/env python3
"""Freeze the H001 train-only reconstruction before calibration or dev inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "h001_train_only_reestablishment_v1"
FAMILY = {
    "standing on": "support_contact",
    "lying on": "support_contact",
    "supported by": "support_contact",
    "close by": "proximity",
    "higher than": "relative_vertical",
    "lower than": "relative_vertical",
}


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


def write_lines(path: Path, values: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in sorted(values)), encoding="utf-8")


def gt_row(root: Path, entry: dict[str, Any], relation: list[Any], relation_index: int, split_name: str) -> dict[str, Any]:
    subject, obj, raw_id, label = int(relation[0]), int(relation[1]), int(relation[2]), str(relation[3])
    scan, split = str(entry["scan"]), int(entry["split"])
    objects = {int(key): str(value) for key, value in entry["objects"].items()}
    return {
        "schema_version": "h001_ground_truth_v1",
        "record_type": "ground_truth",
        "gt_id": f"gt:{split_name}:{scan}:{split}:{subject}:{obj}:{label}",
        "split_name": split_name,
        "subset_source": "local_dataset/3DSSG_subset/relationships_train.json",
        "scan_id": scan,
        "subset_split_id": split,
        "subgraph_id": f"{scan}_{split}",
        "subject_id": subject,
        "object_id": obj,
        "subject_label": objects[subject],
        "object_label": objects[obj],
        "predicate_label": label,
        "predicate_family": FAMILY.get(label, "unsupported_first_pass"),
        "raw_3dssg_predicate_id": raw_id,
        "vlsat_predicate_index": raw_id - 1,
        "source_relation_index": relation_index,
    }


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    if out.exists():
        raise FileExistsError(f"freeze_output_exists:{out}")
    source = root / "local_dataset/SceneGraphFusion_code/3DSSG"
    paths = {
        "train_scans": source / "files/cvpr/train_scans.txt",
        "internal_dev_scans": source / "files/cvpr/validation_scans.txt",
        "final_validation_scans": source / "files/cvpr/test_scans.txt",
        "train_annotations": root / "local_dataset/3DSSG_subset/relationships_train.json",
        "final_validation_annotations": root / "local_dataset/3DSSG_subset/relationships_validation.json",
        "relationships": root / "local_dataset/3DSSG_subset/relationships.txt",
        "source_config": source / "configs/config_3DSSG_full_l160.yaml",
        "checkpoint_manifest": root / "local_dataset/3DSSG_staged/checkpoint/manifest.json",
        "existing_score_provenance": root / "experiments/H001_geom_reliability/confirmatory_evaluation/frozen_v1/manifest.json",
        "calibration_exporter": root / "src/geocalib/export_calibration.py",
        "geometry_joiner": root / "src/geocalib/join_predictions.py",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_protocol_inputs:{missing}")
    train, dev, final = (read_scans(paths[name]) for name in ("train_scans", "internal_dev_scans", "final_validation_scans"))
    train_annotations = json.loads(paths["train_annotations"].read_text(encoding="utf-8"))["scans"]
    final_annotations = json.loads(paths["final_validation_annotations"].read_text(encoding="utf-8"))["scans"]
    train_annotation_scans = {str(row["scan"]) for row in train_annotations}
    final_annotation_scans = {str(row["scan"]) for row in final_annotations}
    split_rows = {
        "train": [row for row in train_annotations if str(row["scan"]) in train],
        "internal_dev": [row for row in train_annotations if str(row["scan"]) in dev],
        "final_validation": [row for row in final_annotations if str(row["scan"]) in final],
    }
    counts: dict[str, Any] = {}
    for name, rows in split_rows.items():
        counts[name] = {
            "scans": len({str(row["scan"]) for row in rows}),
            "contexts": len(rows),
            "directed_pairs": sum(len(row["objects"]) * (len(row["objects"]) - 1) for row in rows),
            "in_scope_gt": sum(1 for row in rows for relation in row["relationships"] if str(relation[3]) in FAMILY),
        }
    validations = {
        "split_counts_1061_117_157": (len(train), len(dev), len(final)) == (1061, 117, 157),
        "split_sets_pairwise_disjoint": not (train & dev or train & final or dev & final),
        "train_annotations_exactly_cover_train_plus_internal_dev": train_annotation_scans == train | dev,
        "final_annotations_exactly_cover_final_split": final_annotation_scans == final,
        "annotation_train_final_disjoint": not (train_annotation_scans & final_annotation_scans),
        "context_counts_3498_354_548": tuple(counts[name]["contexts"] for name in ("train", "internal_dev", "final_validation")) == (3498, 354, 548),
        "denominators_26253_2730_3972": tuple(counts[name]["in_scope_gt"] for name in ("train", "internal_dev", "final_validation")) == (26253, 2730, 3972),
        "all_raw_scan_directories_present": all((root / "local_dataset/3RScan/scans" / scan).is_dir() for scan in train | dev | final),
    }
    out.mkdir(parents=True, exist_ok=False)
    split_dir = out / "splits"
    write_lines(split_dir / "train_scans.txt", train)
    write_lines(split_dir / "internal_dev_scans.txt", dev)
    write_lines(split_dir / "final_validation_scans.txt", final)
    write_lines(split_dir / "method_development_scans.txt", train | dev)
    internal_subset = {"scans": split_rows["internal_dev"]}
    write_json(out / "internal_dev_subset.json", internal_subset)
    gt_path = out / "internal_dev_ground_truth.jsonl"
    with gt_path.open("w", encoding="utf-8") as handle:
        for entry in split_rows["internal_dev"]:
            for relation_index, relation in enumerate(entry["relationships"]):
                handle.write(json.dumps(gt_row(root, entry, relation, relation_index, "train_only_internal_dev"), ensure_ascii=False, sort_keys=True) + "\n")
    split_firewall = {
        "schema_version": SCHEMA,
        "status": "split_firewall_ready" if all(validations.values()) else "blocked_split_firewall",
        "roles": {
            "train": "all fitting, normalization, imputation, counterfactual construction",
            "internal_dev": "method acceptance and diagnostics only; never fit statistics or weights",
            "final_validation": "evaluation only after final lock; never selection or repair",
        },
        "counts": counts,
        "validations": validations,
        "hashes": {name: sha256_file(path) for name, path in paths.items() if name.endswith("scans") or name.endswith("annotations")},
    }
    write_json(out / "split_firewall.json", split_firewall)
    provenance = {
        "schema_version": SCHEMA,
        "verdict": "historical_parameter_fit_has_no_final_validation_rows_but_historical_method_selection_was_validation_informed",
        "components": {
            "geometry_features_and_counterfactual_policy": {"historical_provenance": "official_train_annotations", "action": "reuse_code_and_regenerate_train_only"},
            "normalization_and_calibrator_weights": {"historical_provenance": "train_only_with_pilot_internal_dev_diagnostics", "action": "refit_on_strict_1061_vs_117_firewall"},
            "family_specific_product_promotion": {"historical_provenance": "promoted_after_validation_results", "action": "freeze_now_as_theory_driven_default_in_reconstruction_not_prospective_original"},
            "rank_average_and_rrf": {"historical_provenance": "added_after_validation inspection", "action": "comparators_only_never_default_method"},
            "families_K_denominator_and_gates": {"historical_provenance": "previously observed validation", "action": "freeze_without further change and disclose reconstruction status"},
            "final_validation_metrics": {"historical_provenance": "already observed", "action": "re-evaluate locked method but never label untouched prospective"},
        },
        "claim_boundary": "leakage-controlled train-only reconstruction; prospective confirmation still requires a new target or independent human labels",
    }
    write_json(out / "provenance_audit.json", provenance)
    protocol = {
        "schema_version": SCHEMA,
        "status": "protocol_frozen_before_strict_calibration_and_internal_dev_inference" if all(validations.values()) else "blocked_protocol_freeze",
        "classification": "leakage_controlled_train_only_reconstruction_not_untouched_prospective_confirmation",
        "method": {
            "compatibility": "strict family-specific logistic C_e fit only on 1061-train-split calibration rows",
            "default_score": "semantic_score * C_family_strict",
            "default_score_rationale": "parameter-free lambda=1 multiplicative risk utility; not selected from final validation",
            "source_confidence_excluded_from_compatibility": True,
            "families": ["support_contact", "proximity", "relative_vertical"],
        },
        "comparators_all_reported_no_winner_promotion": [
            "semantic_only", "pooled_product", "geometry_only_family", "rank_average_family", "rrf_c60",
            "product_M_T", "product_M_G", "product_M_add", "product_M_int",
        ],
        "internal_dev_acceptance": {
            "source": "official SceneGraphFusion 3DSSG_full_l160 SGPN checkpoint",
            "primary_k": 100,
            "ks": [5, 10, 20, 50, 100],
            "recall_guardrail": "paired_delta_R_at_100_ci95_lower_gt_-0.01",
            "verifier_validity_gate": "paired_delta_V_at_100_ci95_upper_lt_0",
            "decision": "accept_or_reject_default_product_only; no formula or hyperparameter change after results",
            "controls": ["wrong_T_on_GT_relative_vertical", "close_by_swap", "vertical_inverse_equivariance", "wrong_pair_geometry_continuity"],
            "bootstrap": {"unit": "subgraph_id", "resamples": 1000, "seed": 20260711},
        },
        "final_evaluation": {
            "source": "same frozen 3DSSG_full_l160 checkpoint",
            "contexts": 548,
            "exact_label_denominator": 3972,
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "bootstrap": {"unit": "subgraph_id", "resamples": 1000, "seed": 20260712},
            "all_frozen_conditions_reported": True,
            "no_post_result_repair_or_winner_change": True,
        },
        "forbidden_information_flow": [
            "final_validation_rows_into_fit_or_normalization",
            "final_validation_metrics_into_method_acceptance",
            "source_specific_recalibration",
            "post_final_result_feature_family_score_or_K_change",
        ],
    }
    write_json(out / "protocol.json", protocol)
    manifest = {
        "schema_version": SCHEMA,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": protocol["status"],
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256_file(path)} for name, path in paths.items()},
        "outputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in {
                "protocol": out / "protocol.json",
                "split_firewall": out / "split_firewall.json",
                "provenance_audit": out / "provenance_audit.json",
                "internal_dev_subset": out / "internal_dev_subset.json",
                "internal_dev_ground_truth": gt_path,
                "train_scans": split_dir / "train_scans.txt",
                "internal_dev_scans": split_dir / "internal_dev_scans.txt",
                "final_validation_scans": split_dir / "final_validation_scans.txt",
                "method_development_scans": split_dir / "method_development_scans.txt",
            }.items()
        },
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_reestablishment_freeze",
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "counts": counts, "validations": validations, "out": relpath(root, out)}))
    return 0 if manifest["status"].startswith("protocol_frozen") else 2


if __name__ == "__main__":
    raise SystemExit(main())
