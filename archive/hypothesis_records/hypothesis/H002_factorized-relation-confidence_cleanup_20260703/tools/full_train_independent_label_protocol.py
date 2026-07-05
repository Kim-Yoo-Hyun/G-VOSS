#!/usr/bin/env python3
"""Create full-train rank/role-hidden independent label protocol artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_INPUT_CANDIDATES = RGA_ROOT / "controlled_label_mining/candidate_pool.jsonl"
DEFAULT_POLICY_AUDIT = RGA_ROOT / "label_policy_audit_codex_ver/summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_protocol"

FORBIDDEN_BLIND_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "role",
    "candidate_axis",
    "prediction_id",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "semantic",
    "consistency",
    "disagreement",
    "underconfidence",
]

BLIND_REVIEW_FIELDS = {
    "reviewer_id": "free text; required",
    "review_round": "integer; required",
    "subject_identity_valid": "yes/no/uncertain",
    "object_identity_valid": "yes/no/uncertain",
    "object_pair_visible": "yes/no/partial/uncertain",
    "relation_visible_or_inferable": "yes/no/uncertain",
    "visual_3d_support": "supports/contradicts/uncertain/not_evaluable",
    "relation_informativeness": "informative/trivial_dense/uncertain/not_evaluable",
    "independent_relation_label": (
        "reliable_informative/valid_but_trivial_dense/annotation_sparsity_candidate/"
        "ontology_mismatch/invalid_relation/invalid_pair/visibility_or_geometry_artifact/"
        "abstain_uncertain"
    ),
    "confidence": "high/medium/low",
    "evidence_notes": "free text",
}

LABEL_TO_BINARY_POLICY = {
    "positive": [
        "reliable_informative",
        "annotation_sparsity_candidate",
    ],
    "negative": [
        "valid_but_trivial_dense",
        "invalid_relation",
        "invalid_pair",
        "visibility_or_geometry_artifact",
    ],
    "exclude_or_multiclass_only": [
        "ontology_mismatch",
        "abstain_uncertain",
    ],
}

FAMILY_GUIDANCE = {
    "support_contact": {
        "priority": 1,
        "role": "primary physical-contact reliability family",
        "question": "Is the subject physically supported by or lying/standing on the object?",
        "positive_cues": "visible contact, plausible support surface, consistent vertical support order",
        "negative_cues": "nearby without support, impossible support surface, identity/segmentation artifact",
    },
    "relative_vertical": {
        "priority": 2,
        "role": "geometry-dominant control family",
        "question": "Is the subject clearly higher/lower than the object?",
        "positive_cues": "clear vertical order and comparable object extents",
        "negative_cues": "ambiguous height, wrong direction, non-comparable pair, identity artifact",
    },
    "proximity": {
        "priority": 3,
        "role": "dense-noise and informativeness diagnostic family",
        "question": "Is the close-by relation informative for the object pair?",
        "positive_cues": "meaningful spatial relation beyond dense nearby clutter",
        "negative_cues": "trivial dense relation, pair not meaningfully related, identity artifact",
    },
    "attachment_deferred": {
        "priority": 4,
        "role": "future extension; no current rows in this candidate pool",
        "question": "Is the subject attached/hanging/connected to the object?",
        "positive_cues": "visible anchor, hanging/contact fixture, cable/handle/connection evidence",
        "negative_cues": "only nearby objects without attachment cue",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-candidates", type=Path, default=DEFAULT_INPUT_CANDIDATES)
    parser.add_argument("--policy-audit", type=Path, default=DEFAULT_POLICY_AUDIT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--priority-cap", type=int, default=180)
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def blind_review_id(row: dict[str, Any]) -> str:
    digest = stable_hash("h002_full_train_independent_label_v0:" + str(row["prediction_id"]))
    return "ftind_" + digest[:12]


def asset_request_id(row: dict[str, Any]) -> str:
    key = ":".join(
        str(row.get(name))
        for name in ["scan_id", "subgraph_id", "subject_id", "predicate_label", "object_id"]
    )
    return "asset_" + stable_hash("h002_full_train_asset_request_v0:" + key)[:12]


def family_priority(row: dict[str, Any]) -> int:
    guidance = FAMILY_GUIDANCE.get(str(row.get("predicate_family")), {})
    return int(guidance.get("priority", 99))


def blind_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    return (
        family_priority(row),
        str(row.get("predicate_label")),
        stable_hash("h002_full_train_blind_order:" + str(row.get("prediction_id"))),
    )


def blind_row(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("predicate_family"))
    guidance = FAMILY_GUIDANCE.get(family, {})
    output = {
        "blind_review_id": blind_review_id(row),
        "asset_request_id": asset_request_id(row),
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": family,
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "endpoint_pair_note": "same_label_pair" if row.get("same_endpoint_label") else "",
        "family_question": guidance.get("question", ""),
        "positive_cues": guidance.get("positive_cues", ""),
        "negative_cues": guidance.get("negative_cues", ""),
        "evidence_packet_status": "needs_asset_generation",
        "multiview_packet": "",
        "pointcloud_or_mesh_packet": "",
        "contact_or_context_sheet": "",
    }
    output.update({field: "" for field in BLIND_REVIEW_FIELDS})
    return output


def internal_key_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": blind_review_id(row),
        "asset_request_id": asset_request_id(row),
        "review_id_hidden": row.get("review_id"),
        "prediction_id_hidden": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "queue_kind_hidden": row.get("queue_kind"),
        "candidate_axis_hidden": row.get("candidate_axis"),
        "proposed_audit_role_hidden": row.get("proposed_audit_role"),
        "role_reason_hidden": row.get("role_reason"),
        "label_match_status_hidden": row.get("label_match_status"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "rank_band_hidden": row.get("rank_band"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "consistency_score_hidden": row.get("consistency_score"),
        "disagreement_score_hidden": row.get("disagreement_score"),
        "underconfidence_score_hidden": row.get("underconfidence_score"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "bucket_top50_hidden": row.get("bucket_top50"),
        "bucket_top100_hidden": row.get("bucket_top100"),
        "machine_hint_hidden": row.get("machine_hint"),
        "matched_predicates_hidden": row.get("matched_predicates") or [],
        "matched_gt_ids_hidden": row.get("matched_gt_ids") or [],
        "reason_codes_hidden": row.get("reason_codes") or [],
        "leakage_boundary": "Internal key only. Do not expose before independent labels are locked.",
    }


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_request_id": asset_request_id(row),
        "blind_review_id": blind_review_id(row),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "requested_assets": [
            "subject_object_multiview_crops",
            "co_visible_view_contact_or_context_sheet",
            "object_pair_pointcloud_or_mesh_crop",
            "optional_instance_segmentation_overlay",
        ],
        "asset_policy": "Audit evidence only. Do not use as V_mv_e model input at this stage.",
    }


def priority_sample(rows: list[dict[str, Any]], cap: int) -> list[dict[str, Any]]:
    if cap <= 0 or len(rows) <= cap:
        return list(rows)
    groups: dict[tuple[str, str], deque[dict[str, Any]]] = defaultdict(deque)
    for row in sorted(rows, key=blind_sort_key):
        groups[(str(row.get("predicate_family")), str(row.get("predicate_label")))].append(row)
    selected: list[dict[str, Any]] = []
    keys = deque(sorted(groups, key=lambda key: (FAMILY_GUIDANCE.get(key[0], {}).get("priority", 99), key[1])))
    while keys and len(selected) < cap:
        key = keys.popleft()
        queue = groups[key]
        if queue:
            selected.append(queue.popleft())
        if queue:
            keys.append(key)
    return selected


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "unique_scans": len({str(row.get("scan_id")) for row in rows}),
        "by_family": dict(sorted(Counter(str(row.get("predicate_family")) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row.get("predicate_label")) for row in rows).items())),
    }


def hidden_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_queue_kind_hidden": dict(sorted(Counter(str(row.get("queue_kind")) for row in rows).items())),
        "by_label_match_status_hidden": dict(sorted(Counter(str(row.get("label_match_status")) for row in rows).items())),
        "by_geometry_status_hidden": dict(sorted(Counter(str(row.get("geometry_status")) for row in rows).items())),
        "by_rank_band_hidden": dict(sorted(Counter(str(row.get("rank_band")) for row in rows).items())),
        "by_proposed_audit_role_hidden": dict(sorted(Counter(str(row.get("proposed_audit_role")) for row in rows).items())),
    }


def leakage_audit(fieldnames: list[str]) -> dict[str, Any]:
    hits = []
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_BLIND_SUBSTRINGS:
            if token in lower:
                hits.append({"field": field, "forbidden_substring": token})
    return {
        "status": "pass" if not hits else "fail",
        "forbidden_substrings": FORBIDDEN_BLIND_SUBSTRINGS,
        "hits": hits,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Label Protocol",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage protocol.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this stage.",
        "- Multi-view evidence is audit support only, not model input.",
        "- `proposed_audit_role`, `label_match_status`, `queue_kind`, `geometry_status`, rank, score, and `p_geom_valid` are hidden.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Reason:",
        "",
        summary["decision"],
        "",
        "## Blind Sheets",
        "",
        "| Sheet | Rows | Scans | Families |",
        "| --- | ---: | ---: | --- |",
    ]
    for sheet in summary["blind_sheets"]:
        counts = sheet["summary"]["by_family"]
        family_text = ", ".join(f"{key}:{value}" for key, value in counts.items())
        lines.append(f"| `{sheet['path']}` | {sheet['summary']['rows']} | {sheet['summary']['unique_scans']} | {family_text} |")

    lines.extend(
        [
            "",
            "## Leakage Audit",
            "",
            f"Blind field audit status: `{summary['leakage_audit']['status']}`",
            "",
            "## Label Mapping",
            "",
            "| Binary use | Labels |",
            "| --- | --- |",
        ]
    )
    for key, labels in LABEL_TO_BINARY_POLICY.items():
        lines.append(f"| `{key}` | {', '.join(f'`{label}`' for label in labels)} |")

    lines.extend(
        [
            "",
            "## Output",
            "",
            "```text",
            summary["protocol"],
            summary["internal_key"],
            summary["asset_request_manifest"],
            "```",
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_candidates = as_abs(args.input_candidates)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    rows = sorted(read_jsonl(input_candidates), key=blind_sort_key)
    policy_audit = read_json(args.policy_audit) if as_abs(args.policy_audit).exists() else {}

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row.get("predicate_family"))].append(row)

    priority_rows = priority_sample(rows, args.priority_cap)
    sheet_specs = [
        ("blind_all_sheet.tsv", rows),
        ("blind_priority_sheet.tsv", priority_rows),
        ("blind_support_contact_sheet.tsv", by_family.get("support_contact", [])),
        ("blind_relative_vertical_sheet.tsv", by_family.get("relative_vertical", [])),
        ("blind_proximity_sheet.tsv", by_family.get("proximity", [])),
    ]

    sheets = []
    for filename, source_rows in sheet_specs:
        blind_rows = [blind_row(row) for row in source_rows]
        path = output_dir / filename
        write_tsv(path, blind_rows)
        sheets.append({"path": rel_path(path), "summary": summarize_rows(source_rows)})

    internal_key_rows = [internal_key_row(row) for row in rows]
    asset_request_rows = [asset_request_row(row) for row in rows]
    internal_key_path = output_dir / "internal_key.jsonl"
    asset_manifest_path = output_dir / "asset_request_manifest.jsonl"
    write_jsonl(internal_key_path, internal_key_rows)
    write_jsonl(asset_manifest_path, asset_request_rows)

    sample_blind_fields = list(blind_row(rows[0]).keys()) if rows else []
    blind_leakage = leakage_audit(sample_blind_fields)

    protocol = {
        "schema_version": "h002_full_train_independent_label_protocol_v0",
        "created_at": created_at,
        "input_candidates": rel_path(input_candidates),
        "policy_audit_status": policy_audit.get("status"),
        "objective": (
            "Collect independent relation reliability labels without exposing "
            "rank/status/role/label-policy metadata that explained the previous target."
        ),
        "hidden_from_annotator": [
            "prediction_id",
            "review_id",
            "proposed_audit_role",
            "role_reason",
            "label_match_status",
            "queue_kind",
            "candidate_axis",
            "geometry_status",
            "h001_verification_status",
            "semantic_rank",
            "rank_band",
            "semantic_score_raw",
            "semantic_score_norm",
            "p_geom_valid",
            "consistency_score",
            "disagreement_score",
            "underconfidence_score",
            "label_geometry_bucket",
            "bucket_top50",
            "bucket_top100",
            "machine_hint",
            "matched_gt_ids",
            "matched_predicates",
            "reason_codes",
        ],
        "shown_to_annotator": sample_blind_fields,
        "blind_review_fields": BLIND_REVIEW_FIELDS,
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
        "family_guidance": FAMILY_GUIDANCE,
        "asset_policy": {
            "current_asset_status": "not_generated",
            "asset_request_manifest": rel_path(asset_manifest_path),
            "multi_view_role": "audit_evidence_only",
            "deployable_input_allowed": False,
            "promotion_condition": (
                "Only after current S_e/G_e/C_e/U_e evidence passes rank/role-hidden "
                "independent-label controls."
            ),
        },
        "leakage_audit": blind_leakage,
    }
    protocol_path = output_dir / "protocol.json"
    write_json(protocol_path, protocol)

    status = (
        "full_train_independent_label_protocol_ready_needs_asset_packets"
        if blind_leakage["status"] == "pass"
        else "full_train_independent_label_protocol_leakage_blocked"
    )
    decision = (
        "The full-train independent protocol is ready as a blind labeling surface, "
        "but actual labeling should wait until asset packets are generated. This "
        "keeps the next step focused on evidence packets rather than another "
        "posterior fitting run."
        if blind_leakage["status"] == "pass"
        else "The blind sheet leaks forbidden metadata and must be fixed before labeling."
    )
    next_todo = (
        "full_train_independent_asset_packets: generate or link multi-view/mesh/point-cloud "
        "evidence packets for the blind rows, then run independent label readiness."
        if blind_leakage["status"] == "pass"
        else "fix_full_train_independent_blind_sheet_leakage"
    )
    summary = {
        "schema_version": "h002_full_train_independent_label_protocol_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_candidates": rel_path(input_candidates),
            "policy_audit": rel_path(args.policy_audit),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
            "rank_hidden_from_annotator": True,
            "score_hidden_from_annotator": True,
            "role_hidden_from_annotator": True,
            "label_status_hidden_from_annotator": True,
            "geometry_status_hidden_from_annotator": True,
        },
        "candidate_summary": summarize_rows(rows),
        "hidden_metadata_summary": hidden_summary(rows),
        "priority_sheet_cap": args.priority_cap,
        "blind_sheets": sheets,
        "internal_key": rel_path(internal_key_path),
        "asset_request_manifest": rel_path(asset_manifest_path),
        "protocol": rel_path(protocol_path),
        "leakage_audit": blind_leakage,
        "decision": decision,
        "next_todo": next_todo,
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    counts = summary["candidate_summary"]["by_family"]
    print(
        f"status={summary['status']} rows={summary['candidate_summary']['rows']} "
        f"families={counts} leakage={summary['leakage_audit']['status']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
