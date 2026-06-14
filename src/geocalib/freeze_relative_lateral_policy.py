#!/usr/bin/env python3
"""Freeze the relative-lateral family split and geometry-policy provenance.

This step separates left/right from front/behind after the broader
relative-horizontal coordinate audit. It does not run source metrics and does
not update the paper claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_relative_lateral_policy_freeze_v1"
STATUS = "relative_lateral_policy_threshold_provenance_frozen_no_source_metrics"
TARGET_FAMILY = "relative_lateral"
TARGET_LABELS = ("left", "right")
DEFERRED_FAMILY = "relative_depth_deferred"
DEFERRED_LABELS = ("front", "behind")
DEFAULT_RELH_ROOT = Path("archive/experiments/H001_geom_reliability/sources/relative_horizontal")
DEFAULT_OUT = Path("archive/experiments/H001_geom_reliability/sources/relative_lateral/policy_freeze")
DEFAULT_TRAIN_JSON = Path("local_dataset/3DSSG_subset/relationships_train.json")
DEFAULT_TRAIN_SCANS = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/subset/h001_calib_pilot/train_scans.txt"
)
DEFAULT_DEV_SCANS = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/subset/h001_calib_pilot/dev_scans.txt"
)
CURRENT_FAMILIES = ("support_contact", "proximity", "relative_vertical")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--relative-horizontal-root", type=Path, default=DEFAULT_RELH_ROOT)
    parser.add_argument("--train-json", type=Path, default=DEFAULT_TRAIN_JSON)
    parser.add_argument("--train-scans", type=Path, default=DEFAULT_TRAIN_SCANS)
    parser.add_argument("--dev-scans", type=Path, default=DEFAULT_DEV_SCANS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_scan_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def combine_label_metrics(frame: dict[str, Any], labels: tuple[str, ...]) -> dict[str, Any]:
    strict_match = sum(int(frame["by_label"][label]["strict"]["match"]) for label in labels)
    strict_contra = sum(int(frame["by_label"][label]["strict"]["contradiction"]) for label in labels)
    strict_eligible = sum(int(frame["by_label"][label]["strict"]["eligible"]) for label in labels)
    strict_uncertain = sum(int(frame["by_label"][label]["strict"]["uncertain"]) for label in labels)
    sign_match = sum(int(frame["by_label"][label]["sign_only"]["match"]) for label in labels)
    sign_contra = sum(int(frame["by_label"][label]["sign_only"]["contradiction"]) for label in labels)
    sign_eligible = sum(int(frame["by_label"][label]["sign_only"]["eligible"]) for label in labels)
    sign_uncertain = sum(int(frame["by_label"][label]["sign_only"]["uncertain"]) for label in labels)
    total = sum(int(frame["by_label"][label]["total"]) for label in labels)
    ambiguity = Counter()
    for label in labels:
        for key, value in frame["by_label"][label].get("ambiguity_flag_counts", {}).items():
            ambiguity[key] += int(value)
    return {
        "labels": list(labels),
        "total": total,
        "strict": {
            "match": strict_match,
            "contradiction": strict_contra,
            "eligible": strict_eligible,
            "uncertain": strict_uncertain,
            "purity": strict_match / strict_eligible if strict_eligible else None,
            "eligible_share": strict_eligible / total if total else None,
            "match_to_contradiction_ratio": strict_match / strict_contra if strict_contra else None,
        },
        "sign_only": {
            "match": sign_match,
            "contradiction": sign_contra,
            "eligible": sign_eligible,
            "uncertain": sign_uncertain,
            "purity": sign_match / sign_eligible if sign_eligible else None,
            "eligible_share": sign_eligible / total if total else None,
            "match_to_contradiction_ratio": sign_match / sign_contra if sign_contra else None,
        },
        "ambiguity_flag_counts": dict(sorted(ambiguity.items())),
    }


def rounded_axis(axis: list[Any] | tuple[Any, ...]) -> tuple[float, float]:
    return (round(float(axis[0]), 6), round(float(axis[1]), 6))


def select_lateral_frame(frames: list[dict[str, Any]], preferred_name: str | None) -> tuple[dict[str, Any], list[dict[str, Any]], float | None]:
    ranked: list[dict[str, Any]] = []
    for frame in frames:
        metrics = combine_label_metrics(frame, TARGET_LABELS)
        ranked.append(
            {
                "frame_name": frame["frame_name"],
                "frame_family": frame["frame_family"],
                "left_axis": frame["left_axis"],
                "front_axis": frame["front_axis"],
                "lateral_metrics": metrics,
                "sort_key": (
                    metrics["strict"]["purity"] if metrics["strict"]["purity"] is not None else -1.0,
                    metrics["strict"]["eligible_share"] if metrics["strict"]["eligible_share"] is not None else -1.0,
                    metrics["sign_only"]["purity"] if metrics["sign_only"]["purity"] is not None else -1.0,
                    1.0 if frame["frame_name"] == preferred_name else 0.0,
                    frame["frame_name"],
                ),
            }
        )
    ranked.sort(key=lambda item: item["sort_key"], reverse=True)
    selected = ranked[0]
    selected_left_axis = rounded_axis(selected["left_axis"])
    competing = [
        item for item in ranked[1:] if rounded_axis(item["left_axis"]) != selected_left_axis
    ]
    gap = None
    if competing:
        gap = (
            float(selected["lateral_metrics"]["strict"]["purity"])
            - float(competing[0]["lateral_metrics"]["strict"]["purity"])
        )
    return selected, ranked, gap


def train_dev_counts(train_json: Path, train_scans: set[str], dev_scans: set[str]) -> dict[str, Any]:
    if not train_json.exists():
        return {"status": "missing_train_json", "path": str(train_json)}
    payload = read_json(train_json)
    split_counts: dict[str, Counter[str]] = {
        "train": Counter(),
        "dev": Counter(),
        "other_train_json": Counter(),
    }
    subgraphs = Counter()
    for entry in payload.get("scans", []):
        scan_id = str(entry.get("scan"))
        if scan_id in train_scans:
            split = "train"
        elif scan_id in dev_scans:
            split = "dev"
        else:
            split = "other_train_json"
        subgraphs[split] += 1
        for relation in entry.get("relationships", []):
            if len(relation) < 4:
                continue
            label = str(relation[3])
            if label in TARGET_LABELS or label in DEFERRED_LABELS:
                split_counts[split][label] += 1
    return {
        "status": "ready",
        "path": str(train_json),
        "scan_counts": {
            "train_scan_ids": len(train_scans),
            "dev_scan_ids": len(dev_scans),
        },
        "subgraph_counts": dict(sorted(subgraphs.items())),
        "label_counts": {
            split: dict(sorted(counts.items())) for split, counts in split_counts.items()
        },
        "relative_lateral_counts": {
            split: sum(counts.get(label, 0) for label in TARGET_LABELS)
            for split, counts in split_counts.items()
        },
        "relative_depth_deferred_counts": {
            split: sum(counts.get(label, 0) for label in DEFERRED_LABELS)
            for split, counts in split_counts.items()
        },
    }


def source_rows(scope: dict[str, Any], labels: tuple[str, ...]) -> dict[str, Any]:
    result = {}
    existing = scope.get("existing_verification_status", {})
    for source_key, payload in existing.items():
        counts = payload.get("label_counts", {})
        rows = sum(int(counts.get(label, 0)) for label in labels)
        result[source_key] = {
            "rows": rows,
            "label_counts": {label: int(counts.get(label, 0)) for label in labels},
            "verification_status_counts": {"unsupported": rows},
            "verification_status_note": "lateral-only count derived from per-label rows; source verifier has not been run for this family",
        }
    return result


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def report_md(manifest: dict[str, Any]) -> str:
    lat = manifest["coordinate_evidence"]["relative_lateral"]
    depth = manifest["coordinate_evidence"]["relative_depth_deferred"]
    denom = manifest["denominator"]
    train_dev = manifest["train_dev_provenance"]
    lines = [
        "# Relative Lateral Policy Freeze",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This artifact splits `left/right` into `relative_lateral` and defers",
        "`front/behind` as `relative_depth_deferred`. It freezes denominator,",
        "geometry policy, and threshold provenance only. It is not source metric",
        "evidence and does not change the AAAI main claim.",
        "",
        "## Family Split",
        "",
        "| Family | Labels | GT rows | Status |",
        "|---|---|---:|---|",
        f"| `relative_lateral` | `left`, `right` | {denom['relative_lateral_gt_rows']} | frozen candidate |",
        f"| `relative_depth_deferred` | `front`, `behind` | {denom['relative_depth_deferred_gt_rows']} | deferred |",
        "",
        "## Lateral Coordinate Evidence",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| selected frame | `{manifest['geometry_policy']['selected_frame']}` |",
        f"| strict purity | {fmt(lat['strict']['purity'])} |",
        f"| strict eligible share | {fmt(lat['strict']['eligible_share'])} |",
        f"| strict match/contradiction | {lat['strict']['match']} / {lat['strict']['contradiction']} |",
        f"| sign-only purity | {fmt(lat['sign_only']['purity'])} |",
        f"| distinct-left-axis wrong-frame gap | {fmt(manifest['coordinate_evidence']['distinct_left_axis_wrong_frame_gap'])} |",
        "",
        "## Deferred Depth Evidence",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| strict purity | {fmt(depth['strict']['purity'])} |",
        f"| strict eligible share | {fmt(depth['strict']['eligible_share'])} |",
        f"| strict match/contradiction | {depth['strict']['match']} / {depth['strict']['contradiction']} |",
        "",
        "## Train/Dev Provenance",
        "",
        f"- train/dev source: `{train_dev['path']}`",
        f"- train lateral rows: `{train_dev['relative_lateral_counts'].get('train', 0)}`",
        f"- dev lateral rows: `{train_dev['relative_lateral_counts'].get('dev', 0)}`",
        f"- train depth-deferred rows: `{train_dev['relative_depth_deferred_counts'].get('train', 0)}`",
        f"- dev depth-deferred rows: `{train_dev['relative_depth_deferred_counts'].get('dev', 0)}`",
        "",
        "## Promotion Limits",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    lines.append("")
    return "\n".join(lines)


def commands_md() -> str:
    return """# Relative Lateral Policy Freeze Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  relative_lateral_policy_freeze
