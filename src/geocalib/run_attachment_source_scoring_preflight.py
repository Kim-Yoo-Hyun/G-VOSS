#!/usr/bin/env python3
"""Run bounded source evidence extraction and p_geom scoring for attachment.

This G5b preflight scores a bounded set of VL-SAT/Open3DSG source rows with the
G5a attachment-deferred calibration model. It does not compute source metrics,
controls, bootstrap CIs, or change the current AAAI main claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from fit_attachment_strict_calibration import dot, evidence_features, sigmoid, vectorize
from run_attachment_deferred_extractor_dry_run import (
    PREDICATE_LABELS,
    TARGET_FAMILY,
    ensure_dir,
    iter_jsonl,
    read_json,
    relpath,
    row_edge,
    row_family,
    row_label,
    utc_now,
    write_json,
    write_jsonl,
)
from run_attachment_gt_policy_smoke import build_point_surface_evidence
from validate_attachment_deferred_point_surface import (
    DEFAULT_CONTACT_THRESHOLD_M,
    DEFAULT_MAX_POINTS_PER_OBJECT,
)


SCHEMA_VERSION = "h001_attachment_deferred_source_scoring_preflight_v1"
SCORE_SCHEMA_VERSION = "h001_attachment_deferred_source_p_geom_score_preflight_v1"
STATUS = "attachment_deferred_source_scoring_preflight_ready_no_metrics"
DEFAULT_ATTACHMENT_ROOT = Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_CALIBRATION_DIR = DEFAULT_ATTACHMENT_ROOT / "calibration_fit"
DEFAULT_SCOPE_DIR = DEFAULT_ATTACHMENT_ROOT / "scope_audit"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "source_scoring_preflight"
DEFAULT_VLSAT_VERIFICATION = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl"
)
DEFAULT_OPEN3DSG_VERIFICATION = Path(
    "experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl"
)
FORBIDDEN_SCORE_FIELDS = {
    "recall_credit",
    "gt_match",
    "ranked_at_k",
    "metric_condition",
    "violation_at_k",
    "reranked_score",
    "verification_status",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--scope-audit-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--vlsat-verification", type=Path, default=DEFAULT_VLSAT_VERIFICATION)
    parser.add_argument("--open3dsg-verification", type=Path, default=DEFAULT_OPEN3DSG_VERIFICATION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-rows-per-source-label", type=int, default=20)
    parser.add_argument("--contact-threshold-m", type=float, default=DEFAULT_CONTACT_THRESHOLD_M)
    parser.add_argument("--max-points-per-object", type=int, default=DEFAULT_MAX_POINTS_PER_OBJECT)
    return parser.parse_args()


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def row_id_for_source(source_row: dict[str, Any]) -> str:
    return (
        f"{source_row['source_name']}::{source_row['scan_id']}::"
        f"{source_row['subgraph_id']}::{source_row['subject_id']}::"
        f"{source_row['object_id']}::{source_row['predicate_label']}"
    )


def normalize_source_row(row: dict[str, Any], source_name: str) -> dict[str, Any] | None:
    edge = row_edge(row)
    label = row_label(row)
    if label not in PREDICATE_LABELS:
        return None
    try:
        subject_id = int(edge.get("subject_id"))
        object_id = int(edge.get("object_id"))
    except (TypeError, ValueError):
        return None
    semantic = row.get("semantic") if isinstance(row.get("semantic"), dict) else {}
    ranks = semantic.get("ranks") if isinstance(semantic.get("ranks"), dict) else {}
    return {
        "source_name": source_name,
        "source_prediction_id": row.get("prediction_id"),
        "baseline_run_id": row.get("baseline_run_id"),
        "scan_id": str(row.get("scan_id")),
        "subgraph_id": str(row.get("subgraph_id")),
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_label": edge.get("subject_label"),
        "object_label": edge.get("object_label"),
        "predicate_family": TARGET_FAMILY,
        "predicate_label": str(label),
        "semantic_score": finite_float(semantic.get("predicate_score")),
        "ranking_score": finite_float(semantic.get("ranking_score")),
        "semantic_rank_in_subgraph": ranks.get("semantic_rank_in_subgraph"),
        "predicate_rank_for_pair": ranks.get("predicate_rank_for_pair"),
    }


def selected_source_rows_by_label(
    path: Path,
    source_name: str,
    max_rows_per_label: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates: dict[str, list[dict[str, Any]]] = {label: [] for label in PREDICATE_LABELS}
    skipped = Counter()
    rows_read = 0
    attachment_rows_seen = 0
    for row in iter_jsonl(path):
        rows_read += 1
        if row_family(row) != TARGET_FAMILY:
            continue
        attachment_rows_seen += 1
        label = row_label(row)
        if label not in PREDICATE_LABELS:
            skipped["unsupported_label"] += 1
            continue
        normalized = normalize_source_row(row, source_name)
        if normalized is None:
            skipped["invalid_source_row"] += 1
            continue
        candidates[label].append(normalized)

    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    unique_scan_counts: dict[str, int] = {}
    for label in PREDICATE_LABELS:
        selected: list[dict[str, Any]] = []
        selected_keys: set[tuple[str, str, int, int, str]] = set()
        seen_scans: set[str] = set()
        for candidate in candidates[label]:
            if len(selected) >= max_rows_per_label:
                break
            if candidate["scan_id"] in seen_scans:
                continue
            key = (
                candidate["scan_id"],
                candidate["subgraph_id"],
                candidate["subject_id"],
                candidate["object_id"],
                candidate["predicate_label"],
            )
            selected.append(candidate)
            selected_keys.add(key)
            seen_scans.add(candidate["scan_id"])
        if len(selected) < max_rows_per_label:
            for candidate in candidates[label]:
                if len(selected) >= max_rows_per_label:
                    break
                key = (
                    candidate["scan_id"],
                    candidate["subgraph_id"],
                    candidate["subject_id"],
                    candidate["object_id"],
                    candidate["predicate_label"],
                )
                if key in selected_keys:
                    continue
                selected.append(candidate)
                selected_keys.add(key)
        rows.extend(selected)
        counts[label] = len(selected)
        unique_scan_counts[label] = len({row["scan_id"] for row in selected})
    return rows, {
        "path": str(path),
        "source_name": source_name,
        "rows_read_total": rows_read,
        "attachment_rows_seen_total": attachment_rows_seen,
        "candidate_rows_by_label": {
            label: len(candidates[label]) for label in PREDICATE_LABELS
        },
        "selected_rows": len(rows),
        "selected_by_label": dict(sorted(counts.items())),
        "selected_unique_scans_by_label": dict(sorted(unique_scan_counts.items())),
        "selected_unique_scans_total": len({row["scan_id"] for row in rows}),
        "skipped": dict(sorted(skipped.items())),
    }


def score_evidence_row(
    evidence_row: dict[str, Any],
    *,
    model: dict[str, Any],
) -> tuple[float, dict[str, float | str], list[str]]:
    features = evidence_features(evidence_row)
    unknown_categories: list[str] = []
    for field in model["categorical_fields"]:
        value = str(features[field])
        if value not in model["categorical_values"].get(field, []):
            unknown_categories.append(f"{field}={value}")
    vector = vectorize({"_features": features}, model)
    probability = sigmoid(dot(model["weights"], vector))
    return probability, features, unknown_categories


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p10": None, "median": None, "p90": None, "max": None, "mean": None}
    ordered = sorted(values)

    def pick(frac: float) -> float:
        index = min(len(ordered) - 1, max(0, round(frac * (len(ordered) - 1))))
        return ordered[index]

    return {
        "min": ordered[0],
        "p10": pick(0.10),
        "median": pick(0.50),
        "p90": pick(0.90),
        "max": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def summarize_scores(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "rows": len(scored_rows),
        "p_geom_valid": quantiles([float(row["p_geom_valid"]) for row in scored_rows]),
        "by_source": {},
        "by_label": {},
    }
    for source in sorted({row["source_name"] for row in scored_rows}):
        scoped = [row for row in scored_rows if row["source_name"] == source]
        summary["by_source"][source] = {
            "rows": len(scoped),
            "p_geom_valid": quantiles([float(row["p_geom_valid"]) for row in scoped]),
            "by_label": dict(sorted(Counter(row["predicate_label"] for row in scoped).items())),
        }
    for label in sorted({row["predicate_label"] for row in scored_rows}):
        scoped = [row for row in scored_rows if row["predicate_label"] == label]
        summary["by_label"][label] = {
            "rows": len(scoped),
            "p_geom_valid": quantiles([float(row["p_geom_valid"]) for row in scoped]),
            "by_source": dict(sorted(Counter(row["source_name"] for row in scoped).items())),
        }
    return summary


def validate_scored_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(FORBIDDEN_SCORE_FIELDS):
        if field in row:
            errors.append(f"forbidden_score_field:{field}")
    if row.get("predicate_family") != TARGET_FAMILY:
        errors.append("predicate_family_not_attachment_deferred")
    if row.get("predicate_label") not in PREDICATE_LABELS:
        errors.append("predicate_label_not_in_attachment_labels")
    value = finite_float(row.get("p_geom_valid"))
    if value is None or value < 0.0 or value > 1.0:
        errors.append("invalid_p_geom_valid")
    return errors


def commands_md(max_rows_per_source_label: int) -> str:
    return f"""# Attachment Deferred G5b Source Scoring Preflight Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  attachment_deferred_source_scoring_preflight
