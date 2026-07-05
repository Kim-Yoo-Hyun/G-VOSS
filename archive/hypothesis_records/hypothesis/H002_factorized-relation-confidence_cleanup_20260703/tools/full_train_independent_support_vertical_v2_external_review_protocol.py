#!/usr/bin/env python3
"""Create an external-evidence review protocol after human-proxy target audit failure."""

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
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_human_label_ingestion_codex_proxy_user_review_pending"
DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_human_target_independence_audit_codex_proxy_user_review_pending"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol"

DEFAULT_VALIDATED_LABELS = DEFAULT_INGESTION_DIR / "validated_human_labels.jsonl"
DEFAULT_AUDIT_SUMMARY = DEFAULT_AUDIT_DIR / "summary.json"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "family_question",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
    "external_label_notes",
]

FORBIDDEN_HEADER_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "target_y",
    "label_use",
    "relation_validity_label",
    "posterior",
    "v2",
    "witness_",
    "positive_cues",
    "negative_cues",
    "human_",
    "proxy",
]

REVIEW_VALUES = {
    "endpoint_identity_external": ["both_valid", "subject_wrong", "object_wrong", "both_wrong", "unclear"],
    "visual_pair_evaluability_external": ["evaluable", "occluded_or_unclear", "missing_views"],
    "mesh_pair_evaluability_external": ["evaluable", "missing_mesh", "unclear"],
    "visual_geometry_answer_external": ["supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"],
    "mesh_geometry_answer_external": ["supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"],
    "relation_informativeness_external": ["informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"],
    "final_relation_reliability_external": ["reliable", "unreliable", "uncertain"],
    "uncertainty_reason_external": [
        "none",
        "visual_mesh_disagree",
        "identity_uncertain",
        "occlusion_or_missing_view",
        "ambiguous_relation",
        "trivial_dense_relation",
        "ontology_mismatch",
        "insufficient_evidence",
    ],
}

