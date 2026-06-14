#!/usr/bin/env python3
"""Redesign H002 posterior targets after shortcut-control failure."""

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
DEFAULT_TARGET_JOINED = RGA_ROOT / "factor_dataset/target_joined.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "target_redesign"


TARGET_MODES = {
    "strict_proximity_informativeness": {
        "description": (
            "Geometry-satisfied proximity-only target. Positive rows are true "
            "underconfidence; negative rows are dense relation noise."
        ),
        "positive_labels": {"true_underconfidence"},
        "negative_labels": {"dense_relation_noise"},
        "required_geometry_status": {"satisfied"},
        "required_predicate_family": {"proximity"},
        "use": "small least-confounded hypothesis-stage target",
    },
    "weak_satisfied_actionability": {
        "description": (
            "Geometry-satisfied actionability target. Positive rows are true "
            "underconfidence or annotation sparsity; negative rows are dense "
            "relation noise."
        ),
        "positive_labels": {"true_underconfidence", "annotation_sparsity"},
        "negative_labels": {"dense_relation_noise"},
        "required_geometry_status": {"satisfied"},
        "required_predicate_family": None,
        "use": "larger weak target; family-confounded sensitivity only",
    },
}

LABEL_POLICY = {
    "true_underconfidence": {
        "role": "positive_candidate",
        "rationale": "geometry-supported relation under-ranked by semantic source",
    },
    "annotation_sparsity": {
        "role": "weak_positive_candidate",
        "rationale": "geometry-supported relation likely missing from sparse annotation",
    },
    "dense_relation_noise": {
        "role": "negative_candidate",
        "rationale": "geometry-supported but uninformative/dense relation should not be promoted",
    },
    "ontology_mismatch": {
        "role": "relabel_only",
        "rationale": "edge may be useful after predicate canonicalization, not as keep/reject binary target",
    },
    "semantic_overconfidence": {
        "role": "rga_overconfidence_diagnostic",
        "rationale": "geometry-unsatisfied HL row; useful for RGA, excluded from redesigned posterior target",
    },
    "uncertain_needs_visual_or_mesh": {
        "role": "abstain",
        "rationale": "needs human/mesh confirmation before target assignment",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-joined", type=Path, default=DEFAULT_TARGET_JOINED)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def row_label(row: dict[str, Any]) -> str:
    return str(row["target"]["working_label"])


def row_geometry(row: dict[str, Any]) -> str:
    return str(row["feature_blocks"]["geometry_evidence"]["geometry_status"])


def row_family(row: dict[str, Any]) -> str:
    return str(row["identity"]["predicate_family"])


def row_rank_bucket(row: dict[str, Any]) -> str:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    return "top100" if features.get("top100_semantic") else "tail"


def target_assignment(row: dict[str, Any], mode_name: str) -> dict[str, Any]:
    spec = TARGET_MODES[mode_name]
    label = row_label(row)
    geometry = row_geometry(row)
    family = row_family(row)
    if geometry not in spec["required_geometry_status"]:
        return {"eligible": False, "role": "excluded_geometry_status", "y": None}
    required_families = spec["required_predicate_family"]
    if required_families is not None and family not in required_families:
        return {"eligible": False, "role": "excluded_family", "y": None}
    if label in spec["positive_labels"]:
        return {"eligible": True, "role": "positive", "y": 1}
    if label in spec["negative_labels"]:
        return {"eligible": True, "role": "negative", "y": 0}
    policy = LABEL_POLICY.get(label, {"role": "excluded_unknown_label"})
    return {"eligible": False, "role": policy["role"], "y": None}


def assignment_row(row: dict[str, Any]) -> dict[str, Any]:
    label = row_label(row)
    base = {
        "schema_version": "h002_target_redesign_assignment_v0",
        "prediction_id": row["identity"]["prediction_id"],
        "scan_id": row["identity"]["scan_id"],
        "subgraph_id": row["identity"]["subgraph_id"],
        "subject_id": row["identity"]["subject_id"],
        "object_id": row["identity"]["object_id"],
        "predicate_label": row["identity"]["predicate_label"],
        "predicate_family": row_family(row),
        "geometry_status": row_geometry(row),
        "rank_bucket": row_rank_bucket(row),
        "working_label": label,
        "label_policy_role": LABEL_POLICY.get(label, {"role": "unknown"})["role"],
        "human_confirmed": bool(row["target"].get("human_confirmed")),
        "paper_locked": bool(row["target"].get("paper_locked")),
        "target_modes": {},
        "boundary": "train-only target redesign; not paper metric",
    }
    for mode_name in TARGET_MODES:
        base["target_modes"][mode_name] = target_assignment(row, mode_name)
    return base


def target_row(row: dict[str, Any], assignment: dict[str, Any], mode_name: str) -> dict[str, Any]:
    mode = assignment["target_modes"][mode_name]
    return {
        "schema_version": "h002_redesigned_target_row_v0",
        "target_mode": mode_name,
        "prediction_id": row["identity"]["prediction_id"],
        "identity": row["identity"],
        "baseline_inputs": row["baseline_inputs"],
        "target": {
            "y": mode["y"],
            "role": mode["role"],
            "working_label": row_label(row),
            "geometry_status": row_geometry(row),
            "predicate_family": row_family(row),
            "rank_bucket": row_rank_bucket(row),
            "human_confirmed": bool(row["target"].get("human_confirmed")),
            "paper_locked": bool(row["target"].get("paper_locked")),
            "target_source": "machine_assisted_working_label_reinterpreted",
            "leakage_boundary": (
                "This target controls geometry status by construction. Do not use "
                "geometry_status or RGA bucket identity as evidence of generalization."
            ),
        },
        "provenance": {
            "source": "target_joined.jsonl",
            "split_policy": "train_only_no_validation",
        },
    }


def summarize(rows: list[dict[str, Any]], assignments: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter()
    label_geometry_counts = Counter()
    label_family_counts = Counter()
    label_rank_counts = Counter()
    mode_counts: dict[str, Counter] = {mode: Counter() for mode in TARGET_MODES}
    mode_family_counts: dict[str, Counter] = {mode: Counter() for mode in TARGET_MODES}
    mode_rank_counts: dict[str, Counter] = {mode: Counter() for mode in TARGET_MODES}
    policy_counts = Counter()

    for row, assignment in zip(rows, assignments):
        label = row_label(row)
        geometry = row_geometry(row)
        family = row_family(row)
        rank = row_rank_bucket(row)
        label_counts[label] += 1
        label_geometry_counts[(label, geometry)] += 1
        label_family_counts[(label, family)] += 1
        label_rank_counts[(label, rank)] += 1
        policy_counts[assignment["label_policy_role"]] += 1
        for mode_name, mode in assignment["target_modes"].items():
            role = mode["role"]
            mode_counts[mode_name][role] += 1
            if mode["eligible"]:
                mode_family_counts[mode_name][(mode["y"], family)] += 1
                mode_rank_counts[mode_name][(mode["y"], rank)] += 1

    return {
        "input_rows": len(rows),
        "working_label_counts": dict(label_counts),
        "label_policy_counts": dict(policy_counts),
        "working_label_by_geometry": [
            {"working_label": key[0], "geometry_status": key[1], "rows": value}
            for key, value in sorted(label_geometry_counts.items())
        ],
        "working_label_by_family": [
            {"working_label": key[0], "predicate_family": key[1], "rows": value}
            for key, value in sorted(label_family_counts.items())
        ],
        "working_label_by_rank_bucket": [
            {"working_label": key[0], "rank_bucket": key[1], "rows": value}
            for key, value in sorted(label_rank_counts.items())
        ],
        "target_mode_counts": {
            mode_name: dict(counter) for mode_name, counter in mode_counts.items()
        },
        "target_mode_family_counts": {
            mode_name: [
                {"y": key[0], "predicate_family": key[1], "rows": value}
                for key, value in sorted(counter.items())
            ]
            for mode_name, counter in mode_family_counts.items()
        },
        "target_mode_rank_counts": {
            mode_name: [
                {"y": key[0], "rank_bucket": key[1], "rows": value}
                for key, value in sorted(counter.items())
            ]
            for mode_name, counter in mode_rank_counts.items()
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    strict = summary["counts"]["target_mode_counts"]["strict_proximity_informativeness"]
    weak = summary["counts"]["target_mode_counts"]["weak_satisfied_actionability"]
    lines = [
        "# H002 Target Redesign",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only target redesign.",
        "- No validation/test rows are used.",
        "- Working labels are machine-assisted, not human-confirmed.",
        "- This does not produce a paper-level metric.",
        "",
        "## Redesigned Targets",
        "",
        "| Target mode | Positive | Negative | Main control | Role |",
        "| --- | ---: | ---: | --- | --- |",
        (
            "| `strict_proximity_informativeness` | "
            f"{strict.get('positive', 0)} | {strict.get('negative', 0)} | "
            "`geometry_status=satisfied`, `predicate_family=proximity` | least-confounded small target |"
        ),
        (
            "| `weak_satisfied_actionability` | "
            f"{weak.get('positive', 0)} | {weak.get('negative', 0)} | "
            "`geometry_status=satisfied` | larger weak sensitivity target |"
        ),
        "",
        "## Label Policy",
        "",
        "| Working label | Role |",
        "| --- | --- |",
    ]
    for label, policy in LABEL_POLICY.items():
        lines.append(f"| `{label}` | {policy['role']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The next posterior smoke should use the strict proximity target first.",
            "The weak satisfied-actionability target is sensitivity-only because it is still family-confounded.",
            "No posterior performance claim should be made without human-confirmed labels.",
            "",
            "Next gate: `30_redesigned_target_smoke.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = read_jsonl(args.target_joined)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assignments = [assignment_row(row) for row in rows]
    counts = summarize(rows, assignments)
    created_at = datetime.now(timezone.utc).isoformat()

    paths = {
        "summary": output_dir / "summary.json",
        "target_contract": output_dir / "target_contract.json",
        "assignments": output_dir / "target_assignments.jsonl",
        "strict": output_dir / "strict_proximity_informativeness.jsonl",
        "weak": output_dir / "weak_satisfied_actionability.jsonl",
        "report": output_dir / "report.md",
    }

    strict_rows = []
    weak_rows = []
    for row, assignment in zip(rows, assignments):
        if assignment["target_modes"]["strict_proximity_informativeness"]["eligible"]:
            strict_rows.append(target_row(row, assignment, "strict_proximity_informativeness"))
        if assignment["target_modes"]["weak_satisfied_actionability"]["eligible"]:
            weak_rows.append(target_row(row, assignment, "weak_satisfied_actionability"))

    contract = {
        "schema_version": "h002_target_redesign_contract_v0",
        "target_modes": {
            name: {
                **{
                    key: sorted(value) if isinstance(value, set) else value
                    for key, value in spec.items()
                }
            }
            for name, spec in TARGET_MODES.items()
        },
        "label_policy": LABEL_POLICY,
        "required_boundary": {
            "split": "train_only",
            "validation_usage": False,
            "paper_result": False,
            "human_confirmation_required_for_claim": True,
            "machine_labels_allowed_for_plumbing_smoke": True,
        },
        "blocked_previous_targets": [
            "strict_binary_target",
            "weak_binary_target",
        ],
        "blocked_reason": "previous targets were equivalent or near-equivalent to RGA bucket construction",
    }
    summary = {
        "schema_version": "h002_target_redesign_summary_v0",
        "status": "ready_target_v2_contract",
        "created_at": created_at,
        "input_path": rel_path(args.target_joined),
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "counts": counts,
        "boundary": contract["required_boundary"],
        "decision": {
            "primary_next_target": "strict_proximity_informativeness",
            "sensitivity_target": "weak_satisfied_actionability",
            "posterior_claim_allowed": False,
            "reason": "target rows are machine-assisted and small; human confirmation is required for claim",
        },
    }

    write_json(paths["summary"], summary)
    write_json(paths["target_contract"], contract)
    write_jsonl(paths["assignments"], assignments)
    write_jsonl(paths["strict"], strict_rows)
    write_jsonl(paths["weak"], weak_rows)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    strict_counts = summary["counts"]["target_mode_counts"]["strict_proximity_informativeness"]
    weak_counts = summary["counts"]["target_mode_counts"]["weak_satisfied_actionability"]
    print(
        f"status={summary['status']} "
        f"strict_pos={strict_counts.get('positive', 0)} strict_neg={strict_counts.get('negative', 0)} "
        f"weak_pos={weak_counts.get('positive', 0)} weak_neg={weak_counts.get('negative', 0)} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
