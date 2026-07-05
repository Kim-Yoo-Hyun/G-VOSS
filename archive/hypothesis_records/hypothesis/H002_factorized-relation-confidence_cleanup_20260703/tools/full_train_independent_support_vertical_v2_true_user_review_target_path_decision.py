#!/usr/bin/env python3
"""Decide the H002 path after true-user-review target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_target_independence_audit_rank_band70_codex_proxy_pending_confirmation"
DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_ingestion_rank_band70_codex_proxy_pending_confirmation"
DEFAULT_REVIEW_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_true_user_review_target_path_decision"

RECOMMENDED_REVIEW_SHEET = DEFAULT_REVIEW_DIR / "true_user_review_sheet_rank_band70.tsv"
REVIEWER_INSTRUCTIONS = DEFAULT_REVIEW_DIR / "reviewer_instructions.md"
POST_LABEL_MANIFEST = DEFAULT_REVIEW_DIR / "true_user_manifest_rank_band70_post_label_only.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
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


def count_lines(path: Path) -> int:
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["audit_extract"]["relation_reliability_true_user_review_target"]
    geometry = summary["audit_extract"]["geometry_validity_true_user_review_target"]
    lines = [
        "# H002 True User Review Target Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Direct Answer",
        "",
        "현재 blocker는 posterior 결합 방식보다 결합을 검증할 target/evidence 요소의 독립성 문제다.",
        "더 강한 combiner를 넣어도 hidden prior carryover가 남은 target을 잘 맞추는 실험이 될 가능성이 크다.",
        "",
        "## Audit Extract",
        "",
        "| Target | Rows | Pos | Neg | Strict Slice | Construction Slice | Main Problem |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
        (
            f"| `geometry_validity_true_user_review_target` | {geometry['rows']} | {geometry['positive']} | "
            f"{geometry['negative']} | `{geometry['strict_slice']}` | `{geometry['construction_slice']}` | "
            f"{geometry['main_problem']} |"
        ),
        (
            f"| `relation_reliability_true_user_review_target` | {relation['rows']} | {relation['positive']} | "
            f"{relation['negative']} | `{relation['strict_slice']}` | `{relation['construction_slice']}` | "
            f"{relation['main_problem']} |"
        ),
        "",
        "## Element Failure Matrix",
        "",
        "| Element | Problem | Why Combiner Does Not Fix It | Required Fix |",
        "| --- | --- | --- | --- |",
    ]
    for item in summary["element_failure_matrix"]:
        lines.append(
            f"| `{item['element']}` | {item['problem']} | {item['why_combiner_does_not_fix']} | {item['required_fix']} |"
        )
    lines.extend(
        [
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{summary['decision']}`",
            "",
            "Reason:",
            "",
            summary["decision_reason"],
            "",
            "## Real Label Collection Packet",
            "",
            "| Item | Path / Count |",
            "| --- | --- |",
        ]
    )
    packet = summary["real_label_collection_packet"]
    for key, value in packet.items():
        lines.append(f"| `{key}` | `{value}` |")
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


def write_collection_request(path: Path, summary: dict[str, Any]) -> None:
    packet = summary["real_label_collection_packet"]
    lines = [
        "# H002 Real Independent Label Collection Request",
        "",
        "## Purpose",
        "",
        "Codex-proxy true-user review target은 hidden prior carryover를 제거하지 못했다.",
        "따라서 posterior smoke 전에 실제 독립 user/external reviewer가 같은 packet evidence만 보고 label을 채워야 한다.",
        "",
        "## Use This Sheet",
        "",
        f"`{packet['review_sheet']}`",
        "",
        "## Instructions",
        "",
        f"`{packet['reviewer_instructions']}`",
        "",
        "## Must Not Use",
        "",
        "- semantic score/rank",
        "- `p_geom_valid`",
        "- geometry status",
        "- prior relation validity labels",
        "- previous Codex proxy labels",
        "- posterior target fields",
        "- hidden manifest fields",
        "",
        "## Required Output",
        "",
        "Fill the review completion fields in the sheet and preserve the `blind_review_id` values.",
        "After label lock, the post-label manifest can be joined for audit only.",
        "",
        "## Boundary",
        "",
        "- This is train-only hypothesis-stage collection.",
        "- Multi-view/mesh/contact packets are audit evidence, not model inputs.",
        "- Posterior smoke remains blocked until the completed labels pass target-independence audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    review_dir = as_abs(args.review_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    audit_summary = read_json(audit_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")

    relation_decision = audit_summary["target_decisions"]["relation_reliability_true_user_review_target"]
    relation_original = relation_decision["original"]
    relation_construction = relation_decision.get("recommended_construction_slice")
    geometry_decision = audit_summary["target_decisions"]["geometry_validity_true_user_review_target"]
    geometry_original = geometry_decision["original"]

    review_sheet = review_dir / "true_user_review_sheet_rank_band70.tsv"
    reviewer_instructions = review_dir / "reviewer_instructions.md"
    post_label_manifest = review_dir / "true_user_manifest_rank_band70_post_label_only.jsonl"
    review_sheet_lines = count_lines(review_sheet)
    post_label_manifest_lines = count_lines(post_label_manifest)

    element_failure_matrix = [
        {
            "element": "geometry_validity_target",
            "problem": "69/1에 가까운 single-class target이라 discrimination target으로 약하다.",
            "why_combiner_does_not_fix": "어떤 combiner도 거의 항상 positive인 target에서 geometry validity 구분 능력을 검증할 수 없다.",
            "required_fix": "contradiction/uncertain 사례를 독립 label로 확보하거나 geometry target을 posterior main target에서 제외한다.",
        },
        {
            "element": "relation_reliability_target",
            "problem": "`relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden` carryover가 남았다.",
            "why_combiner_does_not_fix": "성능이 좋아도 relation evidence 결합이 아니라 hidden prior structure 재현일 수 있다.",
            "required_fix": "prior labels를 보지 않은 실제 독립 reviewer label을 확보하고 다시 target-independence audit을 수행한다.",
        },
        {
            "element": "label_source",
            "problem": "현재 label은 Codex-proxy pending-confirmation이며 실제 true user/external annotation이 아니다.",
            "why_combiner_does_not_fix": "label source가 독립적이지 않으면 model score를 해석할 ground truth가 없다.",
            "required_fix": "기존 blank review sheet를 실제 user/external reviewer가 packet evidence만 보고 채운다.",
        },
        {
            "element": "candidate_selection",
            "problem": "rank/queue/geometry-status construction axis는 통제됐지만 prior relation-label axis가 target과 연결된다.",
            "why_combiner_does_not_fix": "balanced construction slice는 plumbing diagnostic일 뿐 method-validation target이 아니다.",
            "required_fix": "prior-label-balanced sample을 충분한 size로 확장하거나 real labels로 carryover를 재검증한다.",
        },
        {
            "element": "deployable_feature_join",
            "problem": "source score/rank와 `p_geom_valid` feature join은 아직 target audit 이후로 미뤄져 있다.",
            "why_combiner_does_not_fix": "clean target 없이 feature를 join하면 feature gain과 target shortcut이 섞인다.",
            "required_fix": "strict/defensible target이 생긴 뒤에만 semantic/geometric feature join과 posterior smoke를 연다.",
        },
    ]

    option_matrix = [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "strict relation-reliability slice가 없고 hidden prior carryover가 남아 있다.",
        },
        {
            "option": "upgrade_combiner_now",
            "verdict": "reject",
            "reason": "현재 blocker는 combiner capacity가 아니라 target/evidence contract다.",
        },
        {
            "option": "use_rank_band_balanced_true_user_review",
            "verdict": "diagnostic_only",
            "reason": "70 rows 35/35이지만 harmful prior risk 3개가 남아 method evidence가 아니다.",
        },
        {
            "option": "revise_codex_proxy_target_again",
            "verdict": "defer",
            "reason": "여러 proxy target pass가 같은 hidden prior carryover를 반복했다.",
        },
        {
            "option": "collect_real_independent_labels_on_rank_band70",
            "verdict": "select",
            "reason": "기존 packet/sheet가 준비되어 있고, target independence 문제를 직접 해결하는 경로다.",
        },
        {
            "option": "expand_to_full127_after_real_first_pass",
            "verdict": "conditional",
            "reason": "rank_band70 실제 label도 strict slice가 없거나 class count가 부족하면 full127로 확장한다.",
        },
    ]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "element_failure_matrix": output_dir / "element_failure_matrix.json",
        "option_matrix": output_dir / "option_matrix.json",
        "real_label_collection_request": output_dir / "real_label_collection_request.md",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_true_user_review_target_path_decision_v1",
        "status": "full_train_independent_support_vertical_v2_true_user_review_target_path_decision_collect_real_independent_labels",
        "created_at": created_at,
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "review_sheet": rel_path(review_sheet),
            "reviewer_instructions": rel_path(reviewer_instructions),
            "post_label_manifest": rel_path(post_label_manifest),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "combiner_upgrade_allowed_before_clean_target": False,
            "codex_proxy_labels_as_method_evidence": False,
            "real_independent_label_required": True,
            "multi_view_as_model_input": False,
            "h001_modified": False,
        },
        "audit_extract": {
            "geometry_validity_true_user_review_target": {
                "rows": geometry_original["rows"],
                "positive": geometry_original["positive"],
                "negative": geometry_original["negative"],
                "strict_slice": "none",
                "construction_slice": "none",
                "main_problem": "near_single_class",
            },
            "relation_reliability_true_user_review_target": {
                "rows": relation_original["rows"],
                "positive": relation_original["positive"],
                "negative": relation_original["negative"],
                "strict_slice": "none",
                "construction_slice": relation_construction["slice_name"] if relation_construction else "none",
                "main_problem": "hidden_prior_carryover",
                "top_harmful_prior_risks": relation_original["top_harmful_prior_risks"],
            },
        },
        "ingestion_status": ingestion_summary.get("status"),
        "element_failure_matrix": element_failure_matrix,
        "option_matrix": option_matrix,
        "decision": "collect_real_independent_labels_on_rank_band70_first",
        "decision_reason": (
            "Posterior 결합 방식은 아직 검증 대상이 아니다. 현재 blocker는 target/evidence 요소가 "
            "hidden prior carryover에서 충분히 독립적이지 않다는 점이며, 이를 직접 해결하려면 "
            "기존 rank_band70 packet을 실제 독립 reviewer가 다시 label해야 한다."
        ),
        "real_label_collection_packet": {
            "review_sheet": rel_path(review_sheet),
            "review_sheet_rows_plus_header": review_sheet_lines,
            "reviewer_instructions": rel_path(reviewer_instructions),
            "post_label_manifest_audit_only": rel_path(post_label_manifest),
            "post_label_manifest_rows": post_label_manifest_lines,
        },
        "next_todo": "collect_real_user_labels_on_rank_band70_sheet",
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["element_failure_matrix"], {"items": element_failure_matrix})
    write_json(output_paths["option_matrix"], {"items": option_matrix})
    write_report(output_paths["report"], summary)
    write_collection_request(output_paths["real_label_collection_request"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    relation = summary["audit_extract"]["relation_reliability_true_user_review_target"]
    geometry = summary["audit_extract"]["geometry_validity_true_user_review_target"]
    print(
        f"status={summary['status']} decision={summary['decision']} "
        f"relation_rows={relation['rows']} relation_pos={relation['positive']} relation_neg={relation['negative']} "
        f"relation_strict={relation['strict_slice']} relation_construction={relation['construction_slice']} "
        f"geometry_pos={geometry['positive']} geometry_neg={geometry['negative']} "
        f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
