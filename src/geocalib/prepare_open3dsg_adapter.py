#!/usr/bin/env python3
"""Prepare the Open3DSG output-dump patch and H001 adapter contract."""

from __future__ import annotations

import argparse
import difflib
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
DEFAULT_SOURCE_CONTRACT = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "open3dsg_ov"
    / "source_contract"
    / "manifest.json"
)
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "adapter"

RAW_SCHEMA_VERSION = "h001_open3dsg_eval_dump_v1"
PREDICTION_SCHEMA_VERSION = "h001_prediction_v1"
BASELINE_NAME = "open3dsg_ov"
ADAPTER_VERSION = "v0"
DEFAULT_SPLIT_NAME = "hardened_open3dsg"

TARGET_PREDICATES = {
    "standing on": "support_contact",
    "lying on": "support_contact",
    "supported by": "support_contact",
    "close by": "proximity",
    "higher than": "relative_vertical",
    "lower than": "relative_vertical",
}

SOURCE_MARKERS = {
    "run_py_vis_arg": "parser.add_argument('--vis_graphs'",
    "trainer_eval_dict_scores": "eval_dict['predicates_mapped_probs'] = predicates_mapped_probs",
    "trainer_eval_dict_mapped": "eval_dict['predicates_mapped'] = predicates_mapped",
    "trainer_eval_dict_text": "eval_dict['predicates_blip'] = predicates",
    "trainer_eval_dict_objects": 'eval_dict["objects_id"] = data_dict["objects_id"].cpu()',
    "trainer_eval_dict_edges": 'eval_dict["edges"] = data_dict["edges"].cpu()',
    "trainer_append_point": "self.test_step_outputs.append(eval_dict)",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--source-contract", type=Path, default=DEFAULT_SOURCE_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def source_checks(source: Path) -> dict[str, bool]:
    run_text = read_text(source / "open3dsg" / "scripts" / "run.py")
    trainer_text = read_text(source / "open3dsg" / "scripts" / "trainer.py")
    combined = run_text + "\n" + trainer_text
    return {name: marker in combined for name, marker in SOURCE_MARKERS.items()}


def raw_schema() -> dict[str, Any]:
    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "record_type": "open3dsg_eval_dict",
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": "open3dsg_eval_<run-id>",
        "source_scan_id": "3RScan scan id with Open3DSG split suffix, e.g. <scan_uuid>-1",
        "scan_id": "3RScan scan uuid without split suffix",
        "subset_split_id": "3DSSG_subset split id parsed from the suffix when absent",
        "object_ids": ["3DSSG object ids in Open3DSG node order"],
        "object_labels": ["optional predicted or GT object labels in node order"],
        "edges": [["subject_node_index", "object_node_index"]],
        "predicates_blip": ["free-form generated predicate text per edge"],
        "relationships_text": ["full generated relation sentence per edge"],
        "predicates_mapped": [["3DSSG predicate labels sorted by mapped score per edge"]],
        "predicates_mapped_probs": [
            ["mapped predicate scores in 3DSSG relationships.txt order per edge"]
        ],
        "predicate_vocab": "3DSSG_subset_relationships_txt_including_none",
        "predicate_min_dist": [["optional pair min-distance vector from Open3DSG"]],
    }


def adapter_mapping() -> dict[str, Any]:
    return {
        "baseline_name": BASELINE_NAME,
        "adapter_name": "open3dsg_to_h001_predictions",
        "adapter_version": ADAPTER_VERSION,
        "output_schema_version": PREDICTION_SCHEMA_VERSION,
        "default_split_name": DEFAULT_SPLIT_NAME,
        "target_predicates": TARGET_PREDICATES,
        "row_rules": [
            "parse Open3DSG source_scan_id into scan_id and subset_split_id if needed",
            "map edge node indices to 3DSSG object ids through object_ids",
            "emit H001 prediction rows only for target_predicates",
            "use predicates_mapped_probs in 3DSSG relationships.txt order as ranking_score",
            "preserve predicates_blip and relationships_text under adapter.source_text",
            "do not normalize Open3DSG text-embedding scores into p_geom_valid",
            "run existing H001 geometry join after prediction export",
        ],
        "first_smoke_policy": {
            "task_mode": "predcls_relation",
            "object_policy": "prefer Open3DSG --gt_objects to isolate relation transfer",
            "claim_limit": "source-transfer feasibility only until metric run exists",
        },
    }


