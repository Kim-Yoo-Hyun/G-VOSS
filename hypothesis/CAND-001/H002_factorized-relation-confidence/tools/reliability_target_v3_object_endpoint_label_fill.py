#!/usr/bin/env python3
"""Fill the object/endpoint-controlled H002 reliability target v3 sheet."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v3_label_fill as base_fill


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

MINING_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_candidate_mining"
DEFAULT_INPUT_SHEET = MINING_DIR / "object_endpoint_label_sheet.tsv"
DEFAULT_SCHEMA = MINING_DIR / "v3_label_schema.json"
DEFAULT_MANIFEST = MINING_DIR / "object_endpoint_manifest_post_label_only.jsonl"
DEFAULT_MINING_SUMMARY = MINING_DIR / "summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested"

SCHEMA_VERSION = "h002_reliability_target_v3_object_endpoint_label_fill_summary_v1"
STATUS_READY = "h002_reliability_target_v3_object_endpoint_label_filled_codex_proxy_user_requested"
STATUS_ERROR = "h002_reliability_target_v3_object_endpoint_label_fill_errors"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--mining-summary", type=Path, default=DEFAULT_MINING_SUMMARY)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(mining_summary: dict[str, Any], visible_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if mining_summary.get("next_todo") != "reliability_target_v3_object_endpoint_label_fill":
        errors.append({"error_type": "unexpected_mining_next_todo", "value": mining_summary.get("next_todo")})
    boundary = mining_summary.get("boundary", {})
    if boundary.get("validation_usage") is not False:
        errors.append({"error_type": "mining_validation_usage_not_false"})
    if boundary.get("test_usage") is not False:
        errors.append({"error_type": "mining_test_usage_not_false"})
    if boundary.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "mining_posterior_smoke_not_false"})

    visible_ids = [str(row.get("blind_review_id") or "") for row in visible_rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(visible_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_visible_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})
    visible_set = {blind_id for blind_id in visible_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(visible_set - manifest_set):
        errors.append({"error_type": "visible_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - visible_set):
        errors.append({"error_type": "manifest_id_missing_from_visible_sheet", "blind_review_id": blind_id})
    return errors


def fill_visible_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    filled_rows = []
    for row in rows:
        filled = base_fill.fill_row(row)
        filled["label_notes_v3"] = (
            "codex proxy object/endpoint-controlled v3 fill; label decision used only visible "
            "subject/object/predicate identity and packet availability heuristic; hidden sampling "
            "manifest was not used before label lock"
        )
        filled_rows.append(filled)
    return filled_rows


def label_record(row: dict[str, Any]) -> dict[str, Any]:
    record = base_fill.label_record(row)
    record["schema_version"] = "h002_reliability_target_v3_object_endpoint_proxy_label_v1"
    record["provenance"]["batch_name"] = "reliability_target_v3_object_endpoint_label_fill"
    record["provenance"]["object_endpoint_controlled_sheet"] = True
    return record


def hidden(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest.get("hidden_sampling_axes_post_label_only", {}))


def diagnostic_group_value(manifest: dict[str, Any], group_key: str) -> str:
    if group_key in manifest:
        return str(manifest.get(group_key))
    hidden_fields = hidden(manifest)
    if group_key in hidden_fields:
        return str(hidden_fields.get(group_key))
    return "missing"


def grouped_diagnostics(
    filled_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    group_key: str,
) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filled_rows:
        manifest = manifest_by_id.get(str(row["blind_review_id"]), {})
        grouped[diagnostic_group_value(manifest, group_key)].append(row)

    diagnostics = []
    for value, rows in sorted(grouped.items()):
        reliability = Counter(row["relation_reliability_v3"] for row in rows)
        geometry = Counter(row["geometry_support_v3"] for row in rows)
        usefulness = Counter(row["relation_usefulness_v3"] for row in rows)
        diagnostics.append(
            {
                "group_key_post_label_only": group_key,
                "group_value": value,
                "rows": len(rows),
                "reliable": reliability.get("reliable", 0),
                "unreliable_geometry": reliability.get("unreliable_geometry", 0),
                "unreliable_trivial": reliability.get("unreliable_trivial", 0),
                "unreliable_ontology": reliability.get("unreliable_ontology", 0),
                "uncertain": reliability.get("uncertain", 0),
                "geometry_support_counts": json.dumps(dict(sorted(geometry.items())), sort_keys=True),
                "relation_usefulness_counts": json.dumps(dict(sorted(usefulness.items())), sort_keys=True),
            }
        )
    return diagnostics


def all_post_label_diagnostics(filled_rows: list[dict[str, Any]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for group_key in [
        "sampling_category_hidden",
        "sampling_proxy_label_key_hidden",
        "sampling_cell_type_hidden",
        "sampling_tier_hidden",
        "endpoint_flag_pattern_hidden",
        "candidate_proxy_class_hidden",
    ]:
        diagnostics.extend(grouped_diagnostics(filled_rows, manifest_rows, group_key))
    return diagnostics


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    reliability = counts["relation_reliability_v3"]
    geometry = counts["geometry_support_v3"]
    usefulness = counts["relation_usefulness_v3"]
    lines = [
        "# H002 Reliability Target V3 Object/Endpoint Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Filled by Codex proxy at user request; this is not independent human annotation.",
        "- Label decisions use only labeler-visible identity fields and packet path availability.",
        "- Hidden sampling tier/cell, proxy class, semantic score/rank, `p_geom_valid`, geometry status, label-match status, endpoint pattern, and numeric witness values are not used for label decisions.",
        "- Hidden manifest is joined only after label fill for diagnostics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| reliable | {reliability.get('reliable', 0)} |",
        f"| unreliable_geometry | {reliability.get('unreliable_geometry', 0)} |",
        f"| unreliable_trivial | {reliability.get('unreliable_trivial', 0)} |",
        f"| unreliable_ontology | {reliability.get('unreliable_ontology', 0)} |",
        f"| uncertain | {reliability.get('uncertain', 0)} |",
        f"| validation errors | {counts['validation_errors']} |",
        f"| input validation errors | {counts['input_validation_errors']} |",
        "",
        "## Geometry Support",
        "",
        "| Geometry support | Count |",
        "| --- | ---: |",
    ]
    for key, value in geometry.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Relation Usefulness", "", "| Usefulness | Count |", "| --- | ---: |"])
    for key, value in usefulness.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_sheet = as_abs(args.input_sheet)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    mining_summary_path = as_abs(args.mining_summary)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    fieldnames, visible_rows = read_tsv(input_sheet)
    schema = read_json(schema_path)
    manifest_rows = read_jsonl(manifest_path)
    mining_summary = read_json(mining_summary_path)

    input_errors = validate_inputs(mining_summary, visible_rows, manifest_rows)
    filled_rows = fill_visible_rows(visible_rows)
    fill_errors = base_fill.validate_rows(filled_rows, schema)
    label_rows = [label_record(row) for row in filled_rows]
    post_label_diagnostics = all_post_label_diagnostics(filled_rows, manifest_rows)

    reliability_counts = Counter(row["relation_reliability_v3"] for row in filled_rows)
    geometry_counts = Counter(row["geometry_support_v3"] for row in filled_rows)
    usefulness_counts = Counter(row["relation_usefulness_v3"] for row in filled_rows)
    family_counts = Counter(row["predicate_family"] for row in filled_rows)
    endpoint_counts = Counter(row["endpoint_identity_v3"] for row in filled_rows)
    evaluability_counts = Counter(row["pair_evaluability_v3"] for row in filled_rows)
    primary_counts = Counter(row["primary_reason_v3"] for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_object_endpoint_label_sheet_codex_proxy_user_requested.tsv",
        "v3_proxy_labels": output_dir / "object_endpoint_v3_proxy_labels.jsonl",
        "post_label_diagnostics": output_dir / "post_label_diagnostics.csv",
        "post_label_diagnostics_json": output_dir / "post_label_diagnostics.json",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
        "input_validation_errors": output_dir / "input_validation_errors.jsonl",
    }

    errors = input_errors + fill_errors
    status = STATUS_ERROR if errors else STATUS_READY
    next_todo = (
        "fix_reliability_target_v3_object_endpoint_label_fill"
        if errors
        else "reliability_target_v3_object_endpoint_label_ingestion"
    )
    decision = (
        "Input or fill validation errors block ingestion."
        if errors
        else (
            "Filled the object/endpoint-controlled v3 sheet as a user-requested Codex proxy. "
            "This creates hypothesis-stage labels for ingestion and target-independence audit, "
            "but it is not independent human evidence and does not unlock posterior smoke by itself."
        )
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "object_endpoint_label_sheet": rel_path(input_sheet),
            "v3_label_schema": rel_path(schema_path),
            "post_label_manifest": rel_path(manifest_path),
            "candidate_mining_summary": rel_path(mining_summary_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "user_requested_proxy_fill": True,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "used_hidden_manifest_for_label_decision": False,
            "used_sampling_category_for_label_decision": False,
            "used_expected_role_for_label_decision": False,
            "used_candidate_proxy_class_for_label_decision": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_geometry_status": False,
            "used_label_match_status": False,
            "used_endpoint_flag_pattern": False,
            "used_numeric_witness_values": False,
            "post_label_hidden_manifest_diagnostic_join": True,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "input_validation_errors": len(input_errors),
            "validation_errors": len(fill_errors),
            "by_family": dict(sorted(family_counts.items())),
            "endpoint_identity_v3": dict(sorted(endpoint_counts.items())),
            "pair_evaluability_v3": dict(sorted(evaluability_counts.items())),
            "geometry_support_v3": dict(sorted(geometry_counts.items())),
            "relation_usefulness_v3": dict(sorted(usefulness_counts.items())),
            "relation_reliability_v3": dict(sorted(reliability_counts.items())),
            "primary_reason_v3": dict(sorted(primary_counts.items())),
        },
        "post_label_diagnostics": post_label_diagnostics,
        "next_todo": next_todo,
    }

    write_tsv(output_paths["completed_sheet"], filled_rows, fieldnames)
    write_jsonl(output_paths["v3_proxy_labels"], label_rows)
    write_csv(output_paths["post_label_diagnostics"], post_label_diagnostics)
    write_json(output_paths["post_label_diagnostics_json"], {"diagnostics": post_label_diagnostics})
    write_jsonl(output_paths["fill_validation_errors"], fill_errors)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["relation_reliability_v3"]
    print(
        "status={status} rows={rows} reliable={reliable} unreliable_geometry={unreliable_geometry} "
        "unreliable_trivial={unreliable_trivial} unreliable_ontology={unreliable_ontology} "
        "uncertain={uncertain} input_errors={input_errors} errors={errors} validation_used={validation_used} "
        "test_used={test_used} posterior_allowed={posterior_allowed} next={next_todo}".format(
            status=summary["status"],
            rows=counts["rows"],
            reliable=reliability.get("reliable", 0),
            unreliable_geometry=reliability.get("unreliable_geometry", 0),
            unreliable_trivial=reliability.get("unreliable_trivial", 0),
            unreliable_ontology=reliability.get("unreliable_ontology", 0),
            uncertain=reliability.get("uncertain", 0),
            input_errors=counts["input_validation_errors"],
            errors=counts["validation_errors"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
