#!/usr/bin/env python3
"""Write the H002 close-by target-plan contract before row materialization."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_target_plan"

EXPECTED_PREVIOUS_STATUS = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready"
EXPECTED_PREVIOUS_NEXT = "compatibility_dataset_v3_proximity_close_by_target_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_proximity_close_by_target_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_proximity_close_by_target_plan_ready_for_source_inventory"
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_target_plan_input_errors"
SELECTED_PATH = "plan_close_by_source_inventory_for_near_far_hard_negative_target"
NEXT_TODO = "compatibility_dataset_v3_proximity_close_by_source_inventory"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(capacity_summary: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity_summary.get("status") != EXPECTED_PREVIOUS_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity_summary.get("status")})
    if capacity_summary.get("next_todo") != EXPECTED_PREVIOUS_NEXT:
        errors.append({"error_type": "unexpected_capacity_next_todo", "actual": capacity_summary.get("next_todo")})
    if capacity_summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": capacity_summary.get("validation_errors")})
    boundary = capacity_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["summary.json", "predicate_capacity.csv"]:
        path = args.capacity_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_capacity_artifact", "path": rel_path(path)})
    match_rows = args.train_rga_dir / "match_rows.jsonl"
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def predicate_label(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_label")
    return row.get("predicate_label")


def nested_get(row: dict[str, Any], *keys: str) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def quantiles(values: list[float], qs: tuple[float, ...] = (0.1, 0.25, 0.5, 0.75, 0.9)) -> dict[str, float]:
    if not values:
        return {}
    values = sorted(values)
    out: dict[str, float] = {}
    last = len(values) - 1
    for q in qs:
        out[f"q{int(q * 100):02d}"] = round(values[int(round(q * last))], 6)
    return out


def flatten_counter(counter: Counter[Any], limit: int = 10) -> str:
    return "; ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def scan_close_by(match_rows_path: Path) -> dict[str, Any]:
    counters: dict[str, Counter[Any]] = {
        "label_match_status": Counter(),
        "geometry_status": Counter(),
        "rank_band": Counter(),
        "raw_feature_keys": Counter(),
    }
    values_by_axis: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    examples: list[dict[str, Any]] = []
    total = 0
    for line in match_rows_path.open("r", encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        if predicate_label(row) != "close by":
            continue
        total += 1
        label_status = nested_get(row, "label", "label_match_status")
        geometry_status = nested_get(row, "geometry", "geometry_status")
        rank_band = nested_get(row, "rga", "rank_band")
        counters["label_match_status"][label_status] += 1
        counters["geometry_status"][geometry_status] += 1
        counters["rank_band"][rank_band] += 1
        raw_features = nested_get(row, "geometry", "raw_features") or {}
        if isinstance(raw_features, dict):
            for key, value in raw_features.items():
                counters["raw_feature_keys"][key] += 1
                if key in {
                    "distance_3d",
                    "distance_xy",
                    "normalized_distance_3d",
                    "normalized_distance_xy",
                    "projected_iou_xy",
                    "projected_subject_overlap_ratio",
                    "projected_object_overlap_ratio",
                }:
                    try:
                        numeric = float(value)
                    except (TypeError, ValueError):
                        continue
                    values_by_axis[f"feature:{key}"]["all"].append(numeric)
                    values_by_axis[f"feature:{key}"][f"label:{label_status}"].append(numeric)
                    values_by_axis[f"feature:{key}"][f"geometry:{geometry_status}"].append(numeric)
        if len(examples) < 5:
            examples.append(
                {
                    "prediction_id": nested_get(row, "identity", "prediction_id"),
                    "label_match_status": label_status,
                    "geometry_status": geometry_status,
                    "rank_band": rank_band,
                    "p_geom_valid": nested_get(row, "geometry", "p_geom_valid"),
                    "raw_feature_keys": sorted(raw_features) if isinstance(raw_features, dict) else [],
                }
            )
    quantile_rows: list[dict[str, Any]] = []
    for feature, axis_values in sorted(values_by_axis.items()):
        for axis, values in sorted(axis_values.items()):
            row = {"feature": feature.replace("feature:", ""), "axis": axis, "count": len(values)}
            row.update(quantiles(values))
            quantile_rows.append(row)
    return {
        "total_rows": total,
        "label_match_status_counts": flatten_counter(counters["label_match_status"]),
        "geometry_status_counts": flatten_counter(counters["geometry_status"]),
        "rank_band_counts": flatten_counter(counters["rank_band"]),
        "raw_feature_key_counts": flatten_counter(counters["raw_feature_keys"], limit=20),
        "quantile_rows": quantile_rows,
        "examples": examples,
    }


def find_close_by_capacity(predicate_capacity: list[dict[str, str]]) -> dict[str, str]:
    for row in predicate_capacity:
        if row.get("predicate_label") == "close by":
            return row
    return {}


def build_target_contract(close_by_capacity: dict[str, Any], full_scan: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_predicate": "close by",
        "relation_family": "proximity",
        "purpose": (
            "Build a train-only proximity target that tests predicate-geometry compatibility, "
            "not a no-GT-vs-GT shortcut and not a plain distance threshold."
        ),
        "current_capacity_snapshot": close_by_capacity,
        "full_match_rows_snapshot": {
            "total_rows": full_scan["total_rows"],
            "label_match_status_counts": full_scan["label_match_status_counts"],
            "geometry_status_counts": full_scan["geometry_status_counts"],
            "rank_band_counts": full_scan["rank_band_counts"],
            "raw_feature_key_counts": full_scan["raw_feature_key_counts"],
        },
        "factor_boundary": {
            "T_e": "predicate text/label, proximity family, subject/object class semantics; no source score or rank",
            "Z_e": "source score/rank/source-id only; allowed in final reliability baselines, blocked from C_e",
            "G_e": "predicate-independent geometry vector or tokens from distance, scale, overlap, and pair geometry",
            "C_e": "compatibility(T_e, G_e); must not read Z_e, GT-match status, queue label, or p_geom_valid target",
            "Q_e": "geometry coverage, degeneracy, missingness, large-object ambiguity, dense-scene uncertainty",
            "p_obs": "whether evidence is sufficient to decide close-by reliability",
            "p_rel": "whether the relation is reliable conditioned on p_obs being high",
        },
        "hard_rules": [
            "Do not use no_gt_for_pair as an automatic reject label.",
            "Do not use pair_has_other_predicate as an automatic reject label.",
            "Do not use HL/LH membership as a target label.",
            "Do not use p_geom_valid as the main target; it is a baseline or teacher candidate only.",
            "Do not use validation/test rows in hypothesis target construction.",
            "C_e must exclude source score, source rank, and source id.",
        ],
        "positive_definition": [
            "GT exact close-by relation with near-distance evidence and adequate geometry coverage.",
            "Human/audit-confirmed close-by relation from visual/mesh/context review, if later used.",
            "Near relation must be assessed with object scale, object extent, and scene context rather than raw distance alone.",
        ],
        "negative_definition": [
            "Far-distance or non-proximity pair confirmed by geometry and/or visual evidence.",
            "Hard negative should match predicate, source/rank band, class-pair when possible, and coverage quality.",
            "Near but no-GT pairs are not negative unless audit or distance/scale policy confirms non-proximity.",
        ],
        "abstain_definition": [
            "No-GT but near-geometry pair where annotation sparsity is plausible.",
            "Very large objects, room-scale entities, or dense clutter where close-by is ill-defined.",
            "Missing, degenerate, or low-coverage geometry.",
            "Conflicting geometry/view evidence.",
        ],
        "promotion_gate": {
            "source_inventory_required": True,
            "minimum_binary_rows": 400,
            "minimum_accept": 160,
            "minimum_reject": 160,
            "minimum_abstain_for_p_obs": 80,
            "required_controls": [
                "distance_only",
                "class_pair_only",
                "source_only",
                "source_rank_only",
                "shuffled_geometry",
                "wrong_pair_geometry",
                "same_distance_matched_subset",
            ],
            "must_beat": [
                "source_only on grouped scan split",
                "class_pair_only shortcut probe",
                "distance_only on same-distance matched subset",
            ],
        },
    }


def build_evidence_schema() -> list[dict[str, Any]]:
    return [
        {"factor": "T_e", "field": "predicate_text=close by", "role": "semantic claim", "allowed_for_C_e": "yes", "notes": "source score/rank excluded"},
        {"factor": "T_e", "field": "subject_class_text/object_class_text", "role": "object semantic context", "allowed_for_C_e": "yes", "notes": "must be audited by class-pair shortcut controls"},
        {"factor": "Z_e", "field": "source_score", "role": "relation-source confidence", "allowed_for_C_e": "no", "notes": "allowed in final reliability baselines only"},
        {"factor": "Z_e", "field": "rank_band/source_id", "role": "source provenance", "allowed_for_C_e": "no", "notes": "blocked from compatibility target and hidden from audit label construction"},
        {"factor": "G_e", "field": "distance_3d/distance_xy", "role": "raw pair separation", "allowed_for_C_e": "yes", "notes": "must be controlled by distance-only baseline"},
        {"factor": "G_e", "field": "normalized_distance_3d/normalized_distance_xy", "role": "scale-aware separation", "allowed_for_C_e": "yes", "notes": "primary proximity evidence candidate"},
        {"factor": "G_e", "field": "projected_iou_xy/overlap_ratios", "role": "spatial adjacency/overlap", "allowed_for_C_e": "yes", "notes": "helps distinguish adjacency from far pairs"},
        {"factor": "G_e", "field": "object extents/size ratio", "role": "close-by scale context", "allowed_for_C_e": "yes", "notes": "source inventory must derive or confirm availability"},
        {"factor": "G_e", "field": "p_geom_valid", "role": "rule-based baseline or teacher", "allowed_for_C_e": "baseline_only", "notes": "not a target label and not a main learned input by default"},
        {"factor": "Q_e", "field": "geometry_available/degenerate_size/missing_features", "role": "observability quality", "allowed_for_C_e": "no", "notes": "feeds p_obs or abstain head"},
        {"factor": "Q_e", "field": "large_object_or_room_like_pair", "role": "semantic ambiguity quality", "allowed_for_C_e": "no", "notes": "abstain candidate, not accept/reject evidence"},
    ]


def build_label_policy() -> list[dict[str, Any]]:
    return [
        {
            "target_axis": "C_e/p_rel",
            "label": "accept",
            "definition": "The object pair is close by under scale-aware geometry and context.",
            "candidate_source": "exact_match close-by plus near geometry; later human/audit confirmation if used",
            "blocked_shortcut": "not merely high source score or high rank",
        },
        {
            "target_axis": "C_e/p_rel",
            "label": "reject",
            "definition": "The object pair is not close by under scale-aware geometry and context.",
            "candidate_source": "far or non-proximity pair from full train relation universe",
            "blocked_shortcut": "not merely no_gt_for_pair or pair_has_other_predicate",
        },
        {
            "target_axis": "Q_e/p_obs",
            "label": "abstain",
            "definition": "Evidence is insufficient or the close-by relation is semantically/visually ambiguous.",
            "candidate_source": "near no-GT rows, large-object rows, low-coverage rows, or conflicting evidence rows",
            "blocked_shortcut": "not a hidden negative class",
        },
    ]


def build_quota_plan() -> list[dict[str, Any]]:
    return [
        {"stage": "source_inventory", "split": "train_only", "target_rows": 0, "accept": 0, "reject": 0, "abstain": 0, "purpose": "measure near/far capacity and available evidence before materialization"},
        {"stage": "candidate_materialization_minimum", "split": "train_only", "target_rows": 400, "accept": 160, "reject": 160, "abstain": 80, "purpose": "minimum viable close-by audit/model target"},
        {"stage": "candidate_materialization_preferred", "split": "train_only", "target_rows": 720, "accept": 240, "reject": 240, "abstain": 240, "purpose": "balanced p_rel plus p_obs/abstain target if inventory supports it"},
        {"stage": "diagnostic_fallback", "split": "train_only", "target_rows": 240, "accept": 80, "reject": 80, "abstain": 80, "purpose": "diagnostic-only if hard negatives or abstains are sparse"},
    ]


def build_hard_negative_policy() -> list[dict[str, Any]]:
    return [
        {"negative_type": "far_same_predicate", "definition": "close-by candidate whose pair geometry is scale-normalized far", "control": "match class pair/rank/source band when possible"},
        {"negative_type": "same_class_pair_far", "definition": "same subject/object class pair as positive anchor but far in metric space", "control": "prevents class-pair-only target"},
        {"negative_type": "same_distance_nonclose_context", "definition": "similar raw distance but context/object scale makes close-by unsupported", "control": "tests beyond raw distance threshold"},
        {"negative_type": "wrong_pair_geometry", "definition": "semantic relation paired with another object-pair geometry", "control": "tests whether model uses the actual pair geometry"},
        {"negative_type": "shuffled_geometry", "definition": "geometry vectors shuffled across rows within predicate/family", "control": "must collapse near chance"},
    ]


def build_shortcut_gates() -> list[dict[str, Any]]:
    return [
        {"gate": "no_gt_not_negative", "requirement": "no_gt_for_pair cannot define reject", "pass_condition": "label policy has independent near/far/audit rule"},
        {"gate": "pair_has_other_not_negative", "requirement": "pair_has_other_predicate cannot define reject", "pass_condition": "other-predicate rows are audit/abstain unless geometry confirms reject"},
        {"gate": "class_pair_balance", "requirement": "accept/reject within class-pair or matched class-pair blocks", "pass_condition": "class-pair majority accuracy <= 0.65 or diagnostic-only"},
        {"gate": "rank_source_balance", "requirement": "accept/reject across source/rank bands", "pass_condition": "source/rank-only AUROC close to chance or below compatibility model"},
        {"gate": "distance_only_control", "requirement": "raw/normalized distance is a baseline, not the claim", "pass_condition": "compatibility model improves on distance-only under matched-distance subset"},
        {"gate": "geometry_shuffle_control", "requirement": "model must use paired geometry", "pass_condition": "shuffled-G and wrong-pair-G controls degrade substantially"},
        {"gate": "coverage_abstain_separation", "requirement": "Q_e governs abstain, not accept/reject truth", "pass_condition": "low Q_e routes to abstain without directly becoming reject"},
    ]


def build_baseline_controls() -> list[dict[str, Any]]:
    return [
        {"baseline": "semantic_only_T", "features": "predicate/object class text only", "purpose": "checks whether semantics alone solves target"},
        {"baseline": "source_only_Z", "features": "source score/rank/source id", "purpose": "checks source confidence shortcut"},
        {"baseline": "geometry_only_G", "features": "distance/scale/overlap vector", "purpose": "checks whether proximity is just a geometry threshold"},
        {"baseline": "distance_only", "features": "distance_3d/distance_xy/normalized distances", "purpose": "mandatory close-by control"},
        {"baseline": "T_plus_G_compatibility", "features": "T_e and G_e interaction without Z_e", "purpose": "main C_e claim"},
        {"baseline": "Z_plus_C_plus_Q_decision", "features": "source confidence plus compatibility plus observability", "purpose": "later p_rel/p_obs decision candidate"},
        {"baseline": "p_geom_valid_rule", "features": "existing rule-based p_geom_valid", "purpose": "H001-style geometry baseline or teacher, not main target"},
    ]


def build_source_inventory_contract(full_scan: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "input_rows": "train-only Open3DSG full match_rows close-by rows and pair universe",
        "observed_full_close_by_rows": full_scan["total_rows"],
        "required_outputs": [
            "near/far/ambiguous bucket counts by normalized distance and object scale",
            "exact-match positive-anchor inventory",
            "far hard-negative inventory not derived from no-GT status alone",
            "same-class-pair and same-rank-band mixed-capacity table",
            "feature availability table for G_e and Q_e",
            "candidate materialization route decision",
        ],
        "do_not_materialize_yet": True,
        "support_contact_after_close_by": [
            "standing on individual predicate probe",
            "lying on individual predicate probe",
            "supported by individual predicate probe",
        ],
    }


def build_report(summary: dict[str, Any], contract: dict[str, Any], full_scan: dict[str, Any]) -> str:
    return f"""# H002 Proximity Close-By Target Plan

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Decision

