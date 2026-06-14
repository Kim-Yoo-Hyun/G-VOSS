#!/usr/bin/env python3
"""Optional VL-SAT validation hook for preserving H001 join metadata.

This module is intended to be copied or imported from a local VL-SAT checkout.
It does not run VL-SAT by itself. Call it inside the official validation loop
while subgraph id, edge indices, node ids, and relation scores are still
available.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np


RAW_SCHEMA_VERSION = "h001_vlsat_raw_dump_v1"


def _tolist(value: Any) -> Any:
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _subgraph_parts(subgraph_id: str) -> tuple[str, int]:
    scan_id, split_id = subgraph_id.rsplit("_", 1)
    return scan_id, int(split_id)


def _read_instance_ids_from_ply(dataset: Any, subgraph_id: str) -> set[int]:
    """Read instance ids using the same PLY label source as VL-SAT.

    The official dataset does not return node instance ids. It creates them by
    filtering official subgraph objects to instances present in the labeled PLY.
    This reproduces that logic for an export hook.
    """

    try:
        import trimesh
        from utils import util_ply
    except Exception as exc:  # pragma: no cover - executed in VL-SAT env
        raise RuntimeError("VL-SAT hook needs trimesh and utils.util_ply") from exc

    scan_id, _ = _subgraph_parts(subgraph_id)
    ply_path = Path(dataset.root_3rscan) / scan_id / dataset.mconfig.label_file
    mesh = trimesh.load(str(ply_path), process=False)
    instances = util_ply.read_labels(mesh).flatten()
    instance_ids = {int(x) for x in np.unique(instances)}
    instance_ids.discard(0)
    return instance_ids


def node_instance_ids(dataset: Any, subgraph_id: str) -> list[int]:
    """Return node index -> 3RScan instance id mapping for one subgraph."""

    object_ids = list(dataset.objs_json[subgraph_id].keys())
    present_instance_ids = _read_instance_ids_from_ply(dataset, subgraph_id)
    return [int(object_id) for object_id in object_ids if int(object_id) in present_instance_ids]


def make_raw_record(
    *,
    dataset: Any,
    dataset_index: int,
    edge_indices: Any,
    rel_scores_3d: Any,
    baseline_run_id: str,
    rel_scores_2d: Any | None = None,
    obj_scores_3d: Any | None = None,
    obj_scores_2d: Any | None = None,
) -> dict[str, Any]:
    """Create one raw H001 dump record from a VL-SAT validation item.

    Assumptions:
    - validation DataLoader uses batch_size=1 and shuffle=False;
    - `dataset_index` is the validation-loop index `i`;
    - `rel_scores_3d` is the sigmoid output from `PointNetRelClsMulti`;
    - `edge_indices` still refers to node indices within the same subgraph.
    """

    subgraph_id = dataset.scans[int(dataset_index)]
    scan_id, subset_split_id = _subgraph_parts(subgraph_id)
    rel_scores = _tolist(rel_scores_3d)
    edges = _tolist(edge_indices)
    node_ids = node_instance_ids(dataset, subgraph_id)

    if len(edges) != len(rel_scores):
        raise ValueError(
            f"edge/score length mismatch for {subgraph_id}: "
            f"{len(edges)} edges vs {len(rel_scores)} score rows"
        )

    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "record_type": "vlsat_raw_subgraph_scores",
        "baseline_name": "vlsat_closed_set",
        "baseline_run_id": baseline_run_id,
        "created_at": date.today().isoformat(),
        "scan_id": scan_id,
        "subset_split_id": subset_split_id,
        "subgraph_id": subgraph_id,
        "score_source": "vlsat_rel_cls_3d_sigmoid",
        "relation_names": list(dataset.relationNames),
        "node_instance_ids": node_ids,
        "edge_indices": edges,
        "rel_scores_3d": rel_scores,
        "rel_scores_2d": _tolist(rel_scores_2d) if rel_scores_2d is not None else None,
        "obj_scores_3d": _tolist(obj_scores_3d) if obj_scores_3d is not None else None,
        "obj_scores_2d": _tolist(obj_scores_2d) if obj_scores_2d is not None else None,
    }


def append_raw_record(path: str | os.PathLike[str], record: dict[str, Any]) -> None:
    """Append one raw record as JSONL."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def usage_note() -> str:
    return """Minimal insertion sketch:

from h001_vlsat_dump_hook import append_raw_record, make_raw_record

# inside validation loop, with batch_size=1 and shuffle=False, after rel_cls_3d exists:
raw = make_raw_record(
    dataset=self.dataset_valid,
    dataset_index=i,
    edge_indices=edge_indices.detach().cpu(),
    rel_scores_3d=rel_cls_3d.detach().cpu(),
    baseline_run_id="vlsat_eval_YYYYMMDD",
)
append_raw_record("h001_vlsat_raw.jsonl", raw)
"""
