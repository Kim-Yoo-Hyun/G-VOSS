#!/usr/bin/env python3
"""Audit relative-horizontal scope before any metric promotion.

This script does not implement a verifier and does not run paper metrics. It
records the denominator, source-row availability, current unsupported status,
and promotion blockers for the optional relative-horizontal expansion track.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HYPOTHESIS_ROOT = Path("hypothesis/CAND-001/H001_geometry-grounded-verification")
HARDENED_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened"
HARDENED_GEOM_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened_geometry"
EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")

RELATIVE_HORIZONTAL_LABELS = ("left", "right", "front", "behind")
CURRENT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
TARGET_FAMILY = "relative_horizontal"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path):
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


def count_family_labels(path: Path) -> dict[str, Any]:
    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    family_label_counts: Counter[str] = Counter()
    total = 0
    subgraphs: set[str] = set()
    scans: set[str] = set()
    directed_pairs: set[tuple[str, str, Any, Any]] = set()

    for row in iter_jsonl(path):
        total += 1
        family = get_family(row) or "missing_family"
        label = get_label(row) or "missing_label"
        family_counts[family] += 1
        label_counts[label] += 1
        family_label_counts[f"{family}::{label}"] += 1
        scan_id = row.get("scan_id")
        subgraph_id = row.get("subgraph_id")
        edge = row.get("edge") if isinstance(row.get("edge"), dict) else {}
        subject_id = row.get("subject_id", edge.get("subject_id"))
        object_id = row.get("object_id", edge.get("object_id"))
        if scan_id:
            scans.add(str(scan_id))
        if subgraph_id:
            subgraphs.add(str(subgraph_id))
        if scan_id and subgraph_id and subject_id is not None and object_id is not None:
            directed_pairs.add((str(scan_id), str(subgraph_id), subject_id, object_id))

    return {
        "path": str(path),
        "rows": total,
        "scans": len(scans),
        "subgraphs": len(subgraphs),
        "directed_pairs": len(directed_pairs),
        "family_counts": dict(sorted(family_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "family_label_counts": dict(sorted(family_label_counts.items())),
        "relative_horizontal_rows": family_counts.get(TARGET_FAMILY, 0),
        "relative_horizontal_label_counts": {
            label: label_counts.get(label, 0) for label in RELATIVE_HORIZONTAL_LABELS
        },
    }


def count_verification_status(path: Path) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    rows = 0

    for row in iter_jsonl(path):
        if get_family(row) != TARGET_FAMILY:
            continue
        rows += 1
        label = get_label(row) or "missing_label"
        label_counts[label] += 1
        status_counts[str(row.get("verification_status", "missing_status"))] += 1
        verification = row.get("verification")
        if isinstance(verification, dict):
            for reason in verification.get("reason_codes", []) or []:
                reason_counts[str(reason)] += 1

    return {
        "path": str(path),
        "relative_horizontal_rows": rows,
        "label_counts": dict(sorted(label_counts.items())),
        "verification_status_counts": dict(sorted(status_counts.items())),
        "reason_code_counts": dict(sorted(reason_counts.items())),
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
        "# Relative Horizontal Scope Audit",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This audit does not change the current H001 paper claim. "
        "`relative_horizontal` remains a separate expansion track until it "
        "passes coordinate-frame validation, verifier design, calibration, "
        "metrics, controls, bootstrap CI, and failure/audit gates.",
        "",
        "## Denominator",
        "",
        markdown_table(
            ["Item", "Count"],
            [
                ["current H001 GT denominator", denom["current_h001_gt_denominator"]],
                ["relative_horizontal GT rows", denom["relative_horizontal_gt_rows"]],
                ["expanded candidate denominator", denom["expanded_candidate_denominator"]],
                ["all held-out GT rows", denom["all_held_out_gt_rows"]],
                ["expanded denominator share", denom["expanded_denominator_share"]],
            ],
        ).rstrip(),
        "",
        "## Relative-Horizontal GT Labels",
        "",
        markdown_table(
            ["Label", "GT rows"],
            [[label, gt["relative_horizontal_label_counts"].get(label, 0)] for label in RELATIVE_HORIZONTAL_LABELS],
        ).rstrip(),
        "",
        "## Source Prediction Rows",
        "",
        markdown_table(
            ["Source", "relative_horizontal rows"],
            [
                ["VL-SAT", source_rows["vlsat"]["relative_horizontal_rows"]],
                ["Open3DSG", source_rows["open3dsg"]["relative_horizontal_rows"]],
            ],
        ).rstrip(),
        "",
        "## Existing Verification Status",
        "",
        "The current geometry join intentionally treats `relative_horizontal` as out of scope.",
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
        "## Required First Gate",
        "",
        "- Freeze coordinate-frame semantics for `left/right/front/behind`.",
        "- Add a wrong-frame or axis-flip control before metric promotion.",
        "- Keep exact predicate-label recall; family grouping must not collapse labels.",
        "- Keep the current main paper claim unchanged until all promotion gates pass.",
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
        default=EXPERIMENT_ROOT / "sources/relative_horizontal/scope_audit",
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

    metric_denominator = denominator_policy["metric_denominator"]
    current_denominator = metric_denominator["h001_geometry_checkable_gt_denominator"]
    relative_horizontal_rows = metric_denominator["excluded_family_counts"]["relative_horizontal"]
    expanded_denominator = current_denominator + relative_horizontal_rows
    all_rows = metric_denominator["fixed_gt_rows"]

    manifest = {
        "schema_version": "h001_relative_horizontal_scope_audit_v1",
        "status": "relative_horizontal_scope_audit_ready_no_metric_execution",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "current_families": list(CURRENT_FAMILIES),
            "candidate_family": TARGET_FAMILY,
            "promotion_rule": "Do not promote to main claim until current H001 evidence standard is matched.",
        },
        "denominator": {
            "all_held_out_gt_rows": all_rows,
            "current_h001_gt_denominator": current_denominator,
            "relative_horizontal_gt_rows": relative_horizontal_rows,
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
            "relative_horizontal_labels": predicate_mapping["predicate_family_map"][TARGET_FAMILY],
        },
        "coordinate_frame_hypotheses": [
            "scan_or_world_axis_aligned_xy",
            "camera_or_annotation_viewpoint_axis",
            "room_layout_axis_after_alignment",
            "object_pair_or_subject_centric_axis",
        ],
        "required_controls": [
            "wrong_frame_or_axis_flip_geometry",
            "wrong_pair_geometry",
            "shuffled_geometry_within_family",
            "geometry_only_ranking",
            "distance_only_if_meaningful",
        ],
        "blockers": [
            "coordinate_frame_semantics_unverified",
            "relative_horizontal_verifier_not_implemented",
            "train_dev_calibration_not_built",
            "gt_counterfactual_verifier_eval_not_run",
            "source_metrics_not_run",
            "bootstrap_ci_not_run",
            "failure_analysis_and_visual_audit_not_run",
        ],
        "next_gate": "G0_coordinate_frame_and_label_semantics_audit",
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
    write_report(out / "report.md", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
