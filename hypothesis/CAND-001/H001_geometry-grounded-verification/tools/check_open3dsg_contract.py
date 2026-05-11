#!/usr/bin/env python3
"""Check Open3DSG source-contract coverage for H001 relation families."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_SOURCE = Path("/tmp/open3dsg_source")
DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "source_contract"

TARGET_FAMILIES = {
    "support_contact": ["standing on", "lying on", "supported by"],
    "proximity": ["close by"],
    "relative_vertical": ["higher than", "lower than"],
}

MANUAL_MAPPING_PATTERNS = {
    "next_to_to_close_by": "known_mapping['next to'] = 'close by'",
    "above_to_higher_than": "known_mapping['above'] = 'higher than'",
    "under_to_lower_than": "known_mapping['under'] = 'lower than'",
    "placed_on_top_to_standing_on": "known_mapping['placed on top'] = 'standing on'",
}

SOURCE_PATTERNS = {
    "free_form_blip_relationship_text": "Describe the relationship between",
    "predicate_text_output": "predicates_blip",
    "mapped_predicate_output": "predicates_mapped",
    "mapped_score_output": "predicates_mapped_probs",
    "object_id_output": '"objects_id"',
    "edge_index_output": '"edges"',
    "predicate_min_distance_output": '"predicate_min_dist"',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_relationship_labels(local_dataset: Path) -> list[str]:
    path = local_dataset / "3DSSG_subset" / "relationships.txt"
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def exists_any(root: Path, pattern: str) -> bool:
    return root.exists() and any(root.rglob(pattern))


def main() -> int:
    args = parse_args()
    source = args.open3dsg_source
    local_dataset = args.local_dataset

    trainer_path = source / "open3dsg" / "scripts" / "trainer.py"
    sgpn_path = source / "open3dsg" / "models" / "sgpn.py"
    preprocess_path = source / "open3dsg" / "data" / "preprocess_3rscan.py"
    readme_path = source / "README.md"

    trainer_text = read_text(trainer_path)
    sgpn_text = read_text(sgpn_path)
    preprocess_text = read_text(preprocess_path)
    combined_text = "\n".join([trainer_text, sgpn_text, preprocess_text, read_text(readme_path)])

    relationship_labels = read_relationship_labels(local_dataset)
    relationship_label_set = set(relationship_labels)

    family_coverage: dict[str, Any] = {}
    for family, labels in TARGET_FAMILIES.items():
        present = {label: label in relationship_label_set for label in labels}
        family_coverage[family] = {
            "target_labels": labels,
            "target_labels_present": present,
            "all_target_labels_present": all(present.values()),
        }

    manual_mapping = {
        name: pattern in combined_text
        for name, pattern in MANUAL_MAPPING_PATTERNS.items()
    }
    source_features = {
        name: pattern in combined_text
        for name, pattern in SOURCE_PATTERNS.items()
    }
    required_files = {
        "README.md": readme_path.exists(),
        "open3dsg/scripts/trainer.py": trainer_path.exists(),
        "open3dsg/models/sgpn.py": sgpn_path.exists(),
        "open3dsg/data/preprocess_3rscan.py": preprocess_path.exists(),
    }

    local_runtime = {
        "relationships_custom_txt": (local_dataset / "3RScan" / "relationships_custom.txt").exists(),
        "obj_boxes_train_refined_json": (local_dataset / "3RScan" / "obj_boxes_train_refined.json").exists(),
        "obj_boxes_val_refined_json": (local_dataset / "3RScan" / "obj_boxes_val_refined.json").exists(),
        "relationships_test_json": (local_dataset / "3DSSG_subset" / "relationships_test.json").exists(),
        "open3dsg_preprocessed_pickles": exists_any(local_dataset, "data_dict_*.pkl"),
        "open3dsg_checkpoint": exists_any(local_dataset, "*.ckpt"),
        "blip2_positional_embedding": exists_any(local_dataset, "blip2_positional_embedding.pt"),
        "precomputed_features": exists_any(local_dataset, "*.pt"),
    }

    coverage_ready = (
        all(item["all_target_labels_present"] for item in family_coverage.values())
        and manual_mapping["next_to_to_close_by"]
        and manual_mapping["above_to_higher_than"]
        and manual_mapping["under_to_lower_than"]
        and source_features["free_form_blip_relationship_text"]
        and source_features["mapped_predicate_output"]
        and source_features["mapped_score_output"]
        and source_features["object_id_output"]
        and source_features["edge_index_output"]
    )

    blockers: list[str] = []
    if not source.exists():
        blockers.append("missing_open3dsg_source")
    for name, exists in required_files.items():
        if not exists:
            blockers.append(f"missing_source_file:{name}")
    if not coverage_ready:
        blockers.append("source_contract_coverage_not_ready")
    for name, exists in local_runtime.items():
        if name == "precomputed_features":
            continue
        if not exists:
            blockers.append(f"missing_runtime:{name}")

    warnings: list[str] = []
    if not local_runtime["precomputed_features"]:
        warnings.append("missing_precomputed_features_optional_but_large_runtime_cost")

    if not coverage_ready:
        status = "blocked_source_contract"
    elif any(blocker.startswith("missing_runtime:") for blocker in blockers):
        status = "source_contract_ready_runtime_blocked"
    else:
        status = "ready_for_adapter_or_smoke_run"

    manifest = {
        "schema_version": "h001_open3dsg_source_contract_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "open3dsg_source": relpath(source),
        "open3dsg_source_commit": git_head(source),
        "required_files": required_files,
        "source_features": source_features,
        "manual_mapping": manual_mapping,
        "family_coverage": family_coverage,
        "local_runtime": local_runtime,
        "blockers": blockers,
        "warnings": warnings,
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_report(args.output_dir / "report.md", manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Open3DSG Source Contract",
        "",
        f"Date: {manifest['date_checked']}",
        f"Status: `{manifest['status']}`",
        f"Source commit: `{manifest.get('open3dsg_source_commit')}`",
        "",
        "## Family Coverage",
        "",
        "| Family | Target labels | Present |",
        "| --- | --- | --- |",
    ]
    for family, payload in manifest["family_coverage"].items():
        labels = ", ".join(f"`{label}`" for label in payload["target_labels"])
        present = "yes" if payload["all_target_labels_present"] else "no"
        lines.append(f"| `{family}` | {labels} | {present} |")

    lines.extend(["", "## Source Features", ""])
    for name, exists in manifest["source_features"].items():
        lines.append(f"- `{name}`: `{exists}`")

    lines.extend(["", "## Manual Mappings", ""])
    for name, exists in manifest["manual_mapping"].items():
        lines.append(f"- `{name}`: `{exists}`")

    lines.extend(["", "## Runtime Readiness", ""])
    for name, exists in manifest["local_runtime"].items():
        lines.append(f"- `{name}`: `{exists}`")

    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if manifest["warnings"]:
        lines.extend(f"- `{warning}`" for warning in manifest["warnings"])
    else:
        lines.append("- none")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
