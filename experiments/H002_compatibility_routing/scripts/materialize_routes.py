#!/usr/bin/env python3
"""Materialize promoted H002 route rows inside Docker."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


SCHEMA_VERSION = "h002_route_materialization_v1"
PROTOCOL_SPLIT = "unassigned_pre_grouped_holdout"


@dataclass(frozen=True)
class RouteSpec:
    family: str
    role: str
    model_safe_path: str
    hidden_path: str | None
    row_id_key: str
    hidden_id_key: str
    row_filter: Callable[[dict[str, Any]], bool]
    hidden_filter: Callable[[dict[str, Any]], bool]
    source_artifact: str
    extra_hidden_paths: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


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


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def get_feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = row.get("feature_blocks")
    if not isinstance(blocks, dict):
        return {}
    return blocks


def infer_predicate(row: dict[str, Any]) -> str:
    blocks = get_feature_blocks(row)
    te = blocks.get("T_e", {}) if isinstance(blocks.get("T_e"), dict) else {}
    for value in [row.get("predicate_label"), te.get("predicate_label"), row.get("candidate_predicate_label")]:
        if value:
            return str(value)
    return "unknown_predicate"


def infer_family(row: dict[str, Any], fallback: str) -> str:
    blocks = get_feature_blocks(row)
    te = blocks.get("T_e", {}) if isinstance(blocks.get("T_e"), dict) else {}
    for value in [row.get("family"), te.get("relation_family"), te.get("predicate_family")]:
        if value:
            return str(value)
    return fallback


def infer_target_y(row: dict[str, Any]) -> int | None:
    if "target_y" in row:
        return int(row["target_y"])
    labels = row.get("labels")
    if isinstance(labels, dict):
        for key in ["C_e", "target_y", "compatibility_target_y", "is_compatible"]:
            if key in labels:
                return int(labels[key])
    return None


def infer_group_id(row: dict[str, Any]) -> str:
    split_metadata = row.get("split_metadata") if isinstance(row.get("split_metadata"), dict) else {}
    for value in [
        row.get("cv_group_id"),
        row.get("cv_group"),
        row.get("group_id"),
        split_metadata.get("cv_group_id"),
    ]:
        if value:
            return str(value)
    return "missing_group_id"


def normalize_feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = get_feature_blocks(row)
    normalized: dict[str, Any] = {
        "T_e": {},
        "G_e": {},
        "Q_e": {},
        "Z_e": {},
        "extra_safe_blocks": {},
    }
    for key, value in blocks.items():
        if key == "T_e":
            normalized["T_e"] = value
        elif key.startswith("G_e"):
            normalized["G_e"][key] = value
        elif key.startswith("Q_e"):
            normalized["Q_e"][key] = value
        elif key.startswith("Z_e"):
            normalized["Z_e"][key] = value
        else:
            normalized["extra_safe_blocks"][key] = value
    return normalized


def route_specs() -> list[RouteSpec]:
    return [
        RouteSpec(
            family="relative_vertical",
            role="candidate_clean_compatibility_route",
            model_safe_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/"
                "sanitized_primary_view.jsonl"
            ),
            hidden_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization/"
                "hidden_manifest.jsonl"
            ),
            row_id_key="example_id",
            hidden_id_key="row_id",
            row_filter=lambda row: infer_family(row, "") == "relative_vertical",
            hidden_filter=lambda row: row.get("family") == "relative_vertical",
            source_artifact="compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit",
        ),
        RouteSpec(
            family="size_relative",
            role="candidate_clean_compatibility_route",
            model_safe_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization/"
                "smoke_ready_view.jsonl"
            ),
            hidden_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_size_relative_candidate_materialization_after_plan/"
                "hidden_manifest.jsonl"
            ),
            row_id_key="row_id",
            hidden_id_key="row_id",
            row_filter=lambda row: row.get("subset") == "primary_compatibility",
            hidden_filter=lambda row: row.get("subset") == "primary_compatibility",
            source_artifact="compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization",
        ),
        RouteSpec(
            family="relative_horizontal",
            role="candidate_frame_aware_compatibility_route",
            model_safe_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization/"
                "smoke_ready_view.jsonl"
            ),
            hidden_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan/"
                "hidden_manifest.jsonl"
            ),
            row_id_key="row_id",
            hidden_id_key="row_id",
            row_filter=lambda row: row.get("subset") == "primary_compatibility",
            hidden_filter=lambda row: row.get("subset") == "primary_compatibility",
            source_artifact="compatibility_dataset_v3_relative_horizontal_schema_shortcut_audit_after_materialization",
        ),
        RouteSpec(
            family="support_contact",
            role="candidate_challenging_compatibility_route",
            model_safe_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit/"
                "smoke_ready_view.jsonl"
            ),
            hidden_path=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/"
                "source_manifest.jsonl"
            ),
            row_id_key="row_id",
            hidden_id_key="row_id",
            row_filter=lambda row: True,
            hidden_filter=lambda row: row.get("predicate_label") in {"standing on", "lying on"},
            source_artifact="compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit",
            extra_hidden_paths=(
                "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
                "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/"
                "control_manifest.jsonl",
            ),
        ),
    ]


def build_hidden_map(repo_root: Path, spec: RouteSpec) -> dict[str, dict[str, Any]]:
    hidden: dict[str, dict[str, Any]] = {}
    if spec.hidden_path:
        path = repo_root / spec.hidden_path
        for row in read_jsonl(path):
            if spec.hidden_filter(row):
                hidden[str(row[spec.hidden_id_key])] = {"primary_hidden": row}
    for extra in spec.extra_hidden_paths:
        path = repo_root / extra
        for row in read_jsonl(path):
            row_id = str(row[spec.hidden_id_key])
            hidden.setdefault(row_id, {})[Path(extra).stem] = row
    return hidden


def materialize(repo_root: Path, out: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    route_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    route_counts: Counter[str] = Counter()
    predicate_counts: Counter[tuple[str, str]] = Counter()
    label_counts: Counter[tuple[str, int]] = Counter()
    source_paths: dict[str, dict[str, str]] = {}
    duplicate_ids: set[str] = set()
    seen_ids: set[str] = set()

    for spec in route_specs():
        model_path = repo_root / spec.model_safe_path
        if not model_path.exists():
            errors.append({"error_type": "missing_model_safe_source", "family": spec.family, "path": spec.model_safe_path})
            continue
        if spec.hidden_path and not (repo_root / spec.hidden_path).exists():
            errors.append({"error_type": "missing_hidden_source", "family": spec.family, "path": spec.hidden_path})
            continue
        hidden_map = build_hidden_map(repo_root, spec)
        rows = [row for row in read_jsonl(model_path) if spec.row_filter(row)]
        source_paths[spec.family] = {
            "model_safe_source": spec.model_safe_path,
            "hidden_source": spec.hidden_path or "",
            "extra_hidden_sources": list(spec.extra_hidden_paths),
        }
        for row in rows:
            source_row_id = str(row[spec.row_id_key])
            unified_row_id = f"{spec.family}::{source_row_id}"
            if unified_row_id in seen_ids:
                duplicate_ids.add(unified_row_id)
            seen_ids.add(unified_row_id)
            target_y = infer_target_y(row)
            predicate = infer_predicate(row)
            group_id = infer_group_id(row)
            if target_y not in {0, 1}:
                errors.append(
                    {
                        "error_type": "missing_or_invalid_binary_target",
                        "family": spec.family,
                        "source_row_id": source_row_id,
                        "target_y": target_y,
                    }
                )
                continue
            if group_id == "missing_group_id":
                errors.append({"error_type": "missing_group_id", "family": spec.family, "source_row_id": source_row_id})

            safe_feature_blocks = normalize_feature_blocks(row)
            route_row = {
                "schema_version": SCHEMA_VERSION,
                "unified_row_id": unified_row_id,
                "source_row_id": source_row_id,
                "route_family": spec.family,
                "route_role": spec.role,
                "predicate_label": predicate,
                "target_name": "C_e",
                "target_y": target_y,
                "source_split": row.get("split", "train"),
                "protocol_split": PROTOCOL_SPLIT,
                "cv_group_id": group_id,
                "source_artifact": spec.source_artifact,
                "paper_metric_ready": False,
            }
            model_safe_row = {
                **route_row,
                "feature_blocks": safe_feature_blocks,
                "feature_use_policy": {
                    "C_e_allowed_blocks": ["T_e", "G_e"],
                    "C_e_blocked_blocks": ["Z_e", "Q_e", "extra_safe_blocks"],
                    "Q_e_allowed_blocks": ["Q_e"],
                    "Z_e_allowed_blocks": ["Z_e"],
                    "p_rel_may_use_after_protocol_lock": ["T_e", "G_e", "C_e", "Q_e", "Z_e"],
                    "p_obs_may_use_after_protocol_lock": ["Q_e"],
                },
                "model_safe_source": spec.model_safe_path,
            }
            hidden_row = {
                "schema_version": SCHEMA_VERSION,
                "unified_row_id": unified_row_id,
                "source_row_id": source_row_id,
                "route_family": spec.family,
                "predicate_label": predicate,
                "target_y": target_y,
                "cv_group_id": group_id,
                "hidden_source": spec.hidden_path or "",
                "extra_hidden_sources": list(spec.extra_hidden_paths),
                "hidden": hidden_map.get(source_row_id, {}),
            }
            if not hidden_row["hidden"]:
                errors.append({"error_type": "missing_hidden_row", "family": spec.family, "source_row_id": source_row_id})

            route_rows.append(route_row)
            model_safe_rows.append(model_safe_row)
            hidden_rows.append(hidden_row)
            route_counts[spec.family] += 1
            predicate_counts[(spec.family, predicate)] += 1
            label_counts[(spec.family, target_y)] += 1

    for unified_row_id in sorted(duplicate_ids):
        errors.append({"error_type": "duplicate_unified_row_id", "unified_row_id": unified_row_id})
    for spec in route_specs():
        labels = {label: label_counts[(spec.family, label)] for label in [0, 1]}
        if labels[0] == 0 or labels[1] == 0:
            errors.append({"error_type": "route_missing_binary_class", "family": spec.family, "label_counts": labels})

    out.mkdir(parents=True, exist_ok=True)
    route_rows_count = write_jsonl(out / "route_rows.jsonl", route_rows)
    model_safe_count = write_jsonl(out / "model_safe_view.jsonl", model_safe_rows)
    hidden_count = write_jsonl(out / "hidden_manifest.jsonl", hidden_rows)
    write_jsonl(out / "validation_errors.jsonl", errors)

    route_count_table = [
        {
            "route_family": family,
            "row_count": route_counts[family],
            "label_0": label_counts[(family, 0)],
            "label_1": label_counts[(family, 1)],
            "predicates": {
                predicate: predicate_counts[(family, predicate)]
                for fam, predicate in predicate_counts
                if fam == family
            },
        }
        for family in sorted(route_counts)
    ]
    predicate_count_table = [
        {
            "route_family": family,
            "predicate_label": predicate,
            "row_count": count,
        }
        for (family, predicate), count in sorted(predicate_counts.items())
    ]
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not errors else "errors",
        "created_at_utc": created_at,
        "protocol_split": PROTOCOL_SPLIT,
        "row_counts": {
            "route_rows": route_rows_count,
            "model_safe_view": model_safe_count,
            "hidden_manifest": hidden_count,
            "validation_errors": len(errors),
        },
        "route_count_table": route_count_table,
        "predicate_count_table": predicate_count_table,
        "source_paths": source_paths,
        "boundary": {
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
            "runtime_output_root": repo_rel(repo_root, out),
        },
        "next_required_gate": "materialization_schema_shortcut_audit",
    }
    write_json(out / "row_manifest.json", row_manifest)
    return row_manifest


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    row_manifest = materialize(repo_root=repo_root, out=args.out)
    print(json.dumps(row_manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if row_manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
