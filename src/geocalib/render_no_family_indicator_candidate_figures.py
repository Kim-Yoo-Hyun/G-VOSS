#!/usr/bin/env python3
"""Render isolated qualitative/teaser candidates with the refitted model."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_renderer(root: Path) -> Any:
    path = root / "paper/scripts/render_figure3_geometry_panels.py"
    spec = importlib.util.spec_from_file_location("h001_candidate_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_import:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dynamic_context(renderer: Any, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        return renderer.attach_structured_product_ranks(cases)
    except ValueError as error:
        marker = "invalid_teaser_context:"
        message = str(error)
        if marker not in message:
            raise
        context = ast.literal_eval(message.split(marker, 1)[1])
        stable_checks = {
            key: value
            for key, value in context["validations"].items()
            if key not in {"removed_rank_lock", "promoted_rank_lock"}
        }
        if not all(stable_checks.values()):
            raise ValueError(f"candidate_teaser_membership_changed:{stable_checks}") from error
        removed = context["target_removed"]
        promoted = context["promoted"]
        renderer.TEASER_EXPECTED_RANKS = {
            "removed": (removed["source_rank"], removed["routed_rank"]),
            "promoted": (promoted["source_rank"], promoted["routed_rank"]),
        }
        cases.clear()
        cases.update(renderer.load_queue_cases())
        return renderer.attach_structured_product_ranks(cases)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    out.mkdir(parents=True, exist_ok=True)
    branch = root / "experiments/H001_geom_reliability/no_family_indicator_v1"
    renderer = load_renderer(root)
    renderer.STRUCTURED_MODEL_JSON = branch / "fit/structured_models.json"
    renderer.PRIMARY_SCAN_CI_JSON = branch / "evaluation/scan_cluster/summary.json"
    renderer.SURFACE_AUDIT_JSON = branch / "evaluation/surface_audit/summary.json"
    cases = renderer.load_queue_cases()
    missing = [case_id for case_id in renderer.EXPECTED_CASES if case_id not in cases]
    if missing:
        raise ValueError(f"missing_qualitative_cases:{missing}")
    context = dynamic_context(renderer, cases)
    metrics = renderer.load_teaser_metrics()
    qualitative_svg, records = renderer.render_camera_ready_qualitative(cases)
    teaser_svg = renderer.render_exchange_teaser(metrics, context)
    qualitative_path = out / "figure3_qualitative.svg"
    teaser_path = out / "teaser_exchange.svg"
    qualitative_path.write_text(renderer.enforce_minimum_stroke(qualitative_svg), encoding="utf-8")
    teaser_path.write_text(renderer.enforce_minimum_stroke(teaser_svg), encoding="utf-8")
    records_path = out / "qualitative_cases.json"
    records_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "h001_no_family_indicator_candidate_figures_v1",
        "status": "completed_svg_candidates",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_path": str(renderer.STRUCTURED_MODEL_JSON.relative_to(root)),
        "model_sha256": sha256(renderer.STRUCTURED_MODEL_JSON),
        "teaser_context": {
            "scan_id": context["scan_id"],
            "subgraph_id": context["subgraph_id"],
            "target_removed": context["target_removed"],
            "promoted": context["promoted"],
            "validations": context["validations"],
        },
        "aggregate_metrics": metrics,
        "rendered_case_ids": [record["case_id"] for record in records],
        "outputs": {
            "qualitative_svg": qualitative_path.name,
            "qualitative_sha256": sha256(qualitative_path),
            "teaser_svg": teaser_path.name,
            "teaser_sha256": sha256(teaser_path),
            "cases_json": records_path.name,
        },
        "claim_boundary": "illustrative source-backed cases only; not representative evaluation samples",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": manifest["status"], "ranks": {
        "removed": [context["target_removed"]["source_rank"], context["target_removed"]["routed_rank"]],
        "promoted": [context["promoted"]["source_rank"], context["promoted"]["routed_rank"]],
    }}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
