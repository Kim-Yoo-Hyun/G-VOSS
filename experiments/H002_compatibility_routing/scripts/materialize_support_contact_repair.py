#!/usr/bin/env python3
"""Materialize pose-aware support/contact repair rows for H002."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_support_contact_generalization_repair_materialization_v1"
REQUIRED_REPAIR_STATUS = "h002_support_contact_generalization_repair_ready"
MAIN_PREDICATES = {"standing on", "lying on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--hard-materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"),
    )
    parser.add_argument(
        "--repair-plan-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_generalization_repair/latest"),
    )
    parser.add_argument("--class-pair-cap", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def label_value(row: dict[str, Any]) -> int:
    labels = row.get("labels", {})
    return int(labels.get("C_e", 0))


def feature_vector(row: dict[str, Any]) -> dict[str, float]:
    return row.get("feature_blocks", {}).get("G_e", {}).get("g_e_feature_vector", {})


def pose_proxy(row: dict[str, Any]) -> dict[str, Any]:
    vec = feature_vector(row)
    vertical = safe_float(vec.get("subject_vertical_extent_ratio"))
    horizontal = safe_float(vec.get("subject_horizontal_extent_ratio"))
    flatness = safe_float(vec.get("subject_flatness_ratio"))
    contact = safe_float(vec.get("contact_patch_ratio_proxy"))
    density = safe_float(vec.get("local_contact_point_density"))
    support = safe_float(vec.get("support_contact_likelihood_proxy"))
    abs_gap = safe_float(vec.get("abs_surface_gap_subject_bottom_to_object_top"))
    support_score = 0.45 * support + 0.25 * min(contact * 5.0, 1.0) + 0.20 * min(density * 2.0, 1.0) + 0.10 * max(0.0, 1.0 - min(abs_gap, 1.0))
    upright_score = 0.55 * vertical + 0.25 * max(0.0, 1.0 - min(horizontal / 2.0, 1.0)) + 0.20 * flatness
    lying_score = 0.55 * min(horizontal / 3.0, 1.0) + 0.25 * max(0.0, 1.0 - vertical) + 0.20 * max(0.0, 1.0 - flatness)
    if support_score < 0.35:
        state = "weak_support_evidence"
    elif abs(upright_score - lying_score) < 0.10:
        state = "ambiguous_pose"
    elif upright_score > lying_score:
        state = "upright_like"
    else:
        state = "horizontal_like"
    return {
        "support_score_proxy": round(support_score, 6),
        "upright_score_proxy": round(upright_score, 6),
        "lying_score_proxy": round(lying_score, 6),
        "pose_proxy_state": state,
    }


def with_class_t(row: dict[str, Any], hidden: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("feature_blocks", {}).get("T_e", {}))
    t["subject_class_label"] = hidden.get("subject_class_label")
    t["object_class_label"] = hidden.get("object_class_label")
    t["class_pair"] = hidden.get("class_pair")
    return t


def no_class_t(row: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("feature_blocks", {}).get("T_e", {}))
    for key in ["subject_class_label", "object_class_label", "class_pair"]:
        t.pop(key, None)
    return t


def binary_row(row: dict[str, Any], hidden: dict[str, Any], include_class: bool, role: str) -> dict[str, Any]:
    labels = {
        "C_e": label_value(row),
        "decision_label": "accept" if label_value(row) == 1 else "reject",
        "p_obs": 1,
        "repair_role": role,
    }
    t_block = with_class_t(row, hidden) if include_class else no_class_t(row)
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": row["candidate_id"],
        "split": "validation",
        "route_family": "support_contact",
        "predicate_label": row["predicate_label"],
        "labels": labels,
        "feature_blocks": {
            "T_e": t_block,
            "G_e": row.get("feature_blocks", {}).get("G_e", {}),
        },
        "feature_use_policy": {
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "excluded_from_primary_C_e": ["Z_e", "Q_e", "H001 p_geom_valid", "source score/rank"],
            "class_semantic_policy": "included" if include_class else "excluded_control_view",
            "label_not_features": ["labels.C_e", "labels.decision_label", "labels.p_obs", "labels.repair_role"],
        },
        "paper_metric_ready": False,
        "official_validation_eval_only": True,
        "official_test_used": False,
    }


def selective_row(row: dict[str, Any], hidden: dict[str, Any], group_role: str, selected_binary: bool) -> dict[str, Any]:
    if selected_binary:
        decision = "accept" if label_value(row) == 1 else "reject"
        c_e: int | None = label_value(row)
        p_obs = 1
    else:
        decision = "abstain"
        c_e = None
        p_obs = 0
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": row["candidate_id"],
        "split": "validation",
        "route_family": "support_contact",
        "predicate_label": row["predicate_label"],
        "labels": {
            "C_e": c_e,
            "decision_label": decision,
            "p_obs": p_obs,
            "repair_role": group_role,
        },
        "feature_blocks": {
            "T_e": no_class_t(row),
            "G_e": row.get("feature_blocks", {}).get("G_e", {}),
        },
        "feature_use_policy": {
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "excluded_from_primary_C_e": ["Z_e", "Q_e", "class labels", "H001 p_geom_valid", "source score/rank"],
            "label_not_features": ["labels.C_e", "labels.decision_label", "labels.p_obs", "labels.repair_role"],
        },
        "paper_metric_ready": False,
        "official_validation_eval_only": True,
        "official_test_used": False,
    }


def geometry_only_row(row: dict[str, Any], role: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": row["candidate_id"],
        "split": "validation",
        "route_family": "support_contact",
        "predicate_label": row["predicate_label"],
        "labels": {
            "C_e": label_value(row),
            "decision_label": "accept" if label_value(row) == 1 else "reject",
            "p_obs": 1,
            "repair_role": role,
        },
        "feature_blocks": {"G_e": row.get("feature_blocks", {}).get("G_e", {})},
        "feature_use_policy": {
            "main_C_e_allowed_blocks": ["G_e"],
            "excluded_from_primary_C_e": ["T_e", "Z_e", "Q_e", "class labels", "H001 p_geom_valid"],
            "label_not_features": ["labels.C_e", "labels.decision_label", "labels.p_obs", "labels.repair_role"],
        },
        "paper_metric_ready": False,
        "official_validation_eval_only": True,
        "official_test_used": False,
    }


def validate_repair_plan(path: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary = read_json(path / "summary.json")
    if summary.get("status") != REQUIRED_REPAIR_STATUS:
        errors.append({"error_type": "unexpected_repair_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "repair_plan_has_validation_errors", "actual": summary.get("validation_errors")})
    if summary.get("decision", {}).get("selected_path") != "pose_aware_relabel_abstain_repair_before_more_model_capacity":
        errors.append({"error_type": "unexpected_repair_path", "actual": summary.get("decision", {}).get("selected_path")})
    return errors


def blocked_field_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    blocked = {"Z_e", "Q_e", "source_score", "rank", "p_geom_valid", "gt", "target_generation_rule"}
    for row in rows:
        as_text = json.dumps(row.get("feature_blocks", {}), sort_keys=True)
        for token in blocked:
            if token in as_text:
                hits.append({"candidate_id": row.get("candidate_id"), "blocked_token": token})
    return hits


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    hard_dir = resolve(repo_root, args.hard_materialization_dir)
    repair_dir = resolve(repo_root, args.repair_plan_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors = validate_repair_plan(repair_dir)
    hard_manifest = read_json(hard_dir / "row_manifest.json")
    if hard_manifest.get("validation_errors") != 0:
        validation_errors.append({"error_type": "hard_materialization_has_validation_errors", "actual": hard_manifest.get("validation_errors")})

    hard_rows = list(iter_jsonl(hard_dir / "model_safe_main_no_class.jsonl"))
    hidden_rows = list(iter_jsonl(hard_dir / "hidden_manifest.jsonl"))
    hidden_by_id = {row["candidate_id"]: row for row in hidden_rows}
    if len(hard_rows) != len(hidden_rows):
        validation_errors.append({"error_type": "row_hidden_count_mismatch", "hard_rows": len(hard_rows), "hidden_rows": len(hidden_rows)})

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in hard_rows:
        hidden = hidden_by_id.get(row["candidate_id"], {})
        group_key = hidden.get("cv_or_group_key") or row["candidate_id"].rsplit("::", 2)[0]
        groups[group_key].append(row)

    positive_by_class_pair: dict[str, Counter[str]] = defaultdict(Counter)
    for members in groups.values():
        if len(members) != 2:
            continue
        pos = [row for row in members if label_value(row) == 1]
        if len(pos) != 1:
            continue
        hidden = hidden_by_id.get(pos[0]["candidate_id"], {})
        positive_by_class_pair[hidden.get("class_pair", "")][pos[0]["predicate_label"]] += 1

    mixed_class_pairs = {
        pair
        for pair, counts in positive_by_class_pair.items()
        if counts.get("standing on", 0) > 0 and counts.get("lying on", 0) > 0
    }

    groups_by_pair_pos: dict[tuple[str, str], list[tuple[str, list[dict[str, Any]]]]] = defaultdict(list)
    group_meta: dict[str, dict[str, Any]] = {}
    for group_key, members in sorted(groups.items()):
        pos = [row for row in members if label_value(row) == 1]
        hidden = hidden_by_id.get(members[0]["candidate_id"], {})
        class_pair = hidden.get("class_pair", "")
        pos_predicate = pos[0]["predicate_label"] if len(pos) == 1 else "invalid"
        group_meta[group_key] = {
            "class_pair": class_pair,
            "positive_predicate": pos_predicate,
            "is_mixed_class_pair": class_pair in mixed_class_pairs,
        }
        if class_pair in mixed_class_pairs and pos_predicate in MAIN_PREDICATES:
            groups_by_pair_pos[(class_pair, pos_predicate)].append((group_key, members))

    selected_groups: set[str] = set()
    class_pair_rows: list[dict[str, Any]] = []
    for class_pair in sorted(mixed_class_pairs):
        standing = groups_by_pair_pos.get((class_pair, "standing on"), [])
        lying = groups_by_pair_pos.get((class_pair, "lying on"), [])
        take = min(len(standing), len(lying), args.class_pair_cap)
        for group_key, _members in standing[:take] + lying[:take]:
            selected_groups.add(group_key)
        class_pair_rows.append(
            {
                "class_pair": class_pair,
                "standing_positive_groups": len(standing),
                "lying_positive_groups": len(lying),
                "selected_per_positive_predicate": take,
                "selected_groups": take * 2,
                "selected_binary_rows": take * 4,
                "class_pair_role": "main_binary_mixed_class_pair" if take > 0 else "insufficient_after_balance",
            }
        )

    binary_no_class: list[dict[str, Any]] = []
    binary_with_class: list[dict[str, Any]] = []
    binary_geometry: list[dict[str, Any]] = []
    selective_no_class: list[dict[str, Any]] = []
    hidden_out: list[dict[str, Any]] = []
    group_out: list[dict[str, Any]] = []
    pose_rows: list[dict[str, Any]] = []

    for group_key, members in sorted(groups.items()):
        meta = group_meta[group_key]
        selected = group_key in selected_groups
        if selected:
            role = "main_binary_mixed_class_pair"
        elif meta["is_mixed_class_pair"]:
            role = "abstain_mixed_class_pair_overflow"
        else:
            role = "abstain_single_subtype_class_pair"
        predicates = sorted(row["predicate_label"] for row in members)
        labels = sorted(label_value(row) for row in members)
        pose_states = []
        for row in members:
            hidden = hidden_by_id.get(row["candidate_id"], {})
            pose = pose_proxy(row)
            pose_states.append(pose["pose_proxy_state"])
            selective_no_class.append(selective_row(row, hidden, role, selected))
            hidden_out.append(
                {
                    "schema_version": f"{SCHEMA_VERSION}_hidden_manifest",
                    "candidate_id": row["candidate_id"],
                    "cv_or_group_key": group_key,
                    "class_pair": hidden.get("class_pair"),
                    "subject_class_label": hidden.get("subject_class_label"),
                    "object_class_label": hidden.get("object_class_label"),
                    "predicate_label": row["predicate_label"],
                    "original_C_e": label_value(row),
                    "repair_role": role,
                    "selected_binary": selected,
                    "positive_predicate_for_group": meta["positive_predicate"],
                    "is_mixed_class_pair": meta["is_mixed_class_pair"],
                    "pose_proxy": pose,
                    "source_hidden_manifest": hidden.get("source_hidden_manifest", {}),
                    "source_score_policy": "hidden_or_future_p_rel_only_not_main_C_e",
                    "h001_p_geom_valid_policy": "hidden_or_diagnostic_only_not_main_G_e",
                }
            )
            pose_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "cv_or_group_key": group_key,
                    "class_pair": hidden.get("class_pair"),
                    "predicate_label": row["predicate_label"],
                    "original_C_e": label_value(row),
                    "repair_role": role,
                    **pose,
                }
            )
            if selected:
                binary_no_class.append(binary_row(row, hidden, include_class=False, role=role))
                binary_with_class.append(binary_row(row, hidden, include_class=True, role=role))
                binary_geometry.append(geometry_only_row(row, role=role))

        group_out.append(
            {
                "schema_version": f"{SCHEMA_VERSION}_group_manifest",
                "cv_or_group_key": group_key,
                "class_pair": meta["class_pair"],
                "positive_predicate": meta["positive_predicate"],
                "predicates": predicates,
                "labels": labels,
                "repair_role": role,
                "selected_binary": selected,
                "pair_integrity_ok": len(members) == 2 and predicates == sorted(MAIN_PREDICATES) and labels == [0, 1],
                "pose_proxy_states": sorted(set(pose_states)),
            }
        )

    blocked_hits = blocked_field_hits(binary_no_class)
    if blocked_hits:
        validation_errors.append({"error_type": "blocked_field_hits", "count": len(blocked_hits)})

    label_counts = Counter(str(row["labels"]["C_e"]) for row in binary_no_class)
    predicate_counts = Counter(row["predicate_label"] for row in binary_no_class)
    role_counts = Counter(row["labels"]["repair_role"] for row in selective_no_class)
    decision_counts = Counter(row["labels"]["decision_label"] for row in selective_no_class)
    binary_class_pairs = Counter(hidden_by_id[row["candidate_id"]].get("class_pair", "") for row in binary_no_class)

    capacity_gate = len(binary_no_class) >= 200 and len(mixed_class_pairs) >= 10
    gate_failures: list[dict[str, Any]] = []
    if not capacity_gate:
        gate_failures.append(
            {
                "gate": "main_binary_capacity",
                "binary_rows": len(binary_no_class),
                "mixed_class_pairs": len(mixed_class_pairs),
                "required_binary_rows": 200,
                "required_mixed_class_pairs": 10,
                "decision": "metric_rerun_blocked",
            }
        )

    write_jsonl(out / "model_safe_binary_no_class.jsonl", binary_no_class)
    write_jsonl(out / "model_safe_binary_with_class_semantic.jsonl", binary_with_class)
    write_jsonl(out / "model_safe_binary_geometry_only.jsonl", binary_geometry)
    write_jsonl(out / "model_safe_selective_no_class.jsonl", selective_no_class)
    write_jsonl(out / "hidden_manifest.jsonl", hidden_out)
    write_jsonl(out / "group_manifest.jsonl", group_out)
    write_csv(
        out / "class_pair_quota.csv",
        class_pair_rows,
        [
            "class_pair",
            "standing_positive_groups",
            "lying_positive_groups",
            "selected_per_positive_predicate",
            "selected_groups",
            "selected_binary_rows",
            "class_pair_role",
        ],
    )
    write_csv(
        out / "pose_proxy_diagnostics.csv",
        pose_rows,
        [
            "candidate_id",
            "cv_or_group_key",
            "class_pair",
            "predicate_label",
            "original_C_e",
            "repair_role",
            "support_score_proxy",
            "upright_score_proxy",
            "lying_score_proxy",
            "pose_proxy_state",
        ],
    )
    schema_precheck = {
        "schema_version": SCHEMA_VERSION,
        "blocked_field_hits": len(blocked_hits),
        "blocked_field_hit_examples": blocked_hits[:20],
        "binary_label_counts": dict(sorted(label_counts.items())),
        "binary_predicate_counts": dict(sorted(predicate_counts.items())),
        "selective_decision_counts": dict(sorted(decision_counts.items())),
        "selective_role_counts": dict(sorted(role_counts.items())),
        "binary_class_pair_counts": dict(sorted(binary_class_pairs.items())),
        "capacity_gate_pass": capacity_gate,
        "paper_metric_ready": False,
        "metric_rerun_ready": capacity_gate and len(blocked_hits) == 0,
    }
    write_json(out / "schema_precheck.json", schema_precheck)
    with (out / "validation_errors.jsonl").open("w", encoding="utf-8") as handle:
        for err in validation_errors:
            handle.write(json.dumps(err, ensure_ascii=False, sort_keys=True) + "\n")
    with (out / "gate_failures.jsonl").open("w", encoding="utf-8") as handle:
        for err in gate_failures:
            handle.write(json.dumps(err, ensure_ascii=False, sort_keys=True) + "\n")

    row_manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "h002_support_contact_generalization_repair_materialization_ready",
        "validation_errors": len(validation_errors),
        "gate_failures": len(gate_failures),
        "gate_failure_policy": "capacity_below_gate_blocks_metric_rerun_but_is_not_schema_validation_error",
        "source_artifacts": {
            "hard_materialization": repo_rel(repo_root, hard_dir),
            "repair_plan": repo_rel(repo_root, repair_dir),
        },
        "row_counts": {
            "hard_input_rows": len(hard_rows),
            "hard_input_groups": len(groups),
            "model_safe_binary_no_class": len(binary_no_class),
            "model_safe_binary_with_class_semantic": len(binary_with_class),
            "model_safe_binary_geometry_only": len(binary_geometry),
            "model_safe_selective_no_class": len(selective_no_class),
            "hidden_manifest": len(hidden_out),
            "group_manifest": len(group_out),
            "mixed_class_pairs": len(mixed_class_pairs),
            "single_subtype_groups": sum(1 for row in group_out if row["repair_role"] == "abstain_single_subtype_class_pair"),
            "mixed_overflow_groups": sum(1 for row in group_out if row["repair_role"] == "abstain_mixed_class_pair_overflow"),
            "main_binary_groups": sum(1 for row in group_out if row["repair_role"] == "main_binary_mixed_class_pair"),
        },
        "label_counts": dict(sorted(label_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "class_pair_quota": class_pair_rows,
        "schema_precheck": schema_precheck,
        "boundary": {
            "official_validation_eval_only": True,
            "official_test_used": False,
            "paper_metric_ready": False,
            "metric_rerun_ready": schema_precheck["metric_rerun_ready"],
            "h001_artifacts_modified": False,
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "Z_e_policy": "excluded_from_C_e_hidden_or_future_p_rel_only",
            "Q_e_policy": "not_in_C_e_main_input",
        },
        "decision": {
            "support_contact_solved": False,
            "main_binary_capacity_sufficient": capacity_gate,
            "selected_path": "mixed_class_pair_main_binary_plus_single_subtype_abstain_diagnostic",
            "reason": "only a small number of class-pairs contain both standing-on and lying-on positives; class-pair shortcut remains the limiting issue",
            "next_todo": "support_contact_generalization_repair_capacity_decision",
        },
        "output_artifacts": {
            "model_safe_binary_no_class": repo_rel(repo_root, out / "model_safe_binary_no_class.jsonl"),
            "model_safe_binary_with_class_semantic": repo_rel(repo_root, out / "model_safe_binary_with_class_semantic.jsonl"),
            "model_safe_binary_geometry_only": repo_rel(repo_root, out / "model_safe_binary_geometry_only.jsonl"),
            "model_safe_selective_no_class": repo_rel(repo_root, out / "model_safe_selective_no_class.jsonl"),
            "hidden_manifest": repo_rel(repo_root, out / "hidden_manifest.jsonl"),
            "group_manifest": repo_rel(repo_root, out / "group_manifest.jsonl"),
            "class_pair_quota": repo_rel(repo_root, out / "class_pair_quota.csv"),
            "pose_proxy_diagnostics": repo_rel(repo_root, out / "pose_proxy_diagnostics.csv"),
            "schema_precheck": repo_rel(repo_root, out / "schema_precheck.json"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "gate_failures": repo_rel(repo_root, out / "gate_failures.jsonl"),
            "row_manifest": repo_rel(repo_root, out / "row_manifest.json"),
        },
    }
    write_json(out / "row_manifest.json", row_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
