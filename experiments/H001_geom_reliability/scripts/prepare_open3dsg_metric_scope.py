#!/usr/bin/env python3
"""Freeze Open3DSG predicate-family mapping and denominator caveats before metric execution."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_metric_scope_v1"
STATUS_READY = "metric_scope_policy_ready_no_metric_execution"
TARGET_FAMILIES = ["support_contact", "proximity", "relative_vertical"]

PREDICATE_FAMILY_MAP = {
    "support_contact": ["standing on", "lying on", "supported by"],
    "proximity": ["close by"],
    "relative_vertical": ["higher than", "lower than"],
    "relative_horizontal": ["left", "right", "front", "behind", "in front of"],
    "attachment_deferred": ["attached to", "hanging on", "mounted on", "connected to"],
    "background_none": ["none"],
    "unsupported_first_pass": [
        "inside",
        "bigger than",
        "smaller than",
        "same symmetry as",
        "same as",
        "leaning against",
        "part of",
        "belonging to",
        "build in",
        "standing in",
        "cover",
        "lying in",
        "hanging in",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--relationships-file",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships.txt"),
    )
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/"
            "vlsat_closed_set/hardened/ground_truth.jsonl"
        ),
    )
    parser.add_argument(
        "--train-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--validation-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--checkpoint-plan",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_plan.json"),
    )
    parser.add_argument(
        "--raw-identity-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/metric_scope"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError:
        return {"status": "unreadable_json"}


def read_relationship_labels(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def inverse_mapping() -> dict[str, str]:
    inverse: dict[str, str] = {}
    for family, labels in PREDICATE_FAMILY_MAP.items():
        for label in labels:
            inverse[label] = family
    return inverse


def mapping_policy(repo_root: Path, relationships_file: Path) -> dict[str, Any]:
    labels = read_relationship_labels(relationships_file)
    inverse = inverse_mapping()
    labels_missing_mapping = [label for label in labels if label not in inverse]
    mapped_labels_not_in_file = [
        label
        for label in sorted(inverse)
        if label not in labels and label not in {"in front of", "mounted on"}
    ]
    family_rows = []
    for family, labels_for_family in PREDICATE_FAMILY_MAP.items():
        family_rows.append(
            {
                "family": family,
                "predicate_labels": labels_for_family,
                "in_h001_metric_denominator": family in TARGET_FAMILIES,
                "claim_use": (
                    "geometry-checkable H001 metric family"
                    if family in TARGET_FAMILIES
                    else "reported as excluded/caveat only"
                ),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "relationships_file": relpath(repo_root, relationships_file),
        "target_families": TARGET_FAMILIES,
        "predicate_family_map": PREDICATE_FAMILY_MAP,
        "family_rows": family_rows,
        "official_relationship_labels": labels,
        "labels_missing_mapping": labels_missing_mapping,
        "mapped_labels_not_in_file": mapped_labels_not_in_file,
        "adapter_rule": (
            "`none` is not exported as a relation prediction; unsupported/out-of-scope labels may remain "
            "in prediction JSONL but are excluded from H001 geometry-checkable metric denominator."
        ),
        "recall_rule": "Recall matching remains predicate-label exact; family grouping is for verifier/violation reporting, not label collapsing.",
    }


def count_ground_truth(repo_root: Path, gt_path: Path) -> dict[str, Any]:
    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    family_label_counts: Counter[tuple[str, str]] = Counter()
    rows = 0
    blockers: list[str] = []
    if not gt_path.exists():
        return {
            "ground_truth_jsonl": relpath(repo_root, gt_path),
            "status": "missing_ground_truth",
            "rows": 0,
            "blockers": [f"missing_ground_truth:{relpath(repo_root, gt_path)}"],
        }
    with gt_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                blockers.append(f"invalid_gt_jsonl:{line_no}:{exc}")
                continue
            family = str(row.get("predicate_family"))
            label = str(row.get("predicate_label"))
            family_counts[family] += 1
            label_counts[label] += 1
            family_label_counts[(family, label)] += 1

    in_scope = sum(family_counts[family] for family in TARGET_FAMILIES)
    excluded = rows - in_scope
    return {
        "ground_truth_jsonl": relpath(repo_root, gt_path),
        "status": "ready" if not blockers else "blocked",
        "rows": rows,
        "in_scope_gt_denominator": in_scope,
        "excluded_gt_rows": excluded,
        "target_family_counts": {family: family_counts[family] for family in TARGET_FAMILIES},
        "all_family_counts": dict(sorted(family_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "family_label_counts": {
            f"{family}::{label}": count
            for (family, label), count in sorted(family_label_counts.items())
        },
        "blockers": blockers,
    }


def filter_summary(repo_root: Path, train_filter: Path, validation_filter: Path, checkpoint_plan: Path) -> dict[str, Any]:
    train = load_json_if_exists(train_filter)
    validation = load_json_if_exists(validation_filter)
    plan = load_json_if_exists(checkpoint_plan)
    readiness = plan.get("current_readiness", {}) if isinstance(plan, dict) else {}
    return {
        "train_filter_manifest": relpath(repo_root, train_filter),
        "validation_filter_manifest": relpath(repo_root, validation_filter),
        "checkpoint_plan": relpath(repo_root, checkpoint_plan),
        "train": {
            "status": train.get("status") if isinstance(train, dict) else "missing",
            "original": train.get("original", {}) if isinstance(train, dict) else {},
            "filtered": train.get("filtered", {}) if isinstance(train, dict) else {},
            "removed": train.get("removed", {}) if isinstance(train, dict) else {},
        },
        "validation_train_dev": {
            "status": validation.get("status") if isinstance(validation, dict) else "missing",
            "original": validation.get("original", {}) if isinstance(validation, dict) else {},
            "filtered": validation.get("filtered", {}) if isinstance(validation, dict) else {},
            "removed": validation.get("removed", {}) if isinstance(validation, dict) else {},
        },
        "h001_eval_preprocess_readiness": {
            "status": readiness.get("h001_eval_preprocess"),
            "expected_contexts": readiness.get("h001_eval_preprocessed_expected"),
            "ready_contexts": readiness.get("h001_eval_preprocessed_ready"),
            "caveat": (
                "Plan-level eval preprocess readiness is not the final metric denominator. "
                "Final Open3DSG coverage must be recomputed from raw dump identity audit and adapter export."
            ),
        },
    }


def denominator_policy(gt: dict[str, Any], filters: dict[str, Any], raw_identity: dict[str, Any] | None) -> dict[str, Any]:
    raw_scope = raw_identity.get("scope", {}) if isinstance(raw_identity, dict) else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "metric_denominator": {
            "fixed_h001_eval_scope": {
                "scans": raw_scope.get("selected_scans", 127),
                "contexts": raw_scope.get("contexts", 388),
                "directed_pairs": raw_scope.get("directed_pairs", 25916),
            },
            "fixed_gt_rows": gt.get("rows"),
            "h001_geometry_checkable_gt_denominator": gt.get("in_scope_gt_denominator"),
            "target_family_counts": gt.get("target_family_counts"),
            "excluded_family_counts": {
                key: value
                for key, value in gt.get("all_family_counts", {}).items()
                if key not in TARGET_FAMILIES
            },
        },
        "prediction_scope_rule": {
            "candidate_predictions": "Open3DSG prediction JSONL may contain all exported predicates except `none`.",
            "metric_in_scope_predictions": "Rows whose predicate_family is support_contact, proximity, or relative_vertical.",
            "metric_excluded_predictions": "Rows in relative_horizontal, attachment_deferred, background_none, or unsupported_first_pass.",
            "topk_rule": "Top-k metrics must be computed after applying the same H001 family scope used for VL-SAT.",
        },
        "coverage_rule": {
            "full_h001_denominator_preferred": "Use 127 scans / 388 contexts / 2,545 in-scope GT rows if raw dump covers the fixed H001 identity scope.",
            "if_open3dsg_raw_dump_has_missing_contexts": (
                "Report covered_contexts, covered_gt_rows, excluded_contexts, and exclusion reasons. "
                "Do not silently treat missing Open3DSG contexts as model negatives or as full-denominator evidence."
            ),
            "intersection_claim_boundary": (
                "If Open3DSG coverage is filtered below the fixed H001 scope, Table 6 is an Open3DSG-covered-scope "
                "comparison, not a full H001-scope cross-source result."
            ),
        },
        "filtered_training_caveat": {
            "train": filters["train"],
            "validation_train_dev": filters["validation_train_dev"],
            "paper_wording": (
                "Open3DSG checkpoint reproduction uses an explicitly filtered preprocessed-ready runtime split. "
                "Report retained and removed train/train-dev subgraphs and relations; do not describe it as full "
                "official train preprocessing."
            ),
        },
        "h001_eval_preprocess_caveat": filters["h001_eval_preprocess_readiness"],
    }


def build_report(manifest: dict[str, Any]) -> str:
    gt = manifest["ground_truth_denominator"]
    filters = manifest["denominator_policy"]["filtered_training_caveat"]
    lines = [
        "# Open3DSG Metric Scope",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Fact",
        "",
        "- Predicate-family mapping and denominator policy are frozen before Open3DSG metric execution.",
        "- This artifact does not run Open3DSG metrics, inspect prediction failures, or change the verifier.",
        "- Recall matching remains predicate-label exact; family grouping is used for H001 verifier/violation reporting.",
        "",
        "## H001 Denominator",
        "",
        f"- all GT rows: `{gt.get('rows')}`",
        f"- in-scope GT rows: `{gt.get('in_scope_gt_denominator')}`",
        f"- target family counts: `{gt.get('target_family_counts')}`",
        "",
        "## Filtered Training Caveat",
        "",
        f"- train filtered: `{filters['train'].get('filtered')}`",
        f"- train removed: `{filters['train'].get('removed')}`",
        f"- train-dev filtered: `{filters['validation_train_dev'].get('filtered')}`",
        f"- train-dev removed: `{filters['validation_train_dev'].get('removed')}`",
        "",
        "## Claim Boundary",
        "",
        "Open3DSG Table 6 cannot be promoted to a full cross-source result unless raw dump coverage, prediction export, geometry join, and metric scope all match this policy.",
        "",
    ]
    if manifest["blockers"]:
        lines.extend(["## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
        lines.append("")
    return "\n".join(lines)


def build_commands() -> str:
    return """# Open3DSG Metric Scope Commands

