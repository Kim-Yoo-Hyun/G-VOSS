#!/usr/bin/env python3
"""Stage an isolated Open3DSG runtime for H002 train-origin raw dumps."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_open3dsg_train_pilot_runtime_stage_v1"
EMPTY_SUBSET = {"scans": []}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h002_train_pilot_runtime"),
    )
    parser.add_argument("--raw-scans-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument(
        "--template-runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument(
        "--source-contract-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/source_contract"
        ),
    )
    parser.add_argument("--contexts-file-name", default="pilot_contexts.jsonl")
    parser.add_argument("--subset-file-name", default="relationships_train_pilot.json")
    parser.add_argument("--scope-label", default="train_pilot")
    parser.add_argument("--report-title", default="H002 Open3DSG Train Pilot Runtime Stage")
    parser.add_argument(
        "--feature-load-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/output/features/"
            "clip_features_h001_official_blip_top5_scales3"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/runtime_stage"
        ),
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
    return rows


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def write_lines(path: Path, lines: list[str]) -> dict[str, Any]:
    content = "".join(f"{line}\n" for line in lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return {"path": str(path), "status": "ready_existing", "lines": len(lines)}
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "status": "written", "lines": len(lines)}


def copy_file(repo_root: Path, src: Path, dst: Path) -> dict[str, Any]:
    record = {"src": relpath(repo_root, src), "dst": relpath(repo_root, dst), "src_exists": src.is_file()}
    if not src.is_file():
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or (dst.exists() and not dst.is_file()):
        record["status"] = "blocked_existing_wrong_type"
        return record
    if dst.exists() and src.read_bytes() == dst.read_bytes():
        record["status"] = "ready_existing"
        return record
    shutil.copy2(src, dst)
    record["status"] = "copied"
    record["bytes"] = dst.stat().st_size
    return record


def write_json_payload(repo_root: Path, dst: Path, payload: Any) -> dict[str, Any]:
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.is_file() and dst.read_text(encoding="utf-8") == content:
        return {"path": relpath(repo_root, dst), "status": "ready_existing"}
    if dst.exists() and not dst.is_file():
        return {"path": relpath(repo_root, dst), "status": "blocked_existing_wrong_type"}
    dst.write_text(content, encoding="utf-8")
    return {"path": relpath(repo_root, dst), "status": "written"}


def symlink_path(repo_root: Path, src: Path, dst: Path, *, is_dir: bool) -> dict[str, Any]:
    record = {
        "src": relpath(repo_root, src),
        "dst": relpath(repo_root, dst),
        "src_exists": src.is_dir() if is_dir else src.is_file(),
    }
    if not record["src_exists"]:
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    target = os.path.relpath(src.resolve(), dst.parent.resolve())
    if dst.is_symlink():
        if os.readlink(dst) == target:
            record["status"] = "ready_symlink"
        else:
            dst.unlink()
            dst.symlink_to(target, target_is_directory=is_dir)
            record["status"] = "normalized_symlink"
        return record
    if dst.exists():
        correct_type = dst.is_dir() if is_dir else dst.is_file()
        record["status"] = "ready_existing_path" if correct_type else "blocked_existing_wrong_type"
        return record
    dst.symlink_to(target, target_is_directory=is_dir)
    record["status"] = "created_symlink"
    return record


def sequence_summary(scan_dir: Path) -> dict[str, Any]:
    sequence_dir = scan_dir / "sequence"
    return {
        "sequence_dir_exists": sequence_dir.is_dir(),
        "color_frames": len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.is_dir() else 0,
        "info_exists": (sequence_dir / "_info.txt").is_file(),
    }


def feature_id(row: dict[str, Any]) -> str:
    return f"{row['scan_id']}-{hex(int(row['split']))[-1]}.pt"


def feature_paths(feature_load_dir: Path, fid: str) -> tuple[Path, Path, Path]:
    return (
        feature_load_dir
        / "export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1"
        / fid,
        feature_load_dir / "export_obj_clip_valids" / fid,
        feature_load_dir
        / "export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998"
        / fid,
    )


def feature_gate(feature_load_dir: Path, contexts: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[str] = []
    for row in contexts:
        fid = feature_id(row)
        if not all(path.is_file() for path in feature_paths(feature_load_dir, fid)):
            missing.append(fid)
    return {
        "feature_load_dir": str(feature_load_dir),
        "checked_contexts": len(contexts),
        "missing_contexts": len(missing),
        "missing_sample": missing[:10],
        "status": "ready" if not missing else "blocked",
    }


def make_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['report_title']}",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Counts",
        "",
        f"- selected scans: `{payload['counts']['selected_scans']}`",
        f"- contexts: `{payload['counts']['contexts']}`",
        f"- linked scans: `{payload['counts']['linked_scans']}`",
        f"- sequence-ready scans: `{payload['counts']['sequence_ready_scans']}`",
        f"- missing feature contexts: `{payload['feature_gate']['missing_contexts']}`",
        "",
        "## Runtime",
        "",
        f"- runtime root: `{payload['paths']['runtime_root']}`",
        f"- source root: `{payload['paths']['runtime_source_root']}`",
        f"- subset root: `{payload['paths']['runtime_subset_root']}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runtime_root = resolve(repo_root, args.runtime_root).resolve()
    raw_scans_root = resolve(repo_root, args.raw_scans_root).resolve()
    template_runtime = resolve(repo_root, args.template_runtime_root).resolve()
    source_contract_dir = resolve(repo_root, args.source_contract_dir).resolve()
    feature_load_dir = resolve(repo_root, args.feature_load_dir).resolve()
    out_dir = resolve(repo_root, args.out_dir).resolve()

    source_contract = source_contract_dir / "source_contract.json"
    selected_scans_path = source_contract_dir / "selected_scans.txt"
    contexts_path = source_contract_dir / args.contexts_file_name
    source_subset_path = source_contract_dir / args.subset_file_name

    blockers: list[str] = []
    for label, path in {
        "source_contract": source_contract,
        "selected_scans": selected_scans_path,
        "contexts": contexts_path,
        "source_subset": source_subset_path,
    }.items():
        if not path.is_file():
            blockers.append(f"missing_{label}:{relpath(repo_root, path)}")

    selected_scans: list[str] = []
    contexts: list[dict[str, Any]] = []
    source_subset: dict[str, Any] = EMPTY_SUBSET
    if not blockers:
        contract = load_json(source_contract)
        if contract.get("status") != "ready":
            blockers.append(f"source_contract_not_ready:{contract.get('status')}")
        selected_scans = read_lines(selected_scans_path)
        contexts = load_jsonl(contexts_path)
        source_subset = load_json(source_subset_path)

    records: list[dict[str, Any]] = []
    subset_records: list[dict[str, Any]] = []
    metadata_records: list[dict[str, Any]] = []
    runtime_records: list[dict[str, Any]] = []

    runtime_r3scan = runtime_root / "data/3RScan"
    runtime_subset = runtime_r3scan / "3DSSG_subset"
    runtime_output = runtime_root / "output"

    for scan_id in selected_scans:
        src = raw_scans_root / scan_id
        dst = runtime_r3scan / scan_id
        record = {"scan_id": scan_id, **symlink_path(repo_root, src, dst, is_dir=True)}
        record.update(sequence_summary(dst))
        records.append(record)

    linked_scans = sum(
        1
        for record in records
        if record["status"] in {"created_symlink", "ready_symlink", "normalized_symlink", "ready_existing_path"}
    )
    sequence_ready = sum(
        1
        for record in records
        if record["sequence_dir_exists"] and record["color_frames"] > 0 and record["info_exists"]
    )

    if linked_scans != len(selected_scans):
        blockers.append(f"linked_scans:{linked_scans}/{len(selected_scans)}")
    if sequence_ready != len(selected_scans):
        blockers.append(f"sequence_ready_scans:{sequence_ready}/{len(selected_scans)}")

    subset_src_root = repo_root / "local_dataset/3DSSG_subset"
    for filename in ("classes.txt", "relationships.txt", "relationships.json"):
        subset_records.append(copy_file(repo_root, subset_src_root / filename, runtime_subset / filename))

    subset_records.append(write_json_payload(repo_root, runtime_subset / "relationships_validation.json", source_subset))
    subset_records.append(write_json_payload(repo_root, runtime_subset / "relationships_train.json", EMPTY_SUBSET))
    subset_records.append(write_json_payload(repo_root, runtime_subset / "relationships_test.json", EMPTY_SUBSET))
    subset_records.append(write_lines(runtime_subset / "validation_scans.txt", selected_scans))
    subset_records.append(write_lines(runtime_subset / "train_scans.txt", []))
    subset_records.append(write_lines(runtime_subset / "test_scans.txt", []))

    for record in subset_records:
        if str(record.get("status", "")).startswith("blocked") or record.get("status") == "missing_source":
            blockers.append(f"subset:{record.get('status')}:{record.get('dst') or record.get('path')}")

    for filename in (
        "classes.txt",
        "relationships.txt",
        "relationships_custom.txt",
        "obj_boxes_train_refined.json",
        "obj_boxes_val_refined.json",
    ):
        metadata_records.append(
            copy_file(repo_root, template_runtime / "data/3RScan" / filename, runtime_r3scan / filename)
        )

    metadata_links = {
        "SCANNET": (template_runtime / "data/SCANNET", runtime_root / "data/SCANNET"),
        "OpenSG_3RScan/views": (
            template_runtime / "output/datasets/OpenSG_3RScan/views",
            runtime_output / "datasets/OpenSG_3RScan/views",
        ),
        "OpenSG_3RScan/preprocessed": (
            template_runtime / "output/datasets/OpenSG_3RScan/preprocessed",
            runtime_output / "datasets/OpenSG_3RScan/preprocessed",
        ),
        "OpenSG_ScanNet": (
            template_runtime / "output/datasets/OpenSG_ScanNet",
            runtime_output / "datasets/OpenSG_ScanNet",
        ),
        "source": (
            template_runtime / "source/open3dsg_source",
            runtime_root / "source/open3dsg_source",
        ),
        "checkpoints": (
            template_runtime / "output/checkpoints",
            runtime_output / "checkpoints",
        ),
    }
    for name, (src, dst) in metadata_links.items():
        record = {"name": name, **symlink_path(repo_root, src, dst, is_dir=True)}
        metadata_records.append(record)

    for path in (
        runtime_output / "features",
        runtime_root / "mlops/opensg/mlflow",
        runtime_root / "mlops/opensg/tensorboards",
    ):
        path.mkdir(parents=True, exist_ok=True)
        runtime_records.append({"path": relpath(repo_root, path), "status": "ready_dir"})

    for record in metadata_records:
        if str(record.get("status", "")).startswith("blocked") or record.get("status") == "missing_source":
            blockers.append(f"metadata:{record.get('name', record.get('dst'))}:{record.get('status')}")

    feature_result = feature_gate(feature_load_dir, contexts)
    if feature_result["status"] != "ready":
        blockers.append(f"features_missing:{feature_result['missing_contexts']}/{feature_result['checked_contexts']}")

    paths_payload = {
        "runtime_root": relpath(repo_root, runtime_root),
        "runtime_r3scan_root": relpath(repo_root, runtime_r3scan),
        "runtime_subset_root": relpath(repo_root, runtime_subset),
        "runtime_source_root": relpath(repo_root, runtime_root / "source/open3dsg_source"),
        "source_contract": relpath(repo_root, source_contract),
        "selected_scans": relpath(repo_root, selected_scans_path),
        "contexts": relpath(repo_root, contexts_path),
        "source_subset": relpath(repo_root, source_subset_path),
        "feature_load_dir": relpath(repo_root, feature_load_dir),
        "records": relpath(repo_root, out_dir / "records.jsonl"),
        "subset_records": relpath(repo_root, out_dir / "subset_records.jsonl"),
        "metadata_records": relpath(repo_root, out_dir / "metadata_records.jsonl"),
        "runtime_records": relpath(repo_root, out_dir / "runtime_records.jsonl"),
    }
    counts_payload = {
        "selected_scans": len(selected_scans),
        "contexts": len(source_subset.get("scans", [])),
        "linked_scans": linked_scans,
        "sequence_ready_scans": sequence_ready,
    }
    if args.scope_label == "train_pilot":
        paths_payload["pilot_subset"] = relpath(repo_root, source_subset_path)
        counts_payload["pilot_contexts"] = len(source_subset.get("scans", []))

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "ready" if not blockers else "blocked",
        "paths": paths_payload,
        "counts": counts_payload,
        "feature_gate": feature_result,
        "record_status_counts": dict(Counter(str(record.get("status")) for record in records)),
        "subset_status_counts": dict(Counter(str(record.get("status")) for record in subset_records)),
        "metadata_status_counts": dict(Counter(str(record.get("status")) for record in metadata_records)),
        "runtime_status_counts": dict(Counter(str(record.get("status")) for record in runtime_records)),
        "blockers": blockers,
        "report_title": args.report_title,
        "scope_label": args.scope_label,
        "claim_boundary": (
            "This stages a train-origin H002 subset into the Open3DSG eval split because the "
            "upstream Open3DSG --test path reads validation filenames. It is still train-set H002 "
            "evidence only if provenance records point to the H002 train source subset and no "
            "held-out source artifacts are used."
        ),
    }

    if args.write:
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "manifest.json", payload)
        write_jsonl(out_dir / "records.jsonl", records)
        write_jsonl(out_dir / "subset_records.jsonl", subset_records)
        write_jsonl(out_dir / "metadata_records.jsonl", metadata_records)
        write_jsonl(out_dir / "runtime_records.jsonl", runtime_records)
        (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": payload["status"],
                "blockers": blockers,
                "runtime_root": relpath(repo_root, runtime_root),
                "selected_scans": len(selected_scans),
                "contexts": len(source_subset.get("scans", [])),
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