Proceed with `close by` first, but only as a controlled proximity target plan.
The next step is not learned smoke. It is a source inventory that checks whether
we can build near/far/abstain rows without turning `no_gt_for_pair` into a fake
negative label.

Support/contact is deferred to individual predicate probes after this path:

```text
standing on
lying on
supported by
```

## Why This Plan Is Needed

The previous capacity scan saw only the HL/LH queues:

```text
queue close-by rows = {contract["current_capacity_snapshot"].get("queue_rows")}
HL rows = {contract["current_capacity_snapshot"].get("hl_rows")}
LH rows = {contract["current_capacity_snapshot"].get("lh_rows")}
```

The full train match rows show a wider geometry-status distribution:

```text
full close-by rows = {full_scan["total_rows"]}
label status = {full_scan["label_match_status_counts"]}
geometry status = {full_scan["geometry_status_counts"]}
rank bands = {full_scan["rank_band_counts"]}
```

This means `close by` has enough row mass, but the target must be designed
carefully. `exact_match` rows are candidate positives. `no_gt_for_pair` and
`pair_has_other_predicate` are not candidate negatives by themselves because 3DSSG
annotations are incomplete and dense proximity relations can be missing from GT.

## Target Contract

```text
T_e = predicate/object semantic content
Z_e = source score/rank/source provenance
G_e = predicate-independent proximity geometry
C_e = compatibility(T_e, G_e), excluding Z_e
Q_e = geometry/evidence quality and ambiguity
p_obs = can this edge be judged?
p_rel = is the edge reliable when observable?
```

