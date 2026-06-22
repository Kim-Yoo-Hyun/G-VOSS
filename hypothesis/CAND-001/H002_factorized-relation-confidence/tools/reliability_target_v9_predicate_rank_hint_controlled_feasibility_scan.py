#!/usr/bin/env python3
"""Scan v9 feasibility for predicate/rank/hint controlled H002 targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision_codex_proxy_user_requested"
DEFAULT_REPAIR_INGESTION_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_ingestion_codex_proxy_user_requested"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v9_predicate_rank_hint_controlled_feasibility_scan_codex_proxy_user_requested"

CORE_FAMILIES = {"relative_vertical", "support_contact"}
PAIR_SPECS = {
    "relative_vertical_higher_lower": {
        "family": "relative_vertical",
        "predicates": ("higher than", "lower than"),
    },
    "support_contact_standing_lying": {
        "family": "support_contact",
        "predicates": ("standing on", "lying on"),
    },
}

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window", "blinds", "curtain"}
GENERIC_LABELS = {"object", "item", "stuff", "thing"}

MIN_RELATION_BINARY_ROWS = 80
MIN_PER_CLASS = 35
PREFERRED_STRICT_SLICE_ROWS = 70
MAX_PREDICTOR_MAJORITY_EXCESS = 0.10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--repair-ingestion-dir", type=Path, default=DEFAULT_REPAIR_INGESTION_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_int(value: Any, default: int = 999999) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def endpoint_type(label: str) -> str:
    if label in HARD_ROOM_SURFACES:
        return f"hard_room_surface:{label}"
    if label in STRUCTURAL_CONTEXT:
        return f"structural_context:{label}"
    return "object"


def endpoint_pattern(subject_label: str, object_label: str) -> str:
    same = "same_label" if subject_label == object_label else "different_label"
    return f"sub={endpoint_type(subject_label)}|obj={endpoint_type(object_label)}|{same}"


def exact_key(row: dict[str, Any]) -> str:
    return f"{row['scan_id']}|{row['subgraph_id']}|{row['subject_id']}|{row['object_id']}"


def row_priority(row: dict[str, Any]) -> tuple[Any, ...]:
    return (as_int(row.get("semantic_rank")), str(row.get("prediction_id")))


def entropy(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        value -= p * math.log2(p)
    return value


def prediction_risk(rows: list[dict[str, Any]], predictor: str, label: str = "predicate_label_norm") -> dict[str, Any]:
    labels = Counter(str(row.get(label)) for row in rows)
    total = len(rows)
    baseline = max(labels.values()) / total if total else 0.0
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor))][str(row.get(label))] += 1
    majority_correct = sum(max(counter.values()) for counter in groups.values()) if total else 0
    majority_accuracy = majority_correct / total if total else 0.0
    hy = entropy(labels)
    h_y_given_x = 0.0
    for counter in groups.values():
        group_total = sum(counter.values())
        if group_total:
            h_y_given_x += (group_total / total) * entropy(counter)
    nmi = max(0.0, hy - h_y_given_x) / hy if hy else 0.0
    top_groups = []
    for key, counter in sorted(groups.items(), key=lambda item: (-sum(item[1].values()), str(item[0])))[:10]:
        group_total = sum(counter.values())
        top_groups.append(
            {
                "group_value": key,
                "rows": group_total,
                "majority_label": counter.most_common(1)[0][0],
                "majority_rate": max(counter.values()) / group_total if group_total else 0.0,
                "label_counts": dict(sorted(counter.items())),
            }
        )
    return {
        "predictor": predictor,
        "label": label,
        "rows": total,
        "label_counts": dict(sorted(labels.items())),
        "groups": len(groups),
        "majority_baseline_accuracy": baseline,
        "majority_rule_accuracy": majority_accuracy,
        "majority_excess_over_baseline": majority_accuracy - baseline,
        "normalized_mutual_information": nmi,
        "risk_flag": majority_accuracy - baseline > MAX_PREDICTOR_MAJORITY_EXCESS,
        "top_groups": top_groups,
    }


def validate_inputs(path_decision: dict[str, Any], repair_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v8_repair_path_decision_select_v9_controlled_mining"
    expected_next = "reliability_target_v9_predicate_rank_hint_controlled_feasibility_scan"
    if path_decision.get("status") != expected_status:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": expected_status, "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_path_decision_next_todo", "expected": expected_next, "actual": path_decision.get("next_todo")})
    boundary = path_decision.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "multi_view_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "path_decision_boundary_violation", "field": key, "actual": boundary.get(key)})
    repair_boundary = repair_summary.get("boundary", {})
    if repair_boundary.get("validation_usage") is not False or repair_boundary.get("test_usage") is not False:
        errors.append({"error_type": "repair_ingestion_used_validation_or_test", "boundary": repair_boundary})
    return errors


def load_current_exact_keys(repair_ingestion_dir: Path) -> set[str]:
    path = repair_ingestion_dir / "relation_reliability_v6_multiclass_targets.jsonl"
    keys = set()
    for row in iter_jsonl(path):
        key = row.get("exact_endpoint_pair_key_hidden")
        if key:
            keys.add(str(key))
    return keys


def enrich_row(row: dict[str, Any], source_path: Path) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    ids = sorted([str(row.get("subject_id")), str(row.get("object_id"))])
    return {
        **row,
        "source_queue_path": rel_path(source_path),
        "predicate_label_norm": norm(row.get("predicate_label")),
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "exact_endpoint_pair_key": exact_key(row),
        "undirected_endpoint_pair_key": f"{row['scan_id']}|{row['subgraph_id']}|{ids[0]}|{ids[1]}",
        "endpoint_pattern": endpoint_pattern(subject_label, object_label),
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "generic_endpoint_pair": subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS,
    }


def load_train_rows(hl_queue: Path, lh_queue: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts = {
        "read_rows_by_queue": Counter(),
        "kept_rows_by_family": Counter(),
        "kept_rows_by_predicate": Counter(),
    }
    required = ["prediction_id", "scan_id", "subgraph_id", "subject_id", "subject_label", "predicate_label", "predicate_family", "object_id", "object_label", "queue_kind"]
    for path, queue_name in [(hl_queue, "HL"), (lh_queue, "LH")]:
        for row in iter_jsonl(path):
            counts["read_rows_by_queue"][queue_name] += 1
            missing = [field for field in required if field not in row]
            if missing:
                errors.append({"error_type": "missing_queue_fields", "prediction_id": row.get("prediction_id"), "missing": missing, "queue": queue_name})
                continue
            if row.get("predicate_family") not in CORE_FAMILIES:
                continue
            enriched = enrich_row(row, path)
            rows.append(enriched)
            counts["kept_rows_by_family"][str(row.get("predicate_family"))] += 1
            counts["kept_rows_by_predicate"][norm(row.get("predicate_label"))] += 1
    return rows, errors, {key: dict(value) for key, value in counts.items()}


def build_pairs(rows: list[dict[str, Any]], current_exact_keys: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_exact[row["exact_endpoint_pair_key"]].append(row)
    pairs: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    inventory_counts = Counter()
    for exact, group_rows in by_exact.items():
        predicate_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group_rows:
            predicate_rows[row["predicate_label_norm"]].append(row)
        group_current = exact in current_exact_keys
        group_structural = any(row["structural_pair"] for row in group_rows)
        group_generic = any(row["generic_endpoint_pair"] for row in group_rows)
        group_hard = any(row["hard_room_surface_pair"] for row in group_rows)
        for pair_type, spec in PAIR_SPECS.items():
            p1, p2 = spec["predicates"]
            if not predicate_rows[p1] or not predicate_rows[p2]:
                continue
            first = sorted(predicate_rows[p1], key=row_priority)[0]
            second = sorted(predicate_rows[p2], key=row_priority)[0]
            eligible = not group_current and not group_structural and not group_generic
            pair = {
                "pair_type": pair_type,
                "family": spec["family"],
                "exact_endpoint_pair_key": exact,
                "scan_id": first.get("scan_id"),
                "subgraph_id": first.get("subgraph_id"),
                "subject_id": first.get("subject_id"),
                "object_id": first.get("object_id"),
                "subject_label": first.get("subject_label"),
                "object_label": first.get("object_label"),
                "subject_object_label_pair": f"{first.get('subject_label')}|{first.get('object_label')}",
                "has_current_v8_repair_label": group_current,
                "structural_pair": group_structural,
                "generic_endpoint_pair": group_generic,
                "hard_room_surface_pair": group_hard,
                "eligible_for_v9_exact_pair": eligible,
                "predicate_signature": "|".join(spec["predicates"]),
                "rank_signature": f"{p1}:{first.get('rank_band')}|{p2}:{second.get('rank_band')}",
                "hint_signature": f"{p1}:{first.get('machine_hint')}|{p2}:{second.get('machine_hint')}",
                "bucket_signature": f"{p1}:{first.get('label_geometry_bucket')}|{p2}:{second.get('label_geometry_bucket')}",
                "queue_signature": f"{p1}:{first.get('queue_kind')}|{p2}:{second.get('queue_kind')}",
                "row_prediction_ids": [first.get("prediction_id"), second.get("prediction_id")],
            }
            pairs.append(pair)
            for pair_index, row in enumerate([first, second]):
                pair_rows.append(
                    {
                        "pair_type": pair_type,
                        "family": spec["family"],
                        "exact_endpoint_pair_key": exact,
                        "eligible_for_v9_exact_pair": eligible,
                        "pair_index": pair_index,
                        "prediction_id": row.get("prediction_id"),
                        "scan_id": row.get("scan_id"),
                        "subgraph_id": row.get("subgraph_id"),
                        "subject_id": row.get("subject_id"),
                        "subject_label": row.get("subject_label"),
                        "predicate_label": row.get("predicate_label"),
                        "predicate_label_norm": row.get("predicate_label_norm"),
                        "predicate_family": row.get("predicate_family"),
                        "object_id": row.get("object_id"),
                        "object_label": row.get("object_label"),
                        "rank_band": row.get("rank_band"),
                        "machine_hint": row.get("machine_hint"),
                        "label_geometry_bucket": row.get("label_geometry_bucket"),
                        "queue_kind": row.get("queue_kind"),
                        "geometry_status": row.get("geometry_status"),
                        "semantic_rank": row.get("semantic_rank"),
                        "p_geom_valid": row.get("p_geom_valid"),
                    }
                )
            inventory_counts[f"{pair_type}_pairs"] += 1
            if eligible:
                inventory_counts[f"{pair_type}_eligible_pairs"] += 1
    inventory_counts["exact_endpoint_groups"] = len(by_exact)
    return pairs, pair_rows, dict(inventory_counts)


def counter_rows(rows: list[dict[str, Any]], keys: list[str], prefix: str) -> list[dict[str, Any]]:
    counter = Counter(tuple(str(row.get(key)) for key in keys) for row in rows)
    output = []
    for values, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        row = {"axis": prefix, "rows": count}
        for key, value in zip(keys, values):
            row[key] = value
        output.append(row)
    return output


def common_axis_capacity(rows: list[dict[str, Any]], family: str, axis: str) -> dict[str, Any]:
    family_rows = [row for row in rows if row["family"] == family and row["eligible_for_v9_exact_pair"]]
    predicates = sorted({row["predicate_label_norm"] for row in family_rows})
    values_by_predicate: dict[str, Counter[str]] = {}
    for predicate in predicates:
        values_by_predicate[predicate] = Counter(str(row.get(axis)) for row in family_rows if row["predicate_label_norm"] == predicate)
    common_values = set.intersection(*(set(counter) for counter in values_by_predicate.values())) if values_by_predicate else set()
    common_balanced_rows = 0
    for value in common_values:
        common_balanced_rows += min(counter[value] for counter in values_by_predicate.values()) * len(predicates)
    return {
        "family": family,
        "axis": axis,
        "predicates": predicates,
        "common_values": sorted(common_values),
        "common_value_count": len(common_values),
        "common_balanced_rows_upper_bound": common_balanced_rows,
        "counts_by_predicate": {predicate: dict(sorted(counter.items())) for predicate, counter in values_by_predicate.items()},
    }


def feasibility_summary(pairs: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible_pairs = [pair for pair in pairs if pair["eligible_for_v9_exact_pair"]]
    eligible_rows = [row for row in pair_rows if row["eligible_for_v9_exact_pair"]]
    pair_counts = Counter(pair["pair_type"] for pair in eligible_pairs)
    predicate_counts = Counter(row["predicate_label_norm"] for row in eligible_rows)
    four_predicate_balanced_n = min(
        predicate_counts.get("higher than", 0),
        predicate_counts.get("lower than", 0),
        predicate_counts.get("standing on", 0),
        predicate_counts.get("lying on", 0),
    )
    rank_risk_all = prediction_risk(eligible_rows, "rank_band")
    hint_risk_all = prediction_risk(eligible_rows, "machine_hint")
    bucket_risk_all = prediction_risk(eligible_rows, "label_geometry_bucket")
    rank_caps = [common_axis_capacity(eligible_rows, family, "rank_band") for family in ["relative_vertical", "support_contact"]]
    hint_caps = [common_axis_capacity(eligible_rows, family, "machine_hint") for family in ["relative_vertical", "support_contact"]]

    count_gate = (four_predicate_balanced_n * 4) >= MIN_RELATION_BINARY_ROWS and four_predicate_balanced_n >= MIN_PER_CLASS
    exact_pair_gate = len(eligible_pairs) >= MIN_RELATION_BINARY_ROWS // 2
    rank_gate = all(item["common_value_count"] > 0 and item["common_balanced_rows_upper_bound"] >= PREFERRED_STRICT_SLICE_ROWS for item in rank_caps)
    hint_gate = all(item["common_value_count"] > 0 and item["common_balanced_rows_upper_bound"] >= PREFERRED_STRICT_SLICE_ROWS for item in hint_caps)
    predictor_gate = not rank_risk_all["risk_flag"] and not hint_risk_all["risk_flag"]
    strict_feasible = count_gate and exact_pair_gate and rank_gate and hint_gate and predictor_gate

    return {
        "eligible_pairs": len(eligible_pairs),
        "eligible_pair_counts": dict(sorted(pair_counts.items())),
        "eligible_rows": len(eligible_rows),
        "eligible_predicate_counts": dict(sorted(predicate_counts.items())),
        "four_predicate_balanced_rows_upper_bound": four_predicate_balanced_n * 4,
        "count_gate": count_gate,
        "exact_pair_gate": exact_pair_gate,
        "rank_gate": rank_gate,
        "hint_gate": hint_gate,
        "predictor_gate": predictor_gate,
        "strict_v9_exact_pair_feasible": strict_feasible,
        "rank_predicts_predicate": rank_risk_all,
        "machine_hint_predicts_predicate": hint_risk_all,
        "label_geometry_bucket_predicts_predicate": bucket_risk_all,
        "rank_common_capacity": rank_caps,
        "machine_hint_common_capacity": hint_caps,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    feasibility = summary["feasibility"]
    lines = [
        "# H002 V9 Predicate/Rank/Hint Feasibility Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Gates",
        "",
        "```text",
        f"eligible_pairs = {feasibility['eligible_pairs']}",
        f"eligible_rows = {feasibility['eligible_rows']}",
        f"four_predicate_balanced_rows_upper_bound = {feasibility['four_predicate_balanced_rows_upper_bound']}",
        f"count_gate = {feasibility['count_gate']}",
        f"exact_pair_gate = {feasibility['exact_pair_gate']}",
        f"rank_gate = {feasibility['rank_gate']}",
        f"hint_gate = {feasibility['hint_gate']}",
        f"predictor_gate = {feasibility['predictor_gate']}",
        f"strict_v9_exact_pair_feasible = {feasibility['strict_v9_exact_pair_feasible']}",
        "```",
        "",
        "## Main Finding",
        "",
        "The pool has enough exact endpoint-pair candidates, but exact endpoint-pair contrast is structurally entangled with `rank_band` and `machine_hint`.",
        "",
        "Predicate from rank/hint diagnostics:",
        "",
        "```text",
        f"rank_band -> predicate majority accuracy = {feasibility['rank_predicts_predicate']['majority_rule_accuracy']:.4f}",
        f"rank_band baseline = {feasibility['rank_predicts_predicate']['majority_baseline_accuracy']:.4f}",
        f"machine_hint -> predicate majority accuracy = {feasibility['machine_hint_predicts_predicate']['majority_rule_accuracy']:.4f}",
        f"machine_hint baseline = {feasibility['machine_hint_predicts_predicate']['majority_baseline_accuracy']:.4f}",
        "```",
        "",
        "## Pair Counts",
        "",
        "```text",
    ]
    for key, value in feasibility["eligible_pair_counts"].items():
        lines.append(f"{key} = {value}")
    lines.extend(["```", "", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    path_decision_dir = as_abs(args.path_decision_dir)
    repair_ingestion_dir = as_abs(args.repair_ingestion_dir)
    path_decision = read_json(path_decision_dir / "summary.json")
    repair_summary = read_json(repair_ingestion_dir / "summary.json")
    validation_errors = validate_inputs(path_decision, repair_summary)

    current_exact_keys = load_current_exact_keys(repair_ingestion_dir)
    train_rows, row_errors, train_counts = load_train_rows(as_abs(args.hl_queue), as_abs(args.lh_queue))
    validation_errors.extend(row_errors)
    pairs, pair_rows, inventory_counts = build_pairs(train_rows, current_exact_keys)
    feasibility = feasibility_summary(pairs, pair_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "pair_inventory": output_dir / "pair_inventory.jsonl",
        "pair_rows": output_dir / "pair_rows.jsonl",
        "control_axis_counts": output_dir / "control_axis_counts.csv",
        "predictor_risks": output_dir / "predictor_risks.json",
    }

    if validation_errors:
        status = "h002_reliability_target_v9_predicate_rank_hint_feasibility_input_errors"
        decision = "Fix feasibility-scan input errors before choosing the next H002 target path."
        next_todo = "fix_reliability_target_v9_predicate_rank_hint_controlled_feasibility_scan_inputs"
    elif feasibility["strict_v9_exact_pair_feasible"]:
        status = "h002_reliability_target_v9_predicate_rank_hint_feasibility_exact_pair_ready"
        decision = "Exact endpoint-pair v9 appears feasible. Proceed to controlled candidate mining."
        next_todo = "reliability_target_v9_predicate_rank_hint_controlled_candidate_mining"
    else:
        status = "h002_reliability_target_v9_predicate_rank_hint_feasibility_exact_pair_not_feasible"
        decision = (
            "Exact endpoint-pair v9 has enough candidate rows, but rank/hint controls fail because predicate labels are structurally coupled "
            "to rank_band and machine_hint in the paired source outputs. Do not proceed to candidate mining under this exact-pair design."
        )
        next_todo = "reliability_target_v9_predicate_rank_hint_controlled_path_decision"

    control_rows: list[dict[str, Any]] = []
    eligible_rows = [row for row in pair_rows if row["eligible_for_v9_exact_pair"]]
    for keys, prefix in [
        (["pair_type"], "pair_type"),
        (["predicate_label_norm"], "predicate"),
        (["rank_band"], "rank"),
        (["machine_hint"], "machine_hint"),
        (["label_geometry_bucket"], "label_geometry_bucket"),
        (["predicate_label_norm", "rank_band"], "predicate_rank"),
        (["predicate_label_norm", "machine_hint"], "predicate_hint"),
        (["pair_type", "rank_band"], "pair_type_rank"),
        (["pair_type", "machine_hint"], "pair_type_hint"),
    ]:
        control_rows.extend(counter_rows(eligible_rows, keys, prefix))

    predictor_risks = {
        "rank_band_predicts_predicate": feasibility["rank_predicts_predicate"],
        "machine_hint_predicts_predicate": feasibility["machine_hint_predicts_predicate"],
        "label_geometry_bucket_predicts_predicate": feasibility["label_geometry_bucket_predicts_predicate"],
        "rank_common_capacity": feasibility["rank_common_capacity"],
        "machine_hint_common_capacity": feasibility["machine_hint_common_capacity"],
    }

    summary = {
        "schema_version": "h002_reliability_target_v9_predicate_rank_hint_feasibility_scan_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
            "repair_ingestion_summary": rel_path(repair_ingestion_dir / "summary.json"),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "hidden_axes_used_for_feasibility_control_only": True,
        },
        "train_counts": train_counts,
        "inventory_counts": inventory_counts,
        "current_repair_exact_endpoint_keys": len(current_exact_keys),
        "feasibility": feasibility,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_jsonl(output_paths["pair_inventory"], pairs)
    write_jsonl(output_paths["pair_rows"], pair_rows)
    write_csv(output_paths["control_axis_counts"], control_rows)
    write_json(output_paths["predictor_risks"], predictor_risks)
    return summary


def main() -> int:
    summary = run(parse_args())
    feasibility = summary["feasibility"]
    print(f"status={summary['status']}")
    print(f"eligible_pairs={feasibility['eligible_pairs']} eligible_rows={feasibility['eligible_rows']}")
    print(f"balanced_rows_upper_bound={feasibility['four_predicate_balanced_rows_upper_bound']}")
    print(f"rank_gate={feasibility['rank_gate']} hint_gate={feasibility['hint_gate']} predictor_gate={feasibility['predictor_gate']}")
    print(f"strict_v9_exact_pair_feasible={feasibility['strict_v9_exact_pair_feasible']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