FAMILY_QUESTIONS = {
    "support_contact": "Does the subject physically contact or support/attach to the object in the packet evidence?",
    "relative_vertical": "Is the subject clearly higher/lower than the object in the packet evidence?",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validated-labels", type=Path, default=DEFAULT_VALIDATED_LABELS)
    parser.add_argument("--audit-summary", type=Path, default=DEFAULT_AUDIT_SUMMARY)
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
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


def packet_paths(label: dict[str, Any]) -> dict[str, str]:
    deployable = label.get("deployable_evidence_after_label_lock", {})
    paths = deployable.get("audit_packet_paths_not_model_input", {})
    return {
        "multiview_packet": str(paths.get("multiview_packet") or ""),
        "pointcloud_or_mesh_packet": str(paths.get("pointcloud_or_mesh_packet") or ""),
        "contact_or_context_sheet": str(paths.get("contact_or_context_sheet") or ""),
    }


def visible_row(label: dict[str, Any]) -> dict[str, Any]:
    paths = packet_paths(label)
    family = str(label.get("predicate_family") or "")
    return {
        "blind_review_id": label.get("blind_review_id"),
        "review_scope": "selected_support_vertical_external_evidence_review_v1",
        "scan_id": label.get("scan_id"),
        "scene_context_id": label.get("subgraph_id"),
        "subject_id": label.get("subject_id"),
        "subject_label": label.get("subject_label"),
        "predicate_label": label.get("predicate_label"),
        "predicate_family": family,
        "object_id": label.get("object_id"),
        "object_label": label.get("object_label"),
        "family_question": FAMILY_QUESTIONS.get(family, "Does the packet evidence support this relation?"),
        "evidence_packet_status": label.get("evidence_packet_status"),
        **paths,
        "external_reviewer_id": "",
        "external_review_round": "",
        "endpoint_identity_external": "",
        "visual_pair_evaluability_external": "",
        "mesh_pair_evaluability_external": "",
        "visual_geometry_answer_external": "",
        "mesh_geometry_answer_external": "",
        "relation_informativeness_external": "",
        "final_relation_reliability_external": "",
        "uncertainty_reason_external": "",
        "external_label_notes": "",
    }


def manifest_row(label: dict[str, Any]) -> dict[str, Any]:
    fields = label.get("human_label_fields") or label.get("audit_only_human_label_fields") or {}
    hidden = label.get("hidden_audit_metadata_post_label_only", {})
    return {
        "blind_review_id": label.get("blind_review_id"),
        "scan_id": label.get("scan_id"),
        "subgraph_id": label.get("subgraph_id"),
        "subject_id": label.get("subject_id"),
        "subject_label": label.get("subject_label"),
        "predicate_label": label.get("predicate_label"),
        "predicate_family": label.get("predicate_family"),
        "object_id": label.get("object_id"),
        "object_label": label.get("object_label"),
        "packet_paths": packet_paths(label),
        "previous_codex_proxy_human_fields_post_label_only": fields,
        "hidden_audit_metadata_post_label_only": hidden,
        "forbidden_as_labeler_visible": [
            "source score/rank",
            "p_geom_valid",
            "geometry_status",
            "numeric witness values",
            "positive/negative cue text",
            "previous Codex proxy labels",
            "hidden prior labels",
            "v2 reference axes",
            "posterior target fields",
        ],
    }


def check_packet_files(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in rows:
        for key in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(key) or "")
            if not value:
                missing.append({"blind_review_id": row.get("blind_review_id"), "field": key, "path": "", "error_type": "missing_path"})
                continue
            path = as_abs(Path(value))
            if not path.exists():
                missing.append({"blind_review_id": row.get("blind_review_id"), "field": key, "path": value, "error_type": "path_not_found"})
    return missing


def header_leakage() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in VISIBLE_FIELDS:
        lowered = field.lower()
        for token in FORBIDDEN_HEADER_SUBSTRINGS:
            if token in lowered:
                hits.append({"field": field, "forbidden_substring": token})
    return hits


def top_risks(audit_summary: dict[str, Any], target_name: str) -> dict[str, Any]:
    target = audit_summary["target_decisions"][target_name]
    original = target["original"]
    return {
        "target_status": target["status"],
        "top_harmful_prior_risks": original["top_harmful_prior_risks"][:3],
        "top_construction_risks": original["top_construction_risks"][:3],
        "top_visible_non_target_risks": original["top_visible_non_target_risks"][:3],
        "recommended_strict_slice": target.get("recommended_strict_slice"),
        "recommended_construction_slice": target.get("recommended_construction_slice"),
    }


def write_instructions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# H002 External Evidence Review Instructions",
                "",
                "## Goal",
                "",
                "Label each relation using only the provided packet evidence. Do not infer the answer from source model rank, previous labels, hidden metadata, numeric witness values, or the old Codex-proxy review.",
                "",
                "## Evidence To Use",
                "",
                "- `multiview_packet`: object crops and contact/context sheet.",
                "- `pointcloud_or_mesh_packet`: mesh and instance-file pointers for local inspection.",
                "- `contact_or_context_sheet`: compact visual/contact context.",
                "",
                "## Evidence Not To Use",
                "",
                "- source semantic score or rank.",
                "- `p_geom_valid`.",
                "- deterministic geometry status.",
                "- raw numeric witness columns.",
                "- previous human-proxy/Codex labels.",
                "- hidden prior label or posterior target fields.",
                "",
                "## Labeling Rule",
                "",
                "1. Confirm endpoint identity first.",
                "2. Judge visual and mesh evidence separately.",
                "3. Mark geometry support/contradiction/uncertainty without using numeric residuals.",
                "4. Mark whether the relation is informative or a trivial dense/room-structure relation.",
                "5. Set final reliability to `reliable`, `unreliable`, or `uncertain`.",
                "",
                "## Target Derivation After Label Lock",
                "",
                "- `geometry_validity_external_target` is positive only when visual or mesh evidence supports the predicate and neither modality clearly contradicts it.",
                "- `relation_reliability_external_target` is positive only when endpoint identity is valid, geometry supports the predicate, the relation is informative, and final reliability is `reliable`.",
                "- `uncertain` rows remain excluded from binary posterior targets.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 External Review Protocol",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Why Revision Is Needed",
        "",
        "- The Codex-proxy human target still correlates with hidden prior validity labels.",
        "- The old human sheet exposed numeric witness fields and cue text, which are too close to deployable geometry evidence.",
        "- A stronger combiner would likely learn target-construction shortcuts before we have an independent target.",
        "",
        "## New Protocol",
        "",
        "- Hide source score/rank, `p_geom_valid`, geometry status, numeric witness fields, cue text, previous proxy labels, hidden labels, and v2 reference axes.",
        "- Expose only identity fields and external audit packets.",
        "- Use multi-view/contact/mesh evidence as label/audit evidence first, not posterior input.",
        "- Derive targets only after label lock.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| review rows | {summary['counts']['review_rows']} |",
        f"| ready packets | {summary['counts']['ready_packets']} |",
        f"| packet path errors | {summary['counts']['packet_path_errors']} |",
        f"| header leakage hits | {summary['counts']['header_leakage_hits']} |",
        "",
        "## Previous Audit Risk",
        "",
        "| Target | Status | Top Harmful Prior Risk | Construction Diagnostic |",
        "| --- | --- | --- | --- |",
    ]
    for target_name, risk in summary["previous_audit_risks"].items():
        harmful = risk["top_harmful_prior_risks"][0] if risk["top_harmful_prior_risks"] else None
        construction = risk.get("recommended_construction_slice")
        lines.append(
            f"| `{target_name}` | `{risk['target_status']}` | "
            f"`{harmful['group_key'] if harmful else 'none'}` | "
            f"`{construction['slice_name'] if construction else 'none'}` |"
        )
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    labels_path = as_abs(args.validated_labels)
    audit_summary_path = as_abs(args.audit_summary)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    labels = read_jsonl(labels_path)
    audit_summary = read_json(audit_summary_path)
    visible_rows = [visible_row(label) for label in labels]
    manifest_rows = [manifest_row(label) for label in labels]
    missing_packet_paths = check_packet_files(visible_rows)
    leakage_hits = header_leakage()
    by_family = Counter(row["predicate_family"] for row in visible_rows)
    by_packet_status = Counter(row["evidence_packet_status"] for row in visible_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "external_review_sheet": output_dir / "external_evidence_review_sheet.tsv",
        "external_manifest_post_label_only": output_dir / "external_manifest_post_label_only.jsonl",
        "external_review_schema": output_dir / "external_review_schema.json",
        "reviewer_instructions": output_dir / "reviewer_instructions.md",
        "labeler_header_leakage_hits": output_dir / "labeler_header_leakage_hits.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
    }

    status = "full_train_independent_support_vertical_v2_external_review_protocol_ready"
    if leakage_hits or missing_packet_paths:
        status = "full_train_independent_support_vertical_v2_external_review_protocol_ready_with_warnings"

    summary = {
        "schema_version": "h002_support_vertical_v2_external_review_protocol_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": "Use external packet evidence for a new label pass before any posterior smoke or combiner upgrade.",
        "input_paths": {
            "validated_human_labels": rel_path(labels_path),
            "human_target_independence_audit_summary": rel_path(audit_summary_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "uses_previous_proxy_labels_as_visible_input": False,
            "uses_numeric_witness_as_visible_input": False,
            "uses_source_score_or_rank_as_visible_input": False,
            "uses_p_geom_valid_as_visible_input": False,
            "uses_geometry_status_as_visible_input": False,
            "uses_hidden_prior_labels_as_visible_input": False,
            "uses_v2_reference_axes_as_visible_input": False,
            "multi_view_as_model_input": False,
            "multi_view_as_audit_evidence": True,
            "mesh_as_audit_evidence": True,
            "contact_context_as_audit_evidence": True,
            "posterior_smoke_allowed": False,
            "combiner_upgrade_allowed": False,
        },
        "counts": {
            "review_rows": len(visible_rows),
            "ready_packets": by_packet_status.get("ready", 0),
            "packet_path_errors": len(missing_packet_paths),
            "header_leakage_hits": len(leakage_hits),
            "by_family": dict(sorted(by_family.items())),
            "by_packet_status": dict(sorted(by_packet_status.items())),
        },
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_header_substrings": FORBIDDEN_HEADER_SUBSTRINGS,
        "allowed_review_values": REVIEW_VALUES,
        "target_derivation_contract": {
            "geometry_validity_external_target": {
                "positive": "visual or mesh answer supports_predicate and neither available modality contradicts_predicate",
                "negative": "visual or mesh answer contradicts_predicate with evaluable evidence and no supporting modality",
                "exclude": "endpoint unclear/wrong, visual and mesh uncertain, missing evidence, or reviewer marks uncertainty",
            },
            "relation_reliability_external_target": {
                "positive": "endpoint_identity_external=both_valid, geometry supports predicate, relation_informativeness_external=informative, final_relation_reliability_external=reliable",
                "negative": "final_relation_reliability_external=unreliable, endpoint wrong, geometry contradicts predicate, ontology mismatch, or trivial dense/room-structure relation",
                "exclude": "final_relation_reliability_external=uncertain or evidence is insufficient",
            },
        },
        "previous_audit_risks": {
            "geometry_validity_human_target": top_risks(audit_summary, "geometry_validity_human_target"),
            "relation_reliability_human_target": top_risks(audit_summary, "relation_reliability_human_target"),
        },
        "next_todo": "fill_external_evidence_review_sheet_or_user_review",
    }

    write_tsv(output_paths["external_review_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["external_manifest_post_label_only"], manifest_rows)
    write_json(output_paths["external_review_schema"], {
        "schema_version": "h002_support_vertical_v2_external_review_schema_v1",
        "visible_fields": VISIBLE_FIELDS,
        "completion_fields": [
            "external_reviewer_id",
            "external_review_round",
            *REVIEW_VALUES.keys(),
            "external_label_notes",
        ],
        "allowed_review_values": REVIEW_VALUES,
        "forbidden_visible_inputs": summary["boundary"],
        "target_derivation_contract": summary["target_derivation_contract"],
    })
    write_jsonl(output_paths["labeler_header_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["packet_path_errors"], missing_packet_paths)
    write_instructions(output_paths["reviewer_instructions"])
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} rows={counts['review_rows']} "
        f"ready_packets={counts['ready_packets']} packet_path_errors={counts['packet_path_errors']} "
        f"header_leakage_hits={counts['header_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
