#!/usr/bin/env python3
"""Freeze the attachment-deferred full-source scoring and metric protocol.

This G5c artifact is a protocol freeze only. It audits source coverage and
creates deterministic shard/metric contracts before any full-source attachment
scoring, R@K, Violation@K, controls, bootstrap CI, or claim update.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_deferred_full_source_protocol_v1"
STATUS = "attachment_deferred_full_source_protocol_frozen_no_metrics"
TARGET_FAMILY = "attachment_deferred"
ATTACHMENT_LABELS = ("attached to", "hanging on", "connected to")
DEFAULT_ROOT = Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_SCOPE_DIR = DEFAULT_ROOT / "scope_audit"
DEFAULT_CALIBRATION_DIR = DEFAULT_ROOT / "calibration_fit"
DEFAULT_PREFLIGHT_DIR = DEFAULT_ROOT / "source_scoring_preflight"
DEFAULT_OUT = DEFAULT_ROOT / "full_source_protocol"
DEFAULT_GT = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
)
DEFAULT_VLSAT_VERIFICATION = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl"
)
DEFAULT_OPEN3DSG_VERIFICATION = Path(
    "experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--scope-audit-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--source-preflight-dir", type=Path, default=DEFAULT_PREFLIGHT_DIR)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GT)
    parser.add_argument("--vlsat-verification", type=Path, default=DEFAULT_VLSAT_VERIFICATION)
    parser.add_argument("--open3dsg-verification", type=Path, default=DEFAULT_OPEN3DSG_VERIFICATION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--rows-per-shard", type=int, default=2000)
    parser.add_argument("--ks", type=int, nargs="+", default=[50, 100])
    parser.add_argument(
        "--derive-shards-from-source",
        action="store_true",
        help=(
            "Build shard counts from the provided source verification files instead of "
            "the historical scope audit manifest. Use this for full-validation extension runs."
        ),
    )
    parser.add_argument(
        "--allow-scope-denominator-mismatch",
        action="store_true",
        help=(
            "Allow the active ground-truth denominator to differ from the historical "
            "scope audit denominator. The mismatch is still recorded in validation."
        ),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def abs_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def row_family(row: dict[str, Any]) -> str | None:
    if row.get("predicate_family") is not None:
        return str(row.get("predicate_family"))
    predicate = row.get("predicate") if isinstance(row.get("predicate"), dict) else {}
    value = predicate.get("predicate_family")
    return str(value) if value is not None else None


def row_label(row: dict[str, Any]) -> str | None:
    if row.get("predicate_label") is not None:
        return str(row.get("predicate_label"))
    predicate = row.get("predicate") if isinstance(row.get("predicate"), dict) else {}
    value = predicate.get("predicate_label")
    return str(value) if value is not None else None


def row_edge(row: dict[str, Any]) -> dict[str, Any]:
    edge = row.get("edge") if isinstance(row.get("edge"), dict) else {}
    return {
        "subject_id": row.get("subject_id", edge.get("subject_id")),
        "object_id": row.get("object_id", edge.get("object_id")),
    }


def int_or_none(value: Any) -> int | None:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def relation_key(row: dict[str, Any]) -> tuple[str, str, int, int, str] | None:
    edge = row_edge(row)
    subject_id = int_or_none(edge.get("subject_id"))
    object_id = int_or_none(edge.get("object_id"))
    label = row_label(row)
    scan_id = row.get("scan_id")
    subgraph_id = row.get("subgraph_id")
    if None in (subject_id, object_id) or not scan_id or not subgraph_id or label not in ATTACHMENT_LABELS:
        return None
    return str(scan_id), str(subgraph_id), int(subject_id), int(object_id), str(label)


def load_gt_attachment(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(path):
        if row_family(row) == TARGET_FAMILY and row_label(row) in ATTACHMENT_LABELS:
            key = relation_key(row)
            if key is None:
                continue
            rows.append(
                {
                    "scan_id": key[0],
                    "subgraph_id": key[1],
                    "subject_id": key[2],
                    "object_id": key[3],
                    "predicate_label": key[4],
                }
            )
    return rows


def source_key_set(path: Path) -> tuple[set[tuple[str, str, int, int, str]], dict[str, Any]]:
    keys: set[tuple[str, str, int, int, str]] = set()
    label_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    rows_read = 0
    rows_used = 0
    scans: set[str] = set()
    subgraphs: set[str] = set()
    directed_pairs: set[tuple[str, str, int, int]] = set()
    for row in iter_jsonl(path):
        rows_read += 1
        family = row_family(row)
        if family != TARGET_FAMILY:
            continue
        family_counts[family] += 1
        key = relation_key(row)
        if key is None:
            continue
        rows_used += 1
        keys.add(key)
        label_counts[key[4]] += 1
        scans.add(key[0])
        subgraphs.add(key[1])
        directed_pairs.add(key[:4])
    return keys, {
        "path": str(path),
        "rows_read": rows_read,
        "attachment_rows_used": rows_used,
        "unique_exact_keys": len(keys),
        "label_counts": dict(sorted(label_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "scans": len(scans),
        "subgraphs": len(subgraphs),
        "directed_pairs": len(directed_pairs),
    }


def denominator_audit(
    gt_rows: list[dict[str, Any]],
    source_keys: dict[str, set[tuple[str, str, int, int, str]]],
    source_stats: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    gt_keys = {
        (
            row["scan_id"],
            row["subgraph_id"],
            row["subject_id"],
            row["object_id"],
            row["predicate_label"],
        )
        for row in gt_rows
    }
    gt_label_counts = Counter(row["predicate_label"] for row in gt_rows)
    result: dict[str, Any] = {
        "family": TARGET_FAMILY,
        "global_exact_label_gt_denominator": len(gt_keys),
        "global_gt_label_counts": dict(sorted(gt_label_counts.items())),
        "sources": {},
        "policy": {
            "primary_recall_denominator": "source_specific_covered_exact_label_gt_denominator",
            "also_report_global_candidate_denominator": True,
            "global_candidate_denominator": len(gt_keys),
            "coverage_must_be_frozen_before_metric_execution": True,
            "exact_predicate_label_matching_required": True,
            "do_not_compare_sources_without_coverage_caveat": True,
        },
    }
    for source_name, keys in sorted(source_keys.items()):
        covered = gt_keys & keys
        missing = gt_keys - keys
        result["sources"][source_name] = {
            "covered_exact_label_gt_denominator": len(covered),
            "missing_exact_label_gt_rows": len(missing),
            "coverage_ratio_vs_global": len(covered) / len(gt_keys) if gt_keys else None,
            "covered_label_counts": dict(sorted(Counter(key[4] for key in covered).items())),
            "missing_label_counts": dict(sorted(Counter(key[4] for key in missing).items())),
            "source_attachment_stats": source_stats[source_name],
        }
    return result


def build_shards(scope_manifest: dict[str, Any], rows_per_shard: int) -> list[dict[str, Any]]:
    if rows_per_shard <= 0:
        raise ValueError("rows_per_shard must be positive")
    source_specs = [
        ("vlsat", "vlsat_closed_set"),
        ("open3dsg", "open3dsg_ov"),
    ]
    shards: list[dict[str, Any]] = []
    for source_key, source_name in source_specs:
        label_counts = (
            scope_manifest.get("source_prediction_rows", {})
            .get(source_key, {})
            .get("attachment_label_counts", {})
        )
        for label in ATTACHMENT_LABELS:
            total = int(label_counts.get(label, 0))
            label_slug = label.replace(" ", "_")
            shard_index = 0
            for start in range(0, total, rows_per_shard):
                end = min(start + rows_per_shard, total)
                shards.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "shard_id": f"{source_name}_{label_slug}_{shard_index:04d}",
                        "source_key": source_key,
                        "source_name": source_name,
                        "predicate_family": TARGET_FAMILY,
                        "predicate_label": label,
                        "start_ordinal_in_source_label": start,
                        "end_ordinal_exclusive": end,
                        "expected_rows": end - start,
                        "rows_per_shard": rows_per_shard,
                        "selection_rule": (
                            "iterate the frozen source verification JSONL in file order, "
                            "keep attachment_deferred rows for this label, and select "
                            "[start_ordinal_in_source_label, end_ordinal_exclusive)"
                        ),
                    }
                )
                shard_index += 1
    return shards


def build_shards_from_source_stats(
    source_stats: dict[str, dict[str, Any]],
    rows_per_shard: int,
) -> list[dict[str, Any]]:
    if rows_per_shard <= 0:
        raise ValueError("rows_per_shard must be positive")
    source_specs = [
        ("vlsat", "vlsat_closed_set"),
        ("open3dsg", "open3dsg_ov"),
    ]
    shards: list[dict[str, Any]] = []
    for source_key, source_name in source_specs:
        label_counts = source_stats.get(source_name, {}).get("label_counts", {})
        for label in ATTACHMENT_LABELS:
            total = int(label_counts.get(label, 0))
            label_slug = label.replace(" ", "_")
            shard_index = 0
            for start in range(0, total, rows_per_shard):
                end = min(start + rows_per_shard, total)
                shards.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "shard_id": f"{source_name}_{label_slug}_{shard_index:04d}",
                        "source_key": source_key,
                        "source_name": source_name,
                        "predicate_family": TARGET_FAMILY,
                        "predicate_label": label,
                        "start_ordinal_in_source_label": start,
                        "end_ordinal_exclusive": end,
                        "expected_rows": end - start,
                        "rows_per_shard": rows_per_shard,
                        "selection_rule": (
                            "iterate the provided source verification JSONL in file order, "
                            "keep attachment_deferred rows for this label, and select "
                            "[start_ordinal_in_source_label, end_ordinal_exclusive)"
                        ),
                    }
                )
                shard_index += 1
    return shards


def protocol_payload(
    *,
    model: dict[str, Any],
    denominator: dict[str, Any],
    rows_per_shard: int,
    shard_count: int,
    expected_rows: int,
    ks: list[int],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "artifact_type": "metric_freeze_protocol_no_metric_execution",
        "family": TARGET_FAMILY,
        "labels": list(ATTACHMENT_LABELS),
        "calibration_model": {
            "model_id": model.get("model_id"),
            "training_scope": "G4c strict-only train/dev rows",
            "semantic_source_features_used": False,
            "connected_to_label_specific_dev_calibration": False,
            "connected_to_policy": (
                "Use pooled calibration for scoring, report connected-to dev absence, "
                "and do not claim label-specific connected-to calibration."
            ),
        },
        "full_source_scoring": {
            "expected_total_source_rows": expected_rows,
            "rows_per_shard": rows_per_shard,
            "shard_count": shard_count,
            "resume_key": "shard_id",
            "selection_rule": "source + predicate-label file-order ordinal intervals from shards.jsonl",
            "required_outputs_per_shard": [
                "source_rows.jsonl",
                "evidence_rows.jsonl",
                "diagnostics.jsonl",
                "scored_rows.jsonl",
                "status.json",
            ],
            "required_aggregate_outputs": [
                "manifest.json",
                "summary.json",
                "scored_rows.jsonl",
                "validation.json",
                "report.md",
            ],
            "scored_row_required_fields": [
                "schema_version",
                "source_name",
                "baseline_run_id",
                "scan_id",
                "subgraph_id",
                "subject_id",
                "object_id",
                "predicate_family",
                "predicate_label",
                "semantic.predicate_score",
                "semantic.ranking_score",
                "attachment_policy_decision",
                "attachment_policy_reason_codes",
                "p_geom_valid",
                "p_geom_invalid",
                "calibration_model_id",
                "evidence.row_id",
                "evidence.geometry_available",
                "evidence.unknown_model_categories",
            ],
            "forbidden_scoring_stage_fields": [
                "recall_credit",
                "gt_match",
                "ranked_at_k",
                "metric_condition",
                "violation_at_k",
                "main_claim_update",
            ],
            "unknown_category_policy": (
                "Keep scoring deterministic, record unknown_model_categories per row, "
                "summarize counts by source/label, and do not tune model categories on "
                "held-out source metrics."
            ),
        },
        "metric_protocol": {
            "ks": ks,
            "recall": {
                "match_rule": "exact scan/subgraph/subject/object/predicate-label match",
                "denominator": denominator["policy"]["primary_recall_denominator"],
                "report_global_candidate_denominator": denominator["policy"][
                    "also_report_global_candidate_denominator"
                ],
                "source_denominators": denominator["sources"],
            },
            "violation": {
                "definition": (
                    "top-k prediction is a violation when the frozen attachment policy "
                    "decision is `violated`; `uncertain` is reported separately."
                ),
                "required_rates": [
                    "violation_rate_at_k",
                    "uncertain_rate_at_k",
                    "evidence_missing_rate_at_k",
                ],
            },
            "ranking_conditions": [
                {
                    "name": "semantic_only",
                    "ranking_score": "semantic.ranking_score or semantic.predicate_score",
                    "purpose": "source baseline",
                },
                {
                    "name": "probabilistic_recalibrated",
                    "ranking_score": "semantic_score * p_geom_valid",
                    "purpose": "main attachment reliability reranking condition if promoted",
                },
                {
                    "name": "rule_verified_attachment_policy",
                    "ranking_score": "filter-safe demotion of attachment_policy_decision == violated",
                    "purpose": "hard-rule operating point separate from probabilistic calibration",
                },
                {
                    "name": "control_p_geom_valid_only",
                    "ranking_score": "p_geom_valid only",
                    "purpose": "geometry-only control",
                },
                {
                    "name": "control_distance_only",
                    "ranking_score": "negative point/surface distance only",
                    "purpose": "simple heuristic control",
                },
                {
                    "name": "control_shuffled_geometry",
                    "ranking_score": "semantic_score * shuffled p_geom_valid within source/label",
                    "purpose": "tests whether geometry is identity-coupled",
                },
                {
                    "name": "control_wrong_pair_geometry",
                    "ranking_score": "semantic_score * p_geom_valid from a wrong directed pair",
                    "purpose": "wrong-pair geometry control",
                },
            ],
            "control_order": [
                "schema_and_denominator_validation",
                "semantic_only",
                "probabilistic_recalibrated",
                "rule_verified_attachment_policy",
                "control_p_geom_valid_only",
                "control_distance_only",
                "control_shuffled_geometry",
                "control_wrong_pair_geometry",
                "subgraph_bootstrap_ci_if_any_attachment_result_is_reported",
                "failure_rows_and_visual_audit_before_main_claim_promotion",
            ],
        },
        "claim_boundary": {
            "current_main_AAAI_claim_unchanged": True,
            "attachment_promotion_requires_user_confirmation": True,
            "protocol_is_not_metric_evidence": True,
            "minimum_promotion_evidence": [
                "full-source scoring validation",
                "VL-SAT and Open3DSG source metrics",
                "controls",
                "bootstrap CI if reported in paper",
                "failure rows",
                "qualitative or visual audit",
                "explicit connected-to caveat or augmented calibration evidence",
            ],
        },
    }


def commands_md() -> str:
    return """# Attachment Deferred G5c Full-Source Protocol Commands

