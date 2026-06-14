#!/usr/bin/env python3
"""Prepare the attachment-deferred G3 calibration/counterfactual route.

This step freezes train-dev positive seeds, counterfactual-negative seed
generation policy, policy-smoke routing, GT verifier-evaluation inputs, and the
threshold-freeze protocol before any held-out source metrics. It does not apply
the verifier policy, fit a calibrator, score source predictions, or compute
paper metrics.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from paths import H001_HYPOTHESIS_REL


SCHEMA_VERSION = "h001_attachment_deferred_calibration_counterfactuals_v1"
POSITIVE_SCHEMA_VERSION = "h001_attachment_deferred_positive_seed_v1"
NEGATIVE_SCHEMA_VERSION = "h001_attachment_deferred_counterfactual_seed_v1"
STATUS = "attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics"
TARGET_FAMILY = "attachment_deferred"
NEXT_GATE = "G4_attachment_gt_verifier_evaluation_and_policy_smoke"
PREDICATE_LABELS = ("attached to", "hanging on", "connected to")

HYPOTHESIS_ROOT = H001_HYPOTHESIS_REL
DEFAULT_CALIB_ROOT = HYPOTHESIS_ROOT / "artifacts/subset/h001_calib_pilot"
DEFAULT_TRAIN_SCANS = DEFAULT_CALIB_ROOT / "train_scans.txt"
DEFAULT_DEV_SCANS = DEFAULT_CALIB_ROOT / "dev_scans.txt"
DEFAULT_HELDOUT_GT = (
    HYPOTHESIS_ROOT
    / "artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
)
DEFAULT_SUBSET_JSON = Path("local_dataset/3DSSG_subset/relationships_train.json")
DEFAULT_EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")
DEFAULT_ATTACHMENT_ROOT = DEFAULT_EXPERIMENT_ROOT / "sources/attachment_deferred"
DEFAULT_POLICY_DIR = DEFAULT_ATTACHMENT_ROOT / "verifier_policy"
DEFAULT_POINT_SURFACE_DIR = DEFAULT_ATTACHMENT_ROOT / "point_surface_validation"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "calibration_counterfactuals"

FLOOR_LABELS = {"floor"}
VERTICAL_SURFACE_LABELS = {"wall", "window", "door", "doorframe", "mirror", "picture"}
OVERHEAD_LABELS = {"ceiling", "light", "lamp"}
FURNITURE_LABELS = {
    "table",
    "desk",
    "counter",
    "kitchen counter",
    "shelf",
    "cabinet",
    "sofa",
    "chair",
    "bed",
    "stool",
    "bench",
    "wardrobe",
}
FIXTURE_LABELS = {
    "tv",
    "monitor",
    "radiator",
    "sink",
    "toilet",
    "curtain",
    "pipe",
    "heater",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare attachment-deferred G3 calibration/counterfactual route."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--subset-json", type=Path, default=DEFAULT_SUBSET_JSON)
    parser.add_argument("--train-scans", type=Path, default=DEFAULT_TRAIN_SCANS)
    parser.add_argument("--dev-scans", type=Path, default=DEFAULT_DEV_SCANS)
    parser.add_argument("--heldout-gt-jsonl", type=Path, default=DEFAULT_HELDOUT_GT)
    parser.add_argument("--verifier-policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--point-surface-dir", type=Path, default=DEFAULT_POINT_SURFACE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-negatives-per-positive", type=int, default=2)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_scan_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def surface_type(label: str | None) -> str:
    normalized = (label or "").strip().lower()
    if normalized in FLOOR_LABELS:
        return "floor"
    if normalized in {"ceiling"}:
        return "ceiling"
    if normalized in VERTICAL_SURFACE_LABELS:
        return "wall"
    if normalized in FURNITURE_LABELS:
        return "furniture"
    if normalized in FIXTURE_LABELS:
        return "fixture"
    return "object_part"


def subtype_hint(predicate_label: str, subject_label: str, object_label: str) -> str:
    support_type = surface_type(object_label)
    if predicate_label == "attached to":
        if support_type in {"wall", "ceiling", "fixture"}:
            return "attached_to_vertical_or_overhead_surface"
        if support_type in {"furniture", "object_part"}:
            return "attached_to_furniture_or_fixture"
        return "ambiguous_functional_attachment"
    if predicate_label == "hanging on":
        if support_type in {"ceiling", "fixture"}:
            return "hanging_from_overhead_or_fixture"
        if support_type in {"wall", "furniture", "object_part"}:
            return "hanging_from_vertical_surface"
        return "ambiguous_draped_or_occluded_hanging"
    if predicate_label == "connected to":
        if support_type in {"fixture", "furniture", "object_part"}:
            return "connected_by_fixture_or_part"
        return "connected_adjacent_or_contiguous"
    return "unknown"


def load_heldout_scans(path: Path) -> set[str]:
    scans: set[str] = set()
    if not path.exists():
        return scans
    for row in iter_jsonl(path):
        scan_id = row.get("scan_id")
        if scan_id:
            scans.add(str(scan_id))
    return scans


def load_relationship_scans(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    scans = payload.get("scans") if isinstance(payload, dict) else None
    if not isinstance(scans, list):
        raise ValueError(f"relationships_json_missing_scans:{path}")
    return scans


def make_positive_seed(
    *,
    scan: dict[str, Any],
    relation: list[Any],
    relation_index: int,
    split_role: str,
) -> dict[str, Any]:
    scan_id = str(scan["scan"])
    subset_split_id = int(scan["split"])
    subject_id = int(relation[0])
    object_id = int(relation[1])
    raw_predicate_id = int(relation[2])
    predicate_label = str(relation[3])
    objects = scan.get("objects", {})
    subject_label = str(objects.get(str(subject_id), "unknown"))
    object_label = str(objects.get(str(object_id), "unknown"))
    subgraph_id = f"{scan_id}_{subset_split_id}"
    seed_id = (
        f"pos:attachment_g3:{split_role}:{scan_id}:{subset_split_id}:"
        f"{subject_id}:{object_id}:{predicate_label}:{relation_index}"
    )
    return {
        "schema_version": POSITIVE_SCHEMA_VERSION,
        "record_type": "calibration_positive_seed",
        "seed_id": seed_id,
        "split_name": "attachment_deferred_train_dev",
        "split_role": split_role,
        "scan_id": scan_id,
        "subgraph_id": subgraph_id,
        "subset_split_id": subset_split_id,
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_label": subject_label,
        "object_label": object_label,
        "predicate_family": TARGET_FAMILY,
        "predicate_label": predicate_label,
        "raw_3dssg_predicate_id": raw_predicate_id,
        "subtype_hint": subtype_hint(predicate_label, subject_label, object_label),
        "label": {
            "geom_valid": 1,
            "label_status": "positive",
            "label_source": "gt_attachment_positive_train_dev",
        },
        "quality": {
            "calibration_role": "train_dev_candidate",
            "leakage_group": "scan_id",
            "requires_evidence_extraction": True,
            "requires_policy_application": True,
        },
        "provenance": {
            "source": "local_dataset/3DSSG_subset/relationships_train.json",
            "source_relation_index": relation_index,
        },
    }


def candidate_object_ids(scan: dict[str, Any], exclude: set[int]) -> list[int]:
    ids = []
    for raw_id in scan.get("objects", {}).keys():
        try:
            object_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if object_id not in exclude:
            ids.append(object_id)
    return sorted(ids)


def relation_key(relation: list[Any]) -> tuple[int, int, str]:
    return int(relation[0]), int(relation[1]), str(relation[3])


def strategy_candidates(
    positive: dict[str, Any],
    scan: dict[str, Any],
    existing_positive_edges: set[tuple[int, int, str]],
) -> list[dict[str, Any]]:
    predicate_label = positive["predicate_label"]
    subject_id = int(positive["subject_id"])
    object_id = int(positive["object_id"])
    objects = scan.get("objects", {})
    object_ids = candidate_object_ids(scan, {subject_id, object_id})
    candidates: list[dict[str, Any]] = []

    def add(strategy: str, candidate_object_id: int, required_checks: list[str]) -> None:
        candidate_label = str(objects.get(str(candidate_object_id), "unknown"))
        key = (subject_id, candidate_object_id, predicate_label)
        if key in existing_positive_edges:
            return
        candidates.append(
            {
                "strategy": strategy,
                "subject_id": subject_id,
                "object_id": candidate_object_id,
                "subject_label": positive["subject_label"],
                "object_label": candidate_label,
                "required_margin_checks": required_checks,
            }
        )

    if predicate_label == "hanging on":
        for candidate_object_id in object_ids:
            if surface_type(str(objects.get(str(candidate_object_id), ""))) == "floor":
                add(
                    "floor_support_replacement_for_hanging",
                    candidate_object_id,
                    [
                        "surface_type_contradicts_hanging",
                        "floor_or_table_supported",
                        "hanging_geometry_score_low",
                    ],
                )
                break
        for candidate_object_id in object_ids:
            add(
                "gravity_inconsistent_hanging",
                candidate_object_id,
                [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                    "floor_clearance_below_hanging_minimum",
                ],
            )
            break
    elif predicate_label == "attached to":
        for candidate_object_id in object_ids:
            if surface_type(str(objects.get(str(candidate_object_id), ""))) == "floor":
                add(
                    "wrong_surface_replacement",
                    candidate_object_id,
                    [
                        "surface_type_floor_or_unknown",
                        "min_point_distance_m_ge_clear_far_or_no_contact",
                    ],
                )
                break
        for candidate_object_id in object_ids:
            add(
                "far_object_pair",
                candidate_object_id,
                [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                ],
            )
            break
    elif predicate_label == "connected to":
        for candidate_object_id in object_ids:
            add(
                "wrong_pair_attachment",
                candidate_object_id,
                [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                    "no_visible_connector_or_contiguity",
                ],
            )
            break
        for candidate_object_id in reversed(object_ids):
            add(
                "far_object_pair",
                candidate_object_id,
                [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                ],
            )
            break
    return candidates


def make_negative_seed(
    positive: dict[str, Any],
    candidate: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    negative_id = (
        f"neg:attachment_g3:{positive['split_role']}:{positive['scan_id']}:"
        f"{positive['subset_split_id']}:{candidate['subject_id']}:{candidate['object_id']}:"
        f"{positive['predicate_label']}:{candidate['strategy']}:{index}"
    )
    return {
        "schema_version": NEGATIVE_SCHEMA_VERSION,
        "record_type": "counterfactual_negative_seed",
        "negative_id": negative_id,
        "base_positive_seed_id": positive["seed_id"],
        "split_name": positive["split_name"],
        "split_role": positive["split_role"],
        "scan_id": positive["scan_id"],
        "subgraph_id": positive["subgraph_id"],
        "subset_split_id": positive["subset_split_id"],
        "subject_id": candidate["subject_id"],
        "object_id": candidate["object_id"],
        "subject_label": candidate["subject_label"],
        "object_label": candidate["object_label"],
        "predicate_family": TARGET_FAMILY,
        "predicate_label": positive["predicate_label"],
        "subtype_hint": subtype_hint(
            positive["predicate_label"],
            candidate["subject_label"],
            candidate["object_label"],
        ),
        "strategy": candidate["strategy"],
        "required_margin_checks": candidate["required_margin_checks"],
        "label": {
            "geom_valid": 0,
            "label_status": "counterfactual_negative_seed",
            "label_source": "attachment_counterfactual_requires_geometry_margin",
        },
        "quality": {
            "calibration_role": "train_dev_candidate",
            "leakage_group": "scan_id",
            "requires_evidence_extraction": True,
            "requires_policy_application": True,
            "requires_geometry_margin_validation": True,
            "emit_to_calibration_table": False,
        },
    }


def build_seeds(
    scans: list[dict[str, Any]],
    train_scans: set[str],
    dev_scans: set[str],
    *,
    max_negatives_per_positive: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    positives: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    negative_ids: set[str] = set()
    positive_counts: Counter[str] = Counter()
    negative_counts: Counter[str] = Counter()
    skipped: Counter[str] = Counter()
    positive_edges_by_subgraph: dict[tuple[str, int], set[tuple[int, int, str]]] = {}

    for scan in scans:
        scan_id = str(scan.get("scan"))
        if scan_id not in train_scans and scan_id not in dev_scans:
            continue
        subset_split_id = int(scan["split"])
        key = (scan_id, subset_split_id)
        edges = set()
        for relation in scan.get("relationships", []):
            if isinstance(relation, list) and len(relation) >= 4:
                edges.add(relation_key(relation))
        positive_edges_by_subgraph[key] = edges

    scan_lookup = {(str(scan.get("scan")), int(scan["split"])): scan for scan in scans}
    for scan in scans:
        scan_id = str(scan.get("scan"))
        if scan_id in train_scans:
            split_role = "train"
        elif scan_id in dev_scans:
            split_role = "dev"
        else:
            continue
        subset_split_id = int(scan["split"])
        existing_edges = positive_edges_by_subgraph[(scan_id, subset_split_id)]
        for relation_index, relation in enumerate(scan.get("relationships", [])):
            if not isinstance(relation, list) or len(relation) < 4:
                continue
            predicate_label = str(relation[3])
            if predicate_label not in PREDICATE_LABELS:
                continue
            positive = make_positive_seed(
                scan=scan,
                relation=relation,
                relation_index=relation_index,
                split_role=split_role,
            )
            positives.append(positive)
            positive_counts[f"{split_role}:{predicate_label}"] += 1

            generated_for_positive = 0
            for candidate_index, candidate in enumerate(
                strategy_candidates(positive, scan_lookup[(scan_id, subset_split_id)], existing_edges)
            ):
                if generated_for_positive >= max_negatives_per_positive:
                    break
                negative = make_negative_seed(positive, candidate, candidate_index)
                if negative["negative_id"] in negative_ids:
                    skipped["duplicate_negative_id"] += 1
                    continue
                negative_ids.add(negative["negative_id"])
                negatives.append(negative)
                generated_for_positive += 1
                negative_counts[f"{split_role}:{negative['predicate_label']}:{negative['strategy']}"] += 1
            if generated_for_positive == 0:
                skipped[f"no_negative_candidate:{split_role}:{predicate_label}"] += 1

    summary = {
        "positive_counts": dict(sorted(positive_counts.items())),
        "negative_counts": dict(sorted(negative_counts.items())),
        "skipped_negative_generation": dict(sorted(skipped.items())),
    }
    return positives, negatives, summary


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_role = Counter(row["split_role"] for row in rows)
    by_label = Counter(row["predicate_label"] for row in rows)
    by_role_label = Counter(f"{row['split_role']}:{row['predicate_label']}" for row in rows)
    scans_by_role: dict[str, set[str]] = defaultdict(set)
    subgraphs_by_role: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        scans_by_role[row["split_role"]].add(row["scan_id"])
        subgraphs_by_role[row["split_role"]].add(row["subgraph_id"])
    return {
        "rows": len(rows),
        "by_role": dict(sorted(by_role.items())),
        "by_label": dict(sorted(by_label.items())),
        "by_role_label": dict(sorted(by_role_label.items())),
        "scans_by_role": {key: len(value) for key, value in sorted(scans_by_role.items())},
        "subgraphs_by_role": {key: len(value) for key, value in sorted(subgraphs_by_role.items())},
    }


def summarize_negative_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_rows(rows)
    summary["by_strategy"] = dict(sorted(Counter(row["strategy"] for row in rows).items()))
    summary["by_role_strategy"] = dict(
        sorted(Counter(f"{row['split_role']}:{row['strategy']}" for row in rows).items())
    )
    return summary


def count_smoke_rows(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "by_source": {}, "by_label": {}, "path_exists": False}
    by_source: Counter[str] = Counter()
    by_label: Counter[str] = Counter()
    rows = 0
    for row in iter_jsonl(path):
        rows += 1
        by_source[str(row.get("source_name", "missing"))] += 1
        by_label[str(row.get("predicate_label", "missing"))] += 1
    return {
        "rows": rows,
        "by_source": dict(sorted(by_source.items())),
        "by_label": dict(sorted(by_label.items())),
        "path_exists": True,
    }


def counterfactual_plan(max_negatives_per_positive: int) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "negative_seed_policy": "counterfactual_seeds_require_geometry_margin_validation",
        "max_negatives_per_positive": max_negatives_per_positive,
        "do_not_use_absent_edges_as_negatives": True,
        "strategies": {
            "wrong_surface_replacement": {
                "role": "tests predicate/surface compatibility",
                "required_margin_checks": [
                    "surface_type_floor_or_unknown",
                    "min_point_distance_m_ge_clear_far_or_no_contact",
                ],
            },
            "far_object_pair": {
                "role": "tests clear separation from plausible attachment/contact surface",
                "required_margin_checks": [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                ],
            },
            "wrong_pair_attachment": {
                "role": "tests object-pair identity and visible continuity",
                "required_margin_checks": [
                    "min_point_distance_m_ge_clear_far",
                    "near_contact_point_count_eq_zero",
                    "no_visible_connector_or_contiguity",
                ],
            },
            "floor_support_replacement_for_hanging": {
                "role": "tests support explanation that contradicts hanging",
                "required_margin_checks": [
                    "surface_type_contradicts_hanging",
                    "floor_or_table_supported",
                    "hanging_geometry_score_low",
                ],
            },
            "gravity_inconsistent_hanging": {
                "role": "tests hanging relations with no plausible gravity/support cue",
                "required_margin_checks": [
                    "floor_clearance_below_hanging_minimum",
                    "near_vertical_or_overhead_surface_false",
                ],
            },
            "shuffled_geometry_within_attachment_family": {
                "role": "future control; swap geometry among same-label rows after extraction",
                "required_margin_checks": ["identity_preserving_shuffle_key_recorded"],
            },
        },
        "promotion_rule": (
            "Negative seeds become calibration negatives only after the extractor "
            "confirms required margin checks; otherwise they remain uncertain/skip rows."
        ),
    }


def policy_smoke_plan(point_surface_dir: Path) -> dict[str, Any]:
    smoke_rows = count_smoke_rows(point_surface_dir / "rows.jsonl")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "smoke_input": {
            "point_surface_rows": "point_surface_validation/rows.jsonl",
            "counts": smoke_rows,
        },
        "required_steps": [
            "implement policy evaluator from verifier_policy/verifier_policy.json",
            "run evaluator on G1c 36-row smoke set without fitting calibration",
            "verify decision_schema compliance and reason-code coverage",
            "verify ambiguous functional subtypes remain uncertain unless clear geometry exists",
            "verify forbidden metric/calibration fields are absent from extractor outputs",
        ],
        "non_claim_boundary": [
            "G1c smoke rows are not train-dev calibration data",
            "G1c smoke rows are not held-out source metrics",
            "policy smoke cannot be reported as source performance",
        ],
    }


def gt_eval_inputs(
    repo_root: Path,
    out: Path,
    positive_summary: dict[str, Any],
    negative_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "input_files": {
            "positive_seeds": relpath(repo_root, out / "positive_seeds.jsonl"),
            "counterfactual_seeds": relpath(repo_root, out / "counterfactual_seeds.jsonl"),
        },
        "positive_summary": positive_summary,
        "counterfactual_summary": negative_summary,
        "required_gt_verifier_metrics": [
            "GT-positive nonviolated rate",
            "counterfactual negative nonsatisfied rate",
            "p_geom_valid AUROC",
            "p_geom_valid AUPRC",
            "p_geom_valid Brier",
            "uncertain rate by predicate label and subtype",
        ],
        "blocking_rule": (
            "Do not run VL-SAT/Open3DSG attachment source metrics until this "
            "GT-positive/counterfactual evaluation passes and thresholds are frozen."
        ),
    }


def threshold_freeze_protocol(repo_root: Path, policy_dir: Path, out: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "policy_source": relpath(repo_root, policy_dir / "verifier_policy.json"),
        "threshold_source": relpath(repo_root, policy_dir / "threshold_plan.json"),
        "frozen_before_source_metrics": [
            "predicate mapping for attached to / hanging on / connected to",
            "decision schema",
            "reason-code vocabulary",
            "clear negative geometry requirement for violated",
            "class affordance may not be used as proof",
            "near-contact threshold 0.05m",
            "uncertain contact band 0.05-0.15m",
            "clear-far distance 0.30m",
            "min near-contact points 3",
            "min contact patch score 0.20",
        ],
        "may_be_fit_only_on_train_dev": [
            "decision-to-probability calibration mapping",
            "family/subtype intercepts for p_geom_valid",
            "operating point for probabilistic vs rule-verified reporting",
        ],
        "forbidden_before_source_metrics": [
            "using VL-SAT/Open3DSG held-out attachment metrics to tune thresholds",
            "using visual failure cases from source metrics to change G2 policy without version bump",
            "collapsing exact predicate-label recall into family-level recall",
        ],
        "frozen_output_targets": {
            "manifest": relpath(repo_root, out / "manifest.json"),
            "positive_seeds": relpath(repo_root, out / "positive_seeds.jsonl"),
            "counterfactual_seeds": relpath(repo_root, out / "counterfactual_seeds.jsonl"),
        },
    }


def commands_md() -> str:
    return """# Attachment Deferred G3 Calibration / Counterfactual Route