def insert_after_marker(lines: list[str], marker: str, insert: list[str]) -> list[str]:
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and marker in line:
            out.extend(insert)
            inserted = True
    return out


def insert_before_marker(lines: list[str], marker: str, insert: list[str]) -> list[str]:
    out: list[str] = []
    inserted = False
    for line in lines:
        if not inserted and marker in line:
            out.extend(insert)
            inserted = True
        out.append(line)
    return out


def dump_patch(source: Path) -> str:
    run_rel = Path("open3dsg/scripts/run.py")
    trainer_rel = Path("open3dsg/scripts/trainer.py")
    run_lines = (source / run_rel).read_text(encoding="utf-8").splitlines(keepends=True)
    trainer_lines = (source / trainer_rel).read_text(encoding="utf-8").splitlines(keepends=True)

    run_insert = [
        "    parser.add_argument('--h001_dump_jsonl', type=str, default=None,\n",
        "                        help=\"Append identity-preserving Open3DSG eval rows for H001 JSONL adaptation\")\n",
    ]
    run_new = insert_after_marker(
        run_lines,
        "parser.add_argument('--vis_graphs'",
        run_insert,
    )

    helper_insert = [
        "\n",
        "    def _h001_jsonable(self, value):\n",
        "        if torch.is_tensor(value):\n",
        "            return value.detach().cpu().tolist()\n",
        "        if isinstance(value, np.ndarray):\n",
        "            return value.tolist()\n",
        "        if isinstance(value, (np.integer,)):\n",
        "            return int(value)\n",
        "        if isinstance(value, (np.floating,)):\n",
        "            return float(value)\n",
        "        if isinstance(value, (list, tuple)):\n",
        "            return [self._h001_jsonable(v) for v in value]\n",
        "        if isinstance(value, dict):\n",
        "            return {str(k): self._h001_jsonable(v) for k, v in value.items()}\n",
        "        return value\n",
        "\n",
        "    def _h001_append_eval_dump(self, eval_dict):\n",
        "        dump_path = self.hparams.get('h001_dump_jsonl')\n",
        "        if not dump_path:\n",
        "            return\n",
        "        source_scan_id = self._h001_jsonable(eval_dict.get('scan_id'))\n",
        "        if isinstance(source_scan_id, list) and source_scan_id:\n",
        "            source_scan_id = source_scan_id[0]\n",
        "        record = {\n",
        "            \"schema_version\": \"h001_open3dsg_eval_dump_v1\",\n",
        "            \"record_type\": \"open3dsg_eval_dict\",\n",
        "            \"baseline_name\": \"open3dsg_ov\",\n",
        "            \"baseline_run_id\": self.hparams.get('run_name') or \"open3dsg_eval\",\n",
        "            \"source_scan_id\": source_scan_id,\n",
        "            \"object_ids\": self._h001_jsonable(eval_dict.get('objects_id')),\n",
        "            \"objects_count\": self._h001_jsonable(eval_dict.get('objects_count')),\n",
        "            \"edges\": self._h001_jsonable(eval_dict.get('edges')),\n",
        "            \"predicate_count\": self._h001_jsonable(eval_dict.get('predicate_count')),\n",
        "            \"predicates_blip\": self._h001_jsonable(eval_dict.get('predicates_blip')),\n",
        "            \"predicates_mapped\": self._h001_jsonable(eval_dict.get('predicates_mapped')),\n",
        "            \"predicates_mapped_probs\": self._h001_jsonable(eval_dict.get('predicates_mapped_probs')),\n",
        "            \"predicate_min_dist\": self._h001_jsonable(eval_dict.get('predicate_min_dist')),\n",
        "            \"relationships_text\": self._h001_jsonable(eval_dict.get('relationships', ([], [], [], []))[0]),\n",
        "        }\n",
        "        dump_dir = os.path.dirname(dump_path)\n",
        "        if dump_dir:\n",
        "            os.makedirs(dump_dir, exist_ok=True)\n",
        "        with open(dump_path, 'a') as f:\n",
        "            f.write(json.dumps(record) + \"\\n\")\n",
        "\n",
    ]
    trainer_with_helper = insert_before_marker(
        trainer_lines,
        "    def train_dataloader(self) -> DataLoader:",
        helper_insert,
    )
    trainer_new = insert_before_marker(
        trainer_with_helper,
        "        self.test_step_outputs.append(eval_dict)",
        [
            "        if self.hparams.get('h001_dump_jsonl') and eval_dict:\n",
            "            self._h001_append_eval_dump(eval_dict)\n",
        ],
    )

    chunks: list[str] = []
    chunks.append(f"diff --git a/{run_rel} b/{run_rel}\n")
    chunks.extend(
        difflib.unified_diff(
            run_lines,
            run_new,
            fromfile=f"a/{run_rel}",
            tofile=f"b/{run_rel}",
        )
    )
    chunks.append(f"diff --git a/{trainer_rel} b/{trainer_rel}\n")
    chunks.extend(
        difflib.unified_diff(
            trainer_lines,
            trainer_new,
            fromfile=f"a/{trainer_rel}",
            tofile=f"b/{trainer_rel}",
        )
    )
    return "".join(chunks)


