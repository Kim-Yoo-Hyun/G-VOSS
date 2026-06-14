#!/usr/bin/env python3
"""Create H002 human confirmation protocol artifacts for target v2."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_STRICT = RGA_ROOT / "target_redesign/strict_proximity_informativeness.jsonl"
DEFAULT_WEAK = RGA_ROOT / "target_redesign/weak_satisfied_actionability.jsonl"
DEFAULT_WORKING_LABELS = RGA_ROOT / "manual_audit/working_labels.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "human_confirmation_protocol"


REVIEW_FIELDS = {
    "reviewer_id": "free text; required",
    "review_round": "integer; required",
    "object_pair_valid": "yes/no/uncertain",
    "predicate_visually_plausible": "yes/no/uncertain",
    "geometry_witness_correct": "yes/no/uncertain",
    "relation_informative": "yes/no/uncertain",
    "relation_trivial_or_dense": "yes/no/uncertain",
    "annotation_missing_or_sparse": "yes/no/uncertain",
    "ontology_or_granularity_issue": "yes/no/uncertain",
    "segmentation_or_instance_issue": "yes/no/uncertain",
    "final_human_label": (
        "reliable_promote/unreliable_dense_noise/relabel_only/"
        "abstain_uncertain/invalid_pair/geometry_artifact"
    ),
    "confidence": "high/medium/low",
    "notes": "free text",
}

FINAL_LABEL_POLICY = {
    "reliable_promote": {
        "posterior_target": 1,
        "meaning": "valid object pair, plausible predicate, correct geometry witness, informative relation",
    },
    "unreliable_dense_noise": {
        "posterior_target": 0,
        "meaning": "geometry-supported but too trivial/dense/unhelpful to promote",
    },
    "relabel_only": {
        "posterior_target": None,
        "meaning": "relationship may be useful after predicate canonicalization; exclude from binary target",
    },
    "abstain_uncertain": {
        "posterior_target": None,
        "meaning": "visual/mesh evidence is insufficient or ambiguous",
    },
    "invalid_pair": {
        "posterior_target": None,
        "meaning": "object pair or instance segmentation is invalid",
    },
    "geometry_artifact": {
        "posterior_target": None,
        "meaning": "geometry witness is wrong or unreliable",
    },
}

ACCEPTANCE_CRITERIA = {
    "hypothesis_stage_minimum": {
        "reviewers": 1,
        "strict_rows_completed": 27,
        "required_fields": [
            "object_pair_valid",
            "predicate_visually_plausible",
            "geometry_witness_correct",
            "relation_informative",
            "relation_trivial_or_dense",
            "final_human_label",
            "confidence",
        ],
        "usable_binary_rows_min": 20,
        "per_class_min_after_exclusion": 8,
        "allowed_use": "train-only posterior plumbing smoke",
    },
    "paper_evidence_minimum": {
        "reviewers": 2,
        "strict_rows_completed": 27,
        "agreement_target": ">= 0.75 exact final-label agreement or all conflicts adjudicated",
        "usable_binary_rows_min": 20,
        "per_class_min_after_exclusion": 8,
        "required_action": "adjudicate disagreement before any posterior claim",
        "allowed_use": "still not held-out evidence; only label-quality gate",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", type=Path, default=DEFAULT_STRICT)
    parser.add_argument("--weak", type=Path, default=DEFAULT_WEAK)
    parser.add_argument("--working-labels", type=Path, default=DEFAULT_WORKING_LABELS)
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


def load_manual_by_prediction(path: Path) -> dict[str, dict[str, Any]]:
    manual = {}
    for row in read_jsonl(path):
        manual[str(row["prediction_id"])] = row
    return manual


def compact_assets(manual_row: dict[str, Any] | None) -> dict[str, Any]:
    if not manual_row:
        return {}
    assets = manual_row.get("visual_assets") or {}
    return {
        "contact_sheet": assets.get("contact_sheet"),
        "scan_dir": assets.get("scan_dir"),
        "mesh_obj": assets.get("mesh_obj"),
        "instance_ply": assets.get("instance_ply"),
        "subject_images": (assets.get("subject_images") or [])[:2],
        "object_images": (assets.get("object_images") or [])[:2],
        "subject_image_count": assets.get("subject_image_count"),
        "object_image_count": assets.get("object_image_count"),
    }


def review_row(target_row: dict[str, Any], manual_row: dict[str, Any] | None, priority: str) -> dict[str, Any]:
    features = target_row["baseline_inputs"]["factorized_reliability_posterior"]
    identity = target_row["identity"]
    target = target_row["target"]
    return {
        "schema_version": "h002_human_confirmation_review_v0",
        "priority": priority,
        "target_mode": target_row["target_mode"],
        "prediction_id": target_row["prediction_id"],
        "scan_id": identity["scan_id"],
        "subgraph_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "object_id": identity["object_id"],
        "subject_label": manual_row.get("subject_label") if manual_row else None,
        "object_label": manual_row.get("object_label") if manual_row else None,
        "predicate_label": identity["predicate_label"],
        "predicate_family": identity["predicate_family"],
        "working_label": target["working_label"],
        "machine_y": target["y"],
        "geometry_status": target["geometry_status"],
        "rank_bucket": target["rank_bucket"],
        "semantic_score_raw": features.get("semantic_score_raw"),
        "semantic_score_norm": features.get("semantic_score_norm"),
        "p_geom_valid": features.get("p_geom_valid_imputed_neutral"),
        "consistency_score": features.get("consistency_score"),
        "geometry_residual_proxy": features.get("geometry_residual_proxy"),
        "visual_assets": compact_assets(manual_row),
        "review_fields": {field: None for field in REVIEW_FIELDS},
        "final_label_policy": FINAL_LABEL_POLICY,
        "boundary": "human confirmation template; no label filled yet",
    }


def write_review_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "priority",
        "target_mode",
        "prediction_id",
        "scan_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "object_id",
        "object_label",
        "working_label",
        "machine_y",
        "contact_sheet",
        "mesh_obj",
        *REVIEW_FIELDS.keys(),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            assets = row.get("visual_assets") or {}
            flat = {
                "priority": row["priority"],
                "target_mode": row["target_mode"],
                "prediction_id": row["prediction_id"],
                "scan_id": row["scan_id"],
                "subject_id": row["subject_id"],
                "subject_label": row.get("subject_label"),
                "predicate_label": row["predicate_label"],
                "object_id": row["object_id"],
                "object_label": row.get("object_label"),
                "working_label": row["working_label"],
                "machine_y": row["machine_y"],
                "contact_sheet": assets.get("contact_sheet"),
                "mesh_obj": assets.get("mesh_obj"),
            }
            flat.update({field: "" for field in REVIEW_FIELDS})
            writer.writerow(flat)


def summarize(strict_rows: list[dict[str, Any]], weak_rows: list[dict[str, Any]], missing_assets: list[str]) -> dict[str, Any]:
    def label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        return dict(Counter(str(row["working_label"]) for row in rows))

    def asset_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        contact = sum(1 for row in rows if (row.get("visual_assets") or {}).get("contact_sheet"))
        mesh = sum(1 for row in rows if (row.get("visual_assets") or {}).get("mesh_obj"))
        return {"contact_sheet": contact, "mesh_obj": mesh}

    return {
        "strict_rows": len(strict_rows),
        "weak_rows": len(weak_rows),
        "strict_label_counts": label_counts(strict_rows),
        "weak_label_counts": label_counts(weak_rows),
        "strict_asset_counts": asset_counts(strict_rows),
        "weak_asset_counts": asset_counts(weak_rows),
        "missing_manual_asset_prediction_ids": missing_assets,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Human Confirmation Protocol",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only confirmation protocol.",
        "- No validation/test rows are used.",
        "- This creates review templates only; no human labels are filled.",
        "- Posterior claims remain blocked.",
        "",
        "## Queues",
        "",
        "| Queue | Rows | Contact sheets | Mesh links |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| strict primary | {summary['counts']['strict_rows']} | "
            f"{summary['counts']['strict_asset_counts']['contact_sheet']} | "
            f"{summary['counts']['strict_asset_counts']['mesh_obj']} |"
        ),
        (
            f"| weak extension | {summary['counts']['weak_rows']} | "
            f"{summary['counts']['weak_asset_counts']['contact_sheet']} | "
            f"{summary['counts']['weak_asset_counts']['mesh_obj']} |"
        ),
        "",
        "## Final Labels",
        "",
        "| Label | Posterior target |",
        "| --- | --- |",
    ]
    for label, policy in FINAL_LABEL_POLICY.items():
        lines.append(f"| `{label}` | `{policy['posterior_target']}` |")
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "- Start with the 27 strict rows.",
            "- Treat results as posterior-training evidence only after required fields are complete.",
            "- Paper-level claims require two reviewers or adjudicated conflicts.",
            "",
            "Next gate: `32_human_label_readiness.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manual = load_manual_by_prediction(args.working_labels)
    strict_target_rows = read_jsonl(args.strict)
    weak_target_rows = read_jsonl(args.weak)

    missing_assets: list[str] = []
    strict_review = []
    weak_review = []
    for row in strict_target_rows:
        manual_row = manual.get(str(row["prediction_id"]))
        if manual_row is None:
            missing_assets.append(str(row["prediction_id"]))
        strict_review.append(review_row(row, manual_row, "primary"))
    for row in weak_target_rows:
        manual_row = manual.get(str(row["prediction_id"]))
        if manual_row is None:
            missing_assets.append(str(row["prediction_id"]))
        weak_review.append(review_row(row, manual_row, "extension_after_strict_pass"))

    created_at = datetime.now(timezone.utc).isoformat()
    paths = {
        "summary": output_dir / "summary.json",
        "protocol": output_dir / "protocol.json",
        "strict_queue": output_dir / "strict_review_queue.jsonl",
        "weak_queue": output_dir / "weak_extension_queue.jsonl",
        "strict_sheet": output_dir / "strict_review_sheet.tsv",
        "weak_sheet": output_dir / "weak_extension_sheet.tsv",
        "report": output_dir / "report.md",
    }
    counts = summarize(strict_review, weak_review, sorted(set(missing_assets)))
    protocol = {
        "schema_version": "h002_human_confirmation_protocol_v0",
        "review_fields": REVIEW_FIELDS,
        "final_label_policy": FINAL_LABEL_POLICY,
        "acceptance_criteria": ACCEPTANCE_CRITERIA,
        "review_order": [
            "strict_proximity_informativeness first",
            "weak_satisfied_actionability only after strict queue passes",
        ],
        "claim_boundary": {
            "posterior_claim_allowed_before_confirmation": False,
            "validation_usage": False,
            "paper_result": False,
        },
    }
    summary = {
        "schema_version": "h002_human_confirmation_protocol_summary_v0",
        "status": "ready_protocol_no_human_labels",
        "created_at": created_at,
        "input_paths": {
            "strict": rel_path(args.strict),
            "weak": rel_path(args.weak),
            "working_labels": rel_path(args.working_labels),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "counts": counts,
        "boundary": {
            "split": "train_only",
            "not_paper_result": True,
            "human_labels_filled": False,
            "posterior_claim_allowed": False,
            "validation_usage": False,
        },
        "next_gate": "32_human_label_readiness.md",
    }

    write_json(paths["summary"], summary)
    write_json(paths["protocol"], protocol)
    write_jsonl(paths["strict_queue"], strict_review)
    write_jsonl(paths["weak_queue"], weak_review)
    write_review_sheet(paths["strict_sheet"], strict_review)
    write_review_sheet(paths["weak_sheet"], weak_review)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} "
        f"strict={summary['counts']['strict_rows']} weak={summary['counts']['weak_rows']} "
        f"missing_assets={len(summary['counts']['missing_manual_asset_prediction_ids'])} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
