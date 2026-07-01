#!/usr/bin/env python3
"""Write the size-relative train-only sanitized-view smoke plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit"

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit"
EXPECTED_INPUT_SCHEMA = "h002_size_relative_smoke_ready_view_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_v1"
SMOKE_READY_SCHEMA = "h002_size_relative_runner_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_input_errors"
NEXT_TODO = "compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan"

EXPECTED_ROWS = 2400
EXPECTED_GROUPS = 1200
EXPECTED_POSITIVE = 1200
EXPECTED_NEGATIVE = 1200
EXPECTED_PREDICATES = {"bigger than": 1200, "smaller than": 1200}
EXPECTED_FEATURE_BLOCKS = {"G_e_size", "T_e"}

NEAR_CHANCE_AUROC_MAX = 0.60
PRIMARY_AUROC_MIN = 0.95
PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN = 0.30
CONTROL_AUROC_MAX = 0.60
PAIRED_SCORE_MARGIN_PASS_RATE_MIN = 0.90

FORBIDDEN_FEATURE_TOKENS = [
    "anchor",
    "candidate_component",
    "class",
    "construction",
    "direction_by",
    "directed_pair",
    "gt_",
    "object_id",
    "scan_id",
    "source",
    "subgraph",
    "subject_id",
    "volume_ratio_band",
    "z_e",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str, prefix: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def feature_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        out: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.append(child_prefix)
            out.extend(feature_paths(child, child_prefix))
        return out
    return [prefix]


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row["row_id"])
        normalized.append(
            {
                "schema_version": SMOKE_READY_SCHEMA,
                "dataset_name": row["dataset_name"],
                "example_id": stable_hash(row_id, "ex"),
                "row_id": row_id,
                "cv_group_id": str(row["cv_group"]),
                "split": "train",
                "target_name": "C_e",
                "target_y": int(row["labels"]["C_e"]),
                "feature_blocks": row["feature_blocks"],
                "metadata_note": "row_id/cv_group_id/target_y are metadata or target only; not feature input",
            }
        )
    return normalized


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(int(row["target_y"]) for row in rows)
    predicates = Counter(str(nested_get(row, "feature_blocks.T_e.predicate_label")) for row in rows)
    schemas = Counter(str(row.get("schema_version")) for row in rows)
    blocks = Counter(tuple(sorted(row.get("feature_blocks", {}).keys())) for row in rows)
    by_group: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        by_group[str(row["cv_group_id"])].append(int(row["target_y"]))
    paired_groups = sum(1 for values in by_group.values() if sorted(values) == [0, 1])
    two_row_groups = sum(1 for values in by_group.values() if len(values) == 2)
    return {
        "rows": len(rows),
        "positive": labels[1],
        "negative": labels[0],
        "cv_groups": len(by_group),
        "two_row_cv_groups": two_row_groups,
        "paired_groups_with_one_positive_one_negative": paired_groups,
        "predicate_counts": dict(sorted(predicates.items())),
        "schema_versions": dict(sorted(schemas.items())),
        "feature_block_sets": {",".join(key): count for key, count in sorted(blocks.items())},
    }


def validate_inputs(audit_summary: dict[str, Any], raw_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]], audit_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if int(audit_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("gate", {}).get("smoke_ready") is not True:
        errors.append({"error_type": "audit_not_smoke_ready", "gate": audit_summary.get("gate", {})})
    if audit_summary.get("boundary", {}).get("validation_usage") is not False or audit_summary.get("boundary", {}).get("test_usage") is not False:
        errors.append({"error_type": "audit_boundary_used_validation_or_test", "boundary": audit_summary.get("boundary", {})})
    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors_file", "path": rel_path(validation_path)})

    raw_schema_counts = Counter(str(row.get("schema_version")) for row in raw_rows)
    if raw_schema_counts != Counter({EXPECTED_INPUT_SCHEMA: EXPECTED_ROWS}):
        errors.append({"error_type": "unexpected_raw_schema_counts", "actual": dict(raw_schema_counts)})

    counts = count_summary(smoke_rows)
    if counts["rows"] != EXPECTED_ROWS or counts["positive"] != EXPECTED_POSITIVE or counts["negative"] != EXPECTED_NEGATIVE:
        errors.append({"error_type": "unexpected_row_or_label_counts", **counts})
    if counts["cv_groups"] != EXPECTED_GROUPS or counts["two_row_cv_groups"] != EXPECTED_GROUPS:
        errors.append({"error_type": "unexpected_cv_group_counts", **counts})
    if counts["paired_groups_with_one_positive_one_negative"] != EXPECTED_GROUPS:
        errors.append({"error_type": "unexpected_paired_group_counts", **counts})
    if counts["predicate_counts"] != EXPECTED_PREDICATES:
        errors.append({"error_type": "unexpected_predicate_counts", **counts})
    if counts["schema_versions"] != {SMOKE_READY_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_smoke_schema_versions", **counts})

    for row in smoke_rows:
        feature_blocks = row.get("feature_blocks", {})
        if set(feature_blocks) != EXPECTED_FEATURE_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row.get("row_id"), "blocks": sorted(feature_blocks)})
        feature_text = json.dumps(feature_blocks, ensure_ascii=False, sort_keys=True).lower()
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_token_in_feature_blocks", "row_id": row.get("row_id"), "token": token})
        for field in [
            "feature_blocks.G_e_size.log_footprint_area_ratio_s_over_o",
            "feature_blocks.G_e_size.log_max_extent_ratio_s_over_o",
            "feature_blocks.G_e_size.log_vertical_extent_ratio_s_over_o",
            "feature_blocks.G_e_size.log_volume_ratio_s_over_o",
        ]:
            value = nested_get(row, field)
            if not isinstance(value, (int, float)):
                errors.append({"error_type": "non_numeric_geometry_feature", "row_id": row.get("row_id"), "field": field, "value": value})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.predicate_text",
        "feature_blocks.T_e.relation_family",
        "feature_blocks.G_e_size.log_footprint_area_ratio_s_over_o",
        "feature_blocks.G_e_size.log_max_extent_ratio_s_over_o",
        "feature_blocks.G_e_size.log_vertical_extent_ratio_s_over_o",
        "feature_blocks.G_e_size.log_volume_ratio_s_over_o",
    ]
    out: list[dict[str, Any]] = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        finite = 0
        for value in values:
            try:
                float(value)
            except (TypeError, ValueError):
                continue
            finite += 1
        out.append(
            {
                "feature_path": path,
                "rows": len(rows),
                "missing": missing,
                "distinct_values": distinct,
                "finite_numeric": finite,
                "usable_as_feature": True,
            }
        )
    return out


def feature_path_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = sorted({path for row in rows for path in feature_paths(row.get("feature_blocks", {}), "feature_blocks")})
    return [{"feature_path": path, "model_input_allowed": True} for path in paths]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {"model": "M0_intercept", "input_blocks": "none", "primary": False, "role": "class-balance sanity baseline"},
        {"model": "M1_semantic_only_T", "input_blocks": "T_e", "primary": False, "role": "predicate/family semantic-only shortcut baseline"},
        {"model": "M2_geometry_only_G_size", "input_blocks": "G_e_size", "primary": False, "role": "predicate-independent size geometry baseline; should be near chance"},
        {"model": "M3_TG_concat_no_interaction", "input_blocks": "T_e + G_e_size", "primary": False, "role": "plain concatenation without explicit predicate-conditioned products"},
        {"model": "M4_TG_size_interaction", "input_blocks": "T_e + G_e_size", "primary": True, "role": "primary predicate-geometry compatibility smoke"},
        {"model": "S1_predicate_label_shortcut", "input_blocks": "T_e.predicate_label", "primary": False, "role": "single visible predicate shortcut probe"},
        {"model": "S2_geometry_exact_tuple_shortcut", "input_blocks": "G_e_size exact tuple", "primary": False, "role": "same-G paired construction should make exact geometry tuple uninformative"},
        {"model": "C1_wrong_T_same_G", "input_blocks": "wrong T_e + same G_e_size", "primary": False, "role": "predicate-conditioning negative control"},
        {"model": "C2_shuffled_G_global", "input_blocks": "T_e + globally shuffled G_e_size", "primary": False, "role": "geometry-alignment negative control"},
        {"model": "C3_shuffled_G_within_predicate", "input_blocks": "T_e + within-predicate shuffled G_e_size", "primary": False, "role": "harder geometry-alignment control"},
        {"model": "C4_sign_flipped_G_control", "input_blocks": "T_e + sign-flipped G_e_size", "primary": False, "role": "directional size-evidence inversion control"},
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {"gate": "data_integrity", "criterion": "rows=2400, labels=1200/1200, 1200 two-row cv groups, each group has one positive and one negative", "blocks_runner_if_fail": True},
        {"gate": "schema_safety", "criterion": "runner reads only smoke_ready_view.jsonl feature_blocks; row_id/cv_group_id/target_y are metadata or target only", "blocks_runner_if_fail": True},
        {"gate": "single_factor_shortcut_control", "criterion": f"M1/M2/S1/S2 AUROC <= {NEAR_CHANCE_AUROC_MAX:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "plain_concat_boundary", "criterion": "M3 is diagnostic; if M3 solves the task, report that explicit interaction is unnecessary for this family", "blocks_paper_claim_if_fail": True},
        {"gate": "primary_interaction_signal", "criterion": f"M4 AUROC >= {PRIMARY_AUROC_MIN:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "interaction_gain", "criterion": f"M4 beats max(M1, M2, S1, S2) by >= {PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN:.2f} AUROC", "blocks_promotion_if_fail": True},
        {"gate": "wrong_T_degradation", "criterion": f"C1 wrong-T same-G should degrade to <= {CONTROL_AUROC_MAX:.2f} AUROC or invert", "blocks_promotion_if_fail": True},
        {"gate": "shuffled_G_degradation", "criterion": f"C2/C3 shuffled-G should degrade to <= {CONTROL_AUROC_MAX:.2f} AUROC", "blocks_promotion_if_fail": True},
        {"gate": "sign_flip_control", "criterion": "C4 sign-flipped G should invert or strongly degrade compatibility scores", "blocks_promotion_if_fail": True},
        {"gate": "paired_score_margin", "criterion": f"score(compatible)-score(incompatible) > 0 in at least {PAIRED_SCORE_MARGIN_PASS_RATE_MIN:.2f} of groups", "blocks_promotion_if_fail": True},
        {"gate": "paper_boundary", "criterion": "train-only hypothesis smoke; Docker reproduction and held-out protocol required before paper evidence", "blocks_paper_evidence": True},
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {"control": "wrong_T_same_G", "construction": "swap bigger than <-> smaller than in T_e while keeping G_e_size and target", "expected_result": "predicate-conditioned compatibility should degrade or invert"},
        {"control": "shuffled_G_global", "construction": "permute G_e_size across all rows with a deterministic seed", "expected_result": "breaks aligned object-pair size evidence"},
        {"control": "shuffled_G_within_predicate", "construction": "permute G_e_size within each predicate label", "expected_result": "preserves predicate distribution while breaking paired geometry"},
        {"control": "sign_flipped_G", "construction": "multiply all log-ratio G_e_size fields by -1", "expected_result": "inverts the size relation direction"},
        {"control": "no_interaction_concat", "construction": "compare M3 plain concat with M4 predicate-conditioned interaction", "expected_result": "tests whether explicit compatibility products are necessary"},
    ]


def smoke_plan(input_path: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": {
            "name": "size-relative predicate-geometry compatibility C_e smoke",
            "target": "target_y",
            "target_semantics": "1 if bigger/smaller predicate is compatible with the signed size-ratio geometry evidence",
            "not_in_scope": ["Z_e posterior", "p_rel final reliability", "p_obs abstention", "validation/test performance", "paper-level claim"],
        },
        "input_contract": {
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "row_count": EXPECTED_ROWS,
            "positive": EXPECTED_POSITIVE,
            "negative": EXPECTED_NEGATIVE,
            "group_key": "cv_group_id",
            "target": "target_y",
            "feature_root": "feature_blocks",
            "allowed_blocks": sorted(EXPECTED_FEATURE_BLOCKS),
            "metadata_only": ["dataset_name", "example_id", "row_id", "cv_group_id", "schema_version", "split", "target_name", "target_y", "metadata_note"],
            "forbidden_as_features": FORBIDDEN_FEATURE_TOKENS,
        },
        "split_policy": {
            "split": "train_internal_grouped_cv",
            "folds": 5,
            "group_key": "cv_group_id",
            "group_rule": "the compatible and incompatible row with identical G_e_size must remain in the same fold",
            "validation_usage": False,
            "test_usage": False,
        },
        "feature_engineering": {
            "T_e": "predicate label/text and relation family only",
            "G_e_size": "predicate-independent continuous log-ratio size geometry fields",
            "primary_interaction": "expected_size_sign(predicate) times each signed G_e_size log-ratio",
            "expected_size_sign": {"bigger than": 1, "smaller than": -1},
            "Z_e_policy": "excluded from this C_e smoke; source confidence remains outside compatibility",
            "Q_e_policy": "primary rows are observable; ambiguous size rows remain diagnostic and outside this smoke",
        },
        "models": model_view_rows(),
        "gates": gate_rows(),
        "controls": control_rows(),
        "metrics": ["AUROC", "AUPRC", "accuracy", "balanced_accuracy", "Brier", "ECE", "fold mean/std", "paired margin pass rate"],
        "paper_boundary": {
            "hypothesis_stage_only": True,
            "paper_evidence_allowed": False,
            "docker_required_before_paper_promotion": True,
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 Size-Relative Sanitized View Smoke Plan After Schema Audit

## Status

```text
artifact_root = {summary["output_paths"]["artifact_root"]}
status = {summary["status"]}
rows = {counts["rows"]}
positive / negative = {counts["positive"]} / {counts["negative"]}
cv_groups = {counts["cv_groups"]}
paired_groups = {counts["paired_groups_with_one_positive_one_negative"]}
predicate_counts = {json.dumps(counts["predicate_counts"], ensure_ascii=False, sort_keys=True)}
validation_errors = {summary["validation_errors"]}
learned_smoke_executed = false
next_todo = {summary["next_todo"]}
```

## Planned Main Comparison

- `M1_semantic_only_T`
- `M2_geometry_only_G_size`
- `M3_TG_concat_no_interaction`
- `M4_TG_size_interaction` as the primary compatibility smoke

## Required Controls

- wrong-T same-G
- shuffled-G global
- shuffled-G within predicate
- sign-flipped G
- no-interaction concat

## Interpretation

This step does not train a model. It freezes the train-only grouped-CV smoke input
and the comparison contract for `bigger than` / `smaller than`. The target is not
whether size geometry is useful by itself. The target is whether the same
predicate-independent `G_e_size` evidence changes meaning under different `T_e`
predicates.
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    raw_rows = read_jsonl(args.audit_dir / "smoke_ready_view.jsonl")
    smoke_rows = normalize_rows(raw_rows)
    validation_errors = validate_inputs(audit_summary, raw_rows, smoke_rows, args.audit_dir)
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    next_todo = NEXT_TODO if not validation_errors else "compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_repair"

    input_path = args.output_dir / "smoke_ready_view.jsonl"
    write_jsonl(input_path, smoke_rows)
    counts = count_summary(smoke_rows)
    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "control_plan": rel_path(args.output_dir / "control_plan.csv"),
        "feature_paths": rel_path(args.output_dir / "feature_paths.csv"),
        "gate_plan": rel_path(args.output_dir / "gate_plan.csv"),
        "input_manifest": rel_path(args.output_dir / "input_manifest.json"),
        "input_profile": rel_path(args.output_dir / "input_profile.csv"),
        "model_views": rel_path(args.output_dir / "model_views.csv"),
        "report": rel_path(args.output_dir / "report.md"),
        "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
        "smoke_ready_view": rel_path(input_path),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "learned_smoke_executed": False,
        "smoke_runner_implementation_allowed": not validation_errors,
        "primary_model": "M4_TG_size_interaction",
        "near_chance_auroc_max": NEAR_CHANCE_AUROC_MAX,
        "primary_auroc_min": PRIMARY_AUROC_MIN,
        "primary_gain_over_single_factor_min": PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN,
        "counts": counts,
        "input_paths": {
            "audit_summary": rel_path(args.audit_dir / "summary.json"),
            "audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
        },
        "output_paths": output_paths,
        "boundary": {
            "split": "train_only_smoke_plan",
            "materializes_new_rows": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "source_score_used": False,
            "q_e_used_as_truth": False,
        },
    }
    input_manifest = {
        "schema_version": "h002_size_relative_smoke_input_manifest_v1",
        "input_sha256": sha256_file(input_path),
        "input_rows": counts["rows"],
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
        "source_audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
        "runner_ready_schema": SMOKE_READY_SCHEMA,
    }

    write_csv(args.output_dir / "control_plan.csv", control_rows())
    write_csv(args.output_dir / "feature_paths.csv", feature_path_rows(smoke_rows))
    write_csv(args.output_dir / "gate_plan.csv", gate_rows())
    write_json(args.output_dir / "input_manifest.json", input_manifest)
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(smoke_rows))
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_json(args.output_dir / "smoke_plan.json", smoke_plan(input_path))
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