```

Current default selection is bounded to `{max_rows_per_source_label}` rows per
source/predicate label. This is a preflight only. It does not compute R@K,
Violation@K, controls, bootstrap CI, or any source metric.

Validation:

```bash
python -m py_compile src/geocalib/run_attachment_source_scoring_preflight.py
python -m json.tool archive/experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/manifest.json >/dev/null
python -m json.tool archive/experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/summary.json >/dev/null
```
"""


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    score_summary = summary["score_summary"]["p_geom_valid"]
    lines = [
        "# Attachment Deferred Source Scoring Preflight",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a bounded source evidence extraction and p_geom scoring preflight.",
        "It does not compute source metrics, controls, bootstrap CI, or update the",
        "current AAAI main claim.",
        "",
        "## Counts",
        "",
        f"- selected source rows: `{summary['counts']['selected_source_rows']}`",
        f"- evidence rows: `{summary['counts']['evidence_rows']}`",
        f"- scored rows: `{summary['counts']['scored_rows']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Source Counts",
        "",
    ]
    for source, count in summary["counts"]["source_counts"].items():
        lines.append(f"- `{source}`: {count}")
    lines.extend(
        [
            "",
            "## Selection",
            "",
            f"- max rows per source/label: `{summary['selection']['max_rows_per_source_label']}`",
            f"- VL-SAT attachment rows seen: `{summary['selection']['vlsat']['attachment_rows_seen_total']}`",
            f"- VL-SAT selected unique scans: `{summary['selection']['vlsat']['selected_unique_scans_total']}`",
            f"- Open3DSG attachment rows seen: `{summary['selection']['open3dsg']['attachment_rows_seen_total']}`",
            f"- Open3DSG selected unique scans: `{summary['selection']['open3dsg']['selected_unique_scans_total']}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Score Distribution",
            "",
            f"- mean p_geom_valid: `{score_summary['mean']}`",
            f"- median p_geom_valid: `{score_summary['median']}`",
            f"- min/max p_geom_valid: `{score_summary['min']}` / `{score_summary['max']}`",
            "",
            "## Warnings",
            "",
        ]
    )
    if manifest["warnings"]:
        lines.extend(f"- `{warning}`" for warning in manifest["warnings"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "`G5c_attachment_full_source_scoring_or_metric_protocol_freeze`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = args.dataset_root if args.dataset_root.is_absolute() else repo_root / args.dataset_root
    calibration_dir = args.calibration_dir if args.calibration_dir.is_absolute() else repo_root / args.calibration_dir
    scope_dir = args.scope_audit_dir if args.scope_audit_dir.is_absolute() else repo_root / args.scope_audit_dir
    vlsat_path = args.vlsat_verification if args.vlsat_verification.is_absolute() else repo_root / args.vlsat_verification
    open3dsg_path = args.open3dsg_verification if args.open3dsg_verification.is_absolute() else repo_root / args.open3dsg_verification
    out = args.out if args.out.is_absolute() else repo_root / args.out

    calibration_manifest_path = calibration_dir / "manifest.json"
    model_path = calibration_dir / "model.json"
    scope_manifest_path = scope_dir / "manifest.json"
    for path in [calibration_manifest_path, model_path, scope_manifest_path, vlsat_path, open3dsg_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing source scoring preflight input: {path}")

    calibration_manifest = read_json(calibration_manifest_path)
    model = read_json(model_path)
    scope_manifest = read_json(scope_manifest_path)
    if calibration_manifest.get("status") != "attachment_deferred_calibration_fit_ready_no_source_metrics":
        raise ValueError(f"unexpected_calibration_status:{calibration_manifest.get('status')}")
    if model.get("status") != "attachment_deferred_calibration_fit_ready_no_source_metrics":
        raise ValueError(f"unexpected_model_status:{model.get('status')}")

    vlsat_rows, vlsat_selection = selected_source_rows_by_label(
        vlsat_path,
        "vlsat_closed_set",
        args.max_rows_per_source_label,
    )
    open3dsg_rows, open3dsg_selection = selected_source_rows_by_label(
        open3dsg_path,
        "open3dsg_ov",
        args.max_rows_per_source_label,
    )
    source_rows = vlsat_rows + open3dsg_rows
    expected_selected = len(PREDICATE_LABELS) * args.max_rows_per_source_label * 2
    warnings: list[str] = []
    blockers: list[str] = [
        "source_metrics_not_run",
        "controls_not_run",
        "bootstrap_ci_not_run",
        "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
    ]
    if len(source_rows) != expected_selected:
        warnings.append(f"bounded_preflight_selected_rows_{len(source_rows)}_expected_{expected_selected}")

    evidence_rows, diagnostics, evidence_meta = build_point_surface_evidence(
        source_rows=source_rows,
        dataset_root=dataset_root,
        contact_threshold_m=args.contact_threshold_m,
        max_points_per_object=args.max_points_per_object,
    )
    metadata_by_row_id = {row_id_for_source(row): row for row in source_rows}
    scored_rows: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    unknown_categories: Counter[str] = Counter()
    for evidence in evidence_rows:
        source_meta = metadata_by_row_id.get(evidence["row_id"], {})
        probability, features, unknowns = score_evidence_row(evidence, model=model)
        for unknown in unknowns:
            unknown_categories[unknown] += 1
        row = {
            "schema_version": SCORE_SCHEMA_VERSION,
            "record_type": "attachment_deferred_source_p_geom_score_preflight",
            "score_scope": "bounded_source_preflight",
            "calibration_model_id": model["model_id"],
            "source_name": evidence["source_name"],
            "source_prediction_id": source_meta.get("source_prediction_id"),
            "baseline_run_id": source_meta.get("baseline_run_id"),
            "scan_id": evidence["scan_id"],
            "subgraph_id": evidence["subgraph_id"],
            "subject_id": evidence["subject_id"],
            "object_id": evidence["object_id"],
            "subject_label": evidence.get("subject_label"),
            "object_label": evidence.get("object_label"),
            "predicate_family": evidence["predicate_family"],
            "predicate_label": evidence["predicate_label"],
            "subtype_hint": evidence.get("subtype_hint"),
            "semantic": {
                "predicate_score": source_meta.get("semantic_score"),
                "ranking_score": source_meta.get("ranking_score"),
                "semantic_rank_in_subgraph": source_meta.get("semantic_rank_in_subgraph"),
                "predicate_rank_for_pair": source_meta.get("predicate_rank_for_pair"),
            },
            "evidence": {
                "row_id": evidence["row_id"],
                "extractor_status": evidence.get("extractor_status"),
                "geometry_available": evidence.get("geometry_available"),
                "missing_fields": evidence.get("missing_fields", []),
                "quality_flags": evidence.get("quality_flags", []),
                "unknown_model_categories": unknowns,
            },
            "p_geom_valid": probability,
            "p_geom_invalid": 1.0 - probability,
            "feature_snapshot": {
                key: features[key]
                for key in (
                    "min_point_distance_m",
                    "contact_patch_score",
                    "surface_distance_m",
                    "projected_xy_overlap",
                    "surface_type",
                    "surface_normal_class",
                    "class_pair_prior",
                )
            },
        }
        errors = validate_scored_row(row)
        if errors:
            validation_errors.append({"row_id": evidence["row_id"], "errors": errors})
        scored_rows.append(row)

    source_counts = Counter(row["source_name"] for row in scored_rows)
    label_counts = Counter(row["predicate_label"] for row in scored_rows)
    extractor_status_counts = Counter(row.get("extractor_status") for row in evidence_rows)
    geometry_ready_rows = sum(
        1
        for row in evidence_rows
        if row.get("geometry_available", {}).get("points")
        and row.get("geometry_available", {}).get("surface_candidates")
        and row.get("geometry_available", {}).get("normals")
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS if not validation_errors else "attachment_deferred_source_scoring_preflight_failed_validation",
        "created_at": utc_now(),
        "counts": {
            "selected_source_rows": len(source_rows),
            "evidence_rows": len(evidence_rows),
            "diagnostic_rows": len(diagnostics),
            "scored_rows": len(scored_rows),
            "validation_errors": len(validation_errors),
            "geometry_ready_rows": geometry_ready_rows,
            "source_counts": dict(sorted(source_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
            "extractor_status_counts": dict(sorted((str(k), v) for k, v in extractor_status_counts.items())),
            "unknown_model_category_counts": dict(sorted(unknown_categories.items())),
        },
        "score_summary": summarize_scores(scored_rows),
        "selection": {
            "max_rows_per_source_label": args.max_rows_per_source_label,
            "expected_selected_rows": expected_selected,
            "vlsat": vlsat_selection,
            "open3dsg": open3dsg_selection,
        },
        "full_source_scope_reference": {
            "vlsat_attachment_rows": scope_manifest.get("source_prediction_rows", {})
            .get("vlsat", {})
            .get("attachment_deferred_rows"),
            "open3dsg_attachment_rows": scope_manifest.get("source_prediction_rows", {})
            .get("open3dsg", {})
            .get("attachment_deferred_rows"),
            "expanded_candidate_denominator": scope_manifest.get("denominator", {})
            .get("expanded_candidate_denominator"),
        },
        "evidence_meta": evidence_meta,
        "validation_errors": validation_errors,
    }
    status = summary["status"]
    if validation_errors:
        blockers.append("score_validation_errors")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": summary["created_at"],
        "claim_boundary": {
            "artifact_type": "bounded_attachment_source_scoring_preflight",
            "bounded_preflight_rows_scored": True,
            "full_source_predictions_scored": False,
            "source_metrics_computed": False,
            "controls_run": False,
            "bootstrap_ci_run": False,
            "current_main_claim_unchanged": True,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
        "inputs": {
            "calibration_manifest": relpath(repo_root, calibration_manifest_path),
            "model": relpath(repo_root, model_path),
            "scope_manifest": relpath(repo_root, scope_manifest_path),
            "vlsat_verification_jsonl": relpath(repo_root, vlsat_path),
            "open3dsg_verification_jsonl": relpath(repo_root, open3dsg_path),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "outputs": {
            "manifest": "manifest.json",
            "summary": "summary.json",
            "source_rows": "source_rows.jsonl",
            "evidence_rows": "evidence_rows.jsonl",
            "diagnostics": "diagnostics.jsonl",
            "scored_rows": "scored_rows.jsonl",
            "commands": "commands.md",
            "report": "report.md",
        },
        "counts": summary["counts"],
        "warnings": warnings,
        "blockers": blockers,
        "next_gate": "G5c_attachment_full_source_scoring_or_metric_protocol_freeze",
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "source_rows.jsonl", source_rows)
    write_jsonl(out / "evidence_rows.jsonl", evidence_rows)
    write_jsonl(out / "diagnostics.jsonl", diagnostics)
    write_jsonl(out / "scored_rows.jsonl", scored_rows)
    write_text(out / "commands.md", commands_md(args.max_rows_per_source_label))
    write_text(out / "report.md", report_md(manifest, summary))
    print(
        json.dumps(
            {
                "status": status,
                "out": relpath(repo_root, out),
                "selected_source_rows": len(source_rows),
                "scored_rows": len(scored_rows),
                "validation_errors": len(validation_errors),
                "source_counts": dict(sorted(source_counts.items())),
                "label_counts": dict(sorted(label_counts.items())),
                "warnings": warnings,
            },
            sort_keys=True,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
