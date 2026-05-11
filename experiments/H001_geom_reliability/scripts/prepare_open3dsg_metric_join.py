#!/usr/bin/env python3
"""Freeze the Open3DSG metric/join runner contract before runtime inputs exist."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_metric_join_contract_v1"
METRICS_SCHEMA_VERSION = "h001_open3dsg_metrics_v1"
BASELINE_NAME = "open3dsg_ov"
SPLIT_NAME = "h001_validation_hardened"
TARGET_FAMILIES = ["support_contact", "proximity", "relative_vertical"]
STATUS_BLOCKED = "blocked_runtime_inputs_missing"
STATUS_READY = "ready_runtime_inputs_present_contract_only"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--predictions-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl"),
    )
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/"
            "vlsat_closed_set/hardened/ground_truth.jsonl"
        ),
    )
    parser.add_argument(
        "--geometry-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl"),
    )
    parser.add_argument(
        "--calibration-model-json",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/"
            "p_geom_valid_smoke/model.json"
        ),
    )
    parser.add_argument(
        "--family-calibration-model-json",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/"
            "p_geom_valid_family/model.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/metric_join_contract"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_lines(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_first_jsonl(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            return json.loads(line)
    return None


def input_contract() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_name": BASELINE_NAME,
        "split_name": SPLIT_NAME,
        "required_runtime_inputs": {
            "predictions_jsonl": {
                "schema": "h001_prediction_v1",
                "required_fields": [
                    "prediction_id",
                    "scan_id",
                    "subgraph_id",
                    "subset_split_id",
                    "edge.subject_id",
                    "edge.object_id",
                    "predicate.predicate_label",
                    "predicate.predicate_family",
                    "scores.ranking_score",
                ],
                "identity_rule": "prediction_id must preserve scan/subgraph/subject/object/predicate identity from the Open3DSG raw dump.",
            },
            "ground_truth_jsonl": {
                "schema": "h001_ground_truth_relation_rows",
                "required_fields": [
                    "scan_id",
                    "subset_split_id",
                    "subject_id",
                    "object_id",
                    "predicate_label",
                    "predicate_family",
                ],
                "scope": "same H001 held-out validation denominator used by VL-SAT.",
            },
            "geometry_jsonl": {
                "schema": "h001_prediction_geometry_v1",
                "required_fields": [
                    "prediction_id",
                    "verification_status",
                    "consistency_score",
                    "calibration.p_geom_valid",
                    "geometry.features",
                    "verification_variants",
                ],
                "join_rule": "one geometry/verification row per prediction_id; missing rows block paper-result metrics.",
            },
        },
        "optional_inputs": {
            "calibration_model_json": "frozen p_geom_valid model for probabilistic_recalibrated condition",
            "family_calibration_model_json": "family-specific control model for Table 2/Table 6 diagnostics",
        },
        "target_families": TARGET_FAMILIES,
    }


def output_contract() -> dict[str, Any]:
    metric_block = {
        "recall": {
            "by_k": {
                "50": {"correct": "integer", "recall": "number|null", "selected_predictions": "integer"},
                "100": {"correct": "integer", "recall": "number|null", "selected_predictions": "integer"},
            }
        },
        "violation_rate": {
            "by_k": {
                "50": {"violations": "integer", "violation_rate": "number|null", "selected_predictions": "integer"},
                "100": {"violations": "integer", "violation_rate": "number|null", "selected_predictions": "integer"},
            }
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "metrics_schema_version": METRICS_SCHEMA_VERSION,
        "required_outputs": {
            "metrics_json": {
                "required_top_level_fields": [
                    "schema_version",
                    "status",
                    "baseline_name",
                    "split_name",
                    "counts",
                    "conditions",
                    "blocked",
                    "claim_boundary",
                ],
                "conditions": {
                    "open3dsg_semantic_only": metric_block,
                    "open3dsg_probabilistic_recalibrated": metric_block,
                    "open3dsg_rule_verified_point_subtype": metric_block,
                    "open3dsg_family_specific_p_geom_valid": metric_block,
                },
            },
            "report_md": "human-readable summary that separates Fact, Inference, and Claim boundary",
            "joined_manifest_json": "input hashes, row counts, join counts, missing geometry rows, and blocked reasons",
        },
        "table_builder_hook": {
            "table": "Table 6",
            "blocked_until": "Open3DSG metrics_json status is ready",
            "allowed_claim_after_ready": "cross-predictor trend within measured H001 families only",
        },
    }


def inspect_input(repo_root: Path, name: str, path: Path, required: bool) -> dict[str, Any]:
    exists = path.exists()
    payload: dict[str, Any] = {
        "name": name,
        "path": relpath(repo_root, path),
        "required": required,
        "exists": exists,
        "line_count": count_lines(path),
        "sample_keys": [],
        "status": "present" if exists else ("missing_required" if required else "missing_optional"),
    }
    if exists and path.suffix == ".jsonl":
        try:
            sample = read_first_jsonl(path)
            payload["sample_keys"] = sorted(sample.keys()) if isinstance(sample, dict) else []
        except Exception as exc:  # noqa: BLE001 - contract preflight records parse failures.
            payload["status"] = "unreadable_jsonl"
            payload["error"] = str(exc)
    elif exists and path.suffix == ".json":
        try:
            sample = json.loads(path.read_text(encoding="utf-8"))
            payload["sample_keys"] = sorted(sample.keys()) if isinstance(sample, dict) else []
        except Exception as exc:  # noqa: BLE001
            payload["status"] = "unreadable_json"
            payload["error"] = str(exc)
    return payload


def blocked_metrics(status: str, blocked: list[str], input_rows: dict[str, int | None]) -> dict[str, Any]:
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "contract_schema_version": SCHEMA_VERSION,
        "status": status,
        "baseline_name": BASELINE_NAME,
        "split_name": SPLIT_NAME,
        "target_families": TARGET_FAMILIES,
        "counts": {
            "predictions": input_rows.get("predictions_jsonl"),
            "ground_truth": input_rows.get("ground_truth_jsonl"),
            "geometry": input_rows.get("geometry_jsonl"),
            "in_scope_gt_denominator": None,
        },
        "conditions": {},
        "blocked": blocked,
        "claim_boundary": (
            "This is a contract/blocked-input artifact only. It is not Open3DSG metric evidence "
            "until reproduced checkpoint predictions, geometry join, and metric calculations exist."
        ),
    }


def render_report(manifest: dict[str, Any], metrics: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Metric/Join Contract",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Fact",
        "",
        "- The Open3DSG metric runner contract is frozen before Open3DSG runtime metrics exist.",
        "- This command does not train Open3DSG, inspect predictions, compute metrics, or assign failure labels.",
        "- It writes blocked outputs when required runtime inputs are missing.",
        "",
        "## Runtime Inputs",
        "",
    ]
    for item in manifest["inputs"].values():
        lines.append(
            f"- `{item['name']}`: status `{item['status']}`, rows `{item['line_count']}`, path `{item['path']}`"
        )
    lines.extend(
        [
            "",
            "## Blocked",
            "",
        ]
    )
    if manifest["blocked"]:
        lines.extend(f"- `{item}`" for item in manifest["blocked"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Output Contract",
            "",
            "- `metrics.json` must expose semantic-only, probabilistic rerank, rule-verified, and family-specific control conditions when real inputs exist.",
            "- Table 6 must remain blocked until `metrics.json` status is `ready`.",
            "",
            "## Claim Boundary",
            "",
            metrics["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def render_commands() -> str:
    return "\n".join(
        [
            "# Open3DSG Metric/Join Contract Commands",
            "",
            "Run from the repository root.",
            "",
            "## Contract / Blocked-Input Preflight",
            "",
            "```bash",
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_join_contract'",
            "```",
            "",
            "## Real Runtime Inputs Required Later",
            "",
            "- `experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl`",
            "- `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl`",
            "- `experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl`",
            "",
            "Do not promote this contract output to paper-result evidence.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_paths = {
        "predictions_jsonl": resolve(repo_root, args.predictions_jsonl),
        "ground_truth_jsonl": resolve(repo_root, args.ground_truth_jsonl),
        "geometry_jsonl": resolve(repo_root, args.geometry_jsonl),
        "calibration_model_json": resolve(repo_root, args.calibration_model_json),
        "family_calibration_model_json": resolve(repo_root, args.family_calibration_model_json),
    }
    required = {"predictions_jsonl", "ground_truth_jsonl", "geometry_jsonl"}
    inputs = {
        name: inspect_input(repo_root, name, path, required=name in required)
        for name, path in input_paths.items()
    }
    blocked = [
        f"{name}:{item['status']}:{item['path']}"
        for name, item in inputs.items()
        if item["required"] and item["status"] != "present"
    ]
    status = STATUS_BLOCKED if blocked else STATUS_READY
    input_rows = {name: item["line_count"] for name, item in inputs.items()}
    metrics = blocked_metrics(status=status, blocked=blocked, input_rows=input_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "baseline_name": BASELINE_NAME,
        "split_name": SPLIT_NAME,
        "target_families": TARGET_FAMILIES,
        "inputs": inputs,
        "blocked": blocked,
        "outputs": {
            "input_contract_json": relpath(repo_root, out_dir / "input_contract.json"),
            "output_contract_json": relpath(repo_root, out_dir / "output_contract.json"),
            "metrics_json": relpath(repo_root, out_dir / "metrics.json"),
            "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
            "commands_md": relpath(repo_root, out_dir / "commands.md"),
            "report_md": relpath(repo_root, out_dir / "report.md"),
        },
        "next_action": (
            "After Open3DSG prediction JSONL and geometry join exist, replace blocked metrics "
            "with real H001 metric calculation without changing the frozen input/output contract."
        ),
    }
    write_json(out_dir / "input_contract.json", input_contract())
    write_json(out_dir / "output_contract.json", output_contract())
    write_json(out_dir / "metrics.json", metrics)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "commands.md").write_text(render_commands(), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(manifest, metrics), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "blocked": blocked,
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