```

This freezes family split, denominator, geometry policy, and threshold
provenance only. It does not run source metrics or update the paper claim.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    relh_root = resolve(repo_root, args.relative_horizontal_root)
    out = resolve(repo_root, args.out)
    train_json = resolve(repo_root, args.train_json)
    train_scans = read_scan_set(resolve(repo_root, args.train_scans))
    dev_scans = read_scan_set(resolve(repo_root, args.dev_scans))

    scope = read_json(relh_root / "scope_audit" / "manifest.json")
    coord = read_json(relh_root / "coordinate_audit" / "manifest.json")
    frames = read_json(relh_root / "coordinate_audit" / "frame_metrics.json")["frames"]
    bucket = read_json(relh_root / "bucket_inspection" / "summary.json")

    preferred = coord.get("selected_frame", {}).get("frame_name")
    selected, ranked, distinct_axis_gap = select_lateral_frame(frames, preferred)
    lateral = selected["lateral_metrics"]
    selected_frame = selected["frame_name"]
    selected_left_axis = selected["left_axis"]
    selected_front_axis = selected["front_axis"]
    depth = combine_label_metrics(
        next(frame for frame in frames if frame["frame_name"] == selected_frame),
        DEFERRED_LABELS,
    )

    gt_counts = scope["ground_truth"]["relative_horizontal_label_counts"]
    lateral_gt = sum(int(gt_counts.get(label, 0)) for label in TARGET_LABELS)
    depth_gt = sum(int(gt_counts.get(label, 0)) for label in DEFERRED_LABELS)
    current_den = int(scope["denominator"]["current_h001_gt_denominator"])
    thresholds = coord.get("thresholds", {})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "current_families": list(CURRENT_FAMILIES),
            "candidate_family": TARGET_FAMILY,
            "deferred_family": DEFERRED_FAMILY,
            "source_metrics_run": False,
            "paper_claim_promotion_allowed": False,
            "reason": "Family split and policy provenance only; source metrics and audit are not run.",
        },
        "inputs": {
            "relative_horizontal_scope_manifest": relpath(repo_root, relh_root / "scope_audit" / "manifest.json"),
            "relative_horizontal_coordinate_manifest": relpath(repo_root, relh_root / "coordinate_audit" / "manifest.json"),
            "relative_horizontal_frame_metrics": relpath(repo_root, relh_root / "coordinate_audit" / "frame_metrics.json"),
            "relative_horizontal_bucket_summary": relpath(repo_root, relh_root / "bucket_inspection" / "summary.json"),
            "train_json": relpath(repo_root, train_json),
            "train_scans": relpath(repo_root, resolve(repo_root, args.train_scans)),
            "dev_scans": relpath(repo_root, resolve(repo_root, args.dev_scans)),
        },
        "family_split": {
            "relative_lateral": {
                "labels": list(TARGET_LABELS),
                "definition": "lateral relation along the selected scan x-axis sign convention",
                "rationale": "left/right have symmetric inverse consistency and higher strict purity than front/behind.",
            },
            "relative_depth_deferred": {
                "labels": list(DEFERRED_LABELS),
                "definition": "front/behind depth relation with unresolved frame/viewpoint semantics",
                "rationale": "front/behind purity and ambiguity buckets remain below promotion standard.",
            },
        },
        "denominator": {
            "current_h001_gt_denominator": current_den,
            "relative_lateral_gt_rows": lateral_gt,
            "relative_lateral_label_counts": {label: int(gt_counts.get(label, 0)) for label in TARGET_LABELS},
            "relative_depth_deferred_gt_rows": depth_gt,
            "relative_depth_deferred_label_counts": {label: int(gt_counts.get(label, 0)) for label in DEFERRED_LABELS},
            "expanded_if_lateral_validated": current_den + lateral_gt,
            "expanded_if_full_relative_horizontal_validated": int(scope["denominator"]["expanded_candidate_denominator"]),
            "all_held_out_gt_rows": int(scope["denominator"]["all_held_out_gt_rows"]),
        },
        "source_rows": {
            "relative_lateral": source_rows(scope, TARGET_LABELS),
            "relative_depth_deferred": source_rows(scope, DEFERRED_LABELS),
        },
        "geometry_policy": {
            "policy_name": "relative_lateral_scan_x_sign_policy_v1",
            "selected_frame": selected_frame,
            "selected_left_axis": selected_left_axis,
            "orthogonal_axis_for_ambiguity_only": selected_front_axis,
            "status_rules": {
                "satisfied": "left if subject-object center delta projects positively on selected_left_axis, right if it projects negatively, with no ambiguity flags",
                "violated": "opposite sign under the same non-ambiguous condition",
                "uncertain": "missing geometry, axis margin ambiguity, strong projected overlap, or orthogonal-axis dominance",
            },
            "inverse_consistency_rule": "left/right inverse-pair consistency is a sanity check and is not used to override row-level geometry status.",
            "exact_label_recall": True,
            "front_behind_excluded": True,
        },
        "threshold_provenance": {
            "status": "frozen_provenance_no_metric_execution",
            "threshold_source": "inherited from pre-existing relative_horizontal coordinate audit constants before relative_lateral source metrics",
            "threshold_basis": {
                "official_benchmark_threshold": False,
                "purpose": "operational sanity gate for deciding whether a relation family deserves full source-metric execution",
                "predeclared_before_relative_lateral_source_metrics": True,
                "not_used_as_primary_result": True,
                "reported_as_continuous_evidence": [
                    "strict purity",
                    "strict eligible share",
                    "inverse consistency",
                    "distinct-left-axis wrong-frame gap",
                    "ambiguity buckets",
                ],
                "anti_tuning_rule": "If promoted later, threshold/policy lock must be rerun on train/dev provenance before held-out source metrics are used as paper evidence.",
            },
            "thresholds": thresholds,
            "not_tuned_on_source_predictions": True,
            "heldout_audit_used_for_family_split": True,
            "main_claim_caveat": (
                "Because the split was motivated by the held-out coordinate audit, "
                "main-claim promotion requires a train/dev calibration or policy-lock "
                "rerun before held-out source metrics are used as paper evidence."
            ),
        },
        "train_dev_provenance": train_dev_counts(train_json, train_scans, dev_scans),
        "coordinate_evidence": {
            "relative_lateral": lateral,
            "relative_depth_deferred": depth,
            "selected_frame": selected_frame,
            "lateral_front_axis_tie_expected": True,
            "distinct_left_axis_wrong_frame_gap": distinct_axis_gap,
            "top_lateral_frame_candidates": [
                {
                    "frame_name": item["frame_name"],
                    "frame_family": item["frame_family"],
                    "left_axis": item["left_axis"],
                    "front_axis": item["front_axis"],
                    "strict_purity": item["lateral_metrics"]["strict"]["purity"],
                    "strict_eligible_share": item["lateral_metrics"]["strict"]["eligible_share"],
                    "sign_only_purity": item["lateral_metrics"]["sign_only"]["purity"],
                }
                for item in ranked[:8]
            ],
            "bucket_summary_reference": {
                "relative_lateral_left": bucket["by_label"]["left"],
                "relative_lateral_right": bucket["by_label"]["right"],
                "relative_depth_front": bucket["by_label"]["front"],
                "relative_depth_behind": bucket["by_label"]["behind"],
            },
        },
        "blockers": [
            "train_dev_policy_lock_or_calibration_fit_not_run",
            "relative_lateral_source_metrics_not_run",
            "controls_not_run",
            "bootstrap_ci_not_run",
            "failure_analysis_and_visual_audit_not_run",
            "main_claim_requires_explicit_user_confirmation",
        ],
        "next_gate": "relative_lateral_train_dev_policy_lock_or_calibration",
    }

    family_split = manifest["family_split"]
    denominator = manifest["denominator"]
    geometry_policy = manifest["geometry_policy"]
    threshold_provenance = manifest["threshold_provenance"]
    calibration_plan = {
        "schema_version": SCHEMA_VERSION,
        "status": "relative_lateral_train_dev_calibration_plan_frozen_no_fit",
        "positive_seed_source": relpath(repo_root, train_json),
        "split_source": {
            "train_scans": relpath(repo_root, resolve(repo_root, args.train_scans)),
            "dev_scans": relpath(repo_root, resolve(repo_root, args.dev_scans)),
        },
        "candidate_positive_labels": list(TARGET_LABELS),
        "candidate_counterfactuals": [
            "inverse_label_counterfactual:left_to_right_or_right_to_left",
            "wrong_pair_lateral_geometry",
            "axis_margin_ambiguous_as_uncertain_not_negative",
            "strong_overlap_ambiguous_as_uncertain_not_negative",
        ],
        "fit_policy": "Use train/dev only; do not use held-out source metrics or failure rows to tune thresholds.",
        "required_before_main_promotion": True,
        "train_dev_counts": manifest["train_dev_provenance"],
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "family_split.json", family_split)
    write_json(out / "denominator.json", denominator)
    write_json(out / "geometry_policy.json", geometry_policy)
    write_json(out / "threshold_provenance.json", threshold_provenance)
    write_json(out / "calibration_plan.json", calibration_plan)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest))
    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "relative_lateral_gt_rows": lateral_gt,
                "relative_depth_deferred_gt_rows": depth_gt,
                "strict_purity": lateral["strict"]["purity"],
                "strict_eligible_share": lateral["strict"]["eligible_share"],
                "distinct_left_axis_wrong_frame_gap": distinct_axis_gap,
                "train_lateral_rows": manifest["train_dev_provenance"].get("relative_lateral_counts", {}).get("train"),
                "dev_lateral_rows": manifest["train_dev_provenance"].get("relative_lateral_counts", {}).get("dev"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