This command prepares G3 planning artifacts. It does not fit a calibrator, apply
the verifier, score source predictions, or compute metrics.

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  attachment_deferred_calibration_counterfactuals
```

Validation:

```bash
python -m py_compile \\
  src/geocalib/prepare_attachment_calibration_counterfactuals.py
python -m json.tool \\
  archive/experiments/H001_geom_reliability/sources/attachment_deferred/calibration_counterfactuals/manifest.json >/dev/null
```
"""


def report_md(
    *,
    created_at: str,
    positive_summary: dict[str, Any],
    negative_summary: dict[str, Any],
    warnings: list[str],
    next_gate: str,
) -> str:
    warning_lines = "\n".join(f"- `{warning}`" for warning in warnings) or "- none"
    return f"""# Attachment Deferred G3 Calibration / Counterfactual Route

Status: `{STATUS}`
Created at: `{created_at}`

## Claim Boundary

This is a G3 route-freeze artifact. It prepares train-dev positive seeds,
counterfactual-negative seeds, policy-smoke routing, GT verifier-evaluation
inputs, and threshold-freeze protocol before any source metrics. It does not
apply the verifier policy, fit calibration, score VL-SAT/Open3DSG predictions,
or compute paper metrics.

## Positive Seeds

- rows: `{positive_summary['rows']}`
- by role: `{positive_summary['by_role']}`
- by label: `{positive_summary['by_label']}`
- by role/label: `{positive_summary['by_role_label']}`

## Counterfactual Seeds

- rows: `{negative_summary['rows']}`
- by role: `{negative_summary['by_role']}`
- by label: `{negative_summary['by_label']}`
- by strategy: `{negative_summary['by_strategy']}`

Counterfactual seeds require geometry-margin validation before becoming
calibration negatives. They are not absent-edge negatives.

## Warnings

{warning_lines}

## Next Gate

`{next_gate}`
"""


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    subset_json = (repo_root / args.subset_json).resolve() if not args.subset_json.is_absolute() else args.subset_json
    train_scans_path = (repo_root / args.train_scans).resolve() if not args.train_scans.is_absolute() else args.train_scans
    dev_scans_path = (repo_root / args.dev_scans).resolve() if not args.dev_scans.is_absolute() else args.dev_scans
    heldout_gt = (repo_root / args.heldout_gt_jsonl).resolve() if not args.heldout_gt_jsonl.is_absolute() else args.heldout_gt_jsonl
    policy_dir = (repo_root / args.verifier_policy_dir).resolve() if not args.verifier_policy_dir.is_absolute() else args.verifier_policy_dir
    point_surface_dir = (repo_root / args.point_surface_dir).resolve() if not args.point_surface_dir.is_absolute() else args.point_surface_dir
    out = (repo_root / args.out).resolve() if not args.out.is_absolute() else args.out
    ensure_dir(out)

    policy_manifest = read_json(policy_dir / "manifest.json")
    if policy_manifest.get("status") != "attachment_deferred_verifier_policy_ready_no_decisions_no_metrics":
        raise ValueError(f"unexpected_verifier_policy_status:{policy_manifest.get('status')}")

    train_scans = set(read_scan_list(train_scans_path))
    dev_scans = set(read_scan_list(dev_scans_path))
    heldout_scans = load_heldout_scans(heldout_gt)
    train_dev_scans = train_scans | dev_scans
    heldout_overlap = sorted(train_dev_scans & heldout_scans)
    if heldout_overlap:
        raise ValueError(f"train_dev_heldout_overlap:{heldout_overlap[:5]}")

    scans = load_relationship_scans(subset_json)
    positives, negatives, generation_summary = build_seeds(
        scans,
        train_scans,
        dev_scans,
        max_negatives_per_positive=args.max_negatives_per_positive,
    )
    positive_summary = summarize_rows(positives)
    negative_summary = summarize_negative_rows(negatives)

    warnings: list[str] = []
    if positive_summary["by_role_label"].get("dev:connected to", 0) == 0:
        warnings.append("dev_split_has_no_connected_to_positive_seed_use_pooled_or_augmented_dev_before_family_specific_connected_claim")
    if negative_summary["rows"] == 0:
        warnings.append("no_counterfactual_seeds_generated")
    if generation_summary["skipped_negative_generation"]:
        warnings.append(f"skipped_negative_generation:{generation_summary['skipped_negative_generation']}")

    write_jsonl(out / "positive_seeds.jsonl", positives)
    write_jsonl(out / "counterfactual_seeds.jsonl", negatives)

    split_plan = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "split_name": "attachment_deferred_train_dev",
        "train_scans": len(train_scans),
        "dev_scans": len(dev_scans),
        "heldout_overlap_scans": heldout_overlap,
        "leakage_group": "scan_id",
        "selected_scan_files": {
            "train": relpath(repo_root, train_scans_path),
            "dev": relpath(repo_root, dev_scans_path),
            "heldout_gt": relpath(repo_root, heldout_gt),
        },
        "positive_summary": positive_summary,
        "counterfactual_summary": negative_summary,
        "warnings": warnings,
    }
    write_json(out / "split_plan.json", split_plan)
    write_json(out / "counterfactual_plan.json", counterfactual_plan(args.max_negatives_per_positive))
    write_json(out / "policy_smoke_plan.json", policy_smoke_plan(point_surface_dir))
    write_json(out / "gt_eval_inputs.json", gt_eval_inputs(repo_root, out, positive_summary, negative_summary))
    write_json(out / "threshold_freeze_protocol.json", threshold_freeze_protocol(repo_root, policy_dir, out))

    created_at = utc_now()
    blockers = [
        "verifier_policy_not_applied_to_train_dev_rows",
        "calibrator_not_fit",
        "GT_verifier_evaluation_not_run",
        "source_metrics_not_run",
        "bootstrap_ci_not_run",
        "visual_audit_not_run",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "claim_boundary": {
            "artifact_type": "g3_route_freeze",
            "current_main_claim_unchanged": True,
            "decision_rows_emitted": False,
            "calibration_fitted": False,
            "source_predictions_scored": False,
            "metric_evidence": False,
        },
        "inputs": {
            "subset_json": relpath(repo_root, subset_json),
            "train_scans": relpath(repo_root, train_scans_path),
            "dev_scans": relpath(repo_root, dev_scans_path),
            "heldout_gt_jsonl": relpath(repo_root, heldout_gt),
            "verifier_policy_manifest": relpath(repo_root, policy_dir / "manifest.json"),
            "point_surface_rows": relpath(repo_root, point_surface_dir / "rows.jsonl"),
        },
        "outputs": {
            "positive_seeds": "positive_seeds.jsonl",
            "counterfactual_seeds": "counterfactual_seeds.jsonl",
            "split_plan": "split_plan.json",
            "counterfactual_plan": "counterfactual_plan.json",
            "policy_smoke_plan": "policy_smoke_plan.json",
            "gt_eval_inputs": "gt_eval_inputs.json",
            "threshold_freeze_protocol": "threshold_freeze_protocol.json",
            "commands": "commands.md",
            "report": "report.md",
        },
        "positive_summary": positive_summary,
        "counterfactual_summary": negative_summary,
        "generation_summary": generation_summary,
        "warnings": warnings,
        "blockers": blockers,
        "next_gate": NEXT_GATE,
    }
    write_json(out / "manifest.json", manifest)
    write_text(out / "commands.md", commands_md())
    write_text(
        out / "report.md",
        report_md(
            created_at=created_at,
            positive_summary=positive_summary,
            negative_summary=negative_summary,
            warnings=warnings,
            next_gate=NEXT_GATE,
        ),
    )

    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "positive_rows": positive_summary["rows"],
                "counterfactual_rows": negative_summary["rows"],
                "warnings": len(warnings),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
