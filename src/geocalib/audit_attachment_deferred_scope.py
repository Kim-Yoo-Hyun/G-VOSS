#!/usr/bin/env python3
"""Audit attachment-deferred scope and freeze its evidence-schema plan.

This script does not implement a verifier and does not run source metrics. It
records denominator/source availability and the attachment-specific evidence
contract required before any promotion beyond the current H001 claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from paths import H001_HYPOTHESIS_REL


HYPOTHESIS_ROOT = H001_HYPOTHESIS_REL
HARDENED_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened"
HARDENED_GEOM_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened_geometry"
EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")

CURRENT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
TARGET_FAMILY = "attachment_deferred"
ATTACHMENT_LABELS = ("attached to", "hanging on", "connected to")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def get_family(row: dict[str, Any]) -> str | None:
    if "predicate_family" in row:
        return row.get("predicate_family")
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_family")
    return None


def get_label(row: dict[str, Any]) -> str | None:
    if "predicate_label" in row:
        return row.get("predicate_label")
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_label")
    return None


def edge_ids(row: dict[str, Any]) -> tuple[Any, Any]:
    edge = row.get("edge") if isinstance(row.get("edge"), dict) else {}
    return row.get("subject_id", edge.get("subject_id")), row.get("object_id", edge.get("object_id"))


def count_family_labels(path: Path) -> dict[str, Any]:
    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    family_label_counts: Counter[str] = Counter()
    target_label_counts: Counter[str] = Counter()
    total = 0
    subgraphs: set[str] = set()
    scans: set[str] = set()
    directed_pairs: set[tuple[str, str, Any, Any]] = set()
    target_scans: set[str] = set()
    target_subgraphs: set[str] = set()
    target_pairs: set[tuple[str, str, Any, Any]] = set()

    for row in iter_jsonl(path):
        total += 1
        family = get_family(row) or "missing_family"
        label = get_label(row) or "missing_label"
        family_counts[family] += 1
        label_counts[label] += 1
        family_label_counts[f"{family}::{label}"] += 1

        scan_id = row.get("scan_id")
        subgraph_id = row.get("subgraph_id")
        subject_id, object_id = edge_ids(row)

        if scan_id:
            scans.add(str(scan_id))
        if subgraph_id:
            subgraphs.add(str(subgraph_id))
        if scan_id and subgraph_id and subject_id is not None and object_id is not None:
            pair_key = (str(scan_id), str(subgraph_id), subject_id, object_id)
            directed_pairs.add(pair_key)
            if family == TARGET_FAMILY:
                target_pairs.add(pair_key)
        if family == TARGET_FAMILY:
            target_label_counts[label] += 1
            if scan_id:
                target_scans.add(str(scan_id))
            if subgraph_id:
                target_subgraphs.add(str(subgraph_id))

    return {
        "path": str(path),
        "rows": total,
        "scans": len(scans),
        "subgraphs": len(subgraphs),
        "directed_pairs": len(directed_pairs),
        "family_counts": dict(sorted(family_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "family_label_counts": dict(sorted(family_label_counts.items())),
        "attachment_deferred_rows": family_counts.get(TARGET_FAMILY, 0),
        "attachment_label_counts": {
            label: target_label_counts.get(label, 0) for label in ATTACHMENT_LABELS
        },
        "attachment_scans": len(target_scans),
        "attachment_subgraphs": len(target_subgraphs),
        "attachment_directed_pairs": len(target_pairs),
    }


def count_verification_status(path: Path) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    quality_geometry_available: Counter[str] = Counter()
    geometry_feature_key_counts: Counter[str] = Counter()
    geometry_source_counts: Counter[str] = Counter()
    missing_object_rows = 0
    rows = 0

    for row in iter_jsonl(path):
        if get_family(row) != TARGET_FAMILY:
            continue
        rows += 1
        label = get_label(row) or "missing_label"
        label_counts[label] += 1
        status_counts[str(row.get("verification_status", "missing_status"))] += 1

        quality = row.get("quality") if isinstance(row.get("quality"), dict) else {}
        quality_geometry_available[str(quality.get("geometry_available", "missing"))] += 1

        verification = row.get("verification")
        if isinstance(verification, dict):
            for reason in verification.get("reason_codes", []) or []:
                reason_counts[str(reason)] += 1

        geometry = row.get("geometry") if isinstance(row.get("geometry"), dict) else {}
        geometry_source_counts[str(geometry.get("geometry_source", "missing"))] += 1
        features = geometry.get("features") if isinstance(geometry.get("features"), dict) else {}
        for key, value in features.items():
            if value is not None:
                geometry_feature_key_counts[str(key)] += 1
        if geometry.get("missing_object_ids"):
            missing_object_rows += 1

    return {
        "path": str(path),
        "attachment_deferred_rows": rows,
        "label_counts": dict(sorted(label_counts.items())),
        "verification_status_counts": dict(sorted(status_counts.items())),
        "reason_code_counts": dict(sorted(reason_counts.items())),
        "quality_geometry_available_counts": dict(sorted(quality_geometry_available.items())),
        "geometry_source_counts": dict(sorted(geometry_source_counts.items())),
        "geometry_feature_key_counts": dict(sorted(geometry_feature_key_counts.items())),
        "missing_object_rows": missing_object_rows,
    }


def attachment_evidence_schema() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_evidence_schema_v1",
        "status": "schema_plan_frozen_no_verifier_no_metric",
        "target_family": TARGET_FAMILY,
        "predicate_labels": list(ATTACHMENT_LABELS),
        "subtypes": {
            "attached to": [
                "attached_to_vertical_or_overhead_surface",
                "attached_to_furniture_or_fixture",
                "ambiguous_functional_attachment",
            ],
            "hanging on": [
                "hanging_from_vertical_surface",
                "hanging_from_overhead_or_fixture",
                "ambiguous_draped_or_occluded_hanging",
            ],
            "connected to": [
                "connected_adjacent_or_contiguous",
                "connected_by_fixture_or_part",
                "ambiguous_functional_connection",
            ],
        },
        "existing_reusable_evidence": [
            "object labels",
            "subject/object OBB extents",
            "3D and XY distance",
            "normalized distance",
            "projected XY overlap",
            "vertical extents and gaps",
            "segmented object point clouds when available",
        ],
        "new_required_evidence": [
            "candidate attachment surface type: wall, ceiling, floor, furniture, fixture, or unknown",
            "local object-to-surface distance",
            "local point-contact or near-contact count",
            "contact patch size or projected overlap on candidate surface",
            "surface normal / dominant plane orientation",
            "hanging gravity cue: subject suspended above floor or near vertical/overhead support",
            "contradictory support cue: object is better explained as floor/table supported",
            "optional class-pair affordance cue, never as the sole proof of validity",
        ],
        "status_policy_principles": {
            "satisfied": [
                "clear near-contact with plausible attachment surface",
                "surface orientation and predicate subtype agree",
                "no stronger contradictory support explanation",
            ],
            "violated": [
                "object pair is far from any plausible attachment surface",
                "predicate requires hanging/attachment but geometry indicates unrelated separated objects",
                "support surface type contradicts the predicate with sufficient geometric margin",
            ],
            "uncertain": [
                "mesh or segmented points are insufficient",
                "visible geometry supports multiple explanations",
                "relation likely depends on hidden fasteners, wires, or functional context",
                "class affordance suggests attachment but geometry is not decisive",
            ],
        },
        "counterfactual_negative_strategies": [
            "wrong_surface_replacement",
            "far_object_pair",
            "wrong_pair_attachment",
            "shuffled_geometry_within_attachment_family",
            "floor_support_replacement_for_wall_or_hanging_cases",
            "gravity_inconsistent_hanging_case",
        ],
        "required_controls": [
            "geometry_only_ranking",
            "distance_or_contact_only_ranking",
            "shuffled_geometry",
            "wrong_pair_geometry",
            "surface_type_ablation",
            "class_affordance_only_ablation",
        ],
        "function_reasoning_boundary": {
            "allowed_after_relation_metrics": [
                "small physical-precondition case study",
                "wall-mounted or hanging plausibility query",
                "connected-object consistency query",
            ],
            "blocked_until_separate_benchmark": [
                "broad affordance prediction",
                "robotics task success claim",
                "general functional relation discovery",
            ],
        },
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    denom = manifest["denominator"]
    gt = manifest["ground_truth"]
    source_rows = manifest["source_prediction_rows"]
    verification = manifest["existing_verification_status"]

    lines = [
        "# Attachment Deferred Scope Audit",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This audit does not change the current H001 paper claim. "
        "`attachment_deferred` is a future upgrade path and remains outside "
        "paper metrics until its attachment-specific evidence extractor, "
        "verifier, calibration, controls, GT evaluation, source metrics, "
        "bootstrap CI, and audit gates pass.",
        "",
        "## Denominator",
        "",
        markdown_table(
            ["Item", "Count"],
            [
                ["current H001 GT denominator", denom["current_h001_gt_denominator"]],
                ["attachment_deferred GT rows", denom["attachment_deferred_gt_rows"]],
                ["expanded candidate denominator", denom["expanded_candidate_denominator"]],
                ["all held-out GT rows", denom["all_held_out_gt_rows"]],
                ["expanded denominator share", denom["expanded_denominator_share"]],
            ],
        ).rstrip(),
        "",
        "## Attachment GT Labels",
        "",
        markdown_table(
            ["Label", "GT rows"],
            [[label, gt["attachment_label_counts"].get(label, 0)] for label in ATTACHMENT_LABELS],
        ).rstrip(),
        "",
        "## Source Prediction Rows",
        "",
        markdown_table(
            ["Source", "attachment_deferred rows"],
            [
                ["VL-SAT", source_rows["vlsat"]["attachment_deferred_rows"]],
                ["Open3DSG", source_rows["open3dsg"]["attachment_deferred_rows"]],
            ],
        ).rstrip(),
        "",
        "## Existing Verification Status",
        "",
        "The current geometry join intentionally treats `attachment_deferred` as out of scope.",
        "",
        markdown_table(
            ["Source", "Status", "Rows"],
            [
                [source, status, count]
                for source, payload in verification.items()
                for status, count in payload["verification_status_counts"].items()
            ],
        ).rstrip(),
        "",
        "## Evidence Schema Decision",
        "",
        "- Reuse OBB distance/overlap and segmented point evidence where available.",
        "- Add attachment-specific surface/contact/normal/gravity fields before any verifier.",
        "- Treat object affordance as optional context, not as a proof of physical validity.",
        "- Preserve exact predicate-label recall for `attached to`, `hanging on`, and `connected to`.",
        "",
        "## Next Gate",
        "",
        f"`{manifest['next_gate']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    lines.append("")
    ensure_dir(path.parent)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--out",
        type=Path,
        default=EXPERIMENT_ROOT / "sources/attachment_deferred/scope_audit",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    out = args.out
    if not out.is_absolute():
        out = repo_root / out

    gt_path = repo_root / HARDENED_ROOT / "ground_truth.jsonl"
    vlsat_pred_path = repo_root / HARDENED_ROOT / "predictions.jsonl"
    vlsat_ver_path = repo_root / HARDENED_GEOM_ROOT / "verification.jsonl"
    open_pred_path = repo_root / EXPERIMENT_ROOT / "sources/open3dsg/adapter/predictions.jsonl"
    open_ver_path = repo_root / EXPERIMENT_ROOT / "sources/open3dsg/geometry/verification.jsonl"
    denom_path = repo_root / EXPERIMENT_ROOT / "sources/open3dsg/metric_scope/denominator_policy.json"
    mapping_path = repo_root / EXPERIMENT_ROOT / "sources/open3dsg/metric_scope/predicate_mapping.json"

    required_paths = [
        gt_path,
        vlsat_pred_path,
        vlsat_ver_path,
        open_pred_path,
        open_ver_path,
        denom_path,
        mapping_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required audit inputs: " + ", ".join(missing))

    denominator_policy = read_json(denom_path)
    predicate_mapping = read_json(mapping_path)
    gt_counts = count_family_labels(gt_path)
    vlsat_counts = count_family_labels(vlsat_pred_path)
    open_counts = count_family_labels(open_pred_path)
    vlsat_ver = count_verification_status(vlsat_ver_path)
    open_ver = count_verification_status(open_ver_path)
    evidence_schema = attachment_evidence_schema()

    metric_denominator = denominator_policy["metric_denominator"]
    current_denominator = metric_denominator["h001_geometry_checkable_gt_denominator"]
    attachment_rows = metric_denominator["excluded_family_counts"][TARGET_FAMILY]
    expanded_denominator = current_denominator + attachment_rows
    all_rows = metric_denominator["fixed_gt_rows"]

    manifest = {
        "schema_version": "h001_attachment_deferred_scope_audit_v1",
        "status": "attachment_deferred_scope_schema_ready_no_metric_execution",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "current_families": list(CURRENT_FAMILIES),
            "candidate_family": TARGET_FAMILY,
            "promotion_rule": "Do not promote until attachment evidence extractor, verifier, calibration, source metrics, controls, bootstrap CI, and audit match the current H001 evidence standard.",
            "function_reasoning_boundary": "Function reasoning is only a secondary pilot after relation reliability passes.",
        },
        "denominator": {
            "all_held_out_gt_rows": all_rows,
            "current_h001_gt_denominator": current_denominator,
            "attachment_deferred_gt_rows": attachment_rows,
            "expanded_candidate_denominator": expanded_denominator,
            "expanded_denominator_share": round(expanded_denominator / all_rows, 4),
        },
        "ground_truth": gt_counts,
        "source_prediction_rows": {
            "vlsat": vlsat_counts,
            "open3dsg": open_counts,
        },
        "existing_verification_status": {
            "vlsat": vlsat_ver,
            "open3dsg": open_ver,
        },
        "predicate_mapping_source": {
            "path": str(mapping_path),
            "attachment_deferred_labels": predicate_mapping["predicate_family_map"][TARGET_FAMILY],
        },
        "evidence_schema_file": "evidence_schema.json",
        "next_gate": "G1_attachment_evidence_extractor_design",
        "blockers": [
            "attachment_evidence_extractor_not_implemented",
            "surface_type_and_normal_estimation_not_validated",
            "local_point_contact_policy_not_frozen",
            "attachment_verifier_not_implemented",
            "train_dev_calibration_not_built",
            "gt_counterfactual_verifier_eval_not_run",
            "source_metrics_not_run",
            "bootstrap_ci_not_run",
            "failure_analysis_and_visual_audit_not_run",
            "function_reasoning_pilot_blocked_until_relation_metrics_pass",
        ],
        "inputs": {
            "ground_truth_jsonl": str(gt_path),
            "vlsat_predictions_jsonl": str(vlsat_pred_path),
            "vlsat_verification_jsonl": str(vlsat_ver_path),
            "open3dsg_predictions_jsonl": str(open_pred_path),
            "open3dsg_verification_jsonl": str(open_ver_path),
            "denominator_policy_json": str(denom_path),
            "predicate_mapping_json": str(mapping_path),
        },
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(
        out / "label_counts.json",
        {
            "ground_truth": gt_counts,
            "vlsat_predictions": vlsat_counts,
            "open3dsg_predictions": open_counts,
            "vlsat_existing_verification": vlsat_ver,
            "open3dsg_existing_verification": open_ver,
        },
    )
    write_json(out / "evidence_schema.json", evidence_schema)
    write_report(out / "report.md", manifest)

    print(json.dumps({"status": manifest["status"], "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