Freeze or refresh the predicate-family mapping and denominator policy:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_scope'
```

Run this before real Open3DSG metric execution. Metric code must not change predicate-family mapping or denominator caveats after prediction/failure inspection.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    relationships_file = resolve(repo_root, args.relationships_file)
    gt_path = resolve(repo_root, args.ground_truth_jsonl)
    train_filter = resolve(repo_root, args.train_filter_manifest)
    validation_filter = resolve(repo_root, args.validation_filter_manifest)
    checkpoint_plan = resolve(repo_root, args.checkpoint_plan)
    raw_identity_path = resolve(repo_root, args.raw_identity_manifest)

    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = mapping_policy(repo_root, relationships_file)
    gt = count_ground_truth(repo_root, gt_path)
    filters = filter_summary(repo_root, train_filter, validation_filter, checkpoint_plan)
    raw_identity = load_json_if_exists(raw_identity_path)
    policy = denominator_policy(gt, filters, raw_identity)

    blockers: list[str] = []
    blockers.extend(gt.get("blockers", []))
    blockers.extend(f"unmapped_relationship_label:{label}" for label in mapping["labels_missing_mapping"])
    if filters["train"]["status"] != "filter_applied":
        blockers.append(f"train_filter_not_applied:{filters['train']['status']}")
    if filters["validation_train_dev"]["status"] != "filter_applied":
        blockers.append(f"validation_filter_not_applied:{filters['validation_train_dev']['status']}")
    if raw_identity is None:
        blockers.append(f"missing_raw_identity_manifest:{relpath(repo_root, raw_identity_path)}")
    elif raw_identity.get("scope", {}).get("status") != "ready":
        blockers.append(f"raw_identity_scope_not_ready:{raw_identity.get('scope', {}).get('status')}")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": STATUS_READY if not blockers else "metric_scope_policy_blocked",
        "predicate_mapping": "predicate_mapping.json",
        "denominator_policy": "denominator_policy.json",
        "ground_truth_denominator": gt,
        "filter_summary": filters,
        "raw_identity_manifest": relpath(repo_root, raw_identity_path),
        "blockers": blockers,
        "claim_boundary": (
            "This artifact freezes mapping and denominator policy only. It is not Open3DSG metric evidence."
        ),
    }

    write_json(out_dir / "predicate_mapping.json", mapping)
    write_json(out_dir / "denominator_policy.json", policy)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "commands.md").write_text(build_commands(), encoding="utf-8")
    (out_dir / "report.md").write_text(build_report({**manifest, "denominator_policy": policy}), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "in_scope_gt_denominator": gt.get("in_scope_gt_denominator"),
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