Hard rules:

- Do not use `no_gt_for_pair` as automatic reject.
- Do not use `pair_has_other_predicate` as automatic reject.
- Do not use `HL/LH` queue membership as a target label.
- Do not use `p_geom_valid` as the main label; keep it as a rule baseline or teacher candidate.
- Do not use validation/test rows.
- Do not allow `Z_e` inside `C_e`.

## Next Source Inventory

The source inventory must determine whether we can form:

- GT/exact or audit-confirmed near positives.
- Scale-aware far negatives.
- Ambiguous rows for `Q_e` and `p_obs`.
- Same-class-pair, same-rank-band, and same-distance controls.

If this inventory cannot produce controlled accept/reject/abstain rows, `close by`
stays diagnostic rather than becoming a main H002 result.
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    capacity_summary_path = args.capacity_dir / "summary.json"
    capacity_summary = read_json(capacity_summary_path) if capacity_summary_path.exists() else {}
    validation_errors = validate_inputs(capacity_summary, args)

    predicate_capacity_path = args.capacity_dir / "predicate_capacity.csv"
    predicate_capacity = read_csv(predicate_capacity_path) if predicate_capacity_path.exists() else []
    close_by_capacity = find_close_by_capacity(predicate_capacity)

    full_scan = scan_close_by(args.train_rga_dir / "match_rows.jsonl") if not validation_errors else {
        "total_rows": 0,
        "label_match_status_counts": "",
        "geometry_status_counts": "",
        "rank_band_counts": "",
        "raw_feature_key_counts": "",
        "quantile_rows": [],
        "examples": [],
    }

    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_input_errors",
        "next_todo": NEXT_TODO if not validation_errors else "fix_input_errors",
        "validation_errors": len(validation_errors),
        "input_capacity_summary": rel_path(capacity_summary_path),
        "boundary": {
            "split": "train_only_target_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "close_by_full_snapshot": {
            "total_rows": full_scan["total_rows"],
            "label_match_status_counts": full_scan["label_match_status_counts"],
            "geometry_status_counts": full_scan["geometry_status_counts"],
            "rank_band_counts": full_scan["rank_band_counts"],
            "raw_feature_key_counts": full_scan["raw_feature_key_counts"],
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "target_contract": rel_path(args.output_dir / "target_contract.json"),
            "evidence_schema": rel_path(args.output_dir / "evidence_schema.csv"),
            "label_policy": rel_path(args.output_dir / "label_policy.csv"),
            "quota_plan": rel_path(args.output_dir / "quota_plan.csv"),
            "hard_negative_policy": rel_path(args.output_dir / "hard_negative_policy.csv"),
            "shortcut_gates": rel_path(args.output_dir / "shortcut_gates.csv"),
            "baseline_controls": rel_path(args.output_dir / "baseline_controls.csv"),
            "source_inventory_contract": rel_path(args.output_dir / "source_inventory_contract.json"),
            "close_by_distance_quantiles": rel_path(args.output_dir / "close_by_distance_quantiles.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    contract = build_target_contract(close_by_capacity, full_scan)
    source_inventory_contract = build_source_inventory_contract(full_scan)
    route_decision = [
        {
            "decision": SELECTED_PATH if not validation_errors else "blocked_input_errors",
            "reason": (
                "close by has high row mass and full match rows include satisfied/uncertain/unsatisfied geometry, "
                "but the target must mine controlled near/far evidence instead of no-GT negatives"
            ),
            "next_todo": summary["next_todo"],
            "support_contact_plan": "defer grouped support/contact; run standing_on/lying_on/supported_by individual predicate probes after close-by inventory",
        }
    ]

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "target_contract.json", contract)
    write_json(args.output_dir / "source_inventory_contract.json", source_inventory_contract)
    write_json(args.output_dir / "example_rows.json", full_scan["examples"])
    write_csv(args.output_dir / "evidence_schema.csv", build_evidence_schema())
    write_csv(args.output_dir / "label_policy.csv", build_label_policy())
    write_csv(args.output_dir / "quota_plan.csv", build_quota_plan())
    write_csv(args.output_dir / "hard_negative_policy.csv", build_hard_negative_policy())
    write_csv(args.output_dir / "shortcut_gates.csv", build_shortcut_gates())
    write_csv(args.output_dir / "baseline_controls.csv", build_baseline_controls())
    write_csv(args.output_dir / "close_by_distance_quantiles.csv", full_scan["quantile_rows"])
    write_csv(args.output_dir / "route_decision.csv", route_decision)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, contract, full_scan), encoding="utf-8")


if __name__ == "__main__":
    main()
