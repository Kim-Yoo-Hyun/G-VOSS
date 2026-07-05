#!/usr/bin/env python3
"""Materialize H002 train-only factor feature and target datasets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_TARGETS = RGA_ROOT / "factor_contract/factor_targets.jsonl"
DEFAULT_CONTRACT = RGA_ROOT / "factor_contract/factor_contract.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "factor_dataset"

SUPPORTED_GEOMETRY_FAMILIES = {"proximity", "relative_vertical", "support_contact"}
FORBIDDEN_DEPLOYABLE_FEATURE_KEYS = {
    "label_match_status",
    "label_match",
    "family_match",
    "matched_gt_ids",
    "matched_predicates",
    "working_label",
    "human_final_audit_label",
    "strict_binary_target",
    "weak_binary_target",
    "soft_reliability_target",
    "action_target",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path):
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def prediction_id(row: dict[str, Any]) -> str:
    return str(row["identity"]["prediction_id"])


def load_targets(path: Path) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    duplicate_ids = 0
    for _, row in read_jsonl(path):
        pred_id = str(row["prediction_id"])
        if pred_id in targets:
            duplicate_ids += 1
        targets[pred_id] = row
    targets["_meta"] = {"duplicate_prediction_ids": duplicate_ids}  # type: ignore[assignment]
    return targets


def identity_block(row: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    predicate = row["predicate"]
    return {
        "prediction_id": identity["prediction_id"],
        "scan_id": identity["scan_id"],
        "subgraph_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "object_id": identity["object_id"],
        "predicate_label": predicate["predicate_label"],
        "predicate_family": predicate["predicate_family"],
        "source_id": row["source"]["source_id"],
        "split_name": row["source"]["split_name"],
    }


def status_one_hot(status: str, prefix: str) -> dict[str, int]:
    values = ["satisfied", "unsatisfied", "uncertain", "unsupported", "missing"]
    return {f"{prefix}_{value}": 1 if status == value else 0 for value in values}


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    semantic = row["semantic"]
    geometry = row["geometry"]
    rga = row["rga"]
    predicate = row["predicate"]
    source = row["source"]
    status = str(geometry["geometry_status"])
    family = str(predicate["predicate_family"])
    p_geom_valid = safe_float(geometry.get("p_geom_valid"))
    semantic_norm = safe_float(semantic.get("semantic_score_norm"))
    reason_codes = [str(item) for item in geometry.get("reason_codes") or []]
    raw_features = geometry.get("raw_features") or {}
    covered = status in {"satisfied", "unsatisfied", "uncertain"}
    supported_family = family in SUPPORTED_GEOMETRY_FAMILIES

    semantic_minus_geom = None
    if semantic_norm is not None and p_geom_valid is not None:
        semantic_minus_geom = semantic_norm - p_geom_valid

    return {
        "semantic_evidence": {
            "semantic_score_raw": safe_float(semantic.get("semantic_score_raw")),
            "semantic_score_norm": semantic_norm,
            "rank_in_context": safe_int(semantic.get("rank_in_context")),
            "predicate_rank_for_pair": safe_int(semantic.get("predicate_rank_for_pair")),
            "top50_semantic": bool(semantic.get("top50_semantic")),
            "top100_semantic": bool(semantic.get("top100_semantic")),
            "context_prediction_count": safe_int(semantic.get("context_prediction_count")),
            "predicate_label": predicate["predicate_label"],
            "predicate_family": family,
            "source_id": source["source_id"],
        },
        "geometry_evidence": {
            "geometry_status": status,
            **status_one_hot(status, "geometry_status"),
            "p_geom_valid": p_geom_valid,
            "p_geom_invalid": safe_float(geometry.get("p_geom_invalid")),
            "p_geom_valid_available": p_geom_valid is not None,
            "p_geom_valid_imputed_neutral": p_geom_valid if p_geom_valid is not None else 0.5,
            "consistency_score": safe_float(geometry.get("consistency_score")),
            "geometry_residual_proxy": safe_float(geometry.get("geometry_residual_proxy")),
            "reason_codes": reason_codes,
            "reason_code_count": len(reason_codes),
            "raw_features": raw_features,
            "raw_feature_count": len(raw_features),
            "selected_policy": geometry.get("selected_policy"),
        },
        "coverage_evidence": {
            "coverage_state": rga.get("coverage_state"),
            "geometry_available": bool(geometry.get("geometry_available")),
            "geometry_checkable": bool(geometry.get("geometry_checkable")),
            "predicate_family_supported": supported_family,
            "missing_geometry": status == "missing",
            "unsupported_family": status == "unsupported",
            "covered_checkable": covered,
            "visual_asset_available_for_audit": None,
        },
        "uncertainty_evidence": {
            "geometry_status_is_uncertain": status == "uncertain",
            "geometry_status_is_unsupported": status == "unsupported",
            "semantic_geometry_disagreement_score": safe_float(rga.get("disagreement_score")),
            "underconfidence_score": safe_float(rga.get("underconfidence_score")),
            "absolute_disagreement": safe_float(rga.get("absolute_disagreement")),
            "low_working_label_confidence_if_available": None,
            "abstain_reason_codes": reason_codes if status in {"uncertain", "unsupported", "missing"} else [],
        },
        "interactions": {
            "semantic_score_norm_minus_p_geom_valid": semantic_minus_geom,
            "top100_and_unsatisfied": bool(semantic.get("top100_semantic")) and status == "unsatisfied",
            "tail_gt100_and_satisfied": not bool(semantic.get("top100_semantic")) and status == "satisfied",
            "covered_and_uncertain": covered and status == "uncertain",
            "support_contact_x_p_geom_valid": p_geom_valid if family == "support_contact" else 0.0,
            "relative_vertical_x_p_geom_valid": p_geom_valid if family == "relative_vertical" else 0.0,
            "proximity_x_p_geom_valid": p_geom_valid if family == "proximity" else 0.0,
        },
    }


def flat_baseline_inputs(blocks: dict[str, Any]) -> dict[str, dict[str, Any]]:
    s = blocks["semantic_evidence"]
    g = blocks["geometry_evidence"]
    c = blocks["coverage_evidence"]
    u = blocks["uncertainty_evidence"]
    i = blocks["interactions"]

    semantic_only = {
        "semantic_score_raw": s["semantic_score_raw"],
        "semantic_score_norm": s["semantic_score_norm"],
        "rank_in_context": s["rank_in_context"],
        "predicate_rank_for_pair": s["predicate_rank_for_pair"],
        "top50_semantic": bool_int(s["top50_semantic"]),
        "top100_semantic": bool_int(s["top100_semantic"]),
        "predicate_label": s["predicate_label"],
        "predicate_family": s["predicate_family"],
        "source_id": s["source_id"],
    }
    geometry_only = {
        "geometry_status": g["geometry_status"],
        "geometry_status_satisfied": g["geometry_status_satisfied"],
        "geometry_status_unsatisfied": g["geometry_status_unsatisfied"],
        "geometry_status_uncertain": g["geometry_status_uncertain"],
        "geometry_status_unsupported": g["geometry_status_unsupported"],
        "p_geom_valid_imputed_neutral": g["p_geom_valid_imputed_neutral"],
        "p_geom_valid_available": bool_int(g["p_geom_valid_available"]),
        "p_geom_invalid": g["p_geom_invalid"],
        "consistency_score": g["consistency_score"],
        "geometry_residual_proxy": g["geometry_residual_proxy"],
        "geometry_available": bool_int(c["geometry_available"]),
        "geometry_checkable": bool_int(c["geometry_checkable"]),
        "predicate_family_supported": bool_int(c["predicate_family_supported"]),
        "unsupported_family": bool_int(c["unsupported_family"]),
        "missing_geometry": bool_int(c["missing_geometry"]),
    }
    semantic_plus_geometry = {**semantic_only, **geometry_only}
    factorized = {
        **semantic_plus_geometry,
        "coverage_state": c["coverage_state"],
        "covered_checkable": bool_int(c["covered_checkable"]),
        "geometry_status_is_uncertain": bool_int(u["geometry_status_is_uncertain"]),
        "geometry_status_is_unsupported": bool_int(u["geometry_status_is_unsupported"]),
        "semantic_geometry_disagreement_score": u["semantic_geometry_disagreement_score"],
        "underconfidence_score": u["underconfidence_score"],
        "absolute_disagreement": u["absolute_disagreement"],
        "semantic_score_norm_minus_p_geom_valid": i["semantic_score_norm_minus_p_geom_valid"],
        "top100_and_unsatisfied": bool_int(i["top100_and_unsatisfied"]),
        "tail_gt100_and_satisfied": bool_int(i["tail_gt100_and_satisfied"]),
        "covered_and_uncertain": bool_int(i["covered_and_uncertain"]),
        "support_contact_x_p_geom_valid": i["support_contact_x_p_geom_valid"],
        "relative_vertical_x_p_geom_valid": i["relative_vertical_x_p_geom_valid"],
        "proximity_x_p_geom_valid": i["proximity_x_p_geom_valid"],
    }
    return {
        "semantic_only": semantic_only,
        "geometry_only": geometry_only,
        "semantic_plus_geometry": semantic_plus_geometry,
        "factorized_reliability_posterior": factorized,
    }


def deployable_feature_row(row: dict[str, Any]) -> dict[str, Any]:
    blocks = feature_blocks(row)
    return {
        "schema_version": "h002_deployable_feature_row_v0",
        "record_type": "h002_deployable_features",
        "identity": identity_block(row),
        "feature_blocks": blocks,
        "baseline_inputs": flat_baseline_inputs(blocks),
        "leakage_boundary": "No label/audit evidence is included in deployable features.",
    }


def target_block(target: dict[str, Any], target_mode: str) -> dict[str, Any]:
    y_key = f"{target_mode}_target"
    if target_mode == "strict_binary":
        y_value = target.get("strict_binary_target")
    elif target_mode == "weak_binary":
        y_value = target.get("weak_binary_target")
    else:
        raise ValueError(f"unknown target mode: {target_mode}")
    return {
        "target_mode": target_mode,
        "y": y_value,
        "sample_weight": target.get("sample_weight"),
        "working_label": target.get("working_label"),
        "working_label_confidence": target.get("working_label_confidence"),
        "action_target": target.get("action_target"),
        "target_source": target.get("target_source"),
        "paper_locked": target.get("paper_locked"),
        "human_confirmed": target.get("human_confirmed"),
        "target_key": y_key,
        "leakage_boundary": target.get("leakage_boundary"),
    }


def smoke_row(feature_row: dict[str, Any], target: dict[str, Any], target_mode: str) -> dict[str, Any]:
    return {
        "schema_version": "h002_factor_smoke_row_v0",
        "record_type": "h002_factor_smoke_row",
        "identity": feature_row["identity"],
        "baseline_inputs": feature_row["baseline_inputs"],
        "target": target_block(target, target_mode),
        "provenance": {
            "feature_source": "deployable_features_all.jsonl",
            "target_source": "factor_targets.jsonl",
            "split_policy": "train_only_no_validation",
        },
    }


def joined_target_row(feature_row: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_factor_target_joined_v0",
        "record_type": "h002_factor_target_joined",
        "identity": feature_row["identity"],
        "feature_blocks": feature_row["feature_blocks"],
        "baseline_inputs": feature_row["baseline_inputs"],
        "target": {
            "strict_binary_target": target.get("strict_binary_target"),
            "weak_binary_target": target.get("weak_binary_target"),
            "soft_reliability_target": target.get("soft_reliability_target"),
            "action_target": target.get("action_target"),
            "sample_weight": target.get("sample_weight"),
            "working_label": target.get("working_label"),
            "working_label_confidence": target.get("working_label_confidence"),
            "target_source": target.get("target_source"),
            "paper_locked": target.get("paper_locked"),
            "human_confirmed": target.get("human_confirmed"),
        },
        "leakage_boundary": "Target block is supervised label metadata, not deployable input.",
    }


def find_forbidden_keys(value: Any, path: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_DEPLOYABLE_FEATURE_KEYS:
                found.add(f"{path}.{key}" if path else key)
            found.update(find_forbidden_keys(child, f"{path}.{key}" if path else key))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.update(find_forbidden_keys(child, f"{path}[{idx}]"))
    return found


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Factor Dataset",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Outputs",
        "",
        "| Artifact | Rows |",
        "| --- | ---: |",
        f"| deployable_features_all.jsonl | {summary['counts']['feature_rows']} |",
        f"| target_joined.jsonl | {summary['counts']['target_joined_rows']} |",
        f"| strict_smoke.jsonl | {summary['counts']['strict_smoke_rows']} |",
        f"| weak_smoke.jsonl | {summary['counts']['weak_smoke_rows']} |",
        "",
        "## Target Counts",
        "",
        "| Target | Positive | Negative |",
        "| --- | ---: | ---: |",
        f"| strict | {summary['targets']['strict_positive']} | {summary['targets']['strict_negative']} |",
        f"| weak | {summary['targets']['weak_positive']} | {summary['targets']['weak_negative']} |",
        "",
        "## Leakage Check",
        "",
        f"- forbidden deployable feature keys: `{summary['validation']['forbidden_deployable_feature_keys']}`",
        f"- missing target joins: `{summary['validation']['missing_target_joins']}`",
        f"- extra targets not found in features: `{summary['validation']['extra_targets_not_found']}`",
        "",
        "## Boundary",
        "",
        "All rows are train-only. Label/audit evidence appears only in target blocks, not in deployable feature blocks.",
        "",
        "## Next Gate",
        "",
        "`27_factor_smoke.md`: fit train-only smoke baselines and report only hypothesis-stage diagnostics.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_dataset(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = load_targets(args.targets)
    target_meta = targets.pop("_meta")  # type: ignore[arg-type]
    contract = read_json(args.contract)
    created_at = datetime.now(timezone.utc).isoformat()

    paths = {
        "deployable_features_all": output_dir / "deployable_features_all.jsonl",
        "target_joined": output_dir / "target_joined.jsonl",
        "strict_smoke": output_dir / "strict_smoke.jsonl",
        "weak_smoke": output_dir / "weak_smoke.jsonl",
        "summary": output_dir / "dataset_summary.json",
        "schema": output_dir / "schema.json",
        "report": output_dir / "report.md",
    }

    counts = Counter()
    targets_seen: set[str] = set()
    forbidden_keys: set[str] = set()
    status_counts = Counter()
    family_counts = Counter()
    strict_counts = Counter()
    weak_counts = Counter()

    with (
        paths["deployable_features_all"].open("w", encoding="utf-8") as all_handle,
        paths["target_joined"].open("w", encoding="utf-8") as joined_handle,
        paths["strict_smoke"].open("w", encoding="utf-8") as strict_handle,
        paths["weak_smoke"].open("w", encoding="utf-8") as weak_handle,
    ):
        for _, row in read_jsonl(args.match_rows):
            feature_row = deployable_feature_row(row)
            pred_id = feature_row["identity"]["prediction_id"]
            all_handle.write(json.dumps(feature_row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
            counts["feature_rows"] += 1
            status_counts[feature_row["feature_blocks"]["geometry_evidence"]["geometry_status"]] += 1
            family_counts[feature_row["identity"]["predicate_family"]] += 1
            if counts["feature_rows"] <= 10:
                forbidden_keys.update(find_forbidden_keys(feature_row["feature_blocks"]))
                forbidden_keys.update(find_forbidden_keys(feature_row["baseline_inputs"]))

            target = targets.get(pred_id)
            if target is None:
                continue
            targets_seen.add(pred_id)
            joined = joined_target_row(feature_row, target)
            joined_handle.write(json.dumps(joined, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
            counts["target_joined_rows"] += 1

            strict_y = target.get("strict_binary_target")
            if strict_y is not None:
                strict_handle.write(
                    json.dumps(smoke_row(feature_row, target, "strict_binary"), sort_keys=True, ensure_ascii=False) + "\n"
                )
                counts["strict_smoke_rows"] += 1
                strict_counts["positive" if strict_y == 1 else "negative"] += 1

            weak_y = target.get("weak_binary_target")
            if weak_y is not None:
                weak_handle.write(
                    json.dumps(smoke_row(feature_row, target, "weak_binary"), sort_keys=True, ensure_ascii=False) + "\n"
                )
                counts["weak_smoke_rows"] += 1
                weak_counts["positive" if weak_y == 1 else "negative"] += 1

    missing_targets = sorted(set(targets) - targets_seen)
    summary = {
        "schema_version": "h002_factor_dataset_v0",
        "status": "ready" if not forbidden_keys and not missing_targets else "blocked",
        "created_at": created_at,
        "input_paths": {
            "match_rows": rel_path(args.match_rows),
            "targets": rel_path(args.targets),
            "contract": rel_path(args.contract),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "counts": {
            "feature_rows": counts["feature_rows"],
            "target_joined_rows": counts["target_joined_rows"],
            "strict_smoke_rows": counts["strict_smoke_rows"],
            "weak_smoke_rows": counts["weak_smoke_rows"],
            "target_input_rows": len(targets),
            "target_duplicate_prediction_ids": target_meta["duplicate_prediction_ids"],
        },
        "targets": {
            "strict_positive": strict_counts["positive"],
            "strict_negative": strict_counts["negative"],
            "weak_positive": weak_counts["positive"],
            "weak_negative": weak_counts["negative"],
        },
        "feature_distribution": {
            "geometry_status": dict(sorted(status_counts.items())),
            "predicate_family": dict(sorted(family_counts.items())),
        },
        "baseline_inputs": contract["baseline_contract"]["minimum_main_table_conditions"],
        "validation": {
            "forbidden_deployable_feature_keys": sorted(forbidden_keys),
            "missing_target_joins": len(missing_targets),
            "extra_targets_not_found": missing_targets[:20],
            "checked_forbidden_feature_rows": min(10, counts["feature_rows"]),
            "validation_usage": "none",
        },
        "boundary": {
            "split": "train_only",
            "not_paper_result": True,
            "label_evidence_as_input": False,
            "target_labels_are_machine_assisted": True,
            "human_confirmed": False,
        },
    }

    schema = {
        "schema_version": "h002_factor_dataset_schema_v0",
        "deployable_feature_row": {
            "identity": "non-label row identity fields",
            "feature_blocks": [
                "semantic_evidence",
                "geometry_evidence",
                "coverage_evidence",
                "uncertainty_evidence",
                "interactions",
            ],
            "baseline_inputs": contract["baseline_contract"]["minimum_main_table_conditions"],
            "forbidden_deployable_feature_keys": sorted(FORBIDDEN_DEPLOYABLE_FEATURE_KEYS),
        },
        "target_joined_row": {
            "feature_blocks": "same deployable feature blocks",
            "target": "strict/weak/soft/action target metadata; not deployable input",
        },
    }
    write_json(paths["summary"], summary)
    write_json(paths["schema"], schema)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = build_dataset(args)
    print(
        f"status={summary['status']} features={summary['counts']['feature_rows']} "
        f"targets={summary['counts']['target_joined_rows']} "
        f"strict={summary['counts']['strict_smoke_rows']} weak={summary['counts']['weak_smoke_rows']} "
        f"output={as_abs(args.output_dir)}"
    )
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
