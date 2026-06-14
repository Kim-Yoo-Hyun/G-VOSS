#!/usr/bin/env python3
"""Plan Open3DSG runtime artifact acquisition for H001."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_SOURCE = Path("/tmp/open3dsg_source")
DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "runtime_plan"
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"

SCAN_REQUIRED_RAW = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)

SCAN_REQUIRED_OPEN3DSG = (
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
)

SEQUENCE_PATTERNS = ("*.color.jpg", "*.depth.pgm", "*.pose.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_scans(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_labels(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def git_head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def count_scans_with(scan_root: Path, scans: list[str], relative_file: str) -> int:
    return sum(1 for scan_id in scans if (scan_root / scan_id / relative_file).exists())


def count_sequence(scan_root: Path, scans: list[str], pattern: str) -> dict[str, int]:
    scans_with = 0
    file_count = 0
    for scan_id in scans:
        files = list((scan_root / scan_id / "sequence").glob(pattern))
        if files:
            scans_with += 1
            file_count += len(files)
    return {"scans": scans_with, "files": file_count}


def exists_any(root: Path, pattern: str) -> bool:
    return root.exists() and any(root.rglob(pattern))


def count_preprocessed_pickles(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob("data_dict_*.pkl"))


def expected_preprocessed_pickles(subset_root: Path) -> int:
    expected = 0
    for split in ("train", "validation"):
        path = subset_root / f"relationships_{split}.json"
        payload = load_json(path)
        scans = payload.get("scans", []) if isinstance(payload, dict) else []
        expected += len(scans)
    return expected


def subset_counts(subset_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split in ("train", "validation", "test"):
        path = subset_root / f"relationships_{split}.json"
        payload = load_json(path)
        scans = payload.get("scans", []) if isinstance(payload, dict) else []
        out[split] = {
            "path": relpath(path),
            "exists": path.exists(),
            "subgraphs": len(scans),
            "unique_scans": len({entry.get("scan") for entry in scans if entry.get("scan")}),
            "relations": sum(len(entry.get("relationships", [])) for entry in scans),
        }
    return out


def source_facts(source: Path) -> dict[str, Any]:
    readme = read_text(source / "README.md")
    config = read_text(source / "open3dsg" / "config" / "config.py")
    trainer = read_text(source / "open3dsg" / "scripts" / "trainer.py")
    sgpn = read_text(source / "open3dsg" / "models" / "sgpn.py")
    preprocess = read_text(source / "open3dsg" / "data" / "preprocess_3rscan.py")
    frames = read_text(source / "open3dsg" / "data" / "get_object_frame.py")
    downloader = read_text(REPO_ROOT / "local_dataset" / "3RScan" / "files" / "download_3rscan.py")
    return {
        "readme_mentions_3dssg_subset": "3DSSG_subset.zip" in readme,
        "readme_mentions_additional_meta_drive": "Additional meta files" in readme,
        "readme_mentions_openseg_checkpoint": "OpenSeg Checkpoint" in readme,
        "readme_mentions_blip2_positional_embedding": "BLIP2 Positional Embedding" in readme,
        "config_requires_existing_paths": "assert os.path.exists(path)" in config,
        "trainer_loads_relationships_test": "3DSSG_subset/relationships_test.json" in trainer,
        "trainer_loads_scannet_subgraphs_unconditionally": (
            'SCANNET_TRAIN = load_scan(CONF.PATH.SCANNET, "subgraphs/relationships_train.json")'
            in trainer
        ),
        "trainer_uses_jina_relation_mapper": "jinaai/jina-embeddings-v2-base-en" in trainer,
        "sgpn_loads_blip2_positional_embedding_at_import": "blip2_positional_embedding.pt" in sgpn,
        "sgpn_loads_openseg_saved_model": "tf2.saved_model.load" in sgpn and "openseg" in sgpn,
        "preprocess_reads_refined_obj": "mesh.refined.v2.obj" in preprocess,
        "preprocess_reads_texture_png": "mesh.refined_0.png" in preprocess,
        "preprocess_reads_object2image_pickle": "object2image.pkl" in preprocess,
        "preprocess_ignores_refined_boxes_in_current_branch": "test = True" in preprocess,
        "get_object_frame_reads_sequence": "sequence" in frames and "frame-%s." in frames,
        "download_script_supports_refined_obj": "mesh.refined.v2.obj" in downloader,
        "download_script_supports_refined_mtl": "mesh.refined.mtl" in downloader,
        "download_script_supports_texture_png": "mesh.refined_0.png" in downloader,
    }


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    local_dataset = args.local_dataset
    selected_scans = read_scans(args.selected_scans)
    raw_scan_root = local_dataset / "3RScan" / "scans"
    subset_root = local_dataset / "3DSSG_subset"
    staged_data_root = args.staged_root / "data"
    staged_r3scan_raw = staged_data_root / "3RScan"
    staged_subset_root = staged_r3scan_raw / "3DSSG_subset"
    staged_output_root = args.staged_root / "output"
    staged_preprocessed_root = staged_output_root / "datasets" / "OpenSG_3RScan" / "preprocessed"
    staged_preprocessed_expected = expected_preprocessed_pickles(staged_subset_root)

    scan_files = {
        name: count_scans_with(raw_scan_root, selected_scans, name)
        for name in SCAN_REQUIRED_RAW + SCAN_REQUIRED_OPEN3DSG
    }
    mesh_texture_ready = bool(selected_scans) and all(
        scan_files[name] == len(selected_scans) for name in SCAN_REQUIRED_OPEN3DSG
    )
    sequence = {pattern: count_sequence(raw_scan_root, selected_scans, pattern) for pattern in SEQUENCE_PATTERNS}
    sequence["_info.txt"] = {
        "scans": count_scans_with(raw_scan_root, selected_scans, "sequence/_info.txt"),
        "files": count_scans_with(raw_scan_root, selected_scans, "sequence/_info.txt"),
    }

    subset_relationships = read_labels(subset_root / "relationships.txt")
    full_relationships = read_labels(local_dataset / "3DSSG" / "relationships.txt")

    local_files = {
        "subset_classes": (subset_root / "classes.txt").exists(),
        "subset_relationships": (subset_root / "relationships.txt").exists(),
        "subset_relationships_train": (subset_root / "relationships_train.json").exists(),
        "subset_relationships_validation": (subset_root / "relationships_validation.json").exists(),
        "subset_relationships_test": (subset_root / "relationships_test.json").exists(),
        "staged_subset_relationships_train": (staged_subset_root / "relationships_train.json").exists(),
        "staged_subset_relationships_validation": (staged_subset_root / "relationships_validation.json").exists(),
        "staged_subset_relationships_test": (staged_subset_root / "relationships_test.json").exists(),
        "relationships_custom": exists_any(local_dataset, "relationships_custom.txt"),
        "staged_relationships_custom": (staged_r3scan_raw / "relationships_custom.txt").exists(),
        "staged_obj_boxes_train_refined": (staged_r3scan_raw / "obj_boxes_train_refined.json").exists(),
        "staged_obj_boxes_val_refined": (staged_r3scan_raw / "obj_boxes_val_refined.json").exists(),
        "staged_scannet_train_subgraph": (
            staged_output_root / "datasets" / "OpenSG_ScanNet" / "subgraphs" / "relationships_train.json"
        ).exists(),
        "staged_scannet_validation_subgraph": (
            staged_output_root / "datasets" / "OpenSG_ScanNet" / "subgraphs" / "relationships_validation.json"
        ).exists(),
        "top_level_full_relationships": (local_dataset / "3DSSG" / "relationships.txt").exists(),
        "download_3rscan_py": (local_dataset / "3RScan" / "files" / "download_3rscan.py").exists(),
        "open3dsg_checkpoint": exists_any(local_dataset, "*.ckpt"),
        "blip2_positional_embedding": exists_any(local_dataset, "blip2_positional_embedding.pt"),
        "openseg_saved_model_dir": exists_any(local_dataset, "saved_model.pb")
        and any("openseg" in str(path).lower() for path in local_dataset.rglob("saved_model.pb")),
        "pointnet_weights": exists_any(local_dataset, "pointnet.pth"),
        "pointnet2_weights": exists_any(local_dataset, "pointnet2_ulip.pt"),
        "preprocessed_pickles": count_preprocessed_pickles(staged_preprocessed_root),
        "preprocessed_pickles_expected": staged_preprocessed_expected,
        "view_pickles": sum(1 for _ in local_dataset.rglob("*_object2image.pkl")) if local_dataset.exists() else 0,
    }
    checkpoint_root = staged_output_root / "checkpoints"
    model_paths = {
        "checkpoint_root": relpath(checkpoint_root),
        "open3dsg_checkpoint_candidates": [
            relpath(path) for path in sorted(local_dataset.rglob("*.ckpt"))
        ],
        "blip2_positional_embedding": relpath(
            checkpoint_root / "blip2_positional_embedding.pt"
        ),
        "openseg_saved_model": relpath(checkpoint_root / "openseg" / "saved_model.pb"),
        "openseg_variables_data": relpath(
            checkpoint_root / "openseg" / "variables" / "variables.data-00000-of-00001"
        ),
        "openseg_variables_index": relpath(
            checkpoint_root / "openseg" / "variables" / "variables.index"
        ),
        "pointnet_weights": relpath(checkpoint_root / "pointnet.pth"),
        "pointnet2_weights": relpath(checkpoint_root / "pointnet2_ulip.pt"),
    }

    labels_note = {
        "subset_relationship_count": len(subset_relationships),
        "full_relationship_count": len(full_relationships),
        "use_subset_relationships_for_open3dsg_top_level": len(subset_relationships) == 27,
        "reason": (
            "Open3DSG test code asserts 27 mapped predicates; the local full 3DSSG "
            "relationships file has more labels, so the staged top-level relationships.txt "
            "should come from 3DSSG_subset for H001 smoke."
        ),
    }

    locally_generatable = [
        {
            "item": "open3dsg_staged_root",
            "path": relpath(args.staged_root),
            "action": "create ignored staged root; do not mutate local_dataset/3DSSG_subset or official source clone",
        },
        {
            "item": "top_level_classes_and_relationships",
            "action": "copy 3DSSG_subset/classes.txt and 3DSSG_subset/relationships.txt to staged 3RScan root",
        },
        {
            "item": "relationships_test.json",
            "action": "derive a staged H001 validation/test JSON from fixed hardened scans; trainer loads it unconditionally",
        },
        {
            "item": "relationships_custom.txt",
            "action": "prefer official Open3DSG additional metadata; otherwise stage an H001 smoke vocabulary and mark as non-final",
        },
        {
            "item": "obj_boxes_train_refined.json and obj_boxes_val_refined.json",
            "action": "for H001 smoke only, empty JSON stubs unblock file open because current preprocess branch recomputes axis_aligned boxes",
        },
        {
            "item": "empty_scannet_subgraph_placeholders",
            "action": "stage empty ScanNet train/validation subgraph JSONs because trainer loads them before dataset filtering",
        },
        {
            "item": "view_pickles",
            "action": "run get_object_frame.py after scan mesh/texture files exist",
        },
        {
            "item": "preprocessed_pickles",
            "action": "run preprocess_3rscan.py after view pickles and metadata exist",
        },
    ]

    external_or_user_artifacts = [
        {
            "item": "mesh.refined.v2.obj / mesh.refined.mtl / mesh.refined_0.png",
            "source": "3RScan public downloader",
            "status": "ready" if mesh_texture_ready else "missing_for_selected_scans",
            "needed_count": len(selected_scans),
            "ready_file_counts": {name: scan_files[name] for name in SCAN_REQUIRED_OPEN3DSG},
        },
        {
            "item": "Open3DSG checkpoint",
            "source": "trained Open3DSG run or trusted checkpoint artifact",
            "status": "ready" if local_files["open3dsg_checkpoint"] else "missing",
            "note": (
                "the official README describes evaluating a trained model but does not place a "
                "checkpoint in the repo"
            ),
        },
        {
            "item": "BLIP2 positional embedding",
            "source": "Open3DSG README Google Drive link",
            "status": "ready" if local_files["blip2_positional_embedding"] else "missing",
        },
        {
            "item": "OpenSeg checkpoint",
            "source": "Open3DSG README OpenSeg link",
            "status": "ready" if local_files["openseg_saved_model_dir"] else "missing",
            "note": "needed for the official OpenSeg test command; alternative CLIP settings would weaken faithfulness",
        },
        {
            "item": "PointNet/PointNet2 weights",
            "source": "Open3DSG README pointnet_weights Google Drive folder",
            "status": "ready"
            if local_files["pointnet_weights"] and local_files["pointnet2_weights"]
            else "missing",
            "note": "training-route dependency; this folder does not contain a trained Open3DSG checkpoint",
        },
        {
            "item": "Hugging Face model cache",
            "source": "jinaai/jina-embeddings-v2-base-en and Salesforce/instructblip-vicuna-7b",
            "status": "not_checked",
            "note": "network/cache dependency for test-time relation mapping and BLIP generation",
        },
    ]

    recommended_order = [
        "apply or stage config-path patch plus h001 dump patch in a local Open3DSG working clone",
        "create local_dataset/Open3DSG_staged/h001_runtime with data/ and output/ subroots",
        "stage H001-specific 3DSSG_subset JSONs and top-level 27-label classes/relationships files",
        "stage relationships_custom.txt and smoke-only obj_boxes JSONs, recording whether official metadata was used",
        "download mesh.refined.v2.obj, mesh.refined.mtl, and mesh.refined_0.png for selected H001 scans",
        "run get_object_frame.py --mode validation --dataset R3SCAN to create views",
        "run preprocess_3rscan.py to create OpenSG_3RScan/preprocessed data_dict pickles",
        "place or train the Open3DSG checkpoint and verify required model caches; BLIP2/OpenSeg are separately audited",
        "run patched Open3DSG with --test --dataset 3rscan --gt_objects --blip --h001_dump_jsonl",
        "only after raw dump exists, run the open3dsg_ov prediction JSONL adapter, geometry join, and metrics",
    ]

    command_templates = {
        "download_refined_mesh_triplet": [
            "while read scan_id; do",
            "  python3 local_dataset/3RScan/files/download_3rscan.py -o local_dataset/3RScan/scans --id \"$scan_id\" --type mesh.refined.v2.obj",
            "  python3 local_dataset/3RScan/files/download_3rscan.py -o local_dataset/3RScan/scans --id \"$scan_id\" --type mesh.refined.mtl",
            "  python3 local_dataset/3RScan/files/download_3rscan.py -o local_dataset/3RScan/scans --id \"$scan_id\" --type mesh.refined_0.png",
            f"done < {relpath(args.selected_scans)}",
        ],
        "view_pickle_generation": [
            "python3 open3dsg/data/get_object_frame.py --mode validation --dataset R3SCAN",
        ],
        "preprocess_generation": [
            "python3 open3dsg/data/preprocess_3rscan.py",
        ],
        "model_artifact_downloads": [
            "python -m gdown 'https://drive.google.com/uc?id=1BfvxB6eo3XksE6AfMUgoBHwzVYce1ed1' -O <checkpoints>/blip2_positional_embedding.pt",
            "python -m gdown 'https://drive.google.com/uc?id=18RIPkqlt7KXiG8BzxNIweMxYvjlMZifO' -O <checkpoints>/pointnet.pth",
            "python -m gdown 'https://drive.google.com/uc?id=14oH-eZjyB4rlh2-_25pNpGBhbegKi16I' -O <checkpoints>/pointnet2_ulip.pt",
            "curl -fL -o <checkpoints>/openseg/graph_def.txt https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/graph_def.txt",
            "curl -fL -o <checkpoints>/openseg/saved_model.pb https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/saved_model.pb",
            "curl -fL -o <checkpoints>/openseg/variables/variables.index https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/variables/variables.index",
            "curl -fL -o <checkpoints>/openseg/variables/variables.data-00000-of-00001 https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/variables/variables.data-00000-of-00001",
        ],
        "first_raw_dump_smoke": [
            "python3 open3dsg/scripts/run.py --test --dataset 3rscan --checkpoint <open3dsg.ckpt> --n_beams 5 --weight_2d 0.5 --clip_model OpenSeg --node_model ViT-L/14@336px --blip --gt_objects --h001_dump_jsonl <raw.jsonl>",
        ],
    }

    blockers: list[str] = []
    warnings: list[str] = []
    if not args.open3dsg_source.exists():
        blockers.append("missing_open3dsg_source")
    if not selected_scans:
        blockers.append("missing_selected_h001_scans")
    for name in SCAN_REQUIRED_OPEN3DSG:
        if scan_files[name] < len(selected_scans):
            blockers.append(f"missing_scan_file:{name}:{scan_files[name]}/{len(selected_scans)}")
    if not local_files["subset_relationships_test"] and not local_files["staged_subset_relationships_test"]:
        blockers.append("missing_metadata:relationships_test_json")
    if not local_files["relationships_custom"] and not local_files["staged_relationships_custom"]:
        blockers.append("missing_metadata:relationships_custom_txt")
    if not local_files["open3dsg_checkpoint"]:
        blockers.append("missing_model:open3dsg_checkpoint")
    if not local_files["blip2_positional_embedding"]:
        blockers.append("missing_model:blip2_positional_embedding")
    if not local_files["openseg_saved_model_dir"]:
        blockers.append("missing_model:openseg_saved_model")
    if local_files["view_pickles"] == 0:
        blockers.append("missing_runtime:view_pickles")
    if staged_preprocessed_expected and local_files["preprocessed_pickles"] == 0:
        blockers.append(
            f"missing_runtime:open3dsg_preprocessed_pickles:{local_files['preprocessed_pickles']}/{staged_preprocessed_expected}"
        )
    elif staged_preprocessed_expected and local_files["preprocessed_pickles"] < staged_preprocessed_expected:
        warnings.append(
            f"partial_runtime:open3dsg_preprocessed_pickles:{local_files['preprocessed_pickles']}/{staged_preprocessed_expected}"
        )

    status = "runtime_acquisition_plan_ready_blocked_artifacts_missing"
    if not blockers:
        status = "runtime_artifacts_ready_for_raw_dump_smoke"
        if any(warning.startswith("partial_runtime:open3dsg_preprocessed_pickles") for warning in warnings):
            status = "runtime_artifacts_ready_for_raw_dump_smoke_partial_preprocess"

    if "missing_open3dsg_source" in blockers:
        next_action = "Acquire or point to an Open3DSG source checkout."
    elif any(blocker.startswith("missing_metadata:") for blocker in blockers):
        next_action = "Stage Open3DSG metadata/runtime root."
    elif any(blocker.startswith("missing_scan_file:") for blocker in blockers):
        next_action = "Acquire missing Open3DSG mesh/texture files for selected scans."
    elif "missing_runtime:view_pickles" in blockers:
        next_action = "Run Open3DSG view pickle generation for the selected H001 scans."
    elif any(blocker.startswith("missing_runtime:open3dsg_preprocessed_pickles") for blocker in blockers):
        next_action = "Run Open3DSG preprocess generation after view pickles exist."
    elif blockers == ["missing_model:open3dsg_checkpoint"]:
        next_action = "Run Open3DSG training route feasibility/preflight unless a trusted checkpoint is supplied."
    elif any(blocker.startswith("missing_model:") for blocker in blockers):
        next_action = "Acquire the missing Open3DSG model artifacts listed in blockers."
    else:
        next_action = "Run patched Open3DSG raw dump smoke, then JSONL adapter and metrics."

    return {
        "schema_version": "h001_open3dsg_runtime_plan_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "open3dsg_source": relpath(args.open3dsg_source),
        "open3dsg_source_commit": git_head(args.open3dsg_source),
        "selected_scans_file": relpath(args.selected_scans),
        "selected_scan_count": len(selected_scans),
        "proposed_staged_root": relpath(args.staged_root),
        "proposed_staged_paths": {
            "data_root": relpath(staged_data_root),
            "r3scan_raw": relpath(staged_r3scan_raw),
            "output_root": relpath(staged_output_root),
            "opensg_3rscan": relpath(staged_output_root / "datasets" / "OpenSG_3RScan"),
            "opensg_scannet_placeholder": relpath(staged_output_root / "datasets" / "OpenSG_ScanNet"),
            "checkpoints": relpath(staged_output_root / "checkpoints"),
            "features": relpath(staged_output_root / "features"),
        },
        "source_facts": source_facts(args.open3dsg_source),
        "local_files": local_files,
        "subset_counts": subset_counts(subset_root),
        "relationship_label_policy": labels_note,
        "selected_scan_file_counts": scan_files,
        "mesh_texture_ready": mesh_texture_ready,
        "model_paths": model_paths,
        "selected_sequence_counts": sequence,
        "locally_generatable": locally_generatable,
        "external_or_user_artifacts": external_or_user_artifacts,
        "recommended_order": recommended_order,
        "command_templates": command_templates,
        "blockers": blockers,
        "warnings": warnings,
        "claim_limit": "No Open3DSG metric or improvement claim until raw dump, JSONL export, geometry join, and metric run exist.",
        "next_action": next_action,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Open3DSG Runtime Acquisition Plan",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Open3DSG commit: `{manifest.get('open3dsg_source_commit')}`",
        f"Selected scans: `{manifest['selected_scan_count']}`",
        "",
        "## Local Readiness",
        "",
        "| Item | Ready |",
        "| --- | --- |",
    ]
    for name, value in manifest["local_files"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Selected Scan Files", "", "| File | Scans ready |", "| --- | --- |"])
    total = manifest["selected_scan_count"]
    for name, count in manifest["selected_scan_file_counts"].items():
        lines.append(f"| `{name}` | `{count}/{total}` |")

    lines.extend(["", "## Sequence Files", "", "| Pattern | Scans ready | Files |", "| --- | --- | --- |"])
    for pattern, counts in manifest["selected_sequence_counts"].items():
        lines.append(f"| `{pattern}` | `{counts['scans']}/{total}` | `{counts['files']}` |")

    lines.extend(["", "## Acquisition Split", "", "Locally generatable:"])
    for item in manifest["locally_generatable"]:
        lines.append(f"- `{item['item']}`: {item['action']}")

    lines.extend(["", "External or user-provided artifacts:"])
    for item in manifest["external_or_user_artifacts"]:
        note = f" {item['note']}" if item.get("note") else ""
        lines.append(f"- `{item['item']}` from {item['source']}: `{item['status']}`.{note}")

    lines.extend(["", "## Recommended Order", ""])
    for idx, item in enumerate(manifest["recommended_order"], start=1):
        lines.append(f"{idx}. {item}")

    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if manifest.get("warnings"):
        lines.extend(f"- `{warning}`" for warning in manifest["warnings"])
    else:
        lines.append("- none")

    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_commands(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Open3DSG Runtime Command Templates",
        "",
        "These commands are not executed by this planning step.",
        "",
    ]
    for name, command_lines in manifest["command_templates"].items():
        lines.extend([f"## {name}", "", "```bash"])
        lines.extend(command_lines)
        lines.extend(["```", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def checklist(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers = set(manifest["blockers"])
    warnings = set(manifest.get("warnings", []))
    metadata_ready = not any(blocker.startswith("missing_metadata:") for blocker in blockers)
    mesh_ready = bool(manifest.get("mesh_texture_ready"))
    views_ready = "missing_runtime:view_pickles" not in blockers
    preprocessed_ready = not any(blocker.startswith("missing_runtime:open3dsg_preprocessed_pickles") for blocker in blockers)
    model_blockers = sorted(blocker for blocker in blockers if blocker.startswith("missing_model:"))
    model_ready = not model_blockers
    if model_ready:
        model_status = "ready"
    elif model_blockers == ["missing_model:open3dsg_checkpoint"]:
        model_status = "partial_ready_checkpoint_missing"
    else:
        model_status = "blocked_missing_external"
    view_status = "ready" if views_ready else ("now" if mesh_ready else "blocked_until_mesh_texture")
    preprocess_partial = any(warning.startswith("partial_runtime:open3dsg_preprocessed_pickles") for warning in warnings)
    if preprocessed_ready and preprocess_partial:
        preprocess_status = "partial_ready"
    else:
        preprocess_status = "ready" if preprocessed_ready else ("now" if views_ready else "blocked_until_views")
    if preprocessed_ready and model_ready:
        raw_dump_status = "ready_to_run_partial_preprocess" if preprocess_partial else "ready_to_run"
    elif preprocessed_ready:
        raw_dump_status = "blocked_until_model"
    elif model_ready:
        raw_dump_status = "blocked_until_preprocessed"
    else:
        raw_dump_status = "blocked_until_preprocessed_and_model"

    return {
        "schema_version": "h001_open3dsg_runtime_checklist_v1",
        "date_checked": manifest["date_checked"],
        "items": [
            {"id": "stage_root", "status": "ready", "depends_on": []},
            {
                "id": "metadata_stage",
                "status": "ready" if metadata_ready else "blocked_missing_metadata",
                "depends_on": ["stage_root"],
            },
            {
                "id": "mesh_texture_download",
                "status": "ready" if mesh_ready else "blocked_missing_external",
                "depends_on": ["stage_root"],
            },
            {
                "id": "view_pickle_generation",
                "status": view_status,
                "depends_on": ["mesh_texture_download"],
            },
            {
                "id": "preprocessed_pickles",
                "status": preprocess_status,
                "depends_on": ["view_pickle_generation"],
            },
            {
                "id": "model_artifacts",
                "status": model_status,
                "depends_on": ["stage_root"],
            },
            {
                "id": "raw_dump_smoke",
                "status": raw_dump_status,
                "depends_on": ["preprocessed_pickles", "model_artifacts"],
            },
            {
                "id": "h001_jsonl_adapter",
                "status": "blocked_until_raw_dump",
                "depends_on": ["raw_dump_smoke"],
            },
        ],
    }


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "manifest.json", manifest)
        write_report(args.output_dir / "report.md", manifest)
        write_commands(args.output_dir / "commands.md", manifest)
        write_json(args.output_dir / "checklist.json", checklist(manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
