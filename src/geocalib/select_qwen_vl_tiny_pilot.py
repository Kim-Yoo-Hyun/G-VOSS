#!/usr/bin/env python3
"""Select a contract-only H001 Qwen-VL tiny pilot scope."""

from __future__ import annotations

import argparse
import json
import pickle
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA_VERSION = "h001_qwen_vl_tiny_pilot_scope_v1"
TARGET_FAMILIES = ["support_contact", "proximity", "relative_vertical"]
DEFAULT_EXCLUDED_SCANS = ["f62fd5fd-9a3f-2f44-883a-1e5cf819608e"]


@dataclass(frozen=True)
class Candidate:
    scan_id: str
    split_id: int
    subgraph_id: str
    subject_id: int
    object_id: int
    subject_label: str
    object_label: str
    predicate_id: int
    predicate_label: str
    predicate_family: str
    context_frame: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--contract-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    parser.add_argument(
        "--train-json",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/"
            "relationships_train.json"
        ),
    )
    parser.add_argument(
        "--train-scans",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/"
            "train_scans.txt"
        ),
    )
    parser.add_argument(
        "--heldout-scans",
        type=Path,
        default=Path(
            "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--views-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/views"
        ),
    )
    parser.add_argument("--rscan-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot"),
    )
    parser.add_argument("--records-per-family", type=int, default=10)
    parser.add_argument("--max-per-scan", type=int, default=3)
    parser.add_argument("--max-per-subgraph", type=int, default=2)
    parser.add_argument("--exclude-scan", action="append", default=[])
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
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def read_lines(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def first_context_frame(repo_root: Path, rscan_root: Path, scan_id: str) -> str | None:
    scan_dir = rscan_root / scan_id / "sequence"
    if not scan_dir.exists():
        return None
    frames = sorted(scan_dir.glob("frame-*.color.jpg"))
    if not frames:
        return None
    return relpath(repo_root, frames[0])


def load_object2image(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as handle:
            payload = pickle.load(handle)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def object_frames(payload: dict[str, Any], object_id: int) -> set[str]:
    frames: set[str] = set()
    for entry in payload.get(str(object_id), []):
        if len(entry) >= 4:
            frames.add(str(entry[0]))
    return frames


def has_shared_pair_view(payload: dict[str, Any], subject_id: int, object_id: int) -> bool:
    subject_frames = object_frames(payload, subject_id)
    object_frames_ = object_frames(payload, object_id)
    return bool(subject_frames and object_frames_ and subject_frames.intersection(object_frames_))


def build_family_map(contract: dict[str, Any]) -> dict[str, list[str]]:
    return {
        str(family): [str(item) for item in predicates]
        for family, predicates in contract["input_schema"]["predicate_family_map"].items()
    }


def predicate_to_family(family_map: dict[str, list[str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for family, labels in family_map.items():
        for label in labels:
            mapping[label] = family
    return mapping


def collect_candidates(
    repo_root: Path,
    train_json: Path,
    train_scans: set[str],
    heldout_scans: set[str],
    excluded_scans: set[str],
    views_dir: Path,
    rscan_root: Path,
    label_to_family: dict[str, str],
) -> tuple[list[Candidate], dict[str, Any]]:
    candidates: list[Candidate] = []
    skipped = Counter()
    seen_record_keys: set[tuple[str, int, int, str]] = set()
    for entry in load_json(train_json).get("scans", []):
        scan_id = str(entry["scan"])
        if train_scans and scan_id not in train_scans:
            skipped["not_in_train_scans"] += 1
            continue
        if scan_id in heldout_scans:
            skipped["heldout_scan"] += 1
            continue
        if scan_id in excluded_scans:
            skipped["explicitly_excluded_scan"] += 1
            continue
        view_path = views_dir / f"{scan_id}_object2image.pkl"
        if not view_path.exists():
            skipped["missing_object2image_view_metadata"] += 1
            continue
        object2image = load_object2image(view_path)
        if object2image is None:
            skipped["unreadable_object2image_view_metadata"] += 1
            continue
        context_frame = first_context_frame(repo_root, rscan_root, scan_id)
        if context_frame is None:
            skipped["missing_context_frame"] += 1
            continue
        split_id = int(entry["split"])
        subgraph_id = f"{scan_id}_{split_id}"
        objects = {int(key): str(value) for key, value in entry.get("objects", {}).items()}
        for relation in entry.get("relationships", []):
            subject_id = int(relation[0])
            object_id = int(relation[1])
            predicate_id = int(relation[2])
            predicate_label = str(relation[3])
            family = label_to_family.get(predicate_label)
            if family not in TARGET_FAMILIES:
                continue
            if subject_id == object_id:
                skipped["same_endpoint_relation"] += 1
                continue
            if subject_id not in objects or object_id not in objects:
                skipped["missing_object_label"] += 1
                continue
            if not has_shared_pair_view(object2image, subject_id, object_id):
                skipped["missing_shared_pair_view"] += 1
                continue
            key = (subgraph_id, subject_id, object_id, family)
            if key in seen_record_keys:
                skipped["duplicate_pair_family"] += 1
                continue
            seen_record_keys.add(key)
            candidates.append(
                Candidate(
                    scan_id=scan_id,
                    split_id=split_id,
                    subgraph_id=subgraph_id,
                    subject_id=subject_id,
                    object_id=object_id,
                    subject_label=objects[subject_id],
                    object_label=objects[object_id],
                    predicate_id=predicate_id,
                    predicate_label=predicate_label,
                    predicate_family=family,
                    context_frame=context_frame,
                )
            )
    audit = {
        "candidate_count": len(candidates),
        "family_counts": dict(Counter(item.predicate_family for item in candidates)),
        "skipped": dict(skipped),
    }
    return candidates, audit


def select_balanced(
    candidates: list[Candidate],
    records_per_family: int,
    max_per_scan: int,
    max_per_subgraph: int,
) -> tuple[list[Candidate], dict[str, Any]]:
    by_family: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_family[candidate.predicate_family].append(candidate)
    for family in by_family:
        by_family[family].sort(
            key=lambda item: (
                item.scan_id,
                item.split_id,
                item.subject_label,
                item.object_label,
                item.subject_id,
                item.object_id,
                item.predicate_label,
            )
        )

    selected: list[Candidate] = []
    scan_counts: Counter[str] = Counter()
    subgraph_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()

    def take(candidate: Candidate) -> None:
        selected.append(candidate)
        scan_counts[candidate.scan_id] += 1
        subgraph_counts[candidate.subgraph_id] += 1
        family_counts[candidate.predicate_family] += 1

    for family in TARGET_FAMILIES:
        for candidate in by_family.get(family, []):
            if family_counts[family] >= records_per_family:
                break
            if scan_counts[candidate.scan_id] >= max_per_scan:
                continue
            if subgraph_counts[candidate.subgraph_id] >= max_per_subgraph:
                continue
            take(candidate)

    for family in TARGET_FAMILIES:
        if family_counts[family] >= records_per_family:
            continue
        for candidate in by_family.get(family, []):
            if family_counts[family] >= records_per_family:
                break
            if candidate in selected:
                continue
            take(candidate)

    selected.sort(key=lambda item: (TARGET_FAMILIES.index(item.predicate_family), item.scan_id, item.split_id))
    selection_audit = {
        "selected_count": len(selected),
        "family_counts": dict(family_counts),
        "scan_count": len(scan_counts),
        "scan_counts": dict(sorted(scan_counts.items())),
        "subgraph_count": len(subgraph_counts),
    }
    return selected, selection_audit


def record_id(candidate: Candidate) -> str:
    return (
        f"qwen_tiny_pilot::{candidate.subgraph_id}::"
        f"obj_{candidate.subject_id}->obj_{candidate.object_id}::{candidate.predicate_family}"
    )


def input_record(candidate: Candidate, family_map: dict[str, list[str]]) -> dict[str, Any]:
    rid = record_id(candidate)
    safe_id = sanitize(rid)
    return {
        "schema_version": "h001_qwen_vl_input_v2",
        "record_id": rid,
        "scan_id": candidate.scan_id,
        "subgraph_id": candidate.subgraph_id,
        "split": "pilot",
        "subject_id": candidate.subject_id,
        "object_id": candidate.object_id,
        "subject_label": candidate.subject_label,
        "object_label": candidate.object_label,
        "predicate_family": candidate.predicate_family,
        "candidate_predicates": family_map[candidate.predicate_family],
        "view_set_id": f"{candidate.subgraph_id}::obj_{candidate.subject_id}->obj_{candidate.object_id}::tiny_v0",
        "crop_paths": [
            {
                "path": f"local_dataset/qwen_vl_crops/tiny_pilot/{safe_id}/pair_view_000.png",
                "role": "pair",
                "view_id": "pair_view_000",
                "frame_id": None,
                "subject_bbox_xyxy": None,
                "object_bbox_xyxy": None,
            },
            {
                "path": candidate.context_frame,
                "role": "context",
                "view_id": "context_frame_000",
                "frame_id": Path(candidate.context_frame).name,
                "subject_bbox_xyxy": None,
                "object_bbox_xyxy": None,
            },
        ],
    }


def selection_record(candidate: Candidate) -> dict[str, Any]:
    return {
        "record_id": record_id(candidate),
        "scan_id": candidate.scan_id,
        "source_split": "train",
        "source_split_id": candidate.split_id,
        "subgraph_id": candidate.subgraph_id,
        "subject_id": candidate.subject_id,
        "object_id": candidate.object_id,
        "subject_label": candidate.subject_label,
        "object_label": candidate.object_label,
        "predicate_family": candidate.predicate_family,
        "source_predicate_id": candidate.predicate_id,
        "source_predicate_label": candidate.predicate_label,
        "not_for_prompt": True,
    }


def raw_response_template(row: dict[str, Any]) -> dict[str, str]:
    predicate = row["candidate_predicates"][0]
    payload = {
        "answer_is_visible": True,
        "predictions": [
            {
                "predicate": predicate,
                "confidence": 0.5,
                "rationale_short": "contract-only parser template",
            }
        ],
    }
    return {"record_id": row["record_id"], "raw_response": json.dumps(payload, sort_keys=True)}


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Tiny Pilot Scope",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This freezes a non-held-out tiny pilot input scope for Qwen-VL prompt/parser runtime smoke.",
        "It does not download a Qwen model, run inference, render pair crops, or create metric evidence.",
        "",
        "## Counts",
        "",
        f"- input rows: `{manifest['counts']['input_rows']}`",
        f"- scans: `{manifest['counts']['scan_count']}`",
        f"- subgraphs: `{manifest['counts']['subgraph_count']}`",
        f"- held-out overlaps: `{manifest['leakage_checks']['heldout_overlap_count']}`",
        "",
        "## Family Counts",
        "",
    ]
    for family, count in manifest["counts"]["family_counts"].items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
        ]
    )
    for name, path in manifest["outputs"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This artifact is only a pilot scope contract. It is not Qwen-VL performance evidence and must not be used in paper metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    contract_dir = resolve(repo_root, args.contract_dir)
    train_json = resolve(repo_root, args.train_json)
    train_scans_path = resolve(repo_root, args.train_scans)
    heldout_scans_path = resolve(repo_root, args.heldout_scans)
    views_dir = resolve(repo_root, args.views_dir)
    rscan_root = resolve(repo_root, args.rscan_root)
    out_dir = resolve(repo_root, args.out)
    assert contract_dir is not None
    assert train_json is not None
    assert views_dir is not None
    assert rscan_root is not None
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    contract = load_json(contract_dir / "adapter_contract.json")
    family_map = build_family_map(contract)
    label_to_family = predicate_to_family(family_map)
    train_scans = set(read_lines(train_scans_path))
    heldout_scans = set(read_lines(heldout_scans_path))
    excluded_scans = set(DEFAULT_EXCLUDED_SCANS) | set(args.exclude_scan)

    candidates, candidate_audit = collect_candidates(
        repo_root=repo_root,
        train_json=train_json,
        train_scans=train_scans,
        heldout_scans=heldout_scans,
        excluded_scans=excluded_scans,
        views_dir=views_dir,
        rscan_root=rscan_root,
        label_to_family=label_to_family,
    )
    selected, selection_audit = select_balanced(
        candidates,
        records_per_family=args.records_per_family,
        max_per_scan=args.max_per_scan,
        max_per_subgraph=args.max_per_subgraph,
    )
    expected = args.records_per_family * len(TARGET_FAMILIES)
    heldout_overlap = sorted({item.scan_id for item in selected}.intersection(heldout_scans))
    family_counts = Counter(item.predicate_family for item in selected)
    errors: list[str] = []
    if len(selected) != expected:
        errors.append(f"selected_count:{len(selected)} expected:{expected}")
    missing_families = {
        family: args.records_per_family - family_counts.get(family, 0)
        for family in TARGET_FAMILIES
        if family_counts.get(family, 0) != args.records_per_family
    }
    if missing_families:
        errors.append(f"family_quota_mismatch:{missing_families}")
    if heldout_overlap:
        errors.append(f"heldout_overlap:{heldout_overlap}")

    input_rows = [input_record(item, family_map) for item in selected]
    selection_rows = [selection_record(item) for item in selected]
    raw_template_rows = [raw_response_template(row) for row in input_rows]
    scans = sorted({item.scan_id for item in selected})
    (out_dir / "scans.txt").write_text("\n".join(scans) + "\n", encoding="utf-8")
    write_jsonl(out_dir / "input.jsonl", input_rows)
    write_jsonl(out_dir / "selection.jsonl", selection_rows)
    write_jsonl(out_dir / "raw_response_template.jsonl", raw_template_rows)

    status = "tiny_pilot_scope_ready_no_model_runtime" if not errors else "blocked_tiny_pilot_scope_errors"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "runtime_policy": "no_model_download_no_inference_no_crop_rendering",
        "parameters": {
            "families": TARGET_FAMILIES,
            "records_per_family": args.records_per_family,
            "max_per_scan": args.max_per_scan,
            "max_per_subgraph": args.max_per_subgraph,
            "excluded_scans": sorted(excluded_scans),
            "source_split": "train",
        },
        "inputs": {
            "contract_dir": relpath(repo_root, contract_dir),
            "train_json": relpath(repo_root, train_json),
            "train_scans": relpath(repo_root, train_scans_path),
            "heldout_scans": relpath(repo_root, heldout_scans_path),
            "views_dir": relpath(repo_root, views_dir),
            "rscan_root": relpath(repo_root, rscan_root),
        },
        "outputs": {
            "input_jsonl": relpath(repo_root, out_dir / "input.jsonl"),
            "selection_jsonl": relpath(repo_root, out_dir / "selection.jsonl"),
            "raw_response_template_jsonl": relpath(repo_root, out_dir / "raw_response_template.jsonl"),
            "scans_txt": relpath(repo_root, out_dir / "scans.txt"),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "counts": {
            "input_rows": len(input_rows),
            "scan_count": len(scans),
            "subgraph_count": len({item.subgraph_id for item in selected}),
            "family_counts": dict(sorted(family_counts.items())),
            "source_predicate_counts": dict(sorted(Counter(item.predicate_label for item in selected).items())),
        },
        "candidate_audit": candidate_audit,
        "selection_audit": selection_audit,
        "leakage_checks": {
            "heldout_overlap_count": len(heldout_overlap),
            "heldout_overlap_scans": heldout_overlap,
            "input_records_contain_source_predicate_label": False,
            "selection_jsonl_contains_source_predicate_label_for_internal_audit_only": True,
        },
        "crop_status": {
            "pair_crops": "reserved_paths_pending_crop_render",
            "context_frames": "existing_raw_3rscan_frame_paths",
            "crop_rendering_started": False,
        },
        "validation": {"errors": errors, "warnings": []},
        "next_action": "Run qwen_vl_tiny_pilot_validator; do not download a model or run inference until explicit model id/revision/local-dir are fixed.",
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