Run from repository root.

Current full-validation extension:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  attachment_deferred_full_validation_protocol
```

Historical 127-scan provenance branch:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  attachment_deferred_full_source_protocol
```

This freezes the source coverage, sharding, scoring schema, metric conditions,
control order, and claim boundary before any full-source attachment metrics.
It does not compute R@K, Violation@K, controls, bootstrap CI, or any source
metric.

Validation:

```bash
python -m py_compile src/geocalib/freeze_attachment_full_source_protocol.py
python -m json.tool <active-output-root>/manifest.json >/dev/null
python -m json.tool <active-output-root>/protocol.json >/dev/null
python -m json.tool <active-output-root>/denominator_audit.json >/dev/null
```
"""


def report_md(manifest: dict[str, Any], denominator: dict[str, Any], shards: list[dict[str, Any]]) -> str:
    lines = [
        "# Attachment Deferred Full-Source Protocol",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a G5c protocol freeze only. It does not run full-source scoring,",
        "R@K, Violation@K, controls, bootstrap CI, source metrics, or main-claim",
        "promotion. The current AAAI claim remains unchanged.",
        "",
        "## Denominator Policy",
        "",
        f"- global attachment exact-label GT denominator: `{denominator['global_exact_label_gt_denominator']}`",
        "- primary recall denominator: source-specific covered exact-label GT rows",
        "- exact predicate-label matching: required",
        "- source comparison: requires coverage caveat",
        "",
        "## Source Coverage",
        "",
    ]
    for source_name, payload in denominator["sources"].items():
        lines.append(
            f"- `{source_name}`: covered `{payload['covered_exact_label_gt_denominator']}`, "
            f"missing `{payload['missing_exact_label_gt_rows']}`, "
            f"coverage `{payload['coverage_ratio_vs_global']:.4f}`"
        )
    lines.extend(
        [
            "",
            "## Sharding",
            "",
            f"- shard count: `{len(shards)}`",
            f"- expected full-source rows: `{manifest['counts']['expected_full_source_rows']}`",
            f"- rows per shard: `{manifest['counts']['rows_per_shard']}`",
            "",
            "## Required Metric Conditions",
            "",
            "- `semantic_only`",
            "- `probabilistic_recalibrated`",
            "- `rule_verified_attachment_policy`",
            "- `control_p_geom_valid_only`",
            "- `control_distance_only`",
            "- `control_shuffled_geometry`",
            "- `control_wrong_pair_geometry`",
            "",
            "## Known Caveat",
            "",
            "`connected to` has no dev strict rows in G4c. The frozen protocol allows",
            "pooled scoring but forbids a label-specific connected-to calibration claim",
            "unless future train/dev evidence is added before source metrics.",
            "",
            "## Next Gate",
            "",
            "`G5d_attachment_full_source_scoring_metrics_controls`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    ks = sorted(set(int(k) for k in args.ks))
    if not ks or any(k <= 0 for k in ks):
        raise ValueError("--ks must contain one or more positive integers")
    scope_dir = abs_path(repo_root, args.scope_audit_dir)
    calibration_dir = abs_path(repo_root, args.calibration_dir)
    preflight_dir = abs_path(repo_root, args.source_preflight_dir)
    gt_path = abs_path(repo_root, args.ground_truth)
    vlsat_path = abs_path(repo_root, args.vlsat_verification)
    open3dsg_path = abs_path(repo_root, args.open3dsg_verification)
    out = abs_path(repo_root, args.out)

    required = [
        scope_dir / "manifest.json",
        calibration_dir / "manifest.json",
        calibration_dir / "model.json",
        preflight_dir / "manifest.json",
        preflight_dir / "summary.json",
        gt_path,
        vlsat_path,
        open3dsg_path,
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"missing G5c input: {path}")

    scope_manifest = read_json(scope_dir / "manifest.json")
    calibration_manifest = read_json(calibration_dir / "manifest.json")
    model = read_json(calibration_dir / "model.json")
    preflight_manifest = read_json(preflight_dir / "manifest.json")

    validation_errors: list[str] = []
    expected_statuses = {
        "scope": "attachment_deferred_scope_schema_ready_no_metric_execution",
        "calibration": "attachment_deferred_calibration_fit_ready_no_source_metrics",
        "preflight": "attachment_deferred_source_scoring_preflight_ready_no_metrics",
    }
    if scope_manifest.get("status") != expected_statuses["scope"]:
        validation_errors.append(f"unexpected_scope_status:{scope_manifest.get('status')}")
    if calibration_manifest.get("status") != expected_statuses["calibration"]:
        validation_errors.append(f"unexpected_calibration_status:{calibration_manifest.get('status')}")
    if model.get("status") != expected_statuses["calibration"]:
        validation_errors.append(f"unexpected_model_status:{model.get('status')}")
    if preflight_manifest.get("status") != expected_statuses["preflight"]:
        validation_errors.append(f"unexpected_preflight_status:{preflight_manifest.get('status')}")

    gt_rows = load_gt_attachment(gt_path)
    source_keys: dict[str, set[tuple[str, str, int, int, str]]] = {}
    source_stats: dict[str, dict[str, Any]] = {}
    for source_name, path in {
        "vlsat_closed_set": vlsat_path,
        "open3dsg_ov": open3dsg_path,
    }.items():
        keys, stats = source_key_set(path)
        source_keys[source_name] = keys
        source_stats[source_name] = stats

    denominator = denominator_audit(gt_rows, source_keys, source_stats)
    expected_gt = int(scope_manifest.get("denominator", {}).get("attachment_deferred_gt_rows", 0))
    allowed_mismatches: list[str] = []
    if denominator["global_exact_label_gt_denominator"] != expected_gt:
        mismatch = (
            "denominator_mismatch:"
            f"{denominator['global_exact_label_gt_denominator']}!={expected_gt}"
        )
        if not args.allow_scope_denominator_mismatch:
            validation_errors.append(mismatch)
        else:
            allowed_mismatches.append(mismatch)

    if args.derive_shards_from_source:
        shards = build_shards_from_source_stats(source_stats, args.rows_per_shard)
        scoped_expected = sum(
            int(source_stats[source_name]["attachment_rows_used"])
            for source_name in ("vlsat_closed_set", "open3dsg_ov")
        )
        shard_validation_target = "source_stats"
    else:
        shards = build_shards(scope_manifest, args.rows_per_shard)
        scoped_expected = sum(
            int(
                scope_manifest.get("source_prediction_rows", {})
                .get(source_key, {})
                .get("attachment_deferred_rows", 0)
            )
            for source_key in ("vlsat", "open3dsg")
        )
        shard_validation_target = "scope_manifest"
    expected_rows = sum(int(row["expected_rows"]) for row in shards)
    if expected_rows != scoped_expected:
        validation_errors.append(f"shard_expected_rows_mismatch:{expected_rows}!={scoped_expected}")

    warnings = [
        "connected_to_dev_absent_use_pooled_or_train_only_caveat",
        "protocol_only_no_source_metrics",
        "main_AAAI_claim_unchanged_until_user_confirmation",
    ]
    warnings.extend(f"allowed_{item}" for item in allowed_mismatches)
    blockers = [
        "full_source_scoring_not_run",
        "source_metrics_not_run",
        "controls_not_run",
        "bootstrap_ci_not_run",
        "failure_analysis_and_visual_audit_not_run",
        "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
    ]
    if validation_errors:
        blockers.append("protocol_validation_errors")

    protocol = protocol_payload(
        model=model,
        denominator=denominator,
        rows_per_shard=args.rows_per_shard,
        shard_count=len(shards),
        expected_rows=expected_rows,
        ks=ks,
    )
    status = STATUS if not validation_errors else "attachment_deferred_full_source_protocol_failed_validation"
    created_at = utc_now()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": created_at,
        "claim_boundary": protocol["claim_boundary"],
        "inputs": {
            "scope_manifest": relpath(repo_root, scope_dir / "manifest.json"),
            "calibration_manifest": relpath(repo_root, calibration_dir / "manifest.json"),
            "calibration_model": relpath(repo_root, calibration_dir / "model.json"),
            "source_preflight_manifest": relpath(repo_root, preflight_dir / "manifest.json"),
            "ground_truth_jsonl": relpath(repo_root, gt_path),
            "vlsat_verification_jsonl": relpath(repo_root, vlsat_path),
            "open3dsg_verification_jsonl": relpath(repo_root, open3dsg_path),
        },
        "outputs": {
            "manifest": "manifest.json",
            "protocol": "protocol.json",
            "denominator_audit": "denominator_audit.json",
            "shards": "shards.jsonl",
            "validation": "validation.json",
            "commands": "commands.md",
            "report": "report.md",
        },
        "counts": {
            "global_attachment_gt_denominator": denominator["global_exact_label_gt_denominator"],
            "expected_full_source_rows": expected_rows,
            "rows_per_shard": args.rows_per_shard,
            "shards": len(shards),
            "derive_shards_from_source": args.derive_shards_from_source,
            "shard_validation_target": shard_validation_target,
            "ks": ks,
            "vlsat_attachment_rows": source_stats["vlsat_closed_set"]["attachment_rows_used"],
            "open3dsg_attachment_rows": source_stats["open3dsg_ov"]["attachment_rows_used"],
        },
        "warnings": warnings,
        "blockers": blockers,
        "next_gate": "G5d_attachment_full_source_scoring_metrics_controls",
    }
    validation = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if not validation_errors else "failed",
        "errors": validation_errors,
        "checks": {
            "expected_input_statuses": expected_statuses,
            "attachment_denominator_matches_scope": not any(
                error.startswith("denominator_mismatch") for error in validation_errors
            ),
            "scope_denominator_mismatch_allowed": args.allow_scope_denominator_mismatch,
            "shard_expected_rows_matches_target": not any(
                error.startswith("shard_expected_rows_mismatch") for error in validation_errors
            ),
            "shard_validation_target": shard_validation_target,
        },
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "protocol.json", protocol)
    write_json(out / "denominator_audit.json", denominator)
    write_jsonl(out / "shards.jsonl", shards)
    write_json(out / "validation.json", validation)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, denominator, shards))
    print(
        json.dumps(
            {
                "status": status,
                "out": relpath(repo_root, out),
                "expected_full_source_rows": expected_rows,
                "shards": len(shards),
                "validation_errors": len(validation_errors),
                "denominator": denominator["sources"],
            },
            sort_keys=True,
        )
    )
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
