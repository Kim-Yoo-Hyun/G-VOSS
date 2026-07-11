#!/usr/bin/env python3
"""Freeze the untouched ReplicaSSG/FROSS dataset-level confirmation target."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "h001_replicassg_dataset_prospective_protocol_v1"
REPLICASSG_COMMIT = "94190972e0732543fcd0fdad7c9f2fc9c44ee0c4"
FROSS_COMMIT = "645153bf2b4b54ffd3d214ee4b8fdd2539b1bf55"
FROSS_WEIGHT_SHA256 = "03dc86a1a0f40321a2caa0e35ec2739f458837365455017b5a830a0f5349467c"
REPLICA_HABITAT_CONFIG_SHA256 = "253a179e638ddadcbcb6fc694d9aeb607e37386376ec4db37d7d92eebc62afdf"
EXPECTED_HASHES = {
    "test_scans.txt": "b7f8e16ad992562c76192dbfc96566dc1fdc4ab129a14bc1585e87badeb0dd33",
    "validation_scans.txt": "c07f7389f1cfbeecb814179a69a7456d132a8f1e71a006105972e77c8dc4563e",
    "objects.json": "3bceb3d838c7992ec7099dc4b46b49346b4961154376bff5748b1d1b7c5e96d5",
    "relationships.json": "11fd5a4b2fca5c654f0d5429fd381f174fa8668840532866c1efeb150442e240",
    "replica_to_visual_genome.json": "c9d3a8246faee97c6f679323652945b4292da250d2abcd3036a5a235da1d8014",
}
EXPECTED_TEST_SCANS = [
    "apartment_1",
    "apartment_2",
    "office_1",
    "office_3",
    "office_4",
    "room_1",
    "room_2",
    "hotel_0",
    "frl_apartment_3",
    "frl_apartment_4",
    "frl_apartment_5",
]
EXPECTED_VALIDATION_SCANS = [
    "apartment_0",
    "office_0",
    "office_2",
    "room_0",
    "frl_apartment_0",
    "frl_apartment_1",
    "frl_apartment_2",
]
PREDICATE_MAPPING = {
    "above": {"canonical_predicate": "higher than", "family": "relative_vertical"},
    "near": {"canonical_predicate": "close by", "family": "proximity"},
    "under": {"canonical_predicate": "lower than", "family": "relative_vertical"},
}
EXPECTED_ANNOTATION_PREDICATES = {
    "above",
    "against",
    "attached to",
    "has",
    "in",
    "near",
    "on",
    "under",
    "with",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dump_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--annotation-root",
        type=Path,
        default=Path("local_dataset/ReplicaSSG_code/files"),
    )
    parser.add_argument(
        "--source-prediction",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/replicassg/"
            "fross_raw/replica/"
            "predictions_gaussian_obj0.7_rel10_hell0.85_kfnone_test_gtpose.pkl"
        ),
    )
    parser.add_argument(
        "--weight-zip",
        type=Path,
        default=Path("local_dataset/FROSS_weights/VG.zip"),
    )
    parser.add_argument(
        "--replica-archive-sha256-file",
        type=Path,
        default=Path("local_dataset/ReplicaSSG_runtime/replica_v1_0.combined.sha256"),
    )
    parser.add_argument(
        "--replica-habitat-config-zip",
        type=Path,
        default=Path("local_dataset/ReplicaSSG_download/additional_habitat_configs.zip"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/replicassg/prospective_protocol/frozen_v1"
        ),
    )
    args = parser.parse_args()

    root = args.repo_root.resolve()
    annotation_root = args.annotation_root if args.annotation_root.is_absolute() else root / args.annotation_root
    prediction_path = args.source_prediction if args.source_prediction.is_absolute() else root / args.source_prediction
    weight_zip = args.weight_zip if args.weight_zip.is_absolute() else root / args.weight_zip
    archive_sha_path = (
        args.replica_archive_sha256_file
        if args.replica_archive_sha256_file.is_absolute()
        else root / args.replica_archive_sha256_file
    )
    habitat_config_zip = (
        args.replica_habitat_config_zip
        if args.replica_habitat_config_zip.is_absolute()
        else root / args.replica_habitat_config_zip
    )
    out = args.out if args.out.is_absolute() else root / args.out
    out.mkdir(parents=True, exist_ok=True)

    implementation_paths = {
        "adapter_sha256": root / "src/geocalib/export_replicassg_fross_predictions.py",
        "geometry_sha256": root / "src/geocalib/score_replicassg_geometry.py",
        "evaluator_sha256": root / "src/geocalib/run_replicassg_prospective_evaluation.py",
        "shard_merger_sha256": root / "src/geocalib/merge_replicassg_fross_shards.py",
        "streaming_runner_sha256": root / "scripts/run_replicassg_fross_streaming.sh",
        "dataset_stager_sha256": root / "scripts/extract_replicassg_test_habitat.sh",
        "engine_builder_sha256": root / "src/geocalib/build_fross_tensorrt_engines.py",
        "archive_auditor_sha256": root / "scripts/audit_replicassg_archive.sh",
        "scene_texture_stager_sha256": root / "scripts/extract_replicassg_scene_textures.sh",
        "compose_sha256": root / "configs/fross/compose.yaml",
        "runtime_dockerfile_sha256": root / "configs/fross/Dockerfile.runtime",
        "render_dockerfile_sha256": root / "configs/fross/Dockerfile.render",
    }

    validation_errors: list[str] = []
    implementation_hashes: dict[str, str] = {}
    for name, path in implementation_paths.items():
        if not path.is_file():
            validation_errors.append(f"missing_implementation:{path.relative_to(root)}")
        else:
            implementation_hashes[name] = sha256(path)
    observed_hashes = {}
    for name, expected in EXPECTED_HASHES.items():
        path = annotation_root / name
        if not path.is_file():
            validation_errors.append(f"missing_annotation:{name}")
            continue
        observed_hashes[name] = sha256(path)
        if observed_hashes[name] != expected:
            validation_errors.append(f"hash_mismatch:{name}")

    test_scans = read_lines(annotation_root / "test_scans.txt")
    validation_scans = read_lines(annotation_root / "validation_scans.txt")
    if test_scans != EXPECTED_TEST_SCANS:
        validation_errors.append("test_scan_order_or_membership_changed")
    if validation_scans != EXPECTED_VALIDATION_SCANS:
        validation_errors.append("validation_scan_order_or_membership_changed")
    if set(test_scans) & set(validation_scans):
        validation_errors.append("validation_test_overlap_nonzero")
    if prediction_path.exists():
        validation_errors.append("source_prediction_existed_before_protocol_freeze")
    observed_weight_sha256 = sha256(weight_zip) if weight_zip.is_file() else None
    if observed_weight_sha256 is None:
        validation_errors.append("missing_fross_weight_zip")
    elif observed_weight_sha256 != FROSS_WEIGHT_SHA256:
        validation_errors.append("fross_weight_hash_mismatch")
    observed_archive_sha256 = None
    if archive_sha_path.is_file():
        candidate = archive_sha_path.read_text(encoding="utf-8").split()[0]
        if len(candidate) == 64 and all(char in "0123456789abcdef" for char in candidate.lower()):
            observed_archive_sha256 = candidate.lower()
        else:
            validation_errors.append("invalid_replica_archive_hash_record")
    observed_habitat_config_sha256 = sha256(habitat_config_zip) if habitat_config_zip.is_file() else None
    if observed_habitat_config_sha256 is None:
        validation_errors.append("missing_replica_habitat_config_zip")
    elif observed_habitat_config_sha256 != REPLICA_HABITAT_CONFIG_SHA256:
        validation_errors.append("replica_habitat_config_hash_mismatch")

    relationships = json.loads((annotation_root / "relationships.json").read_text(encoding="utf-8"))
    objects = json.loads((annotation_root / "objects.json").read_text(encoding="utf-8"))
    mapping = json.loads((annotation_root / "replica_to_visual_genome.json").read_text(encoding="utf-8"))
    ontology = set(mapping["VisualGenome_rel"])
    if not set(PREDICATE_MAPPING).issubset(ontology):
        validation_errors.append("mapped_predicate_missing_from_source_ontology")

    object_by_scan: dict[str, dict[int, str]] = {}
    for scan in objects["scans"]:
        if scan["scan"] in test_scans:
            object_by_scan[scan["scan"]] = {
                int(obj["id"]): str(obj["label"]) for obj in scan["objects"]
            }

    observed_annotation_predicates = {
        str(rel[3])
        for scan in relationships["scans"]
        for rel in scan["relationships"]
    }
    observed_test_predicates: set[str] = set()
    gt_rows: list[dict[str, object]] = []
    by_predicate: Counter[str] = Counter()
    by_family: Counter[str] = Counter()
    by_scan: Counter[str] = Counter()
    endpoint_errors = 0
    for scan in relationships["scans"]:
        scan_id = scan["scan"]
        if scan_id not in test_scans:
            continue
        for subject_id, object_id, source_predicate_id, source_predicate in scan["relationships"]:
            observed_test_predicates.add(source_predicate)
            if source_predicate not in PREDICATE_MAPPING:
                continue
            if subject_id not in object_by_scan.get(scan_id, {}) or object_id not in object_by_scan.get(scan_id, {}):
                endpoint_errors += 1
                continue
            mapped = PREDICATE_MAPPING[source_predicate]
            row = {
                "family": mapped["family"],
                "gt_id": f"replicassg:test:{scan_id}:{subject_id}:{object_id}:{mapped['canonical_predicate']}",
                "object_id": int(object_id),
                "object_label": object_by_scan[scan_id][int(object_id)],
                "predicate": mapped["canonical_predicate"],
                "predicate_family": mapped["family"],
                "predicate_label": mapped["canonical_predicate"],
                "scan_id": scan_id,
                "source_predicate": source_predicate,
                "source_predicate_id": int(source_predicate_id),
                "split": "official_test",
                "subgraph_id": scan_id,
                "subject_id": int(subject_id),
                "subject_label": object_by_scan[scan_id][int(subject_id)],
                "subset_split_id": 0,
            }
            gt_rows.append(row)
            by_predicate[row["predicate"]] += 1
            by_family[row["family"]] += 1
            by_scan[scan_id] += 1

    if observed_annotation_predicates != EXPECTED_ANNOTATION_PREDICATES:
        validation_errors.append("annotation_predicate_set_changed")
    if endpoint_errors:
        validation_errors.append(f"mapped_gt_endpoint_errors:{endpoint_errors}")
    if not gt_rows:
        validation_errors.append("mapped_gt_denominator_empty")

    gt_rows.sort(key=lambda row: (row["scan_id"], row["subject_id"], row["object_id"], row["predicate"]))
    gt_path = out / "ground_truth.jsonl"
    with gt_path.open("w", encoding="utf-8") as handle:
        for row in gt_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    (out / "test_scans.txt").write_text("\n".join(test_scans) + "\n", encoding="utf-8")
    dump_json(out / "predicate_mapping.json", PREDICATE_MAPPING)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen_before_source_prediction" if not validation_errors else "invalid_freeze",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "classification_target": "untouched_dataset_and_source_prospective_confirmation",
        "dataset": {
            "name": "ReplicaSSG",
            "annotation_repo": "https://github.com/Howardkhh/ReplicaSSG",
            "annotation_commit": REPLICASSG_COMMIT,
            "base_dataset": "Replica v1.0",
            "base_archive_sha256": observed_archive_sha256,
            "base_archive_hash_status": "locked_pre_source" if observed_archive_sha256 else "pending_dataset_stage_pre_source",
            "additional_habitat_configs_sha256": observed_habitat_config_sha256,
            "test_scans": test_scans,
            "test_scan_count": len(test_scans),
            "validation_scans": validation_scans,
            "validation_scan_policy": "never_used_for_method_selection_calibration_thresholds_or_reporting_before_test_lock",
            "validation_test_overlap": len(set(test_scans) & set(validation_scans)),
            "annotation_hashes": observed_hashes,
        },
        "semantic_source": {
            "name": "FROSS_RTD-ETR_EGTR_VisualGenome_zero_shot",
            "repo": "https://github.com/Howardkhh/FROSS",
            "commit": FROSS_COMMIT,
            "weights_google_drive_file_id": "1glMkDC1UPQbd8JfjQa6VzNQRwMDAnOsI",
            "weight_zip_path": str(weight_zip.relative_to(root)),
            "weight_zip_sha256": observed_weight_sha256,
            "weight_hash_policy": "locked_after_download_and_before_engine_export_or inference",
            "engine_policy": "build FP16 TensorRT 10.8 engines on RTX 5090 from the released, weight-archive-locked FROSS ONNX graphs; do not refit or re-export network weights",
            "inference": {
                "split": "test",
                "label_categories": "replica",
                "obj_thresh": 0.7,
                "rel_topk": 10,
                "hellinger_threshold": 0.85,
                "keyframe_strategy": "none",
                "camera_pose": "ReplicaSSG_ground_truth_pose",
                "use_gt_2d_scene_graph": False,
                "use_validation_scenes": False,
                "not_preload": True,
            },
            "source_prediction_path": str(prediction_path.relative_to(root)),
            "source_prediction_present_at_freeze": prediction_path.exists(),
        },
        "scope": {
            "predicate_mapping": PREDICATE_MAPPING,
            "excluded_predicates": sorted(EXPECTED_ANNOTATION_PREDICATES - set(PREDICATE_MAPPING)),
            "observed_test_predicates": sorted(observed_test_predicates),
            "excluded_reason": "no exact pre-existing H001 predicate semantics; no post-hoc synonym or support-subtype mapping",
            "families": ["proximity", "relative_vertical"],
            "support_contact": "not evaluated because ReplicaSSG on/against are not exact standing-on/lying-on/supported-by labels",
            "coordinate_contract": {
                "source_mesh": "Replica habitat/mesh_semantic.ply",
                "metadata_up_axis": "raw_y",
                "canonical_transform": "(x_canonical,y_canonical,z_canonical)=(x_raw,z_raw,y_raw)",
                "rationale": "ReplicaSSG config semantic_up=[0,1,0]; GeoCalib models expect vertical z",
            },
        },
        "denominator": {
            "mapped_gt_rows": len(gt_rows),
            "by_predicate": dict(sorted(by_predicate.items())),
            "by_family": dict(sorted(by_family.items())),
            "by_scan": {scan: by_scan[scan] for scan in test_scans},
            "gt_presence_never_used_for_candidate_ranking_filtering_or_routing": True,
            "no_synthetic_predictions": True,
        },
        "adapter": {
            "object_matching": "official_FROSS_one_to_one_GT_to_prediction_matching_at_0.1m_with_0.5_overlap_and_0.75_ambiguity_ratio",
            "geometry_for_compatibility": "full_GT_instance_geometry_after_source_object_matching",
            "candidate_policy": "all three mapped predicate probabilities for every matched FROSS directed edge; actual edges only",
            "source_score": "FROSS normalized edge_cls vote probability",
        },
        "storage_execution": {
            "mode": "scene_wise_render_inference_and_verified_shard_merge",
            "scientific_equivalence": "identical full official trajectory and frozen FROSS settings per scene; only storage scheduling changes",
            "parent_render_assets_audit_bytes": 22934143370,
            "all_scene_extraction_gate_bytes": 15000000000,
            "texture_policy": "gate exceeded; extract exact official texture path one scene at a time",
            "transient_cleanup": "delete a scene sequence and extracted texture copy only after its one-scene prediction shard passes schema and scan-identity validation and its SHA256 is logged; retain the official compressed archive",
            "preserved": ["per_scene_prediction_shards", "merged_source_prediction", "instance_geometry", "cleanup_audit_log"],
        },
        "frozen_methods": {
            "semantic_only": "source_score",
            "family_product": "source_score * strict_train_only_family_compatibility",
            "rank_average_family": "0.5*(within_scene_semantic_percentile+within_scene_family_compatibility_percentile)",
            "rrf_c60": "1/(60+within_scene_semantic_rank)+1/(60+within_scene_family_compatibility_rank)",
            "factor_condition_diagnostics": {
                "product_M_T": "source_score * T-only compatibility",
                "product_M_G": "source_score * true G-only compatibility",
                "product_M_add": "source_score * additive T+G compatibility",
                "product_M_int": "source_score * T-by-G interaction compatibility",
                "promotion_policy": "report_only; no result-conditioned replacement of the four primary frozen methods",
            },
            "all_conditions_reported_no_winner_promotion": True,
            "model_sha256": "bf52a2d7c90d3f11e024f74ac6f3ba7a88f04d2865fb0df7a34a079b200f3c6f",
            "score_definition_sha256": "e9186633c6514f7eb2804e0cc91d2bc0fbb089be2680bcecaa61ecaaee718fac",
        },
        "frozen_controls": {
            "wrong_T_relative_vertical": "on exact-label GT candidate rows, compare correct predicate against its vertical inverse with G fixed",
            "close_by_endpoint_swap": "deterministically swap endpoint geometry and require/report compatibility invariance error",
            "vertical_inverse_equivariance": "swap endpoint geometry and invert higher/lower predicate; report compatibility equivariance error",
            "wrong_pair_geometry": "within-scene lexicographic directed-pair cyclic shift with predicate T fixed; exact-label GT rows only",
            "support_contact_endpoint_swap": "prohibited because this target has no exact H001 support/contact mapping",
            "conditions": ["family_specific", "M_T", "M_G", "M_add", "M_int"],
            "use_for_method_selection": False,
        },
        "implementation_hashes": implementation_hashes,
        "evaluation": {
            "context": "one official ReplicaSSG test scene",
            "context_count": len(test_scans),
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "bootstrap": {"unit": "scene", "resamples": 1000, "seed": 20260711, "shared_indices": True},
            "primary_product_gate": "paired dRecall@100 CI lower > -0.01 and paired dViolation@100 CI upper < 0",
            "framework_gate": "at least one pre-specified soft instantiation passes the product-form joint rule; report both",
            "formula_robust_gate": "both family_product and rank_average_family independently pass the joint rule",
            "zero_violation_denominator_policy": "report undefined for a scene/condition cell; never impute zero",
        },
        "claim_boundary": {
            "allowed_if_primary_passes": "dataset-level prospective transfer on ReplicaSSG proximity and relative-vertical relations",
            "not_allowed": [
                "support_contact transfer",
                "all-family transfer",
                "ReplicaSSG SOTA",
                "FROSS reproduction leaderboard claim",
                "post-result method or predicate remapping",
            ],
        },
        "outputs": {
            "ground_truth_jsonl": str(gt_path.relative_to(root)),
            "ground_truth_sha256": sha256(gt_path),
            "predicate_mapping_json": str((out / "predicate_mapping.json").relative_to(root)),
            "test_scans_txt": str((out / "test_scans.txt").relative_to(root)),
        },
        "validation_errors": validation_errors,
    }
    dump_json(out / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "test_scans": len(test_scans),
        "mapped_gt_rows": len(gt_rows),
        "by_predicate": manifest["denominator"]["by_predicate"],
        "validation_errors": validation_errors,
    }, indent=2, sort_keys=True))
    if validation_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
