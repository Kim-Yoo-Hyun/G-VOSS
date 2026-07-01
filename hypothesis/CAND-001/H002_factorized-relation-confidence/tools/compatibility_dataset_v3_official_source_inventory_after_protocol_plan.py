#!/usr/bin/env python3
"""Inventory official validation GT, geometry, and source-candidate availability for H002."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review"
DEFAULT_SUBSET_DIR = REPO_ROOT / "local_dataset/3DSSG_subset"
DEFAULT_SCAN_DIR = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan"

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_official_source_inventory_after_protocol_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_source_inventory_after_protocol_plan_input_errors"
SELECTED_PATH = "official_source_inventory_ready_select_candidate_materialization_protocol"
NEXT_TODO = "compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory"

FAMILY_PREDICATES = {
    "relative_horizontal": ["left", "right", "front", "behind"],
    "relative_vertical": ["higher than", "lower than"],
    "size_relative": ["bigger than", "smaller than"],
    "support_contact": ["standing on", "lying on"],
}
PREDICATE_TO_FAMILY = {
    predicate: family
    for family, predicates in FAMILY_PREDICATES.items()
    for predicate in predicates
}
PROMOTED_PREDICATES = set(PREDICATE_TO_FAMILY)

SOURCE_SPECS = [
    {
        "source_id": "vlsat_full_validation",
        "role": "secondary_source_bridge",
        "adapter_manifest": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/manifest.json",
        "adapter_predictions": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl",
        "geometry_manifest": "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/manifest.json",
        "geometry_verification": "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl",
        "provenance_note": "VL-SAT full official validation source from H001; read-only bridge candidate for H002.",
    },
    {
        "source_id": "open3dsg_recovery_relaxed_views_min2",
        "role": "secondary_source_bridge",
        "adapter_manifest": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/manifest.json",
        "adapter_predictions": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl",
        "geometry_manifest": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/manifest.json",
        "geometry_verification": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl",
        "provenance_note": "Open3DSG full validation recovery branch from H001; must disclose min-visible/recovery provenance if reused.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--subset-dir", type=Path, default=DEFAULT_SUBSET_DIR)
    parser.add_argument("--scan-dir", type=Path, default=DEFAULT_SCAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def relationship_predicate(rel: Any) -> str:
    if isinstance(rel, list) and len(rel) >= 4:
        return str(rel[3])
    if isinstance(rel, dict):
        return str(rel.get("predicate") or rel.get("relationship") or rel.get("relation") or "unknown")
    return "unknown"


def relationship_subject(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[0])
    if isinstance(rel, dict):
        value = rel.get("subject_id") or rel.get("subject") or rel.get("source_id")
        return int(value) if value is not None else None
    return None


def relationship_object(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[1])
    if isinstance(rel, dict):
        value = rel.get("object_id") or rel.get("object") or rel.get("target_id")
        return int(value) if value is not None else None
    return None


def scan_relationships(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        scans = data.get("scans", [])
    elif isinstance(data, list):
        scans = data
    else:
        scans = []
    return scans if isinstance(scans, list) else []


def semseg_object_index(scan_dir: Path, scan_id: str) -> tuple[set[int], set[int], bool, bool]:
    scan_root = scan_dir / scan_id
    semseg_path = scan_root / "semseg.v2.json"
    segs_path = scan_root / "mesh.refined.0.010000.segs.v2.json"
    if not semseg_path.exists():
        return set(), set(), False, segs_path.exists()
    try:
        semseg = read_json(semseg_path)
    except json.JSONDecodeError:
        return set(), set(), False, segs_path.exists()
    object_ids: set[int] = set()
    obb_ids: set[int] = set()
    for group in semseg.get("segGroups", []):
        object_id = group.get("objectId", group.get("id"))
        if object_id is None:
            continue
        oid = int(object_id)
        object_ids.add(oid)
        obb = group.get("obb")
        if isinstance(obb, dict) and obb.get("centroid") is not None and obb.get("axesLengths") is not None:
            obb_ids.add(oid)
    return object_ids, obb_ids, True, segs_path.exists()


def validation_gt_inventory(subset_dir: Path, scan_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    path = subset_dir / "relationships_validation.json"
    data = read_json(path)
    scans = scan_relationships(data)
    semseg_cache: dict[str, tuple[set[int], set[int], bool, bool]] = {}
    predicate_rows: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    family_rows: dict[str, Counter[str]] = defaultdict(Counter)
    family_scans: dict[str, set[str]] = defaultdict(set)
    predicate_scans: dict[tuple[str, str], set[str]] = defaultdict(set)

    for scan in scans:
        scan_id = str(scan.get("scan"))
        if scan_id not in semseg_cache:
            semseg_cache[scan_id] = semseg_object_index(scan_dir, scan_id)
        object_ids, obb_ids, semseg_exists, mesh_segs_exists = semseg_cache[scan_id]
        for rel in scan.get("relationships", []):
            predicate = relationship_predicate(rel)
            if predicate not in PROMOTED_PREDICATES:
                continue
            family = PREDICATE_TO_FAMILY[predicate]
            subject_id = relationship_subject(rel)
            object_id = relationship_object(rel)
            key = (family, predicate)
            for counter in [predicate_rows[key], family_rows[family]]:
                counter["gt_relations"] += 1
                counter["semseg_file_available"] += int(semseg_exists)
                counter["mesh_segs_file_available"] += int(mesh_segs_exists)
                pair_in_semseg = subject_id in object_ids and object_id in object_ids
                pair_has_obb = subject_id in obb_ids and object_id in obb_ids
                counter["subject_object_in_semseg"] += int(pair_in_semseg)
                counter["subject_object_obb_available"] += int(pair_has_obb)
            family_scans[family].add(scan_id)
            predicate_scans[key].add(scan_id)

    predicate_output: list[dict[str, Any]] = []
    for family, predicates in FAMILY_PREDICATES.items():
        for predicate in predicates:
            key = (family, predicate)
            c = predicate_rows[key]
            total = c["gt_relations"]
            predicate_output.append(
                {
                    "level": "predicate",
                    "route_family": family,
                    "predicate_label": predicate,
                    "gt_relations": total,
                    "unique_scans": len(predicate_scans[key]),
                    "semseg_file_available": c["semseg_file_available"],
                    "mesh_segs_file_available": c["mesh_segs_file_available"],
                    "subject_object_in_semseg": c["subject_object_in_semseg"],
                    "subject_object_obb_available": c["subject_object_obb_available"],
                    "obb_pair_coverage": round(c["subject_object_obb_available"] / total, 6) if total else 0.0,
                }
            )

    family_output: list[dict[str, Any]] = []
    for family, predicates in FAMILY_PREDICATES.items():
        c = family_rows[family]
        total = c["gt_relations"]
        family_output.append(
            {
                "level": "family",
                "route_family": family,
                "predicate_label": "ALL",
                "predicates": "; ".join(predicates),
                "gt_relations": total,
                "unique_scans": len(family_scans[family]),
                "semseg_file_available": c["semseg_file_available"],
                "mesh_segs_file_available": c["mesh_segs_file_available"],
                "subject_object_in_semseg": c["subject_object_in_semseg"],
                "subject_object_obb_available": c["subject_object_obb_available"],
                "obb_pair_coverage": round(c["subject_object_obb_available"] / total, 6) if total else 0.0,
                "inventory_status": "candidate_ready" if total and c["subject_object_obb_available"] else "blocked_no_geometry",
            }
        )

    split_summary = {
        "validation_file": rel_path(path),
        "validation_scans": len(scans),
        "promoted_gt_relations": sum(row["gt_relations"] for row in family_output),
        "semseg_scan_files_available": sum(1 for value in semseg_cache.values() if value[2]),
        "mesh_segs_scan_files_available": sum(1 for value in semseg_cache.values() if value[3]),
        "scans_with_any_promoted_family": len(set().union(*family_scans.values())) if family_scans else 0,
    }
    return family_output, predicate_output, split_summary


def source_row_key(row: dict[str, Any]) -> tuple[str, str, int | None, int | None, str]:
    edge = row.get("edge", {}) if isinstance(row.get("edge"), dict) else {}
    predicate = row.get("predicate", {}) if isinstance(row.get("predicate"), dict) else {}
    return (
        str(row.get("scan_id", "")),
        str(row.get("subgraph_id", "")),
        edge.get("subject_id"),
        edge.get("object_id"),
        str(predicate.get("predicate_label", "")),
    )


def count_adapter_predictions(path: Path) -> tuple[dict[str, Counter[str]], dict[tuple[str, str], Counter[str]], set[tuple[str, str, int | None, int | None, str]]]:
    family_counts: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    keys: set[tuple[str, str, int | None, int | None, str]] = set()
    family_scans: dict[str, set[str]] = defaultdict(set)
    predicate_scans: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in iter_jsonl(path):
        predicate_block = row.get("predicate", {}) if isinstance(row.get("predicate"), dict) else {}
        predicate = str(predicate_block.get("predicate_label", ""))
        if predicate not in PROMOTED_PREDICATES:
            continue
        family = PREDICATE_TO_FAMILY[predicate]
        key = (family, predicate)
        family_counts[family]["prediction_rows"] += 1
        predicate_counts[key]["prediction_rows"] += 1
        score = row.get("scores", {}).get("ranking_score") if isinstance(row.get("scores"), dict) else None
        rank = row.get("ranks", {}).get("semantic_rank_in_subgraph") if isinstance(row.get("ranks"), dict) else None
        family_counts[family]["ranking_score_available"] += int(score is not None)
        predicate_counts[key]["ranking_score_available"] += int(score is not None)
        family_counts[family]["semantic_rank_available"] += int(rank is not None)
        predicate_counts[key]["semantic_rank_available"] += int(rank is not None)
        scan_id = str(row.get("scan_id", ""))
        family_scans[family].add(scan_id)
        predicate_scans[key].add(scan_id)
        keys.add(source_row_key(row))
    for family, scans in family_scans.items():
        family_counts[family]["unique_scans"] = len(scans)
    for key, scans in predicate_scans.items():
        predicate_counts[key]["unique_scans"] = len(scans)
    return family_counts, predicate_counts, keys


def count_geometry_verification(path: Path) -> tuple[dict[str, Counter[str]], dict[tuple[str, str], Counter[str]], set[tuple[str, str, int | None, int | None, str]]]:
    family_counts: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    keys: set[tuple[str, str, int | None, int | None, str]] = set()
    for row in iter_jsonl(path):
        predicate_block = row.get("predicate", {}) if isinstance(row.get("predicate"), dict) else {}
        predicate = str(predicate_block.get("predicate_label", ""))
        if predicate not in PROMOTED_PREDICATES:
            continue
        family = PREDICATE_TO_FAMILY[predicate]
        key = (family, predicate)
        quality = row.get("quality", {}) if isinstance(row.get("quality"), dict) else {}
        verification = row.get("verification", {}) if isinstance(row.get("verification"), dict) else {}
        calibration = row.get("calibration", {}) if isinstance(row.get("calibration"), dict) else {}
        status = str(verification.get("verification_status") or row.get("verification_status") or "missing_status")
        for counter in [family_counts[family], predicate_counts[key]]:
            counter["verification_rows"] += 1
            counter["geometry_available"] += int(bool(quality.get("geometry_available")))
            counter["geometry_checkable"] += int(bool(quality.get("geometry_checkable")))
            counter["p_geom_valid_available"] += int(calibration.get("p_geom_valid") is not None)
            counter[f"status_{status}"] += 1
        keys.add(source_row_key(row))
    return family_counts, predicate_counts, keys


def source_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    family_rows: list[dict[str, Any]] = []
    predicate_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        adapter_manifest_path = REPO_ROOT / spec["adapter_manifest"]
        adapter_predictions_path = REPO_ROOT / spec["adapter_predictions"]
        geometry_manifest_path = REPO_ROOT / spec["geometry_manifest"]
        geometry_verification_path = REPO_ROOT / spec["geometry_verification"]
        adapter_manifest = read_json(adapter_manifest_path) if adapter_manifest_path.exists() else {}
        geometry_manifest = read_json(geometry_manifest_path) if geometry_manifest_path.exists() else {}
        manifest_rows.append(
            {
                "source_id": spec["source_id"],
                "role": spec["role"],
                "adapter_manifest": rel_path(adapter_manifest_path),
                "adapter_manifest_exists": adapter_manifest_path.exists(),
                "adapter_status": adapter_manifest.get("status", ""),
                "adapter_predictions": rel_path(adapter_predictions_path),
                "adapter_predictions_exists": adapter_predictions_path.exists(),
                "geometry_manifest": rel_path(geometry_manifest_path),
                "geometry_manifest_exists": geometry_manifest_path.exists(),
                "geometry_status": geometry_manifest.get("status", ""),
                "geometry_verification": rel_path(geometry_verification_path),
                "geometry_verification_exists": geometry_verification_path.exists(),
                "provenance_note": spec["provenance_note"],
            }
        )
        adapter_family, adapter_predicate, adapter_keys = count_adapter_predictions(adapter_predictions_path)
        geometry_family, geometry_predicate, geometry_keys = count_geometry_verification(geometry_verification_path)
        for family, predicates in FAMILY_PREDICATES.items():
            a = adapter_family[family]
            g = geometry_family[family]
            total = a["prediction_rows"]
            family_rows.append(
                {
                    "source_id": spec["source_id"],
                    "level": "family",
                    "route_family": family,
                    "predicate_label": "ALL",
                    "predicates": "; ".join(predicates),
                    "prediction_rows": total,
                    "unique_scans": a["unique_scans"],
                    "ranking_score_available": a["ranking_score_available"],
                    "semantic_rank_available": a["semantic_rank_available"],
                    "verification_rows": g["verification_rows"],
                    "geometry_available": g["geometry_available"],
                    "geometry_checkable": g["geometry_checkable"],
                    "p_geom_valid_available": g["p_geom_valid_available"],
                    "status_satisfied": g["status_satisfied"],
                    "status_violated": g["status_violated"],
                    "status_uncertain": g["status_uncertain"],
                    "status_unsupported": g["status_unsupported"],
                    "geometry_checkable_rate": round(g["geometry_checkable"] / g["verification_rows"], 6) if g["verification_rows"] else 0.0,
                    "inventory_status": "candidate_ready" if total and g["verification_rows"] else "missing_source_or_geometry",
                }
            )
        for family, predicates in FAMILY_PREDICATES.items():
            for predicate in predicates:
                key = (family, predicate)
                a = adapter_predicate[key]
                g = geometry_predicate[key]
                predicate_rows.append(
                    {
                        "source_id": spec["source_id"],
                        "level": "predicate",
                        "route_family": family,
                        "predicate_label": predicate,
                        "prediction_rows": a["prediction_rows"],
                        "unique_scans": a["unique_scans"],
                        "ranking_score_available": a["ranking_score_available"],
                        "semantic_rank_available": a["semantic_rank_available"],
                        "verification_rows": g["verification_rows"],
                        "geometry_available": g["geometry_available"],
                        "geometry_checkable": g["geometry_checkable"],
                        "p_geom_valid_available": g["p_geom_valid_available"],
                        "status_satisfied": g["status_satisfied"],
                        "status_violated": g["status_violated"],
                        "status_uncertain": g["status_uncertain"],
                        "status_unsupported": g["status_unsupported"],
                        "geometry_checkable_rate": round(g["geometry_checkable"] / g["verification_rows"], 6) if g["verification_rows"] else 0.0,
                    }
                )
        if adapter_keys != geometry_keys:
            missing_geom = len(adapter_keys - geometry_keys)
            missing_adapter = len(geometry_keys - adapter_keys)
            manifest_rows[-1]["adapter_geometry_key_mismatch"] = True
            manifest_rows[-1]["adapter_keys_missing_geometry"] = missing_geom
            manifest_rows[-1]["geometry_keys_missing_adapter"] = missing_adapter
        else:
            manifest_rows[-1]["adapter_geometry_key_mismatch"] = False
            manifest_rows[-1]["adapter_keys_missing_geometry"] = 0
            manifest_rows[-1]["geometry_keys_missing_adapter"] = 0
    return family_rows, predicate_rows, manifest_rows


def validate_inputs(
    *,
    protocol_summary: dict[str, Any],
    protocol_errors: list[dict[str, Any]],
    protocol_split_rows: list[dict[str, str]],
    gt_family_rows: list[dict[str, Any]],
    source_family_rows: list[dict[str, Any]],
    source_manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol_summary.get("next_todo")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_summary_validation_errors", "actual": protocol_summary.get("validation_errors")})
    if protocol_errors:
        errors.append({"error_type": "protocol_validation_error_rows_present", "rows": len(protocol_errors)})

    validation_rows = [row for row in protocol_split_rows if row.get("split") == "validation"]
    if len(validation_rows) != 4:
        errors.append({"error_type": "unexpected_validation_split_inventory_rows", "rows": len(validation_rows)})

    for row in gt_family_rows:
        if row["gt_relations"] <= 0:
            errors.append({"error_type": "gt_family_zero", "family": row["route_family"]})
        if row["subject_object_obb_available"] <= 0:
            errors.append({"error_type": "gt_family_no_obb_pairs", "family": row["route_family"]})

    for row in source_manifest_rows:
        for key in ["adapter_manifest_exists", "adapter_predictions_exists", "geometry_manifest_exists", "geometry_verification_exists"]:
            if row.get(key) is not True:
                errors.append({"error_type": "source_file_missing", "source_id": row["source_id"], "key": key})
        if row.get("adapter_geometry_key_mismatch"):
            errors.append(
                {
                    "error_type": "source_adapter_geometry_key_mismatch",
                    "source_id": row["source_id"],
                    "adapter_keys_missing_geometry": row.get("adapter_keys_missing_geometry"),
                    "geometry_keys_missing_adapter": row.get("geometry_keys_missing_adapter"),
                }
            )

    for source_id in {row["source_id"] for row in source_family_rows}:
        rows = [row for row in source_family_rows if row["source_id"] == source_id]
        if not rows:
            errors.append({"error_type": "source_family_rows_missing", "source_id": source_id})
        for row in rows:
            if row["prediction_rows"] <= 0:
                errors.append({"error_type": "source_family_prediction_zero", "source_id": source_id, "family": row["route_family"]})
            if row["verification_rows"] <= 0:
                errors.append({"error_type": "source_family_verification_zero", "source_id": source_id, "family": row["route_family"]})
    return errors


def source_readiness_rows(gt_family_rows: list[dict[str, Any]], source_family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    gt_by_family = {row["route_family"]: row for row in gt_family_rows}
    source_ids = sorted({row["source_id"] for row in source_family_rows})
    for family, gt in gt_by_family.items():
        for source_id in source_ids:
            source = next(row for row in source_family_rows if row["source_id"] == source_id and row["route_family"] == family)
            status = "ready_for_protocol_design"
            caveat = []
            if gt["obb_pair_coverage"] < 0.95:
                caveat.append("gt_geometry_coverage_below_0.95")
            if source["geometry_checkable_rate"] < 0.5:
                caveat.append("source_geometry_checkable_rate_below_0.5")
            if family == "support_contact":
                status = "diagnostic_challenging_route"
                caveat.append("support_contact_partial_internal_claim")
            rows.append(
                {
                    "route_family": family,
                    "source_id": source_id,
                    "gt_validation_relations": gt["gt_relations"],
                    "gt_obb_pair_coverage": gt["obb_pair_coverage"],
                    "source_prediction_rows": source["prediction_rows"],
                    "source_geometry_checkable_rate": source["geometry_checkable_rate"],
                    "readiness_status": status,
                    "caveat": "; ".join(caveat) if caveat else "none",
                }
            )
    return rows


def write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    gt_family_rows: list[dict[str, Any]],
    source_family_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Official Source Inventory",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "Official validation has enough GT/object-geometry/source-candidate material to proceed to candidate materialization protocol. This stage did not run official metrics.",
        "",
        "## GT Geometry Inventory",
        "",
        "| Family | GT relations | Unique scans | OBB pair coverage | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in gt_family_rows:
        lines.append(
            f"| `{row['route_family']}` | {row['gt_relations']} | {row['unique_scans']} | {row['obb_pair_coverage']:.6f} | {row['inventory_status']} |"
        )
    lines.extend(
        [
            "",
            "## Source Family Inventory",
            "",
            "| Source | Family | Prediction rows | Geometry checkable | p_geom_valid available | Checkable rate |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in source_family_rows:
        lines.append(
            f"| `{row['source_id']}` | `{row['route_family']}` | {row['prediction_rows']} | {row['geometry_checkable']} | {row['p_geom_valid_available']} | {row['geometry_checkable_rate']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Readiness",
            "",
            "| Family | Source | Readiness | Caveat |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in readiness_rows:
        lines.append(
            f"| `{row['route_family']}` | `{row['source_id']}` | {row['readiness_status']} | {row['caveat']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- official validation metric 생성 없음.",
            "- official test 사용 없음.",
            "- paper-level result 생성 없음.",
            "- H001 source artifacts는 read-only inventory로만 사용.",
            "- 다음 단계는 candidate materialization protocol이며 metric 실행이 아니다.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    protocol_errors = read_jsonl(args.protocol_dir / "validation_errors.jsonl")
    protocol_split_rows = read_csv(args.protocol_dir / "official_split_inventory.csv")
    gt_family_rows, gt_predicate_rows, gt_summary = validation_gt_inventory(args.subset_dir, args.scan_dir)
    source_family_rows, source_predicate_rows, source_manifest_rows = source_inventory()
    readiness = source_readiness_rows(gt_family_rows, source_family_rows)

    validation_errors = validate_inputs(
        protocol_summary=protocol_summary,
        protocol_errors=protocol_errors,
        protocol_split_rows=protocol_split_rows,
        gt_family_rows=gt_family_rows,
        source_family_rows=source_family_rows,
        source_manifest_rows=source_manifest_rows,
    )
    status = STATUS_ERRORS if validation_errors else STATUS_READY

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_official_source_inventory_inputs",
        "next_todo": NEXT_TODO if not validation_errors else "fix_official_source_inventory_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "subset_validation": rel_path(args.subset_dir / "relationships_validation.json"),
            "scan_dir": rel_path(args.scan_dir),
        },
        "gt_summary": gt_summary,
        "source_summary": {
            "source_count": len(source_manifest_rows),
            "sources": [row["source_id"] for row in source_manifest_rows],
        },
        "boundary": {
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "h001_artifacts_modified": False,
            "h001_artifacts_read_only_inventory": True,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
        },
        "selected_policy": {
            "next_stage": "official_candidate_materialization_protocol",
            "primary_route": "GT_counterfactual_mechanism",
            "secondary_routes": ["VL-SAT_source_candidates", "Open3DSG_source_candidates"],
            "support_contact_role": "diagnostic_challenging_route",
        },
        "output_artifacts": {
            "gt_geometry_inventory": rel_path(args.output_dir / "gt_geometry_inventory.csv"),
            "gt_predicate_inventory": rel_path(args.output_dir / "gt_predicate_inventory.csv"),
            "source_manifest_inventory": rel_path(args.output_dir / "source_manifest_inventory.csv"),
            "source_family_inventory": rel_path(args.output_dir / "source_family_inventory.csv"),
            "source_predicate_inventory": rel_path(args.output_dir / "source_predicate_inventory.csv"),
            "source_readiness": rel_path(args.output_dir / "source_readiness.csv"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_json(
        args.output_dir / "next_runner_contract.json",
        {
            "next_todo": summary["next_todo"],
            "runner_purpose": "Freeze official validation candidate materialization before metrics.",
            "candidate_routes": [
                {
                    "route": "GT_counterfactual_mechanism",
                    "role": "primary",
                    "inputs": ["3DSSG_subset validation GT", "3RScan semseg OBB geometry"],
                },
                {
                    "route": "VL-SAT_source_candidates",
                    "role": "secondary_bridge",
                    "inputs": ["H001 VL-SAT adapter predictions", "H001 VL-SAT geometry verification"],
                },
                {
                    "route": "Open3DSG_source_candidates",
                    "role": "secondary_bridge",
                    "inputs": ["H001 Open3DSG recovery adapter predictions", "H001 Open3DSG recovery geometry verification"],
                },
            ],
            "must_not_do": [
                "compute official validation metrics",
                "touch official test",
                "modify H001 artifacts",
                "enable p_rel/p_obs",
            ],
        },
    )
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "gt_geometry_inventory.csv", gt_family_rows)
    write_csv(args.output_dir / "gt_predicate_inventory.csv", gt_predicate_rows)
    write_csv(args.output_dir / "source_manifest_inventory.csv", source_manifest_rows)
    write_csv(args.output_dir / "source_family_inventory.csv", source_family_rows)
    write_csv(args.output_dir / "source_predicate_inventory.csv", source_predicate_rows)
    write_csv(args.output_dir / "source_readiness.csv", readiness)
    write_report(
        args.output_dir / "report.md",
        summary=summary,
        gt_family_rows=gt_family_rows,
        source_family_rows=source_family_rows,
        readiness_rows=readiness,
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