def make_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Adapter Prep",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Open3DSG source commit: `{manifest.get('open3dsg_source_commit')}`",
        "",
        "## Outputs",
        "",
        "- `dump_patch.diff`: minimal Open3DSG patch for identity-preserving eval dump",
        "- `raw_schema.json`: expected raw JSONL row contract",
        "- `adapter_mapping.json`: H001 prediction-row mapping contract",
        "- `manifest.json`: this prep result",
        "",
        "## Source Patch Points",
        "",
    ]
    for name, passed in manifest["source_checks"].items():
        lines.append(f"- `{name}`: `{passed}`")
    lines.extend(["", "## Runtime Blockers", ""])
    if manifest["runtime_blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["runtime_blockers"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The output-dump and adapter boundary is feasible at source level.",
            "It is not executable evidence until an Open3DSG run writes raw JSONL and the H001 adapter exports predictions.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    checks = source_checks(args.open3dsg_source)
    missing_checks = [name for name, passed in checks.items() if not passed]
    source_contract = load_json(args.source_contract) if args.source_contract.exists() else {}
    runtime_blockers = [
        blocker
        for blocker in source_contract.get("blockers", [])
        if str(blocker).startswith("missing_runtime:")
    ]

    status = "adapter_feasibility_ready_runtime_blocked"
    if missing_checks:
        status = "blocked_source_patch_points"

    manifest = {
        "schema_version": "h001_open3dsg_adapter_prep_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "open3dsg_source": relpath(args.open3dsg_source),
        "open3dsg_source_commit": git_head(args.open3dsg_source),
        "source_contract": relpath(args.source_contract),
        "source_contract_status": source_contract.get("status"),
        "source_checks": checks,
        "missing_source_checks": missing_checks,
        "runtime_blockers": runtime_blockers,
        "outputs": {
            "dump_patch": "dump_patch.diff",
            "raw_schema": "raw_schema.json",
            "adapter_mapping": "adapter_mapping.json",
            "report": "report.md",
        },
        "next_action": "Open3DSG runtime artifact acquisition path",
        "claim_limit": "Do not claim Open3DSG improvement until raw dump, JSONL export, geometry join, and metric run exist.",
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "dump_patch.diff").write_text(dump_patch(args.open3dsg_source), encoding="utf-8")
        (args.output_dir / "raw_schema.json").write_text(
            json.dumps(raw_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "adapter_mapping.json").write_text(
            json.dumps(adapter_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "report.md").write_text(make_report(manifest), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if missing_checks else 0


if __name__ == "__main__":
    raise SystemExit(main())
