#!/usr/bin/env python3
"""Validate the H001 Qwen-VL JSONL contracts and parser skeleton."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA_VERSION = "h001_qwen_vl_contract_validation_v1"
PARSER_CONTRACT_VERSION = "h001_qwen_vl_parser_skeleton_v1"
BASELINE_NAME = "qwen_vl_semantic_source"
DEFAULT_MODEL_ID = "CONTRACT_ONLY_NO_MODEL_RUNTIME"
DEFAULT_MODEL_REVISION = "CONTRACT_ONLY_NO_MODEL_RUNTIME"
BANNED_SEMANTIC_SCORE_KEYS = {
    "p_geom_valid",
    "geometry_score",
    "verifier_decision",
    "verifier_label",
    "violation_label",
    "ground_truth",
    "ground_truth_label",
    "gt_label",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/validation"),
    )
    parser.add_argument("--input-jsonl", type=Path)
    parser.add_argument("--raw-response-jsonl", type=Path)
    parser.add_argument("--baseline-run-id", default="qwen_vl_contract_parser_skeleton")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-revision", default=DEFAULT_MODEL_REVISION)
    parser.add_argument("--prompt-version", default="semantic_only_v1")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_line(row))
            handle.write("\n")


def canonical_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def validate_schema(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        expected = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected):
            errors.append(f"{path}: expected {expected}, got {json_type(value)}")
            return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.fullmatch(str(schema["pattern"]), value):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and float(value) < float(schema["minimum"]):
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and float(value) > float(schema["maximum"]):
            errors.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            for item in value:
                marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if marker in seen:
                    errors.append(f"{path}: duplicate array item {item!r}")
                    break
                seen.add(marker)
        if "items" in schema:
            item_schema = schema["items"]
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key}: missing required field")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in value:
                if key not in allowed:
                    errors.append(f"{path}.{key}: additional property not allowed")
        for key, item in value.items():
            if key in properties:
                errors.extend(validate_schema(item, properties[key], f"{path}.{key}"))
    return errors


def read_jsonl_with_lines(path: Path) -> list[tuple[int, str, dict[str, Any]]]:
    rows: list[tuple[int, str, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{line_no}")
            rows.append((line_no, line, row))
    return rows


def validate_input_record(
    row: dict[str, Any],
    line_no: int,
    input_schema: dict[str, Any],
    family_map: dict[str, list[str]],
    prompt_version: str,
) -> tuple[list[str], list[str]]:
    errors = validate_schema(row, input_schema, f"input:{line_no}")
    warnings: list[str] = []
    family = row.get("predicate_family")
    if isinstance(family, str) and family in family_map:
        expected = family_map[family]
        if row.get("candidate_predicates") != expected:
            errors.append(f"input:{line_no}.candidate_predicates: must exactly match family map for {family}")
    if row.get("subject_id") == row.get("object_id"):
        errors.append(f"input:{line_no}: subject_id and object_id must differ")
    if prompt_version == "semantic_only_v1" and row.get("geometry_summary") not in (None,):
        errors.append(f"input:{line_no}.geometry_summary: semantic_only_v1 must not include geometry summary")
    for crop_index, crop in enumerate(row.get("crop_paths", [])):
        if isinstance(crop, dict) and str(crop.get("path", "")).startswith("/"):
            warnings.append(f"input:{line_no}.crop_paths[{crop_index}]: absolute crop path; prefer mounted-root relative path")
    return errors, warnings


def raw_response_rows(path: Path | None, example_response: str, example_record_id: str) -> dict[str, str]:
    if path is None:
        return {example_record_id: example_response}
    responses: dict[str, str] = {}
    for line_no, _line, row in read_jsonl_with_lines(path):
        record_id = row.get("record_id")
        raw_response = row.get("raw_response")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"raw response row missing record_id at {path}:{line_no}")
        if not isinstance(raw_response, str):
            raise ValueError(f"raw response row missing raw_response at {path}:{line_no}")
        responses[record_id] = raw_response
    return responses


def parse_response(raw_response: str, candidate_predicates: list[str]) -> tuple[str, list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        lowered = raw_response.lower()
        if "sorry" in lowered or "cannot" in lowered or "refus" in lowered:
            return "refused", [], ["raw_response_refusal_like_non_json"]
        return "unparseable", [], ["raw_response_not_strict_json"]

    if not isinstance(payload, dict):
        return "unparseable", [], ["raw_response_json_root_not_object"]
    if payload.get("refusal"):
        return "refused", [], ["raw_response_contains_refusal"]

    answer_is_visible = payload.get("answer_is_visible")
    if not isinstance(answer_is_visible, bool):
        warnings.append("answer_is_visible_missing_or_not_boolean")
        answer_is_visible = False
    raw_predictions = payload.get("predictions")
    if raw_predictions is None:
        raw_predictions = []
        warnings.append("predictions_missing")
    if not isinstance(raw_predictions, list):
        raw_predictions = []
        warnings.append("predictions_not_array")

    parsed: list[dict[str, Any]] = []
    seen_predicates: set[str] = set()
    for item_index, item in enumerate(raw_predictions):
        if not isinstance(item, dict):
            warnings.append(f"prediction_{item_index}_not_object")
            continue
        predicate = item.get("predicate")
        if not isinstance(predicate, str) or not predicate:
            warnings.append(f"prediction_{item_index}_missing_predicate")
            continue
        if predicate not in candidate_predicates:
            warnings.append(f"prediction_{item_index}_predicate_not_allowed:{predicate}")
            continue
        if predicate in seen_predicates:
            warnings.append(f"prediction_{item_index}_duplicate_predicate:{predicate}")
            continue
        seen_predicates.add(predicate)
        confidence = item.get("confidence", item.get("semantic_score"))
        semantic_score: float | None
        try:
            semantic_score = float(confidence)
        except (TypeError, ValueError):
            semantic_score = None
        if semantic_score is not None and not (0.0 <= semantic_score <= 1.0):
            warnings.append(f"prediction_{item_index}_confidence_out_of_range")
            semantic_score = None
        rationale = item.get("rationale_short")
        if not isinstance(rationale, str):
            rationale = ""
            warnings.append(f"prediction_{item_index}_rationale_missing_or_not_string")
        parsed.append(
            {
                "predicate": predicate,
                "rank": len(parsed) + 1,
                "semantic_score": semantic_score,
                "answer_is_visible": answer_is_visible,
                "rationale_short": rationale[:240],
            }
        )

    if not answer_is_visible and parsed:
        warnings.append("answer_is_visible_false_with_predictions_dropped")
        parsed = []

    for index, item in enumerate(parsed, 1):
        if item["semantic_score"] is None:
            item["semantic_score"] = 1.0 / index
            warnings.append(f"prediction_{index - 1}_rank_score_fallback")

    status = "parsed_with_warning" if warnings else "parsed"
    return status, parsed, warnings


def decoding_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "backend": "contract_only_no_model_runtime",
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
    }


def make_prediction_row(
    input_row: dict[str, Any],
    input_line: str,
    raw_response: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    parser_status, predictions, warnings = parse_response(
        raw_response, list(input_row.get("candidate_predicates", []))
    )
    return {
        "schema_version": "h001_qwen_vl_prediction_v2",
        "record_id": input_row["record_id"],
        "scan_id": input_row["scan_id"],
        "subgraph_id": input_row["subgraph_id"],
        "split": input_row["split"],
        "subject_id": input_row["subject_id"],
        "object_id": input_row["object_id"],
        "predicate_family": input_row["predicate_family"],
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": args.baseline_run_id,
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "prompt_version": args.prompt_version,
        "input_record_sha256": hashlib.sha256(input_line.encode("utf-8")).hexdigest(),
        "decoding": decoding_payload(args),
        "raw_response": raw_response,
        "parser_status": parser_status,
        "predictions": predictions,
        "warnings": warnings,
    }


def collect_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(collect_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(collect_keys(item))
    return keys


def validate_output_record(
    row: dict[str, Any],
    line_no: int,
    output_schema: dict[str, Any],
    input_by_record_id: dict[str, tuple[str, dict[str, Any]]],
) -> tuple[list[str], list[str]]:
    errors = validate_schema(row, output_schema, f"output:{line_no}")
    warnings: list[str] = []
    if row.get("model_revision") == "main":
        errors.append(f"output:{line_no}.model_revision: 'main' is not allowed")
    banned = sorted(collect_keys(row).intersection(BANNED_SEMANTIC_SCORE_KEYS))
    if banned:
        errors.append(f"output:{line_no}: banned semantic-source leakage keys present: {banned}")
    linked = input_by_record_id.get(str(row.get("record_id")))
    if linked is None:
        errors.append(f"output:{line_no}.record_id: no matching input row")
        return errors, warnings
    input_line, input_row = linked
    for field in ["scan_id", "subgraph_id", "split", "subject_id", "object_id", "predicate_family"]:
        if row.get(field) != input_row.get(field):
            errors.append(f"output:{line_no}.{field}: does not match input record")
    expected_hash = hashlib.sha256(input_line.encode("utf-8")).hexdigest()
    if row.get("input_record_sha256") != expected_hash:
        errors.append(f"output:{line_no}.input_record_sha256: does not match exact input line")
    allowed_predicates = set(input_row.get("candidate_predicates", []))
    expected_rank = 1
    for prediction in row.get("predictions", []):
        if prediction.get("rank") != expected_rank:
            errors.append(f"output:{line_no}.predictions: ranks must be consecutive from 1")
            break
        expected_rank += 1
        if prediction.get("predicate") not in allowed_predicates:
            errors.append(f"output:{line_no}.predictions[{expected_rank - 2}].predicate: not allowed by input")
    if row.get("parser_status") == "parsed" and row.get("warnings"):
        warnings.append(f"output:{line_no}: parser_status parsed but warnings are non-empty")
    return errors, warnings


def load_input_rows(
    repo_root: Path,
    contract_dir: Path,
    input_jsonl: Path | None,
    out_dir: Path,
) -> tuple[list[tuple[int, str, dict[str, Any]]], Path]:
    if input_jsonl is not None:
        input_path = resolve(repo_root, input_jsonl)
        assert input_path is not None
        return read_jsonl_with_lines(input_path), input_path
    example = load_json(contract_dir / "input_schema_example.json")
    input_path = out_dir / "input_smoke.jsonl"
    write_jsonl(input_path, [example])
    return read_jsonl_with_lines(input_path), input_path


def parser_contract() -> dict[str, Any]:
    return {
        "schema_version": PARSER_CONTRACT_VERSION,
        "runtime_policy": "contract_only_no_model_download_no_inference",
        "accepted_raw_response": {
            "type": "strict JSON object",
            "required_fields": ["answer_is_visible", "predictions"],
            "prediction_fields": ["predicate", "confidence", "rationale_short"],
        },
        "parser_status_values": ["parsed", "parsed_with_warning", "unparseable", "refused", "runtime_error"],
        "scoring_policy": {
            "confidence": "Use confidence in [0, 1] as semantic_score when present.",
            "fallback": "Use 1/rank if confidence is missing or invalid, and record a warning.",
            "not_allowed": sorted(BANNED_SEMANTIC_SCORE_KEYS),
        },
    }


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Contract Validation Report",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This is a contract-only validator/parser skeleton. It does not download a model and does not run Qwen-VL inference.",
        "",
        "## Counts",
        "",
        f"- input rows: `{manifest['counts']['input_rows']}`",
        f"- parsed rows: `{manifest['counts']['parsed_rows']}`",
        f"- input errors: `{manifest['counts']['input_errors']}`",
        f"- output errors: `{manifest['counts']['output_errors']}`",
        f"- warnings: `{manifest['counts']['warnings']}`",
        "",
        "## Outputs",
        "",
    ]
    for name, path in manifest["outputs"].items():
        if path is not None:
            lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Keep using this validator before any Qwen-VL model download or inference. Runtime smoke remains optional and requires an explicit model id, fixed revision/local-dir, prompt version, and Docker command.",
            "",
        ]
    )
    if manifest["validation"]["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- `{item}`" for item in manifest["validation"]["errors"][:50])
        lines.append("")
    if manifest["validation"]["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- `{item}`" for item in manifest["validation"]["warnings"][:50])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    contract_dir = resolve(repo_root, args.contract_dir)
    out_dir = resolve(repo_root, args.out)
    assert contract_dir is not None
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    input_schema = load_json(contract_dir / "input_schema.json")
    output_schema = load_json(contract_dir / "output_schema.json")
    adapter_contract = load_json(contract_dir / "adapter_contract.json")
    prediction_example = load_json(contract_dir / "prediction_schema_example.json")
    family_map = adapter_contract["input_schema"]["predicate_family_map"]

    input_rows, input_path = load_input_rows(repo_root, contract_dir, args.input_jsonl, out_dir)
    example_record_id = input_rows[0][2]["record_id"] if input_rows else ""
    raw_responses = raw_response_rows(
        resolve(repo_root, args.raw_response_jsonl),
        str(prediction_example["raw_response"]),
        str(example_record_id),
    )

    input_errors: list[str] = []
    output_errors: list[str] = []
    warnings: list[str] = []
    input_by_record_id: dict[str, tuple[str, dict[str, Any]]] = {}
    output_rows: list[dict[str, Any]] = []

    for line_no, line, row in input_rows:
        errors, row_warnings = validate_input_record(row, line_no, input_schema, family_map, args.prompt_version)
        input_errors.extend(errors)
        warnings.extend(row_warnings)
        record_id = str(row.get("record_id"))
        input_by_record_id[record_id] = (line, row)
        raw_response = raw_responses.get(record_id)
        if raw_response is not None and not errors:
            output_rows.append(make_prediction_row(row, line, raw_response, args))

    output_example_errors = validate_schema(prediction_example, output_schema, "prediction_schema_example")
    output_errors.extend(output_example_errors)
    for line_no, row in enumerate(output_rows, 1):
        errors, row_warnings = validate_output_record(row, line_no, output_schema, input_by_record_id)
        output_errors.extend(errors)
        warnings.extend(row_warnings)

    parsed_path = out_dir / "parsed.jsonl"
    if output_rows:
        write_jsonl(parsed_path, output_rows)
    parser_contract_path = out_dir / "parser_contract.json"
    write_json(parser_contract_path, parser_contract())

    all_errors = input_errors + output_errors
    status = "validator_parser_skeleton_ready_no_model_runtime" if not all_errors else "blocked_contract_validation_errors"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "runtime_policy": "no_model_download_no_inference",
        "inputs": {
            "contract_dir": relpath(repo_root, contract_dir),
            "input_jsonl": relpath(repo_root, input_path),
            "raw_response_jsonl": relpath(repo_root, resolve(repo_root, args.raw_response_jsonl)),
            "prompt_version": args.prompt_version,
        },
        "outputs": {
            "input_smoke_jsonl": relpath(repo_root, out_dir / "input_smoke.jsonl")
            if args.input_jsonl is None
            else None,
            "parsed_jsonl": relpath(repo_root, parsed_path) if output_rows else None,
            "parser_contract": relpath(repo_root, parser_contract_path),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "counts": {
            "input_rows": len(input_rows),
            "parsed_rows": len(output_rows),
            "input_errors": len(input_errors),
            "output_errors": len(output_errors),
            "warnings": len(warnings),
        },
        "validation": {"errors": all_errors, "warnings": warnings},
        "next_action": "Use this validator/parser before any Qwen-VL model download or inference.",
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not all_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
