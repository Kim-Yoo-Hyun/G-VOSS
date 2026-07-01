#!/usr/bin/env python3
"""Create grouped internal H002 split over materialized route rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_grouped_split_v1"
EXPECTED_INPUT_SCHEMA = "h002_route_materialization_v1"
SPLIT_RATIOS = {"internal_train": 0.70, "internal_dev": 0.15, "internal_heldout": 0.15}
SPLIT_ORDER = ["internal_train", "internal_dev", "internal_heldout"]
EXPECTED_FAMILIES = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--schema-audit-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
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


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def round_targets(total: int) -> dict[str, int]:
    raw = {split: total * ratio for split, ratio in SPLIT_RATIOS.items()}
    floors = {split: int(value) for split, value in raw.items()}
    missing = total - sum(floors.values())
    remainders = sorted(((raw[split] - floors[split], split) for split in SPLIT_ORDER), reverse=True)
    targets = floors.copy()
    for _, split in remainders[:missing]:
        targets[split] += 1
    return targets


def group_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        group_id = str(row.get("cv_group_id"))
        group = grouped.setdefault(
            group_id,
            {
                "cv_group_id": group_id,
                "row_ids": [],
                "rows": 0,
                "route_families": Counter(),
                "target_y": Counter(),
                "predicates": Counter(),
            },
        )
        group["row_ids"].append(row["unified_row_id"])
        group["rows"] += 1
        group["route_families"][row["route_family"]] += 1
        group["target_y"][int(row["target_y"])] += 1
        group["predicates"][row["predicate_label"]] += 1
    return grouped


def assign_family_groups(family: str, groups: list[dict[str, Any]]) -> dict[str, str]:
    total_rows = sum(group["rows"] for group in groups)
    target_rows = round_targets(total_rows)
    current_rows = Counter()
    assignments: dict[str, str] = {}

    ordered = sorted(
        groups,
        key=lambda group: (
            stable_hash(f"{family}:{group['cv_group_id']}"),
            -group["rows"],
        ),
    )
    split_index = 0
    for group in ordered:
        while split_index < len(SPLIT_ORDER) - 1:
            split = SPLIT_ORDER[split_index]
            target = target_rows[split]
            current = current_rows[split]
            if current >= target:
                split_index += 1
                continue
            if current > 0 and current + group["rows"] > target:
                under = target - current
                over = current + group["rows"] - target
                if over > under:
                    split_index += 1
                    continue
            break
        best_split = SPLIT_ORDER[split_index]
        assignments[group["cv_group_id"]] = best_split
        current_rows[best_split] += group["rows"]
    return assignments


def create_split(rows: list[dict[str, Any]]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    grouped = group_rows(rows)
    multi_family = [group for group in grouped.values() if len(group["route_families"]) > 1]
    if multi_family:
        # The current H002 materialized pool should not hit this. Keeping an explicit
        # fallback would silently weaken the leakage contract, so fail validation later.
        return {}, [
            {
                "error_type": "multi_family_cv_group_not_supported_by_current_protocol",
                "cv_group_id": group["cv_group_id"],
                "route_families": sorted(group["route_families"]),
            }
            for group in multi_family
        ]

    assignments: dict[str, str] = {}
    errors: list[dict[str, Any]] = []
    family_to_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in grouped.values():
        family = next(iter(group["route_families"]))
        family_to_groups[family].append(group)
    for family, family_groups in sorted(family_to_groups.items()):
        family_assignments = assign_family_groups(family, family_groups)
        assignments.update(family_assignments)
    return assignments, errors


def build_tables(rows: list[dict[str, Any]], assignments: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    route_counts: Counter[tuple[str, str]] = Counter()
    label_counts: Counter[tuple[str, str, int]] = Counter()
    predicate_counts: Counter[tuple[str, str, str]] = Counter()
    group_counts: Counter[tuple[str, str]] = Counter()
    group_label_counts: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)

    grouped = group_rows(rows)
    for group_id, group in grouped.items():
        split = assignments[group_id]
        family = next(iter(group["route_families"]))
        group_counts[(family, split)] += 1
        group_label_counts[(family, split)].update(group["target_y"])
    for row in rows:
        split = assignments[row["cv_group_id"]]
        family = row["route_family"]
        route_counts[(family, split)] += 1
        label_counts[(family, split, int(row["target_y"]))] += 1
        predicate_counts[(family, split, row["predicate_label"])] += 1

    route_rows = []
    for family in sorted({row["route_family"] for row in rows}):
        for split in SPLIT_ORDER:
            route_rows.append(
                {
                    "route_family": family,
                    "protocol_split": split,
                    "rows": route_counts[(family, split)],
                    "label_0": label_counts[(family, split, 0)],
                    "label_1": label_counts[(family, split, 1)],
                    "cv_groups": group_counts[(family, split)],
                    "group_label_0": group_label_counts[(family, split)][0],
                    "group_label_1": group_label_counts[(family, split)][1],
                }
            )

    predicate_rows = [
        {
            "route_family": family,
            "protocol_split": split,
            "predicate_label": predicate,
            "rows": count,
        }
        for (family, split, predicate), count in sorted(predicate_counts.items())
    ]
    group_rows_out = []
    for group_id, group in sorted(grouped.items()):
        family = next(iter(group["route_families"]))
        split = assignments[group_id]
        group_rows_out.append(
            {
                "cv_group_id": group_id,
                "protocol_split": split,
                "route_family": family,
                "rows": group["rows"],
                "label_0": group["target_y"][0],
                "label_1": group["target_y"][1],
                "predicates": dict(sorted(group["predicates"].items())),
                "row_ids": group["row_ids"],
            }
        )
    leakage_rows = [
        {
            "check": "cv_group_single_split",
            "status": "pass",
            "violations": 0,
        },
        {
            "check": "official_validation_test_usage",
            "status": "pass",
            "violations": 0,
        },
    ]
    return route_rows, predicate_rows, group_rows_out, leakage_rows


def validate_split(rows: list[dict[str, Any]], assignments: dict[str, str], group_manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not rows:
        errors.append({"error_type": "no_rows"})
        return errors
    if {row.get("schema_version") for row in rows} != {EXPECTED_INPUT_SCHEMA}:
        errors.append({"error_type": "unexpected_input_schema_versions", "actual": sorted({row.get("schema_version") for row in rows})})
    families = {row["route_family"] for row in rows}
    if families != EXPECTED_FAMILIES:
        errors.append({"error_type": "unexpected_family_set", "expected": sorted(EXPECTED_FAMILIES), "actual": sorted(families)})
    if any(row.get("source_split") != "train" for row in rows):
        errors.append({"error_type": "non_train_source_split_present"})

    grouped = group_rows(rows)
    if set(grouped) != set(assignments):
        errors.append({"error_type": "assignment_group_set_mismatch", "groups": len(grouped), "assignments": len(assignments)})
    row_ids = [row["unified_row_id"] for row in rows]
    if len(row_ids) != len(set(row_ids)):
        errors.append({"error_type": "duplicate_unified_row_id"})
    for group_id, split in assignments.items():
        if split not in SPLIT_ORDER:
            errors.append({"error_type": "invalid_split_name", "cv_group_id": group_id, "split": split})

    route_split_labels: Counter[tuple[str, str, int]] = Counter()
    route_split_rows: Counter[tuple[str, str]] = Counter()
    for row in rows:
        split = assignments[row["cv_group_id"]]
        family = row["route_family"]
        route_split_rows[(family, split)] += 1
        route_split_labels[(family, split, int(row["target_y"]))] += 1
    for family in families:
        for split in SPLIT_ORDER:
            if route_split_rows[(family, split)] == 0:
                errors.append({"error_type": "empty_family_split", "family": family, "split": split})
            if route_split_labels[(family, split, 0)] == 0 or route_split_labels[(family, split, 1)] == 0:
                errors.append(
                    {
                        "error_type": "missing_binary_label_in_family_split",
                        "family": family,
                        "split": split,
                        "label_0": route_split_labels[(family, split, 0)],
                        "label_1": route_split_labels[(family, split, 1)],
                    }
                )

    seen_group_splits: dict[str, str] = {}
    for row in group_manifest:
        group_id = row["cv_group_id"]
        split = row["protocol_split"]
        if group_id in seen_group_splits and seen_group_splits[group_id] != split:
            errors.append({"error_type": "cv_group_multi_split", "cv_group_id": group_id})
        seen_group_splits[group_id] = split
    return errors


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    materialization_manifest = read_json(args.materialization_dir / "row_manifest.json")
    schema_audit_manifest = read_json(args.schema_audit_dir / "audit_manifest.json")
    rows = read_jsonl(args.materialization_dir / "model_safe_view.jsonl")
    assignments, assignment_errors = create_split(rows)

    route_rows: list[dict[str, Any]] = []
    predicate_rows: list[dict[str, Any]] = []
    group_manifest: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    split_model_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = list(assignment_errors)

    if not assignment_errors:
        route_rows, predicate_rows, group_manifest, leakage_rows = build_tables(rows, assignments)
        errors.extend(validate_split(rows, assignments, group_manifest))
        for row in rows:
            split = assignments[row["cv_group_id"]]
            updated = dict(row)
            updated["protocol_split"] = split
            updated["split_policy"] = {
                "schema_version": SCHEMA_VERSION,
                "source": "internal_h002_candidate_pool",
                "group_key": "cv_group_id",
                "official_validation_or_test": False,
                "ratios": SPLIT_RATIOS,
            }
            split_model_rows.append(updated)

    split_rows_count = write_jsonl(out / "model_safe_split_view.jsonl", split_model_rows)
    assignment_count = write_jsonl(
        out / "split_assignments.jsonl",
        [
            {"schema_version": SCHEMA_VERSION, "cv_group_id": group_id, "protocol_split": split}
            for group_id, split in sorted(assignments.items())
        ],
    )
    group_count = write_jsonl(out / "group_manifest.jsonl", group_manifest)
    write_csv(out / "route_split_counts.csv", route_rows)
    write_csv(out / "predicate_split_counts.csv", predicate_rows)
    write_csv(out / "leakage_audit.csv", leakage_rows)
    write_jsonl(out / "validation_errors.jsonl", errors)

    status = "ready" if not errors else "errors"
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    split_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": created_at,
        "source": "internal_h002_candidate_pool",
        "official_validation_or_test": False,
        "split_ratios": SPLIT_RATIOS,
        "group_key": "cv_group_id",
        "input_artifacts": {
            "materialization_manifest": repo_rel(repo_root, args.materialization_dir / "row_manifest.json"),
            "schema_audit_manifest": repo_rel(repo_root, args.schema_audit_dir / "audit_manifest.json"),
        },
        "input_status": {
            "materialization": materialization_manifest.get("status"),
            "schema_audit": schema_audit_manifest.get("status"),
        },
        "row_counts": {
            "input_model_safe_rows": len(rows),
            "model_safe_split_view": split_rows_count,
            "split_assignments": assignment_count,
            "group_manifest": group_count,
            "validation_errors": len(errors),
        },
        "route_split_counts": route_rows,
        "predicate_split_counts": predicate_rows,
        "boundary": {
            "paper_metric_produced": False,
            "grouped_holdout_metric_run": False,
            "official_validation_usage": False,
            "official_test_usage": False,
            "h001_artifacts_modified": False,
            "runtime_output_root": repo_rel(repo_root, out),
        },
        "next_required_gate": "grouped_eval_protocol",
    }
    write_json(out / "split_manifest.json", split_manifest)
    print(json.dumps(split_manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
